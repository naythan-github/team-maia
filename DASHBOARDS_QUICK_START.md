# Maia Dashboards - Quick Start Guide

**Status**: ✅ **RESTORED AND READY** (New MacBook)
**Dependencies**: ✅ Installed (streamlit, dash, plotly, all extras)
**Launcher Scripts**: ✅ Created

## 🚀 Quick Start (3 Commands)

### Option 1: Launch All Dashboards
```bash
./dashboard start
```

### Option 2: Individual Dashboard
```bash
./dashboard list   # See all URLs
./dashboard open   # Open Unified Hub
```

### Option 3: Check Status
```bash
./dashboard status
```

## 📊 Available Dashboards

| Dashboard | Port | URL | Framework | Purpose |
|-----------|------|-----|-----------|---------|
| **Unified Hub** | 8100 | http://localhost:8100 | Dash | Central platform with service registry |
| **AI Business Intelligence** | 8050 | http://localhost:8050 | Dash | Business analytics & insights |
| **DORA Metrics** | 8060 | http://localhost:8060 | Dash | DevOps performance metrics |
| **Governance** | 8070 | http://localhost:8070 | Dash | Governance monitoring |
| **Dashboard Home** | 8500 | http://localhost:8500 | Streamlit | Alternative hub |
| **Main Dashboard** | 8501 | http://localhost:8501 | Streamlit | Agent monitoring |
| **System Status** | 8504 | http://localhost:8504 | Streamlit | Real-time system health |
| **Performance** | 8505 | http://localhost:8505 | Streamlit | Performance analytics |
| **Token Savings** | 8506 | http://localhost:8506 | Streamlit | M4 acceleration & costs |
| **Project Backlog** | 8507 | http://localhost:8507 | Streamlit | Development tracking |

## 🎯 Control Commands

```bash
# Launch all dashboards
./dashboard start

# Stop all dashboards
./dashboard stop

# Restart all dashboards
./dashboard restart

# Check status
./dashboard status

# Open Unified Hub in browser
./dashboard open

# List all dashboard URLs
./dashboard list
```

## 📝 What Was Restored

### ✅ Installed Dependencies
- streamlit 1.50.0
- dash 3.2.0
- plotly 6.3.0
- dash-bootstrap-components 2.0.4
- dash-ag-grid 32.3.2
- All supporting packages

### ✅ Created Launcher Scripts
1. `./dashboard` - Control script (start, stop, status, etc.)
2. `./launch_all_dashboards.sh` - Full launcher
3. PATH configured for Python 3.9 user packages

### ✅ Verified Dashboard Files
- 10+ dashboard Python files from personal laptop
- All monitoring tools operational
- Service registry database intact
- Configuration files ready

## 🏗️ Architecture Overview

### Dash Dashboards (Enterprise)
- **Unified Hub** (8100) - Service registry & orchestration
- **AI Business Intelligence** (8050) - Business analytics
- **DORA Metrics** (8060) - DevOps KPIs
- **Governance** (8070) - Compliance monitoring

### Streamlit Dashboards (Real-time)
- **System Status** (8504) - Live health monitoring
- **Token Savings** (8506) - Cost optimization tracking
- **Performance** (8505) - Deep performance analytics
- **Project Backlog** (8507) - Development planning

## 💡 Recommended Usage

### Daily Workflow
```bash
# Morning: Start all dashboards
./dashboard start

# Access Unified Hub
open http://localhost:8100

# Check system health
open http://localhost:8504

# Evening: Stop dashboards
./dashboard stop
```

### Selective Launch
```bash
# Just the essentials
python3 claude/tools/monitoring/unified_dashboard_platform.py &
export PATH="/Users/naythandawe/Library/Python/3.9/bin:$PATH"
streamlit run claude/tools/system_status_dashboard.py --server.port 8504 &
```

### Presentation Mode
```bash
# Full ecosystem demo
./dashboard start

# Show Unified Hub
./dashboard open

# Navigate to specialized dashboards from hub
```

## 🔧 Troubleshooting

### Port Conflicts
```bash
# Check what's using a port
lsof -i :8100

# Stop specific dashboard
pkill -f "unified_dashboard_platform"
```

### Dependencies Missing
```bash
# Reinstall all dashboard packages
pip3 install streamlit dash dash-bootstrap-components dash-ag-grid plotly pandas psutil requests
```

### Script Not Executable
```bash
# Make scripts executable
chmod +x dashboard
chmod +x launch_all_dashboards.sh
```

### Streamlit Not Found
```bash
# Add to PATH (add to ~/.zshrc for persistence)
export PATH="/Users/naythandawe/Library/Python/3.9/bin:$PATH"
```

## 📈 Dashboard Features

### Unified Hub (Port 8100)
- 14+ service registry
- Real-time health checks
- Launch controls for all services
- Centralized navigation
- Service discovery

### AI Business Intelligence (Port 8050)
- Predictive analytics
- Business insights dashboard
- Custom data visualization
- Report generation

### System Status (Port 8504)
- Real-time system metrics
- M4 hardware acceleration status
- Token savings integration
- Active process monitoring

### Token Savings (Port 8506)
- M4 acceleration analytics
- Cost savings calculations
- Annual projections
- Before/after comparisons

## ✅ Restoration Checklist

- [x] Install streamlit
- [x] Install dash extras (bootstrap-components, ag-grid)
- [x] Create `./dashboard` control script
- [x] Create `./launch_all_dashboards.sh` launcher
- [x] Verify PATH includes Python 3.9 bin
- [x] Test dashboard control commands
- [x] Document access methods

## 🎊 Success!

**Dashboard system fully restored!**

**To start using**:
1. Run: `./dashboard start`
2. Open: http://localhost:8100
3. Navigate to specialized dashboards as needed

**All dashboard files from your personal laptop are operational on the new MacBook!**

---

**Quick Reference**:
```bash
./dashboard start    # Launch all
./dashboard open     # Access hub
./dashboard status   # Check health
./dashboard stop     # Shutdown all
```
