# Tier 2: Standard Save State (10-15 min)

**When to use**: End of work session, completing logical unit of work, ready to document properly

**Philosophy**: Balance between thoroughness and efficiency - document what matters without excessive overhead

---

## Steps

### 1. Update SYSTEM_STATE.md (5 min)
Add complete phase entry OR update existing phase with substantive progress:

```markdown
## 📊 PHASE NNN: [Phase Name] (YYYY-MM-DD)

### Achievement
**[One-line summary of what was accomplished]**

### Problem Solved
[Brief description of the problem or user request]

### Solution
[Key implementation details - 2-3 paragraphs]

### Result
[Metrics, outcomes, what works now]

### Files Changed
- Created: [list new files]
- Modified: [list modified files]
```

### 2. Update capability_index.md (1 min)
Add any new tools/agents to Recent Capabilities section:

```markdown
### Phase NNN ([Date]) - [Phase Name]
- [tool_name.py] - [One-line description with key feature]
- [agent_name] - [Purpose and specialization]
```

### 3. Update README.md IF major capabilities changed (2 min)
**Only if** changes affect user-facing features or major system capabilities:

- Add new features to relevant sections
- Update capability descriptions
- Keep concise (reference SYSTEM_STATE.md for details)

**Skip if**: Internal refactoring, bug fixes, minor enhancements

### 4. Run security check (1 min)
```bash
python3 claude/tools/sre/save_state_security_checker.py --verbose
```

**Action on warnings**: Review and fix any critical issues before committing

### 5. Git commit with structured message (3 min)
```bash
git add -A
git commit -m "$(cat <<'EOF'
🎯 PHASE NNN: [Title]

Achievement: [One-line summary]
Result: [Key metrics/outcomes]
Status: ✅ [Complete/In Progress/etc]

[Optional: Additional details if needed]

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
git push
```

---

## What to SKIP

- ❌ Pre-flight checks (rarely catch issues, use for major releases)
- ❌ available.md / agents.md detailed updates (unless tools/agents actually changed significantly)
- ❌ Session summaries (use for complex multi-day work)
- ❌ Design decision JSON (use for architectural decisions only)
- ❌ Comprehensive testing (use Tier 3 for releases)

---

## Example Workflow

```bash
# 1. Update SYSTEM_STATE.md with full phase entry
# (Edit manually with achievement, problem, solution, result)

# 2. Update capability_index.md
# Add: - disaster_recovery_system.py - Full system backup + OneDrive sync

# 3. Skip README (internal tool, not user-facing)

# 4. Security check
python3 claude/tools/sre/save_state_security_checker.py --verbose
# Output: ✅ Passed

# 5. Commit
git add -A
git commit -m "$(cat <<'EOF'
🎯 PHASE 114: Disaster Recovery System

Achievement: Built automated backup system with OneDrive sync
Result: 100% coverage of critical data, daily automated backups
Status: ✅ Complete

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
git push
```

**Total Time**: 10-15 minutes
**Token Cost**: ~2,000 tokens
**Use Case**: End of session, logical completion points

---

## When to Upgrade to Tier 3

- End of major phase (10+ changes)
- Weekly review or sprint completion
- Architecture changes
- Pre-release validation
- Significant system changes requiring comprehensive documentation

---

## When to Downgrade to Tier 1

- Making incremental changes within same session
- Quick bug fixes during active development
- Small iterations during prototyping
