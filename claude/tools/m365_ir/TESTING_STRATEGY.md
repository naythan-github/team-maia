# M365 IR Data Quality System - Testing Strategy

**Project**: M365-DQ-2026-001
**Version**: 1.0
**Last Updated**: 2026-01-06

---

## Executive Summary

This document defines the Test-Driven Development (TDD) strategy for the M365 IR Data Quality System rebuild. The project mandates **100% test coverage** for all new code, with tests written **before implementation**.

**Key Principle**: **Red → Green → Refactor**
1. **Red**: Write failing test first
2. **Green**: Implement minimum code to pass
3. **Refactor**: Improve while keeping tests green

---

## Testing Philosophy

### Why TDD for This Project?

The PIR-OCULUS incident demonstrated catastrophic consequences of data interpretation errors:
- 8 accounts compromised
- 44-day dwell time
- Forensic report concluded "attack failed" when it succeeded

**Root Cause**: No automated validation caught the wrong field selection (`status_error_code` vs `conditional_access_status`).

**Solution**: TDD ensures every failure mode has a corresponding test that prevents regression.

### Testing Pyramid

```
       /\
      /  \     10% - End-to-End Tests (full IR workflow)
     /----\
    /      \   30% - Integration Tests (tool combinations)
   /--------\
  /          \ 60% - Unit Tests (individual functions)
 /____________\
```

**Target Distribution**:
- **60% Unit Tests**: Fast, isolated, test single functions
- **30% Integration Tests**: Test tool interactions and data flow
- **10% E2E Tests**: Full import → verification → analysis workflow

---

## TDD Workflow

### Standard TDD Cycle

For every feature:

1. **Write Test First** (Test file in `tests/m365_ir/data_quality/`)
   ```python
   def test_verify_sign_in_logs_detects_breach(oculus_test_db):
       """Test that system detects Oculus-style breach."""
       from claude.tools.m365_ir.auth_verifier import verify_sign_in_status

       result = verify_sign_in_status(oculus_test_db)

       assert result.breach_detected is True  # WILL FAIL initially
   ```

2. **Run Test - Expect Failure**
   ```bash
   pytest tests/m365_ir/data_quality/test_extended_auth_verifier.py::test_verify_sign_in_logs_detects_breach -v
   # Expected: ImportError or AssertionError
   ```

3. **Implement Minimum Code**
   ```python
   # claude/tools/m365_ir/auth_verifier.py
   def verify_sign_in_status(db_path: str) -> SignInVerificationSummary:
       # Minimum implementation to pass test
       return SignInVerificationSummary(breach_detected=True)
   ```

4. **Run Test - Expect Pass**
   ```bash
   pytest tests/m365_ir/data_quality/test_extended_auth_verifier.py::test_verify_sign_in_logs_detects_breach -v
   # Expected: PASSED
   ```

5. **Refactor** (improve code quality while keeping test green)
   ```python
   def verify_sign_in_status(db_path: str) -> SignInVerificationSummary:
       # Proper implementation with edge case handling
       conn = sqlite3.connect(db_path)
       # ... full logic ...
       return SignInVerificationSummary(breach_detected=analysis.is_breach())
   ```

6. **Repeat** for next test case

### Commit Discipline

**Every commit must have passing tests**:
```bash
# Before committing:
pytest tests/m365_ir/data_quality/ -v --tb=short

# If all pass:
git add .
git commit -m "feat(auth_verifier): Add sign_in_logs verification

- Detect breach via conditional_access_status field
- Reject unreliable status_error_code field (100% uniform)
- Alert on >80% foreign IP success rate
- Tests: test_extended_auth_verifier.py (6 tests, all passing)"

# Pre-commit hook will enforce test pass
```

---

## Test Organization

### Directory Structure

```
tests/m365_ir/data_quality/
├── __init__.py                          # Test package init
├── conftest.py                          # Shared fixtures
├── test_extended_auth_verifier.py       # Phase 1.1 tests
├── test_quality_checker.py              # Phase 1.2 tests
├── test_status_codes.py                 # Phase 1.3 tests
├── test_reliability_scorer.py           # Phase 2.1 tests
├── test_dashboard.py                    # Phase 2.2 tests
├── test_alerting.py                     # Phase 2.3 tests
└── integration/                         # Integration tests
    ├── test_full_import_workflow.py
    └── test_oculus_case_reproduction.py
```

### Test Naming Convention

**Format**: `test_{module}_{action}_{condition}`

Examples:
- `test_verify_sign_in_logs_detects_breach()` - verify sign_in_logs when breach present
- `test_verify_sign_in_logs_with_perfect_data()` - verify when data quality is perfect
- `test_quality_checker_rejects_uniform_field()` - quality checker behavior on bad data

**Docstring Requirements**:
- What is being tested
- Expected input/conditions
- Expected output/behavior
- Why this test matters (link to requirement/error if applicable)

---

## Test Fixtures

### Core Fixtures (conftest.py)

| Fixture | Purpose | Usage |
|---------|---------|-------|
| `temp_db` | Clean temporary SQLite database | Base fixture for custom schemas |
| `oculus_test_db` | Recreates PIR-OCULUS scenario | Test breach detection |
| `perfect_quality_db` | High-quality data (all fields populated) | Test happy path |
| `bad_quality_db` | Poor quality data (uniform fields) | Test quality checks |
| `status_code_reference_db` | Lookup table with known codes | Test code resolution |
| `synthetic_data_generator` | Helper to generate test data | Create custom scenarios |

### Fixture Usage Examples

```python
def test_breach_detection(oculus_test_db):
    """Use oculus_test_db to test Oculus-style breach."""
    result = verify_sign_in_status(oculus_test_db)
    assert result.breach_detected is True

def test_quality_pass(perfect_quality_db):
    """Use perfect_quality_db to test happy path."""
    result = check_data_quality(perfect_quality_db)
    assert result.quality_score >= 0.95

def test_quality_fail(bad_quality_db):
    """Use bad_quality_db to test quality check failures."""
    result = check_data_quality(bad_quality_db)
    assert result.quality_score < 0.5

def test_custom_scenario(temp_db, synthetic_data_generator):
    """Create custom test scenario."""
    logs = synthetic_data_generator.generate_sign_in_logs(
        count=100,
        breach=True,
        uniform_status=False
    )
    # Insert into temp_db and test
```

---

## Test Categories and Markers

### Pytest Markers

Mark tests by phase and type:

```python
# Phase markers
@pytest.mark.phase_0    # Phase 0: Project Setup
@pytest.mark.phase_1_1  # Phase 1.1: Extended Auth Verifier
@pytest.mark.phase_1_2  # Phase 1.2: Quality Checker
@pytest.mark.phase_1_3  # Phase 1.3: Status Code Lookups
@pytest.mark.phase_2_1  # Phase 2.1: Reliability Scorer
@pytest.mark.phase_2_2  # Phase 2.2: Dashboard
@pytest.mark.phase_2_3  # Phase 2.3: Alerting

# Type markers
@pytest.mark.unit           # Unit test (single function)
@pytest.mark.integration    # Integration test (multiple tools)
@pytest.mark.e2e            # End-to-end test (full workflow)
@pytest.mark.performance    # Performance/benchmark test
@pytest.mark.regression     # Regression test (prevent known bug)

# Special markers
@pytest.mark.critical       # Critical test (must always pass)
@pytest.mark.slow           # Slow test (>1 second)
```

### Running Tests by Category

```bash
# Run all Phase 1.1 tests
pytest -m phase_1_1 -v

# Run only unit tests
pytest -m unit -v

# Run critical tests only (CI/CD fast check)
pytest -m critical -v

# Run all tests except slow ones
pytest -m "not slow" -v

# Run integration tests for Phase 1
pytest -m "integration and (phase_1_1 or phase_1_2 or phase_1_3)" -v
```

---

## Coverage Requirements

### Minimum Coverage Targets

| Component | Target | Enforcement |
|-----------|--------|-------------|
| **Overall** | 100% | Pre-commit hook blocks <95% |
| **Core verification** | 100% | Manual review required |
| **Quality checks** | 100% | Manual review required |
| **Utilities** | 95% | Acceptable |
| **Integration tests** | 90% | Acceptable |

### Measuring Coverage

```bash
# Run tests with coverage report
pytest tests/m365_ir/data_quality/ --cov=claude/tools/m365_ir --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html

# Fail if coverage < 95%
pytest tests/m365_ir/data_quality/ --cov=claude/tools/m365_ir --cov-fail-under=95
```

### Coverage Enforcement

Pre-commit hook checks coverage:
```bash
# .git/hooks/pre-commit (partial)
pytest tests/m365_ir/data_quality/ --cov=claude/tools/m365_ir --cov-fail-under=95 -q
if [ $? -ne 0 ]; then
    echo "ERROR: Test coverage below 95%. Commit blocked."
    exit 1
fi
```

---

## Performance Testing

### Performance Benchmarks

All verification tools must meet performance targets:

| Operation | Dataset Size | Target | Test |
|-----------|-------------|--------|------|
| `verify_sign_in_status()` | 10K events | <2 seconds | `test_verify_sign_in_logs_performance()` |
| `verify_audit_log_operations()` | 10K events | <2 seconds | `test_verify_audit_log_performance()` |
| `check_data_quality()` | 10K events | <1 second | `test_quality_checker_performance()` |
| `calculate_reliability_score()` | 100K events | <5 seconds | `test_reliability_scorer_performance()` |
| Full import workflow | 27K events (Oculus size) | <5 minutes | `test_full_oculus_import_e2e()` |

### Performance Test Pattern

```python
import time
import pytest

def test_verify_sign_in_logs_performance(oculus_test_db):
    """Test that verification completes in <2 seconds for 3K records."""
    from claude.tools.m365_ir.auth_verifier import verify_sign_in_status

    start = time.time()
    result = verify_sign_in_status(oculus_test_db)
    elapsed = time.time() - start

    assert elapsed < 2.0, f"Verification took {elapsed:.2f}s, target <2s"
    assert result.total_records == 2987  # Verify correctness too
```

---

## Integration Testing

### Integration Test Scope

Integration tests verify:
1. **Tool Combinations**: auth_verifier + quality_checker + status_code_manager
2. **Database Interactions**: Multi-table joins, transaction integrity
3. **Import Pipeline**: CSV import → verification → quality check → storage
4. **Alerting Workflow**: Breach detected → alert triggered → email sent

### Key Integration Tests

| Test | What It Validates | Files Involved |
|------|-------------------|----------------|
| `test_full_import_workflow()` | End-to-end import with all verifications | log_importer.py, auth_verifier.py, quality_checker.py |
| `test_oculus_case_reproduction()` | Exact Oculus scenario reproduction | All Phase 1 components |
| `test_quality_check_blocks_bad_import()` | Bad data rejected at import | log_importer.py, quality_checker.py |
| `test_breach_alert_email_delivery()` | Alert reaches SRE team | auth_verifier.py, alert_system.py |

### Integration Test Example

```python
@pytest.mark.integration
@pytest.mark.e2e
def test_full_oculus_import_workflow(temp_db):
    """
    End-to-end test: Import Oculus CSVs → Verify → Detect Breach → Alert.

    This is the master integration test that validates the entire system.
    """
    from claude.tools.m365_ir.log_importer import import_logs
    from claude.tools.m365_ir.auth_verifier import verify_sign_in_status
    from claude.tools.m365_ir.quality_checker import check_data_quality
    from claude.tools.m365_ir.alert_system import get_last_alert

    # Step 1: Import sign_in_logs CSV
    import_result = import_logs('test_data/oculus_sign_in_logs.csv', temp_db, 'sign_in_logs')
    assert import_result.records_imported == 2987

    # Step 2: Verification should auto-run (called by import_logs)
    assert import_result.verification_ran is True
    assert import_result.verification_status == 'BREACH_DETECTED'

    # Step 3: Quality check should pass (conditional_access_status reliable)
    quality_result = check_data_quality(temp_db, 'sign_in_logs')
    assert quality_result.quality_score >= 0.9

    # Step 4: Breach alert should be sent
    alert = get_last_alert()
    assert alert is not None
    assert alert.severity == 'CRITICAL'
    assert alert.message.startswith('Breach indicator detected')

    # Step 5: Verify stored results
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM verification_summary WHERE log_type='sign_in_logs'")
    row = cursor.fetchone()
    assert row is not None
    conn.close()
```

---

## Regression Testing

### Preventing Known Errors

Every discovered bug gets a regression test:

| Bug/Error | Regression Test | Prevents |
|-----------|----------------|----------|
| PIR-OCULUS wrong field | `test_verify_sign_in_logs_rejects_unreliable_field()` | Using status_error_code instead of conditional_access_status |
| Uniform field false positive | `test_quality_checker_detects_uniform_field()` | Trusting 100% uniform fields |
| Missing verification | `test_log_importer_calls_all_verifiers()` | Skipping verification on import |
| False breach alert | `test_breach_alert_does_not_trigger_for_normal_traffic()` | Alerting on business travel |

### Regression Test Pattern

```python
@pytest.mark.regression
@pytest.mark.critical
def test_pir_oculus_error_prevented(oculus_test_db):
    """
    REGRESSION TEST: Prevent PIR-OCULUS class error.

    Bug: Used status_error_code (100% uniform) instead of conditional_access_status.
    Result: Concluded "attack failed" when 8 accounts were compromised.

    This test ensures the system REJECTS unreliable fields and uses ground truth.
    """
    from claude.tools.m365_ir.auth_verifier import verify_sign_in_status

    result = verify_sign_in_status(oculus_test_db)

    # MUST use correct field
    assert result.status_field_used == 'conditional_access_status', \
        "REGRESSION: System used wrong status field (Oculus error pattern)"

    # MUST detect breach
    assert result.breach_detected is True, \
        "REGRESSION: Failed to detect breach (Oculus false negative)"

    # MUST warn about unreliable field
    assert any('status_error_code' in w for w in result.warnings), \
        "REGRESSION: Did not warn about unreliable field"
```

---

## Test Data Management

### Synthetic Test Data

Use `synthetic_data_generator` fixture for predictable test data:

```python
def test_with_synthetic_data(temp_db, synthetic_data_generator):
    """Generate custom test scenario."""

    # Generate 500 sign-in logs with 10% breach traffic
    logs = synthetic_data_generator.generate_sign_in_logs(
        count=500,
        breach=True,  # Include breach traffic
        uniform_status=False,  # Don't make status_error_code uniform
        countries=['AU', 'US', 'CN']
    )

    # Insert into database
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    # ... insert logs ...

    # Test your function
    result = verify_sign_in_status(temp_db)
    assert result.breach_detected is True
```

### Real Test Data (Anonymized)

For critical tests, use anonymized real data:

```
tests/m365_ir/data_quality/test_data/
├── oculus_sign_in_logs.csv         # Anonymized Oculus sign-in logs
├── oculus_unified_audit_log.csv    # Anonymized audit logs
├── perfect_quality_sample.csv      # High-quality real data sample
└── README.md                       # Data source and anonymization notes
```

**Anonymization Requirements**:
- Replace UPNs with `user{N}@test.com`
- Preserve country codes and timestamps
- Preserve status codes (critical for testing)
- Remove all PII (names, real emails, phone numbers)

---

## Continuous Integration

### CI Pipeline (GitHub Actions)

```yaml
# .github/workflows/m365_ir_data_quality_tests.yml
name: M365 IR Data Quality Tests

on:
  push:
    paths:
      - 'claude/tools/m365_ir/**'
      - 'tests/m365_ir/data_quality/**'
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run critical tests
        run: pytest -m critical -v --tb=short

      - name: Run all tests with coverage
        run: |
          pytest tests/m365_ir/data_quality/ \
            --cov=claude/tools/m365_ir \
            --cov-report=html \
            --cov-report=term \
            --cov-fail-under=95 \
            -v

      - name: Upload coverage report
        uses: actions/upload-artifact@v3
        with:
          name: coverage-report
          path: htmlcov/
```

### Pre-Commit Hooks

Local pre-commit hook enforces test pass:

```bash
#!/bin/bash
# .git/hooks/pre-commit

echo "Running M365 IR Data Quality tests..."

# Run critical tests (fast)
pytest tests/m365_ir/data_quality/ -m critical -q
if [ $? -ne 0 ]; then
    echo "❌ CRITICAL TESTS FAILED - Commit blocked"
    exit 1
fi

# Run all tests with coverage
pytest tests/m365_ir/data_quality/ \
    --cov=claude/tools/m365_ir \
    --cov-fail-under=95 \
    -q

if [ $? -ne 0 ]; then
    echo "❌ TESTS FAILED or COVERAGE <95% - Commit blocked"
    exit 1
fi

echo "✅ All tests passed with coverage ≥95%"
exit 0
```

---

## Debugging Failed Tests

### Verbose Output

```bash
# Run with verbose output and full traceback
pytest tests/m365_ir/data_quality/test_extended_auth_verifier.py::test_verify_sign_in_logs_detects_breach -vv --tb=long

# Show local variables in traceback
pytest tests/m365_ir/data_quality/test_extended_auth_verifier.py::test_verify_sign_in_logs_detects_breach -vv --tb=long --showlocals
```

### Print Debugging in Tests

```python
def test_debug_example(oculus_test_db):
    """Example of debug output in tests."""
    import sqlite3

    # Check database state
    conn = sqlite3.connect(oculus_test_db)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM sign_in_logs")
    count = cursor.fetchone()[0]
    print(f"\n🔍 DEBUG: sign_in_logs record count: {count}")

    cursor.execute("SELECT DISTINCT conditional_access_status FROM sign_in_logs")
    statuses = [row[0] for row in cursor.fetchall()]
    print(f"🔍 DEBUG: Unique statuses: {statuses}")
    conn.close()

    # Run test
    result = verify_sign_in_status(oculus_test_db)
    print(f"🔍 DEBUG: Result: {result}")

    assert result.breach_detected is True
```

Run with `-s` to see print statements:
```bash
pytest tests/m365_ir/data_quality/test_extended_auth_verifier.py::test_debug_example -s
```

### Interactive Debugging

```bash
# Drop into debugger on failure
pytest tests/m365_ir/data_quality/test_extended_auth_verifier.py::test_verify_sign_in_logs_detects_breach --pdb

# Drop into debugger on first failure
pytest tests/m365_ir/data_quality/ -x --pdb
```

---

## Test Maintenance

### Updating Tests When Requirements Change

When requirements change:
1. **Update test first** (TDD principle holds)
2. **Run test - expect failure**
3. **Update implementation**
4. **Run test - expect pass**

Example:
```python
# Old requirement: Alert on >80% foreign success
def test_breach_alert_threshold():
    assert result.breach_detected is True  # 85% foreign

# New requirement: Alert on >90% foreign success
def test_breach_alert_threshold():
    assert result.breach_detected is False  # 85% foreign (below new threshold)
```

### Deprecating Tests

When tests become obsolete:
1. Mark with `@pytest.mark.skip` and reason
2. Document in test docstring
3. Remove after 2 releases

```python
@pytest.mark.skip(reason="Status code lookup deprecated in v2.0 (replaced by API)")
def test_status_code_lookup_legacy():
    """Legacy test - kept for reference, remove after v2.2."""
    pass
```

---

## Summary

### TDD Checklist

For every feature:
- [ ] Write failing test first
- [ ] Run test - confirm failure
- [ ] Implement minimum code to pass
- [ ] Run test - confirm pass
- [ ] Refactor (keep test green)
- [ ] Commit with passing tests
- [ ] Verify coverage ≥95%

### Key Testing Principles

1. **Tests First**: No implementation without failing test
2. **100% Coverage Target**: <95% blocks commit
3. **Regression Prevention**: Every bug gets a test
4. **Performance Validation**: Benchmarks in tests
5. **Integration Over Isolation**: Test real workflows
6. **Fail Fast**: Critical tests run first
7. **Maintainability**: Clear names, docstrings, fixtures

---

**Last Updated**: 2026-01-06
**Next Review**: End of Phase 1 (Week 4)
