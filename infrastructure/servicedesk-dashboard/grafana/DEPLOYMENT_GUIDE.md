# ServiceDesk Tier Tracker Dashboard - Deployment Guide

**Project**: TIER-TRACKER-001
**Phase**: 4 - Grafana Dashboard
**Date**: 2025-10-27
**Version**: 1.0.0

---

## Overview

This guide provides step-by-step instructions for deploying the ServiceDesk Tier Optimization Dashboard to Grafana.

### Dashboard Features
- **11 Panels**: 4 KPI panels, 2 trend panels, 2 monthly breakdown panels, 3 category/pod panels
- **Real-time Data**: Auto-refreshes every 5 minutes
- **Performance**: All queries execute in <6ms (well under 100ms SLO)
- **Cost Tracking**: Dynamic cost calculations from tier_cost_config table

---

## Prerequisites

### Required
- [x] Grafana instance running (v10.0+ recommended)
- [x] PostgreSQL datasource configured in Grafana
- [x] Database: servicedesk-postgres with 10,939 categorized tickets
- [x] Tables: `servicedesk.tickets`, `servicedesk.tier_cost_config`

### Datasource Configuration
**Name**: `PostgreSQL`
**Type**: `postgres`
**Host**: `servicedesk-postgres:5432` (or localhost if port-forwarded)
**Database**: `servicedesk`
**User**: `servicedesk_user`
**SSL Mode**: `disable` (internal network)

---

## Deployment Methods

### Method 1: Grafana UI Import (Recommended for Testing)

1. **Login to Grafana**
   ```
   http://localhost:3000 (or your Grafana URL)
   ```

2. **Navigate to Dashboards**
   - Click "Dashboards" in left sidebar
   - Click "New" → "Import"

3. **Upload Dashboard JSON**
   - Click "Upload JSON file"
   - Select: `infrastructure/servicedesk-dashboard/grafana/servicedesk-tier-tracker.json`
   - OR: Paste JSON content directly

4. **Configure Import**
   - **Name**: ServiceDesk Tier Optimization Dashboard
   - **Folder**: ServiceDesk (create if doesn't exist)
   - **UID**: servicedesk-tier-tracker (unique identifier)
   - **Datasource**: Select "PostgreSQL" datasource

5. **Import**
   - Click "Import"
   - Dashboard should load with 11 panels showing live data

---

### Method 2: Grafana API (Recommended for Production)

```bash
# Set Grafana credentials
GRAFANA_URL="http://localhost:3000"
GRAFANA_API_KEY="your-api-key-here"  # Create in Grafana UI: Configuration → API Keys

# Deploy dashboard
curl -X POST \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  -H "Content-Type: application/json" \
  -d @infrastructure/servicedesk-dashboard/grafana/servicedesk-tier-tracker.json \
  ${GRAFANA_URL}/api/dashboards/db
```

**Expected Response**:
```json
{
  "id": 1,
  "slug": "servicedesk-tier-optimization-dashboard",
  "status": "success",
  "uid": "servicedesk-tier-tracker",
  "url": "/d/servicedesk-tier-tracker/servicedesk-tier-optimization-dashboard",
  "version": 1
}
```

---

### Method 3: Terraform/Infrastructure as Code

If using Terraform with Grafana provider:

```hcl
resource "grafana_dashboard" "servicedesk_tier_tracker" {
  config_json = file("${path.module}/grafana/servicedesk-tier-tracker.json")
  folder      = grafana_folder.servicedesk.id
  overwrite   = true
}
```

---

## Post-Deployment Verification

### 1. Visual Inspection

**Check Each Panel**:
- [ ] Panel 1: L1 Percentage shows ~30.7% (current baseline)
- [ ] Panel 2: L2 Percentage shows ~67.2%
- [ ] Panel 3: L3 Percentage shows ~2.1%
- [ ] Panel 4: Cost Savings shows ~$340K/year
- [ ] Panel 5: Stacked area chart shows 12 months of data
- [ ] Panel 6: Gauges show current vs target progress
- [ ] Panel 7: Bar chart shows last 6 months grouped by tier
- [ ] Panel 8: MoM delta table shows percentage changes
- [ ] Panel 9: L1 pie chart shows top categories (Support Tickets 67.4%)
- [ ] Panel 10: L2 pie chart shows top categories
- [ ] Panel 11: Pod bar chart (currently shows "Unassigned" only - pods forming)

### 2. Query Performance Test

Run in Grafana Query Inspector (click panel → Inspect → Query):

```sql
-- Should execute in <10ms
SELECT
  ROUND(
    COUNT(*) FILTER (WHERE support_tier = 'L1')::NUMERIC /
    COUNT(*)::NUMERIC * 100, 1
  ) as value
FROM servicedesk.tickets
WHERE DATE_TRUNC('month', "TKT-Created Time"::timestamp) = DATE_TRUNC('month', CURRENT_DATE);
```

**Expected**:
- Execution time: <10ms ✅
- Value: ~30.7% ✅

### 3. Dashboard Load Time

- [ ] Dashboard loads in <2 seconds (NFR-1.2)
- [ ] All 11 panels render without errors
- [ ] No "Panel Error" or "Query Error" messages

### 4. Data Validation

**Run in PostgreSQL** to cross-check dashboard values:

```sql
-- Verify current month distribution
SELECT
  COUNT(*) as total,
  COUNT(*) FILTER (WHERE support_tier = 'L1') as l1_count,
  ROUND(COUNT(*) FILTER (WHERE support_tier = 'L1')::NUMERIC / COUNT(*)::NUMERIC * 100, 1) as l1_pct,
  COUNT(*) FILTER (WHERE support_tier = 'L2') as l2_count,
  ROUND(COUNT(*) FILTER (WHERE support_tier = 'L2')::NUMERIC / COUNT(*)::NUMERIC * 100, 1) as l2_pct,
  COUNT(*) FILTER (WHERE support_tier = 'L3') as l3_count,
  ROUND(COUNT(*) FILTER (WHERE support_tier = 'L3')::NUMERIC / COUNT(*)::NUMERIC * 100, 1) as l3_pct
FROM servicedesk.tickets
WHERE DATE_TRUNC('month', "TKT-Created Time"::timestamp) = DATE_TRUNC('month', CURRENT_DATE);
```

**Expected (as of 2025-10-27)**:
```
total: 1188
l1_count: 365  (30.7%)
l2_count: 799  (67.2%)
l3_count: 24   (2.1%)
```

Dashboard panels 1-3 should match these values ✅

---

## Troubleshooting

### Issue: "Panel Error: Query error"

**Cause**: PostgreSQL datasource not configured or connection failed

**Fix**:
1. Go to Configuration → Data Sources → PostgreSQL
2. Test connection: Should show "Data source is working"
3. Check host, database, credentials

---

### Issue: Panels show "No data"

**Cause**: Time range doesn't include current month data

**Fix**:
1. Check time picker (top right): Should be "Last 6 months" or include current month
2. Verify data exists: `SELECT COUNT(*) FROM servicedesk.tickets WHERE "TKT-Created Time"::timestamp >= CURRENT_DATE - INTERVAL '6 months';`

---

### Issue: Panel 11 (Pod chart) is empty

**Expected Behavior**: Pods are currently being formed, so all tickets show "Unassigned"

**Future Fix**: As pods are assigned, update tickets:
```sql
UPDATE servicedesk.tickets
SET assigned_pod = 'Cloud Pod'
WHERE "TKT-Ticket ID" IN (SELECT ... FROM pod_assignment_logic);
```

---

### Issue: Cost Savings calculation shows $0

**Cause**: tier_cost_config table missing or empty

**Fix**:
```sql
-- Verify config exists
SELECT * FROM servicedesk.tier_cost_config;

-- Should return:
-- tier | cost_per_ticket | target_percentage | effective_date
-- L1   | 100.00          | 65.0             | 2025-10-27
-- L2   | 200.00          | 30.0             | 2025-10-27
-- L3   | 300.00          | 7.5              | 2025-10-27
```

---

## Configuration Changes

### Update Cost Model

To change tier costs (e.g., L1 from $100 to $120):

```sql
-- Update cost
UPDATE servicedesk.tier_cost_config
SET
  cost_per_ticket = 120.00,
  effective_date = CURRENT_DATE
WHERE tier = 'L1';

-- Dashboard auto-updates on next refresh (no code changes needed)
```

### Update Target Percentages

To change targets (e.g., L1 from 65% to 70%):

```sql
UPDATE servicedesk.tier_cost_config
SET
  target_percentage = 70.0,
  effective_date = CURRENT_DATE
WHERE tier = 'L1';
```

---

## Monitoring & Maintenance

### Auto-Refresh

Dashboard refreshes every **5 minutes** automatically.

To change: Click ⚙️ → Settings → Time Options → Auto Refresh → Select interval

### Annotations

Dashboard includes annotation layer showing tier target changes:
- Queries: `tier_cost_config.effective_date`
- Displays: Vertical line on time-series charts when targets updated

### Alerts (Phase 5)

Alerting will be configured in Phase 5:
- Alert 1: L1 rate <50% for 7 consecutive days
- Alert 2: L2 rate >50% for 7 consecutive days

Dashboard notifications only (no email/Slack yet).

---

## Access Control

### Recommended Permissions

**Viewer Role**:
- ServiceDesk team members (read-only access)
- Stakeholders (view metrics, no edit)

**Editor Role**:
- ServiceDesk managers (can modify dashboard)
- SRE team (can adjust thresholds, queries)

**Admin Role**:
- Platform team (full access, including deletion)

### Setup

```bash
# Create ServiceDesk team in Grafana
# Add users to team
# Assign dashboard to team with appropriate permissions
```

---

## Backup & Version Control

### Git Repository

Dashboard JSON stored in:
```
infrastructure/servicedesk-dashboard/grafana/servicedesk-tier-tracker.json
```

**Versioning**:
- Major version (1.0.0): Breaking changes to queries or schema
- Minor version (1.1.0): New panels or features
- Patch version (1.0.1): Bug fixes, visual tweaks

### Export Current Dashboard

To backup current state from Grafana:

```bash
curl -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  ${GRAFANA_URL}/api/dashboards/uid/servicedesk-tier-tracker \
  | jq '.dashboard' > servicedesk-tier-tracker-backup-$(date +%Y%m%d).json
```

---

## Performance Metrics

### Query Execution Times (Measured 2025-10-27)

| Panel | Query Type | Execution Time | SLO Status |
|-------|------------|----------------|------------|
| 1 | L1 Percentage | 2.7ms | ✅ Pass (<100ms) |
| 2 | L2 Percentage | 2.5ms | ✅ Pass |
| 3 | L3 Percentage | 2.4ms | ✅ Pass |
| 4 | Cost Savings | 3.1ms | ✅ Pass |
| 5 | Tier Trends | 5.2ms | ✅ Pass |
| 6 | Gauges | 2.8ms | ✅ Pass |
| 7 | Monthly Bars | 4.7ms | ✅ Pass |
| 8 | MoM Delta | 4.2ms | ✅ Pass |
| 9 | L1 by Category | 2.9ms | ✅ Pass |
| 10 | L2 by Category | 3.0ms | ✅ Pass |
| 11 | L1 by Pod | 2.6ms | ✅ Pass |

**Dashboard Load Time**: <2 seconds ✅ (NFR-1.2)

### Database Indexes Supporting Performance

```sql
-- Created in Phase 3
CREATE INDEX idx_tickets_support_tier ON servicedesk.tickets(support_tier);
CREATE INDEX idx_tickets_created_time ON servicedesk.tickets("TKT-Created Time");
CREATE INDEX idx_tickets_category ON servicedesk.tickets("TKT-Category");
CREATE INDEX idx_tickets_assigned_pod ON servicedesk.tickets(assigned_pod);
CREATE INDEX idx_tickets_tier_created ON servicedesk.tickets(support_tier, "TKT-Created Time");
```

---

## Next Steps

### Phase 5: Alerting (15 minutes)
- Configure 2 dashboard alerts (L1 <50%, L2 >50%)
- Test alert state changes

### Phase 6: Automation (1 hour)
- Weekly tier snapshot capture
- Daily data validation
- Runbook for operations

### Phase 7: Documentation (1 hour)
- Update ARCHITECTURE.md
- Create ADR-003
- Update active_deployments.md

---

## Support

**Questions?** Contact SRE team or see:
- Project Plan: `claude/data/SERVICEDESK_TIER_TRACKER_PROJECT_PLAN.md`
- Requirements: `claude/data/tier_tracker_requirements.md`
- Architecture: `infrastructure/servicedesk-dashboard/ARCHITECTURE.md`

---

**Deployment Status**: ✅ Ready for Production
**Last Updated**: 2025-10-27
**Next Review**: After Phase 5 (Alerting)
