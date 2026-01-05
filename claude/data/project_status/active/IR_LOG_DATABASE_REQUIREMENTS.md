# IR Log Database Implementation Requirements

**Project**: Per-Investigation SQLite Log Storage
**Status**: REQUIREMENTS COMPLETE - Ready for Implementation
**Priority**: High
**Requesting Agent**: M365 Incident Response Agent v2.4
**Implementing Agent**: SRE Principal Engineer Agent

---

## 1. Problem Statement

### Current State
- M365 IR pipeline parses customer log exports (CSV/JSON) into analysis outputs
- Each analysis run is stateless - no persistence of parsed log data
- Follow-up questions require re-parsing source files
- No SQL query capability for ad-hoc investigation questions

### Pain Points
1. **Iterative investigations**: Analysts return with follow-up questions during active cases
2. **Re-parsing overhead**: Same logs parsed multiple times per investigation
3. **Limited querying**: Can't easily ask "show all activity from IP X across all log types"
4. **Correlation difficulty**: Joining sign-in logs + UAL + mailbox audit requires manual effort

### User Story
> As an IR analyst, I want parsed log data stored in a queryable database so that I can ask follow-up questions during an investigation without re-parsing source files.

---

## 2. Proposed Solution

### Architecture: Per-Investigation SQLite Database

Each investigation gets its own SQLite database containing all parsed log data. This maintains:
- **Case isolation**: Customer data stays separate (chain of custody, legal)
- **Portability**: Single `.db` file per case for archival/sharing
- **Query flexibility**: Full SQL for ad-hoc questions
- **Evidence preservation**: Original CSVs remain untouched

### Directory Structure
```
~/work_projects/ir_cases/{case_id}/
├── {case_id}_logs.db              # Parsed log data (NEW)
├── exports/                        # Original customer CSVs (unchanged)
│   ├── AzureADSignInLogs.csv
│   ├── UnifiedAuditLog.csv
│   └── MailboxAuditLog.csv
├── analysis/                       # Generated reports (unchanged)
│   ├── timeline.json
│   ├── iocs.json
│   └── report.md
└── metadata.json                   # Case metadata (NEW)
```

---

## 3. Technical Requirements

### 3.1 Database Schema

#### Table: `sign_in_logs`
```sql
CREATE TABLE sign_in_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,              -- ISO 8601 format
    user_principal_name TEXT NOT NULL,
    ip_address TEXT,
    location_city TEXT,
    location_country TEXT,
    location_coordinates TEXT,            -- "lat,lon"
    client_app TEXT,
    device_detail TEXT,                   -- JSON blob
    status_error_code INTEGER,
    status_failure_reason TEXT,
    conditional_access_status TEXT,
    mfa_detail TEXT,                      -- JSON blob
    risk_level TEXT,
    risk_detail TEXT,
    resource_display_name TEXT,
    app_display_name TEXT,
    correlation_id TEXT,
    raw_record TEXT,                      -- Original JSON for edge cases
    imported_at TEXT NOT NULL
);

CREATE INDEX idx_signin_timestamp ON sign_in_logs(timestamp);
CREATE INDEX idx_signin_user ON sign_in_logs(user_principal_name);
CREATE INDEX idx_signin_ip ON sign_in_logs(ip_address);
CREATE INDEX idx_signin_country ON sign_in_logs(location_country);
```

#### Table: `unified_audit_log`
```sql
CREATE TABLE unified_audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,              -- CreationDate in ISO 8601
    user_id TEXT,
    operation TEXT NOT NULL,
    workload TEXT,                        -- Exchange, AzureActiveDirectory, etc.
    record_type INTEGER,
    result_status TEXT,
    client_ip TEXT,
    user_agent TEXT,
    object_id TEXT,                       -- Target of operation
    item_type TEXT,
    audit_data TEXT,                      -- Full AuditData JSON
    raw_record TEXT,
    imported_at TEXT NOT NULL
);

CREATE INDEX idx_ual_timestamp ON unified_audit_log(timestamp);
CREATE INDEX idx_ual_user ON unified_audit_log(user_id);
CREATE INDEX idx_ual_operation ON unified_audit_log(operation);
CREATE INDEX idx_ual_ip ON unified_audit_log(client_ip);
CREATE INDEX idx_ual_workload ON unified_audit_log(workload);
```

#### Table: `mailbox_audit_log`
```sql
CREATE TABLE mailbox_audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    user TEXT NOT NULL,
    operation TEXT NOT NULL,
    log_on_type TEXT,                     -- Owner, Delegate, Admin
    client_ip TEXT,
    client_info TEXT,
    item_id TEXT,
    folder_path TEXT,
    subject TEXT,
    result TEXT,
    raw_record TEXT,
    imported_at TEXT NOT NULL
);

CREATE INDEX idx_mailbox_timestamp ON mailbox_audit_log(timestamp);
CREATE INDEX idx_mailbox_user ON mailbox_audit_log(user);
CREATE INDEX idx_mailbox_operation ON mailbox_audit_log(operation);
CREATE INDEX idx_mailbox_ip ON mailbox_audit_log(client_ip);
```

#### Table: `oauth_consents`
```sql
CREATE TABLE oauth_consents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    user_principal_name TEXT,
    app_id TEXT NOT NULL,
    app_display_name TEXT,
    permissions TEXT,                     -- JSON array
    consent_type TEXT,                    -- User, Admin
    client_ip TEXT,
    risk_score REAL,                      -- Calculated risk 0.0-1.0
    raw_record TEXT,
    imported_at TEXT NOT NULL
);

CREATE INDEX idx_oauth_timestamp ON oauth_consents(timestamp);
CREATE INDEX idx_oauth_user ON oauth_consents(user_principal_name);
CREATE INDEX idx_oauth_app ON oauth_consents(app_id);
```

#### Table: `inbox_rules`
```sql
CREATE TABLE inbox_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    user TEXT NOT NULL,
    operation TEXT,                       -- Set-InboxRule, New-InboxRule, Remove-InboxRule
    rule_name TEXT,
    rule_id TEXT,
    forward_to TEXT,
    forward_as_attachment_to TEXT,
    redirect_to TEXT,
    delete_message INTEGER,               -- Boolean
    move_to_folder TEXT,
    conditions TEXT,                      -- JSON
    client_ip TEXT,
    raw_record TEXT,
    imported_at TEXT NOT NULL
);

CREATE INDEX idx_rules_timestamp ON inbox_rules(timestamp);
CREATE INDEX idx_rules_user ON inbox_rules(user);
CREATE INDEX idx_rules_forward ON inbox_rules(forward_to);
```

#### Table: `import_metadata`
```sql
CREATE TABLE import_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_file TEXT NOT NULL,
    source_hash TEXT NOT NULL,            -- SHA256 of source file
    log_type TEXT NOT NULL,               -- sign_in, ual, mailbox, oauth
    records_imported INTEGER NOT NULL,
    records_failed INTEGER DEFAULT 0,
    import_started TEXT NOT NULL,
    import_completed TEXT,
    parser_version TEXT NOT NULL
);
```

### 3.2 Python Module Structure

```
claude/tools/m365_ir/
├── __init__.py                    # Existing
├── m365_log_parser.py             # Existing - extend
├── m365_ir_cli.py                 # Existing - extend
├── log_database.py                # NEW - Database management
├── log_importer.py                # NEW - CSV/JSON to SQLite
├── log_query.py                   # NEW - Query interface
└── schema.sql                     # NEW - Schema definitions
```

### 3.3 Core Classes

#### `IRLogDatabase` (log_database.py)
```python
class IRLogDatabase:
    """Manages per-investigation SQLite database."""

    def __init__(self, case_id: str, base_path: Optional[str] = None):
        """Initialize database for case.

        Args:
            case_id: Investigation identifier (e.g., PIR-ACME-2025-001)
            base_path: Base directory (default: ~/work_projects/ir_cases/)
        """

    def create(self) -> Path:
        """Create new database with schema."""

    def connect(self) -> sqlite3.Connection:
        """Get connection to existing database."""

    def get_stats(self) -> Dict[str, int]:
        """Return record counts per table."""

    def vacuum(self) -> None:
        """Optimize database after bulk import."""
```

#### `LogImporter` (log_importer.py)
```python
class LogImporter:
    """Imports parsed logs into SQLite database."""

    def __init__(self, db: IRLogDatabase):
        """Initialize with target database."""

    def import_sign_in_logs(self, source: Path) -> ImportResult:
        """Import Azure AD sign-in logs from CSV/JSON."""

    def import_ual(self, source: Path) -> ImportResult:
        """Import Unified Audit Log entries."""

    def import_mailbox_audit(self, source: Path) -> ImportResult:
        """Import mailbox audit logs."""

    def import_all(self, exports_dir: Path) -> Dict[str, ImportResult]:
        """Auto-detect and import all log types from directory."""

@dataclass
class ImportResult:
    source_file: str
    source_hash: str
    records_imported: int
    records_failed: int
    errors: List[str]
    duration_seconds: float
```

#### `LogQuery` (log_query.py)
```python
class LogQuery:
    """Query interface for investigation database."""

    def __init__(self, db: IRLogDatabase):
        """Initialize with database."""

    # Convenience methods
    def activity_by_ip(self, ip: str) -> List[Dict]:
        """All activity from IP across all log types."""

    def activity_by_user(self, user: str,
                         start: Optional[datetime] = None,
                         end: Optional[datetime] = None) -> List[Dict]:
        """User activity timeline."""

    def suspicious_operations(self) -> List[Dict]:
        """Pre-filtered high-risk operations."""

    def inbox_rules_summary(self) -> List[Dict]:
        """All inbox rule changes with risk indicators."""

    def oauth_consents_summary(self) -> List[Dict]:
        """All OAuth consents with risk scores."""

    # Raw SQL
    def execute(self, sql: str, params: tuple = ()) -> List[Dict]:
        """Execute arbitrary SQL query."""

    def execute_cross_table(self,
                            tables: List[str],
                            where: str,
                            params: tuple = ()) -> List[Dict]:
        """Query across multiple tables with UNION."""
```

### 3.4 CLI Extensions

Extend `m365_ir_cli.py` with new commands:

```bash
# Import logs into database (new default behavior)
python3 claude/tools/m365_ir/m365_ir_cli.py import /path/to/exports \
    --case-id PIR-ACME-2025-001 \
    --customer "ACME Corp"

# Query database
python3 claude/tools/m365_ir/m365_ir_cli.py query PIR-ACME-2025-001 \
    --ip 185.234.xx.xx

python3 claude/tools/m365_ir/m365_ir_cli.py query PIR-ACME-2025-001 \
    --user victim@acme.com \
    --start 2025-01-01 \
    --end 2025-01-15

python3 claude/tools/m365_ir/m365_ir_cli.py query PIR-ACME-2025-001 \
    --sql "SELECT * FROM sign_in_logs WHERE location_country = 'RU'"

# Show database stats
python3 claude/tools/m365_ir/m365_ir_cli.py stats PIR-ACME-2025-001

# List all cases
python3 claude/tools/m365_ir/m365_ir_cli.py list
```

---

## 4. Integration Requirements

### 4.1 Existing Pipeline Integration

The existing `analyze` command should:
1. Auto-create database during analysis
2. Import logs before running detectors
3. Store analysis results referencing DB records

```bash
# Existing command - now also creates DB
python3 claude/tools/m365_ir/m365_ir_cli.py analyze /path/to/exports \
    --customer "ACME Corp" \
    --output ./results
    # NEW: --case-id PIR-ACME-2025-001 (auto-generated if not provided)
```

### 4.2 IR Knowledge Base Integration

Link to existing `ir_knowledge.db`:
- When IOCs are extracted, cross-reference with IR Knowledge Base
- New IOCs discovered during queries should be easily addable

```python
# Example integration
from ir_knowledge import IRKnowledgeBase
from log_query import LogQuery

kb = IRKnowledgeBase("path/to/ir_knowledge.db")
query = LogQuery(case_db)

# Check if IP was seen before
ip = "185.234.xx.xx"
prior_hits = kb.query_ioc("ip", ip)
current_hits = query.activity_by_ip(ip)
```

### 4.3 Agent Integration

The IR agent should be able to:
1. Create/open case databases via natural language
2. Run queries based on investigation questions
3. Correlate across log types automatically

**Example Agent Interaction**:
```
USER: "Show me all activity from the Russian IP we found"

AGENT THOUGHT: Need to query the case database for IP activity
AGENT ACTION: query.activity_by_ip("185.234.xx.xx")
AGENT RESULT: [sign-in logs, UAL entries, mailbox audit entries]
```

---

## 5. Testing Requirements

### 5.1 Unit Tests

Location: `tests/m365_ir/`

| Test File | Coverage |
|-----------|----------|
| `test_log_database.py` | Database creation, schema, connections |
| `test_log_importer.py` | CSV/JSON parsing, import accuracy, error handling |
| `test_log_query.py` | Query methods, SQL injection prevention, edge cases |

### 5.2 Test Data

Create sanitized test fixtures:
```
tests/m365_ir/fixtures/
├── sample_signin_logs.csv       # 50 records, various scenarios
├── sample_ual.csv               # 100 records, key operations
├── sample_mailbox_audit.csv     # 30 records
├── malformed_logs.csv           # Error handling tests
└── expected_outputs/            # Expected query results
```

### 5.3 Integration Tests

| Test | Validates |
|------|-----------|
| Full import pipeline | CSV → DB → Query → Results |
| Cross-table queries | UNION queries across log types |
| Large file handling | 100K+ record imports |
| Concurrent access | Multiple query sessions |

### 5.4 Performance Benchmarks

| Scenario | Target |
|----------|--------|
| Import 100K sign-in logs | < 30 seconds |
| Query by IP (indexed) | < 100ms |
| Cross-table timeline query | < 500ms |
| Database file size | < 2x CSV size |

---

## 6. Security Requirements

### 6.1 Data Handling
- Original CSVs NEVER modified (chain of custody)
- Database files inherit directory permissions
- No PII in error logs/exceptions

### 6.2 Query Safety
- Parameterized queries only (no string interpolation)
- Read-only mode for query operations
- SQL injection prevention in CLI arguments

### 6.3 File Permissions
```bash
# Database files should be user-only readable
chmod 600 {case_id}_logs.db
```

---

## 7. Implementation Phases

### Phase 1: Core Database (Priority: HIGH)
- [ ] `log_database.py` - IRLogDatabase class
- [ ] `schema.sql` - All table definitions
- [ ] Unit tests for database operations
- **Deliverable**: Can create/connect to case databases

### Phase 2: Import Pipeline (Priority: HIGH)
- [ ] `log_importer.py` - LogImporter class
- [ ] Extend `m365_log_parser.py` for DB output
- [ ] Import metadata tracking
- [ ] Unit tests for import accuracy
- **Deliverable**: Can import all log types to DB

### Phase 3: Query Interface (Priority: HIGH)
- [ ] `log_query.py` - LogQuery class
- [ ] Convenience methods for common queries
- [ ] Raw SQL execution with safety
- [ ] Unit tests for query methods
- **Deliverable**: Can query case databases programmatically

### Phase 4: CLI Integration (Priority: MEDIUM)
- [ ] Extend `m365_ir_cli.py` with new commands
- [ ] `import`, `query`, `stats`, `list` subcommands
- [ ] Integration with existing `analyze` command
- **Deliverable**: Full CLI interface

### Phase 5: Agent Integration (Priority: MEDIUM)
- [ ] Update `m365_incident_response_agent.md` with new capabilities
- [ ] Add query examples to agent few-shots
- [ ] Integration with IR Knowledge Base
- **Deliverable**: Agent can use DB queries naturally

---

## 8. Success Criteria

| Criteria | Measurement |
|----------|-------------|
| Import reliability | 99.9% of valid records imported |
| Query performance | P95 < 500ms for indexed queries |
| Storage efficiency | DB size < 2x original CSV |
| Test coverage | > 90% for new modules |
| Agent usability | Follow-up questions answered without re-parsing |

---

## 9. Out of Scope (Future Considerations)

- Multi-tenant database (each case stays isolated)
- Cloud storage for databases (local only for now)
- Real-time log streaming (batch import only)
- GUI query builder (CLI/programmatic only)
- Cross-case queries (use IR Knowledge Base for this)

---

## 10. References

- Existing M365 IR tools: `claude/tools/m365_ir/`
- IR Knowledge Base: `claude/tools/ir/ir_knowledge.py`
- Test patterns: `tests/m365_ir/`
- TDD Protocol: `claude/context/core/tdd_development_protocol.md`

---

**Document Version**: 1.0
**Created**: 2025-01-05
**Author**: M365 Incident Response Agent
**Next Step**: Hand to SRE Principal Engineer Agent for implementation
