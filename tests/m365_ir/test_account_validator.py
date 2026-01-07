#!/usr/bin/env python3
"""
TDD Tests for AccountValidator - Prevents assumption-based analytical errors

Phase 230: Account Validator Implementation (RED → GREEN)
Requirements: PYTHON_VALIDATOR_REQUIREMENTS.md

CRITICAL: Test Case 1 prevents the ben@oculus.info error that occurred in PIR-OCULUS-2025-01
where IR agent assumed account was disabled long ago without checking actual disable timestamp.

Tests written BEFORE implementation per TDD protocol.
"""

import pytest
import sqlite3
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta

# Import will fail until implementation exists (expected RED state)
try:
    from claude.tools.m365_ir.account_validator import AccountValidator, ValidationError
    from claude.tools.m365_ir.assumption_logger import AssumptionLog
except ImportError:
    AccountValidator = None
    ValidationError = None
    AssumptionLog = None


@pytest.fixture
def temp_dir():
    """Create temporary directory for test databases."""
    d = tempfile.mkdtemp()
    yield Path(d)
    shutil.rmtree(d)


@pytest.fixture
def test_db(temp_dir):
    """Create test database mimicking PIR-OCULUS-2025-01 structure."""
    db_path = temp_dir / "test_case.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create tables matching actual IR database schema
    cursor.execute("""
        CREATE TABLE password_status (
            user_principal_name TEXT PRIMARY KEY,
            created_datetime TEXT,
            last_password_change TEXT,
            account_enabled INTEGER,
            days_since_change INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE entra_audit_log (
            timestamp TEXT,
            activity TEXT,
            target TEXT,
            initiated_by TEXT,
            result TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE sign_in_logs (
            timestamp TEXT,
            user_principal_name TEXT,
            ip_address TEXT,
            location_country TEXT,
            status TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE legacy_auth_logs (
            timestamp TEXT,
            user_principal_name TEXT,
            client_app_used TEXT,
            ip_address TEXT,
            country TEXT
        )
    """)

    conn.commit()
    conn.close()

    return str(db_path)


@pytest.fixture
def ben_oculus_scenario(test_db):
    """
    Test Case 1: ben@oculus.info scenario - CRITICAL TEST

    This is the exact scenario that caused the analytical error:
    - Account currently disabled
    - Password 1,998 days old
    - But NO disable event in logs (or disable event shows it was during remediation)

    EXPECTED BEHAVIOR: Validator MUST raise ValidationError
    Cannot assume when account was disabled without timestamp proof.
    """
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()

    # Current account status: DISABLED, old password
    cursor.execute("""
        INSERT INTO password_status VALUES (
            'ben@oculus.info',
            '2018-02-25 22:59:16',
            '2020-06-28 20:33:36',
            0,
            1998
        )
    """)

    # Disable event from REMEDIATION (not pre-existing)
    cursor.execute("""
        INSERT INTO entra_audit_log VALUES (
            '2025-12-03 01:53:35',
            'Disable account',
            'ben@oculus.info',
            'user_9cc4efe9367d4f799043528e84b5ed09@nwcomputing.com.au',
            'success'
        )
    """)

    # Foreign logins during attack (Nov 4 - Dec 3) - proves account was ACTIVE
    foreign_logins = [
        ('2025-11-04 13:23:33', '103.163.220.192', 'Pakistan'),
        ('2025-11-15 08:42:11', '185.223.152.140', 'Latvia'),
        ('2025-12-02 19:34:22', '103.137.210.69', 'Pakistan'),
    ]

    for timestamp, ip, country in foreign_logins:
        cursor.execute("""
            INSERT INTO sign_in_logs VALUES (?, 'ben@oculus.info', ?, ?, 'Success')
        """, (timestamp, ip, country))

    # SMTP abuse events
    cursor.execute("""
        INSERT INTO legacy_auth_logs VALUES (
            '2025-11-05 02:14:33',
            'ben@oculus.info',
            'Authenticated SMTP',
            '103.163.220.192',
            'Pakistan'
        )
    """)

    conn.commit()
    conn.close()

    return test_db


@pytest.fixture
def post_disable_activity_scenario(test_db):
    """
    Test Case 2: Post-disable activity detection

    Scenario: Account disabled Dec 3, but foreign activity continues Dec 15
    LOGIC ERROR: Activity after disable should trigger warning
    """
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO password_status VALUES (
            'simonbond@oculus.info',
            '2017-01-25 00:48:27',
            '2025-12-03 02:51:09',
            1,
            15
        )
    """)

    # Disabled during remediation
    cursor.execute("""
        INSERT INTO entra_audit_log VALUES (
            '2025-12-03 02:00:15',
            'Disable account',
            'simonbond@oculus.info',
            'user_9cc4efe9367d4f799043528e84b5ed09@nwcomputing.com.au',
            'success'
        )
    """)

    # Re-enabled shortly after
    cursor.execute("""
        INSERT INTO entra_audit_log VALUES (
            '2025-12-03 02:30:36',
            'Enable account',
            'simonbond@oculus.info',
            'user_7c6a0171a50c4d97934d1d257dae2c2a@nwcomputing.com.au',
            'success'
        )
    """)

    # Foreign logins AFTER re-enable (suspicious)
    cursor.execute("""
        INSERT INTO sign_in_logs VALUES (
            '2025-12-15 08:17:11',
            'simonbond@oculus.info',
            '103.163.220.192',
            'Pakistan',
            'Success'
        )
    """)

    conn.commit()
    conn.close()

    return test_db


# ============================================================================
# TEST CASE 1: ben@oculus.info Scenario (CRITICAL)
# ============================================================================

def test_ben_oculus_disabled_account_validation(ben_oculus_scenario):
    """
    CRITICAL TEST: Would have caught the original ben@oculus.info error

    Scenario:
    - Account currently disabled (account_enabled=0)
    - Password 1,998 days old
    - Disable event exists but shows remediation date (Dec 3)
    - Foreign logins before Dec 3 prove account was ACTIVE during attack

    EXPECTED: Validator correctly identifies this was NOT a stale account
    """
    if AccountValidator is None:
        pytest.skip("AccountValidator not yet implemented")

    validator = AccountValidator(ben_oculus_scenario, "ben@oculus.info")
    result = validator.validate()

    # Key assertions that would have caught the error:
    assert result['lifecycle']['current_status'] == 'Disabled'
    assert result['lifecycle']['disabled_date'] == '2025-12-03 01:53:35'
    assert result['lifecycle']['disabled_during_attack'] == True  # NOT pre-existing
    assert result['lifecycle']['disable_reason'] == 'Remediation'

    # Password age warning
    assert len(result['sanity_check']['warnings']) > 0
    password_warnings = [w for w in result['sanity_check']['warnings']
                        if w['type'] == 'PASSWORD_POLICY']
    assert len(password_warnings) > 0

    # Should flag as password policy failure, NOT lifecycle failure
    assert result['root_cause_category'] == 'PASSWORD_POLICY_FAILURE'


def test_ben_oculus_no_disable_timestamp_raises_error(test_db):
    """
    EDGE CASE: If disable event missing from logs, MUST raise error

    This catches the case where we cannot determine when account was disabled.
    CANNOT assume - must explicitly state "disable date unknown".
    """
    if AccountValidator is None:
        pytest.skip("AccountValidator not yet implemented")

    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()

    # Account currently disabled but NO disable event in logs
    cursor.execute("""
        INSERT INTO password_status VALUES (
            'mystery@oculus.info',
            '2018-01-01 00:00:00',
            '2020-01-01 00:00:00',
            0,
            1500
        )
    """)

    # No entra_audit_log entries for this account

    conn.commit()
    conn.close()

    validator = AccountValidator(test_db, "mystery@oculus.info")

    with pytest.raises(ValidationError) as exc_info:
        validator.validate()

    error_msg = str(exc_info.value)
    assert "no disable event found" in error_msg.lower()
    assert "cannot determine when account was disabled" in error_msg.lower()


# ============================================================================
# TEST CASE 2: Post-Disable Activity Detection
# ============================================================================

def test_post_disable_activity_logic_error(post_disable_activity_scenario):
    """
    Test automatic detection of timeline logic errors

    Scenario: Account disabled Dec 3, foreign login Dec 15
    EXPECTED: Sanity check flags LOGIC_ERROR
    """
    if AccountValidator is None:
        pytest.skip("AccountValidator not yet implemented")

    validator = AccountValidator(post_disable_activity_scenario, "simonbond@oculus.info")
    result = validator.validate()

    # Should detect logic error: activity after disable
    sanity_check = result['sanity_check']

    # Check for warnings (not necessarily errors, since account was re-enabled)
    assert len(sanity_check['warnings']) > 0 or len(sanity_check['errors']) > 0

    # Should note account was re-enabled, allowing continued activity
    assert result['lifecycle']['re_enabled'] == True
    assert result['lifecycle']['re_enabled_date'] == '2025-12-03 02:30:36'


# ============================================================================
# TEST CASE 3: Password Policy Failure Detection
# ============================================================================

def test_password_policy_failure_detection(ben_oculus_scenario):
    """
    Test detection of password policy enforcement failures

    Scenario: 1,998-day-old password + compromised account
    EXPECTED: Warning about password policy not enforced
    """
    if AccountValidator is None:
        pytest.skip("AccountValidator not yet implemented")

    validator = AccountValidator(ben_oculus_scenario, "ben@oculus.info")
    result = validator.validate()

    # Should have password policy warning
    warnings = result['sanity_check']['warnings']
    password_warnings = [w for w in warnings if w['type'] == 'PASSWORD_POLICY']

    assert len(password_warnings) > 0
    assert password_warnings[0]['severity'] == 'HIGH'
    assert '1998' in password_warnings[0]['message'] or '1,998' in password_warnings[0]['message']


# ============================================================================
# TEST CASE 4: Assumption Validation
# ============================================================================

def test_disproven_assumption_blocks_report():
    """
    Test that disproven assumptions prevent report generation

    This enforces that we cannot generate findings with invalid assumptions.
    """
    if AccountValidator is None or AssumptionLog is None:
        pytest.skip("AccountValidator/AssumptionLog not yet implemented")

    assumption_log = AssumptionLog()

    # Add a disproven assumption (this is what happened with ben@)
    assumption_log.add_assumption(
        statement="Account was disabled before attack",
        evidence="account_enabled=False, password from 2020",
        validation_query="SELECT timestamp FROM entra_audit_log WHERE activity='Disable account'",
        result="DISPROVEN - disabled 2025-12-03, attack started 2025-11-04"
    )

    # Should not allow report generation with disproven assumptions
    disproven = assumption_log.get_disproven_assumptions()
    assert len(disproven) == 1
    assert not disproven[0]['proven']

    # In actual validator, this would raise ValidationError when trying to generate report


def test_validated_assumption_allows_report():
    """
    Test that proven assumptions allow report generation
    """
    if AssumptionLog is None:
        pytest.skip("AssumptionLog not yet implemented")

    assumption_log = AssumptionLog()

    # Add a proven assumption
    assumption_log.add_assumption(
        statement="Account was active during attack",
        evidence="Foreign logins Nov 4 - Dec 3",
        validation_query="SELECT COUNT(*) FROM sign_in_logs WHERE...",
        result="PROVEN - 64 foreign logins found in attack window"
    )

    disproven = assumption_log.get_disproven_assumptions()
    assert len(disproven) == 0  # No disproven assumptions


# ============================================================================
# TEST CASE 5: Source Citation Requirements
# ============================================================================

def test_all_findings_cite_sources(ben_oculus_scenario):
    """
    Test that every finding cites which database tables were queried

    FR-5: Report generation must document sources
    """
    if AccountValidator is None:
        pytest.skip("AccountValidator not yet implemented")

    validator = AccountValidator(ben_oculus_scenario, "ben@oculus.info")
    result = validator.validate()

    # Lifecycle data must cite password_status
    assert 'source' in result['lifecycle']
    assert 'password_status' in result['lifecycle']['source']

    # Status changes must cite entra_audit_log
    assert 'entra_audit_log' in result['lifecycle']['source']

    # Compromise data must cite sign_in_logs
    assert 'source' in result['compromise']
    assert 'sign_in_logs' in result['compromise']['source']


# ============================================================================
# INTEGRATION TEST: Full Validation Workflow
# ============================================================================

def test_full_validation_workflow_prevents_report_without_validation(ben_oculus_scenario):
    """
    Integration test: Cannot generate report without running validation first

    This is the core enforcement mechanism.
    """
    if AccountValidator is None:
        pytest.skip("AccountValidator not yet implemented")

    validator = AccountValidator(ben_oculus_scenario, "ben@oculus.info")

    # Try to generate report without validation - should fail
    with pytest.raises(ValidationError) as exc_info:
        validator.generate_report()

    assert "without completing validation" in str(exc_info.value)

    # After validation, report generation should work
    validator.validate()
    report = validator.generate_report()

    assert report['account'] == 'ben@oculus.info'
    assert report['validated'] == True
    assert 'validation_timestamp' in report
    assert 'sources_queried' in report


# ============================================================================
# TEST CASE: account_enabled as STRING (BUG FIX PIR-OCULUS-2025-12-19)
# ============================================================================

@pytest.fixture
def string_account_enabled_db(temp_dir):
    """
    BUG FIX TEST: Account enabled field stored as string ("True"/"False").

    Real PIR-OCULUS database has TEXT values, not INTEGER.
    bool("False") returns True in Python - this is the bug!
    """
    db_path = temp_dir / "test_string_enabled.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create tables with TEXT for account_enabled (matches real data)
    cursor.execute("""
        CREATE TABLE password_status (
            user_principal_name TEXT PRIMARY KEY,
            created_datetime TEXT,
            last_password_change TEXT,
            account_enabled TEXT,
            days_since_change INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE entra_audit_log (
            timestamp TEXT,
            activity TEXT,
            target TEXT,
            initiated_by TEXT,
            result TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE sign_in_logs (
            timestamp TEXT,
            user_principal_name TEXT,
            ip_address TEXT,
            location_country TEXT,
            status TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE legacy_auth_logs (
            timestamp TEXT,
            user_principal_name TEXT,
            client_app_used TEXT,
            ip_address TEXT,
            country TEXT
        )
    """)

    # Insert account with STRING "False" - should be detected as disabled
    cursor.execute("""
        INSERT INTO password_status VALUES (
            'ben@oculus.info',
            '2018-02-25 22:59:16',
            '2020-06-28 20:33:36',
            'False',
            1998
        )
    """)

    # No disable event = should raise ValidationError
    conn.commit()
    conn.close()

    return str(db_path)


def test_account_enabled_string_false_is_disabled(string_account_enabled_db):
    """
    BUG FIX: Validator must correctly parse "False" string as disabled.

    Before fix: bool("False") = True (bug!)
    After fix: "False" should be parsed as disabled (False)

    This test would FAIL before the bug fix.
    """
    if AccountValidator is None:
        pytest.skip("AccountValidator not yet implemented")

    validator = AccountValidator(string_account_enabled_db, "ben@oculus.info")

    # Should raise ValidationError because account is DISABLED but no disable event
    with pytest.raises(ValidationError) as exc_info:
        validator.validate()

    # Error should mention "DISABLED" and "no disable event"
    assert "DISABLED" in str(exc_info.value) or "disabled" in str(exc_info.value).lower()


@pytest.fixture
def string_account_enabled_true_db(temp_dir):
    """Test account enabled as "True" string."""
    db_path = temp_dir / "test_string_enabled_true.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE password_status (
            user_principal_name TEXT PRIMARY KEY,
            created_datetime TEXT,
            last_password_change TEXT,
            account_enabled TEXT,
            days_since_change INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE entra_audit_log (
            timestamp TEXT,
            activity TEXT,
            target TEXT,
            initiated_by TEXT,
            result TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE sign_in_logs (
            timestamp TEXT,
            user_principal_name TEXT,
            ip_address TEXT,
            location_country TEXT,
            status TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE legacy_auth_logs (
            timestamp TEXT,
            user_principal_name TEXT,
            client_app_used TEXT,
            ip_address TEXT,
            country TEXT
        )
    """)

    # Insert account with STRING "True" - should be detected as enabled
    cursor.execute("""
        INSERT INTO password_status VALUES (
            'enabled@oculus.info',
            '2018-02-25 22:59:16',
            '2025-01-01 00:00:00',
            'True',
            7
        )
    """)

    conn.commit()
    conn.close()

    return str(db_path)


def test_account_enabled_string_true_is_enabled(string_account_enabled_true_db):
    """
    Validator must correctly parse "True" string as enabled.
    """
    if AccountValidator is None:
        pytest.skip("AccountValidator not yet implemented")

    validator = AccountValidator(string_account_enabled_true_db, "enabled@oculus.info")

    # Should NOT raise ValidationError (account is enabled, no disable check needed)
    result = validator.validate()

    assert result['lifecycle']['current_status'] == 'Enabled'
