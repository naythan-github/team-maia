# TDD Test Plan: Project Backlog Dashboard
**Date**: 2025-10-27
**Agents**: Domain Specialist (Streamlit) + SRE Principal Engineer
**Target**: `/Users/naythandawe/git/maia/claude/tools/project_management/project_backlog_dashboard.py`

---

## Executive Summary

### Current State Analysis
**Dashboard File**: `claude/tools/project_management/project_backlog_dashboard.py`
- **Status**: ❌ NOT WORKING (user confirmed: "well that isn't working")
- **Type**: Streamlit web application (834 lines)
- **Database**: SQLite at `claude/data/project_registry.db` (34 projects, 106KB)
- **Issue**: Dashboard runs with warnings but needs Streamlit server (`streamlit run` command)

### Root Cause Diagnosis
1. **Dashboard Execution Issue**:
   - Dashboard is Python script that requires Streamlit server
   - When run directly with `python3`, it shows warnings: "to view this Streamlit app on a browser, run it with the following command: streamlit run..."
   - NOT a code bug - this is EXPECTED Streamlit behavior

2. **Integration Gap**:
   - Dashboard NOT registered with unified dashboard hub (port 8100)
   - Hub at `claude/tools/monitoring/unified_dashboard_platform.py` manages all dashboards
   - Missing registration means dashboard not accessible via centralized hub
   - Other dashboards registered via pattern: `claude/tools/orchestration/register_agent_dashboard.py`

3. **Dashboard Hub System** (identified from codebase):
   - **Hub Location**: `claude/tools/monitoring/unified_dashboard_platform.py`
   - **Hub Port**: 8100 (Flask-based service discovery)
   - **Control Script**: `claude/tools/monitoring/dashboard_hub_control.sh`
   - **Registry Database**: `claude/data/dashboard_registry.db` (SQLite)
   - **Configuration**: `claude/tools/monitoring/config/dashboard_services.yaml`
   - **Port Range**: 8050-8099 (reserved for dashboards)
   - **Registration API**: `DashboardRegistry.register_dashboard(DashboardConfig)` class

---

## Test Strategy

### Test Pyramid
```
          /\
         /  \        E2E Tests (5%)
        /────\       - Full dashboard hub integration
       /      \      - End-user workflows
      /────────\     Integration Tests (25%)
     /          \    - Database queries
    /            \   - Chart rendering
   /──────────────\  Unit Tests (70%)
  /                \ - Individual functions
 /                  \- Data transformations
/────────────────────\
```

### Testing Approach
1. **Unit Tests** (70% coverage target):
   - Database connection and path resolution
   - SQL query functions return correct data structures
   - Data transformation logic (priority mapping, date formatting)
   - Utility functions (emoji mapping, color schemes)

2. **Integration Tests** (25% coverage target):
   - End-to-end database query → DataFrame → display logic
   - Multi-table JOIN queries work correctly
   - Streamlit caching behavior (60-second TTL)
   - Chart generation with Plotly (figure objects valid)

3. **End-to-End Tests** (5% coverage target):
   - Dashboard hub registration successful
   - Dashboard accessible via allocated port
   - Health endpoint responds correctly
   - Hub control scripts work (start/stop/status)

---

## Test Cases

### Phase 1: Unit Tests (RED → GREEN → REFACTOR)

#### Test Suite 1: Database Connection
```python
class TestDatabaseConnection:
    def test_get_database_path_returns_absolute_path(self):
        """Database path resolution returns absolute path"""

    def test_get_database_path_respects_maia_root(self):
        """Database path correctly uses MAIA_ROOT environment variable"""

    def test_get_db_connection_succeeds_with_valid_db(self):
        """Database connection succeeds when DB file exists"""

    def test_get_db_connection_handles_missing_db_gracefully(self):
        """Connection attempt with missing DB raises clear error"""

    def test_database_has_required_tables(self):
        """Database contains: projects, deliverables, dependencies, project_updates"""
```

#### Test Suite 2: Executive Summary Queries
```python
class TestExecutiveSummary:
    def test_get_executive_summary_returns_dict_with_required_keys(self):
        """Summary dict contains: by_status, active_count, active_effort, backlog_count, etc."""

    def test_by_status_counts_match_database(self):
        """Status counts from summary match direct DB queries"""

    def test_active_effort_calculates_correctly(self):
        """Active effort sums all effort_hours for status='active'"""

    def test_velocity_30d_filters_date_correctly(self):
        """Velocity calculation only includes last 30 days"""

    def test_blocked_count_identifies_blocked_projects(self):
        """Blocked count matches projects with status='blocked'"""

    def test_executive_summary_handles_empty_database(self):
        """Summary returns zeros/empty dicts when database has no projects"""
```

#### Test Suite 3: Project Status Queries
```python
class TestProjectStatusQueries:
    def test_get_projects_by_status_returns_dataframe(self):
        """Query returns pandas DataFrame object"""

    def test_dataframe_contains_required_columns(self):
        """DataFrame has: id, name, status, priority, effort_hours, impact, etc."""

    def test_priority_ordering_correct(self):
        """Projects ordered: critical, high, medium, low"""

    def test_deliverable_count_joins_correctly(self):
        """Deliverable count matches LEFT JOIN on deliverables table"""

    def test_dependency_count_joins_correctly(self):
        """Dependency count matches LEFT JOIN on dependencies table"""

    def test_status_filter_returns_only_matching_projects(self):
        """get_projects_by_status('active') returns ONLY active projects"""
```

#### Test Suite 4: Priority Matrix
```python
class TestPriorityMatrix:
    def test_get_priority_matrix_filters_planned_active_only(self):
        """Matrix includes only projects with status in ('planned', 'active')"""

    def test_matrix_excludes_null_effort_or_impact(self):
        """Matrix excludes projects where effort_hours IS NULL or impact IS NULL"""

    def test_matrix_dataframe_structure(self):
        """DataFrame contains: id, name, priority, effort_hours, impact, status, category"""

    def test_impact_mapping_to_numeric_scale(self):
        """Impact values map correctly: low=1, medium=2, high=3"""
```

#### Test Suite 5: Analytics Data
```python
class TestAnalyticsData:
    def test_get_analytics_data_returns_dict_with_five_keys(self):
        """Returns: completion_trend, category_distribution, status_distribution, priority_distribution, effort_variance"""

    def test_completion_trend_groups_by_week(self):
        """Trend uses strftime('%Y-%W') for weekly grouping"""

    def test_completion_trend_filters_90_days(self):
        """Only includes completed projects from last 90 days"""

    def test_category_distribution_limits_top_10(self):
        """Category distribution returns max 10 rows"""

    def test_effort_variance_calculates_percentage_correctly(self):
        """Variance % = (actual - estimated) * 100 / estimated"""

    def test_effort_variance_sorts_by_absolute_variance(self):
        """Results ordered by ABS(variance) DESC"""
```

#### Test Suite 6: Project Details
```python
class TestProjectDetails:
    def test_get_project_details_returns_dict(self):
        """Returns dict or None if project not found"""

    def test_project_details_includes_deliverables(self):
        """Dict contains 'deliverables' key with list of deliverable dicts"""

    def test_project_details_includes_dependencies(self):
        """Dict contains 'dependencies' key with dependency details + related project info"""

    def test_project_details_includes_updates(self):
        """Dict contains 'updates' key with last 10 project updates ordered DESC"""

    def test_project_details_handles_nonexistent_project(self):
        """Returns None when project_id doesn't exist"""
```

### Phase 2: Integration Tests

#### Test Suite 7: Streamlit Component Rendering
```python
class TestStreamlitComponents:
    @mock.patch('streamlit.metric')
    @mock.patch('streamlit.header')
    def test_render_executive_summary_calls_streamlit_api(self, mock_header, mock_metric):
        """Executive summary renders without errors"""

    @mock.patch('streamlit.tabs')
    def test_render_project_status_board_creates_four_tabs(self, mock_tabs):
        """Status board creates tabs: Active, Planned, Blocked, Completed"""

    @mock.patch('streamlit.dataframe')
    def test_render_project_table_displays_dataframe(self, mock_dataframe):
        """Project table calls st.dataframe with formatted data"""

    @mock.patch('streamlit.plotly_chart')
    def test_render_priority_heatmap_generates_scatter_plot(self, mock_chart):
        """Priority heatmap generates Plotly scatter plot"""

    def test_emoji_mapping_adds_correct_icons(self):
        """Priority/status emoji mapping applies correct icons"""
```

#### Test Suite 8: Chart Generation
```python
class TestChartGeneration:
    def test_status_breakdown_bar_chart_structure(self):
        """Bar chart has correct data structure and colors"""

    def test_completion_velocity_line_chart_structure(self):
        """Line chart shows completed projects over time"""

    def test_category_pie_chart_structure(self):
        """Pie chart shows project distribution by category"""

    def test_effort_variance_bar_chart_colors(self):
        """Variance chart: red for over-estimate, green for under-estimate"""

    def test_priority_scatter_plot_quadrants(self):
        """Scatter plot includes quadrant lines and labels"""
```

### Phase 3: Dashboard Hub Integration Tests

#### Test Suite 9: Dashboard Registration
```python
class TestDashboardRegistration:
    def test_register_project_backlog_dashboard_succeeds(self):
        """Registration script successfully registers dashboard with hub"""

    def test_dashboard_config_has_required_fields(self):
        """DashboardConfig includes: name, description, file_path, port, host, etc."""

    def test_port_allocation_in_valid_range(self):
        """Allocated port is between 8050-8099"""

    def test_registration_inserts_into_registry_db(self):
        """Dashboard appears in dashboard_registry.db after registration"""

    def test_dashboard_category_set_to_project_management(self):
        """Category field = 'project_management'"""
```

#### Test Suite 10: Hub Integration
```python
class TestHubIntegration:
    def test_dashboard_starts_via_hub_control_script(self):
        """Dashboard can be started via unified dashboard platform"""

    def test_dashboard_accessible_on_allocated_port(self):
        """HTTP GET to http://127.0.0.1:{port} returns 200"""

    def test_health_endpoint_responds(self):
        """Health endpoint returns valid response"""

    def test_dashboard_appears_in_hub_ui(self):
        """Dashboard listed when accessing http://127.0.0.1:8100"""

    def test_dashboard_stop_via_hub_control_script(self):
        """Dashboard stops cleanly via hub control"""
```

### Phase 4: End-to-End Tests

#### Test Suite 11: Full User Workflow
```python
class TestEndToEndWorkflow:
    def test_user_can_start_dashboard_from_hub(self):
        """User navigates to hub → clicks 'Start' → dashboard launches"""

    def test_user_can_view_executive_summary(self):
        """Dashboard loads → executive summary displays metrics"""

    def test_user_can_filter_projects_by_status(self):
        """User clicks Active tab → sees only active projects"""

    def test_user_can_drill_into_project_details(self):
        """User selects project from dropdown → sees deliverables/dependencies"""

    def test_user_can_view_priority_heatmap(self):
        """User navigates to Priority Heatmap → scatter plot renders"""

    def test_user_can_refresh_data(self):
        """User clicks Refresh button → cache clears → data reloads"""
```

---

## Test Implementation Details

### Test File Structure
```
/Users/naythandawe/git/maia/tests/
├── test_project_backlog_dashboard.py          # Main test file
├── test_project_backlog_dashboard_integration.py  # Integration tests
├── test_project_backlog_dashboard_e2e.py      # End-to-end tests
└── fixtures/
    ├── test_project_registry.db               # Test database fixture
    └── mock_streamlit_context.py              # Streamlit mocking utilities
```

### Test Database Fixture
```sql
-- Create minimal test database with known data
CREATE TABLE projects (
    id TEXT PRIMARY KEY,
    name TEXT,
    status TEXT CHECK(status IN ('planned', 'active', 'blocked', 'completed', 'archived')),
    priority TEXT CHECK(priority IN ('critical', 'high', 'medium', 'low')),
    effort_hours INTEGER,
    actual_hours INTEGER,
    impact TEXT CHECK(impact IN ('low', 'medium', 'high')),
    category TEXT,
    description TEXT,
    created_date TEXT,
    started_date TEXT,
    completed_date TEXT
);

-- Insert test data (5 projects across all statuses)
INSERT INTO projects VALUES
('TEST-001', 'Test Active Project', 'active', 'high', 40, NULL, 'high', 'testing', 'Test project', '2025-10-01', '2025-10-05', NULL),
('TEST-002', 'Test Planned Project', 'planned', 'medium', 20, NULL, 'medium', 'testing', 'Test project', '2025-10-01', NULL, NULL),
('TEST-003', 'Test Blocked Project', 'blocked', 'critical', 60, NULL, 'high', 'testing', 'Test project', '2025-10-01', '2025-10-05', NULL),
('TEST-004', 'Test Completed Project', 'completed', 'high', 30, 35, 'high', 'testing', 'Test project', '2025-09-01', '2025-09-05', '2025-09-28'),
('TEST-005', 'Test Low Priority', 'planned', 'low', 10, NULL, 'low', 'testing', 'Test project', '2025-10-01', NULL, NULL);
```

### Mocking Strategy

#### Streamlit Components
```python
import pytest
from unittest import mock

@pytest.fixture
def mock_streamlit():
    """Mock all Streamlit components"""
    with mock.patch('streamlit.set_page_config'), \
         mock.patch('streamlit.title'), \
         mock.patch('streamlit.header'), \
         mock.patch('streamlit.subheader'), \
         mock.patch('streamlit.markdown'), \
         mock.patch('streamlit.metric'), \
         mock.patch('streamlit.columns'), \
         mock.patch('streamlit.tabs'), \
         mock.patch('streamlit.dataframe'), \
         mock.patch('streamlit.plotly_chart'), \
         mock.patch('streamlit.button'), \
         mock.patch('streamlit.selectbox'), \
         mock.patch('streamlit.radio'), \
         mock.patch('streamlit.info'), \
         mock.patch('streamlit.error'), \
         mock.patch('streamlit.cache_data'), \
         mock.patch('streamlit.cache_resource'), \
         mock.patch('streamlit.sidebar'), \
         mock.patch('streamlit.rerun'):
        yield
```

#### Database Connection
```python
@pytest.fixture
def test_db_path(tmp_path):
    """Create temporary test database"""
    db_path = tmp_path / "test_project_registry.db"

    # Create tables and insert test data
    import sqlite3
    conn = sqlite3.connect(db_path)

    # Create schema (from fixture SQL above)
    # ... schema creation ...

    conn.commit()
    conn.close()

    return str(db_path)

@pytest.fixture
def mock_db_path(test_db_path, monkeypatch):
    """Monkeypatch DB_PATH to use test database"""
    import claude.tools.project_management.project_backlog_dashboard as dashboard
    monkeypatch.setattr(dashboard, 'DB_PATH', test_db_path)
```

---

## Success Criteria

### Phase 1: Unit Tests (RED → GREEN)
- ✅ All 30+ unit tests written and initially FAILING
- ✅ Dashboard code fixed to make all unit tests PASS
- ✅ Test coverage ≥70% for all query functions
- ✅ No test uses actual database (all use fixtures/mocks)

### Phase 2: Integration Tests (GREEN → REFACTOR)
- ✅ All 15+ integration tests written and PASSING
- ✅ Streamlit component rendering tested with mocks
- ✅ Chart generation validated (Plotly figure objects)
- ✅ Cache behavior verified (TTL=60 seconds)

### Phase 3: Hub Integration (GREEN)
- ✅ Dashboard registration script created and tested
- ✅ Dashboard appears in `dashboard_registry.db`
- ✅ Port allocated in valid range (8050-8099)
- ✅ Dashboard starts/stops via hub control script
- ✅ Dashboard accessible at allocated port

### Phase 4: End-to-End Validation (REFACTOR)
- ✅ User can start dashboard from hub UI
- ✅ All dashboard views render correctly
- ✅ Data loads from real database (34 projects)
- ✅ Interactive features work (tabs, dropdown, refresh)
- ✅ Health endpoint responds correctly

### Phase 5: Documentation
- ✅ Test plan document created (this file)
- ✅ Test implementation guide written
- ✅ Integration instructions documented
- ✅ Troubleshooting guide included

---

## Implementation Timeline

### Step 1: Test Infrastructure (30 minutes)
- Create test directory structure
- Set up pytest configuration
- Create test database fixture
- Write Streamlit mocking utilities

### Step 2: Unit Tests - RED Phase (60 minutes)
- Write all unit tests (expect FAILURES)
- Verify tests fail for right reasons
- Document test failures

### Step 3: Fix Dashboard - GREEN Phase (45 minutes)
- Fix database connection issues (if any)
- Fix query logic to pass tests
- Fix data transformation logic
- Verify all unit tests PASS

### Step 4: Integration Tests (45 minutes)
- Write integration tests
- Test Streamlit component rendering
- Test chart generation
- Verify all integration tests PASS

### Step 5: Hub Integration (30 minutes)
- Create dashboard registration script
- Test registration with hub
- Verify dashboard starts via hub
- Test health endpoint

### Step 6: End-to-End Testing (30 minutes)
- Start full dashboard hub
- Test complete user workflows
- Verify all features working
- Document any issues

### Step 7: Documentation (30 minutes)
- Update integration instructions
- Document troubleshooting steps
- Create quick-start guide
- Update capability_index.md

**Total Estimated Time**: 4 hours

---

## Risk Assessment

### High-Risk Areas
1. **Streamlit Mocking Complexity**:
   - Risk: Streamlit's context-dependent API hard to mock
   - Mitigation: Use `@mock.patch` at module level, not function level
   - Fallback: Test logic separately from Streamlit rendering

2. **Database Schema Assumptions**:
   - Risk: Test database schema doesn't match production
   - Mitigation: Use actual schema from `project_registry.db`
   - Validation: Query `sqlite_master` to verify tables/columns

3. **Port Allocation Conflicts**:
   - Risk: Allocated port already in use
   - Mitigation: Hub has port availability checking
   - Fallback: Manual port selection if allocation fails

### Medium-Risk Areas
1. **Cache Behavior**:
   - Risk: Streamlit cache doesn't work as expected in tests
   - Mitigation: Test cache bypass with `st.cache_data.clear()`

2. **Date Filtering Logic**:
   - Risk: SQLite `datetime()` functions behave differently in tests
   - Mitigation: Use fixed test dates (not relative)

### Low-Risk Areas
1. **Chart Rendering**: Plotly generates figures independently of Streamlit
2. **Database Queries**: Standard SQLite, well-tested
3. **Hub Registration**: Existing proven pattern from other dashboards

---

## Deliverable Checklist

- [ ] Test Plan Document (THIS FILE)
- [ ] Test Implementation File (`test_project_backlog_dashboard.py`)
- [ ] Integration Test File (`test_project_backlog_dashboard_integration.py`)
- [ ] E2E Test File (`test_project_backlog_dashboard_e2e.py`)
- [ ] Dashboard Registration Script (`register_project_backlog_dashboard.py`)
- [ ] Test Database Fixture (`fixtures/test_project_registry.db`)
- [ ] Streamlit Mocking Utilities (`fixtures/mock_streamlit_context.py`)
- [ ] Integration Documentation (`PROJECT_BACKLOG_DASHBOARD_INTEGRATION.md`)
- [ ] Quick-Start Guide (section in integration doc)
- [ ] Troubleshooting Guide (section in integration doc)
- [ ] Updated `capability_index.md` entry

---

## Appendix A: Dashboard Hub Architecture

```
┌────────────────────────────────────────────────────────────┐
│ Unified Dashboard Hub (Port 8100)                         │
│ - Service Discovery UI                                     │
│ - Health Monitoring                                        │
│ - Start/Stop Controls                                      │
└────────────────────────────────────────────────────────────┘
                           │
                           │ (HTTP)
                           ▼
┌────────────────────────────────────────────────────────────┐
│ Dashboard Registry (SQLite)                                │
│ - claude/data/dashboard_registry.db                        │
│ - Tables: dashboards, dashboard_logs                       │
└────────────────────────────────────────────────────────────┘
                           │
                           │ (manages)
                           ▼
┌──────────────────┬──────────────────┬─────────────────────┐
│ Agent Dashboard  │ ServiceDesk Dash │ PROJECT BACKLOG ←NEW│
│ Port: 8066       │ Port: 8065       │ Port: TBD (8050+)  │
│ Category: Orch   │ Category: Ops    │ Category: PM       │
└──────────────────┴──────────────────┴─────────────────────┘
```

### Registration Flow
1. Developer creates dashboard Python file (Streamlit/Flask/Dash)
2. Developer creates registration script using `DashboardRegistry` API
3. Registration script:
   - Allocates port from available range (8050-8099)
   - Creates `DashboardConfig` object
   - Calls `registry.register_dashboard(config)`
   - Dashboard inserted into `dashboard_registry.db`
4. Dashboard appears in hub UI at `http://127.0.0.1:8100`
5. User clicks "Start" → Hub spawns dashboard process
6. Dashboard accessible at `http://127.0.0.1:{allocated_port}`

---

## Appendix B: Test Execution Commands

```bash
# Run all tests
pytest tests/test_project_backlog_dashboard*.py -v

# Run only unit tests
pytest tests/test_project_backlog_dashboard.py -v

# Run only integration tests
pytest tests/test_project_backlog_dashboard_integration.py -v

# Run only E2E tests
pytest tests/test_project_backlog_dashboard_e2e.py -v

# Run with coverage report
pytest tests/test_project_backlog_dashboard*.py --cov=claude.tools.project_management --cov-report=html

# Run specific test class
pytest tests/test_project_backlog_dashboard.py::TestDatabaseConnection -v

# Run specific test
pytest tests/test_project_backlog_dashboard.py::TestDatabaseConnection::test_get_database_path_returns_absolute_path -v

# Run in watch mode (re-run on file changes)
pytest-watch tests/test_project_backlog_dashboard.py

# Generate test report
pytest tests/ --html=tests/report.html --self-contained-html
```

---

## Appendix C: Known Issues & Workarounds

### Issue 1: Streamlit "No runtime found" Warning
- **Symptom**: `WARNING: No runtime found, using MemoryCacheStorageManager`
- **Root Cause**: Running Streamlit outside of `streamlit run` context
- **Impact**: Cache decorators (`@st.cache_data`) don't persist across runs
- **Workaround**: Expected behavior in tests; use `@mock.patch` to bypass caching
- **Resolution**: Not an error; tests will mock Streamlit components

### Issue 2: Database Path Resolution
- **Symptom**: `DB_PATH = "claude/data/project_registry.db"` is relative
- **Root Cause**: Relies on `MAIA_ROOT` environment variable
- **Impact**: Dashboard fails if run from wrong directory
- **Workaround**: Always run from MAIA root or set `MAIA_ROOT` env var
- **Resolution**: Tests will monkeypatch `DB_PATH` to use temp database

### Issue 3: Port Already in Use
- **Symptom**: Dashboard fails to start (port conflict)
- **Root Cause**: Another service using allocated port
- **Impact**: Dashboard won't start via hub
- **Workaround**: Use `lsof -i :{port}` to find conflicting process
- **Resolution**: Hub's `allocate_port()` checks availability before assignment

---

**End of Test Plan**
