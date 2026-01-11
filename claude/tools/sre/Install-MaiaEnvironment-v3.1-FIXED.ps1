#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Maia environment setup for WSL - FIXED VERSION with all corrections.

.DESCRIPTION
    Simplified installer that sets up Maia development environment inside WSL.

    PREREQUISITES (install first):
    - WSL with Ubuntu (Windows Store or 'wsl --install')
    - VSCode (https://code.visualstudio.com)

    WHAT THIS SCRIPT DOES:
    - Installs Python 3.11+ in WSL (with deadsnakes PPA)
    - Installs Node.js LTS in WSL (for MCP servers)
    - Clones Maia repository
    - Installs Claude Code CLI (native binary - recommended)
    - Installs MCP servers
    - Configures environment

.PARAMETER MaiaRepo
    GitHub repository URL. Default: https://github.com/naythan-orro/maia.git

.PARAMETER SkipMCPServers
    Skip MCP server installation.

.PARAMETER CheckOnly
    Only check prerequisites.

.PARAMETER Verbose
    Show detailed output from installation commands.

.PARAMETER UseNpmClaude
    Use npm installation for Claude Code instead of native binary (not recommended).

.EXAMPLE
    .\Install-MaiaEnvironment-v3.1-FIXED.ps1

.EXAMPLE
    .\Install-MaiaEnvironment-v3.1-FIXED.ps1 -Verbose

.NOTES
    Version: 3.1-FIXED
    Changes v3.1:
    - Fixed Python 3.11 installation (added deadsnakes PPA)
    - Changed Claude Code to native binary installation (recommended)
    - Fixed environment variable escaping in .bashrc
    - Improved error handling with detailed output
    - Added -Verbose parameter for debugging
#>

[CmdletBinding()]
param(
    [string]$MaiaRepo = "https://github.com/naythan-orro/maia.git",
    [switch]$SkipMCPServers,
    [switch]$CheckOnly,
    [switch]$UseNpmClaude
)

function Write-Banner { param([string]$Text)
    Write-Host "`n============================================================" -ForegroundColor Cyan
    Write-Host $Text -ForegroundColor Cyan
    Write-Host "============================================================`n" -ForegroundColor Cyan
}

function Write-Step { param([int]$Number, [string]$Description)
    Write-Host "`n[$Number] $Description" -ForegroundColor Yellow
}

function Write-Status { param([string]$Message, [string]$Status)
    $color = @{"OK"="Green";"WARN"="Yellow";"ERROR"="Red"}[$Status]
    $symbol = @{"OK"="[OK]  ";"WARN"="[WARN]";"ERROR"="[FAIL]"}[$Status]
    Write-Host "$symbol $Message" -ForegroundColor $color
}

function Invoke-WSLCommand {
    param(
        [string]$Command,
        [string]$Description,
        [bool]$AsRoot = $true,
        [bool]$ShowOutput = $false
    )

    $userArg = if ($AsRoot) { "-u root" } else { "" }
    $fullCmd = "wsl -d $script:UbuntuDistro $userArg -- bash -c `"$Command`""

    # Check if running in Verbose mode (built-in CmdletBinding parameter)
    $isVerbose = ($VerbosePreference -eq 'Continue')

    if ($isVerbose -or $ShowOutput) {
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

$script:Summary = @{Passed=@();Warnings=@();Failed=@()}

Write-Banner "MAIA Environment Installer v3.1-FIXED"
Write-Host "MODE: $(if($CheckOnly){'Check Only'}else{'Full Installation'})" -ForegroundColor $(if($CheckOnly){'Yellow'}else{'Green'})
if ($VerbosePreference -eq 'Continue') { Write-Host "VERBOSE: Enabled" -ForegroundColor Yellow }

# Step 1: Prerequisites
Write-Step 1 "Checking Prerequisites"

# WSL check
$wslCmd = Get-Command wsl.exe -ErrorAction SilentlyContinue
if ($wslCmd) {
    Write-Status "WSL is installed" "OK"
    $script:Summary.Passed += "WSL is installed"

    $distros = wsl --list --quiet 2>&1 | Out-String
    if ($distros -match "Ubuntu") {
        $distroLines = $distros -split "`n" | Where-Object { $_ -match "Ubuntu" }
        $script:UbuntuDistro = ($distroLines[0] -replace "\0", "").Trim()
        Write-Status "Ubuntu distro: $script:UbuntuDistro" "OK"
        $script:Summary.Passed += "Ubuntu: $script:UbuntuDistro"
    } else {
        Write-Status "No Ubuntu distro found" "ERROR"
        Write-Host "`n    Install from: https://apps.microsoft.com/detail/9pdxgncfsczv" -ForegroundColor Cyan
        Write-Host "    Or run: wsl --install -d Ubuntu`n" -ForegroundColor Cyan
        $script:Summary.Failed += "No Ubuntu distro"
        if (-not $CheckOnly) { exit 1 }
    }
} else {
    Write-Status "WSL not installed" "ERROR"
    Write-Host "`n    Run: wsl --install" -ForegroundColor Cyan
    Write-Host "    Or install from: https://apps.microsoft.com/detail/9pdxgncfsczv`n" -ForegroundColor Cyan
    $script:Summary.Failed += "WSL not installed"
    if (-not $CheckOnly) { exit 1 }
}

# VSCode check
if (Get-Command code -ErrorAction SilentlyContinue) {
    Write-Status "VSCode installed" "OK"
    $script:Summary.Passed += "VSCode installed"
} else {
    Write-Status "VSCode not installed (optional)" "WARN"
    Write-Host "    Download from: https://code.visualstudio.com/download`n" -ForegroundColor Cyan
    $script:Summary.Warnings += "VSCode not installed"
}

if ($CheckOnly) {
    Write-Banner "Check Summary"
    if ($script:Summary.Passed) { Write-Host "PASSED:" -ForegroundColor Green; $script:Summary.Passed | % { Write-Host "  + $_" -ForegroundColor Green } }
    if ($script:Summary.Warnings) { Write-Host "`nWARNINGS:" -ForegroundColor Yellow; $script:Summary.Warnings | % { Write-Host "  ! $_" -ForegroundColor Yellow } }
    if ($script:Summary.Failed) { Write-Host "`nFAILED:" -ForegroundColor Red; $script:Summary.Failed | % { Write-Host "  x $_" -ForegroundColor Red } }
    exit 0
}

# Step 2: Update package lists
Write-Step 2 "Updating Ubuntu Package Lists"
if (Invoke-WSLCommand -Command "apt-get update -qq" -Description "apt-get update" -AsRoot $true) {
    Write-Status "Package lists updated" "OK"
    $script:Summary.Passed += "Package lists updated"
} else {
    Write-Status "Package update failed" "ERROR"
    $script:Summary.Failed += "Package update failed"
}

# Step 3: Python 3.11 with deadsnakes PPA
Write-Step 3 "Installing Python 3.11 in WSL"
Write-Host "    Adding deadsnakes PPA for Python 3.11..." -ForegroundColor Gray

# Add deadsnakes PPA
if (Invoke-WSLCommand -Command "add-apt-repository ppa:deadsnakes/ppa -y" -Description "Add deadsnakes PPA" -AsRoot $true) {
    Write-Status "Deadsnakes PPA added" "OK"
} else {
    Write-Status "PPA addition failed" "WARN"
    $script:Summary.Warnings += "Deadsnakes PPA failed (continuing anyway)"
}

# Update package lists again after adding PPA
Invoke-WSLCommand -Command "apt-get update -qq" -Description "apt-get update after PPA" -AsRoot $true | Out-Null

# Install Python 3.11 and tools
Write-Host "    Installing Python 3.11 and build tools..." -ForegroundColor Gray
$pythonPackages = "python3.11 python3.11-venv python3.11-dev python3-pip build-essential git curl wget"
if (Invoke-WSLCommand -Command "DEBIAN_FRONTEND=noninteractive apt-get install -y $pythonPackages" -Description "Install Python 3.11" -AsRoot $true) {
    $pyVer = wsl -d $script:UbuntuDistro -- python3.11 --version 2>&1
    if ($pyVer -match "Python 3\.11") {
        Write-Status "Python installed: $pyVer" "OK"
        $script:Summary.Passed += "Python: $pyVer"

        # Set Python 3.11 as default python3
        Invoke-WSLCommand -Command "update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1" -Description "Set Python 3.11 as default" -AsRoot $true | Out-Null
    } else {
        Write-Status "Python verification failed" "ERROR"
        $script:Summary.Failed += "Python verification failed"
    }
} else {
    Write-Status "Python install failed" "ERROR"
    $script:Summary.Failed += "Python install failed"
}

# Step 4: Node.js (for MCP servers)
Write-Step 4 "Installing Node.js LTS in WSL"
Write-Host "    Downloading NodeSource setup script..." -ForegroundColor Gray
if (Invoke-WSLCommand -Command "curl -fsSL https://deb.nodesource.com/setup_lts.x | bash -" -Description "Setup NodeSource repository" -AsRoot $true) {
    Write-Host "    Installing Node.js..." -ForegroundColor Gray
    if (Invoke-WSLCommand -Command "DEBIAN_FRONTEND=noninteractive apt-get install -y nodejs" -Description "Install Node.js" -AsRoot $true) {
        $nodeVer = wsl -d $script:UbuntuDistro -- node --version 2>&1
        $npmVer = wsl -d $script:UbuntuDistro -- npm --version 2>&1
        if ($nodeVer -match "v\d+\.") {
            Write-Status "Node.js installed: $nodeVer" "OK"
            Write-Status "npm installed: $npmVer" "OK"
            $script:Summary.Passed += "Node.js: $nodeVer"
        } else {
            Write-Status "Node.js verification failed" "ERROR"
            $script:Summary.Failed += "Node.js verification failed"
        }
    } else {
        Write-Status "Node.js install failed" "ERROR"
        $script:Summary.Failed += "Node.js install failed"
    }
} else {
    Write-Status "NodeSource setup failed" "ERROR"
    $script:Summary.Failed += "NodeSource setup failed"
}

# Step 5: Claude Code CLI
Write-Step 5 "Installing Claude Code CLI"

if ($UseNpmClaude) {
    Write-Host "    Using npm installation (not recommended)..." -ForegroundColor Yellow
    if (Invoke-WSLCommand -Command "npm install -g @anthropic-ai/claude-code" -Description "Install Claude Code via npm" -AsRoot $false) {
        $claudeVer = wsl -d $script:UbuntuDistro -- claude --version 2>&1
        if ($claudeVer -match "\d+\.\d+") {
            Write-Status "Claude Code: $claudeVer (npm)" "OK"
            $script:Summary.Passed += "Claude Code: $claudeVer (npm)"
        } else {
            Write-Status "Claude Code verification failed" "WARN"
            $script:Summary.Warnings += "Claude Code install issues"
        }
    } else {
        Write-Status "Claude Code npm install failed" "ERROR"
        $script:Summary.Failed += "Claude Code npm install failed"
    }
} else {
    Write-Host "    Using native binary installation (recommended)..." -ForegroundColor Gray
    Write-Host "    Downloading from https://claude.ai/install.sh..." -ForegroundColor Gray
    if (Invoke-WSLCommand -Command "curl -fsSL https://claude.ai/install.sh | bash" -Description "Install Claude Code native binary" -AsRoot $false) {
        # Wait a moment for installation to complete
        Start-Sleep -Seconds 2
        $claudeVer = wsl -d $script:UbuntuDistro -- bash -c "~/.local/bin/claude --version 2>/dev/null || claude --version 2>/dev/null" 2>&1
        if ($claudeVer -match "\d+\.\d+") {
            Write-Status "Claude Code: $claudeVer (native)" "OK"
            $script:Summary.Passed += "Claude Code: $claudeVer (native)"
        } else {
            Write-Status "Claude Code verification failed (may need manual PATH update)" "WARN"
            $script:Summary.Warnings += "Claude Code may need PATH update"
        }
    } else {
        Write-Status "Claude Code native install failed" "ERROR"
        $script:Summary.Failed += "Claude Code native install failed"
    }
}

# Step 6: Clone Maia
Write-Step 6 "Cloning Maia Repository"
Write-Host "    Repo: $MaiaRepo" -ForegroundColor Gray
$maiaCheck = wsl -d $script:UbuntuDistro -- test -d ~/maia
if ($LASTEXITCODE -eq 0) {
    Write-Status "Maia directory exists (skipped)" "WARN"
    $script:Summary.Warnings += "Maia already exists"
} else {
    Write-Host "    Cloning from GitHub..." -ForegroundColor Gray
    if ($VerbosePreference -eq 'Continue') {
        wsl -d $script:UbuntuDistro -- git clone $MaiaRepo ~/maia
    } else {
        $output = wsl -d $script:UbuntuDistro -- git clone $MaiaRepo ~/maia 2>&1
    }

    if ($LASTEXITCODE -eq 0) {
        Write-Status "Maia cloned successfully" "OK"
        $script:Summary.Passed += "Maia cloned"
    } else {
        Write-Status "Git clone failed" "ERROR"
        Write-Host "    Try using HTTPS URL or check SSH keys" -ForegroundColor Red
        $script:Summary.Failed += "Git clone failed"
    }
}

# Step 7: Python dependencies
Write-Step 7 "Installing Python Dependencies"
$maiaCheck = wsl -d $script:UbuntuDistro -- test -f ~/maia/requirements.txt
if ($LASTEXITCODE -eq 0) {
    Write-Host "    Installing packages from requirements.txt..." -ForegroundColor Gray
    if (Invoke-WSLCommand -Command "cd ~/maia && python3 -m pip install --user -q -r requirements.txt" -Description "Install Python dependencies" -AsRoot $false) {
        Write-Status "Python dependencies installed" "OK"
        $script:Summary.Passed += "Python dependencies"
    } else {
        Write-Status "Python dependencies failed (check requirements.txt)" "WARN"
        $script:Summary.Warnings += "Some Python packages may have failed"
    }
} else {
    Write-Status "Maia directory or requirements.txt not found" "WARN"
    $script:Summary.Warnings += "No Maia directory"
}

# Step 8: Environment configuration
Write-Step 8 "Configuring Environment"
Write-Host "    Adding environment variables to ~/.bashrc..." -ForegroundColor Gray

# Use a more reliable method to add environment variables
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
Write-Status "Environment configured" "OK"
$script:Summary.Passed += "Environment configured"

# Step 9: MCP Servers
if (-not $SkipMCPServers) {
    Write-Step 9 "Installing MCP Servers"
    Write-Host "    Installing @modelcontextprotocol packages..." -ForegroundColor Gray
    if (Invoke-WSLCommand -Command "npm install -g @modelcontextprotocol/server-filesystem @modelcontextprotocol/server-github" -Description "Install MCP servers" -AsRoot $false) {
        Write-Status "MCP servers installed" "OK"
        $script:Summary.Passed += "MCP servers"
    } else {
        Write-Status "MCP servers install failed" "WARN"
        $script:Summary.Warnings += "MCP servers may have issues"
    }
}

# Summary
Write-Banner "Installation Summary"
if ($script:Summary.Passed) {
    Write-Host "PASSED ($($script:Summary.Passed.Count)):" -ForegroundColor Green
    $script:Summary.Passed | % { Write-Host "  + $_" -ForegroundColor Green }
}
if ($script:Summary.Warnings) {
    Write-Host "`nWARNINGS ($($script:Summary.Warnings.Count)):" -ForegroundColor Yellow
    $script:Summary.Warnings | % { Write-Host "  ! $_" -ForegroundColor Yellow }
}
if ($script:Summary.Failed) {
    Write-Host "`nFAILED ($($script:Summary.Failed.Count)):" -ForegroundColor Red
    $script:Summary.Failed | % { Write-Host "  x $_" -ForegroundColor Red }
}

# Next steps
Write-Banner "Next Steps"
if ($script:Summary.Failed.Count -eq 0) {
    Write-Host "Installation complete! To start:`n" -ForegroundColor Green
    Write-Host "  1. Open Ubuntu terminal:" -ForegroundColor Cyan
    Write-Host "     wsl -d $script:UbuntuDistro`n" -ForegroundColor Cyan
    Write-Host "  2. Navigate to Maia:" -ForegroundColor Cyan
    Write-Host "     cd ~/maia`n" -ForegroundColor Cyan
    Write-Host "  3. Reload environment (first time only):" -ForegroundColor Cyan
    Write-Host "     source ~/.bashrc`n" -ForegroundColor Cyan
    Write-Host "  4. Start Claude Code:" -ForegroundColor Cyan
    Write-Host "     claude`n" -ForegroundColor Cyan
    Write-Host "  5. Authenticate when prompted" -ForegroundColor Cyan
} else {
    Write-Host "Installation incomplete. Fix errors above and re-run script." -ForegroundColor Yellow
    Write-Host "Tip: Run with -Verbose flag for detailed output:" -ForegroundColor Yellow
    Write-Host "  .\Install-MaiaEnvironment-v3.1-FIXED.ps1 -Verbose`n" -ForegroundColor Cyan
}
