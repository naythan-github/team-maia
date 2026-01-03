# Phase 218: File System Technical Debt Cleanup - Dependency Analysis

**Date**: 2024-12-02
**Status**: ✅ Option A+B Complete
**TDD Validation**: `tests/test_file_reorganization_safety.py` (5 tests passing)
**Post-Archive Validation**: ✅ All tests pass - no broken imports

---

## Versioned Tools Dependency Matrix

| File | Importers | Status | Action |
|------|-----------|--------|--------|
| `claude/tools/orro_app_inventory_v2.py` | 8 files (orro_app_inventory_fast.py, orro_app_inventory_direct.py, etc.) | 🛑 BLOCKED | Keep in place |
| `claude/tools/pmp/pmp_complete_intelligence_extractor_v2.py` | None | ✅ SAFE | Archive |
| `claude/tools/pmp/pmp_complete_intelligence_extractor_v3.py` | None | ✅ SAFE | Archive |
| `claude/tools/pmp/pmp_complete_intelligence_extractor_v4_resume.py` | 5 files (pmp_extract_remaining.py, pmp_extract_som.py, tests) | 🛑 BLOCKED | Keep in place |
| `claude/tools/pmp/pmp_config_extractor_v4.py` | None | ✅ SAFE | Archive |
| `claude/tools/sre/agent_v23_validator.py` | None | ✅ SAFE | Archive |
| `claude/tools/testing/test_v2.2_enhanced.py` | None | ✅ SAFE | Archive |
| `claude/tools/testing/test_v2_vs_v2.1.py` | None | ✅ SAFE | Archive |
| `claude/tools/testing/validate_v2.2_patterns.py` | None | ✅ SAFE | Archive |

---

## Blocked Files - Dependency Details

### orro_app_inventory_v2.py
**Why blocked**: Active dependency chain
```
orro_app_inventory_v2.py
├── orro_app_inventory_fast.py (4 imports)
└── orro_app_inventory_direct.py (4 imports)
```
**Resolution**: Cannot archive without refactoring importers to use direct implementation

### pmp_complete_intelligence_extractor_v4_resume.py
**Why blocked**: Primary PMP extraction tool
```
pmp_complete_intelligence_extractor_v4_resume.py
├── pmp_extract_remaining.py → imports PMPCompleteIntelligenceExtractor
├── pmp_extract_som.py → imports PMPCompleteIntelligenceExtractor
├── pmp_extract_missing_endpoints.py → imports PMPCompleteIntelligenceExtractor
├── tests/test_api_integration.py → imports for testing
└── tests/test_som_endpoints.py → imports for testing (3 locations)
```
**Resolution**: This is the ACTIVE version - keep as primary, archive v2/v3

---

## Archive Manifest

### Files Archived (2024-12-02)
| Original Location | Archive Location | Reason |
|-------------------|------------------|--------|
| `claude/tools/pmp/pmp_complete_intelligence_extractor_v2.py` | `claude/tools/archive/2024-12/pmp/` | Superseded by v4_resume |
| `claude/tools/pmp/pmp_complete_intelligence_extractor_v3.py` | `claude/tools/archive/2024-12/pmp/` | Superseded by v4_resume |
| `claude/tools/pmp/pmp_config_extractor_v4.py` | `claude/tools/archive/2024-12/pmp/` | No active importers |
| `claude/tools/sre/agent_v23_validator.py` | `claude/tools/archive/2024-12/sre/` | Validation utility, superseded |
| `claude/tools/testing/test_v2.2_enhanced.py` | `claude/tools/archive/2024-12/testing/` | Test variant, superseded |
| `claude/tools/testing/test_v2_vs_v2.1.py` | `claude/tools/archive/2024-12/testing/` | Comparison test, completed |
| `claude/tools/testing/validate_v2.2_patterns.py` | `claude/tools/archive/2024-12/testing/` | Validation tool, superseded |

---

## Validation Protocol

### Pre-Archive Checklist
- [x] Run `tests/test_file_reorganization_safety.py` - All 5 tests pass
- [x] Verify no active imports for each file
- [x] Document dependency chain for blocked files
- [x] Create archive directory structure

### Post-Archive Validation
- [x] Run validation tests again - ✅ 5/5 passed
- [x] Verify no broken imports - ✅ Confirmed
- [ ] Update capability_index.md if needed (future task)

---

## TDD Safety Net

Test file: `tests/test_file_reorganization_safety.py`

Tests:
1. `test_all_tool_imports_resolve` - Validates all tools can be imported
2. `test_no_syntax_errors_in_tools` - Catches syntax errors
3. `test_internal_imports_have_targets` - Verifies import targets exist
4. `test_versioned_tools_dependency_check` - Documents versioned file dependencies
5. `test_pmp_extractor_dependencies` - Specific PMP tool analysis

Run before AND after any file moves:
```bash
python3 -m pytest tests/test_file_reorganization_safety.py -v
```
