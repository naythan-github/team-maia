# Dashboard Restoration Guide

**System**: New MacBook with 32GB RAM
**Status**: Restored from personal laptop, dependencies need installation
**Goal**: Restore all dashboard systems for local operation

## 📊 Dashboard Inventory

### Existing Dashboard Systems

**Dash-Based Dashboards** (Installed: ✅):
1. `ai_business_intelligence_dashboard.py` - Port 8050
2. `dora_metrics_dashboard.py` - Port 8060
3. `governance_dashboard.py` - Port 8070
4. `unified_dashboard_platform.py` - Port 8100 (Hub)

**Streamlit Dashboards** (Need installation: ❌):
1. `system_status_dashboard.py` - Port 8504
2. `token_savings_dashboard.py` - Port 8506
3. `performance_monitoring_dashboard.py` - Port 8505
4. `project_backlog_dashboard.py` - Port 8507
5. `streamlit_dashboard.py` - Port 8501 (Main)
6. `maia_dashboard_home.py` - Port 8500 (Hub)

## 🚀 Restoration Steps

### Step 1: Install Dashboard Dependencies

```bash
# Install Streamlit (required for 6 dashboards)
pip3 install streamlit

# Install additional dashboard packages
pip3 install dash-bootstrap-components dash-ag-grid

# Verify installations
pip3 list | grep -E "(streamlit|dash|plotly)"
```

**Expected Output**:
```
dash                      3.2.0  ✅ (already installed)
dash-ag-grid              [version]
dash-bootstrap-components [version]
plotly                    6.3.0  ✅ (already installed)
streamlit                 [version]
```

### Step 2: Test Dash Dashboards (Already Available)

```bash
# Test AI Business Intelligence Dashboard
python3 claude/tools/monitoring/ai_business_intelligence_dashboard.py &
# Access: http://localhost:8050

# Test DORA Metrics Dashboard
python3 claude/tools/monitoring/dora_metrics_dashboard.py &
# Access: http://localhost:8060

# Test Governance Dashboard
python3 claude/tools/governance/governance_dashboard.py &
# Access: http://localhost:8070

# Test Unified Dashboard Hub
python3 claude/tools/monitoring/unified_dashboard_platform.py &
# Access: http://localhost:8100
```

### Step 3: Set Up Streamlit Dashboards

```bash
# System Status Dashboard
streamlit run claude/tools/system_status_dashboard.py --server.port 8504 &

# Token Savings Dashboard
streamlit run claude/tools/token_savings_dashboard.py --server.port 8506 &

# Performance Monitoring Dashboard
streamlit run claude/tools/performance_monitoring_dashboard.py --server.port 8505 &

# Project Backlog Dashboard
streamlit run claude/tools/project_backlog_dashboard.py --server.port 8507 &

# Main Streamlit Dashboard
streamlit run claude/tools/streamlit_dashboard.py --server.port 8501 &

# Dashboard Hub (Streamlit version)
streamlit run claude/tools/maia_dashboard_home.py --server.port 8500 &
```

### Step 4: Create Unified Launcher Script

Save as `launch_all_dashboards.sh`:

```bash
#!/bin/bash
# Maia Dashboard Launcher - All Services

echo "🚀 Launching Maia Dashboard Platform..."

# Dash Dashboards (Background)
echo "📊 Starting Dash dashboards..."
python3 claude/tools/monitoring/ai_business_intelligence_dashboard.py &
python3 claude/tools/monitoring/dora_metrics_dashboard.py &
python3 claude/tools/governance/governance_dashboard.py &

# Streamlit Dashboards (Background)
echo "📈 Starting Streamlit dashboards..."
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false streamlit run claude/tools/system_status_dashboard.py --server.port 8504 --server.headless true &
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false streamlit run claude/tools/token_savings_dashboard.py --server.port 8506 --server.headless true &
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false streamlit run claude/tools/performance_monitoring_dashboard.py --server.port 8505 --server.headless true &
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false streamlit run claude/tools/project_backlog_dashboard.py --server.port 8507 --server.headless true &
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false streamlit run claude/tools/streamlit_dashboard.py --server.port 8501 --server.headless true &

# Unified Dashboard Hub (Foreground)
echo "🏠 Starting Unified Dashboard Hub..."
python3 claude/tools/monitoring/unified_dashboard_platform.py

echo "✅ All dashboards launched!"
echo ""
echo "📊 Dashboard URLs:"
echo "  🏠 Unified Hub: http://localhost:8100"
echo "  💼 AI Business Intelligence: http://localhost:8050"
echo "  📈 DORA Metrics: http://localhost:8060"
echo "  🔒 Governance: http://localhost:8070"
echo "  🔍 System Status: http://localhost:8504"
echo "  💰 Token Savings: http://localhost:8506"
echo "  ⚡ Performance: http://localhost:8505"
echo "  📋 Project Backlog: http://localhost:8507"
echo "  🤖 Main Dashboard: http://localhost:8501"
```

Make executable:
```bash
chmod +x launch_all_dashboards.sh
```

## 🎯 Quick Start Guide

### Method 1: Launch All Dashboards
```bash
./launch_all_dashboards.sh
```

### Method 2: Individual Dashboards
```bash
# Just the Unified Hub
python3 claude/tools/monitoring/unified_dashboard_platform.py

# Just AI Business Intelligence
python3 claude/tools/monitoring/ai_business_intelligence_dashboard.py

# Just System Status
streamlit run claude/tools/system_status_dashboard.py --server.port 8504
```

### Method 3: Use Existing Dashboard Hub
```bash
# Start the Streamlit dashboard hub
streamlit run claude/tools/maia_dashboard_home.py --server.port 8500

# Access: http://localhost:8500
# Click links to launch other dashboards
```

## 📋 Dashboard Port Reference

| Dashboard | Port | Framework | Description |
|-----------|------|-----------|-------------|
| **Unified Hub** | 8100 | Dash | Central dashboard platform with service registry |
| **Dashboard Home** | 8500 | Streamlit | Alternative hub with navigation |
| **Main Dashboard** | 8501 | Streamlit | Agent monitoring and system overview |
| **System Status** | 8504 | Streamlit | Real-time system health |
| **Performance** | 8505 | Streamlit | Performance analytics |
| **Token Savings** | 8506 | Streamlit | M4 acceleration & cost tracking |
| **Project Backlog** | 8507 | Streamlit | Development tracking |
| **AI Business Intelligence** | 8050 | Dash | Business intelligence & analytics |
| **DORA Metrics** | 8060 | Dash | DevOps metrics |
| **Governance** | 8070 | Dash | Governance monitoring |

## 🔧 Troubleshooting

### Streamlit Not Found
```bash
# Install streamlit
pip3 install streamlit

# Verify installation
which streamlit
streamlit --version
```

### Port Conflicts
```bash
# Check what's using ports
lsof -i :8100  # Check specific port
lsof -i :8500-8507  # Check range

# Kill processes if needed
kill -9 <PID>
```

### Missing Dependencies
```bash
# Install all dashboard dependencies
pip3 install streamlit dash dash-bootstrap-components dash-ag-grid plotly pandas psutil requests
```

### Dashboard Won't Start
```bash
# Check Python path
which python3

# Run with verbose output
python3 -v claude/tools/monitoring/unified_dashboard_platform.py

# Check logs
tail -f claude/data/dashboard.log
```

## 💡 Best Practices

### For Daily Use
1. **Start with Unified Hub** (port 8100) - Best overview
2. **Or use Dashboard Home** (port 8500) - Streamlit alternative
3. **Launch only needed dashboards** - Save resources

### For Development
1. **Individual dashboards** - Test specific features
2. **Background mode** - Keep dashboards running
3. **Monitor logs** - Track issues

### For Presentations
1. **All dashboards** - Full ecosystem demo
2. **Unified Hub** - Professional central view
3. **AI Business Intelligence** - Business value demo

## 🎨 Dashboard Features

### Unified Dashboard Hub (Port 8100)
- Service registry with 14+ services
- Real-time health monitoring
- Launch controls for all dashboards
- Centralized navigation

### AI Business Intelligence (Port 8050)
- Predictive analytics
- Business insights
- Data visualization
- Custom reporting

### System Status (Port 8504)
- Real-time system health
- M4 hardware acceleration status
- Token savings integration
- Process monitoring

### Token Savings (Port 8506)
- M4 acceleration analytics
- Cost savings calculations
- Annual projections
- Efficiency metrics

## ✅ Restoration Checklist

- [ ] Install streamlit: `pip3 install streamlit`
- [ ] Install dash extras: `pip3 install dash-bootstrap-components dash-ag-grid`
- [ ] Test Dash dashboards (already have packages)
- [ ] Test Streamlit dashboards (need streamlit)
- [ ] Create launcher script
- [ ] Test all dashboard ports
- [ ] Verify Unified Hub (8100) works
- [ ] Document access methods
- [ ] Add to system startup (optional)

## 🚀 Next Steps

1. **Run installation commands**
2. **Test individual dashboards**
3. **Create launcher script**
4. **Access Unified Hub at http://localhost:8100**
5. **Bookmark dashboard URLs**

---

**Note**: All dashboard Python files are already restored from your personal laptop. You just need to install the missing `streamlit` package and optional dashboard components.
