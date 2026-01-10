#!/usr/bin/env python3
"""
TDD Test for M365 IR Password Hygiene Schema Fix (FIX-2)

Tests that password hygiene analysis uses production schema:
- MFA data is in sign_in_logs.mfa_detail (JSON), not password_status.mfa_status
- mfa_detail is TEXT containing JSON like: {"authMethod": "PhoneAppNotification", ...}

Requirements: /tmp/M365_IR_MISSING_LOG_HANDLERS_REQUIREMENTS.md v2.0
"""

import pytest
import sqlite3
import json
import tempfile
from pathlib import Path

from claude.tools.m365_ir.log_database import IRLogDatabase
from claude.tools.m365_ir.phase0_auto_checks import (
    get_mfa_enforcement_rate,
    analyze_password_hygiene_with_context
)


@pytest.fixture
def temp_dir(tmp_path):
    """Create temporary directory for test databases."""
    return tmp_path


@pytest.fixture
def production_schema_db(temp_dir):
    """
    Create database with PRODUCTION schema.

    Production schema:
    - password_status: Does NOT have mfa_status column
    - sign_in_logs: Has mfa_detail TEXT column (JSON)
    """
    db = IRLogDatabase(case_id="PIR-SCHEMA-TEST-001", base_path=str(temp_dir))
    db.create()

    conn = sqlite3.connect(db.db_path)

    # Insert password status records (no MFA columns here)
    conn.execute("""
        INSERT INTO password_status (user_principal_name, display_name, last_password_change, imported_at)
        VALUES
            ('user1@example.com', 'User 1', '2023-01-01 00:00:00', '2025-01-01 00:00:00'),
            ('user2@example.com', 'User 2', '2023-01-01 00:00:00', '2025-01-01 00:00:00'),
            ('user3@example.com', 'User 3', '2023-01-01 00:00:00', '2025-01-01 00:00:00'),
            ('user4@example.com', 'User 4', '2023-01-01 00:00:00', '2025-01-01 00:00:00')
    """)

    # Insert sign-in logs with MFA detail (production format)
    # mfa_detail is JSON containing MFA status information
    conn.execute("""
        INSERT INTO sign_in_logs
        (timestamp, user_principal_name, ip_address, location_country, mfa_detail, imported_at)
        VALUES
            ('2025-01-01 10:00:00', 'user1@example.com', '1.2.3.4', 'US',
             '{"authMethod": "PhoneAppNotification", "authDetail": "Authenticator App"}',
             '2025-01-01 00:00:00'),
            ('2025-01-01 10:05:00', 'user2@example.com', '1.2.3.5', 'US',
             '{"authMethod": "PhoneAppNotification", "authDetail": "Authenticator App"}',
             '2025-01-01 00:00:00'),
            ('2025-01-01 10:10:00', 'user3@example.com', '1.2.3.6', 'US',
             '{"authMethod": "OneWaySMS", "authDetail": "SMS"}',
             '2025-01-01 00:00:00'),
            ('2025-01-01 10:15:00', 'user4@example.com', '1.2.3.7', 'US',
             NULL,
             '2025-01-01 00:00:00')
    """)

    conn.commit()
    conn.close()

    return db.db_path


def test_mfa_enforcement_rate_production_schema(production_schema_db):
    """
    Test that get_mfa_enforcement_rate() works with production schema.

    This test will FAIL with current implementation because:
    - Current code queries password_status.mfa_status (doesn't exist)
    - Should query sign_in_logs.mfa_detail (JSON)
    """
    conn = sqlite3.connect(production_schema_db)

    # This should NOT raise "no such column: mfa_status" error
    mfa_rate = get_mfa_enforcement_rate(conn)

    conn.close()

    # Should calculate MFA rate from sign_in_logs
    # 3 out of 4 users have MFA (user4 has NULL)
    assert mfa_rate == 75.0, f"Expected 75.0% MFA rate, got {mfa_rate}"


def test_password_hygiene_with_context_production_schema(production_schema_db):
    """
    Test that analyze_password_hygiene_with_context() works with production schema.

    This is the end-to-end test for FIX-2.
    """
    # This should NOT raise "no such column: mfa_status" error
    result = analyze_password_hygiene_with_context(production_schema_db)

    # Verify structure
    assert 'mfa_rate' in result
    assert 'context' in result
    assert 'risk' in result

    # Verify MFA rate is calculated from sign_in_logs
    assert result['mfa_rate'] == 75.0

    # With 75% MFA, context should be MODERATE_RISK (50-89%)
    assert result['context'] == 'MODERATE_RISK'


def test_mfa_rate_with_no_mfa_detail(temp_dir):
    """
    Test that MFA rate handles NULL mfa_detail gracefully.
    """
    db = IRLogDatabase(case_id="PIR-SCHEMA-TEST-002", base_path=str(temp_dir))
    db.create()

    conn = sqlite3.connect(db.db_path)

    # Insert password status
    conn.execute("""
        INSERT INTO password_status (user_principal_name, last_password_change, imported_at)
        VALUES ('user1@example.com', '2023-01-01 00:00:00', '2025-01-01 00:00:00')
    """)

    # Insert sign-in log with NULL mfa_detail
    conn.execute("""
        INSERT INTO sign_in_logs
        (timestamp, user_principal_name, ip_address, mfa_detail, imported_at)
        VALUES ('2025-01-01 10:00:00', 'user1@example.com', '1.2.3.4', NULL, '2025-01-01 00:00:00')
    """)

    conn.commit()

    # Should return 0% MFA rate (1 user, 0 with MFA)
    mfa_rate = get_mfa_enforcement_rate(conn)

    conn.close()

    assert mfa_rate == 0.0, f"Expected 0.0% MFA rate for NULL mfa_detail, got {mfa_rate}"


def test_mfa_rate_with_no_sign_in_data(temp_dir):
    """
    Test that MFA rate returns None when no sign-in data exists.
    """
    db = IRLogDatabase(case_id="PIR-SCHEMA-TEST-003", base_path=str(temp_dir))
    db.create()

    conn = sqlite3.connect(db.db_path)

    # Insert password status but NO sign-in logs
    conn.execute("""
        INSERT INTO password_status (user_principal_name, last_password_change, imported_at)
        VALUES ('user1@example.com', '2023-01-01 00:00:00', '2025-01-01 00:00:00')
    """)

    conn.commit()

    # Should return None (no sign-in data)
    mfa_rate = get_mfa_enforcement_rate(conn)

    conn.close()

    assert mfa_rate is None, f"Expected None for no sign-in data, got {mfa_rate}"
