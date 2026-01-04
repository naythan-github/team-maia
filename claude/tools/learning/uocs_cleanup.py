#!/usr/bin/env python3
"""
UOCS cleanup - prune old captures.

Removes output directories older than N days to manage disk space.
Default retention: 7 days.
"""

import shutil
from datetime import datetime, timedelta
from pathlib import Path


def cleanup_old_outputs(days: int = 7) -> int:
    """
    Remove output directories older than N days.

    Args:
        days: Number of days to retain (default 7)

    Returns:
        Number of directories removed
    """
    outputs_root = Path.home() / ".maia" / "outputs"
    if not outputs_root.exists():
        return 0

    cutoff = datetime.now() - timedelta(days=days)
    removed = 0

    for session_dir in outputs_root.iterdir():
        if not session_dir.is_dir():
            continue

        manifest = session_dir / "manifest.json"
        if manifest.exists():
            mtime = datetime.fromtimestamp(manifest.stat().st_mtime)
            if mtime < cutoff:
                shutil.rmtree(session_dir)
                removed += 1

    return removed


if __name__ == "__main__":
    import sys
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    removed = cleanup_old_outputs(days)
    print(f"Removed {removed} output directories older than {days} days")
