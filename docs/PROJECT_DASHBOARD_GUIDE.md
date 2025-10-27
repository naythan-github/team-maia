# Maia Project Dashboard Guide

## Quick Start

### Launch Dashboard
```bash
# Option 1: Quick launcher script
./launch_dashboard.sh

# Option 2: Direct command
streamlit run claude/tools/project_management/project_backlog_dashboard.py

# Option 3: Custom port
streamlit run claude/tools/project_management/project_backlog_dashboard.py --server.port=8888
```

**Access**: http://localhost:8501

---

## Dashboard Sections

### 📊 Executive Summary
- **Active Projects**: Current work in progress
- **Backlog Items**: Planned projects ready to start
- **Completion Velocity**: Projects completed in last 30 days
- **Total Effort**: Hours estimated vs actual

### 📋 Project Status Board
4 tabs showing projects by status:
- **Active**: Currently in progress
- **Planned**: Ready to start (prioritized backlog)
- **Blocked**: Waiting on dependencies
- **Completed**: Finished projects with metrics

**Features**:
- Color-coded priority badges (🔴 Critical, 🟠 High, 🟡 Medium, 🟢 Low)
- Effort estimates and actual hours
- Deliverable counts
- Click project ID to view details

### 🎯 Priority Heatmap
Scatter plot showing **Impact vs Effort** for all projects:

**Quadrants**:
- **Top-Left**: Quick Wins (High Impact / Low Effort) ⭐
- **Top-Right**: Strategic Initiatives (High Impact / High Effort)
- **Bottom-Left**: Low Priority (Low Impact / Low Effort)
- **Bottom-Right**: Time Sinks (Low Impact / High Effort)

**Quick Wins Section**: Automatically identifies high-value, low-effort projects

### 📈 Analytics

#### Completion Trend
Line chart showing projects completed over last 90 days
- Weekly aggregation
- Actual vs estimated hours
- Velocity trends

#### Category Distribution
Pie chart showing project breakdown by category:
- ServiceDesk
- SRE
- Agent Enhancement
- Security
- DevOps
- etc.

#### Effort Variance
Bar chart showing estimation accuracy:
- Green bars: Under estimate (delivered faster)
- Red bars: Over estimate (took longer)
- Helps improve future estimates

---

## Interactive Features

### Project Details Drill-Down
1. Click any **Project ID** in the status board
2. Details expand below showing:
   - Full description
   - All deliverables with status
   - Dependencies (if any)
   - Timeline (created → started → completed)
   - Effort variance

### Data Refresh
- **Automatic**: Data cached for 60 seconds
- **Manual**: Click "🔄 Refresh Data" button in sidebar
- **Real-time**: Updates reflect immediately after CLI changes

### Filters
- Select specific project from dropdown
- Filter by status in tabs
- Hover over charts for detailed tooltips

---

## Technical Details

### Data Source
- **Database**: `claude/data/project_registry.db`
- **Schema**: projects, deliverables, dependencies, project_updates
- **Connection**: SQLite3 with WAL mode

### Performance
- **Query Latency**: <100ms (cached)
- **Load Time**: ~2-3 seconds initial
- **Refresh**: <1 second
- **Cache TTL**: 60 seconds

### Dependencies
All pre-installed:
- `streamlit==1.50.0` - Web framework
- `plotly==6.3.0` - Interactive charts
- `pandas==2.3.3` - Data manipulation

### Files
- **Dashboard**: `claude/tools/project_management/project_backlog_dashboard.py` (25KB)
- **Database**: `claude/data/project_registry.db`
- **Launcher**: `launch_dashboard.sh`
- **Command Spec**: `claude/commands/project_backlog_dashboard.md`

---

## Integration with CLI

The dashboard reads from the same database as the CLI tool:

```bash
# Add project via CLI
python3 claude/tools/project_management/project_registry.py add \
  --project-id PROJ-TEST-001 \
  --name "Test Project" \
  --status planned \
  --priority high

# View in dashboard
# Refresh dashboard → new project appears
```

**Workflow**:
1. Manage projects with CLI (add, update, start, complete)
2. Visualize progress in dashboard
3. Both tools share same SQLite database

---

## Troubleshooting

### Dashboard won't start
```bash
# Check if port 8501 is available
lsof -i :8501

# Use different port
streamlit run claude/tools/project_management/project_backlog_dashboard.py --server.port=8888
```

### Database not found
```bash
# Verify database exists
ls -lh claude/data/project_registry.db

# Check you're in MAIA_ROOT
pwd  # Should be ~/git/maia
```

### Missing dependencies
```bash
# Reinstall packages
pip3 install streamlit plotly pandas
```

### Charts not rendering
- Clear browser cache
- Try different browser
- Check JavaScript is enabled

### Data not updating
- Click "🔄 Refresh Data" button
- Wait 60 seconds for cache expiry
- Restart dashboard

---

## Best Practices

### Daily Workflow
1. **Morning**: Check dashboard for active projects and priorities
2. **During Work**: Use CLI to update status (`project_registry.py update`)
3. **End of Day**: Review progress in Analytics section
4. **Weekly**: Check velocity trends and adjust priorities

### Project Planning
1. Use **Priority Heatmap** to identify Quick Wins
2. Start with high-impact, low-effort projects
3. Monitor **Completion Trend** for velocity patterns
4. Review **Effort Variance** to improve estimates

### Team Collaboration
1. Share dashboard URL (run on shared server)
2. Use dashboard for standup meetings
3. Track dependencies in Dependencies tab
4. Export project list for external tools

---

## Future Enhancements

Potential additions (not yet implemented):
- Gantt chart for project timelines
- Team member assignment tracking
- Real-time collaboration features
- Email notifications for blocked projects
- Integration with GitHub issues
- Confluence export

---

## Support

**Documentation**:
- CLI Tool: `docs/PROJECT_REGISTRY_QUICK_REF.md`
- Project Plan: `claude/data/MAIA_PROJECT_REGISTRY_SYSTEM.md`
- Database Schema: `claude/data/project_registry_schema.sql`

**Status**: ✅ Production-ready (implemented 2025-10-27)
