# Checkpoint - Compaction-Ready Progress Documentation

**Purpose**: Generate structured checkpoint for mid-project compaction with guaranteed resumption
**Command**: `/checkpoint` | "checkpoint" | "save progress"
**Status**: ✅ Production | **Phase 260.5**: Compaction resilience for code projects

---

## Why This Exists

**Problem**: Context compaction during active projects causes:
- Agent not loading correctly (defaults to generic, produces "terrible code")
- Lost progress tracking (what was done, what's next)
- Test state amnesia (which tests passing)
- File change tracking lost

**Solution**: Structured checkpoint with explicit agent restoration protocol

---

## Usage

```bash
# Interactive (prompts for phase info)
/checkpoint

# With phase context
/checkpoint Phase 260 Timeline Persistence

# Quick checkpoint (auto-detect everything)
/checkpoint --auto
```

---

## Protocol Steps

### Step 1: Gather Project State
Auto-detect:
```bash
# Git changes
git diff --name-status          # Unstaged
git diff --name-status --cached # Staged

# Test status
pytest tests/ -v --tb=short 2>&1 | tail -20

# Token usage (from context metadata)
# Current agent (from session)
CONTEXT_ID=$(python3 claude/hooks/swarm_auto_loader.py get_context_id)
cat ~/.maia/sessions/swarm_session_${CONTEXT_ID}.json

# TDD phase (prompt if code changes detected)
```

### Step 2: Detect Project Type
```bash
# Code project indicators
if [[ $(git diff --name-only | grep -E '\.(py|ts|js|go)$') ]]; then
  PROJECT_TYPE="code"
  RECOMMENDED_AGENT="sre_principal_engineer_agent"
else
  PROJECT_TYPE="docs"
  RECOMMENDED_AGENT="current_agent_or_default"
fi
```

### Step 3: Generate Checkpoint Document

**Location**: `/tmp/CHECKPOINT_PHASE_{N}_{M}.md` (auto-increment M if exists)

**Template**:
```markdown
# Phase {N}: {Name} - Checkpoint {M}

**Date**: {ISO_TIMESTAMP}
**Status**: {COMPLETED_DESC} ({PERCENT}% done)
**Tests Passing**: {PASS}/{TOTAL} ({DETAILS})
**Agent**: {CURRENT_AGENT}
**TDD Phase**: {P0-P6.5}
**Token Usage**: {CURRENT}/{MAX} ({REMAINING} remaining)

---

## Completed Components

{AUTO_GENERATE_FROM_GIT_COMMITS_OR_USER_INPUT}

### 1. {Component_Name}
✅ {File_or_Action}:
- {Detail_1}
- {Detail_2}

**Tests**: {Relevant_tests_passing}

---

## In Progress

{CURRENT_ATOMIC_OPERATION}

### {Component_Name}
🔄 {Current_task}:
- Status: {RED|YELLOW|GREEN}
- Blocker: {None_or_description}

---

## Next Steps (Remaining {PERCENT}%)

{AUTO_GENERATE_FROM_TODOS_OR_USER_INPUT}

### {N}. {Component_Name}
- {Action_1}
- {Action_2}

---

## Files Modified/Created

**Modified** ({M} files):
{GIT_DIFF_M_FILES}

**Created** ({A} files):
{GIT_DIFF_A_FILES}

**Deleted** ({D} files):
{GIT_DIFF_D_FILES}

---

## Test Coverage

```
{PYTEST_OUTPUT_SUMMARY}
```

**Total**: {PASS}/{TOTAL} tests passing

---

## Resume Instructions ⚠️ CRITICAL FOR POST-COMPACTION

### Step 1: Restore Agent (MANDATORY for code projects)
```bash
# Ensure SRE agent loads (prevents terrible code from generic agent)
/init sre
```

**Why**: After compaction, agent session may not persist. Without SRE agent, code quality degrades significantly.

### Step 2: Load Checkpoint Context
```bash
# Read this file
cat /tmp/CHECKPOINT_PHASE_{N}_{M}.md

# Verify git state matches checkpoint
git status
```

### Step 3: Verify Environment
```bash
# Run tests to confirm state
pytest tests/ -v --tb=short

# Expected: {PASS}/{TOTAL} passing (same as checkpoint)
```

### Step 4: Continue from Exact Point
**Next Action**: {EXACT_NEXT_STEP}

{ADDITIONAL_CONTEXT_FOR_RESUMPTION}

### Step 5: Update Checkpoint When Phase Complete
```bash
# After completing next component
/checkpoint  # Generates CHECKPOINT_PHASE_{N}_{M+1}.md
```

---

## Git State at Checkpoint

```
{GIT_STATUS_OUTPUT}
```

**Branch**: {CURRENT_BRANCH}
**Last Commit**: {LAST_COMMIT_HASH_AND_MESSAGE}

---

## Context Metadata

| Property | Value |
|----------|-------|
| Context ID | {CONTEXT_ID} |
| Session Start | {SESSION_START} |
| Agent | {CURRENT_AGENT} |
| Domain | {DOMAIN} |
| TDD Phase | {TDD_PHASE} |
| Atomic Op | {CURRENT_ATOMIC_OP} |
| Checkpoint Time | {ISO_TIMESTAMP} |

---

## Compaction Safety Checklist

Before compaction occurs, verify:
- ✅ This checkpoint file saved to `/tmp/`
- ✅ Git changes staged (or documented as WIP)
- ✅ Current atomic operation COMPLETE (not mid-edit)
- ✅ Tests in known state (documented pass/fail counts)
- ✅ Resume instructions include `/init sre` for code projects
- ✅ Next action is EXPLICIT (not vague)

---

## Auto-Recovery Protocol

If compaction happens unexpectedly:

1. **Check for checkpoint**: `ls -lt /tmp/CHECKPOINT_* | head -1`
2. **Restore agent**: `/init sre` (for code projects)
3. **Read checkpoint**: Review completed/next sections
4. **Verify state**: `git status` + `pytest` should match checkpoint
5. **Resume**: Execute "Next Action" from resume instructions

---

## Integration with Existing Tools

- **feature_tracker.py**: Checkpoint can parse feature list for progress %
- **save_state.py**: Run after checkpoint to commit progress
- **close-session**: Checkpoints reviewed during pre-shutdown
- **context_monitor.py**: Triggers checkpoint at 70% token usage

---

## Example Output

See `/tmp/CHECKPOINT_PHASE_260_1.md` for real-world example structure.

---

## Key Rules

1. **ALWAYS include `/init sre`** in resume instructions for code projects
2. **NEVER checkpoint mid-atomic-operation** (finish current edit/test/commit)
3. **EXPLICIT next actions** (not "continue working on X")
4. **Auto-increment checkpoint numbers** (don't overwrite)
5. **Test counts MUST match** between checkpoint and verification
6. **Git state documented** (staged vs unstaged vs untracked)

---

## Command Implementation

The command should:
1. Auto-detect project state (git, tests, agent, tokens)
2. Prompt for: Phase name, % complete, what's done, what's next
3. Generate markdown using template above
4. Save to `/tmp/CHECKPOINT_PHASE_{N}_{M}.md`
5. Display: "Checkpoint saved. Resume with: cat /tmp/CHECKPOINT_PHASE_{N}_{M}.md && /init sre"

---

## Related Commands

- `/init` - Restore UFC + agent (CRITICAL for post-compaction)
- `/save_state` - Commit progress with doc enforcement
- `/close-session` - Pre-shutdown workflow
- `save progress` - Alias for checkpoint

---

## Technical Notes

- Checkpoint files in `/tmp/` survive compaction (not in repo)
- Auto-increment prevents overwriting previous checkpoints
- Agent restoration is MANDATORY for code quality post-compaction
- TDD phase tracking enables resuming at correct gate
- Atomic operation tracking prevents partial work resumption
