#!/usr/bin/env python3
"""
Register Agent Performance Dashboard with Unified Dashboard Platform

Integrates the agent performance monitoring dashboard into the MAIA unified
dashboard hub for centralized access and management.
"""

import sys
from pathlib import Path

# Add maia root to path
MAIA_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

from claude.tools.monitoring.unified_dashboard_platform import DashboardRegistry, DashboardConfig

def register_agent_performance_dashboard():
    """Register agent performance dashboard with unified platform."""

    registry = DashboardRegistry()

    # Find available port in dashboard range (8050-8099)
    # From existing dashboards, 8066 appears to be free
    config = DashboardConfig(
        name="agent_performance_dashboard",
        description="Real-time agent routing performance monitoring - tracks success rates, execution times, bottlenecks, and routing strategy effectiveness for Phase 121 automatic agent routing",
        file_path=str(MAIA_ROOT / "claude/tools/orchestration/agent_performance_dashboard_web.py"),
        port=8066,
        host="127.0.0.1",
        auto_start=False,  # Can be started from hub
        health_endpoint="/health",
        category="orchestration",
        version="1.0",
        dependencies=["performance_monitoring"]
    )

    success = registry.register_dashboard(config)

    if success:
        print("✅ Agent Performance Dashboard registered successfully!")
        print(f"   Name: {config.name}")
        print(f"   Port: {config.port}")
        print(f"   Category: {config.category}")
        print(f"   Description: {config.description}")
        print("")
        print("📊 Access via:")
        print(f"   CLI: python3 {config.file_path}")
        print(f"   Hub: http://127.0.0.1:8080 (when unified dashboard hub is running)")
    else:
        print("❌ Failed to register dashboard")
        sys.exit(1)

if __name__ == "__main__":
    register_agent_performance_dashboard()
