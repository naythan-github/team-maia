# Smart Context Loader Reliability Enhancement - TDD Requirements

**Project**: Smart Loader Reliability Enhancement (Phase 177)
**Created**: 2025-11-23
**Agent Pairing**: SRE Principal Engineer Agent (primary)
**Status**: Requirements Discovery

---

## 1. Problem Statement

### Current State
The Smart Context Loader has multiple reliability issues:

1. **Capability Amnesia**: `capability_index.md` (31K tokens) exceeds Read tool limit (25K), causing complete failure
2. **Performance Bug**: `_get_recent_phases()` reads full 2.1MB markdown even when DB available
3. **Stale Mappings**: Hardcoded phase numbers (2, 107-111, 103-105) frozen at Phase 111; 55+ new phases unmapped
4. **No Guaranteed Minimum**: If all loading fails, Maia has zero context awareness
5. **CLAUDE.md Drift**: Instructions reference deprecated patterns (raw markdown load)

### Impact
- Maia rebuilds existing tools (capability amnesia)
- Slow context loading (100-500ms instead of <1ms)
- Wrong phases loaded for new domains
- No fallback when primary loading fails

---

## 2. Success Criteria

| Metric | Current | Target | Validation |
|--------|---------|--------|------------|
| Capability awareness | 0% (31K > 25K limit) | 100% | Summary always loads |
| Context load time (DB path) | 100-500ms | <10ms | Benchmark tests |
| Phase mapping coverage | 65% (111/170) | 100% | Dynamic DB search |
| Fallback reliability | Undefined | 100% | Graceful degradation tests |
| Token overhead (baseline) | 31K (fails) | <200 tokens | Guaranteed minimum |

---

## 3. Functional Requirements

### FR-1: Guaranteed Minimum Context (CRITICAL)
**Purpose**: Ensure Maia ALWAYS has basic awareness, even if all other loading fails

**Requirements**:
- FR-1.1: `load_guaranteed_minimum()` method always succeeds (no exceptions)
- FR-1.2: Returns capability summary (counts by type/category) in <100 tokens
- FR-1.3: Returns recent phase titles (last 5) in <100 tokens
- FR-1.4: Total output <200 tokens
- FR-1.5: Works with DB unavailable (hardcoded fallback)
- FR-1.6: Works with markdown unavailable (minimal static fallback)
- FR-1.7: Execution time <50ms even in fallback mode

**Acceptance Criteria**:
```python
def test_guaranteed_minimum_always_succeeds():
    # Even with no DB, no markdown, no network
    loader = SmartContextLoader(maia_root="/nonexistent")
    result = loader.load_guaranteed_minimum()
    assert result is not None
    assert len(result) > 0
    assert len(result) // 4 < 200  # Token estimate
```

---

### FR-2: DB-First Phase Discovery
**Purpose**: Eliminate performance bug in `_get_recent_phases()`

**Requirements**:
- FR-2.1: Use `SystemStateQueries.get_recent_phase_numbers()` when DB available
- FR-2.2: Fall back to markdown parsing only when DB unavailable
- FR-2.3: Cache phase numbers for session (avoid repeated queries)
- FR-2.4: Query time <5ms for DB path

**Acceptance Criteria**:
```python
def test_get_recent_phases_uses_db():
    loader = SmartContextLoader()
    if loader.use_database:
        start = time.perf_counter()
        phases = loader._get_recent_phases(10)
        elapsed = time.perf_counter() - start
        assert elapsed < 0.005  # 5ms
        assert len(phases) == 10
```

---

### FR-3: Dynamic Strategy Selection
**Purpose**: Replace hardcoded phase mappings with DB-driven search

**Requirements**:
- FR-3.1: Extract keywords from user query
- FR-3.2: Search phase titles/narratives in DB for matching keywords
- FR-3.3: Return matching phases (up to 10) sorted by relevance
- FR-3.4: Fall back to recent phases if no matches
- FR-3.5: Preserve existing strategies as keyword hints (not hardcoded phases)

**Acceptance Criteria**:
```python
def test_dynamic_strategy_finds_database_phases():
    loader = SmartContextLoader()
    # Query about databases should find Phases 164-168
    result = loader.load_for_intent("database integration performance")
    assert any(p in result.phases_loaded for p in [164, 165, 166, 167, 168])

def test_dynamic_strategy_finds_agent_phases():
    loader = SmartContextLoader()
    # Query about agents should find recent agent phases, not just 107-111
    result = loader.load_for_intent("agent enhancement routing")
    assert any(p > 130 for p in result.phases_loaded)  # Should include Phase 134+
```

---

### FR-4: Tiered Loading Architecture
**Purpose**: Progressive context loading based on need

**Requirements**:
- FR-4.1: Tier 0 (Guaranteed) - Always loads, ~160 tokens
- FR-4.2: Tier 1 (Intent-Matched) - Loads when query matches domain, 2-5K tokens
- FR-4.3: Tier 2 (Deep Context) - Loads on explicit request or high complexity, 10-20K tokens
- FR-4.4: Each tier includes all lower tiers
- FR-4.5: Token budget enforced at each tier

**Acceptance Criteria**:
```python
def test_tier_0_always_included():
    loader = SmartContextLoader()
    result = loader.load_for_intent("simple question")
    # Tier 0 content (summary) should be present
    assert "Capabilities:" in result.content or "capabilities" in result.content.lower()

def test_tier_2_includes_lower_tiers():
    loader = SmartContextLoader()
    result = loader.load_for_intent("complex strategic planning for system redesign")
    # Should have both summary AND detailed phases
    assert result.token_count > 5000  # Tier 2 budget
    assert len(result.phases_loaded) >= 10  # Significant context
```

---

### FR-5: Graceful Degradation
**Purpose**: System remains functional under partial failures

**Requirements**:
- FR-5.1: DB unavailable → Use markdown with warning logged
- FR-5.2: Markdown unavailable → Use cached/static data with warning
- FR-5.3: Both unavailable → Return guaranteed minimum (never empty)
- FR-5.4: Partial DB data → Supplement with markdown for missing phases
- FR-5.5: All failures logged with severity levels

**Acceptance Criteria**:
```python
def test_graceful_degradation_db_failure():
    loader = SmartContextLoader()
    loader.use_database = False  # Simulate DB failure
    result = loader.load_for_intent("any query")
    assert result.content is not None
    assert result.loading_strategy.endswith("_fallback") or result.loading_strategy == "default"

def test_graceful_degradation_total_failure():
    loader = SmartContextLoader(maia_root="/nonexistent")
    result = loader.load_guaranteed_minimum()
    assert "Capabilities" in result  # Static fallback
```

---

## 4. Non-Functional Requirements

### NFR-1: Performance
- Context load time (DB): <10ms P95
- Context load time (markdown fallback): <500ms P95
- Guaranteed minimum: <50ms P99
- Memory overhead: <50MB additional

### NFR-2: Reliability
- Availability: 100% (guaranteed minimum ensures no complete failures)
- Fallback success rate: 100%
- Error logging: All failures captured with context

### NFR-3: Observability
- Log: Strategy selected, phases loaded, token count, load time
- Metrics: Load time histogram, fallback trigger rate, strategy distribution
- Alerts: Fallback trigger rate >10% → investigate

### NFR-4: Maintainability
- No hardcoded phase numbers (all dynamic)
- Clear separation: DB queries vs markdown parsing vs fallback
- Comprehensive test coverage: >90%

---

## 5. Implementation Phases

### Phase 1: Fix _get_recent_phases() Performance Bug
**Effort**: 30 minutes
**Risk**: Low

**Changes**:
1. Add `get_recent_phase_numbers()` to `SystemStateQueries`
2. Modify `_get_recent_phases()` to use DB when available
3. Add caching for phase numbers (session-level)

**Tests**:
- `test_get_recent_phases_uses_db()`
- `test_get_recent_phases_fallback_to_markdown()`
- `test_get_recent_phases_performance()`
- `test_get_recent_phases_caching()`

**Files Modified**:
- `claude/tools/sre/system_state_queries.py` (+15 lines)
- `claude/tools/sre/smart_context_loader.py` (+20 lines)

---

### Phase 2: Implement Guaranteed Minimum Context
**Effort**: 45 minutes
**Risk**: Low

**Changes**:
1. Add `load_guaranteed_minimum()` method
2. Add `_get_capability_summary_safe()` with fallback
3. Add `_get_recent_phase_titles()` method
4. Add static fallback data for total failure scenario

**Tests**:
- `test_guaranteed_minimum_always_succeeds()`
- `test_guaranteed_minimum_token_budget()`
- `test_guaranteed_minimum_db_unavailable()`
- `test_guaranteed_minimum_total_failure()`
- `test_guaranteed_minimum_performance()`

**Files Modified**:
- `claude/tools/sre/smart_context_loader.py` (+60 lines)

---

### Phase 3: Replace Hardcoded Strategies with DB Search
**Effort**: 1 hour
**Risk**: Medium

**Changes**:
1. Add `search_phases_by_keywords()` to `SystemStateQueries`
2. Modify `_determine_strategy()` to use DB search
3. Keep keyword hints for domain detection, remove hardcoded phase numbers
4. Add relevance scoring for search results

**Tests**:
- `test_dynamic_strategy_finds_database_phases()`
- `test_dynamic_strategy_finds_agent_phases()`
- `test_dynamic_strategy_finds_sre_phases()`
- `test_dynamic_strategy_fallback_to_recent()`
- `test_dynamic_strategy_no_stale_mappings()`

**Files Modified**:
- `claude/tools/sre/system_state_queries.py` (+40 lines)
- `claude/tools/sre/smart_context_loader.py` (+50 lines, -30 lines hardcoded)

---

### Phase 4: Implement Tiered Loading
**Effort**: 45 minutes
**Risk**: Low

**Changes**:
1. Refactor `load_for_intent()` to use tiered architecture
2. Add `_load_tier_0()`, `_load_tier_1()`, `_load_tier_2()` methods
3. Ensure each tier includes lower tiers
4. Add tier selection logic based on complexity

**Tests**:
- `test_tier_0_always_included()`
- `test_tier_1_intent_matched()`
- `test_tier_2_deep_context()`
- `test_tier_2_includes_lower_tiers()`
- `test_tier_selection_by_complexity()`

**Files Modified**:
- `claude/tools/sre/smart_context_loader.py` (+80 lines)

---

### Phase 5: Update CLAUDE.md Instructions
**Effort**: 15 minutes
**Risk**: Low

**Changes**:
1. Remove reference to raw `capability_index.md` loading
2. Add reference to `load_guaranteed_minimum()`
3. Update Layer 1 description
4. Document new loading architecture

**Tests**:
- Manual verification of CLAUDE.md accuracy
- Validate no references to deprecated patterns

**Files Modified**:
- `CLAUDE.md` (~20 lines modified)

---

### Phase 6: Integration Testing & Documentation
**Effort**: 30 minutes
**Risk**: Low

**Changes**:
1. End-to-end integration tests
2. Performance benchmarks
3. Update capability_index.md with new methods
4. Create progress tracker for Phase 177

**Tests**:
- `test_full_loading_workflow()`
- `test_performance_benchmarks()`
- `test_fallback_chain()`

**Files Created**:
- `claude/tools/sre/test_smart_loader_reliability.py` (new test file)
- `claude/data/project_status/active/SMART_LOADER_RELIABILITY_progress.md`

---

## 6. Test Matrix

| Test ID | Requirement | Phase | Priority |
|---------|-------------|-------|----------|
| T-1.1 | FR-1.1: guaranteed_minimum always succeeds | 2 | P0 |
| T-1.2 | FR-1.2: capability summary <100 tokens | 2 | P0 |
| T-1.3 | FR-1.5: works without DB | 2 | P0 |
| T-1.4 | FR-1.6: works without markdown | 2 | P0 |
| T-1.5 | FR-1.7: execution <50ms | 2 | P1 |
| T-2.1 | FR-2.1: uses DB for phase discovery | 1 | P0 |
| T-2.2 | FR-2.2: fallback to markdown | 1 | P0 |
| T-2.3 | FR-2.4: query time <5ms | 1 | P1 |
| T-3.1 | FR-3.2: DB search for phases | 3 | P0 |
| T-3.2 | FR-3.3: returns matching phases | 3 | P0 |
| T-3.3 | FR-3.4: fallback to recent | 3 | P0 |
| T-4.1 | FR-4.1: Tier 0 always loads | 4 | P0 |
| T-4.2 | FR-4.4: Tier 2 includes lower | 4 | P1 |
| T-5.1 | FR-5.1: DB failure graceful | 2 | P0 |
| T-5.2 | FR-5.3: total failure returns minimum | 2 | P0 |

**Total Tests**: 15 core tests + integration tests
**Coverage Target**: 90%+

---

## 7. Rollback Plan

If issues discovered post-deployment:

1. **Revert smart_context_loader.py** to previous version
2. **Keep DB query improvements** (backward compatible)
3. **CLAUDE.md can remain** (references both old and new patterns)

**Rollback Trigger**:
- Fallback rate >20% in production
- Load time regression >2x
- Any complete loading failures

---

## 8. Dependencies

| Dependency | Status | Notes |
|------------|--------|-------|
| system_state.db | ✅ Available | 60 phases, 100% coverage |
| capabilities.db | ✅ Available | Full registry |
| SystemStateQueries | ✅ Available | May need minor extension |
| CapabilitiesRegistry | ✅ Available | No changes needed |

---

## 9. Sign-Off

- [ ] Requirements complete (user confirmation)
- [ ] Test cases reviewed
- [ ] Implementation phases approved
- [ ] Rollback plan acceptable

---

*Document Version: 1.0*
*Last Updated: 2025-11-23*
*Agent: SRE Principal Engineer Agent*
