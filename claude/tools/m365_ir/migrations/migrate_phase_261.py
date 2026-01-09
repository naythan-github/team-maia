#!/usr/bin/env python3
"""
Phase 261 Database Migration

Migrates existing PIR-SGS-4241809 database to Phase 261 view definition.

This script:
1. Creates backup of old v_sign_in_auth_status view
2. Recreates view with LIKELY_SUCCESS_RISKY classification
3. Adds investigation_priority column

Usage:
    python3 migrate_phase_261.py /path/to/case_logs.db

Author: Maia System (SRE Principal Engineer Agent)
Created: 2026-01-09
"""

import sqlite3
import sys
from pathlib import Path


def migrate_database(db_path: str) -> dict:
    """
    Migrate database to Phase 261 view definition.

    Args:
        db_path: Path to database file

    Returns:
        Dict with migration results
    """
    result = {
        'success': False,
        'backup_created': False,
        'view_updated': False,
        'error': None
    }

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print(f"Migrating database: {db_path}")

        # Step 1: Create backup view
        print("Creating backup view v_sign_in_auth_status_v4_backup...")
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS v_sign_in_auth_status_v4_backup AS
            SELECT
                *,
                CASE
                    WHEN conditional_access_status = 'success' THEN 'CONFIRMED_SUCCESS'
                    WHEN conditional_access_status = 'failure' THEN 'CA_BLOCKED'
                    WHEN conditional_access_status = 'notApplied'
                         AND (status_error_code IS NULL OR status_error_code = 0)
                    THEN 'LIKELY_SUCCESS_NO_CA'
                    WHEN status_error_code IS NOT NULL AND status_error_code != 0
                    THEN 'AUTH_FAILED'
                    ELSE 'INDETERMINATE'
                END as auth_determination,
                CASE
                    WHEN conditional_access_status = 'success' THEN 100
                    WHEN conditional_access_status = 'failure' THEN 100
                    WHEN conditional_access_status = 'notApplied'
                         AND (status_error_code IS NULL OR status_error_code = 0) THEN 60
                    WHEN status_error_code IS NOT NULL AND status_error_code != 0 THEN 90
                    ELSE 0
                END as auth_confidence_pct
            FROM sign_in_logs
        """)
        result['backup_created'] = True
        print("✓ Backup view created")

        # Step 2: Drop and recreate main view
        print("Dropping old v_sign_in_auth_status view...")
        cursor.execute("DROP VIEW IF EXISTS v_sign_in_auth_status")

        print("Creating new v_sign_in_auth_status view with Phase 261 logic...")
        cursor.execute("""
            CREATE VIEW v_sign_in_auth_status AS
            SELECT
                id,
                timestamp,
                user_principal_name,
                user_display_name,
                ip_address,
                location_city,
                location_country,
                location_coordinates,
                client_app,
                app_display_name,
                device_detail,
                browser,
                os,
                status_error_code,
                status_failure_reason,
                conditional_access_status,
                mfa_detail,
                risk_level,
                risk_state,
                risk_detail,
                resource_display_name,
                correlation_id,
                raw_record,
                imported_at,

                -- Enhanced authentication determination
                CASE
                    -- CONFIRMED SUCCESS: CA explicitly passed
                    WHEN LOWER(TRIM(conditional_access_status)) IN ('success')
                         AND (status_error_code IS NULL OR status_error_code = 0)
                    THEN 'CONFIRMED_SUCCESS'

                    -- CA BLOCKED: CA explicitly failed
                    WHEN LOWER(TRIM(conditional_access_status)) IN ('failure')
                    THEN 'CA_BLOCKED'

                    -- AUTH FAILED: Known Microsoft failure error codes
                    WHEN status_error_code IN (
                        50126,  -- Invalid username or password
                        50140,  -- Keep me signed in interrupt
                        50074,  -- Strong auth required
                        50076,  -- MFA required
                        50079,  -- User needs to register for MFA
                        50055,  -- Password expired
                        50057,  -- User disabled
                        50053,  -- Account locked
                        50034,  -- User not found
                        53003,  -- Blocked by CA
                        530032, -- Blocked by security defaults
                        7000218 -- Client app not allowed
                    )
                    THEN 'AUTH_FAILED'

                    -- NEW: LIKELY_SUCCESS_RISKY - High/medium risk but NOT blocked
                    WHEN LOWER(TRIM(COALESCE(risk_level, ''))) IN ('high', 'medium')
                         AND (status_error_code IS NULL OR status_error_code IN (0, 1))
                         AND LOWER(TRIM(COALESCE(conditional_access_status, ''))) IN ('notapplied', 'not applied', 'not_applied', '')
                    THEN 'LIKELY_SUCCESS_RISKY'

                    -- AUTH_INTERRUPTED: Error code 1 is PowerShell internal flag
                    WHEN status_error_code = 1
                         AND LOWER(TRIM(COALESCE(conditional_access_status, ''))) IN ('notapplied', 'not applied', 'not_applied', '')
                         AND LOWER(TRIM(COALESCE(risk_level, ''))) NOT IN ('high', 'medium')
                    THEN 'AUTH_INTERRUPTED'

                    -- LIKELY SUCCESS: No CA, no error, low/no risk
                    WHEN (status_error_code IS NULL OR status_error_code = 0)
                         AND LOWER(TRIM(COALESCE(conditional_access_status, ''))) IN ('notapplied', 'not applied', 'not_applied', '')
                         AND LOWER(TRIM(COALESCE(risk_level, ''))) IN ('none', 'low', 'hidden', 'unknown', '')
                    THEN 'LIKELY_SUCCESS_NO_CA'

                    -- Cannot determine
                    ELSE 'INDETERMINATE'
                END AS auth_determination,

                -- Confidence percentages
                CASE
                    WHEN LOWER(TRIM(conditional_access_status)) IN ('success')
                         AND (status_error_code IS NULL OR status_error_code = 0)
                    THEN 100

                    WHEN LOWER(TRIM(conditional_access_status)) IN ('failure')
                    THEN 100

                    WHEN status_error_code IN (50126, 50140, 50074, 50076, 50079, 50055, 50057, 50053, 50034, 53003, 530032, 7000218)
                    THEN 95

                    WHEN LOWER(TRIM(COALESCE(risk_level, ''))) IN ('high', 'medium')
                         AND (status_error_code IS NULL OR status_error_code IN (0, 1))
                         AND LOWER(TRIM(COALESCE(conditional_access_status, ''))) IN ('notapplied', 'not applied', 'not_applied', '')
                    THEN 70

                    WHEN status_error_code = 1
                         AND LOWER(TRIM(COALESCE(conditional_access_status, ''))) IN ('notapplied', 'not applied', 'not_applied', '')
                    THEN 50

                    WHEN (status_error_code IS NULL OR status_error_code = 0)
                         AND LOWER(TRIM(COALESCE(conditional_access_status, ''))) IN ('notapplied', 'not applied', 'not_applied', '')
                    THEN 60

                    ELSE 0
                END AS auth_confidence_pct,

                -- Investigation priority
                CASE
                    WHEN LOWER(TRIM(COALESCE(risk_level, ''))) IN ('high', 'medium')
                         AND LOWER(TRIM(COALESCE(conditional_access_status, ''))) IN ('notapplied', 'not applied', 'not_applied', '')
                    THEN 'P1_IMMEDIATE'

                    WHEN LOWER(TRIM(conditional_access_status)) IN ('success')
                         AND location_country NOT IN ('AU', 'Australia')
                    THEN 'P2_REVIEW'

                    ELSE 'P4_NORMAL'
                END AS investigation_priority

            FROM sign_in_logs
        """)
        result['view_updated'] = True
        print("✓ New view created")

        conn.commit()
        conn.close()

        result['success'] = True
        print("\n✅ Migration completed successfully")

    except Exception as e:
        result['error'] = str(e)
        print(f"\n❌ Migration failed: {e}")

    return result


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 migrate_phase_261.py /path/to/case_logs.db")
        sys.exit(1)

    db_path = sys.argv[1]

    if not Path(db_path).exists():
        print(f"Error: Database not found: {db_path}")
        sys.exit(1)

    result = migrate_database(db_path)

    if not result['success']:
        sys.exit(1)
