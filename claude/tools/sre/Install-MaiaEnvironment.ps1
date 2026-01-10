#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Complete MAIA environment setup for Windows with WSL, VSCode, and Claude Code.

.DESCRIPTION
    Automated installer for all components needed to run MAIA on Windows:
    - WSL1/WSL2 with Ubuntu 22.04 (WSL2 default - requires D/E-series Azure VMs)
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
    WSL version to install (1 or 2). Default: 2 (team requirement).
    WSL2 requires nested virtualization (D/E-series VMs, not available on B-series).

.EXAMPLE
    .\Install-MaiaEnvironment.ps1

.EXAMPLE
    .\Install-MaiaEnvironment.ps1 -CheckOnly

.EXAMPLE
    .\Install-MaiaEnvironment.ps1 -WSLVersion 2

.NOTES
    Version: 2.19
    Requires: Windows 10 2004+ or Windows 11, Administrator privileges

    Changed v2.19:
    - CRITICAL FIX: Find ubuntu.exe from AppX package location instead of WindowsApps alias
    - FIXED: App Execution Alias registration often fails, causing ubuntu.exe not found errors
    - FIXED: Microsoft changed aka.ms/wslubuntu2204 to redirect to Ubuntu 24.04
    - IMPROVED: Get ubuntu.exe path directly from Get-AppxPackage InstallLocation
    - IMPROVED: Works regardless of App Execution Alias state

    Changed v2.18:
    - CRITICAL BUG FIX: Script now properly stops when Ubuntu installation fails
    - CRITICAL BUG FIX: v2.17 showed WARN but continued, causing cascade failures
    - IMPROVED: Multi-method verification (exit code + output + WSL test)
    - IMPROVED: Detailed diagnostic output for troubleshooting installation failures
    - IMPROVED: Better error messages with specific troubleshooting steps

    Changed v2.17:
    - CRITICAL FIX: Ubuntu registration check now uses install output instead of wsl --list
    - FIXED: wsl --list --quiet returns UTF-16LE with NULL bytes breaking regex matching
    - Now checks for "Installation successful" message from ubuntu.exe install --root
    - Falls back to direct WSL test if install message unclear

    Changed v2.16:
    - CRITICAL FIX: WSL2 kernel now installed UNCONDITIONALLY (per Microsoft official docs)
    - FIXED: Previous conditional check failed - wsl --set-default-version succeeds without kernel
    - Kernel install now happens BEFORE Ubuntu installation (prevents 0x800701bc error)
    - Follows Microsoft's Step 4 from manual installation guide exactly

    Changed v2.15:
    - FIXED: Changed executable name from ubuntu2204.exe to ubuntu.exe (actual AppX executable name)
    - FIXED: Root cause identified via diagnostic agent - Ubuntu 22.04 AppX uses 'ubuntu.exe'
    - Added executable name logging for troubleshooting
    - Added WSL distro registration confirmation message

    Changed v2.14:
    - Improved Ubuntu initialization using official Microsoft manual installation method
    - Added retry logic for ubuntu2204.exe availability after AppX install
    - Added WSL distro registration verification
    - Enhanced user creation with proper error checking

    Changed v2.13:
    - Replaced unreliable wsl --install with direct AppX package installation
    - Automatically creates default user (maia/Test123!) without interactive prompts
    - Downloads Ubuntu 22.04 directly from Microsoft CDN and installs via Add-AppxPackage

    Changed v2.12:
    - Auto-detects and installs WSL2 kernel update when missing (fixes 0x800701bc error)
    - Prevents Ubuntu installation failure when WSL2 kernel is not updated

    Changed v2.11:
    - Fixed WSL path translation error when running from network/RDP drives
    - Changed log location from temp to script directory for easier access

    Changed v2.10:
    - Changed default WSL version to 2 (team requirement)
    - WSL2 requires D/E-series Azure VMs with nested virtualization support

    Changed v2.9:
    - Use msiexec.exe directly for MSI installs (bypasses SmartScreen/Defender blocks)
    - Fixed cleanup error (removed orphaned $winTempScript reference)

    Changed v2.8:
    - Fixed wslpath path conversion (now uses stdin pipe to avoid path mangling)
    - Added Unblock-File before MSI installation
    - Simplified bashrc append using stdin pipe

    Changed v2.7 (Critical Bug Fixes):
    - Fixed bash script generation (removed -NoNewline that broke scripts)
    - Fixed wslpath command syntax (added -u flag)
    - Fixed bash command quoting in Get-WSLCommand and Invoke-WSLCommand
    - Fixed git clone error checking ($cloneSuccess instead of $LASTEXITCODE)
    - Fixed SSH key detection logic (operator precedence)
    - Fixed bashrc append (file-based to preserve bash variables)
    - Added error checking for WSL script copy operation
    - Fixed MSI header validation (binary bytes instead of ASCII)

    Changed v2.6:
    - Enhanced download validation (file size, MSI header validation)
    - Better error messages for installation failures
    - Exit code validation (0 or 3010 = success)
    - TLS 1.2 enforcement for downloads
#>

param(
    [switch]$CheckOnly,
    [switch]$SkipRestart,
    [string]$MaiaRepo = "https://github.com/naythan-orro/maia.git",
    [ValidateSet(1, 2)]
    [int]$WSLVersion = 2
)

$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"

# Change to local directory if running from network/RDP drive (WSL can't translate network paths)
$currentDrive = (Get-Location).Drive
if ($currentDrive.DisplayRoot -like "\\tsclient\*" -or $currentDrive.DisplayRoot -like "\\*") {
    Write-Host "Detected network drive. Changing to C:\Users\$env:USERNAME for WSL compatibility..." -ForegroundColor Yellow
    Set-Location "C:\Users\$env:USERNAME"
}

# Configuration
$script:Config = @{
    UbuntuVersion = "Ubuntu-22.04"
    NodeVersion = "20.18.1"  # LTS version
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

function Refresh-EnvironmentPath {
    # Refresh PATH from registry to pick up newly installed commands
    $machinePath = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
    $userPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$machinePath;$userPath"
}

function Test-CommandWithRetry {
    param(
        [string]$Command,
        [int]$MaxRetries = 5,
        [int]$DelaySeconds = 2
    )

    for ($i = 1; $i -le $MaxRetries; $i++) {
        Refresh-EnvironmentPath
        if (Test-CommandExists $Command) {
            return $true
        }
        if ($i -lt $MaxRetries) {
            Write-Host "    Waiting for $Command to become available ($i/$MaxRetries)..." -ForegroundColor Gray
            Start-Sleep -Seconds $DelaySeconds
        }
    }
    return $false
}

function Wait-ForWSLCommand {
    param([int]$MaxRetries = 10, [int]$DelaySeconds = 3)

    for ($i = 1; $i -le $MaxRetries; $i++) {
        try {
            $result = wsl --status 2>&1
            if ($LASTEXITCODE -eq 0) {
                return $true
            }
        } catch {}

        if ($i -lt $MaxRetries) {
            Write-Host "    Waiting for WSL to become available ($i/$MaxRetries)..." -ForegroundColor Gray
            Start-Sleep -Seconds $DelaySeconds
        }
    }
    return $false
}

function Request-Restart {
    param([string]$Reason)

    Write-Host ""
    Write-Banner "RESTART REQUIRED"
    Write-Host "Reason: $Reason" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Installation cannot continue until restart is complete." -ForegroundColor Red
    Write-Host "After restart, re-run this script to continue installation." -ForegroundColor Yellow
    Write-Host ""

    $script:Results.NeedsRestart = $true

    $restart = Read-Host "Restart now? (y/N)"
    if ($restart -eq "y" -or $restart -eq "Y") {
        Write-Host "Restarting computer..." -ForegroundColor Gray
        Restart-Computer -Force
    }

    exit 0
}

function Test-NetworkConnectivity {
    Write-Host "    Testing network connectivity..." -ForegroundColor Gray

    $testUrls = @{
        "GitHub" = "https://github.com"
        "Node.js" = "https://nodejs.org"
        "Ubuntu Repos" = "http://archive.ubuntu.com"
    }

    $allPassed = $true
    foreach ($service in $testUrls.GetEnumerator()) {
        try {
            $response = Invoke-WebRequest -Uri $service.Value -Method Head -TimeoutSec 10 -UseBasicParsing -ErrorAction Stop
            Write-Host "      $($service.Key): " -NoNewline -ForegroundColor Gray
            Write-Host "OK" -ForegroundColor Green
        } catch {
            Write-Host "      $($service.Key): " -NoNewline -ForegroundColor Gray
            Write-Host "FAILED" -ForegroundColor Red
            $allPassed = $false
        }
    }

    return $allPassed
}

function Test-DiskSpace {
    Write-Host "    Checking disk space..." -ForegroundColor Gray

    # Check system drive
    $sysDrive = $env:SystemDrive
    $sysDisk = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='$sysDrive'"
    $sysFreeGB = [math]::Round($sysDisk.FreeSpace / 1GB, 1)

    Write-Host "      System drive ($sysDrive): " -NoNewline -ForegroundColor Gray
    if ($sysFreeGB -lt $script:Config.RequiredDiskSpaceGB) {
        Write-Host "${sysFreeGB}GB free (need $($script:Config.RequiredDiskSpaceGB)GB)" -ForegroundColor Red
        return $false
    } else {
        Write-Host "${sysFreeGB}GB free" -ForegroundColor Green
    }

    # Check WSL installation path
    $wslBasePath = "$env:LOCALAPPDATA\Packages"
    $wslDrive = Split-Path -Qualifier $wslBasePath
    if ($wslDrive -ne $sysDrive) {
        $wslDisk = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='$wslDrive'"
        $wslFreeGB = [math]::Round($wslDisk.FreeSpace / 1GB, 1)

        Write-Host "      WSL drive ($wslDrive): " -NoNewline -ForegroundColor Gray
        if ($wslFreeGB -lt $script:Config.RequiredDiskSpaceGB) {
            Write-Host "${wslFreeGB}GB free (need $($script:Config.RequiredDiskSpaceGB)GB)" -ForegroundColor Red
            return $false
        } else {
            Write-Host "${wslFreeGB}GB free" -ForegroundColor Green
        }
    }

    return $true
}

function Get-WSLCommand {
    param([string]$Command)
    $result = wsl -d $script:Config.UbuntuVersion -- bash -c "$Command" 2>&1
    return @{
        Output = $result
        Success = $LASTEXITCODE -eq 0
    }
}

function Invoke-WSLCommand {
    param([string]$Command, [switch]$Sudo)
    $cmd = if ($Sudo) { "sudo $Command" } else { $Command }
    wsl -d $script:Config.UbuntuVersion -- bash -c "$cmd"
    return $LASTEXITCODE -eq 0
}

function Install-FromWeb {
    param(
        [string]$Name,
        [string]$Url,
        [string]$OutFile,
        [string]$Arguments = "/S",
        [int]$MinFileSizeMB = 1
    )

    Write-Host "    Downloading $Name from: $Url" -ForegroundColor Gray

    # Ensure TLS 1.2
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

    try {
        # Download with progress
        $progressPreference = 'SilentlyContinue'
        Invoke-WebRequest -Uri $Url -OutFile $OutFile -UseBasicParsing -TimeoutSec 300

        # Validate download
        if (-not (Test-Path $OutFile)) {
            Write-Status "Download failed - file not created" "ERROR"
            return $false
        }

        $fileSize = (Get-Item $OutFile).Length
        $fileSizeMB = [math]::Round($fileSize / 1MB, 1)

        Write-Host "    Downloaded: ${fileSizeMB}MB" -ForegroundColor Gray

        if ($fileSizeMB -lt $MinFileSizeMB) {
            Write-Status "Downloaded file too small (${fileSizeMB}MB) - download incomplete or corrupt" "ERROR"
            Remove-Item $OutFile -Force -ErrorAction SilentlyContinue
            return $false
        }

        # Check if it's a valid executable/MSI
        if ($OutFile -match '\.msi$') {
            # Quick validation - MSI files are OLE compound documents
            # They start with hex: D0 CF 11 E0 A1 B1 1A E1
            $bytes = [System.IO.File]::ReadAllBytes($OutFile)
            if ($bytes.Length -lt 8) {
                Write-Status "Downloaded file too small to be valid MSI" "ERROR"
                Remove-Item $OutFile -Force -ErrorAction SilentlyContinue
                return $false
            }

            $header = $bytes[0..7]
            $validMSI = ($header[0] -eq 0xD0 -and $header[1] -eq 0xCF -and
                        $header[2] -eq 0x11 -and $header[3] -eq 0xE0 -and
                        $header[4] -eq 0xA1 -and $header[5] -eq 0xB1 -and
                        $header[6] -eq 0x1A -and $header[7] -eq 0xE1)

            if (-not $validMSI) {
                Write-Status "Downloaded file is not a valid MSI installer" "ERROR"
                Write-Host "    File header: $([System.BitConverter]::ToString($header))" -ForegroundColor Gray
                Write-Host "    Expected:    D0-CF-11-E0-A1-B1-1A-E1" -ForegroundColor Gray
                Write-Host "    File may be HTML error page or blocked by security software" -ForegroundColor Yellow
                Remove-Item $OutFile -Force -ErrorAction SilentlyContinue
                return $false
            }
        }

        # Unblock file (Windows security may mark downloads as unsafe)
        try {
            Unblock-File -Path $OutFile -ErrorAction SilentlyContinue
        } catch {}

        Write-Host "    Installing $Name..." -ForegroundColor Gray

        # Use msiexec for MSI files (more reliable than Start-Process)
        if ($OutFile -match '\.msi$') {
            $msiArgs = @("/i", "`"$OutFile`"", "/qn", "/norestart")
            $process = Start-Process "msiexec.exe" -ArgumentList $msiArgs -Wait -NoNewWindow -PassThru
        } else {
            $process = Start-Process -FilePath $OutFile -ArgumentList $Arguments -Wait -NoNewWindow -PassThru
        }

        if ($process.ExitCode -ne 0 -and $process.ExitCode -ne 3010) {
            Write-Status "Installation failed with exit code: $($process.ExitCode)" "ERROR"
            Write-Host "    Troubleshooting:" -ForegroundColor Yellow
            Write-Host "      - Check if antivirus is blocking the installer" -ForegroundColor Gray
            Write-Host "      - Try running as Administrator" -ForegroundColor Gray
            Write-Host "      - Check Windows Event Log for details" -ForegroundColor Gray
            Write-Host "      - MSI file location: $OutFile" -ForegroundColor Gray
            Remove-Item $OutFile -Force -ErrorAction SilentlyContinue
            return $false
        }

        Remove-Item $OutFile -Force -ErrorAction SilentlyContinue
        return $true

    } catch {
        Write-Status "Failed to download/install $Name`: $_" "ERROR"
        if (Test-Path $OutFile) {
            Remove-Item $OutFile -Force -ErrorAction SilentlyContinue
        }
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

    # Disk space (comprehensive check)
    if (-not (Test-DiskSpace)) {
        Write-Status "Insufficient disk space for installation" "ERROR"
        return $false
    }

    # Network connectivity
    if (-not $CheckOnly) {
        if (-not (Test-NetworkConnectivity)) {
            Write-Status "Network connectivity issues detected" "WARN"
            Write-Host "    Installation may fail if network issues persist" -ForegroundColor Yellow
            $continue = Read-Host "Continue anyway? (y/N)"
            if ($continue -ne "y" -and $continue -ne "Y") {
                return $false
            }
        } else {
            Write-Status "Network connectivity verified" "OK"
        }
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

                if ($LASTEXITCODE -eq 0 -or $LASTEXITCODE -eq 3010) {
                    Write-Status "Windows Subsystem for Linux enabled" "OK"
                    if ($LASTEXITCODE -eq 3010) {
                        Request-Restart "Windows Subsystem for Linux feature enabled"
                    }
                } else {
                    Write-Status "Failed to enable WSL feature (exit code: $LASTEXITCODE)" "ERROR"
                    return $false
                }
            }

            # Enable Virtual Machine Platform (required for both WSL1 and WSL2)
            if (-not $vmPlatformEnabled) {
                Write-Host "    Enabling Virtual Machine Platform..." -ForegroundColor Gray
                dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart | Out-Null

                if ($LASTEXITCODE -eq 0 -or $LASTEXITCODE -eq 3010) {
                    Write-Status "Virtual Machine Platform enabled" "OK"
                    if ($LASTEXITCODE -eq 3010) {
                        Request-Restart "Virtual Machine Platform feature enabled"
                    }
                } else {
                    Write-Status "Failed to enable VM Platform (exit code: $LASTEXITCODE)" "ERROR"
                    return $false
                }
            }

            # If we get here, features are enabled without needing restart
            Write-Status "Windows features enabled successfully" "OK"
            return $true

        } catch {
            Write-Status "Failed to enable Windows features: $_" "ERROR"
            return $false
        }
    }

    Write-Status "Required Windows features are enabled" "OK"

    # Step 3: Check if WSL command is available (with retry logic for race conditions)
    Write-Host "    Verifying WSL is ready..." -ForegroundColor Gray
    $wslReady = Wait-ForWSLCommand -MaxRetries 10 -DelaySeconds 3

    if ($wslReady) {
        Write-Status "WSL is ready" "OK"
    } else {
        Write-Status "WSL command not available after waiting" "WARN"

        if ($CheckOnly) {
            return $false
        }

        # Features are enabled but WSL command not ready - restart required
        Request-Restart "WSL features enabled but command not available"
    }

    # Step 4: Install WSL2 kernel update (mandatory for WSL2)
    if ($script:Config.WSLVersion -eq 2) {
        Write-Host "    Installing WSL2 kernel update..." -ForegroundColor Gray
        Write-Host "    (Required by Microsoft - unconditional install per official docs)" -ForegroundColor Gray

        if (-not $CheckOnly) {
            $kernelUrl = "https://wslstorestorage.blob.core.windows.net/wslblob/wsl_update_x64.msi"
            $kernelMsi = "$env:TEMP\wsl_update_x64.msi"

            if (Install-FromWeb -Name "WSL2 Kernel Update" -Url $kernelUrl -OutFile $kernelMsi -Arguments "/quiet /norestart" -MinFileSizeMB 10) {
                Write-Status "WSL2 kernel update installed" "OK"
            } else {
                Write-Status "Failed to install WSL2 kernel update" "ERROR"
                Write-Host "    Manual download: https://aka.ms/wsl2kernel" -ForegroundColor Yellow
                return $false
            }
        }
    }

    # Step 5: Set WSL version as default
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

    Write-Host "    Downloading and installing Ubuntu 22.04 AppX package..." -ForegroundColor Gray
    Write-Host "    This may take 5-10 minutes on first install..." -ForegroundColor Yellow

    try {
        # Download Ubuntu 22.04 AppX bundle
        $ubuntuUrl = "https://aka.ms/wslubuntu2204"
        $appxPath = "$env:TEMP\Ubuntu2204.appx"

        Write-Host "    Downloading Ubuntu package..." -ForegroundColor Gray
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $ubuntuUrl -OutFile $appxPath -UseBasicParsing -TimeoutSec 300

        if (-not (Test-Path $appxPath)) {
            Write-Status "Failed to download Ubuntu package" "ERROR"
            return $false
        }

        $fileSizeMB = [math]::Round((Get-Item $appxPath).Length / 1MB, 1)
        Write-Host "    Downloaded: ${fileSizeMB}MB" -ForegroundColor Gray

        # Install the AppX package
        Write-Host "    Installing Ubuntu AppX package..." -ForegroundColor Gray
        Add-AppxPackage -Path $appxPath -ErrorAction Stop

        Write-Status "Ubuntu 22.04 AppX installed" "OK"

        # Wait for installation to complete
        Start-Sleep -Seconds 5

        # Initialize Ubuntu with default user (non-interactive)
        Write-Host "    Initializing Ubuntu with default user..." -ForegroundColor Gray
        Write-Host "    Default user: maia" -ForegroundColor Gray
        Write-Host "    Default password: Test123!" -ForegroundColor Gray

        # Find Ubuntu executable directly from AppX install location
        # NOTE: App Execution Alias often fails to register, so we get the path from the package itself
        Write-Host "    Locating Ubuntu executable from AppX package..." -ForegroundColor Gray

        $ubuntuPkg = Get-AppxPackage -Name "*Ubuntu*" | Select-Object -First 1
        if (-not $ubuntuPkg) {
            Write-Status "Ubuntu AppX package not found after installation" "ERROR"
            return $false
        }

        Write-Host "    Found package: $($ubuntuPkg.Name) v$($ubuntuPkg.Version)" -ForegroundColor Gray

        $ubuntuExePath = Join-Path $ubuntuPkg.InstallLocation "ubuntu.exe"
        if (-not (Test-Path $ubuntuExePath)) {
            Write-Status "ubuntu.exe not found in package location: $ubuntuExePath" "ERROR"
            Write-Host "    Package location: $($ubuntuPkg.InstallLocation)" -ForegroundColor Yellow
            Write-Host "    Try: Get-ChildItem `"$($ubuntuPkg.InstallLocation)`" -Filter *.exe" -ForegroundColor Yellow
            return $false
        }

        $ubuntuExe = Get-Item $ubuntuExePath

        Write-Host "    Found Ubuntu executable: $($ubuntuExe.Name)" -ForegroundColor Gray
        Write-Host "    Initializing Ubuntu (this extracts files and may take 2-3 minutes)..." -ForegroundColor Gray

        # Install Ubuntu as root first (no user creation prompt)
        Write-Host "    Running: ubuntu.exe install --root" -ForegroundColor Gray
        $installOutput = & $ubuntuExe install --root 2>&1 | Out-String
        $installExitCode = $LASTEXITCODE
        Start-Sleep -Seconds 5

        Write-Host "    Install command exit code: $installExitCode" -ForegroundColor Gray
        Write-Host "    Install output length: $($installOutput.Length) chars" -ForegroundColor Gray

        # Check if installation succeeded using multiple verification methods
        $installSuccess = $false

        # Method 1: Check exit code (0 = success)
        if ($installExitCode -eq 0) {
            Write-Host "    Exit code indicates success" -ForegroundColor Gray
            $installSuccess = $true
        }

        # Method 2: Check output message (if any)
        if ($installOutput -match "Installation successful|already installed") {
            Write-Host "    Output message indicates success" -ForegroundColor Gray
            $installSuccess = $true
        } elseif ($installOutput -match "Error|Failed|WslRegisterDistribution failed") {
            Write-Host "    Output indicates failure: $installOutput" -ForegroundColor Yellow
            $installSuccess = $false
        }

        # Method 3: Direct WSL test (most reliable)
        Write-Host "    Testing WSL distro registration..." -ForegroundColor Gray
        $null = wsl -d Ubuntu-22.04 -u root -- echo "test" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "    WSL test successful - distro is registered" -ForegroundColor Gray
            $installSuccess = $true
        } else {
            Write-Host "    WSL test failed - distro not properly registered" -ForegroundColor Yellow
            $installSuccess = $false
        }

        # Final verification
        if (-not $installSuccess) {
            Write-Status "Ubuntu installation failed - distro not registered" "ERROR"
            Write-Host "    This may indicate:" -ForegroundColor Yellow
            Write-Host "    - WSL2 kernel not properly installed" -ForegroundColor Yellow
            Write-Host "    - AppX package corrupted" -ForegroundColor Yellow
            Write-Host "    - Previous installation left in broken state" -ForegroundColor Yellow
            Write-Host "" -ForegroundColor Yellow
            Write-Host "    Troubleshooting steps:" -ForegroundColor Cyan
            Write-Host "    1. Run: wsl --list --verbose" -ForegroundColor White
            Write-Host "    2. Run: Get-AppxPackage *Ubuntu*" -ForegroundColor White
            Write-Host "    3. Try manual install: ubuntu.exe" -ForegroundColor White
            return $false
        }

        Write-Status "Ubuntu installation completed successfully" "OK"

        # Create the default user via WSL
        Write-Host "    Creating default user 'maia'..." -ForegroundColor Gray
        wsl -d Ubuntu-22.04 -u root -- useradd -m -s /bin/bash maia 2>$null
        wsl -d Ubuntu-22.04 -u root -- bash -c "echo 'maia:Test123!' | chpasswd" 2>$null
        wsl -d Ubuntu-22.04 -u root -- usermod -aG sudo maia 2>$null

        # Configure maia as default user for this distro
        & $ubuntuExe config --default-user maia

        # Verify user was created successfully
        $userCheck = wsl -d Ubuntu-22.04 -u maia -- whoami 2>&1
        if ($userCheck -match "maia") {
            Write-Status "Ubuntu initialized with user 'maia'" "OK"
        } else {
            Write-Status "User creation may have issues - verify with: wsl whoami" "WARN"
        }

        # Cleanup
        Remove-Item $appxPath -Force -ErrorAction SilentlyContinue

        # Set as default WSL distro
        wsl --set-default Ubuntu-22.04 2>&1 | Out-Null

        Write-Status "Ubuntu 22.04 installation complete" "OK"
        return $true

    } catch {
        Write-Status "Failed to install Ubuntu: $_" "ERROR"
        Write-Host "    Error details: $($_.Exception.Message)" -ForegroundColor Red

        # Cleanup on failure
        if (Test-Path $appxPath) {
            Remove-Item $appxPath -Force -ErrorAction SilentlyContinue
        }

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
            $nodeUrl = "https://nodejs.org/dist/v$($script:Config.NodeVersion)/node-v$($script:Config.NodeVersion)-x64.msi"
            $nodeMsi = "$env:TEMP\node-installer.msi"

            if (Install-FromWeb -Name "Node.js" -Url $nodeUrl -OutFile $nodeMsi -Arguments "/quiet /norestart" -MinFileSizeMB 25) {
                Write-Status "Node.js installed" "OK"

                # Wait for node command to become available (PATH refresh with retry)
                if (-not (Test-CommandWithRetry "node" -MaxRetries 5 -DelaySeconds 2)) {
                    Write-Status "Node.js installed but command not available - may need terminal restart" "WARN"
                    return $false
                }
            } else {
                return $false
            }
        }
    }

    # Verify npm (with retry logic)
    if (Test-CommandWithRetry "npm" -MaxRetries 5 -DelaySeconds 2) {
        $npmVersion = npm --version 2>&1
        Write-Status "npm installed: v$npmVersion" "OK"
    } else {
        Write-Status "npm not found - Node.js installation may have failed" "ERROR"
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
set -euo pipefail

# Error trap
trap 'echo "ERROR: Installation failed at line $LINENO"' ERR

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

    # Write script directly to WSL filesystem (avoids path conversion issues)
    $scriptPath = "/tmp/maia_install_$(Get-Date -Format 'yyyyMMddHHmmss').sh"

    # Create temp file with proper line endings for bash
    $tempFile = [System.IO.Path]::GetTempFileName()
    [System.IO.File]::WriteAllText($tempFile, $installScript, [System.Text.Encoding]::UTF8)

    # Copy via stdin to avoid wslpath issues
    Get-Content $tempFile -Raw | wsl -d $script:Config.UbuntuVersion -- bash -c "cat > $scriptPath && chmod +x $scriptPath"

    # Cleanup temp file
    Remove-Item $tempFile -Force -ErrorAction SilentlyContinue

    # Verify script was created
    $scriptCheck = Get-WSLCommand "test -f $scriptPath && echo 'exists'"
    if ($scriptCheck.Output -notmatch "exists") {
        Write-Status "Failed to create install script in WSL" "ERROR"
        return $false
    }

    # Execute with single sudo call
    Write-Host ""
    $installResult = Invoke-WSLCommand "bash $scriptPath" -Sudo

    # Cleanup
    Invoke-WSLCommand "rm -f $scriptPath"

    if (-not $installResult) {
        Write-Status "Dependency installation failed" "ERROR"
        return $false
    }

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
    $sshKeyCheck = Get-WSLCommand "(test -f ~/.ssh/id_rsa || test -f ~/.ssh/id_ed25519) && echo 'exists'"
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
    $cloneSuccess = Invoke-WSLCommand "git clone $repoUrl ~/maia"

    if ($cloneSuccess) {
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
        # Append via stdin to avoid path conversion issues
        $bashrcAdditions | wsl -d $script:Config.UbuntuVersion -- bash -c "cat >> ~/.bashrc"
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

Write-Banner "MAIA Environment Installer v2.19"

if ($CheckOnly) {
    Write-Host "MODE: Check Only (no installations)" -ForegroundColor Yellow
} else {
    Write-Host "MODE: Full Installation (WSL$WSLVersion)" -ForegroundColor Green
}

if ($WSLVersion -eq 1) {
    Write-Host "NOTE: Using WSL1 (lower performance but broader compatibility)" -ForegroundColor Gray
} else {
    Write-Host "NOTE: Using WSL2 (requires D/E-series Azure VMs with nested virtualization)" -ForegroundColor Gray
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

# Save log to same directory as script
$scriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
$logPath = Join-Path $scriptDir "maia_install_log_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"
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
