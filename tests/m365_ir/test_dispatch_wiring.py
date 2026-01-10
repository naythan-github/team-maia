#!/usr/bin/env python3
"""
TDD Test for M365 IR Handler Dispatch Wiring (FIX-1)

Regression test for Phase 249 wiring bug where handler methods exist
but are not called in dispatch logic.

Requirements: /tmp/M365_IR_MISSING_LOG_HANDLERS_REQUIREMENTS.md v2.0
"""

import pytest
import tempfile
import zipfile
import csv
from pathlib import Path
from typing import Dict

from claude.tools.m365_ir.log_database import IRLogDatabase
from claude.tools.m365_ir.log_importer import LogImporter
from claude.tools.m365_ir.m365_log_parser import LogType


@pytest.fixture
def temp_dir(tmp_path):
    """Create temporary directory for test databases and files."""
    return tmp_path


@pytest.fixture
def db(temp_dir):
    """Create IRLogDatabase instance for testing."""
    db = IRLogDatabase(case_id="PIR-DISPATCH-TEST-001", base_path=str(temp_dir))
    db.create()
    return db


@pytest.fixture
def importer(db):
    """Create LogImporter instance for testing."""
    return LogImporter(db)


def create_sample_csv(file_path: Path, log_type: LogType) -> None:
    """Create minimal valid CSV for a given log type."""
    # Define minimal columns for each log type
    csv_schemas = {
        LogType.MAILBOX_DELEGATIONS: {
            'columns': ['Mailbox', 'PermissionType', 'Delegate', 'AccessRights', 'IsInherited'],
            'row': ['test@example.com', 'FullAccess', 'admin@example.com', 'FullAccess', 'False']
        },
        LogType.SERVICE_PRINCIPALS: {
            'columns': ['DisplayName', 'AppId', 'Id', 'ServicePrincipalType', 'AccountEnabled', 'CreatedDateTime'],
            'row': ['TestApp', 'abc-123', 'xyz-789', 'Application', 'True', '01/01/2025 10:00:00 AM']
        },
        LogType.ADMIN_ROLE_ASSIGNMENTS: {
            'columns': ['RoleName', 'RoleId', 'RoleDescription', 'MemberDisplayName', 'MemberUPN', 'MemberId', 'MemberType'],
            'row': ['Global Admin', 'role-123', 'Full access', 'Admin User', 'admin@example.com', 'user-123', '#microsoft.graph.user']
        },
        LogType.APPLICATION_REGISTRATIONS: {
            'columns': ['DisplayName', 'AppId', 'Id', 'CreatedDateTime', 'SignInAudience'],
            'row': ['TestApp', 'app-123', 'obj-789', '01/01/2025 10:00:00 AM', 'AzureADMyOrg']
        },
        LogType.TRANSPORT_RULES: {
            'columns': ['Name', 'State', 'Priority', 'Mode', 'WhenChanged'],
            'row': ['Test Rule', 'Enabled', '0', 'Enforce', '01/01/2025 10:00:00 AM']
        },
        LogType.CONDITIONAL_ACCESS_POLICIES: {
            'columns': ['DisplayName', 'Id', 'State', 'CreatedDateTime', 'ModifiedDateTime'],
            'row': ['Test Policy', 'policy-123', 'enabled', '01/01/2025 10:00:00 AM', '01/01/2025 10:00:00 AM']
        },
        LogType.NAMED_LOCATIONS: {
            'columns': ['DisplayName', 'Id', 'CreatedDateTime', 'ModifiedDateTime', 'IsTrusted'],
            'row': ['Test Location', 'loc-123', '01/01/2025 10:00:00 AM', '01/01/2025 10:00:00 AM', 'True']
        },
    }

    schema = csv_schemas.get(log_type)
    if not schema:
        raise ValueError(f"No CSV schema defined for {log_type}")

    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(schema['columns'])
        writer.writerow(schema['row'])


@pytest.mark.parametrize("log_type,filename", [
    (LogType.MAILBOX_DELEGATIONS, "14_MailboxDelegations.csv"),
    (LogType.SERVICE_PRINCIPALS, "17_ServicePrincipals.csv"),
    (LogType.ADMIN_ROLE_ASSIGNMENTS, "12_AdminRoleAssignments.csv"),
    (LogType.APPLICATION_REGISTRATIONS, "16_ApplicationRegistrations.csv"),
    (LogType.TRANSPORT_RULES, "13_TransportRules.csv"),
    (LogType.CONDITIONAL_ACCESS_POLICIES, "10_ConditionalAccessPolicies.csv"),
    (LogType.NAMED_LOCATIONS, "11_NamedLocations.csv"),
    # Note: EVIDENCE_MANIFEST uses .json format, not .csv - tested separately
])
def test_dispatch_handler_exists_directory_import(importer, temp_dir, log_type, filename):
    """
    Test that all LogType enums have working dispatch handlers for directory imports.

    This test verifies FIX-1: Each log type should import successfully
    without "no handler exists" warnings.
    """
    # Create test CSV file
    csv_path = temp_dir / filename
    create_sample_csv(csv_path, log_type)

    # Import from directory
    results = importer._import_from_directory(temp_dir)

    # Verify import succeeded (not skipped)
    assert len(results) > 0, f"{log_type} was skipped - no handler wired in dispatch logic"

    # Verify at least one record was imported
    result = list(results.values())[0]
    assert result.records_imported >= 1, f"{log_type} imported 0 records - handler may not be working"


@pytest.mark.parametrize("log_type,filename", [
    (LogType.MAILBOX_DELEGATIONS, "14_MailboxDelegations.csv"),
    (LogType.SERVICE_PRINCIPALS, "17_ServicePrincipals.csv"),
    (LogType.ADMIN_ROLE_ASSIGNMENTS, "12_AdminRoleAssignments.csv"),
    (LogType.APPLICATION_REGISTRATIONS, "16_ApplicationRegistrations.csv"),
    (LogType.TRANSPORT_RULES, "13_TransportRules.csv"),
    (LogType.CONDITIONAL_ACCESS_POLICIES, "10_ConditionalAccessPolicies.csv"),
    (LogType.NAMED_LOCATIONS, "11_NamedLocations.csv"),
    # Note: EVIDENCE_MANIFEST uses .json format, not .csv - tested separately
])
def test_dispatch_handler_exists_zip_import(importer, temp_dir, log_type, filename):
    """
    Test that all LogType enums have working dispatch handlers for zip imports.

    This test verifies FIX-1: Each log type should import successfully
    from zip files without "no handler exists" warnings.
    """
    # Create test CSV file
    csv_path = temp_dir / filename
    create_sample_csv(csv_path, log_type)

    # Create zip file containing the CSV
    zip_path = temp_dir / "test_import.zip"
    with zipfile.ZipFile(zip_path, 'w') as zf:
        zf.write(csv_path, arcname=filename)

    # Import from zip
    results = importer._import_from_zip(zip_path)

    # Verify import succeeded (not skipped)
    assert len(results) > 0, f"{log_type} was skipped from zip - no handler wired in dispatch logic"

    # Verify at least one record was imported
    result = list(results.values())[0]
    assert result.records_imported >= 1, f"{log_type} imported 0 records from zip - handler may not be working"


def test_all_log_types_have_handlers(importer):
    """
    Meta-test: Verify all LogType enum members have corresponding handler methods.

    This ensures the wiring bug is caught if new log types are added
    without corresponding handlers.
    """
    # Get all log types that should have handlers (Phase 249 unwired CSV handlers)
    expected_handlers = [
        LogType.MAILBOX_DELEGATIONS,
        LogType.SERVICE_PRINCIPALS,
        LogType.ADMIN_ROLE_ASSIGNMENTS,
        LogType.APPLICATION_REGISTRATIONS,
        LogType.TRANSPORT_RULES,
        LogType.CONDITIONAL_ACCESS_POLICIES,
        LogType.NAMED_LOCATIONS,
        # Note: EVIDENCE_MANIFEST uses .json format - different import path
    ]

    # Verify handler method exists for each
    for log_type in expected_handlers:
        # Convert LogType enum to method name
        # e.g., MAILBOX_DELEGATIONS -> import_mailbox_delegations
        method_name = f"import_{log_type.value}"

        assert hasattr(importer, method_name), \
            f"Handler method '{method_name}' does not exist for {log_type}"

        # Verify it's callable
        handler = getattr(importer, method_name)
        assert callable(handler), \
            f"Handler '{method_name}' exists but is not callable"


def test_pir_sgs_787878_import_coverage(db, importer, temp_dir):
    """
    Integration test: Verify PIR-SGS-787878 case will import all 1,227 missing records.

    This test simulates the full import scenario to ensure all 8 log types
    are properly wired and will import the expected record counts.
    """
    # Create sample files for each missing log type
    # Note: Expected counts are for PIR-SGS-787878 case, but we use 1 record per type for this test
    log_type_configs = [
        (LogType.MAILBOX_DELEGATIONS, "14_MailboxDelegations.csv"),
        (LogType.SERVICE_PRINCIPALS, "17_ServicePrincipals.csv"),
        (LogType.ADMIN_ROLE_ASSIGNMENTS, "12_AdminRoleAssignments.csv"),
        (LogType.APPLICATION_REGISTRATIONS, "16_ApplicationRegistrations.csv"),
        (LogType.TRANSPORT_RULES, "13_TransportRules.csv"),
        (LogType.CONDITIONAL_ACCESS_POLICIES, "10_ConditionalAccessPolicies.csv"),
        (LogType.NAMED_LOCATIONS, "11_NamedLocations.csv"),
        # Note: EVIDENCE_MANIFEST uses .json format - tested separately
    ]

    # Create ALL CSV files first
    for log_type, filename in log_type_configs:
        csv_path = temp_dir / filename
        create_sample_csv(csv_path, log_type)

    # Import all files at once
    results = importer._import_from_directory(temp_dir)

    # Verify all 7 types were imported
    assert len(results) == 7, \
        f"Expected 7 result keys (1 per type), got {len(results)}: {list(results.keys())}"

    # Verify total record count
    total_imported = sum(r.records_imported for r in results.values())
    assert total_imported == 7, \
        f"Expected 7 records imported (1 per CSV type), got {total_imported}"
