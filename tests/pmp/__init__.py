"""
PMP Test Suite

Comprehensive testing for Patch Manager Plus API extraction tools.

Test Categories:
1. Schema Validation (test_schema_validation.py)
2. API Integration (test_api_integration.py)
3. Data Integrity (test_data_integrity.py) - CRITICAL
4. Resume Capability (test_resume_capability.py)
5. Error Handling (test_error_handling.py)
6. Performance (test_performance.py)
7. WAL/Concurrency (test_wal_concurrency.py)
8. Integration (test_integration.py)

Usage:
    # Run all tests
    pytest

    # Run specific category
    pytest -m critical

    # Run specific test file
    pytest tests/test_data_integrity.py

    # Run with coverage
    pytest --cov=. --cov-report=html

    # Run verbose
    pytest -v

See: claude/tools/pmp/pmp_tdd_checklist.md for complete testing protocol
"""

__version__ = "1.0.0"
