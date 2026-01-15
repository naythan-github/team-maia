"""
Tests for Script MAIA_ROOT Usage

Verifies that critical scripts use get_maia_root() for dynamic detection
instead of hardcoded Path(__file__) patterns.

Sprint: SPRINT-001-REPO-SYNC
Story: 1.2 - Update All Scripts to Use get_maia_root()
Phase: P0 - Test-First Design

Created: 2026-01-15
"""

import pytest
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from claude.tools.core.paths import get_maia_root, clear_maia_root_cache


class TestSaveStateUsage:
    """Test save_state.py uses dynamic MAIA_ROOT detection."""

    def setup_method(self):
        """Clear cache before each test."""
        clear_maia_root_cache()

    def test_save_state_uses_get_maia_root(self):
        """
        Test save_state.py uses get_maia_root() not hardcoded path.

        Given: CWD is team-maia repository
        When: SaveState instantiated
        Then: maia_root uses team-maia path (not hardcoded)
        """
        from claude.tools.sre.save_state import SaveState

        test_repo = Path('/Users/username/team-maia')

        # Mock validation to accept test path
        def mock_is_valid(path):
            return path == test_repo

        with patch.dict(os.environ, {}, clear=True):  # Clear env vars
            with patch('claude.tools.core.paths._is_valid_maia_repo', side_effect=mock_is_valid):
                with patch('pathlib.Path.cwd', return_value=test_repo):
                    clear_maia_root_cache()

                    # Create SaveState instance
                    save_state = SaveState()

                    # Should use dynamic detection, not hardcoded
                    assert save_state.maia_root == test_repo

    def test_save_state_respects_env_var(self):
        """
        Test save_state respects MAIA_ROOT environment variable.

        Given: MAIA_ROOT env var set
        When: SaveState instantiated
        Then: Uses env var path
        """
        from claude.tools.sre.save_state import SaveState

        test_repo = Path('/Users/username/team-maia')

        with patch.dict(os.environ, {'MAIA_ROOT': str(test_repo)}):
            with patch('claude.tools.core.paths._is_valid_maia_repo', return_value=True):
                clear_maia_root_cache()

                save_state = SaveState()
                assert save_state.maia_root == test_repo


class TestSwarmAutoLoaderUsage:
    """Test swarm_auto_loader.py uses dynamic MAIA_ROOT detection."""

    def test_swarm_auto_loader_uses_get_maia_root(self):
        """
        Test swarm_auto_loader.py uses get_maia_root().

        Given: Module imported with CWD in team-maia
        When: MAIA_ROOT accessed
        Then: Uses dynamic detection
        """
        test_repo = Path('/Users/username/team-maia')

        # Mock validation
        def mock_is_valid(path):
            return path == test_repo

        with patch.dict(os.environ, {}, clear=True):  # Clear env vars
            with patch('claude.tools.core.paths._is_valid_maia_repo', side_effect=mock_is_valid):
                with patch('pathlib.Path.cwd', return_value=test_repo):
                    clear_maia_root_cache()

                    # Re-import to pick up new MAIA_ROOT
                    import importlib
                    import claude.hooks.swarm_auto_loader as sal
                    importlib.reload(sal)

                    # Should use dynamic detection
                    assert sal.MAIA_ROOT == test_repo

    def test_swarm_auto_loader_switches_repos(self):
        """
        Test swarm_auto_loader can switch repos when cache cleared.

        Given: MAIA_ROOT was personal repo
        When: Cache cleared and CWD changed to work repo
        Then: New import uses work repo
        """
        personal_repo = Path('/Users/username/maia')
        work_repo = Path('/Users/username/team-maia')

        def mock_is_valid(path):
            return path in [personal_repo, work_repo]

        with patch.dict(os.environ, {}, clear=True):  # Clear env vars
            with patch('claude.tools.core.paths._is_valid_maia_repo', side_effect=mock_is_valid):
                # First: personal repo
                with patch('pathlib.Path.cwd', return_value=personal_repo):
                    clear_maia_root_cache()
                    import importlib
                    import claude.hooks.swarm_auto_loader as sal
                    importlib.reload(sal)
                    assert sal.MAIA_ROOT == personal_repo

                # Then: work repo
                with patch('pathlib.Path.cwd', return_value=work_repo):
                    clear_maia_root_cache()
                    importlib.reload(sal)
                    assert sal.MAIA_ROOT == work_repo


class TestSmartContextLoaderUsage:
    """Test smart_context_loader.py uses dynamic MAIA_ROOT detection."""

    def test_smart_context_loader_uses_get_maia_root(self):
        """
        Test smart_context_loader.py uses get_maia_root().

        Given: Script run from team-maia
        When: MAIA_ROOT referenced
        Then: Uses team-maia path
        """
        test_repo = Path('/Users/username/team-maia')

        def mock_is_valid(path):
            return path == test_repo

        with patch('claude.tools.core.paths._is_valid_maia_root', side_effect=mock_is_valid):
            with patch('pathlib.Path.cwd', return_value=test_repo):
                clear_maia_root_cache()

                # Import should use dynamic MAIA_ROOT
                from claude.tools.sre import smart_context_loader
                # Script uses MAIA_ROOT from paths module
                assert smart_context_loader.MAIA_ROOT == test_repo or \
                       smart_context_loader.paths.MAIA_ROOT == test_repo
