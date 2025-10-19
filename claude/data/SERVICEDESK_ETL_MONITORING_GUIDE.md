# ServiceDesk ETL V2 - Monitoring Guide

**Version**: 2.0
**Date**: 2025-10-19
**Status**: Production Ready

---

## Overview

This guide covers monitoring the ServiceDesk ETL V2 pipeline for reliability, performance, and data quality.

---

## Key Metrics

### Pipeline Performance

**Metric**: `etl_profiler_duration_seconds`
- **Description**: Time to profile database
- **Target**: <300s (5 min) for 260K rows
- **Alert**: >600s (10 min)
- **Source**: Phase 1 profiler

**Metric**: `etl_cleaner_duration_seconds`
- **Description**: Time to clean database
- **Target**: <900s (15 min) for 260K rows
- **Alert**: >1800s (30 min)
- **Source**: Phase 2 cleaner

**Metric**: `etl_migration_duration_seconds`
- **Description**: Time to migrate to PostgreSQL
- **Target**: <300s (5 min) for 260K rows
- **Alert**: >600s (10 min)
- **Source**: Phase 3 migration

### Data Quality

**Metric**: `etl_quality_score`
- **Description**: Overall data quality (0-100)
- **Target**: ≥80
- **Alert**: <70 (WARNING), <50 (CRITICAL)
- **Source**: Phase 2 quality scorer

**Metric**: `etl_dates_standardized_total`
- **Description**: Count of dates converted DD/MM/YYYY → YYYY-MM-DD
- **Target**: Trending down (fewer issues over time)
- **Source**: Phase 2 cleaner

**Metric**: `etl_empty_strings_converted_total`
- **Description**: Count of empty strings → NULL
- **Target**: Trending down
- **Source**: Phase 2 cleaner

### Error Tracking

**Metric**: `etl_errors_total`
- **Description**: Total errors by gate (profiler, cleaner, migration)
- **Target**: 0
- **Alert**: >0 (immediate investigation)
- **Source**: All phases

**Metric**: `etl_circuit_breaker_halts_total`
- **Description**: Count of circuit breaker triggers
- **Target**: 0
- **Alert**: >0 (data quality issue)
- **Source**: Phase 1 profiler

### Health Checks

**Metric**: `etl_disk_space_gb`
- **Description**: Available disk space
- **Target**: ≥2GB
- **Alert**: <1GB (CRITICAL)
- **Source**: Phase 0 observability

**Metric**: `etl_memory_usage_percent`
- **Description**: Memory utilization
- **Target**: <80%
- **Alert**: >90% (CRITICAL)
- **Source**: Phase 0 observability

---

## Alert Configuration

### Critical Alerts (PagerDuty)

```yaml
# Migration failed
alert: ETL_Migration_Failed
expr: etl_errors_total{gate="migration"} > 0
severity: critical
action: Execute rollback procedure immediately
oncall: SRE

# Quality gate blocked migration
alert: ETL_Quality_Gate_Failed
expr: etl_quality_score < 50
severity: critical
action: Investigate data source quality
oncall: Data Engineering

# Disk space critical
alert: ETL_Disk_Space_Critical
expr: etl_disk_space_gb < 1.0
severity: critical
action: Free disk space, halt migrations
oncall: SRE
```

### Warning Alerts (Slack)

```yaml
# Slow migration
alert: ETL_Migration_Slow
expr: etl_migration_duration_seconds > 600
severity: warning
action: Investigate performance degradation
channel: #servicedesk-etl-alerts

# Quality score low
alert: ETL_Quality_Score_Low
expr: etl_quality_score < 70
severity: warning
action: Review data source, consider manual cleanup
channel: #servicedesk-etl-alerts

# Data freshness
alert: ETL_Data_Stale
expr: (time() - etl_last_import_timestamp) > 172800  # 48 hours
severity: warning
action: Check import schedule
channel: #servicedesk-etl-alerts
```

---

## Grafana Dashboard Setup

### ETL Pipeline Dashboard

**Panels**:
1. **Pipeline Duration** (Time Series)
   - Profiler, Cleaner, Migration durations stacked
   - SLA line at 25 minutes

2. **Quality Score Trend** (Time Series)
   - Quality score over time
   - Threshold lines at 80 (target) and 50 (critical)

3. **Error Rate** (Single Stat)
   - Total errors in last 24 hours
   - Red if >0

4. **Data Quality Improvements** (Bar Chart)
   - Dates standardized
   - Empty strings converted
   - Shows cleaning effectiveness

5. **Resource Usage** (Gauge)
   - Disk space available
   - Memory usage
   - Thresholds: green <80%, yellow 80-90%, red >90%

**JSON Import**:
```json
{
  "dashboard": {
    "title": "ServiceDesk ETL V2 Pipeline",
    "panels": [
      {
        "title": "Pipeline Duration",
        "targets": [
          {
            "expr": "etl_profiler_duration_seconds",
            "legendFormat": "Profiler"
          },
          {
            "expr": "etl_cleaner_duration_seconds",
            "legendFormat": "Cleaner"
          },
          {
            "expr": "etl_migration_duration_seconds",
            "legendFormat": "Migration"
          }
        ]
      }
    ]
  }
}
```

---

## Log Aggregation

### Structured Logging Format

All ETL components emit JSON logs:

```json
{
  "timestamp": "2025-10-19T14:30:22.123456",
  "level": "INFO",
  "gate": "Gate2_Cleaner",
  "message": "Date standardization complete",
  "total_converted": 15,
  "duration_seconds": 3.2
}
```

### Log Query Examples

**Find all errors in last hour**:
```bash
grep '"level":"ERROR"' /var/log/servicedesk-etl/*.log | \
  jq -r 'select(.timestamp > (now - 3600))'
```

**Calculate average cleaning duration**:
```bash
grep 'Cleaning complete' /var/log/servicedesk-etl/cleaner.log | \
  jq -r '.duration_seconds' | \
  awk '{sum+=$1; count++} END {print sum/count}'
```

**Find circuit breaker triggers**:
```bash
grep 'circuit_breaker' /var/log/servicedesk-etl/profiler.log | \
  jq 'select(.circuit_breaker.should_halt == true)'
```

---

## Performance Baselines

### Established Baselines (260K rows)

| Phase | Metric | Baseline | P95 | P99 |
|-------|--------|----------|-----|-----|
| Profiler | Duration | 180s | 240s | 300s |
| Cleaner | Duration | 600s | 750s | 900s |
| Migration | Duration | 120s | 180s | 240s |
| Full Pipeline | Duration | 900s | 1200s | 1500s |

### Scaling Estimates

**520K rows (2x volume)**:
- Profiler: ~360s (2x)
- Cleaner: ~1200s (2x)
- Migration: ~240s (2x)
- Full Pipeline: ~1800s (2x)

**Expected**: Linear scaling confirmed by Phase 5 load tests

---

## Health Check Procedures

### Automated Health Checks

**Pre-flight (before each migration)**:
```bash
python3 claude/tools/sre/servicedesk_etl_preflight.py --source db.db

# Checks:
# - Disk space ≥2x DB size
# - PostgreSQL connectivity
# - Backup tools available
# - Memory ≥4GB recommended
# - Dependencies installed
```

**During migration (every 10K rows)**:
```python
# Automatic checks in cleaner/migration
check_disk_space_health(threshold_gb=1.0)
check_memory_health(threshold_percent=90.0)
```

### Manual Health Checks (Weekly)

```bash
# 1. Check PostgreSQL table sizes
docker exec servicedesk-postgres psql -U servicedesk_user -d servicedesk -c \
  "SELECT pg_size_pretty(pg_total_relation_size('servicedesk.tickets'));"

# 2. Verify backup retention
ls -lht /backups/*.db.* | head -10

# 3. Check log rotation
du -sh /var/log/servicedesk-etl/

# 4. Test rollback procedure (non-production)
# See operational runbook for rollback test procedure
```

---

## Troubleshooting Metrics

### High Migration Duration

**Investigate**:
1. Check PostgreSQL query performance: `EXPLAIN ANALYZE`
2. Review disk I/O: `iostat -x 5`
3. Check network latency (if PostgreSQL remote)
4. Examine table indexes

### Low Quality Score

**Investigate**:
1. Run profiler to identify specific issues
2. Compare with previous imports (is trend declining?)
3. Check vendor data source quality
4. Review circuit breaker thresholds (may need adjustment)

### Memory Alerts

**Investigate**:
1. Check Python process memory: `ps aux | grep python`
2. Review batch size settings (may need to reduce)
3. Check for memory leaks (long-running processes)
4. Verify database connection pooling

---

## Best Practices

1. **Monitor trends, not just absolutes**: Quality score declining is more concerning than a single low score
2. **Alert on rate of change**: Sudden duration increases indicate issues
3. **Correlate metrics**: High error rate + low quality score = data source problem
4. **Regular baseline updates**: Re-establish baselines after infrastructure changes
5. **Test alerting**: Simulate failures to verify alert delivery

---

**Document Status**: Production Ready
**Last Updated**: 2025-10-19
**Review Cycle**: Monthly
