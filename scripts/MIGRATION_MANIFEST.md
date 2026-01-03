# Maia Migration Manifest

Detailed specification of where every file/directory goes in the new structure.

## Legend

| Action | Meaning |
|--------|---------|
| **REPO** | Keep in shared repository (maia/) |
| **USER** | Move to user directory (~/.maia/) - NOT in git |
| **REGEN** | Delete - regenerates locally from source |
| **TEMPLATE** | Keep template in repo, user creates own |
| **WORK** | Move to ~/work_projects/ - NOT in git |
| **DELETE** | Remove entirely (obsolete/temp) |

---

## Directory Structure

### Root Level

| Path | Action | Notes |
|------|--------|-------|
| `CLAUDE.md` | REPO | System instructions |
| `SYSTEM_STATE.md` | REPO | Phase history |
| `VERSION` | REPO | Version tracking |
| `CHANGELOG.md` | REPO | Change history |
| `requirements.txt` | REPO | Dependencies |
| `requirements-dev.txt` | REPO | Dev dependencies |
| `.gitignore` | REPO | Git exclusions |
| `.github/` | REPO | CI/CD, CODEOWNERS |

### claude/agents/

| Path | Action | Notes |
|------|--------|-------|
| `claude/agents/*.md` | REPO | All agent definitions |

### claude/commands/

| Path | Action | Notes |
|------|--------|-------|
| `claude/commands/*.md` | REPO | Slash commands |

### claude/context/

| Path | Action | Notes |
|------|--------|-------|
| `claude/context/ufc_system.md` | REPO | Core UFC system |
| `claude/context/core/` | REPO | Core context (identity, protocols) |
| `claude/context/tools/` | REPO | Tool documentation |
| `claude/context/session/` | DELETE | Temp session data |
| `claude/context/personal/` | **TEMPLATE** | See below |

#### Personal Context (TEMPLATE)

| In Repo | User Creates At |
|---------|-----------------|
| `claude/context/personal/TEMPLATE_profile.md` | `~/.maia/context/personal/profile.md` |
| `claude/context/personal/.gitkeep` | - |

**Current personal files to REMOVE from repo:**
- `claude/context/personal/profile.md` → User creates own
- `claude/context/personal/linkedin_ai_transformation_guide.md` → User's own

### claude/data/

| Path | Action | Notes |
|------|--------|-------|
| `claude/data/project_status/` | REPO | Phase documentation |
| `claude/data/ab_tests/` | REPO | Test scenarios (shared) |
| `claude/data/email_commands/` | USER | Personal email data |
| `claude/data/ir_findings/` | WORK | Incident reports (outputs) |
| `claude/data/transcripts/` | USER | Personal meeting transcripts |
| `claude/data/llm_routing_log.jsonl` | DELETE | Runtime log |
| `claude/data/model_usage_log.txt` | DELETE | Runtime log |
| `claude/data/dashboard_registry.db` | REGEN | Regenerates |
| `claude/data/capability_cache.json` | REGEN | Regenerates |
| `claude/data/context_state.json` | DELETE | Session state |
| `claude/data/user_preferences.json` | **USER** | → `~/.maia/data/user_preferences.json` |

#### claude/data/databases/

| Path | Action | Notes |
|------|--------|-------|
| `claude/data/databases/system/` | REGEN | System DBs regenerate from source |
| `claude/data/databases/intelligence/` | REGEN | Intelligence DBs regenerate |
| `claude/data/databases/user/` | **USER** | → `~/.maia/data/databases/user/` |

**User databases (move to ~/.maia/):**
- `*_naythan.db` files
- `personal_knowledge_graph.db`
- `preferences.db`

### claude/hooks/

| Path | Action | Notes |
|------|--------|-------|
| `claude/hooks/*.py` | REPO | All hooks |
| `claude/hooks/tests/` | REPO | Hook tests |

### claude/tools/

| Path | Action | Notes |
|------|--------|-------|
| `claude/tools/core/` | REPO | Core utilities |
| `claude/tools/sre/` | REPO | SRE tools |
| `claude/tools/security/` | REPO | Security tools |
| `claude/tools/automation/` | REPO | Automation tools |
| `claude/tools/business/` | REPO | Business tools |
| `claude/tools/communication/` | REPO | Comm tools |
| `claude/tools/dashboards/` | REPO | Dashboard tools |
| `claude/tools/monitoring/` | REPO | Monitoring tools |
| `claude/tools/servicedesk/` | REPO | ServiceDesk tools |
| `claude/tools/experimental/` | REPO | Experimental (keep .gitkeep) |
| `claude/tools/archive/` | REPO | Archived tools |

### claude/extensions/

| Path | Action | Notes |
|------|--------|-------|
| `claude/extensions/` | REPO | Keep .gitkeep only |

### claude/infrastructure/

| Path | Action | Notes |
|------|--------|-------|
| `claude/infrastructure/` | REPO | Infrastructure code |
| `claude/infrastructure/*/.env` | DELETE | Local env files |

### scripts/

| Path | Action | Notes |
|------|--------|-------|
| `scripts/hooks/` | REPO | Git hooks |
| `scripts/setup-team-member.sh` | REPO | Setup script |
| `scripts/migrate-to-fresh-repo.sh` | REPO | Migration script |

### tests/

| Path | Action | Notes |
|------|--------|-------|
| `tests/` | REPO | All tests |

---

## Session Files

| Location | Notes |
|----------|-------|
| `~/.maia/sessions/swarm_session_*.json` | Agent session state (per-context) |
| `~/.maia/data/checkpoints/*.json` | State checkpoints |
| `/tmp/maia_*` (legacy) | Automatically migrated on first access |

---

## Files to Create Templates For

| Template (in repo) | User file (in ~/.maia/) |
|--------------------|-------------------------|
| `claude/context/personal/TEMPLATE_profile.md` | `~/.maia/context/personal/profile.md` |
| `claude/data/TEMPLATE_user_preferences.json` | `~/.maia/data/user_preferences.json` |

---

## Summary Counts

| Action | Estimated Items |
|--------|-----------------|
| REPO | ~500+ files |
| USER | ~20 files |
| REGEN | ~15 databases |
| TEMPLATE | 2 templates |
| DELETE | ~30 temp/log files |
| WORK | ~10 output files |

---

## Migration Script Actions

The migration script should:

1. **Copy REPO files** to new location
2. **Create templates** from personal files (strip personal data)
3. **Skip USER files** (not copied to repo)
4. **Delete REGEN files** (will regenerate)
5. **Delete DELETE files** (temp/logs)
6. **Create .gitkeep** in empty directories
7. **Scan for remaining personal data** and warn

---

## Post-Migration: Setup Script Actions

The `setup-team-member.sh` script should:

1. Create `~/.maia/` directory structure
2. Copy templates to user location
3. Prompt user to fill in profile
4. Install git hooks
5. Generate local databases
