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
import sqlite3
from datetime import datetime
from typing import Dict, NamedTuple, Optional


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
