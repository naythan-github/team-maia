# Updating v2 Agents to v2.2 (Enhanced) - Implementation Guide

**Purpose**: Guide for updating 5 existing v2 agents with advanced patterns from v2.2 template

---

## Agents to Update

1. **dns_specialist_agent_v2.md** (1,114 lines → target: ~450 lines)
2. **sre_principal_engineer_agent_v2.md** (986 lines → target: ~550 lines)
3. **azure_solutions_architect_agent_v2.md** (760 lines → target: ~420 lines)
4. **service_desk_manager_agent_v2.md** (1,272 lines → target: ~520 lines)
5. **ai_specialists_agent_v2.md** (1,272 lines → target: ~550 lines)

---

## What to Add (5 Advanced Patterns)

### 1. Self-Reflection & Review (Core Behavior Principles)

**Location**: After "3. Systematic Planning" in Core Behavior Principles section

**Add**:
```markdown
### 4. Self-Reflection & Review ⭐ ADVANCED PATTERN
**Core Principle**: Check your work before declaring done. Catch errors early.

**Self-Reflection Questions** (ask before completing):
- ✅ Did I fully address the user's request?
- ✅ Are there edge cases I missed?
- ✅ What could go wrong with this solution?
- ✅ Would this work if scaled 10x?

**Example**:
```
INITIAL RESULT:
[Domain-specific first solution]

SELF-REVIEW:
Wait - let me validate this:
- ❓ Did I test the configuration?
- ❓ Are there security implications?
- ❓ Will this handle production load?

OBSERVATION: [Identify gap - domain-specific issue]

REVISED RESULT:
[Improved solution with validation + monitoring]
```
```

**Estimated size**: +25 lines

---

### 2. Review Pattern in Few-Shot Example

**Location**: Add to ONE existing few-shot example (choose most complex one)

**Add to example**:
```markdown
SELF-REVIEW (before declaring done):
Wait - let me check this solution:
- ❓ Did I validate it works? [Check 1]
- ❓ Are there edge cases? [Check 2]
- ❓ Will this scale? [Check 3]

OBSERVATION: [Identify gap if any]

REVISED RESULT: [Enhanced solution addressing gaps]
```

**Estimated size**: +15 lines (added to existing example, not new section)

---

### 3. Prompt Chaining Guidance

**Location**: After problem-solving template, before Performance Metrics

**Add**:
```markdown
### When to Use Prompt Chaining ⭐ ADVANCED PATTERN

Break complex tasks into sequential subtasks when:
- Task has >4 distinct phases with different reasoning modes
- Each phase output feeds into next phase as input
- Too complex for single-turn resolution
- Requires switching between analysis → design → implementation

**Example**: [Domain-specific multi-stage workflow]
1. **Subtask 1**: [Stage 1 - data collection]
2. **Subtask 2**: [Stage 2 - analysis using data from #1]
3. **Subtask 3**: [Stage 3 - solution design using analysis from #2]
4. **Subtask 4**: [Stage 4 - implementation using design from #3]

Each subtask's output becomes the next subtask's input.
```

**Estimated size**: +20 lines

---

### 4. Explicit Handoff Declaration

**Location**: In "Integration Points" section, after "Handoff Triggers"

**Add**:
```markdown
### Explicit Handoff Declaration Pattern ⭐ ADVANCED PATTERN

When handing off to another agent, use this format:

```markdown
HANDOFF DECLARATION:
To: [target_agent_name]
Reason: [Why this agent is needed]
Context:
  - Work completed: [What I've accomplished]
  - Current state: [Where things stand]
  - Next steps: [What receiving agent should do]
  - Key data: {
      "[field1]": "[value1]",
      "[field2]": "[value2]",
      "status": "[current_status]"
    }
```

**Example - [Domain-Specific Handoff]**:
```markdown
HANDOFF DECLARATION:
To: [relevant_agent]
Reason: [Domain-specific reason]
Context:
  - Work completed: [Domain work done]
  - Current state: [Current status]
  - Next steps: [What next agent should do]
  - Key data: {
      "[domain_field]": "[domain_value]",
      "status": "phase_complete"
    }
```

This explicit format enables the orchestration layer to parse and route efficiently.
```

**Estimated size**: +30 lines

---

### 5. Test Frequently + Self-Reflection Checkpoint

**Location**: In "Problem-Solving Approach" template, Phase 3

**Modify Phase 3 from**:
```markdown
**Phase 3: [Resolution Phase] (<[timeframe])**
- [Key activity 1 - Implementation]
- [Key activity 2 - Validation]
- [Key activity 3 - Documentation]
```

**To**:
```markdown
**Phase 3: [Resolution & Validation] (<[timeframe])**
- [Key activity 1 - Implementation]
- [Key activity 2 - Testing] ⭐ **Test frequently** - Validate solution works
- **Self-Reflection Checkpoint** ⭐:
  - Did I fully address the request?
  - Are there edge cases I missed?
  - What could go wrong? (failure modes)
  - Would this scale to production?
- [Key activity 3 - Documentation]
```

**Estimated size**: +5 lines (modification, not addition)

---

## What to Remove (Size Reduction)

### Compress Core Behavior Principles

**Current size**: ~140 lines
**Target size**: ~80 lines
**Reduction**: -60 lines

**How**:
- Keep OpenAI's 3 reminders
- Add new #4 Self-Reflection (+25 lines)
- Remove verbose domain-specific examples (-85 lines)
- Net: -60 lines

### Reduce Few-Shot Examples

**Current**: 3-7 examples per agent (very verbose, 150-200 lines each)
**Target**: 2-3 examples (concise, 80-100 lines each)
**Reduction**: -200 to -400 lines depending on agent

**How**:
- Keep 1 straightforward + 1 complex ReACT example
- Add review pattern to complex example (+15 lines)
- Remove redundant examples
- Compress remaining examples (remove verbose explanations)

### Simplify Problem-Solving Templates

**Current**: 2-3 templates per agent
**Target**: 1 template with modifications
**Reduction**: -100 to -200 lines

**How**:
- Keep most essential template
- Add testing + self-reflection to Phase 3 (+5 lines)
- Remove redundant templates

---

## Total Size Impact Per Agent

**Additions**:
- Self-Reflection section: +25 lines
- Review in example: +15 lines (embedded in existing)
- Prompt Chaining: +20 lines
- Explicit Handoff: +30 lines
- Test Frequently: +5 lines (embedded in existing)
- **Total additions: ~95 lines**

**Reductions**:
- Core Behavior compression: -60 lines
- Few-shot reduction: -200 to -400 lines
- Problem-solving reduction: -100 to -200 lines
- **Total reductions: -360 to -660 lines**

**Net change**: -265 to -565 lines per agent (40-50% size reduction)

---

## Example: Azure Solutions Architect

**Current v2**: 760 lines

**Target v2.2**:
- Additions: +95 lines
- Reductions: -435 lines (estimated)
- **Result**: ~420 lines (45% reduction)

**Breakdown**:
- Core Behavior: 140 → 105 lines (add self-reflection, compress examples)
- Few-Shot: 3 examples (300 lines) → 2 examples with review (180 lines)
- Problem-Solving: 2 templates (150 lines) → 1 template with testing (80 lines)
- Handoff section: 30 → 60 lines (add explicit pattern)
- New section: Prompt Chaining (+20 lines)

---

## Implementation Checklist Per Agent

### Phase 1: Add Advanced Patterns
- [ ] Add Self-Reflection & Review to Core Behavior Principles
- [ ] Add review pattern to one complex few-shot example
- [ ] Add Prompt Chaining section after problem-solving
- [ ] Add Explicit Handoff Declaration to Integration Points
- [ ] Modify Phase 3 to include Test Frequently + Self-Reflection Checkpoint

### Phase 2: Compress Existing Content
- [ ] Compress Core Behavior Principles (remove verbose examples)
- [ ] Reduce few-shot examples from 3-7 to 2-3
- [ ] Compress remaining examples (80-100 lines each target)
- [ ] Keep only 1 problem-solving template (most essential)
- [ ] Remove duplicate/redundant content

### Phase 3: Validate
- [ ] Check all 5 patterns are present
- [ ] Verify target size achieved (400-550 lines based on complexity)
- [ ] Test with validation script
- [ ] Compare quality score vs v2

---

## Time Estimates

**Per agent**: 2-3 hours (careful editing to maintain quality)
**Total for 5 agents**: 10-15 hours

**Breakdown per agent**:
- Add patterns: 1 hour
- Compress/reduce: 1-1.5 hours
- Review/validate: 0.5 hour

---

## Recommendation

Given time constraints, **prioritize**:

1. **Immediate**: Update 1 agent completely (Azure - smallest, 760 lines) as reference
2. **Next session**: Update remaining 4 agents using Azure as template
3. **Testing**: Validate all 5 updated agents
4. **Decision**: Finalize v2.2 based on test results

This phased approach ensures quality without rushing.

---

## Automated Detection Script

Created: `test_v2_to_v2.2_migration.py`

Checks for:
- ✅ Self-Reflection & Review present
- ✅ Review pattern in at least one example
- ✅ Prompt Chaining section present
- ✅ Explicit Handoff Declaration present
- ✅ Test Frequently in problem-solving
- ✅ Target size achieved

Run on each updated agent to validate patterns added.
