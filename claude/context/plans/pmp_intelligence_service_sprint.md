# TDD Sprint Plan: PMP Unified Intelligence Service

**Sprint ID**: SPRINT-PMP-INTEL-001
**Created**: 2026-01-15
**Completed**: 2026-01-15
**Author**: Data Analyst Agent (handoff from SRE Principal Engineer)
**Status**: ✅ COMPLETE - All phases passed

---

## Problem Statement

During PMP database analysis, Maia encountered significant friction:

| Issue | Impact | Example |
|-------|--------|---------|
| **Database fragmentation** | 3 DBs queried for single question | "GS1 Windows failures" required pmp_config.db + pmp_systemreports.db + pmp_resilient.db |
| **Schema inconsistencies** | Manual column mapping | `resource_name` vs `computer_name` vs `config_name` |
| **JSON extraction overhead** | Verbose queries | Every query needs `json_extract(raw_data, '$.field')` |
| **No semantic layer** | Agent must know raw schema | No "get_failed_patches_for_org()" abstraction |
| **Timestamp inconsistencies** | Manual conversion | Mixed Unix ms, Unix s, and DATETIME strings |
| **Stale data detection** | Manual checking | No automatic freshness warnings |

---

## Solution: Unified PMP Intelligence Service

A Python module providing:
1. **Single query interface** across all PMP databases
2. **Semantic query methods** for common questions
3. **Automatic database selection** based on query type
4. **Timestamp normalization** (all → ISO 8601)
5. **Data freshness tracking** with staleness warnings
6. **Query templates** for Maia agent consumption

---

## Sprint Phases (TDD Protocol)

### Phase 0: Discovery & Anti-Duplication Check
**Model**: Haiku (fast capability search)
**Duration**: Research only

- [ ] Search existing tools for similar functionality
- [ ] Verify no existing unified query interface
- [ ] Document gaps in current tooling
- [ ] Confirm sprint scope

**Gate**: No duplicate tool exists

---

### Phase 1: Test Infrastructure Setup
**Model**: Sonnet
**Deliverables**:
- [ ] `tests/test_pmp_intelligence_service.py` - Test file skeleton
- [ ] Mock database fixtures (SQLite in-memory)
- [ ] Sample data representing all 3 database schemas

**Tests** (must fail initially):
```python
def test_query_systems_by_org_returns_normalized_data():
    """Systems query returns consistent schema regardless of source DB."""

def test_query_failed_patches_aggregates_across_databases():
    """Failed patch query combines pmp_config + pmp_systemreports data."""

def test_timestamps_normalized_to_iso8601():
    """All timestamp fields converted to ISO 8601 strings."""

def test_staleness_warning_on_old_data():
    """Query result includes warning if data >7 days old."""
```

**Gate**: P1 - Tests exist and FAIL (red)

---

### Phase 2: Core Module Implementation
**Model**: Sonnet
**Deliverables**:
- [ ] `claude/tools/pmp/pmp_intelligence_service.py`

**Classes**:
```python
@dataclass
class PMPQueryResult:
    """Standardized query result with metadata."""
    data: List[Dict[str, Any]]
    source_database: str
    extraction_timestamp: datetime
    is_stale: bool  # True if >7 days old
    staleness_warning: Optional[str]
    query_time_ms: int

class PMPIntelligenceService:
    """Unified interface for PMP database queries."""

    def __init__(self, db_path: Path = None):
        """Auto-discover databases in ~/.maia/databases/intelligence/"""

    # Semantic query methods
    def get_systems_by_organization(self, org_pattern: str) -> PMPQueryResult
    def get_failed_patches(self, org_pattern: str = None, os_filter: str = None) -> PMPQueryResult
    def get_vulnerable_systems(self, severity: int = 3) -> PMPQueryResult
    def get_patch_deployment_status(self, patch_id: str) -> PMPQueryResult
    def get_data_freshness_report(self) -> Dict[str, datetime]

    # Low-level methods
    def query_raw(self, sql: str, database: str = "auto") -> PMPQueryResult
    def _normalize_timestamp(self, value: Any) -> str
    def _detect_best_database(self, query_type: str) -> str
```

**Gate**: P2 - Tests PASS (green)

---

### Phase 3: Query Templates for Agent Consumption
**Model**: Sonnet
**Deliverables**:
- [ ] `claude/tools/pmp/pmp_query_templates.py`

**Templates** (pre-built SQL + semantic wrappers):
```python
TEMPLATES = {
    "org_systems": {
        "description": "Get all systems for an organization/branch",
        "parameters": ["org_pattern"],
        "example": "get_systems_by_organization('GS1%')"
    },
    "failed_patches_windows": {
        "description": "Windows Server patches with deployment failures",
        "parameters": ["org_pattern"],
        "sql": "..."
    },
    "vulnerable_by_os": {
        "description": "Highly vulnerable systems grouped by OS",
        "parameters": ["severity_threshold"],
        "sql": "..."
    },
    "patch_compliance": {
        "description": "Compliance summary by organization",
        "parameters": ["org_pattern", "days_lookback"],
        "sql": "..."
    }
}
```

**Gate**: P3 - Template tests pass

---

### Phase 4: Agent Context Documentation
**Model**: Haiku (documentation)
**Deliverables**:
- [ ] Update `claude/agents/data_analyst_agent.md` with PMP intelligence service reference
- [ ] Add query examples to agent context
- [ ] Create `claude/context/knowledge/pmp/pmp_intelligence_quickstart.md`

**Content**:
```markdown
## PMP Intelligence Service (Quick Reference)

### Common Queries
```python
from claude.tools.pmp.pmp_intelligence_service import PMPIntelligenceService
pmp = PMPIntelligenceService()

# Get GS1 Windows servers with failed patches
result = pmp.get_failed_patches(org_pattern="GS1%", os_filter="Windows Server%")

# Check data freshness
freshness = pmp.get_data_freshness_report()
# {'pmp_config.db': '2026-01-15T10:30:00', 'pmp_systemreports.db': '2025-11-28T...'}
```
```

**Gate**: P4 - Documentation complete, agent context updated

---

### Phase 5: Integration Testing
**Model**: Sonnet
**Deliverables**:
- [ ] `tests/integration/test_pmp_intelligence_integration.py`
- [ ] Real database tests (not mocks)
- [ ] Performance benchmarks

**Tests**:
```python
def test_real_database_query_gs1_systems():
    """Query real pmp_config.db for GS1 systems."""

def test_cross_database_aggregation():
    """Combine data from multiple real databases."""

def test_query_performance_under_1_second():
    """All standard queries complete in <1s."""
```

**Gate**: P5 - Integration tests pass on real data

---

### Phase 6: Capability Registration
**Model**: Haiku
**Deliverables**:
- [ ] Register in `claude/data/databases/system/capabilities.db`
- [ ] Add to capability index

```sql
INSERT INTO capabilities (name, type, category, path, description, keywords)
VALUES (
    'pmp_intelligence_service',
    'tool',
    'pmp',
    'claude/tools/pmp/pmp_intelligence_service.py',
    'Unified PMP database query interface with semantic methods',
    'pmp,patch,manageengine,query,intelligence,unified'
);
```

**Gate**: P6 - Tool discoverable via `find_capability.py pmp`

---

### Phase 6.5: Completeness Review
**Model**: Sonnet
**Checklist**:
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Agent context includes new tool
- [ ] No TODO comments in code
- [ ] Capability registered
- [ ] No breaking changes to existing tools

---

## Model/Subagent Selection Summary

| Phase | Model | Rationale |
|-------|-------|-----------|
| P0 | Haiku | Fast capability search, low cost |
| P1 | Sonnet | Test design requires careful structure |
| P2 | Sonnet | Core implementation, moderate complexity |
| P3 | Sonnet | SQL template design |
| P4 | Haiku | Documentation, straightforward |
| P5 | Sonnet | Integration testing with real DBs |
| P6 | Haiku | Registration queries |
| P6.5 | Sonnet | Final review requires judgment |

---

## Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| Query simplification | 3 DBs → 1 call | Count DB connections per question |
| Code reduction | 50% fewer lines | Compare before/after query code |
| Response time | <1 second | Benchmark common queries |
| Data freshness visibility | Always shown | Staleness warning in all results |
| Agent adoption | Used in next PMP session | Track tool usage |

---

## Files to Create/Modify

| Action | Path |
|--------|------|
| CREATE | `claude/tools/pmp/pmp_intelligence_service.py` |
| CREATE | `claude/tools/pmp/pmp_query_templates.py` |
| CREATE | `tests/test_pmp_intelligence_service.py` |
| CREATE | `tests/integration/test_pmp_intelligence_integration.py` |
| CREATE | `claude/context/knowledge/pmp/pmp_intelligence_quickstart.md` |
| MODIFY | `claude/agents/data_analyst_agent.md` (add reference) |
| MODIFY | `capabilities.db` (register tool) |

---

## Risks & Mitigations

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Schema drift in source DBs | Medium | Add schema validation on init |
| Performance degradation with large datasets | Low | Add query result limits, pagination |
| Breaking existing PMP tools | Low | Service is additive, no modifications to existing |

---

## Approval Request

**Ready for implementation?**

- [ ] Approve plan as-is
- [ ] Request modifications
- [ ] Defer to future sprint
