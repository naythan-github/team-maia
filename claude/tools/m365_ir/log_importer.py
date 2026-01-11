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

from .compression import compress_json
from .log_database import IRLogDatabase
from .m365_log_parser import (
    M365LogParser,
    LogType,
    LOG_FILE_PATTERNS,
    parse_m365_datetime,
    normalize_status,
)
from .log_coverage import update_log_coverage_summary
from .powershell_validation import check_powershell_object_corruption, validate_all_tables

# Configure module logger
logger = logging.getLogger(__name__)

# Parser version for tracking
PARSER_VERSION = "1.0.0"


def _extract_case_id_from_db_path(db_path: Path) -> Optional[str]:
    """
    Extract case_id from database path.

    Expected: ~/work_projects/ir_cases/{case_id}/{case_id}_logs.db

    Example: PIR-OCULUS-2025-12-19_logs.db → PIR-OCULUS-2025-12-19

    Args:
        db_path: Path to database file

    Returns:
        Case ID string if extractable, None otherwise
    """
    try:
        db_filename = db_path.name
        if db_filename.endswith('_logs.db'):
            return db_filename[:-8]  # Remove "_logs.db"
    except Exception as e:
        logger.warning(f"Failed to extract case_id from {db_path}: {e}")

    return None


class DataQualityError(Exception):
    """
    Raised when data quality checks fail during import.

    This exception is raised when:
    - Overall quality score < 0.5 (threshold)
    - Too many unreliable fields detected
    - Critical fields are 100% uniform

    Attributes:
        message: Error message with quality score and recommendations
        quality_score: Overall quality score (0-1)
        unreliable_fields: List of unreliable field names
        recommendations: Suggested actions to fix quality issues
    """

    def __init__(
        self,
        message: str,
        quality_score: float = 0.0,
        unreliable_fields: List[str] = None,
        recommendations: List[str] = None
    ):
        super().__init__(message)
        self.quality_score = quality_score
        self.unreliable_fields = unreliable_fields or []
        self.recommendations = recommendations or []


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
            # Phase 264: Use schema-aware parser
            parser = M365LogParser()
            entries = parser.parse_with_schema(source)

            for entry_num, entry in enumerate(entries, start=1):
                try:
                    # INSERT OR IGNORE for deduplication via UNIQUE constraint
                    cursor.execute("""
                        INSERT OR IGNORE INTO sign_in_logs
                        (timestamp, user_principal_name, user_display_name,
                         ip_address, location_city, location_country,
                         client_app, app_display_name, browser, os,
                         status_error_code, conditional_access_status,
                         risk_level, risk_state, correlation_id,
                         raw_record, imported_at,
                         schema_variant, sign_in_type, is_service_principal,
                         service_principal_id, service_principal_name,
                         user_id, request_id, auth_requirement, mfa_result,
                         latency_ms, device_compliant, device_managed,
                         credential_key_id, resource_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        entry.timestamp.isoformat() if entry.timestamp else None,
                        entry.user_principal_name or '',
                        entry.user_display_name or '',
                        entry.ip_address or '',
                        entry.city or '',
                        entry.country or '',
                        getattr(entry, 'client_app', '') or '',
                        entry.app_display_name or '',
                        entry.browser or '',
                        entry.os or '',
                        getattr(entry, 'status_error_code', 0) or 0,
                        entry.conditional_access_status or '',
                        getattr(entry, 'risk_level_during_signin', '') or '',
                        entry.risk_state or '',
                        getattr(entry, 'correlation_id', '') or '',
                        compress_json(getattr(entry, 'raw_data', {})),
                        now,
                        # Phase 264: Multi-schema ETL fields
                        entry.schema_variant or '',
                        entry.sign_in_type or '',
                        1 if entry.is_service_principal else 0,
                        entry.service_principal_id or '',
                        entry.service_principal_name or '',
                        entry.user_id or '',
                        entry.request_id or '',
                        entry.auth_requirement or '',
                        entry.mfa_result or '',
                        entry.latency_ms,
                        1 if entry.device_compliant else None,
                        1 if entry.device_managed else None,
                        entry.credential_key_id or '',
                        entry.resource_id or ''
                    ))
                    # Check if row was actually inserted (rowcount=0 means duplicate)
                    if cursor.rowcount > 0:
                        records_imported += 1
                    else:
                        records_skipped += 1

                except Exception as e:
                    records_failed += 1
                    errors.append(f"Entry {entry_num}: {str(e)}")
                    logger.debug(f"Failed to import entry {entry_num}: {e}")

            # Update import metadata
            cursor.execute("""
                UPDATE import_metadata
                SET records_imported = ?, records_failed = ?, import_completed = ?
                WHERE id = ?
            """, (records_imported, records_failed, datetime.now().isoformat(), import_id))

            # Phase 1.2: Run quality checks BEFORE commit (fail-fast mode)
            if records_imported > 0:
                try:
                    from .data_quality_checker import check_table_quality

                    quality_report = check_table_quality(
                        str(self._db.db_path),
                        'sign_in_logs',
                        conn=conn  # Pass existing connection to see uncommitted data
                    )

                    # Check if quality_check_summary table exists
                    cursor.execute("""
                        SELECT name FROM sqlite_master
                        WHERE type='table' AND name='quality_check_summary'
                    """)

                    if cursor.fetchone():
                        # Store quality check results
                        cursor.execute("""
                            INSERT INTO quality_check_summary
                            (table_name, overall_quality_score, reliable_fields_count,
                             unreliable_fields_count, check_passed, warnings, recommendations, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            'sign_in_logs',
                            quality_report.overall_quality_score,
                            len(quality_report.reliable_fields),
                            len(quality_report.unreliable_fields),
                            1 if quality_report.overall_quality_score >= 0.5 else 0,
                            '; '.join(quality_report.warnings) if quality_report.warnings else None,
                            '; '.join(quality_report.recommendations) if quality_report.recommendations else None,
                            quality_report.created_at
                        ))

                    # Fail-fast: Raise error if quality score below threshold
                    if quality_report.overall_quality_score < 0.5:
                        error_msg = (
                            f"Data quality check FAILED: Quality score {quality_report.overall_quality_score:.2f} "
                            f"is below threshold (0.5). Import aborted.\n\n"
                            f"Unreliable fields ({len(quality_report.unreliable_fields)}): "
                            f"{', '.join(quality_report.unreliable_fields)}\n\n"
                        )
                        if quality_report.recommendations:
                            error_msg += "Recommendations:\n"
                            for rec in quality_report.recommendations:
                                error_msg += f"  - {rec}\n"

                        raise DataQualityError(
                            error_msg,
                            quality_score=quality_report.overall_quality_score,
                            unreliable_fields=quality_report.unreliable_fields,
                            recommendations=quality_report.recommendations
                        )

                    # Log quality warnings (even if check passed)
                    if quality_report.warnings:
                        print(f"\n⚠️  Data quality warnings:")
                        for warning in quality_report.warnings:
                            print(f"   - {warning}")

                    logger.info(
                        f"Quality check passed: Score {quality_report.overall_quality_score:.2f}, "
                        f"{len(quality_report.reliable_fields)} reliable fields, "
                        f"{len(quality_report.unreliable_fields)} unreliable fields"
                    )

                except DataQualityError:
                    # Re-raise quality errors (will be caught by outer except and rolled back)
                    raise
                except Exception as e:
                    # Don't fail import if quality check itself fails
                    logger.warning(f"Quality check failed to run: {e}")

            conn.commit()

            # Phase 1.1: Auto-verify sign-in status after import
            if records_imported > 0:
                try:
                    from .auth_verifier import verify_sign_in_status

                    result = verify_sign_in_status(str(self._db.db_path))

                    # Store verification results
                    verification_status = 'BREACH_DETECTED' if result.breach_detected else 'OK'
                    cursor.execute("""
                        INSERT INTO verification_summary
                        (log_type, total_records, success_count, failure_count,
                         success_rate, verification_status, notes, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        'sign_in_logs',
                        result.total_records,
                        result.success_count,
                        result.failure_count,
                        result.success_rate,
                        verification_status,
                        f"Foreign success: {result.foreign_success_count} ({result.foreign_success_rate:.1f}%). "
                        f"Field used: {result.status_field_used}. "
                        f"Warnings: {'; '.join(result.warnings) if result.warnings else 'None'}",
                        result.created_at
                    ))
                    conn.commit()

                    # Phase 2.1.4: Store field usage outcome for learning
                    try:
                        from .auth_verifier import HISTORICAL_DB_PATH, USE_PHASE_2_1_SCORING
                        from .field_reliability_scorer import store_field_usage

                        if USE_PHASE_2_1_SCORING and hasattr(result, 'field_used') and result.field_used:
                            case_id = _extract_case_id_from_db_path(self._db.db_path)

                            if case_id:
                                verification_successful = not any('CRITICAL' in w for w in result.warnings)

                                store_field_usage(
                                    history_db_path=str(HISTORICAL_DB_PATH),
                                    case_id=case_id,
                                    log_type='sign_in_logs',
                                    field_name=result.field_used,
                                    reliability_score=result.field_score or 0.5,
                                    used_for_verification=True,
                                    verification_successful=verification_successful,
                                    breach_detected=result.breach_detected,
                                    notes=f"Foreign success: {result.foreign_success_rate:.1f}%"
                                )

                                logger.info(f"Stored field usage: {result.field_used} (case: {case_id})")

                    except Exception as e:
                        logger.warning(f"Failed to store field usage: {e}")

                    # Print verification summary
                    print(f"\n✅ Sign-in logs auto-verification completed:")
                    print(f"   Total: {result.total_records} records")
                    print(f"   Successful: {result.success_count} ({result.success_rate:.1f}%)")
                    print(f"   Failed: {result.failure_count} ({100-result.success_rate:.1f}%)")
                    print(f"   Foreign success: {result.foreign_success_count} ({result.foreign_success_rate:.1f}%)")

                    if result.breach_detected:
                        print(f"   ⚠️  BREACH DETECTED: {result.alert_severity}")

                    if result.warnings:
                        for warning in result.warnings:
                            print(f"   ⚠️  {warning}")

                except Exception as e:
                    logger.warning(f"Auto-verification failed: {e}")

                    # Store failed verification in verification_summary
                    try:
                        total_records = cursor.execute(
                            "SELECT COUNT(*) FROM sign_in_logs"
                        ).fetchone()[0]

                        cursor.execute("""
                            INSERT INTO verification_summary
                            (log_type, total_records, success_count, failure_count,
                             success_rate, verification_status, notes, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            'sign_in_logs',
                            total_records,
                            0,
                            0,
                            0.0,
                            'VERIFICATION_FAILED',
                            f"Verification failed: {str(e)}",
                            datetime.now().isoformat()
                        ))
                        conn.commit()
                    except Exception as storage_error:
                        logger.warning(f"Failed to store verification failure: {storage_error}")

                    # Don't fail import if verification fails

            # Phase 1.3: Scan for unknown status codes
            if records_imported > 0:
                try:
                    from .status_code_manager import StatusCodeManager

                    manager = StatusCodeManager(str(self._db.db_path))

                    # Scan for unknown status_error_code values
                    unknown_codes = manager.scan_for_unknown_codes(
                        log_type='sign_in_logs',
                        field_name='status_error_code'
                    )

                    if unknown_codes:
                        print(f"\n⚠️  Unknown status codes detected:")
                        for code_info in unknown_codes[:5]:  # Show first 5
                            print(f"   - Code '{code_info['code_value']}' appears {code_info['count']} times")
                        if len(unknown_codes) > 5:
                            print(f"   - ... and {len(unknown_codes) - 5} more unknown codes")

                        logger.warning(
                            f"Found {len(unknown_codes)} unknown status code(s) in sign_in_logs. "
                            f"Consider updating status_code_reference table."
                        )

                except Exception as e:
                    logger.warning(f"Unknown code detection failed: {e}")
                    # Don't fail import if code detection fails

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
                            compress_json(audit_data),
                            compress_json(row),
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

            # Phase 1.1: Auto-verify unified audit log after import
            if records_imported > 0:
                try:
                    from .auth_verifier import verify_audit_log_operations

                    result = verify_audit_log_operations(str(self._db.db_path))

                    # Store verification results
                    verification_status = 'EXFILTRATION_INDICATOR' if result.exfiltration_indicator else 'OK'
                    cursor.execute("""
                        INSERT INTO verification_summary
                        (log_type, total_records, success_count, failure_count,
                         success_rate, verification_status, notes, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        'unified_audit_log',
                        result.total_records,
                        0,  # N/A for audit logs
                        0,  # N/A for audit logs
                        0.0,  # N/A for audit logs
                        verification_status,
                        f"MailItemsAccessed: {result.mail_items_accessed}. "
                        f"FileSyncDownloadedFull: {result.file_sync_downloaded}. "
                        f"Exfiltration indicator: {result.exfiltration_indicator}",
                        result.created_at
                    ))
                    conn.commit()

                    # Print verification summary
                    print(f"\n✅ Unified audit log auto-verification completed:")
                    print(f"   Total: {result.total_records} records")
                    print(f"   MailItemsAccessed: {result.mail_items_accessed}")
                    print(f"   FileSyncDownloadedFull: {result.file_sync_downloaded}")

                    if result.exfiltration_indicator:
                        print(f"   ⚠️  EXFILTRATION INDICATOR DETECTED")

                except Exception as e:
                    logger.warning(f"Auto-verification failed: {e}")
                    # Don't fail import if verification fails

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
                            compress_json(row),
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
                            compress_json(row),
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
                            compress_json(row),
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

    def import_legacy_auth(self, source: Union[str, Path]) -> ImportResult:
        """
        Import legacy authentication sign-in logs from CSV.

        Parses legacy auth logs (IMAP, POP3, SMTP) which bypass MFA.
        Uses Australian date format (DD/MM/YYYY H:MM:SS AM/PM).

        Args:
            source: Path to legacy auth CSV file

        Returns:
            ImportResult with import statistics
        """
        source = Path(source)
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source}")

        start_time = time.time()
        source_hash = self._calculate_hash(source)

        # Check if already imported
        if self._is_already_imported(source_hash, 'legacy_auth'):
            return ImportResult(
                source_file=str(source),
                source_hash=source_hash,
                records_imported=0,
                records_failed=0,
                errors=[],
                duration_seconds=time.time() - start_time
            )

        with open(source, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            return self._import_legacy_auth_internal(
                reader, str(source), source_hash, start_time
            )

    def _import_legacy_auth_internal(
        self,
        reader: csv.DictReader,
        source_id: str,
        source_hash: str,
        start_time: float
    ) -> ImportResult:
        """
        Internal method to import legacy auth logs from a CSV reader.

        Shared implementation for both file-based and bytes-based imports.

        Args:
            reader: CSV DictReader (from file or StringIO)
            source_id: Source identifier for tracking
            source_hash: SHA256 hash of source
            start_time: Import start time for duration calculation

        Returns:
            ImportResult with import statistics
        """
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
        """, (source_id, source_hash, 'legacy_auth', now, PARSER_VERSION))
        import_id = cursor.lastrowid

        try:
            for row_num, row in enumerate(reader, start=2):
                try:
                    # Parse datetime with AU format
                    timestamp = parse_m365_datetime(
                        row.get('CreatedDateTime', ''),
                        self._detect_date_format(row.get('CreatedDateTime', ''))
                    )

                    # INSERT OR IGNORE for deduplication via UNIQUE constraint
                    cursor.execute("""
                        INSERT OR IGNORE INTO legacy_auth_logs
                        (timestamp, user_principal_name, user_display_name,
                         client_app_used, app_display_name, ip_address, city,
                         country, status, failure_reason, conditional_access_status,
                         raw_record, imported_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        timestamp.isoformat(),
                        row.get('UserPrincipalName', ''),
                        row.get('UserDisplayName', ''),
                        row.get('ClientAppUsed', ''),
                        row.get('AppDisplayName', ''),
                        row.get('IPAddress', ''),
                        row.get('City', ''),
                        row.get('Country', ''),
                        row.get('Status', ''),
                        row.get('FailureReason', ''),
                        row.get('ConditionalAccessStatus', ''),
                        compress_json(row),
                        now
                    ))
                    if cursor.rowcount > 0:
                        records_imported += 1
                    else:
                        records_skipped += 1

                except Exception as e:
                    records_failed += 1
                    errors.append(f"Row {row_num}: {str(e)}")
                    logger.debug(f"Failed to import legacy auth row {row_num}: {e}")

            # Update import metadata
            cursor.execute("""
                UPDATE import_metadata
                SET records_imported = ?, records_failed = ?, import_completed = ?
                WHERE id = ?
            """, (records_imported, records_failed, datetime.now().isoformat(), import_id))

            conn.commit()

            # Phase 241: Auto-verify authentication status after import
            if records_imported > 0:
                try:
                    from .auth_verifier import verify_auth_status, store_verification

                    result = verify_auth_status(conn, log_type='legacy_auth')
                    store_verification(conn, result)

                    # Print verification summary
                    print(f"\n✅ Auto-verification completed:")
                    print(f"   Total: {result.total_events} events")
                    print(f"   Successful: {result.successful} ({result.success_rate:.1f}%)")
                    print(f"   Failed: {result.failed} ({100-result.success_rate:.1f}%)")

                    if result.warnings:
                        for warning in result.warnings:
                            print(f"   {warning}")

                except Exception as e:
                    logger.warning(f"Auto-verification failed: {e}")
                    # Don't fail import if verification fails

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

    def import_password_status(self, source: Union[str, Path]) -> ImportResult:
        """
        Import password last changed status from CSV.

        Uses INSERT OR REPLACE for single record per user.
        Uses Australian date format (DD/MM/YYYY H:MM:SS AM/PM).

        Args:
            source: Path to password status CSV file

        Returns:
            ImportResult with import statistics
        """
        source = Path(source)
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source}")

        start_time = time.time()
        source_hash = self._calculate_hash(source)

        # Note: We don't skip password_status imports because they're point-in-time
        # snapshots that should be replaced with newer data

        with open(source, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            return self._import_password_status_internal(
                reader, str(source), source_hash, start_time
            )

    def _import_password_status_internal(
        self,
        reader: csv.DictReader,
        source_id: str,
        source_hash: str,
        start_time: float
    ) -> ImportResult:
        """
        Internal method to import password status from a CSV reader.

        Shared implementation for both file-based and bytes-based imports.

        Args:
            reader: CSV DictReader (from file or StringIO)
            source_id: Source identifier for tracking
            source_hash: SHA256 hash of source
            start_time: Import start time for duration calculation

        Returns:
            ImportResult with import statistics
        """
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
        """, (source_id, source_hash, 'password_status', now, PARSER_VERSION))
        import_id = cursor.lastrowid

        try:
            for row_num, row in enumerate(reader, start=2):
                try:
                    # Parse datetime with AU format
                    last_change = None
                    last_change_str = row.get('LastPasswordChangeDateTime', '')
                    if last_change_str:
                        last_change = parse_m365_datetime(
                            last_change_str,
                            self._detect_date_format(last_change_str)
                        )

                    created = None
                    created_str = row.get('CreatedDateTime', '')
                    if created_str:
                        created = parse_m365_datetime(
                            created_str,
                            self._detect_date_format(created_str)
                        )

                    # Parse days_since_change as integer
                    days_str = row.get('DaysSinceChange', '')
                    days_since_change = int(days_str) if days_str.isdigit() else None

                    # INSERT OR REPLACE for single record per user
                    cursor.execute("""
                        INSERT OR REPLACE INTO password_status
                        (user_principal_name, display_name, last_password_change,
                         days_since_change, password_policies, account_enabled,
                         created_datetime, raw_record, imported_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row.get('UserPrincipalName', ''),
                        row.get('DisplayName', ''),
                        last_change.isoformat() if last_change else None,
                        days_since_change,
                        row.get('PasswordPolicies', ''),
                        row.get('AccountEnabled', ''),
                        created.isoformat() if created else None,
                        compress_json(row),
                        now
                    ))
                    records_imported += 1

                except Exception as e:
                    records_failed += 1
                    errors.append(f"Row {row_num}: {str(e)}")
                    logger.debug(f"Failed to import password status row {row_num}: {e}")

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
            source_file=source_id,
            source_hash=source_hash,
            records_imported=records_imported,
            records_failed=records_failed,
            errors=errors,
            duration_seconds=time.time() - start_time,
            records_skipped=records_skipped
        )

    def import_mfa_changes(self, source: Union[str, Path]) -> ImportResult:
        """
        Import MFA registration/change events from CSV.

        Expected columns: ActivityDateTime, ActivityDisplayName, User, Result

        Args:
            source: Path to MFA changes CSV file

        Returns:
            ImportResult with import statistics
        """
        source = Path(source)
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source}")

        start_time = time.time()
        source_hash = self._calculate_hash(source)

        # Check if already imported
        if self._is_already_imported(source_hash, 'mfa_changes'):
            logger.info(f"Skipping duplicate MFA changes import: {source}")
            return ImportResult(
                source_file=str(source),
                source_hash=source_hash,
                records_imported=0,
                records_failed=0,
                errors=["Duplicate import skipped"],
                duration_seconds=time.time() - start_time,
                records_skipped=0
            )

        with open(source, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            return self._import_mfa_changes_internal(
                reader, str(source), source_hash, start_time
            )

    def _import_mfa_changes_internal(
        self,
        reader: csv.DictReader,
        source_id: str,
        source_hash: str,
        start_time: float
    ) -> ImportResult:
        """
        Internal method to import MFA changes from a CSV reader.

        Args:
            reader: CSV DictReader
            source_id: Source identifier for tracking
            source_hash: SHA256 hash of source
            start_time: Import start time for duration calculation

        Returns:
            ImportResult with import statistics
        """
        records_imported = 0
        records_failed = 0
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
        """, (source_id, source_hash, 'mfa_changes', now, PARSER_VERSION))
        import_id = cursor.lastrowid

        try:
            for row_num, row in enumerate(reader, start=2):
                try:
                    # Parse timestamp
                    timestamp_str = row.get('ActivityDateTime', '')
                    timestamp = None
                    if timestamp_str:
                        timestamp = parse_m365_datetime(
                            timestamp_str,
                            self._detect_date_format(timestamp_str)
                        )

                    cursor.execute("""
                        INSERT INTO mfa_changes
                        (timestamp, activity_display_name, user, result, imported_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        timestamp.isoformat() if timestamp else None,
                        row.get('ActivityDisplayName', ''),
                        row.get('User', ''),
                        row.get('Result', ''),
                        now
                    ))
                    records_imported += 1

                except Exception as e:
                    records_failed += 1
                    errors.append(f"Row {row_num}: {str(e)}")
                    logger.debug(f"Failed to import MFA changes row {row_num}: {e}")

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
            source_file=source_id,
            source_hash=source_hash,
            records_imported=records_imported,
            records_failed=records_failed,
            errors=errors,
            duration_seconds=time.time() - start_time,
            records_skipped=0
        )

    def import_risky_users(self, source: Union[str, Path]) -> ImportResult:
        """
        Import risky user detections from CSV.

        Expected columns vary but may include: UserPrincipalName, RiskLevel,
        RiskState, RiskDetail, RiskLastUpdatedDateTime

        Args:
            source: Path to risky users CSV file

        Returns:
            ImportResult with import statistics
        """
        source = Path(source)
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source}")

        start_time = time.time()
        source_hash = self._calculate_hash(source)

        # Check if already imported
        if self._is_already_imported(source_hash, 'risky_users'):
            logger.info(f"Skipping duplicate risky users import: {source}")
            return ImportResult(
                source_file=str(source),
                source_hash=source_hash,
                records_imported=0,
                records_failed=0,
                errors=["Duplicate import skipped"],
                duration_seconds=time.time() - start_time,
                records_skipped=0
            )

        with open(source, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            return self._import_risky_users_internal(
                reader, str(source), source_hash, start_time
            )

    def _import_risky_users_internal(
        self,
        reader: csv.DictReader,
        source_id: str,
        source_hash: str,
        start_time: float
    ) -> ImportResult:
        """
        Internal method to import risky users from a CSV reader.

        Args:
            reader: CSV DictReader
            source_id: Source identifier for tracking
            source_hash: SHA256 hash of source
            start_time: Import start time for duration calculation

        Returns:
            ImportResult with import statistics
        """
        records_imported = 0
        records_failed = 0
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
        """, (source_id, source_hash, 'risky_users', now, PARSER_VERSION))
        import_id = cursor.lastrowid

        try:
            for row_num, row in enumerate(reader, start=2):
                try:
                    # Parse risk last updated timestamp
                    risk_updated_str = row.get('RiskLastUpdatedDateTime', '')
                    risk_updated = None
                    if risk_updated_str:
                        risk_updated = parse_m365_datetime(
                            risk_updated_str,
                            self._detect_date_format(risk_updated_str)
                        )

                    cursor.execute("""
                        INSERT INTO risky_users
                        (user_principal_name, risk_level, risk_state, risk_detail,
                         risk_last_updated, imported_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        row.get('UserPrincipalName', ''),
                        row.get('RiskLevel', ''),
                        row.get('RiskState', ''),
                        row.get('RiskDetail', ''),
                        risk_updated.isoformat() if risk_updated else None,
                        now
                    ))
                    records_imported += 1

                except Exception as e:
                    records_failed += 1
                    errors.append(f"Row {row_num}: {str(e)}")
                    logger.debug(f"Failed to import risky user row {row_num}: {e}")

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
            source_file=source_id,
            source_hash=source_hash,
            records_imported=records_imported,
            records_failed=records_failed,
            errors=errors,
            duration_seconds=time.time() - start_time,
            records_skipped=0
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
        results = None
        if source.is_file() and source.suffix.lower() == '.zip':
            results = self._import_from_zip(source)
        elif source.is_dir():
            results = self._import_from_directory(source)
        else:
            # Try as zip if it's a file (might not have .zip extension)
            if source.is_file():
                try:
                    results = self._import_from_zip(source)
                except zipfile.BadZipFile:
                    raise
            else:
                raise FileNotFoundError(f"Source must be a directory or zip file: {source}")

        # Phase 258: Post-import validation (PIR-FYNA-2025-12-08 lessons learned)
        if results:
            self._run_post_import_validation(results)

        return results

    def _run_post_import_validation(self, results: Dict[str, 'ImportResult']) -> None:
        """
        Run Phase 258 post-import validation checks.

        PIR-FYNA-2025-12-08 lessons learned - automatically detects:
        1. Log coverage gaps (forensic timeline incomplete)
        2. PowerShell .NET object corruption (unexpanded objects)

        Logs warnings but does not fail import - allows analyst to decide.
        """
        try:
            # 1. Update log coverage summary
            coverage_result = update_log_coverage_summary(self._db.db_path)
            if coverage_result['gaps_detected'] > 0:
                logger.warning(
                    f"⚠️  FORENSIC COVERAGE GAPS DETECTED: {coverage_result['gaps_detected']} log types "
                    f"have insufficient coverage. Query log_coverage_summary for details."
                )
                for item in coverage_result['coverage_report']:
                    if item['gap_detected']:
                        logger.warning(f"    - {item['log_type']}: {item['gap_description']}")

            # 2. Check for PowerShell .NET object corruption
            ps_results = validate_all_tables(self._db.db_path)
            any_corrupted = False
            for table, ps_result in ps_results.items():
                if ps_result['corrupted']:
                    any_corrupted = True
                    logger.warning(
                        f"⚠️  POWERSHELL EXPORT CORRUPTION in {table}: "
                        f"Fields {ps_result['affected_fields']} contain .NET type names instead of values. "
                        f"Re-export with: | ConvertTo-Json -Depth 10"
                    )

            if any_corrupted:
                logger.warning(
                    "⚠️  CRITICAL: PowerShell export corruption detected. "
                    "Analysis may be unreliable. Request re-export from customer."
                )

        except Exception as e:
            # Log but don't fail import - validation is advisory
            logger.error(f"Post-import validation failed (non-fatal): {e}")

    def _import_from_directory(self, exports_dir: Path) -> Dict[str, ImportResult]:
        """
        Import from extracted directory with recursive subdirectory scanning.

        CRITICAL: Recursively scans all subdirectories to ensure no export
        folders are missed. This prevents data loss when multiple export
        folders exist (e.g., Fyna/, TenantWide_Investigation/).

        Results are merged - if multiple files of the same type exist,
        all are imported (deduplication handled by UNIQUE constraints).
        """
        results: Dict[str, ImportResult] = {}

        # Recursively find all CSV files in directory and subdirectories
        all_csv_files = list(exports_dir.rglob('*.csv'))

        # Log discovery for audit trail
        if all_csv_files:
            subdirs = set(f.parent.relative_to(exports_dir) for f in all_csv_files if f.parent != exports_dir)
            if subdirs:
                logger.info(f"Found CSV files in {len(subdirs) + 1} directories: {exports_dir}, {subdirs}")

        for file in all_csv_files:
            # Skip macOS metadata files
            if '__MACOSX' in str(file) or file.name.startswith('.'):
                continue

            for log_type, pattern in LOG_FILE_PATTERNS.items():
                if re.match(pattern, file.name):
                    try:
                        result_key = None
                        import_result = None

                        if log_type == LogType.SIGNIN:
                            result_key = 'sign_in'
                            import_result = self.import_sign_in_logs(file)
                        elif log_type == LogType.FULL_AUDIT:
                            result_key = 'ual'
                            import_result = self.import_ual(file)
                        elif log_type == LogType.ENTRA_AUDIT:
                            result_key = 'entra_audit'
                            import_result = self.import_entra_audit(file)
                        elif log_type == LogType.AUDIT:
                            # Deprecated: AUDIT now mapped to ENTRA_AUDIT
                            result_key = 'entra_audit'
                            import_result = self.import_entra_audit(file)
                        elif log_type == LogType.MAILBOX_AUDIT:
                            result_key = 'mailbox'
                            import_result = self.import_mailbox_audit(file)
                        elif log_type == LogType.OAUTH_CONSENTS:
                            result_key = 'oauth'
                            import_result = self.import_oauth_consents(file)
                        elif log_type == LogType.INBOX_RULES:
                            result_key = 'inbox_rules'
                            import_result = self.import_inbox_rules(file)
                        elif log_type == LogType.LEGACY_AUTH:
                            result_key = 'legacy_auth'
                            import_result = self.import_legacy_auth(file)
                        elif log_type == LogType.PASSWORD_CHANGED:
                            result_key = 'password_status'
                            import_result = self.import_password_status(file)
                        elif log_type == LogType.MFA_CHANGES:
                            result_key = 'mfa_changes'
                            import_result = self.import_mfa_changes(file)
                        elif log_type == LogType.RISKY_USERS:
                            result_key = 'risky_users'
                            import_result = self.import_risky_users(file)
                        # Phase 249 unwired handlers - FIX-1
                        elif log_type == LogType.MAILBOX_DELEGATIONS:
                            result_key = 'mailbox_delegations'
                            import_result = self.import_mailbox_delegations(file)
                        elif log_type == LogType.SERVICE_PRINCIPALS:
                            result_key = 'service_principals'
                            import_result = self.import_service_principals(file)
                        elif log_type == LogType.ADMIN_ROLE_ASSIGNMENTS:
                            result_key = 'admin_role_assignments'
                            import_result = self.import_admin_role_assignments(file)
                        elif log_type == LogType.APPLICATION_REGISTRATIONS:
                            result_key = 'application_registrations'
                            import_result = self.import_application_registrations(file)
                        elif log_type == LogType.TRANSPORT_RULES:
                            result_key = 'transport_rules'
                            import_result = self.import_transport_rules(file)
                        elif log_type == LogType.CONDITIONAL_ACCESS_POLICIES:
                            result_key = 'conditional_access_policies'
                            import_result = self.import_conditional_access_policies(file)
                        elif log_type == LogType.NAMED_LOCATIONS:
                            result_key = 'named_locations'
                            import_result = self.import_named_locations(file)
                        elif log_type == LogType.EVIDENCE_MANIFEST:
                            result_key = 'evidence_manifest'
                            import_result = self.import_evidence_manifest(file)

                        # WARNING: File matched pattern but no handler exists (Phase 231)
                        if result_key is None and import_result is None:
                            logger.warning(
                                f"File {file.name} matched pattern for {log_type} but no import handler exists. "
                                f"File will be SKIPPED. This may indicate missing forensic data."
                            )

                        # Merge results if multiple files of same type
                        if result_key and import_result:
                            if result_key in results:
                                # Merge: accumulate counts from multiple files
                                existing = results[result_key]
                                results[result_key] = ImportResult(
                                    source_file=f"{existing.source_file}; {import_result.source_file}",
                                    source_hash=f"{existing.source_hash}; {import_result.source_hash}",
                                    records_imported=existing.records_imported + import_result.records_imported,
                                    records_failed=existing.records_failed + import_result.records_failed,
                                    errors=existing.errors + import_result.errors,
                                    duration_seconds=existing.duration_seconds + import_result.duration_seconds,
                                    records_skipped=existing.records_skipped + import_result.records_skipped
                                )
                                logger.info(f"Merged {result_key} from {file}: +{import_result.records_imported} records")
                            else:
                                results[result_key] = import_result

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
                            elif log_type == LogType.FULL_AUDIT:
                                results['ual'] = self._import_ual_from_bytes(
                                    content, source_id, source_hash
                                )
                            elif log_type == LogType.ENTRA_AUDIT:
                                results['entra_audit'] = self._import_entra_audit_from_bytes(
                                    content, source_id, source_hash
                                )
                            elif log_type == LogType.AUDIT:
                                # Deprecated: AUDIT now mapped to ENTRA_AUDIT
                                results['entra_audit'] = self._import_entra_audit_from_bytes(
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
                            elif log_type == LogType.LEGACY_AUTH:
                                results['legacy_auth'] = self._import_legacy_auth_from_bytes(
                                    content, source_id, source_hash
                                )
                            elif log_type == LogType.PASSWORD_CHANGED:
                                results['password_status'] = self._import_password_status_from_bytes(
                                    content, source_id, source_hash
                                )
                            elif log_type == LogType.MFA_CHANGES:
                                results['mfa_changes'] = self._import_mfa_changes_from_bytes(
                                    content, source_id, source_hash
                                )
                            elif log_type == LogType.RISKY_USERS:
                                results['risky_users'] = self._import_risky_users_from_bytes(
                                    content, source_id, source_hash
                                )
                            # Phase 249 unwired handlers - FIX-1
                            # These use temp file extraction since _from_bytes helpers don't exist yet
                            elif log_type in [
                                LogType.MAILBOX_DELEGATIONS, LogType.SERVICE_PRINCIPALS,
                                LogType.ADMIN_ROLE_ASSIGNMENTS, LogType.APPLICATION_REGISTRATIONS,
                                LogType.TRANSPORT_RULES, LogType.CONDITIONAL_ACCESS_POLICIES,
                                LogType.NAMED_LOCATIONS, LogType.EVIDENCE_MANIFEST
                            ]:
                                # Extract to temp file and import
                                import tempfile
                                with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.csv') as tmp:
                                    tmp.write(content)
                                    tmp_path = tmp.name
                                try:
                                    # Map log type to result key and method
                                    handlers = {
                                        LogType.MAILBOX_DELEGATIONS: ('mailbox_delegations', self.import_mailbox_delegations),
                                        LogType.SERVICE_PRINCIPALS: ('service_principals', self.import_service_principals),
                                        LogType.ADMIN_ROLE_ASSIGNMENTS: ('admin_role_assignments', self.import_admin_role_assignments),
                                        LogType.APPLICATION_REGISTRATIONS: ('application_registrations', self.import_application_registrations),
                                        LogType.TRANSPORT_RULES: ('transport_rules', self.import_transport_rules),
                                        LogType.CONDITIONAL_ACCESS_POLICIES: ('conditional_access_policies', self.import_conditional_access_policies),
                                        LogType.NAMED_LOCATIONS: ('named_locations', self.import_named_locations),
                                        LogType.EVIDENCE_MANIFEST: ('evidence_manifest', self.import_evidence_manifest),
                                    }
                                    result_key, handler = handlers[log_type]
                                    results[result_key] = handler(tmp_path)
                                    # Update source_file and source_hash to reflect zip origin
                                    results[result_key].source_file = source_id
                                    results[result_key].source_hash = source_hash
                                finally:
                                    import os
                                    os.unlink(tmp_path)
                            else:
                                # WARNING: Pattern matched but no handler (Phase 231)
                                logger.warning(
                                    f"File {filename} in zip matched pattern for {log_type} "
                                    f"but no import handler exists. File will be SKIPPED."
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
                        compress_json(row),
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

            # Phase 1.2: Run quality checks for zip imports (BUG FIX)
            # PIR-OCULUS-2025-12-19: Zip imports were NOT running quality checks
            if records_imported > 0:
                try:
                    from .data_quality_checker import check_table_quality

                    quality_report = check_table_quality(
                        str(self._db.db_path),
                        'sign_in_logs',
                        conn=conn  # Pass existing connection to see uncommitted data
                    )

                    # Check if quality_check_summary table exists
                    cursor.execute("""
                        SELECT name FROM sqlite_master
                        WHERE type='table' AND name='quality_check_summary'
                    """)

                    if cursor.fetchone():
                        # Store quality check results
                        cursor.execute("""
                            INSERT INTO quality_check_summary
                            (table_name, overall_quality_score, reliable_fields_count,
                             unreliable_fields_count, check_passed, warnings, recommendations, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            'sign_in_logs',
                            quality_report.overall_quality_score,
                            len(quality_report.reliable_fields),
                            len(quality_report.unreliable_fields),
                            1 if quality_report.overall_quality_score >= 0.5 else 0,
                            '; '.join(quality_report.warnings) if quality_report.warnings else None,
                            '; '.join(quality_report.recommendations) if quality_report.recommendations else None,
                            quality_report.created_at
                        ))

                    # Fail-fast: Raise error if quality score below threshold
                    if quality_report.overall_quality_score < 0.5:
                        error_msg = (
                            f"Data quality check FAILED: Quality score {quality_report.overall_quality_score:.2f} "
                            f"is below threshold (0.5). Import aborted.\n\n"
                            f"Unreliable fields ({len(quality_report.unreliable_fields)}): "
                            f"{', '.join(quality_report.unreliable_fields)}\n\n"
                        )
                        if quality_report.recommendations:
                            error_msg += "Recommendations:\n"
                            for rec in quality_report.recommendations:
                                error_msg += f"  - {rec}\n"

                        raise DataQualityError(
                            error_msg,
                            quality_score=quality_report.overall_quality_score,
                            unreliable_fields=quality_report.unreliable_fields,
                            recommendations=quality_report.recommendations
                        )

                    # Log quality warnings (even if check passed)
                    if quality_report.warnings:
                        print(f"\n⚠️  Data quality warnings:")
                        for warning in quality_report.warnings:
                            print(f"   - {warning}")

                    logger.info(
                        f"Quality check passed: Score {quality_report.overall_quality_score:.2f}, "
                        f"{len(quality_report.reliable_fields)} reliable fields, "
                        f"{len(quality_report.unreliable_fields)} unreliable fields"
                    )

                except DataQualityError:
                    # Re-raise quality errors (will be caught by outer except and rolled back)
                    raise
                except Exception as e:
                    # Quality check failed but don't block import
                    logger.warning(f"Quality check failed (non-fatal): {e}")

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
                        compress_json(audit_data),
                        compress_json(row),
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
                        compress_json(row),
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
                        compress_json(row),
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
                        compress_json(row),
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

    def _import_legacy_auth_from_bytes(
        self, content: bytes, source_id: str, source_hash: str
    ) -> ImportResult:
        """
        Import legacy auth logs from bytes content.

        Delegates to _import_legacy_auth_internal after decoding bytes to CSV reader.
        """
        start_time = time.time()

        if self._is_already_imported(source_hash, 'legacy_auth'):
            return ImportResult(
                source_file=source_id,
                source_hash=source_hash,
                records_imported=0,
                records_failed=0,
                errors=[],
                duration_seconds=time.time() - start_time
            )

        text_content = content.decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(text_content))
        return self._import_legacy_auth_internal(reader, source_id, source_hash, start_time)

    def _import_password_status_from_bytes(
        self, content: bytes, source_id: str, source_hash: str
    ) -> ImportResult:
        """
        Import password status from bytes content.

        Delegates to _import_password_status_internal after decoding bytes to CSV reader.
        """
        start_time = time.time()
        text_content = content.decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(text_content))
        return self._import_password_status_internal(reader, source_id, source_hash, start_time)

    def _import_mfa_changes_from_bytes(
        self, content: bytes, source_id: str, source_hash: str
    ) -> ImportResult:
        """
        Import MFA changes from bytes content.

        Delegates to _import_mfa_changes_internal after decoding bytes to CSV reader.
        """
        start_time = time.time()
        text_content = content.decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(text_content))
        return self._import_mfa_changes_internal(reader, source_id, source_hash, start_time)

    def _import_risky_users_from_bytes(
        self, content: bytes, source_id: str, source_hash: str
    ) -> ImportResult:
        """
        Import risky users from bytes content.

        Delegates to _import_risky_users_internal after decoding bytes to CSV reader.
        """
        start_time = time.time()
        text_content = content.decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(text_content))
        return self._import_risky_users_internal(reader, source_id, source_hash, start_time)

    def import_entra_audit(self, source: Union[str, Path]) -> ImportResult:
        """
        Import Entra ID (Azure AD) audit logs from CSV.

        Parses directory-level audit events: password changes, role assignments,
        app consents, conditional access changes, etc.
        Uses Australian date format (DD/MM/YYYY H:MM:SS AM/PM).

        Args:
            source: Path to Entra audit CSV file

        Returns:
            ImportResult with import statistics
        """
        source = Path(source)
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source}")

        start_time = time.time()
        source_hash = self._calculate_hash(source)

        # Check if already imported
        if self._is_already_imported(source_hash, 'entra_audit'):
            return ImportResult(
                source_file=str(source),
                source_hash=source_hash,
                records_imported=0,
                records_failed=0,
                errors=[],
                duration_seconds=time.time() - start_time
            )

        with open(source, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            return self._import_entra_audit_internal(
                reader, str(source), source_hash, start_time
            )

    def _import_entra_audit_internal(
        self,
        reader: csv.DictReader,
        source_id: str,
        source_hash: str,
        start_time: float
    ) -> ImportResult:
        """
        Internal method to import Entra audit logs from a CSV reader.

        Args:
            reader: CSV DictReader (from file or StringIO)
            source_id: Source identifier for tracking
            source_hash: SHA256 hash of source
            start_time: Import start time for duration calculation

        Returns:
            ImportResult with import statistics
        """
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
        """, (source_id, source_hash, 'entra_audit', now, PARSER_VERSION))
        import_id = cursor.lastrowid

        try:
            for row_num, row in enumerate(reader, start=2):
                try:
                    # Parse datetime with AU format
                    timestamp = parse_m365_datetime(
                        row.get('ActivityDateTime', ''),
                        self._detect_date_format(row.get('ActivityDateTime', ''))
                    )

                    # INSERT OR IGNORE for deduplication via UNIQUE constraint
                    cursor.execute("""
                        INSERT OR IGNORE INTO entra_audit_log
                        (timestamp, activity, initiated_by, target, result,
                         result_reason, raw_record, imported_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        timestamp.isoformat(),
                        row.get('ActivityDisplayName', ''),
                        row.get('InitiatedBy', ''),
                        row.get('Target', ''),
                        row.get('Result', ''),
                        row.get('ResultReason', ''),
                        compress_json(row),
                        now
                    ))
                    if cursor.rowcount > 0:
                        records_imported += 1
                    else:
                        records_skipped += 1

                except Exception as e:
                    records_failed += 1
                    errors.append(f"Row {row_num}: {str(e)}")
                    logger.debug(f"Failed to import Entra audit row {row_num}: {e}")

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
            source_file=source_id,
            source_hash=source_hash,
            records_imported=records_imported,
            records_failed=records_failed,
            errors=errors,
            duration_seconds=time.time() - start_time,
            records_skipped=records_skipped
        )

    def import_transport_rules(self, source: Union[str, Path]) -> ImportResult:
        """
        Import Exchange Transport Rules from CSV.

        CRITICAL for exfiltration detection - org-wide mail flow rules.
        MITRE ATT&CK: T1114.003 (Email Collection: Email Forwarding Rule)

        Maps columns:
        - Name → name (rule identifier)
        - State → state (Enabled/Disabled)
        - Priority → priority
        - Mode → mode (Enforce/Audit)
        - BlindCopyTo → blind_copy_to (EXFILTRATION IOC)
        - CopyTo → copy_to (EXFILTRATION IOC)
        - RedirectMessageTo → redirect_message_to (EXFILTRATION IOC)
        - DeleteMessage → delete_message (Evidence destruction)
        - SetSCL → set_scl (-1 = whitelist/spam bypass)
        - WhenChanged → when_changed

        Note: This is a point-in-time config snapshot, not time-series events.

        Args:
            source: Path to TransportRules CSV file

        Returns:
            ImportResult with import statistics
        """
        source = Path(source)
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source}")

        start_time = time.time()
        source_hash = self._calculate_hash(source)

        # Check if already imported
        if self._is_already_imported(source_hash, 'transport_rules'):
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
        """, (str(source), source_hash, 'transport_rules', now, PARSER_VERSION))
        import_id = cursor.lastrowid

        try:
            with open(source, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row_num, row in enumerate(reader, start=2):
                    try:
                        # Parse priority
                        priority_str = row.get('Priority', '0')
                        priority = int(priority_str) if priority_str else 0

                        # Parse SetSCL (-1 = whitelist)
                        scl_str = row.get('SetSCL', '')
                        set_scl = int(scl_str) if scl_str and scl_str != '' else None

                        # Parse DeleteMessage boolean
                        delete_str = row.get('DeleteMessage', 'False')
                        delete_message = 1 if delete_str.lower() == 'true' else 0

                        # Parse WhenChanged datetime
                        when_changed = row.get('WhenChanged', '')

                        # INSERT OR REPLACE for deduplication via UNIQUE constraint on name
                        cursor.execute("""
                            INSERT OR REPLACE INTO transport_rules
                            (name, state, priority, mode, from_scope, sent_to_scope,
                             blind_copy_to, copy_to, redirect_message_to, delete_message,
                             modify_subject, set_scl, conditions, exceptions, when_changed,
                             comments, raw_record, imported_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            row.get('Name', ''),
                            row.get('State', ''),
                            priority,
                            row.get('Mode', ''),
                            row.get('FromScope', ''),
                            row.get('SentToScope', ''),
                            row.get('BlindCopyTo', ''),
                            row.get('CopyTo', ''),
                            row.get('RedirectMessageTo', ''),
                            delete_message,
                            row.get('ModifySubject', ''),
                            set_scl,
                            row.get('Conditions', ''),
                            row.get('Exceptions', ''),
                            when_changed,
                            row.get('Comments', ''),
                            compress_json(row),
                            now
                        ))
                        if cursor.rowcount > 0:
                            records_imported += 1
                        else:
                            records_skipped += 1

                    except Exception as e:
                        records_failed += 1
                        errors.append(f"Row {row_num}: {str(e)}")
                        logger.debug(f"Failed to import transport rule row {row_num}: {e}")

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

    def import_evidence_manifest(self, source: Union[str, Path]) -> ImportResult:
        """
        Import Evidence Manifest JSON file.

        Contains chain of custody metadata and SHA256 hashes for all evidence files.
        Note: File is typically UTF-16 LE encoded with BOM.

        Args:
            source: Path to _EVIDENCE_MANIFEST.json

        Returns:
            ImportResult with import statistics
        """
        source = Path(source)
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source}")

        start_time = time.time()
        source_hash = self._calculate_hash(source)

        # Check if already imported
        if self._is_already_imported(source_hash, 'evidence_manifest'):
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
        """, (str(source), source_hash, 'evidence_manifest', now, PARSER_VERSION))
        import_id = cursor.lastrowid

        try:
            # Parse manifest using M365LogParser
            parser = M365LogParser(date_format=self._date_format)
            manifest = parser.parse_evidence_manifest(source)

            # Extract case_id from database path
            case_id = _extract_case_id_from_db_path(self._db.db_path) if self._db.db_path else None

            # INSERT OR REPLACE for deduplication via UNIQUE constraint on investigation_id
            cursor.execute("""
                INSERT OR REPLACE INTO evidence_manifest
                (case_id, investigation_id, collection_version, collected_at,
                 collected_by, collected_on, date_range_start, date_range_end,
                 days_back, files_manifest, raw_json, imported_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                case_id,
                manifest.investigation_id,
                manifest.collection_version,
                manifest.collected_at,
                manifest.collected_by,
                manifest.collected_on,
                manifest.date_range_start,
                manifest.date_range_end,
                manifest.days_back,
                json.dumps(manifest.files),
                compress_json({'raw': manifest.raw_json}),
                now
            ))
            if cursor.rowcount > 0:
                records_imported = 1

            # Update import metadata
            cursor.execute("""
                UPDATE import_metadata
                SET records_imported = ?, records_failed = ?, import_completed = ?
                WHERE id = ?
            """, (records_imported, records_failed, datetime.now().isoformat(), import_id))

            conn.commit()

        except Exception as e:
            records_failed = 1
            errors.append(str(e))
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
            duration_seconds=time.time() - start_time
        )

    def import_mailbox_delegations(self, source: Union[str, Path]) -> ImportResult:
        """
        Import Mailbox Delegations CSV file.

        MITRE ATT&CK: T1098.002 (Account Manipulation: Exchange Email Delegate)

        Args:
            source: Path to MailboxDelegations CSV

        Returns:
            ImportResult with import statistics
        """
        source = Path(source)
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source}")

        start_time = time.time()
        source_hash = self._calculate_hash(source)

        if self._is_already_imported(source_hash, 'mailbox_delegations'):
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

        cursor.execute("""
            INSERT INTO import_metadata
            (source_file, source_hash, log_type, records_imported, records_failed,
             import_started, parser_version)
            VALUES (?, ?, ?, 0, 0, ?, ?)
        """, (str(source), source_hash, 'mailbox_delegations', now, PARSER_VERSION))
        import_id = cursor.lastrowid

        try:
            with open(source, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row_num, row in enumerate(reader, start=2):
                    try:
                        is_inherited = 1 if row.get('IsInherited', 'False').lower() == 'true' else 0

                        cursor.execute("""
                            INSERT OR IGNORE INTO mailbox_delegations
                            (mailbox, permission_type, delegate, access_rights,
                             is_inherited, raw_record, imported_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            row.get('Mailbox', ''),
                            row.get('PermissionType', ''),
                            row.get('Delegate', ''),
                            row.get('AccessRights', ''),
                            is_inherited,
                            compress_json(row),
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
            source_file=str(source),
            source_hash=source_hash,
            records_imported=records_imported,
            records_failed=records_failed,
            errors=errors,
            duration_seconds=time.time() - start_time,
            records_skipped=records_skipped
        )

    def import_admin_role_assignments(self, source: Union[str, Path]) -> ImportResult:
        """
        Import Admin Role Assignments CSV file.

        MITRE ATT&CK: T1078.004 (Valid Accounts: Cloud), T1098 (Account Manipulation)

        Args:
            source: Path to AdminRoleAssignments CSV

        Returns:
            ImportResult with import statistics
        """
        source = Path(source)
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source}")

        start_time = time.time()
        source_hash = self._calculate_hash(source)

        if self._is_already_imported(source_hash, 'admin_role_assignments'):
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

        cursor.execute("""
            INSERT INTO import_metadata
            (source_file, source_hash, log_type, records_imported, records_failed,
             import_started, parser_version)
            VALUES (?, ?, ?, 0, 0, ?, ?)
        """, (str(source), source_hash, 'admin_role_assignments', now, PARSER_VERSION))
        import_id = cursor.lastrowid

        try:
            with open(source, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row_num, row in enumerate(reader, start=2):
                    try:
                        cursor.execute("""
                            INSERT OR IGNORE INTO admin_role_assignments
                            (role_name, role_id, role_description, member_display_name,
                             member_upn, member_id, member_type, raw_record, imported_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            row.get('RoleName', ''),
                            row.get('RoleId', ''),
                            row.get('RoleDescription', ''),
                            row.get('MemberDisplayName', ''),
                            row.get('MemberUPN', ''),
                            row.get('MemberId', ''),
                            row.get('MemberType', ''),
                            compress_json(row),
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
            source_file=str(source),
            source_hash=source_hash,
            records_imported=records_imported,
            records_failed=records_failed,
            errors=errors,
            duration_seconds=time.time() - start_time,
            records_skipped=records_skipped
        )

    def import_conditional_access_policies(self, source: Union[str, Path]) -> ImportResult:
        """
        Import Conditional Access Policies CSV.

        MITRE ATT&CK: T1562.001 (Impair Defenses: Disable or Modify Tools)
        """
        start_time = time.time()
        source = Path(source)

        with open(source, 'rb') as f:
            source_hash = hashlib.sha256(f.read()).hexdigest()

        if self._is_already_imported(source_hash, 'conditional_access_policies'):
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
        errors = []
        now = datetime.now().isoformat()

        conn = self._db.connect()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO import_metadata
            (source_file, source_hash, log_type, records_imported, records_failed, import_started, parser_version)
            VALUES (?, ?, ?, 0, 0, ?, ?)
        """, (str(source), source_hash, 'conditional_access_policies', now, PARSER_VERSION))
        import_id = cursor.lastrowid

        try:
            parser = M365LogParser(date_format='AU')
            entries = parser.parse_conditional_access_policies(source)

            for entry in entries:
                try:
                    created_dt = entry.created_datetime.isoformat() if entry.created_datetime else None
                    modified_dt = entry.modified_datetime.isoformat() if entry.modified_datetime else None

                    cursor.execute("""
                        INSERT OR IGNORE INTO conditional_access_policies
                        (display_name, policy_id, state, created_datetime, modified_datetime,
                         conditions, grant_controls, session_controls, raw_record, imported_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        entry.display_name,
                        entry.policy_id,
                        entry.state,
                        created_dt,
                        modified_dt,
                        entry.conditions,
                        entry.grant_controls,
                        entry.session_controls,
                        compress_json(json.loads(entry.raw_record)) if entry.raw_record else None,
                        now
                    ))
                    if cursor.rowcount > 0:
                        records_imported += 1
                    else:
                        records_skipped += 1

                except Exception as e:
                    records_failed += 1
                    errors.append(f"Policy {entry.display_name}: {str(e)}")

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

    def import_named_locations(self, source: Union[str, Path]) -> ImportResult:
        """Import Named Locations CSV."""
        start_time = time.time()
        source = Path(source)

        with open(source, 'rb') as f:
            source_hash = hashlib.sha256(f.read()).hexdigest()

        if self._is_already_imported(source_hash, 'named_locations'):
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
        errors = []
        now = datetime.now().isoformat()

        conn = self._db.connect()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO import_metadata
            (source_file, source_hash, log_type, records_imported, records_failed, import_started, parser_version)
            VALUES (?, ?, ?, 0, 0, ?, ?)
        """, (str(source), source_hash, 'named_locations', now, PARSER_VERSION))
        import_id = cursor.lastrowid

        try:
            parser = M365LogParser(date_format='AU')
            entries = parser.parse_named_locations(source)

            for entry in entries:
                try:
                    created_dt = entry.created_datetime.isoformat() if entry.created_datetime else None
                    modified_dt = entry.modified_datetime.isoformat() if entry.modified_datetime else None

                    cursor.execute("""
                        INSERT OR IGNORE INTO named_locations
                        (display_name, location_id, created_datetime, modified_datetime,
                         location_type, is_trusted, ip_ranges, countries_and_regions, raw_record, imported_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        entry.display_name,
                        entry.location_id,
                        created_dt,
                        modified_dt,
                        entry.location_type,
                        1 if entry.is_trusted else 0,
                        entry.ip_ranges,
                        entry.countries_and_regions,
                        compress_json(json.loads(entry.raw_record)) if entry.raw_record else None,
                        now
                    ))
                    if cursor.rowcount > 0:
                        records_imported += 1
                    else:
                        records_skipped += 1

                except Exception as e:
                    records_failed += 1
                    errors.append(f"Location {entry.display_name}: {str(e)}")

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

    def import_application_registrations(self, source: Union[str, Path]) -> ImportResult:
        """
        Import Application Registrations CSV.

        MITRE ATT&CK: T1098.001 (Account Manipulation: Additional Cloud Credentials)
        """
        start_time = time.time()
        source = Path(source)

        with open(source, 'rb') as f:
            source_hash = hashlib.sha256(f.read()).hexdigest()

        if self._is_already_imported(source_hash, 'application_registrations'):
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
        errors = []
        now = datetime.now().isoformat()

        conn = self._db.connect()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO import_metadata
            (source_file, source_hash, log_type, records_imported, records_failed, import_started, parser_version)
            VALUES (?, ?, ?, 0, 0, ?, ?)
        """, (str(source), source_hash, 'application_registrations', now, PARSER_VERSION))
        import_id = cursor.lastrowid

        try:
            parser = M365LogParser(date_format='AU')
            entries = parser.parse_application_registrations(source)

            for entry in entries:
                try:
                    created_dt = entry.created_datetime.isoformat() if entry.created_datetime else None

                    cursor.execute("""
                        INSERT OR IGNORE INTO application_registrations
                        (display_name, app_id, object_id, created_datetime, sign_in_audience,
                         publisher_domain, required_resource_access, password_credentials,
                         key_credentials, web_redirect_uris, raw_record, imported_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        entry.display_name,
                        entry.app_id,
                        entry.object_id,
                        created_dt,
                        entry.sign_in_audience,
                        entry.publisher_domain,
                        entry.required_resource_access,
                        entry.password_credentials,
                        entry.key_credentials,
                        entry.web_redirect_uris,
                        compress_json(json.loads(entry.raw_record)) if entry.raw_record else None,
                        now
                    ))
                    if cursor.rowcount > 0:
                        records_imported += 1
                    else:
                        records_skipped += 1

                except Exception as e:
                    records_failed += 1
                    errors.append(f"App {entry.display_name}: {str(e)}")

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

    def import_service_principals(self, source: Union[str, Path]) -> ImportResult:
        """Import Service Principals CSV."""
        start_time = time.time()
        source = Path(source)

        with open(source, 'rb') as f:
            source_hash = hashlib.sha256(f.read()).hexdigest()

        if self._is_already_imported(source_hash, 'service_principals'):
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
        errors = []
        now = datetime.now().isoformat()

        conn = self._db.connect()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO import_metadata
            (source_file, source_hash, log_type, records_imported, records_failed, import_started, parser_version)
            VALUES (?, ?, ?, 0, 0, ?, ?)
        """, (str(source), source_hash, 'service_principals', now, PARSER_VERSION))
        import_id = cursor.lastrowid

        try:
            parser = M365LogParser(date_format='AU')
            entries = parser.parse_service_principals(source)

            for entry in entries:
                try:
                    created_dt = entry.created_datetime.isoformat() if entry.created_datetime else None

                    cursor.execute("""
                        INSERT OR IGNORE INTO service_principals
                        (display_name, app_id, object_id, service_principal_type, account_enabled,
                         created_datetime, app_owner_organization_id, reply_urls, tags, raw_record, imported_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        entry.display_name,
                        entry.app_id,
                        entry.object_id,
                        entry.service_principal_type,
                        1 if entry.account_enabled else 0,
                        created_dt,
                        entry.app_owner_organization_id,
                        entry.reply_urls,
                        entry.tags,
                        compress_json(json.loads(entry.raw_record)) if entry.raw_record else None,
                        now
                    ))
                    if cursor.rowcount > 0:
                        records_imported += 1
                    else:
                        records_skipped += 1

                except Exception as e:
                    records_failed += 1
                    errors.append(f"SP {entry.display_name}: {str(e)}")

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

    def _import_entra_audit_from_bytes(
        self, content: bytes, source_id: str, source_hash: str
    ) -> ImportResult:
        """
        Import Entra audit logs from bytes content.

        Delegates to _import_entra_audit_internal after decoding bytes to CSV reader.
        """
        start_time = time.time()

        if self._is_already_imported(source_hash, 'entra_audit'):
            return ImportResult(
                source_file=source_id,
                source_hash=source_hash,
                records_imported=0,
                records_failed=0,
                errors=[],
                duration_seconds=time.time() - start_time
            )

        text_content = content.decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(text_content))
        return self._import_entra_audit_internal(reader, source_id, source_hash, start_time)

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
