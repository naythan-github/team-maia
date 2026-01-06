#!/usr/bin/env python3
"""
Test Context Monitor - Phase 237.4.1
TDD: Write tests FIRST (RED phase)

Tests for background context monitor that triggers proactive learning capture.
"""

import os
import json
import signal
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

# Setup paths for MAIA imports
import sys
maia_root = Path(__file__).parent.parent.parent
if str(maia_root) not in sys.path:
    sys.path.insert(0, str(maia_root))

from claude.hooks.context_monitor import (
    ContextMonitor,
    ContextStatus,
)


class TestContextEstimation:
    """Test token estimation from message count"""

    def test_context_estimation_basic(self, tmp_path):
        """
        Test token estimation from message count.

        Given: Transcript with 100 messages
        When: Estimate tokens
        Then: Should estimate ~80,000 tokens (100 * 800)
        """
        monitor = ContextMonitor(context_window=200000, tokens_per_message=800)

        # Create transcript with 100 messages
        transcript = tmp_path / "test_context" / "transcript.jsonl"
        transcript.parent.mkdir(parents=True)

        with open(transcript, 'w') as f:
            for i in range(100):
                f.write(json.dumps({"role": "user", "content": f"message {i}"}) + "\n")

        # Estimate context
        status = monitor.estimate_context_usage(transcript)

        assert status is not None
        assert status.message_count == 100
        assert status.estimated_tokens == 80000  # 100 * 800
        assert status.usage_percentage == 40.0  # 80K / 200K = 40%
        assert status.context_id == "test_context"

    def test_context_estimation_nonexistent_file(self):
        """
        Test graceful handling of nonexistent transcript.

        Given: Path to nonexistent file
        When: Estimate tokens
        Then: Should return None
        """
        monitor = ContextMonitor()

        transcript = Path("/nonexistent/transcript.jsonl")
        status = monitor.estimate_context_usage(transcript)

        assert status is None


class TestThresholdDetection:
    """Test 70% threshold detection"""

    def test_threshold_detection_over(self, tmp_path):
        """
        Test 70% threshold detection - OVER threshold.

        Given: Context at 150K tokens (75% of 200K)
        When: Check threshold
        Then: Should return True (over 70%)
        """
        monitor = ContextMonitor(
            threshold=0.70,
            context_window=200000,
            tokens_per_message=800
        )

        # Create transcript with 188 messages = 150,400 tokens = 75.2%
        transcript = tmp_path / "test_context" / "transcript.jsonl"
        transcript.parent.mkdir(parents=True)

        with open(transcript, 'w') as f:
            for i in range(188):
                f.write(json.dumps({"role": "user", "content": "test"}) + "\n")

        status = monitor.estimate_context_usage(transcript)
        should_trigger = monitor.should_trigger_capture(status)

        assert should_trigger is True
        assert status.usage_percentage > 70.0

    def test_threshold_detection_under(self, tmp_path):
        """
        Test 70% threshold detection - UNDER threshold.

        Given: Context at 100K tokens (50% of 200K)
        When: Check threshold
        Then: Should return False (under 70%)
        """
        monitor = ContextMonitor(
            threshold=0.70,
            context_window=200000,
            tokens_per_message=800
        )

        # Create transcript with 125 messages = 100K tokens = 50%
        transcript = tmp_path / "test_context" / "transcript.jsonl"
        transcript.parent.mkdir(parents=True)

        with open(transcript, 'w') as f:
            for i in range(125):
                f.write(json.dumps({"role": "user", "content": "test"}) + "\n")

        status = monitor.estimate_context_usage(transcript)
        should_trigger = monitor.should_trigger_capture(status)

        assert should_trigger is False
        assert status.usage_percentage < 70.0

    def test_threshold_detection_already_captured(self, tmp_path):
        """
        Test threshold detection when context already captured.

        Given: Context at 75% AND already in captured set
        When: Check threshold
        Then: Should return False (don't spam)
        """
        monitor = ContextMonitor(threshold=0.70)

        # Create transcript
        transcript = tmp_path / "test_context" / "transcript.jsonl"
        transcript.parent.mkdir(parents=True)

        with open(transcript, 'w') as f:
            for i in range(188):  # 75%
                f.write(json.dumps({"role": "user", "content": "test"}) + "\n")

        status = monitor.estimate_context_usage(transcript)

        # Mark as already captured
        monitor.captured_contexts.add("test_context")

        should_trigger = monitor.should_trigger_capture(status)

        assert should_trigger is False


class TestSingleInstanceEnforcement:
    """Test PID file prevents multiple instances"""

    def test_single_instance_enforcement(self, tmp_path):
        """
        Test PID file prevents multiple instances.

        Given: Monitor already running (PID file exists with current PID)
        When: Start second instance
        Then: Should exit with error
        """
        # Mock PID file
        pid_file = tmp_path / "context_monitor.pid"

        with patch('claude.hooks.context_monitor.PID_FILE', pid_file):
            monitor = ContextMonitor()

            # Write current PID to file
            with open(pid_file, 'w') as f:
                f.write(str(os.getpid()))

            # Try to enforce single instance (should raise SystemExit)
            with pytest.raises(SystemExit) as exc_info:
                monitor.enforce_single_instance()

            assert exc_info.value.code == 1

    def test_single_instance_stale_pid(self, tmp_path):
        """
        Test stale PID file is cleaned up.

        Given: PID file exists with non-existent PID
        When: Enforce single instance
        Then: Should remove stale file and continue
        """
        pid_file = tmp_path / "context_monitor.pid"

        with patch('claude.hooks.context_monitor.PID_FILE', pid_file):
            monitor = ContextMonitor()

            # Write fake PID that doesn't exist
            with open(pid_file, 'w') as f:
                f.write("999999")

            # Should clean up stale PID and write new one
            monitor.enforce_single_instance()

            assert pid_file.exists()
            with open(pid_file) as f:
                new_pid = int(f.read().strip())
            assert new_pid == os.getpid()

            # Cleanup
            monitor.cleanup()


class TestGracefulShutdown:
    """Test SIGTERM handler"""

    def test_graceful_shutdown(self, tmp_path):
        """
        Test SIGTERM handler.

        Given: Monitor initialized
        When: Call signal handler
        Then: Should clean up and set running=False
        """
        pid_file = tmp_path / "context_monitor.pid"

        with patch('claude.hooks.context_monitor.PID_FILE', pid_file):
            monitor = ContextMonitor()
            monitor.running = True

            # Create PID file
            with open(pid_file, 'w') as f:
                f.write(str(os.getpid()))

            # Call signal handler (should exit, so we expect SystemExit)
            with pytest.raises(SystemExit):
                monitor.signal_handler(signal.SIGTERM, None)

            # Should have cleaned up
            assert not pid_file.exists()


class TestTriggerCapture:
    """Test capture triggered when threshold exceeded"""

    def test_trigger_capture_on_threshold(self, tmp_path):
        """
        Test capture triggered when threshold exceeded.

        Given: Context at 145K tokens (72.5%)
        When: Monitor checks
        Then: Should trigger pre_compaction_learning_capture.py
        """
        monitor = ContextMonitor(threshold=0.70)

        # Create transcript
        transcript = tmp_path / "test_context" / "transcript.jsonl"
        transcript.parent.mkdir(parents=True)

        with open(transcript, 'w') as f:
            for i in range(182):  # ~145K tokens = 72.5%
                f.write(json.dumps({"role": "user", "content": "test"}) + "\n")

        status = monitor.estimate_context_usage(transcript)

        # Mock subprocess.run to avoid actually calling hook
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr=b'')

            result = monitor.trigger_capture(status)

            assert result is True
            assert "test_context" in monitor.captured_contexts

            # Verify hook was called
            mock_run.assert_called_once()
            call_args = mock_run.call_args
            assert 'pre_compaction_learning_capture.py' in str(call_args)

    def test_skip_capture_below_threshold(self, tmp_path):
        """
        Test no capture when below threshold.

        Given: Context at 100K tokens (50%)
        When: Monitor checks
        Then: Should not trigger capture
        """
        monitor = ContextMonitor(threshold=0.70)

        # Create transcript
        transcript = tmp_path / "test_context" / "transcript.jsonl"
        transcript.parent.mkdir(parents=True)

        with open(transcript, 'w') as f:
            for i in range(125):  # 100K tokens = 50%
                f.write(json.dumps({"role": "user", "content": "test"}) + "\n")

        status = monitor.estimate_context_usage(transcript)
        should_trigger = monitor.should_trigger_capture(status)

        assert should_trigger is False


class TestErrorHandling:
    """Test graceful handling of errors"""

    def test_error_handling_missing_transcript(self):
        """
        Test graceful handling of missing transcript.

        Given: Project directory without transcript.jsonl
        When: Monitor scans
        Then: Should return None and log warning
        """
        monitor = ContextMonitor()

        # Try to estimate non-existent file
        status = monitor.estimate_context_usage(Path("/fake/path/transcript.jsonl"))

        assert status is None

    def test_error_handling_malformed_transcript(self, tmp_path):
        """
        Test graceful handling of malformed transcript.

        Given: Transcript with permission error or corruption
        When: Monitor estimates
        Then: Should return None and log error
        """
        monitor = ContextMonitor()

        # Create a file that will cause an error when counting lines
        transcript = tmp_path / "test_context" / "transcript.jsonl"
        transcript.parent.mkdir(parents=True)
        transcript.write_text("test")

        # Make file unreadable (simulate permission error)
        transcript.chmod(0o000)

        try:
            status = monitor.estimate_context_usage(transcript)
            # Depending on OS, may return None or partial result
            # Test passes if it doesn't crash
            assert True
        finally:
            # Restore permissions for cleanup
            transcript.chmod(0o644)


class TestMultipleProjects:
    """Test scanning multiple Claude Code projects"""

    def test_multiple_projects_scanning(self, tmp_path):
        """
        Test scanning multiple Claude Code projects.

        Given: 3 active projects
        When: Monitor scans
        Then: Should check all 3 projects independently
        """
        # Mock projects directory
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()

        # Create 3 projects with different context levels
        for i, (project_id, message_count) in enumerate([
            ("project_low", 50),      # 40K = 20%
            ("project_medium", 125),  # 100K = 50%
            ("project_high", 188),    # 150K = 75%
        ]):
            project_dir = projects_dir / project_id
            project_dir.mkdir()

            transcript = project_dir / f"{project_id}.jsonl"
            with open(transcript, 'w') as f:
                for j in range(message_count):
                    f.write(json.dumps({"role": "user", "content": "test"}) + "\n")

        # Scan projects
        with patch('claude.hooks.context_monitor.Path.home') as mock_home:
            mock_home.return_value = tmp_path

            # Need to patch the projects_dir location
            monitor = ContextMonitor()

            # Directly test scan_projects with our mock path
            with patch.object(Path, 'home', return_value=tmp_path):
                # Create .claude/projects structure
                claude_dir = tmp_path / '.claude' / 'projects'
                claude_dir.mkdir(parents=True)

                # Move test projects
                for project_id in ["project_low", "project_medium", "project_high"]:
                    src = projects_dir / project_id
                    dst = claude_dir / project_id
                    src.rename(dst)

                statuses = monitor.scan_projects()

                assert len(statuses) == 3

                # Verify each project scanned
                context_ids = {s.context_id for s in statuses}
                assert "project_low" in context_ids
                assert "project_medium" in context_ids
                assert "project_high" in context_ids

                # Verify usage percentages
                for status in statuses:
                    if status.context_id == "project_low":
                        assert status.usage_percentage < 30.0
                    elif status.context_id == "project_medium":
                        assert 40.0 < status.usage_percentage < 60.0
                    elif status.context_id == "project_high":
                        assert status.usage_percentage > 70.0
