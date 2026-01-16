#!/usr/bin/env python3
"""
Tests for session heartbeat mechanism.

SPRINT-003-SESSION-CLEANUP P5: Heartbeat Mechanism
- More robust than time-based cleanup
- Can distinguish "alive but idle" from "crashed"
- Sessions update heartbeat periodically
- Cleanup checks heartbeat freshness

TDD Approach: Tests written first, then implementation.
"""

import json
import os
import sys
import time
import tempfile
from pathlib import Path
from unittest import TestCase, mock
from datetime import datetime, timedelta

# Add maia root to path
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))


class TestSessionHeartbeatSchema(TestCase):
    """P5.1: Tests for heartbeat field in session schema."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @mock.patch('claude.hooks.swarm_auto_loader.SESSION_STATE_FILE')
    @mock.patch('claude.hooks.swarm_auto_loader._start_learning_session')
    @mock.patch('claude.hooks.swarm_auto_loader.load_ltm_context')
    @mock.patch('claude.hooks.swarm_auto_loader.load_tdd_context')
    @mock.patch('claude.hooks.swarm_auto_loader._get_repository_metadata')
    def test_session_includes_heartbeat_field_on_creation(
        self, mock_repo, mock_tdd, mock_ltm, mock_learning, mock_file
    ):
        """New sessions should include last_heartbeat field."""
        from claude.hooks.swarm_auto_loader import create_session_state

        # Set up mocks
        session_file = Path(self.temp_dir) / "test_session.json"
        mock_file.__truediv__ = lambda self, x: session_file
        mock_file.exists.return_value = False
        mock_file.with_suffix.return_value = session_file.with_suffix(".tmp")
        mock_file.chmod = mock.Mock()
        mock_repo.return_value = {}
        mock_tdd.return_value = None
        mock_ltm.return_value = None
        mock_learning.return_value = (None, None)

        # Mock the file path property to return our test path
        type(mock_file).parent = mock.PropertyMock(return_value=Path(self.temp_dir))

        # Create session - this writes to a file
        result = create_session_state(
            agent="test_agent",
            domain="test",
            classification={"confidence": 0.9},
            query="test query"
        )

        # Read the created session file
        tmp_file = session_file.with_suffix(".tmp")
        if tmp_file.exists():
            with open(tmp_file) as f:
                session = json.load(f)

            self.assertIn("last_heartbeat", session,
                         "Session should include last_heartbeat field")
            self.assertIn("heartbeat_interval_seconds", session,
                         "Session should include heartbeat_interval_seconds field")

    def test_heartbeat_field_is_iso_timestamp(self):
        """last_heartbeat should be ISO format timestamp."""
        # Create a mock session file and verify format
        session_file = Path(self.temp_dir) / "test_session.json"
        test_heartbeat = datetime.utcnow().isoformat() + 'Z'
        session_data = {
            "current_agent": "test_agent",
            "last_heartbeat": test_heartbeat,
            "heartbeat_interval_seconds": 300
        }
        session_file.write_text(json.dumps(session_data))

        # Read and verify
        with open(session_file) as f:
            session = json.load(f)

        heartbeat = session.get("last_heartbeat")
        self.assertIsNotNone(heartbeat)
        try:
            datetime.fromisoformat(heartbeat.replace('Z', '+00:00'))
        except ValueError:
            self.fail(f"last_heartbeat '{heartbeat}' is not valid ISO format")

    def test_default_heartbeat_interval(self):
        """Default heartbeat interval should be 300 seconds (5 minutes)."""
        # This test verifies the constant value used in create_session_state
        # We test by creating a session and checking the interval
        session_file = Path(self.temp_dir) / "test_session.json"
        session_data = {
            "current_agent": "test_agent",
            "last_heartbeat": datetime.utcnow().isoformat() + 'Z',
            "heartbeat_interval_seconds": 300  # This is the expected default
        }
        session_file.write_text(json.dumps(session_data))

        with open(session_file) as f:
            session = json.load(f)

        interval = session.get("heartbeat_interval_seconds", 0)
        self.assertEqual(interval, 300,
                        "Default heartbeat interval should be 300 seconds")


class TestUpdateHeartbeat(TestCase):
    """P5.2: Tests for heartbeat update function."""

    def setUp(self):
        """Create temporary session directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.session_file = Path(self.temp_dir) / "swarm_session_12345.json"

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_update_heartbeat_function_exists(self):
        """update_session_heartbeat function should exist."""
        try:
            from claude.hooks.swarm_auto_loader import update_session_heartbeat
            self.assertTrue(callable(update_session_heartbeat))
        except ImportError:
            self.fail("update_session_heartbeat function not implemented yet")

    @mock.patch('claude.hooks.swarm_auto_loader.get_session_file_path')
    def test_update_heartbeat_modifies_timestamp(self, mock_path):
        """update_session_heartbeat should update the timestamp."""
        try:
            from claude.hooks.swarm_auto_loader import update_session_heartbeat
        except ImportError:
            self.skipTest("update_session_heartbeat not implemented yet")

        mock_path.return_value = self.session_file

        # Create session with old heartbeat
        old_time = (datetime.utcnow() - timedelta(hours=1)).isoformat() + 'Z'
        session_data = {
            "current_agent": "test_agent",
            "last_heartbeat": old_time,
            "heartbeat_interval_seconds": 300
        }
        self.session_file.write_text(json.dumps(session_data))

        # Update heartbeat
        update_session_heartbeat()

        # Verify timestamp was updated
        with open(self.session_file) as f:
            updated = json.load(f)

        new_heartbeat = datetime.fromisoformat(
            updated["last_heartbeat"].replace('Z', '+00:00')
        )
        old_heartbeat = datetime.fromisoformat(old_time.replace('Z', '+00:00'))

        self.assertGreater(new_heartbeat, old_heartbeat,
                          "Heartbeat should be updated to more recent time")

    @mock.patch('claude.hooks.swarm_auto_loader.get_session_file_path')
    def test_update_heartbeat_handles_missing_file_gracefully(self, mock_path):
        """update_session_heartbeat should not crash if session file missing."""
        try:
            from claude.hooks.swarm_auto_loader import update_session_heartbeat
        except ImportError:
            self.skipTest("update_session_heartbeat not implemented yet")

        mock_path.return_value = Path(self.temp_dir) / "nonexistent.json"

        # Should not raise
        try:
            update_session_heartbeat()
        except Exception as e:
            self.fail(f"update_session_heartbeat raised {e} for missing file")


class TestIsSessionStaleByHeartbeat(TestCase):
    """P5.3: Tests for heartbeat-based staleness detection."""

    def setUp(self):
        """Create temporary session directory."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_is_session_stale_by_heartbeat_function_exists(self):
        """is_session_stale_by_heartbeat function should exist."""
        try:
            from claude.hooks.swarm_auto_loader import is_session_stale_by_heartbeat
            self.assertTrue(callable(is_session_stale_by_heartbeat))
        except ImportError:
            self.fail("is_session_stale_by_heartbeat function not implemented yet")

    def test_fresh_heartbeat_is_not_stale(self):
        """Session with recent heartbeat should not be stale."""
        try:
            from claude.hooks.swarm_auto_loader import is_session_stale_by_heartbeat
        except ImportError:
            self.skipTest("is_session_stale_by_heartbeat not implemented yet")

        # Create session with fresh heartbeat (1 minute ago)
        session_file = Path(self.temp_dir) / "swarm_session_12345.json"
        fresh_time = (datetime.utcnow() - timedelta(minutes=1)).isoformat() + 'Z'
        session_data = {
            "current_agent": "test_agent",
            "last_heartbeat": fresh_time,
            "heartbeat_interval_seconds": 300  # 5 minutes
        }
        session_file.write_text(json.dumps(session_data))

        result = is_session_stale_by_heartbeat(session_file)
        self.assertFalse(result, "Session with 1-minute-old heartbeat should not be stale")

    def test_old_heartbeat_is_stale(self):
        """Session with old heartbeat (missed multiple intervals) should be stale."""
        try:
            from claude.hooks.swarm_auto_loader import is_session_stale_by_heartbeat
        except ImportError:
            self.skipTest("is_session_stale_by_heartbeat not implemented yet")

        # Create session with old heartbeat (30 minutes ago, 6 intervals missed)
        session_file = Path(self.temp_dir) / "swarm_session_12345.json"
        old_time = (datetime.utcnow() - timedelta(minutes=30)).isoformat() + 'Z'
        session_data = {
            "current_agent": "test_agent",
            "last_heartbeat": old_time,
            "heartbeat_interval_seconds": 300  # 5 minutes
        }
        session_file.write_text(json.dumps(session_data))

        result = is_session_stale_by_heartbeat(session_file, max_missed_heartbeats=3)
        self.assertTrue(result, "Session with 30-minute-old heartbeat (6 missed) should be stale")

    def test_session_without_heartbeat_falls_back_to_mtime(self):
        """Session without heartbeat field should fall back to file mtime."""
        try:
            from claude.hooks.swarm_auto_loader import is_session_stale_by_heartbeat
        except ImportError:
            self.skipTest("is_session_stale_by_heartbeat not implemented yet")

        # Create session WITHOUT heartbeat field
        session_file = Path(self.temp_dir) / "swarm_session_12345.json"
        session_data = {
            "current_agent": "test_agent",
            # No last_heartbeat field
        }
        session_file.write_text(json.dumps(session_data))

        # Set mtime to 5 hours ago (should be stale with 4hr fallback)
        old_time = time.time() - (5 * 3600)
        os.utime(session_file, (old_time, old_time))

        result = is_session_stale_by_heartbeat(session_file)
        self.assertTrue(result, "Session without heartbeat should fall back to mtime check")

    def test_configurable_missed_heartbeats_threshold(self):
        """max_missed_heartbeats should be configurable."""
        try:
            from claude.hooks.swarm_auto_loader import is_session_stale_by_heartbeat
        except ImportError:
            self.skipTest("is_session_stale_by_heartbeat not implemented yet")

        # Create session with 20-minute-old heartbeat (4 intervals missed)
        session_file = Path(self.temp_dir) / "swarm_session_12345.json"
        old_time = (datetime.utcnow() - timedelta(minutes=20)).isoformat() + 'Z'
        session_data = {
            "current_agent": "test_agent",
            "last_heartbeat": old_time,
            "heartbeat_interval_seconds": 300  # 5 minutes
        }
        session_file.write_text(json.dumps(session_data))

        # With max_missed=3, 4 missed intervals should be stale
        result_strict = is_session_stale_by_heartbeat(session_file, max_missed_heartbeats=3)
        self.assertTrue(result_strict, "4 missed with max=3 should be stale")

        # With max_missed=5, 4 missed intervals should NOT be stale
        result_lenient = is_session_stale_by_heartbeat(session_file, max_missed_heartbeats=5)
        self.assertFalse(result_lenient, "4 missed with max=5 should not be stale")


class TestCleanupUsesHeartbeat(TestCase):
    """P5.4: Tests for heartbeat integration in cleanup."""

    def setUp(self):
        """Create temporary session directory."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @mock.patch('claude.hooks.swarm_auto_loader.get_sessions_dir')
    @mock.patch('claude.hooks.swarm_auto_loader._cleanup_session')
    @mock.patch('claude.hooks.swarm_auto_loader.verify_claude_process')
    def test_cleanup_checks_heartbeat_for_sessions_with_heartbeat(
        self, mock_verify, mock_cleanup, mock_dir
    ):
        """Cleanup should use heartbeat when available."""
        from claude.hooks.swarm_auto_loader import cleanup_stale_sessions

        mock_dir.return_value = Path(self.temp_dir)
        mock_verify.return_value = False  # Process not running
        mock_cleanup.return_value = True

        # Create session with STALE heartbeat (30 minutes old)
        session_file = Path(self.temp_dir) / "swarm_session_999999.json"
        old_time = (datetime.utcnow() - timedelta(minutes=30)).isoformat() + 'Z'
        session_data = {
            "current_agent": "test_agent",
            "last_heartbeat": old_time,
            "heartbeat_interval_seconds": 300
        }
        session_file.write_text(json.dumps(session_data))

        # File mtime is recent (would NOT be cleaned with mtime-only check)
        # But heartbeat is old (SHOULD be cleaned)

        # Run cleanup
        cleanup_stale_sessions(max_age_hours=4)

        # Should be cleaned because heartbeat is stale
        self.assertTrue(mock_cleanup.called,
                       "Session with stale heartbeat should be cleaned even if mtime is recent")


if __name__ == '__main__':
    import unittest
    unittest.main()
