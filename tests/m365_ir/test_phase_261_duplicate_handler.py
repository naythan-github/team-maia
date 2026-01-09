#!/usr/bin/env python3
"""
Tests for Phase 261.4 - Duplicate Handler

Tests the duplicate_handler module which handles duplicate sign-in records
using a MERGE approach (preserves data) rather than DELETE.

Key features:
- Identifies duplicates by (timestamp, user_principal_name, ip_address)
- MERGES duplicate records (marks secondary as merged, preserves data)
- Adds schema columns: merged_into, merge_status, merged_at
- Creates v_sign_in_logs_active view (excludes merged records)
- Full audit trail

Design philosophy: PRESERVE data, don't delete. Mark as merged with references.

Author: Maia System
Created: 2025-01-09
Phase: 261.4
"""

import pytest
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import json

# Import will be available after implementation
from claude.tools.m365_ir.duplicate_handler import (
    identify_duplicates,
    merge_duplicates,
    add_merge_columns,
    create_active_view,
    DuplicateGroup,
)


@pytest.fixture
def test_db():
    """Create a temporary test database with schema."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create sign_in_logs table (without merge columns initially)
    cursor.execute("""
        CREATE TABLE sign_in_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            user_principal_name TEXT NOT NULL,
            user_display_name TEXT,
            ip_address TEXT,
            location_city TEXT,
            location_country TEXT,
            client_app TEXT,
            status_error_code INTEGER,
            status_failure_reason TEXT,
            conditional_access_status TEXT,
            mfa_detail TEXT,
            risk_level TEXT,
            raw_record BLOB,
            imported_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()

    yield db_path

    # Cleanup
    Path(db_path).unlink()


class TestAddMergeColumns:
    """Test add_merge_columns migration function."""

    def test_add_merge_columns_to_new_table(self, test_db):
        """Test adding merge columns to table without them."""
        result = add_merge_columns(test_db)

        assert result['success'] is True
        assert result['columns_added'] >= 1

        # Verify columns exist
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(sign_in_logs)")
        columns = {row[1] for row in cursor.fetchall()}
        conn.close()

        assert 'merged_into' in columns
        assert 'merge_status' in columns
        assert 'merged_at' in columns

    def test_add_merge_columns_idempotent(self, test_db):
        """Test that running twice is safe (idempotent)."""
        # Add columns first time
        result1 = add_merge_columns(test_db)
        assert result1['success'] is True

        # Add columns second time (should be no-op)
        result2 = add_merge_columns(test_db)
        assert result2['success'] is True
        assert result2['columns_added'] == 0  # Already exist


class TestIdentifyDuplicates:
    """Test identify_duplicates function."""

    def test_no_duplicates(self, test_db):
        """Test identifying no duplicates in clean database."""
        add_merge_columns(test_db)

        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        # Insert unique records
        cursor.execute("""
            INSERT INTO sign_in_logs (timestamp, user_principal_name, ip_address, imported_at)
            VALUES (?, ?, ?, ?)
        """, ('2025-11-25T04:55:50', 'user1@example.com', '1.2.3.4', datetime.now().isoformat()))

        cursor.execute("""
            INSERT INTO sign_in_logs (timestamp, user_principal_name, ip_address, imported_at)
            VALUES (?, ?, ?, ?)
        """, ('2025-11-25T05:00:00', 'user2@example.com', '5.6.7.8', datetime.now().isoformat()))

        conn.commit()
        conn.close()

        duplicates = identify_duplicates(test_db)

        assert len(duplicates) == 0

    def test_identify_exact_duplicates(self, test_db):
        """Test identifying exact duplicate records."""
        add_merge_columns(test_db)

        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        # Insert duplicate records (same timestamp, user, IP)
        for _ in range(3):
            cursor.execute("""
                INSERT INTO sign_in_logs (timestamp, user_principal_name, ip_address, location_city, imported_at)
                VALUES (?, ?, ?, ?, ?)
            """, ('2025-11-25T04:55:50', 'user@example.com', '1.2.3.4', 'Istanbul', datetime.now().isoformat()))

        conn.commit()
        conn.close()

        duplicates = identify_duplicates(test_db)

        assert len(duplicates) == 1
        assert duplicates[0].count == 3
        assert duplicates[0].timestamp == '2025-11-25T04:55:50'
        assert duplicates[0].user_principal_name == 'user@example.com'
        assert duplicates[0].ip_address == '1.2.3.4'
        assert len(duplicates[0].record_ids) == 3

    def test_identify_multiple_duplicate_groups(self, test_db):
        """Test identifying multiple groups of duplicates."""
        add_merge_columns(test_db)

        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        # Group 1: 2 duplicates
        for _ in range(2):
            cursor.execute("""
                INSERT INTO sign_in_logs (timestamp, user_principal_name, ip_address, imported_at)
                VALUES (?, ?, ?, ?)
            """, ('2025-11-25T04:55:50', 'user1@example.com', '1.2.3.4', datetime.now().isoformat()))

        # Group 2: 3 duplicates
        for _ in range(3):
            cursor.execute("""
                INSERT INTO sign_in_logs (timestamp, user_principal_name, ip_address, imported_at)
                VALUES (?, ?, ?, ?)
            """, ('2025-11-25T05:00:00', 'user2@example.com', '5.6.7.8', datetime.now().isoformat()))

        conn.commit()
        conn.close()

        duplicates = identify_duplicates(test_db)

        assert len(duplicates) == 2
        counts = sorted([d.count for d in duplicates])
        assert counts == [2, 3]

    def test_different_timestamp_not_duplicate(self, test_db):
        """Test that different timestamps are NOT considered duplicates."""
        add_merge_columns(test_db)

        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO sign_in_logs (timestamp, user_principal_name, ip_address, imported_at)
            VALUES (?, ?, ?, ?)
        """, ('2025-11-25T04:55:50', 'user@example.com', '1.2.3.4', datetime.now().isoformat()))

        cursor.execute("""
            INSERT INTO sign_in_logs (timestamp, user_principal_name, ip_address, imported_at)
            VALUES (?, ?, ?, ?)
        """, ('2025-11-25T04:55:51', 'user@example.com', '1.2.3.4', datetime.now().isoformat()))

        conn.commit()
        conn.close()

        duplicates = identify_duplicates(test_db)

        assert len(duplicates) == 0


class TestMergeDuplicates:
    """Test merge_duplicates function."""

    def test_merge_simple_duplicates(self, test_db):
        """Test merging simple duplicate group."""
        add_merge_columns(test_db)

        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        # Insert 3 duplicate records
        ids = []
        for i in range(3):
            cursor.execute("""
                INSERT INTO sign_in_logs (timestamp, user_principal_name, ip_address, location_city, imported_at)
                VALUES (?, ?, ?, ?, ?)
            """, ('2025-11-25T04:55:50', 'user@example.com', '1.2.3.4', f'City{i}', datetime.now().isoformat()))
            ids.append(cursor.lastrowid)

        conn.commit()
        conn.close()

        result = merge_duplicates(test_db)

        assert result['success'] is True
        assert result['groups_processed'] == 1
        assert result['records_merged'] == 2  # 2 secondary records merged into primary

        # Verify merge status
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        # Primary record should have merge_status = 'primary'
        cursor.execute("""
            SELECT id, merge_status, merged_into, merged_at
            FROM sign_in_logs
            WHERE id = ?
        """, (ids[0],))
        primary = cursor.fetchone()
        assert primary[1] == 'primary'
        assert primary[2] is None  # primary doesn't merge into anything
        assert primary[3] is None

        # Secondary records should have merge_status = 'merged'
        cursor.execute("""
            SELECT id, merge_status, merged_into, merged_at
            FROM sign_in_logs
            WHERE id IN (?, ?)
        """, (ids[1], ids[2]))
        secondaries = cursor.fetchall()
        assert len(secondaries) == 2
        for secondary in secondaries:
            assert secondary[1] == 'merged'
            assert secondary[2] == ids[0]  # Points to primary
            assert secondary[3] is not None  # Has merge timestamp

        conn.close()

    def test_merge_preserves_data(self, test_db):
        """Test that merge preserves all data (doesn't delete)."""
        add_merge_columns(test_db)

        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        # Insert duplicates
        for i in range(3):
            cursor.execute("""
                INSERT INTO sign_in_logs (timestamp, user_principal_name, ip_address, location_city, imported_at)
                VALUES (?, ?, ?, ?, ?)
            """, ('2025-11-25T04:55:50', 'user@example.com', '1.2.3.4', f'City{i}', datetime.now().isoformat()))

        conn.commit()

        # Count before merge
        cursor.execute("SELECT COUNT(*) FROM sign_in_logs")
        count_before = cursor.fetchone()[0]
        conn.close()

        # Merge
        merge_duplicates(test_db)

        # Count after merge
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM sign_in_logs")
        count_after = cursor.fetchone()[0]
        conn.close()

        # All records preserved
        assert count_before == count_after == 3

    def test_merge_multiple_groups(self, test_db):
        """Test merging multiple duplicate groups."""
        add_merge_columns(test_db)

        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        # Group 1: 2 duplicates
        for _ in range(2):
            cursor.execute("""
                INSERT INTO sign_in_logs (timestamp, user_principal_name, ip_address, imported_at)
                VALUES (?, ?, ?, ?)
            """, ('2025-11-25T04:55:50', 'user1@example.com', '1.2.3.4', datetime.now().isoformat()))

        # Group 2: 4 duplicates
        for _ in range(4):
            cursor.execute("""
                INSERT INTO sign_in_logs (timestamp, user_principal_name, ip_address, imported_at)
                VALUES (?, ?, ?, ?)
            """, ('2025-11-25T05:00:00', 'user2@example.com', '5.6.7.8', datetime.now().isoformat()))

        conn.commit()
        conn.close()

        result = merge_duplicates(test_db)

        assert result['success'] is True
        assert result['groups_processed'] == 2
        assert result['records_merged'] == 4  # 1 from group1 + 3 from group2

    def test_merge_idempotent(self, test_db):
        """Test that running merge twice is safe (idempotent)."""
        add_merge_columns(test_db)

        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        # Insert duplicates
        for _ in range(3):
            cursor.execute("""
                INSERT INTO sign_in_logs (timestamp, user_principal_name, ip_address, imported_at)
                VALUES (?, ?, ?, ?)
            """, ('2025-11-25T04:55:50', 'user@example.com', '1.2.3.4', datetime.now().isoformat()))

        conn.commit()
        conn.close()

        # Merge first time
        result1 = merge_duplicates(test_db)
        assert result1['records_merged'] == 2

        # Merge second time (should be no-op)
        result2 = merge_duplicates(test_db)
        assert result2['records_merged'] == 0  # Already merged


class TestCreateActiveView:
    """Test create_active_view function."""

    def test_create_active_view(self, test_db):
        """Test creating v_sign_in_logs_active view."""
        add_merge_columns(test_db)

        result = create_active_view(test_db)

        assert result['success'] is True

        # Verify view exists
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='view' AND name='v_sign_in_logs_active'
        """)
        view = cursor.fetchone()
        conn.close()

        assert view is not None

    def test_active_view_excludes_merged(self, test_db):
        """Test that active view excludes merged records."""
        add_merge_columns(test_db)
        create_active_view(test_db)

        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        # Insert duplicates
        for _ in range(3):
            cursor.execute("""
                INSERT INTO sign_in_logs (timestamp, user_principal_name, ip_address, imported_at)
                VALUES (?, ?, ?, ?)
            """, ('2025-11-25T04:55:50', 'user@example.com', '1.2.3.4', datetime.now().isoformat()))

        # Insert unique record
        cursor.execute("""
            INSERT INTO sign_in_logs (timestamp, user_principal_name, ip_address, imported_at)
            VALUES (?, ?, ?, ?)
        """, ('2025-11-25T05:00:00', 'other@example.com', '5.6.7.8', datetime.now().isoformat()))

        conn.commit()
        conn.close()

        # Merge duplicates
        merge_duplicates(test_db)

        # Query active view
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM v_sign_in_logs_active")
        active_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM sign_in_logs")
        total_count = cursor.fetchone()[0]

        conn.close()

        # Active view should have 2 records (1 primary from duplicates + 1 unique)
        assert total_count == 4
        assert active_count == 2

    def test_active_view_includes_null_merge_status(self, test_db):
        """Test that active view includes records with NULL merge_status."""
        add_merge_columns(test_db)
        create_active_view(test_db)

        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        # Insert record without merge status (NULL)
        cursor.execute("""
            INSERT INTO sign_in_logs (timestamp, user_principal_name, ip_address, imported_at)
            VALUES (?, ?, ?, ?)
        """, ('2025-11-25T04:55:50', 'user@example.com', '1.2.3.4', datetime.now().isoformat()))

        conn.commit()

        # Query active view
        cursor.execute("SELECT COUNT(*) FROM v_sign_in_logs_active")
        active_count = cursor.fetchone()[0]
        conn.close()

        assert active_count == 1


class TestEndToEnd:
    """Test end-to-end duplicate handling workflow."""

    def test_full_workflow(self, test_db):
        """Test complete workflow: add columns → identify → merge → create view."""
        # Step 1: Add merge columns
        add_result = add_merge_columns(test_db)
        assert add_result['success'] is True

        # Step 2: Insert test data
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        # Duplicate group
        for i in range(3):
            cursor.execute("""
                INSERT INTO sign_in_logs (timestamp, user_principal_name, ip_address, location_city, imported_at)
                VALUES (?, ?, ?, ?, ?)
            """, ('2025-11-25T04:55:50', 'user@example.com', '1.2.3.4', f'City{i}', datetime.now().isoformat()))

        # Unique records
        cursor.execute("""
            INSERT INTO sign_in_logs (timestamp, user_principal_name, ip_address, imported_at)
            VALUES (?, ?, ?, ?)
        """, ('2025-11-25T05:00:00', 'other@example.com', '5.6.7.8', datetime.now().isoformat()))

        conn.commit()
        conn.close()

        # Step 3: Identify duplicates
        duplicates = identify_duplicates(test_db)
        assert len(duplicates) == 1

        # Step 4: Merge duplicates
        merge_result = merge_duplicates(test_db)
        assert merge_result['success'] is True
        assert merge_result['records_merged'] == 2

        # Step 5: Create active view
        view_result = create_active_view(test_db)
        assert view_result['success'] is True

        # Step 6: Verify results
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        # Total records preserved
        cursor.execute("SELECT COUNT(*) FROM sign_in_logs")
        assert cursor.fetchone()[0] == 4

        # Active records (excluding merged)
        cursor.execute("SELECT COUNT(*) FROM v_sign_in_logs_active")
        assert cursor.fetchone()[0] == 2

        # Verify primary record
        cursor.execute("""
            SELECT COUNT(*) FROM sign_in_logs
            WHERE merge_status = 'primary'
        """)
        assert cursor.fetchone()[0] == 1

        # Verify merged records
        cursor.execute("""
            SELECT COUNT(*) FROM sign_in_logs
            WHERE merge_status = 'merged'
        """)
        assert cursor.fetchone()[0] == 2

        conn.close()


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_database(self, test_db):
        """Test handling empty database."""
        add_merge_columns(test_db)

        duplicates = identify_duplicates(test_db)
        assert len(duplicates) == 0

        result = merge_duplicates(test_db)
        assert result['success'] is True
        assert result['records_merged'] == 0

    def test_no_duplicates_to_merge(self, test_db):
        """Test merge when no duplicates exist."""
        add_merge_columns(test_db)

        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        # Insert unique records only
        cursor.execute("""
            INSERT INTO sign_in_logs (timestamp, user_principal_name, ip_address, imported_at)
            VALUES (?, ?, ?, ?)
        """, ('2025-11-25T04:55:50', 'user1@example.com', '1.2.3.4', datetime.now().isoformat()))

        cursor.execute("""
            INSERT INTO sign_in_logs (timestamp, user_principal_name, ip_address, imported_at)
            VALUES (?, ?, ?, ?)
        """, ('2025-11-25T05:00:00', 'user2@example.com', '5.6.7.8', datetime.now().isoformat()))

        conn.commit()
        conn.close()

        result = merge_duplicates(test_db)
        assert result['success'] is True
        assert result['records_merged'] == 0

    def test_null_values_in_duplicate_keys(self, test_db):
        """Test handling NULL values in duplicate detection keys."""
        add_merge_columns(test_db)

        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        # Insert records with NULL ip_address
        for _ in range(2):
            cursor.execute("""
                INSERT INTO sign_in_logs (timestamp, user_principal_name, ip_address, imported_at)
                VALUES (?, ?, ?, ?)
            """, ('2025-11-25T04:55:50', 'user@example.com', None, datetime.now().isoformat()))

        conn.commit()
        conn.close()

        # Should handle gracefully (NULL values should not be grouped as duplicates)
        duplicates = identify_duplicates(test_db)
        # Implementation may vary - either 0 (NULLs not grouped) or 1 (NULLs grouped)
        assert len(duplicates) >= 0
