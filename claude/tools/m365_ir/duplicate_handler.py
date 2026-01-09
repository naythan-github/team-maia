#!/usr/bin/env python3
"""
Duplicate Handler - Phase 261.4

Handles duplicate sign-in records using a MERGE approach that preserves all data
rather than deleting records.

Design Philosophy:
- PRESERVE all data (never delete)
- MERGE duplicates by marking secondary records as merged
- MAINTAIN audit trail with merge timestamps and references
- CREATE active view for queries that excludes merged records

Key Features:
1. Identifies duplicates by (timestamp, user_principal_name, ip_address)
2. Adds schema columns: merged_into, merge_status, merged_at
3. Marks primary record with merge_status='primary'
4. Marks secondary records with merge_status='merged' and merged_into=primary_id
5. Creates v_sign_in_logs_active view (excludes merged records)

Usage:
    from duplicate_handler import merge_duplicates, add_merge_columns, create_active_view

    # One-time schema migration
    add_merge_columns(db_path)
    create_active_view(db_path)

    # Run periodically to merge duplicates
    result = merge_duplicates(db_path)
    print(f"Merged {result['records_merged']} records")

Author: Maia System
Created: 2025-01-09
Phase: 261.4
"""

import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass


@dataclass
class DuplicateGroup:
    """Represents a group of duplicate records."""
    timestamp: str
    user_principal_name: str
    ip_address: str
    count: int
    record_ids: List[int]


def add_merge_columns(db_path: str) -> Dict[str, Any]:
    """
    Add merge tracking columns to sign_in_logs table.

    Adds three columns:
    - merged_into (INTEGER): ID of the primary record this was merged into
    - merge_status (TEXT): Status (NULL, 'primary', 'merged')
    - merged_at (TEXT): Timestamp when merge occurred

    This is a one-time migration, idempotent (safe to run multiple times).

    Args:
        db_path: Path to the investigation database

    Returns:
        {
            'success': bool,
            'columns_added': int,
            'message': str
        }
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check existing columns
    cursor.execute("PRAGMA table_info(sign_in_logs)")
    existing_columns = {row[1] for row in cursor.fetchall()}

    columns_to_add = []
    if 'merged_into' not in existing_columns:
        columns_to_add.append(('merged_into', 'INTEGER'))
    if 'merge_status' not in existing_columns:
        columns_to_add.append(('merge_status', 'TEXT'))
    if 'merged_at' not in existing_columns:
        columns_to_add.append(('merged_at', 'TEXT'))

    # Add missing columns
    for col_name, col_type in columns_to_add:
        cursor.execute(f"ALTER TABLE sign_in_logs ADD COLUMN {col_name} {col_type}")

    conn.commit()
    conn.close()

    return {
        'success': True,
        'columns_added': len(columns_to_add),
        'message': f"Added {len(columns_to_add)} merge columns to sign_in_logs"
    }


def create_active_view(db_path: str) -> Dict[str, Any]:
    """
    Create v_sign_in_logs_active view that excludes merged records.

    The view includes:
    - Records with merge_status = NULL (never involved in merge)
    - Records with merge_status = 'primary' (kept as primary in merge)

    Excludes:
    - Records with merge_status = 'merged' (secondary duplicates)

    This view should be used for all queries that want to see only "active" records.

    Args:
        db_path: Path to the investigation database

    Returns:
        {
            'success': bool,
            'message': str
        }
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Drop existing view if it exists
    cursor.execute("DROP VIEW IF EXISTS v_sign_in_logs_active")

    # Create new view
    cursor.execute("""
        CREATE VIEW v_sign_in_logs_active AS
        SELECT *
        FROM sign_in_logs
        WHERE merge_status IS NULL OR merge_status = 'primary'
    """)

    conn.commit()
    conn.close()

    return {
        'success': True,
        'message': 'Created v_sign_in_logs_active view'
    }


def identify_duplicates(db_path: str) -> List[DuplicateGroup]:
    """
    Identify duplicate records in sign_in_logs.

    Duplicates are defined as records with identical:
    - timestamp
    - user_principal_name
    - ip_address

    Only considers records that are not already merged (merge_status != 'merged').

    Args:
        db_path: Path to the investigation database

    Returns:
        List of DuplicateGroup objects, sorted by count (descending)
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Find groups with duplicates
    cursor.execute("""
        SELECT
            timestamp,
            user_principal_name,
            ip_address,
            COUNT(*) as count,
            GROUP_CONCAT(id) as ids
        FROM sign_in_logs
        WHERE (merge_status IS NULL OR merge_status != 'merged')
          AND timestamp IS NOT NULL
          AND user_principal_name IS NOT NULL
        GROUP BY timestamp, user_principal_name, ip_address
        HAVING COUNT(*) > 1
        ORDER BY COUNT(*) DESC
    """)

    results = cursor.fetchall()
    conn.close()

    duplicate_groups = []
    for row in results:
        timestamp, upn, ip, count, ids_str = row
        record_ids = [int(id_str) for id_str in ids_str.split(',')]

        duplicate_groups.append(DuplicateGroup(
            timestamp=timestamp,
            user_principal_name=upn,
            ip_address=ip,
            count=count,
            record_ids=record_ids
        ))

    return duplicate_groups


def merge_duplicates(db_path: str, dry_run: bool = False) -> Dict[str, Any]:
    """
    Merge duplicate records by marking secondary records as merged.

    For each duplicate group:
    1. Select primary record (lowest ID = oldest import)
    2. Mark primary with merge_status='primary'
    3. Mark all secondaries with merge_status='merged' and merged_into=primary_id
    4. Record merge timestamp

    Data preservation: ALL records are kept in the database. Secondary records
    are simply marked as merged, allowing full audit trail and recovery if needed.

    Args:
        db_path: Path to the investigation database
        dry_run: If True, only identify duplicates without merging

    Returns:
        {
            'success': bool,
            'groups_processed': int,
            'records_merged': int,
            'details': List[dict]
        }
    """
    duplicate_groups = identify_duplicates(db_path)

    if not duplicate_groups:
        return {
            'success': True,
            'groups_processed': 0,
            'records_merged': 0,
            'details': [],
            'message': 'No duplicates found'
        }

    if dry_run:
        return {
            'success': True,
            'groups_processed': len(duplicate_groups),
            'records_merged': sum(g.count - 1 for g in duplicate_groups),
            'details': [
                {
                    'timestamp': g.timestamp,
                    'user': g.user_principal_name,
                    'ip': g.ip_address,
                    'count': g.count,
                    'primary_id': g.record_ids[0],
                    'secondary_ids': g.record_ids[1:]
                }
                for g in duplicate_groups
            ],
            'message': 'Dry run - no changes made'
        }

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    merge_timestamp = datetime.now().isoformat()
    details = []
    total_merged = 0

    for group in duplicate_groups:
        # Primary record is the one with lowest ID (oldest import)
        primary_id = group.record_ids[0]
        secondary_ids = group.record_ids[1:]

        # Mark primary record
        cursor.execute("""
            UPDATE sign_in_logs
            SET merge_status = 'primary'
            WHERE id = ?
              AND (merge_status IS NULL OR merge_status != 'primary')
        """, (primary_id,))

        # Mark secondary records as merged
        for secondary_id in secondary_ids:
            cursor.execute("""
                UPDATE sign_in_logs
                SET merge_status = 'merged',
                    merged_into = ?,
                    merged_at = ?
                WHERE id = ?
                  AND (merge_status IS NULL OR merge_status != 'merged')
            """, (primary_id, merge_timestamp, secondary_id))

        total_merged += len(secondary_ids)

        details.append({
            'timestamp': group.timestamp,
            'user': group.user_principal_name,
            'ip': group.ip_address,
            'count': group.count,
            'primary_id': primary_id,
            'secondary_ids': secondary_ids
        })

    conn.commit()
    conn.close()

    return {
        'success': True,
        'groups_processed': len(duplicate_groups),
        'records_merged': total_merged,
        'details': details,
        'message': f"Merged {total_merged} duplicate records across {len(duplicate_groups)} groups"
    }


def unmerge_group(db_path: str, primary_id: int) -> Dict[str, Any]:
    """
    Unmerge a group of previously merged records (recovery function).

    Resets merge_status, merged_into, and merged_at for the specified group.
    Useful for recovering from incorrect merges.

    Args:
        db_path: Path to the investigation database
        primary_id: ID of the primary record whose group should be unmerged

    Returns:
        {
            'success': bool,
            'records_unmerged': int,
            'message': str
        }
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Unmerge secondary records
    cursor.execute("""
        UPDATE sign_in_logs
        SET merge_status = NULL,
            merged_into = NULL,
            merged_at = NULL
        WHERE merged_into = ?
    """, (primary_id,))

    secondary_count = cursor.rowcount

    # Unmerge primary record
    cursor.execute("""
        UPDATE sign_in_logs
        SET merge_status = NULL
        WHERE id = ? AND merge_status = 'primary'
    """, (primary_id,))

    conn.commit()
    conn.close()

    return {
        'success': True,
        'records_unmerged': secondary_count,
        'message': f"Unmerged {secondary_count} records from primary ID {primary_id}"
    }


def get_merge_statistics(db_path: str) -> Dict[str, Any]:
    """
    Get statistics about merge operations in the database.

    Returns:
        {
            'total_records': int,
            'active_records': int,
            'merged_records': int,
            'primary_records': int,
            'merge_groups': int
        }
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Total records
    cursor.execute("SELECT COUNT(*) FROM sign_in_logs")
    total_records = cursor.fetchone()[0]

    # Active records (NULL or primary)
    cursor.execute("""
        SELECT COUNT(*) FROM sign_in_logs
        WHERE merge_status IS NULL OR merge_status = 'primary'
    """)
    active_records = cursor.fetchone()[0]

    # Merged records (secondary)
    cursor.execute("""
        SELECT COUNT(*) FROM sign_in_logs
        WHERE merge_status = 'merged'
    """)
    merged_records = cursor.fetchone()[0]

    # Primary records
    cursor.execute("""
        SELECT COUNT(*) FROM sign_in_logs
        WHERE merge_status = 'primary'
    """)
    primary_records = cursor.fetchone()[0]

    conn.close()

    return {
        'total_records': total_records,
        'active_records': active_records,
        'merged_records': merged_records,
        'primary_records': primary_records,
        'merge_groups': primary_records  # Each primary represents one merge group
    }


if __name__ == '__main__':
    import sys
    import argparse
    import json

    parser = argparse.ArgumentParser(description='Handle duplicate sign-in records')
    parser.add_argument('db_path', help='Path to investigation database')
    parser.add_argument('--action', choices=['identify', 'merge', 'stats', 'add-columns', 'create-view', 'unmerge'],
                        default='identify', help='Action to perform')
    parser.add_argument('--dry-run', action='store_true', help='Dry run (identify only)')
    parser.add_argument('--primary-id', type=int, help='Primary ID for unmerge action')

    args = parser.parse_args()

    if args.action == 'add-columns':
        result = add_merge_columns(args.db_path)
    elif args.action == 'create-view':
        result = create_active_view(args.db_path)
    elif args.action == 'identify':
        duplicates = identify_duplicates(args.db_path)
        result = {
            'groups_found': len(duplicates),
            'total_duplicates': sum(g.count - 1 for g in duplicates),
            'groups': [
                {
                    'timestamp': g.timestamp,
                    'user': g.user_principal_name,
                    'ip': g.ip_address,
                    'count': g.count,
                    'record_ids': g.record_ids
                }
                for g in duplicates
            ]
        }
    elif args.action == 'merge':
        result = merge_duplicates(args.db_path, dry_run=args.dry_run)
    elif args.action == 'unmerge':
        if not args.primary_id:
            print("Error: --primary-id required for unmerge action")
            sys.exit(1)
        result = unmerge_group(args.db_path, args.primary_id)
    elif args.action == 'stats':
        result = get_merge_statistics(args.db_path)
    else:
        result = {'error': 'Unknown action'}

    print(json.dumps(result, indent=2, default=str))
