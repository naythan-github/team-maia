#!/bin/bash
# Setup Azure VM Idle Shutdown Automation
# Purpose: Complete setup for activity-based VM shutdown
# Version: 1.0

set -e

# ============================================================================
# CONFIGURATION - Update these values for your environment
# ============================================================================

SUBSCRIPTION_ID="YOUR_SUBSCRIPTION_ID"
RESOURCE_GROUP="YOUR_RESOURCE_GROUP"
VM_NAME="YOUR_VM_NAME"
LOCATION="australiaeast"  # or your preferred region

# Automation Account settings
AUTOMATION_ACCOUNT_NAME="vm-idle-shutdown-automation"
RUNBOOK_NAME="Stop-IdleVM"

# Alert settings
ALERT_NAME="vm-idle-alert-${VM_NAME}"
ACTION_GROUP_NAME="vm-idle-shutdown-actions"

# Thresholds
IDLE_CPU_THRESHOLD=5        # Percentage
IDLE_NETWORK_THRESHOLD=100  # KB
IDLE_DURATION_MINUTES=30    # How long idle before shutdown

# ============================================================================
# Script Start
# ============================================================================

echo "=========================================="
echo "Azure VM Idle Shutdown Setup"
echo "=========================================="
echo ""
echo "Configuration:"
echo "  Subscription: $SUBSCRIPTION_ID"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  VM: $VM_NAME"
echo "  Location: $LOCATION"
echo "  Idle CPU Threshold: ${IDLE_CPU_THRESHOLD}%"
echo "  Idle Duration: ${IDLE_DURATION_MINUTES} minutes"
echo ""

read -p "Continue with setup? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Setup cancelled"
    exit 0
fi

# Set active subscription
echo ""
echo "Step 1: Setting active subscription..."
az account set --subscription "$SUBSCRIPTION_ID"
echo "✅ Subscription set"

# Create Automation Account
echo ""
echo "Step 2: Creating Automation Account..."
az automation account create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$AUTOMATION_ACCOUNT_NAME" \
    --location "$LOCATION" \
    --sku Basic \
    || echo "⚠️  Automation Account may already exist"
echo "✅ Automation Account ready"

# Enable Managed Identity
echo ""
echo "Step 3: Enabling Managed Identity..."
az automation account update \
    --resource-group "$RESOURCE_GROUP" \
    --name "$AUTOMATION_ACCOUNT_NAME" \
    --set identity.type=SystemAssigned
echo "✅ Managed Identity enabled"

# Get Managed Identity Principal ID
echo ""
echo "Step 4: Retrieving Managed Identity Principal ID..."
PRINCIPAL_ID=$(az automation account show \
    --resource-group "$RESOURCE_GROUP" \
    --name "$AUTOMATION_ACCOUNT_NAME" \
    --query identity.principalId -o tsv)
echo "✅ Principal ID: $PRINCIPAL_ID"

# Assign Contributor role to Automation Account on the VM
echo ""
echo "Step 5: Assigning RBAC permissions..."
VM_ID=$(az vm show -g "$RESOURCE_GROUP" -n "$VM_NAME" --query id -o tsv)

az role assignment create \
    --assignee "$PRINCIPAL_ID" \
    --role "Virtual Machine Contributor" \
    --scope "$VM_ID"

az role assignment create \
    --assignee "$PRINCIPAL_ID" \
    --role "Monitoring Reader" \
    --scope "$VM_ID"

echo "✅ RBAC permissions granted"

# Import required PowerShell modules
echo ""
echo "Step 6: Importing PowerShell modules..."
az automation module create \
    --resource-group "$RESOURCE_GROUP" \
    --automation-account-name "$AUTOMATION_ACCOUNT_NAME" \
    --name "Az.Accounts" \
    --content-link uri="https://www.powershellgallery.com/api/v2/package/Az.Accounts"

az automation module create \
    --resource-group "$RESOURCE_GROUP" \
    --automation-account-name "$AUTOMATION_ACCOUNT_NAME" \
    --name "Az.Compute" \
    --content-link uri="https://www.powershellgallery.com/api/v2/package/Az.Compute"

az automation module create \
    --resource-group "$RESOURCE_GROUP" \
    --automation-account-name "$AUTOMATION_ACCOUNT_NAME" \
    --name "Az.Monitor" \
    --content-link uri="https://www.powershellgallery.com/api/v2/package/Az.Monitor"

echo "✅ PowerShell modules imported (may take 5-10 minutes to complete)"

# Create runbook
echo ""
echo "Step 7: Creating runbook..."

RUNBOOK_PATH="$(dirname "$0")/azure_vm_idle_shutdown_runbook.ps1"

if [ ! -f "$RUNBOOK_PATH" ]; then
    echo "❌ Error: Runbook file not found at $RUNBOOK_PATH"
    exit 1
fi

az automation runbook create \
    --resource-group "$RESOURCE_GROUP" \
    --automation-account-name "$AUTOMATION_ACCOUNT_NAME" \
    --name "$RUNBOOK_NAME" \
    --type "PowerShell" \
    --location "$LOCATION"

# Upload runbook content
az automation runbook replace-content \
    --resource-group "$RESOURCE_GROUP" \
    --automation-account-name "$AUTOMATION_ACCOUNT_NAME" \
    --name "$RUNBOOK_NAME" \
    --content "@${RUNBOOK_PATH}"

# Publish runbook
az automation runbook publish \
    --resource-group "$RESOURCE_GROUP" \
    --automation-account-name "$AUTOMATION_ACCOUNT_NAME" \
    --name "$RUNBOOK_NAME"

echo "✅ Runbook created and published"

# Create webhook for the runbook
echo ""
echo "Step 8: Creating webhook..."
WEBHOOK_URI=$(az automation webhook create \
    --resource-group "$RESOURCE_GROUP" \
    --automation-account-name "$AUTOMATION_ACCOUNT_NAME" \
    --name "vm-idle-webhook" \
    --runbook-name "$RUNBOOK_NAME" \
    --expiry-time "$(date -u -d '+1 year' +%Y-%m-%dT%H:%M:%SZ)" \
    --query uri -o tsv)

echo "✅ Webhook created"
echo "⚠️  IMPORTANT: Save this webhook URI (shown only once):"
echo "$WEBHOOK_URI"
echo ""

# Create Action Group
echo ""
echo "Step 9: Creating Action Group..."
az monitor action-group create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$ACTION_GROUP_NAME" \
    --short-name "VMIdle" \
    --webhook-receiver name="IdleShutdown" uri="$WEBHOOK_URI" use-common-alert-schema=true

echo "✅ Action Group created"

# Create metric alert for CPU
echo ""
echo "Step 10: Creating metric alert for idle detection..."
az monitor metrics alert create \
    --name "$ALERT_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --scopes "$VM_ID" \
    --condition "avg Percentage CPU < $IDLE_CPU_THRESHOLD" \
    --window-size "${IDLE_DURATION_MINUTES}m" \
    --evaluation-frequency "5m" \
    --action "$ACTION_GROUP_NAME" \
    --description "Triggers when VM is idle (low CPU/network) for $IDLE_DURATION_MINUTES minutes"

echo "✅ Metric alert created"

# Test the runbook
echo ""
echo "Step 11: Testing runbook (dry run)..."
echo "Triggering test job..."
JOB_NAME=$(az automation job create \
    --resource-group "$RESOURCE_GROUP" \
    --automation-account-name "$AUTOMATION_ACCOUNT_NAME" \
    --runbook-name "$RUNBOOK_NAME" \
    --query name -o tsv)

echo "Job started: $JOB_NAME"
echo "Waiting for job to complete..."
sleep 10

az automation job show \
    --resource-group "$RESOURCE_GROUP" \
    --automation-account-name "$AUTOMATION_ACCOUNT_NAME" \
    --name "$JOB_NAME"

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Summary:"
echo "  Automation Account: $AUTOMATION_ACCOUNT_NAME"
echo "  Runbook: $RUNBOOK_NAME"
echo "  Alert: $ALERT_NAME"
echo "  Webhook: [saved above - store securely]"
echo ""
echo "How it works:"
echo "  1. Azure Monitor checks VM metrics every 5 minutes"
echo "  2. If CPU < ${IDLE_CPU_THRESHOLD}% for ${IDLE_DURATION_MINUTES} minutes, alert fires"
echo "  3. Alert triggers webhook → runbook executes"
echo "  4. Runbook validates idle state and stops VM"
echo ""
echo "To start VM manually:"
echo "  az vm start -g $RESOURCE_GROUP -n $VM_NAME"
echo ""
echo "To view runbook logs:"
echo "  az automation job list -g $RESOURCE_GROUP --automation-account-name $AUTOMATION_ACCOUNT_NAME"
echo ""
