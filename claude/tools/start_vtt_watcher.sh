#!/bin/bash
# Start VTT Watcher as background service

# Auto-detect MAIA_ROOT from script location if not set
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MAIA_ROOT="${MAIA_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
PID_FILE="$MAIA_ROOT/claude/data/vtt_watcher.pid"
LOG_FILE="$MAIA_ROOT/claude/data/logs/vtt_watcher.log"

# Check if already running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "✅ VTT Watcher is already running (PID: $PID)"
        exit 0
    else
        echo "Removing stale PID file"
        rm "$PID_FILE"
    fi
fi

# Start the watcher
echo "🚀 Starting VTT Watcher..."
cd "$MAIA_ROOT"
nohup python3 claude/tools/vtt_watcher.py >> "$LOG_FILE" 2>&1 &
PID=$!

# Save PID
echo $PID > "$PID_FILE"

echo "✅ VTT Watcher started (PID: $PID)"
echo "📁 Monitoring: ~/Library/CloudStorage/OneDrive-YOUR_ORG/Documents/1-VTT"
echo "📊 Summaries: $MAIA_ROOT/claude/data/transcript_summaries"
echo "📝 Logs: $LOG_FILE"
