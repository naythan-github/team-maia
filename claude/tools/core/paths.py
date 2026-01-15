#!/usr/bin/env python3
"""
Maia Path Resolution - Portable path handling for multi-user operation.

Provides consistent path resolution regardless of user or machine.
All tools should use these functions instead of hardcoded paths.

Usage:
    from claude.tools.core.paths import MAIA_ROOT, PathManager

    # Shared repo paths
    db_path = MAIA_ROOT / "claude/data/databases/system/system_state.db"
    tool_path = MAIA_ROOT / "claude/tools/sre/smart_context_loader.py"

    # User-specific paths (multi-user support)
    user_data = PathManager.get_user_data_path()       # ~/.maia/
    user_db = PathManager.get_user_db_path("prefs.db") # ~/.maia/data/databases/user/prefs.db

Environment Variables:
    MAIA_ROOT - Override Maia repository location
    MAIA_USER_DATA - Override user data location (default: ~/.maia)

Author: DevOps Principal Architect Agent
Date: 2026-01-03
"""

import os
from pathlib import Path
from typing import Optional


# Module-level cache for MAIA_ROOT
_maia_root_cache: Optional[Path] = None


def get_maia_root() -> Path:
    """
    Detect MAIA_ROOT dynamically from multiple sources.

    Priority order:
    1. MAIA_ROOT environment variable (highest priority)
    2. Walk up from CWD looking for .git + claude/ directory
    3. Fallback to script location (backward compat)

    Returns:
        Path to maia repository root

    Raises:
        ValueError: If no valid maia repo found or validation fails

    Performance:
        Result is cached per session, <100ms on first call, <1ms cached

    Examples:
        >>> # With environment variable
        >>> os.environ['MAIA_ROOT'] = '/Users/username/team-maia'
        >>> get_maia_root()
        PosixPath('/Users/username/team-maia')

        >>> # Auto-detection from CWD
        >>> os.chdir('/Users/username/maia/claude/tools')
        >>> get_maia_root()
        PosixPath('/Users/username/maia')
    """
    global _maia_root_cache

    # Return cached result (performance optimization)
    if _maia_root_cache is not None:
        return _maia_root_cache

    # 1. Check environment variable (highest priority)
    if 'MAIA_ROOT' in os.environ:
        root = Path(os.environ['MAIA_ROOT'])
        if _is_valid_maia_repo(root):
            _maia_root_cache = root
            return root
        else:
            raise ValueError(f"MAIA_ROOT env var points to invalid repo: {root}")

    # 2. Walk up from current working directory
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        if _is_valid_maia_repo(parent):
            _maia_root_cache = parent
            return parent

    # 3. Fallback to script location (backward compat)
    # This file is at: claude/tools/core/paths.py
    # Maia root is 4 levels up
    script_root = Path(__file__).parent.parent.parent.parent.resolve()
    if _is_valid_maia_repo(script_root):
        _maia_root_cache = script_root
        return script_root

    raise ValueError("No valid Maia repository found in env, CWD, or script location")


def _is_valid_maia_repo(path: Path) -> bool:
    """
    Validate that path is a valid Maia repository.

    Checks:
    - Path exists and is a directory
    - .git directory exists
    - claude/ directory exists
    - Path is readable

    Args:
        path: Path to check

    Returns:
        True if valid Maia repo, False otherwise

    Examples:
        >>> _is_valid_maia_repo(Path('/Users/username/maia'))
        True
        >>> _is_valid_maia_repo(Path('/tmp'))
        False
    """
    try:
        return (
            path.exists() and
            path.is_dir() and
            (path / '.git').exists() and
            (path / 'claude').exists() and
            (path / 'claude').is_dir()
        )
    except (OSError, PermissionError):
        return False


def clear_maia_root_cache():
    """
    Clear cached MAIA_ROOT (for testing and repo switching).

    Use this when:
    - Running tests that change MAIA_ROOT
    - Switching between repositories
    - Debugging path resolution

    Examples:
        >>> # Test with different repos
        >>> os.environ['MAIA_ROOT'] = '/Users/username/maia'
        >>> get_maia_root()  # Cached: /Users/username/maia
        >>> clear_maia_root_cache()
        >>> os.environ['MAIA_ROOT'] = '/Users/username/team-maia'
        >>> get_maia_root()  # Now: /Users/username/team-maia
    """
    global _maia_root_cache
    _maia_root_cache = None


# Global constant for import
MAIA_ROOT = get_maia_root()


# Convenience paths
CLAUDE_DIR = MAIA_ROOT / "claude"
TOOLS_DIR = CLAUDE_DIR / "tools"
DATA_DIR = CLAUDE_DIR / "data"
AGENTS_DIR = CLAUDE_DIR / "agents"
CONTEXT_DIR = CLAUDE_DIR / "context"
HOOKS_DIR = CLAUDE_DIR / "hooks"
DATABASES_DIR = DATA_DIR / "databases"


def ensure_maia_root_env():
    """Set MAIA_ROOT environment variable if not already set."""
    if "MAIA_ROOT" not in os.environ:
        os.environ["MAIA_ROOT"] = str(MAIA_ROOT)


class PathManager:
    """
    Centralized path resolution for multi-user Maia.

    Locations:
    - MAIA_ROOT: Shared repository (tools, agents, context)
    - USER_DATA: Personal data (~/.maia/)
    - WORK_PROJECTS: User's work outputs (~/work_projects/)
    """

    _user_data: Optional[Path] = None

    @classmethod
    def get_maia_root(cls) -> Path:
        """Get Maia repository root (shared code)."""
        return MAIA_ROOT

    @classmethod
    def get_user_data_path(cls) -> Path:
        """
        Get user-specific data directory (~/.maia/).

        This directory contains:
        - Personal profile
        - User preferences
        - User databases
        - Session checkpoints

        Creates the directory if it doesn't exist.

        Returns:
            Path to user data directory
        """
        if cls._user_data is not None:
            return cls._user_data

        # Check environment override
        env_path = os.environ.get("MAIA_USER_DATA")
        if env_path:
            user_data = Path(env_path)
        else:
            user_data = Path.home() / ".maia"

        # Ensure directory exists with proper structure
        user_data.mkdir(parents=True, exist_ok=True)
        (user_data / "data" / "databases" / "user").mkdir(parents=True, exist_ok=True)
        (user_data / "data" / "checkpoints").mkdir(parents=True, exist_ok=True)
        (user_data / "context" / "personal").mkdir(parents=True, exist_ok=True)
        (user_data / "sessions").mkdir(parents=True, exist_ok=True)

        cls._user_data = user_data
        return user_data

    @classmethod
    def get_user_db_path(cls, db_name: str) -> Path:
        """
        Get path for user-specific database.

        Args:
            db_name: Database filename (e.g., "preferences.db")

        Returns:
            Full path to database in user data directory
        """
        return cls.get_user_data_path() / "data" / "databases" / "user" / db_name

    @classmethod
    def get_shared_db_path(cls, db_name: str) -> Path:
        """
        Get path for shared/derived database (regenerated locally).

        Args:
            db_name: Database filename (e.g., "capabilities.db")

        Returns:
            Full path to database in system directory
        """
        return DATABASES_DIR / "system" / db_name

    @classmethod
    def get_work_projects_path(cls) -> Path:
        """
        Get user's work projects directory.

        This is for work outputs FROM Maia, not Maia system files.

        Returns:
            Path to work projects directory (~/work_projects/)
        """
        work_path = Path.home() / "work_projects"
        work_path.mkdir(parents=True, exist_ok=True)
        return work_path

    @classmethod
    def get_session_path(cls, session_id: str) -> Path:
        """
        Get path for session state file.

        Sessions are stored in ~/.maia/sessions/ to survive reboots.

        Args:
            session_id: Unique session identifier

        Returns:
            Path to session file
        """
        return cls.get_user_data_path() / "sessions" / f"session_{session_id}.json"

    @classmethod
    def get_profile_path(cls) -> Path:
        """
        Get path to user's personal profile.

        Returns:
            Path to profile.md in user data directory
        """
        return cls.get_user_data_path() / "context" / "personal" / "profile.md"

    @classmethod
    def get_preferences_path(cls) -> Path:
        """
        Get path to user preferences file.

        Returns:
            Path to user_preferences.json
        """
        return cls.get_user_data_path() / "data" / "user_preferences.json"

    @classmethod
    def clear_cache(cls) -> None:
        """Clear cached paths (useful for testing)."""
        cls._user_data = None


# Convenience functions
def get_user_data() -> Path:
    """Shortcut for PathManager.get_user_data_path()"""
    return PathManager.get_user_data_path()


if __name__ == "__main__":
    print("Maia Path Resolution Test")
    print("=" * 50)
    print(f"MAIA_ROOT:     {MAIA_ROOT}")
    print(f"CLAUDE_DIR:    {CLAUDE_DIR}")
    print(f"TOOLS_DIR:     {TOOLS_DIR}")
    print(f"DATA_DIR:      {DATA_DIR}")
    print(f"USER_DATA:     {PathManager.get_user_data_path()}")
    print(f"User DB:       {PathManager.get_user_db_path('test.db')}")
    print(f"Work Projects: {PathManager.get_work_projects_path()}")
    print(f"Profile:       {PathManager.get_profile_path()}")
    print("=" * 50)
    print(f"MAIA_ROOT exists: {MAIA_ROOT.exists()}")
    print("✅ All paths resolved successfully")
