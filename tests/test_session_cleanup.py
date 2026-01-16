#!/usr/bin/env python3
"""
Tests for session cleanup robustness improvements.

SPRINT-003-SESSION-CLEANUP
- P1: EPERM bug fix in is_process_alive()
- P2: Learning data preservation in cleanup
- P3: Process name validation
- P4: Threshold reduction (after P1-P3)

TDD Approach: Tests written first, then implementation.
"""

import json
import os
import sys
import time
import tempfile
import subprocess
from pathlib import Path
from unittest import TestCase, mock
from datetime import datetime

# Add maia root to path
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

from claude.hooks.swarm_auto_loader import (
    is_process_alive,
    cleanup_stale_sessions,
    _cleanup_session,
    get_sessions_dir,
)


class TestIsProcessAliveEPERMFix(TestCase):
    """P1: Tests for EPERM bug fix in is_process_alive()."""

    def test_is_process_alive_returns_true_for_running_process(self):
        """Current process should be detected as alive."""
        # Use current process PID - guaranteed to be running
        current_pid = os.getpid()
        self.assertTrue(is_process_alive(current_pid))

    def test_is_process_alive_returns_false_for_nonexistent_process(self):
        """Non-existent PID should return False."""
        # Use a very high PID unlikely to exist
        fake_pid = 999999
        self.assertFalse(is_process_alive(fake_pid))

    @mock.patch('claude.hooks.swarm_auto_loader.os.kill')
    def test_is_process_alive_eperm_returns_true(self, mock_kill):
        """PermissionError (EPERM) means process exists but no permission - should return True."""
        mock_kill.side_effect = PermissionError("Operation not permitted")
        result = is_process_alive(12345)
        self.assertTrue(result, "EPERM should indicate process exists - return True")

    @mock.patch('claude.hooks.swarm_auto_loader.os.kill')
    def test_is_process_alive_esrch_returns_false(self, mock_kill):
        """ProcessLookupError (ESRCH) means process doesn't exist - should return False."""
        mock_kill.side_effect = ProcessLookupError("No such process")
        result = is_process_alive(12345)
        self.assertFalse(result, "ESRCH should indicate process doesn't exist - return False")

    def test_is_process_alive_negative_pid_returns_false(self):
        """Negative PIDs should return False (safety check)."""
        # Negative PIDs have special meaning in kill() - should be rejected
        result = is_process_alive(-1)
        self.assertFalse(result, "Negative PID should return False for safety")

    def test_is_process_alive_zero_pid_returns_false(self):
        """Zero PID should return False (safety check)."""
        result = is_process_alive(0)
        self.assertFalse(result, "Zero PID should return False for safety")


class TestCleanupPreservesLearningData(TestCase):
    """P2: Tests for learning data preservation during cleanup."""

    def setUp(self):
        """Create temporary session directory for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_get_sessions_dir = None

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cleanup_session_captures_memory_before_delete(self):
        """_cleanup_session should capture session memory before deleting file."""
        # Create a test session file
        session_file = Path(self.temp_dir) / "swarm_session_99999.json"
        session_data = {
            "current_agent": "test_agent",
            "session_start": "2026-01-15T00:00:00Z",
            "domain": "test"
        }
        session_file.write_text(json.dumps(session_data))

        # Mock _capture_session_memory to verify it's called
        with mock.patch('claude.hooks.swarm_auto_loader._capture_session_memory') as mock_capture:
            result = _cleanup_session(session_file)

            # Verify memory capture was called with session data
            self.assertTrue(mock_capture.called, "_capture_session_memory should be called")
            if mock_capture.called:
                call_args = mock_capture.call_args[0][0]
                self.assertEqual(call_args.get('current_agent'), 'test_agent')

        # Verify file was deleted
        self.assertFalse(session_file.exists(), "Session file should be deleted after cleanup")

    @mock.patch('claude.hooks.swarm_auto_loader.get_sessions_dir')
    @mock.patch('claude.hooks.swarm_auto_loader._cleanup_session')
    @mock.patch('claude.hooks.swarm_auto_loader.is_process_alive')
    def test_cleanup_stale_sessions_uses_cleanup_session(self, mock_alive, mock_cleanup, mock_dir):
        """cleanup_stale_sessions should use _cleanup_session, not direct unlink."""
        # Setup mock sessions directory
        mock_dir.return_value = Path(self.temp_dir)
        mock_alive.return_value = False  # Process is dead
        mock_cleanup.return_value = True

        # Create old session file (25 hours old)
        session_file = Path(self.temp_dir) / "swarm_session_88888.json"
        session_file.write_text('{"test": "data"}')
        old_time = time.time() - (25 * 3600)
        os.utime(session_file, (old_time, old_time))

        # Run cleanup
        cleanup_stale_sessions(max_age_hours=24)

        # Verify _cleanup_session was called (not direct unlink)
        self.assertTrue(mock_cleanup.called,
                       "cleanup_stale_sessions should call _cleanup_session to preserve learning data")


class TestProcessNameValidation(TestCase):
    """P3: Tests for process name validation."""

    def test_verify_claude_process_exists(self):
        """verify_claude_process function should exist after P3 implementation."""
        try:
            from claude.hooks.swarm_auto_loader import verify_claude_process
            self.assertTrue(callable(verify_claude_process))
        except ImportError:
            self.fail("verify_claude_process function not implemented yet")

    @mock.patch('claude.hooks.swarm_auto_loader.subprocess.run')
    @mock.patch('claude.hooks.swarm_auto_loader.is_process_alive')
    def test_verify_claude_process_returns_true_for_claude(self, mock_alive, mock_run):
        """Should return True when process name contains 'claude'."""
        try:
            from claude.hooks.swarm_auto_loader import verify_claude_process
        except ImportError:
            self.skipTest("verify_claude_process not implemented yet")

        mock_alive.return_value = True
        mock_run.return_value = mock.Mock(returncode=0, stdout="claude\n")

        result = verify_claude_process(12345)
        self.assertTrue(result, "Should return True for claude process")

    @mock.patch('claude.hooks.swarm_auto_loader.subprocess.run')
    @mock.patch('claude.hooks.swarm_auto_loader.is_process_alive')
    def test_verify_claude_process_returns_true_for_native_binary(self, mock_alive, mock_run):
        """Should return True when process name contains 'native-binary'."""
        try:
            from claude.hooks.swarm_auto_loader import verify_claude_process
        except ImportError:
            self.skipTest("verify_claude_process not implemented yet")

        mock_alive.return_value = True
        mock_run.return_value = mock.Mock(returncode=0, stdout="native-binary/claude\n")

        result = verify_claude_process(12345)
        self.assertTrue(result, "Should return True for native-binary process")

    @mock.patch('claude.hooks.swarm_auto_loader.subprocess.run')
    @mock.patch('claude.hooks.swarm_auto_loader.is_process_alive')
    def test_verify_claude_process_returns_false_for_other_process(self, mock_alive, mock_run):
        """Should return False when process is not Claude."""
        try:
            from claude.hooks.swarm_auto_loader import verify_claude_process
        except ImportError:
            self.skipTest("verify_claude_process not implemented yet")

        mock_alive.return_value = True
        mock_run.return_value = mock.Mock(returncode=0, stdout="chrome\n")

        result = verify_claude_process(12345)
        self.assertFalse(result, "Should return False for non-Claude process")

    @mock.patch('claude.hooks.swarm_auto_loader.is_process_alive')
    def test_verify_claude_process_returns_false_for_dead_process(self, mock_alive):
        """Should return False when process is not running."""
        try:
            from claude.hooks.swarm_auto_loader import verify_claude_process
        except ImportError:
            self.skipTest("verify_claude_process not implemented yet")

        mock_alive.return_value = False

        result = verify_claude_process(12345)
        self.assertFalse(result, "Should return False for dead process")

    @mock.patch('claude.hooks.swarm_auto_loader.subprocess.run')
    @mock.patch('claude.hooks.swarm_auto_loader.is_process_alive')
    def test_verify_claude_process_handles_ps_failure_gracefully(self, mock_alive, mock_run):
        """Should return True (conservative) when ps command fails."""
        try:
            from claude.hooks.swarm_auto_loader import verify_claude_process
        except ImportError:
            self.skipTest("verify_claude_process not implemented yet")

        mock_alive.return_value = True
        mock_run.side_effect = subprocess.TimeoutExpired("ps", 0.5)

        result = verify_claude_process(12345)
        self.assertTrue(result, "Should return True (conservative) when ps fails")


class TestCleanupIntegration(TestCase):
    """Integration tests for cleanup with all P1-P3 fixes."""

    def setUp(self):
        """Create temporary session directory."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @mock.patch('claude.hooks.swarm_auto_loader.get_sessions_dir')
    @mock.patch('claude.hooks.swarm_auto_loader._cleanup_session')
    def test_cleanup_removes_old_dead_sessions(self, mock_cleanup, mock_dir):
        """Old sessions with dead processes should be cleaned up."""
        mock_dir.return_value = Path(self.temp_dir)
        mock_cleanup.return_value = True

        # Create old session file with non-existent PID
        session_file = Path(self.temp_dir) / "swarm_session_999999.json"
        session_file.write_text('{"current_agent": "test"}')
        old_time = time.time() - (25 * 3600)
        os.utime(session_file, (old_time, old_time))

        # Run cleanup
        cleanup_stale_sessions(max_age_hours=24)

        # Verify cleanup was attempted
        self.assertTrue(mock_cleanup.called, "Should attempt to clean old dead session")

    @mock.patch('claude.hooks.swarm_auto_loader.get_sessions_dir')
    @mock.patch('claude.hooks.swarm_auto_loader._cleanup_session')
    def test_cleanup_preserves_recent_sessions(self, mock_cleanup, mock_dir):
        """Recent sessions should not be cleaned up regardless of process state."""
        mock_dir.return_value = Path(self.temp_dir)

        # Create recent session file (1 hour old)
        session_file = Path(self.temp_dir) / "swarm_session_999998.json"
        session_file.write_text('{"current_agent": "test"}')
        recent_time = time.time() - 3600  # 1 hour ago
        os.utime(session_file, (recent_time, recent_time))

        # Run cleanup
        cleanup_stale_sessions(max_age_hours=24)

        # Verify cleanup was NOT called for recent session
        self.assertFalse(mock_cleanup.called, "Should not clean recent session")

    @mock.patch('claude.hooks.swarm_auto_loader.get_sessions_dir')
    @mock.patch('claude.hooks.swarm_auto_loader._cleanup_session')
    @mock.patch('claude.hooks.swarm_auto_loader.is_process_alive')
    def test_cleanup_preserves_active_sessions(self, mock_alive, mock_cleanup, mock_dir):
        """Active sessions (process running) should not be cleaned up."""
        mock_dir.return_value = Path(self.temp_dir)
        mock_alive.return_value = True  # Process is alive

        # Create old session file
        session_file = Path(self.temp_dir) / "swarm_session_999997.json"
        session_file.write_text('{"current_agent": "test"}')
        old_time = time.time() - (25 * 3600)
        os.utime(session_file, (old_time, old_time))

        # Run cleanup
        cleanup_stale_sessions(max_age_hours=24)

        # Verify cleanup was NOT called for active session
        self.assertFalse(mock_cleanup.called, "Should not clean active session")


class TestP4ThresholdReduction(TestCase):
    """P4: Tests for 4-hour threshold reduction."""

    def setUp(self):
        """Create temporary session directory."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @mock.patch('claude.hooks.swarm_auto_loader.get_sessions_dir')
    @mock.patch('claude.hooks.swarm_auto_loader._cleanup_session')
    def test_cleanup_removes_5_hour_old_sessions(self, mock_cleanup, mock_dir):
        """Sessions 5 hours old (> 4 hour threshold) should be cleaned."""
        mock_dir.return_value = Path(self.temp_dir)
        mock_cleanup.return_value = True

        # Create 5-hour-old session file with non-existent PID
        session_file = Path(self.temp_dir) / "swarm_session_999999.json"
        session_file.write_text('{"current_agent": "test"}')
        old_time = time.time() - (5 * 3600)  # 5 hours ago
        os.utime(session_file, (old_time, old_time))

        # Run cleanup with 4-hour threshold
        cleanup_stale_sessions(max_age_hours=4)

        # Verify cleanup was attempted
        self.assertTrue(mock_cleanup.called, "Should clean 5-hour-old dead session with 4hr threshold")

    @mock.patch('claude.hooks.swarm_auto_loader.get_sessions_dir')
    @mock.patch('claude.hooks.swarm_auto_loader._cleanup_session')
    def test_cleanup_preserves_3_hour_old_sessions(self, mock_cleanup, mock_dir):
        """Sessions 3 hours old (< 4 hour threshold) should be preserved."""
        mock_dir.return_value = Path(self.temp_dir)

        # Create 3-hour-old session file
        session_file = Path(self.temp_dir) / "swarm_session_999998.json"
        session_file.write_text('{"current_agent": "test"}')
        recent_time = time.time() - (3 * 3600)  # 3 hours ago
        os.utime(session_file, (recent_time, recent_time))

        # Run cleanup with 4-hour threshold
        cleanup_stale_sessions(max_age_hours=4)

        # Verify cleanup was NOT called
        self.assertFalse(mock_cleanup.called, "Should preserve 3-hour-old session with 4hr threshold")

    @mock.patch('claude.hooks.swarm_auto_loader.get_sessions_dir')
    @mock.patch('claude.hooks.swarm_auto_loader._cleanup_session')
    def test_cleanup_boundary_at_4_hours(self, mock_cleanup, mock_dir):
        """Test cleanup at exactly 4 hour boundary."""
        mock_dir.return_value = Path(self.temp_dir)
        mock_cleanup.return_value = True

        # Create session file exactly 4 hours + 1 minute old
        session_file = Path(self.temp_dir) / "swarm_session_999997.json"
        session_file.write_text('{"current_agent": "test"}')
        boundary_time = time.time() - (4 * 3600 + 60)  # 4 hours + 1 minute ago
        os.utime(session_file, (boundary_time, boundary_time))

        # Run cleanup with 4-hour threshold
        cleanup_stale_sessions(max_age_hours=4)

        # Verify cleanup was attempted (just over threshold)
        self.assertTrue(mock_cleanup.called, "Should clean session just over 4hr threshold")


if __name__ == '__main__':
    import unittest
    unittest.main()
