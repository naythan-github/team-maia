# TDD Sprint Plan: PMP Data Consolidation

**Sprint ID**: SPRINT-PMP-CONSOLIDATE-001
**Created**: 2026-01-15
**Author**: SRE Principal Engineer Agent
**Status**: PENDING APPROVAL
**Predecessor**: SPRINT-INTEL-FRAMEWORK-001 (Unified Intelligence Framework)

---

## Problem Statement

PMP data extraction has accumulated technical debt across multiple phases (188-191), resulting in:

| Issue | Impact | Current State |
|-------|--------|---------------|
| 4 extractors → 3 databases | No unified view | pmp_config.db, pmp_resilient.db, pmp_systemreports.db |
| Empty metric tables | Can't track patch health | patch_metrics, severity_metrics, system_health_metrics = 0 rows |
| No snapshot tracking | Can't trend analysis | snapshots = 0 rows |
| Missing API coverage | Incomplete data | vulnerabilities, deploymenttasks endpoints not called |
| 2 empty databases | Wasted schema | pmp_complete_intelligence.db, pmp_patch_systems.db |

### Data Fragmentation Map

```
Current Architecture (Fragmented):
┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│ pmp_config.db       │  │ pmp_resilient.db    │  │ pmp_systemreports   │
│ 114 MB              │  │ 1.7 MB              │  │ 267 MB              │
├─────────────────────┤  ├─────────────────────┤  ├─────────────────────┤
│ all_patches: 12,559 │  │ systems: 2,799      │  │ systems: 3,359      │
│ all_systems: 3,332  │  │ checkpoints: 3      │  │ system_reports:     │
│ supported_patches:  │  │ extraction_gaps: 17 │  │   127,928           │
│   43,182            │  │                     │  │                     │
│ scan_details: 3,272 │  │ (11 empty tables)   │  │                     │
│ missing_patches:    │  │                     │  │                     │
│   1,672             │  │                     │  │                     │
│ (11 empty tables)   │  │                     │  │                     │
└─────────────────────┘  └─────────────────────┘  └─────────────────────┘
        ↓                         ↓                        ↓
        └─────────────────────────┼────────────────────────┘
                                  ↓
                    Target: pmp_intelligence.db (unified)
```

---

## Solution: Unified PMP Intelligence Database

### Target Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    pmp_intelligence.db                           │
├─────────────────────────────────────────────────────────────────┤
│ Core Tables (Raw Data)                                          │
│ ├── snapshots              → Extraction run tracking            │
│ ├── systems                → All system inventory               │
│ ├── patches                → All patch definitions              │
│ ├── patch_system_mapping   → Which systems need which patches   │
│ └── vulnerabilities        → CVE mappings (NEW)                 │
├─────────────────────────────────────────────────────────────────┤
│ Metric Tables (Calculated per snapshot)                         │
│ ├── patch_metrics          → Missing/installed counts           │
│ ├── severity_metrics       → Critical/high/medium/low counts    │
│ ├── system_health_metrics  → Healthy/unhealthy system counts    │
│ └── vulnerability_metrics  → CVE exposure counts (NEW)          │
├─────────────────────────────────────────────────────────────────┤
│ Policy Tables                                                   │
│ ├── deployment_policies    → Patch deployment configs           │
│ ├── deployment_tasks       → Deployment history (NEW)           │
│ └── compliance_checks      → Essential Eight compliance         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Model & Subagent Selection

| Phase | Model | Subagent | Rationale |
|-------|-------|----------|-----------|
| P0 | Sonnet | Explore | Schema research requires codebase exploration |
| P1 | Sonnet | general-purpose | Data migration requires careful SQL, integrity checks |
| P2 | Sonnet | general-purpose | Metrics calculation requires accurate aggregation SQL |
| P3 | Sonnet | general-purpose | API integration requires error handling |
| P4 | Sonnet | general-purpose | Orchestration complexity, snapshot management |
| P5 | Sonnet | general-purpose | Compliance logic accuracy critical |
| P6 | Sonnet | general-purpose | Backward compatibility requires careful refactoring |
| P7 | Haiku | general-purpose | Documentation and cleanup, less complex |

**No Haiku for code phases** because:
1. Data migration must preserve integrity (127,928+ records)
2. SQL aggregations must be accurate for compliance reporting
3. API error handling requires careful design
4. Snapshot tracking logic is critical for trend analysis

---

## Sprint Phases

### P0: Schema Design & Migration Planning
**Goal**: Design unified schema, plan data migration
**Model**: Sonnet
**Subagent**: Explore (codebase research for existing schemas)

#### Deliverables
- `claude/tools/pmp/pmp_unified_schema.sql`
- Migration mapping document

#### Tests (4 tests)
```python
# tests/test_pmp_unified_schema.py

class TestSchemaDesign:
    def test_schema_creates_all_tables(self):
        """Schema creates 12 required tables."""

    def test_schema_has_snapshot_foreign_keys(self):
        """All metric tables have snapshot_id FK."""

    def test_schema_has_proper_indexes(self):
        """Performance indexes on key lookup columns."""

    def test_schema_compatible_with_base_intelligence(self):
        """Schema supports BaseIntelligenceService interface."""
```

**Gate**: Schema review approved

---

### P1: Data Migration Tool
**Goal**: Migrate existing data to unified database
**Model**: Sonnet
**Subagent**: general-purpose (data integrity critical)

#### Files to Create
- `claude/tools/pmp/pmp_data_migrator.py`

#### Tests (8 tests)
```python
# tests/test_pmp_data_migrator.py

class TestMigrationPreparation:
    def test_detect_source_databases(self):
        """Finds all 3 source databases."""

    def test_validate_source_schemas(self):
        """Validates source table structures."""

class TestDataMigration:
    def test_migrate_systems_deduplicates(self):
        """Merges systems from config, resilient, systemreports."""

    def test_migrate_patches_preserves_all(self):
        """All 12,559 patches migrated."""

    def test_migrate_system_reports_to_mapping(self):
        """127,928 system_reports → patch_system_mapping."""

    def test_creates_initial_snapshot(self):
        """Creates snapshot_id=1 for migrated data."""

class TestMigrationIntegrity:
    def test_no_data_loss(self):
        """Record counts match source databases."""

    def test_foreign_keys_valid(self):
        """All FKs resolve to valid records."""
```

**Gate**: 8/8 tests pass, data integrity verified

---

### P2: Metrics Calculation Engine
**Goal**: Calculate derived metrics from raw data
**Model**: Sonnet
**Subagent**: general-purpose (SQL aggregation accuracy)

#### Files to Create
- `claude/tools/pmp/pmp_metrics_calculator.py`

#### Tests (10 tests)
```python
# tests/test_pmp_metrics_calculator.py

class TestMetricsCalculatorImport:
    def test_import_calculator(self):
        """MetricsCalculator importable."""

class TestPatchMetrics:
    def test_calculate_patch_metrics(self):
        """Calculates missing/installed/applicable counts."""

    def test_patch_metrics_by_category(self):
        """Breaks down by OS, application, security."""

class TestSeverityMetrics:
    def test_calculate_severity_distribution(self):
        """Counts critical/high/medium/low."""

    def test_severity_trend_calculation(self):
        """Calculates delta from previous snapshot."""

class TestSystemHealthMetrics:
    def test_calculate_system_health(self):
        """Counts healthy/unhealthy/unknown systems."""

    def test_health_by_organization(self):
        """Breaks down by organization."""

class TestMetricsStorage:
    def test_metrics_linked_to_snapshot(self):
        """All metrics have snapshot_id."""

    def test_idempotent_calculation(self):
        """Recalculating doesn't duplicate."""

    def test_metrics_queryable(self):
        """Can query metrics by date range."""
```

**Gate**: 10/10 tests pass

---

### P3: Missing API Endpoints
**Goal**: Extract data from uncalled PMP API endpoints
**Model**: Sonnet
**Subagent**: general-purpose (API integration, error handling)

#### Files to Create
- `claude/tools/pmp/pmp_vulnerability_extractor.py`
- `claude/tools/pmp/pmp_deployment_extractor.py`

#### Tests (8 tests)
```python
# tests/test_pmp_additional_extractors.py

class TestVulnerabilityExtractor:
    def test_extract_vulnerabilities(self):
        """Calls /api/1.4/patch/vulnerabilities."""

    def test_maps_cve_to_patches(self):
        """Links CVE IDs to patch records."""

    def test_stores_cvss_scores(self):
        """Captures CVSS severity scores."""

class TestDeploymentExtractor:
    def test_extract_deployment_tasks(self):
        """Calls /api/1.4/patch/deploymenttasks."""

    def test_tracks_deployment_status(self):
        """Captures success/failure/pending."""

    def test_links_to_policies(self):
        """Links tasks to deployment_policies."""

class TestPatchGroupExtractor:
    def test_extract_patch_groups(self):
        """Calls /api/1.4/patch/patchgroups."""

    def test_maps_patches_to_groups(self):
        """Creates patch-group relationships."""
```

**Gate**: 8/8 tests pass

---

### P4: Unified Extractor
**Goal**: Single extractor that calls all endpoints with snapshot tracking
**Model**: Sonnet
**Subagent**: general-purpose (orchestration complexity)

#### Files to Create
- `claude/tools/pmp/pmp_unified_extractor.py`

#### Tests (12 tests)
```python
# tests/test_pmp_unified_extractor.py

class TestUnifiedExtractorImport:
    def test_import_extractor(self):
        """UnifiedPMPExtractor importable."""

class TestSnapshotManagement:
    def test_creates_snapshot_first(self):
        """Creates snapshot record before extraction."""

    def test_links_all_data_to_snapshot(self):
        """All extracted data has snapshot_id."""

    def test_marks_snapshot_complete(self):
        """Sets snapshot.status = 'complete' on success."""

    def test_marks_snapshot_failed(self):
        """Sets snapshot.status = 'failed' on error."""

class TestEndpointCoverage:
    def test_calls_all_endpoints(self):
        """Calls all 15 PMP API endpoints."""

    def test_handles_endpoint_failures(self):
        """Continues on individual endpoint failure."""

    def test_records_endpoint_status(self):
        """Logs success/failure per endpoint."""

class TestMetricsIntegration:
    def test_triggers_metrics_calculation(self):
        """Calls MetricsCalculator after extraction."""

    def test_metrics_linked_to_snapshot(self):
        """Calculated metrics have correct snapshot_id."""

class TestSchedulerIntegration:
    def test_works_with_collection_scheduler(self):
        """Can be called by CollectionScheduler."""

    def test_refresh_command_format(self):
        """CLI interface matches scheduler config."""
```

**Gate**: 12/12 tests pass

---

### P5: Compliance Checks
**Goal**: Implement Essential Eight compliance evaluation
**Model**: Sonnet
**Subagent**: general-purpose (compliance logic accuracy)

#### Files to Create
- `claude/tools/pmp/pmp_compliance_checker.py`

#### Tests (8 tests)
```python
# tests/test_pmp_compliance_checker.py

class TestComplianceCheckerImport:
    def test_import_checker(self):
        """ComplianceChecker importable."""

class TestEssentialEightChecks:
    def test_patch_applications_maturity(self):
        """Calculates E8 Patch Applications maturity level."""

    def test_critical_patch_sla(self):
        """Checks critical patches applied within 48 hours."""

    def test_high_patch_sla(self):
        """Checks high patches applied within 2 weeks."""

class TestComplianceStorage:
    def test_stores_compliance_results(self):
        """Writes to compliance_checks table."""

    def test_compliance_linked_to_snapshot(self):
        """Results have snapshot_id."""

    def test_compliance_history_queryable(self):
        """Can query compliance trend over time."""

class TestComplianceReporting:
    def test_generate_compliance_report(self):
        """Generates human-readable compliance report."""
```

**Gate**: 8/8 tests pass

---

### P6: PMPIntelligenceService Update
**Goal**: Update service to use unified database
**Model**: Sonnet
**Subagent**: general-purpose (backward compatibility critical)

#### Files to Modify
- `claude/tools/pmp/pmp_intelligence_service.py`

#### Tests (6 additional tests)
```python
# tests/test_pmp_intelligence_service.py (additions)

class TestUnifiedDatabaseIntegration:
    def test_uses_unified_database(self):
        """Points to pmp_intelligence.db."""

    def test_queries_with_snapshot_filter(self):
        """Can filter by snapshot_id."""

    def test_get_latest_snapshot(self):
        """Returns most recent snapshot data."""

class TestNewQueryMethods:
    def test_get_vulnerability_exposure(self):
        """Returns CVE exposure summary."""

    def test_get_compliance_status(self):
        """Returns current compliance maturity."""

    def test_get_deployment_history(self):
        """Returns recent deployment tasks."""
```

**Gate**: All existing tests pass + 6 new tests

---

### P7: Cleanup & Documentation
**Goal**: Remove legacy databases, update documentation
**Model**: Haiku
**Subagent**: general-purpose (documentation, less complex)

#### Tasks
1. Archive legacy databases to `~/.maia/archive/pmp_legacy/`
2. Update scheduler config to use unified extractor
3. Update capability registration
4. Create migration guide

#### Files to Create/Modify
- `claude/context/knowledge/pmp/pmp_unified_quickstart.md`
- `claude/agents/sre_principal_engineer_agent.md` (update PMP section)

**Gate**: Documentation review, legacy DBs archived

---

## Test Summary

| Phase | Tests | Focus |
|-------|-------|-------|
| P0 | 4 | Schema design |
| P1 | 8 | Data migration |
| P2 | 10 | Metrics calculation |
| P3 | 8 | Additional extractors |
| P4 | 12 | Unified extractor |
| P5 | 8 | Compliance checks |
| P6 | 6 | Service update |
| **Total** | **56** | |

---

## Dependencies

| Dependency | Purpose | Required |
|------------|---------|----------|
| requests | PMP API calls | Yes |
| sqlite3 | Database operations | Yes (stdlib) |
| BaseIntelligenceService | Service interface | Yes (from P1-INTEL) |

---

## Success Criteria

1. **56/56 tests pass**
2. **Single unified database** (`pmp_intelligence.db`)
3. **All metric tables populated** with calculated data
4. **Snapshot tracking** enables trend analysis
5. **Compliance checks** provide Essential Eight maturity
6. **Legacy databases archived** (not deleted)
7. **PMPIntelligenceService** backward compatible

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Data loss during migration | Migrate to NEW db, keep originals |
| API endpoint changes | Validate schema before extraction |
| Backward compatibility breaks | Run all existing tests before/after |
| Large data volumes | Batch processing, progress tracking |

---

## Estimated Effort

| Phase | Effort |
|-------|--------|
| P0 | 1 hr |
| P1 | 2 hrs |
| P2 | 2 hrs |
| P3 | 2 hrs |
| P4 | 3 hrs |
| P5 | 2 hrs |
| P6 | 1.5 hrs |
| P7 | 1 hr |
| **Total** | **~14-15 hours** |

---

## Approval Request

**Ready for implementation?**

- [ ] Approve plan as-is
- [ ] Request modifications
- [ ] Defer to future sprint
