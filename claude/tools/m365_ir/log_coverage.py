#!/usr/bin/env python3
"""
Log Coverage Summary - Forensic coverage gap detection for M365 IR.

Phase 258 - PIR-FYNA-2025-12-08 lessons learned

Provides instant visibility into forensic coverage gaps during IR triage.
Different log types have different retention windows:
- Sign-in logs: ~60 days
- Unified Audit Log: ~32 days (default, up to 180 with E5)
- Mailbox audit: ~35 days

Usage:
    from claude.tools.m365_ir.log_coverage import update_log_coverage_summary

    result = update_log_coverage_summary("/path/to/case.db")
    if result['gaps_detected'] > 0:
        print("WARNING: Forensic gaps detected!")
        for gap in result['coverage_report']:
            if gap['gap_detected']:
                print(f"  {gap['log_type']}: {gap['gap_description']}")

Author: Maia System (SRE Principal Engineer Agent)
Created: 2026-01-08
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Union


# Log table configuration: (table_name, timestamp_column, log_type_name, expected_days)
LOG_TABLES = {
    'sign_in_logs': ('timestamp', 'sign_in', 90),
    'unified_audit_log': ('timestamp', 'unified_audit_log', 90),
    'mailbox_audit_log': ('timestamp', 'mailbox_audit', 90),
    'entra_audit_log': ('timestamp', 'entra_audit', 90),
    'inbox_rules': ('timestamp', 'inbox_rules', 90),
    'oauth_consents': ('timestamp', 'oauth', 90),
    'legacy_auth_logs': ('timestamp', 'legacy_auth', 90),
    'password_status': ('last_password_change', 'password_status', 90),
    'risky_users': ('risk_last_updated', 'risky_users', 90),
}

# Gap threshold: 80% of expected coverage
GAP_THRESHOLD = 0.8


def update_log_coverage_summary(db_path: Union[str, Path]) -> Dict:
    """
    Scan all log tables and populate/update log_coverage_summary.

    Creates the log_coverage_summary table if it doesn't exist, then
    scans all known log tables to calculate coverage statistics.

    Args:
        db_path: Path to the SQLite database

    Returns:
        dict with keys:
            - tables_scanned: int - number of tables scanned
            - gaps_detected: int - number of tables with coverage gaps
            - coverage_report: list - per-table coverage details
    """
    db_path = Path(db_path)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Ensure table exists
    _create_coverage_table(cursor)

    tables_scanned = 0
    gaps_detected = 0
    coverage_report = []
    now = datetime.now().isoformat()

    # Scan each log table
    for table_name, (ts_column, log_type, expected_days) in LOG_TABLES.items():
        # Check if table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name=?
        """, (table_name,))
        if not cursor.fetchone():
            continue

        tables_scanned += 1

        # Get coverage stats
        cursor.execute(f"""
            SELECT
                MIN({ts_column}) as earliest,
                MAX({ts_column}) as latest,
                COUNT(*) as total
            FROM {table_name}
        """)
        row = cursor.fetchone()

        earliest = row['earliest']
        latest = row['latest']
        total_records = row['total']

        # Calculate coverage days
        coverage_days = 0
        if earliest and latest:
            try:
                earliest_dt = _parse_timestamp(earliest)
                latest_dt = _parse_timestamp(latest)
                coverage_days = (latest_dt - earliest_dt).days
            except (ValueError, TypeError):
                pass

        # Detect gap
        gap_detected = coverage_days < (expected_days * GAP_THRESHOLD)
        gap_description = None
        if total_records == 0:
            gap_description = "No records found"
            gap_detected = True
        elif gap_detected:
            gap_description = (
                f"Only {coverage_days} days of coverage "
                f"(expected ~{expected_days} days, threshold {int(expected_days * GAP_THRESHOLD)})"
            )

        if gap_detected:
            gaps_detected += 1

        # Upsert coverage record
        cursor.execute("""
            INSERT INTO log_coverage_summary (
                log_type, earliest_timestamp, latest_timestamp,
                total_records, coverage_days, expected_days,
                gap_detected, gap_description, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(log_type) DO UPDATE SET
                earliest_timestamp = excluded.earliest_timestamp,
                latest_timestamp = excluded.latest_timestamp,
                total_records = excluded.total_records,
                coverage_days = excluded.coverage_days,
                expected_days = excluded.expected_days,
                gap_detected = excluded.gap_detected,
                gap_description = excluded.gap_description,
                last_updated = excluded.last_updated
        """, (
            log_type,
            earliest or '',
            latest or '',
            total_records,
            coverage_days,
            expected_days,
            1 if gap_detected else 0,
            gap_description,
            now
        ))

        coverage_report.append({
            'log_type': log_type,
            'table_name': table_name,
            'earliest': earliest,
            'latest': latest,
            'total_records': total_records,
            'coverage_days': coverage_days,
            'expected_days': expected_days,
            'gap_detected': gap_detected,
            'gap_description': gap_description,
        })

    conn.commit()
    conn.close()

    return {
        'tables_scanned': tables_scanned,
        'gaps_detected': gaps_detected,
        'coverage_report': coverage_report,
    }


def _create_coverage_table(cursor: sqlite3.Cursor) -> None:
    """Create the log_coverage_summary table if it doesn't exist."""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS log_coverage_summary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            log_type TEXT NOT NULL UNIQUE,
            earliest_timestamp TEXT,
            latest_timestamp TEXT,
            total_records INTEGER NOT NULL,
            coverage_days INTEGER NOT NULL,
            expected_days INTEGER DEFAULT 90,
            gap_detected INTEGER DEFAULT 0,
            gap_description TEXT,
            last_updated TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_coverage_log_type
        ON log_coverage_summary(log_type)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_coverage_gap
        ON log_coverage_summary(gap_detected)
    """)


def _parse_timestamp(ts_str: str) -> datetime:
    """Parse various timestamp formats to datetime."""
    if not ts_str:
        raise ValueError("Empty timestamp")

    # Try ISO format first
    try:
        return datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
    except ValueError:
        pass

    # Try common formats
    formats = [
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%d/%m/%Y %I:%M:%S %p",
        "%m/%d/%Y %I:%M:%S %p",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(ts_str, fmt)
        except ValueError:
            continue

    raise ValueError(f"Cannot parse timestamp: {ts_str}")


def get_coverage_summary(db_path: Union[str, Path]) -> Dict:
    """
    Get existing coverage summary without recalculating.

    Args:
        db_path: Path to the SQLite database

    Returns:
        dict mapping log_type to coverage info
    """
    db_path = Path(db_path)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM log_coverage_summary")
        rows = cursor.fetchall()
    except sqlite3.OperationalError:
        return {}
    finally:
        conn.close()

    return {row['log_type']: dict(row) for row in rows}


if __name__ == "__main__":
    # Demo usage
    import sys
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
        result = update_log_coverage_summary(db_path)
        print(f"Scanned {result['tables_scanned']} tables")
        print(f"Gaps detected: {result['gaps_detected']}")
        for item in result['coverage_report']:
            status = "⚠️ GAP" if item['gap_detected'] else "✅"
            print(f"  {status} {item['log_type']}: {item['total_records']} records, "
                  f"{item['coverage_days']} days")
