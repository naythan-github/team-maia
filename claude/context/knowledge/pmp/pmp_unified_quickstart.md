# PMP Unified Intelligence System - Quickstart Guide

**Phase**: P4 - P7 (Unified Extraction & Cleanup)
**Sprint**: SPRINT-PMP-UNIFIED-001
**Version**: 1.0
**Date**: 2026-01-15

---

## Overview

The PMP Unified Intelligence System consolidates ManageEngine Patch Management Plus (PMP) data collection into a single, production-grade extractor with integrated compliance checking and metrics calculation.

### What Changed from Legacy System

**Before (Legacy)**:
- Separate extractors for each endpoint (config, vulnerabilities, deployments, system reports)
- Multiple databases with different schemas
- Manual orchestration and metric calculation
- No unified compliance evaluation

**After (Unified)**:
- Single `pmp_unified_extractor.py` orchestrates all API endpoints
- Unified schema with snapshot-based temporal tracking
- Integrated metrics calculation
- Essential Eight compliance checking built-in
- Backward-compatible with existing queries via `PMPIntelligenceService`

### Key Improvements

| Aspect | Legacy | Unified |
|--------|--------|---------|
| Extractors | 4-5 separate tools | 1 orchestrator |
| Schema Consistency | Manual alignment | Unified schema |
| Metrics | Manual calculation | Automatic via calculator |
| Compliance Checks | Manual review | Automated E8 assessment |
| Snapshot Tracking | Per-endpoint | Single snapshot_id |
| Error Handling | Limited | Partial success support |

---

## Quick Start

### 1. Understanding the Architecture

```
PMP Unified System
├── pmp_unified_extractor.py        # Single orchestrator for all endpoints
├── pmp_metrics_calculator.py        # Derives metrics from raw data
├── pmp_compliance_checker.py        # Essential Eight maturity assessment
├── pmp_intelligence_service.py      # Query interface (unchanged)
├── pmp_data_migrator.py            # Legacy data migration tool
└── pmp_unified_schema.sql          # Unified database schema
```

### 2. Database Location

All PMP intelligence data lives in:
```
~/.maia/databases/intelligence/pmp_intelligence.db
```

Legacy databases (archived):
```
~/.maia/archive/pmp_legacy/pmp_complete_intelligence.db
~/.maia/archive/pmp_legacy/pmp_patch_systems.db
```

Active source databases (still used):
```
~/.maia/databases/intelligence/pmp_config.db      # Configuration data
~/.maia/databases/intelligence/pmp_systemreports.db  # Deployment details
~/.maia/databases/intelligence/pmp_resilient.db     # Fresh inventory
```

### 3. Running the Unified Extractor

**Manual extraction (immediate)**:
```bash
cd $MAIA_ROOT
python3 claude/tools/pmp/pmp_unified_extractor.py
```

**Scheduled extraction** (daily at 18:00):
- Configured in: `~/.maia/config/collection_schedule.yaml`
- Triggered by: `CollectionScheduler` daemon
- No manual action required

**Output**:
```
INFO: unified_pmp_extractor_initialized
INFO: unified_extraction_started [snapshot_id: 1234567890]
INFO: extracted_from_summary_endpoint [count: 156 systems]
INFO: extracted_vulnerabilities [count: 4521 patches]
INFO: extracted_deployment_tasks [count: 892 tasks]
INFO: calculated_metrics [patch_metrics, severity_metrics, system_health_metrics]
INFO: generated_compliance_report [maturity_level: 2]
INFO: unified_extraction_completed [duration_ms: 3421, snapshot_id: 1234567890]
```

---

## Core Components

### 1. Unified Extractor

**File**: `claude/tools/pmp/pmp_unified_extractor.py`
**Class**: `UnifiedPMPExtractor`

Orchestrates extraction from three PMP API endpoints:

```python
from claude.tools.pmp.pmp_unified_extractor import UnifiedPMPExtractor

extractor = UnifiedPMPExtractor()
snapshot_id = extractor.extract()
# Returns: snapshot_id (integer timestamp)
# Output: Populated pmp_intelligence.db with all endpoint data
```

**Endpoints extracted**:
1. `/api/json/patching/summary` → Systems, patches, deployments
2. `/api/json/patching/vulnerabilities` → Vulnerability details
3. `/api/json/patching/deploymenttasks` → Deployment task status

**Features**:
- Single snapshot_id for all data (temporal consistency)
- Error handling with partial success (continues if one endpoint fails)
- Metrics auto-calculation on completion
- Structured logging for troubleshooting

### 2. Metrics Calculator

**File**: `claude/tools/pmp/pmp_metrics_calculator.py`
**Class**: `PMPMetricsCalculator`

Calculates derived metrics from raw extracted data:

```python
from claude.tools.pmp.pmp_metrics_calculator import PMPMetricsCalculator

calculator = PMPMetricsCalculator()
result = calculator.calculate_all(snapshot_id=1234567890)
```

**Calculated metrics**:
- **Patch Metrics**: Total, installed, missing, failed, applicable counts
- **Severity Metrics**: Critical/high/medium/low patch breakdown
- **System Health**: Healthy/vulnerable/unknown system counts
- **Deployment Health**: Success/failure rates by organization

**Output** (stored in `pmp_metrics` table):
```json
{
  "snapshot_id": 1234567890,
  "total_systems": 156,
  "total_patches": 4521,
  "patches_installed": 3892,
  "patches_missing": 629,
  "critical_patches_missing": 47,
  "healthy_systems": 128,
  "vulnerable_systems": 28,
  "avg_deployment_success_rate": 0.92
}
```

### 3. Compliance Checker

**File**: `claude/tools/pmp/pmp_compliance_checker.py`
**Class**: `PMPComplianceChecker`

Evaluates Essential Eight (E8) Patch Application maturity levels:

```python
from claude.tools.pmp.pmp_compliance_checker import PMPComplianceChecker

checker = PMPComplianceChecker()
report = checker.generate_report(snapshot_id=1234567890)
print(report)
```

**Maturity Levels**:

| Level | Definition | Compliance Thresholds |
|-------|-----------|----------------------|
| **0** | Below minimum | <80% overall compliance |
| **1** | Foundational | 80%+ compliance; all patches within 30 days |
| **2** | Intermediate | 90%+ compliance; critical patches within 48hrs; all patches within 14 days |
| **3** | Optimized | 95%+ compliance; critical patches within 24hrs; all patches within 48hrs |

**Output** (stored in `pmp_compliance_reports` table):
```json
{
  "snapshot_id": 1234567890,
  "assessment_timestamp": "2026-01-15T18:30:00",
  "maturity_level": 2,
  "critical_patch_compliance": 0.94,
  "high_patch_compliance": 0.91,
  "overall_compliance": 0.89,
  "compliance_gaps": [
    "3 critical patches >48hrs old (Windows Server 2019)",
    "142 patches >14 days overdue (non-critical)"
  ],
  "recommendations": [
    "Prioritize deployment for 3 critical patches on Windows Server 2019",
    "Schedule batch deployment for aging non-critical patches"
  ]
}
```

### 4. Intelligence Service (Query Interface)

**File**: `claude/tools/pmp/pmp_intelligence_service.py`
**Class**: `PMPIntelligenceService`

Unified query interface for all PMP data:

```python
from claude.tools.pmp.pmp_intelligence_service import PMPIntelligenceService

pmp = PMPIntelligenceService()

# Get systems by organization
systems = pmp.get_systems_by_organization("GS1%")

# Get failed patches
failures = pmp.get_failed_patches(org_pattern="GS1%")

# Get vulnerable systems
vulnerable = pmp.get_vulnerable_systems(severity=2)

# Raw SQL query
result = pmp.query_raw("SELECT COUNT(*) FROM all_systems")
```

**Why use this over raw SQL?**:
- Automatic database selection (uses unified schema)
- Normalized column names across databases
- Staleness checking and warnings
- Error handling and logging
- Supports both legacy and unified databases

---

## Database Schema Overview

### Core Tables (Unified Schema)

**snapshots** - Extraction metadata
```sql
id                      INTEGER PRIMARY KEY  -- Unique snapshot ID
extraction_timestamp    DATETIME             -- When data was extracted
extraction_duration_ms  INTEGER              -- Extraction time
endpoint_results        TEXT JSON            -- Per-endpoint stats
```

**systems** - System inventory
```sql
snapshot_id             INTEGER
resource_id            INTEGER PRIMARY KEY  -- PMP resource ID
resource_name          TEXT                 -- System hostname
organization           TEXT
os_name                TEXT
deployment_status      INTEGER              -- Health status code
last_scan_date         DATETIME
```

**patches** - Patch inventory
```sql
snapshot_id             INTEGER
patch_id               INTEGER PRIMARY KEY  -- PMP patch ID
patch_name             TEXT                 -- e.g., "KB5068864"
severity_id            INTEGER              -- 1=low, 2=medium, 3=high, 4=critical
release_date           DATETIME
applicable_count       INTEGER              -- Systems applicable
installed_count        INTEGER              -- Systems with patch installed
failed_count           INTEGER              -- Deployment failures
```

**patch_deployments** - Deployment task status
```sql
snapshot_id             INTEGER
task_id                INTEGER PRIMARY KEY  -- Deployment task ID
patch_id               INTEGER
resource_id            INTEGER
deployment_status      INTEGER              -- 206=failed, 207=pending, 209=success
last_update_date       DATETIME
failure_reason         TEXT
```

**pmp_metrics** - Calculated metrics
```sql
snapshot_id             INTEGER
metric_name             TEXT                 -- 'patch_metrics', 'compliance_metrics', etc.
metric_value           REAL
calculated_timestamp   DATETIME
```

**pmp_compliance_reports** - Compliance assessments
```sql
snapshot_id             INTEGER
maturity_level         INTEGER              -- 0-3
critical_patch_compliance     REAL
high_patch_compliance  REAL
overall_compliance     REAL
compliance_gaps        TEXT JSON            -- Array of gaps
recommendations        TEXT JSON            -- Array of recommendations
report_timestamp       DATETIME
```

---

## Common Use Cases

### 1. Check Data Freshness

**Before running queries, always check staleness**:

```python
from claude.tools.pmp.pmp_intelligence_service import PMPIntelligenceService

pmp = PMPIntelligenceService()
freshness = pmp.get_data_freshness_report()

for db, info in freshness.items():
    if info['is_stale']:
        print(f"⚠️  {db} is {info['days_old']} days old - re-extraction recommended")
    else:
        print(f"✅ {db} is {info['days_old']} days old - data is current")
```

### 2. Generate Compliance Report

**Get Essential Eight assessment**:

```python
from claude.tools.pmp.pmp_compliance_checker import PMPComplianceChecker

checker = PMPComplianceChecker()
latest_snapshot = checker.get_latest_snapshot()

report = checker.generate_report(snapshot_id=latest_snapshot)
print(f"Maturity Level: {report['maturity_level']}")
print(f"Overall Compliance: {report['overall_compliance']:.1%}")

print("\nCompliance Gaps:")
for gap in report['compliance_gaps']:
    print(f"  - {gap}")

print("\nRecommendations:")
for rec in report['recommendations']:
    print(f"  - {rec}")
```

### 3. Find Systems Missing Critical Patches

```python
from claude.tools.pmp.pmp_intelligence_service import PMPIntelligenceService

pmp = PMPIntelligenceService()

# Get systems with health_status = 3 (highly vulnerable)
vulnerable = pmp.get_vulnerable_systems(severity=3)

print(f"Found {len(vulnerable.data)} highly vulnerable systems:")
for sys in vulnerable.data:
    print(f"  {sys['name']} ({sys['os']}) - Last scan: {sys['last_scan_date']}")
```

### 4. Deployment Failure Analysis

```python
import sqlite3
from pathlib import Path

db_path = Path.home() / ".maia/databases/intelligence/pmp_intelligence.db"
conn = sqlite3.connect(db_path)

# Get failures by organization
query = """
SELECT
    s.organization,
    p.patch_name,
    COUNT(*) as failure_count,
    GROUP_CONCAT(pd.failure_reason) as reasons
FROM patch_deployments pd
JOIN systems s ON pd.resource_id = s.resource_id
JOIN patches p ON pd.patch_id = p.patch_id
WHERE pd.deployment_status = 206
GROUP BY s.organization, p.patch_name
ORDER BY failure_count DESC
"""

cursor = conn.cursor()
cursor.execute(query)

print("Top Deployment Failures:")
for org, patch, count, reasons in cursor.fetchall():
    print(f"\n{org} - {patch}: {count} failures")
    print(f"  Reasons: {reasons[:100]}...")
```

### 5. Metrics Calculation and Trending

```python
from claude.tools.pmp.pmp_metrics_calculator import PMPMetricsCalculator
import sqlite3

calculator = PMPMetricsCalculator()

# Calculate for latest snapshot
latest = calculator.get_latest_snapshot()
result = calculator.calculate_all(snapshot_id=latest)

print(f"Latest Metrics (Snapshot {latest}):")
print(f"  Total Systems: {result['system_health_metrics']['total_systems']}")
print(f"  Healthy Systems: {result['system_health_metrics']['healthy_systems']}")
print(f"  Vulnerable Systems: {result['system_health_metrics']['vulnerable_systems']}")
print(f"  Avg Deployment Success: {result['system_health_metrics']['avg_deployment_success_rate']:.1%}")
```

---

## Query Templates

Pre-built SQL templates for common queries (located in `pmp_query_templates.py`):

```python
from claude.tools.pmp.pmp_query_templates import TEMPLATES

# List all available templates
for name, template in TEMPLATES.items():
    print(f"{name}: {template['description']}")

# Example: Get Windows Server systems
template = TEMPLATES['windows_servers']
# Returns SQL ready for parameterized execution
```

**Available templates**:
- `org_systems` - Systems by organization pattern
- `windows_servers` - Windows Server systems only
- `vulnerable_systems` - Health status >= threshold
- `stale_systems` - Not scanned in N days
- `failed_patches` - Patches with deployment failures
- `critical_patches_missing` - Undeployed critical patches
- `deployment_failures_by_system` - Failures grouped by system
- `reboot_pending_systems` - Awaiting reboot after patch
- `org_health_summary` - Health metrics by organization
- `os_distribution` - System count by OS
- `never_patched_systems` - Systems with no patch history

---

## Data Migration from Legacy System

If you need to migrate data from archived legacy databases:

```bash
cd $MAIA_ROOT

# Migrate pmp_complete_intelligence.db
python3 claude/tools/pmp/pmp_data_migrator.py \
  --source ~/.maia/archive/pmp_legacy/pmp_complete_intelligence.db \
  --target ~/.maia/databases/intelligence/pmp_intelligence.db \
  --table-mapping old_systems:systems,old_patches:patches

# Verify migration
python3 -c "
import sqlite3
conn = sqlite3.connect(Path.home() / '.maia/databases/intelligence/pmp_intelligence.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM systems')
print(f'Migrated {cursor.fetchone()[0]} systems')
"
```

---

## Troubleshooting

### Issue: "FileNotFoundError: Database not found"

**Cause**: Unified database hasn't been created yet

**Solution**:
```bash
# Run the unified extractor
python3 $MAIA_ROOT/claude/tools/pmp/pmp_unified_extractor.py
# This creates pmp_intelligence.db with all schema
```

### Issue: "Data is stale (>7 days)"

**Cause**: Last extraction was more than 7 days ago

**Solution**:
```bash
# Manual re-extraction
python3 $MAIA_ROOT/claude/tools/pmp/pmp_unified_extractor.py

# Or verify scheduler is running
ps aux | grep CollectionScheduler
# Check last run time in logs:
tail -f ~/.maia/logs/collection_scheduler.log
```

### Issue: "Some endpoints failed, partial data extracted"

**Cause**: One or more API endpoints are unreachable

**Expected behavior**: Unified extractor continues with available data

**How to investigate**:
```python
from claude.tools.pmp.pmp_unified_extractor import UnifiedPMPExtractor

extractor = UnifiedPMPExtractor()
snapshot_id = extractor.extract()

# Check endpoint results
print(extractor.endpoint_results)
# Example output:
# {
#   'summary': {'success': True, 'count': 156},
#   'vulnerabilities': {'success': False, 'error': 'Connection timeout'},
#   'deployments': {'success': True, 'count': 892}
# }
```

### Issue: "Compliance checker returns 'database not found'"

**Cause**: Compliance checker expects unified database location

**Solution**:
```python
from pathlib import Path
from claude.tools.pmp.pmp_compliance_checker import PMPComplianceChecker

# Explicitly specify database path
checker = PMPComplianceChecker(
    db_path=Path.home() / ".maia/databases/intelligence/pmp_intelligence.db"
)

report = checker.generate_report(snapshot_id=latest)
```

---

## CLI Usage

### Extract Data
```bash
python3 $MAIA_ROOT/claude/tools/pmp/pmp_unified_extractor.py
```

### Check Compliance
```bash
# Interactive mode (asks for snapshot ID)
python3 $MAIA_ROOT/claude/tools/pmp/pmp_compliance_checker.py

# With specific snapshot
python3 -c "
from claude.tools.pmp.pmp_compliance_checker import PMPComplianceChecker
checker = PMPComplianceChecker()
print(checker.generate_report(snapshot_id=1234567890))
"
```

### Calculate Metrics
```bash
python3 -c "
from claude.tools.pmp.pmp_metrics_calculator import PMPMetricsCalculator
calc = PMPMetricsCalculator()
result = calc.calculate_all(snapshot_id=1234567890)
print(f'Patch Metrics: {result[\"patch_metrics\"]}')
print(f'System Health: {result[\"system_health_metrics\"]}')
"
```

### Query Data
```bash
# List all systems
python3 -c "
from claude.tools.pmp.pmp_intelligence_service import PMPIntelligenceService
pmp = PMPIntelligenceService()
result = pmp.get_systems_by_organization('GS1%')
print(f'Found {len(result.data)} systems')
"
```

---

## Integration with Other Systems

### CollectionScheduler Integration

The unified extractor is registered with the daily collection scheduler:

**Config location**: `~/.maia/config/collection_schedule.yaml`

```yaml
sources:
  pmp:
    refresh_time: "18:00"
    enabled: true
    refresh_command: "python3 claude/tools/pmp/pmp_unified_extractor.py"
```

### Capability Database Integration

Core PMP capabilities registered in `capabilities.db`:

```bash
sqlite3 $MAIA_ROOT/claude/data/databases/system/capabilities.db \
  "SELECT name, category FROM capabilities WHERE name LIKE '%pmp_unified%'"
```

**Registered capabilities**:
- `pmp_unified_extractor.py` (sre)
- `pmp_metrics_calculator.py` (sre)
- `pmp_compliance_checker.py` (sre)
- `pmp_data_migrator.py` (sre)

---

## Reference

### Key Files

| File | Purpose |
|------|---------|
| `claude/tools/pmp/pmp_unified_extractor.py` | Main orchestrator |
| `claude/tools/pmp/pmp_metrics_calculator.py` | Metrics derivation |
| `claude/tools/pmp/pmp_compliance_checker.py` | E8 compliance evaluation |
| `claude/tools/pmp/pmp_intelligence_service.py` | Query interface |
| `claude/tools/pmp/pmp_unified_schema.sql` | Database schema |
| `claude/tools/pmp/pmp_data_migrator.py` | Legacy data migration |
| `~/.maia/config/collection_schedule.yaml` | Scheduler configuration |

### Environment Variables

None required - uses default locations:
- Database: `~/.maia/databases/intelligence/pmp_intelligence.db`
- Config: `~/.maia/config/`
- Logs: `~/.maia/logs/`

### Performance Notes

- Single extraction: 2-5 minutes (depends on API responsiveness)
- Metrics calculation: <30 seconds
- Compliance assessment: <10 seconds
- Typical daily schedule impact: minimal (18:00 UTC daily)

---

## Support & Escalation

**For data issues**:
1. Check data freshness with `get_data_freshness_report()`
2. Verify API authentication with `PMPOAuthManager().verify_credentials()`
3. Re-run extractor: `pmp_unified_extractor.py`

**For compliance questions**:
- Refer to Essential Eight implementation docs in `pmp_compliance_checker.py`
- Review compliance report recommendations

**For schema changes**:
- Update `pmp_unified_schema.sql`
- Run migration: `pmp_data_migrator.py` with proper mapping

---

**Document Version**: 1.0
**Last Updated**: 2026-01-15
**Phase**: P7 - Cleanup & Documentation
**Sprint**: SPRINT-PMP-UNIFIED-001
