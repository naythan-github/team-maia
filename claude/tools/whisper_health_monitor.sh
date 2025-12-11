#!/bin/bash
# Whisper Server Health Monitor - SRE-grade service monitoring
# Checks whisper-server health every 30s, restarts if unhealthy

# Auto-detect MAIA_ROOT from script location if not set
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MAIA_ROOT="${MAIA_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"

HEALTH_URL="http://127.0.0.1:8090/"
LOG_FILE="$MAIA_ROOT/claude/data/logs/whisper-health-monitor.log"
FAILURE_COUNT=0
MAX_FAILURES=3

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

check_health() {
    # Try to hit the server
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$HEALTH_URL" 2>&1)

    if [ "$HTTP_CODE" = "200" ]; then
        return 0  # Healthy
    else
        return 1  # Unhealthy
    fi
}

restart_service() {
    log "⚠️  Restarting whisper-server after $FAILURE_COUNT consecutive failures"
    launchctl kickstart -k gui/$(id -u)/com.maia.whisper-server
    FAILURE_COUNT=0
    log "✅ Restart command issued"
}

# Main health check logic
if check_health; then
    # Server healthy
    if [ "$FAILURE_COUNT" -gt 0 ]; then
        log "✅ Server recovered (was at $FAILURE_COUNT failures)"
        FAILURE_COUNT=0
    fi
else
    # Server unhealthy
    FAILURE_COUNT=$((FAILURE_COUNT + 1))
    log "❌ Health check failed (failure $FAILURE_COUNT/$MAX_FAILURES)"

    if [ "$FAILURE_COUNT" -ge "$MAX_FAILURES" ]; then
        restart_service
    fi
fi
