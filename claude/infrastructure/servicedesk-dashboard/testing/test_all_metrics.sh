#!/bin/bash
# Test All 23 Metrics from ServiceDesk Metrics Catalog
# Tests each metric query against PostgreSQL database

set -e

PASSED=0
FAILED=0
TOTAL=23

echo "======================================================================="
echo "TESTING ALL 23 SERVICEDESK METRICS"
echo "Target: PostgreSQL servicedesk database"
echo "======================================================================="
echo ""

# Test function
test_metric() {
    local metric_name="$1"
    local sql="$2"
    local expected_type="$3"  # number, percentage, etc.

    echo "Testing: $metric_name"

    result=$(docker exec servicedesk-postgres psql -U servicedesk_user -d servicedesk -t -c "$sql" 2>&1)
    exit_code=$?

    if [ $exit_code -eq 0 ]; then
        # Check if result is not empty
        if [ -n "$result" ]; then
            echo "  ✅ PASS - Result: $result"
            ((PASSED++))
            return 0
        else
            echo "  ❌ FAIL - Empty result"
            ((FAILED++))
            return 1
        fi
    else
        echo "  ❌ FAIL - SQL Error: $result"
        ((FAILED++))
        return 1
    fi
}

echo "CATEGORY 1: CRITICAL METRICS (5 metrics)"
echo "-------------------------------------------------------------------"

# 1.1 SLA Compliance Rate
test_metric "1.1 SLA Compliance Rate" \
"SELECT ROUND(100.0 * SUM(CASE WHEN \"TKT-SLA Met\" = 'yes' THEN 1 ELSE 0 END) / COUNT(*), 2) as value FROM servicedesk.tickets WHERE \"TKT-SLA Met\" IS NOT NULL;" \
"percentage"

# 1.2 Average Resolution Time
test_metric "1.2 Average Resolution Time (days)" \
"SELECT ROUND(AVG(CAST((EXTRACT(EPOCH FROM (\"TKT-Actual Resolution Date\" - \"TKT-Created Time\"))/86400) AS NUMERIC)), 2) as value FROM servicedesk.tickets WHERE \"TKT-Status\" IN ('Closed', 'Resolved') AND \"TKT-Actual Resolution Date\" IS NOT NULL AND \"TKT-Created Time\" IS NOT NULL;" \
"number"

# 1.3 First Contact Resolution Rate
test_metric "1.3 FCR Rate" \
"WITH customer_facing_comments AS (SELECT ticket_id, COUNT(*) as customer_comment_count FROM servicedesk.comments WHERE visible_to_customer = 'Yes' GROUP BY ticket_id) SELECT ROUND(100.0 * SUM(CASE WHEN COALESCE(cfc.customer_comment_count, 0) <= 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as value FROM servicedesk.tickets t LEFT JOIN customer_facing_comments cfc ON t.\"TKT-Ticket ID\" = cfc.ticket_id WHERE t.\"TKT-Status\" IN ('Closed', 'Resolved');" \
"percentage"

# 1.4 Customer Communication Coverage
test_metric "1.4 Customer Communication Coverage" \
"WITH customer_facing_comments AS (SELECT ticket_id, COUNT(*) as customer_comment_count FROM servicedesk.comments WHERE visible_to_customer = 'Yes' GROUP BY ticket_id) SELECT ROUND(100.0 * SUM(CASE WHEN cfc.customer_comment_count > 0 THEN 1 ELSE 0 END) / COUNT(*), 2) as value FROM servicedesk.tickets t LEFT JOIN customer_facing_comments cfc ON t.\"TKT-Ticket ID\" = cfc.ticket_id WHERE t.\"TKT-Status\" IN ('Closed', 'Resolved');" \
"percentage"

# 1.5 Overall Quality Score
test_metric "1.5 Overall Quality Score" \
"SELECT ROUND(AVG(quality_score)::numeric, 2) as value FROM servicedesk.comment_quality WHERE quality_score IS NOT NULL;" \
"number"

echo ""
echo "CATEGORY 2: OPERATIONAL METRICS (8 metrics)"
echo "-------------------------------------------------------------------"

# 2.1 Ticket Reassignment Rate
test_metric "2.1 Reassignment Rate" \
"WITH reassignments AS (SELECT \"TS-Ticket Project Master Code\" as ticket_id, COUNT(DISTINCT \"TS-User Full Name\") as agent_count FROM servicedesk.timesheets GROUP BY \"TS-Ticket Project Master Code\") SELECT ROUND(100.0 * SUM(CASE WHEN COALESCE(r.agent_count, 1) > 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as value FROM servicedesk.tickets t LEFT JOIN reassignments r ON t.\"TKT-Ticket ID\" = r.ticket_id WHERE t.\"TKT-Status\" IN ('Closed', 'Resolved');" \
"percentage"

# 2.2 Total Ticket Volume
test_metric "2.2 Total Ticket Volume" \
"SELECT COUNT(*) as value FROM servicedesk.tickets;" \
"number"

# 2.3 Tickets by Category
test_metric "2.3 Top Category" \
"SELECT \"TKT-Category\", COUNT(*) as count FROM servicedesk.tickets WHERE \"TKT-Category\" IS NOT NULL GROUP BY \"TKT-Category\" ORDER BY count DESC LIMIT 1;" \
"text"

# 2.4 Root Cause Distribution
test_metric "2.4 Top Root Cause" \
"SELECT \"TKT-Root Cause Category\", COUNT(*) as count FROM servicedesk.tickets WHERE \"TKT-Root Cause Category\" IS NOT NULL GROUP BY \"TKT-Root Cause Category\" ORDER BY count DESC LIMIT 1;" \
"text"

# 2.5 Team Workload Distribution
test_metric "2.5 Team with Most Tickets" \
"SELECT \"TKT-Team\", COUNT(*) as count FROM servicedesk.tickets WHERE \"TKT-Team\" IS NOT NULL GROUP BY \"TKT-Team\" ORDER BY count DESC LIMIT 1;" \
"text"

# 2.6 Team Resolution Time
test_metric "2.6 Fastest Team Resolution Time" \
"SELECT \"TKT-Team\", ROUND(AVG(CAST((EXTRACT(EPOCH FROM (\"TKT-Actual Resolution Date\" - \"TKT-Created Time\"))/86400) AS NUMERIC)), 2) as avg_days FROM servicedesk.tickets WHERE \"TKT-Status\" IN ('Closed', 'Resolved') AND \"TKT-Actual Resolution Date\" IS NOT NULL AND \"TKT-Team\" IS NOT NULL GROUP BY \"TKT-Team\" ORDER BY avg_days ASC LIMIT 1;" \
"text"

# 2.7 Team Communication Coverage
test_metric "2.7 Best Team Communication Coverage" \
"WITH customer_facing_comments AS (SELECT ticket_id, COUNT(*) as comment_count FROM servicedesk.comments WHERE visible_to_customer = 'Yes' GROUP BY ticket_id) SELECT t.\"TKT-Team\", ROUND(100.0 * SUM(CASE WHEN cfc.comment_count > 0 THEN 1 ELSE 0 END) / COUNT(*), 2) as coverage FROM servicedesk.tickets t LEFT JOIN customer_facing_comments cfc ON t.\"TKT-Ticket ID\" = cfc.ticket_id WHERE t.\"TKT-Status\" IN ('Closed', 'Resolved') AND t.\"TKT-Team\" IS NOT NULL GROUP BY t.\"TKT-Team\" ORDER BY coverage DESC LIMIT 1;" \
"text"

# 2.8 Incident Handling Efficiency
test_metric "2.8 Most Efficient Team" \
"SELECT t.\"TKT-Team\", COUNT(ts.\"TS-User Full Name\") as total_events FROM servicedesk.tickets t LEFT JOIN servicedesk.timesheets ts ON t.\"TKT-Ticket ID\" = ts.\"TS-Ticket Project Master Code\" WHERE t.\"TKT-Team\" IS NOT NULL AND t.\"TKT-Status\" IN ('Closed', 'Resolved') GROUP BY t.\"TKT-Team\" ORDER BY total_events ASC LIMIT 1;" \
"text"

echo ""
echo "CATEGORY 3: QUALITY METRICS (6 metrics)"
echo "-------------------------------------------------------------------"

# 3.1 Quality Score by Dimension
test_metric "3.1 Professionalism Score" \
"SELECT ROUND(AVG(professionalism_score)::numeric, 2) as value FROM servicedesk.comment_quality WHERE professionalism_score IS NOT NULL;" \
"number"

# 3.2 Quality Tier Distribution
test_metric "3.2 Quality Tier Counts" \
"SELECT quality_tier, COUNT(*) as count FROM servicedesk.comment_quality WHERE quality_tier IS NOT NULL GROUP BY quality_tier ORDER BY count DESC LIMIT 1;" \
"text"

# 3.3 Clarity Score
test_metric "3.3 Clarity Score" \
"SELECT ROUND(AVG(clarity_score)::numeric, 2) as value FROM servicedesk.comment_quality WHERE clarity_score IS NOT NULL;" \
"number"

# 3.4 Empathy Score
test_metric "3.4 Empathy Score" \
"SELECT ROUND(AVG(empathy_score)::numeric, 2) as value FROM servicedesk.comment_quality WHERE empathy_score IS NOT NULL;" \
"number"

# 3.5 Actionability Score
test_metric "3.5 Actionability Score" \
"SELECT ROUND(AVG(actionability_score)::numeric, 2) as value FROM servicedesk.comment_quality WHERE actionability_score IS NOT NULL;" \
"number"

# 3.6 Quality Coverage
test_metric "3.6 Quality Analysis Coverage" \
"SELECT ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM servicedesk.comments), 2) as value FROM servicedesk.comment_quality;" \
"percentage"

echo ""
echo "CATEGORY 4: TREND & PERFORMANCE METRICS (4 metrics)"
echo "-------------------------------------------------------------------"

# 4.1 Monthly Ticket Trend
test_metric "4.1 Current Month Ticket Count" \
"SELECT COUNT(*) as value FROM servicedesk.tickets WHERE \"TKT-Month Created\" = (SELECT \"TKT-Month Created\" FROM servicedesk.tickets WHERE \"TKT-Month Created\" IS NOT NULL ORDER BY \"TKT-Created Time\" DESC LIMIT 1);" \
"number"

# 4.2 Resolution Time Trend
test_metric "4.2 Latest Month Avg Resolution Time" \
"SELECT ROUND(AVG(CAST((EXTRACT(EPOCH FROM (\"TKT-Actual Resolution Date\" - \"TKT-Created Time\"))/86400) AS NUMERIC)), 2) as value FROM servicedesk.tickets WHERE \"TKT-Month Created\" = (SELECT \"TKT-Month Created\" FROM servicedesk.tickets WHERE \"TKT-Month Created\" IS NOT NULL ORDER BY \"TKT-Created Time\" DESC LIMIT 1) AND \"TKT-Actual Resolution Date\" IS NOT NULL;" \
"number"

# 4.3 Team FCR Distribution
test_metric "4.3 Best Team FCR Rate" \
"WITH customer_facing_comments AS (SELECT ticket_id, COUNT(*) as comment_count FROM servicedesk.comments WHERE visible_to_customer = 'Yes' GROUP BY ticket_id) SELECT t.\"TKT-Team\", ROUND(100.0 * SUM(CASE WHEN COALESCE(cfc.comment_count, 0) <= 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as fcr_rate FROM servicedesk.tickets t LEFT JOIN customer_facing_comments cfc ON t.\"TKT-Ticket ID\" = cfc.ticket_id WHERE t.\"TKT-Status\" IN ('Closed', 'Resolved') AND t.\"TKT-Team\" IS NOT NULL GROUP BY t.\"TKT-Team\" ORDER BY fcr_rate DESC LIMIT 1;" \
"text"

# 4.4 Data Quality Check
test_metric "4.4 Tickets with SLA Data" \
"SELECT ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM servicedesk.tickets), 2) as value FROM servicedesk.tickets WHERE \"TKT-SLA Met\" IS NOT NULL;" \
"percentage"

echo ""
echo "======================================================================="
echo "TEST SUMMARY"
echo "======================================================================="
echo "Total Tests: $TOTAL"
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "🎉 ALL TESTS PASSED!"
    exit 0
else
    echo "⚠️  Some tests failed. Review output above."
    exit 1
fi
