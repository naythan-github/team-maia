# validate_file_location Tool - Requirements

**Created**: 2025-11-07 (Retroactive - TDD compliance)
**Component**: Python validation tool
**Purpose**: Runtime file location validation against file organization policy

---

## Core Purpose

**Problem**: Agents need way to validate file locations before saving (prevent policy violations).

**Solution**: Command-line tool that checks proposed file path against policy rules and provides recommendations if non-compliant.

---

## Functional Requirements

### FR1: Main Validation Function
**Requirement**: `validate_file_location(filepath: str, file_purpose: str) -> Dict`

**Inputs**:
- `filepath`: Proposed file path (relative or absolute)
- `file_purpose`: Description of file purpose (e.g., "ServiceDesk analysis")

**Output**:
```python
{
    "valid": bool,                    # True if compliant
    "recommended_path": str,          # Suggested path (or actual if valid)
    "reason": str,                    # Human-readable explanation
    "policy_violated": str or None    # Which policy rule violated (if any)
}
```

**Acceptance Criteria**:
- ✅ Function signature matches spec
- ✅ Returns dict with all 4 keys
- ✅ Handles both relative and absolute paths
- ✅ `valid=True` when compliant, `False` when not

**Example**:
```python
validate_file_location("claude/data/Analysis.xlsx", "ServiceDesk analysis")
# Returns: {
#   "valid": False,
#   "recommended_path": "~/work_projects/servicedesk_analysis/",
#   "reason": "Work outputs should not be in Maia repository",
#   "policy_violated": "Operational Data Separation Policy"
# }
```

---

### FR2: Work Output Detection
**Requirement**: `is_work_output(file_purpose: str, filepath: Path) -> bool`

**Detection Criteria**:
1. **Purpose keywords**: analysis, report, summary, deliverable, client, output
2. **Filename patterns**: ServiceDesk, Infrastructure, Lance_Letran, L2_, Analysis, Summary

**Acceptance Criteria**:
- ✅ Returns `True` if ANY keyword matches
- ✅ Case-insensitive matching
- ✅ Checks both purpose string AND filename

**Test Cases**:
| Input Purpose | Input Filename | Expected |
|--------------|----------------|----------|
| "ServiceDesk analysis report" | "report.xlsx" | True |
| "Maia tool implementation" | "tool.py" | False |
| "Database" | "ServiceDesk_Analysis.xlsx" | True |
| "System config" | "config.json" | False |

---

### FR3: File Size Enforcement
**Requirement**: Reject files >10 MB (except RAG databases).

**Rules**:
- Check file size if file exists
- Reject if >10 MB AND path doesn't contain `rag_databases`
- Provide size in error message (e.g., "file is 15.3 MB")

**Acceptance Criteria**:
- ✅ File size checked (if file exists)
- ✅ 10 MB threshold enforced
- ✅ RAG databases exemption
- ✅ Size included in error message

**Test Cases**:
| File Path | Size | Contains `rag_databases`? | Expected |
|-----------|------|--------------------------|----------|
| `claude/data/large.db` | 15 MB | No | Invalid (size) |
| `claude/data/rag_databases/vectors.db` | 50 MB | Yes | Valid (exempt) |
| `claude/data/small.db` | 5 MB | No | Valid (size OK) |

---

### FR4: UFC Structure Validation
**Requirement**: `matches_ufc_structure(filepath: Path) -> bool`

**UFC Structure Rules**:
1. Must be under `claude/` directory (or `tests/`, `docs/`)
2. Second level must be valid: `agents`, `tools`, `commands`, `context`, `data`, `hooks`, `extensions`
3. Minimum 2 levels deep (e.g., `claude/tools/`)

**Acceptance Criteria**:
- ✅ Returns `True` for valid UFC paths
- ✅ Returns `False` for random files not in structure
- ✅ Allows `tests/` and `docs/` as exceptions

**Test Cases**:
| Path | Expected | Reason |
|------|----------|--------|
| `claude/agents/test_agent.md` | True | Valid UFC |
| `claude/tools/test_tool.py` | True | Valid UFC |
| `tests/test_something.py` | True | Exception |
| `random_file.md` | False | Not in UFC |
| `claude/invalid/file.py` | False | Invalid second level |

---

### FR5: UFC-Compliant Path Suggestions
**Requirement**: `get_ufc_compliant_path(filepath: Path) -> Path`

**Mapping Rules**:
- `*_agent.md` → `claude/agents/`
- `*.py` (not test) → `claude/tools/`
- `test_*.py` → `tests/`
- `*.db` → `claude/data/databases/system/`
- `*_PLAN.md` → `claude/data/project_status/active/`
- `*_progress.md` → `claude/data/project_status/active/`
- `PHASE_*.md` → `claude/data/project_status/active/`
- Default → `claude/data/`

**Acceptance Criteria**:
- ✅ All 8+ file patterns have mappings
- ✅ Returns absolute path
- ✅ Path uses MAIA_ROOT environment variable

**Test Cases**:
| Input Filename | Expected Path |
|----------------|--------------|
| `my_agent.md` | `{MAIA_ROOT}/claude/agents/my_agent.md` |
| `my_tool.py` | `{MAIA_ROOT}/claude/tools/my_tool.py` |
| `test_feature.py` | `{MAIA_ROOT}/tests/test_feature.py` |
| `data.db` | `{MAIA_ROOT}/claude/data/databases/system/data.db` |
| `PROJECT_PLAN.md` | `{MAIA_ROOT}/claude/data/project_status/active/PROJECT_PLAN.md` |

---

### FR6: Root Directory Restriction
**Requirement**: Only 4 core files allowed in repository root.

**Allowed Files**:
1. `CLAUDE.md`
2. `README.md`
3. `SYSTEM_STATE.md`
4. `SYSTEM_STATE_ARCHIVE.md`

**Acceptance Criteria**:
- ✅ Validates if file is in root (no `/` in path)
- ✅ Checks against allowed list
- ✅ Rejects all other root files
- ✅ Recommends `claude/data/project_status/active/`

**Test Cases**:
| Filename | Location | Expected |
|----------|----------|----------|
| `CLAUDE.md` | Root | Valid (allowed) |
| `README.md` | Root | Valid (allowed) |
| `RANDOM.md` | Root | Invalid (not allowed) |
| `anything.md` | `claude/data/` | Valid (not root) |

---

### FR7: Project Inference
**Requirement**: `infer_project(filepath: Path) -> str`

**Inference Rules**:
- `servicedesk` in filename → `servicedesk_analysis`
- `infrastructure` in filename → `infrastructure_team`
- `recruitment` or `l2_` in filename → `recruitment`
- Default → `general`

**Acceptance Criteria**:
- ✅ Case-insensitive matching
- ✅ Returns one of 4 project names
- ✅ Falls back to `general` if no match

**Test Cases**:
| Filename | Expected Project |
|----------|-----------------|
| `ServiceDesk_Analysis.xlsx` | `servicedesk_analysis` |
| `Infrastructure_Data.csv` | `infrastructure_team` |
| `L2_Test.md` | `recruitment` |
| `random_file.txt` | `general` |

---

### FR8: CLI Interface
**Requirement**: Command-line usage with clear output.

**Usage**:
```bash
python3 validate_file_location.py <filepath> <purpose>
```

**Output - Valid**:
```
✅ Valid: Compliant with file organization policy
   Path: /path/to/file
```

**Output - Invalid**:
```
❌ Invalid: Work outputs should not be in Maia repository
   Recommended: ~/work_projects/servicedesk_analysis/
   Policy violated: Operational Data Separation Policy

See: claude/context/core/file_organization_policy.md
```

**Exit Codes**:
- `0`: Valid (compliant)
- `1`: Invalid (non-compliant)

**Acceptance Criteria**:
- ✅ Usage help if <2 arguments
- ✅ Clear ✅/❌ output
- ✅ Exit code 0 for valid, 1 for invalid
- ✅ Policy reference link included

---

## Non-Functional Requirements

### NFR1: Performance
- Execution time: <50ms per validation
- No network calls
- Minimal file I/O (only if checking size)

**Acceptance Criteria**:
- ✅ Validation completes in <50ms (99th percentile)
- ✅ No external dependencies beyond stdlib

---

### NFR2: Error Handling
- Handle non-existent files gracefully (size check skipped)
- Handle invalid paths gracefully (return Invalid)
- No crashes on any input

**Acceptance Criteria**:
- ✅ No exceptions raised for any valid input
- ✅ Graceful handling of edge cases

---

### NFR3: Maintainability
- Clear function names
- Type hints for all functions
- Docstrings for public functions
- Configuration constants at top

**Acceptance Criteria**:
- ✅ All functions have type hints
- ✅ Public functions have docstrings
- ✅ Constants defined at module level

---

## Edge Cases

### EDGE1: Relative vs. Absolute Paths
**Scenario**: User provides relative path `claude/data/file.db`

**Expected**: Convert to absolute using MAIA_ROOT

**Acceptance Criteria**:
- ✅ Both relative and absolute paths handled
- ✅ MAIA_ROOT environment variable used

---

### EDGE2: File Doesn't Exist Yet
**Scenario**: Validating path for file to be created

**Expected**: Skip size check, validate path only

**Acceptance Criteria**:
- ✅ No error if file doesn't exist
- ✅ Size check skipped for non-existent files

---

### EDGE3: Symlinks
**Scenario**: File is symlink to different location

**Expected**: Resolve symlink, validate target

**Acceptance Criteria**:
- ✅ Symlinks resolved before validation
- ✅ Target path validated

---

## Test Requirements

### Unit Tests (Required):
1. `test_work_output_detection()` - 4 test cases
2. `test_size_limit()` - 3 test cases
3. `test_ufc_structure()` - 5 test cases
4. `test_recommended_paths()` - 5 test cases
5. `test_project_inference()` - 4 test cases
6. `test_validation_integration()` - 4 test cases

**Total**: Minimum 25 test cases

**Acceptance Criteria**:
- ✅ All test cases pass
- ✅ Edge cases covered
- ✅ Integration tests included

---

## Success Metrics

1. **Accuracy**: >95% correct validation (valid files approved, invalid rejected)
2. **Performance**: <50ms execution (99th percentile)
3. **Usability**: Clear output (users understand why rejected)
4. **Coverage**: ≥90% code coverage by tests

---

## Integration Points

### Integration 1: File Organization Policy
- Uses same rules as policy document
- References policy in error messages
- Stays synchronized with policy updates

### Integration 2: Pre-Commit Hook
- Hook can call this tool for validation
- Shares constants (ALLOWED_ROOT_FILES, etc.)

### Integration 3: Agent Usage
- Agents can call from command line or import as module
- Returns structured data (dict) for programmatic use

---

**Status**: ✅ Requirements Complete (Retroactive)
**Next**: Validate implementation and expand test suite
