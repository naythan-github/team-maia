#!/usr/bin/env python3
"""
TDD Tests for Log Coverage Summary (M365 IR Data Enhancements - Requirement 1)

Provides instant visibility into forensic coverage gaps during IR triage.
Prevents analysts from missing that different log types have different
retention windows (sign-in ~60d, UAL ~32d, mailbox ~35d).

Run: pytest claude/tools/m365_ir/tests/test_log_coverage_summary.py -v

Author: Maia System (SRE Principal Engineer Agent)
Created: 2026-01-08 (PIR-FYNA-2025-12-08 lessons learned)
"""

import pytest
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add Maia root to path
MAIA_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

from claude.tools.m365_ir.log_database import IRLogDatabase


class TestLogCoverageSummary:
    """Tests for log_coverage_summary table and population logic."""

    @pytest.fixture
    def temp_db(self, tmp_path):
        """Create temporary database with schema."""
        db = IRLogDatabase(case_id="TEST-COVERAGE", base_path=str(tmp_path))
        db.create()
        return db

    def _insert_sign_in_logs(
        self,
        db: IRLogDatabase,
        start_date: str = None,
        end_date: str = None,
        count: int = 10
    ):
        """Helper to insert sign-in log records with known date range."""
        conn = db.connect()
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        # Parse dates or use defaults
        if start_date:
            start = datetime.fromisoformat(start_date)
        else:
            start = datetime.now() - timedelta(days=60)

        if end_date:
            end = datetime.fromisoformat(end_date)
        else:
            end = datetime.now()

        # Distribute records evenly across date range
        delta = (end - start) / max(count - 1, 1)
        for i in range(count):
            ts = (start + delta * i).isoformat()
            cursor.execute("""
                INSERT INTO sign_in_logs (
                    timestamp, user_principal_name, ip_address, imported_at
                ) VALUES (?, ?, ?, ?)
            """, (ts, f"user{i}@test.com", f"1.1.1.{i}", now))

        conn.commit()
        conn.close()

    def _insert_ual_logs(
        self,
        db: IRLogDatabase,
        start_date: str = None,
        end_date: str = None,
        count: int = 10
    ):
        """Helper to insert unified audit log records."""
        conn = db.connect()
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        if start_date:
            start = datetime.fromisoformat(start_date)
        else:
            start = datetime.now() - timedelta(days=32)

        if end_date:
            end = datetime.fromisoformat(end_date)
        else:
            end = datetime.now()

        delta = (end - start) / max(count - 1, 1)
        for i in range(count):
            ts = (start + delta * i).isoformat()
            cursor.execute("""
                INSERT INTO unified_audit_log (
                    timestamp, operation, imported_at
                ) VALUES (?, ?, ?)
            """, (ts, f"Operation{i}", now))

        conn.commit()
        conn.close()

    def _query_coverage(self, db: IRLogDatabase, log_type: str) -> dict:
        """Query coverage summary for a log type."""
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM log_coverage_summary WHERE log_type = ?
        """, (log_type,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
        return None

    def _count_coverage_rows(self, db: IRLogDatabase, log_type: str) -> int:
        """Count rows for a specific log type."""
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM log_coverage_summary WHERE log_type = ?
        """, (log_type,))
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def test_creates_table_if_not_exists(self, temp_db):
        """Table should be created on first run."""
        # Import the function we'll create
        from claude.tools.m365_ir.log_coverage import update_log_coverage_summary

        update_log_coverage_summary(temp_db.db_path)

        conn = temp_db.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='log_coverage_summary'
        """)
        result = cursor.fetchone()
        conn.close()
        assert result is not None

    def test_calculates_coverage_days_correctly(self, temp_db):
        """Coverage days = latest - earliest timestamps."""
        from claude.tools.m365_ir.log_coverage import update_log_coverage_summary

        # Insert sign_in_logs with known 59-day range
        self._insert_sign_in_logs(
            temp_db,
            start_date='2025-11-10T00:00:00',
            end_date='2026-01-08T00:00:00',
            count=10
        )
        update_log_coverage_summary(temp_db.db_path)

        result = self._query_coverage(temp_db, 'sign_in')
        assert result is not None
        assert result['coverage_days'] == 59  # Nov 10 to Jan 8

    def test_detects_gap_when_below_threshold(self, temp_db):
        """Gap detected when coverage < 80% of expected."""
        from claude.tools.m365_ir.log_coverage import update_log_coverage_summary

        # Insert UAL with only 32 days coverage (< 80% of 90 expected)
        self._insert_ual_logs(
            temp_db,
            start_date='2025-12-07T00:00:00',
            end_date='2026-01-08T00:00:00',
            count=10
        )
        update_log_coverage_summary(temp_db.db_path)

        result = self._query_coverage(temp_db, 'unified_audit_log')
        assert result is not None
        assert result['gap_detected'] == 1  # SQLite stores bool as int
        assert result['coverage_days'] == 32
        assert '32' in result['gap_description']

    def test_no_gap_when_coverage_sufficient(self, temp_db):
        """No gap when coverage >= 80% of expected."""
        from claude.tools.m365_ir.log_coverage import update_log_coverage_summary

        # Insert sign_in_logs with 90 days coverage (>= 80% of 90)
        self._insert_sign_in_logs(
            temp_db,
            start_date='2025-10-10T00:00:00',
            end_date='2026-01-08T00:00:00',
            count=20
        )
        update_log_coverage_summary(temp_db.db_path)

        result = self._query_coverage(temp_db, 'sign_in')
        assert result is not None
        assert result['gap_detected'] == 0  # No gap

    def test_handles_empty_table(self, temp_db):
        """Empty tables should show 0 records, no crash."""
        from claude.tools.m365_ir.log_coverage import update_log_coverage_summary

        # Don't insert any records - table is empty
        update_log_coverage_summary(temp_db.db_path)

        result = self._query_coverage(temp_db, 'sign_in')
        assert result is not None
        assert result['total_records'] == 0
        assert result['earliest_timestamp'] is None or result['earliest_timestamp'] == ''

    def test_upserts_on_reimport(self, temp_db):
        """Re-running should update, not duplicate."""
        from claude.tools.m365_ir.log_coverage import update_log_coverage_summary

        # First import
        self._insert_sign_in_logs(temp_db, count=100)
        update_log_coverage_summary(temp_db.db_path)

        # Second import with more records
        self._insert_sign_in_logs(temp_db, count=50)
        update_log_coverage_summary(temp_db.db_path)

        count = self._count_coverage_rows(temp_db, 'sign_in')
        assert count == 1  # Only one row, not duplicated

    def test_returns_summary_dict(self, temp_db):
        """Function should return summary dict."""
        from claude.tools.m365_ir.log_coverage import update_log_coverage_summary

        self._insert_sign_in_logs(temp_db, count=10)
        result = update_log_coverage_summary(temp_db.db_path)

        assert isinstance(result, dict)
        assert 'tables_scanned' in result
        assert 'gaps_detected' in result
        assert 'coverage_report' in result

    def test_scans_all_known_log_types(self, temp_db):
        """Should scan all known log table types."""
        from claude.tools.m365_ir.log_coverage import update_log_coverage_summary

        # Insert data in multiple tables
        self._insert_sign_in_logs(temp_db, count=5)
        self._insert_ual_logs(temp_db, count=5)

        result = update_log_coverage_summary(temp_db.db_path)

        # Should have scanned multiple tables
        assert result['tables_scanned'] >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
