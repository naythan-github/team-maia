# Azure Access Configuration

## Overview
Azure subscription access for Maia agents using persisted Azure CLI authentication.

**Last Updated**: 2026-01-06
**Authentication Method**: Azure CLI with persisted tokens
**Verification Status**: ✅ Active

---

## Subscription Details

| Property | Value |
|----------|-------|
| **Subscription Name** | Visual Studio Enterprise Subscription – MPN |
| **Subscription ID** | `9b8e7b3f-d3e7-4da9-a22a-9bf7c8ee4dde` |
| **Tenant** | ORRO PTY LTD |
| **Tenant ID** | `7e0c3f88-faec-4a28-86ad-33bfe7c4b326` |
| **User** | naythan.dawe@orro.group |
| **Credit Type** | Visual Studio Enterprise ($150/month) |
| **Default** | Yes |

---

## Authentication Method

### Approach: Persisted Azure CLI Login

**Why This Method**:
- ✅ Standard Azure pattern, minimal complexity
- ✅ Tokens auto-refresh (long-lived sessions)
- ✅ No credential storage in code/config
- ✅ Works for both CLI and Python SDK

**Token Location**: `~/.azure/`
**Token Lifetime**: ~90 days (auto-refresh)

### Initial Authentication (One-Time)

```bash
# Login with device code
az login --use-device-code

# Verify subscription is set as default
az account show

# Set subscription explicitly (if needed)
az account set --subscription "9b8e7b3f-d3e7-4da9-a22a-9bf7c8ee4dde"
```

### Re-Authentication (When Tokens Expire)

```bash
# Check current auth status
az account show

# If expired, re-authenticate
az login --use-device-code
```

---

## Agent Discovery Protocol

### For New Agents/Contexts

When an agent needs Azure access:

1. **Check auth status**:
   ```bash
   python3 claude/tools/cloud/azure_auth_helper.py status
   ```

2. **If authenticated**: Proceed with Azure operations

3. **If not authenticated**:
   ```bash
   az login --use-device-code
   az account set --subscription "9b8e7b3f-d3e7-4da9-a22a-9bf7c8ee4dde"
   ```

4. **Verify access**:
   ```bash
   az account show
   az group list --output table
   ```

---

## Cost Management

### Budget Configuration

**Budget Name**: VS-Enterprise-Monthly-Budget
**Amount**: $150 USD/month
**Alert Threshold**: 50% ($75)
**Alert Contact**: naythan.dawe@orro.group
**Status**: ✅ Active (created 2026-01-06)

**Creation Method**: Azure REST API (2019-05-01 version)

**Automated Budget Creation**:
```bash
ACCESS_TOKEN=$(az account get-access-token --query accessToken -o tsv)

curl -X PUT \
  "https://management.azure.com/subscriptions/9b8e7b3f-d3e7-4da9-a22a-9bf7c8ee4dde/providers/Microsoft.Consumption/budgets/VS-Enterprise-Monthly-Budget?api-version=2019-05-01" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "properties": {
      "category": "Cost",
      "amount": 150,
      "timeGrain": "Monthly",
      "timePeriod": {
        "startDate": "2026-01-01T00:00:00Z",
        "endDate": "2030-12-31T23:59:59Z"
      },
      "notifications": {
        "Actual_GreaterThan_50_Percent": {
          "enabled": true,
          "operator": "GreaterThan",
          "threshold": 50,
          "contactEmails": ["naythan.dawe@orro.group"],
          "thresholdType": "Actual"
        }
      }
    }
  }'
```

**Note**: Must use `api-version=2019-05-01` (newer versions have filter requirements)

### Cost Monitoring

```bash
# Check current spend
az consumption usage list --start-date "2026-01-01" --end-date "2026-01-31"

# Check budget status
az consumption budget list --output table

# Detailed budget info (JSON)
az consumption budget list --output json
```

---

## Resource Organization

### Resource Group Strategy

**Approach**: Create as needed (no default RG)

**Naming Convention**: TBD based on project requirements

**Example**:
```bash
# Create project-specific resource group
az group create --name "maia-dev-rg" --location "australiaeast"
```

---

## Common Operations

### List Resources

```bash
# List all resource groups
az group list --output table

# List resources in a group
az resource list --resource-group "maia-dev-rg" --output table
```

### Python SDK Usage

```python
from azure.identity import AzureCliCredential
from azure.mgmt.resource import ResourceManagementClient

# Uses persisted CLI credentials automatically
credential = AzureCliCredential()
subscription_id = "9b8e7b3f-d3e7-4da9-a22a-9bf7c8ee4dde"

client = ResourceManagementClient(credential, subscription_id)
for rg in client.resource_groups.list():
    print(rg.name)
```

---

## Troubleshooting

### Token Expired

**Symptom**: Commands fail with authentication errors

**Solution**:
```bash
az login --use-device-code
```

### Wrong Subscription Selected

**Symptom**: Resources not found

**Solution**:
```bash
# Check current subscription
az account show

# Switch to VS Enterprise subscription
az account set --subscription "9b8e7b3f-d3e7-4da9-a22a-9bf7c8ee4dde"
```

### Multiple Tenants

**Note**: Authentication warnings about "NW Computing" tenant are expected and can be ignored. The VS Enterprise subscription is in the ORRO PTY LTD tenant.

---

## Security Considerations

1. **Token Storage**: Tokens stored in `~/.azure/` (standard Azure practice)
2. **Scope**: Full subscription access (personal dev subscription)
3. **Rotation**: Automatic via token refresh
4. **Audit**: All operations logged to Azure Activity Log

---

## Helper Tools

- **Auth Status Check**: `claude/tools/cloud/azure_auth_helper.py`
- **Cost Monitoring**: Via Azure Portal Cost Management
- **Resource Discovery**: `az resource list`

---

---

## Environment Assessment (Completed 2026-01-06)

### Subscription Type & Limitations

**Type**: Visual Studio Enterprise Subscription (MSDN)
**Primary Use**: Development and testing only

**Critical Limitation**: **Spending Limit Active**
- **Impact**: When $150/month credit exhausted, all resources suspend
- **Cannot be disabled**: MSDN subscription restriction
- **Mitigation**: Budget alert at 50%, auto-shutdown on VMs
- **Recommendation**: Not suitable for production workloads

### Permissions & Governance

| Assessment Area | Status | Details |
|----------------|--------|---------|
| **RBAC Role** | ✅ Owner | Full subscription permissions |
| **Azure Policy** | ✅ None | No organizational restrictions |
| **Regional Access** | ✅ All regions | 98+ Azure regions available |
| **Resource Providers** | ✅ Auto-register | Providers register on first use |
| **VM SKU Availability** | ⚠️ Some limits | Legacy B1s/B2s unavailable, use v2 SKUs |
| **vCPU Quota** | ✅ Sufficient | ~20 vCPUs/region (MSDN standard) |

### Successfully Tested Resources

All resource types successfully deployed and tested:
- ✅ Resource Groups
- ✅ Virtual Machines (Standard_B2als_v2, Standard_B4als_v2)
- ✅ Storage Accounts (Standard_LRS, StorageV2)
- ✅ Virtual Networks + Subnets
- ✅ Network Security Groups
- ✅ Public IP Addresses
- ✅ Managed Disks

**Verdict**: Fully functional for development/testing, no significant restrictions beyond spending limit.

---

## Windows VM Deployment Guide

### VS Enterprise Licensing Benefits

**Included with your subscription** (no additional cost):
- ✅ **Windows 11 Enterprise** - $0 license cost for dev/test
- ✅ **Windows 10 Enterprise** - $0 license cost for dev/test
- ✅ **Windows Server** - Reduced dev/test pricing (~60% discount)
- ✅ **SQL Server Developer** - Free
- ✅ **Visual Studio 2022 Enterprise** - Pre-installed images available

**Cost Comparison** (Standard_B4als_v2, Australia East):
- Windows 11 Enterprise: ~$55/month (same as Linux, $0 OS license)
- Windows Server 2022: ~$70/month (~$15/month OS license)
- Ubuntu Linux: ~$55/month ($0 OS license)

### Recommended Windows 11 Images

| Image SKU | Description | Use Case | Pre-installed Tools |
|-----------|-------------|----------|---------------------|
| `win11-23h2-ent` | Plain Windows 11 Enterprise | Lightweight dev, custom setup | None |
| `vs-2022-ent-general-win11-m365-gen2` | Full VS 2022 Enterprise | Heavy development | VS 2022, VS Code, Git, Azure CLI, M365 |
| `vs-latest-ent-win11-m365-gen2` | Latest VS Enterprise | Always current | VS 2022, VS Code, Git, Azure CLI, M365 |

### Deploy Windows 11 VM with VS Code (Automated)

**Option 1: Plain Windows 11 + Auto-Install VS Code** (Recommended)

```bash
# Create resource group
az group create --name "dev-rg" --location "australiaeast"

# Deploy VM
az vm create \
  --resource-group "dev-rg" \
  --name "win11-dev" \
  --image "MicrosoftWindowsDesktop:windows-11:win11-23h2-ent:latest" \
  --size "Standard_B4als_v2" \
  --admin-username "azureuser" \
  --admin-password "YourSecurePassword123!" \
  --location "australiaeast" \
  --public-ip-sku "Standard" \
  --nsg-rule "RDP"

# Install VS Code via run command
az vm run-command invoke \
  --resource-group "dev-rg" \
  --name "win11-dev" \
  --command-id "RunPowerShellScript" \
  --scripts "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://update.code.visualstudio.com/latest/win32-x64-user/stable' -OutFile C:\vscode.exe; Start-Process -FilePath C:\vscode.exe -Args '/VERYSILENT /NORESTART /MERGETASKS=desktopicon,addcontextmenufiles,addtopath' -Wait"

# Configure auto-shutdown (7 PM daily)
az vm auto-shutdown \
  --resource-group "dev-rg" \
  --name "win11-dev" \
  --time "1900" \
  --location "australiaeast" \
  --email "naythan.dawe@orro.group"
```

**Cost**: ~$55/month (or ~$18/month with 8hr/day auto-shutdown)

**Option 2: Full VS 2022 Image** (VS Code pre-installed)

```bash
az vm create \
  --resource-group "dev-rg" \
  --name "win11-vs2022" \
  --image "MicrosoftVisualStudio:visualstudio2022:vs-2022-ent-general-win11-m365-gen2:latest" \
  --size "Standard_D4as_v5" \
  --admin-username "azureuser" \
  --admin-password "YourSecurePassword123!" \
  --location "australiaeast"
```

**Cost**: ~$120/month (requires larger VM for VS 2022)

### VM Size Recommendations

| Use Case | Recommended Size | vCPU/RAM | Monthly Cost | Notes |
|----------|-----------------|----------|--------------|-------|
| VS Code only | Standard_B2als_v2 | 2/4GB | ~$30 | Budget option |
| VS Code + Light Dev | Standard_B4als_v2 | 4/8GB | ~$55 | Recommended |
| Visual Studio 2022 | Standard_D4as_v5 | 4/16GB | ~$120 | Minimum for VS |
| Heavy Development | Standard_D8as_v5 | 8/32GB | ~$240 | High performance |

**Note**: Use auto-shutdown to reduce costs by 60-70% (8 hours/day usage)

---

## Security Configuration

### Network Security Groups (NSG)

**Current Configuration** (win11-vscode VM):
- **Allowed Source IP**: 115.70.58.231/32 (home IP only)
- **Allowed Port**: 3389 (RDP)
- **Protocol**: TCP
- **Access**: Inbound only from whitelisted IP

**Update NSG Rule** (when IP changes):
```bash
az network nsg rule update \
  --resource-group "dev-rg" \
  --nsg-name "win11-vscodeNSG" \
  --name "RDP" \
  --source-address-prefixes "NEW_IP/32"
```

**Add Multiple IPs** (home + office):
```bash
az network nsg rule update \
  --resource-group "dev-rg" \
  --nsg-name "win11-vscodeNSG" \
  --name "RDP" \
  --source-address-prefixes "HOME_IP/32" "OFFICE_IP/32"
```

**Security Best Practices**:
1. ✅ IP whitelisting (implemented)
2. ✅ Auto-shutdown (reduces attack window + saves cost)
3. ✅ Strong passwords (20+ characters recommended)
4. ✅ Budget alerts (spending limit protection)
5. ⚠️ Consider: Microsoft Defender for Cloud (adds ~$15/month)

---

## Current Deployed Resources

### Active Resources (as of 2026-01-06)

**Resource Group**: `dev-rg`
- **Location**: Australia East
- **Tags**: `purpose=development`, `owner=naythan.dawe@orro.group`

**Virtual Machine**: `win11-vscode`
- **Size**: Standard_B4als_v2 (4 vCPU, 8GB RAM)
- **OS**: Windows 11 Enterprise (23H2)
- **Public IP**: 4.147.176.243
- **Private IP**: 10.0.0.5
- **Status**: Running
- **Auto-shutdown**: Enabled (7 PM UTC daily)
- **Security**: IP whitelisted (115.70.58.231/32)
- **Installed Software**: VS Code (via automated installation)

**Cost Estimate** (with auto-shutdown):
- VM Compute: ~$18/month (8 hrs/day)
- OS Disk (30GB): ~$4/month
- Public IP: ~$3/month
- **Total**: ~$25/month

### Management Commands

**Get VM Status**:
```bash
az vm show --resource-group "dev-rg" --name "win11-vscode" --show-details --query "powerState"
```

**Start VM**:
```bash
az vm start --resource-group "dev-rg" --name "win11-vscode"
```

**Stop VM** (deallocate to save costs):
```bash
az vm stop --resource-group "dev-rg" --name "win11-vscode"
az vm deallocate --resource-group "dev-rg" --name "win11-vscode"
```

**Get Connection Details**:
```bash
az vm show --resource-group "dev-rg" --name "win11-vscode" --show-details --query "{Name:name, PowerState:powerState, PublicIP:publicIps, PrivateIP:privateIps}"
```

**Delete VM** (cleanup):
```bash
# Delete entire resource group
az group delete --name "dev-rg" --yes --no-wait
```

**Update NSG Security Rule**:
```bash
# Get current public IP
curl -s ifconfig.me

# Update NSG to allow your current IP
az network nsg rule update \
  --resource-group "dev-rg" \
  --nsg-name "win11-vscodeNSG" \
  --name "RDP" \
  --source-address-prefixes "$(curl -s ifconfig.me)/32"
```

---

## Quick Reference for Future Agents

### Pre-Flight Checklist

Before working with Azure resources:

1. **Check authentication**:
   ```bash
   python3 claude/tools/cloud/azure_auth_helper.py status
   ```

2. **Verify subscription**:
   ```bash
   az account show --query "{Name:name, ID:id, State:state}"
   ```

3. **Check budget status**:
   ```bash
   az consumption budget list --output table
   ```

4. **List current resources**:
   ```bash
   az group list --output table
   az vm list --output table
   ```

### Common Scenarios

**Scenario 1: Deploy new development VM**
1. Choose VM size based on workload (see recommendations above)
2. Use Windows 11 Enterprise image (no license cost)
3. Configure auto-shutdown (saves 60-70% cost)
4. Apply IP whitelisting for security
5. Estimated time: 5-10 minutes

**Scenario 2: Access existing VM**
1. Check VM status: `az vm show --resource-group dev-rg --name win11-vscode --show-details`
2. Start if stopped: `az vm start --resource-group dev-rg --name win11-vscode`
3. Get public IP from output
4. RDP connection: `mstsc /v:<PUBLIC_IP>`
5. Credentials: azureuser / VSCode2026!SecurePass

**Scenario 3: Cost optimization**
1. Review current spend: `az consumption usage list`
2. Check VM sizes: Downsize if underutilized
3. Enable auto-shutdown if not configured
4. Deallocate VMs when not in use (stops billing)
5. Delete unused resource groups

### Important Notes for Agents

**DO**:
- ✅ Use `az account show` to verify correct subscription before operations
- ✅ Check budget before deploying expensive resources
- ✅ Apply tags to all resources (`owner`, `purpose`, `environment`)
- ✅ Use B-series v2 or D-series v5 SKUs (avoid legacy v1 SKUs)
- ✅ Enable auto-shutdown on dev VMs
- ✅ Deallocate VMs when done to save costs

**DON'T**:
- ❌ Deploy production workloads (spending limit will suspend resources)
- ❌ Use legacy VM SKUs (B1s, B2s - use B2als_v2, B4als_v2 instead)
- ❌ Leave VMs running 24/7 without auto-shutdown (wastes budget)
- ❌ Expose RDP to 0.0.0.0/0 (always use IP whitelisting)
- ❌ Exceed $75/month without user approval (50% budget threshold)

---

## References

- **Azure CLI Docs**: https://docs.microsoft.com/en-us/cli/azure/
- **Cost Management**: https://portal.azure.com/#view/Microsoft_Azure_CostManagement
- **Activity Log**: https://portal.azure.com/#view/Microsoft_Azure_ActivityLog
- **VM Pricing**: https://azure.microsoft.com/en-us/pricing/details/virtual-machines/windows/
- **VS Subscription Benefits**: https://visualstudio.microsoft.com/subscriptions/
