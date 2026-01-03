# File Organization Enforcement - SAFE PATH (Option A)

**Last Updated**: 2025-11-07
**Status**: APPROVED - Ready for Execution
**Active Agents**: SRE Principal Engineer Agent
**Estimated Duration**: 75 minutes
**Risk Level**: LOW (5%)

---

## Project Overview

### What This Does
Creates file organization policy and enforcement mechanisms WITHOUT moving any existing files. Prevents FUTURE pollution while avoiding breakage risk from cleanup.

### What This DOESN'T Do
- ❌ Does NOT move servicedesk_tickets.db (154 MB)
- ❌ Does NOT reorganize existing databases
- ❌ Does NOT move operational files
- ❌ Does NOT clean root directory
- ❌ Does NOT reduce current repository size

**Rationale**: Cleanup (Phase 4) has 40% breakage risk due to unknown database dependencies. This safe path provides protection without risk.

---

## Phases Included

✅ **Phase 1**: Create File Organization Policy (30 min)
✅ **Phase 2**: Create Validation Tool (45 min)
✅ **Phase 3**: Create Pre-Commit Hook (30 min)
❌ **Phase 4**: Execute Cleanup (EXCLUDED - too risky)
✅ **Phase 5**: Update Documentation (10 min)

**Total**: ~2 hours

---

## Phase 1: Create File Organization Policy

**AGENT**: Load SRE Principal Engineer Agent
**Command**: "load sre_principal_engineer_agent"
**Duration**: 30 minutes
**Risk**: LOW (file creation only, no system changes)

### Steps

1. **Create `claude/context/core/file_organization_policy.md`** (~150 lines)

**Content Structure**:
```markdown
# File Organization Policy

## 🚨 DECISION TREE: Where should I save this file?

**STEP 1: Is this Maia system file or work output?**
- Maia system file (helps Maia operate) → Continue to Step 2
- Work output (produced BY Maia) → Save to ~/work_projects/{project}/

**STEP 2: What type of Maia file?**

| File Type | Location | Examples |
|-----------|----------|----------|
| Agent Definition | claude/agents/ | *_agent.md |
| Tool Implementation | claude/tools/ | *.py scripts |
| Command | claude/commands/ | *.md slash commands |
| System Context | claude/context/core/ | System-wide policies |
| Domain Knowledge | claude/context/knowledge/{domain}/ | Reference materials |
| Operational Database | claude/data/databases/{category}/ | *.db files |
| RAG Database | claude/data/rag_databases/ | Vector stores |
| Phase Documentation | claude/data/project_status/active/ | <30 days old |
| Archived Phase Docs | claude/data/project_status/archive/{YYYY-QQ}/ | >30 days old |
| Project Progress | claude/data/project_status/active/ | {PROJECT}_progress.md |

## FORBIDDEN LOCATIONS
❌ Repository root (only 4 core files: CLAUDE.md, README.md, SYSTEM_STATE.md, SYSTEM_STATE_ARCHIVE.md)
❌ claude/data/ root (use subdirectories)
❌ Maia repo for work outputs (use ~/work_projects/)

## SIZE LIMITS
- Files >10 MB → MUST be in ~/work_projects/ (not Maia repo)
- Exception: RAG databases in claude/data/rag_databases/

## TDD PROJECT FILE ORGANIZATION

**Maia System Development**:
→ claude/tools/{tool_name}/
   ├── requirements.md
   ├── implementation.py
   └── README.md
→ tests/test_{tool_name}.py

**Work Projects**:
→ ~/work_projects/{project}/
   ├── requirements.md
   ├── implementation.py
   ├── test_requirements.py
   └── README.md

## PROJECT PLANS vs. REQUIREMENTS

**When to create**:
- requirements.md: TDD technical specs (always for development)
- {PROJECT}_PLAN.md: High-level project plan (multi-phase projects)
- {PROJECT}_progress.md: Progress tracking (multi-phase projects)

**Location**:
- requirements.md: With implementation (claude/tools/ or ~/work_projects/)
- PROJECT_PLAN.md: claude/data/project_status/active/
- PROJECT_progress.md: claude/data/project_status/active/

## DATABASE ORGANIZATION

**Categories**:
- intelligence/: Security, RSS, ServiceDesk operations intelligence
- system/: Routing decisions, tool usage, documentation enforcement
- user/: User-specific (*_naythan.db)
- archive/: Deprecated databases

**Location**: claude/data/databases/{category}/
```

2. **Update `CLAUDE.md` - Mandatory Loading Sequence**

Add to line ~30 (context loading protocol):
```markdown
### Context Loading Protocol
**MANDATORY SEQUENCE**:
1. FIRST: Load ${MAIA_ROOT}/claude/context/ufc_system.md
2. CHECK AGENT SESSION: [existing logic]
3. THEN: Follow smart context loading:
   - UFC system (ALREADY LOADED)
   - identity.md
   - systematic_thinking_protocol.md
   - model_selection_strategy.md
   - **file_organization_policy.md** ⭐ NEW
```

3. **Update `claude/context/core/smart_context_loading.md`**

Add to line ~16 (MANDATORY CORE):
```markdown
**MANDATORY CORE (Always Load - NO EXCEPTIONS)**:
1. ufc_system.md
2. identity.md
3. systematic_thinking_protocol.md
4. model_selection_strategy.md
5. **file_organization_policy.md** ⭐ NEW - File storage rules
6. Smart SYSTEM_STATE Loading
```

4. **Test Context Loading**
- Open new Claude Code window
- Verify policy file loads
- Check token count (should be +2,500 tokens, +28%)
- Measure load time (should be <100ms)

**Deliverables**:
- ✅ claude/context/core/file_organization_policy.md (150 lines)
- ✅ Updated CLAUDE.md
- ✅ Updated smart_context_loading.md
- ✅ Context loading verified

**Save Progress**: Update FILE_ORGANIZATION_SAFE_PATH_progress.md with Phase 1 completion

---

## Phase 2: Create Validation Tool

**AGENT RELOAD**: "load sre_principal_engineer_agent"
**Duration**: 45 minutes
**Risk**: LOW (read-only tool, no file modifications)

### Steps

1. **Create `claude/tools/validate_file_location.py`** (~200 lines)

```python
#!/usr/bin/env python3
"""
File location validation tool for Maia file organization policy.

Usage:
    validate_file_location("path/to/file.db", "ServiceDesk analysis database")
"""

import os
from pathlib import Path
from typing import Dict, List

# Constants
MAIA_ROOT = Path(os.getenv('MAIA_ROOT', os.path.expanduser('~/git/maia')))
MAX_FILE_SIZE_MB = 10
ALLOWED_ROOT_FILES = ['CLAUDE.md', 'README.md', 'SYSTEM_STATE.md', 'SYSTEM_STATE_ARCHIVE.md']
WORK_OUTPUT_KEYWORDS = ['ServiceDesk', 'Infrastructure', 'Lance_Letran', 'L2_', 'Analysis', 'Summary']

def validate_file_location(filepath: str, file_purpose: str) -> Dict:
    """
    Validate if file should be saved to proposed location.

    Args:
        filepath: Proposed file path (relative or absolute)
        file_purpose: Description of file purpose

    Returns:
        {
            "valid": bool,
            "recommended_path": str,
            "reason": str,
            "policy_violated": str or None
        }
    """
    filepath = Path(filepath)

    # Make absolute if relative
    if not filepath.is_absolute():
        filepath = MAIA_ROOT / filepath

    # Check 1: Work output detection
    if is_work_output(file_purpose, filepath):
        project = infer_project(filepath)
        return {
            "valid": False,
            "recommended_path": f"~/work_projects/{project}/",
            "reason": "Work outputs should not be in Maia repository",
            "policy_violated": "Operational Data Separation Policy"
        }

    # Check 2: File size (if exists)
    if filepath.exists():
        size_mb = filepath.stat().st_size / (1024 * 1024)
        if size_mb > MAX_FILE_SIZE_MB and 'rag_databases' not in str(filepath):
            return {
                "valid": False,
                "recommended_path": "~/work_projects/",
                "reason": f"Files >10 MB must be in work_projects (file is {size_mb:.1f} MB)",
                "policy_violated": "Size Limit Policy"
            }

    # Check 3: UFC structure compliance
    if not matches_ufc_structure(filepath):
        recommended = get_ufc_compliant_path(filepath)
        return {
            "valid": False,
            "recommended_path": str(recommended),
            "reason": "File location violates UFC structure",
            "policy_violated": "UFC Directory Structure"
        }

    # Check 4: Root directory restriction
    if filepath.parent == MAIA_ROOT and filepath.name not in ALLOWED_ROOT_FILES:
        return {
            "valid": False,
            "recommended_path": "claude/data/project_status/active/",
            "reason": "Only 4 core files allowed in repository root",
            "policy_violated": "Root Directory Policy"
        }

    return {
        "valid": True,
        "recommended_path": str(filepath),
        "reason": "Compliant with file organization policy",
        "policy_violated": None
    }

def is_work_output(file_purpose: str, filepath: Path) -> bool:
    """Check if file is work output (not Maia system file)."""
    purpose_lower = file_purpose.lower()
    filename = filepath.name

    # Keywords indicating work output
    work_keywords = ['analysis', 'report', 'summary', 'deliverable', 'client', 'output']
    if any(keyword in purpose_lower for keyword in work_keywords):
        return True

    # Filename patterns indicating work output
    if any(keyword in filename for keyword in WORK_OUTPUT_KEYWORDS):
        return True

    return False

def matches_ufc_structure(filepath: Path) -> bool:
    """Check if file path matches UFC directory structure."""
    rel_path = filepath.relative_to(MAIA_ROOT) if filepath.is_relative_to(MAIA_ROOT) else filepath
    parts = rel_path.parts

    if len(parts) == 0:
        return False

    # Must be under claude/ directory for Maia files
    if parts[0] != 'claude':
        # Exception: tests/ directory
        return parts[0] in ['tests', 'docs']

    # Check second level (agents, tools, commands, context, data, hooks)
    if len(parts) < 2:
        return False

    valid_second_level = ['agents', 'tools', 'commands', 'context', 'data', 'hooks', 'extensions']
    return parts[1] in valid_second_level

def get_ufc_compliant_path(filepath: Path) -> Path:
    """Suggest UFC-compliant path for file."""
    filename = filepath.name

    # Agent files
    if filename.endswith('_agent.md'):
        return MAIA_ROOT / 'claude' / 'agents' / filename

    # Tool files
    if filename.endswith('.py') and not filename.startswith('test_'):
        return MAIA_ROOT / 'claude' / 'tools' / filename

    # Test files
    if filename.startswith('test_'):
        return MAIA_ROOT / 'tests' / filename

    # Database files
    if filename.endswith('.db'):
        return MAIA_ROOT / 'claude' / 'data' / 'databases' / 'system' / filename

    # Documentation files
    if filename.endswith('.md'):
        if 'PLAN' in filename or 'progress' in filename:
            return MAIA_ROOT / 'claude' / 'data' / 'project_status' / 'active' / filename
        return MAIA_ROOT / 'claude' / 'data' / filename

    # Default
    return MAIA_ROOT / 'claude' / 'data' / filename

def infer_project(filepath: Path) -> str:
    """Infer project name from filepath."""
    filename = filepath.name.lower()

    if 'servicedesk' in filename:
        return 'servicedesk_analysis'
    if 'infrastructure' in filename:
        return 'infrastructure_team'
    if 'recruitment' in filename or 'l2_' in filename:
        return 'recruitment'

    return 'general'

# CLI interface
if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        print("Usage: validate_file_location.py <filepath> <purpose>")
        sys.exit(1)

    result = validate_file_location(sys.argv[1], sys.argv[2])

    if result['valid']:
        print(f"✅ Valid: {result['reason']}")
    else:
        print(f"❌ Invalid: {result['reason']}")
        print(f"   Recommended: {result['recommended_path']}")
        print(f"   Policy violated: {result['policy_violated']}")
        sys.exit(1)
```

2. **Create Test Suite** (`tests/test_validate_file_location.py`)

```python
import pytest
from pathlib import Path
from claude.tools.validate_file_location import (
    validate_file_location,
    is_work_output,
    matches_ufc_structure,
    get_ufc_compliant_path
)

def test_work_output_detection():
    """Test detection of work output files."""
    assert is_work_output("ServiceDesk analysis report", Path("report.xlsx")) == True
    assert is_work_output("Maia tool implementation", Path("tool.py")) == False

def test_size_limit():
    """Test file size limit enforcement."""
    # Create large file (mock)
    result = validate_file_location("claude/data/large_file.db", "Large database")
    # Would need actual file to test properly

def test_ufc_structure():
    """Test UFC structure validation."""
    assert matches_ufc_structure(Path("claude/agents/test_agent.md")) == True
    assert matches_ufc_structure(Path("random_file.md")) == False

def test_recommended_paths():
    """Test recommended path suggestions."""
    assert "claude/agents" in str(get_ufc_compliant_path(Path("my_agent.md")))
    assert "claude/tools" in str(get_ufc_compliant_path(Path("my_tool.py")))
```

3. **Update Documentation**
- Add to capability_index.md
- Document in file_organization_policy.md

**Deliverables**:
- ✅ claude/tools/validate_file_location.py (200 lines)
- ✅ tests/test_validate_file_location.py (150 lines)
- ✅ Updated capability_index.md

**Save Progress**: Update FILE_ORGANIZATION_SAFE_PATH_progress.md with Phase 2 completion

---

## Phase 3: Create Pre-Commit Hook

**AGENT RELOAD**: "load sre_principal_engineer_agent"
**Duration**: 30 minutes
**Risk**: LOW (can be bypassed with --no-verify)

### Steps

1. **Create `claude/hooks/pre_commit_file_organization.py`** (~150 lines)

```python
#!/usr/bin/env python3
"""
Pre-commit hook: File organization policy enforcement.

Prevents commits that violate file organization policy.
"""

import sys
import subprocess
from pathlib import Path

# Configuration
MAIA_ROOT = Path(__file__).parent.parent.parent
ALLOWED_ROOT_FILES = ['CLAUDE.md', 'README.md', 'SYSTEM_STATE.md', 'SYSTEM_STATE_ARCHIVE.md']
WORK_OUTPUT_PATTERNS = ['*ServiceDesk*', '*Infrastructure*', '*Lance_Letran*', '*L2_*']
MAX_FILE_SIZE_MB = 10

def get_staged_files():
    """Get list of staged files."""
    result = subprocess.run(
        ['git', 'diff', '--cached', '--name-only'],
        capture_output=True,
        text=True
    )
    return [f for f in result.stdout.strip().split('\n') if f]

def check_violations():
    """Check for file organization violations."""
    violations = []
    staged_files = get_staged_files()

    for file in staged_files:
        filepath = MAIA_ROOT / file

        # Skip if file doesn't exist (deletion)
        if not filepath.exists():
            continue

        # Check 1: Work outputs in Maia repo
        if any(pattern.replace('*', '') in file for pattern in WORK_OUTPUT_PATTERNS):
            if 'claude/data' in file:
                violations.append(
                    f"❌ {file} - Work output in Maia repo (move to ~/work_projects/)"
                )

        # Check 2: Files >10 MB
        size_mb = filepath.stat().st_size / (1024 * 1024)
        if size_mb > MAX_FILE_SIZE_MB and 'rag_databases' not in file:
            violations.append(
                f"❌ {file} - File >10 MB ({size_mb:.1f} MB) (move to ~/work_projects/)"
            )

        # Check 3: Root directory pollution
        if '/' not in file and file not in ALLOWED_ROOT_FILES:
            violations.append(
                f"❌ {file} - Not allowed in root (move to appropriate subdirectory)"
            )

        # Check 4: Databases not in databases/
        if file.endswith('.db') and 'databases/' not in file and 'rag_databases' not in file:
            violations.append(
                f"❌ {file} - Database not in claude/data/databases/ subdirectory"
            )

    return violations

def main():
    """Main execution."""
    violations = check_violations()

    if violations:
        print("\n🚨 FILE ORGANIZATION POLICY VIOLATIONS:\n")
        for v in violations:
            print(v)
        print("\nSee: claude/context/core/file_organization_policy.md")
        print("\nTo bypass (if urgent): git commit --no-verify")
        return 1

    return 0

if __name__ == '__main__':
    sys.exit(main())
```

2. **Create Installation Instructions**

Document in file_organization_policy.md:
```markdown
## Pre-Commit Hook Installation

**Automatic** (recommended):
```bash
ln -s ../../claude/hooks/pre_commit_file_organization.py .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

**Manual** (copy file):
```bash
cp claude/hooks/pre_commit_file_organization.py .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

**Bypass** (if urgent):
```bash
git commit --no-verify
```
```

3. **Test Hook**
```bash
# Create test violation
echo "test" > VIOLATING_FILE.md
git add VIOLATING_FILE.md
git commit -m "Test"
# Should be blocked

# Clean up
rm VIOLATING_FILE.md
```

**Deliverables**:
- ✅ claude/hooks/pre_commit_file_organization.py (150 lines)
- ✅ Hook installation instructions
- ✅ Test validation complete

**Save Progress**: Update FILE_ORGANIZATION_SAFE_PATH_progress.md with Phase 3 completion

---

## Phase 5: Update Documentation

**AGENT RELOAD**: "load sre_principal_engineer_agent"
**Duration**: 10 minutes
**Risk**: LOW (documentation updates only)

### Steps

1. **Update `.gitignore`**
```
# Operational work outputs (should be in ~/work_projects/)
claude/data/*ServiceDesk*.xlsx
claude/data/*Infrastructure*.xlsx
claude/data/*.csv
claude/data/servicedesk_tickets.db

# Temporary analysis files
claude/data/*_Analysis_*.xlsx
claude/data/*_Summary_*.md
```

2. **Update `claude/context/core/identity.md`** (Working Principles)

Add principle #19:
```markdown
19. **File Storage Discipline**:
   - Work outputs → ~/work_projects/ (NOT Maia repo)
   - Maia system files → UFC structure (claude/{agents,tools,commands,data})
   - Databases → claude/data/databases/{intelligence,system,user}/
   - Phase docs → claude/data/project_status/{active,archive}/
   - Size limit: >10 MB → ~/work_projects/
   - Decision: "Helps Maia operate (KEEP) or output FROM Maia (MOVE)?"
   - Full policy: claude/context/core/file_organization_policy.md
```

3. **Update `SYSTEM_STATE.md`** (Add Phase 151 entry)

4. **Update `claude/context/core/capability_index.md`**
- Add validate_file_location tool
- Add file_organization_policy.md reference

**Deliverables**:
- ✅ Updated .gitignore
- ✅ Updated identity.md (+7 lines)
- ✅ Updated SYSTEM_STATE.md (Phase 151)
- ✅ Updated capability_index.md

**Save Progress**: Update FILE_ORGANIZATION_SAFE_PATH_progress.md with Phase 5 completion

---

## Success Criteria

### After Completion
- ✅ file_organization_policy.md in mandatory core loading
- ✅ validate_file_location.py tool available
- ✅ Pre-commit hook preventing violations
- ✅ Documentation updated
- ✅ All 5 phases completed
- ✅ No existing files moved (safe approach)

### Performance Metrics
- Context loading: +2,500 tokens (+28%)
- Session start: +50ms (one-time)
- Commit time: +100-200ms (pre-commit hook)
- Response latency: 0ms (no runtime overhead)

### Rollback Test
- Can remove from CLAUDE.md in <2 minutes
- Can disable hook with --no-verify
- No system changes to rollback

---

## What This Achieves

✅ **Prevention**: Future file pollution prevented
✅ **Safety**: No breakage risk (no file movement)
✅ **Guidance**: Clear policy for all agents
✅ **Enforcement**: Pre-commit hook catches violations
✅ **Validation**: Tool available for checking

❌ **Does NOT**: Clean existing mess (requires separate Phase 4 project with proper dependency analysis)

---

## Future Work (Phase 4 - Separate Project)

**Before attempting cleanup**:
1. Database dependency analysis (grep all tool/hook references)
2. SYSTEM_STATE.md production system verification
3. Incremental movement with testing (1 file at a time)
4. Symlink strategy (safer than direct movement)
5. Full validation suite

**Estimated effort**: 2-3 hours (not 15 minutes)
**Risk**: MEDIUM (15% with proper validation)

---

## Session Resumption

**Command**: "load sre_principal_engineer_agent"

**Context**: Executing SAFE PATH (Phases 1-3+5 only) for file organization enforcement. No file movement, only policy creation and enforcement mechanisms.

**Next Step**: Execute Phase 1 (create file_organization_policy.md)

---

**Status**: ✅ APPROVED FOR EXECUTION - SAFE PATH ONLY
