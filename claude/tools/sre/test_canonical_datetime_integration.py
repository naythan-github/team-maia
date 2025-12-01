#!/usr/bin/env python3
"""
Integration Tests for Canonical DateTime System
Phase 216: Date/Time Reliability Enhancement

Purpose:
    Validate real-world usage scenarios with actual databases,
    document generation, and cross-system consistency.

Test Coverage:
    - SQLite database timestamp storage/retrieval
    - SYSTEM_STATE.md phase date generation
    - Cross-system consistency (Python → DB → validation)
    - Timezone handling across operations
    - Document metadata generation

Author: SRE Principal Engineer Agent (Maia)
Date: 2025-12-01
"""

import pytest
import sqlite3
import tempfile
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from claude.tools.sre.canonical_datetime import CanonicalDateTime


class TestDatabaseIntegration:
    """Integration tests with SQLite database operations"""

    def test_database_timestamp_storage_and_retrieval(self):
        """
        Real-world scenario: Store timestamp in DB, retrieve it, validate

        This is the most critical integration test - validates that
        timestamps can be stored and retrieved without corruption.
        """
        # Create temp database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name

        try:
            # Create table with timestamp columns (typical schema)
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE test_phases (
                    id INTEGER PRIMARY KEY,
                    phase_number INTEGER,
                    title TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)

            # Generate timestamps using CanonicalDateTime
            created = CanonicalDateTime.now_iso_utc()
            updated = CanonicalDateTime.now_iso_utc()

            # Insert into database
            cursor.execute("""
                INSERT INTO test_phases (phase_number, title, created_at, updated_at)
                VALUES (?, ?, ?, ?)
            """, (216, "Test Phase", created, updated))
            conn.commit()

            # Retrieve from database
            cursor.execute("SELECT created_at, updated_at FROM test_phases WHERE phase_number = 216")
            row = cursor.fetchone()
            retrieved_created, retrieved_updated = row

            # Validate retrieved timestamps
            assert retrieved_created == created, "Timestamp corrupted during storage/retrieval"
            assert retrieved_updated == updated, "Timestamp corrupted during storage/retrieval"

            # Validate timestamps can be validated after retrieval
            assert CanonicalDateTime.validate_timestamp(retrieved_created) is True
            assert CanonicalDateTime.validate_timestamp(retrieved_updated) is True

            # Verify they're valid ISO format with UTC timezone
            assert '+00:00' in retrieved_created or retrieved_created.endswith('Z')
            assert '+00:00' in retrieved_updated or retrieved_updated.endswith('Z')

            conn.close()

        finally:
            # Cleanup
            Path(db_path).unlink(missing_ok=True)

    def test_database_with_local_and_utc_timestamps(self):
        """
        Test storing both local (AWST) and UTC timestamps

        Validates that we can correctly handle timezone-aware operations
        when some timestamps are local and some are UTC.
        """
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE test_events (
                    id INTEGER PRIMARY KEY,
                    event_name TEXT,
                    local_time TEXT,
                    utc_time TEXT
                )
            """)

            # Generate both local and UTC timestamps
            local_ts = CanonicalDateTime.now_iso()      # AWST +08:00
            utc_ts = CanonicalDateTime.now_iso_utc()    # UTC +00:00

            # Store both
            cursor.execute("""
                INSERT INTO test_events (event_name, local_time, utc_time)
                VALUES (?, ?, ?)
            """, ("Test Event", local_ts, utc_ts))
            conn.commit()

            # Retrieve and validate
            cursor.execute("SELECT local_time, utc_time FROM test_events")
            local_retrieved, utc_retrieved = cursor.fetchone()

            # Both should be valid
            assert CanonicalDateTime.validate_timestamp(local_retrieved) is True
            assert CanonicalDateTime.validate_timestamp(utc_retrieved) is True

            # Timezone should be preserved
            assert '+08:00' in local_retrieved, "AWST timezone lost"
            assert '+00:00' in utc_retrieved or utc_retrieved.endswith('Z'), "UTC timezone lost"

            # Parse both timestamps
            local_dt = datetime.fromisoformat(local_retrieved)
            utc_dt = datetime.fromisoformat(utc_retrieved.replace('Z', '+00:00'))

            # Verify they represent approximately the same moment
            # (accounting for microsecond differences from generation timing)
            time_diff = abs((local_dt - utc_dt.astimezone(local_dt.tzinfo)).total_seconds())
            assert time_diff < 1.0, f"Timestamps represent different moments (diff: {time_diff}s)"

            conn.close()

        finally:
            Path(db_path).unlink(missing_ok=True)


class TestDocumentGeneration:
    """Integration tests for document metadata generation"""

    def test_phase_entry_date_generation(self):
        """
        Simulate SYSTEM_STATE.md phase entry generation

        Validates the exact use case that prompted this enhancement:
        generating phase dates for SYSTEM_STATE.md without manual typos.
        """
        # Generate phase entry metadata (how SYSTEM_STATE.md is created)
        phase_date = CanonicalDateTime.today_iso()
        phase_timestamp = CanonicalDateTime.now_iso()

        # Validate format matches SYSTEM_STATE.md convention
        assert len(phase_date) == 10, "Date should be YYYY-MM-DD (10 chars)"
        assert phase_date.count('-') == 2, "Date should have 2 dashes"

        # Should be parseable
        datetime.strptime(phase_date, '%Y-%m-%d')

        # Timestamp should include timezone
        assert '+' in phase_timestamp or phase_timestamp.endswith('Z')

        # Validate both
        assert CanonicalDateTime.validate_timestamp(phase_date) is True
        assert CanonicalDateTime.validate_timestamp(phase_timestamp) is True

    def test_document_prepared_date(self):
        """
        Simulate "Date Prepared: YYYY-MM-DD" in documents

        Validates interview questions, reports, and other document
        generation scenarios.
        """
        # Generate "Date Prepared" field
        date_prepared = CanonicalDateTime.today_iso()

        # Should match expected format
        year, month, day = date_prepared.split('-')
        assert len(year) == 4, "Year should be 4 digits"
        assert len(month) == 2, "Month should be 2 digits"
        assert len(day) == 2, "Day should be 2 digits"

        # Should be current date
        current_date = datetime.now().strftime('%Y-%m-%d')
        assert date_prepared == current_date, "Should match system date"

        # Should validate
        assert CanonicalDateTime.validate_timestamp(date_prepared) is True


class TestCrossSystemConsistency:
    """Test consistency across Python, system, and database"""

    def test_python_system_database_consistency(self):
        """
        End-to-end test: Python generates → DB stores → retrieves → validates

        This validates the entire chain to ensure no corruption anywhere.
        """
        # Step 1: Generate in Python
        python_date = CanonicalDateTime.today_iso()
        python_timestamp = CanonicalDateTime.now_iso_utc()

        # Step 2: Verify against system
        verification = CanonicalDateTime.verify()
        assert verification['verified'] is True, "Python doesn't match system time"

        # Step 3: Store in database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE test_consistency (
                    date TEXT,
                    timestamp TEXT
                )
            """)
            cursor.execute(
                "INSERT INTO test_consistency (date, timestamp) VALUES (?, ?)",
                (python_date, python_timestamp)
            )
            conn.commit()

            # Step 4: Retrieve from database
            cursor.execute("SELECT date, timestamp FROM test_consistency")
            db_date, db_timestamp = cursor.fetchone()

            # Step 5: Validate consistency
            assert db_date == python_date, "Date corrupted in DB round-trip"
            assert db_timestamp == python_timestamp, "Timestamp corrupted in DB round-trip"

            # Step 6: Validate retrieved data
            assert CanonicalDateTime.validate_timestamp(db_date) is True
            assert CanonicalDateTime.validate_timestamp(db_timestamp) is True

            conn.close()

        finally:
            Path(db_path).unlink(missing_ok=True)


class TestRelativeTimeWithDatabase:
    """Test relative time calculations in database context"""

    def test_days_ago_query_scenario(self):
        """
        Real-world scenario: Query records from last 7 days

        Validates "get phases from last week" type queries.
        """
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE test_records (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    created_date TEXT
                )
            """)

            # Insert records from today, 3 days ago, 7 days ago, 10 days ago
            today = CanonicalDateTime.today_iso()
            three_days_ago = CanonicalDateTime.days_ago(3).strftime('%Y-%m-%d')
            seven_days_ago = CanonicalDateTime.days_ago(7).strftime('%Y-%m-%d')
            ten_days_ago = CanonicalDateTime.days_ago(10).strftime('%Y-%m-%d')

            cursor.execute("INSERT INTO test_records (name, created_date) VALUES (?, ?)", ("Today", today))
            cursor.execute("INSERT INTO test_records (name, created_date) VALUES (?, ?)", ("3 days", three_days_ago))
            cursor.execute("INSERT INTO test_records (name, created_date) VALUES (?, ?)", ("7 days", seven_days_ago))
            cursor.execute("INSERT INTO test_records (name, created_date) VALUES (?, ?)", ("10 days", ten_days_ago))
            conn.commit()

            # Query: Get records from last 7 days
            cursor.execute("""
                SELECT name FROM test_records
                WHERE created_date >= ?
                ORDER BY created_date DESC
            """, (seven_days_ago,))

            results = [row[0] for row in cursor.fetchall()]

            # Should include today, 3 days, 7 days (but NOT 10 days)
            assert "Today" in results
            assert "3 days" in results
            assert "7 days" in results
            assert "10 days" not in results, "Should exclude records older than 7 days"

            conn.close()

        finally:
            Path(db_path).unlink(missing_ok=True)


class TestTimezoneConsistency:
    """Test timezone handling across operations"""

    def test_utc_storage_local_display_pattern(self):
        """
        Common pattern: Store UTC in DB, display local to user

        This is the recommended pattern for multi-timezone apps.
        """
        # Store in UTC (database)
        utc_stored = CanonicalDateTime.now_iso_utc()

        # Display in local (user interface)
        local_displayed = CanonicalDateTime.now_iso()

        # Both should be valid
        assert CanonicalDateTime.validate_timestamp(utc_stored) is True
        assert CanonicalDateTime.validate_timestamp(local_displayed) is True

        # Parse both
        utc_dt = datetime.fromisoformat(utc_stored.replace('Z', '+00:00'))
        local_dt = datetime.fromisoformat(local_displayed)

        # Should represent approximately the same moment
        # (accounting for microsecond timing differences)
        time_diff = abs((utc_dt.astimezone(local_dt.tzinfo) - local_dt).total_seconds())
        assert time_diff < 1.0, f"UTC and local represent different moments (diff: {time_diff}s)"


class TestErrorPrevention:
    """Integration tests for error prevention (the original problem)"""

    def test_prevents_manual_date_typos_in_database(self):
        """
        Validate that using CanonicalDateTime prevents the exact
        error that prompted this enhancement: wrong dates in DB.
        """
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE test_phases (
                    phase_number INTEGER,
                    date_correct TEXT,
                    date_manual TEXT
                )
            """)

            # Correct way: Using CanonicalDateTime
            correct_date = CanonicalDateTime.today_iso()

            # Wrong way: Manual entry (simulating typo - month 13)
            manual_date = "2025-13-01"  # Invalid!

            # Store correct date
            cursor.execute(
                "INSERT INTO test_phases (phase_number, date_correct) VALUES (?, ?)",
                (216, correct_date)
            )
            conn.commit()

            # Attempt to validate manual date (should fail)
            with pytest.raises(ValueError, match="Invalid month"):
                CanonicalDateTime.validate_timestamp(manual_date)

            # Correct date should validate
            assert CanonicalDateTime.validate_timestamp(correct_date) is True

            # Retrieve and validate correct date still works
            cursor.execute("SELECT date_correct FROM test_phases WHERE phase_number = 216")
            retrieved = cursor.fetchone()[0]
            assert CanonicalDateTime.validate_timestamp(retrieved) is True

            conn.close()

        finally:
            Path(db_path).unlink(missing_ok=True)


if __name__ == "__main__":
    """Run integration tests with pytest"""
    print("=" * 70)
    print("CANONICAL DATETIME - INTEGRATION TESTS")
    print("=" * 70)
    print("\nTesting real-world scenarios:")
    print("  - Database storage/retrieval")
    print("  - Document generation")
    print("  - Cross-system consistency")
    print("  - Timezone handling")
    print("  - Error prevention")
    print("\n" + "=" * 70 + "\n")

    pytest.main([__file__, "-v", "--tb=short", "-s"])
