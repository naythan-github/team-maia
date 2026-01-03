# Maia Team Sharing Project Plan

**Created**: 2025-11-22
**Completed**: 2025-12-11
**Status**: ✅ COMPLETE (Phase 1 & 3) | ⏭️ Phase 2 Skipped (Optional)
**Estimated Effort**: 1-1.5 hours
**Priority**: When ready to share with team

---

## Problem Statement

Maia currently has:
1. **Nested repo structure**: `/git/` is repo root, `/git/maia/` is project folder
2. **136 files with hardcoded paths**: `/Users/naythandawe/git/maia/...`
3. **44 code occurrences** that will break on teammates' machines

These must be fixed before team can use Maia.

---

## Project Goals

1. ✅ Team can `git clone` and run Maia immediately
2. ✅ No hardcoded user-specific paths
3. ✅ Clean GitHub appearance (files at root, not in subfolder)
4. ✅ Portable across machines

---

## Phase 1: Fix Hardcoded Paths (MANDATORY)

**Effort**: 30-45 minutes
**Files affected**: 44 code occurrences across Python, shell, plist files

### Step 1.1: Create MAIA_ROOT pattern

Add to a central config or use Path-based resolution:

```python
# claude/tools/core/paths.py (new file)
from pathlib import Path
import os

def get_maia_root() -> Path:
    """Get Maia root directory - works on any machine."""
    # Option 1: Environment variable
    if "MAIA_ROOT" in os.environ:
        return Path(os.environ["MAIA_ROOT"])

    # Option 2: Derive from this file's location
    # This file is at: claude/tools/core/paths.py
    # Maia root is 3 levels up
    return Path(__file__).parent.parent.parent.parent

MAIA_ROOT = get_maia_root()
```

### Step 1.2: Find and replace patterns

| Pattern | Replacement | Count |
|---------|-------------|-------|
| `/Users/naythandawe/git/maia/claude/data/` | `MAIA_ROOT / "claude/data/"` | ~15 |
| `/Users/naythandawe/git/maia/claude/tools/` | `MAIA_ROOT / "claude/tools/"` | ~10 |
| `/Users/naythandawe/git/maia/claude/` | `MAIA_ROOT / "claude/"` | ~10 |
| `/Users/naythandawe/git/maia` (base) | `MAIA_ROOT` | ~9 |

### Step 1.3: Files requiring manual review

```
claude/tools/security/com.maia.security-orchestrator.plist  # LaunchAgent
claude/tools/whisper_health_monitor.sh                       # Shell script
claude/tools/start_vtt_watcher.sh                            # Shell script
claude/tools/stop_vtt_watcher.sh                             # Shell script
```

These need `$MAIA_ROOT` env var or relative paths.

### Step 1.4: Test on current machine

```bash
# Temporarily unset to simulate teammate
export MAIA_ROOT_BACKUP="$MAIA_ROOT"
unset MAIA_ROOT

# Test key tools
python3 claude/tools/sre/system_state_queries.py recent --count 5
python3 claude/tools/morning_email_intelligence_local.py --help

# Restore
export MAIA_ROOT="$MAIA_ROOT_BACKUP"
```

---

## Phase 2: Restructure Repository (OPTIONAL but recommended)

**Effort**: 5-10 minutes
**Prerequisite**: Phase 1 complete and tested

### Step 2.1: Install git-filter-repo

```bash
pip install git-filter-repo
```

### Step 2.2: Create backup

```bash
cd /Users/naythandawe/git
cp -r . ../git-backup-$(date +%Y%m%d)
```

### Step 2.3: Run filter-repo

```bash
cd /Users/naythandawe/git
git filter-repo --subdirectory-filter maia/ --force
```

This makes `maia/` contents become the repo root.

### Step 2.4: Force push

```bash
git push --force origin main
```

### Step 2.5: Re-clone to new location

```bash
cd ~
git clone https://github.com/naythan-orro/maia.git maia
cd maia
```

### Step 2.6: Update working directory

- Claude Code: Open new location
- Any scripts referencing old path: Update

---

## Phase 3: Team Onboarding Prep

**Effort**: 15-20 minutes

### Step 3.1: Create setup script

```bash
# setup.sh (new file at repo root)
#!/bin/bash
set -e

echo "Setting up Maia..."

# Set MAIA_ROOT
export MAIA_ROOT="$(cd "$(dirname "$0")" && pwd)"
echo "export MAIA_ROOT=\"$MAIA_ROOT\"" >> ~/.zshrc

# Install Python dependencies
pip install -r requirements.txt

# Verify installation
python3 claude/tools/sre/maia_comprehensive_test_suite.py --quick

echo "Maia setup complete!"
```

### Step 3.2: Create requirements.txt

Consolidate all Python dependencies.

### Step 3.3: Update README.md

```markdown
# Maia - My AI Agent

## Quick Start

1. Clone: `git clone https://github.com/naythan-orro/maia.git`
2. Setup: `./setup.sh`
3. Use with Claude Code

## Requirements
- Python 3.11+
- Claude Code CLI
- Ollama (for local LLMs)
```

### Step 3.4: Test fresh clone

```bash
# Simulate teammate
cd /tmp
git clone https://github.com/naythan-orro/maia.git maia-test
cd maia-test
./setup.sh
python3 claude/tools/sre/maia_comprehensive_test_suite.py
```

---

## Validation Checklist

### Phase 1 Complete ✅ (2025-12-11)
- [x] `paths.py` created with `get_maia_root()`
- [x] All 44 code occurrences updated (40+ files fixed)
- [x] LaunchAgents updated (plist files - portability note added)
- [x] Shell scripts use `$MAIA_ROOT`
- [x] Tests pass without hardcoded paths (294+ tests)

### Phase 2 Complete ⏭️ SKIPPED (Optional)
- [ ] Backup created
- [ ] filter-repo executed
- [ ] Force push successful
- [ ] Re-cloned to new location
- [ ] Claude Code working in new location

### Phase 3 Complete ✅ (2025-12-11)
- [x] setup.sh created and tested
- [x] requirements.txt complete (already existed)
- [x] README.md updated with Quick Start
- [x] Fresh clone test passes

---

## Rollback Plan

### If Phase 1 breaks things
```bash
git checkout -- .  # Revert all changes
```

### If Phase 2 breaks things
```bash
# Restore from backup
rm -rf /Users/naythandawe/git
mv /Users/naythandawe/git-backup-YYYYMMDD /Users/naythandawe/git
```

### If remote is broken
```bash
# Force push backup
cd /Users/naythandawe/git-backup-YYYYMMDD
git push --force origin main
```

---

## Files to Modify (Reference)

### High-priority (functional code)
```
claude/tools/macos_calendar_bridge.py
claude/tools/enhanced_email_triage.py
claude/tools/meeting_prep_automation.py
claude/tools/unified_morning_briefing.py
claude/tools/unified_action_tracker.py
claude/tools/sre/automated_health_monitor.py
claude/tools/sre/servicedesk_quality_analyzer_postgres.py
claude/tools/security/ufc_compliance_checker.py
claude/tools/security/com.maia.security-orchestrator.plist
```

### Medium-priority (utilities)
```
claude/tools/whisper_health_monitor.sh
claude/tools/start_vtt_watcher.sh
claude/tools/stop_vtt_watcher.sh
claude/tools/validate_file_location.py
claude/tools/project_management/*.py
```

### Low-priority (documentation)
```
SYSTEM_STATE.md
claude/documentation/*.md (92 occurrences - bulk sed replace)
```

---

## Command Reference

### Bulk replace in docs (Phase 1)
```bash
find claude/documentation -name "*.md" -exec sed -i '' 's|/Users/naythandawe/git/maia|$MAIA_ROOT|g' {} \;
```

### Count remaining hardcoded paths
```bash
grep -r "/Users/naythandawe" --include="*.py" --include="*.sh" | wc -l
```

### Verify no hardcoded paths remain
```bash
grep -r "/Users/naythandawe" --include="*.py" --include="*.sh" --include="*.plist"
# Should return empty
```

---

## Decision Log

| Decision | Rationale |
|----------|-----------|
| Use `MAIA_ROOT` env var | Works across machines, easy to set |
| Path.resolve() fallback | Works without env var if file structure intact |
| Restructure optional | Path fix is mandatory, restructure is cosmetic |
| Backup before filter-repo | History rewrite is irreversible |

---

## Success Criteria

1. Teammate can clone and run `./setup.sh` in <5 minutes
2. All tools work without modification
3. No `/Users/naythandawe` in any code file
4. Test suite passes on fresh clone
