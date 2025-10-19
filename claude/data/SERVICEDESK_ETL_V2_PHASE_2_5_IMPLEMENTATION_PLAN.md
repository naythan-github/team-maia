# ServiceDesk ETL V2 - Phase 2-5 Implementation Plan

**Created**: 2025-10-19
**Status**: Ready for Implementation
**Estimated Effort**: 8-12 hours remaining
**Current Progress**: 40% complete (Phase 0-1 done)

---

## Session 2 Objectives

Complete the remaining 60% of the V2 SRE-hardened ETL pipeline:
- Phase 2: Enhanced Data Cleaner (2h)
- Phase 3: Enhanced Migration Script (3h)
- Phase 4: Documentation (2h)
- Phase 5: Load Testing & Validation (4h)

**Target**: 100% V2 pipeline complete with full test coverage

---

## Phase 2: Enhanced Data Cleaner (2 hours)

### Deliverable
**File**: `claude/tools/sre/servicedesk_etl_data_cleaner_enhanced.py` (~400 lines)
**Tests**: `tests/test_servicedesk_etl_data_cleaner_enhanced.py` (~350 lines)

### Core Requirements

#### 1. Transaction Management (CRITICAL)
```python
def clean_database(source_db: str, output_db: str, config: dict) -> dict:
    """
    Clean SQLite database with atomic transaction.

    CRITICAL: Never modify source database in-place
    """
    # Verify source and output are different
    if source_db == output_db:
        raise ValueError("Source and output must be different files")

    # Copy source to output
    shutil.copy(source_db, output_db)

    # Clean output database in transaction
    conn = sqlite3.connect(output_db)
    try:
        conn.execute("BEGIN EXCLUSIVE")  # Lock database

        # Cleaning operations
        stats = {
            'dates_standardized': clean_dates(conn, config),
            'empty_strings_converted': clean_empty_strings(conn),
            'quality_score_before': None,
            'quality_score_after': None
        }

        # Validate results
        quality_score = score_quality(conn)
        if quality_score < config.get('min_quality', 80):
            raise ValueError(f"Quality {quality_score} below threshold")

        conn.commit()  # SUCCESS
        return stats

    except Exception as e:
        conn.rollback()  # ROLLBACK
        conn.close()
        os.remove(output_db)  # Delete partial results
        raise CleaningError(f"Cleaning failed: {e}")
```

#### 2. Date Format Standardization
```python
def standardize_dates(conn: sqlite3.Connection, table: str, column: str) -> int:
    """
    Convert DD/MM/YYYY and other formats to YYYY-MM-DD HH:MM:SS

    Patterns to detect and convert:
    - DD/MM/YYYY H:MM → YYYY-MM-DD HH:MM:SS
    - D/MM/YYYY H:MM → YYYY-MM-DD HH:MM:SS
    - MM/DD/YYYY (ambiguous, flag for manual review)

    Returns: Number of rows converted
    """
    cursor = conn.cursor()

    # Get all date values
    cursor.execute(f'SELECT rowid, "{column}" FROM {table} WHERE "{column}" LIKE "%/%"')
    rows_to_update = cursor.fetchall()

    converted = 0
    for rowid, date_str in rows_to_update:
        try:
            # Try DD/MM/YYYY pattern
            match = re.match(r'(\d{1,2})/(\d{1,2})/(\d{4})\s*(\d{1,2}):(\d{2})', date_str)
            if match:
                day, month, year, hour, minute = match.groups()
                standardized = f"{year}-{month:0>2}-{day:0>2} {hour:0>2}:{minute}:00"

                cursor.execute(
                    f'UPDATE {table} SET "{column}" = ? WHERE rowid = ?',
                    (standardized, rowid)
                )
                converted += 1
        except Exception:
            # Log but continue
            pass

    return converted
```

#### 3. Empty String → NULL Conversion
```python
def convert_empty_to_null(conn: sqlite3.Connection, table: str, columns: List[str]) -> int:
    """
    Convert empty strings to NULL for specified columns

    Returns: Number of rows updated
    """
    total_updated = 0

    for column in columns:
        cursor = conn.cursor()
        cursor.execute(
            f'UPDATE {table} SET "{column}" = NULL WHERE "{column}" = ""'
        )
        total_updated += cursor.rowcount

    return total_updated
```

#### 4. Health Checks & Progress Tracking
```python
def clean_with_health_checks(conn: sqlite3.Connection, total_rows: int):
    """
    Clean data with periodic health checks
    """
    from claude.tools.sre.servicedesk_etl_observability import (
        ProgressTracker, check_disk_space_health, check_memory_health
    )

    tracker = ProgressTracker(total_rows=total_rows)
    processed = 0
    batch_size = 1000

    for offset in range(0, total_rows, batch_size):
        # Health check every 10K rows
        if processed % 10000 == 0:
            disk = check_disk_space_health(threshold_gb=1.0)
            if not disk['healthy']:
                raise HealthCheckError("Disk space critically low")

            memory = check_memory_health(threshold_percent=90)
            if not memory['healthy']:
                raise HealthCheckError("Memory usage critically high")

        # Process batch
        clean_batch(conn, offset, batch_size)
        processed += batch_size
        tracker.update(rows_processed=processed)
```

### Test Cases (TDD)

```python
# tests/test_servicedesk_etl_data_cleaner_enhanced.py

class TestTransactionManagement:
    def test_clean_to_new_file_never_modifies_source():
        """CRITICAL: Verify source database never modified"""

    def test_cleaning_rolls_back_on_error():
        """Verify transaction rollback on any error"""

    def test_output_file_deleted_on_rollback():
        """Verify partial output deleted on failure"""

class TestDateStandardization:
    def test_converts_ddmmyyyy_to_iso():
        """Verify DD/MM/YYYY → YYYY-MM-DD conversion"""

    def test_handles_single_digit_days_months():
        """Verify D/M/YYYY → YYYY-MM-DD conversion"""

    def test_preserves_already_standard_dates():
        """Verify YYYY-MM-DD dates unchanged"""

class TestEmptyStringConversion:
    def test_converts_empty_strings_to_null():
        """Verify '' → NULL in date columns"""

    def test_preserves_actual_null_values():
        """Verify NULL values unchanged"""

class TestHealthChecks:
    def test_halts_on_low_disk_space():
        """Verify cleaning halts when disk <1GB"""

    def test_halts_on_high_memory_usage():
        """Verify cleaning halts when memory >90%"""

class TestIntegration:
    def test_phase1_database_cleaning_roundtrip():
        """End-to-end test with Phase 1 database"""
```

### Success Criteria
- ✅ Source database NEVER modified (atomic guarantee)
- ✅ Transaction rollback on any error
- ✅ Converts 9 DD/MM/YYYY dates to YYYY-MM-DD (Phase 1 data)
- ✅ Converts empty strings to NULL
- ✅ Quality score improves +20-30 points
- ✅ Health checks prevent resource exhaustion
- ✅ Progress tracking (<1ms overhead)

---

## Phase 3: Enhanced Migration Script (3 hours)

### Deliverable
**File**: `claude/infrastructure/servicedesk-dashboard/migration/migrate_sqlite_to_postgres_enhanced.py` (~700 lines)
**Tests**: `tests/test_migrate_sqlite_to_postgres_enhanced.py` (~400 lines)

### Core Requirements

#### 1. Quality Gate Integration
```python
def migrate_with_quality_gate(source_db: str, postgres_conn, min_quality: int = 80):
    """
    Migration with quality gate validation
    """
    from claude.tools.sre.servicedesk_etl_data_profiler import profile_database
    from claude.tools.sre.servicedesk_quality_scorer import score_database

    # Pre-migration profiling
    profile = profile_database(source_db)

    # Check circuit breaker
    if profile['circuit_breaker']['should_halt']:
        raise MigrationError(
            f"Circuit breaker halt: {profile['circuit_breaker']['reason']}"
        )

    # Check quality score
    quality = score_database(source_db)
    if quality < min_quality:
        raise MigrationError(
            f"Quality {quality} below threshold {min_quality}"
        )

    # Proceed with migration
    return migrate_database(source_db, postgres_conn)
```

#### 2. Canary Deployment
```python
def canary_migration(source_db: str, postgres_conn, sample_rate: float = 0.10):
    """
    Test migration on 10% sample before full migration
    """
    # Create 10% sample
    sample_db = create_sample_database(source_db, sample_rate)

    try:
        # Migrate sample to temp schema
        migrate_to_schema(sample_db, postgres_conn, schema='servicedesk_canary')

        # Validate sample migration
        validate_migration(sample_db, postgres_conn, schema='servicedesk_canary')

        # Run test queries
        run_test_queries(postgres_conn, schema='servicedesk_canary')

        # SUCCESS: Drop canary, proceed with full
        drop_schema(postgres_conn, 'servicedesk_canary')

    except Exception as e:
        drop_schema(postgres_conn, 'servicedesk_canary')
        raise CanaryError(f"Canary migration failed: {e}")

    # Full migration
    return migrate_to_schema(source_db, postgres_conn, schema='servicedesk')
```

#### 3. Blue-Green Deployment
```python
def migrate_blue_green(source_db: str, postgres_conn):
    """
    Zero-downtime migration with versioned schemas
    """
    new_schema = f"servicedesk_v{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    try:
        # Create new schema
        create_schema(postgres_conn, new_schema)

        # Migrate to new schema
        migrate_to_schema(source_db, postgres_conn, schema=new_schema)

        # Validate
        validate_migration(source_db, postgres_conn, schema=new_schema)

        # Ready for cutover
        return {
            'status': 'success',
            'new_schema': new_schema,
            'cutover_command': f'UPDATE datasource SET schema=\'{new_schema}\'',
            'rollback_command': f'UPDATE datasource SET schema=\'servicedesk_old\''
        }

    except Exception as e:
        drop_schema(postgres_conn, new_schema)
        raise MigrationError(f"Migration failed: {e}")
```

#### 4. Enhanced Rollback
```python
def migrate_with_rollback(source_db: str, postgres_conn, schema: str = 'servicedesk'):
    """
    Migration with automatic rollback on failure
    """
    # Pre-migration backup
    backup_path = None
    if schema_exists(postgres_conn, schema):
        backup_path = backup_postgres_schema(schema)

    try:
        # Begin transaction
        postgres_conn.execute("BEGIN")

        # Drop and recreate schema
        drop_schema(postgres_conn, schema)
        create_schema(postgres_conn, schema)

        # Migrate
        migrate_to_schema(source_db, postgres_conn, schema)

        # Validate
        validate_migration(source_db, postgres_conn, schema)

        # Commit
        postgres_conn.execute("COMMIT")

    except Exception as e:
        # Rollback
        postgres_conn.execute("ROLLBACK")

        # Restore from backup
        if backup_path:
            restore_postgres_schema(backup_path)

        raise MigrationError(f"Migration failed and rolled back: {e}")
```

### Test Cases

```python
class TestQualityGate:
    def test_rejects_migration_below_quality_threshold():
        """Verify quality gate blocks poor data"""

    def test_proceeds_with_high_quality_data():
        """Verify quality gate allows good data"""

class TestCanaryDeployment:
    def test_canary_validates_before_full_migration():
        """Verify 10% sample tested first"""

    def test_canary_failure_prevents_full_migration():
        """Verify full migration blocked on canary failure"""

class TestBlueGreen:
    def test_creates_versioned_schema():
        """Verify new schema has timestamp version"""

    def test_enables_instant_rollback():
        """Verify old schema preserved for rollback"""

class TestEnhancedRollback:
    def test_restores_from_backup_on_failure():
        """Verify automatic restore from pg_dump backup"""

    def test_transaction_rollback_on_validation_failure():
        """Verify ROLLBACK on post-migration validation failure"""
```

### Success Criteria
- ✅ Creates correct TIMESTAMP columns (not TEXT)
- ✅ Handles Phase 1 date format edge cases
- ✅ Post-migration quality ≥ pre-migration
- ✅ Zero manual schema fixes required
- ✅ Canary deployment validates before full migration
- ✅ Rollback tested and reliable
- ✅ Blue-green enables zero-downtime cutover

---

## Phase 4: Documentation (2 hours)

### Deliverables

#### 4.1: Query Template Library
**File**: `claude/infrastructure/servicedesk-dashboard/query_templates.sql` (~200 lines)

```sql
-- Template: All 23 Dashboard Metrics with PostgreSQL-Compatible Syntax

-- 1. Average Quality Score
-- PostgreSQL quirk: ROUND() requires ::numeric cast for REAL columns
SELECT ROUND(AVG(quality_score)::numeric, 2) as avg_quality
FROM comment_quality
WHERE quality_score IS NOT NULL;

-- 2. Resolution Time (days)
-- PostgreSQL feature: EXTRACT(EPOCH FROM ...) for date arithmetic
SELECT ROUND(
    AVG(
        EXTRACT(EPOCH FROM ("TKT-Actual Resolution Date" - "TKT-Created Time"))
        / 86400  -- Convert seconds to days
    )::numeric,
    2
) as avg_resolution_days
FROM tickets
WHERE "TKT-Status" IN ('Closed', 'Resolved')
  AND "TKT-Actual Resolution Date" IS NOT NULL;

-- [... 21 more metrics ...]
```

#### 4.2: Operational Runbook
**File**: `claude/data/SERVICEDESK_ETL_OPERATIONAL_RUNBOOK.md` (~500 lines)

**Sections**:
1. Deployment Checklist (pre/during/post deployment)
2. Common Operations (quarterly import, manual fixes)
3. Troubleshooting Guide (quality gate failures, migration errors)
4. Rollback Procedures (emergency rollback, testing rollback)
5. Monitoring & Alerts (key metrics, alert thresholds)
6. Emergency Contacts & Escalation

#### 4.3: Monitoring Guide
**File**: `claude/data/SERVICEDESK_ETL_MONITORING_GUIDE.md` (~300 lines)

**Sections**:
1. Key Metrics (profiler_duration, quality_score, errors_total)
2. Alert Configuration (CRITICAL, WARNING thresholds)
3. Grafana Dashboard Setup
4. Log Aggregation (structured JSON logs)
5. Performance Baselines

#### 4.4: Best Practices Guide (Enhanced)
**File**: `claude/data/SERVICEDESK_ETL_BEST_PRACTICES.md` (~400 lines)

**New Sections for V2**:
1. Transaction Management Patterns
2. Idempotency Strategies
3. Circuit Breaker Design Principles
4. Failure Mode Analysis
5. Production Deployment Patterns

---

## Phase 5: Load Testing & Validation (4 hours)

### Deliverables

#### 5.1: Performance Test Suite
**File**: `tests/test_performance.py` (~400 lines)

```python
def test_profiler_meets_5min_sla():
    """Verify profiler completes in <5 min on 260K rows"""
    db = create_test_db(rows=260000)

    start = time.time()
    profile_database(db, sample_size=5000)
    elapsed = time.time() - start

    assert elapsed < 300, f"Profiler took {elapsed}s (SLA: 300s)"

def test_cleaner_meets_15min_sla():
    """Verify cleaner completes in <15 min on 260K rows"""

def test_migration_meets_5min_sla():
    """Verify migration completes in <5 min on 260K rows"""

def test_full_pipeline_meets_25min_sla():
    """Verify full pipeline completes in <25 min"""
```

#### 5.2: Stress Test Suite
**File**: `tests/test_stress.py` (~300 lines)

```python
def test_linear_scaling_to_520k_rows():
    """Verify linear scaling to 2x data volume"""

def test_memory_usage_bounded():
    """Verify profiler uses <500MB for 1M rows"""

def test_concurrent_operations_prevented():
    """Verify migration lock prevents concurrent runs"""
```

#### 5.3: Failure Injection Test Suite
**File**: `tests/test_failure_injection.py` (~400 lines)

```python
def test_network_failure_rollback():
    """Verify rollback on PostgreSQL connection loss"""

def test_disk_full_handling():
    """Verify graceful failure on disk full"""

def test_process_kill_recovery():
    """Verify idempotency allows safe retry"""
```

#### 5.4: Regression Test Suite
**File**: `tests/test_phase1_regressions.py` (~300 lines)

```python
def test_timestamp_type_mismatch_detected():
    """Verify profiler detects TIMESTAMP label with TEXT data"""

def test_ddmmyyyy_date_format_converted():
    """Verify cleaner converts DD/MM/YYYY to YYYY-MM-DD"""

def test_empty_strings_converted_to_null():
    """Verify cleaner converts empty strings to NULL"""

def test_postgres_round_casting_works():
    """Verify query templates work with PostgreSQL"""
```

---

## Implementation Strategy

### Session 2 Workflow

**Hour 1-2: Phase 2 (Enhanced Cleaner)**
1. Create TDD test suite (45 min)
2. Implement core functionality (60 min)
3. Run tests, fix failures (15 min)

**Hour 3-5: Phase 3 (Enhanced Migration)**
1. Create TDD test suite (60 min)
2. Implement quality gate + canary (90 min)
3. Run tests, fix failures (30 min)

**Hour 6-7: Phase 4 (Documentation)**
1. Query templates (45 min)
2. Operational runbook (45 min)
3. Monitoring guide + best practices (30 min)

**Hour 8-11: Phase 5 (Load Testing)**
1. Performance tests (90 min)
2. Stress tests (60 min)
3. Failure injection tests (60 min)
4. Regression tests (30 min)

**Hour 12: Final Validation**
1. Run full test suite (all 150+ tests)
2. Update documentation
3. Create final save state
4. Git commit + push

---

## Success Metrics

### Code Quality
- **Target**: 100% test coverage maintained
- **Expected**: 150+ tests passing
- **Lines**: ~3,500 additional lines (implementation + tests)

### Performance
- **Profiler**: <5 min for 260K rows
- **Cleaner**: <15 min for 260K rows
- **Migration**: <5 min for 260K rows
- **Full Pipeline**: <25 min total

### Reliability
- **Zero false negatives**: All Phase 1 issues detected
- **100% rollback success**: All failure modes handled
- **Graceful degradation**: Health checks prevent catastrophic failures

---

## Key Files to Reference

### Existing Phase 0-1 Tools
```
claude/tools/sre/
├── servicedesk_etl_preflight.py (419 lines)
├── servicedesk_etl_backup.py (458 lines)
├── servicedesk_etl_observability.py (453 lines)
└── servicedesk_etl_data_profiler.py (582 lines)

tests/
├── test_servicedesk_etl_preflight.py (350 lines)
├── test_servicedesk_etl_backup.py (436 lines)
├── test_servicedesk_etl_observability.py (440 lines)
└── test_servicedesk_etl_data_profiler.py (470 lines)
```

### Phase 127 Tools (for integration)
```
claude/tools/sre/
├── servicedesk_etl_validator.py (792 lines)
├── servicedesk_etl_cleaner.py (612 lines - enhance this for Phase 2)
└── servicedesk_quality_scorer.py (705 lines)
```

### Existing Migration Script (to enhance)
```
claude/infrastructure/servicedesk-dashboard/migration/
└── migrate_sqlite_to_postgres.py (354 lines - enhance for Phase 3)
```

---

## Pre-Session 2 Checklist

Before starting Session 2:

1. ✅ Review Phase 0-1 implementations
2. ✅ Read this implementation plan completely
3. ✅ Verify Phase 127 tools are accessible
4. ✅ Have Phase 1 test database available (servicedesk_tickets.db)
5. ✅ PostgreSQL Docker container running
6. ✅ Fresh terminal session with clean token budget

---

## Expected Final State

### After Session 2 Completion

**Files Created**: 12 new files
- 4 implementation files (cleaner, migration, templates, tests)
- 4 documentation files (runbook, monitoring, best practices, templates)
- 4 test suites (performance, stress, failure injection, regression)

**Total Project Stats**:
- Implementation: ~5,400 lines
- Tests: ~3,500 lines
- Documentation: ~1,400 lines
- **Total**: ~10,300 lines
- **Test Coverage**: 150+ tests, 100% passing

**Production Readiness**: Complete V2 SRE-hardened ETL pipeline
- ✅ All 8 critical gaps addressed
- ✅ Full observability
- ✅ Complete rollback capability
- ✅ Comprehensive documentation
- ✅ Performance validated
- ✅ Zero manual post-migration fixes

---

**Status**: Ready for Session 2 Implementation
**Confidence**: 95% - Clear plan, solid foundation, proven TDD approach
