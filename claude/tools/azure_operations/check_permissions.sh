#!/bin/bash
# Azure Permissions Checker
#
# Purpose: Verify Azure RBAC permissions before running audit scripts
# Tests:
#   1. Resource Graph access (Reader role)
#   2. VM access (VM Contributor role for Run Command)
#
# Author: SRE Principal Engineer Agent
# Created: 2026-01-07
#
# Usage:
#   ./check_permissions.sh [subscription-id]
#   ./check_permissions.sh --all  # Check all accessible subscriptions

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check a single subscription
check_subscription() {
    local SUB_ID="$1"
    local SUB_NAME="$2"

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📋 Subscription: $SUB_NAME"
    echo "   ID: $SUB_ID"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Set subscription context
    az account set --subscription "$SUB_ID" 2>/dev/null

    # Test 1: Resource Graph access (Reader role)
    echo -n "🔍 Resource Graph Query (Reader role)... "
    if RESULT=$(az graph query \
        -q "Resources | where type =~ 'microsoft.compute/virtualmachines' | count" \
        --subscriptions "$SUB_ID" \
        --query "data[0].count_" -o tsv 2>/dev/null); then
        echo -e "${GREEN}✅ PASS${NC} ($RESULT VMs found)"
        GRAPH_OK=1
    else
        echo -e "${RED}❌ FAIL${NC} (need Reader role)"
        GRAPH_OK=0
    fi

    # Test 2: VM listing (Reader role)
    echo -n "💻 VM Listing (Reader role)... "
    if VM_COUNT=$(az vm list --subscription "$SUB_ID" --query "length(@)" -o tsv 2>/dev/null); then
        echo -e "${GREEN}✅ PASS${NC} ($VM_COUNT VMs accessible)"
        VM_LIST_OK=1
    else
        echo -e "${RED}❌ FAIL${NC} (need Reader role)"
        VM_LIST_OK=0
        VM_COUNT=0
    fi

    # Test 3: VM Run Command access (VM Contributor role)
    echo -n "⚡ Run Command (VM Contributor role)... "

    if (( VM_COUNT == 0 )); then
        echo -e "${YELLOW}⚠️  SKIP${NC} (no VMs to test)"
        RUN_CMD_OK=2  # Unknown
    else
        # Find a running Windows VM
        RUNNING_VM=$(az vm list \
            --subscription "$SUB_ID" \
            --query "[?powerState=='VM running' && storageProfile.osDisk.osType=='Windows'] | [0].{id:id, name:name, rg:resourceGroup}" \
            -o json 2>/dev/null)

        if [[ "$RUNNING_VM" == "null" ]] || [[ -z "$RUNNING_VM" ]]; then
            # Try any Windows VM (deallocated)
            TEST_VM=$(az vm list \
                --subscription "$SUB_ID" \
                --query "[?storageProfile.osDisk.osType=='Windows'] | [0].{id:id, name:name, rg:resourceGroup}" \
                -o json 2>/dev/null)

            if [[ "$TEST_VM" == "null" ]] || [[ -z "$TEST_VM" ]]; then
                echo -e "${YELLOW}⚠️  SKIP${NC} (no Windows VMs found)"
                RUN_CMD_OK=2
            else
                VM_NAME=$(echo "$TEST_VM" | jq -r '.name')
                VM_RG=$(echo "$TEST_VM" | jq -r '.rg')

                # Test if we can access the VM (permissions check, not actual run)
                if az vm show --name "$VM_NAME" --resource-group "$VM_RG" --subscription "$SUB_ID" &>/dev/null; then
                    echo -e "${YELLOW}⚠️  PARTIAL${NC} (VM accessible, but deallocated - Run Command requires running VM)"
                    RUN_CMD_OK=2
                else
                    echo -e "${RED}❌ FAIL${NC} (need VM Contributor role)"
                    RUN_CMD_OK=0
                fi
            fi
        else
            VM_NAME=$(echo "$RUNNING_VM" | jq -r '.name')
            VM_RG=$(echo "$RUNNING_VM" | jq -r '.rg')

            # Test actual Run Command execution (minimal script)
            if az vm run-command invoke \
                --resource-group "$VM_RG" \
                --name "$VM_NAME" \
                --command-id RunPowerShellScript \
                --scripts "Write-Output 'Permission test OK'" \
                --subscription "$SUB_ID" \
                --query "value[0].message" -o tsv &>/dev/null; then
                echo -e "${GREEN}✅ PASS${NC} (tested on $VM_NAME)"
                RUN_CMD_OK=1
            else
                echo -e "${RED}❌ FAIL${NC} (need VM Contributor role)"
                RUN_CMD_OK=0
            fi
        fi
    fi

    # Summary
    echo ""
    echo "📊 Summary for $SUB_NAME:"

    if (( GRAPH_OK == 1 && VM_LIST_OK == 1 )); then
        echo -e "   ${GREEN}✅ environment_discovery.sh${NC} - Ready to use"
    else
        echo -e "   ${RED}❌ environment_discovery.sh${NC} - Missing Reader role"
    fi

    if (( GRAPH_OK == 1 && RUN_CMD_OK == 1 )); then
        echo -e "   ${GREEN}✅ vm_disk_audit.sh${NC} - Ready to use (full audit)"
    elif (( GRAPH_OK == 1 && RUN_CMD_OK == 2 )); then
        echo -e "   ${YELLOW}⚠️  vm_disk_audit.sh${NC} - Partial (Phase 1 HDD detection only)"
    else
        echo -e "   ${RED}❌ vm_disk_audit.sh${NC} - Missing Reader or VM Contributor role"
    fi

    echo ""

    # Return summary status
    if (( GRAPH_OK == 1 && RUN_CMD_OK == 1 )); then
        return 0  # Full access
    elif (( GRAPH_OK == 1 )); then
        return 1  # Partial access
    else
        return 2  # No access
    fi
}

# Main script
echo "🔐 Azure Permissions Checker"
echo "============================"
echo ""

# Check if --all flag
if [[ "${1:-}" == "--all" ]]; then
    echo "Checking all accessible subscriptions..."

    # Get all enabled subscriptions
    SUBS=$(az account list --query "[?state=='Enabled']" -o json)
    SUB_COUNT=$(echo "$SUBS" | jq '. | length')

    if (( SUB_COUNT == 0 )); then
        echo "❌ No enabled subscriptions found. Run 'az login' first."
        exit 1
    fi

    echo "Found $SUB_COUNT subscription(s)"

    FULL_ACCESS=0
    PARTIAL_ACCESS=0
    NO_ACCESS=0

    while IFS= read -r sub; do
        SUB_ID=$(echo "$sub" | jq -r '.id')
        SUB_NAME=$(echo "$sub" | jq -r '.name')

        if check_subscription "$SUB_ID" "$SUB_NAME"; then
            ((FULL_ACCESS++)) || true
        elif [[ $? -eq 1 ]]; then
            ((PARTIAL_ACCESS++)) || true
        else
            ((NO_ACCESS++)) || true
        fi
    done < <(echo "$SUBS" | jq -c '.[]')

    # Overall summary
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📊 Overall Summary"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Total subscriptions: $SUB_COUNT"
    echo -e "${GREEN}Full access (Reader + VM Contributor): $FULL_ACCESS${NC}"
    echo -e "${YELLOW}Partial access (Reader only): $PARTIAL_ACCESS${NC}"
    echo -e "${RED}No access: $NO_ACCESS${NC}"
    echo ""

elif [[ -n "${1:-}" ]] && [[ "${1:-}" != "--help" ]]; then
    # Single subscription check
    SUB_ID="$1"

    # Get subscription name
    SUB_NAME=$(az account show --subscription "$SUB_ID" --query "name" -o tsv 2>/dev/null || echo "Unknown")

    check_subscription "$SUB_ID" "$SUB_NAME"

else
    # Help
    cat << 'EOF'
Usage:
  ./check_permissions.sh [subscription-id]
  ./check_permissions.sh --all
  ./check_permissions.sh --help

Examples:
  # Check current subscription
  ./check_permissions.sh $(az account show --query id -o tsv)

  # Check specific subscription
  ./check_permissions.sh 9b8e7b3f-d3e7-4da9-a22a-9bf7c8ee4dde

  # Check all accessible subscriptions
  ./check_permissions.sh --all

Required Permissions:
  - Reader role (subscription-level) - for environment_discovery.sh
  - Virtual Machine Contributor role - for vm_disk_audit.sh Run Command

Tests Performed:
  ✅ Resource Graph query (Reader role)
  ✅ VM listing (Reader role)
  ✅ Run Command execution (VM Contributor role)

Output:
  ✅ PASS - Permission granted
  ❌ FAIL - Permission missing
  ⚠️  PARTIAL/SKIP - Limited access or cannot test
EOF
    exit 0
fi
