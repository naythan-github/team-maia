#!/bin/bash
# Maia Dashboard Launcher - Working Dashboards Only
# Uses only dashboards that actually exist

echo "🚀 Launching Maia Dashboard Platform..."
echo ""

# Set environment
export PATH="/Users/naythandawe/Library/Python/3.9/bin:$PATH"
export MAIA_ROOT="/Users/naythandawe/git/maia"
export PYTHONPATH="/Users/naythandawe/git/maia"

# Start Dash Dashboards (Background)
echo "📊 Starting Dash dashboards..."

# AI Business Intelligence (Port 8050)
python3 claude/tools/monitoring/ai_business_intelligence_dashboard.py &
sleep 2

# DORA Metrics (Port 8060)
python3 claude/tools/monitoring/dora_metrics_dashboard.py &
sleep 2

# Governance Dashboard (Port 8070)
python3 claude/tools/governance/governance_dashboard.py &
sleep 2

# Team Intelligence (Port 8090)
python3 claude/tools/monitoring/team_intelligence_dashboard.py &
sleep 2

# Security Operations (Port 8091)
python3 claude/tools/monitoring/security_operations_dashboard.py &
sleep 2

echo ""
echo "✅ All dashboards launched!"
echo ""
echo "📊 Dashboard URLs:"
echo "  🏠 Unified Hub: http://localhost:8100"
echo "  💼 AI Business Intelligence: http://localhost:8050"
echo "  📈 DORA Metrics: http://localhost:8060"
echo "  🔒 Governance: http://localhost:8070"
echo "  👥 Team Intelligence: http://localhost:8090"
echo "  🛡️  Security Operations: http://localhost:8091"
echo ""
echo "🌐 nginx Service Mesh: http://localhost:8080"
echo ""
echo "Press Ctrl+C to stop all dashboards"
echo ""

# Launch unified dashboard hub in foreground
python3 claude/tools/monitoring/unified_dashboard_platform.py
