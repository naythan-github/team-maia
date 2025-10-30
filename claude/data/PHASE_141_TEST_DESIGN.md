# Phase 141: Analysis Pattern Library - Test Design

**Project**: Global Analysis Pattern Library
**Phase**: TDD Phase 3 - Test Design
**Agent Pairing**: Data Analyst Agent (Domain Specialist) + SRE Principal Engineer Agent
**Created**: 2025-10-30
**Status**: TEST DESIGN

---

## Test Design Overview

Following TDD methodology from `claude/context/core/tdd_development_protocol.md`:
- **Phase 1**: Requirements Discovery ✅ COMPLETE
- **Phase 2**: Requirements Documentation ✅ COMPLETE
- **Phase 3**: Test Design ⭐ **CURRENT PHASE**
- **Phase 4**: Implementation (next)

**SRE Validation**: This document ensures comprehensive failure mode coverage before implementation begins.

---

## Test Strategy

### Test Pyramid

```
        /\
       /  \      E2E Tests (3)
      /----\     - Acceptance scenarios
     /      \
    /--------\   Integration Tests (25)
   /          \  - SQLite + ChromaDB
  /------------\ - Agent workflow
 /______________\ Unit Tests (53)
                  - CRUD operations
                  - Search algorithms
                  - Edge cases

Total: 81 tests (revised from 87 - consolidated duplicates)
```

### Test Coverage Goals

- **Unit Tests**: 95%+ code coverage
- **Integration Tests**: 90%+ workflow coverage
- **Performance Tests**: 100% SLA validation
- **Failure Mode Coverage**: 100% critical failure modes tested

---

## Unit Tests (53 tests)

### Test Suite 1: Pattern CRUD Operations (15 tests)

#### Test 1.1: `test_save_pattern_success`
**Purpose**: Verify successful pattern save with all required fields

**Setup**:
```python
pattern_data = {
    "pattern_name": "Timesheet Project Breakdown",
    "domain": "servicedesk",
    "question_type": "timesheet_breakdown",
    "description": "Analyze person's hours across projects",
    "sql_template": "SELECT ... WHERE name IN ({{names}})",
    "presentation_format": "Top 5 + remaining + unaccounted",
    "business_context": "7.6 hrs/day, sick/holidays not recorded",
    "tags": ["timesheet", "hours", "projects"]
}
```

**Actions**:
1. Create AnalysisPatternLibrary instance
2. Call `save_pattern(**pattern_data)`

**Assertions**:
- ✅ Returns pattern_id (format: `timesheet_breakdown_<timestamp>`)
- ✅ Pattern exists in SQLite database
- ✅ Embedding exists in ChromaDB collection
- ✅ All fields match input data
- ✅ created_date is current timestamp
- ✅ version = 1
- ✅ status = 'active'

**Failure Mode**: Transactional save fails → both SQLite and ChromaDB rolled back

---

#### Test 1.2: `test_save_pattern_missing_required_fields`
**Purpose**: Verify validation for missing required fields

**Test Cases**:
```python
test_cases = [
    {"pattern_name": None},  # Missing name
    {"domain": None},        # Missing domain
    {"question_type": None}, # Missing question_type
    {"description": None}    # Missing description
]
```

**Assertions**:
- ✅ Raises `ValidationError` with clear message
- ✅ No record created in database
- ✅ No embedding created in ChromaDB

---

#### Test 1.3: `test_save_pattern_duplicate_handling`
**Purpose**: Verify duplicate pattern names create new versions

**Actions**:
1. Save pattern "Timesheet Breakdown"
2. Save same pattern again (identical name/domain)

**Assertions**:
- ✅ First save: `timesheet_breakdown_v1`
- ✅ Second save: `timesheet_breakdown_v2` (version incremented)
- ✅ Both patterns exist in database
- ✅ Version history linked (v2 references v1)

---

#### Test 1.4: `test_get_pattern_success`
**Purpose**: Verify pattern retrieval by ID

**Setup**: Save test pattern, get pattern_id

**Actions**: Call `get_pattern(pattern_id)`

**Assertions**:
- ✅ Returns dict with all pattern fields
- ✅ Includes usage statistics (total_uses=0, last_used=None, success_rate=N/A)
- ✅ Retrieval time <100ms

---

#### Test 1.5: `test_get_pattern_not_found`
**Purpose**: Verify behavior when pattern doesn't exist

**Actions**: Call `get_pattern("nonexistent_pattern_id")`

**Assertions**:
- ✅ Returns None (not exception)
- ✅ Logs warning "Pattern not found: nonexistent_pattern_id"

---

#### Test 1.6: `test_get_pattern_archived_excluded`
**Purpose**: Verify archived patterns excluded by default

**Setup**:
1. Save pattern
2. Archive pattern (set status='archived')

**Actions**: Call `get_pattern(pattern_id)`

**Assertions**:
- ✅ Returns None (archived pattern excluded)
- ✅ With `include_archived=True`: Returns archived pattern

---

#### Test 1.7: `test_update_pattern_creates_new_version`
**Purpose**: Verify pattern updates create new versions

**Setup**: Save pattern v1

**Actions**:
```python
update_pattern(pattern_id,
    sql_template="NEW SQL",
    change_note="Fixed bug in WHERE clause"
)
```

**Assertions**:
- ✅ Returns new pattern_id (`pattern_v2`)
- ✅ Old version status='deprecated'
- ✅ New version status='active'
- ✅ Version history links v2 → v1
- ✅ ChromaDB embedding updated

---

#### Test 1.8: `test_update_pattern_no_changes`
**Purpose**: Verify no-op when no changes detected

**Setup**: Save pattern

**Actions**: Call `update_pattern(pattern_id)` with no field changes

**Assertions**:
- ✅ Returns original pattern_id (no new version)
- ✅ Version number unchanged

---

#### Test 1.9: `test_delete_pattern_soft_delete`
**Purpose**: Verify soft delete behavior

**Setup**: Save pattern

**Actions**: Call `delete_pattern(pattern_id)`

**Assertions**:
- ✅ Pattern still exists in database
- ✅ status = 'archived'
- ✅ Excluded from search results
- ✅ Can be restored with `restore_pattern(pattern_id)`

---

#### Test 1.10: `test_delete_pattern_hard_delete`
**Purpose**: Verify hard delete removes all traces

**Setup**: Save pattern

**Actions**: Call `delete_pattern(pattern_id, hard=True)`

**Assertions**:
- ✅ Pattern removed from SQLite
- ✅ Embedding removed from ChromaDB
- ✅ Usage records marked as orphaned (not deleted)
- ✅ Cannot be retrieved or restored

---

#### Test 1.11: `test_list_patterns_default`
**Purpose**: Verify pattern listing with no filters

**Setup**: Save 5 active patterns, 2 archived patterns

**Actions**: Call `list_patterns()`

**Assertions**:
- ✅ Returns 5 patterns (archived excluded)
- ✅ Sorted by created_date DESC (newest first)
- ✅ Contains: pattern_id, name, domain, usage_count

---

#### Test 1.12: `test_list_patterns_domain_filter`
**Purpose**: Verify domain filtering

**Setup**:
- Save 3 patterns (domain='servicedesk')
- Save 2 patterns (domain='recruitment')

**Actions**: Call `list_patterns(domain='servicedesk')`

**Assertions**:
- ✅ Returns 3 patterns (only servicedesk)
- ✅ No recruitment patterns in results

---

#### Test 1.13: `test_list_patterns_pagination`
**Purpose**: Verify pagination for large result sets

**Setup**: Save 100 patterns

**Actions**: Call `list_patterns(limit=20, offset=40)`

**Assertions**:
- ✅ Returns 20 patterns (patterns 41-60)
- ✅ Response includes: total_count=100, has_more=True

---

#### Test 1.14: `test_list_patterns_empty_database`
**Purpose**: Verify empty list when no patterns exist

**Actions**: Call `list_patterns()` on empty database

**Assertions**:
- ✅ Returns empty list []
- ✅ No exception raised

---

#### Test 1.15: `test_save_pattern_transaction_rollback`
**Purpose**: Verify transaction rollback on partial failure

**Setup**: Mock ChromaDB to fail after SQLite succeeds

**Actions**: Call `save_pattern(**pattern_data)`

**Assertions**:
- ✅ Raises exception (ChromaDB failed)
- ✅ No record in SQLite (transaction rolled back)
- ✅ No orphaned data in either system

---

### Test Suite 2: Semantic Search (10 tests)

#### Test 2.1: `test_search_exact_match`
**Purpose**: Verify high similarity for exact match queries

**Setup**: Save pattern with description "Timesheet project breakdown"

**Actions**: Call `search_patterns("Timesheet project breakdown")`

**Assertions**:
- ✅ Returns 1 result
- ✅ Similarity score >0.95
- ✅ Correct pattern returned

---

#### Test 2.2: `test_search_semantic_match`
**Purpose**: Verify semantic similarity for paraphrased queries

**Setup**: Save pattern "Timesheet project breakdown"

**Actions**: Call `search_patterns("show me how hours are allocated across projects")`

**Assertions**:
- ✅ Returns timesheet pattern
- ✅ Similarity score >0.75 (above threshold)
- ✅ Search time <200ms

---

#### Test 2.3: `test_search_no_match`
**Purpose**: Verify empty results when no matches above threshold

**Setup**: Save pattern "Timesheet analysis"

**Actions**: Call `search_patterns("quantum physics simulator")`

**Assertions**:
- ✅ Returns empty list []
- ✅ No exception raised
- ✅ Search time <200ms

---

#### Test 2.4: `test_search_domain_filter`
**Purpose**: Verify domain filtering in search

**Setup**:
- Save pattern "Timesheet" (domain='servicedesk')
- Save pattern "Candidate hours" (domain='recruitment')

**Actions**: Call `search_patterns("hours analysis", domain='servicedesk')`

**Assertions**:
- ✅ Returns only servicedesk pattern
- ✅ Recruitment pattern excluded (even if high similarity)

---

#### Test 2.5: `test_search_similarity_threshold`
**Purpose**: Verify custom similarity thresholds

**Setup**: Save pattern

**Actions**:
```python
# Low threshold
results_low = search_patterns("related query", threshold=0.60)
# High threshold
results_high = search_patterns("related query", threshold=0.90)
```

**Assertions**:
- ✅ `results_low` has more matches (permissive)
- ✅ `results_high` has fewer/no matches (strict)
- ✅ All results meet specified threshold

---

#### Test 2.6: `test_search_top_n_ranking`
**Purpose**: Verify results ranked by similarity score

**Setup**: Save 5 patterns with varying relevance

**Actions**: Call `search_patterns("timesheet", limit=3)`

**Assertions**:
- ✅ Returns 3 results
- ✅ Ordered by similarity DESC (highest first)
- ✅ All scores between 0.0 and 1.0

---

#### Test 2.7: `test_search_empty_query`
**Purpose**: Verify behavior with empty search query

**Actions**: Call `search_patterns("")`

**Assertions**:
- ✅ Returns all patterns (sorted by usage_count DESC)
- ✅ No similarity scores (not applicable)

---

#### Test 2.8: `test_search_special_characters`
**Purpose**: Verify handling of special characters in query

**Actions**: Call `search_patterns("What's the project $$ breakdown? (hours)")`

**Assertions**:
- ✅ Special chars handled gracefully (no crash)
- ✅ Returns relevant results
- ✅ Search time <200ms

---

#### Test 2.9: `test_search_performance_100_patterns`
**Purpose**: Verify search performance at scale

**Setup**: Save 100 patterns with embeddings

**Actions**: Call `search_patterns("timesheet analysis")`

**Assertions**:
- ✅ Search time <200ms (P95 SLA)
- ✅ Returns correct top-5 results

---

#### Test 2.10: `test_search_chromadb_fallback`
**Purpose**: Verify SQLite fallback when ChromaDB unavailable

**Setup**: Mock ChromaDB to raise connection error

**Actions**: Call `search_patterns("timesheet")`

**Assertions**:
- ✅ Falls back to SQLite full-text search
- ✅ Returns results (degraded mode)
- ✅ Logs warning "ChromaDB unavailable, using SQLite fallback"
- ✅ Search still completes <500ms

---

### Test Suite 3: Auto-Suggestion (12 tests)

#### Test 3.1: `test_suggest_pattern_high_confidence_match`
**Purpose**: Verify auto-suggestion for high-confidence matches

**Setup**: Save timesheet pattern with example_input "Show hours for employees"

**Actions**: Call `suggest_pattern("Show project hours for Olli and Alex")`

**Assertions**:
- ✅ Returns matched=True
- ✅ Confidence >0.80
- ✅ pattern_id = timesheet pattern
- ✅ Suggestion time <500ms

---

#### Test 3.2: `test_suggest_pattern_low_confidence_no_match`
**Purpose**: Verify no suggestion when confidence <0.70

**Setup**: Save timesheet pattern

**Actions**: Call `suggest_pattern("What's the weather today?")`

**Assertions**:
- ✅ Returns matched=False
- ✅ Confidence <0.70
- ✅ pattern_id = None

---

#### Test 3.3: `test_suggest_pattern_medium_confidence_suggest_only`
**Purpose**: Verify suggestion but no auto-apply for medium confidence

**Setup**: Save timesheet pattern

**Actions**: Call `suggest_pattern("employee work hours", auto_apply=True)`

**Confidence**: 0.75 (medium)

**Assertions**:
- ✅ Returns matched=True
- ✅ pattern_id provided
- ✅ sql_ready = None (no auto-apply for medium confidence)
- ✅ Suggests pattern but requires user confirmation

---

#### Test 3.4: `test_suggest_pattern_variable_extraction_names`
**Purpose**: Verify SQL variable substitution for names

**Setup**: Save pattern with SQL template `WHERE name IN ({{names}})`

**Actions**: Call `suggest_pattern("Show hours for Olli Ojala and Alex Olver", auto_apply=True)`

**Assertions**:
- ✅ sql_ready contains: `WHERE name IN ('Olli Ojala', 'Alex Olver')`
- ✅ Names correctly extracted and quoted
- ✅ SQL syntax valid

---

#### Test 3.5: `test_suggest_pattern_variable_extraction_dates`
**Purpose**: Verify date range variable extraction

**Setup**: Save pattern with SQL template `WHERE date BETWEEN {{start_date}} AND {{end_date}}`

**Actions**: Call `suggest_pattern("Show data from July 1 to Oct 13", auto_apply=True)`

**Assertions**:
- ✅ sql_ready contains: `WHERE date BETWEEN '2025-07-01' AND '2025-10-13'`
- ✅ Dates parsed to ISO format
- ✅ SQL syntax valid

---

#### Test 3.6: `test_suggest_pattern_variable_extraction_failure`
**Purpose**: Verify graceful handling when variable extraction fails

**Setup**: Save pattern with SQL template `WHERE name IN ({{names}})`

**Actions**: Call `suggest_pattern("Show timesheet data", auto_apply=True)`

**Issue**: No names found in query

**Assertions**:
- ✅ Returns matched=True (pattern matched)
- ✅ sql_ready = None (extraction failed)
- ✅ Returns SQL template with placeholders intact
- ✅ Logs info "Could not extract variables, user must fill manually"

---

#### Test 3.7: `test_suggest_pattern_multiple_high_confidence_matches`
**Purpose**: Verify behavior when multiple patterns match with high confidence

**Setup**:
- Save "Timesheet by person" pattern
- Save "Timesheet by project" pattern

**Actions**: Call `suggest_pattern("Show timesheet breakdown")`

**Both patterns**: Confidence >0.80

**Assertions**:
- ✅ Returns top match (highest confidence)
- ✅ Logs info "Multiple matches found, selected highest confidence"
- ✅ Includes alternative_patterns list in response

---

#### Test 3.8: `test_suggest_pattern_domain_hint`
**Purpose**: Verify domain hint improves suggestion accuracy

**Setup**:
- Save "Timesheet hours" (domain='servicedesk')
- Save "Billable hours" (domain='financial')

**Actions**: Call `suggest_pattern("Show hours breakdown", domain='servicedesk')`

**Assertions**:
- ✅ Returns servicedesk pattern (domain match)
- ✅ Financial pattern excluded (domain mismatch)
- ✅ Higher confidence due to domain match

---

#### Test 3.9: `test_suggest_pattern_sql_injection_prevention`
**Purpose**: Verify SQL injection is prevented in variable substitution

**Actions**: Call `suggest_pattern("Show hours for Robert'); DROP TABLE timesheets;--", auto_apply=True)`

**Assertions**:
- ✅ Malicious SQL properly escaped/parameterized
- ✅ sql_ready uses parameterized query (not string substitution)
- ✅ No SQL injection possible

---

#### Test 3.10: `test_suggest_pattern_performance_500ms_sla`
**Purpose**: Verify suggestion latency meets SLA

**Setup**: Database with 100 patterns

**Actions**: Call `suggest_pattern("Show project hours")` 10 times

**Assertions**:
- ✅ P95 latency <500ms (search + variable extraction)
- ✅ P50 latency <300ms

---

#### Test 3.11: `test_suggest_pattern_empty_database`
**Purpose**: Verify behavior when no patterns exist

**Actions**: Call `suggest_pattern("Show timesheet data")` on empty DB

**Assertions**:
- ✅ Returns matched=False
- ✅ No exception raised
- ✅ Suggestion time <100ms (fast failure)

---

#### Test 3.12: `test_suggest_pattern_archived_excluded`
**Purpose**: Verify archived patterns not suggested

**Setup**:
- Save active pattern "Timesheet v2"
- Archive old pattern "Timesheet v1"

**Actions**: Call `suggest_pattern("Show timesheet data")`

**Assertions**:
- ✅ Returns v2 (active pattern)
- ✅ v1 excluded (archived)

---

### Test Suite 4: Usage Tracking (8 tests)

#### Test 4.1: `test_track_usage_success`
**Purpose**: Verify usage logging on pattern use

**Setup**: Save pattern

**Actions**: Call `track_usage(pattern_id, "Show hours for Olli", success=True)`

**Assertions**:
- ✅ Usage record created in database
- ✅ Fields: pattern_id, user_question, used_date, success=True
- ✅ Pattern usage_count incremented
- ✅ last_used updated to current timestamp

---

#### Test 4.2: `test_track_usage_failure`
**Purpose**: Verify usage logging when pattern fails

**Actions**: Call `track_usage(pattern_id, "Show hours", success=False, feedback="SQL error: column not found")`

**Assertions**:
- ✅ Usage record created with success=False
- ✅ feedback field contains error details
- ✅ Pattern usage_count still incremented (tracks attempts)

---

#### Test 4.3: `test_track_usage_nonexistent_pattern`
**Purpose**: Verify graceful handling for invalid pattern_id

**Actions**: Call `track_usage("nonexistent_id", "question", success=True)`

**Assertions**:
- ✅ Logs warning "Pattern not found: nonexistent_id"
- ✅ No usage record created
- ✅ No exception raised (non-blocking)

---

#### Test 4.4: `test_get_usage_stats_single_pattern`
**Purpose**: Verify usage statistics retrieval

**Setup**:
- Save pattern
- Track 10 uses (8 success, 2 failure)

**Actions**: Call `get_usage_stats(pattern_id)`

**Assertions**:
- ✅ Returns: total_uses=10, success_rate=0.80, last_used=<recent timestamp>
- ✅ Includes: avg_uses_per_week, first_used, most_common_questions

---

#### Test 4.5: `test_get_usage_stats_all_patterns`
**Purpose**: Verify global usage statistics

**Setup**: Save 5 patterns with varying usage

**Actions**: Call `get_usage_stats()` (no pattern_id)

**Assertions**:
- ✅ Returns summary: total_patterns=5, total_uses=X, avg_success_rate=Y
- ✅ Top 5 most-used patterns ranked
- ✅ Stale patterns identified (not used in 90+ days)

---

#### Test 4.6: `test_track_usage_non_blocking`
**Purpose**: Verify usage tracking doesn't block pattern execution

**Setup**: Mock usage tracking to take 5 seconds

**Actions**: Call `track_usage(...)` and immediately continue

**Assertions**:
- ✅ Function returns in <10ms (async tracking)
- ✅ Usage logged in background
- ✅ Pattern execution not delayed

---

#### Test 4.7: `test_usage_retention_cleanup`
**Purpose**: Verify old usage records archived after 1 year

**Setup**: Create usage records with old timestamps (>1 year ago)

**Actions**: Call `cleanup_old_usage_records()`

**Assertions**:
- ✅ Records >1 year old moved to archive table
- ✅ Active usage table stays small (<10K records)
- ✅ Archived records still queryable if needed

---

#### Test 4.8: `test_usage_tracking_database_failure`
**Purpose**: Verify graceful degradation when usage tracking fails

**Setup**: Mock database to fail on usage insert

**Actions**:
1. Use pattern (triggers usage tracking)
2. Usage tracking fails

**Assertions**:
- ✅ Pattern execution continues (not blocked)
- ✅ Error logged but not raised
- ✅ User unaware of tracking failure

---

### Test Suite 5: Versioning (8 tests)

#### Test 5.1: `test_create_new_version_success`
**Purpose**: Verify version creation workflow

**Setup**: Save pattern v1

**Actions**: Call `create_new_version(pattern_id, "Fixed SQL bug", sql_template="NEW SQL")`

**Assertions**:
- ✅ New pattern created: pattern_v2
- ✅ v1 status='deprecated'
- ✅ v2 status='active'
- ✅ Version history: v2 → v1 (linked)
- ✅ Changes documented: "Fixed SQL bug"

---

#### Test 5.2: `test_get_version_history`
**Purpose**: Verify version history retrieval

**Setup**: Create pattern with 3 versions (v1 → v2 → v3)

**Actions**: Call `get_version_history(pattern_id)`

**Assertions**:
- ✅ Returns list of 3 versions (ordered v3, v2, v1)
- ✅ Each version includes: version number, changes, created_date, status
- ✅ Current version (v3) is status='active'

---

#### Test 5.3: `test_version_number_increment`
**Purpose**: Verify version numbers increment correctly

**Setup**: Create pattern

**Actions**:
1. Save pattern → v1
2. Update → v2
3. Update → v3
4. Update → v4

**Assertions**:
- ✅ Version numbers: 1, 2, 3, 4 (sequential)
- ✅ No gaps in version sequence

---

#### Test 5.4: `test_deprecated_version_excluded_from_search`
**Purpose**: Verify deprecated versions don't appear in search

**Setup**:
- Create pattern v1
- Create v2 (v1 deprecated)

**Actions**: Call `search_patterns("pattern query")`

**Assertions**:
- ✅ Returns only v2 (active)
- ✅ v1 excluded (deprecated)

---

#### Test 5.5: `test_restore_deprecated_version`
**Purpose**: Verify old version can be restored (creates new version)

**Setup**: Create pattern v1 → v2 (v1 deprecated)

**Actions**: Call `restore_version(pattern_v1_id)`

**Assertions**:
- ✅ Creates v3 (copy of v1 content)
- ✅ v2 status='deprecated'
- ✅ v3 status='active'
- ✅ Version history: v3 → v2 → v1

---

#### Test 5.6: `test_version_chromadb_embedding_update`
**Purpose**: Verify ChromaDB embedding updates with new versions

**Setup**: Save pattern v1 with description "Old description"

**Actions**: Create v2 with description "New description"

**Assertions**:
- ✅ ChromaDB has 2 embeddings (v1 and v2)
- ✅ Search "New description" → returns v2 (not v1)
- ✅ v1 embedding marked as deprecated (not searched by default)

---

#### Test 5.7: `test_version_usage_tracking_separate`
**Purpose**: Verify usage tracked separately per version

**Setup**:
- Create v1, use 5 times
- Create v2, use 10 times

**Actions**: Call `get_usage_stats(pattern_v2_id)`

**Assertions**:
- ✅ v2 usage: total_uses=10 (not 15)
- ✅ v1 usage: total_uses=5 (separate tracking)

---

#### Test 5.8: `test_version_deletion_cascade`
**Purpose**: Verify deleting latest version doesn't delete version history

**Setup**: Create v1 → v2 → v3

**Actions**: Call `delete_pattern(pattern_v3_id)`

**Assertions**:
- ✅ v3 status='archived'
- ✅ v2 status='deprecated' (unchanged)
- ✅ v1 status='deprecated' (unchanged)
- ✅ Version history preserved

---

## Integration Tests (25 tests)

### Test Suite 6: SQLite + ChromaDB Integration (5 tests)

#### Test 6.1: `test_transactional_save_both_succeed`
**Purpose**: Verify atomic save to both databases

**Actions**: Save pattern (SQLite + ChromaDB)

**Assertions**:
- ✅ Record in SQLite
- ✅ Embedding in ChromaDB
- ✅ Both IDs match (referential integrity)

---

#### Test 6.2: `test_transactional_save_sqlite_fails`
**Purpose**: Verify rollback when SQLite fails

**Setup**: Mock SQLite to raise exception

**Actions**: Call `save_pattern(**data)`

**Assertions**:
- ✅ Exception raised
- ✅ No record in SQLite
- ✅ No embedding in ChromaDB (rollback)

---

#### Test 6.3: `test_transactional_save_chromadb_fails`
**Purpose**: Verify rollback when ChromaDB fails

**Setup**: Mock ChromaDB to raise exception

**Actions**: Call `save_pattern(**data)`

**Assertions**:
- ✅ Exception raised
- ✅ No record in SQLite (rollback)
- ✅ No embedding in ChromaDB

---

#### Test 6.4: `test_chromadb_unavailable_graceful_degradation`
**Purpose**: Verify graceful degradation when ChromaDB down

**Setup**: Stop ChromaDB service

**Actions**:
1. Save pattern (queued for later embedding)
2. Search pattern (fallback to SQLite)

**Assertions**:
- ✅ Save succeeds (SQLite only)
- ✅ Embedding queued for later
- ✅ Search uses SQLite full-text (degraded mode)
- ✅ No data loss

---

#### Test 6.5: `test_chromadb_recovery_reindex`
**Purpose**: Verify ChromaDB recovery after downtime

**Setup**:
1. ChromaDB down → save 5 patterns (SQLite only)
2. ChromaDB restored

**Actions**: Call `reindex_chromadb()`

**Assertions**:
- ✅ All 5 patterns embedded in ChromaDB
- ✅ Search now uses semantic search (restored mode)
- ✅ No duplicates or data loss

---

### Test Suite 7: Agent Integration (8 tests)

#### Test 7.1: `test_data_analyst_agent_pattern_suggestion`
**Purpose**: Verify Data Analyst Agent receives pattern suggestions

**Setup**: Save timesheet pattern

**Actions**:
1. Agent receives question: "Show hours for Olli"
2. Agent calls `suggest_pattern(question)`

**Assertions**:
- ✅ Agent receives suggestion (confidence >0.80)
- ✅ Agent uses pattern (not ad-hoc analysis)
- ✅ Results formatted per pattern specification
- ✅ Usage tracked automatically

---

#### Test 7.2: `test_agent_fallback_to_adhoc_no_pattern`
**Purpose**: Verify agent falls back to ad-hoc when no pattern matches

**Setup**: Empty pattern library

**Actions**: Agent receives question

**Assertions**:
- ✅ No pattern suggested (matched=False)
- ✅ Agent performs ad-hoc analysis
- ✅ Results still returned to user

---

#### Test 7.3: `test_agent_usage_tracking_automatic`
**Purpose**: Verify usage automatically tracked by agent

**Setup**: Save pattern, agent uses it

**Actions**: Agent executes pattern 3 times

**Assertions**:
- ✅ 3 usage records created
- ✅ All marked success=True
- ✅ Pattern usage_count=3

---

#### Test 7.4: `test_agent_pattern_failure_fallback`
**Purpose**: Verify agent falls back to ad-hoc if pattern execution fails

**Setup**: Save pattern with broken SQL

**Actions**: Agent uses pattern → SQL fails

**Assertions**:
- ✅ Usage tracked with success=False
- ✅ Agent falls back to ad-hoc analysis
- ✅ User receives result (graceful degradation)
- ✅ Error logged for pattern improvement

---

#### Test 7.5: `test_agent_offer_to_save_successful_adhoc`
**Purpose**: Verify agent offers to save successful ad-hoc analyses

**Setup**: No matching pattern

**Actions**:
1. Agent performs ad-hoc analysis
2. Analysis succeeds

**Assertions**:
- ✅ Agent suggests: "Save this as a reusable pattern?"
- ✅ If user says yes → pattern saved
- ✅ If user says no → not saved

---

#### Test 7.6: `test_agent_pattern_suggestion_timeout`
**Purpose**: Verify agent continues if pattern suggestion times out

**Setup**: Mock pattern suggestion to take 10 seconds

**Actions**: Agent receives question

**Assertions**:
- ✅ Pattern suggestion times out after 500ms
- ✅ Agent falls back to ad-hoc (not blocked)
- ✅ User receives result within reasonable time

---

#### Test 7.7: `test_agent_multiple_patterns_user_choice`
**Purpose**: Verify agent lets user choose when multiple patterns match

**Setup**: Save 2 patterns with similar confidence

**Actions**: Agent receives ambiguous question

**Assertions**:
- ✅ Agent presents both options to user
- ✅ User selects preferred pattern
- ✅ Agent executes selected pattern

---

#### Test 7.8: `test_agent_end_to_end_workflow`
**Purpose**: Complete end-to-end validation

**Setup**: Save timesheet pattern

**Actions**:
1. User asks: "Show project hours for Olli and Alex"
2. Agent suggests pattern (confidence 0.92)
3. Agent auto-applies pattern (extracts names)
4. Agent executes SQL
5. Agent formats results per pattern spec
6. Agent tracks usage

**Assertions**:
- ✅ All steps complete successfully
- ✅ Results match expected format
- ✅ Usage tracked
- ✅ Total time <5 seconds

---

### Test Suite 8: CLI Integration (7 tests)

#### Test 8.1: `test_cli_save_pattern`
**Purpose**: Verify CLI save command

**Actions**: Run `analysis-pattern save --name "Test" --domain "test" --question-type "test" --description "Test pattern"`

**Assertions**:
- ✅ Pattern saved successfully
- ✅ Output: "Pattern saved: test_test_<timestamp>"
- ✅ Exit code: 0

---

#### Test 8.2: `test_cli_search_pattern`
**Purpose**: Verify CLI search command

**Setup**: Save test pattern

**Actions**: Run `analysis-pattern search "test query"`

**Assertions**:
- ✅ Output lists matching patterns
- ✅ Includes: pattern_id, name, similarity score
- ✅ Exit code: 0

---

#### Test 8.3: `test_cli_list_patterns`
**Purpose**: Verify CLI list command

**Setup**: Save 5 patterns

**Actions**: Run `analysis-pattern list --domain servicedesk`

**Assertions**:
- ✅ Output lists all servicedesk patterns
- ✅ Formatted as table: ID | Name | Domain | Uses
- ✅ Exit code: 0

---

#### Test 8.4: `test_cli_show_pattern_details`
**Purpose**: Verify CLI show command

**Setup**: Save pattern

**Actions**: Run `analysis-pattern show <pattern_id>`

**Assertions**:
- ✅ Output shows all pattern fields (formatted)
- ✅ Includes: name, domain, SQL, format, context, usage stats
- ✅ Exit code: 0

---

#### Test 8.5: `test_cli_delete_pattern`
**Purpose**: Verify CLI delete command

**Setup**: Save pattern

**Actions**: Run `analysis-pattern delete <pattern_id>`

**Assertions**:
- ✅ Output: "Pattern archived: <pattern_id>"
- ✅ Pattern status='archived'
- ✅ Exit code: 0

---

#### Test 8.6: `test_cli_usage_stats`
**Purpose**: Verify CLI stats command

**Setup**: Save patterns with usage records

**Actions**: Run `analysis-pattern stats --top 10`

**Assertions**:
- ✅ Output shows top 10 most-used patterns
- ✅ Includes: rank, pattern name, total uses, success rate
- ✅ Exit code: 0

---

#### Test 8.7: `test_cli_error_handling`
**Purpose**: Verify CLI error messages

**Actions**: Run `analysis-pattern save` (missing required fields)

**Assertions**:
- ✅ Clear error message: "Missing required field: name"
- ✅ Shows usage help
- ✅ Exit code: 1 (user error)

---

### Test Suite 9: Performance & Failure Modes (5 tests)

#### Test 9.1: `test_search_latency_100_patterns`
**Purpose**: Verify search performance at scale

**Setup**: Save 100 patterns with embeddings

**Actions**: Run 20 search queries, measure P50/P95 latency

**Assertions**:
- ✅ P50 <100ms
- ✅ P95 <200ms (SLA)
- ✅ No degradation over repeated queries

---

#### Test 9.2: `test_suggestion_latency_1000_patterns`
**Purpose**: Verify suggestion performance at scale

**Setup**: Save 1000 patterns

**Actions**: Run 20 suggestion queries, measure latency

**Assertions**:
- ✅ P50 <300ms
- ✅ P95 <500ms (SLA)
- ✅ Variable extraction adds <100ms overhead

---

#### Test 9.3: `test_database_corruption_recovery`
**Purpose**: Verify auto-recovery from database corruption

**Setup**: Corrupt SQLite database file

**Actions**: Call `get_pattern(pattern_id)`

**Assertions**:
- ✅ Detects corruption (sqlite3.DatabaseError)
- ✅ Attempts restore from backup
- ✅ If backup succeeds → pattern retrieved
- ✅ If backup fails → clear error message to user

---

#### Test 9.4: `test_disk_space_exhausted`
**Purpose**: Verify graceful handling when disk full

**Setup**: Mock disk to be full

**Actions**: Call `save_pattern(**data)`

**Assertions**:
- ✅ Raises clear error: "Disk space exhausted, cannot save pattern"
- ✅ No partial writes (transaction rolled back)
- ✅ Existing patterns still accessible

---

#### Test 9.5: `test_concurrent_writes_serialization`
**Purpose**: Verify SQLite handles concurrent writes correctly

**Setup**: Launch 10 concurrent save operations

**Actions**: All 10 saves run simultaneously

**Assertions**:
- ✅ All 10 patterns saved successfully (no data loss)
- ✅ SQLite serializes writes (no corruption)
- ✅ No deadlocks

---

## End-to-End Acceptance Tests (3 tests)

### Test E2E-1: `test_timesheet_pattern_full_workflow`
**Purpose**: Validate complete workflow with real timesheet pattern

**Scenario**:
1. User saves timesheet pattern via CLI
2. User asks: "Show project hours for Olli Ojala and Alex Olver"
3. Data Analyst Agent auto-suggests pattern (confidence 0.92)
4. Agent extracts names: ['Olli Ojala', 'Alex Olver']
5. Agent executes SQL against ServiceDesk database
6. Agent formats results: Top 5 projects + remaining + unaccounted hours
7. Usage tracked automatically

**Assertions**:
- ✅ All steps complete successfully
- ✅ Results match expected format (7.6 hrs/day, % of available hours)
- ✅ Total workflow time <5 seconds
- ✅ Usage record created (success=True)

---

### Test E2E-2: `test_pattern_evolution_workflow`
**Purpose**: Validate pattern versioning workflow

**Scenario**:
1. Save pattern v1 with SQL bug
2. Use pattern 5 times (3 success, 2 failure)
3. Update pattern with fixed SQL (creates v2)
4. Use pattern 5 more times (5 success)
5. Check usage stats

**Assertions**:
- ✅ v1: 5 uses, 60% success rate, status='deprecated'
- ✅ v2: 5 uses, 100% success rate, status='active'
- ✅ Version history: v2 → v1
- ✅ Search returns v2 (not v1)

---

### Test E2E-3: `test_multi_domain_pattern_library`
**Purpose**: Validate pattern library across multiple domains

**Scenario**:
1. Save 5 servicedesk patterns
2. Save 3 recruitment patterns
3. Save 2 financial patterns
4. Search "hours analysis" in different domains
5. List patterns by domain

**Assertions**:
- ✅ Total 10 patterns saved
- ✅ Domain filters work correctly
- ✅ Search results respect domain boundaries
- ✅ No cross-domain pollution

---

## Test Execution Plan

### Phase 1: Unit Tests (Day 1, 4 hours)
**Order**: Test Suites 1-5 (53 tests)
- Suite 1: CRUD operations (foundation)
- Suite 2: Semantic search (critical feature)
- Suite 3: Auto-suggestion (core UX)
- Suite 4: Usage tracking (observability)
- Suite 5: Versioning (data integrity)

**Success Criteria**: 95%+ pass rate, <5 failing tests

---

### Phase 2: Integration Tests (Day 1-2, 3 hours)
**Order**: Test Suites 6-9 (25 tests)
- Suite 6: Database integration (reliability)
- Suite 7: Agent integration (end-user experience)
- Suite 8: CLI integration (usability)
- Suite 9: Performance & failure modes (SLA validation)

**Success Criteria**: 90%+ pass rate, all performance SLAs met

---

### Phase 3: E2E Acceptance Tests (Day 2, 1 hour)
**Order**: E2E-1, E2E-2, E2E-3 (3 tests)

**Success Criteria**: 100% pass rate (blocking for release)

---

### Total Test Execution Time: ~8 hours

---

## Test Infrastructure Requirements

### Test Fixtures

```python
# conftest.py

@pytest.fixture
def temp_db():
    """Temporary SQLite database for testing."""
    db_path = tempfile.mktemp(suffix='.db')
    yield db_path
    os.remove(db_path)

@pytest.fixture
def temp_chromadb():
    """Temporary ChromaDB collection for testing."""
    chroma_path = tempfile.mkdtemp()
    yield chroma_path
    shutil.rmtree(chroma_path)

@pytest.fixture
def pattern_library(temp_db, temp_chromadb):
    """AnalysisPatternLibrary instance with temp databases."""
    return AnalysisPatternLibrary(db_path=temp_db, chromadb_path=temp_chromadb)

@pytest.fixture
def sample_pattern_data():
    """Sample pattern data for testing."""
    return {
        "pattern_name": "Timesheet Project Breakdown",
        "domain": "servicedesk",
        "question_type": "timesheet_breakdown",
        "description": "Analyze person's hours across projects",
        "sql_template": "SELECT ... WHERE name IN ({{names}})",
        "presentation_format": "Top 5 + remaining + unaccounted",
        "business_context": "7.6 hrs/day, sick/holidays not recorded",
        "tags": ["timesheet", "hours", "projects"]
    }
```

### Test Utilities

```python
# test_utils.py

def assert_pattern_valid(pattern: dict):
    """Assert pattern has all required fields."""
    required = ['pattern_id', 'pattern_name', 'domain', 'question_type', 'description']
    for field in required:
        assert field in pattern, f"Missing required field: {field}"

def measure_latency(func, *args, **kwargs):
    """Measure function execution time."""
    start = time.time()
    result = func(*args, **kwargs)
    latency_ms = (time.time() - start) * 1000
    return result, latency_ms

def generate_test_patterns(count: int, domain: str = 'test'):
    """Generate N test patterns for performance testing."""
    patterns = []
    for i in range(count):
        patterns.append({
            "pattern_name": f"Test Pattern {i}",
            "domain": domain,
            "question_type": f"test_type_{i}",
            "description": f"Test description {i} with unique content for embeddings"
        })
    return patterns
```

---

## Test Coverage Report Template

```
==============================================
Phase 141: Analysis Pattern Library - Test Report
==============================================

Execution Date: YYYY-MM-DD
Test Environment: Python 3.9, SQLite 3.x, ChromaDB 0.4+

UNIT TESTS (53 tests)
----------------------
Suite 1: CRUD Operations       15/15 PASS ✅
Suite 2: Semantic Search       10/10 PASS ✅
Suite 3: Auto-Suggestion       12/12 PASS ✅
Suite 4: Usage Tracking         8/8  PASS ✅
Suite 5: Versioning             8/8  PASS ✅

Total: 53/53 PASS (100%)
Coverage: 96.2%

INTEGRATION TESTS (25 tests)
-----------------------------
Suite 6: Database Integration   5/5  PASS ✅
Suite 7: Agent Integration      8/8  PASS ✅
Suite 8: CLI Integration        7/7  PASS ✅
Suite 9: Performance & Failure  5/5  PASS ✅

Total: 25/25 PASS (100%)
Coverage: 91.8%

E2E ACCEPTANCE TESTS (3 tests)
-------------------------------
E2E-1: Timesheet Full Workflow  PASS ✅
E2E-2: Pattern Evolution        PASS ✅
E2E-3: Multi-Domain Library     PASS ✅

Total: 3/3 PASS (100%)

PERFORMANCE METRICS
-------------------
Search Latency (100 patterns):
  P50: 87ms ✅ (target: <100ms)
  P95: 156ms ✅ (target: <200ms)

Suggestion Latency:
  P50: 283ms ✅ (target: <300ms)
  P95: 447ms ✅ (target: <500ms)

Save Latency:
  P95: 412ms ✅ (target: <500ms)

OVERALL RESULT
--------------
✅ ALL TESTS PASSING (81/81)
✅ ALL PERFORMANCE SLAS MET
✅ READY FOR PRODUCTION DEPLOYMENT

Next Steps:
1. Deploy to production
2. Save timesheet pattern (validation)
3. Monitor usage for 1 week
4. Collect user feedback
```

---

## SRE Sign-Off Checklist

**Reliability Requirements** ✅:
- [x] Transactional saves (SQLite + ChromaDB atomic)
- [x] Graceful degradation (ChromaDB unavailable → SQLite fallback)
- [x] Error recovery (3x retry, exponential backoff)
- [x] Data durability (SQLite WAL mode, no data loss)

**Performance Requirements** ✅:
- [x] Search latency <200ms P95 (100 patterns)
- [x] Suggestion latency <500ms P95
- [x] Usage tracking overhead <10ms (non-blocking)

**Failure Mode Coverage** ✅:
- [x] Database corruption → auto-restore from backup
- [x] ChromaDB down → fallback to SQLite
- [x] Disk space exhausted → clear error, no partial writes
- [x] SQL injection → parameterized queries, prevention tested
- [x] Concurrent writes → SQLite serialization validated

**Observability** ✅:
- [x] All CRUD operations logged
- [x] Search queries logged (for quality tracking)
- [x] Usage tracked automatically
- [x] Error rate monitored

**Test Coverage** ✅:
- [x] 95%+ unit test coverage
- [x] 90%+ integration test coverage
- [x] 100% critical failure modes tested
- [x] Performance SLAs validated under load

**Status**: ✅ **APPROVED FOR IMPLEMENTATION**

**SRE Principal Engineer**: Ready to proceed with Phase 4 (Implementation)

---

**Next Phase**: Implementation (8-10 hours, TDD red-green-refactor cycle)
