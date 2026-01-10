# Maia Quick Start Guide (v3.0)

**5-Minute Setup** | Windows with WSL

---

## Prerequisites (One-Time, ~10 minutes)

### 1. Install WSL + Ubuntu

**PowerShell as Admin:**
```powershell
wsl --install -d Ubuntu
```

**After restart, create user:**
- Username: `maia`
- Password: `Test123456!`

### 2. Install VSCode (Optional)

Download: https://code.visualstudio.com/download

---

## Install Maia (~5 minutes)

### 1. Check Prerequisites

**PowerShell as Admin:**
```powershell
.\Install-MaiaEnvironment-v3.ps1 -CheckOnly
```

**Expected:**
```
[OK] WSL is installed
[OK] Ubuntu distro: Ubuntu
[OK] VSCode installed
```

### 2. Run Installation

```powershell
.\Install-MaiaEnvironment-v3.ps1
```

**Wait 5-10 minutes** while it installs:
- Python 3.11
- Node.js
- Claude Code CLI
- Maia repository
- Dependencies

### 3. Verify

```powershell
wsl -d Ubuntu
cd ~/maia
python3 --version  # Should show: Python 3.11.x
claude --version   # Should show: 2.x.x
```

---

## Start Using Maia

### Command Line
```bash
wsl -d Ubuntu
cd ~/maia
claude
```

### VSCode (Recommended)
```powershell
code --remote wsl+Ubuntu ~/maia
```

Then in VSCode terminal:
```bash
claude
```

---

## Common Issues

**"wsl: command not found"**
```powershell
wsl --install
# Restart computer
```

**"No Ubuntu distro"**
```powershell
wsl --install -d Ubuntu
```

**"Git clone failed"**
```powershell
.\Install-MaiaEnvironment-v3.ps1 -MaiaRepo "https://github.com/naythan-orro/maia.git"
```

---

## Full Documentation

See: `INSTALLATION_GUIDE.md` for detailed instructions and troubleshooting.

---

**Support:** https://github.com/naythan-orro/maia/issues
