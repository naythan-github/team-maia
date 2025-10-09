#!/bin/bash
# Whisper Dictation System Status - Check all components

echo "═══════════════════════════════════════════════════════════"
echo "🎤 Whisper Dictation System Status"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Check whisper-server
echo "1️⃣  Whisper Server (Port 8090)"
if curl -s http://127.0.0.1:8090/ | grep -q "Whisper"; then
    echo "   ✅ Running and responding"
    launchctl list | grep whisper-server | awk '{print "   PID: " $1 " | Status: " $2}'
else
    echo "   ❌ Not responding"
fi
echo ""

# Check health monitor
echo "2️⃣  Health Monitor"
if launchctl list | grep -q "whisper-health"; then
    echo "   ✅ Running"
    launchctl list | grep whisper-health | awk '{print "   Status: " $2}'
else
    echo "   ❌ Not running"
fi
echo ""

# Check skhd
echo "3️⃣  skhd (Keyboard Shortcuts)"
if launchctl list | grep -q "skhd"; then
    echo "   ✅ Running"
    launchctl list | grep skhd | awk '{print "   PID: " $1 " | Status: " $2}'
    echo "   Hotkey: Cmd+Shift+Space"
else
    echo "   ❌ Not running"
fi
echo ""

# Check logs
echo "4️⃣  Recent Logs"
if [ -f ~/git/maia/claude/data/logs/whisper-server.log ]; then
    echo "   Server log (last 3 lines):"
    tail -3 ~/git/maia/claude/data/logs/whisper-server.log 2>/dev/null | sed 's/^/   /'
else
    echo "   ⚠️  No server log found"
fi
echo ""

if [ -f ~/git/maia/claude/data/logs/whisper-health-monitor.log ]; then
    echo "   Health monitor log (last 3 lines):"
    tail -3 ~/git/maia/claude/data/logs/whisper-health-monitor.log 2>/dev/null | sed 's/^/   /'
else
    echo "   ⚠️  No health monitor log found"
fi
echo ""

echo "═══════════════════════════════════════════════════════════"
echo "📊 Commands"
echo "═══════════════════════════════════════════════════════════"
echo "View server logs:  tail -f ~/git/maia/claude/data/logs/whisper-server.log"
echo "View health logs:  tail -f ~/git/maia/claude/data/logs/whisper-health-monitor.log"
echo "Restart server:    launchctl kickstart -k gui/\$(id -u)/com.maia.whisper-server"
echo "Restart skhd:      skhd --restart-service"
echo "Test dictation:    python3 ~/git/maia/claude/tools/whisper_dictation_server.py"
echo "═══════════════════════════════════════════════════════════"
