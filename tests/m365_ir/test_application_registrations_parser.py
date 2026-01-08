#!/usr/bin/env python3
"""
TDD Tests for ApplicationRegistrations Parser

Priority 7: Entra ID app registrations
MITRE: T1098.001 (Account Manipulation: Additional Cloud Credentials)

Test data: /tmp/fyna_extract/TenantWide_Investigation_20260108_083839/16_ApplicationRegistrations.csv
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
# Columns: DisplayName,AppId,Id,CreatedDateTime,SignInAudience,PublisherDomain,RequiredResourceAccess,PasswordCredentials,KeyCredentials,Web_RedirectUris
SAMPLE_APP_REGISTRATIONS_CSV = '''"DisplayName","AppId","Id","CreatedDateTime","SignInAudience","PublisherDomain","RequiredResourceAccess","PasswordCredentials","KeyCredentials","Web_RedirectUris"
"Azure-physical4b06authandaccessaadapp","ecb566e3-65ee-489c-862a-6d50e4c0f0e0","0d29ca9f-9595-4fa7-8787-2c45002c8d6d","3/05/2023 2:28:59 AM","AzureADMyOrg","fyna.com.au","",,,""
"backupradar.com","2218fab9-d52f-4178-b7dd-44bc8b5d0a8c","2eb95f9c-64db-485e-8b9a-a79c8fcff2bb","28/07/2023 5:26:11 AM","AzureADMyOrg","fyna.com.au","{""ResourceAccess"":[{""Id"":""e1fe6dd8""}]}",,,"https://backupradar.com/"
'''


class TestLogTypeEnum:
    """Test that APPLICATION_REGISTRATIONS is in LogType enum."""

    def test_application_registrations_in_enum(self):
        """LogType enum should include APPLICATION_REGISTRATIONS."""
        assert hasattr(LogType, 'APPLICATION_REGISTRATIONS')
        assert LogType.APPLICATION_REGISTRATIONS.value == "application_registrations"


class TestFilePatternMatching:
    """Test file pattern matching for app registrations CSV."""

    def test_pattern_matches_numbered_format(self):
        """Pattern should match '16_ApplicationRegistrations.csv' format."""
        import re
        pattern = LOG_FILE_PATTERNS.get(LogType.APPLICATION_REGISTRATIONS)
        assert pattern is not None, "APPLICATION_REGISTRATIONS pattern not in LOG_FILE_PATTERNS"

        assert re.match(pattern, "16_ApplicationRegistrations.csv")
        assert re.match(pattern, "16_FynaFoods_ApplicationRegistrations.csv")

    def test_pattern_rejects_non_app_registration_files(self):
        """Pattern should not match other log types."""
        import re
        pattern = LOG_FILE_PATTERNS.get(LogType.APPLICATION_REGISTRATIONS)
        assert pattern is not None

        assert not re.match(pattern, "01_SignInLogs.csv")
        assert not re.match(pattern, "17_ServicePrincipals.csv")


class TestApplicationRegistrationEntryDataclass:
    """Test ApplicationRegistrationEntry dataclass structure."""

    def test_dataclass_has_required_fields(self):
        """ApplicationRegistrationEntry should have all required fields."""
        from claude.tools.m365_ir.m365_log_parser import ApplicationRegistrationEntry

        required_fields = [
            'display_name', 'app_id', 'object_id', 'created_datetime',
            'sign_in_audience', 'publisher_domain', 'required_resource_access',
            'password_credentials', 'key_credentials', 'web_redirect_uris', 'raw_record'
        ]

        entry_fields = [f.name for f in ApplicationRegistrationEntry.__dataclass_fields__.values()]
        for field in required_fields:
            assert field in entry_fields, f"Missing field: {field}"

    def test_dataclass_is_hashable(self):
        """ApplicationRegistrationEntry should be hashable."""
        from claude.tools.m365_ir.m365_log_parser import ApplicationRegistrationEntry

        entry = ApplicationRegistrationEntry(
            display_name="Test App",
            app_id="test-app-id",
            object_id="test-object-id",
            created_datetime=None,
            sign_in_audience="AzureADMyOrg",
            publisher_domain="example.com",
            required_resource_access="",
            password_credentials="",
            key_credentials="",
            web_redirect_uris="",
            raw_record=""
        )
        hash(entry)


class TestApplicationRegistrationsParser:
    """Test M365LogParser.parse_application_registrations() method."""

    @pytest.fixture
    def parser(self):
        return M365LogParser(date_format="AU")

    @pytest.fixture
    def sample_csv_path(self, tmp_path):
        csv_file = tmp_path / "16_ApplicationRegistrations.csv"
        csv_file.write_text(SAMPLE_APP_REGISTRATIONS_CSV, encoding='utf-8')
        return csv_file

    def test_parse_returns_list_of_entries(self, parser, sample_csv_path):
        """Parser should return list of ApplicationRegistrationEntry objects."""
        entries = parser.parse_application_registrations(sample_csv_path)

        assert isinstance(entries, list)
        assert len(entries) == 2

        from claude.tools.m365_ir.m365_log_parser import ApplicationRegistrationEntry
        assert all(isinstance(e, ApplicationRegistrationEntry) for e in entries)

    def test_parse_extracts_display_name(self, parser, sample_csv_path):
        """Parser should extract display name correctly."""
        entries = parser.parse_application_registrations(sample_csv_path)

        assert entries[0].display_name == "Azure-physical4b06authandaccessaadapp"
        assert entries[1].display_name == "backupradar.com"

    def test_parse_extracts_app_id(self, parser, sample_csv_path):
        """Parser should extract application ID (client ID)."""
        entries = parser.parse_application_registrations(sample_csv_path)

        assert entries[0].app_id == "ecb566e3-65ee-489c-862a-6d50e4c0f0e0"

    def test_parse_extracts_sign_in_audience(self, parser, sample_csv_path):
        """Parser should extract sign-in audience."""
        entries = parser.parse_application_registrations(sample_csv_path)

        assert entries[0].sign_in_audience == "AzureADMyOrg"

    def test_parse_extracts_publisher_domain(self, parser, sample_csv_path):
        """Parser should extract publisher domain."""
        entries = parser.parse_application_registrations(sample_csv_path)

        assert entries[0].publisher_domain == "fyna.com.au"

    def test_parse_extracts_redirect_uris(self, parser, sample_csv_path):
        """Parser should extract web redirect URIs."""
        entries = parser.parse_application_registrations(sample_csv_path)

        assert entries[0].web_redirect_uris == ""
        assert "backupradar.com" in entries[1].web_redirect_uris

    def test_parse_handles_empty_file(self, parser, tmp_path):
        """Parser should handle empty CSV gracefully."""
        empty_csv = tmp_path / "16_ApplicationRegistrations.csv"
        empty_csv.write_text('"DisplayName","AppId","Id","CreatedDateTime","SignInAudience","PublisherDomain","RequiredResourceAccess","PasswordCredentials","KeyCredentials","Web_RedirectUris"\n')

        entries = parser.parse_application_registrations(empty_csv)
        assert entries == []


class TestCredentialDetection:
    """Test forensic queries for credential detection."""

    @pytest.fixture
    def parser(self):
        return M365LogParser(date_format="AU")

    @pytest.fixture
    def sample_csv_path(self, tmp_path):
        csv_file = tmp_path / "16_ApplicationRegistrations.csv"
        csv_file.write_text(SAMPLE_APP_REGISTRATIONS_CSV, encoding='utf-8')
        return csv_file

    def test_detect_apps_with_api_permissions(self, parser, sample_csv_path):
        """Should detect apps with required resource access."""
        entries = parser.parse_application_registrations(sample_csv_path)

        with_permissions = [e for e in entries if e.required_resource_access]
        assert len(with_permissions) == 1


class TestDiscoverLogFiles:
    """Test that discover_log_files() finds app registrations."""

    def test_discover_includes_app_registrations(self, tmp_path):
        """discover_log_files() should find app registrations CSV."""
        (tmp_path / "16_ApplicationRegistrations.csv").write_text('"DisplayName","AppId"\n"Test","id"\n')

        parser = M365LogParser(date_format="AU")
        discovered = parser.discover_log_files(tmp_path)

        assert LogType.APPLICATION_REGISTRATIONS in discovered


class TestRealDataParsing:
    """Test with actual FYNA data if available."""

    FYNA_DATA_PATH = Path("/tmp/fyna_extract/TenantWide_Investigation_20260108_083839/16_ApplicationRegistrations.csv")

    @pytest.mark.skipif(
        not FYNA_DATA_PATH.exists(),
        reason="FYNA sample data not available"
    )
    def test_parse_real_fyna_data(self):
        """Parse actual FYNA app registrations data."""
        parser = M365LogParser(date_format="AU")
        entries = parser.parse_application_registrations(self.FYNA_DATA_PATH)

        # FYNA has 8 app registrations
        assert len(entries) == 8


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
