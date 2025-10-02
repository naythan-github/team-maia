#!/bin/bash
"""
Maia Dashboard Hub Launcher
Quick launcher for the central dashboard hub
"""

echo "🏠 Starting Maia Dashboard Hub..."
echo "Dashboard will be available at: http://localhost:8500"
echo "Press Ctrl+C to stop"

cd /Users/naythan/git/maia

STREAMLIT_BROWSER_GATHER_USAGE_STATS=false python3 -m streamlit run claude/tools/maia_dashboard_home.py --server.port 8500 --server.headless true