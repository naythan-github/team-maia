# M365 IR Data Quality System Rebuild

**Project ID**: M365-DQ-2026-001
**Start Date**: 2026-01-06
**Target Completion**: 2026-04-06 (13 weeks)
**Status**: 🟢 ACTIVE - Phase 0 (Project Setup)
**Approval**: ✅ FULL APPROVAL (2026-01-06)

---

## Executive Summary

**Problem**: 15-25% forensic error rate in M365 IR investigations due to data interpretation errors. Critical incident (PIR-OCULUS) incorrectly concluded as "attack failed" when 8 accounts were actually compromised.

**Solution**: Comprehensive data quality system with:
- Automated field validation and reliability scoring
- Status code lookup tables (persistent knowledge base)
- Pre-analysis quality checks (fail-fast on bad data)
- Multi-field verification protocol (prevent wrong field selection)

**Target Outcome**: 80-90% error reduction (15-25% → 2-4% residual error rate)

**Timeline**: 13 weeks across 4 phases (Phase 0-3)

**Lead Agent**: SRE Principal Engineer + M365 IR Agent collaboration
**Testing Strategy**: Full TDD - tests written before implementation, 100% coverage target

---

## Project State Machine

```
Current State: PHASE_0_SETUP
Next State: PHASE_1_FOUNDATION

States:
├─ PHASE_0_SETUP           [CURRENT]
├─ PHASE_1_FOUNDATION      [Week 1-4]
├─ PHASE_2_AUTOMATION      [Week 5-8]
├─ PHASE_3_OPTIMIZATION    [Week 9-12]
└─ PHASE_4_DEPLOYMENT      [Week 13]
```

**State Transitions**:
- Each phase: DISCOVERY → PLANNING → IMPLEMENTATION → TESTING → REVIEW → COMPLETE
- Cannot advance to next phase until current phase passes review
- Checkpoint required every 10 tool uses OR phase boundary

---

## Phase 0: Project Setup (Week 0)

**Status**: 🟡 IN PROGRESS
**Duration**: 1 week
**State**: DISCOVERY

### Objectives
1. Create comprehensive project plan with cross-context tracking
2. Initialize project tracking database
3. Set up TDD infrastructure
4. Define success metrics and checkpoints
5. Create initial test framework

### Tasks

#### P0.1: Project Infrastructure ⏳ IN PROGRESS
- [x] Create PROJECT_PLAN.md with state machine
- [ ] Create project tracking table in system database
- [ ] Define checkpoint protocol for multi-context sessions
- [ ] Set up progress dashboard query

#### P0.2: Test Infrastructure 📋 PENDING
- [ ] Create `tests/m365_ir/data_quality/` directory structure
- [ ] Set up pytest fixtures for test databases
- [ ] Create test data generators (synthetic M365 logs)
- [ ] Write TDD protocol document specific to this project

#### P0.3: Database Schema Planning 📋 PENDING
- [ ] Design `status_code_reference` table schema
- [ ] Design `field_reliability_scores` table schema
- [ ] Design `data_quality_checks` table schema
- [ ] Design `quality_check_results` log table
- [ ] Review schema with SRE agent

#### P0.4: Initial Documentation 📋 PENDING
- [ ] Create ARCHITECTURE.md for data quality system
- [ ] Create TESTING_STRATEGY.md with TDD approach
- [ ] Create CONTEXT_HANDOFF_PROTOCOL.md for multi-window tracking
- [ ] Update capability index with new tools

### Success Criteria
- ✅ Project plan exists with complete phase breakdown
- ✅ Database tracking system operational
- ✅ Test infrastructure can run `pytest tests/m365_ir/data_quality/ -v`
- ✅ All Phase 0 tasks marked complete in tracking system

### Deliverables
1. This project plan document
2. `project_tracking` table in system database
3. Test infrastructure in `tests/m365_ir/data_quality/`
4. Architecture and testing strategy documents

---

## Phase 1: Foundation (Weeks 1-4) - P0 CRITICAL

**Status**: 📋 PENDING
**Duration**: 4 weeks
**Priority**: P0 - CRITICAL (highest ROI, prevents 80% of errors)

### Objectives
1. Extend auth_verifier to all M365 log types
2. Implement pre-analysis quality checks
3. Create status code lookup tables
4. Achieve 100% test coverage for core validation

### Phase 1.1: Extended Auth Verification (Week 1)

**State**: PENDING
**Lead**: M365 IR Agent + SRE Agent collaboration

#### Tasks
- [ ] **TEST**: Write tests for sign_in_logs verification (TDD)
- [ ] **TEST**: Write tests for unified_audit_log verification (TDD)
- [ ] **CODE**: Extend `auth_verifier.py` to handle sign_in_logs
- [ ] **CODE**: Add `conditional_access_status` field validation
- [ ] **CODE**: Extend to unified_audit_log (Operation field analysis)
- [ ] **TEST**: Verify >80% foreign IP success triggers alert
- [ ] **INTEGRATION**: Update `log_importer.py` to call new verifiers
- [ ] **DOCS**: Update IR_PLAYBOOK.md with new verification steps

#### Technical Specs
```python
# New function signatures needed:
def verify_sign_in_status(db_path: str) -> SignInVerificationSummary:
    """
    Validates sign_in_logs using conditional_access_status field.
    Detects: 0% success (all blocked), >80% foreign success (breach).
    """

def verify_audit_log_operations(db_path: str) -> AuditVerificationSummary:
    """
    Validates unified_audit_log using Operation + ResultStatus fields.
    Detects: MailItemsAccessed patterns, data exfiltration indicators.
    """
```

#### Success Criteria
- ✅ All tests pass: `pytest tests/m365_ir/data_quality/test_extended_auth_verifier.py -v`
- ✅ Oculus case: system auto-detects 188 successful foreign logins
- ✅ Oculus case: system triggers breach alert (>80% success from foreign IPs)
- ✅ Performance: <2 seconds for 10K events
- ✅ Integration: `python3 claude/tools/m365_ir/log_importer.py` runs all verifiers

### Phase 1.2: Pre-Analysis Quality Checks (Week 2)

**State**: PENDING
**Lead**: SRE Agent (reliability patterns) + M365 IR Agent (domain logic)

#### Tasks
- [ ] **TEST**: Write tests for field population detection (TDD)
- [ ] **TEST**: Write tests for discriminatory power calculation (TDD)
- [ ] **CODE**: Implement `data_quality_checker.py` tool
- [ ] **CODE**: Add field population analysis (detect 100% uniform fields)
- [ ] **CODE**: Add discriminatory power scoring (detect useful vs useless fields)
- [ ] **CODE**: Add multi-field consistency checks
- [ ] **TEST**: Verify detection of `status_error_code` as unreliable (100% uniform)
- [ ] **INTEGRATION**: Add quality check to import pipeline (fail-fast mode)
- [ ] **DOCS**: Create runbook: "What to do when quality check fails"

#### Technical Specs
```python
class FieldReliabilityCheck:
    """Pre-analysis validation to prevent wrong field selection."""

    def check_field_population(self, table: str, field: str) -> PopulationScore:
        """Detect unpopulated fields (>95% same value = unreliable)."""

    def check_discriminatory_power(self, table: str, field: str) -> float:
        """Calculate 0-1 score: unique_values / total_rows."""

    def recommend_status_field(self, table: str) -> FieldRecommendation:
        """Auto-select most reliable status field for analysis."""
```

#### Success Criteria
- ✅ All tests pass: `pytest tests/m365_ir/data_quality/test_quality_checker.py -v`
- ✅ Oculus case: system flags `status_error_code` as unreliable (100% uniform)
- ✅ Oculus case: system recommends `conditional_access_status` instead
- ✅ Import fails gracefully when quality check detects bad data
- ✅ Manual override flag works: `--skip-quality-check` for edge cases

### Phase 1.3: Status Code Lookup Tables (Week 3)

**State**: PENDING
**Lead**: M365 IR Agent (domain knowledge) + SRE Agent (schema design)

#### Tasks
- [ ] **SCHEMA**: Design `status_code_reference` table
- [ ] **SCHEMA**: Design `schema_versions` table (track Microsoft API changes)
- [ ] **TEST**: Write tests for code lookup (TDD)
- [ ] **TEST**: Write tests for unknown code detection (TDD)
- [ ] **DATA**: Populate initial status codes from Microsoft Entra ID docs
- [ ] **CODE**: Create `status_code_manager.py` tool
- [ ] **CODE**: Implement auto-lookup during import
- [ ] **CODE**: Add alerting for unknown codes (email to SRE)
- [ ] **DOCS**: Create maintenance runbook (quarterly review process)

#### Schema Design
```sql
CREATE TABLE status_code_reference (
    code_id INTEGER PRIMARY KEY,
    log_type TEXT NOT NULL,           -- 'sign_in_logs', 'legacy_auth', etc.
    field_name TEXT NOT NULL,         -- 'status_error_code', 'conditional_access_status'
    code_value TEXT NOT NULL,         -- '0', '50126', 'success', 'failure'
    meaning TEXT NOT NULL,            -- Human-readable explanation
    severity TEXT NOT NULL,           -- 'INFO', 'WARNING', 'CRITICAL'
    first_seen DATE NOT NULL,         -- When code was first documented
    last_validated DATE NOT NULL,     -- Last quarterly review date
    deprecated BOOLEAN DEFAULT 0,     -- Microsoft deprecated this code
    UNIQUE(log_type, field_name, code_value)
);

CREATE TABLE schema_versions (
    version_id INTEGER PRIMARY KEY,
    log_type TEXT NOT NULL,
    api_version TEXT NOT NULL,        -- 'v1.0', 'beta'
    schema_hash TEXT NOT NULL,        -- SHA256 of field list
    detected_date DATE NOT NULL,
    notes TEXT
);
```

#### Success Criteria
- ✅ All tests pass: `pytest tests/m365_ir/data_quality/test_status_codes.py -v`
- ✅ Database contains >50 known status codes from Microsoft docs
- ✅ Import auto-flags unknown codes and emails SRE
- ✅ Quarterly maintenance runbook documented
- ✅ SRE owner assigned for lookup table maintenance

### Phase 1.4: Integration Testing (Week 4)

**State**: PENDING
**Lead**: SRE Agent (integration patterns)

#### Tasks
- [ ] **TEST**: End-to-end test: Oculus case import with all checks
- [ ] **TEST**: Error injection tests (simulate bad data)
- [ ] **TEST**: Performance tests (100K+ event dataset)
- [ ] **TEST**: Regression tests (ensure Phase 241 still works)
- [ ] **CODE**: Fix any integration issues discovered
- [ ] **REVIEW**: SRE agent reviews all Phase 1 code
- [ ] **DOCS**: Update all affected documentation
- [ ] **CHECKPOINT**: Save state before Phase 2

#### Success Criteria
- ✅ Oculus case: Full import with all verifications passes
- ✅ Oculus case: System correctly identifies breach (8 accounts, 188 logins)
- ✅ Error injection: Quality checks catch and fail gracefully
- ✅ Performance: <5 minutes for full Oculus import (27K events)
- ✅ All Phase 1 tests pass: `pytest tests/m365_ir/data_quality/ -v`
- ✅ SRE review: Grade B+ or higher

### Phase 1 Deliverables
1. `auth_verifier.py` extended to all log types
2. `data_quality_checker.py` with pre-analysis validation
3. `status_code_manager.py` with lookup tables
4. `status_code_reference` database populated with 50+ codes
5. Complete test suite with 100% coverage
6. Updated documentation (IR_PLAYBOOK.md, runbooks)

---

## Phase 2: Automation (Weeks 5-8) - P1 HIGH

**Status**: 📋 PENDING
**Duration**: 4 weeks
**Priority**: P1 - HIGH (operational readiness)

### Objectives
1. Implement field reliability scoring with context awareness
2. Set up monitoring dashboard
3. Configure alerting system
4. Create operational runbooks
5. Train IR analysts

### Phase 2.1: Field Reliability Scoring (Week 5)

**State**: PENDING

#### Tasks
- [ ] **TEST**: Write tests for context-aware reliability rules (TDD)
- [ ] **CODE**: Implement `field_reliability_scorer.py`
- [ ] **CODE**: Add context rules (e.g., "legacy_auth has no conditional_access_status")
- [ ] **CODE**: Store scores in `field_reliability_scores` table
- [ ] **TEST**: Verify scoring accuracy on historical cases
- [ ] **INTEGRATION**: Auto-run scoring on every import
- [ ] **DOCS**: Document scoring algorithm and context rules

#### Technical Specs
```python
class FieldReliabilityScorer:
    """Context-aware field reliability with learned rules."""

    def calculate_base_score(self, table: str, field: str) -> float:
        """Population rate × discriminatory power × consistency."""

    def apply_context_rules(self, log_type: str, field: str, base_score: float) -> float:
        """Adjust score based on known context (e.g., legacy_auth quirks)."""

    def recommend_fields(self, table: str, purpose: str) -> List[FieldRecommendation]:
        """Return ranked fields for specific analysis purpose."""
```

#### Success Criteria
- ✅ All tests pass: `pytest tests/m365_ir/data_quality/test_reliability_scorer.py -v`
- ✅ Scoring correctly ranks `conditional_access_status` > `status_error_code`
- ✅ Context rules handle legacy_auth edge cases
- ✅ Historical cases: 95%+ correct field recommendations

### Phase 2.2: Monitoring Dashboard (Week 6)

**State**: PENDING

#### Tasks
- [ ] **SCHEMA**: Design dashboard queries and views
- [ ] **TEST**: Write tests for dashboard metrics calculation
- [ ] **CODE**: Create `data_quality_dashboard.py` CLI tool
- [ ] **CODE**: Implement metrics: error rate trends, quality check pass/fail, unknown codes
- [ ] **CODE**: Add time-series analysis (30-day rolling window)
- [ ] **TEST**: Verify dashboard accuracy on synthetic data
- [ ] **DOCS**: Create dashboard user guide

#### Dashboard Metrics
```
M365 IR Data Quality Dashboard
================================
Period: Last 30 days

Quality Check Pass Rate:        94% (47/50 imports)
Unknown Code Detections:        3 codes flagged
Forensic Error Rate:           4% (2/50 cases corrected)
Avg Import Time:               2.3 minutes
Verifications Run:             150 (3 per import × 50 imports)

Recent Failures:
- 2026-01-03: PIR-XYZ - Novel status code 530031 detected
- 2026-01-01: PIR-ABC - Quality check failed (95% null values)

Top Reliable Fields (Last 30 days):
1. conditional_access_status    (score: 0.98)
2. result_status               (score: 0.92)
3. operation                   (score: 0.89)
```

#### Success Criteria
- ✅ Dashboard runs: `python3 claude/tools/m365_ir/data_quality_dashboard.py`
- ✅ Metrics accurate to ±2% vs manual calculation
- ✅ Dashboard generates in <5 seconds
- ✅ All metrics have TDD tests

### Phase 2.3: Alerting System (Week 7)

**State**: PENDING

#### Tasks
- [ ] **TEST**: Write tests for alert trigger conditions
- [ ] **CODE**: Create `quality_alert_system.py`
- [ ] **CODE**: Implement alert rules (unknown codes, quality check failures, breach indicators)
- [ ] **CODE**: Add email integration (SMTP for SRE notifications)
- [ ] **CODE**: Add severity levels (INFO/WARNING/CRITICAL)
- [ ] **TEST**: Verify alert delivery and deduplication
- [ ] **CONFIG**: Set up alert recipients and thresholds
- [ ] **DOCS**: Create alert runbook (how to respond to each alert type)

#### Alert Rules
```python
ALERT_RULES = {
    "unknown_status_code": {
        "severity": "WARNING",
        "threshold": 1,  # Alert on any unknown code
        "recipients": ["sre@maia.local"],
        "message": "Unknown status code detected in {log_type}: {code_value}"
    },
    "quality_check_failure": {
        "severity": "CRITICAL",
        "threshold": 1,
        "recipients": ["sre@maia.local", "ir-team@maia.local"],
        "message": "Data quality check failed for {case_id}: {failure_reason}"
    },
    "breach_indicator": {
        "severity": "CRITICAL",
        "threshold": 1,
        "recipients": ["ir-team@maia.local"],
        "message": "Breach indicator detected: {indicator_type} in {case_id}"
    }
}
```

#### Success Criteria
- ✅ All tests pass: `pytest tests/m365_ir/data_quality/test_alerting.py -v`
- ✅ Test alert delivered to configured recipients
- ✅ Alert deduplication works (no spam)
- ✅ CRITICAL alerts escalate properly

### Phase 2.4: Operational Runbooks (Week 8)

**State**: PENDING

#### Tasks
- [ ] **DOCS**: Create "Unknown Status Code Response" runbook
- [ ] **DOCS**: Create "Quality Check Failure Response" runbook
- [ ] **DOCS**: Create "Quarterly Lookup Table Maintenance" runbook
- [ ] **DOCS**: Create "Adding New Log Type" runbook
- [ ] **DOCS**: Create "Troubleshooting Guide" for common issues
- [ ] **TEST**: Dry-run each runbook with SRE agent
- [ ] **REVIEW**: IR team reviews runbooks for clarity

#### Success Criteria
- ✅ 5 operational runbooks completed
- ✅ Each runbook tested in practice scenario
- ✅ IR team approves runbook clarity and completeness
- ✅ Runbooks indexed in capability database

### Phase 2 Deliverables
1. `field_reliability_scorer.py` with context-aware rules
2. `data_quality_dashboard.py` CLI tool
3. `quality_alert_system.py` with email integration
4. 5 operational runbooks
5. Complete test coverage for all automation
6. Monitoring infrastructure operational

---

## Phase 3: Optimization (Weeks 9-12) - P2 MEDIUM

**Status**: 📋 PENDING
**Duration**: 4 weeks
**Priority**: P2 - MEDIUM (performance and long-term maintainability)

### Objectives
1. Performance benchmarking and optimization
2. Implement normalized views (if needed)
3. Automate lookup table maintenance
4. Complete documentation and training

### Phase 3.1: Performance Benchmarking (Week 9)

**State**: PENDING

#### Tasks
- [ ] **TEST**: Create synthetic datasets (10K, 100K, 1M events)
- [ ] **BENCHMARK**: Measure auth_verifier performance at scale
- [ ] **BENCHMARK**: Measure quality checker performance at scale
- [ ] **BENCHMARK**: Measure normalized view query performance
- [ ] **ANALYZE**: Identify bottlenecks (profiling)
- [ ] **OPTIMIZE**: Apply targeted optimizations
- [ ] **TEST**: Verify optimizations don't break functionality

#### Performance Targets
```
Target Performance (p95 latency):
- 10K events:    <2 seconds (MUST PASS)
- 100K events:   <20 seconds (SHOULD PASS)
- 1M events:     <180 seconds (NICE TO HAVE)

If normalized views fail targets:
→ Implement materialized table alternative
```

#### Success Criteria
- ✅ Performance targets met for 10K and 100K datasets
- ✅ Bottlenecks identified and documented
- ✅ Profiling data saved for future optimization

### Phase 3.2: Normalized Views (Week 10)

**State**: PENDING (CONDITIONAL - only if performance requires)

#### Tasks
- [ ] **SCHEMA**: Design normalized status view (if needed)
- [ ] **TEST**: Write tests for view correctness
- [ ] **CODE**: Implement view or materialized table
- [ ] **BENCHMARK**: Compare view vs materialized table performance
- [ ] **DECIDE**: Choose implementation based on benchmark
- [ ] **INTEGRATION**: Update tools to use normalized layer
- [ ] **TEST**: Regression test all existing functionality

#### Schema Design (if needed)
```sql
CREATE VIEW v_normalized_status AS
SELECT
    log_id,
    log_type,
    'sign_in' as event_type,
    CASE
        WHEN conditional_access_status = 'success' THEN 'SUCCESS'
        WHEN conditional_access_status = 'failure' THEN 'FAILURE'
        ELSE 'UNKNOWN'
    END as normalized_status,
    timestamp,
    user_id,
    location_country
FROM sign_in_logs
UNION ALL
SELECT ...
FROM legacy_auth_logs
UNION ALL
SELECT ...
FROM unified_audit_log;

-- If performance poor, convert to materialized table:
CREATE TABLE normalized_status_materialized AS SELECT * FROM v_normalized_status;
CREATE INDEX idx_normalized_status ON normalized_status_materialized(normalized_status, timestamp);
```

#### Success Criteria
- ✅ Normalized layer performs at target benchmarks
- ✅ All existing queries work with normalized layer
- ✅ Maintenance overhead acceptable (<2 hours/week)

### Phase 3.3: Automated Maintenance (Week 11)

**State**: PENDING

#### Tasks
- [ ] **TEST**: Write tests for maintenance automation
- [ ] **CODE**: Create `lookup_table_maintenance.py` scheduler
- [ ] **CODE**: Implement quarterly review automation
- [ ] **CODE**: Add deprecation detection (Microsoft API changelog monitoring)
- [ ] **CODE**: Auto-generate maintenance report
- [ ] **CONFIG**: Set up cron job or task scheduler
- [ ] **TEST**: Dry-run automated maintenance cycle
- [ ] **DOCS**: Document automation and override procedures

#### Automation Features
```python
class LookupTableMaintenance:
    """Quarterly automated maintenance of status code tables."""

    def detect_unknown_codes(self) -> List[str]:
        """Find codes detected in last 90 days not in reference table."""

    def check_microsoft_changelog(self) -> List[SchemaChange]:
        """Scrape Microsoft Entra ID docs for API changes."""

    def generate_maintenance_report(self) -> MaintenanceReport:
        """Create quarterly review checklist for SRE."""

    def auto_add_codes(self, codes: List[str], approval_required: bool = True):
        """Add new codes with optional manual approval."""
```

#### Success Criteria
- ✅ Automation runs successfully in dry-run mode
- ✅ Maintenance report accurate and actionable
- ✅ SRE can review and approve changes in <30 minutes
- ✅ Deprecation detection catches known schema changes

### Phase 3.4: Final Documentation & Training (Week 12)

**State**: PENDING

#### Tasks
- [ ] **DOCS**: Update ARCHITECTURE.md with final system design
- [ ] **DOCS**: Create comprehensive user guide for IR analysts
- [ ] **DOCS**: Create SRE handoff document (maintenance procedures)
- [ ] **DOCS**: Document lessons learned
- [ ] **DOCS**: Update capability index with all new tools
- [ ] **TRAINING**: Create training materials (slides, demos)
- [ ] **TRAINING**: Conduct IR analyst training session
- [ ] **REVIEW**: Final SRE review of complete system

#### Documentation Deliverables
1. System Architecture Document (updated)
2. IR Analyst User Guide (new)
3. SRE Maintenance Guide (new)
4. Lessons Learned Report (new)
5. Training Materials (slides + recorded demo)

#### Success Criteria
- ✅ All documentation complete and reviewed
- ✅ IR analysts complete training (95%+ satisfaction)
- ✅ SRE accepts handoff with documented procedures
- ✅ Final system review: Grade A- or higher

### Phase 3 Deliverables
1. Performance benchmarks and optimization report
2. Normalized views (if implemented)
3. Automated maintenance system
4. Complete documentation package
5. Training materials and analyst certification

---

## Phase 4: Deployment & Handoff (Week 13)

**Status**: 📋 PENDING
**Duration**: 1 week
**Priority**: P0 - CRITICAL

### Objectives
1. Production deployment
2. Final validation
3. SRE handoff
4. Project closure

### Phase 4.1: Production Deployment

**State**: PENDING

#### Tasks
- [ ] **DEPLOY**: Merge all code to main branch
- [ ] **DEPLOY**: Update production IR_PLAYBOOK.md
- [ ] **DEPLOY**: Enable quality checks in production imports
- [ ] **DEPLOY**: Activate monitoring and alerting
- [ ] **TEST**: Run production validation (import real case)
- [ ] **MONITOR**: Watch for 48 hours (alert response time)
- [ ] **FIX**: Address any production issues immediately

#### Success Criteria
- ✅ All code merged without conflicts
- ✅ Production import succeeds with all checks
- ✅ No critical alerts in first 48 hours
- ✅ Monitoring dashboard operational

### Phase 4.2: Final Validation

**State**: PENDING

#### Tasks
- [ ] **TEST**: Re-run Oculus case with production system
- [ ] **VERIFY**: System catches all known errors
- [ ] **VERIFY**: Performance meets SLAs
- [ ] **VERIFY**: Alerting works end-to-end
- [ ] **VERIFY**: Dashboard shows accurate metrics
- [ ] **DOCUMENT**: Final validation report

#### Success Criteria
- ✅ Oculus case: All 8 compromised accounts detected
- ✅ Oculus case: Quality checks flag unreliable fields
- ✅ Oculus case: Breach alert triggered correctly
- ✅ All success metrics met (see below)

### Phase 4.3: SRE Handoff

**State**: PENDING

#### Tasks
- [ ] **HANDOFF**: Transfer ownership to SRE team
- [ ] **HANDOFF**: Review maintenance runbooks
- [ ] **HANDOFF**: Set up quarterly maintenance calendar
- [ ] **HANDOFF**: Document on-call escalation procedures
- [ ] **HANDOFF**: Archive project artifacts
- [ ] **CLOSURE**: Mark project COMPLETE in tracking system

#### Success Criteria
- ✅ SRE team accepts ownership
- ✅ Quarterly maintenance scheduled
- ✅ On-call procedures documented
- ✅ All project artifacts archived

### Phase 4 Deliverables
1. Production system deployed and operational
2. Final validation report
3. SRE handoff package
4. Project closure documentation

---

## Success Metrics (Final Validation)

### Primary Metrics

| Metric | Baseline | Target | Actual | Status |
|--------|----------|--------|--------|--------|
| **Forensic Error Rate** | 15-25% | 2-4% | TBD | 📋 |
| **PIR-OCULUS Class Errors** | 1/year | 0/12 months | TBD | 📋 |
| **Import Quality Check Time** | N/A | <1 minute | TBD | 📋 |
| **Unknown Code Detection** | Manual | <24 hours | TBD | 📋 |
| **Test Coverage** | 0% | 100% | TBD | 📋 |

### Secondary Metrics

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| **Import Performance (10K events)** | <2 seconds | TBD | 📋 |
| **Import Performance (100K events)** | <20 seconds | TBD | 📋 |
| **Alert False Positive Rate** | <5% | TBD | 📋 |
| **Analyst Satisfaction** | 95%+ | TBD | 📋 |
| **SRE Maintenance Time** | <1 hour/week | TBD | 📋 |

---

## Multi-Context Tracking Protocol

### Checkpoint System

**Automatic Checkpoints**: Every 10 tool uses OR phase boundary
**Manual Checkpoints**: On request via `save state`

**Checkpoint Contents**:
1. Current phase and state
2. Completed tasks (marked in todos)
3. Current work-in-progress
4. Blockers or decisions needed
5. Next 3 tasks to execute

### Context Handoff Protocol

When context window fills (>150K tokens) or session ends:

1. **Save State**: `python3 claude/tools/sre/save_state.py`
2. **Update Tracking**: Mark completed tasks in tracking database
3. **Document Handoff**: Write checkpoint to PROJECT_PLAN.md
4. **Next Steps**: Explicitly state next 3 tasks for continuation

### Progress Queries

```bash
# Check current phase and status
sqlite3 claude/data/databases/system/project_tracking.db \
  "SELECT * FROM project_status WHERE project_id='M365-DQ-2026-001'"

# Get incomplete tasks for current phase
sqlite3 claude/data/databases/system/project_tracking.db \
  "SELECT * FROM project_tasks WHERE phase='PHASE_1' AND status<>'COMPLETE'"

# Get overall progress percentage
sqlite3 claude/data/databases/system/project_tracking.db \
  "SELECT
     COUNT(CASE WHEN status='COMPLETE' THEN 1 END) * 100.0 / COUNT(*) as progress_pct
   FROM project_tasks
   WHERE project_id='M365-DQ-2026-001'"
```

---

## Checkpoint Log

### Checkpoint #0: 2026-01-06 (Project Initialization)

**Phase**: PHASE_0_SETUP
**State**: DISCOVERY
**Completed**:
- Created comprehensive project plan (this document)

**In Progress**:
- Setting up project tracking database

**Next 3 Tasks**:
1. Create project_tracking tables in system database
2. Initialize test infrastructure (tests/m365_ir/data_quality/)
3. Design status_code_reference schema

**Blockers**: None
**Decisions Needed**: None

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **Normalized views too slow** | MEDIUM | MEDIUM | Materialized table alternative ready |
| **Lookup tables decay** | MEDIUM | HIGH | Automated quarterly maintenance |
| **False sense of security** | MEDIUM | HIGH | Training emphasizes 80-90% reduction, not 100% |
| **Quality checks block valid import** | LOW | MEDIUM | Manual override flag + feature flags |
| **SRE capacity constraints** | MEDIUM | HIGH | Automate maintenance, reduce to <1 hr/week |
| **Microsoft API changes** | HIGH | MEDIUM | Schema versioning + deprecation tracking |
| **Multi-context loss of state** | MEDIUM | HIGH | Checkpoint every 10 tools + database tracking |

---

## Notes

### Design Decisions

1. **TDD Mandatory**: Tests written before implementation for all code
2. **Database-First**: All tracking persists in SQLite for cross-context continuity
3. **Phased Rollout**: Cannot skip phases, each must pass review
4. **SRE Collaboration**: Architecture decisions require SRE agent review
5. **Checkpoint Discipline**: Every 10 tools OR phase boundary

### Lessons Learned (Will Update Throughout)

- TBD (updated as project progresses)

---

**Last Updated**: 2026-01-06
**Next Review**: End of Phase 0 (Week 0)
**Project Lead**: Claude (SRE Principal Engineer Agent)
