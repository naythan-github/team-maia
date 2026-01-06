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

## References

- **Azure CLI Docs**: https://docs.microsoft.com/en-us/cli/azure/
- **Cost Management**: https://portal.azure.com/#view/Microsoft_Azure_CostManagement
- **Activity Log**: https://portal.azure.com/#view/Microsoft_Azure_ActivityLog
