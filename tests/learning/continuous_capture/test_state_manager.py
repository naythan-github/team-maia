#!/usr/bin/env python3
"""
Phase 2: High-Water Mark Tracking - TDD Tests

Tests for CaptureStateManager that tracks processing state per project.
"""

import pytest
import json
from pathlib import Path
from datetime import datetime

from claude.tools.learning.continuous_capture.state_manager import CaptureStateManager


class TestCaptureStateManager:
    """Test state manager for tracking capture progress."""

    def test_load_nonexistent_state_returns_defaults(self, tmp_path):
        """Loading state for new context should return default values."""
        manager = CaptureStateManager(state_dir=tmp_path)

        state = manager.load_state("new_context_123")

        assert state['context_id'] == "new_context_123"
        assert state['last_message_index'] == 0
        assert state['last_message_count'] == 0
        assert state['compaction_count'] == 0
        assert 'last_capture_timestamp' in state

    def test_save_and_load_state_roundtrip(self, tmp_path):
        """Saved state should persist and be retrievable."""
        manager = CaptureStateManager(state_dir=tmp_path)
        context_id = "test_ctx_456"

        # Save state
        manager.save_state(
            context_id=context_id,
            last_message_index=42,
            last_message_count=50,
            compaction_count=3
        )

        # Load state
        loaded = manager.load_state(context_id)

        assert loaded['context_id'] == context_id
        assert loaded['last_message_index'] == 42
        assert loaded['last_message_count'] == 50
        assert loaded['compaction_count'] == 3

    def test_state_persists_across_instances(self, tmp_path):
        """State should persist even when manager is recreated."""
        context_id = "persist_test"

        # First instance saves
        manager1 = CaptureStateManager(state_dir=tmp_path)
        manager1.save_state(
            context_id=context_id,
            last_message_index=100,
            last_message_count=120
        )

        # Second instance loads
        manager2 = CaptureStateManager(state_dir=tmp_path)
        loaded = manager2.load_state(context_id)

        assert loaded['last_message_index'] == 100
        assert loaded['last_message_count'] == 120

    def test_state_file_format(self, tmp_path):
        """State files should be valid JSON with correct structure."""
        manager = CaptureStateManager(state_dir=tmp_path)
        context_id = "format_test"

        manager.save_state(
            context_id=context_id,
            last_message_index=10,
            last_message_count=15
        )

        # Read file directly
        state_file = tmp_path / f"{context_id}.json"
        assert state_file.exists(), "State file should be created"

        with open(state_file) as f:
            data = json.load(f)

        assert 'context_id' in data
        assert 'last_message_index' in data
        assert 'last_message_count' in data
        assert 'last_capture_timestamp' in data
        assert 'compaction_count' in data


class TestCompactionDetection:
    """Test detection of compaction events."""

    def test_detects_compaction_when_message_count_decreases(self, tmp_path):
        """Should detect compaction when new count < stored count."""
        manager = CaptureStateManager(state_dir=tmp_path)
        context_id = "compaction_test_1"

        # Initial state: 100 messages processed
        manager.save_state(
            context_id=context_id,
            last_message_index=100,
            last_message_count=100
        )

        # Simulate compaction: message count dropped to 20
        is_compacted = manager.detect_compaction(context_id, current_message_count=20)

        assert is_compacted is True, "Should detect compaction when count decreases"

    def test_no_compaction_when_message_count_increases(self, tmp_path):
        """Should not detect compaction when count increases normally."""
        manager = CaptureStateManager(state_dir=tmp_path)
        context_id = "compaction_test_2"

        # Initial state: 50 messages
        manager.save_state(
            context_id=context_id,
            last_message_index=50,
            last_message_count=50
        )

        # Normal growth: count increased to 75
        is_compacted = manager.detect_compaction(context_id, current_message_count=75)

        assert is_compacted is False, "Should not detect compaction when count increases"

    def test_no_compaction_when_count_unchanged(self, tmp_path):
        """Should not detect compaction when count is same."""
        manager = CaptureStateManager(state_dir=tmp_path)
        context_id = "compaction_test_3"

        manager.save_state(
            context_id=context_id,
            last_message_index=30,
            last_message_count=30
        )

        # Same count
        is_compacted = manager.detect_compaction(context_id, current_message_count=30)

        assert is_compacted is False

    def test_resets_high_water_mark_on_compaction(self, tmp_path):
        """On compaction, should reset high-water mark to 0."""
        manager = CaptureStateManager(state_dir=tmp_path)
        context_id = "reset_test"

        # Initial state
        manager.save_state(
            context_id=context_id,
            last_message_index=100,
            last_message_count=100,
            compaction_count=2
        )

        # Handle compaction (count dropped to 25)
        manager.handle_compaction(context_id, new_message_count=25)

        # Load state and verify reset
        state = manager.load_state(context_id)

        assert state['last_message_index'] == 0, "High-water mark should reset to 0"
        assert state['last_message_count'] == 25, "Should update to new count"
        assert state['compaction_count'] == 3, "Should increment compaction counter"

    def test_first_run_with_no_state(self, tmp_path):
        """First run on a context should not falsely detect compaction."""
        manager = CaptureStateManager(state_dir=tmp_path)
        context_id = "first_run_test"

        # No state exists yet
        is_compacted = manager.detect_compaction(context_id, current_message_count=50)

        # Should not detect compaction on first run
        assert is_compacted is False

    def test_compaction_detection_threshold(self, tmp_path):
        """Should handle edge case near compaction threshold."""
        manager = CaptureStateManager(state_dir=tmp_path)
        context_id = "threshold_test"

        # Saved 100 messages
        manager.save_state(
            context_id=context_id,
            last_message_index=100,
            last_message_count=100
        )

        # Small decrease (99) - might be deletion, not compaction
        # Current implementation: any decrease = compaction
        is_compacted = manager.detect_compaction(context_id, current_message_count=99)
        assert is_compacted is True

    def test_update_high_water_mark(self, tmp_path):
        """Should update high-water mark for incremental processing."""
        manager = CaptureStateManager(state_dir=tmp_path)
        context_id = "update_test"

        # Initial: processed 50 out of 60 messages
        manager.save_state(
            context_id=context_id,
            last_message_index=50,
            last_message_count=60
        )

        # Now processed up to message 60
        manager.update_high_water_mark(context_id, new_index=60, message_count=60)

        state = manager.load_state(context_id)
        assert state['last_message_index'] == 60
        assert state['last_message_count'] == 60
