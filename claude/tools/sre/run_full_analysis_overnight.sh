#!/bin/bash
################################################################################
# ServiceDesk Comment Quality Analysis - Overnight Full Run
# Analyzes 3,300 stratified comment sample
# Estimated time: 55 minutes
################################################################################

cd ~/git/maia

echo "════════════════════════════════════════════════════════════════════════════"
echo "ServiceDesk Comment Quality Analysis - Full Run"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""
echo "📊 Sample size: 3,300 comments (stratified sample)"
echo "⏱️  Estimated time: ~55 minutes"
echo "🤖 Model: llama3.2:3b (Apple M4 GPU accelerated)"
echo ""
echo "Starting analysis at $(date)..."
echo ""

# Stop any existing analysis
pkill -f servicedesk_comment_quality_analyzer 2>/dev/null

# Run full analysis pipeline
nohup python3 claude/tools/sre/servicedesk_comment_quality_analyzer.py \
    --full \
    --sample-size 3300 \
    --batch-size 10 \
    > ~/servicedesk_full_analysis.log 2>&1 &

ANALYSIS_PID=$!

echo "✅ Analysis started (PID: $ANALYSIS_PID)"
echo ""
echo "📝 Log file: ~/servicedesk_full_analysis.log"
echo ""
echo "Monitor progress:"
echo "  watch -n 10 'sqlite3 ~/git/maia/claude/data/servicedesk_tickets.db \"SELECT COUNT(*) FROM comment_quality\"'"
echo ""
echo "Check when complete (tomorrow morning):"
echo "  python3 claude/tools/sre/servicedesk_comment_quality_analyzer.py --report"
echo ""
echo "════════════════════════════════════════════════════════════════════════════"
