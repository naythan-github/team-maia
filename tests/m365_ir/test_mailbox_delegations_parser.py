#!/usr/bin/env python3
"""
TDD Tests for MailboxDelegations Parser

Priority 3: Mailbox access permissions mapping
MITRE: T1098.002 (Account Manipulation: Exchange Email Delegate)

Test data: /tmp/fyna_extract/TenantWide_Investigation_20260108_083839/14_MailboxDelegations.csv
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
# Columns: Mailbox,PermissionType,Delegate,AccessRights,IsInherited
SAMPLE_MAILBOX_DELEGATIONS_CSV = '''"Mailbox","PermissionType","Delegate","AccessRights","IsInherited"
"accountspayable@fyna.com.au","FullAccess","KarenA@fyna.com.au","FullAccess","False"
"sales@fyna.com.au","SendAs","admin@fyna.com.au","SendAs","True"
"ceo@fyna.com.au","SendOnBehalf","assistant@fyna.com.au","SendOnBehalf","False"
'''


class TestLogTypeEnum:
    """Test that MAILBOX_DELEGATIONS is in LogType enum."""

    def test_mailbox_delegations_in_enum(self):
        """LogType enum should include MAILBOX_DELEGATIONS."""
        assert hasattr(LogType, 'MAILBOX_DELEGATIONS')
        assert LogType.MAILBOX_DELEGATIONS.value == "mailbox_delegations"


class TestFilePatternMatching:
    """Test file pattern matching for mailbox delegations CSV."""

    def test_pattern_matches_numbered_format(self):
        """Pattern should match '14_MailboxDelegations.csv' format."""
        import re
        pattern = LOG_FILE_PATTERNS.get(LogType.MAILBOX_DELEGATIONS)
        assert pattern is not None, "MAILBOX_DELEGATIONS pattern not in LOG_FILE_PATTERNS"

        # Test various filename formats
        assert re.match(pattern, "14_MailboxDelegations.csv")
        assert re.match(pattern, "14_FynaFoods_MailboxDelegations.csv")

    def test_pattern_rejects_non_delegation_files(self):
        """Pattern should not match other log types."""
        import re
        pattern = LOG_FILE_PATTERNS.get(LogType.MAILBOX_DELEGATIONS)
        assert pattern is not None

        assert not re.match(pattern, "01_SignInLogs.csv")
        assert not re.match(pattern, "13_TransportRules.csv")


class TestMailboxDelegationEntryDataclass:
    """Test MailboxDelegationEntry dataclass structure."""

    def test_dataclass_has_required_fields(self):
        """MailboxDelegationEntry should have all required fields."""
        from claude.tools.m365_ir.m365_log_parser import MailboxDelegationEntry

        required_fields = [
            'mailbox', 'permission_type', 'delegate',
            'access_rights', 'is_inherited', 'raw_record'
        ]

        entry_fields = [f.name for f in MailboxDelegationEntry.__dataclass_fields__.values()]
        for field in required_fields:
            assert field in entry_fields, f"Missing field: {field}"

    def test_dataclass_is_hashable(self):
        """MailboxDelegationEntry should be hashable for set operations."""
        from claude.tools.m365_ir.m365_log_parser import MailboxDelegationEntry

        entry = MailboxDelegationEntry(
            mailbox="test@example.com",
            permission_type="FullAccess",
            delegate="delegate@example.com",
            access_rights="FullAccess",
            is_inherited=False,
            raw_record=""
        )
        # Should not raise
        hash(entry)


class TestMailboxDelegationsParser:
    """Test M365LogParser.parse_mailbox_delegations() method."""

    @pytest.fixture
    def parser(self):
        """Create parser instance with AU date format."""
        return M365LogParser(date_format="AU")

    @pytest.fixture
    def sample_csv_path(self, tmp_path):
        """Create sample CSV file for testing."""
        csv_file = tmp_path / "14_MailboxDelegations.csv"
        csv_file.write_text(SAMPLE_MAILBOX_DELEGATIONS_CSV, encoding='utf-8')
        return csv_file

    def test_parse_returns_list_of_entries(self, parser, sample_csv_path):
        """Parser should return list of MailboxDelegationEntry objects."""
        entries = parser.parse_mailbox_delegations(sample_csv_path)

        assert isinstance(entries, list)
        assert len(entries) == 3  # 3 delegations in sample data

        from claude.tools.m365_ir.m365_log_parser import MailboxDelegationEntry
        assert all(isinstance(e, MailboxDelegationEntry) for e in entries)

    def test_parse_extracts_mailbox(self, parser, sample_csv_path):
        """Parser should extract mailbox correctly."""
        entries = parser.parse_mailbox_delegations(sample_csv_path)

        assert entries[0].mailbox == "accountspayable@fyna.com.au"
        assert entries[1].mailbox == "sales@fyna.com.au"

    def test_parse_extracts_permission_type(self, parser, sample_csv_path):
        """Parser should extract permission type."""
        entries = parser.parse_mailbox_delegations(sample_csv_path)

        assert entries[0].permission_type == "FullAccess"
        assert entries[1].permission_type == "SendAs"
        assert entries[2].permission_type == "SendOnBehalf"

    def test_parse_extracts_delegate(self, parser, sample_csv_path):
        """Parser should extract delegate (who has access)."""
        entries = parser.parse_mailbox_delegations(sample_csv_path)

        assert entries[0].delegate == "KarenA@fyna.com.au"
        assert entries[1].delegate == "admin@fyna.com.au"

    def test_parse_extracts_is_inherited(self, parser, sample_csv_path):
        """Parser should parse IsInherited boolean."""
        entries = parser.parse_mailbox_delegations(sample_csv_path)

        assert entries[0].is_inherited is False
        assert entries[1].is_inherited is True
        assert entries[2].is_inherited is False

    def test_parse_handles_empty_file(self, parser, tmp_path):
        """Parser should handle empty CSV gracefully."""
        empty_csv = tmp_path / "14_MailboxDelegations.csv"
        empty_csv.write_text('"Mailbox","PermissionType","Delegate","AccessRights","IsInherited"\n')

        entries = parser.parse_mailbox_delegations(empty_csv)
        assert entries == []


class TestDelegationDetection:
    """Test forensic queries for delegation detection."""

    @pytest.fixture
    def parser(self):
        return M365LogParser(date_format="AU")

    @pytest.fixture
    def sample_csv_path(self, tmp_path):
        csv_file = tmp_path / "14_MailboxDelegations.csv"
        csv_file.write_text(SAMPLE_MAILBOX_DELEGATIONS_CSV, encoding='utf-8')
        return csv_file

    def test_detect_full_access_delegations(self, parser, sample_csv_path):
        """Should detect FullAccess delegations (highest risk)."""
        entries = parser.parse_mailbox_delegations(sample_csv_path)

        full_access = [e for e in entries if e.permission_type == "FullAccess"]
        assert len(full_access) == 1
        assert full_access[0].delegate == "KarenA@fyna.com.au"

    def test_detect_sendas_delegations(self, parser, sample_csv_path):
        """Should detect SendAs delegations (impersonation risk)."""
        entries = parser.parse_mailbox_delegations(sample_csv_path)

        send_as = [e for e in entries if e.permission_type == "SendAs"]
        assert len(send_as) == 1


class TestDiscoverLogFiles:
    """Test that discover_log_files() finds mailbox delegations."""

    def test_discover_includes_mailbox_delegations(self, tmp_path):
        """discover_log_files() should find mailbox delegations CSV."""
        # Create a mock export directory
        (tmp_path / "14_MailboxDelegations.csv").write_text('"Mailbox","PermissionType"\n"test@example.com","FullAccess"\n')
        (tmp_path / "01_SignInLogs.csv").write_text("CreatedDateTime\n")

        parser = M365LogParser(date_format="AU")
        discovered = parser.discover_log_files(tmp_path)

        assert LogType.MAILBOX_DELEGATIONS in discovered
        assert discovered[LogType.MAILBOX_DELEGATIONS].name == "14_MailboxDelegations.csv"


class TestRealDataParsing:
    """Test with actual FYNA data if available."""

    FYNA_DATA_PATH = Path("/tmp/fyna_extract/TenantWide_Investigation_20260108_083839/14_MailboxDelegations.csv")

    @pytest.mark.skipif(
        not FYNA_DATA_PATH.exists(),
        reason="FYNA sample data not available"
    )
    def test_parse_real_fyna_data(self):
        """Parse actual FYNA mailbox delegations data."""
        parser = M365LogParser(date_format="AU")
        entries = parser.parse_mailbox_delegations(self.FYNA_DATA_PATH)

        # FYNA has 62 mailbox delegations (from prior analysis)
        assert len(entries) == 62

        # Verify we have FullAccess delegations
        full_access = [e for e in entries if e.permission_type == "FullAccess"]
        assert len(full_access) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
