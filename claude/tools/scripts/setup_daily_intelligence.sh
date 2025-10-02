#!/bin/bash
"""
Daily Intelligence Automation Setup
===================================

Sets up automated daily intelligence briefings and self-improvement monitoring.
"""

echo "🚀 Setting up Daily Intelligence Automation"
echo "=========================================="

# Set project directory
PROJECT_DIR="/Users/naythan/git/maia"
CRON_FILE="$PROJECT_DIR/claude/data/maia_intelligence_cron.txt"

# Create directories
mkdir -p "$PROJECT_DIR/claude/data/briefings"
mkdir -p "$PROJECT_DIR/claude/logs"

# Create cron job configuration
cat > "$CRON_FILE" << EOF
# Maia Daily Intelligence Automation
# ==================================

# Morning Intelligence Briefing - 7:30 AM weekdays
30 7 * * 1-5 cd $PROJECT_DIR && python3 claude/tools/automated_morning_briefing.py >> claude/logs/morning_briefing.log 2>&1

# Daily RSS Intelligence Sweep - 8:00 AM daily
0 8 * * * cd $PROJECT_DIR && python3 claude/tools/intelligent_rss_monitor.py >> claude/logs/rss_monitor.log 2>&1

# Self-Improvement Monitoring - 6:00 PM weekdays
0 18 * * 1-5 cd $PROJECT_DIR && python3 claude/tools/maia_self_improvement_monitor.py >> claude/logs/self_improvement.log 2>&1

# Weekly Intelligence Summary - 8:00 AM Mondays
0 8 * * 1 cd $PROJECT_DIR && python3 claude/scripts/automated_intelligence_brief.py weekly "$PROJECT_DIR/claude/data/briefings/weekly_brief_$(date +%Y%m%d).md" >> claude/logs/weekly_brief.log 2>&1

EOF

echo "📅 Cron configuration created: $CRON_FILE"
echo ""
echo "⏰ Scheduled Tasks:"
echo "  • 7:30 AM (Mon-Fri): Morning email briefing"
echo "  • 8:00 AM (Daily): RSS intelligence sweep"
echo "  • 6:00 PM (Mon-Fri): Self-improvement scan"
echo "  • 8:00 AM (Monday): Weekly intelligence summary"
echo ""

# Test the systems
echo "🧪 Testing Intelligence Systems"
echo "==============================="

echo "📧 Testing morning briefing system..."
cd "$PROJECT_DIR"
python3 claude/tools/automated_morning_briefing.py

echo ""
echo "🤖 Testing self-improvement monitor..."
python3 claude/tools/maia_self_improvement_monitor.py

echo ""
echo "✅ Installation Options:"
echo ""
echo "1. Install cron jobs (automated):"
echo "   crontab $CRON_FILE"
echo ""
echo "2. Manual execution commands:"
echo "   # Morning briefing"
echo "   python3 $PROJECT_DIR/claude/tools/automated_morning_briefing.py"
echo ""
echo "   # Self-improvement scan"
echo "   python3 $PROJECT_DIR/claude/tools/maia_self_improvement_monitor.py"
echo ""
echo "   # Intelligence sweep"
echo "   python3 $PROJECT_DIR/claude/tools/intelligent_rss_monitor.py"
echo ""
echo "3. View logs:"
echo "   tail -f $PROJECT_DIR/claude/logs/*.log"
echo ""

read -p "🚀 Install cron jobs now? (y/N): " install_cron
if [[ $install_cron =~ ^[Yy]$ ]]; then
    echo "📅 Installing cron jobs..."
    crontab "$CRON_FILE"
    echo "✅ Cron jobs installed! Check with: crontab -l"
else
    echo "ℹ️  Cron jobs not installed. Run manually or install later with: crontab $CRON_FILE"
fi

echo ""
echo "🎉 Daily Intelligence Automation Setup Complete!"
echo ""
echo "📧 You will receive daily briefings at: nd25@londonxyz.com"
echo "🤖 Maia will continuously monitor for self-improvement opportunities"
echo "📊 Intelligence data will be automatically collected and analyzed"