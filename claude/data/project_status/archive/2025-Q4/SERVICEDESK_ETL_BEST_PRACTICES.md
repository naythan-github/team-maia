# ServiceDesk ETL V2 - Best Practices Guide

**Version**: 2.0
**Date**: 2025-10-19
**Status**: Production Ready

---

## Core Principles

### 1. Never Modify Source Data In-Place

**Rationale**: Source data is irreplaceable. All transformations must preserve originals.

**V2 Implementation**:
- Phase 2 cleaner: `--source input.db --output input_clean.db`
- Atomic copy + transaction ensures source untouched
- MD5 verification confirms source integrity

**Anti-Pattern**:
```bash
# ❌ DON'T: Modify source directly
sqlite3 source.db "UPDATE tickets SET created_time = ..."
```

**Best Practice**:
```bash
# ✅ DO: Clean to new file
python3 claude/tools/sre/servicedesk_etl_data_cleaner_enhanced.py \
  --source source.db \
  --output source_clean.db
```

---

### 2. Always Backup Before Migration

**Rationale**: Migrations can fail. Rollback requires backups.

**V2 Implementation**:
- Phase 0 backup: Automatic timestamped backups with MD5 checksums
- PostgreSQL pg_dump: Schema backup before DROP/CREATE
- Retention policy: Keep backups for 30 days

**Best Practice**:
```bash
# Backup SQLite
python3 claude/tools/sre/servicedesk_etl_backup.py backup \
  --source db.db \
  --output /backups/ \
  --retention-days 30

# Backup PostgreSQL
docker exec servicedesk-postgres pg_dump \
  -U servicedesk_user \
  -d servicedesk \
  -n servicedesk \
  -F c \
  -f /backups/servicedesk_$(date +%Y%m%d_%H%M%S).backup
```

---

### 3. Quality Gate Everything

**Rationale**: Prevent bad data from reaching production dashboards.

**V2 Implementation**:
- Phase 1 profiler: Circuit breaker halts if >20% corrupt or >10% type mismatches
- Phase 2 scorer: Quality gate blocks migration if score <80
- Phase 3 canary: Test 10% sample before full migration

**Best Practice**:
```bash
# Run profiler first
python3 claude/tools/sre/servicedesk_etl_data_profiler.py \
  --source db.db \
  --use-validator \
  --use-scorer

# Check circuit breaker status
# If should_halt: true, FIX SOURCE before proceeding

# Migration with quality gate
python3 claude/infrastructure/servicedesk-dashboard/migration/migrate_sqlite_to_postgres_enhanced.py \
  --source db_clean.db \
  --mode canary \
  --min-quality 80
```

---

### 4. Transaction Safety

**Rationale**: Partial updates corrupt data. All-or-nothing commitment required.

**V2 Implementation**:
- Phase 2 cleaner: `BEGIN EXCLUSIVE → operations → COMMIT` or `ROLLBACK`
- Phase 3 migration: Transaction wrapper with automatic rollback on failure
- Output cleanup: Delete partial files on error

**Pattern**:
```python
conn = sqlite3.connect(output_db)
try:
    conn.execute("BEGIN EXCLUSIVE")  # Lock database

    # All cleaning operations
    clean_dates(conn)
    clean_empty_strings(conn)

    # Validate before commit
    if validate(conn):
        conn.commit()  # SUCCESS
    else:
        raise ValidationError()

except Exception as e:
    conn.rollback()  # ROLLBACK on any error
    os.remove(output_db)  # Delete partial output
    raise
```

---

### 5. Idempotency

**Rationale**: Pipelines must be safely re-runnable without side effects.

**V2 Implementation**:
- Cleaning operations detect already-cleaned data (no double-conversion)
- Migration can re-run to same schema (DROP + CREATE pattern)
- Blue-green mode enables multiple schema versions

**Test for Idempotency**:
```bash
# Run cleaner twice
python3 claude/tools/sre/servicedesk_etl_data_cleaner_enhanced.py \
  --source db.db --output db_clean1.db

python3 claude/tools/sre/servicedesk_etl_data_cleaner_enhanced.py \
  --source db_clean1.db --output db_clean2.db

# Second run should find nothing to clean
# dates_standardized: 0
# empty_strings_converted: 0
```

---

### 6. Observability First

**Rationale**: You can't fix what you can't see. Comprehensive logging essential.

**V2 Implementation**:
- Structured JSON logs: Timestamp, level, gate, message, context
- Prometheus metrics: Duration, errors, quality scores
- Progress tracking: Real-time ETA, rows/second rate
- Health checks: Periodic disk/memory monitoring

**Usage**:
```python
from claude.tools.sre.servicedesk_etl_observability import ETLLogger, ETLMetrics

logger = ETLLogger("Gate2_Cleaner")
metrics = ETLMetrics()

logger.info("Starting operation", rows=100000)
metrics.record("dates_standardized", 42)
```

---

### 7. Circuit Breakers

**Rationale**: Fail fast on unfixable data. Don't waste time on doomed migrations.

**V2 Thresholds**:
- Type mismatches >10% of columns → HALT
- Corrupt dates >20% of rows → HALT
- Quality score <50 → HALT (configurable)

**Implementation**:
```python
if type_mismatch_pct > 0.10:
    raise CircuitBreakerError("Type mismatches exceed 10% - FIX SOURCE")

if corrupt_date_pct > 0.20:
    raise CircuitBreakerError("Corrupt dates exceed 20% - FIX SOURCE")
```

---

### 8. Canary Deployments

**Rationale**: Test migrations on sample before risking full data.

**V2 Implementation**:
- Create 10% random sample database
- Migrate to `servicedesk_canary` schema
- Run validation queries
- Drop canary if successful
- Proceed with full migration

**Pattern**:
```python
# 1. Create 10% sample
sample_db = create_sample_database(source_db, sample_rate=0.10)

# 2. Migrate sample to canary schema
migrate_to_schema(sample_db, postgres_conn, schema='servicedesk_canary')

# 3. Validate canary
validate_migration(sample_db, postgres_conn, schema='servicedesk_canary')

# 4. Drop canary
drop_schema(postgres_conn, 'servicedesk_canary')

# 5. Full migration (canary passed)
migrate_to_schema(source_db, postgres_conn, schema='servicedesk')
```

---

### 9. Blue-Green Deployments

**Rationale**: Zero-downtime deployments with instant rollback capability.

**V2 Implementation**:
- Create versioned schema: `servicedesk_v20251019_143022`
- Migrate to new schema while old schema serves traffic
- Validate new schema
- Cutover by changing Grafana datasource schema
- Keep old schema for instant rollback

**Cutover Process**:
```bash
# 1. Migrate to new schema
python3 migrate_sqlite_to_postgres_enhanced.py \
  --source db_clean.db \
  --mode blue-green

# Output:
# new_schema: servicedesk_v20251019_143022
# cutover_command: UPDATE datasource SET schema='servicedesk_v20251019_143022'
# rollback_command: UPDATE datasource SET schema='servicedesk_v20251019_120000'

# 2. Validate new schema
docker exec servicedesk-postgres psql ... -c "SELECT COUNT(*) FROM servicedesk_v20251019_143022.tickets;"

# 3. Cutover in Grafana (update datasource schema)

# 4. If issues: instant rollback (revert datasource schema)
```

---

### 10. Type Validation (Sample-Based)

**Rationale**: Schema labels lie. Validate actual data types.

**V2 Implementation**:
- Phase 1 profiler: Sample 5000 rows, detect actual types
- Confidence scoring: ≥95% threshold for type assignment
- Circuit breaker: Halt if type mismatch >10%

**Anti-Pattern**:
```python
# ❌ DON'T: Trust schema labels
schema = cursor.execute("PRAGMA table_info(tickets)").fetchall()
# TIMESTAMP label doesn't mean TIMESTAMP data!
```

**Best Practice**:
```python
# ✅ DO: Sample-based type detection
sample_values = cursor.execute("SELECT created_time FROM tickets LIMIT 5000").fetchall()

for value in sample_values:
    detected_type = detect_type(value)  # Actual type inference

confidence = count(detected_type == 'timestamp') / total
if confidence >= 0.95:
    type_assignment = 'timestamp'
```

---

### 11. Date Format Standardization

**Rationale**: PostgreSQL requires consistent YYYY-MM-DD HH:MM:SS format.

**V2 Implementation**:
- Regex-based detection: DD/MM/YYYY, D/M/YYYY patterns
- Conversion to ISO format with zero-padding
- Edge case handling: 31/01, 29/02 (leap year)

**Pattern**:
```python
import re

# Detect DD/MM/YYYY H:MM pattern
match = re.match(r'(\d{1,2})/(\d{1,2})/(\d{4})\s+(\d{1,2}):(\d{2})', date_str)
if match:
    day, month, year, hour, minute = match.groups()

    # Convert to ISO format
    standardized = f"{year}-{int(month):02d}-{int(day):02d} {int(hour):02d}:{minute}:00"
```

---

### 12. Empty String vs NULL Handling

**Rationale**: PostgreSQL distinguishes empty strings from NULL. SQLite often uses '' instead of NULL.

**V2 Implementation**:
- Phase 2 cleaner: Convert '' → NULL for date/timestamp columns
- Configurable column list
- Preserves actual NULL values (no double-conversion)

**Pattern**:
```sql
-- Convert empty strings to NULL
UPDATE tickets
SET created_time = NULL
WHERE created_time = '';

-- Verify
SELECT COUNT(CASE WHEN created_time IS NULL THEN 1 END) as nulls,
       COUNT(CASE WHEN created_time = '' THEN 1 END) as empty_strings
FROM tickets;
```

---

### 13. Health Monitoring

**Rationale**: Prevent resource exhaustion during long-running operations.

**V2 Implementation**:
- Disk space check: Every 10K rows, halt if <1GB
- Memory check: Every 10K rows, halt if >90%
- PostgreSQL connection: Periodic ping

**Pattern**:
```python
for offset in range(0, total_rows, 10000):
    # Health check every 10K rows
    disk = check_disk_space_health(threshold_gb=1.0)
    if not disk['healthy']:
        raise HealthCheckError("Disk space critically low")

    memory = check_memory_health(threshold_percent=90.0)
    if not memory['healthy']:
        raise HealthCheckError("Memory usage critically high")

    # Process batch
    process_batch(offset, 10000)
```

---

### 14. Progress Tracking

**Rationale**: Long operations need visibility for operators.

**V2 Implementation**:
- ProgressTracker: Real-time rows/second rate
- ETA calculation: Based on current rate
- Overhead: <1ms per update (negligible)

**Usage**:
```python
tracker = ProgressTracker(total_rows=260000)

for batch in batches:
    process(batch)
    tracker.update(rows_processed=current_count)
    # Emits: "Processed 50000/260000 (19.2%) - ETA: 3m 42s - Rate: 2314 rows/sec"
```

---

### 15. Rollback Testing

**Rationale**: Untested rollback procedures fail when needed most.

**V2 Practice**:
- Test rollback in non-production quarterly
- Document rollback time (RTO)
- Verify data integrity post-rollback

**Test Procedure**:
```bash
# 1. Perform test migration
python3 migrate_sqlite_to_postgres_enhanced.py --source test.db --mode blue-green

# 2. Simulate failure (manual trigger)

# 3. Execute rollback
docker exec servicedesk-postgres psql ... -c "DROP SCHEMA servicedesk_v20251019_143022 CASCADE;"

# 4. Verify old schema intact
docker exec servicedesk-postgres psql ... -c "SELECT COUNT(*) FROM servicedesk_v20251019_120000.tickets;"

# 5. Document rollback time
echo "Rollback completed in 45 seconds" >> rollback_tests.log
```

---

## Anti-Patterns to Avoid

### ❌ Trusting Schema Labels
SQLite `TIMESTAMP` columns often contain TEXT. Always sample-validate.

### ❌ In-Place Modifications
Never `UPDATE` source database directly. Clean to new file.

### ❌ Ignoring Quality Gates
Bypassing quality checks leads to production data issues.

### ❌ Missing Backups
"It's just a test migration" - famous last words.

### ❌ Hardcoded Thresholds
Make quality/circuit breaker thresholds configurable.

### ❌ Silent Failures
Log everything. Metrics beat intuition.

---

## Checklist for New Deployments

- [ ] Pre-flight checks passed
- [ ] Source database backed up (MD5 verified)
- [ ] PostgreSQL schema backed up (pg_dump)
- [ ] Profiler run (circuit breaker status checked)
- [ ] Quality score ≥80
- [ ] Canary deployment validated (if using)
- [ ] Row counts match (SQLite == PostgreSQL)
- [ ] Column types correct (TIMESTAMP not TEXT)
- [ ] Sample queries execute without error
- [ ] All 4 dashboards load correctly
- [ ] Rollback procedure tested (non-production)
- [ ] Deployment documented in log

---

## Performance Optimization Tips

1. **Batch Processing**: Process in 10K row batches (memory-efficient)
2. **Sampling**: Profile 5K rows, not entire dataset (99% accuracy, 50x faster)
3. **Indexes**: Create indexes on frequently queried columns post-migration
4. **Partitioning**: Partition large tables by date for faster queries
5. **Connection Pooling**: Reuse PostgreSQL connections (avoid connection overhead)

---

**Document Status**: Production Ready
**Last Updated**: 2025-10-19
**Review Cycle**: Quarterly
