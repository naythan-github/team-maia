# Sandbox VM Idle Shutdown - Quick Deployment

> Automatically stop `win11-vscode` VM when idle to save costs

## Pre-Deployment Checklist

- [ ] Azure PowerShell installed (`Az` module) or Azure CLI (`az`)
- [ ] Access to Azure subscription with Contributor rights
- [ ] Know your Resource Group name (default: `DEV-RG`)
- [ ] Know your Subscription ID

## Get Your Subscription Info

### PowerShell
```powershell
Connect-AzAccount
Get-AzSubscription | Format-Table Name, Id
Get-AzVM | Format-Table ResourceGroupName, Name, Location
```

### Azure CLI
```bash
az login
az account list --output table
az vm list --output table
```

**Note down:**
- Subscription ID: `_____________________________________`
- Resource Group: `_____________________________________`
- VM Name: `win11-vscode` (or actual name if different)

---

## Deploy in 2 Minutes

### Step 1: Navigate to Scripts
```powershell
cd ~/maia/claude/tools/sre
```

### Step 2: Run Setup Script
```powershell
./Setup-SandboxVMIdleShutdown.ps1
```

**If using custom values:**
```powershell
./Setup-SandboxVMIdleShutdown.ps1 `
    -SubscriptionId "your-sub-id-here" `
    -ResourceGroup "actual-rg-name" `
    -VMName "actual-vm-name"
```

### Step 3: Save Webhook URI
⚠️ **IMPORTANT**: During setup, you'll see a webhook URI. Copy and save it securely.

```
⚠️  IMPORTANT: Save this webhook URI (shown only once):
https://s2events.azure-automation.net/webhooks?token=...
```

**Save it to:** `~/.maia/secrets/sandbox_vm_webhook.txt`

### Step 4: Verify
```powershell
./Manage-VMIdleShutdown.ps1 -Action Status -ResourceGroup "DEV-RG" -VMName "win11-vscode"
```

---

## What Happens Next

### Automatic Shutdown
- VM monitored every **5 minutes**
- If CPU < **5%** for **30 minutes** → VM stops automatically
- Status: **Deallocated** (compute cost = $0/hour)

### Manual Start
```powershell
# PowerShell
Start-AzVM -ResourceGroupName "DEV-RG" -Name "win11-vscode"

# Azure CLI
az vm start -g DEV-RG -n win11-vscode

# Azure Portal
Portal → Virtual Machines → win11-vscode → Start
```

### Cost Savings
| Usage Pattern | Cost/Month | Savings |
|---------------|------------|---------|
| 24/7 running | ~$70 | Baseline |
| 8 hours/day | ~$23 | **$47/month** |
| 4 hours/day | ~$12 | **$58/month** |
| Stopped | $0 compute | **$70/month** |

*(Assumes Standard D2s_v3, actual costs vary by VM size)*

---

## Management Commands

### Check Current Status
```powershell
./Manage-VMIdleShutdown.ps1 -Action Status -ResourceGroup "DEV-RG" -VMName "win11-vscode"
```

Shows:
- VM power state
- Alert enabled/disabled
- Recent shutdowns
- Current CPU/network metrics

### Test Shutdown Logic
```powershell
./Manage-VMIdleShutdown.ps1 -Action Test -ResourceGroup "DEV-RG" -VMName "win11-vscode"
```

Runs the idle detection logic without actually stopping the VM (if VM is active).

### Temporarily Disable
```powershell
./Manage-VMIdleShutdown.ps1 -Action Disable -ResourceGroup "DEV-RG" -VMName "win11-vscode"
```

Use when:
- Running long-running tasks (training, builds, deployments)
- Troubleshooting
- Weekend work sessions

### Re-Enable
```powershell
./Manage-VMIdleShutdown.ps1 -Action Enable -ResourceGroup "DEV-RG" -VMName "win11-vscode"
```

### View Execution History
```powershell
./Manage-VMIdleShutdown.ps1 -Action ViewLogs -ResourceGroup "DEV-RG" -VMName "win11-vscode"
```

Shows last 10 runbook executions with output.

---

## Customization

### Adjust Idle Threshold

**More aggressive** (shutdown sooner):
```powershell
# Edit alert in Portal: Monitor → Alerts → sandbox-idle-alert
# Change: CPU < 5% → CPU < 10%
# Change: 30 minutes → 20 minutes
```

**Less aggressive** (prevent accidental shutdowns):
```powershell
# Edit alert in Portal
# Change: CPU < 5% → CPU < 2%
# Change: 30 minutes → 45 minutes
```

### Edit Runbook Logic

File: `azure_vm_idle_shutdown_runbook.ps1`

Current thresholds:
```powershell
$IDLE_THRESHOLD_CPU = 5          # Percentage
$IDLE_THRESHOLD_NETWORK = 102400 # Bytes (100 KB)
$CHECK_PERIOD_MINUTES = 30       # Minutes
```

After editing, republish:
```powershell
Import-AzAutomationRunbook `
    -ResourceGroupName "DEV-RG" `
    -AutomationAccountName "sandbox-vm-idle-shutdown" `
    -Name "Stop-IdleVM" `
    -Type PowerShell `
    -Path "./azure_vm_idle_shutdown_runbook.ps1" `
    -Force

Publish-AzAutomationRunbook `
    -ResourceGroupName "DEV-RG" `
    -AutomationAccountName "sandbox-vm-idle-shutdown" `
    -Name "Stop-IdleVM"
```

---

## Troubleshooting

### Alert Not Firing

**Check alert status:**
```powershell
Get-AzMetricAlertRuleV2 -ResourceGroupName "DEV-RG" -Name "sandbox-idle-alert"
```

**Verify enabled:**
```powershell
$alert = Get-AzMetricAlertRuleV2 -ResourceGroupName "DEV-RG" -Name "sandbox-idle-alert"
if (-not $alert.Enabled) {
    Write-Host "Alert is DISABLED"
}
```

**Check recent alerts:**
```powershell
Get-AzAlert -ResourceGroupName "DEV-RG" | Where-Object {$_.Name -like "*idle*"} | Select-Object Name, State, MonitorCondition, FiredDateTime
```

### Runbook Fails

**Check permissions:**
```powershell
$vm = Get-AzVM -ResourceGroupName "DEV-RG" -Name "win11-vscode"
Get-AzRoleAssignment -Scope $vm.Id
```

**Should show:**
- Virtual Machine Contributor (for Automation Account managed identity)
- Monitoring Reader (for Automation Account managed identity)

**View error logs:**
```powershell
./Manage-VMIdleShutdown.ps1 -Action ViewLogs -ResourceGroup "DEV-RG" -VMName "win11-vscode"
```

### Modules Not Loading

**Check module status:**
```powershell
Get-AzAutomationModule `
    -ResourceGroupName "DEV-RG" `
    -AutomationAccountName "sandbox-vm-idle-shutdown" `
    | Select-Object Name, ProvisioningState, CreationTime
```

**Reimport if failed:**
```powershell
$modules = @("Az.Accounts", "Az.Compute", "Az.Monitor", "Az.Resources")
foreach ($module in $modules) {
    New-AzAutomationModule `
        -ResourceGroupName "DEV-RG" `
        -AutomationAccountName "sandbox-vm-idle-shutdown" `
        -Name $module `
        -ContentLinkUri "https://www.powershellgallery.com/api/v2/package/$module"
}
```

Wait 10 minutes, then test.

### VM Stops During Active Use

**Symptom**: VM shuts down while you're coding/working

**Cause**: Workload is too light (VS Code doesn't use much CPU when idle in editor)

**Solution**: Increase thresholds
```powershell
# Option 1: Disable auto-shutdown when actively working
./Manage-VMIdleShutdown.ps1 -Action Disable -ResourceGroup "DEV-RG" -VMName "win11-vscode"

# Option 2: Adjust thresholds (edit alert in Portal)
# CPU < 5% → CPU < 1% (only shutdown when completely idle)
# 30 minutes → 60 minutes (longer idle period)
```

---

## Advanced: Scheduled Start

Combine with auto-start for full automation:

### Start VM at 8 AM Weekdays
```powershell
# Create schedule
New-AzAutomationSchedule `
    -ResourceGroupName "DEV-RG" `
    -AutomationAccountName "sandbox-vm-idle-shutdown" `
    -Name "WorkdayStart" `
    -StartTime "08:00" `
    -DayInterval 1 `
    -WeekInterval @("Monday", "Tuesday", "Wednesday", "Thursday", "Friday")

# Create start runbook
$startScript = @'
param([string]$ResourceGroupName, [string]$VMName)
Connect-AzAccount -Identity
Start-AzVM -ResourceGroupName $ResourceGroupName -Name $VMName
'@

Import-AzAutomationRunbook `
    -ResourceGroupName "DEV-RG" `
    -AutomationAccountName "sandbox-vm-idle-shutdown" `
    -Name "Start-SandboxVM" `
    -Type PowerShell `
    -Force

# Link schedule to runbook
Register-AzAutomationScheduledRunbook `
    -ResourceGroupName "DEV-RG" `
    -AutomationAccountName "sandbox-vm-idle-shutdown" `
    -RunbookName "Start-SandboxVM" `
    -ScheduleName "WorkdayStart" `
    -Parameters @{ResourceGroupName="DEV-RG"; VMName="win11-vscode"}
```

**Result**: VM automatically starts at 8 AM Mon-Fri, shuts down when idle.

---

## Cleanup / Removal

To completely remove the idle shutdown system:

```powershell
# Remove alert
Remove-AzMetricAlertRuleV2 -ResourceGroupName "DEV-RG" -Name "sandbox-idle-alert"

# Remove action group
Remove-AzActionGroup -ResourceGroupName "DEV-RG" -Name "sandbox-vm-idle-actions"

# Remove Automation Account (includes runbooks, webhooks, schedules)
Remove-AzAutomationAccount -ResourceGroupName "DEV-RG" -Name "sandbox-vm-idle-shutdown" -Force
```

---

## Support

**Files:**
- Setup: `Setup-SandboxVMIdleShutdown.ps1`
- Management: `Manage-VMIdleShutdown.ps1`
- Runbook: `azure_vm_idle_shutdown_runbook.ps1`
- Full docs: `AZURE_VM_IDLE_SHUTDOWN_README.md`
- Quick ref: `azure_vm_idle_shutdown_quickref.txt`

**Issues?**
1. Run status check: `./Manage-VMIdleShutdown.ps1 -Action Status`
2. View logs: `./Manage-VMIdleShutdown.ps1 -Action ViewLogs`
3. Test manually: `./Manage-VMIdleShutdown.ps1 -Action Test`

---

**Deployment Date**: _________________
**Webhook Saved**: [ ] Yes [ ] No
**First Test Complete**: [ ] Yes [ ] No
**Cost Tracking Started**: [ ] Yes [ ] No
