# Tier 1: Quick Checkpoint (2-3 min)

**When to use**: Making incremental progress, multiple checkpoints per session, still in flow state

**Philosophy**: Minimum viable documentation to preserve context without breaking flow

---

## Steps

### 1. Update SYSTEM_STATE.md (1 min)
Add bullet to current phase section with brief change description:

```markdown
## 📊 PHASE NNN: [Current Phase Name]

### Recent Progress
- [DATE] [Brief description of what changed - 1 sentence]
```

### 2. Update capability_index.md IF new capability (30 sec)
Only if you created a new tool or agent:

```markdown
### Phase NNN ([Date])
- [tool_name.py] - [One-line description]
```

### 3. Consider compaction every 3rd checkpoint (optional)

**When**: This is your 3rd+ Tier 1 checkpoint AND session >40 messages

**Execute**: `/compact` to prevent hitting conversation length limits

**Skip**: First 2 checkpoints or session <40 messages

### 4. Git commit with short message (1 min)
```bash
git add -A
git commit -m "🔧 Phase NNN: [what changed in 5-10 words]"
git push
```

---

## What to SKIP

- ❌ Pre-flight checks (use for major changes only)
- ❌ Security validation (unless adding secrets/credentials)
- ❌ README updates (use Tier 2 for user-facing changes)
- ❌ available.md / agents.md updates (use Tier 2)
- ❌ Comprehensive phase documentation (use Tier 3)

---

## Example Workflow

```bash
# 1. Quick SYSTEM_STATE bullet
echo "- 2025-10-15 Added retry logic to backup script" >> SYSTEM_STATE.md

# 2. Skip capability_index (no new tool)

# 3. Quick commit
git add -A && git commit -m "🔧 Phase 114: Added retry logic to backup" && git push
```

**Total Time**: 2-3 minutes
**Token Cost**: ~500 tokens
**Use Case**: Incremental progress during active development

---

## When to Upgrade to Tier 2

- Completing a logical unit of work
- End of work session
- New capability needs full documentation
- Changes affect user-facing features
