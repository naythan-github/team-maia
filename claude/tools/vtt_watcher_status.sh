#!/bin/bash
# VTT Watcher Status Check

# Auto-detect MAIA_ROOT from script location if not set
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MAIA_ROOT="${MAIA_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"

echo "📊 VTT Watcher Status"
echo "===================="
echo ""

# Check LaunchAgent
if launchctl list | grep -q "com.maia.vtt-watcher"; then
    PID=$(launchctl list | grep "com.maia.vtt-watcher" | awk '{print $1}')
    STATUS=$(launchctl list | grep "com.maia.vtt-watcher" | awk '{print $2}')

    echo "✅ LaunchAgent: ACTIVE"
    echo "   PID: $PID"
    echo "   Exit Status: $STATUS"

    if ps -p "$PID" > /dev/null 2>&1; then
        echo "   Process: RUNNING"
    else
        echo "   Process: NOT RUNNING (will auto-restart)"
    fi
else
    echo "❌ LaunchAgent: NOT LOADED"
fi

echo ""
echo "📁 Monitoring: ~/Library/CloudStorage/OneDrive-ORROPTYLTD/Documents/1-VTT"
echo "📊 Output: $MAIA_ROOT/claude/data/transcript_summaries/"
echo ""

# Recent log entries
if [ -f "$MAIA_ROOT/claude/data/logs/vtt_watcher.log" ]; then
    echo "📝 Recent Activity:"
    tail -5 "$MAIA_ROOT/claude/data/logs/vtt_watcher.log" | sed 's/^/   /'
fi

echo ""
echo "🔧 Management Commands:"
echo "   Status:  bash $MAIA_ROOT/claude/tools/vtt_watcher_status.sh"
echo "   Disable: launchctl unload ~/Library/LaunchAgents/com.maia.vtt-watcher.plist"
echo "   Enable:  launchctl load ~/Library/LaunchAgents/com.maia.vtt-watcher.plist"
echo "   Logs:    tail -f $MAIA_ROOT/claude/data/logs/vtt_watcher.log"
