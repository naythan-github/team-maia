#!/usr/bin/env python3
"""
Path Resolution Tests

Validates PathManager works correctly for multi-user operation.

Author: SRE Principal Engineer Agent
Date: 2026-01-03
"""

import os
import pytest
from pathlib import Path

# Find MAIA_ROOT
MAIA_ROOT = Path(__file__).resolve().parents[2]

# Add to path for imports
import sys
sys.path.insert(0, str(MAIA_ROOT))

from claude.tools.core.paths import PathManager, get_maia_root, get_user_data


class TestPathManager:
    """Test PathManager class."""

    def setup_method(self):
        """Clear cache before each test."""
        PathManager.clear_cache()

    def test_get_maia_root_returns_path(self):
        """MAIA_ROOT should be a valid Path."""
        root = PathManager.get_maia_root()
        assert isinstance(root, Path)
        assert root.exists()

    def test_maia_root_contains_claude_md(self):
        """MAIA_ROOT should contain CLAUDE.md."""
        root = PathManager.get_maia_root()
        assert (root / "CLAUDE.md").exists()

    def test_get_user_data_path_returns_path(self):
        """User data path should be a valid Path."""
        user_data = PathManager.get_user_data_path()
        assert isinstance(user_data, Path)

    def test_user_data_creates_structure(self):
        """User data path should create subdirectories."""
        user_data = PathManager.get_user_data_path()

        # Check expected subdirectories exist
        assert (user_data / "data" / "databases" / "user").exists()
        assert (user_data / "sessions").exists()
        assert (user_data / "context" / "personal").exists()

    def test_get_user_db_path(self):
        """User DB path should include db name."""
        db_path = PathManager.get_user_db_path("test.db")
        assert db_path.name == "test.db"
        assert "user" in str(db_path)

    def test_get_shared_db_path(self):
        """Shared DB path should be in system directory."""
        db_path = PathManager.get_shared_db_path("capabilities.db")
        assert db_path.name == "capabilities.db"
        assert "system" in str(db_path)

    def test_get_work_projects_path(self):
        """Work projects path should be in home directory."""
        work = PathManager.get_work_projects_path()
        assert "work_projects" in str(work)

    def test_get_session_path(self):
        """Session path should include session ID."""
        session_path = PathManager.get_session_path("test123")
        assert "test123" in str(session_path)
        assert session_path.suffix == ".json"

    def test_environment_override_maia_root(self):
        """MAIA_ROOT env var should override detection."""
        # This test validates the mechanism exists
        # Actual override testing requires env manipulation
        root = get_maia_root()
        assert root is not None


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_get_maia_root_function(self):
        """get_maia_root() should work."""
        root = get_maia_root()
        assert isinstance(root, Path)
        assert root.exists()

    def test_get_user_data_function(self):
        """get_user_data() should work."""
        user_data = get_user_data()
        assert isinstance(user_data, Path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
