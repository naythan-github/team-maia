#!/usr/bin/env python3
"""
Test Suite for Feature Tracker - TDD Enforcement Tool

Tests written BEFORE implementation per TDD protocol.
Requirements: claude/data/project_status/active/feature_tracker_requirements.md

Run: python3 -m pytest claude/tools/sre/tests/test_feature_tracker.py -v
"""

import pytest
import json
import tempfile
import time
from pathlib import Path
from datetime import datetime
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from feature_tracker import FeatureTracker, FeatureTrackerError


class TestInitialization:
    """FR-1: Project Initialization"""

    def test_init_creates_json_file(self, tmp_path):
        """FR-1.1: init creates {project}_features.json"""
        tracker = FeatureTracker(data_dir=tmp_path)
        result = tracker.init("test_project")

        assert result["success"] is True
        assert (tmp_path / "test_project_features.json").exists()

    def test_init_creates_valid_schema(self, tmp_path):
        """FR-1.2: JSON schema includes required fields"""
        tracker = FeatureTracker(data_dir=tmp_path)
        tracker.init("test_project")

        with open(tmp_path / "test_project_features.json") as f:
            data = json.load(f)

        assert "schema_version" in data
        assert data["project"] == "test_project"
        assert "created" in data
        assert "features" in data
        assert "summary" in data

    def test_init_starts_empty(self, tmp_path):
        """FR-1.3: Initial state: 0 features, 0% completion"""
        tracker = FeatureTracker(data_dir=tmp_path)
        tracker.init("test_project")

        with open(tmp_path / "test_project_features.json") as f:
            data = json.load(f)

        assert len(data["features"]) == 0
        assert data["summary"]["total"] == 0
        assert data["summary"]["completion_percentage"] == 0.0

    def test_init_fails_if_exists(self, tmp_path):
        """FR-1.4: Fails gracefully if file exists"""
        tracker = FeatureTracker(data_dir=tmp_path)
        tracker.init("test_project")

        result = tracker.init("test_project")
        assert result["success"] is False
        assert "exists" in result["error"].lower()

    def test_init_force_overwrites(self, tmp_path):
        """FR-1.4: --force overwrites existing"""
        tracker = FeatureTracker(data_dir=tmp_path)
        tracker.init("test_project")
        tracker.add("test_project", "Feature 1")

        result = tracker.init("test_project", force=True)
        assert result["success"] is True

        with open(tmp_path / "test_project_features.json") as f:
            data = json.load(f)
        assert len(data["features"]) == 0


class TestFeatureManagement:
    """FR-2: Feature Management"""

    def test_add_creates_feature(self, tmp_path):
        """FR-2.1: add creates feature with name and category"""
        tracker = FeatureTracker(data_dir=tmp_path)
        tracker.init("test_project")

        result = tracker.add("test_project", "User auth", category="api", priority=1)

        assert result["success"] is True
        assert "id" in result

    def test_add_auto_generates_id(self, tmp_path):
        """FR-2.2: Auto-generates feature ID"""
        tracker = FeatureTracker(data_dir=tmp_path)
        tracker.init("test_project")

        result1 = tracker.add("test_project", "Feature 1")
        result2 = tracker.add("test_project", "Feature 2")

        assert result1["id"] == "F001"
        assert result2["id"] == "F002"

    def test_add_with_verification_steps(self, tmp_path):
        """FR-2.3: add with verification steps"""
        tracker = FeatureTracker(data_dir=tmp_path)
        tracker.init("test_project")

        tracker.add("test_project", "Login", verification=["POST returns 200", "Token in response"])

        data = tracker.load("test_project")
        feature = data["features"][0]

        assert len(feature["verification"]) == 2
        assert "POST returns 200" in feature["verification"]

    def test_add_with_test_file(self, tmp_path):
        """FR-2.4: add with test file link"""
        tracker = FeatureTracker(data_dir=tmp_path)
        tracker.init("test_project")

        tracker.add("test_project", "Login", test_file="tests/test_auth.py")

        data = tracker.load("test_project")
        assert data["features"][0]["test_file"] == "tests/test_auth.py"

    def test_add_defaults(self, tmp_path):
        """FR-2.5: New features default to passes=false, attempts=0"""
        tracker = FeatureTracker(data_dir=tmp_path)
        tracker.init("test_project")
        tracker.add("test_project", "Feature 1")

        data = tracker.load("test_project")
        feature = data["features"][0]

        assert feature["passes"] is False
        assert feature["attempts"] == 0
        assert feature["blocked"] is False


class TestStatusUpdates:
    """FR-3: Status Updates"""

    def test_update_passes(self, tmp_path):
        """FR-3.1: update --passes marks feature as passing"""
        tracker = FeatureTracker(data_dir=tmp_path)
        tracker.init("test_project")
        tracker.add("test_project", "Feature 1")

        result = tracker.update("test_project", "F001", passes=True)

        assert result["success"] is True
        data = tracker.load("test_project")
        assert data["features"][0]["passes"] is True

    def test_update_fails_increments_attempts(self, tmp_path):
        """FR-3.2: update --fails increments attempts"""
        tracker = FeatureTracker(data_dir=tmp_path)
        tracker.init("test_project")
        tracker.add("test_project", "Feature 1")

        tracker.update("test_project", "F001", passes=False)
        tracker.update("test_project", "F001", passes=False)

        data = tracker.load("test_project")
        assert data["features"][0]["attempts"] == 2

    def test_update_recalculates_summary(self, tmp_path):
        """FR-3.3: update recalculates summary"""
        tracker = FeatureTracker(data_dir=tmp_path)
        tracker.init("test_project")
        tracker.add("test_project", "Feature 1")
        tracker.add("test_project", "Feature 2")

        tracker.update("test_project", "F001", passes=True)

        data = tracker.load("test_project")
        assert data["summary"]["passing"] == 1
        assert data["summary"]["failing"] == 1
        assert data["summary"]["completion_percentage"] == 50.0

    def test_update_records_timestamp(self, tmp_path):
        """FR-3.4: update records last_tested timestamp"""
        tracker = FeatureTracker(data_dir=tmp_path)
        tracker.init("test_project")
        tracker.add("test_project", "Feature 1")

        before = datetime.utcnow().isoformat()
        tracker.update("test_project", "F001", passes=True)

        data = tracker.load("test_project")
        assert data["features"][0]["last_tested"] is not None
        assert data["features"][0]["last_tested"] >= before[:10]


class TestCircuitBreaker:
    """FR-4: Circuit Breaker"""

    def test_blocks_at_max_attempts(self, tmp_path):
        """FR-4.1: Feature blocked when attempts >= max_attempts"""
        tracker = FeatureTracker(data_dir=tmp_path)
        tracker.init("test_project")
        tracker.add("test_project", "Feature 1")

        # Fail 5 times (default max_attempts)
        for _ in range(5):
            tracker.update("test_project", "F001", passes=False)

        data = tracker.load("test_project")
        assert data["features"][0]["blocked"] is True

    def test_blocked_excluded_from_next(self, tmp_path):
        """FR-4.2: Blocked features excluded from next"""
        tracker = FeatureTracker(data_dir=tmp_path)
        tracker.init("test_project")
        tracker.add("test_project", "Feature 1", priority=1)
        tracker.add("test_project", "Feature 2", priority=2)

        # Block feature 1
        for _ in range(5):
            tracker.update("test_project", "F001", passes=False)

        result = tracker.next("test_project")
        assert result["id"] == "F002"

    def test_reset_clears_attempts(self, tmp_path):
        """FR-4.3: reset clears attempts and unblocks"""
        tracker = FeatureTracker(data_dir=tmp_path)
        tracker.init("test_project")
        tracker.add("test_project", "Feature 1")

        for _ in range(5):
            tracker.update("test_project", "F001", passes=False)

        tracker.reset("test_project", "F001")

        data = tracker.load("test_project")
        assert data["features"][0]["attempts"] == 0
        assert data["features"][0]["blocked"] is False

    def test_block_reason_recorded(self, tmp_path):
        """FR-4.4: Block reason recorded"""
        tracker = FeatureTracker(data_dir=tmp_path)
        tracker.init("test_project")
        tracker.add("test_project", "Feature 1")

        for _ in range(5):
            tracker.update("test_project", "F001", passes=False)

        data = tracker.load("test_project")
        assert data["features"][0]["block_reason"] is not None
        assert "max" in data["features"][0]["block_reason"].lower()


class TestProgressQueries:
    """FR-5: Progress Queries"""

    def test_next_returns_highest_priority(self, tmp_path):
        """FR-5.1: next returns highest-priority failing feature"""
        tracker = FeatureTracker(data_dir=tmp_path)
        tracker.init("test_project")
        tracker.add("test_project", "Low priority", priority=3)
        tracker.add("test_project", "High priority", priority=1)
        tracker.add("test_project", "Medium priority", priority=2)

        result = tracker.next("test_project")
        assert result["name"] == "High priority"

    def test_next_returns_none_when_all_passing(self, tmp_path):
        """FR-5.2: next returns None if all passing"""
        tracker = FeatureTracker(data_dir=tmp_path)
        tracker.init("test_project")
        tracker.add("test_project", "Feature 1")
        tracker.update("test_project", "F001", passes=True)

        result = tracker.next("test_project")
        assert result is None

    def test_next_returns_none_when_all_blocked(self, tmp_path):
        """FR-5.2: next returns None if all blocked"""
        tracker = FeatureTracker(data_dir=tmp_path)
        tracker.init("test_project")
        tracker.add("test_project", "Feature 1")

        for _ in range(5):
            tracker.update("test_project", "F001", passes=False)

        result = tracker.next("test_project")
        assert result is None

    def test_summary_returns_counts(self, tmp_path):
        """FR-5.3: summary returns accurate counts"""
        tracker = FeatureTracker(data_dir=tmp_path)
        tracker.init("test_project")
        tracker.add("test_project", "Feature 1")
        tracker.add("test_project", "Feature 2")
        tracker.add("test_project", "Feature 3")

        tracker.update("test_project", "F001", passes=True)
        for _ in range(5):
            tracker.update("test_project", "F002", passes=False)

        result = tracker.summary("test_project")

        assert result["total"] == 3
        assert result["passing"] == 1
        assert result["failing"] == 1
        assert result["blocked"] == 1

    def test_list_shows_all_features(self, tmp_path):
        """FR-5.4: list shows all features"""
        tracker = FeatureTracker(data_dir=tmp_path)
        tracker.init("test_project")
        tracker.add("test_project", "Feature 1")
        tracker.add("test_project", "Feature 2")

        result = tracker.list_features("test_project")

        assert len(result) == 2
        assert result[0]["id"] == "F001"
        assert result[1]["id"] == "F002"


class TestSessionIntegration:
    """FR-6: Session Integration"""

    def test_status_returns_formatted_output(self, tmp_path):
        """FR-6.1: status returns agent-injectable format"""
        tracker = FeatureTracker(data_dir=tmp_path)
        tracker.init("test_project")
        tracker.add("test_project", "User auth", verification=["Check login", "Check token"])

        result = tracker.status("test_project")

        assert "test_project" in result
        assert "0/1" in result or "passing" in result.lower()

    def test_status_includes_next_feature(self, tmp_path):
        """FR-6.2: Status includes next feature and verification"""
        tracker = FeatureTracker(data_dir=tmp_path)
        tracker.init("test_project")
        tracker.add("test_project", "User auth", verification=["Check login"])

        result = tracker.status("test_project")

        assert "User auth" in result
        assert "Check login" in result


class TestReliability:
    """NFR-1: Reliability"""

    def test_atomic_write_creates_backup(self, tmp_path):
        """NFR-1.2: Backup before write"""
        tracker = FeatureTracker(data_dir=tmp_path)
        tracker.init("test_project")
        tracker.add("test_project", "Feature 1")

        # Should create backup on subsequent writes
        tracker.add("test_project", "Feature 2")

        # Backup should exist after modification
        backup_file = tmp_path / "test_project_features.json.backup"
        assert backup_file.exists()

    def test_load_validates_schema(self, tmp_path):
        """NFR-1.3: Schema validation on load"""
        # Create invalid JSON
        invalid_file = tmp_path / "bad_project_features.json"
        invalid_file.write_text('{"invalid": "schema"}')

        tracker = FeatureTracker(data_dir=tmp_path)

        with pytest.raises(FeatureTrackerError):
            tracker.load("bad_project")

    def test_graceful_error_handling(self, tmp_path):
        """NFR-1.4: Never crash, return error dict"""
        tracker = FeatureTracker(data_dir=tmp_path)

        result = tracker.update("nonexistent", "F001", passes=True)

        assert result["success"] is False
        assert "error" in result


class TestPerformance:
    """NFR-2: Performance"""

    def test_operations_under_50ms(self, tmp_path):
        """NFR-2.1: All operations < 50ms"""
        tracker = FeatureTracker(data_dir=tmp_path)

        start = time.time()
        tracker.init("test_project")
        assert (time.time() - start) < 0.05

        start = time.time()
        tracker.add("test_project", "Feature 1")
        assert (time.time() - start) < 0.05

        start = time.time()
        tracker.update("test_project", "F001", passes=True)
        assert (time.time() - start) < 0.05

        start = time.time()
        tracker.next("test_project")
        assert (time.time() - start) < 0.05


class TestCLI:
    """CLI Interface Tests"""

    def test_cli_init(self, tmp_path):
        """CLI: init command works"""
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "feature_tracker", "--data-dir", str(tmp_path), "init", "cli_test"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        assert result.returncode == 0 or "created" in result.stdout.lower()

    def test_cli_summary(self, tmp_path):
        """CLI: summary command works"""
        tracker = FeatureTracker(data_dir=tmp_path)
        tracker.init("cli_test")
        tracker.add("cli_test", "Feature 1")

        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "feature_tracker", "--data-dir", str(tmp_path), "summary", "cli_test"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        assert "total" in result.stdout.lower() or result.returncode == 0
