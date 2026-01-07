#!/usr/bin/env python3
"""
TDD Tests for Learning Archive Infrastructure
Phase 240: Fix missing archive infrastructure causing silent capture failures

Tests verify:
1. Archive directory exists
2. conversation_archive.db has correct schema
3. learning.db has correct tables (patterns, preferences, metrics)
4. Monitor can trigger capture without database errors
"""

import pytest
import sqlite3
from pathlib import Path


class TestArchiveInfrastructure:
    """Test archive infrastructure is properly initialized."""

    def test_archive_directory_exists(self):
        """Archive directory must exist at ~/.maia/data/"""
        archive_dir = Path.home() / ".maia" / "data"
        assert archive_dir.exists(), f"Archive directory missing: {archive_dir}"
        assert archive_dir.is_dir(), f"Archive path is not a directory: {archive_dir}"

    def test_archive_database_exists(self):
        """conversation_archive.db must exist."""
        archive_db = Path.home() / ".maia" / "data" / "conversation_archive.db"
        assert archive_db.exists(), f"Archive database missing: {archive_db}"

    def test_archive_database_has_snapshots_table(self):
        """conversation_archive.db must have conversation_snapshots table."""
        archive_db = Path.home() / ".maia" / "data" / "conversation_archive.db"
        if not archive_db.exists():
            pytest.skip("Archive DB doesn't exist yet")

        conn = sqlite3.connect(archive_db)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='conversation_snapshots'"
        )
        result = cursor.fetchone()
        conn.close()

        assert result is not None, "conversation_snapshots table missing"

    def test_archive_database_has_metrics_table(self):
        """conversation_archive.db must have compaction_metrics table."""
        archive_db = Path.home() / ".maia" / "data" / "conversation_archive.db"
        if not archive_db.exists():
            pytest.skip("Archive DB doesn't exist yet")

        conn = sqlite3.connect(archive_db)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='compaction_metrics'"
        )
        result = cursor.fetchone()
        conn.close()

        assert result is not None, "compaction_metrics table missing"

    def test_archive_schema_allows_proactive_monitor(self):
        """Schema must allow 'proactive_monitor' trigger_type."""
        archive_db = Path.home() / ".maia" / "data" / "conversation_archive.db"
        if not archive_db.exists():
            pytest.skip("Archive DB doesn't exist yet")

        conn = sqlite3.connect(archive_db)
        try:
            # Try inserting with proactive_monitor trigger type
            conn.execute("""
                INSERT INTO compaction_metrics
                (context_id, compaction_timestamp, trigger_type, success)
                VALUES ('test', 1704672000, 'proactive_monitor', 1)
            """)
            conn.commit()

            # Clean up test data
            conn.execute("DELETE FROM compaction_metrics WHERE context_id = 'test'")
            conn.commit()
        except sqlite3.IntegrityError as e:
            pytest.fail(f"proactive_monitor trigger type not allowed: {e}")
        finally:
            conn.close()


class TestLearningDatabase:
    """Test learning.db is properly initialized."""

    def test_learning_database_exists(self):
        """learning.db must exist."""
        # Check both possible locations
        maia_root = Path(__file__).parent.parent.parent
        learning_db = maia_root / "claude" / "data" / "databases" / "intelligence" / "learning.db"
        assert learning_db.exists(), f"Learning database missing: {learning_db}"

    def test_learning_database_has_patterns_table(self):
        """learning.db must have patterns table."""
        maia_root = Path(__file__).parent.parent.parent
        learning_db = maia_root / "claude" / "data" / "databases" / "intelligence" / "learning.db"
        if not learning_db.exists():
            pytest.skip("Learning DB doesn't exist yet")

        conn = sqlite3.connect(learning_db)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='patterns'"
        )
        result = cursor.fetchone()
        conn.close()

        assert result is not None, "patterns table missing"

    def test_learning_database_has_preferences_table(self):
        """learning.db must have preferences table."""
        maia_root = Path(__file__).parent.parent.parent
        learning_db = maia_root / "claude" / "data" / "databases" / "intelligence" / "learning.db"
        if not learning_db.exists():
            pytest.skip("Learning DB doesn't exist yet")

        conn = sqlite3.connect(learning_db)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='preferences'"
        )
        result = cursor.fetchone()
        conn.close()

        assert result is not None, "preferences table missing"

    def test_learning_database_has_metrics_table(self):
        """learning.db must have metrics table."""
        maia_root = Path(__file__).parent.parent.parent
        learning_db = maia_root / "claude" / "data" / "databases" / "intelligence" / "learning.db"
        if not learning_db.exists():
            pytest.skip("Learning DB doesn't exist yet")

        conn = sqlite3.connect(learning_db)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='metrics'"
        )
        result = cursor.fetchone()
        conn.close()

        assert result is not None, "metrics table missing"


class TestArchiveModuleInitialization:
    """Test archive module can initialize properly."""

    def test_archive_module_imports(self):
        """Archive module must import without errors."""
        try:
            from claude.tools.learning.archive import get_archive
        except ImportError as e:
            pytest.fail(f"Failed to import archive module: {e}")

    def test_archive_module_initializes(self):
        """Archive module must initialize without errors."""
        from claude.tools.learning.archive import get_archive

        try:
            archive = get_archive()
            assert archive is not None
        except Exception as e:
            pytest.fail(f"Archive module failed to initialize: {e}")

    def test_archive_can_log_metric(self):
        """Archive must be able to log compaction metrics."""
        from claude.tools.learning.archive import get_archive

        archive = get_archive()

        try:
            # This should not raise an error
            archive.log_compaction_metric(
                context_id="test_context",
                trigger_type="proactive_monitor",
                execution_time_ms=100,
                messages_processed=50,
                learnings_extracted=5,
                success=True,
                snapshot_id=None,
                error_message=None
            )
        except Exception as e:
            pytest.fail(f"Failed to log compaction metric: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
