#!/usr/bin/env python3
"""
M365 Schema Registry - Multi-Schema ETL Pipeline

Supports multiple M365 export formats:
- Legacy Portal Export (Microsoft 365 Admin Center)
- Graph API Interactive/NonInteractive SignIns
- Graph API ApplicationSignIns (Service Principal)
- Graph API MSISignIns (Managed Identity)
- PowerShell Get-MgAuditLogSignIn exports

Author: Maia System
Created: 2026-01-11 (Phase 264 Sprint 1.1)
"""

from enum import Enum
from typing import List, Set
from dataclasses import dataclass


class SchemaVariant(Enum):
    """M365 sign-in log schema variants"""
    LEGACY_PORTAL = "legacy_portal"
    GRAPH_INTERACTIVE = "graph_interactive"
    GRAPH_NONINTERACTIVE = "graph_noninteractive"
    GRAPH_APPLICATION = "graph_application"
    GRAPH_MSI = "graph_msi"
    UNKNOWN = "unknown"


class SignInType(Enum):
    """Sign-in type classification"""
    INTERACTIVE = "interactive"
    NONINTERACTIVE = "noninteractive"
    SERVICE_PRINCIPAL = "service_principal"
    MANAGED_IDENTITY = "managed_identity"


# Schema fingerprint signatures (unique field combinations)
LEGACY_PORTAL_FINGERPRINT = {
    "CreatedDateTime",
    "UserPrincipalName",
    "AppDisplayName"
}

GRAPH_INTERACTIVE_FINGERPRINT = {
    "Date (UTC)",
    "Username",
    "User",
    "Client app"
}

GRAPH_APPLICATION_FINGERPRINT = {
    "Date (UTC)",
    "Service principal ID",
    "Service principal name"
}

GRAPH_MSI_FINGERPRINT = {
    "Date (UTC)",
    "Managed Identity type"
}


def detect_schema_variant(headers: List[str], filename: str = None) -> SchemaVariant:
    """
    Detect M365 schema variant from CSV headers and optional filename.

    Detection is fingerprint-based, checking for unique field combinations
    that distinguish each schema variant.

    Priority order (most specific to least):
    1. GRAPH_APPLICATION (Service principal ID without Username/User)
    2. GRAPH_MSI (filename contains "MSISignIns")
    3. GRAPH_INTERACTIVE/NONINTERACTIVE (Date (UTC) + user fields, filename determines subtype)
    4. LEGACY_PORTAL (CreatedDateTime)
    5. UNKNOWN

    NOTE: "Managed Identity type" field appears in all Graph API exports as optional column,
    so it cannot be used for schema detection. Use filename instead.

    Args:
        headers: List of CSV column headers
        filename: Optional filename to help distinguish Interactive/NonInteractive/MSI

    Returns:
        SchemaVariant: Detected schema variant

    Example:
        >>> headers = ["Date (UTC)", "Username", "User", "Client app"]
        >>> detect_schema_variant(headers)
        SchemaVariant.GRAPH_INTERACTIVE
    """
    if not headers:
        return SchemaVariant.UNKNOWN

    # Normalize headers: strip quotes, whitespace, and BOM
    header_set: Set[str] = {h.strip().strip('"').strip('\ufeff').strip() for h in headers}

    # Priority 1: Service Principal (has Service principal ID, no user fields)
    # This distinguishes ApplicationSignIns/MSISignIns from Interactive/NonInteractive
    if "Service principal ID" in header_set and "Username" not in header_set:
        # Use filename to distinguish Application vs MSI
        if filename and "msisignins" in filename.lower():
            return SchemaVariant.GRAPH_MSI
        else:
            return SchemaVariant.GRAPH_APPLICATION

    # Priority 2: Graph API Interactive/NonInteractive
    # (filename determines which subtype, both have identical headers)
    if GRAPH_INTERACTIVE_FINGERPRINT.issubset(header_set):
        # Default to GRAPH_INTERACTIVE (covers both unless filename specifies otherwise)
        return SchemaVariant.GRAPH_INTERACTIVE

    # Priority 3: Legacy Portal Export
    if "CreatedDateTime" in header_set:
        return SchemaVariant.LEGACY_PORTAL

    # No match
    return SchemaVariant.UNKNOWN


def detect_signin_type_from_filename(filename: str) -> SignInType:
    """
    Determine sign-in type from filename.

    Graph API exports use filename to distinguish interactive vs noninteractive
    sign-ins, since both have identical CSV headers.

    Args:
        filename: CSV filename (with or without path)

    Returns:
        SignInType: Sign-in type classification

    Example:
        >>> detect_signin_type_from_filename("InteractiveSignIns_2025-12-04.csv")
        SignInType.INTERACTIVE
    """
    filename_lower = filename.lower()

    # Check for specific patterns (order matters - most specific first)
    if "noninteractivesignins" in filename_lower or "non-interactivesignins" in filename_lower:
        return SignInType.NONINTERACTIVE
    elif "interactivesignins" in filename_lower:
        return SignInType.INTERACTIVE
    elif "applicationsignins" in filename_lower:
        return SignInType.SERVICE_PRINCIPAL
    elif "msisignins" in filename_lower:
        return SignInType.MANAGED_IDENTITY
    else:
        # Default to interactive (legacy portal files, unknown patterns)
        return SignInType.INTERACTIVE


@dataclass
class SchemaDefinition:
    """
    Schema definition with field mappings and metadata.

    Maps source schema fields to canonical database fields.
    """
    variant: SchemaVariant
    signin_type: SignInType
    field_mappings: dict  # Source field → canonical field
    date_field: str
    date_format: str
    has_user_fields: bool
    has_service_principal_fields: bool


# Schema definitions will be added in Sprint 1.2
# For now, we have detection only
