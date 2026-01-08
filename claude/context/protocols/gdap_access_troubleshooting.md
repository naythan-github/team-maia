# GDAP Access Troubleshooting Protocol

## Overview

GDAP (Granular Delegated Admin Privileges) allows Orro to manage customer Microsoft 365 and Azure tenants. This protocol covers diagnosing and resolving GDAP access issues.

## How GDAP Works

```
┌─────────────────────────────────────────────────────────────────────┐
│  GDAP Access Chain                                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. SECURITY GROUP created in Orro's Entra ID                       │
│     (e.g., "GDAP-CustomerName-Admins")                              │
│                              │                                      │
│                              ▼                                      │
│  2. Security group LINKED to GDAP relationship in Partner Center    │
│     (defines which customer tenant)                                 │
│                              │                                      │
│                              ▼                                      │
│  3. ROLES assigned to the GDAP relationship                         │
│     (e.g., "Global Reader", "Cloud Device Admin", etc.)             │
│                              │                                      │
│                              ▼                                      │
│  4. USER added to the security group                                │
│     (grants access to customer tenant with those roles)             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## GDAP vs Direct Account

| Access Type | Description | Use Case |
|-------------|-------------|----------|
| **GDAP** | Access customer tenant via Orro credentials | Standard partner access |
| **Direct Account** | Separate account in customer tenant | Full integration, CA policies apply |

## Diagnosis Commands

### Step 1: Check Current Authentication

```bash
# Who am I logged in as?
az account show -o json | jq '{user: .user.name, tenant: .tenantDisplayName}'

# What subscriptions can I see?
az account list --all -o table
```

### Step 2: Check GDAP Group Membership (Orro Tenant)

```bash
# Login to Orro tenant
az login --tenant "Orrogroup.onmicrosoft.com"

# List groups you're a member of
az rest --method GET --url "https://graph.microsoft.com/v1.0/me/memberOf" -o json | \
  jq -r '.value[] | select(.["@odata.type"] == "#microsoft.graph.group") | .displayName'

# Search for GDAP-related groups
az rest --method GET --url "https://graph.microsoft.com/v1.0/me/memberOf" -o json | \
  jq -r '.value[] | select(.displayName | test("gdap|partner|csp|admin"; "i")) | .displayName'
```

### Step 3: Check GDAP Relationships

```bash
# Query delegated admin relationships (requires Partner Center permissions)
az rest --method GET --url "https://graph.microsoft.com/v1.0/tenantRelationships/delegatedAdminRelationships" -o json
```

### Step 4: Test Customer Tenant Access

```bash
# Try to login to customer tenant via GDAP
az login --tenant "<customer-tenant-id>"

# Or with explicit subscription listing
az account list --all -o table
```

## Common Issues

### Issue 1: No Customer Tenants Visible

**Symptom**: `az account list` only shows Orro subscriptions

**Causes**:
1. Not added to GDAP security group
2. GDAP relationship doesn't include Azure (M365 only)
3. Need to refresh token after being added to group

**Resolution**:
```bash
# Force token refresh
az logout
az login

# Check if customer tenants now visible
az account list --all -o table
```

If still not visible, contact Partner Center admin to verify:
- You're in the correct security group
- The GDAP relationship includes Azure roles

### Issue 2: Conditional Access Blocking (AADSTS53003)

**Symptom**:
```
ERROR: AADSTS53003: Access has been blocked by Conditional Access policies
Device state: Unregistered
```

**Cause**: Customer tenant requires compliant/registered devices

**Diagnosis**:
- Check error details for "Device state: Unregistered"
- Note the IP address being blocked
- Check if using Azure CLI vs Azure Portal

**Resolution Options**:

| Option | Description |
|--------|-------------|
| Request CA exception | Ask customer to add exception for your user/IP/app |
| Use managed device | Access from customer-managed VM or device |
| Use Azure Portal | Browser may have different CA rules |
| Register device | If allowed, register Mac via Company Portal |

### Issue 3: No Azure Subscriptions (M365 Only)

**Symptom**: Login succeeds but "No subscriptions found"

**Cause**: GDAP relationship only covers M365, not Azure

**Resolution**:
```bash
# Login with tenant-level access (no subscriptions needed)
az login --tenant "<customer-tenant-id>" --allow-no-subscriptions

# Can still query Entra ID / Graph API
az rest --method GET --url "https://graph.microsoft.com/v1.0/users"
```

For Azure access, request Azure Lighthouse onboarding instead.

### Issue 4: Direct Account with CA Blocking

**Symptom**: Have `user@customer.com` account but CA blocks CLI access

**Example**: NW Computing tenant blocks unregistered devices

**Resolution Options**:
1. **Azure Portal**: Try browser at `https://portal.azure.com/#@customer.com`
2. **Request Exception**: Ask customer IT for CA policy modification
3. **Use Customer Device**: Access from registered/compliant device

## GDAP Roles for Azure Access

| Role | Purpose | Minimum for |
|------|---------|-------------|
| Reader | View resources | Metrics, resource enumeration |
| Monitoring Reader | View metrics/alerts | Performance investigation |
| Log Analytics Reader | Query Log Analytics | Advanced log queries |
| Virtual Machine Contributor | Manage VMs | Run Command execution |
| Contributor | Full resource management | Most operational tasks |

## GDAP vs Azure Lighthouse

| Feature | GDAP | Azure Lighthouse |
|---------|------|------------------|
| M365 access | Yes | No |
| Azure access | Limited | Full |
| Persistent cross-tenant | Session-based | Native |
| Granular Azure RBAC | Limited roles | Full RBAC |
| Scale (100+ tenants) | Tedious | Designed for scale |
| PIM/JIT elevation | No | Yes |

**Recommendation**: For heavy Azure operations, request Azure Lighthouse in addition to GDAP.

## Partner Center Access

View GDAP relationships at:
```
https://partner.microsoft.com/dashboard/commerce/granularpermissions/list
```

## Related Documentation

- [Azure Environment Discovery](azure_environment_discovery.md)
- [Azure VM Performance Investigation](azure_vm_performance_investigation.md)

---

**Last Updated**: 2026-01-08
**Maintained By**: Azure Operations Engineer Agent
