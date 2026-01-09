# Manage VM Idle Shutdown System
# Purpose: Test, monitor, and manage the idle shutdown automation
# Version: 1.0

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("Test", "Status", "Disable", "Enable", "ViewLogs", "StartVM", "ManualShutdown")]
    [string]$Action,

    [Parameter(Mandatory=$true)]
    [string]$ResourceGroup,

    [Parameter(Mandatory=$true)]
    [string]$VMName,

    [Parameter(Mandatory=$false)]
    [string]$AutomationAccountName = "vm-idle-shutdown-automation"
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "VM Idle Shutdown Manager" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Action: $Action"
Write-Host "VM: $VMName"
Write-Host "Resource Group: $ResourceGroup"
Write-Host ""

switch ($Action) {
    "Test" {
        Write-Host "Testing idle detection runbook..." -ForegroundColor Yellow

        $RunbookName = "Stop-IdleVM"

        $Job = Start-AzAutomationRunbook `
            -ResourceGroupName $ResourceGroup `
            -AutomationAccountName $AutomationAccountName `
            -Name $RunbookName `
            -Wait

        Write-Host ""
        Write-Host "Job Status: $($Job.Status)" -ForegroundColor $(if($Job.Status -eq "Completed"){"Green"}else{"Red"})
        Write-Host ""
        Write-Host "Job Output:" -ForegroundColor Yellow

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

        # Show any errors
        $Errors = Get-AzAutomationJobOutput `
            -ResourceGroupName $ResourceGroup `
            -AutomationAccountName $AutomationAccountName `
            -Id $Job.JobId `
            -Stream Error

        if ($Errors) {
            Write-Host ""
            Write-Host "Errors:" -ForegroundColor Red
            foreach ($error in $Errors) {
                $record = Get-AzAutomationJobOutputRecord `
                    -ResourceGroupName $ResourceGroup `
                    -AutomationAccountName $AutomationAccountName `
                    -JobId $Job.JobId `
                    -Id $error.StreamRecordId
                Write-Host $record.Value.value -ForegroundColor Red
            }
        }
    }

    "Status" {
        Write-Host "Checking VM and automation status..." -ForegroundColor Yellow
        Write-Host ""

        # VM Status
        $VM = Get-AzVM -ResourceGroupName $ResourceGroup -Name $VMName -Status
        $PowerState = ($VM.Statuses | Where-Object {$_.Code -like "PowerState/*"}).Code
        Write-Host "VM Power State: $PowerState" -ForegroundColor $(if($PowerState -eq "PowerState/running"){"Green"}else{"Yellow"})

        # Alert Status
        $AlertName = "vm-idle-alert-$VMName"
        $Alert = Get-AzMetricAlertRuleV2 -ResourceGroupName $ResourceGroup -Name $AlertName -ErrorAction SilentlyContinue

        if ($Alert) {
            Write-Host "Alert Enabled: $($Alert.Enabled)" -ForegroundColor $(if($Alert.Enabled){"Green"}else{"Red"})
            Write-Host "Alert Threshold: CPU < $($Alert.Criteria.Threshold)%"
            Write-Host "Alert Window: $($Alert.WindowSize.TotalMinutes) minutes"
        } else {
            Write-Host "Alert: Not found" -ForegroundColor Red
        }

        # Recent Jobs
        Write-Host ""
        Write-Host "Recent Runbook Jobs (last 5):" -ForegroundColor Yellow
        $Jobs = Get-AzAutomationJob `
            -ResourceGroupName $ResourceGroup `
            -AutomationAccountName $AutomationAccountName `
            -RunbookName "Stop-IdleVM" `
            | Select-Object -First 5 `
            | Select-Object StartTime, Status, JobId

        $Jobs | Format-Table -AutoSize

        # Current Metrics
        Write-Host ""
        Write-Host "Current Metrics (last 15 minutes):" -ForegroundColor Yellow

        $VMId = $VM.Id
        $EndTime = Get-Date
        $StartTime = $EndTime.AddMinutes(-15)

        $CpuMetric = Get-AzMetric -ResourceId $VMId `
            -MetricName "Percentage CPU" `
            -StartTime $StartTime `
            -EndTime $EndTime `
            -TimeGrain 00:05:00 `
            -WarningAction SilentlyContinue

        if ($CpuMetric.Data) {
            $AvgCpu = ($CpuMetric.Data | Where-Object {$_.Average -ne $null} | Measure-Object -Property Average -Average).Average
            Write-Host "  Average CPU: $([math]::Round($AvgCpu, 2))%"
        }

        $NetworkMetric = Get-AzMetric -ResourceId $VMId `
            -MetricName "Network In Total" `
            -StartTime $StartTime `
            -EndTime $EndTime `
            -TimeGrain 00:05:00 `
            -WarningAction SilentlyContinue

        if ($NetworkMetric.Data) {
            $AvgNetwork = ($NetworkMetric.Data | Where-Object {$_.Average -ne $null} | Measure-Object -Property Average -Average).Average
            Write-Host "  Average Network In: $([math]::Round($AvgNetwork/1024, 2)) KB"
        }
    }

    "Disable" {
        Write-Host "Disabling idle shutdown alert..." -ForegroundColor Yellow

        $AlertName = "vm-idle-alert-$VMName"

        # Disable the alert
        $Alert = Get-AzMetricAlertRuleV2 -ResourceGroupName $ResourceGroup -Name $AlertName
        $Alert.Enabled = $false

        Add-AzMetricAlertRuleV2 `
            -Name $AlertName `
            -ResourceGroupName $ResourceGroup `
            -WindowSize $Alert.WindowSize `
            -Frequency $Alert.EvaluationFrequency `
            -TargetResourceId $Alert.Scopes[0] `
            -Condition $Alert.Criteria `
            -ActionGroupId $Alert.Actions.ActionGroupId `
            -Severity $Alert.Severity `
            -DisableRule

        Write-Host "✅ Alert disabled - VM will not auto-shutdown" -ForegroundColor Green
    }

    "Enable" {
        Write-Host "Enabling idle shutdown alert..." -ForegroundColor Yellow

        $AlertName = "vm-idle-alert-$VMName"

        # Enable the alert
        $Alert = Get-AzMetricAlertRuleV2 -ResourceGroupName $ResourceGroup -Name $AlertName

        Add-AzMetricAlertRuleV2 `
            -Name $AlertName `
            -ResourceGroupName $ResourceGroup `
            -WindowSize $Alert.WindowSize `
            -Frequency $Alert.EvaluationFrequency `
            -TargetResourceId $Alert.Scopes[0] `
            -Condition $Alert.Criteria `
            -ActionGroupId $Alert.Actions.ActionGroupId `
            -Severity $Alert.Severity

        Write-Host "✅ Alert enabled - VM will auto-shutdown when idle" -ForegroundColor Green
    }

    "ViewLogs" {
        Write-Host "Viewing recent runbook execution logs..." -ForegroundColor Yellow
        Write-Host ""

        $Jobs = Get-AzAutomationJob `
            -ResourceGroupName $ResourceGroup `
            -AutomationAccountName $AutomationAccountName `
            -RunbookName "Stop-IdleVM" `
            | Select-Object -First 10

        foreach ($Job in $Jobs) {
            Write-Host "========================================" -ForegroundColor Cyan
            Write-Host "Job: $($Job.JobId)" -ForegroundColor Yellow
            Write-Host "Start: $($Job.StartTime)"
            Write-Host "Status: $($Job.Status)"
            Write-Host "Duration: $($Job.EndTime - $Job.StartTime)" -ForegroundColor Gray
            Write-Host ""

            # Get output
            $Output = Get-AzAutomationJobOutput `
                -ResourceGroupName $ResourceGroup `
                -AutomationAccountName $AutomationAccountName `
                -Id $Job.JobId `
                -Stream Output

            foreach ($out in $Output) {
                $record = Get-AzAutomationJobOutputRecord `
                    -ResourceGroupName $ResourceGroup `
                    -AutomationAccountName $AutomationAccountName `
                    -JobId $Job.JobId `
                    -Id $out.StreamRecordId
                Write-Host $record.Value.value
            }
            Write-Host ""
        }
    }

    "StartVM" {
        Write-Host "Starting VM..." -ForegroundColor Yellow

        Start-AzVM -ResourceGroupName $ResourceGroup -Name $VMName

        Write-Host "✅ VM started successfully" -ForegroundColor Green

        # Show status
        $VM = Get-AzVM -ResourceGroupName $ResourceGroup -Name $VMName -Status
        $PowerState = ($VM.Statuses | Where-Object {$_.Code -like "PowerState/*"}).Code
        Write-Host "Current state: $PowerState" -ForegroundColor Green
    }

    "ManualShutdown" {
        Write-Host "Manually triggering idle shutdown runbook..." -ForegroundColor Yellow

        $confirm = Read-Host "This will stop the VM if it's idle. Continue? (y/n)"
        if ($confirm -ne 'y') {
            Write-Host "Cancelled" -ForegroundColor Yellow
            exit
        }

        $RunbookName = "Stop-IdleVM"

        $Job = Start-AzAutomationRunbook `
            -ResourceGroupName $ResourceGroup `
            -AutomationAccountName $AutomationAccountName `
            -Name $RunbookName `
            -Wait

        Write-Host ""
        Write-Host "Result:" -ForegroundColor Yellow

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
    }
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Operation Complete" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
