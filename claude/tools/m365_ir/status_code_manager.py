"""
Status Code Manager - Phase 1.3

This module manages status code lookups for M365 IR log analysis.

Features:
    - Fast lookup of known status codes (indexed)
    - Automatic unknown code detection
    - Batch lookup for performance
    - Track deprecated codes
    - Support for multiple log types (sign_in_logs, unified_audit_log, etc.)

Usage:
    >>> from claude.tools.m365_ir.status_code_manager import StatusCodeManager
    >>> manager = StatusCodeManager('case.db')
    >>> result = manager.lookup_status_code('sign_in_logs', 'status_error_code', '0')
    >>> print(result.meaning)
    'Success - No error'

Phase: PHASE_1_FOUNDATION (Phase 1.3 - Status Code Lookup Tables)
"""

import sqlite3
import logging
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class StatusCodeInfo:
    """
    Information about a status code.

    Attributes:
        code_value: The status code value (e.g., '0', '50126', 'success')
        meaning: Human-readable explanation
        severity: INFO, WARNING, or CRITICAL
        is_known: True if code exists in reference table
        deprecated: True if Microsoft deprecated this code
        log_type: Log type this code belongs to
        field_name: Field name this code belongs to
    """

    code_value: str
    meaning: str
    severity: str
    is_known: bool
    deprecated: bool = False
    log_type: str = ''
    field_name: str = ''


class StatusCodeManager:
    """
    Manages status code lookups and unknown code detection.

    This class provides fast, indexed lookups of status codes from the
    status_code_reference table and detects unknown codes for investigation.
    """

    def __init__(self, db_path: str):
        """
        Initialize StatusCodeManager.

        Args:
            db_path: Path to SQLite database containing status_code_reference table
        """
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")

    def lookup_status_code(
        self,
        log_type: str,
        field_name: str,
        code_value: str
    ) -> StatusCodeInfo:
        """
        Look up a single status code.

        Args:
            log_type: Log type (e.g., 'sign_in_logs', 'unified_audit_log')
            field_name: Field name (e.g., 'status_error_code', 'conditional_access_status')
            code_value: Code value to look up (e.g., '0', '50126', 'success')

        Returns:
            StatusCodeInfo with meaning and severity, or UNKNOWN if not found

        Example:
            >>> manager = StatusCodeManager('case.db')
            >>> result = manager.lookup_status_code('sign_in_logs', 'status_error_code', '0')
            >>> print(f"{result.meaning} ({result.severity})")
            'Success - No error (INFO)'
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT meaning, severity, deprecated
                FROM status_code_reference
                WHERE log_type = ? AND field_name = ? AND code_value = ?
            """, (log_type, field_name, code_value))

            row = cursor.fetchone()

            if row:
                meaning, severity, deprecated = row
                return StatusCodeInfo(
                    code_value=code_value,
                    meaning=meaning,
                    severity=severity,
                    is_known=True,
                    deprecated=bool(deprecated),
                    log_type=log_type,
                    field_name=field_name
                )
            else:
                # Unknown code
                logger.warning(
                    f"Unknown status code: {log_type}.{field_name}='{code_value}'"
                )
                return StatusCodeInfo(
                    code_value=code_value,
                    meaning='UNKNOWN',
                    severity='WARNING',
                    is_known=False,
                    deprecated=False,
                    log_type=log_type,
                    field_name=field_name
                )

        finally:
            conn.close()

    def lookup_batch(
        self,
        log_type: str,
        field_name: str,
        code_values: List[str]
    ) -> Dict[str, StatusCodeInfo]:
        """
        Look up multiple status codes in a single database query.

        This is significantly faster than individual lookups when processing
        large datasets.

        Args:
            log_type: Log type
            field_name: Field name
            code_values: List of code values to look up

        Returns:
            Dictionary mapping code_value to StatusCodeInfo

        Example:
            >>> manager = StatusCodeManager('case.db')
            >>> results = manager.lookup_batch('sign_in_logs', 'status_error_code',
            ...                                 ['0', '50126', '50053'])
            >>> for code, info in results.items():
            ...     print(f"{code}: {info.meaning}")
        """
        if not code_values:
            return {}

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Use parameterized query with IN clause
            placeholders = ','.join('?' * len(code_values))
            query = f"""
                SELECT code_value, meaning, severity, deprecated
                FROM status_code_reference
                WHERE log_type = ? AND field_name = ? AND code_value IN ({placeholders})
            """
            params = [log_type, field_name] + code_values

            cursor.execute(query, params)
            rows = cursor.fetchall()

            # Build lookup dict from results
            known_codes = {}
            for code_value, meaning, severity, deprecated in rows:
                known_codes[code_value] = StatusCodeInfo(
                    code_value=code_value,
                    meaning=meaning,
                    severity=severity,
                    is_known=True,
                    deprecated=bool(deprecated),
                    log_type=log_type,
                    field_name=field_name
                )

            # Add UNKNOWN entries for codes not found
            result = {}
            for code_value in code_values:
                if code_value in known_codes:
                    result[code_value] = known_codes[code_value]
                else:
                    logger.warning(
                        f"Unknown status code: {log_type}.{field_name}='{code_value}'"
                    )
                    result[code_value] = StatusCodeInfo(
                        code_value=code_value,
                        meaning='UNKNOWN',
                        severity='WARNING',
                        is_known=False,
                        deprecated=False,
                        log_type=log_type,
                        field_name=field_name
                    )

            return result

        finally:
            conn.close()

    def scan_for_unknown_codes(
        self,
        log_type: str,
        field_name: str,
        table_name: Optional[str] = None
    ) -> List[Dict]:
        """
        Scan a log table for unknown status codes.

        This identifies codes that exist in the data but are not in the
        status_code_reference table, which may indicate:
        - New Microsoft API codes (need documentation update)
        - Data quality issues (invalid codes)
        - Schema changes requiring investigation

        Args:
            log_type: Log type to scan
            field_name: Field to scan for unknown codes
            table_name: Optional table name (defaults to log_type)

        Returns:
            List of dicts with unknown code information:
            [
                {
                    'code_value': '99999',
                    'count': 42,
                    'field_name': 'status_error_code',
                    'log_type': 'sign_in_logs'
                }
            ]

        Example:
            >>> manager = StatusCodeManager('case.db')
            >>> unknown = manager.scan_for_unknown_codes('sign_in_logs', 'status_error_code')
            >>> for item in unknown:
            ...     print(f"Unknown code '{item['code_value']}' appears {item['count']} times")
        """
        if table_name is None:
            table_name = log_type

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Get all distinct codes from the log table
            cursor.execute(f"""
                SELECT DISTINCT {field_name}, COUNT(*) as count
                FROM {table_name}
                WHERE {field_name} IS NOT NULL AND {field_name} != ''
                GROUP BY {field_name}
            """)

            log_codes = cursor.fetchall()

            # Get all known codes from reference table
            cursor.execute("""
                SELECT code_value
                FROM status_code_reference
                WHERE log_type = ? AND field_name = ?
            """, (log_type, field_name))

            # Convert known codes to strings for comparison (SQLite may return integers)
            known_codes = set(str(row[0]) for row in cursor.fetchall())

            # Find unknown codes
            unknown_codes = []
            for code_value, count in log_codes:
                # Convert code_value to string for comparison
                code_str = str(code_value)
                if code_str not in known_codes:
                    unknown_codes.append({
                        'code_value': code_str,
                        'count': count,
                        'field_name': field_name,
                        'log_type': log_type
                    })

            if unknown_codes:
                logger.warning(
                    f"Found {len(unknown_codes)} unknown code(s) in {table_name}.{field_name}"
                )

            return unknown_codes

        finally:
            conn.close()

    def add_status_code(
        self,
        log_type: str,
        field_name: str,
        code_value: str,
        meaning: str,
        severity: str,
        deprecated: bool = False
    ) -> None:
        """
        Add a new status code to the reference table.

        Use this to document newly discovered codes or update existing ones.

        Args:
            log_type: Log type
            field_name: Field name
            code_value: Code value
            meaning: Human-readable explanation
            severity: INFO, WARNING, or CRITICAL
            deprecated: Whether this code is deprecated by Microsoft

        Raises:
            ValueError: If severity is not INFO, WARNING, or CRITICAL
            sqlite3.IntegrityError: If code already exists (use update instead)

        Example:
            >>> manager = StatusCodeManager('case.db')
            >>> manager.add_status_code(
            ...     log_type='sign_in_logs',
            ...     field_name='status_error_code',
            ...     code_value='50126',
            ...     meaning='Invalid username or password',
            ...     severity='WARNING'
            ... )
        """
        # Validate severity
        valid_severities = ['INFO', 'WARNING', 'CRITICAL']
        if severity not in valid_severities:
            raise ValueError(
                f"Severity must be one of {valid_severities}, got '{severity}'"
            )

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            now = datetime.now().isoformat()

            cursor.execute("""
                INSERT INTO status_code_reference
                (log_type, field_name, code_value, meaning, severity,
                 first_seen, last_validated, deprecated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                log_type,
                field_name,
                code_value,
                meaning,
                severity,
                now,
                now,
                1 if deprecated else 0
            ))

            conn.commit()

            logger.info(
                f"Added status code: {log_type}.{field_name}='{code_value}' ({severity})"
            )

        finally:
            conn.close()

    def update_status_code(
        self,
        log_type: str,
        field_name: str,
        code_value: str,
        meaning: Optional[str] = None,
        severity: Optional[str] = None,
        deprecated: Optional[bool] = None
    ) -> None:
        """
        Update an existing status code in the reference table.

        Args:
            log_type: Log type
            field_name: Field name
            code_value: Code value
            meaning: Optional new meaning
            severity: Optional new severity
            deprecated: Optional new deprecated status

        Example:
            >>> manager = StatusCodeManager('case.db')
            >>> manager.update_status_code(
            ...     log_type='sign_in_logs',
            ...     field_name='status_error_code',
            ...     code_value='50001',
            ...     deprecated=True
            ... )
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            updates = []
            params = []

            if meaning is not None:
                updates.append('meaning = ?')
                params.append(meaning)

            if severity is not None:
                if severity not in ['INFO', 'WARNING', 'CRITICAL']:
                    raise ValueError(f"Invalid severity: {severity}")
                updates.append('severity = ?')
                params.append(severity)

            if deprecated is not None:
                updates.append('deprecated = ?')
                params.append(1 if deprecated else 0)

            if not updates:
                return  # Nothing to update

            # Always update last_validated
            updates.append('last_validated = ?')
            params.append(datetime.now().isoformat())

            # Add WHERE clause params
            params.extend([log_type, field_name, code_value])

            query = f"""
                UPDATE status_code_reference
                SET {', '.join(updates)}
                WHERE log_type = ? AND field_name = ? AND code_value = ?
            """

            cursor.execute(query, params)
            conn.commit()

            if cursor.rowcount > 0:
                logger.info(
                    f"Updated status code: {log_type}.{field_name}='{code_value}'"
                )
            else:
                logger.warning(
                    f"Status code not found for update: {log_type}.{field_name}='{code_value}'"
                )

        finally:
            conn.close()
