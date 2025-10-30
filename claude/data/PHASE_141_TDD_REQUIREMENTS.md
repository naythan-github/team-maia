# Phase 141: Analysis Pattern Library - TDD Requirements

**Project**: Global Analysis Pattern Library
**Methodology**: Test-Driven Development (TDD)
**Agent Pairing**: Data Analyst Agent (Domain Specialist) + SRE Principal Engineer Agent
**Created**: 2025-10-30
**Status**: REQUIREMENTS DISCOVERY

---

## TDD Workflow Overview

Following `claude/context/core/tdd_development_protocol.md`:

**Phase 1**: Requirements Discovery (SRE defines reliability requirements) ✅ THIS DOCUMENT
**Phase 2**: Requirements Documentation (complete functional + non-functional specs)
**Phase 3**: Test Design (SRE validates failure mode coverage)
**Phase 4**: Implementation (SRE collaborates + reviews)

---

## Phase 1: Requirements Discovery

### Functional Requirements

#### FR1: Pattern Storage
**User Story**: As a Data Analyst, I want to save proven analytical patterns so I can reuse them in future conversations.

**Acceptance Criteria**:
- ✅ Save pattern with: name, domain, question type, SQL template, presentation format, business context, example I/O, tags
- ✅ Auto-generate unique pattern_id (domain + question_type + timestamp)
- ✅ Store in SQLite database with full metadata
- ✅ Create ChromaDB embedding for semantic search
- ✅ Return pattern_id on successful save
- ✅ Validate required fields (name, domain, question_type, description)
- ✅ Handle duplicate pattern names (append version number)

**Edge Cases**:
- Empty/null required fields → ValidationError
- SQL template with invalid syntax → Warning (not blocking)
- Duplicate pattern_id → Append timestamp to ensure uniqueness
- Very long text fields (>10KB) → Truncate with warning

**SRE Reliability Requirements**:
- **Atomicity**: Save to SQLite + ChromaDB is transactional (both succeed or both fail)
- **Idempotency**: Saving same pattern twice creates new version, not duplicate
- **Data integrity**: Foreign key constraints enforced, no orphaned records
- **Error handling**: Graceful degradation if ChromaDB unavailable (save to SQLite only, queue embedding)

---

#### FR2: Pattern Retrieval
**User Story**: As a Data Analyst, I want to retrieve saved patterns by ID so I can use them in my analysis.

**Acceptance Criteria**:
- ✅ Retrieve pattern by exact pattern_id
- ✅ Return all metadata fields (name, SQL, format, context, etc.)
- ✅ Include usage statistics (total uses, last used, success rate)
- ✅ Return None if pattern not found (not exception)
- ✅ Exclude archived patterns by default (unless explicitly requested)

**Edge Cases**:
- Pattern doesn't exist → Return None
- Pattern archived → Return None (unless include_archived=True)
- Database connection lost → Retry 3x with exponential backoff, then raise error

**SRE Reliability Requirements**:
- **Availability**: <1s retrieval latency P95
- **Caching**: LRU cache for frequently accessed patterns (TTL: 5 minutes)
- **Monitoring**: Log retrieval errors for pattern not found (helps identify stale references)

---

#### FR3: Pattern Search (Semantic)
**User Story**: As a Data Analyst, I want to search for patterns using natural language so I can find relevant patterns without knowing exact IDs.

**Acceptance Criteria**:
- ✅ Accept natural language query ("show me project hours for employees")
- ✅ Return top-N matches ranked by similarity score (0-1)
- ✅ Filter by domain (optional)
- ✅ Filter by minimum similarity threshold (default: 0.75)
- ✅ Include similarity score in results
- ✅ Return empty list if no matches above threshold

**Edge Cases**:
- Empty query → Return all patterns (sorted by usage)
- Very short query (<3 words) → Lower threshold to 0.65 (more permissive)
- No matches above threshold → Return empty list (not error)
- ChromaDB unavailable → Fallback to SQLite full-text search (less semantic, but works)

**SRE Reliability Requirements**:
- **Latency**: <200ms P95 for search (100 patterns in database)
- **Scalability**: <500ms P95 for 1000 patterns
- **Fallback**: SQLite full-text search if ChromaDB fails (degraded mode)
- **Accuracy**: >85% user satisfaction (relevant pattern in top 3 results)

---

#### FR4: Pattern Auto-Suggestion
**User Story**: As a Data Analyst Agent, I want automatic pattern suggestions when analyzing user questions so I can reuse proven approaches without manual search.

**Acceptance Criteria**:
- ✅ Accept user's analytical question
- ✅ Search for matching patterns (semantic search)
- ✅ Return best match if confidence >0.80
- ✅ Return None if no high-confidence match
- ✅ Optionally auto-apply: substitute variables in SQL template
- ✅ Include confidence score, pattern metadata, and ready-to-execute SQL

**Variable Substitution Examples**:
```python
# Pattern SQL template
"SELECT ... WHERE \"TS-User Full Name\" IN ({{names}})"

# User question
"Show hours for Olli Ojala and Alex Olver"

# Auto-applied SQL
"SELECT ... WHERE \"TS-User Full Name\" IN ('Olli Ojala', 'Alex Olver')"
```

**Edge Cases**:
- Multiple high-confidence matches (>0.80) → Return top match, log ambiguity
- Confidence between 0.70-0.80 → Suggest but don't auto-apply
- Variable extraction fails → Return pattern with template (user fills manually)
- Domain mismatch → Lower confidence score by 0.1

**SRE Reliability Requirements**:
- **Latency**: <500ms P95 (search + variable extraction)
- **Accuracy**: >90% correct pattern suggestion for known question types
- **Safety**: SQL injection prevention (parameterized queries, no direct string substitution)
- **Observability**: Log all suggestions (question, pattern, confidence) for quality tracking

---

#### FR5: Pattern Listing
**User Story**: As a user, I want to list all saved patterns so I can browse available analytical approaches.

**Acceptance Criteria**:
- ✅ List all active patterns (exclude archived)
- ✅ Filter by domain (optional)
- ✅ Filter by question type (optional)
- ✅ Sort by: name, created_date, usage_count, last_used
- ✅ Return summary view (ID, name, domain, usage count)
- ✅ Pagination support (limit + offset)

**Edge Cases**:
- No patterns in database → Return empty list
- Invalid domain filter → Raise ValidationError
- Very large result set (>100 patterns) → Auto-paginate (limit=50 default)

**SRE Reliability Requirements**:
- **Performance**: <100ms for listing 100 patterns
- **Scalability**: <500ms for listing 1000 patterns (with pagination)

---

#### FR6: Pattern Update (Versioning)
**User Story**: As a Data Analyst, I want to update patterns while preserving version history so I can evolve patterns without losing previous versions.

**Acceptance Criteria**:
- ✅ Update any field (SQL, format, context, tags, etc.)
- ✅ Create new version (increment version number)
- ✅ Archive old version (status='deprecated')
- ✅ Link new version to previous version (version history chain)
- ✅ Update ChromaDB embedding with new content
- ✅ Return new pattern_id (e.g., v1 → v2)

**Edge Cases**:
- No changes detected → Return existing pattern_id (no new version)
- Pattern doesn't exist → Raise NotFoundError
- Concurrent updates → Last write wins (log conflict)

**SRE Reliability Requirements**:
- **Data preservation**: Old versions never deleted (only deprecated)
- **Atomicity**: Version creation is transactional (SQLite + ChromaDB both updated)
- **Audit trail**: Log who updated, when, what changed

---

#### FR7: Pattern Deletion (Soft Delete)
**User Story**: As a user, I want to delete obsolete patterns so the library stays clean and relevant.

**Acceptance Criteria**:
- ✅ Soft delete (set status='archived', don't remove from database)
- ✅ Archived patterns excluded from search/listing by default
- ✅ Can restore archived patterns (set status='active')
- ✅ Hard delete option (admin only, removes from database permanently)
- ✅ Cascade to usage records (mark as orphaned, don't delete)

**Edge Cases**:
- Pattern doesn't exist → Return False (not error)
- Pattern already archived → Idempotent (return True)
- Pattern has many usage records (>100) → Warn user before deletion

**SRE Reliability Requirements**:
- **Recoverability**: Soft delete allows undo (hard delete is irreversible)
- **Cleanup**: Hard delete also removes ChromaDB embeddings
- **Audit**: Log all deletions (who, when, pattern_id)

---

#### FR8: Usage Tracking
**User Story**: As a Data Analyst, I want to track pattern usage so I can identify the most valuable patterns.

**Acceptance Criteria**:
- ✅ Log every pattern use (pattern_id, question, timestamp, success)
- ✅ Calculate usage statistics (total uses, success rate, last used)
- ✅ Track feedback (optional user comments)
- ✅ Identify most-used patterns (top 10)
- ✅ Identify stale patterns (not used in 90+ days)

**Edge Cases**:
- Usage tracking fails → Don't block pattern execution (log error, continue)
- Very high usage (>1000 records) → Archive old usage records (>1 year old)

**SRE Reliability Requirements**:
- **Non-blocking**: Usage tracking failures don't impact pattern execution
- **Performance**: <10ms overhead for logging usage
- **Retention**: Keep usage records for 1 year, then archive

---

#### FR9: CLI Interface
**User Story**: As a user, I want a command-line interface so I can manage patterns without writing Python code.

**Acceptance Criteria**:
- ✅ Commands: save, search, list, show, update, delete, stats
- ✅ Help text for each command
- ✅ JSON output mode (for scripting)
- ✅ Verbose mode (detailed output)
- ✅ Dry-run mode (show what would happen, don't execute)

**Commands**:
```bash
# Save pattern
analysis-pattern save --name "X" --domain "Y" --sql-file "Z.sql"

# Search patterns
analysis-pattern search "show project hours"

# List patterns
analysis-pattern list --domain servicedesk --sort usage

# Show pattern details
analysis-pattern show pattern_id

# Update pattern
analysis-pattern update pattern_id --sql-file new.sql --change-note "Fixed bug"

# Delete pattern
analysis-pattern delete pattern_id

# Usage statistics
analysis-pattern stats --top 10
```

**SRE Reliability Requirements**:
- **Error messages**: Clear, actionable error messages (not stack traces)
- **Exit codes**: 0=success, 1=user error, 2=system error
- **Logging**: All CLI operations logged for audit

---

### Non-Functional Requirements

#### NFR1: Performance
- **Search latency**: <200ms P95 (100 patterns), <500ms P95 (1000 patterns)
- **Suggestion latency**: <500ms P95 (search + variable extraction)
- **Retrieval latency**: <100ms P95
- **Save latency**: <500ms P95 (SQLite + ChromaDB embedding)
- **Usage tracking overhead**: <10ms (non-blocking)

**Failure Mode**: If performance degrades beyond SLA:
- Enable query result caching (LRU, TTL: 5 min)
- Add database indexes on common query paths
- Implement ChromaDB batch embedding (reduces latency by 30%)

---

#### NFR2: Reliability
- **Availability**: 99.9% (downtime <43 min/month)
- **Data durability**: Zero data loss (SQLite WAL mode + backups)
- **Graceful degradation**: ChromaDB unavailable → fallback to SQLite full-text search
- **Error recovery**: 3x retry with exponential backoff on transient failures

**Failure Modes**:
1. **ChromaDB unavailable**: Fallback to SQLite, queue embeddings for later
2. **SQLite locked**: Retry 3x with backoff, then raise error
3. **Disk full**: Log error, alert user, prevent new saves
4. **Corrupted database**: Auto-restore from backup (last 24 hours)

---

#### NFR3: Scalability
- **Pattern capacity**: Support 1000+ patterns without performance degradation
- **Usage record capacity**: Support 10,000+ usage records (1 year retention)
- **Concurrent users**: Single-user system (Maia), no concurrency needed
- **Database size**: <100MB for 1000 patterns + usage records

**Scalability Plan** (if limits exceeded):
- **1000+ patterns**: Implement domain-based sharding (separate ChromaDB collections)
- **10K+ usage records**: Archive old records (>1 year) to separate table
- **100MB+ database**: Implement vacuum/compression, archive old versions

---

#### NFR4: Security
- **SQL injection prevention**: Parameterized queries only, no string concatenation
- **Access control**: Single-user system (file permissions: 0o600)
- **Sensitive data**: No PII stored in patterns (patterns are analytical templates, not data)
- **Audit trail**: All CRUD operations logged with timestamp

**Security Failure Modes**:
1. **SQL injection attempt**: Reject query, log security event
2. **Unauthorized file access**: Database files 0o600 permissions
3. **Malicious SQL template**: Warning (not blocking), require user review before execution

---

#### NFR5: Maintainability
- **Code coverage**: >90% test coverage (unit + integration)
- **Documentation**: Complete API reference + user guide
- **Logging**: Structured logging (JSON format) for all operations
- **Monitoring**: Key metrics tracked (search latency, success rate, usage count)

**Maintainability Requirements**:
- Clear error messages (actionable, not technical jargon)
- Type hints for all public APIs
- Docstrings for all public methods (Google style)
- Example code for all major use cases

---

#### NFR6: Observability
- **Metrics**: Search latency, suggestion accuracy, usage count, error rate
- **Logging**: All CRUD operations, search queries, suggestions, errors
- **Alerting**: Error rate >5% (log warning), database size >90% capacity (alert user)

**Key Observability Metrics**:
```python
{
    "pattern_library_metrics": {
        "total_patterns": 42,
        "active_patterns": 38,
        "archived_patterns": 4,
        "total_usage_count": 287,
        "search_latency_p95_ms": 145,
        "suggestion_latency_p95_ms": 320,
        "suggestion_accuracy_pct": 92.3,
        "error_rate_pct": 0.8
    }
}
```

---

### Data Quality Requirements

#### DQ1: Pattern Completeness
- **Required fields**: name, domain, question_type, description (validated on save)
- **Recommended fields**: sql_template, presentation_format, example_input (warnings if missing)
- **Optional fields**: business_context, example_output, tags

**Quality Checks**:
- SQL template is valid SQL (syntax check, not blocking)
- Tags are meaningful (no single-char tags, no duplicates)
- Description is descriptive (>20 characters)

---

#### DQ2: Search Relevance
- **Target**: >85% user satisfaction (relevant pattern in top 3 results)
- **Measurement**: Track user selection from search results
- **Improvement**: Retrain embeddings if accuracy <80%

**Quality Metrics**:
- Precision@3: % of searches where user's desired pattern is in top 3
- Mean Reciprocal Rank (MRR): Average rank of selected pattern
- Zero-result rate: % of searches with no results above threshold

---

#### DQ3: Pattern Freshness
- **Stale pattern detection**: Not used in 90+ days
- **Deprecation workflow**: Notify user, suggest archival or update
- **Version recency**: Flag patterns with deprecated SQL schemas

---

### Agent Integration Requirements

#### AI1: Data Analyst Agent Integration
**User Story**: As a Data Analyst Agent, I want automatic pattern suggestions integrated into my workflow so I can reuse proven approaches seamlessly.

**Integration Points**:
1. **Before analysis**: Check for matching pattern
2. **During analysis**: Use pattern if high confidence (>0.80)
3. **After analysis**: Track usage, log success/failure
4. **Ad-hoc success**: Offer to save new pattern

**Workflow**:
```python
def analyze_data(user_question: str):
    # 1. Check for existing pattern
    pattern_lib = AnalysisPatternLibrary()
    suggestion = pattern_lib.suggest_pattern(user_question, domain='servicedesk')

    if suggestion['matched'] and suggestion['confidence'] > 0.80:
        # 2. Use pattern
        result = execute_with_pattern(suggestion['pattern'], user_question)
        # 3. Track usage
        pattern_lib.track_usage(suggestion['pattern_id'], user_question, success=True)
        return result
    else:
        # 4. Perform ad-hoc analysis
        result = perform_new_analysis(user_question)
        # 5. Offer to save as new pattern (if successful)
        if result['success']:
            offer_to_save_pattern(user_question, result)
        return result
```

**SRE Requirements**:
- Pattern suggestion doesn't block agent (<500ms timeout)
- Usage tracking is async (doesn't slow down results)
- Fallback to ad-hoc if pattern fails (graceful degradation)

---

### Test Coverage Requirements

#### TC1: Unit Tests (Target: 95%+ coverage)
- **CRUD operations**: save, get, update, delete, list (15 tests)
- **Search**: semantic search, filtering, ranking (8 tests)
- **Auto-suggestion**: pattern matching, variable extraction (10 tests)
- **Usage tracking**: log usage, calculate stats (5 tests)
- **Versioning**: create version, version history (5 tests)
- **Edge cases**: empty DB, invalid input, null handling (10 tests)

**Total**: ~53 unit tests

---

#### TC2: Integration Tests (Target: 90%+ coverage)
- **SQLite + ChromaDB**: transactional saves, rollback on failure (3 tests)
- **Agent workflow**: end-to-end pattern suggestion → execution → tracking (5 tests)
- **CLI**: all commands working correctly (9 tests)
- **Performance**: latency SLAs under load (3 tests)
- **Failure modes**: ChromaDB down, SQLite locked, disk full (5 tests)

**Total**: ~25 integration tests

---

#### TC3: Performance Tests
- **Search latency**: 100 patterns → <200ms P95 (3 tests: best case, worst case, average)
- **Bulk insert**: 1000 patterns → <5 min (1 test)
- **Large result sets**: 1000 patterns → list/search still fast (2 tests)

**Total**: ~6 performance tests

---

#### TC4: Acceptance Tests
- **Timesheet pattern**: Save → search "project hours" → auto-suggest works (1 test)
- **Pattern reuse**: Use pattern 5x → usage stats accurate (1 test)
- **Pattern evolution**: Update pattern → new version created (1 test)

**Total**: ~3 acceptance tests

**Grand Total**: ~87 tests

---

## SRE Principal Engineer - Reliability Requirements Summary

### Critical Failure Modes to Test

1. **Database Corruption**
   - Test: Corrupt SQLite file → auto-restore from backup
   - Test: Corrupt ChromaDB collection → rebuild embeddings from SQLite

2. **ChromaDB Unavailable**
   - Test: ChromaDB down → fallback to SQLite full-text search (degraded mode)
   - Test: ChromaDB slow (>1s) → timeout, fallback to SQLite

3. **Concurrent Writes** (low priority for single-user Maia)
   - Test: Two saves at same time → both succeed (SQLite handles serialization)

4. **Disk Space Exhausted**
   - Test: Disk full → save fails gracefully, alerts user
   - Test: Database grows beyond threshold (100MB) → alert for cleanup

5. **SQL Injection**
   - Test: Malicious SQL template → blocked by parameterized queries
   - Test: User input with SQL chars → properly escaped

---

### Observability Requirements

**Metrics to Track**:
- Pattern library size (total patterns, active, archived)
- Usage statistics (total uses, avg uses per pattern, most-used patterns)
- Performance (search P50/P95/P99 latency, save latency, suggestion latency)
- Quality (suggestion accuracy, search relevance, zero-result rate)
- Errors (error rate, failure modes, recovery success rate)

**Logging Requirements**:
- All CRUD operations (who, what, when)
- All searches (query, results count, top result)
- All suggestions (question, pattern, confidence, used?)
- All errors (error type, context, recovery action)

**Alerting** (for future integration with monitoring):
- Error rate >5% (log warning)
- Search latency P95 >500ms (performance degradation)
- Database size >90MB (approaching capacity)
- Zero-result rate >20% (poor pattern coverage or search quality)

---

## Acceptance Criteria for Phase 141 Completion

### Must-Have (Blocking)
- ✅ Save timesheet pattern with all metadata
- ✅ Search "project hours" → returns timesheet pattern (similarity >0.80)
- ✅ Auto-suggest works for known question
- ✅ SQL variable substitution extracts names correctly
- ✅ Usage tracking increments on pattern use
- ✅ All 87 tests passing (95%+ coverage)
- ✅ Performance SLAs met (<200ms search, <500ms suggestion)
- ✅ Data Analyst Agent integration working end-to-end
- ✅ CLI commands working (save, search, list, show, stats)
- ✅ Documentation complete (API reference + user guide)

### Should-Have (Important)
- ✅ Pattern versioning working (v1 → v2)
- ✅ Soft delete (archive, restore)
- ✅ Domain filtering in search
- ✅ Graceful degradation (ChromaDB unavailable → SQLite fallback)
- ✅ Example patterns ready to import (timesheet, recruitment, financial)

### Nice-to-Have (Future)
- ⏳ Auto-save successful ad-hoc analyses as patterns
- ⏳ Pattern quality scoring (based on usage + success rate)
- ⏳ Pattern recommendations (suggest related patterns)
- ⏳ Export/import patterns (JSON format for sharing)

---

## Next Steps

**Phase 2**: Requirements Documentation ✅ COMPLETE (this document)
**Phase 3**: Test Design (SRE validates failure mode coverage)
**Phase 4**: Implementation (SRE collaborates + reviews)

**Ready for Test Design Phase** → Create `PHASE_141_TEST_DESIGN.md`
