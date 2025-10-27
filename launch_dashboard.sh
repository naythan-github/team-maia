#!/bin/bash
# Quick launcher for Maia Project Backlog Dashboard

cd "$(dirname "$0")" || exit 1

echo "🚀 Launching Maia Project Backlog Dashboard..."
echo "📊 Database: claude/data/project_registry.db"
echo "🌐 URL: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the dashboard"
echo ""

streamlit run claude/tools/project_management/project_backlog_dashboard.py
