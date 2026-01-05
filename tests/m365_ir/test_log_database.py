#!/usr/bin/env python3
"""
TDD Tests for IRLogDatabase - Per-investigation SQLite storage

Phase: P3 - Test Design (RED)
Requirements: IR_LOG_DATABASE_REQUIREMENTS.md

Tests written BEFORE implementation per TDD protocol.
"""

import pytest
import sqlite3
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Import will fail until implementation exists (expected RED state)
try:
    from claude.tools.m365_ir.log_database import IRLogDatabase
except ImportError:
    IRLogDatabase = None


@pytest.fixture
def temp_dir():
    """Create temporary directory for test databases."""
    d = tempfile.mkdtemp()
    yield Path(d)
    shutil.rmtree(d)


@pytest.fixture
def db(temp_dir):
    """Create IRLogDatabase instance for testing."""
    if IRLogDatabase is None:
        pytest.skip("IRLogDatabase not yet implemented")
    return IRLogDatabase(case_id="PIR-TEST-2025-001", base_path=str(temp_dir))


class TestIRLogDatabaseCreation:
    """Tests for database creation and schema."""

    def test_create_returns_path(self, db, temp_dir):
        """create() should return the database file path."""
        db_path = db.create()
        assert db_path is not None
        assert isinstance(db_path, Path)
        assert db_path.exists()

    def test_create_makes_correct_directory_structure(self, db, temp_dir):
        """create() should make case_id directory with _logs.db file."""
        db_path = db.create()
        assert db_path.parent.name == "PIR-TEST-2025-001"
        assert db_path.name == "PIR-TEST-2025-001_logs.db"

    def test_create_initializes_all_tables(self, db):
        """create() should initialize all required tables."""
        db.create()
        conn = db.connect()
        cursor = conn.cursor()

        # Check all required tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]

        expected_tables = [
            'import_metadata',
            'inbox_rules',
            'mailbox_audit_log',
            'oauth_consents',
            'sign_in_logs',
            'unified_audit_log',
        ]

        for table in expected_tables:
            assert table in tables, f"Missing table: {table}"

        conn.close()

    def test_create_adds_indexes(self, db):
        """create() should add performance indexes."""
        db.create()
        conn = db.connect()
        cursor = conn.cursor()

        # Check indexes exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [row[0] for row in cursor.fetchall()]

        # Should have indexes on key columns
        assert any('timestamp' in idx for idx in indexes)
        assert any('user' in idx or 'upn' in idx for idx in indexes)
        assert any('ip' in idx for idx in indexes)

        conn.close()

    def test_create_is_idempotent(self, db):
        """create() called twice should not error or duplicate."""
        path1 = db.create()
        path2 = db.create()
        assert path1 == path2


class TestIRLogDatabaseConnection:
    """Tests for database connection handling."""

    def test_connect_returns_connection(self, db):
        """connect() should return sqlite3 Connection."""
        db.create()
        conn = db.connect()
        assert isinstance(conn, sqlite3.Connection)
        conn.close()

    def test_connect_without_create_raises(self, temp_dir):
        """connect() without create() should raise FileNotFoundError."""
        if IRLogDatabase is None:
            pytest.skip("IRLogDatabase not yet implemented")

        db = IRLogDatabase(case_id="PIR-NONEXISTENT-001", base_path=str(temp_dir))
        with pytest.raises(FileNotFoundError):
            db.connect()

    def test_connect_with_row_factory(self, db):
        """connect() should use Row factory for dict-like access."""
        db.create()
        conn = db.connect()

        # Insert test data
        conn.execute("""
            INSERT INTO sign_in_logs (timestamp, user_principal_name, imported_at)
            VALUES (?, ?, ?)
        """, (datetime.now().isoformat(), "test@example.com", datetime.now().isoformat()))
        conn.commit()

        # Query should return dict-like rows
        cursor = conn.execute("SELECT * FROM sign_in_logs LIMIT 1")
        row = cursor.fetchone()

        # Should be able to access by column name
        assert row['user_principal_name'] == "test@example.com"

        conn.close()


class TestIRLogDatabaseStats:
    """Tests for database statistics."""

    def test_get_stats_empty_database(self, db):
        """get_stats() on empty DB should return all zeros."""
        db.create()
        stats = db.get_stats()

        assert isinstance(stats, dict)
        assert stats.get('sign_in_logs', 0) == 0
        assert stats.get('unified_audit_log', 0) == 0
        assert stats.get('mailbox_audit_log', 0) == 0

    def test_get_stats_with_data(self, db):
        """get_stats() should return correct counts."""
        db.create()
        conn = db.connect()

        # Insert test data
        now = datetime.now().isoformat()
        for i in range(5):
            conn.execute("""
                INSERT INTO sign_in_logs (timestamp, user_principal_name, imported_at)
                VALUES (?, ?, ?)
            """, (now, f"user{i}@example.com", now))

        for i in range(3):
            conn.execute("""
                INSERT INTO unified_audit_log (timestamp, operation, imported_at)
                VALUES (?, ?, ?)
            """, (now, f"Operation{i}", now))

        conn.commit()
        conn.close()

        stats = db.get_stats()
        assert stats['sign_in_logs'] == 5
        assert stats['unified_audit_log'] == 3
        assert stats['mailbox_audit_log'] == 0


class TestIRLogDatabaseVacuum:
    """Tests for database optimization."""

    def test_vacuum_runs_without_error(self, db):
        """vacuum() should complete without error."""
        db.create()
        db.vacuum()  # Should not raise

    def test_vacuum_after_bulk_insert(self, db):
        """vacuum() should optimize after bulk operations."""
        db.create()
        conn = db.connect()

        # Bulk insert
        now = datetime.now().isoformat()
        for i in range(100):
            conn.execute("""
                INSERT INTO sign_in_logs (timestamp, user_principal_name, imported_at)
                VALUES (?, ?, ?)
            """, (now, f"user{i}@example.com", now))
        conn.commit()
        conn.close()

        # Vacuum should run
        db.vacuum()


class TestIRLogDatabaseSchema:
    """Tests for schema correctness."""

    def test_sign_in_logs_schema(self, db):
        """sign_in_logs table should have all required columns."""
        db.create()
        conn = db.connect()
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(sign_in_logs)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}  # name: type

        required = [
            'timestamp', 'user_principal_name', 'ip_address',
            'location_city', 'location_country', 'client_app',
            'status_error_code', 'raw_record', 'imported_at'
        ]

        for col in required:
            assert col in columns, f"Missing column: {col}"

        conn.close()

    def test_unified_audit_log_schema(self, db):
        """unified_audit_log table should have all required columns."""
        db.create()
        conn = db.connect()
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(unified_audit_log)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        required = [
            'timestamp', 'user_id', 'operation', 'workload',
            'client_ip', 'audit_data', 'imported_at'
        ]

        for col in required:
            assert col in columns, f"Missing column: {col}"

        conn.close()

    def test_import_metadata_schema(self, db):
        """import_metadata table should track imports."""
        db.create()
        conn = db.connect()
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(import_metadata)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        required = [
            'source_file', 'source_hash', 'log_type',
            'records_imported', 'records_failed', 'import_started'
        ]

        for col in required:
            assert col in columns, f"Missing column: {col}"

        conn.close()


class TestIRLogDatabaseCaseIsolation:
    """Tests for case isolation (chain of custody)."""

    def test_different_cases_different_dbs(self, temp_dir):
        """Different case_ids should create separate databases."""
        if IRLogDatabase is None:
            pytest.skip("IRLogDatabase not yet implemented")

        db1 = IRLogDatabase(case_id="PIR-CASE-001", base_path=str(temp_dir))
        db2 = IRLogDatabase(case_id="PIR-CASE-002", base_path=str(temp_dir))

        path1 = db1.create()
        path2 = db2.create()

        assert path1 != path2
        assert path1.parent.name == "PIR-CASE-001"
        assert path2.parent.name == "PIR-CASE-002"

    def test_case_data_isolated(self, temp_dir):
        """Data in one case should not appear in another."""
        if IRLogDatabase is None:
            pytest.skip("IRLogDatabase not yet implemented")

        db1 = IRLogDatabase(case_id="PIR-CASE-001", base_path=str(temp_dir))
        db2 = IRLogDatabase(case_id="PIR-CASE-002", base_path=str(temp_dir))

        db1.create()
        db2.create()

        # Insert into case 1
        conn1 = db1.connect()
        now = datetime.now().isoformat()
        conn1.execute("""
            INSERT INTO sign_in_logs (timestamp, user_principal_name, imported_at)
            VALUES (?, ?, ?)
        """, (now, "case1@example.com", now))
        conn1.commit()
        conn1.close()

        # Case 2 should be empty
        conn2 = db2.connect()
        cursor = conn2.execute("SELECT COUNT(*) FROM sign_in_logs")
        count = cursor.fetchone()[0]
        conn2.close()

        assert count == 0


class TestIRLogDatabaseProperties:
    """Tests for database properties."""

    def test_case_id_property(self, db):
        """Should expose case_id as property."""
        assert db.case_id == "PIR-TEST-2025-001"

    def test_db_path_property(self, db):
        """Should expose db_path after creation."""
        db.create()
        assert db.db_path is not None
        assert db.db_path.exists()

    def test_db_path_before_connect(self, temp_dir):
        """db_path should return expected path even before connect().

        Bug fix: stats command showed 'Database: None' because db_path
        was only set after connect() was called.
        """
        # Create a database
        db1 = IRLogDatabase(case_id="PIR-PATH-TEST-001", base_path=str(temp_dir))
        db1.create()

        # Now create a new instance that hasn't called connect()
        db2 = IRLogDatabase(case_id="PIR-PATH-TEST-001", base_path=str(temp_dir))

        # db_path should still return the correct path
        assert db2.db_path is not None
        expected = temp_dir / "PIR-PATH-TEST-001" / "PIR-PATH-TEST-001_logs.db"
        assert db2.db_path == expected

    def test_exists_property(self, db):
        """exists property should indicate DB state."""
        assert not db.exists
        db.create()
        assert db.exists
