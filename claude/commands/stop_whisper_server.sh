#!/bin/bash
#
# Stop Whisper Server
#
# Usage:
#   bash claude/commands/stop_whisper_server.sh

set -e

PID_FILE="$HOME/.maia/whisper-server.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "⚠️  Whisper server not running (no PID file)"
    exit 0
fi

PID=$(cat "$PID_FILE")

if ! ps -p "$PID" > /dev/null 2>&1; then
    echo "⚠️  Whisper server not running (stale PID)"
    rm "$PID_FILE"
    exit 0
fi

echo "🛑 Stopping Whisper server (PID: $PID)..."
kill "$PID"

# Wait for graceful shutdown
for i in {1..10}; do
    if ! ps -p "$PID" > /dev/null 2>&1; then
        rm "$PID_FILE"
        echo "✅ Whisper server stopped"
        exit 0
    fi
    sleep 1
done

# Force kill if still running
echo "⚠️  Graceful shutdown failed, forcing..."
kill -9 "$PID" 2>/dev/null || true
rm "$PID_FILE"
echo "✅ Whisper server stopped (forced)"
