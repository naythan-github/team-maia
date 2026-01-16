# Sprint Plan: Session Cleanup Robustness

**Sprint ID**: SPRINT-003-SESSION-CLEANUP
**Created**: 2026-01-16
**Status**: IN PROGRESS (P1-P5 COMPLETE, P6 DEFERRED)
**Priority**: HIGH (operational reliability)

---

## Objective

Fix session cleanup reliability issues identified by swarm review:
1. Fix EPERM bug causing false negatives in process detection
2. Preserve learning data when cleaning stale sessions
3. Add process name validation to prevent PID reuse false positives
4. Reduce cleanup threshold safely (with fixes in place)
5. Add heartbeat mechanism for robust crash detection
6. Migrate to UUID-based sessions (eliminates PID problems)

---

## Current State

| Component | Status | Issue |
|-----------|--------|-------|
| `is_process_alive()` | BUGGY | Treats PermissionError as "dead" |
| `cleanup_stale_sessions()` | BUGGY | Bypasses `_cleanup_session()`, loses learning data |
| Process validation | MISSING | No check if PID is actually Claude |
| Cleanup threshold | 24 hours | Too conservative for overnight crashes |
| Heartbeat mechanism | MISSING | Can't distinguish idle vs crashed |
| Session ID scheme | PID-based | Vulnerable to PID reuse |

---

## Sprint Phases (TDD)

### Phase 1: Fix EPERM Bug in `is_process_alive()`
**Agent**: `sre_principal_engineer_agent`
**Model**: Sonnet
**Effort**: Low (15 min)
**Risk**: Low

**Problem**: Current code treats `PermissionError` (EPERM) as "process dead" when it actually means "process exists but owned by another user".

| Step | Action |
|------|--------|
| 1.1 | Write failing test: `test_is_process_alive_eperm_returns_true` |
| 1.2 | Write failing test: `test_is_process_alive_esrch_returns_false` |
| 1.3 | Write failing test: `test_is_process_alive_negative_pid_returns_false` |
| 1.4 | Fix `is_process_alive()` to handle exceptions correctly |
| 1.5 | Run tests → GREEN |

**Files**:
- `tests/test_session_cleanup.py` (CREATE)
- `claude/hooks/swarm_auto_loader.py` (MODIFY lines 213-228)

**Test Template**:
```python
def test_is_process_alive_eperm_returns_true(self, mock_kill):
    """PermissionError means process exists but no permission - should return True."""
    mock_kill.side_effect = PermissionError("EPERM")
    assert is_process_alive(12345) is True

def test_is_process_alive_esrch_returns_false(self, mock_kill):
    """ProcessLookupError means process doesn't exist - should return False."""
    mock_kill.side_effect = ProcessLookupError("ESRCH")
    assert is_process_alive(12345) is False
```

---

### Phase 2: Fix Learning Data Loss in Cleanup
**Agent**: `sre_principal_engineer_agent`
**Model**: Sonnet
**Effort**: Low (15 min)
**Risk**: Low

**Problem**: `cleanup_stale_sessions()` calls `session_file.unlink()` directly, bypassing `_cleanup_session()` which captures learning data first.

| Step | Action |
|------|--------|
| 2.1 | Write failing test: `test_cleanup_captures_session_memory` |
| 2.2 | Write failing test: `test_cleanup_legacy_captures_memory` |
| 2.3 | Refactor `cleanup_stale_sessions()` to use `_cleanup_session()` |
| 2.4 | Run tests → GREEN |

**Files**:
- `tests/test_session_cleanup.py` (EXTEND)
- `claude/hooks/swarm_auto_loader.py` (MODIFY lines 262, 273)

**Code Change**:
```python
# Before (BUGGY):
session_file.unlink()

# After (CORRECT):
_cleanup_session(session_file)
```

---

### Phase 3: Add Process Name Validation
**Agent**: `sre_principal_engineer_agent`
**Model**: Sonnet
**Effort**: Medium (30 min)
**Risk**: Low

**Problem**: PID reuse means an unrelated process (Chrome, Slack) could keep an orphaned Claude session alive indefinitely.

| Step | Action |
|------|--------|
| 3.1 | Write failing test: `test_verify_claude_process_returns_true_for_claude` |
| 3.2 | Write failing test: `test_verify_claude_process_returns_false_for_other` |
| 3.3 | Write failing test: `test_verify_claude_process_handles_ps_failure` |
| 3.4 | Implement `verify_claude_process(pid)` function |
| 3.5 | Integrate into `cleanup_stale_sessions()` |
| 3.6 | Run tests → GREEN |

**Files**:
- `tests/test_session_cleanup.py` (EXTEND)
- `claude/hooks/swarm_auto_loader.py` (ADD function, MODIFY cleanup logic)

**New Function**:
```python
def verify_claude_process(pid: int) -> bool:
    """Verify PID belongs to Claude Code process, not an unrelated process."""
    if not is_process_alive(pid):
        return False
    try:
        result = subprocess.run(
            ['ps', '-p', str(pid), '-o', 'comm='],
            capture_output=True, text=True, timeout=0.5
        )
        if result.returncode == 0:
            comm = result.stdout.strip().lower()
            return 'claude' in comm or 'native-binary' in comm
    except Exception:
        pass
    return True  # Conservative: assume alive if can't verify
```

---

### Phase 4: Reduce Cleanup Threshold to 4 Hours
**Agent**: `sre_principal_engineer_agent`
**Model**: Sonnet
**Effort**: Low (10 min)
**Risk**: Low (after P1-P3 fixes)

**Prerequisite**: P1, P2, P3 must be complete and tested.

| Step | Action |
|------|--------|
| 4.1 | Update test: `test_stale_session_cleanup` to use 5-hour-old file |
| 4.2 | Update test: `test_recent_session_preserved` to use 3-hour-old file |
| 4.3 | Write test: `test_threshold_boundary_4_hours` |
| 4.4 | Change threshold from 24 to 4 hours |
| 4.5 | Run tests → GREEN |

**Files**:
- `tests/test_session_cleanup.py` (EXTEND)
- `tests/test_multi_context_isolation.py` (MODIFY - update existing tests)
- `claude/hooks/swarm_auto_loader.py` (MODIFY line 2161)

---

### Phase 5: Add Heartbeat Mechanism
**Agent**: `devops_principal_architect_agent`
**Model**: Sonnet
**Effort**: High (2-3 hours)
**Risk**: Medium

**Problem**: Time-based cleanup can't distinguish "alive but idle" from "crashed". Heartbeat provides active liveness signal.

| Step | Action |
|------|--------|
| 5.1 | Write failing test: `test_session_includes_heartbeat_field` |
| 5.2 | Write failing test: `test_update_heartbeat_modifies_timestamp` |
| 5.3 | Write failing test: `test_is_session_stale_by_heartbeat` |
| 5.4 | Write failing test: `test_cleanup_uses_heartbeat_over_mtime` |
| 5.5 | Add `last_heartbeat` field to session schema |
| 5.6 | Implement `update_session_heartbeat()` function |
| 5.7 | Implement `is_session_stale_by_heartbeat()` function |
| 5.8 | Integrate heartbeat into existing hook (e.g., `dynamic_context_loader.py`) |
| 5.9 | Modify `cleanup_stale_sessions()` to check heartbeat |
| 5.10 | Run tests → GREEN |

**Files**:
- `tests/test_session_cleanup.py` (EXTEND)
- `tests/test_session_heartbeat.py` (CREATE)
- `claude/hooks/swarm_auto_loader.py` (MODIFY - add heartbeat functions)
- `claude/hooks/dynamic_context_loader.py` (MODIFY - call heartbeat update)

**Session Schema Update**:
```json
{
  "current_agent": "sre_principal_engineer_agent",
  "last_heartbeat": "2026-01-16T06:30:00Z",
  "heartbeat_interval_seconds": 300,
  ...
}
```

**Cleanup Logic Update**:
```python
def is_session_stale(session_file: Path, max_missed_heartbeats: int = 3) -> bool:
    """Check if session is stale based on heartbeat, falling back to mtime."""
    try:
        with open(session_file) as f:
            data = json.load(f)
        if 'last_heartbeat' in data:
            interval = data.get('heartbeat_interval_seconds', 300)
            max_age = interval * max_missed_heartbeats
            last_hb = datetime.fromisoformat(data['last_heartbeat'])
            return (datetime.utcnow() - last_hb).total_seconds() > max_age
    except Exception:
        pass
    # Fallback to mtime-based check
    return session_file.stat().st_mtime < (time.time() - 4 * 3600)
```

---

### Phase 6: Migrate to UUID-Based Sessions
**Agent**: `software_architect_agent`
**Model**: Opus (architectural decision)
**Effort**: High (4-6 hours)
**Risk**: Medium (migration complexity)

**Problem**: PID-based session IDs are fundamentally vulnerable to PID reuse. UUIDs eliminate this class of problems entirely.

| Step | Action |
|------|--------|
| 6.1 | Design: Write ADR for UUID migration |
| 6.2 | Write failing test: `test_create_session_id_is_uuid_format` |
| 6.3 | Write failing test: `test_uuid_session_file_naming` |
| 6.4 | Write failing test: `test_legacy_pid_session_migration` |
| 6.5 | Write failing test: `test_env_var_session_id_propagation` |
| 6.6 | Implement `create_session_id()` with UUID format |
| 6.7 | Modify `get_context_id()` to prefer UUID over PID |
| 6.8 | Implement migration logic for existing PID sessions |
| 6.9 | Update all session file operations to use new naming |
| 6.10 | Add `MAIA_SESSION_ID` env var propagation |
| 6.11 | Run tests → GREEN |
| 6.12 | Run integration tests across multiple contexts |

**Files**:
- `claude/context/architecture/adr_uuid_sessions.md` (CREATE)
- `tests/test_session_cleanup.py` (EXTEND)
- `tests/test_uuid_session_migration.py` (CREATE)
- `claude/hooks/swarm_auto_loader.py` (MAJOR MODIFY)
- `claude/tools/sre/repo_validator.py` (MODIFY - if needed)
- `CLAUDE.md` (UPDATE - document new session format)

**UUID Format**:
```python
def create_session_id() -> str:
    """Generate globally unique session ID."""
    return f"s_{datetime.utcnow():%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:8]}"
    # Example: s_20260116_063000_a8b3f2c1
```

**Migration Strategy**:
1. New sessions get UUID-based IDs
2. Legacy PID sessions detected by numeric-only context_id
3. Legacy sessions migrated on first access (rename file + update internal ID)
4. Grace period: 30 days before removing legacy support

---

## Dependencies

```
P1 (EPERM fix) ──┐
P2 (Learning)  ──┼──→ P4 (Threshold) ──→ P5 (Heartbeat) ──→ P6 (UUID)
P3 (Process)   ──┘
```

- P1, P2, P3 can run in parallel
- P4 requires P1, P2, P3 complete
- P5 requires P4 complete
- P6 requires P5 complete (or can run in parallel with P5)

---

## Test File Structure

```
tests/
├── test_session_cleanup.py        # P1-P4 tests (CREATE)
├── test_session_heartbeat.py      # P5 tests (CREATE)
├── test_uuid_session_migration.py # P6 tests (CREATE)
├── test_multi_context_isolation.py # (MODIFY existing)
└── test_phase_134_5_session_discovery_fix.py # (VERIFY still passes)
```

---

## Rollback Plan

Each phase is independently deployable and revertible:

| Phase | Rollback |
|-------|----------|
| P1 | Revert exception handling (tests will catch regressions) |
| P2 | Revert to direct `unlink()` (learning loss acceptable short-term) |
| P3 | Remove `verify_claude_process()` calls (falls back to PID-only) |
| P4 | Change threshold back to 24 hours |
| P5 | Remove heartbeat checks (falls back to mtime-based) |
| P6 | Continue supporting PID sessions indefinitely |

---

## Success Criteria

| Metric | Before | After |
|--------|--------|-------|
| Orphaned sessions after crash | Accumulate for 24h | Cleaned within 4h |
| Learning data from crashed sessions | Lost | Captured |
| PID reuse false positives | Possible | Prevented |
| Session detection accuracy | ~95% | ~99.9% |

---

## References

- Swarm Review: Python Code Reviewer (agent a58d42c)
- Swarm Review: DevOps/SRE (agent a8b8dc1)
- Swarm Review: Architecture (agent af11f8a)
- Related: SPRINT-001-REPO-SYNC (multi-repo validation)
- Related: SPRINT-002-PROMPT-CAPTURE (learning system)
