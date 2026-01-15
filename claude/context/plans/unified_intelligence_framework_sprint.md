# TDD Sprint Plan: Unified Intelligence Framework

**Sprint ID**: SPRINT-INTEL-FRAMEWORK-001
**Created**: 2026-01-15
**Author**: SRE Principal Engineer Agent
**Status**: PENDING APPROVAL

---

## Problem Statement

Following the successful PMP Intelligence Service (SPRINT-PMP-INTEL-001), we identified similar friction points across other data sources:

| Issue | Impact | Affected Systems |
|-------|--------|------------------|
| No unified query interface | Maia must know 20+ OTC tools, column prefixes (TKT-*, TKTCT-*, TS-*) | OTC ServiceDesk |
| No freshness awareness | Queries against stale data without warning | PMP, OTC, Azure |
| Manual data refresh | User must remember to trigger collection | All sources |
| Inconsistent patterns | Different approaches per system | All sources |
| No extensibility | Adding new sources requires full implementation | Future sources |

---

## Solution: Unified Intelligence Framework

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              BaseIntelligenceService (Abstract)              │
│                                                              │
│  Common Interface:                                           │
│  - get_data_freshness_report() → Dict[str, FreshnessInfo]   │
│  - query_raw(sql, params) → QueryResult                      │
│  - refresh() → bool                                          │
│  - is_stale() → bool                                         │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ↓                     ↓                     ↓
┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐
│ PMPIntelligence   │ │ OTCIntelligence   │ │ AzureIntelligence │
│ Service           │ │ Service           │ │ Service (Future)  │
│ (SQLite)          │ │ (PostgreSQL)      │ │                   │
│                   │ │                   │ │                   │
│ Domain Methods:   │ │ Domain Methods:   │ │ Domain Methods:   │
│ - get_systems_by_ │ │ - get_tickets_by_ │ │ - get_costs_by_   │
│   organization()  │ │   team()          │ │   subscription()  │
│ - get_failed_     │ │ - get_open_       │ │ - get_resources() │
│   patches()       │ │   tickets()       │ │                   │
│ - get_vulnerable_ │ │ - get_user_       │ │                   │
│   systems()       │ │   workload()      │ │                   │
└───────────────────┘ └───────────────────┘ └───────────────────┘
        ✅ DONE              THIS SPRINT           FUTURE

┌─────────────────────────────────────────────────────────────┐
│                   CollectionScheduler                        │
│                                                              │
│  - schedule_daily_refresh(source, time)                     │
│  - run_pending_refreshes()                                   │
│  - get_schedule_status() → Dict[str, ScheduleInfo]          │
└─────────────────────────────────────────────────────────────┘
```

---

## Sprint Phases

### P0: Anti-Duplication Check
**Goal**: Verify no existing unified OTC service
**Model**: Haiku (mechanical search)
**Subagent**: Explore

| Check | Expected Result |
|-------|-----------------|
| `find claude/tools -name "*otc*intelligence*"` | No matches |
| `grep -r "OTCIntelligenceService" claude/` | No matches |
| `grep -r "class.*Intelligence.*Service" claude/tools/` | Only PMPIntelligenceService |

**Gate**: PASS if no duplicates found

---

### P1: Base Class & Core Infrastructure
**Goal**: Create extensible base class
**Model**: Sonnet (architecture design, code quality critical)
**Subagent**: None (direct implementation)

#### Files to Create
- `claude/tools/collection/base_intelligence_service.py`
- `claude/tools/collection/__init__.py`

#### Tests (8 tests)
```python
# tests/test_base_intelligence_service.py

class TestBaseIntelligenceServiceImport:
    def test_import_base_class(self):
        """Base class should be importable."""

    def test_base_class_is_abstract(self):
        """Cannot instantiate directly."""

class TestQueryResultDataclass:
    def test_query_result_structure(self):
        """QueryResult has data, source, timestamp, is_stale, warning."""

    def test_staleness_auto_detection(self):
        """is_stale=True when extraction_timestamp > threshold."""

class TestFreshnessInfo:
    def test_freshness_info_structure(self):
        """FreshnessInfo has last_refresh, days_old, is_stale, record_count."""

class TestBaseClassInterface:
    def test_requires_get_data_freshness_report(self):
        """Subclass must implement get_data_freshness_report()."""

    def test_requires_query_raw(self):
        """Subclass must implement query_raw()."""

    def test_requires_refresh(self):
        """Subclass must implement refresh()."""
```

#### Base Class Design
```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

@dataclass
class QueryResult:
    """Standardized query result across all intelligence services."""
    data: List[Dict[str, Any]]
    source: str  # "pmp_config.db", "servicedesk.tickets", etc.
    extraction_timestamp: datetime
    is_stale: bool = False
    staleness_warning: Optional[str] = None
    query_time_ms: int = 0

    def __post_init__(self):
        if self.extraction_timestamp:
            days_old = (datetime.now() - self.extraction_timestamp).days
            if days_old > 7 and not self.is_stale:
                self.is_stale = True
                self.staleness_warning = f"Data is {days_old} days old"

@dataclass
class FreshnessInfo:
    """Data freshness information for a source."""
    last_refresh: Optional[datetime]
    days_old: int
    is_stale: bool
    record_count: int
    warning: Optional[str] = None

class BaseIntelligenceService(ABC):
    """Abstract base for all intelligence services."""

    STALENESS_THRESHOLD_DAYS = 7

    @abstractmethod
    def get_data_freshness_report(self) -> Dict[str, FreshnessInfo]:
        """Return freshness info for all data sources."""
        pass

    @abstractmethod
    def query_raw(self, sql: str, params: tuple = ()) -> QueryResult:
        """Execute raw SQL query."""
        pass

    @abstractmethod
    def refresh(self) -> bool:
        """Refresh data from source. Returns True on success."""
        pass

    def is_stale(self) -> bool:
        """Check if any data source is stale."""
        report = self.get_data_freshness_report()
        return any(info.is_stale for info in report.values())
```

**Gate**: 8/8 tests pass

---

### P2: OTC Intelligence Service - Core Implementation
**Goal**: Unified OTC query interface
**Model**: Sonnet (complex PostgreSQL integration, error handling critical)
**Subagent**: None (direct implementation)

#### Files to Create
- `claude/tools/collection/otc_intelligence_service.py`

#### Tests (18 tests)
```python
# tests/test_otc_intelligence_service.py

class TestOTCIntelligenceServiceImport:
    def test_import_service(self):
        """OTCIntelligenceService should be importable."""

    def test_inherits_base_class(self):
        """Should inherit from BaseIntelligenceService."""

class TestServiceInitialization:
    def test_init_with_default_connection(self):
        """Uses default PostgreSQL connection settings."""

    def test_init_with_custom_connection(self):
        """Accepts custom connection parameters."""

    def test_connection_failure_handling(self):
        """Graceful error when PostgreSQL unavailable."""

class TestFreshnessReport:
    def test_freshness_report_structure(self):
        """Returns FreshnessInfo for tickets, comments, timesheets."""

    def test_freshness_uses_v_data_freshness_view(self):
        """Queries servicedesk.v_data_freshness."""

    def test_staleness_detection(self):
        """Marks sources stale when >7 days old."""

class TestTicketQueries:
    def test_get_tickets_by_team(self):
        """Filters by TKT-Team field."""

    def test_get_open_tickets(self):
        """Excludes Closed, Incident Resolved."""

    def test_get_unassigned_tickets(self):
        """Filters PendingAssignment."""

    def test_normalized_field_names(self):
        """Returns team, status, assignee (not TKT-Team, TKT-Status)."""

class TestUserQueries:
    def test_get_user_workload(self):
        """Returns open tickets for user."""

    def test_get_user_activity(self):
        """Returns 30-day activity summary."""

class TestTeamQueries:
    def test_get_team_backlog(self):
        """Returns unassigned team tickets."""

    def test_get_team_health_summary(self):
        """Returns ticket counts by status per team."""

class TestRawQueryInterface:
    def test_query_raw_returns_query_result(self):
        """Raw SQL returns QueryResult dataclass."""

    def test_query_raw_includes_timing(self):
        """query_time_ms is populated."""
```

#### Key Implementation Details

**PostgreSQL Connection** (from exploration):
```python
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "servicedesk",
    "user": "servicedesk_user",
    "password": "ServiceDesk2025!SecurePass"
}
```

**Column Name Normalization** (critical for usability):
```python
# Input: "TKT-Team", "TKT-Status", "TKT-Assigned To User"
# Output: "team", "status", "assignee"

COLUMN_NORMALIZATION = {
    "TKT-Team": "team",
    "TKT-Status": "status",
    "TKT-Assigned To User": "assignee",
    "TKT-Ticket ID": "ticket_id",
    "TKT-Title": "title",
    "TKT-Created Time": "created_time",
    "TKT-Category": "category",
    "TKT-Severity": "priority",
    "TKT-Account Name": "account",
}
```

**Freshness Query**:
```python
def get_data_freshness_report(self) -> Dict[str, FreshnessInfo]:
    sql = "SELECT * FROM servicedesk.v_data_freshness"
    # Parse view_name, last_loaded, age, total_records
```

**Gate**: 18/18 tests pass

---

### P3: OTC Query Templates
**Goal**: Pre-built SQL patterns for common queries
**Model**: Sonnet (SQL accuracy critical)
**Subagent**: None (direct implementation)

#### Files to Create
- `claude/tools/collection/otc_query_templates.py`

#### Tests (10 tests)
```python
# tests/test_otc_query_templates.py

class TestTemplateRegistry:
    def test_templates_dict_exists(self):
        """TEMPLATES dictionary is populated."""

    def test_template_structure(self):
        """Each template has name, description, parameters, sql."""

class TestTeamTemplates:
    def test_team_workload_template(self):
        """team_workload returns open/unassigned counts."""

    def test_team_backlog_template(self):
        """team_backlog returns unassigned tickets."""

class TestUserTemplates:
    def test_user_workload_template(self):
        """user_workload returns user's open tickets."""

    def test_user_activity_template(self):
        """user_activity returns 30-day summary."""

class TestTicketTemplates:
    def test_ticket_age_distribution_template(self):
        """ticket_age_distribution buckets by age."""

    def test_open_tickets_by_priority_template(self):
        """open_tickets_by_priority groups by severity."""

class TestTemplateExecution:
    def test_templates_execute_without_error(self):
        """All templates execute successfully."""

    def test_describe_templates_function(self):
        """describe_templates() returns readable summary."""
```

#### Templates to Create (10 templates)
```python
TEMPLATES = {
    # Team queries
    "team_workload": "Open/closed/unassigned by team",
    "team_backlog": "Unassigned tickets per team",
    "engineering_summary": "All 3 engineering queues summary",

    # User queries
    "user_workload": "User's open tickets with age",
    "user_activity": "30-day activity summary",
    "user_hours": "Timesheet hours per user",

    # Ticket queries
    "ticket_age_distribution": "Tickets by age bucket",
    "open_tickets_by_priority": "Open tickets grouped by severity",
    "recent_tickets": "Tickets created in last N days",

    # Quality queries
    "orphaned_data_summary": "Orphaned comments/timesheets count",
}
```

**Gate**: 10/10 tests pass

---

### P4: Collection Scheduler
**Goal**: Automated daily data refresh
**Model**: Sonnet (scheduler logic, cron-style parsing)
**Subagent**: None (direct implementation)

#### Files to Create
- `claude/tools/collection/scheduler.py`
- `~/.maia/config/collection_schedule.yaml` (user config)

#### Tests (10 tests)
```python
# tests/test_collection_scheduler.py

class TestSchedulerImport:
    def test_import_scheduler(self):
        """CollectionScheduler should be importable."""

class TestScheduleConfiguration:
    def test_load_schedule_from_yaml(self):
        """Loads schedule from ~/.maia/config/collection_schedule.yaml."""

    def test_default_schedule_when_no_config(self):
        """Uses sensible defaults if config missing."""

    def test_schedule_structure(self):
        """Each entry has source, refresh_time, enabled."""

class TestScheduleExecution:
    def test_get_pending_refreshes(self):
        """Returns sources due for refresh."""

    def test_run_single_refresh(self):
        """Executes refresh for one source."""

    def test_run_all_pending(self):
        """Executes all pending refreshes."""

    def test_refresh_updates_last_run(self):
        """Tracks last_run timestamp after refresh."""

class TestScheduleStatus:
    def test_get_schedule_status(self):
        """Returns status for all configured sources."""

    def test_status_includes_next_run(self):
        """Status shows next scheduled run time."""
```

#### Schedule Configuration
```yaml
# ~/.maia/config/collection_schedule.yaml
sources:
  pmp:
    refresh_time: "06:00"
    enabled: true
    refresh_command: "python3 claude/tools/pmp/pmp_resilient_extractor.py"

  otc:
    refresh_time: "06:30"
    enabled: true
    refresh_command: "python3 -m claude.tools.integrations.otc.load_to_postgres all"
```

**Gate**: 10/10 tests pass

---

### P5: PMP Service Refactor (Inherit Base Class)
**Goal**: Refactor existing PMPIntelligenceService to inherit from BaseIntelligenceService
**Model**: Sonnet (refactor existing working code)
**Subagent**: None (direct implementation)

#### Files to Modify
- `claude/tools/pmp/pmp_intelligence_service.py`

#### Tests (4 additional tests)
```python
# tests/test_pmp_intelligence_service.py (additions)

class TestBaseClassInheritance:
    def test_inherits_base_class(self):
        """PMPIntelligenceService inherits BaseIntelligenceService."""

    def test_returns_query_result_type(self):
        """Methods return QueryResult (not PMPQueryResult)."""

    def test_freshness_returns_freshness_info(self):
        """get_data_freshness_report returns FreshnessInfo objects."""

    def test_refresh_method_exists(self):
        """refresh() method is implemented."""
```

**Changes**:
1. Import and inherit from `BaseIntelligenceService`
2. Replace `PMPQueryResult` with `QueryResult` (or alias)
3. Return `FreshnessInfo` from `get_data_freshness_report()`
4. Add `refresh()` method (calls pmp_resilient_extractor)

**Gate**: All 34 existing tests pass + 4 new tests

---

### P6: Integration Tests
**Goal**: Test real database queries
**Model**: Sonnet (integration complexity)
**Subagent**: None (direct implementation)

#### Files to Create
- `tests/integration/test_otc_intelligence_integration.py`

#### Tests (8 tests, skip if PostgreSQL unavailable)
```python
# tests/integration/test_otc_intelligence_integration.py

pytestmark = pytest.mark.skipif(
    not has_postgresql_connection(),
    reason="PostgreSQL not available"
)

class TestRealDatabaseQueries:
    def test_service_connects_to_postgresql(self):
        """Service connects to servicedesk database."""

    def test_freshness_report_real_data(self):
        """Freshness report returns actual timestamps."""

    def test_get_tickets_by_team_real(self):
        """Returns real Cloud - Infrastructure tickets."""

    def test_get_user_workload_real(self):
        """Returns real workload for known user."""

class TestQueryPerformance:
    def test_team_query_under_1_second(self):
        """Team queries complete in <1s."""

    def test_freshness_query_under_500ms(self):
        """Freshness check is fast."""

class TestDataIntegrity:
    def test_normalized_field_names(self):
        """Results use normalized names (team, not TKT-Team)."""

    def test_no_null_required_fields(self):
        """ticket_id, team, status are never null."""
```

**Gate**: 8/8 integration tests pass (or skip if no PostgreSQL)

---

### P6.5: Documentation & Registration
**Goal**: Complete documentation, agent context, capability registration
**Model**: Sonnet (documentation quality matters for agent usability)
**Subagent**: None (direct implementation)

#### Files to Create/Modify
- `claude/context/knowledge/servicedesk/otc_intelligence_quickstart.md` (new)
- `claude/agents/data_analyst_agent.md` (add OTC section)
- `claude/data/databases/system/capabilities.db` (register tools)

#### Documentation Structure
```markdown
# OTC Intelligence Service - Quick Reference

## Quick Start
```python
from claude.tools.collection import OTCIntelligenceService

otc = OTCIntelligenceService()

# Always check freshness first
freshness = otc.get_data_freshness_report()

# Common queries
result = otc.get_tickets_by_team("Cloud - Infrastructure")
result = otc.get_user_workload("Dion Jewell")
result = otc.get_team_backlog("Cloud - Security")
```

## Normalized Field Names
| Database Column | Normalized Name |
|-----------------|-----------------|
| TKT-Team | team |
| TKT-Status | status |
| TKT-Assigned To User | assignee |
...
```

#### Capability Registration
```sql
INSERT INTO capabilities (name, type, category, path, keywords, purpose)
VALUES
('OTCIntelligenceService', 'tool', 'servicedesk',
 'claude/tools/collection/otc_intelligence_service.py',
 'otc, servicedesk, tickets, team, workload, query',
 'Unified query interface for OTC ServiceDesk data'),
('CollectionScheduler', 'tool', 'collection',
 'claude/tools/collection/scheduler.py',
 'scheduler, refresh, collection, daily, automated',
 'Scheduled data refresh for intelligence sources');
```

**Gate**:
- [ ] Quickstart doc created
- [ ] Data Analyst agent updated
- [ ] 2 tools registered in capabilities.db
- [ ] All tests still pass

---

## Test Summary

| Phase | Tests | Model | Rationale |
|-------|-------|-------|-----------|
| P0 | 0 (check only) | Haiku | Mechanical file search |
| P1 | 8 | Sonnet | Architecture design, abstract class |
| P2 | 18 | Sonnet | Complex PostgreSQL integration |
| P3 | 10 | Sonnet | SQL accuracy critical |
| P4 | 10 | Sonnet | Scheduler logic complexity |
| P5 | 4 | Sonnet | Refactor existing working code |
| P6 | 8 | Sonnet | Integration test complexity |
| P6.5 | 0 (docs) | Sonnet | Documentation quality for agents |
| **Total** | **58** | | |

---

## Model Selection Rationale

| Model | Use Cases | Why |
|-------|-----------|-----|
| **Sonnet** | All code phases (P1-P6) | Code quality, SQL accuracy, error handling critical |
| **Haiku** | P0 anti-duplication only | Simple file search, no judgment needed |

**No Haiku for code** because:
1. PostgreSQL connection handling requires careful error handling
2. SQL column name normalization must be accurate
3. Scheduler logic needs proper cron-style parsing
4. Integration tests require careful assertion design

---

## Extensibility: Adding New Sources

After this sprint, adding Azure Intelligence Service would be:

```python
# claude/tools/collection/azure_intelligence_service.py
from claude.tools.collection.base_intelligence_service import BaseIntelligenceService

class AzureIntelligenceService(BaseIntelligenceService):
    """Azure cost and resource intelligence."""

    def get_data_freshness_report(self):
        # Query azure cost_optimization.db
        pass

    def query_raw(self, sql, params=()):
        # Execute against SQLite
        pass

    def refresh(self):
        # Call azure collection tools
        pass

    # Domain-specific methods
    def get_costs_by_subscription(self, subscription_pattern):
        pass

    def get_resource_inventory(self):
        pass
```

**Time to add**: ~2-3 hours (copy pattern, adjust for Azure schema)

---

## Dependencies

| Dependency | Purpose | Required |
|------------|---------|----------|
| psycopg2-binary | PostgreSQL connection | Yes |
| pyyaml | Schedule config parsing | Yes |
| pytest | Test execution | Yes (dev) |

---

## Success Criteria

1. **58/58 tests pass**
2. **OTCIntelligenceService works with real PostgreSQL**
3. **Collection scheduler runs daily refreshes**
4. **PMPIntelligenceService inherits base class (backward compatible)**
5. **Adding new sources follows documented pattern**
6. **Maia can answer "how many open tickets does Cloud - Infrastructure have?" in 1 tool call**

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| PostgreSQL unavailable | Integration tests skip gracefully |
| PMP refactor breaks existing tests | Run all 34 PMP tests before/after |
| Schedule config syntax errors | Validate YAML on load, use defaults |
| Column mapping errors | Comprehensive test coverage |

---

## Approval Request

**Ready for implementation?**

- [ ] Approve plan as-is
- [ ] Request modifications
- [ ] Defer to future sprint

---

## Estimated Effort

| Phase | Effort |
|-------|--------|
| P0 | 5 min |
| P1 | 30 min |
| P2 | 1.5 hr |
| P3 | 45 min |
| P4 | 1 hr |
| P5 | 30 min |
| P6 | 45 min |
| P6.5 | 30 min |
| **Total** | **~5-6 hours** |
