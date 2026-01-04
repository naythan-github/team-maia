# Save State Command - Enforced Documentation Protocol

**Purpose**: Checkpoint system state with ENFORCED documentation updates + git commit
**Status**: ✅ Production Ready | **Phase 233**: Blocking enforcement active

---

## Quick Start

```bash
# Standard save (blocks if docs missing)
python3 claude/tools/sre/save_state.py

# Check what's needed without committing
python3 claude/tools/sre/save_state.py --check

# Emergency bypass (NOT RECOMMENDED)
python3 claude/tools/sre/save_state.py --force
```

---

## What It Enforces

### 1. Auto-Detection
The script automatically detects what changed:
- New tools in `claude/tools/` → requires capability_index.md
- New agents in `claude/agents/` → requires agents.md + capability_index.md
- Significant work (>5 files or new capabilities) → requires SYSTEM_STATE.md

### 2. Blocking Rules

| Change Detected | Required Documentation | Action if Missing |
|-----------------|----------------------|-------------------|
| New tools | capability_index.md | **BLOCK** |
| New agents | agents.md + capability_index.md | **BLOCK** |
| Significant work | SYSTEM_STATE.md | **BLOCK** |
| Security issues | Fix secrets | **BLOCK** |

### 3. Automatic Actions
- Syncs capabilities.db on every save
- Runs security check
- Generates structured commit message
- Pushes to remote

---

## Example Output

### Clean Save
```
============================================================
🔍 SAVE STATE - Documentation Enforcement
============================================================

📋 Analyzing changes...
   New tools: 2
   New agents: 0
   Modified files: 8

📝 Checking documentation updates...
   ✅ All required documentation updated

🔄 Syncing capabilities database...
   ✅ Capabilities DB synced: 569 tools, 95 agents

🔒 Running security check...
   ✅ Security check passed

💾 Committing changes...
   ✅ Committed: feat: 2 new tools

🚀 Pushing to remote...
   ✅ Pushed to remote

============================================================
✅ SAVE STATE COMPLETE
============================================================
```

### Blocked (Missing Docs)
```
============================================================
🔍 SAVE STATE - Documentation Enforcement
============================================================

📋 Analyzing changes...
   New tools: 7
   New agents: 0
   Modified files: 12

📝 Checking documentation updates...

❌ NEW TOOLS/AGENTS DETECTED but capability_index.md not updated:
   Tools: claude/tools/learning/schema.py, claude/tools/learning/uocs.py...
   → Add entries to claude/context/core/capability_index.md

❌ SIGNIFICANT WORK DETECTED but SYSTEM_STATE.md not updated:
   New tools: 7
   Modified files: 12
   → Add phase entry to SYSTEM_STATE.md

============================================================
🚫 BLOCKED: Update documentation before committing
   Use --force to bypass (NOT RECOMMENDED)
============================================================
```

---

## When to Use

| Situation | Action |
|-----------|--------|
| Created new tools/agents | Run save_state, update docs if blocked |
| Completed a feature | Run save_state |
| End of session | Run save_state |
| Quick checkpoint | `git commit` directly (minor changes only) |

---

## Bypass (Emergency Only)

```bash
python3 claude/tools/sre/save_state.py --force
```

⚠️ **Only use when**:
- Urgent fix needed
- Docs will be updated in next commit
- You understand the debt you're creating

---

## Related

- **capability_index.md**: Tool/agent registry
- **SYSTEM_STATE.md**: Phase history
- **close-session**: Pre-shutdown workflow
- **capabilities_registry.py**: Database sync
