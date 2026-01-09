# Sandbox Idle Shutdown - Test Results

**Test Date**: 2026-01-09
**Environment**: Visual Studio Enterprise Subscription (9b8e7b3f-d3e7-4da9-a22a-9bf7c8ee4dde)

---

## ✅ Configuration Verification

### VM Details (Verified via Azure CLI)
```
Name:           win11-vscode
Resource Group: DEV-RG
Location:       australiaeast
VM Size:        Standard_D2as_v5 (2 vCPU, 8 GB RAM)
OS:             Windows 11 Enterprise 23H2
Status:         Running
Public IP:      4.147.176.243
```

### Configuration Files
- ✅ **sandbox_environment.json** - All details correct
- ✅ **azure_vm_idle_shutdown_runbook.ps1** - Defaults set to DEV-RG/win11-vscode
- ✅ **Setup-SandboxVMIdleShutdown.ps1** - Defaults set to DEV-RG/win11-vscode
- ✅ **sandbox.sh** - Helper script working perfectly

---

## ✅ Helper Script Tests

### Test 1: Status Check
```bash
./sandbox.sh status
```
**Result**: ✅ PASS
- Successfully connected to subscription
- Retrieved VM status (Running)
- Displayed VM details correctly

### Test 2: RDP Connection Info
```bash
./sandbox.sh connect
```
**Result**: ✅ PASS
- Retrieved public IP: 4.147.176.243
- Displayed connection details
- Generated RDP command

### Test 3: Cost Information
```bash
./sandbox.sh cost
```
**Result**: ✅ PASS
- Displayed accurate cost breakdown
- Showed savings potential: ~$47/month
- All calculations correct for Standard_D2as_v5

---

## ⏭️ Deployment Test (Requires PowerShell)

### Prerequisites Check
- ✅ Azure CLI: Installed and working
- ❌ PowerShell (pwsh): Not installed on this Mac
- ✅ Azure Subscription: Connected successfully
- ✅ VM: Found and accessible

### Deployment Steps Ready
The deployment would execute these steps:

1. **Connect to Azure** ✅ (Tested)
   - Switch to subscription: 9b8e7b3f-d3e7-4da9-a22a-9bf7c8ee4dde
   - Verify VM exists in DEV-RG

2. **Create Automation Account**
   - Name: sandbox-vm-idle-shutdown
   - Location: australiaeast
   - Plan: Basic

3. **Configure Managed Identity**
   - Enable system-assigned identity
   - Assign RBAC roles:
     - Virtual Machine Contributor (on win11-vscode)
     - Monitoring Reader (on win11-vscode)

4. **Import PowerShell Modules**
   - Az.Accounts
   - Az.Compute
   - Az.Monitor
   - Az.Resources

5. **Deploy Runbook**
   - Upload: azure_vm_idle_shutdown_runbook.ps1
   - Publish runbook

6. **Create Webhook**
   - Generate unique URI
   - Link to runbook

7. **Create Action Group**
   - Name: sandbox-vm-idle-actions
   - Add webhook receiver

8. **Create Alert Rule**
   - Name: sandbox-idle-alert
   - Condition: CPU < 5% for 30 minutes
   - Frequency: Check every 5 minutes
   - Action: Trigger webhook → runbook

9. **Test Runbook**
   - Execute dry run
   - Verify metrics retrieval
   - Confirm logic works

---

## 📋 Deployment Options

### Option 1: On Mac (PowerShell Required)
```bash
# Install PowerShell first
brew install powershell

# Then deploy
cd ~/maia/claude/tools/sre
./deploy_sandbox_idle_shutdown.sh
```

### Option 2: Via Azure Portal
1. Open https://portal.azure.com
2. Follow manual deployment steps in SANDBOX_DEPLOYMENT_GUIDE.md
3. Upload runbook via portal interface

### Option 3: From Windows VM (Easiest)
```powershell
# RDP to win11-vscode (4.147.176.243)
# Clone repo or copy scripts to VM
cd C:\maia\claude\tools\sre
./Setup-SandboxVMIdleShutdown.ps1
```

---

## ✅ All Systems Ready

### What Works Now
- ✅ Subscription access (Visual Studio Enterprise)
- ✅ VM found and accessible (win11-vscode in DEV-RG)
- ✅ Helper script fully functional
- ✅ All configuration files correct
- ✅ Runbook script ready to deploy
- ✅ Documentation complete

### What Needs PowerShell
- ⏳ Actual deployment of Automation Account
- ⏳ Runbook upload and publishing
- ⏳ Alert rule creation
- ⏳ Full end-to-end testing

### Recommendation
**Deploy from the Windows VM itself** - Most straightforward approach:
1. RDP to win11-vscode (already running)
2. Open PowerShell on the VM
3. Clone Maia repo or copy scripts
4. Run `./Setup-SandboxVMIdleShutdown.ps1`
5. System monitors itself and auto-shuts down when idle

---

## 💡 Alternative: Manual Azure CLI Deployment

If PowerShell is unavailable, I can create Azure CLI versions of the deployment scripts. Would you like that?

---

## Summary

**Status**: ✅ All configuration verified and ready
**Helper Scripts**: ✅ Working perfectly
**Deployment**: ⏳ Pending PowerShell availability
**Next Step**: Install PowerShell or deploy from Windows VM

**Estimated Deployment Time**: 10-15 minutes (once PowerShell available)
**Estimated Savings**: ~$47/month (for 8h/day usage pattern)
