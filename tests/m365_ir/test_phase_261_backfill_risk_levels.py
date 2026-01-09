#!/usr/bin/env python3
"""
Phase 261.2: Risk Level Backfill Migration Tests

Tests the backfill_risk_levels migration that extracts risk_level from raw_record JSON
for records where it's NULL/unknown.

Author: Maia System (SRE Principal Engineer Agent)
Created: 2026-01-09
"""

import pytest
import sqlite3
import tempfile
import json
from pathlib import Path

from claude.tools.m365_ir.log_database import IRLogDatabase
from claude.tools.m365_ir.compression import compress_json


@pytest.fixture
def test_db():
    """Create temporary test database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db = IRLogDatabase(case_id="TEST-PHASE-261-BACKFILL", base_path=tmpdir)
        db.create()
        yield db


class TestRiskLevelBackfill:
    """Test risk level backfill migration."""

    def test_backfill_finds_null_risk_levels(self, test_db):
        """Migration should find records with NULL risk_level"""
        conn = test_db.connect()

        # Insert record with NULL risk_level but raw_record contains 'high'
        raw_data = {
            "RiskLevelDuringSignIn": "high",
            "RiskState": "atRisk",
            "UserPrincipalName": "test@test.com"
        }
        compressed = compress_json(raw_data)

        conn.execute("""
            INSERT INTO sign_in_logs (
                timestamp, user_principal_name, ip_address,
                location_country, status_error_code, conditional_access_status,
                risk_level, raw_record, imported_at
            ) VALUES (
                '2025-11-25T10:00:00', 'test@test.com', '1.2.3.4',
                'AU', 0, 'notApplied', NULL, ?, datetime('now')
            )
        """, (compressed,))
        conn.commit()

        # Import and run backfill
        from claude.tools.m365_ir.migrations.backfill_risk_levels import backfill_risk_levels

        result = backfill_risk_levels(test_db.db_path)

        assert result['success'] is True
        assert result['records_checked'] == 1
        assert result['records_updated'] == 1
        assert len(result['errors']) == 0

        # Verify risk_level was updated
        updated = conn.execute("""
            SELECT risk_level FROM sign_in_logs
            WHERE user_principal_name = 'test@test.com'
        """).fetchone()

        assert updated[0] == 'high'
        conn.close()

    def test_backfill_finds_empty_string_risk_levels(self, test_db):
        """Migration should find records with empty string risk_level"""
        conn = test_db.connect()

        raw_data = {
            "RiskLevelDuringSignIn": "medium",
            "UserPrincipalName": "test2@test.com"
        }
        compressed = compress_json(raw_data)

        conn.execute("""
            INSERT INTO sign_in_logs (
                timestamp, user_principal_name, ip_address,
                location_country, status_error_code, conditional_access_status,
                risk_level, raw_record, imported_at
            ) VALUES (
                '2025-11-25T10:00:00', 'test2@test.com', '1.2.3.4',
                'AU', 0, 'notApplied', '', ?, datetime('now')
            )
        """, (compressed,))
        conn.commit()

        from claude.tools.m365_ir.migrations.backfill_risk_levels import backfill_risk_levels

        result = backfill_risk_levels(test_db.db_path)

        assert result['success'] is True
        assert result['records_updated'] == 1

        updated = conn.execute("""
            SELECT risk_level FROM sign_in_logs
            WHERE user_principal_name = 'test2@test.com'
        """).fetchone()

        assert updated[0] == 'medium'
        conn.close()

    def test_backfill_finds_unknown_risk_levels(self, test_db):
        """Migration should find records with 'unknown' risk_level"""
        conn = test_db.connect()

        raw_data = {
            "RiskLevelDuringSignIn": "low",
            "UserPrincipalName": "test3@test.com"
        }
        compressed = compress_json(raw_data)

        conn.execute("""
            INSERT INTO sign_in_logs (
                timestamp, user_principal_name, ip_address,
                location_country, status_error_code, conditional_access_status,
                risk_level, raw_record, imported_at
            ) VALUES (
                '2025-11-25T10:00:00', 'test3@test.com', '1.2.3.4',
                'AU', 0, 'notApplied', 'unknown', ?, datetime('now')
            )
        """, (compressed,))
        conn.commit()

        from claude.tools.m365_ir.migrations.backfill_risk_levels import backfill_risk_levels

        result = backfill_risk_levels(test_db.db_path)

        assert result['success'] is True
        assert result['records_updated'] == 1

        updated = conn.execute("""
            SELECT risk_level FROM sign_in_logs
            WHERE user_principal_name = 'test3@test.com'
        """).fetchone()

        assert updated[0] == 'low'
        conn.close()

    def test_backfill_skips_already_populated(self, test_db):
        """Migration should skip records that already have risk_level"""
        conn = test_db.connect()

        raw_data = {
            "RiskLevelDuringSignIn": "high",
            "UserPrincipalName": "test4@test.com"
        }
        compressed = compress_json(raw_data)

        conn.execute("""
            INSERT INTO sign_in_logs (
                timestamp, user_principal_name, ip_address,
                location_country, status_error_code, conditional_access_status,
                risk_level, raw_record, imported_at
            ) VALUES (
                '2025-11-25T10:00:00', 'test4@test.com', '1.2.3.4',
                'AU', 0, 'notApplied', 'medium', ?, datetime('now')
            )
        """, (compressed,))
        conn.commit()

        from claude.tools.m365_ir.migrations.backfill_risk_levels import backfill_risk_levels

        result = backfill_risk_levels(test_db.db_path)

        # Should check record but not update it
        assert result['success'] is True
        assert result['records_updated'] == 0

        # Verify risk_level unchanged
        updated = conn.execute("""
            SELECT risk_level FROM sign_in_logs
            WHERE user_principal_name = 'test4@test.com'
        """).fetchone()

        assert updated[0] == 'medium'  # Original value, not 'high'
        conn.close()

    def test_backfill_skips_records_without_raw_record(self, test_db):
        """Migration should skip records without raw_record"""
        conn = test_db.connect()

        conn.execute("""
            INSERT INTO sign_in_logs (
                timestamp, user_principal_name, ip_address,
                location_country, status_error_code, conditional_access_status,
                risk_level, raw_record, imported_at
            ) VALUES (
                '2025-11-25T10:00:00', 'test5@test.com', '1.2.3.4',
                'AU', 0, 'notApplied', NULL, NULL, datetime('now')
            )
        """)
        conn.commit()

        from claude.tools.m365_ir.migrations.backfill_risk_levels import backfill_risk_levels

        result = backfill_risk_levels(test_db.db_path)

        assert result['success'] is True
        assert result['records_checked'] == 0  # Not checked because no raw_record

        # Verify risk_level unchanged
        updated = conn.execute("""
            SELECT risk_level FROM sign_in_logs
            WHERE user_principal_name = 'test5@test.com'
        """).fetchone()

        assert updated[0] is None
        conn.close()

    def test_backfill_handles_multiple_records(self, test_db):
        """Migration should handle multiple records"""
        conn = test_db.connect()

        # Insert 5 records needing backfill
        for i in range(5):
            raw_data = {
                "RiskLevelDuringSignIn": "high" if i % 2 == 0 else "low",
                "UserPrincipalName": f"user{i}@test.com"
            }
            compressed = compress_json(raw_data)

            conn.execute("""
                INSERT INTO sign_in_logs (
                    timestamp, user_principal_name, ip_address,
                    location_country, status_error_code, conditional_access_status,
                    risk_level, raw_record, imported_at
                ) VALUES (
                    '2025-11-25T10:00:00', ?, '1.2.3.4',
                    'AU', 0, 'notApplied', '', ?, datetime('now')
                )
            """, (f"user{i}@test.com", compressed))

        conn.commit()

        from claude.tools.m365_ir.migrations.backfill_risk_levels import backfill_risk_levels

        result = backfill_risk_levels(test_db.db_path)

        assert result['success'] is True
        assert result['records_checked'] == 5
        assert result['records_updated'] == 5

        # Verify all records updated
        for i in range(5):
            updated = conn.execute("""
                SELECT risk_level FROM sign_in_logs
                WHERE user_principal_name = ?
            """, (f"user{i}@test.com",)).fetchone()

            expected = 'high' if i % 2 == 0 else 'low'
            assert updated[0] == expected

        conn.close()

    def test_backfill_handles_missing_risk_field_in_json(self, test_db):
        """Migration should handle raw_record without RiskLevelDuringSignIn"""
        conn = test_db.connect()

        raw_data = {
            "UserPrincipalName": "test6@test.com",
            "ConditionalAccessStatus": "notApplied"
            # No RiskLevelDuringSignIn field
        }
        compressed = compress_json(raw_data)

        conn.execute("""
            INSERT INTO sign_in_logs (
                timestamp, user_principal_name, ip_address,
                location_country, status_error_code, conditional_access_status,
                risk_level, raw_record, imported_at
            ) VALUES (
                '2025-11-25T10:00:00', 'test6@test.com', '1.2.3.4',
                'AU', 0, 'notApplied', NULL, ?, datetime('now')
            )
        """, (compressed,))
        conn.commit()

        from claude.tools.m365_ir.migrations.backfill_risk_levels import backfill_risk_levels

        result = backfill_risk_levels(test_db.db_path)

        assert result['success'] is True
        assert result['records_checked'] == 1
        assert result['records_updated'] == 0  # Nothing to update

        # Verify risk_level unchanged
        updated = conn.execute("""
            SELECT risk_level FROM sign_in_logs
            WHERE user_principal_name = 'test6@test.com'
        """).fetchone()

        assert updated[0] is None
        conn.close()

    def test_backfill_case_insensitive_comparison(self, test_db):
        """Migration should handle case variations in RiskLevelDuringSignIn"""
        conn = test_db.connect()

        test_cases = [
            ('HIGH', 'high'),
            ('Low', 'low'),
            ('Medium', 'medium'),
            ('None', 'none')
        ]

        for i, (raw_value, expected) in enumerate(test_cases):
            raw_data = {
                "RiskLevelDuringSignIn": raw_value,
                "UserPrincipalName": f"case{i}@test.com"
            }
            compressed = compress_json(raw_data)

            conn.execute("""
                INSERT INTO sign_in_logs (
                    timestamp, user_principal_name, ip_address,
                    location_country, status_error_code, conditional_access_status,
                    risk_level, raw_record, imported_at
                ) VALUES (
                    '2025-11-25T10:00:00', ?, '1.2.3.4',
                    'AU', 0, 'notApplied', '', ?, datetime('now')
                )
            """, (f"case{i}@test.com", compressed))

        conn.commit()

        from claude.tools.m365_ir.migrations.backfill_risk_levels import backfill_risk_levels

        result = backfill_risk_levels(test_db.db_path)

        assert result['success'] is True
        assert result['records_updated'] == 4

        # Verify all converted to lowercase
        for i, (raw_value, expected) in enumerate(test_cases):
            updated = conn.execute("""
                SELECT risk_level FROM sign_in_logs
                WHERE user_principal_name = ?
            """, (f"case{i}@test.com",)).fetchone()

            assert updated[0] == expected

        conn.close()

    def test_backfill_idempotent(self, test_db):
        """Migration should be idempotent (safe to run multiple times)"""
        conn = test_db.connect()

        raw_data = {
            "RiskLevelDuringSignIn": "high",
            "UserPrincipalName": "test7@test.com"
        }
        compressed = compress_json(raw_data)

        conn.execute("""
            INSERT INTO sign_in_logs (
                timestamp, user_principal_name, ip_address,
                location_country, status_error_code, conditional_access_status,
                risk_level, raw_record, imported_at
            ) VALUES (
                '2025-11-25T10:00:00', 'test7@test.com', '1.2.3.4',
                'AU', 0, 'notApplied', NULL, ?, datetime('now')
            )
        """, (compressed,))
        conn.commit()

        from claude.tools.m365_ir.migrations.backfill_risk_levels import backfill_risk_levels

        # Run migration first time
        result1 = backfill_risk_levels(test_db.db_path)
        assert result1['records_updated'] == 1

        # Run migration second time
        result2 = backfill_risk_levels(test_db.db_path)
        assert result2['records_updated'] == 0  # Already updated

        # Verify risk_level correct
        updated = conn.execute("""
            SELECT risk_level FROM sign_in_logs
            WHERE user_principal_name = 'test7@test.com'
        """).fetchone()

        assert updated[0] == 'high'
        conn.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
