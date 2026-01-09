# Azure VM Idle Shutdown Runbook v1.0
# Purpose: Stop VMs that are idle (low CPU, network, disk activity)
# Trigger: Azure Monitor Alert via webhook

param(
    [Parameter(Mandatory=$false)]
    [object]$WebhookData
)

# Configuration
$IDLE_THRESHOLD_CPU = 5          # Percentage CPU
$IDLE_THRESHOLD_NETWORK = 102400 # Bytes (100 KB)
$IDLE_THRESHOLD_DISK = 1         # Operations/sec
$CHECK_PERIOD_MINUTES = 30       # How long to check for idle state

# Authenticate using Managed Identity
try {
    Write-Output "Connecting to Azure with Managed Identity..."
    Connect-AzAccount -Identity -ErrorAction Stop
    Write-Output "✅ Successfully authenticated"
} catch {
    Write-Error "❌ Failed to authenticate: $_"
    exit 1
}

# Parse webhook data if provided
if ($WebhookData) {
    $WebhookBody = ConvertFrom-Json -InputObject $WebhookData.RequestBody
    $AlertContext = $WebhookBody.data.context

    # Extract VM details from alert
    $ResourceId = $AlertContext.resourceId
    $ResourceGroup = $ResourceId.Split('/')[4]
    $VMName = $ResourceId.Split('/')[-1]

    Write-Output "Alert triggered for VM: $VMName in RG: $ResourceGroup"
} else {
    # Manual execution - sandbox environment defaults
    Write-Output "Manual execution - using sandbox VM"
    $ResourceGroup = "DEV-RG"
    $VMName = "win11-vscode"
}

# Get VM status
try {
    $VM = Get-AzVM -ResourceGroupName $ResourceGroup -Name $VMName -Status -ErrorAction Stop
    $PowerState = ($VM.Statuses | Where-Object {$_.Code -like "PowerState/*"}).Code

    Write-Output "Current VM state: $PowerState"

    if ($PowerState -ne "PowerState/running") {
        Write-Output "VM is not running - skipping shutdown"
        exit 0
    }
} catch {
    Write-Error "❌ Failed to get VM status: $_"
    exit 1
}

# Check recent metrics to confirm idle state
try {
    Write-Output "Checking metrics for last $CHECK_PERIOD_MINUTES minutes..."

    $EndTime = Get-Date
    $StartTime = $EndTime.AddMinutes(-$CHECK_PERIOD_MINUTES)
    $ResourceId = "/subscriptions/$((Get-AzContext).Subscription.Id)/resourceGroups/$ResourceGroup/providers/Microsoft.Compute/virtualMachines/$VMName"

    # Check CPU
    $CpuMetric = Get-AzMetric -ResourceId $ResourceId `
        -MetricName "Percentage CPU" `
        -StartTime $StartTime `
        -EndTime $EndTime `
        -TimeGrain 00:05:00 `
        -WarningAction SilentlyContinue

    $AvgCpu = ($CpuMetric.Data | Where-Object {$_.Average -ne $null} | Measure-Object -Property Average -Average).Average

    Write-Output "Average CPU: $([math]::Round($AvgCpu, 2))%"

    # Check Network In
    $NetworkMetric = Get-AzMetric -ResourceId $ResourceId `
        -MetricName "Network In Total" `
        -StartTime $StartTime `
        -EndTime $EndTime `
        -TimeGrain 00:05:00 `
        -WarningAction SilentlyContinue

    $AvgNetwork = ($NetworkMetric.Data | Where-Object {$_.Average -ne $null} | Measure-Object -Property Average -Average).Average

    Write-Output "Average Network In: $([math]::Round($AvgNetwork, 2)) bytes"

    # Determine if VM is idle
    $IsIdle = ($AvgCpu -lt $IDLE_THRESHOLD_CPU) -and ($AvgNetwork -lt $IDLE_THRESHOLD_NETWORK)

    if ($IsIdle) {
        Write-Output "🔴 VM is IDLE - proceeding with shutdown"
        Write-Output "  - CPU: $([math]::Round($AvgCpu, 2))% (threshold: $IDLE_THRESHOLD_CPU%)"
        Write-Output "  - Network: $([math]::Round($AvgNetwork, 2)) bytes (threshold: $IDLE_THRESHOLD_NETWORK bytes)"

        # Stop the VM (deallocate to save costs)
        Write-Output "Stopping VM: $VMName..."
        Stop-AzVM -ResourceGroupName $ResourceGroup -Name $VMName -Force -NoWait

        Write-Output "✅ Shutdown command issued successfully"
        Write-Output "VM will be deallocated (no compute charges)"

    } else {
        Write-Output "🟢 VM is ACTIVE - no action needed"
        Write-Output "  - CPU: $([math]::Round($AvgCpu, 2))% (threshold: $IDLE_THRESHOLD_CPU%)"
        Write-Output "  - Network: $([math]::Round($AvgNetwork, 2)) bytes (threshold: $IDLE_THRESHOLD_NETWORK bytes)"
    }

} catch {
    Write-Error "❌ Failed to check metrics or stop VM: $_"
    Write-Error $_.Exception.Message
    exit 1
}

Write-Output "Runbook execution complete"
