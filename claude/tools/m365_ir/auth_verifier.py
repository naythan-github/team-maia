#!/usr/bin/env python3
"""
Authentication Status Verifier - Phase 241

Prevents forensic analysis errors by automatically verifying authentication
success vs failure rates in M365 IR logs.

Background:
-----------
PIR-OCULUS-2025-12-19 error: Analyst claimed "37 SMTP authentication events
while disabled = bypass" when ALL 37 had status code 50126 (FAILED). The error
occurred because field name "Authenticated SMTP" was assumed to mean "successful
authentication" when it actually meant "SMTP authentication was attempted".

Solution:
---------
This module forces verification by:
1. Checking status field distribution
2. Calculating success vs failure rates
3. Generating warnings for suspicious patterns
4. Storing results for audit trail

Critical Rule:
--------------
PRIMARY EVIDENCE (status codes) > FIELD NAMES > DOCUMENTATION > ASSUMPTIONS

Author: Maia System (SRE Principal Engineer Agent)
Created: 2026-01-06
"""

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, NamedTuple, Optional

logger = logging.getLogger(__name__)

# Phase 2.1.4: Historical learning database
try:
    from claude.tools.core.paths import PathManager
    HISTORICAL_DB_PATH = PathManager.get_shared_db_path("m365_ir_field_reliability_history.db")
except ImportError:
    # Fallback if PathManager not available
    HISTORICAL_DB_PATH = Path.home() / ".maia" / "data" / "databases" / "system" / "m365_ir_field_reliability_history.db"

# Feature flag for Phase 2.1 integration
USE_PHASE_2_1_SCORING = True  # Set False to use Phase 1 legacy behavior


class VerificationResult(NamedTuple):
    """Result of authentication status verification.

    Attributes:
        log_type: Type of log verified ('legacy_auth', 'sign_in', etc.)
        total_events: Total authentication events in database
        successful: Count where status = '0' or 'Success'
        failed: Count where status != '0' and != 'Success'
        success_rate: Percentage (0.0 - 100.0)
        status_codes: Dict mapping status code to count
        warnings: List of warning messages for suspicious patterns
        verified_at: ISO timestamp when verification ran
    """
    log_type: str
    total_events: int
    successful: int
    failed: int
    success_rate: float
    status_codes: Dict[str, int]
    warnings: list[str]
    verified_at: str


# M365 Status Codes Reference
STATUS_CODE_DESCRIPTIONS = {
    '0': 'Success',
    'Success': 'Success',
    '50126': 'Invalid credentials (FAILED)',
    '50053': 'Malicious IP / Account locked (FAILED)',
    '50057': 'Account disabled (FAILED)',
    '50055': 'Expired password (FAILED)',
    '50074': 'Strong auth required (FAILED)',
    '50076': 'Application not found (FAILED)',
    '50079': 'User needs to enroll for MFA (FAILED)',
    '50158': 'External security challenge not satisfied (FAILED)',
}


def verify_auth_status(
    conn: sqlite3.Connection,
    log_type: str = 'legacy_auth'
) -> VerificationResult:
    """
    Verify authentication success vs failure rates for a log type.

    This function checks the status field to determine actual authentication
    outcomes, preventing errors like PIR-OCULUS-2025-12-19 where field names
    were misinterpreted as indicating success.

    Args:
        conn: Database connection with Row factory enabled
        log_type: Type of log to verify:
            - 'legacy_auth': Legacy authentication logs (SMTP, POP3, IMAP)
            - 'sign_in': Modern sign-in logs
            - 'unified_audit': Unified audit log (if has status field)

    Returns:
        VerificationResult with statistics and warnings

    Raises:
        ValueError: If log_type is unknown or table has no status field
        sqlite3.Error: If database query fails

    Example:
        >>> conn = db.connect()
        >>> result = verify_auth_status(conn, 'legacy_auth')
        >>> print(f"Success rate: {result.success_rate:.1f}%")
        >>> if result.warnings:
        ...     for warning in result.warnings:
        ...         print(warning)
    """
    # Map log types to database tables
    table_map = {
        'legacy_auth': 'legacy_auth_logs',
        'sign_in': 'sign_in_logs',
        'unified_audit': 'unified_audit_log'
    }

    if log_type not in table_map:
        raise ValueError(
            f"Unknown log_type: {log_type}. "
            f"Valid types: {', '.join(table_map.keys())}"
        )

    table = table_map[log_type]

    # Verify table exists
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,)
    )
    if not cursor.fetchone():
        raise ValueError(f"Table {table} does not exist")

    # Verify table has status field
    schema = cursor.execute(f"PRAGMA table_info({table})").fetchall()
    has_status = any(col[1] == 'status' for col in schema)

    if not has_status:
        raise ValueError(
            f"Table {table} has no status field. "
            f"Cannot verify authentication outcomes."
        )

    # Calculate totals
    # Status = '0' or 'Success' means authentication succeeded
    # Any other value means authentication FAILED
    totals = cursor.execute(f"""
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN status = '0' OR status = 'Success' THEN 1 END) as successful,
            COUNT(CASE WHEN status != '0' AND status != 'Success' THEN 1 END) as failed
        FROM {table}
    """).fetchone()

    total_events, successful, failed = totals
    success_rate = (successful / total_events * 100.0) if total_events > 0 else 0.0

    # Get status code breakdown
    status_codes = {}
    for row in cursor.execute(
        f"SELECT status, COUNT(*) FROM {table} GROUP BY status"
    ).fetchall():
        status_codes[row[0]] = row[1]

    # Generate warnings based on patterns
    warnings = []

    if total_events == 0:
        warnings.append("ℹ️  No events found in this log type")
    elif success_rate == 0.0:
        warnings.append(
            "✅ 0% success rate - all authentication attempts FAILED "
            "(attack was blocked)"
        )
    elif success_rate == 100.0:
        warnings.append(
            "⚠️  100% success rate - verify this is expected "
            "(legitimate access or compromised account)"
        )
    elif success_rate >= 80.0:
        warnings.append(
            f"⚠️  High success rate ({success_rate:.1f}%) - "
            f"verify if this indicates compromise"
        )

    # Warning for unusual status codes
    unknown_codes = [
        code for code in status_codes.keys()
        if code not in STATUS_CODE_DESCRIPTIONS
    ]
    if unknown_codes:
        warnings.append(
            f"⚠️  Unknown status codes detected: {', '.join(unknown_codes)}"
        )

    return VerificationResult(
        log_type=log_type,
        total_events=total_events,
        successful=successful,
        failed=failed,
        success_rate=success_rate,
        status_codes=status_codes,
        warnings=warnings,
        verified_at=datetime.now().isoformat()
    )


def store_verification(
    conn: sqlite3.Connection,
    result: VerificationResult
) -> int:
    """
    Store verification result in database.

    Results are stored in the verification_summary table for audit trail
    and future reference. This allows IR analysts to review verification
    history and confirm authentication claims.

    Args:
        conn: Database connection
        result: VerificationResult to store

    Returns:
        ID of inserted verification record

    Raises:
        sqlite3.Error: If database write fails

    Example:
        >>> result = verify_auth_status(conn, 'legacy_auth')
        >>> verification_id = store_verification(conn, result)
        >>> print(f"Verification stored: {verification_id}")
    """
    notes = "; ".join(result.warnings) if result.warnings else None

    cursor = conn.execute("""
        INSERT INTO verification_summary
        (log_type, total_events, successful, failed, success_rate,
         status_code_breakdown, verified_at, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        result.log_type,
        result.total_events,
        result.successful,
        result.failed,
        result.success_rate,
        json.dumps(result.status_codes),
        result.verified_at,
        notes
    ))

    conn.commit()
    return cursor.lastrowid


def get_verification_history(
    conn: sqlite3.Connection,
    log_type: Optional[str] = None
) -> list[Dict]:
    """
    Retrieve verification history from database.

    Args:
        conn: Database connection
        log_type: Filter by log type (None = all types)

    Returns:
        List of verification records as dicts

    Example:
        >>> history = get_verification_history(conn, 'legacy_auth')
        >>> for record in history:
        ...     print(f"{record['verified_at']}: {record['success_rate']:.1f}%")
    """
    query = "SELECT * FROM verification_summary"
    params = []

    if log_type:
        query += " WHERE log_type = ?"
        params.append(log_type)

    query += " ORDER BY verified_at DESC"

    cursor = conn.execute(query, params)
    return [dict(row) for row in cursor.fetchall()]


# =============================================================================
# Phase 1.1: Extended Authentication Verification
# =============================================================================
#
# Author: Maia System (SRE Principal Engineer Agent)
# Created: 2026-01-06
# Purpose: Extend verification to sign_in_logs and unified_audit_log
#          to prevent PIR-OCULUS class errors
#
# Background:
# -----------
# PIR-OCULUS-2025-12-19 error occurred in sign_in_logs analysis:
# - Analyst used status_error_code field (100% uniform, unreliable)
# - Should have used conditional_access_status field (ground truth)
# - Result: Concluded "attack failed" when 8 accounts were compromised
#
# Solution:
# ---------
# 1. Auto-detect reliable status field (reject uniform fields)
# 2. Calculate foreign IP success rate (breach indicator)
# 3. Alert on >80% foreign success (strong compromise signal)
# 4. Verify unified_audit_log for exfiltration patterns
#
# Critical Rule:
# --------------
# NEVER trust field names. ALWAYS verify field reliability before use.
# =============================================================================

from dataclasses import dataclass
from typing import List


@dataclass
class SignInVerificationSummary:
    """
    Result of sign_in_logs authentication verification.

    This dataclass stores the complete analysis of sign_in_logs including
    breach detection, field reliability analysis, and data quality scoring.

    Attributes:
        total_records: Total sign_in_logs records analyzed
        success_count: Records with successful authentication
        failure_count: Records with failed authentication
        success_rate: Percentage of successful authentications (0-100)
        foreign_success_count: Successful logins from foreign IPs
        foreign_success_rate: Percentage of foreign successes (0-100)
        breach_detected: True if >80% foreign success rate (critical threshold)
        status_field_used: Which field was used ('conditional_access_status' or other)
        warnings: List of warning messages
        data_quality_score: Data quality score (0-1)
        alert_severity: 'INFO', 'WARNING', or 'CRITICAL'
        created_at: ISO timestamp of verification
    """
    total_records: int
    success_count: int
    failure_count: int
    success_rate: float
    foreign_success_count: int
    foreign_success_rate: float
    breach_detected: bool
    status_field_used: str
    warnings: List[str]
    data_quality_score: float
    alert_severity: str
    created_at: str

    # Phase 2.1.4 extensions (optional with defaults - non-breaking)
    field_used: Optional[str] = None
    field_confidence: Optional[str] = None  # HIGH/MEDIUM/LOW
    field_score: Optional[float] = None  # 0-1 reliability score
    field_selection_reasoning: Optional[str] = None


@dataclass
class AuditVerificationSummary:
    """
    Result of unified_audit_log verification for data exfiltration.

    Detects MailItemsAccessed and FileSyncDownloadedFull operations which
    indicate potential data exfiltration after account compromise.

    Attributes:
        total_records: Total unified_audit_log records analyzed
        mail_items_accessed: Count of MailItemsAccessed operations
        file_sync_downloaded: Count of FileSyncDownloadedFull operations
        exfiltration_indicator: True if high-volume suspicious operations detected
        suspicious_operations: List of suspicious operation details
        created_at: ISO timestamp of verification
    """
    total_records: int
    mail_items_accessed: int
    file_sync_downloaded: int
    exfiltration_indicator: bool
    suspicious_operations: List[Dict]
    created_at: str


def _check_field_reliability(
    db_path: str,
    table: str,
    field: str
) -> tuple[float, bool]:
    """
    Check if a field is reliable (has meaningful variation).

    A field is UNRELIABLE if:
    1. Only 1 distinct value (100% uniform)
    2. Only 2 distinct values with >99% mode (e.g., 99.5% one value, 0.5% another)

    A field is RELIABLE if it has at least 2 distinct values with reasonable distribution.

    Returns:
        (discriminatory_power, is_reliable)
        - discriminatory_power: distinct values / total rows (0-1)
        - is_reliable: True if field has meaningful variation
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get total count
    total = cursor.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    if total == 0:
        conn.close()
        return (0.0, False)

    # Get distinct value count
    distinct = cursor.execute(
        f"SELECT COUNT(DISTINCT {field}) FROM {table}"
    ).fetchone()[0]

    # If only 1 distinct value → 100% uniform → unreliable
    if distinct == 1:
        conn.close()
        return (1.0 / total, False)

    # Get mode (most common value) percentage
    mode_count = cursor.execute(
        f"""
        SELECT COUNT(*) as cnt
        FROM {table}
        GROUP BY {field}
        ORDER BY cnt DESC
        LIMIT 1
        """
    ).fetchone()[0]

    conn.close()

    mode_percentage = (mode_count / total) * 100.0
    discriminatory_power = distinct / total

    # Field is unreliable if >99.5% uniform (basically one value with noise)
    # Example: 99.8% value A, 0.2% value B = unreliable
    # But: 98% value A, 2% value B = RELIABLE (meaningful signal)
    is_reliable = mode_percentage <= 99.5

    return (discriminatory_power, is_reliable)


def _ensure_historical_db() -> str:
    """
    Ensure historical learning database exists (lazy initialization).

    Creates on first use. Safe to call multiple times (idempotent).

    Returns:
        Path to historical database
    """
    from .field_reliability_scorer import create_history_database

    history_path = str(HISTORICAL_DB_PATH)

    if not HISTORICAL_DB_PATH.exists():
        logger.info(f"Creating historical learning database at {history_path}")
        HISTORICAL_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        create_history_database(history_path)

    return history_path


def verify_sign_in_status(db_path: str) -> SignInVerificationSummary:
    """
    Verify sign_in_logs authentication status with automatic field selection.

    This function prevents PIR-OCULUS class errors by:
    1. Auto-detecting the most reliable status field
    2. Rejecting 100% uniform fields (like status_error_code in Oculus)
    3. Calculating foreign IP success rate (breach indicator)
    4. Alerting on >80% foreign success (critical threshold)

    Args:
        db_path: Path to SQLite database containing sign_in_logs table

    Returns:
        SignInVerificationSummary with complete analysis

    Raises:
        ValueError: If sign_in_logs table doesn't exist
        sqlite3.Error: If database query fails

    Example:
        >>> result = verify_sign_in_status('PIR-OCULUS-2025-12-19_logs.db')
        >>> print(f"Breach detected: {result.breach_detected}")
        >>> print(f"Field used: {result.status_field_used}")
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Verify table exists
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='sign_in_logs'"
    )
    if not cursor.fetchone():
        conn.close()
        raise ValueError("Table sign_in_logs does not exist")

    # Phase 2.1.4: Intelligent field selection
    reliable_field = None
    field_confidence = None
    field_score = None
    field_reasoning = None
    warnings = []

    if USE_PHASE_2_1_SCORING:
        from .field_reliability_scorer import recommend_best_field

        try:
            history_db = _ensure_historical_db()
            recommendation = recommend_best_field(
                db_path=db_path,
                table='sign_in_logs',
                log_type='sign_in_logs',
                historical_db_path=history_db
            )

            reliable_field = recommendation.recommended_field
            field_confidence = recommendation.confidence
            field_score = recommendation.all_candidates[0].reliability_score.overall_score
            field_reasoning = recommendation.reasoning

            logger.info(f"Phase 2.1 selected '{reliable_field}' (confidence: {field_confidence}, score: {field_score:.2f})")

            # Collect warnings from all candidates
            for ranking in recommendation.all_candidates:
                warnings.extend(ranking.reliability_score.warnings)

        except Exception as e:
            logger.warning(f"Phase 2.1 failed: {e}. Falling back to Phase 1.")
            reliable_field = None  # Trigger Phase 1 fallback

    # Phase 1 fallback (preserve original logic)
    if not reliable_field:
        candidate_fields = [
            'conditional_access_status',
            'status_error_code',
            'result_status'
        ]

        for field in candidate_fields:
            # Check if field exists
            schema = cursor.execute("PRAGMA table_info(sign_in_logs)").fetchall()
            field_exists = any(col[1] == field for col in schema)

            if not field_exists:
                continue

            # Check reliability
            disc_power, is_reliable = _check_field_reliability(
                db_path, 'sign_in_logs', field
            )

            if not is_reliable:
                warnings.append(
                    f"Field '{field}' is unreliable (>99.5% uniform or only 1 distinct value, "
                    f"discriminatory power: {disc_power:.3f})"
                )
            elif reliable_field is None:
                # Use first reliable field found (but keep checking others for warnings)
                reliable_field = field

    if not reliable_field:
        conn.close()
        raise ValueError(
            "No reliable status field found in sign_in_logs. "
            "All candidate fields are >99.5% uniform."
        )

    # Count total records
    total_records = cursor.execute(
        "SELECT COUNT(*) FROM sign_in_logs"
    ).fetchone()[0]

    # Count successes and failures using reliable field
    if reliable_field == 'conditional_access_status':
        success_count = cursor.execute(
            """
            SELECT COUNT(*) FROM sign_in_logs
            WHERE conditional_access_status = 'success'
            """
        ).fetchone()[0]

        failure_count = cursor.execute(
            """
            SELECT COUNT(*) FROM sign_in_logs
            WHERE conditional_access_status = 'failure'
            """
        ).fetchone()[0]
    elif reliable_field == 'status_error_code':
        success_count = cursor.execute(
            """
            SELECT COUNT(*) FROM sign_in_logs
            WHERE status_error_code = 0
            """
        ).fetchone()[0]

        failure_count = cursor.execute(
            """
            SELECT COUNT(*) FROM sign_in_logs
            WHERE status_error_code != 0
            """
        ).fetchone()[0]
    else:  # result_status
        success_count = cursor.execute(
            """
            SELECT COUNT(*) FROM sign_in_logs
            WHERE result_status = 'Success'
            """
        ).fetchone()[0]

        failure_count = cursor.execute(
            """
            SELECT COUNT(*) FROM sign_in_logs
            WHERE result_status != 'Success'
            """
        ).fetchone()[0]

    success_rate = (success_count / total_records * 100.0) if total_records > 0 else 0.0

    # Calculate foreign IP success rate (breach indicator)
    # Check if location_country field exists
    schema = cursor.execute("PRAGMA table_info(sign_in_logs)").fetchall()
    has_location = any(col[1] == 'location_country' for col in schema)

    foreign_success_count = 0
    if has_location and reliable_field == 'conditional_access_status':
        foreign_success_count = cursor.execute(
            """
            SELECT COUNT(*) FROM sign_in_logs
            WHERE conditional_access_status = 'success'
            AND location_country NOT IN ('AU', 'Australia')
            """
        ).fetchone()[0]

    foreign_success_rate = (
        (foreign_success_count / success_count * 100.0)
        if success_count > 0 else 0.0
    )

    # Determine breach status and alert severity
    # Thresholds:
    # >5% foreign success rate = breach detected (Oculus was 6.3%)
    # >50% = HIGH severity
    # >80% = CRITICAL severity
    breach_detected = foreign_success_rate > 5.0

    if foreign_success_rate > 80.0:
        alert_severity = 'CRITICAL'
        warnings.append(
            f"BREACH DETECTED (CRITICAL): {foreign_success_rate:.1f}% foreign IP success rate "
            f"({foreign_success_count} foreign logins)"
        )
    elif foreign_success_rate > 50.0:
        alert_severity = 'CRITICAL'
        warnings.append(
            f"BREACH DETECTED (HIGH): {foreign_success_rate:.1f}% foreign IP success rate "
            f"({foreign_success_count} foreign logins)"
        )
    elif foreign_success_rate > 5.0:
        alert_severity = 'WARNING'
        warnings.append(
            f"BREACH DETECTED: {foreign_success_rate:.1f}% foreign IP success rate "
            f"({foreign_success_count} foreign logins)"
        )
    else:
        alert_severity = 'INFO'

    # Calculate data quality score based on field reliability
    # Start with perfect score, subtract for each issue
    data_quality_score = 1.0

    # Count unreliable fields from warnings
    unreliable_count = sum(1 for w in warnings if 'unreliable' in w and 'Field' in w)

    # Penalize for unreliable fields (each -0.3)
    data_quality_score -= unreliable_count * 0.3

    # Bonus for using preferred field (conditional_access_status)
    if reliable_field != 'conditional_access_status':
        data_quality_score -= 0.2

    # Clamp to 0-1 range
    data_quality_score = max(0.0, min(1.0, data_quality_score))

    # Store results in verification_summary table if it exists
    try:
        cursor.execute("""
            INSERT INTO verification_summary
            (log_type, total_records, success_count, failure_count,
             success_rate, verification_status, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'sign_in_logs',
            total_records,
            success_count,
            failure_count,
            success_rate,
            'BREACH_DETECTED' if breach_detected else 'OK',
            '; '.join(warnings) if warnings else None,
            datetime.now().isoformat()
        ))
        conn.commit()
    except sqlite3.OperationalError:
        # verification_summary table might not exist, that's OK
        pass

    conn.close()

    return SignInVerificationSummary(
        total_records=total_records,
        success_count=success_count,
        failure_count=failure_count,
        success_rate=success_rate,
        foreign_success_count=foreign_success_count,
        foreign_success_rate=foreign_success_rate,
        breach_detected=breach_detected,
        status_field_used=reliable_field,  # Backward compat
        warnings=warnings,
        data_quality_score=data_quality_score,
        alert_severity=alert_severity,
        created_at=datetime.now().isoformat(),
        # Phase 2.1.4 fields (only set if Phase 2.1 was actually used)
        field_used=reliable_field if field_confidence is not None else None,
        field_confidence=field_confidence,
        field_score=field_score,
        field_selection_reasoning=field_reasoning
    )


def verify_audit_log_operations(db_path: str) -> AuditVerificationSummary:
    """
    Verify unified_audit_log for data exfiltration indicators.

    Detects:
    - MailItemsAccessed: Mailbox access (potential email exfiltration)
    - FileSyncDownloadedFull: OneDrive bulk download (potential file exfiltration)

    Args:
        db_path: Path to SQLite database containing unified_audit_log table

    Returns:
        AuditVerificationSummary with exfiltration analysis

    Raises:
        ValueError: If unified_audit_log table doesn't exist

    Example:
        >>> result = verify_audit_log_operations('PIR-OCULUS-2025-12-19_logs.db')
        >>> if result.exfiltration_indicator:
        ...     print("Data exfiltration detected!")
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Verify table exists
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='unified_audit_log'"
    )
    if not cursor.fetchone():
        conn.close()
        raise ValueError("Table unified_audit_log does not exist")

    # Count total records
    total_records = cursor.execute(
        "SELECT COUNT(*) FROM unified_audit_log"
    ).fetchone()[0]

    # Count MailItemsAccessed operations
    mail_items_accessed = cursor.execute(
        """
        SELECT COUNT(*) FROM unified_audit_log
        WHERE operation = 'MailItemsAccessed'
        """
    ).fetchone()[0]

    # Count FileSyncDownloadedFull operations
    file_sync_downloaded = cursor.execute(
        """
        SELECT COUNT(*) FROM unified_audit_log
        WHERE operation = 'FileSyncDownloadedFull'
        """
    ).fetchone()[0]

    # Detect exfiltration indicator
    # Threshold: >100 MailItemsAccessed OR >50 FileSyncDownloadedFull
    exfiltration_indicator = (
        mail_items_accessed > 100 or
        file_sync_downloaded > 50
    )

    # Collect suspicious operations
    suspicious_operations = []
    if mail_items_accessed > 0:
        suspicious_operations.append({
            'operation': 'MailItemsAccessed',
            'count': mail_items_accessed
        })
    if file_sync_downloaded > 0:
        suspicious_operations.append({
            'operation': 'FileSyncDownloadedFull',
            'count': file_sync_downloaded
        })

    conn.close()

    return AuditVerificationSummary(
        total_records=total_records,
        mail_items_accessed=mail_items_accessed,
        file_sync_downloaded=file_sync_downloaded,
        exfiltration_indicator=exfiltration_indicator,
        suspicious_operations=suspicious_operations,
        created_at=datetime.now().isoformat()
    )


if __name__ == "__main__":
    # Demo usage
    import sys
    from pathlib import Path

    # Add parent directory to path for imports
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    from claude.tools.m365_ir.log_database import IRLogDatabase

    print("=== Auth Verifier Demo ===\n")
    print("This module prevents forensic errors like PIR-OCULUS-2025-12-19")
    print("by forcing verification of authentication success vs failure.\n")

    # Create test database
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        db = IRLogDatabase(case_id='DEMO-VERIFY-001', base_path=tmpdir)
        db.create()
        conn = db.connect()

        # Insert test data simulating PIR-OCULUS-2025-12-19 scenario
        print("Simulating PIR-OCULUS-2025-12-19 scenario...")
        cursor = conn.cursor()

        # Insert failed authentication attempts (status 50126)
        for i in range(37):
            cursor.execute("""
                INSERT INTO legacy_auth_logs
                (timestamp, user_principal_name, client_app_used, status,
                 failure_reason, imported_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                f"2025-12-03T06:{13+i}:00",
                'ben@oculus.info',
                'Authenticated SMTP',
                '50126',
                'Error validating credentials due to invalid username or password',
                datetime.now().isoformat()
            ))

        conn.commit()

        # Run verification
        print("\nRunning verification...")
        result = verify_auth_status(conn, 'legacy_auth')

        print(f"\n{'='*60}")
        print(f"Verification Results - {result.log_type}")
        print(f"{'='*60}")
        print(f"Total events: {result.total_events}")
        print(f"Successful: {result.successful} ({result.success_rate:.1f}%)")
        print(f"Failed: {result.failed} ({100-result.success_rate:.1f}%)")
        print(f"\nStatus code breakdown:")
        for code, count in result.status_codes.items():
            desc = STATUS_CODE_DESCRIPTIONS.get(code, "Unknown")
            print(f"  {code} ({desc}): {count} events")

        if result.warnings:
            print(f"\nWarnings:")
            for warning in result.warnings:
                print(f"  {warning}")

        # Store verification
        verification_id = store_verification(conn, result)
        print(f"\n✅ Verification stored (ID: {verification_id})")

        print("\n" + "="*60)
        print("Conclusion:")
        print("="*60)
        print("BEFORE Phase 241: Claimed '37 SMTP authentications = bypass'")
        print("AFTER Phase 241: Auto-detected 0% success rate = attack BLOCKED")
        print("\nThis prevents future PIR-OCULUS-2025-12-19 errors.")

        conn.close()
