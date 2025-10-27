# Project Backlog Visualization Dashboard

## Purpose
Web-based dashboard showing project status, priorities, and backlog visualization across all Maia components.

## Command Usage
```bash
# Launch dashboard (from MAIA_ROOT)
streamlit run claude/tools/project_management/project_backlog_dashboard.py

# Launch on specific port
streamlit run claude/tools/project_management/project_backlog_dashboard.py --server.port=8505

# Launch with dark theme
streamlit run claude/tools/project_management/project_backlog_dashboard.py --theme.base=dark
```

**Dashboard URL**: http://localhost:8501

## Dashboard Features
- **Project Overview**: Active projects with status indicators
- **Backlog Management**: Prioritized task lists with effort estimates
- **Progress Tracking**: Visual progress bars and completion metrics
- **Agent Status**: Current agent workloads and capabilities
- **Recent Activity**: Latest commits, files created, achievements
- **Priority Matrix**: Eisenhower matrix for task prioritization

## Dashboard Sections

### 🎯 Executive Summary
- Active projects count
- Total backlog items
- Weekly progress metrics
- Upcoming deadlines

### 📋 Project Status Board
- **In Progress**: Current active work
- **Ready to Start**: Prioritized backlog
- **Blocked**: Items waiting on dependencies
- **Completed**: Recent achievements

### 🔥 Priority Heatmap
- High Impact / High Effort quadrant
- Quick Wins identification
- Strategic initiatives tracking
- Resource allocation visualization

### 📊 Analytics
- Velocity trends
- Token usage patterns
- Agent utilization metrics
- Completion rate forecasting

## Implementation Details
1. **Data Source**: SQLite database (`claude/data/project_registry.db`)
2. **Web Framework**: Streamlit with Plotly visualizations
3. **Database Integration**: Direct SQL queries via sqlite3
4. **Interactive Features**:
   - Click project IDs to view details
   - Filter by status/priority/category
   - Real-time data refresh (60s cache)
   - Responsive charts with hover tooltips
5. **Implementation File**: `claude/tools/project_management/project_backlog_dashboard.py`

## Status
✅ **IMPLEMENTED** - Ready to use

**Implementation**: `claude/tools/project_management/project_backlog_dashboard.py` (25KB, 700+ lines)

**Dependencies**:
- streamlit (installed)
- plotly (installed)
- pandas (installed)

**Runtime**: No AI processing cost - pure local visualization

## Success Metrics
- Clear visibility into all projects
- Easy prioritization and planning
- Reduced context switching
- Better resource allocation decisions