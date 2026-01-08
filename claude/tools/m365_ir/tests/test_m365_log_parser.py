#!/usr/bin/env python3
"""
TDD Tests for M365 Log Parser

Tests written FIRST per TDD methodology.
Run: pytest claude/tools/m365_ir/tests/test_m365_log_parser.py -v

Author: Maia System
Created: 2025-12-18 (Phase 225)
"""

import pytest
from datetime import datetime, date
from pathlib import Path
import sys

# Add Maia root to path
MAIA_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

from claude.tools.m365_ir.m365_log_parser import (
    M365LogParser,
    detect_date_format,
    parse_m365_datetime,
    LogType,
    SignInLogEntry,
    AuditLogEntry,
    MailboxAuditEntry,
    LegacyAuthEntry,
)


class TestDateFormatDetection:
    """Test automatic date format detection (AU DD/MM vs US MM/DD)"""

    def test_detect_au_format_unambiguous(self):
        """15/11/2025 must be AU format (day > 12)"""
        assert detect_date_format("15/11/2025 7:22:01 AM") == "AU"

    def test_detect_au_format_day_greater_than_12(self):
        """Any day > 12 confirms AU format"""
        assert detect_date_format("25/12/2025 10:00:00 AM") == "AU"
        assert detect_date_format("13/01/2025 3:00:00 PM") == "AU"
        assert detect_date_format("31/12/2025 11:59:59 PM") == "AU"

    def test_ambiguous_date_with_context(self):
        """3/11/2025 is ambiguous - need context from other dates"""
        # When we have other unambiguous dates showing AU format
        sample_dates = [
            "15/11/2025 7:22:01 AM",  # Unambiguous AU
            "3/11/2025 6:01:01 PM",    # Ambiguous
            "20/11/2025 10:00:00 AM",  # Unambiguous AU
        ]
        assert detect_date_format(sample_dates) == "AU"

    def test_all_ambiguous_defaults_to_au(self):
        """If all dates are ambiguous, default to AU (Australian tenant)"""
        sample_dates = [
            "3/11/2025 6:01:01 PM",
            "5/11/2025 3:55:59 AM",
            "1/12/2025 10:00:00 AM",
        ]
        # Default to AU for Australian tenants
        assert detect_date_format(sample_dates, default="AU") == "AU"

    def test_invalid_date_raises_error(self):
        """Invalid date format should raise ValueError"""
        with pytest.raises(ValueError):
            detect_date_format("not-a-date")

    def test_empty_input_raises_error(self):
        """Empty input should raise ValueError"""
        with pytest.raises(ValueError):
            detect_date_format("")
        with pytest.raises(ValueError):
            detect_date_format([])


class TestDateTimeParsing:
    """Test datetime parsing with correct format"""

    def test_parse_au_datetime(self):
        """Parse AU format datetime correctly"""
        result = parse_m365_datetime("3/12/2025 7:22:01 AM", date_format="AU")
        assert result.year == 2025
        assert result.month == 12
        assert result.day == 3
        assert result.hour == 7
        assert result.minute == 22
        assert result.second == 1

    def test_parse_au_datetime_pm(self):
        """Parse AU format PM datetime correctly"""
        result = parse_m365_datetime("15/11/2025 3:30:00 PM", date_format="AU")
        assert result.hour == 15
        assert result.minute == 30

    def test_parse_us_datetime(self):
        """Parse US format datetime correctly"""
        result = parse_m365_datetime("12/3/2025 7:22:01 AM", date_format="US")
        assert result.year == 2025
        assert result.month == 12
        assert result.day == 3

    def test_parse_iso_datetime(self):
        """Parse ISO format datetime from AuditData JSON"""
        result = parse_m365_datetime("2025-12-03T07:31:34", date_format="ISO")
        assert result.year == 2025
        assert result.month == 12
        assert result.day == 3
        assert result.hour == 7
        assert result.minute == 31


class TestSignInLogParsing:
    """Test sign-in log CSV parsing"""

    @pytest.fixture
    def parser(self):
        return M365LogParser(date_format="AU")

    @pytest.fixture
    def sample_signin_csv(self, tmp_path):
        """Create sample sign-in log CSV"""
        csv_content = '''"CreatedDateTime","UserPrincipalName","UserDisplayName","AppDisplayName","IPAddress","City","Country","Device","Browser","OS","Status","RiskState","RiskLevelDuringSignIn","RiskLevelAggregated","ConditionalAccessStatus"
"3/12/2025 7:22:01 AM","mark.laririt@oculus.info","Mark Laririt","Microsoft Authentication Broker","103.137.15.46","Melbourne","AU","","Mobile Safari 18.2","Ios 18.6.2","Microsoft.Graph.PowerShell.Models.MicrosoftGraphSignInStatus","none","hidden","hidden","notApplied"
"15/11/2025 3:55:59 AM","simonbond@oculus.info","Simon Bond","Microsoft Office","185.234.72.10","Moscow","RU","","Chrome 119","Windows 10","Microsoft.Graph.PowerShell.Models.MicrosoftGraphSignInStatus","none","none","none","success"
'''
        csv_file = tmp_path / "signin_logs.csv"
        csv_file.write_text(csv_content)
        return csv_file

    def test_parse_signin_logs_returns_list(self, parser, sample_signin_csv):
        """Parser should return list of SignInLogEntry"""
        entries = parser.parse_signin_logs(sample_signin_csv)
        assert isinstance(entries, list)
        assert len(entries) == 2
        assert all(isinstance(e, SignInLogEntry) for e in entries)

    def test_parse_signin_logs_correct_fields(self, parser, sample_signin_csv):
        """Parser should extract all fields correctly"""
        entries = parser.parse_signin_logs(sample_signin_csv)
        entry = entries[0]

        assert entry.user_principal_name == "mark.laririt@oculus.info"
        assert entry.user_display_name == "Mark Laririt"
        assert entry.ip_address == "103.137.15.46"
        assert entry.city == "Melbourne"
        assert entry.country == "AU"
        assert entry.app_display_name == "Microsoft Authentication Broker"
        assert entry.conditional_access_status == "notApplied"

    def test_parse_signin_logs_datetime_parsed(self, parser, sample_signin_csv):
        """Datetime should be parsed to Python datetime"""
        entries = parser.parse_signin_logs(sample_signin_csv)
        entry = entries[0]

        assert isinstance(entry.created_datetime, datetime)
        assert entry.created_datetime.year == 2025
        assert entry.created_datetime.month == 12
        assert entry.created_datetime.day == 3

    def test_handle_status_object_bug(self, parser, sample_signin_csv):
        """Handle Microsoft.Graph.PowerShell.Models object in Status field"""
        entries = parser.parse_signin_logs(sample_signin_csv)
        entry = entries[0]

        # Status should be normalized, not the raw object reference
        assert entry.status_raw == "Microsoft.Graph.PowerShell.Models.MicrosoftGraphSignInStatus"
        # We flag this as "unknown" since we can't determine success/failure
        assert entry.status_normalized == "unknown"

    def test_parse_signin_logs_foreign_login(self, parser, sample_signin_csv):
        """Parser should correctly identify foreign login"""
        entries = parser.parse_signin_logs(sample_signin_csv)
        russian_entry = entries[1]

        assert russian_entry.country == "RU"
        assert russian_entry.user_principal_name == "simonbond@oculus.info"


class TestMailboxAuditParsing:
    """Test mailbox audit log CSV parsing with nested JSON"""

    @pytest.fixture
    def parser(self):
        return M365LogParser(date_format="AU")

    @pytest.fixture
    def sample_mailbox_csv(self, tmp_path):
        """Create sample mailbox audit CSV with nested JSON (M365 uses "" for escaping)"""
        csv_content = '''"RecordType","CreationDate","UserIds","Operations","AuditData","ResultIndex","ResultCount","Identity","IsValid","ObjectState"
"ExchangeItemAggregated","3/12/2025 7:31:34 AM","claire@oculus.info","MailItemsAccessed","{""CreationTime"":""2025-12-03T07:31:34"",""Operation"":""MailItemsAccessed"",""UserId"":""claire@oculus.info"",""ClientIPAddress"":""110.175.56.190"",""ClientInfoString"":""Client=OWA;Action=ViaProxy""}","1","226494","8b236c9f-f890-4078-97e1-5e8d8abe4680","True","Unchanged"
'''
        csv_file = tmp_path / "mailbox_audit.csv"
        csv_file.write_text(csv_content)
        return csv_file

    def test_parse_mailbox_audit_returns_list(self, parser, sample_mailbox_csv):
        """Parser should return list of MailboxAuditEntry"""
        entries = parser.parse_mailbox_audit(sample_mailbox_csv)
        assert isinstance(entries, list)
        assert len(entries) == 1
        assert all(isinstance(e, MailboxAuditEntry) for e in entries)

    def test_parse_mailbox_audit_extracts_ip_from_json(self, parser, sample_mailbox_csv):
        """Parser should extract ClientIPAddress from nested JSON"""
        entries = parser.parse_mailbox_audit(sample_mailbox_csv)
        entry = entries[0]

        assert entry.client_ip_address == "110.175.56.190"

    def test_parse_mailbox_audit_extracts_operation(self, parser, sample_mailbox_csv):
        """Parser should extract operation type"""
        entries = parser.parse_mailbox_audit(sample_mailbox_csv)
        entry = entries[0]

        assert entry.operation == "MailItemsAccessed"
        assert entry.user_id == "claire@oculus.info"


class TestLegacyAuthParsing:
    """Test legacy auth sign-in log parsing"""

    @pytest.fixture
    def parser(self):
        return M365LogParser(date_format="AU")

    @pytest.fixture
    def sample_legacy_auth_csv(self, tmp_path):
        """Create sample legacy auth CSV"""
        csv_content = '''"CreatedDateTime","UserPrincipalName","UserDisplayName","ClientAppUsed","AppDisplayName","IPAddress","City","Country","Status","FailureReason","ConditionalAccessStatus"
"8/12/2025 3:09:32 PM","alia@oculus.info","Alia Horvath","Authenticated SMTP","Office 365 Exchange Online","121.18.148.10","Shijiazhuang","CN","50126","Error validating credentials due to invalid username or password.","notApplied"
"15/12/2025 10:30:00 AM","simonbond@oculus.info","Simon Bond","IMAP4","Office 365 Exchange Online","185.234.72.10","Moscow","RU","50126","Sign-in was blocked because it came from","failure"
'''
        csv_file = tmp_path / "legacy_auth.csv"
        csv_file.write_text(csv_content)
        return csv_file

    def test_parse_legacy_auth_returns_list(self, parser, sample_legacy_auth_csv):
        """Parser should return list of LegacyAuthEntry"""
        entries = parser.parse_legacy_auth(sample_legacy_auth_csv)
        assert isinstance(entries, list)
        assert len(entries) == 2
        assert all(isinstance(e, LegacyAuthEntry) for e in entries)

    def test_parse_legacy_auth_client_app(self, parser, sample_legacy_auth_csv):
        """Parser should extract client app type"""
        entries = parser.parse_legacy_auth(sample_legacy_auth_csv)

        assert entries[0].client_app_used == "Authenticated SMTP"
        assert entries[1].client_app_used == "IMAP4"

    def test_parse_legacy_auth_failure_reason(self, parser, sample_legacy_auth_csv):
        """Parser should extract failure reason"""
        entries = parser.parse_legacy_auth(sample_legacy_auth_csv)

        assert "Error validating credentials" in entries[0].failure_reason
        assert "blocked" in entries[1].failure_reason

    def test_parse_legacy_auth_status_code(self, parser, sample_legacy_auth_csv):
        """Parser should handle numeric status codes"""
        entries = parser.parse_legacy_auth(sample_legacy_auth_csv)

        assert entries[0].status == "50126"
        assert entries[0].status_normalized == "failure"  # 50126 = invalid credentials


class TestMultiExportMerging:
    """Test merging multiple export directories"""

    @pytest.fixture
    def parser(self):
        return M365LogParser(date_format="AU")

    def test_merge_overlapping_exports(self, parser, tmp_path):
        """Merge exports with overlapping date ranges"""
        # Create two export directories with overlapping data
        export1 = tmp_path / "export1"
        export2 = tmp_path / "export2"
        export1.mkdir()
        export2.mkdir()

        # Export 1: Nov 3 - Dec 3
        csv1 = '''"CreatedDateTime","UserPrincipalName","UserDisplayName","AppDisplayName","IPAddress","City","Country","Device","Browser","OS","Status","RiskState","RiskLevelDuringSignIn","RiskLevelAggregated","ConditionalAccessStatus"
"3/11/2025 6:01:01 PM","user@test.com","Test User","App","1.1.1.1","City","AU","","Chrome","Windows","status","none","none","none","success"
"15/11/2025 10:00:00 AM","user@test.com","Test User","App","1.1.1.1","City","AU","","Chrome","Windows","status","none","none","none","success"
'''
        # Export 2: Nov 10 - Dec 10 (overlaps with export 1)
        csv2 = '''"CreatedDateTime","UserPrincipalName","UserDisplayName","AppDisplayName","IPAddress","City","Country","Device","Browser","OS","Status","RiskState","RiskLevelDuringSignIn","RiskLevelAggregated","ConditionalAccessStatus"
"15/11/2025 10:00:00 AM","user@test.com","Test User","App","1.1.1.1","City","AU","","Chrome","Windows","status","none","none","none","success"
"25/11/2025 10:00:00 AM","user@test.com","Test User","App","1.1.1.1","City","AU","","Chrome","Windows","status","none","none","none","success"
'''
        (export1 / "1_AllUsers_SignInLogs.csv").write_text(csv1)
        (export2 / "1_AllUsers_SignInLogs.csv").write_text(csv2)

        merged = parser.merge_exports([export1, export2], log_type=LogType.SIGNIN)

        # Should deduplicate the Nov 15 entry
        assert len(merged) == 3  # Nov 3, Nov 15 (deduped), Nov 25

    def test_merge_preserves_chronological_order(self, parser, tmp_path):
        """Merged entries should be in chronological order"""
        export1 = tmp_path / "export1"
        export1.mkdir()

        csv1 = '''"CreatedDateTime","UserPrincipalName","UserDisplayName","AppDisplayName","IPAddress","City","Country","Device","Browser","OS","Status","RiskState","RiskLevelDuringSignIn","RiskLevelAggregated","ConditionalAccessStatus"
"15/11/2025 10:00:00 AM","user@test.com","Test User","App","1.1.1.1","City","AU","","Chrome","Windows","status","none","none","none","success"
"3/11/2025 6:01:01 PM","user@test.com","Test User","App","1.1.1.1","City","AU","","Chrome","Windows","status","none","none","none","success"
'''
        (export1 / "1_AllUsers_SignInLogs.csv").write_text(csv1)

        entries = parser.parse_signin_logs(export1 / "1_AllUsers_SignInLogs.csv")
        sorted_entries = parser.sort_chronologically(entries)

        # Nov 3 should come before Nov 15
        assert sorted_entries[0].created_datetime < sorted_entries[1].created_datetime


class TestExportDirectoryDiscovery:
    """Test automatic discovery of log files in export directories"""

    @pytest.fixture
    def parser(self):
        return M365LogParser(date_format="AU")

    def test_discover_log_files(self, parser, tmp_path):
        """Parser should discover all log files in export directory"""
        export = tmp_path / "export"
        export.mkdir()

        # Create typical export files
        (export / "1_AllUsers_SignInLogs.csv").write_text("header\n")
        (export / "2_AllUsers_AuditLogs.csv").write_text("header\n")
        (export / "4_AllUsers_MailboxAudit.csv").write_text("header\n")
        (export / "10_LegacyAuthSignIns.csv").write_text("header\n")

        discovered = parser.discover_log_files(export)

        assert LogType.SIGNIN in discovered
        # Note: LogType.AUDIT is deprecated, use ENTRA_AUDIT instead
        assert LogType.ENTRA_AUDIT in discovered
        assert LogType.MAILBOX_AUDIT in discovered
        assert LogType.LEGACY_AUTH in discovered

    def test_handle_missing_optional_files(self, parser, tmp_path):
        """Parser should handle missing optional files gracefully"""
        export = tmp_path / "export"
        export.mkdir()

        # Only create required files (no legacy auth)
        (export / "1_AllUsers_SignInLogs.csv").write_text("header\n")

        discovered = parser.discover_log_files(export)

        assert LogType.SIGNIN in discovered
        assert LogType.LEGACY_AUTH not in discovered  # Not an error


class TestAutoDateFormatDetection:
    """Test automatic date format detection from log files"""

    @pytest.fixture
    def sample_export_au(self, tmp_path):
        """Create export with AU date format"""
        export = tmp_path / "export_au"
        export.mkdir()

        csv = '''"CreatedDateTime","UserPrincipalName","UserDisplayName","AppDisplayName","IPAddress","City","Country","Device","Browser","OS","Status","RiskState","RiskLevelDuringSignIn","RiskLevelAggregated","ConditionalAccessStatus"
"15/11/2025 10:00:00 AM","user@test.com","Test","App","1.1.1.1","City","AU","","Chrome","Windows","status","none","none","none","success"
"25/12/2025 3:00:00 PM","user@test.com","Test","App","1.1.1.1","City","AU","","Chrome","Windows","status","none","none","none","success"
'''
        (export / "1_AllUsers_SignInLogs.csv").write_text(csv)
        return export

    def test_auto_detect_au_format(self, sample_export_au):
        """Parser should auto-detect AU format from unambiguous dates"""
        parser = M365LogParser.from_export(sample_export_au)

        assert parser.date_format == "AU"

    def test_parser_uses_detected_format(self, sample_export_au):
        """Parser should use detected format for all parsing"""
        parser = M365LogParser.from_export(sample_export_au)
        entries = parser.parse_signin_logs(sample_export_au / "1_AllUsers_SignInLogs.csv")

        # Nov 15 should be parsed correctly
        assert entries[0].created_datetime.month == 11
        assert entries[0].created_datetime.day == 15


class TestParseErrorHandling:
    """Test logging and tracking of parse errors (Security Finding Fix - Phase 225.2)"""

    @pytest.fixture
    def parser(self):
        return M365LogParser(date_format="AU")

    @pytest.fixture
    def malformed_signin_csv(self, tmp_path):
        """Create CSV with some malformed rows"""
        csv_content = '''"CreatedDateTime","UserPrincipalName","UserDisplayName","AppDisplayName","IPAddress","City","Country","Device","Browser","OS","Status","RiskState","RiskLevelDuringSignIn","RiskLevelAggregated","ConditionalAccessStatus"
"3/12/2025 7:22:01 AM","good@test.com","Good User","App","1.1.1.1","City","AU","","Chrome","Windows","status","none","none","none","success"
"INVALID_DATE","bad@test.com","Bad User","App","1.1.1.1","City","AU","","Chrome","Windows","status","none","none","none","success"
"15/11/2025 10:00:00 AM","good2@test.com","Good User 2","App","2.2.2.2","City","AU","","Chrome","Windows","status","none","none","none","success"
'''
        csv_file = tmp_path / "malformed_signin.csv"
        csv_file.write_text(csv_content)
        return csv_file

    def test_parse_continues_on_malformed_row(self, parser, malformed_signin_csv):
        """Parser should continue processing after malformed row"""
        entries = parser.parse_signin_logs(malformed_signin_csv)
        # Should get 2 valid entries (skip the malformed one)
        assert len(entries) == 2
        assert entries[0].user_principal_name == "good@test.com"
        assert entries[1].user_principal_name == "good2@test.com"

    def test_parse_logs_malformed_rows(self, parser, malformed_signin_csv, caplog):
        """Parser should log warning for malformed rows"""
        import logging
        with caplog.at_level(logging.DEBUG, logger="claude.tools.m365_ir.m365_log_parser"):
            entries = parser.parse_signin_logs(malformed_signin_csv)

        # Should have logged the parse error
        assert any("malformed" in record.message.lower() or "skipped" in record.message.lower()
                   or "failed" in record.message.lower() for record in caplog.records), \
            f"Expected log about malformed row, got: {[r.message for r in caplog.records]}"

    def test_parse_tracks_error_count(self, parser, malformed_signin_csv):
        """Parser should track number of parse errors"""
        entries = parser.parse_signin_logs(malformed_signin_csv)

        # Parser should expose error count
        assert hasattr(parser, 'last_parse_errors'), "Parser should have last_parse_errors attribute"
        assert parser.last_parse_errors == 1, f"Expected 1 error, got {parser.last_parse_errors}"

    def test_parse_error_count_resets_each_parse(self, parser, malformed_signin_csv, tmp_path):
        """Error count should reset on each parse call"""
        # First parse with errors
        parser.parse_signin_logs(malformed_signin_csv)

        # Create clean CSV
        clean_csv = tmp_path / "clean.csv"
        clean_csv.write_text('''"CreatedDateTime","UserPrincipalName","UserDisplayName","AppDisplayName","IPAddress","City","Country","Device","Browser","OS","Status","RiskState","RiskLevelDuringSignIn","RiskLevelAggregated","ConditionalAccessStatus"
"3/12/2025 7:22:01 AM","user@test.com","User","App","1.1.1.1","City","AU","","Chrome","Windows","status","none","none","none","success"
''')
        # Second parse with no errors
        parser.parse_signin_logs(clean_csv)

        assert parser.last_parse_errors == 0, "Error count should reset to 0 for clean parse"


class TestMailboxParseErrorHandling:
    """Test error handling for mailbox audit parsing"""

    @pytest.fixture
    def parser(self):
        return M365LogParser(date_format="AU")

    @pytest.fixture
    def malformed_mailbox_csv(self, tmp_path):
        """Create mailbox CSV with malformed JSON"""
        csv_content = '''"RecordType","CreationDate","UserIds","Operations","AuditData","ResultIndex","ResultCount","Identity","IsValid","ObjectState"
"ExchangeItemAggregated","3/12/2025 7:31:34 AM","good@test.com","MailItemsAccessed","{""CreationTime"":""2025-12-03T07:31:34"",""ClientIPAddress"":""1.1.1.1""}","1","1","id1","True","Unchanged"
"ExchangeItemAggregated","INVALID_DATE","bad@test.com","MailItemsAccessed","{""CreationTime"":""2025-12-03T07:31:34""}","1","1","id2","True","Unchanged"
"ExchangeItemAggregated","15/11/2025 10:00:00 AM","good2@test.com","MailItemsAccessed","{""CreationTime"":""2025-11-15T10:00:00"",""ClientIPAddress"":""2.2.2.2""}","1","1","id3","True","Unchanged"
'''
        csv_file = tmp_path / "malformed_mailbox.csv"
        csv_file.write_text(csv_content)
        return csv_file

    def test_mailbox_parse_continues_on_error(self, parser, malformed_mailbox_csv):
        """Mailbox parser should continue after malformed row"""
        entries = parser.parse_mailbox_audit(malformed_mailbox_csv)
        assert len(entries) == 2

    def test_mailbox_parse_tracks_errors(self, parser, malformed_mailbox_csv):
        """Mailbox parser should track errors"""
        entries = parser.parse_mailbox_audit(malformed_mailbox_csv)
        assert hasattr(parser, 'last_parse_errors')
        assert parser.last_parse_errors == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
