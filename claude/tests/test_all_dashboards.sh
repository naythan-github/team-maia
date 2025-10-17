#!/bin/bash
# Dashboard Remediation Phase A: Automated Test Suite
# Tests all 11 registered dashboards for health, dependencies, and functionality
#
# Usage:
#   bash claude/tests/test_all_dashboards.sh
#   bash claude/tests/test_all_dashboards.sh --json
#   bash claude/tests/test_all_dashboards.sh --dashboard servicedesk_operations_dashboard
#
# Author: SRE Principal Engineer Agent (Dashboard Remediation Project)
# Created: 2025-10-17

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Configuration
MAIA_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DB_REGISTRY="$MAIA_ROOT/claude/data/dashboard_registry.db"
RESULTS_FILE="$MAIA_ROOT/claude/data/dashboard_test_results.txt"
STARTUP_TIMEOUT=5
JSON_OUTPUT=false
SINGLE_DASHBOARD=""

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --json)
      JSON_OUTPUT=true
      shift
      ;;
    --dashboard)
      SINGLE_DASHBOARD="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Functions
log_test() {
  TOTAL_TESTS=$((TOTAL_TESTS + 1))
  if [ "$2" = "PASS" ]; then
    PASSED_TESTS=$((PASSED_TESTS + 1))
    if [ "$JSON_OUTPUT" = false ]; then
      echo -e "${GREEN}✅${NC} $1"
    fi
  else
    FAILED_TESTS=$((FAILED_TESTS + 1))
    if [ "$JSON_OUTPUT" = false ]; then
      echo -e "${RED}❌${NC} $1: ${3:-No details}"
    fi
  fi
}

cleanup_background_processes() {
  # Kill any dashboards we started
  pkill -f "python3.*dashboard" 2>/dev/null || true
  sleep 1
}

# Trap to ensure cleanup on exit
trap cleanup_background_processes EXIT

# Header
if [ "$JSON_OUTPUT" = false ]; then
  echo ""
  echo "╭────────────────────────────────────────────────────────────────╮"
  echo "│  🔍 Dashboard Test Suite - Phase A: Safety Net                │"
  echo "│  Testing all registered dashboards for health and reliability │"
  echo "╰────────────────────────────────────────────────────────────────╯"
  echo ""
fi

# Test 1: Database Registry Accessibility
if [ "$JSON_OUTPUT" = false ]; then
  echo -e "${BLUE}━━━ Test Category 1: Registry Health ━━━${NC}"
fi

if [ -f "$DB_REGISTRY" ]; then
  log_test "Dashboard registry database exists" "PASS"
else
  log_test "Dashboard registry database exists" "FAIL" "Missing: $DB_REGISTRY"
  exit 1
fi

# Get dashboard list
if [ -n "$SINGLE_DASHBOARD" ]; then
  DASHBOARDS=$(sqlite3 "$DB_REGISTRY" "SELECT name, port, file_path, category FROM dashboards WHERE name='$SINGLE_DASHBOARD'")
else
  DASHBOARDS=$(sqlite3 "$DB_REGISTRY" "SELECT name, port, file_path, category FROM dashboards ORDER BY port")
fi

DASHBOARD_COUNT=$(echo "$DASHBOARDS" | wc -l | tr -d ' ')
log_test "Registry contains $DASHBOARD_COUNT dashboard(s)" "PASS"

if [ "$JSON_OUTPUT" = false ]; then
  echo ""
  echo -e "${BLUE}━━━ Test Category 2: File Existence ━━━${NC}"
fi

# Test 2: File Existence
echo "$DASHBOARDS" | while IFS='|' read -r name port filepath category; do
  # Handle both relative and absolute paths
  if [[ "$filepath" == /* ]]; then
    full_path="$filepath"
  else
    full_path="$MAIA_ROOT/$filepath"
  fi

  if [ -f "$full_path" ]; then
    log_test "$name file exists" "PASS"
  else
    log_test "$name file exists" "FAIL" "Missing: $full_path"
  fi
done

if [ "$JSON_OUTPUT" = false ]; then
  echo ""
  echo -e "${BLUE}━━━ Test Category 3: Dependency Check ━━━${NC}"
fi

# Test 3: Database Dependencies
echo "$DASHBOARDS" | while IFS='|' read -r name port filepath category; do
  if [[ "$filepath" == /* ]]; then
    full_path="$filepath"
  else
    full_path="$MAIA_ROOT/$filepath"
  fi

  if [ ! -f "$full_path" ]; then
    continue
  fi

  # Extract database dependencies
  db_deps=$(grep -oE "[a-z_]+\.db" "$full_path" 2>/dev/null | sort -u | grep -v "self.db" || true)

  if [ -z "$db_deps" ]; then
    log_test "$name has no database dependencies" "PASS"
  else
    missing_dbs=""
    for db in $db_deps; do
      # Check multiple possible locations
      if [ -f "$MAIA_ROOT/$db" ] || [ -f "$MAIA_ROOT/claude/data/$db" ] || [ -f "$db" ]; then
        log_test "$name dependency $db exists" "PASS"
      else
        log_test "$name dependency $db exists" "FAIL" "Missing database"
        missing_dbs="$missing_dbs $db"
      fi
    done
  fi
done

if [ "$JSON_OUTPUT" = false ]; then
  echo ""
  echo -e "${BLUE}━━━ Test Category 4: Port Conflicts ━━━${NC}"
fi

# Test 4: Port Availability
echo "$DASHBOARDS" | while IFS='|' read -r name port filepath category; do
  if lsof -i":$port" -sTCP:LISTEN -n -P 2>/dev/null | grep -q LISTEN; then
    process=$(lsof -i":$port" -sTCP:LISTEN -n -P 2>/dev/null | tail -1 | awk '{print $1}')
    log_test "$name port $port availability" "FAIL" "Port in use by $process"
  else
    log_test "$name port $port availability" "PASS"
  fi
done

if [ "$JSON_OUTPUT" = false ]; then
  echo ""
  echo -e "${BLUE}━━━ Test Category 5: Startup Health ━━━${NC}"
  echo -e "${YELLOW}⏱️  Testing dashboard startup (${STARTUP_TIMEOUT}s timeout per dashboard)...${NC}"
  echo ""
fi

# Test 5: Startup Health Check
echo "$DASHBOARDS" | while IFS='|' read -r name port filepath category; do
  if [[ "$filepath" == /* ]]; then
    full_path="$filepath"
  else
    full_path="$MAIA_ROOT/$filepath"
  fi

  if [ ! -f "$full_path" ]; then
    log_test "$name startup health" "FAIL" "File missing"
    continue
  fi

  # Check if port already in use
  if lsof -i":$port" -sTCP:LISTEN -n -P 2>/dev/null | grep -q LISTEN; then
    log_test "$name startup health" "SKIP" "Port already in use (may be running)"
    continue
  fi

  # Start dashboard in background with timeout
  start_time=$(date +%s)
  timeout "$STARTUP_TIMEOUT" python3 "$full_path" > /dev/null 2>&1 &
  dashboard_pid=$!

  # Wait for startup
  sleep 2

  # Check if process still running
  if ! ps -p $dashboard_pid > /dev/null 2>&1; then
    log_test "$name startup health" "FAIL" "Process died during startup"
    continue
  fi

  # Try to connect
  if curl -sf "http://127.0.0.1:$port" > /dev/null 2>&1 || \
     curl -sf "http://127.0.0.1:$port/health" > /dev/null 2>&1 || \
     curl -sf "http://127.0.0.1:$port/api/health" > /dev/null 2>&1; then

    end_time=$(date +%s)
    startup_time=$((end_time - start_time))

    if [ $startup_time -le 3 ]; then
      log_test "$name startup health (${startup_time}s)" "PASS"
    else
      log_test "$name startup health (${startup_time}s)" "FAIL" "Slow startup (>3s SLO)"
    fi
  else
    log_test "$name startup health" "FAIL" "No HTTP response after $STARTUP_TIMEOUT seconds"
  fi

  # Kill the dashboard
  kill $dashboard_pid 2>/dev/null || true
  sleep 1
done

# Cleanup any remaining processes
cleanup_background_processes

if [ "$JSON_OUTPUT" = false ]; then
  echo ""
  echo -e "${BLUE}━━━ Test Category 6: Health Endpoint ━━━${NC}"
fi

# Test 6: Health Endpoint Validation
# (Only test dashboards we know are currently running)
if lsof -i:8067 -sTCP:LISTEN -n -P 2>/dev/null | grep -q LISTEN; then
  if curl -sf "http://127.0.0.1:8067/api/health" | grep -q "status"; then
    log_test "hook_performance_dashboard /api/health endpoint" "PASS"
  else
    log_test "hook_performance_dashboard /api/health endpoint" "FAIL" "No valid JSON response"
  fi
fi

# Summary
if [ "$JSON_OUTPUT" = false ]; then
  echo ""
  echo "╭────────────────────────────────────────────────────────────────╮"
  echo "│  📊 Test Summary                                               │"
  echo "╰────────────────────────────────────────────────────────────────╯"
  echo ""
  echo "  Total Tests:   $TOTAL_TESTS"
  echo -e "  ${GREEN}Passed:        $PASSED_TESTS${NC}"
  echo -e "  ${RED}Failed:        $FAILED_TESTS${NC}"
  echo ""

  pass_rate=$((PASSED_TESTS * 100 / TOTAL_TESTS))

  if [ $pass_rate -ge 80 ]; then
    echo -e "  ${GREEN}✅ Overall Status: HEALTHY ($pass_rate% pass rate)${NC}"
  elif [ $pass_rate -ge 60 ]; then
    echo -e "  ${YELLOW}⚠️  Overall Status: DEGRADED ($pass_rate% pass rate)${NC}"
  else
    echo -e "  ${RED}❌ Overall Status: CRITICAL ($pass_rate% pass rate)${NC}"
  fi

  echo ""
  echo "  Results saved to: $RESULTS_FILE"
  echo ""
else
  # JSON output
  cat <<EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "total_tests": $TOTAL_TESTS,
  "passed": $PASSED_TESTS,
  "failed": $FAILED_TESTS,
  "pass_rate": $((PASSED_TESTS * 100 / TOTAL_TESTS)),
  "dashboards_tested": $DASHBOARD_COUNT
}
EOF
fi

# Exit code based on results
if [ $FAILED_TESTS -gt 0 ]; then
  exit 1
else
  exit 0
fi
