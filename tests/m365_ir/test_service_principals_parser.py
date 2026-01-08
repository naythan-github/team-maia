#!/usr/bin/env python3
"""
TDD Tests for ServicePrincipals Parser

Priority 8: Enterprise applications - local instances of apps
Test data: /tmp/fyna_extract/TenantWide_Investigation_20260108_083839/17_ServicePrincipals.csv
"""

import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from claude.tools.m365_ir.m365_log_parser import (
    M365LogParser,
    LogType,
    LOG_FILE_PATTERNS,
)


# Sample CSV data matching FYNA export format
# Columns: DisplayName,AppId,Id,ServicePrincipalType,AccountEnabled,CreatedDateTime,AppOwnerOrganizationId,ReplyUrls,Tags
SAMPLE_SERVICE_PRINCIPALS_CSV = '''"DisplayName","AppId","Id","ServicePrincipalType","AccountEnabled","CreatedDateTime","AppOwnerOrganizationId","ReplyUrls","Tags"
"Microsoft Discovery Service","6f82282e-0070-4e78-bc23-e6320c5fa7de","000b0037-a2a0-49c4-bb14-bb7aa668ae1a","Application","True",,"f8cdef31-a31e-4b4a-93e4-5f571e91255a","",""
"Power Platform Environment Discovery","3e36f539-fc2c-479c-90fb-3cfa21da3a4b","00127b1d-919a-4c38-a9dd-277f0a7d72a1","Application","False",,"f8cdef31-a31e-4b4a-93e4-5f571e91255a","",""
"Custom ManagedIdentity App","aaaabbbb-cccc-dddd-eeee-ffffffffffff","12345678-1234-5678-abcd-123456789abc","ManagedIdentity","True","1/01/2024 10:00:00 AM","tenant-id","https://example.com/callback","HideApp"
'''


class TestLogTypeEnum:
    """Test that SERVICE_PRINCIPALS is in LogType enum."""

    def test_service_principals_in_enum(self):
        """LogType enum should include SERVICE_PRINCIPALS."""
        assert hasattr(LogType, 'SERVICE_PRINCIPALS')
        assert LogType.SERVICE_PRINCIPALS.value == "service_principals"


class TestFilePatternMatching:
    """Test file pattern matching for service principals CSV."""

    def test_pattern_matches_numbered_format(self):
        """Pattern should match '17_ServicePrincipals.csv' format."""
        import re
        pattern = LOG_FILE_PATTERNS.get(LogType.SERVICE_PRINCIPALS)
        assert pattern is not None, "SERVICE_PRINCIPALS pattern not in LOG_FILE_PATTERNS"

        assert re.match(pattern, "17_ServicePrincipals.csv")
        assert re.match(pattern, "17_FynaFoods_ServicePrincipals.csv")

    def test_pattern_rejects_non_service_principal_files(self):
        """Pattern should not match other log types."""
        import re
        pattern = LOG_FILE_PATTERNS.get(LogType.SERVICE_PRINCIPALS)
        assert pattern is not None

        assert not re.match(pattern, "01_SignInLogs.csv")
        assert not re.match(pattern, "16_ApplicationRegistrations.csv")


class TestServicePrincipalEntryDataclass:
    """Test ServicePrincipalEntry dataclass structure."""

    def test_dataclass_has_required_fields(self):
        """ServicePrincipalEntry should have all required fields."""
        from claude.tools.m365_ir.m365_log_parser import ServicePrincipalEntry

        required_fields = [
            'display_name', 'app_id', 'object_id', 'service_principal_type',
            'account_enabled', 'created_datetime', 'app_owner_organization_id',
            'reply_urls', 'tags', 'raw_record'
        ]

        entry_fields = [f.name for f in ServicePrincipalEntry.__dataclass_fields__.values()]
        for field in required_fields:
            assert field in entry_fields, f"Missing field: {field}"

    def test_dataclass_is_hashable(self):
        """ServicePrincipalEntry should be hashable."""
        from claude.tools.m365_ir.m365_log_parser import ServicePrincipalEntry

        entry = ServicePrincipalEntry(
            display_name="Test App",
            app_id="test-app-id",
            object_id="test-object-id",
            service_principal_type="Application",
            account_enabled=True,
            created_datetime=None,
            app_owner_organization_id="tenant-id",
            reply_urls="",
            tags="",
            raw_record=""
        )
        hash(entry)


class TestServicePrincipalsParser:
    """Test M365LogParser.parse_service_principals() method."""

    @pytest.fixture
    def parser(self):
        return M365LogParser(date_format="AU")

    @pytest.fixture
    def sample_csv_path(self, tmp_path):
        csv_file = tmp_path / "17_ServicePrincipals.csv"
        csv_file.write_text(SAMPLE_SERVICE_PRINCIPALS_CSV, encoding='utf-8')
        return csv_file

    def test_parse_returns_list_of_entries(self, parser, sample_csv_path):
        """Parser should return list of ServicePrincipalEntry objects."""
        entries = parser.parse_service_principals(sample_csv_path)

        assert isinstance(entries, list)
        assert len(entries) == 3

        from claude.tools.m365_ir.m365_log_parser import ServicePrincipalEntry
        assert all(isinstance(e, ServicePrincipalEntry) for e in entries)

    def test_parse_extracts_display_name(self, parser, sample_csv_path):
        """Parser should extract display name correctly."""
        entries = parser.parse_service_principals(sample_csv_path)

        assert entries[0].display_name == "Microsoft Discovery Service"
        assert entries[1].display_name == "Power Platform Environment Discovery"

    def test_parse_extracts_service_principal_type(self, parser, sample_csv_path):
        """Parser should extract service principal type."""
        entries = parser.parse_service_principals(sample_csv_path)

        assert entries[0].service_principal_type == "Application"
        assert entries[2].service_principal_type == "ManagedIdentity"

    def test_parse_extracts_account_enabled(self, parser, sample_csv_path):
        """Parser should parse AccountEnabled boolean."""
        entries = parser.parse_service_principals(sample_csv_path)

        assert entries[0].account_enabled is True
        assert entries[1].account_enabled is False

    def test_parse_extracts_app_owner_org(self, parser, sample_csv_path):
        """Parser should extract app owner organization ID."""
        entries = parser.parse_service_principals(sample_csv_path)

        assert entries[0].app_owner_organization_id == "f8cdef31-a31e-4b4a-93e4-5f571e91255a"

    def test_parse_extracts_tags(self, parser, sample_csv_path):
        """Parser should extract tags."""
        entries = parser.parse_service_principals(sample_csv_path)

        assert entries[0].tags == ""
        assert entries[2].tags == "HideApp"

    def test_parse_handles_empty_file(self, parser, tmp_path):
        """Parser should handle empty CSV gracefully."""
        empty_csv = tmp_path / "17_ServicePrincipals.csv"
        empty_csv.write_text('"DisplayName","AppId","Id","ServicePrincipalType","AccountEnabled","CreatedDateTime","AppOwnerOrganizationId","ReplyUrls","Tags"\n')

        entries = parser.parse_service_principals(empty_csv)
        assert entries == []


class TestServicePrincipalDetection:
    """Test forensic queries for service principal analysis."""

    @pytest.fixture
    def parser(self):
        return M365LogParser(date_format="AU")

    @pytest.fixture
    def sample_csv_path(self, tmp_path):
        csv_file = tmp_path / "17_ServicePrincipals.csv"
        csv_file.write_text(SAMPLE_SERVICE_PRINCIPALS_CSV, encoding='utf-8')
        return csv_file

    def test_detect_disabled_service_principals(self, parser, sample_csv_path):
        """Should detect disabled service principals."""
        entries = parser.parse_service_principals(sample_csv_path)

        disabled = [e for e in entries if not e.account_enabled]
        assert len(disabled) == 1

    def test_detect_managed_identities(self, parser, sample_csv_path):
        """Should detect managed identity service principals."""
        entries = parser.parse_service_principals(sample_csv_path)

        managed = [e for e in entries if e.service_principal_type == "ManagedIdentity"]
        assert len(managed) == 1


class TestDiscoverLogFiles:
    """Test that discover_log_files() finds service principals."""

    def test_discover_includes_service_principals(self, tmp_path):
        """discover_log_files() should find service principals CSV."""
        (tmp_path / "17_ServicePrincipals.csv").write_text('"DisplayName","AppId"\n"Test","id"\n')

        parser = M365LogParser(date_format="AU")
        discovered = parser.discover_log_files(tmp_path)

        assert LogType.SERVICE_PRINCIPALS in discovered


class TestRealDataParsing:
    """Test with actual FYNA data if available."""

    FYNA_DATA_PATH = Path("/tmp/fyna_extract/TenantWide_Investigation_20260108_083839/17_ServicePrincipals.csv")

    @pytest.mark.skipif(
        not FYNA_DATA_PATH.exists(),
        reason="FYNA sample data not available"
    )
    def test_parse_real_fyna_data(self):
        """Parse actual FYNA service principals data."""
        parser = M365LogParser(date_format="AU")
        entries = parser.parse_service_principals(self.FYNA_DATA_PATH)

        # FYNA has 626 service principals
        assert len(entries) == 626


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
