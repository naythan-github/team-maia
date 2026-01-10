#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Maia environment setup for WSL - focuses on what matters.

.DESCRIPTION
    Simplified installer that sets up Maia development environment inside WSL.

    PREREQUISITES (install first):
    - WSL with Ubuntu (Windows Store or 'wsl --install')
    - VSCode (https://code.visualstudio.com)

    WHAT THIS SCRIPT DOES:
    - Installs Python 3.11+ in WSL
    - Installs Node.js LTS in WSL
    - Clones Maia repository
    - Installs Claude Code CLI
    - Installs MCP servers
    - Configures environment

.PARAMETER MaiaRepo
    GitHub repository URL. Default: https://github.com/naythan-orro/maia.git

.PARAMETER SkipMCPServers
    Skip MCP server installation.

.PARAMETER CheckOnly
    Only check prerequisites.

.EXAMPLE
    .\Install-MaiaEnvironment.ps1

.NOTES
    Version: 3.0
    Changed v3.0: MAJOR SIMPLIFICATION - removed OS component installation
#>

[CmdletBinding()]
param(
    [string]$MaiaRepo = "https://github.com/naythan-orro/maia.git",
    [switch]$SkipMCPServers,
    [switch]$CheckOnly
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

$script:Summary = @{Passed=@();Warnings=@();Failed=@()}

Write-Banner "MAIA Environment Installer v3.0"
Write-Host "MODE: $(if($CheckOnly){'Check Only'}else{'Full Installation'})" -ForegroundColor $(if($CheckOnly){'Yellow'}else{'Green'})

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

# Step 2: Python
Write-Step 2 "Installing Python 3.11 in WSL"
wsl -d $script:UbuntuDistro -u root -- bash -c "apt-get update -qq" 2>&1 | Out-Null
wsl -d $script:UbuntuDistro -u root -- bash -c "DEBIAN_FRONTEND=noninteractive apt-get install -y python3.11 python3.11-venv python3-pip build-essential git curl" 2>&1 | Out-Null
$pyVer = wsl -d $script:UbuntuDistro -- python3.11 --version 2>&1
if ($pyVer -match "Python 3\.11") {
    Write-Status "Python installed: $pyVer" "OK"
    $script:Summary.Passed += "Python: $pyVer"
    wsl -d $script:UbuntuDistro -u root -- update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 2>&1 | Out-Null
} else {
    Write-Status "Python install failed" "ERROR"
    $script:Summary.Failed += "Python install failed"
}

# Step 3: Node.js
Write-Step 3 "Installing Node.js LTS in WSL"
wsl -d $script:UbuntuDistro -u root -- bash -c "curl -fsSL https://deb.nodesource.com/setup_lts.x | bash -" 2>&1 | Out-Null
wsl -d $script:UbuntuDistro -u root -- bash -c "DEBIAN_FRONTEND=noninteractive apt-get install -y nodejs" 2>&1 | Out-Null
$nodeVer = wsl -d $script:UbuntuDistro -- node --version 2>&1
if ($nodeVer -match "v\d+\.") {
    Write-Status "Node.js installed: $nodeVer" "OK"
    $script:Summary.Passed += "Node.js: $nodeVer"
} else {
    Write-Status "Node.js install failed" "ERROR"
    $script:Summary.Failed += "Node.js install failed"
}

# Step 4: Claude Code
Write-Step 4 "Installing Claude Code CLI"
wsl -d $script:UbuntuDistro -- bash -c "npm install -g @anthropic-ai/claude-code" 2>&1 | Out-Null
$claudeVer = wsl -d $script:UbuntuDistro -- claude --version 2>&1
if ($claudeVer -match "\d+\.\d+") {
    Write-Status "Claude Code: $claudeVer" "OK"
    $script:Summary.Passed += "Claude Code: $claudeVer"
} else {
    Write-Status "Claude Code install issues" "WARN"
    $script:Summary.Warnings += "Claude Code install issues"
}

# Step 5: Clone Maia
Write-Step 5 "Cloning Maia Repository"
Write-Host "    Repo: $MaiaRepo" -ForegroundColor Gray
$maiaCheck = wsl -d $script:UbuntuDistro -- test -d ~/maia
if ($LASTEXITCODE -eq 0) {
    Write-Status "Maia directory exists (skipped)" "WARN"
    $script:Summary.Warnings += "Maia already exists"
} else {
    wsl -d $script:UbuntuDistro -- git clone $MaiaRepo ~/maia 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Status "Maia cloned successfully" "OK"
        $script:Summary.Passed += "Maia cloned"
    } else {
        Write-Status "Git clone failed" "ERROR"
        $script:Summary.Failed += "Git clone failed"
    }
}

# Step 6: Python deps
Write-Step 6 "Installing Python Dependencies"
$maiaCheck = wsl -d $script:UbuntuDistro -- test -f ~/maia/requirements.txt
if ($LASTEXITCODE -eq 0) {
    wsl -d $script:UbuntuDistro -- bash -c "cd ~/maia && python3 -m pip install --user -q -r requirements.txt" 2>&1 | Out-Null
    Write-Status "Python dependencies installed" "OK"
    $script:Summary.Passed += "Python dependencies"
} else {
    Write-Status "Maia directory not found" "WARN"
    $script:Summary.Warnings += "No Maia directory"
}

# Step 7: Environment
Write-Step 7 "Configuring Environment"
wsl -d $script:UbuntuDistro -- bash -c "grep -q MAIA_ROOT ~/.bashrc || cat >> ~/.bashrc << 'EOF'
export MAIA_ROOT=~/maia
export PATH=\$MAIA_ROOT/scripts:\$PATH
export PYTHONPATH=\$MAIA_ROOT:\$PYTHONPATH
alias maia='cd ~/maia'
EOF" 2>&1 | Out-Null
Write-Status "Environment configured" "OK"
$script:Summary.Passed += "Environment configured"

# Step 8: MCP Servers
if (-not $SkipMCPServers) {
    Write-Step 8 "Installing MCP Servers"
    wsl -d $script:UbuntuDistro -- npm install -g @modelcontextprotocol/server-filesystem @modelcontextprotocol/server-github 2>&1 | Out-Null
    Write-Status "MCP servers installed" "OK"
    $script:Summary.Passed += "MCP servers"
}

# Summary
Write-Banner "Installation Summary"
if ($script:Summary.Passed) { Write-Host "PASSED ($($script:Summary.Passed.Count)):" -ForegroundColor Green; $script:Summary.Passed | % { Write-Host "  + $_" -ForegroundColor Green } }
if ($script:Summary.Warnings) { Write-Host "`nWARNINGS ($($script:Summary.Warnings.Count)):" -ForegroundColor Yellow; $script:Summary.Warnings | % { Write-Host "  ! $_" -ForegroundColor Yellow } }
if ($script:Summary.Failed) { Write-Host "`nFAILED ($($script:Summary.Failed.Count)):" -ForegroundColor Red; $script:Summary.Failed | % { Write-Host "  x $_" -ForegroundColor Red } }

# Next steps
Write-Banner "Next Steps"
if ($script:Summary.Failed.Count -eq 0) {
    Write-Host "Installation complete! To start:`n" -ForegroundColor Green
    Write-Host "  wsl -d $script:UbuntuDistro" -ForegroundColor Cyan
    Write-Host "  cd ~/maia" -ForegroundColor Cyan
    Write-Host "  claude`n" -ForegroundColor Cyan
} else {
    Write-Host "Fix errors and re-run script." -ForegroundColor Yellow
}
