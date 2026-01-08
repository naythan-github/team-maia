#!/usr/bin/env python3
"""
TDD Tests for ConditionalAccessPolicies Parser

Priority 5: Security policy configuration
MITRE: T1562.001 (Impair Defenses: Disable or Modify Tools)

Test data: /tmp/fyna_extract/TenantWide_Investigation_20260108_083839/10_ConditionalAccessPolicies.csv
"""

import pytest
import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from claude.tools.m365_ir.m365_log_parser import (
    M365LogParser,
    LogType,
    LOG_FILE_PATTERNS,
)


# Sample CSV data matching FYNA export format
# Columns: DisplayName,Id,State,CreatedDateTime,ModifiedDateTime,Conditions,GrantControls,SessionControls
# Note: JSON in CSV cells uses doubled quotes for escaping
SAMPLE_CA_POLICIES_CSV = '''"DisplayName","Id","State","CreatedDateTime","ModifiedDateTime","Conditions","GrantControls","SessionControls"
"Baseline - Block legacy authentication","069d431d-4031-4445-a904-b59f61ff70c0","enabled","18/12/2025 12:31:21 AM","18/12/2025 4:26:16 AM","{""ClientAppTypes"":[""exchangeActiveSync"",""other""]}","{""BuiltInControls"":[""block""]}","{}"
"Baseline - Geo-blocking outside Countries","9dbf3b53-bc07-48dc-8c70-d12d23b9ed8e","disabled","18/12/2025 12:31:57 AM","18/12/2025 4:26:26 AM","{""ClientAppTypes"":[""all""]}","{""BuiltInControls"":[""mfa""]}","{}"
'''


class TestLogTypeEnum:
    """Test that CONDITIONAL_ACCESS_POLICIES is in LogType enum."""

    def test_conditional_access_policies_in_enum(self):
        """LogType enum should include CONDITIONAL_ACCESS_POLICIES."""
        assert hasattr(LogType, 'CONDITIONAL_ACCESS_POLICIES')
        assert LogType.CONDITIONAL_ACCESS_POLICIES.value == "conditional_access_policies"


class TestFilePatternMatching:
    """Test file pattern matching for CA policies CSV."""

    def test_pattern_matches_numbered_format(self):
        """Pattern should match '10_ConditionalAccessPolicies.csv' format."""
        import re
        pattern = LOG_FILE_PATTERNS.get(LogType.CONDITIONAL_ACCESS_POLICIES)
        assert pattern is not None, "CONDITIONAL_ACCESS_POLICIES pattern not in LOG_FILE_PATTERNS"

        assert re.match(pattern, "10_ConditionalAccessPolicies.csv")
        assert re.match(pattern, "10_FynaFoods_ConditionalAccessPolicies.csv")

    def test_pattern_rejects_non_ca_files(self):
        """Pattern should not match other log types."""
        import re
        pattern = LOG_FILE_PATTERNS.get(LogType.CONDITIONAL_ACCESS_POLICIES)
        assert pattern is not None

        assert not re.match(pattern, "01_SignInLogs.csv")
        assert not re.match(pattern, "11_NamedLocations.csv")


class TestConditionalAccessPolicyEntryDataclass:
    """Test ConditionalAccessPolicyEntry dataclass structure."""

    def test_dataclass_has_required_fields(self):
        """ConditionalAccessPolicyEntry should have all required fields."""
        from claude.tools.m365_ir.m365_log_parser import ConditionalAccessPolicyEntry

        required_fields = [
            'display_name', 'policy_id', 'state',
            'created_datetime', 'modified_datetime',
            'conditions', 'grant_controls', 'session_controls',
            'raw_record'
        ]

        entry_fields = [f.name for f in ConditionalAccessPolicyEntry.__dataclass_fields__.values()]
        for field in required_fields:
            assert field in entry_fields, f"Missing field: {field}"

    def test_dataclass_is_hashable(self):
        """ConditionalAccessPolicyEntry should be hashable."""
        from claude.tools.m365_ir.m365_log_parser import ConditionalAccessPolicyEntry

        entry = ConditionalAccessPolicyEntry(
            display_name="Test Policy",
            policy_id="test-id",
            state="enabled",
            created_datetime=None,
            modified_datetime=None,
            conditions="{}",
            grant_controls="{}",
            session_controls="{}",
            raw_record=""
        )
        hash(entry)


class TestConditionalAccessPoliciesParser:
    """Test M365LogParser.parse_conditional_access_policies() method."""

    @pytest.fixture
    def parser(self):
        return M365LogParser(date_format="AU")

    @pytest.fixture
    def sample_csv_path(self, tmp_path):
        csv_file = tmp_path / "10_ConditionalAccessPolicies.csv"
        csv_file.write_text(SAMPLE_CA_POLICIES_CSV, encoding='utf-8')
        return csv_file

    def test_parse_returns_list_of_entries(self, parser, sample_csv_path):
        """Parser should return list of ConditionalAccessPolicyEntry objects."""
        entries = parser.parse_conditional_access_policies(sample_csv_path)

        assert isinstance(entries, list)
        assert len(entries) == 2

        from claude.tools.m365_ir.m365_log_parser import ConditionalAccessPolicyEntry
        assert all(isinstance(e, ConditionalAccessPolicyEntry) for e in entries)

    def test_parse_extracts_display_name(self, parser, sample_csv_path):
        """Parser should extract display name correctly."""
        entries = parser.parse_conditional_access_policies(sample_csv_path)

        assert entries[0].display_name == "Baseline - Block legacy authentication"
        assert entries[1].display_name == "Baseline - Geo-blocking outside Countries"

    def test_parse_extracts_policy_id(self, parser, sample_csv_path):
        """Parser should extract policy ID (GUID)."""
        entries = parser.parse_conditional_access_policies(sample_csv_path)

        assert entries[0].policy_id == "069d431d-4031-4445-a904-b59f61ff70c0"

    def test_parse_extracts_state(self, parser, sample_csv_path):
        """Parser should extract state (enabled/disabled)."""
        entries = parser.parse_conditional_access_policies(sample_csv_path)

        assert entries[0].state == "enabled"
        assert entries[1].state == "disabled"

    def test_parse_extracts_grant_controls(self, parser, sample_csv_path):
        """Parser should extract grant controls JSON."""
        entries = parser.parse_conditional_access_policies(sample_csv_path)

        # Should be parseable JSON
        controls = json.loads(entries[0].grant_controls)
        assert "BuiltInControls" in controls
        assert "block" in controls["BuiltInControls"]

    def test_parse_handles_empty_file(self, parser, tmp_path):
        """Parser should handle empty CSV gracefully."""
        empty_csv = tmp_path / "10_ConditionalAccessPolicies.csv"
        empty_csv.write_text('"DisplayName","Id","State","CreatedDateTime","ModifiedDateTime","Conditions","GrantControls","SessionControls"\n')

        entries = parser.parse_conditional_access_policies(empty_csv)
        assert entries == []


class TestSecurityPolicyDetection:
    """Test forensic queries for security policy analysis."""

    @pytest.fixture
    def parser(self):
        return M365LogParser(date_format="AU")

    @pytest.fixture
    def sample_csv_path(self, tmp_path):
        csv_file = tmp_path / "10_ConditionalAccessPolicies.csv"
        csv_file.write_text(SAMPLE_CA_POLICIES_CSV, encoding='utf-8')
        return csv_file

    def test_detect_blocking_policies(self, parser, sample_csv_path):
        """Should detect policies that block access."""
        entries = parser.parse_conditional_access_policies(sample_csv_path)

        blocking = [
            e for e in entries
            if '"block"' in e.grant_controls.lower()
        ]
        assert len(blocking) == 1

    def test_detect_disabled_policies(self, parser, sample_csv_path):
        """Should detect disabled policies (potential security gap)."""
        entries = parser.parse_conditional_access_policies(sample_csv_path)

        disabled = [e for e in entries if e.state == "disabled"]
        assert len(disabled) == 1


class TestDiscoverLogFiles:
    """Test that discover_log_files() finds CA policies."""

    def test_discover_includes_ca_policies(self, tmp_path):
        """discover_log_files() should find CA policies CSV."""
        (tmp_path / "10_ConditionalAccessPolicies.csv").write_text('"DisplayName","Id"\n"Test","id"\n')

        parser = M365LogParser(date_format="AU")
        discovered = parser.discover_log_files(tmp_path)

        assert LogType.CONDITIONAL_ACCESS_POLICIES in discovered


class TestRealDataParsing:
    """Test with actual FYNA data if available."""

    FYNA_DATA_PATH = Path("/tmp/fyna_extract/TenantWide_Investigation_20260108_083839/10_ConditionalAccessPolicies.csv")

    @pytest.mark.skipif(
        not FYNA_DATA_PATH.exists(),
        reason="FYNA sample data not available"
    )
    def test_parse_real_fyna_data(self):
        """Parse actual FYNA CA policies data."""
        parser = M365LogParser(date_format="AU")
        entries = parser.parse_conditional_access_policies(self.FYNA_DATA_PATH)

        # FYNA has 2 CA policies
        assert len(entries) == 2

        # Verify known policy exists
        legacy_block = [e for e in entries if "legacy" in e.display_name.lower()]
        assert len(legacy_block) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
