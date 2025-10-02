"""
Maia Portable Path Manager

Provides dynamic path resolution for Maia system to ensure portability across
different environments and directory locations.

Usage:
    from claude.tools.core.path_manager import get_maia_root, get_tools_dir, get_data_dir

    maia_root = get_maia_root()
    tools_dir = get_tools_dir()
    data_dir = get_data_dir()
"""

import os
from pathlib import Path
from typing import Optional


def get_maia_root() -> Path:
    """
    Get the Maia root directory using multiple fallback strategies.

    Priority:
    1. MAIA_ROOT environment variable
    2. Auto-detection from this file's location
    3. Current working directory if it contains 'claude' folder

    Returns:
        Path: Absolute path to Maia root directory
    """
    # Strategy 1: Environment variable
    if 'MAIA_ROOT' in os.environ:
        return Path(os.environ['MAIA_ROOT']).resolve()

    # Strategy 2: Auto-detect from this file's location
    # This file is at: maia/claude/tools/core/path_manager.py
    # So maia root is 4 levels up
    current_file = Path(__file__).resolve()
    maia_root = current_file.parent.parent.parent.parent

    # Verify this looks like Maia root (has claude directory)
    if (maia_root / 'claude').exists():
        return maia_root

    # Strategy 3: Check current working directory
    cwd = Path.cwd()
    if (cwd / 'claude').exists():
        return cwd

    # Strategy 4: Check parent directories up to 3 levels
    for parent in [cwd.parent, cwd.parent.parent, cwd.parent.parent.parent]:
        if (parent / 'claude').exists():
            return parent

    # Fallback: Return auto-detected path even if validation failed
    # This allows the system to work in edge cases
    return maia_root


def get_tools_dir() -> Path:
    """Get the tools directory path."""
    return get_maia_root() / 'claude' / 'tools'


def get_data_dir() -> Path:
    """Get the data directory path."""
    return get_maia_root() / 'claude' / 'data'


def get_agents_dir() -> Path:
    """Get the agents directory path."""
    return get_maia_root() / 'claude' / 'agents'


def get_commands_dir() -> Path:
    """Get the commands directory path."""
    return get_maia_root() / 'claude' / 'commands'


def get_context_dir() -> Path:
    """Get the context directory path."""
    return get_maia_root() / 'claude' / 'context'


def get_hooks_dir() -> Path:
    """Get the hooks directory path."""
    return get_maia_root() / 'claude' / 'hooks'


def resolve_path(relative_path: str) -> Path:
    """
    Resolve a relative path from Maia root.

    Args:
        relative_path: Path relative to Maia root (e.g., "claude/data/jobs.db")

    Returns:
        Path: Absolute resolved path
    """
    return get_maia_root() / relative_path


def get_database_path(db_name: str) -> Path:
    """
    Get path to a database file in claude/data directory.

    Args:
        db_name: Database filename (e.g., "jobs.db")

    Returns:
        Path: Absolute path to database file
    """
    return get_data_dir() / db_name


# Convenience function for backward compatibility
def get_path(path_type: str) -> Optional[Path]:
    """
    Get common Maia paths by type.

    Args:
        path_type: One of 'root', 'tools', 'data', 'agents', 'commands', 'context', 'hooks'

    Returns:
        Path or None if invalid type
    """
    path_map = {
        'root': get_maia_root,
        'tools': get_tools_dir,
        'data': get_data_dir,
        'agents': get_agents_dir,
        'commands': get_commands_dir,
        'context': get_context_dir,
        'hooks': get_hooks_dir,
    }

    getter = path_map.get(path_type.lower())
    return getter() if getter else None


if __name__ == '__main__':
    # Display current Maia paths for debugging
    print("🗂️  Maia Path Manager")
    print("=" * 50)
    print(f"MAIA_ROOT:     {get_maia_root()}")
    print(f"Tools:         {get_tools_dir()}")
    print(f"Data:          {get_data_dir()}")
    print(f"Agents:        {get_agents_dir()}")
    print(f"Commands:      {get_commands_dir()}")
    print(f"Context:       {get_context_dir()}")
    print(f"Hooks:         {get_hooks_dir()}")
    print("=" * 50)

    # Verify directories exist
    print("\n✓ Verification:")
    for name, path in [
        ('Root', get_maia_root()),
        ('Tools', get_tools_dir()),
        ('Data', get_data_dir()),
    ]:
        status = "✅" if path.exists() else "❌"
        print(f"{status} {name}: {path}")
