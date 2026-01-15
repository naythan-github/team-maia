# /finish Skill Fix-Forward Project
**Sprint ID**: SPRINT-FINISH-FIXFORWARD-001
**Status**: READY TO EXECUTE
**Created**: 2026-01-15
**Priority**: High (blocks clean /finish runs)

---

## Context

The `/finish` skill was implemented successfully (34 tests passing). Running `/finish` revealed issues that need fix-forward resolution:

### Sprint Deliverables (Complete)
- `claude/tools/sre/finish_checker.py` - Core tool
- `claude/tools/sre/finish_schema.sql` - DB schema
- `claude/commands/finish.md` - Skill markdown
- `tests/test_finish_checker.py` - 26 unit tests
- `tests/integration/test_finish_integration.py` - 8 integration tests
- Session integration in `swarm_auto_loader.py`
- Documentation updates (CLAUDE.md, close-session.md, SRE agent)

---

## Issues to Fix

### 1. Git Status - Uncommitted Changes
**Status**: FAIL
**Files**:
```
M claude/agents/sre_principal_engineer_agent.md
M claude/commands/close-session.md
M claude/data/databases/system/capabilities.db
M claude/hooks/swarm_auto_loader.py
M CLAUDE.md
?? claude/commands/finish.md
?? claude/tools/sre/finish_checker.py
?? claude/tools/sre/finish_schema.sql
?? tests/test_finish_checker.py
?? tests/integration/test_finish_integration.py
```

**Fix**: Commit all changes with `save state`

### 2. Capability Check - Command Files
**Status**: FAIL (false positive)
**Issue**: `finish.md` and `close-session.md` flagged as unregistered
**Root Cause**: Capability check includes `claude/commands/` but commands are markdown skill definitions, not tools/agents

**Fix**: Update `finish_checker.py` to exclude `claude/commands/*.md` from capability registration check (they're not meant to be in capabilities.db)

### 3. Pre-existing Test Gaps
**Status**: FAIL (not from this sprint)
**Files missing tests**:
- `claude/tools/learning/prompt_export.py`
- `claude/tools/learning/schema.py`
- `claude/tools/pmp/pmp_query_templates.py`

**Fix**: Create test files (separate sprint or quick fix)

### 4. Learning Session Attribute
**Status**: WARN
**Issue**: `'SessionManager' object has no attribute 'current_session'`
**Root Cause**: SessionManager API changed, finish_checker using old attribute name

**Fix**: Update `finish_checker.py` to use correct SessionManager API

---

## Execution Plan

### Phase 1: Quick Fixes (10 min)
1. Fix capability check to exclude commands directory
2. Fix SessionManager attribute name

### Phase 2: Commit Sprint (5 min)
1. Run `save state` to commit all /finish sprint changes

### Phase 3: Test Gap Resolution (30 min, optional)
1. Create stub tests for pre-existing tools (prompt_export, schema, pmp_query_templates)

### Phase 4: Verify (5 min)
1. Run `/finish` again - should show all PASS or acceptable WARN

---

## Success Criteria

- [ ] `/finish` shows 0 FAIL items
- [ ] Git status clean after commit
- [ ] Capability check excludes command markdown files
- [ ] Learning check uses correct SessionManager API

---

## Files to Modify

| File | Change |
|------|--------|
| `claude/tools/sre/finish_checker.py` | Exclude commands/, fix SessionManager attr |
| (new) `tests/test_prompt_export.py` | Stub test (optional) |
| (new) `tests/test_schema.py` | Stub test (optional) |
| (new) `tests/test_pmp_query_templates.py` | Stub test (optional) |
