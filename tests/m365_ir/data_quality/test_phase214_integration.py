"""
Phase 2.1.4 - Integration Tests

Test Objective:
    Validate integration of field_reliability_scorer.py with auth_verifier.py
    and log_importer.py. Ensure backward compatibility and graceful degradation.

Key Features Tested:
    1. Phase 2.1 scoring replaces hard-coded field selection
    2. Backward compatibility with Phase 1 when disabled
    3. Graceful degradation on Phase 2.1 errors
    4. Historical learning database storage after verification
    5. Cross-case learning accumulation

Phase: PHASE_2_SMART_ANALYSIS (Phase 2.1.4 - Integration)
Status: TDD - RED Phase (tests written, implementation pending)
TDD Cycle: Red → Green → Refactor
"""

import pytest
import sqlite3
import tempfile
import os
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock


@pytest.mark.phase_2_1
class TestPhase214Integration:
    """Integration tests for Phase 2.1.4."""

    def setup_method(self):
        """Create test environment before each test."""
        self.tmpdir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.tmpdir, "PIR-TEST-2025-01_logs.db")

        # Historical DB path (use temp location for tests)
        self.history_db_path = os.path.join(self.tmpdir, "history.db")

    def teardown_method(self):
        """Clean up test environment after each test."""
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _create_test_sign_in_db(
        self,
        db_path: str,
        conditional_access_distribution: tuple = (50, 50),
        status_error_code_distribution: tuple = (99, 1)
    ):
        """
        Create test sign_in_logs database with configurable field distributions.

        Args:
            db_path: Path to database
            conditional_access_distribution: (success_count, failure_count)
            status_error_code_distribution: (same_value_count, different_value_count)
        """
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create sign_in_logs table with realistic schema
        cursor.execute("""
            CREATE TABLE sign_in_logs (
                id INTEGER PRIMARY KEY,
                user_principal_name TEXT,
                created_date_time TEXT,
                ip_address TEXT,
                conditional_access_status TEXT,
                status_error_code INTEGER,
                result_status TEXT,
                is_suspicious_activity INTEGER
            )
        """)

        # Insert records with specified distributions
        total_records = sum(conditional_access_distribution)

        for i in range(total_records):
            # conditional_access_status: varies by distribution
            ca_status = "success" if i < conditional_access_distribution[0] else "failure"

            # status_error_code: mostly same value (99% = 1)
            error_code = 1 if i < status_error_code_distribution[0] else 2

            # result_status: similar to conditional_access
            result = "Success" if i < conditional_access_distribution[0] else "Failure"

            cursor.execute("""
                INSERT INTO sign_in_logs (
                    user_principal_name,
                    created_date_time,
                    ip_address,
                    conditional_access_status,
                    status_error_code,
                    result_status,
                    is_suspicious_activity
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                f"user{i}@test.com",
                "2025-01-07T10:00:00Z",
                "192.168.1.1" if i % 2 == 0 else "10.0.0.1",
                ca_status,
                error_code,
                result,
                1 if i >= 80 else 0  # 80% foreign for breach detection
            ))

        conn.commit()
        conn.close()

    def test_phase214_full_integration_with_phase21_scoring(self):
        """
        Test 1: Verify Phase 2.1 scoring is used when enabled.

        Expected behavior:
        - Phase 2.1 recommend_best_field() selects best field
        - SignInVerificationSummary has Phase 2.1 metadata
        - Historical DB has 1 record after verification
        """
        from claude.tools.m365_ir.auth_verifier import verify_sign_in_status, USE_PHASE_2_1_SCORING

        # Create test DB with clear winner (50/50 vs 99% uniform)
        self._create_test_sign_in_db(
            self.test_db_path,
            conditional_access_distribution=(50, 50),
            status_error_code_distribution=(99, 1)
        )

        # Patch HISTORICAL_DB_PATH to use test location
        with patch('claude.tools.m365_ir.auth_verifier.HISTORICAL_DB_PATH', Path(self.history_db_path)):
            # Verify Phase 2.1 is enabled
            assert USE_PHASE_2_1_SCORING is True, "Phase 2.1 should be enabled for this test"

            # Call verification
            result = verify_sign_in_status(self.test_db_path)

            # Assert Phase 2.1 field selection
            assert result.field_used == 'conditional_access_status', \
                "Phase 2.1 should select conditional_access_status (best field)"

            assert result.field_confidence in ['HIGH', 'MEDIUM'], \
                f"Expected HIGH or MEDIUM confidence, got {result.field_confidence}"

            assert result.field_score is not None and result.field_score > 0.5, \
                "Field score should be set and > 0.5"

            assert result.field_selection_reasoning is not None, \
                "Field selection reasoning should be provided"

            # Verify backward compatibility field also set
            assert result.status_field_used == 'conditional_access_status', \
                "Backward compat field should match field_used"

            # Verify historical DB was created and populated
            # Note: This will be checked in test 4 in detail
            assert Path(self.history_db_path).exists(), \
                "Historical DB should be created during verification"

    def test_phase214_backward_compatibility_with_phase1_fallback(self):
        """
        Test 2: Verify Phase 1 fallback when Phase 2.1 disabled.

        Expected behavior:
        - Verification succeeds with Phase 1 logic
        - Phase 2.1 fields are None/unset
        - No historical DB records created
        """
        from claude.tools.m365_ir.auth_verifier import verify_sign_in_status

        # Create test DB
        self._create_test_sign_in_db(self.test_db_path)

        # Temporarily disable Phase 2.1
        with patch('claude.tools.m365_ir.auth_verifier.USE_PHASE_2_1_SCORING', False):
            with patch('claude.tools.m365_ir.auth_verifier.HISTORICAL_DB_PATH', Path(self.history_db_path)):
                # Call verification
                result = verify_sign_in_status(self.test_db_path)

                # Assert Phase 1 behavior
                assert result.status_field_used is not None, \
                    "Verification should succeed with Phase 1 logic"

                # Phase 2.1 fields should be None (not set)
                assert result.field_used is None, \
                    "field_used should be None when Phase 2.1 disabled"

                assert result.field_confidence is None, \
                    "field_confidence should be None when Phase 2.1 disabled"

                assert result.field_score is None, \
                    "field_score should be None when Phase 2.1 disabled"

                # Historical DB should NOT be created (Phase 1 doesn't use it)
                assert not Path(self.history_db_path).exists(), \
                    "Historical DB should not be created when Phase 2.1 disabled"

    def test_phase214_graceful_degradation_on_phase21_error(self):
        """
        Test 3: Verify automatic fallback when Phase 2.1 fails.

        Expected behavior:
        - Phase 2.1 exception caught and logged
        - Fallback to Phase 1 logic (no exception propagated)
        - Verification succeeds with Phase 1 field selection
        - Warning logged containing "Phase 2.1 failed" and "fallback"
        """
        from claude.tools.m365_ir.auth_verifier import verify_sign_in_status

        # Create test DB
        self._create_test_sign_in_db(self.test_db_path)

        # Mock recommend_best_field to raise exception
        with patch('claude.tools.m365_ir.auth_verifier.USE_PHASE_2_1_SCORING', True):
            with patch('claude.tools.m365_ir.auth_verifier.HISTORICAL_DB_PATH', Path(self.history_db_path)):
                with patch('claude.tools.m365_ir.field_reliability_scorer.recommend_best_field') as mock_recommend:
                    # Mock failure
                    mock_recommend.side_effect = ValueError("Mock Phase 2.1 failure")

                    # Call verification (should NOT raise exception)
                    result = verify_sign_in_status(self.test_db_path)

                    # Assert fallback to Phase 1 succeeded
                    assert result.status_field_used is not None, \
                        "Verification should succeed with Phase 1 fallback"

                    # Phase 2.1 fields should be None (fallback used)
                    assert result.field_used is None or result.field_confidence is None, \
                        "Phase 2.1 fields should be None when fallback triggered"

                    # Verify recommend_best_field was called (and failed)
                    assert mock_recommend.called, \
                        "Phase 2.1 recommend_best_field should have been attempted"

    def test_phase214_historical_learning_storage(self):
        """
        Test 4: Verify field usage outcome stored after verification.

        Expected behavior:
        - After import, historical DB has 1 record
        - Record has correct case_id, field_name, breach_detected
        - Timestamp is recent
        """
        from claude.tools.m365_ir.field_reliability_scorer import create_history_database

        # Create historical DB first
        create_history_database(self.history_db_path)

        # Create test DB with breach scenario
        self._create_test_sign_in_db(self.test_db_path)

        # Patch HISTORICAL_DB_PATH
        with patch('claude.tools.m365_ir.auth_verifier.HISTORICAL_DB_PATH', Path(self.history_db_path)):
            with patch('claude.tools.m365_ir.auth_verifier.USE_PHASE_2_1_SCORING', True):
                # Import via log_importer (triggers verification and storage)
                # Note: Need to create importer with test DB
                # This test may need adjustment based on actual log_importer API

                # For now, test direct storage call (integration with importer tested in e2e)
                from claude.tools.m365_ir.auth_verifier import verify_sign_in_status
                from claude.tools.m365_ir.field_reliability_scorer import store_field_usage

                # Run verification
                result = verify_sign_in_status(self.test_db_path)

                # Manually store (simulating what log_importer does)
                case_id = "PIR-TEST-2025-01"
                verification_successful = not any('CRITICAL' in w for w in result.warnings)

                store_field_usage(
                    history_db_path=self.history_db_path,
                    case_id=case_id,
                    log_type='sign_in_logs',
                    field_name=result.field_used,
                    reliability_score=result.field_score or 0.5,
                    used_for_verification=True,
                    verification_successful=verification_successful,
                    breach_detected=result.breach_detected,
                    notes=f"Foreign success: {result.foreign_success_rate:.1f}%"
                )

                # Verify historical DB record
                conn = sqlite3.connect(self.history_db_path)
                cursor = conn.cursor()

                records = cursor.execute("""
                    SELECT case_id, log_type, field_name, used_for_verification,
                           verification_successful, breach_detected, created_at
                    FROM field_reliability_history
                """).fetchall()

                conn.close()

                # Assert exactly 1 record
                assert len(records) == 1, \
                    f"Expected 1 historical record, got {len(records)}"

                record = records[0]
                assert record[0] == case_id, "case_id should match"
                assert record[1] == 'sign_in_logs', "log_type should be sign_in_logs"
                assert record[2] == 'conditional_access_status', "field_name should be the selected field"
                assert record[3] == 1, "used_for_verification should be 1"
                assert record[4] in [0, 1], "verification_successful should be 0 or 1"
                assert record[5] in [0, 1], "breach_detected should be 0 or 1"
                assert record[6] is not None, "created_at should be set"

    def test_phase214_multiple_cases_learning_accumulation(self):
        """
        Test 5: Verify historical learning accumulates across cases.

        Expected behavior:
        - 3 separate case imports create 3 records
        - field_a_status has 2 records (used in 2 cases)
        - field_a_status AVG(verification_successful) calculated correctly
        - Historical data influences future recommendations
        """
        from claude.tools.m365_ir.field_reliability_scorer import (
            create_history_database,
            store_field_usage,
            recommend_best_field
        )

        # Create historical DB
        create_history_database(self.history_db_path)

        # Create 3 test databases
        case1_db = os.path.join(self.tmpdir, "PIR-CASE1-2025-01_logs.db")
        case2_db = os.path.join(self.tmpdir, "PIR-CASE2-2025-01_logs.db")
        case3_db = os.path.join(self.tmpdir, "PIR-CASE3-2025-01_logs.db")

        # Case 1: field_a_status (via conditional_access_status), successful, no breach
        self._create_test_sign_in_db(case1_db, (60, 40), (99, 1))

        # Store usage for case 1
        store_field_usage(
            self.history_db_path,
            "PIR-CASE1-2025-01",
            "test_logs",
            "conditional_access_status",
            0.7,
            True,
            True,  # Successful
            False,  # No breach
            "Case 1 test"
        )

        # Case 2: field_a_status (via conditional_access_status), successful, breach detected
        self._create_test_sign_in_db(case2_db, (60, 40), (99, 1))

        store_field_usage(
            self.history_db_path,
            "PIR-CASE2-2025-01",
            "test_logs",
            "conditional_access_status",
            0.7,
            True,
            True,  # Successful
            True,  # Breach detected
            "Case 2 test"
        )

        # Case 3: field_b_status (via result_status), successful, no breach
        self._create_test_sign_in_db(case3_db, (60, 40), (99, 1))

        store_field_usage(
            self.history_db_path,
            "PIR-CASE3-2025-01",
            "test_logs",
            "result_status",
            0.65,
            True,
            True,  # Successful
            False,  # No breach
            "Case 3 test"
        )

        # Query historical DB
        conn = sqlite3.connect(self.history_db_path)
        cursor = conn.cursor()

        all_records = cursor.execute("""
            SELECT case_id, field_name, verification_successful, breach_detected
            FROM field_reliability_history
            ORDER BY case_id
        """).fetchall()

        # Calculate AVG for conditional_access_status
        ca_avg = cursor.execute("""
            SELECT AVG(verification_successful)
            FROM field_reliability_history
            WHERE field_name = 'conditional_access_status' AND log_type = 'test_logs'
        """).fetchone()[0]

        conn.close()

        # Assert 3 records total
        assert len(all_records) == 3, \
            f"Expected 3 historical records, got {len(all_records)}"

        # Assert conditional_access_status has 2 records
        ca_records = [r for r in all_records if r[1] == 'conditional_access_status']
        assert len(ca_records) == 2, \
            "conditional_access_status should have 2 records"

        # Assert AVG(verification_successful) for conditional_access_status = 1.0
        assert ca_avg == 1.0, \
            f"conditional_access_status should have 100% success rate, got {ca_avg}"

        # Assert result_status has 1 record
        rs_records = [r for r in all_records if r[1] == 'result_status']
        assert len(rs_records) == 1, \
            "result_status should have 1 record"


# Mark all tests for Phase 2.1
pytestmark = pytest.mark.phase_2_1
