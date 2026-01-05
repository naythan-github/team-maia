#!/usr/bin/env python3
"""
LogImporter - CSV/JSON to SQLite import for M365 IR logs.

Phase 226 - IR Log Database Implementation
Imports parsed M365 security logs into per-investigation SQLite databases.

Usage:
    from log_database import IRLogDatabase
    from log_importer import LogImporter

    db = IRLogDatabase(case_id="PIR-ACME-2025-001")
    db.create()

    importer = LogImporter(db)
    result = importer.import_sign_in_logs("/path/to/signin.csv")
    print(f"Imported {result.records_imported} records")

Author: Maia System (SRE Principal Engineer Agent)
Created: 2025-01-05
"""

import csv
import hashlib
import io
import json
import logging
import re
import time
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union, BinaryIO

from .log_database import IRLogDatabase
from .m365_log_parser import (
    M365LogParser,
    LogType,
    LOG_FILE_PATTERNS,
    parse_m365_datetime,
    normalize_status,
)

# Configure module logger
logger = logging.getLogger(__name__)

# Parser version for tracking
PARSER_VERSION = "1.0.0"


@dataclass
class ImportResult:
    """Result of a log import operation."""

    source_file: str
    source_hash: str
    records_imported: int
    records_failed: int
    errors: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    records_skipped: int = 0  # Duplicates skipped by UNIQUE constraint


class LogImporter:
    """
    Imports parsed M365 logs into SQLite database.

    Handles CSV parsing, record transformation, deduplication,
    and import tracking.
    """

    def __init__(self, db: IRLogDatabase):
        """
        Initialize importer with target database.

        Args:
            db: IRLogDatabase instance (must be created first)
        """
        self._db = db
        self._parser = M365LogParser()

    @property
    def db(self) -> IRLogDatabase:
        """Return the database reference."""
        return self._db

    def import_sign_in_logs(self, source: Union[str, Path]) -> ImportResult:
        """
        Import Azure AD sign-in logs from CSV.

        Args:
            source: Path to sign-in logs CSV file

        Returns:
            ImportResult with import statistics

        Raises:
            FileNotFoundError: If source file doesn't exist
        """
        source = Path(source)
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source}")

        start_time = time.time()
        source_hash = self._calculate_hash(source)

        # Check if already imported
        if self._is_already_imported(source_hash, 'sign_in'):
            return ImportResult(
                source_file=str(source),
                source_hash=source_hash,
                records_imported=0,
                records_failed=0,
                errors=[],
                duration_seconds=time.time() - start_time
            )

        records_imported = 0
        records_failed = 0
        records_skipped = 0
        errors: List[str] = []

        conn = self._db.connect()
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        # Record import start
        cursor.execute("""
            INSERT INTO import_metadata
            (source_file, source_hash, log_type, records_imported, records_failed,
             import_started, parser_version)
            VALUES (?, ?, ?, 0, 0, ?, ?)
        """, (str(source), source_hash, 'sign_in', now, PARSER_VERSION))
        import_id = cursor.lastrowid

        try:
            with open(source, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row_num, row in enumerate(reader, start=2):
                    try:
                        # Parse datetime
                        timestamp = parse_m365_datetime(
                            row.get('CreatedDateTime', ''),
                            self._detect_date_format(row.get('CreatedDateTime', ''))
                        )

                        # INSERT OR IGNORE for deduplication via UNIQUE constraint
                        cursor.execute("""
                            INSERT OR IGNORE INTO sign_in_logs
                            (timestamp, user_principal_name, user_display_name,
                             ip_address, location_city, location_country,
                             client_app, app_display_name, browser, os,
                             status_error_code, conditional_access_status,
                             risk_level, risk_state, correlation_id,
                             raw_record, imported_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            timestamp.isoformat(),
                            row.get('UserPrincipalName', ''),
                            row.get('UserDisplayName', ''),
                            row.get('IPAddress', ''),
                            row.get('City', ''),
                            row.get('Country', ''),
                            row.get('ClientAppUsed', ''),
                            row.get('AppDisplayName', ''),
                            row.get('Browser', ''),
                            row.get('OS', ''),
                            0 if normalize_status(row.get('Status', '')) == 'success' else 1,
                            row.get('ConditionalAccessStatus', ''),
                            row.get('RiskLevelDuringSignIn', ''),
                            row.get('RiskState', ''),
                            row.get('CorrelationId', ''),
                            json.dumps(row),
                            now
                        ))
                        # Check if row was actually inserted (rowcount=0 means duplicate)
                        if cursor.rowcount > 0:
                            records_imported += 1
                        else:
                            records_skipped += 1

                    except Exception as e:
                        records_failed += 1
                        errors.append(f"Row {row_num}: {str(e)}")
                        logger.debug(f"Failed to import row {row_num}: {e}")

            # Update import metadata
            cursor.execute("""
                UPDATE import_metadata
                SET records_imported = ?, records_failed = ?, import_completed = ?
                WHERE id = ?
            """, (records_imported, records_failed, datetime.now().isoformat(), import_id))

            conn.commit()

        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()

        return ImportResult(
            source_file=str(source),
            source_hash=source_hash,
            records_imported=records_imported,
            records_failed=records_failed,
            errors=errors,
            duration_seconds=time.time() - start_time,
            records_skipped=records_skipped
        )

    def import_ual(self, source: Union[str, Path]) -> ImportResult:
        """
        Import Unified Audit Log from CSV.

        Args:
            source: Path to UAL CSV file

        Returns:
            ImportResult with import statistics

        Raises:
            FileNotFoundError: If source file doesn't exist
        """
        source = Path(source)
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source}")

        start_time = time.time()
        source_hash = self._calculate_hash(source)

        # Check if already imported
        if self._is_already_imported(source_hash, 'ual'):
            return ImportResult(
                source_file=str(source),
                source_hash=source_hash,
                records_imported=0,
                records_failed=0,
                errors=[],
                duration_seconds=time.time() - start_time
            )

        records_imported = 0
        records_failed = 0
        records_skipped = 0
        errors: List[str] = []

        conn = self._db.connect()
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        # Record import start
        cursor.execute("""
            INSERT INTO import_metadata
            (source_file, source_hash, log_type, records_imported, records_failed,
             import_started, parser_version)
            VALUES (?, ?, ?, 0, 0, ?, ?)
        """, (str(source), source_hash, 'ual', now, PARSER_VERSION))
        import_id = cursor.lastrowid

        try:
            with open(source, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row_num, row in enumerate(reader, start=2):
                    try:
                        # Parse datetime - UAL uses CreationDate
                        date_str = row.get('CreationDate', row.get('CreatedDateTime', ''))
                        timestamp = parse_m365_datetime(
                            date_str,
                            self._detect_date_format(date_str)
                        )

                        # Extract client IP and object_id from AuditData if not in columns
                        audit_data = row.get('AuditData', '{}')
                        client_ip = row.get('ClientIP', '')
                        object_id = row.get('ObjectId', '')
                        try:
                            audit_json = json.loads(audit_data)
                            if not client_ip:
                                client_ip = audit_json.get('ClientIPAddress', audit_json.get('ClientIP', ''))
                            if not object_id:
                                object_id = audit_json.get('ObjectId', '')
                        except json.JSONDecodeError:
                            pass

                        # INSERT OR IGNORE for deduplication via UNIQUE constraint
                        cursor.execute("""
                            INSERT OR IGNORE INTO unified_audit_log
                            (timestamp, user_id, operation, workload, record_type,
                             result_status, client_ip, object_id, audit_data,
                             raw_record, imported_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            timestamp.isoformat(),
                            row.get('UserIds', row.get('UserId', '')),
                            row.get('Operations', row.get('Operation', '')),
                            row.get('Workload', ''),
                            row.get('RecordType', ''),
                            row.get('ResultStatus', ''),
                            client_ip,
                            object_id,
                            audit_data,
                            json.dumps(row),
                            now
                        ))
                        if cursor.rowcount > 0:
                            records_imported += 1
                        else:
                            records_skipped += 1

                    except Exception as e:
                        records_failed += 1
                        errors.append(f"Row {row_num}: {str(e)}")
                        logger.debug(f"Failed to import UAL row {row_num}: {e}")

            # Update import metadata
            cursor.execute("""
                UPDATE import_metadata
                SET records_imported = ?, records_failed = ?, import_completed = ?
                WHERE id = ?
            """, (records_imported, records_failed, datetime.now().isoformat(), import_id))

            conn.commit()

        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()

        return ImportResult(
            source_file=str(source),
            source_hash=source_hash,
            records_imported=records_imported,
            records_failed=records_failed,
            errors=errors,
            duration_seconds=time.time() - start_time,
            records_skipped=records_skipped
        )

    def import_mailbox_audit(self, source: Union[str, Path]) -> ImportResult:
        """
        Import mailbox audit logs from CSV.

        Args:
            source: Path to mailbox audit CSV file

        Returns:
            ImportResult with import statistics

        Raises:
            FileNotFoundError: If source file doesn't exist
        """
        source = Path(source)
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source}")

        start_time = time.time()
        source_hash = self._calculate_hash(source)

        # Check if already imported
        if self._is_already_imported(source_hash, 'mailbox'):
            return ImportResult(
                source_file=str(source),
                source_hash=source_hash,
                records_imported=0,
                records_failed=0,
                errors=[],
                duration_seconds=time.time() - start_time
            )

        records_imported = 0
        records_failed = 0
        records_skipped = 0
        errors: List[str] = []

        conn = self._db.connect()
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        # Record import start
        cursor.execute("""
            INSERT INTO import_metadata
            (source_file, source_hash, log_type, records_imported, records_failed,
             import_started, parser_version)
            VALUES (?, ?, ?, 0, 0, ?, ?)
        """, (str(source), source_hash, 'mailbox', now, PARSER_VERSION))
        import_id = cursor.lastrowid

        try:
            with open(source, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row_num, row in enumerate(reader, start=2):
                    try:
                        # Parse datetime - try various column names
                        date_str = row.get('LastAccessed', row.get('CreationDate',
                                    row.get('CreatedDateTime', '')))
                        timestamp = parse_m365_datetime(
                            date_str,
                            self._detect_date_format(date_str)
                        )

                        # Extract client IP and item_id from columns or AuditData
                        audit_data = row.get('AuditData', '{}')
                        client_ip = row.get('ClientIPAddress', '')
                        item_id = row.get('ItemId', '')
                        try:
                            audit_json = json.loads(audit_data)
                            if not client_ip:
                                client_ip = audit_json.get('ClientIPAddress', '')
                            if not item_id:
                                item_id = audit_json.get('ItemId', '')
                        except json.JSONDecodeError:
                            pass

                        # INSERT OR IGNORE for deduplication via UNIQUE constraint
                        cursor.execute("""
                            INSERT OR IGNORE INTO mailbox_audit_log
                            (timestamp, user, operation, client_ip, item_id,
                             raw_record, imported_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            timestamp.isoformat(),
                            row.get('MailboxOwnerUPN', row.get('UserIds', row.get('User', ''))),
                            row.get('Operation', row.get('Operations', '')),
                            client_ip,
                            item_id,
                            json.dumps(row),
                            now
                        ))
                        if cursor.rowcount > 0:
                            records_imported += 1
                        else:
                            records_skipped += 1

                    except Exception as e:
                        records_failed += 1
                        errors.append(f"Row {row_num}: {str(e)}")
                        logger.debug(f"Failed to import mailbox row {row_num}: {e}")

            # Update import metadata
            cursor.execute("""
                UPDATE import_metadata
                SET records_imported = ?, records_failed = ?, import_completed = ?
                WHERE id = ?
            """, (records_imported, records_failed, datetime.now().isoformat(), import_id))

            conn.commit()

        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()

        return ImportResult(
            source_file=str(source),
            source_hash=source_hash,
            records_imported=records_imported,
            records_failed=records_failed,
            errors=errors,
            duration_seconds=time.time() - start_time,
            records_skipped=records_skipped
        )

    def import_oauth_consents(self, source: Union[str, Path]) -> ImportResult:
        """
        Import OAuth consents from CSV.

        Maps columns from real M365 export format:
        - ClientId → app_id
        - ConsentType → consent_type
        - PrincipalId → user_principal_name
        - Scope → permissions

        Note: This is a point-in-time snapshot, no timestamp in source.

        Args:
            source: Path to OAuth consents CSV file

        Returns:
            ImportResult with import statistics
        """
        source = Path(source)
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source}")

        start_time = time.time()
        source_hash = self._calculate_hash(source)

        # Check if already imported
        if self._is_already_imported(source_hash, 'oauth'):
            return ImportResult(
                source_file=str(source),
                source_hash=source_hash,
                records_imported=0,
                records_failed=0,
                errors=[],
                duration_seconds=time.time() - start_time
            )

        records_imported = 0
        records_failed = 0
        records_skipped = 0
        errors: List[str] = []

        conn = self._db.connect()
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        # Record import start
        cursor.execute("""
            INSERT INTO import_metadata
            (source_file, source_hash, log_type, records_imported, records_failed,
             import_started, parser_version)
            VALUES (?, ?, ?, 0, 0, ?, ?)
        """, (str(source), source_hash, 'oauth', now, PARSER_VERSION))
        import_id = cursor.lastrowid

        try:
            with open(source, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row_num, row in enumerate(reader, start=2):
                    try:
                        # INSERT OR IGNORE for deduplication via UNIQUE constraint
                        cursor.execute("""
                            INSERT OR IGNORE INTO oauth_consents
                            (timestamp, user_principal_name, app_id, app_display_name,
                             permissions, consent_type, client_ip, risk_score,
                             raw_record, imported_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            now,  # No timestamp in source, use import time
                            row.get('PrincipalId', ''),
                            row.get('ClientId', ''),
                            '',  # app_display_name not in export
                            row.get('Scope', ''),
                            row.get('ConsentType', ''),
                            '',  # client_ip not in export
                            None,  # risk_score
                            json.dumps(row),
                            now
                        ))
                        if cursor.rowcount > 0:
                            records_imported += 1
                        else:
                            records_skipped += 1

                    except Exception as e:
                        records_failed += 1
                        errors.append(f"Row {row_num}: {str(e)}")
                        logger.debug(f"Failed to import OAuth row {row_num}: {e}")

            # Update import metadata
            cursor.execute("""
                UPDATE import_metadata
                SET records_imported = ?, records_failed = ?, import_completed = ?
                WHERE id = ?
            """, (records_imported, records_failed, datetime.now().isoformat(), import_id))

            conn.commit()

        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()

        return ImportResult(
            source_file=str(source),
            source_hash=source_hash,
            records_imported=records_imported,
            records_failed=records_failed,
            errors=errors,
            duration_seconds=time.time() - start_time,
            records_skipped=records_skipped
        )

    def import_inbox_rules(self, source: Union[str, Path]) -> ImportResult:
        """
        Import inbox rules from CSV.

        Maps columns from real M365 export format:
        - Mailbox → user
        - RuleName → rule_name
        - ForwardTo → forward_to
        - ForwardAsAttachmentTo → forward_as_attachment_to
        - RedirectTo → redirect_to
        - DeleteMessage → delete_message (bool)
        - MoveToFolder → move_to_folder

        Note: This is a point-in-time snapshot, no timestamp in source.

        Args:
            source: Path to inbox rules CSV file

        Returns:
            ImportResult with import statistics
        """
        source = Path(source)
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source}")

        start_time = time.time()
        source_hash = self._calculate_hash(source)

        # Check if already imported
        if self._is_already_imported(source_hash, 'inbox_rules'):
            return ImportResult(
                source_file=str(source),
                source_hash=source_hash,
                records_imported=0,
                records_failed=0,
                errors=[],
                duration_seconds=time.time() - start_time
            )

        records_imported = 0
        records_failed = 0
        records_skipped = 0
        errors: List[str] = []

        conn = self._db.connect()
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        # Record import start
        cursor.execute("""
            INSERT INTO import_metadata
            (source_file, source_hash, log_type, records_imported, records_failed,
             import_started, parser_version)
            VALUES (?, ?, ?, 0, 0, ?, ?)
        """, (str(source), source_hash, 'inbox_rules', now, PARSER_VERSION))
        import_id = cursor.lastrowid

        try:
            with open(source, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row_num, row in enumerate(reader, start=2):
                    try:
                        # Parse boolean delete_message
                        delete_msg = row.get('DeleteMessage', 'False')
                        delete_message = 1 if delete_msg.lower() == 'true' else 0

                        # INSERT OR IGNORE for deduplication via UNIQUE constraint
                        cursor.execute("""
                            INSERT OR IGNORE INTO inbox_rules
                            (timestamp, user, operation, rule_name, rule_id,
                             forward_to, forward_as_attachment_to, redirect_to,
                             delete_message, move_to_folder, conditions, client_ip,
                             raw_record, imported_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            now,  # No timestamp in source, use import time
                            row.get('Mailbox', ''),
                            'CurrentRule',  # Snapshot of current rule, not an event
                            row.get('RuleName', ''),
                            '',  # rule_id not in export
                            row.get('ForwardTo', ''),
                            row.get('ForwardAsAttachmentTo', ''),
                            row.get('RedirectTo', ''),
                            delete_message,
                            row.get('MoveToFolder', ''),
                            '',  # conditions not in export
                            '',  # client_ip not in export
                            json.dumps(row),
                            now
                        ))
                        if cursor.rowcount > 0:
                            records_imported += 1
                        else:
                            records_skipped += 1

                    except Exception as e:
                        records_failed += 1
                        errors.append(f"Row {row_num}: {str(e)}")
                        logger.debug(f"Failed to import inbox rule row {row_num}: {e}")

            # Update import metadata
            cursor.execute("""
                UPDATE import_metadata
                SET records_imported = ?, records_failed = ?, import_completed = ?
                WHERE id = ?
            """, (records_imported, records_failed, datetime.now().isoformat(), import_id))

            conn.commit()

        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()

        return ImportResult(
            source_file=str(source),
            source_hash=source_hash,
            records_imported=records_imported,
            records_failed=records_failed,
            errors=errors,
            duration_seconds=time.time() - start_time,
            records_skipped=records_skipped
        )

    def import_all(self, source: Union[str, Path]) -> Dict[str, ImportResult]:
        """
        Auto-detect and import all log types from directory or zip file.

        Automatically detects whether source is a zip file or directory
        and imports accordingly. Zip files are streamed without extraction.

        Args:
            source: Directory or zip file containing M365 log exports

        Returns:
            Dict mapping log type to ImportResult

        Raises:
            FileNotFoundError: If source doesn't exist
            zipfile.BadZipFile: If source is a corrupted zip file
        """
        source = Path(source)

        if not source.exists():
            raise FileNotFoundError(f"Source not found: {source}")

        # Detect source type and dispatch
        if source.is_file() and source.suffix.lower() == '.zip':
            return self._import_from_zip(source)
        elif source.is_dir():
            return self._import_from_directory(source)
        else:
            # Try as zip if it's a file (might not have .zip extension)
            if source.is_file():
                try:
                    return self._import_from_zip(source)
                except zipfile.BadZipFile:
                    raise
            raise FileNotFoundError(f"Source must be a directory or zip file: {source}")

    def _import_from_directory(self, exports_dir: Path) -> Dict[str, ImportResult]:
        """Import from extracted directory (original behavior)."""
        results: Dict[str, ImportResult] = {}

        for file in exports_dir.iterdir():
            if not file.is_file() or not file.suffix.lower() == '.csv':
                continue

            for log_type, pattern in LOG_FILE_PATTERNS.items():
                if re.match(pattern, file.name):
                    try:
                        if log_type == LogType.SIGNIN:
                            results['sign_in'] = self.import_sign_in_logs(file)
                        elif log_type in [LogType.FULL_AUDIT, LogType.AUDIT]:
                            results['ual'] = self.import_ual(file)
                        elif log_type == LogType.MAILBOX_AUDIT:
                            results['mailbox'] = self.import_mailbox_audit(file)
                        elif log_type == LogType.OAUTH_CONSENTS:
                            results['oauth'] = self.import_oauth_consents(file)
                        elif log_type == LogType.INBOX_RULES:
                            results['inbox_rules'] = self.import_inbox_rules(file)
                    except Exception as e:
                        logger.error(f"Failed to import {file.name}: {e}")
                    break

        return results

    def _import_from_zip(self, zip_path: Path) -> Dict[str, ImportResult]:
        """
        Import logs directly from zip file without extraction.

        Streams CSV files from zip archive, matching filenames against
        LOG_FILE_PATTERNS to auto-detect log types.

        Args:
            zip_path: Path to zip file

        Returns:
            Dict mapping log type to ImportResult
        """
        results: Dict[str, ImportResult] = {}

        with zipfile.ZipFile(zip_path, 'r') as zf:
            # Find all CSV files in zip (including subdirectories)
            csv_members = [
                name for name in zf.namelist()
                if name.lower().endswith('.csv') and not name.startswith('__MACOSX')
            ]

            for member_name in csv_members:
                # Get just the filename for pattern matching
                filename = Path(member_name).name

                for log_type, pattern in LOG_FILE_PATTERNS.items():
                    if re.match(pattern, filename):
                        try:
                            # Read zip entry content
                            with zf.open(member_name) as zf_entry:
                                content = zf_entry.read()

                            # Calculate hash from content
                            source_hash = hashlib.sha256(content).hexdigest()

                            # Create source identifier for tracking
                            source_id = f"{zip_path}:{member_name}"

                            # Import based on type
                            if log_type == LogType.SIGNIN:
                                results['sign_in'] = self._import_sign_in_from_bytes(
                                    content, source_id, source_hash
                                )
                            elif log_type in [LogType.FULL_AUDIT, LogType.AUDIT]:
                                results['ual'] = self._import_ual_from_bytes(
                                    content, source_id, source_hash
                                )
                            elif log_type == LogType.MAILBOX_AUDIT:
                                results['mailbox'] = self._import_mailbox_from_bytes(
                                    content, source_id, source_hash
                                )
                            elif log_type == LogType.OAUTH_CONSENTS:
                                results['oauth'] = self._import_oauth_from_bytes(
                                    content, source_id, source_hash
                                )
                            elif log_type == LogType.INBOX_RULES:
                                results['inbox_rules'] = self._import_inbox_rules_from_bytes(
                                    content, source_id, source_hash
                                )
                        except Exception as e:
                            logger.error(f"Failed to import {member_name} from zip: {e}")
                        break

        return results

    def _import_sign_in_from_bytes(
        self, content: bytes, source_id: str, source_hash: str
    ) -> ImportResult:
        """Import sign-in logs from bytes content."""
        start_time = time.time()

        # Check if already imported
        if self._is_already_imported(source_hash, 'sign_in'):
            return ImportResult(
                source_file=source_id,
                source_hash=source_hash,
                records_imported=0,
                records_failed=0,
                errors=[],
                duration_seconds=time.time() - start_time
            )

        records_imported = 0
        records_failed = 0
        records_skipped = 0
        errors: List[str] = []

        conn = self._db.connect()
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        # Record import start
        cursor.execute("""
            INSERT INTO import_metadata
            (source_file, source_hash, log_type, records_imported, records_failed,
             import_started, parser_version)
            VALUES (?, ?, ?, 0, 0, ?, ?)
        """, (source_id, source_hash, 'sign_in', now, PARSER_VERSION))
        import_id = cursor.lastrowid

        try:
            # Parse CSV from bytes
            text_content = content.decode('utf-8-sig')
            reader = csv.DictReader(io.StringIO(text_content))

            for row_num, row in enumerate(reader, start=2):
                try:
                    timestamp = parse_m365_datetime(
                        row.get('CreatedDateTime', ''),
                        self._detect_date_format(row.get('CreatedDateTime', ''))
                    )

                    cursor.execute("""
                        INSERT OR IGNORE INTO sign_in_logs
                        (timestamp, user_principal_name, user_display_name,
                         ip_address, location_city, location_country,
                         client_app, app_display_name, browser, os,
                         status_error_code, conditional_access_status,
                         risk_level, risk_state, correlation_id,
                         raw_record, imported_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        timestamp.isoformat(),
                        row.get('UserPrincipalName', ''),
                        row.get('UserDisplayName', ''),
                        row.get('IPAddress', ''),
                        row.get('City', ''),
                        row.get('Country', ''),
                        row.get('ClientAppUsed', ''),
                        row.get('AppDisplayName', ''),
                        row.get('Browser', ''),
                        row.get('OS', ''),
                        0 if normalize_status(row.get('Status', '')) == 'success' else 1,
                        row.get('ConditionalAccessStatus', ''),
                        row.get('RiskLevelDuringSignIn', ''),
                        row.get('RiskState', ''),
                        row.get('CorrelationId', ''),
                        json.dumps(row),
                        now
                    ))
                    if cursor.rowcount > 0:
                        records_imported += 1
                    else:
                        records_skipped += 1

                except Exception as e:
                    records_failed += 1
                    errors.append(f"Row {row_num}: {str(e)}")

            cursor.execute("""
                UPDATE import_metadata
                SET records_imported = ?, records_failed = ?, import_completed = ?
                WHERE id = ?
            """, (records_imported, records_failed, datetime.now().isoformat(), import_id))

            conn.commit()

        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()

        return ImportResult(
            source_file=source_id,
            source_hash=source_hash,
            records_imported=records_imported,
            records_failed=records_failed,
            errors=errors,
            duration_seconds=time.time() - start_time,
            records_skipped=records_skipped
        )

    def _import_ual_from_bytes(
        self, content: bytes, source_id: str, source_hash: str
    ) -> ImportResult:
        """Import UAL from bytes content."""
        start_time = time.time()

        if self._is_already_imported(source_hash, 'ual'):
            return ImportResult(
                source_file=source_id,
                source_hash=source_hash,
                records_imported=0,
                records_failed=0,
                errors=[],
                duration_seconds=time.time() - start_time
            )

        records_imported = 0
        records_failed = 0
        records_skipped = 0
        errors: List[str] = []

        conn = self._db.connect()
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        cursor.execute("""
            INSERT INTO import_metadata
            (source_file, source_hash, log_type, records_imported, records_failed,
             import_started, parser_version)
            VALUES (?, ?, ?, 0, 0, ?, ?)
        """, (source_id, source_hash, 'ual', now, PARSER_VERSION))
        import_id = cursor.lastrowid

        try:
            text_content = content.decode('utf-8-sig')
            reader = csv.DictReader(io.StringIO(text_content))

            for row_num, row in enumerate(reader, start=2):
                try:
                    date_str = row.get('CreationDate', row.get('CreatedDateTime', ''))
                    timestamp = parse_m365_datetime(
                        date_str,
                        self._detect_date_format(date_str)
                    )

                    audit_data = row.get('AuditData', '{}')
                    client_ip = row.get('ClientIP', '')
                    object_id = row.get('ObjectId', '')
                    try:
                        audit_json = json.loads(audit_data)
                        if not client_ip:
                            client_ip = audit_json.get('ClientIPAddress', audit_json.get('ClientIP', ''))
                        if not object_id:
                            object_id = audit_json.get('ObjectId', '')
                    except json.JSONDecodeError:
                        pass

                    cursor.execute("""
                        INSERT OR IGNORE INTO unified_audit_log
                        (timestamp, user_id, operation, workload, record_type,
                         result_status, client_ip, object_id, audit_data,
                         raw_record, imported_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        timestamp.isoformat(),
                        row.get('UserIds', row.get('UserId', '')),
                        row.get('Operations', row.get('Operation', '')),
                        row.get('Workload', ''),
                        row.get('RecordType', ''),
                        row.get('ResultStatus', ''),
                        client_ip,
                        object_id,
                        audit_data,
                        json.dumps(row),
                        now
                    ))
                    if cursor.rowcount > 0:
                        records_imported += 1
                    else:
                        records_skipped += 1

                except Exception as e:
                    records_failed += 1
                    errors.append(f"Row {row_num}: {str(e)}")

            cursor.execute("""
                UPDATE import_metadata
                SET records_imported = ?, records_failed = ?, import_completed = ?
                WHERE id = ?
            """, (records_imported, records_failed, datetime.now().isoformat(), import_id))

            conn.commit()

        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()

        return ImportResult(
            source_file=source_id,
            source_hash=source_hash,
            records_imported=records_imported,
            records_failed=records_failed,
            errors=errors,
            duration_seconds=time.time() - start_time,
            records_skipped=records_skipped
        )

    def _import_mailbox_from_bytes(
        self, content: bytes, source_id: str, source_hash: str
    ) -> ImportResult:
        """Import mailbox audit from bytes content."""
        start_time = time.time()

        if self._is_already_imported(source_hash, 'mailbox'):
            return ImportResult(
                source_file=source_id,
                source_hash=source_hash,
                records_imported=0,
                records_failed=0,
                errors=[],
                duration_seconds=time.time() - start_time
            )

        records_imported = 0
        records_failed = 0
        records_skipped = 0
        errors: List[str] = []

        conn = self._db.connect()
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        cursor.execute("""
            INSERT INTO import_metadata
            (source_file, source_hash, log_type, records_imported, records_failed,
             import_started, parser_version)
            VALUES (?, ?, ?, 0, 0, ?, ?)
        """, (source_id, source_hash, 'mailbox', now, PARSER_VERSION))
        import_id = cursor.lastrowid

        try:
            text_content = content.decode('utf-8-sig')
            reader = csv.DictReader(io.StringIO(text_content))

            for row_num, row in enumerate(reader, start=2):
                try:
                    date_str = row.get('LastAccessed', row.get('CreationDate',
                                row.get('CreatedDateTime', '')))
                    timestamp = parse_m365_datetime(
                        date_str,
                        self._detect_date_format(date_str)
                    )

                    audit_data = row.get('AuditData', '{}')
                    client_ip = row.get('ClientIPAddress', '')
                    item_id = row.get('ItemId', '')
                    try:
                        audit_json = json.loads(audit_data)
                        if not client_ip:
                            client_ip = audit_json.get('ClientIPAddress', '')
                        if not item_id:
                            item_id = audit_json.get('ItemId', '')
                    except json.JSONDecodeError:
                        pass

                    cursor.execute("""
                        INSERT OR IGNORE INTO mailbox_audit_log
                        (timestamp, user, operation, client_ip, item_id,
                         raw_record, imported_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        timestamp.isoformat(),
                        row.get('MailboxOwnerUPN', row.get('UserIds', row.get('User', ''))),
                        row.get('Operation', row.get('Operations', '')),
                        client_ip,
                        item_id,
                        json.dumps(row),
                        now
                    ))
                    if cursor.rowcount > 0:
                        records_imported += 1
                    else:
                        records_skipped += 1

                except Exception as e:
                    records_failed += 1
                    errors.append(f"Row {row_num}: {str(e)}")

            cursor.execute("""
                UPDATE import_metadata
                SET records_imported = ?, records_failed = ?, import_completed = ?
                WHERE id = ?
            """, (records_imported, records_failed, datetime.now().isoformat(), import_id))

            conn.commit()

        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()

        return ImportResult(
            source_file=source_id,
            source_hash=source_hash,
            records_imported=records_imported,
            records_failed=records_failed,
            errors=errors,
            duration_seconds=time.time() - start_time,
            records_skipped=records_skipped
        )

    def _import_oauth_from_bytes(
        self, content: bytes, source_id: str, source_hash: str
    ) -> ImportResult:
        """Import OAuth consents from bytes content."""
        start_time = time.time()

        if self._is_already_imported(source_hash, 'oauth'):
            return ImportResult(
                source_file=source_id,
                source_hash=source_hash,
                records_imported=0,
                records_failed=0,
                errors=[],
                duration_seconds=time.time() - start_time
            )

        records_imported = 0
        records_failed = 0
        records_skipped = 0
        errors: List[str] = []

        conn = self._db.connect()
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        cursor.execute("""
            INSERT INTO import_metadata
            (source_file, source_hash, log_type, records_imported, records_failed,
             import_started, parser_version)
            VALUES (?, ?, ?, 0, 0, ?, ?)
        """, (source_id, source_hash, 'oauth', now, PARSER_VERSION))
        import_id = cursor.lastrowid

        try:
            text_content = content.decode('utf-8-sig')
            reader = csv.DictReader(io.StringIO(text_content))

            for row_num, row in enumerate(reader, start=2):
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO oauth_consents
                        (timestamp, user_principal_name, app_id, app_display_name,
                         permissions, consent_type, client_ip, risk_score,
                         raw_record, imported_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        now,
                        row.get('PrincipalId', ''),
                        row.get('ClientId', ''),
                        '',
                        row.get('Scope', ''),
                        row.get('ConsentType', ''),
                        '',
                        None,
                        json.dumps(row),
                        now
                    ))
                    if cursor.rowcount > 0:
                        records_imported += 1
                    else:
                        records_skipped += 1

                except Exception as e:
                    records_failed += 1
                    errors.append(f"Row {row_num}: {str(e)}")

            cursor.execute("""
                UPDATE import_metadata
                SET records_imported = ?, records_failed = ?, import_completed = ?
                WHERE id = ?
            """, (records_imported, records_failed, datetime.now().isoformat(), import_id))

            conn.commit()

        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()

        return ImportResult(
            source_file=source_id,
            source_hash=source_hash,
            records_imported=records_imported,
            records_failed=records_failed,
            errors=errors,
            duration_seconds=time.time() - start_time,
            records_skipped=records_skipped
        )

    def _import_inbox_rules_from_bytes(
        self, content: bytes, source_id: str, source_hash: str
    ) -> ImportResult:
        """Import inbox rules from bytes content."""
        start_time = time.time()

        if self._is_already_imported(source_hash, 'inbox_rules'):
            return ImportResult(
                source_file=source_id,
                source_hash=source_hash,
                records_imported=0,
                records_failed=0,
                errors=[],
                duration_seconds=time.time() - start_time
            )

        records_imported = 0
        records_failed = 0
        records_skipped = 0
        errors: List[str] = []

        conn = self._db.connect()
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        cursor.execute("""
            INSERT INTO import_metadata
            (source_file, source_hash, log_type, records_imported, records_failed,
             import_started, parser_version)
            VALUES (?, ?, ?, 0, 0, ?, ?)
        """, (source_id, source_hash, 'inbox_rules', now, PARSER_VERSION))
        import_id = cursor.lastrowid

        try:
            text_content = content.decode('utf-8-sig')
            reader = csv.DictReader(io.StringIO(text_content))

            for row_num, row in enumerate(reader, start=2):
                try:
                    delete_msg = row.get('DeleteMessage', 'False')
                    delete_message = 1 if delete_msg.lower() == 'true' else 0

                    cursor.execute("""
                        INSERT OR IGNORE INTO inbox_rules
                        (timestamp, user, operation, rule_name, rule_id,
                         forward_to, forward_as_attachment_to, redirect_to,
                         delete_message, move_to_folder, conditions, client_ip,
                         raw_record, imported_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        now,
                        row.get('Mailbox', ''),
                        'CurrentRule',
                        row.get('RuleName', ''),
                        '',
                        row.get('ForwardTo', ''),
                        row.get('ForwardAsAttachmentTo', ''),
                        row.get('RedirectTo', ''),
                        delete_message,
                        row.get('MoveToFolder', ''),
                        '',
                        '',
                        json.dumps(row),
                        now
                    ))
                    if cursor.rowcount > 0:
                        records_imported += 1
                    else:
                        records_skipped += 1

                except Exception as e:
                    records_failed += 1
                    errors.append(f"Row {row_num}: {str(e)}")

            cursor.execute("""
                UPDATE import_metadata
                SET records_imported = ?, records_failed = ?, import_completed = ?
                WHERE id = ?
            """, (records_imported, records_failed, datetime.now().isoformat(), import_id))

            conn.commit()

        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()

        return ImportResult(
            source_file=source_id,
            source_hash=source_hash,
            records_imported=records_imported,
            records_failed=records_failed,
            errors=errors,
            duration_seconds=time.time() - start_time,
            records_skipped=records_skipped
        )

    def _calculate_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file."""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _is_already_imported(self, source_hash: str, log_type: str) -> bool:
        """Check if file was already imported."""
        conn = self._db.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM import_metadata
            WHERE source_hash = ? AND log_type = ?
        """, (source_hash, log_type))
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0

    def _detect_date_format(self, date_str: str) -> str:
        """Detect date format from string."""
        if not date_str:
            return "AU"

        # Extract date part
        date_part = date_str.split()[0] if ' ' in date_str else date_str

        # Try to parse
        match = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{4})$', date_part)
        if not match:
            return "AU"

        first, second, _ = int(match.group(1)), int(match.group(2)), int(match.group(3))

        # If first > 12, must be day (AU format)
        if first > 12:
            return "AU"
        # If second > 12, first must be month (US format)
        if second > 12:
            return "US"

        # Default to AU for Australian tenants
        return "AU"


if __name__ == "__main__":
    # Quick demo
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test CSV
        csv_path = Path(tmpdir) / "test_signin.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['CreatedDateTime', 'UserPrincipalName', 'IPAddress'])
            writer.writeheader()
            writer.writerow({
                'CreatedDateTime': '15/12/2025 9:30:00 AM',
                'UserPrincipalName': 'test@example.com',
                'IPAddress': '1.2.3.4'
            })

        db = IRLogDatabase(case_id="PIR-DEMO-2025-001", base_path=tmpdir)
        db.create()

        importer = LogImporter(db)
        result = importer.import_sign_in_logs(csv_path)

        print(f"Imported: {result.records_imported}, Failed: {result.records_failed}")
        print(f"Hash: {result.source_hash}")
        print(f"Duration: {result.duration_seconds:.3f}s")
