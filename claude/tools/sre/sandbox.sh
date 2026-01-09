#!/bin/bash
# Sandbox Environment Helper
# Quick access to win11-vscode sandbox VM

SUBSCRIPTION_ID="9b8e7b3f-d3e7-4da9-a22a-9bf7c8ee4dde"
RESOURCE_GROUP="DEV-RG"
VM_NAME="win11-vscode"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

usage() {
    echo "Sandbox Environment Helper"
    echo ""
    echo "Usage: ./sandbox.sh [command]"
    echo ""
    echo "Commands:"
    echo "  status    - Show VM status and details"
    echo "  start     - Start the VM"
    echo "  stop      - Stop the VM (deallocate)"
    echo "  restart   - Restart the VM"
    echo "  connect   - Get RDP connection info"
    echo "  cost      - Show cost information"
    echo "  switch    - Switch to sandbox subscription"
    echo ""
    echo "Examples:"
    echo "  ./sandbox.sh status"
    echo "  ./sandbox.sh start"
    echo ""
}

# Switch to subscription
switch_subscription() {
    echo -e "${BLUE}Switching to sandbox subscription...${NC}"
    az account set --subscription "$SUBSCRIPTION_ID"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Connected to Visual Studio Enterprise Subscription${NC}"
        az account show --query "{Name:name, Tenant:tenantId}" -o table
    else
        echo -e "${RED}❌ Failed to switch subscription${NC}"
        exit 1
    fi
}

# Get VM status
get_status() {
    switch_subscription
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}Sandbox VM Status${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    POWER_STATE=$(az vm get-instance-view -g "$RESOURCE_GROUP" -n "$VM_NAME" \
        --query "instanceView.statuses[?starts_with(code, 'PowerState/')].displayStatus" -o tsv)

    echo ""
    echo "  VM Name: $VM_NAME"
    echo "  Resource Group: $RESOURCE_GROUP"

    if [[ "$POWER_STATE" == *"running"* ]]; then
        echo -e "  Status: ${GREEN}$POWER_STATE${NC}"
    elif [[ "$POWER_STATE" == *"deallocated"* ]] || [[ "$POWER_STATE" == *"stopped"* ]]; then
        echo -e "  Status: ${YELLOW}$POWER_STATE${NC}"
    else
        echo -e "  Status: ${RED}$POWER_STATE${NC}"
    fi

    echo ""
    echo "  Details:"
    az vm show -g "$RESOURCE_GROUP" -n "$VM_NAME" \
        --query "{Size:hardwareProfile.vmSize, Location:location, OS:storageProfile.osDisk.osType}" -o table | tail -n +2 | sed 's/^/    /'

    echo ""
}

# Start VM
start_vm() {
    switch_subscription
    echo ""
    echo -e "${BLUE}Starting VM...${NC}"
    az vm start -g "$RESOURCE_GROUP" -n "$VM_NAME" --no-wait
    echo -e "${GREEN}✅ Start command issued${NC}"
    echo "VM will be ready in ~30 seconds"
    echo ""
    echo "Check status: ./sandbox.sh status"
}

# Stop VM
stop_vm() {
    switch_subscription
    echo ""
    echo -e "${YELLOW}Stopping VM (deallocating to save costs)...${NC}"
    read -p "Are you sure? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        az vm deallocate -g "$RESOURCE_GROUP" -n "$VM_NAME" --no-wait
        echo -e "${GREEN}✅ Stop command issued${NC}"
        echo "VM will be deallocated in ~30 seconds (cost: \$0/hour)"
    else
        echo "Cancelled"
    fi
    echo ""
}

# Restart VM
restart_vm() {
    switch_subscription
    echo ""
    echo -e "${BLUE}Restarting VM...${NC}"
    az vm restart -g "$RESOURCE_GROUP" -n "$VM_NAME" --no-wait
    echo -e "${GREEN}✅ Restart command issued${NC}"
    echo ""
}

# Get RDP info
get_rdp_info() {
    switch_subscription
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}RDP Connection Info${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    PUBLIC_IP=$(az vm show -g "$RESOURCE_GROUP" -n "$VM_NAME" -d --query publicIps -o tsv)

    if [ -z "$PUBLIC_IP" ]; then
        echo -e "${RED}❌ No public IP found. Is the VM running?${NC}"
    else
        echo "  Host: $PUBLIC_IP"
        echo "  User: azureuser"
        echo "  Port: 3389 (RDP)"
        echo ""
        echo "  RDP Command:"
        echo "    open rdp://full%20address=s:$PUBLIC_IP"
    fi
    echo ""
}

# Show cost info
show_costs() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}Cost Information - Standard_D2as_v5${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "  Hourly (running):     ~\$0.096/hour"
    echo "  Daily (24h):          ~\$2.30/day"
    echo "  Monthly (24/7):       ~\$70/month"
    echo "  Monthly (8h/day):     ~\$23/month"
    echo "  Storage (always):     ~\$8/month"
    echo ""
    echo -e "${GREEN}  When stopped (deallocated): \$0/hour${NC}"
    echo ""
    echo "  Potential savings with idle shutdown: ~\$47/month"
    echo ""
}

# Main
case "$1" in
    status)
        get_status
        ;;
    start)
        start_vm
        ;;
    stop)
        stop_vm
        ;;
    restart)
        restart_vm
        ;;
    connect)
        get_rdp_info
        ;;
    cost)
        show_costs
        ;;
    switch)
        switch_subscription
        ;;
    *)
        usage
        exit 1
        ;;
esac
