#!/bin/bash
# Dashboard #7 Customer Sentiment & Team Performance - TDD Test Suite
# Following strict TDD methodology from Dashboard #6 success

set -e

# Auto-detect MAIA_ROOT from script location if not set
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MAIA_ROOT="${MAIA_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Database connection
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="servicedesk"
DB_USER="servicedesk_user"
DB_CONTAINER="servicedesk-postgres"

# Grafana connection
GRAFANA_URL="http://localhost:3000"
GRAFANA_USER="admin"
GRAFANA_PASS="Grafana2025!SecureAdmin"
DASHBOARD_UID="servicedesk-sentiment-team-performance"
DASHBOARD_FILE="$MAIA_ROOT/claude/infrastructure/servicedesk-dashboard/grafana/dashboards/7_customer_sentiment_team_performance.json"

# Helper function to run SQL
run_sql() {
    docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -A -c "$1"
}

# Helper function to run test
run_test() {
    local test_name="$1"
    local test_function="$2"

    TESTS_RUN=$((TESTS_RUN + 1))
    echo -e "\n${YELLOW}Test $TESTS_RUN: $test_name${NC}"

    if $test_function; then
        echo -e "${GREEN}✓ PASS${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# Test 1: Verify customer-facing comments exist
test_customer_comments_exist() {
    local count=$(run_sql "SELECT COUNT(*) FROM servicedesk.comments WHERE visible_to_customer = 'Yes' AND created_time >= '2025-07-01';")

    if [ "$count" -gt 1000 ]; then
        echo "Found $count customer-facing comments"
        return 0
    else
        echo "ERROR: Only $count customer-facing comments found (expected > 1000)"
        return 1
    fi
}

# Test 2: Verify SLA data exists
test_sla_data_exists() {
    local count=$(run_sql "SELECT COUNT(*) FROM servicedesk.tickets WHERE \"TKT-Created Time\" >= '2025-07-01' AND \"TKT-SLA Met\" IS NOT NULL;")

    if [ "$count" -gt 1000 ]; then
        echo "Found $count tickets with SLA data"
        return 0
    else
        echo "ERROR: Only $count tickets with SLA data found (expected > 1000)"
        return 1
    fi
}

# Test 3: Verify sentiment keyword matching works
test_sentiment_keywords() {
    local result=$(run_sql "
        SELECT
            SUM(CASE WHEN LOWER(comment_text) ~ '.*(thank|great|excellent|happy).*' THEN 1 ELSE 0 END) as positive,
            SUM(CASE WHEN LOWER(comment_text) ~ '.*(issue|problem|urgent|error).*' THEN 1 ELSE 0 END) as negative
        FROM servicedesk.comments
        WHERE visible_to_customer = 'Yes'
        AND created_time >= '2025-07-01'
        LIMIT 1000;
    ")

    local positive=$(echo "$result" | cut -d'|' -f1)
    local negative=$(echo "$result" | cut -d'|' -f2)

    if [ "$positive" -gt 0 ] && [ "$negative" -gt 0 ]; then
        echo "Sentiment keywords working: $positive positive, $negative negative"
        return 0
    else
        echo "ERROR: Sentiment keyword matching failed (positive=$positive, negative=$negative)"
        return 1
    fi
}

# Test 4: Verify resolution time calculation works
test_resolution_time_calculation() {
    local result=$(run_sql "
        SELECT
            COUNT(*) as count,
            AVG(EXTRACT(EPOCH FROM (\"TKT-Actual Resolution Date\" - \"TKT-Created Time\"))/3600) as avg_hours
        FROM servicedesk.tickets
        WHERE \"TKT-Created Time\" >= '2025-07-01'
        AND \"TKT-Actual Resolution Date\" IS NOT NULL;
    ")

    local count=$(echo "$result" | cut -d'|' -f1)
    local avg_hours=$(echo "$result" | cut -d'|' -f2)

    if [ "$count" -gt 1000 ] && [ -n "$avg_hours" ]; then
        echo "Resolution time calculation working: $count tickets, avg $avg_hours hours"
        return 0
    else
        echo "ERROR: Resolution time calculation failed (count=$count, avg_hours=$avg_hours)"
        return 1
    fi
}

# Test 5: Verify sentiment by assignee query works
test_sentiment_by_assignee() {
    local count=$(run_sql "
        WITH assignee_tickets AS (
            SELECT \"TKT-Assigned To User\" as assignee, \"TKT-Ticket ID\" as ticket_id
            FROM servicedesk.tickets
            WHERE \"TKT-Created Time\" >= '2025-07-01'
            AND \"TKT-Assigned To User\" IS NOT NULL
        ),
        ticket_sentiment AS (
            SELECT ticket_id,
                SUM(CASE WHEN LOWER(comment_text) ~ '.*(thank|great|excellent|happy).*' THEN 1 ELSE 0 END) as positive
            FROM servicedesk.comments
            WHERE visible_to_customer = 'Yes'
            GROUP BY ticket_id
        )
        SELECT COUNT(DISTINCT at.assignee)
        FROM assignee_tickets at
        LEFT JOIN ticket_sentiment ts ON at.ticket_id = ts.ticket_id
        WHERE at.assignee NOT LIKE ' %';
    ")

    if [ "$count" -gt 10 ]; then
        echo "Sentiment by assignee query working: $count assignees found"
        return 0
    else
        echo "ERROR: Sentiment by assignee query failed (found $count assignees, expected > 10)"
        return 1
    fi
}

# Test 6: Verify composite score calculation
test_composite_score_calculation() {
    local result=$(run_sql "
        WITH assignee_metrics AS (
            SELECT
                \"TKT-Assigned To User\" as assignee,
                COUNT(*) as total_tickets,
                SUM(CASE WHEN \"TKT-SLA Met\" = 'yes' THEN 1 ELSE 0 END)*100.0/COUNT(*) as sla_pct,
                AVG(EXTRACT(EPOCH FROM (\"TKT-Actual Resolution Date\" - \"TKT-Created Time\"))/3600) as avg_hours
            FROM servicedesk.tickets
            WHERE \"TKT-Created Time\" >= '2025-07-01'
            AND \"TKT-Assigned To User\" IS NOT NULL
            AND \"TKT-SLA Met\" IS NOT NULL
            GROUP BY \"TKT-Assigned To User\"
            HAVING COUNT(*) >= 50
        )
        SELECT
            assignee,
            (sla_pct * 0.3) + ((100 - LEAST(avg_hours, 100)) * 0.3) as composite_score
        FROM assignee_metrics
        ORDER BY composite_score DESC
        LIMIT 1;
    ")

    if [ -n "$result" ]; then
        echo "Composite score calculation working: Top performer = $result"
        return 0
    else
        echo "ERROR: Composite score calculation failed"
        return 1
    fi
}

# Test 7: Verify dashboard file exists
test_dashboard_file_exists() {
    if [ -f "$DASHBOARD_FILE" ]; then
        echo "Dashboard file exists at $DASHBOARD_FILE"
        return 0
    else
        echo "ERROR: Dashboard file not found at $DASHBOARD_FILE"
        return 1
    fi
}

# Test 8: Verify dashboard JSON is valid
test_dashboard_json_valid() {
    if ! [ -f "$DASHBOARD_FILE" ]; then
        echo "Skipping: Dashboard file doesn't exist yet"
        return 1
    fi

    if python3 -m json.tool "$DASHBOARD_FILE" > /dev/null 2>&1; then
        echo "Dashboard JSON is valid"
        return 0
    else
        echo "ERROR: Dashboard JSON is invalid"
        return 1
    fi
}

# Test 9: Verify dashboard has required panels
test_dashboard_has_required_panels() {
    if ! [ -f "$DASHBOARD_FILE" ]; then
        echo "Skipping: Dashboard file doesn't exist yet"
        return 1
    fi

    local panel_count=$(python3 -c "import json; data=json.load(open('$DASHBOARD_FILE')); print(len([p for p in data['dashboard']['panels'] if p.get('type') != 'row']))" 2>/dev/null || echo "0")

    if [ "$panel_count" -ge 8 ]; then
        echo "Dashboard has $panel_count panels (required: >= 8)"
        return 0
    else
        echo "ERROR: Dashboard has only $panel_count panels (required: >= 8)"
        return 1
    fi
}

# Test 10: Verify dashboard imports successfully
test_dashboard_imports() {
    if ! [ -f "$DASHBOARD_FILE" ]; then
        echo "Skipping: Dashboard file doesn't exist yet"
        return 1
    fi

    # Check if Grafana is running
    if ! curl -s "$GRAFANA_URL/api/health" > /dev/null 2>&1; then
        echo "ERROR: Grafana is not running at $GRAFANA_URL"
        return 1
    fi

    # Try to import dashboard
    local response=$(curl -s -X POST "$GRAFANA_URL/api/dashboards/db" \
        -H "Content-Type: application/json" \
        -u "$GRAFANA_USER:$GRAFANA_PASS" \
        -d @"$DASHBOARD_FILE")

    if echo "$response" | grep -q '"status":"success"'; then
        echo "Dashboard imported successfully"
        return 0
    else
        echo "ERROR: Dashboard import failed: $response"
        return 1
    fi
}

# Test 11: Verify dashboard is accessible via API
test_dashboard_accessible() {
    if ! [ -f "$DASHBOARD_FILE" ]; then
        echo "Skipping: Dashboard file doesn't exist yet"
        return 1
    fi

    local response=$(curl -s "$GRAFANA_URL/api/dashboards/uid/$DASHBOARD_UID" \
        -u "$GRAFANA_USER:$GRAFANA_PASS")

    if echo "$response" | grep -q "\"uid\":\"$DASHBOARD_UID\""; then
        echo "Dashboard is accessible via API"
        return 0
    else
        echo "ERROR: Dashboard not accessible via API"
        return 1
    fi
}

# Test 12: Verify data source UID is correct (lesson from Dashboard #6)
test_datasource_uid_correct() {
    if ! [ -f "$DASHBOARD_FILE" ]; then
        echo "Skipping: Dashboard file doesn't exist yet"
        return 1
    fi

    local datasource_uid=$(python3 << PYEOF
import json
data = json.load(open('$DASHBOARD_FILE'))
panels = [p for p in data['dashboard']['panels'] if p.get('type') != 'row']
if panels and 'targets' in panels[0] and panels[0]['targets']:
    print(panels[0]['targets'][0].get('datasource', {}).get('uid', 'NONE'))
else:
    print('NONE')
PYEOF
)

    if [ "$datasource_uid" = "P6BECECF7273D15EE" ]; then
        echo "Data source UID is correct: $datasource_uid"
        return 0
    else
        echo "ERROR: Data source UID is wrong: $datasource_uid (expected: P6BECECF7273D15EE)"
        return 1
    fi
}

# Main test execution
main() {
    echo "=========================================="
    echo "Dashboard #7 TDD Test Suite"
    echo "Customer Sentiment & Team Performance"
    echo "=========================================="

    # Phase 1: Data validation tests (always run)
    echo -e "\n${YELLOW}=== PHASE 1: DATA VALIDATION ===${NC}"
    run_test "Customer-facing comments exist" test_customer_comments_exist
    run_test "SLA data exists" test_sla_data_exists
    run_test "Sentiment keyword matching works" test_sentiment_keywords
    run_test "Resolution time calculation works" test_resolution_time_calculation
    run_test "Sentiment by assignee query works" test_sentiment_by_assignee
    run_test "Composite score calculation works" test_composite_score_calculation

    # Phase 2: Dashboard validation tests (run if dashboard exists)
    echo -e "\n${YELLOW}=== PHASE 2: DASHBOARD VALIDATION ===${NC}"
    run_test "Dashboard file exists" test_dashboard_file_exists
    run_test "Dashboard JSON is valid" test_dashboard_json_valid
    run_test "Dashboard has required panels" test_dashboard_has_required_panels
    run_test "Data source UID is correct" test_datasource_uid_correct

    # Phase 3: Integration tests (run if Grafana is accessible)
    echo -e "\n${YELLOW}=== PHASE 3: INTEGRATION TESTS ===${NC}"
    run_test "Dashboard imports successfully" test_dashboard_imports
    run_test "Dashboard is accessible via API" test_dashboard_accessible

    # Summary
    echo -e "\n=========================================="
    echo -e "Test Results Summary"
    echo -e "=========================================="
    echo -e "Tests Run:    $TESTS_RUN"
    echo -e "${GREEN}Tests Passed: $TESTS_PASSED${NC}"
    if [ $TESTS_FAILED -gt 0 ]; then
        echo -e "${RED}Tests Failed: $TESTS_FAILED${NC}"
    else
        echo -e "${GREEN}Tests Failed: $TESTS_FAILED${NC}"
    fi
    echo -e "Pass Rate:    $(awk "BEGIN {printf \"%.1f\", ($TESTS_PASSED/$TESTS_RUN)*100}")%"
    echo -e "=========================================="

    # Exit with error if any tests failed
    if [ $TESTS_FAILED -gt 0 ]; then
        exit 1
    else
        exit 0
    fi
}

# Run main function
main
