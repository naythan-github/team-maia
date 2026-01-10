"""
Tests for M365 IR Phase 0 Auto-Checks
Sprint 1: Critical Bug Fixes (A1-A4)
"""

import pytest
import sqlite3
import os
import sys
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tests.fixtures.test_db_helpers import (
    create_test_db,
    create_test_db_with_password_distribution,
    create_test_db_with_sign_ins,
    create_empty_test_db,
    create_test_db_without_role_data,
    add_mfa_status,
    add_passwords,
    add_accounts,
    add_role_assignments,
    add_audit_logs,
    add_unified_audit_logs,
    add_sign_ins,
    add_sign_ins_with_coords,
    add_mfa_events,
    cleanup_test_db,
)


# ============================================================================
# A1: SQL INJECTION PREVENTION TESTS
# ============================================================================

def test_foreign_baseline_sql_injection_prevention():
    """Ensure SQL injection via home_country is prevented"""
    from claude.tools.m365_ir.phase0_auto_checks import check_foreign_baseline

    db_path = create_test_db_with_sign_ins()

    try:
        # Attempt SQL injection via malicious country name
        malicious_country = "AU'; DROP TABLE sign_in_logs; --"

        # Should NOT execute the injection
        result = check_foreign_baseline(db_path, override_home_country=malicious_country)

        # Table should still exist
        conn = sqlite3.connect(db_path)
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        assert ('sign_in_logs',) in tables
        conn.close()

        # Result should indicate no data or safe handling
        assert result['status'] in ['NO_DATA', 'OK']

    finally:
        cleanup_test_db(db_path)


def test_foreign_baseline_uses_parameterized_queries():
    """Verify parameterized queries are used (code inspection test)"""
    import inspect
    from claude.tools.m365_ir.phase0_auto_checks import check_foreign_baseline

    source = inspect.getsource(check_foreign_baseline)

    # Should NOT contain f-string SQL patterns with direct string interpolation
    dangerous_pattern_1 = "f\"\"\"" in source and "location_country = '" in source
    dangerous_pattern_2 = "f\"" in source and "location_country = '{" in source

    assert not dangerous_pattern_1, "Found f-string with single quote in SQL (SQL injection risk)"
    assert not dangerous_pattern_2, "Found f-string with brace interpolation in SQL (SQL injection risk)"

    # Should contain parameterized pattern
    has_param_pattern = "location_country = ?" in source or "location_country = :country" in source
    assert has_param_pattern, "Missing parameterized query pattern (? or :param)"


# ============================================================================
# A2: CONNECTION MANAGEMENT TESTS
# ============================================================================

def test_connection_always_closed_on_success():
    """Verify connection is closed after successful query"""
    from claude.tools.m365_ir.phase0_auto_checks import analyze_password_hygiene

    db_path = create_test_db_with_password_distribution(total=100, over_1_year=50)

    try:
        # Run analysis
        result = analyze_password_hygiene(db_path)

        assert result is not None

        # Connection should be closed - verify by checking if we can delete the file
        # (Some OS lock files with open connections)
        try:
            test_path = db_path + '.test'
            os.rename(db_path, test_path)
            os.rename(test_path, db_path)
            connection_closed = True
        except (PermissionError, OSError):
            connection_closed = False

        assert connection_closed, "Connection not properly closed - file is locked"

    finally:
        cleanup_test_db(db_path)


def test_connection_closed_on_exception():
    """Verify connection is closed even when exception occurs"""
    from claude.tools.m365_ir.phase0_auto_checks import analyze_password_hygiene

    db_path = "/nonexistent/directory/test.db"

    # Should raise exception for nonexistent path
    with pytest.raises(Exception):
        analyze_password_hygiene(db_path)

    # Should not leave any dangling connections
    # (Implementation uses try/finally or context manager)
    # This test primarily validates that the function doesn't hang


# ============================================================================
# A3: THRESHOLD BOUNDARY TESTS
# ============================================================================

def test_password_threshold_70_percent_is_critical():
    """70.0% should be CRITICAL, not HIGH (boundary test)"""
    from claude.tools.m365_ir.phase0_auto_checks import analyze_password_hygiene

    db_path = create_test_db_with_password_distribution(
        total=100,
        over_1_year=70  # Exactly 70%
    )

    try:
        result = analyze_password_hygiene(db_path)

        assert result['pct_over_1_year'] == 70.0
        assert result['risk'] == 'CRITICAL', f"Expected CRITICAL but got {result['risk']}"

    finally:
        cleanup_test_db(db_path)


def test_password_threshold_50_percent_is_high():
    """50.0% should be HIGH, not MEDIUM"""
    from claude.tools.m365_ir.phase0_auto_checks import analyze_password_hygiene

    db_path = create_test_db_with_password_distribution(total=100, over_1_year=50)

    try:
        result = analyze_password_hygiene(db_path)

        assert result['pct_over_1_year'] == 50.0
        assert result['risk'] == 'HIGH', f"Expected HIGH but got {result['risk']}"

    finally:
        cleanup_test_db(db_path)


def test_password_threshold_30_percent_is_medium():
    """30.0% should be MEDIUM, not OK"""
    from claude.tools.m365_ir.phase0_auto_checks import analyze_password_hygiene

    db_path = create_test_db_with_password_distribution(total=100, over_1_year=30)

    try:
        result = analyze_password_hygiene(db_path)

        assert result['pct_over_1_year'] == 30.0
        assert result['risk'] == 'MEDIUM', f"Expected MEDIUM but got {result['risk']}"

    finally:
        cleanup_test_db(db_path)


def test_password_threshold_29_percent_is_ok():
    """29.9% should be OK"""
    from claude.tools.m365_ir.phase0_auto_checks import analyze_password_hygiene

    db_path = create_test_db_with_password_distribution(total=1000, over_1_year=299)

    try:
        result = analyze_password_hygiene(db_path)

        assert result['pct_over_1_year'] == 29.9
        assert result['risk'] == 'OK', f"Expected OK but got {result['risk']}"

    finally:
        cleanup_test_db(db_path)


# ============================================================================
# A4: NULL HANDLING TESTS
# ============================================================================

def test_null_password_dates_handled():
    """Accounts with NULL password dates should not cause errors"""
    from claude.tools.m365_ir.phase0_auto_checks import analyze_password_hygiene

    db_path = create_test_db()
    conn = sqlite3.connect(db_path)
    conn.execute("""
        INSERT INTO password_status (user_principal_name, last_password_change)
        VALUES ('user1@test.com', '2020-01-01'),
               ('user2@test.com', NULL),
               ('user3@test.com', '2024-01-01')
    """)
    conn.commit()
    conn.close()

    try:
        result = analyze_password_hygiene(db_path)

        # Should only count non-NULL accounts
        assert result['total_accounts'] == 2, "NULL password dates should be excluded from count"
        assert 'error' not in result

    finally:
        cleanup_test_db(db_path)


def test_empty_table_returns_no_data():
    """Empty password_status table should return NO_DATA, not error"""
    from claude.tools.m365_ir.phase0_auto_checks import analyze_password_hygiene

    db_path = create_empty_test_db()

    try:
        result = analyze_password_hygiene(db_path)

        assert result['risk'] == 'NO_DATA'
        assert 'error' not in result

    finally:
        cleanup_test_db(db_path)


def test_all_null_dates_returns_no_data():
    """Table with only NULL dates should return NO_DATA"""
    from claude.tools.m365_ir.phase0_auto_checks import analyze_password_hygiene

    db_path = create_test_db()
    conn = sqlite3.connect(db_path)
    conn.execute("""
        INSERT INTO password_status (user_principal_name, last_password_change)
        VALUES ('user1@test.com', NULL),
               ('user2@test.com', NULL)
    """)
    conn.commit()
    conn.close()

    try:
        result = analyze_password_hygiene(db_path)

        assert result['risk'] == 'NO_DATA'

    finally:
        cleanup_test_db(db_path)


# ============================================================================
# ADDITIONAL VALIDATION TESTS
# ============================================================================

def test_password_hygiene_returns_expected_structure():
    """Validate the structure of returned data"""
    from claude.tools.m365_ir.phase0_auto_checks import analyze_password_hygiene

    db_path = create_test_db_with_password_distribution(total=100, over_1_year=60)

    try:
        result = analyze_password_hygiene(db_path)

        # Verify all expected keys exist
        assert 'risk' in result
        assert 'total_accounts' in result
        assert 'over_1_year' in result
        assert 'over_2_years' in result
        assert 'over_3_years' in result
        assert 'pct_over_1_year' in result

        # Verify data types
        assert isinstance(result['risk'], str)
        assert isinstance(result['total_accounts'], int)
        assert isinstance(result['pct_over_1_year'], float)

    finally:
        cleanup_test_db(db_path)


def test_foreign_baseline_returns_expected_structure():
    """Validate the structure of foreign baseline data"""
    from claude.tools.m365_ir.phase0_auto_checks import check_foreign_baseline

    db_path = create_test_db_with_sign_ins()

    try:
        result = check_foreign_baseline(db_path)

        assert 'status' in result
        assert result['status'] in ['OK', 'NO_DATA']

        if result['status'] == 'OK':
            assert 'home_country' in result
            assert 'accounts' in result

    finally:
        cleanup_test_db(db_path)


###############################################################################
# Sprint 2: B1 - MFA Context Check
###############################################################################

def test_mfa_context_checked_before_password_analysis():
    """Password crisis severity depends on MFA enforcement (B1)"""
    from claude.tools.m365_ir.phase0_auto_checks import analyze_password_hygiene_with_context

    db_path = create_test_db_with_password_distribution(total=100, over_1_year=80)

    try:
        # Scenario 1: Low MFA = password crisis is PRIMARY
        add_mfa_status(db_path, mfa_enforced_pct=20)
        result = analyze_password_hygiene_with_context(db_path)
        assert result['risk'] == 'CRITICAL'
        assert result['context'] == 'PRIMARY_VULNERABILITY'
        assert result['mfa_rate'] == 20.0

        # Scenario 2: High MFA = password crisis is SECONDARY
        add_mfa_status(db_path, mfa_enforced_pct=95)
        result = analyze_password_hygiene_with_context(db_path)
        assert result['risk'] == 'CRITICAL'  # Still critical
        assert result['context'] == 'SECONDARY_VULNERABILITY'  # But less urgent
        assert result['mfa_rate'] == 95.0

    finally:
        cleanup_test_db(db_path)


def test_mfa_below_50_percent_makes_password_primary():
    """MFA < 50% means password is PRIMARY vulnerability (B1)"""
    from claude.tools.m365_ir.phase0_auto_checks import analyze_password_hygiene_with_context

    db_path = create_test_db_with_password_distribution(total=100, over_1_year=80)

    try:
        # Test boundary: 49% should be PRIMARY
        add_mfa_status(db_path, mfa_enforced_pct=49)
        result = analyze_password_hygiene_with_context(db_path)
        assert result['context'] == 'PRIMARY_VULNERABILITY'
        assert result['mfa_rate'] == 49.0

        # Test boundary: 25% should be PRIMARY
        add_mfa_status(db_path, mfa_enforced_pct=25)
        result = analyze_password_hygiene_with_context(db_path)
        assert result['context'] == 'PRIMARY_VULNERABILITY'

    finally:
        cleanup_test_db(db_path)


def test_mfa_above_90_percent_makes_password_secondary():
    """MFA >= 90% means password is SECONDARY vulnerability (B1)"""
    from claude.tools.m365_ir.phase0_auto_checks import analyze_password_hygiene_with_context

    db_path = create_test_db_with_password_distribution(total=100, over_1_year=80)

    try:
        # Test boundary: 90% should be SECONDARY
        add_mfa_status(db_path, mfa_enforced_pct=90)
        result = analyze_password_hygiene_with_context(db_path)
        assert result['context'] == 'SECONDARY_VULNERABILITY'
        assert result['mfa_rate'] == 90.0

        # Test boundary: 95% should be SECONDARY
        add_mfa_status(db_path, mfa_enforced_pct=95)
        result = analyze_password_hygiene_with_context(db_path)
        assert result['context'] == 'SECONDARY_VULNERABILITY'

    finally:
        cleanup_test_db(db_path)


###############################################################################
# Sprint 2: B2 - Service Account Detection
###############################################################################

def test_service_accounts_excluded_from_dormant_detection():
    """Service accounts should not trigger dormant account alerts (B2)"""
    from claude.tools.m365_ir.phase0_auto_checks import detect_dormant_accounts

    db_path = create_test_db()

    try:
        add_accounts(db_path, [
            ('svc_backup@test.com', 'service', 90, 1000),  # Service, 90 days no login
            ('app_integration@test.com', 'service', 90, 800),  # Service, 90 days no login
            ('admin@test.com', 'admin', 90, 500),  # Should be flagged (90 days > 60 day window)
        ])

        result = detect_dormant_accounts(db_path)

        flagged_accounts = [a['upn'] for a in result['dormant_accounts']]
        assert 'svc_backup@test.com' not in flagged_accounts
        assert 'app_integration@test.com' not in flagged_accounts
        assert 'admin@test.com' in flagged_accounts

    finally:
        cleanup_test_db(db_path)


def test_service_account_patterns_detected():
    """Various service account naming patterns should be detected (B2)"""
    from claude.tools.m365_ir.phase0_auto_checks import is_service_account

    patterns = [
        'svc_backup@test.com',
        'service.account@test.com',
        'app-integration@test.com',
        'noreply@test.com',
    ]
    for account in patterns:
        assert is_service_account(account), f"Pattern {account} should be detected as service account"


###############################################################################
# Sprint 2: B3 - Break-Glass Account Whitelist
###############################################################################

def test_breakglass_accounts_excluded():
    """Break-glass accounts should not trigger dormant alerts (B3)"""
    from claude.tools.m365_ir.phase0_auto_checks import detect_dormant_accounts

    db_path = create_test_db()

    try:
        add_accounts(db_path, [
            ('breakglass@test.com', 'admin', 90, 1000),  # 90 days no login
            ('emergency.admin@test.com', 'admin', 90, 800),
            ('regular.admin@test.com', 'admin', 90, 500),
        ])

        whitelist = ['breakglass@test.com', 'emergency.admin@test.com']

        result = detect_dormant_accounts(db_path, breakglass_whitelist=whitelist)

        flagged = [a['upn'] for a in result['dormant_accounts']]
        assert 'breakglass@test.com' not in flagged
        assert 'emergency.admin@test.com' not in flagged
        assert 'regular.admin@test.com' in flagged

    finally:
        cleanup_test_db(db_path)


###############################################################################
# Sprint 2: B4 - FIDO2/Passwordless Detection
###############################################################################

def test_fido2_accounts_excluded_from_password_analysis():
    """FIDO2/passwordless accounts should not affect password hygiene score (B4)"""
    from claude.tools.m365_ir.phase0_auto_checks import analyze_password_hygiene

    db_path = create_test_db()

    try:
        # 80 accounts with old passwords
        add_passwords(db_path, [
            (f'user{i}@test.com', '2020-01-01', 'password')
            for i in range(80)
        ])

        # 20 accounts with FIDO2 (no password)
        add_passwords(db_path, [
            (f'fido{i}@test.com', '2020-01-01', 'fido2')
            for i in range(20)
        ])

        result = analyze_password_hygiene(db_path, exclude_passwordless=True)

        # Should only count password-based accounts (80), not FIDO2 (20)
        assert result['total_accounts'] == 80
        assert result['pct_over_1_year'] == 100.0  # All 80 have old passwords

    finally:
        cleanup_test_db(db_path)


###############################################################################
# Sprint 2: B5 - Role-Based Admin Detection
###############################################################################

def test_admin_detected_by_role_not_name():
    """Admin accounts detected by Entra role, not naming convention (B5)"""
    from claude.tools.m365_ir.phase0_auto_checks import get_admin_accounts

    db_path = create_test_db()

    try:
        add_role_assignments(db_path, [
            ('john.smith@test.com', 'Global Administrator'),
            ('jane.doe@test.com', 'Privileged Authentication Administrator'),
            ('regular.user@test.com', None),
        ])

        admins = get_admin_accounts(db_path)

        assert 'john.smith@test.com' in admins  # Admin by role
        assert 'jane.doe@test.com' in admins    # Admin by role
        assert 'regular.user@test.com' not in admins

    finally:
        cleanup_test_db(db_path)


def test_fallback_to_naming_convention():
    """If no role data, fallback to naming convention (B5)"""
    from claude.tools.m365_ir.phase0_auto_checks import get_admin_accounts

    db_path = create_test_db_without_role_data()

    try:
        add_accounts(db_path, [
            ('sysadmin@test.com', 'admin', 0, 500),
            ('itadmin@test.com', 'admin', 0, 500),
            ('regular@test.com', 'user', 0, 500),
        ])

        admins = get_admin_accounts(db_path, fallback_to_naming=True)

        assert 'sysadmin@test.com' in admins
        assert 'itadmin@test.com' in admins
        assert 'regular@test.com' not in admins

    finally:
        cleanup_test_db(db_path)


# ============================================================================
# SPRINT 3: FALSE NEGATIVE PREVENTION TESTS
# ============================================================================

# ============================================================================
# C1: T1562.008 - DISABLE CLOUD LOGS DETECTION
# ============================================================================

def test_detect_cloud_logging_disabled():
    """Detect when audit logging is disabled (C1 - T1562.008)"""
    from claude.tools.m365_ir.phase0_auto_checks import detect_logging_tampering

    db_path = create_test_db()

    try:
        # Scenario: Attacker disables audit logging via multiple methods
        add_audit_logs(db_path, [
            ('2024-01-15 14:23:11', 'Set-AdminAuditLogConfig', 'attacker@test.com'),
            ('2024-01-15 14:25:43', 'Update service principal', 'attacker@test.com'),
        ])

        add_unified_audit_logs(db_path, [
            ('2024-01-15 14:27:00', 'attacker@test.com', 'Set-MailboxAuditBypassAssociation'),
        ])

        result = detect_logging_tampering(db_path)

        assert result['risk_level'] == 'CRITICAL'
        assert result['mitre_technique'] == 'T1562.008'
        assert len(result['logging_changes']) >= 2  # At least 2 from entra_audit_log

        # Check that we found the specific activities
        activities = [change['activity'] for change in result['logging_changes']]
        assert 'Set-AdminAuditLogConfig' in activities or 'Set-MailboxAuditBypassAssociation' in activities

    finally:
        cleanup_test_db(db_path)


def test_logging_tampering_returns_expected_structure():
    """Verify detect_logging_tampering returns correct structure (C1)"""
    from claude.tools.m365_ir.phase0_auto_checks import detect_logging_tampering

    db_path = create_test_db()

    try:
        # No logging tampering events
        result = detect_logging_tampering(db_path)

        # Should still return valid structure
        assert 'logging_changes' in result
        assert 'risk_level' in result
        assert 'mitre_technique' in result
        assert isinstance(result['logging_changes'], list)
        assert result['mitre_technique'] == 'T1562.008'

        # With no events, risk should be OK or NONE
        assert result['risk_level'] in ['OK', 'NONE']

    finally:
        cleanup_test_db(db_path)


# ============================================================================
# C2: IMPOSSIBLE TRAVEL DETECTION
# ============================================================================

def test_impossible_travel_detected():
    """Detect geographically impossible logins (C2)"""
    from claude.tools.m365_ir.phase0_auto_checks import detect_impossible_travel

    db_path = create_test_db()

    try:
        # Scenario: User logs in from NYC, then Beijing 1.5 hours later (impossible!)
        add_sign_ins_with_coords(db_path, [
            ('user@test.com', '2024-01-15 10:00:00', 'US', '40.7128,-74.0060'),  # NYC
            ('user@test.com', '2024-01-15 11:30:00', 'CN', '39.9042,116.4074'),  # Beijing
        ])

        result = detect_impossible_travel(db_path)

        assert result['risk_level'] == 'CRITICAL'
        assert len(result['impossible_travel_events']) == 1

        event = result['impossible_travel_events'][0]
        assert event['upn'] == 'user@test.com'
        assert event['distance_km'] > 10900  # ~10,989 km NYC to Beijing (Haversine great circle distance)
        assert event['time_hours'] == 1.5
        assert event['speed_mph'] > 4000  # Way over 500 mph threshold!

    finally:
        cleanup_test_db(db_path)


def test_possible_travel_not_flagged():
    """Legitimate travel should not trigger alerts (C2)"""
    from claude.tools.m365_ir.phase0_auto_checks import detect_impossible_travel

    db_path = create_test_db()

    try:
        # Scenario: User logs in from Sydney, then Melbourne 2 hours later (possible)
        add_sign_ins_with_coords(db_path, [
            ('user@test.com', '2024-01-15 10:00:00', 'AU', '-33.8688,151.2093'),  # Sydney
            ('user@test.com', '2024-01-15 12:00:00', 'AU', '-37.8136,144.9631'),  # Melbourne (~700km, 2 hours = 350 mph possible with flight)
        ])

        result = detect_impossible_travel(db_path)

        # Should be OK or have no events (speed is under 500 mph threshold)
        assert len(result['impossible_travel_events']) == 0
        assert result['risk_level'] == 'OK'

    finally:
        cleanup_test_db(db_path)


def test_missing_coordinates_handled():
    """Handle sign-ins without coordinates gracefully (C2 - A4: NULL handling)"""
    from claude.tools.m365_ir.phase0_auto_checks import detect_impossible_travel

    db_path = create_test_db()

    try:
        # Scenario: Some sign-ins have coordinates, some don't
        add_sign_ins_with_coords(db_path, [
            ('user1@test.com', '2024-01-15 10:00:00', 'US', '40.7128,-74.0060'),  # Has coords
        ])

        # Add sign-in without coordinates (using old helper)
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.execute("""
            INSERT INTO sign_in_logs (user_principal_name, timestamp, location_country)
            VALUES (?, ?, ?)
        """, ('user1@test.com', '2024-01-15 11:00:00', 'CN'))
        conn.commit()
        conn.close()

        result = detect_impossible_travel(db_path)

        # Should not crash, should skip pairs with missing coordinates
        assert 'impossible_travel_events' in result
        assert 'risk_level' in result
        # No events expected since one login is missing coordinates
        assert len(result['impossible_travel_events']) == 0

    finally:
        cleanup_test_db(db_path)


# ============================================================================
# C3: BIDIRECTIONAL MFA BYPASS DETECTION
# ============================================================================

def test_bidirectional_mfa_bypass_detected():
    """Detect MFA enabled then disabled (C3 - bypass attempt)"""
    from claude.tools.m365_ir.phase0_auto_checks import detect_mfa_bypass

    db_path = create_test_db()

    try:
        # Scenario: Attacker enables MFA, then disables it 4.5 hours later
        add_mfa_events(db_path, [
            ('victim@test.com', '2024-01-15 10:00:00', 'Enable MFA'),
            ('victim@test.com', '2024-01-15 14:30:00', 'Disable MFA'),
        ])

        result = detect_mfa_bypass(db_path)

        assert result['risk_level'] == 'HIGH'
        assert len(result['mfa_bypass_attempts']) == 1

        attempt = result['mfa_bypass_attempts'][0]
        assert attempt['upn'] == 'victim@test.com'
        assert attempt['time_delta_hours'] == 4.5
        assert attempt['time_delta_hours'] < 24  # Within threshold

    finally:
        cleanup_test_db(db_path)


def test_mfa_enable_only_not_flagged():
    """Normal MFA enabling should not trigger bypass alert (C3)"""
    from claude.tools.m365_ir.phase0_auto_checks import detect_mfa_bypass

    db_path = create_test_db()

    try:
        # Scenario: User enables MFA and leaves it enabled (normal behavior)
        add_mfa_events(db_path, [
            ('user@test.com', '2024-01-15 10:00:00', 'Enable MFA'),
        ])

        result = detect_mfa_bypass(db_path)

        # Should be OK since no disable event
        assert len(result['mfa_bypass_attempts']) == 0
        assert result['risk_level'] == 'OK'

    finally:
        cleanup_test_db(db_path)


# =============================================================================
# END-TO-END INTEGRATION TESTS
# =============================================================================

def test_cli_integration_all_checks_clean_tenant():
    """E2E: Run all Phase 0 checks on a clean tenant (all OK)"""
    from claude.tools.m365_ir.phase0_cli import run_phase0_checks

    db_path = create_test_db()

    try:
        # Create clean tenant data (recent passwords, recent logins)
        add_passwords(db_path, [
            ('user1@test.com', '2025-12-01 10:00:00', 'enabled'),  # Recent password
            ('user2@test.com', '2025-12-02 10:00:00', 'enabled'),  # Recent password
        ])

        add_sign_ins(db_path, [
            ('user1@test.com', '2026-01-08 10:00:00', 'US', None),  # Recent login
            ('user2@test.com', '2026-01-08 11:00:00', 'US', None),  # Recent login
        ])

        # Run all checks
        results = run_phase0_checks(db_path, output_format='json')

        # Verify structure
        assert 'timestamp' in results
        assert 'database' in results
        assert 'checks' in results
        assert 'summary' in results

        # Verify all 7 checks executed
        expected_checks = ['password_hygiene', 'foreign_baseline', 'dormant_accounts',
                          'admin_accounts', 'logging_tampering', 'impossible_travel', 'mfa_bypass']
        for check_name in expected_checks:
            assert check_name in results['checks'], f"Missing check: {check_name}"
            assert 'error' not in results['checks'][check_name], f"Error in {check_name}: {results['checks'][check_name].get('error')}"

        # Verify summary for clean tenant
        summary = results['summary']
        assert summary['critical'] == 0, f"Unexpected critical issues: {summary['critical']}"
        assert summary['total_checks'] == 7

    finally:
        cleanup_test_db(db_path)


def test_cli_integration_compromised_tenant():
    """E2E: Run all checks on compromised tenant (multiple CRITICAL findings)"""
    from claude.tools.m365_ir.phase0_cli import run_phase0_checks

    db_path = create_test_db()

    try:
        # Create compromised tenant indicators

        # Critical password hygiene (70%+ old passwords, low MFA)
        add_passwords(db_path, [
            ('user1@test.com', '2020-01-01 10:00:00', 'disabled'),  # 4+ years old, no MFA
            ('user2@test.com', '2020-06-01 10:00:00', 'disabled'),  # 3+ years old, no MFA
            ('user3@test.com', '2023-01-01 10:00:00', 'disabled'),  # 1+ year old, no MFA
            ('user4@test.com', '2024-01-01 10:00:00', 'enabled'),   # Recent, MFA enabled
        ])

        # Impossible travel
        add_sign_ins_with_coords(db_path, [
            ('user1@test.com', '2024-01-15 10:00:00', 'US', '40.7128,-74.0060'),  # NYC
            ('user1@test.com', '2024-01-15 11:30:00', 'CN', '39.9042,116.4074'),  # Beijing - impossible!
        ])

        # Logging tampering (use unified audit log for Exchange operations)
        add_unified_audit_logs(db_path, [
            ('2024-01-15 14:23:11', 'attacker@test.com', 'Set-AdminAuditLogConfig'),
        ])

        # MFA bypass
        add_mfa_events(db_path, [
            ('user2@test.com', '2024-01-15 10:00:00', 'Enable MFA'),
            ('user2@test.com', '2024-01-15 10:30:00', 'Disable MFA'),  # <1 hour - CRITICAL
        ])

        # Run all checks
        results = run_phase0_checks(db_path, output_format='json')

        # Verify all checks executed
        assert len(results['checks']) == 7

        # Verify CRITICAL findings detected
        summary = results['summary']
        assert summary['critical'] >= 3, f"Expected ≥3 critical issues, got {summary['critical']}"

        # Verify specific critical findings
        assert results['checks']['password_hygiene']['risk'] in ['CRITICAL', 'HIGH']
        assert results['checks']['impossible_travel']['risk_level'] == 'CRITICAL'
        assert results['checks']['logging_tampering']['risk_level'] == 'CRITICAL'
        assert results['checks']['mfa_bypass']['risk_level'] == 'CRITICAL'

    finally:
        cleanup_test_db(db_path)


def test_cli_output_formats():
    """E2E: Verify all 3 output formats work correctly"""
    from claude.tools.m365_ir.phase0_cli import run_phase0_checks, format_json, format_table, format_summary

    db_path = create_test_db()

    try:
        add_passwords(db_path, [
            ('user1@test.com', '2025-12-01 10:00:00', 'enabled'),  # Recent password
        ])

        # Test JSON format
        results_json = run_phase0_checks(db_path, output_format='json')
        json_output = format_json(results_json)
        assert json_output.startswith('{')
        parsed = json.loads(json_output)
        assert 'checks' in parsed

        # Test table format
        results_table = run_phase0_checks(db_path, output_format='table')
        table_output = format_table(results_table)
        assert 'M365 IR Phase 0 Auto-Checks' in table_output
        assert 'Check' in table_output or 'Risk' in table_output

        # Test summary format
        results_summary = run_phase0_checks(db_path, output_format='summary')
        summary_output = format_summary(results_summary)
        assert 'M365 IR Phase 0 Auto-Checks - Summary' in summary_output
        assert 'Total checks run' in summary_output

    finally:
        cleanup_test_db(db_path)


def test_cli_graceful_degradation_missing_tables():
    """E2E: Verify graceful degradation when optional tables missing"""
    from claude.tools.m365_ir.phase0_cli import run_phase0_checks

    # Create minimal database (only required tables)
    db_path = '/tmp/test_phase0_minimal.db'
    conn = sqlite3.connect(db_path)

    try:
        # Only create required tables (no entra_audit_log, unified_audit_log, mfa_changes)
        conn.execute("""
            CREATE TABLE password_status (
                user_principal_name TEXT,
                last_password_change TEXT,
                mfa_status TEXT,
                auth_method TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE sign_in_logs (
                user_principal_name TEXT,
                timestamp TEXT,
                location_country TEXT,
                latitude REAL,
                longitude REAL,
                auth_method TEXT
            )
        """)

        conn.execute("""
            INSERT INTO password_status VALUES ('user@test.com', '2024-01-01 10:00:00', 'enabled', 'Password')
        """)

        conn.execute("""
            INSERT INTO sign_in_logs VALUES ('user@test.com', '2024-01-10 10:00:00', 'US', NULL, NULL, 'Password')
        """)

        conn.commit()
        conn.close()

        # Run checks - should not crash despite missing tables
        results = run_phase0_checks(db_path, output_format='json')

        # Verify all checks attempted
        assert len(results['checks']) == 7

        # Verify graceful handling (no errors, defaults to OK/empty)
        assert results['checks']['logging_tampering']['risk_level'] == 'OK'  # No data = OK
        assert results['checks']['mfa_bypass']['risk_level'] == 'OK'  # No table = OK
        assert 'error' not in results['checks']['password_hygiene']

    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_cli_exit_code_logic():
    """E2E: Verify exit code determination logic (not actual sys.exit)"""
    from claude.tools.m365_ir.phase0_cli import run_phase0_checks

    db_path = create_test_db()

    try:
        # Scenario 1: Clean tenant (should exit 0)
        add_passwords(db_path, [
            ('user1@test.com', '2025-12-01 10:00:00', 'enabled'),  # Recent password
        ])

        results = run_phase0_checks(db_path)
        assert results['summary']['critical'] == 0
        assert results['summary']['high'] == 0
        # Exit code would be 0

        # Scenario 2: Add CRITICAL issue (should exit 2)
        add_unified_audit_logs(db_path, [
            ('2024-01-15 14:23:11', 'attacker@test.com', 'Set-AdminAuditLogConfig'),
        ])

        results = run_phase0_checks(db_path)
        assert results['summary']['critical'] > 0
        # Exit code would be 2

    finally:
        cleanup_test_db(db_path)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
