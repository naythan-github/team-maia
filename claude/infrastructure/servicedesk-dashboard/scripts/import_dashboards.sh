#!/bin/bash

# ServiceDesk Dashboard Import Script
# Imports all 5 automation analytics dashboards into Grafana
# Author: SRE Principal Engineer Agent
# Date: 2025-10-19

set -e  # Exit on error

# Configuration
GRAFANA_URL="${GRAFANA_URL:-http://localhost:3000}"
GRAFANA_USER="${GRAFANA_USER:-admin}"

# Load password from .env if available
SCRIPT_DIR="$(dirname "$0")"
ENV_FILE="$SCRIPT_DIR/../.env"
if [ -f "$ENV_FILE" ]; then
  export $(grep -v '^#' "$ENV_FILE" | grep GRAFANA_ADMIN_PASSWORD | xargs)
fi
GRAFANA_PASSWORD="${GRAFANA_ADMIN_PASSWORD:-admin}"

DASHBOARD_DIR="$(dirname "$0")/../grafana/dashboards"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   ServiceDesk Automation Analytics Dashboard Import           ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if Grafana is accessible
echo -e "${YELLOW}Checking Grafana connectivity...${NC}"
if ! curl -s -f -u "$GRAFANA_USER:$GRAFANA_PASSWORD" "$GRAFANA_URL/api/health" > /dev/null; then
  echo -e "${RED}✗ Error: Cannot connect to Grafana at $GRAFANA_URL${NC}"
  echo -e "${RED}  Please ensure Grafana is running: docker ps | grep grafana${NC}"
  exit 1
fi
echo -e "${GREEN}✓ Grafana is accessible${NC}"
echo ""

# Check if dashboard directory exists
if [ ! -d "$DASHBOARD_DIR" ]; then
  echo -e "${RED}✗ Error: Dashboard directory not found: $DASHBOARD_DIR${NC}"
  exit 1
fi

# Count dashboards
DASHBOARD_COUNT=$(ls -1 "$DASHBOARD_DIR"/*.json 2>/dev/null | wc -l | tr -d ' ')
if [ "$DASHBOARD_COUNT" -eq 0 ]; then
  echo -e "${RED}✗ Error: No dashboard JSON files found in $DASHBOARD_DIR${NC}"
  exit 1
fi

echo -e "${BLUE}Found $DASHBOARD_COUNT dashboards to import${NC}"
echo ""

# Import each dashboard
SUCCESS_COUNT=0
FAIL_COUNT=0

for dashboard_file in "$DASHBOARD_DIR"/*.json; do
  dashboard_name=$(basename "$dashboard_file")
  echo -e "${YELLOW}Importing: $dashboard_name${NC}"

  # Import dashboard
  response=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -u "$GRAFANA_USER:$GRAFANA_PASSWORD" \
    -d @"$dashboard_file" \
    "$GRAFANA_URL/api/dashboards/db")

  # Check response
  if echo "$response" | grep -q '"status":"success"'; then
    dashboard_uid=$(echo "$response" | grep -o '"uid":"[^"]*"' | cut -d'"' -f4)
    dashboard_url="$GRAFANA_URL/d/$dashboard_uid"
    echo -e "${GREEN}  ✓ Success: $dashboard_url${NC}"
    ((SUCCESS_COUNT++))
  else
    echo -e "${RED}  ✗ Failed: $(echo "$response" | grep -o '"message":"[^"]*"' | cut -d'"' -f4)${NC}"
    ((FAIL_COUNT++))
  fi
  echo ""
done

# Summary
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    Import Summary                              ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}✓ Successfully imported: $SUCCESS_COUNT dashboards${NC}"
if [ $FAIL_COUNT -gt 0 ]; then
  echo -e "${RED}✗ Failed to import: $FAIL_COUNT dashboards${NC}"
fi
echo ""

if [ $SUCCESS_COUNT -gt 0 ]; then
  echo -e "${BLUE}Dashboard URLs:${NC}"
  echo -e "${GREEN}1. Automation Executive Overview:${NC}"
  echo -e "   $GRAFANA_URL/d/servicedesk-automation-exec"
  echo ""
  echo -e "${GREEN}2. Alert Analysis Deep-Dive:${NC}"
  echo -e "   $GRAFANA_URL/d/servicedesk-alert-analysis"
  echo ""
  echo -e "${GREEN}3. Support Pattern Analysis:${NC}"
  echo -e "   $GRAFANA_URL/d/servicedesk-support-patterns"
  echo ""
  echo -e "${GREEN}4. Team Performance & Task-Level:${NC}"
  echo -e "   $GRAFANA_URL/d/servicedesk-team-performance"
  echo ""
  echo -e "${GREEN}5. Improvement Tracking & ROI:${NC}"
  echo -e "   $GRAFANA_URL/d/servicedesk-improvement-tracking"
  echo ""
  echo -e "${BLUE}Access Grafana at: $GRAFANA_URL${NC}"
  echo -e "${BLUE}Login: $GRAFANA_USER / (password from .env)${NC}"
  echo ""
fi

exit $FAIL_COUNT
