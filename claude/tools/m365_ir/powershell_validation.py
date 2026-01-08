#!/usr/bin/env python3
"""
PowerShell Export Validation - Detect corrupted M365 exports.

Phase 258 - PIR-FYNA-2025-12-08 lessons learned

Detects exports where PowerShell failed to expand .NET objects, resulting in
type names like:
    Microsoft.Graph.PowerShell.Models.MicrosoftGraphSignInStatus

Instead of actual values. This led to incorrect breach determination in
PIR-FYNA-2025-12-08 when the Status field contained object type names
rather than actual status values.

Usage:
    from claude.tools.m365_ir.powershell_validation import check_powershell_object_corruption

    result = check_powershell_object_corruption("/path/to/case.db", "sign_in_logs")
    if result['corrupted']:
        print(f"WARNING: Corrupted fields: {result['affected_fields']}")
        print(f"Samples: {result['sample_values']}")

Author: Maia System (SRE Principal Engineer Agent)
Created: 2026-01-08
"""

import re
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Union


# Pattern to detect PowerShell .NET object type names
# Matches: Microsoft.Graph.PowerShell.Models.* or Microsoft.PowerShell.Models.*
POWERSHELL_OBJECT_PATTERN = re.compile(
    r'^Microsoft\.(Graph\.)?PowerShell\.Models\.',
    re.IGNORECASE
)

# Known text columns to check for corruption
TEXT_COLUMNS = {
    'sign_in_logs': [
        'status_failure_reason',
        'conditional_access_status',
        'risk_detail',
        'risk_state',
        'mfa_detail',
        'device_detail',
    ],
    'unified_audit_log': [
        'result_status',
        'user_agent',
    ],
    'entra_audit_log': [
        'result',
        'result_reason',
    ],
}


def check_powershell_object_corruption(
    db_path: Union[str, Path],
    table: str
) -> Dict:
    """
    Scan text columns for PowerShell object type patterns.

    Args:
        db_path: Path to the SQLite database
        table: Table name to scan

    Returns:
        dict with keys:
            - corrupted: bool - True if any corruption detected
            - affected_fields: list - column names with corruption
            - sample_values: dict - {column: sample_value} for debugging
    """
    db_path = Path(db_path)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    affected_fields = []
    sample_values = {}

    # Get columns to check for this table
    columns_to_check = TEXT_COLUMNS.get(table, [])

    if not columns_to_check:
        # Fallback: get all TEXT columns from schema
        cursor.execute(f"PRAGMA table_info({table})")
        columns_to_check = [
            row['name'] for row in cursor.fetchall()
            if row['type'].upper() == 'TEXT'
        ]

    # Check each column
    for column in columns_to_check:
        try:
            # Check if column exists
            cursor.execute(f"PRAGMA table_info({table})")
            existing_columns = [row['name'] for row in cursor.fetchall()]
            if column not in existing_columns:
                continue

            # Query for PowerShell object patterns
            cursor.execute(f"""
                SELECT {column} FROM {table}
                WHERE {column} LIKE 'Microsoft.%PowerShell.Models.%'
                LIMIT 5
            """)
            rows = cursor.fetchall()

            if rows:
                # Verify with regex (LIKE is case-insensitive approximation)
                for row in rows:
                    value = row[column]
                    if value and POWERSHELL_OBJECT_PATTERN.match(value):
                        if column not in affected_fields:
                            affected_fields.append(column)
                            sample_values[column] = value
                        break

        except sqlite3.OperationalError:
            # Column doesn't exist or other DB error
            continue

    corrupted = len(affected_fields) > 0

    # Update quality_check_summary if corruption found
    if corrupted:
        _update_quality_summary(cursor, table, affected_fields)
        conn.commit()

    conn.close()

    return {
        'corrupted': corrupted,
        'affected_fields': affected_fields,
        'sample_values': sample_values,
    }


def _update_quality_summary(
    cursor: sqlite3.Cursor,
    table: str,
    affected_fields: List[str]
) -> None:
    """Update quality_check_summary with PowerShell corruption warning."""
    now = datetime.now().isoformat()

    # Build warning message
    warning = (
        f"PowerShell object corruption detected in fields: {', '.join(affected_fields)}. "
        f"Data may contain .NET type names instead of actual values."
    )

    recommendation = (
        "Re-export logs using -ExpandProperty or ConvertTo-Json -Depth 10 "
        "to properly serialize nested objects."
    )

    try:
        cursor.execute("""
            INSERT INTO quality_check_summary (
                table_name, overall_quality_score, reliable_fields_count,
                unreliable_fields_count, check_passed, warnings,
                recommendations, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            table,
            0.5,  # Low quality score due to corruption
            0,  # Can't determine reliable fields
            len(affected_fields),
            0,  # Failed check
            warning,
            recommendation,
            now
        ))
    except sqlite3.IntegrityError:
        # Row already exists, update it
        cursor.execute("""
            UPDATE quality_check_summary
            SET warnings = ?, recommendations = ?, check_passed = 0,
                overall_quality_score = 0.5, created_at = ?
            WHERE table_name = ?
        """, (warning, recommendation, now, table))


def validate_all_tables(db_path: Union[str, Path]) -> Dict:
    """
    Validate all known tables for PowerShell corruption.

    Args:
        db_path: Path to the SQLite database

    Returns:
        dict mapping table name to validation result
    """
    results = {}
    for table in TEXT_COLUMNS.keys():
        results[table] = check_powershell_object_corruption(db_path, table)
    return results


if __name__ == "__main__":
    # Demo usage
    import sys
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
        print("Checking for PowerShell export corruption...")
        results = validate_all_tables(db_path)

        any_corrupted = False
        for table, result in results.items():
            if result['corrupted']:
                any_corrupted = True
                print(f"⚠️  {table}: CORRUPTED")
                print(f"    Fields: {result['affected_fields']}")
                for field, sample in result['sample_values'].items():
                    print(f"    Sample {field}: {sample[:80]}...")
            else:
                print(f"✅ {table}: OK")

        if any_corrupted:
            print("\n⚠️  WARNING: PowerShell export corruption detected!")
            print("   Re-export with: | ConvertTo-Json -Depth 10")
