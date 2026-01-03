# Maia Guidance Document Template v1.0

**Purpose**: Standard format for all Maia context/guidance files to minimize token usage
**Target**: ≥50% reduction from prose format while preserving essential content

---

## Format Standards

### Header Block
```markdown
# [Document Name] v[X.Y] (Compressed)

**Purpose**: [1 sentence - what this doc enables]
**Updated**: YYYY-MM-DD | **Status**: [Active/Draft/Deprecated]
```

### Section Structure
- Use `---` dividers between major sections
- Prefer tables over prose for lists/comparisons
- Use `|` pipe notation for inline alternatives
- Compress examples to 1-2 lines max

---

## Allowed Patterns

### Quick Reference Tables
```markdown
| Item | Purpose | Key Commands |
|------|---------|--------------|
| `tool.py` | Description | `--flag1`, `--flag2` |
```

### Decision Trees (ASCII)
```markdown
```
Trigger?
├── YES → Action A
├── NO → Action B
└── MAYBE → Check X → Then Y
```
```

### State Machines (Inline)
```markdown
```
State1 → State2 → State3
  ↓ GATE    ↓ GATE
 [condition] [condition]
```
```

### Compressed Lists
```markdown
**ALWAYS**: Item1 | Item2 | Item3
**NEVER**: Item4 | Item5
**EXEMPT**: Item6 (reason)
```

### Key-Value Pairs
```markdown
**KEY**: Value with details | Alternative | Fallback
```

---

## Anti-Patterns (Avoid)

| ❌ Don't | ✅ Do Instead |
|----------|---------------|
| Long prose explanations | Tables, bullets, key-value |
| Multiple examples per concept | 1-2 examples max |
| Nested sub-sub-sections | Flat structure, tables |
| Redundant phrasing | Direct statements |
| "In order to..." | Just state the action |
| Full sentences in tables | Keywords/phrases |

---

## Section Templates

### Workflow Section
```markdown
## Workflow

### Phase N: [Name]
**TRIGGER**: [when this phase starts]
**ACTIONS**: Action1 | Action2 | Action3
**GATE**: [what must be true to proceed]
**OUTPUT**: [deliverable]
```

### Tool Reference Section
```markdown
## Tools (`claude/tools/[category]/`)

| Tool | Purpose | Key Commands |
|------|---------|--------------|
| `name.py` | 1-line description | `cmd1`, `cmd2` |
```

### Agent Reference Section
```markdown
## Agents

| Agent | File | Purpose | Capabilities |
|-------|------|---------|--------------|
| Name | `file.md` | 1-line | keyword1, keyword2 |
```

### Decision Guide Section
```markdown
## Decision Guide

| Scenario | Action |
|----------|--------|
| "user says X" | → Tool/Agent Y |
| "need to Z" | → Workflow W |
```

---

## Footer Block
```markdown
---

*v[X.Y] | [Original]→[Compressed] lines ([N]% reduction) | [Key preservation note]*
```

---

## Validation Checklist

Before finalizing a guidance doc:
- [ ] Header block complete (purpose, date, status)
- [ ] ≥50% line reduction from prose equivalent
- [ ] All essential content preserved (test with grep for keywords)
- [ ] Tables used instead of prose lists
- [ ] Examples compressed to 1-2 lines
- [ ] No redundant explanations
- [ ] Footer with version and reduction stats

---

## Example: Minimal Workflow Doc

```markdown
# Feature X Protocol v1.0 (Compressed)

**Purpose**: Define workflow for Feature X
**Updated**: 2025-01-03 | **Status**: Active

---

## Workflow

```
Trigger → Phase1 → Phase2 → Complete
           ↓ GATE    ↓ GATE
         [cond1]   [cond2]
```

### Phase 1: Setup
**ACTIONS**: Action1 | Action2
**GATE**: Condition met

### Phase 2: Execute
**ACTIONS**: Action3 | Action4
**OUTPUT**: Result

---

## Quick Reference

| Scenario | Action |
|----------|--------|
| Need X | → `tool.py --flag` |
| Need Y | → Agent Z |

---

*v1.0 | ~50 lines | Workflow + tools preserved*
```

---

*v1.0 | Template for all Maia guidance documents | Targets ≥50% token reduction*
