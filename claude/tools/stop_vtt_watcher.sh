#!/bin/bash
# Stop VTT Watcher background service

# Auto-detect MAIA_ROOT from script location if not set
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MAIA_ROOT="${MAIA_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
PID_FILE="$MAIA_ROOT/claude/data/vtt_watcher.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "❌ VTT Watcher is not running (no PID file)"
    exit 1
fi

PID=$(cat "$PID_FILE")

if ps -p "$PID" > /dev/null 2>&1; then
    echo "🛑 Stopping VTT Watcher (PID: $PID)..."
    kill "$PID"
    sleep 1

    # Force kill if still running
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "Force killing..."
        kill -9 "$PID"
    fi

    rm "$PID_FILE"
    echo "✅ VTT Watcher stopped"
else
    echo "❌ VTT Watcher is not running (stale PID file)"
    rm "$PID_FILE"
    exit 1
fi
