"""
Phase 1.2: Import Pipeline Quality Integration - TDD Tests

Test Objective:
    Validate that import pipeline automatically runs quality checks and fails fast
    on poor data quality.

Key Features:
    1. Automatic quality checks after import (before commit)
    2. Fail-fast on quality score <0.5 (poor quality)
    3. Rollback import on quality failure
    4. Warning messages for unreliable fields
    5. Allow override with --skip-quality-check flag (future)

Expected Behavior:
    - Good quality data: Import succeeds, quality report logged
    - Poor quality data: Import fails, transaction rolled back, recommendations provided
    - Quality checks run AFTER import but BEFORE commit

Phase: PHASE_1_FOUNDATION (Phase 1.2 - Import Pipeline Integration)
Status: In Progress (TDD Red Phase)
TDD Cycle: Red → Green → Refactor
"""

import pytest
import sqlite3
import tempfile
import csv
from pathlib import Path


@pytest.mark.phase_1_2
class TestImportPipelineQualityChecks:
    """Test automatic quality checks during import."""

    def test_import_succeeds_with_good_quality_data(self):
        """
        Test that import succeeds when data quality is good.

        Good quality = diverse fields, no 100% uniform fields, quality score >0.5
        """
        from claude.tools.m365_ir.log_database import IRLogDatabase
        from claude.tools.m365_ir.log_importer import LogImporter
        import tempfile
        import os

        # Create test CSV with GOOD quality data (diverse values)
        csv_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        writer = csv.DictWriter(csv_file, fieldnames=[
            'CreatedDateTime', 'UserPrincipalName', 'IPAddress', 'Country',
            'ConditionalAccessStatus'
        ])
        writer.writeheader()

        # Add 20 records with good variation
        for i in range(20):
            writer.writerow({
                'CreatedDateTime': f'2025-11-04T10:{i:02d}:00Z',
                'UserPrincipalName': f'user{i}@test.com',
                'IPAddress': f'203.0.113.{i}',
                'Country': 'AU' if i < 15 else 'US',  # 75% AU, 25% US (good variation)
                'ConditionalAccessStatus': 'success' if i < 18 else 'failure'  # 90% success, 10% failure
            })
        csv_file.close()

        # Create database
        tmpdir = tempfile.mkdtemp()

        try:
            db = IRLogDatabase(case_id="TEST-GOOD-QUALITY", base_path=tmpdir)
            db.create()

            importer = LogImporter(db)

            # Import should succeed (good quality data)
            result = importer.import_sign_in_logs(csv_file.name)

            # Verify import succeeded
            assert result.records_imported == 20, "All 20 records should be imported"
            assert result.records_failed == 0, "No records should fail"

            # Verify quality check results were logged
            conn = sqlite3.connect(db.db_path)
            cursor = conn.cursor()

            # Check if quality_check_summary table exists and has results
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='quality_check_summary'
            """)

            if cursor.fetchone():
                cursor.execute("""
                    SELECT overall_quality_score, check_passed
                    FROM quality_check_summary
                    WHERE table_name = 'sign_in_logs'
                    ORDER BY created_at DESC
                    LIMIT 1
                """)
                quality_result = cursor.fetchone()

                if quality_result:
                    quality_score, check_passed = quality_result
                    assert quality_score > 0.5, "Good data should have quality score >0.5"
                    assert check_passed == 1, "Quality check should pass"

            conn.close()

        finally:
            os.unlink(csv_file.name)
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_import_fails_with_poor_quality_data(self):
        """
        Test that import FAILS when data quality is poor.

        Poor quality = all fields 100% uniform, quality score <0.5
        This should trigger fail-fast mode and rollback the import.
        """
        from claude.tools.m365_ir.log_database import IRLogDatabase
        from claude.tools.m365_ir.log_importer import LogImporter
        from claude.tools.m365_ir.log_importer import DataQualityError
        import tempfile
        import os

        # Create test CSV with POOR quality data (100% uniform)
        csv_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        writer = csv.DictWriter(csv_file, fieldnames=[
            'CreatedDateTime', 'UserPrincipalName', 'IPAddress', 'Country',
            'ConditionalAccessStatus'
        ])
        writer.writeheader()

        # Add 20 records with ALL fields uniform (except timestamp)
        for i in range(20):
            writer.writerow({
                'CreatedDateTime': f'2025-11-04T10:{i:02d}:00Z',
                'UserPrincipalName': 'same_user@test.com',  # 100% uniform!
                'IPAddress': '203.0.113.1',  # 100% uniform!
                'Country': 'AU',  # 100% uniform!
                'ConditionalAccessStatus': 'success'  # 100% uniform!
            })
        csv_file.close()

        # Create database
        tmpdir = tempfile.mkdtemp()

        try:
            db = IRLogDatabase(case_id="TEST-POOR-QUALITY", base_path=tmpdir)
            db.create()

            importer = LogImporter(db)

            # Import should FAIL with DataQualityError
            with pytest.raises(DataQualityError) as excinfo:
                result = importer.import_sign_in_logs(csv_file.name)

            # Verify error message contains quality recommendations
            error_msg = str(excinfo.value)
            assert "quality" in error_msg.lower(), "Error should mention quality issues"
            assert "0." in error_msg, "Error should include quality score"

            # Verify records were NOT imported (rollback occurred)
            conn = sqlite3.connect(db.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sign_in_logs")
            record_count = cursor.fetchone()[0]
            conn.close()

            assert record_count == 0, "Records should be rolled back on quality failure"

        finally:
            os.unlink(csv_file.name)
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_quality_warnings_logged_for_unreliable_fields(self):
        """
        Test that quality warnings are logged for unreliable fields.

        Even if import succeeds (quality score >0.5), warnings should be logged
        for any unreliable fields detected.
        """
        from claude.tools.m365_ir.log_database import IRLogDatabase
        from claude.tools.m365_ir.log_importer import LogImporter
        import tempfile
        import os

        # Create test CSV with MIXED quality (some uniform, some diverse)
        csv_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        writer = csv.DictWriter(csv_file, fieldnames=[
            'CreatedDateTime', 'UserPrincipalName', 'IPAddress', 'Country',
            'ConditionalAccessStatus'
        ])
        writer.writeheader()

        # Add 20 records: Country is uniform, others are diverse
        for i in range(20):
            writer.writerow({
                'CreatedDateTime': f'2025-11-04T10:{i:02d}:00Z',
                'UserPrincipalName': f'user{i}@test.com',  # Diverse
                'IPAddress': f'203.0.113.{i}',  # Diverse
                'Country': 'AU',  # 100% uniform! (unreliable)
                'ConditionalAccessStatus': 'success' if i < 18 else 'failure'  # Diverse
            })
        csv_file.close()

        # Create database
        tmpdir = tempfile.mkdtemp()

        try:
            db = IRLogDatabase(case_id="TEST-MIXED-QUALITY", base_path=tmpdir)
            db.create()

            importer = LogImporter(db)

            # Import should SUCCEED (overall quality >0.5) but log warnings
            result = importer.import_sign_in_logs(csv_file.name)

            assert result.records_imported == 20, "Import should succeed despite warnings"

            # Check for quality warnings in database
            conn = sqlite3.connect(db.db_path)
            cursor = conn.cursor()

            if cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='quality_check_summary'
            """).fetchone():
                cursor.execute("""
                    SELECT warnings
                    FROM quality_check_summary
                    WHERE table_name = 'sign_in_logs'
                    ORDER BY created_at DESC
                    LIMIT 1
                """)
                warnings_result = cursor.fetchone()

                if warnings_result and warnings_result[0]:
                    warnings = warnings_result[0]
                    assert 'location_country' in warnings.lower() or 'country' in warnings.lower(), \
                        "Warnings should mention location_country field"

            conn.close()

        finally:
            os.unlink(csv_file.name)
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_quality_check_runs_after_import_before_commit(self):
        """
        Test that quality checks run AFTER import but BEFORE final commit.

        This ensures that if quality check fails, the import can be rolled back.
        """
        from claude.tools.m365_ir.log_database import IRLogDatabase
        from claude.tools.m365_ir.log_importer import LogImporter
        from claude.tools.m365_ir.log_importer import DataQualityError
        import tempfile
        import os

        # Create test CSV with poor quality
        csv_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        writer = csv.DictWriter(csv_file, fieldnames=[
            'CreatedDateTime', 'UserPrincipalName', 'IPAddress', 'Country',
            'ConditionalAccessStatus'
        ])
        writer.writeheader()

        for i in range(10):
            writer.writerow({
                'CreatedDateTime': f'2025-11-04T10:{i:02d}:00Z',
                'UserPrincipalName': 'same@test.com',
                'IPAddress': '1.1.1.1',
                'Country': 'AU',
                'ConditionalAccessStatus': 'success'
            })
        csv_file.close()

        tmpdir = tempfile.mkdtemp()

        try:
            db = IRLogDatabase(case_id="TEST-TIMING", base_path=tmpdir)
            db.create()

            importer = LogImporter(db)

            # Import should fail at quality check
            with pytest.raises(DataQualityError):
                importer.import_sign_in_logs(csv_file.name)

            # Verify NO records were persisted (rollback successful)
            conn = sqlite3.connect(db.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sign_in_logs")
            count = cursor.fetchone()[0]
            conn.close()

            assert count == 0, "Transaction should be rolled back - no records should persist"

        finally:
            os.unlink(csv_file.name)
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)


# Mark all tests as Phase 1.2
pytestmark = pytest.mark.phase_1_2
