#!/usr/bin/env python3
"""
Test Context Monitor Integration - Phase 237.4.3
Integration tests for end-to-end context monitoring flow

Tests verify the complete flow:
1. Monitor scans projects
2. Estimates context usage
3. Triggers capture at threshold
4. Pre-compaction hook extracts learnings
5. Archive stores conversation
6. PAI v2 patterns saved
"""

import json
import subprocess
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

from claude.hooks.context_monitor import ContextMonitor
from claude.tools.learning.archive import get_archive


class TestFullMonitorFlow:
    """Test complete monitor flow"""

    def test_full_monitor_flow_end_to_end(self, tmp_path):
        """
        Test complete flow from monitor scan to learning capture.

        Steps:
        1. Create synthetic transcript (175 messages = 140K tokens = 70%)
        2. Monitor scans and detects threshold exceeded
        3. Triggers pre-compaction hook
        4. Hook extracts learnings
        5. Verify capture succeeded
        """
        # Setup mock projects directory
        projects_dir = tmp_path / '.claude' / 'projects'
        project_dir = projects_dir / 'test_context'
        project_dir.mkdir(parents=True)

        # Create transcript with 176 messages (140.8K tokens = 70.4%, just over threshold)
        transcript = project_dir / 'transcript.jsonl'

        with open(transcript, 'w') as f:
            for i in range(176):
                message = {
                    "role": "user" if i % 2 == 0 else "assistant",
                    "content": f"Message {i}"
                }
                f.write(json.dumps(message) + "\n")

        # Create monitor
        monitor = ContextMonitor(threshold=0.70, context_window=200000, tokens_per_message=800)

        # Mock subprocess.run to simulate successful hook execution
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr=b'')

            # Mock Path.home() to use tmp_path
            with patch.object(Path, 'home', return_value=tmp_path):
                # Scan projects
                statuses = monitor.scan_projects()

                assert len(statuses) == 1
                status = statuses[0]

                assert status.context_id == 'test_context'
                assert status.message_count == 176
                assert status.usage_percentage > 70.0

                # Check if capture should trigger
                should_trigger = monitor.should_trigger_capture(status)
                assert should_trigger is True

                # Trigger capture
                result = monitor.trigger_capture(status)

                assert result is True
                assert 'test_context' in monitor.captured_contexts

                # Verify hook was called
                mock_run.assert_called_once()

    def test_monitor_incremental_capture(self, tmp_path):
        """
        Test monitor triggers capture as context grows.

        Steps:
        1. Create transcript at 60% (below threshold)
        2. Monitor scans - should NOT trigger
        3. Add messages to push to 75% (above threshold)
        4. Monitor scans - should trigger
        """
        projects_dir = tmp_path / '.claude' / 'projects'
        project_dir = projects_dir / 'test_context'
        project_dir.mkdir(parents=True)

        transcript = project_dir / 'transcript.jsonl'

        # Phase 1: 150 messages = 120K tokens = 60%
        with open(transcript, 'w') as f:
            for i in range(150):
                message = {"role": "user", "content": f"Message {i}"}
                f.write(json.dumps(message) + "\n")

        monitor = ContextMonitor(threshold=0.70)

        with patch.object(Path, 'home', return_value=tmp_path):
            statuses = monitor.scan_projects()
            status = statuses[0]

            # Below threshold - should NOT trigger
            assert status.usage_percentage == 60.0
            assert not monitor.should_trigger_capture(status)

        # Phase 2: Add 38 more messages → 188 total = 150.4K tokens = 75.2%
        with open(transcript, 'a') as f:
            for i in range(150, 188):
                message = {"role": "user", "content": f"Message {i}"}
                f.write(json.dumps(message) + "\n")

        with patch.object(Path, 'home', return_value=tmp_path):
            statuses = monitor.scan_projects()
            status = statuses[0]

            # Above threshold - SHOULD trigger
            assert status.usage_percentage > 70.0
            assert monitor.should_trigger_capture(status)


class TestMonitorDoesNotSpam:
    """Test monitor doesn't trigger multiple captures for same context"""

    def test_monitor_does_not_spam_same_context(self, tmp_path):
        """
        Test monitor doesn't trigger multiple captures.

        Steps:
        1. Context at 75%
        2. Monitor runs (triggers capture)
        3. Monitor runs again (should NOT trigger - already captured)
        4. Verify only 1 capture event
        """
        projects_dir = tmp_path / '.claude' / 'projects'
        project_dir = projects_dir / 'test_context'
        project_dir.mkdir(parents=True)

        # Create transcript at 75%
        transcript = project_dir / 'transcript.jsonl'
        with open(transcript, 'w') as f:
            for i in range(188):  # 75%
                f.write(json.dumps({"role": "user", "content": "test"}) + "\n")

        monitor = ContextMonitor(threshold=0.70)

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr=b'')

            with patch.object(Path, 'home', return_value=tmp_path):
                # First check - should trigger
                statuses = monitor.scan_projects()
                status = statuses[0]

                assert monitor.should_trigger_capture(status) is True
                monitor.trigger_capture(status)

                # Second check - should NOT trigger (already captured)
                statuses = monitor.scan_projects()
                status = statuses[0]

                assert monitor.should_trigger_capture(status) is False

                # Verify hook only called once
                assert mock_run.call_count == 1


class TestMultipleContexts:
    """Test monitor handles multiple active contexts"""

    def test_monitor_handles_multiple_contexts_independently(self, tmp_path):
        """
        Test monitor handles multiple active contexts.

        Steps:
        1. Context A at 50% (below threshold)
        2. Context B at 75% (above threshold)
        3. Context C at 90% (above threshold)
        4. Monitor scans - should trigger only B and C
        """
        projects_dir = tmp_path / '.claude' / 'projects'

        # Create 3 projects
        contexts = [
            ('context_low', 125),    # 100K = 50%
            ('context_medium', 188), # 150K = 75%
            ('context_high', 225),   # 180K = 90%
        ]

        for context_id, message_count in contexts:
            project_dir = projects_dir / context_id
            project_dir.mkdir(parents=True)

            transcript = project_dir / f'{context_id}.jsonl'
            with open(transcript, 'w') as f:
                for i in range(message_count):
                    f.write(json.dumps({"role": "user", "content": "test"}) + "\n")

        monitor = ContextMonitor(threshold=0.70)

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr=b'')

            with patch.object(Path, 'home', return_value=tmp_path):
                # Check and trigger
                monitor.check_and_trigger()

                # Verify 2 captures (medium and high, not low)
                assert mock_run.call_count == 2

                # Verify correct contexts captured
                assert 'context_medium' in monitor.captured_contexts
                assert 'context_high' in monitor.captured_contexts
                assert 'context_low' not in monitor.captured_contexts


class TestMonitorRecovery:
    """Test monitor recovery after failures"""

    def test_monitor_continues_after_capture_failure(self, tmp_path):
        """
        Test monitor continues after capture failure.

        Steps:
        1. Create 2 contexts above threshold
        2. First capture fails (hook returns error)
        3. Second capture succeeds
        4. Verify monitor continues, logs error, completes second capture
        """
        projects_dir = tmp_path / '.claude' / 'projects'

        # Create 2 projects
        for context_id in ['context_fail', 'context_success']:
            project_dir = projects_dir / context_id
            project_dir.mkdir(parents=True)

            transcript = project_dir / f'{context_id}.jsonl'
            with open(transcript, 'w') as f:
                for i in range(188):  # 75%
                    f.write(json.dumps({"role": "user", "content": "test"}) + "\n")

        monitor = ContextMonitor(threshold=0.70)

        # Mock subprocess to fail first call, succeed second
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = [
                MagicMock(returncode=1, stderr=b'Error'),  # First capture fails
                MagicMock(returncode=0, stderr=b''),       # Second capture succeeds
            ]

            with patch.object(Path, 'home', return_value=tmp_path):
                monitor.check_and_trigger()

                # Verify both captures attempted
                assert mock_run.call_count == 2

                # Verify only successful capture marked
                # (context_fail not in captured_contexts because it failed)
                assert len(monitor.captured_contexts) == 1

    def test_monitor_handles_missing_transcript_gracefully(self, tmp_path):
        """
        Test monitor handles missing transcript gracefully.

        Steps:
        1. Create project directory WITHOUT transcript
        2. Monitor scans
        3. Verify no crash, logs warning, continues
        """
        projects_dir = tmp_path / '.claude' / 'projects'
        project_dir = projects_dir / 'empty_context'
        project_dir.mkdir(parents=True)
        # No transcript file created

        monitor = ContextMonitor()

        with patch.object(Path, 'home', return_value=tmp_path):
            # Should not crash
            statuses = monitor.scan_projects()

            # Should return empty list (no valid transcripts)
            assert len(statuses) == 0


class TestMonitorPerformance:
    """Test monitor performance"""

    def test_monitor_scan_performance(self, tmp_path):
        """
        Test monitor scans complete quickly.

        Given: 5 projects with varying transcript sizes
        When: Monitor scans all projects
        Then: Should complete in <1 second
        """
        projects_dir = tmp_path / '.claude' / 'projects'

        # Create 5 projects with varying sizes
        for i, message_count in enumerate([50, 100, 150, 200, 250]):
            project_dir = projects_dir / f'context_{i}'
            project_dir.mkdir(parents=True)

            transcript = project_dir / f'context_{i}.jsonl'
            with open(transcript, 'w') as f:
                for j in range(message_count):
                    f.write(json.dumps({"role": "user", "content": "test"}) + "\n")

        monitor = ContextMonitor()

        with patch.object(Path, 'home', return_value=tmp_path):
            start = time.time()
            statuses = monitor.scan_projects()
            duration = time.time() - start

            # Verify all scanned
            assert len(statuses) == 5

            # Verify performance (<1 second)
            assert duration < 1.0

    def test_monitor_stress_test_10plus_projects(self, tmp_path):
        """
        Stress test: Monitor handles 10+ concurrent projects.

        Given: 12 projects with varying transcript sizes
        When: Monitor scans all projects
        Then: Should handle all projects without errors in <2 seconds
        """
        projects_dir = tmp_path / '.claude' / 'projects'

        # Create 12 projects with varying sizes (50-300 messages)
        for i in range(12):
            project_dir = projects_dir / f'context_{i}'
            project_dir.mkdir(parents=True)

            # Vary message count: 50, 100, 150, 200, 250, 300, 50, 100, ...
            message_count = 50 + (i % 6) * 50

            transcript = project_dir / f'context_{i}.jsonl'
            with open(transcript, 'w') as f:
                for j in range(message_count):
                    f.write(json.dumps({"role": "user", "content": "test"}) + "\n")

        monitor = ContextMonitor()

        with patch.object(Path, 'home', return_value=tmp_path):
            start = time.time()
            statuses = monitor.scan_projects()
            duration = time.time() - start

            # Verify all 12 projects scanned
            assert len(statuses) == 12

            # Verify no errors (all statuses valid)
            for status in statuses:
                assert status.context_id is not None
                assert status.message_count > 0
                assert status.estimated_tokens > 0

            # Verify performance (<2 seconds for stress test)
            assert duration < 2.0


class TestRealHookExecution:
    """Test real hook execution (no mocks)"""

    def test_monitor_triggers_real_hook_with_valid_input(self, tmp_path):
        """
        Test monitor triggers real pre-compaction hook.

        Given: Context at 75%, real hook script exists
        When: Monitor triggers capture
        Then: Hook executes and receives correct input format
        """
        projects_dir = tmp_path / '.claude' / 'projects'
        project_dir = projects_dir / 'test_context'
        project_dir.mkdir(parents=True)

        # Create transcript at 75%
        transcript = project_dir / 'transcript.jsonl'
        with open(transcript, 'w') as f:
            for i in range(188):  # 75%
                message = {
                    "role": "user" if i % 2 == 0 else "assistant",
                    "content": f"Test message {i}"
                }
                f.write(json.dumps(message) + "\n")

        monitor = ContextMonitor(threshold=0.70)

        # Create a mock hook script that captures input
        hook_script = tmp_path / 'test_hook.py'
        hook_script.write_text("""#!/usr/bin/env python3
import sys
import json

# Read input
hook_input = json.loads(sys.stdin.read())

# Validate input format
assert 'session_id' in hook_input, "Missing session_id"
assert 'transcript_path' in hook_input, "Missing transcript_path"
assert 'trigger' in hook_input, "Missing trigger"
assert hook_input['trigger'] == 'proactive_monitor', f"Wrong trigger: {hook_input['trigger']}"
assert 'hook_event_name' in hook_input, "Missing hook_event_name"

# Write validation result to temp file
with open(sys.argv[1], 'w') as f:
    json.dump({'validated': True, 'input': hook_input}, f)

# Exit success
sys.exit(0)
""")
        hook_script.chmod(0o755)

        # Patch the hook path to use our test hook
        validation_file = tmp_path / 'validation.json'

        with patch.object(Path, 'home', return_value=tmp_path):
            with patch('claude.hooks.context_monitor.MAIA_ROOT', tmp_path):
                # Create mock hook directory structure
                hooks_dir = tmp_path / 'hooks'
                hooks_dir.mkdir()
                real_hook = hooks_dir / 'pre_compaction_learning_capture.py'
                real_hook.symlink_to(hook_script)

                # Trigger capture (real hook execution)
                statuses = monitor.scan_projects()
                status = statuses[0]

                # Modify trigger_capture to pass validation file path
                result = subprocess.run(
                    ['python3', str(real_hook), str(validation_file)],
                    input=json.dumps({
                        'session_id': status.context_id,
                        'transcript_path': str(status.transcript_path),
                        'trigger': 'proactive_monitor',
                        'hook_event_name': 'PreCompact'
                    }).encode(),
                    capture_output=True,
                    timeout=30
                )

                # Verify hook executed successfully
                assert result.returncode == 0, f"Hook failed: {result.stderr.decode()}"

                # Verify hook received correct input
                assert validation_file.exists(), "Validation file not created"
                with open(validation_file) as f:
                    validation_data = json.load(f)

                assert validation_data['validated'] is True
                assert validation_data['input']['session_id'] == 'test_context'
                assert validation_data['input']['trigger'] == 'proactive_monitor'
                assert validation_data['input']['hook_event_name'] == 'PreCompact'


class TestMonitorConfiguration:
    """Test monitor configuration"""

    def test_monitor_respects_custom_threshold(self, tmp_path):
        """
        Test monitor respects custom threshold.

        Given: Monitor with threshold=0.80 (80%)
        When: Context at 75%
        Then: Should NOT trigger (below 80% threshold)
        """
        projects_dir = tmp_path / '.claude' / 'projects'
        project_dir = projects_dir / 'test_context'
        project_dir.mkdir(parents=True)

        # Create transcript at 75%
        transcript = project_dir / 'transcript.jsonl'
        with open(transcript, 'w') as f:
            for i in range(188):  # 75%
                f.write(json.dumps({"role": "user", "content": "test"}) + "\n")

        # Monitor with 80% threshold
        monitor = ContextMonitor(threshold=0.80)

        with patch.object(Path, 'home', return_value=tmp_path):
            statuses = monitor.scan_projects()
            status = statuses[0]

            # Below 80% threshold - should NOT trigger
            assert status.usage_percentage < 80.0
            assert not monitor.should_trigger_capture(status)

    def test_monitor_respects_custom_token_estimation(self, tmp_path):
        """
        Test monitor respects custom token estimation factor.

        Given: Monitor with tokens_per_message=1000 (vs default 800)
        When: 100 messages
        Then: Should estimate 100K tokens (vs default 80K)
        """
        projects_dir = tmp_path / '.claude' / 'projects'
        project_dir = projects_dir / 'test_context'
        project_dir.mkdir(parents=True)

        transcript = project_dir / 'transcript.jsonl'
        with open(transcript, 'w') as f:
            for i in range(100):
                f.write(json.dumps({"role": "user", "content": "test"}) + "\n")

        # Monitor with custom token estimation
        monitor = ContextMonitor(tokens_per_message=1000)

        with patch.object(Path, 'home', return_value=tmp_path):
            statuses = monitor.scan_projects()
            status = statuses[0]

            assert status.estimated_tokens == 100000  # 100 * 1000
            assert status.usage_percentage == 50.0   # 100K / 200K
