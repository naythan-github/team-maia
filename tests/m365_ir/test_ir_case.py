#!/usr/bin/env python3
"""
Tests for IRCase workflow management.

TDD: Tests written first for case folder structure, zip handling, and date extraction.

Requirements:
1. Move zip files to project folder/source-files/
2. Case ID includes date from zip file mtime: PIR-{CUSTOMER}-{YYYY-MM-DD}
3. Reports output to /reports subdirectory
"""

import shutil
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from claude.tools.m365_ir.ir_case import IRCase


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test cases."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_zip(temp_dir) -> Path:
    """Create a sample zip file with known mtime."""
    zip_path = temp_dir / "downloads" / "Export_2025-12-15.zip"
    zip_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, 'w') as zf:
        zf.writestr("1_SignInLogs.csv", "CreatedDateTime,UserPrincipalName\n15/12/2025,test@example.com")

    # Set specific mtime: 2025-12-15 10:30:00
    import os
    mtime = datetime(2025, 12, 15, 10, 30, 0).timestamp()
    os.utime(zip_path, (mtime, mtime))

    return zip_path


class TestCaseIdGeneration:
    """Test case ID generation from zip file."""

    def test_case_id_uses_zip_mtime(self, temp_dir, sample_zip):
        """Case ID should use zip file modification date."""
        case = IRCase.from_zip(
            zip_path=sample_zip,
            customer="FYNA",
            base_path=temp_dir / "ir-cases"
        )

        # Zip mtime is 2025-12-15
        assert case.case_id == "PIR-FYNA-2025-12-15"

    def test_case_id_is_zero_padded(self, temp_dir):
        """Date should be zero-padded (01 not 1)."""
        zip_path = temp_dir / "test.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("dummy.csv", "data")

        # Set mtime to 2025-01-05 (single digit month and day)
        import os
        mtime = datetime(2025, 1, 5, 10, 0, 0).timestamp()
        os.utime(zip_path, (mtime, mtime))

        case = IRCase.from_zip(
            zip_path=zip_path,
            customer="ACME",
            base_path=temp_dir / "ir-cases"
        )

        assert case.case_id == "PIR-ACME-2025-01-05"

    def test_customer_name_uppercased(self, temp_dir, sample_zip):
        """Customer name should be uppercased in case ID."""
        case = IRCase.from_zip(
            zip_path=sample_zip,
            customer="fyna foods",
            base_path=temp_dir / "ir-cases"
        )

        assert "FYNA-FOODS" in case.case_id

    def test_customer_name_sanitized(self, temp_dir, sample_zip):
        """Customer name should be sanitized for filesystem."""
        case = IRCase.from_zip(
            zip_path=sample_zip,
            customer="Acme Corp.",
            base_path=temp_dir / "ir-cases"
        )

        # Should replace spaces/special chars with hyphens
        assert "ACME-CORP" in case.case_id
        assert "." not in case.case_id


class TestDirectoryStructure:
    """Test case directory structure creation."""

    def test_creates_case_directory(self, temp_dir, sample_zip):
        """Should create case directory."""
        case = IRCase.from_zip(
            zip_path=sample_zip,
            customer="FYNA",
            base_path=temp_dir / "ir-cases"
        )
        case.initialize()

        assert case.case_dir.exists()
        assert case.case_dir.is_dir()

    def test_creates_source_files_directory(self, temp_dir, sample_zip):
        """Should create source-files subdirectory."""
        case = IRCase.from_zip(
            zip_path=sample_zip,
            customer="FYNA",
            base_path=temp_dir / "ir-cases"
        )
        case.initialize()

        assert case.source_files_dir.exists()
        assert case.source_files_dir.name == "source-files"

    def test_creates_reports_directory(self, temp_dir, sample_zip):
        """Should create reports subdirectory."""
        case = IRCase.from_zip(
            zip_path=sample_zip,
            customer="FYNA",
            base_path=temp_dir / "ir-cases"
        )
        case.initialize()

        assert case.reports_dir.exists()
        assert case.reports_dir.name == "reports"

    def test_full_directory_structure(self, temp_dir, sample_zip):
        """Should create complete directory structure."""
        case = IRCase.from_zip(
            zip_path=sample_zip,
            customer="FYNA",
            base_path=temp_dir / "ir-cases"
        )
        case.initialize()

        expected_structure = {
            case.case_dir,
            case.source_files_dir,
            case.reports_dir,
        }

        for path in expected_structure:
            assert path.exists(), f"Missing: {path}"


class TestZipFileHandling:
    """Test zip file move operations."""

    def test_moves_zip_to_source_files(self, temp_dir, sample_zip):
        """Should move zip file to source-files directory."""
        original_path = sample_zip

        case = IRCase.from_zip(
            zip_path=sample_zip,
            customer="FYNA",
            base_path=temp_dir / "ir-cases"
        )
        case.initialize()
        moved_path = case.move_source_zip()

        # Original should not exist
        assert not original_path.exists()

        # New location should exist
        assert moved_path.exists()
        assert moved_path.parent == case.source_files_dir

    def test_preserves_zip_filename(self, temp_dir, sample_zip):
        """Should preserve original zip filename when moving."""
        original_name = sample_zip.name

        case = IRCase.from_zip(
            zip_path=sample_zip,
            customer="FYNA",
            base_path=temp_dir / "ir-cases"
        )
        case.initialize()
        moved_path = case.move_source_zip()

        assert moved_path.name == original_name

    def test_handles_duplicate_zip_names(self, temp_dir, sample_zip):
        """Should handle case where zip with same name already exists."""
        case = IRCase.from_zip(
            zip_path=sample_zip,
            customer="FYNA",
            base_path=temp_dir / "ir-cases"
        )
        case.initialize()

        # Move first zip
        first_moved = case.move_source_zip()

        # Create another zip with same name
        new_zip = temp_dir / "downloads" / sample_zip.name
        new_zip.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(new_zip, 'w') as zf:
            zf.writestr("1_SignInLogs.csv", "different,data")

        # Move second zip - should rename to avoid conflict
        case2 = IRCase(case_id=case.case_id, base_path=temp_dir / "ir-cases")
        second_moved = case2.add_source_file(new_zip)

        assert first_moved.exists()
        assert second_moved.exists()
        assert first_moved != second_moved


class TestDatabaseIntegration:
    """Test integration with IRLogDatabase."""

    def test_database_in_case_directory(self, temp_dir, sample_zip):
        """Database should be created in case directory."""
        case = IRCase.from_zip(
            zip_path=sample_zip,
            customer="FYNA",
            base_path=temp_dir / "ir-cases"
        )
        case.initialize()

        # Database should be in case dir, not a subdirectory
        assert case.db_path.parent == case.case_dir
        assert case.db_path.name == f"{case.case_id}_logs.db"

    def test_get_database_returns_configured_db(self, temp_dir, sample_zip):
        """get_database() should return properly configured IRLogDatabase."""
        case = IRCase.from_zip(
            zip_path=sample_zip,
            customer="FYNA",
            base_path=temp_dir / "ir-cases"
        )
        case.initialize()

        db = case.get_database()
        db.create()

        assert db.db_path.exists()
        assert db.db_path == case.db_path


class TestExistingCaseHandling:
    """Test handling of existing cases."""

    def test_open_existing_case(self, temp_dir, sample_zip):
        """Should be able to open existing case by ID."""
        # Create case
        case1 = IRCase.from_zip(
            zip_path=sample_zip,
            customer="FYNA",
            base_path=temp_dir / "ir-cases"
        )
        case1.initialize()
        case_id = case1.case_id

        # Open same case
        case2 = IRCase(case_id=case_id, base_path=temp_dir / "ir-cases")

        assert case2.case_dir.exists()
        assert case2.case_id == case_id

    def test_add_additional_zip_to_existing_case(self, temp_dir, sample_zip):
        """Should be able to add more zip files to existing case."""
        case = IRCase.from_zip(
            zip_path=sample_zip,
            customer="FYNA",
            base_path=temp_dir / "ir-cases"
        )
        case.initialize()
        case.move_source_zip()

        # Create another zip
        new_zip = temp_dir / "downloads" / "Export_2025-12-20.zip"
        new_zip.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(new_zip, 'w') as zf:
            zf.writestr("1_SignInLogs.csv", "more,data")

        # Add to existing case
        moved = case.add_source_file(new_zip)

        assert moved.exists()
        assert moved.parent == case.source_files_dir
        assert len(list(case.source_files_dir.glob("*.zip"))) == 2


class TestReportsDirectory:
    """Test reports directory functionality."""

    def test_reports_path_property(self, temp_dir, sample_zip):
        """Should provide reports directory path."""
        case = IRCase.from_zip(
            zip_path=sample_zip,
            customer="FYNA",
            base_path=temp_dir / "ir-cases"
        )
        case.initialize()

        expected = case.case_dir / "reports"
        assert case.reports_dir == expected

    def test_can_write_to_reports_dir(self, temp_dir, sample_zip):
        """Should be able to write files to reports directory."""
        case = IRCase.from_zip(
            zip_path=sample_zip,
            customer="FYNA",
            base_path=temp_dir / "ir-cases"
        )
        case.initialize()

        report_file = case.reports_dir / "analysis_summary.json"
        report_file.write_text('{"status": "complete"}')

        assert report_file.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
