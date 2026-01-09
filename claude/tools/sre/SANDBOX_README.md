# win11-vscode Sandbox VM - Auto Idle Shutdown

**Save ~$47/month** by automatically stopping your development VM when not in use.

---

## 🚀 Quick Deploy (2 Minutes)

### Option 1: One-Line Deploy (Easiest)
```bash
cd ~/maia/claude/tools/sre
./deploy_sandbox_idle_shutdown.sh
```

### Option 2: PowerShell Direct
```powershell
cd ~/maia/claude/tools/sre
./Setup-SandboxVMIdleShutdown.ps1
```

**That's it!** The system is now monitoring your VM.

---

## 📊 What You Get

### Automatic Cost Optimization
- **Monitors**: CPU and network activity every 5 minutes
- **Triggers**: When idle for 30 minutes (CPU < 5%)
- **Action**: Deallocates VM automatically
- **Savings**: $0/hour when stopped vs ~$0.10/hour when running

### Your Usage Scenarios
| When | What Happens | Cost Impact |
|------|--------------|-------------|
| Actively coding | VM stays running | Normal cost |
| Lunch break (30+ min) | Auto-stops | $0/hour |
| Overnight | Auto-stops | $0/hour |
| Weekend | Auto-stops | $0/hour |
| Need VM again | Manual start (30 sec) | Resumes normal |

---

## 🎮 Daily Usage

### Starting Your VM

**PowerShell:**
```powershell
Start-AzVM -ResourceGroupName DEV-RG -Name win11-vscode
```

**Azure CLI:**
```bash
az vm start -g DEV-RG -n win11-vscode
```

**Azure Portal:**
1. Go to https://portal.azure.com
2. Virtual Machines → win11-vscode → Start

**Startup time**: ~30 seconds

### Working Sessions

**No action needed!** Just use your VM normally:
- Code in VS Code
- Run builds/tests
- Browse/debug
- The system only triggers when **truly idle** (no activity for 30 min)

### End of Day

**No action needed!** Leave VM running:
- After 30 min idle → auto-stops
- You pay $0 overnight
- Next day: quick start and resume work

### Long-Running Tasks

**Disable auto-shutdown** before starting:
```powershell
./Manage-VMIdleShutdown.ps1 -Action Disable -ResourceGroup DEV-RG -VMName win11-vscode

# Run your long task (training, deployment, etc.)

# Re-enable when done
./Manage-VMIdleShutdown.ps1 -Action Enable -ResourceGroup DEV-RG -VMName win11-vscode
```

---

## 🔍 Check Status Anytime

```powershell
./Manage-VMIdleShutdown.ps1 -Action Status -ResourceGroup DEV-RG -VMName win11-vscode
```

**Shows:**
- VM power state (running/stopped)
- Alert enabled/disabled
- Recent auto-shutdowns
- Current metrics (CPU, network)

---

## 🧪 Test It Out

### Simulate Idle Detection
```powershell
./Manage-VMIdleShutdown.ps1 -Action Test -ResourceGroup DEV-RG -VMName win11-vscode
```

This runs the idle detection logic and shows what would happen (won't stop active VM).

### View History
```powershell
./Manage-VMIdleShutdown.ps1 -Action ViewLogs -ResourceGroup DEV-RG -VMName win11-vscode
```

See last 10 automatic shutdowns with reasons.

---

## 💰 Cost Tracking

### Before Auto-Shutdown (24/7 Running)
```
Compute: $0.096/hour × 730 hours = $70/month
Storage: $8/month
Total: ~$78/month
```

### After Auto-Shutdown (8 hours/day usage)
```
Compute: $0.096/hour × 240 hours = $23/month
Storage: $8/month
Total: ~$31/month

Savings: $47/month (60%)
```

### Track Your Savings
```powershell
# View VM uptime this month
Get-AzMetric -ResourceId (Get-AzVM -ResourceGroupName DEV-RG -Name win11-vscode).Id `
    -MetricName "Percentage CPU" `
    -StartTime (Get-Date).AddDays(-30) `
    -EndTime (Get-Date) `
    | Measure-Object
```

---

## 🛠️ Management Commands

All commands use this format:
```powershell
./Manage-VMIdleShutdown.ps1 -Action <ACTION> -ResourceGroup DEV-RG -VMName win11-vscode
```

| Action | What It Does |
|--------|--------------|
| `Status` | Check VM state, alert status, recent activity |
| `Test` | Test idle detection (dry run) |
| `Disable` | Turn off auto-shutdown temporarily |
| `Enable` | Turn on auto-shutdown |
| `ViewLogs` | See execution history (last 10 runs) |
| `StartVM` | Start the VM if stopped |
| `ManualShutdown` | Force idle check and stop if idle |

---

## ⚙️ Configuration

### Current Settings
- **CPU Threshold**: < 5% (very light activity)
- **Idle Duration**: 30 minutes
- **Check Frequency**: Every 5 minutes
- **Monitored Metrics**: CPU, Network In/Out

### Too Aggressive? (Stops while you're working)

**Increase thresholds:**
1. Azure Portal → Monitor → Alerts → `sandbox-idle-alert`
2. Edit condition: CPU < 5% → CPU < 2%
3. Edit window: 30 minutes → 45 minutes

Or just **disable** when actively working:
```powershell
./Manage-VMIdleShutdown.ps1 -Action Disable -ResourceGroup DEV-RG -VMName win11-vscode
```

### Not Aggressive Enough? (Takes too long to stop)

**Decrease thresholds:**
1. Azure Portal → Monitor → Alerts → `sandbox-idle-alert`
2. Edit window: 30 minutes → 20 minutes

---

## 🚨 Troubleshooting

### VM Stopped Unexpectedly

**Check if idle shutdown triggered:**
```powershell
./Manage-VMIdleShutdown.ps1 -Action ViewLogs -ResourceGroup DEV-RG -VMName win11-vscode
```

Look for recent "VM is IDLE - proceeding with shutdown" messages.

**Prevention:**
- Disable during work hours if too sensitive
- Increase idle duration threshold
- Run light background task (ping script)

### Auto-Shutdown Not Working

**Verify alert is enabled:**
```powershell
Get-AzMetricAlertRuleV2 -ResourceGroupName DEV-RG -Name sandbox-idle-alert | Select-Object Enabled
```

If `Enabled = False`:
```powershell
./Manage-VMIdleShutdown.ps1 -Action Enable -ResourceGroup DEV-RG -VMName win11-vscode
```

**Test manually:**
```powershell
./Manage-VMIdleShutdown.ps1 -Action Test -ResourceGroup DEV-RG -VMName win11-vscode
```

### Can't Start VM

**Check if still stopped from shutdown:**
```powershell
Get-AzVM -ResourceGroupName DEV-RG -Name win11-vscode -Status | Select-Object PowerState
```

**Start it:**
```powershell
Start-AzVM -ResourceGroupName DEV-RG -Name win11-vscode
```

---

## 📚 Files Reference

| File | Purpose |
|------|---------|
| `SANDBOX_README.md` | **This file** - Quick sandbox guide |
| `SANDBOX_DEPLOYMENT_GUIDE.md` | Detailed deployment steps |
| `Setup-SandboxVMIdleShutdown.ps1` | Main setup script |
| `Manage-VMIdleShutdown.ps1` | Management utility |
| `azure_vm_idle_shutdown_runbook.ps1` | Actual shutdown logic |
| `deploy_sandbox_idle_shutdown.sh` | Bash wrapper (one-line deploy) |
| `AZURE_VM_IDLE_SHUTDOWN_README.md` | Full technical documentation |
| `azure_vm_idle_shutdown_quickref.txt` | Command cheat sheet |

---

## 🔐 Security

- **No stored credentials**: Uses Azure Managed Identity
- **Least privilege RBAC**: Only VM-level permissions
- **Audit logging**: All shutdowns logged to Azure Activity Log
- **Webhook security**: HTTPS with unique token (treat as secret)

---

## 🗑️ Remove/Uninstall

To completely remove the auto-shutdown system:

```powershell
# Remove alert
Remove-AzMetricAlertRuleV2 -ResourceGroupName DEV-RG -Name sandbox-idle-alert

# Remove action group
Remove-AzActionGroup -ResourceGroupName DEV-RG -Name sandbox-vm-idle-actions

# Remove automation account
Remove-AzAutomationAccount -ResourceGroupName DEV-RG -Name sandbox-vm-idle-shutdown -Force
```

Your VM remains untouched - only the monitoring/automation is removed.

---

## 📞 Support

**Quick checks:**
1. Status: `./Manage-VMIdleShutdown.ps1 -Action Status -ResourceGroup DEV-RG -VMName win11-vscode`
2. Logs: `./Manage-VMIdleShutdown.ps1 -Action ViewLogs -ResourceGroup DEV-RG -VMName win11-vscode`
3. Test: `./Manage-VMIdleShutdown.ps1 -Action Test -ResourceGroup DEV-RG -VMName win11-vscode`

**Common issues:**
- "Runbook fails" → Check RBAC permissions (see deployment guide)
- "Alert not firing" → Verify enabled status
- "Stops during work" → Increase thresholds or disable temporarily

---

## 🎯 Best Practices

### Daily Workflow
1. **Morning**: Start VM manually (30 sec)
2. **Work**: Code normally (system stays dormant)
3. **Lunch/breaks**: System auto-stops after 30 min idle
4. **Evening**: Leave running, auto-stops overnight

### Weekly Maintenance
- Check status once/week
- Review logs for unexpected shutdowns
- Adjust thresholds if needed

### Cost Optimization
- Track monthly savings via Azure Cost Management
- Compare "before" vs "after" costs
- Share success with team for other VMs

---

**Deployed**: _______________
**First auto-shutdown**: _______________
**Monthly savings target**: $47
**Status**: 🟢 Active
