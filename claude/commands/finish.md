# Finish - Completion Verification Skill

## Purpose
Validate that work is truly complete before declaring "done". Unlike `/complete`, this skill **blocks** on failures and requires **mandatory interactive review** with evidence. Completion state is persisted for audit trails.

## Usage
```
/finish              # Full verification workflow
/finish --quick      # Essential checks only (git + capabilities + testing)
```

## When to Use
- **Before saying "done", "complete", or "finished"**
- Before closing a session (`/close-session` will warn if not run)
- After implementing any new tool, agent, or command
- After multi-step development tasks
- End of any sprint or project phase

---

## Workflow Execution

### Phase 1: Automated Checks (6 checks)

Run all automated checks:
```bash
python3 claude/tools/sre/finish_checker.py summary
```

| Check | Detection | PASS | FAIL |
|-------|-----------|------|------|
| **Git Status** | `git status --short` | Clean tree | Uncommitted core files |
| **Capability Registration** | Cross-ref with capabilities.db | All registered | Missing entries |
| **Documentation** | Parse AST for docstrings | Module docstrings present | Missing docstrings |
| **Testing** | Check tests/ directory | Test files exist | Missing tests |
| **Learning Capture** | Check session manager | Session active | No session |
| **Pre-Integration** | `ruff check` | No E/F/W errors | Linting errors |

### Phase 2: Block on Failures

**CRITICAL**: If ANY check returns FAIL:

1. **Stop and display blockers**
2. **Must fix before proceeding**
3. **Re-run `/finish` after fixing**

```
Blockers (must fix):
  - capability: 2 unregistered file(s)
  - testing: 1 tool(s) missing test files

Fix these issues and run /finish again.
```

### Phase 3: Interactive Review (MANDATORY)

**You MUST answer all 4 questions with evidence.** Short answers like "No" or "None" will be rejected.

#### Question 1: CLAUDE.md Impact
```
Does CLAUDE.md need updating?

Acceptable responses:
- "No change needed - only added internal tool, no new principle or workflow"
- "Updated: Added /finish to Key Commands section at line 145"
- "NEEDS UPDATE - new principle about completion verification needed"
```

#### Question 2: Dependent Systems
```
Are dependent systems affected?

Acceptable responses:
- "Checked: swarm_auto_loader.py, close-session.md, init.md - no impact"
- "Updated: close-session.md now references /finish warning"
- "None - this is a standalone tool with no integrations"
```

#### Question 3: Ripple Effects
```
Any ripple effects to consider?

Acceptable responses:
- "Verified: No other tools use completion checking pattern"
- "Checked related: feature_tracker.py, save_state.py - patterns compatible"
- "None identified - new isolated functionality"
```

#### Question 4: Documentation Completeness
```
All documentation complete?

Acceptable responses:
- "Complete: docstrings in place, test file created, capability registered"
- "Updated: capability_index.md, SYSTEM_STATE.md phase entry added"
- "Complete: module docstring, function docstrings, inline comments for complex logic"
```

### Phase 4: Persist Completion

After all checks pass and review complete:
```bash
python3 claude/tools/sre/finish_checker.py persist \
  --session-id $(python3 claude/hooks/swarm_auto_loader.py get_context_id) \
  --context-id $(python3 claude/hooks/swarm_auto_loader.py get_context_id) \
  --project "PROJECT_NAME" \
  --agent "AGENT_NAME"
```

---

## Output Format

```
/finish Checklist
==================================================

✅ Git Status                     [PASS]
   Working tree clean

✅ Capability                     [PASS]
   All 3 recent file(s) registered

⚠️  Documentation                  [WARN]
   1 file(s) missing full documentation

✅ Testing                        [PASS]
   All 2 tool(s) have test files

✅ Learning                       [PASS]
   Learning session active: s_20260115_120000

✅ Pre Integration                [PASS]
   ruff check passed (no E/F/W errors)

==================================================
Result: 5/6 PASS | 1 WARN | 0 FAIL

Interactive Review Required:
1. CLAUDE.md impact? ______________________
2. Dependent systems? _____________________
3. Ripple effects? ________________________
4. Documentation complete? ________________
```

---

## Blocking Behavior

### Circuit Breaker
After 5 consecutive FAIL runs:
- **Escalates to human intervention**
- Message: "Circuit breaker triggered - requires manual review"
- Must acknowledge and reset before continuing

### What Blocks vs Warns

| Status | Behavior | Example |
|--------|----------|---------|
| **FAIL** | Blocks completion | Missing test file, unregistered tool |
| **WARN** | Shows warning, allows continuation | Minor uncommitted changes, no active session |
| **PASS** | Proceeds | All checks satisfied |

---

## Session Integration

### Before `/close-session`
The `/close-session` command checks for `/finish` completion:
```
⚠️  Warning: /finish was not run for this session.
    Run /finish to verify completion before closing.
```

### Completion State
Records stored in `project_tracking.db`:
- Session ID linkage (audit trail)
- Check results (JSON)
- Review responses (JSON)
- Files touched
- Status (COMPLETE/BLOCKED/ESCALATED)

Query past completions:
```bash
sqlite3 claude/data/databases/system/project_tracking.db \
  "SELECT * FROM v_recent_completions"
```

---

## Technical Details

### Files
| Component | Path |
|-----------|------|
| Core Tool | `claude/tools/sre/finish_checker.py` |
| DB Schema | `claude/tools/sre/finish_schema.sql` |
| This Skill | `claude/commands/finish.md` |
| Database | `claude/data/databases/system/project_tracking.db` |

### Classes
- `FinishChecker` - Main orchestrator
- `CheckResult` - Individual check result
- `CompletionRecord` - Persistence record

### Performance
- All 6 checks complete in <5 seconds
- Database writes are atomic
- Graceful degradation if components unavailable

---

## Comparison: `/complete` vs `/finish`

| Aspect | `/complete` | `/finish` |
|--------|-------------|-----------|
| Automated checks | ✅ 6 checks | ✅ Same 6 checks |
| Blocking on FAIL | ❌ Shows result only | ✅ **Blocks until fixed** |
| Interactive review | ⚠️ Optional | ✅ **Mandatory with evidence** |
| Persistence | ❌ None | ✅ Database records |
| Session integration | ❌ None | ✅ `/close-session` warns |
| Circuit breaker | ❌ None | ✅ After 5 failures |

---

## Related Commands

- `/complete` - Non-blocking completion checklist (predecessor)
- `/close-session` - Clean session shutdown (integrates with /finish)
- `/init` - Start new session
- `save state` - Documentation + git commit

---

## Success Criteria

Ready to declare "done" when:
- [ ] 0 FAIL items in automated checks
- [ ] All 4 review questions answered with evidence
- [ ] Completion record persisted
- [ ] `/close-session` shows no /finish warning
