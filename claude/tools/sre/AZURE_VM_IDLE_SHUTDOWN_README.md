# Azure VM Idle Shutdown Automation

Automatically shut down Azure VMs based on activity monitoring (CPU, network, disk) to reduce costs.

## Overview

This solution monitors Azure VM metrics and automatically deallocates VMs when they're idle for a specified period. When stopped (deallocated), you pay **$0/hour** for compute - only storage costs (~$5-10/month).

## How It Works

```
Azure Monitor (metrics) → Alert Rule (idle detected) → Webhook → Automation Runbook → Stop VM
```

1. **Azure Monitor** checks VM metrics every 5 minutes
2. **Alert fires** if CPU < threshold for specified duration (e.g., 30 minutes)
3. **Webhook triggers** Azure Automation runbook
4. **Runbook validates** idle state by checking multiple metrics
5. **VM deallocates** if confirmed idle (or remains running if active)

## Files

| File | Purpose |
|------|---------|
| `azure_vm_idle_shutdown_runbook.ps1` | PowerShell runbook that checks metrics and stops VM |
| `setup_azure_vm_idle_shutdown.sh` | Bash setup script (Linux/Mac) |
| `Setup-AzureVMIdleShutdown.ps1` | PowerShell setup script (Windows) |
| `Manage-VMIdleShutdown.ps1` | Management utility for testing and monitoring |

## Prerequisites

- Azure subscription with VM running
- Azure CLI (`az`) or Azure PowerShell (`Az` module)
- Permissions: Contributor on VM, ability to create Automation Account

## Quick Start

### Option 1: Bash (Linux/Mac)

1. **Configure** the script:
   ```bash
   vim setup_azure_vm_idle_shutdown.sh
   ```
   Update these variables:
   ```bash
   SUBSCRIPTION_ID="your-subscription-id"
   RESOURCE_GROUP="your-rg"
   VM_NAME="your-vm-name"
   LOCATION="australiaeast"
   ```

2. **Run setup**:
   ```bash
   chmod +x setup_azure_vm_idle_shutdown.sh
   ./setup_azure_vm_idle_shutdown.sh
   ```

3. **Save the webhook URI** shown during setup (you'll need it if you rebuild)

### Option 2: PowerShell (Windows/Mac/Linux)

1. **Run setup** with parameters:
   ```powershell
   ./Setup-AzureVMIdleShutdown.ps1 `
       -SubscriptionId "your-subscription-id" `
       -ResourceGroup "your-rg" `
       -VMName "your-vm-name" `
       -Location "australiaeast" `
       -IdleCpuThreshold 5 `
       -IdleDurationMinutes 30
   ```

2. **Save the webhook URI** shown during setup

## Configuration

### Thresholds

| Parameter | Default | Description |
|-----------|---------|-------------|
| `IdleCpuThreshold` | 5% | CPU percentage below which VM is considered idle |
| `IdleNetworkThreshold` | 100 KB | Network traffic below which VM is idle |
| `IdleDurationMinutes` | 30 min | How long VM must be idle before shutdown |

### Customization

Edit the runbook (`azure_vm_idle_shutdown_runbook.ps1`) to change:

```powershell
$IDLE_THRESHOLD_CPU = 5          # Percentage
$IDLE_THRESHOLD_NETWORK = 102400 # Bytes (100 KB)
$CHECK_PERIOD_MINUTES = 30       # Minutes
```

## Management

### Test Runbook
```powershell
./Manage-VMIdleShutdown.ps1 -Action Test -ResourceGroup "your-rg" -VMName "your-vm"
```

### Check Status
```powershell
./Manage-VMIdleShutdown.ps1 -Action Status -ResourceGroup "your-rg" -VMName "your-vm"
```

Shows:
- VM power state
- Alert enabled/disabled
- Recent runbook executions
- Current metrics (CPU, network)

### Disable Auto-Shutdown
```powershell
./Manage-VMIdleShutdown.ps1 -Action Disable -ResourceGroup "your-rg" -VMName "your-vm"
```

### Enable Auto-Shutdown
```powershell
./Manage-VMIdleShutdown.ps1 -Action Enable -ResourceGroup "your-rg" -VMName "your-vm"
```

### View Logs
```powershell
./Manage-VMIdleShutdown.ps1 -Action ViewLogs -ResourceGroup "your-rg" -VMName "your-vm"
```

### Start VM
```powershell
./Manage-VMIdleShutdown.ps1 -Action StartVM -ResourceGroup "your-rg" -VMName "your-vm"
```

Or via Azure CLI:
```bash
az vm start -g your-rg -n your-vm
```

## Cost Savings

### Example: D2s_v3 VM (2 vCPU, 8 GB RAM)

| State | Hourly Cost | Daily Cost (24h) | Monthly Cost |
|-------|-------------|------------------|--------------|
| **Running** | $0.096/hr | $2.30/day | $70/month |
| **Deallocated** | $0.00/hr | $0.00/day | $0/month |
| **Storage (always)** | - | - | ~$8/month |

**Scenario**: VM runs 8 hours/day (business hours), auto-shuts down 16 hours/day
- **Cost without shutdown**: $70/month
- **Cost with idle shutdown**: $23 (compute) + $8 (storage) = **$31/month**
- **Savings**: **$39/month (56%)**

## Troubleshooting

### Runbook fails with "Failed to authenticate"

**Cause**: Managed Identity not fully propagated or missing permissions

**Fix**:
1. Wait 2-3 minutes for identity propagation
2. Verify RBAC assignments:
   ```powershell
   $VM = Get-AzVM -ResourceGroupName "your-rg" -Name "your-vm"
   Get-AzRoleAssignment -Scope $VM.Id
   ```
3. Ensure these roles exist:
   - Virtual Machine Contributor
   - Monitoring Reader

### Alert not firing despite idle VM

**Causes**:
- Alert disabled
- Threshold not met for full duration
- Metrics delayed (can be 3-5 minutes behind)

**Fix**:
1. Check alert status:
   ```powershell
   Get-AzMetricAlertRuleV2 -ResourceGroupName "your-rg" -Name "vm-idle-alert-your-vm"
   ```
2. Manually test runbook:
   ```powershell
   ./Manage-VMIdleShutdown.ps1 -Action Test -ResourceGroup "your-rg" -VMName "your-vm"
   ```

### VM shuts down during active use

**Cause**: Thresholds too aggressive for workload type

**Fix**: Increase thresholds
```powershell
# Edit the alert rule in Azure Portal or update via CLI
az monitor metrics alert update \
    -n "vm-idle-alert-your-vm" \
    -g "your-rg" \
    --condition "avg Percentage CPU < 10"  # Increase from 5 to 10
```

### PowerShell modules not importing

**Cause**: Gallery API issues or transient failures

**Fix**:
```powershell
# Manually import modules
$modules = @("Az.Accounts", "Az.Compute", "Az.Monitor", "Az.Resources")
foreach ($module in $modules) {
    New-AzAutomationModule `
        -ResourceGroupName "your-rg" `
        -AutomationAccountName "vm-idle-shutdown-automation" `
        -Name $module `
        -ContentLinkUri "https://www.powershellgallery.com/api/v2/package/$module"
}
```

Wait 10-15 minutes for import to complete.

## Architecture Details

### Components

1. **Azure Automation Account**
   - Managed Identity (System-assigned)
   - RBAC: Virtual Machine Contributor + Monitoring Reader
   - Runbook: PowerShell script

2. **Azure Monitor Alert**
   - Metric: Percentage CPU
   - Threshold: < 5% (configurable)
   - Window: 30 minutes (configurable)
   - Frequency: 5 minutes

3. **Action Group**
   - Webhook receiver
   - Common alert schema enabled
   - Triggers runbook via HTTPS

### Security

- **Managed Identity**: No stored credentials, Azure AD authentication
- **RBAC**: Least privilege (only VM-level permissions)
- **Webhook**: HTTPS with unique URI (treat as secret)
- **Audit**: All actions logged to Azure Activity Log

## Advanced Usage

### Multi-VM Setup

To monitor multiple VMs, run setup for each VM:

```bash
# VM 1
./setup_azure_vm_idle_shutdown.sh  # Configure for VM1
# VM 2
./setup_azure_vm_idle_shutdown.sh  # Configure for VM2
```

Or use **tags** with a single runbook:
1. Tag VMs with `AutoShutdown=True`
2. Modify runbook to query all VMs with tag
3. Single alert with dynamic scope

### Custom Metrics

Add custom application metrics to idle detection:

```powershell
# In runbook, add custom metric check
$AppMetric = Get-AzMetric -ResourceId $appInsightsId `
    -MetricName "activeUsers" `
    -StartTime $StartTime `
    -EndTime $EndTime

$IsIdle = ($AvgCpu -lt $threshold) -and ($AppMetric.Data[-1].Total -eq 0)
```

### Integration with Auto-Start

Combine with scheduled start for full automation:

```powershell
# Schedule VM to start at 8 AM Mon-Fri
New-AzAutomationSchedule `
    -ResourceGroupName "your-rg" `
    -AutomationAccountName "vm-idle-shutdown-automation" `
    -Name "WorkdayStart" `
    -StartTime "08:00" `
    -DayInterval 1 `
    -WeekInterval @("Monday", "Tuesday", "Wednesday", "Thursday", "Friday")

# Create start runbook
New-AzAutomationRunbook -Name "Start-VM" -Type PowerShell -Content "Start-AzVM ..."
Register-AzAutomationScheduledRunbook -RunbookName "Start-VM" -ScheduleName "WorkdayStart"
```

## Support

For issues or questions:
1. Check runbook logs: `./Manage-VMIdleShutdown.ps1 -Action ViewLogs`
2. Test manually: `./Manage-VMIdleShutdown.ps1 -Action Test`
3. Review Azure Activity Log for VM stop operations

## License

MIT License - Use freely, no warranties provided.

## Version History

- **v1.0** (2026-01-09): Initial release
  - CPU + Network metric monitoring
  - Automated setup scripts (Bash + PowerShell)
  - Management utility
  - Comprehensive documentation
