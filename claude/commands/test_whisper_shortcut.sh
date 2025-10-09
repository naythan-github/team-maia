#!/bin/bash
# Test script for whisper dictation keyboard shortcut
# Verifies that skhd service is running and ready

echo "🔍 Checking Whisper Dictation Keyboard Shortcut Setup"
echo "=================================================="
echo ""

# Check 1: skhd service running
echo "1. Checking skhd service..."
if launchctl list | grep -q "com.koekeishiya.skhd"; then
    echo "   ✅ skhd service is running"
else
    echo "   ❌ skhd service is NOT running"
    echo "   Fix: Run 'skhd --start-service'"
    exit 1
fi

# Check 2: Configuration file exists
echo ""
echo "2. Checking skhd configuration..."
if [ -f "$HOME/.skhdrc" ]; then
    echo "   ✅ Configuration file exists: ~/.skhdrc"
    echo "   📝 Configured shortcut: Option+Escape"
else
    echo "   ❌ Configuration file missing: ~/.skhdrc"
    exit 1
fi

# Check 3: Whisper server running
echo ""
echo "3. Checking Whisper server..."
if curl -s http://127.0.0.1:8090/health | grep -q "ok"; then
    echo "   ✅ Whisper server is running"
else
    echo "   ⚠️  Whisper server is NOT running"
    echo "   Fix: Run 'bash claude/commands/start_whisper_server.sh'"
    exit 1
fi

# Check 4: Python dependencies
echo ""
echo "4. Checking Python dependencies..."
if python3 -c "import pyperclip, requests" 2>/dev/null; then
    echo "   ✅ Python dependencies installed"
else
    echo "   ❌ Python dependencies missing"
    echo "   Fix: Run 'pip3 install pyperclip requests'"
    exit 1
fi

echo ""
echo "=================================================="
echo "✅ ALL CHECKS PASSED"
echo ""
echo "📋 NEXT STEP: Grant Accessibility Permission"
echo "   1. System Settings → Privacy & Security → Accessibility"
echo "   2. Look for 'skhd' in the list"
echo "   3. Toggle it ON"
echo "   4. Restart skhd: skhd --restart-service"
echo ""
echo "🎤 THEN TEST: Press Option+Escape, speak, paste (Cmd+V)"
echo ""
