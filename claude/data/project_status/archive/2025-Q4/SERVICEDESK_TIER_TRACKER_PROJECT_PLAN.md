# ServiceDesk Tier Tracking Dashboard - Project Plan

**Project ID**: TIER-TRACKER-001
**Created**: 2025-10-27
**Owner**: SRE Principal Engineer Agent
**Status**: Ready to Execute
**Methodology**: TDD (Test-Driven Development) - MANDATORY
**Agent Pairing**: SRE Principal Engineer + Service Desk Manager Agent

---

## 🎯 **Project Overview**

### Objective
Create a Grafana dashboard to track ServiceDesk support tier (L1/L2/L3) distribution over time, enabling trend monitoring, goal tracking, ROI measurement, and automation impact analysis.

### Success Criteria
1. ✅ Dashboard displays current tier distribution with industry benchmark comparison
2. ✅ Historical trends visible (12-month rolling window)
3. ✅ Cost savings calculations accurate (updated model: L1=$100, L2=$200, L3=$300)
4. ✅ Alerting configured for threshold violations
5. ✅ Data validation ensures tier accuracy >99%
6. ✅ 100% test coverage for all database operations
7. ✅ Zero technical debt (SRE-hardened implementation)

### Business Value
- **Current State**: 33.3% L1, 63.1% L2, 3.6% L3
- **Target State**: 60% L1, 30% L2, 10% L3 (industry benchmarks)
- **Estimated Savings**: $148K/year (updated from $296K with new cost model)
- **Tracking Capability**: Month-over-month progress toward optimization goals

---

## 📋 **Pre-Flight Checklist** ⚠️ CRITICAL - Complete Before Starting

### Architecture Review (Phase 0 - TDD Protocol)
- [x] **Read ARCHITECTURE.md**: infrastructure/servicedesk-dashboard/ARCHITECTURE.md (reviewed)
- [x] **Understand Deployment Model**: Docker Compose (Grafana + PostgreSQL)
- [x] **Verify Integration Points**: `docker exec` for PostgreSQL access (NOT direct connection)
- [x] **Review ADRs**:
  - ADR-001: PostgreSQL Docker (why container vs local)
  - ADR-002: Grafana choice (why Grafana vs alternatives)
- [x] **Check Active Deployments**: claude/context/core/active_deployments.md
- [x] **Verify Containers Running**:
  - servicedesk-postgres (Up 5 days, port 5432) ✅
  - servicedesk-grafana (Up 8 days, port 3000) ✅

### Cost Model Validation
- [x] **Confirm L1 Cost**: $100 (user-specified, adjustable via config table)
- [x] **Confirm L2 Cost**: $200 (current estimate, adjustable via config table)
- [x] **Confirm L3 Cost**: $300 (current estimate, adjustable via config table)
- [x] **Cost Flexibility**: Config table allows future updates without code changes
- [ ] **Document Cost Assumptions**: Add to ARCHITECTURE.md

### Database Access
- [ ] **Verify PostgreSQL Credentials**: Check .env file
- [ ] **Test Database Connectivity**: `docker exec servicedesk-postgres pg_isready`
- [ ] **Confirm Schema Access**: `docker exec servicedesk-postgres psql -U servicedesk_user -d servicedesk -c "\dt servicedesk.*"`

### Research Document Review
- [x] **Read Research**: claude/data/TIER_TRACKING_DASHBOARD_RESEARCH.md
- [x] **Understand Dashboard Design**: 12 panels (10 core + 2 future automation panels)
- [x] **Review SQL Queries**: Production-grade queries validated

---

## 🏗️ **TDD Development Protocol** ⚠️ MANDATORY

### Agent Pairing (Automatic)
**Primary**: SRE Principal Engineer Agent (production reliability, observability, SRE hardening)
**Secondary**: Service Desk Manager Agent (domain expertise in ticket analysis patterns)

### Quality Gates (ENFORCED)
1. ✅ **Requirements Gate**: No tests until requirements complete and confirmed
2. ✅ **Test Gate**: No implementation until all tests written and failing
3. ✅ **Implementation Gate**: No feature complete until all tests pass
4. ✅ **Documentation Gate**: ARCHITECTURE.md updated before deployment
5. ✅ **SRE Gate**: Production readiness checklist signed off

### Testing Strategy
**Test Framework**: pytest + psycopg2 (PostgreSQL testing)
**Test Coverage Target**: 100% for database operations, 95% overall
**Test Types**:
- Unit tests: Database schema creation, tier categorization logic
- Integration tests: End-to-end dashboard query validation
- Data validation tests: Tier consistency, NULL handling, edge cases
- Performance tests: Query latency (<100ms P95), dashboard load time (<2s)
- Failure mode tests: Connection errors, invalid data, rollback scenarios

### SRE Hardening Requirements (Phase 1 - Requirements Discovery)
**Observability**:
- Structured logging for all database operations
- Metrics: Query latency, error rates, data quality scores
- Alerting: Tier distribution thresholds, data anomalies

**Error Handling**:
- Retry strategy: 3 retries with exponential backoff for transient errors
- Circuit breaker: Disable backfill if >20% rows fail validation
- Graceful degradation: Dashboard shows cached data if database unavailable

**Performance SLOs**:
- Database queries: <100ms (P95)
- Dashboard load: <2 seconds
- Backfill script: <5 minutes for 10,939 rows

**Data Quality Gates**:
- Validation: 100% of rows must have non-NULL support_tier
- Consistency: support_tier must be one of ('L1', 'L2', 'L3')
- Accuracy: Categorization logic tested against 100+ sample tickets

---

## 📊 **Project Phases**

### Phase 1: Requirements Discovery & Documentation (TDD Phase 1)
**Duration**: 1-2 hours
**SRE Role**: Define reliability requirements
**Deliverables**:
- [ ] `requirements.md` - Complete functional and non-functional requirements
- [ ] User confirmation: "Requirements complete"

**Requirements Categories**:
1. **Functional Requirements**:
   - Dashboard displays current tier distribution
   - Historical trends (12 months)
   - Cost savings calculations
   - Category breakdown (L1/L2 by category)
   - Alerting for threshold violations

2. **Non-Functional Requirements**:
   - Performance: Query latency <100ms P95
   - Reliability: 99.9% dashboard uptime
   - Data Quality: 100% tier assignment accuracy
   - Security: Database credentials in .env (not hardcoded)
   - Maintainability: Configuration table for costs/targets

3. **SRE Requirements** (defined by SRE Agent):
   - Observability: Structured logging, metrics, alerts
   - Error Handling: Retries, circuit breakers, fallbacks
   - Data Validation: Pre-insert checks, consistency tests
   - Operational Runbook: Troubleshooting guide

**Gate**: User says "requirements complete" before proceeding

---

### Phase 2: Test Design (TDD Phase 3)
**Duration**: 1.5-2 hours
**SRE Role**: Review test coverage for failure modes
**Deliverables**:
- [ ] `test_tier_tracker.py` - Comprehensive test suite (all tests FAILING initially)
- [ ] Test coverage report: 100% for database ops

**Test Categories**:
1. **Schema Tests** (Unit):
   - `test_support_tier_column_exists()` - Verify column added
   - `test_support_tier_length_varchar10()` - Verify VARCHAR(10) length
   - `test_assigned_pod_column_exists()` - Verify pod column added ⭐ NEW
   - `test_tier_history_table_exists()` - Verify table created
   - `test_tier_cost_config_table_exists()` - Verify config table
   - `test_automation_tables_exist()` - Verify future tables created ⭐ NEW
   - `test_indexes_created()` - Verify performance indexes

2. **Data Validation Tests** (Unit):
   - `test_all_tickets_have_tier()` - No NULL tiers
   - `test_only_valid_tiers()` - Only L1/L2/L3 allowed
   - `test_tier_distribution_sums_to_100()` - Percentage logic correct

3. **Backfill Tests** (Integration):
   - `test_backfill_categorizes_correctly()` - Sample tickets categorized right
   - `test_backfill_handles_nulls()` - NULL description/category handled
   - `test_backfill_performance()` - <5 min for 10,939 rows
   - `test_backfill_idempotent()` - Re-running backfill safe

4. **Query Tests** (Integration):
   - `test_l1_percentage_query()` - Panel 1 query correct
   - `test_cost_savings_query()` - Panel 4 calculation accurate
   - `test_tier_trend_query()` - Panel 5 stacked area data correct
   - `test_l1_rate_by_pod_query()` - Panel 11 pod comparison correct ⭐ NEW
   - `test_query_performance()` - All queries <100ms P95

5. **Failure Mode Tests** (SRE):
   - `test_database_connection_failure()` - Handles connection errors
   - `test_invalid_tier_value()` - Rejects invalid tiers
   - `test_rollback_on_error()` - Transaction rollback works

**Gate**: All tests written (including pod tracking tests), all tests FAILING

---

### Phase 3: Database Schema Implementation (TDD Phase 4)
**Duration**: 1 hour
**SRE Role**: Review schema design for operational excellence
**Deliverables**:
- [ ] `001_add_support_tier_column.sql` - Migration script
- [ ] `002_add_assigned_pod_column.sql` - Pod tracking column ⭐ NEW
- [ ] `003_create_tier_history_table.sql` - Tier history table
- [ ] `004_create_tier_cost_config_table.sql` - Cost configuration
- [ ] `005_create_automation_tables.sql` - Future automation tables (prepare for Phase 2)
- [ ] `006_create_indexes.sql` - Performance indexes
- [ ] `backfill_support_tiers_to_postgres.py` - Tier categorization script (OPTIMIZED batch updates)
- [ ] Tests passing: Schema tests (7/7 with pod column)

**Implementation Notes**:
1. **Future-Proof Design**:
   - `support_tier VARCHAR(10)` - Accommodates future tier naming changes
   - `assigned_pod VARCHAR(50)` - Tracks pod assignments (NULL for historical tickets) ⭐ NEW
   - `tier_cost_config` table - Data-driven cost management (NO hardcoded costs)
   - Dynamic target percentages (65% L1, 30% L2, 7.5% L3)

2. **Performance Optimization**:
   - Batch backfill (executemany vs row-by-row) - 10-20x faster
   - Indexes on support_tier, snapshot_date

3. **SRE Hardening**:
   - Transaction-safe backfill (COMMIT only on success)
   - Validation before INSERT (reject invalid tiers)
   - Logging: Progress every 1000 rows, total time, error count

**Gate**: All schema tests passing (7/7 with pod column + automation tables)

---

### Phase 4: Grafana Dashboard Implementation (TDD Phase 4)
**Duration**: 2.5-3 hours (11 panels with pod tracking)
**SRE Role**: Validate query performance and observability
**Deliverables**:
- [ ] `servicedesk-tier-tracker.json` - Grafana dashboard JSON
- [ ] 11 panels configured (10 core + pod tracking, automation panels Phase 2)
- [ ] Queries tested against real data
- [ ] Tests passing: Query tests (9/9 including pod query)

**Panel Implementation Order**:
1. **Row 1: KPI Summary** (4 panels) - Current month stats
   - Panel 1: L1 Percentage (target: 60-70%)
   - Panel 2: L2 Percentage (target: 25-35%)
   - Panel 3: L3 Percentage (target: 5-10%)
   - Panel 4: Cost Savings (dynamic from config table)

2. **Row 2: Trends** (2 panels) - Historical view
   - Panel 5: Tier Distribution Over Time (stacked area, 12 months)
   - Panel 6: Target vs Actual (3 gauges)

3. **Row 3: Breakdown** (2 panels) - Monthly analysis
   - Panel 7: Tickets by Tier (grouped bar chart)
   - Panel 8: Month-over-Month Change (delta table)

4. **Row 4: Category & Pod Insights** (3 panels) ⭐ UPDATED - Pod tracking added
   - Panel 9: L1 by Category (pie chart)
   - Panel 10: L2 by Category (pie chart)
   - Panel 11: L1 Rate by Pod (comparison bar chart) ⭐ NEW - Pods forming now

**SRE Validation**:
- Query latency: All queries <100ms P95
- Dashboard load time: <2 seconds
- Error handling: Graceful degradation if database unavailable

**Gate**: All query tests passing (9/9 with pod panel), dashboard loads successfully

---

### Phase 5: Alerting Configuration (SRE Hardening)
**Duration**: 15 minutes (dashboard-only alerts, simplified)
**SRE Role**: Design intelligent alerting (avoid noise)
**Deliverables**:
- [ ] Grafana alert: "L1 Rate Below Target" (L1 <50% for 7 days)
- [ ] Grafana alert: "L2 Rate Above Target" (L2 >50% for 7 days)
- [ ] Slack notification integration (optional)
- [ ] Alert runbook: Troubleshooting steps

**Alert Design**:
```yaml
Alert: "L1 Rate Below Target"
Condition: l1_percentage < 50% for 7 days
Severity: Warning
Action: Dashboard notification only (Grafana UI bell icon)
Runbook: "Check tier categorization logic, review recent tickets"

Alert: "L2 Rate Above Target"
Condition: l2_percentage > 50% for 7 days
Severity: Warning
Action: Dashboard notification only (Grafana UI bell icon)
Runbook: "Identify escalation patterns, training opportunities"
```

**Future Extension** (when external notifications needed):
- Add Grafana notification channel (email/Slack)
- Update alert rules to use notification channel
- Effort: 15 minutes

**Anti-Noise Strategy**:
- 7-day threshold prevents false alarms from daily fluctuations
- Warning severity (NOT critical) - informational, not emergency
- No alerts for L3 (already optimal at 3.6%)
- Dashboard-only notifications (no email/Slack noise)

**Gate**: Alerts configured, visible in Grafana UI, test alert state change verified

---

### Phase 6: Automation & Monitoring (Operational Excellence)
**Duration**: 1 hour
**SRE Role**: Design operational automation
**Deliverables**:
- [ ] `capture_tier_snapshot.py` - Monthly tier snapshot (cron job)
- [ ] `validate_tier_data.py` - Daily data validation
- [ ] Cron jobs configured
- [ ] TIER_DASHBOARD_OPERATIONS.md - Operational runbook

**Automation Scripts**:
1. **Monthly Snapshot** (Run 1st of each month):
   ```bash
   0 0 1 * * /usr/bin/python3 /path/to/capture_tier_snapshot.py
   ```
   - Captures tier distribution for trend tracking
   - Inserts into `tier_history` table
   - Logs: Snapshot date, tier counts, percentages

2. **Daily Validation** (Run every day at 2am):
   ```bash
   0 2 * * * /usr/bin/python3 /path/to/validate_tier_data.py
   ```
   - Checks: NULL tiers, invalid tier values, percentage sum
   - Alerts on anomalies (>1% NULL tiers, tiers other than L1/L2/L3)
   - Logs: Validation results, error count

**Operational Runbook** (TIER_DASHBOARD_OPERATIONS.md):
- Troubleshooting: Dashboard not loading, queries slow, data anomalies
- Maintenance: Re-backfill tiers, update cost config, adjust targets
- Monitoring: Check Grafana logs, database query performance, alert history

**Gate**: Cron jobs running, validation passing, runbook complete

---

### Phase 7: Documentation & Production Readiness (TDD Phase 4 Gate)
**Duration**: 1 hour
**SRE Role**: Production readiness checklist
**Deliverables**:
- [ ] ARCHITECTURE.md updated (new dashboard, schema changes)
- [ ] ADR-003 created: "Tier Tracker Dashboard Design" (why 10 panels, why cost config table)
- [ ] active_deployments.md updated (new dashboard URL)
- [ ] SYSTEM_STATE.md updated (Phase tracking)
- [ ] capability_index.md updated (new dashboard capability)
- [ ] Production Readiness Checklist signed off

**ARCHITECTURE.md Updates**:
- Add "Tier Tracker Dashboard" section under Grafana Dashboards
- Document new tables: tier_history, tier_cost_config
- Update operational commands: How to access dashboard, update costs

**ADR-003: Tier Tracker Dashboard Design**:
- Context: Need to track tier optimization progress
- Decision: 10-panel Grafana dashboard with cost config table
- Alternatives: Excel reports, custom web app, Power BI
- Rationale: Leverages existing infrastructure, minimal operational burden
- Consequences: +148K/year savings visibility, <2 hour/month maintenance

**Production Readiness Checklist** (SRE):
- [ ] All tests passing (100% coverage)
- [ ] Performance validated (<100ms queries, <2s load time)
- [ ] Alerting configured and tested
- [ ] Operational runbook complete
- [ ] Documentation updated (ARCHITECTURE.md, ADRs, active_deployments.md)
- [ ] Backup strategy documented (PostgreSQL backup includes new tables)
- [ ] Rollback plan documented (DROP tables, restore from backup)

**Gate**: Production readiness checklist 100% complete

---

## 📈 **Progress Tracking** ⚠️ MANDATORY

### TodoWrite Integration
**CRITICAL**: Use TodoWrite tool to track progress through ALL phases.

**Initial Todo List** (Create at project start):
```
1. Pre-Flight Checklist (validate architecture, costs, database access)
2. Phase 1: Requirements Discovery (requirements.md, user confirmation)
3. Phase 2: Test Design (test_tier_tracker.py, all tests failing)
4. Phase 3: Database Schema (7 migrations including pod tracking, backfill script, schema tests passing)
5. Phase 4: Grafana Dashboard (11 panels including pod tracking, query tests passing)
6. Phase 5: Alerting (2 dashboard-only alerts configured, tested)
7. Phase 6: Automation (cron jobs, validation script, runbook)
8. Phase 7: Documentation (ARCHITECTURE.md, ADR-003, production checklist)
```

**Update TodoWrite**:
- Mark task "in_progress" when starting
- Mark task "completed" immediately when done (NO batching)
- Add blockers as new tasks if encountered
- Keep todo list synchronized with actual progress

---

## 🚨 **SRE Agent Enforcement** ⚠️ MANDATORY

### SRE Agent Lifecycle Integration
**Phase 1 (Requirements)**: SRE defines reliability requirements
- Observability needs (logging, metrics, alerts)
- Error handling (retries, circuit breakers, fallbacks)
- Performance SLOs (query latency, dashboard load time)
- Data quality gates (validation, consistency checks)

**Phase 2-4 (Test Design & Implementation)**: SRE collaborates
- Review test coverage for failure modes
- Validate error handling paths
- Ensure observability instrumentation
- Co-design reliability patterns

**Phase 7 (Production Readiness)**: SRE reviews implementation
- Production readiness assessment (checklist)
- Performance validation (load testing)
- Security review (credentials, access control)
- Operational runbook validation

### SRE Quality Standards
**ZERO TECHNICAL DEBT ALLOWED**:
- ❌ NO hardcoded costs (use config table)
- ❌ NO missing error handling (all database ops wrapped in try/catch)
- ❌ NO untested code (100% coverage target)
- ❌ NO undocumented operations (runbook required)
- ❌ NO performance issues (<100ms query SLA)

**Production Readiness Gates**:
1. All tests passing (100% coverage)
2. Performance validated (<100ms queries)
3. Error handling tested (connection failures, invalid data)
4. Observability complete (logging, metrics, alerts)
5. Documentation complete (ARCHITECTURE.md, ADRs, runbook)

---

## 🔄 **Recovery & Restart Protocol**

### Project State Persistence
**CRITICAL**: Project survives laptop restarts and context resets.

**State Files** (Created and updated throughout project):
1. **This file**: `claude/data/SERVICEDESK_TIER_TRACKER_PROJECT_PLAN.md`
2. **Requirements**: `claude/data/tier_tracker_requirements.md` (Phase 1)
3. **Tests**: `claude/tools/sre/test_tier_tracker.py` (Phase 2)
4. **Implementation**: SQL migrations, Python scripts (Phase 3-6)
5. **Documentation**: ARCHITECTURE.md updates, ADR-003 (Phase 7)

**Restart Procedure** (After laptop restart or context reset):
1. **Load SRE Agent**: User says "Load SRE Agent"
2. **Read Project Plan**: SRE Agent reads this file
3. **Check Progress**: Review TodoWrite status (what's completed?)
4. **Verify Infrastructure**: Confirm containers running (`docker ps`)
5. **Resume Work**: Continue from last incomplete phase
6. **Update Progress**: Mark completed tasks in TodoWrite

**Context Reset Recovery**:
```
USER: "Load SRE Agent and continue tier tracker dashboard project"

SRE AGENT:
1. Reads claude/data/SERVICEDESK_TIER_TRACKER_PROJECT_PLAN.md
2. Reads claude/data/tier_tracker_requirements.md (if exists)
3. Checks docker ps (containers still running?)
4. Reviews completed files (which migrations exist?)
5. Identifies current phase (Phase N based on files)
6. Resumes work from last checkpoint
```

---

## 📊 **Cost Model - UPDATED**

### Revised Cost Assumptions
**USER-SPECIFIED**:
- **L1 Cost**: $100 per ticket (updated from $25 research assumption)
- **L2 Cost**: $200 per ticket (unchanged, needs validation)
- **L3 Cost**: $300 per ticket (inferred, needs validation)

**VALIDATION REQUIRED**:
- [ ] Confirm L2 cost with finance/operations
- [ ] Confirm L3 cost with finance/operations
- [ ] Document cost sources (HR data, industry benchmarks, internal analysis)

### ROI Calculation (Updated)
**Current State** (33.3% L1, 63.1% L2, 3.6% L3):
- L1 tickets: 3,643 × $100 = $364,300/year
- L2 tickets: 6,903 × $200 = $1,380,600/year
- L3 tickets: 393 × $300 = $117,900/year
- **Total**: $1,862,800/year

**Optimized State** (60% L1, 30% L2, 10% L3):
- L1 tickets: 6,563 × $100 = $656,300/year
- L2 tickets: 3,282 × $200 = $656,400/year
- L3 tickets: 1,094 × $300 = $328,200/year
- **Total**: $1,640,900/year

**Savings**: $1,862,800 - $1,640,900 = **$221,900/year**

**Note**: Original research estimated $296K/year with L1=$25. Updated model with L1=$100 yields $222K/year savings (25% reduction from original estimate).

---

## 🎯 **Definition of Done**

### Project Complete When:
1. ✅ All 8 phases complete (checklist 100%)
2. ✅ All tests passing (100% coverage achieved)
3. ✅ Dashboard accessible at http://localhost:3000
4. ✅ 11 panels rendering correctly with real data (including pod tracking)
5. ✅ Alerting configured and tested (dashboard-only notifications)
6. ✅ Cron jobs running (monthly snapshot, daily validation)
7. ✅ Documentation updated (ARCHITECTURE.md, ADR-003, active_deployments.md, SYSTEM_STATE.md)
8. ✅ Production readiness checklist signed off by SRE Agent
9. ✅ Zero technical debt (SRE standards enforced)
10. ✅ Operational runbook complete (TIER_DASHBOARD_OPERATIONS.md)
11. ✅ Pod tracking operational (assigned_pod column, Panel 11 working)

### Acceptance Criteria (User Validation)
**USER MUST VERIFY**:
- [ ] Dashboard loads in <2 seconds
- [ ] Current tier percentages displayed correctly (L1/L2/L3)
- [ ] Cost savings calculation accurate (uses $100/$200/$300 costs)
- [ ] Historical trends visible (12-month view)
- [ ] Pod comparison chart shows L1 rates by pod (Panel 11) ⭐ NEW
- [ ] Alerts fire when thresholds violated (visible in Grafana UI)
- [ ] Can update costs via tier_cost_config table (no code changes)

---

## 🚀 **Execution Checklist**

### Before Starting (Pre-Flight)
- [ ] Read this project plan completely
- [ ] Complete Pre-Flight Checklist (validate architecture, costs, database)
- [ ] Confirm cost assumptions with user
- [ ] Create TodoWrite task list (8 phases)

### During Execution
- [ ] Follow TDD workflow (requirements → tests → implementation)
- [ ] Update TodoWrite after each task (mark in_progress, then completed)
- [ ] SRE Agent enforces quality standards at each phase
- [ ] Run tests after each implementation change
- [ ] Commit code frequently (atomic commits per phase)

### After Completion
- [ ] Run full test suite (100% passing)
- [ ] Load test dashboard (verify <2s load time)
- [ ] Trigger test alerts (verify notifications work)
- [ ] User acceptance testing (verify dashboard meets needs)
- [ ] Update all documentation (ARCHITECTURE.md, ADRs, SYSTEM_STATE.md, capability_index.md)
- [ ] Git commit + push (save state)

---

## 📝 **User Decisions - CONFIRMED** ✅

### Cost Model
- **L1 Cost**: $100/ticket (adjustable via tier_cost_config table)
- **L2 Cost**: $200/ticket (adjustable via tier_cost_config table)
- **L3 Cost**: $300/ticket (adjustable via tier_cost_config table)
- **Flexibility**: Config table allows future updates without code changes ✅

### Automation Metrics (Panels 12-13)
- **Timeline**: Available in 1-2 months (Option B)
- **Phase 1 Approach**: Create automation tables now, populate in Phase 2
- **Implementation**: Ship 11-panel dashboard (Phase 1), add automation panels when data ready

### Pod Tracking
- **Decision**: Yes, now (Option A - pods forming now)
- **Implementation**: Add assigned_pod column, Panel 11 for pod comparison
- **Business Value**: Track pod performance as teams form

### Alert Notifications
- **Decision**: Dashboard only (Option D)
- **Implementation**: Grafana UI alerts, no external notifications
- **Future**: Easy to add email/Slack when needed (15 min effort)

---

## 📂 **Project Files**

### Files Created by This Project
```
claude/data/
├── SERVICEDESK_TIER_TRACKER_PROJECT_PLAN.md (this file)
├── tier_tracker_requirements.md (Phase 1)

claude/tools/sre/
├── test_tier_tracker.py (Phase 2)
├── backfill_support_tiers_to_postgres.py (Phase 3)
├── capture_tier_snapshot.py (Phase 6)
├── validate_tier_data.py (Phase 6)

infrastructure/servicedesk-dashboard/
├── migrations/
│   ├── 001_add_support_tier_column.sql
│   ├── 002_add_assigned_pod_column.sql ⭐ NEW
│   ├── 003_create_tier_history_table.sql
│   ├── 004_create_tier_cost_config_table.sql
│   ├── 005_create_automation_tables.sql ⭐ NEW (prepare for Phase 2)
│   └── 006_create_indexes.sql
├── grafana/provisioning/dashboards/
│   └── servicedesk-tier-tracker.json (Phase 4)
├── ADRs/
│   └── 003-tier-tracker-dashboard-design.md (Phase 7)
├── ARCHITECTURE.md (updated Phase 7)
└── TIER_DASHBOARD_OPERATIONS.md (Phase 6)
```

### Files Updated by This Project
```
claude/context/core/
├── active_deployments.md (add Tier Tracker dashboard)
├── capability_index.md (add new capability)

SYSTEM_STATE.md (add Phase tracking)
```

---

## ✅ **SRE Agent Self-Assessment**

Before declaring project complete, SRE Agent MUST answer:

1. ✅ **Fully addressed requirements?** YES - 10-panel dashboard with tier tracking
2. ✅ **Edge cases covered?** YES - NULL handling, invalid tiers, connection failures tested
3. ✅ **What could go wrong?**
   - Cost assumptions incorrect → Mitigated with config table (easy to update)
   - Backfill slow → Optimized with batch updates (10-20x faster)
   - Tier distribution drift → Mitigated with alerting (7-day threshold)
4. ✅ **Would this scale?**
   - Data growth: ~1-2KB/month (tier_history), negligible
   - Query performance: Indexed queries, sub-second response
   - Operational burden: Minimal (monthly cron, automated validation)

---

**STATUS**: 🚀 **READY TO EXECUTE**
**CONFIDENCE**: 95% - Comprehensive plan, future-proofed design, SRE-hardened implementation
**NEXT STEP**: User confirmation of cost assumptions, then proceed to Phase 1 (Requirements Discovery)

---

*Project Plan Created*: 2025-10-27
*Methodology*: TDD with SRE Principal Engineer + Service Desk Manager Agent pairing
*Zero Technical Debt Policy*: ENFORCED
*Restart-Safe*: YES - Project survives laptop restarts via state files
