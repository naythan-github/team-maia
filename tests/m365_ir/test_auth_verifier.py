#!/usr/bin/env python3
"""
Test suite for authentication status verifier - Phase 241

Tests the auth_verifier module to prevent forensic errors like
PIR-OCULUS-2025-12-19 where field names were misinterpreted as
indicating successful authentication.

Author: Maia System (SRE Principal Engineer Agent)
Created: 2026-01-06
"""

import json
import pytest
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path

from claude.tools.m365_ir.auth_verifier import (
    verify_auth_status,
    store_verification,
    get_verification_history,
    VerificationResult,
    STATUS_CODE_DESCRIPTIONS
)
from claude.tools.m365_ir.log_database import IRLogDatabase


@pytest.fixture
def test_db():
    """Create a test database with verification_summary table."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db = IRLogDatabase(case_id='TEST-AUTH-VERIFY', base_path=tmpdir)
        db.create()
        conn = db.connect()
        yield conn
        conn.close()


@pytest.fixture
def db_all_failed(test_db):
    """Database with 100% failed authentications (PIR-OCULUS-2025-12-19 scenario)."""
    cursor = test_db.cursor()

    # Insert 354 failed authentication attempts
    # 192 with status 50126, 162 with status 50053
    for i in range(192):
        cursor.execute("""
            INSERT INTO legacy_auth_logs
            (timestamp, user_principal_name, client_app_used, status,
             failure_reason, imported_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            f"2025-12-03T06:{i%60:02d}:00",
            'ben@oculus.info',
            'Authenticated SMTP',
            '50126',
            'Invalid credentials',
            datetime.now().isoformat()
        ))

    for i in range(162):
        cursor.execute("""
            INSERT INTO legacy_auth_logs
            (timestamp, user_principal_name, client_app_used, status,
             failure_reason, imported_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            f"2025-12-03T07:{i%60:02d}:00",
            'alia@oculus.info',
            'Authenticated SMTP',
            '50053',
            'Account locked',
            datetime.now().isoformat()
        ))

    test_db.commit()
    return test_db


@pytest.fixture
def db_mixed_success(test_db):
    """Database with mixed success/failure (25% success rate)."""
    cursor = test_db.cursor()

    # 25 successful authentications
    for i in range(25):
        cursor.execute("""
            INSERT INTO legacy_auth_logs
            (timestamp, user_principal_name, client_app_used, status,
             failure_reason, imported_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            f"2025-12-01T{i%24:02d}:00:00",
            'legitimate@company.com',
            'Mobile Apps and Desktop clients',
            '0',
            None,
            datetime.now().isoformat()
        ))

    # 75 failed authentications
    for i in range(75):
        cursor.execute("""
            INSERT INTO legacy_auth_logs
            (timestamp, user_principal_name, client_app_used, status,
             failure_reason, imported_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            f"2025-12-02T{i%24:02d}:00:00",
            'attacker@evil.com',
            'Authenticated SMTP',
            '50126',
            'Invalid credentials',
            datetime.now().isoformat()
        ))

    test_db.commit()
    return test_db


@pytest.fixture
def db_all_success(test_db):
    """Database with 100% successful authentications."""
    cursor = test_db.cursor()

    for i in range(50):
        cursor.execute("""
            INSERT INTO legacy_auth_logs
            (timestamp, user_principal_name, client_app_used, status,
             failure_reason, imported_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            f"2025-12-01T{i%24:02d}:00:00",
            'admin@company.com',
            'Mobile Apps and Desktop clients',
            '0',
            None,
            datetime.now().isoformat()
        ))

    test_db.commit()
    return test_db


@pytest.fixture
def db_empty(test_db):
    """Database with no authentication records."""
    return test_db


@pytest.fixture
def db_no_status_field(test_db):
    """Database with a table that has no status field."""
    cursor = test_db.cursor()

    # Create a custom table without status field
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS custom_logs (
            id INTEGER PRIMARY KEY,
            timestamp TEXT,
            user_principal_name TEXT
        )
    """)

    test_db.commit()
    return test_db


class TestVerifyAuthStatus:
    """Test verify_auth_status function."""

    def test_verify_all_failed_pir_oculus_scenario(self, db_all_failed):
        """
        Verify detection of 100% failure rate (PIR-OCULUS-2025-12-19).

        This test simulates the exact error scenario where 354 "Authenticated SMTP"
        events were incorrectly interpreted as successful authentications, when
        ALL were actually failures (status 50126/50053).
        """
        result = verify_auth_status(db_all_failed, 'legacy_auth')

        assert result.total_events == 354
        assert result.successful == 0
        assert result.failed == 354
        assert result.success_rate == 0.0
        assert len(result.warnings) >= 1
        assert any("0% success rate" in w for w in result.warnings)
        assert any("all authentication attempts FAILED" in w for w in result.warnings)

        # Verify status code breakdown
        assert result.status_codes['50126'] == 192
        assert result.status_codes['50053'] == 162
        assert sum(result.status_codes.values()) == result.total_events

    def test_verify_mixed_success(self, db_mixed_success):
        """Verify detection of mixed success/failure (25% success)."""
        result = verify_auth_status(db_mixed_success, 'legacy_auth')

        assert result.total_events == 100
        assert result.successful == 25
        assert result.failed == 75
        assert result.success_rate == 25.0

        # No warnings for normal mixed pattern
        suspicious_warnings = [
            w for w in result.warnings
            if "100% success" in w or "0% success" in w
        ]
        assert len(suspicious_warnings) == 0

    def test_verify_100_percent_success_warning(self, db_all_success):
        """Verify warning for 100% success rate (potential compromise)."""
        result = verify_auth_status(db_all_success, 'legacy_auth')

        assert result.success_rate == 100.0
        assert result.total_events == 50
        assert result.successful == 50
        assert result.failed == 0
        assert any("100% success rate" in w for w in result.warnings)
        assert any("verify this is expected" in w for w in result.warnings)

    def test_verify_high_success_rate_warning(self, test_db):
        """Verify warning for >80% success rate."""
        cursor = test_db.cursor()

        # 85 successful, 15 failed = 85% success rate
        for i in range(85):
            cursor.execute("""
                INSERT INTO legacy_auth_logs
                (timestamp, user_principal_name, client_app_used, status, imported_at)
                VALUES (?, ?, ?, ?, ?)
            """, (f"2025-12-01T00:00:{i}", 'user@test.com', 'Client', '0', datetime.now().isoformat()))

        for i in range(15):
            cursor.execute("""
                INSERT INTO legacy_auth_logs
                (timestamp, user_principal_name, client_app_used, status, imported_at)
                VALUES (?, ?, ?, ?, ?)
            """, (f"2025-12-01T01:00:{i}", 'user@test.com', 'Client', '50126', datetime.now().isoformat()))

        test_db.commit()

        result = verify_auth_status(test_db, 'legacy_auth')
        assert result.success_rate == 85.0
        assert any("High success rate" in w for w in result.warnings)

    def test_verify_empty_database(self, db_empty):
        """Verify handling of empty database (no events)."""
        result = verify_auth_status(db_empty, 'legacy_auth')

        assert result.total_events == 0
        assert result.successful == 0
        assert result.failed == 0
        assert result.success_rate == 0.0
        assert any("No events found" in w for w in result.warnings)

    def test_verify_status_code_breakdown(self, db_all_failed):
        """Verify status code breakdown is accurate."""
        result = verify_auth_status(db_all_failed, 'legacy_auth')

        # Check exact counts
        assert result.status_codes['50126'] == 192
        assert result.status_codes['50053'] == 162

        # Verify sum equals total
        assert sum(result.status_codes.values()) == result.total_events

        # No successful status codes should be present
        assert '0' not in result.status_codes
        assert 'Success' not in result.status_codes

    def test_verify_invalid_log_type(self, test_db):
        """Verify error on invalid log type."""
        with pytest.raises(ValueError, match="Unknown log_type"):
            verify_auth_status(test_db, 'invalid_type')

    def test_verify_table_no_status_field(self, test_db):
        """Verify error when table has no status field."""
        # unified_audit_log exists but uses 'result_status', not 'status'
        # This should raise ValueError
        with pytest.raises(ValueError, match="has no status field"):
            verify_auth_status(test_db, 'unified_audit')

    def test_verify_unknown_status_codes(self, test_db):
        """Verify warning for unknown status codes."""
        cursor = test_db.cursor()

        # Insert events with unknown status code
        cursor.execute("""
            INSERT INTO legacy_auth_logs
            (timestamp, user_principal_name, client_app_used, status, imported_at)
            VALUES (?, ?, ?, ?, ?)
        """, ('2025-12-01T00:00:00', 'user@test.com', 'Client', '99999', datetime.now().isoformat()))

        test_db.commit()

        result = verify_auth_status(test_db, 'legacy_auth')
        assert any("Unknown status codes" in w for w in result.warnings)
        assert '99999' in result.status_codes

    def test_verify_result_has_timestamp(self, db_mixed_success):
        """Verify result includes ISO timestamp."""
        result = verify_auth_status(db_mixed_success, 'legacy_auth')

        assert result.verified_at is not None
        # Verify it's valid ISO format
        datetime.fromisoformat(result.verified_at)

    def test_verify_success_with_status_text(self, test_db):
        """Verify handling of 'Success' text status (not just '0')."""
        cursor = test_db.cursor()

        # Some logs use 'Success' instead of '0'
        cursor.execute("""
            INSERT INTO legacy_auth_logs
            (timestamp, user_principal_name, client_app_used, status, imported_at)
            VALUES (?, ?, ?, ?, ?)
        """, ('2025-12-01T00:00:00', 'user@test.com', 'Client', 'Success', datetime.now().isoformat()))

        test_db.commit()

        result = verify_auth_status(test_db, 'legacy_auth')
        assert result.successful == 1
        assert result.success_rate == 100.0


class TestStoreVerification:
    """Test store_verification function."""

    def test_store_verification_basic(self, test_db):
        """Verify results are stored in database."""
        # Create a verification result
        result = VerificationResult(
            log_type='legacy_auth',
            total_events=100,
            successful=25,
            failed=75,
            success_rate=25.0,
            status_codes={'0': 25, '50126': 75},
            warnings=[],
            verified_at=datetime.now().isoformat()
        )

        verification_id = store_verification(test_db, result)

        # Verify it was stored
        stored = test_db.execute(
            "SELECT * FROM verification_summary WHERE id = ?",
            (verification_id,)
        ).fetchone()

        assert stored is not None
        assert stored['log_type'] == 'legacy_auth'
        assert stored['total_events'] == 100
        assert stored['successful'] == 25
        assert stored['failed'] == 75
        assert stored['success_rate'] == 25.0

        # Verify status_code_breakdown is valid JSON
        breakdown = json.loads(stored['status_code_breakdown'])
        assert breakdown['0'] == 25
        assert breakdown['50126'] == 75

    def test_store_verification_with_warnings(self, test_db):
        """Verify warnings are stored as notes."""
        result = VerificationResult(
            log_type='legacy_auth',
            total_events=50,
            successful=0,
            failed=50,
            success_rate=0.0,
            status_codes={'50126': 50},
            warnings=["⚠️ Warning 1", "⚠️ Warning 2"],
            verified_at=datetime.now().isoformat()
        )

        verification_id = store_verification(test_db, result)

        stored = test_db.execute(
            "SELECT notes FROM verification_summary WHERE id = ?",
            (verification_id,)
        ).fetchone()

        assert stored['notes'] == "⚠️ Warning 1; ⚠️ Warning 2"

    def test_store_verification_no_warnings(self, test_db):
        """Verify NULL notes when no warnings."""
        result = VerificationResult(
            log_type='legacy_auth',
            total_events=50,
            successful=25,
            failed=25,
            success_rate=50.0,
            status_codes={'0': 25, '50126': 25},
            warnings=[],
            verified_at=datetime.now().isoformat()
        )

        verification_id = store_verification(test_db, result)

        stored = test_db.execute(
            "SELECT notes FROM verification_summary WHERE id = ?",
            (verification_id,)
        ).fetchone()

        assert stored['notes'] is None

    def test_store_verification_returns_id(self, test_db):
        """Verify store_verification returns valid ID."""
        result = VerificationResult(
            log_type='legacy_auth',
            total_events=10,
            successful=5,
            failed=5,
            success_rate=50.0,
            status_codes={'0': 5, '50126': 5},
            warnings=[],
            verified_at=datetime.now().isoformat()
        )

        verification_id = store_verification(test_db, result)

        assert isinstance(verification_id, int)
        assert verification_id > 0


class TestGetVerificationHistory:
    """Test get_verification_history function."""

    def test_get_verification_history_all(self, test_db):
        """Retrieve all verification records."""
        # Store multiple verifications
        for i in range(3):
            result = VerificationResult(
                log_type='legacy_auth' if i % 2 == 0 else 'sign_in',
                total_events=100 + i,
                successful=50,
                failed=50 + i,
                success_rate=50.0,
                status_codes={'0': 50},
                warnings=[],
                verified_at=datetime.now().isoformat()
            )
            store_verification(test_db, result)

        history = get_verification_history(test_db)

        assert len(history) == 3
        assert all(isinstance(record, dict) for record in history)

    def test_get_verification_history_filtered(self, test_db):
        """Retrieve verification records filtered by log type."""
        # Store verifications for different log types
        for log_type in ['legacy_auth', 'sign_in', 'legacy_auth']:
            result = VerificationResult(
                log_type=log_type,
                total_events=100,
                successful=50,
                failed=50,
                success_rate=50.0,
                status_codes={'0': 50},
                warnings=[],
                verified_at=datetime.now().isoformat()
            )
            store_verification(test_db, result)

        history = get_verification_history(test_db, log_type='legacy_auth')

        assert len(history) == 2
        assert all(record['log_type'] == 'legacy_auth' for record in history)

    def test_get_verification_history_empty(self, test_db):
        """Verify empty list when no verifications exist."""
        history = get_verification_history(test_db)
        assert history == []

    def test_get_verification_history_ordered(self, test_db):
        """Verify results are ordered by verified_at DESC."""
        import time

        # Store verifications with slight time delays
        timestamps = []
        for i in range(3):
            result = VerificationResult(
                log_type='legacy_auth',
                total_events=100,
                successful=50,
                failed=50,
                success_rate=50.0,
                status_codes={'0': 50},
                warnings=[],
                verified_at=datetime.now().isoformat()
            )
            timestamps.append(result.verified_at)
            store_verification(test_db, result)
            time.sleep(0.01)  # Small delay to ensure different timestamps

        history = get_verification_history(test_db)

        # Should be in reverse chronological order
        assert len(history) == 3
        # Most recent should be first
        assert history[0]['verified_at'] >= history[1]['verified_at']
        assert history[1]['verified_at'] >= history[2]['verified_at']


class TestIntegration:
    """Integration tests combining verify + store + retrieve."""

    def test_full_workflow_pir_oculus_scenario(self, db_all_failed):
        """
        Full workflow test simulating PIR-OCULUS-2025-12-19 investigation.

        This test validates the complete Phase 241 solution:
        1. Import logs with misleading field names
        2. Run verification
        3. Detect 0% success rate
        4. Store verification
        5. Retrieve history
        """
        # Step 1: Verify authentication status
        result = verify_auth_status(db_all_failed, 'legacy_auth')

        # Step 2: Validate detection
        assert result.total_events == 354
        assert result.success_rate == 0.0
        assert any("0% success rate" in w for w in result.warnings)
        assert any("FAILED" in w for w in result.warnings)

        # Step 3: Store verification
        verification_id = store_verification(db_all_failed, result)
        assert verification_id > 0

        # Step 4: Retrieve history
        history = get_verification_history(db_all_failed, 'legacy_auth')
        assert len(history) == 1
        assert history[0]['total_events'] == 354
        assert history[0]['success_rate'] == 0.0

        # Step 5: Verify status code breakdown in history
        breakdown = json.loads(history[0]['status_code_breakdown'])
        assert breakdown['50126'] == 192
        assert breakdown['50053'] == 162

        # Step 6: Verify warnings are in notes
        assert "0% success rate" in history[0]['notes']


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, '-v', '--tb=short'])
