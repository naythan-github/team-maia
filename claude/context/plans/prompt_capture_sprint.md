# Sprint Plan: Prompt Capture for Learning System

**Sprint ID**: SPRINT-002-PROMPT-CAPTURE
**Created**: 2026-01-15
**Completed**: 2026-01-15
**Status**: COMPLETE

---

## Objective

Capture all user prompts during sessions for:
1. **Primary**: Team sharing - export conversation history
2. **Secondary**: Learning system enhancement - pattern analysis, prompt effectiveness

---

## Current State

| Component | Status |
|-----------|--------|
| `UserPromptSubmit` hook | ❌ Not configured |
| Prompt storage | ❌ Only `initial_query` (first prompt) |
| Search capability | ❌ None |
| Export capability | ❌ None |

---

## Sprint Phases (TDD)

### Phase 1: Schema + Tests
**Model**: Sonnet
**Subagent**: None (direct implementation)
**Effort**: Low

| Step | Action |
|------|--------|
| 1.1 | Write failing tests for `session_prompts` table creation |
| 1.2 | Write failing tests for FTS5 virtual table |
| 1.3 | Implement `PROMPTS_SCHEMA` in `schema.py` |
| 1.4 | Run tests → GREEN |

**Files**:
- `tests/learning/test_prompt_capture.py` (CREATE - test stubs)
- `claude/tools/learning/schema.py` (MODIFY)

---

### Phase 2: Memory APIs + Tests
**Model**: Sonnet
**Subagent**: None (direct implementation)
**Effort**: Medium

| Step | Action |
|------|--------|
| 2.1 | Write failing tests for `capture_prompt()` |
| 2.2 | Write failing tests for `get_prompts_for_session()` |
| 2.3 | Write failing tests for `search_prompts()` |
| 2.4 | Implement methods in `memory.py` |
| 2.5 | Run tests → GREEN |

**Files**:
- `tests/learning/test_prompt_capture.py` (EXTEND)
- `claude/tools/learning/memory.py` (MODIFY)

---

### Phase 3: Hook Implementation
**Model**: Sonnet
**Subagent**: None (direct implementation)
**Effort**: Medium

| Step | Action |
|------|--------|
| 3.1 | Write failing tests for hook processing |
| 3.2 | Write failing tests for session resolution |
| 3.3 | Write failing tests for non-blocking behavior |
| 3.4 | Implement `prompt_capture.py` hook |
| 3.5 | Run tests → GREEN |

**Files**:
- `tests/learning/test_prompt_capture.py` (EXTEND)
- `claude/hooks/prompt_capture.py` (CREATE)

---

### Phase 4: Export System
**Model**: Sonnet
**Subagent**: None (direct implementation)
**Effort**: Low

| Step | Action |
|------|--------|
| 4.1 | Write failing tests for JSONL export |
| 4.2 | Write failing tests for Markdown export |
| 4.3 | Write failing tests for CSV export |
| 4.4 | Implement `prompt_export.py` |
| 4.5 | Run tests → GREEN |

**Files**:
- `tests/learning/test_prompt_capture.py` (EXTEND)
- `claude/tools/learning/prompt_export.py` (CREATE)

---

### Phase 5: Hook Configuration
**Model**: Sonnet
**Subagent**: None (direct implementation)
**Effort**: Low

| Step | Action |
|------|--------|
| 5.1 | Update `~/.claude/settings.json` with UserPromptSubmit hook |
| 5.2 | Manual integration test |

**Files**:
- `~/.claude/settings.json` (MODIFY)

---

### Phase 6: Integration Verification
**Model**: Sonnet
**Subagent**: Explore (for verification)
**Effort**: Low

| Step | Action |
|------|--------|
| 6.1 | Run full test suite |
| 6.2 | Manual E2E test: `/init` → prompts → query DB |
| 6.3 | Verify export works |
| 6.4 | Update CLAUDE.md if needed |

---

## Model Selection Rationale

| Phase | Model | Reason |
|-------|-------|--------|
| 1-6 | Sonnet | Consistent quality, FTS5 triggers need precision, marginal Haiku savings not worth risk |

---

## Subagent Usage

| Phase | Subagent | Reason |
|-------|----------|--------|
| 1-5 | None | Direct implementation, well-scoped |
| 6 | Explore | Verify integration across files |

---

## Success Criteria

- [x] All tests pass: `pytest tests/learning/test_prompt_capture.py -v` (28/28 PASSED)
- [x] Hook configured in ~/.claude/settings.json
- [x] Prompts visible in DB: `sqlite3 ~/.maia/memory/memory.db "SELECT * FROM session_prompts"`
- [x] Search works: `memory.search_prompts("keyword")`
- [x] Export works: All 3 formats (JSONL, MD, CSV)

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Hook slows prompt submission | <50ms target, non-blocking design |
| Missing session on capture | Graceful skip with logging |
| DB errors | Catch/log, never block user |
| Backward compatibility | Auto-create table on first access |

---

## Estimated Effort

| Phase | Time |
|-------|------|
| Phase 1 | 10 min |
| Phase 2 | 20 min |
| Phase 3 | 20 min |
| Phase 4 | 15 min |
| Phase 5 | 5 min |
| Phase 6 | 10 min |
| **Total** | **~80 min** |

---

## Approval

Ready to proceed with Phase 1?
