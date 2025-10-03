#!/bin/bash
# Setup Daily Briefing Automation
# Creates cron job for 7:30 AM weekday delivery
#
# Phase: 84-85 - Complete Daily Intelligence System
# Date: 2025-10-03

set -e

echo "📊 Setting up Daily Briefing Automation"
echo "========================================="

# Define paths
MAIA_ROOT="$HOME/git/maia"
BRIEFING_SCRIPT="$MAIA_ROOT/claude/tools/automated_daily_briefing.py"
LOG_DIR="$MAIA_ROOT/claude/data/logs"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Create cron job
CRON_CMD="30 7 * * 1-5 cd $MAIA_ROOT && /usr/bin/python3 $BRIEFING_SCRIPT >> $LOG_DIR/daily_briefing.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "automated_daily_briefing.py"; then
    echo "✅ Daily briefing cron job already exists"
else
    # Add to crontab
    (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
    echo "✅ Daily briefing cron job created"
fi

echo ""
echo "📅 Schedule: 7:30 AM, Monday-Friday"
echo "📂 Logs: $LOG_DIR/daily_briefing.log"
echo "📧 Output: ~/git/maia/claude/data/daily_briefing_email.html"
echo ""
echo "🎯 To manually run:"
echo "   cd $MAIA_ROOT && python3 $BRIEFING_SCRIPT"
echo ""
echo "📋 To view current cron jobs:"
echo "   crontab -l"
echo ""
echo "🗑️  To remove automation:"
echo "   crontab -l | grep -v 'automated_daily_briefing.py' | crontab -"
echo ""
echo "✅ Setup complete!"
