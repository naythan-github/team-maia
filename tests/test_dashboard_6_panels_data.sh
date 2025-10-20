#!/bin/bash
# Dashboard #6 - REAL Panel Data Verification Test
# Tests that panels actually return data via Grafana API (not just JSON validity)

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Grafana config
GRAFANA_URL="http://localhost:3000"
GRAFANA_USER="admin"
GRAFANA_PASSWORD="Grafana2025!SecureAdmin"
DASHBOARD_UID="servicedesk-incident-classification"
DATASOURCE_UID="P6BECECF7273D15EE"

# Time range (matches dashboard default)
TIME_FROM="2025-07-01T00:00:00.000Z"
TIME_TO="now"

print_result() {
    local test_name="$1"
    local status="$2"
    local message="$3"

    TESTS_RUN=$((TESTS_RUN + 1))

    if [ "$status" = "PASS" ]; then
        echo -e "${GREEN}✓${NC} $test_name: PASS"
        [ -n "$message" ] && echo "  $message"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗${NC} $test_name: FAIL"
        echo "  $message"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Test Grafana API connectivity
test_grafana_connectivity() {
    local response=$(curl -s -u "$GRAFANA_USER:$GRAFANA_PASSWORD" "$GRAFANA_URL/api/health")
    local status=$(echo "$response" | jq -r '.database' 2>/dev/null || echo "error")

    if [ "$status" = "ok" ]; then
        print_result "Grafana API Connectivity" "PASS" "Grafana is running and healthy"
    else
        print_result "Grafana API Connectivity" "FAIL" "Grafana health check failed"
    fi
}

# Test that dashboard exists
test_dashboard_exists() {
    local response=$(curl -s -u "$GRAFANA_USER:$GRAFANA_PASSWORD" \
        "$GRAFANA_URL/api/dashboards/uid/$DASHBOARD_UID")
    local uid=$(echo "$response" | jq -r '.dashboard.uid' 2>/dev/null || echo "error")

    if [ "$uid" = "$DASHBOARD_UID" ]; then
        print_result "Dashboard Exists" "PASS" "Dashboard UID: $uid"
    else
        print_result "Dashboard Exists" "FAIL" "Dashboard not found or error retrieving it"
    fi
}

# Helper: Query a panel via Grafana API and check for data
query_panel() {
    local panel_id="$1"
    local panel_name="$2"

    # Get dashboard to extract panel query
    local dashboard=$(curl -s -u "$GRAFANA_USER:$GRAFANA_PASSWORD" \
        "$GRAFANA_URL/api/dashboards/uid/$DASHBOARD_UID")

    local raw_sql=$(echo "$dashboard" | jq -r ".dashboard.panels[] | select(.id == $panel_id) | .targets[0].rawSql" 2>/dev/null)

    if [ -z "$raw_sql" ] || [ "$raw_sql" = "null" ]; then
        print_result "Panel $panel_id: $panel_name" "FAIL" "Could not extract query from dashboard JSON"
        return
    fi

    # Execute query directly via datasource API
    local query_payload=$(jq -n \
        --arg sql "$raw_sql" \
        --arg from "$TIME_FROM" \
        --arg to "$TIME_TO" \
        '{
            "queries": [{
                "refId": "A",
                "datasource": {"type": "postgres", "uid": "'$DATASOURCE_UID'"},
                "rawSql": $sql,
                "format": "table"
            }],
            "from": $from,
            "to": $to
        }')

    local response=$(curl -s -u "$GRAFANA_USER:$GRAFANA_PASSWORD" \
        -X POST \
        -H "Content-Type: application/json" \
        -d "$query_payload" \
        "$GRAFANA_URL/api/ds/query")

    # Check if response has data
    local has_data=$(echo "$response" | jq -r '.results.A.frames[0].data.values[0] | length' 2>/dev/null || echo "0")

    if [ "$has_data" -gt 0 ]; then
        print_result "Panel $panel_id: $panel_name" "PASS" "Returns $has_data data points"
    else
        # Check for errors
        local error=$(echo "$response" | jq -r '.results.A.error // .message // "Unknown error"' 2>/dev/null)
        print_result "Panel $panel_id: $panel_name" "FAIL" "No data returned. Error: $error"
    fi
}

# Test all 10 panels
test_panel_1_primary_classification() {
    query_panel 1 "Primary Incident Classification (Cloud/Telecom/Networking)"
}

test_panel_2_cloud_incidents() {
    query_panel 2 "Cloud Incidents"
}

test_panel_3_telecom_incidents() {
    query_panel 3 "Telecommunications Incidents"
}

test_panel_4_networking_incidents() {
    query_panel 4 "Networking Incidents"
}

test_panel_5_classification_trends() {
    query_panel 5 "Classification Trends Over Time"
}

test_panel_6_networking_subcategories() {
    query_panel 6 "Networking Sub-Categories"
}

test_panel_7_telecom_subcategories() {
    query_panel 7 "Telecommunications Sub-Categories"
}

test_panel_8_file_share_incidents() {
    query_panel 8 "File Share Incidents (Cloud Category)"
}

test_panel_9_recent_networking() {
    query_panel 9 "Recent Networking Incidents"
}

test_panel_10_recent_telecom() {
    query_panel 10 "Recent Telecommunications Incidents"
}

# Main execution
echo "=========================================="
echo "Dashboard #6 - REAL Panel Data Tests"
echo "Testing via Grafana API (not just JSON validity)"
echo "=========================================="
echo ""

# Run all tests
test_grafana_connectivity
test_dashboard_exists
test_panel_1_primary_classification
test_panel_2_cloud_incidents
test_panel_3_telecom_incidents
test_panel_4_networking_incidents
test_panel_5_classification_trends
test_panel_6_networking_subcategories
test_panel_7_telecom_subcategories
test_panel_8_file_share_incidents
test_panel_9_recent_networking
test_panel_10_recent_telecom

# Print summary
echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo "Tests Run:    $TESTS_RUN"
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All panels return data!${NC}"
    echo "Dashboard is working correctly in Grafana."
    exit 0
else
    echo -e "${RED}✗ Some panels are not returning data${NC}"
    echo "Open http://localhost:3000/d/$DASHBOARD_UID to inspect manually."
    exit 1
fi
