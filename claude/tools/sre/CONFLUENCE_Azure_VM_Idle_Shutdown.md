# Azure VM Idle Shutdown - Cost Optimization Solution

**Space**: ORRO
**Author**: Naythan Dawe
**Date**: 2026-01-09
**Version**: 1.0
**Tags**: Azure, Cost Optimization, Automation, DevOps, SRE

---

## Overview

Automated activity-based shutdown system for Azure VMs to reduce costs by automatically deallocating VMs when idle.

### Key Benefits
- **Cost Savings**: ~$47/month per VM (60% reduction for 8h/day usage)
- **Zero Manual Intervention**: Fully automated monitoring and shutdown
- **Safe**: Double-validation before shutdown, easy manual override
- **Production-Ready**: Tested with Windows 11 development VMs

### Quick Stats
| Metric | Value |
|--------|-------|
| Cost Reduction | 60% for 8h/day usage |
| Idle Detection | 30 minutes |
| Check Frequency | Every 5 minutes |
| Startup Time | ~30 seconds |
| Deployment Time | 10-15 minutes |

---

## Architecture

### How It Works

```
┌─────────────────┐
│  Azure Monitor  │ Checks CPU/Network every 5 min
└────────┬────────┘
         │ CPU < 5% for 30 min?
         ▼
┌─────────────────┐
│   Alert Rule    │ Fires when threshold met
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│     Webhook     │ Triggers automation
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│     Runbook     │ Validates metrics + Stops VM
└─────────────────┘
```

### Components

1. **Azure Monitor Alert Rule**
   - Monitors: CPU percentage, Network In/Out
   - Threshold: CPU < 5% for 30 consecutive minutes
   - Frequency: Checks every 5 minutes

2. **Azure Automation Account**
   - Managed Identity (no stored credentials)
   - RBAC: VM Contributor + Monitoring Reader
   - PowerShell runbook with validation logic

3. **Webhook**
   - Secure HTTPS endpoint
   - Links alert → runbook execution
   - Unique token authentication

4. **Action Group**
   - Receives alert notifications
   - Triggers webhook
   - Common alert schema enabled

---

## Cost Analysis

### Example: Standard_D2as_v5 (win11-vscode sandbox)

| Scenario | Hours/Month | Compute Cost | Storage | Total | Savings |
|----------|-------------|--------------|---------|-------|---------|
| **24/7 Running** | 730 | $70 | $8 | **$78** | Baseline |
| **8h/day (weekdays)** | 240 | $23 | $8 | **$31** | **$47/month (60%)** |
| **4h/day** | 120 | $12 | $8 | **$20** | **$58/month (74%)** |
| **Stopped** | 0 | $0 | $8 | **$8** | **$70/month (90%)** |

**ROI**: Deployment time (~15 min) pays back in reduced costs within hours.

### Annual Savings (8h/day usage)
- **Per VM**: $564/year
- **10 VMs**: $5,640/year
- **50 VMs**: $28,200/year

---

## Deployment Guide

### Prerequisites

- Azure subscription with Contributor rights
- Target VM running in Azure
- PowerShell or Azure CLI access

### Step 1: Prepare Scripts

**Location**: OneDrive → Documents → remote-shared

**Required Files**:
- `Setup-SandboxVMIdleShutdown.ps1` (main deployment)
- `azure_vm_idle_shutdown_runbook.ps1` (monitoring logic)
- `Manage-VMIdleShutdown.ps1` (management utility)

### Step 2: Run Deployment

**On Windows VM (Recommended)**:
```powershell
# Open PowerShell as Administrator
cd "$env:OneDrive\Documents\remote-shared"
.\Setup-SandboxVMIdleShutdown.ps1
```

**On Mac/Linux**:
```bash
cd ~/maia/claude/tools/sre
./deploy_sandbox_idle_shutdown.sh
```

### Step 3: Save Webhook URI

During deployment, a **webhook URI** appears once. Save it securely:
```
https://s2events.azure-automation.net/webhooks?token=...
```

**Store in**: Password manager or `~/.maia/secrets/sandbox_vm_webhook.txt`

### Step 4: Verify Deployment

```powershell
.\Manage-VMIdleShutdown.ps1 -Action Status -ResourceGroup DEV-RG -VMName win11-vscode
```

Expected output:
- VM power state
- Alert enabled status
- Recent execution history
- Current metrics

---

## Configuration

### Default Thresholds

| Parameter | Default | Description |
|-----------|---------|-------------|
| CPU Threshold | < 5% | Percentage below which VM is idle |
| Network Threshold | < 100 KB | Network traffic threshold |
| Idle Duration | 30 minutes | Sustained idle period before shutdown |
| Check Frequency | 5 minutes | How often metrics are evaluated |

### Customization

**Adjust thresholds** (Azure Portal):
1. Navigate to: Monitor → Alerts → `sandbox-idle-alert`
2. Edit condition:
   - More aggressive: CPU < 10%, Duration 20 min
   - Less aggressive: CPU < 2%, Duration 45 min

**Edit runbook logic**:
```powershell
# In azure_vm_idle_shutdown_runbook.ps1
$IDLE_THRESHOLD_CPU = 5          # Percentage
$IDLE_THRESHOLD_NETWORK = 102400 # Bytes
$CHECK_PERIOD_MINUTES = 30       # Minutes
```

After editing, republish:
```powershell
Import-AzAutomationRunbook -ResourceGroupName "DEV-RG" `
    -AutomationAccountName "sandbox-vm-idle-shutdown" `
    -Name "Stop-IdleVM" -Type PowerShell `
    -Path "./azure_vm_idle_shutdown_runbook.ps1" -Force

Publish-AzAutomationRunbook -ResourceGroupName "DEV-RG" `
    -AutomationAccountName "sandbox-vm-idle-shutdown" `
    -Name "Stop-IdleVM"
```

---

## Daily Operations

### Starting a Stopped VM

**PowerShell**:
```powershell
Start-AzVM -ResourceGroupName DEV-RG -Name win11-vscode
```

**Azure CLI**:
```bash
az vm start -g DEV-RG -n win11-vscode
```

**Azure Portal**:
1. Navigate to Virtual Machines
2. Select VM → Start
3. Wait ~30 seconds

### Disabling Auto-Shutdown (Long Tasks)

**Before running long-running tasks** (builds, deployments, training):
```powershell
.\Manage-VMIdleShutdown.ps1 -Action Disable -ResourceGroup DEV-RG -VMName win11-vscode

# Run your long task
# ...

# Re-enable when done
.\Manage-VMIdleShutdown.ps1 -Action Enable -ResourceGroup DEV-RG -VMName win11-vscode
```

### Checking Status

```powershell
.\Manage-VMIdleShutdown.ps1 -Action Status -ResourceGroup DEV-RG -VMName win11-vscode
```

Shows:
- Current VM power state
- Alert enabled/disabled
- Recent shutdowns (last 10)
- Current CPU/network metrics

### Viewing History

```powershell
.\Manage-VMIdleShutdown.ps1 -Action ViewLogs -ResourceGroup DEV-RG -VMName win11-vscode
```

---

## Management Commands

| Action | Command | Purpose |
|--------|---------|---------|
| **Status** | `.\Manage-VMIdleShutdown.ps1 -Action Status` | Check current state |
| **Test** | `.\Manage-VMIdleShutdown.ps1 -Action Test` | Test idle detection |
| **Disable** | `.\Manage-VMIdleShutdown.ps1 -Action Disable` | Temporarily disable |
| **Enable** | `.\Manage-VMIdleShutdown.ps1 -Action Enable` | Re-enable monitoring |
| **Logs** | `.\Manage-VMIdleShutdown.ps1 -Action ViewLogs` | View execution history |
| **Start VM** | `.\Manage-VMIdleShutdown.ps1 -Action StartVM` | Start stopped VM |

---

## Troubleshooting

### VM Shuts Down During Active Use

**Symptom**: VM stops while you're working

**Cause**: Light workload (VS Code idle in editor uses minimal CPU)

**Solution**:
1. **Immediate**: Disable auto-shutdown
   ```powershell
   .\Manage-VMIdleShutdown.ps1 -Action Disable -ResourceGroup DEV-RG -VMName win11-vscode
   ```

2. **Long-term**: Increase thresholds
   - Portal → Monitor → Alerts → sandbox-idle-alert
   - Change: CPU < 5% → CPU < 1%
   - Change: 30 minutes → 60 minutes

### Alert Not Firing

**Check alert status**:
```powershell
Get-AzMetricAlertRuleV2 -ResourceGroupName DEV-RG -Name sandbox-idle-alert | Select-Object Enabled
```

If `Enabled = False`:
```powershell
.\Manage-VMIdleShutdown.ps1 -Action Enable -ResourceGroup DEV-RG -VMName win11-vscode
```

### Runbook Execution Fails

**Check RBAC permissions**:
```powershell
$vm = Get-AzVM -ResourceGroupName DEV-RG -Name win11-vscode
Get-AzRoleAssignment -Scope $vm.Id
```

Required roles:
- Virtual Machine Contributor (Automation Account managed identity)
- Monitoring Reader (Automation Account managed identity)

**View error logs**:
```powershell
.\Manage-VMIdleShutdown.ps1 -Action ViewLogs -ResourceGroup DEV-RG -VMName win11-vscode
```

### PowerShell Modules Not Loading

**Check module status**:
```powershell
Get-AzAutomationModule -ResourceGroupName DEV-RG `
    -AutomationAccountName sandbox-vm-idle-shutdown `
    | Select-Object Name, ProvisioningState, CreationTime
```

**Reimport if failed**:
```powershell
$modules = @("Az.Accounts", "Az.Compute", "Az.Monitor", "Az.Resources")
foreach ($module in $modules) {
    New-AzAutomationModule -ResourceGroupName DEV-RG `
        -AutomationAccountName sandbox-vm-idle-shutdown `
        -Name $module `
        -ContentLinkUri "https://www.powershellgallery.com/api/v2/package/$module"
}
```

Wait 10 minutes for import to complete.

---

## Security & Compliance

### Authentication
- **Managed Identity**: System-assigned, no stored credentials
- **Azure AD Integration**: Native Azure authentication
- **No Secrets**: Webhook URI is the only sensitive data

### Authorization
- **Least Privilege**: Only VM-level permissions
- **RBAC Roles**: Virtual Machine Contributor + Monitoring Reader
- **Scope**: Limited to specific VM resource

### Audit Trail
- **Azure Activity Log**: All VM operations logged
- **Automation Job History**: Full execution logs retained
- **Alert History**: Trigger events tracked

### Data Privacy
- **No Data Collection**: Only Azure metrics (CPU, network)
- **No External Calls**: All operations within Azure
- **Regional**: Runs in same region as VM

---

## Advanced Features

### Scheduled Auto-Start

Combine with scheduled start for full automation:

```powershell
# Start VM at 8 AM Mon-Fri
New-AzAutomationSchedule -ResourceGroupName DEV-RG `
    -AutomationAccountName sandbox-vm-idle-shutdown `
    -Name "WorkdayStart" -StartTime "08:00" `
    -DayInterval 1 `
    -WeekInterval @("Monday","Tuesday","Wednesday","Thursday","Friday")

# Create start runbook
$startScript = @'
param([string]$ResourceGroupName, [string]$VMName)
Connect-AzAccount -Identity
Start-AzVM -ResourceGroupName $ResourceGroupName -Name $VMName
'@

Set-Content -Path "Start-SandboxVM.ps1" -Value $startScript

Import-AzAutomationRunbook -ResourceGroupName DEV-RG `
    -AutomationAccountName sandbox-vm-idle-shutdown `
    -Name "Start-SandboxVM" -Type PowerShell `
    -Path "./Start-SandboxVM.ps1" -Force

Publish-AzAutomationRunbook -ResourceGroupName DEV-RG `
    -AutomationAccountName sandbox-vm-idle-shutdown `
    -Name "Start-SandboxVM"

# Link schedule to runbook
Register-AzAutomationScheduledRunbook -ResourceGroupName DEV-RG `
    -AutomationAccountName sandbox-vm-idle-shutdown `
    -RunbookName "Start-SandboxVM" -ScheduleName "WorkdayStart" `
    -Parameters @{ResourceGroupName="DEV-RG"; VMName="win11-vscode"}
```

**Result**: VM auto-starts 8 AM Mon-Fri, auto-stops when idle.

### Multi-VM Deployment

Apply to multiple VMs:

1. **Tag-based approach**:
   - Tag VMs with `AutoShutdown=True`
   - Modify runbook to query tagged VMs
   - Single alert monitors all tagged VMs

2. **Per-VM approach**:
   - Run setup script for each VM
   - Independent alerts and runbooks
   - Granular control per VM

### Custom Metrics

Add application-specific metrics:

```powershell
# In runbook, add custom metric check
$AppMetric = Get-AzMetric -ResourceId $appInsightsId `
    -MetricName "activeUsers" `
    -StartTime $StartTime -EndTime $EndTime

$IsIdle = ($AvgCpu -lt $threshold) -and ($AppMetric.Data[-1].Total -eq 0)
```

---

## Removal Instructions

To completely remove the system:

```powershell
# Remove alert rule
Remove-AzMetricAlertRuleV2 -ResourceGroupName DEV-RG -Name sandbox-idle-alert

# Remove action group
Remove-AzActionGroup -ResourceGroupName DEV-RG -Name sandbox-vm-idle-actions

# Remove Automation Account (includes runbooks, webhooks, schedules)
Remove-AzAutomationAccount -ResourceGroupName DEV-RG `
    -Name sandbox-vm-idle-shutdown -Force
```

**Note**: VM remains untouched. Only monitoring infrastructure removed.

---

## Resources

### Documentation
- **Setup Guide**: `Setup-SandboxVMIdleShutdown.ps1`
- **Usage Guide**: `SANDBOX_README.md`
- **Deployment Guide**: `SANDBOX_DEPLOYMENT_GUIDE.md`
- **Management Utility**: `Manage-VMIdleShutdown.ps1`

### File Locations
- **OneDrive**: `Documents/remote-shared/`
- **Maia Repo**: `claude/tools/sre/`
- **GitHub**: https://github.com/naythan-orro/maia

### Support Contacts
- **Primary**: Naythan Dawe (naythan.dawe@orro.group)
- **Team**: Maia AI/SRE Team

---

## Change Log

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2026-01-09 | Initial implementation for win11-vscode sandbox | Naythan Dawe |

---

## Related Pages

- [Azure Cost Optimization](link)
- [DevOps Best Practices](link)
- [SRE Runbooks](link)
- [Azure Automation Guide](link)

---

**Tags**: #Azure #CostOptimization #Automation #SRE #DevOps #AzureMonitor #PowerShell
