#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Exports Windows Update diagnostic logs in JSON format for analysis.

.DESCRIPTION
    Collects all relevant Windows Update logs, event logs, and system state
    into a structured JSON format for automated parsing and root cause analysis.

.PARAMETER OutputPath
    Directory to export logs. Defaults to current directory.

.PARAMETER MaxEventAge
    Maximum age of events to collect in days. Default 7.

.EXAMPLE
    .\Export-WindowsUpdateLogs.ps1 -OutputPath C:\Logs\WUDiag
#>

param(
    [string]$OutputPath = (Join-Path $env:USERPROFILE "WUDiagnostics_$(Get-Date -Format 'yyyyMMdd_HHmmss')"),
    [int]$MaxEventAge = 7
)

$ErrorActionPreference = "Continue"
$StartTime = (Get-Date).AddDays(-$MaxEventAge)

function Write-Status {
    param([string]$Message, [string]$Status = "INFO")
    $color = switch ($Status) {
        "OK"    { "Green" }
        "WARN"  { "Yellow" }
        "ERROR" { "Red" }
        default { "Cyan" }
    }
    Write-Host "[$Status] $Message" -ForegroundColor $color
}

# Create output directory
New-Item -ItemType Directory -Path $OutputPath -Force | Out-Null
Write-Status "Output directory: $OutputPath"

$DiagnosticData = @{
    ExportTimestamp = (Get-Date -Format "o")
    ComputerName = $env:COMPUTERNAME
    OSVersion = (Get-CimInstance Win32_OperatingSystem).Caption
    OSBuild = (Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion").DisplayVersion
    EventAgeFilter = "$MaxEventAge days"
    Logs = @{}
    Events = @{}
    SystemState = @{}
    Errors = @()
}

# 1. Generate and parse WindowsUpdate.log
Write-Status "Generating WindowsUpdate.log..."
$WULogPath = Join-Path $OutputPath "WindowsUpdate.log"
try {
    Get-WindowsUpdateLog -LogPath $WULogPath -ErrorAction Stop | Out-Null

    if (Test-Path $WULogPath) {
        $WULogContent = Get-Content $WULogPath -Raw
        $WULogLines = Get-Content $WULogPath | ForEach-Object {
            if ($_ -match '^(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2}\.\d+)\s+(\d+)\s+(\d+)\s+(\w+)\s+(.*)$') {
                @{
                    Timestamp = $Matches[1]
                    ProcessId = $Matches[2]
                    ThreadId = $Matches[3]
                    Component = $Matches[4]
                    Message = $Matches[5]
                    IsError = $_ -match '(error|fail|0x8|exception)' -and $_ -notmatch 'success'
                }
            }
        } | Where-Object { $_ }

        $DiagnosticData.Logs.WindowsUpdate = @{
            Path = $WULogPath
            LineCount = ($WULogContent -split "`n").Count
            ParsedEntries = $WULogLines | Select-Object -Last 500
            Errors = $WULogLines | Where-Object { $_.IsError } | Select-Object -Last 100
        }
        Write-Status "WindowsUpdate.log parsed" "OK"
    }
} catch {
    $DiagnosticData.Errors += "WindowsUpdate.log: $_"
    Write-Status "WindowsUpdate.log generation failed: $_" "WARN"
}

# 2. CBS.log
Write-Status "Parsing CBS.log..."
$CBSPath = "C:\Windows\Logs\CBS\CBS.log"
if (Test-Path $CBSPath) {
    try {
        Copy-Item $CBSPath (Join-Path $OutputPath "CBS.log") -Force
        $CBSContent = Get-Content $CBSPath -ErrorAction Stop
        $CBSParsed = $CBSContent | ForEach-Object {
            if ($_ -match '^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}),\s*(\w+)\s+(.*)$') {
                @{
                    Timestamp = $Matches[1]
                    Level = $Matches[2]
                    Message = $Matches[3]
                    IsError = $Matches[2] -eq 'Error' -or $_ -match '(CBS_E_|HRESULT|0x8)'
                }
            }
        } | Where-Object { $_ }

        $DiagnosticData.Logs.CBS = @{
            Path = $CBSPath
            LineCount = $CBSContent.Count
            ParsedEntries = $CBSParsed | Select-Object -Last 500
            Errors = $CBSParsed | Where-Object { $_.IsError } | Select-Object -Last 100
        }
        Write-Status "CBS.log parsed" "OK"
    } catch {
        $DiagnosticData.Errors += "CBS.log: $_"
        Write-Status "CBS.log parse failed: $_" "WARN"
    }
} else {
    Write-Status "CBS.log not found" "WARN"
}

# 3. DISM.log
Write-Status "Parsing DISM.log..."
$DISMPath = "C:\Windows\Logs\DISM\DISM.log"
if (Test-Path $DISMPath) {
    try {
        Copy-Item $DISMPath (Join-Path $OutputPath "DISM.log") -Force
        $DISMContent = Get-Content $DISMPath -ErrorAction Stop
        $DISMParsed = $DISMContent | ForEach-Object {
            if ($_ -match '^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}),\s*(\w+)\s+\[(\d+)\]\s*(.*)$') {
                @{
                    Timestamp = $Matches[1]
                    Level = $Matches[2]
                    ThreadId = $Matches[3]
                    Message = $Matches[4]
                    IsError = $Matches[2] -match 'Error|Warning' -or $_ -match '0x8'
                }
            }
        } | Where-Object { $_ }

        $DiagnosticData.Logs.DISM = @{
            Path = $DISMPath
            LineCount = $DISMContent.Count
            ParsedEntries = $DISMParsed | Select-Object -Last 300
            Errors = $DISMParsed | Where-Object { $_.IsError } | Select-Object -Last 50
        }
        Write-Status "DISM.log parsed" "OK"
    } catch {
        $DiagnosticData.Errors += "DISM.log: $_"
        Write-Status "DISM.log parse failed: $_" "WARN"
    }
} else {
    Write-Status "DISM.log not found" "WARN"
}

# 4. Setup logs (for feature updates)
Write-Status "Checking setup logs..."
$SetupLogs = @(
    "C:\Windows\Panther\setuperr.log",
    "C:\Windows\Panther\setupact.log",
    "C:\`$WINDOWS.~BT\Sources\Panther\setuperr.log"
)
$DiagnosticData.Logs.Setup = @{}
foreach ($log in $SetupLogs) {
    if (Test-Path $log) {
        $logName = Split-Path $log -Leaf
        try {
            $content = Get-Content $log -ErrorAction Stop | Select-Object -Last 200
            Copy-Item $log (Join-Path $OutputPath $logName) -Force -ErrorAction SilentlyContinue
            $DiagnosticData.Logs.Setup[$logName] = @{
                Path = $log
                LastLines = $content
                Errors = $content | Where-Object { $_ -match '(error|fail|0x8)' -and $_ -notmatch 'success' }
            }
            Write-Status "$logName found" "OK"
        } catch {
            $DiagnosticData.Errors += "${logName}: $_"
        }
    }
}

# 5. Event Logs
Write-Status "Exporting event logs..."
$EventLogQueries = @{
    WindowsUpdateClient = @{
        LogName = "Microsoft-Windows-WindowsUpdateClient/Operational"
        Description = "Windows Update client operations"
    }
    Setup = @{
        LogName = "Setup"
        Description = "Windows setup events"
    }
    System_WU = @{
        Filter = { $_.ProviderName -match 'WindowsUpdate|WUAU|TrustedInstaller|CBS' }
        LogName = "System"
        Description = "System events related to updates"
    }
    Application_WU = @{
        Filter = { $_.ProviderName -match 'MsiInstaller|WindowsUpdate' }
        LogName = "Application"
        Description = "Application events related to updates"
    }
}

foreach ($query in $EventLogQueries.GetEnumerator()) {
    try {
        $events = if ($query.Value.Filter) {
            Get-WinEvent -LogName $query.Value.LogName -ErrorAction Stop |
                Where-Object { $_.TimeCreated -ge $StartTime } |
                Where-Object $query.Value.Filter |
                Select-Object -First 200
        } else {
            Get-WinEvent -LogName $query.Value.LogName -MaxEvents 200 -ErrorAction Stop |
                Where-Object { $_.TimeCreated -ge $StartTime }
        }

        $DiagnosticData.Events[$query.Key] = @{
            Description = $query.Value.Description
            Count = $events.Count
            Events = $events | ForEach-Object {
                @{
                    TimeCreated = $_.TimeCreated.ToString("o")
                    Id = $_.Id
                    Level = $_.LevelDisplayName
                    Provider = $_.ProviderName
                    Message = $_.Message
                    IsError = $_.Level -le 2
                }
            }
            Errors = $events | Where-Object { $_.Level -le 2 } | ForEach-Object {
                @{
                    TimeCreated = $_.TimeCreated.ToString("o")
                    Id = $_.Id
                    Message = $_.Message
                }
            }
        }
        Write-Status "$($query.Key): $($events.Count) events" "OK"
    } catch {
        $DiagnosticData.Errors += "EventLog $($query.Key): $_"
        Write-Status "EventLog $($query.Key) failed: $_" "WARN"
    }
}

# 6. System State
Write-Status "Collecting system state..."

# Update history
try {
    $Session = New-Object -ComObject Microsoft.Update.Session
    $Searcher = $Session.CreateUpdateSearcher()
    $History = $Searcher.QueryHistory(0, 50)
    $DiagnosticData.SystemState.UpdateHistory = $History | ForEach-Object {
        @{
            Title = $_.Title
            Date = $_.Date.ToString("o")
            Operation = switch ($_.Operation) { 1 {"Install"} 2 {"Uninstall"} default {"Other"} }
            ResultCode = switch ($_.ResultCode) {
                0 {"NotStarted"} 1 {"InProgress"} 2 {"Succeeded"}
                3 {"SucceededWithErrors"} 4 {"Failed"} 5 {"Aborted"}
                default {"Unknown"}
            }
            HResult = "0x{0:X8}" -f $_.HResult
            UpdateId = $_.UpdateIdentity.UpdateID
            IsFailed = $_.ResultCode -ge 4
        }
    }
    $FailedUpdates = $DiagnosticData.SystemState.UpdateHistory | Where-Object { $_.IsFailed }
    Write-Status "Update history: $($History.Count) entries, $($FailedUpdates.Count) failed" "OK"
} catch {
    $DiagnosticData.Errors += "UpdateHistory: $_"
    Write-Status "Update history collection failed: $_" "WARN"
}

# Pending updates
try {
    $Searcher = (New-Object -ComObject Microsoft.Update.Session).CreateUpdateSearcher()
    $Pending = $Searcher.Search("IsInstalled=0 and Type='Software'")
    $DiagnosticData.SystemState.PendingUpdates = $Pending.Updates | ForEach-Object {
        @{
            Title = $_.Title
            KBArticleIDs = $_.KBArticleIDs -join ","
            MsrcSeverity = $_.MsrcSeverity
            IsMandatory = $_.IsMandatory
            IsDownloaded = $_.IsDownloaded
            RebootRequired = $_.RebootRequired
        }
    }
    Write-Status "Pending updates: $($Pending.Updates.Count)" "OK"
} catch {
    $DiagnosticData.Errors += "PendingUpdates: $_"
}

# Component store health
try {
    Write-Status "Checking component store health (this may take a minute)..."
    $DISMCheck = & DISM /Online /Cleanup-Image /CheckHealth 2>&1
    $DiagnosticData.SystemState.ComponentStoreHealth = @{
        Output = $DISMCheck -join "`n"
        IsHealthy = $DISMCheck -match 'No component store corruption detected|The component store is repairable'
    }
    Write-Status "Component store check complete" "OK"
} catch {
    $DiagnosticData.Errors += "ComponentStoreHealth: $_"
}

# Windows Update service state
try {
    $WUServices = Get-Service -Name wuauserv, bits, cryptsvc, msiserver -ErrorAction Stop
    $DiagnosticData.SystemState.Services = $WUServices | ForEach-Object {
        @{
            Name = $_.Name
            DisplayName = $_.DisplayName
            Status = $_.Status.ToString()
            StartType = $_.StartType.ToString()
        }
    }
    Write-Status "Service status collected" "OK"
} catch {
    $DiagnosticData.Errors += "Services: $_"
}

# Disk space
try {
    $SystemDrive = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'"
    $DiagnosticData.SystemState.DiskSpace = @{
        Drive = "C:"
        FreeGB = [math]::Round($SystemDrive.FreeSpace / 1GB, 2)
        TotalGB = [math]::Round($SystemDrive.Size / 1GB, 2)
        PercentFree = [math]::Round(($SystemDrive.FreeSpace / $SystemDrive.Size) * 100, 1)
        IsLow = ($SystemDrive.FreeSpace / 1GB) -lt 10
    }
    Write-Status "Disk space: $($DiagnosticData.SystemState.DiskSpace.FreeGB) GB free" "OK"
} catch {
    $DiagnosticData.Errors += "DiskSpace: $_"
}

# 7. Error Summary
Write-Status "Generating error summary..."
$AllErrors = @()

# Collect all errors from logs
if ($DiagnosticData.Logs.WindowsUpdate.Errors) {
    $AllErrors += $DiagnosticData.Logs.WindowsUpdate.Errors | ForEach-Object {
        @{ Source = "WindowsUpdate.log"; Timestamp = $_.Timestamp; Message = $_.Message }
    }
}
if ($DiagnosticData.Logs.CBS.Errors) {
    $AllErrors += $DiagnosticData.Logs.CBS.Errors | ForEach-Object {
        @{ Source = "CBS.log"; Timestamp = $_.Timestamp; Message = $_.Message }
    }
}

# Extract unique error codes
$ErrorCodes = @()
$AllErrors | ForEach-Object {
    if ($_.Message -match '(0x[0-9A-Fa-f]{8})') {
        $ErrorCodes += $Matches[1]
    }
    if ($_.Message -match '(CBS_E_\w+)') {
        $ErrorCodes += $Matches[1]
    }
}

$DiagnosticData.Summary = @{
    TotalErrors = $AllErrors.Count
    UniqueErrorCodes = ($ErrorCodes | Select-Object -Unique)
    FailedUpdates = @($DiagnosticData.SystemState.UpdateHistory | Where-Object { $_.IsFailed })
    CollectionErrors = $DiagnosticData.Errors
    RecommendedActions = @()
}

# Add recommendations based on findings
if ($DiagnosticData.SystemState.DiskSpace.IsLow) {
    $DiagnosticData.Summary.RecommendedActions += "LOW DISK SPACE: Free up space on C: drive"
}
if ($DiagnosticData.SystemState.ComponentStoreHealth -and -not $DiagnosticData.SystemState.ComponentStoreHealth.IsHealthy) {
    $DiagnosticData.Summary.RecommendedActions += "COMPONENT STORE: Run 'DISM /Online /Cleanup-Image /RestoreHealth'"
}
if ($DiagnosticData.Summary.UniqueErrorCodes -contains '0x80070005') {
    $DiagnosticData.Summary.RecommendedActions += "ACCESS DENIED: Check Windows Update service permissions"
}
if ($DiagnosticData.Summary.UniqueErrorCodes | Where-Object { $_ -match '0x8024' }) {
    $DiagnosticData.Summary.RecommendedActions += "WU AGENT ERROR: Consider running Windows Update troubleshooter"
}

# 8. Export to JSON
$JsonPath = Join-Path $OutputPath "WUDiagnostics.json"
$DiagnosticData | ConvertTo-Json -Depth 10 -Compress:$false | Out-File $JsonPath -Encoding UTF8
Write-Status "JSON export: $JsonPath" "OK"

# 9. Create analysis-ready CSV of errors
$ErrorCsvPath = Join-Path $OutputPath "Errors.csv"
$AllErrors | Export-Csv $ErrorCsvPath -NoTypeInformation
Write-Status "Error CSV: $ErrorCsvPath" "OK"

# 10. Final summary
Write-Host "`n" + "="*60 -ForegroundColor Cyan
Write-Host "EXPORT COMPLETE" -ForegroundColor Green
Write-Host "="*60 -ForegroundColor Cyan
Write-Host "Output: $OutputPath"
Write-Host "Main file: WUDiagnostics.json"
Write-Host "`nSummary:"
Write-Host "  - Total errors found: $($DiagnosticData.Summary.TotalErrors)"
Write-Host "  - Unique error codes: $($DiagnosticData.Summary.UniqueErrorCodes.Count)"
Write-Host "  - Failed updates: $($DiagnosticData.Summary.FailedUpdates.Count)"
Write-Host "  - Collection errors: $($DiagnosticData.Errors.Count)"

if ($DiagnosticData.Summary.RecommendedActions.Count -gt 0) {
    Write-Host "`nRecommended Actions:" -ForegroundColor Yellow
    $DiagnosticData.Summary.RecommendedActions | ForEach-Object { Write-Host "  - $_" }
}

Write-Host "`nTo analyze, provide the WUDiagnostics.json file for parsing." -ForegroundColor Cyan

# Return path for automation
return $OutputPath
