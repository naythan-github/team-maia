# IR Timeline Persistence - Requirements Document

**Version**: 1.1 (Decisions Finalized)
**Author**: DevOps Principal Architect Agent
**Date**: 2026-01-09
**Status**: APPROVED - Ready for Implementation
**Handoff To**: SRE Principal Engineer Agent (TDD Implementation)
**Phase**: 260 (IR Timeline Persistence)

---

## 1. Problem Statement

### Current State
The M365 IR pipeline builds attack timelines **in memory only** via `timeline_builder.py`:

```python
# Current implementation - all in memory
builder = TimelineBuilder()
timeline = builder.build(signin_entries, audit_entries, mailbox_entries)
# timeline is List[TimelineEvent] - lost when session ends
```

### Issues
| Issue | Impact |
|-------|--------|
| **No persistence** | Timeline lost between analysis sessions |
| **No incremental building** | Must rebuild from scratch each time |
| **No analyst annotations** | Cannot add notes to specific events |
| **No audit trail** | No record of what was analyzed when |
| **No cross-session continuity** | Returning to case loses prior timeline work |
| **Manual PIR correlation** | Timeline not linked to PIR sections |

### Business Impact
- Analyst time wasted rebuilding timelines
- Risk of missing events on re-analysis
- No version history of timeline evolution
- Cannot track analyst findings over multi-day investigations

---

## 2. Proposed Solution

### 2.1 New Database Tables

Add three tables to the existing per-case SQLite database (`PIR-{CASE}_logs.db`):

#### Table 1: `timeline_events`
Core timeline event storage with full audit trail.

```sql
CREATE TABLE timeline_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Event identification
    event_hash TEXT NOT NULL UNIQUE,  -- SHA256 of (timestamp, user, action, source_id)

    -- Core event data
    timestamp TEXT NOT NULL,          -- ISO8601 UTC
    user_principal_name TEXT NOT NULL,
    action TEXT NOT NULL,             -- "Sign-in from AU", "Set-InboxRule", etc.
    details TEXT,                     -- Extended description

    -- Source traceability (FK to raw log tables)
    source_type TEXT NOT NULL,        -- 'sign_in_logs', 'entra_audit_log', 'unified_audit_log', etc.
    source_id INTEGER NOT NULL,       -- FK to source table's id

    -- Classification
    phase TEXT,                       -- EventPhase enum value
    severity TEXT DEFAULT 'INFO',     -- INFO, WARNING, ALERT, CRITICAL
    mitre_technique TEXT,             -- T1078.004, T1114.003, etc.

    -- Evidence (denormalized for query performance)
    ip_address TEXT,
    location_country TEXT,
    client_app TEXT,

    -- Metadata
    created_at TEXT NOT NULL,         -- When added to timeline
    created_by TEXT DEFAULT 'system', -- 'system' or analyst name

    -- Soft delete for timeline curation
    excluded INTEGER DEFAULT 0,       -- 1 = excluded from timeline view
    exclusion_reason TEXT
);

-- Indexes
CREATE INDEX idx_timeline_timestamp ON timeline_events(timestamp);
CREATE INDEX idx_timeline_user ON timeline_events(user_principal_name);
CREATE INDEX idx_timeline_phase ON timeline_events(phase);
CREATE INDEX idx_timeline_severity ON timeline_events(severity);
CREATE INDEX idx_timeline_source ON timeline_events(source_type, source_id);
CREATE INDEX idx_timeline_mitre ON timeline_events(mitre_technique);
```

#### Table 2: `timeline_annotations`
Analyst notes and findings attached to specific events.

```sql
CREATE TABLE timeline_annotations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Link to timeline event
    timeline_event_id INTEGER NOT NULL,

    -- Annotation content
    annotation_type TEXT NOT NULL,    -- 'note', 'finding', 'question', 'ioc', 'false_positive'
    content TEXT NOT NULL,

    -- PIR integration
    pir_section TEXT,                 -- 'executive_summary', 'timeline', 'root_cause', etc.
    include_in_pir INTEGER DEFAULT 1,

    -- Metadata
    created_at TEXT NOT NULL,
    created_by TEXT DEFAULT 'analyst',
    updated_at TEXT,

    FOREIGN KEY (timeline_event_id) REFERENCES timeline_events(id)
);

CREATE INDEX idx_annotation_event ON timeline_annotations(timeline_event_id);
CREATE INDEX idx_annotation_type ON timeline_annotations(annotation_type);
CREATE INDEX idx_annotation_pir ON timeline_annotations(pir_section);
```

#### Table 3: `timeline_phases`
Attack phase boundaries with confidence levels.

```sql
CREATE TABLE timeline_phases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Phase definition
    phase TEXT NOT NULL,              -- EventPhase enum value
    phase_start TEXT NOT NULL,        -- ISO8601 timestamp
    phase_end TEXT,                   -- NULL = ongoing/unknown

    -- Trigger event
    trigger_event_id INTEGER,         -- FK to timeline_events

    -- Classification
    confidence TEXT DEFAULT 'MEDIUM', -- HIGH, MEDIUM, LOW
    description TEXT NOT NULL,

    -- Evidence count (denormalized)
    event_count INTEGER DEFAULT 0,

    -- Metadata
    created_at TEXT NOT NULL,
    updated_at TEXT,

    FOREIGN KEY (trigger_event_id) REFERENCES timeline_events(id)
);

CREATE INDEX idx_phase_name ON timeline_phases(phase);
CREATE INDEX idx_phase_start ON timeline_phases(phase_start);
CREATE INDEX idx_phase_confidence ON timeline_phases(confidence);
```

#### Table 4: `timeline_build_history`
Audit trail of timeline generation runs.

```sql
CREATE TABLE timeline_build_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Build metadata
    build_timestamp TEXT NOT NULL,
    build_type TEXT NOT NULL,         -- 'full', 'incremental', 'manual'

    -- Statistics
    events_added INTEGER DEFAULT 0,
    events_updated INTEGER DEFAULT 0,
    phases_detected INTEGER DEFAULT 0,

    -- Source data summary
    source_tables TEXT,               -- JSON: {"sign_in_logs": 1500, "entra_audit_log": 200}
    date_range_start TEXT,
    date_range_end TEXT,

    -- Parameters used
    home_country TEXT DEFAULT 'AU',
    parameters TEXT,                  -- JSON: additional build parameters

    -- Status
    status TEXT DEFAULT 'completed',  -- 'completed', 'partial', 'failed'
    error_message TEXT
);

CREATE INDEX idx_build_timestamp ON timeline_build_history(build_timestamp);
CREATE INDEX idx_build_status ON timeline_build_history(status);
```

---

### 2.2 View: Unified Timeline

SQL view combining events with annotations for easy querying:

```sql
CREATE VIEW v_timeline AS
SELECT
    te.id,
    te.timestamp,
    te.user_principal_name,
    te.action,
    te.details,
    te.source_type,
    te.phase,
    te.severity,
    te.mitre_technique,
    te.ip_address,
    te.location_country,
    te.excluded,

    -- Aggregated annotations
    (SELECT COUNT(*) FROM timeline_annotations ta WHERE ta.timeline_event_id = te.id) as annotation_count,
    (SELECT GROUP_CONCAT(ta.annotation_type, ', ') FROM timeline_annotations ta WHERE ta.timeline_event_id = te.id) as annotation_types,

    -- Phase context
    tp.phase as phase_name,
    tp.confidence as phase_confidence

FROM timeline_events te
LEFT JOIN timeline_phases tp ON te.phase = tp.phase
WHERE te.excluded = 0
ORDER BY te.timestamp;
```

---

## 3. Integration Requirements

### 3.1 TimelineBuilder Modifications

Update `timeline_builder.py` to support persistence:

```python
class TimelineBuilder:
    def __init__(self, db: IRLogDatabase, home_country: str = "AU"):
        self.db = db
        self.home_country = home_country

    def build_and_persist(
        self,
        incremental: bool = True,
        force_rebuild: bool = False
    ) -> TimelineBuildResult:
        """
        Build timeline from raw logs and persist to database.

        Args:
            incremental: Only process new records since last build
            force_rebuild: Clear existing timeline and rebuild from scratch

        Returns:
            TimelineBuildResult with statistics
        """
        pass

    def add_annotation(
        self,
        event_id: int,
        annotation_type: str,
        content: str,
        pir_section: Optional[str] = None
    ) -> int:
        """Add analyst annotation to timeline event."""
        pass

    def exclude_event(self, event_id: int, reason: str) -> None:
        """Soft-delete event from timeline with reason."""
        pass

    def get_timeline(
        self,
        user: Optional[str] = None,
        phase: Optional[str] = None,
        severity: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        include_excluded: bool = False
    ) -> List[TimelineEvent]:
        """Query persisted timeline with filters."""
        pass
```

### 3.2 CLI Integration

Add timeline commands to `m365_ir_cli.py`:

```bash
# Build/rebuild timeline
python3 m365_ir_cli.py timeline build PIR-CASE-ID [--incremental] [--force]

# Query timeline
python3 m365_ir_cli.py timeline query PIR-CASE-ID [--user USER] [--phase PHASE] [--severity SEVERITY]

# Add annotation
python3 m365_ir_cli.py timeline annotate PIR-CASE-ID EVENT_ID --type note --content "Analyst finding"

# Export for PIR
python3 m365_ir_cli.py timeline export PIR-CASE-ID --format markdown --sections timeline,findings

# Show timeline stats
python3 m365_ir_cli.py timeline stats PIR-CASE-ID
```

### 3.3 Query Patterns for PIR Generation

#### Executive Summary Events
```sql
SELECT * FROM v_timeline
WHERE severity IN ('CRITICAL', 'ALERT')
ORDER BY timestamp
LIMIT 10;
```

#### Phase-by-Phase Timeline
```sql
SELECT
    tp.phase,
    tp.phase_start,
    tp.phase_end,
    tp.confidence,
    tp.description,
    tp.event_count,
    (SELECT GROUP_CONCAT(te.action, '; ')
     FROM timeline_events te
     WHERE te.phase = tp.phase
     ORDER BY te.timestamp
     LIMIT 5) as key_events
FROM timeline_phases tp
ORDER BY tp.phase_start;
```

#### Analyst Findings for PIR
```sql
SELECT
    te.timestamp,
    te.user_principal_name,
    te.action,
    ta.content as finding,
    ta.pir_section
FROM timeline_events te
JOIN timeline_annotations ta ON ta.timeline_event_id = te.id
WHERE ta.annotation_type = 'finding'
  AND ta.include_in_pir = 1
ORDER BY ta.pir_section, te.timestamp;
```

#### IOC Extraction from Timeline
```sql
SELECT DISTINCT
    te.ip_address,
    te.location_country,
    COUNT(*) as event_count,
    MIN(te.timestamp) as first_seen,
    MAX(te.timestamp) as last_seen
FROM timeline_events te
WHERE te.severity IN ('CRITICAL', 'ALERT')
  AND te.ip_address IS NOT NULL
GROUP BY te.ip_address, te.location_country
ORDER BY event_count DESC;
```

---

## 4. Incremental Build Logic

### 4.1 Detection of New Records

Track last processed record per source table:

```sql
-- Get last processed timestamp per source
SELECT source_type, MAX(timestamp) as last_processed
FROM timeline_events
GROUP BY source_type;

-- Find new records to process
SELECT * FROM sign_in_logs
WHERE timestamp > :last_processed_signin
ORDER BY timestamp;
```

### 4.2 Event Hash for Deduplication

```python
def compute_event_hash(timestamp: str, user: str, action: str, source_id: int) -> str:
    """Generate unique hash for timeline event deduplication."""
    data = f"{timestamp}|{user}|{action}|{source_id}"
    return hashlib.sha256(data.encode()).hexdigest()
```

### 4.3 Build Process Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    TIMELINE BUILD FLOW                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Check build history for last run                         │
│     └─> If incremental: get last_processed per source        │
│                                                              │
│  2. Query new records from source tables                     │
│     └─> sign_in_logs, entra_audit_log, unified_audit_log    │
│     └─> Filter: timestamp > last_processed                   │
│                                                              │
│  3. Transform to TimelineEvent objects                       │
│     └─> Compute event_hash                                   │
│     └─> Detect phase (INITIAL_ACCESS, PERSISTENCE, etc.)     │
│     └─> Set severity based on rules                          │
│     └─> Map MITRE technique                                  │
│                                                              │
│  4. INSERT OR IGNORE into timeline_events                    │
│     └─> event_hash UNIQUE prevents duplicates                │
│                                                              │
│  5. Update timeline_phases                                   │
│     └─> Detect new phase boundaries                          │
│     └─> Update event_count                                   │
│                                                              │
│  6. Record in timeline_build_history                         │
│     └─> events_added, events_updated, status                 │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. Migration Strategy

### 5.1 Schema Version Update

Update `SCHEMA_VERSION` in `log_database.py`:
```python
# v4: Timeline persistence (Phase XXX)
SCHEMA_VERSION = 4
```

### 5.2 Migration Script

```python
def migrate_to_v4(db: IRLogDatabase) -> None:
    """Add timeline tables to existing databases."""
    conn = db.connect()
    cursor = conn.cursor()

    # Check current version
    cursor.execute("SELECT MAX(version_id) FROM schema_versions WHERE log_type = 'database'")
    current = cursor.fetchone()[0] or 3

    if current < 4:
        # Create new tables
        _create_timeline_tables(cursor)
        _create_timeline_indexes(cursor)
        _create_timeline_views(cursor)

        # Record migration
        cursor.execute("""
            INSERT INTO schema_versions (log_type, api_version, schema_hash, detected_date, notes)
            VALUES ('database', '4', ?, datetime('now'), 'Timeline persistence tables added')
        """, (compute_schema_hash(),))

        conn.commit()

    conn.close()
```

### 5.3 Backward Compatibility

- Existing databases without timeline tables continue to work
- Timeline build is opt-in via `timeline build` command
- No breaking changes to existing import/query workflows

---

## 6. Testing Requirements

### 6.1 Unit Tests

| Test | Description |
|------|-------------|
| `test_timeline_event_hash_uniqueness` | Same event produces same hash |
| `test_timeline_incremental_build` | Only new records processed |
| `test_timeline_phase_detection` | Correct phases assigned |
| `test_timeline_annotation_crud` | Create/read/update/delete annotations |
| `test_timeline_exclusion` | Soft delete works correctly |
| `test_timeline_view_excludes_deleted` | v_timeline hides excluded events |

### 6.2 Integration Tests

| Test | Description |
|------|-------------|
| `test_timeline_build_from_real_case` | Full build on PIR-OCULUS data |
| `test_timeline_pir_export` | Markdown export matches PIR format |
| `test_timeline_cli_commands` | All CLI subcommands work |
| `test_timeline_migration` | v3 → v4 migration succeeds |

### 6.3 Validation Dataset

Use existing PIR-OCULUS-2025-12-19 database for validation:
- 17,959 sign-in records
- Known attack timeline for comparison
- Expected phases: Initial Access, Persistence, Detection, Containment

---

## 7. Acceptance Criteria

### Must Have (P0)
- [ ] Timeline events persisted to SQLite
- [ ] Incremental build (no full rebuild required)
- [ ] Event hash deduplication
- [ ] Phase detection stored
- [ ] CLI `timeline build` command
- [ ] CLI `timeline query` command
- [ ] Backward compatible with existing DBs

### Should Have (P1)
- [ ] Analyst annotations with PIR section tagging
- [ ] Soft-delete with exclusion reason
- [ ] Timeline export to markdown
- [ ] Build history audit trail

### Nice to Have (P2)
- [ ] Timeline diff between builds
- [ ] Event correlation linking
- [ ] MITRE ATT&CK auto-mapping
- [ ] Timeline visualization output

---

## 8. Implementation Estimate

| Component | Complexity | Files Modified |
|-----------|------------|----------------|
| Schema tables | Low | `log_database.py` |
| TimelineBuilder persistence | Medium | `timeline_builder.py` |
| CLI commands | Medium | `m365_ir_cli.py` |
| Migration script | Low | New file |
| Unit tests | Medium | New test file |
| Integration tests | Medium | New test file |

**Recommended approach**: TDD - write tests first, then implement.

---

## 9. Design Decisions (Finalized)

| Question | Decision | Rationale |
|----------|----------|-----------|
| **Event granularity** | Interesting events only | Avoid duplicating raw data; focus on anomalies, foreign logins, phase triggers |
| **Annotation storage** | Same per-case DB | Single source of truth; portable when archived to SharePoint |
| **Multi-analyst support** | Yes | `created_by` field required; source from `git config user.name` or `MAIA_ANALYST` env |
| **Timeline versioning** | No (Phase 2 if needed) | Build history + annotation timestamps sufficient; defer complexity |

### 9.1 Event Inclusion Criteria

**Include in timeline (interesting events):**
| Event Type | Source Table | Rationale |
|------------|--------------|-----------|
| Foreign logins (non-AU) | `sign_in_logs` | Attack indicators |
| Failed auth (status != 0) | `sign_in_logs`, `legacy_auth_logs` | Credential attacks |
| Legacy auth events | `legacy_auth_logs` | MFA bypass vectors |
| Inbox rule changes | `inbox_rules`, `unified_audit_log` | Persistence |
| Password/MFA changes | `entra_audit_log`, `mfa_changes` | Account manipulation |
| Admin role assignments | `admin_role_assignments`, `entra_audit_log` | Privilege escalation |
| OAuth consents | `oauth_consents` | App-based attacks |
| High-risk IPs | Cross-reference `ir_knowledge.db` | Known bad actors |
| Transport rule changes | `transport_rules` | Exfiltration |

**Exclude by default:**
- Routine successful AU logins
- Normal business app access (Office, Teams from home country)
- Read-only mailbox operations without anomaly markers

**Escape hatch:** `--include-all` flag for complete timeline if needed.

### 9.2 Analyst Identity Source

```python
def get_analyst_name() -> str:
    """Get analyst name for created_by field."""
    # Priority: env var > git config > fallback
    import os
    import subprocess

    if name := os.environ.get('MAIA_ANALYST'):
        return name

    try:
        result = subprocess.run(
            ['git', 'config', 'user.name'],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except:
        return 'analyst'
```

---

## 10. Handoff Checklist

- [x] Problem statement documented
- [x] Schema design complete
- [x] Integration points identified
- [x] Query patterns defined
- [x] Migration strategy outlined
- [x] Testing requirements specified
- [x] Acceptance criteria defined

**Next Step**: Review with user, then handoff to SRE Agent for TDD implementation.
