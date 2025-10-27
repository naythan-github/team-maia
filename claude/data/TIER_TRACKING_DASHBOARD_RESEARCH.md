# ServiceDesk Tier Tracking Dashboard - Research & Design

**Date**: 2025-10-27
**Purpose**: Research dashboard options for tracking L1/L2/L3 tier distribution changes over time
**Implementation**: Future (using SRE Agent)

---

## 🎯 **Objective**

Create a Grafana dashboard to track ServiceDesk support tier metrics over time, enabling:
1. **Trend monitoring**: L1/L2/L3 distribution changes month-over-month
2. **Goal tracking**: Progress toward industry benchmarks (60-70% L1, 25-35% L2, 5-10% L3)
3. **ROI measurement**: Cost savings from tier optimization initiatives
4. **Automation impact**: Ticket volume reduction from automation/self-service

---

## ✅ **Existing Infrastructure** (Already Running)

### **Grafana + PostgreSQL Stack**

| Component | Status | Details |
|-----------|--------|---------|
| **Grafana** | ✅ Running | servicedesk-grafana container, port 3000 |
| **PostgreSQL** | ✅ Running | servicedesk-postgres container, port 5432 |
| **Database** | ✅ Populated | servicedesk schema, 7 tables, 266,622 rows |
| **Existing Dashboards** | ✅ 10 dashboards | Executive, Operations, Quality, Team Performance, etc. |

### **Database Schema**

```sql
servicedesk schema (7 tables):
├── tickets (10,939 rows)           -- Main ticket data
├── comments (108,129 rows)          -- Ticket comments
├── timesheets (141,062 rows)        -- Time tracking
├── comment_quality (6,319 rows)     -- LLM quality analysis
├── comment_sentiment (109 rows)     -- Sentiment analysis
├── cloud_team_roster (48 rows)      -- Team data
└── import_metadata (16 rows)        -- ETL tracking
```

**Key Field**: `tickets` table has ALL ticket data including categories and root causes

---

## 📊 **Proposed Dashboard Design**

### **Dashboard Name**: "ServiceDesk Tier Optimization Tracker"

**UID**: `servicedesk-tier-tracker`
**Refresh**: 5 minutes (auto-refresh)
**Time Range**: Last 12 months (configurable)

---

### **Dashboard Layout** (4 rows, 12 panels total)

```
┌─────────────────────────────────────────────────────────────────────┐
│ ROW 1: KPI Summary (Current Month)                      [4 panels]  │
├─────────────┬─────────────┬─────────────┬───────────────────────────┤
│ L1 %        │ L2 %        │ L3 %        │ Cost Savings              │
│ 33.3%       │ 63.1%       │ 3.6%        │ $0 → $296K                │
│ ⚠️ -27%     │ ⚠️ +28%     │ ✅ Optimal  │ (vs optimized)            │
│ vs 60-70%   │ vs 25-35%   │ vs 5-10%    │                           │
└─────────────┴─────────────┴─────────────┴───────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ ROW 2: Tier Distribution Trends                         [2 panels]  │
├────────────────────────────────────┬────────────────────────────────┤
│ Tier Distribution Over Time        │ Target vs Actual               │
│ (Stacked Area Chart)               │ (Gauge Charts)                 │
│                                    │                                │
│ 100%─────────────────              │  L1: [====    ] 33% → 60%     │
│   L3 (3.6%)                        │  L2: [========] 63% → 30%     │
│   L2 (63.1%)                       │  L3: [==      ] 3.6% → 7%     │
│   L1 (33.3%)                       │                                │
│ 0%───────────────────              │                                │
│   Jan  Mar  May  Jul  Sep  Nov     │                                │
└────────────────────────────────────┴────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ ROW 3: Monthly Breakdown                                [2 panels]  │
├────────────────────────────────────┬────────────────────────────────┤
│ Tickets by Tier (Monthly Bar)     │ Tier Change MoM (Delta)        │
│                                    │                                │
│ 8000─                              │ Month    L1Δ    L2Δ    L3Δ    │
│ 6000─    ████                      │ Jan     +0.5%  -0.3%  -0.2%   │
│ 4000─    ████  ████                │ Feb     +1.2%  -0.8%  -0.4%   │
│ 2000─    ████  ████  ████          │ Mar     +2.1%  -1.5%  -0.6%   │
│    0─────────────────              │ Apr     +1.8%  -1.2%  -0.6%   │
│       Jan   Feb   Mar              │ May     +0.9%  -0.6%  -0.3%   │
│       L1   L2   L3                 │                                │
└────────────────────────────────────┴────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ ROW 4: Category & Automation Impact                     [4 panels]  │
├──────────────┬──────────────┬──────────────┬───────────────────────┤
│ L1 by        │ L2 by        │ Automation   │ Self-Service          │
│ Category     │ Category     │ Savings      │ Deflection            │
│              │              │              │                       │
│ Support: 39% │ Support: 55% │ SSL: 100/qtr │ Password: 60/qtr     │
│ Alert: 22%   │ Alert: 78%   │ Patch: 80/qtr│ Access: 200/qtr      │
│ PHI: 53%     │ PHI: 44%     │ Azure: 40/qtr│ Config: 100/qtr      │
└──────────────┴──────────────┴──────────────┴───────────────────────┘
```

---

## 📋 **Panel Details**

### **Row 1: KPI Summary** (4 Stat Panels)

#### **Panel 1: L1 Percentage**
```sql
-- Current month L1 percentage
SELECT
  ROUND(
    COUNT(*) FILTER (WHERE support_tier = 'L1')::NUMERIC /
    COUNT(*)::NUMERIC * 100,
    1
  ) as l1_percentage
FROM servicedesk.tickets
WHERE DATE_TRUNC('month', "TKT-Created Time"::timestamp) = DATE_TRUNC('month', CURRENT_DATE);
```

**Display**:
- Big number: `33.3%`
- Threshold: Red if <50%, Yellow if 50-60%, Green if ≥60%
- Sparkline: Last 6 months trend
- Target: `60-70%`

#### **Panel 2: L2 Percentage**
Similar query, threshold: Green if ≤35%, Yellow if 35-45%, Red if >45%

#### **Panel 3: L3 Percentage**
Similar query, threshold: Green if 5-10%, Yellow otherwise

#### **Panel 4: Estimated Cost Savings**
```sql
-- Calculate potential savings from tier optimization
SELECT
  ROUND(
    (COUNT(*) FILTER (WHERE support_tier = 'L2') -
     COUNT(*) * 0.30) * 175 + -- L2 avg cost $200, L1 avg cost $25, diff = $175
    (COUNT(*) FILTER (WHERE support_tier = 'L1') -
     COUNT(*) * 0.65) * (-175)
  ) as estimated_savings
FROM servicedesk.tickets
WHERE DATE_TRUNC('month', "TKT-Created Time"::timestamp) = DATE_TRUNC('month', CURRENT_DATE);
```

**Display**: `$0 → $296K/year` (current to potential)

---

### **Row 2: Tier Distribution Trends**

#### **Panel 5: Tier Distribution Over Time** (Stacked Area Chart)
```sql
-- Monthly tier distribution (last 12 months)
SELECT
  DATE_TRUNC('month', "TKT-Created Time"::timestamp) as month,
  support_tier as tier,
  COUNT(*) as ticket_count,
  ROUND(COUNT(*)::NUMERIC / SUM(COUNT(*)) OVER (PARTITION BY DATE_TRUNC('month', "TKT-Created Time"::timestamp)) * 100, 1) as percentage
FROM servicedesk.tickets
WHERE "TKT-Created Time"::timestamp >= CURRENT_DATE - INTERVAL '12 months'
GROUP BY DATE_TRUNC('month', "TKT-Created Time"::timestamp), support_tier
ORDER BY month, tier;
```

**Visualization**: Stacked area chart (100% stacked)
- L1: Blue
- L2: Orange
- L3: Red
- Shows trend toward optimization

#### **Panel 6: Target vs Actual** (3 Gauge Charts)
```sql
-- Current vs target for each tier
SELECT
  support_tier,
  ROUND(COUNT(*)::NUMERIC / (SELECT COUNT(*) FROM servicedesk.tickets WHERE DATE_TRUNC('month', "TKT-Created Time"::timestamp) = DATE_TRUNC('month', CURRENT_DATE))::NUMERIC * 100, 1) as actual_pct,
  CASE
    WHEN support_tier = 'L1' THEN 65.0  -- Target 65% (mid-point of 60-70%)
    WHEN support_tier = 'L2' THEN 30.0  -- Target 30% (mid-point of 25-35%)
    WHEN support_tier = 'L3' THEN 7.5   -- Target 7.5% (mid-point of 5-10%)
  END as target_pct
FROM servicedesk.tickets
WHERE DATE_TRUNC('month', "TKT-Created Time"::timestamp) = DATE_TRUNC('month', CURRENT_DATE)
GROUP BY support_tier;
```

**Visualization**: 3 gauge charts side-by-side
- Shows progress toward target
- Color-coded (green approaching target)

---

### **Row 3: Monthly Breakdown**

#### **Panel 7: Tickets by Tier** (Grouped Bar Chart)
```sql
-- Monthly ticket counts by tier (last 6 months)
SELECT
  DATE_TRUNC('month', "TKT-Created Time"::timestamp) as month,
  support_tier,
  COUNT(*) as ticket_count
FROM servicedesk.tickets
WHERE "TKT-Created Time"::timestamp >= CURRENT_DATE - INTERVAL '6 months'
GROUP BY DATE_TRUNC('month', "TKT-Created Time"::timestamp), support_tier
ORDER BY month, support_tier;
```

**Visualization**: Grouped bar chart (side-by-side bars)

#### **Panel 8: Month-over-Month Change** (Table)
```sql
-- MoM percentage point changes
WITH monthly_pct AS (
  SELECT
    DATE_TRUNC('month', "TKT-Created Time"::timestamp) as month,
    support_tier,
    ROUND(COUNT(*)::NUMERIC / SUM(COUNT(*)) OVER (PARTITION BY DATE_TRUNC('month', "TKT-Created Time"::timestamp)) * 100, 1) as pct
  FROM servicedesk.tickets
  WHERE "TKT-Created Time"::timestamp >= CURRENT_DATE - INTERVAL '6 months'
  GROUP BY DATE_TRUNC('month', "TKT-Created Time"::timestamp), support_tier
)
SELECT
  month,
  MAX(CASE WHEN support_tier = 'L1' THEN pct - LAG(pct) OVER (PARTITION BY support_tier ORDER BY month) END) as "L1 Δ",
  MAX(CASE WHEN support_tier = 'L2' THEN pct - LAG(pct) OVER (PARTITION BY support_tier ORDER BY month) END) as "L2 Δ",
  MAX(CASE WHEN support_tier = 'L3' THEN pct - LAG(pct) OVER (PARTITION BY support_tier ORDER BY month) END) as "L3 Δ"
FROM monthly_pct
GROUP BY month
ORDER BY month DESC;
```

**Visualization**: Table with color-coded deltas
- Green for positive L1 changes, negative L2 changes
- Shows optimization progress

---

### **Row 4: Category & Automation Impact**

#### **Panel 9: L1 by Category** (Pie Chart)
```sql
-- L1 breakdown by category (current month)
SELECT
  "TKT-Category" as category,
  COUNT(*) as count,
  ROUND(COUNT(*)::NUMERIC / (SELECT COUNT(*) FROM servicedesk.tickets WHERE support_tier = 'L1' AND DATE_TRUNC('month', "TKT-Created Time"::timestamp) = DATE_TRUNC('month', CURRENT_DATE))::NUMERIC * 100, 1) as percentage
FROM servicedesk.tickets
WHERE support_tier = 'L1'
  AND DATE_TRUNC('month', "TKT-Created Time"::timestamp) = DATE_TRUNC('month', CURRENT_DATE)
GROUP BY "TKT-Category"
ORDER BY count DESC
LIMIT 10;
```

#### **Panel 10: L2 by Category** (Pie Chart)
Similar to Panel 9, filter for L2

#### **Panel 11: Automation Savings** (Stat Panel with Table)
```sql
-- Track automated ticket reduction (requires automation tracking table)
-- This would need a new table: automation_metrics
SELECT
  automation_type,
  tickets_automated,
  hours_saved,
  cost_saved
FROM servicedesk.automation_metrics  -- To be created
WHERE month = DATE_TRUNC('month', CURRENT_DATE)
ORDER BY tickets_automated DESC;
```

**Note**: Requires new table to track automation impact

#### **Panel 12: Self-Service Deflection** (Stat Panel)
```sql
-- Track self-service portal usage (requires new table)
SELECT
  service_type,
  deflected_tickets,
  success_rate
FROM servicedesk.self_service_metrics  -- To be created
WHERE month = DATE_TRUNC('month', CURRENT_DATE);
```

**Note**: Requires new table for self-service tracking

---

## 🔧 **Implementation Requirements**

### **1. Database Schema Changes**

#### **Add `support_tier` Column to `tickets` Table**
```sql
-- Add support_tier column (L1/L2/L3)
ALTER TABLE servicedesk.tickets
ADD COLUMN support_tier VARCHAR(3);

-- Backfill with tier categorization logic (from your Python script)
-- This would be done via the categorize_tickets_by_tier.py script
```

#### **Create `tier_history` Table** (Track changes over time)
```sql
CREATE TABLE servicedesk.tier_history (
  id SERIAL PRIMARY KEY,
  snapshot_date DATE NOT NULL,
  support_tier VARCHAR(3) NOT NULL,
  ticket_count INTEGER NOT NULL,
  percentage NUMERIC(5,2) NOT NULL,
  category VARCHAR(100),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for fast queries
CREATE INDEX idx_tier_history_date ON servicedesk.tier_history(snapshot_date);
CREATE INDEX idx_tier_history_tier ON servicedesk.tier_history(support_tier);
```

#### **Create `automation_metrics` Table** (Track automation impact)
```sql
CREATE TABLE servicedesk.automation_metrics (
  id SERIAL PRIMARY KEY,
  month DATE NOT NULL,
  automation_type VARCHAR(100) NOT NULL,  -- 'SSL Alerts', 'Password Reset', etc.
  tickets_automated INTEGER NOT NULL,
  hours_saved NUMERIC(10,2),
  cost_saved NUMERIC(10,2),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **Create `self_service_metrics` Table** (Track self-service)
```sql
CREATE TABLE servicedesk.self_service_metrics (
  id SERIAL PRIMARY KEY,
  month DATE NOT NULL,
  service_type VARCHAR(100) NOT NULL,  -- 'Password Reset', 'Account Access', etc.
  deflected_tickets INTEGER NOT NULL,
  success_rate NUMERIC(5,2),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### **2. Data Population Scripts**

#### **Script 1: Backfill Support Tiers** (One-time)
```python
# claude/tools/sre/backfill_support_tiers_to_postgres.py

"""
Backfill support_tier column in PostgreSQL using tier categorization logic.

Reads from servicedesk.tickets, applies L1/L2/L3 logic, updates support_tier column.
"""

import psycopg2
from categorize_tickets_by_tier import TierCategorizer

# Connect to PostgreSQL
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="servicedesk",
    user="servicedesk_user",
    password="<from .env>"
)

# Load all tickets
cursor = conn.cursor()
cursor.execute('SELECT "TKT-Ticket ID", "TKT-Title", "TKT-Description", "TKT-Category", "TKT-Root Cause Category" FROM servicedesk.tickets')

# Categorize and update
categorizer = TierCategorizer()
for row in cursor.fetchall():
    ticket_id, title, description, category, root_cause = row

    tier = categorizer.categorize_ticket({
        'title': title,
        'description': description,
        'category': category,
        'root_cause': root_cause
    })

    # Update database
    update_cursor = conn.cursor()
    update_cursor.execute(
        'UPDATE servicedesk.tickets SET support_tier = %s WHERE "TKT-Ticket ID" = %s',
        (tier, ticket_id)
    )
    update_cursor.close()

conn.commit()
conn.close()
```

#### **Script 2: Monthly Tier Snapshot** (Recurring)
```python
# claude/tools/sre/capture_tier_snapshot.py

"""
Capture monthly tier distribution snapshot for trend tracking.

Run: Monthly (cron job or manual)
"""

import psycopg2
from datetime import date

conn = psycopg2.connect(...)

cursor = conn.cursor()

# Calculate tier distribution for current month
cursor.execute('''
  SELECT
    support_tier,
    COUNT(*) as ticket_count,
    ROUND(COUNT(*)::NUMERIC / SUM(COUNT(*)) OVER () * 100, 2) as percentage
  FROM servicedesk.tickets
  WHERE DATE_TRUNC('month', "TKT-Created Time"::timestamp) = DATE_TRUNC('month', CURRENT_DATE)
  GROUP BY support_tier
''')

# Insert into tier_history
for row in cursor.fetchall():
    tier, count, pct = row
    insert_cursor = conn.cursor()
    insert_cursor.execute(
        'INSERT INTO servicedesk.tier_history (snapshot_date, support_tier, ticket_count, percentage) VALUES (%s, %s, %s, %s)',
        (date.today(), tier, count, pct)
    )
    insert_cursor.close()

conn.commit()
conn.close()
```

---

### **3. Grafana Dashboard JSON**

**Location**: `infrastructure/servicedesk-dashboard/grafana/provisioning/dashboards/servicedesk-tier-tracker.json`

**Dashboard Structure**:
```json
{
  "dashboard": {
    "uid": "servicedesk-tier-tracker",
    "title": "ServiceDesk Tier Optimization Tracker",
    "tags": ["servicedesk", "tier-analysis", "optimization"],
    "timezone": "browser",
    "refresh": "5m",
    "time": {
      "from": "now-12M",
      "to": "now"
    },
    "panels": [
      // 12 panels as designed above
    ]
  }
}
```

**Note**: Full JSON would be ~500-800 lines (generated by Grafana UI or scripted)

---

## 📅 **Implementation Timeline** (With SRE Agent)

### **Phase 1: Database Preparation** (1-2 hours)
1. Add `support_tier` column to `tickets` table
2. Create `tier_history`, `automation_metrics`, `self_service_metrics` tables
3. Run backfill script to populate `support_tier` column

### **Phase 2: Dashboard Creation** (2-3 hours)
1. Create Grafana dashboard via UI (12 panels)
2. Export JSON and save to provisioning directory
3. Test all queries and visualizations

### **Phase 3: Automation Setup** (1-2 hours)
1. Create monthly snapshot cron job (`capture_tier_snapshot.py`)
2. Set up automation/self-service tracking (future)
3. Document operational procedures

**Total**: ~5-7 hours implementation time (with SRE Agent)

---

## 💡 **Key Features**

### **What Makes This Dashboard Valuable**

1. **Trend Visibility**: See tier distribution changes over time (are we improving?)
2. **Goal Tracking**: Visual progress toward industry benchmarks
3. **ROI Measurement**: Quantify cost savings from optimization
4. **Early Warning**: Alerts when tiers drift from targets
5. **Category Insights**: Which categories improving/declining at L1
6. **Automation ROI**: Track actual impact of automation initiatives

### **Business Value**

- **Executives**: "$296K savings opportunity, 33% → 60% L1 progress"
- **Operations**: "L1 FCR improving 5% month-over-month"
- **Management**: "Support Tickets category L1 rate: 39% → 52% (goal: 60%)"
- **Team**: "Automation reduced SSL alerts by 100 tickets/quarter"

---

## 🚀 **Next Steps** (When Ready to Build)

### **With SRE Agent**:

1. **Load SRE Principal Engineer Agent**
2. **Provide this research document**
3. **Request**: "Build ServiceDesk Tier Tracking Dashboard following the design in TIER_TRACKING_DASHBOARD_RESEARCH.md"

### **SRE Agent Will**:
1. Review existing Grafana/PostgreSQL infrastructure
2. Create database schema changes (tier_history, automation_metrics tables)
3. Write backfill and snapshot scripts
4. Build Grafana dashboard JSON
5. Test end-to-end
6. Document operational procedures

**Estimated Effort**: 5-7 hours (with SRE Agent automation)

---

## 📊 **Alternative: Quick Win Dashboard** (Simpler Version)

If full implementation too complex, start with **3-panel minimal dashboard**:

### **Minimal Tier Tracker** (1 hour implementation)

**Panel 1**: Current Tier Distribution (Pie Chart)
**Panel 2**: Tier Trend (Last 6 months - Line Chart)
**Panel 3**: Target vs Actual (Gauge Charts)

**Requirements**: Only needs `support_tier` column added to `tickets` table

**Value**: 80% of insights, 20% of implementation effort

---

## 📂 **Files to Create** (Summary)

When implementing with SRE Agent, create:

1. **Database Migrations**:
   - `001_add_support_tier_column.sql`
   - `002_create_tier_history_table.sql`
   - `003_create_automation_metrics_table.sql`
   - `004_create_self_service_metrics_table.sql`

2. **Python Scripts**:
   - `backfill_support_tiers_to_postgres.py`
   - `capture_tier_snapshot.py` (monthly cron)
   - `update_automation_metrics.py` (track automation)

3. **Grafana Dashboard**:
   - `servicedesk-tier-tracker.json`

4. **Documentation**:
   - `TIER_DASHBOARD_OPERATIONS.md` (how to maintain)

---

**Research Completed**: 2025-10-27
**Status**: Ready for SRE Agent implementation
**Estimated ROI**: High (enables tracking $296K/year optimization opportunity)
