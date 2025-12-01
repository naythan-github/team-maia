# Contributing to PMP Extraction Tools

**Purpose**: Guidelines for contributing to Patch Manager Plus extraction tools
**Scope**: Code contributions, bug fixes, feature additions, documentation
**Required Reading**: This document + `pmp_tdd_checklist.md`

---

## Prerequisites

### Required Knowledge
- Python 3.9+
- SQLite database design
- REST API integration
- OAuth 2.0 authentication
- Test-Driven Development (TDD)

### Required Tools
- Python 3.9 or higher
- pytest (`pip3 install pytest`)
- sqlite3 (built-in)
- Git

---

## Development Workflow

### 1. Setup Development Environment

```bash
# Clone repository
cd ~/git/maia

# Install dependencies
pip3 install pytest pytest-cov requests

# Verify test environment
python3 -m pytest claude/tools/pmp/tests/ -v
```

### 2. Create Feature Branch

```bash
# Create branch from main
git checkout main
git pull origin main
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/bug-description
```

### 3. Development Process (TDD MANDATORY)

**CRITICAL**: All development MUST follow TDD methodology. See `pmp_tdd_checklist.md`.

#### Step 1: Write Failing Test (RED)

```python
# claude/tools/pmp/tests/test_new_feature.py

def test_new_feature_does_something():
    """
    Test that new feature does XYZ.

    Context: Why this feature is needed
    Expected: What should happen
    """
    result = new_feature_function(input_data)
    assert result == expected_output
```

Run test (should FAIL):
```bash
python3 -m pytest tests/test_new_feature.py::test_new_feature_does_something -v
# ❌ FAILED (function doesn't exist yet)
```

#### Step 2: Implement Minimal Code (GREEN)

```python
# claude/tools/pmp/pmp_new_feature.py

def new_feature_function(input_data):
    """Minimal implementation to pass test"""
    return expected_output
```

Run test (should PASS):
```bash
python3 -m pytest tests/test_new_feature.py::test_new_feature_does_something -v
# ✅ PASSED
```

#### Step 3: Refactor (REFACTOR)

```python
def new_feature_function(input_data):
    """
    Production-quality implementation.

    Args:
        input_data: Description

    Returns:
        Description

    Raises:
        ValueError: If input invalid
    """
    # Add error handling
    if not input_data:
        raise ValueError("Input required")

    # Add business logic
    result = process(input_data)

    return result
```

Run full test suite:
```bash
python3 -m pytest tests/ -m critical
# ✅ All tests PASSED
```

### 4. Code Quality Checks

**Before committing**, verify:

✅ **All tests pass**
```bash
python3 -m pytest tests/ -m critical --tb=short
```

✅ **No syntax errors**
```bash
python3 -m py_compile claude/tools/pmp/pmp_new_feature.py
```

✅ **Code follows style guide** (see Code Standards below)

✅ **Documentation updated** (docstrings, README, guides)

### 5. Commit Changes

```bash
# Stage changes
git add claude/tools/pmp/pmp_new_feature.py
git add claude/tools/pmp/tests/test_new_feature.py

# Commit with descriptive message
git commit -m "Add new feature with TDD validation

- Implemented new_feature_function with error handling
- Added comprehensive tests (5 test cases)
- All tests passing

Refs: #123"
```

### 6. Push and Create Pull Request

```bash
# Push to remote
git push origin feature/your-feature-name

# Create PR via GitHub/GitLab
# Include:
# - Description of changes
# - Test results
# - References to issues
```

---

## Code Standards

### Python Style Guide

**Follow PEP 8** with these specifics:

```python
# Imports: Standard library, third-party, local
import sys
import json
from pathlib import Path

import requests
import sqlite3

from pmp_oauth_manager import PMPOAuthManager

# Constants: UPPER_CASE
PAGE_SIZE = 25
MAX_RETRIES = 3

# Functions: snake_case
def extract_supported_patches(patches: List[Dict]) -> int:
    """Extract supported patches from API response."""
    pass

# Classes: PascalCase
class PMPExtractor:
    """Patch Manager Plus data extractor."""
    pass

# Private methods: _leading_underscore
def _internal_helper(data):
    """Internal helper function."""
    pass
```

### Docstrings

**All public functions/classes MUST have docstrings**:

```python
def extract_endpoint(endpoint: str, table: str, data_key: str) -> int:
    """
    Extract data from PMP API endpoint to database.

    Args:
        endpoint: API endpoint path (e.g., '/api/1.4/patch/supported patches')
        table: Database table name
        data_key: JSON response key containing data

    Returns:
        Number of records extracted

    Raises:
        ValueError: If endpoint or table invalid
        sqlite3.Error: If database operation fails
        requests.RequestException: If API call fails

    Example:
        >>> count = extract_endpoint('/api/1.4/patch/allpatches', 'all_patches', 'allpatches')
        >>> print(f"Extracted {count} patches")
        Extracted 5200 patches
    """
    pass
```

### Error Handling

**Always use specific exceptions**:

```python
# ❌ BAD
try:
    data = response.json()
except:
    pass

# ✅ GOOD
try:
    data = response.json()
except ValueError as e:
    print(f"JSON parse error: {e}")
    return None
except requests.exceptions.RequestException as e:
    print(f"Network error: {e}")
    raise
```

### Database Operations

**Always close connections**:

```python
# ✅ GOOD (context manager)
def query_database(db_path: str):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM patches")
        return cursor.fetchall()
    # Connection automatically closed

# ✅ ALSO GOOD (explicit close)
def query_database_explicit(db_path: str):
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM patches")
        return cursor.fetchall()
    finally:
        conn.close()
```

---

## Testing Requirements

### Test Coverage Requirements

**MANDATORY for all code**:
- Critical path: 100% coverage
- High priority: >90% coverage
- Medium priority: >70% coverage

### Test Categories

**Every feature MUST have tests in appropriate categories**:

1. **Unit Tests**: Test individual functions in isolation
2. **Integration Tests**: Test component interactions
3. **Schema Tests**: Validate database schema correctness
4. **Data Integrity Tests**: Verify data preservation

### Test Naming Convention

```python
# Format: test_<feature>_<behavior>_<condition>

def test_extract_patches_preserves_all_records():
    """Unit test: Verify all fetched records saved"""
    pass

def test_extract_patches_handles_rate_limit_gracefully():
    """Integration test: Rate limit handling"""
    pass

def test_supported_patches_schema_uses_unique_primary_key():
    """Schema test: PRIMARY KEY uniqueness"""
    pass
```

### Test Documentation

**All tests MUST have docstrings**:

```python
def test_extract_supported_patches_preserves_all_records():
    """
    Verify ALL fetched records are saved to database.

    Context:
    - PRIMARY KEY bug caused 99.98% data loss
    - This test would have caught the bug immediately

    Test Scenario:
    - Fetch 1000 patches from API (mock)
    - Insert into database
    - Verify all 1000 saved (not just 10)

    Expected:
    - db_count == 1000
    - All patch_ids unique
    """
    pass
```

---

## Bug Fixes

### Bug Fix Workflow

**MANDATORY steps for ALL bug fixes**:

1. **Create regression test** (test that fails due to bug)
2. **Verify test fails** (confirms bug exists)
3. **Fix the bug** (minimal code change)
4. **Verify test passes** (confirms bug fixed)
5. **Run full test suite** (no regressions)
6. **Document in commit message** (reference issue #)

### Example: Fixing a Bug

**Step 1: Create regression test**
```python
def test_handles_empty_api_response():
    """
    Bug: Crashes on empty API response.

    Expected: Return empty list (not crash)
    """
    response = {}
    records = extract_records(response, 'patches')
    assert records == []  # Should not crash
```

**Step 2: Run test (should FAIL)**
```bash
python3 -m pytest tests/test_bug_fix.py::test_handles_empty_api_response -v
# ❌ FAILED: KeyError: 'patches'
```

**Step 3: Fix the bug**
```python
def extract_records(response, key):
    # BEFORE (buggy)
    # return response[key]  # Crashes if key missing

    # AFTER (fixed)
    return response.get(key, [])  # Returns empty list if missing
```

**Step 4: Verify test passes**
```bash
python3 -m pytest tests/test_bug_fix.py::test_handles_empty_api_response -v
# ✅ PASSED
```

**Step 5: Commit**
```bash
git commit -m "Fix crash on empty API response

- Added .get() fallback for missing keys
- Returns empty list instead of crashing
- Added regression test to prevent recurrence

Fixes: #456"
```

---

## Documentation

### Documentation Requirements

**MANDATORY documentation for all changes**:

1. **Code Comments**: Explain WHY (not what)
2. **Docstrings**: Describe function/class behavior
3. **README Updates**: If feature adds new capabilities
4. **Test Documentation**: Explain test purpose
5. **Post-Mortem**: For significant bugs (use template)

### Documentation Templates

**Post-Mortem Template**:
See `docs/PRIMARY_KEY_BUG_POSTMORTEM.md` as example

**Test Documentation Template**:
```python
def test_feature():
    """
    One-line summary.

    Context: Why this test exists
    Test Scenario: What it does
    Expected: What should happen
    """
```

---

## Pull Request Process

### PR Checklist

**Before creating PR, verify**:

- [ ] All tests passing (`pytest tests/ -m critical`)
- [ ] Code follows style guide (PEP 8)
- [ ] Docstrings added/updated
- [ ] Test coverage >80% on new code
- [ ] Documentation updated
- [ ] Commit messages descriptive
- [ ] No merge conflicts with main

### PR Description Template

```markdown
## Summary
Brief description of changes

## Motivation
Why this change is needed

## Changes
- Added X feature
- Fixed Y bug
- Updated Z documentation

## Testing
- All 72 tests passing
- Added 5 new tests for new feature
- Coverage: 85% on new code

## References
Fixes: #123
Related: #456
```

### Review Process

1. **Self-Review**: Review your own PR first
2. **Automated Tests**: CI runs full test suite
3. **Peer Review**: At least 1 approval required
4. **Address Feedback**: Make requested changes
5. **Merge**: Squash commits, merge to main

---

## Release Process

### Version Numbering

**Semantic Versioning** (MAJOR.MINOR.PATCH):
- **MAJOR**: Breaking changes (schema changes, API changes)
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

- [ ] All tests passing
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version bumped in code
- [ ] Git tag created
- [ ] Release notes written

---

## Getting Help

### Resources

**Documentation**:
- TDD Checklist: `pmp_tdd_checklist.md`
- Test Guide: `docs/TEST_EXECUTION_GUIDE.md`
- Post-Mortem: `docs/PRIMARY_KEY_BUG_POSTMORTEM.md`

**Code Examples**:
- Good examples: `tests/test_schema_validation.py`
- Bad examples: See `docs/PRIMARY_KEY_BUG_POSTMORTEM.md`

**Common Issues**:
- Test failures: `docs/TEST_EXECUTION_GUIDE.md#troubleshooting`
- Database issues: `docs/TEST_EXECUTION_GUIDE.md#database-locked-errors`

---

## Code of Conduct

### Core Principles

1. **Quality Over Speed**: TDD saves time in the long run
2. **Test Before Commit**: No exceptions
3. **Fix Forward**: Fix bugs properly (not Band-Aids)
4. **Document Everything**: Code, tests, decisions
5. **Respect Reviews**: Address feedback constructively

### Prohibited Practices

❌ **NEVER**:
- Commit without running tests
- Skip TDD "to save time"
- Remove failing tests
- Hardcode credentials
- Ignore code review feedback
- Merge with test failures

---

## Examples

### Good Contribution Example

```python
# Feature: Add retry logic for transient API errors

# Test (written FIRST)
def test_retries_on_network_error():
    """
    Verify transient network errors trigger retry.

    Context: API sometimes returns ConnectionError
    Expected: Retry 3 times before failing
    """
    with patch('requests.get', side_effect=[
        requests.exceptions.ConnectionError(),
        requests.exceptions.ConnectionError(),
        Mock(status_code=200, json=lambda: {'data': []})
    ]):
        result = fetch_with_retry('/api/endpoint')
        assert result is not None

# Implementation
def fetch_with_retry(endpoint: str, max_retries: int = 3) -> dict:
    """
    Fetch endpoint with retry on transient errors.

    Args:
        endpoint: API endpoint path
        max_retries: Maximum retry attempts

    Returns:
        API response data

    Raises:
        MaxRetriesExceeded: If all retries fail
    """
    for attempt in range(max_retries):
        try:
            response = requests.get(endpoint)
            return response.json()
        except requests.exceptions.ConnectionError:
            if attempt == max_retries - 1:
                raise MaxRetriesExceeded()
            time.sleep(2 ** attempt)  # Exponential backoff
```

### Bad Contribution Example

```python
# ❌ BAD: No test, no error handling, no documentation

def fetch(url):
    return requests.get(url).json()
```

---

## License

This project follows Maia's licensing terms. By contributing, you agree to these terms.

---

**Last Updated**: 2025-12-01
**Version**: 1.0
**Maintainer**: SRE Principal Engineer Agent
**Status**: ✅ READY FOR USE
