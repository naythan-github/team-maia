#!/usr/bin/env python3
"""
Feature Tracker - TDD Enforcement Tool

Implements Anthropic's JSON feature list pattern for structural TDD enforcement.
Prevents Maia from skipping TDD by requiring feature tracking.

Usage:
    # Library
    from feature_tracker import FeatureTracker
    tracker = FeatureTracker()
    tracker.init("my_project")
    tracker.add("my_project", "User auth", category="api", priority=1)

    # CLI
    python3 feature_tracker.py init my_project
    python3 feature_tracker.py add my_project "User auth" --category api
    python3 feature_tracker.py next my_project
    python3 feature_tracker.py update my_project F001 --passes
    python3 feature_tracker.py summary my_project

Author: SRE Principal Engineer Agent (Maia)
Date: 2025-12-14
Version: 1.0
Status: Production Ready
"""

import json
import argparse
import shutil
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any


class FeatureTrackerError(Exception):
    """Base exception for Feature Tracker operations"""
    pass


class FeatureTracker:
    """
    TDD Enforcement Tool - Tracks features with pass/fail status.

    Provides structural enforcement of TDD workflow:
    - init: Forces requirements phase
    - add: Documents features before coding
    - next: Guides incremental work
    - update: Requires test results
    - summary: Objective progress tracking
    """

    SCHEMA_VERSION = "1.0"
    DEFAULT_MAX_ATTEMPTS = 5

    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize Feature Tracker.

        Args:
            data_dir: Directory for feature JSON files.
                     Defaults to claude/data/project_status/active/
        """
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            # Default: maia/claude/data/project_status/active/
            self.data_dir = Path(__file__).parent.parent.parent / "data" / "project_status" / "active"

        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, project: str) -> Path:
        """Get path to project features file."""
        return self.data_dir / f"{project}_features.json"

    def _get_backup_path(self, project: str) -> Path:
        """Get path to backup file."""
        return self.data_dir / f"{project}_features.json.backup"

    def _now_iso(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.utcnow().isoformat() + "Z"

    def _create_empty_schema(self, project: str) -> Dict[str, Any]:
        """Create empty project schema."""
        return {
            "schema_version": self.SCHEMA_VERSION,
            "project": project,
            "created": self._now_iso(),
            "last_updated": self._now_iso(),
            "features": [],
            "summary": {
                "total": 0,
                "passing": 0,
                "failing": 0,
                "blocked": 0,
                "completion_percentage": 0.0
            }
        }

    def _recalculate_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recalculate summary from features."""
        features = data["features"]
        total = len(features)
        passing = sum(1 for f in features if f["passes"])
        blocked = sum(1 for f in features if f["blocked"])
        failing = total - passing - blocked

        data["summary"] = {
            "total": total,
            "passing": passing,
            "failing": failing,
            "blocked": blocked,
            "completion_percentage": round((passing / total * 100) if total > 0 else 0.0, 1)
        }
        return data

    def _validate_schema(self, data: Dict[str, Any]) -> bool:
        """Validate JSON schema."""
        required_keys = ["schema_version", "project", "features", "summary"]
        return all(key in data for key in required_keys)

    def _atomic_write(self, project: str, data: Dict[str, Any]) -> None:
        """
        Atomic write with backup.

        NFR-1.1: tmp + rename prevents corruption
        NFR-1.2: Creates backup before overwrite
        """
        file_path = self._get_file_path(project)
        backup_path = self._get_backup_path(project)
        tmp_path = file_path.with_suffix(".tmp")

        # Create backup if file exists
        if file_path.exists():
            shutil.copy2(file_path, backup_path)

        # Update timestamp
        data["last_updated"] = self._now_iso()

        # Atomic write: write to tmp, then rename
        with open(tmp_path, 'w') as f:
            json.dump(data, f, indent=2)

        tmp_path.replace(file_path)

    def _generate_id(self, features: List[Dict]) -> str:
        """Generate next feature ID (F001, F002, etc.)."""
        if not features:
            return "F001"

        # Extract numeric parts and find max
        max_num = 0
        for f in features:
            try:
                num = int(f["id"][1:])
                max_num = max(max_num, num)
            except (ValueError, KeyError, IndexError):
                pass

        return f"F{max_num + 1:03d}"

    # =========================================================================
    # Public API
    # =========================================================================

    def init(self, project: str, force: bool = False) -> Dict[str, Any]:
        """
        Initialize a new project feature tracker.

        FR-1.1: Creates {project}_features.json
        FR-1.3: Starts with 0 features
        FR-1.4: Fails if exists (unless force=True)

        Args:
            project: Project name
            force: Overwrite if exists

        Returns:
            Result dict with success status
        """
        file_path = self._get_file_path(project)

        if file_path.exists() and not force:
            return {
                "success": False,
                "error": f"Project '{project}' already exists. Use force=True to overwrite."
            }

        data = self._create_empty_schema(project)
        self._atomic_write(project, data)

        return {
            "success": True,
            "project": project,
            "file": str(file_path)
        }

    def load(self, project: str) -> Dict[str, Any]:
        """
        Load project features from JSON.

        NFR-1.3: Validates schema on load

        Args:
            project: Project name

        Returns:
            Project data dict

        Raises:
            FeatureTrackerError: If file missing or invalid
        """
        file_path = self._get_file_path(project)

        if not file_path.exists():
            raise FeatureTrackerError(f"Project '{project}' not found at {file_path}")

        with open(file_path) as f:
            data = json.load(f)

        if not self._validate_schema(data):
            raise FeatureTrackerError(f"Invalid schema in {file_path}")

        return data

    def add(
        self,
        project: str,
        name: str,
        category: str = "general",
        priority: int = 1,
        verification: Optional[List[str]] = None,
        test_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add a new feature to track.

        FR-2.1: Creates feature with name, category, priority
        FR-2.2: Auto-generates ID
        FR-2.5: Defaults to passes=false, attempts=0

        Args:
            project: Project name
            name: Feature name
            category: Feature category
            priority: Priority (1=highest)
            verification: List of verification steps
            test_file: Path to test file

        Returns:
            Result dict with feature ID
        """
        try:
            data = self.load(project)
        except FeatureTrackerError as e:
            return {"success": False, "error": str(e)}

        feature_id = self._generate_id(data["features"])

        feature = {
            "id": feature_id,
            "name": name,
            "category": category,
            "priority": priority,
            "passes": False,
            "blocked": False,
            "block_reason": None,
            "verification": verification or [],
            "test_file": test_file,
            "last_tested": None,
            "attempts": 0,
            "max_attempts": self.DEFAULT_MAX_ATTEMPTS
        }

        data["features"].append(feature)
        data = self._recalculate_summary(data)
        self._atomic_write(project, data)

        return {
            "success": True,
            "id": feature_id,
            "name": name
        }

    def update(
        self,
        project: str,
        feature_id: str,
        passes: bool
    ) -> Dict[str, Any]:
        """
        Update feature pass/fail status.

        FR-3.1: --passes marks passing
        FR-3.2: --fails increments attempts
        FR-3.3: Recalculates summary
        FR-3.4: Records timestamp
        FR-4.1: Blocks at max_attempts

        Args:
            project: Project name
            feature_id: Feature ID (e.g., "F001")
            passes: True if test passed

        Returns:
            Result dict
        """
        try:
            data = self.load(project)
        except FeatureTrackerError as e:
            return {"success": False, "error": str(e)}

        # Find feature
        feature = None
        for f in data["features"]:
            if f["id"] == feature_id:
                feature = f
                break

        if not feature:
            return {"success": False, "error": f"Feature '{feature_id}' not found"}

        # Update status
        feature["passes"] = passes
        feature["last_tested"] = self._now_iso()

        if not passes:
            feature["attempts"] += 1

            # Circuit breaker
            if feature["attempts"] >= feature["max_attempts"]:
                feature["blocked"] = True
                feature["block_reason"] = f"Max attempts ({feature['max_attempts']}) reached - requires human intervention"
        else:
            # Reset on success
            feature["blocked"] = False
            feature["block_reason"] = None

        data = self._recalculate_summary(data)
        self._atomic_write(project, data)

        return {
            "success": True,
            "id": feature_id,
            "passes": passes,
            "attempts": feature["attempts"],
            "blocked": feature["blocked"]
        }

    def reset(self, project: str, feature_id: str) -> Dict[str, Any]:
        """
        Reset feature attempts and unblock.

        FR-4.3: Clears attempts, unblocks

        Args:
            project: Project name
            feature_id: Feature ID

        Returns:
            Result dict
        """
        try:
            data = self.load(project)
        except FeatureTrackerError as e:
            return {"success": False, "error": str(e)}

        for f in data["features"]:
            if f["id"] == feature_id:
                f["attempts"] = 0
                f["blocked"] = False
                f["block_reason"] = None
                break
        else:
            return {"success": False, "error": f"Feature '{feature_id}' not found"}

        data = self._recalculate_summary(data)
        self._atomic_write(project, data)

        return {"success": True, "id": feature_id}

    def next(self, project: str) -> Optional[Dict[str, Any]]:
        """
        Get next failing feature to work on.

        FR-5.1: Returns highest-priority failing (not blocked)
        FR-5.2: Returns None if all passing or blocked

        Args:
            project: Project name

        Returns:
            Feature dict or None
        """
        try:
            data = self.load(project)
        except FeatureTrackerError:
            return None

        # Filter to failing, non-blocked features
        candidates = [
            f for f in data["features"]
            if not f["passes"] and not f["blocked"]
        ]

        if not candidates:
            return None

        # Sort by priority (lowest number = highest priority)
        candidates.sort(key=lambda f: f["priority"])

        return candidates[0]

    def summary(self, project: str) -> Dict[str, Any]:
        """
        Get project summary.

        FR-5.3: Returns total/passing/failing/blocked/completion%

        Args:
            project: Project name

        Returns:
            Summary dict
        """
        try:
            data = self.load(project)
            return data["summary"]
        except FeatureTrackerError as e:
            return {"error": str(e)}

    def list_features(self, project: str) -> List[Dict[str, Any]]:
        """
        List all features.

        FR-5.4: Shows all features with status

        Args:
            project: Project name

        Returns:
            List of feature dicts
        """
        try:
            data = self.load(project)
            return data["features"]
        except FeatureTrackerError:
            return []

    def status(self, project: str) -> str:
        """
        Get formatted status for agent context injection.

        FR-6.1: Returns agent-injectable format
        FR-6.2: Includes next feature and verification

        Args:
            project: Project name

        Returns:
            Formatted status string
        """
        try:
            data = self.load(project)
        except FeatureTrackerError as e:
            return f"TDD Status: Error loading project - {e}"

        summary = data["summary"]
        next_feature = self.next(project)

        lines = [
            f"📋 TDD PROJECT: {project}",
            f"   Status: {summary['passing']}/{summary['total']} passing ({summary['completion_percentage']}%)",
        ]

        if summary["blocked"] > 0:
            lines.append(f"   ⚠️ Blocked: {summary['blocked']} features (need human intervention)")

        if next_feature:
            lines.append(f"")
            lines.append(f"   Next: {next_feature['name']} [{next_feature['id']}]")
            lines.append(f"   Priority: {next_feature['priority']} | Attempts: {next_feature['attempts']}/{next_feature['max_attempts']}")

            if next_feature["verification"]:
                lines.append(f"   Verification:")
                for step in next_feature["verification"]:
                    lines.append(f"     - {step}")

            if next_feature["test_file"]:
                lines.append(f"   Test: {next_feature['test_file']}")
        else:
            if summary["passing"] == summary["total"]:
                lines.append(f"")
                lines.append(f"   ✅ All features passing!")
            else:
                lines.append(f"")
                lines.append(f"   ⛔ All remaining features blocked")

        return "\n".join(lines)


# =============================================================================
# CLI Interface Helpers
# =============================================================================

def _create_argument_parser():
    """Create and configure argument parser for CLI.

    Returns:
        argparse.ArgumentParser: Configured parser with all subcommands
    """
    parser = argparse.ArgumentParser(
        description="Feature Tracker - TDD Enforcement Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument("--data-dir", type=Path, help="Data directory for JSON files")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # init
    init_parser = subparsers.add_parser("init", help="Initialize project")
    init_parser.add_argument("project", help="Project name")
    init_parser.add_argument("--force", action="store_true", help="Overwrite if exists")

    # add
    add_parser = subparsers.add_parser("add", help="Add feature")
    add_parser.add_argument("project", help="Project name")
    add_parser.add_argument("name", help="Feature name")
    add_parser.add_argument("--category", default="general", help="Category")
    add_parser.add_argument("--priority", type=int, default=1, help="Priority (1=highest)")
    add_parser.add_argument("--test", dest="test_file", help="Test file path")
    add_parser.add_argument("--verification", nargs="+", help="Verification steps")

    # update
    update_parser = subparsers.add_parser("update", help="Update feature status")
    update_parser.add_argument("project", help="Project name")
    update_parser.add_argument("feature_id", help="Feature ID (e.g., F001)")
    update_parser.add_argument("--passes", action="store_true", help="Mark as passing")
    update_parser.add_argument("--fails", action="store_true", help="Mark as failing")

    # next
    next_parser = subparsers.add_parser("next", help="Get next feature")
    next_parser.add_argument("project", help="Project name")

    # summary
    summary_parser = subparsers.add_parser("summary", help="Show summary")
    summary_parser.add_argument("project", help="Project name")

    # list
    list_parser = subparsers.add_parser("list", help="List all features")
    list_parser.add_argument("project", help="Project name")

    # status
    status_parser = subparsers.add_parser("status", help="Get formatted status")
    status_parser.add_argument("project", help="Project name")

    # reset
    reset_parser = subparsers.add_parser("reset", help="Reset feature attempts")
    reset_parser.add_argument("project", help="Project name")
    reset_parser.add_argument("feature_id", help="Feature ID")

    return parser


def _handle_command(tracker: FeatureTracker, args):
    """Dispatch command to appropriate tracker method.

    Args:
        tracker: FeatureTracker instance
        args: Parsed CLI arguments
    """
    if args.command == "init":
        result = tracker.init(args.project, force=args.force)
        if result["success"]:
            print(f"✅ Project '{args.project}' created at {result['file']}")
        else:
            print(f"❌ {result['error']}")
            sys.exit(1)

    elif args.command == "add":
        result = tracker.add(
            args.project,
            args.name,
            category=args.category,
            priority=args.priority,
            verification=args.verification,
            test_file=args.test_file
        )
        if result["success"]:
            print(f"✅ Added: {result['id']} - {result['name']}")
        else:
            print(f"❌ {result['error']}")
            sys.exit(1)

    elif args.command == "update":
        if not args.passes and not args.fails:
            print("❌ Must specify --passes or --fails")
            sys.exit(1)

        result = tracker.update(args.project, args.feature_id, passes=args.passes)
        if result["success"]:
            status = "✅ PASSING" if result["passes"] else "❌ FAILING"
            print(f"{status}: {result['id']} (attempt {result['attempts']})")
            if result["blocked"]:
                print("⚠️ Feature BLOCKED - max attempts reached")
        else:
            print(f"❌ {result['error']}")
            sys.exit(1)

    elif args.command == "next":
        feature = tracker.next(args.project)
        if feature:
            print(f"Next: {feature['id']} - {feature['name']} (priority {feature['priority']})")
        else:
            print("No pending features (all passing or blocked)")

    elif args.command == "summary":
        summary = tracker.summary(args.project)
        if "error" in summary:
            print(f"❌ {summary['error']}")
            sys.exit(1)
        print(f"Total: {summary['total']}")
        print(f"Passing: {summary['passing']}")
        print(f"Failing: {summary['failing']}")
        print(f"Blocked: {summary['blocked']}")
        print(f"Completion: {summary['completion_percentage']}%")

    elif args.command == "list":
        features = tracker.list_features(args.project)
        for f in features:
            status = "✅" if f["passes"] else ("⛔" if f["blocked"] else "❌")
            print(f"{status} {f['id']}: {f['name']} (P{f['priority']})")

    elif args.command == "status":
        print(tracker.status(args.project))

    elif args.command == "reset":
        result = tracker.reset(args.project, args.feature_id)
        if result["success"]:
            print(f"✅ Reset: {result['id']}")
        else:
            print(f"❌ {result['error']}")
            sys.exit(1)


# =============================================================================
# CLI Interface
# =============================================================================

def main():
    """CLI entry point."""
    parser = _create_argument_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    tracker = FeatureTracker(data_dir=args.data_dir)
    _handle_command(tracker, args)


if __name__ == "__main__":
    main()
