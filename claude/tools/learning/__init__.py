#!/usr/bin/env python3
"""
Maia Personal Learning System (PAI v2 Implementation)

Personal-only learning with no team sharing:
- UOCS: Universal Output Capture System
- Memory: Session history and summaries (Maia Memory)
- VERIFY: Success measurement
- LEARN: Pattern extraction

Storage: ~/.maia/ (per-user, NOT in git)
"""

from pathlib import Path


def get_learning_root() -> Path:
    """
    Get ~/.maia/ learning root, create if needed.

    Returns:
        Path to ~/.maia/ directory with all subdirectories created.
    """
    root = Path.home() / ".maia"

    # Create directory structure
    dirs = [
        root / "outputs",
        root / "memory" / "summaries",
        root / "learning",
    ]

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    return root


# Initialize on import
LEARNING_ROOT = get_learning_root()

__all__ = ["get_learning_root", "LEARNING_ROOT"]
