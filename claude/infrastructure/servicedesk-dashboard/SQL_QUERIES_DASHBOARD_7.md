# Dashboard #7 - SQL Query Reference
## Customer Sentiment & Team Performance Analysis

This document contains all SQL queries used in Dashboard #7 for reference and debugging.

---

## Panel 1: Total Customer-Facing Comments

**Type**: Stat Panel
**Description**: Total count of customer-facing comments since July 2025

```sql
SELECT COUNT(*) as value
FROM servicedesk.comments
WHERE visible_to_customer = 'Yes'
AND created_time >= '2025-07-01';
```

**Expected Output**: Single value (16,620)

---

## Panel 2: Positive Sentiment Rate

**Type**: Stat Panel
**Description**: Percentage of comments containing positive keywords

```sql
SELECT
  CAST(SUM(CASE WHEN LOWER(comment_text) ~ '.*(thank|great|excellent|happy|appreciate|wonderful|fantastic|perfect|amazing).*' THEN 1 ELSE 0 END)*100.0/COUNT(*) AS NUMERIC(10,1)) as value
FROM servicedesk.comments
WHERE visible_to_customer = 'Yes'
AND created_time >= '2025-07-01';
```

**Expected Output**: Single percentage value (50.6%)

**Positive Keywords**:
- thank, great, excellent, happy, appreciate
- wonderful, fantastic, perfect, amazing

---

## Panel 3: Average Team SLA Compliance

**Type**: Stat Panel
**Description**: Overall SLA compliance rate across all team members

```sql
SELECT
  CAST(SUM(CASE WHEN "TKT-SLA Met" = 'yes' THEN 1 ELSE 0 END)*100.0/COUNT(*) AS NUMERIC(10,1)) as value
FROM servicedesk.tickets
WHERE "TKT-Created Time" >= '2025-07-01'
AND "TKT-SLA Met" IS NOT NULL
AND "TKT-Assigned To User" NOT LIKE ' %';
```

**Expected Output**: Single percentage value (98.6%)

**Filter**: Excludes system/placeholder assignees (names starting with space)

---

## Panel 4: Average Comment Quality Score

**Type**: Stat Panel
**Description**: Average quality score from analyzed comments (1-3 scale)

```sql
SELECT
  CAST(AVG(quality_score) AS NUMERIC(10,2)) as value
FROM servicedesk.comment_quality
WHERE created_time >= '2025-07-01';
```

**Expected Output**: Single value (1.77)

**Note**: Limited sample size (517 analyzed comments)

---

## Panel 5: Ranked Team Performance (Composite Score)

**Type**: Table Panel
**Description**: Team members ranked by composite score (SLA + Speed + Sentiment)

```sql
WITH assignee_metrics AS (
  SELECT
    t."TKT-Assigned To User" as assignee,
    COUNT(DISTINCT t."TKT-Ticket ID") as total_tickets,
    SUM(CASE WHEN t."TKT-SLA Met" = 'yes' THEN 1 ELSE 0 END)*100.0/COUNT(*) as sla_pct,
    AVG(EXTRACT(EPOCH FROM (t."TKT-Actual Resolution Date" - t."TKT-Created Time"))/3600) as avg_resolution_hours
  FROM servicedesk.tickets t
  WHERE t."TKT-Created Time" >= '2025-07-01'
  AND t."TKT-Assigned To User" IS NOT NULL
  AND t."TKT-SLA Met" IS NOT NULL
  GROUP BY t."TKT-Assigned To User"
  HAVING COUNT(*) >= 20
),
assignee_sentiment AS (
  SELECT
    t."TKT-Assigned To User" as assignee,
    SUM(CASE WHEN LOWER(c.comment_text) ~ '.*(thank|great|excellent|happy|appreciate|wonderful|fantastic|perfect|amazing).*' THEN 1 ELSE 0 END) as positive,
    SUM(CASE WHEN LOWER(c.comment_text) ~ '.*(issue|problem|unhappy|frustrated|angry|disappointed|urgent|critical|error|fail).*' THEN 1 ELSE 0 END) as negative,
    COUNT(*) as total_comments
  FROM servicedesk.tickets t
  INNER JOIN servicedesk.comments c ON t."TKT-Ticket ID" = c.ticket_id
  WHERE t."TKT-Created Time" >= '2025-07-01'
  AND t."TKT-Assigned To User" IS NOT NULL
  AND c.visible_to_customer = 'Yes'
  GROUP BY t."TKT-Assigned To User"
),
scored AS (
  SELECT
    am.assignee,
    am.total_tickets,
    CAST(am.sla_pct AS NUMERIC(10,1)) as sla_percentage,
    CAST(am.avg_resolution_hours AS NUMERIC(10,1)) as avg_hours,
    COALESCE(asent.positive, 0) as positive_comments,
    COALESCE(asent.negative, 0) as negative_comments,
    COALESCE(asent.total_comments, 0) as total_comments,
    CAST(
      (am.sla_pct * 0.3) +
      ((100 - LEAST(am.avg_resolution_hours, 100)) * 0.3) +
      (CASE
        WHEN COALESCE(asent.total_comments, 0) > 0
        THEN ((COALESCE(asent.positive, 0) - COALESCE(asent.negative, 0))*100.0/asent.total_comments * 0.4)
        ELSE 0
      END)
    AS NUMERIC(10,2)) as composite_score
  FROM assignee_metrics am
  LEFT JOIN assignee_sentiment asent ON am.assignee = asent.assignee
  WHERE am.assignee NOT LIKE ' %'
)
SELECT
  ROW_NUMBER() OVER (ORDER BY composite_score DESC) as "Rank",
  assignee as "Team Member",
  CAST(composite_score AS NUMERIC(10,1)) as "Score",
  sla_percentage as "SLA %",
  avg_hours as "Avg Resolution (hrs)",
  total_tickets as "Tickets",
  positive_comments as "Positive",
  negative_comments as "Negative",
  total_comments as "Total Comments"
FROM scored
ORDER BY composite_score DESC
LIMIT 20;
```

**Expected Output**: 20 rows with columns: Rank, Team Member, Score, SLA %, Avg Resolution, Tickets, Positive, Negative, Total Comments

**Composite Score Formula**:
```
composite_score = (sla_pct * 0.3) +                              # 30% weight on SLA compliance
                  ((100 - LEAST(avg_hours, 100)) * 0.3) +        # 30% weight on speed (inverted)
                  ((positive - negative) / total * 100 * 0.4)    # 40% weight on sentiment
```

**Filters**:
- Minimum 20 tickets per assignee
- Excludes system/placeholder assignees

---

## Panel 6: Positive vs Negative Comments Bar Chart

**Type**: Bar Chart
**Description**: Top 15 team members by comment volume, showing sentiment breakdown

```sql
WITH assignee_sentiment AS (
  SELECT
    t."TKT-Assigned To User" as assignee,
    SUM(CASE WHEN LOWER(c.comment_text) ~ '.*(thank|great|excellent|happy|appreciate|wonderful|fantastic|perfect|amazing).*' THEN 1 ELSE 0 END) as positive,
    SUM(CASE WHEN LOWER(c.comment_text) ~ '.*(issue|problem|unhappy|frustrated|angry|disappointed|urgent|critical|error|fail).*' THEN 1 ELSE 0 END) as negative
  FROM servicedesk.tickets t
  INNER JOIN servicedesk.comments c ON t."TKT-Ticket ID" = c.ticket_id
  WHERE t."TKT-Created Time" >= '2025-07-01'
  AND t."TKT-Assigned To User" IS NOT NULL
  AND c.visible_to_customer = 'Yes'
  GROUP BY t."TKT-Assigned To User"
  HAVING COUNT(*) >= 50
)
SELECT
  assignee as "Team Member",
  positive as "Positive",
  negative as "Negative"
FROM assignee_sentiment
WHERE assignee NOT LIKE ' %'
ORDER BY (positive + negative) DESC
LIMIT 15;
```

**Expected Output**: 15 rows with columns: Team Member, Positive, Negative

**Filter**: Minimum 50 customer-facing comments per assignee

---

## Panel 7: Sentiment Trend Over Time

**Type**: Time Series (Stacked Area Chart)
**Description**: Daily trend of positive/negative/neutral sentiment

```sql
SELECT
  DATE(created_time) as time,
  SUM(CASE WHEN LOWER(comment_text) ~ '.*(thank|great|excellent|happy|appreciate|wonderful|fantastic|perfect|amazing).*' THEN 1 ELSE 0 END) as "Positive",
  SUM(CASE WHEN LOWER(comment_text) ~ '.*(issue|problem|unhappy|frustrated|angry|disappointed|urgent|critical|error|fail).*' THEN 1 ELSE 0 END) as "Negative",
  COUNT(*) - SUM(CASE WHEN LOWER(comment_text) ~ '.*(thank|great|excellent|happy|appreciate|wonderful|fantastic|perfect|amazing|issue|problem|unhappy|frustrated|angry|disappointed|urgent|critical|error|fail).*' THEN 1 ELSE 0 END) as "Neutral"
FROM servicedesk.comments
WHERE visible_to_customer = 'Yes'
AND created_time >= '2025-07-01'
GROUP BY DATE(created_time)
ORDER BY time;
```

**Expected Output**: 94 rows (one per day) with columns: time, Positive, Negative, Neutral

**Visualization**: Stacked area chart showing sentiment composition over time

**Negative Keywords**:
- issue, problem, unhappy, frustrated, angry
- disappointed, urgent, critical, error, fail

---

## Panel 8: SLA Compliance by Team Member

**Type**: Bar Gauge
**Description**: Top 15 team members by SLA compliance percentage

```sql
SELECT
  "TKT-Assigned To User" as "Team Member",
  CAST(SUM(CASE WHEN "TKT-SLA Met" = 'yes' THEN 1 ELSE 0 END)*100.0/COUNT(*) AS NUMERIC(10,1)) as "SLA %"
FROM servicedesk.tickets
WHERE "TKT-Created Time" >= '2025-07-01'
AND "TKT-Assigned To User" IS NOT NULL
AND "TKT-SLA Met" IS NOT NULL
AND "TKT-Assigned To User" NOT LIKE ' %'
GROUP BY "TKT-Assigned To User"
HAVING COUNT(*) >= 50
ORDER BY "SLA %" DESC
LIMIT 15;
```

**Expected Output**: 15 rows with columns: Team Member, SLA %

**Thresholds**:
- 🔴 Red: <85%
- 🟡 Yellow: 85-95%
- 🟢 Green: >95%

**Filter**: Minimum 50 tickets per assignee

---

## Panel 9: Average Resolution Time by Team Member

**Type**: Bar Gauge
**Description**: Top 15 fastest team members by average resolution time

```sql
SELECT
  "TKT-Assigned To User" as "Team Member",
  CAST(AVG(EXTRACT(EPOCH FROM ("TKT-Actual Resolution Date" - "TKT-Created Time"))/3600) AS NUMERIC(10,1)) as "Avg Hours"
FROM servicedesk.tickets
WHERE "TKT-Created Time" >= '2025-07-01'
AND "TKT-Assigned To User" IS NOT NULL
AND "TKT-Actual Resolution Date" IS NOT NULL
AND "TKT-Assigned To User" NOT LIKE ' %'
GROUP BY "TKT-Assigned To User"
HAVING COUNT(*) >= 50
ORDER BY "Avg Hours" ASC
LIMIT 15;
```

**Expected Output**: 15 rows with columns: Team Member, Avg Hours

**Thresholds** (inverted - lower is better):
- 🟢 Green: <48 hours
- 🟡 Yellow: 48-72 hours
- 🔴 Red: >72 hours

**Filter**: Minimum 50 resolved tickets per assignee

---

## Panel 10: Recent Positive Customer Comments

**Type**: Table Panel
**Description**: Last 50 customer-facing comments with positive sentiment

```sql
SELECT
  c.created_time as "Date",
  t."TKT-Ticket ID" as "Ticket",
  t."TKT-Assigned To User" as "Assignee",
  LEFT(c.comment_text, 100) || '...' as "Comment Excerpt"
FROM servicedesk.comments c
INNER JOIN servicedesk.tickets t ON c.ticket_id = t."TKT-Ticket ID"
WHERE c.visible_to_customer = 'Yes'
AND c.created_time >= '2025-07-01'
AND LOWER(c.comment_text) ~ '.*(thank|great|excellent|happy|appreciate|wonderful|fantastic|perfect|amazing).*'
ORDER BY c.created_time DESC
LIMIT 50;
```

**Expected Output**: 50 rows with columns: Date, Ticket, Assignee, Comment Excerpt

**Purpose**: Identify recent positive customer interactions for recognition/training

---

## Panel 11: Recent Negative/Issue Comments

**Type**: Table Panel
**Description**: Last 50 customer-facing comments with negative sentiment or issues

```sql
SELECT
  c.created_time as "Date",
  t."TKT-Ticket ID" as "Ticket",
  t."TKT-Assigned To User" as "Assignee",
  LEFT(c.comment_text, 100) || '...' as "Comment Excerpt"
FROM servicedesk.comments c
INNER JOIN servicedesk.tickets t ON c.ticket_id = t."TKT-Ticket ID"
WHERE c.visible_to_customer = 'Yes'
AND c.created_time >= '2025-07-01'
AND LOWER(c.comment_text) ~ '.*(issue|problem|unhappy|frustrated|angry|disappointed|urgent|critical|error|fail).*'
ORDER BY c.created_time DESC
LIMIT 50;
```

**Expected Output**: 50 rows with columns: Date, Ticket, Assignee, Comment Excerpt

**Purpose**: Identify recent customer issues for immediate attention/coaching

---

## Query Performance Tips

### Optimization Strategies

1. **Date Range Filtering**:
   - Always filter by `created_time >= '2025-07-01'` early in query
   - Creates index scan instead of sequential scan
   - Reduces dataset before joins/aggregations

2. **Indexes Recommended**:
   ```sql
   CREATE INDEX idx_comments_customer_facing_date
   ON servicedesk.comments(visible_to_customer, created_time);

   CREATE INDEX idx_tickets_assigned_created
   ON servicedesk.tickets("TKT-Assigned To User", "TKT-Created Time");

   CREATE INDEX idx_comments_ticket_id
   ON servicedesk.comments(ticket_id);
   ```

3. **CTE Usage**:
   - Complex queries use CTEs for readability
   - PostgreSQL 12+ optimizes CTEs inline (materialization when beneficial)
   - Can force materialization: `WITH cte AS MATERIALIZED (...)`

4. **Regex Performance**:
   - PostgreSQL `~` operator is case-sensitive (faster)
   - Use `LOWER(column) ~ 'pattern'` for case-insensitive
   - Consider full-text search for large-scale sentiment analysis

### Troubleshooting

**Slow Query Diagnostics**:
```sql
EXPLAIN ANALYZE
[your query here];
```

**Check Index Usage**:
```sql
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE schemaname = 'servicedesk'
ORDER BY idx_scan DESC;
```

**Query Statistics**:
```sql
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
WHERE query LIKE '%servicedesk.comments%'
ORDER BY total_time DESC
LIMIT 10;
```

---

## Keyword Reference

### Positive Sentiment Keywords

- thank, thanks, thanked, thanking
- great, excellent, wonderful, fantastic, amazing, perfect
- happy, pleased, satisfied, delighted
- appreciate, appreciated, appreciation

**Regex Pattern**:
```
'.*(thank|great|excellent|happy|appreciate|wonderful|fantastic|perfect|amazing).*'
```

### Negative Sentiment Keywords

- issue, issues, problem, problems
- unhappy, frustrated, frustration, angry, anger
- disappointed, disappointment
- urgent, critical, severe
- error, errors, fail, failed, failure

**Regex Pattern**:
```
'.*(issue|problem|unhappy|frustrated|angry|disappointed|urgent|critical|error|fail).*'
```

### Neutral Comments

- No positive keywords
- No negative keywords
- Calculated as: `total - (positive + negative)`

---

## Testing Queries

### Validate Sentiment Keyword Matching

```sql
-- Sample positive comments
SELECT comment_text
FROM servicedesk.comments
WHERE visible_to_customer = 'Yes'
AND LOWER(comment_text) ~ '.*(thank|great|excellent).*'
LIMIT 10;

-- Sample negative comments
SELECT comment_text
FROM servicedesk.comments
WHERE visible_to_customer = 'Yes'
AND LOWER(comment_text) ~ '.*(issue|problem|urgent).*'
LIMIT 10;
```

### Validate Composite Score Calculation

```sql
-- Test score components for single assignee
WITH test AS (
  SELECT
    COUNT(*) as tickets,
    SUM(CASE WHEN "TKT-SLA Met" = 'yes' THEN 1 ELSE 0 END)*100.0/COUNT(*) as sla_pct,
    AVG(EXTRACT(EPOCH FROM ("TKT-Actual Resolution Date" - "TKT-Created Time"))/3600) as avg_hours
  FROM servicedesk.tickets
  WHERE "TKT-Assigned To User" = 'Anil Kumar'
  AND "TKT-Created Time" >= '2025-07-01'
)
SELECT
  sla_pct,
  avg_hours,
  (sla_pct * 0.3) as sla_component,
  ((100 - LEAST(avg_hours, 100)) * 0.3) as speed_component,
  (sla_pct * 0.3) + ((100 - LEAST(avg_hours, 100)) * 0.3) as score_without_sentiment
FROM test;
```

### Validate Data Source UID

```bash
# Extract datasource UID from dashboard JSON
python3 << 'EOF'
import json
data = json.load(open('/Users/YOUR_USERNAME/git/maia/claude/infrastructure/servicedesk-dashboard/grafana/dashboards/7_customer_sentiment_team_performance.json'))
panels = [p for p in data['dashboard']['panels'] if p.get('type') != 'row']
for p in panels[:3]:
    uid = p['targets'][0]['datasource']['uid'] if 'targets' in p and p['targets'] else 'NONE'
    print(f"Panel {p['id']}: {uid}")
EOF
```

**Expected**: All panels return `P6BECECF7273D15EE`

---

## Common Issues & Solutions

### Issue: No Data in Panels

**Symptoms**: Panels show "No data" despite SQL returning results in psql

**Diagnosis**:
1. Check datasource UID: Should be `P6BECECF7273D15EE` (not variable)
2. Verify column names: Match exactly (case-sensitive with quotes)
3. Test via Grafana API (not just PostgreSQL):
   ```bash
   bash /Users/YOUR_USERNAME/git/maia/tests/test_dashboard_7_panels_data.sh
   ```

**Solution**: Run integration tests to identify exact failure point

### Issue: Incorrect Team Member Ranking

**Symptoms**: Unexpected team members at top/bottom of rankings

**Diagnosis**:
1. Check filters: Minimum ticket count (20 or 50 depending on panel)
2. Validate sentiment join: Must join via `ticket_id`, not username
3. Verify composite score calculation: Check weights (30/30/40)

**Solution**: Run query with `EXPLAIN ANALYZE` to check join behavior

### Issue: Sentiment Keywords Missing Matches

**Symptoms**: Positive/negative counts seem low

**Diagnosis**:
1. Case sensitivity: Use `LOWER(comment_text)` before regex
2. Regex syntax: PostgreSQL uses `~` operator, not LIKE
3. Keyword coverage: May need to expand keyword list

**Solution**: Run test queries to sample matched comments (see Testing Queries above)

---

## References

- **Dashboard JSON**: `/Users/YOUR_USERNAME/git/maia/claude/infrastructure/servicedesk-dashboard/grafana/dashboards/7_customer_sentiment_team_performance.json`
- **Implementation Report**: `/Users/YOUR_USERNAME/git/maia/claude/infrastructure/servicedesk-dashboard/DASHBOARD_7_IMPLEMENTATION_REPORT.md`
- **Unit Tests**: `/Users/YOUR_USERNAME/git/maia/tests/test_dashboard_7_sentiment.sh`
- **Integration Tests**: `/Users/YOUR_USERNAME/git/maia/tests/test_dashboard_7_panels_data.sh`

---

**Last Updated**: 2025-10-20
**Dashboard Version**: 1.0
**PostgreSQL Version**: 14+
**Grafana Version**: 9.5+
