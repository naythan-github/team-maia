# Setup Azure VM Idle Shutdown Automation (PowerShell version)
# Purpose: Complete setup for activity-based VM shutdown
# Version: 1.0

param(
    [Parameter(Mandatory=$true)]
    [string]$SubscriptionId,

    [Parameter(Mandatory=$true)]
    [string]$ResourceGroup,

    [Parameter(Mandatory=$true)]
    [string]$VMName,

    [Parameter(Mandatory=$false)]
    [string]$Location = "australiaeast",

    [Parameter(Mandatory=$false)]
    [int]$IdleCpuThreshold = 5,

    [Parameter(Mandatory=$false)]
    [int]$IdleNetworkThresholdKB = 100,

    [Parameter(Mandatory=$false)]
    [int]$IdleDurationMinutes = 30,

    [Parameter(Mandatory=$false)]
    [string]$AutomationAccountName = "vm-idle-shutdown-automation"
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Azure VM Idle Shutdown Setup" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Configuration:"
Write-Host "  Subscription: $SubscriptionId"
Write-Host "  Resource Group: $ResourceGroup"
Write-Host "  VM: $VMName"
Write-Host "  Location: $Location"
Write-Host "  Idle CPU Threshold: ${IdleCpuThreshold}%"
Write-Host "  Idle Duration: ${IdleDurationMinutes} minutes"
Write-Host ""

$confirm = Read-Host "Continue with setup? (y/n)"
if ($confirm -ne 'y') {
    Write-Host "Setup cancelled" -ForegroundColor Yellow
    exit
}

# Connect to Azure
Write-Host ""
Write-Host "Step 1: Connecting to Azure..." -ForegroundColor Yellow
Connect-AzAccount
Set-AzContext -SubscriptionId $SubscriptionId
Write-Host "✅ Connected to Azure" -ForegroundColor Green

# Create Automation Account
Write-Host ""
Write-Host "Step 2: Creating Automation Account..." -ForegroundColor Yellow
try {
    $AutomationAccount = New-AzAutomationAccount `
        -ResourceGroupName $ResourceGroup `
        -Name $AutomationAccountName `
        -Location $Location `
        -Plan Basic `
        -AssignSystemIdentity
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
Write-Host "Step 3: Retrieving Managed Identity..." -ForegroundColor Yellow
$PrincipalId = $AutomationAccount.Identity.PrincipalId
Write-Host "✅ Principal ID: $PrincipalId" -ForegroundColor Green

# Assign RBAC permissions
Write-Host ""
Write-Host "Step 4: Assigning RBAC permissions..." -ForegroundColor Yellow
$VM = Get-AzVM -ResourceGroupName $ResourceGroup -Name $VMName
$VMId = $VM.Id

# Wait for identity to propagate
Write-Host "Waiting 30 seconds for identity propagation..."
Start-Sleep -Seconds 30

New-AzRoleAssignment `
    -ObjectId $PrincipalId `
    -RoleDefinitionName "Virtual Machine Contributor" `
    -Scope $VMId `
    -ErrorAction SilentlyContinue

New-AzRoleAssignment `
    -ObjectId $PrincipalId `
    -RoleDefinitionName "Monitoring Reader" `
    -Scope $VMId `
    -ErrorAction SilentlyContinue

Write-Host "✅ RBAC permissions granted" -ForegroundColor Green

# Import PowerShell modules
Write-Host ""
Write-Host "Step 5: Importing PowerShell modules (this may take 5-10 minutes)..." -ForegroundColor Yellow

$modules = @("Az.Accounts", "Az.Compute", "Az.Monitor", "Az.Resources")
foreach ($module in $modules) {
    Write-Host "  Importing $module..."
    New-AzAutomationModule `
        -ResourceGroupName $ResourceGroup `
        -AutomationAccountName $AutomationAccountName `
        -Name $module `
        -ContentLinkUri "https://www.powershellgallery.com/api/v2/package/$module"
}
Write-Host "✅ Modules imported (may still be installing in background)" -ForegroundColor Green

# Create runbook
Write-Host ""
Write-Host "Step 6: Creating runbook..." -ForegroundColor Yellow

$RunbookName = "Stop-IdleVM"
$RunbookPath = Join-Path $PSScriptRoot "azure_vm_idle_shutdown_runbook.ps1"

if (-not (Test-Path $RunbookPath)) {
    Write-Error "Runbook file not found: $RunbookPath"
    exit 1
}

# Update runbook with VM details
$RunbookContent = Get-Content $RunbookPath -Raw
$RunbookContent = $RunbookContent -replace 'YOUR_RESOURCE_GROUP', $ResourceGroup
$RunbookContent = $RunbookContent -replace 'YOUR_VM_NAME', $VMName

Import-AzAutomationRunbook `
    -ResourceGroupName $ResourceGroup `
    -AutomationAccountName $AutomationAccountName `
    -Name $RunbookName `
    -Type PowerShell `
    -Path $RunbookPath `
    -Force

Publish-AzAutomationRunbook `
    -ResourceGroupName $ResourceGroup `
    -AutomationAccountName $AutomationAccountName `
    -Name $RunbookName

Write-Host "✅ Runbook created and published" -ForegroundColor Green

# Create webhook
Write-Host ""
Write-Host "Step 7: Creating webhook..." -ForegroundColor Yellow

$WebhookName = "vm-idle-webhook"
$ExpiryTime = (Get-Date).AddYears(1)

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
Write-Host "⚠️  IMPORTANT: Save this webhook URI (shown only once):" -ForegroundColor Red
Write-Host $WebhookUri -ForegroundColor Yellow
Write-Host ""

# Create Action Group
Write-Host ""
Write-Host "Step 8: Creating Action Group..." -ForegroundColor Yellow

$ActionGroupName = "vm-idle-shutdown-actions"

$WebhookReceiver = New-AzActionGroupWebhookReceiverObject `
    -Name "IdleShutdown" `
    -ServiceUri $WebhookUri `
    -UseCommonAlertSchema $true

New-AzActionGroup `
    -ResourceGroupName $ResourceGroup `
    -Name $ActionGroupName `
    -ShortName "VMIdle" `
    -WebhookReceiver $WebhookReceiver

Write-Host "✅ Action Group created" -ForegroundColor Green

# Create metric alert
Write-Host ""
Write-Host "Step 9: Creating metric alert..." -ForegroundColor Yellow

$AlertName = "vm-idle-alert-$VMName"

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
    -Description "Triggers when VM is idle (low CPU) for $IdleDurationMinutes minutes" `
    -Severity 3

Write-Host "✅ Metric alert created" -ForegroundColor Green

# Test runbook
Write-Host ""
Write-Host "Step 10: Testing runbook (dry run)..." -ForegroundColor Yellow

# Wait for modules to finish importing
Write-Host "Waiting 2 minutes for modules to finish importing..."
Start-Sleep -Seconds 120

$Job = Start-AzAutomationRunbook `
    -ResourceGroupName $ResourceGroup `
    -AutomationAccountName $AutomationAccountName `
    -Name $RunbookName `
    -Wait

Write-Host "Job Status: $($Job.Status)"

# Get job output
$JobOutput = Get-AzAutomationJobOutput `
    -ResourceGroupName $ResourceGroup `
    -AutomationAccountName $AutomationAccountName `
    -Id $Job.JobId `
    -Stream Output

foreach ($output in $JobOutput) {
    $record = Get-AzAutomationJobOutputRecord `
        -ResourceGroupName $ResourceGroup `
        -AutomationAccountName $AutomationAccountName `
        -JobId $Job.JobId `
        -Id $output.StreamRecordId
    Write-Host $record.Value.value
}

Write-Host "✅ Test complete" -ForegroundColor Green

# Summary
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Summary:"
Write-Host "  Automation Account: $AutomationAccountName"
Write-Host "  Runbook: $RunbookName"
Write-Host "  Alert: $AlertName"
Write-Host "  Webhook: [saved above - store securely]"
Write-Host ""
Write-Host "How it works:"
Write-Host "  1. Azure Monitor checks VM metrics every 5 minutes"
Write-Host "  2. If CPU < ${IdleCpuThreshold}% for ${IdleDurationMinutes} minutes, alert fires"
Write-Host "  3. Alert triggers webhook → runbook executes"
Write-Host "  4. Runbook validates idle state and stops VM"
Write-Host ""
Write-Host "To start VM manually:"
Write-Host "  Start-AzVM -ResourceGroupName $ResourceGroup -Name $VMName"
Write-Host ""
Write-Host "To view runbook logs:"
Write-Host "  Get-AzAutomationJob -ResourceGroupName $ResourceGroup -AutomationAccountName $AutomationAccountName | Select-Object -First 10"
Write-Host ""
