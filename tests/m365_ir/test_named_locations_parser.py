#!/usr/bin/env python3
"""
TDD Tests for NamedLocations Parser

Priority 6: Geographic/IP-based access control locations
Used in Conditional Access policies

Test data: /tmp/fyna_extract/TenantWide_Investigation_20260108_083839/11_NamedLocations.csv
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
# Columns: DisplayName,Id,CreatedDateTime,ModifiedDateTime,Type,IsTrusted,IpRanges,CountriesAndRegions
SAMPLE_NAMED_LOCATIONS_CSV = '''"DisplayName","Id","CreatedDateTime","ModifiedDateTime","Type","IsTrusted","IpRanges","CountriesAndRegions"
"Block all except AU + COB","18a72932-ea12-4aa6-ac77-102ad2fe9b8a","18/12/2025 12:31:37 AM","18/12/2025 12:32:46 AM","#microsoft.graph.countryNamedLocation","","","AU; NZ; SG"
"Trusted Office IPs","abc12345-1234-5678-abcd-123456789abc","18/12/2025 12:31:37 AM","18/12/2025 12:32:46 AM","#microsoft.graph.ipNamedLocation","True","10.0.0.0/8; 192.168.1.0/24",""
'''


class TestLogTypeEnum:
    """Test that NAMED_LOCATIONS is in LogType enum."""

    def test_named_locations_in_enum(self):
        """LogType enum should include NAMED_LOCATIONS."""
        assert hasattr(LogType, 'NAMED_LOCATIONS')
        assert LogType.NAMED_LOCATIONS.value == "named_locations"


class TestFilePatternMatching:
    """Test file pattern matching for named locations CSV."""

    def test_pattern_matches_numbered_format(self):
        """Pattern should match '11_NamedLocations.csv' format."""
        import re
        pattern = LOG_FILE_PATTERNS.get(LogType.NAMED_LOCATIONS)
        assert pattern is not None, "NAMED_LOCATIONS pattern not in LOG_FILE_PATTERNS"

        assert re.match(pattern, "11_NamedLocations.csv")
        assert re.match(pattern, "11_FynaFoods_NamedLocations.csv")

    def test_pattern_rejects_non_named_location_files(self):
        """Pattern should not match other log types."""
        import re
        pattern = LOG_FILE_PATTERNS.get(LogType.NAMED_LOCATIONS)
        assert pattern is not None

        assert not re.match(pattern, "01_SignInLogs.csv")
        assert not re.match(pattern, "10_ConditionalAccessPolicies.csv")


class TestNamedLocationEntryDataclass:
    """Test NamedLocationEntry dataclass structure."""

    def test_dataclass_has_required_fields(self):
        """NamedLocationEntry should have all required fields."""
        from claude.tools.m365_ir.m365_log_parser import NamedLocationEntry

        required_fields = [
            'display_name', 'location_id', 'created_datetime',
            'modified_datetime', 'location_type', 'is_trusted',
            'ip_ranges', 'countries_and_regions', 'raw_record'
        ]

        entry_fields = [f.name for f in NamedLocationEntry.__dataclass_fields__.values()]
        for field in required_fields:
            assert field in entry_fields, f"Missing field: {field}"

    def test_dataclass_is_hashable(self):
        """NamedLocationEntry should be hashable."""
        from claude.tools.m365_ir.m365_log_parser import NamedLocationEntry

        entry = NamedLocationEntry(
            display_name="Test Location",
            location_id="test-id",
            created_datetime=None,
            modified_datetime=None,
            location_type="countryNamedLocation",
            is_trusted=False,
            ip_ranges="",
            countries_and_regions="AU",
            raw_record=""
        )
        hash(entry)


class TestNamedLocationsParser:
    """Test M365LogParser.parse_named_locations() method."""

    @pytest.fixture
    def parser(self):
        return M365LogParser(date_format="AU")

    @pytest.fixture
    def sample_csv_path(self, tmp_path):
        csv_file = tmp_path / "11_NamedLocations.csv"
        csv_file.write_text(SAMPLE_NAMED_LOCATIONS_CSV, encoding='utf-8')
        return csv_file

    def test_parse_returns_list_of_entries(self, parser, sample_csv_path):
        """Parser should return list of NamedLocationEntry objects."""
        entries = parser.parse_named_locations(sample_csv_path)

        assert isinstance(entries, list)
        assert len(entries) == 2

        from claude.tools.m365_ir.m365_log_parser import NamedLocationEntry
        assert all(isinstance(e, NamedLocationEntry) for e in entries)

    def test_parse_extracts_display_name(self, parser, sample_csv_path):
        """Parser should extract display name correctly."""
        entries = parser.parse_named_locations(sample_csv_path)

        assert entries[0].display_name == "Block all except AU + COB"
        assert entries[1].display_name == "Trusted Office IPs"

    def test_parse_extracts_location_type(self, parser, sample_csv_path):
        """Parser should extract location type."""
        entries = parser.parse_named_locations(sample_csv_path)

        assert "countryNamedLocation" in entries[0].location_type
        assert "ipNamedLocation" in entries[1].location_type

    def test_parse_extracts_is_trusted(self, parser, sample_csv_path):
        """Parser should parse IsTrusted boolean."""
        entries = parser.parse_named_locations(sample_csv_path)

        assert entries[0].is_trusted is False
        assert entries[1].is_trusted is True

    def test_parse_extracts_countries(self, parser, sample_csv_path):
        """Parser should extract countries and regions."""
        entries = parser.parse_named_locations(sample_csv_path)

        assert "AU" in entries[0].countries_and_regions
        assert entries[1].countries_and_regions == ""

    def test_parse_extracts_ip_ranges(self, parser, sample_csv_path):
        """Parser should extract IP ranges."""
        entries = parser.parse_named_locations(sample_csv_path)

        assert entries[0].ip_ranges == ""
        assert "10.0.0.0/8" in entries[1].ip_ranges

    def test_parse_handles_empty_file(self, parser, tmp_path):
        """Parser should handle empty CSV gracefully."""
        empty_csv = tmp_path / "11_NamedLocations.csv"
        empty_csv.write_text('"DisplayName","Id","CreatedDateTime","ModifiedDateTime","Type","IsTrusted","IpRanges","CountriesAndRegions"\n')

        entries = parser.parse_named_locations(empty_csv)
        assert entries == []


class TestDiscoverLogFiles:
    """Test that discover_log_files() finds named locations."""

    def test_discover_includes_named_locations(self, tmp_path):
        """discover_log_files() should find named locations CSV."""
        (tmp_path / "11_NamedLocations.csv").write_text('"DisplayName","Id"\n"Test","id"\n')

        parser = M365LogParser(date_format="AU")
        discovered = parser.discover_log_files(tmp_path)

        assert LogType.NAMED_LOCATIONS in discovered


class TestRealDataParsing:
    """Test with actual FYNA data if available."""

    FYNA_DATA_PATH = Path("/tmp/fyna_extract/TenantWide_Investigation_20260108_083839/11_NamedLocations.csv")

    @pytest.mark.skipif(
        not FYNA_DATA_PATH.exists(),
        reason="FYNA sample data not available"
    )
    def test_parse_real_fyna_data(self):
        """Parse actual FYNA named locations data."""
        parser = M365LogParser(date_format="AU")
        entries = parser.parse_named_locations(self.FYNA_DATA_PATH)

        # FYNA has 1 named location
        assert len(entries) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
