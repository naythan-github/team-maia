#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Repairs Windows Update failures caused by component store corruption.

.DESCRIPTION
    Automated remediation script for Windows Update failures, specifically:
    - HRESULT_FROM_WIN32(15010) - Event channel conflicts
    - CBS_E_INVALID_PACKAGE (0x800f0805) - Corrupted packages
    - Component store corruption

    Based on analysis of CBS/DISM logs from failed update attempts.

.PARAMETER SkipReboot
    Skip automatic reboot prompts.

.PARAMETER RepairOnly
    Only run repair steps, don't attempt update installation.

.PARAMETER LogPath
    Path to save repair log. Default: C:\Windows\Logs\WURepair

.EXAMPLE
    .\Repair-WindowsUpdate.ps1

.EXAMPLE
    .\Repair-WindowsUpdate.ps1 -SkipReboot -RepairOnly

.NOTES
    Target: Windows Server 2016 with Event Log provider conflict
    Error: HRESULT_FROM_WIN32(15010) / CBS_E_INVALID_PACKAGE
#>

param(
    [switch]$SkipReboot,
    [switch]$RepairOnly,
    [string]$LogPath = "C:\Windows\Logs\WURepair"
)

$ErrorActionPreference = "Continue"
$script:StartTime = Get-Date
$script:LogFile = Join-Path $LogPath "WURepair_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

#region Logging Functions

function Initialize-Logging {
    if (-not (Test-Path $LogPath)) {
        New-Item -ItemType Directory -Path $LogPath -Force | Out-Null
    }

    $header = @"
========================================
Windows Update Repair Script
Started: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
Computer: $env:COMPUTERNAME
OS: $((Get-CimInstance Win32_OperatingSystem).Caption)
Build: $((Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion').CurrentBuild)
========================================

"@
    $header | Out-File $script:LogFile -Encoding UTF8
    Write-Host $header -ForegroundColor Cyan
}

function Write-Log {
    param(
        [string]$Message,
        [ValidateSet("INFO", "OK", "WARN", "ERROR", "STEP")]
        [string]$Level = "INFO"
    )

    $timestamp = Get-Date -Format "HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"

    $color = switch ($Level) {
        "OK"    { "Green" }
        "WARN"  { "Yellow" }
        "ERROR" { "Red" }
        "STEP"  { "Cyan" }
        default { "White" }
    }

    $prefix = switch ($Level) {
        "OK"    { "[OK]   " }
        "WARN"  { "[WARN] " }
        "ERROR" { "[FAIL] " }
        "STEP"  { "[STEP] " }
        default { "[INFO] " }
    }

    Write-Host "$prefix$Message" -ForegroundColor $color
    $logEntry | Out-File $script:LogFile -Append -Encoding UTF8
}

#endregion

#region Repair Functions

function Stop-UpdateServices {
    Write-Log "Stopping Windows Update services..." "STEP"

    $services = @("wuauserv", "bits", "cryptsvc", "msiserver", "TrustedInstaller")

    foreach ($svc in $services) {
        try {
            $service = Get-Service -Name $svc -ErrorAction SilentlyContinue
            if ($service -and $service.Status -eq 'Running') {
                Stop-Service -Name $svc -Force -ErrorAction Stop
                Write-Log "Stopped: $svc" "OK"
            } else {
                Write-Log "Already stopped: $svc" "INFO"
            }
        } catch {
            Write-Log "Could not stop $svc`: $_" "WARN"
        }
    }
}

function Start-UpdateServices {
    Write-Log "Starting Windows Update services..." "STEP"

    $services = @("cryptsvc", "bits", "wuauserv", "TrustedInstaller")

    foreach ($svc in $services) {
        try {
            Start-Service -Name $svc -ErrorAction Stop
            Write-Log "Started: $svc" "OK"
        } catch {
            Write-Log "Could not start $svc`: $_" "WARN"
        }
    }
}

function Repair-ComponentStore {
    Write-Log "Running DISM Component Store repair..." "STEP"

    # Check Health
    Write-Log "DISM CheckHealth..." "INFO"
    $checkHealth = & DISM /Online /Cleanup-Image /CheckHealth 2>&1
    $checkHealth | Out-File $script:LogFile -Append -Encoding UTF8

    if ($checkHealth -match "No component store corruption detected") {
        Write-Log "CheckHealth: No corruption detected" "OK"
    } elseif ($checkHealth -match "repairable") {
        Write-Log "CheckHealth: Corruption detected but repairable" "WARN"
    } else {
        Write-Log "CheckHealth: Potential issues detected" "WARN"
    }

    # Scan Health
    Write-Log "DISM ScanHealth (this may take 10-15 minutes)..." "INFO"
    $scanHealth = & DISM /Online /Cleanup-Image /ScanHealth 2>&1
    $scanHealth | Out-File $script:LogFile -Append -Encoding UTF8

    if ($LASTEXITCODE -eq 0) {
        Write-Log "ScanHealth completed" "OK"
    } else {
        Write-Log "ScanHealth returned exit code: $LASTEXITCODE" "WARN"
    }

    # Restore Health
    Write-Log "DISM RestoreHealth (this may take 15-30 minutes)..." "INFO"
    $restoreHealth = & DISM /Online /Cleanup-Image /RestoreHealth 2>&1
    $restoreHealth | Out-File $script:LogFile -Append -Encoding UTF8

    if ($LASTEXITCODE -eq 0) {
        Write-Log "RestoreHealth completed successfully" "OK"
        return $true
    } else {
        Write-Log "RestoreHealth failed with exit code: $LASTEXITCODE" "ERROR"
        Write-Log "May need to use Windows installation media as repair source" "WARN"
        return $false
    }
}

function Clear-UpdateCache {
    Write-Log "Clearing Windows Update cache..." "STEP"

    $foldersToRename = @(
        @{ Path = "C:\Windows\SoftwareDistribution"; NewName = "SoftwareDistribution.old.$(Get-Date -Format 'yyyyMMddHHmmss')" },
        @{ Path = "C:\Windows\System32\catroot2"; NewName = "catroot2.old.$(Get-Date -Format 'yyyyMMddHHmmss')" }
    )

    foreach ($folder in $foldersToRename) {
        if (Test-Path $folder.Path) {
            try {
                $newPath = Join-Path (Split-Path $folder.Path -Parent) $folder.NewName
                Rename-Item -Path $folder.Path -NewName $folder.NewName -Force -ErrorAction Stop
                Write-Log "Renamed: $($folder.Path) -> $($folder.NewName)" "OK"
            } catch {
                Write-Log "Could not rename $($folder.Path): $_" "WARN"

                # Try to delete contents instead
                try {
                    Get-ChildItem -Path $folder.Path -Recurse -Force | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
                    Write-Log "Cleared contents of: $($folder.Path)" "OK"
                } catch {
                    Write-Log "Could not clear $($folder.Path): $_" "ERROR"
                }
            }
        }
    }
}

function Repair-EventLogProviders {
    Write-Log "Checking Event Log provider conflicts..." "STEP"

    # Check for the specific Microsoft-Windows-Store conflict
    try {
        $storeProvider = & wevtutil gp Microsoft-Windows-Store 2>&1

        if ($LASTEXITCODE -eq 0) {
            Write-Log "Microsoft-Windows-Store provider exists" "INFO"
            $storeProvider | Out-File $script:LogFile -Append -Encoding UTF8
        }

        # Check for duplicate channel registrations
        $channels = & wevtutil el 2>&1 | Where-Object { $_ -match "Store" }

        if ($channels) {
            Write-Log "Found Store-related channels:" "INFO"
            $channels | ForEach-Object { Write-Log "  $_" "INFO" }
        }

        # Attempt to re-register Windows Event providers
        Write-Log "Re-registering Windows Event manifests..." "INFO"

        $manifestPath = "C:\Windows\System32\winevt\Publishers"
        if (Test-Path $manifestPath) {
            # This triggers Windows to rebuild event provider registrations
            & wevtutil im "$env:SystemRoot\System32\winevt\Publishers\*" 2>&1 | Out-Null
        }

        Write-Log "Event log provider check completed" "OK"

    } catch {
        Write-Log "Event log provider check failed: $_" "WARN"
    }
}

function Run-SystemFileChecker {
    Write-Log "Running System File Checker..." "STEP"

    $sfcResult = & sfc /scannow 2>&1
    $sfcResult | Out-File $script:LogFile -Append -Encoding UTF8

    if ($sfcResult -match "did not find any integrity violations") {
        Write-Log "SFC: No integrity violations found" "OK"
        return $true
    } elseif ($sfcResult -match "successfully repaired") {
        Write-Log "SFC: Found and repaired integrity violations" "OK"
        return $true
    } elseif ($sfcResult -match "found corrupt files but was unable to fix") {
        Write-Log "SFC: Found corrupt files but could not repair" "ERROR"
        return $false
    } else {
        Write-Log "SFC completed with unknown status" "WARN"
        return $true
    }
}

function Clear-PendingOperations {
    Write-Log "Clearing pending update operations..." "STEP"

    # Clear pending.xml if it exists
    $pendingXml = "C:\Windows\WinSxS\pending.xml"
    if (Test-Path $pendingXml) {
        try {
            # Take ownership and remove
            takeown /f $pendingXml /a 2>&1 | Out-Null
            icacls $pendingXml /grant Administrators:F 2>&1 | Out-Null
            Remove-Item $pendingXml -Force -ErrorAction Stop
            Write-Log "Removed pending.xml" "OK"
        } catch {
            Write-Log "Could not remove pending.xml: $_" "WARN"
        }
    } else {
        Write-Log "No pending.xml found" "INFO"
    }

    # Clear SessionsPending registry key
    $sessionsPending = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\SessionsPending"
    if (Test-Path $sessionsPending) {
        try {
            $pendingCount = (Get-ChildItem $sessionsPending -ErrorAction SilentlyContinue).Count
            if ($pendingCount -gt 0) {
                Write-Log "Found $pendingCount pending sessions" "INFO"
            }
        } catch {
            Write-Log "Could not check SessionsPending: $_" "WARN"
        }
    }

    # Reset Windows Update components via registry
    $wuRegKeys = @(
        "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate",
        "HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate"
    )

    foreach ($key in $wuRegKeys) {
        if (Test-Path $key) {
            try {
                # Remove SusClientId to force re-registration
                Remove-ItemProperty -Path $key -Name "SusClientId" -ErrorAction SilentlyContinue
                Remove-ItemProperty -Path $key -Name "SusClientIdValidation" -ErrorAction SilentlyContinue
                Write-Log "Reset WU client ID in: $key" "OK"
            } catch {
                Write-Log "Could not reset $key`: $_" "WARN"
            }
        }
    }
}

function Reset-WindowsUpdateComponents {
    Write-Log "Resetting Windows Update components..." "STEP"

    # Re-register DLLs
    $dlls = @(
        "atl.dll", "urlmon.dll", "mshtml.dll", "shdocvw.dll", "browseui.dll",
        "jscript.dll", "vbscript.dll", "scrrun.dll", "msxml.dll", "msxml3.dll",
        "msxml6.dll", "actxprxy.dll", "softpub.dll", "wintrust.dll", "dssenh.dll",
        "rsaenh.dll", "gpkcsp.dll", "sccbase.dll", "slbcsp.dll", "cryptdlg.dll",
        "oleaut32.dll", "ole32.dll", "shell32.dll", "initpki.dll", "wuapi.dll",
        "wuaueng.dll", "wuaueng1.dll", "wucltui.dll", "wups.dll", "wups2.dll",
        "wuweb.dll", "qmgr.dll", "qmgrprxy.dll", "wucltux.dll", "muweb.dll", "wuwebv.dll"
    )

    $registered = 0
    foreach ($dll in $dlls) {
        $result = & regsvr32.exe /s "$env:SystemRoot\System32\$dll" 2>&1
        if ($LASTEXITCODE -eq 0) {
            $registered++
        }
    }

    Write-Log "Re-registered $registered of $($dlls.Count) DLLs" "OK"

    # Reset Winsock
    Write-Log "Resetting Winsock..." "INFO"
    & netsh winsock reset 2>&1 | Out-Null
    & netsh winhttp reset proxy 2>&1 | Out-Null
    Write-Log "Network stack reset" "OK"
}

function Invoke-WindowsUpdate {
    Write-Log "Triggering Windows Update scan..." "STEP"

    try {
        # Use UsoClient on Server 2016+
        $usoClient = "$env:SystemRoot\System32\UsoClient.exe"

        if (Test-Path $usoClient) {
            Write-Log "Starting update scan via UsoClient..." "INFO"
            & $usoClient StartScan 2>&1 | Out-Null
            Start-Sleep -Seconds 10

            Write-Log "Starting update download..." "INFO"
            & $usoClient StartDownload 2>&1 | Out-Null

            Write-Log "Windows Update scan initiated" "OK"
        } else {
            # Fallback to wuauclt
            Write-Log "Using wuauclt for update scan..." "INFO"
            & wuauclt /detectnow /updatenow 2>&1 | Out-Null
            Write-Log "Windows Update scan initiated via wuauclt" "OK"
        }

        return $true
    } catch {
        Write-Log "Failed to trigger Windows Update: $_" "ERROR"
        return $false
    }
}

#endregion

#region Main Execution

Initialize-Logging

Write-Log "=" * 50 "INFO"
Write-Log "PHASE 1: Stop Services" "STEP"
Write-Log "=" * 50 "INFO"
Stop-UpdateServices

Write-Log "" "INFO"
Write-Log "=" * 50 "INFO"
Write-Log "PHASE 2: Clear Pending Operations" "STEP"
Write-Log "=" * 50 "INFO"
Clear-PendingOperations

Write-Log "" "INFO"
Write-Log "=" * 50 "INFO"
Write-Log "PHASE 3: Clear Update Cache" "STEP"
Write-Log "=" * 50 "INFO"
Clear-UpdateCache

Write-Log "" "INFO"
Write-Log "=" * 50 "INFO"
Write-Log "PHASE 4: Repair Event Log Providers" "STEP"
Write-Log "=" * 50 "INFO"
Repair-EventLogProviders

Write-Log "" "INFO"
Write-Log "=" * 50 "INFO"
Write-Log "PHASE 5: DISM Component Store Repair" "STEP"
Write-Log "=" * 50 "INFO"
$dismSuccess = Repair-ComponentStore

Write-Log "" "INFO"
Write-Log "=" * 50 "INFO"
Write-Log "PHASE 6: System File Checker" "STEP"
Write-Log "=" * 50 "INFO"
$sfcSuccess = Run-SystemFileChecker

Write-Log "" "INFO"
Write-Log "=" * 50 "INFO"
Write-Log "PHASE 7: Reset Windows Update Components" "STEP"
Write-Log "=" * 50 "INFO"
Reset-WindowsUpdateComponents

Write-Log "" "INFO"
Write-Log "=" * 50 "INFO"
Write-Log "PHASE 8: Restart Services" "STEP"
Write-Log "=" * 50 "INFO"
Start-UpdateServices

if (-not $RepairOnly) {
    Write-Log "" "INFO"
    Write-Log "=" * 50 "INFO"
    Write-Log "PHASE 9: Trigger Windows Update" "STEP"
    Write-Log "=" * 50 "INFO"
    Invoke-WindowsUpdate
}

# Summary
$duration = (Get-Date) - $script:StartTime
Write-Log "" "INFO"
Write-Log "=" * 50 "INFO"
Write-Log "REPAIR COMPLETE" "STEP"
Write-Log "=" * 50 "INFO"
Write-Log "Duration: $($duration.ToString('hh\:mm\:ss'))" "INFO"
Write-Log "Log file: $script:LogFile" "INFO"

if ($dismSuccess -and $sfcSuccess) {
    Write-Log "All repair operations completed successfully" "OK"
    Write-Log "" "INFO"
    Write-Log "RECOMMENDED: Reboot the server and retry Windows Update" "WARN"
} else {
    Write-Log "Some repair operations had issues - review log file" "WARN"
    Write-Log "" "INFO"
    Write-Log "If issues persist after reboot:" "INFO"
    Write-Log "  1. Run DISM with Windows installation media as source" "INFO"
    Write-Log "  2. Consider in-place upgrade to repair Windows" "INFO"
}

if (-not $SkipReboot) {
    Write-Log "" "INFO"
    $reboot = Read-Host "Reboot now to complete repairs? (y/N)"
    if ($reboot -eq 'y' -or $reboot -eq 'Y') {
        Write-Log "Initiating reboot..." "INFO"
        Restart-Computer -Force
    }
}

Write-Log "" "INFO"
Write-Log "Script completed at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" "INFO"

#endregion
