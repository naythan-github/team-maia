#!/usr/bin/env python3
"""
TDD Tests for M365 IR Compromise Validator Additional Indicators (FIX-5 & FIX-6)

Tests for two new post-compromise indicators:
- FIX-5: Pre-existing delegations (static check)
- FIX-6: Password reset bypass detection (timing pattern)

Requirements: /tmp/M365_IR_MISSING_LOG_HANDLERS_REQUIREMENTS.md v2.0
"""

import pytest
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from claude.tools.m365_ir.log_database import IRLogDatabase


@pytest.fixture
def temp_dir(tmp_path):
    """Create temporary directory for test databases."""
    return tmp_path


@pytest.fixture
def production_schema_db_with_delegations(temp_dir):
    """
    Create database with mailbox delegations (FIX-1 table).
    """
    db = IRLogDatabase(case_id="PIR-DELEGATION-TEST-001", base_path=str(temp_dir))
    db.create()

    conn = sqlite3.connect(db.db_path)

    # Insert mailbox delegations (pre-existing - no timestamp)
    conn.execute("""
        INSERT INTO mailbox_delegations
        (mailbox, delegate, permission_type, access_rights, is_inherited, imported_at)
        VALUES
            ('thegoodoil@goodsams.org.au', 'TIsbester@goodsams.org.au', 'FullAccess', 'FullAccess', 0, '2025-01-01 00:00:00'),
            ('normaluser@goodsams.org.au', 'admin@goodsams.org.au', 'SendAs', 'SendAs', 0, '2025-01-01 00:00:00')
    """)

    conn.commit()
    conn.close()

    return db.db_path


@pytest.fixture
def production_schema_db_with_password_reset(temp_dir):
    """
    Create database with password reset + sign-in pattern.
    """
    db = IRLogDatabase(case_id="PIR-RESET-TEST-001", base_path=str(temp_dir))
    db.create()

    conn = sqlite3.connect(db.db_path)

    # Password reset at 10:00
    reset_time = datetime(2025, 1, 10, 10, 0, 0)

    # Sign-in 30 minutes later (SUSPICIOUS - within 1 hour)
    signin_time_suspicious = reset_time + timedelta(minutes=30)

    # Sign-in 2 hours later (NORMAL - outside 1 hour window)
    signin_time_normal = reset_time + timedelta(hours=2)

    # Insert entra audit log with password reset
    conn.execute("""
        INSERT INTO entra_audit_log
        (timestamp, activity, initiated_by, target, result, imported_at)
        VALUES
            (?, 'Update user', 'admin@goodsams.org.au', 'cslattery@goodsams.org.au', 'success', '2025-01-01 00:00:00')
    """, (reset_time.isoformat(),))

    # Insert sign-in logs
    conn.execute("""
        INSERT INTO sign_in_logs
        (timestamp, user_principal_name, ip_address, location_country, imported_at)
        VALUES
            (?, 'cslattery@goodsams.org.au', '1.2.3.4', 'US', '2025-01-01 00:00:00'),
            (?, 'normaluser@goodsams.org.au', '5.6.7.8', 'US', '2025-01-01 00:00:00')
    """, (signin_time_suspicious.isoformat(), signin_time_normal.isoformat()))

    conn.commit()
    conn.close()

    return db.db_path


###############################################################################
# FIX-5: Pre-existing Delegations Check
###############################################################################

def test_check_pre_existing_delegations_detected(production_schema_db_with_delegations):
    """
    Test that pre-existing delegations are detected.

    This test will FAIL until FIX-5 is implemented.
    """
    from claude.tools.m365_ir.compromise_validator import check_pre_existing_delegations

    result = check_pre_existing_delegations(
        production_schema_db_with_delegations,
        'thegoodoil@goodsams.org.au'
    )

    # Should detect delegation to TIsbester
    assert result['detected'] is True, "Should detect pre-existing delegation"
    assert result['confidence'] >= 0.70, "Should have high confidence for delegation"
    assert result['count'] >= 1, "Should count at least one delegation"

    # Should include details
    assert 'delegations' in result
    assert len(result['delegations']) >= 1

    # Verify delegation details
    delegation = result['delegations'][0]
    assert delegation['delegate'] == 'TIsbester@goodsams.org.au'
    assert delegation['permission_type'] == 'FullAccess'


def test_check_pre_existing_delegations_not_detected(production_schema_db_with_delegations):
    """
    Test that accounts without delegations return no detection.
    """
    from claude.tools.m365_ir.compromise_validator import check_pre_existing_delegations

    result = check_pre_existing_delegations(
        production_schema_db_with_delegations,
        'noone@goodsams.org.au'  # No delegations for this user
    )

    # Should NOT detect delegations
    assert result['detected'] is False
    assert result['confidence'] == 0.0
    assert result['count'] == 0
    assert len(result['delegations']) == 0


def test_check_pre_existing_delegations_inherited_excluded(production_schema_db_with_delegations):
    """
    Test that inherited delegations are excluded (only manual delegations count).
    """
    from claude.tools.m365_ir.compromise_validator import check_pre_existing_delegations

    conn = sqlite3.connect(production_schema_db_with_delegations)

    # Add inherited delegation
    conn.execute("""
        INSERT INTO mailbox_delegations
        (mailbox, delegate, permission_type, access_rights, is_inherited, imported_at)
        VALUES ('inherited@goodsams.org.au', 'admin@goodsams.org.au', 'FullAccess', 'FullAccess', 1, '2025-01-01 00:00:00')
    """)
    conn.commit()
    conn.close()

    result = check_pre_existing_delegations(
        production_schema_db_with_delegations,
        'inherited@goodsams.org.au'
    )

    # Should NOT detect inherited delegation (is_inherited = 1)
    assert result['detected'] is False, "Inherited delegations should be excluded"
    assert result['count'] == 0


###############################################################################
# FIX-6: Password Reset Bypass Detection
###############################################################################

def test_check_password_reset_bypass_detected(production_schema_db_with_password_reset):
    """
    Test that password reset followed by quick login is detected.

    This test will FAIL until FIX-6 is implemented.
    """
    from claude.tools.m365_ir.compromise_validator import check_password_reset_bypass

    signin_time = datetime(2025, 1, 10, 10, 30, 0)  # 30 min after reset

    result = check_password_reset_bypass(
        production_schema_db_with_password_reset,
        'cslattery@goodsams.org.au',
        signin_time
    )

    # Should detect reset bypass pattern
    assert result['detected'] is True, "Should detect password reset bypass"
    assert result['confidence'] >= 0.85, "Should have high confidence for bypass pattern"

    # Should include timing details
    assert 'reset_time' in result
    assert 'signin_time' in result
    assert 'minutes_between' in result
    assert result['minutes_between'] <= 60, "Should be within 1 hour"


def test_check_password_reset_bypass_not_detected_long_delay(production_schema_db_with_password_reset):
    """
    Test that password reset with long delay before login is NOT flagged.
    """
    from claude.tools.m365_ir.compromise_validator import check_password_reset_bypass

    signin_time = datetime(2025, 1, 10, 12, 0, 0)  # 2 hours after reset (normal)

    result = check_password_reset_bypass(
        production_schema_db_with_password_reset,
        'normaluser@goodsams.org.au',
        signin_time
    )

    # Should NOT detect (delay > 1 hour)
    assert result['detected'] is False
    assert result['confidence'] == 0.0


def test_check_password_reset_bypass_not_detected_no_reset(temp_dir):
    """
    Test that sign-in without prior reset returns no detection.
    """
    from claude.tools.m365_ir.compromise_validator import check_password_reset_bypass

    db = IRLogDatabase(case_id="PIR-NO-RESET-001", base_path=str(temp_dir))
    db.create()

    conn = sqlite3.connect(db.db_path)

    # Only sign-in, no password reset
    conn.execute("""
        INSERT INTO sign_in_logs
        (timestamp, user_principal_name, ip_address, imported_at)
        VALUES ('2025-01-10 10:00:00', 'user@example.com', '1.2.3.4', '2025-01-01 00:00:00')
    """)
    conn.commit()
    conn.close()

    signin_time = datetime(2025, 1, 10, 10, 0, 0)

    result = check_password_reset_bypass(
        db.db_path,
        'user@example.com',
        signin_time
    )

    # Should NOT detect (no prior reset)
    assert result['detected'] is False
    assert result['confidence'] == 0.0


def test_check_password_reset_bypass_lookback_window(production_schema_db_with_password_reset):
    """
    Test that password reset bypass only looks back 24 hours.
    """
    from claude.tools.m365_ir.compromise_validator import check_password_reset_bypass

    conn = sqlite3.connect(production_schema_db_with_password_reset)

    # Add old password reset (>24 hours before sign-in)
    old_reset_time = datetime(2025, 1, 8, 10, 0, 0)  # 2 days before
    signin_time = datetime(2025, 1, 10, 10, 30, 0)

    conn.execute("""
        INSERT INTO entra_audit_log
        (timestamp, activity, initiated_by, target, result, imported_at)
        VALUES (?, 'Update user', 'admin@example.com', 'olduser@example.com', 'success', '2025-01-01 00:00:00')
    """, (old_reset_time.isoformat(),))

    conn.execute("""
        INSERT INTO sign_in_logs
        (timestamp, user_principal_name, ip_address, imported_at)
        VALUES (?, 'olduser@example.com', '1.2.3.4', '2025-01-01 00:00:00')
    """, (signin_time.isoformat(),))

    conn.commit()
    conn.close()

    result = check_password_reset_bypass(
        production_schema_db_with_password_reset,
        'olduser@example.com',
        signin_time
    )

    # Should NOT detect (reset too old - outside 24h lookback window)
    assert result['detected'] is False, "Should not detect resets older than 24 hours"
