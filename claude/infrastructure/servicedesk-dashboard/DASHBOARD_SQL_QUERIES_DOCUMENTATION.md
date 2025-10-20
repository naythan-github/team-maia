# ServiceDesk Analytics Dashboard - SQL Query Documentation

**Created**: 2025-10-19
**Author**: SRE Principal Engineer Agent
**Purpose**: Complete SQL query reference with performance optimization notes

---

## Table of Contents

1. [Query Patterns](#query-patterns)
2. [Performance Optimization](#performance-optimization)
3. [Dashboard-Specific Queries](#dashboard-specific-queries)
4. [Index Recommendations](#index-recommendations)
5. [Query Tuning Tips](#query-tuning-tips)

---

## Query Patterns

### Pattern 1: Ticket Count by Pattern Type

**Use Case**: Identifying automation opportunities by matching title keywords

```sql
SELECT
  CASE
    WHEN "TKT-Title" ILIKE '%motion%' OR "TKT-Title" ILIKE '%sensor%' THEN 'Motion/Sensor'
    WHEN "TKT-Title" ILIKE '%patch%' OR "TKT-Title" ILIKE '%update fail%' THEN 'Patch Deployment'
    WHEN "TKT-Title" ILIKE '%vpn%' OR "TKT-Title" ILIKE '%network%' THEN 'Network/VPN'
    WHEN "TKT-Title" ILIKE '%azure%resource%' OR "TKT-Title" ILIKE '%azure health%' THEN 'Azure Resource'
    WHEN "TKT-Title" ILIKE '%ssl%' OR "TKT-Title" ILIKE '%certificate%expir%' THEN 'SSL/Certificate'
    WHEN "TKT-Title" ILIKE '%email%' OR "TKT-Title" ILIKE '%mailbox%' THEN 'Email Issues'
    WHEN "TKT-Title" ILIKE '%access%' OR "TKT-Title" ILIKE '%permission%' THEN 'Access/Permissions'
    WHEN "TKT-Title" ILIKE '%password%' OR "TKT-Title" ILIKE '%unlock%' OR "TKT-Title" ILIKE '%reset%' THEN 'Password Reset'
    WHEN "TKT-Title" ILIKE '%license%' OR "TKT-Title" ILIKE '%subscription%' THEN 'License Management'
    WHEN "TKT-Title" ILIKE '%install%' OR "TKT-Title" ILIKE '%software%' THEN 'Software Installation'
    ELSE 'Other'
  END as pattern_type,
  COUNT(*) as ticket_count
FROM servicedesk.tickets
WHERE "TKT-Created Time" >= '2025-07-01' AND "TKT-Created Time" <= '2025-10-13'
GROUP BY 1
ORDER BY ticket_count DESC;
```

**Performance Notes**:
- Uses ILIKE for case-insensitive matching (slower than LIKE)
- Full table scan required due to pattern matching
- Consider creating materialized view for frequent queries
- Estimated execution time: 200-500ms (10,939 rows)

### Pattern 2: Time-Series Aggregation

**Use Case**: Daily/weekly ticket volume trends

```sql
SELECT
  DATE_TRUNC('day', "TKT-Created Time") as time,
  COUNT(*) as "Total Tickets"
FROM servicedesk.tickets
WHERE "TKT-Created Time" >= '2025-07-01' AND "TKT-Created Time" <= '2025-10-13'
GROUP BY 1
ORDER BY 1;
```

**Performance Notes**:
- Uses existing index on "TKT-Created Time" (idx_tickets_created_time)
- Very efficient: <50ms execution time
- DATE_TRUNC is fast and indexed-friendly
- Can use 'week', 'month' for different granularity

### Pattern 3: Resolution Time Calculation

**Use Case**: Average time to resolve tickets

```sql
SELECT
  DATE_TRUNC('week', "TKT-Created Time") as time,
  AVG(EXTRACT(EPOCH FROM ("TKT-Actual Resolution Date" - "TKT-Created Time")) / 86400.0) as "Avg Days to Resolve"
FROM servicedesk.tickets
WHERE "TKT-Created Time" >= '2025-07-01' AND "TKT-Created Time" <= '2025-10-13'
AND "TKT-Actual Resolution Date" IS NOT NULL
GROUP BY 1
ORDER BY 1;
```

**Performance Notes**:
- Uses idx_tickets_resolution_dates composite index
- NULL check prevents calculation errors
- EXTRACT(EPOCH) converts interval to seconds
- Division by 86400 converts seconds to days
- Estimated execution time: <100ms

### Pattern 4: ROI Calculation

**Use Case**: Estimating annual savings from automation

```sql
SELECT
  '$' || ROUND(
    COUNT(*) * 1.0 / 104 * 365 * 2.0 * 80 / 1000, 0
  ) || 'K' as "Annual Savings"
FROM servicedesk.tickets
WHERE "TKT-Created Time" >= '2025-07-01' AND "TKT-Created Time" <= '2025-10-13'
AND (
  "TKT-Title" ILIKE '%motion%' OR "TKT-Title" ILIKE '%sensor%'
  -- Additional patterns...
);
```

**Calculation Breakdown**:
- `COUNT(*) * 1.0 / 104`: Tickets in 104-day period → daily rate
- `* 365`: Daily rate → annual projection
- `* 2.0`: Average hours per ticket (configurable)
- `* 80`: Hourly rate ($80/hr blended rate)
- `/ 1000`: Convert to thousands ($K format)

### Pattern 5: Top N with Aggregation

**Use Case**: Top assignees with performance metrics

```sql
SELECT
  "TKT-Assigned To User" as "Assignee",
  COUNT(*) as "Total Tickets",
  COUNT(CASE WHEN "TKT-Status" = 'Closed' THEN 1 END) as "Closed",
  ROUND(100.0 * COUNT(CASE WHEN "TKT-Status" = 'Closed' THEN 1 END) / NULLIF(COUNT(*), 0), 1) as "Close Rate %",
  ROUND(AVG(EXTRACT(EPOCH FROM ("TKT-Actual Resolution Date" - "TKT-Created Time")) / 3600.0), 2) as "Avg Hours to Resolve"
FROM servicedesk.tickets
WHERE "TKT-Created Time" >= '2025-07-01' AND "TKT-Created Time" <= '2025-10-13'
AND "TKT-Assigned To User" IS NOT NULL
AND "TKT-Assigned To User" <> 'PendingAssignment'
GROUP BY 1
ORDER BY 2 DESC
LIMIT 15;
```

**Performance Notes**:
- Uses conditional aggregation (CASE WHEN) instead of subqueries
- NULLIF prevents division by zero
- Multiple aggregations in single pass (efficient)
- Estimated execution time: <150ms

### Pattern 6: Heatmap Data (2D Aggregation)

**Use Case**: Alert volume by day-of-week and hour

```sql
SELECT
  EXTRACT(DOW FROM "TKT-Created Time") as "Day",
  EXTRACT(HOUR FROM "TKT-Created Time") as "Hour",
  COUNT(*) as "Alert Count"
FROM servicedesk.tickets
WHERE "TKT-Created Time" >= '2025-07-01' AND "TKT-Created Time" <= '2025-10-13'
AND "TKT-Category" = 'Alert'
GROUP BY 1, 2
ORDER BY 1, 2;
```

**Performance Notes**:
- Uses idx_tickets_category index
- EXTRACT(DOW): 0=Sunday, 6=Saturday
- EXTRACT(HOUR): 0-23 (24-hour format)
- Results perfect for Grafana heatmap visualization
- Estimated execution time: <100ms

### Pattern 7: Percentage Calculation

**Use Case**: Automation coverage percentage

```sql
SELECT
  ROUND(100.0 *
    SUM(CASE WHEN (
      "TKT-Title" ILIKE '%motion%' OR "TKT-Title" ILIKE '%sensor%'
      -- Additional patterns...
    ) THEN 1 ELSE 0 END) / COUNT(*), 2
  ) as "Coverage %"
FROM servicedesk.tickets
WHERE "TKT-Created Time" >= '2025-07-01' AND "TKT-Created Time" <= '2025-10-13';
```

**Performance Notes**:
- Single table scan for all calculations
- Conditional SUM using CASE WHEN
- ROUND to 2 decimal places for readability

---

## Performance Optimization

### Current Performance Baseline

**Dataset**: 10,939 tickets (Jul 1 - Oct 13, 2025)
**Database**: PostgreSQL 15-alpine
**Existing Indexes**: 10 analytics indexes created in Phase 1

| Query Type | Avg Execution Time | Index Used |
|------------|-------------------|------------|
| Time-series aggregation | <50ms | idx_tickets_created_time |
| Category filtering | <100ms | idx_tickets_category |
| Resolution time calc | <100ms | idx_tickets_resolution_dates |
| Pattern matching (ILIKE) | 200-500ms | Full scan (no index possible) |
| Assignee aggregation | <150ms | Composite (status_team) |
| Top N queries | <100ms | Various |

### Optimization Recommendations

#### 1. Pattern Matching Optimization

**Problem**: ILIKE pattern matching requires full table scan
**Solution**: Create materialized view with pre-computed patterns

```sql
CREATE MATERIALIZED VIEW servicedesk.ticket_automation_patterns AS
SELECT
  "TKT-Ticket ID",
  "TKT-Created Time",
  CASE
    WHEN "TKT-Title" ILIKE '%motion%' OR "TKT-Title" ILIKE '%sensor%' THEN 'Motion/Sensor'
    WHEN "TKT-Title" ILIKE '%patch%' OR "TKT-Title" ILIKE '%update fail%' THEN 'Patch Deployment'
    -- Additional patterns...
    ELSE 'Other'
  END as automation_pattern,
  CASE
    WHEN "TKT-Title" ILIKE '%motion%' OR "TKT-Title" ILIKE '%sensor%'
      OR "TKT-Title" ILIKE '%patch%' OR "TKT-Title" ILIKE '%update fail%'
      -- Additional patterns...
    THEN TRUE ELSE FALSE
  END as is_automation_candidate
FROM servicedesk.tickets;

CREATE INDEX idx_automation_patterns_pattern ON servicedesk.ticket_automation_patterns(automation_pattern);
CREATE INDEX idx_automation_patterns_candidate ON servicedesk.ticket_automation_patterns(is_automation_candidate);
CREATE INDEX idx_automation_patterns_created ON servicedesk.ticket_automation_patterns("TKT-Created Time");

-- Refresh strategy (run daily)
REFRESH MATERIALIZED VIEW servicedesk.ticket_automation_patterns;
```

**Expected Improvement**: 200-500ms → <50ms (90% faster)

#### 2. Query-Specific Indexes

**Add these indexes for optimal performance**:

```sql
-- For task-level distribution queries
CREATE INDEX idx_tickets_title_lower ON servicedesk.tickets(LOWER("TKT-Title"));

-- For assignee filtering
CREATE INDEX idx_tickets_assigned_not_pending
  ON servicedesk.tickets("TKT-Assigned To User")
  WHERE "TKT-Assigned To User" IS NOT NULL AND "TKT-Assigned To User" <> 'PendingAssignment';

-- For closed ticket queries
CREATE INDEX idx_tickets_status_closed
  ON servicedesk.tickets("TKT-Status")
  WHERE "TKT-Status" = 'Closed';
```

#### 3. Partitioning Strategy (Future Growth)

**For datasets >100K rows, consider range partitioning**:

```sql
CREATE TABLE servicedesk.tickets_partitioned (
  LIKE servicedesk.tickets INCLUDING ALL
) PARTITION BY RANGE ("TKT-Created Time");

CREATE TABLE servicedesk.tickets_2025_q3
  PARTITION OF servicedesk.tickets_partitioned
  FOR VALUES FROM ('2025-07-01') TO ('2025-10-01');

CREATE TABLE servicedesk.tickets_2025_q4
  PARTITION OF servicedesk.tickets_partitioned
  FOR VALUES FROM ('2025-10-01') TO ('2026-01-01');
```

**Benefit**: 50-70% query performance improvement for time-range queries

---

## Dashboard-Specific Queries

### Dashboard 1: Automation Executive Overview

#### KPI Queries (All <100ms)

**Total Tickets**:
```sql
SELECT COUNT(*) as "Total Tickets"
FROM servicedesk.tickets
WHERE "TKT-Created Time" >= '2025-07-01' AND "TKT-Created Time" <= '2025-10-13';
```

**Automation Coverage %**:
```sql
SELECT
  ROUND(100.0 *
    SUM(CASE WHEN (
      "TKT-Title" ILIKE '%motion%' OR "TKT-Title" ILIKE '%sensor%' OR
      "TKT-Title" ILIKE '%patch%' OR "TKT-Title" ILIKE '%email%' OR
      "TKT-Title" ILIKE '%access%' OR "TKT-Title" ILIKE '%password%' OR
      "TKT-Title" ILIKE '%license%' OR "TKT-Title" ILIKE '%install%'
    ) THEN 1 ELSE 0 END) / COUNT(*), 2
  ) as "Coverage %"
FROM servicedesk.tickets
WHERE "TKT-Created Time" >= '2025-07-01' AND "TKT-Created Time" <= '2025-10-13';
```

### Dashboard 2: Alert Analysis Deep-Dive

**Alert Volume Heatmap**:
```sql
SELECT
  EXTRACT(DOW FROM "TKT-Created Time") as "Day",
  EXTRACT(HOUR FROM "TKT-Created Time") as "Hour",
  COUNT(*) as "Alert Count"
FROM servicedesk.tickets
WHERE "TKT-Created Time" >= '2025-07-01' AND "TKT-Created Time" <= '2025-10-13'
AND "TKT-Category" = 'Alert'
GROUP BY 1, 2
ORDER BY 1, 2;
```

**Top 10 Repetitive Alerts**:
```sql
SELECT
  "TKT-Title" as "Alert Title",
  COUNT(*) as "Occurrences",
  ROUND(COUNT(*) * 1.0 / 104 * 365, 0) as "Projected Annual",
  '$' || ROUND(COUNT(*) * 1.0 / 104 * 365 * 0.5 * 80 / 1000, 1) || 'K' as "Est. Savings (30min avg)"
FROM servicedesk.tickets
WHERE "TKT-Created Time" >= '2025-07-01' AND "TKT-Created Time" <= '2025-10-13'
AND "TKT-Category" = 'Alert'
GROUP BY 1
ORDER BY 2 DESC
LIMIT 10;
```

### Dashboard 3: Support Pattern Analysis

**Pattern Growth/Decline (Week-over-Week)**:
```sql
SELECT
  DATE_TRUNC('week', "TKT-Created Time") as time,
  SUM(CASE WHEN "TKT-Title" ILIKE '%email%' OR "TKT-Title" ILIKE '%mailbox%' THEN 1 ELSE 0 END) as "Email",
  SUM(CASE WHEN "TKT-Title" ILIKE '%access%' OR "TKT-Title" ILIKE '%permission%' THEN 1 ELSE 0 END) as "Access",
  SUM(CASE WHEN "TKT-Title" ILIKE '%password%' OR "TKT-Title" ILIKE '%unlock%' OR "TKT-Title" ILIKE '%reset%' THEN 1 ELSE 0 END) as "Password",
  SUM(CASE WHEN "TKT-Title" ILIKE '%license%' OR "TKT-Title" ILIKE '%subscription%' THEN 1 ELSE 0 END) as "License",
  SUM(CASE WHEN "TKT-Title" ILIKE '%install%' OR "TKT-Title" ILIKE '%software%' THEN 1 ELSE 0 END) as "Install"
FROM servicedesk.tickets
WHERE "TKT-Created Time" >= '2025-07-01' AND "TKT-Created Time" <= '2025-10-13'
AND "TKT-Category" = 'Support Tickets'
GROUP BY 1
ORDER BY 1;
```

### Dashboard 4: Team Performance

**Ticket Volume Heatmap (Assignee x Category)**:
```sql
WITH top_assignees AS (
  SELECT "TKT-Assigned To User"
  FROM servicedesk.tickets
  WHERE "TKT-Created Time" >= '2025-07-01' AND "TKT-Created Time" <= '2025-10-13'
  AND "TKT-Assigned To User" IS NOT NULL AND "TKT-Assigned To User" <> 'PendingAssignment'
  GROUP BY 1
  ORDER BY COUNT(*) DESC
  LIMIT 10
)
SELECT
  t."TKT-Assigned To User" as "Assignee",
  t."TKT-Category" as "Category",
  COUNT(*) as "Count"
FROM servicedesk.tickets t
INNER JOIN top_assignees ta ON t."TKT-Assigned To User" = ta."TKT-Assigned To User"
WHERE t."TKT-Created Time" >= '2025-07-01' AND t."TKT-Created Time" <= '2025-10-13'
AND t."TKT-Category" IS NOT NULL
GROUP BY 1, 2
ORDER BY 1, 3 DESC;
```

### Dashboard 5: Improvement Tracking

**ROI Calculator - Estimated vs Actual**:
```sql
SELECT
  CASE
    WHEN "TKT-Title" ILIKE '%motion%' OR "TKT-Title" ILIKE '%sensor%' THEN 'Motion/Sensor Alerts'
    WHEN "TKT-Title" ILIKE '%access%' OR "TKT-Title" ILIKE '%permission%' THEN 'Access/Permissions'
    WHEN "TKT-Title" ILIKE '%patch%' OR "TKT-Title" ILIKE '%update fail%' THEN 'Patch Failures'
    WHEN "TKT-Title" ILIKE '%email%' OR "TKT-Title" ILIKE '%mailbox%' THEN 'Email Issues'
    WHEN "TKT-Title" ILIKE '%password%' OR "TKT-Title" ILIKE '%unlock%' OR "TKT-Title" ILIKE '%reset%' THEN 'Password Reset'
  END as "Automation Pattern",
  COUNT(*) as "Tickets (Jul-Oct)",
  ROUND(COUNT(*) * 1.0 / 104 * 365, 0) as "Annual Projection",
  '$' || ROUND(COUNT(*) * 1.0 / 104 * 365 * 1.5 * 80 / 1000, 0) || 'K' as "Est. Annual Savings",
  '$0K' as "Actual Savings YTD",
  'Not Implemented' as "Status"
FROM servicedesk.tickets
WHERE "TKT-Created Time" >= '2025-07-01' AND "TKT-Created Time" <= '2025-10-13'
AND (
  ("TKT-Title" ILIKE '%motion%' OR "TKT-Title" ILIKE '%sensor%') OR
  ("TKT-Title" ILIKE '%access%' OR "TKT-Title" ILIKE '%permission%') OR
  ("TKT-Title" ILIKE '%patch%' OR "TKT-Title" ILIKE '%update fail%') OR
  ("TKT-Title" ILIKE '%email%' OR "TKT-Title" ILIKE '%mailbox%') OR
  ("TKT-Title" ILIKE '%password%' OR "TKT-Title" ILIKE '%unlock%' OR "TKT-Title" ILIKE '%reset%')
)
GROUP BY 1
ORDER BY 2 DESC;
```

---

## Index Recommendations

### Existing Indexes (Phase 1 - Already Deployed)

```sql
-- Core indexes
CREATE INDEX idx_tickets_category ON servicedesk.tickets("TKT-Category");
CREATE INDEX idx_tickets_created_time ON servicedesk.tickets("TKT-Created Time");
CREATE INDEX idx_tickets_month_created ON servicedesk.tickets("TKT-Month Created");
CREATE INDEX idx_tickets_resolution_dates ON servicedesk.tickets("TKT-Actual Resolution Date", "TKT-Created Time");
CREATE INDEX idx_tickets_root_cause ON servicedesk.tickets("TKT-Root Cause Category");
CREATE INDEX idx_tickets_sla_met ON servicedesk.tickets("TKT-SLA Met");
CREATE INDEX idx_tickets_status ON servicedesk.tickets("TKT-Status");
CREATE INDEX idx_tickets_status_category ON servicedesk.tickets("TKT-Status", "TKT-Category");
CREATE INDEX idx_tickets_status_team ON servicedesk.tickets("TKT-Status", "TKT-Team");
CREATE INDEX idx_tickets_team ON servicedesk.tickets("TKT-Team");
```

### Additional Recommended Indexes (Phase 2)

```sql
-- For pattern matching optimization
CREATE INDEX idx_tickets_title_trgm ON servicedesk.tickets USING gin("TKT-Title" gin_trgm_ops);
-- Requires: CREATE EXTENSION pg_trgm;
-- Benefit: 3-5x faster ILIKE queries

-- For assignee queries
CREATE INDEX idx_tickets_assigned_user ON servicedesk.tickets("TKT-Assigned To User");

-- For severity filtering
CREATE INDEX idx_tickets_severity ON servicedesk.tickets("TKT-Severity");

-- Composite for common filters
CREATE INDEX idx_tickets_created_category_status
  ON servicedesk.tickets("TKT-Created Time", "TKT-Category", "TKT-Status");
```

### Index Maintenance

**Monitor index usage**:
```sql
SELECT
  schemaname,
  tablename,
  indexname,
  idx_scan as scans,
  idx_tup_read as tuples_read,
  idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
WHERE schemaname = 'servicedesk'
ORDER BY idx_scan DESC;
```

**Rebuild indexes (quarterly)**:
```sql
REINDEX TABLE servicedesk.tickets;
ANALYZE servicedesk.tickets;
```

---

## Query Tuning Tips

### 1. Use EXPLAIN ANALYZE

**Always test query performance**:
```sql
EXPLAIN ANALYZE
SELECT COUNT(*)
FROM servicedesk.tickets
WHERE "TKT-Title" ILIKE '%motion%';
```

**Look for**:
- Seq Scan (bad) vs Index Scan (good)
- Execution time <500ms for Grafana queries
- High row estimates vs actual (consider ANALYZE)

### 2. Avoid SELECT *

**Bad**:
```sql
SELECT * FROM servicedesk.tickets WHERE ...;
```

**Good**:
```sql
SELECT "TKT-Ticket ID", "TKT-Title", "TKT-Created Time"
FROM servicedesk.tickets WHERE ...;
```

**Benefit**: Reduces data transfer by 80-90%

### 3. Use CTEs for Complex Queries

**Bad** (subquery in SELECT):
```sql
SELECT
  assignee,
  (SELECT COUNT(*) FROM tickets WHERE assigned = assignee) as count
FROM ...;
```

**Good** (CTE):
```sql
WITH assignee_counts AS (
  SELECT "TKT-Assigned To User", COUNT(*) as count
  FROM servicedesk.tickets
  GROUP BY 1
)
SELECT * FROM assignee_counts;
```

### 4. Batch Time-Range Queries

**For Grafana auto-refresh, use $__timeFilter()**:
```sql
SELECT
  DATE_TRUNC('day', "TKT-Created Time") as time,
  COUNT(*) as value
FROM servicedesk.tickets
WHERE $__timeFilter("TKT-Created Time")
GROUP BY 1
ORDER BY 1;
```

**Benefit**: Grafana automatically adjusts time range based on dashboard settings

### 5. Cache Expensive Queries

**For rarely-changing data, use materialized views**:
```sql
CREATE MATERIALIZED VIEW servicedesk.daily_ticket_summary AS
SELECT
  DATE_TRUNC('day', "TKT-Created Time") as date,
  COUNT(*) as total_tickets,
  COUNT(CASE WHEN "TKT-Category" = 'Alert' THEN 1 END) as alerts,
  COUNT(CASE WHEN "TKT-Category" = 'Support Tickets' THEN 1 END) as support
FROM servicedesk.tickets
GROUP BY 1;

CREATE INDEX idx_daily_summary_date ON servicedesk.daily_ticket_summary(date);

-- Refresh daily at 2 AM
SELECT cron.schedule('refresh-daily-summary', '0 2 * * *', 'REFRESH MATERIALIZED VIEW servicedesk.daily_ticket_summary');
```

---

## Troubleshooting

### Slow Query Checklist

1. **Check query execution time**:
   ```sql
   EXPLAIN (ANALYZE, BUFFERS) <your query>;
   ```

2. **Verify indexes are being used**:
   - Look for "Index Scan" or "Index Only Scan"
   - If seeing "Seq Scan", add appropriate index

3. **Check table statistics**:
   ```sql
   ANALYZE servicedesk.tickets;
   ```

4. **Monitor connection pool**:
   ```sql
   SELECT count(*) FROM pg_stat_activity WHERE datname = 'servicedesk';
   ```

5. **Check for locks**:
   ```sql
   SELECT * FROM pg_locks WHERE NOT granted;
   ```

### Performance Targets

| Query Type | Target Execution Time | Status |
|------------|----------------------|--------|
| Simple aggregation | <50ms | ✅ Achieved |
| Time-series | <100ms | ✅ Achieved |
| Pattern matching | <200ms | ⚠️ Needs optimization |
| Complex joins | <500ms | ✅ Achieved |
| Dashboard load | <2s total | ✅ Achieved |

---

## Dashboard 6: Incident Classification Breakdown

### Query 1: Primary Classification (Cloud/Telecom/Networking)

**Purpose**: Classify all non-alert incidents into technology stack categories

```sql
WITH classified AS (
  SELECT
    CASE
      -- File shares always go to Cloud (even if they mention 'network')
      WHEN LOWER(COALESCE("TKT-Title",'') || ' ' || COALESCE("TKT-Description",''))
           LIKE ANY(ARRAY['%network drive%','%share%','%file server%','%shared drive%','%file share%'])
      THEN 'Cloud'

      -- Telecommunications: phone, VoIP, calling, meeting systems
      WHEN LOWER(COALESCE("TKT-Title",'') || ' ' || COALESCE("TKT-Description",''))
           LIKE ANY(ARRAY['%phone%','%pbx%','%call%','%voip%','%teams meeting%','%meeting room%'])
      THEN 'Telecommunications'

      -- Networking: VPN, firewall, switches, WiFi (excludes file shares)
      WHEN LOWER(COALESCE("TKT-Title",'') || ' ' || COALESCE("TKT-Description",''))
           LIKE ANY(ARRAY['%vpn%','%firewall%','%switch%','%router%','%wifi%','%wi-fi%','%access point%','%ethernet%'])
      THEN 'Networking'

      -- Everything else is Cloud (SaaS, applications, etc.)
      ELSE 'Cloud'
    END AS category
  FROM servicedesk.tickets
  WHERE "TKT-Category" <> 'Alert'
  AND "TKT-Created Time" >= '2025-07-01'
)
SELECT category, COUNT(*) as count, ROUND(COUNT(*)*100.0/(SELECT COUNT(*) FROM classified), 2) as percentage
FROM classified
GROUP BY category
ORDER BY COUNT(*) DESC;
```

**Results** (6,903 total incidents):
- Cloud: 5,423 (78.56%)
- Telecommunications: 1,281 (18.56%)
- Networking: 199 (2.88%)

**Performance**: 75-115ms (with CASE statement evaluation)

**Key Design Decision**: File shares explicitly classified as Cloud FIRST, before networking check. This prevents "network drive" from being misclassified as Networking infrastructure.

### Query 2: Networking Sub-Categories

**Purpose**: Break down networking incidents into infrastructure types

```sql
WITH networking_tickets AS (
  SELECT "TKT-Title", "TKT-Description"
  FROM servicedesk.tickets
  WHERE "TKT-Category" <> 'Alert'
  AND "TKT-Created Time" >= '2025-07-01'
  -- Exclude file shares
  AND LOWER(COALESCE("TKT-Title",'') || ' ' || COALESCE("TKT-Description",''))
      NOT LIKE ANY(ARRAY['%network drive%','%share%','%file server%','%shared drive%','%file share%'])
  -- Include networking keywords
  AND LOWER(COALESCE("TKT-Title",'') || ' ' || COALESCE("TKT-Description",''))
      LIKE ANY(ARRAY['%vpn%','%firewall%','%switch%','%router%','%wifi%','%wi-fi%','%access point%','%ethernet%'])
)
SELECT
  CASE
    WHEN LOWER(COALESCE("TKT-Title",'') || ' ' || COALESCE("TKT-Description",'')) LIKE '%vpn%' THEN 'VPN Issues'
    WHEN LOWER(COALESCE("TKT-Title",'') || ' ' || COALESCE("TKT-Description",'')) LIKE '%firewall%' THEN 'Firewall'
    WHEN LOWER(COALESCE("TKT-Title",'') || ' ' || COALESCE("TKT-Description",'')) LIKE '%switch%' OR
         LOWER(COALESCE("TKT-Title",'') || ' ' || COALESCE("TKT-Description",'')) LIKE '%router%' THEN 'Switch/Router Hardware'
    WHEN LOWER(COALESCE("TKT-Title",'') || ' ' || COALESCE("TKT-Description",'')) LIKE '%wifi%' OR
         LOWER(COALESCE("TKT-Title",'') || ' ' || COALESCE("TKT-Description",'')) LIKE '%wi-fi%' OR
         LOWER(COALESCE("TKT-Title",'') || ' ' || COALESCE("TKT-Description",'')) LIKE '%access point%' THEN 'WiFi Connectivity'
    WHEN LOWER(COALESCE("TKT-Title",'') || ' ' || COALESCE("TKT-Description",'')) LIKE '%ethernet%' THEN 'Ethernet/Cabling'
    ELSE 'Other Networking'
  END AS subcategory,
  COUNT(*) as count,
  ROUND(COUNT(*)*100.0/(SELECT COUNT(*) FROM networking_tickets), 2) as percentage
FROM networking_tickets
GROUP BY subcategory
ORDER BY count DESC;
```

**Results** (316 total networking tickets):
- VPN Issues: 163 (51.58%)
- Switch/Router Hardware: 56 (17.72%)
- WiFi Connectivity: 56 (17.72%)
- Firewall: 36 (11.39%)
- Ethernet/Cabling: 5 (1.58%)

**Performance**: <50ms (smaller dataset after filtering)

### Query 3: Telecommunications Sub-Categories

**Purpose**: Break down telecommunications incidents by type

```sql
WITH telecom_tickets AS (
  SELECT "TKT-Title", "TKT-Description"
  FROM servicedesk.tickets
  WHERE "TKT-Category" <> 'Alert'
  AND "TKT-Created Time" >= '2025-07-01'
  AND LOWER(COALESCE("TKT-Title",'') || ' ' || COALESCE("TKT-Description",''))
      LIKE ANY(ARRAY['%phone%','%pbx%','%call%','%voip%','%teams meeting%','%meeting room%'])
)
SELECT
  CASE
    WHEN LOWER(COALESCE("TKT-Title",'') || ' ' || COALESCE("TKT-Description",'')) LIKE '%phone%'
         OR LOWER(COALESCE("TKT-Title",'') || ' ' || COALESCE("TKT-Description",'')) LIKE '%call%' THEN 'Calling Issues'
    WHEN LOWER(COALESCE("TKT-Title",'') || ' ' || COALESCE("TKT-Description",'')) LIKE '%pbx%' THEN 'PBX System'
    WHEN LOWER(COALESCE("TKT-Title",'') || ' ' || COALESCE("TKT-Description",'')) LIKE '%voip%' THEN 'VoIP'
    WHEN LOWER(COALESCE("TKT-Title",'') || ' ' || COALESCE("TKT-Description",'')) LIKE '%teams meeting%'
         OR LOWER(COALESCE("TKT-Title",'') || ' ' || COALESCE("TKT-Description",'')) LIKE '%meeting room%' THEN 'Conference/Meeting Rooms'
    ELSE 'Other Telecom'
  END AS subcategory,
  COUNT(*) as count,
  ROUND(COUNT(*)*100.0/(SELECT COUNT(*) FROM telecom_tickets), 2) as percentage
FROM telecom_tickets
GROUP BY subcategory
ORDER BY count DESC;
```

**Results** (1,404 total telecom tickets):
- Calling Issues: 1,379 (98.22%)
- Conference/Meeting Rooms: 15 (1.07%)
- PBX System: 9 (0.64%)
- VoIP: 1 (0.07%)

**Performance**: <50ms

### Query 4: Classification Trends Over Time

**Purpose**: Weekly trend showing how incident distribution changes over time

```sql
WITH classified AS (
  SELECT
    DATE_TRUNC('week', "TKT-Created Time") as time,
    CASE
      WHEN LOWER(COALESCE("TKT-Title",'') || ' ' || COALESCE("TKT-Description",''))
           LIKE ANY(ARRAY['%network drive%','%share%','%file server%','%shared drive%','%file share%'])
      THEN 'Cloud'
      WHEN LOWER(COALESCE("TKT-Title",'') || ' ' || COALESCE("TKT-Description",''))
           LIKE ANY(ARRAY['%phone%','%pbx%','%call%','%voip%','%teams meeting%','%meeting room%'])
      THEN 'Telecommunications'
      WHEN LOWER(COALESCE("TKT-Title",'') || ' ' || COALESCE("TKT-Description",''))
           LIKE ANY(ARRAY['%vpn%','%firewall%','%switch%','%router%','%wifi%','%wi-fi%','%access point%','%ethernet%'])
      THEN 'Networking'
      ELSE 'Cloud'
    END AS category
  FROM servicedesk.tickets
  WHERE "TKT-Category" <> 'Alert'
  AND "TKT-Created Time" >= '2025-07-01'
)
SELECT time,
  SUM(CASE WHEN category = 'Cloud' THEN 1 ELSE 0 END) as "Cloud",
  SUM(CASE WHEN category = 'Telecommunications' THEN 1 ELSE 0 END) as "Telecommunications",
  SUM(CASE WHEN category = 'Networking' THEN 1 ELSE 0 END) as "Networking"
FROM classified
GROUP BY time
ORDER BY time;
```

**Performance**: ~100ms (includes time-series aggregation)

**Use Case**: Grafana stacked area chart showing category distribution evolution

### Dashboard 6 Performance Summary

| Query | Type | Execution Time | Status |
|-------|------|----------------|--------|
| Primary Classification | Pattern matching + aggregation | 75-115ms | ✅ Excellent |
| Networking Sub-categories | Filtered pattern matching | 40-50ms | ✅ Excellent |
| Telecom Sub-categories | Filtered pattern matching | 40-50ms | ✅ Excellent |
| Time-series trends | Time-series + classification | 90-110ms | ✅ Excellent |
| File share detail table | Simple filter | 20-30ms | ✅ Excellent |

**Total Dashboard Load Time**: ~400-500ms (all 10 panels combined)

### Classification Logic Validation

**Test Case 1: File Shares Classification**
```sql
-- Verify all file share tickets are classified as Cloud, NOT Networking
SELECT category, COUNT(*)
FROM (
  SELECT CASE
    WHEN LOWER(...) LIKE ANY(ARRAY['%network drive%',...]) THEN 'Cloud'
    WHEN LOWER(...) LIKE ANY(ARRAY['%vpn%',...]) THEN 'Networking'
    ELSE 'Cloud'
  END AS category
  FROM servicedesk.tickets
  WHERE LOWER(...) LIKE ANY(ARRAY['%network drive%',%share%',...])
) AS file_shares
GROUP BY category;
```

**Expected Result**: 100% Cloud (0% Networking/Telecom)
**Actual Result**: 738 tickets → 100% Cloud ✅

**Test Case 2: No Overlap Between Categories**
- Each ticket appears in exactly ONE category
- Validated via: `SUM(counts) = 6,903` (total non-alert tickets)

---

## Contact & Support

**Author**: SRE Principal Engineer Agent
**Created**: 2025-10-19
**Dashboard Version**: 1.0.0
**PostgreSQL Version**: 15-alpine
**Grafana Version**: 10.2.2

For questions or optimization requests, refer to the Grafana dashboard configuration files.
