# Maia Dashboard Commands Reference

## 🏠 Dashboard Hub (Central Command Center)
**Launch:** `./launch_dashboard_hub.sh` or `streamlit run claude/tools/maia_dashboard_home.py --server.port 8500`
**URL:** http://localhost:8500
**Description:** Central hub for all Maia dashboards with unified navigation and system overview

## 🔍 Core System Dashboards

### System Status Dashboard
**Launch:** `streamlit run claude/tools/system_status_dashboard.py --server.port 8504`  
**URL:** http://localhost:8504  
**Features:**
- Real-time system health monitoring
- M4 hardware acceleration status
- Token savings integration
- Session activity tracking
- Active process monitoring

### Main Maia Dashboard  
**Launch:** `streamlit run claude/tools/streamlit_dashboard.py --server.port 8501`
**URL:** http://localhost:8501
**Features:**
- Agent monitoring and tracking
- Activity logs and system health
- Token analysis and optimization
- Comprehensive system overview

## ⚡ Optimization & Performance

### Token Savings Dashboard
**Launch:** `streamlit run claude/tools/token_savings_dashboard.py --server.port 8506`
**URL:** http://localhost:8506
**Features:**
- M4 acceleration analytics
- Cost savings calculations  
- Annual projection tracking
- Processing efficiency metrics
- Before/after comparisons

### Performance Monitoring Dashboard
**Launch:** `streamlit run claude/tools/performance_monitoring_dashboard.py --server.port 8505`
**URL:** http://localhost:8505  
**Features:**
- Agent communication analytics
- Message bus performance
- Context quality metrics
- Resource utilization tracking
- Historical performance analysis

## 📋 Project Management

### Project Backlog Dashboard
**Launch:** `streamlit run claude/tools/project_backlog_dashboard.py --server.port 8507`
**URL:** http://localhost:8507
**Features:**
- Project tracking and visualization
- Development backlog analysis
- Priority management
- Progress monitoring

## 💻 Terminal Dashboards

### Dashboard Launcher (Terminal)
**Launch:** `python3 claude/tools/dashboard_launcher.py`
**Features:**
- Interactive menu for launching dashboards
- Terminal and web dashboard options
- Combined dashboard launching

## 🚀 Quick Launch All Dashboards

### Method 1: Dashboard Hub
1. Launch the hub: `./launch_dashboard_hub.sh`
2. Use the web interface to launch other dashboards

### Method 2: Command Line (All at Once)
```bash
# System Status
streamlit run claude/tools/system_status_dashboard.py --server.port 8504 &

# Token Savings  
streamlit run claude/tools/token_savings_dashboard.py --server.port 8506 &

# Performance Monitoring
streamlit run claude/tools/performance_monitoring_dashboard.py --server.port 8505 &

# Project Backlog
streamlit run claude/tools/project_backlog_dashboard.py --server.port 8507 &

# Main Dashboard
streamlit run claude/tools/streamlit_dashboard.py --server.port 8501 &

# Dashboard Hub
streamlit run claude/tools/maia_dashboard_home.py --server.port 8500
```

### Method 3: Background Launch Script
```bash
#!/bin/bash
echo "🚀 Starting all Maia dashboards..."

# Launch all dashboards in background
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false streamlit run claude/tools/system_status_dashboard.py --server.port 8504 --server.headless true &
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false streamlit run claude/tools/token_savings_dashboard.py --server.port 8506 --server.headless true &  
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false streamlit run claude/tools/performance_monitoring_dashboard.py --server.port 8505 --server.headless true &
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false streamlit run claude/tools/project_backlog_dashboard.py --server.port 8507 --server.headless true &
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false streamlit run claude/tools/streamlit_dashboard.py --server.port 8501 --server.headless true &

# Launch dashboard hub in foreground
echo "All dashboards started! Opening dashboard hub..."
echo "🏠 Dashboard Hub: http://localhost:8500"
echo "🔍 System Status: http://localhost:8504" 
echo "💰 Token Savings: http://localhost:8506"
echo "📊 Performance: http://localhost:8505"
echo "📋 Project Backlog: http://localhost:8507"
echo "🤖 Main Dashboard: http://localhost:8501"

STREAMLIT_BROWSER_GATHER_USAGE_STATS=false streamlit run claude/tools/maia_dashboard_home.py --server.port 8500
```

## 📊 Dashboard Features Matrix

| Dashboard | System Health | Token Savings | Performance | Project Mgmt | Real-time |
|-----------|---------------|---------------|-------------|--------------|-----------|
| Dashboard Hub | ✅ Overview | ✅ Summary | ✅ Overview | ✅ Links | ✅ |
| System Status | ✅ Full | ✅ Integrated | ⚡ Basic | ❌ | ✅ |
| Token Savings | ⚡ Basic | ✅ Full | ⚡ M4 Only | ❌ | ✅ |
| Performance | ✅ Advanced | ✅ Metrics | ✅ Full | ❌ | ✅ |
| Project Backlog | ❌ | ❌ | ❌ | ✅ Full | ✅ |
| Main Dashboard | ✅ Full | ✅ Analysis | ⚡ Basic | ⚡ Basic | ✅ |

## 🔧 Troubleshooting

### Port Conflicts
If you get port conflicts, modify the port numbers:
- Default ports: 8500-8507
- Alternative range: 8510-8517

### Dependencies
Ensure you have required packages:
```bash
pip install streamlit plotly pandas psutil requests
```

### M4 Acceleration
Enable M4 for token savings tracking:
```bash
python3 claude/tools/m4_integration_manager.py --enable
```

## 🎯 Recommended Usage

1. **Start with Dashboard Hub** (`port 8500`) - Central navigation
2. **Monitor System Status** (`port 8504`) - Real-time health 
3. **Track Token Savings** (`port 8506`) - Cost optimization
4. **Analyze Performance** (`port 8505`) - Deep analytics when needed
5. **Manage Projects** (`port 8507`) - Development tracking

The Dashboard Hub provides the best entry point with unified navigation to all other specialized dashboards!