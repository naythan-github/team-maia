#!/usr/bin/env python3
"""
Phase 261.2: Risk Level Backfill Migration

Backfills risk_level column from raw_record JSON for records where it's NULL/unknown.

This migration extracts RiskLevelDuringSignIn from the raw_record BLOB and populates
the risk_level column for better query performance.

Usage:
    python3 backfill_risk_levels.py /path/to/case_logs.db

Author: Maia System (SRE Principal Engineer Agent)
Created: 2026-01-09
"""

import sqlite3
import sys
import json
from pathlib import Path
from typing import Dict


def backfill_risk_levels(db_path: str) -> Dict:
    """
    Backfill risk_level column from raw_record JSON.

    Args:
        db_path: Path to the database file

    Returns:
        {
            'success': bool,
            'records_checked': int,
            'records_updated': int,
            'errors': []
        }
    """
    from claude.tools.m365_ir.compression import decompress_json

    result = {
        'success': False,
        'records_checked': 0,
        'records_updated': 0,
        'errors': []
    }

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Find records with raw_record but unknown risk_level
        cursor.execute("""
            SELECT id, raw_record FROM sign_in_logs
            WHERE raw_record IS NOT NULL
            AND (risk_level IS NULL OR risk_level = '' OR risk_level = 'unknown')
        """)

        records = cursor.fetchall()

        for row in records:
            result['records_checked'] += 1
            record_id = row['id']
            raw_blob = row['raw_record']

            try:
                # Decompress and parse JSON
                raw_json = decompress_json(raw_blob)
                if isinstance(raw_json, str):
                    raw_json = json.loads(raw_json)

                # Extract risk level (case-insensitive, convert to lowercase)
                risk_signin = raw_json.get('RiskLevelDuringSignIn', '').lower()

                # Only update if we found a non-empty, non-unknown value
                if risk_signin and risk_signin != 'unknown':
                    cursor.execute("""
                        UPDATE sign_in_logs
                        SET risk_level = ?
                        WHERE id = ?
                    """, (risk_signin, record_id))
                    result['records_updated'] += 1

            except Exception as e:
                result['errors'].append(f"Record {record_id}: {e}")

        conn.commit()
        result['success'] = True

    except Exception as e:
        result['errors'].append(f"Migration failed: {e}")
        if 'conn' in locals():
            conn.rollback()

    finally:
        if 'conn' in locals():
            conn.close()

    return result


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 backfill_risk_levels.py /path/to/case_logs.db")
        sys.exit(1)

    db_path = sys.argv[1]

    if not Path(db_path).exists():
        print(f"Error: Database not found: {db_path}")
        sys.exit(1)

    print(f"Backfilling risk_level from raw_record JSON...")
    print(f"Database: {db_path}\n")

    result = backfill_risk_levels(db_path)

    print(f"Records checked: {result['records_checked']}")
    print(f"Records updated: {result['records_updated']}")

    if result['errors']:
        print(f"\nErrors encountered: {len(result['errors'])}")
        for error in result['errors'][:10]:  # Show first 10
            print(f"  - {error}")

    if result['success']:
        print("\n✅ Migration completed successfully")
    else:
        print("\n❌ Migration failed")
        sys.exit(1)
