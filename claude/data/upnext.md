# Up Next - Pending Projects

Projects queued for implementation after approval.

---

## 1. /finish Skill Fix-Forward (HIGH PRIORITY)
**Sprint ID**: SPRINT-FINISH-FIXFORWARD-001
**Status**: READY TO EXECUTE
**Plan**: `claude/data/project_status/active/FINISH_SKILL_FIX_FORWARD.md`
**Estimated Effort**: 15-45 minutes

### Summary
Fix-forward issues from `/finish` skill implementation:
- Commit all sprint changes (`save state`)
- Fix capability check to exclude `claude/commands/*.md`
- Fix SessionManager attribute name in learning check
- (Optional) Create stub tests for pre-existing tools

### To Start
```
/init sre
```
Then paste the restart prompt below.

---

## 2. Unified Intelligence Framework
**Sprint ID**: SPRINT-INTEL-FRAMEWORK-001
**Status**: PENDING APPROVAL
**Plan**: `claude/context/plans/unified_intelligence_framework_sprint.md`
**Estimated Effort**: 5-6 hours

### Summary
- **BaseIntelligenceService** - Abstract base class for extensibility
- **OTCIntelligenceService** - Unified PostgreSQL query interface for ServiceDesk
- **CollectionScheduler** - Daily automated data refresh (PMP @ 06:00, OTC @ 06:30)
- **PMP Refactor** - Inherit base class (backward compatible)

### Why
- OTC queries require knowing 20+ tools, TKT-*/TKTCT-*/TS-* column prefixes
- No freshness awareness before queries
- Manual data refresh only
- No consistent pattern across data sources

### Tests
58 total across 7 phases

### To Start
```
Review and approve: claude/context/plans/unified_intelligence_framework_sprint.md
```

---

## 3. Azure Lighthouse Terraform Rollout (Lighthouse-TF)
**Sprint ID**: SPRINT-LIGHTHOUSE-TF-001
**Status**: READY TO START
**Plan**: `claude/context/projects/lighthouse_tf_rollout.md`
**Estimated Effort**: Multi-day (phased rollout to 100+ customers)

### Summary
Roll out Azure Lighthouse to all MCP customers using Terraform, enabling:
- Single pane of glass management from Orro tenant
- Foundation for AMA (Azure Monitor Agent) migration
- Azure Policy deployment at scale
- Future Azure operations (patching, security, compliance)

### Context
- **Current state**: GDAP access only, no Lighthouse
- **Scale**: 100+ MCP customers
- **Why Terraform**: Orro making TF workflows a priority
- **Why Lighthouse first**: Foundation for everything else

### Key Decisions Already Made
1. Terraform over ARM templates
2. Lighthouse before AMA deployment
3. Contributor access level
4. Single state file (optimize later if needed)
5. Phased rollout: Pilot → 10% → 50% → 100%

### Required Before Starting
- [ ] Orro Managing Tenant ID (GUID)
- [ ] Orro-AzureOps Security Group ID
- [ ] Orro-Monitoring Security Group ID
- [ ] Orro-ReadOnly Security Group ID
- [ ] Azure Storage Account for Terraform state
- [ ] Customer subscription list export from Partner Center

### To Start
```
/init sre
```
Then paste the restart prompt below.

### Restart Prompt
```
Resume: Azure Lighthouse Terraform Rollout (SPRINT-LIGHTHOUSE-TF-001)

Context:
- Rolling out Azure Lighthouse to 100+ MCP customers using Terraform
- This is foundation for AMA (Azure Monitor Agent) migration
- Currently have GDAP access, need Lighthouse for scale
- Orro making Terraform workflows a priority

Plan file: claude/context/projects/lighthouse_tf_rollout.md

Key decisions made:
1. Terraform (not ARM) - aligns with Orro TF priority
2. Lighthouse first, then AMA via Azure Policy
3. Contributor access for Orro-AzureOps group
4. Single TF state file initially
5. Phased rollout (pilot → 10% → 50% → 100%)

Terraform structure:
- modules/lighthouse-offer/ (definition + assignment)
- environments/customers.tfvars (subscription list)
- Azure Storage backend for state

Next actions needed:
1. Gather required info (tenant ID, security group IDs, storage account)
2. Create Terraform repo structure
3. Build lighthouse-offer module
4. Test on pilot customer
5. Scale to full rollout

What phase should we start with?
```

---

## Completed Recently

| Sprint | Date | Summary |
|--------|------|---------|
| SPRINT-PMP-INTEL-001 | 2026-01-15 | PMP Intelligence Service - unified query interface |
| SPRINT-002-PROMPT-CAPTURE | 2026-01-14 | Prompt capture system for team sharing |
| SPRINT-001-REPO-SYNC | 2026-01-13 | Multi-repo context validation |
