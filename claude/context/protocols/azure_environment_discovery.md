# Azure Environment Discovery Protocol

## Quick Reference Commands

### List All Accessible Subscriptions
```bash
az account list --output table
```

### Check Current Default Subscription
```bash
az account show --output table
```

### Switch Subscription Context
```bash
az account set --subscription "subscription-name-or-id"
```

### Identify Environment Type
- **Sandbox/Dev**: Contains "dev", "test", "sandbox" in subscription name or resource group names
- **Customer**: Customer name in subscription (e.g., "Aus-E-Mart")
- **Internal/Orro**: "Visual Studio", "ORRO", "Orrogroup" tenant domain

## Environment Inventory (Updated 2026-01-07)

### Orro Internal Environments

| Environment | Subscription Name | Subscription ID | Tenant | Purpose |
|-------------|-------------------|-----------------|--------|---------|
| **Sandbox/Dev** | Visual Studio Enterprise Subscription – MPN | 9b8e7b3f-d3e7-4da9-a22a-9bf7c8ee4dde | ORRO PTY LTD (Orrogroup.onmicrosoft.com) | Development, testing, script validation ($150/month credits, default subscription) |
| Resource Group | dev-rg | - | - | Primary sandbox resource group |

### Customer Environments

| Customer | Subscription Name | Subscription ID | Tenant | Notes |
|----------|-------------------|-----------------|--------|-------|
| Aus-E-Mart | Aus-E-Mart | 3681c5eb-0e60-4beb-96fa-0a067f6969ac | 63dff77c-b5c0-4308-85b0-d14caf72a671 | Production |
| Aus-E-Mart | Aus-E-Mart Dev Sub 1 | 5c5eaea6-1f2c-4d3b-9651-8c50bd6a4656 | 63dff77c-b5c0-4308-85b0-d14caf72a671 | Development |

## Discovery Workflow

### Step 1: Initial Context Check
```bash
az account show --query "{User:user.name, Subscription:name, Tenant:tenantDisplayName}" -o table
```

### Step 2: List All Accessible Environments
```bash
az account list --query "[].{Name:name, ID:id, Tenant:tenantDisplayName, TenantDomain:tenantDefaultDomain, State:state}" -o table
```

### Step 3: Inventory Resources per Environment
```bash
az account set --subscription "subscription-id"
az group list --query "[].{Name:name, Location:location}" -o table
```

### Step 4: Identify Sandbox
**Characteristics**:
- Subscription name contains: "Visual Studio", "Dev", "Test", "Sandbox"
- Tenant domain: Orrogroup.onmicrosoft.com
- Resource groups: dev-rg, test-rg, sandbox-rg patterns
- Low resource count (development workloads only)

### Step 5: Identify Customer Environments
**Characteristics**:
- Subscription name = Customer name
- Different tenant ID (not Orrogroup)
- Production resource groups (prod-rg, production, etc.)
- Higher resource counts

## Multi-Tenant Safety Protocol

### Before Running Scripts Across Environments

1. **Verify subscription context**:
```bash
az account show --query "name" -o tsv
```

2. **Use explicit subscription parameters**:
```bash
# GOOD - explicit subscription
az vm list --subscription "9b8e7b3f-d3e7-4da9-a22a-9bf7c8ee4dde"

# BAD - relies on default context
az vm list
```

3. **Confirm with user before cross-tenant operations**:
```
User, I'm about to run this script against:
- Subscription: Aus-E-Mart (3681c5eb...)
- Tenant: Customer Tenant XYZ
- Estimated impact: 150 VMs
Proceed? (y/n)
```

## Sandbox Access

**Account**: naythan.dawe@orro.group
**Subscription**: Visual Studio Enterprise Subscription – MPN (9b8e7b3f-d3e7-4da9-a22a-9bf7c8ee4dde)
**Tenant**: ORRO PTY LTD (Orrogroup.onmicrosoft.com)
**Tenant ID**: 7e0c3f88-faec-4a28-86ad-33bfe7c4b326
**Resource Group**: dev-rg
**Credits**: $150 USD/month (Azure credits for testing and development)
**Status**: Default subscription (set via `az account set`)

**Login**:
```bash
az login --tenant 7e0c3f88-faec-4a28-86ad-33bfe7c4b326
az account set --subscription "9b8e7b3f-d3e7-4da9-a22a-9bf7c8ee4dde"
```

## Testing Protocol

### Before Running Scripts on Customer Environments

1. **Test in sandbox first**:
```bash
az account set --subscription "9b8e7b3f-d3e7-4da9-a22a-9bf7c8ee4dde"
./script.ps1 -ResourceGroupName "dev-rg" -WhatIf
```

2. **Deploy test VMs if needed**:
- Tag with `Environment=Test`, `AutoDelete=True`
- Set auto-shutdown schedules
- Document test VM configurations

3. **Validate script behavior**:
- Check error handling
- Verify output format
- Test throttling limits

4. **Get approval before customer execution**

## Environment-Specific Considerations

### Sandbox (dev-rg)
- **Purpose**: Script testing, validation, proof-of-concept
- **Existing VMs**: win11-vscode (deallocated, Premium SSD)
- **Auto-cleanup**: Enabled (auto-shutdown schedules)
- **Budget**: $150 USD/month Azure credits (current usage: ~$40/month)
- **Available for testing**: ~$110/month remaining credit
- **Safe for**: Breaking changes, Run Command testing, configuration experiments

### Customer Environments
- **Purpose**: Production workloads, managed services
- **Safety requirements**:
  - WhatIf mode mandatory first
  - Approval required
  - Outside business hours preferred
  - Rollback plan documented
- **Throttling**: 500 Run Commands/hour limit per subscription

## Updating This Documentation

When new environments are added:
1. Run discovery workflow
2. Update environment inventory table
3. Document any environment-specific notes
4. Update safety protocols if needed
5. Sync to capabilities database

**Last Updated**: 2026-01-07
**Maintained By**: Azure Operations Engineer Agent / SRE Principal Engineer
