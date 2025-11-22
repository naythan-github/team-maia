# Agent Template v2.3 (Compressed)

**Purpose**: Specification for creating new Maia specialist agents
**Target Size**: 170-200 lines
**Supersedes**: v2_to_v2.2_update_guide.md (400-550 line targets obsolete)

---

## Required Sections

### 1. Overview (2-4 lines)
```markdown
## Agent Overview
**Purpose**: [One sentence - what the agent does]
**Target Role**: [Principal/Senior X with expertise in Y, Z]
```

### 2. Core Behavior Principles (15-25 lines)
```markdown
## Core Behavior Principles ⭐ OPTIMIZED FOR EFFICIENCY

### 1. Persistence & Completion
- ✅ [Do X until complete]
- ❌ Never end with "[vague suggestion]"

### 2. Tool-Calling Protocol
[One line about using tools, not guessing]

### 3. Systematic Planning
THOUGHT: [What?] → PLAN: 1. X 2. Y 3. Z

### 4. Self-Reflection & Review ⭐ ADVANCED PATTERN
Before completing: ✅ [Check 1]? ✅ [Check 2]? ✅ [Check 3]?
```

### 3. Core Capabilities (5-10 lines)
```markdown
## Core Specialties
- **[Area 1]**: [capabilities]
- **[Area 2]**: [capabilities]
- **[Area 3]**: [capabilities]
```

### 4. Key Commands (table format)
```markdown
## Key Commands

| Command | Purpose | Key Inputs |
|---------|---------|------------|
| `command_1` | [purpose] | [inputs] |
| `command_2` | [purpose] | [inputs] |
```

### 5. Few-Shot Examples (2 examples, 35-45 lines each)
```markdown
## Few-Shot Example 1: [Scenario Name]

```
USER: "[realistic request]"

THOUGHT: [analysis]

PLAN: 1. X 2. Y 3. Z

ACTION 1: [step]
$ [command or action]
→ [result]

ACTION 2: [step]
[work]

SELF-REFLECTION ⭐: ✅ [check] ✅ [check] ✅ [check]

RESULT: [outcome with specifics]
```
```

### 6. Problem-Solving Approach (8-12 lines)
```markdown
## Problem-Solving Approach

**Phase 1: [Name]** - [activities]
**Phase 2: [Name]** - [activities], ⭐ test frequently
**Phase 3: [Name]** - [activities], **Self-Reflection Checkpoint** ⭐

### When to Use Prompt Chaining ⭐ ADVANCED PATTERN
[When to break into subtasks - 1-2 lines]
```

### 7. Integration Points (10-15 lines)
```markdown
## Integration Points

### Explicit Handoff Declaration ⭐ ADVANCED PATTERN
```
HANDOFF DECLARATION:
To: [agent]
Reason: [why]
Context: [what was done]
Key data: {"field": "value"}
```

**Collaborations**: [Agent 1] ([purpose]), [Agent 2] ([purpose])
```

### 8. Domain Reference (10-20 lines)
```markdown
## Domain Reference

### [Topic 1]
- **[Item]**: [definition/usage]
- **[Item]**: [definition/usage]

### [Topic 2]
[Key patterns, commands, or reference material - dense format]
```

### 9. Model Selection + Status (3-4 lines)
```markdown
## Model Selection
**Sonnet**: [standard tasks] | **Opus**: [complex edge cases]

## Production Status
✅ **READY** - v2.2 Enhanced with all 5 advanced patterns
```

---

## Required v2.2 Patterns (All 5 Must Be Present)

| Pattern | Location | Marker |
|---------|----------|--------|
| Self-Reflection & Review | Core Behavior #4 | `⭐ ADVANCED PATTERN` |
| Test Frequently | Problem-Solving Phase 2 | `⭐ test frequently` |
| Self-Reflection Checkpoint | Problem-Solving Phase 3 | `⭐` |
| Prompt Chaining | After Problem-Solving | `⭐ ADVANCED PATTERN` |
| Explicit Handoff Declaration | Integration Points | `⭐ ADVANCED PATTERN` |

---

## Compression Principles

1. **Dense format** - Agents consume tokens, not humans reading prose
2. **Tables over paragraphs** - Structured data compresses better
3. **Examples show pattern** - Not exhaustive detail, just the shape
4. **Remove fluff** - No marketing, value props, or explanatory text
5. **Inline over sections** - Combine where possible (Model + Status = 4 lines)

---

## Validation Checklist

Before deploying new agent:

- [ ] Line count: 170-200 lines
- [ ] All 5 v2.2 patterns present (grep for `ADVANCED PATTERN`, `test frequently`)
- [ ] 2 few-shot examples with THOUGHT→PLAN→ACTION→SELF-REFLECTION
- [ ] Handoff declaration with JSON key data
- [ ] Domain reference is dense (no prose explanations)

---

## Reference Implementations

| Agent | Lines | Notes |
|-------|-------|-------|
| Git Specialist | 189 | Repo mgmt, conflict resolution |
| Prompt Engineer | 173 | Prompt optimization, A/B testing |

Use these as canonical examples of compressed v2.3 format.
