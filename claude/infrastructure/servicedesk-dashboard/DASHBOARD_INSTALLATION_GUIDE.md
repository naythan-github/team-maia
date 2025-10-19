# ServiceDesk Analytics Dashboards - Installation & Customization Guide

**Created**: 2025-10-19
**Author**: SRE Principal Engineer Agent
**Version**: 1.0.0

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Dashboard Overview](#dashboard-overview)
3. [Installation Instructions](#installation-instructions)
4. [Configuration](#configuration)
5. [Customization Guide](#customization-guide)
6. [Troubleshooting](#troubleshooting)
7. [Maintenance](#maintenance)

---

## Quick Start

### Prerequisites Check

**System Requirements**:
- Docker and Docker Compose installed
- PostgreSQL 15+ with ServiceDesk data loaded
- Grafana 10.2.2+ (included in docker-compose.yml)
- Network access to localhost:3000 (Grafana) and localhost:5432 (PostgreSQL)

**Verify Infrastructure**:
```bash
# Check if containers are running
docker ps | grep servicedesk

# Should see:
# servicedesk-grafana (port 3000)
# servicedesk-postgres (port 5432)
```

### 5-Minute Installation

```bash
# 1. Navigate to dashboard directory
cd /Users/naythandawe/git/maia/claude/infrastructure/servicedesk-dashboard

# 2. Verify Grafana is running
curl http://localhost:3000/api/health
# Expected: {"database":"ok","version":"10.2.2"}

# 3. Import all 5 dashboards using Grafana API
./scripts/import_dashboards.sh

# OR import manually via Grafana UI (see Manual Import below)

# 4. Access dashboards
open http://localhost:3000
# Login: admin / <check .env for password>
```

**Expected Result**: All 5 dashboards imported and accessible in Grafana UI.

---

## Dashboard Overview

### Dashboard 1: Automation Executive Overview
**UID**: `servicedesk-automation-exec`
**Purpose**: Single-pane-of-glass view of automation opportunities and ROI
**Panels**: 9 panels (6 KPI stats, 2 time-series, 1 bar chart)
**Refresh**: 5 minutes
**Best For**: Executive reporting, automation planning

**Key Metrics**:
- Total tickets analyzed: 10,939
- Automation opportunities: 4,842 tickets (82.2% coverage)
- Annual savings potential: ~$952K
- Quick wins: Motion/Sensor alerts (960 tickets)

### Dashboard 2: Alert Analysis Deep-Dive
**UID**: `servicedesk-alert-analysis`
**Purpose**: Deep analysis of alert patterns for automation prioritization
**Panels**: 9 panels (5 time-series, 1 heatmap, 1 table, 1 pie chart, 1 stat)
**Refresh**: 5 minutes
**Best For**: Alert pattern analysis, automation scoping

**Alert Patterns**:
- Motion/Sensor: 960 tickets
- Azure Resource Health: 678 tickets
- Patch Deployment: 555 tickets
- Network/VPN: 490 tickets
- SSL/Certificate: 248 tickets

### Dashboard 3: Support Ticket Pattern Analysis
**UID**: `servicedesk-support-patterns`
**Purpose**: Support ticket automation opportunities with recommendations
**Panels**: 8 panels (5 time-series, 1 pie chart, 1 trend, 1 table)
**Refresh**: 5 minutes
**Best For**: Support automation planning, self-service portal scoping

**Support Patterns**:
- Access/Permissions: 908 tickets
- Email Issues: 526 tickets
- Password Reset: 196 tickets
- Software Installation: 125 tickets
- License Management: 94 tickets

### Dashboard 4: Team Performance & Task-Level Analysis
**UID**: `servicedesk-team-performance`
**Purpose**: Workload distribution and team performance metrics
**Panels**: 8 panels (2 bar charts, 1 pie chart, 3 time-series, 1 heatmap, 1 table)
**Refresh**: 5 minutes
**Best For**: Team management, capacity planning, workload balancing

**Key Metrics**:
- Top 15 assignees by ticket volume
- Task-level distribution (Comms: 41.4%, Admin: 25%, Technical: 31.9%, Expert: 1.8%)
- Average resolution time trends
- PendingAssignment backlog: 3,131 tickets (28.6%)

### Dashboard 5: Improvement Tracking & ROI Calculator
**UID**: `servicedesk-improvement-tracking`
**Purpose**: Baseline metrics and future automation impact tracking
**Panels**: 13 panels (8 stats, 2 time-series, 1 table, 1 bar gauge, 1 text)
**Refresh**: 5 minutes
**Best For**: ROI tracking, before/after comparisons, progress reporting

**Current Status**: Baseline phase (pre-automation)
**Future Use**: Will populate with actual savings post-automation implementation

---

## Installation Instructions

### Method 1: Automated Import (Recommended)

**Create import script**:
```bash
# Create script file
cat > /Users/naythandawe/git/maia/claude/infrastructure/servicedesk-dashboard/scripts/import_dashboards.sh << 'EOF'
#!/bin/bash

# ServiceDesk Dashboard Import Script
# Imports all 5 dashboards into Grafana

GRAFANA_URL="http://localhost:3000"
GRAFANA_USER="admin"
GRAFANA_PASSWORD="${GRAFANA_ADMIN_PASSWORD:-admin}"  # From .env or default

DASHBOARD_DIR="/Users/naythandawe/git/maia/claude/infrastructure/servicedesk-dashboard/grafana/dashboards"

echo "Starting dashboard import..."

for dashboard in "$DASHBOARD_DIR"/*.json; do
  dashboard_name=$(basename "$dashboard")
  echo "Importing $dashboard_name..."

  curl -X POST \
    -H "Content-Type: application/json" \
    -u "$GRAFANA_USER:$GRAFANA_PASSWORD" \
    -d @"$dashboard" \
    "$GRAFANA_URL/api/dashboards/db"

  echo ""
done

echo "Import complete! Access dashboards at $GRAFANA_URL"
EOF

# Make executable
chmod +x /Users/naythandawe/git/maia/claude/infrastructure/servicedesk-dashboard/scripts/import_dashboards.sh

# Run import
./scripts/import_dashboards.sh
```

**Expected Output**:
```
Starting dashboard import...
Importing 1_automation_executive_overview.json...
{"id":1,"uid":"servicedesk-automation-exec","url":"/d/servicedesk-automation-exec"}
Importing 2_alert_analysis_deepdive.json...
{"id":2,"uid":"servicedesk-alert-analysis","url":"/d/servicedesk-alert-analysis"}
...
Import complete! Access dashboards at http://localhost:3000
```

### Method 2: Manual Import via Grafana UI

**Steps**:

1. **Access Grafana**:
   - Open http://localhost:3000 in browser
   - Login: `admin` / `<password from .env>`

2. **Navigate to Dashboards**:
   - Click "Dashboards" in left sidebar
   - Click "New" → "Import"

3. **Import Each Dashboard**:
   - Click "Upload JSON file"
   - Select dashboard file:
     - `1_automation_executive_overview.json`
     - `2_alert_analysis_deepdive.json`
     - `3_support_pattern_analysis.json`
     - `4_team_performance_tasklevel.json`
     - `5_improvement_tracking_roi.json`
   - Click "Load"
   - Select data source: "ServiceDesk PostgreSQL"
   - Click "Import"

4. **Verify**:
   - Each dashboard should load with data
   - Check for errors in panels (red exclamation marks)

### Method 3: Docker Volume Mount (Development)

**Mount dashboards directory**:
```yaml
# Add to docker-compose.yml under grafana service
volumes:
  - grafana_data:/var/lib/grafana
  - ./grafana/provisioning:/etc/grafana/provisioning
  - ./grafana/dashboards:/var/lib/grafana/dashboards  # Add this line
```

**Restart Grafana**:
```bash
docker-compose restart grafana
```

**Benefit**: Auto-reload on dashboard file changes (hot reload)

---

## Configuration

### Data Source Configuration

**Verify PostgreSQL data source**:
```bash
# Check data source configuration
cat /Users/naythandawe/git/maia/claude/infrastructure/servicedesk-dashboard/grafana/provisioning/datasources/postgres.yml
```

**Expected content**:
```yaml
apiVersion: 1

datasources:
  - name: ServiceDesk PostgreSQL
    type: postgres
    access: proxy
    url: servicedesk-postgres:5432
    database: servicedesk
    user: servicedesk_user
    secureJsonData:
      password: 'ServiceDesk2025!SecurePass'
    jsonData:
      sslmode: 'disable'
      maxOpenConns: 10
      maxIdleConns: 5
      connMaxLifetime: 14400
      postgresVersion: 1500
      timescaledb: false
    editable: true
    isDefault: true
```

**Test connection**:
```bash
# From Grafana UI
1. Go to Configuration → Data Sources
2. Click "ServiceDesk PostgreSQL"
3. Scroll to bottom, click "Save & Test"
4. Expected: "Database Connection OK"
```

### Dashboard Variables

**All dashboards use these variables**:

| Variable | Type | Default | Purpose |
|----------|------|---------|---------|
| `datasource` | Data source | ServiceDesk PostgreSQL | Select PostgreSQL data source |

**To add custom variables**:
1. Open dashboard
2. Click gear icon (Dashboard settings)
3. Go to "Variables" tab
4. Click "Add variable"
5. Configure (example: add "Client" filter)

**Example: Add Client Filter**:
```json
{
  "name": "client",
  "label": "Client",
  "type": "query",
  "query": "SELECT DISTINCT \"TKT-Client Name\" FROM servicedesk.tickets ORDER BY 1",
  "datasource": "ServiceDesk PostgreSQL",
  "multi": true,
  "includeAll": true,
  "allValue": ".*"
}
```

**Use in query**:
```sql
SELECT COUNT(*)
FROM servicedesk.tickets
WHERE "TKT-Client Name" IN ($client)
```

### Time Range Configuration

**Default time range**: Jul 1, 2025 - Oct 13, 2025 (baseline period)

**To change time range**:
1. Open dashboard
2. Click time picker (top right)
3. Select:
   - **Absolute**: Custom start/end dates
   - **Relative**: Last 30 days, Last 90 days, etc.
   - **Quick ranges**: Today, This week, This month

**To set default time range** (all dashboards):
```json
// In dashboard JSON, modify:
"time": {
  "from": "now-90d",  // Last 90 days
  "to": "now"
}
```

### Refresh Interval

**Current setting**: 5 minutes auto-refresh

**To change**:
1. Open dashboard
2. Click refresh icon (top right)
3. Select interval: Off, 5m, 15m, 30m, 1h

**To set default** (dashboard JSON):
```json
"refresh": "15m",  // Change to 15 minutes
"timepicker": {
  "refresh_intervals": ["5m", "15m", "30m", "1h", "2h"]
}
```

---

## Customization Guide

### Customizing Queries

#### Example 1: Change Hourly Rate in ROI Calculations

**Current**: $80/hr blended rate
**To Change**: Update to $100/hr

**Find and replace in dashboard JSON**:
```bash
# Search for: * 80 /
# Replace with: * 100 /
```

**Or edit panel query directly**:
1. Open dashboard
2. Click panel title → Edit
3. Find query with ROI calculation
4. Change: `COUNT(*) * 1.0 / 104 * 365 * 2.0 * 80 / 1000`
5. To: `COUNT(*) * 1.0 / 104 * 365 * 2.0 * 100 / 1000`
6. Click "Apply"

#### Example 2: Add New Automation Pattern

**Pattern**: VDI/Desktop tickets

**Step 1**: Add to pattern matching CASE statement
```sql
CASE
  WHEN "TKT-Title" ILIKE '%motion%' OR "TKT-Title" ILIKE '%sensor%' THEN 'Motion/Sensor'
  -- Existing patterns...
  WHEN "TKT-Title" ILIKE '%vdi%' OR "TKT-Title" ILIKE '%desktop%' THEN 'VDI/Desktop'  -- Add this
  ELSE 'Other'
END as pattern_type
```

**Step 2**: Add to automation candidates WHERE clause
```sql
WHERE (
  "TKT-Title" ILIKE '%motion%' OR "TKT-Title" ILIKE '%sensor%' OR
  -- Existing patterns...
  "TKT-Title" ILIKE '%vdi%' OR "TKT-Title" ILIKE '%desktop%'  -- Add this
)
```

**Step 3**: Update all affected panels (use Find/Replace in dashboard JSON)

#### Example 3: Change Average Hours Per Ticket

**Current**: 2.0 hours average (for alerts), 1.5 hours (for support)
**To Change**: Update based on actual data

**Option A: Use actual data from timesheets**:
```sql
SELECT
  AVG(CASE WHEN "TKT-Category" = 'Alert' THEN "TS-Hours" END) as avg_alert_hours,
  AVG(CASE WHEN "TKT-Category" = 'Support Tickets' THEN "TS-Hours" END) as avg_support_hours
FROM servicedesk.tickets t
LEFT JOIN servicedesk.timesheets ts ON t."TKT-Ticket ID" = ts."TS-Crm ID"
WHERE "TKT-Created Time" >= '2025-07-01' AND "TKT-Created Time" <= '2025-10-13';
```

**Option B: Use fixed values in queries**:
Replace `* 2.0 *` with `* 3.5 *` (for 3.5 hour average)

### Adding New Panels

#### Example: Add "Top 5 Clients by Ticket Volume" Panel

**JSON structure**:
```json
{
  "id": 99,  // Unique panel ID
  "type": "barchart",
  "title": "Top 5 Clients by Ticket Volume",
  "description": "Clients with most tickets in analysis period",
  "gridPos": {"h": 8, "w": 12, "x": 0, "y": 50},  // Position on grid
  "targets": [
    {
      "datasource": {"type": "postgres", "uid": "${datasource}"},
      "format": "table",
      "rawSql": "SELECT \"TKT-Client Name\" as \"Client\", COUNT(*) as \"Tickets\" FROM servicedesk.tickets WHERE \"TKT-Created Time\" >= '2025-07-01' AND \"TKT-Created Time\" <= '2025-10-13' GROUP BY 1 ORDER BY 2 DESC LIMIT 5;",
      "refId": "A"
    }
  ],
  "options": {
    "orientation": "horizontal",
    "xField": "Client",
    "showValue": "always"
  }
}
```

**Steps**:
1. Copy existing panel from dashboard JSON
2. Change `id` to unique number
3. Update `gridPos` to position on dashboard
4. Modify `rawSql` query
5. Save dashboard JSON
6. Re-import dashboard

### Customizing Visualizations

#### Change Panel Type

**Example**: Convert time-series to bar chart

1. Edit panel
2. Change "Panel type" dropdown (top right)
3. Select "Bar chart" or "Bar gauge"
4. Adjust options:
   - Orientation: Horizontal/Vertical
   - Display mode: Gradient gauge, LCD gauge, Basic
   - Show values: Always, Auto, Never

#### Change Color Schemes

**Thresholds** (stat panels):
```json
"thresholds": {
  "mode": "absolute",
  "steps": [
    {"value": 0, "color": "red"},      // <1000
    {"value": 1000, "color": "yellow"}, // 1000-5000
    {"value": 5000, "color": "green"}   // >5000
  ]
}
```

**Color mode**:
- `"value"`: Number only
- `"background"`: Colored background
- `"none"`: No color

#### Customize Legends

**Show/Hide**:
```json
"legend": {
  "showLegend": true,          // true/false
  "displayMode": "table",      // list, table, hidden
  "placement": "bottom",       // bottom, right, top
  "calcs": ["mean", "max", "last"]  // Calculations to show
}
```

### Dashboard Organization

#### Create Dashboard Folders

1. Go to Dashboards → Browse
2. Click "New" → "New folder"
3. Name: "ServiceDesk Analytics"
4. Move all 5 dashboards into folder

#### Set Dashboard Home

1. Go to Configuration → Preferences
2. Set "Home Dashboard" to "Automation Executive Overview"
3. Users will see this dashboard on login

#### Share Dashboards

**Generate shareable link**:
1. Open dashboard
2. Click "Share" icon (top right)
3. Select "Link" tab
4. Toggle "Shorten URL"
5. Copy link

**Export dashboard**:
1. Click gear icon → "JSON Model"
2. Copy JSON
3. Share with team

**Create snapshot**:
1. Click "Share" → "Snapshot"
2. Set expiration time
3. Click "Publish to snapshot"
4. Copy snapshot URL (external sharing, no login required)

---

## Troubleshooting

### Issue 1: Dashboard Not Loading / Blank Panels

**Symptoms**: Dashboard loads but panels show "No data" or spinning loader

**Diagnosis**:
```bash
# 1. Check Grafana logs
docker logs servicedesk-grafana

# 2. Check PostgreSQL connection
docker exec servicedesk-postgres psql -U servicedesk_user -d servicedesk -c "SELECT COUNT(*) FROM servicedesk.tickets;"

# 3. Test query directly in Grafana
# Go to Explore → Select data source → Run query
```

**Solutions**:
- **No data source**: Go to Configuration → Data Sources → Add PostgreSQL
- **Query error**: Check panel edit mode for error message
- **Time range**: Adjust dashboard time picker to Jul 1 - Oct 13, 2025
- **Permissions**: Verify servicedesk_user has SELECT on servicedesk.tickets

### Issue 2: Slow Dashboard Performance

**Symptoms**: Dashboard takes >5 seconds to load, panels refresh slowly

**Diagnosis**:
```bash
# 1. Check query execution times
docker exec servicedesk-postgres psql -U servicedesk_user -d servicedesk -c "EXPLAIN ANALYZE SELECT COUNT(*) FROM servicedesk.tickets WHERE \"TKT-Title\" ILIKE '%motion%';"

# 2. Check database statistics
docker exec servicedesk-postgres psql -U servicedesk_user -d servicedesk -c "SELECT * FROM pg_stat_user_tables WHERE schemaname = 'servicedesk';"
```

**Solutions**:
- **Missing indexes**: Run ANALYZE and check index usage (see SQL documentation)
- **Large dataset**: Reduce time range or add filters
- **Slow queries**: Optimize ILIKE pattern matching (see Performance Optimization section)
- **Connection pool**: Increase maxOpenConns in data source config

### Issue 3: Dashboard Import Fails

**Symptoms**: Error when importing dashboard JSON

**Common Errors**:
```json
// Error: "Dashboard UID already exists"
// Solution: Change "uid" in JSON to unique value

// Error: "Invalid JSON"
// Solution: Validate JSON at jsonlint.com

// Error: "Data source not found"
// Solution: Update data source UID in dashboard JSON
```

**Fix data source UID**:
```bash
# 1. Get data source UID
curl -u admin:admin http://localhost:3000/api/datasources

# 2. Find "ServiceDesk PostgreSQL" UID (e.g., "P6BECECF7273D15EE")

# 3. Update dashboard JSON
# Find: "uid": "P6BECECF7273D15EE"
# Replace with your data source UID
```

### Issue 4: Incorrect Data / Wrong Calculations

**Symptoms**: Numbers don't match expected values

**Diagnosis**:
```sql
-- Verify ticket count
SELECT COUNT(*) FROM servicedesk.tickets
WHERE "TKT-Created Time" >= '2025-07-01' AND "TKT-Created Time" <= '2025-10-13';
-- Expected: 10,939

-- Verify alert count
SELECT COUNT(*) FROM servicedesk.tickets
WHERE "TKT-Category" = 'Alert'
AND "TKT-Created Time" >= '2025-07-01' AND "TKT-Created Time" <= '2025-10-13';
-- Expected: 4,036

-- Verify pattern matching
SELECT COUNT(*) FROM servicedesk.tickets
WHERE ("TKT-Title" ILIKE '%motion%' OR "TKT-Title" ILIKE '%sensor%')
AND "TKT-Created Time" >= '2025-07-01' AND "TKT-Created Time" <= '2025-10-13';
-- Expected: 960
```

**Solutions**:
- **Time zone mismatch**: Set Grafana timezone to browser/UTC
- **Date filter**: Verify time range includes full baseline period
- **Case sensitivity**: Use ILIKE (not LIKE) for pattern matching
- **NULL values**: Add NULL checks in WHERE clauses

### Issue 5: Annotations Not Showing

**Symptoms**: Automation implementation dates not visible on dashboards

**Setup Annotations**:
1. Open Dashboard 5 (Improvement Tracking)
2. Click gear icon → "Annotations"
3. Verify "Automation Implementation Dates" is enabled
4. Add annotation manually:
   - Ctrl/Cmd + Click on graph
   - Enter annotation text
   - Save

**Persistent Annotations** (use tags):
```bash
# Create annotation via API
curl -X POST \
  -H "Content-Type: application/json" \
  -u admin:admin \
  -d '{
    "dashboardId": 5,
    "time": 1698364800000,
    "text": "Motion Alert Automation Deployed",
    "tags": ["automation", "motion"]
  }' \
  http://localhost:3000/api/annotations
```

---

## Maintenance

### Weekly Tasks

**1. Verify Dashboard Functionality**:
```bash
# Test dashboard access
curl -u admin:admin http://localhost:3000/api/dashboards/uid/servicedesk-automation-exec | jq .

# Expected: JSON response with dashboard details
```

**2. Check Query Performance**:
```bash
# Run ANALYZE on tickets table
docker exec servicedesk-postgres psql -U servicedesk_user -d servicedesk -c "ANALYZE servicedesk.tickets;"
```

### Monthly Tasks

**1. Update Baseline Metrics** (if new data added):
```bash
# Update time range in dashboards to include new months
# Example: Change from Jul-Oct to Jul-Nov

# Option A: Update dashboard JSON
# Find: "from": "2025-07-01T00:00:00.000Z", "to": "2025-10-13T23:59:59.000Z"
# Replace with: "from": "2025-07-01T00:00:00.000Z", "to": "2025-11-30T23:59:59.000Z"

# Option B: Use relative time range
# Change to: "from": "now-6M", "to": "now"
```

**2. Review and Archive Old Dashboards**:
```bash
# Export dashboard before deletion
curl -u admin:admin http://localhost:3000/api/dashboards/uid/<dashboard-uid> > backup_dashboard_$(date +%Y%m%d).json
```

**3. Backup Grafana Configuration**:
```bash
# Backup Grafana database
docker exec servicedesk-grafana grafana-cli admin reset-admin-password <new-password>

# Backup dashboards directory
tar -czf grafana_dashboards_backup_$(date +%Y%m%d).tar.gz grafana/dashboards/
```

### Quarterly Tasks

**1. Optimize Database Indexes**:
```bash
# Rebuild indexes
docker exec servicedesk-postgres psql -U servicedesk_user -d servicedesk -c "REINDEX TABLE servicedesk.tickets;"

# Vacuum and analyze
docker exec servicedesk-postgres psql -U servicedesk_user -d servicedesk -c "VACUUM ANALYZE servicedesk.tickets;"
```

**2. Review Query Performance** (see SQL documentation):
```sql
-- Check slow queries
SELECT
  query,
  calls,
  mean_exec_time,
  max_exec_time
FROM pg_stat_statements
WHERE query LIKE '%servicedesk.tickets%'
ORDER BY mean_exec_time DESC
LIMIT 10;
```

**3. Dashboard Health Check**:
```bash
# Test all dashboard queries
for dashboard in grafana/dashboards/*.json; do
  echo "Testing $dashboard..."
  # Extract and test queries (manual process)
done
```

### Automation Deployment Updates

**When automation is implemented, update Dashboard 5**:

1. **Add annotation** marking deployment date
2. **Update placeholder panels** with actual data:
   - Change "N/A - Not Yet Implemented" to real queries
   - Add comparison queries (before vs after)
3. **Update ROI calculator**:
   - Change "Actual Savings YTD" from "$0K" to calculated value
   - Add "Status" column update logic

**Example post-automation query**:
```sql
-- After automation: Calculate actual savings
SELECT
  '$' || ROUND(
    (
      (SELECT COUNT(*) FROM servicedesk.tickets WHERE "TKT-Created Time" >= '2025-07-01' AND "TKT-Created Time" <= '2025-10-13' AND "TKT-Title" ILIKE '%motion%')
      -
      (SELECT COUNT(*) FROM servicedesk.tickets WHERE "TKT-Created Time" >= '2025-11-01' AND "TKT-Created Time" <= '2026-01-31' AND "TKT-Title" ILIKE '%motion%')
    ) * 1.0 / 92 * 365 * 0.5 * 80 / 1000, 0
  ) || 'K' as "Actual Motion Alert Savings"
;
```

---

## Advanced Configuration

### Custom Alerting Rules

**Note**: User declined alerting in requirements, but if needed:

```yaml
# grafana/provisioning/alerting/rules.yml
apiVersion: 1
groups:
  - name: servicedesk_alerts
    interval: 5m
    rules:
      - uid: pending_assignment_high
        title: High PendingAssignment Backlog
        condition: A
        data:
          - refId: A
            queryType: ''
            relativeTimeRange:
              from: 600
              to: 0
            datasourceUid: <postgres-uid>
            model:
              rawSql: "SELECT COUNT(*) FROM servicedesk.tickets WHERE \"TKT-Assigned To User\" = 'PendingAssignment'"
        noDataState: NoData
        execErrState: Error
        for: 10m
        annotations:
          description: 'PendingAssignment backlog exceeds 3000 tickets'
        labels:
          severity: warning
```

### Integration with External Tools

**Export to Excel** (via Python script):
```python
import pandas as pd
from sqlalchemy import create_engine

# Connect to PostgreSQL
engine = create_engine('postgresql://servicedesk_user:ServiceDesk2025!SecurePass@localhost:5432/servicedesk')

# Export automation opportunities
query = """
SELECT
  CASE
    WHEN "TKT-Title" ILIKE '%motion%' OR "TKT-Title" ILIKE '%sensor%' THEN 'Motion/Sensor'
    -- Additional patterns...
  END as pattern,
  COUNT(*) as tickets
FROM servicedesk.tickets
WHERE "TKT-Created Time" >= '2025-07-01' AND "TKT-Created Time" <= '2025-10-13'
GROUP BY 1
ORDER BY 2 DESC
"""

df = pd.read_sql(query, engine)
df.to_excel('automation_opportunities.xlsx', index=False)
```

**Slack Integration** (send daily summary):
```bash
#!/bin/bash
# daily_dashboard_summary.sh

# Get KPIs from database
TOTAL_TICKETS=$(docker exec servicedesk-postgres psql -U servicedesk_user -d servicedesk -t -c "SELECT COUNT(*) FROM servicedesk.tickets WHERE \"TKT-Created Time\" >= CURRENT_DATE - INTERVAL '1 day'")

# Send to Slack
curl -X POST -H 'Content-type: application/json' \
  --data "{\"text\":\"Daily ServiceDesk Summary: $TOTAL_TICKETS tickets created yesterday\"}" \
  <SLACK_WEBHOOK_URL>
```

---

## Dashboard Access URLs

Once imported, access dashboards at:

1. **Automation Executive Overview**: http://localhost:3000/d/servicedesk-automation-exec
2. **Alert Analysis Deep-Dive**: http://localhost:3000/d/servicedesk-alert-analysis
3. **Support Pattern Analysis**: http://localhost:3000/d/servicedesk-support-patterns
4. **Team Performance**: http://localhost:3000/d/servicedesk-team-performance
5. **Improvement Tracking**: http://localhost:3000/d/servicedesk-improvement-tracking

---

## Support & Documentation

**Files Included**:
- `DASHBOARD_INSTALLATION_GUIDE.md` (this file)
- `DASHBOARD_SQL_QUERIES_DOCUMENTATION.md` - Complete SQL reference
- `DASHBOARD_MOCKUP_DESCRIPTIONS.md` - Visual descriptions (see next file)
- Dashboard JSON files (5 files in grafana/dashboards/)

**Contact**: SRE Principal Engineer Agent
**Created**: 2025-10-19
**Version**: 1.0.0
