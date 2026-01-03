"""Core utilities for Maia tools."""

from claude.tools.core.paths import (
    MAIA_ROOT,
    CLAUDE_DIR,
    TOOLS_DIR,
    DATA_DIR,
    AGENTS_DIR,
    CONTEXT_DIR,
    HOOKS_DIR,
    DATABASES_DIR,
    get_maia_root,
    get_user_data,
    ensure_maia_root_env,
    PathManager,
)

__all__ = [
    "MAIA_ROOT",
    "CLAUDE_DIR",
    "TOOLS_DIR",
    "DATA_DIR",
    "AGENTS_DIR",
    "CONTEXT_DIR",
    "HOOKS_DIR",
    "DATABASES_DIR",
    "get_maia_root",
    "get_user_data",
    "ensure_maia_root_env",
    "PathManager",
]
