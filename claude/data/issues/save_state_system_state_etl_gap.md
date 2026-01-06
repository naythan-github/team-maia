# Save State System State ETL Gap

**Date**: 2026-01-06
**Severity**: MEDIUM (Automation Gap)
**Status**: Requires SRE Fix

---

## Problem Summary

`save_state.py` automatically syncs `capabilities.db` but does NOT automatically sync `system_state.db` when SYSTEM_STATE.md is modified. This creates an incomplete automation loop where one database is synced but the other requires manual intervention.

### Current Behavior

When `save_state.py` runs:
- ✅ Auto-runs `capabilities_registry.py scan` (line 529)
- ❌ Does NOT run `system_state_etl.py` to sync system_state.db

### Expected Behavior

When `save_state.py` runs and SYSTEM_STATE.md is modified:
- ✅ Auto-run `capabilities_registry.py scan`
- ✅ Auto-run `system_state_etl.py` to sync SYSTEM_STATE.md → system_state.db

---

## Root Cause

`save_state.py` (Phase 233) was designed to sync capabilities.db but system_state.db ETL sync was not included in the automation scope.

**Evidence**:
```python
# Line 527-529 in save_state.py
# 3. Sync capabilities DB
print("🔄 Syncing capabilities database...")
sync_ok, sync_msg = self.sync_capabilities_db()
```

No corresponding `sync_system_state_db()` method exists.

---

## Impact

**When someone updates SYSTEM_STATE.md:**
1. Uses `save_state.py` to commit
2. `capabilities.db` syncs automatically ✅
3. `system_state.db` does NOT sync ❌
4. Developer must manually run `python3 claude/tools/sre/system_state_etl.py`
5. If forgotten, queries to system_state.db return stale data

**Real-world example (2026-01-06):**
- Added Phase 238 to SYSTEM_STATE.md
- Did not use save_state.py (manual workflow)
- Had to manually run both syncs separately
- User correctly identified this should be automatic

---

## Proposed Solution

### Add System State DB Sync to save_state.py

**Requirements**:
1. Detect when SYSTEM_STATE.md is modified
2. Auto-run `system_state_etl.py` when detected
3. Report sync status (success/failure)
4. Handle errors gracefully (non-blocking, like capabilities sync)
5. TDD implementation with tests

**Implementation Pattern** (follow existing `sync_capabilities_db()` at line 323):

```python
def sync_system_state_db(self) -> Tuple[bool, str]:
    """
    Sync system_state.db with SYSTEM_STATE.md.

    Returns:
        (success, message)
    """
    etl_path = self.maia_root / "claude" / "tools" / "sre" / "system_state_etl.py"

    if not etl_path.exists():
        return False, "system_state_etl.py not found"

    try:
        result = subprocess.run(
            ["python3", str(etl_path)],
            cwd=self.maia_root,
            capture_output=True,
            text=True,
            timeout=60  # ETL can be slower than capabilities scan
        )

        if result.returncode == 0:
            # Extract phase count from output
            output = result.stdout
            return True, f"✅ System State DB synced\n{output.strip()}"
        else:
            return False, f"⚠️ System State sync warning: {result.stderr}"

    except subprocess.TimeoutExpired:
        return False, "⚠️ System State sync timed out"
    except Exception as e:
        return False, f"⚠️ System State sync error: {e}"
```

**Integration Point** (after line 529):

```python
# 3. Sync capabilities DB
print("🔄 Syncing capabilities database...")
sync_ok, sync_msg = self.sync_capabilities_db()
print(f"   {sync_msg}")
print()

# 3b. Sync system state DB (if SYSTEM_STATE.md modified)
if analysis.system_state_modified:
    print("🔄 Syncing system state database...")
    state_sync_ok, state_sync_msg = self.sync_system_state_db()
    print(f"   {state_sync_msg}")
    print()
```

---

## Test Requirements

### Test 1: SYSTEM_STATE.md Modified → ETL Runs
```python
def test_system_state_sync_when_modified():
    # Given: SYSTEM_STATE.md has uncommitted changes
    # When: save_state.py runs
    # Then: system_state_etl.py executed, system_state.db synced
```

### Test 2: SYSTEM_STATE.md NOT Modified → ETL Skipped
```python
def test_system_state_sync_skipped_when_not_modified():
    # Given: SYSTEM_STATE.md unchanged
    # When: save_state.py runs
    # Then: system_state_etl.py NOT executed (optimization)
```

### Test 3: ETL Failure → Non-Blocking Warning
```python
def test_system_state_sync_failure_is_non_blocking():
    # Given: system_state_etl.py returns non-zero exit code
    # When: save_state.py runs
    # Then: Warning displayed, commit proceeds (like capabilities sync)
```

### Test 4: Both DBs Sync Together
```python
def test_both_databases_sync_in_single_run():
    # Given: New tool added + SYSTEM_STATE.md updated
    # When: save_state.py runs
    # Then: Both capabilities.db AND system_state.db synced
```

---

## Acceptance Criteria

- [ ] `sync_system_state_db()` method added to SaveState class
- [ ] Auto-runs when `analysis.system_state_modified == True`
- [ ] Skipped when SYSTEM_STATE.md unchanged (optimization)
- [ ] Errors are non-blocking (like capabilities sync)
- [ ] 4/4 tests passing
- [ ] No regressions in existing save_state.py tests
- [ ] Updated save_state.py docstring to mention both DB syncs
- [ ] Phase 233 entry updated in SYSTEM_STATE.md

---

## Files to Modify

- **`claude/tools/sre/save_state.py`** - Add `sync_system_state_db()` method
- **`tests/sre/test_save_state.py`** - Add 4 new tests (if file exists, else create)
- **`SYSTEM_STATE.md`** - Update Phase 233 entry to document both DB syncs

---

## References

- **Phase 233**: Save State Enforcement (SYSTEM_STATE.md line 198)
- **Existing sync method**: `sync_capabilities_db()` at save_state.py line 323
- **ETL script**: `claude/tools/sre/system_state_etl.py`
- **Related**: Phase 238 documentation update exposed this gap

---

**Next Steps**: Handoff to SRE Principal Engineer Agent for TDD implementation.
