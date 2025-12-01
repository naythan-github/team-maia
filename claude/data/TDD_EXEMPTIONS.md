# TDD Exemption Log - Phase 217

## Purpose
Track legitimate TDD protocol bypasses using `git commit --no-verify`.

## Process
When using `--no-verify` to bypass TDD enforcement:
1. Include clear justification in commit message
2. Log exemption here with date, file, reason
3. Create follow-up issue if tests need to be added later

## Automatic Exemptions (No logging required)
- `__init__.py` files
- Test files themselves (`test_*.py`, `*_test.py`)
- `conftest.py` (pytest config)
- `setup.py` scripts
- `README.md` documentation
- `requirements.txt`, `requirements.md`

## Manual Exemptions Log

### Format
```
Date: YYYY-MM-DD
File: path/to/file.py
Reason: Why TDD was skipped
Remediation: Plan to add tests (or "N/A - utility script")
Commit: <commit-hash>
```

---

### 2025-12-01
**File**: `claude/hooks/pre_commit_tdd_gate.py`
**Reason**: Pre-commit hook created during TDD enforcement implementation (Phase 217)
**Remediation**: Will add tests in Phase 217 completion
**Commit**: TBD
**Status**: ✅ Tests added in same phase

---

## Statistics
- Total exemptions granted: 1
- With remediation plan: 1 (100%)
- Remediated: 0 (pending)

## Review Schedule
- Monthly review of outstanding exemptions
- Close exemptions when tests added
- Track trends (increasing exemptions = enforcement problem)
