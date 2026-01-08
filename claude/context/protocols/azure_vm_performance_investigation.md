# Azure VM Performance Investigation Runbook

## Overview

This runbook covers investigating Windows VM performance issues (CPU spikes, high IOPS, disk latency) by correlating Azure platform metrics with guest OS data.

## Data Sources Available

### Platform-Level (Always Collected - No Setup)

| Metric | Granularity | Retention | Notes |
|--------|-------------|-----------|-------|
| Percentage CPU | 1-min | 93 days | Host-level only, not per-process |
| Disk Read/Write Bytes | Per-disk, 1-min | 93 days | Throughput |
| Disk Read/Write Operations/Sec | Per-disk, 1-min | 93 days | IOPS |
| OS/Data Disk IOPS Consumed % | Per-disk, 1-min | 93 days | Shows throttling |
| Network In/Out | Aggregate | 93 days | No per-connection detail |

**Limitations**: No process-level breakdown, no queue depths, no latency metrics.

### Guest OS (Requires Azure Monitor Agent + DCR)

| Data | Requires |
|------|----------|
| Per-process CPU | AMA + Perf counters DCR |
| Disk queue length, latency | AMA + Perf counters DCR |
| Memory pressure details | AMA + Perf counters DCR |
| Windows Event Logs | AMA + Windows Events DCR |
| Application crashes | AMA or Application Insights |

### Retention Summary

| Data Source | Default Retention |
|-------------|-------------------|
| Platform Metrics | 93 days (fixed) |
| Activity Log | 90 days (export to LA for longer) |
| Guest OS Logs (via AMA) | 31 days (configurable to 2 years) |
| Boot Diagnostics | Indefinite (storage account) |

## Investigation Workflow

### Phase 1: Quick Triage (No Setup Required)

#### 1.1 Query Platform Metrics

```bash
# Set variables
RG="resource-group"
VM="vm-name"
SUB="subscription-id"
START="2026-01-07T00:00:00Z"
END="2026-01-08T00:00:00Z"

# Get CPU, IOPS, throttling
az monitor metrics list \
  --resource "/subscriptions/$SUB/resourceGroups/$RG/providers/Microsoft.Compute/virtualMachines/$VM" \
  --metric "Percentage CPU" "OS Disk IOPS Consumed Percentage" "Disk Read Operations/Sec" "Disk Write Operations/Sec" \
  --start-time $START \
  --end-time $END \
  --interval PT5M \
  -o json > azure_metrics.json
```

#### 1.2 Check Activity Log (What Changed?)

```bash
az monitor activity-log list \
  --resource-id "/subscriptions/$SUB/resourceGroups/$RG/providers/Microsoft.Compute/virtualMachines/$VM" \
  --start-time $START \
  -o json > activity_log.json
```

#### 1.3 Check Resource Health

```bash
az resource show \
  --ids "/subscriptions/$SUB/resourceGroups/$RG/providers/Microsoft.Compute/virtualMachines/$VM/providers/Microsoft.ResourceHealth/availabilityStatuses/current" \
  -o json
```

#### 1.4 KQL Queries (If Log Analytics Available)

```kql
// Platform metrics - CPU and IOPS spikes
AzureMetrics
| where ResourceId contains "vm-name"
| where MetricName in ("Percentage CPU", "OS Disk IOPS Consumed Percentage")
| where Average > 80
| project TimeGenerated, MetricName, Average, Maximum
| order by TimeGenerated desc

// Activity Log - config changes
AzureActivity
| where ResourceId contains "vm-name"
| where ActivityStatusValue == "Success"
| project TimeGenerated, OperationNameValue, Caller
| order by TimeGenerated desc
```

### Phase 2: Guest OS Data Collection

#### Option A: Export via Azure Run Command

```bash
# Quick summary of errors/warnings in last 24h
az vm run-command invoke \
  --resource-group $RG \
  --name $VM \
  --command-id RunPowerShellScript \
  --scripts '
    Get-WinEvent -FilterHashtable @{
        LogName="System","Application"
        Level=1,2,3
        StartTime=(Get-Date).AddHours(-24)
    } | Group-Object ProviderName, Id |
    Sort-Object Count -Descending |
    Select-Object Count, @{N="Source";E={$_.Name}} -First 20 |
    ConvertTo-Json
  '

# Export to JSON (limited to ~4KB output)
az vm run-command invoke \
  --resource-group $RG \
  --name $VM \
  --command-id RunPowerShellScript \
  --scripts '
    Get-WinEvent -FilterHashtable @{
        LogName="System"
        Level=1,2,3
        StartTime=(Get-Date).AddHours(-24)
    } | Select TimeCreated, Id, LevelDisplayName, ProviderName,
        @{N="Message";E={$_.Message.Substring(0,[Math]::Min(200,$_.Message.Length))}} |
    ConvertTo-Json -Depth 2
  ' -o json > guest_events.json
```

#### Option B: RDP/Bastion and Export Locally

```powershell
# On the VM - export events to CSV
$StartTime = (Get-Date).AddHours(-24)
$ExportPath = "C:\Temp\EventExport"
New-Item -Path $ExportPath -ItemType Directory -Force

Get-WinEvent -FilterHashtable @{
    LogName = 'System'
    StartTime = $StartTime
} | Export-Csv "$ExportPath\System_Events.csv" -NoTypeInformation

Get-WinEvent -FilterHashtable @{
    LogName = 'Application'
    StartTime = $StartTime
} | Export-Csv "$ExportPath\Application_Events.csv" -NoTypeInformation

# Disk-specific logs
Get-WinEvent -FilterHashtable @{
    LogName = 'Microsoft-Windows-Storage-Storport/Operational'
    StartTime = $StartTime
} -ErrorAction SilentlyContinue | Export-Csv "$ExportPath\Storport_Events.csv" -NoTypeInformation

Compress-Archive -Path "$ExportPath\*" -DestinationPath "C:\Temp\EventLogs.zip" -Force
```

#### Option C: Export Raw EVTX Files

```powershell
# Export native Windows format
wevtutil epl System "C:\Temp\System.evtx"
wevtutil epl Application "C:\Temp\Application.evtx"
```

### Phase 3: Correlation Analysis

#### Python Correlation Script

```python
import pandas as pd
import json
from datetime import datetime, timedelta

# Load Azure metrics
with open('azure_metrics.json') as f:
    metrics_data = json.load(f)

# Parse into DataFrame
metrics_rows = []
for metric in metrics_data['value']:
    metric_name = metric['name']['value']
    for ts in metric['timeseries']:
        for data in ts['data']:
            if data.get('average') is not None:
                metrics_rows.append({
                    'TimeGenerated': data['timeStamp'],
                    'Metric': metric_name,
                    'Average': data.get('average'),
                    'Maximum': data.get('maximum')
                })

azure_df = pd.DataFrame(metrics_rows)
azure_df['TimeGenerated'] = pd.to_datetime(azure_df['TimeGenerated'])

# Load Windows events
events_df = pd.read_csv('System_Events.csv')
events_df['TimeCreated'] = pd.to_datetime(events_df['TimeCreated'])

# Find CPU spikes > 80%
cpu_spikes = azure_df[(azure_df['Metric'] == 'Percentage CPU') & (azure_df['Average'] > 80)]

# Correlate events within ±5 minutes of each spike
for _, spike in cpu_spikes.iterrows():
    spike_time = spike['TimeGenerated']
    window_start = spike_time - timedelta(minutes=5)
    window_end = spike_time + timedelta(minutes=5)

    related_events = events_df[
        (events_df['TimeCreated'] >= window_start) &
        (events_df['TimeCreated'] <= window_end)
    ]

    if len(related_events) > 0:
        print(f"\n=== CPU Spike at {spike_time} ({spike['Average']:.1f}%) ===")
        for _, event in related_events.iterrows():
            print(f"  {event['TimeCreated']} | {event['LevelDisplayName']} | {event['ProviderName']}")
```

### Phase 4: Full Visibility Setup (Azure Monitor Agent)

#### Check Current Monitoring State

```bash
# What extensions are installed?
az vm extension list --resource-group $RG --vm-name $VM -o table

# Any DCRs associated?
az monitor data-collection rule association list \
  --resource "/subscriptions/$SUB/resourceGroups/$RG/providers/Microsoft.Compute/virtualMachines/$VM" \
  -o table
```

#### Install Azure Monitor Agent

```bash
az vm extension set \
  --resource-group $RG \
  --vm-name $VM \
  --name AzureMonitorWindowsAgent \
  --publisher Microsoft.Azure.Monitor \
  --enable-auto-upgrade true
```

#### Create Data Collection Rule

See [Microsoft Docs: Create DCR](https://docs.microsoft.com/en-us/azure/azure-monitor/agents/data-collection-rule-azure-monitor-agent) for full DCR JSON template.

Key performance counters for VM performance:
```
\Processor(_Total)\% Processor Time
\Process(*)\% Processor Time
\PhysicalDisk(*)\Disk Reads/sec
\PhysicalDisk(*)\Disk Writes/sec
\PhysicalDisk(*)\Avg. Disk Queue Length
\PhysicalDisk(*)\Avg. Disk sec/Read
\PhysicalDisk(*)\Avg. Disk sec/Write
\Memory\Available MBytes
\Memory\% Committed Bytes In Use
```

## Key Windows Event IDs for Performance Issues

| Event ID | Log | Indicates |
|----------|-----|-----------|
| 7 | System | Disk bad block |
| 11 | System | Disk controller error |
| 15 | System | Disk not ready |
| 51 | System | Disk paging error |
| 129 | System | Storage timeout reset |
| 153 | System | Disk IO retry (storage latency) |
| 1001 | Application | Windows Error Reporting (app crash) |
| 6008 | System | Unexpected shutdown |
| 41 | System | Kernel power failure |

```powershell
# Quick filter for disk-related issues
Get-WinEvent -FilterHashtable @{
    LogName = 'System'
    StartTime = (Get-Date).AddHours(-24)
    Id = 7,11,15,51,129,153
}
```

## GDAP/Cross-Tenant Access

For customer VMs, see [GDAP Access Troubleshooting](gdap_access_troubleshooting.md).

Required roles:
- **Monitoring Reader**: Query platform metrics
- **Virtual Machine Contributor**: Run Command access
- **Log Analytics Reader**: Query Log Analytics workspace

## Related Documentation

- [GDAP Access Troubleshooting](gdap_access_troubleshooting.md)
- [Azure Environment Discovery](azure_environment_discovery.md)

---

**Last Updated**: 2026-01-08
**Maintained By**: Azure Operations Engineer Agent
