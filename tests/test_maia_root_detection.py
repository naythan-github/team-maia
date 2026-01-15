"""
Tests for Dynamic MAIA_ROOT Detection

Tests the get_maia_root() utility function that detects repository root
from multiple sources with priority order.

Sprint: SPRINT-001-REPO-SYNC
Story: 1.1 - Create get_maia_root() Utility Function
Phase: P0 - Test-First Design

Created: 2026-01-15
"""

import pytest
import os
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import will fail initially (P0 - tests should fail)
from claude.tools.core.paths import get_maia_root, clear_maia_root_cache


class TestGetMaiaRoot:
    """Test suite for get_maia_root() dynamic detection."""

    def setup_method(self):
        """Clear cache before each test."""
        clear_maia_root_cache()

    def test_get_maia_root_from_env_variable(self):
        """
        Test MAIA_ROOT from environment variable (highest priority).

        Given: MAIA_ROOT environment variable set
        When: get_maia_root() called
        Then: Returns path from environment variable
        """
        test_path = '/Users/username/team-maia'

        # Mock valid repo structure
        with patch.dict(os.environ, {'MAIA_ROOT': test_path}):
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.is_dir', return_value=True):
                    result = get_maia_root()
                    assert result == Path(test_path)

    def test_get_maia_root_from_cwd_walk(self):
        """
        Test MAIA_ROOT detection from CWD walk-up.

        Given: CWD is /Users/username/team-maia/claude/tools
        When: get_maia_root() called and env var not set
        Then: Walks up to /Users/username/team-maia (has .git + claude/)
        """
        cwd_deep = Path('/Users/username/team-maia/claude/tools')
        expected_root = Path('/Users/username/team-maia')

        def mock_exists(path_self):
            """Mock Path.exists() to simulate valid repo structure."""
            path_str = str(path_self)
            # Root path exists with .git and claude/
            if path_str == str(expected_root):
                return True
            if path_str == str(expected_root / '.git'):
                return True
            if path_str == str(expected_root / 'claude'):
                return True
            # Deep path exists
            if path_str == str(cwd_deep):
                return True
            return False

        def mock_is_dir(path_self):
            """Mock Path.is_dir() for directories."""
            path_str = str(path_self)
            return 'claude' in path_str or path_str == str(expected_root)

        with patch.dict(os.environ, {}, clear=True):  # No MAIA_ROOT env var
            with patch('pathlib.Path.cwd', return_value=cwd_deep):
                with patch.object(Path, 'exists', mock_exists):
                    with patch.object(Path, 'is_dir', mock_is_dir):
                        result = get_maia_root()
                        assert result == expected_root

    def test_get_maia_root_fallback_to_script_location(self):
        """
        Test fallback to script location when env/CWD fail.

        Given: No MAIA_ROOT env var and CWD walk finds nothing
        When: get_maia_root() called
        Then: Falls back to script's parent path
        """
        from claude.tools.core import paths as paths_module

        def mock_is_valid(path: Path) -> bool:
            """Mock validation - only script location is valid."""
            # Reject /tmp and its parents (CWD walk should fail)
            if str(path) == '/tmp' or str(path).startswith('/tmp'):
                return False
            # Accept only script location (fallback)
            script_root = Path(paths_module.__file__).parent.parent.parent.parent
            return path == script_root

        with patch.dict(os.environ, {}, clear=True):
            with patch('pathlib.Path.cwd', return_value=Path('/tmp')):
                with patch('claude.tools.core.paths._is_valid_maia_repo', side_effect=mock_is_valid):
                    result = get_maia_root()
                    # Should be script location, which contains 'maia'
                    assert 'maia' in str(result).lower()

    def test_get_maia_root_caching(self):
        """
        Test that result is cached per session.

        Given: get_maia_root() called once
        When: Called again
        Then: Returns same object reference (cached)
        """
        with patch.dict(os.environ, {'MAIA_ROOT': '/Users/username/maia'}):
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.is_dir', return_value=True):
                    root1 = get_maia_root()
                    root2 = get_maia_root()

                    # Same object reference (cached)
                    assert root1 is root2

    def test_get_maia_root_validates_structure(self):
        """
        Test that detected path has required structure.

        Given: MAIA_ROOT env var points to invalid directory
        When: get_maia_root() called
        Then: Raises ValueError
        """
        invalid_path = '/tmp/invalid_repo'

        with patch.dict(os.environ, {'MAIA_ROOT': invalid_path}):
            # Mock path exists but missing .git or claude/
            def mock_exists(path_self):
                path_str = str(path_self)
                if path_str == invalid_path:
                    return True  # Path exists
                return False  # But no .git or claude/

            with patch.object(Path, 'exists', mock_exists):
                with patch.object(Path, 'is_dir', return_value=True):
                    with pytest.raises(ValueError, match="Not a valid Maia repo|MAIA_ROOT env var"):
                        get_maia_root()

    def test_get_maia_root_performance(self):
        """
        Test detection completes in <100ms.

        Given: Cache cleared
        When: get_maia_root() called
        Then: Completes in <100ms (first call)
        """
        clear_maia_root_cache()

        with patch.dict(os.environ, {'MAIA_ROOT': '/Users/username/maia'}):
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.is_dir', return_value=True):
                    start = time.time()
                    get_maia_root()
                    duration = time.time() - start

                    assert duration < 0.1, f"Detection took {duration:.3f}s, expected <0.1s"

    def test_get_maia_root_cached_performance(self):
        """
        Test cached lookup is <1ms.

        Given: get_maia_root() already called (cached)
        When: Called again
        Then: Completes in <1ms (cached lookup)
        """
        with patch.dict(os.environ, {'MAIA_ROOT': '/Users/username/maia'}):
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.is_dir', return_value=True):
                    # First call (prime cache)
                    get_maia_root()

                    # Second call (should be cached)
                    start = time.time()
                    result = get_maia_root()
                    duration = time.time() - start

                    assert duration < 0.001, f"Cached lookup took {duration:.3f}s, expected <0.001s"


class TestClearMaiaRootCache:
    """Test suite for cache clearing (test utility)."""

    def test_clear_cache_allows_new_detection(self):
        """
        Test clearing cache allows new detection.

        Given: Cached result exists
        When: clear_maia_root_cache() called
        Then: Next call re-detects (not cached)
        """
        with patch.dict(os.environ, {'MAIA_ROOT': '/Users/username/maia'}):
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.is_dir', return_value=True):
                    root1 = get_maia_root()

                    # Clear cache
                    clear_maia_root_cache()

                    # Change env var
                    with patch.dict(os.environ, {'MAIA_ROOT': '/Users/username/team-maia'}):
                        root2 = get_maia_root()

                        # Should be different paths (not same cached object)
                        assert root1 != root2
