#!/bin/bash
# Dashboard #6 Incident Classification - TDD Test Suite
# Following strict TDD methodology as demonstrated in test_dashboards.sh

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Dashboard path
DASHBOARD_DIR="/Users/naythandawe/git/maia/claude/infrastructure/servicedesk-dashboard"
DASHBOARD_FILE="$DASHBOARD_DIR/grafana/dashboards/6_incident_classification_breakdown.json"

# Database connection
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="servicedesk"
DB_USER="servicedesk_user"
DB_CONTAINER="servicedesk-postgres"

# Helper function to run SQL query via Docker
run_sql() {
    local query="$1"
    docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -A -c "$query" 2>/dev/null
}

# Helper function to run SQL and get single value
run_sql_value() {
    local query="$1"
    run_sql "$query" | head -1
}

# Helper function to print test result
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

# Test 1: Verify database connection
test_database_connection() {
    local count=$(run_sql_value "SELECT COUNT(*) FROM servicedesk.tickets;")

    if [ -n "$count" ] && [ "$count" -gt 0 ]; then
        print_result "Database Connection" "PASS" "Found $count tickets in database"
    else
        print_result "Database Connection" "FAIL" "Cannot connect to database or no tickets found"
    fi
}

# Test 2: Primary classification query executes without error
test_classification_query_valid() {
    local query="
    WITH classified AS (
      SELECT
        CASE
          WHEN LOWER(COALESCE(\"TKT-Title\",'') || ' ' || COALESCE(\"TKT-Description\",''))
               LIKE ANY(ARRAY['%network drive%','%share%','%file server%','%shared drive%','%file share%'])
          THEN 'Cloud'

          WHEN LOWER(COALESCE(\"TKT-Title\",'') || ' ' || COALESCE(\"TKT-Description\",''))
               LIKE ANY(ARRAY['%phone%','%pbx%','%call%','%voip%','%teams meeting%','%meeting room%'])
          THEN 'Telecommunications'

          WHEN LOWER(COALESCE(\"TKT-Title\",'') || ' ' || COALESCE(\"TKT-Description\",''))
               LIKE ANY(ARRAY['%vpn%','%firewall%','%switch%','%router%','%wifi%','%wi-fi%','%access point%','%ethernet%'])
          THEN 'Networking'

          ELSE 'Cloud'
        END AS category
      FROM servicedesk.tickets
      WHERE \"TKT-Category\" <> 'Alert'
      AND \"TKT-Created Time\" >= '2025-07-01'
    )
    SELECT COUNT(DISTINCT category) FROM classified;
    "

    local category_count=$(run_sql_value "$query")

    if [ "$category_count" = "3" ]; then
        print_result "Classification Query Valid" "PASS" "Returns 3 categories as expected"
    else
        print_result "Classification Query Valid" "FAIL" "Expected 3 categories, got $category_count"
    fi
}

# Test 3: Classification percentages are within expected ranges
test_classification_percentages() {
    local query="
    WITH classified AS (
      SELECT
        CASE
          WHEN LOWER(COALESCE(\"TKT-Title\",'') || ' ' || COALESCE(\"TKT-Description\",''))
               LIKE ANY(ARRAY['%network drive%','%share%','%file server%','%shared drive%','%file share%'])
          THEN 'Cloud'

          WHEN LOWER(COALESCE(\"TKT-Title\",'') || ' ' || COALESCE(\"TKT-Description\",''))
               LIKE ANY(ARRAY['%phone%','%pbx%','%call%','%voip%','%teams meeting%','%meeting room%'])
          THEN 'Telecommunications'

          WHEN LOWER(COALESCE(\"TKT-Title\",'') || ' ' || COALESCE(\"TKT-Description\",''))
               LIKE ANY(ARRAY['%vpn%','%firewall%','%switch%','%router%','%wifi%','%wi-fi%','%access point%','%ethernet%'])
          THEN 'Networking'

          ELSE 'Cloud'
        END AS category
      FROM servicedesk.tickets
      WHERE \"TKT-Category\" <> 'Alert'
      AND \"TKT-Created Time\" >= '2025-07-01'
    )
    SELECT category, ROUND(COUNT(*)*100.0/(SELECT COUNT(*) FROM classified), 2) as percentage
    FROM classified
    GROUP BY category
    ORDER BY category;
    "

    local results=$(run_sql "$query")
    local cloud_pct=$(echo "$results" | grep "Cloud" | cut -d'|' -f2)
    local network_pct=$(echo "$results" | grep "Networking" | cut -d'|' -f2)
    local telecom_pct=$(echo "$results" | grep "Telecommunications" | cut -d'|' -f2)

    # Expected ranges (±5% tolerance): Cloud: 73-83%, Telecom: 13-23%, Networking: 0-8%
    local pass=true
    local msg=""

    if (( $(echo "$cloud_pct < 73 || $cloud_pct > 83" | bc -l) )); then
        pass=false
        msg="${msg}Cloud: $cloud_pct% (expected 73-83%); "
    fi

    if (( $(echo "$telecom_pct < 13 || $telecom_pct > 23" | bc -l) )); then
        pass=false
        msg="${msg}Telecom: $telecom_pct% (expected 13-23%); "
    fi

    if (( $(echo "$network_pct < 0 || $network_pct > 8" | bc -l) )); then
        pass=false
        msg="${msg}Networking: $network_pct% (expected 0-8%); "
    fi

    if [ "$pass" = true ]; then
        print_result "Classification Percentages" "PASS" "Cloud: $cloud_pct%, Telecom: $telecom_pct%, Networking: $network_pct%"
    else
        print_result "Classification Percentages" "FAIL" "$msg"
    fi
}

# Test 4: Networking sub-categories query returns expected categories
test_networking_subcategories() {
    local query="
    WITH networking_tickets AS (
      SELECT \"TKT-Title\", \"TKT-Description\"
      FROM servicedesk.tickets
      WHERE \"TKT-Category\" <> 'Alert'
      AND \"TKT-Created Time\" >= '2025-07-01'
      AND LOWER(COALESCE(\"TKT-Title\",'') || ' ' || COALESCE(\"TKT-Description\",''))
          NOT LIKE ANY(ARRAY['%network drive%','%share%','%file server%','%shared drive%','%file share%'])
      AND LOWER(COALESCE(\"TKT-Title\",'') || ' ' || COALESCE(\"TKT-Description\",''))
          LIKE ANY(ARRAY['%vpn%','%firewall%','%switch%','%router%','%wifi%','%wi-fi%','%access point%','%ethernet%'])
    )
    SELECT COUNT(DISTINCT
      CASE
        WHEN LOWER(COALESCE(\"TKT-Title\",'') || ' ' || COALESCE(\"TKT-Description\",'')) LIKE '%vpn%' THEN 'VPN Issues'
        WHEN LOWER(COALESCE(\"TKT-Title\",'') || ' ' || COALESCE(\"TKT-Description\",'')) LIKE '%firewall%' THEN 'Firewall'
        WHEN LOWER(COALESCE(\"TKT-Title\",'') || ' ' || COALESCE(\"TKT-Description\",'')) LIKE '%switch%' OR
             LOWER(COALESCE(\"TKT-Title\",'') || ' ' || COALESCE(\"TKT-Description\",'')) LIKE '%router%' THEN 'Switch/Router Hardware'
        WHEN LOWER(COALESCE(\"TKT-Title\",'') || ' ' || COALESCE(\"TKT-Description\",'')) LIKE '%wifi%' OR
             LOWER(COALESCE(\"TKT-Title\",'') || ' ' || COALESCE(\"TKT-Description\",'')) LIKE '%wi-fi%' OR
             LOWER(COALESCE(\"TKT-Title\",'') || ' ' || COALESCE(\"TKT-Description\",'')) LIKE '%access point%' THEN 'WiFi Connectivity'
        WHEN LOWER(COALESCE(\"TKT-Title\",'') || ' ' || COALESCE(\"TKT-Description\",'')) LIKE '%ethernet%' THEN 'Ethernet/Cabling'
        ELSE 'Other Networking'
      END
    ) FROM networking_tickets;
    "

    local subcat_count=$(run_sql_value "$query")

    if [ "$subcat_count" -ge "4" ]; then
        print_result "Networking Sub-categories" "PASS" "Found $subcat_count sub-categories"
    else
        print_result "Networking Sub-categories" "FAIL" "Expected at least 4 sub-categories, got $subcat_count"
    fi
}

# Test 5: Telecommunications sub-categories query returns expected categories
test_telecom_subcategories() {
    local query="
    WITH telecom_tickets AS (
      SELECT \"TKT-Title\", \"TKT-Description\"
      FROM servicedesk.tickets
      WHERE \"TKT-Category\" <> 'Alert'
      AND \"TKT-Created Time\" >= '2025-07-01'
      AND LOWER(COALESCE(\"TKT-Title\",'') || ' ' || COALESCE(\"TKT-Description\",''))
          LIKE ANY(ARRAY['%phone%','%pbx%','%call%','%voip%','%teams meeting%','%meeting room%'])
    )
    SELECT COUNT(DISTINCT
      CASE
        WHEN LOWER(COALESCE(\"TKT-Title\",'') || ' ' || COALESCE(\"TKT-Description\",'')) LIKE '%phone%'
             OR LOWER(COALESCE(\"TKT-Title\",'') || ' ' || COALESCE(\"TKT-Description\",'')) LIKE '%call%' THEN 'Calling Issues'
        WHEN LOWER(COALESCE(\"TKT-Title\",'') || ' ' || COALESCE(\"TKT-Description\",'')) LIKE '%pbx%' THEN 'PBX System'
        WHEN LOWER(COALESCE(\"TKT-Title\",'') || ' ' || COALESCE(\"TKT-Description\",'')) LIKE '%voip%' THEN 'VoIP'
        WHEN LOWER(COALESCE(\"TKT-Title\",'') || ' ' || COALESCE(\"TKT-Description\",'')) LIKE '%teams meeting%'
             OR LOWER(COALESCE(\"TKT-Title\",'') || ' ' || COALESCE(\"TKT-Description\",'')) LIKE '%meeting room%' THEN 'Conference/Meeting Rooms'
        ELSE 'Other Telecom'
      END
    ) FROM telecom_tickets;
    "

    local subcat_count=$(run_sql_value "$query")

    if [ "$subcat_count" -ge "3" ]; then
        print_result "Telecom Sub-categories" "PASS" "Found $subcat_count sub-categories"
    else
        print_result "Telecom Sub-categories" "FAIL" "Expected at least 3 sub-categories, got $subcat_count"
    fi
}

# Test 6: File shares are classified as Cloud, NOT Networking/Telecom
test_file_shares_in_cloud() {
    local query="
    WITH file_share_tickets AS (
      SELECT
        CASE
          WHEN LOWER(COALESCE(\"TKT-Title\",'') || ' ' || COALESCE(\"TKT-Description\",''))
               LIKE ANY(ARRAY['%network drive%','%share%','%file server%','%shared drive%','%file share%'])
          THEN 'Cloud'

          WHEN LOWER(COALESCE(\"TKT-Title\",'') || ' ' || COALESCE(\"TKT-Description\",''))
               LIKE ANY(ARRAY['%phone%','%pbx%','%call%','%voip%','%teams meeting%','%meeting room%'])
          THEN 'Telecommunications'

          WHEN LOWER(COALESCE(\"TKT-Title\",'') || ' ' || COALESCE(\"TKT-Description\",''))
               LIKE ANY(ARRAY['%vpn%','%firewall%','%switch%','%router%','%wifi%','%wi-fi%','%access point%','%ethernet%'])
          THEN 'Networking'

          ELSE 'Cloud'
        END AS category
      FROM servicedesk.tickets
      WHERE \"TKT-Category\" <> 'Alert'
      AND \"TKT-Created Time\" >= '2025-07-01'
      AND LOWER(COALESCE(\"TKT-Title\",'') || ' ' || COALESCE(\"TKT-Description\",''))
          LIKE ANY(ARRAY['%network drive%','%share%','%file server%','%shared drive%','%file share%'])
    )
    SELECT category, COUNT(*) FROM file_share_tickets GROUP BY category;
    "

    local results=$(run_sql "$query")
    local cloud_count=$(echo "$results" | grep "Cloud" | cut -d'|' -f2 || echo "0")
    local other_lines=$(echo "$results" | grep -v "Cloud" | wc -l | tr -d ' ')

    if [ "$cloud_count" -gt 0 ] && [ "$other_lines" = "0" ]; then
        print_result "File Shares in Cloud" "PASS" "All $cloud_count file share tickets classified as Cloud"
    else
        print_result "File Shares in Cloud" "FAIL" "File shares found in non-Cloud categories (Cloud: $cloud_count, Others: $other_lines lines)"
    fi
}

# Test 7: Dashboard JSON file exists and is valid
test_dashboard_json_valid() {
    if [ ! -f "$DASHBOARD_FILE" ]; then
        print_result "Dashboard JSON Valid" "FAIL" "Dashboard file not found: $DASHBOARD_FILE"
        return
    fi

    if jq empty "$DASHBOARD_FILE" 2>/dev/null; then
        print_result "Dashboard JSON Valid" "PASS" "Dashboard JSON is valid"
    else
        print_result "Dashboard JSON Valid" "FAIL" "Dashboard JSON is invalid or malformed"
    fi
}

# Test 8: Dashboard has expected number of panels
test_dashboard_has_panels() {
    if [ ! -f "$DASHBOARD_FILE" ]; then
        print_result "Dashboard Panel Count" "FAIL" "Dashboard file not found"
        return
    fi

    local panel_count=$(jq '[.dashboard.panels[]? // .panels[]?] | length' "$DASHBOARD_FILE" 2>/dev/null)

    if [ "$panel_count" -ge "8" ]; then
        print_result "Dashboard Panel Count" "PASS" "Dashboard has $panel_count panels"
    else
        print_result "Dashboard Panel Count" "FAIL" "Expected at least 8 panels, found $panel_count"
    fi
}

# Test 9: Dashboard can be imported via Grafana API
test_dashboard_import() {
    if [ ! -f "$DASHBOARD_FILE" ]; then
        print_result "Dashboard Import" "FAIL" "Dashboard file not found"
        return
    fi

    # Check if Grafana is running
    if ! curl -s http://localhost:3000/api/health >/dev/null 2>&1; then
        print_result "Dashboard Import" "FAIL" "Grafana is not running on localhost:3000"
        return
    fi

    # Note: Actual import test would require credentials, just verify structure for now
    local has_dashboard=$(jq 'has("dashboard") or has("panels")' "$DASHBOARD_FILE" 2>/dev/null)

    if [ "$has_dashboard" = "true" ]; then
        print_result "Dashboard Import Structure" "PASS" "Dashboard has valid import structure"
    else
        print_result "Dashboard Import Structure" "FAIL" "Dashboard missing required structure"
    fi
}

# Test 10: Query performance is acceptable (<500ms)
test_performance() {
    local query="
    EXPLAIN ANALYZE
    WITH classified AS (
      SELECT
        CASE
          WHEN LOWER(COALESCE(\"TKT-Title\",'') || ' ' || COALESCE(\"TKT-Description\",''))
               LIKE ANY(ARRAY['%network drive%','%share%','%file server%','%shared drive%','%file share%'])
          THEN 'Cloud'

          WHEN LOWER(COALESCE(\"TKT-Title\",'') || ' ' || COALESCE(\"TKT-Description\",''))
               LIKE ANY(ARRAY['%phone%','%pbx%','%call%','%voip%','%teams meeting%','%meeting room%'])
          THEN 'Telecommunications'

          WHEN LOWER(COALESCE(\"TKT-Title\",'') || ' ' || COALESCE(\"TKT-Description\",''))
               LIKE ANY(ARRAY['%vpn%','%firewall%','%switch%','%router%','%wifi%','%wi-fi%','%access point%','%ethernet%'])
          THEN 'Networking'

          ELSE 'Cloud'
        END AS category
      FROM servicedesk.tickets
      WHERE \"TKT-Category\" <> 'Alert'
      AND \"TKT-Created Time\" >= '2025-07-01'
    )
    SELECT category, COUNT(*) FROM classified GROUP BY category;
    "

    local exec_time=$(run_sql "$query" | grep "Execution Time" | awk '{print $3}')

    if [ -n "$exec_time" ]; then
        local exec_time_ms=$(echo "$exec_time" | bc)
        if (( $(echo "$exec_time_ms < 500" | bc -l) )); then
            print_result "Query Performance" "PASS" "Execution time: ${exec_time}ms (< 500ms)"
        else
            print_result "Query Performance" "FAIL" "Execution time: ${exec_time}ms (>= 500ms)"
        fi
    else
        print_result "Query Performance" "FAIL" "Could not measure execution time"
    fi
}

# Main execution
echo "=========================================="
echo "Dashboard #6 Classification - TDD Test Suite"
echo "=========================================="
echo ""

# Run all tests
test_database_connection
test_classification_query_valid
test_classification_percentages
test_networking_subcategories
test_telecom_subcategories
test_file_shares_in_cloud
test_dashboard_json_valid
test_dashboard_has_panels
test_dashboard_import
test_performance

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
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed.${NC}"
    exit 1
fi
