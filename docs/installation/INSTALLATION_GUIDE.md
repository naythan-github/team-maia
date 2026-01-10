# Maia Installation Guide for Windows (v3.0)

**Last Updated:** 2026-01-10
**Script Version:** 3.0
**Estimated Time:** 15-20 minutes

---

## Overview

This guide walks you through setting up the Maia AI development environment on Windows using WSL (Windows Subsystem for Linux).

**What You'll Install:**
1. WSL with Ubuntu (Windows component)
2. VSCode (optional but recommended)
3. Maia environment (via automated script)

---

## Part 1: Prerequisites (One-Time Setup)

### Step 1.1: Install WSL with Ubuntu

**Method A: Using PowerShell (Recommended)**

1. Open PowerShell as Administrator:
   - Press `Win + X`
   - Select "Windows PowerShell (Admin)" or "Terminal (Admin)"

2. Run the installation command:
   ```powershell
   wsl --install -d Ubuntu
   ```

3. Wait for installation to complete (5-10 minutes)

4. **IMPORTANT:** Your computer will restart automatically

5. After restart, Ubuntu will launch automatically and ask you to create a user:
   ```
   Enter new UNIX username: maia
   New password: Test123456!
   Retype new password: Test123456!
   ```

6. Verify WSL is working:
   ```powershell
   wsl --list --verbose
   ```

   **Expected Output:**
   ```
   NAME      STATE           VERSION
   * Ubuntu  Running         2
   ```

**Method B: Using Windows Store (Alternative)**

1. Open Microsoft Store
2. Search for "Ubuntu"
3. Click "Ubuntu 22.04 LTS" or latest version
4. Click "Get" or "Install"
5. Once installed, click "Open"
6. Create user account when prompted (username: `maia`, password: `Test123456!`)

**Troubleshooting:**
- If `wsl --install` fails with "This application requires the Windows Subsystem for Linux Optional Component":
  ```powershell
  dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
  dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
  ```
  Then restart and run `wsl --install -d Ubuntu` again.

---

### Step 1.2: Install VSCode (Optional)

**Method A: Download from Website**

1. Visit: https://code.visualstudio.com/download
2. Download "Windows x64 User Installer"
3. Run the installer
4. **IMPORTANT:** Check "Add to PATH" during installation
5. Complete installation

**Method B: Using winget**

```powershell
winget install Microsoft.VisualStudioCode
```

**Verify Installation:**
```powershell
code --version
```

**Expected Output:**
```
1.xx.x
xxxxxxx
x64
```

---

## Part 2: Run Maia Installation Script

### Step 2.1: Access the Script

**If using RDP with network drive (Z:):**
```powershell
# Check script is accessible
Test-Path Z:\Install-MaiaEnvironment-v3.ps1

# If True, proceed to Step 2.2
# If False, map network drive or copy script locally
```

**If copying script locally:**
1. Copy `Install-MaiaEnvironment-v3.ps1` to `C:\scripts\`
2. Open PowerShell as Administrator
3. Navigate to script location:
   ```powershell
   cd C:\scripts
   ```

---

### Step 2.2: Check Prerequisites

Before running the full installation, verify prerequisites:

```powershell
.\Install-MaiaEnvironment-v3.ps1 -CheckOnly
```

**Expected Output:**
```
============================================================
MAIA Environment Installer v3.0
============================================================

MODE: Check Only

[1] Checking Prerequisites
[OK]   WSL is installed
[OK]   Ubuntu distro: Ubuntu
[OK]   VSCode installed
...
============================================================
Check Summary
============================================================

PASSED (X):
  + WSL is installed
  + Ubuntu: Ubuntu
  + VSCode installed
```

**If you see errors:**
- `[FAIL] WSL not installed` → Go back to Step 1.1
- `[FAIL] No Ubuntu distro found` → Go back to Step 1.1
- `[WARN] VSCode not installed` → Optional, you can continue

---

### Step 2.3: Run Full Installation

Once prerequisites check passes, run the full installation:

```powershell
.\Install-MaiaEnvironment-v3.ps1
```

**What Happens:**
1. ✅ Checks prerequisites (WSL, Ubuntu, VSCode)
2. ✅ Updates Ubuntu package lists
3. ✅ Installs Python 3.11 + build tools (~2 minutes)
4. ✅ Installs Node.js LTS (~2 minutes)
5. ✅ Installs Claude Code CLI (~1 minute)
6. ✅ Clones Maia repository from GitHub (~30 seconds)
7. ✅ Installs Python dependencies (~2 minutes)
8. ✅ Configures environment variables
9. ✅ Installs MCP servers (~1 minute)

**Total Time:** ~8-10 minutes

**Expected Final Output:**
```
============================================================
Installation Summary
============================================================

PASSED (10):
  + WSL is installed
  + Ubuntu: Ubuntu
  + Python installed: Python 3.11.x
  + Node.js installed: v20.x.x
  + Claude Code installed: 2.x.x
  + Maia repository cloned
  + Python dependencies installed
  + Environment configured
  + MCP servers installed

============================================================
Next Steps
============================================================

Installation complete! To start:

  wsl -d Ubuntu
  cd ~/maia
  claude
```

---

## Part 3: Verify Installation

### Step 3.1: Open WSL

```powershell
wsl -d Ubuntu
```

You should see:
```
maia@hostname:~$
```

### Step 3.2: Navigate to Maia

```bash
cd ~/maia
pwd
```

**Expected Output:**
```
/home/maia/maia
```

### Step 3.3: Verify Python

```bash
python3 --version
```

**Expected Output:**
```
Python 3.11.x
```

### Step 3.4: Verify Node.js

```bash
node --version
npm --version
```

**Expected Output:**
```
v20.x.x
10.x.x
```

### Step 3.5: Verify Claude Code

```bash
claude --version
```

**Expected Output:**
```
2.x.x (Claude Code)
```

### Step 3.6: Test Maia Setup Script

```bash
python3 -c "from claude.tools.core.paths import MAIA_ROOT; print(MAIA_ROOT)"
```

**Expected Output:**
```
/home/maia/maia
```

---

## Part 4: Start Using Maia

### Option A: Command Line

1. Open WSL:
   ```powershell
   wsl -d Ubuntu
   ```

2. Navigate to Maia:
   ```bash
   cd ~/maia
   ```

3. Authenticate Claude Code:
   ```bash
   claude
   ```

4. Follow the authentication prompts

### Option B: VSCode (Recommended)

1. Open VSCode

2. Install WSL extension (if not already installed):
   - Press `Ctrl + Shift + X`
   - Search: "WSL"
   - Install "WSL" by Microsoft

3. Open Maia in WSL:
   ```powershell
   code --remote wsl+Ubuntu ~/maia
   ```

   Or from VSCode:
   - Press `F1`
   - Type: "WSL: Open Folder in WSL"
   - Select: `/home/maia/maia`

4. Open integrated terminal in VSCode (`Ctrl + ` `)

5. Authenticate Claude:
   ```bash
   claude
   ```

---

## Common Issues & Solutions

### Issue 1: "wsl: command not found"

**Cause:** WSL not installed or not in PATH

**Solution:**
```powershell
# Check if WSL is installed
dism.exe /online /get-features | findstr /i "linux"

# If not installed, run:
wsl --install
```

---

### Issue 2: "No Ubuntu distro found"

**Cause:** Ubuntu not installed in WSL

**Solution:**
```powershell
# Install Ubuntu
wsl --install -d Ubuntu

# Or from Windows Store:
# https://apps.microsoft.com/detail/9pdxgncfsczv
```

---

### Issue 3: "Git clone failed"

**Cause:** No SSH keys or authentication set up

**Solution A - Use HTTPS (Recommended for first time):**
```powershell
.\Install-MaiaEnvironment-v3.ps1 -MaiaRepo "https://github.com/naythan-orro/maia.git"
```

**Solution B - Set up SSH keys:**
```bash
wsl -d Ubuntu
ssh-keygen -t ed25519 -C "your_email@example.com"
cat ~/.ssh/id_ed25519.pub
# Copy output and add to GitHub: https://github.com/settings/keys
```

---

### Issue 4: "Python dependencies failed"

**Cause:** Network issues or missing system packages

**Solution:**
```bash
wsl -d Ubuntu
cd ~/maia
python3 -m pip install --user -r requirements.txt
```

If still failing, check specific package errors and install missing system dependencies.

---

### Issue 5: "Claude Code not found"

**Cause:** npm global bin not in PATH

**Solution:**
```bash
wsl -d Ubuntu

# Add to .bashrc
echo 'export PATH="$HOME/.npm-global/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Reinstall Claude Code
npm install -g @anthropic-ai/claude-code
```

---

### Issue 6: Script execution policy error

**Error:**
```
File Install-MaiaEnvironment-v3.ps1 cannot be loaded because running scripts is disabled
```

**Solution:**
```powershell
# Temporarily allow script execution
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# Then run script
.\Install-MaiaEnvironment-v3.ps1
```

---

## Advanced Configuration

### Custom Repository

Install from a forked repository:
```powershell
.\Install-MaiaEnvironment-v3.ps1 -MaiaRepo "https://github.com/yourusername/maia.git"
```

### Skip MCP Servers

If you don't need MCP servers:
```powershell
.\Install-MaiaEnvironment-v3.ps1 -SkipMCPServers
```

### Re-run Installation

If installation partially fails, you can re-run the script:
```powershell
.\Install-MaiaEnvironment-v3.ps1
```

The script will:
- ✅ Skip already installed components
- ✅ Show warnings for existing directories
- ✅ Attempt to fix incomplete installations

---

## Uninstallation

### Remove Maia Environment

```bash
wsl -d Ubuntu
rm -rf ~/maia
```

### Remove Ubuntu from WSL

```powershell
wsl --unregister Ubuntu
```

**WARNING:** This deletes ALL data in the Ubuntu distro.

### Remove WSL Completely

```powershell
# Disable WSL features
dism.exe /online /disable-feature /featurename:Microsoft-Windows-Subsystem-Linux
dism.exe /online /disable-feature /featurename:VirtualMachinePlatform

# Restart computer
```

---

## Getting Help

### Script Issues
- Check log file: `C:\scripts\maia_install_v3_log_YYYYMMDD_HHMMSS.txt`
- Run with `-CheckOnly` to diagnose prerequisites
- Review error messages carefully

### Maia Issues
- GitHub Issues: https://github.com/naythan-orro/maia/issues
- Run `/init` in Maia for system initialization
- Check `claude/data/SYSTEM_STATE.md` for system status

### WSL Issues
- Microsoft Docs: https://docs.microsoft.com/en-us/windows/wsl/
- Check WSL version: `wsl --status`
- Update WSL: `wsl --update`

---

## Appendix A: System Requirements

### Minimum Requirements
- **OS:** Windows 10 build 19041 or later, OR Windows 11
- **CPU:** 64-bit processor
- **RAM:** 8 GB
- **Disk:** 20 GB free space
- **Network:** Internet connection

### Recommended Requirements
- **OS:** Windows 11
- **CPU:** 4+ cores
- **RAM:** 16 GB
- **Disk:** 50 GB free space (SSD preferred)
- **Network:** Broadband internet

### For Azure VMs
- **WSL2:** Requires D-series or E-series VMs (nested virtualization support)
- **WSL1:** Works on B-series VMs (no nested virtualization required)

---

## Appendix B: What Gets Installed

### Windows (User Installs)
- WSL (Windows Subsystem for Linux)
- Ubuntu 22.04 LTS distro
- VSCode (optional)

### Ubuntu (Script Installs)
- Python 3.11
- python3.11-venv
- python3-pip
- build-essential
- libssl-dev
- libffi-dev
- python3-dev
- git
- curl
- Node.js LTS (v20.x)
- npm (v10.x)

### Global NPM Packages
- @anthropic-ai/claude-code
- @modelcontextprotocol/server-filesystem
- @modelcontextprotocol/server-github

### Python Packages
- All packages from `~/maia/requirements.txt`

### Maia Repository
- Cloned to: `~/maia`
- Branch: main
- Remote: https://github.com/naythan-orro/maia.git

---

## Appendix C: File Locations

### Windows Paths
- Script: `Z:\Install-MaiaEnvironment-v3.ps1` or `C:\scripts\Install-MaiaEnvironment-v3.ps1`
- Log: `C:\scripts\maia_install_v3_log_YYYYMMDD_HHMMSS.txt`

### WSL Paths (from Windows)
- Ubuntu home: `\\wsl$\Ubuntu\home\maia\`
- Maia repo: `\\wsl$\Ubuntu\home\maia\maia\`

### WSL Paths (from Ubuntu)
- Home: `/home/maia/` or `~/`
- Maia repo: `/home/maia/maia/` or `~/maia/`
- Configuration: `~/.bashrc`
- SSH keys: `~/.ssh/`

---

## Appendix D: Quick Reference

### Essential Commands

**PowerShell (Windows):**
```powershell
# Check prerequisites
.\Install-MaiaEnvironment-v3.ps1 -CheckOnly

# Full installation
.\Install-MaiaEnvironment-v3.ps1

# Open WSL
wsl -d Ubuntu

# Open Maia in VSCode
code --remote wsl+Ubuntu ~/maia
```

**Bash (Ubuntu/WSL):**
```bash
# Navigate to Maia
cd ~/maia

# Authenticate Claude
claude

# Check Python version
python3 --version

# Check Node version
node --version

# Update Maia
cd ~/maia
git pull

# Reinstall Python dependencies
python3 -m pip install --user -r requirements.txt
```

---

## Version History

- **v3.0** (2026-01-10): Major simplification - removed OS component installation
- **v2.20** (2026-01-10): Dynamic distro name detection
- **v2.19** (2026-01-10): App Execution Alias fix
- **Earlier versions**: Full automation attempts (deprecated due to complexity)

---

## Support

For issues or questions:
1. Check this guide's troubleshooting section
2. Review script log files
3. Check GitHub issues: https://github.com/naythan-orro/maia/issues
4. Contact: maiateam

---

**End of Installation Guide**
