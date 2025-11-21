# SYSTEM_STATE Hybrid Database - Requirements Specification

**Project**: Phase 164 - SYSTEM_STATE.md Migration to Hybrid SQLite Database
**Agent**: SRE Principal Engineer Agent
**Methodology**: Test-Driven Development (TDD)
**Date**: 2025-11-21
**Status**: Requirements Phase

---

## 1. Problem Statement

### Current State (Inefficient)

**SYSTEM_STATE.md** stores 163 phases of Maia development history:
- **Size**: 2.1 MB, 44,865 lines, 208 phase entries
- **Format**: Markdown narrative (human-readable, machine-unfriendly)
- **Query Method**: Smart loader with keyword matching (Phase 2)
- **Limitations**:
  - No structured queries ("total time savings across all phases")
  - No pattern analysis ("all phases with SQL injection fixes")
  - No metric aggregation ("average phase completion time")
  - 10,330 chars/phase (verbose, ~30% markdown overhead)
  - Archive tool broken since Phase 87 (format drift)

### Desired State (Efficient)

**Hybrid Architecture**:
- **SQLite Database**: Structured data (metrics, problems, solutions, files)
- **Markdown Narrative**: Full context preserved (generated from DB or kept as reference)
- **Query Interface**: SQL for structured queries + keyword search for narrative
- **Smart Loader**: Query DB first (milliseconds), fall back to markdown if needed
- **ETL Pipeline**: Markdown → Database on each save state
- **Single Source of Truth**: Database (can regenerate markdown)

---

## 2. Requirements

### FR-1: Database Schema Design

**Requirement**: Design normalized SQLite schema capturing phase information

**Tables**:

1. **phases** (core phase metadata):
   - `id` INTEGER PRIMARY KEY
   - `phase_number` INTEGER UNIQUE NOT NULL
   - `title` TEXT NOT NULL
   - `date` TEXT NOT NULL (ISO 8601: YYYY-MM-DD)
   - `status` TEXT (e.g., "PRODUCTION READY", "COMPLETE", "IN PROGRESS")
   - `achievement` TEXT (brief summary)
   - `agent_team` TEXT (comma-separated agent names)
   - `git_commits` TEXT (comma-separated commit hashes)
   - `narrative_text` TEXT (full markdown content for this phase)
   - `created_at` TEXT DEFAULT CURRENT_TIMESTAMP

2. **problems** (problems solved in each phase):
   - `id` INTEGER PRIMARY KEY
   - `phase_id` INTEGER NOT NULL FOREIGN KEY → phases(id)
   - `problem_category` TEXT (e.g., "SQL injection", "performance", "reliability")
   - `before_state` TEXT (description of problem before fix)
   - `root_cause` TEXT (why did this happen?)

3. **solutions** (how problems were solved):
   - `id` INTEGER PRIMARY KEY
   - `phase_id` INTEGER NOT NULL FOREIGN KEY → phases(id)
   - `solution_category` TEXT (e.g., "architecture", "refactor", "tooling")
   - `after_state` TEXT (description after fix)
   - `architecture` TEXT (architectural approach)
   - `implementation_approach` TEXT (how it was built)

4. **metrics** (quantitative measurements):
   - `id` INTEGER PRIMARY KEY
   - `phase_id` INTEGER NOT NULL FOREIGN KEY → phases(id)
   - `metric_name` TEXT (e.g., "time_savings_hours", "performance_improvement_percent")
   - `value` REAL NOT NULL
   - `unit` TEXT (e.g., "hours", "percent", "seconds")
   - `baseline` TEXT (what was it before?)
   - `target` TEXT (what was the goal?)

5. **files_created** (deliverables from each phase):
   - `id` INTEGER PRIMARY KEY
   - `phase_id` INTEGER NOT NULL FOREIGN KEY → phases(id)
   - `file_path` TEXT NOT NULL
   - `file_type` TEXT (e.g., "tool", "agent", "database", "documentation")
   - `purpose` TEXT (what does this file do?)
   - `status` TEXT (e.g., "production", "deprecated", "experimental")

6. **tags** (categorization for pattern analysis):
   - `id` INTEGER PRIMARY KEY
   - `phase_id` INTEGER NOT NULL FOREIGN KEY → phases(id)
   - `tag` TEXT NOT NULL (e.g., "security", "performance", "TDD", "agent-enhancement")

**Acceptance Criteria**:
- ✅ Schema supports all information in current SYSTEM_STATE.md
- ✅ Foreign key constraints enforced (PRAGMA foreign_keys = ON)
- ✅ Indexes on frequently queried columns (phase_number, date, metric_name)
- ✅ No data loss from markdown → database conversion

---

### FR-2: ETL (Extract, Transform, Load)

**Requirement**: Parse SYSTEM_STATE.md and populate database

**ETL Pipeline**:

1. **Extract**: Read SYSTEM_STATE.md, split into phases
2. **Transform**: Parse each phase section:
   - Extract phase number, title, date, status from header
   - Parse "Achievement" section → phases.achievement
   - Parse "Problem Solved" → problems table
   - Parse "Implementation Details" → solutions table
   - Parse "Metrics" → metrics table
   - Parse "Files Created" → files_created table
   - Extract agent team, git commits
   - Store full markdown as narrative_text
3. **Load**: Insert into database with transaction safety

**Parsing Strategy**:
- Regex patterns for phase headers (handle emoji variations)
- Section markers (### Achievement, ### Problem Solved, etc.)
- Bullet point parsing for lists
- Metric extraction (parse "X hours → Y hours" patterns)

**Acceptance Criteria**:
- ✅ Parse all 163 existing phases without errors
- ✅ Extract 100% of phase numbers, titles, dates
- ✅ Extract ≥90% of metrics (some phases lack formal metrics)
- ✅ Transaction safety (rollback on any error)
- ✅ Idempotent (can re-run without duplicates)
- ✅ Progress reporting (show parsing status)
- ✅ Validation report (missing data, parse errors)

---

### FR-3: Query Interface

**Requirement**: Provide SQL query functions for common use cases

**Query Functions**:

1. **Pattern Analysis**:
   ```python
   get_phases_by_problem_category(category: str) -> List[Phase]
   # Example: get_phases_by_problem_category("SQL injection")
   ```

2. **Metric Aggregation**:
   ```python
   aggregate_metric(metric_name: str, operation: str) -> float
   # Example: aggregate_metric("time_savings_hours", "SUM")
   # Returns: 2847.5
   ```

3. **Technology Timeline**:
   ```python
   search_narrative(keyword: str) -> List[Phase]
   # Example: search_narrative("ChromaDB")
   # Returns phases that mention ChromaDB with context
   ```

4. **Recent Activity**:
   ```python
   get_recent_phases(count: int = 20) -> List[Phase]
   # Example: get_recent_phases(20)
   ```

5. **File Tracking**:
   ```python
   get_files_by_type(file_type: str) -> List[File]
   # Example: get_files_by_type("agent")
   # Returns all agents created across all phases
   ```

**Acceptance Criteria**:
- ✅ All query functions return correct results
- ✅ Performance: Queries complete in <100ms for 163 phases
- ✅ Type safety: Proper Python type hints
- ✅ Error handling: Graceful failures with clear messages

---

### FR-4: Integration with Smart Loader

**Requirement**: Update smart context loader to query database

**Integration Points**:

1. **Smart Loader Enhancement**:
   - Check if database exists
   - Query database for relevant phases (fast path)
   - Fall back to markdown parsing if DB unavailable
   - Cache DB connection for performance

2. **Backward Compatibility**:
   - Existing markdown-based queries still work
   - Gradual migration (DB optional initially)
   - Fallback to markdown if DB query fails

**Acceptance Criteria**:
- ✅ Smart loader queries DB first (when available)
- ✅ Falls back to markdown if DB missing/corrupt
- ✅ Performance improvement: 5-20ms DB query vs 100-500ms markdown parse
- ✅ No breaking changes to existing workflows

---

### FR-5: Reporting and Analytics

**Requirement**: Generate reports from structured data

**Report Types**:

1. **ROI Dashboard**:
   - Total time savings across all phases
   - Average phase completion time
   - Phases by status (production ready vs in progress)

2. **Pattern Analysis**:
   - Most common problem categories
   - Technology adoption timeline
   - Agent productivity (phases per agent)

3. **Quality Metrics**:
   - Phases with automated tests
   - Code quality scores over time
   - Documentation completeness

**Acceptance Criteria**:
- ✅ Generate markdown reports from DB
- ✅ Export CSV for external analysis
- ✅ SQL queries for custom reporting

---

## 3. Non-Functional Requirements

### NFR-1: Performance

- **ETL Performance**: Parse and load all 163 phases in <30 seconds
- **Query Performance**: All queries complete in <100ms
- **Database Size**: <10 MB for 163 phases (vs 2.1 MB markdown)

### NFR-2: Reliability

- **Transaction Safety**: All writes wrapped in transactions
- **Foreign Key Integrity**: PRAGMA foreign_keys = ON
- **Error Handling**: Clear error messages, no silent failures
- **Validation**: Detect and report parsing errors

### NFR-3: Maintainability

- **Schema Evolution**: Support schema migrations as phase format evolves
- **Documentation**: Comprehensive README with usage examples
- **Testing**: ≥90% code coverage with automated tests
- **Logging**: Comprehensive logging for debugging

### NFR-4: Usability

- **CLI Interface**: Simple command-line usage
- **Progress Reporting**: Show ETL progress (% complete)
- **Validation Reports**: Clear summary of what was extracted
- **Query Examples**: Document common query patterns

---

## 4. Test Plan

### Unit Tests

1. **Schema Tests**:
   - ✅ Foreign key constraints enforced
   - ✅ UNIQUE constraints prevent duplicates
   - ✅ NOT NULL constraints validated
   - ✅ Indexes created correctly

2. **Parser Tests**:
   - ✅ Extract phase number from header variations
   - ✅ Parse date in multiple formats
   - ✅ Extract metrics from various formats
   - ✅ Handle missing sections gracefully

3. **Query Tests**:
   - ✅ Pattern analysis returns correct phases
   - ✅ Metric aggregation calculates correctly
   - ✅ Search finds relevant phases
   - ✅ Edge cases handled (empty results, invalid input)

### Integration Tests

1. **ETL Pipeline**:
   - ✅ Parse last 20 phases (Phases 144-163) successfully
   - ✅ Validate extracted data matches markdown
   - ✅ Transaction rollback on error

2. **Smart Loader Integration**:
   - ✅ Smart loader queries DB successfully
   - ✅ Falls back to markdown when needed
   - ✅ Performance improvement measured

### Validation Tests

1. **Data Accuracy**:
   - ✅ Spot-check 10 random phases (manual validation)
   - ✅ Metric totals match manual calculation
   - ✅ File counts match git repository

2. **Performance Benchmarks**:
   - ✅ ETL completes in <30s for 163 phases
   - ✅ Queries complete in <100ms
   - ✅ Database size <10 MB

---

## 5. Deliverables

### Phase 164 (Initial Implementation):

1. **Database Schema** (`claude/data/databases/system/system_state.db`):
   - Schema creation script
   - Indexes for performance
   - Foreign key constraints

2. **ETL Tool** (`claude/tools/sre/system_state_etl.py`):
   - Markdown parser
   - Database populator
   - Validation reporting

3. **Query Library** (`claude/tools/sre/system_state_queries.py`):
   - Common query functions
   - Report generation
   - CLI interface

4. **Test Suite** (`claude/tools/sre/test_system_state_db.py`):
   - Unit tests (schema, parser, queries)
   - Integration tests (ETL, smart loader)
   - Validation tests (data accuracy)

5. **Documentation**:
   - README.md (usage guide)
   - SCHEMA.md (database schema documentation)
   - EXAMPLES.md (query examples)

### Phase 165-170 (Future):

- Backfill all 163 phases
- Smart loader integration
- Reporting dashboards
- Schema migration tools

---

## 6. Success Criteria

**Phase 164 Complete When**:

- ✅ Schema created with all tables and constraints
- ✅ ETL successfully parses last 20 phases (144-163)
- ✅ All automated tests passing (≥90% coverage)
- ✅ Query functions working with test data
- ✅ Documentation complete
- ✅ Validation report shows <5% data loss from markdown

**Long-Term Success** (Phase 170+):

- ✅ All 163 phases migrated to database
- ✅ Smart loader using DB as primary source
- ✅ ROI reports generated from structured data
- ✅ Pattern analysis enables learning from history
- ✅ Markdown regeneration from DB proves single source of truth

---

## 7. Risk Assessment

### Technical Risks

1. **Parsing Complexity** (MEDIUM):
   - Phase format has evolved over 163 iterations
   - Regex patterns may not cover all variations
   - **Mitigation**: Start with last 20 phases (consistent format), iteratively improve parser

2. **Data Loss** (LOW):
   - ETL may miss nuanced information in narrative
   - **Mitigation**: Store full markdown as narrative_text (fallback)

3. **Performance** (LOW):
   - Database queries may be slower than expected
   - **Mitigation**: Indexes on key columns, benchmark early

### Process Risks

1. **Scope Creep** (MEDIUM):
   - Temptation to add features beyond MVP
   - **Mitigation**: Phase 164 = last 20 phases only, validate before expansion

2. **Schema Evolution** (LOW):
   - Future phase format changes break ETL
   - **Mitigation**: Store full markdown (can reprocess), schema migration tools

---

## 8. Approval

**Requirements Approved By**: User (SRE Principal Engineer Agent executing)
**Date**: 2025-11-21
**Next Step**: Design database schema + write tests (TDD approach)

---

**Agent Notes**:
- Following TDD: Tests before implementation
- SRE focus: Transaction safety, error handling, observability
- Incremental approach: 20 phases first, then expand
- Keep markdown as backup: Safety net during migration
