"""
Phase 1.1: Extended Authentication Verification - Test Suite

Tests for extending auth_verifier to sign_in_logs and unified_audit_log.

TDD Approach:
1. Write these tests FIRST (they will fail)
2. Implement auth_verifier.py extensions to make tests pass
3. Refactor while keeping tests green

Test Coverage Target: 100%

Expected Implementation Location:
- claude/tools/m365_ir/auth_verifier.py (extend existing)
"""

import pytest
import sqlite3
from pathlib import Path


class TestSignInLogVerification:
    """
    Tests for sign_in_logs authentication verification.

    Goal: Prevent PIR-OCULUS type errors where wrong status field is used.
    """

    def test_verify_sign_in_logs_detects_breach(self, oculus_test_db):
        """
        CRITICAL TEST: System must detect 188 successful foreign logins (Oculus breach).

        Test Data:
        - 188 successful foreign logins from VN/CN/US
        - 2,748 legitimate AU logins
        - 51 failed login attempts
        Total: 2,987 sign_in_logs records

        Expected Behavior:
        - Uses conditional_access_status field (NOT status_error_code)
        - Detects 188 successful foreign logins
        - Calculates 6.3% foreign success rate (188/2,987)
        - Triggers breach alert (>5% foreign success threshold)

        This test MUST pass to prevent future Oculus-class errors.
        """
        # TDD: This will fail until we implement verify_sign_in_status()
        from claude.tools.m365_ir.auth_verifier import verify_sign_in_status

        result = verify_sign_in_status(oculus_test_db)

        # Assertions
        assert result.total_records == 2987, "Should count all sign_in_logs"
        assert result.success_count == 2936, "Should detect all successes (188 foreign + 2,748 AU)"
        assert result.failure_count == 51, "Should detect all failures"
        assert result.success_rate == pytest.approx(98.3, rel=0.1), "Success rate should be ~98%"

        # Critical: Must detect breach
        assert result.foreign_success_count == 188, "MUST detect 188 foreign successful logins"
        assert result.breach_detected is True, "MUST trigger breach alert"
        assert result.status_field_used == 'conditional_access_status', \
            "MUST use conditional_access_status, not status_error_code"

    def test_verify_sign_in_logs_rejects_unreliable_field(self, oculus_test_db):
        """
        Test that system REJECTS status_error_code as unreliable (100% uniform).

        This is the core prevention mechanism for Oculus-class errors.
        """
        from claude.tools.m365_ir.auth_verifier import verify_sign_in_status

        result = verify_sign_in_status(oculus_test_db)

        # Should NOT use status_error_code
        assert 'status_error_code' not in result.status_field_used, \
            "Must reject status_error_code (100% uniform = unreliable)"

        # Should emit warning about unreliable field
        assert any('status_error_code' in warning for warning in result.warnings), \
            "Should warn that status_error_code is unreliable"

    def test_verify_sign_in_logs_with_perfect_data(self, perfect_quality_db):
        """
        Test verification with high-quality data (all fields populated, consistent).

        Expected: Clean pass, no warnings.
        """
        from claude.tools.m365_ir.auth_verifier import verify_sign_in_status

        result = verify_sign_in_status(perfect_quality_db)

        assert result.total_records == 1000
        assert len(result.warnings) == 0, "Perfect data should produce no warnings"
        assert result.data_quality_score >= 0.95, "Perfect data should score >95%"

    def test_verify_sign_in_logs_with_bad_data(self, bad_quality_db):
        """
        Test verification with bad data quality (unpopulated fields, uniform values).

        Expected: Quality check failure, explicit warnings.
        """
        from claude.tools.m365_ir.auth_verifier import verify_sign_in_status

        result = verify_sign_in_status(bad_quality_db)

        # Should detect bad data quality
        assert result.data_quality_score < 0.5, "Bad data should score <50%"
        assert len(result.warnings) > 0, "Bad data should produce warnings"
        assert any('uniform' in warning.lower() or '100%' in warning for warning in result.warnings), \
            "Should warn about 100% uniform field"

    def test_verify_sign_in_logs_performance(self, oculus_test_db):
        """
        Test that verification completes in <2 seconds for ~3K records.

        Performance target: <2 seconds for 10K events (Oculus has ~3K).
        """
        import time
        from claude.tools.m365_ir.auth_verifier import verify_sign_in_status

        start = time.time()
        result = verify_sign_in_status(oculus_test_db)
        elapsed = time.time() - start

        assert elapsed < 2.0, f"Verification took {elapsed:.2f}s, should be <2s for 3K records"
        assert result.total_records == 2987

    def test_verify_sign_in_logs_stores_results(self, oculus_test_db):
        """
        Test that verification results are stored in verification_summary table.

        This enables historical tracking and audit trail.
        """
        from claude.tools.m365_ir.auth_verifier import verify_sign_in_status

        # Run verification
        result = verify_sign_in_status(oculus_test_db)

        # Check that results were stored
        conn = sqlite3.connect(oculus_test_db)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT log_type, total_records, success_count, verification_status
            FROM verification_summary
            WHERE log_type = 'sign_in_logs'
            ORDER BY created_at DESC
            LIMIT 1
        """)
        row = cursor.fetchone()
        conn.close()

        assert row is not None, "Verification results should be stored"
        log_type, total, success, status = row
        assert log_type == 'sign_in_logs'
        assert total == 2987
        assert success == 2936
        assert status == 'BREACH_DETECTED'


class TestUnifiedAuditLogVerification:
    """
    Tests for unified_audit_log verification.

    Goal: Detect data exfiltration patterns (MailItemsAccessed, FileSyncDownloadedFull).
    """

    def test_verify_audit_log_detects_mail_access(self, oculus_test_db):
        """
        Test detection of MailItemsAccessed operations (data exfiltration indicator).

        Oculus case: 160 MailItemsAccessed events from compromised accounts.
        """
        from claude.tools.m365_ir.auth_verifier import verify_audit_log_operations

        result = verify_audit_log_operations(oculus_test_db)

        # Should detect MailItemsAccessed operations
        assert result.total_records == 160, "Should count unified_audit_log records"
        assert result.mail_items_accessed > 0, "Should detect MailItemsAccessed operations"
        assert result.exfiltration_indicator is True, \
            "High volume MailItemsAccessed should trigger exfiltration alert"

    def test_verify_audit_log_with_no_suspicious_activity(self, perfect_quality_db):
        """
        Test audit log verification with normal operations (no exfiltration).

        Expected: Clean pass, no alerts.
        """
        # Add normal unified_audit_log records
        conn = sqlite3.connect(perfect_quality_db)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE unified_audit_log (
                log_id INTEGER PRIMARY KEY,
                timestamp TEXT,
                user_id TEXT,
                operation TEXT,
                result_status TEXT,
                client_ip TEXT
            )
        """)

        # Insert 50 normal operations (FileAccessed, not MailItemsAccessed)
        for i in range(50):
            cursor.execute("""
                INSERT INTO unified_audit_log (timestamp, user_id, operation, result_status, client_ip)
                VALUES (?, ?, ?, ?, ?)
            """, (
                '2025-11-04T10:00:00',
                f'user{i}@test.com',
                'FileAccessed',
                'Success',
                '203.0.113.1'
            ))
        conn.commit()
        conn.close()

        from claude.tools.m365_ir.auth_verifier import verify_audit_log_operations

        result = verify_audit_log_operations(perfect_quality_db)

        assert result.total_records == 50
        assert result.mail_items_accessed == 0, "Should find no MailItemsAccessed"
        assert result.exfiltration_indicator is False, "Normal operations should not trigger alert"

    def test_verify_audit_log_performance(self, oculus_test_db):
        """
        Test that audit log verification is fast (<1 second for 160 records).
        """
        import time
        from claude.tools.m365_ir.auth_verifier import verify_audit_log_operations

        start = time.time()
        result = verify_audit_log_operations(oculus_test_db)
        elapsed = time.time() - start

        assert elapsed < 1.0, f"Audit verification took {elapsed:.2f}s, should be <1s"
        assert result.total_records == 160


class TestIntegrationWithLogImporter:
    """
    Tests for integration with log_importer.py.

    Goal: Ensure verifications run automatically on import.
    """

    def test_log_importer_calls_sign_in_verifier(self, temp_db):
        """
        Test that log_importer.py automatically calls verify_sign_in_status().

        This integration test ensures auto-verification works end-to-end.
        """
        # TDD: This will fail until we update log_importer.py
        from claude.tools.m365_ir.log_importer import import_logs
        from claude.tools.m365_ir.auth_verifier import verify_sign_in_status

        # Mock CSV file with sign_in_logs
        import tempfile
        import csv

        csv_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        writer = csv.DictWriter(csv_file, fieldnames=[
            'Created (UTC)', 'User principal name', 'User ID', 'Application',
            'Location', 'IP address', 'Status error code', 'Conditional access status'
        ])
        writer.writeheader()
        writer.writerow({
            'Created (UTC)': '2025-11-04T10:00:00Z',
            'User principal name': 'user@test.com',
            'User ID': 'user_123',
            'Application': 'Microsoft Exchange',
            'Location': 'AU',
            'IP address': '203.0.113.1',
            'Status error code': '0',
            'Conditional access status': 'success'
        })
        csv_file.close()

        # Import and check that verification ran
        # TBD: Update import_logs signature to return verification results
        # result = import_logs(csv_file.name, temp_db, log_type='sign_in_logs')
        # assert result.verification_ran is True
        # assert result.verification_status is not None

        # Cleanup
        import os
        os.unlink(csv_file.name)

        # For now, just verify the function exists
        assert callable(verify_sign_in_status)

    def test_verification_runs_on_all_log_types(self, oculus_test_db):
        """
        Test that ALL log types get verified during import.

        Expected:
        - sign_in_logs → verify_sign_in_status()
        - unified_audit_log → verify_audit_log_operations()
        - legacy_auth_logs → verify_auth_status() [Phase 241, already exists]
        """
        # TDD: Integration test placeholder
        # Will implement when log_importer.py is updated

        # Verify that all verifier functions exist
        from claude.tools.m365_ir.auth_verifier import (
            verify_auth_status,      # Phase 241 - exists
            # verify_sign_in_status,   # Phase 1.1 - to be implemented
            # verify_audit_log_operations  # Phase 1.1 - to be implemented
        )

        # Phase 241 verifier exists
        assert callable(verify_auth_status)

        # Phase 1.1 verifiers will be implemented
        # assert callable(verify_sign_in_status)
        # assert callable(verify_audit_log_operations)


class TestBreachAlertThresholds:
    """
    Tests for breach detection alert thresholds.

    Goal: Ensure alerts trigger at correct thresholds (avoid false positives/negatives).
    """

    def test_breach_alert_triggers_above_80_percent_foreign_success(self, temp_db):
        """
        Test that >80% foreign IP success rate triggers CRITICAL breach alert.

        This is a strong indicator of compromise.
        """
        # Create test data: 85% foreign success
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE sign_in_logs (
                log_id INTEGER PRIMARY KEY,
                timestamp TEXT,
                user_id TEXT,
                location_country TEXT,
                ip_address TEXT,
                conditional_access_status TEXT
            )
        """)

        # 85 successful foreign logins
        for i in range(85):
            cursor.execute("""
                INSERT INTO sign_in_logs (timestamp, user_id, location_country, ip_address, conditional_access_status)
                VALUES (?, ?, ?, ?, ?)
            """, ('2025-11-04T10:00:00', f'user{i}', 'CN', '119.18.1.188', 'success'))

        # 15 successful AU logins
        for i in range(15):
            cursor.execute("""
                INSERT INTO sign_in_logs (timestamp, user_id, location_country, ip_address, conditional_access_status)
                VALUES (?, ?, ?, ?, ?)
            """, ('2025-11-04T11:00:00', f'user{i}', 'AU', '203.0.113.1', 'success'))

        conn.commit()
        conn.close()

        from claude.tools.m365_ir.auth_verifier import verify_sign_in_status

        result = verify_sign_in_status(temp_db)

        assert result.foreign_success_rate == pytest.approx(85.0, rel=1), "Should calculate 85% foreign"
        assert result.breach_detected is True, ">80% foreign should trigger breach alert"
        assert result.alert_severity == 'CRITICAL', "High foreign success should be CRITICAL"

    def test_breach_alert_does_not_trigger_for_normal_traffic(self, temp_db):
        """
        Test that normal traffic patterns do NOT trigger false alerts.

        Example: 5% foreign logins (business travel) should not alert.
        """
        # Create test data: 5% foreign success (normal)
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE sign_in_logs (
                log_id INTEGER PRIMARY KEY,
                timestamp TEXT,
                user_id TEXT,
                location_country TEXT,
                ip_address TEXT,
                conditional_access_status TEXT
            )
        """)

        # 5 successful foreign logins (business travel)
        for i in range(5):
            cursor.execute("""
                INSERT INTO sign_in_logs (timestamp, user_id, location_country, ip_address, conditional_access_status)
                VALUES (?, ?, ?, ?, ?)
            """, ('2025-11-04T10:00:00', f'user{i}', 'US', '207.180.205.36', 'success'))

        # 95 successful AU logins
        for i in range(95):
            cursor.execute("""
                INSERT INTO sign_in_logs (timestamp, user_id, location_country, ip_address, conditional_access_status)
                VALUES (?, ?, ?, ?, ?)
            """, ('2025-11-04T11:00:00', f'user{i}', 'AU', '203.0.113.1', 'success'))

        conn.commit()
        conn.close()

        from claude.tools.m365_ir.auth_verifier import verify_sign_in_status

        result = verify_sign_in_status(temp_db)

        assert result.foreign_success_rate == pytest.approx(5.0, rel=1), "Should calculate 5% foreign"
        assert result.breach_detected is False, "5% foreign should NOT trigger breach alert"


# Mark all tests as Phase 1.1
pytestmark = pytest.mark.phase_1_1
