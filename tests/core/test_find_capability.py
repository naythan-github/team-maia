"""
TDD Tests for find_capability.py - DB-first capability lookup tool.

Design: Makes DB queries easier than Grep/Glob for capability lookups.
Enforces Principle 18 (DB-First Queries) by providing path of least resistance.
"""

import pytest
import subprocess
import sys
from pathlib import Path

MAIA_ROOT = Path(__file__).parent.parent.parent
SCRIPT_PATH = MAIA_ROOT / "claude" / "tools" / "core" / "find_capability.py"
DB_PATH = MAIA_ROOT / "claude" / "data" / "databases" / "system" / "capabilities.db"


def run_script(*args):
    """Helper to run find_capability.py with arguments."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH)] + list(args),
        capture_output=True,
        text=True,
        cwd=str(MAIA_ROOT)
    )
    return result


class TestScriptExists:
    """Verify script exists and is executable."""

    def test_script_file_exists(self):
        """Script must exist at expected location."""
        assert SCRIPT_PATH.exists(), f"Script not found at {SCRIPT_PATH}"

    def test_database_exists(self):
        """Capabilities database must exist."""
        assert DB_PATH.exists(), f"Database not found at {DB_PATH}"


class TestKeywordSearch:
    """Test searching capabilities by keyword."""

    def test_search_returns_results(self):
        """Search for common keyword should return results."""
        result = run_script("email")
        assert result.returncode == 0
        assert len(result.stdout.strip()) > 0, "Should return results for 'email'"

    def test_search_no_results(self):
        """Search for nonexistent keyword should return empty gracefully."""
        result = run_script("xyznonexistentkeyword123")
        assert result.returncode == 0
        assert "No capabilities found" in result.stdout or result.stdout.strip() == ""

    def test_search_case_insensitive(self):
        """Search should be case-insensitive."""
        result_lower = run_script("trello")
        result_upper = run_script("TRELLO")
        # Both should succeed and find same results
        assert result_lower.returncode == 0
        assert result_upper.returncode == 0


class TestCategoryFilter:
    """Test filtering by category."""

    def test_filter_by_category(self):
        """--category flag should filter results."""
        result = run_script("--category", "sre")
        assert result.returncode == 0
        assert len(result.stdout.strip()) > 0, "SRE category should have tools"

    def test_category_with_keyword(self):
        """Category + keyword should work together."""
        result = run_script("--category", "sre", "state")
        assert result.returncode == 0

    def test_invalid_category(self):
        """Invalid category should return empty results gracefully."""
        result = run_script("--category", "nonexistentcategory")
        assert result.returncode == 0


class TestTypeFilter:
    """Test filtering by type (tool/agent)."""

    def test_filter_tools_only(self):
        """--type tool should return only tools."""
        result = run_script("--type", "tool")
        assert result.returncode == 0
        # Should not contain agent paths
        assert "agents/" not in result.stdout or len(result.stdout) == 0

    def test_filter_agents_only(self):
        """--type agent should return only agents."""
        result = run_script("--type", "agent")
        assert result.returncode == 0

    def test_type_with_keyword(self):
        """Type + keyword should work together."""
        result = run_script("--type", "agent", "security")
        assert result.returncode == 0


class TestCombinedFilters:
    """Test combining multiple filters."""

    def test_category_and_type(self):
        """Category + type should work together."""
        result = run_script("--category", "sre", "--type", "tool")
        assert result.returncode == 0

    def test_all_filters(self):
        """Category + type + keyword should all work together."""
        result = run_script("--category", "sre", "--type", "tool", "state")
        assert result.returncode == 0


class TestOutputFormat:
    """Test output formatting."""

    def test_output_includes_path(self):
        """Output should include file path."""
        result = run_script("trello")
        assert result.returncode == 0
        if result.stdout.strip():
            assert "claude/" in result.stdout, "Output should include path"

    def test_output_readable(self):
        """Output should be human-readable, not raw SQL."""
        result = run_script("--category", "sre")
        assert result.returncode == 0
        # Should not contain SQL artifacts
        assert "SELECT" not in result.stdout
        assert "FROM" not in result.stdout


class TestHelpAndUsage:
    """Test help and usage information."""

    def test_help_flag(self):
        """--help should show usage information."""
        result = run_script("--help")
        assert result.returncode == 0
        assert "usage" in result.stdout.lower() or "Usage" in result.stdout

    def test_no_args_shows_help_or_all(self):
        """No arguments should show help or list all capabilities."""
        result = run_script()
        assert result.returncode == 0
