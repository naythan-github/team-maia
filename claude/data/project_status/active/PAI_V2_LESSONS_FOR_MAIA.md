# PAI v2 Lessons for MAIA - Future Implementation Reference

**Created**: 2026-01-05
**Status**: Research Complete - Awaiting Implementation
**Source**: Comparative analysis of PAI v2 learning system vs broader MAIA architecture

---

## Executive Summary

PAI v2 demonstrates that focused, well-designed subsystems (~400 LOC) outperform sprawling architectures. Key patterns worth adopting across MAIA:

1. Non-blocking observation
2. Confidence-gated persistence
3. FTS5 for all searchable data
4. Privacy-first storage
5. Tool-specific capture modes

---

## PAI v2 Architecture (Reference)

### Components (7 files, ~400 LOC)
| File | Purpose | Key Pattern |
|------|---------|-------------|
| `schema.py` | Database schemas | Idempotent (IF NOT EXISTS) |
| `uocs.py` | Output capture | Async, <1ms, never blocks |
| `memory.py` | Session history | FTS5 full-text search |
| `verify.py` | Success measurement | Confidence scoring (0.7 threshold) |
| `learn.py` | Pattern extraction | Only from successful sessions |
| `session.py` | Orchestration | Singleton with reset |
| `uocs_cleanup.py` | Retention | 7-day cleanup |

### Storage
```
~/.maia/
├── outputs/{session_id}/     # UOCS captures
├── memory/memory.db          # Sessions + FTS5
└── learning/learning.db      # Patterns, preferences
```

---

## Lessons Learned

### 1. Simplicity Wins

**Finding**: PAI v2's 7 files accomplish cross-session learning that larger systems fail to deliver.

**Principle**: Start with the smallest working unit. Constraints force better design.

**MAIA Application**:
- Review complex subsystems for simplification opportunities
- Consider whether orchestration layers add value or complexity
- Each component should do ONE thing well

---

### 2. Non-Blocking by Default

**Finding**: UOCS uses daemon threads with <1ms overhead. If capture fails, session continues.

**Pattern**:
```python
def capture(self, tool_name, input_data, output_data):
    thread = threading.Thread(target=self._capture_async, daemon=True)
    thread.start()  # Fire and forget
```

**MAIA Application**:
- Learning/observability should be invisible to users
- Extend non-blocking pattern to:
  - Agent handoff logging
  - Performance metrics collection
  - Audit trail capture

---

### 3. Confidence-Gated Learning

**Finding**: PAI v2 only learns from sessions where VERIFY returns success=True with confidence >= 0.7.

**Pattern**:
```python
if verify_result.success and verify_result.confidence >= 0.7:
    learn_phase.extract_patterns(session)
```

**MAIA Application**:
- Don't persist agent handoff patterns unless they worked
- Don't save tool sequences unless task completed successfully
- Add confidence scoring to:
  - Agent recommendations
  - Context loading decisions
  - Capability lookups

---

### 4. FTS5 for Searchable Data

**Finding**: PAI v2 uses SQLite FTS5 with automatic trigger-based index sync.

**Capabilities**:
- Phrase matching
- Boolean operators
- Relevance scoring
- Sub-50ms search

**MAIA Application**:
- Add FTS5 to `capabilities.db` for tool/agent search
- Add FTS5 to `system_state.db` for phase history search
- Consider FTS5 for agent documentation search

**Implementation**:
```sql
CREATE VIRTUAL TABLE capabilities_fts USING fts5(
    name, description, keywords,
    content='capabilities', content_rowid='id'
);

CREATE TRIGGER capabilities_ai AFTER INSERT ON capabilities BEGIN
    INSERT INTO capabilities_fts(rowid, name, description, keywords)
    VALUES (new.id, new.name, new.description, new.keywords);
END;
```

---

### 5. Privacy-First Storage

**Finding**: PAI v2 stores ALL user data in `~/.maia/`, never in repo.

| Type | PAI v2 Location | Current MAIA |
|------|-----------------|--------------|
| Session data | `~/.maia/` | `~/.maia/` |
| User preferences | `~/.maia/` | `claude/data/` (repo) |
| Learning patterns | `~/.maia/` | N/A |

**MAIA Application**:
- Move `user_preferences.json` to `~/.maia/`
- Keep only code/templates in repo
- Full multi-user support

---

### 6. Tool-Specific Capture Modes

**Finding**: Not all data is equally valuable. PAI v2 captures differently per tool.

**Pattern**:
```python
CAPTURE_MODES = {
    'bash': 'output',      # Full stdout/stderr
    'read': 'metadata',    # Just path + size
    'edit': 'diff',        # Only the changes
    'webfetch': 'summary', # First 1000 chars
    'task': 'metadata',    # Agent result summary
}
```

**MAIA Application**:
- Tiered logging for observability
- **Full**: Critical operations (deployments, security changes)
- **Metadata**: Routine reads/writes
- **Summary**: Large outputs, web fetches
- **None**: High-frequency low-value operations

---

### 7. Singleton with Reset

**Finding**: PAI v2 uses lazy-loaded singletons that can be reset for testing.

**Pattern**:
```python
_manager = None

def get_session_manager():
    global _manager
    if _manager is None:
        _manager = SessionManager()
    return _manager

def reset_session_manager():
    global _manager
    _manager = None
```

**MAIA Application**:
- Adopt for orchestration components
- Enables test isolation
- Memory efficient (single instance)
- Thread-safe with locks

---

### 8. Idempotent Schema Operations

**Finding**: PAI v2 schemas are safe to re-run at any time.

**Pattern**:
```sql
CREATE TABLE IF NOT EXISTS sessions (...);
CREATE INDEX IF NOT EXISTS idx_sessions_date ON sessions(started_at);
```

**MAIA Application**:
- All database migrations should be idempotent
- Schema initialization should be safe to call multiple times
- Simplifies deployment and recovery

---

## Recommended Implementation Projects

### Project 1: VERIFY for Agent Handoffs
**Priority**: High
**Effort**: Medium

Add success measurement to agent handoff chains:
- Did the chain complete the task?
- What was the confidence?
- Should we learn from this sequence?

**Files to modify**:
- `claude/tools/orchestration/agent_swarm.py`
- `claude/hooks/swarm_auto_loader.py`

---

### Project 2: FTS5 for Capabilities
**Priority**: Medium
**Effort**: Low

Add full-text search to capabilities database:
- Faster tool/agent lookup
- Natural language queries
- Relevance-ranked results

**Files to modify**:
- `claude/tools/sre/capabilities_registry.py`
- `claude/data/databases/system/capabilities.db`

---

### Project 3: Unified Data Location
**Priority**: Medium
**Effort**: Medium

Move all user data to `~/.maia/`:
- `user_preferences.json` → `~/.maia/config/`
- User-specific databases → `~/.maia/data/`
- Full multi-user support

**Files to modify**:
- `claude/data/user_preferences.json` → migrate
- `claude/tools/core/paths.py` → update paths
- All tools referencing user prefs

---

### Project 4: Non-Blocking Observability
**Priority**: Low
**Effort**: Medium

Extend UOCS pattern to all observability:
- Agent handoff logging
- Performance metrics
- Audit trails

**Pattern**: Fire-and-forget daemon threads

---

### Project 5: Tiered Capture Modes
**Priority**: Low
**Effort**: Low

Implement tool-specific capture for debugging/audit:
- Full capture for critical ops
- Metadata only for routine ops
- Reduces storage, improves signal/noise

---

## Metrics to Track

If implementing these changes, measure:

| Metric | Baseline | Target |
|--------|----------|--------|
| Search latency (capabilities) | ~50ms | <10ms with FTS5 |
| Learning accuracy | N/A | >80% useful patterns |
| Storage usage | Current | -30% with tiered capture |
| Multi-user support | Partial | Full |

---

## References

- PAI v2 source: `claude/tools/learning/`
- PAI v2 tests: `tests/learning/`
- MAIA architecture: `CLAUDE.md`, `claude/context/core/`
- Session management: `claude/hooks/swarm_auto_loader.py`

---

## Change Log

| Date | Change |
|------|--------|
| 2026-01-05 | Initial research complete |
| 2026-01-05 | Phase 235: DB-first capability checks (fixes context bloat) |
| 2026-01-05 | Phase 236: Unconditional learning session start (fixes learning not capturing) |
