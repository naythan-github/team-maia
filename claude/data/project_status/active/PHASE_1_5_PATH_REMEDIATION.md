# Phase 1.5: Complete Path Remediation

**Created**: 2025-12-15
**Status**: PENDING
**Priority**: HIGH - Blocking team sharing
**Estimated Effort**: 45-60 minutes
**Context**: Continuation of Team Sharing Project (marked complete 2025-12-11 but incomplete)

---

## Problem Statement

Phase 1 of Team Sharing Project claimed "All 44 code occurrences updated" but **108 violations remain** in Python files. This was discovered when `convert_md_to_docx.py` failed due to hardcoded path.

### Root Cause
Phase 1 only fixed files explicitly listed in the project plan. It did NOT do a comprehensive grep to find all violations.

---

## Files Requiring Remediation

### Group A: Direct Hardcoded Paths (22 files)
Pattern: `Path.home() / "git" / "maia"` or similar

```
claude/tools/data_analyst_pattern_integration.py
claude/tools/document_conversion/convert_md_to_docx.py
claude/tools/downloads_vtt_mover.py
claude/tools/information_management/auto_capture_integration.py
claude/tools/information_management/executive_information_manager.py
claude/tools/information_management/quick_capture.py
claude/tools/information_management/stakeholder_intelligence.py
claude/tools/intelligent_downloads_router.py
claude/tools/monitoring/security_intelligence_dashboard.py
claude/tools/personal_assistant_startup.py
claude/tools/productivity/decision_intelligence.py
claude/tools/security/save_state_security_checker.py
claude/tools/security/security_intelligence_dashboard.py
claude/tools/security/security_orchestration_service.py
claude/tools/sre/file_organization_checker.py
claude/tools/sre/incremental_import_servicedesk.py
claude/tools/sre/launchagent_health_monitor.py
claude/tools/sre/save_state_security_checker.py
claude/tools/sre/servicedesk_operations_intelligence.py
claude/tools/sre/system_state_etl.py
claude/tools/vtt_to_email_rag.py
claude/tools/vtt_watcher.py
```

### Group B: Fallback Pattern Violations (6 files)
Pattern: `os.environ.get("MAIA_ROOT", os.path.expanduser("~/git/maia"))`

```
claude/tools/document/pir/pir_template_manager.py
claude/tools/project_management/migrate_existing_projects.py
claude/tools/project_management/project_backlog_dashboard.py
claude/tools/project_management/project_registry.py
claude/tools/validate_file_location.py
claude/tools/whisper_meeting_transcriber.py
```

**Total: 28 files**

---

## Standard Fix Pattern

### Import from paths.py
```python
# BEFORE (wrong)
MAIA_ROOT = Path.home() / "git" / "maia"

# AFTER (correct)
from claude.tools.core.paths import MAIA_ROOT
```

### For files that can't import (circular deps)
```python
# BEFORE (wrong)
MAIA_ROOT = os.environ.get("MAIA_ROOT", os.path.expanduser("~/git/maia"))

# AFTER (correct - derive from script location)
MAIA_ROOT = Path(__file__).resolve().parent.parent.parent.parent
```

---

## Execution Steps

### Step 1: Fix Group A files (22 files)

For each file, add import and remove hardcoded path:

```python
# Add at top of file (after other imports)
from claude.tools.core.paths import MAIA_ROOT

# Remove lines like:
# MAIA_ROOT = Path.home() / "git" / "maia"
# maia_root = Path.home() / "git" / "maia"
```

### Step 2: Fix Group B files (6 files)

Replace fallback pattern with paths.py import:

```python
# BEFORE
MAIA_ROOT = os.environ.get("MAIA_ROOT", os.path.expanduser("~/git/maia"))

# AFTER
from claude.tools.core.paths import MAIA_ROOT
```

### Step 3: Verify no remaining violations

```bash
# Should return empty
grep -r "Path\.home().*git.*maia\|~/git/maia" --include="*.py" claude/tools/ | grep -v archive/
```

### Step 4: Test critical tools

```bash
# Test converter
python3 claude/tools/document_conversion/convert_md_to_docx.py --help

# Test VTT watcher
python3 claude/tools/vtt_watcher.py --help

# Test security tools
python3 claude/tools/security/security_intelligence_dashboard.py --help
```

---

## Validation Checklist

- [ ] All 22 Group A files fixed
- [ ] All 6 Group B files fixed
- [ ] Grep returns zero violations
- [ ] `convert_md_to_docx.py` runs successfully
- [ ] `vtt_watcher.py` runs successfully
- [ ] Test suite passes (basic smoke test)

---

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Import errors | paths.py is already in core/, imports work |
| Circular imports | Use `Path(__file__)` pattern as fallback |
| Breaking changes | All changes are path resolution only, no logic changes |

---

## Success Criteria

1. Zero hardcoded paths in Python files (excluding archive/)
2. All tools run from any directory location
3. `grep -r "Path.home().*maia" --include="*.py" claude/tools/` returns empty

---

## Related Documents

- Original project: `claude/data/project_status/active/maia_team_sharing_project_plan.md`
- Portability guide: `claude/context/core/portability_guide.md`
- paths.py: `claude/tools/core/paths.py`

---

## Command Reference

### Find all violations
```bash
grep -r "Path\.home().*git.*maia\|Path\.home().*maia\|~/git/maia" --include="*.py" claude/tools/ | grep -v archive/
```

### Count violations
```bash
grep -r "Path\.home().*git.*maia\|~/git/maia" --include="*.py" claude/tools/ | grep -v archive/ | wc -l
```

### Test paths.py works
```bash
python3 -c "from claude.tools.core.paths import MAIA_ROOT; print(f'MAIA_ROOT: {MAIA_ROOT}')"
```
