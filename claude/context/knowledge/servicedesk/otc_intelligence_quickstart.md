# OTC Intelligence Service - Quick Start Guide

**Sprint**: SPRINT-UFC-001 (Unified Intelligence Framework)
**Phase**: 265
**Created**: 2026-01-15

## Overview

The OTC Intelligence Service provides a unified query interface for OTC ServiceDesk PostgreSQL data with automatic data freshness monitoring, column name normalization, and pre-built query templates.

**Tool**: `claude/tools/collection/otc_intelligence_service.py`

---

## Quick Start

### Basic Usage

```python
from claude.tools.collection.otc_intelligence_service import OTCIntelligenceService

# Initialize service (connects to PostgreSQL)
service = OTCIntelligenceService()

# Always check freshness first
freshness = service.get_data_freshness_report()
for source, info in freshness.items():
    print(f"{source}: {info.days_old} days old, {info.record_count} records")
    if info.is_stale:
        print(f"  WARNING: {info.warning}")

# Query team tickets
result = service.get_tickets_by_team("Cloud - Infrastructure")
print(f"Found {len(result.data)} tickets in {result.query_time_ms}ms")

# Check for staleness warnings
if result.is_stale:
    print(f"WARNING: {result.staleness_warning}")
```

---

## Common Query Patterns

### 1. Team Workload Analysis

```python
# Get all tickets for a team
result = service.get_tickets_by_team("Cloud - Infrastructure")

# Get team backlog (unassigned tickets)
backlog = service.get_team_backlog("Cloud - Security")

# Get team health summary (status breakdown)
health = service.get_team_health_summary("Cloud - L3 Escalation")
for row in health.data:
    print(f"{row['status']}: {row['count']} tickets")
```

### 2. User Activity Tracking

```python
# Get user's open tickets
workload = service.get_user_workload("Dion Jewell")
print(f"{len(workload.data)} open tickets")

# Get 30-day activity summary
activity = service.get_user_activity("Trevor Harte")
for row in activity.data:
    print(f"Tickets: {row['tickets_updated']}, Comments: {row['comments_added']}, Hours: {row['hours_logged']}")
```

### 3. Ticket Status Queries

```python
# Get all open tickets (excludes Closed and Incident Resolved)
open_tickets = service.get_open_tickets()

# Get unassigned tickets (PendingAssignment status)
unassigned = service.get_unassigned_tickets()
```

### 4. Raw SQL Queries

```python
# Execute custom SQL
sql = """
    SELECT "TKT-Team", COUNT(*) as count
    FROM servicedesk.tickets
    WHERE "TKT-Status" NOT IN ('Closed', 'Incident Resolved')
    GROUP BY "TKT-Team"
    ORDER BY count DESC
"""
result = service.query_raw(sql)

# With parameters (use %s for placeholders)
sql = """
    SELECT * FROM servicedesk.tickets
    WHERE "TKT-Team" = %s AND "TKT-Severity" = %s
"""
result = service.query_raw(sql, ("Cloud - Infrastructure", "High"))
```

---

## Normalized Field Names

The service automatically normalizes OTC column names for easier use:

| Original Column Name | Normalized Name | Example Value |
|---------------------|-----------------|---------------|
| `TKT-Ticket ID` | `ticket_id` | `INC123456` |
| `TKT-Title` | `title` | `VM Migration Request` |
| `TKT-Team` | `team` | `Cloud - Infrastructure` |
| `TKT-Status` | `status` | `Open`, `Closed` |
| `TKT-Assigned To User` | `assignee` | `Dion Jewell` |
| `TKT-Created Time` | `created_time` | `2026-01-15 10:30:00` |
| `TKT-Category` | `category` | `Service Request` |
| `TKT-Severity` | `priority` | `High`, `Medium`, `Low` |
| `TKT-Account Name` | `account` | `GS1 Australia` |

**Usage**:
```python
result = service.get_tickets_by_team("Cloud - Infrastructure")
for ticket in result.data:
    print(f"{ticket['ticket_id']}: {ticket['title']} ({ticket['status']})")
    # No need to remember TKT-Ticket ID, TKT-Title, TKT-Status
```

---

## Data Freshness Checking

### Why Freshness Matters

OTC data is refreshed periodically (not real-time). Always check freshness before making decisions:

```python
# Get freshness report
freshness = service.get_data_freshness_report()

# Check specific source
tickets_info = freshness.get("tickets")
if tickets_info:
    print(f"Tickets last refreshed: {tickets_info.last_refresh}")
    print(f"Age: {tickets_info.days_old} days")
    print(f"Total records: {tickets_info.record_count}")

    if tickets_info.is_stale:
        print(f"⚠️  WARNING: {tickets_info.warning}")
```

### FreshnessInfo Object

```python
@dataclass
class FreshnessInfo:
    last_refresh: datetime      # Last data refresh timestamp
    days_old: int               # Age in days
    is_stale: bool              # True if > STALENESS_THRESHOLD_DAYS (7)
    record_count: int           # Total records in source
    warning: Optional[str]      # Warning message if stale
```

### Automatic Staleness Warnings

All query results include staleness information:

```python
result = service.get_tickets_by_team("Cloud - Infrastructure")

if result.is_stale:
    # Automatically set if data > 7 days old
    print(f"⚠️  Data may be outdated: {result.staleness_warning}")
```

---

## Query Templates

Pre-built SQL templates for common queries:

```python
from claude.tools.collection.otc_query_templates import execute_template, describe_templates

# List all available templates
print(describe_templates())

# Execute a template
result = execute_template(
    "team_workload",
    {"team_name": "Cloud - Infrastructure"},
    service
)

# Common templates:
# - team_workload: Open/closed/unassigned counts by team
# - team_backlog: Unassigned tickets per team
# - engineering_summary: All 3 engineering queues summary
# - user_workload: User's open tickets with age
# - user_activity: 30-day activity summary
# - ticket_age_distribution: Tickets by age bucket
```

**Reference**: `claude/tools/collection/otc_query_templates.py`

---

## Data Refresh

### Manual Refresh

```python
# Trigger data refresh (calls existing ETL pipeline)
success = service.refresh()

if success:
    print("Data refresh completed successfully")
else:
    print("Data refresh failed")
```

### Automated Refresh

Use the collection scheduler for automated daily refreshes:

```python
from claude.tools.collection.scheduler import CollectionScheduler

scheduler = CollectionScheduler()
scheduler.schedule_daily_refresh("otc", hour=6, minute=0)  # 6:00 AM daily
```

**Reference**: `claude/tools/collection/scheduler.py`

---

## Error Handling

### Connection Failures

```python
# Service gracefully degrades if PostgreSQL unavailable
service = OTCIntelligenceService()

result = service.get_tickets_by_team("Cloud - Infrastructure")

if result.is_stale:
    # Check for connection errors
    if "unavailable" in result.staleness_warning.lower():
        print("PostgreSQL connection failed - check Docker container")
```

### Query Failures

```python
# Query errors return empty results with warnings
result = service.query_raw("INVALID SQL")

if result.is_stale:
    print(f"Query failed: {result.staleness_warning}")
```

---

## QueryResult Object

All query methods return a `QueryResult` dataclass:

```python
@dataclass
class QueryResult:
    data: List[Dict[str, Any]]          # Query results (list of dictionaries)
    source: str                          # Data source identifier
    extraction_timestamp: datetime       # When query was executed
    query_time_ms: int                   # Query execution time (milliseconds)
    is_stale: bool                       # True if data is stale
    staleness_warning: Optional[str]     # Warning message if stale
```

**Usage**:
```python
result = service.get_tickets_by_team("Cloud - Infrastructure")

print(f"Retrieved {len(result.data)} records from {result.source}")
print(f"Query completed in {result.query_time_ms}ms")
print(f"Extracted at: {result.extraction_timestamp}")

if result.is_stale:
    print(f"⚠️  {result.staleness_warning}")

for row in result.data:
    # Process normalized field names
    print(f"{row['ticket_id']}: {row['title']}")
```

---

## Database Schema Reference

### Connection Configuration

```python
DEFAULT_DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "servicedesk",
    "user": "servicedesk_user",
    "password": "ServiceDesk2025!SecurePass",
}

# Custom configuration
custom_config = {
    "host": "remote-db.example.com",
    "port": 5432,
    "database": "servicedesk",
    "user": "analyst",
    "password": "SecurePassword123",
}
service = OTCIntelligenceService(db_config=custom_config)
```

### Core Tables

- **servicedesk.tickets** (~188K records): Main ticket data
- **servicedesk.comments** (~318K records): Ticket comments
- **servicedesk.timesheets** (~850K records): Time tracking
- **servicedesk.user_lookup** (~350 records): Username → Full name mapping

### Freshness View

```sql
-- Check data freshness directly
SELECT * FROM servicedesk.v_data_freshness;
```

**Reference**: `claude/context/knowledge/servicedesk/otc_database_reference.md`

---

## Best Practices

### 1. Always Check Freshness First

```python
# ✅ CORRECT
freshness = service.get_data_freshness_report()
if freshness["tickets"].is_stale:
    print("⚠️  Data may be outdated - consider refreshing")

result = service.get_tickets_by_team("Cloud - Infrastructure")
```

### 2. Use Normalized Field Names

```python
# ✅ CORRECT - Use normalized names in code
for ticket in result.data:
    print(f"{ticket['ticket_id']}: {ticket['assignee']}")

# ❌ INCORRECT - Don't rely on raw column names
for ticket in result.data:
    print(f"{ticket['TKT-Ticket ID']}: {ticket['TKT-Assigned To User']}")
```

### 3. Handle Staleness Warnings

```python
# ✅ CORRECT - Check staleness before making decisions
result = service.get_tickets_by_team("Cloud - Infrastructure")
if result.is_stale:
    print(f"⚠️  WARNING: {result.staleness_warning}")
    # Optionally trigger refresh
    service.refresh()
```

### 4. Use Templates for Common Queries

```python
# ✅ CORRECT - Use pre-built templates
result = execute_template("team_workload", {"team_name": "Cloud - Infrastructure"}, service)

# ❌ INCORRECT - Write custom SQL for common patterns
sql = "SELECT status, COUNT(*) FROM tickets WHERE team = %s GROUP BY status"
result = service.query_raw(sql, ("Cloud - Infrastructure",))
```

---

## Integration Examples

### With Data Analyst Agent

```python
# Typical workflow for ServiceDesk analysis
service = OTCIntelligenceService()

# 1. Check freshness
freshness = service.get_data_freshness_report()

# 2. Get team health
health = service.get_team_health_summary("Cloud - Infrastructure")

# 3. Analyze backlog
backlog = service.get_team_backlog("Cloud - Infrastructure")

# 4. User workload distribution
for user in ["Dion Jewell", "Trevor Harte", "Llewellyn Booth"]:
    workload = service.get_user_workload(user)
    print(f"{user}: {len(workload.data)} open tickets")
```

### With UI Systems Agent

```python
# Prepare data for dashboard visualization
service = OTCIntelligenceService()

# Get all engineering team metrics
teams = ["Cloud - Infrastructure", "Cloud - Security", "Cloud - L3 Escalation"]
metrics = []

for team in teams:
    health = service.get_team_health_summary(team)
    backlog = service.get_team_backlog(team)

    metrics.append({
        "team": team,
        "health": health.data,
        "backlog_count": len(backlog.data),
    })

# Pass metrics to UI Systems Agent for dashboard creation
```

---

## Troubleshooting

### Connection Refused

```bash
# Check if PostgreSQL container is running
docker ps --filter "name=servicedesk-postgres"

# Start container if not running
docker start servicedesk-postgres

# Check logs
docker logs servicedesk-postgres
```

### Import Errors

```python
# psycopg2 not installed
pip install psycopg2-binary

# Or use conda
conda install psycopg2
```

### Data Not Found

```python
# Check if data has been loaded
freshness = service.get_data_freshness_report()

if not freshness:
    # No data loaded - run initial ETL
    service.refresh()
```

---

## See Also

- **OTC Database Reference**: `claude/context/knowledge/servicedesk/otc_database_reference.md`
- **Query Templates**: `claude/tools/collection/otc_query_templates.py`
- **Base Intelligence Service**: `claude/tools/collection/base_intelligence_service.py`
- **Collection Scheduler**: `claude/tools/collection/scheduler.py`
- **Data Analyst Agent**: `claude/agents/data_analyst_agent.md`

---

## Production Status

✅ **READY** - v1.0 (Phase 265, SPRINT-UFC-001)
