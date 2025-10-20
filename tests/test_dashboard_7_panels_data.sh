#!/bin/bash
# Dashboard #7 Panel Data Integration Tests
# Critical lesson from Dashboard #6: Test panels via Grafana API, not just SQL

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Grafana connection
GRAFANA_URL="http://localhost:3000"
GRAFANA_USER="admin"
GRAFANA_PASS="Grafana2025!SecureAdmin"
DASHBOARD_UID="servicedesk-sentiment-team-performance"

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

# Get panel query results from Grafana
get_panel_data() {
    local panel_id="$1"

    # Get dashboard with panel details
    local response=$(curl -s "$GRAFANA_URL/api/dashboards/uid/$DASHBOARD_UID" \
        -u "$GRAFANA_USER:$GRAFANA_PASS")

    # Extract the panel
    local panel=$(echo "$response" | python3 -c "
import json, sys
data = json.load(sys.stdin)
panels = [p for p in data['dashboard']['panels'] if p.get('id') == $panel_id]
if panels:
    print(json.dumps(panels[0]))
else:
    print('{}')
" 2>/dev/null)

    if [ "$panel" = "{}" ]; then
        echo "ERROR: Panel $panel_id not found"
        return 1
    fi

    # Extract SQL query
    local sql_query=$(echo "$panel" | python3 -c "
import json, sys
panel = json.load(sys.stdin)
if 'targets' in panel and panel['targets']:
    print(panel['targets'][0].get('rawSql', ''))
" 2>/dev/null)

    if [ -z "$sql_query" ]; then
        echo "ERROR: No SQL query found for panel $panel_id"
        return 1
    fi

    # Test query via Grafana's datasource proxy
    local datasource_uid="P6BECECF7273D15EE"
    local query_response=$(curl -s -X POST \
        "$GRAFANA_URL/api/ds/query" \
        -H "Content-Type: application/json" \
        -u "$GRAFANA_USER:$GRAFANA_PASS" \
        -d '{
            "queries": [
                {
                    "datasource": {"type": "postgres", "uid": "'"$datasource_uid"'"},
                    "rawSql": '"$(echo "$sql_query" | python3 -c 'import sys, json; print(json.dumps(sys.stdin.read()))')"',
                    "format": "table",
                    "refId": "A"
                }
            ],
            "from": "1719792000000",
            "to": "now"
        }')

    echo "$query_response"
}

# Test Panel 1: Total Customer-Facing Comments
test_panel_1_customer_comments() {
    local result=$(get_panel_data 1)

    # Check if we got data (not an error)
    if echo "$result" | grep -q '"error"'; then
        echo "ERROR: Query failed: $(echo "$result" | python3 -c 'import json, sys; print(json.load(sys.stdin).get("error", "Unknown error"))' 2>/dev/null || echo "$result")"
        return 1
    fi

    # Check if we got rows
    local row_count=$(echo "$result" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if 'results' in data and data['results']:
        frames = data['results'].get('A', {}).get('frames', [])
        if frames and len(frames) > 0:
            rows = frames[0].get('data', {}).get('values', [[]])[0]
            print(len(rows) if rows else 0)
        else:
            print(0)
    else:
        print(0)
except:
    print(0)
" 2>/dev/null || echo "0")

    if [ "$row_count" -gt 0 ]; then
        echo "Panel 1 returns data: $row_count rows"
        return 0
    else
        echo "ERROR: Panel 1 returned no data"
        return 1
    fi
}

# Test Panel 2: Positive Sentiment Rate
test_panel_2_positive_sentiment() {
    local result=$(get_panel_data 2)

    if echo "$result" | grep -q '"error"'; then
        echo "ERROR: Query failed"
        return 1
    fi

    local has_data=$(echo "$result" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if 'results' in data and data['results']:
        frames = data['results'].get('A', {}).get('frames', [])
        print('yes' if frames and len(frames) > 0 else 'no')
    else:
        print('no')
except:
    print('no')
" 2>/dev/null || echo "no")

    if [ "$has_data" = "yes" ]; then
        echo "Panel 2 returns data"
        return 0
    else
        echo "ERROR: Panel 2 returned no data"
        return 1
    fi
}

# Test Panel 3: SLA Compliance
test_panel_3_sla_compliance() {
    local result=$(get_panel_data 3)

    if echo "$result" | grep -q '"error"'; then
        echo "ERROR: Query failed"
        return 1
    fi

    local has_data=$(echo "$result" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if 'results' in data and data['results']:
        frames = data['results'].get('A', {}).get('frames', [])
        print('yes' if frames and len(frames) > 0 else 'no')
    else:
        print('no')
except:
    print('no')
" 2>/dev/null || echo "no")

    if [ "$has_data" = "yes" ]; then
        echo "Panel 3 returns data"
        return 0
    else
        echo "ERROR: Panel 3 returned no data"
        return 1
    fi
}

# Test Panel 5: Ranked Team Performance Table
test_panel_5_ranked_performance() {
    local result=$(get_panel_data 5)

    if echo "$result" | grep -q '"error"'; then
        echo "ERROR: Query failed"
        return 1
    fi

    local row_count=$(echo "$result" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if 'results' in data and data['results']:
        frames = data['results'].get('A', {}).get('frames', [])
        if frames and len(frames) > 0:
            # Count rows from first column
            rows = frames[0].get('data', {}).get('values', [[]])[0]
            print(len(rows) if rows else 0)
        else:
            print(0)
    else:
        print(0)
except:
    print(0)
" 2>/dev/null || echo "0")

    if [ "$row_count" -ge 5 ]; then
        echo "Panel 5 returns $row_count team members (expected >= 5)"
        return 0
    else
        echo "ERROR: Panel 5 returned only $row_count rows (expected >= 5)"
        return 1
    fi
}

# Test Panel 6: Positive vs Negative Comments Bar Chart
test_panel_6_sentiment_barchart() {
    local result=$(get_panel_data 6)

    if echo "$result" | grep -q '"error"'; then
        echo "ERROR: Query failed"
        return 1
    fi

    local row_count=$(echo "$result" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if 'results' in data and data['results']:
        frames = data['results'].get('A', {}).get('frames', [])
        if frames and len(frames) > 0:
            rows = frames[0].get('data', {}).get('values', [[]])[0]
            print(len(rows) if rows else 0)
        else:
            print(0)
    else:
        print(0)
except:
    print(0)
" 2>/dev/null || echo "0")

    if [ "$row_count" -ge 5 ]; then
        echo "Panel 6 returns $row_count team members"
        return 0
    else
        echo "ERROR: Panel 6 returned only $row_count rows"
        return 1
    fi
}

# Test Panel 7: Sentiment Trend Time Series
test_panel_7_sentiment_trend() {
    local result=$(get_panel_data 7)

    if echo "$result" | grep -q '"error"'; then
        echo "ERROR: Query failed"
        return 1
    fi

    local row_count=$(echo "$result" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if 'results' in data and data['results']:
        frames = data['results'].get('A', {}).get('frames', [])
        if frames and len(frames) > 0:
            rows = frames[0].get('data', {}).get('values', [[]])[0]
            print(len(rows) if rows else 0)
        else:
            print(0)
    else:
        print(0)
except:
    print(0)
" 2>/dev/null || echo "0")

    if [ "$row_count" -ge 10 ]; then
        echo "Panel 7 returns $row_count time points"
        return 0
    else
        echo "ERROR: Panel 7 returned only $row_count rows (expected >= 10 days)"
        return 1
    fi
}

# Test Panel 10: Recent Positive Comments
test_panel_10_positive_comments() {
    local result=$(get_panel_data 10)

    if echo "$result" | grep -q '"error"'; then
        echo "ERROR: Query failed"
        return 1
    fi

    local row_count=$(echo "$result" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if 'results' in data and data['results']:
        frames = data['results'].get('A', {}).get('frames', [])
        if frames and len(frames) > 0:
            rows = frames[0].get('data', {}).get('values', [[]])[0]
            print(len(rows) if rows else 0)
        else:
            print(0)
    else:
        print(0)
except:
    print(0)
" 2>/dev/null || echo "0")

    if [ "$row_count" -ge 10 ]; then
        echo "Panel 10 returns $row_count positive comments"
        return 0
    else
        echo "ERROR: Panel 10 returned only $row_count comments"
        return 1
    fi
}

# Test Panel 11: Recent Negative Comments
test_panel_11_negative_comments() {
    local result=$(get_panel_data 11)

    if echo "$result" | grep -q '"error"'; then
        echo "ERROR: Query failed"
        return 1
    fi

    local row_count=$(echo "$result" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if 'results' in data and data['results']:
        frames = data['results'].get('A', {}).get('frames', [])
        if frames and len(frames) > 0:
            rows = frames[0].get('data', {}).get('values', [[]])[0]
            print(len(rows) if rows else 0)
        else:
            print(0)
    else:
        print(0)
except:
    print(0)
" 2>/dev/null || echo "0")

    if [ "$row_count" -ge 10 ]; then
        echo "Panel 11 returns $row_count negative comments"
        return 0
    else
        echo "ERROR: Panel 11 returned only $row_count comments"
        return 1
    fi
}

# Main test execution
main() {
    echo "=========================================="
    echo "Dashboard #7 Panel Data Integration Tests"
    echo "Testing via Grafana API (Dashboard #6 lesson)"
    echo "=========================================="

    # Check if Grafana is accessible
    if ! curl -s "$GRAFANA_URL/api/health" > /dev/null 2>&1; then
        echo -e "${RED}ERROR: Grafana is not accessible at $GRAFANA_URL${NC}"
        exit 1
    fi

    # Check if dashboard exists
    local dashboard_check=$(curl -s "$GRAFANA_URL/api/dashboards/uid/$DASHBOARD_UID" \
        -u "$GRAFANA_USER:$GRAFANA_PASS" | grep -q '"uid":"'$DASHBOARD_UID'"' && echo "yes" || echo "no")

    if [ "$dashboard_check" != "yes" ]; then
        echo -e "${RED}ERROR: Dashboard $DASHBOARD_UID not found in Grafana${NC}"
        exit 1
    fi

    echo -e "${GREEN}✓ Dashboard found in Grafana${NC}"

    # Run panel tests
    echo -e "\n${YELLOW}=== TESTING STAT PANELS ===${NC}"
    run_test "Panel 1: Total Customer-Facing Comments" test_panel_1_customer_comments
    run_test "Panel 2: Positive Sentiment Rate" test_panel_2_positive_sentiment
    run_test "Panel 3: Average SLA Compliance" test_panel_3_sla_compliance

    echo -e "\n${YELLOW}=== TESTING TABLE/CHART PANELS ===${NC}"
    run_test "Panel 5: Ranked Team Performance Table" test_panel_5_ranked_performance
    run_test "Panel 6: Sentiment Bar Chart" test_panel_6_sentiment_barchart
    run_test "Panel 7: Sentiment Trend Time Series" test_panel_7_sentiment_trend

    echo -e "\n${YELLOW}=== TESTING FEEDBACK TABLES ===${NC}"
    run_test "Panel 10: Recent Positive Comments" test_panel_10_positive_comments
    run_test "Panel 11: Recent Negative Comments" test_panel_11_negative_comments

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
    echo -e "Pass Rate:    $(python3 -c "print(f'{($TESTS_PASSED/$TESTS_RUN)*100:.1f}%')")"
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
