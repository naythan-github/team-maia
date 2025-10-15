#!/bin/bash
# Dashboard Hub Control Script
# Simple wrapper to manage the unified dashboard hub

MAIA_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
HUB_SCRIPT="$MAIA_ROOT/claude/tools/monitoring/unified_dashboard_platform.py"
LAUNCHAGENT_PLIST="$HOME/Library/LaunchAgents/com.maia.dashboard-hub.plist"

case "${1:-status}" in
    start)
        echo "🚀 Starting Dashboard Hub..."

        # Check if LaunchAgent exists
        if [[ -f "$LAUNCHAGENT_PLIST" ]]; then
            echo "📋 Using LaunchAgent for persistent service..."
            launchctl load "$LAUNCHAGENT_PLIST" 2>/dev/null || echo "LaunchAgent already loaded"
            sleep 2
        else
            echo "📋 LaunchAgent not found, starting manually..."
            python3 "$HUB_SCRIPT" service-start --foreground &
            sleep 3
        fi

        # Check if it's running
        if lsof -i :8100 >/dev/null 2>&1; then
            echo "✅ Dashboard Hub is running"
            echo "🌐 Access at: http://127.0.0.1:8100"
        else
            echo "❌ Dashboard Hub failed to start"
            echo "Check logs at: $MAIA_ROOT/claude/data/logs/dashboard-hub.log"
            exit 1
        fi
        ;;

    stop)
        echo "🛑 Stopping Dashboard Hub..."

        # Stop LaunchAgent if loaded
        if launchctl list | grep -q com.maia.dashboard-hub; then
            launchctl unload "$LAUNCHAGENT_PLIST" 2>/dev/null
            echo "✅ LaunchAgent stopped"
        fi

        # Kill any remaining processes on port 8100
        PID=$(lsof -ti :8100 2>/dev/null)
        if [[ -n "$PID" ]]; then
            kill "$PID" 2>/dev/null
            echo "✅ Dashboard Hub stopped (PID: $PID)"
        else
            echo "ℹ️  Dashboard Hub was not running"
        fi
        ;;

    restart)
        echo "🔄 Restarting Dashboard Hub..."
        "$0" stop
        sleep 2
        "$0" start
        ;;

    status)
        echo "📊 Dashboard Hub Status"
        echo "─────────────────────────────────────"

        # Check if running
        if lsof -i :8100 >/dev/null 2>&1; then
            PID=$(lsof -ti :8100)
            echo "Status: ✅ RUNNING (PID: $PID)"
            echo "URL: http://127.0.0.1:8100"

            # Check LaunchAgent status
            if launchctl list | grep -q com.maia.dashboard-hub; then
                echo "Mode: LaunchAgent (persistent)"
            else
                echo "Mode: Manual (temporary)"
            fi
        else
            echo "Status: ❌ NOT RUNNING"
            echo ""
            echo "To start: $0 start"
        fi

        # Show recent logs if available
        LOG_FILE="$MAIA_ROOT/claude/data/logs/dashboard-hub.log"
        if [[ -f "$LOG_FILE" ]]; then
            echo ""
            echo "Recent logs (last 5 lines):"
            tail -5 "$LOG_FILE" 2>/dev/null | sed 's/^/  /'
        fi
        ;;

    logs)
        LOG_FILE="$MAIA_ROOT/claude/data/logs/dashboard-hub.log"
        if [[ -f "$LOG_FILE" ]]; then
            tail -f "$LOG_FILE"
        else
            echo "❌ Log file not found: $LOG_FILE"
            exit 1
        fi
        ;;

    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the dashboard hub"
        echo "  stop    - Stop the dashboard hub"
        echo "  restart - Restart the dashboard hub"
        echo "  status  - Show current status"
        echo "  logs    - Tail dashboard hub logs"
        exit 1
        ;;
esac
