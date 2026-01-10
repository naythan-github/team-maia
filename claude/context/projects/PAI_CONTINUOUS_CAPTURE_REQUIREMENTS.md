# PAI Continuous Capture System - Requirements & Implementation Plan

**Phase**: 263
**Status**: Ready for TDD Implementation
**Owner**: SRE Agent
**Created**: 2026-01-10

---

## Executive Summary

The current PAI learning system fails to capture learnings reliably because:
1. **PreCompact hooks have a known bug** - they don't fire during real Claude Code compactions
2. **Sessions undergo multiple compactions** - context is lost before `/close-session` runs
3. **PAI v2 bridge has a critical bug** - `sqlite3.Connection()` vs `sqlite3.connect()`

This document specifies a **Continuous Incremental Capture** system that doesn't depend on compaction events.

---

## Problem Statement

### Current State (Broken)
```
Session starts
    ↓
Work happens, context fills
    ↓
Compaction event (PreCompact hook SHOULD fire - but doesn't due to bug)
    ↓
Context lost, no learnings captured
    ↓
More work, more compactions
    ↓
Session ends (user rarely calls /close-session)
    ↓
Result: 98% of sessions have zero learnings captured
```

### Evidence
- 107 sessions tracked, only 2 have extracted learnings (1.9%)
- PreCompact hooks registered but no real compaction events in logs
- Context monitor runs but only triggers at 70% threshold (too late)
- PAI v2 bridge silently fails due to sqlite API bug

---

## Solution: Continuous Incremental Capture

### Architecture
```
┌─────────────────────────────────────────────────────────────┐
│ CONTINUOUS CAPTURE DAEMON (every 2-3 minutes)              │
│                                                             │
│ For each active Claude project:                            │
│   1. Read transcript.jsonl                                 │
│   2. Load high-water mark (last processed message index)   │
│   3. Extract learnings from NEW messages only              │
│   4. Write learnings to append-only queue file             │
│   5. Update high-water mark                                │
│   6. On compaction detected: reset high-water mark to 0    │
│                                                             │
│ Separate background processor:                             │
│   - Reads queue files                                      │
│   - Inserts to database                                    │
│   - Deletes processed queue files                          │
│   - Alerts on failures                                     │
└─────────────────────────────────────────────────────────────┘
```

### Why This Works
1. **Doesn't depend on PreCompact hooks** - runs on timer, not events
2. **Captures incrementally** - processes only new content each cycle
3. **Survives compaction** - learnings already on disk before compaction
4. **Decouples capture from storage** - file write (fast) separate from DB (can fail)
5. **Recoverable** - queue files persist until successfully processed

---

## Functional Requirements

### FR-1: Continuous Capture Daemon
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-1.1 | Scan all active Claude projects every 2-3 minutes | Must |
| FR-1.2 | Track high-water mark per project (last processed message index) | Must |
| FR-1.3 | Extract learnings only from messages after high-water mark | Must |
| FR-1.4 | Write extracted learnings to queue file before any DB operations | Must |
| FR-1.5 | Detect compaction (message count decreased) and reset high-water mark | Must |
| FR-1.6 | Run as LaunchAgent (macOS) with auto-restart | Must |
| FR-1.7 | Log all activity to ~/.maia/logs/continuous_capture.log | Must |

### FR-2: Queue-Based Storage
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-2.1 | Queue directory: ~/.maia/learning_queue/ | Must |
| FR-2.2 | Queue file format: {timestamp}_{context_id}.json | Must |
| FR-2.3 | Queue files are append-only, never modified in place | Must |
| FR-2.4 | Each queue file is self-contained (no dependencies on prior files) | Must |

### FR-3: Background Queue Processor
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-3.1 | Process queue files oldest-first | Must |
| FR-3.2 | Insert learnings to PAI v2 database | Must |
| FR-3.3 | Delete queue file only after confirmed DB insert | Must |
| FR-3.4 | Retry failed inserts with exponential backoff | Must |
| FR-3.5 | Alert (log + optional notification) on persistent failures | Must |
| FR-3.6 | Run as separate daemon or scheduled task | Must |

### FR-4: Compaction Detection
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-4.1 | Detect compaction by comparing current msg count to stored count | Must |
| FR-4.2 | On compaction detected: log event, reset high-water mark | Must |
| FR-4.3 | Treat post-compaction transcript as fresh (re-extract from beginning) | Should |

### FR-5: Bug Fixes (Prerequisites)
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-5.1 | Fix PAI v2 bridge: sqlite3.Connection → sqlite3.connect | Must |
| FR-5.2 | Fix compaction_metrics schema: add 'proactive_monitor' to CHECK constraint | Should |

---

## Non-Functional Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-1 | Capture cycle overhead | < 500ms per project |
| NFR-2 | Queue file write latency | < 50ms |
| NFR-3 | Memory footprint (daemon) | < 50MB |
| NFR-4 | Disk usage (queue files) | < 100MB (with cleanup) |
| NFR-5 | Recovery time after failure | < 5 minutes |
| NFR-6 | Data loss on crash | Zero (queue files are durable) |

---

## Data Structures

### High-Water Mark Storage
```json
// ~/.maia/capture_state/{context_id}.json
{
  "context_id": "7625",
  "last_message_index": 42,
  "last_message_count": 50,
  "last_capture_timestamp": "2026-01-10T12:00:00Z",
  "compaction_count": 3
}
```

### Queue File Format
```json
// ~/.maia/learning_queue/1704888000_7625.json
{
  "capture_id": "uuid",
  "context_id": "7625",
  "captured_at": "2026-01-10T12:00:00Z",
  "message_range": [43, 50],
  "compaction_number": 3,
  "learnings": [
    {
      "type": "decision",
      "content": "Chose queue-based architecture over direct DB writes",
      "confidence": 0.85,
      "source_message_index": 45
    }
  ],
  "metadata": {
    "agent": "sre_principal_engineer_agent",
    "tools_used": ["Read", "Bash", "Write"]
  }
}
```

---

## Implementation Plan (TDD)

### Phase 1: Bug Fixes (30 min)
```
1. Fix sqlite3.Connection bug in pai_v2_bridge.py
   - Test: test_pai_v2_bridge_connects_correctly

2. Fix compaction_metrics CHECK constraint
   - Test: test_metrics_accepts_proactive_monitor_trigger
```

### Phase 2: High-Water Mark Tracking (1 hr)
```
1. Create CaptureStateManager class
   - Test: test_load_nonexistent_state_returns_defaults
   - Test: test_save_and_load_state_roundtrip
   - Test: test_state_persists_across_instances

2. Implement compaction detection
   - Test: test_detects_compaction_when_message_count_decreases
   - Test: test_no_compaction_when_message_count_increases
   - Test: test_resets_high_water_mark_on_compaction
```

### Phase 3: Incremental Extraction (1.5 hr)
```
1. Create IncrementalExtractor class
   - Test: test_extracts_only_messages_after_high_water_mark
   - Test: test_returns_empty_when_no_new_messages
   - Test: test_handles_empty_transcript
   - Test: test_handles_malformed_messages_gracefully

2. Integrate with existing extraction.py patterns
   - Test: test_uses_all_12_pattern_types
   - Test: test_extraction_returns_structured_learnings
```

### Phase 4: Queue File Writer (1 hr)
```
1. Create QueueWriter class
   - Test: test_writes_to_correct_directory
   - Test: test_file_naming_convention
   - Test: test_atomic_write_no_partial_files
   - Test: test_self_contained_queue_file

2. Implement file rotation/cleanup
   - Test: test_cleanup_processed_files
   - Test: test_preserves_unprocessed_files
```

### Phase 5: Queue Processor (1.5 hr)
```
1. Create QueueProcessor class
   - Test: test_processes_oldest_first
   - Test: test_inserts_to_database
   - Test: test_deletes_only_after_confirmed_insert
   - Test: test_retries_on_failure
   - Test: test_alerts_on_persistent_failure

2. Integrate with PAI v2 bridge (fixed)
   - Test: test_end_to_end_queue_to_database
```

### Phase 6: Continuous Capture Daemon (1 hr)
```
1. Create ContinuousCaptureDaemon class
   - Test: test_scans_all_active_projects
   - Test: test_respects_scan_interval
   - Test: test_handles_project_errors_gracefully
   - Test: test_shutdown_gracefully

2. Integrate all components
   - Test: test_full_capture_cycle
   - Test: test_survives_simulated_compaction
```

### Phase 7: LaunchAgent Installation (30 min)
```
1. Create installer script
   - Test: test_generates_valid_plist
   - Test: test_installs_to_correct_location
   - Test: test_uninstall_removes_cleanly

2. Update existing context_monitor_installer.py or create new
```

### Phase 8: Integration Testing (1 hr)
```
1. End-to-end tests
   - Test: test_captures_learnings_before_simulated_compaction
   - Test: test_queue_survives_daemon_restart
   - Test: test_database_populated_after_queue_processing
   - Test: test_no_duplicate_learnings_on_reprocess
```

---

## File Structure

```
claude/tools/learning/
├── continuous_capture/
│   ├── __init__.py
│   ├── daemon.py              # ContinuousCaptureDaemon
│   ├── state_manager.py       # CaptureStateManager (high-water marks)
│   ├── incremental_extractor.py  # IncrementalExtractor
│   ├── queue_writer.py        # QueueWriter
│   ├── queue_processor.py     # QueueProcessor
│   └── installer.py           # LaunchAgent installer

tests/learning/
├── continuous_capture/
│   ├── test_state_manager.py
│   ├── test_incremental_extractor.py
│   ├── test_queue_writer.py
│   ├── test_queue_processor.py
│   ├── test_daemon.py
│   └── test_integration.py
```

---

## Acceptance Criteria

### Must Pass Before Complete
- [ ] All TDD tests pass (pytest tests/learning/continuous_capture/ -v)
- [ ] PAI v2 bridge bug fixed and tested
- [ ] Daemon runs continuously via LaunchAgent
- [ ] Queue files created during normal usage
- [ ] Learnings appear in PAI v2 database
- [ ] System survives simulated compaction (message count reset)
- [ ] No data loss on daemon restart
- [ ] Logs show capture activity every 2-3 minutes

### Success Metrics (Post-Deploy)
- Learning extraction rate: >50% of sessions (currently 1.9%)
- Queue processing latency: <5 minutes from capture to database
- Zero silent failures (all errors logged and alerted)

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Transcript file locked during read | Capture fails | Use file copy or retry with backoff |
| Queue directory fills up | Disk space | Implement max queue size + cleanup |
| Database unavailable | Learnings not stored | Queue files persist until DB available |
| Daemon crashes | Missing captures | LaunchAgent auto-restart + startup recovery |

---

## Handoff Notes

1. **Start with Phase 1** (bug fixes) - these are blocking everything else
2. **Use existing extraction.py** - 12 pattern types already implemented
3. **Reuse context_monitor.py patterns** - project scanning, LaunchAgent structure
4. **Test against real transcripts** - copy from ~/.claude/projects/*/transcript.jsonl
5. **Check logs frequently** - ~/.maia/logs/ for debugging

---

## References

- Current learning system: claude/tools/learning/
- Context monitor: claude/hooks/context_monitor.py
- Extraction patterns: claude/tools/learning/extraction.py
- PAI v2 bridge (buggy): claude/tools/learning/pai_v2_bridge.py:60
- Archive schema: claude/tools/learning/archive_schema.sql
