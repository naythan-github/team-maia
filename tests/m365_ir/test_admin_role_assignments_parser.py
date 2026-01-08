#!/usr/bin/env python3
"""
TDD Tests for AdminRoleAssignments Parser

Priority 4: Privileged access mapping
MITRE: T1078.004 (Valid Accounts: Cloud), T1098 (Account Manipulation)

Test data: /tmp/fyna_extract/TenantWide_Investigation_20260108_083839/12_AdminRoleAssignments.csv
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
# Columns: RoleName,RoleId,RoleDescription,MemberDisplayName,MemberUPN,MemberId,MemberType
SAMPLE_ADMIN_ROLE_ASSIGNMENTS_CSV = '''"RoleName","RoleId","RoleDescription","MemberDisplayName","MemberUPN","MemberId","MemberType"
"Global Administrator","3bf20276-5595-40ef-96b1-d3ebc13273a0","Can manage all aspects of Microsoft Entra ID and Microsoft services that use Microsoft Entra identities.","NW Admin","nwadmin-az365@fyna.com.au","cde65995-892f-4db9-9a77-fb14719510ad","#microsoft.graph.user"
"Exchange Administrator","e8611ab8-c189-46e8-94e1-60213ab1f814","Can manage all aspects of the Exchange product.","Mail Admin","mailadmin@fyna.com.au","abc12345-678-90ab-cdef-111111111111","#microsoft.graph.user"
"Security Reader","5d6b6bb7-de71-4623-b4af-96380a352509","Can read security information and reports.","Audit Service","","svc12345-audit-principal","#microsoft.graph.servicePrincipal"
'''


class TestLogTypeEnum:
    """Test that ADMIN_ROLE_ASSIGNMENTS is in LogType enum."""

    def test_admin_role_assignments_in_enum(self):
        """LogType enum should include ADMIN_ROLE_ASSIGNMENTS."""
        assert hasattr(LogType, 'ADMIN_ROLE_ASSIGNMENTS')
        assert LogType.ADMIN_ROLE_ASSIGNMENTS.value == "admin_role_assignments"


class TestFilePatternMatching:
    """Test file pattern matching for admin role assignments CSV."""

    def test_pattern_matches_numbered_format(self):
        """Pattern should match '12_AdminRoleAssignments.csv' format."""
        import re
        pattern = LOG_FILE_PATTERNS.get(LogType.ADMIN_ROLE_ASSIGNMENTS)
        assert pattern is not None, "ADMIN_ROLE_ASSIGNMENTS pattern not in LOG_FILE_PATTERNS"

        # Test various filename formats
        assert re.match(pattern, "12_AdminRoleAssignments.csv")
        assert re.match(pattern, "12_FynaFoods_AdminRoleAssignments.csv")

    def test_pattern_rejects_non_admin_role_files(self):
        """Pattern should not match other log types."""
        import re
        pattern = LOG_FILE_PATTERNS.get(LogType.ADMIN_ROLE_ASSIGNMENTS)
        assert pattern is not None

        assert not re.match(pattern, "01_SignInLogs.csv")
        assert not re.match(pattern, "14_MailboxDelegations.csv")


class TestAdminRoleAssignmentEntryDataclass:
    """Test AdminRoleAssignmentEntry dataclass structure."""

    def test_dataclass_has_required_fields(self):
        """AdminRoleAssignmentEntry should have all required fields."""
        from claude.tools.m365_ir.m365_log_parser import AdminRoleAssignmentEntry

        required_fields = [
            'role_name', 'role_id', 'role_description',
            'member_display_name', 'member_upn', 'member_id',
            'member_type', 'raw_record'
        ]

        entry_fields = [f.name for f in AdminRoleAssignmentEntry.__dataclass_fields__.values()]
        for field in required_fields:
            assert field in entry_fields, f"Missing field: {field}"

    def test_dataclass_is_hashable(self):
        """AdminRoleAssignmentEntry should be hashable for set operations."""
        from claude.tools.m365_ir.m365_log_parser import AdminRoleAssignmentEntry

        entry = AdminRoleAssignmentEntry(
            role_name="Global Administrator",
            role_id="test-role-id",
            role_description="Test description",
            member_display_name="Test User",
            member_upn="test@example.com",
            member_id="test-member-id",
            member_type="#microsoft.graph.user",
            raw_record=""
        )
        # Should not raise
        hash(entry)


class TestAdminRoleAssignmentsParser:
    """Test M365LogParser.parse_admin_role_assignments() method."""

    @pytest.fixture
    def parser(self):
        """Create parser instance with AU date format."""
        return M365LogParser(date_format="AU")

    @pytest.fixture
    def sample_csv_path(self, tmp_path):
        """Create sample CSV file for testing."""
        csv_file = tmp_path / "12_AdminRoleAssignments.csv"
        csv_file.write_text(SAMPLE_ADMIN_ROLE_ASSIGNMENTS_CSV, encoding='utf-8')
        return csv_file

    def test_parse_returns_list_of_entries(self, parser, sample_csv_path):
        """Parser should return list of AdminRoleAssignmentEntry objects."""
        entries = parser.parse_admin_role_assignments(sample_csv_path)

        assert isinstance(entries, list)
        assert len(entries) == 3  # 3 assignments in sample data

        from claude.tools.m365_ir.m365_log_parser import AdminRoleAssignmentEntry
        assert all(isinstance(e, AdminRoleAssignmentEntry) for e in entries)

    def test_parse_extracts_role_name(self, parser, sample_csv_path):
        """Parser should extract role name correctly."""
        entries = parser.parse_admin_role_assignments(sample_csv_path)

        assert entries[0].role_name == "Global Administrator"
        assert entries[1].role_name == "Exchange Administrator"
        assert entries[2].role_name == "Security Reader"

    def test_parse_extracts_role_id(self, parser, sample_csv_path):
        """Parser should extract role ID (GUID)."""
        entries = parser.parse_admin_role_assignments(sample_csv_path)

        assert entries[0].role_id == "3bf20276-5595-40ef-96b1-d3ebc13273a0"

    def test_parse_extracts_member_upn(self, parser, sample_csv_path):
        """Parser should extract member UPN."""
        entries = parser.parse_admin_role_assignments(sample_csv_path)

        assert entries[0].member_upn == "nwadmin-az365@fyna.com.au"
        assert entries[1].member_upn == "mailadmin@fyna.com.au"
        # Service principal may not have UPN
        assert entries[2].member_upn == ""

    def test_parse_extracts_member_type(self, parser, sample_csv_path):
        """Parser should extract member type (user/servicePrincipal/group)."""
        entries = parser.parse_admin_role_assignments(sample_csv_path)

        assert entries[0].member_type == "#microsoft.graph.user"
        assert entries[2].member_type == "#microsoft.graph.servicePrincipal"

    def test_parse_handles_empty_file(self, parser, tmp_path):
        """Parser should handle empty CSV gracefully."""
        empty_csv = tmp_path / "12_AdminRoleAssignments.csv"
        empty_csv.write_text('"RoleName","RoleId","RoleDescription","MemberDisplayName","MemberUPN","MemberId","MemberType"\n')

        entries = parser.parse_admin_role_assignments(empty_csv)
        assert entries == []


class TestPrivilegedAccessDetection:
    """Test forensic queries for privileged access detection."""

    @pytest.fixture
    def parser(self):
        return M365LogParser(date_format="AU")

    @pytest.fixture
    def sample_csv_path(self, tmp_path):
        csv_file = tmp_path / "12_AdminRoleAssignments.csv"
        csv_file.write_text(SAMPLE_ADMIN_ROLE_ASSIGNMENTS_CSV, encoding='utf-8')
        return csv_file

    def test_detect_global_admins(self, parser, sample_csv_path):
        """Should detect Global Administrator role assignments (highest risk)."""
        entries = parser.parse_admin_role_assignments(sample_csv_path)

        global_admins = [e for e in entries if e.role_name == "Global Administrator"]
        assert len(global_admins) == 1
        assert global_admins[0].member_upn == "nwadmin-az365@fyna.com.au"

    def test_detect_service_principal_assignments(self, parser, sample_csv_path):
        """Should detect service principal role assignments."""
        entries = parser.parse_admin_role_assignments(sample_csv_path)

        svc_principals = [e for e in entries if "servicePrincipal" in e.member_type]
        assert len(svc_principals) == 1

    def test_detect_exchange_admins(self, parser, sample_csv_path):
        """Should detect Exchange Administrator assignments (email access risk)."""
        entries = parser.parse_admin_role_assignments(sample_csv_path)

        exchange_admins = [e for e in entries if "Exchange" in e.role_name]
        assert len(exchange_admins) == 1


class TestDiscoverLogFiles:
    """Test that discover_log_files() finds admin role assignments."""

    def test_discover_includes_admin_role_assignments(self, tmp_path):
        """discover_log_files() should find admin role assignments CSV."""
        # Create a mock export directory
        (tmp_path / "12_AdminRoleAssignments.csv").write_text('"RoleName","RoleId"\n"Global Administrator","test-id"\n')
        (tmp_path / "01_SignInLogs.csv").write_text("CreatedDateTime\n")

        parser = M365LogParser(date_format="AU")
        discovered = parser.discover_log_files(tmp_path)

        assert LogType.ADMIN_ROLE_ASSIGNMENTS in discovered
        assert discovered[LogType.ADMIN_ROLE_ASSIGNMENTS].name == "12_AdminRoleAssignments.csv"


class TestRealDataParsing:
    """Test with actual FYNA data if available."""

    FYNA_DATA_PATH = Path("/tmp/fyna_extract/TenantWide_Investigation_20260108_083839/12_AdminRoleAssignments.csv")

    @pytest.mark.skipif(
        not FYNA_DATA_PATH.exists(),
        reason="FYNA sample data not available"
    )
    def test_parse_real_fyna_data(self):
        """Parse actual FYNA admin role assignments data."""
        parser = M365LogParser(date_format="AU")
        entries = parser.parse_admin_role_assignments(self.FYNA_DATA_PATH)

        # FYNA has 2 admin role assignments (from prior analysis)
        assert len(entries) == 2

        # Verify we have Global Administrator
        global_admins = [e for e in entries if e.role_name == "Global Administrator"]
        assert len(global_admins) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
