# Phase 141.1: Data Analyst Agent Integration - TDD Project Plan

**Project**: Hybrid Auto-Pattern Integration (Option C)
**Methodology**: Test-Driven Development (TDD)
**Agent Pairing**: Data Analyst Agent + SRE Principal Engineer Agent
**Created**: 2025-10-30
**Status**: PLANNING - TDD Requirements

---

## Executive Summary

**Goal**: Integrate Analysis Pattern Library with Data Analyst Agent for automatic pattern checking and user-controlled pattern saving.

**Approach**: Hybrid (Option C)
- ✅ Auto-check pattern library (silent)
- ✅ Auto-use if matched (silent, transparent)
- ✅ **Prompt to save** after successful ad-hoc analysis (user control)

**Expected Outcome**:
- 50% time reduction on repeat analyses (auto-use existing patterns)
- User stays in control (decides what to save)
- Transparent operation (user knows when patterns reused)

**Estimated Effort**: 3-4 hours (TDD implementation)

---

## Problem Statement

**Current State**: Pattern library operational but requires manual invocation
- User must explicitly call `lib.save_pattern()`
- No integration with Data Analyst Agent workflow
- Patterns not automatically detected or used
- No prompts to save successful analyses

**Desired State**: Seamless pattern integration
- Agent automatically checks for existing patterns
- Agent uses patterns when confidence >0.70
- Agent prompts to save successful ad-hoc analyses
- User retains control over what gets saved

---

## User Experience Design

### Scenario 1: No Pattern Exists (First Time)

```
User: "Show project hours for Olli Ojala and Alex Olver"

Maia: [Checks pattern library - no match]
      [Performs ad-hoc analysis]
      [Displays results - timesheet breakdown with 7.6 hrs/day format]

      💡 I noticed this analysis follows a clear pattern.
         Would you like me to save it for future use?
         Next time you ask similar questions, I'll use this format. (yes/no)

User: "yes"

Maia: ✅ Pattern saved as "Personnel Project Hours Analysis"

      Saved details:
      - SQL query with name substitution
      - Presentation: Top 5 + remaining + unaccounted
      - Business context: 7.6 hrs/day standard

      You can now ask similar questions and I'll use this pattern.
```

---

### Scenario 2: Pattern Exists (Subsequent Time)

```
User: "Show project hours for Sarah Chen and Bob Smith"

Maia: 🔍 Found matching pattern: "Personnel Project Hours Analysis" (confidence: 0.87)
      Using saved format for consistency...

      [Executes pattern with new names substituted]
      [Displays results in same format as before]

      📊 Sarah Chen - 245.30 hours total (44% of available 562.4 hrs)...
          Bob Smith - 189.75 hours total (34% of available 562.4 hrs)...

      ℹ️ Pattern used: Personnel Project Hours Analysis (used 2 times, 100% success)
```

---

### Scenario 3: Pattern Exists But User Declines to Use

```
User: "Show project hours but use 8 hours per day instead"

Maia: 🔍 Found matching pattern: "Personnel Project Hours Analysis" (confidence: 0.85)
      However, you've specified different requirements (8 hrs/day vs 7.6 hrs/day).

      Performing custom analysis...

      [Displays results with 8 hrs/day calculation]

      💡 Would you like to save this as a separate pattern? (yes/no)

User: "no"

Maia: ✅ Got it. I'll use the original pattern for standard queries.
```

---

### Scenario 4: Low Confidence Match

```
User: "Analyze employee productivity metrics"

Maia: 🔍 Found similar pattern: "Personnel Project Hours Analysis" (confidence: 0.62)
      This is somewhat related but not a strong match.

      Would you like to:
      1) Use the existing pattern and adapt it
      2) Perform a new analysis

User: "2"

Maia: [Performs new analysis]
      💡 Save this as a new pattern? (yes/no)
```

---

## Functional Requirements

### FR1: Pattern Auto-Check (Silent)

**User Story**: As a Data Analyst Agent, when a user asks an analytical question, I want to automatically check the pattern library so I can reuse proven approaches.

**Acceptance Criteria**:
- ✅ Check pattern library BEFORE performing analysis
- ✅ Use `suggest_pattern(user_question)` with confidence threshold 0.70
- ✅ Operation is silent (no user notification during check)
- ✅ Non-blocking (if check fails, continue with ad-hoc)
- ✅ Performance: <500ms overhead

**Edge Cases**:
- Pattern library unavailable → Continue with ad-hoc (graceful degradation)
- Multiple high-confidence matches → Use highest confidence
- Confidence exactly 0.70 → Use pattern (inclusive threshold)

---

### FR2: Pattern Auto-Use (Transparent)

**User Story**: As a user, when my question matches an existing pattern, I want the agent to automatically use it so I get consistent, fast results.

**Acceptance Criteria**:
- ✅ If confidence ≥0.70, use pattern automatically
- ✅ Notify user: "🔍 Found matching pattern: {name} (confidence: {score})"
- ✅ Extract variables from user question (e.g., names: "Olli", "Alex")
- ✅ Substitute variables in SQL template
- ✅ Use presentation format from pattern
- ✅ Track usage: `lib.track_usage(pattern_id, question, success=True)`
- ✅ Display pattern metadata: "Pattern used: {name} (used {count} times)"

**Edge Cases**:
- Variable extraction fails → Notify user, fall back to ad-hoc
- Pattern execution fails (SQL error) → Track failure, fall back to ad-hoc
- User question contains negation ("don't use the usual format") → Skip pattern

---

### FR3: Save Prompt After Ad-Hoc Analysis (User Control)

**User Story**: As a user, after a successful ad-hoc analysis, I want to be prompted to save it as a pattern so I can reuse it later.

**Acceptance Criteria**:
- ✅ Trigger: Ad-hoc analysis completed successfully
- ✅ Condition: No pattern was used (confidence <0.70)
- ✅ Prompt: "💡 Would you like to save this as a reusable pattern? (yes/no)"
- ✅ If YES: Extract metadata (SQL, format, context) and save
- ✅ If NO: Continue without saving
- ✅ Confirmation: "✅ Pattern saved as {name}"

**Metadata Extraction**:
- **SQL template**: Extract query used, replace specific values with {{placeholders}}
- **Presentation format**: Capture output structure description
- **Business context**: Extract key assumptions (e.g., "7.6 hrs/day")
- **Tags**: Auto-generate from domain + question type
- **Example input**: User's original question
- **Example output**: Summary of results (first 100 chars)

**Edge Cases**:
- User ignores prompt (no response) → Auto-timeout after 30s, assume NO
- Analysis failed → Don't prompt to save
- User says "yes" but metadata extraction fails → Notify user, offer manual save

---

### FR4: Pattern Metadata Display

**User Story**: As a user, when a pattern is used, I want to see which pattern and its usage stats so I understand what's happening.

**Acceptance Criteria**:
- ✅ Display after results: "ℹ️ Pattern used: {name} (used {count} times, {success_rate}% success)"
- ✅ Include confidence score when pattern matched
- ✅ Link to pattern details (if user wants to update/delete)

---

### FR5: Pattern Override Capability

**User Story**: As a user, I want to override pattern usage when my requirements differ so I maintain control.

**Acceptance Criteria**:
- ✅ Detect override signals: "don't use the usual format", "use 8 hours per day", "custom analysis"
- ✅ Skip pattern when override detected
- ✅ Notify: "Performing custom analysis as requested..."
- ✅ Still prompt to save as new pattern if successful

---

## Non-Functional Requirements

### NFR1: Performance

- Pattern check: <500ms overhead
- Variable extraction: <200ms
- Total overhead: <1 second (acceptable for 50% time savings on pattern reuse)

### NFR2: Reliability

- Pattern library unavailable → Graceful degradation (ad-hoc continues)
- Pattern execution fails → Track failure, fall back to ad-hoc
- Non-blocking errors (don't fail entire analysis if pattern check fails)

### NFR3: User Experience

- Clear, concise prompts (≤2 sentences)
- Transparent operation (user knows when patterns used)
- Respectful of user's time (prompts are optional, auto-timeout)

---

## Technical Design

### Architecture

```
User Question
      ↓
Data Analyst Agent (entry point)
      ↓
[Check Pattern Library] ← suggest_pattern(question)
      ↓
   Match?
   ├─ YES (confidence ≥0.70)
   │    ↓
   │  [Use Pattern]
   │    ├─ Extract variables
   │    ├─ Substitute in SQL
   │    ├─ Execute query
   │    ├─ Format results
   │    ├─ Track usage
   │    └─ Display with metadata
   │
   └─ NO (confidence <0.70)
        ↓
      [Ad-Hoc Analysis]
        ↓
      Success?
        ├─ YES
        │    ↓
        │  [Prompt to Save]
        │    ├─ User says YES
        │    │   ↓
        │    │ [Extract Metadata]
        │    │   ↓
        │    │ [Save Pattern]
        │    │   ↓
        │    │ Confirmation
        │    │
        │    └─ User says NO
        │        ↓
        │      Continue
        │
        └─ NO
            ↓
          Don't prompt
```

---

### Data Analyst Agent Modifications

**File**: `claude/agents/data_analyst_agent.md`

**Changes Required**:
1. Import pattern library at agent initialization
2. Add pattern check before analysis
3. Add pattern execution logic
4. Add save prompt after ad-hoc analysis
5. Add variable extraction helper
6. Add metadata extraction helper

**Estimated Changes**: ~200 lines of modifications

---

### Pattern Variable Extraction

**Challenge**: Extract names/dates/values from user questions

**Approach**: Simple regex + keyword matching
```python
def extract_variables(user_question: str, pattern: dict) -> dict:
    """
    Extract variable values from user question.

    Returns: {'names': ['Olli Ojala', 'Alex Olver'], ...}
    """
    variables = {}

    # Extract names (for {{names}} placeholder)
    if '{{names}}' in pattern['sql_template']:
        # Pattern: "for {Name} and {Name}"
        names = re.findall(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', user_question)
        variables['names'] = names

    # Extract dates (for {{start_date}}, {{end_date}})
    if '{{start_date}}' in pattern['sql_template']:
        # Pattern: "from {date} to {date}"
        dates = extract_dates(user_question)
        variables['start_date'] = dates[0] if dates else None
        variables['end_date'] = dates[1] if len(dates) > 1 else None

    return variables
```

---

### Pattern Metadata Extraction

**Challenge**: Extract metadata from ad-hoc analysis results

**Approach**: Capture during analysis execution
```python
def extract_pattern_metadata(analysis_context: dict) -> dict:
    """
    Extract metadata from successful ad-hoc analysis.

    Args:
        analysis_context: {
            'sql_query': "SELECT...",
            'user_question': "Show hours for...",
            'result_format': "Top 5 + remaining",
            'business_rules': ["7.6 hrs/day", ...],
            'output_sample': "Alex: 287 hrs..."
        }

    Returns:
        Pattern metadata dict ready for save_pattern()
    """
    # Replace specific values with placeholders
    sql_template = templatize_sql(analysis_context['sql_query'])

    # Extract domain from question
    domain = infer_domain(analysis_context['user_question'])

    # Generate pattern name
    pattern_name = generate_pattern_name(domain, analysis_context['user_question'])

    return {
        'pattern_name': pattern_name,
        'domain': domain,
        'question_type': infer_question_type(analysis_context),
        'description': generate_description(analysis_context),
        'sql_template': sql_template,
        'presentation_format': analysis_context['result_format'],
        'business_context': '; '.join(analysis_context['business_rules']),
        'example_input': analysis_context['user_question'],
        'example_output': analysis_context['output_sample'][:200],
        'tags': generate_tags(domain, analysis_context)
    }
```

---

## TDD Test Plan

### Test Suite 1: Pattern Auto-Check (8 tests)

**Test 1.1**: `test_agent_checks_pattern_before_analysis`
- Agent receives question → calls `suggest_pattern()` before proceeding
- Assert: `suggest_pattern()` was called

**Test 1.2**: `test_agent_uses_high_confidence_pattern`
- Pattern exists (confidence 0.85) → Agent uses pattern
- Assert: Pattern executed, ad-hoc skipped

**Test 1.3**: `test_agent_skips_low_confidence_pattern`
- Pattern exists (confidence 0.50) → Agent performs ad-hoc
- Assert: Pattern not used, ad-hoc executed

**Test 1.4**: `test_agent_handles_pattern_library_unavailable`
- Pattern library raises exception → Agent continues with ad-hoc
- Assert: Ad-hoc analysis completed, no error raised

**Test 1.5**: `test_agent_notifies_user_of_pattern_match`
- Pattern matched (confidence 0.80) → User sees notification
- Assert: Output contains "Found matching pattern: {name}"

**Test 1.6**: `test_pattern_check_performance`
- Pattern check completes in <500ms
- Assert: Latency measurement <500ms

**Test 1.7**: `test_multiple_patterns_selects_highest_confidence`
- 2 patterns match (0.75, 0.85) → Agent uses 0.85 pattern
- Assert: Higher confidence pattern selected

**Test 1.8**: `test_pattern_check_is_silent_on_no_match`
- No pattern matches → No notification shown
- Assert: Output does NOT contain pattern-related messages

---

### Test Suite 2: Pattern Auto-Use (10 tests)

**Test 2.1**: `test_variable_extraction_for_names`
- User: "Show hours for Olli Ojala and Alex Olver"
- Assert: Extracted names = ['Olli Ojala', 'Alex Olver']

**Test 2.2**: `test_variable_substitution_in_sql`
- Names extracted → SQL WHERE clause updated
- Assert: SQL contains "WHERE name IN ('Olli Ojala', 'Alex Olver')"

**Test 2.3**: `test_pattern_execution_tracks_usage`
- Pattern used successfully → Usage tracked
- Assert: `track_usage()` called with success=True

**Test 2.4**: `test_pattern_execution_failure_fallback`
- Pattern SQL fails (column not found) → Falls back to ad-hoc
- Assert: Ad-hoc analysis completed, failure tracked

**Test 2.5**: `test_presentation_format_applied`
- Pattern has format "Top 5 + remaining" → Output matches format
- Assert: Output structure matches pattern specification

**Test 2.6**: `test_business_context_preserved`
- Pattern has context "7.6 hrs/day" → Results use 7.6 hrs/day
- Assert: Calculation uses correct hours/day

**Test 2.7**: `test_pattern_metadata_displayed`
- Pattern used → Metadata shown to user
- Assert: Output contains "Pattern used: {name} (used {count} times)"

**Test 2.8**: `test_variable_extraction_failure_fallback`
- Cannot extract names from question → Falls back to ad-hoc
- Assert: User notified, ad-hoc proceeds

**Test 2.9**: `test_pattern_override_detection`
- User says "don't use usual format" → Pattern skipped
- Assert: Ad-hoc analysis performed

**Test 2.10**: `test_pattern_reuse_performance`
- Pattern reuse is faster than ad-hoc (>30% time reduction)
- Assert: Pattern execution time < ad-hoc baseline

---

### Test Suite 3: Save Prompt (12 tests)

**Test 3.1**: `test_prompt_shown_after_adhoc_success`
- Ad-hoc analysis succeeds → Prompt shown
- Assert: Output contains "Would you like to save this as a reusable pattern?"

**Test 3.2**: `test_prompt_not_shown_after_pattern_use`
- Pattern used (not ad-hoc) → No prompt
- Assert: Save prompt NOT shown

**Test 3.3**: `test_prompt_not_shown_after_adhoc_failure`
- Ad-hoc analysis fails → No prompt
- Assert: Save prompt NOT shown

**Test 3.4**: `test_user_says_yes_pattern_saved`
- User responds "yes" → Pattern saved
- Assert: `save_pattern()` called, confirmation shown

**Test 3.5**: `test_user_says_no_pattern_not_saved`
- User responds "no" → Pattern NOT saved
- Assert: `save_pattern()` NOT called

**Test 3.6**: `test_metadata_extraction_success`
- Ad-hoc analysis → Metadata extracted correctly
- Assert: SQL templatized, context captured, tags generated

**Test 3.7**: `test_sql_templatization`
- SQL "WHERE name IN ('Olli', 'Alex')" → "WHERE name IN ({{names}})"
- Assert: Specific values replaced with placeholders

**Test 3.8**: `test_pattern_name_generation`
- Question about timesheets → Pattern name includes "Timesheet"
- Assert: Generated name is descriptive

**Test 3.9**: `test_domain_inference`
- ServiceDesk-related question → Domain = "servicedesk"
- Assert: Domain correctly inferred

**Test 3.10**: `test_tags_auto_generation`
- Timesheet analysis → Tags include ["timesheet", "hours", "projects"]
- Assert: Relevant tags generated

**Test 3.11**: `test_prompt_timeout`
- User doesn't respond for 30s → Assumes NO
- Assert: Pattern NOT saved, analysis continues

**Test 3.12**: `test_metadata_extraction_failure_graceful`
- Cannot extract metadata → User notified, offer manual save
- Assert: Error handled gracefully, no crash

---

### Test Suite 4: End-to-End Scenarios (5 tests)

**Test 4.1**: `test_e2e_first_time_user_saves_pattern`
- Complete workflow: Question → Ad-hoc → Prompt → Save → Confirmation
- Assert: Pattern saved, usable in future

**Test 4.2**: `test_e2e_second_time_pattern_reused`
- First: Save pattern | Second: Same question → Pattern used
- Assert: Pattern matched, executed, 50% faster

**Test 4.3**: `test_e2e_low_confidence_user_chooses_adhoc`
- Pattern exists (0.62 confidence) → User chooses ad-hoc → New pattern saved
- Assert: 2 patterns in library (original + new)

**Test 4.4**: `test_e2e_pattern_fails_fallback_works`
- Pattern matched → SQL fails → Ad-hoc succeeds → Failure tracked
- Assert: Results delivered, pattern marked as failed

**Test 4.5**: `test_e2e_user_overrides_pattern`
- Pattern exists → User says "custom analysis" → Ad-hoc performed → User declines save
- Assert: Original pattern preserved, no new pattern

---

## Implementation Phases

### Phase 1: Core Integration (2 hours)
- Modify Data Analyst Agent to check pattern library
- Implement pattern auto-use logic
- Write 8 tests (pattern auto-check)
- **Deliverable**: Agent checks patterns, uses if matched

### Phase 2: Save Prompting (1.5 hours)
- Implement save prompt after ad-hoc
- Implement metadata extraction
- Write 12 tests (save prompt suite)
- **Deliverable**: Users prompted to save successful analyses

### Phase 3: Variable Extraction (1 hour)
- Implement name extraction
- Implement date extraction
- Write 10 tests (pattern auto-use suite)
- **Deliverable**: Variables extracted and substituted

### Phase 4: E2E Testing (0.5 hours)
- Write 5 E2E tests
- Validate complete workflows
- **Deliverable**: All scenarios tested end-to-end

**Total**: 3-4 hours

---

## Success Metrics

**Immediate (Week 1)**:
- ✅ 35/35 tests passing (100%)
- ✅ Agent integration operational
- ✅ User prompted to save patterns
- ✅ Pattern reuse working

**Short-term (Month 1)**:
- ✅ 5+ patterns saved by user
- ✅ 50% time reduction measured on repeat analyses
- ✅ Pattern usage tracked (10+ reuses)

**Long-term (Quarter 1)**:
- ✅ 20+ patterns in library
- ✅ 80% of repeat questions use patterns
- ✅ User satisfaction: "Maia remembers how I like my analyses"

---

## Risk Analysis

**Risk 1: Metadata Extraction Accuracy** (Medium probability, Medium impact)
- **Scenario**: Cannot accurately extract SQL template variables
- **Mitigation**: Start with simple patterns (names only), expand gradually
- **Contingency**: Offer manual metadata editing

**Risk 2: User Prompt Fatigue** (High probability, Low impact)
- **Scenario**: User annoyed by frequent save prompts
- **Mitigation**: Only prompt once per unique analysis type
- **Contingency**: Add "don't ask again for this type" option

**Risk 3: Variable Extraction False Positives** (Medium probability, High impact)
- **Scenario**: Extract wrong values from question ("Alex" company name vs "Alex" person)
- **Mitigation**: Context-aware extraction, show extracted values for confirmation
- **Contingency**: Validation prompt "I'll use these values: [X, Y, Z]. Correct?"

**Risk 4: Pattern Execution Failures** (Low probability, Medium impact)
- **Scenario**: Saved pattern SQL breaks when schema changes
- **Mitigation**: Graceful fallback to ad-hoc, track failures
- **Contingency**: Pattern deprecation workflow (auto-disable after 3 failures)

---

## Rollback Plan

**If integration causes issues**:
1. Feature flag: `ENABLE_PATTERN_INTEGRATION = False`
2. Agent reverts to pure ad-hoc (no pattern checking)
3. Pattern library remains operational for manual use
4. Total rollback time: <5 minutes (config change)

---

## Next Steps

**Upon Approval**:
1. ✅ Create TDD test specifications (this document)
2. ⏳ Write 35 tests (red phase)
3. ⏳ Implement integration (green phase)
4. ⏳ Refactor for quality
5. ⏳ Document user guide
6. ⏳ Update SYSTEM_STATE.md

**Status**: ✅ **TDD PLAN COMPLETE** - Ready for test writing (Phase 1)

---

**Prepared By**: SRE Principal Engineer Agent
**Date**: 2025-10-30
**Estimated Delivery**: Phase 141.1 complete in 3-4 hours with TDD methodology
