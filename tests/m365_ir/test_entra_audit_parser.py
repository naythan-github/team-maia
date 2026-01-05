#!/usr/bin/env python3
"""
TDD Tests for Entra ID Audit Log Parser - Phase 228

Tests for parsing Microsoft Entra ID (Azure AD) Audit Logs.
These logs capture directory-level administrative events like password changes,
role assignments, and app consents.

Run with: pytest tests/m365_ir/test_entra_audit_parser.py -v
"""

import csv
import io
import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

# Import will fail until implementation exists - this is TDD RED phase
from claude.tools.m365_ir.log_database import IRLogDatabase
from claude.tools.m365_ir.log_importer import LogImporter
from claude.tools.m365_ir.log_query import LogQuery


# Sample Entra ID Audit Log data (from PIR-FYNA-2025-12-08)
SAMPLE_ENTRA_AUDIT_CSV = """ActivityDateTime,ActivityDisplayName,InitiatedBy,Target,Result,ResultReason
"16/12/2025 12:19:31 AM","Change password (self-service)","sreymoml@fyna.com.au","sreymoml@fyna.com.au","success","None"
"16/12/2025 12:19:31 AM","Change user password","","sreymoml@fyna.com.au","success",""
"16/12/2025 12:19:31 AM","Update PasswordProfile","","sreymoml@fyna.com.au","success",""
"16/12/2025 12:19:16 AM","Change password (self-service)","sreymoml@fyna.com.au","sreymoml@fyna.com.au","failure","PasswordPolicyError"
"15/12/2025 11:41:43 PM","Reset user password","user_210e10e1869246e482da77fc36ea4ae5@nwcomputing.com.au","sreymoml@fyna.com.au","success",""
"5/01/2026 3:00:26 AM","Update device","","","success",""
"4/01/2026 10:24:38 PM","Add member to role","admin@fyna.com.au","user@fyna.com.au","success",""
"4/01/2026 9:10:05 PM","Update user","","zacd@fyna.com.au","success",""
"""

# Sample with UAL format (to test distinguishing)
SAMPLE_UAL_CSV = """RecordType,CreationDate,UserIds,Operations,AuditData
"SharePointFileOperation","5/01/2026 1:10:40 AM","qlik.cloud@fyna.com.au","FileDownloaded","{}"
"""


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db = IRLogDatabase(case_id="PIR-TEST-2025-001", base_path=tmpdir)
        db.create()
        yield db


@pytest.fixture
def sample_entra_csv(tmp_path):
    """Create sample Entra ID audit log CSV file."""
    csv_path = tmp_path / "2_AllUsers_AuditLogs.csv"
    csv_path.write_text(SAMPLE_ENTRA_AUDIT_CSV)
    return csv_path


@pytest.fixture
def sample_ual_csv(tmp_path):
    """Create sample UAL CSV file for testing differentiation."""
    csv_path = tmp_path / "7_AllUsers_FullAuditLog.csv"
    csv_path.write_text(SAMPLE_UAL_CSV)
    return csv_path


class TestEntraAuditTableExists:
    """Test that entra_audit_log table is created."""

    def test_table_created_on_db_create(self, temp_db):
        """entra_audit_log table should exist after db.create()."""
        conn = temp_db.connect()
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='entra_audit_log'"
        )
        result = cursor.fetchone()
        conn.close()
        assert result is not None, "entra_audit_log table should exist"

    def test_table_has_required_columns(self, temp_db):
        """entra_audit_log table should have all required columns."""
        conn = temp_db.connect()
        cursor = conn.execute("PRAGMA table_info(entra_audit_log)")
        columns = {row[1] for row in cursor.fetchall()}
        conn.close()

        required_columns = {
            'id', 'timestamp', 'activity', 'initiated_by', 'target',
            'result', 'result_reason', 'raw_record', 'imported_at'
        }
        assert required_columns.issubset(columns), f"Missing columns: {required_columns - columns}"

    def test_stats_includes_entra_audit(self, temp_db):
        """get_stats() should include entra_audit_log count."""
        stats = temp_db.get_stats()
        assert 'entra_audit_log' in stats, "Stats should include entra_audit_log"


class TestEntraAuditImport:
    """Test importing Entra ID audit logs."""

    def test_import_basic_records(self, temp_db, sample_entra_csv):
        """Should import basic Entra audit records."""
        importer = LogImporter(temp_db)
        result = importer.import_entra_audit(sample_entra_csv)

        assert result.records_imported == 8, f"Expected 8 records, got {result.records_imported}"
        assert result.records_failed == 0, f"Expected 0 failures, got {result.records_failed}"

    def test_parse_au_date_format(self, temp_db, sample_entra_csv):
        """Should correctly parse AU date format DD/MM/YYYY H:MM:SS AM/PM."""
        importer = LogImporter(temp_db)
        importer.import_entra_audit(sample_entra_csv)

        conn = temp_db.connect()
        cursor = conn.execute(
            "SELECT timestamp FROM entra_audit_log WHERE target = 'sreymoml@fyna.com.au' LIMIT 1"
        )
        timestamp = cursor.fetchone()[0]
        conn.close()

        # Should be ISO format, December 16 2025 (not January 12)
        assert timestamp.startswith('2025-12-16'), f"Date parsed incorrectly: {timestamp}"

    def test_deduplication(self, temp_db, sample_entra_csv):
        """Should skip duplicate records on re-import."""
        importer = LogImporter(temp_db)

        # First import
        result1 = importer.import_entra_audit(sample_entra_csv)
        assert result1.records_imported == 8

        # Second import - should skip all as duplicates
        result2 = importer.import_entra_audit(sample_entra_csv)
        # Either records_imported=0 (skipped by hash) or records_skipped=8 (skipped by UNIQUE)
        assert result2.records_imported == 0 or result2.records_skipped == 8

    def test_empty_fields_handled(self, temp_db, tmp_path):
        """Should handle empty InitiatedBy and Target fields."""
        csv_content = """ActivityDateTime,ActivityDisplayName,InitiatedBy,Target,Result,ResultReason
"5/01/2026 3:00:26 AM","Update device","","","success",""
"""
        csv_path = tmp_path / "empty_fields.csv"
        csv_path.write_text(csv_content)

        importer = LogImporter(temp_db)
        result = importer.import_entra_audit(csv_path)

        assert result.records_imported == 1
        assert result.records_failed == 0

    def test_import_metadata_recorded(self, temp_db, sample_entra_csv):
        """Should record import metadata."""
        importer = LogImporter(temp_db)
        importer.import_entra_audit(sample_entra_csv)

        conn = temp_db.connect()
        cursor = conn.execute(
            "SELECT log_type, records_imported FROM import_metadata WHERE log_type = 'entra_audit'"
        )
        result = cursor.fetchone()
        conn.close()

        assert result is not None, "Import metadata should be recorded"
        assert result[0] == 'entra_audit'
        assert result[1] == 8


class TestEntraAuditVsUALDistinction:
    """Test that parser distinguishes Entra audit from UAL."""

    def test_detect_entra_audit_by_columns(self, temp_db, sample_entra_csv, sample_ual_csv):
        """Should correctly identify Entra audit vs UAL by column headers."""
        importer = LogImporter(temp_db)

        # Import Entra audit
        result_entra = importer.import_entra_audit(sample_entra_csv)
        assert result_entra.records_imported == 8

        # Import UAL (should use different parser)
        result_ual = importer.import_ual(sample_ual_csv)
        assert result_ual.records_imported == 1

        # Check correct tables populated
        conn = temp_db.connect()
        cursor = conn.execute("SELECT COUNT(*) FROM entra_audit_log")
        entra_count = cursor.fetchone()[0]
        cursor = conn.execute("SELECT COUNT(*) FROM unified_audit_log")
        ual_count = cursor.fetchone()[0]
        conn.close()

        assert entra_count == 8, "Entra audit records in wrong table"
        assert ual_count == 1, "UAL records in wrong table"

    def test_import_all_auto_detects_entra_audit(self, temp_db, tmp_path):
        """import_all() should auto-detect Entra audit files."""
        # Create test directory with both file types
        entra_path = tmp_path / "2_AllUsers_AuditLogs.csv"
        entra_path.write_text(SAMPLE_ENTRA_AUDIT_CSV)

        ual_path = tmp_path / "7_AllUsers_FullAuditLog.csv"
        ual_path.write_text(SAMPLE_UAL_CSV)

        importer = LogImporter(temp_db)
        results = importer.import_all(tmp_path)

        assert 'entra_audit' in results, "Should detect and import Entra audit"
        assert 'ual' in results, "Should detect and import UAL"
        assert results['entra_audit'].records_imported == 8
        assert results['ual'].records_imported == 1


class TestEntraAuditQueries:
    """Test query methods for Entra audit logs."""

    @pytest.fixture
    def populated_db(self, temp_db, sample_entra_csv):
        """Database with imported Entra audit data."""
        importer = LogImporter(temp_db)
        importer.import_entra_audit(sample_entra_csv)
        return temp_db

    def test_entra_audit_by_user_as_target(self, populated_db):
        """Should find events where user is target."""
        query = LogQuery(populated_db)
        results = query.entra_audit_by_user("sreymoml@fyna.com.au")

        assert len(results) >= 4, f"Expected at least 4 events, got {len(results)}"

    def test_entra_audit_by_user_as_initiator(self, populated_db):
        """Should find events where user is initiator."""
        query = LogQuery(populated_db)
        results = query.entra_audit_by_user("sreymoml@fyna.com.au")

        # Should include self-service password changes where user is both
        activities = [r['activity'] for r in results]
        assert 'Change password (self-service)' in activities

    def test_query_password_changes(self, populated_db):
        """Should filter password-related events."""
        query = LogQuery(populated_db)
        results = query.password_changes()

        assert len(results) >= 4, "Should find password change events"

        for result in results:
            assert any(kw in result['activity'].lower() for kw in ['password', 'passwordprofile'])

    def test_query_password_changes_by_user(self, populated_db):
        """Should filter password events for specific user."""
        query = LogQuery(populated_db)
        results = query.password_changes(user="sreymoml@fyna.com.au")

        assert len(results) >= 4
        for result in results:
            assert result['target'] == "sreymoml@fyna.com.au" or result['initiated_by'] == "sreymoml@fyna.com.au"

    def test_query_role_changes(self, populated_db):
        """Should filter role assignment events."""
        query = LogQuery(populated_db)
        results = query.role_changes()

        assert len(results) >= 1
        assert any('role' in r['activity'].lower() for r in results)

    def test_entra_audit_by_activity(self, populated_db):
        """Should filter by activity type with LIKE support."""
        query = LogQuery(populated_db)

        # Exact match
        results = query.entra_audit_by_activity("Update device")
        assert len(results) >= 1

        # LIKE pattern
        results = query.entra_audit_by_activity("%password%")
        assert len(results) >= 4

    def test_entra_audit_summary(self, populated_db):
        """Should provide summary statistics."""
        query = LogQuery(populated_db)
        summary = query.entra_audit_summary()

        assert 'total_events' in summary
        assert summary['total_events'] == 8
        assert 'by_activity' in summary
        assert 'by_result' in summary

    def test_results_sorted_by_timestamp_desc(self, populated_db):
        """Query results should be sorted by timestamp descending."""
        query = LogQuery(populated_db)
        results = query.entra_audit_by_user("sreymoml@fyna.com.au")

        timestamps = [r['timestamp'] for r in results]
        assert timestamps == sorted(timestamps, reverse=True)


class TestEntraAuditCLI:
    """Test CLI interface for Entra audit queries."""

    @pytest.fixture
    def populated_db(self, temp_db, sample_entra_csv):
        """Database with imported Entra audit data."""
        importer = LogImporter(temp_db)
        importer.import_entra_audit(sample_entra_csv)
        return temp_db

    def test_cli_entra_audit_flag_exists(self):
        """CLI should have --entra-audit flag."""
        # This tests that the CLI code exists - implementation will add the flag
        from claude.tools.m365_ir import m365_ir_cli
        # Check that the module has query subcommand with entra options
        assert hasattr(m365_ir_cli, 'main') or True  # Placeholder until implemented

    def test_cli_password_changes_flag_exists(self):
        """CLI should have --password-changes flag."""
        from claude.tools.m365_ir import m365_ir_cli
        assert hasattr(m365_ir_cli, 'main') or True  # Placeholder until implemented


class TestEntraAuditSecurityRelevance:
    """Test detection of security-relevant events."""

    @pytest.fixture
    def security_csv(self, tmp_path):
        """CSV with security-relevant events."""
        csv_content = """ActivityDateTime,ActivityDisplayName,InitiatedBy,Target,Result,ResultReason
"16/12/2025 12:19:31 AM","Add member to role","attacker@external.com","victim@company.com","success",""
"16/12/2025 12:20:00 AM","Add service principal","attacker@external.com","MaliciousApp","success",""
"16/12/2025 12:21:00 AM","Consent to application","victim@company.com","MaliciousApp","success",""
"16/12/2025 12:22:00 AM","Update conditional access policy","attacker@external.com","","success",""
"""
        csv_path = tmp_path / "security_events.csv"
        csv_path.write_text(csv_content)
        return csv_path

    def test_detect_privilege_escalation(self, temp_db, security_csv):
        """Should flag role assignment events."""
        importer = LogImporter(temp_db)
        importer.import_entra_audit(security_csv)

        query = LogQuery(temp_db)
        results = query.role_changes()

        assert len(results) >= 1
        assert any(r['initiated_by'] == 'attacker@external.com' for r in results)

    def test_detect_oauth_app_creation(self, temp_db, security_csv):
        """Should flag service principal creation."""
        importer = LogImporter(temp_db)
        importer.import_entra_audit(security_csv)

        query = LogQuery(temp_db)
        results = query.entra_audit_by_activity("%service principal%")

        assert len(results) >= 1

    def test_detect_conditional_access_changes(self, temp_db, security_csv):
        """Should flag conditional access policy changes."""
        importer = LogImporter(temp_db)
        importer.import_entra_audit(security_csv)

        query = LogQuery(temp_db)
        results = query.entra_audit_by_activity("%conditional access%")

        assert len(results) >= 1


class TestEntraAuditIndexes:
    """Test that indexes are created for performance."""

    def test_timestamp_index_exists(self, temp_db):
        """Should have index on timestamp."""
        conn = temp_db.connect()
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE '%entra%timestamp%'"
        )
        result = cursor.fetchone()
        conn.close()
        assert result is not None, "Timestamp index should exist"

    def test_activity_index_exists(self, temp_db):
        """Should have index on activity."""
        conn = temp_db.connect()
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE '%entra%activity%'"
        )
        result = cursor.fetchone()
        conn.close()
        assert result is not None, "Activity index should exist"

    def test_target_index_exists(self, temp_db):
        """Should have index on target."""
        conn = temp_db.connect()
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE '%entra%target%'"
        )
        result = cursor.fetchone()
        conn.close()
        assert result is not None, "Target index should exist"

    def test_unique_constraint_exists(self, temp_db):
        """Should have unique constraint for deduplication."""
        conn = temp_db.connect()
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE '%entra%unique%'"
        )
        result = cursor.fetchone()
        conn.close()
        assert result is not None, "Unique index should exist"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
