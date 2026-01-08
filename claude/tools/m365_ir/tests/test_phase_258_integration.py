#!/usr/bin/env python3
"""
Integration Tests for Phase 258 Data Quality Features

Verifies that the full import flow triggers:
1. Log coverage summary population
2. PowerShell validation checks
3. Auth status view creation

These tests verify END-TO-END behavior, not unit functionality.

Run: pytest claude/tools/m365_ir/tests/test_phase_258_integration.py -v

Author: Maia System (SRE Principal Engineer Agent)
Created: 2026-01-08 (PIR-FYNA-2025-12-08 lessons learned)
"""

import csv
import io
import pytest
import sqlite3
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add Maia root to path
MAIA_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

from claude.tools.m365_ir.log_database import IRLogDatabase
from claude.tools.m365_ir.log_importer import LogImporter


class TestPhase258Integration:
    """Integration tests for Phase 258 post-import validation."""

    @pytest.fixture
    def temp_db(self, tmp_path):
        """Create temporary database with schema."""
        db = IRLogDatabase(case_id="TEST-INTEGRATION", base_path=str(tmp_path))
        db.create()
        return db

    @pytest.fixture
    def sample_signin_csv(self, tmp_path):
        """Create a sample sign-in CSV with good data spanning 90 days."""
        csv_path = tmp_path / "01_AllUsers_SignInLogs.csv"

        # Create 100 records over 90 days with varied data to pass quality checks
        rows = []
        base_date = datetime.now() - timedelta(days=90)

        cities = ['Sydney', 'Melbourne', 'Brisbane', 'Perth', 'Adelaide']
        browsers = ['Chrome', 'Edge', 'Firefox', 'Safari']
        os_list = ['Windows 10', 'Windows 11', 'macOS', 'iOS']
        apps = ['Microsoft Office', 'Outlook', 'Teams', 'OneDrive', 'SharePoint']
        ca_statuses = ['success', 'success', 'success', 'notApplied', 'notApplied']  # Mix

        for i in range(100):
            ts = base_date + timedelta(days=i * 0.9)
            rows.append({
                'CreatedDateTime': ts.strftime('%Y-%m-%dT%H:%M:%S'),
                'UserPrincipalName': f'user{i % 10}@test.com',  # 10 different users
                'UserDisplayName': f'User {i % 10}',
                'AppDisplayName': apps[i % len(apps)],
                'IPAddress': f'{10 + (i % 5)}.{20 + (i % 10)}.{30 + (i % 20)}.{i % 256}',
                'City': cities[i % len(cities)],
                'Country': 'AU',
                'Browser': browsers[i % len(browsers)],
                'OS': os_list[i % len(os_list)],
                'ClientAppUsed': 'Browser' if i % 3 != 0 else 'Mobile Apps and Desktop clients',
                'Status': 'Success',
                'RiskState': 'none' if i % 5 != 0 else 'atRisk',  # Some variation
                'RiskLevelDuringSignIn': 'none' if i % 10 != 0 else 'low',
                'ConditionalAccessStatus': ca_statuses[i % len(ca_statuses)],
                'CorrelationId': f'corr-{i:05d}',
            })

        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

        return csv_path

    @pytest.fixture
    def corrupted_signin_csv(self, tmp_path):
        """Create a sign-in CSV with PowerShell .NET object corruption."""
        csv_path = tmp_path / "01_AllUsers_SignInLogs.csv"

        rows = [{
            'CreatedDateTime': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
            'UserPrincipalName': 'test@example.com',
            'UserDisplayName': 'Test User',
            'AppDisplayName': 'Office',
            'IPAddress': '1.2.3.4',
            'City': 'Sydney',
            'Country': 'AU',
            'Browser': 'Chrome',
            'OS': 'Windows10',
            'ClientAppUsed': 'Browser',
            # PowerShell .NET object corruption - this is the bug we're detecting
            'Status': 'Microsoft.Graph.PowerShell.Models.MicrosoftGraphSignInStatus',
            'RiskState': 'none',
            'RiskLevelDuringSignIn': 'none',
            'ConditionalAccessStatus': 'success',
            'CorrelationId': 'corr-1',
        }]

        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

        return csv_path

    @pytest.fixture
    def gap_signin_csv(self, tmp_path):
        """Create a sign-in CSV with only 30 days of coverage (gap detected)."""
        csv_path = tmp_path / "01_AllUsers_SignInLogs.csv"

        # Only 30 days of coverage - should trigger gap detection
        # More varied data to pass quality checks
        rows = []
        base_date = datetime.now() - timedelta(days=30)

        cities = ['Sydney', 'Melbourne', 'Brisbane', 'Perth', 'Adelaide']
        browsers = ['Chrome', 'Edge', 'Firefox', 'Safari']
        os_list = ['Windows 10', 'Windows 11', 'macOS', 'iOS']
        apps = ['Microsoft Office', 'Outlook', 'Teams', 'OneDrive', 'SharePoint']

        for i in range(60):  # 60 records over 30 days (2 per day)
            ts = base_date + timedelta(days=i * 0.5)
            rows.append({
                'CreatedDateTime': ts.strftime('%Y-%m-%dT%H:%M:%S'),
                'UserPrincipalName': f'test{i % 10}@example.com',
                'UserDisplayName': f'Test User {i % 10}',
                'AppDisplayName': apps[i % len(apps)],
                'IPAddress': f'{10 + (i % 5)}.{20 + (i % 10)}.{30 + (i % 20)}.{i % 256}',
                'City': cities[i % len(cities)],
                'Country': 'AU',
                'Browser': browsers[i % len(browsers)],
                'OS': os_list[i % len(os_list)],
                'ClientAppUsed': 'Browser' if i % 3 != 0 else 'Mobile Apps and Desktop clients',
                'Status': 'Success',
                'RiskState': 'none' if i % 5 != 0 else 'atRisk',
                'RiskLevelDuringSignIn': 'none',
                'ConditionalAccessStatus': 'success' if i % 3 != 0 else 'notApplied',
                'CorrelationId': f'gap-corr-{i:05d}',
            })

        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

        return csv_path

    def test_import_creates_auth_status_view(self, temp_db, sample_signin_csv):
        """Import should create v_sign_in_auth_status view queryable."""
        importer = LogImporter(temp_db)
        importer.import_sign_in_logs(sample_signin_csv)

        conn = temp_db.connect()
        cursor = conn.cursor()

        # Query the view
        cursor.execute("""
            SELECT auth_determination, auth_confidence_pct
            FROM v_sign_in_auth_status
            LIMIT 1
        """)
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        assert row['auth_determination'] == 'CONFIRMED_SUCCESS'
        assert row['auth_confidence_pct'] == 100

    def test_import_all_populates_log_coverage_summary(self, temp_db, sample_signin_csv):
        """import_all should populate log_coverage_summary table."""
        importer = LogImporter(temp_db)

        # Use import_all to trigger post-import validation
        results = importer.import_all(sample_signin_csv.parent)

        conn = temp_db.connect()
        cursor = conn.cursor()

        # Check coverage summary was created
        cursor.execute("""
            SELECT log_type, total_records, coverage_days, gap_detected
            FROM log_coverage_summary
            WHERE log_type = 'sign_in'
        """)
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        assert row['total_records'] == 100
        assert row['coverage_days'] >= 80  # 90 days of coverage

    def test_import_detects_coverage_gap(self, temp_db, gap_signin_csv):
        """Import should detect when log coverage is below threshold."""
        importer = LogImporter(temp_db)

        # Import with gap (only 30 days)
        results = importer.import_all(gap_signin_csv.parent)

        conn = temp_db.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT gap_detected, gap_description
            FROM log_coverage_summary
            WHERE log_type = 'sign_in'
        """)
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        # Gap should be detected (30 days < 80% of 90 days = 72 days)
        assert row['gap_detected'] == 1
        assert 'days' in (row['gap_description'] or '').lower()

    def test_import_runs_powershell_validation(self, temp_db, sample_signin_csv):
        """Import should run PowerShell validation without errors."""
        importer = LogImporter(temp_db)

        # This should complete without raising exceptions
        results = importer.import_all(sample_signin_csv.parent)

        # Verify no corruption in quality summary (clean data)
        conn = temp_db.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT table_name, warnings
            FROM quality_check_summary
            WHERE table_name = 'sign_in_logs'
              AND warnings LIKE '%PowerShell%'
        """)
        row = cursor.fetchone()
        conn.close()

        # No PowerShell warning should be present for clean data
        assert row is None

    def test_auth_view_shows_different_determinations(self, temp_db, sample_signin_csv):
        """Auth view should correctly classify different auth scenarios after import.

        Note: Detailed auth determination logic is tested in unit tests
        (test_auth_status_view.py). This integration test verifies that
        the view correctly reports determinations after a real CSV import.
        """
        importer = LogImporter(temp_db)
        importer.import_sign_in_logs(sample_signin_csv)

        conn = temp_db.connect()
        cursor = conn.cursor()

        # Query view to verify auth determinations are populated
        cursor.execute("""
            SELECT
                auth_determination,
                COUNT(*) as count
            FROM v_sign_in_auth_status
            GROUP BY auth_determination
        """)
        results = {row['auth_determination']: row['count'] for row in cursor.fetchall()}
        conn.close()

        # The sample CSV has a mix of 'success' and 'notApplied' CA statuses
        # Verify that the view classifies them correctly
        assert 'CONFIRMED_SUCCESS' in results  # CA status = 'success'
        assert 'LIKELY_SUCCESS_NO_CA' in results  # CA status = 'notApplied'
        assert results['CONFIRMED_SUCCESS'] > 0
        assert results['LIKELY_SUCCESS_NO_CA'] > 0

    def test_e2e_clean_import_no_warnings(self, temp_db, sample_signin_csv, caplog):
        """End-to-end: Clean data import should not log warnings."""
        import logging
        caplog.set_level(logging.WARNING)

        importer = LogImporter(temp_db)
        results = importer.import_all(sample_signin_csv.parent)

        # Should have imported records
        assert 'sign_in' in results
        assert results['sign_in'].records_imported > 0

        # Should NOT have PowerShell corruption warnings
        ps_warnings = [r for r in caplog.records if 'POWERSHELL' in r.message.upper()]
        assert len(ps_warnings) == 0

    def test_e2e_gap_import_logs_warning(self, temp_db, gap_signin_csv, caplog):
        """End-to-end: Gap data should log coverage warning."""
        import logging
        caplog.set_level(logging.WARNING)

        importer = LogImporter(temp_db)
        results = importer.import_all(gap_signin_csv.parent)

        # Should have coverage gap warning
        gap_warnings = [r for r in caplog.records if 'GAP' in r.message.upper()]
        assert len(gap_warnings) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
