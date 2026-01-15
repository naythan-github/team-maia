# PMP Intelligence Service - Quick Reference

**Tool**: `claude/tools/pmp/pmp_intelligence_service.py`
**Version**: 1.0 (Sprint SPRINT-PMP-INTEL-001)
**Purpose**: Unified query interface for ManageEngine PMP databases

---

## Why Use This Tool?

**Before** (manual multi-database queries):
```python
# Had to query 3 different databases manually
conn1 = sqlite3.connect("~/.maia/databases/intelligence/pmp_config.db")
conn2 = sqlite3.connect("~/.maia/databases/intelligence/pmp_systemreports.db")
# Different column names: resource_name vs computer_name
# Different timestamp formats: Unix ms vs datetime strings
# No staleness warnings
```

**After** (unified interface):
```python
from claude.tools.pmp.pmp_intelligence_service import PMPIntelligenceService
pmp = PMPIntelligenceService()
result = pmp.get_failed_patches(org_pattern="GS1%")
# Automatic database selection, normalized schema, staleness warnings
```

---

## Quick Start

### Initialize Service
```python
from claude.tools.pmp.pmp_intelligence_service import PMPIntelligenceService

pmp = PMPIntelligenceService()
# Auto-discovers databases in ~/.maia/databases/intelligence/
print(f"Available: {pmp.available_databases}")
```

### Check Data Freshness (Always Do This First)
```python
freshness = pmp.get_data_freshness_report()
for db, info in freshness.items():
    if info['is_stale']:
        print(f"WARNING: {db} is {info['days_old']} days old!")
```

---

## Common Queries

### 1. Get Systems by Organization
```python
result = pmp.get_systems_by_organization("GS1%")
print(f"Found {len(result.data)} GS1 systems")

for sys in result.data:
    print(f"{sys['name']}: {sys['os']} (health: {sys['health_status']})")
```

**Returns normalized fields**: `name`, `os`, `health_status`, `organization`

### 2. Get Failed Patches
```python
result = pmp.get_failed_patches()
# Or filter:
result = pmp.get_failed_patches(org_pattern="GS1%", os_filter="Windows Server%")

for patch in result.data:
    print(f"{patch['patch_name']}: {patch['failed_count']} failures")
```

### 3. Get Vulnerable Systems
```python
# Highly vulnerable (health_status = 3)
result = pmp.get_vulnerable_systems(severity=3)

# Moderate + Highly vulnerable (health_status >= 2)
result = pmp.get_vulnerable_systems(severity=2)
```

### 4. Get Patch Deployment Status
```python
result = pmp.get_patch_deployment_status("KB5068864")
for sys in result.data:
    print(f"{sys['system_name']}: {sys['status_text']}")
```

### 5. Raw SQL Query
```python
result = pmp.query_raw(
    "SELECT COUNT(*) as cnt FROM all_systems",
    database="pmp_config.db"  # or "auto" for automatic selection
)
```

---

## Query Templates

Pre-built SQL patterns for common queries:

```python
from claude.tools.pmp.pmp_query_templates import TEMPLATES, describe_templates

# List all templates
print(describe_templates())

# Available templates:
# - org_systems: Systems by organization
# - windows_servers: Windows Server systems only
# - vulnerable_systems: Health status >= threshold
# - stale_systems: Not scanned in N days
# - failed_patches: Patches with deployment failures
# - failed_patches_windows: Windows-specific failures
# - critical_patches_missing: Critical patches not deployed
# - deployment_failures_by_system: Failures grouped by system
# - reboot_pending_systems: Awaiting reboot
# - org_health_summary: Health by organization
# - os_distribution: System count by OS
# - never_patched_systems: Never been patched
```

---

## Understanding Results

### PMPQueryResult Structure
```python
@dataclass
class PMPQueryResult:
    data: List[Dict[str, Any]]      # Query results
    source_database: str            # Which DB was queried
    extraction_timestamp: datetime  # When data was extracted
    is_stale: bool                  # True if >7 days old
    staleness_warning: Optional[str] # Warning message
    query_time_ms: int              # Query performance
```

### Health Status Values
| Value | Meaning |
|-------|---------|
| 1 | Healthy |
| 2 | Moderately Vulnerable |
| 3 | Highly Vulnerable |

### Deployment Status Codes
| Code | Meaning |
|------|---------|
| 206 | Failed |
| 207 | Reboot Pending |
| 209 | Installed |
| 245 | Delayed |

---

## Database Reference

| Database | Content | Best For |
|----------|---------|----------|
| `pmp_config.db` | Aggregate data, policies, JSON raw_data | Summary queries, org-level analysis |
| `pmp_systemreports.db` | Per-system deployment details | System-specific queries, failure details |
| `pmp_resilient.db` | Fresh system inventory | Latest system snapshots |

---

## Troubleshooting

### FileNotFoundError: Database directory not found
```python
# Databases not extracted. Run extractor:
python3 claude/tools/pmp/pmp_config_extractor.py
```

### Data is stale (>7 days)
```python
# Check freshness first
freshness = pmp.get_data_freshness_report()
# If stale, re-extract:
python3 claude/tools/pmp/pmp_resilient_extractor.py
```

### Missing per-system deployment details
```python
# pmp_systemreports.db may need updating:
python3 claude/tools/pmp/pmp_systemreport_extractor.py
```

---

## CLI Usage

```bash
# Interactive mode
python3 claude/tools/pmp/pmp_intelligence_service.py

# Query specific organization
python3 claude/tools/pmp/pmp_intelligence_service.py "GS1%"

# List query templates
python3 claude/tools/pmp/pmp_query_templates.py
```
