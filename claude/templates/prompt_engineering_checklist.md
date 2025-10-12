# Prompt Engineering Checklist for New Agents

**Purpose**: Quick reference checklist for creating or upgrading agents to v2.2 Enhanced standard

**Source**: `claude/data/PROMPT_ENGINEER_AGENT_ANALYSIS.md`

---

## Structure Checklist

### ✅ Core Sections (Required)

- [ ] **Agent Overview** (4-6 lines)
  - [ ] Purpose: One-sentence description
  - [ ] Target Role: Expertise level and domain

- [ ] **Core Behavior Principles** (80-100 lines)
  - [ ] Persistence & Completion (OpenAI Critical Reminder #1)
  - [ ] Tool-Calling Protocol (OpenAI Critical Reminder #2)
  - [ ] Systematic Planning (OpenAI Critical Reminder #3)
  - [ ] Self-Reflection & Review (Advanced Pattern)

- [ ] **Core Specialties** (4-6 bullets)
  - [ ] Use action verbs (analyze, design, implement, optimize)
  - [ ] Specific domain capabilities

- [ ] **Key Commands** (150-250 lines)
  - [ ] Each command has: Purpose, Inputs, Outputs
  - [ ] Minimum 2 few-shot examples per command
  - [ ] Tool-calling patterns with code examples

- [ ] **Problem-Solving Approach** (30-50 lines)
  - [ ] 3-phase methodology or domain-specific template
  - [ ] Self-reflection checkpoints

- [ ] **Performance Metrics** (20-30 lines)
  - [ ] Agent-specific success criteria
  - [ ] Measurable outcomes

- [ ] **Integration Points** (40-60 lines)
  - [ ] Explicit handoff declaration pattern
  - [ ] Primary collaborations
  - [ ] Handoff triggers

- [ ] **Model Selection Strategy** (10 lines)
  - [ ] Sonnet (default) / Opus (when needed)

- [ ] **Domain Expertise** (30-50 lines)
  - [ ] Reference information and knowledge base

---

## Content Quality Checklist

### ✅ Few-Shot Examples (Critical)

- [ ] **Minimum 2 examples per key command**
- [ ] Examples show complete workflow (USER → REASONING → ACTION → RESULT)
- [ ] At least 1 ReACT pattern example (THOUGHT → ACTION → OBSERVATION → REFLECTION)
- [ ] Examples are domain-specific (not generic)
- [ ] Examples demonstrate self-correction where appropriate

**Example Template**:
```markdown
USER: "Check if example.com has SPF record configured"

AGENT REASONING:
- Need to query DNS TXT records
- SPF records are TXT records starting with "v=spf1"

ACTION:
result = self.call_tool(
    tool_name="dns_query",
    parameters={"domain": "example.com", "record_type": "TXT"}
)

OBSERVATION:
Found 3 TXT records, 1 is SPF record: "v=spf1 include:_spf.google.com -all"

RESULT: Yes, SPF record is configured correctly.
```

### ✅ Tool-Calling Protocol (Critical)

- [ ] Every example uses `self.call_tool()` (never guesses)
- [ ] Tool parameters explicitly defined
- [ ] Results validated before responding
- [ ] Error handling shown

**Anti-Pattern**: ❌ "Assuming there are 46 agents..."
**Correct**: ✅ `agents = self.call_tool(tool_name="glob_files", parameters={"pattern": "claude/agents/*.md"})`

### ✅ Self-Reflection Pattern (Advanced)

- [ ] Self-reflection checkpoint in at least 1 example
- [ ] Questions asked before completion:
  - Did I fully address the user's request?
  - Are there edge cases I missed?
  - What could go wrong with this solution?
  - Would this work if scaled 10x?

**Example**:
```markdown
SELF-REVIEW CHECKPOINT ⭐:
- ✅ Complete audit? YES - sampled 10 agents, identified patterns
- ✅ Edge cases? Some agents are client-specific (may not need full upgrade)
- ✅ Prioritization? Focus on high-impact agents (MSP operations, cloud infrastructure)
```

### ✅ Explicit Handoff Declaration (Advanced)

- [ ] Handoff pattern included in Integration Points
- [ ] Structured format:
  - To: [target_agent]
  - Reason: [why handoff needed]
  - Context: [work completed, current state, next steps, key data]
  - Expected Output: [what target agent should return]

**Example**:
```markdown
HANDOFF DECLARATION:
To: dns_specialist_agent
Reason: Email authentication audit required (SPF/DKIM/DMARC)
Context:
  - Work completed: Azure tenant health check (all systems GREEN)
  - Current state: Deliverability issue confirmed
  - Key data: {"domain": "example.com", "issue_type": "email_deliverability"}
Expected Output: DNS audit findings with remediation recommendations
```

---

## Testing & Validation Checklist

### ✅ Quality Scoring (Use Rubric)

- [ ] Task Completion: 40 points (fully resolved vs partial)
- [ ] Tool-Calling: 20 points (proper tool use vs guessing)
- [ ] Problem Decomposition: 20 points (systematic vs ad-hoc)
- [ ] Response Quality: 15 points (completeness, accuracy, clarity)
- [ ] Persistence: 5 points (follow-through vs stopping early)

**Target Score**: 75+/100 (Good), 85+/100 (Excellent)

### ✅ Template Compliance

- [ ] Agent follows v2.2 Enhanced template structure
- [ ] All required sections present
- [ ] OpenAI's 3 critical reminders included
- [ ] Self-reflection pattern demonstrated
- [ ] Size: 300-600 lines (balanced completeness/conciseness)

### ✅ Test Cases

- [ ] Test with 3-5 realistic queries
- [ ] Verify tool-calling works correctly
- [ ] Check handoff patterns trigger appropriately
- [ ] Validate output quality against rubric

---

## Common Mistakes to Avoid

### ❌ What NOT to Do

1. **No Examples**: Agent with zero few-shot examples (critical gap)
2. **Generic Examples**: Examples that could apply to any agent
3. **Verbose Bloat**: Agent >1,000 lines with redundant content
4. **Missing Reminders**: Skipping OpenAI's 3 critical reminders
5. **No Self-Reflection**: Examples don't show self-correction
6. **Tool-Calling Violations**: Agent guesses instead of using tools
7. **Vague Commands**: Commands without clear inputs/outputs/examples
8. **No Handoff Patterns**: Integration Points missing handoff guidance

---

## Size Guidelines

**Target Size**: 300-600 lines
- **Too Small** (<200 lines): Missing patterns, insufficient examples
- **Optimal** (300-600 lines): Balanced depth, clear patterns, good examples
- **Too Large** (>1,000 lines): Bloated, redundant, harder to maintain

**Size Breakdown (v2.2 Enhanced)**:
- Core Behavior Principles: 80-100 lines
- Key Commands (with examples): 150-250 lines
- Problem-Solving Approach: 30-50 lines
- Integration Points: 40-60 lines
- Other sections: 100-140 lines

---

## Quick Reference: v2.2 Enhanced Template

**File**: `claude/templates/agent_prompt_template_v2.1_lean.md`

**Key Features**:
- OpenAI's 3 critical reminders (Persistence, Tool-Calling, Planning)
- Self-Reflection & Review pattern
- 2 few-shot examples per command (minimum)
- ReACT pattern demonstration
- Explicit handoff declarations
- Prompt chaining guidance (when to use)
- Test frequently reminders

**Evolution from v2**:
- v2: 1,081 lines average (too bloated)
- v2.2 Enhanced: 358 lines (67% reduction)
- Quality: 85+/100 (improved from 65/100)

---

## Validation Before Deployment

### Pre-Deployment Checklist

- [ ] All sections present (Agent Overview → Domain Expertise)
- [ ] 2+ few-shot examples per key command
- [ ] At least 1 ReACT pattern example
- [ ] Self-reflection checkpoint demonstrated
- [ ] Tool-calling protocol followed (no guessing)
- [ ] Handoff patterns documented
- [ ] Quality score: 75+/100 (validate with rubric)
- [ ] Size: 300-600 lines (not bloated, not sparse)
- [ ] Test cases passing (3-5 realistic queries)
- [ ] Integration points documented (which agents to collaborate with)

### Post-Deployment Monitoring

- [ ] Track quality scores over first 30 days
- [ ] Monitor for regressions (alerting system)
- [ ] Collect user feedback
- [ ] A/B test if major changes made
- [ ] Document learnings for future agent improvements

---

## Resources

**Templates**:
- `claude/templates/agent_prompt_template_v2.1_lean.md` - v2.2 Enhanced template
- `claude/templates/few_shot_examples_library.md` - 20 examples by pattern type

**Documentation**:
- `claude/data/PROMPT_ENGINEER_AGENT_ANALYSIS.md` - Complete guide (1,961 lines)
- `claude/data/AGENT_EVOLUTION_PROJECT_PLAN.md` - Full project plan

**Tools**:
- `claude/tools/sre/automated_quality_scorer.py` - Quality rubric scorer
- `claude/tools/sre/ab_testing_framework.py` - A/B testing
- `claude/tools/sre/agent_quality_alerting.py` - Quality monitoring

**Examples (Upgraded Agents)**:
- `claude/agents/dns_specialist_agent.md` - 100/100 quality score
- `claude/agents/sre_principal_engineer_agent.md` - 88/100 quality score
- `claude/agents/service_desk_manager_agent.md` - 100/100 quality score

---

## Summary: The 5 Critical Requirements

1. **OpenAI's 3 Reminders**: Persistence, Tool-Calling, Systematic Planning
2. **Few-Shot Examples**: Minimum 2 per command, domain-specific, complete workflows
3. **Self-Reflection**: Pre-completion validation checkpoints
4. **Handoff Patterns**: Explicit declarations for multi-agent coordination
5. **Quality Validation**: Score 75+/100 using rubric before deployment

**Remember**: Quality > Size. Better to have 400 lines with strong patterns than 1,000 lines of generic content.
