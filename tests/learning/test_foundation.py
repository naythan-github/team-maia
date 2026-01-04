#!/usr/bin/env python3
"""
Tests for Phase 1: Foundation (TDD)

Tests directory structure creation and database schema initialization.
"""

import pytest
import tempfile
import sqlite3
from pathlib import Path
from unittest.mock import patch


class TestLearningPackageInit:
    """Tests for claude/tools/learning/__init__.py"""

    def test_get_learning_root_creates_directories(self):
        """Test that get_learning_root creates all required directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning import get_learning_root

                root = get_learning_root()

                # Verify root is ~/.maia
                assert root == fake_home / ".maia"

                # Verify all required directories exist
                assert (root / "outputs").exists()
                assert (root / "outputs").is_dir()
                assert (root / "memory" / "summaries").exists()
                assert (root / "memory" / "summaries").is_dir()
                assert (root / "learning").exists()
                assert (root / "learning").is_dir()

    def test_get_learning_root_idempotent(self):
        """Test that calling get_learning_root multiple times is safe."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning import get_learning_root

                # Call multiple times
                root1 = get_learning_root()
                root2 = get_learning_root()

                # Should return same path
                assert root1 == root2

                # Directories should still exist
                assert (root1 / "outputs").exists()

    def test_learning_root_constant_available(self):
        """Test that LEARNING_ROOT constant is exported."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                # Force reimport to get fresh module
                import importlib
                import claude.tools.learning as learning_module
                importlib.reload(learning_module)

                from claude.tools.learning import LEARNING_ROOT

                assert LEARNING_ROOT is not None
                assert isinstance(LEARNING_ROOT, Path)


class TestDatabaseSchema:
    """Tests for claude/tools/learning/schema.py"""

    def test_memory_schema_creates_sessions_table(self):
        """Test that Memory schema creates sessions table."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "memory.db"

            from claude.tools.learning.schema import init_memory_db

            conn = init_memory_db(db_path)

            # Verify sessions table exists
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'"
            )
            assert cursor.fetchone() is not None

            # Verify required columns
            cursor = conn.execute("PRAGMA table_info(sessions)")
            columns = {row[1] for row in cursor.fetchall()}

            required_columns = {
                'id', 'context_id', 'started_at', 'ended_at', 'initial_query',
                'agent_used', 'domain', 'status', 'summary_text', 'key_decisions',
                'tools_used', 'files_touched', 'verify_success', 'verify_confidence',
                'verify_metrics', 'learn_insights', 'patterns_extracted'
            }

            assert required_columns.issubset(columns), f"Missing columns: {required_columns - columns}"

            conn.close()

    def test_memory_schema_creates_fts_table(self):
        """Test that Memory schema creates FTS virtual table."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "memory.db"

            from claude.tools.learning.schema import init_memory_db

            conn = init_memory_db(db_path)

            # Verify FTS table exists
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='sessions_fts'"
            )
            assert cursor.fetchone() is not None

            conn.close()

    def test_memory_schema_creates_indexes(self):
        """Test that Memory schema creates performance indexes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "memory.db"

            from claude.tools.learning.schema import init_memory_db

            conn = init_memory_db(db_path)

            # Verify indexes exist
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index'"
            )
            indexes = {row[0] for row in cursor.fetchall()}

            assert 'idx_sessions_date' in indexes
            assert 'idx_sessions_domain' in indexes

            conn.close()

    def test_learning_schema_creates_patterns_table(self):
        """Test that learning schema creates patterns table."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "learning.db"

            from claude.tools.learning.schema import init_learning_db

            conn = init_learning_db(db_path)

            # Verify patterns table exists
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='patterns'"
            )
            assert cursor.fetchone() is not None

            # Verify pattern_type constraint
            cursor = conn.execute("PRAGMA table_info(patterns)")
            columns = {row[1] for row in cursor.fetchall()}

            required_columns = {
                'id', 'pattern_type', 'domain', 'description', 'pattern_data',
                'confidence', 'occurrence_count', 'first_seen', 'last_seen',
                'decayed_confidence'
            }

            assert required_columns.issubset(columns)

            conn.close()

    def test_learning_schema_creates_preferences_table(self):
        """Test that learning schema creates preferences table."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "learning.db"

            from claude.tools.learning.schema import init_learning_db

            conn = init_learning_db(db_path)

            # Verify preferences table exists
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='preferences'"
            )
            assert cursor.fetchone() is not None

            # Verify unique constraint on (category, key)
            cursor = conn.execute("PRAGMA index_list(preferences)")
            indexes = cursor.fetchall()

            # Should have unique index
            unique_indexes = [idx for idx in indexes if idx[2] == 1]  # idx[2] is unique flag
            assert len(unique_indexes) >= 1

            conn.close()

    def test_learning_schema_creates_metrics_table(self):
        """Test that learning schema creates metrics table."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "learning.db"

            from claude.tools.learning.schema import init_learning_db

            conn = init_learning_db(db_path)

            # Verify metrics table exists
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='metrics'"
            )
            assert cursor.fetchone() is not None

            conn.close()

    def test_database_init_idempotent(self):
        """Test that initializing database multiple times is safe."""
        with tempfile.TemporaryDirectory() as tmpdir:
            kai_path = Path(tmpdir) / "memory.db"
            learning_path = Path(tmpdir) / "learning.db"

            from claude.tools.learning.schema import init_memory_db, init_learning_db

            # Initialize twice
            conn1 = init_memory_db(kai_path)
            conn1.close()
            conn2 = init_memory_db(kai_path)

            conn3 = init_learning_db(learning_path)
            conn3.close()
            conn4 = init_learning_db(learning_path)

            # Should not raise errors
            assert conn2 is not None
            assert conn4 is not None

            conn2.close()
            conn4.close()

    def test_memory_schema_insert_and_query(self):
        """Test that we can insert and query session data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "memory.db"

            from claude.tools.learning.schema import init_memory_db

            conn = init_memory_db(db_path)
            conn.row_factory = sqlite3.Row  # Use Row for named access

            # Insert test data
            conn.execute("""
                INSERT INTO sessions (id, context_id, started_at, initial_query, status)
                VALUES (?, ?, ?, ?, ?)
            """, ("test_001", "ctx_123", "2026-01-04T12:00:00", "Fix the bug", "active"))
            conn.commit()

            # Query it back
            cursor = conn.execute("SELECT * FROM sessions WHERE id = ?", ("test_001",))
            row = cursor.fetchone()

            assert row is not None
            assert row["id"] == "test_001"
            assert row["initial_query"] == "Fix the bug"
            assert row["status"] == "active"

            conn.close()

    def test_learning_schema_pattern_type_constraint(self):
        """Test that pattern_type CHECK constraint works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "learning.db"

            from claude.tools.learning.schema import init_learning_db

            conn = init_learning_db(db_path)

            # Valid pattern type should work
            conn.execute("""
                INSERT INTO patterns (id, pattern_type, description)
                VALUES (?, ?, ?)
            """, ("p1", "workflow", "Test pattern"))
            conn.commit()

            # Invalid pattern type should fail
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute("""
                    INSERT INTO patterns (id, pattern_type, description)
                    VALUES (?, ?, ?)
                """, ("p2", "invalid_type", "Bad pattern"))
                conn.commit()

            conn.close()


class TestDirectoryStructureValidation:
    """Integration tests for directory structure."""

    def test_full_directory_structure(self):
        """Test complete directory structure matches spec."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning import get_learning_root

                root = get_learning_root()

                # Verify structure matches Phase 1.1 spec
                expected_dirs = [
                    root / "outputs",
                    root / "memory" / "summaries",
                    root / "learning",
                ]

                for d in expected_dirs:
                    assert d.exists(), f"Directory {d} should exist"
                    assert d.is_dir(), f"{d} should be a directory"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
