# System Status Overview

## Purpose
Unified view of all active work streams, states, and ingress across the Maia ecosystem.

## Description
Aggregates distributed state files to provide a single-pane-of-glass view of:
- Active projects and their completion status
- Session states and work streams
- Agent activity and health
- System components and their operational status
- Stale states requiring cleanup

## Usage
```bash
cd ${MAIA_ROOT}
python3 claude/tools/system_status_overview.py
```

## Key Features
- **Unified Dashboard**: Consolidates 20+ distributed state files
- **Progress Tracking**: Shows completion percentages and next actions
- **Health Monitoring**: Identifies stale or problematic states
- **Quick Navigation**: Direct links to detailed state files
- **Cleanup Recommendations**: Suggests maintenance actions

## Output Format
- System overview with operational status
- Active work streams with progress indicators
- Recent activity summary
- Maintenance recommendations
- Quick action items

## Integration
- Part of daily workflow efficiency protocols
- Can be chained with other monitoring commands
- Supports both CLI and programmatic access
