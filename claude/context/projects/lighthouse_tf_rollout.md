# Azure Lighthouse Terraform Rollout - MCP Customer Migration

**Sprint ID**: SPRINT-LIGHTHOUSE-TF-001
**Status**: INFRASTRUCTURE COMPLETE - Configuration Pending
**Created**: 2026-01-15
**Updated**: 2026-01-15
**Priority**: HIGH (foundation for AMA migration)
**Progress**: Phase 1-2 Complete, Phase 3-6 Pending

---

## Executive Summary

Roll out Azure Lighthouse to 100+ MCP customers using Terraform, enabling centralized management for the Azure Monitor Agent (AMA) migration and all future Azure operations.

**Business Driver**: MMA (Microsoft Monitoring Agent) was deprecated August 2024. Customers need migration to AMA. GDAP alone doesn't scale for 100+ customers - Lighthouse provides single pane of glass.

---

## Background & Research

### Why Lighthouse + Terraform

| Factor | Decision |
|--------|----------|
| **Current State** | GDAP access only, no Lighthouse |
| **Scale** | 100+ MCP customers |
| **Terraform Priority** | Orro making TF workflows a priority |
| **Complexity** | Low - good first Terraform project |

### MMA → AMA Migration Context

- **MMA Deprecated**: August 31, 2024
- **Ingestion Support End**: February 1, 2025
- **Replacement**: Azure Monitor Agent (AMA) with Data Collection Rules (DCRs)
- **Deployment Method**: Azure Policy (DeployIfNotExists) via Lighthouse

### Why Lighthouse First

1. Single pane of glass for all customers
2. One Azure Policy assignment covers all delegated subscriptions
3. Foundation for future Azure operations (patching, security, compliance)
4. Build once, use forever

---

## Architecture

### Terraform Structure

```
orro-lighthouse/
├── modules/
│   └── lighthouse-offer/
│       ├── main.tf          # Definition + assignment
│       ├── variables.tf     # Tenant ID, roles, groups
│       └── outputs.tf
├── environments/
│   ├── customers.tfvars     # List of customer subscriptions
│   └── orro.tfvars          # Orro tenant details
├── main.tf                  # Calls module per customer
├── providers.tf
└── backend.tf               # State storage (Azure Storage)
```

### Key Terraform Resources

```hcl
azurerm_lighthouse_definition    # The managed service offer
azurerm_lighthouse_assignment    # Applies offer to customer subscription
```

### RBAC Role Design

| Orro Security Group | Azure Role | Purpose |
|---------------------|------------|---------|
| `Orro-AzureOps` | Contributor | Deploy AMA, manage resources |
| `Orro-Monitoring` | Monitoring Contributor | DCRs, alerts, dashboards |
| `Orro-ReadOnly` | Reader | Visibility without changes |

### State Management Strategy

**Recommendation**: Single state file initially
- 100 customers × 2 resources = 200 resources
- Manageable in single state
- Optimize later if performance degrades

---

## Implementation Phases

### Phase 1: Terraform Foundation ✅ COMPLETE

- [x] Set up Terraform repo (`orro-lighthouse`) - Location: `~/work_projects/orro-lighthouse`
- [x] Configure Azure Storage backend for state - Template ready in backend.tf
- [x] Create module structure - Complete with modules/lighthouse-offer/
- [x] Define Orro tenant variables (tenant ID, security group IDs) - Tenant ID discovered, group IDs pending

### Phase 2: Lighthouse Module ✅ COMPLETE

- [x] Create `azurerm_lighthouse_definition` resource
- [x] Define role assignments (Contributor, Monitoring Contributor, Reader)
- [x] Create `azurerm_lighthouse_assignment` resource
- [ ] Test on single customer subscription - Pending customer data

### Phase 3: Customer Inventory

- [ ] Export list of all MCP customer subscriptions
- [ ] Create `customers.tfvars` with subscription IDs
- [ ] Validate GDAP access to each subscription

### Phase 4: Pilot Rollout

- [ ] Deploy to 5-10 pilot customers
- [ ] Validate Lighthouse access works
- [ ] Test cross-tenant resource visibility
- [ ] Document any issues

### Phase 5: Full Rollout

- [ ] Phased deployment (10% → 50% → 100%)
- [ ] Monitor for failures
- [ ] Document customer-specific exceptions

### Phase 6: AMA Deployment (Post-Lighthouse)

- [ ] Create Data Collection Rules (DCRs)
- [ ] Assign AMA Azure Policy initiative via Lighthouse
- [ ] Run remediation tasks for existing VMs
- [ ] Validate AMA deployment
- [ ] Plan MMA removal

---

## Required Information

| Item | Status | Value |
|------|--------|-------|
| Orro Managing Tenant ID | ✅ FOUND | `7e0c3f88-faec-4a28-86ad-33bfe7c4b326` |
| Orro-AzureOps Security Group ID | PENDING | Recommendation: Use Orro CSG DevOps Team (3f6e871b-b82d-47e3-8f12-ae0bc54bcaec) |
| Orro-Monitoring Security Group ID | PENDING | Needs creation or mapping to existing group |
| Orro-ReadOnly Security Group ID | PENDING | Needs creation or mapping to existing group |
| Azure Storage Account for TF state | OPTIONS | Existing: costoptimizersapmtw752k OR create: orrolighthousestate |
| Customer subscription list | NEEDED | Export from Partner Center |

---

## Key Decisions Made

1. **Terraform over ARM**: Aligns with Orro's TF priority, better for ongoing management
2. **Lighthouse before AMA**: Foundation first, enables everything else
3. **Contributor access**: Full resource management capability
4. **Single state file**: Start simple, optimize if needed
5. **Phased rollout**: Pilot → 10% → 50% → 100%

---

## Sources & References

- [Azure Lighthouse Overview](https://learn.microsoft.com/en-us/azure/lighthouse/overview)
- [Deploy Azure Policy at scale via Lighthouse](https://learn.microsoft.com/en-us/azure/lighthouse/how-to/policy-at-scale)
- [GDAP Introduction](https://learn.microsoft.com/en-us/partner-center/customers/gdap-introduction)
- [Migrate to Azure Monitor Agent](https://learn.microsoft.com/en-us/azure/azure-monitor/agents/azure-monitor-agent-migration)
- [Cross-tenant management with Lighthouse](https://learn.microsoft.com/en-us/azure/lighthouse/concepts/cross-tenant-management-experience)

---

## Success Criteria

| Metric | Target |
|--------|--------|
| Lighthouse onboarded | 100% of MCP customers |
| Cross-tenant visibility | All subscriptions visible from Orro tenant |
| AMA deployment ready | Policy can be assigned at scale |
| Terraform state | Clean, versioned, backed up |

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Customer rejects Lighthouse | Document, handle manually via GDAP |
| GDAP permissions insufficient | Verify roles before starting |
| Terraform state corruption | Azure Storage with versioning + backups |
| Too many customers at once | Phased rollout with validation gates |

---

## Restart Prompt

See `upnext.md` for the restart prompt to continue this project.
