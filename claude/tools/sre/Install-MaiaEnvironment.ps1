#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Complete MAIA environment setup for Windows with WSL, VSCode, and Claude Code.

.DESCRIPTION
    Automated installer for all components needed to run MAIA on Windows:
    - WSL2 with Ubuntu 22.04
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

.EXAMPLE
    .\Install-MaiaEnvironment.ps1

.EXAMPLE
    .\Install-MaiaEnvironment.ps1 -CheckOnly

.NOTES
    Version: 2.0
    Requires: Windows 10 2004+ or Windows 11, Administrator privileges
#>

param(
    [switch]$CheckOnly,
    [switch]$SkipRestart,
    [string]$MaiaRepo = "https://github.com/naythan-orro/maia.git"
)

$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"

# Configuration
$script:Config = @{
    UbuntuVersion = "Ubuntu-22.04"
    NodeVersion = "20"  # LTS version
    PythonVersion = "3.11"
    RequiredDiskSpaceGB = 10
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
    Write-Step 2 "Checking WSL2"

    # Check if WSL is installed
    $wslInstalled = $false
    try {
        $wslVersion = wsl --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $wslInstalled = $true
            Write-Status "WSL2 is installed" "OK"
        }
    } catch {}

    if (-not $wslInstalled) {
        Write-Status "WSL2 is not installed" "WARN"

        if ($CheckOnly) {
            return $false
        }

        Write-Host "    Installing WSL2..." -ForegroundColor Gray

        try {
            # Enable WSL feature
            dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart | Out-Null
            dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart | Out-Null

            # Set WSL2 as default
            wsl --set-default-version 2 2>&1 | Out-Null

            Write-Status "WSL2 features enabled" "OK"
            Write-Status "RESTART REQUIRED to complete WSL2 installation" "WARN"
            $script:Results.NeedsRestart = $true
            return $false
        } catch {
            Write-Status "Failed to enable WSL2: $_" "ERROR"
            return $false
        }
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

    # Install packages in WSL
    Write-Host "    Updating apt packages..." -ForegroundColor Gray
    Invoke-WSLCommand "apt update" -Sudo | Out-Null

    Write-Host "    Installing core packages..." -ForegroundColor Gray
    $packages = "build-essential curl wget git vim htop tree jq unzip software-properties-common apt-transport-https ca-certificates gnupg lsb-release ripgrep fd-find bat"
    Invoke-WSLCommand "apt install -y $packages" -Sudo | Out-Null
    Write-Status "Core packages installed" "OK"

    # Python 3.11
    Write-Host "    Installing Python 3.11..." -ForegroundColor Gray
    Invoke-WSLCommand "add-apt-repository ppa:deadsnakes/ppa -y" -Sudo | Out-Null
    Invoke-WSLCommand "apt update" -Sudo | Out-Null
    Invoke-WSLCommand "apt install -y python3.11 python3.11-dev python3.11-venv python3-pip python3.11-distutils" -Sudo | Out-Null
    Invoke-WSLCommand "update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1" -Sudo | Out-Null

    $pythonCheck = Get-WSLCommand "python3 --version"
    if ($pythonCheck.Success) {
        Write-Status "Python: $($pythonCheck.Output)" "OK"
    }

    # Node.js in WSL
    Write-Host "    Installing Node.js in WSL..." -ForegroundColor Gray
    Invoke-WSLCommand "curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -" | Out-Null
    Invoke-WSLCommand "apt install -y nodejs" -Sudo | Out-Null

    $nodeCheck = Get-WSLCommand "node --version"
    if ($nodeCheck.Success) {
        Write-Status "Node.js (WSL): $($nodeCheck.Output)" "OK"
    }

    # Claude Code in WSL
    Write-Host "    Installing Claude Code in WSL..." -ForegroundColor Gray
    Invoke-WSLCommand "npm install -g @anthropic-ai/claude-code" -Sudo | Out-Null

    $claudeCheck = Get-WSLCommand "claude --version"
    if ($claudeCheck.Success) {
        Write-Status "Claude Code (WSL): $($claudeCheck.Output)" "OK"
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

    # Create directory and clone
    Invoke-WSLCommand "mkdir -p ~/maia"
    $cloneResult = Invoke-WSLCommand "git clone $MaiaRepo ~/maia"

    if ($cloneResult) {
        Write-Status "MAIA repository cloned" "OK"
    } else {
        Write-Status "Failed to clone MAIA - check repository access" "ERROR"
        return $false
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
export MAIA_ENV=wsl2
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

Write-Banner "MAIA Environment Installer v2.0"

if ($CheckOnly) {
    Write-Host "MODE: Check Only (no installations)" -ForegroundColor Yellow
} else {
    Write-Host "MODE: Full Installation" -ForegroundColor Green
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
