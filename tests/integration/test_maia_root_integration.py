"""
Integration Tests for Dynamic MAIA_ROOT Detection

Tests get_maia_root() in real repository environments.
Requires actual Maia repositories to exist.

Sprint: SPRINT-001-REPO-SYNC
Story: 1.1 - Create get_maia_root() Utility Function
Phase: P5 - Integration Testing

Created: 2026-01-15
"""

import pytest
import os
from pathlib import Path

from claude.tools.core.paths import get_maia_root, clear_maia_root_cache


@pytest.mark.integration
class TestMaiaRootIntegration:
    """Integration tests for get_maia_root() in real environments."""

    def setup_method(self):
        """Clear cache before each test."""
        clear_maia_root_cache()

    def test_get_maia_root_from_actual_repo(self):
        """
        Integration Test: Detect repo from actual working directory.

        Given: Running in actual Maia repository
        When: get_maia_root() called
        Then: Returns correct repository root
        """
        # Clear cache to force detection
        clear_maia_root_cache()

        # Clear env var to test CWD detection
        env_backup = os.environ.pop('MAIA_ROOT', None)

        try:
            # Get root from current working directory
            result = get_maia_root()

            # Verify it's a valid Maia repo
            assert result.exists(), f"MAIA_ROOT doesn't exist: {result}"
            assert (result / '.git').exists(), f"No .git in {result}"
            assert (result / 'claude').exists(), f"No claude/ in {result}"
            assert (result / 'claude' / 'tools').exists(), f"No claude/tools in {result}"

            # Verify this file is inside the detected repo
            this_file = Path(__file__).resolve()
            assert str(this_file).startswith(str(result)), \
                f"Test file {this_file} not under MAIA_ROOT {result}"

        finally:
            # Restore env var
            if env_backup:
                os.environ['MAIA_ROOT'] = env_backup

    def test_get_maia_root_with_deep_cwd(self):
        """
        Integration Test: Detect repo from deep subdirectory.

        Given: CWD is deep in repository (e.g., tests/integration/)
        When: get_maia_root() called
        Then: Walks up and finds repository root
        """
        clear_maia_root_cache()

        # Clear env var
        env_backup = os.environ.pop('MAIA_ROOT', None)

        try:
            # Save current directory
            original_cwd = Path.cwd()

            # Change to deep subdirectory
            deep_dir = Path(__file__).parent  # tests/integration/
            os.chdir(deep_dir)

            # Detect root from deep directory
            result = get_maia_root()

            # Should still find repository root
            assert (result / 'claude').exists()
            assert (result / '.git').exists()

            # Verify deep_dir is under result
            assert str(deep_dir).startswith(str(result))

        finally:
            # Restore
            os.chdir(original_cwd)
            if env_backup:
                os.environ['MAIA_ROOT'] = env_backup

    def test_get_maia_root_env_var_override(self):
        """
        Integration Test: Environment variable takes precedence.

        Given: MAIA_ROOT env var set to valid repo
        When: get_maia_root() called
        Then: Uses env var, not CWD
        """
        clear_maia_root_cache()

        # Get actual repo root
        original_cwd = Path.cwd()
        env_backup = os.environ.pop('MAIA_ROOT', None)

        try:
            # Walk up to find actual root
            current = original_cwd
            while current.parent != current:
                if (current / '.git').exists() and (current / 'claude').exists():
                    break
                current = current.parent

            # Set env var to this root
            os.environ['MAIA_ROOT'] = str(current)

            # Change to different directory
            os.chdir('/tmp')

            # Should still return env var path
            result = get_maia_root()
            assert result == current

        finally:
            os.chdir(original_cwd)
            if env_backup:
                os.environ['MAIA_ROOT'] = env_backup
            else:
                os.environ.pop('MAIA_ROOT', None)

    def test_get_maia_root_caching_in_real_repo(self):
        """
        Integration Test: Caching works in real repository.

        Given: get_maia_root() called twice
        When: Second call made
        Then: Returns same object (cached)
        """
        clear_maia_root_cache()

        root1 = get_maia_root()
        root2 = get_maia_root()

        # Same object reference
        assert root1 is root2

        # Both are valid paths
        assert root1.exists()
        assert (root1 / 'claude').exists()

    @pytest.mark.skip(reason="Requires team-maia repo to exist")
    def test_get_maia_root_multi_repo_switching(self):
        """
        Integration Test: Switching between repositories.

        Given: Two Maia repositories exist
        When: Switch repos and clear cache
        Then: Detects new repository correctly

        Note: This test is skipped by default - run manually when both repos exist
        """
        personal_repo = Path('/Users/username/maia')
        work_repo = Path('/Users/username/team-maia')

        # Skip if repos don't exist
        if not (personal_repo.exists() and work_repo.exists()):
            pytest.skip("Both repos required for multi-repo test")

        # Test personal repo
        os.chdir(personal_repo)
        clear_maia_root_cache()
        result1 = get_maia_root()
        assert result1 == personal_repo

        # Test work repo
        os.chdir(work_repo)
        clear_maia_root_cache()
        result2 = get_maia_root()
        assert result2 == work_repo

        # Verify they're different
        assert result1 != result2
