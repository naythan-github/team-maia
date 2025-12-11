#!/bin/bash
# Organize Downloads - Manual trigger for intelligent downloads router
# Run this when you want to organize your downloads

# Auto-detect MAIA_ROOT from script location if not set
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MAIA_ROOT="${MAIA_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"

python3 "$MAIA_ROOT/claude/tools/intelligent_downloads_router.py" --scan-only
