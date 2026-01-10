#!/usr/bin/env python3
"""
Phase 1: Bug Fixes - TDD Tests

Tests for critical bugs preventing PAI learning system from working:
1. sqlite3.Connection bug in pai_v2_bridge.py
2. compaction_metrics CHECK constraint bug
"""

import pytest
import sqlite3
import tempfile
from pathlib import Path
from datetime import datetime

from claude.tools.learning.pai_v2_bridge import PAIv2Bridge, get_pai_v2_bridge


class TestPAIv2BridgeConnectionBug:
    """Test that PAI v2 bridge connects correctly to database."""

    def test_pai_v2_bridge_connects_correctly(self, tmp_path):
        """
        Bug: pai_v2_bridge.py line 60 uses sqlite3.Connection(path) instead of sqlite3.connect(path)
        Expected: Bridge should successfully create connection and save patterns
        """
        # Setup
        db_path = tmp_path / "test_learning.db"

        # Create learning database manually
        from claude.tools.learning.schema import init_learning_db
        conn = init_learning_db(db_path)
        conn.close()

        # Create bridge instance pointing to test DB
        bridge = PAIv2Bridge()
        bridge.db_path = db_path

        # Test: Should successfully get connection without error
        try:
            conn = bridge._get_conn()
            assert conn is not None, "Connection should not be None"
            assert isinstance(conn, sqlite3.Connection), "Should return sqlite3.Connection"

            # Verify connection is usable
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            assert 'patterns' in tables, "patterns table should exist"

            conn.close()
        except Exception as e:
            pytest.fail(f"Failed to create connection: {e}")

    def test_bridge_saves_learnings_successfully(self, tmp_path):
        """
        Integration test: Bridge should save learnings to database
        This will fail if sqlite3.Connection bug exists
        """
        # Setup
        db_path = tmp_path / "test_learning.db"
        from claude.tools.learning.schema import init_learning_db
        init_learning_db(db_path).close()

        bridge = PAIv2Bridge()
        bridge.db_path = db_path

        # Test data
        learnings = [
            {
                'type': 'decision',
                'content': 'Chose queue-based architecture for reliability',
                'timestamp': datetime.now().isoformat(),
                'context': {'agent': 'sre'}
            },
            {
                'type': 'solution',
                'content': 'Fixed sqlite3.Connection bug',
                'timestamp': datetime.now().isoformat(),
                'context': {}
            }
        ]

        # Execute: Save learnings
        pattern_ids = bridge.save_learnings_as_patterns(
            learnings=learnings,
            context_id='test_ctx_123',
            session_id='test_session_1',
            domain='learning'
        )

        # Verify: Should return pattern IDs
        assert len(pattern_ids) == 2, "Should create 2 patterns"
        assert all(pid.startswith('pat_') for pid in pattern_ids), "Pattern IDs should have correct format"

        # Verify: Patterns exist in database
        for pattern_id in pattern_ids:
            pattern = bridge.get_pattern(pattern_id)
            assert pattern is not None, f"Pattern {pattern_id} should exist"
            assert pattern['domain'] == 'learning'
            assert pattern['confidence'] > 0


class TestCompactionMetricsConstraint:
    """Test that compaction_metrics table accepts all trigger types."""

    def test_metrics_accepts_proactive_monitor_trigger(self, tmp_path):
        """
        Bug: compaction_metrics CHECK constraint may only allow 'auto'|'manual'
        Expected: Should accept 'proactive_monitor' and 'skill' as well
        """
        from claude.tools.learning.archive import ConversationArchive

        # Setup
        db_path = tmp_path / "test_archive.db"
        archive = ConversationArchive(db_path)

        context_id = "test_context_monitor"

        # Test: Log metric with proactive_monitor trigger
        try:
            archive.log_compaction_metric(
                context_id=context_id,
                trigger_type='proactive_monitor',
                execution_time_ms=100,
                messages_processed=50,
                learnings_extracted=5,
                success=True,
                snapshot_id=None
            )
        except sqlite3.IntegrityError as e:
            if "CHECK constraint" in str(e):
                pytest.fail(f"CHECK constraint failed - schema needs updating: {e}")
            raise

        # Verify: Metric was saved
        conn = sqlite3.connect(db_path)
        row = conn.execute(
            "SELECT * FROM compaction_metrics WHERE context_id = ? AND trigger_type = ?",
            (context_id, 'proactive_monitor')
        ).fetchone()
        conn.close()

        assert row is not None, "Metric with proactive_monitor trigger should be saved"

    def test_metrics_accepts_skill_trigger(self, tmp_path):
        """Test that 'skill' trigger type is accepted."""
        from claude.tools.learning.archive import ConversationArchive

        db_path = tmp_path / "test_archive.db"
        archive = ConversationArchive(db_path)

        # Test: Log metric with skill trigger
        try:
            archive.log_compaction_metric(
                context_id="test_skill_context",
                trigger_type='skill',
                execution_time_ms=50,
                messages_processed=20,
                learnings_extracted=2,
                success=True,
                snapshot_id=None
            )
        except sqlite3.IntegrityError as e:
            if "CHECK constraint" in str(e):
                pytest.fail(f"CHECK constraint failed for 'skill' trigger: {e}")
            raise

        # Should complete without error
        assert True

    def test_metrics_rejects_invalid_trigger(self, tmp_path):
        """Test that invalid trigger types are still rejected."""
        from claude.tools.learning.archive import ConversationArchive

        db_path = tmp_path / "test_archive.db"
        archive = ConversationArchive(db_path)

        # Test: Should reject invalid trigger type
        with pytest.raises(sqlite3.IntegrityError):
            archive.log_compaction_metric(
                context_id="test_invalid",
                trigger_type='invalid_type',
                execution_time_ms=50,
                messages_processed=20,
                learnings_extracted=0,
                success=False,
                snapshot_id=None
            )


class TestBugFixesIntegration:
    """Integration tests verifying both bugs are fixed."""

    def test_end_to_end_learning_capture_with_monitor_trigger(self, tmp_path):
        """
        End-to-end test: Extract learnings → save via bridge → log metrics
        Tests both bugs together in realistic scenario
        """
        from claude.tools.learning.archive import ConversationArchive

        # Setup databases
        learning_db = tmp_path / "learning.db"
        archive_db = tmp_path / "archive.db"

        from claude.tools.learning.schema import init_learning_db
        init_learning_db(learning_db).close()

        bridge = PAIv2Bridge()
        bridge.db_path = learning_db

        archive = ConversationArchive(archive_db)

        # Simulate learning extraction
        learnings = [
            {
                'type': 'breakthrough',
                'content': 'Discovered PreCompact hooks have a known bug',
                'timestamp': datetime.now().isoformat(),
                'context': {'phase': 263}
            }
        ]

        # Save via bridge (tests sqlite3.Connection bug fix)
        pattern_ids = bridge.save_learnings_as_patterns(
            learnings=learnings,
            context_id='test_e2e',
            domain='sre'
        )

        assert len(pattern_ids) == 1

        # Log metrics with proactive_monitor trigger (tests CHECK constraint bug fix)
        archive.log_compaction_metric(
            context_id='test_e2e',
            trigger_type='proactive_monitor',  # Would fail with old constraint
            execution_time_ms=150,
            messages_processed=100,
            learnings_extracted=1,
            success=True,
            snapshot_id=1
        )

        # Verify both operations succeeded
        pattern = bridge.get_pattern(pattern_ids[0])
        assert pattern is not None
        assert pattern['pattern_type'] == 'workflow'  # breakthrough → workflow
        assert pattern['confidence'] == 0.95  # breakthrough has highest confidence
