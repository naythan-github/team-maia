## PMP Test Execution Guide

**Purpose**: Comprehensive guide for running, debugging, and maintaining the PMP test suite
**Audience**: Developers, SRE, QA Engineers
**Prerequisites**: Python 3.9+, pytest, sqlite3

---

## Quick Start

### Run All Tests
```bash
cd claude/tools/pmp
python3 -m pytest tests/ -v
```

### Run Critical Tests Only
```bash
python3 -m pytest tests/ -m critical -v
```

### Run Specific Category
```bash
# Schema validation tests
python3 -m pytest tests/test_schema_validation.py -v

# Data integrity tests
python3 -m pytest tests/test_data_integrity.py -v

# API integration tests
python3 -m pytest tests/test_api_integration.py -v
```

---

## Test Organization

### Directory Structure
```
claude/tools/pmp/tests/
├── __init__.py                      # Test package
├── conftest.py                      # Pytest fixtures (15 fixtures)
├── fixtures/                        # Mock data
│   ├── mock_api_responses.json
│   └── sample_patches.json
├── test_schema_validation.py        # Schema correctness (17 tests)
├── test_data_integrity.py           # Data preservation (11 tests)
├── test_api_integration.py          # API bugs validation (21 tests)
├── test_resume_capability.py        # Resume logic (9 tests)
├── test_error_handling.py           # Error handling (9 tests)
├── test_performance.py              # Performance (7 tests)
├── test_wal_concurrency.py          # WAL mode (8 tests)
└── test_integration.py              # End-to-end (4 tests)
```

**Total**: 86 tests across 8 categories

---

## Test Markers

### Available Markers

```python
@pytest.mark.unit              # Fast, isolated tests
@pytest.mark.integration       # Slower, external dependencies
@pytest.mark.critical          # Must pass before deployment
@pytest.mark.schema            # Database schema validation
@pytest.mark.api               # API integration tests
@pytest.mark.data_integrity    # Data preservation tests
@pytest.mark.resume            # Resume capability tests
@pytest.mark.error_handling    # Error handling tests
@pytest.mark.performance       # Performance tests
@pytest.mark.wal               # WAL mode tests
```

### Usage Examples

```bash
# Run only critical tests (blocking)
python3 -m pytest -m critical

# Run schema + data integrity tests
python3 -m pytest -m "schema or data_integrity"

# Run all except performance tests
python3 -m pytest -m "not performance"

# Run integration tests only
python3 -m pytest -m integration
```

---

## Common Use Cases

### Pre-Commit Validation
```bash
# Run before committing code
python3 -m pytest tests/ -m critical --tb=short

# If ANY test fails: DO NOT COMMIT
# Fix the test or code, then re-run
```

### Debugging Failed Tests
```bash
# Run single failing test with full traceback
python3 -m pytest tests/test_data_integrity.py::test_extract_supported_patches_preserves_all_records -vv

# Show local variables in traceback
python3 -m pytest tests/test_data_integrity.py::test_extract_supported_patches_preserves_all_records -vv -l

# Drop into debugger on failure
python3 -m pytest tests/test_data_integrity.py::test_extract_supported_patches_preserves_all_records --pdb
```

### Performance Profiling
```bash
# Run with timing
python3 -m pytest tests/test_performance.py -v --durations=10

# Show slowest 10 tests
python3 -m pytest tests/ --durations=10
```

### Coverage Analysis
```bash
# Generate coverage report
pip3 install pytest-cov
python3 -m pytest tests/ --cov=. --cov-report=html

# View report
open tests/coverage_html/index.html
```

---

## Understanding Test Results

### PASSED (✅)
```
tests/test_schema_validation.py::test_supported_patches_primary_key_is_unique PASSED
```
**Meaning**: Test executed successfully, all assertions passed
**Action**: None required

### FAILED (❌)
```
FAILED tests/test_data_integrity.py::test_extract_supported_patches_preserves_all_records
AssertionError: Expected 1000 records, got 10
```
**Meaning**: Test detected a bug or regression
**Action**:
1. Review error message
2. Check if code bug or test bug
3. Fix and re-run
4. **DO NOT COMMIT** until test passes

### SKIPPED (⊘)
```
tests/test_integration.py::test_real_api_call SKIPPED [missing credentials]
```
**Meaning**: Test intentionally skipped (missing dependency, slow test, etc.)
**Action**: Review skip reason, address if needed

### ERROR (⚠️)
```
ERROR tests/test_api_integration.py::test_oauth_flow - ImportError: No module named 'requests'
```
**Meaning**: Test setup failed (missing import, fixture error, etc.)
**Action**:
1. Install missing dependencies
2. Fix fixture or setup code
3. Re-run

---

## Fixtures Reference

### Database Fixtures

**`temp_db`**: Temporary SQLite database with schema
```python
def test_something(temp_db):
    conn = sqlite3.connect(temp_db)
    # ... test code
```

**`temp_db_corrected`**: Database with CORRECTED schema (patch_id PRIMARY KEY)
```python
def test_fixed_schema(temp_db_corrected):
    # Test with corrected schema
```

**`extraction_id`**: Pre-created extraction run ID
```python
def test_extraction(temp_db, extraction_id):
    # extraction_id already exists in api_extraction_runs
```

### Mock Data Fixtures

**`mock_supported_patches`**: 1000 realistic patch records
```python
def test_bulk_insert(temp_db, mock_supported_patches):
    assert len(mock_supported_patches) == 1000
```

**`mock_all_patches`**: 100 patch records
**`mock_api_response`**: Generic API response wrapper

### Mock API Fixtures

**`mock_oauth_manager`**: Mocked PMPOAuthManager
```python
def test_oauth(mock_oauth_manager):
    headers = mock_oauth_manager.get_auth_headers()
```

**`mock_api_success_response`**: 200 OK response
**`mock_api_rate_limit_response`**: 429 Too Many Requests
**`mock_api_html_throttle_response`**: HTML throttling page

### Helper Fixtures

**`db_helper`**: Database utility functions
```python
def test_count(temp_db, db_helper):
    count = db_helper.get_count(temp_db, 'supported_patches')
    schema = db_helper.get_schema(temp_db, 'supported_patches')
    exists = db_helper.record_exists(temp_db, 'supported_patches', patch_id=1)
```

---

## Test Development Workflow

### TDD Cycle (RED → GREEN → REFACTOR)

**Step 1: Write Failing Test (RED)**
```python
def test_new_feature():
    """Test new feature description"""
    result = new_feature()
    assert result == expected_value
```

Run test:
```bash
python3 -m pytest tests/test_new_feature.py::test_new_feature -v
# ❌ FAILED (no implementation yet)
```

**Step 2: Implement Minimal Code (GREEN)**
```python
def new_feature():
    return expected_value  # Minimal implementation
```

Run test:
```bash
python3 -m pytest tests/test_new_feature.py::test_new_feature -v
# ✅ PASSED
```

**Step 3: Refactor (REFACTOR)**
```python
def new_feature():
    # Improve implementation
    # Add error handling
    # Optimize performance
    return expected_value
```

Run full suite:
```bash
python3 -m pytest tests/ -m critical
# ✅ All tests PASSED
```

**Step 4: Commit**
```bash
git add tests/test_new_feature.py pmp_new_feature.py
git commit -m "Add new feature with TDD validation"
```

---

## Continuous Integration

### Pre-Commit Hook

Create `.git/hooks/pre-commit`:
```bash
#!/bin/bash
# Run critical tests before commit
python3 -m pytest claude/tools/pmp/tests/ -m critical --tb=short

if [ $? -ne 0 ]; then
    echo "❌ Tests failed - commit blocked"
    exit 1
fi

echo "✅ Tests passed - commit allowed"
exit 0
```

Make executable:
```bash
chmod +x .git/hooks/pre-commit
```

### GitHub Actions (Future)

See `claude/tools/pmp/docs/CONTRIBUTING.md` for CI/CD pipeline setup.

---

## Troubleshooting

### Tests Fail Locally But Pass in CI
**Cause**: Environment differences (Python version, dependencies, etc.)
**Solution**: Use same Python version as CI, check dependency versions

### Database Locked Errors
**Cause**: Multiple connections to temp database
**Solution**: Ensure connections are closed in tests:
```python
conn = sqlite3.connect(temp_db)
# ... test code
conn.close()  # Always close!
```

### Intermittent Test Failures
**Cause**: Race conditions in concurrent tests
**Solution**: Use proper synchronization or isolate tests:
```python
@pytest.mark.order(1)  # Run first
def test_setup():
    pass

@pytest.mark.order(2)  # Run after setup
def test_dependent():
    pass
```

### Slow Test Execution
**Cause**: Too many tests, large datasets
**Solution**:
1. Use `-m critical` to run subset
2. Reduce test dataset size
3. Run tests in parallel: `pytest -n 4` (requires pytest-xdist)

---

## Best Practices

### ✅ DO

- **Run tests before committing** (pre-commit hook)
- **Fix failing tests immediately** (don't accumulate technical debt)
- **Add tests for bug fixes** (prevent regression)
- **Keep tests fast** (<100ms per unit test)
- **Use descriptive test names** (`test_extract_supported_patches_preserves_all_records`)
- **Document complex tests** (docstrings explaining WHY)

### ❌ DON'T

- **Skip failing tests** (mark as xfail if intentional)
- **Commit without running tests**
- **Remove tests that fail** (fix the bug or test)
- **Write tests that depend on network** (use mocks)
- **Hardcode paths or credentials** (use fixtures and env vars)

---

## Test Maintenance

### Adding New Tests

1. Choose appropriate test file (or create new one)
2. Write test following naming convention: `test_<feature>_<behavior>`
3. Use existing fixtures where possible
4. Add appropriate markers (`@pytest.mark.critical`, etc.)
5. Run test to ensure it passes
6. Run full suite to ensure no regressions

### Updating Tests After Code Changes

1. Identify affected tests (run full suite)
2. Update test expectations if behavior changed intentionally
3. If test still fails, fix the code bug
4. Validate fix with full test suite

### Deprecating Tests

If test is no longer relevant:
1. Document why (comment in code)
2. Remove from test suite
3. Update test count in documentation
4. Commit with clear message

---

## Performance Benchmarks

### Expected Test Execution Times

| Category | Tests | Time | Per Test |
|----------|-------|------|----------|
| Schema Validation | 17 | <1s | <50ms |
| Data Integrity | 11 | <2s | <200ms |
| API Integration | 21 | <1s | <50ms |
| Resume Capability | 9 | <2s | <200ms |
| Error Handling | 9 | <1s | <100ms |
| Performance | 7 | ~5s | ~700ms |
| WAL/Concurrency | 8 | ~3s | ~400ms |
| Integration | 4 | ~2s | ~500ms |
| **TOTAL** | **86** | **~20s** | **~230ms** |

If tests significantly slower: investigate and optimize.

---

## Support

### Getting Help

**Documentation**:
- TDD Checklist: `claude/tools/pmp/pmp_tdd_checklist.md`
- Post-Mortem: `claude/tools/pmp/docs/PRIMARY_KEY_BUG_POSTMORTEM.md`
- Contributing Guide: `claude/tools/pmp/docs/CONTRIBUTING.md`

**Debugging**:
1. Read test docstring (explains what it tests)
2. Check fixture documentation (conftest.py)
3. Run with `-vv` for detailed output
4. Use `--pdb` to drop into debugger

---

**Last Updated**: 2025-12-01
**Version**: 1.0
**Status**: ✅ READY FOR USE
