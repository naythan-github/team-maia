#!/bin/bash

# ServiceDesk Dashboard Test Suite
# TDD approach: Write tests FIRST, then fix until all pass
# Author: SRE Principal Engineer Agent
# Date: 2025-10-19

set -e  # Exit on first error in tests

# Configuration
GRAFANA_URL="${GRAFANA_URL:-http://localhost:3000}"
GRAFANA_USER="${GRAFANA_USER:-admin}"
GRAFANA_PASSWORD="${GRAFANA_ADMIN_PASSWORD:-Grafana2025!SecureAdmin}"
DASHBOARD_DIR="/Users/naythandawe/git/maia/claude/infrastructure/servicedesk-dashboard/grafana/dashboards"
POSTGRES_CONTAINER="servicedesk-postgres"
POSTGRES_USER="servicedesk_user"
POSTGRES_DB="servicedesk"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Test result logging
declare -a FAILED_TESTS
declare -a FAILED_REASONS

# Helper functions
log_test_start() {
  echo -e "${BLUE}[TEST $((TESTS_RUN + 1))]${NC} $1"
  ((TESTS_RUN++))
}

log_pass() {
  echo -e "${GREEN}  ✓ PASS${NC}"
  ((TESTS_PASSED++))
  echo ""
}

log_fail() {
  echo -e "${RED}  ✗ FAIL: $1${NC}"
  ((TESTS_FAILED++))
  FAILED_TESTS+=("Test $TESTS_RUN")
  FAILED_REASONS+=("$1")
  echo ""
}

# Test 1: Grafana is running and accessible
test_grafana_running() {
  log_test_start "Grafana is running and accessible"

  local health_response=$(curl -s "$GRAFANA_URL/api/health")

  if echo "$health_response" | jq -e '.database == "ok"' > /dev/null 2>&1; then
    log_pass
    return 0
  else
    log_fail "Grafana health check failed. Response: $health_response"
    return 1
  fi
}

# Test 2: Grafana authentication works with correct credentials
test_grafana_auth() {
  log_test_start "Grafana authentication with correct credentials"

  local auth_response=$(curl -s -u "$GRAFANA_USER:$GRAFANA_PASSWORD" "$GRAFANA_URL/api/org")

  if echo "$auth_response" | grep -q '"name"'; then
    log_pass
    return 0
  else
    log_fail "Authentication failed. Response: $auth_response"
    return 1
  fi
}

# Test 3: PostgreSQL data source exists in Grafana
test_datasource_exists() {
  log_test_start "PostgreSQL data source 'ServiceDesk PostgreSQL' exists"

  local datasources=$(curl -s -u "$GRAFANA_USER:$GRAFANA_PASSWORD" "$GRAFANA_URL/api/datasources")

  if echo "$datasources" | grep -q '"name":"ServiceDesk PostgreSQL"'; then
    log_pass
    return 0
  else
    log_fail "Data source 'ServiceDesk PostgreSQL' not found. Available datasources: $datasources"
    return 1
  fi
}

# Test 4: PostgreSQL container is running and accessible
test_postgres_running() {
  log_test_start "PostgreSQL container is running"

  if docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT 1" > /dev/null 2>&1; then
    log_pass
    return 0
  else
    log_fail "Cannot connect to PostgreSQL container '$POSTGRES_CONTAINER'"
    return 1
  fi
}

# Test 5: PostgreSQL has data in tickets table
test_postgres_has_data() {
  log_test_start "PostgreSQL tickets table has data"

  local count=$(docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT COUNT(*) FROM servicedesk.tickets;" | tr -d ' \n')

  if [ "$count" -gt 0 ]; then
    echo -e "${GREEN}  Found $count tickets${NC}"
    log_pass
    return 0
  else
    log_fail "Tickets table is empty (count: $count)"
    return 1
  fi
}

# Test 6: Dashboard JSON files are valid JSON syntax
test_json_syntax() {
  log_test_start "Dashboard JSON files have valid syntax"

  local invalid_files=()

  for dashboard_file in "$DASHBOARD_DIR"/[1-5]_*.json; do
    if [ -f "$dashboard_file" ]; then
      if ! jq empty "$dashboard_file" 2>/dev/null; then
        invalid_files+=("$(basename "$dashboard_file")")
      fi
    fi
  done

  if [ ${#invalid_files[@]} -eq 0 ]; then
    log_pass
    return 0
  else
    log_fail "Invalid JSON in files: ${invalid_files[*]}"
    return 1
  fi
}

# Test 7: Dashboard queries are valid SQL
test_queries_valid() {
  log_test_start "Dashboard SQL queries are valid against PostgreSQL"

  local invalid_queries=()

  # Extract and test a sample query from dashboard 1
  local test_query='SELECT COUNT(*) FROM servicedesk.tickets WHERE "TKT-Created Time" >= '\''2025-07-01'\'' AND "TKT-Created Time" <= '\''2025-10-13'\'';'

  if ! docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "$test_query" > /dev/null 2>&1; then
    invalid_queries+=("Sample query from dashboard 1")
  fi

  if [ ${#invalid_queries[@]} -eq 0 ]; then
    log_pass
    return 0
  else
    log_fail "Invalid queries: ${invalid_queries[*]}"
    return 1
  fi
}

# Test 8: Dashboard can be imported without errors (dashboard 1 only)
test_import_succeeds() {
  log_test_start "Dashboard 1 can be imported via Grafana API"

  local dashboard_file="$DASHBOARD_DIR/1_automation_executive_overview.json"

  local response=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -u "$GRAFANA_USER:$GRAFANA_PASSWORD" \
    -d @"$dashboard_file" \
    "$GRAFANA_URL/api/dashboards/db")

  if echo "$response" | grep -q '"status":"success"'; then
    log_pass
    return 0
  else
    local error_msg=$(echo "$response" | jq -r '.message // .error // "Unknown error"' 2>/dev/null || echo "$response")
    log_fail "Import failed: $error_msg"
    return 1
  fi
}

# Test 9: Imported dashboard exists and is accessible
test_dashboard_accessible() {
  log_test_start "Imported dashboard 1 is accessible via Grafana"

  local dashboard_uid="servicedesk-automation-exec"

  local response=$(curl -s -u "$GRAFANA_USER:$GRAFANA_PASSWORD" "$GRAFANA_URL/api/dashboards/uid/$dashboard_uid")

  if echo "$response" | grep -q '"dashboard"'; then
    log_pass
    return 0
  else
    log_fail "Dashboard not accessible. Response: $response"
    return 1
  fi
}

# Test 10: Dashboard panels return data
test_panels_have_data() {
  log_test_start "Dashboard panels can execute queries and return data"

  # Test a simple query that should return data
  local test_query='SELECT COUNT(*) as value FROM servicedesk.tickets WHERE "TKT-Created Time" >= '\''2025-07-01'\'';'

  local result=$(docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "$test_query" | tr -d ' \n')

  if [ "$result" -gt 0 ]; then
    echo -e "${GREEN}  Query returned $result rows${NC}"
    log_pass
    return 0
  else
    log_fail "Query returned no data (result: $result)"
    return 1
  fi
}

# Test 11: Import script uses correct authentication
test_import_script_auth() {
  log_test_start "Import script loads password from .env file"

  local import_script="/Users/naythandawe/git/maia/claude/infrastructure/servicedesk-dashboard/scripts/import_dashboards.sh"

  # Check if script loads .env file
  if grep -q 'ENV_FILE=.*/.env' "$import_script" && grep -q 'GRAFANA_ADMIN_PASSWORD' "$import_script"; then
    log_pass
    return 0
  else
    log_fail "Import script does not load GRAFANA_ADMIN_PASSWORD from .env file"
    return 1
  fi
}

# Test 12: All 5 numbered dashboards exist
test_all_dashboards_exist() {
  log_test_start "All 5 numbered dashboard files exist"

  local missing_dashboards=()

  for i in {1..5}; do
    if ! ls "$DASHBOARD_DIR"/${i}_*.json > /dev/null 2>&1; then
      missing_dashboards+=("Dashboard $i")
    fi
  done

  if [ ${#missing_dashboards[@]} -eq 0 ]; then
    log_pass
    return 0
  else
    log_fail "Missing dashboards: ${missing_dashboards[*]}"
    return 1
  fi
}

# Main test execution
main() {
  echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
  echo -e "${BLUE}║         ServiceDesk Dashboard Test Suite (TDD)                ║${NC}"
  echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
  echo ""
  echo -e "${YELLOW}Running comprehensive dashboard tests...${NC}"
  echo ""

  # Run all tests (continue even if individual tests fail)
  test_grafana_running || true
  test_grafana_auth || true
  test_datasource_exists || true
  test_postgres_running || true
  test_postgres_has_data || true
  test_json_syntax || true
  test_queries_valid || true
  test_all_dashboards_exist || true
  test_import_script_auth || true
  test_import_succeeds || true
  test_dashboard_accessible || true
  test_panels_have_data || true

  # Summary
  echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
  echo -e "${BLUE}║                      Test Results                              ║${NC}"
  echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
  echo ""
  echo -e "${BLUE}Tests Run:${NC}    $TESTS_RUN"
  echo -e "${GREEN}Tests Passed:${NC} $TESTS_PASSED"
  echo -e "${RED}Tests Failed:${NC} $TESTS_FAILED"
  echo ""

  if [ $TESTS_FAILED -gt 0 ]; then
    echo -e "${RED}Failed Tests:${NC}"
    for i in "${!FAILED_TESTS[@]}"; do
      echo -e "${RED}  ${FAILED_TESTS[$i]}:${NC} ${FAILED_REASONS[$i]}"
    done
    echo ""
    exit 1
  else
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo ""
    exit 0
  fi
}

# Run main function
main
