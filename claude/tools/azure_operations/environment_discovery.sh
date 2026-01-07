#!/bin/bash
# Azure Environment Discovery - Bash/Azure CLI version
# Alternative to environment_discovery.ps1 for systems without PowerShell
#
# Purpose: Discover and document all accessible Azure environments
# Author: SRE Principal Engineer Agent
# Last Updated: 2026-01-07

set -euo pipefail

# Default output path
OUTPUT_PATH="${1:-$HOME/work_projects/azure_operations/inventory/azure_environment_inventory_$(date +%Y%m%d_%H%M%S).md}"

echo "🔍 Discovering Azure environments..." >&2
echo "" >&2

# Get all enabled subscriptions
echo "📋 Querying subscriptions..." >&2
SUBS=$(az account list --query "[?state=='Enabled']" -o json)

if [ "$(echo "$SUBS" | jq '. | length')" -eq 0 ]; then
    echo "❌ No enabled subscriptions found. Run 'az login' first." >&2
    exit 1
fi

SUB_COUNT=$(echo "$SUBS" | jq '. | length')
echo "   Found $SUB_COUNT subscription(s)" >&2
echo "" >&2

# Arrays to store results
declare -a INTERNAL_ENVS
declare -a CUSTOMER_ENVS

# Process each subscription
while IFS= read -r sub; do
    NAME=$(echo "$sub" | jq -r '.name')
    ID=$(echo "$sub" | jq -r '.id')
    TENANT_DOMAIN=$(echo "$sub" | jq -r '.tenantDefaultDomain // "Unknown"')
    TENANT_NAME=$(echo "$sub" | jq -r '.tenantDisplayName // "Unknown"')

    echo "   Processing: $NAME..." >&2

    # Set context
    az account set --subscription "$ID" 2>/dev/null || continue

    # Get resource groups
    RGS=$(az group list --query "[].name" -o tsv 2>/dev/null | tr '\n' ',' | sed 's/,$//' || echo "None")
    RG_COUNT=$(az group list --query "length([])" -o tsv 2>/dev/null || echo "0")

    # Classify environment
    if [[ "$NAME" =~ (Visual Studio|Dev|Test|Sandbox) ]]; then
        ENV_TYPE="Sandbox/Internal"
    elif [[ "$TENANT_DOMAIN" == "Orrogroup.onmicrosoft.com" ]]; then
        ENV_TYPE="Internal"
    else
        ENV_TYPE="Customer"
    fi

    # Build table row
    ROW="| $NAME | $ID | $TENANT_DOMAIN | $RGS |"

    if [ "$ENV_TYPE" = "Customer" ]; then
        CUSTOMER_ENVS+=("$ROW")
    else
        INTERNAL_ENVS+=("$ROW")
    fi

done < <(echo "$SUBS" | jq -c '.[]')

echo "" >&2
echo "📝 Generating markdown inventory..." >&2

# Generate markdown
{
    echo "# Azure Environment Inventory"
    echo ""
    echo "**Generated**: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "**Total Subscriptions**: $SUB_COUNT"
    echo ""
    echo "## Internal/Sandbox Environments"
    echo ""
    echo "| Subscription Name | Subscription ID | Tenant | Resource Groups |"
    echo "|-------------------|-----------------|--------|-----------------|"

    if [ ${#INTERNAL_ENVS[@]} -eq 0 ]; then
        echo "| None | - | - | - |"
    else
        printf '%s\n' "${INTERNAL_ENVS[@]}"
    fi

    echo ""
    echo "## Customer Environments"
    echo ""
    echo "| Subscription Name | Subscription ID | Tenant | Resource Groups |"
    echo "|-------------------|-----------------|--------|-----------------|"

    if [ ${#CUSTOMER_ENVS[@]} -eq 0 ]; then
        echo "| None | - | - | - |"
    else
        printf '%s\n' "${CUSTOMER_ENVS[@]}"
    fi

    echo ""
    echo "---"
    echo ""
    echo "**Discovery Script**: \`claude/tools/azure_operations/environment_discovery.ps1\` (PowerShell) or \`environment_discovery.sh\` (Bash)"
    echo "**Protocol Documentation**: \`claude/context/protocols/azure_environment_discovery.md\`"
} > "$OUTPUT_PATH"

echo "✅ Environment inventory saved to: $OUTPUT_PATH" >&2
echo "" >&2
echo "📊 Summary:" >&2
echo "   Internal/Sandbox: ${#INTERNAL_ENVS[@]}" >&2
echo "   Customer: ${#CUSTOMER_ENVS[@]}" >&2
echo "   Total: $SUB_COUNT" >&2
echo "" >&2
echo "✅ Discovery complete!" >&2
