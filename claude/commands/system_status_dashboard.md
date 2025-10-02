# System Status Dashboard

## Purpose
Web-based dashboard providing visual monitoring of all Maia work streams, states, and system health.

## Description
Streamlit web interface that displays the system_status_overview data in an interactive, visual format with:
- Real-time system health monitoring
- Visual activity timelines and charts
- Interactive data tables
- Auto-refresh capabilities
- Cleanup recommendations

## Usage
```bash
cd ${MAIA_ROOT}
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false python3 -m streamlit run claude/tools/system_status_dashboard.py --server.port 8504 --server.headless true
```

## Features
- **System Overview**: Health metrics, component status, key updates
- **Session Activity**: Timeline charts, age distribution, recent activity tables
- **Project States**: Visual project status with interactive charts
- **Agent Activity**: Real-time agent monitoring and status
- **Active Processes**: Cron jobs and system process monitoring
- **Cleanup Recommendations**: Automated maintenance suggestions
- **Auto Refresh**: Optional 30-second auto-refresh for live monitoring

## Dashboard Sections
1. **🚀 System Overview** - Main system state and health metrics
2. **⚡ Active Processes** - Running processes and cron jobs
3. **📝 Session Activity** - Session state analysis with charts
4. **🎯 Project States** - Project status visualization
5. **🤖 Agent Activity** - Recent agent work and status
6. **🧹 Cleanup Recommendations** - System maintenance alerts
7. **📊 Summary Statistics** - Overall system health score

## Integration
- Uses `system_status_overview.py` as data source
- Runs on dedicated port (8504) for separate tab access
- Compatible with existing monitoring infrastructure
- Real-time data caching for performance