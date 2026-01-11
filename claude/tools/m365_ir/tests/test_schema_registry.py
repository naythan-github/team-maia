#!/usr/bin/env python3
"""
TDD Tests for M365 Schema Registry

Tests written FIRST per TDD methodology (Phase 264 Sprint 1.1).
Run: pytest claude/tools/m365_ir/tests/test_schema_registry.py -v

Author: Maia System
Created: 2026-01-11 (Phase 264)
"""

import pytest
from pathlib import Path
import sys

# Add Maia root to path
MAIA_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

from claude.tools.m365_ir.schema_registry import (
    SchemaVariant,
    SignInType,
    detect_schema_variant,
    detect_signin_type_from_filename,
)


class TestSchemaVariantEnum:
    """Test SchemaVariant enum values exist"""

    def test_legacy_portal_variant_exists(self):
        """LEGACY_PORTAL variant should exist"""
        assert hasattr(SchemaVariant, 'LEGACY_PORTAL')

    def test_graph_interactive_variant_exists(self):
        """GRAPH_INTERACTIVE variant should exist"""
        assert hasattr(SchemaVariant, 'GRAPH_INTERACTIVE')

    def test_graph_noninteractive_variant_exists(self):
        """GRAPH_NONINTERACTIVE variant should exist"""
        assert hasattr(SchemaVariant, 'GRAPH_NONINTERACTIVE')

    def test_graph_application_variant_exists(self):
        """GRAPH_APPLICATION variant should exist (service principal)"""
        assert hasattr(SchemaVariant, 'GRAPH_APPLICATION')

    def test_graph_msi_variant_exists(self):
        """GRAPH_MSI variant should exist (managed identity)"""
        assert hasattr(SchemaVariant, 'GRAPH_MSI')

    def test_unknown_variant_exists(self):
        """UNKNOWN variant should exist for unrecognized schemas"""
        assert hasattr(SchemaVariant, 'UNKNOWN')


class TestSignInTypeEnum:
    """Test SignInType enum values exist"""

    def test_interactive_type_exists(self):
        """INTERACTIVE type should exist"""
        assert hasattr(SignInType, 'INTERACTIVE')

    def test_noninteractive_type_exists(self):
        """NONINTERACTIVE type should exist"""
        assert hasattr(SignInType, 'NONINTERACTIVE')

    def test_service_principal_type_exists(self):
        """SERVICE_PRINCIPAL type should exist"""
        assert hasattr(SignInType, 'SERVICE_PRINCIPAL')

    def test_managed_identity_type_exists(self):
        """MANAGED_IDENTITY type should exist"""
        assert hasattr(SignInType, 'MANAGED_IDENTITY')


class TestLegacyPortalSchemaDetection:
    """Test detection of Legacy Portal Export format"""

    def test_detect_legacy_portal_minimal_headers(self):
        """Legacy Portal has CreatedDateTime, UserPrincipalName, AppDisplayName"""
        headers = [
            "CreatedDateTime",
            "UserPrincipalName",
            "AppDisplayName",
            "IPAddress",
            "Status"
        ]
        assert detect_schema_variant(headers) == SchemaVariant.LEGACY_PORTAL

    def test_detect_legacy_portal_full_headers(self):
        """Legacy Portal with all 15 standard columns"""
        headers = [
            "CreatedDateTime",
            "UserPrincipalName",
            "UserDisplayName",
            "AppDisplayName",
            "IPAddress",
            "City",
            "Country",
            "Device",
            "Browser",
            "OS",
            "Status",
            "RiskState",
            "RiskLevelDuringSignIn",
            "RiskLevelAggregated",
            "ConditionalAccessStatus"
        ]
        assert detect_schema_variant(headers) == SchemaVariant.LEGACY_PORTAL

    def test_legacy_portal_fingerprint_unique(self):
        """CreatedDateTime field is unique to Legacy Portal"""
        headers = ["CreatedDateTime", "Other", "Fields"]
        assert detect_schema_variant(headers) == SchemaVariant.LEGACY_PORTAL


class TestGraphInteractiveSchemaDetection:
    """Test detection of Graph API InteractiveSignIns format"""

    def test_detect_graph_interactive_minimal_headers(self):
        """Graph API has Date (UTC), Username, User, Client app"""
        headers = [
            "Date (UTC)",
            "Username",
            "User",
            "Application",
            "IP address",
            "Client app"
        ]
        assert detect_schema_variant(headers) == SchemaVariant.GRAPH_INTERACTIVE

    def test_detect_graph_interactive_full_headers(self):
        """Graph API InteractiveSignIns with 56 columns (excluding Managed Identity type)"""
        headers = [
            "Date (UTC)",
            "Request ID",
            "User agent",
            "Correlation ID",
            "User ID",
            "User",
            "Username",
            "User type",
            "Cross tenant access type",
            "Incoming token type",
            "Authentication Protocol",
            "Unique token identifier",
            "Original transfer method",
            "Client credential type",
            "Token Protection - Sign In Session",
            "Token Protection - Sign In Session StatusCode",
            "Application",
            "Application ID ",
            "App owner tenant ID",
            "Resource",
            "Resource ID ",
            "Resource tenant ID",
            "Resource owner tenant ID",
            "Home tenant ID",
            "Home tenant name",
            "IP address",
            "Location",
            "Status",
            "Sign-in error code",
            "Failure reason",
            "Client app",
            "Device ID",
            "Browser",
            "Operating System",
            "Compliant",
            "Managed",
            "Join Type",
            "Multifactor authentication result",
            "Multifactor authentication auth method",
            "Multifactor authentication auth detail",
            "Authentication requirement",
            "Sign-in identifier",
            "Session ID",
            "IP address (seen by resource)",
            "Through Global Secure Access",
            "Global Secure Access IP address",
            "Autonomous system  number",
            "Flagged for review",
            "Token issuer type",
            "Incoming token type",
            "Token issuer name",
            "Latency",
            "Conditional Access",
            "Associated Resource Id",
            "Federated Token Id",
            "Federated Token Issuer"
        ]
        assert detect_schema_variant(headers) == SchemaVariant.GRAPH_INTERACTIVE

    def test_graph_interactive_with_service_principal_field(self):
        """Graph Interactive may have Service principal ID as optional field (real data)"""
        headers = [
            "Date (UTC)",
            "Username",
            "User",
            "Client app",
            "Service principal ID"  # Optional field in Interactive exports
        ]
        # If both user fields AND service principal fields exist, user fields take precedence
        result = detect_schema_variant(headers)
        assert result == SchemaVariant.GRAPH_INTERACTIVE


class TestGraphApplicationSchemaDetection:
    """Test detection of Graph API ApplicationSignIns format (service principal)"""

    def test_detect_graph_application_minimal_headers(self):
        """Graph Application has Service principal ID/name, no user fields"""
        headers = [
            "Date (UTC)",
            "Service principal ID",
            "Service principal name",
            "Application",
            "IP address"
        ]
        assert detect_schema_variant(headers) == SchemaVariant.GRAPH_APPLICATION

    def test_detect_graph_application_full_headers(self):
        """Graph API ApplicationSignIns with 22 columns"""
        headers = [
            "Date (UTC)",
            "Request ID",
            "Correlation ID",
            "Service principal ID",
            "Service principal name",
            "Credential key ID",
            "Credential thumbprint",
            "Application",
            "Application ID ",
            "App owner tenant ID",
            "Resource",
            "Resource ID ",
            "Resource tenant ID",
            "Resource owner tenant ID",
            "Home tenant ID",
            "Home tenant name",
            "IP address",
            "Location",
            "Status",
            "Sign-in error code",
            "Failure reason",
            "Conditional Access"
        ]
        assert detect_schema_variant(headers) == SchemaVariant.GRAPH_APPLICATION

    def test_graph_application_fingerprint_unique(self):
        """Service principal ID is unique to ApplicationSignIns"""
        headers = [
            "Date (UTC)",
            "Service principal ID",
            "Other fields"
        ]
        assert detect_schema_variant(headers) == SchemaVariant.GRAPH_APPLICATION


class TestGraphNonInteractiveSchemaDetection:
    """Test detection of Graph API NonInteractiveSignIns format"""

    def test_noninteractive_same_as_interactive_headers(self):
        """NonInteractive has same headers as Interactive"""
        headers = [
            "Date (UTC)",
            "Username",
            "User",
            "Application",
            "Client app"
        ]
        # Differentiation comes from filename, not headers
        assert detect_schema_variant(headers) == SchemaVariant.GRAPH_INTERACTIVE


class TestGraphMSISchemaDetection:
    """Test detection of Graph API MSISignIns format"""

    def test_detect_graph_msi_with_filename(self):
        """Graph MSI requires filename for detection (headers same as ApplicationSignIns)"""
        headers = [
            "Date (UTC)",
            "Service principal ID",
            "Service principal name",
            "Application",
            "IP address"
        ]
        # Without filename, defaults to APPLICATION
        assert detect_schema_variant(headers) == SchemaVariant.GRAPH_APPLICATION

        # With filename, detects as MSI
        assert detect_schema_variant(headers, "MSISignIns_2025-12-04.csv") == SchemaVariant.GRAPH_MSI


class TestUnknownSchemaDetection:
    """Test handling of unknown/unrecognized schemas"""

    def test_empty_headers_returns_unknown(self):
        """Empty header list should return UNKNOWN"""
        assert detect_schema_variant([]) == SchemaVariant.UNKNOWN

    def test_random_headers_returns_unknown(self):
        """Unrecognized headers should return UNKNOWN"""
        headers = ["Foo", "Bar", "Baz", "Qux"]
        assert detect_schema_variant(headers) == SchemaVariant.UNKNOWN

    def test_partial_match_returns_unknown(self):
        """Headers that partially match but don't meet fingerprint should return UNKNOWN"""
        headers = ["Date (UTC)", "SomeOtherField"]
        # Has Date (UTC) but missing other required fingerprint fields
        result = detect_schema_variant(headers)
        # Should return UNKNOWN because fingerprint is incomplete
        assert result == SchemaVariant.UNKNOWN


class TestHeaderNormalization:
    """Test that header detection handles various formats"""

    def test_headers_with_quotes(self):
        """CSV headers may have quotes that need stripping"""
        headers = [
            '"Date (UTC)"',
            '"Username"',
            '"User"',
            '"Client app"'
        ]
        assert detect_schema_variant(headers) == SchemaVariant.GRAPH_INTERACTIVE

    def test_headers_with_whitespace(self):
        """Headers may have leading/trailing whitespace"""
        headers = [
            "  Date (UTC)  ",
            " Username ",
            "User",
            "Client app  "
        ]
        assert detect_schema_variant(headers) == SchemaVariant.GRAPH_INTERACTIVE

    def test_headers_mixed_case(self):
        """Headers should be case-sensitive (preserve Microsoft casing)"""
        headers = [
            "date (utc)",  # lowercase
            "username",
            "user",
            "client app"
        ]
        # This should NOT match because Graph API uses exact casing
        result = detect_schema_variant(headers)
        assert result == SchemaVariant.UNKNOWN


class TestSignInTypeFromFilename:
    """Test determining sign-in type from filename"""

    def test_interactive_from_filename(self):
        """InteractiveSignIns in filename → INTERACTIVE"""
        assert detect_signin_type_from_filename("InteractiveSignIns_2025-12-04.csv") == SignInType.INTERACTIVE

    def test_noninteractive_from_filename(self):
        """NonInteractiveSignIns in filename → NONINTERACTIVE"""
        assert detect_signin_type_from_filename("NonInteractiveSignIns_2025-12-04.csv") == SignInType.NONINTERACTIVE

    def test_application_from_filename(self):
        """ApplicationSignIns in filename → SERVICE_PRINCIPAL"""
        assert detect_signin_type_from_filename("ApplicationSignIns_2025-12-04.csv") == SignInType.SERVICE_PRINCIPAL

    def test_msi_from_filename(self):
        """MSISignIns in filename → MANAGED_IDENTITY"""
        assert detect_signin_type_from_filename("MSISignIns_2025-12-04.csv") == SignInType.MANAGED_IDENTITY

    def test_legacy_portal_from_filename(self):
        """Legacy Portal files → INTERACTIVE (default)"""
        assert detect_signin_type_from_filename("01_SignInLogs.csv") == SignInType.INTERACTIVE

    def test_unknown_filename_returns_interactive(self):
        """Unknown filename patterns default to INTERACTIVE"""
        assert detect_signin_type_from_filename("random_file.csv") == SignInType.INTERACTIVE


class TestPriorityDetection:
    """Test schema detection priority when multiple fingerprints match"""

    def test_service_principal_without_user_fields(self):
        """Service principal ID without user fields → APPLICATION"""
        headers = [
            "Date (UTC)",
            "Service principal ID",
            "Service principal name",
            "Application"
        ]
        assert detect_schema_variant(headers) == SchemaVariant.GRAPH_APPLICATION

    def test_user_fields_take_priority_over_service_principal(self):
        """If both user and service principal fields exist, user fields take priority"""
        headers = [
            "Date (UTC)",
            "Username",
            "User",
            "Client app",
            "Service principal ID"  # Optional field
        ]
        # Real data: Interactive files may have Service principal ID as optional column
        assert detect_schema_variant(headers) == SchemaVariant.GRAPH_INTERACTIVE

    def test_legacy_portal_vs_graph_api(self):
        """CreatedDateTime vs Date (UTC) should not conflict"""
        legacy_headers = ["CreatedDateTime", "UserPrincipalName"]
        graph_headers = ["Date (UTC)", "Username", "User", "Client app"]  # Full fingerprint

        assert detect_schema_variant(legacy_headers) == SchemaVariant.LEGACY_PORTAL
        assert detect_schema_variant(graph_headers) == SchemaVariant.GRAPH_INTERACTIVE
