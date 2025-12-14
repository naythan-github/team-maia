#!/usr/bin/env python3
"""
Test Suite for TDD Hook Integration

Tests for feature_tracker integration with swarm_auto_loader.
Verifies TDD state is loaded and injected into agent context.

Run: python3 -m pytest claude/tools/sre/tests/test_tdd_hook_integration.py -v
"""

import pytest
import json
import tempfile
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "hooks"))

from feature_tracker import FeatureTracker


class TestFeatureTrackerStateLoading:
    """F001: Load feature tracker state on session startup"""

    def test_finds_active_features_json(self, tmp_path):
        """Finds active features.json in project_status/active/"""
        # Create a features file
        tracker = FeatureTracker(data_dir=tmp_path)
        tracker.init("test_project")
        tracker.add("test_project", "Feature 1", priority=1)

        # Verify file exists
        features_file = tmp_path / "test_project_features.json"
        assert features_file.exists()

    def test_returns_tdd_context_if_project_active(self, tmp_path):
        """Returns TDD context when project has features.json"""
        tracker = FeatureTracker(data_dir=tmp_path)
        tracker.init("active_project")
        tracker.add("active_project", "Auth feature", priority=1)

        # Get status (simulates what hook would call)
        status = tracker.status("active_project")

        assert "active_project" in status
        assert "0/1" in status or "passing" in status.lower()
        assert "Auth feature" in status

    def test_returns_empty_if_no_active_project(self, tmp_path):
        """Returns None/empty when no features.json exists"""
        tracker = FeatureTracker(data_dir=tmp_path)

        # Try to load non-existent project
        features = tracker.list_features("nonexistent")

        assert features == []

    def test_loads_next_feature_details(self, tmp_path):
        """Loads next feature with verification steps"""
        tracker = FeatureTracker(data_dir=tmp_path)
        tracker.init("test_project")
        tracker.add(
            "test_project",
            "User auth",
            priority=1,
            verification=["POST returns 200", "Token valid"]
        )

        next_feature = tracker.next("test_project")

        assert next_feature is not None
        assert next_feature["name"] == "User auth"
        assert "POST returns 200" in next_feature["verification"]

    def test_skips_passing_features(self, tmp_path):
        """next() skips features that are passing"""
        tracker = FeatureTracker(data_dir=tmp_path)
        tracker.init("test_project")
        tracker.add("test_project", "Feature 1", priority=1)
        tracker.add("test_project", "Feature 2", priority=2)

        # Mark first as passing
        tracker.update("test_project", "F001", passes=True)

        next_feature = tracker.next("test_project")

        assert next_feature["id"] == "F002"
        assert next_feature["name"] == "Feature 2"


class TestTDDContextInjection:
    """F002: Inject TDD status into agent context"""

    def test_status_format_for_context_injection(self, tmp_path):
        """status() returns agent-injectable format"""
        tracker = FeatureTracker(data_dir=tmp_path)
        tracker.init("my_project")
        tracker.add("my_project", "Feature A", verification=["Step 1"])

        status = tracker.status("my_project")

        # Should contain key elements for agent context
        assert "TDD PROJECT" in status
        assert "my_project" in status
        assert "0/1" in status
        assert "Feature A" in status
        assert "Step 1" in status

    def test_status_shows_blocked_features(self, tmp_path):
        """status() shows blocked feature count"""
        tracker = FeatureTracker(data_dir=tmp_path)
        tracker.init("my_project")
        tracker.add("my_project", "Blocked feature")

        # Block the feature
        for _ in range(5):
            tracker.update("my_project", "F001", passes=False)

        status = tracker.status("my_project")

        assert "Blocked" in status or "blocked" in status.lower()

    def test_status_shows_completion_when_all_passing(self, tmp_path):
        """status() shows completion message when all pass"""
        tracker = FeatureTracker(data_dir=tmp_path)
        tracker.init("my_project")
        tracker.add("my_project", "Only feature")
        tracker.update("my_project", "F001", passes=True)

        status = tracker.status("my_project")

        assert "passing" in status.lower() or "100" in status or "✅" in status


class TestDevelopmentTaskDetection:
    """F003: Detect development tasks needing TDD"""

    def test_identifies_tool_development(self):
        """Identifies tool creation as development task"""
        dev_keywords = [
            "create a tool",
            "build a new feature",
            "implement feature",
            "add functionality",
            "write a script",
            "develop an agent"
        ]

        for keyword in dev_keywords:
            assert _is_development_task(keyword), f"Should detect: {keyword}"

    def test_ignores_non_development(self):
        """Ignores queries that aren't development"""
        non_dev = [
            "what time is it",
            "explain this code",
            "how does X work",
            "search for files"
        ]

        for query in non_dev:
            assert not _is_development_task(query), f"Should ignore: {query}"

    def test_checks_features_json_exists(self, tmp_path):
        """Checks if features.json exists for detected project"""
        tracker = FeatureTracker(data_dir=tmp_path)

        # No project initialized
        assert not (tmp_path / "new_tool_features.json").exists()

        # After init
        tracker.init("new_tool")
        assert (tmp_path / "new_tool_features.json").exists()


class TestMultipleProjectSupport:
    """Support for multiple concurrent TDD projects"""

    def test_lists_all_active_projects(self, tmp_path):
        """Can list all active TDD projects"""
        tracker = FeatureTracker(data_dir=tmp_path)
        tracker.init("project_a")
        tracker.init("project_b")
        tracker.init("project_c")

        # List all features files
        active_projects = list(tmp_path.glob("*_features.json"))

        assert len(active_projects) == 3

    def test_independent_project_tracking(self, tmp_path):
        """Projects tracked independently"""
        tracker = FeatureTracker(data_dir=tmp_path)
        tracker.init("project_a")
        tracker.init("project_b")

        tracker.add("project_a", "Feature A1")
        tracker.add("project_b", "Feature B1")
        tracker.add("project_b", "Feature B2")

        assert tracker.summary("project_a")["total"] == 1
        assert tracker.summary("project_b")["total"] == 2


# =============================================================================
# Helper Functions (to be implemented in hook)
# =============================================================================

def _is_development_task(query: str) -> bool:
    """
    Detect if a query is a development task requiring TDD.

    This will be integrated into the hook system.
    """
    dev_indicators = [
        "create", "build", "implement", "add", "write", "develop",
        "tool", "agent", "feature", "script", "function", "class",
        "fix bug", "refactor", "enhance", "modify"
    ]

    query_lower = query.lower()

    # Check for development indicators
    dev_score = sum(1 for indicator in dev_indicators if indicator in query_lower)

    # Non-development patterns
    non_dev_patterns = [
        "what", "how does", "explain", "search", "find", "list",
        "show me", "where is", "when", "why"
    ]

    non_dev_score = sum(1 for pattern in non_dev_patterns if query_lower.startswith(pattern))

    return dev_score >= 2 and non_dev_score == 0


def find_active_tdd_project(data_dir: Path) -> str:
    """
    Find the most recently modified TDD project.

    Returns project name or None.
    """
    features_files = list(data_dir.glob("*_features.json"))

    if not features_files:
        return None

    # Sort by modification time, most recent first
    features_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

    # Extract project name from filename
    most_recent = features_files[0]
    project_name = most_recent.stem.replace("_features", "")

    return project_name
