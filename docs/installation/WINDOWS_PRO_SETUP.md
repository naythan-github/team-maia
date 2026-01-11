# Windows Professional Setup Guide
## VSCode, WSL, and Claude Code Installation

**Target OS:** Windows 10/11 Professional
**Installation Method:** Microsoft Store (preferred) + Command Line
**Estimated Time:** 20-30 minutes
**Last Updated:** 2026-01-11

---

## Overview

This guide provides the **optimal installation sequence** for setting up a complete Claude Code development environment on Windows Professional using WSL, Ubuntu, and VSCode.

**Why this order matters:**
1. WSL must be enabled before installing Linux distributions
2. Ubuntu provides the runtime environment for Claude Code
3. VSCode integrates with WSL after both are installed
4. Claude Code runs inside Ubuntu (WSL)

---

## Prerequisites

### System Requirements
- **OS:** Windows 10 Pro (build 19041+) or Windows 11 Pro
- **CPU:** 64-bit processor with virtualization support
- **RAM:** 8 GB minimum, 16 GB recommended
- **Disk:** 20 GB free space minimum
- **Network:** Active internet connection
- **Account:** Administrator access required

### For Azure VMs (Important!)
If installing on an Azure VM:
- **VM Size:** D-series v3+ (D4s_v3 minimum recommended)
- **Security Type:** **Standard** (NOT Trusted Launch - blocks nested virtualization)
- See [Azure D-Series Requirements](#appendix-azure-vm-requirements) for details

---

## Installation Sequence

### Phase 1: Enable WSL (Foundation)

WSL (Windows Subsystem for Linux) must be installed first as it's the foundation for running Ubuntu.

#### Step 1.1: Enable WSL Feature

Open **PowerShell as Administrator**:
- Press `Win + X`
- Select "Windows Terminal (Admin)" or "PowerShell (Admin)"

Run the installation command:
```powershell
wsl --install --no-distribution
```

**What this does:**
- Enables WSL 2 feature
- Enables Virtual Machine Platform
- Downloads WSL kernel
- Does NOT install a Linux distribution yet (we'll use Store for that)

**Expected Output:**
```
Installing: Windows Subsystem for Linux
Windows Subsystem for Linux has been installed.
Installing: Virtual Machine Platform
Virtual Machine Platform has been installed.
The requested operation is successful. Changes will not be effective until the system is rebooted.
```

#### Step 1.2: Restart Computer

**CRITICAL:** Restart is required for WSL to activate.

```powershell
Restart-Computer
```

Or manually restart via Start Menu.

#### Step 1.3: Verify WSL Installation

After restart, open PowerShell (Administrator not required) and verify:

```powershell
wsl --version
```

**Expected Output:**
```
WSL version: 2.0.x.x
Kernel version: 5.15.x.x
WSLg version: 1.0.x
...
```

**Verification checklist:**
- [ ] WSL version shows 2.0.x or higher
- [ ] Kernel version displays
- [ ] No error messages

**Troubleshooting:**
If `wsl --version` fails with "command not found":
```powershell
# Manually enable features
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

# Restart and try again
Restart-Computer
```

---

### Phase 2: Install Ubuntu (Operating System)

With WSL enabled, install Ubuntu from Microsoft Store.

#### Step 2.1: Open Microsoft Store

**Method A: Start Menu**
- Press `Win` key
- Type "Microsoft Store"
- Press `Enter`

**Method B: Run Command**
- Press `Win + R`
- Type: `ms-windows-store:`
- Press `Enter`

#### Step 2.2: Install Ubuntu 22.04 LTS

1. In Microsoft Store search box, type: **Ubuntu 22.04**
2. Click **"Ubuntu 22.04.3 LTS"** (official Canonical app)
3. Click **"Get"** or **"Install"**
4. Wait for download to complete (~450 MB)

**Store Link:**
```
ms-windows-store://pdp/?ProductId=9PN20MSR04DW
```

#### Step 2.3: First Launch Setup

After installation completes:

1. Click **"Open"** in Microsoft Store
   - Or press `Win` key, type "Ubuntu", press `Enter`

2. Wait for Ubuntu to initialize (1-2 minutes)
   ```
   Installing, this may take a few minutes...
   ```

3. **Create Unix User Account** when prompted:
   ```
   Enter new UNIX username: yourusername
   New password: ********
   Retype new password: ********
   ```

   **Recommendations:**
   - Username: lowercase, no spaces (e.g., `maia`, `dev`, your firstname)
   - Password: Strong password (you'll need this for `sudo` commands)
   - Password won't display while typing (normal behavior)

4. Successful setup shows:
   ```
   Installation successful!
   yourusername@hostname:~$
   ```

#### Step 2.4: Verify Ubuntu Installation

In the Ubuntu terminal that just opened:

```bash
# Check Ubuntu version
lsb_release -a

# Check WSL version (should show 2)
cat /proc/version
```

**Expected Output:**
```
Distributor ID: Ubuntu
Description:    Ubuntu 22.04.3 LTS
Release:        22.04
Codename:       jammy
```

From PowerShell (optional verification):
```powershell
wsl --list --verbose
```

**Expected Output:**
```
  NAME            STATE           VERSION
* Ubuntu-22.04    Running         2
```

**Verification checklist:**
- [ ] Ubuntu terminal opens successfully
- [ ] User account created
- [ ] Shows Ubuntu 22.04.x LTS
- [ ] WSL version is 2 (not 1)

---

### Phase 3: Install VSCode (IDE)

With WSL and Ubuntu running, install VSCode to integrate with your Linux environment.

#### Step 3.1: Install VSCode from Microsoft Store

**IMPORTANT:** Use Microsoft Store version for automatic updates and Windows integration.

1. Open **Microsoft Store**
2. Search for: **Visual Studio Code**
3. Select **"Visual Studio Code"** (by Microsoft Corporation)
4. Click **"Get"** or **"Install"**
5. Wait for installation (~200 MB)

**Store Link:**
```
ms-windows-store://pdp/?ProductId=XP9KHM4BK9FZ7Q
```

**Alternative: Direct Download**
If Store version is unavailable:
1. Visit: https://code.visualstudio.com/download
2. Download "Windows x64 User Installer"
3. Run installer
4. **CHECK:** "Add to PATH" during installation
5. Complete installation

#### Step 3.2: Verify VSCode Installation

Open PowerShell:
```powershell
code --version
```

**Expected Output:**
```
1.85.x
abc123def456...
x64
```

#### Step 3.3: Install WSL Extension (Critical!)

**Method A: Command Line (Fastest)**
```powershell
code --install-extension ms-vscode-remote.remote-wsl
```

**Method B: VSCode UI**
1. Launch VSCode
2. Press `Ctrl + Shift + X` (Extensions panel)
3. Search: **WSL**
4. Install: **"WSL"** by Microsoft
   - Extension ID: `ms-vscode-remote.remote-wsl`
5. Click **"Install"**

#### Step 3.4: Verify WSL Extension

Open VSCode, then:
- Press `F1`
- Type: `WSL`
- Should see commands like:
  - "WSL: Open Folder in WSL..."
  - "WSL: Connect to WSL"
  - "WSL: Reopen Folder in WSL"

**Verification checklist:**
- [ ] VSCode opens successfully
- [ ] `code --version` works in PowerShell
- [ ] WSL extension installed
- [ ] WSL commands appear in command palette

---

### Phase 4: Install Claude Code (CLI Tool)

Final step: Install Claude Code CLI inside Ubuntu (WSL).

#### Step 4.1: Update Ubuntu System Packages

Open Ubuntu terminal:
```bash
sudo apt update && sudo apt upgrade -y
```

Enter your Ubuntu password when prompted.

**Expected Output:**
```
Hit:1 http://archive.ubuntu.com/ubuntu jammy InRelease
...
Reading package lists... Done
```

#### Step 4.2: Install Node.js (Claude Code Dependency)

Claude Code requires Node.js 18+. Install via NodeSource repository:

```bash
# Download and run NodeSource setup script
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -

# Install Node.js
sudo apt install -y nodejs

# Verify installation
node --version
npm --version
```

**Expected Output:**
```
v20.11.x
10.2.x
```

**Verification checklist:**
- [ ] Node.js version 20.x or higher
- [ ] npm version 10.x or higher
- [ ] No errors during installation

#### Step 4.3: Install Claude Code CLI

```bash
# Install Claude Code globally
npm install -g @anthropic-ai/claude-code

# Verify installation
claude --version
```

**Expected Output:**
```
2.x.x (Claude Code)
```

**Troubleshooting:**
If `claude: command not found`:
```bash
# Add npm global bin to PATH
echo 'export PATH="$HOME/.npm-global/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Try reinstalling
npm install -g @anthropic-ai/claude-code
```

#### Step 4.4: Authenticate Claude Code

```bash
# Launch Claude Code authentication
claude
```

**What happens:**
1. Claude Code opens authentication prompt
2. Browser window launches with Anthropic login
3. Log in with your Anthropic account
4. Authorize the application
5. Return to terminal - authentication complete

**Expected Output:**
```
? Ready to authenticate with Claude? (Y/n) Y
Opening browser for authentication...
✓ Successfully authenticated!
```

**Verification checklist:**
- [ ] `claude --version` displays version
- [ ] Authentication completes successfully
- [ ] Claude Code prompt appears

---

## Post-Installation Configuration

### Set Up Development Environment

#### 1. Configure Environment Variables

Add to `~/.bashrc`:
```bash
# Open bashrc in editor
nano ~/.bashrc

# Add these lines at the end:
export MAIA_ROOT=~/maia
export PYTHONPATH=~/maia

# Save: Ctrl+O, Enter, Ctrl+X
```

Reload configuration:
```bash
source ~/.bashrc
```

#### 2. Install Python Build Tools

For Python development (if needed):
```bash
sudo apt install -y python3 python3-pip python3-venv build-essential \
    libssl-dev libffi-dev python3-dev git curl wget
```

#### 3. Configure Git

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Verify
git config --list
```

#### 4. Install VSCode Python Extension

From VSCode (while connected to WSL):
```bash
code --install-extension ms-python.python
```

---

## Testing the Complete Setup

### Test 1: WSL Integration

From PowerShell:
```powershell
# Open Ubuntu directly
wsl -d Ubuntu-22.04

# Check you're in WSL
uname -a
```

Expected: `Linux ... Microsoft ... WSL2`

### Test 2: VSCode + WSL Integration

```powershell
# Open VSCode connected to WSL
code --remote wsl+Ubuntu-22.04 ~
```

Expected:
- VSCode opens
- Bottom left corner shows: **"WSL: Ubuntu-22.04"** (green badge)
- Integrated terminal shows Linux prompt

### Test 3: Claude Code from VSCode

In VSCode:
1. Open integrated terminal: `Ctrl + ` ` (backtick)
2. Terminal should show Ubuntu prompt
3. Run: `claude --version`
4. Expected: Version number displays

### Test 4: Full Workflow

```bash
# Create test project
mkdir ~/test-claude
cd ~/test-claude

# Initialize git
git init

# Open in VSCode
code .

# Start Claude Code
claude
```

**Success criteria:**
- [ ] Directory created in WSL filesystem
- [ ] Git initializes
- [ ] VSCode opens project in WSL context
- [ ] Claude Code launches successfully
- [ ] Can interact with Claude in terminal

---

## Daily Usage Workflow

### Starting a Session

**Option A: From Windows (Recommended)**
```powershell
# Open project in VSCode + WSL
code --remote wsl+Ubuntu-22.04 ~/your-project

# VSCode opens → Use integrated terminal → Run 'claude'
```

**Option B: From Ubuntu Terminal**
```bash
# Launch Ubuntu
wsl -d Ubuntu-22.04

# Navigate to project
cd ~/your-project

# Start Claude Code
claude
```

### Working with Files

**Best Practice:** Keep projects in WSL filesystem for best performance.

```bash
# Good (fast) - WSL filesystem
~/projects/my-app

# Bad (slow) - Windows filesystem via WSL
/mnt/c/Users/YourName/projects/my-app
```

**Accessing WSL files from Windows:**
- Windows Explorer: `\\wsl$\Ubuntu-22.04\home\yourusername\`
- Network path works for drag-drop, file operations

---

## Troubleshooting

### Issue 1: WSL Command Not Found

**Symptom:**
```powershell
wsl : The term 'wsl' is not recognized...
```

**Solution:**
```powershell
# Check Windows version
winver

# Must be Windows 10 build 19041+ or Windows 11
# Update Windows if needed:
Start-Process "ms-settings:windowsupdate"
```

---

### Issue 2: Ubuntu Installation Fails with Error 0x80370102

**Symptom:**
```
WslRegisterDistribution failed with error: 0x80370102
The virtual machine could not be started because a required feature is not installed.
```

**Solution - Enable Virtualization in BIOS:**

1. Restart computer
2. Enter BIOS/UEFI (usually F2, F10, Del, or Esc during boot)
3. Find virtualization settings:
   - Intel: "Intel VT-x" or "Intel Virtualization Technology"
   - AMD: "SVM Mode" or "AMD-V"
4. Enable the setting
5. Save and exit BIOS
6. Boot Windows and try Ubuntu installation again

**Solution - For Azure VMs:**
- Ensure VM is D-series v3+ (not B-series)
- Security Type must be **Standard** (NOT Trusted Launch)
- See [Appendix: Azure VM Requirements](#appendix-azure-vm-requirements)

---

### Issue 3: VSCode Not Finding WSL

**Symptom:**
VSCode shows "WSL: Ubuntu-22.04" but terminal fails to open.

**Solution:**
```powershell
# Restart WSL
wsl --shutdown
wsl -d Ubuntu-22.04

# Restart VSCode
# Try reconnecting
```

---

### Issue 4: Claude Code Installation Fails

**Symptom:**
```
npm ERR! code EACCES
npm ERR! syscall mkdir
npm ERR! path /usr/local/lib/node_modules/@anthropic-ai
```

**Solution - Fix npm Permissions:**
```bash
# Configure npm to use user directory
mkdir -p ~/.npm-global
npm config set prefix '~/.npm-global'

# Add to PATH
echo 'export PATH="$HOME/.npm-global/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Retry installation
npm install -g @anthropic-ai/claude-code
```

---

### Issue 5: Slow Performance in WSL

**Symptom:**
- File operations lag
- Git commands slow
- VSCode sluggish

**Solution - Move to WSL Filesystem:**
```bash
# Check current location
pwd

# If shows /mnt/c/... (Windows filesystem), move to WSL:
cd ~
mkdir projects
mv /mnt/c/path/to/project ~/projects/

# Work from ~/projects/ for best performance
```

**Why:** Cross-filesystem access (WSL ↔ Windows) has significant overhead.

---

### Issue 6: Authentication Token Expired

**Symptom:**
```
Error: Authentication token expired or invalid
```

**Solution:**
```bash
# Re-authenticate
claude --logout
claude

# Follow authentication flow again
```

---

## Maintenance & Updates

### Update WSL

```powershell
# Update WSL itself
wsl --update

# Check version
wsl --version
```

### Update Ubuntu

```bash
sudo apt update && sudo apt upgrade -y
```

### Update VSCode

If installed from Microsoft Store:
- Updates automatically via Windows Update

If manually installed:
- VSCode shows notification when updates available
- Help → Check for Updates

### Update Claude Code

```bash
npm update -g @anthropic-ai/claude-code
```

### Update Node.js

```bash
# Check current version
node --version

# Update via NodeSource (if needed)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

---

## Uninstallation

### Remove Claude Code
```bash
npm uninstall -g @anthropic-ai/claude-code
```

### Remove Node.js
```bash
sudo apt remove nodejs npm
sudo apt autoremove
```

### Remove Ubuntu from WSL
```powershell
# WARNING: Deletes all Ubuntu data!
wsl --unregister Ubuntu-22.04
```

### Remove VSCode

**If from Microsoft Store:**
- Settings → Apps → Visual Studio Code → Uninstall

**If manually installed:**
- Control Panel → Programs → Uninstall

### Disable WSL Completely
```powershell
# Disable features
dism.exe /online /disable-feature /featurename:Microsoft-Windows-Subsystem-Linux
dism.exe /online /disable-feature /featurename:VirtualMachinePlatform

# Restart required
Restart-Computer
```

---

## Appendix: Azure VM Requirements

### Required VM Configuration for WSL2

If installing on Azure Windows VMs, nested virtualization is required for WSL2.

**Supported VM Series:**
- **D-series:** Dv3, Dsv3, Dv4, Dsv4, Dv5, Dsv5 (all sizes)
- **E-series:** Ev3, Esv3, Ev4, Esv4, Ev5, Esv5 (all sizes)

**Minimum Recommended:**
- **Standard_D4s_v3** (4 vCPUs, 16 GB RAM)
- **Standard_D8s_v3** (8 vCPUs, 32 GB RAM) for better performance

**NOT Supported:**
- **B-series** (Burstable) - No nested virtualization
- **A-series** (Basic) - No nested virtualization

### Critical VM Settings

**1. Security Type: MUST be Standard**

When creating VM in Azure Portal:
- **Basics** tab → **Security type** dropdown
- Select: **Standard**
- Do NOT use: **Trusted launch** (blocks nested virtualization)

**2. VM Generation: Gen 2 Recommended**
- Supports UEFI boot
- Better performance
- Required for some VM sizes

**3. Enable Accelerated Networking**
- Improves network performance
- Reduces latency
- Available on most D/E series VMs

### Verification After VM Creation

Connect to VM and run in PowerShell:
```powershell
# Check if nested virtualization is enabled
systeminfo | findstr /i "Hyper-V"
```

**Expected Output:**
```
Hyper-V Requirements:      VM Monitor Mode Extensions: Yes
                           Virtualization Enabled In Firmware: Yes
                           Second Level Address Translation: Yes
                           Data Execution Prevention Available: Yes
```

If "No" appears, VM does not support nested virtualization - resize to D/E series.

### Resizing Existing VM

If current VM doesn't support WSL2:

```powershell
# From Azure Cloud Shell or Azure CLI
az vm resize --resource-group YourRG --name YourVM --size Standard_D4s_v3

# Or via Azure Portal:
# VM → Size → Select D4s_v3 or higher → Resize
```

**Note:** VM will restart during resize operation.

---

## Quick Reference Card

### Essential Commands

**PowerShell (Windows):**
```powershell
# Open Ubuntu
wsl -d Ubuntu-22.04

# Open VSCode in WSL
code --remote wsl+Ubuntu-22.04 ~/project

# Check WSL status
wsl --list --verbose

# Restart WSL
wsl --shutdown
```

**Bash (Ubuntu/WSL):**
```bash
# Navigate to project
cd ~/project

# Start Claude Code
claude

# Check versions
node --version
npm --version
claude --version
python3 --version

# Update system
sudo apt update && sudo apt upgrade -y
```

**VSCode:**
```
Ctrl + Shift + P  → Command Palette
Ctrl + `          → Toggle Terminal
F1                → Command Palette
Ctrl + Shift + X  → Extensions
```

### File System Paths

**WSL from Windows:**
```
\\wsl$\Ubuntu-22.04\home\yourusername\
```

**Windows from WSL:**
```
/mnt/c/Users/YourName/
```

**Project Locations (Best Practice):**
```bash
# Good - Fast (WSL filesystem)
~/projects/my-app

# Avoid - Slow (Windows filesystem)
/mnt/c/Users/YourName/projects/my-app
```

---

## Installation Checklist

Print and check off each step:

### Phase 1: WSL
- [ ] Ran `wsl --install --no-distribution`
- [ ] Restarted computer
- [ ] Verified with `wsl --version`

### Phase 2: Ubuntu
- [ ] Installed Ubuntu 22.04 from Microsoft Store
- [ ] Completed first-launch user setup
- [ ] Verified with `lsb_release -a`
- [ ] Confirmed WSL version 2 with `wsl --list --verbose`

### Phase 3: VSCode
- [ ] Installed VSCode from Microsoft Store (or website)
- [ ] Verified with `code --version`
- [ ] Installed WSL extension
- [ ] Verified WSL commands in Command Palette

### Phase 4: Claude Code
- [ ] Ran `sudo apt update && sudo apt upgrade`
- [ ] Installed Node.js 20.x
- [ ] Verified Node with `node --version`
- [ ] Installed Claude Code with `npm install -g`
- [ ] Verified with `claude --version`
- [ ] Completed authentication with `claude`

### Post-Installation
- [ ] Configured environment variables in `~/.bashrc`
- [ ] Installed Python tools (if needed)
- [ ] Configured Git username and email
- [ ] Tested VSCode + WSL integration
- [ ] Created test project and launched Claude

---

## Support Resources

### Official Documentation
- **WSL:** https://docs.microsoft.com/en-us/windows/wsl/
- **VSCode Remote:** https://code.visualstudio.com/docs/remote/wsl
- **Claude Code:** https://claude.ai/code
- **Node.js:** https://nodejs.org/en/docs/

### Community
- **WSL GitHub:** https://github.com/microsoft/WSL/issues
- **VSCode GitHub:** https://github.com/microsoft/vscode/issues
- **Claude Code:** https://github.com/anthropics/claude-code/issues

### Troubleshooting Commands
```powershell
# WSL diagnostics
wsl --status
wsl --list --all --verbose

# Update WSL
wsl --update

# Check Windows version
winver

# View WSL logs
Get-Content "$env:LOCALAPPDATA\Packages\CanonicalGroupLimited.Ubuntu22.04LTS_*\LocalState\install.log"
```

---

**Guide Version:** 1.0
**Last Updated:** 2026-01-11
**Tested On:** Windows 11 Pro 23H2, Windows 10 Pro 22H2
**Status:** ✅ Production Ready
