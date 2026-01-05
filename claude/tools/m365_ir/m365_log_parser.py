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


# File patterns for log discovery
# Note: ENTRA_AUDIT (2_*AuditLogs.csv) is Entra ID/Azure AD directory audit,
# distinct from FULL_AUDIT (7_*FullAuditLog.csv) which is the Unified Audit Log
LOG_FILE_PATTERNS = {
    LogType.SIGNIN: r"1_.*SignInLogs\.csv$",
    LogType.ENTRA_AUDIT: r"2_.*AuditLogs\.csv$",
    LogType.AUDIT: r"2_.*AuditLogs\.csv$",  # Deprecated: use ENTRA_AUDIT
    LogType.INBOX_RULES: r"3_.*InboxRules\.csv$",
    LogType.MAILBOX_AUDIT: r"4_.*MailboxAudit\.csv$",
    LogType.OAUTH_CONSENTS: r"5_.*OAuthConsents\.csv$",
    LogType.MFA_CHANGES: r"6_.*MFAChanges\.csv$",
    LogType.FULL_AUDIT: r"7_.*FullAuditLog\.csv$",
    LogType.RISKY_USERS: r"8_.*RiskyUsers\.csv$",
    LogType.PASSWORD_CHANGED: r"9_.*PasswordLastChanged\.csv$",
    LogType.LEGACY_AUTH: r"10_.*LegacyAuth.*\.csv$",
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
            for attr in ['created_datetime', 'creation_date', 'activity_datetime']:
                if hasattr(entry, attr):
                    return getattr(entry, attr)
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
