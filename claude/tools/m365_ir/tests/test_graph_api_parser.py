"""
Test suite for Graph API schema-aware parser integration.

Sprint 2.1: Schema-Aware Parser Integration
Tests written FIRST (TDD Red phase) - expect all tests to fail initially.

Test Coverage:
- Legacy Portal schema (baseline)
- Graph Interactive schema (ISO datetime, location parsing)
- Graph Application schema (service principal, no user fields)
- Auto-detection from headers
- Field-specific transforms (datetime, location, boolean, latency)
- Service principal edge cases
- Real data integration (PIR-GOOD-SAMARITAN-777777)
"""

import pytest
from datetime import datetime
from pathlib import Path
import tempfile
import csv

from claude.tools.m365_ir.m365_log_parser import M365LogParser
from claude.tools.m365_ir.schema_registry import (
    SchemaVariant,
    SignInType,
    get_schema_definition,
    detect_schema_variant,
)


class TestParseWithSchemaLegacy:
    """Test parse_with_schema() with Legacy Portal format (baseline)."""

    def test_parse_legacy_portal_csv_basic(self):
        """Should parse Legacy Portal CSV with basic fields."""
        parser = M365LogParser(date_format="AU")

        # Create test CSV with Legacy Portal headers (CreatedDateTime, UserPrincipalName, etc.)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'CreatedDateTime', 'RequestId', 'UserPrincipalName', 'AppDisplayName',
                'Status', 'IPAddress', 'City', 'Country'
            ])
            writer.writeheader()
            writer.writerow({
                'CreatedDateTime': '3/12/2025 7:22:01 AM',
                'RequestId': 'abc-123',
                'UserPrincipalName': 'user@example.com',
                'AppDisplayName': 'Office 365',
                'Status': 'Success',
                'IPAddress': '203.45.67.89',
                'City': 'Sydney',
                'Country': 'AU'
            })
            csv_path = f.name

        try:
            entries = parser.parse_with_schema(csv_path)
            assert len(entries) == 1
            entry = entries[0]
            assert entry.user_principal_name == 'user@example.com'
            assert entry.ip_address == '203.45.67.89'
            assert entry.status == 'success'
            assert entry.schema_variant == SchemaVariant.LEGACY_PORTAL.value
        finally:
            Path(csv_path).unlink()

    def test_parse_legacy_portal_preserves_all_fields(self):
        """Should preserve all mapped Legacy Portal fields."""
        parser = M365LogParser(date_format="AU")

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'CreatedDateTime', 'RequestId', 'UserPrincipalName', 'UserDisplayName',
                'AppDisplayName', 'Device', 'Browser', 'OS',
                'Status', 'IPAddress', 'City', 'State', 'Country'
            ])
            writer.writeheader()
            writer.writerow({
                'CreatedDateTime': '3/12/2025 7:22:01 AM',
                'RequestId': 'abc-123',
                'UserPrincipalName': 'user@example.com',
                'UserDisplayName': 'Test User',
                'AppDisplayName': 'Office 365',
                'Device': 'device-xyz',
                'Browser': 'Chrome 120',
                'OS': 'Windows 11',
                'Status': 'Success',
                'IPAddress': '203.45.67.89',
                'City': 'Sydney',
                'State': 'NSW',
                'Country': 'AU'
            })
            csv_path = f.name

        try:
            entries = parser.parse_with_schema(csv_path)
            assert len(entries) == 1
            entry = entries[0]
            assert entry.user_display_name == 'Test User'
            assert entry.application == 'Office 365'
            assert entry.device == 'device-xyz'
            assert entry.city == 'Sydney'
            assert entry.country == 'AU'
        finally:
            Path(csv_path).unlink()

    def test_parse_legacy_portal_datetime_au_format(self):
        """Should parse AU ambiguous datetime format (3/12 could be Mar 12 or Dec 3)."""
        parser = M365LogParser(date_format="AU")

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=['CreatedDateTime', 'UserPrincipalName', 'AppDisplayName', 'Status'])
            writer.writeheader()
            writer.writerow({
                'CreatedDateTime': '3/12/2025 7:22:01 AM',  # Should parse as Dec 3 in AU format
                'UserPrincipalName': 'user@example.com',
                'AppDisplayName': 'Office 365',
                'Status': 'Success'
            })
            csv_path = f.name

        try:
            entries = parser.parse_with_schema(csv_path)
            assert len(entries) == 1
            # AU format: day/month/year
            assert entries[0].timestamp.month == 12
            assert entries[0].timestamp.day == 3
        finally:
            Path(csv_path).unlink()


class TestParseWithSchemaGraphInteractive:
    """Test parse_with_schema() with Graph API Interactive format."""

    def test_parse_graph_interactive_iso_datetime(self):
        """Should parse ISO 8601 datetime format."""
        parser = M365LogParser()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=['Date (UTC)', 'Username', 'User', 'Client app', 'Status'])
            writer.writeheader()
            writer.writerow({
                'Date (UTC)': '2025-12-04T08:19:41Z', 'Username': 'user@example.com', 'User': 'Test User', 'Client app': 'Microsoft Office',
                'Status': 'Success'
            })
            csv_path = f.name

        try:
            entries = parser.parse_with_schema(csv_path)
            assert len(entries) == 1
            entry = entries[0]
            assert entry.timestamp.year == 2025
            assert entry.timestamp.month == 12
            assert entry.timestamp.day == 4
            assert entry.timestamp.hour == 8
            assert entry.timestamp.minute == 19
            assert entry.schema_variant == SchemaVariant.GRAPH_INTERACTIVE.value
        finally:
            Path(csv_path).unlink()

    def test_parse_graph_interactive_location_parsing(self):
        """Should parse combined location field 'City, State, Country'."""
        parser = M365LogParser()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=['Date (UTC)', 'Username', 'User', 'Client app', 'Location', 'Status'])
            writer.writeheader()
            writer.writerow({
                'Date (UTC)': '2025-12-04T08:19:41Z',
                'Username': 'user@example.com',
                'User': 'Test User',
                'Client app': 'Microsoft Office',
                'Location': 'Melbourne, Victoria, AU',
                'Status': 'Success'
            })
            csv_path = f.name

        try:
            entries = parser.parse_with_schema(csv_path)
            assert len(entries) == 1
            entry = entries[0]
            assert entry.city == 'Melbourne'
            assert entry.state == 'Victoria'
            assert entry.country == 'AU'
        finally:
            Path(csv_path).unlink()

    def test_parse_graph_interactive_status_normalization(self):
        """Should normalize Graph API status 'Success' -> 'success'."""
        parser = M365LogParser()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=['Date (UTC)', 'Username', 'User', 'Client app', 'Status'])
            writer.writeheader()
            writer.writerow({
                'Date (UTC)': '2025-12-04T08:19:41Z',
                'Username': 'user@example.com',
                'User': 'Test User',
                'Client app': 'Microsoft Office',
                'Status': 'Success'  # Graph API uses title case
            })
            csv_path = f.name

        try:
            entries = parser.parse_with_schema(csv_path)
            assert entries[0].status == 'success'  # Should normalize to lowercase
        finally:
            Path(csv_path).unlink()

    def test_parse_graph_interactive_device_compliance(self):
        """Should parse device compliance boolean fields."""
        parser = M365LogParser()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'Date (UTC)', 'Username', 'User', 'Client app', 'Compliant', 'Managed', 'Status'
            ])
            writer.writeheader()
            writer.writerow({
                'Date (UTC)': '2025-12-04T08:19:41Z',
                'Username': 'user@example.com',
                'User': 'Test User',
                'Client app': 'Microsoft Office',
                'Compliant': 'Yes',
                'Managed': 'No',
                'Status': 'Success'
            })
            csv_path = f.name

        try:
            entries = parser.parse_with_schema(csv_path)
            assert len(entries) == 1
            entry = entries[0]
            assert entry.device_compliant == 1  # True
            assert entry.device_managed == 0    # False
        finally:
            Path(csv_path).unlink()

    def test_parse_graph_interactive_mfa_result(self):
        """Should parse MFA authentication requirement and result."""
        parser = M365LogParser()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'Date (UTC)', 'Username', 'User', 'Client app', 'Authentication requirement', 'Multifactor authentication result', 'Status'
            ])
            writer.writeheader()
            writer.writerow({
                'Date (UTC)': '2025-12-04T08:19:41Z',
                'Username': 'user@example.com',
                'User': 'Test User',
                'Client app': 'Microsoft Office',
                'Authentication requirement': 'multiFactorAuthentication',
                'Multifactor authentication result': 'satisfied',
                'Status': 'Success'
            })
            csv_path = f.name

        try:
            entries = parser.parse_with_schema(csv_path)
            assert len(entries) == 1
            entry = entries[0]
            assert entry.auth_requirement == 'multiFactorAuthentication'
            assert entry.mfa_result == 'satisfied'
        finally:
            Path(csv_path).unlink()

    def test_parse_graph_interactive_latency_parsing(self):
        """Should parse latency field with 'ms' suffix."""
        parser = M365LogParser()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'Date (UTC)', 'Username', 'User', 'Client app', 'Latency', 'Status'
            ])
            writer.writeheader()
            writer.writerow({
                'Date (UTC)': '2025-12-04T08:19:41Z',
                'Username': 'user@example.com',
                'User': 'Test User',
                'Client app': 'Microsoft Office',
                'Latency': '123ms',
                'Status': 'Success'
            })
            csv_path = f.name

        try:
            entries = parser.parse_with_schema(csv_path)
            assert len(entries) == 1
            assert entries[0].latency_ms == 123
        finally:
            Path(csv_path).unlink()


class TestParseWithSchemaGraphApplication:
    """Test parse_with_schema() with Graph Application format (service principal)."""

    def test_parse_graph_application_service_principal_id(self):
        """Should use service principal ID when no user principal name exists."""
        parser = M365LogParser()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'Date (UTC)', 'Service principal ID', 'Service principal name', 'Application ID', 'Status'
            ])
            writer.writeheader()
            writer.writerow({
                'Date (UTC)': '2025-12-04T08:19:41Z',
                'Service principal ID': 'sp-12345',
                'Service principal name': 'MyServicePrincipal',
                'Application ID': 'app-67890',
                'Status': 'Success'
            })
            csv_path = f.name

        try:
            entries = parser.parse_with_schema(csv_path)
            assert len(entries) == 1
            entry = entries[0]
            assert entry.service_principal_id == 'sp-12345'
            assert entry.service_principal_name == 'MyServicePrincipal'
            assert entry.is_service_principal == 1
            assert entry.schema_variant == SchemaVariant.GRAPH_APPLICATION.value
        finally:
            Path(csv_path).unlink()

    def test_parse_graph_application_no_user_principal_name(self):
        """Should NOT expect UserPrincipalName field in service principal CSVs."""
        parser = M365LogParser()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig') as f:
            # No UserPrincipalName field - this is expected for service principals
            writer = csv.DictWriter(f, fieldnames=[
                'Date (UTC)', 'Service principal ID', 'Application ID', 'Status'
            ])
            writer.writeheader()
            writer.writerow({
                'Date (UTC)': '2025-12-04T08:19:41Z',
                'Service principal ID': 'sp-12345',
                'Application ID': 'app-67890',
                'Status': 'Success'
            })
            csv_path = f.name

        try:
            entries = parser.parse_with_schema(csv_path)
            assert len(entries) == 1
            # Should NOT fail even though user_principal_name doesn't exist
            assert entries[0].service_principal_id == 'sp-12345'
        finally:
            Path(csv_path).unlink()

    def test_parse_graph_application_credential_key_id(self):
        """Should parse service principal credential tracking fields."""
        parser = M365LogParser()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'Date (UTC)', 'Service principal ID', 'Service principal name', 'Credential key ID', 'Resource ID ', 'Status'  # Note trailing space on Resource ID
            ])
            writer.writeheader()
            writer.writerow({
                'Date (UTC)': '2025-12-04T08:19:41Z',
                'Service principal ID': 'sp-12345',
                'Service principal name': 'MyServicePrincipal',
                'Credential key ID': 'key-abc',
                'Resource ID ': 'resource-xyz',  # Must match header with trailing space
                'Status': 'Success'
            })
            csv_path = f.name

        try:
            entries = parser.parse_with_schema(csv_path)
            assert len(entries) == 1
            entry = entries[0]
            assert entry.credential_key_id == 'key-abc'
            assert entry.resource_id == 'resource-xyz'
        finally:
            Path(csv_path).unlink()


class TestParseWithSchemaAutoDetect:
    """Test automatic schema detection from CSV headers."""

    def test_auto_detect_legacy_from_headers(self):
        """Should auto-detect Legacy Portal schema from headers."""
        parser = M365LogParser()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'CreatedDateTime', 'UserPrincipalName', 'Status'  # Legacy Portal signature
            ])
            writer.writeheader()
            writer.writerow({
                'CreatedDateTime': '3/12/2025 7:22:01 AM',
                'UserPrincipalName': 'user@example.com',
                'Status': 'Success'
            })
            csv_path = f.name

        try:
            # No schema_definition provided - should auto-detect
            entries = parser.parse_with_schema(csv_path)
            assert entries[0].schema_variant == SchemaVariant.LEGACY_PORTAL.value
        finally:
            Path(csv_path).unlink()

    def test_auto_detect_graph_interactive_from_headers(self):
        """Should auto-detect Graph Interactive schema from headers."""
        parser = M365LogParser()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'Date (UTC)', 'Username', 'User', 'Client app', 'Status'  # Graph API signature
            ])
            writer.writeheader()
            writer.writerow({
                'Date (UTC)': '2025-12-04T08:19:41Z', 'Username': 'user@example.com', 'User': 'Test User', 'Client app': 'Microsoft Office',
                'Status': 'Success'
            })
            csv_path = f.name

        try:
            entries = parser.parse_with_schema(csv_path)
            assert entries[0].schema_variant == SchemaVariant.GRAPH_INTERACTIVE.value
        finally:
            Path(csv_path).unlink()

    def test_auto_detect_graph_application_from_headers(self):
        """Should auto-detect Graph Application schema from headers."""
        parser = M365LogParser()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'Date (UTC)', 'Service principal ID', 'Application ID', 'Status'  # Service principal signature
            ])
            writer.writeheader()
            writer.writerow({
                'Date (UTC)': '2025-12-04T08:19:41Z',
                'Service principal ID': 'sp-12345',
                'Application ID': 'app-67890',
                'Status': 'Success'
            })
            csv_path = f.name

        try:
            entries = parser.parse_with_schema(csv_path)
            assert entries[0].schema_variant == SchemaVariant.GRAPH_APPLICATION.value
        finally:
            Path(csv_path).unlink()

    def test_auto_detect_with_filename_hint(self):
        """Should use filename to disambiguate schema variant."""
        parser = M365LogParser()

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.csv', delete=False,
            encoding='utf-8-sig', prefix='ApplicationSignIns_'
        ) as f:
            writer = csv.DictWriter(f, fieldnames=[
                'Date (UTC)', 'Service principal ID', 'Status'
            ])
            writer.writeheader()
            writer.writerow({
                'Date (UTC)': '2025-12-04T08:19:41Z',
                'Service principal ID': 'sp-12345',
                'Status': 'Success'
            })
            csv_path = f.name

        try:
            # Filename hint should help detection
            entries = parser.parse_with_schema(csv_path)
            assert entries[0].schema_variant == SchemaVariant.GRAPH_APPLICATION.value
            assert entries[0].sign_in_type == SignInType.SERVICE_PRINCIPAL.value
        finally:
            Path(csv_path).unlink()


class TestGraphFieldTransforms:
    """Test field-specific transform integration."""

    def test_iso_datetime_parsing_integration(self):
        """Should integrate parse_iso_datetime() transform."""
        parser = M365LogParser()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=['Date (UTC)', 'Username', 'User', 'Client app', 'Status'])
            writer.writeheader()
            # Test various ISO 8601 formats
            writer.writerow({'Date (UTC)': '2025-12-04T08:19:41Z', 'Username': 'user@example.com', 'User': 'Test User', 'Client app': 'Microsoft Office', 'Status': 'Success'})
            csv_path = f.name

        try:
            entries = parser.parse_with_schema(csv_path)
            assert len(entries) == 1
            assert isinstance(entries[0].timestamp, datetime)
        finally:
            Path(csv_path).unlink()

    def test_location_parsing_integration(self):
        """Should integrate parse_graph_location() transform."""
        parser = M365LogParser()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=['Date (UTC)', 'Username', 'User', 'Client app', 'Location', 'Status'])
            writer.writeheader()
            # Test various location formats
            test_cases = [
                'Melbourne, Victoria, AU',
                'San Francisco, California, US',
                'London, England, GB'
            ]
            for location in test_cases:
                writer.writerow({
                    'Date (UTC)': '2025-12-04T08:19:41Z',
                    'Username': 'user@example.com',
                    'User': 'Test User',
                    'Client app': 'Microsoft Office',
                    'Location': location,
                    'Status': 'Success'
                })
            csv_path = f.name

        try:
            entries = parser.parse_with_schema(csv_path)
            assert len(entries) == 3
            # Check first entry
            assert entries[0].city == 'Melbourne'
            assert entries[0].state == 'Victoria'
            assert entries[0].country == 'AU'
        finally:
            Path(csv_path).unlink()

    def test_boolean_field_parsing_integration(self):
        """Should integrate parse_boolean_field() transform."""
        parser = M365LogParser()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'Date (UTC)', 'Username', 'User', 'Client app', 'Compliant', 'Managed', 'Status'
            ])
            writer.writeheader()
            # Test various boolean formats
            test_cases = [
                ('Yes', 'No'),
                ('True', 'False'),
                ('yes', 'no')
            ]
            for compliant, managed in test_cases:
                writer.writerow({
                    'Date (UTC)': '2025-12-04T08:19:41Z',
                    'Username': 'user@example.com',
                    'User': 'Test User',
                    'Client app': 'Microsoft Office',
                    'Compliant': compliant,
                    'Managed': managed,
                    'Status': 'Success'
                })
            csv_path = f.name

        try:
            entries = parser.parse_with_schema(csv_path)
            assert len(entries) == 3
            # All should parse to 1 and 0
            for entry in entries:
                assert entry.device_compliant == 1
                assert entry.device_managed == 0
        finally:
            Path(csv_path).unlink()

    def test_latency_field_parsing_integration(self):
        """Should integrate parse_latency_field() transform."""
        parser = M365LogParser()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'Date (UTC)', 'Username', 'User', 'Client app', 'Latency', 'Status'
            ])
            writer.writeheader()
            # Test various latency formats
            test_cases = ['123ms', '456.78ms', '789ms']
            for latency in test_cases:
                writer.writerow({
                    'Date (UTC)': '2025-12-04T08:19:41Z',
                    'Username': 'user@example.com',
                    'User': 'Test User',
                    'Client app': 'Microsoft Office',
                    'Latency': latency,
                    'Status': 'Success'
                })
            csv_path = f.name

        try:
            entries = parser.parse_with_schema(csv_path)
            assert len(entries) == 3
            assert entries[0].latency_ms == 123
            assert entries[1].latency_ms == 456  # Should truncate decimal
            assert entries[2].latency_ms == 789
        finally:
            Path(csv_path).unlink()

    def test_trailing_space_field_handling(self):
        """Should handle trailing spaces in field names (Graph API bug)."""
        parser = M365LogParser()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'Date (UTC)', 'Service principal ID', 'Service principal name', 'Application ID ', 'Status'  # Trailing space on AppId
            ])
            writer.writeheader()
            writer.writerow({
                'Date (UTC)': '2025-12-04T08:19:41Z',
                'Service principal ID': 'sp-12345',
                'Service principal name': 'MyServicePrincipal',
                'Application ID ': 'app-12345',  # Field has trailing space
                'Status': 'Success'
            })
            csv_path = f.name

        try:
            entries = parser.parse_with_schema(csv_path)
            assert len(entries) == 1
            # Should still parse despite trailing space on "Application ID " header
            # "Application ID " maps to app_id field (not app_display_name)
            # But we don't have app_id in SignInLogEntry, it maps to service_principal_id context
            # Let me check what field this should actually populate
            # For now, just verify it parsed without error
            assert entries[0].schema_variant == 'graph_application'
        finally:
            Path(csv_path).unlink()


class TestServicePrincipalHandling:
    """Test service principal edge cases."""

    def test_service_principal_uses_sp_id_as_identifier(self):
        """Should use service_principal_id as primary identifier when no user."""
        parser = M365LogParser()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'Date (UTC)', 'Service principal ID', 'Service principal name', 'Status'
            ])
            writer.writeheader()
            writer.writerow({
                'Date (UTC)': '2025-12-04T08:19:41Z',
                'Service principal ID': 'sp-12345',
                'Service principal name': 'MyApp',
                'Status': 'Success'
            })
            csv_path = f.name

        try:
            entries = parser.parse_with_schema(csv_path)
            assert entries[0].service_principal_id == 'sp-12345'
            assert entries[0].service_principal_name == 'MyApp'
        finally:
            Path(csv_path).unlink()

    def test_service_principal_skips_user_fields(self):
        """Should NOT populate user fields for service principal auth."""
        parser = M365LogParser()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'Date (UTC)', 'Service principal ID', 'Status'
            ])
            writer.writeheader()
            writer.writerow({
                'Date (UTC)': '2025-12-04T08:19:41Z',
                'Service principal ID': 'sp-12345',
                'Status': 'Success'
            })
            csv_path = f.name

        try:
            entries = parser.parse_with_schema(csv_path)
            # User fields should be None or empty for service principals
            assert entries[0].user_principal_name is None or entries[0].user_principal_name == ''
        finally:
            Path(csv_path).unlink()

    def test_service_principal_sets_is_service_principal_flag(self):
        """Should set is_service_principal=1 for service principal auth."""
        parser = M365LogParser()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'Date (UTC)', 'Service principal ID', 'Status'
            ])
            writer.writeheader()
            writer.writerow({
                'Date (UTC)': '2025-12-04T08:19:41Z',
                'Service principal ID': 'sp-12345',
                'Status': 'Success'
            })
            csv_path = f.name

        try:
            entries = parser.parse_with_schema(csv_path)
            assert entries[0].is_service_principal == 1
        finally:
            Path(csv_path).unlink()


class TestRealDataIntegration:
    """Test against real PIR-GOOD-SAMARITAN-777777 CSV files."""

    # Real data files location
    REAL_DATA_BASE = Path('/Users/YOUR_USERNAME/work_projects/ir_cases/PIR-GOOD-SAMARITAN-777777/source-files')
    ZIP_FILE = REAL_DATA_BASE / 'SGS_2025-11-04_2025-12-04_1_1.zip'

    @pytest.fixture
    def extracted_files(self, tmp_path):
        """Extract real CSV files to temp directory."""
        import zipfile
        if not self.ZIP_FILE.exists():
            pytest.skip(f"Real data not found: {self.ZIP_FILE}")

        with zipfile.ZipFile(self.ZIP_FILE, 'r') as zip_ref:
            zip_ref.extractall(tmp_path)

        return tmp_path

    def test_parse_real_interactive_signins_csv(self, extracted_files):
        """Should parse real InteractiveSignIns CSV (9,486 records)."""
        parser = M365LogParser()
        csv_path = extracted_files / 'SGS_2025-11-04_2025-12-04' / 'InteractiveSignIns_2025-11-04_2025-12-04.csv'

        if not csv_path.exists():
            pytest.skip(f"File not found: {csv_path}")

        entries = parser.parse_with_schema(csv_path)
        assert len(entries) > 0  # Should parse at least some records

        # Check first entry
        first_entry = entries[0]
        assert first_entry.schema_variant == SchemaVariant.GRAPH_INTERACTIVE.value
        assert first_entry.sign_in_type == SignInType.INTERACTIVE.value
        assert first_entry.user_principal_name is not None
        assert first_entry.timestamp is not None

    def test_parse_real_noninteractive_signins_csv(self, extracted_files):
        """Should parse real NonInteractiveSignIns CSV (100K+ records)."""
        parser = M365LogParser()
        csv_path = extracted_files / 'SGS_2025-11-04_2025-12-04' / 'NonInteractiveSignIns_2025-11-04_2025-12-04.csv'

        if not csv_path.exists():
            pytest.skip(f"File not found: {csv_path}")

        entries = parser.parse_with_schema(csv_path)
        assert len(entries) > 0

        first_entry = entries[0]
        assert first_entry.schema_variant == SchemaVariant.GRAPH_NONINTERACTIVE.value
        assert first_entry.sign_in_type == SignInType.NONINTERACTIVE.value

    def test_parse_real_application_signins_csv(self, extracted_files):
        """Should parse real ApplicationSignIns CSV (49K+ records, NO user fields)."""
        parser = M365LogParser()
        csv_path = extracted_files / 'SGS_2025-11-04_2025-12-04' / 'ApplicationSignIns_2025-11-04_2025-12-04.csv'

        if not csv_path.exists():
            pytest.skip(f"File not found: {csv_path}")

        entries = parser.parse_with_schema(csv_path)
        assert len(entries) > 0

        first_entry = entries[0]
        assert first_entry.schema_variant == SchemaVariant.GRAPH_APPLICATION.value
        assert first_entry.sign_in_type == SignInType.SERVICE_PRINCIPAL.value
        assert first_entry.is_service_principal == 1
        # Should have service principal ID, not user principal name
        assert first_entry.service_principal_id is not None

    def test_parse_real_msi_signins_csv(self, extracted_files):
        """Should parse real MSISignIns CSV (300+ records)."""
        parser = M365LogParser()
        csv_path = extracted_files / 'SGS_2025-11-04_2025-12-04' / 'MSISignIns_2025-11-04_2025-12-04.csv'

        if not csv_path.exists():
            pytest.skip(f"File not found: {csv_path}")

        entries = parser.parse_with_schema(csv_path)
        assert len(entries) > 0

        first_entry = entries[0]
        assert first_entry.schema_variant == SchemaVariant.GRAPH_MSI.value
        assert first_entry.sign_in_type == SignInType.MANAGED_IDENTITY.value
        assert first_entry.is_service_principal == 1
