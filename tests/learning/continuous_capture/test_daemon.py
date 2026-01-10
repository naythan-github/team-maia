#!/usr/bin/env python3
"""
Phase 6: Continuous Capture Daemon - TDD Tests

Tests for ContinuousCaptureDaemon that orchestrates the full capture cycle:
- Scans active Claude projects
- Loads state (high-water marks)
- Extracts learnings incrementally
- Writes to queue files
- Handles errors gracefully
- Shutdown management
"""

import pytest
import json
import time
import threading
from pathlib import Path
from datetime import datetime

from claude.tools.learning.continuous_capture.daemon import ContinuousCaptureDaemon


class TestDaemonBasics:
    """Test basic daemon functionality."""

    def test_scans_all_active_projects(self, tmp_path):
        """Should discover and scan all active Claude projects."""
        # Create mock Claude projects directory structure
        projects_dir = tmp_path / "projects"

        # Create 3 mock projects
        project_contexts = ['ctx_1', 'ctx_2', 'ctx_3']
        for ctx in project_contexts:
            project_dir = projects_dir / ctx
            project_dir.mkdir(parents=True)

            # Create transcript with some messages
            transcript = project_dir / "transcript.jsonl"
            messages = [
                {"type": "user_message", "content": f"test message in {ctx}"},
                {"type": "assistant_message", "content": f"decided to use TDD for {ctx}"}
            ]
            with open(transcript, 'w') as f:
                for msg in messages:
                    f.write(json.dumps(msg) + '\n')

        # Create daemon configured to scan mock directory
        queue_dir = tmp_path / "queue"
        state_dir = tmp_path / "state"

        daemon = ContinuousCaptureDaemon(
            projects_dir=projects_dir,
            queue_dir=queue_dir,
            state_dir=state_dir,
            scan_interval=0  # No sleep for testing
        )

        # Run single capture cycle
        projects_scanned = daemon.scan_projects()

        # Should discover all 3 projects
        assert len(projects_scanned) == 3, "Should discover all active projects"

        # Verify context IDs match
        scanned_ids = {p['context_id'] for p in projects_scanned}
        assert scanned_ids == set(project_contexts), "Should identify correct context IDs"

    def test_respects_scan_interval(self, tmp_path):
        """Daemon should wait specified interval between scans."""
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()

        daemon = ContinuousCaptureDaemon(
            projects_dir=projects_dir,
            scan_interval=0.1  # 100ms for testing
        )

        # Start daemon in background thread
        daemon_thread = threading.Thread(target=daemon.run, daemon=True)

        start_time = time.time()
        daemon_thread.start()

        # Let it run for ~250ms (should complete 2-3 cycles)
        time.sleep(0.25)
        daemon.stop()
        daemon_thread.join(timeout=1)

        elapsed = time.time() - start_time

        # Should have completed multiple cycles (not blocking)
        assert daemon.cycles_completed >= 2, "Should respect scan interval"
        assert elapsed < 0.5, "Should not block excessively"

    def test_handles_project_errors_gracefully(self, tmp_path):
        """Should continue processing other projects if one fails."""
        projects_dir = tmp_path / "projects"

        # Create 3 projects: 1 valid, 1 malformed transcript, 1 empty
        # Valid project
        valid_dir = projects_dir / "valid_ctx"
        valid_dir.mkdir(parents=True)
        valid_transcript = valid_dir / "transcript.jsonl"
        with open(valid_transcript, 'w') as f:
            f.write('{"type": "assistant_message", "content": "fixed bug"}\n')

        # Malformed transcript
        malformed_dir = projects_dir / "malformed_ctx"
        malformed_dir.mkdir(parents=True)
        malformed_transcript = malformed_dir / "transcript.jsonl"
        with open(malformed_transcript, 'w') as f:
            f.write('not valid json\n')

        # Empty project
        empty_dir = projects_dir / "empty_ctx"
        empty_dir.mkdir(parents=True)
        empty_transcript = empty_dir / "transcript.jsonl"
        empty_transcript.touch()  # Empty file

        queue_dir = tmp_path / "queue"
        state_dir = tmp_path / "state"

        daemon = ContinuousCaptureDaemon(
            projects_dir=projects_dir,
            queue_dir=queue_dir,
            state_dir=state_dir,
            scan_interval=0
        )

        # Should not crash on malformed data
        projects_scanned = daemon.scan_projects()

        # Should scan all 3 (even if some fail)
        assert len(projects_scanned) >= 1, "Should process valid projects despite errors"

        # Should capture from valid project
        daemon.capture_cycle()

        # Verify valid project was processed (queue file created)
        queue_files = list(queue_dir.glob('*.json'))
        # May or may not create queue file depending on extraction results
        # Main test: daemon didn't crash

    def test_shutdown_gracefully(self, tmp_path):
        """Daemon should handle shutdown signals cleanly."""
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()

        daemon = ContinuousCaptureDaemon(
            projects_dir=projects_dir,
            scan_interval=1.0  # Long interval
        )

        # Start in background
        daemon_thread = threading.Thread(target=daemon.run, daemon=True)
        daemon_thread.start()

        # Let it start
        time.sleep(0.1)

        # Request shutdown
        daemon.stop()

        # Should stop within reasonable time
        daemon_thread.join(timeout=2.0)

        assert not daemon_thread.is_alive(), "Daemon should stop cleanly"
        assert daemon.shutdown_requested, "Should record shutdown request"


class TestDaemonCaptureIntegration:
    """Test full capture cycle integration."""

    def test_full_capture_cycle(self, tmp_path):
        """Should execute complete capture cycle: state → extract → queue → update state."""
        # Setup project with transcript
        projects_dir = tmp_path / "projects"
        project_dir = projects_dir / "test_ctx_123"
        project_dir.mkdir(parents=True)

        transcript = project_dir / "transcript.jsonl"
        messages = [
            {"type": "user_message", "content": "Please fix the bug"},
            {"type": "assistant_message", "content": "Fixed the bug by adding validation"},
            {"type": "user_message", "content": "Now optimize it"},
            {"type": "assistant_message", "content": "Optimized from 2s to 50ms using caching"}
        ]
        with open(transcript, 'w') as f:
            for msg in messages:
                f.write(json.dumps(msg) + '\n')

        queue_dir = tmp_path / "queue"
        state_dir = tmp_path / "state"

        daemon = ContinuousCaptureDaemon(
            projects_dir=projects_dir,
            queue_dir=queue_dir,
            state_dir=state_dir,
            scan_interval=0
        )

        # Run capture cycle
        daemon.capture_cycle()

        # Verify state file created
        state_files = list(state_dir.glob('test_ctx_123.json'))
        assert len(state_files) == 1, "Should create state file"

        # Verify state updated
        with open(state_files[0]) as f:
            state = json.load(f)

        assert state['last_message_index'] == 4, "Should update high-water mark to end"
        assert state['last_message_count'] == 4, "Should record message count"

        # Verify queue file created (if learnings extracted)
        queue_files = list(queue_dir.glob('*.json'))
        # May be 0 or 1 depending on extraction results

        # Run second cycle with no new messages
        daemon.capture_cycle()

        # State should remain same (no new messages)
        with open(state_files[0]) as f:
            state2 = json.load(f)

        assert state2['last_message_index'] == 4, "Should not change when no new messages"

    def test_survives_simulated_compaction(self, tmp_path):
        """Should detect compaction and reset high-water mark."""
        projects_dir = tmp_path / "projects"
        project_dir = projects_dir / "compaction_test_ctx"
        project_dir.mkdir(parents=True)

        transcript = project_dir / "transcript.jsonl"

        # Initial transcript (10 messages)
        initial_messages = [
            {"type": "assistant_message", "content": f"message {i}"}
            for i in range(10)
        ]
        with open(transcript, 'w') as f:
            for msg in initial_messages:
                f.write(json.dumps(msg) + '\n')

        queue_dir = tmp_path / "queue"
        state_dir = tmp_path / "state"

        daemon = ContinuousCaptureDaemon(
            projects_dir=projects_dir,
            queue_dir=queue_dir,
            state_dir=state_dir,
            scan_interval=0
        )

        # First capture (process all 10 messages)
        daemon.capture_cycle()

        # Verify state
        state_file = state_dir / "compaction_test_ctx.json"
        with open(state_file) as f:
            state1 = json.load(f)

        assert state1['last_message_count'] == 10
        assert state1['compaction_count'] == 0  # No compaction yet

        # SIMULATE COMPACTION: Replace transcript with only 3 messages
        compacted_messages = [
            {"type": "assistant_message", "content": "compacted message 0"},
            {"type": "assistant_message", "content": "compacted message 1"},
            {"type": "assistant_message", "content": "discovered compaction"}
        ]
        with open(transcript, 'w') as f:
            for msg in compacted_messages:
                f.write(json.dumps(msg) + '\n')

        # Second capture (should detect compaction)
        daemon.capture_cycle()

        # Verify compaction detected
        with open(state_file) as f:
            state2 = json.load(f)

        assert state2['last_message_count'] == 3, "Should update to new count"
        assert state2['compaction_count'] == 1, "Should increment compaction count"
        assert state2['last_message_index'] == 3, "Should reset high-water mark"

        # Verify learnings extracted from new transcript
        # (compaction creates fresh context to re-extract)

    def test_incremental_processing_on_new_messages(self, tmp_path):
        """Should process only new messages in subsequent cycles."""
        projects_dir = tmp_path / "projects"
        project_dir = projects_dir / "incremental_ctx"
        project_dir.mkdir(parents=True)

        transcript = project_dir / "transcript.jsonl"

        # Initial 5 messages
        initial_messages = [
            {"type": "assistant_message", "content": f"initial message {i}"}
            for i in range(5)
        ]
        with open(transcript, 'w') as f:
            for msg in initial_messages:
                f.write(json.dumps(msg) + '\n')

        queue_dir = tmp_path / "queue"
        state_dir = tmp_path / "state"

        daemon = ContinuousCaptureDaemon(
            projects_dir=projects_dir,
            queue_dir=queue_dir,
            state_dir=state_dir,
            scan_interval=0
        )

        # First cycle - process all 5
        daemon.capture_cycle()

        state_file = state_dir / "incremental_ctx.json"
        with open(state_file) as f:
            state1 = json.load(f)

        assert state1['last_message_index'] == 5

        # Add 3 new messages
        new_messages = [
            {"type": "assistant_message", "content": "new message 5"},
            {"type": "assistant_message", "content": "new message 6"},
            {"type": "assistant_message", "content": "discovered incremental capture works"}
        ]
        with open(transcript, 'a') as f:  # Append
            for msg in new_messages:
                f.write(json.dumps(msg) + '\n')

        # Second cycle - should process only new 3
        daemon.capture_cycle()

        with open(state_file) as f:
            state2 = json.load(f)

        assert state2['last_message_index'] == 8, "Should advance to end"
        assert state2['last_message_count'] == 8, "Should record new count"

        # Verify only new messages processed (implementation detail - extractor handles this)


class TestDaemonConfiguration:
    """Test daemon configuration options."""

    def test_custom_scan_interval(self, tmp_path):
        """Should accept custom scan interval."""
        daemon = ContinuousCaptureDaemon(
            projects_dir=tmp_path,
            scan_interval=2.5
        )

        assert daemon.scan_interval == 2.5, "Should use custom interval"

    def test_custom_directories(self, tmp_path):
        """Should accept custom queue and state directories."""
        custom_queue = tmp_path / "custom_queue"
        custom_state = tmp_path / "custom_state"

        daemon = ContinuousCaptureDaemon(
            projects_dir=tmp_path,
            queue_dir=custom_queue,
            state_dir=custom_state
        )

        # Directories should be created
        daemon.capture_cycle()

        assert custom_queue.exists(), "Should create custom queue dir"
        assert custom_state.exists(), "Should create custom state dir"

    def test_default_directories(self, tmp_path):
        """Should use sensible defaults if directories not specified."""
        daemon = ContinuousCaptureDaemon(
            projects_dir=tmp_path
        )

        # Should have default queue and state directories
        assert daemon.queue_dir is not None
        assert daemon.state_dir is not None
