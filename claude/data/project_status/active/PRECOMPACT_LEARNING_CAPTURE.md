# Pre-Compaction Learning Capture System
**Phase 237: Intelligent Context Compaction with Learning Preservation**

## Status: 🚧 IN DEVELOPMENT
**Started**: 2026-01-06
**Target**: Production-ready with extensive testing
**Priority**: CRITICAL - Fixes learning loss during compaction

---

## Executive Summary

**Problem**: Claude Code's context compaction breaks long conversations and prevents PAI v2 from capturing learnings.

**Solution**: Pre-compaction hook that extracts learnings and archives full conversations BEFORE summarization happens.

**Impact**:
- ✅ Zero learning loss across compactions
- ✅ Full conversation history preserved (cold storage)
- ✅ Conversation continuity maintained
- ✅ PAI v2 learning database enriched with compaction-triggered captures

---

## Architecture Decisions

### 1. Learning Extraction Scope: **HYBRID** (1c)
- **UOCs** (existing PAI v2 taxonomy): decisions, solutions, outcomes
- **Conversation metadata**: tool usage patterns, agent handoffs, error recovery sequences
- **Rationale**: Preserve UOC quality while adding continuity metadata

### 2. Retrieval Priority: **PHASE 1 INCLUDED** (2a)
- Basic retrieval (`get_conversation(context_id)`) built immediately
- **Rationale**: Archive without retrieval = untestable, unvalidated

### 3. Failure Mode: **RETRY WITH FALLBACK** (3c)
- 3 retry attempts with exponential backoff
- Graceful degradation on failure (log error, proceed with compaction)
- User alert on degraded capture
- **Rationale**: Never break conversation, capture what we can

### 4. Testing Strategy: **SYNTHETIC → MANUAL → PRODUCTION** (4c)
- Unit tests on synthetic transcripts
- Integration tests with manual `/compact`
- Production auto-compaction after validation
- **Rationale**: Prove safety before enabling auto-trigger

### 5. Backward Compatibility: **PARALLEL SYSTEMS** (5c)
- Archive runs alongside existing `learning_session_*.json` files
- No migration of old data (new sessions only)
- **Rationale**: Don't break existing system, prove new system first

### 6. Progress Tracking: **COMMITS + DEV LOG** (6c)
- Git commits per component (code proof)
- Live updates to this document (decision log)
- **Rationale**: Code + context = full recovery after compaction

### 7. Testing Scope: **COMPREHENSIVE** (7d)
- Full lifecycle (SessionStart → compaction → retrieval)
- Edge cases (empty, huge, corrupted conversations)
- Performance (<5s hook execution)
- **Rationale**: Production-ready = bulletproof

### 8. Success Criteria: **ALL CHECKBOXES** (8)
See "Definition of Done" section below.

---

## System Components

### 1. Pre-Compaction Hook Script
**File**: `claude/hooks/pre_compaction_learning_capture.py`

**Responsibilities**:
- Triggered by Claude Code PreCompact event
- Reads full transcript from provided path
- Extracts learnings (UOCs + metadata)
- Archives full conversation to SQLite
- Saves learnings to PAI v2 database
- Retry logic with graceful degradation
- Performance target: <5s for 1000-message conversations

**Input** (from Claude Code):
```json
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../abc123.jsonl",
  "hook_event_name": "PreCompact",
  "trigger": "auto",
  "permission_mode": "default"
}
```

**Output**:
- Silent success (exit 0)
- Error logged to `~/.maia/logs/pre_compaction_errors.log`
- Metrics logged to `~/.maia/logs/pre_compaction_metrics.jsonl`

---

### 2. Learning Extraction Engine
**File**: `claude/tools/learning/extraction.py`

**Responsibilities**:
- Parse JSONL transcript
- Identify learning moments via pattern matching
- Extract conversation metadata
- Classify learning types (UOC taxonomy)
- Return structured learning objects

**Learning Triggers**:
```python
LEARNING_PATTERNS = {
    'decision': [
        r'decided to (\w+)',
        r'chose (\w+) over (\w+) because',
        r'went with (\w+)',
    ],
    'solution': [
        r'fixed (.*) by (.*)',
        r'root cause was (.*)',
        r'resolved by (.*)',
    ],
    'outcome': [
        r'✅.*worked',
        r'✅.*complete',
        r'failed because (.*)',
        r'blocked by (.*)',
    ],
    'handoff': [
        r'HANDOFF DECLARATION:',
        r'To: (\w+)_agent',
    ],
    'checkpoint': [
        r'save state',
        r'git commit',
        r'deployed to',
    ],
}
```

**Metadata Captured**:
- Tool usage frequency (which tools called, how often)
- Agent transitions (which agents used, when)
- Error recovery sequences (error → solution pairs)
- Conversation checkpoints (save state, commits)
- Performance metrics (tool execution times)

**Output Format**:
```python
{
    'learnings': [
        {
            'type': 'decision',
            'content': 'chose SQLite over Postgres because simpler deployment',
            'timestamp': '2026-01-06T10:30:00Z',
            'context': {
                'surrounding_messages': [...],
                'active_agent': 'sre_principal_engineer_agent',
                'tools_used': ['Read', 'Edit'],
            }
        },
        ...
    ],
    'metadata': {
        'tool_usage': {'Read': 15, 'Edit': 8, 'Bash': 12},
        'agents_used': ['sre_principal_engineer_agent'],
        'error_count': 2,
        'checkpoint_count': 3,
    }
}
```

---

### 3. Conversation Archive System
**File**: `claude/tools/learning/archive.py`

**Database**: `~/.maia/data/conversation_archive.db`

**Schema**:
```sql
CREATE TABLE conversation_snapshots (
    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
    context_id TEXT NOT NULL,
    session_id TEXT,
    snapshot_timestamp INTEGER NOT NULL,
    trigger_type TEXT,  -- 'auto' or 'manual'

    -- Transcript data
    transcript_path TEXT,
    full_conversation TEXT,  -- Complete JSONL
    message_count INTEGER,
    token_estimate INTEGER,

    -- Learning summary
    learning_count INTEGER,
    learning_ids TEXT,  -- JSON array of PAI v2 learning IDs

    -- Metadata
    tool_usage_stats TEXT,  -- JSON: tool frequency map
    agents_used TEXT,  -- JSON: agent list
    error_count INTEGER,

    -- Retrieval optimization
    first_message TEXT,  -- First user message (for search)
    last_message TEXT,   -- Last message before compaction
    topics TEXT,  -- JSON: extracted topics/keywords

    UNIQUE(context_id, snapshot_timestamp)
);

CREATE INDEX idx_context_snapshots ON conversation_snapshots(context_id, snapshot_timestamp DESC);
CREATE INDEX idx_session_snapshots ON conversation_snapshots(session_id);
CREATE INDEX idx_snapshot_time ON conversation_snapshots(snapshot_timestamp DESC);

-- Retrieval performance
CREATE VIRTUAL TABLE conversation_search USING fts5(
    context_id,
    first_message,
    topics,
    content=conversation_snapshots,
    content_rowid=snapshot_id
);
```

**Operations**:
- `archive_conversation(transcript_path, context_id, metadata)` → snapshot_id
- `get_conversation(context_id, before_timestamp=None)` → full transcript
- `search_conversations(query, limit=10)` → matching snapshots
- `get_snapshot_metadata(snapshot_id)` → learning count, tools used, etc.

---

### 4. Retrieval Tools
**File**: `claude/tools/learning/retrieval.py`

**Functions**:

```python
def get_conversation(context_id: str, before_timestamp: Optional[int] = None) -> dict:
    """
    Retrieve archived conversation for a context.

    Args:
        context_id: Claude context window ID
        before_timestamp: Get snapshot before this time (default: latest)

    Returns:
        {
            'snapshot_id': int,
            'context_id': str,
            'timestamp': int,
            'messages': [...],  # Parsed JSONL
            'metadata': {...},
            'learnings': [...]
        }
    """

def search_conversations(query: str, limit: int = 10) -> List[dict]:
    """
    Search archived conversations by content.

    Args:
        query: Search keywords
        limit: Max results

    Returns:
        List of matching snapshots with relevance scores
    """

def get_compaction_history(context_id: str) -> List[dict]:
    """
    Get all compaction events for a context (timeline view).

    Returns:
        [{
            'timestamp': int,
            'trigger': 'auto' | 'manual',
            'messages_before': int,
            'learnings_captured': int,
        }]
    """

def export_conversation(context_id: str, format: str = 'markdown') -> str:
    """
    Export archived conversation in human-readable format.

    Formats: markdown, json, html
    """
```

---

### 5. PAI v2 Integration
**File**: `claude/tools/learning/session.py` (existing, extend)

**New Methods**:
```python
class SessionManager:
    def capture_precompaction_learnings(
        self,
        context_id: str,
        learnings: List[dict],
        metadata: dict
    ) -> List[str]:
        """
        Save learnings extracted during pre-compaction.

        Returns:
            List of learning IDs created in PAI v2 database
        """
```

**Integration Points**:
- Learning extraction → SessionManager.capture_precompaction_learnings()
- Use existing UOC taxonomy (verify.py patterns)
- Associate learnings with session_id (via context_id lookup)
- Update session metadata (compaction_count, total_learnings)

---

### 6. Hook Configuration
**File**: `~/.claude/settings.local.json`

**Configuration**:
```json
{
  "hooks": {
    "PreCompact": [
      {
        "matcher": "manual",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR\"/claude/hooks/pre_compaction_learning_capture.py",
            "timeout": 5000
          }
        ]
      }
    ]
  }
}
```

**Phase 1**: `"matcher": "manual"` (testing only)
**Phase 2**: Add `"matcher": "auto"` after validation

---

## Implementation Plan

### Phase 1: Core Capture + Validation (Days 1-3)

#### Day 1: Foundation
- [ ] **DB Schema**: Create `conversation_archive.db` with schema
- [ ] **Test Framework**: Set up pytest fixtures for synthetic transcripts
- [ ] **Extraction Engine**: `extraction.py` with pattern matching (TDD)
  - [ ] Unit tests: decision patterns
  - [ ] Unit tests: solution patterns
  - [ ] Unit tests: outcome patterns
  - [ ] Unit tests: metadata extraction
- [ ] **Commit**: "feat(learning): Add extraction engine with TDD"
- [ ] **Update this doc**: Progress checkpoint

#### Day 2: Archive + Retrieval
- [ ] **Archive System**: `archive.py` with SQLite operations (TDD)
  - [ ] Unit tests: archive conversation
  - [ ] Unit tests: handle duplicates (same context_id + timestamp)
  - [ ] Unit tests: token estimation
- [ ] **Retrieval Tools**: `retrieval.py` basic functions (TDD)
  - [ ] Unit tests: get_conversation()
  - [ ] Unit tests: get_conversation() with timestamp filter
  - [ ] Unit tests: search_conversations()
- [ ] **Integration Tests**: extraction → archive → retrieval roundtrip
- [ ] **Commit**: "feat(learning): Add archive and retrieval with TDD"
- [ ] **Update this doc**: Progress checkpoint

#### Day 3: Hook + PAI v2 Integration
- [ ] **Hook Script**: `pre_compaction_learning_capture.py`
  - [ ] Read hook input (stdin JSON)
  - [ ] Call extraction engine
  - [ ] Call archive system
  - [ ] Call PAI v2 integration
  - [ ] Error handling + logging
- [ ] **PAI v2 Extension**: SessionManager.capture_precompaction_learnings()
- [ ] **Unit Tests**: Hook with synthetic input
- [ ] **Integration Test**: Full flow (mock transcript → hook → verify archive + PAI v2)
- [ ] **Manual Testing**: Create synthetic transcript, run hook manually
- [ ] **Commit**: "feat(learning): Add pre-compaction hook with PAI v2 integration"
- [ ] **Update this doc**: Progress checkpoint

---

### Phase 2: Production Hardening (Days 4-6)

#### Day 4: Retry Logic + Edge Cases
- [ ] **Retry Mechanism**: 3 attempts with exponential backoff
  - [ ] Unit tests: retry on DB lock
  - [ ] Unit tests: retry on filesystem error
  - [ ] Unit tests: graceful failure after 3 retries
- [ ] **Edge Case Handling**:
  - [ ] Empty conversations (0 messages)
  - [ ] Huge conversations (10K+ messages)
  - [ ] Corrupted JSONL (malformed JSON lines)
  - [ ] Missing transcript file
  - [ ] Concurrent compactions (same context_id)
- [ ] **Commit**: "feat(learning): Add retry logic and edge case handling"
- [ ] **Update this doc**: Progress checkpoint

#### Day 5: Performance + Monitoring
- [ ] **Performance Optimization**:
  - [ ] Streaming JSONL parsing (don't load full file to memory)
  - [ ] Batch DB inserts
  - [ ] Pattern matching optimization
  - [ ] Target: <5s for 1000-message conversations
- [ ] **Performance Tests**:
  - [ ] Benchmark: 100-message conversation
  - [ ] Benchmark: 1000-message conversation
  - [ ] Benchmark: 10K-message conversation
- [ ] **Monitoring**:
  - [ ] Metrics logging: execution time, learnings captured, errors
  - [ ] Dashboard query: compaction frequency, average capture time
- [ ] **Commit**: "perf(learning): Optimize pre-compaction hook for <5s target"
- [ ] **Update this doc**: Progress checkpoint

#### Day 6: Integration Testing + Production Config
- [ ] **Full Lifecycle Test**:
  - [ ] Start session → generate conversation → manual /compact → verify archive
  - [ ] Verify learnings in PAI v2 database
  - [ ] Verify retrieval works
  - [ ] Verify metadata accuracy
- [ ] **Failure Mode Test**:
  - [ ] Hook crash → verify compaction proceeds
  - [ ] DB locked → verify retry works
  - [ ] Timeout → verify graceful degradation
- [ ] **Production Configuration**:
  - [ ] Add to `~/.claude/settings.local.json` (manual trigger)
  - [ ] Test with real session + manual `/compact`
  - [ ] Validate archive created correctly
  - [ ] Enable auto-compaction (`"matcher": "auto"`)
  - [ ] Monitor first auto-compaction event
- [ ] **Commit**: "feat(learning): Enable pre-compaction hook in production"
- [ ] **Update this doc**: Progress checkpoint

---

## Testing Specifications

### Unit Tests
**File**: `tests/learning/test_extraction.py`

```python
def test_extract_decision_patterns():
    """Test decision pattern matching"""

def test_extract_solution_patterns():
    """Test solution pattern matching"""

def test_extract_outcome_patterns():
    """Test outcome pattern matching"""

def test_extract_metadata_tool_usage():
    """Test tool usage frequency extraction"""

def test_extract_metadata_agent_transitions():
    """Test agent transition tracking"""

def test_extract_empty_conversation():
    """Test handling of empty conversations"""

def test_extract_malformed_jsonl():
    """Test handling of corrupted JSONL"""
```

**File**: `tests/learning/test_archive.py`

```python
def test_archive_conversation():
    """Test basic conversation archival"""

def test_archive_duplicate_prevention():
    """Test unique constraint on (context_id, timestamp)"""

def test_archive_token_estimation():
    """Test token count estimation accuracy"""

def test_archive_concurrent_writes():
    """Test handling of concurrent archival (DB locking)"""
```

**File**: `tests/learning/test_retrieval.py`

```python
def test_get_conversation_latest():
    """Test retrieval of latest snapshot"""

def test_get_conversation_by_timestamp():
    """Test retrieval of specific snapshot by time"""

def test_search_conversations():
    """Test full-text search"""

def test_get_compaction_history():
    """Test timeline view of compactions"""
```

**File**: `tests/learning/test_pre_compaction_hook.py`

```python
def test_hook_input_parsing():
    """Test parsing of Claude Code hook input"""

def test_hook_full_flow():
    """Test complete hook execution"""

def test_hook_retry_logic():
    """Test retry on transient failures"""

def test_hook_graceful_degradation():
    """Test failure doesn't block compaction"""

def test_hook_performance():
    """Test <5s execution time requirement"""
```

### Integration Tests
**File**: `tests/integration/test_pre_compaction_lifecycle.py`

```python
def test_full_lifecycle():
    """
    Test complete flow:
    1. Create synthetic transcript
    2. Trigger pre-compaction hook
    3. Verify archive created
    4. Verify learnings in PAI v2
    5. Verify retrieval works
    6. Verify metadata accurate
    """

def test_manual_compaction_trigger():
    """Test hook with manual /compact command"""

def test_auto_compaction_trigger():
    """Test hook with automatic compaction (Phase 2)"""

def test_backward_compatibility():
    """Verify existing learning sessions unaffected"""
```

### Performance Tests
**File**: `tests/performance/test_pre_compaction_performance.py`

```python
def test_100_message_conversation():
    """Benchmark: 100-message conversation (<1s target)"""

def test_1000_message_conversation():
    """Benchmark: 1000-message conversation (<5s target)"""

def test_10k_message_conversation():
    """Benchmark: 10K-message conversation (<30s acceptable)"""
```

### Edge Case Tests
**File**: `tests/learning/test_edge_cases.py`

```python
def test_empty_conversation():
    """Test conversation with 0 messages"""

def test_huge_conversation():
    """Test conversation with 50K+ messages"""

def test_corrupted_jsonl():
    """Test malformed JSON lines"""

def test_missing_transcript():
    """Test transcript file not found"""

def test_concurrent_compactions():
    """Test multiple contexts compacting simultaneously"""
```

---

## Test Coverage Requirements

**Minimum Coverage**: 90% for production release

**Coverage by Component**:
- `extraction.py`: 95% (core logic, must be bulletproof)
- `archive.py`: 90% (DB operations)
- `retrieval.py`: 90% (read operations)
- `pre_compaction_learning_capture.py`: 85% (hook integration)

**Enforcement**:
```bash
pytest --cov=claude/tools/learning --cov-report=term-missing --cov-fail-under=90
```

---

## Definition of Done

**ALL of these must be TRUE before marking complete**:

### Functionality
- [x] Hook fires on manual `/compact` and captures learnings
- [ ] Hook fires on auto-compaction (Phase 2)
- [ ] Full transcript archived to SQLite with retrieval working
- [ ] PAI v2 integration successful (learnings queryable via existing tools)
- [ ] Retry logic works (3 attempts on failure)
- [ ] Graceful degradation (hook crash doesn't break compaction)

### Testing
- [ ] Unit tests >90% coverage (hook, extraction, archival, retrieval)
- [ ] Integration test: full conversation → compaction → verify archive matches transcript
- [ ] Performance test: hook completes in <5s for 1000-message conversation
- [ ] Edge case tests: empty, huge (10K+), corrupted conversations
- [ ] Failure test: hook crash doesn't break compaction
- [ ] Backward compatibility: existing learning sessions unaffected

### Documentation
- [ ] Hook architecture documented (this file)
- [ ] Testing guide (pytest commands, coverage requirements)
- [ ] Troubleshooting guide (common errors, debugging steps)
- [ ] API documentation (extraction, archive, retrieval functions)

### Production
- [ ] Production config added to `~/.claude/settings.local.json`
- [ ] Manual compaction validated in real session
- [ ] Auto-compaction enabled and validated (Phase 2)
- [ ] Monitoring dashboard (compaction frequency, capture success rate)
- [ ] Error alerting (degraded capture notifications)

### Code Quality
- [ ] Pre-commit TDD hook passes (all tests green)
- [ ] Python code reviewer approval (quality loop)
- [ ] No hardcoded paths (use MAIA_ROOT, expanduser())
- [ ] Type hints on all public functions
- [ ] Error messages actionable (tell user what to do)

---

## Progress Log

### 2026-01-06 10:45 - Project Initialized
- Created implementation plan
- Defined architecture decisions (1c, 2a, 3c, 4c, 5c, 6c, 7d, 8-all)
- Set success criteria (all checkboxes)
- Established testing requirements (90% coverage)
- **Status**: Ready to begin Day 1 implementation
- **Next**: Create DB schema and test framework

---

## Checkpoints (Updated Live)

### Checkpoint 1: Foundation Complete
**Date**: TBD
**Completed**:
- [ ] DB schema created
- [ ] Test framework ready
- [ ] Extraction engine implemented
- [ ] Unit tests passing (>90% coverage)
- [ ] Commit: "feat(learning): Add extraction engine with TDD"

### Checkpoint 2: Archive + Retrieval Complete
**Date**: TBD
**Completed**:
- [ ] Archive system implemented
- [ ] Retrieval tools implemented
- [ ] Integration tests passing (extraction → archive → retrieval)
- [ ] Commit: "feat(learning): Add archive and retrieval with TDD"

### Checkpoint 3: Hook + PAI v2 Integration Complete
**Date**: TBD
**Completed**:
- [ ] Hook script implemented
- [ ] PAI v2 integration implemented
- [ ] Manual testing successful
- [ ] Commit: "feat(learning): Add pre-compaction hook with PAI v2 integration"

### Checkpoint 4: Production Hardening Complete
**Date**: TBD
**Completed**:
- [ ] Retry logic implemented
- [ ] Edge cases handled
- [ ] Performance optimized (<5s)
- [ ] All tests passing (>90% coverage)
- [ ] Commit: "perf(learning): Optimize pre-compaction hook for <5s target"

### Checkpoint 5: Production Release
**Date**: TBD
**Completed**:
- [ ] Full lifecycle tests passing
- [ ] Production config enabled
- [ ] Manual compaction validated
- [ ] Auto-compaction enabled
- [ ] All Definition of Done criteria met ✅

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Hook timeout (>5s) on huge conversations | Medium | High | Streaming parsing, batch inserts, performance tests |
| Concurrent compactions cause DB locks | Low | Medium | Retry logic with exponential backoff |
| Transcript format changes (Claude Code update) | Low | High | Version detection, format migration path |
| Hook crash breaks compaction | Low | Critical | Graceful degradation, extensive error handling |
| Learning extraction misses critical patterns | Medium | Medium | Comprehensive pattern library, user feedback loop |
| Retrieval too slow for large archives | Low | Low | Indexed queries, FTS5 optimization |

---

## Dependencies

### External
- Claude Code v2 with PreCompact hook support ✅
- Python 3.11+ ✅
- SQLite 3.35+ (FTS5 support) ✅
- pytest + pytest-cov (testing) ✅

### Internal
- PAI v2 learning system (`claude/tools/learning/`) ✅
- MAIA session management (`~/.maia/sessions/`) ✅
- Existing hooks infrastructure (`claude/hooks/`) ✅

---

## Open Questions

**Resolved**:
- Learning scope → 1c: Hybrid (UOCs + metadata)
- Retrieval priority → 2a: Phase 1 included
- Failure mode → 3c: Retry with fallback
- Testing strategy → 4c: Synthetic → manual → production
- Backward compatibility → 5c: Parallel systems
- Progress tracking → 6c: Commits + dev log
- Testing scope → 7d: All (lifecycle, edge cases, performance)
- Success criteria → 8: All checkboxes

**Unresolved**: None

---

## Future Enhancements (Post-Phase 2)

### Phase 3: Advanced Retrieval
- Semantic search (embeddings for similarity matching)
- Cross-conversation patterns (learning trends over time)
- Conversation diffing (compare snapshots, see what changed)

### Phase 4: Intelligent Compaction
- Custom compaction strategy (preserve tagged content)
- Adaptive compaction (preserve more context if learning-dense)
- Multi-tier archival (hot/warm/cold storage)

### Phase 5: Analytics Dashboard
- Learning capture rate over time
- Most common learning patterns
- Compaction frequency analysis
- Tool usage trends

---

## References

- Claude Code Hooks Documentation: https://code.claude.com/docs/en/hooks.md#precompact
- PAI v2 Learning System: `claude/tools/learning/README.md`
- MAIA Context Loading Protocol: `claude/commands/init.md`
- TDD Development Protocol: `claude/context/core/tdd_development_protocol.md`
