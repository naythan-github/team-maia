#!/bin/bash
# Azure VM Disk Audit Script
#
# Purpose: Audit Azure VMs for:
#   1. HDD OS disks (Standard_LRS)
#   2. Unallocated disk space on SSD OS disks
#
# Author: SRE Principal Engineer Agent
# Created: 2026-01-07
#
# Usage:
#   ./vm_disk_audit.sh [subscription-id] [output-file.csv]
#   ./vm_disk_audit.sh --help

set -euo pipefail

# Configuration
SUBSCRIPTION_ID="${1:-}"
OUTPUT_FILE="${2:-$HOME/work_projects/azure_operations/audit_results/vm_disk_audit_$(date +%Y%m%d_%H%M%S)}"
BATCH_SIZE=10
TEMP_DIR="/tmp/vm_disk_audit_$$"

# Determine output format from extension
if [[ "$OUTPUT_FILE" == *.xlsx ]]; then
    OUTPUT_FORMAT="xlsx"
    CSV_FILE="${OUTPUT_FILE%.xlsx}.csv"
elif [[ "$OUTPUT_FILE" == *.csv ]]; then
    OUTPUT_FORMAT="csv"
    CSV_FILE="$OUTPUT_FILE"
else
    # Default to xlsx if no extension
    OUTPUT_FORMAT="xlsx"
    CSV_FILE="${OUTPUT_FILE}.csv"
    OUTPUT_FILE="${OUTPUT_FILE}.xlsx"
fi

# Help
if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
    cat << EOF
Azure VM Disk Audit Script

PURPOSE:
  Audit Azure VMs for disk configuration issues:
  - HDD OS disks (Standard_LRS)
  - Unallocated space on SSD OS disks

USAGE:
  $0 [subscription-id] [output-file]
  $0 --help

EXAMPLES:
  # Audit current subscription (default: XLSX format)
  # Outputs to: ~/work_projects/azure_operations/audit_results/vm_disk_audit_YYYYMMDD_HHMMSS.xlsx
  $0

  # Audit specific subscription
  $0 9b8e7b3f-d3e7-4da9-a22a-9bf7c8ee4dde

  # Custom output file (XLSX)
  $0 9b8e7b3f-d3e7-4da9-a22a-9bf7c8ee4dde ~/work_projects/azure_operations/audit_results/audit_results.xlsx

  # CSV format
  $0 9b8e7b3f-d3e7-4da9-a22a-9bf7c8ee4dde ~/work_projects/azure_operations/audit_results/audit_results.csv

PHASES:
  Phase 1: Azure Resource Graph query for HDD detection (instant)
  Phase 2: Run Command for partition allocation check (requires running VMs)

OUTPUT:
  CSV file with columns:
  - VMName, ResourceGroup, DiskType, DiskSizeGB, AllocatedGB, UnallocatedGB, Issue

EOF
    exit 0
fi

mkdir -p "$TEMP_DIR"
trap "rm -rf $TEMP_DIR" EXIT

echo "🔍 Azure VM Disk Audit"
echo "====================="
echo ""

# Set subscription if provided
if [[ -n "$SUBSCRIPTION_ID" ]]; then
    echo "Setting subscription context: $SUBSCRIPTION_ID"
    az account set --subscription "$SUBSCRIPTION_ID"
fi

# Show current context
CURRENT_SUB=$(az account show --query "{Name:name, ID:id}" -o tsv | tr '\t' ' - ')
echo "Subscription: $CURRENT_SUB"
echo "Output file: $OUTPUT_FILE"
echo ""

# Phase 1: Azure Resource Graph - HDD Detection
echo "📊 Phase 1: Detecting HDD OS disks via Azure Resource Graph..."
echo ""

# Query for all Windows VMs with OS disk information
QUERY='Resources
| where type =~ "microsoft.compute/virtualmachines"
| extend osDiskId = tostring(properties.storageProfile.osDisk.managedDisk.id)
| extend osType = tostring(properties.storageProfile.osDisk.osType)
| join kind=inner (
    Resources
    | where type =~ "microsoft.compute/disks"
    | extend diskSku = tostring(sku.name),
             diskSizeGB = toint(properties.diskSizeGB),
             diskId = tostring(id)
) on $left.osDiskId == $right.diskId
| project
    VMName = name,
    ResourceGroup = resourceGroup,
    DiskType = diskSku,
    DiskSizeGB = diskSizeGB,
    OSType = osType,
    PowerState = tostring(properties.extended.instanceView.powerState.displayStatus)
| where OSType == "Windows"'

# Execute query
az graph query -q "$QUERY" --first 1000 -o json > "$TEMP_DIR/phase1_results.json"

# Parse results
TOTAL_VMS=$(jq -r '.data | length' "$TEMP_DIR/phase1_results.json")
HDD_COUNT=$(jq -r '[.data[] | select(.DiskType == "Standard_LRS")] | length' "$TEMP_DIR/phase1_results.json")

echo "  Total Windows VMs found: $TOTAL_VMS"
echo "  VMs with HDD OS disks (Standard_LRS): $HDD_COUNT"
echo ""

# Initialize CSV
echo "VMName,ResourceGroup,DiskType,DiskSizeGB,AllocatedGB,UnallocatedGB,Issue,Details" > "$CSV_FILE"

# Add HDD results to CSV
jq -r '.data[] | select(.DiskType == "Standard_LRS") |
    [.VMName, .ResourceGroup, .DiskType, .DiskSizeGB, "N/A", "N/A", "HDD_OS_DISK", "Standard_LRS (HDD) detected as OS disk"] |
    @csv' "$TEMP_DIR/phase1_results.json" >> "$CSV_FILE"

echo "✅ Phase 1 complete: $HDD_COUNT HDD OS disks detected"
echo ""

# Phase 2: Run Command - Partition Allocation Check
echo "📊 Phase 2: Checking partition allocation on running VMs..."
echo ""

# Get running VMs with SSD OS disks
RUNNING_VMS=$(jq -r '.data[] |
    select(.DiskType != "Standard_LRS") |
    select(.PowerState == "VM running") |
    [.VMName, .ResourceGroup, .DiskType, .DiskSizeGB] |
    @tsv' "$TEMP_DIR/phase1_results.json")

if [[ -z "$RUNNING_VMS" ]]; then
    echo "  ⚠️  No running VMs with SSD OS disks found"
    echo "  Tip: Start VMs and re-run audit for partition allocation check"
    echo ""
else
    VM_COUNT=$(echo "$RUNNING_VMS" | wc -l | tr -d ' ')
    echo "  Running VMs to check: $VM_COUNT"
    echo ""

    # Partition check script
    cat > "$TEMP_DIR/check_partition.ps1" << 'PSEOF'
$disk = Get-Disk | Where-Object {$_.IsBoot -eq $true}
$partition = Get-Partition -DiskNumber $disk.Number | Where-Object {$_.DriveLetter -eq 'C'}
[PSCustomObject]@{
    DiskSizeGB = [math]::Round($disk.Size / 1GB, 2)
    AllocatedGB = [math]::Round($partition.Size / 1GB, 2)
    UnallocatedGB = [math]::Round(($disk.Size - $partition.Size) / 1GB, 2)
} | ConvertTo-Json -Compress
PSEOF

    # Process VMs
    BATCH_NUM=1
    while IFS=$'\t' read -r VM_NAME RG DISK_TYPE DISK_SIZE_GB; do
        echo "  [$BATCH_NUM/$VM_COUNT] Checking $VM_NAME..."

        # Run command
        RESULT=$(az vm run-command invoke \
            --resource-group "$RG" \
            --name "$VM_NAME" \
            --command-id RunPowerShellScript \
            --scripts @"$TEMP_DIR/check_partition.ps1" \
            --query 'value[0].message' \
            -o tsv 2>/dev/null || echo '{"DiskSizeGB":0,"AllocatedGB":0,"UnallocatedGB":0}')

        # Parse JSON result
        ALLOCATED_GB=$(echo "$RESULT" | jq -r '.AllocatedGB // "0"')
        UNALLOCATED_GB=$(echo "$RESULT" | jq -r '.UnallocatedGB // "0"')

        # Check for significant unallocated space (>10GB)
        if (( $(echo "$UNALLOCATED_GB > 10" | bc -l) )); then
            ISSUE="UNALLOCATED_SPACE"
            DETAILS="SSD with ${UNALLOCATED_GB}GB unallocated space"
            echo "    ⚠️  FLAGGED: ${UNALLOCATED_GB}GB unallocated"
        else
            ISSUE="OK"
            DETAILS="Properly configured"
            echo "    ✅ OK: Fully allocated"
        fi

        # Append to CSV
        echo "\"$VM_NAME\",\"$RG\",\"$DISK_TYPE\",$DISK_SIZE_GB,$ALLOCATED_GB,$UNALLOCATED_GB,\"$ISSUE\",\"$DETAILS\"" >> "$CSV_FILE"

        ((BATCH_NUM++)) || true

        # Throttle to avoid Run Command limits (500/hour)
        if (( BATCH_NUM % BATCH_SIZE == 0 )); then
            echo "    (Throttling: 10s pause after $BATCH_SIZE VMs)"
            sleep 10
        fi
    done <<< "$RUNNING_VMS"

    echo ""
    echo "✅ Phase 2 complete: $VM_COUNT VMs checked"
fi

echo ""
echo "📝 Audit Summary"
echo "================"
echo ""

# Count issues
TOTAL_ISSUES=$(tail -n +2 "$CSV_FILE" | grep -v ",OK," | wc -l | tr -d ' ')
HDD_ISSUES=$(grep ",HDD_OS_DISK," "$CSV_FILE" | wc -l | tr -d ' ')
UNALLOC_ISSUES=$(grep ",UNALLOCATED_SPACE," "$CSV_FILE" | wc -l | tr -d ' ')
OK_VMS=$(grep ",OK," "$CSV_FILE" | wc -l | tr -d ' ')

echo "Total VMs audited: $TOTAL_VMS"
echo "Issues found: $TOTAL_ISSUES"
echo "  - HDD OS disks: $HDD_ISSUES"
echo "  - Unallocated space: $UNALLOC_ISSUES"
echo "OK (properly configured): $OK_VMS"
echo ""

# Convert to XLSX if requested
if [[ "$OUTPUT_FORMAT" == "xlsx" ]]; then
    echo "📊 Converting to Excel format..."

    python3 << PYEOF
import csv
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from datetime import datetime

csv_file = "$CSV_FILE"
xlsx_file = "$OUTPUT_FILE"

wb = Workbook()
ws = wb.active
ws.title = "VM Disk Audit"

# Read CSV
with open(csv_file, 'r') as f:
    reader = csv.reader(f)
    for row in reader:
        cleaned_row = [cell.strip('"') for cell in row]
        ws.append(cleaned_row)

# Header formatting
header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
header_font = Font(bold=True, color="FFFFFF", size=11)
border = Border(left=Side(style='thin'), right=Side(style='thin'),
                top=Side(style='thin'), bottom=Side(style='thin'))

for cell in ws[1]:
    cell.fill = header_fill
    cell.font = header_font
    cell.alignment = Alignment(horizontal='center', vertical='center')
    cell.border = border

# Conditional formatting for Issue column
for row_idx in range(2, ws.max_row + 1):
    issue_cell = ws[f'G{row_idx}']

    for col in range(1, 9):
        cell = ws.cell(row=row_idx, column=col)
        cell.border = border
        cell.alignment = Alignment(vertical='center')

    if issue_cell.value == 'HDD_OS_DISK':
        issue_cell.fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
        issue_cell.font = Font(bold=True, color="9C0006")
    elif issue_cell.value == 'UNALLOCATED_SPACE':
        issue_cell.fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
        issue_cell.font = Font(bold=True, color="9C6500")
    elif issue_cell.value == 'OK':
        issue_cell.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
        issue_cell.font = Font(bold=True, color="006100")

# Auto-adjust columns
for col in range(1, ws.max_column + 1):
    max_length = 0
    column = get_column_letter(col)
    for cell in ws[column]:
        try:
            if len(str(cell.value)) > max_length:
                max_length = len(str(cell.value))
        except:
            pass
    ws.column_dimensions[column].width = min(max_length + 2, 50)

ws.freeze_panes = 'A2'

# Summary sheet
summary = wb.create_sheet(title="Summary")
summary['A1'] = "VM Disk Audit Summary"
summary['A1'].font = Font(bold=True, size=14)
summary['A3'] = "Audit Date:"
summary['B3'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

summary['A7'] = "Summary Statistics"
summary['A7'].font = Font(bold=True, size=12)

total_vms = ws.max_row - 1
hdd_count = sum(1 for row in range(2, ws.max_row + 1) if ws[f'G{row}'].value == 'HDD_OS_DISK')
unalloc_count = sum(1 for row in range(2, ws.max_row + 1) if ws[f'G{row}'].value == 'UNALLOCATED_SPACE')
ok_count = sum(1 for row in range(2, ws.max_row + 1) if ws[f'G{row}'].value == 'OK')

summary['A9'] = "Total VMs Audited:"
summary['B9'] = total_vms
summary['A10'] = "HDD OS Disks:"
summary['B10'] = hdd_count
summary['B10'].fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
summary['A11'] = "Unallocated Space:"
summary['B11'] = unalloc_count
summary['B11'].fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
summary['A12'] = "OK (Properly Configured):"
summary['B12'] = ok_count
summary['B12'].fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
summary['A14'] = "Total Issues:"
summary['B14'] = hdd_count + unalloc_count
summary['B14'].font = Font(bold=True)

for col in ['A', 'B']:
    summary.column_dimensions[col].width = 30

wb.save(xlsx_file)
PYEOF

    if [[ $? -eq 0 ]]; then
        echo "   ✅ Excel file created"
        # Clean up CSV file
        rm -f "$CSV_FILE"
    else
        echo "   ⚠️  Excel conversion failed, keeping CSV"
        OUTPUT_FILE="$CSV_FILE"
    fi
fi

echo ""
echo "✅ Audit complete!"
echo "📄 Results saved to: $OUTPUT_FILE"
echo ""

# Show flagged VMs
if (( TOTAL_ISSUES > 0 )); then
    echo "⚠️  Flagged VMs:"
    echo ""
    if [[ "$OUTPUT_FORMAT" == "csv" ]]; then
        column -t -s ',' "$CSV_FILE" | grep -v ",OK," | head -20
    else
        echo "   Open $OUTPUT_FILE in Excel to view details"
    fi
fi
