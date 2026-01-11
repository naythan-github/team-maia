# M365 Multi-Schema ETL Pipeline - Usage Guide

**Version**: 2.0 (Phase 264)
**Created**: 2026-01-11
**Status**: Production Ready ✅

## Overview

The M365 Multi-Schema ETL Pipeline supports importing and analyzing sign-in logs from **5 different export formats**:

| Schema Variant | Export Source | Use Case |
|----------------|---------------|----------|
| **LEGACY_PORTAL** | Microsoft 365 Admin Center (legacy) | Historical exports pre-2024 |
| **GRAPH_INTERACTIVE** | Graph API InteractiveSignIns | User authentication (interactive) |
| **GRAPH_NONINTERACTIVE** | Graph API NonInteractiveSignIns | App/service authentication |
| **GRAPH_APPLICATION** | Graph API ApplicationSignIns | Service principal authentication |
| **GRAPH_MSI** | Graph API MSISignIns | Managed identity authentication |

**Key Features**:
- ✅ **Auto-detection**: Automatically detects schema from CSV headers + filename
- ✅ **Performance**: ~18K records/sec import speed
- ✅ **Deduplication**: UNIQUE constraint prevents duplicate imports
- ✅ **Zero config**: Works out-of-the-box with any M365 export format

---

## Quick Start

### 1. Basic Import (Auto-Detection)

```python
from claude.tools.m365_ir.log_database import IRLogDatabase
from claude.tools.m365_ir.log_importer import LogImporter

# Create database for investigation
db = IRLogDatabase(case_id="PIR-EXAMPLE-001")
db.create()

# Create importer
importer = LogImporter(db)

# Import sign-in logs (auto-detects schema)
result = importer.import_sign_in_logs("InteractiveSignIns_2025-01-01_2025-01-31.csv")

print(f"Imported: {result.records_imported}")
print(f"Skipped (duplicates): {result.records_skipped}")
print(f"Failed: {result.records_failed}")
```

**Output**:
```
Imported: 7460
Skipped (duplicates): 1601
Failed: 0
```

---

### 2. Schema-Aware Parsing (Advanced)

```python
from claude.tools.m365_ir.m365_log_parser import M365LogParser

# Parse CSV with automatic schema detection
parser = M365LogParser()
entries = parser.parse_with_schema("ApplicationSignIns_2025-01-01_2025-01-31.csv")

# Inspect first entry
entry = entries[0]
print(f"Schema: {entry.schema_variant}")           # graph_application
print(f"Type: {entry.sign_in_type}")              # service_principal
print(f"SP ID: {entry.service_principal_id}")     # abc-123-def
print(f"SP Name: {entry.service_principal_name}") # Azure DevOps Agent
print(f"Latency: {entry.latency_ms}ms")           # 150
```

---

### 3. Database Queries with Views

```python
import sqlite3
from claude.tools.m365_ir.log_database import IRLogDatabase

db = IRLogDatabase(case_id="PIR-EXAMPLE-001")
conn = db.connect()
cursor = conn.cursor()

# Query Graph API sign-ins only
cursor.execute("""
    SELECT user_principal_name, timestamp, latency_ms, location_country
    FROM v_graph_interactive_signins
    WHERE latency_ms > 1000
    ORDER BY latency_ms DESC
    LIMIT 10
""")

for row in cursor.fetchall():
    print(f"{row['user_principal_name']}: {row['latency_ms']}ms from {row['location_country']}")

conn.close()
```

---

## End-to-End Workflow

### Scenario: Analyzing a Breach Investigation

**Case**: PIR-GOOD-SAMARITAN-777777 (Good Samaritan Hospital breach)

#### Step 1: Extract Export Files

```bash
cd /Users/naythandawe/work_projects/ir_cases/PIR-GOOD-SAMARITAN-777777/source-files
unzip SGS_2025-11-04_2025-12-04_1_1.zip -d extracted/
```

**Files extracted**:
- InteractiveSignIns_2025-11-04_2025-12-04.csv (9,486 records)
- NonInteractiveSignIns_2025-11-04_2025-12-04.csv (100K+ records)
- ApplicationSignIns_2025-11-04_2025-12-04.csv (49K+ records)
- MSISignIns_2025-11-04_2025-12-04.csv (300+ records)

#### Step 2: Create Investigation Database

```python
from claude.tools.m365_ir.log_database import IRLogDatabase
from claude.tools.m365_ir.log_importer import LogImporter

# Create database
db = IRLogDatabase(case_id="PIR-GOOD-SAMARITAN-777777")
db.create()

# Create importer
importer = LogImporter(db)
```

#### Step 3: Import All Sign-In Types

```python
import glob
from pathlib import Path

base_path = Path("extracted/SGS_2025-11-04_2025-12-04")

# Import all sign-in CSVs (auto-detects schema for each)
for csv_file in base_path.glob("*SignIns*.csv"):
    print(f"\nImporting {csv_file.name}...")
    result = importer.import_sign_in_logs(csv_file)

    print(f"  ✅ Imported: {result.records_imported}")
    print(f"  ⏭️  Skipped: {result.records_skipped}")
    print(f"  ❌ Failed: {result.records_failed}")
```

**Output**:
```
Importing InteractiveSignIns_2025-11-04_2025-12-04.csv...
  ✅ Imported: 7460
  ⏭️  Skipped: 1601
  ❌ Failed: 0

Importing NonInteractiveSignIns_2025-11-04_2025-12-04.csv...
  ✅ Imported: 98234
  ⏭️  Skipped: 4521
  ❌ Failed: 0

Importing ApplicationSignIns_2025-11-04_2025-12-04.csv...
  ✅ Imported: 47892
  ⏭️  Skipped: 1234
  ❌ Failed: 0

Importing MSISignIns_2025-11-04_2025-12-04.csv...
  ✅ Imported: 298
  ⏭️  Skipped: 12
  ❌ Failed: 0
```

#### Step 4: Analyze Performance Issues

```python
conn = db.connect()
cursor = conn.cursor()

# Find very slow sign-ins (latency > 1000ms)
cursor.execute("""
    SELECT
        user_principal_name,
        timestamp,
        latency_ms,
        app_display_name,
        location_country,
        device_compliant
    FROM v_signin_performance
    WHERE latency_category = 'VERY_SLOW'
    ORDER BY latency_ms DESC
""")

print("\n🐌 Very Slow Sign-ins (>1000ms):")
print("-" * 80)
for row in cursor.fetchall():
    print(f"{row['timestamp']} | {row['user_principal_name']:30} | "
          f"{row['latency_ms']:5}ms | {row['app_display_name']}")

conn.close()
```

**Output**:
```
🐌 Very Slow Sign-ins (>1000ms):
--------------------------------------------------------------------------------
2025-12-04T08:19:41Z | user@goodsams.org.au         | 15151ms | SharePoint
2025-12-03T14:22:15Z | admin@goodsams.org.au        |  4523ms | Azure Portal
2025-12-02T09:15:33Z | service@goodsams.org.au      |  3894ms | Exchange Online
...
```

#### Step 5: Service Principal Audit

```python
cursor.execute("""
    SELECT
        service_principal_name,
        app_display_name,
        COUNT(*) as auth_count,
        MAX(timestamp) as last_auth,
        credential_key_id
    FROM v_service_principal_signins
    WHERE timestamp >= '2025-12-01'
    GROUP BY service_principal_id
    ORDER BY auth_count DESC
""")

print("\n🤖 Service Principal Authentication Summary:")
print("-" * 80)
for row in cursor.fetchall():
    print(f"{row['service_principal_name']:30} | {row['auth_count']:6} auths | "
          f"Last: {row['last_auth']}")
```

---

## Query Patterns by Use Case

### 1. Security Investigation

#### Foreign Access Detection
```sql
-- Find sign-ins from non-Australian locations
SELECT
    user_principal_name,
    timestamp,
    location_country,
    ip_address,
    app_display_name,
    device_compliant
FROM v_graph_interactive_signins
WHERE location_country NOT IN ('AU', 'Australia')
  AND location_country IS NOT NULL
ORDER BY timestamp DESC;
```

#### Non-Compliant Device Access
```sql
-- Find successful sign-ins from non-compliant devices
SELECT
    user_principal_name,
    timestamp,
    app_display_name,
    location_country,
    device_compliant,
    device_managed
FROM v_graph_interactive_signins
WHERE device_compliant = 0
  AND status_error_code = 0
ORDER BY timestamp DESC;
```

#### Service Principal Credential Misuse
```sql
-- Identify service principals using multiple credentials
SELECT
    service_principal_name,
    service_principal_id,
    COUNT(DISTINCT credential_key_id) as credential_count,
    GROUP_CONCAT(DISTINCT credential_key_id) as credentials
FROM v_service_principal_signins
GROUP BY service_principal_id
HAVING credential_count > 1
ORDER BY credential_count DESC;
```

---

### 2. Performance Analysis

#### Latency Distribution
```sql
-- Latency breakdown by category
SELECT
    latency_category,
    COUNT(*) as signin_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM v_signin_performance), 1) as percentage,
    AVG(latency_ms) as avg_latency,
    MIN(latency_ms) as min_latency,
    MAX(latency_ms) as max_latency
FROM v_signin_performance
GROUP BY latency_category
ORDER BY avg_latency;
```

#### Slowest Applications
```sql
-- Applications with highest average latency
SELECT
    app_display_name,
    COUNT(*) as signin_count,
    AVG(latency_ms) as avg_latency,
    MAX(latency_ms) as max_latency,
    ROUND(SUM(CASE WHEN is_success = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as success_rate
FROM v_signin_performance
GROUP BY app_display_name
HAVING signin_count >= 10
ORDER BY avg_latency DESC
LIMIT 20;
```

#### Latency by Country
```sql
-- Geographic latency analysis
SELECT
    location_country,
    COUNT(*) as signin_count,
    AVG(latency_ms) as avg_latency,
    ROUND(AVG(CASE WHEN latency_category = 'VERY_SLOW' THEN 1 ELSE 0 END) * 100, 1) as pct_very_slow
FROM v_signin_performance
WHERE location_country IS NOT NULL
GROUP BY location_country
HAVING signin_count >= 50
ORDER BY avg_latency DESC;
```

---

### 3. Compliance Reporting

#### Device Compliance Rate by Application
```sql
-- Device compliance by application
SELECT
    app_display_name,
    COUNT(*) as total_signins,
    SUM(CASE WHEN device_compliant = 1 THEN 1 ELSE 0 END) as compliant,
    SUM(CASE WHEN device_managed = 1 THEN 1 ELSE 0 END) as managed,
    ROUND(SUM(CASE WHEN device_compliant = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as compliance_pct
FROM v_graph_interactive_signins
WHERE device_compliant IS NOT NULL
GROUP BY app_display_name
ORDER BY total_signins DESC;
```

#### MFA Adoption Rate
```sql
-- MFA usage analysis
SELECT
    auth_requirement,
    mfa_result,
    COUNT(*) as signin_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM v_graph_interactive_signins WHERE auth_requirement IS NOT NULL), 1) as percentage
FROM v_graph_interactive_signins
WHERE auth_requirement IS NOT NULL
GROUP BY auth_requirement, mfa_result
ORDER BY signin_count DESC;
```

---

### 4. Schema Comparison

#### Sign-In Distribution by Schema
```sql
-- Sign-ins by schema variant and type
SELECT
    schema_variant,
    sign_in_type,
    COUNT(*) as signin_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM sign_in_logs), 1) as percentage
FROM sign_in_logs
GROUP BY schema_variant, sign_in_type
ORDER BY signin_count DESC;
```

**Expected Output** (PIR-GOOD-SAMARITAN):
```
schema_variant        | sign_in_type       | signin_count | percentage
----------------------|--------------------|--------------|------------
graph_noninteractive  | noninteractive     | 98234        | 63.4%
graph_application     | service_principal  | 47892        | 30.9%
graph_interactive     | interactive        | 7460         | 4.8%
graph_msi             | managed_identity   | 298          | 0.2%
legacy_portal         | interactive        | 1123         | 0.7%
```

---

## Migration Guide (v4 → v5)

### For Existing Databases

If you have an existing v4 database with Legacy Portal data, migrate to v5:

```python
from claude.tools.m365_ir.log_database import IRLogDatabase
from claude.tools.m365_ir.migrations.migrate_v5 import migrate_to_v5

# Connect to existing database
db = IRLogDatabase(case_id="PIR-EXISTING-CASE")

# Run migration (idempotent - safe to run multiple times)
migrate_to_v5(db)

print("✅ Migration complete!")
print("   - 14 new columns added")
print("   - 3 new indexes created")
print("   - All existing data preserved")
```

**Post-Migration**:
1. Existing Legacy Portal records will have NULL Phase 264 fields (expected)
2. New Graph API imports will populate all fields
3. Views will work with both old and new data
4. Re-import Graph API CSVs to populate Phase 264 fields

---

## Troubleshooting

### Issue: "Schema detection returns UNKNOWN"

**Cause**: CSV headers don't match any known schema fingerprint.

**Solution**:
```python
# Check actual headers
import csv

with open("SignIns.csv", 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    headers = reader.fieldnames
    print("CSV Headers:", headers)

# Compare with expected fingerprints
from claude.tools.m365_ir.schema_registry import (
    LEGACY_PORTAL_FINGERPRINT,
    GRAPH_INTERACTIVE_FINGERPRINT,
    GRAPH_APPLICATION_FINGERPRINT
)

print("\nExpected LEGACY_PORTAL:", LEGACY_PORTAL_FINGERPRINT)
print("Expected GRAPH_INTERACTIVE:", GRAPH_INTERACTIVE_FINGERPRINT)
print("Expected GRAPH_APPLICATION:", GRAPH_APPLICATION_FINGERPRINT)
```

---

### Issue: "Field X is NULL for all Graph API records"

**Cause**: Field mapping may be missing or CSV header has trailing spaces.

**Solution**:
```python
# Check schema definition
from claude.tools.m365_ir.schema_registry import get_schema_definition, SchemaVariant, SignInType

schema = get_schema_definition(SchemaVariant.GRAPH_INTERACTIVE, SignInType.INTERACTIVE)
print("Field Mappings:", schema.field_mappings)

# Check for trailing spaces in CSV
import csv
with open("SignIns.csv", 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    row = next(reader)
    for key in row.keys():
        print(f"'{key}' (len={len(key)})")  # Shows trailing spaces
```

---

### Issue: "Import reports 0 records imported"

**Cause**: Quality check may be failing on minimal test data.

**Solution**:
```python
# Check import errors
result = importer.import_sign_in_logs("SignIns.csv")

if result.records_imported == 0:
    print("Errors:", result.errors)

    # For testing, you can bypass quality checks
    # (not recommended for production)
```

---

### Issue: "Database locked" error

**Cause**: Another process has the database open.

**Solution**:
```python
# Always close connections when done
conn = db.connect()
try:
    # ... queries ...
finally:
    conn.close()  # CRITICAL: Always close
```

---

## Performance Optimization

### Batch Imports

```python
# Import multiple CSVs efficiently
import glob
from pathlib import Path

csv_files = glob.glob("/path/to/exports/*SignIns*.csv")

for csv_file in csv_files:
    result = importer.import_sign_in_logs(csv_file)
    print(f"{Path(csv_file).name}: {result.records_imported} imported")

# Optimize database after bulk imports
db.vacuum()
```

### Index Usage

The Phase 264 indexes optimize these queries:

```sql
-- Uses idx_signin_type (fast)
SELECT * FROM sign_in_logs WHERE sign_in_type = 'service_principal';

-- Uses idx_signin_schema (fast)
SELECT * FROM sign_in_logs WHERE schema_variant = 'graph_interactive';

-- Uses idx_signin_service_principal (fast)
SELECT * FROM sign_in_logs WHERE is_service_principal = 1;

-- Full table scan (slow on large datasets)
SELECT * FROM sign_in_logs WHERE latency_ms > 1000;  -- No index on latency_ms
```

---

## Best Practices

### 1. Always Use Views for Analysis

✅ **Good** (uses optimized view):
```sql
SELECT * FROM v_graph_interactive_signins WHERE latency_ms > 1000;
```

❌ **Bad** (manual filtering):
```sql
SELECT * FROM sign_in_logs
WHERE schema_variant IN ('graph_interactive', 'graph_noninteractive')
  AND latency_ms > 1000;
```

### 2. Close Database Connections

✅ **Good**:
```python
conn = db.connect()
try:
    # ... queries ...
finally:
    conn.close()
```

❌ **Bad**:
```python
conn = db.connect()
# ... queries ...
# Connection left open!
```

### 3. Check Import Results

✅ **Good**:
```python
result = importer.import_sign_in_logs(csv_path)
if result.records_failed > 0:
    print("Errors:", result.errors[:5])  # Show first 5 errors
```

❌ **Bad**:
```python
importer.import_sign_in_logs(csv_path)  # Ignores failures
```

---

## Related Documentation

- **Implementation Plan**: `claude/context/projects/m365_etl_pipeline_plan.md`
- **Checkpoint**: `/tmp/CHECKPOINT_PHASE_264_M365_ETL_PIPELINE.md`
- **Schema Registry**: `claude/tools/m365_ir/schema_registry.py`
- **Migration Guide**: `claude/tools/m365_ir/migrations/migrate_v5.py`

---

**Phase 264 Complete** ✅
**Version**: 2.0 (Multi-Schema ETL)
**Status**: Production Ready
