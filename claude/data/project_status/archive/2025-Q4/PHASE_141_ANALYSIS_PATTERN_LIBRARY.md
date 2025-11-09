# Phase 141: Global Analysis Pattern Library

**Status**: PLANNING
**Priority**: HIGH
**Estimated Effort**: 8-10 hours
**Dependencies**: Phase 130 (ServiceDesk Ops Intelligence - proven SQLite + ChromaDB pattern)
**Created**: 2025-10-30
**Owner**: Data Analyst Agent + SRE Principal Engineer Agent (TDD pairing)

---

## Executive Summary

**Problem**: Analytical patterns (SQL queries, presentation formats, business context) are ephemeral and lost when conversations end. Each new analysis reinvents the wheel, wasting time and losing institutional knowledge.

**Solution**: Build a global Analysis Pattern Library that stores, indexes, and auto-suggests proven analytical approaches across all domains (ServiceDesk, recruitment, financial, etc.).

**Value Proposition**:
- **50% time reduction** on repeat analyses (pattern reuse vs reinvention)
- **Institutional knowledge** preserved across conversation resets
- **Pattern evolution** tracking (v1 → v2 as preferences improve)
- **Auto-suggestion** when similar questions detected (semantic search)
- **Cross-domain** reusability (works for all agents: Data Analyst, Financial Advisor, etc.)

**First Use Case**: ServiceDesk timesheet project breakdown pattern (person → projects → % of available hours with 7.6 hrs/day calculation)

---

## Business Case

### Current State Pain Points

1. **Pattern Amnesia** (High Impact)
   - Each conversation starts fresh, no memory of proven approaches
   - User must re-explain preferences ("show top 5 projects, then remaining")
   - Analysts reinvent SQL queries for common questions
   - **Time waste**: 10-20 min per repeat analysis

2. **No Pattern Discovery** (Medium Impact)
   - Can't search: "How did we analyze timesheets last time?"
   - No visibility into proven patterns across domains
   - New analysts can't leverage existing knowledge
   - **Knowledge loss**: High-value patterns disappear

3. **Manual Format Enforcement** (Low Impact)
   - Must manually specify: "use 7.6 hrs/day, show % of available"
   - Business context (sick/holiday caveat) not preserved
   - Presentation format inconsistencies
   - **Quality variance**: Ad-hoc vs standardized outputs

### Proposed Solution Benefits

**Immediate (Week 1)**:
- ✅ Save timesheet analysis pattern (validation)
- ✅ Auto-suggest when similar questions asked
- ✅ Consistent presentation format

**Short-term (Month 1)**:
- ✅ 10+ patterns saved (ServiceDesk, recruitment, financial)
- ✅ 50% time reduction on repeat analyses
- ✅ Pattern usage tracking (identify most valuable)

**Long-term (Quarter 1)**:
- ✅ 30+ patterns across all domains
- ✅ Institutional analytical memory
- ✅ Pattern evolution (v1 → v2 based on usage)
- ✅ New analyst onboarding asset

### ROI Calculation

**Implementation Cost**:
- 8 hours dev work × $150/hr = **$1,200**

**Annual Savings** (conservative):
- 2 repeat analyses/week × 10 min saved × 52 weeks = 17.3 hours
- 17.3 hours × $85/hr = **$1,470/year**

**Payback Period**: 0.8 months (immediate ROI)
**3-Year NPV**: $3,210 (267% ROI)

**Intangible Benefits**:
- Improved analysis quality (standardized approaches)
- Reduced cognitive load (no reinvention)
- Knowledge preservation (institutional memory)

---

## Technical Design

### Architecture Overview

**Components**:
1. **SQLite Database** - Structured pattern metadata (name, domain, SQL, format, usage)
2. **ChromaDB** - Semantic search for pattern discovery
3. **Python Library** - CRUD operations + auto-suggestion engine
4. **CLI Tool** - Save, search, list, delete patterns
5. **Agent Integration** - Data Analyst Agent uses patterns automatically

**Tech Stack** (proven from Phase 130):
- SQLite 3 (relational metadata)
- ChromaDB 0.4+ (semantic embeddings)
- sentence-transformers/all-MiniLM-L6-v2 (384-dim embeddings)
- Python 3.9+ (standard library)

### Database Schema

#### SQLite Tables

```sql
-- Core pattern metadata
CREATE TABLE analysis_patterns (
    pattern_id TEXT PRIMARY KEY,  -- e.g., 'timesheet_project_breakdown_v1'
    pattern_name TEXT NOT NULL,   -- Human-readable name
    domain TEXT NOT NULL,          -- 'servicedesk', 'recruitment', 'financial', etc.
    question_type TEXT NOT NULL,   -- 'timesheet_breakdown', 'roi_calculation', etc.
    description TEXT,              -- What this pattern does
    sql_template TEXT,             -- SQL with {{placeholders}}
    presentation_format TEXT,      -- Output structure description
    business_context TEXT,         -- Important caveats/assumptions
    example_input TEXT,            -- Sample question that triggers this
    example_output TEXT,           -- Sample result
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,               -- Agent or user who created
    version INTEGER DEFAULT 1,
    status TEXT DEFAULT 'active',  -- 'active', 'deprecated', 'archived'
    tags TEXT                      -- JSON array: ['timesheet', 'hours', 'projects']
);

-- Pattern usage tracking
CREATE TABLE pattern_usage (
    usage_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_id TEXT NOT NULL,
    used_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_question TEXT,            -- Original question that triggered pattern
    success BOOLEAN,               -- Did pattern work? (for quality tracking)
    feedback TEXT,                 -- Optional user feedback
    FOREIGN KEY (pattern_id) REFERENCES analysis_patterns(pattern_id)
);

-- Pattern evolution (versioning)
CREATE TABLE pattern_versions (
    version_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    changes TEXT,                  -- What changed from previous version
    previous_version_id TEXT,      -- Link to superseded pattern
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pattern_id) REFERENCES analysis_patterns(pattern_id)
);

-- Indexes for performance
CREATE INDEX idx_patterns_domain ON analysis_patterns(domain);
CREATE INDEX idx_patterns_question_type ON analysis_patterns(question_type);
CREATE INDEX idx_patterns_status ON analysis_patterns(status);
CREATE INDEX idx_usage_pattern ON pattern_usage(pattern_id);
CREATE INDEX idx_usage_date ON pattern_usage(used_date);
```

#### ChromaDB Collections

```python
# Collection: analysis_patterns_embeddings
{
    "collection_name": "analysis_patterns_embeddings",
    "metadata": {
        "description": "Semantic embeddings for pattern discovery",
        "embedding_model": "all-MiniLM-L6-v2",
        "dimension": 384
    },
    "documents": [
        # Each pattern stored as: description + example_input + tags
        "Timesheet project breakdown: analyze person's hours across projects with percentage of available time. Example: 'show me project hours for Olli and Alex'. Tags: timesheet, hours, projects, personnel"
    ],
    "metadatas": [
        {"pattern_id": "timesheet_project_breakdown_v1", "domain": "servicedesk"}
    ]
}
```

### API Design

```python
# analysis_pattern_library.py

class AnalysisPatternLibrary:
    """
    Global analysis pattern storage and retrieval system.

    Stores proven analytical approaches (SQL, presentation format, business context)
    for reuse across conversations and agents.
    """

    def __init__(self, db_path: str = "claude/data/analysis_patterns.db",
                 chromadb_path: str = "claude/data/rag_databases/analysis_patterns"):
        """Initialize SQLite + ChromaDB connections."""
        pass

    # Core CRUD operations
    def save_pattern(self,
                     pattern_name: str,
                     domain: str,
                     question_type: str,
                     description: str,
                     sql_template: str = None,
                     presentation_format: str = None,
                     business_context: str = None,
                     example_input: str = None,
                     example_output: str = None,
                     tags: list = None) -> str:
        """
        Save a new analysis pattern.

        Returns:
            pattern_id: Auto-generated ID (e.g., 'timesheet_project_breakdown_v1')
        """
        pass

    def get_pattern(self, pattern_id: str) -> dict:
        """Retrieve pattern by ID."""
        pass

    def update_pattern(self, pattern_id: str, **kwargs) -> bool:
        """Update existing pattern (creates new version)."""
        pass

    def delete_pattern(self, pattern_id: str) -> bool:
        """Soft delete (set status='archived')."""
        pass

    # Search and discovery
    def search_patterns(self, query: str,
                        domain: str = None,
                        limit: int = 5,
                        similarity_threshold: float = 0.75) -> list:
        """
        Semantic search for matching patterns.

        Args:
            query: User's question or description
            domain: Filter by domain (optional)
            limit: Max results
            similarity_threshold: Minimum similarity score (0-1)

        Returns:
            List of (pattern_dict, similarity_score) tuples
        """
        pass

    def list_patterns(self, domain: str = None,
                      question_type: str = None,
                      status: str = 'active') -> list:
        """List all patterns (optionally filtered)."""
        pass

    # Auto-suggestion
    def suggest_pattern(self, user_question: str,
                        domain: str = None,
                        auto_apply: bool = False) -> dict:
        """
        Auto-detect if user's question matches existing pattern.

        Args:
            user_question: "Show me project hours for Olli and Alex"
            domain: Optional domain hint
            auto_apply: If True, return ready-to-execute pattern

        Returns:
            {
                'matched': True/False,
                'pattern_id': 'timesheet_project_breakdown_v1',
                'confidence': 0.92,
                'pattern': {...},
                'sql_ready': "SELECT ... WHERE name IN ('Olli', 'Alex')"  # if auto_apply
            }
        """
        pass

    # Usage tracking
    def track_usage(self, pattern_id: str,
                    user_question: str,
                    success: bool = True,
                    feedback: str = None):
        """Log pattern usage for analytics."""
        pass

    def get_usage_stats(self, pattern_id: str = None) -> dict:
        """Get usage statistics (total uses, success rate, last used)."""
        pass

    # Pattern evolution
    def create_new_version(self, pattern_id: str,
                          changes: str,
                          **updated_fields) -> str:
        """
        Create new version of pattern (increments version number).

        Returns:
            new_pattern_id: e.g., 'timesheet_project_breakdown_v2'
        """
        pass

    def get_version_history(self, pattern_id: str) -> list:
        """Get all versions of a pattern."""
        pass
```

### CLI Tool

```bash
# Save new pattern
python3 claude/tools/analysis_pattern_library.py save \
    --name "Timesheet Project Breakdown" \
    --domain servicedesk \
    --question-type timesheet_breakdown \
    --description "Analyze person's hours across projects with % of available time" \
    --sql-file timesheet_breakdown.sql \
    --format "Top 5 projects + remaining + unaccounted with % of available hours" \
    --context "Use 7.6 hrs/day, note that sick/holidays not in timesheets" \
    --tags "timesheet,hours,projects,personnel"

# Search for patterns
python3 claude/tools/analysis_pattern_library.py search "project hours for employees"

# List all patterns
python3 claude/tools/analysis_pattern_library.py list --domain servicedesk

# Show pattern details
python3 claude/tools/analysis_pattern_library.py show timesheet_project_breakdown_v1

# Usage statistics
python3 claude/tools/analysis_pattern_library.py stats --top 10

# Delete pattern
python3 claude/tools/analysis_pattern_library.py delete timesheet_project_breakdown_v1
```

---

## Implementation Plan

### Phase 1: Core Infrastructure (2 hours)

**Deliverables**:
- ✅ SQLite schema creation (3 tables + indexes)
- ✅ ChromaDB collection initialization
- ✅ Basic CRUD operations (save, get, update, delete)
- ✅ Database migrations script

**Tests**:
- Create pattern → retrieve → verify all fields
- Update pattern → new version created
- Delete pattern → status='archived'
- Database constraints enforced (unique pattern_id, foreign keys)

**Success Criteria**:
- Can save timesheet pattern with all metadata
- Can retrieve pattern by ID
- Versioning works (v1 → v2)

---

### Phase 2: Semantic Search (2 hours)

**Deliverables**:
- ✅ ChromaDB embedding generation
- ✅ Semantic search implementation
- ✅ Similarity scoring (0-1 scale)
- ✅ Domain filtering

**Tests**:
- Search "project hours" → matches timesheet pattern (>0.75 similarity)
- Search "recruitment pipeline" → no match for timesheet pattern
- Domain filter works (servicedesk vs recruitment)
- Top-5 ranking correct

**Success Criteria**:
- Semantic search finds timesheet pattern with >0.80 similarity
- Search time <200ms (ChromaDB optimized)
- False positive rate <10%

---

### Phase 3: Auto-Suggestion Engine (2 hours)

**Deliverables**:
- ✅ Pattern matching from user questions
- ✅ Confidence scoring (0-1)
- ✅ SQL template variable substitution
- ✅ Auto-apply mode (ready-to-execute SQL)

**Tests**:
- Question "show hours for Olli" → suggests timesheet pattern (0.85+ confidence)
- Auto-apply extracts names: Olli → WHERE name ILIKE '%olli%'
- Low confidence (<0.70) → no suggestion
- Multiple matches → ranked by confidence

**Success Criteria**:
- 90%+ accuracy on known questions
- SQL substitution works for 5 test cases
- <500ms suggestion latency

---

### Phase 4: Agent Integration (2 hours)

**Deliverables**:
- ✅ Data Analyst Agent integration
- ✅ Pattern suggestion in agent workflow
- ✅ Usage tracking automatic
- ✅ Feedback loop (success/failure tracking)

**Integration Points**:
```python
# In Data Analyst Agent workflow
def analyze_data(user_question: str):
    # Check for existing pattern
    pattern_lib = AnalysisPatternLibrary()
    suggestion = pattern_lib.suggest_pattern(user_question, domain='servicedesk')

    if suggestion['matched'] and suggestion['confidence'] > 0.80:
        print(f"Found matching pattern: {suggestion['pattern_id']} (confidence: {suggestion['confidence']})")
        # Use pattern
        result = execute_with_pattern(suggestion['pattern'], user_question)
        pattern_lib.track_usage(suggestion['pattern_id'], user_question, success=True)
    else:
        # Perform ad-hoc analysis
        result = perform_new_analysis(user_question)
```

**Tests**:
- Agent receives timesheet question → auto-suggests pattern
- Usage tracked in database
- Success/failure logged
- Agent can create new pattern from successful ad-hoc analysis

**Success Criteria**:
- Data Analyst Agent successfully uses timesheet pattern
- Usage count increments
- End-to-end workflow <5s total latency

---

### Phase 5: CLI + Documentation (1 hour)

**Deliverables**:
- ✅ CLI tool (save, search, list, show, stats, delete)
- ✅ User documentation (README)
- ✅ Developer documentation (API reference)
- ✅ Example patterns (timesheet, recruitment, financial)

**Documentation Sections**:
1. Quick Start (5-minute tutorial)
2. Pattern Creation Guide
3. Search Best Practices
4. Agent Integration Examples
5. Troubleshooting

**Success Criteria**:
- User can save pattern via CLI in <2 minutes
- Documentation covers all use cases
- 3 example patterns ready to import

---

### Phase 6: Testing + Validation (1 hour)

**Test Coverage**:
- ✅ Unit tests (15 tests): CRUD, search, auto-suggest
- ✅ Integration tests (8 tests): Agent workflow, ChromaDB, SQLite
- ✅ Performance tests (3 tests): Search latency, bulk insert, large dataset
- ✅ Edge cases (5 tests): Empty DB, duplicate patterns, invalid SQL

**Validation Scenarios**:
1. Save timesheet pattern → search "project hours" → auto-suggest works
2. Create 10 patterns → search performance <200ms
3. Agent uses pattern 5 times → usage stats accurate
4. Update pattern → new version created, old version archived
5. Delete pattern → soft delete (status='archived'), not hard delete

**Success Criteria**:
- 95%+ test pass rate
- All performance SLAs met (<200ms search, <500ms suggestion)
- Zero critical bugs

---

## Success Metrics

### Immediate (Week 1)

**Technical**:
- ✅ Timesheet pattern saved and retrievable
- ✅ Search works (>0.80 similarity for known questions)
- ✅ Auto-suggestion latency <500ms
- ✅ All tests passing (95%+)

**Business**:
- ✅ Pattern reused in 2nd timesheet analysis (validates concept)
- ✅ 50% time reduction measured (10 min → 5 min)

### Short-term (Month 1)

**Adoption**:
- ✅ 10+ patterns saved across domains (ServiceDesk, recruitment, financial)
- ✅ 20+ pattern uses logged
- ✅ 3+ users creating patterns

**Quality**:
- ✅ 90%+ search accuracy (user finds desired pattern)
- ✅ 85%+ success rate (pattern works as expected)
- ✅ <5% false positive rate

### Long-term (Quarter 1)

**Scale**:
- ✅ 30+ patterns in library
- ✅ 100+ pattern uses
- ✅ 5+ domains covered

**Impact**:
- ✅ 50% average time reduction on repeat analyses
- ✅ Pattern library referenced in onboarding docs
- ✅ Pattern evolution (3+ patterns on v2+)

---

## Risk Analysis

### Technical Risks

**Risk 1: ChromaDB Performance Degradation** (Medium probability, Medium impact)
- **Scenario**: Search latency >500ms with 100+ patterns
- **Mitigation**: Benchmark at 50, 100, 500 patterns; implement caching if needed
- **Contingency**: Fallback to SQLite full-text search (less semantic, but faster)

**Risk 2: SQL Template Substitution Edge Cases** (High probability, Low impact)
- **Scenario**: User question "show hours for Olli, Alex, and Bob" → substitution fails
- **Mitigation**: Robust NLP for name extraction; clear error messages
- **Contingency**: Manual SQL editing mode (user adjusts template)

**Risk 3: Pattern Namespace Collision** (Low probability, High impact)
- **Scenario**: Two patterns with same name/domain create conflicts
- **Mitigation**: Enforce unique pattern_id generation (domain + question_type + timestamp)
- **Contingency**: Manual conflict resolution UI in CLI

### Business Risks

**Risk 4: Low Adoption** (Medium probability, High impact)
- **Scenario**: Users prefer ad-hoc analysis, don't save patterns
- **Mitigation**: Make saving patterns 1-click in agent workflow
- **Contingency**: Auto-save successful analyses as patterns (opt-out vs opt-in)

**Risk 5: Pattern Staleness** (High probability, Medium impact)
- **Scenario**: Database schema changes break old SQL patterns
- **Mitigation**: Version tracking, schema change alerts, pattern validation on use
- **Contingency**: Pattern deprecation workflow (mark deprecated, suggest alternatives)

---

## Rollback Plan

**If system proves not valuable after 1 month:**

1. **Export patterns to JSON** (simple file format)
2. **Archive database** (preserve data, disable auto-suggestion)
3. **Remove agent integration** (back to ad-hoc analysis)
4. **Total cost**: 8 hours sunk, minimal ongoing maintenance

**No data loss** - patterns preserved in JSON for future use

---

## Dependencies

**External**:
- ✅ SQLite 3 (already installed)
- ✅ ChromaDB 0.4+ (already used in Phase 130)
- ✅ sentence-transformers (already installed)

**Internal**:
- ✅ Phase 130 (ServiceDesk Ops Intelligence) - proven SQLite + ChromaDB pattern
- ✅ Data Analyst Agent - integration target
- ⚠️ Agent session persistence (Phase 134) - nice-to-have for pattern suggestions

---

## Open Questions

1. **Auto-save behavior**: Should successful ad-hoc analyses auto-save as patterns? (Opt-in vs opt-out)
2. **Pattern sharing**: Multi-user environment - who can edit/delete patterns? (Single-user Maia system, low priority)
3. **Pattern categories**: Should we have "public" vs "private" patterns? (Not needed for single-user)
4. **Embedding model**: all-MiniLM-L6-v2 vs larger model? (Start small, upgrade if accuracy issues)

---

## First Pattern to Save

**Timesheet Project Breakdown Pattern** (validates system immediately)

```json
{
    "pattern_id": "timesheet_project_breakdown_v1",
    "pattern_name": "Timesheet Project Breakdown",
    "domain": "servicedesk",
    "question_type": "timesheet_breakdown",
    "description": "Analyze individual's hours across projects with percentage of available working hours (accounting for unrecorded sick/holiday time)",
    "sql_template": "SELECT \"TS-User Full Name\", \"TS-Ticket Project Master Code\" as project_code, \"TS-Title\" as project_title, COUNT(*) as timesheet_entries, SUM(\"TS-Hours\") as total_hours FROM servicedesk.timesheets WHERE \"TS-User Full Name\" IN ({{names}}) GROUP BY \"TS-User Full Name\", \"TS-Ticket Project Master Code\", \"TS-Title\" ORDER BY \"TS-User Full Name\", total_hours DESC;",
    "presentation_format": "Top 5 projects with hours and % of available time, remaining projects summary, unaccounted hours (49-76% typically due to unreported leave)",
    "business_context": "Use 7.6 hours/day as standard working hours. Sick leave and holidays are NOT recorded in timesheets, so unaccounted hours are expected. Show as 'available hours' not 'expected hours' to avoid confusion.",
    "example_input": "Show me project hours for Olli Ojala and Alex Olver",
    "example_output": "Alex Olver - 287.06 hours total (51% of available 562.4 hrs): Top 5 projects (Zenitas 108.20hrs/19.2%, NWR 64hrs/11.4%, ...), Unaccounted 275.34 hrs (49%)",
    "tags": ["timesheet", "hours", "projects", "personnel", "utilization"]
}
```

---

## Approval & Next Steps

**Decision Required**:
- ✅ Approve Phase 141 implementation
- ✅ Proceed with TDD methodology (Domain Specialist + SRE pairing)
- ✅ Estimated timeline: 8-10 hours over 1-2 days

**Once approved**:
1. Create TDD requirements document
2. Pair Domain Specialist (Data Analyst) + SRE Principal Engineer
3. Execute Phases 1-6 with full test coverage
4. Validate with timesheet pattern reuse
5. Document in SYSTEM_STATE.md

**Status**: READY FOR APPROVAL
