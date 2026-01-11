"""Test PAI v2 learning system integration."""

import pytest
import json
import tempfile
from pathlib import Path
from claude.hooks.session_handoffs import HandoffPatternTracker


class TestLearningSystemIntegration:
    """Test PAI v2 learning system integration."""

    def test_patterns_stored_after_successful_handoffs(self):
        """Successful handoffs are stored as patterns."""
        storage = Path(tempfile.gettempdir()) / "test_patterns_success.json"
        # Clean up any existing file
        if storage.exists():
            storage.unlink()
        tracker = HandoffPatternTracker(storage_path=storage)

        # Log successful handoffs
        tracker.log_handoff("sre", "security", "Security review", True)
        tracker.log_handoff("security", "devops", "CI/CD integration", True)

        patterns = tracker.get_patterns()

        assert len(patterns) == 2
        assert all(p["success"] for p in patterns)

    def test_failed_handoffs_logged_with_error_context(self):
        """Failed handoffs are logged with success=False."""
        storage = Path(tempfile.gettempdir()) / "test_patterns_failure.json"
        # Clean up any existing file
        if storage.exists():
            storage.unlink()
        tracker = HandoffPatternTracker(storage_path=storage)

        # Log failed handoff
        tracker.log_handoff(
            from_agent="sre",
            to_agent="nonexistent",
            query="Test query",
            success=False
        )

        patterns = tracker.get_patterns()

        failed = [p for p in patterns if not p["success"]]
        assert len(failed) >= 1
        # Verify the failed handoff was logged correctly
        assert failed[0]["from"] == "sre"
        assert failed[0]["to"] == "nonexistent"
        assert failed[0]["success"] is False

    def test_pattern_retrieval_for_analytics(self):
        """Patterns can be retrieved for analytics."""
        storage = Path(tempfile.gettempdir()) / "test_patterns_analytics.json"
        # Clean up any existing file
        if storage.exists():
            storage.unlink()
        tracker = HandoffPatternTracker(storage_path=storage)

        # Create diverse patterns
        tracker.log_handoff("a", "b", "q1", True)
        tracker.log_handoff("a", "b", "q2", True)
        tracker.log_handoff("a", "c", "q3", True)
        tracker.log_handoff("b", "c", "q4", False)

        stats = tracker.get_pattern_stats("a", "b")

        assert stats["count"] == 2
        assert stats["success_rate"] == 1.0

    def test_cross_session_pattern_aggregation(self):
        """Patterns persist across tracker instances."""
        storage = Path(tempfile.gettempdir()) / "test_patterns_persist.json"
        # Clean up any existing file
        if storage.exists():
            storage.unlink()

        # First session
        tracker1 = HandoffPatternTracker(storage_path=storage)
        tracker1.log_handoff("x", "y", "query1", True)

        # Second session (new instance)
        tracker2 = HandoffPatternTracker(storage_path=storage)
        tracker2.log_handoff("x", "y", "query2", True)

        # Third session should see both
        tracker3 = HandoffPatternTracker(storage_path=storage)
        patterns = tracker3.get_patterns()

        xy_patterns = [p for p in patterns if p["from"] == "x" and p["to"] == "y"]
        assert len(xy_patterns) >= 2
