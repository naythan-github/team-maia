#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Complete MAIA environment setup for Windows with WSL, VSCode, and Claude Code.

.DESCRIPTION
    Automated installer for all components needed to run MAIA on Windows:
    - WSL1/WSL2 with Ubuntu 22.04 (WSL1 default for broader VM compatibility)
    - VSCode with Remote-WSL extension
    - Claude Code CLI
    - Node.js (for Claude Code and MCP servers)
    - Python 3.11+ with dependencies
    - Git configuration
    - MAIA repository clone and setup

.PARAMETER CheckOnly
    Only check prerequisites without installing anything.

.PARAMETER SkipRestart
    Skip automatic restart prompts.

.PARAMETER MaiaRepo
    GitHub repository URL for MAIA. Default: https://github.com/naythan-orro/maia.git

.PARAMETER WSLVersion
    WSL version to install (1 or 2). Default: 1 (better Azure VM compatibility).
    WSL2 requires nested virtualization (not available on B-series VMs).

.EXAMPLE
    .\Install-MaiaEnvironment.ps1

.EXAMPLE
    .\Install-MaiaEnvironment.ps1 -CheckOnly

.EXAMPLE
    .\Install-MaiaEnvironment.ps1 -WSLVersion 2

.NOTES
    Version: 2.2
    Requires: Windows 10 2004+ or Windows 11, Administrator privileges
    Changed:
    - WSL1 default for Azure VM compatibility
    - Batched sudo operations (8+ prompts → 2 prompts)
    - Fixed Node.js installation reliability
    - Added Git SSH key authentication handling
#>

param(
    [switch]$CheckOnly,
    [switch]$SkipRestart,
    [string]$MaiaRepo = "https://github.com/naythan-orro/maia.git",
    [ValidateSet(1, 2)]
    [int]$WSLVersion = 1
)

$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"

# Configuration
$script:Config = @{
    UbuntuVersion = "Ubuntu-22.04"
    NodeVersion = "20"  # LTS version
    PythonVersion = "3.11"
    RequiredDiskSpaceGB = 10
    WSLVersion = $WSLVersion
    VSCodeExtensions = @(
        "ms-vscode-remote.remote-wsl",
        "ms-python.python",
        "ms-python.vscode-pylance"
    )
}

# Status tracking
$script:Results = @{
    Passed = @()
    Failed = @()
    Warnings = @()
    NeedsRestart = $false
}

#region Helper Functions

function Write-Banner {
    param([string]$Text)
    $line = "=" * 60
    Write-Host "`n$line" -ForegroundColor Cyan
    Write-Host $Text -ForegroundColor Cyan
    Write-Host "$line`n" -ForegroundColor Cyan
}

function Write-Step {
    param([int]$Number, [string]$Text)
    Write-Host "`n[$Number] $Text" -ForegroundColor Yellow
}

function Write-Status {
    param(
        [string]$Message,
        [ValidateSet("OK", "WARN", "ERROR", "INFO", "SKIP")]
        [string]$Status = "INFO"
    )

    $config = switch ($Status) {
        "OK"    { @{ Color = "Green";  Icon = "[OK]   " } }
        "WARN"  { @{ Color = "Yellow"; Icon = "[WARN] " } }
        "ERROR" { @{ Color = "Red";    Icon = "[FAIL] " } }
        "SKIP"  { @{ Color = "Gray";   Icon = "[SKIP] " } }
        default { @{ Color = "White";  Icon = "[INFO] " } }
    }

    Write-Host "$($config.Icon)$Message" -ForegroundColor $config.Color

    switch ($Status) {
        "OK"    { $script:Results.Passed += $Message }
        "ERROR" { $script:Results.Failed += $Message }
        "WARN"  { $script:Results.Warnings += $Message }
    }
}

function Test-CommandExists {
    param([string]$Command)
    return $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
}

function Get-WSLCommand {
    param([string]$Command)
    $result = wsl -d $script:Config.UbuntuVersion -- bash -c $Command 2>&1
    return @{
        Output = $result
        Success = $LASTEXITCODE -eq 0
    }
}

function Invoke-WSLCommand {
    param([string]$Command, [switch]$Sudo)
    $cmd = if ($Sudo) { "sudo $Command" } else { $Command }
    wsl -d $script:Config.UbuntuVersion -- bash -c $cmd
    return $LASTEXITCODE -eq 0
}

function Install-FromWeb {
    param(
        [string]$Name,
        [string]$Url,
        [string]$OutFile,
        [string]$Arguments = "/S"
    )

    Write-Host "    Downloading $Name..." -ForegroundColor Gray
    try {
        Invoke-WebRequest -Uri $Url -OutFile $OutFile -UseBasicParsing
        Write-Host "    Installing $Name..." -ForegroundColor Gray
        Start-Process -FilePath $OutFile -ArgumentList $Arguments -Wait -NoNewWindow
        Remove-Item $OutFile -Force -ErrorAction SilentlyContinue
        return $true
    } catch {
        Write-Status "Failed to install $Name`: $_" "ERROR"
        return $false
    }
}

#endregion

#region Prerequisite Checks

function Test-SystemRequirements {
    Write-Step 1 "Checking System Requirements"

    # Windows version
    $os = Get-CimInstance Win32_OperatingSystem
    $build = [int](Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion").CurrentBuild

    if ($build -ge 19041) {
        Write-Status "Windows version: $($os.Caption) (Build $build)" "OK"
    } else {
        Write-Status "Windows 10 2004+ or Windows 11 required (Build 19041+). Current: $build" "ERROR"
        return $false
    }

    # Disk space
    $systemDrive = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'"
    $freeGB = [math]::Round($systemDrive.FreeSpace / 1GB, 1)

    if ($freeGB -ge $script:Config.RequiredDiskSpaceGB) {
        Write-Status "Disk space: ${freeGB}GB free" "OK"
    } else {
        Write-Status "Insufficient disk space: ${freeGB}GB free, need $($script:Config.RequiredDiskSpaceGB)GB" "ERROR"
        return $false
    }

    # RAM
    $ram = [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 0)
    if ($ram -ge 8) {
        Write-Status "RAM: ${ram}GB" "OK"
    } else {
        Write-Status "RAM: ${ram}GB (8GB+ recommended)" "WARN"
    }

    return $true
}

function Install-WSL {
    Write-Step 2 "Checking WSL$($script:Config.WSLVersion)"

    # Step 1: Check if required Windows features are enabled
    Write-Host "    Checking Windows features..." -ForegroundColor Gray

    $wslFeature = Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux -ErrorAction SilentlyContinue
    $vmPlatformFeature = Get-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform -ErrorAction SilentlyContinue

    $wslEnabled = $wslFeature -and $wslFeature.State -eq "Enabled"
    $vmPlatformEnabled = $vmPlatformFeature -and $vmPlatformFeature.State -eq "Enabled"

    # Step 2: Enable features if not already enabled
    if (-not $wslEnabled -or -not $vmPlatformEnabled) {
        if ($CheckOnly) {
            if (-not $wslEnabled) { Write-Status "Windows Subsystem for Linux feature not enabled" "WARN" }
            if (-not $vmPlatformEnabled) { Write-Status "Virtual Machine Platform feature not enabled" "WARN" }
            return $false
        }

        Write-Status "Enabling required Windows features (this may take 2-5 minutes)..." "INFO"

        try {
            # Enable WSL feature (required for both WSL1 and WSL2)
            if (-not $wslEnabled) {
                Write-Host "    Enabling Windows Subsystem for Linux..." -ForegroundColor Gray
                dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart | Out-Null

                if ($LASTEXITCODE -eq 0) {
                    Write-Status "Windows Subsystem for Linux enabled" "OK"
                } else {
                    Write-Status "Failed to enable WSL feature (exit code: $LASTEXITCODE)" "ERROR"
                    return $false
                }
            }

            # Enable Virtual Machine Platform (required for both WSL1 and WSL2)
            if (-not $vmPlatformEnabled) {
                Write-Host "    Enabling Virtual Machine Platform..." -ForegroundColor Gray
                dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart | Out-Null

                if ($LASTEXITCODE -eq 0) {
                    Write-Status "Virtual Machine Platform enabled" "OK"
                } else {
                    Write-Status "Failed to enable VM Platform (exit code: $LASTEXITCODE)" "ERROR"
                    return $false
                }
            }

            Write-Status "RESTART REQUIRED to activate Windows features" "WARN"
            Write-Host "    After restart, re-run this script to continue installation" -ForegroundColor Yellow
            $script:Results.NeedsRestart = $true
            return $false

        } catch {
            Write-Status "Failed to enable Windows features: $_" "ERROR"
            return $false
        }
    }

    Write-Status "Required Windows features are enabled" "OK"

    # Step 3: Check if WSL command is available
    $wslInstalled = $false
    try {
        $wslVersion = wsl --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $wslInstalled = $true
            Write-Status "WSL is installed" "OK"
        }
    } catch {}

    if (-not $wslInstalled) {
        Write-Status "WSL command not available (features enabled but may need restart)" "WARN"

        if ($CheckOnly) {
            return $false
        }

        # Features are enabled but WSL command not ready - likely needs restart
        Write-Status "Windows features enabled but WSL not ready - restart may be required" "WARN"
        $script:Results.NeedsRestart = $true
        return $false
    }

    # Step 4: Set WSL version as default
    Write-Host "    Setting WSL$($script:Config.WSLVersion) as default..." -ForegroundColor Gray
    wsl --set-default-version $script:Config.WSLVersion 2>&1 | Out-Null

    if ($LASTEXITCODE -eq 0 -or $LASTEXITCODE -eq 1) {
        Write-Status "WSL$($script:Config.WSLVersion) set as default" "OK"
    } else {
        Write-Status "Could not set WSL version (may already be set)" "WARN"
    }

    return $true
}

function Install-Ubuntu {
    Write-Step 3 "Checking Ubuntu Distribution"

    $distros = wsl --list --quiet 2>&1 | Out-String

    if ($distros -match "Ubuntu") {
        Write-Status "Ubuntu distribution found" "OK"

        # Set as default if not already
        wsl --set-default $script:Config.UbuntuVersion 2>&1 | Out-Null
        return $true
    }

    Write-Status "Ubuntu not found" "WARN"

    if ($CheckOnly) {
        return $false
    }

    Write-Host "    Installing $($script:Config.UbuntuVersion)..." -ForegroundColor Gray

    try {
        wsl --install -d $script:Config.UbuntuVersion --no-launch

        Write-Status "$($script:Config.UbuntuVersion) installation initiated" "OK"
        Write-Status "After restart, launch Ubuntu from Start Menu to complete setup" "WARN"
        $script:Results.NeedsRestart = $true
        return $false
    } catch {
        Write-Status "Failed to install Ubuntu: $_" "ERROR"
        return $false
    }
}

function Install-VSCode {
    Write-Step 4 "Checking VSCode"

    $vscodePaths = @(
        "$env:LOCALAPPDATA\Programs\Microsoft VS Code\Code.exe",
        "$env:ProgramFiles\Microsoft VS Code\Code.exe"
    )

    $vscodeInstalled = $vscodePaths | Where-Object { Test-Path $_ } | Select-Object -First 1

    if ($vscodeInstalled) {
        Write-Status "VSCode installed: $vscodeInstalled" "OK"
    } else {
        Write-Status "VSCode not installed" "WARN"

        if ($CheckOnly) {
            return $false
        }

        $installerUrl = "https://code.visualstudio.com/sha/download?build=stable&os=win32-x64-user"
        $installerPath = "$env:TEMP\VSCodeSetup.exe"

        if (Install-FromWeb -Name "VSCode" -Url $installerUrl -OutFile $installerPath -Arguments "/VERYSILENT /MERGETASKS=!runcode,addtopath") {
            Write-Status "VSCode installed" "OK"
            # Refresh PATH
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
        } else {
            return $false
        }
    }

    # Install extensions
    Write-Host "    Checking VSCode extensions..." -ForegroundColor Gray

    if (Test-CommandExists "code") {
        $installedExtensions = code --list-extensions 2>&1 | Out-String

        foreach ($ext in $script:Config.VSCodeExtensions) {
            if ($installedExtensions -match $ext) {
                Write-Status "Extension: $ext" "OK"
            } else {
                if (-not $CheckOnly) {
                    Write-Host "    Installing extension: $ext..." -ForegroundColor Gray
                    code --install-extension $ext --force 2>&1 | Out-Null
                    Write-Status "Extension installed: $ext" "OK"
                } else {
                    Write-Status "Extension missing: $ext" "WARN"
                }
            }
        }
    } else {
        Write-Status "VSCode 'code' command not in PATH - restart terminal after install" "WARN"
    }

    return $true
}

function Install-NodeJS {
    Write-Step 5 "Checking Node.js (for Claude Code)"

    # Check Windows Node.js (for npm global installs)
    $nodeInstalled = Test-CommandExists "node"

    if ($nodeInstalled) {
        $nodeVersion = node --version 2>&1
        Write-Status "Node.js installed: $nodeVersion" "OK"
    } else {
        Write-Status "Node.js not installed" "WARN"

        if ($CheckOnly) {
            return $false
        }

        Write-Host "    Installing Node.js LTS..." -ForegroundColor Gray

        # Use winget if available, otherwise download installer
        if (Test-CommandExists "winget") {
            winget install OpenJS.NodeJS.LTS --silent --accept-package-agreements --accept-source-agreements 2>&1 | Out-Null

            if ($LASTEXITCODE -eq 0) {
                Write-Status "Node.js installed via winget" "OK"
                # Refresh PATH
                $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
            } else {
                Write-Status "winget install failed, trying direct download..." "WARN"
                $nodeInstalled = $false
            }
        }

        if (-not (Test-CommandExists "node")) {
            $nodeUrl = "https://nodejs.org/dist/v$($script:Config.NodeVersion).0.0/node-v$($script:Config.NodeVersion).0.0-x64.msi"
            $nodeMsi = "$env:TEMP\node-installer.msi"

            if (Install-FromWeb -Name "Node.js" -Url $nodeUrl -OutFile $nodeMsi -Arguments "/quiet /norestart") {
                Write-Status "Node.js installed" "OK"
                $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
            } else {
                return $false
            }
        }
    }

    # Verify npm
    if (Test-CommandExists "npm") {
        $npmVersion = npm --version 2>&1
        Write-Status "npm installed: v$npmVersion" "OK"
    } else {
        Write-Status "npm not found - restart terminal and re-run script" "WARN"
        return $false
    }

    return $true
}

function Install-ClaudeCode {
    Write-Step 6 "Checking Claude Code CLI"

    # Check if Claude Code is installed
    $claudeInstalled = Test-CommandExists "claude"

    if ($claudeInstalled) {
        $claudeVersion = claude --version 2>&1
        Write-Status "Claude Code installed: $claudeVersion" "OK"
        return $true
    }

    Write-Status "Claude Code not installed" "WARN"

    if ($CheckOnly) {
        return $false
    }

    if (-not (Test-CommandExists "npm")) {
        Write-Status "npm required to install Claude Code - install Node.js first" "ERROR"
        return $false
    }

    Write-Host "    Installing Claude Code via npm..." -ForegroundColor Gray

    try {
        npm install -g @anthropic-ai/claude-code 2>&1 | Out-Null

        if ($LASTEXITCODE -eq 0) {
            Write-Status "Claude Code installed" "OK"
            Write-Host "    Run 'claude' to authenticate and configure" -ForegroundColor Gray
            return $true
        } else {
            Write-Status "npm install failed" "ERROR"
            return $false
        }
    } catch {
        Write-Status "Failed to install Claude Code: $_" "ERROR"
        return $false
    }
}

function Install-WSLDependencies {
    Write-Step 7 "Checking WSL Dependencies"

    # Verify WSL is accessible
    $wslTest = Get-WSLCommand "echo 'WSL OK'"
    if (-not $wslTest.Success) {
        Write-Status "Cannot connect to WSL - ensure Ubuntu setup is complete" "ERROR"
        Write-Host "    Launch Ubuntu from Start Menu to complete initial setup" -ForegroundColor Yellow
        return $false
    }

    Write-Status "WSL connection verified" "OK"

    if ($CheckOnly) {
        # Just check what's installed
        $checks = @(
            @{ Name = "Python 3"; Cmd = "python3 --version" },
            @{ Name = "pip"; Cmd = "pip3 --version" },
            @{ Name = "Git"; Cmd = "git --version" },
            @{ Name = "Node.js"; Cmd = "node --version" },
            @{ Name = "Build tools"; Cmd = "gcc --version" }
        )

        foreach ($check in $checks) {
            $result = Get-WSLCommand $check.Cmd
            if ($result.Success) {
                Write-Status "$($check.Name): $($result.Output | Select-Object -First 1)" "OK"
            } else {
                Write-Status "$($check.Name) not installed" "WARN"
            }
        }
        return $true
    }

    # BATCHED INSTALLATION - Single sudo session for all operations
    Write-Host "    Installing all dependencies (this may take 5-10 minutes)..." -ForegroundColor Gray
    Write-Host "    You will be prompted for your password ONCE at the start..." -ForegroundColor Yellow

    # Create a single script that runs all sudo operations
    $installScript = @'
#!/bin/bash
set -e

echo "[1/6] Updating apt..."
apt update 2>&1 | grep -v "does not have a stable CLI" || true

echo "[2/6] Installing core packages..."
apt install -y build-essential curl wget git vim htop tree jq unzip software-properties-common apt-transport-https ca-certificates gnupg lsb-release 2>&1 | grep -v "does not have a stable CLI" || true

echo "[3/6] Adding Python 3.11 repository..."
add-apt-repository ppa:deadsnakes/ppa -y 2>&1 | grep -v "does not have a stable CLI" || true
apt update 2>&1 | grep -v "does not have a stable CLI" || true

echo "[4/6] Installing Python 3.11..."
apt install -y python3.11 python3.11-dev python3.11-venv python3-pip python3.11-distutils 2>&1 | grep -v "does not have a stable CLI" || true
update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 2>/dev/null || true

echo "[5/6] Installing Node.js..."
curl -fsSL https://deb.nodesource.com/setup_lts.x -o /tmp/nodesource_setup.sh
bash /tmp/nodesource_setup.sh 2>&1 | grep -v "does not have a stable CLI" || true
apt install -y nodejs 2>&1 | grep -v "does not have a stable CLI" || true

echo "[6/6] Verifying installations..."
python3 --version
node --version
npm --version

echo "Installation complete!"
'@

    # Write script to temp file in WSL
    $scriptPath = "/tmp/maia_install_$(Get-Date -Format 'yyyyMMddHHmmss').sh"
    Invoke-WSLCommand "echo '$installScript' > $scriptPath && chmod +x $scriptPath"

    # Execute with single sudo call
    Write-Host ""
    Invoke-WSLCommand "bash $scriptPath" -Sudo

    # Cleanup
    Invoke-WSLCommand "rm -f $scriptPath"

    # Verify installations
    Write-Host ""
    $pythonCheck = Get-WSLCommand "python3 --version"
    if ($pythonCheck.Success) {
        Write-Status "Python: $($pythonCheck.Output)" "OK"
    } else {
        Write-Status "Python installation may have issues" "WARN"
    }

    $nodeCheck = Get-WSLCommand "node --version"
    if ($nodeCheck.Success) {
        Write-Status "Node.js: $($nodeCheck.Output)" "OK"
    } else {
        Write-Status "Node.js installation failed" "ERROR"
        return $false
    }

    $npmCheck = Get-WSLCommand "npm --version"
    if ($npmCheck.Success) {
        Write-Status "npm: v$($npmCheck.Output)" "OK"
    } else {
        Write-Status "npm not available" "ERROR"
        return $false
    }

    # Claude Code in WSL (separate call - needs npm)
    Write-Host "    Installing Claude Code CLI..." -ForegroundColor Gray
    Invoke-WSLCommand "npm install -g @anthropic-ai/claude-code" -Sudo | Out-Null

    $claudeCheck = Get-WSLCommand "claude --version"
    if ($claudeCheck.Success) {
        Write-Status "Claude Code: $($claudeCheck.Output)" "OK"
    } else {
        Write-Status "Claude Code installation had issues (can install later)" "WARN"
    }

    return $true
}

function Install-Maia {
    Write-Step 8 "Setting up MAIA"

    # Check if MAIA already exists
    $maiaCheck = Get-WSLCommand "test -d ~/maia && echo 'exists'"

    if ($maiaCheck.Output -match "exists") {
        Write-Status "MAIA directory exists at ~/maia" "OK"

        # Verify it's a git repo
        $gitCheck = Get-WSLCommand "cd ~/maia && git status"
        if ($gitCheck.Success) {
            Write-Status "MAIA repository verified" "OK"
        } else {
            Write-Status "~/maia exists but is not a git repository" "WARN"
        }
        return $true
    }

    if ($CheckOnly) {
        Write-Status "MAIA not installed at ~/maia" "WARN"
        return $false
    }

    Write-Host "    Cloning MAIA repository..." -ForegroundColor Gray
    Write-Host "    Repository: $MaiaRepo" -ForegroundColor Gray

    # Check if SSH key exists
    $sshKeyCheck = Get-WSLCommand "test -f ~/.ssh/id_rsa || test -f ~/.ssh/id_ed25519 && echo 'exists'"
    $hasSshKey = $sshKeyCheck.Output -match "exists"

    # Try SSH URL first if SSH key exists
    $repoUrl = $MaiaRepo
    if ($hasSshKey -and $MaiaRepo -match "https://github.com/(.*)") {
        $repoPath = $Matches[1] -replace '\.git$', ''
        $sshUrl = "git@github.com:$repoPath.git"
        Write-Host "    SSH key found, trying SSH clone: $sshUrl" -ForegroundColor Gray
        $repoUrl = $sshUrl
    }

    # Create directory and clone
    Invoke-WSLCommand "mkdir -p ~/maia"
    $cloneResult = Invoke-WSLCommand "git clone $repoUrl ~/maia 2>&1"

    if ($LASTEXITCODE -eq 0) {
        Write-Status "MAIA repository cloned successfully" "OK"
    } else {
        Write-Status "Failed to clone MAIA" "ERROR"
        Write-Host ""
        Write-Host "    Git clone failed. This repository requires authentication." -ForegroundColor Yellow
        Write-Host ""
        Write-Host "    Option 1: Use SSH key (recommended)" -ForegroundColor Cyan
        Write-Host "      1. Generate SSH key: wsl ssh-keygen -t ed25519 -C 'your_email@example.com'" -ForegroundColor Gray
        Write-Host "      2. Add key to GitHub: wsl cat ~/.ssh/id_ed25519.pub" -ForegroundColor Gray
        Write-Host "      3. Re-run this script" -ForegroundColor Gray
        Write-Host ""
        Write-Host "    Option 2: Use GitHub CLI" -ForegroundColor Cyan
        Write-Host "      1. Install: wsl sudo apt install gh" -ForegroundColor Gray
        Write-Host "      2. Authenticate: wsl gh auth login" -ForegroundColor Gray
        Write-Host "      3. Re-run this script" -ForegroundColor Gray
        Write-Host ""
        Write-Host "    Option 3: Clone manually after setup" -ForegroundColor Cyan
        Write-Host "      1. Complete this installation (will skip MAIA clone)" -ForegroundColor Gray
        Write-Host "      2. Then run: wsl git clone $MaiaRepo ~/maia" -ForegroundColor Gray
        Write-Host ""

        $response = Read-Host "Skip MAIA clone and continue with other setup? (y/N)"
        if ($response -eq "y" -or $response -eq "Y") {
            Write-Status "Skipping MAIA clone - manual setup required" "WARN"
            return $true
        } else {
            return $false
        }
    }

    # Install Python dependencies
    Write-Host "    Installing Python dependencies..." -ForegroundColor Gray
    Invoke-WSLCommand "cd ~/maia && pip3 install -r requirements.txt 2>/dev/null || pip3 install requests beautifulsoup4 pandas pyyaml python-dotenv rich typer pydantic"
    Write-Status "Python dependencies installed" "OK"

    # Set up environment variables
    Write-Host "    Configuring environment..." -ForegroundColor Gray

    $bashrcAdditions = @"

# MAIA Environment
export MAIA_ROOT=~/maia
export MAIA_ENV=wsl$($script:Config.WSLVersion)
export PYTHONPATH=~/maia:\$PYTHONPATH
cd ~/maia 2>/dev/null
"@

    # Check if already configured
    $envCheck = Get-WSLCommand "grep -q MAIA_ROOT ~/.bashrc && echo 'configured'"
    if ($envCheck.Output -notmatch "configured") {
        Invoke-WSLCommand "echo '$bashrcAdditions' >> ~/.bashrc"
        Write-Status "Environment variables configured in ~/.bashrc" "OK"
    } else {
        Write-Status "Environment already configured" "OK"
    }

    return $true
}

function Install-MCPServers {
    Write-Step 9 "Installing MCP Servers (Optional)"

    if ($CheckOnly) {
        Write-Status "MCP servers check skipped in check-only mode" "SKIP"
        return $true
    }

    Write-Host "    Installing global MCP servers..." -ForegroundColor Gray

    $mcpServers = @(
        "@modelcontextprotocol/server-filesystem",
        "@modelcontextprotocol/server-git"
    )

    foreach ($server in $mcpServers) {
        Invoke-WSLCommand "npm install -g $server 2>/dev/null" -Sudo | Out-Null
    }

    Write-Status "MCP servers installed" "OK"
    return $true
}

#endregion

#region Main Execution

Write-Banner "MAIA Environment Installer v2.2"

if ($CheckOnly) {
    Write-Host "MODE: Check Only (no installations)" -ForegroundColor Yellow
} else {
    Write-Host "MODE: Full Installation (WSL$WSLVersion)" -ForegroundColor Green
}

if ($WSLVersion -eq 1) {
    Write-Host "NOTE: Using WSL1 for broader Azure VM compatibility" -ForegroundColor Gray
} else {
    Write-Host "NOTE: WSL2 requires nested virtualization support" -ForegroundColor Gray
}
Write-Host ""

# Run all installation steps
$steps = @(
    { Test-SystemRequirements },
    { Install-WSL },
    { Install-Ubuntu },
    { Install-VSCode },
    { Install-NodeJS },
    { Install-ClaudeCode },
    { Install-WSLDependencies },
    { Install-Maia },
    { Install-MCPServers }
)

$allPassed = $true
foreach ($step in $steps) {
    $result = & $step
    if (-not $result) {
        $allPassed = $false
    }
}

# Summary
Write-Banner "Installation Summary"

if ($script:Results.Passed.Count -gt 0) {
    Write-Host "PASSED ($($script:Results.Passed.Count)):" -ForegroundColor Green
    $script:Results.Passed | ForEach-Object { Write-Host "  + $_" -ForegroundColor Green }
}

if ($script:Results.Warnings.Count -gt 0) {
    Write-Host "`nWARNINGS ($($script:Results.Warnings.Count)):" -ForegroundColor Yellow
    $script:Results.Warnings | ForEach-Object { Write-Host "  ! $_" -ForegroundColor Yellow }
}

if ($script:Results.Failed.Count -gt 0) {
    Write-Host "`nFAILED ($($script:Results.Failed.Count)):" -ForegroundColor Red
    $script:Results.Failed | ForEach-Object { Write-Host "  x $_" -ForegroundColor Red }
}

# Next steps
Write-Host "`n" -NoNewline
Write-Banner "Next Steps"

if ($script:Results.NeedsRestart) {
    Write-Host "1. RESTART YOUR COMPUTER to complete WSL2 installation" -ForegroundColor Red
    Write-Host "2. After restart, launch Ubuntu from Start Menu to complete setup" -ForegroundColor Yellow
    Write-Host "3. Re-run this script to continue installation" -ForegroundColor Yellow

    if (-not $SkipRestart) {
        $restart = Read-Host "`nRestart now? (y/N)"
        if ($restart -eq "y" -or $restart -eq "Y") {
            Restart-Computer -Force
        }
    }
} elseif ($allPassed) {
    Write-Host "Installation complete! To get started:" -ForegroundColor Green
    Write-Host ""
    Write-Host "  1. Open Windows Terminal or PowerShell" -ForegroundColor White
    Write-Host "  2. Type: wsl" -ForegroundColor Cyan
    Write-Host "  3. Navigate to MAIA: cd ~/maia" -ForegroundColor Cyan
    Write-Host "  4. Launch VSCode: code ." -ForegroundColor Cyan
    Write-Host "  5. Authenticate Claude: claude" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Or open VSCode directly:" -ForegroundColor White
    Write-Host "  code --remote wsl+Ubuntu-22.04 ~/maia" -ForegroundColor Cyan
} else {
    Write-Host "Some components need attention. Review warnings above." -ForegroundColor Yellow
    Write-Host "Re-run this script after addressing issues." -ForegroundColor Yellow
}

# Save log
$logPath = "$env:TEMP\maia_install_log_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"
@"
MAIA Environment Installation Log
Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

PASSED:
$($script:Results.Passed -join "`n")

WARNINGS:
$($script:Results.Warnings -join "`n")

FAILED:
$($script:Results.Failed -join "`n")
"@ | Out-File $logPath -Encoding UTF8

Write-Host "`nLog saved: $logPath" -ForegroundColor Gray

#endregion
