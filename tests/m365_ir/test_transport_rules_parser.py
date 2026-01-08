#!/usr/bin/env python3
"""
TDD Tests for TransportRules Parser

Priority 1: Active exfiltration detection
MITRE: T1114.003 (Email Collection: Email Forwarding Rule)

Test data: /tmp/fyna_extract/TenantWide_Investigation_20260108_083839/13_TransportRules.csv
"""

import pytest
import csv
import tempfile
from pathlib import Path
from datetime import datetime

# Import paths for test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from claude.tools.m365_ir.m365_log_parser import (
    M365LogParser,
    LogType,
    LOG_FILE_PATTERNS,
)


# Sample CSV data matching FYNA export format exactly
# Note: Column order is Name,State,Priority,Mode,FromScope,SentToScope,BlindCopyTo,CopyTo,RedirectMessageTo,DeleteMessage,ModifySubject,SetSCL,Conditions,Exceptions,WhenChanged,Comments
SAMPLE_TRANSPORT_RULES_CSV = '''"Name","State","Priority","Mode","FromScope","SentToScope","BlindCopyTo","CopyTo","RedirectMessageTo","DeleteMessage","ModifySubject","SetSCL","Conditions","Exceptions","WhenChanged","Comments"
"T20230512.0084-Forwarding from Orders@fyna.com.au Email Address","Enabled","0","Enforce",,,,"","fynafoods@letlucy.biz orders@fyna.com.au","False",,,"Microsoft.Exchange.MessagingPolicies.Rules.Tasks.SentToPredicate; Microsoft.Exchange.MessagingPolicies.Rules.Tasks.AttachmentSizeOverPredicate","","26/08/2024 12:41:04 AM",
"NW Aware Spam Filtering Whitelisting","Enabled","1","Enforce",,,,,,"False",,"-1","Microsoft.Exchange.MessagingPolicies.Rules.Tasks.SenderIpRangesPredicate","","26/08/2024 1:05:55 AM",
"Spam Bypass Rule","Disabled","2","Enforce",,,,,,"True",,"-1","","","1/01/2024 10:00:00 AM",
'''


class TestLogTypeEnum:
    """Test that TRANSPORT_RULES is added to LogType enum."""

    def test_transport_rules_in_enum(self):
        """LogType enum should include TRANSPORT_RULES."""
        assert hasattr(LogType, 'TRANSPORT_RULES')
        assert LogType.TRANSPORT_RULES.value == "transport_rules"


class TestFilePatternMatching:
    """Test file pattern matching for transport rules CSV."""

    def test_pattern_matches_numbered_format(self):
        """Pattern should match '13_TransportRules.csv' format."""
        import re
        pattern = LOG_FILE_PATTERNS.get(LogType.TRANSPORT_RULES)
        assert pattern is not None, "TRANSPORT_RULES pattern not in LOG_FILE_PATTERNS"

        # Test various filename formats
        assert re.match(pattern, "13_TransportRules.csv")
        assert re.match(pattern, "13_FynaFoods_TransportRules.csv")

    def test_pattern_rejects_non_transport_files(self):
        """Pattern should not match other log types."""
        import re
        pattern = LOG_FILE_PATTERNS.get(LogType.TRANSPORT_RULES)
        assert pattern is not None

        assert not re.match(pattern, "01_SignInLogs.csv")
        assert not re.match(pattern, "14_MailboxDelegations.csv")


class TestTransportRuleEntryDataclass:
    """Test TransportRuleEntry dataclass structure."""

    def test_dataclass_has_required_fields(self):
        """TransportRuleEntry should have all IOC-relevant fields."""
        from claude.tools.m365_ir.m365_log_parser import TransportRuleEntry

        # Check critical IOC fields exist
        required_fields = [
            'name', 'state', 'priority', 'mode',
            'blind_copy_to', 'copy_to', 'redirect_message_to',
            'delete_message', 'set_scl', 'conditions',
            'when_changed', 'raw_record'
        ]

        entry_fields = [f.name for f in TransportRuleEntry.__dataclass_fields__.values()]
        for field in required_fields:
            assert field in entry_fields, f"Missing field: {field}"


class TestTransportRulesParser:
    """Test M365LogParser.parse_transport_rules() method."""

    @pytest.fixture
    def parser(self):
        """Create parser instance with AU date format."""
        return M365LogParser(date_format="AU")

    @pytest.fixture
    def sample_csv_path(self, tmp_path):
        """Create sample CSV file for testing."""
        csv_file = tmp_path / "13_TransportRules.csv"
        csv_file.write_text(SAMPLE_TRANSPORT_RULES_CSV, encoding='utf-8')
        return csv_file

    def test_parse_returns_list_of_entries(self, parser, sample_csv_path):
        """Parser should return list of TransportRuleEntry objects."""
        entries = parser.parse_transport_rules(sample_csv_path)

        assert isinstance(entries, list)
        assert len(entries) == 3  # 3 rules in sample data

        from claude.tools.m365_ir.m365_log_parser import TransportRuleEntry
        assert all(isinstance(e, TransportRuleEntry) for e in entries)

    def test_parse_extracts_rule_name(self, parser, sample_csv_path):
        """Parser should extract rule name correctly."""
        entries = parser.parse_transport_rules(sample_csv_path)

        assert entries[0].name == "T20230512.0084-Forwarding from Orders@fyna.com.au Email Address"
        assert entries[1].name == "NW Aware Spam Filtering Whitelisting"

    def test_parse_extracts_state(self, parser, sample_csv_path):
        """Parser should extract rule state (Enabled/Disabled)."""
        entries = parser.parse_transport_rules(sample_csv_path)

        assert entries[0].state == "Enabled"
        assert entries[2].state == "Disabled"

    def test_parse_extracts_redirect_to(self, parser, sample_csv_path):
        """Parser should extract RedirectMessageTo (exfiltration IOC)."""
        entries = parser.parse_transport_rules(sample_csv_path)

        assert "fynafoods@letlucy.biz" in entries[0].redirect_message_to
        assert entries[1].redirect_message_to == ""  # Empty for non-redirect rules

    def test_parse_extracts_scl(self, parser, sample_csv_path):
        """Parser should extract SetSCL (spam bypass indicator)."""
        entries = parser.parse_transport_rules(sample_csv_path)

        assert entries[1].set_scl == -1  # Whitelisting
        assert entries[0].set_scl is None  # No SCL set

    def test_parse_extracts_delete_flag(self, parser, sample_csv_path):
        """Parser should extract DeleteMessage flag."""
        entries = parser.parse_transport_rules(sample_csv_path)

        assert entries[0].delete_message is False
        assert entries[2].delete_message is True

    def test_parse_extracts_when_changed(self, parser, sample_csv_path):
        """Parser should parse WhenChanged datetime."""
        entries = parser.parse_transport_rules(sample_csv_path)

        # AU format: 26/08/2024 12:41:04 AM
        assert entries[0].when_changed == datetime(2024, 8, 26, 0, 41, 4)

    def test_parse_handles_empty_file(self, parser, tmp_path):
        """Parser should handle empty CSV gracefully."""
        empty_csv = tmp_path / "13_TransportRules.csv"
        empty_csv.write_text("Name,State,Priority,Mode,FromScope,SentToScope,BlindCopyTo,CopyTo,RedirectMessageTo,DeleteMessage,ModifySubject,SetSCL,Conditions,Exceptions,WhenChanged,Comments\n")

        entries = parser.parse_transport_rules(empty_csv)
        assert entries == []


class TestExfiltrationDetection:
    """Test forensic queries for exfiltration detection."""

    @pytest.fixture
    def parser(self):
        return M365LogParser(date_format="AU")

    @pytest.fixture
    def sample_csv_path(self, tmp_path):
        csv_file = tmp_path / "13_TransportRules.csv"
        csv_file.write_text(SAMPLE_TRANSPORT_RULES_CSV, encoding='utf-8')
        return csv_file

    def test_detect_external_forwarding(self, parser, sample_csv_path):
        """Should detect rules forwarding to external domains."""
        entries = parser.parse_transport_rules(sample_csv_path)

        # Filter for external forwarding IOCs
        external_forwarding = [
            e for e in entries
            if e.redirect_message_to or e.blind_copy_to or e.copy_to
        ]

        assert len(external_forwarding) == 1
        assert "letlucy.biz" in external_forwarding[0].redirect_message_to

    def test_detect_spam_bypass_rules(self, parser, sample_csv_path):
        """Should detect rules that bypass spam filtering (SCL=-1)."""
        entries = parser.parse_transport_rules(sample_csv_path)

        spam_bypass = [e for e in entries if e.set_scl == -1]
        assert len(spam_bypass) == 2


class TestDiscoverLogFiles:
    """Test that discover_log_files() finds transport rules."""

    def test_discover_includes_transport_rules(self, tmp_path):
        """discover_log_files() should find transport rules CSV."""
        # Create a mock export directory
        (tmp_path / "13_TransportRules.csv").write_text("Name,State\nTest,Enabled\n")
        (tmp_path / "01_SignInLogs.csv").write_text("CreatedDateTime\n")

        parser = M365LogParser(date_format="AU")
        discovered = parser.discover_log_files(tmp_path)

        assert LogType.TRANSPORT_RULES in discovered
        assert discovered[LogType.TRANSPORT_RULES].name == "13_TransportRules.csv"


class TestRealDataParsing:
    """Test with actual FYNA data if available."""

    FYNA_DATA_PATH = Path("/tmp/fyna_extract/TenantWide_Investigation_20260108_083839/13_TransportRules.csv")

    @pytest.mark.skipif(
        not FYNA_DATA_PATH.exists(),
        reason="FYNA sample data not available"
    )
    def test_parse_real_fyna_data(self):
        """Parse actual FYNA transport rules data."""
        parser = M365LogParser(date_format="AU")
        entries = parser.parse_transport_rules(self.FYNA_DATA_PATH)

        # FYNA has 8 transport rules
        assert len(entries) == 8

        # Verify known exfiltration rule exists
        exfil_rules = [
            e for e in entries
            if "letlucy.biz" in (e.redirect_message_to or "")
        ]
        assert len(exfil_rules) == 1
        assert exfil_rules[0].state == "Enabled"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
