# ServiceDesk Tier Tracking Dashboard - Requirements Document

**Project**: TIER-TRACKER-001
**Created**: 2025-10-27
**Agent**: SRE Principal Engineer + Service Desk Manager Agent
**Status**: Requirements Discovery (TDD Phase 1)
**User Confirmation**: PENDING

---

## 📋 **Pre-Flight Validation** ✅ COMPLETE

### Architecture Review
- [x] Read ARCHITECTURE.md (infrastructure/servicedesk-dashboard/)
- [x] Deployment model understood: Docker Compose (Grafana + PostgreSQL)
- [x] Integration points verified: `docker exec` for PostgreSQL access
- [x] Containers verified running:
  - servicedesk-postgres (Up 5 days, healthy, port 5432)
  - servicedesk-grafana (Up 8 days, healthy, port 3000)
- [x] Database schema verified: 7 tables, 266,622 rows
- [x] ADRs reviewed: ADR-001 (PostgreSQL Docker), ADR-002 (Grafana choice)

### User Decisions Confirmed
- [x] **Cost Model**: L1=$100, L2=$200, L3=$300 (adjustable via config table)
- [x] **Pod Tracking**: Yes, now (pods forming, need Panel 11)
- [x] **Automation Metrics**: Phase 2 (1-2 months, tables prepared now)
- [x] **Alert Notifications**: Dashboard only (no email/Slack for now)

---

## 🎯 **1. CORE PURPOSE**

### Problem Statement
ServiceDesk currently has sub-optimal tier distribution (33.3% L1, 63.1% L2, 3.6% L3) compared to industry benchmarks (60% L1, 30% L2, 10% L3), resulting in higher operational costs ($1.86M/year vs $1.64M/year optimized).

**Root Issues**:
- No visibility into tier distribution trends over time
- No tracking of optimization progress toward goals
- No quantified ROI measurement for tier optimization initiatives
- No pod performance comparison as teams form
- No automated alerting when tier distribution drifts from targets

### Solution
Create a Grafana dashboard leveraging existing ServiceDesk infrastructure (PostgreSQL + Grafana) to track tier distribution, measure progress, calculate cost savings, and enable data-driven optimization decisions.

### Success Criteria
1. ✅ Dashboard displays current tier percentages (L1/L2/L3) with industry benchmark comparison
2. ✅ Historical trends visible (12-month rolling window, month-over-month changes)
3. ✅ Cost savings calculations accurate ($148K/year opportunity with updated cost model)
4. ✅ Pod performance tracking operational (L1 rates by pod as teams form)
5. ✅ Automated alerts configured (L1 <50%, L2 >50% for 7 days)
6. ✅ Dashboard loads in <2 seconds, queries return in <100ms P95
7. ✅ Cost model adjustable without code changes (tier_cost_config table)
8. ✅ Zero technical debt (SRE-hardened implementation with 100% test coverage)

### Who Will Use This
- **Executives**: Track $148K/year savings opportunity, strategic decision-making
- **Operations Managers**: Monitor tier distribution trends, identify optimization opportunities
- **Team Leads**: Compare pod performance (L1 rates), identify training needs
- **Support Teams**: Understand categorization patterns, improve ticket handling

---

## 📊 **2. FUNCTIONAL REQUIREMENTS**

### FR-1: Current Tier Distribution Display (Row 1 - KPI Summary)

**FR-1.1: L1 Percentage Panel**
- **Input**: Current month tickets from servicedesk.tickets table
- **Processing**: Calculate % of tickets with support_tier='L1'
- **Output**: Big number display (e.g., "33.3%")
- **Thresholds**:
  - Red: <50% (significantly below target)
  - Yellow: 50-60% (approaching target)
  - Green: ≥60% (at or above target 60-70% range)
- **Additional**: Sparkline showing last 6 months trend
- **Target Display**: Show "Target: 60-70%"

**FR-1.2: L2 Percentage Panel**
- **Input**: Current month tickets
- **Processing**: Calculate % of tickets with support_tier='L2'
- **Output**: Big number display (e.g., "63.1%")
- **Thresholds**:
  - Green: ≤35% (at or below target)
  - Yellow: 35-45% (slightly above target)
  - Red: >45% (significantly above target)
- **Target Display**: "Target: 25-35%"

**FR-1.3: L3 Percentage Panel**
- **Input**: Current month tickets
- **Processing**: Calculate % of tickets with support_tier='L3'
- **Output**: Big number display (e.g., "3.6%")
- **Thresholds**:
  - Green: 5-10% (optimal range)
  - Yellow: Otherwise
- **Target Display**: "Target: 5-10%"

**FR-1.4: Cost Savings Panel**
- **Input**:
  - Current tier distribution (actual percentages)
  - Target tier distribution (from tier_cost_config table)
  - Tier costs (from tier_cost_config table)
  - Current month ticket volume
- **Processing**:
  - Calculate current annual cost: Σ(tier_count × tier_cost × 12)
  - Calculate optimized cost: Σ(target_count × tier_cost × 12)
  - Savings = Current cost - Optimized cost
- **Output**: "$148K/year" (annual savings opportunity)
- **Display Format**: "$XXK → $YYK" (current to optimized)

**Acceptance Criteria FR-1**:
- [ ] All 4 panels render correctly with real data
- [ ] Color thresholds apply automatically based on current values
- [ ] Cost calculation uses tier_cost_config table (NO hardcoded values)
- [ ] Panels update when time range changed

---

### FR-2: Historical Trend Visualization (Row 2 - Trends)

**FR-2.1: Tier Distribution Over Time (Stacked Area Chart)**
- **Input**: Last 12 months of tickets, support_tier values
- **Processing**:
  - Group tickets by month
  - Calculate tier % for each month
  - Generate time-series data (month, L1%, L2%, L3%)
- **Output**: 100% stacked area chart
  - X-axis: Months (last 12 months)
  - Y-axis: Percentage (0-100%)
  - Areas: L1 (blue), L2 (orange), L3 (red)
- **Interaction**: Hover shows exact percentages for that month
- **Business Value**: Visualize trend toward optimization (L1 increasing, L2 decreasing over time)

**FR-2.2: Target vs Actual (3 Gauge Charts)**
- **Input**:
  - Current month tier percentages (actual)
  - Target percentages from tier_cost_config (L1: 65%, L2: 30%, L3: 7.5%)
- **Processing**: Calculate gap between actual and target
- **Output**: 3 side-by-side gauge charts
  - Gauge 1: L1 progress (33.3% → 65% target)
  - Gauge 2: L2 progress (63.1% → 30% target)
  - Gauge 3: L3 progress (3.6% → 7.5% target)
- **Visual**: Needle pointing to current value, target marked on gauge
- **Color**: Green approaching target, red far from target

**Acceptance Criteria FR-2**:
- [ ] Stacked area chart shows 12 months of data
- [ ] Chart updates dynamically when new month added
- [ ] Gauges show correct gap between actual and target
- [ ] Targets pulled from tier_cost_config table (data-driven)

---

### FR-3: Monthly Breakdown Analysis (Row 3 - Breakdown)

**FR-3.1: Tickets by Tier (Grouped Bar Chart)**
- **Input**: Last 6 months of tickets
- **Processing**:
  - Group tickets by month and tier
  - Count tickets for each (month, tier) combination
- **Output**: Grouped bar chart
  - X-axis: Months (last 6 months)
  - Y-axis: Ticket count
  - Bars: L1 (blue), L2 (orange), L3 (red) side-by-side
- **Business Value**: See absolute volumes (not just percentages), identify seasonal patterns

**FR-3.2: Month-over-Month Change (Delta Table)**
- **Input**: Last 6 months tier percentages
- **Processing**:
  - Calculate MoM percentage point change: Current month % - Previous month %
  - Example: Jan L1=33%, Feb L1=35% → Delta=+2.0%
- **Output**: Table with columns:
  - Month
  - L1 Δ (percentage point change, e.g., "+2.0%")
  - L2 Δ
  - L3 Δ
- **Color Coding**:
  - L1: Green for positive Δ, red for negative Δ
  - L2: Green for negative Δ (reduction is good), red for positive Δ
  - L3: Neutral (target range 5-10%, both directions acceptable)
- **Business Value**: Quick visual identification of improvement/regression

**Acceptance Criteria FR-3**:
- [ ] Bar chart shows last 6 months correctly
- [ ] Delta table calculates MoM changes correctly
- [ ] Color coding reflects optimization direction (L1 increase=good, L2 decrease=good)

---

### FR-4: Category & Pod Insights (Row 4)

**FR-4.1: L1 by Category (Pie Chart)**
- **Input**: Current month L1 tickets
- **Processing**:
  - Group by TKT-Category
  - Calculate count and percentage for each category
  - Limit to top 10 categories
- **Output**: Pie chart showing L1 distribution across categories
- **Labels**: Category name + percentage (e.g., "Support: 39%")
- **Business Value**: Identify which categories achieving L1 success, which need improvement

**FR-4.2: L2 by Category (Pie Chart)**
- **Input**: Current month L2 tickets
- **Processing**: Same as FR-4.1, but filter for L2
- **Output**: Pie chart showing L2 distribution
- **Business Value**: Identify categories with high L2 rates (escalation opportunities)

**FR-4.3: L1 Rate by Pod (Bar Chart)** ⭐ NEW - Pod Tracking
- **Input**:
  - Current month tickets
  - Filter: assigned_pod IS NOT NULL
- **Processing**:
  - Group by assigned_pod
  - Calculate L1 rate: COUNT(support_tier='L1') / COUNT(*) × 100
- **Output**: Horizontal bar chart
  - X-axis: L1 percentage (0-100%)
  - Y-axis: Pod names (e.g., "Cloud Pod", "Security Pod")
  - Bars: Color-coded (green ≥60%, yellow 50-60%, red <50%)
- **Target Line**: Vertical line at 60% (target L1 rate)
- **Business Value**: Compare pod performance, identify training needs, share best practices

**Acceptance Criteria FR-4**:
- [ ] Pie charts show top 10 categories correctly
- [ ] Pod bar chart filters out NULL pods (historical tickets)
- [ ] Pod bar chart shows pods in descending order (highest L1 rate first)
- [ ] Target line visible at 60% on pod chart

---

### FR-5: Alerting & Notifications

**FR-5.1: L1 Rate Below Target Alert**
- **Trigger Condition**: L1 percentage <50% for 7 consecutive days
- **Severity**: Warning (not critical)
- **Action**: Dashboard notification only (Grafana UI bell icon)
- **Runbook Reference**: "Check tier categorization logic, review recent tickets"
- **Anti-Noise**: 7-day threshold prevents false alarms from daily fluctuations

**FR-5.2: L2 Rate Above Target Alert**
- **Trigger Condition**: L2 percentage >50% for 7 consecutive days
- **Severity**: Warning
- **Action**: Dashboard notification only
- **Runbook Reference**: "Identify escalation patterns, training opportunities"

**FR-5.3: Future Extension (Not Phase 1)**
- Email/Slack notifications (when requested by user)
- Effort: +15 minutes to add notification channel

**Acceptance Criteria FR-5**:
- [ ] Alerts visible in Grafana UI (bell icon)
- [ ] Alert state changes logged in Grafana alert history
- [ ] Test alert fires correctly (simulate L1 <50% condition)
- [ ] No false alarms from short-term fluctuations (<7 days)

---

### FR-6: Data Management & Automation

**FR-6.1: Monthly Tier Snapshot**
- **Schedule**: 1st day of each month at 00:00 (cron job)
- **Input**: Previous month tier distribution
- **Processing**:
  - Calculate tier percentages for completed month
  - Insert into tier_history table (snapshot_date, tier, count, percentage)
- **Output**: tier_history table populated weekly (52 snapshots/year)
- **Logging**: Snapshot date, week ending date, tier counts, completion status
- **Granularity**: Weekly (not monthly) for operational tracking
- **Storage**: 156 rows/year (52 weeks × 3 tiers)

**FR-6.2: Daily Data Validation**
- **Schedule**: Daily at 2:00 AM (cron job)
- **Validation Checks**:
  1. NULL tier check: COUNT(support_tier IS NULL) = 0
  2. Valid tier check: support_tier IN ('L1', 'L2', 'L3')
  3. Percentage sum check: L1% + L2% + L3% = 100%
- **Alert Threshold**: >1% NULL tiers or invalid tiers
- **Logging**: Validation results, error count, anomaly details

**FR-6.3: Cost Configuration Management**
- **Table**: tier_cost_config
- **Fields**:
  - tier (VARCHAR(10), PRIMARY KEY): 'L1', 'L2', 'L3'
  - cost_per_ticket (NUMERIC): $100, $200, $300
  - target_percentage (NUMERIC): 65.0, 30.0, 7.5
  - effective_date (DATE): When costs/targets became active
- **Update Process**: UPDATE tier_cost_config SET cost_per_ticket=X WHERE tier='L1'
- **No Code Changes**: Dashboard queries pull from config table dynamically

**Acceptance Criteria FR-6**:
- [ ] Monthly snapshot runs automatically (cron verified)
- [ ] Daily validation runs automatically
- [ ] Validation errors logged and visible
- [ ] Cost updates via SQL (no code deployment needed)

---

## ⚙️ **3. NON-FUNCTIONAL REQUIREMENTS**

### NFR-1: Performance

**NFR-1.1: Query Performance**
- **SLO**: All dashboard queries <100ms (P95 latency)
- **Measurement**: Grafana query timing, PostgreSQL slow query log
- **Optimization**: Indexes on support_tier, snapshot_date, assigned_pod

**NFR-1.2: Dashboard Load Time**
- **SLO**: Dashboard loads in <2 seconds (cold start)
- **Measurement**: Browser DevTools Network tab
- **Optimization**: Query result caching, panel lazy loading

**NFR-1.3: Backfill Performance**
- **SLO**: Backfill 10,939 rows in <5 minutes
- **Measurement**: Script execution timer
- **Optimization**: Batch updates (executemany), transaction-safe commits

**Acceptance Criteria NFR-1**:
- [ ] Performance tests validate <100ms query latency (P95)
- [ ] Dashboard load test shows <2s total load time
- [ ] Backfill script tested and completes in <5 minutes

---

### NFR-2: Reliability (SRE Requirements)

**NFR-2.1: Data Quality**
- **Requirement**: 100% of tickets have valid support_tier (L1/L2/L3)
- **Validation**: Pre-insert checks, daily validation cron
- **Error Handling**: Reject invalid tier values, log errors

**NFR-2.2: Graceful Degradation**
- **Requirement**: Dashboard shows cached data if PostgreSQL unavailable
- **Implementation**: Grafana query result caching (5 min TTL)
- **User Experience**: Stale data indicator when cache served

**NFR-2.3: Transaction Safety**
- **Requirement**: Backfill script uses transactions (COMMIT only on success)
- **Error Handling**: ROLLBACK on errors, preserve data integrity
- **Idempotency**: Re-running backfill safe (UPDATE WHERE clause prevents duplicates)

**NFR-2.4: Observability**
- **Logging**:
  - Structured logs for all database operations
  - Progress logging every 1000 rows during backfill
  - Error context (SQL query, parameters, stack trace)
- **Metrics**:
  - Query latency histogram (P50, P95, P99)
  - Error rate (failures per 1000 queries)
  - Data quality score (% valid tiers)
- **Alerting**:
  - Tier distribution thresholds (L1 <50%, L2 >50%)
  - Data validation failures (>1% invalid tiers)

**Acceptance Criteria NFR-2**:
- [ ] Data validation tests pass (100% valid tiers)
- [ ] Transaction rollback tested (simulate error mid-backfill)
- [ ] Graceful degradation tested (stop PostgreSQL, verify cached data)
- [ ] Observability instrumentation complete (logs, metrics, alerts)

---

### NFR-3: Security

**NFR-3.1: Credential Management**
- **Requirement**: Database credentials in .env file (NOT hardcoded)
- **Implementation**: Load credentials via environment variables
- **Access Control**: .env file gitignored, file permissions 0600

**NFR-3.2: Database Access**
- **Requirement**: Use `docker exec` for PostgreSQL access (per ARCHITECTURE.md)
- **Rationale**: Database in isolated Docker container (ADR-001)
- **Anti-Pattern**: Direct psycopg2 connection (will fail)

**Acceptance Criteria NFR-3**:
- [ ] No hardcoded credentials in code (grep verification)
- [ ] Database access via docker exec (matches ARCHITECTURE.md)
- [ ] .env file permissions verified (0600 or more restrictive)

---

### NFR-4: Maintainability

**NFR-4.1: Configuration Table (Cost/Target Flexibility)**
- **Requirement**: Costs and targets in tier_cost_config table (NOT hardcoded)
- **Benefit**: Update costs without code changes (user requirement)
- **Implementation**: All queries JOIN tier_cost_config for dynamic values

**NFR-4.2: Test Coverage**
- **Requirement**: 100% test coverage for database operations
- **Test Types**:
  - Unit tests: Schema, data validation, tier categorization
  - Integration tests: End-to-end queries, dashboard panels
  - Performance tests: Query latency, dashboard load time
  - Failure mode tests: Connection errors, invalid data, rollbacks
- **Framework**: pytest + psycopg2

**NFR-4.3: Documentation**
- **Required Files**:
  - ARCHITECTURE.md updated (new dashboard, schema changes)
  - ADR-003: Tier Tracker Dashboard Design
  - TIER_DASHBOARD_OPERATIONS.md (operational runbook)
  - active_deployments.md updated

**Acceptance Criteria NFR-4**:
- [ ] Cost update tested (change L1 cost via SQL, verify dashboard updates)
- [ ] Test coverage report shows 100% for database ops
- [ ] Documentation complete and reviewed

---

### NFR-5: Future Extensibility

**NFR-5.1: Pod Tracking (Phase 1)**
- **Column**: assigned_pod VARCHAR(50) (NULL for historical tickets)
- **Backfill Handling**: NULL pods filtered out from pod comparison panel
- **Migration Path**: UPDATE tickets SET assigned_pod='Cloud Pod' WHERE team='Cloud'

**NFR-5.2: Automation Metrics (Phase 2 - Prepared)**
- **Tables Created Now**: automation_metrics, self_service_metrics
- **Panels Deferred**: Panels 12-13 (automation impact)
- **Timeline**: 1-2 months (when automation data available)
- **Effort**: +2-3 hours to add panels when ready

**NFR-5.3: Tier Redefinition Flexibility**
- **Current**: Categorization logic in backfill_support_tiers_to_postgres.py
- **Change Process**:
  1. Update categorization logic
  2. Re-run backfill script (<5 min)
  3. Dashboard queries unchanged (same support_tier column)

**Acceptance Criteria NFR-5**:
- [ ] assigned_pod column supports NULL (historical tickets)
- [ ] Pod panel filters WHERE assigned_pod IS NOT NULL
- [ ] Automation tables created (empty, ready for Phase 2)

---

## 📐 **4. DATABASE SCHEMA REQUIREMENTS**

### Schema Change 1: Add support_tier Column
```sql
ALTER TABLE servicedesk.tickets
ADD COLUMN support_tier VARCHAR(10);

-- Reason for VARCHAR(10): Accommodates future tier naming
-- Examples: 'L1', 'L2', 'L3', 'Tier 1', 'L1-Standard'
```

**Validation**:
- [ ] Column exists: `\d servicedesk.tickets` shows support_tier
- [ ] Length correct: VARCHAR(10)
- [ ] NULL allowed initially (backfill populates values)

---

### Schema Change 2: Add assigned_pod Column ⭐ NEW
```sql
ALTER TABLE servicedesk.tickets
ADD COLUMN assigned_pod VARCHAR(50);

-- NULL for historical tickets (before pod structure)
-- Populated for new tickets as pods form
```

**Validation**:
- [ ] Column exists
- [ ] NULL handling tested (historical tickets excluded from pod panel)

---

### Schema Change 3: Create tier_history Table
```sql
CREATE TABLE servicedesk.tier_history (
  id SERIAL PRIMARY KEY,
  snapshot_date DATE NOT NULL,
  support_tier VARCHAR(10) NOT NULL,
  ticket_count INTEGER NOT NULL,
  percentage NUMERIC(5,2) NOT NULL,
  category VARCHAR(100),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tier_history_date ON servicedesk.tier_history(snapshot_date);
CREATE INDEX idx_tier_history_tier ON servicedesk.tier_history(support_tier);
```

**Purpose**: Track tier distribution snapshots monthly for trend analysis

**Validation**:
- [ ] Table exists with correct schema
- [ ] Indexes created (query performance)
- [ ] Monthly snapshot script inserts correctly

---

### Schema Change 4: Create tier_cost_config Table
```sql
CREATE TABLE servicedesk.tier_cost_config (
  tier VARCHAR(10) PRIMARY KEY,
  cost_per_ticket NUMERIC(10,2) NOT NULL,
  target_percentage NUMERIC(5,2) NOT NULL,
  effective_date DATE NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO servicedesk.tier_cost_config VALUES
  ('L1', 100.00, 65.0, CURRENT_DATE),
  ('L2', 200.00, 30.0, CURRENT_DATE),
  ('L3', 300.00, 7.5, CURRENT_DATE);
```

**Purpose**: Data-driven cost/target management (NO hardcoded values)

**Validation**:
- [ ] Table exists with initial data (L1/L2/L3)
- [ ] Cost update tested (UPDATE tier_cost_config, verify dashboard changes)
- [ ] Panel 4 query uses config table (no hardcoded costs)

---

### Schema Change 5: Create Automation Tables (Phase 2 Prep)
```sql
CREATE TABLE servicedesk.automation_metrics (
  id SERIAL PRIMARY KEY,
  month DATE NOT NULL,
  automation_type VARCHAR(100) NOT NULL,
  tickets_automated INTEGER NOT NULL,
  hours_saved NUMERIC(10,2),
  cost_saved NUMERIC(10,2),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE servicedesk.self_service_metrics (
  id SERIAL PRIMARY KEY,
  month DATE NOT NULL,
  service_type VARCHAR(100) NOT NULL,
  deflected_tickets INTEGER NOT NULL,
  success_rate NUMERIC(5,2),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Purpose**: Prepare for Phase 2 automation panels (1-2 months)

**Validation**:
- [ ] Tables created (empty for now)
- [ ] Schema matches future panel requirements

---

### Schema Change 6: Performance Indexes
```sql
CREATE INDEX idx_tickets_support_tier ON servicedesk.tickets(support_tier);
CREATE INDEX idx_tickets_assigned_pod ON servicedesk.tickets(assigned_pod);
CREATE INDEX idx_tickets_created_time ON servicedesk.tickets("TKT-Created Time");
```

**Purpose**: Ensure <100ms query latency (NFR-1.1)

**Validation**:
- [ ] Indexes created
- [ ] Query performance tests show <100ms P95

---

## 🔄 **5. DATA PROCESSING REQUIREMENTS**

### DP-1: Tier Categorization Logic

**Input**: Ticket attributes (title, description, category, root_cause)

**Processing**: Apply categorization rules from categorize_tickets_by_tier.py
- **L1 Examples**: Standard requests, password resets, access grants, alerts, routine configs
- **L2 Examples**: Escalated issues, complex troubleshooting, multi-step resolutions
- **L3 Examples**: Architectural changes, emergency escalations, vendor involvement

**Output**: support_tier value ('L1', 'L2', or 'L3')

**Edge Cases**:
- NULL description → Use category/title only
- NULL category → Use description/title only
- Ambiguous cases → Default to L2 (safer overestimate)

**Validation**:
- [ ] 100+ sample tickets categorized correctly (manual review)
- [ ] NULL handling tested (no crashes, reasonable defaults)
- [ ] Edge case tests pass (ambiguous tickets → L2)

---

### DP-2: Backfill Process

**Script**: backfill_support_tiers_to_postgres.py

**Input**: 10,939 tickets from servicedesk.tickets (support_tier IS NULL)

**Processing**:
1. Load all tickets (id, title, description, category, root_cause)
2. Batch categorize (1000 rows at a time)
3. Batch update: `executemany('UPDATE ... SET support_tier=? WHERE id=?', batch)`
4. Log progress every 1000 rows
5. COMMIT on success, ROLLBACK on error

**Output**: 100% of tickets have valid support_tier

**Performance Optimization**:
- Batch size: 1000 rows (10-20x faster than row-by-row)
- Single transaction (atomic, rollback on error)
- Progress logging (visibility during 5 min execution)

**Validation**:
- [ ] Backfill completes in <5 minutes (NFR-1.3)
- [ ] 100% of rows updated (no NULL tiers remain)
- [ ] Transaction safety tested (simulate error mid-backfill, verify rollback)
- [ ] Idempotency tested (re-run backfill, no duplicates/errors)

---

### DP-3: Weekly Snapshot Capture ⭐ UPDATED

**Script**: capture_tier_snapshot.py

**Schedule**: Every Sunday, 00:00 (cron: `0 0 * * 0`)

**Processing**:
```sql
INSERT INTO servicedesk.tier_history (snapshot_date, support_tier, ticket_count, percentage)
SELECT
  DATE_TRUNC('week', CURRENT_DATE - INTERVAL '1 week') as snapshot_date,
  support_tier,
  COUNT(*) as ticket_count,
  ROUND(COUNT(*)::NUMERIC / SUM(COUNT(*)) OVER () * 100, 2) as percentage
FROM servicedesk.tickets
WHERE DATE_TRUNC('week', "TKT-Created Time"::timestamp) = DATE_TRUNC('week', CURRENT_DATE - INTERVAL '1 week')
GROUP BY support_tier;
```

**Output**: tier_history table populated with previous week snapshot (52 times/year)

**Validation**:
- [ ] Weekly snapshot inserts correct data (spot check against dashboard)
- [ ] Cron job runs every Sunday (verify via crontab -l, check logs)
- [ ] Idempotency safe (duplicate snapshots prevented)
- [ ] 52 data points visible in dashboard after 1 year

---

### DP-4: Daily Data Validation

**Script**: validate_tier_data.py

**Schedule**: Daily, 02:00 (cron)

**Validation Checks**:
1. **NULL Check**: `SELECT COUNT(*) FROM tickets WHERE support_tier IS NULL` (expect: 0)
2. **Valid Tier Check**: `SELECT COUNT(*) FROM tickets WHERE support_tier NOT IN ('L1','L2','L3')` (expect: 0)
3. **Percentage Sum**: `SELECT SUM(percentage) FROM tier_history WHERE snapshot_date=CURRENT_DATE-1` (expect: 100.0)

**Alert Threshold**: >1% invalid/NULL tiers

**Output**: Log validation results, alert on failures

**Validation**:
- [ ] Validation script detects NULL tiers (test with intentional NULL)
- [ ] Validation script detects invalid tiers (test with 'L4')
- [ ] Alerts fire when threshold exceeded

---

## 📊 **6. DASHBOARD PANEL SPECIFICATIONS**

### Panel 1: L1 Percentage (Stat Panel)
**Query**:
```sql
SELECT ROUND(
  COUNT(*) FILTER (WHERE support_tier = 'L1')::NUMERIC /
  COUNT(*)::NUMERIC * 100, 1
) as l1_percentage
FROM servicedesk.tickets
WHERE DATE_TRUNC('month', "TKT-Created Time"::timestamp) = DATE_TRUNC('month', CURRENT_DATE);
```

**Visualization**: Stat panel, big number
**Thresholds**: Red <50%, Yellow 50-60%, Green ≥60%
**Sparkline**: Last 6 months trend
**Unit**: Percentage (%)

---

### Panel 2: L2 Percentage (Stat Panel)
**Query**: Similar to Panel 1, filter for L2
**Thresholds**: Green ≤35%, Yellow 35-45%, Red >45%

---

### Panel 3: L3 Percentage (Stat Panel)
**Query**: Similar to Panel 1, filter for L3
**Thresholds**: Green 5-10%, Yellow otherwise

---

### Panel 4: Cost Savings (Stat Panel)
**Query**:
```sql
WITH costs AS (
  SELECT tier, cost_per_ticket, target_percentage
  FROM servicedesk.tier_cost_config
),
current_dist AS (
  SELECT
    support_tier,
    COUNT(*) as count,
    COUNT(*)::NUMERIC / SUM(COUNT(*)) OVER () as percentage
  FROM servicedesk.tickets
  WHERE DATE_TRUNC('month', "TKT-Created Time"::timestamp) = DATE_TRUNC('month', CURRENT_DATE)
  GROUP BY support_tier
)
SELECT ROUND(
  SUM((cd.percentage - (c.target_percentage / 100)) * cd.count * 12 * c.cost_per_ticket)
) as estimated_annual_savings
FROM current_dist cd
JOIN costs c ON cd.support_tier = c.tier;
```

**Visualization**: Stat panel
**Unit**: Currency (USD)

---

### Panel 5: Tier Distribution Over Time (Stacked Area Chart)
**Query**:
```sql
SELECT
  DATE_TRUNC('month', "TKT-Created Time"::timestamp) as month,
  support_tier,
  ROUND(COUNT(*)::NUMERIC / SUM(COUNT(*)) OVER (PARTITION BY DATE_TRUNC('month', "TKT-Created Time"::timestamp)) * 100, 1) as percentage
FROM servicedesk.tickets
WHERE "TKT-Created Time"::timestamp >= CURRENT_DATE - INTERVAL '12 months'
GROUP BY DATE_TRUNC('month', "TKT-Created Time"::timestamp), support_tier
ORDER BY month, support_tier;
```

**Visualization**: Stacked area (100% stacked)
**Colors**: L1=Blue, L2=Orange, L3=Red

---

### Panel 6: Target vs Actual (3 Gauges)
**Query**:
```sql
SELECT
  support_tier,
  ROUND(COUNT(*)::NUMERIC / (SELECT COUNT(*) FROM servicedesk.tickets WHERE DATE_TRUNC('month', "TKT-Created Time"::timestamp) = DATE_TRUNC('month', CURRENT_DATE))::NUMERIC * 100, 1) as actual_pct,
  c.target_percentage as target_pct
FROM servicedesk.tickets t
JOIN servicedesk.tier_cost_config c ON t.support_tier = c.tier
WHERE DATE_TRUNC('month', "TKT-Created Time"::timestamp) = DATE_TRUNC('month', CURRENT_DATE)
GROUP BY support_tier, c.target_percentage;
```

**Visualization**: 3 gauge panels (L1, L2, L3)
**Max Value**: 100%
**Target Line**: Pulled from tier_cost_config

---

### Panel 7: Tickets by Tier (Grouped Bar Chart)
**Query**:
```sql
SELECT
  DATE_TRUNC('month', "TKT-Created Time"::timestamp) as month,
  support_tier,
  COUNT(*) as ticket_count
FROM servicedesk.tickets
WHERE "TKT-Created Time"::timestamp >= CURRENT_DATE - INTERVAL '6 months'
GROUP BY DATE_TRUNC('month', "TKT-Created Time"::timestamp), support_tier
ORDER BY month, support_tier;
```

**Visualization**: Grouped bar chart (bars side-by-side)

---

### Panel 8: Month-over-Month Change (Table)
**Query**:
```sql
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
  TO_CHAR(month, 'YYYY-MM') as month,
  MAX(CASE WHEN support_tier = 'L1' THEN pct - LAG(pct) OVER (PARTITION BY support_tier ORDER BY month) END) as "L1 Δ",
  MAX(CASE WHEN support_tier = 'L2' THEN pct - LAG(pct) OVER (PARTITION BY support_tier ORDER BY month) END) as "L2 Δ",
  MAX(CASE WHEN support_tier = 'L3' THEN pct - LAG(pct) OVER (PARTITION BY support_tier ORDER BY month) END) as "L3 Δ"
FROM monthly_pct
GROUP BY month
ORDER BY month DESC;
```

**Visualization**: Table with color-coded cells

---

### Panel 9: L1 by Category (Pie Chart)
**Query**:
```sql
SELECT
  "TKT-Category" as category,
  COUNT(*) as count
FROM servicedesk.tickets
WHERE support_tier = 'L1'
  AND DATE_TRUNC('month', "TKT-Created Time"::timestamp) = DATE_TRUNC('month', CURRENT_DATE)
GROUP BY "TKT-Category"
ORDER BY count DESC
LIMIT 10;
```

**Visualization**: Pie chart (top 10 categories)

---

### Panel 10: L2 by Category (Pie Chart)
**Query**: Similar to Panel 9, filter for L2

---

### Panel 11: L1 Rate by Pod (Bar Chart) ⭐ NEW
**Query**:
```sql
SELECT
  assigned_pod as pod,
  ROUND(COUNT(*) FILTER (WHERE support_tier = 'L1')::NUMERIC / COUNT(*)::NUMERIC * 100, 1) as l1_rate
FROM servicedesk.tickets
WHERE assigned_pod IS NOT NULL
  AND DATE_TRUNC('month', "TKT-Created Time"::timestamp) = DATE_TRUNC('month', CURRENT_DATE)
GROUP BY assigned_pod
ORDER BY l1_rate DESC;
```

**Visualization**: Horizontal bar chart
**Thresholds**: Green ≥60%, Yellow 50-60%, Red <50%
**Target Line**: Vertical line at 60%

---

## ✅ **7. ACCEPTANCE CRITERIA SUMMARY**

### Phase 1 Complete When:
- [ ] This requirements document reviewed and approved by user
- [ ] All functional requirements (FR-1 through FR-6) understood
- [ ] All non-functional requirements (NFR-1 through NFR-5) understood
- [ ] Database schema requirements (6 schema changes) understood
- [ ] Data processing requirements (DP-1 through DP-4) understood
- [ ] Dashboard panel specifications (11 panels) understood
- [ ] User says "requirements complete"

### Phase 2-7 Complete When:
- [ ] All tests passing (100% coverage)
- [ ] All 11 panels rendering with real data
- [ ] Performance SLOs met (<100ms queries, <2s dashboard load)
- [ ] Alerting operational (dashboard notifications)
- [ ] Automation running (cron jobs for snapshot + validation)
- [ ] Documentation updated (ARCHITECTURE.md, ADR-003, runbook)
- [ ] Production readiness checklist signed off by SRE Agent
- [ ] User acceptance testing passed

---

## 🚨 **8. SRE QUALITY GATES** (Zero Technical Debt)

### Gate 1: Requirements Completeness
- [ ] User confirms: "Requirements complete, proceed to testing"
- [ ] No ambiguous requirements remain
- [ ] Edge cases identified and documented
- [ ] Success criteria measurable

### Gate 2: Test Coverage
- [ ] 100% coverage for database operations
- [ ] All edge cases have tests
- [ ] Performance tests included (<100ms queries)
- [ ] Failure mode tests included (connection errors, rollbacks)

### Gate 3: Implementation Quality
- [ ] No hardcoded costs (tier_cost_config table used)
- [ ] No hardcoded credentials (.env file)
- [ ] Transaction-safe database operations
- [ ] Batch optimizations applied (backfill <5 min)

### Gate 4: Observability
- [ ] Structured logging for all database ops
- [ ] Metrics instrumented (query latency, error rate)
- [ ] Alerts configured (tier thresholds, data validation)

### Gate 5: Documentation
- [ ] ARCHITECTURE.md updated
- [ ] ADR-003 created (design decisions)
- [ ] Operational runbook complete (TIER_DASHBOARD_OPERATIONS.md)
- [ ] active_deployments.md updated

---

## 📝 **9. OPEN QUESTIONS FOR USER** ⚠️ REQUIRES ANSWERS

### Question 1: Pod Assignment Process ✅ ANSWERED
**Context**: Panel 11 tracks L1 rates by pod, requires assigned_pod column

**User Answer**:
- **Current Process**: Manual assignment, mostly L1 triage → L2, occasionally direct to infrastructure pod
- **Future Plan**: AI-based routing by complexity (not yet implemented)
- **Pod Structure**: Currently forming, single large infrastructure support pod exists

**Implementation Decision**:
- `assigned_pod` column: NULL for now (historical + current tickets)
- Panel 11: Shows "No data" initially (filters WHERE assigned_pod IS NOT NULL)
- When pods operational: Manual UPDATE or import script populates assigned_pod
- Schema ready for future AI routing

---

### Question 2: Tier Categorization Accuracy ✅ ANSWERED
**Context**: Backfill uses categorize_tickets_by_tier.py logic

**User Answer**: NOT tested yet

**Implementation Decision - Phased Validation Approach**:
1. **Phase 3 (Backfill)**: Run on sample (100 tickets), manual accuracy review
2. **Accuracy Threshold**: If <90% accurate, refine logic and re-backfill
3. **If ≥90%**: Proceed with full backfill (10,939 tickets)
4. **Post-Backfill**: User spot-checks 20-30 tickets, confirms acceptable
5. **TDD Test**: `test_backfill_categorizes_correctly()` validates sample tickets
6. **Edge Cases**: Default ambiguous tickets → L2 (safer overestimate)

---

### Question 3: Snapshot Frequency ✅ ANSWERED
**Context**: Weekly snapshots for trend tracking

**User Answer**: **Option B - Weekly snapshots**

**Implementation Decision**:
- **Frequency**: Weekly (every Sunday at 00:00)
- **Granularity**: Tier-only (no category breakdown)
- **Storage**: 52 snapshots/year × 3 tiers = 156 rows/year (acceptable)
- **Dashboard**: 52 data points over 12 months (operational tracking)
- **Cron Schedule**: `0 0 * * 0 /usr/bin/python3 /path/to/capture_tier_snapshot.py`
- **Benefits**: See week-to-week optimization progress, identify short-term trends, track training/initiative impact
- **Upgrade Path**: Can aggregate to monthly view if chart too noisy (GROUP BY month in queries)

---

### Question 4: Alert Escalation ✅ ANSWERED
**Context**: Dashboard-only alerts for Phase 1

**User Answer**: Later, may use another mechanism (not email/Slack)

**Implementation Decision**:
- **Phase 1**: Dashboard-only alerts (Grafana UI bell icon)
- **Future**: Different notification mechanism (TBD by user)
- **Documentation**: Note in runbook that external notifications deferred
- **Extension Ready**: Grafana notification channels can be added later (15 min effort)
- **No Build**: Skip notification channel setup entirely

---

## ✅ **USER CONFIRMATION REQUIRED**

**Please review this requirements document and confirm**:

1. **Functional Requirements (FR-1 to FR-6)**: Accurate? Missing anything?
2. **Non-Functional Requirements (NFR-1 to NFR-5)**: Performance, reliability, security acceptable?
3. **Database Schema (6 changes)**: Correct approach? Concerns about schema modifications?
4. **Dashboard Panels (11 panels)**: Right visualizations? Preferred chart types?
5. **Open Questions (4 questions)**: Answers needed for pod assignment, categorization, snapshots, alerts

**Once you confirm "requirements complete"**, we proceed to:
- **Phase 2**: Test Design (create test_tier_tracker.py with all tests failing)
- **Phase 3-7**: Implementation → Dashboard → Alerts → Automation → Documentation

---

**Status**: ✅ REQUIREMENTS COMPLETE - USER CONFIRMED
**Decisions Finalized**:
1. ✅ Pod assignment: Manual (NULL for now), schema ready for future AI routing
2. ✅ Categorization: Phased validation (sample → full backfill with accuracy checks)
3. ✅ Snapshot frequency: **Weekly** (52 data points/year, operational tracking)
4. ✅ Alert escalation: Dashboard-only, external notifications deferred

**Next Step**: Phase 2 - Test Design (create comprehensive test suite)
**Conversation Recovery**: This file persists requirements across laptop restarts
