#!/bin/bash
# Maia Dashboard Launcher - All Services
# Restored on new MacBook - Phase 75

echo "🚀 Launching Maia Dashboard Platform..."
echo ""

# Add Python bin to PATH for streamlit
export PATH="/Users/naythandawe/Library/Python/3.9/bin:$PATH"

# Set Maia root
export MAIA_ROOT="/Users/naythandawe/git/maia"

# Dash Dashboards (Background)
echo "📊 Starting Dash dashboards..."
python3 claude/tools/monitoring/ai_business_intelligence_dashboard.py &
sleep 2
python3 claude/tools/monitoring/dora_metrics_dashboard.py &
sleep 2
python3 claude/tools/governance/governance_dashboard.py &
sleep 2

# Streamlit Dashboards (Background)
echo "📈 Starting Streamlit dashboards..."
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false streamlit run claude/tools/system_status_dashboard.py --server.port 8504 --server.headless true &
sleep 1
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false streamlit run claude/tools/token_savings_dashboard.py --server.port 8506 --server.headless true &
sleep 1
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false streamlit run claude/tools/performance_monitoring_dashboard.py --server.port 8505 --server.headless true &
sleep 1
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false streamlit run claude/tools/project_backlog_dashboard.py --server.port 8507 --server.headless true &
sleep 1
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false streamlit run claude/tools/streamlit_dashboard.py --server.port 8501 --server.headless true &
sleep 2

echo ""
echo "✅ All background dashboards launched!"
echo ""
echo "🏠 Starting Unified Dashboard Hub (foreground)..."
echo ""
echo "📊 Dashboard URLs:"
echo "  🏠 Unified Hub: http://localhost:8100"
echo "  💼 AI Business Intelligence: http://localhost:8050"
echo "  📈 DORA Metrics: http://localhost:8060"
echo "  🔒 Governance: http://localhost:8070"
echo "  🔍 System Status: http://localhost:8504"
echo "  💰 Token Savings: http://localhost:8506"
echo "  ⚡ Performance: http://localhost:8505"
echo "  📋 Project Backlog: http://localhost:8507"
echo "  🤖 Main Dashboard: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop all dashboards"
echo ""

# Launch unified dashboard hub in foreground
python3 claude/tools/monitoring/unified_dashboard_platform.py
