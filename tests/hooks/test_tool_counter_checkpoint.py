#!/usr/bin/env python3
"""
Tests for Tool Counter Auto-Checkpoint (Phase 264.1)

Workaround for unreliable PreCompact hooks.
Tests the PostToolUse-based checkpoint triggering.

GitHub Issues Reference:
- #13572: PreCompact hook not triggered
- #13668: PreCompact receives empty transcript_path
- #10814: Hooks broken in v2.0.31
- #16047: Hooks stop after ~2.5 hours

Author: Maia (Phase 264.1)
Created: 2026-01-11
"""

import json
import pytest
import tempfile
import shutil
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime


# Import will fail until implementation exists
try:
    from claude.hooks.tool_output_capture import (
        get_tool_count,
        increment_tool_count,
        reset_tool_count,
        trigger_auto_checkpoint,
        maybe_auto_checkpoint,
        CHECKPOINT_INTERVAL,
    )
    IMPLEMENTATION_EXISTS = True
except ImportError:
    IMPLEMENTATION_EXISTS = False


@pytest.fixture
def temp_state_dir():
    """Create temporary state directory."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_counter_dir(temp_state_dir):
    """Patch COUNTER_DIR to use temp directory."""
    with patch('claude.hooks.tool_output_capture.COUNTER_DIR', temp_state_dir):
        yield temp_state_dir


class TestToolCounter:
    """Tests for tool count tracking."""

    @pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="Implementation not yet created")
    def test_get_tool_count_returns_zero_initially(self, mock_counter_dir):
        """Returns 0 when no counter file exists."""
        result = get_tool_count("test_session")
        assert result == 0

    @pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="Implementation not yet created")
    def test_increment_tool_count_increments(self, mock_counter_dir):
        """Increments counter and returns new value."""
        assert increment_tool_count("test_session") == 1
        assert increment_tool_count("test_session") == 2
        assert increment_tool_count("test_session") == 3

    @pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="Implementation not yet created")
    def test_get_tool_count_returns_current_value(self, mock_counter_dir):
        """Returns current counter value."""
        increment_tool_count("test_session")
        increment_tool_count("test_session")

        result = get_tool_count("test_session")
        assert result == 2

    @pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="Implementation not yet created")
    def test_reset_tool_count_resets_to_zero(self, mock_counter_dir):
        """Resets counter to 0."""
        increment_tool_count("test_session")
        increment_tool_count("test_session")

        reset_tool_count("test_session")

        result = get_tool_count("test_session")
        assert result == 0

    @pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="Implementation not yet created")
    def test_counter_persists_to_file(self, mock_counter_dir):
        """Counter is persisted to JSON file."""
        increment_tool_count("test_session")

        counter_file = mock_counter_dir / "tool_counter_test_session.json"
        assert counter_file.exists()

        data = json.loads(counter_file.read_text())
        assert data["count"] == 1
        assert "last_updated" in data

    @pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="Implementation not yet created")
    def test_separate_counters_per_session(self, mock_counter_dir):
        """Different sessions have separate counters."""
        increment_tool_count("session_a")
        increment_tool_count("session_a")
        increment_tool_count("session_b")

        assert get_tool_count("session_a") == 2
        assert get_tool_count("session_b") == 1


class TestAutoCheckpoint:
    """Tests for auto-checkpoint triggering."""

    @pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="Implementation not yet created")
    def test_maybe_auto_checkpoint_does_not_trigger_below_interval(self, mock_counter_dir):
        """Does not trigger checkpoint when below interval."""
        with patch('claude.hooks.tool_output_capture.CHECKPOINT_INTERVAL', 50):
            result = maybe_auto_checkpoint("test_session")

            assert result["checkpoint_triggered"] is False
            assert result["tool_count"] == 1
            assert result["next_checkpoint_in"] == 49

    @pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="Implementation not yet created")
    def test_maybe_auto_checkpoint_triggers_at_interval(self, mock_counter_dir):
        """Triggers checkpoint when count reaches interval."""
        with patch('claude.hooks.tool_output_capture.CHECKPOINT_INTERVAL', 3):
            with patch('claude.hooks.tool_output_capture.trigger_auto_checkpoint', return_value=True):
                # Count up to interval
                maybe_auto_checkpoint("test_session")  # 1
                maybe_auto_checkpoint("test_session")  # 2
                result = maybe_auto_checkpoint("test_session")  # 3 - trigger!

                assert result["checkpoint_triggered"] is True
                assert result["checkpoint_success"] is True

    @pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="Implementation not yet created")
    def test_maybe_auto_checkpoint_resets_after_success(self, mock_counter_dir):
        """Resets counter after successful checkpoint."""
        with patch('claude.hooks.tool_output_capture.CHECKPOINT_INTERVAL', 2):
            with patch('claude.hooks.tool_output_capture.trigger_auto_checkpoint', return_value=True):
                maybe_auto_checkpoint("test_session")  # 1
                result = maybe_auto_checkpoint("test_session")  # 2 - trigger!

                assert result["tool_count"] == 0

                # Next call should be 1 again
                result2 = maybe_auto_checkpoint("test_session")
                assert result2["tool_count"] == 1

    @pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="Implementation not yet created")
    def test_maybe_auto_checkpoint_handles_failure(self, mock_counter_dir):
        """Handles checkpoint failure gracefully."""
        with patch('claude.hooks.tool_output_capture.CHECKPOINT_INTERVAL', 2):
            with patch('claude.hooks.tool_output_capture.trigger_auto_checkpoint', return_value=False):
                maybe_auto_checkpoint("test_session")  # 1
                result = maybe_auto_checkpoint("test_session")  # 2 - trigger fails

                assert result["checkpoint_triggered"] is True
                assert result["checkpoint_success"] is False
                # Counter should NOT reset on failure
                assert result["tool_count"] == 2

    @pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="Implementation not yet created")
    def test_maybe_auto_checkpoint_disabled_by_env(self, mock_counter_dir):
        """Can be disabled via environment variable."""
        with patch('claude.hooks.tool_output_capture.CHECKPOINT_ENABLED', False):
            result = maybe_auto_checkpoint("test_session")

            assert result["checkpoint_enabled"] is False


class TestTriggerAutoCheckpoint:
    """Tests for the actual checkpoint trigger."""

    @pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="Implementation not yet created")
    def test_trigger_auto_checkpoint_calls_generator(self, mock_counter_dir):
        """Calls CheckpointGenerator.save_durable_checkpoint."""
        mock_generator = MagicMock()
        mock_generator.gather_state.return_value = MagicMock()
        mock_generator.save_durable_checkpoint.return_value = Path("/tmp/test.json")

        with patch('claude.tools.sre.checkpoint.CheckpointGenerator', return_value=mock_generator):
            result = trigger_auto_checkpoint("test_session")

            assert result is True
            mock_generator.save_durable_checkpoint.assert_called_once()

    @pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="Implementation not yet created")
    def test_trigger_auto_checkpoint_sets_metadata(self, mock_counter_dir):
        """Sets appropriate metadata on state."""
        mock_generator = MagicMock()
        mock_state = MagicMock()
        mock_generator.gather_state.return_value = mock_state
        mock_generator.save_durable_checkpoint.return_value = Path("/tmp/test.json")

        with patch('claude.tools.sre.checkpoint.CheckpointGenerator', return_value=mock_generator):
            trigger_auto_checkpoint("test_session")

            assert mock_state.phase_name == "Auto-checkpoint (tool counter)"
            assert mock_state.context_id == "test_session"

    @pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="Implementation not yet created")
    def test_trigger_auto_checkpoint_returns_false_on_error(self, mock_counter_dir):
        """Returns False on error (non-blocking)."""
        with patch('claude.tools.sre.checkpoint.CheckpointGenerator', side_effect=Exception("Test error")):
            result = trigger_auto_checkpoint("test_session")

            assert result is False


class TestProcessToolOutputIntegration:
    """Integration tests for full hook flow."""

    @pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="Implementation not yet created")
    def test_process_tool_output_includes_checkpoint_status(self, mock_counter_dir):
        """process_tool_output includes checkpoint information."""
        from claude.hooks.tool_output_capture import process_tool_output

        with patch('claude.hooks.tool_output_capture.capture_to_uocs', return_value={'captured': True}):
            input_data = {
                'session_id': 'test_session',
                'tool_name': 'Read',
                'tool_input': {},
                'tool_response': {},
            }

            result = process_tool_output(input_data)

            assert 'checkpoint' in result
            assert 'tool_count' in result['checkpoint']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
