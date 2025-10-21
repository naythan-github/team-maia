#!/bin/bash
#
# Maia Weekly Health Check - Automated Quality Monitoring
# Phase 134.2 - Team Deployment Monitoring
#
# Run this weekly (or set up as cron job) to validate Maia health
# Each team member runs independently on their laptop
#
# Usage:
#   ./claude/tools/sre/weekly_health_check.sh
#   ./claude/tools/sre/weekly_health_check.sh --email  # Future: email report
#

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "======================================================================"
echo "MAIA WEEKLY HEALTH CHECK"
echo "======================================================================"
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 1. Run Maia health check
echo "1. Running Maia health check..."
python3 claude/tools/sre/maia_health_check.py
HEALTH_EXIT=$?

if [ $HEALTH_EXIT -eq 0 ]; then
    echo -e "${GREEN}✅ Health check PASSED${NC}"
elif [ $HEALTH_EXIT -eq 1 ]; then
    echo -e "${YELLOW}⚠️  Health check has WARNINGS${NC}"
else
    echo -e "${RED}❌ Health check FAILED${NC}"
fi

echo ""
echo "======================================================================"

# 2. Run agent quality spot-check
echo "2. Running agent quality spot-check (10 agents)..."
python3 tests/test_agent_quality_spot_check.py > /dev/null 2>&1
QUALITY_EXIT=$?

if [ $QUALITY_EXIT -eq 0 ]; then
    echo -e "${GREEN}✅ Agent quality tests PASSED${NC}"
else
    echo -e "${RED}❌ Agent quality tests FAILED${NC}"
    echo "   Run: python3 tests/test_agent_quality_spot_check.py"
    echo "   for detailed results"
fi

echo ""
echo "======================================================================"

# 3. Check routing accuracy (last 7 days)
echo "3. Checking routing accuracy (last 7 days)..."
if [ -f "claude/data/routing_decisions.db" ]; then
    python3 claude/tools/orchestration/weekly_accuracy_report.py \
        --start $(date -v-7d '+%Y-%m-%d' 2>/dev/null || date -d '7 days ago' '+%Y-%m-%d') \
        --end $(date '+%Y-%m-%d') \
        > /dev/null 2>&1

    echo -e "${GREEN}✅ Routing report generated${NC}"
    echo "   See: claude/data/logs/routing_accuracy_*.md"
else
    echo -e "${YELLOW}⚠️  No routing data yet (use Maia more to collect data)${NC}"
fi

echo ""
echo "======================================================================"

# 4. Overall status
echo "OVERALL STATUS"
echo "======================================================================"

if [ $HEALTH_EXIT -eq 0 ] && [ $QUALITY_EXIT -eq 0 ]; then
    echo -e "${GREEN}✅ ALL CHECKS PASSED - Maia is healthy${NC}"
    exit 0
elif [ $HEALTH_EXIT -le 1 ] && [ $QUALITY_EXIT -eq 0 ]; then
    echo -e "${YELLOW}⚠️  OPERATIONAL WITH WARNINGS${NC}"
    echo "   Review health check output above"
    exit 1
else
    echo -e "${RED}❌ DEGRADED - Action required${NC}"
    echo "   1. Review health check output"
    echo "   2. Review quality test failures"
    echo "   3. Fix issues before using Maia"
    exit 2
fi
