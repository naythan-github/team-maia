# Copy Scripts to win11-vscode VM

## Easiest Method: RDP + Copy/Paste

**Step 1: RDP to VM**
```
Host: 4.147.176.243
User: azureuser
```

**Step 2: On VM, open PowerShell as Administrator**

**Step 3: Create directory**
```powershell
New-Item -Path C:\MaiaScripts -ItemType Directory -Force
cd C:\MaiaScripts
```

**Step 4: Copy main setup script**

Copy this entire script and paste into VM PowerShell, save as `Setup-SandboxVMIdleShutdown.ps1`:

**File location on Mac**: `/Users/YOUR_USERNAME/maia/claude/tools/sre/Setup-SandboxVMIdleShutdown.ps1`

```powershell
# Run this to create the file on VM
$content = @'
[PASTE CONTENT HERE FROM Setup-SandboxVMIdleShutdown.ps1]
'@

Set-Content -Path "C:\MaiaScripts\Setup-SandboxVMIdleShutdown.ps1" -Value $content
```

---

## Alternative: GitHub Clone (Easiest!)

**On VM:**
```powershell
# Install Git (if not already installed)
winget install Git.Git

# Clone Maia repo
cd C:\
git clone https://github.com/naythan-orro/maia.git

# Navigate to scripts
cd C:\maia\claude\tools\sre

# Run setup
.\Setup-SandboxVMIdleShutdown.ps1
```

---

## Alternative: Azure File Share

**Step 1: Create file share (from Mac)**
```bash
# Create storage account
az storage account create \
  --name maiafiles$(date +%s) \
  --resource-group DEV-RG \
  --location australiaeast \
  --sku Standard_LRS

# Create file share
az storage share create \
  --name scripts \
  --account-name <storage-account-name>

# Upload files
az storage file upload-batch \
  --destination scripts \
  --source ~/maia/claude/tools/sre \
  --account-name <storage-account-name>
```

**Step 2: Mount on VM (in PowerShell)**
```powershell
# Get connection string from Azure Portal
net use Z: \\<storageaccount>.file.core.windows.net\scripts /user:<username> <password>
cd Z:\
.\Setup-SandboxVMIdleShutdown.ps1
```

---

## Alternative: Download from Azure VM Extension

**From Mac:**
```bash
# Zip the scripts
cd ~/maia/claude/tools/sre
tar -czf /tmp/maia-scripts.tar.gz *.ps1 *.md *.json

# Upload to blob storage (create container first)
az storage blob upload \
  --account-name <storage> \
  --container-name scripts \
  --name maia-scripts.tar.gz \
  --file /tmp/maia-scripts.tar.gz

# Get SAS URL
az storage blob generate-sas \
  --account-name <storage> \
  --container-name scripts \
  --name maia-scripts.tar.gz \
  --permissions r \
  --expiry 2026-01-10 \
  --output tsv
```

**On VM:**
```powershell
# Download and extract
Invoke-WebRequest -Uri "<SAS-URL>" -OutFile C:\maia-scripts.tar.gz
# Extract with 7zip or tar (Windows 11 has tar built-in)
tar -xzf C:\maia-scripts.tar.gz -C C:\MaiaScripts
```

---

## RECOMMENDED: GitHub Clone Method

This is the simplest because:
1. Repo is already public (or use your credentials)
2. One command gets everything
3. Easy to update later with `git pull`
4. No manual file transfer

**Just run on VM:**
```powershell
cd C:\
git clone https://github.com/naythan-orro/maia.git
cd C:\maia\claude\tools\sre
.\Setup-SandboxVMIdleShutdown.ps1
```

Done!

---

## Files You Need (if manual copy)

**Minimum files for deployment:**
1. `Setup-SandboxVMIdleShutdown.ps1` (main setup script)
2. `azure_vm_idle_shutdown_runbook.ps1` (the runbook)
3. `Manage-VMIdleShutdown.ps1` (management utility)

**Optional but useful:**
4. `SANDBOX_README.md` (usage guide)
5. `sandbox_environment.json` (config reference)
