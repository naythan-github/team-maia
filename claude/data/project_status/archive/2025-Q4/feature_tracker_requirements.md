# Feature Tracker Requirements

**Project**: feature_tracker.py
**Purpose**: TDD enforcement tool implementing Anthropic's JSON feature list pattern
**Date**: 2025-12-14
**Agents**: SRE Principal Engineer + AI Specialists

---

## Problem Statement

Maia sometimes forgets to follow TDD protocol. Current enforcement is documentation-based (easily ignored). Need structural enforcement that:
1. Forces requirements phase before coding
2. Tracks progress objectively (X/Y passing)
3. Recovers TDD state after context compaction
4. Prevents infinite retry loops

---

## Functional Requirements

### FR-1: Project Initialization
- **FR-1.1**: `init <project_name>` creates `{project}_features.json`
- **FR-1.2**: JSON schema includes: project, created, features[], summary
- **FR-1.3**: Initial state: 0 features, 0% completion
- **FR-1.4**: Fails gracefully if file already exists (--force to overwrite)

### FR-2: Feature Management
- **FR-2.1**: `add "<name>" --category <cat> --priority <n>` adds feature
- **FR-2.2**: Auto-generates feature ID (F001, F002, etc.)
- **FR-2.3**: `add` with `--verification "step1" "step2"` adds verification steps
- **FR-2.4**: `add` with `--test path/to/test.py` links test file
- **FR-2.5**: New features default to passes=false, attempts=0

### FR-3: Status Updates
- **FR-3.1**: `update <id> --passes` marks feature as passing
- **FR-3.2**: `update <id> --fails` marks feature as failing, increments attempts
- **FR-3.3**: `update` recalculates summary automatically
- **FR-3.4**: `update` records last_tested timestamp

### FR-4: Circuit Breaker
- **FR-4.1**: Feature blocked when attempts >= max_attempts (default 5)
- **FR-4.2**: Blocked features excluded from `next` command
- **FR-4.3**: `reset <id>` clears attempts and unblocks
- **FR-4.4**: Block reason recorded in JSON

### FR-5: Progress Queries
- **FR-5.1**: `next` returns highest-priority failing feature (not blocked)
- **FR-5.2**: `next` returns None if all passing or all blocked
- **FR-5.3**: `summary` returns total/passing/failing/blocked/completion%
- **FR-5.4**: `list` shows all features with status

### FR-6: Session Integration
- **FR-6.1**: `status` returns formatted TDD state for agent context injection
- **FR-6.2**: Status includes: project name, X/Y passing, next feature, verification steps

---

## Non-Functional Requirements

### NFR-1: Reliability
- **NFR-1.1**: Atomic writes (tmp + rename) - no corruption on crash
- **NFR-1.2**: Backup before write ({file}.backup)
- **NFR-1.3**: Schema validation on load
- **NFR-1.4**: Graceful error handling - never crash, return error dict

### NFR-2: Performance
- **NFR-2.1**: All operations < 50ms
- **NFR-2.2**: JSON file < 1MB supported

### NFR-3: Compatibility
- **NFR-3.1**: Python 3.9+
- **NFR-3.2**: No external dependencies (stdlib only)
- **NFR-3.3**: CLI and library usage

---

## Data Schema

```json
{
  "schema_version": "1.0",
  "project": "string",
  "created": "ISO8601",
  "last_updated": "ISO8601",

  "features": [
    {
      "id": "F001",
      "name": "string",
      "category": "string",
      "priority": 1,
      "passes": false,
      "blocked": false,
      "block_reason": null,
      "verification": ["step1", "step2"],
      "test_file": "path/to/test.py|null",
      "last_tested": "ISO8601|null",
      "attempts": 0,
      "max_attempts": 5
    }
  ],

  "summary": {
    "total": 0,
    "passing": 0,
    "failing": 0,
    "blocked": 0,
    "completion_percentage": 0.0
  }
}
```

---

## CLI Interface

```bash
# Initialize project
python3 feature_tracker.py init my_project

# Add features
python3 feature_tracker.py add "User authentication" --category api --priority 1
python3 feature_tracker.py add "Rate limiting" --category security --priority 2 --test tests/test_rate.py

# Update status
python3 feature_tracker.py update F001 --passes
python3 feature_tracker.py update F002 --fails

# Query progress
python3 feature_tracker.py next
python3 feature_tracker.py summary
python3 feature_tracker.py list
python3 feature_tracker.py status  # For agent context injection

# Recovery
python3 feature_tracker.py reset F002
```

---

## Acceptance Criteria

1. ✅ `init` creates valid JSON with correct schema
2. ✅ `add` creates feature with auto-generated ID
3. ✅ `update --passes` marks passing, records timestamp
4. ✅ `update --fails` increments attempts, blocks at max
5. ✅ `next` returns correct priority feature, skips blocked
6. ✅ `summary` shows accurate counts
7. ✅ `status` returns agent-injectable format
8. ✅ Atomic writes prevent corruption
9. ✅ All operations < 50ms
10. ✅ 90%+ test coverage

---

## File Locations

- Tool: `claude/tools/sre/feature_tracker.py`
- Tests: `claude/tools/sre/tests/test_feature_tracker.py`
- Data: `claude/data/project_status/active/{project}_features.json`

---

*Requirements Complete - Ready for Phase 3 (Test Design)*
