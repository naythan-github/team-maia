#!/usr/bin/env python3
"""
Phase 261.1: Auth Determination View Tests

Tests the revised v_sign_in_auth_status view with LIKELY_SUCCESS_RISKY classification.

Critical: edelaney Turkey login MUST classify as LIKELY_SUCCESS_RISKY, NOT AUTH_FAILED.

Author: Maia System (SRE Principal Engineer Agent)
Created: 2026-01-09
"""

import pytest
import sqlite3
import tempfile
from pathlib import Path
from datetime import datetime

from claude.tools.m365_ir.log_database import IRLogDatabase


@pytest.fixture
def test_db():
    """Create temporary test database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db = IRLogDatabase(case_id="TEST-PHASE-261", base_path=tmpdir)
        db.create()
        yield db


class TestAuthDeterminationView:
    """Test v_sign_in_auth_status view classifications."""

    def test_confirmed_success_ca_passed(self, test_db):
        """CA=success + error=0 -> CONFIRMED_SUCCESS (100%)"""
        conn = test_db.connect()

        conn.execute("""
            INSERT INTO sign_in_logs (
                timestamp, user_principal_name, ip_address,
                location_country, status_error_code, conditional_access_status,
                risk_level, imported_at
            ) VALUES (
                '2025-11-25T10:00:00', 'user@test.com', '1.2.3.4',
                'AU', 0, 'success', 'none', datetime('now')
            )
        """)
        conn.commit()

        result = conn.execute("""
            SELECT auth_determination, auth_confidence_pct
            FROM v_sign_in_auth_status
            WHERE user_principal_name = 'user@test.com'
        """).fetchone()

        assert result[0] == 'CONFIRMED_SUCCESS'
        assert result[1] == 100
        conn.close()

    def test_ca_blocked(self, test_db):
        """CA=failure -> CA_BLOCKED (100%)"""
        conn = test_db.connect()

        conn.execute("""
            INSERT INTO sign_in_logs (
                timestamp, user_principal_name, ip_address,
                location_country, status_error_code, conditional_access_status,
                risk_level, imported_at
            ) VALUES (
                '2025-11-25T10:00:00', 'user@test.com', '1.2.3.4',
                'AU', NULL, 'failure', 'low', datetime('now')
            )
        """)
        conn.commit()

        result = conn.execute("""
            SELECT auth_determination, auth_confidence_pct
            FROM v_sign_in_auth_status
            WHERE user_principal_name = 'user@test.com'
        """).fetchone()

        assert result[0] == 'CA_BLOCKED'
        assert result[1] == 100
        conn.close()

    def test_auth_failed_error_codes(self, test_db):
        """Known error codes -> AUTH_FAILED (95%)"""
        conn = test_db.connect()

        # Test multiple known error codes
        error_codes = [50126, 50140, 50074, 50076, 50053]

        for error_code in error_codes:
            conn.execute("""
                INSERT INTO sign_in_logs (
                    timestamp, user_principal_name, ip_address,
                    location_country, status_error_code, conditional_access_status,
                    risk_level, imported_at
                ) VALUES (
                    '2025-11-25T10:00:00', ?, '1.2.3.4',
                    'AU', ?, 'notApplied', 'none', datetime('now')
                )
            """, (f'user{error_code}@test.com', error_code))

        conn.commit()

        for error_code in error_codes:
            result = conn.execute("""
                SELECT auth_determination, auth_confidence_pct
                FROM v_sign_in_auth_status
                WHERE user_principal_name = ?
            """, (f'user{error_code}@test.com',)).fetchone()

            assert result[0] == 'AUTH_FAILED', f"Error code {error_code} should be AUTH_FAILED"
            assert result[1] == 95, f"Error code {error_code} should have 95% confidence"

        conn.close()

    def test_edelaney_turkey_login_classification(self, test_db):
        """
        THE CRITICAL TEST: edelaney Turkey login classification.

        This is the canonical test case from PIR-SGS-4241809.

        Expected: LIKELY_SUCCESS_RISKY (70%), NOT AUTH_FAILED
        """
        conn = test_db.connect()

        # Insert the EXACT edelaney record
        conn.execute("""
            INSERT INTO sign_in_logs (
                timestamp, user_principal_name, ip_address,
                location_country, status_error_code, conditional_access_status,
                risk_level, imported_at
            ) VALUES (
                '2025-11-25T04:55:50', 'edelaney@goodsams.org.au', '46.252.102.34',
                'TR', 1, 'notApplied', 'high', datetime('now')
            )
        """)
        conn.commit()

        result = conn.execute("""
            SELECT auth_determination, auth_confidence_pct, investigation_priority
            FROM v_sign_in_auth_status
            WHERE user_principal_name = 'edelaney@goodsams.org.au'
        """).fetchone()

        # CRITICAL ASSERTIONS
        assert result[0] == 'LIKELY_SUCCESS_RISKY', \
            f"edelaney MUST be LIKELY_SUCCESS_RISKY, got {result[0]}"
        assert result[1] == 70, \
            f"edelaney confidence MUST be 70%, got {result[1]}"
        assert result[2] == 'P1_IMMEDIATE', \
            f"edelaney priority MUST be P1_IMMEDIATE, got {result[2]}"

        conn.close()

    def test_likely_success_risky_high_risk(self, test_db):
        """HIGH risk + notApplied + error=0 -> LIKELY_SUCCESS_RISKY (70%)"""
        conn = test_db.connect()

        conn.execute("""
            INSERT INTO sign_in_logs (
                timestamp, user_principal_name, ip_address,
                location_country, status_error_code, conditional_access_status,
                risk_level, imported_at
            ) VALUES (
                '2025-11-25T10:00:00', 'risky@test.com', '1.2.3.4',
                'CN', 0, 'notApplied', 'high', datetime('now')
            )
        """)
        conn.commit()

        result = conn.execute("""
            SELECT auth_determination, auth_confidence_pct, investigation_priority
            FROM v_sign_in_auth_status
            WHERE user_principal_name = 'risky@test.com'
        """).fetchone()

        assert result[0] == 'LIKELY_SUCCESS_RISKY'
        assert result[1] == 70
        assert result[2] == 'P1_IMMEDIATE'
        conn.close()

    def test_likely_success_risky_medium_risk(self, test_db):
        """MEDIUM risk + notApplied + error=1 -> LIKELY_SUCCESS_RISKY (70%)"""
        conn = test_db.connect()

        conn.execute("""
            INSERT INTO sign_in_logs (
                timestamp, user_principal_name, ip_address,
                location_country, status_error_code, conditional_access_status,
                risk_level, imported_at
            ) VALUES (
                '2025-11-25T10:00:00', 'mediumrisk@test.com', '1.2.3.4',
                'RU', 1, 'notApplied', 'medium', datetime('now')
            )
        """)
        conn.commit()

        result = conn.execute("""
            SELECT auth_determination, auth_confidence_pct, investigation_priority
            FROM v_sign_in_auth_status
            WHERE user_principal_name = 'mediumrisk@test.com'
        """).fetchone()

        assert result[0] == 'LIKELY_SUCCESS_RISKY'
        assert result[1] == 70
        assert result[2] == 'P1_IMMEDIATE'
        conn.close()

    def test_auth_interrupted_error_code_1(self, test_db):
        """error=1 + notApplied + low risk -> AUTH_INTERRUPTED (50%)"""
        conn = test_db.connect()

        conn.execute("""
            INSERT INTO sign_in_logs (
                timestamp, user_principal_name, ip_address,
                location_country, status_error_code, conditional_access_status,
                risk_level, imported_at
            ) VALUES (
                '2025-11-25T10:00:00', 'interrupted@test.com', '1.2.3.4',
                'AU', 1, 'notApplied', 'low', datetime('now')
            )
        """)
        conn.commit()

        result = conn.execute("""
            SELECT auth_determination, auth_confidence_pct
            FROM v_sign_in_auth_status
            WHERE user_principal_name = 'interrupted@test.com'
        """).fetchone()

        assert result[0] == 'AUTH_INTERRUPTED'
        assert result[1] == 50
        conn.close()

    def test_likely_success_no_ca(self, test_db):
        """error=0 + notApplied + no/low risk -> LIKELY_SUCCESS_NO_CA (60%)"""
        conn = test_db.connect()

        conn.execute("""
            INSERT INTO sign_in_logs (
                timestamp, user_principal_name, ip_address,
                location_country, status_error_code, conditional_access_status,
                risk_level, imported_at
            ) VALUES (
                '2025-11-25T10:00:00', 'nocarisk@test.com', '1.2.3.4',
                'AU', 0, 'notApplied', 'none', datetime('now')
            )
        """)
        conn.commit()

        result = conn.execute("""
            SELECT auth_determination, auth_confidence_pct
            FROM v_sign_in_auth_status
            WHERE user_principal_name = 'nocarisk@test.com'
        """).fetchone()

        assert result[0] == 'LIKELY_SUCCESS_NO_CA'
        assert result[1] == 60
        conn.close()

    def test_case_insensitive_ca_status(self, test_db):
        """CA status matching should be case-insensitive"""
        conn = test_db.connect()

        # Test various casings
        test_cases = [
            ('SUCCESS', 'CONFIRMED_SUCCESS', 100),
            ('Success', 'CONFIRMED_SUCCESS', 100),
            ('success', 'CONFIRMED_SUCCESS', 100),
            ('notApplied', 'LIKELY_SUCCESS_NO_CA', 60),
            ('NotApplied', 'LIKELY_SUCCESS_NO_CA', 60),
            ('NOTAPPLIED', 'LIKELY_SUCCESS_NO_CA', 60),
        ]

        for i, (ca_status, expected_determination, expected_confidence) in enumerate(test_cases):
            conn.execute("""
                INSERT INTO sign_in_logs (
                    timestamp, user_principal_name, ip_address,
                    location_country, status_error_code, conditional_access_status,
                    risk_level, imported_at
                ) VALUES (
                    '2025-11-25T10:00:00', ?, '1.2.3.4',
                    'AU', 0, ?, 'none', datetime('now')
                )
            """, (f'user{i}@test.com', ca_status))

        conn.commit()

        for i, (ca_status, expected_determination, expected_confidence) in enumerate(test_cases):
            result = conn.execute("""
                SELECT auth_determination, auth_confidence_pct
                FROM v_sign_in_auth_status
                WHERE user_principal_name = ?
            """, (f'user{i}@test.com',)).fetchone()

            assert result[0] == expected_determination, \
                f"CA status '{ca_status}' failed: expected {expected_determination}, got {result[0]}"
            assert result[1] == expected_confidence, \
                f"CA status '{ca_status}' confidence failed: expected {expected_confidence}, got {result[1]}"

        conn.close()

    def test_case_insensitive_risk_level(self, test_db):
        """Risk level matching should be case-insensitive"""
        conn = test_db.connect()

        # Test various casings of HIGH risk
        test_cases = ['HIGH', 'High', 'high', 'HiGh']

        for i, risk_level in enumerate(test_cases):
            conn.execute("""
                INSERT INTO sign_in_logs (
                    timestamp, user_principal_name, ip_address,
                    location_country, status_error_code, conditional_access_status,
                    risk_level, imported_at
                ) VALUES (
                    '2025-11-25T10:00:00', ?, '1.2.3.4',
                    'TR', 0, 'notApplied', ?, datetime('now')
                )
            """, (f'user{i}@test.com', risk_level))

        conn.commit()

        for i, risk_level in enumerate(test_cases):
            result = conn.execute("""
                SELECT auth_determination, auth_confidence_pct
                FROM v_sign_in_auth_status
                WHERE user_principal_name = ?
            """, (f'user{i}@test.com',)).fetchone()

            assert result[0] == 'LIKELY_SUCCESS_RISKY', \
                f"Risk level '{risk_level}' failed: expected LIKELY_SUCCESS_RISKY, got {result[0]}"
            assert result[1] == 70, \
                f"Risk level '{risk_level}' confidence failed: expected 70, got {result[1]}"

        conn.close()

    def test_whitespace_trimming(self, test_db):
        """Fields should be trimmed before comparison"""
        conn = test_db.connect()

        conn.execute("""
            INSERT INTO sign_in_logs (
                timestamp, user_principal_name, ip_address,
                location_country, status_error_code, conditional_access_status,
                risk_level, imported_at
            ) VALUES (
                '2025-11-25T10:00:00', 'whitespace@test.com', '1.2.3.4',
                'TR', 0, '  notApplied  ', '  high  ', datetime('now')
            )
        """)
        conn.commit()

        result = conn.execute("""
            SELECT auth_determination, auth_confidence_pct
            FROM v_sign_in_auth_status
            WHERE user_principal_name = 'whitespace@test.com'
        """).fetchone()

        assert result[0] == 'LIKELY_SUCCESS_RISKY'
        assert result[1] == 70
        conn.close()

    def test_investigation_priority_p1_immediate(self, test_db):
        """High/medium risk + notApplied -> P1_IMMEDIATE"""
        conn = test_db.connect()

        conn.execute("""
            INSERT INTO sign_in_logs (
                timestamp, user_principal_name, ip_address,
                location_country, status_error_code, conditional_access_status,
                risk_level, imported_at
            ) VALUES (
                '2025-11-25T10:00:00', 'p1@test.com', '1.2.3.4',
                'CN', 0, 'notApplied', 'high', datetime('now')
            )
        """)
        conn.commit()

        result = conn.execute("""
            SELECT investigation_priority
            FROM v_sign_in_auth_status
            WHERE user_principal_name = 'p1@test.com'
        """).fetchone()

        assert result[0] == 'P1_IMMEDIATE'
        conn.close()

    def test_investigation_priority_p2_review(self, test_db):
        """CA=success + foreign country -> P2_REVIEW"""
        conn = test_db.connect()

        conn.execute("""
            INSERT INTO sign_in_logs (
                timestamp, user_principal_name, ip_address,
                location_country, status_error_code, conditional_access_status,
                risk_level, imported_at
            ) VALUES (
                '2025-11-25T10:00:00', 'p2@test.com', '1.2.3.4',
                'US', 0, 'success', 'none', datetime('now')
            )
        """)
        conn.commit()

        result = conn.execute("""
            SELECT investigation_priority
            FROM v_sign_in_auth_status
            WHERE user_principal_name = 'p2@test.com'
        """).fetchone()

        assert result[0] == 'P2_REVIEW'
        conn.close()

    def test_investigation_priority_p4_normal(self, test_db):
        """Domestic + low risk -> P4_NORMAL"""
        conn = test_db.connect()

        conn.execute("""
            INSERT INTO sign_in_logs (
                timestamp, user_principal_name, ip_address,
                location_country, status_error_code, conditional_access_status,
                risk_level, imported_at
            ) VALUES (
                '2025-11-25T10:00:00', 'p4@test.com', '1.2.3.4',
                'AU', 0, 'notApplied', 'none', datetime('now')
            )
        """)
        conn.commit()

        result = conn.execute("""
            SELECT investigation_priority
            FROM v_sign_in_auth_status
            WHERE user_principal_name = 'p4@test.com'
        """).fetchone()

        assert result[0] == 'P4_NORMAL'
        conn.close()

    def test_indeterminate_classification(self, test_db):
        """Unknown conditions -> INDETERMINATE (0%)"""
        conn = test_db.connect()

        conn.execute("""
            INSERT INTO sign_in_logs (
                timestamp, user_principal_name, ip_address,
                location_country, status_error_code, conditional_access_status,
                risk_level, imported_at
            ) VALUES (
                '2025-11-25T10:00:00', 'indeterminate@test.com', '1.2.3.4',
                'AU', 999, 'unknownStatus', 'unknown', datetime('now')
            )
        """)
        conn.commit()

        result = conn.execute("""
            SELECT auth_determination, auth_confidence_pct
            FROM v_sign_in_auth_status
            WHERE user_principal_name = 'indeterminate@test.com'
        """).fetchone()

        assert result[0] == 'INDETERMINATE'
        assert result[1] == 0
        conn.close()

    def test_backward_compatibility_existing_queries(self, test_db):
        """Existing queries must continue to work"""
        conn = test_db.connect()

        # Insert mix of records
        conn.execute("""
            INSERT INTO sign_in_logs (
                timestamp, user_principal_name, ip_address,
                location_country, status_error_code, conditional_access_status,
                risk_level, imported_at
            ) VALUES
                ('2025-11-25T10:00:00', 'user1@test.com', '1.2.3.4', 'AU', 0, 'success', 'none', datetime('now')),
                ('2025-11-25T10:01:00', 'user2@test.com', '1.2.3.5', 'CN', 0, 'notApplied', 'high', datetime('now')),
                ('2025-11-25T10:02:00', 'user3@test.com', '1.2.3.6', 'AU', 50126, 'notApplied', 'none', datetime('now'))
        """)
        conn.commit()

        # Test typical existing query: foreign country logins
        result = conn.execute("""
            SELECT user_principal_name, auth_determination, auth_confidence_pct
            FROM v_sign_in_auth_status
            WHERE location_country NOT IN ('AU')
        """).fetchall()

        assert len(result) == 1
        assert result[0][0] == 'user2@test.com'
        assert result[0][1] == 'LIKELY_SUCCESS_RISKY'

        # Test typical existing query: failed auths
        result = conn.execute("""
            SELECT user_principal_name, auth_determination, auth_confidence_pct
            FROM v_sign_in_auth_status
            WHERE auth_determination = 'AUTH_FAILED'
        """).fetchall()

        assert len(result) == 1
        assert result[0][0] == 'user3@test.com'

        conn.close()

    def test_null_risk_level_handling(self, test_db):
        """NULL risk_level should be handled gracefully"""
        conn = test_db.connect()

        conn.execute("""
            INSERT INTO sign_in_logs (
                timestamp, user_principal_name, ip_address,
                location_country, status_error_code, conditional_access_status,
                risk_level, imported_at
            ) VALUES (
                '2025-11-25T10:00:00', 'nullrisk@test.com', '1.2.3.4',
                'AU', 0, 'notApplied', NULL, datetime('now')
            )
        """)
        conn.commit()

        result = conn.execute("""
            SELECT auth_determination, auth_confidence_pct
            FROM v_sign_in_auth_status
            WHERE user_principal_name = 'nullrisk@test.com'
        """).fetchone()

        assert result[0] == 'LIKELY_SUCCESS_NO_CA'
        assert result[1] == 60
        conn.close()

    def test_empty_string_risk_level(self, test_db):
        """Empty string risk_level should be treated as low risk"""
        conn = test_db.connect()

        conn.execute("""
            INSERT INTO sign_in_logs (
                timestamp, user_principal_name, ip_address,
                location_country, status_error_code, conditional_access_status,
                risk_level, imported_at
            ) VALUES (
                '2025-11-25T10:00:00', 'emptyrisk@test.com', '1.2.3.4',
                'AU', 0, 'notApplied', '', datetime('now')
            )
        """)
        conn.commit()

        result = conn.execute("""
            SELECT auth_determination, auth_confidence_pct
            FROM v_sign_in_auth_status
            WHERE user_principal_name = 'emptyrisk@test.com'
        """).fetchone()

        assert result[0] == 'LIKELY_SUCCESS_NO_CA'
        assert result[1] == 60
        conn.close()

    def test_hidden_risk_level(self, test_db):
        """'hidden' risk_level should be treated as low risk"""
        conn = test_db.connect()

        conn.execute("""
            INSERT INTO sign_in_logs (
                timestamp, user_principal_name, ip_address,
                location_country, status_error_code, conditional_access_status,
                risk_level, imported_at
            ) VALUES (
                '2025-11-25T10:00:00', 'hiddenrisk@test.com', '1.2.3.4',
                'AU', 0, 'notApplied', 'hidden', datetime('now')
            )
        """)
        conn.commit()

        result = conn.execute("""
            SELECT auth_determination, auth_confidence_pct
            FROM v_sign_in_auth_status
            WHERE user_principal_name = 'hiddenrisk@test.com'
        """).fetchone()

        assert result[0] == 'LIKELY_SUCCESS_NO_CA'
        assert result[1] == 60
        conn.close()


class TestBackupViewCreation:
    """Test backup view creation before changes."""

    def test_backup_view_exists(self, test_db):
        """Backup view v_sign_in_auth_status_v4_backup should exist"""
        conn = test_db.connect()

        # Check if backup view exists
        result = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='view' AND name='v_sign_in_auth_status_v4_backup'
        """).fetchone()

        assert result is not None, "Backup view v_sign_in_auth_status_v4_backup should exist"
        conn.close()

    def test_backup_view_queryable(self, test_db):
        """Backup view should be queryable"""
        conn = test_db.connect()

        # Insert test record
        conn.execute("""
            INSERT INTO sign_in_logs (
                timestamp, user_principal_name, ip_address,
                location_country, status_error_code, conditional_access_status,
                risk_level, imported_at
            ) VALUES (
                '2025-11-25T10:00:00', 'backup@test.com', '1.2.3.4',
                'AU', 0, 'success', 'none', datetime('now')
            )
        """)
        conn.commit()

        # Query backup view
        result = conn.execute("""
            SELECT COUNT(*) FROM v_sign_in_auth_status_v4_backup
        """).fetchone()

        assert result[0] >= 0  # Should be queryable without error
        conn.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
