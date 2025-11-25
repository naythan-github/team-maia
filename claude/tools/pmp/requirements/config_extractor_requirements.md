# PMP Configuration Extractor - Requirements Specification v1.0

## Executive Summary
Extract and analyze ManageEngine Patch Manager Plus configuration data using confirmed OAuth API endpoints. Focus on time-series trend analysis and compliance monitoring through historical snapshots of summary-level metrics.

## 1. API Data Sources (Confirmed Working)

### 1.1 Primary Endpoint: `/api/1.4/patch/summary`
**Status**: ✅ Confirmed working with OAuth scope `PatchManagerPlusCloud.PatchMgmt.READ`
**Rate Limit**: 3000 requests per 5 minutes (50 req/min conservative)
**Response Time**: ~500-800ms average

**Available Data Points** (27 total):

#### Patch Configuration Metrics
- `installed_patches` - Total patches successfully installed
- `applicable_patches` - Total patches available for environment
- `new_patches` - Recently published patches
- `missing_patches` - Patches not yet installed

#### Severity Distribution
- `critical_count` - Critical severity missing patches
- `important_count` - High severity missing patches
- `moderate_count` - Medium severity missing patches
- `low_count` - Low severity missing patches
- `unrated_count` - Unrated/unknown severity patches
- `total_count` - Total missing patches (validation field)

#### System Health Status
- `total_systems` - Total managed systems
- `healthy_systems` - Systems with no critical/high missing patches
- `moderately_vulnerable_systems` - Systems with 1-5 critical/high missing
- `highly_vulnerable_systems` - Systems with 6+ critical/high missing
- `health_unknown_systems` - Systems with stale scan data

#### Scan Configuration & Status
- `scanned_systems` - Successfully scanned systems
- `unscanned_system_count` - Never scanned or scan pending
- `scan_success_count` - Recent scan successes
- `scan_failure_count` - Recent scan failures

#### Vulnerability Database Configuration
- `last_db_update_status` - Success/Failed status
- `last_db_update_time` - Unix timestamp (milliseconds)
- `is_auto_db_update_disabled` - Auto-update configuration
- `db_update_in_progress` - Current update status

#### Automated Patch Deployment (APD)
- `number_of_apd_tasks` - Active automated deployment tasks

### 1.2 Secondary Endpoint: `/api/1.4/patch/dbupdatestatus`
**Status**: ✅ Confirmed working
**Purpose**: Detailed vulnerability database update history
**Data**: Update timestamps, status, version info

### 1.3 Unavailable Endpoints (OAuth Scope Limitations)
- `/api/1.4/patch/allpatches` - Patch catalog ❌
- `/api/1.4/patch/scandetails` - Per-system details ❌
- `/api/1.4/patch/systemreport` - Individual system patches ❌

**Implication**: System focuses on **aggregate trend analysis** rather than per-system/per-patch details.

---

## 2. Data Storage Architecture

### 2.1 Primary Storage: SQLite Database
**Location**: `~/.maia/databases/intelligence/pmp_config.db`
**Purpose**: Historical snapshot storage for trend analysis
**Size Estimate**: ~2-5 MB per year (daily snapshots)

**Schema Design** (5 tables):

```sql
CREATE TABLE snapshots (
    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    api_version TEXT DEFAULT '1.4',
    extraction_duration_ms INTEGER,
    status TEXT CHECK(status IN ('success', 'partial', 'failed'))
);

CREATE TABLE patch_metrics (
    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id INTEGER NOT NULL,
    installed_patches INTEGER,
    applicable_patches INTEGER,
    new_patches INTEGER,
    missing_patches INTEGER,
    FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id)
);

CREATE TABLE severity_metrics (
    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id INTEGER NOT NULL,
    critical_count INTEGER,
    important_count INTEGER,
    moderate_count INTEGER,
    low_count INTEGER,
    unrated_count INTEGER,
    FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id)
);

CREATE TABLE system_health_metrics (
    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id INTEGER NOT NULL,
    total_systems INTEGER,
    healthy_systems INTEGER,
    moderately_vulnerable_systems INTEGER,
    highly_vulnerable_systems INTEGER,
    health_unknown_systems INTEGER,
    scanned_systems INTEGER,
    unscanned_system_count INTEGER,
    scan_success_count INTEGER,
    scan_failure_count INTEGER,
    FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id)
);

CREATE TABLE compliance_checks (
    check_id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id INTEGER NOT NULL,
    check_name TEXT NOT NULL,
    check_category TEXT, -- 'essential_eight', 'cis', 'custom'
    passed BOOLEAN,
    severity TEXT, -- 'critical', 'high', 'medium', 'low'
    details TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id)
);
```

**Indexes for Performance**:
```sql
CREATE INDEX idx_snapshot_timestamp ON snapshots(timestamp);
CREATE INDEX idx_patch_metrics_snapshot ON patch_metrics(snapshot_id);
CREATE INDEX idx_severity_metrics_snapshot ON severity_metrics(snapshot_id);
CREATE INDEX idx_system_health_snapshot ON system_health_metrics(snapshot_id);
CREATE INDEX idx_compliance_snapshot ON compliance_checks(snapshot_id);
CREATE INDEX idx_compliance_category ON compliance_checks(check_category, passed);
```

### 2.2 Secondary Storage: Excel Reports (On-Demand)
**Location**: `~/work_projects/pmp_reports/YYYY-MM-DD_report_name.xlsx`
**Purpose**: Business-friendly reports for audits, management, compliance
**Refresh Strategy**: Generated from SQLite on-demand (never edited directly)

**Report Types**:
1. **Compliance Dashboard** - 30/90-day compliance trends with charts
2. **Executive Summary** - High-level KPIs and risk scores
3. **Trend Analysis** - Month-over-month metrics with sparklines
4. **Vulnerability Report** - Critical/high patch gaps with aging analysis

---

## 3. Data Collection Requirements

### 3.1 Extraction Schedule
- **Frequency**: Daily at 2 AM local time (off-peak)
- **Retry Policy**: 3 attempts with exponential backoff (1min, 5min, 15min)
- **Timeout**: 30 seconds per API call
- **Rate Limiting**: Maximum 10 requests per minute (well below 50/min limit)

### 3.2 Error Handling
| Error Code | Condition | Response |
|-----------|-----------|----------|
| 401 | Token expired | Refresh OAuth token, retry once |
| 403 | Scope insufficient | Log error, alert user, skip endpoint |
| 429 | Rate limit exceeded | Respect Retry-After header, exponential backoff |
| 500/502/503 | Server error | Retry 3 times with 5-second delays |
| Timeout | API unresponsive | Retry 2 times, mark snapshot as 'partial' |

### 3.3 Data Validation
- **Schema Validation**: Verify all expected fields present before insert
- **Value Ranges**: total_systems > 0, percentages 0-100, counts >= 0
- **Consistency Checks**: `missing_patches == sum(severity_counts)`
- **Timestamp Validation**: Ensure snapshot timestamps are monotonically increasing

---

## 4. Compliance Analysis Rules

### 4.1 Essential Eight Alignment
**Maturity Level 2/3 Requirements** (Patch Applications):

| Rule | Threshold | Severity | Check |
|------|-----------|----------|-------|
| Critical patches within 48h | `critical_count <= 5` | CRITICAL | Essential Eight L2/3 |
| Important patches within 30 days | `important_count <= 50` | HIGH | Essential Eight L2/3 |
| System vulnerability rate | `highly_vulnerable_systems / total_systems <= 0.05` (5%) | HIGH | Essential Eight L2 |
| Scan coverage | `scanned_systems / total_systems >= 0.95` (95%) | MEDIUM | Essential Eight L1 |
| DB update freshness | `last_db_update_time < 7 days ago` | MEDIUM | Essential Eight L1 |

### 4.2 CIS Controls Alignment
| Control | Rule | Threshold |
|---------|------|-----------|
| CIS 7.1 | Vulnerability scanning deployed | `scanned_systems >= 95%` |
| CIS 7.2 | Critical patches remediated | `critical_count == 0` (30 days) |
| CIS 7.3 | Automated patching enabled | `number_of_apd_tasks > 0` |

### 4.3 Custom MSP Rules
- **Healthy System Ratio**: `healthy_systems / total_systems >= 0.60` (60%)
- **Scan Success Rate**: `scan_success_count / scanned_systems >= 0.98` (98%)
- **Unscanned System Alert**: `unscanned_system_count <= 50` (absolute count)

---

## 5. Excel Report Specifications

### 5.1 Compliance Dashboard (Primary Report)
**Worksheets** (5 total):
1. **Executive Summary** - KPIs, risk score, compliance status
2. **Trend Charts** - 90-day sparklines for critical metrics
3. **Compliance Checks** - Pass/fail for Essential Eight, CIS, custom rules
4. **Severity Analysis** - Pie chart + table of missing patch severity
5. **Recommendations** - Auto-generated action items based on compliance gaps

**Features**:
- Conditional formatting (red/yellow/green for compliance status)
- Embedded charts (pie, line, bar)
- Data validation (protect formulas)
- Print-optimized layout (fits on letter/A4)

### 5.2 Trend Analysis Report
**Time Ranges**: 7-day, 30-day, 90-day comparisons
**Metrics**: All 27 data points with trend direction indicators (↑↓→)
**Visualizations**: Line charts for critical/high patch counts over time

---

## 6. Performance Requirements

### 6.1 Extraction Performance
- **Full snapshot extraction**: <5 seconds (single API call)
- **Database insert**: <100ms (prepared statements)
- **Compliance analysis**: <500ms (27 rules evaluation)
- **Total extraction cycle**: <10 seconds end-to-end

### 6.2 Report Generation Performance
- **Excel compliance dashboard**: <30 seconds (90 days data)
- **Trend analysis report**: <20 seconds (30 days data)
- **Maximum file size**: <10 MB (Excel compatibility)

### 6.3 Storage Performance
- **Database growth**: ~5 KB per snapshot (daily = 1.8 MB/year)
- **Retention policy**: 2 years active, 5 years compressed archive
- **Query performance**: <50ms for trend queries (30-90 day range)

---

## 7. Security Requirements

### 7.1 Credential Management
- ✅ OAuth tokens encrypted with Fernet (existing pmp_oauth_manager.py)
- ✅ macOS Keychain for client ID/secret (existing implementation)
- ✅ Token file permissions: 600 (owner read/write only)
- ⚠️ Database file permissions: 600 (add to implementation)

### 7.2 Data Protection
- **At Rest**: SQLite database file-level encryption (optional, future enhancement)
- **In Transit**: HTTPS for all API calls (enforced by OAuth manager)
- **Access Control**: Database read-only for non-admin users
- **Audit Trail**: All compliance check failures logged with timestamps

---

## 8. Observability Requirements

### 8.1 Structured Logging
```python
logger.info("snapshot_extracted", extra={
    "snapshot_id": 123,
    "duration_ms": 4200,
    "patch_count": 3566,
    "system_count": 3358,
    "compliance_failures": 2
})
```

### 8.2 Metrics to Track
- `pmp.extraction.duration_ms` - Extraction time
- `pmp.extraction.success_rate` - Percentage of successful extractions
- `pmp.compliance.pass_rate` - Percentage of passing compliance checks
- `pmp.api.rate_limit_hits` - Count of 429 errors
- `pmp.db.size_mb` - Database file size

### 8.3 Alerts
| Condition | Severity | Action |
|-----------|----------|--------|
| 3 consecutive extraction failures | CRITICAL | Email alert, Slack notification |
| Compliance pass rate < 70% | HIGH | Daily summary report |
| Critical patch count > 20 | HIGH | Immediate notification |
| Database size > 100 MB | MEDIUM | Archive old snapshots |

---

## 9. Testing Requirements

### 9.1 Unit Tests (TDD - Phase 3)
- ✅ OAuth token refresh handling
- ✅ API error code handling (401, 403, 429, 500)
- ✅ Data validation (schema, ranges, consistency)
- ✅ Database CRUD operations
- ✅ Compliance rule evaluation
- ✅ Excel report generation

### 9.2 Integration Tests
- ✅ Full extraction workflow (API → DB → Compliance → Excel)
- ✅ Historical trend queries (7/30/90 days)
- ✅ Concurrent extraction handling (lock file)
- ✅ Partial failure recovery (API timeout mid-extraction)

### 9.3 Performance Tests
- ✅ 1000 snapshots query performance (<100ms)
- ✅ Excel generation with 90 days data (<30s)
- ✅ Database growth validation (5 KB per snapshot)

---

## 10. Success Criteria

### 10.1 Functional Success
- ✅ Daily snapshots extracted without manual intervention
- ✅ All 27 data points captured and validated
- ✅ Compliance dashboard generated on-demand (<30s)
- ✅ 30/90-day trend analysis with actionable insights
- ✅ Zero credential exposure (macOS Keychain + encrypted tokens)

### 10.2 Business Success
- ✅ Compliance audits completed in <30 minutes (vs 4+ hours manual)
- ✅ Historical trend visibility (detect configuration drift)
- ✅ Executive-friendly reports (Excel dashboards)
- ✅ Proactive alerting for critical patch accumulation

### 10.3 Technical Success
- ✅ 99.5% extraction success rate (allowing for API maintenance windows)
- ✅ <1 GB database size after 5 years
- ✅ Zero unauthorized OAuth token access
- ✅ All tests passing (unit + integration)

---

## 11. Future Enhancements (Post-MVP)

### 11.1 Phase 2 Enhancements (If More API Endpoints Become Available)
- Per-system patch inventory (if `/api/1.4/patch/scandetails` fixed)
- Individual patch details (if `/api/1.4/patch/allpatches` fixed)
- Deployment history tracking (if `/api/1.4/patch/deployment` accessible)

### 11.2 Advanced Analytics
- Machine learning for anomaly detection (unusual patch counts)
- Predictive modeling (forecast critical patch accumulation)
- Automated remediation recommendations (AI-generated action plans)

### 11.3 Integration Enhancements
- ServiceNow ticket creation for compliance failures
- Slack/Teams notifications for critical thresholds
- Grafana dashboard integration (Prometheus metrics export)

---

## 12. Implementation Phases

### Phase 1: Requirements Discovery ✅ COMPLETE
- API endpoint testing
- Data structure analysis
- OAuth scope verification

### Phase 2: Requirements Documentation ⏳ IN PROGRESS
- Formal specification (this document)
- Database schema design
- Compliance rules definition

### Phase 3: Test Design
- TDD test cases (27 unit tests, 8 integration tests)
- Performance test scenarios
- SRE Principal Engineer review (error handling, observability)

### Phase 4: Database Schema Implementation
- SQLite schema creation
- Index optimization
- Migration scripts (for future schema changes)

### Phase 5: Config Extractor Implementation
- `pmp_config_extractor.py` (main extraction engine)
- OAuth integration (reuse existing pmp_oauth_manager.py)
- Error handling + retry logic
- Structured logging

### Phase 6: Excel Report Generator
- `pmp_report_generator.py` (Excel export engine)
- 4 report templates (compliance, executive, trend, vulnerability)
- Chart generation (openpyxl library)
- Conditional formatting

### Phase 7: Compliance Analyzer
- `pmp_compliance_analyzer.py` (rule evaluation engine)
- Essential Eight / CIS / custom rules
- Recommendation generator
- Alert thresholds

### Phase 8: Integration Testing
- End-to-end workflow validation
- Performance benchmarking
- Failure mode testing (API down, disk full, token expired)

### Phase 9: Documentation & Deployment
- Update SYSTEM_STATE.md (Phase 188)
- Update capability_index.md
- CLI usage documentation
- Cron job setup for daily automation

---

## Appendix A: API Response Sample

```json
{
  "message_type": "summary",
  "message_response": {
    "summary": {
      "patch_summary": {
        "installed_patches": 3566,
        "applicable_patches": 5301,
        "new_patches": 34362,
        "missing_patches": 1735
      },
      "missing_patch_severity_summary": {
        "critical_count": 139,
        "important_count": 452,
        "moderate_count": 549,
        "low_count": 60,
        "unrated_count": 534,
        "total_count": 1734
      },
      "system_summary": {
        "total_systems": 3358,
        "healthy_systems": 1721,
        "moderately_vulnerable_systems": 308,
        "highly_vulnerable_systems": 1300,
        "health_unknown_systems": 29
      },
      "patch_scan_summary": {
        "scanned_systems": 3320,
        "unscanned_system_count": 38,
        "scan_success_count": 3295,
        "scan_failure_count": 25
      },
      "vulnerability_db_summary": {
        "last_db_update_status": "Success",
        "last_db_update_time": 1764052565661,
        "is_auto_db_update_disabled": true,
        "db_update_in_progress": false
      },
      "apd_summary": {
        "number_of_apd_tasks": 70
      }
    }
  },
  "message_version": "1.4",
  "status": "success"
}
```

---

**Document Version**: 1.0
**Last Updated**: 2025-11-25
**Author**: Patch Manager Plus API Specialist Agent + SRE Principal Engineer Agent
**Status**: Ready for Phase 3 (Test Design)
