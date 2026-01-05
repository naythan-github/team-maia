#!/usr/bin/env python3
"""
TDD Tests for LogImporter - CSV/JSON to SQLite import

Phase: P3 - Test Design (RED)
Requirements: IR_LOG_DATABASE_REQUIREMENTS.md

Tests written BEFORE implementation per TDD protocol.
"""

import pytest
import csv
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass

# Import will fail until implementation exists (expected RED state)
try:
    from claude.tools.m365_ir.log_database import IRLogDatabase
    from claude.tools.m365_ir.log_importer import LogImporter, ImportResult
    from claude.tools.m365_ir.compression import decompress_json
except ImportError:
    IRLogDatabase = None
    LogImporter = None
    ImportResult = None
    decompress_json = None


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
    db = IRLogDatabase(case_id="PIR-IMPORT-TEST-001", base_path=str(temp_dir))
    db.create()
    return db


@pytest.fixture
def importer(db):
    """Create LogImporter instance for testing."""
    if LogImporter is None:
        pytest.skip("LogImporter not yet implemented")
    return LogImporter(db)


@pytest.fixture
def sample_signin_csv(temp_dir):
    """Create sample sign-in logs CSV."""
    csv_path = temp_dir / "sample_signin.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'CreatedDateTime', 'UserPrincipalName', 'UserDisplayName',
            'AppDisplayName', 'IPAddress', 'City', 'Country',
            'Device', 'Browser', 'OS', 'Status',
            'RiskState', 'RiskLevelDuringSignIn', 'RiskLevelAggregated',
            'ConditionalAccessStatus'
        ])
        writer.writeheader()
        writer.writerow({
            'CreatedDateTime': '15/12/2025 9:30:00 AM',
            'UserPrincipalName': 'user1@example.com',
            'UserDisplayName': 'User One',
            'AppDisplayName': 'Microsoft Office',
            'IPAddress': '203.0.113.1',
            'City': 'Sydney',
            'Country': 'Australia',
            'Device': 'Windows 11',
            'Browser': 'Chrome 120',
            'OS': 'Windows',
            'Status': 'Success',
            'RiskState': 'none',
            'RiskLevelDuringSignIn': 'none',
            'RiskLevelAggregated': 'none',
            'ConditionalAccessStatus': 'success'
        })
        writer.writerow({
            'CreatedDateTime': '15/12/2025 10:45:00 AM',
            'UserPrincipalName': 'user2@example.com',
            'UserDisplayName': 'User Two',
            'AppDisplayName': 'Exchange Online',
            'IPAddress': '185.234.100.50',
            'City': 'Moscow',
            'Country': 'Russia',
            'Device': '',
            'Browser': 'Safari',
            'OS': 'Windows',
            'Status': 'Failure',
            'RiskState': 'atRisk',
            'RiskLevelDuringSignIn': 'high',
            'RiskLevelAggregated': 'high',
            'ConditionalAccessStatus': 'failure'
        })
    return csv_path


@pytest.fixture
def sample_ual_csv(temp_dir):
    """Create sample Unified Audit Log CSV."""
    csv_path = temp_dir / "sample_ual.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'CreationDate', 'UserIds', 'Operations', 'Workload',
            'RecordType', 'ResultStatus', 'ClientIP', 'ObjectId', 'AuditData'
        ])
        writer.writeheader()
        writer.writerow({
            'CreationDate': '15/12/2025 11:00:00 AM',
            'UserIds': 'user1@example.com',
            'Operations': 'Set-InboxRule',
            'Workload': 'Exchange',
            'RecordType': '1',
            'ResultStatus': 'Succeeded',
            'ClientIP': '185.234.100.50',
            'ObjectId': 'rule-123',
            'AuditData': json.dumps({
                'RuleName': 'Forward External',
                'ForwardTo': 'attacker@evil.com'
            })
        })
        writer.writerow({
            'CreationDate': '15/12/2025 11:30:00 AM',
            'UserIds': 'user1@example.com',
            'Operations': 'MailItemsAccessed',
            'Workload': 'Exchange',
            'RecordType': '2',
            'ResultStatus': 'Succeeded',
            'ClientIP': '185.234.100.50',
            'ObjectId': '',
            'AuditData': json.dumps({'ItemCount': 150})
        })
    return csv_path


@pytest.fixture
def sample_mailbox_csv(temp_dir):
    """Create sample mailbox audit CSV."""
    csv_path = temp_dir / "sample_mailbox.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'CreationDate', 'RecordType', 'UserIds', 'Operations',
            'Identity', 'AuditData'
        ])
        writer.writeheader()
        writer.writerow({
            'CreationDate': '15/12/2025 12:00:00 PM',
            'RecordType': '2',
            'UserIds': 'victim@example.com',
            'Operations': 'FolderBind',
            'Identity': 'folder-bind-001',
            'AuditData': json.dumps({
                'ClientIPAddress': '185.234.100.50',
                'Folders': [{'Path': 'Inbox'}]
            })
        })
    return csv_path


class TestLogImporterCreation:
    """Tests for LogImporter instantiation."""

    def test_create_with_database(self, db):
        """LogImporter should accept IRLogDatabase."""
        if LogImporter is None:
            pytest.skip("LogImporter not yet implemented")
        importer = LogImporter(db)
        assert importer is not None

    def test_exposes_database(self, importer):
        """LogImporter should expose database reference."""
        assert importer.db is not None


class TestImportSignInLogs:
    """Tests for sign-in log import."""

    def test_import_returns_result(self, importer, sample_signin_csv):
        """import_sign_in_logs should return ImportResult."""
        result = importer.import_sign_in_logs(sample_signin_csv)
        assert isinstance(result, ImportResult)

    def test_import_counts_records(self, importer, sample_signin_csv):
        """ImportResult should have correct record count."""
        result = importer.import_sign_in_logs(sample_signin_csv)
        assert result.records_imported == 2
        assert result.records_failed == 0

    def test_import_calculates_hash(self, importer, sample_signin_csv):
        """ImportResult should include source file hash."""
        result = importer.import_sign_in_logs(sample_signin_csv)
        assert result.source_hash is not None
        assert len(result.source_hash) == 64  # SHA256

    def test_import_records_duration(self, importer, sample_signin_csv):
        """ImportResult should include duration."""
        result = importer.import_sign_in_logs(sample_signin_csv)
        assert result.duration_seconds >= 0

    def test_import_inserts_to_database(self, importer, db, sample_signin_csv):
        """Imported records should be in database."""
        importer.import_sign_in_logs(sample_signin_csv)

        conn = db.connect()
        cursor = conn.execute("SELECT COUNT(*) FROM sign_in_logs")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 2

    def test_import_preserves_fields(self, importer, db, sample_signin_csv):
        """Imported records should have all fields."""
        importer.import_sign_in_logs(sample_signin_csv)

        conn = db.connect()
        cursor = conn.execute("""
            SELECT user_principal_name, ip_address, location_country
            FROM sign_in_logs WHERE ip_address = '185.234.100.50'
        """)
        row = cursor.fetchone()
        conn.close()

        assert row['user_principal_name'] == 'user2@example.com'
        assert row['location_country'] == 'Russia'

    def test_import_stores_raw_record(self, importer, db, sample_signin_csv):
        """Should store raw record for edge cases."""
        importer.import_sign_in_logs(sample_signin_csv)

        conn = db.connect()
        cursor = conn.execute("SELECT raw_record FROM sign_in_logs LIMIT 1")
        row = cursor.fetchone()
        conn.close()

        assert row['raw_record'] is not None

    def test_import_metadata_tracked(self, importer, db, sample_signin_csv):
        """Should track import in metadata table."""
        importer.import_sign_in_logs(sample_signin_csv)

        conn = db.connect()
        cursor = conn.execute("SELECT * FROM import_metadata WHERE log_type = 'sign_in'")
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        assert row['records_imported'] == 2
        assert 'sample_signin.csv' in row['source_file']


class TestImportUAL:
    """Tests for Unified Audit Log import."""

    def test_import_ual_returns_result(self, importer, sample_ual_csv):
        """import_ual should return ImportResult."""
        result = importer.import_ual(sample_ual_csv)
        assert isinstance(result, ImportResult)
        assert result.records_imported == 2

    def test_import_ual_to_database(self, importer, db, sample_ual_csv):
        """UAL records should be in database."""
        importer.import_ual(sample_ual_csv)

        conn = db.connect()
        cursor = conn.execute("SELECT * FROM unified_audit_log WHERE operation = 'Set-InboxRule'")
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        assert row['client_ip'] == '185.234.100.50'

    def test_import_ual_preserves_audit_data(self, importer, db, sample_ual_csv):
        """Should preserve full AuditData JSON (compressed in Phase 229)."""
        importer.import_ual(sample_ual_csv)

        conn = db.connect()
        cursor = conn.execute("SELECT audit_data FROM unified_audit_log WHERE operation = 'Set-InboxRule'")
        row = cursor.fetchone()
        conn.close()

        # Phase 229: audit_data is now compressed, decompress before parsing
        audit_data_str = decompress_json(row['audit_data'])
        audit_data = json.loads(audit_data_str)
        assert audit_data['ForwardTo'] == 'attacker@evil.com'


class TestImportMailboxAudit:
    """Tests for mailbox audit import."""

    def test_import_mailbox_returns_result(self, importer, sample_mailbox_csv):
        """import_mailbox_audit should return ImportResult."""
        result = importer.import_mailbox_audit(sample_mailbox_csv)
        assert isinstance(result, ImportResult)
        assert result.records_imported == 1

    def test_import_mailbox_to_database(self, importer, db, sample_mailbox_csv):
        """Mailbox audit records should be in database."""
        importer.import_mailbox_audit(sample_mailbox_csv)

        conn = db.connect()
        cursor = conn.execute("SELECT * FROM mailbox_audit_log")
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        assert row['operation'] == 'FolderBind'


class TestImportAll:
    """Tests for bulk import from directory."""

    def test_import_all_discovers_files(self, importer, temp_dir, sample_signin_csv, sample_ual_csv):
        """import_all should discover and import all log types."""
        # Move files to exports directory
        exports_dir = temp_dir / "exports"
        exports_dir.mkdir()

        # Rename to match M365 patterns
        (exports_dir / "1_TestSignInLogs.csv").write_text(sample_signin_csv.read_text())
        (exports_dir / "7_TestFullAuditLog.csv").write_text(sample_ual_csv.read_text())

        results = importer.import_all(exports_dir)

        assert 'sign_in' in results
        assert 'unified_audit_log' in results or 'ual' in results

    def test_import_all_returns_summary(self, importer, temp_dir, sample_signin_csv):
        """import_all should return dict of ImportResults."""
        exports_dir = temp_dir / "exports"
        exports_dir.mkdir()
        (exports_dir / "1_TestSignInLogs.csv").write_text(sample_signin_csv.read_text())

        results = importer.import_all(exports_dir)

        assert isinstance(results, dict)
        for key, result in results.items():
            assert isinstance(result, ImportResult)


class TestImportErrorHandling:
    """Tests for import error handling."""

    def test_import_malformed_csv_partial(self, importer, temp_dir):
        """Should import valid rows, skip malformed ones."""
        csv_path = temp_dir / "malformed.csv"
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['CreatedDateTime', 'UserPrincipalName', 'IPAddress'])
            writer.writeheader()
            writer.writerow({'CreatedDateTime': '15/12/2025 9:00:00 AM', 'UserPrincipalName': 'valid@test.com', 'IPAddress': '1.2.3.4'})
            writer.writerow({'CreatedDateTime': 'INVALID DATE', 'UserPrincipalName': 'bad@test.com', 'IPAddress': '5.6.7.8'})
            writer.writerow({'CreatedDateTime': '16/12/2025 10:00:00 AM', 'UserPrincipalName': 'valid2@test.com', 'IPAddress': '9.10.11.12'})

        result = importer.import_sign_in_logs(csv_path)

        assert result.records_imported == 2
        assert result.records_failed == 1
        assert len(result.errors) == 1

    def test_import_missing_file_raises(self, importer, temp_dir):
        """Should raise FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            importer.import_sign_in_logs(temp_dir / "nonexistent.csv")

    def test_import_empty_csv(self, importer, temp_dir):
        """Should handle empty CSV gracefully."""
        csv_path = temp_dir / "empty.csv"
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['CreatedDateTime', 'UserPrincipalName'])
            writer.writeheader()
            # No data rows

        result = importer.import_sign_in_logs(csv_path)
        assert result.records_imported == 0
        assert result.records_failed == 0


class TestImportIdempotency:
    """Tests for preventing duplicate imports."""

    def test_reimport_same_file_skips(self, importer, db, sample_signin_csv):
        """Importing same file twice should skip second import."""
        result1 = importer.import_sign_in_logs(sample_signin_csv)
        result2 = importer.import_sign_in_logs(sample_signin_csv)

        # Second import should detect already imported
        assert result2.records_imported == 0 or result2.source_hash == result1.source_hash

        # Database should not have duplicates
        conn = db.connect()
        cursor = conn.execute("SELECT COUNT(*) FROM sign_in_logs")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 2  # Not 4


class TestImportResultDataclass:
    """Tests for ImportResult structure."""

    def test_import_result_has_all_fields(self, importer, sample_signin_csv):
        """ImportResult should have all required fields."""
        result = importer.import_sign_in_logs(sample_signin_csv)

        assert hasattr(result, 'source_file')
        assert hasattr(result, 'source_hash')
        assert hasattr(result, 'records_imported')
        assert hasattr(result, 'records_failed')
        assert hasattr(result, 'errors')
        assert hasattr(result, 'duration_seconds')

    def test_import_result_errors_is_list(self, importer, sample_signin_csv):
        """errors should be a list."""
        result = importer.import_sign_in_logs(sample_signin_csv)
        assert isinstance(result.errors, list)


# ============================================================================
# Phase 226.1 - OAuth Consents and Inbox Rules Import Tests
# ============================================================================

@pytest.fixture
def sample_oauth_csv(temp_dir):
    """Create sample OAuth consents CSV matching real Fyna format."""
    csv_path = temp_dir / "sample_oauth.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'ClientId', 'ConsentType', 'PrincipalId', 'Scope'
        ])
        writer.writeheader()
        writer.writerow({
            'ClientId': '15c54411-814e-446b-920a-3252cf62b503',
            'ConsentType': 'AllPrincipals',
            'PrincipalId': '',
            'Scope': 'user_impersonation'
        })
        writer.writerow({
            'ClientId': 'abc12345-def6-7890-ghij-klmnopqrstuv',
            'ConsentType': 'Principal',
            'PrincipalId': 'user1@example.com',
            'Scope': 'Mail.Read Mail.Send User.Read'
        })
        writer.writerow({
            'ClientId': 'malicious-app-id-suspicious',
            'ConsentType': 'Principal',
            'PrincipalId': 'victim@example.com',
            'Scope': 'Mail.ReadWrite Mail.Send Files.ReadWrite.All'
        })
    return csv_path


@pytest.fixture
def sample_inbox_rules_csv(temp_dir):
    """Create sample inbox rules CSV matching real Fyna format."""
    csv_path = temp_dir / "sample_inbox_rules.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'Mailbox', 'RuleName', 'Enabled', 'Priority',
            'ForwardTo', 'ForwardAsAttachmentTo', 'RedirectTo',
            'DeleteMessage', 'MoveToFolder'
        ])
        writer.writeheader()
        writer.writerow({
            'Mailbox': 'user1@example.com',
            'RuleName': 'Normal Rule',
            'Enabled': 'True',
            'Priority': '1',
            'ForwardTo': '',
            'ForwardAsAttachmentTo': '',
            'RedirectTo': '',
            'DeleteMessage': 'False',
            'MoveToFolder': 'Archive'
        })
        writer.writerow({
            'Mailbox': 'victim@example.com',
            'RuleName': 'RSS Feeds',
            'Enabled': 'True',
            'Priority': '1',
            'ForwardTo': 'attacker@evil.com',
            'ForwardAsAttachmentTo': '',
            'RedirectTo': '',
            'DeleteMessage': 'False',
            'MoveToFolder': ''
        })
        writer.writerow({
            'Mailbox': 'victim@example.com',
            'RuleName': 'Delete Alerts',
            'Enabled': 'True',
            'Priority': '2',
            'ForwardTo': '',
            'ForwardAsAttachmentTo': '',
            'RedirectTo': '',
            'DeleteMessage': 'True',
            'MoveToFolder': ''
        })
    return csv_path


class TestImportOAuthConsents:
    """Tests for OAuth consents import."""

    def test_import_oauth_returns_result(self, importer, sample_oauth_csv):
        """import_oauth_consents should return ImportResult."""
        result = importer.import_oauth_consents(sample_oauth_csv)
        assert isinstance(result, ImportResult)

    def test_import_oauth_counts_records(self, importer, sample_oauth_csv):
        """ImportResult should have correct record count."""
        result = importer.import_oauth_consents(sample_oauth_csv)
        assert result.records_imported == 3
        assert result.records_failed == 0

    def test_import_oauth_to_database(self, importer, db, sample_oauth_csv):
        """OAuth records should be in database."""
        importer.import_oauth_consents(sample_oauth_csv)

        conn = db.connect()
        cursor = conn.execute("SELECT COUNT(*) FROM oauth_consents")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 3

    def test_import_oauth_preserves_fields(self, importer, db, sample_oauth_csv):
        """Imported records should have mapped fields."""
        importer.import_oauth_consents(sample_oauth_csv)

        conn = db.connect()
        cursor = conn.execute("""
            SELECT app_id, consent_type, user_principal_name, permissions
            FROM oauth_consents WHERE user_principal_name = 'victim@example.com'
        """)
        row = cursor.fetchone()
        conn.close()

        assert row['app_id'] == 'malicious-app-id-suspicious'
        assert row['consent_type'] == 'Principal'
        assert 'Mail.ReadWrite' in row['permissions']

    def test_import_oauth_handles_empty_principal(self, importer, db, sample_oauth_csv):
        """Should handle AllPrincipals with empty PrincipalId."""
        importer.import_oauth_consents(sample_oauth_csv)

        conn = db.connect()
        cursor = conn.execute("""
            SELECT * FROM oauth_consents WHERE consent_type = 'AllPrincipals'
        """)
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        assert row['user_principal_name'] == '' or row['user_principal_name'] is None

    def test_import_oauth_metadata_tracked(self, importer, db, sample_oauth_csv):
        """Should track import in metadata table."""
        importer.import_oauth_consents(sample_oauth_csv)

        conn = db.connect()
        cursor = conn.execute("SELECT * FROM import_metadata WHERE log_type = 'oauth'")
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        assert row['records_imported'] == 3


class TestImportInboxRules:
    """Tests for inbox rules import."""

    def test_import_inbox_rules_returns_result(self, importer, sample_inbox_rules_csv):
        """import_inbox_rules should return ImportResult."""
        result = importer.import_inbox_rules(sample_inbox_rules_csv)
        assert isinstance(result, ImportResult)

    def test_import_inbox_rules_counts_records(self, importer, sample_inbox_rules_csv):
        """ImportResult should have correct record count."""
        result = importer.import_inbox_rules(sample_inbox_rules_csv)
        assert result.records_imported == 3
        assert result.records_failed == 0

    def test_import_inbox_rules_to_database(self, importer, db, sample_inbox_rules_csv):
        """Inbox rules should be in database."""
        importer.import_inbox_rules(sample_inbox_rules_csv)

        conn = db.connect()
        cursor = conn.execute("SELECT COUNT(*) FROM inbox_rules")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 3

    def test_import_inbox_rules_preserves_fields(self, importer, db, sample_inbox_rules_csv):
        """Imported records should have mapped fields."""
        importer.import_inbox_rules(sample_inbox_rules_csv)

        conn = db.connect()
        cursor = conn.execute("""
            SELECT user, rule_name, forward_to, delete_message
            FROM inbox_rules WHERE forward_to != ''
        """)
        row = cursor.fetchone()
        conn.close()

        assert row['user'] == 'victim@example.com'
        assert row['rule_name'] == 'RSS Feeds'
        assert row['forward_to'] == 'attacker@evil.com'

    def test_import_inbox_rules_delete_flag(self, importer, db, sample_inbox_rules_csv):
        """Should correctly parse delete_message boolean."""
        importer.import_inbox_rules(sample_inbox_rules_csv)

        conn = db.connect()
        cursor = conn.execute("""
            SELECT delete_message FROM inbox_rules WHERE rule_name = 'Delete Alerts'
        """)
        row = cursor.fetchone()
        conn.close()

        assert row['delete_message'] == 1  # SQLite stores bool as int

    def test_import_inbox_rules_metadata_tracked(self, importer, db, sample_inbox_rules_csv):
        """Should track import in metadata table."""
        importer.import_inbox_rules(sample_inbox_rules_csv)

        conn = db.connect()
        cursor = conn.execute("SELECT * FROM import_metadata WHERE log_type = 'inbox_rules'")
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        assert row['records_imported'] == 3


class TestImportAllWithNewTypes:
    """Tests for import_all including OAuth and Inbox Rules."""

    def test_import_all_discovers_oauth(self, importer, temp_dir, sample_oauth_csv):
        """import_all should discover OAuth consents files."""
        exports_dir = temp_dir / "exports"
        exports_dir.mkdir()
        (exports_dir / "5_AllUsers_OAuthConsents.csv").write_text(sample_oauth_csv.read_text())

        results = importer.import_all(exports_dir)

        assert 'oauth' in results
        assert results['oauth'].records_imported == 3

    def test_import_all_discovers_inbox_rules(self, importer, temp_dir, sample_inbox_rules_csv):
        """import_all should discover inbox rules files."""
        exports_dir = temp_dir / "exports"
        exports_dir.mkdir()
        (exports_dir / "3_AllUsers_InboxRules.csv").write_text(sample_inbox_rules_csv.read_text())

        results = importer.import_all(exports_dir)

        assert 'inbox_rules' in results
        assert results['inbox_rules'].records_imported == 3


# ============================================================================
# Phase 226.2 - Record Deduplication Tests
# ============================================================================

@pytest.fixture
def duplicate_signin_csv(temp_dir):
    """Create CSV with duplicate sign-in records (same timestamp+user+ip)."""
    csv_path = temp_dir / "duplicate_signin.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'CreatedDateTime', 'UserPrincipalName', 'UserDisplayName',
            'AppDisplayName', 'IPAddress', 'City', 'Country',
            'Browser', 'OS', 'Status', 'CorrelationId'
        ])
        writer.writeheader()
        # Record 1
        writer.writerow({
            'CreatedDateTime': '10/12/2024 9:30:00 AM',
            'UserPrincipalName': 'user@example.com',
            'UserDisplayName': 'Test User',
            'AppDisplayName': 'Microsoft Office',
            'IPAddress': '192.168.1.1',
            'City': 'Sydney',
            'Country': 'Australia',
            'Browser': 'Chrome',
            'OS': 'Windows',
            'Status': '0',
            'CorrelationId': 'abc-123'
        })
        # Record 2 - DUPLICATE (same timestamp, user, ip, correlation_id)
        writer.writerow({
            'CreatedDateTime': '10/12/2024 9:30:00 AM',
            'UserPrincipalName': 'user@example.com',
            'UserDisplayName': 'Test User',
            'AppDisplayName': 'Microsoft Office',
            'IPAddress': '192.168.1.1',
            'City': 'Sydney',
            'Country': 'Australia',
            'Browser': 'Chrome',
            'OS': 'Windows',
            'Status': '0',
            'CorrelationId': 'abc-123'
        })
        # Record 3 - UNIQUE (different correlation_id)
        writer.writerow({
            'CreatedDateTime': '10/12/2024 9:30:00 AM',
            'UserPrincipalName': 'user@example.com',
            'UserDisplayName': 'Test User',
            'AppDisplayName': 'Microsoft Office',
            'IPAddress': '192.168.1.1',
            'City': 'Sydney',
            'Country': 'Australia',
            'Browser': 'Chrome',
            'OS': 'Windows',
            'Status': '0',
            'CorrelationId': 'def-456'
        })
    return csv_path


@pytest.fixture
def duplicate_ual_csv(temp_dir):
    """Create CSV with duplicate UAL records (same timestamp+user+operation+object)."""
    csv_path = temp_dir / "duplicate_ual.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'CreationDate', 'UserIds', 'Operations', 'AuditData'
        ])
        writer.writeheader()
        # Record 1
        writer.writerow({
            'CreationDate': '2024-10-12T09:30:00',
            'UserIds': 'user@example.com',
            'Operations': 'FileAccessed',
            'AuditData': json.dumps({
                'CreationTime': '2024-10-12T09:30:00',
                'UserId': 'user@example.com',
                'Operation': 'FileAccessed',
                'ObjectId': 'file123.docx',
                'ClientIP': '192.168.1.1'
            })
        })
        # Record 2 - DUPLICATE (same timestamp, user, operation, object)
        writer.writerow({
            'CreationDate': '2024-10-12T09:30:00',
            'UserIds': 'user@example.com',
            'Operations': 'FileAccessed',
            'AuditData': json.dumps({
                'CreationTime': '2024-10-12T09:30:00',
                'UserId': 'user@example.com',
                'Operation': 'FileAccessed',
                'ObjectId': 'file123.docx',
                'ClientIP': '192.168.1.1'
            })
        })
        # Record 3 - UNIQUE (different object)
        writer.writerow({
            'CreationDate': '2024-10-12T09:30:00',
            'UserIds': 'user@example.com',
            'Operations': 'FileAccessed',
            'AuditData': json.dumps({
                'CreationTime': '2024-10-12T09:30:00',
                'UserId': 'user@example.com',
                'Operation': 'FileAccessed',
                'ObjectId': 'file456.xlsx',
                'ClientIP': '192.168.1.1'
            })
        })
    return csv_path


@pytest.fixture
def duplicate_mailbox_csv(temp_dir):
    """Create CSV with duplicate mailbox audit records."""
    csv_path = temp_dir / "duplicate_mailbox.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'LastAccessed', 'MailboxOwnerUPN', 'Operation',
            'OperationResult', 'LogonType', 'ClientIPAddress', 'ItemId'
        ])
        writer.writeheader()
        # Record 1
        writer.writerow({
            'LastAccessed': '10/12/2024 9:30:00 AM',
            'MailboxOwnerUPN': 'user@example.com',
            'Operation': 'MailItemsAccessed',
            'OperationResult': 'Succeeded',
            'LogonType': 'Owner',
            'ClientIPAddress': '192.168.1.1',
            'ItemId': 'item-abc-123'
        })
        # Record 2 - DUPLICATE (same timestamp, user, operation, item)
        writer.writerow({
            'LastAccessed': '10/12/2024 9:30:00 AM',
            'MailboxOwnerUPN': 'user@example.com',
            'Operation': 'MailItemsAccessed',
            'OperationResult': 'Succeeded',
            'LogonType': 'Owner',
            'ClientIPAddress': '192.168.1.1',
            'ItemId': 'item-abc-123'
        })
        # Record 3 - UNIQUE (different item)
        writer.writerow({
            'LastAccessed': '10/12/2024 9:30:00 AM',
            'MailboxOwnerUPN': 'user@example.com',
            'Operation': 'MailItemsAccessed',
            'OperationResult': 'Succeeded',
            'LogonType': 'Owner',
            'ClientIPAddress': '192.168.1.1',
            'ItemId': 'item-def-456'
        })
    return csv_path


class TestRecordDeduplication:
    """Tests for record-level deduplication using UNIQUE constraints."""

    def test_signin_dedup_on_import(self, importer, db, duplicate_signin_csv):
        """Duplicate sign-in records should be silently skipped."""
        result = importer.import_sign_in_logs(duplicate_signin_csv)

        # Should only import 2 unique records (3 rows - 1 duplicate)
        conn = db.connect()
        cursor = conn.execute("SELECT COUNT(*) FROM sign_in_logs")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 2  # Only unique records

    def test_signin_dedup_reports_skipped(self, importer, duplicate_signin_csv):
        """ImportResult should report actual new records imported."""
        result = importer.import_sign_in_logs(duplicate_signin_csv)

        # records_imported should reflect actual inserts, not attempts
        assert result.records_imported == 2
        assert result.records_skipped == 1  # New field for skipped duplicates

    def test_ual_dedup_on_import(self, importer, db, duplicate_ual_csv):
        """Duplicate UAL records should be silently skipped."""
        result = importer.import_ual(duplicate_ual_csv)

        conn = db.connect()
        cursor = conn.execute("SELECT COUNT(*) FROM unified_audit_log")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 2  # Only unique records

    def test_mailbox_dedup_on_import(self, importer, db, duplicate_mailbox_csv):
        """Duplicate mailbox audit records should be silently skipped."""
        result = importer.import_mailbox_audit(duplicate_mailbox_csv)

        conn = db.connect()
        cursor = conn.execute("SELECT COUNT(*) FROM mailbox_audit_log")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 2  # Only unique records

    def test_multi_file_dedup(self, importer, db, temp_dir, duplicate_signin_csv):
        """Records from different files with same content deduplicate."""
        # Import first file
        result1 = importer.import_sign_in_logs(duplicate_signin_csv)

        # Create second file with DIFFERENT content but overlapping records
        csv_path2 = temp_dir / "signin_file2.csv"
        with open(csv_path2, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'CreatedDateTime', 'UserPrincipalName', 'UserDisplayName',
                'AppDisplayName', 'IPAddress', 'City', 'Country',
                'Browser', 'OS', 'Status', 'CorrelationId'
            ])
            writer.writeheader()
            # Same record as in first file (duplicate)
            writer.writerow({
                'CreatedDateTime': '10/12/2024 9:30:00 AM',
                'UserPrincipalName': 'user@example.com',
                'UserDisplayName': 'Test User',
                'AppDisplayName': 'Microsoft Office',
                'IPAddress': '192.168.1.1',
                'City': 'Sydney',
                'Country': 'Australia',
                'Browser': 'Chrome',
                'OS': 'Windows',
                'Status': '0',
                'CorrelationId': 'abc-123'
            })
            # New unique record
            writer.writerow({
                'CreatedDateTime': '10/12/2024 10:30:00 AM',
                'UserPrincipalName': 'user@example.com',
                'UserDisplayName': 'Test User',
                'AppDisplayName': 'Microsoft Office',
                'IPAddress': '192.168.1.1',
                'City': 'Sydney',
                'Country': 'Australia',
                'Browser': 'Chrome',
                'OS': 'Windows',
                'Status': '0',
                'CorrelationId': 'ghi-789'
            })

        # Import second file (different hash, but has overlapping record)
        result2 = importer.import_sign_in_logs(csv_path2)

        # Should have 3 unique records total (2 from first + 1 new from second)
        conn = db.connect()
        cursor = conn.execute("SELECT COUNT(*) FROM sign_in_logs")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 3  # 2 from first file + 1 new from second
        assert result2.records_imported == 1  # Only 1 new record
        assert result2.records_skipped == 1  # 1 duplicate skipped
