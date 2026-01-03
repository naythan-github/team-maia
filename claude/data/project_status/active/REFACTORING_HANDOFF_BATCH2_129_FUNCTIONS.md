# Phase 230 Refactoring Handoff - Batch 2

**From**: Python Code Reviewer Agent v2.4
**To**: SRE Principal Engineer Agent
**Date**: 2026-01-03
**Status**: PENDING EXECUTION

---

## Executive Summary

AST-based function scanner identified **129 functions** exceeding 100 lines across the Maia codebase. This handoff contains prioritized refactoring targets with execution protocol.

---

## CRITICAL Priority (4 functions - MUST-FIX)

| # | File | Function | Lines | Start Line |
|---|------|----------|-------|------------|
| 1 | `claude/tools/scripts/disaster_recovery_system.py` | `_generate_...` | 400 | 646 |
| 2 | `claude/tools/scripts/create_azure_lighthouse_confluence_pages.py` | `create_all_pages` | 369 | 38 |
| 3 | `claude/tools/sre/pmp_api_comprehensive_inventory.py` | `run_full_inventory` | 210 | 139 |
| 4 | `claude/tools/sre/pmp_complete_intelligence_extractor_v4_resume.py` | `init_database` | 209 | (find) |

### Refactoring Strategy per Function

**1. disaster_recovery_system.py:646 (400 lines)**
- Extract 8-10 helper methods for each report section
- Pattern: `_generate_X_section()` for each logical block
- Target: Main function ~40 lines orchestrating helpers

**2. create_azure_lighthouse_confluence_pages.py:38 (369 lines)**
- Extract page-specific creation functions
- Pattern: `_create_X_page()` for each Confluence page type
- Target: Main function ~30 lines with page creation loop

**3. pmp_api_comprehensive_inventory.py:139 (210 lines)**
- Extract endpoint handlers + report generators
- Pattern: `_test_endpoint_X()`, `_generate_report()`
- Target: Main inventory function ~50 lines

**4. pmp_complete_intelligence_extractor_v4_resume.py (209 lines)**
- Extract schema creation + index creation helpers
- Pattern: `_create_X_table()`, `_create_indexes()`
- Target: init_database ~30 lines

---

## HIGH Priority (Top 10 of 28 - SHOULD-FIX)

| # | File | Function | Lines | Line |
|---|------|----------|-------|------|
| 1 | `production_readiness_report.py` | `check_production_readiness` | 198 | 14 |
| 2 | `reindex_comments_with_quality.py` | `reindex_with_checkpoints` | 189 | 37 |
| 3 | `intelligent_product_grouper.py` | `standardize_product_names` | 188 | 17 |
| 4 | `historical_email_analyzer.py` | `generate_report` | 188 | 118 |
| 5 | `trello_mcp_server.py` | `handle_list_tools` | 185 | 620 |
| 6 | `pmp_complete_intelligence_extractor_v3.py` | `init_database` | 184 | 44 |
| 7 | `server.py` (linkedin) | `LinkedInMCPServer.serve` | 184 | 305 |
| 8 | `pmp_non_esu_systems_export.py` | `main` | 183 | 171 |
| 9 | `system_backup_manager.py` | `main` | 178 | 394 |
| 10 | `secret_detector.py` | `_initialize_patterns` | 176 | 53 |

---

## Phase 230 Refactoring Protocol

### R1 - TDD Foundation
```bash
# Verify existing tests or create smoke tests
python3 -m pytest claude/tools/tests/test_<module>.py -v 2>/dev/null || echo "No tests - create smoke test"
```

### R2 - Extraction Pattern
```python
# Before (monolithic)
def huge_function():
    # 200+ lines of mixed concerns

# After (decomposed)
def huge_function():
    """Orchestrator - now 20-40 lines."""
    result = _step_one()
    _step_two(result)
    return _step_three()

def _step_one(): ...  # 20-40 lines each
def _step_two(): ...
def _step_three(): ...
```

### R3 - Smoke Test Verification
```bash
# After each refactoring
python3 -c "from module import function; print('Import OK')"
python3 <script.py> --help 2>/dev/null || python3 -c "import <module>; print('OK')"
```

---

## Execution Order

1. **disaster_recovery_system.py** (400 lines - highest impact)
2. **create_azure_lighthouse_confluence_pages.py** (369 lines)
3. **pmp_api_comprehensive_inventory.py** (210 lines)
4. **pmp_complete_intelligence_extractor_v4_resume.py** (209 lines)
5. Continue with HIGH priority by line count descending

---

## Key Data
```json
{
  "must_fix": 4,
  "should_fix": 28,
  "advisory": 97,
  "total_functions": 129,
  "tdd_required": true,
  "refactoring_pattern": "Phase 230 helper extraction",
  "target_max_lines": 50,
  "smoke_test_required": true
}
```

---

## Success Criteria

- [ ] All 4 CRITICAL functions refactored to <80 lines
- [ ] Smoke tests pass for all modified files
- [ ] No import errors introduced
- [ ] Git commit with Phase 230 reference

---

## Scanner Command (for verification)

```bash
# Re-scan after refactoring to verify
python3 claude/tools/sre/python_function_scanner.py claude/tools/ --min-lines 100
```

---

**Review Status**: BLOCKED - Awaiting SRE execution
**Handoff Initiated**: 2026-01-03
