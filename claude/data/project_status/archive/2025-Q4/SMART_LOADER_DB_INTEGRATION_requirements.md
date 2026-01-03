# Smart Loader Database Integration - Requirements Specification

**Project**: Phase 165 - Integrate SYSTEM_STATE Database with Smart Context Loader
**Agent**: SRE Principal Engineer Agent
**Methodology**: Test-Driven Development (TDD)
**Date**: 2025-11-21
**Status**: Requirements Phase

---

## 1. Problem Statement

### Current State (Functional but Slow)

**Smart Context Loader** (Phase 2):
- **Method**: Parse 2.1 MB SYSTEM_STATE.md markdown file
- **Performance**: 100-500ms per query (markdown parsing overhead)
- **Token Efficiency**: 85% reduction (5-20K tokens vs 42K full file)
- **Reliability**: ✅ Works well, but slow
- **Limitation**: No memory of structured data (problems, solutions, metrics)

### Desired State (Fast + Better Memory)

**Database-Enhanced Smart Loader**:
- **Primary Path**: Query SQLite database (<20ms)
- **Fallback Path**: Parse markdown if DB unavailable (graceful degradation)
- **Memory Improvement**: Access structured data (problems by category, metrics, files created)
- **Performance Target**: 5-20ms DB query (10-100x faster than markdown)
- **Reliability**: Same or better than current (no regressions)

---

## 2. Requirements

### FR-1: Database Query Interface

**Requirement**: Create query functions for smart loader use cases

**Query Functions Needed**:

1. **get_recent_phases(count: int)** → List[Dict]
   - Returns last N phases with full context
   - Use case: "What happened in recent phases?"
   - SQL: `SELECT * FROM v_recent_phases LIMIT ?`

2. **get_phases_by_keyword(keyword: str)** → List[Dict]
   - Search narrative_text for keyword
   - Use case: "Show phases mentioning ChromaDB"
   - SQL: `SELECT * FROM phases WHERE narrative_text LIKE ?`

3. **get_phases_by_number(phase_numbers: List[int])** → List[Dict]
   - Retrieve specific phases
   - Use case: Smart loader requests Phases 2, 107, 134
   - SQL: `SELECT * FROM phases WHERE phase_number IN (?)`

4. **get_phase_with_context(phase_number: int)** → Dict
   - Get phase with all related data (problems, solutions, metrics, files)
   - Use case: Deep dive into specific phase
   - SQL: JOIN across all tables

5. **search_problems_by_category(category: str)** → List[Dict]
   - Find phases that solved specific problem types
   - Use case: "Show me all SQL injection fixes"
   - SQL: `SELECT * FROM problems WHERE problem_category LIKE ?`

**Acceptance Criteria**:
- ✅ All query functions return correct data types
- ✅ Performance: All queries complete in <20ms
- ✅ Error handling: Graceful failures with clear messages
- ✅ Type hints: Full Python type annotations

---

### FR-2: Smart Loader Integration

**Requirement**: Integrate database queries into existing smart_context_loader.py

**Integration Strategy**:

```python
class SmartContextLoader:
    def __init__(self):
        self.db_path = Path("claude/data/databases/system/system_state.db")
        self.markdown_path = Path("SYSTEM_STATE.md")

    def load_for_intent(self, query: str) -> str:
        """Load relevant context based on query intent"""

        # Try database first (if available)
        if self.db_path.exists():
            try:
                phases = self._query_database_for_intent(query)
                if phases:
                    return self._format_phases_from_db(phases)
            except Exception as e:
                logger.warning(f"DB query failed, falling back to markdown: {e}")

        # Fall back to markdown parsing
        return self._parse_markdown_for_intent(query)

    def _query_database_for_intent(self, query: str) -> List[Dict]:
        """Route query to appropriate DB query based on intent"""
        # Intent detection logic (reuse existing logic)
        # Call appropriate query function
        pass

    def _format_phases_from_db(self, phases: List[Dict]) -> str:
        """Format database results as markdown for context"""
        # Convert DB records to markdown format
        # Preserve same format as current markdown parsing
        pass
```

**Key Design Decisions**:
1. **Database is optional** - Fallback to markdown if missing/corrupt
2. **Preserve existing behavior** - Same output format, same token counts
3. **Reuse intent detection** - Don't rewrite existing routing logic
4. **Structured data bonus** - Access problems/metrics when helpful

**Acceptance Criteria**:
- ✅ DB query path works when database available
- ✅ Markdown fallback works when database unavailable
- ✅ Same quality context returned (or better)
- ✅ No breaking changes to existing smart loader API

---

### FR-3: Performance Benchmarking

**Requirement**: Measure actual performance improvement

**Benchmarks Needed**:

1. **Query Latency**:
   - Measure: DB query time vs markdown parse time
   - Queries: Recent phases, keyword search, specific phase numbers
   - Target: DB 10-100x faster than markdown

2. **Memory Usage**:
   - Measure: Peak memory during query
   - Compare: DB connection vs markdown file read
   - Target: No significant increase

3. **Token Efficiency**:
   - Measure: Tokens in returned context
   - Compare: DB vs markdown results
   - Target: Same or better (no regression)

**Benchmark Script**:
```python
# benchmark_smart_loader.py
def benchmark_query(query: str, iterations: int = 100):
    """Benchmark DB vs markdown for same query"""

    # Warm up
    loader.load_for_intent(query)

    # Benchmark DB path
    db_times = []
    for _ in range(iterations):
        start = time.perf_counter()
        loader._query_database_for_intent(query)
        db_times.append(time.perf_counter() - start)

    # Benchmark markdown path
    md_times = []
    for _ in range(iterations):
        start = time.perf_counter()
        loader._parse_markdown_for_intent(query)
        md_times.append(time.perf_counter() - start)

    # Report
    print(f"DB: {mean(db_times)*1000:.2f}ms ± {stdev(db_times)*1000:.2f}ms")
    print(f"MD: {mean(md_times)*1000:.2f}ms ± {stdev(md_times)*1000:.2f}ms")
    print(f"Speedup: {mean(md_times)/mean(db_times):.1f}x")
```

**Acceptance Criteria**:
- ✅ DB queries 10-100x faster than markdown
- ✅ Memory usage acceptable (<10 MB increase)
- ✅ Token counts same or better

---

### FR-4: Better Memory (Structured Data Access)

**Requirement**: Leverage database structure for improved context

**Memory Improvements**:

1. **Problem Pattern Recognition**:
   - Query: "Have we solved this problem before?"
   - DB: `SELECT * FROM problems WHERE problem_category = ?`
   - Benefit: Maia can say "Yes, we fixed SQL injection in Phases 103, 134"

2. **Metric History**:
   - Query: "What's our total time savings?"
   - DB: `SELECT SUM(value) FROM metrics WHERE metric_name = 'time_savings_hours'`
   - Benefit: Maia can provide aggregate stats

3. **File Tracking**:
   - Query: "What agents have we built?"
   - DB: `SELECT * FROM files_created WHERE file_type = 'agent'`
   - Benefit: Maia knows what tools exist

4. **Technology Timeline**:
   - Query: "When did we start using ChromaDB?"
   - DB: `SELECT MIN(phase_number) FROM phases WHERE narrative_text LIKE '%ChromaDB%'`
   - Benefit: Maia can trace technology adoption

**Acceptance Criteria**:
- ✅ Structured queries work correctly
- ✅ Results enhance Maia's responses
- ✅ Graceful fallback if data missing

---

## 3. Non-Functional Requirements

### NFR-1: Performance

- **DB Query Latency**: <20ms per query (p95)
- **Markdown Fallback**: No slower than current (100-500ms)
- **Memory Overhead**: <10 MB increase from DB connection
- **Database Size**: <10 MB for current 10 phases

### NFR-2: Reliability

- **Graceful Degradation**: Fall back to markdown if DB unavailable
- **Error Handling**: Clear error messages, no silent failures
- **Transaction Safety**: Read-only queries (no corruption risk)
- **Database Lock**: Handle concurrent reads safely

### NFR-3: Maintainability

- **API Compatibility**: No breaking changes to smart loader interface
- **Code Quality**: Type hints, docstrings, clear naming
- **Testing**: ≥90% code coverage
- **Documentation**: Usage examples, integration guide

### NFR-4: Observability

- **Logging**: Log DB vs markdown path selection
- **Metrics**: Track query latency, cache hits, errors
- **Debugging**: Clear debug output when enabled

---

## 4. Test Plan

### Unit Tests

1. **Query Function Tests**:
   - ✅ get_recent_phases returns correct phases
   - ✅ get_phases_by_keyword finds matching phases
   - ✅ get_phases_by_number returns requested phases
   - ✅ get_phase_with_context includes all related data
   - ✅ Error handling (database missing, corrupt, empty results)

2. **Integration Tests**:
   - ✅ Smart loader uses DB when available
   - ✅ Smart loader falls back to markdown when DB missing
   - ✅ Same output format from both paths
   - ✅ Intent routing works correctly

3. **Performance Tests**:
   - ✅ DB queries complete in <20ms
   - ✅ Markdown fallback works at normal speed
   - ✅ Memory usage acceptable

### Integration Tests

1. **End-to-End Tests**:
   - ✅ Load smart loader with DB → correct context
   - ✅ Load smart loader without DB → correct context (fallback)
   - ✅ Simulate DB corruption → graceful fallback

2. **Real-World Queries**:
   - ✅ "Show recent phases" → last 20 phases
   - ✅ "Find ChromaDB phases" → Phases 10, 156
   - ✅ "SQL injection fixes" → Phases 103, 134
   - ✅ "Total time savings" → aggregated metric

### Validation Tests

1. **Output Consistency**:
   - ✅ DB path and markdown path return same content
   - ✅ Token counts within 5% of each other
   - ✅ No missing information in DB path

2. **Performance Benchmarks**:
   - ✅ Run benchmark script on test queries
   - ✅ Verify 10-100x speedup
   - ✅ Document actual performance gains

---

## 5. Deliverables

### Phase 165 (Smart Loader Integration):

1. **Query Interface** (`claude/tools/sre/system_state_queries.py`):
   - Query functions (get_recent_phases, get_phases_by_keyword, etc.)
   - Type hints and docstrings
   - Error handling

2. **Enhanced Smart Loader** (`claude/tools/sre/smart_context_loader.py`):
   - Database query path
   - Markdown fallback path
   - Intent routing to appropriate queries
   - Format conversion (DB → markdown)

3. **Test Suite** (`claude/tools/sre/test_smart_loader_db.py`):
   - Unit tests for query functions
   - Integration tests for smart loader
   - Performance benchmarks

4. **Benchmark Tool** (`claude/tools/sre/benchmark_smart_loader.py`):
   - Query latency measurement
   - Memory usage tracking
   - Token count comparison

5. **Documentation**:
   - Updated smart_context_loading.md
   - Performance benchmark results
   - Integration guide

---

## 6. Success Criteria

**Phase 165 Complete When**:

- ✅ Query interface works with test database (10 phases)
- ✅ Smart loader integrates DB queries successfully
- ✅ Markdown fallback working (graceful degradation)
- ✅ All automated tests passing (≥90% coverage)
- ✅ Performance benchmark shows 10-100x speedup
- ✅ No regressions in smart loader behavior
- ✅ Documentation complete

**Long-Term Success** (Phase 166+):

- ✅ Backfill all 163 phases (if benchmark shows value)
- ✅ Smart loader using DB as primary source
- ✅ Maia responds faster (5-20ms context loading)
- ✅ Maia has better memory (structured data access)

---

## 7. Risk Assessment

### Technical Risks

1. **Database Performance** (LOW):
   - Risk: SQLite slower than expected for full-text search
   - Mitigation: Benchmark early, optimize indexes if needed

2. **Output Format Mismatch** (MEDIUM):
   - Risk: DB output doesn't match markdown format exactly
   - Mitigation: Extensive testing, format conversion layer

3. **Regression Risk** (LOW):
   - Risk: Breaking existing smart loader behavior
   - Mitigation: Comprehensive tests, fallback path always works

### Process Risks

1. **Scope Creep** (LOW):
   - Risk: Adding too many query functions beyond MVP
   - Mitigation: Focus on smart loader integration only, defer analytics

2. **Over-Engineering** (MEDIUM):
   - Risk: Building complex query interface not needed for Maia
   - Mitigation: Build only what smart loader needs, validate value

---

## 8. Design Decisions

### Decision 1: Database is Optional

**Choice**: Make database optional with graceful fallback

**Rationale**:
- Reliability: System still works if DB missing/corrupt
- Migration: Can deploy incrementally
- Testing: Easy to test both paths

**Alternative Rejected**: Require database (breaks existing workflows)

### Decision 2: Preserve Output Format

**Choice**: DB query results formatted as markdown (same as current)

**Rationale**:
- Compatibility: No changes to downstream consumers
- Testing: Easy to validate (compare output strings)
- Simplicity: Reuse existing formatting logic

**Alternative Rejected**: New structured format (breaking change)

### Decision 3: Reuse Intent Detection

**Choice**: Keep existing intent routing logic, just change data source

**Rationale**:
- Proven: Existing logic works well (85% token reduction)
- Low risk: Only changing data retrieval, not routing
- Fast: Minimal code changes

**Alternative Rejected**: Rewrite intent detection (unnecessary risk)

---

## 9. Approval

**Requirements Approved By**: User (SRE Principal Engineer Agent executing)
**Date**: 2025-11-21
**User Goal**: "Make Maia have better memory and faster if possible"
**Next Step**: Design query interface + write tests (TDD approach)

---

**Agent Notes**:
- Following TDD: Tests before implementation
- SRE focus: Performance benchmarking, graceful degradation, observability
- User-centric: "Better memory and faster" = structured data + <20ms queries
- Validation-first: Benchmark to prove value before backfill investment
