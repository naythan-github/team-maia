# pre_commit_file_organization Hook - Requirements

**Created**: 2025-11-07 (Retroactive - TDD compliance)
**Component**: Git pre-commit hook (Python)
**Purpose**: Git-time enforcement of file organization policy (block policy violations before commit)

---

## Core Purpose

**Problem**: Need git-time enforcement to catch policy violations before they enter repository.

**Solution**: Pre-commit hook that validates all staged files against file organization policy and blocks commits with violations.

---

## Functional Requirements

### FR1: Get Staged Files
**Requirement**: `get_staged_files() -> List[str]`

**Implementation**:
```python
git diff --cached --name-only
```

**Acceptance Criteria**:
- ✅ Returns list of staged file paths
- ✅ Handles empty staging area (returns empty list)
- ✅ Handles git command errors gracefully
- ✅ Returns relative paths from repository root

**Test Cases**:
| Staged Files | Expected Output |
|--------------|-----------------|
| `file1.py`, `file2.md` | `['file1.py', 'file2.md']` |
| (none) | `[]` |
| (git error) | `[]` (graceful fallback) |

---

### FR2: Work Output Detection (Violation Check 1)
**Requirement**: Block work outputs in `claude/data/`.

**Pattern Matching**:
- Filename contains: `ServiceDesk`, `Infrastructure`, `Lance_Letran`, `L2_`
- File path starts with: `claude/data/`

**Acceptance Criteria**:
- ✅ Detects all 4 work output patterns
- ✅ Only triggers if path is `claude/data/`
- ✅ Provides clear error message with recommended path

**Test Cases**:
| File Path | Contains Pattern? | Expected |
|-----------|------------------|----------|
| `claude/data/ServiceDesk_Analysis.xlsx` | ServiceDesk | ❌ BLOCK |
| `claude/data/Infrastructure_Data.csv` | Infrastructure | ❌ BLOCK |
| `~/work_projects/ServiceDesk_Analysis.xlsx` | ServiceDesk | ✅ ALLOW (not in claude/data) |
| `claude/agents/infrastructure_agent.md` | Infrastructure | ✅ ALLOW (not in claude/data) |

**Error Message**:
```
❌ claude/data/ServiceDesk_Analysis.xlsx - Work output in Maia repo (move to ~/work_projects/)
```

---

### FR3: File Size Limit (Violation Check 2)
**Requirement**: Block files >10 MB (except `rag_databases/`).

**Size Check**:
- Get file size using `os.path.getsize()`
- Convert to MB: `size_mb = bytes / (1024 * 1024)`
- Block if `size_mb > 10` AND path doesn't contain `rag_databases`

**Acceptance Criteria**:
- ✅ Checks size for all staged files
- ✅ Converts to MB for comparison
- ✅ Exempts `rag_databases/` paths
- ✅ Shows size in error message (e.g., "15.3 MB")

**Test Cases**:
| File Path | Size | Contains `rag_databases`? | Expected |
|-----------|------|--------------------------|----------|
| `claude/data/large.db` | 15 MB | No | ❌ BLOCK |
| `claude/data/rag_databases/vectors.db` | 50 MB | Yes | ✅ ALLOW |
| `claude/data/small.db` | 5 MB | No | ✅ ALLOW |

**Error Message**:
```
❌ claude/data/large.db - File >10 MB (15.3 MB) (move to ~/work_projects/)
```

---

### FR4: Root Directory Restriction (Violation Check 3)
**Requirement**: Block non-core files in repository root.

**Allowed Root Files**:
- `CLAUDE.md`
- `README.md`
- `SYSTEM_STATE.md`
- `SYSTEM_STATE_ARCHIVE.md`
- `.gitignore`
- `requirements-mcp-trello.txt` (existing exception)

**Detection**:
- File path contains no `/` (is in root)
- Filename not in allowed list

**Acceptance Criteria**:
- ✅ Detects root-level files (no `/` in path)
- ✅ Checks against allowed list
- ✅ Allows 6 core files
- ✅ Blocks all others

**Test Cases**:
| File Path | In Root? | In Allowed? | Expected |
|-----------|----------|-------------|----------|
| `CLAUDE.md` | Yes | Yes | ✅ ALLOW |
| `RANDOM.md` | Yes | No | ❌ BLOCK |
| `claude/data/file.md` | No | N/A | ✅ ALLOW (not root) |

**Error Message**:
```
❌ RANDOM.md - Not allowed in root (move to appropriate subdirectory)
```

---

### FR5: Database Location (Violation Check 4)
**Requirement**: Block databases not in `databases/` subdirectory.

**Detection**:
- Filename ends with `.db`
- Path doesn't contain `databases/`
- Path doesn't contain `rag_databases/` (exception)

**Acceptance Criteria**:
- ✅ Detects `.db` files
- ✅ Checks for `databases/` in path
- ✅ Exempts `rag_databases/`
- ✅ Provides correct subdirectory recommendation

**Test Cases**:
| File Path | Ends `.db`? | Has `databases/`? | Has `rag_databases/`? | Expected |
|-----------|------------|------------------|----------------------|----------|
| `claude/data/test.db` | Yes | No | No | ❌ BLOCK |
| `claude/data/databases/system/test.db` | Yes | Yes | No | ✅ ALLOW |
| `claude/data/rag_databases/vectors.db` | Yes | No | Yes | ✅ ALLOW |

**Error Message**:
```
❌ claude/data/test.db - Database not in claude/data/databases/ subdirectory
```

---

### FR6: Skip Deleted Files
**Requirement**: Don't check files being deleted.

**Detection**:
- File in staged list but doesn't exist on filesystem
- Use `filepath.exists()` check

**Acceptance Criteria**:
- ✅ Skips validation for non-existent files
- ✅ Doesn't error on deleted files
- ✅ Continues checking other staged files

**Test Cases**:
| File Path | Exists? | Expected |
|-----------|---------|----------|
| `deleted.py` | No | Skip (no validation) |
| `modified.py` | Yes | Validate normally |

---

### FR7: Skip Git Internal Files
**Requirement**: Don't check `.git/` or hidden files.

**Detection**:
- File path starts with `.git/`
- File path starts with `.` (hidden files like `.gitignore` are exempt)

**Acceptance Criteria**:
- ✅ Skips `.git/*` files
- ✅ Allows `.gitignore`, `.env` (needed files)
- ✅ Doesn't error on git internals

**Test Cases**:
| File Path | Expected |
|-----------|----------|
| `.git/config` | Skip |
| `.gitignore` | Validate (allowed in root) |
| `claude/data/file.py` | Validate normally |

---

### FR8: Violation Reporting
**Requirement**: Clear, actionable error messages.

**Output Format**:
```
🚨 FILE ORGANIZATION POLICY VIOLATIONS:

❌ claude/data/ServiceDesk_Analysis.xlsx - Work output in Maia repo (move to ~/work_projects/)
❌ claude/data/large.db - File >10 MB (15.3 MB) (move to ~/work_projects/)

📚 Policy: claude/context/core/file_organization_policy.md
🔧 Bypass (if urgent): git commit --no-verify
```

**Acceptance Criteria**:
- ✅ Header clearly states "VIOLATIONS"
- ✅ Each violation on separate line with ❌
- ✅ Clear action (what to do)
- ✅ Policy reference link
- ✅ Bypass instructions

---

### FR9: Exit Codes
**Requirement**: Standard Unix exit codes.

**Codes**:
- `0`: No violations (allow commit)
- `1`: Violations found (block commit)

**Acceptance Criteria**:
- ✅ Returns 0 if no violations
- ✅ Returns 1 if any violations
- ✅ Git respects exit codes (blocks on 1)

---

### FR10: Bypass Mechanism
**Requirement**: Allow urgent commits to bypass hook.

**Bypass Command**:
```bash
git commit --no-verify
```

**Acceptance Criteria**:
- ✅ Bypass instructions in error message
- ✅ `--no-verify` flag actually bypasses
- ✅ Hook doesn't run when bypassed

---

## Non-Functional Requirements

### NFR1: Performance
- Execution time: <200ms for typical commit (5-10 files)
- No network calls
- Minimal file I/O (only size checks)

**Acceptance Criteria**:
- ✅ Hook completes in <200ms (99th percentile)
- ✅ Doesn't slow down git workflow

---

### NFR2: Reliability
- No false positives (blocking valid files)
- No false negatives (allowing invalid files)
- Graceful error handling (git command failures)

**Acceptance Criteria**:
- ✅ <1% false positive rate
- ✅ <1% false negative rate
- ✅ No crashes on any input

---

### NFR3: Installation
- Easy to install (single symlink command)
- Easy to uninstall (remove symlink)
- Clear installation instructions

**Acceptance Criteria**:
- ✅ One-line install command
- ✅ Works after installation
- ✅ Instructions in policy document

**Install Command**:
```bash
ln -s ../../claude/hooks/pre_commit_file_organization.py .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

---

### NFR4: Maintainability
- Configuration constants at top
- Clear function names
- Docstrings for main function
- Easy to add new checks

**Acceptance Criteria**:
- ✅ Constants defined at module level
- ✅ Each check in separate section
- ✅ Easy to add new violation types

---

## Edge Cases

### EDGE1: Multiple Violations in One File
**Scenario**: File violates multiple rules (work output + >10 MB)

**Expected**: Report ALL violations for that file

**Acceptance Criteria**:
- ✅ All violations reported (not just first)
- ✅ Each violation gets separate line

---

### EDGE2: Large Number of Violations
**Scenario**: 50+ files violating policy

**Expected**: Report all violations (no truncation)

**Acceptance Criteria**:
- ✅ All violations shown
- ✅ No "... and 20 more" truncation
- ✅ Still completes in <200ms

---

### EDGE3: Symlink in Staging Area
**Scenario**: Staged file is symlink

**Expected**: Resolve symlink, check target

**Acceptance Criteria**:
- ✅ Symlinks resolved
- ✅ Target validated
- ✅ No errors on symlinks

---

### EDGE4: Binary Files
**Scenario**: Staged file is binary (image, etc.)

**Expected**: Size check still works, pattern checks skip

**Acceptance Criteria**:
- ✅ Binary files size-checked
- ✅ No encoding errors

---

## Test Requirements

### Unit Tests (Required):
1. `test_get_staged_files()` - 3 test cases
2. `test_work_output_detection()` - 4 test cases
3. `test_size_limit_enforcement()` - 3 test cases
4. `test_root_restriction()` - 3 test cases
5. `test_database_location()` - 4 test cases
6. `test_skip_deleted_files()` - 2 test cases
7. `test_violation_reporting()` - 2 test cases
8. `test_exit_codes()` - 2 test cases

**Total**: Minimum 23 test cases

### Integration Tests (Required):
1. `test_full_workflow_with_violations()` - Create violations, stage, commit (should block)
2. `test_full_workflow_clean()` - Stage valid files, commit (should succeed)
3. `test_bypass_mechanism()` - Use `--no-verify` (should succeed despite violations)

**Total**: 3 integration tests

**Acceptance Criteria**:
- ✅ All test cases pass
- ✅ Edge cases covered
- ✅ Integration tests with actual git operations

---

## Success Metrics

1. **Accuracy**: >99% correct violation detection
2. **Performance**: <200ms execution (99th percentile)
3. **Usability**: Clear error messages (users understand what to fix)
4. **Effectiveness**: >95% of violations caught before commit

---

## Integration Points

### Integration 1: validate_file_location Tool
- Can optionally call validation tool for additional checks
- Shares constants (ALLOWED_ROOT_FILES, WORK_OUTPUT_PATTERNS, etc.)

### Integration 2: File Organization Policy
- Enforces same rules as policy document
- Error messages reference policy file

### Integration 3: Git Workflow
- Runs automatically on `git commit`
- Respects `--no-verify` flag
- Returns proper exit codes for git

---

## Security Considerations

### SEC1: No Arbitrary Code Execution
- No eval() or exec()
- No user input executed as code
- Git commands use subprocess safely

**Acceptance Criteria**:
- ✅ No eval/exec in code
- ✅ Git commands use list form (not shell=True)

---

### SEC2: Path Traversal Protection
- Validate paths before checking
- Don't follow symlinks outside repo
- Handle `../` in paths safely

**Acceptance Criteria**:
- ✅ Paths validated before use
- ✅ No access outside MAIA_ROOT

---

## Performance Requirements

### PERF1: Fast Execution
**Target**: <200ms for 10 files

**Benchmark**:
- 5 files: <100ms
- 10 files: <200ms
- 50 files: <500ms

**Acceptance Criteria**:
- ✅ Meets all benchmarks
- ✅ No unnecessary file reads
- ✅ Efficient pattern matching

---

### PERF2: Graceful Degradation
**Scenario**: 1000+ files staged

**Expected**: Still completes (may take >500ms)

**Acceptance Criteria**:
- ✅ No timeout
- ✅ All files checked
- ✅ Memory efficient (streaming)

---

## Rollback Plan

### If Hook Causes Issues:
1. **Quick Disable**: `rm .git/hooks/pre-commit` (instant)
2. **Bypass Single Commit**: `git commit --no-verify`
3. **Full Uninstall**: Remove symlink, no other cleanup needed

**Acceptance Criteria**:
- ✅ Can disable in <30 seconds
- ✅ No residual effects after removal
- ✅ Repository unaffected

---

**Status**: ✅ Requirements Complete (Retroactive)
**Next**: Validate implementation and create comprehensive test suite
