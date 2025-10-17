#!/usr/bin/env python3
"""
Register Hook Performance Dashboard with Unified Dashboard Platform

Integrates the hook performance monitoring dashboard into the MAIA unified
dashboard hub for centralized access and management.

Phase 127 - Monitoring & Alerting Integration
"""

import sys
from pathlib import Path

# Add maia root to path
MAIA_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

from claude.tools.monitoring.unified_dashboard_platform import DashboardRegistry, DashboardConfig

def register_hook_performance_dashboard():
    """Register hook performance dashboard with unified platform."""

    registry = DashboardRegistry()

    config = DashboardConfig(
        name="hook_performance_dashboard",
        description="Real-time hook performance monitoring - tracks P50/P95/P99 latency, output pollution, SLO compliance, and performance trends for Phase 126/127 hook optimization",
        file_path=str(MAIA_ROOT / "claude/tools/sre/hook_performance_dashboard.py"),
        port=8067,
        host="127.0.0.1",
        auto_start=False,  # Can be started from hub
        health_endpoint="/api/health",
        category="sre",
        version="1.0",
        dependencies=["performance_metrics.db"]
    )

    success = registry.register_dashboard(config)

    if success:
        print("✅ Hook Performance Dashboard registered successfully!")
        print(f"   Name: {config.name}")
        print(f"   Port: {config.port}")
        print(f"   Category: {config.category}")
        print(f"   Description: {config.description}")
        print("")
        print("📊 Access via:")
        print(f"   Direct: http://127.0.0.1:{config.port}")
        print(f"   CLI: python3 {config.file_path}")
        print(f"   Hub: http://127.0.0.1:8080 (when unified dashboard hub is running)")
        print("")
        print("🔗 Related Tools:")
        print(f"   Alerts: python3 claude/tools/sre/hook_performance_alerts.py check")
        print(f"   Profiler: python3 claude/tools/sre/hook_performance_profiler.py report")
    else:
        print("❌ Failed to register dashboard")
        sys.exit(1)

if __name__ == "__main__":
    register_hook_performance_dashboard()
