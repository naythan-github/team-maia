#!/usr/bin/env python3
"""
Maia Root Path Resolution

Provides portable path resolution for Maia across any machine.
Use MAIA_ROOT instead of hardcoded paths.

Usage:
    from claude.tools.core.paths import MAIA_ROOT

    db_path = MAIA_ROOT / "claude/data/databases/system/system_state.db"
    tool_path = MAIA_ROOT / "claude/tools/sre/smart_context_loader.py"
"""

import os
from pathlib import Path


def get_maia_root() -> Path:
    """
    Get Maia root directory - works on any machine.

    Resolution order:
    1. MAIA_ROOT environment variable (explicit override)
    2. Derive from this file's location (automatic)

    Returns:
        Path to Maia root directory
    """
    # Option 1: Environment variable (explicit)
    if "MAIA_ROOT" in os.environ:
        return Path(os.environ["MAIA_ROOT"]).resolve()

    # Option 2: Derive from this file's location
    # This file is at: claude/tools/core/paths.py
    # Maia root is 4 levels up
    return Path(__file__).parent.parent.parent.parent.resolve()


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


if __name__ == "__main__":
    print(f"MAIA_ROOT: {MAIA_ROOT}")
    print(f"CLAUDE_DIR: {CLAUDE_DIR}")
    print(f"TOOLS_DIR: {TOOLS_DIR}")
    print(f"DATA_DIR: {DATA_DIR}")
    print(f"Exists: {MAIA_ROOT.exists()}")
