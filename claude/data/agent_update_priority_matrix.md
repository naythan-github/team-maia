# Agent Update Priority Matrix - Phase 2
**Created**: 2025-10-11
**Purpose**: Prioritize remaining 31 agents for v2.2 Enhanced template upgrade
**Status**: ACTIVE - Guide for Phase 2 batch upgrades

---

## Executive Summary

**Current Progress**: 14/46 agents upgraded (30.4%)
**Remaining**: 31 agents needing v2.2 Enhanced upgrade
**Approach**: 3-batch strategy prioritized by usage frequency + business impact

**Estimated Effort**:
- Batch 1 (12 high-priority): ~24 hours (2 hours/agent average)
- Batch 2 (10 medium-priority): ~15 hours (1.5 hours/agent average)
- Batch 3 (9 low-priority): ~9 hours (1 hour/agent average)
- **Total**: ~48 hours across 3 batches

---

## Prioritization Methodology

### Criteria (3-Factor Scoring)

**1. Usage Frequency** (0-10 points)
- **High (8-10)**: Used weekly or more (Jobs, LinkedIn, Financial, Cloud)
- **Medium (4-7)**: Used monthly or for specific projects (SOE, Governance, Prompt Engineer)
- **Low (0-3)**: Specialized/rare use (Perth agents, Holiday Research, Travel Monitor)

**2. Business Impact** (0-10 points)
- **Critical (8-10)**: Revenue-generating, client-facing, strategic decisions
- **High (5-7)**: Operational efficiency, compliance, team productivity
- **Medium (0-4)**: Nice-to-have, experimental, personal use

**3. Current Quality Gap** (0-10 points, inverse scoring)
- **Large gap (8-10)**: <100 lines, minimal structure, needs major work
- **Medium gap (4-7)**: 100-250 lines, some structure, needs enhancement
- **Small gap (0-3)**: >250 lines, good structure, needs few-shot examples only

**Priority Score**: Usage + Business Impact + Quality Gap (max 30 points)

---

## Batch 1: High Priority (12 Agents) - Target: 24 hours

**Criteria**: Score ≥20 points (high usage + high business impact)

| # | Agent | Lines | Usage | Impact | Gap | Total | Effort | Rationale |
|---|-------|-------|-------|--------|-----|-------|--------|-----------|
| 1 | **jobs_agent.md** | 216 | 10 | 10 | 6 | 26 | 2.5h | Career decisions, weekly use, revenue-critical |
| 2 | **linkedin_ai_advisor_agent.md** | 332 | 9 | 9 | 4 | 22 | 2h | Professional branding, high visibility, strategic |
| 3 | **financial_advisor_agent.md** | 302 | 8 | 10 | 5 | 23 | 2h | Financial decisions, life-changing impact |
| 4 | **financial_planner_agent.md** | ? | 8 | 9 | 6 | 23 | 2h | Budgeting, savings optimization, monthly use |
| 5 | **principal_cloud_architect_agent.md** | 211 | 9 | 9 | 6 | 24 | 2h | Client proposals, architecture reviews, MSP core |
| 6 | **azure_architect_agent.md** | 162 | 8 | 8 | 7 | 23 | 2.5h | Azure-specific work, overlaps with principal cloud |
| 7 | **finops_engineering_agent.md** | ? | 7 | 9 | 6 | 22 | 2h | Cost optimization, ROI analysis, MSP value |
| 8 | **prompt_engineer_agent.md** | ? | 7 | 8 | 7 | 22 | 2h | Meta-agent for agent improvements (ironic needs upgrade!) |
| 9 | **soe_principal_engineer_agent.md** | ? | 8 | 8 | 6 | 22 | 2h | SOE build/maintenance, MSP core service |
| 10 | **soe_principal_consultant_agent.md** | ? | 7 | 8 | 6 | 21 | 2h | SOE consulting, client advisory |
| 11 | **governance_policy_engine_agent.md** | ? | 6 | 9 | 6 | 21 | 2h | Compliance, risk management, enterprise critical |
| 12 | **engineering_manager_cloud_mentor_agent.md** | ? | 7 | 7 | 6 | 20 | 2h | Team growth, career mentorship, management skills |

**Batch 1 Subtotal**: 12 agents, ~24 hours estimated

---

## Batch 2: Medium Priority (10 Agents) - Target: 15 hours

**Criteria**: Score 15-19 points (medium usage or high specialization)

| # | Agent | Lines | Usage | Impact | Gap | Total | Effort | Rationale |
|---|-------|-------|-------|--------|-----|-------|--------|-----------|
| 13 | **principal_idam_engineer_agent.md** | ? | 6 | 8 | 5 | 19 | 1.5h | Identity/access management, security-critical |
| 14 | **microsoft_licensing_specialist_agent.md** | ? | 6 | 7 | 6 | 19 | 1.5h | License optimization, MSP cost management |
| 15 | **virtual_security_assistant_agent.md** | ? | 5 | 8 | 6 | 19 | 1.5h | Security advisory, threat analysis |
| 16 | **ui_systems_agent.md** | ? | 6 | 7 | 5 | 18 | 1.5h | Dashboard/UI design, visualization |
| 17 | **product_designer_agent.md** | ? | 5 | 7 | 6 | 18 | 1.5h | Product design, user experience |
| 18 | **ux_research_agent.md** | ? | 5 | 6 | 6 | 17 | 1.5h | User research, usability testing |
| 19 | **confluence_organization_agent.md** | ? | 6 | 6 | 5 | 17 | 1.5h | Documentation, knowledge management |
| 20 | **company_research_agent.md** | ? | 5 | 6 | 6 | 17 | 1.5h | Prospect research, competitive intelligence |
| 21 | **blog_writer_agent.md** | ? | 5 | 6 | 5 | 16 | 1.5h | Content creation, thought leadership |
| 22 | **interview_prep_agent.md** | ? | 5 | 6 | 5 | 16 | 1.5h | Interview preparation, career advancement |

**Batch 2 Subtotal**: 10 agents, ~15 hours estimated

---

## Batch 3: Low Priority (9 Agents) - Target: 9 hours

**Criteria**: Score <15 points (specialized, infrequent, or experimental)

| # | Agent | Lines | Usage | Impact | Gap | Total | Effort | Rationale |
|---|-------|-------|-------|--------|-----|-------|--------|-----------|
| 23 | **token_optimization_agent.md** | ? | 4 | 6 | 5 | 15 | 1h | Cost optimization, system efficiency |
| 24 | **senior_construction_recruitment_agent.md** | ? | 3 | 6 | 5 | 14 | 1h | Niche recruitment, specialized industry |
| 25 | **presentation_generator_agent.md** | ? | 4 | 5 | 5 | 14 | 1h | Presentation creation, business communication |
| 26 | **contact_extractor_agent.md** | ? | 3 | 5 | 5 | 13 | 1h | Data extraction, lead generation |
| 27 | **perth_restaurant_discovery_agent.md** | ? | 3 | 3 | 5 | 11 | 1h | Personal use, local recommendations |
| 28 | **perth_liquor_deals_agent.md** | ? | 2 | 2 | 5 | 9 | 1h | Personal use, deal hunting |
| 29 | **holiday_research_agent.md** | ? | 2 | 3 | 5 | 10 | 1h | Travel planning, vacation research |
| 30 | **travel_monitor_alert_agent.md** | ? | 2 | 3 | 5 | 10 | 1h | Flight tracking, travel alerts |
| 31 | **team_knowledge_sharing_agent.md** | 450 | 4 | 6 | 0 | 10 | 0h | **Already v2.2!** (Created Phase 108, no upgrade needed) |

**Batch 3 Subtotal**: 8 agents need upgrade (1 already v2.2), ~8 hours estimated

---

## Upgrade Strategy Per Batch

### Standard Upgrade Process (Per Agent)

**Time Breakdown**:
- Read current agent: 10 min
- Apply v2.2 template structure: 20 min
- Add 2 few-shot examples: 40 min
- Add problem-solving templates: 20 min
- Quality validation: 15 min
- Commit to git: 5 min
- **Total**: ~1.5-2 hours per agent (average)

**Efficiency Gains**:
- Batch 1: Higher complexity (2h average) - More examples needed
- Batch 2: Medium complexity (1.5h average) - Standard templates
- Batch 3: Lower complexity (1h average) - Simpler domains

---

## Quality Validation Checklist (Per Agent)

**Required Elements** (from v2.2 Enhanced template):
- [ ] OpenAI's 3 critical reminders (Persistence, Tool-Calling, Systematic Planning)
- [ ] Self-Reflection & Review pattern
- [ ] 2+ few-shot examples per key command
- [ ] ReACT pattern demonstration (at least 1 example)
- [ ] Problem-solving methodology (3-phase template)
- [ ] Explicit handoff declarations (integration points)
- [ ] Performance metrics defined
- [ ] Action verbs throughout specialties/commands
- [ ] Quality score >75/100 (rubric-based)

---

## Success Metrics

**Phase 2 Completion Criteria**:
- [ ] All 31 agents upgraded to v2.2 Enhanced
- [ ] Average quality score >80/100 across all 46 agents
- [ ] 100% pattern coverage (5/5 patterns in all agents)
- [ ] No agents with critical quality issues (<60/100)
- [ ] System-wide quality audit complete
- [ ] Agent performance dashboard updated

**Expected Outcomes**:
- Task completion rate: 72% → 85%+ (target +18%)
- Agent consistency: Standardized structure across all 46 agents
- Maintenance efficiency: Easier updates with consistent templates
- User experience: Predictable agent behavior and quality

---

## Implementation Timeline

**Week 1-2** (Current session if possible):
- Complete Batch 1 (12 high-priority agents) - 24 hours
- Quality spot-check after 5 agents
- Adjust process if needed

**Week 3**:
- Complete Batch 2 (10 medium-priority agents) - 15 hours
- Interim quality audit

**Week 4**:
- Complete Batch 3 (8 low-priority agents) - 8 hours
- System-wide quality audit (all 46 agents)
- Update agent performance dashboard
- Document Phase 2 completion

**Total Timeline**: 4 weeks (48 hours total effort)

---

## Risk Mitigation

**Risk 1**: Agent upgrades break existing workflows
- **Mitigation**: Test upgraded agents with recent use cases
- **Fallback**: Keep original versions as _v1.md backups

**Risk 2**: Quality inconsistency across batches
- **Mitigation**: Spot-check every 5th agent, validate against rubric
- **Checkpoint**: Pause after Batch 1 to review and adjust

**Risk 3**: Effort underestimated (complex agents take longer)
- **Mitigation**: Track actual time per agent, adjust estimates
- **Buffer**: Add 20% time buffer to each batch

**Risk 4**: User discovers upgraded agent doesn't meet needs
- **Mitigation**: Document changes, collect feedback
- **Recovery**: Iterate on agent based on real-world usage

---

## Notes

**Special Cases**:
- **Team Knowledge Sharing Agent**: Already v2.2 (created Phase 108), skip upgrade
- **Azure Architect vs Principal Cloud Architect**: May need consolidation review (both do Azure architecture)
- **Prompt Engineer Agent**: Meta-agent needs upgrade (currently helping others but not optimized itself)

**Template Reference**:
- Use `claude/templates/agent_prompt_template_v2.1_lean.md` as base
- Evolved to v2.2 Enhanced with 5 advanced patterns
- Reference upgraded agents for domain-specific examples

**Integration Testing**:
- After each batch: Test 2-3 agents with real tasks
- Verify tool-calling works correctly
- Validate handoff patterns with multi-agent workflows

---

**Status**: READY FOR BATCH 1 EXECUTION
**Next Step**: Begin Batch 1 upgrades (12 agents, ~24 hours)
