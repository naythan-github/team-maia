"""
M365 IR Data Quality System - Test Suite

This package contains comprehensive tests for the M365 IR Data Quality System,
following Test-Driven Development (TDD) principles.

Test Organization:
- test_extended_auth_verifier.py: Phase 1.1 - Extended authentication verification
- test_quality_checker.py: Phase 1.2 - Pre-analysis quality checks
- test_status_codes.py: Phase 1.3 - Status code lookup tables
- test_reliability_scorer.py: Phase 2.1 - Field reliability scoring
- test_alerting.py: Phase 2.3 - Alerting system
- conftest.py: Shared pytest fixtures
- test_data_generators.py: Synthetic test data generators

TDD Protocol:
1. Write failing test first
2. Implement minimum code to pass test
3. Refactor while keeping tests green
4. Repeat

Test Coverage Target: 100%
"""

__version__ = "0.1.0"
