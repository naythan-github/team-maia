# Maia WSL Prerequisites Setup Script
# Purpose: Check and install all prerequisites for restoring Maia on Windows+WSL
# Version: 1.0
# Created: 2025-10-21

#Requires -RunAsAdministrator

param(
    [switch]$CheckOnly,  # Only check prerequisites, don't install
    [switch]$Verbose     # Show detailed progress
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Maia WSL Prerequisites Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Track overall status
$script:AllPrerequisitesMet = $true
$script:InstallationLog = @()

function Write-Status {
    param(
        [string]$Message,
        [string]$Type = "Info"  # Info, Success, Warning, Error
    )

    $color = switch ($Type) {
        "Success" { "Green" }
        "Warning" { "Yellow" }
        "Error" { "Red" }
        default { "White" }
    }

    $prefix = switch ($Type) {
        "Success" { "✅" }
        "Warning" { "⚠️ " }
        "Error" { "❌" }
        default { "ℹ️ " }
    }

    Write-Host "$prefix $Message" -ForegroundColor $color
    $script:InstallationLog += "$prefix $Message"
}

function Test-IsAdmin {
    $currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    return $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Test-WSLInstalled {
    Write-Host "`n1️⃣  Checking WSL Installation..." -ForegroundColor Cyan

    try {
        $wslVersion = wsl --version 2>&1

        if ($LASTEXITCODE -eq 0) {
            Write-Status "WSL is installed" "Success"

            # Check WSL version
            $versionInfo = $wslVersion | Out-String
            if ($Verbose) {
                Write-Host "   $versionInfo" -ForegroundColor Gray
            }

            return $true
        }
    } catch {
        # WSL not installed
    }

    Write-Status "WSL is NOT installed" "Warning"
    $script:AllPrerequisitesMet = $false

    if (-not $CheckOnly) {
        Write-Host "   Installing WSL 2..." -ForegroundColor Yellow

        try {
            # Install WSL with default Ubuntu distribution
            wsl --install

            Write-Status "WSL installation initiated" "Success"
            Write-Status "IMPORTANT: System restart required!" "Warning"
            Write-Host "   After restart, run this script again to continue setup." -ForegroundColor Yellow

            $restart = Read-Host "`n   Restart now? (y/N)"
            if ($restart -eq "y") {
                Restart-Computer -Force
            }

            return $false
        } catch {
            Write-Status "Failed to install WSL: $_" "Error"
            Write-Host "   Manual installation: https://learn.microsoft.com/en-us/windows/wsl/install" -ForegroundColor Yellow
            return $false
        }
    }

    return $false
}

function Test-WSLDistribution {
    Write-Host "`n2️⃣  Checking WSL Distribution..." -ForegroundColor Cyan

    try {
        $distros = wsl --list --verbose 2>&1 | Out-String

        if ($distros -match "Ubuntu") {
            Write-Status "Ubuntu distribution found" "Success"

            if ($Verbose) {
                Write-Host "   Installed distributions:" -ForegroundColor Gray
                Write-Host "   $distros" -ForegroundColor Gray
            }

            # Check if default distro is set
            if ($distros -match "\*") {
                Write-Status "Default distribution is set" "Success"
            } else {
                Write-Status "No default distribution set" "Warning"
                if (-not $CheckOnly) {
                    wsl --set-default Ubuntu
                    Write-Status "Set Ubuntu as default" "Success"
                }
            }

            return $true
        } else {
            Write-Status "No Ubuntu distribution found" "Warning"
            $script:AllPrerequisitesMet = $false

            if (-not $CheckOnly) {
                Write-Host "   Installing Ubuntu..." -ForegroundColor Yellow
                wsl --install -d Ubuntu-22.04
                Write-Status "Ubuntu installation initiated" "Success"
                Write-Status "Complete Ubuntu setup, then re-run this script" "Warning"
                return $false
            }
        }
    } catch {
        Write-Status "Could not check WSL distributions: $_" "Error"
        $script:AllPrerequisitesMet = $false
        return $false
    }

    return $false
}

function Test-VSCodeInstalled {
    Write-Host "`n3️⃣  Checking VSCode Installation..." -ForegroundColor Cyan

    $vscodePaths = @(
        "${env:LOCALAPPDATA}\Programs\Microsoft VS Code\Code.exe",
        "${env:ProgramFiles}\Microsoft VS Code\Code.exe",
        "${env:ProgramFiles(x86)}\Microsoft VS Code\Code.exe"
    )

    $vscodeInstalled = $false
    foreach ($path in $vscodePaths) {
        if (Test-Path $path) {
            Write-Status "VSCode found at: $path" "Success"
            $vscodeInstalled = $true
            break
        }
    }

    if (-not $vscodeInstalled) {
        Write-Status "VSCode is NOT installed" "Warning"
        $script:AllPrerequisitesMet = $false

        if (-not $CheckOnly) {
            Write-Host "   Downloading VSCode installer..." -ForegroundColor Yellow

            $installerPath = "$env:TEMP\VSCodeSetup.exe"
            $downloadUrl = "https://code.visualstudio.com/sha/download?build=stable&os=win32-x64-user"

            try {
                Invoke-WebRequest -Uri $downloadUrl -OutFile $installerPath

                Write-Host "   Running VSCode installer..." -ForegroundColor Yellow
                Start-Process -FilePath $installerPath -ArgumentList "/VERYSILENT /MERGETASKS=!runcode" -Wait

                Write-Status "VSCode installed successfully" "Success"
                return $true
            } catch {
                Write-Status "Failed to install VSCode: $_" "Error"
                Write-Host "   Manual download: https://code.visualstudio.com/download" -ForegroundColor Yellow
                return $false
            }
        }

        return $false
    }

    return $true
}

function Test-VSCodeWSLExtension {
    Write-Host "`n4️⃣  Checking VSCode WSL Extension..." -ForegroundColor Cyan

    try {
        $extensions = code --list-extensions 2>&1 | Out-String

        if ($extensions -match "ms-vscode-remote.remote-wsl") {
            Write-Status "VSCode WSL extension is installed" "Success"
            return $true
        } else {
            Write-Status "VSCode WSL extension is NOT installed" "Warning"
            $script:AllPrerequisitesMet = $false

            if (-not $CheckOnly) {
                Write-Host "   Installing VSCode WSL extension..." -ForegroundColor Yellow
                code --install-extension ms-vscode-remote.remote-wsl --force

                if ($LASTEXITCODE -eq 0) {
                    Write-Status "VSCode WSL extension installed" "Success"
                    return $true
                } else {
                    Write-Status "Failed to install VSCode WSL extension" "Error"
                    Write-Host "   Manual: Open VSCode → Extensions → Search 'Remote - WSL' → Install" -ForegroundColor Yellow
                    return $false
                }
            }
        }
    } catch {
        Write-Status "Could not check VSCode extensions: $_" "Warning"
        Write-Host "   You may need to install the Remote - WSL extension manually" -ForegroundColor Yellow
        return $false
    }

    return $false
}

function Test-PythonInWSL {
    Write-Host "`n5️⃣  Checking Python in WSL..." -ForegroundColor Cyan

    try {
        $pythonVersion = wsl python3 --version 2>&1

        if ($LASTEXITCODE -eq 0) {
            Write-Status "Python found in WSL: $pythonVersion" "Success"

            # Check pip
            $pipVersion = wsl pip3 --version 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Status "pip found in WSL: $pipVersion" "Success"
            } else {
                Write-Status "pip NOT found in WSL" "Warning"

                if (-not $CheckOnly) {
                    Write-Host "   Installing pip in WSL..." -ForegroundColor Yellow
                    wsl sudo apt update
                    wsl sudo apt install -y python3-pip
                    Write-Status "pip installed in WSL" "Success"
                }
            }

            return $true
        } else {
            Write-Status "Python is NOT installed in WSL" "Warning"
            $script:AllPrerequisitesMet = $false

            if (-not $CheckOnly) {
                Write-Host "   Installing Python in WSL..." -ForegroundColor Yellow
                wsl sudo apt update
                wsl sudo apt install -y python3 python3-pip

                Write-Status "Python installed in WSL" "Success"
                return $true
            }
        }
    } catch {
        Write-Status "Could not check Python in WSL: $_" "Error"
        Write-Status "Ensure WSL is running and Ubuntu is set as default" "Warning"
        return $false
    }

    return $false
}

function Test-OneDriveSync {
    Write-Host "`n6️⃣  Checking OneDrive Sync..." -ForegroundColor Cyan

    $onedrivePaths = @(
        "$env:USERPROFILE\OneDrive - ORROPTYLTD",
        "$env:USERPROFILE\OneDrive"
    )

    $oneDriveFound = $false
    $oneDrivePath = $null

    foreach ($path in $onedrivePaths) {
        if (Test-Path $path) {
            Write-Status "OneDrive found at: $path" "Success"
            $oneDriveFound = $true
            $oneDrivePath = $path
            break
        }
    }

    if (-not $oneDriveFound) {
        Write-Status "OneDrive folder not found" "Warning"
        Write-Host "   Expected locations:" -ForegroundColor Yellow
        foreach ($path in $onedrivePaths) {
            Write-Host "   - $path" -ForegroundColor Gray
        }
        Write-Host "   Ensure OneDrive is installed and syncing" -ForegroundColor Yellow
        $script:AllPrerequisitesMet = $false
        return $false
    }

    # Check for Maia backups
    $backupPath = Join-Path $oneDrivePath "MaiaBackups"
    if (Test-Path $backupPath) {
        $backups = Get-ChildItem -Path $backupPath -Directory | Where-Object { $_.Name -match "^full_\d{8}_\d{6}$" }

        if ($backups.Count -gt 0) {
            Write-Status "Found $($backups.Count) Maia backup(s)" "Success"

            if ($Verbose) {
                $latestBackup = $backups | Sort-Object Name -Descending | Select-Object -First 1
                Write-Host "   Latest backup: $($latestBackup.Name)" -ForegroundColor Gray
            }
        } else {
            Write-Status "MaiaBackups folder exists but no backups found" "Warning"
            Write-Host "   Backups will appear here after macOS backup runs" -ForegroundColor Gray
        }
    } else {
        Write-Status "MaiaBackups folder not found (will be created during first backup)" "Warning"
    }

    return $true
}

function Test-GitInWSL {
    Write-Host "`n7️⃣  Checking Git in WSL..." -ForegroundColor Cyan

    try {
        $gitVersion = wsl git --version 2>&1

        if ($LASTEXITCODE -eq 0) {
            Write-Status "Git found in WSL: $gitVersion" "Success"
            return $true
        } else {
            Write-Status "Git is NOT installed in WSL" "Warning"

            if (-not $CheckOnly) {
                Write-Host "   Installing Git in WSL..." -ForegroundColor Yellow
                wsl sudo apt update
                wsl sudo apt install -y git

                Write-Status "Git installed in WSL" "Success"
                Write-Host "   Remember to configure Git:" -ForegroundColor Yellow
                Write-Host "     wsl git config --global user.name 'Your Name'" -ForegroundColor Gray
                Write-Host "     wsl git config --global user.email 'your.email@example.com'" -ForegroundColor Gray
                return $true
            }
        }
    } catch {
        Write-Status "Could not check Git in WSL: $_" "Error"
        return $false
    }

    return $false
}

# Main execution
Write-Host "Running prerequisite checks..." -ForegroundColor White
Write-Host ""

if (-not (Test-IsAdmin)) {
    Write-Status "This script must be run as Administrator" "Error"
    Write-Host "`nRight-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

if ($CheckOnly) {
    Write-Host "📋 CHECK-ONLY MODE (no installations will be performed)" -ForegroundColor Yellow
    Write-Host ""
}

# Run all checks
$wslInstalled = Test-WSLInstalled
if (-not $wslInstalled) {
    Write-Host "`n❌ WSL installation incomplete. Please restart and re-run this script." -ForegroundColor Red
    exit 1
}

$wslDistro = Test-WSLDistribution
$vscodeInstalled = Test-VSCodeInstalled
$vscodeWSLExtension = Test-VSCodeWSLExtension
$pythonInWSL = Test-PythonInWSL
$oneDriveSync = Test-OneDriveSync
$gitInWSL = Test-GitInWSL

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($script:AllPrerequisitesMet) {
    Write-Status "All prerequisites are met! ✨" "Success"
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Green
    Write-Host "  1. Ensure you have access to a Maia backup in OneDrive" -ForegroundColor White
    Write-Host "  2. Open WSL terminal (type 'wsl' in PowerShell)" -ForegroundColor White
    Write-Host "  3. Navigate to backup folder:" -ForegroundColor White
    Write-Host "     cd '/mnt/c/Users/$env:USERNAME/OneDrive - ORROPTYLTD/MaiaBackups/full_YYYYMMDD_HHMMSS'" -ForegroundColor Gray
    Write-Host "  4. Run restore script:" -ForegroundColor White
    Write-Host "     ./restore_maia.sh" -ForegroundColor Gray
    Write-Host ""
} else {
    Write-Status "Some prerequisites are missing" "Warning"

    if ($CheckOnly) {
        Write-Host ""
        Write-Host "Re-run this script WITHOUT -CheckOnly to install missing components:" -ForegroundColor Yellow
        Write-Host "  .\setup_wsl_prerequisites.ps1" -ForegroundColor Gray
    } else {
        Write-Host ""
        Write-Host "Please address the warnings above and re-run this script" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Installation log saved to: $env:TEMP\maia_wsl_setup_log.txt" -ForegroundColor Gray
$script:InstallationLog | Out-File -FilePath "$env:TEMP\maia_wsl_setup_log.txt" -Encoding UTF8

Write-Host ""
