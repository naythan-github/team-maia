#!/usr/bin/env python3
"""
Integration test for Phase 231 MFA and Risky Users import handlers.
"""

import pytest
import tempfile
import csv
from pathlib import Path
from claude.tools.m365_ir.log_database import IRLogDatabase
from claude.tools.m365_ir.log_importer import LogImporter


def test_mfa_changes_import_integration():
    """Test MFA changes import end-to-end."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test database
        db = IRLogDatabase(case_id="PIR-TEST-2026-01-06", base_path=tmpdir)
        db.create()
        importer = LogImporter(db)

        # Create test MFA changes CSV
        csv_path = Path(tmpdir) / "6_AllUsers_MFAChanges.csv"
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['ActivityDateTime', 'ActivityDisplayName', 'User', 'Result'])
            writer.writeheader()
            writer.writerow({
                'ActivityDateTime': '3/12/2025 5:34:30 AM',
                'ActivityDisplayName': 'User registered security info',
                'User': 'test@example.com',
                'Result': 'success'
            })

        # Import
        result = importer.import_mfa_changes(csv_path)

        # Verify
        assert result.records_imported == 1
        assert result.records_failed == 0

        # Check database
        conn = db.connect()
        cursor = conn.execute("SELECT * FROM mfa_changes")
        rows = cursor.fetchall()
        conn.close()

        assert len(rows) == 1


def test_risky_users_import_integration():
    """Test risky users import end-to-end."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test database
        db = IRLogDatabase(case_id="PIR-TEST-2026-01-06", base_path=tmpdir)
        db.create()
        importer = LogImporter(db)

        # Create test risky users CSV
        csv_path = Path(tmpdir) / "8_RiskyUsers.csv"
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['UserPrincipalName', 'RiskLevel', 'RiskState', 'RiskDetail', 'RiskLastUpdatedDateTime'])
            writer.writeheader()
            writer.writerow({
                'UserPrincipalName': 'risky@example.com',
                'RiskLevel': 'high',
                'RiskState': 'atRisk',
                'RiskDetail': 'anomalousToken',
                'RiskLastUpdatedDateTime': '3/12/2025 5:34:30 AM'
            })

        # Import
        result = importer.import_risky_users(csv_path)

        # Verify
        assert result.records_imported == 1
        assert result.records_failed == 0

        # Check database
        conn = db.connect()
        cursor = conn.execute("SELECT * FROM risky_users")
        rows = cursor.fetchall()
        conn.close()

        assert len(rows) == 1


def test_import_all_detects_new_types():
    """Test that import_all() auto-detects MFA and Risky Users files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test database
        db = IRLogDatabase(case_id="PIR-TEST-2026-01-06", base_path=tmpdir)
        db.create()
        importer = LogImporter(db)

        # Create test files
        export_dir = Path(tmpdir) / "exports"
        export_dir.mkdir()

        mfa_path = export_dir / "6_AllUsers_MFAChanges.csv"
        with open(mfa_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['ActivityDateTime', 'ActivityDisplayName', 'User', 'Result'])
            writer.writeheader()
            writer.writerow({
                'ActivityDateTime': '3/12/2025 5:34:30 AM',
                'ActivityDisplayName': 'User registered security info',
                'User': 'test@example.com',
                'Result': 'success'
            })

        risky_path = export_dir / "8_RiskyUsers.csv"
        with open(risky_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['UserPrincipalName', 'RiskLevel', 'RiskState', 'RiskDetail'])
            writer.writeheader()
            writer.writerow({
                'UserPrincipalName': 'risky@example.com',
                'RiskLevel': 'high',
                'RiskState': 'atRisk',
                'RiskDetail': 'anomalousToken'
            })

        # Import all
        results = importer.import_all(export_dir)

        # Verify both were imported
        assert 'mfa_changes' in results
        assert 'risky_users' in results
        assert results['mfa_changes'].records_imported == 1
        assert results['risky_users'].records_imported == 1
