# ServiceDesk ETL V2 - Operational Runbook

**Version**: 2.0
**Date**: 2025-10-19
**Status**: Production Ready
**Owner**: SRE Team

---

## Table of Contents

1. [Overview](#overview)
2. [Deployment Checklist](#deployment-checklist)
3. [Common Operations](#common-operations)
4. [Troubleshooting Guide](#troubleshooting-guide)
5. [Rollback Procedures](#rollback-procedures)
6. [Monitoring & Alerts](#monitoring--alerts)
7. [Emergency Contacts](#emergency-contacts)

---

## Overview

### Purpose

This runbook provides step-by-step procedures for operating the ServiceDesk ETL V2 pipeline. It covers:
- Quarterly data imports (4x per year)
- Quality analysis runs
- Emergency rollbacks
- Common troubleshooting scenarios

### Pipeline Architecture

```
Gate 0: Prerequisites
  ├─ Pre-flight checks
  ├─ Backup creation
  └─ Health monitoring

Gate 1: Data Profiling
  ├─ Type detection
  ├─ Circuit breaker
  └─ Quality scoring

Gate 2: Data Cleaning
  ├─ Date standardization
  ├─ Empty string → NULL
  └─ Transaction safety

Gate 3: PostgreSQL Migration
  ├─ Quality gate
  ├─ Canary deployment
  ├─ Blue-green schema
  └─ Enhanced rollback
```

### Key Principles

1. **Never modify source data in-place** - Always clean to NEW file
2. **Always backup before migration** - Automated via Phase 0
3. **Quality gate must pass** - Minimum 80/100 score required
4. **Canary before full migration** - Test 10% sample first
5. **Monitor throughout** - Check logs, metrics, progress

---

## Deployment Checklist

### Pre-Deployment (30 minutes before)

**Environment Validation**:
```bash
# 1. Run pre-flight checks
python3 claude/tools/sre/servicedesk_etl_preflight.py \
  --source /path/to/servicedesk_tickets.db

# Expected: All checks PASS (disk ≥2GB, PostgreSQL connected, etc.)
```

**Backup Current State**:
```bash
# 2. Backup source database
python3 claude/tools/sre/servicedesk_etl_backup.py backup \
  --source /path/to/servicedesk_tickets.db \
  --output /backups/

# Expected: Backup file created with MD5 checksum
```

**PostgreSQL Preparation**:
```bash
# 3. Backup PostgreSQL schema
docker exec servicedesk-postgres pg_dump \
  -U servicedesk_user \
  -d servicedesk \
  -n servicedesk \
  -F c \
  -f /backups/servicedesk_schema_$(date +%Y%m%d_%H%M%S).backup

# Expected: Backup file created
```

**Health Check**:
```bash
# 4. Verify PostgreSQL connectivity
docker exec servicedesk-postgres psql \
  -U servicedesk_user \
  -d servicedesk \
  -c "SELECT version();"

# Expected: PostgreSQL version displayed
```

### During Deployment (25-30 minutes)

**Step 1: Data Profiling** (5 minutes)
```bash
python3 claude/tools/sre/servicedesk_etl_data_profiler.py \
  --source /path/to/servicedesk_tickets.db \
  --use-validator \
  --use-scorer

# Monitor output for:
# - Circuit breaker status (should_halt: false)
# - Type detection confidence (≥95%)
# - Date format issues detected
```

**Step 2: Data Cleaning** (15 minutes for 260K rows)
```bash
python3 claude/tools/sre/servicedesk_etl_data_cleaner_enhanced.py \
  --source /path/to/servicedesk_tickets.db \
  --output /path/to/servicedesk_tickets_clean.db \
  --min-quality 80

# Monitor output for:
# - Dates standardized count (should be >0 if issues exist)
# - Empty strings converted
# - Quality score improvement
# - Transaction committed successfully
```

**Step 3: PostgreSQL Migration** (5 minutes)
```bash
# Option A: Simple migration (fastest)
python3 claude/infrastructure/servicedesk-dashboard/migration/migrate_sqlite_to_postgres_enhanced.py \
  --source /path/to/servicedesk_tickets_clean.db \
  --mode simple \
  --min-quality 80

# Option B: Canary deployment (recommended for production)
python3 claude/infrastructure/servicedesk-dashboard/migration/migrate_sqlite_to_postgres_enhanced.py \
  --source /path/to/servicedesk_tickets_clean.db \
  --mode canary

# Option C: Blue-green deployment (zero-downtime)
python3 claude/infrastructure/servicedesk-dashboard/migration/migrate_sqlite_to_postgres_enhanced.py \
  --source /path/to/servicedesk_tickets_clean.db \
  --mode blue-green

# Monitor output for:
# - Quality gate passed
# - Canary validation success (if using canary mode)
# - Row count match
# - TIMESTAMP columns created
```

### Post-Deployment (5-10 minutes)

**Validation**:
```bash
# 1. Verify row counts match
sqlite3 /path/to/servicedesk_tickets_clean.db \
  "SELECT COUNT(*) FROM tickets;"

docker exec servicedesk-postgres psql \
  -U servicedesk_user \
  -d servicedesk \
  -c "SELECT COUNT(*) FROM servicedesk.tickets;"

# Expected: Counts should match

# 2. Verify TIMESTAMP columns (not TEXT)
docker exec servicedesk-postgres psql \
  -U servicedesk_user \
  -d servicedesk \
  -c "SELECT column_name, data_type FROM information_schema.columns WHERE table_schema='servicedesk' AND table_name='tickets' AND column_name LIKE '%time%' OR column_name LIKE '%date%';"

# Expected: data_type = 'timestamp without time zone'

# 3. Test sample queries
docker exec servicedesk-postgres psql \
  -U servicedesk_user \
  -d servicedesk \
  -c "SELECT COUNT(*) FROM servicedesk.tickets WHERE \"TKT-Created Time\" IS NOT NULL;"

# Expected: Query executes without error
```

**Dashboard Verification**:
```bash
# 4. Open Grafana and check dashboards
# - Executive Dashboard: http://localhost:3000/d/servicedesk-executive
# - Operations Dashboard: http://localhost:3000/d/servicedesk-operations
# - Quality Dashboard: http://localhost:3000/d/servicedesk-quality
# - Team Performance: http://localhost:3000/d/servicedesk-team-performance

# Expected: All panels load without errors
```

**Sign-Off**:
```bash
# 5. Document deployment
echo "Deployment completed at $(date)" >> /var/log/servicedesk-etl/deployments.log
echo "Source: /path/to/servicedesk_tickets.db" >> /var/log/servicedesk-etl/deployments.log
echo "Row count: $(docker exec servicedesk-postgres psql -U servicedesk_user -d servicedesk -t -c 'SELECT COUNT(*) FROM servicedesk.tickets;')" >> /var/log/servicedesk-etl/deployments.log
```

---

## Common Operations

### Quarterly Data Import

**Frequency**: 4 times per year (Jan, Apr, Jul, Oct)
**Duration**: ~30 minutes
**Prerequisites**: New servicedesk_tickets.db file from vendor

**Procedure**:
```bash
# 1. Place new database file
cp /path/to/new/servicedesk_tickets.db /data/servicedesk_tickets_Q4_2025.db

# 2. Run full pipeline
./claude/tools/sre/run_full_pipeline.sh \
  --source /data/servicedesk_tickets_Q4_2025.db \
  --mode canary \
  --min-quality 80

# 3. Verify dashboards updated
# 4. Archive old database
mv /data/servicedesk_tickets_Q3_2025.db /archive/
```

### Quality Analysis Run

**Frequency**: After each import or on-demand
**Duration**: 4-6 hours (for 100K comments)
**Purpose**: Generate quality scores for dashboards

**Procedure**:
```bash
# 1. Run complete quality analyzer
python3 claude/tools/sre/servicedesk_complete_quality_analyzer.py \
  --full \
  --similarity 0.95 \
  --batch-size 10

# 2. Validate quality data
sqlite3 /path/to/servicedesk_tickets.db << 'EOF'
SELECT COUNT(*) as analyzed,
       COUNT(DISTINCT professionalism_score) as unique_prof,
       ROUND(AVG(quality_score), 2) as avg_quality
FROM comment_quality;
EOF

# Expected: unique_prof > 1, avg_quality 2.5-3.5

# 3. Re-migrate quality data to PostgreSQL
docker exec servicedesk-postgres psql -U servicedesk_user -d servicedesk \
  -c "TRUNCATE TABLE servicedesk.comment_quality;"

python3 claude/infrastructure/servicedesk-dashboard/migration/migrate_sqlite_to_postgres_enhanced.py \
  --source /path/to/servicedesk_tickets.db \
  --mode simple
```

### Schema Update (Add New Column)

**Prerequisites**: Updated source database with new column

**Procedure**:
```bash
# 1. Profile new column
python3 claude/tools/sre/servicedesk_etl_data_profiler.py \
  --source /path/to/updated_db.db

# 2. Update migration script to include new column
# Edit: claude/infrastructure/servicedesk-dashboard/migration/migrate_sqlite_to_postgres_enhanced.py
# Add column to CREATE TABLE statement

# 3. Run migration in blue-green mode
python3 claude/infrastructure/servicedesk-dashboard/migration/migrate_sqlite_to_postgres_enhanced.py \
  --source /path/to/updated_db.db \
  --mode blue-green

# 4. Update Grafana datasource to point to new schema
# Manual step: Update datasource schema in Grafana UI

# 5. Verify dashboards with new column
# 6. Drop old schema after verification (24-48h)
```

### Manual Rollback

**When**: Migration failed or data quality issues detected post-deployment

**Procedure**: See [Rollback Procedures](#rollback-procedures) section below

---

## Troubleshooting Guide

### Issue 1: Pre-Flight Checks Fail

**Symptom**: `servicedesk_etl_preflight.py` exits with code 1 or 2

**Common Causes**:
1. Insufficient disk space (<2x database size)
2. PostgreSQL not running
3. Missing dependencies (psycopg2, psutil)

**Resolution**:
```bash
# Check disk space
df -h /

# If <2GB free, clean up:
rm -rf /tmp/old_backups/*
docker system prune -f

# Check PostgreSQL
docker ps | grep servicedesk-postgres

# If not running:
docker start servicedesk-postgres

# Check dependencies
pip3 list | grep -E "psycopg2|psutil"

# If missing:
pip3 install psycopg2-binary psutil
```

### Issue 2: Circuit Breaker Halts Migration

**Symptom**: Profiler output shows `should_halt: true`

**Causes**:
- Type mismatches >10% of columns
- Corrupt dates >20% of rows

**Resolution**:
```bash
# 1. Examine profiler report for specific issues
python3 claude/tools/sre/servicedesk_etl_data_profiler.py \
  --source /path/to/db.db \
  --json > profile.json

cat profile.json | jq '.issues'

# 2. Fix issues at source (vendor data)
# Contact vendor for corrected data export

# 3. OR manually clean specific columns
sqlite3 /path/to/db.db << 'EOF'
-- Fix specific type issue
UPDATE tickets SET "TKT-Priority" = 'Medium' WHERE "TKT-Priority" = '';
EOF

# 4. Re-run profiler
```

### Issue 3: Quality Score Below Threshold

**Symptom**: Migration fails with "Quality score X below threshold 80"

**Causes**:
- Uncleaned data (Phase 2 not run)
- Genuine data quality issues

**Resolution**:
```bash
# 1. Check if Phase 2 cleaner was run
ls -lh /path/to/*_clean.db

# If no clean database:
python3 claude/tools/sre/servicedesk_etl_data_cleaner_enhanced.py \
  --source /path/to/db.db \
  --output /path/to/db_clean.db

# 2. Check quality score components
sqlite3 /path/to/db.db << 'EOF'
SELECT
  COUNT(CASE WHEN "TKT-Created Time" = '' THEN 1 END) as empty_dates,
  COUNT(CASE WHEN "TKT-Priority" IS NULL THEN 1 END) as null_priority,
  COUNT(*) as total
FROM tickets;
EOF

# 3. If legitimate issues, lower threshold temporarily
python3 claude/infrastructure/servicedesk-dashboard/migration/migrate_sqlite_to_postgres_enhanced.py \
  --source /path/to/db_clean.db \
  --mode simple \
  --min-quality 70  # Lower threshold

# 4. Create ticket to investigate root cause
```

### Issue 4: Row Count Mismatch

**Symptom**: PostgreSQL has fewer rows than SQLite

**Causes**:
- Transaction rollback during migration
- Validation failure
- Network interruption

**Resolution**:
```bash
# 1. Check migration logs
tail -100 /var/log/servicedesk-etl/migration.log

# Look for ERROR or ROLLBACK messages

# 2. Re-run migration (idempotent)
python3 claude/infrastructure/servicedesk-dashboard/migration/migrate_sqlite_to_postgres_enhanced.py \
  --source /path/to/db_clean.db \
  --mode simple

# 3. Verify row counts match
sqlite3 /path/to/db_clean.db "SELECT COUNT(*) FROM tickets;" && \
docker exec servicedesk-postgres psql -U servicedesk_user -d servicedesk -t -c "SELECT COUNT(*) FROM servicedesk.tickets;"

# 4. If still mismatched, check for data type issues
```

### Issue 5: Dashboard Shows No Data

**Symptom**: Grafana panels display "No data"

**Causes**:
1. Migration didn't complete
2. Wrong schema selected in datasource
3. Table permissions issue

**Resolution**:
```bash
# 1. Verify data in PostgreSQL
docker exec servicedesk-postgres psql -U servicedesk_user -d servicedesk -c \
  "SELECT COUNT(*) FROM servicedesk.tickets;"

# If 0: Re-run migration

# 2. Check Grafana datasource schema
# UI: Configuration → Data Sources → servicedesk-postgres
# Verify "Schema" field = "servicedesk"

# 3. Test datasource connection
# UI: Data Sources → servicedesk-postgres → "Save & test"
# Expected: "Database Connection OK"

# 4. Check table permissions
docker exec servicedesk-postgres psql -U servicedesk_user -d servicedesk -c \
  "SELECT grantee, privilege_type FROM information_schema.table_privileges WHERE table_name='tickets';"

# Expected: servicedesk_user has SELECT privilege
```

---

## Rollback Procedures

### Scenario 1: Migration Failed (Automatic Rollback)

**Situation**: Migration script errored during execution

**Status**: Automatic rollback already executed by script

**Verification**:
```bash
# Check that source database unchanged
md5sum /path/to/original.db /path/to/original.db.backup

# Expected: MD5 hashes match

# Check PostgreSQL state
docker exec servicedesk-postgres psql -U servicedesk_user -d servicedesk -c \
  "SELECT COUNT(*) FROM servicedesk.tickets;"

# Expected: Previous data intact OR table empty (depending on migration mode)
```

### Scenario 2: Post-Migration Data Quality Issues

**Situation**: Migration completed but discovered data issues in dashboards

**Action**: Manual rollback to previous backup

**Procedure**:
```bash
# 1. Identify backup to restore
ls -lht /backups/servicedesk_schema_*.backup | head -5

# Choose backup from before migration

# 2. Drop current schema
docker exec servicedesk-postgres psql -U servicedesk_user -d servicedesk -c \
  "DROP SCHEMA servicedesk CASCADE;"

# 3. Restore from backup
docker exec servicedesk-postgres pg_restore \
  -U servicedesk_user \
  -d servicedesk \
  -c \
  /backups/servicedesk_schema_YYYYMMDD_HHMMSS.backup

# 4. Verify restoration
docker exec servicedesk-postgres psql -U servicedesk_user -d servicedesk -c \
  "SELECT COUNT(*) FROM servicedesk.tickets;"

# 5. Test dashboards
# Open Grafana and verify panels load correctly

# 6. Document rollback
echo "Rollback performed at $(date) - Restored from backup YYYYMMDD_HHMMSS" >> \
  /var/log/servicedesk-etl/rollbacks.log
```

### Scenario 3: Blue-Green Rollback (Instant)

**Situation**: New schema deployed via blue-green, need to rollback

**Action**: Switch datasource back to old schema

**Procedure**:
```bash
# 1. Identify old schema
docker exec servicedesk-postgres psql -U servicedesk_user -d servicedesk -c \
  "SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'servicedesk%';"

# Example output:
# servicedesk_v20251019_120000 (old)
# servicedesk_v20251019_143000 (new - current)

# 2. Update Grafana datasource to point to old schema
# UI: Configuration → Data Sources → servicedesk-postgres
# Change "Schema" field from "servicedesk_v20251019_143000" to "servicedesk_v20251019_120000"
# Click "Save & test"

# 3. Refresh dashboards
# Dashboards now show data from old schema

# 4. Drop new schema after verification
docker exec servicedesk-postgres psql -U servicedesk_user -d servicedesk -c \
  "DROP SCHEMA servicedesk_v20251019_143000 CASCADE;"
```

### Emergency Rollback Checklist

- [ ] Identify rollback point (which backup/schema)
- [ ] Notify stakeholders (dashboards will be unavailable briefly)
- [ ] Execute rollback procedure
- [ ] Verify data restoration (row counts, sample queries)
- [ ] Test all 4 dashboards
- [ ] Document rollback reason and resolution
- [ ] Create post-mortem ticket

---

## Monitoring & Alerts

### Key Metrics to Monitor

**ETL Pipeline Health**:
- Migration duration (SLA: <25 minutes for 260K rows)
- Quality score (threshold: ≥80)
- Error rate (target: <1% of operations)
- Data freshness (hours since last update)

**Dashboard Performance**:
- Query execution time (target: <5 seconds per panel)
- Panel load errors (target: 0 errors)
- Data completeness (target: >95% non-NULL values)

### Alert Thresholds

| Alert | Severity | Threshold | Action |
|-------|----------|-----------|--------|
| Migration Duration >30min | WARNING | >30 min | Investigate performance |
| Migration Failed | CRITICAL | Any failure | Emergency rollback |
| Quality Score <70 | WARNING | <70 | Review data source |
| Quality Score <50 | CRITICAL | <50 | Block migration |
| Data Freshness >48h | WARNING | >48 hours | Check import schedule |
| Dashboard Query Error | WARNING | >5 errors/hour | Check PostgreSQL |
| Disk Space <1GB | CRITICAL | <1 GB | Free space immediately |

### Log Locations

```bash
# ETL pipeline logs (JSON format)
/var/log/servicedesk-etl/profiler.log
/var/log/servicedesk-etl/cleaner.log
/var/log/servicedesk-etl/migration.log

# PostgreSQL logs
docker logs servicedesk-postgres

# Grafana logs
docker logs servicedesk-grafana

# Metrics (Prometheus format - if configured)
/var/log/servicedesk-etl/metrics.prom
```

### Health Check Commands

```bash
# Check pipeline components available
ls -lh claude/tools/sre/servicedesk_etl_*.py

# Check PostgreSQL responsive
docker exec servicedesk-postgres psql -U servicedesk_user -d servicedesk -c "SELECT 1;"

# Check data freshness
docker exec servicedesk-postgres psql -U servicedesk_user -d servicedesk -c \
  "SELECT EXTRACT(EPOCH FROM (NOW() - MAX(\"TKT-Created Time\"))) / 3600 FROM servicedesk.tickets;"

# Check disk space
df -h / | grep -v tmpfs
```

---

## Emergency Contacts

### Escalation Path

**Level 1: On-Call SRE**
- Slack: #servicedesk-etl-oncall
- PagerDuty: ServiceDesk ETL
- Response Time: 15 minutes

**Level 2: Data Engineering Team Lead**
- Email: data-eng-lead@company.com
- Phone: (555) 123-4567
- Response Time: 30 minutes

**Level 3: Infrastructure Manager**
- Email: infra-manager@company.com
- Phone: (555) 987-6543
- Response Time: 1 hour

### Support Resources

- **Runbook**: This document
- **Architecture Docs**: `/Users/YOUR_USERNAME/git/maia/claude/data/SERVICEDESK_ETL_ENHANCEMENT_PROJECT_V2_SRE_HARDENED.md`
- **Monitoring Guide**: `/Users/YOUR_USERNAME/git/maia/claude/data/SERVICEDESK_ETL_MONITORING_GUIDE.md`
- **Best Practices**: `/Users/YOUR_USERNAME/git/maia/claude/data/SERVICEDESK_ETL_BEST_PRACTICES.md`

---

## Appendix

### Quick Reference Commands

```bash
# Full pipeline (copy-paste ready)
python3 claude/tools/sre/servicedesk_etl_preflight.py --source db.db && \
python3 claude/tools/sre/servicedesk_etl_data_profiler.py --source db.db && \
python3 claude/tools/sre/servicedesk_etl_data_cleaner_enhanced.py --source db.db --output db_clean.db && \
python3 claude/infrastructure/servicedesk-dashboard/migration/migrate_sqlite_to_postgres_enhanced.py --source db_clean.db --mode canary

# Quick validation
docker exec servicedesk-postgres psql -U servicedesk_user -d servicedesk -c "SELECT COUNT(*), MAX(\"TKT-Created Time\") FROM servicedesk.tickets;"

# Emergency stop (if needed)
docker stop servicedesk-postgres servicedesk-grafana
```

### Change Log

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-10-19 | 2.0 | V2 SRE-hardened pipeline documentation | SRE Team |
| 2024-10-14 | 1.0 | Initial runbook for Phase 1 | Data Team |

---

**Document Status**: Production Ready
**Last Updated**: 2025-10-19
**Review Cycle**: Quarterly
**Next Review**: 2026-01-19
