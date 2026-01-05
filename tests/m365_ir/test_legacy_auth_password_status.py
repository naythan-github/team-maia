#!/usr/bin/env python3
"""
TDD Tests for Legacy Auth and Password Status Parsers

Phase: P3 - Test Design (RED)
Requirements: parser_requirements.md (PIR-FYNA-2025-12-08)

Tests for:
1. Legacy Auth Sign-ins (legacy_auth_logs table)
2. Password Last Changed (password_status table)

Tests written BEFORE implementation per TDD protocol.
"""

import pytest
import csv
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Import modules
try:
    from claude.tools.m365_ir.log_database import IRLogDatabase
    from claude.tools.m365_ir.log_importer import LogImporter, ImportResult
    from claude.tools.m365_ir.log_query import LogQuery
except ImportError:
    IRLogDatabase = None
    LogImporter = None
    ImportResult = None
    LogQuery = None


@pytest.fixture
def temp_dir():
    """Create temporary directory for test databases."""
    d = tempfile.mkdtemp()
    yield Path(d)
    shutil.rmtree(d)


@pytest.fixture
def db(temp_dir):
    """Create IRLogDatabase instance for testing."""
    if IRLogDatabase is None:
        pytest.skip("IRLogDatabase not yet implemented")
    db = IRLogDatabase(case_id="PIR-LEGACY-TEST-001", base_path=str(temp_dir))
    db.create()
    return db


@pytest.fixture
def importer(db):
    """Create LogImporter instance for testing."""
    if LogImporter is None:
        pytest.skip("LogImporter not yet implemented")
    return LogImporter(db)


@pytest.fixture
def query(db):
    """Create LogQuery instance for testing."""
    if LogQuery is None:
        pytest.skip("LogQuery not yet implemented")
    return LogQuery(db)


# ============================================================================
# Sample Data Fixtures
# ============================================================================

@pytest.fixture
def sample_legacy_auth_csv(temp_dir):
    """Create sample legacy auth sign-ins CSV with AU date format."""
    csv_path = temp_dir / "10_LegacyAuthSignIns.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'CreatedDateTime', 'UserPrincipalName', 'UserDisplayName',
            'ClientAppUsed', 'AppDisplayName', 'IPAddress', 'City',
            'Country', 'Status', 'FailureReason', 'ConditionalAccessStatus'
        ])
        writer.writeheader()
        # Record 1 - AU date format (4/01/2026 = Jan 4, 2026)
        writer.writerow({
            'CreatedDateTime': '4/01/2026 11:11:18 PM',
            'UserPrincipalName': 'payroll@fyna.com.au',
            'UserDisplayName': 'Fyna Payroll',
            'ClientAppUsed': 'Authenticated SMTP',
            'AppDisplayName': 'Office 365 Exchange Online',
            'IPAddress': '13.236.77.207',
            'City': 'Sydney',
            'Country': 'AU',
            'Status': '0',
            'FailureReason': 'Other.',
            'ConditionalAccessStatus': 'success'
        })
        # Record 2 - Earlier date
        writer.writerow({
            'CreatedDateTime': '25/12/2025 11:38:04 PM',
            'UserPrincipalName': 'payroll@fyna.com.au',
            'UserDisplayName': 'Fyna Payroll',
            'ClientAppUsed': 'Authenticated SMTP',
            'AppDisplayName': 'Office 365 Exchange Online',
            'IPAddress': '13.236.77.207',
            'City': 'Sydney',
            'Country': 'AU',
            'Status': '0',
            'FailureReason': 'Other.',
            'ConditionalAccessStatus': 'success'
        })
        # Record 3 - Different user with IMAP
        writer.writerow({
            'CreatedDateTime': '22/12/2025 12:42:04 AM',
            'UserPrincipalName': 'scanner@fyna.com.au',
            'UserDisplayName': 'Scanner Account',
            'ClientAppUsed': 'IMAP4',
            'AppDisplayName': 'Office 365 Exchange Online',
            'IPAddress': '10.1.1.50',
            'City': '',
            'Country': '',
            'Status': '0',
            'FailureReason': '',
            'ConditionalAccessStatus': 'notApplied'
        })
        # Record 4 - Failed auth
        writer.writerow({
            'CreatedDateTime': '20/12/2025 3:15:00 PM',
            'UserPrincipalName': 'test@fyna.com.au',
            'UserDisplayName': 'Test User',
            'ClientAppUsed': 'POP3',
            'AppDisplayName': 'Office 365 Exchange Online',
            'IPAddress': '185.234.100.50',
            'City': 'Moscow',
            'Country': 'RU',
            'Status': '50126',
            'FailureReason': 'Invalid username or password.',
            'ConditionalAccessStatus': 'failure'
        })
    return csv_path


@pytest.fixture
def sample_password_status_csv(temp_dir):
    """Create sample password last changed CSV with AU date format."""
    csv_path = temp_dir / "9_PasswordLastChanged.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'UserPrincipalName', 'DisplayName', 'LastPasswordChangeDateTime',
            'DaysSinceChange', 'PasswordPolicies', 'AccountEnabled', 'CreatedDateTime'
        ])
        writer.writeheader()
        # Record 1 - Very old password (4000+ days)
        writer.writerow({
            'UserPrincipalName': 'boardroom@fyna.com.au',
            'DisplayName': 'Boardroom Hallam',
            'LastPasswordChangeDateTime': '3/03/2014 12:29:47 AM',
            'DaysSinceChange': '4326',
            'PasswordPolicies': 'DisablePasswordExpiration',
            'AccountEnabled': 'True',
            'CreatedDateTime': '8/12/2021 4:49:11 AM'
        })
        # Record 2 - Recent password change
        writer.writerow({
            'UserPrincipalName': 'zacd@fyna.com.au',
            'DisplayName': 'Zac Downes',
            'LastPasswordChangeDateTime': '25/01/2024 7:06:26 AM',
            'DaysSinceChange': '711',
            'PasswordPolicies': 'DisablePasswordExpiration',
            'AccountEnabled': 'True',
            'CreatedDateTime': '25/01/2024 7:19:23 AM'
        })
        # Record 3 - Very recent change
        writer.writerow({
            'UserPrincipalName': 'sreymom@fyna.com.au',
            'DisplayName': 'Srey Mom Long',
            'LastPasswordChangeDateTime': '16/12/2025 12:19:31 AM',
            'DaysSinceChange': '20',
            'PasswordPolicies': 'DisablePasswordExpiration',
            'AccountEnabled': 'True',
            'CreatedDateTime': '5/04/2024 12:41:16 AM'
        })
        # Record 4 - No password policy (empty)
        writer.writerow({
            'UserPrincipalName': 'ceo_office@fyna.com.au',
            'DisplayName': 'CEO Office',
            'LastPasswordChangeDateTime': '8/12/2021 4:52:49 AM',
            'DaysSinceChange': '1489',
            'PasswordPolicies': '',
            'AccountEnabled': 'True',
            'CreatedDateTime': '8/12/2021 4:52:49 AM'
        })
        # Record 5 - Disabled account
        writer.writerow({
            'UserPrincipalName': 'olduser@fyna.com.au',
            'DisplayName': 'Old User',
            'LastPasswordChangeDateTime': '1/01/2020 12:00:00 AM',
            'DaysSinceChange': '2195',
            'PasswordPolicies': 'None',
            'AccountEnabled': 'False',
            'CreatedDateTime': '1/01/2020 12:00:00 AM'
        })
    return csv_path


@pytest.fixture
def empty_legacy_auth_csv(temp_dir):
    """Create empty legacy auth CSV (header only)."""
    csv_path = temp_dir / "10_Empty_LegacyAuth.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'CreatedDateTime', 'UserPrincipalName', 'UserDisplayName',
            'ClientAppUsed', 'AppDisplayName', 'IPAddress', 'City',
            'Country', 'Status', 'FailureReason', 'ConditionalAccessStatus'
        ])
        writer.writeheader()
        # No data rows
    return csv_path


@pytest.fixture
def empty_password_csv(temp_dir):
    """Create empty password status CSV (header only)."""
    csv_path = temp_dir / "9_Empty_PasswordLastChanged.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'UserPrincipalName', 'DisplayName', 'LastPasswordChangeDateTime',
            'DaysSinceChange', 'PasswordPolicies', 'AccountEnabled', 'CreatedDateTime'
        ])
        writer.writeheader()
    return csv_path


# ============================================================================
# Database Table Tests
# ============================================================================

class TestLegacyAuthTable:
    """Tests for legacy_auth_logs table creation."""

    def test_legacy_auth_table_exists(self, db):
        """Database should have legacy_auth_logs table."""
        conn = db.connect()
        cursor = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='legacy_auth_logs'
        """)
        row = cursor.fetchone()
        conn.close()
        assert row is not None, "legacy_auth_logs table should exist"

    def test_legacy_auth_table_columns(self, db):
        """legacy_auth_logs should have required columns."""
        conn = db.connect()
        cursor = conn.execute("PRAGMA table_info(legacy_auth_logs)")
        columns = {row[1] for row in cursor.fetchall()}
        conn.close()

        required_columns = {
            'id', 'timestamp', 'user_principal_name', 'user_display_name',
            'client_app_used', 'app_display_name', 'ip_address', 'city',
            'country', 'status', 'failure_reason', 'conditional_access_status',
            'raw_record', 'imported_at'
        }
        assert required_columns.issubset(columns), f"Missing columns: {required_columns - columns}"

    def test_legacy_auth_has_indexes(self, db):
        """legacy_auth_logs should have required indexes."""
        conn = db.connect()
        cursor = conn.execute("PRAGMA index_list(legacy_auth_logs)")
        indexes = {row[1] for row in cursor.fetchall()}
        conn.close()

        # Should have indexes on key columns
        assert any('timestamp' in idx or 'legacy_auth' in idx.lower() for idx in indexes)


class TestPasswordStatusTable:
    """Tests for password_status table creation."""

    def test_password_status_table_exists(self, db):
        """Database should have password_status table."""
        conn = db.connect()
        cursor = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='password_status'
        """)
        row = cursor.fetchone()
        conn.close()
        assert row is not None, "password_status table should exist"

    def test_password_status_table_columns(self, db):
        """password_status should have required columns."""
        conn = db.connect()
        cursor = conn.execute("PRAGMA table_info(password_status)")
        columns = {row[1] for row in cursor.fetchall()}
        conn.close()

        required_columns = {
            'id', 'user_principal_name', 'display_name',
            'last_password_change', 'days_since_change',
            'password_policies', 'account_enabled', 'created_datetime',
            'raw_record', 'imported_at'
        }
        assert required_columns.issubset(columns), f"Missing columns: {required_columns - columns}"

    def test_password_status_unique_on_user(self, db):
        """password_status should have unique constraint on user_principal_name."""
        conn = db.connect()
        cursor = conn.execute("PRAGMA index_list(password_status)")
        indexes = [row for row in cursor.fetchall()]
        conn.close()

        # Should have at least one unique index
        unique_indexes = [idx for idx in indexes if idx[2] == 1]  # idx[2] is unique flag
        assert len(unique_indexes) > 0, "password_status should have unique constraint"


# ============================================================================
# Legacy Auth Import Tests
# ============================================================================

class TestImportLegacyAuth:
    """Tests for legacy auth sign-ins import."""

    def test_import_legacy_auth_returns_result(self, importer, sample_legacy_auth_csv):
        """import_legacy_auth should return ImportResult."""
        result = importer.import_legacy_auth(sample_legacy_auth_csv)
        assert isinstance(result, ImportResult)

    def test_import_legacy_auth_counts_records(self, importer, sample_legacy_auth_csv):
        """ImportResult should have correct record count."""
        result = importer.import_legacy_auth(sample_legacy_auth_csv)
        assert result.records_imported == 4
        assert result.records_failed == 0

    def test_import_legacy_auth_to_database(self, importer, db, sample_legacy_auth_csv):
        """Legacy auth records should be in database."""
        importer.import_legacy_auth(sample_legacy_auth_csv)

        conn = db.connect()
        cursor = conn.execute("SELECT COUNT(*) FROM legacy_auth_logs")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 4

    def test_import_legacy_auth_parses_au_date(self, importer, db, sample_legacy_auth_csv):
        """Should correctly parse AU date format (DD/MM/YYYY H:MM:SS AM/PM)."""
        importer.import_legacy_auth(sample_legacy_auth_csv)

        conn = db.connect()
        cursor = conn.execute("""
            SELECT timestamp FROM legacy_auth_logs
            WHERE user_principal_name = 'payroll@fyna.com.au'
            ORDER BY timestamp DESC LIMIT 1
        """)
        row = cursor.fetchone()
        conn.close()

        # 4/01/2026 should be January 4th, 2026 (not April 1st)
        ts = datetime.fromisoformat(row['timestamp'])
        assert ts.month == 1
        assert ts.day == 4
        assert ts.year == 2026

    def test_import_legacy_auth_preserves_fields(self, importer, db, sample_legacy_auth_csv):
        """Imported records should have all fields preserved."""
        importer.import_legacy_auth(sample_legacy_auth_csv)

        conn = db.connect()
        cursor = conn.execute("""
            SELECT user_principal_name, client_app_used, ip_address, country, status
            FROM legacy_auth_logs WHERE ip_address = '185.234.100.50'
        """)
        row = cursor.fetchone()
        conn.close()

        assert row['user_principal_name'] == 'test@fyna.com.au'
        assert row['client_app_used'] == 'POP3'
        assert row['country'] == 'RU'
        assert row['status'] == '50126'

    def test_import_legacy_auth_stores_raw_record(self, importer, db, sample_legacy_auth_csv):
        """Should store raw record for edge cases."""
        importer.import_legacy_auth(sample_legacy_auth_csv)

        conn = db.connect()
        cursor = conn.execute("SELECT raw_record FROM legacy_auth_logs LIMIT 1")
        row = cursor.fetchone()
        conn.close()

        assert row['raw_record'] is not None
        # Should be valid JSON
        raw = json.loads(row['raw_record'])
        assert 'UserPrincipalName' in raw

    def test_import_legacy_auth_metadata_tracked(self, importer, db, sample_legacy_auth_csv):
        """Should track import in metadata table."""
        importer.import_legacy_auth(sample_legacy_auth_csv)

        conn = db.connect()
        cursor = conn.execute("SELECT * FROM import_metadata WHERE log_type = 'legacy_auth'")
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        assert row['records_imported'] == 4

    def test_import_legacy_auth_empty_file(self, importer, empty_legacy_auth_csv):
        """Should handle empty CSV gracefully."""
        result = importer.import_legacy_auth(empty_legacy_auth_csv)
        assert result.records_imported == 0
        assert result.records_failed == 0

    def test_import_legacy_auth_deduplication(self, importer, db, sample_legacy_auth_csv):
        """Should not create duplicates on reimport."""
        result1 = importer.import_legacy_auth(sample_legacy_auth_csv)
        result2 = importer.import_legacy_auth(sample_legacy_auth_csv)

        conn = db.connect()
        cursor = conn.execute("SELECT COUNT(*) FROM legacy_auth_logs")
        count = cursor.fetchone()[0]
        conn.close()

        # Should still have 4 records, not 8
        assert count == 4


# ============================================================================
# Password Status Import Tests
# ============================================================================

class TestImportPasswordStatus:
    """Tests for password status import."""

    def test_import_password_status_returns_result(self, importer, sample_password_status_csv):
        """import_password_status should return ImportResult."""
        result = importer.import_password_status(sample_password_status_csv)
        assert isinstance(result, ImportResult)

    def test_import_password_status_counts_records(self, importer, sample_password_status_csv):
        """ImportResult should have correct record count."""
        result = importer.import_password_status(sample_password_status_csv)
        assert result.records_imported == 5
        assert result.records_failed == 0

    def test_import_password_status_to_database(self, importer, db, sample_password_status_csv):
        """Password status records should be in database."""
        importer.import_password_status(sample_password_status_csv)

        conn = db.connect()
        cursor = conn.execute("SELECT COUNT(*) FROM password_status")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 5

    def test_import_password_status_parses_au_date(self, importer, db, sample_password_status_csv):
        """Should correctly parse AU date format."""
        importer.import_password_status(sample_password_status_csv)

        conn = db.connect()
        cursor = conn.execute("""
            SELECT last_password_change FROM password_status
            WHERE user_principal_name = 'boardroom@fyna.com.au'
        """)
        row = cursor.fetchone()
        conn.close()

        # 3/03/2014 should be March 3rd, 2014 (not 3rd March in US format)
        ts = datetime.fromisoformat(row['last_password_change'])
        assert ts.month == 3
        assert ts.day == 3
        assert ts.year == 2014

    def test_import_password_status_preserves_fields(self, importer, db, sample_password_status_csv):
        """Imported records should have all fields preserved."""
        importer.import_password_status(sample_password_status_csv)

        conn = db.connect()
        cursor = conn.execute("""
            SELECT user_principal_name, display_name, days_since_change,
                   password_policies, account_enabled
            FROM password_status WHERE user_principal_name = 'zacd@fyna.com.au'
        """)
        row = cursor.fetchone()
        conn.close()

        assert row['display_name'] == 'Zac Downes'
        assert row['days_since_change'] == 711
        assert row['password_policies'] == 'DisablePasswordExpiration'
        assert row['account_enabled'] == 'True'

    def test_import_password_status_handles_empty_policies(self, importer, db, sample_password_status_csv):
        """Should handle empty password policies field."""
        importer.import_password_status(sample_password_status_csv)

        conn = db.connect()
        cursor = conn.execute("""
            SELECT password_policies FROM password_status
            WHERE user_principal_name = 'ceo_office@fyna.com.au'
        """)
        row = cursor.fetchone()
        conn.close()

        assert row['password_policies'] == '' or row['password_policies'] is None

    def test_import_password_status_metadata_tracked(self, importer, db, sample_password_status_csv):
        """Should track import in metadata table."""
        importer.import_password_status(sample_password_status_csv)

        conn = db.connect()
        cursor = conn.execute("SELECT * FROM import_metadata WHERE log_type = 'password_status'")
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        assert row['records_imported'] == 5

    def test_import_password_status_empty_file(self, importer, empty_password_csv):
        """Should handle empty CSV gracefully."""
        result = importer.import_password_status(empty_password_csv)
        assert result.records_imported == 0
        assert result.records_failed == 0

    def test_import_password_status_replaces_on_reimport(self, importer, db, temp_dir):
        """Should replace existing user record on reimport (not duplicate)."""
        # First import
        csv_path = temp_dir / "9_Password.csv"
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'UserPrincipalName', 'DisplayName', 'LastPasswordChangeDateTime',
                'DaysSinceChange', 'PasswordPolicies', 'AccountEnabled', 'CreatedDateTime'
            ])
            writer.writeheader()
            writer.writerow({
                'UserPrincipalName': 'test@example.com',
                'DisplayName': 'Test User',
                'LastPasswordChangeDateTime': '1/01/2025 12:00:00 AM',
                'DaysSinceChange': '100',
                'PasswordPolicies': 'None',
                'AccountEnabled': 'True',
                'CreatedDateTime': '1/01/2020 12:00:00 AM'
            })
        importer.import_password_status(csv_path)

        # Second import with updated data
        csv_path2 = temp_dir / "9_Password2.csv"
        with open(csv_path2, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'UserPrincipalName', 'DisplayName', 'LastPasswordChangeDateTime',
                'DaysSinceChange', 'PasswordPolicies', 'AccountEnabled', 'CreatedDateTime'
            ])
            writer.writeheader()
            writer.writerow({
                'UserPrincipalName': 'test@example.com',
                'DisplayName': 'Test User Updated',
                'LastPasswordChangeDateTime': '5/01/2026 12:00:00 AM',
                'DaysSinceChange': '0',
                'PasswordPolicies': 'None',
                'AccountEnabled': 'True',
                'CreatedDateTime': '1/01/2020 12:00:00 AM'
            })
        importer.import_password_status(csv_path2)

        conn = db.connect()
        cursor = conn.execute("SELECT COUNT(*) FROM password_status WHERE user_principal_name = 'test@example.com'")
        count = cursor.fetchone()[0]
        cursor = conn.execute("SELECT days_since_change FROM password_status WHERE user_principal_name = 'test@example.com'")
        row = cursor.fetchone()
        conn.close()

        assert count == 1, "Should have only one record per user"
        assert row['days_since_change'] == 0, "Should have updated value"


# ============================================================================
# Query Method Tests
# ============================================================================

class TestLegacyAuthQueries:
    """Tests for legacy auth query methods."""

    def test_legacy_auth_by_user(self, importer, query, db, sample_legacy_auth_csv):
        """Should query legacy auth by user."""
        importer.import_legacy_auth(sample_legacy_auth_csv)

        results = query.legacy_auth_by_user('payroll@fyna.com.au')

        assert len(results) == 2
        assert all(r['user_principal_name'] == 'payroll@fyna.com.au' for r in results)

    def test_legacy_auth_by_user_partial_match(self, importer, query, db, sample_legacy_auth_csv):
        """Should support partial user matching."""
        importer.import_legacy_auth(sample_legacy_auth_csv)

        results = query.legacy_auth_by_user('%fyna.com.au')

        assert len(results) == 4  # All users are @fyna.com.au

    def test_legacy_auth_by_ip(self, importer, query, db, sample_legacy_auth_csv):
        """Should query legacy auth by IP address."""
        importer.import_legacy_auth(sample_legacy_auth_csv)

        results = query.legacy_auth_by_ip('13.236.77.207')

        assert len(results) == 2
        assert all(r['ip_address'] == '13.236.77.207' for r in results)

    def test_legacy_auth_by_client_app(self, importer, query, db, sample_legacy_auth_csv):
        """Should query legacy auth by client app type."""
        importer.import_legacy_auth(sample_legacy_auth_csv)

        results = query.legacy_auth_by_client_app('Authenticated SMTP')

        assert len(results) == 2
        assert all(r['client_app_used'] == 'Authenticated SMTP' for r in results)

    def test_legacy_auth_summary(self, importer, query, db, sample_legacy_auth_csv):
        """Should provide summary of legacy auth usage."""
        importer.import_legacy_auth(sample_legacy_auth_csv)

        summary = query.legacy_auth_summary()

        assert 'total_events' in summary
        assert 'by_client_app' in summary
        assert 'by_country' in summary
        assert 'unique_users' in summary
        assert summary['total_events'] == 4


class TestPasswordStatusQueries:
    """Tests for password status query methods."""

    def test_password_status_all(self, importer, query, db, sample_password_status_csv):
        """Should return all password status records."""
        importer.import_password_status(sample_password_status_csv)

        results = query.password_status()

        assert len(results) == 5

    def test_password_status_by_user(self, importer, query, db, sample_password_status_csv):
        """Should query password status by user."""
        importer.import_password_status(sample_password_status_csv)

        results = query.password_status(user='zacd@fyna.com.au')

        assert len(results) == 1
        assert results[0]['user_principal_name'] == 'zacd@fyna.com.au'

    def test_stale_passwords(self, importer, query, db, sample_password_status_csv):
        """Should find accounts with passwords older than N days."""
        importer.import_password_status(sample_password_status_csv)

        # Find passwords older than 90 days
        results = query.stale_passwords(days=90)

        # All records except sreymom (20 days) should be stale
        assert len(results) == 4
        assert all(r['days_since_change'] > 90 for r in results)

    def test_stale_passwords_sorted_by_age(self, importer, query, db, sample_password_status_csv):
        """Stale passwords should be sorted by age (oldest first)."""
        importer.import_password_status(sample_password_status_csv)

        results = query.stale_passwords(days=90)

        # Verify sorted by days_since_change descending
        days = [r['days_since_change'] for r in results]
        assert days == sorted(days, reverse=True)

    def test_stale_passwords_enabled_only(self, importer, query, db, sample_password_status_csv):
        """Should optionally filter to enabled accounts only."""
        importer.import_password_status(sample_password_status_csv)

        results = query.stale_passwords(days=90, enabled_only=True)

        # olduser is disabled, should be excluded
        assert all(r['account_enabled'] == 'True' for r in results)
        assert not any(r['user_principal_name'] == 'olduser@fyna.com.au' for r in results)


# ============================================================================
# import_all Integration Tests
# ============================================================================

class TestImportAllWithNewTypes:
    """Tests for import_all with legacy auth and password status."""

    def test_import_all_discovers_legacy_auth(self, importer, temp_dir, sample_legacy_auth_csv):
        """import_all should discover legacy auth files."""
        exports_dir = temp_dir / "exports"
        exports_dir.mkdir()
        (exports_dir / "10_LegacyAuthSignIns.csv").write_text(sample_legacy_auth_csv.read_text())

        results = importer.import_all(exports_dir)

        assert 'legacy_auth' in results
        assert results['legacy_auth'].records_imported == 4

    def test_import_all_discovers_password_status(self, importer, temp_dir, sample_password_status_csv):
        """import_all should discover password status files."""
        exports_dir = temp_dir / "exports"
        exports_dir.mkdir()
        (exports_dir / "9_PasswordLastChanged.csv").write_text(sample_password_status_csv.read_text())

        results = importer.import_all(exports_dir)

        assert 'password_status' in results
        assert results['password_status'].records_imported == 5

    def test_import_all_discovers_both_types(
        self, importer, temp_dir, sample_legacy_auth_csv, sample_password_status_csv
    ):
        """import_all should discover both new log types together."""
        exports_dir = temp_dir / "exports"
        exports_dir.mkdir()
        (exports_dir / "9_PasswordLastChanged.csv").write_text(sample_password_status_csv.read_text())
        (exports_dir / "10_LegacyAuthSignIns.csv").write_text(sample_legacy_auth_csv.read_text())

        results = importer.import_all(exports_dir)

        assert 'legacy_auth' in results
        assert 'password_status' in results


# ============================================================================
# Database Stats Tests
# ============================================================================

class TestDatabaseStatsWithNewTables:
    """Tests for get_stats with new tables."""

    def test_stats_includes_legacy_auth(self, importer, db, sample_legacy_auth_csv):
        """get_stats should include legacy_auth_logs count."""
        importer.import_legacy_auth(sample_legacy_auth_csv)

        stats = db.get_stats()

        assert 'legacy_auth_logs' in stats
        assert stats['legacy_auth_logs'] == 4

    def test_stats_includes_password_status(self, importer, db, sample_password_status_csv):
        """get_stats should include password_status count."""
        importer.import_password_status(sample_password_status_csv)

        stats = db.get_stats()

        assert 'password_status' in stats
        assert stats['password_status'] == 5
