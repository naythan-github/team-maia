# Team Onboarding Guide - Maia on Windows WSL

**Purpose**: Complete guide for team members to set up Maia on Windows laptops
**Target Audience**: New team members with Windows laptops
**Time Required**: 30-60 minutes (first time setup)
**Version**: 1.0 (2025-10-21)

---

## Overview

This guide will help you restore the complete Maia environment on your Windows laptop using:
- **WSL 2** (Windows Subsystem for Linux) - Linux environment on Windows
- **VSCode** - Development IDE with WSL integration
- **OneDrive** - Access to Maia backups created on macOS

**What You'll Get**:
- Full Maia codebase (~182 MB)
- All databases and configurations
- Python environment with dependencies
- VSCode workspace configured for WSL development

---

## Prerequisites Check

Before starting, you'll need:

- [ ] **Windows 10 version 2004+** or **Windows 11**
- [ ] **Administrator access** on your laptop
- [ ] **OneDrive access** with YOUR_ORG organization
- [ ] **Internet connection** (for downloading components)
- [ ] **~5 GB free disk space** (WSL + Ubuntu + Maia + dependencies)

---

## Step 1: Run Automated Setup Script

We have a PowerShell script that checks and installs all prerequisites automatically.

### Download the Setup Script

**Option A: From OneDrive** (if you have access to the Maia repository backup):
1. Navigate to: `OneDrive - YOUR_ORG\MaiaBackups\latest_backup\`
2. Look for: `setup_wsl_prerequisites.ps1`
3. Copy to your Desktop

**Option B: From GitHub/Repository** (if shared via Git):
1. Clone or download the Maia repository
2. Navigate to: `claude\tools\sre\setup_wsl_prerequisites.ps1`
3. Copy to your Desktop

### Run the Setup Script

1. **Right-click on PowerShell** → "Run as Administrator"

2. **Navigate to the script**:
   ```powershell
   cd $HOME\Desktop
   ```

3. **Enable script execution** (if needed):
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

4. **Run the setup script**:
   ```powershell
   .\setup_wsl_prerequisites.ps1
   ```

### What the Script Does

The script will automatically:

✅ **Check WSL Installation**
- Installs WSL 2 if missing
- May require system restart

✅ **Check Ubuntu Distribution**
- Installs Ubuntu 22.04 in WSL
- Sets as default distribution

✅ **Check VSCode**
- Downloads and installs VSCode if missing
- Installs Remote - WSL extension

✅ **Check Python in WSL**
- Installs Python 3 and pip in Ubuntu
- Verifies versions

✅ **Check OneDrive**
- Verifies OneDrive folder exists
- Checks for Maia backups

✅ **Check Git in WSL**
- Installs Git in Ubuntu
- Shows configuration instructions

### Expected Output

```
========================================
Maia WSL Prerequisites Setup
========================================

1️⃣  Checking WSL Installation...
✅ WSL is installed

2️⃣  Checking WSL Distribution...
✅ Ubuntu distribution found
✅ Default distribution is set

3️⃣  Checking VSCode Installation...
✅ VSCode found at: C:\Users\YourName\AppData\Local\Programs\Microsoft VS Code\Code.exe

4️⃣  Checking VSCode WSL Extension...
✅ VSCode WSL extension is installed

5️⃣  Checking Python in WSL...
✅ Python found in WSL: Python 3.10.12
✅ pip found in WSL: pip 22.0.2

6️⃣  Checking OneDrive Sync...
✅ OneDrive found at: C:\Users\YourName\OneDrive - YOUR_ORG
✅ Found 5 Maia backup(s)

7️⃣  Checking Git in WSL...
✅ Git found in WSL: git version 2.34.1

========================================
Summary
========================================

✅ All prerequisites are met! ✨
```

### Troubleshooting Setup Script

**Issue**: "Script cannot be loaded because running scripts is disabled"

**Solution**:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

**Issue**: "This script must be run as Administrator"

**Solution**:
- Close PowerShell
- Right-click PowerShell → "Run as Administrator"
- Re-run script

---

**Issue**: "WSL installation incomplete. Please restart and re-run this script"

**Solution**:
- Restart your computer
- Run the script again after restart

---

## Step 2: Complete Ubuntu Setup (First Time Only)

If WSL was just installed, you'll need to complete Ubuntu setup:

1. **Open PowerShell** and type:
   ```powershell
   wsl
   ```

2. **Ubuntu will launch** and ask for:
   - Username (use your first name, lowercase, no spaces)
   - Password (create a secure password, you'll need this for `sudo` commands)

3. **Verify Ubuntu is ready**:
   ```bash
   whoami
   # Should show your username
   ```

---

## Step 3: Access Maia Backup

### Locate the Latest Backup

1. **Open File Explorer**

2. **Navigate to OneDrive**:
   - `OneDrive - YOUR_ORG\MaiaBackups\`

3. **Find the latest backup** (sorted by date):
   - Format: `full_YYYYMMDD_HHMMSS`
   - Example: `full_20251021_182032`

4. **Note the backup folder name** (you'll need it in the next step)

### Verify Backup Contents

Inside the backup folder, you should see:
- `maia_code.tar.gz` (code repository)
- `maia_data_small.tar.gz` (databases)
- `restore_maia.sh` (restoration script)
- `backup_manifest.json` (backup metadata)
- `requirements_freeze.txt` (Python dependencies)

---

## Step 4: Restore Maia

### Open WSL Terminal

**Option A: From PowerShell**:
```powershell
wsl
```

**Option B: From Windows Terminal** (if installed):
- Open Windows Terminal
- Select "Ubuntu" profile

### Navigate to Backup Folder

Replace `YOUR_USERNAME` and `full_YYYYMMDD_HHMMSS` with your values:

```bash
cd "/mnt/c/Users/YOUR_USERNAME/OneDrive - YOUR_ORG/MaiaBackups/full_YYYYMMDD_HHMMSS"
```

**Example**:
```bash
cd "/mnt/c/Users/jsmith/OneDrive - YOUR_ORG/MaiaBackups/full_20251021_182032"
```

**Tip**: Use Tab completion to avoid typing the full path!

### Verify You're in the Right Place

```bash
ls -lh restore_maia.sh
```

Should show:
```
-rwxr-xr-x 1 user user 12K Oct 21 18:20 restore_maia.sh
```

### Run Restore Script

```bash
./restore_maia.sh
```

**If you get "Permission denied"**:
```bash
chmod +x restore_maia.sh
./restore_maia.sh
```

### Follow Restoration Prompts

The script will:

1. **Detect your environment**:
   ```
   🔍 Detecting system environment...
     Platform: Windows Subsystem for Linux (WSL)
     Windows User: jsmith
     OneDrive: /mnt/c/Users/jsmith/OneDrive - YOUR_ORG
   ```

2. **Ask where to install Maia**:
   ```
   📁 Where should Maia be installed?
     1. ~/maia (WSL home directory - recommended for VSCode)
     2. /mnt/c/Users/jsmith/maia (Windows filesystem)
     3. Custom location

   Choice [1]:
   ```

   **Recommendation**: Press Enter (choose option 1 - `~/maia`)

   **Why?**
   - Faster file I/O (native Linux filesystem)
   - Better Git performance
   - VSCode Remote - WSL works best here
   - Avoid Windows/Linux filesystem permission issues

3. **Restore process** (automated):
   ```
   📦 Restoring Maia code...
     ✅ Code restored

   💾 Restoring databases...
     ✅ Databases restored

   ⚙️  Skipping LaunchAgents (WSL environment - not applicable)
     ℹ️  For automated backups on WSL, use cron instead

   🐚 Skipping macOS shell configs (WSL environment)
     ℹ️  WSL typically uses bash

   🔧 Updating configuration paths...
     ✅ Hook paths updated and disabled for safety
     ✅ Settings paths updated

   📦 Installing Python dependencies...
     [pip install output...]
   ```

4. **Completion message**:
   ```
   🎉 Restoration complete!

   Next steps (WSL):
     1. Open VSCode: code ~/maia
     2. Install VSCode WSL extension if not already installed
     3. Set environment variables in ~/.bashrc:
        echo 'export MAIA_ROOT=~/maia' >> ~/.bashrc
        echo 'export PYTHONPATH=~/maia' >> ~/.bashrc
        source ~/.bashrc
   ```

---

## Step 5: Post-Restore Setup

### Set Environment Variables

```bash
# Add Maia environment variables
echo 'export MAIA_ROOT=~/maia' >> ~/.bashrc
echo 'export PYTHONPATH=~/maia' >> ~/.bashrc

# Reload bashrc
source ~/.bashrc

# Verify
echo $MAIA_ROOT
# Should show: /home/yourusername/maia
```

### Configure Git (First Time Only)

```bash
git config --global user.name "Your Full Name"
git config --global user.email "your.email@orroptyltd.com"

# Verify
git config --global --list
```

### Open Maia in VSCode

```bash
code ~/maia
```

This will:
- Launch VSCode on Windows
- Connect to WSL automatically
- Open the Maia folder in WSL context
- Install/enable WSL extensions

**First time**: VSCode may prompt to "Install recommended extensions for WSL" - click Yes!

---

## Step 6: Verify Installation

### Check Directory Structure

```bash
cd ~/maia
ls -lh
```

Should show:
```
drwxr-xr-x  5 user user 4.0K Oct 21 18:30 claude
-rw-r--r--  1 user user  15K Oct 21 18:30 CLAUDE.md
-rw-r--r--  1 user user  12K Oct 21 18:30 README.md
-rw-r--r--  1 user user  89K Oct 21 18:30 SYSTEM_STATE.md
...
```

### Check Python Dependencies

```bash
cd ~/maia
pip3 list | grep anthropic
```

Should show Claude/Anthropic packages.

### Test Python Import

```bash
python3 -c "import sys; sys.path.insert(0, '~/maia'); print('Maia import works!')"
```

### Check Database Files

```bash
ls -lh ~/maia/claude/data/*.db
```

Should show multiple .db files.

### Verify VSCode Integration

In VSCode:
1. Open terminal (Ctrl + `)
2. Should show WSL bash prompt: `user@HOSTNAME:~/maia$`
3. Run: `python3 --version`
4. Should show Python 3.10+ without errors

---

## Using Maia on WSL

### Starting Maia

**From Windows**:
1. Open Windows Terminal or PowerShell
2. Type: `wsl`
3. Type: `cd ~/maia`

**From VSCode**:
1. Open VSCode
2. Press F1 → "WSL: Open Folder in WSL"
3. Navigate to `/home/yourusername/maia`

### Running Python Scripts

```bash
cd ~/maia
python3 claude/agents/agent_loader.py
```

### Git Operations

```bash
cd ~/maia

# Check status
git status

# Pull latest changes
git pull

# Create branch
git checkout -b feature/your-feature

# Commit changes
git add .
git commit -m "Your commit message"

# Push changes
git push origin feature/your-feature
```

### VSCode Tips

**Open Maia anytime**:
```bash
code ~/maia
```

**Recommended Extensions** (install in WSL context):
- Python (`ms-python.python`)
- GitLens (`eamodio.gitlens`)
- Markdown Preview Enhanced (`shd101wyy.markdown-preview-enhanced`)

**Access Windows files from WSL**:
```bash
cd /mnt/c/Users/YOUR_USERNAME/Documents
```

**Access WSL files from Windows**:
- File Explorer → `\\wsl$\Ubuntu\home\yourusername\maia`

---

## Automated Backups (Optional)

While the macOS system handles backups automatically, you can set up automated backups from WSL if needed:

### Set Up Cron Job

```bash
# Edit crontab
crontab -e

# Add daily 3 AM backup (matching macOS schedule)
0 3 * * * cd ~/maia && python3 claude/tools/sre/disaster_recovery_system.py backup
```

**Important**: Backup target must be Windows OneDrive path for sync to work:

```bash
export MAIA_ONEDRIVE_PATH="/mnt/c/Users/YOUR_USERNAME/OneDrive - YOUR_ORG"
python3 claude/tools/sre/disaster_recovery_system.py backup
```

---

## Troubleshooting

### Issue: "bash: ./restore_maia.sh: Permission denied"

**Solution**:
```bash
chmod +x restore_maia.sh
./restore_maia.sh
```

---

### Issue: "OneDrive not found on Windows filesystem"

**Solution**:
1. Verify OneDrive is running in Windows (system tray icon)
2. Check OneDrive folder exists:
   ```bash
   ls "/mnt/c/Users/$USER/OneDrive - YOUR_ORG"
   ```
3. If using personal OneDrive:
   ```bash
   cd "/mnt/c/Users/$USER/OneDrive/MaiaBackups/..."
   ```

---

### Issue: VSCode won't open from WSL

**Solution**:
1. Ensure VSCode is installed on Windows (not in WSL)
2. Verify `code` command works:
   ```bash
   which code
   # Should show: /mnt/c/Users/.../AppData/Local/Programs/Microsoft VS Code/bin/code
   ```
3. If missing, reinstall VSCode with "Add to PATH" option

---

### Issue: Slow file operations in WSL

**Cause**: You installed Maia on Windows filesystem (`/mnt/c/...`) instead of WSL filesystem (`~/maia`)

**Solution**:
1. Move Maia to WSL filesystem:
   ```bash
   mv /mnt/c/Users/YOUR_USERNAME/maia ~/maia
   ```
2. Update environment variables:
   ```bash
   echo 'export MAIA_ROOT=~/maia' >> ~/.bashrc
   source ~/.bashrc
   ```

---

### Issue: Python dependencies missing

**Solution**:
```bash
cd ~/maia
pip3 install -r requirements_freeze.txt
```

Or install specific package:
```bash
pip3 install anthropic
```

---

### Issue: Git operations fail with permission errors

**Solution**:
```bash
# Reset permissions on Maia directory
cd ~
chmod -R 755 maia

# Verify git config
git config --global --list
```

---

## Getting Help

### Documentation Resources

- **WSL Restore Guide**: `claude/tools/sre/WSL_RESTORE_GUIDE.md` (detailed technical guide)
- **System State**: `SYSTEM_STATE.md` (Phase 135.5 - WSL disaster recovery)
- **Capability Index**: `claude/context/core/capability_index.md`

### Support Channels

1. **Check this guide** - Troubleshooting section above
2. **Ask team lead** - They've been through this process
3. **Review logs** - `~/maia/claude/logs/` (if Maia is running)
4. **WSL documentation** - https://learn.microsoft.com/en-us/windows/wsl/

### Useful Commands

```bash
# Check WSL version
wsl --version

# List WSL distributions
wsl --list --verbose

# Restart WSL
wsl --shutdown
wsl

# Check disk space in WSL
df -h ~

# Check Python environment
python3 --version
pip3 --version
pip3 list

# Check Git config
git config --global --list

# Check environment variables
echo $MAIA_ROOT
echo $PYTHONPATH
```

---

## Quick Reference Card

**Open WSL Terminal**:
```powershell
wsl
```

**Navigate to Maia**:
```bash
cd ~/maia
```

**Open in VSCode**:
```bash
code ~/maia
```

**Update from Git**:
```bash
cd ~/maia
git pull
```

**Check Maia Status**:
```bash
cd ~/maia
python3 claude/tools/sre/maia_health_check.py
```

**Access Windows files**:
```bash
cd /mnt/c/Users/YOUR_USERNAME/
```

**Access WSL files from Windows**:
```
\\wsl$\Ubuntu\home\yourusername\maia
```

---

## Success Checklist

After completing this guide, you should be able to:

- [ ] Open WSL terminal
- [ ] Navigate to `~/maia` directory
- [ ] See Maia code and database files
- [ ] Open Maia in VSCode from WSL
- [ ] Run Python scripts from `~/maia`
- [ ] Use Git commands (status, pull, commit, push)
- [ ] Access environment variables (`$MAIA_ROOT`)
- [ ] Understand where WSL files live vs Windows files

---

## Next Steps

Once Maia is set up, you can:

1. **Explore the codebase**:
   - `claude/agents/` - Agent definitions
   - `claude/tools/` - Tool implementations
   - `claude/context/` - Context management

2. **Try running agents**:
   ```bash
   cd ~/maia
   python3 claude/agents/agent_loader.py
   ```

3. **Review documentation**:
   - Read `CLAUDE.md` for system overview
   - Check `SYSTEM_STATE.md` for recent changes
   - Browse `claude/context/core/` for core concepts

4. **Set up your workflow**:
   - Configure VSCode settings
   - Install preferred extensions
   - Customize shell prompt

5. **Start contributing**:
   - Create feature branches
   - Make changes
   - Commit and push to Git

---

**Welcome to the team! 🎉**

**Document Version**: 1.0
**Last Updated**: 2025-10-21
**Maintained By**: SRE Team
