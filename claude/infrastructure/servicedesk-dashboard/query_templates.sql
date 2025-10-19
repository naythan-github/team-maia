-- ============================================================================
-- ServiceDesk ETL V2 - Query Template Library
-- ============================================================================
--
-- PostgreSQL-compatible query templates for all dashboard metrics.
-- Addresses PostgreSQL quirks and provides reusable patterns.
--
-- Key PostgreSQL Differences from SQLite:
-- 1. ROUND() requires ::numeric cast for REAL/FLOAT columns
-- 2. Date arithmetic uses EXTRACT(EPOCH FROM ...) / 86400 for days
-- 3. String concatenation uses || (not +)
-- 4. Boolean types (TRUE/FALSE not 1/0)
-- 5. TIMESTAMP type (not TEXT) for date columns
--
-- Author: ServiceDesk ETL V2 Team
-- Date: 2025-10-19
-- Status: Production Ready
--
-- ============================================================================

-- ============================================================================
-- SECTION 1: Executive Dashboard Queries
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1.1 Total Tickets
-- ----------------------------------------------------------------------------
-- Description: Count of all tickets in system
-- Panel: Single Stat
-- Refresh: Daily

SELECT COUNT(*) as total_tickets
FROM servicedesk.tickets;

-- ----------------------------------------------------------------------------
-- 1.2 Open Tickets
-- ----------------------------------------------------------------------------
-- Description: Count of tickets not yet closed
-- Panel: Single Stat with threshold (>100 = warning)
-- Refresh: Hourly

SELECT COUNT(*) as open_tickets
FROM servicedesk.tickets
WHERE "TKT-Status" NOT IN ('Closed', 'Resolved');

-- ----------------------------------------------------------------------------
-- 1.3 Average Resolution Time (Days)
-- ----------------------------------------------------------------------------
-- Description: Mean time from created to resolved
-- PostgreSQL Note: EXTRACT(EPOCH FROM ...) converts interval to seconds
-- Panel: Single Stat with unit "days"
-- Refresh: Daily

SELECT ROUND(
    AVG(
        EXTRACT(EPOCH FROM ("TKT-Actual Resolution Date" - "TKT-Created Time"))
        / 86400  -- Convert seconds to days
    )::numeric,  -- Cast required for ROUND()
    2
) as avg_resolution_days
FROM servicedesk.tickets
WHERE "TKT-Status" IN ('Closed', 'Resolved')
  AND "TKT-Actual Resolution Date" IS NOT NULL;

-- ----------------------------------------------------------------------------
-- 1.4 Average Quality Score
-- ----------------------------------------------------------------------------
-- Description: Mean quality score from comment analysis
-- PostgreSQL Note: ROUND() requires ::numeric cast
-- Panel: Gauge (0-5 scale)
-- Refresh: Daily

SELECT ROUND(AVG(quality_score)::numeric, 2) as avg_quality
FROM servicedesk.comment_quality
WHERE quality_score IS NOT NULL;


-- ============================================================================
-- SECTION 2: Operations Dashboard Queries
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 2.1 Tickets by Status (Distribution)
-- ----------------------------------------------------------------------------
-- Description: Count and percentage by status
-- Panel: Pie Chart
-- Refresh: Hourly

SELECT
    "TKT-Status" as status,
    COUNT(*) as count,
    ROUND(
        100.0 * COUNT(*) / (SELECT COUNT(*) FROM servicedesk.tickets),
        2
    ) as percentage
FROM servicedesk.tickets
GROUP BY "TKT-Status"
ORDER BY count DESC;

-- ----------------------------------------------------------------------------
-- 2.2 Tickets by Priority
-- ----------------------------------------------------------------------------
-- Description: Count by priority level
-- Panel: Bar Chart (ordered High → Low)
-- Refresh: Hourly

SELECT
    "TKT-Priority" as priority,
    COUNT(*) as count
FROM servicedesk.tickets
GROUP BY "TKT-Priority"
ORDER BY
    CASE "TKT-Priority"
        WHEN 'Critical' THEN 1
        WHEN 'High' THEN 2
        WHEN 'Medium' THEN 3
        WHEN 'Low' THEN 4
        ELSE 5
    END;

-- ----------------------------------------------------------------------------
-- 2.3 Tickets Created Over Time
-- ----------------------------------------------------------------------------
-- Description: Daily ticket creation trend
-- Panel: Time Series Graph
-- Refresh: Hourly

SELECT
    DATE_TRUNC('day', "TKT-Created Time") as day,
    COUNT(*) as tickets_created
FROM servicedesk.tickets
WHERE "TKT-Created Time" >= NOW() - INTERVAL '90 days'
GROUP BY DATE_TRUNC('day', "TKT-Created Time")
ORDER BY day;

-- ----------------------------------------------------------------------------
-- 2.4 Tickets Resolved Over Time
-- ----------------------------------------------------------------------------
-- Description: Daily resolution trend
-- Panel: Time Series Graph
-- Refresh: Hourly

SELECT
    DATE_TRUNC('day', "TKT-Actual Resolution Date") as day,
    COUNT(*) as tickets_resolved
FROM servicedesk.tickets
WHERE "TKT-Actual Resolution Date" >= NOW() - INTERVAL '90 days'
  AND "TKT-Status" IN ('Closed', 'Resolved')
GROUP BY DATE_TRUNC('day', "TKT-Actual Resolution Date")
ORDER BY day;

-- ----------------------------------------------------------------------------
-- 2.5 Average Resolution Time by Priority
-- ----------------------------------------------------------------------------
-- Description: Resolution time grouped by priority
-- Panel: Bar Chart
-- Refresh: Daily

SELECT
    "TKT-Priority" as priority,
    ROUND(
        AVG(
            EXTRACT(EPOCH FROM ("TKT-Actual Resolution Date" - "TKT-Created Time"))
            / 86400
        )::numeric,
        2
    ) as avg_days
FROM servicedesk.tickets
WHERE "TKT-Status" IN ('Closed', 'Resolved')
  AND "TKT-Actual Resolution Date" IS NOT NULL
GROUP BY "TKT-Priority"
ORDER BY
    CASE "TKT-Priority"
        WHEN 'Critical' THEN 1
        WHEN 'High' THEN 2
        WHEN 'Medium' THEN 3
        WHEN 'Low' THEN 4
        ELSE 5
    END;

-- ----------------------------------------------------------------------------
-- 2.6 Quality Tier Distribution
-- ----------------------------------------------------------------------------
-- Description: Comment quality tier breakdown
-- Panel: Pie Chart
-- Refresh: Daily

SELECT
    quality_tier,
    COUNT(*) as count,
    ROUND(
        100.0 * COUNT(*) / (SELECT COUNT(*) FROM servicedesk.comment_quality),
        2
    ) as percentage
FROM servicedesk.comment_quality
GROUP BY quality_tier
ORDER BY
    CASE quality_tier
        WHEN 'excellent' THEN 1
        WHEN 'good' THEN 2
        WHEN 'acceptable' THEN 3
        WHEN 'poor' THEN 4
        ELSE 5
    END;

-- ----------------------------------------------------------------------------
-- 2.7 SLA Compliance Rate
-- ----------------------------------------------------------------------------
-- Description: Percentage of tickets resolved within SLA
-- Note: Assumes 24-hour SLA for High priority, 72 hours for others
-- Panel: Single Stat with threshold (>95% = green)
-- Refresh: Daily

SELECT
    ROUND(
        100.0 * COUNT(CASE
            WHEN "TKT-Priority" = 'High' AND
                 EXTRACT(EPOCH FROM ("TKT-Actual Resolution Date" - "TKT-Created Time")) <= 86400
            THEN 1
            WHEN "TKT-Priority" != 'High' AND
                 EXTRACT(EPOCH FROM ("TKT-Actual Resolution Date" - "TKT-Created Time")) <= 259200
            THEN 1
        END) / NULLIF(COUNT(*), 0),
        2
    ) as sla_compliance_pct
FROM servicedesk.tickets
WHERE "TKT-Status" IN ('Closed', 'Resolved')
  AND "TKT-Actual Resolution Date" IS NOT NULL;


-- ============================================================================
-- SECTION 3: Quality Dashboard Queries
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 3.1 Average Professionalism Score
-- ----------------------------------------------------------------------------
-- Description: Mean professionalism across all comments
-- Panel: Gauge (1-5 scale)
-- Refresh: Daily

SELECT ROUND(AVG(professionalism_score)::numeric, 2) as avg_professionalism
FROM servicedesk.comment_quality
WHERE professionalism_score IS NOT NULL;

-- ----------------------------------------------------------------------------
-- 3.2 Average Clarity Score
-- ----------------------------------------------------------------------------
-- Description: Mean clarity across all comments
-- Panel: Gauge (1-5 scale)
-- Refresh: Daily

SELECT ROUND(AVG(clarity_score)::numeric, 2) as avg_clarity
FROM servicedesk.comment_quality
WHERE clarity_score IS NOT NULL;

-- ----------------------------------------------------------------------------
-- 3.3 Average Empathy Score
-- ----------------------------------------------------------------------------
-- Description: Mean empathy across all comments
-- Panel: Gauge (1-5 scale)
-- Refresh: Daily

SELECT ROUND(AVG(empathy_score)::numeric, 2) as avg_empathy
FROM servicedesk.comment_quality
WHERE empathy_score IS NOT NULL;

-- ----------------------------------------------------------------------------
-- 3.4 Average Actionability Score
-- ----------------------------------------------------------------------------
-- Description: Mean actionability across all comments
-- Panel: Gauge (1-5 scale)
-- Refresh: Daily

SELECT ROUND(AVG(actionability_score)::numeric, 2) as avg_actionability
FROM servicedesk.comment_quality
WHERE actionability_score IS NOT NULL;

-- ----------------------------------------------------------------------------
-- 3.5 Quality Score Distribution
-- ----------------------------------------------------------------------------
-- Description: Histogram of overall quality scores
-- Panel: Histogram
-- Refresh: Daily

SELECT
    FLOOR(quality_score) as score_bucket,
    COUNT(*) as count
FROM servicedesk.comment_quality
WHERE quality_score IS NOT NULL
GROUP BY FLOOR(quality_score)
ORDER BY score_bucket;

-- ----------------------------------------------------------------------------
-- 3.6 Quality Trend Over Time
-- ----------------------------------------------------------------------------
-- Description: Daily average quality score
-- Panel: Time Series Graph
-- Refresh: Daily

SELECT
    DATE_TRUNC('day', analyzed_at) as day,
    ROUND(AVG(quality_score)::numeric, 2) as avg_quality
FROM servicedesk.comment_quality
WHERE analyzed_at >= NOW() - INTERVAL '90 days'
  AND quality_score IS NOT NULL
GROUP BY DATE_TRUNC('day', analyzed_at)
ORDER BY day;

-- ----------------------------------------------------------------------------
-- 3.7 Low Quality Comments (Coaching Opportunities)
-- ----------------------------------------------------------------------------
-- Description: Comments with quality score <2.0
-- Panel: Table with drill-down
-- Refresh: Daily

SELECT
    ticket_number,
    comment_author,
    quality_score,
    quality_tier,
    intent_summary,
    analyzed_at
FROM servicedesk.comment_quality
WHERE quality_score < 2.0
ORDER BY quality_score ASC, analyzed_at DESC
LIMIT 100;


-- ============================================================================
-- SECTION 4: Team Performance Dashboard Queries
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 4.1 Tickets Resolved by Agent
-- ----------------------------------------------------------------------------
-- Description: Top performers by resolution count
-- Panel: Bar Chart (Top 20)
-- Refresh: Daily

SELECT
    "TKT-Assigned To" as agent,
    COUNT(*) as tickets_resolved
FROM servicedesk.tickets
WHERE "TKT-Status" IN ('Closed', 'Resolved')
  AND "TKT-Assigned To" IS NOT NULL
GROUP BY "TKT-Assigned To"
ORDER BY tickets_resolved DESC
LIMIT 20;

-- ----------------------------------------------------------------------------
-- 4.2 Average Resolution Time by Agent
-- ----------------------------------------------------------------------------
-- Description: Agent efficiency metric
-- Panel: Table with conditional formatting
-- Refresh: Daily

SELECT
    "TKT-Assigned To" as agent,
    COUNT(*) as tickets_handled,
    ROUND(
        AVG(
            EXTRACT(EPOCH FROM ("TKT-Actual Resolution Date" - "TKT-Created Time"))
            / 86400
        )::numeric,
        2
    ) as avg_resolution_days
FROM servicedesk.tickets
WHERE "TKT-Status" IN ('Closed', 'Resolved')
  AND "TKT-Actual Resolution Date" IS NOT NULL
  AND "TKT-Assigned To" IS NOT NULL
GROUP BY "TKT-Assigned To"
HAVING COUNT(*) >= 10  -- Minimum 10 tickets for statistical relevance
ORDER BY avg_resolution_days ASC;

-- ----------------------------------------------------------------------------
-- 4.3 Quality Score by Agent
-- ----------------------------------------------------------------------------
-- Description: Agent quality rankings
-- Panel: Table with drill-down
-- Refresh: Daily

SELECT
    comment_author as agent,
    COUNT(*) as comments_analyzed,
    ROUND(AVG(quality_score)::numeric, 2) as avg_quality,
    ROUND(AVG(professionalism_score)::numeric, 2) as avg_professionalism,
    ROUND(AVG(clarity_score)::numeric, 2) as avg_clarity,
    ROUND(AVG(empathy_score)::numeric, 2) as avg_empathy,
    ROUND(AVG(actionability_score)::numeric, 2) as avg_actionability
FROM servicedesk.comment_quality
WHERE comment_author IS NOT NULL
  AND quality_score IS NOT NULL
GROUP BY comment_author
HAVING COUNT(*) >= 5  -- Minimum 5 comments for statistical relevance
ORDER BY avg_quality DESC;

-- ----------------------------------------------------------------------------
-- 4.4 Agent Workload (Current Open Tickets)
-- ----------------------------------------------------------------------------
-- Description: Current ticket assignments
-- Panel: Bar Chart
-- Refresh: Hourly

SELECT
    "TKT-Assigned To" as agent,
    COUNT(*) as open_tickets
FROM servicedesk.tickets
WHERE "TKT-Status" NOT IN ('Closed', 'Resolved')
  AND "TKT-Assigned To" IS NOT NULL
GROUP BY "TKT-Assigned To"
ORDER BY open_tickets DESC;


-- ============================================================================
-- SECTION 5: Advanced Analytics Queries
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 5.1 Ticket Volume Forecast (7-Day Moving Average)
-- ----------------------------------------------------------------------------
-- Description: Smoothed trend for capacity planning
-- Panel: Time Series Graph with forecast line
-- Refresh: Daily

SELECT
    day,
    tickets_created,
    AVG(tickets_created) OVER (
        ORDER BY day
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) as moving_avg_7day
FROM (
    SELECT
        DATE_TRUNC('day', "TKT-Created Time") as day,
        COUNT(*) as tickets_created
    FROM servicedesk.tickets
    WHERE "TKT-Created Time" >= NOW() - INTERVAL '90 days'
    GROUP BY DATE_TRUNC('day', "TKT-Created Time")
) daily_counts
ORDER BY day;

-- ----------------------------------------------------------------------------
-- 5.2 Resolution Time Percentiles
-- ----------------------------------------------------------------------------
-- Description: P50, P90, P95, P99 resolution times
-- Panel: Table
-- Refresh: Daily

SELECT
    PERCENTILE_CONT(0.50) WITHIN GROUP (
        ORDER BY EXTRACT(EPOCH FROM ("TKT-Actual Resolution Date" - "TKT-Created Time")) / 86400
    ) as p50_days,
    PERCENTILE_CONT(0.90) WITHIN GROUP (
        ORDER BY EXTRACT(EPOCH FROM ("TKT-Actual Resolution Date" - "TKT-Created Time")) / 86400
    ) as p90_days,
    PERCENTILE_CONT(0.95) WITHIN GROUP (
        ORDER BY EXTRACT(EPOCH FROM ("TKT-Actual Resolution Date" - "TKT-Created Time")) / 86400
    ) as p95_days,
    PERCENTILE_CONT(0.99) WITHIN GROUP (
        ORDER BY EXTRACT(EPOCH FROM ("TKT-Actual Resolution Date" - "TKT-Created Time")) / 86400
    ) as p99_days
FROM servicedesk.tickets
WHERE "TKT-Status" IN ('Closed', 'Resolved')
  AND "TKT-Actual Resolution Date" IS NOT NULL;

-- ----------------------------------------------------------------------------
-- 5.3 Quality Improvement Tracking
-- ----------------------------------------------------------------------------
-- Description: Month-over-month quality change
-- Panel: Time Series with trend line
-- Refresh: Weekly

SELECT
    DATE_TRUNC('month', analyzed_at) as month,
    ROUND(AVG(quality_score)::numeric, 2) as avg_quality,
    COUNT(*) as comments_analyzed
FROM servicedesk.comment_quality
WHERE analyzed_at >= NOW() - INTERVAL '12 months'
  AND quality_score IS NOT NULL
GROUP BY DATE_TRUNC('month', analyzed_at)
ORDER BY month;


-- ============================================================================
-- SECTION 6: Data Quality & Monitoring Queries
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 6.1 Data Completeness Check
-- ----------------------------------------------------------------------------
-- Description: NULL value percentage by column
-- Panel: Table (for monitoring)
-- Refresh: Daily

SELECT
    'created_time' as column_name,
    ROUND(100.0 * COUNT(CASE WHEN "TKT-Created Time" IS NULL THEN 1 END) / COUNT(*), 2) as null_pct
FROM servicedesk.tickets
UNION ALL
SELECT
    'resolved_date',
    ROUND(100.0 * COUNT(CASE WHEN "TKT-Actual Resolution Date" IS NULL THEN 1 END) / COUNT(*), 2)
FROM servicedesk.tickets
UNION ALL
SELECT
    'assigned_to',
    ROUND(100.0 * COUNT(CASE WHEN "TKT-Assigned To" IS NULL THEN 1 END) / COUNT(*), 2)
FROM servicedesk.tickets
UNION ALL
SELECT
    'priority',
    ROUND(100.0 * COUNT(CASE WHEN "TKT-Priority" IS NULL THEN 1 END) / COUNT(*), 2)
FROM servicedesk.tickets;

-- ----------------------------------------------------------------------------
-- 6.2 Quality Analysis Coverage
-- ----------------------------------------------------------------------------
-- Description: Percentage of comments analyzed
-- Panel: Single Stat with threshold (>80% = green)
-- Refresh: Daily

SELECT
    ROUND(
        100.0 * (SELECT COUNT(*) FROM servicedesk.comment_quality) /
        (SELECT COUNT(*) FROM servicedesk.comments),
        2
    ) as coverage_pct;

-- ----------------------------------------------------------------------------
-- 6.3 Data Freshness Check
-- ----------------------------------------------------------------------------
-- Description: Time since last data update
-- Panel: Single Stat (alert if >24 hours)
-- Refresh: Hourly

SELECT
    EXTRACT(EPOCH FROM (NOW() - MAX("TKT-Created Time"))) / 3600 as hours_since_last_ticket
FROM servicedesk.tickets;


-- ============================================================================
-- USAGE NOTES
-- ============================================================================
--
-- 1. All queries use schema-qualified table names (servicedesk.tickets)
-- 2. Column names with spaces are quoted ("TKT-Created Time")
-- 3. ROUND() uses ::numeric cast for PostgreSQL compatibility
-- 4. Date arithmetic uses EXTRACT(EPOCH FROM ...) for cross-database compatibility
-- 5. Time series queries use DATE_TRUNC() for PostgreSQL
-- 6. Percentiles use PERCENTILE_CONT() (PostgreSQL-specific)
--
-- Performance Tips:
-- - Create indexes on frequently queried columns
-- - Use materialized views for complex aggregations
-- - Partition large tables by date for faster queries
-- - Monitor query execution time with EXPLAIN ANALYZE
--
-- ============================================================================
