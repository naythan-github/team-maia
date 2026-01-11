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


# =============================================================================
# Phase 264: Multi-Schema Verification (Graph API, Service Principals)
# =============================================================================
#
# Author: Maia System (SRE Principal Engineer Agent)
# Created: 2026-01-11
# Purpose: Extend verification for Graph API schemas and service principals
#
# Features:
# - Service principal authentication verification
# - Latency pattern analysis
# - Device compliance verification
# - MFA requirement vs satisfaction verification
# =============================================================================

@dataclass
class ServicePrincipalVerificationSummary:
    """
    Result of service principal authentication verification.

    Attributes:
        total_sp_signins: Total service principal sign-ins
        sp_success_count: Successful SP authentications
        sp_failure_count: Failed SP authentications
        sp_success_rate: SP success rate percentage (0-100)
        total_user_signins: Total user sign-ins (for comparison)
        unique_service_principals: Count of unique service principals
        by_application: Breakdown by application
        warnings: List of warning messages
        created_at: ISO timestamp of verification
    """
    total_sp_signins: int
    sp_success_count: int
    sp_failure_count: int
    sp_success_rate: float
    total_user_signins: int
    unique_service_principals: int
    by_application: Dict[str, Dict[str, int]]
    warnings: List[str]
    created_at: str


@dataclass
class LatencyVerificationSummary:
    """
    Result of sign-in latency analysis.

    Attributes:
        total_with_latency: Records with latency data
        avg_latency_ms: Average latency in milliseconds
        median_latency_ms: Median latency
        p95_latency_ms: 95th percentile latency
        slow_signin_count: Sign-ins >1000ms
        very_slow_signin_count: Sign-ins >5000ms
        latency_categories: Breakdown by category (FAST/NORMAL/SLOW/VERY_SLOW)
        warnings: List of warning messages
        created_at: ISO timestamp of verification
    """
    total_with_latency: int
    avg_latency_ms: float
    median_latency_ms: int
    p95_latency_ms: int
    slow_signin_count: int
    very_slow_signin_count: int
    latency_categories: Dict[str, int]
    warnings: List[str]
    created_at: str


@dataclass
class DeviceComplianceVerificationSummary:
    """
    Result of device compliance verification.

    Attributes:
        total_with_device_info: Records with device information
        compliant_count: Compliant devices
        noncompliant_count: Non-compliant devices
        compliance_rate: Compliance rate percentage (0-100)
        managed_count: Managed devices
        unmanaged_count: Unmanaged devices
        warnings: List of warning messages
        created_at: ISO timestamp of verification
    """
    total_with_device_info: int
    compliant_count: int
    noncompliant_count: int
    compliance_rate: float
    managed_count: int
    unmanaged_count: int
    warnings: List[str]
    created_at: str


@dataclass
class MFAVerificationSummary:
    """
    Result of MFA requirement verification.

    Attributes:
        total_signins: Total sign-ins analyzed
        mfa_required_count: Sign-ins where MFA was required
        mfa_satisfied_count: Sign-ins where MFA was satisfied
        mfa_gap_count: Required but not satisfied (security risk)
        mfa_satisfaction_rate: MFA satisfaction rate percentage (0-100)
        by_auth_requirement: Breakdown by auth requirement type
        warnings: List of warning messages
        created_at: ISO timestamp of verification
    """
    total_signins: int
    mfa_required_count: int
    mfa_satisfied_count: int
    mfa_gap_count: int
    mfa_satisfaction_rate: float
    by_auth_requirement: Dict[str, int]
    warnings: List[str]
    created_at: str


def verify_service_principal_status(db_path: str) -> ServicePrincipalVerificationSummary:
    """
    Verify service principal authentication patterns.

    Separates service principal authentications from user authentications to
    detect automated attack patterns or credential compromise.

    Args:
        db_path: Path to SQLite database containing sign_in_logs table

    Returns:
        ServicePrincipalVerificationSummary with SP analysis

    Raises:
        ValueError: If sign_in_logs table doesn't exist

    Example:
        >>> result = verify_service_principal_status('case.db')
        >>> print(f"SP success rate: {result.sp_success_rate:.1f}%")
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Verify table exists
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='sign_in_logs'"
    )
    if not cursor.fetchone():
        conn.close()
        raise ValueError("Table sign_in_logs does not exist")

    warnings = []

    # Count service principal sign-ins
    total_sp_signins = cursor.execute(
        "SELECT COUNT(*) FROM sign_in_logs WHERE is_service_principal = 1"
    ).fetchone()[0]

    # Count user sign-ins
    total_user_signins = cursor.execute(
        "SELECT COUNT(*) FROM sign_in_logs WHERE is_service_principal = 0 OR is_service_principal IS NULL"
    ).fetchone()[0]

    if total_sp_signins == 0:
        conn.close()
        return ServicePrincipalVerificationSummary(
            total_sp_signins=0,
            sp_success_count=0,
            sp_failure_count=0,
            sp_success_rate=0.0,
            total_user_signins=total_user_signins,
            unique_service_principals=0,
            by_application={},
            warnings=["No service principal sign-ins found"],
            created_at=datetime.now().isoformat()
        )

    # Count successful vs failed SP authentications
    sp_success_count = cursor.execute("""
        SELECT COUNT(*) FROM sign_in_logs
        WHERE is_service_principal = 1
        AND (status_error_code = 0 OR status_error_code IS NULL)
    """).fetchone()[0]

    sp_failure_count = cursor.execute("""
        SELECT COUNT(*) FROM sign_in_logs
        WHERE is_service_principal = 1
        AND status_error_code != 0
        AND status_error_code IS NOT NULL
    """).fetchone()[0]

    sp_success_rate = (sp_success_count / total_sp_signins * 100.0) if total_sp_signins > 0 else 0.0

    # Count unique service principals
    unique_service_principals = cursor.execute("""
        SELECT COUNT(DISTINCT service_principal_id)
        FROM sign_in_logs
        WHERE is_service_principal = 1
        AND service_principal_id IS NOT NULL
    """).fetchone()[0]

    # Breakdown by application
    by_application = {}
    app_rows = cursor.execute("""
        SELECT app_display_name,
               COUNT(*) as total,
               SUM(CASE WHEN status_error_code = 0 OR status_error_code IS NULL THEN 1 ELSE 0 END) as success,
               SUM(CASE WHEN status_error_code != 0 AND status_error_code IS NOT NULL THEN 1 ELSE 0 END) as failure
        FROM sign_in_logs
        WHERE is_service_principal = 1
        AND app_display_name IS NOT NULL
        GROUP BY app_display_name
    """).fetchall()

    for row in app_rows:
        by_application[row['app_display_name']] = {
            'total': row['total'],
            'success': row['success'],
            'failure': row['failure']
        }

    # Warnings
    if sp_failure_count > sp_success_count:
        warnings.append(
            f"⚠️  High service principal failure rate: {sp_failure_count}/{total_sp_signins} failed "
            f"({100 - sp_success_rate:.1f}%)"
        )

    conn.close()

    return ServicePrincipalVerificationSummary(
        total_sp_signins=total_sp_signins,
        sp_success_count=sp_success_count,
        sp_failure_count=sp_failure_count,
        sp_success_rate=sp_success_rate,
        total_user_signins=total_user_signins,
        unique_service_principals=unique_service_principals,
        by_application=by_application,
        warnings=warnings,
        created_at=datetime.now().isoformat()
    )


def verify_latency_patterns(db_path: str) -> LatencyVerificationSummary:
    """
    Analyze sign-in latency patterns for anomaly detection.

    Slow sign-ins (>1000ms) may indicate automated attacks or credential stuffing.

    Args:
        db_path: Path to SQLite database

    Returns:
        LatencyVerificationSummary with latency analysis

    Example:
        >>> result = verify_latency_patterns('case.db')
        >>> print(f"Average latency: {result.avg_latency_ms}ms")
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    warnings = []

    # Count total records with latency data
    total_with_latency = cursor.execute(
        "SELECT COUNT(*) FROM sign_in_logs WHERE latency_ms IS NOT NULL"
    ).fetchone()[0]

    if total_with_latency == 0:
        conn.close()
        return LatencyVerificationSummary(
            total_with_latency=0,
            avg_latency_ms=0.0,
            median_latency_ms=0,
            p95_latency_ms=0,
            slow_signin_count=0,
            very_slow_signin_count=0,
            latency_categories={},
            warnings=["No latency data available"],
            created_at=datetime.now().isoformat()
        )

    # Calculate statistics
    avg_latency = cursor.execute(
        "SELECT AVG(latency_ms) FROM sign_in_logs WHERE latency_ms IS NOT NULL"
    ).fetchone()[0]

    # Median (50th percentile)
    median_latency = cursor.execute(f"""
        SELECT latency_ms
        FROM sign_in_logs
        WHERE latency_ms IS NOT NULL
        ORDER BY latency_ms
        LIMIT 1 OFFSET {total_with_latency // 2}
    """).fetchone()[0]

    # 95th percentile
    p95_offset = int(total_with_latency * 0.95)
    p95_latency = cursor.execute(f"""
        SELECT latency_ms
        FROM sign_in_logs
        WHERE latency_ms IS NOT NULL
        ORDER BY latency_ms
        LIMIT 1 OFFSET {p95_offset}
    """).fetchone()[0]

    # Count slow sign-ins
    slow_signin_count = cursor.execute(
        "SELECT COUNT(*) FROM sign_in_logs WHERE latency_ms > 1000"
    ).fetchone()[0]

    very_slow_signin_count = cursor.execute(
        "SELECT COUNT(*) FROM sign_in_logs WHERE latency_ms > 5000"
    ).fetchone()[0]

    # Categorize latency
    latency_categories = {
        'FAST': cursor.execute("SELECT COUNT(*) FROM sign_in_logs WHERE latency_ms < 100").fetchone()[0],
        'NORMAL': cursor.execute("SELECT COUNT(*) FROM sign_in_logs WHERE latency_ms >= 100 AND latency_ms < 500").fetchone()[0],
        'SLOW': cursor.execute("SELECT COUNT(*) FROM sign_in_logs WHERE latency_ms >= 500 AND latency_ms < 1000").fetchone()[0],
        'VERY_SLOW': cursor.execute("SELECT COUNT(*) FROM sign_in_logs WHERE latency_ms >= 1000").fetchone()[0],
    }

    # Warnings
    if slow_signin_count > (total_with_latency * 0.1):
        warnings.append(
            f"⚠️  High slow sign-in rate: {slow_signin_count}/{total_with_latency} "
            f"({slow_signin_count / total_with_latency * 100:.1f}%) >1000ms"
        )

    conn.close()

    return LatencyVerificationSummary(
        total_with_latency=total_with_latency,
        avg_latency_ms=avg_latency,
        median_latency_ms=median_latency,
        p95_latency_ms=p95_latency,
        slow_signin_count=slow_signin_count,
        very_slow_signin_count=very_slow_signin_count,
        latency_categories=latency_categories,
        warnings=warnings,
        created_at=datetime.now().isoformat()
    )


def verify_device_compliance(db_path: str) -> DeviceComplianceVerificationSummary:
    """
    Verify device compliance rates for sign-ins.

    Non-compliant devices accessing corporate resources are a security risk.

    Args:
        db_path: Path to SQLite database

    Returns:
        DeviceComplianceVerificationSummary with compliance analysis

    Example:
        >>> result = verify_device_compliance('case.db')
        >>> print(f"Compliance rate: {result.compliance_rate:.1f}%")
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    warnings = []

    # Count records with device info
    total_with_device_info = cursor.execute(
        "SELECT COUNT(*) FROM sign_in_logs WHERE device_compliant IS NOT NULL"
    ).fetchone()[0]

    if total_with_device_info == 0:
        conn.close()
        return DeviceComplianceVerificationSummary(
            total_with_device_info=0,
            compliant_count=0,
            noncompliant_count=0,
            compliance_rate=0.0,
            managed_count=0,
            unmanaged_count=0,
            warnings=["No device compliance data available"],
            created_at=datetime.now().isoformat()
        )

    # Count compliant vs non-compliant
    compliant_count = cursor.execute(
        "SELECT COUNT(*) FROM sign_in_logs WHERE device_compliant = 1"
    ).fetchone()[0]

    noncompliant_count = cursor.execute(
        "SELECT COUNT(*) FROM sign_in_logs WHERE device_compliant = 0"
    ).fetchone()[0]

    compliance_rate = (compliant_count / total_with_device_info * 100.0) if total_with_device_info > 0 else 0.0

    # Count managed vs unmanaged
    managed_count = cursor.execute(
        "SELECT COUNT(*) FROM sign_in_logs WHERE device_managed = 1"
    ).fetchone()[0]

    unmanaged_count = cursor.execute(
        "SELECT COUNT(*) FROM sign_in_logs WHERE device_managed = 0"
    ).fetchone()[0]

    # Warnings
    if compliance_rate < 80.0:
        warnings.append(
            f"⚠️  Low device compliance rate: {compliance_rate:.1f}% "
            f"({noncompliant_count}/{total_with_device_info} non-compliant)"
        )

    conn.close()

    return DeviceComplianceVerificationSummary(
        total_with_device_info=total_with_device_info,
        compliant_count=compliant_count,
        noncompliant_count=noncompliant_count,
        compliance_rate=compliance_rate,
        managed_count=managed_count,
        unmanaged_count=unmanaged_count,
        warnings=warnings,
        created_at=datetime.now().isoformat()
    )


def verify_mfa_status(db_path: str) -> MFAVerificationSummary:
    """
    Verify MFA requirement vs satisfaction.

    Gap between required and satisfied MFA indicates security policy gaps.

    Args:
        db_path: Path to SQLite database

    Returns:
        MFAVerificationSummary with MFA analysis

    Example:
        >>> result = verify_mfa_status('case.db')
        >>> print(f"MFA gap: {result.mfa_gap_count} sign-ins")
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    warnings = []

    # Count total sign-ins with auth requirement data
    total_signins = cursor.execute(
        "SELECT COUNT(*) FROM sign_in_logs WHERE auth_requirement IS NOT NULL"
    ).fetchone()[0]

    if total_signins == 0:
        conn.close()
        return MFAVerificationSummary(
            total_signins=0,
            mfa_required_count=0,
            mfa_satisfied_count=0,
            mfa_gap_count=0,
            mfa_satisfaction_rate=0.0,
            by_auth_requirement={},
            warnings=["No MFA data available"],
            created_at=datetime.now().isoformat()
        )

    # Count MFA required (matches "Multifactor authentication" from Graph API)
    # Also matches legacy "multiFactorAuthentication" format
    mfa_required_count = cursor.execute("""
        SELECT COUNT(*) FROM sign_in_logs
        WHERE auth_requirement LIKE '%Multifactor%'
           OR auth_requirement LIKE '%multiFactor%'
    """).fetchone()[0]

    # Count MFA satisfied - matches real Graph API values:
    # - "MFA requirement satisfied by claim in the token"
    # - "MFA completed in Azure AD"
    # - "MFA not required during Windows broker logon flow"
    mfa_satisfied_count = cursor.execute("""
        SELECT COUNT(*) FROM sign_in_logs
        WHERE (auth_requirement LIKE '%Multifactor%' OR auth_requirement LIKE '%multiFactor%')
        AND (mfa_result LIKE '%satisfied%' OR mfa_result LIKE '%completed%' OR mfa_result LIKE '%not required%')
    """).fetchone()[0]

    # Calculate gap (required but not satisfied)
    mfa_gap_count = mfa_required_count - mfa_satisfied_count

    mfa_satisfaction_rate = (mfa_satisfied_count / mfa_required_count * 100.0) if mfa_required_count > 0 else 0.0

    # Breakdown by auth requirement
    by_auth_requirement = {}
    auth_rows = cursor.execute("""
        SELECT auth_requirement, COUNT(*) as count
        FROM sign_in_logs
        WHERE auth_requirement IS NOT NULL
        GROUP BY auth_requirement
    """).fetchall()

    for row in auth_rows:
        by_auth_requirement[row[0]] = row[1]

    # Warnings
    if mfa_gap_count > 0:
        warnings.append(
            f"⚠️  MFA gap detected: {mfa_gap_count} sign-ins required MFA but not satisfied "
            f"({100 - mfa_satisfaction_rate:.1f}% gap)"
        )

    conn.close()

    return MFAVerificationSummary(
        total_signins=total_signins,
        mfa_required_count=mfa_required_count,
        mfa_satisfied_count=mfa_satisfied_count,
        mfa_gap_count=mfa_gap_count,
        mfa_satisfaction_rate=mfa_satisfaction_rate,
        by_auth_requirement=by_auth_requirement,
        warnings=warnings,
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
