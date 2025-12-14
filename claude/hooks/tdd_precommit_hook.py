#!/usr/bin/env python3
"""
TDD Pre-Commit Hook - Feature Tracker Validation

Phase 221.2: Pre-commit hook that validates TDD project status.
Blocks commits when features are failing or blocked.

Usage:
    As git hook: ln -sf ../../claude/hooks/tdd_precommit_hook.py .git/hooks/pre-commit
    Direct run: python3 claude/hooks/tdd_precommit_hook.py

Exit codes:
    0 - Success (no project or all passing)
    1 - Failure (features failing or blocked)

Performance: <100ms
"""

import json
import sys
from pathlib import Path

# Determine Maia root
SCRIPT_DIR = Path(__file__).parent
MAIA_ROOT = SCRIPT_DIR.parent.parent

# TDD project data directory
TDD_DATA_DIR = MAIA_ROOT / "claude" / "data" / "project_status" / "active"


def validate_tdd_status() -> dict:
    """
    Validate TDD project status for pre-commit.

    Returns:
        {
            "success": bool,
            "reason": "no_project" | "all_passing" | "features_failing" | "features_blocked",
            "failing_count": int,
            "blocked_count": int,
            "project": str | None,
            "features": list
        }
    """
    if not TDD_DATA_DIR.exists():
        return {"success": True, "reason": "no_project", "project": None}

    # Find most recent features.json
    features_files = list(TDD_DATA_DIR.glob("*_features.json"))

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


def format_error_message(result: dict) -> str:
    """Format actionable error message for pre-commit failure."""
    project = result.get("project", "unknown")

    lines = [
        "",
        "=" * 60,
        "❌ TDD PRE-COMMIT CHECK FAILED",
        "=" * 60,
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
        lines.append("📋 Failing (need to pass tests):")
        for f in failing_features[:5]:
            lines.append(f"  - {f.get('id', '?')}: {f.get('name', 'Unknown')}")
        if len(failing_features) > 5:
            lines.append(f"  ... and {len(failing_features) - 5} more")

    if blocked_features:
        lines.append("")
        lines.append("🚫 Blocked (need reset after fixing root cause):")
        for f in blocked_features[:5]:
            lines.append(f"  - {f.get('id', '?')}: {f.get('name', 'Unknown')}")

    # Fix commands
    lines.extend([
        "",
        "🔧 To fix:",
        f"  # Mark feature as passing after tests pass:",
        f"  python3 claude/tools/sre/feature_tracker.py update {project} <ID> --passes",
        "",
        f"  # Reset blocked feature after fixing root cause:",
        f"  python3 claude/tools/sre/feature_tracker.py reset {project} <ID>",
        "",
        f"  # Check current status:",
        f"  python3 claude/tools/sre/feature_tracker.py status {project}",
        "",
        "⚠️  To bypass (use sparingly):",
        "  git commit --no-verify",
        "  # Document justification in claude/data/TDD_EXEMPTIONS.md",
        "",
        "=" * 60,
        ""
    ])

    return "\n".join(lines)


def main():
    """Main entry point for pre-commit hook."""
    result = validate_tdd_status()

    if result["success"]:
        # Optional: Print success message
        if result.get("project"):
            print(f"✅ TDD check passed: {result['project']} ({result['reason']})")
        return 0

    # Print error message
    print(format_error_message(result), file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
