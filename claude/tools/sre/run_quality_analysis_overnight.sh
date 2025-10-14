#!/bin/bash
# ServiceDesk Quality Analysis - Overnight Runner
# Runs full analysis pipeline in background

cd ~/git/maia

echo "🚀 Starting ServiceDesk Comment Quality Analysis..."
echo "   This will run overnight (~2-4 hours)"
echo "   Output logged to: ~/servicedesk_analysis.log"
echo ""

# Run full pipeline in background
nohup python3 claude/tools/sre/servicedesk_comment_quality_analyzer.py \
    --full \
    --sample-size 3300 \
    --batch-size 10 \
    > ~/servicedesk_analysis.log 2>&1 &

PID=$!
echo "✅ Analysis started (PID: $PID)"
echo ""
echo "Monitor progress:"
echo "   tail -f ~/servicedesk_analysis.log"
echo ""
echo "Check if still running:"
echo "   ps aux | grep $PID"
echo ""
echo "Results tomorrow in:"
echo "   ~/git/maia/claude/data/SERVICEDESK_QUALITY_REPORT.txt"
