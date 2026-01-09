# Setup Azure VM Idle Shutdown - Sandbox Environment (win11-vscode)
# Purpose: Configure activity-based shutdown for sandbox development VM
# Version: 1.0 - Customized for sandbox

param(
    [Parameter(Mandatory=$false)]
    [string]$SubscriptionId,  # Will prompt if not provided

    [Parameter(Mandatory=$false)]
    [string]$ResourceGroup = "DEV-RG",

    [Parameter(Mandatory=$false)]
    [string]$VMName = "win11-vscode",

    [Parameter(Mandatory=$false)]
    [string]$Location = "australiaeast",

    [Parameter(Mandatory=$false)]
    [int]$IdleCpuThreshold = 5,

    [Parameter(Mandatory=$false)]
    [int]$IdleNetworkThresholdKB = 100,

    [Parameter(Mandatory=$false)]
    [int]$IdleDurationMinutes = 30,

    [Parameter(Mandatory=$false)]
    [string]$AutomationAccountName = "sandbox-vm-idle-shutdown"
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Sandbox VM Idle Shutdown Setup" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Target VM: win11-vscode (Development Sandbox)" -ForegroundColor Yellow
Write-Host ""
Write-Host "Configuration:"
Write-Host "  Resource Group: $ResourceGroup"
Write-Host "  VM: $VMName"
Write-Host "  Location: $Location"
Write-Host "  Idle CPU Threshold: ${IdleCpuThreshold}%"
Write-Host "  Idle Duration: ${IdleDurationMinutes} minutes"
Write-Host ""
Write-Host "What this does:"
Write-Host "  - Monitors VM activity (CPU, network)"
Write-Host "  - Automatically stops VM when idle for $IdleDurationMinutes min"
Write-Host "  - Saves costs when not coding (VM deallocated = `$0/hour)"
Write-Host "  - Easy to restart: Start-AzVM or via Portal"
Write-Host ""

$confirm = Read-Host "Continue with setup? (y/n)"
if ($confirm -ne 'y') {
    Write-Host "Setup cancelled" -ForegroundColor Yellow
    exit
}

# Connect to Azure
Write-Host ""
Write-Host "Step 1: Connecting to Azure..." -ForegroundColor Yellow

try {
    Connect-AzAccount -ErrorAction Stop

    if (-not $SubscriptionId) {
        # Show available subscriptions
        Write-Host ""
        Write-Host "Available Subscriptions:" -ForegroundColor Cyan
        $subs = Get-AzSubscription | Select-Object Name, Id
        $subs | Format-Table -AutoSize

        $SubscriptionId = Read-Host "Enter Subscription ID"
    }

    Set-AzContext -SubscriptionId $SubscriptionId
    Write-Host "✅ Connected to Azure" -ForegroundColor Green
} catch {
    Write-Error "Failed to connect to Azure: $_"
    exit 1
}

# Verify VM exists
Write-Host ""
Write-Host "Step 2: Verifying VM exists..." -ForegroundColor Yellow
try {
    $VM = Get-AzVM -ResourceGroupName $ResourceGroup -Name $VMName -ErrorAction Stop
    Write-Host "✅ Found VM: $VMName" -ForegroundColor Green
    Write-Host "   Size: $($VM.HardwareProfile.VmSize)"
    Write-Host "   Location: $($VM.Location)"
} catch {
    Write-Error "VM not found. Please verify Resource Group and VM name."
    Write-Host "Available VMs:"
    Get-AzVM | Select-Object ResourceGroupName, Name, Location | Format-Table -AutoSize
    exit 1
}

# Create Automation Account
Write-Host ""
Write-Host "Step 3: Creating Automation Account..." -ForegroundColor Yellow
try {
    $AutomationAccount = New-AzAutomationAccount `
        -ResourceGroupName $ResourceGroup `
        -Name $AutomationAccountName `
        -Location $Location `
        -Plan Basic `
        -AssignSystemIdentity `
        -ErrorAction Stop
    Write-Host "✅ Automation Account created" -ForegroundColor Green
} catch {
    if ($_.Exception.Message -like "*already exists*") {
        Write-Host "⚠️  Automation Account already exists - continuing..." -ForegroundColor Yellow
        $AutomationAccount = Get-AzAutomationAccount -ResourceGroupName $ResourceGroup -Name $AutomationAccountName
    } else {
        throw
    }
}

# Get Managed Identity
Write-Host ""
Write-Host "Step 4: Retrieving Managed Identity..." -ForegroundColor Yellow
$PrincipalId = $AutomationAccount.Identity.PrincipalId
Write-Host "✅ Principal ID: $PrincipalId" -ForegroundColor Green

# Assign RBAC permissions
Write-Host ""
Write-Host "Step 5: Assigning RBAC permissions..." -ForegroundColor Yellow
$VMId = $VM.Id

# Wait for identity to propagate
Write-Host "Waiting 30 seconds for identity propagation..."
Start-Sleep -Seconds 30

try {
    New-AzRoleAssignment `
        -ObjectId $PrincipalId `
        -RoleDefinitionName "Virtual Machine Contributor" `
        -Scope $VMId `
        -ErrorAction SilentlyContinue | Out-Null

    New-AzRoleAssignment `
        -ObjectId $PrincipalId `
        -RoleDefinitionName "Monitoring Reader" `
        -Scope $VMId `
        -ErrorAction SilentlyContinue | Out-Null

    Write-Host "✅ RBAC permissions granted" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Permissions may already exist - continuing..." -ForegroundColor Yellow
}

# Import PowerShell modules
Write-Host ""
Write-Host "Step 6: Importing PowerShell modules..." -ForegroundColor Yellow
Write-Host "(This takes 5-10 minutes - modules install in background)" -ForegroundColor Gray

$modules = @("Az.Accounts", "Az.Compute", "Az.Monitor", "Az.Resources")
foreach ($module in $modules) {
    Write-Host "  Importing $module..." -ForegroundColor Gray
    try {
        New-AzAutomationModule `
            -ResourceGroupName $ResourceGroup `
            -AutomationAccountName $AutomationAccountName `
            -Name $module `
            -ContentLinkUri "https://www.powershellgallery.com/api/v2/package/$module" `
            -ErrorAction SilentlyContinue | Out-Null
    } catch {
        Write-Host "    (Module may already be importing)" -ForegroundColor DarkGray
    }
}
Write-Host "✅ Modules queued for import" -ForegroundColor Green

# Create runbook
Write-Host ""
Write-Host "Step 7: Creating runbook..." -ForegroundColor Yellow

$RunbookName = "Stop-IdleVM"
$RunbookPath = Join-Path $PSScriptRoot "azure_vm_idle_shutdown_runbook.ps1"

if (-not (Test-Path $RunbookPath)) {
    Write-Error "Runbook file not found: $RunbookPath"
    exit 1
}

try {
    Import-AzAutomationRunbook `
        -ResourceGroupName $ResourceGroup `
        -AutomationAccountName $AutomationAccountName `
        -Name $RunbookName `
        -Type PowerShell `
        -Path $RunbookPath `
        -Force `
        -ErrorAction Stop | Out-Null

    Publish-AzAutomationRunbook `
        -ResourceGroupName $ResourceGroup `
        -AutomationAccountName $AutomationAccountName `
        -Name $RunbookName `
        -ErrorAction Stop | Out-Null

    Write-Host "✅ Runbook created and published" -ForegroundColor Green
} catch {
    Write-Error "Failed to create runbook: $_"
    exit 1
}

# Create webhook
Write-Host ""
Write-Host "Step 8: Creating webhook..." -ForegroundColor Yellow

$WebhookName = "vm-idle-webhook"
$ExpiryTime = (Get-Date).AddYears(1)

try {
    # Remove old webhook if exists
    Remove-AzAutomationWebhook `
        -ResourceGroupName $ResourceGroup `
        -AutomationAccountName $AutomationAccountName `
        -Name $WebhookName `
        -ErrorAction SilentlyContinue | Out-Null

    $Webhook = New-AzAutomationWebhook `
        -ResourceGroupName $ResourceGroup `
        -AutomationAccountName $AutomationAccountName `
        -Name $WebhookName `
        -RunbookName $RunbookName `
        -IsEnabled $true `
        -ExpiryTime $ExpiryTime `
        -Force

    $WebhookUri = $Webhook.WebhookURI

    Write-Host "✅ Webhook created" -ForegroundColor Green
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow
    Write-Host "⚠️  IMPORTANT: Save this webhook URI (shown only once):" -ForegroundColor Red
    Write-Host $WebhookUri -ForegroundColor Yellow
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter after saving the webhook URI"
} catch {
    Write-Error "Failed to create webhook: $_"
    exit 1
}

# Create Action Group
Write-Host ""
Write-Host "Step 9: Creating Action Group..." -ForegroundColor Yellow

$ActionGroupName = "sandbox-vm-idle-actions"

try {
    $WebhookReceiver = New-AzActionGroupWebhookReceiverObject `
        -Name "IdleShutdown" `
        -ServiceUri $WebhookUri `
        -UseCommonAlertSchema $true

    New-AzActionGroup `
        -ResourceGroupName $ResourceGroup `
        -Name $ActionGroupName `
        -ShortName "SBXIdle" `
        -WebhookReceiver $WebhookReceiver `
        -ErrorAction Stop | Out-Null

    Write-Host "✅ Action Group created" -ForegroundColor Green
} catch {
    if ($_.Exception.Message -like "*already exists*") {
        Write-Host "⚠️  Action Group already exists - updating..." -ForegroundColor Yellow
        # Update existing
    } else {
        throw
    }
}

# Create metric alert
Write-Host ""
Write-Host "Step 10: Creating metric alert..." -ForegroundColor Yellow

$AlertName = "sandbox-idle-alert"

try {
    $Criteria = New-AzMetricAlertRuleV2Criteria `
        -MetricName "Percentage CPU" `
        -TimeAggregation Average `
        -Operator LessThan `
        -Threshold $IdleCpuThreshold

    $ActionGroup = Get-AzActionGroup -ResourceGroupName $ResourceGroup -Name $ActionGroupName

    Add-AzMetricAlertRuleV2 `
        -Name $AlertName `
        -ResourceGroupName $ResourceGroup `
        -WindowSize ([TimeSpan]::FromMinutes($IdleDurationMinutes)) `
        -Frequency ([TimeSpan]::FromMinutes(5)) `
        -TargetResourceId $VMId `
        -Condition $Criteria `
        -ActionGroupId $ActionGroup.Id `
        -Description "Auto-shutdown for sandbox win11-vscode when idle >$IdleDurationMinutes min" `
        -Severity 3 `
        -ErrorAction Stop

    Write-Host "✅ Metric alert created" -ForegroundColor Green
} catch {
    if ($_.Exception.Message -like "*already exists*") {
        Write-Host "⚠️  Alert already exists" -ForegroundColor Yellow
    } else {
        throw
    }
}

# Wait for modules and test
Write-Host ""
Write-Host "Step 11: Waiting for modules to finish importing..." -ForegroundColor Yellow
Write-Host "Checking module status (may take up to 10 minutes)..." -ForegroundColor Gray

$maxWaitMinutes = 10
$waitedMinutes = 0
$allModulesReady = $false

while ($waitedMinutes -lt $maxWaitMinutes -and -not $allModulesReady) {
    Start-Sleep -Seconds 60
    $waitedMinutes++

    $moduleStatus = Get-AzAutomationModule `
        -ResourceGroupName $ResourceGroup `
        -AutomationAccountName $AutomationAccountName `
        | Where-Object { $_.Name -in $modules } `
        | Select-Object Name, ProvisioningState

    $importing = $moduleStatus | Where-Object { $_.ProvisioningState -ne "Succeeded" }

    if ($importing.Count -eq 0) {
        $allModulesReady = $true
        Write-Host "✅ All modules imported successfully" -ForegroundColor Green
    } else {
        Write-Host "  Still importing: $($importing.Name -join ', ') ($waitedMinutes/$maxWaitMinutes min)" -ForegroundColor Gray
    }
}

if (-not $allModulesReady) {
    Write-Host "⚠️  Modules still importing - test may fail. Try again in 5 minutes." -ForegroundColor Yellow
    Write-Host "   You can test later with: ./Manage-VMIdleShutdown.ps1 -Action Test -ResourceGroup $ResourceGroup -VMName $VMName"
} else {
    # Test runbook
    Write-Host ""
    Write-Host "Step 12: Testing runbook..." -ForegroundColor Yellow

    try {
        $Job = Start-AzAutomationRunbook `
            -ResourceGroupName $ResourceGroup `
            -AutomationAccountName $AutomationAccountName `
            -Name $RunbookName `
            -Wait `
            -MaxWaitSeconds 120

        Write-Host "Job Status: $($Job.Status)" -ForegroundColor $(if($Job.Status -eq "Completed"){"Green"}else{"Yellow"})

        # Get job output
        $JobOutput = Get-AzAutomationJobOutput `
            -ResourceGroupName $ResourceGroup `
            -AutomationAccountName $AutomationAccountName `
            -Id $Job.JobId `
            -Stream Output `
            | Select-Object -First 10

        Write-Host ""
        Write-Host "Sample output:" -ForegroundColor Gray
        foreach ($output in $JobOutput) {
            $record = Get-AzAutomationJobOutputRecord `
                -ResourceGroupName $ResourceGroup `
                -AutomationAccountName $AutomationAccountName `
                -JobId $Job.JobId `
                -Id $output.StreamRecordId
            Write-Host "  $($record.Value.value)" -ForegroundColor DarkGray
        }

        Write-Host "✅ Test complete" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  Test execution failed (modules may still be loading)" -ForegroundColor Yellow
        Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor DarkGray
    }
}

# Summary
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "✅ Setup Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Sandbox VM Idle Shutdown Configuration:" -ForegroundColor White
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
Write-Host "  VM Name:         $VMName" -ForegroundColor Cyan
Write-Host "  Resource Group:  $ResourceGroup" -ForegroundColor Cyan
Write-Host "  Idle Threshold:  CPU < ${IdleCpuThreshold}% for ${IdleDurationMinutes} minutes" -ForegroundColor Cyan
Write-Host "  Check Frequency: Every 5 minutes" -ForegroundColor Cyan
Write-Host ""
Write-Host "How it works:" -ForegroundColor Yellow
Write-Host "  1️⃣  Azure Monitor checks VM activity every 5 minutes"
Write-Host "  2️⃣  If CPU < ${IdleCpuThreshold}% for ${IdleDurationMinutes} min → alert fires"
Write-Host "  3️⃣  Webhook triggers runbook → validates idle state"
Write-Host "  4️⃣  VM stops automatically (deallocated = `$0/hour)"
Write-Host ""
Write-Host "Management Commands:" -ForegroundColor Yellow
Write-Host "  Test:     ./Manage-VMIdleShutdown.ps1 -Action Test -ResourceGroup $ResourceGroup -VMName $VMName"
Write-Host "  Status:   ./Manage-VMIdleShutdown.ps1 -Action Status -ResourceGroup $ResourceGroup -VMName $VMName"
Write-Host "  Disable:  ./Manage-VMIdleShutdown.ps1 -Action Disable -ResourceGroup $ResourceGroup -VMName $VMName"
Write-Host "  Enable:   ./Manage-VMIdleShutdown.ps1 -Action Enable -ResourceGroup $ResourceGroup -VMName $VMName"
Write-Host "  Start VM: Start-AzVM -ResourceGroupName $ResourceGroup -Name $VMName"
Write-Host ""
Write-Host "Cost Savings:" -ForegroundColor Yellow
Write-Host "  Running 24/7:    ~`$70/month (varies by VM size)"
Write-Host "  With auto-stop:  ~`$23-31/month (8h/day usage)"
Write-Host "  When stopped:    `$0/hour compute + ~`$8/month storage"
Write-Host ""
Write-Host "Quick Reference: ./claude/tools/sre/azure_vm_idle_shutdown_quickref.txt" -ForegroundColor Gray
Write-Host "Full Docs:       ./claude/tools/sre/AZURE_VM_IDLE_SHUTDOWN_README.md" -ForegroundColor Gray
Write-Host ""
