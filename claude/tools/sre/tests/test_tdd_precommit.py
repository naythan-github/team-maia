#!/usr/bin/env python3
"""
Test Suite for TDD Pre-Commit Hook

Tests for feature_tracker pre-commit validation.
Verifies commits are blocked when features are failing/blocked.

Run: python3 -m pytest claude/tools/sre/tests/test_tdd_precommit.py -v
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


class TestPreCommitValidation:
    """F001: Pre-commit validates features.json status"""

    def test_passes_when_no_features_json(self, tmp_path):
        """Passes when no TDD project exists"""
        result = validate_tdd_status(tmp_path)

        assert result["success"] is True
        assert result["reason"] == "no_project"

    def test_passes_when_all_features_passing(self, tmp_path):
        """Passes when all features are passing"""
        tracker = FeatureTracker(data_dir=tmp_path)
        tracker.init("test_project")
        tracker.add("test_project", "Feature 1")
        tracker.update("test_project", "F001", passes=True)

        result = validate_tdd_status(tmp_path)

        assert result["success"] is True
        assert result["reason"] == "all_passing"

    def test_blocks_when_features_failing(self, tmp_path):
        """Blocks when any feature is failing"""
        tracker = FeatureTracker(data_dir=tmp_path)
        tracker.init("test_project")
        tracker.add("test_project", "Feature 1")
        tracker.add("test_project", "Feature 2")
        tracker.update("test_project", "F001", passes=True)
        # F002 is failing (default)

        result = validate_tdd_status(tmp_path)

        assert result["success"] is False
        assert result["reason"] == "features_failing"
        assert result["failing_count"] == 1

    def test_blocks_when_features_blocked(self, tmp_path):
        """Blocks when any feature is blocked"""
        tracker = FeatureTracker(data_dir=tmp_path)
        tracker.init("test_project")
        tracker.add("test_project", "Feature 1")

        # Block the feature (5 failures)
        for _ in range(5):
            tracker.update("test_project", "F001", passes=False)

        result = validate_tdd_status(tmp_path)

        assert result["success"] is False
        assert result["reason"] == "features_blocked"
        assert result["blocked_count"] == 1


class TestActionableErrorMessages:
    """F002: Pre-commit provides actionable error message"""

    def test_error_shows_failing_features(self, tmp_path):
        """Error message lists failing features"""
        tracker = FeatureTracker(data_dir=tmp_path)
        tracker.init("test_project")
        tracker.add("test_project", "User auth")
        tracker.add("test_project", "Rate limiting")

        result = validate_tdd_status(tmp_path)
        message = format_error_message(result, "test_project")

        assert "User auth" in message or "F001" in message
        assert "Rate limiting" in message or "F002" in message

    def test_error_shows_fix_commands(self, tmp_path):
        """Error message shows commands to fix"""
        tracker = FeatureTracker(data_dir=tmp_path)
        tracker.init("test_project")
        tracker.add("test_project", "Feature 1")

        result = validate_tdd_status(tmp_path)
        message = format_error_message(result, "test_project")

        assert "feature_tracker.py update" in message
        assert "--passes" in message

    def test_error_shows_bypass_option(self, tmp_path):
        """Error message shows bypass option"""
        tracker = FeatureTracker(data_dir=tmp_path)
        tracker.init("test_project")
        tracker.add("test_project", "Feature 1")

        result = validate_tdd_status(tmp_path)
        message = format_error_message(result, "test_project")

        assert "--no-verify" in message
        assert "TDD_EXEMPTIONS" in message or "justification" in message.lower()


class TestAutoPromptTDDInit:
    """F003: Auto-prompt TDD initialization for dev tasks"""

    def test_detects_dev_task_without_project(self, tmp_path):
        """Detects development task when no features.json"""
        query = "build a new tool for processing data"

        result = check_tdd_init_needed(query, tmp_path)

        assert result["needs_init"] is True
        assert "init" in result["suggestion"].lower()

    def test_suggests_project_name(self, tmp_path):
        """Suggests project name from context"""
        query = "create a data_processor tool"

        result = check_tdd_init_needed(query, tmp_path)

        assert result["needs_init"] is True
        assert "data_processor" in result["suggested_name"] or "data" in result["suggested_name"]

    def test_no_prompt_when_project_exists(self, tmp_path):
        """No prompt when TDD project already exists"""
        tracker = FeatureTracker(data_dir=tmp_path)
        tracker.init("existing_project")

        query = "build a new feature"
        result = check_tdd_init_needed(query, tmp_path)

        assert result["needs_init"] is False


class TestHookIntegration:
    """F004: Integration with existing pre-commit hook"""

    def test_hook_returns_exit_code_0_on_success(self, tmp_path):
        """Returns exit code 0 when validation passes"""
        # No project = success
        exit_code = run_tdd_precommit_check(tmp_path)

        assert exit_code == 0

    def test_hook_returns_exit_code_1_on_failure(self, tmp_path):
        """Returns exit code 1 when validation fails"""
        tracker = FeatureTracker(data_dir=tmp_path)
        tracker.init("test_project")
        tracker.add("test_project", "Failing feature")

        exit_code = run_tdd_precommit_check(tmp_path)

        assert exit_code == 1

    def test_hook_performance_under_100ms(self, tmp_path):
        """Hook completes in <100ms"""
        import time

        tracker = FeatureTracker(data_dir=tmp_path)
        tracker.init("test_project")
        for i in range(10):
            tracker.add("test_project", f"Feature {i}")

        start = time.time()
        run_tdd_precommit_check(tmp_path)
        elapsed = (time.time() - start) * 1000

        assert elapsed < 100, f"Hook took {elapsed:.1f}ms, expected <100ms"


# =============================================================================
# Implementation Functions (to be moved to hook module)
# =============================================================================

def validate_tdd_status(data_dir: Path) -> dict:
    """
    Validate TDD project status for pre-commit.

    Returns:
        {
            "success": bool,
            "reason": "no_project" | "all_passing" | "features_failing" | "features_blocked",
            "failing_count": int,
            "blocked_count": int,
            "project": str | None
        }
    """
    # Find most recent features.json
    features_files = list(data_dir.glob("*_features.json"))

    if not features_files:
        return {"success": True, "reason": "no_project", "project": None}

    # Sort by modification time
    features_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    most_recent = features_files[0]
    project_name = most_recent.stem.replace("_features", "")

    try:
        with open(most_recent, 'r') as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"success": True, "reason": "no_project", "project": None}

    summary = data.get("summary", {})
    failing = summary.get("failing", 0)
    blocked = summary.get("blocked", 0)

    if blocked > 0:
        return {
            "success": False,
            "reason": "features_blocked",
            "blocked_count": blocked,
            "failing_count": failing,
            "project": project_name,
            "features": data.get("features", [])
        }

    if failing > 0:
        return {
            "success": False,
            "reason": "features_failing",
            "failing_count": failing,
            "blocked_count": 0,
            "project": project_name,
            "features": data.get("features", [])
        }

    return {
        "success": True,
        "reason": "all_passing",
        "project": project_name
    }


def format_error_message(result: dict, project: str) -> str:
    """Format actionable error message for pre-commit failure."""
    lines = [
        "❌ TDD PRE-COMMIT CHECK FAILED",
        "",
        f"Project: {project}",
    ]

    if result.get("reason") == "features_failing":
        lines.append(f"Failing features: {result.get('failing_count', 0)}")
    if result.get("reason") == "features_blocked":
        lines.append(f"Blocked features: {result.get('blocked_count', 0)}")

    # List failing/blocked features
    features = result.get("features", [])
    failing_features = [f for f in features if not f.get("passes") and not f.get("blocked")]
    blocked_features = [f for f in features if f.get("blocked")]

    if failing_features:
        lines.append("")
        lines.append("Failing:")
        for f in failing_features[:5]:
            lines.append(f"  - {f.get('id', '?')}: {f.get('name', 'Unknown')}")

    if blocked_features:
        lines.append("")
        lines.append("Blocked (need reset):")
        for f in blocked_features[:5]:
            lines.append(f"  - {f.get('id', '?')}: {f.get('name', 'Unknown')}")

    # Fix commands
    lines.extend([
        "",
        "To fix:",
        f"  python3 claude/tools/sre/feature_tracker.py update {project} <ID> --passes",
        f"  python3 claude/tools/sre/feature_tracker.py reset {project} <ID>  # for blocked",
        "",
        "To bypass (requires justification):",
        "  git commit --no-verify",
        "  # Document in claude/data/TDD_EXEMPTIONS.md"
    ])

    return "\n".join(lines)


def check_tdd_init_needed(query: str, data_dir: Path) -> dict:
    """
    Check if TDD initialization should be prompted.

    Returns:
        {
            "needs_init": bool,
            "suggestion": str,
            "suggested_name": str
        }
    """
    # Check if any features.json exists
    features_files = list(data_dir.glob("*_features.json"))
    if features_files:
        return {"needs_init": False, "suggestion": "", "suggested_name": ""}

    # Check if this looks like a development task
    dev_indicators = [
        "create", "build", "implement", "add", "write", "develop",
        "tool", "agent", "feature", "script", "function", "class"
    ]

    query_lower = query.lower()
    dev_score = sum(1 for indicator in dev_indicators if indicator in query_lower)

    if dev_score < 2:
        return {"needs_init": False, "suggestion": "", "suggested_name": ""}

    # Extract potential project name
    import re
    words = re.findall(r'\b[a-z_]+\b', query_lower)
    project_words = [w for w in words if w not in ["a", "an", "the", "for", "to", "and", "or", "in", "on", "with"]]
    suggested_name = "_".join(project_words[:2]) if project_words else "new_project"

    suggestion = (
        f"TDD project recommended. Initialize with:\n"
        f"  python3 claude/tools/sre/feature_tracker.py init {suggested_name}"
    )

    return {
        "needs_init": True,
        "suggestion": suggestion,
        "suggested_name": suggested_name
    }


def run_tdd_precommit_check(data_dir: Path) -> int:
    """
    Run TDD pre-commit check.

    Returns:
        0 if success, 1 if failure
    """
    result = validate_tdd_status(data_dir)

    if result["success"]:
        return 0

    # Print error message
    message = format_error_message(result, result.get("project", "unknown"))
    print(message)

    return 1
