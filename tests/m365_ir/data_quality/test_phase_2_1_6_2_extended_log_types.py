"""
Phase 2.1.6.2: Extended Log Type Support - TDD Tests

Test Objective:
    Validate that Phase 2.1 intelligent field selection works across all M365 log types,
    not just sign_in_logs.

Key Features:
    1. Field selection for unified_audit_log
    2. Field selection for legacy_auth_logs
    3. Cross-log-type historical learning

Expected Behavior:
    - unified_audit_log: Auto-select best 'operation' or 'result_status' field
    - legacy_auth_logs: Auto-select best status field (e.g., 'status_code')
    - Historical DB: Store and retrieve field usage across different log types

Phase: PHASE_2_SMART_ANALYSIS (Phase 2.1.6.2 - Extended Log Type Support)
Status: In Progress (TDD Red Phase)
TDD Cycle: RED → GREEN → Refactor
"""

import pytest
import sqlite3
import tempfile
from pathlib import Path
from datetime import datetime


@pytest.mark.phase_2_1_6
class TestUnifiedAuditLogFieldSelection:
    """Test Phase 2.1 field selection for unified_audit_log."""

    def test_unified_audit_log_auto_field_selection(self):
        """
        Test that Phase 2.1 automatically selects best field for unified_audit_log.

        Given: unified_audit_log table with multiple candidate fields
        When: recommend_best_field() called with log_type='unified_audit_log'
        Then: Return best field based on multi-factor scoring

        TDD Phase: RED → GREEN
        Expected to FAIL until unified_audit_log support added to field_reliability_scorer.
        """
        from claude.tools.m365_ir.log_database import IRLogDatabase
        from claude.tools.m365_ir.field_reliability_scorer import recommend_best_field
        import tempfile

        tmpdir = tempfile.mkdtemp()

        try:
            # Create database with unified_audit_log table
            db = IRLogDatabase(case_id="TEST-UAL-FIELD-SELECTION", base_path=tmpdir)
            db.create()

            # Populate unified_audit_log with test data
            conn = sqlite3.connect(db.db_path)
            cursor = conn.cursor()

            # Insert test operations with mixed result statuses
            test_data = [
                ('MailItemsAccessed', 'Success', 'user1@test.com'),
                ('MailItemsAccessed', 'Success', 'user2@test.com'),
                ('FileAccessed', 'Success', 'user3@test.com'),
                ('FileDownloaded', 'Failed', 'user4@test.com'),
                ('UserLoggedIn', 'Success', 'user5@test.com'),
            ]

            for operation, result_status, user in test_data:
                cursor.execute("""
                    INSERT INTO unified_audit_log
                    (timestamp, user_id, operation, result_status, client_ip, raw_record, imported_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    datetime.now().isoformat(),
                    user,
                    operation,
                    result_status,
                    '203.0.113.1',
                    '{}',
                    datetime.now().isoformat()
                ))

            conn.commit()
            conn.close()

            # Test Phase 2.1 field selection
            recommendation = recommend_best_field(
                db_path=str(db.db_path),
                table='unified_audit_log',
                log_type='unified_audit_log'
            )

            # Validate recommendations
            assert recommendation.recommended_field == 'result_status', \
                "Should recommend result_status for unified_audit_log (contains 'result' and 'status' keywords)"
            assert recommendation.confidence in ['HIGH', 'MEDIUM', 'LOW'], \
                "Should return valid confidence level"
            assert recommendation.reasoning is not None, \
                "Should provide reasoning for field selection"

            # Validate scoring considers all dimensions
            assert len(recommendation.all_candidates) >= 1, \
                "Should discover at least one candidate field"

            # Validate at least one candidate has high uniformity
            uniformity_scores = [c.reliability_score.uniformity_score for c in recommendation.all_candidates]
            assert max(uniformity_scores) > 0.5, \
                "At least one field should have decent variety"

        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_preferred_fields_bonus_for_unified_audit_log(self):
        """
        Test that PREFERRED_FIELDS gives bonus to 'operation' and 'result_status'.

        Given: unified_audit_log with both operation and result_status populated
        When: recommend_best_field() called
        Then: Preferred fields get semantic preference bonus

        TDD Phase: RED → GREEN
        """
        from claude.tools.m365_ir.log_database import IRLogDatabase
        from claude.tools.m365_ir.field_reliability_scorer import (
            recommend_best_field,
            PREFERRED_FIELDS
        )
        import tempfile

        # Verify PREFERRED_FIELDS includes unified_audit_log
        assert 'unified_audit_log' in PREFERRED_FIELDS, \
            "PREFERRED_FIELDS should include unified_audit_log"
        assert 'operation' in PREFERRED_FIELDS['unified_audit_log'] or \
               'result_status' in PREFERRED_FIELDS['unified_audit_log'], \
            "unified_audit_log should prefer 'operation' or 'result_status'"

        tmpdir = tempfile.mkdtemp()

        try:
            db = IRLogDatabase(case_id="TEST-UAL-PREFERRED", base_path=tmpdir)
            db.create()

            # Populate with data where both operation and result_status have equal scores
            conn = sqlite3.connect(db.db_path)
            cursor = conn.cursor()

            for i in range(10):
                cursor.execute("""
                    INSERT INTO unified_audit_log
                    (timestamp, user_id, operation, result_status, client_ip, raw_record, imported_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    datetime.now().isoformat(),
                    f'user{i}@test.com',
                    f'Operation{i % 3}',  # 3 distinct operations
                    f'Status{i % 2}',     # 2 distinct statuses
                    '203.0.113.1',
                    '{}',
                    datetime.now().isoformat()
                ))

            conn.commit()
            conn.close()

            recommendation = recommend_best_field(
                db_path=str(db.db_path),
                table='unified_audit_log',
                log_type='unified_audit_log'
            )

            # Check that preferred field got bonus
            preferred_fields = PREFERRED_FIELDS.get('unified_audit_log', [])
            if preferred_fields:
                recommended_is_preferred = recommendation.recommended_field in preferred_fields

                # Find the recommended field's score
                recommended_score = next(
                    (c.reliability_score for c in recommendation.all_candidates
                     if c.field_name == recommendation.recommended_field),
                    None
                )

                if recommended_is_preferred and recommended_score:
                    assert recommended_score.semantic_preference > 0, \
                        "Preferred field should receive semantic preference bonus"

        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.mark.phase_2_1_6
class TestLegacyAuthFieldSelection:
    """Test Phase 2.1 field selection for legacy_auth_logs."""

    def test_legacy_auth_auto_field_selection(self):
        """
        Test that Phase 2.1 automatically selects best field for legacy_auth_logs.

        Given: legacy_auth_logs table with status_code field
        When: recommend_best_field() called with log_type='legacy_auth_logs'
        Then: Return best status field based on multi-factor scoring

        TDD Phase: RED → GREEN
        Expected to FAIL until legacy_auth_logs support added.
        """
        from claude.tools.m365_ir.log_database import IRLogDatabase
        from claude.tools.m365_ir.field_reliability_scorer import recommend_best_field
        import tempfile

        tmpdir = tempfile.mkdtemp()

        try:
            # Create database with legacy_auth_logs table
            db = IRLogDatabase(case_id="TEST-LEGACY-AUTH-FIELD", base_path=tmpdir)
            db.create()

            # Populate legacy_auth_logs with test data
            conn = sqlite3.connect(db.db_path)
            cursor = conn.cursor()

            # Insert test data with status variations
            for i in range(20):
                cursor.execute("""
                    INSERT INTO legacy_auth_logs
                    (timestamp, user_principal_name, client_app_used, ip_address, status, raw_record, imported_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    datetime.now().isoformat(),
                    f'user{i}@test.com',
                    'SMTP' if i % 2 == 0 else 'IMAP',
                    '203.0.113.1',
                    'Failure' if i % 3 == 0 else 'Success',  # Mix of success and failure
                    '{}',
                    datetime.now().isoformat()
                ))

            conn.commit()
            conn.close()

            # Test Phase 2.1 field selection
            recommendation = recommend_best_field(
                db_path=str(db.db_path),
                table='legacy_auth_logs',
                log_type='legacy_auth_logs'
            )

            # Validate recommendations
            assert recommendation.recommended_field == 'status', \
                "Should recommend status for legacy_auth_logs"
            assert recommendation.confidence in ['HIGH', 'MEDIUM', 'LOW'], \
                "Should return valid confidence level"

            # Validate multi-factor scoring
            recommended_score = next(
                (c.reliability_score for c in recommendation.all_candidates
                 if c.field_name == 'status'),
                None
            )

            assert recommended_score is not None, "Should find status in candidates"
            assert recommended_score.population_rate > 0.8, \
                "status should be well-populated"

        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.mark.phase_2_1_6
class TestCrossLogTypeLearning:
    """Test that historical learning works across different log types."""

    def test_historical_db_stores_different_log_types(self):
        """
        Test that historical DB can store field usage from multiple log types.

        Given: Field usage stored for sign_in_logs, unified_audit_log, legacy_auth_logs
        When: Query historical success rate
        Then: Returns correct rate grouped by log_type

        TDD Phase: RED → GREEN
        """
        from claude.tools.m365_ir.field_reliability_scorer import (
            create_history_database,
            store_field_usage,
            query_historical_success_rate
        )
        from pathlib import Path

        # Use temporary historical DB
        historical_db_path = Path(tempfile.mkdtemp()) / "test_historical.db"

        try:
            # Initialize historical database
            create_history_database(str(historical_db_path))

            # Store field usage for different log types
            test_cases = [
                # (log_type, field_name, verification_successful, breach_detected)
                ('sign_in_logs', 'conditional_access_status', True, True),
                ('sign_in_logs', 'conditional_access_status', True, False),
                ('unified_audit_log', 'operation', True, True),
                ('unified_audit_log', 'result_status', True, False),
                ('legacy_auth_logs', 'status', True, True),
                ('legacy_auth_logs', 'status', False, False),  # One failure
            ]

            for i, (log_type, field_name, verified, breach) in enumerate(test_cases):
                store_field_usage(
                    history_db_path=str(historical_db_path),
                    case_id=f'TEST-CASE-{i}',
                    log_type=log_type,
                    field_name=field_name,
                    reliability_score=0.75,
                    used_for_verification=True,
                    verification_successful=verified,
                    breach_detected=breach
                )

            # Query historical success rate for each log type + field combination
            sign_in_rate = query_historical_success_rate(
                log_type='sign_in_logs',
                field_name='conditional_access_status',
                historical_db_path=str(historical_db_path)
            )

            unified_audit_operation_rate = query_historical_success_rate(
                log_type='unified_audit_log',
                field_name='operation',
                historical_db_path=str(historical_db_path)
            )

            legacy_auth_rate = query_historical_success_rate(
                log_type='legacy_auth_logs',
                field_name='status',
                historical_db_path=str(historical_db_path)
            )

            # Validate results
            assert sign_in_rate == 1.0, \
                "sign_in_logs conditional_access_status should have 100% success (2/2)"
            assert unified_audit_operation_rate == 1.0, \
                "unified_audit_log operation should have 100% success (1/1)"
            assert legacy_auth_rate == 0.5, \
                "legacy_auth_logs status should have 50% success (1/2)"

        finally:
            import shutil
            shutil.rmtree(historical_db_path.parent, ignore_errors=True)

    def test_cross_log_type_learning_influences_scoring(self):
        """
        Test that historical learning from one log type doesn't affect scoring for another.

        Given: High success rate for 'conditional_access_status' in sign_in_logs
        When: Scoring a field with same name in unified_audit_log
        Then: Historical rate should be log_type-specific (not global)

        TDD Phase: RED → GREEN
        """
        from claude.tools.m365_ir.field_reliability_scorer import (
            create_history_database,
            store_field_usage,
            query_historical_success_rate
        )
        from pathlib import Path

        historical_db_path = Path(tempfile.mkdtemp()) / "test_cross_type.db"

        try:
            # Initialize historical database
            create_history_database(str(historical_db_path))

            # Store successful usage for sign_in_logs
            for i in range(5):
                store_field_usage(
                    history_db_path=str(historical_db_path),
                    case_id=f'SIGN-IN-{i}',
                    log_type='sign_in_logs',
                    field_name='conditional_access_status',
                    reliability_score=0.8,
                    used_for_verification=True,
                    verification_successful=True,
                    breach_detected=True
                )

            # Store failed usage for unified_audit_log (hypothetical field collision)
            store_field_usage(
                history_db_path=str(historical_db_path),
                case_id='UAL-FAIL',
                log_type='unified_audit_log',
                field_name='conditional_access_status',  # Same name, different log type
                reliability_score=0.3,
                used_for_verification=True,
                verification_successful=False,
                breach_detected=False
            )

            # Query should be log_type-specific
            sign_in_rate = query_historical_success_rate(
                log_type='sign_in_logs',
                field_name='conditional_access_status',
                historical_db_path=str(historical_db_path)
            )

            ual_rate = query_historical_success_rate(
                log_type='unified_audit_log',
                field_name='conditional_access_status',
                historical_db_path=str(historical_db_path)
            )

            # Validate isolation
            assert sign_in_rate == 1.0, \
                "sign_in_logs should have 100% success (5/5)"
            assert ual_rate == 0.0, \
                "unified_audit_log should have 0% success (0/1)"

        finally:
            import shutil
            shutil.rmtree(historical_db_path.parent, ignore_errors=True)


# Mark all tests as Phase 2.1.6
pytestmark = pytest.mark.phase_2_1_6
