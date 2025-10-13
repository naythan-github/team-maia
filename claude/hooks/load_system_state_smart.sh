#!/bin/bash
# Smart SYSTEM_STATE.md Loader - Intent-Aware Context Loading
# Part of: Phase 2 SYSTEM_STATE Intelligent Loading Project
# Usage: ./load_system_state_smart.sh "user query context"

set -e

# Detect MAIA_ROOT
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MAIA_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Get user query context (default if not provided)
QUERY="${1:-What is the current system status?}"

# Invoke smart context loader
LOADER_PATH="$MAIA_ROOT/claude/tools/sre/smart_context_loader.py"

if [[ ! -f "$LOADER_PATH" ]]; then
    echo "⚠️  Smart loader not found: $LOADER_PATH" >&2
    echo "   Falling back to static Read of recent SYSTEM_STATE phases..." >&2

    # Fallback: Read recent 1000 lines (Phases 97-111 approximately)
    SYSTEM_STATE="$MAIA_ROOT/SYSTEM_STATE.md"
    if [[ -f "$SYSTEM_STATE" ]]; then
        tail -n 1000 "$SYSTEM_STATE"
        exit 0
    else
        echo "❌ SYSTEM_STATE.md not found: $SYSTEM_STATE" >&2
        exit 1
    fi
fi

# Execute smart loader
python3 "$LOADER_PATH" "$QUERY"
EXIT_CODE=$?

if [[ $EXIT_CODE -ne 0 ]]; then
    echo "⚠️  Smart loader failed with exit code $EXIT_CODE" >&2
    echo "   Falling back to static Read..." >&2
    tail -n 1000 "$MAIA_ROOT/SYSTEM_STATE.md"
    exit 0
fi

exit 0
