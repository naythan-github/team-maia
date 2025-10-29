#!/usr/bin/env python3
"""
Register Project Backlog Dashboard with Unified Dashboard Platform

Integrates the project backlog dashboard into the MAIA unified dashboard hub
for centralized access and management.

Usage:
    python3 claude/tools/project_management/register_project_backlog_dashboard.py
"""

import sys
from pathlib import Path

# Add maia root to path
MAIA_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

from claude.tools.monitoring.unified_dashboard_platform import DashboardRegistry, DashboardConfig


def register_project_backlog_dashboard():
    """Register project backlog dashboard with unified platform."""

    registry = DashboardRegistry()

    # Configuration for project backlog dashboard
    # Port selection: Using 8067 (next available in DevOps/Metrics group 8060-8069)
    config = DashboardConfig(
        name="project_backlog_dashboard",
        description="Maia Project Registry Dashboard - Interactive visualization of project backlog, status, priorities, and analytics with 34+ tracked projects",
        file_path=str(MAIA_ROOT / "claude/tools/project_management/project_backlog_dashboard.py"),
        port=8067,
        host="127.0.0.1",
        auto_start=False,  # Can be started from hub
        health_endpoint="/",  # Streamlit default endpoint
        category="project_management",
        version="1.0",
        dependencies=["project_registry"]
    )

    success = registry.register_dashboard(config)

    if success:
        print("✅ Project Backlog Dashboard registered successfully!")
        print(f"   Name: {config.name}")
        print(f"   Port: {config.port}")
        print(f"   Category: {config.category}")
        print(f"   Description: {config.description}")
        print("")
        print("📊 Access via:")
        print(f"   Direct: streamlit run {config.file_path} --server.port={config.port}")
        print(f"   Hub: http://127.0.0.1:8100 (when unified dashboard hub is running)")
        print("")
        print("🚀 To start dashboard hub:")
        print("   ./dashboards start")
        print("   # Or: bash claude/tools/monitoring/dashboard_hub_control.sh start")
        print("")
        print("📝 Database: claude/data/project_registry.db (34 projects)")
    else:
        print("❌ Failed to register dashboard")
        print("Check that unified dashboard platform is accessible")
        sys.exit(1)


if __name__ == "__main__":
    register_project_backlog_dashboard()
