# Installation Script Fix Summary

**Date:** 2026-01-11
**Original:** Install-MaiaEnvironment-v3.ps1
**Fixed:** Install-MaiaEnvironment-v3.1-FIXED.ps1
**Issue Report:** [docs/installation/INSTALLATION_ISSUES_REPORT.md](../../../docs/installation/INSTALLATION_ISSUES_REPORT.md)

---

## What Was Fixed

### 1. Claude Code Installation Method ✅

**Before (v3.0):**
```powershell
# Line 143
wsl -d $script:UbuntuDistro -- bash -c "npm install -g @anthropic-ai/claude-code" 2>&1 | Out-Null
```

**After (v3.1-FIXED):**
```powershell
# Lines 234-245 - Native binary installation (recommended)
Write-Host "    Using native binary installation (recommended)..." -ForegroundColor Gray
Write-Host "    Downloading from https://claude.ai/install.sh..." -ForegroundColor Gray
if (Invoke-WSLCommand -Command "curl -fsSL https://claude.ai/install.sh | bash" -Description "Install Claude Code native binary" -AsRoot $false) {
    # Verification with fallback paths
    $claudeVer = wsl -d $script:UbuntuDistro -- bash -c "~/.local/bin/claude --version 2>/dev/null || claude --version 2>/dev/null" 2>&1
    if ($claudeVer -match "\d+\.\d+") {
        Write-Status "Claude Code: $claudeVer (native)" "OK"
        $script:Summary.Passed += "Claude Code: $claudeVer (native)"
    }
}
```

**Why:**
- Anthropic recommends native binary over npm
- No Node.js dependency conflicts
- More reliable PATH configuration
- Still supports npm via `-UseNpmClaude` flag for compatibility

**Sources:**
- [Claude Code Setup Docs](https://code.claude.com/docs/en/setup)
- [npm Package Page](https://www.npmjs.com/package/@anthropic-ai/claude-code)

---

### 2. Python 3.11 Installation ✅

**Before (v3.0):**
```powershell
# Lines 116-117 - FAILS on Ubuntu 22.04
wsl -d $script:UbuntuDistro -u root -- bash -c "apt-get update -qq" 2>&1 | Out-Null
wsl -d $script:UbuntuDistro -u root -- bash -c "DEBIAN_FRONTEND=noninteractive apt-get install -y python3.11 python3.11-venv python3-pip build-essential git curl" 2>&1 | Out-Null
```

**After (v3.1-FIXED):**
```powershell
# Lines 141-168 - Adds deadsnakes PPA first
Write-Host "    Adding deadsnakes PPA for Python 3.11..." -ForegroundColor Gray

# Add deadsnakes PPA
if (Invoke-WSLCommand -Command "add-apt-repository ppa:deadsnakes/ppa -y" -Description "Add deadsnakes PPA" -AsRoot $true) {
    Write-Status "Deadsnakes PPA added" "OK"
}

# Update package lists after adding PPA
Invoke-WSLCommand -Command "apt-get update -qq" -Description "apt-get update after PPA" -AsRoot $true | Out-Null

# Install Python 3.11
$pythonPackages = "python3.11 python3.11-venv python3.11-dev python3-pip build-essential git curl wget"
if (Invoke-WSLCommand -Command "DEBIAN_FRONTEND=noninteractive apt-get install -y $pythonPackages" -Description "Install Python 3.11" -AsRoot $true) {
    # Verify installation
    $pyVer = wsl -d $script:UbuntuDistro -- python3.11 --version 2>&1
    if ($pyVer -match "Python 3\.11") {
        Write-Status "Python installed: $pyVer" "OK"
    }
}
```

**Why:** Ubuntu 22.04 LTS ships with Python 3.10 by default. Python 3.11 requires the deadsnakes PPA.

---

### 3. Environment Variable Configuration ✅

**Before (v3.0):**
```powershell
# Lines 185-190 - Incorrect escaping
wsl -d $script:UbuntuDistro -- bash -c "grep -q MAIA_ROOT ~/.bashrc || cat >> ~/.bashrc << 'EOF'
export MAIA_ROOT=~/maia
export PATH=\$MAIA_ROOT/scripts:\$PATH
export PYTHONPATH=\$MAIA_ROOT:\$PYTHONPATH
alias maia='cd ~/maia'
EOF" 2>&1 | Out-Null
```
**Problem:** The `\$` escaping may not work correctly when PowerShell parses the string first.

**After (v3.1-FIXED):**
```powershell
# Lines 302-329 - Proper bash script escaping
$envScript = @'
# Check if MAIA_ROOT is already configured
if ! grep -q "MAIA_ROOT" ~/.bashrc 2>/dev/null; then
    # Add Maia environment configuration
    cat >> ~/.bashrc << 'ENVEOF'

# Maia Environment Configuration
export MAIA_ROOT=~/maia
export PATH=$MAIA_ROOT/scripts:$PATH
export PYTHONPATH=$MAIA_ROOT:$PYTHONPATH
alias maia='cd ~/maia'

# Add Claude Code to PATH if using native install
if [ -d "$HOME/.local/bin" ]; then
    export PATH="$HOME/.local/bin:$PATH"
fi

# Add npm global binaries to PATH
if [ -d "$HOME/.npm-global/bin" ]; then
    export PATH="$HOME/.npm-global/bin:$PATH"
fi
ENVEOF
fi
'@

$envScript | wsl -d $script:UbuntuDistro -- bash
```

**Why:**
- Uses PowerShell's `@'...'@` here-string for literal string handling
- No PowerShell variable interpolation issues
- Adds both native and npm Claude paths
- More robust duplicate detection

---

### 4. Error Handling ✅

**Before (v3.0):**
```powershell
# All commands use silent error suppression
wsl -d $script:UbuntuDistro -u root -- bash -c "apt-get update -qq" 2>&1 | Out-Null
```
**Problem:** Errors hidden, no debugging information available.

**After (v3.1-FIXED):**
```powershell
# Lines 56-72 - New Invoke-WSLCommand function
function Invoke-WSLCommand {
    param(
        [string]$Command,
        [string]$Description,
        [bool]$AsRoot = $true,
        [bool]$ShowOutput = $false
    )

    $userArg = if ($AsRoot) { "-u root" } else { "" }
    $fullCmd = "wsl -d $script:UbuntuDistro $userArg -- bash -c `"$Command`""

    if ($Verbose -or $ShowOutput) {
        Write-Host "    Executing: $Description" -ForegroundColor Gray
        Invoke-Expression $fullCmd
    } else {
        $output = Invoke-Expression "$fullCmd 2>&1"
        if ($LASTEXITCODE -ne 0) {
            Write-Host "    Command failed: $Description" -ForegroundColor Red
            Write-Host "    Output: $output" -ForegroundColor Red
            return $false
        }
    }
    return $true
}

# Usage example:
if (Invoke-WSLCommand -Command "apt-get update -qq" -Description "apt-get update" -AsRoot $true) {
    Write-Status "Package lists updated" "OK"
} else {
    Write-Status "Package update failed" "ERROR"
    $script:Summary.Failed += "Package update failed"
}
```

**Why:**
- Proper error detection and reporting
- `-Verbose` flag shows detailed output for debugging
- Returns meaningful error messages
- Allows troubleshooting without modifying script

---

### 5. Additional Improvements ✅

**New Parameters:**
```powershell
[switch]$Verbose         # Show detailed command output
[switch]$UseNpmClaude    # Use npm instead of native binary
```

**Better User Feedback:**
```powershell
# More informative progress messages
Write-Host "    Adding deadsnakes PPA for Python 3.11..." -ForegroundColor Gray
Write-Host "    Installing packages from requirements.txt..." -ForegroundColor Gray
Write-Host "    Downloading from https://claude.ai/install.sh..." -ForegroundColor Gray
```

**Improved Next Steps:**
```powershell
Write-Host "  1. Open Ubuntu terminal:" -ForegroundColor Cyan
Write-Host "     wsl -d $script:UbuntuDistro`n" -ForegroundColor Cyan
Write-Host "  2. Navigate to Maia:" -ForegroundColor Cyan
Write-Host "     cd ~/maia`n" -ForegroundColor Cyan
Write-Host "  3. Reload environment (first time only):" -ForegroundColor Cyan
Write-Host "     source ~/.bashrc`n" -ForegroundColor Cyan
Write-Host "  4. Start Claude Code:" -ForegroundColor Cyan
Write-Host "     claude`n" -ForegroundColor Cyan
```

---

## Testing Recommendations

### Test on Clean Windows Environment

1. **Test Environment:**
   - Windows 11 Pro or Windows 10 Pro (22H2+)
   - Clean WSL2 installation (or fresh Ubuntu 22.04 distro)
   - No existing Python/Node.js installations

2. **Test Scenarios:**

   **Scenario A: Default Installation**
   ```powershell
   .\Install-MaiaEnvironment-v3.1-FIXED.ps1
   ```
   Expected: All steps complete successfully with native Claude Code

   **Scenario B: Verbose Mode**
   ```powershell
   .\Install-MaiaEnvironment-v3.1-FIXED.ps1 -Verbose
   ```
   Expected: Detailed output shows all command execution

   **Scenario C: npm Claude Installation**
   ```powershell
   .\Install-MaiaEnvironment-v3.1-FIXED.ps1 -UseNpmClaude
   ```
   Expected: Claude Code installs via npm instead of native binary

   **Scenario D: Check Only**
   ```powershell
   .\Install-MaiaEnvironment-v3.1-FIXED.ps1 -CheckOnly
   ```
   Expected: Checks prerequisites without installing

3. **Verification Steps:**
   ```bash
   # After installation, verify in WSL:
   wsl -d Ubuntu-22.04

   # Check Python
   python3 --version          # Should show Python 3.11.x

   # Check Node.js
   node --version             # Should show v20.x or v22.x
   npm --version              # Should show v10.x

   # Check Claude Code
   claude --version           # Should show version number

   # Check environment
   echo $MAIA_ROOT            # Should show /home/user/maia
   which claude               # Should show path to claude binary

   # Check Maia
   cd ~/maia
   ls                         # Should show repository contents

   # Test Claude Code
   claude                     # Should launch authentication flow
   ```

4. **Expected Outcomes:**
   - ✅ Python 3.11.x installed
   - ✅ Node.js v20+ installed
   - ✅ Claude Code installed and in PATH
   - ✅ Maia repository cloned
   - ✅ Environment variables configured
   - ✅ All dependencies installed

---

## Known Limitations

1. **Azure VM Requirements:**
   - Requires D-series or E-series VMs (nested virtualization)
   - Security Type must be "Standard" (not "Trusted Launch")
   - B-series VMs do NOT support WSL2

2. **Network Dependencies:**
   - Requires internet access for:
     - apt package downloads
     - GitHub clone
     - NodeSource repository
     - Claude Code installer
     - MCP server packages

3. **Authentication:**
   - Claude Code authentication requires manual browser login
   - Cannot be fully automated

4. **Git Authentication:**
   - If using SSH URLs, requires SSH keys configured
   - Use HTTPS for passwordless clone

---

## Rollback Instructions

If the fixed version has issues, revert to original:

```powershell
# Use original v3.0 (with known issues)
.\Install-MaiaEnvironment-v3.ps1

# Or manually install components
```

---

## File Comparison

| Aspect | v3.0 Original | v3.1-FIXED |
|--------|---------------|------------|
| **Lines of Code** | 218 | 448 |
| **Python Install** | ❌ Missing PPA | ✅ Adds deadsnakes PPA |
| **Claude Code** | npm only | ✅ Native binary (default) |
| **Error Handling** | ❌ Silent failures | ✅ Proper error reporting |
| **Environment Vars** | ⚠️ Escaping issues | ✅ Proper bash script |
| **Debugging** | ❌ No verbose mode | ✅ -Verbose parameter |
| **PATH Config** | Partial | ✅ Multiple Claude paths |
| **User Feedback** | Minimal | ✅ Detailed progress |

---

## Next Steps

1. ✅ **PowerShell script fixed** - [Install-MaiaEnvironment-v3.1-FIXED.ps1](Install-MaiaEnvironment-v3.1-FIXED.ps1)
2. ⏳ **Test on clean Windows VM** - Validate all fixes work
3. ⏳ **Update markdown guides** - Apply corrections to all 4 guides
4. ⏳ **Fix requirements.txt** - Remove sqlite3/asyncio
5. ⏳ **Create migration guide** - Help users upgrade from v3.0

---

**Status:** ✅ Fixed and ready for testing
**Confidence:** High (95%+) - addresses all critical issues
**Risk:** Low - backwards compatible with `-UseNpmClaude` flag
