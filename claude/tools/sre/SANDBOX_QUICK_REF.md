# Sandbox Environment - Quick Reference

## ⚡ Instant Access

### Azure CLI
```bash
# Switch to sandbox subscription
az account set --subscription 9b8e7b3f-d3e7-4da9-a22a-9bf7c8ee4dde

# Quick commands
az vm start -g DEV-RG -n win11-vscode      # Start VM
az vm stop -g DEV-RG -n win11-vscode       # Stop VM
az vm deallocate -g DEV-RG -n win11-vscode # Deallocate (save costs)
```

### PowerShell
```powershell
# Switch to sandbox subscription
Set-AzContext -SubscriptionId 9b8e7b3f-d3e7-4da9-a22a-9bf7c8ee4dde

# Quick commands
Start-AzVM -ResourceGroupName DEV-RG -Name win11-vscode
Stop-AzVM -ResourceGroupName DEV-RG -Name win11-vscode
Get-AzVM -ResourceGroupName DEV-RG -Name win11-vscode -Status
```

---

## 📋 Environment Details

| Property | Value |
|----------|-------|
| **Subscription** | Visual Studio Enterprise Subscription – MPN |
| **Subscription ID** | `9b8e7b3f-d3e7-4da9-a22a-9bf7c8ee4dde` |
| **Tenant** | ORRO PTY LTD (Orrogroup.onmicrosoft.com) |
| **Resource Group** | `DEV-RG` |
| **VM Name** | `win11-vscode` |
| **Location** | `australiaeast` |
| **VM Size** | `Standard_D2as_v5` (2 vCPU, 8 GB RAM, AMD) |
| **OS** | Windows 11 Enterprise 23H2 |
| **Admin User** | `azureuser` |
| **Created** | 2026-01-09 |

---

## 💰 Cost Info

| Metric | Value |
|--------|-------|
| Hourly (running) | ~$0.096/hour |
| Monthly 24/7 | ~$70/month |
| Monthly 8h/day | ~$23/month |
| Storage | ~$8/month |
| **When stopped** | **$0/hour** |

**Potential savings with idle shutdown**: ~$47/month

---

## 🚀 Deploy Idle Shutdown

```bash
cd ~/maia/claude/tools/sre
./deploy_sandbox_idle_shutdown.sh
```

Or PowerShell:
```powershell
cd ~/maia/claude/tools/sre
./Setup-SandboxVMIdleShutdown.ps1
```

---

## 📂 Config Files

- **Full config**: [sandbox_environment.json](sandbox_environment.json)
- **Deployment guide**: [SANDBOX_DEPLOYMENT_GUIDE.md](SANDBOX_DEPLOYMENT_GUIDE.md)
- **Usage guide**: [SANDBOX_README.md](SANDBOX_README.md)

---

## 🔗 Resource IDs

**VM Resource ID:**
```
/subscriptions/9b8e7b3f-d3e7-4da9-a22a-9bf7c8ee4dde/resourceGroups/DEV-RG/providers/Microsoft.Compute/virtualMachines/win11-vscode
```

**VM UUID:**
```
87bb952d-8e83-4fcd-8098-68ab94d323cc
```

---

## 🏷️ Tags

```json
{
  "environment": "dev",
  "os": "windows11",
  "purpose": "maia-testing",
  "tools": "vscode"
}
```

---

**Last Updated**: 2026-01-09
