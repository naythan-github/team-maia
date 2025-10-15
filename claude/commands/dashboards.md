# Dashboard Hub - Unified Dashboard Access

## Problem This Solves
Dashboard hub not loading at http://127.0.0.1:8100 because it needs to be manually started. This command provides simple, reliable access.

## Quick Start

```bash
# From maia root directory
./dashboards start    # Start the hub
./dashboards status   # Check if running
./dashboards stop     # Stop the hub
```

## What It Does

Starts the unified dashboard hub which provides centralized access to all 10+ MAIA dashboards including:
- Agent Performance Dashboard (8066) - Phase 121 routing metrics
- ServiceDesk Operations (8065)
- Security Operations (8058)
- Team Intelligence (8050)
- And 7 more...

## Access

Once started, open your browser to:
**http://127.0.0.1:8100**

You'll see a central hub showing all dashboards with:
- Status indicators (running/stopped)
- Quick links to each dashboard
- Health monitoring
- Start/stop controls

## Commands

```bash
./dashboards start    # Start hub (runs in background)
./dashboards stop     # Stop hub
./dashboards restart  # Restart hub
./dashboards status   # Show current status
./dashboards logs     # Tail dashboard logs
```

## Troubleshooting

**Hub not loading?**
```bash
./dashboards status   # Check if running
./dashboards start    # Start if not running
```

**Port 8100 already in use?**
```bash
lsof -i :8100        # Find what's using the port
./dashboards stop     # Stop if it's the hub
```

**Check logs:**
```bash
./dashboards logs                                   # Live tail
cat claude/data/logs/unified-dashboard-error.log   # Error log
```

## Auto-Start on Login

The unified dashboard LaunchAgent is configured but needs manual start for now.

To enable auto-start:
```bash
launchctl load ~/Library/LaunchAgents/com.maia.unified-dashboard.plist
```

## Technical Details

- **Hub Port**: 8100
- **Dashboard Range**: 8050-8099 (managed by hub)
- **Control Script**: `claude/tools/monitoring/dashboard_hub_control.sh`
- **Platform**: `claude/tools/monitoring/unified_dashboard_platform.py`
- **Registry**: `claude/data/dashboard_registry.db` (SQLite)

## Related

- Agent performance dashboard: `python3 claude/tools/orchestration/agent_performance_dashboard.py`
- Dashboard registration: `claude/tools/orchestration/register_agent_dashboard.py`
- Individual dashboards can be accessed directly on their assigned ports

##Common Issue: "This is a common problem"

**Root Cause**: Dashboard hub doesn't auto-start on system boot

**Solution**: Use `./dashboards start` command from maia root whenever you need the hub

**Future**: LaunchAgent configured for auto-start (needs debugging for persistent operation)
