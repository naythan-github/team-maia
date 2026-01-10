#!/usr/bin/env python3
"""
M365 Log Parser - Intelligent CSV parsing for M365 security logs

Features:
- Auto-detect date format (AU DD/MM vs US MM/DD)
- Parse all M365 export log types (SignIn, Audit, Mailbox, LegacyAuth)
- Handle Microsoft PowerShell object bug in Status field
- Multi-export merging with deduplication
- Chronological sorting

Author: Maia System
Created: 2025-12-18 (Phase 225)
"""

import csv
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Dict, Optional, Union, Any

# Configure module logger
logger = logging.getLogger(__name__)


class LogType(Enum):
    """M365 log types"""
    SIGNIN = "signin"
    AUDIT = "audit"
    MAILBOX_AUDIT = "mailbox_audit"
    LEGACY_AUTH = "legacy_auth"
    INBOX_RULES = "inbox_rules"
    OAUTH_CONSENTS = "oauth_consents"
    MFA_CHANGES = "mfa_changes"
    FULL_AUDIT = "full_audit"
    RISKY_USERS = "risky_users"
    PASSWORD_CHANGED = "password_changed"
    ENTRA_AUDIT = "entra_audit"
    # New log types (Phase 249 - v2.1.0-Production export format)
    TRANSPORT_RULES = "transport_rules"
    MAILBOX_DELEGATIONS = "mailbox_delegations"
    ADMIN_ROLE_ASSIGNMENTS = "admin_role_assignments"
    CONDITIONAL_ACCESS_POLICIES = "conditional_access_policies"
    NAMED_LOCATIONS = "named_locations"
    APPLICATION_REGISTRATIONS = "application_registrations"
    SERVICE_PRINCIPALS = "service_principals"
    EVIDENCE_MANIFEST = "evidence_manifest"


# File patterns for log discovery
# Note: ENTRA_AUDIT (2_*AuditLogs.csv) is Entra ID/Azure AD directory audit,
# distinct from FULL_AUDIT (7_*FullAuditLog.csv) which is the Unified Audit Log
LOG_FILE_PATTERNS = {
    # Patterns support both "1_" and "01_" zero-padded prefixes AND date-ranged exports
    # Phase 263 Fix: Support ApplicationSignIns_YYYY-MM-DD_YYYY-MM-DD.csv and MSISignIns patterns
    LogType.SIGNIN: r"(?:0?1_.*SignInLogs|.*(?:Application|MSI)SignIns.*)\.csv$",
    LogType.ENTRA_AUDIT: r"(?:0?2_.*(?:Directory)?AuditLogs|AuditLogs_.*)\.csv$",
    LogType.AUDIT: r"(?:0?2_.*(?:Directory)?AuditLogs|AuditLogs_.*)\.csv$",  # Deprecated: use ENTRA_AUDIT
    LogType.INBOX_RULES: r"0?3_.*InboxRules\.csv$",
    LogType.MAILBOX_AUDIT: r"0?4_.*MailboxAudit(?:Log)?\.csv$",
    LogType.OAUTH_CONSENTS: r"0?5_.*OAuthConsents\.csv$",
    LogType.MFA_CHANGES: r"0?6_.*MFAChanges\.csv$",
    LogType.FULL_AUDIT: r"0?7_.*(?:Full)?(?:Unified)?AuditLog\.csv$",
    LogType.RISKY_USERS: r"0?8_.*RiskyUsers\.csv$",
    LogType.PASSWORD_CHANGED: r"0?9_.*Password(?:LastChanged|Status)\.csv$",
    LogType.LEGACY_AUTH: r"(?:10|18)_.*LegacyAuth.*\.csv$",
    # New patterns (Phase 249 - v2.1.0-Production export format)
    LogType.TRANSPORT_RULES: r"13_.*TransportRules\.csv$",
    LogType.MAILBOX_DELEGATIONS: r"14_.*MailboxDelegations\.csv$",
    LogType.ADMIN_ROLE_ASSIGNMENTS: r"12_.*AdminRoleAssignments\.csv$",
    LogType.CONDITIONAL_ACCESS_POLICIES: r"10_.*ConditionalAccessPolicies\.csv$",
    LogType.NAMED_LOCATIONS: r"11_.*NamedLocations\.csv$",
    LogType.APPLICATION_REGISTRATIONS: r"16_.*ApplicationRegistrations\.csv$",
    LogType.SERVICE_PRINCIPALS: r"17_.*ServicePrincipals\.csv$",
    LogType.EVIDENCE_MANIFEST: r"_EVIDENCE_MANIFEST\.json$",
}


@dataclass
class SignInLogEntry:
    """Sign-in log entry"""
    created_datetime: datetime
    user_principal_name: str
    user_display_name: str
    app_display_name: str
    ip_address: str
    city: str
    country: str
    device: str
    browser: str
    os: str
    status_raw: str
    status_normalized: str
    risk_state: str
    risk_level_during_signin: str
    risk_level_aggregated: str
    conditional_access_status: str

    # Computed fields
    is_foreign: bool = False

    def __hash__(self):
        """Hash for deduplication"""
        return hash((
            self.created_datetime.isoformat(),
            self.user_principal_name,
            self.ip_address,
            self.app_display_name
        ))

    def __eq__(self, other):
        if not isinstance(other, SignInLogEntry):
            return False
        return (
            self.created_datetime == other.created_datetime and
            self.user_principal_name == other.user_principal_name and
            self.ip_address == other.ip_address and
            self.app_display_name == other.app_display_name
        )


@dataclass
class AuditLogEntry:
    """Audit log entry"""
    activity_datetime: datetime
    activity_display_name: str
    initiated_by: str
    target: str
    result: str
    result_reason: str

    def __hash__(self):
        return hash((
            self.activity_datetime.isoformat(),
            self.activity_display_name,
            self.target
        ))


@dataclass
class MailboxAuditEntry:
    """Mailbox audit log entry with parsed JSON"""
    creation_date: datetime
    record_type: str
    user_id: str
    operation: str
    client_ip_address: str
    client_info: str
    audit_data_raw: str
    identity: str

    # Extracted from AuditData JSON
    folders: List[str] = field(default_factory=list)
    subjects: List[str] = field(default_factory=list)

    def __hash__(self):
        return hash((
            self.creation_date.isoformat(),
            self.user_id,
            self.operation,
            self.identity
        ))


@dataclass
class LegacyAuthEntry:
    """Legacy authentication log entry"""
    created_datetime: datetime
    user_principal_name: str
    user_display_name: str
    client_app_used: str
    app_display_name: str
    ip_address: str
    city: str
    country: str
    status: str
    status_normalized: str
    failure_reason: str
    conditional_access_status: str

    def __hash__(self):
        return hash((
            self.created_datetime.isoformat(),
            self.user_principal_name,
            self.ip_address,
            self.client_app_used
        ))


@dataclass
class MailboxDelegationEntry:
    """
    Mailbox delegation entry - access permissions mapping.

    MITRE ATT&CK: T1098.002 (Account Manipulation: Exchange Email Delegate)
    """
    mailbox: str  # Target mailbox
    permission_type: str  # FullAccess/SendAs/SendOnBehalf
    delegate: str  # Who has access
    access_rights: str
    is_inherited: bool
    raw_record: str = ""

    def __hash__(self):
        return hash((self.mailbox, self.permission_type, self.delegate))

    def __eq__(self, other):
        if not isinstance(other, MailboxDelegationEntry):
            return False
        return (
            self.mailbox == other.mailbox and
            self.permission_type == other.permission_type and
            self.delegate == other.delegate
        )


@dataclass
class AdminRoleAssignmentEntry:
    """
    Admin role assignment entry - privileged access mapping.

    MITRE ATT&CK: T1078.004 (Valid Accounts: Cloud), T1098 (Account Manipulation)
    """
    role_name: str  # e.g., Global Administrator
    role_id: str
    role_description: str
    member_display_name: str
    member_upn: str
    member_id: str
    member_type: str  # #microsoft.graph.user, servicePrincipal, group
    raw_record: str = ""

    def __hash__(self):
        return hash((self.role_id, self.member_id))

    def __eq__(self, other):
        if not isinstance(other, AdminRoleAssignmentEntry):
            return False
        return self.role_id == other.role_id and self.member_id == other.member_id


@dataclass
class EvidenceManifestEntry:
    """
    Evidence manifest entry - chain of custody metadata.

    Contains investigation metadata and SHA256 hashes for integrity verification.
    File is typically UTF-16 LE encoded with BOM.
    """
    investigation_id: str
    collection_version: str
    collected_at: str  # ISO8601 timestamp
    collected_by: str  # DOMAIN\\user format
    collected_on: str  # Machine name
    date_range_start: str  # ISO8601
    date_range_end: str  # ISO8601
    days_back: int
    files: List[Dict[str, Any]]  # List of {FileName, SHA256, Size, Records}
    raw_json: str = ""

    def get_file_hashes(self) -> Dict[str, str]:
        """Get filename→SHA256 mapping for integrity verification."""
        return {f['FileName']: f['SHA256'] for f in self.files}

    def get_file_sizes(self) -> Dict[str, int]:
        """Get filename→size mapping."""
        return {f['FileName']: f['Size'] for f in self.files}

    def get_file_record_counts(self) -> Dict[str, int]:
        """Get filename→record count mapping."""
        return {f['FileName']: f['Records'] for f in self.files}


@dataclass
class TransportRuleEntry:
    """
    Exchange Transport Rule entry.

    CRITICAL for exfiltration detection:
    - blind_copy_to: BCC to external = silent exfiltration
    - copy_to: CC to external = exfiltration
    - redirect_message_to: Redirect to external = exfiltration
    - delete_message: True = evidence destruction
    - set_scl: -1 = spam filter bypass (whitelisting)

    MITRE ATT&CK: T1114.003 (Email Collection: Email Forwarding Rule)
    """
    name: str
    state: str  # Enabled/Disabled
    priority: int
    mode: str  # Enforce/Audit
    from_scope: str
    sent_to_scope: str
    blind_copy_to: str  # EXFILTRATION IOC
    copy_to: str  # EXFILTRATION IOC
    redirect_message_to: str  # EXFILTRATION IOC
    delete_message: bool  # Evidence destruction
    modify_subject: str
    set_scl: Optional[int]  # -1 = whitelist (spam bypass)
    conditions: str
    exceptions: str
    when_changed: Optional[datetime]
    comments: str
    raw_record: str

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if not isinstance(other, TransportRuleEntry):
            return False
        return self.name == other.name


@dataclass
class ConditionalAccessPolicyEntry:
    """
    Conditional Access Policy entry.

    Security policy configuration - critical for understanding access controls.
    MITRE ATT&CK: T1562.001 (Impair Defenses: Disable or Modify Tools)
    """
    display_name: str
    policy_id: str
    state: str  # enabled/disabled/enabledForReportingButNotEnforced
    created_datetime: Optional[datetime]
    modified_datetime: Optional[datetime]
    conditions: str  # JSON string
    grant_controls: str  # JSON string
    session_controls: str  # JSON string
    raw_record: str = ""

    def __hash__(self):
        return hash(self.policy_id)

    def __eq__(self, other):
        if not isinstance(other, ConditionalAccessPolicyEntry):
            return False
        return self.policy_id == other.policy_id


@dataclass
class NamedLocationEntry:
    """
    Named Location entry - geographic/IP-based access control.

    Used in Conditional Access policies for location-based restrictions.
    """
    display_name: str
    location_id: str
    created_datetime: Optional[datetime]
    modified_datetime: Optional[datetime]
    location_type: str  # countryNamedLocation or ipNamedLocation
    is_trusted: bool
    ip_ranges: str  # JSON or comma-separated
    countries_and_regions: str  # Comma-separated country codes
    raw_record: str = ""

    def __hash__(self):
        return hash(self.location_id)

    def __eq__(self, other):
        if not isinstance(other, NamedLocationEntry):
            return False
        return self.location_id == other.location_id


@dataclass
class ApplicationRegistrationEntry:
    """
    Application Registration entry - Entra ID app registrations.

    MITRE ATT&CK: T1098.001 (Account Manipulation: Additional Cloud Credentials)
    """
    display_name: str
    app_id: str  # Application (client) ID
    object_id: str  # Object ID in Entra
    created_datetime: Optional[datetime]
    sign_in_audience: str  # AzureADMyOrg, AzureADMultipleOrgs, etc.
    publisher_domain: str
    required_resource_access: str  # JSON - API permissions
    password_credentials: str  # JSON - client secrets (SENSITIVE)
    key_credentials: str  # JSON - certificates
    web_redirect_uris: str
    raw_record: str = ""

    def __hash__(self):
        return hash(self.app_id)

    def __eq__(self, other):
        if not isinstance(other, ApplicationRegistrationEntry):
            return False
        return self.app_id == other.app_id


@dataclass
class ServicePrincipalEntry:
    """
    Service Principal entry - enterprise applications.

    Represents the local instance of an application in the tenant.
    """
    display_name: str
    app_id: str
    object_id: str
    service_principal_type: str  # Application, ManagedIdentity, etc.
    account_enabled: bool
    created_datetime: Optional[datetime]
    app_owner_organization_id: str
    reply_urls: str
    tags: str
    raw_record: str = ""

    def __hash__(self):
        return hash(self.object_id)

    def __eq__(self, other):
        if not isinstance(other, ServicePrincipalEntry):
            return False
        return self.object_id == other.object_id


def detect_date_format(
    dates: Union[str, List[str]],
    default: str = "AU"
) -> str:
    """
    Detect date format from sample dates.

    Logic:
    1. If any date has day > 12 → must be AU format (DD/MM)
    2. If any date has first number > 12 → must be US format (MM/DD)
    3. If ambiguous → use default (AU for Australian tenants)

    Args:
        dates: Single date string or list of date strings
        default: Default format if ambiguous ("AU" or "US")

    Returns:
        "AU" or "US"

    Raises:
        ValueError: If dates is empty or invalid format
    """
    if isinstance(dates, str):
        if not dates:
            raise ValueError("Empty date string provided")
        dates = [dates]

    if not dates:
        raise ValueError("No dates provided for format detection")

    valid_date_found = False

    for date_str in dates:
        if not date_str or not isinstance(date_str, str):
            continue

        # Extract date part (before time)
        date_part = date_str.split()[0] if ' ' in date_str else date_str

        # Try to parse as D/M/YYYY or M/D/YYYY
        match = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{4})$', date_part)
        if not match:
            continue

        valid_date_found = True
        first, second, year = int(match.group(1)), int(match.group(2)), int(match.group(3))

        # If first number > 12, it must be the day (AU format)
        if first > 12:
            return "AU"

        # If second number > 12, first must be month (US format)
        if second > 12:
            return "US"

    # If no valid dates found, raise error
    if not valid_date_found:
        raise ValueError(f"No valid date format found in: {dates}")

    # All dates are ambiguous - use default
    return default


def parse_m365_datetime(
    datetime_str: str,
    date_format: str = "AU"
) -> datetime:
    """
    Parse M365 datetime string to Python datetime.

    Args:
        datetime_str: Date string (e.g., "3/12/2025 7:22:01 AM")
        date_format: "AU" (DD/MM/YYYY), "US" (MM/DD/YYYY), or "ISO"

    Returns:
        datetime object
    """
    if not datetime_str:
        raise ValueError("Empty datetime string")

    datetime_str = datetime_str.strip()

    # Handle ISO format from JSON
    if date_format == "ISO" or 'T' in datetime_str:
        # Remove trailing Z if present
        datetime_str = datetime_str.rstrip('Z')
        try:
            return datetime.fromisoformat(datetime_str)
        except ValueError:
            # Try with microseconds
            return datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%S.%f")

    # Handle M365 export format: D/M/YYYY H:MM:SS AM/PM
    if date_format == "AU":
        fmt = "%d/%m/%Y %I:%M:%S %p"
    else:  # US
        fmt = "%m/%d/%Y %I:%M:%S %p"

    try:
        return datetime.strptime(datetime_str, fmt)
    except ValueError:
        # Try without seconds
        if date_format == "AU":
            fmt = "%d/%m/%Y %I:%M %p"
        else:
            fmt = "%m/%d/%Y %I:%M %p"
        return datetime.strptime(datetime_str, fmt)


def normalize_status(status_raw: str) -> str:
    """
    Normalize status field, handling PowerShell object bug.

    Args:
        status_raw: Raw status value from CSV

    Returns:
        Normalized status: "success", "failure", or "unknown"
    """
    if not status_raw:
        return "unknown"

    status_lower = status_raw.lower()

    # Handle PowerShell object bug
    if "microsoft.graph.powershell.models" in status_lower:
        return "unknown"

    # Handle numeric status codes (from legacy auth)
    if status_raw.isdigit():
        code = int(status_raw)
        # Common error codes
        if code == 0:
            return "success"
        elif code in [50126, 50053, 50057, 50055]:
            return "failure"  # Invalid credentials, locked, disabled, expired
        else:
            return "failure"

    # Direct status values
    if status_lower in ["success", "succeeded", "0"]:
        return "success"
    elif status_lower in ["failure", "failed", "error"]:
        return "failure"

    return "unknown"


class M365LogParser:
    """
    Parser for M365 security log exports.

    Usage:
        # Auto-detect date format
        parser = M365LogParser.from_export("/path/to/export")

        # Or specify format
        parser = M365LogParser(date_format="AU")

        # Parse logs
        signin_entries = parser.parse_signin_logs("/path/to/signin.csv")
        mailbox_entries = parser.parse_mailbox_audit("/path/to/mailbox.csv")

        # Merge multiple exports
        merged = parser.merge_exports(["/export1", "/export2"], LogType.SIGNIN)
    """

    def __init__(self, date_format: str = "AU"):
        """
        Initialize parser.

        Args:
            date_format: Date format ("AU" or "US")
        """
        self.date_format = date_format
        self.last_parse_errors = 0  # Track parse errors for observability

    @classmethod
    def from_export(cls, export_path: Union[str, Path]) -> "M365LogParser":
        """
        Create parser with auto-detected date format from export.

        Args:
            export_path: Path to export directory

        Returns:
            M365LogParser with detected date format
        """
        export_path = Path(export_path)

        # Find sign-in logs to detect format
        for file in export_path.iterdir():
            if re.match(LOG_FILE_PATTERNS[LogType.SIGNIN], file.name):
                dates = cls._extract_sample_dates(file)
                if dates:
                    date_format = detect_date_format(dates)
                    return cls(date_format=date_format)

        # Default to AU if no sign-in logs found
        return cls(date_format="AU")

    @staticmethod
    def _extract_sample_dates(csv_path: Path, sample_size: int = 10) -> List[str]:
        """Extract sample dates from CSV for format detection."""
        dates = []
        try:
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for i, row in enumerate(reader):
                    if i >= sample_size:
                        break
                    # Try common date column names
                    for col in ['CreatedDateTime', 'ActivityDateTime', 'CreationDate']:
                        if col in row and row[col]:
                            dates.append(row[col])
                            break
        except (FileNotFoundError, csv.Error, UnicodeDecodeError, KeyError) as e:
            logger.debug(f"Could not extract sample dates from {csv_path}: {e}")
        return dates

    def parse_signin_logs(self, csv_path: Union[str, Path]) -> List[SignInLogEntry]:
        """
        Parse sign-in logs CSV.

        Args:
            csv_path: Path to sign-in logs CSV

        Returns:
            List of SignInLogEntry objects
        """
        entries = []
        csv_path = Path(csv_path)
        self.last_parse_errors = 0  # Reset error counter

        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
                try:
                    entry = SignInLogEntry(
                        created_datetime=parse_m365_datetime(
                            row.get('CreatedDateTime', ''),
                            self.date_format
                        ),
                        user_principal_name=row.get('UserPrincipalName', ''),
                        user_display_name=row.get('UserDisplayName', ''),
                        app_display_name=row.get('AppDisplayName', ''),
                        ip_address=row.get('IPAddress', ''),
                        city=row.get('City', ''),
                        country=row.get('Country', ''),
                        device=row.get('Device', ''),
                        browser=row.get('Browser', ''),
                        os=row.get('OS', ''),
                        status_raw=row.get('Status', ''),
                        status_normalized=normalize_status(row.get('Status', '')),
                        risk_state=row.get('RiskState', ''),
                        risk_level_during_signin=row.get('RiskLevelDuringSignIn', ''),
                        risk_level_aggregated=row.get('RiskLevelAggregated', ''),
                        conditional_access_status=row.get('ConditionalAccessStatus', ''),
                    )
                    entries.append(entry)
                except Exception as e:
                    self.last_parse_errors += 1
                    logger.debug(f"Skipped malformed signin row {row_num}: {e}")
                    continue

        return entries

    def parse_mailbox_audit(self, csv_path: Union[str, Path]) -> List[MailboxAuditEntry]:
        """
        Parse mailbox audit logs CSV with nested JSON.

        Args:
            csv_path: Path to mailbox audit CSV

        Returns:
            List of MailboxAuditEntry objects
        """
        entries = []
        csv_path = Path(csv_path)
        self.last_parse_errors = 0  # Reset error counter

        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, start=2):
                try:
                    # Parse nested AuditData JSON
                    audit_data_raw = row.get('AuditData', '{}')
                    try:
                        audit_data = json.loads(audit_data_raw)
                    except json.JSONDecodeError:
                        audit_data = {}

                    # Extract fields from JSON
                    client_ip = audit_data.get('ClientIPAddress', '')
                    client_info = audit_data.get('ClientInfoString', '')

                    # Extract folder/subject info if present
                    folders = []
                    subjects = []
                    for folder in audit_data.get('Folders', []):
                        if 'Path' in folder:
                            folders.append(folder['Path'])
                        for item in folder.get('FolderItems', []):
                            if 'Subject' in item:
                                subjects.append(item['Subject'])

                    entry = MailboxAuditEntry(
                        creation_date=parse_m365_datetime(
                            row.get('CreationDate', ''),
                            self.date_format
                        ),
                        record_type=row.get('RecordType', ''),
                        user_id=row.get('UserIds', ''),
                        operation=row.get('Operations', ''),
                        client_ip_address=client_ip,
                        client_info=client_info,
                        audit_data_raw=audit_data_raw,
                        identity=row.get('Identity', ''),
                        folders=folders,
                        subjects=subjects,
                    )
                    entries.append(entry)
                except Exception as e:
                    self.last_parse_errors += 1
                    logger.debug(f"Skipped malformed mailbox audit row {row_num}: {e}")
                    continue

        return entries

    def parse_legacy_auth(self, csv_path: Union[str, Path]) -> List[LegacyAuthEntry]:
        """
        Parse legacy authentication logs CSV.

        Args:
            csv_path: Path to legacy auth CSV

        Returns:
            List of LegacyAuthEntry objects
        """
        entries = []
        csv_path = Path(csv_path)
        self.last_parse_errors = 0  # Reset error counter

        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, start=2):
                try:
                    entry = LegacyAuthEntry(
                        created_datetime=parse_m365_datetime(
                            row.get('CreatedDateTime', ''),
                            self.date_format
                        ),
                        user_principal_name=row.get('UserPrincipalName', ''),
                        user_display_name=row.get('UserDisplayName', ''),
                        client_app_used=row.get('ClientAppUsed', ''),
                        app_display_name=row.get('AppDisplayName', ''),
                        ip_address=row.get('IPAddress', ''),
                        city=row.get('City', ''),
                        country=row.get('Country', ''),
                        status=row.get('Status', ''),
                        status_normalized=normalize_status(row.get('Status', '')),
                        failure_reason=row.get('FailureReason', ''),
                        conditional_access_status=row.get('ConditionalAccessStatus', ''),
                    )
                    entries.append(entry)
                except Exception as e:
                    self.last_parse_errors += 1
                    logger.debug(f"Skipped malformed legacy auth row {row_num}: {e}")
                    continue

        return entries

    def parse_audit_logs(self, csv_path: Union[str, Path]) -> List[AuditLogEntry]:
        """
        Parse audit logs CSV.

        Args:
            csv_path: Path to audit logs CSV

        Returns:
            List of AuditLogEntry objects
        """
        entries = []
        csv_path = Path(csv_path)
        self.last_parse_errors = 0  # Reset error counter

        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, start=2):
                try:
                    entry = AuditLogEntry(
                        activity_datetime=parse_m365_datetime(
                            row.get('ActivityDateTime', ''),
                            self.date_format
                        ),
                        activity_display_name=row.get('ActivityDisplayName', ''),
                        initiated_by=row.get('InitiatedBy', ''),
                        target=row.get('Target', ''),
                        result=row.get('Result', ''),
                        result_reason=row.get('ResultReason', ''),
                    )
                    entries.append(entry)
                except Exception as e:
                    self.last_parse_errors += 1
                    logger.debug(f"Skipped malformed audit row {row_num}: {e}")
                    continue

        return entries

    def parse_transport_rules(self, csv_path: Union[str, Path]) -> List[TransportRuleEntry]:
        """
        Parse Exchange Transport Rules CSV.

        CRITICAL for exfiltration detection - examines org-wide mail flow rules
        that may redirect/BCC/delete emails.

        Args:
            csv_path: Path to TransportRules CSV

        Returns:
            List of TransportRuleEntry objects

        CSV Columns:
            Name, State, Priority, Mode, FromScope, SentToScope,
            BlindCopyTo, CopyTo, RedirectMessageTo, DeleteMessage,
            ModifySubject, SetSCL, Conditions, Exceptions, WhenChanged, Comments
        """
        entries = []
        csv_path = Path(csv_path)
        self.last_parse_errors = 0

        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, start=2):
                try:
                    # Parse priority (may be empty)
                    priority_str = row.get('Priority', '0')
                    priority = int(priority_str) if priority_str else 0

                    # Parse SetSCL (-1 = whitelist, None if empty)
                    scl_str = row.get('SetSCL', '')
                    set_scl = int(scl_str) if scl_str and scl_str != '' else None

                    # Parse DeleteMessage boolean
                    delete_str = row.get('DeleteMessage', 'False')
                    delete_message = delete_str.lower() == 'true'

                    # Parse WhenChanged datetime
                    when_changed_str = row.get('WhenChanged', '')
                    when_changed = None
                    if when_changed_str:
                        try:
                            when_changed = parse_m365_datetime(when_changed_str, self.date_format)
                        except ValueError:
                            logger.debug(f"Could not parse WhenChanged: {when_changed_str}")

                    # Build raw record for forensic preservation
                    raw_record = json.dumps(dict(row), ensure_ascii=False)

                    entry = TransportRuleEntry(
                        name=row.get('Name', ''),
                        state=row.get('State', ''),
                        priority=priority,
                        mode=row.get('Mode', ''),
                        from_scope=row.get('FromScope', ''),
                        sent_to_scope=row.get('SentToScope', ''),
                        blind_copy_to=row.get('BlindCopyTo', ''),
                        copy_to=row.get('CopyTo', ''),
                        redirect_message_to=row.get('RedirectMessageTo', ''),
                        delete_message=delete_message,
                        modify_subject=row.get('ModifySubject', ''),
                        set_scl=set_scl,
                        conditions=row.get('Conditions', ''),
                        exceptions=row.get('Exceptions', ''),
                        when_changed=when_changed,
                        comments=row.get('Comments', ''),
                        raw_record=raw_record,
                    )
                    entries.append(entry)
                except Exception as e:
                    self.last_parse_errors += 1
                    logger.debug(f"Skipped malformed transport rule row {row_num}: {e}")
                    continue

        return entries

    def parse_evidence_manifest(self, json_path: Union[str, Path]) -> EvidenceManifestEntry:
        """
        Parse evidence manifest JSON file.

        Handles UTF-16 LE encoding (common in M365 exports) and extracts
        chain of custody metadata including SHA256 hashes for all collected files.

        Args:
            json_path: Path to _EVIDENCE_MANIFEST.json

        Returns:
            EvidenceManifestEntry object
        """
        json_path = Path(json_path)

        # Read file and handle encoding (UTF-16 LE with BOM or UTF-8)
        with open(json_path, 'rb') as f:
            content = f.read()

        # Detect and decode encoding
        if content.startswith(b'\xff\xfe'):
            # UTF-16 LE with BOM - skip BOM and decode
            text = content[2:].decode('utf-16-le')
        elif content.startswith(b'\xef\xbb\xbf'):
            # UTF-8 with BOM
            text = content[3:].decode('utf-8')
        else:
            # Try UTF-8 first, fall back to UTF-16 LE
            try:
                text = content.decode('utf-8')
            except UnicodeDecodeError:
                text = content.decode('utf-16-le')

        # Strip any whitespace/BOM artifacts
        text = text.strip()

        # Parse JSON
        data = json.loads(text)

        return EvidenceManifestEntry(
            investigation_id=data.get('InvestigationId', ''),
            collection_version=data.get('CollectionVersion', ''),
            collected_at=data.get('CollectedAt', ''),
            collected_by=data.get('CollectedBy', ''),
            collected_on=data.get('CollectedOn', ''),
            date_range_start=data.get('DateRangeStart', ''),
            date_range_end=data.get('DateRangeEnd', ''),
            days_back=data.get('DaysBack', 0),
            files=data.get('Files', []),
            raw_json=json.dumps(data, ensure_ascii=False)
        )

    def parse_mailbox_delegations(
        self, csv_path: Union[str, Path]
    ) -> List[MailboxDelegationEntry]:
        """
        Parse mailbox delegations CSV.

        Extracts who has access to which mailboxes - critical for lateral movement detection.
        MITRE ATT&CK: T1098.002 (Account Manipulation: Exchange Email Delegate)

        Args:
            csv_path: Path to MailboxDelegations CSV

        Returns:
            List of MailboxDelegationEntry objects
        """
        entries = []
        csv_path = Path(csv_path)
        self.last_parse_errors = 0

        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, start=2):
                try:
                    is_inherited = row.get('IsInherited', 'False').lower() == 'true'
                    raw_record = json.dumps(dict(row), ensure_ascii=False)

                    entry = MailboxDelegationEntry(
                        mailbox=row.get('Mailbox', ''),
                        permission_type=row.get('PermissionType', ''),
                        delegate=row.get('Delegate', ''),
                        access_rights=row.get('AccessRights', ''),
                        is_inherited=is_inherited,
                        raw_record=raw_record,
                    )
                    entries.append(entry)
                except Exception as e:
                    self.last_parse_errors += 1
                    logger.debug(f"Skipped malformed delegation row {row_num}: {e}")
                    continue

        return entries

    def parse_admin_role_assignments(
        self, csv_path: Union[str, Path]
    ) -> List[AdminRoleAssignmentEntry]:
        """
        Parse admin role assignments CSV.

        Extracts privileged role memberships - critical for privilege escalation detection.
        MITRE ATT&CK: T1078.004 (Valid Accounts: Cloud), T1098 (Account Manipulation)

        Args:
            csv_path: Path to AdminRoleAssignments CSV

        Returns:
            List of AdminRoleAssignmentEntry objects
        """
        entries = []
        csv_path = Path(csv_path)
        self.last_parse_errors = 0

        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, start=2):
                try:
                    raw_record = json.dumps(dict(row), ensure_ascii=False)

                    entry = AdminRoleAssignmentEntry(
                        role_name=row.get('RoleName', ''),
                        role_id=row.get('RoleId', ''),
                        role_description=row.get('RoleDescription', ''),
                        member_display_name=row.get('MemberDisplayName', ''),
                        member_upn=row.get('MemberUPN', ''),
                        member_id=row.get('MemberId', ''),
                        member_type=row.get('MemberType', ''),
                        raw_record=raw_record,
                    )
                    entries.append(entry)
                except Exception as e:
                    self.last_parse_errors += 1
                    logger.debug(f"Skipped malformed admin role row {row_num}: {e}")
                    continue

        return entries

    def parse_conditional_access_policies(
        self, csv_path: Union[str, Path]
    ) -> List[ConditionalAccessPolicyEntry]:
        """
        Parse Conditional Access Policies CSV.

        Extracts security policy configuration - critical for understanding access controls.
        MITRE ATT&CK: T1562.001 (Impair Defenses: Disable or Modify Tools)

        Args:
            csv_path: Path to ConditionalAccessPolicies CSV

        Returns:
            List of ConditionalAccessPolicyEntry objects
        """
        entries = []
        csv_path = Path(csv_path)
        self.last_parse_errors = 0

        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, start=2):
                try:
                    # Parse datetimes
                    created_str = row.get('CreatedDateTime', '')
                    created_datetime = None
                    if created_str:
                        try:
                            created_datetime = parse_m365_datetime(created_str, self.date_format)
                        except ValueError:
                            pass

                    modified_str = row.get('ModifiedDateTime', '')
                    modified_datetime = None
                    if modified_str:
                        try:
                            modified_datetime = parse_m365_datetime(modified_str, self.date_format)
                        except ValueError:
                            pass

                    raw_record = json.dumps(dict(row), ensure_ascii=False)

                    entry = ConditionalAccessPolicyEntry(
                        display_name=row.get('DisplayName', ''),
                        policy_id=row.get('Id', ''),
                        state=row.get('State', ''),
                        created_datetime=created_datetime,
                        modified_datetime=modified_datetime,
                        conditions=row.get('Conditions', '{}'),
                        grant_controls=row.get('GrantControls', '{}'),
                        session_controls=row.get('SessionControls', '{}'),
                        raw_record=raw_record,
                    )
                    entries.append(entry)
                except Exception as e:
                    self.last_parse_errors += 1
                    logger.debug(f"Skipped malformed CA policy row {row_num}: {e}")
                    continue

        return entries

    def parse_named_locations(
        self, csv_path: Union[str, Path]
    ) -> List[NamedLocationEntry]:
        """
        Parse Named Locations CSV.

        Extracts geographic/IP-based access control locations.

        Args:
            csv_path: Path to NamedLocations CSV

        Returns:
            List of NamedLocationEntry objects
        """
        entries = []
        csv_path = Path(csv_path)
        self.last_parse_errors = 0

        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, start=2):
                try:
                    # Parse datetimes
                    created_str = row.get('CreatedDateTime', '')
                    created_datetime = None
                    if created_str:
                        try:
                            created_datetime = parse_m365_datetime(created_str, self.date_format)
                        except ValueError:
                            pass

                    modified_str = row.get('ModifiedDateTime', '')
                    modified_datetime = None
                    if modified_str:
                        try:
                            modified_datetime = parse_m365_datetime(modified_str, self.date_format)
                        except ValueError:
                            pass

                    # Parse IsTrusted boolean
                    is_trusted = row.get('IsTrusted', 'False').lower() == 'true'

                    raw_record = json.dumps(dict(row), ensure_ascii=False)

                    entry = NamedLocationEntry(
                        display_name=row.get('DisplayName', ''),
                        location_id=row.get('Id', ''),
                        created_datetime=created_datetime,
                        modified_datetime=modified_datetime,
                        location_type=row.get('Type', ''),
                        is_trusted=is_trusted,
                        ip_ranges=row.get('IpRanges', ''),
                        countries_and_regions=row.get('CountriesAndRegions', ''),
                        raw_record=raw_record,
                    )
                    entries.append(entry)
                except Exception as e:
                    self.last_parse_errors += 1
                    logger.debug(f"Skipped malformed named location row {row_num}: {e}")
                    continue

        return entries

    def parse_application_registrations(
        self, csv_path: Union[str, Path]
    ) -> List[ApplicationRegistrationEntry]:
        """
        Parse Application Registrations CSV.

        Extracts Entra ID app registrations - critical for credential access detection.
        MITRE ATT&CK: T1098.001 (Account Manipulation: Additional Cloud Credentials)

        Args:
            csv_path: Path to ApplicationRegistrations CSV

        Returns:
            List of ApplicationRegistrationEntry objects
        """
        entries = []
        csv_path = Path(csv_path)
        self.last_parse_errors = 0

        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, start=2):
                try:
                    # Parse datetime
                    created_str = row.get('CreatedDateTime', '')
                    created_datetime = None
                    if created_str:
                        try:
                            created_datetime = parse_m365_datetime(created_str, self.date_format)
                        except ValueError:
                            pass

                    raw_record = json.dumps(dict(row), ensure_ascii=False)

                    entry = ApplicationRegistrationEntry(
                        display_name=row.get('DisplayName', ''),
                        app_id=row.get('AppId', ''),
                        object_id=row.get('Id', ''),
                        created_datetime=created_datetime,
                        sign_in_audience=row.get('SignInAudience', ''),
                        publisher_domain=row.get('PublisherDomain', ''),
                        required_resource_access=row.get('RequiredResourceAccess', ''),
                        password_credentials=row.get('PasswordCredentials', ''),
                        key_credentials=row.get('KeyCredentials', ''),
                        web_redirect_uris=row.get('Web_RedirectUris', ''),
                        raw_record=raw_record,
                    )
                    entries.append(entry)
                except Exception as e:
                    self.last_parse_errors += 1
                    logger.debug(f"Skipped malformed app registration row {row_num}: {e}")
                    continue

        return entries

    def parse_service_principals(
        self, csv_path: Union[str, Path]
    ) -> List[ServicePrincipalEntry]:
        """
        Parse Service Principals CSV.

        Extracts enterprise applications - local instances of apps in the tenant.

        Args:
            csv_path: Path to ServicePrincipals CSV

        Returns:
            List of ServicePrincipalEntry objects
        """
        entries = []
        csv_path = Path(csv_path)
        self.last_parse_errors = 0

        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, start=2):
                try:
                    # Parse datetime
                    created_str = row.get('CreatedDateTime', '')
                    created_datetime = None
                    if created_str:
                        try:
                            created_datetime = parse_m365_datetime(created_str, self.date_format)
                        except ValueError:
                            pass

                    # Parse AccountEnabled boolean
                    account_enabled = row.get('AccountEnabled', 'True').lower() == 'true'

                    raw_record = json.dumps(dict(row), ensure_ascii=False)

                    entry = ServicePrincipalEntry(
                        display_name=row.get('DisplayName', ''),
                        app_id=row.get('AppId', ''),
                        object_id=row.get('Id', ''),
                        service_principal_type=row.get('ServicePrincipalType', ''),
                        account_enabled=account_enabled,
                        created_datetime=created_datetime,
                        app_owner_organization_id=row.get('AppOwnerOrganizationId', ''),
                        reply_urls=row.get('ReplyUrls', ''),
                        tags=row.get('Tags', ''),
                        raw_record=raw_record,
                    )
                    entries.append(entry)
                except Exception as e:
                    self.last_parse_errors += 1
                    logger.debug(f"Skipped malformed service principal row {row_num}: {e}")
                    continue

        return entries

    def discover_log_files(self, export_path: Union[str, Path]) -> Dict[LogType, Path]:
        """
        Discover log files in export directory.

        Args:
            export_path: Path to export directory

        Returns:
            Dict mapping LogType to file path
        """
        export_path = Path(export_path)
        discovered = {}

        for file in export_path.iterdir():
            if not file.is_file():
                continue
            for log_type, pattern in LOG_FILE_PATTERNS.items():
                if re.match(pattern, file.name):
                    discovered[log_type] = file
                    break

        return discovered

    def merge_exports(
        self,
        export_paths: List[Union[str, Path]],
        log_type: LogType
    ) -> List[Any]:
        """
        Merge log entries from multiple exports with deduplication.

        Args:
            export_paths: List of export directory paths
            log_type: Type of log to merge

        Returns:
            Deduplicated, chronologically sorted list of entries
        """
        all_entries = []

        parse_method = {
            LogType.SIGNIN: self.parse_signin_logs,
            LogType.MAILBOX_AUDIT: self.parse_mailbox_audit,
            LogType.LEGACY_AUTH: self.parse_legacy_auth,
            LogType.AUDIT: self.parse_audit_logs,
            LogType.TRANSPORT_RULES: self.parse_transport_rules,
        }.get(log_type)

        if not parse_method:
            raise ValueError(f"Unsupported log type for merging: {log_type}")

        for export_path in export_paths:
            export_path = Path(export_path)
            discovered = self.discover_log_files(export_path)

            if log_type in discovered:
                entries = parse_method(discovered[log_type])
                all_entries.extend(entries)

        # Deduplicate using set (entries have __hash__ and __eq__)
        unique_entries = list(set(all_entries))

        # Sort chronologically
        return self.sort_chronologically(unique_entries)

    def sort_chronologically(self, entries: List[Any]) -> List[Any]:
        """
        Sort entries chronologically.

        Args:
            entries: List of log entries

        Returns:
            Sorted list
        """
        def get_datetime(entry):
            for attr in ['created_datetime', 'creation_date', 'activity_datetime', 'when_changed']:
                if hasattr(entry, attr):
                    val = getattr(entry, attr)
                    if val is not None:
                        return val
            return datetime.min

        return sorted(entries, key=get_datetime)


if __name__ == "__main__":
    # Quick test with Oculus data
    import sys

    if len(sys.argv) > 1:
        export_path = Path(sys.argv[1])
        parser = M365LogParser.from_export(export_path)
        print(f"Detected date format: {parser.date_format}")

        discovered = parser.discover_log_files(export_path)
        print(f"\nDiscovered log files:")
        for log_type, path in discovered.items():
            print(f"  {log_type.value}: {path.name}")

        if LogType.SIGNIN in discovered:
            entries = parser.parse_signin_logs(discovered[LogType.SIGNIN])
            print(f"\nParsed {len(entries)} sign-in entries")
            if entries:
                print(f"  First: {entries[0].created_datetime} - {entries[0].user_principal_name}")
                print(f"  Last:  {entries[-1].created_datetime} - {entries[-1].user_principal_name}")
