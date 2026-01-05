#!/usr/bin/env python3
"""
Tests for zip import functionality in LogImporter.

TDD: Tests written first, implementation follows.

Phase 226.1 - Direct zip import without manual extraction.
"""

import csv
import io
import tempfile
import zipfile
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from claude.tools.m365_ir.log_database import IRLogDatabase
from claude.tools.m365_ir.log_importer import LogImporter


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test databases."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_signin_csv() -> str:
    """Generate sample sign-in log CSV content."""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        'CreatedDateTime', 'UserPrincipalName', 'UserDisplayName',
        'IPAddress', 'City', 'Country', 'ClientAppUsed', 'AppDisplayName',
        'Browser', 'OS', 'Status', 'ConditionalAccessStatus',
        'RiskLevelDuringSignIn', 'RiskState', 'CorrelationId'
    ])
    writer.writeheader()
    writer.writerow({
        'CreatedDateTime': '15/12/2025 9:30:00 AM',
        'UserPrincipalName': 'user@example.com',
        'UserDisplayName': 'Test User',
        'IPAddress': '203.0.113.50',
        'City': 'Sydney',
        'Country': 'AU',
        'ClientAppUsed': 'Browser',
        'AppDisplayName': 'Office 365',
        'Browser': 'Chrome',
        'OS': 'Windows',
        'Status': 'Success',
        'ConditionalAccessStatus': 'success',
        'RiskLevelDuringSignIn': 'none',
        'RiskState': 'none',
        'CorrelationId': 'abc-123'
    })
    writer.writerow({
        'CreatedDateTime': '15/12/2025 10:00:00 AM',
        'UserPrincipalName': 'admin@example.com',
        'UserDisplayName': 'Admin User',
        'IPAddress': '185.234.100.50',
        'City': 'Moscow',
        'Country': 'RU',
        'ClientAppUsed': 'Browser',
        'AppDisplayName': 'Azure Portal',
        'Browser': 'Firefox',
        'OS': 'Linux',
        'Status': 'Success',
        'ConditionalAccessStatus': 'success',
        'RiskLevelDuringSignIn': 'high',
        'RiskState': 'atRisk',
        'CorrelationId': 'def-456'
    })
    return output.getvalue()


@pytest.fixture
def sample_ual_csv() -> str:
    """Generate sample Unified Audit Log CSV content."""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        'CreationDate', 'UserIds', 'Operations', 'Workload',
        'RecordType', 'ResultStatus', 'ClientIP', 'ObjectId', 'AuditData'
    ])
    writer.writeheader()
    writer.writerow({
        'CreationDate': '15/12/2025 11:00:00 AM',
        'UserIds': 'admin@example.com',
        'Operations': 'Add member to role.',
        'Workload': 'AzureActiveDirectory',
        'RecordType': '8',
        'ResultStatus': 'Success',
        'ClientIP': '185.234.100.50',
        'ObjectId': 'Global Administrator',
        'AuditData': '{}'
    })
    return output.getvalue()


class TestZipImportDetection:
    """Test auto-detection of zip vs directory."""

    def test_import_all_accepts_zip_file(self, temp_dir, sample_signin_csv):
        """import_all() should accept a zip file path and import CSVs from it."""
        # Create zip with sign-in logs (filename must match pattern: 1_.*SignInLogs\.csv)
        zip_path = temp_dir / "export.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("1_SignInLogs.csv", sample_signin_csv)

        # Create database and importer
        db = IRLogDatabase(case_id="PIR-TEST-ZIP-001", base_path=str(temp_dir))
        db.create()
        importer = LogImporter(db)

        # Import from zip
        results = importer.import_all(zip_path)

        # Verify import succeeded
        assert 'sign_in' in results
        assert results['sign_in'].records_imported == 2
        assert results['sign_in'].records_failed == 0

    def test_import_all_still_works_with_directory(self, temp_dir, sample_signin_csv):
        """import_all() should still work with extracted directories (backwards compat)."""
        # Create extracted directory with CSV (filename must match pattern)
        export_dir = temp_dir / "exports"
        export_dir.mkdir()
        (export_dir / "1_SignInLogs.csv").write_text(sample_signin_csv)

        # Create database and importer
        db = IRLogDatabase(case_id="PIR-TEST-DIR-001", base_path=str(temp_dir))
        db.create()
        importer = LogImporter(db)

        # Import from directory
        results = importer.import_all(export_dir)

        # Verify import succeeded
        assert 'sign_in' in results
        assert results['sign_in'].records_imported == 2

    def test_import_all_auto_detects_source_type(self, temp_dir, sample_signin_csv):
        """import_all() should auto-detect whether source is zip or directory."""
        # Create both a zip and a directory
        zip_path = temp_dir / "export.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("1_SignInLogs.csv", sample_signin_csv)

        dir_path = temp_dir / "export_dir"
        dir_path.mkdir()
        (dir_path / "1_SignInLogs.csv").write_text(sample_signin_csv)

        # Import from zip
        db1 = IRLogDatabase(case_id="PIR-AUTO-ZIP", base_path=str(temp_dir))
        db1.create()
        importer1 = LogImporter(db1)
        results1 = importer1.import_all(zip_path)

        # Import from directory
        db2 = IRLogDatabase(case_id="PIR-AUTO-DIR", base_path=str(temp_dir))
        db2.create()
        importer2 = LogImporter(db2)
        results2 = importer2.import_all(dir_path)

        # Both should succeed with same record count
        assert results1['sign_in'].records_imported == results2['sign_in'].records_imported == 2


class TestZipImportContent:
    """Test importing various log types from zip."""

    def test_import_multiple_log_types_from_zip(self, temp_dir, sample_signin_csv, sample_ual_csv):
        """Should import multiple log types from single zip."""
        zip_path = temp_dir / "full_export.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("1_SignInLogs.csv", sample_signin_csv)
            zf.writestr("7_FullAuditLog.csv", sample_ual_csv)

        db = IRLogDatabase(case_id="PIR-MULTI-001", base_path=str(temp_dir))
        db.create()
        importer = LogImporter(db)

        results = importer.import_all(zip_path)

        assert 'sign_in' in results
        assert 'ual' in results
        assert results['sign_in'].records_imported == 2
        assert results['ual'].records_imported == 1

    def test_import_csvs_in_subdirectory(self, temp_dir, sample_signin_csv):
        """Should find and import CSVs nested in subdirectories within zip."""
        zip_path = temp_dir / "nested.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            # CSV in subdirectory (common in M365 exports)
            zf.writestr("Export_2025-01-05/1_SignInLogs.csv", sample_signin_csv)

        db = IRLogDatabase(case_id="PIR-NESTED-001", base_path=str(temp_dir))
        db.create()
        importer = LogImporter(db)

        results = importer.import_all(zip_path)

        assert 'sign_in' in results
        assert results['sign_in'].records_imported == 2

    def test_import_handles_empty_zip(self, temp_dir):
        """Should handle zip with no CSV files gracefully."""
        zip_path = temp_dir / "empty.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("readme.txt", "No CSVs here")

        db = IRLogDatabase(case_id="PIR-EMPTY-001", base_path=str(temp_dir))
        db.create()
        importer = LogImporter(db)

        results = importer.import_all(zip_path)

        # Should return empty dict, not error
        assert results == {}


class TestZipImportEdgeCases:
    """Test edge cases and error handling."""

    def test_import_invalid_zip_raises_error(self, temp_dir):
        """Should raise appropriate error for invalid zip file."""
        invalid_path = temp_dir / "not_a_zip.zip"
        invalid_path.write_text("This is not a zip file")

        db = IRLogDatabase(case_id="PIR-INVALID-001", base_path=str(temp_dir))
        db.create()
        importer = LogImporter(db)

        with pytest.raises(zipfile.BadZipFile):
            importer.import_all(invalid_path)

    def test_import_nonexistent_path_raises_error(self, temp_dir):
        """Should raise FileNotFoundError for nonexistent path."""
        db = IRLogDatabase(case_id="PIR-NOEXIST-001", base_path=str(temp_dir))
        db.create()
        importer = LogImporter(db)

        with pytest.raises(FileNotFoundError):
            importer.import_all(temp_dir / "does_not_exist.zip")

    def test_import_zip_deduplication_works(self, temp_dir, sample_signin_csv):
        """Importing same zip twice should skip duplicates."""
        zip_path = temp_dir / "export.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("1_SignInLogs.csv", sample_signin_csv)

        db = IRLogDatabase(case_id="PIR-DEDUP-001", base_path=str(temp_dir))
        db.create()
        importer = LogImporter(db)

        # First import
        results1 = importer.import_all(zip_path)
        assert results1['sign_in'].records_imported == 2

        # Second import - should skip (already imported based on hash)
        results2 = importer.import_all(zip_path)
        assert results2['sign_in'].records_imported == 0

    def test_source_file_in_result_shows_zip_path(self, temp_dir, sample_signin_csv):
        """ImportResult.source_file should reference the zip, not extracted path."""
        zip_path = temp_dir / "export.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("1_SignInLogs.csv", sample_signin_csv)

        db = IRLogDatabase(case_id="PIR-SOURCE-001", base_path=str(temp_dir))
        db.create()
        importer = LogImporter(db)

        results = importer.import_all(zip_path)

        # Source should reference the zip file
        assert "export.zip" in results['sign_in'].source_file


class TestZipImportPerformance:
    """Test that zip import streams without full extraction."""

    def test_no_temp_files_created(self, temp_dir, sample_signin_csv):
        """Import should stream from zip without creating temp files."""
        zip_path = temp_dir / "export.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("1_SignInLogs.csv", sample_signin_csv)

        db = IRLogDatabase(case_id="PIR-NOTEMP-001", base_path=str(temp_dir))
        db.create()
        importer = LogImporter(db)

        # Count files before
        files_before = set(temp_dir.rglob("*"))

        results = importer.import_all(zip_path)

        # Count files after (should only add database files, not extracted CSVs)
        files_after = set(temp_dir.rglob("*"))
        new_files = files_after - files_before

        # New files should only be database-related, not extracted CSVs
        csv_files = [f for f in new_files if f.suffix == '.csv']
        assert len(csv_files) == 0, f"Unexpected CSV files created: {csv_files}"
        assert results['sign_in'].records_imported == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
