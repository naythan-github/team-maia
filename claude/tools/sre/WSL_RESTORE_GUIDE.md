# WSL Restoration Guide

**Purpose**: Restore Maia from macOS backups to Windows laptop running WSL + VSCode
**Version**: 1.0 (Phase 135.5 - Corrected)
**Created**: 2025-10-21

---

## Overview

This guide explains how to restore Maia on a **Windows laptop with WSL (Windows Subsystem for Linux)** from backups created on macOS. The restoration process uses the same `restore_maia.sh` bash script, which automatically detects WSL and adapts accordingly.

**Architecture**:
- **Backup**: Created on macOS (existing disaster_recovery_system.py)
- **Storage**: OneDrive (syncs to Windows)
- **Restore Target**: WSL (Windows Subsystem for Linux)
- **IDE**: VSCode with Remote - WSL extension

---

## Prerequisites

### Windows Setup

1. **Windows 10/11** with WSL 2 installed
   ```powershell
   # Check WSL version
   wsl --list --verbose

   # If not installed, run in PowerShell (Admin):
   wsl --install
   ```

2. **Ubuntu 20.04/22.04** (or preferred Linux distribution)
   ```powershell
   # Install Ubuntu from Microsoft Store or:
   wsl --install -d Ubuntu-22.04
   ```

3. **VSCode** with Remote - WSL extension
   - Install VSCode: https://code.visualstudio.com/
   - Install extension: `ms-vscode-remote.remote-wsl`

4. **OneDrive** synced and accessible from Windows

5. **Python 3.8+** installed in WSL
   ```bash
   # In WSL terminal:
   sudo apt update
   sudo apt install python3 python3-pip
   python3 --version
   ```

---

## Step-by-Step Restoration

### Step 1: Access Windows and Open WSL

1. Open Windows PowerShell or Command Prompt
2. Launch WSL:
   ```powershell
   wsl
   ```
3. You're now in a Linux bash terminal

### Step 2: Locate Backup on OneDrive

OneDrive is mounted in WSL at `/mnt/c/Users/{username}/OneDrive/`:

```bash
# Find your Windows username
ls /mnt/c/Users/

# Navigate to OneDrive backups
cd "/mnt/c/Users/YOUR_USERNAME/OneDrive - YOUR_ORG/MaiaBackups"

# Or Personal OneDrive:
cd "/mnt/c/Users/YOUR_USERNAME/OneDrive/MaiaBackups"

# List available backups
ls -lh
```

You should see backup folders like `full_20251021_182032/`.

### Step 3: Navigate to Backup Folder

```bash
# Change to the backup you want to restore
cd full_20251021_182032

# Verify restore script exists
ls -lh restore_maia.sh
```

### Step 4: Run Restore Script

```bash
# Make script executable (if needed)
chmod +x restore_maia.sh

# Run restoration
./restore_maia.sh
```

### Step 5: Choose Installation Location

The script will detect WSL and offer these options:

```
🔍 Detecting system environment...
  Platform: Windows Subsystem for Linux (WSL)
  Windows User: YourUsername
  OneDrive: /mnt/c/Users/YourUsername/OneDrive - YOUR_ORG

📁 Where should Maia be installed?
  1. ~/maia (WSL home directory - recommended for VSCode)
  2. /mnt/c/Users/YourUsername/maia (Windows filesystem)
  3. Custom location

Choice [1]:
```

**Recommendation**: Choose **Option 1** (`~/maia`) for best VSCode + WSL performance.

**Why**:
- Faster file I/O (native Linux filesystem)
- Better Git performance
- VSCode Remote - WSL works seamlessly
- Avoid Windows/Linux filesystem permissions issues

### Step 6: Restoration Process

The script will:

1. ✅ Extract code (`maia_code.tar.gz` → `~/maia`)
2. ✅ Extract databases (`maia_data_small.tar.gz`)
3. ⏭️ Skip LaunchAgents (WSL uses cron instead)
4. ⏭️ Skip shell configs (WSL uses bash, not zsh)
5. ⏭️ Skip Homebrew (WSL uses apt)
6. ✅ Update config paths (hooks.json, settings.local.json)
7. ✅ Install Python dependencies (pip3)
8. ✅ Restore credentials vault (if password provided)

### Step 7: Set Environment Variables

```bash
# Add to ~/.bashrc
echo 'export MAIA_ROOT=~/maia' >> ~/.bashrc
echo 'export PYTHONPATH=~/maia' >> ~/.bashrc

# Reload bashrc
source ~/.bashrc

# Verify
echo $MAIA_ROOT
```

### Step 8: Open in VSCode

```bash
# From WSL terminal:
code ~/maia
```

This will:
- Launch VSCode on Windows
- Connect to WSL backend
- Open the Maia folder in WSL context
- Install/enable WSL extensions automatically

---

## VSCode + WSL Integration

### Opening Maia in VSCode

**From WSL Terminal**:
```bash
cd ~/maia
code .
```

**From Windows VSCode**:
1. Open VSCode
2. Press `F1` → "WSL: Open Folder in WSL"
3. Navigate to `/home/YOUR_USERNAME/maia`

### VSCode WSL Features

- **Terminal**: Automatically uses WSL bash
- **Extensions**: Install in WSL context (shows "WSL: Ubuntu")
- **Git**: Works natively from WSL filesystem
- **Python**: Uses WSL Python interpreter
- **File Watching**: Fast (native Linux filesystem)

### Recommended VSCode Extensions (WSL)

Install these in WSL context:
- `ms-python.python` - Python language support
- `ms-toolsai.jupyter` - Jupyter notebook support
- `eamodio.gitlens` - Git integration
- `ms-vscode.sublime-keybindings` (if preferred)

---

## Platform Differences: macOS vs WSL

### What's Included (Cross-Platform)

✅ **Code** (Python files, agents, tools, context)
✅ **Databases** (SQLite files in `claude/data/`)
✅ **Configuration** (JSON files, markdown docs)
✅ **Python Dependencies** (requirements.txt)
✅ **Credentials Vault** (encrypted credentials)
✅ **Git Repository** (full git history)

### What's Excluded on WSL

❌ **LaunchAgents** (.plist files) - macOS automation
  - **WSL Alternative**: Use `cron` for scheduled backups

❌ **Homebrew Packages** - macOS package manager
  - **WSL Alternative**: Use `apt` (e.g., `sudo apt install jq`)

❌ **Shell Configs** (.zshrc, .bash_profile) - macOS-specific
  - **WSL Alternative**: Use `~/.bashrc`

### WSL-Specific Setup

After restoration, you may need:

1. **Install System Packages** (apt equivalent of Homebrew):
   ```bash
   sudo apt update
   sudo apt install git curl wget jq
   ```

2. **Configure Git** (if not using global config):
   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "your.email@example.com"
   ```

3. **Set Up Cron** (for automated backups):
   ```bash
   crontab -e
   # Add this line:
   0 3 * * * cd ~/maia && python3 claude/tools/sre/disaster_recovery_system.py backup
   ```

---

## Automated Backups on WSL

### Using Cron

```bash
# Edit crontab
crontab -e

# Add daily 3 AM backup (matching macOS schedule)
0 3 * * * cd ~/maia && python3 claude/tools/sre/disaster_recovery_system.py backup

# Verify cron job
crontab -l
```

### Cron Syntax

```
0 3 * * *  = Daily at 3:00 AM
│ │ │ │ │
│ │ │ │ └─── Day of week (0-7, Sunday=0 or 7)
│ │ │ └───── Month (1-12)
│ │ └─────── Day of month (1-31)
│ └───────── Hour (0-23)
└─────────── Minute (0-59)
```

### Verify Cron Execution

```bash
# Check cron is running
sudo service cron status

# View cron logs
grep CRON /var/log/syslog | tail -20
```

---

## Troubleshooting

### Issue 1: WSL Not Detecting Backups

**Symptom**:
```
⚠️  OneDrive not found on Windows filesystem.
Expected: /mnt/c/Users/USERNAME/OneDrive
```

**Solution**:
```bash
# Check OneDrive path manually
ls /mnt/c/Users/
ls "/mnt/c/Users/YOUR_USERNAME/"

# Look for OneDrive folders
ls "/mnt/c/Users/YOUR_USERNAME/" | grep -i onedrive

# Provide path manually when prompted
```

---

### Issue 2: Python Not Found

**Symptom**:
```
bash: python3: command not found
```

**Solution**:
```bash
# Install Python 3
sudo apt update
sudo apt install python3 python3-pip

# Verify
python3 --version
pip3 --version
```

---

### Issue 3: pip install Fails

**Symptom**:
```
ERROR: Could not install packages due to an EnvironmentError
```

**Solution**:
```bash
# Install pip properly
sudo apt install python3-pip python3-venv

# Use virtual environment (recommended)
cd ~/maia
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_freeze.txt
```

---

### Issue 4: VSCode Can't Open Folder

**Symptom**:
```
Could not resolve path: /home/username/maia
```

**Solution**:
1. Ensure WSL is running: `wsl --list --running`
2. Install VSCode WSL extension: `ms-vscode-remote.remote-wsl`
3. Open from WSL terminal: `cd ~/maia && code .`
4. Restart VSCode

---

### Issue 5: Slow File I/O Performance

**Symptom**:
- Git commands slow
- File saves lag
- VSCode sluggish

**Solution**:
- **Ensure Maia is on WSL filesystem** (`~/maia`), NOT Windows filesystem (`/mnt/c/Users/...`)
- Windows ↔ WSL cross-filesystem access is slow
- Move to WSL: `mv /mnt/c/Users/.../maia ~/maia`

---

### Issue 6: OneDrive Sync Not Working from WSL

**Symptom**:
- Backups created in WSL don't appear in OneDrive on Windows

**Note**: This is expected. OneDrive Windows client only syncs Windows filesystem.

**Solution**:
```bash
# Option 1: Backup to OneDrive path (Windows filesystem)
export MAIA_ONEDRIVE_PATH="/mnt/c/Users/YOUR_USERNAME/OneDrive - YOUR_ORG"
python3 claude/tools/sre/disaster_recovery_system.py backup

# Option 2: Create backup in WSL, manually copy to OneDrive
python3 claude/tools/sre/disaster_recovery_system.py backup
# Then copy from ~/maia/backups to /mnt/c/Users/.../OneDrive/MaiaBackups/
```

---

## Testing Checklist

After restoration, verify:

- [ ] Maia directory exists (`ls ~/maia`)
- [ ] Code files present (`ls ~/maia/claude/agents/`)
- [ ] Databases present (`ls ~/maia/claude/data/*.db`)
- [ ] Python works (`python3 --version`)
- [ ] Dependencies installed (`pip3 list | grep anthropic`)
- [ ] Environment variables set (`echo $MAIA_ROOT`)
- [ ] VSCode opens folder (`code ~/maia`)
- [ ] Git works (`cd ~/maia && git status`)
- [ ] Credentials vault exists (`ls ~/maia/credentials.vault.enc`)

---

## Backup Creation from WSL

Once restored, you can create backups from WSL:

```bash
cd ~/maia

# Create backup (stored on Windows OneDrive filesystem)
python3 claude/tools/sre/disaster_recovery_system.py backup

# Backup will be created at:
# /mnt/c/Users/YOUR_USERNAME/OneDrive - YOUR_ORG/MaiaBackups/full_YYYYMMDD_HHMMSS/
```

**Important**: Backup target must be Windows OneDrive path (`/mnt/c/...`) for OneDrive sync to work.

---

## Command Reference

### WSL Basics

```bash
# Start WSL
wsl

# List WSL distributions
wsl --list

# Shutdown WSL
wsl --shutdown

# Access Windows files from WSL
cd /mnt/c/Users/YOUR_USERNAME

# Access WSL files from Windows
# Windows path: \\wsl$\Ubuntu-22.04\home\username\maia
```

### Restoration

```bash
# Navigate to backup
cd "/mnt/c/Users/YOUR_USERNAME/OneDrive - YOUR_ORG/MaiaBackups/full_20251021_182032"

# Run restore
./restore_maia.sh

# Open in VSCode
code ~/maia
```

### Post-Restore Setup

```bash
# Set environment variables
echo 'export MAIA_ROOT=~/maia' >> ~/.bashrc
echo 'export PYTHONPATH=~/maia' >> ~/.bashrc
source ~/.bashrc

# Set up cron backup
crontab -e
# Add: 0 3 * * * cd ~/maia && python3 claude/tools/sre/disaster_recovery_system.py backup

# Verify setup
echo $MAIA_ROOT
python3 --version
pip3 list
```

---

## Comparison: macOS vs WSL

| Feature | macOS | WSL |
|---------|-------|-----|
| **Backup Creation** | disaster_recovery_system.py | disaster_recovery_system.py (same) |
| **Backup Format** | tar.gz | tar.gz (same) |
| **Restoration Script** | restore_maia.sh | restore_maia.sh (auto-detects WSL) |
| **OneDrive Path** | ~/Library/CloudStorage/OneDrive-YOUR_ORG | /mnt/c/Users/{user}/OneDrive - YOUR_ORG |
| **Automation** | LaunchAgents | cron |
| **Shell** | zsh / bash | bash |
| **Package Manager** | Homebrew (brew) | APT (apt) |
| **IDE** | Native VSCode | VSCode Remote - WSL |
| **Python Location** | /usr/local/bin/python3 | /usr/bin/python3 |
| **Maia Installation** | ~/git/maia | ~/maia (recommended) |

---

## Next Steps

1. **Verify Restoration**: Run through testing checklist above
2. **Configure VSCode**: Install extensions, configure Python interpreter
3. **Set Up Cron**: Automate daily backups (optional)
4. **Test Backup**: Create a test backup from WSL
5. **Update Documentation**: Document any WSL-specific learnings

---

## Support

### Resources

- **WSL Documentation**: https://docs.microsoft.com/en-us/windows/wsl/
- **VSCode Remote - WSL**: https://code.visualstudio.com/docs/remote/wsl
- **Disaster Recovery System**: `claude/tools/sre/disaster_recovery_system.py`
- **Capability Index**: `claude/context/core/capability_index.md` (Phase 135.5)

### Getting Help

1. Check this guide's Troubleshooting section
2. Review backup logs (if created from WSL)
3. Verify WSL is running (`wsl --list --running`)
4. Check OneDrive sync status (Windows OneDrive app)
5. Consult SRE Principal Engineer Agent for advanced issues

---

**Document Version**: 1.0 (Corrected - WSL target, not native Windows)
**Last Updated**: 2025-10-21
**Status**: ✅ Complete (pending WSL testing)
