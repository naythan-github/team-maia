# Agent Orchestration Layer - Implementation Project

**Project ID**: AGENT_ORCH_001
**Created**: 2025-10-13
**Status**: Planning → Implementation
**Priority**: HIGH
**Estimated Time**: 3 hours

---

## Executive Summary

**Problem**: Phase 2 of Information Management System created 3 standalone Python tools misnamed as "agents". Current architecture violates Maia's agent-tool separation pattern and requires users to know CLI commands instead of natural language.

**Solution**: Create proper agent orchestration layer with 3 markdown agent specifications that delegate to the 7 existing tools, providing natural language interface and intelligent workflow coordination.

**Business Value**:
- Natural language interface vs CLI commands (10x easier)
- Intelligent context-aware routing (knows when to use which tool)
- Proper architecture alignment (maintainable, extensible)
- Foundation for future agent expansions

---

## Current State Analysis

### What We Have (Tools)

**Phase 1 Production Tools** (4 systems, 2,750 lines):
- `claude/tools/information_management/enhanced_daily_briefing_strategic.py` (650 lines)
- `claude/tools/information_management/meeting_context_auto_assembly.py` (550 lines)
- `claude/tools/productivity/unified_action_tracker_gtd.py` (850 lines)
- `claude/tools/productivity/weekly_strategic_review.py` (700 lines)

**Phase 2 Experimental Tools** (3 systems, 2,150 lines) - **MISNAMED AS AGENTS**:
- `claude/extensions/experimental/stakeholder_intelligence_agent.py` (750 lines)
- `claude/extensions/experimental/executive_information_manager.py` (700 lines)
- `claude/extensions/experimental/decision_intelligence_agent.py` (700 lines)

### What We're Missing (Agents)

**No orchestration layer** - Users must:
1. Know which tool to use
2. Remember CLI syntax
3. Manually chain tools for complex workflows
4. No natural language interface

### Architecture Violation

**Current**: Tools pretending to be agents
**Should Be**: Markdown agent specs that orchestrate tools

---

## Proposed Architecture

### Agent Layer Design

```
USER (natural language)
    ↓
INFORMATION MANAGEMENT ORCHESTRATOR AGENT (master)
    ├─> STAKEHOLDER INTELLIGENCE AGENT (specialist)
    ├─> DECISION INTELLIGENCE AGENT (specialist)
    └─> Direct tool calls for simple queries
        ↓
TOOL LAYER (7 Python implementations)
    ├─> Phase 1: 4 production tools
    └─> Phase 2: 3 management tools
```

### Three Agents to Create

#### 1. Information Management Orchestrator Agent
**File**: `claude/agents/information_management_orchestrator.md`
**Role**: Master coordinator for all information management workflows
**Size**: ~300 lines

**Capabilities**:
- Intent classification from natural language
- Multi-tool workflow orchestration
- Context awareness (time, calendar, user state)
- Response synthesis across multiple tools

**Example Interactions**:
```
User: "What should I focus on today?"
Agent: Orchestrates morning ritual workflow
  → executive_information_manager.py morning
  → stakeholder_intelligence.py dashboard (at-risk filter)
  → enhanced_daily_briefing_strategic.py
  → Synthesize: "3 critical items, 2 at-risk relationships, here's your plan..."

User: "Prepare me for today"
Agent: Pre-meeting workflow
  → Get calendar events for today
  → For each meeting: stakeholder_intelligence.py context
  → meeting_context_auto_assembly.py
  → Format: Meeting-by-meeting briefing
```

#### 2. Stakeholder Intelligence Agent
**File**: `claude/agents/stakeholder_intelligence_agent.md` (replace existing spec)
**Role**: Natural language interface for relationship management
**Size**: ~200 lines

**Capabilities**:
- Relationship health queries
- Pre-meeting context assembly
- Commitment tracking
- At-risk detection and recommendations

**Example Interactions**:
```
User: "How's my relationship with Hamish?"
Agent:
  → stakeholder_intelligence.py context --id 1
  → Parse: health=77.8, sentiment=+0.65, engagement=medium
  → Response: "Hamish Ridland (77.8/100 - Good) - Last contact 2 days ago
     discussing cloud migration. Relationship stable with positive sentiment."

User: "Who should I check in with?"
Agent:
  → stakeholder_intelligence.py dashboard
  → Filter: health <60 OR sentiment=declining OR last_contact >14 days
  → Prioritize: by health score + strategic importance
  → Response: "3 stakeholders need attention:
     1. Nigel Franklin (38.5 - At Risk) - 25 days no contact
     2. Martin Dunn (64.8 - Needs Attention) - declining sentiment
     3. Russell Gallagher (69.0 - Needs Attention) - 12 days no contact"
```

#### 3. Decision Intelligence Agent
**File**: `claude/agents/decision_intelligence_agent.md` (replace existing spec)
**Role**: Natural language interface for decision capture and learning
**Size**: ~200 lines

**Capabilities**:
- Guided decision capture
- Decision template selection
- Quality scoring and retrospectives
- Pattern analysis and recommendations

**Example Interactions**:
```
User: "I need to decide between AWS and Azure for cloud platform"
Agent: Guided workflow
  1. "This sounds like an architecture decision. Let me help capture it systematically."
  2. → decision_intelligence.py create --type architecture --title "Cloud platform selection"
  3. "What's the core problem you're solving?" [collect problem statement]
  4. "Let's explore AWS first - what are the pros?" [iterate options]
  5. → decision_intelligence.py add-option [for each alternative]
  6. "Which option are you leaning toward?" [capture choice + reasoning]
  7. → decision_intelligence.py choose --id X --option-id Y
  8. → decision_intelligence.py summary --id X
  9. Response: "Decision captured with quality score 43/60.
     Consider adding stakeholder input (Values: 0/10) to improve quality."

User: "What decisions did I get wrong recently?"
Agent:
  → decision_intelligence.py patterns
  → Filter: success_level IN ('failed', 'missed') AND outcome_date >90 days
  → Analyze: common patterns in failed decisions
  → Response: "3 decisions missed targets in past quarter:
     - 2 vendor selections (rushed evaluation)
     - 1 hiring decision (cultural fit misjudged)
     Common pattern: Low information scores (avg 4/10).
     Recommendation: Spend more time on research phase."
```

---

## Implementation Plan

### Phase 1: File Organization (10 minutes)

**Rename and Move Phase 2 Tools**:
```bash
# Remove "agent" from filenames, move to production locations
mv claude/extensions/experimental/stakeholder_intelligence_agent.py \
   claude/tools/information_management/stakeholder_intelligence.py

mv claude/extensions/experimental/executive_information_manager.py \
   claude/tools/information_management/executive_information_manager.py

mv claude/extensions/experimental/decision_intelligence_agent.py \
   claude/tools/productivity/decision_intelligence.py
```

**Update Internal References**:
- Update any import statements
- Update database paths if needed
- Test CLI still works after move

### Phase 2: Create Agent Specifications (90 minutes)

**Agent 1: Information Management Orchestrator** (30 min)
- File: `claude/agents/information_management_orchestrator.md`
- Sections:
  - Purpose & Scope
  - Capabilities (6-8 intent categories)
  - Tool Delegation Map (intent → tool commands)
  - Orchestration Logic (decision trees for complex workflows)
  - Response Templates
  - Integration with other agents
  - Example interactions (5-8 scenarios)
- Size: ~300 lines

**Agent 2: Stakeholder Intelligence Agent** (30 min)
- File: `claude/agents/stakeholder_intelligence_agent.md` (replace)
- Sections:
  - Purpose & Scope
  - Capabilities (relationship queries, health checks, prep)
  - Tool Delegation Map
  - Query Pattern Matching
  - Response Formatting
  - Proactive Recommendations
  - Example interactions (4-6 scenarios)
- Size: ~200 lines

**Agent 3: Decision Intelligence Agent** (30 min)
- File: `claude/agents/decision_intelligence_agent.md` (replace)
- Sections:
  - Purpose & Scope
  - Capabilities (capture, retrospective, learning)
  - Tool Delegation Map
  - Guided Workflow Logic
  - Quality Coaching
  - Pattern Recognition
  - Example interactions (4-6 scenarios)
- Size: ~200 lines

### Phase 3: Update Documentation (15 minutes)

**SYSTEM_STATE.md Updates**:
- Change "Phase 2 Specialist Agents" → "Phase 2 Management Tools"
- Add new section: "Phase 2.1: Agent Orchestration Layer"
- Clear distinction: "3 agent specs orchestrating 7 tools"

**README.md Updates**:
- Update Information Management section
- Clarify architecture: agents (orchestration) vs tools (implementation)
- Update usage examples (natural language vs CLI)

**agents.md Updates**:
- Remove incorrect Phase 2 "agent" entries
- Add 3 new agent specifications
- Include orchestration architecture diagram

### Phase 4: Testing & Validation (30 minutes)

**Test Agent Invocation**:
1. Test through Claude: "What should I focus on today?"
2. Verify agent correctly delegates to tools
3. Test complex multi-tool workflows
4. Validate natural language variations

**Test Tool Functionality**:
1. Verify tools still work after file moves
2. Test database connections
3. Validate CLI commands
4. Check LaunchAgent compatibility

**Documentation Validation**:
1. Verify all references updated
2. Check file paths are correct
3. Validate example commands work

---

## Agent Specification Template

Each agent markdown file follows this structure:

```markdown
# [Agent Name]

**Agent ID**: [lowercase_with_underscores]
**Type**: [Master Orchestrator | Specialist Agent]
**Priority**: [HIGH | MEDIUM | LOW]
**Created**: 2025-10-13

---

## 🎯 Purpose

One-paragraph description of agent's role and value.

---

## 🧠 Core Capabilities

### Capability 1: [Name]
**What it does**: Brief description
**User interactions**: Example queries
**Tool delegation**: Which tools are called

### Capability 2: [Name]
...

---

## 🔗 Tool Delegation Map

### Intent: [intent_name]
**Trigger patterns**: Natural language variations
**Tool sequence**:
1. tool_name.py command --args
2. tool_name.py command --args
**Response format**: How to synthesize output

---

## 🎼 Orchestration Logic

### Workflow: [workflow_name]
**Trigger**: User query pattern
**Decision tree**:
- If condition A → tool X
- Else if condition B → tool Y + tool Z
- Else → default response

---

## 📋 Response Templates

### Template: [template_name]
**Use case**: When to use this template
**Structure**:
```
[Example formatted response]
```

---

## 🔌 Integration Points

### With Other Agents
- Agent X: Handoff scenarios
- Agent Y: Coordination workflows

### With Phase 1 Tools
- tool_name.py: Usage patterns

---

## 💬 Example Interactions

### Scenario 1: [Name]
**User**: "Example query"
**Agent Reasoning**: Internal thought process
**Tool Calls**:
1. tool.py command
2. tool.py command
**Response**: "Example formatted response"

### Scenario 2: [Name]
...

---

## 📊 Success Metrics

- Metric 1: Target value
- Metric 2: Target value

---

## 🚀 Usage

How to invoke this agent through Claude interface.
```

---

## Technical Architecture

### Agent Invocation Flow

```
1. User Query (natural language)
   ↓
2. Claude Code receives query
   ↓
3. Context loading: Load agent markdown specification
   ↓
4. Intent Classification: Parse query against agent capabilities
   ↓
5. Tool Delegation: Execute tool commands per delegation map
   ↓
6. Response Synthesis: Format tool outputs per response templates
   ↓
7. User Response (natural language)
```

### Agent-Tool Interface

**Agents** (markdown specifications):
- Natural language understanding
- Intent classification
- Workflow orchestration
- Response formatting
- Context awareness

**Tools** (Python implementations):
- Data processing
- Database operations
- External integrations
- Computation/algorithms
- CLI interfaces

**Clear Separation**:
- Agents: WHAT to do (orchestration logic)
- Tools: HOW to do it (implementation)

---

## Success Criteria

### Functional Requirements
- ✅ 3 agent specifications created (~700 lines total)
- ✅ 7 tools correctly organized and named
- ✅ Natural language queries work through agents
- ✅ Multi-tool workflows orchestrate correctly
- ✅ All documentation updated with correct terminology

### Architecture Requirements
- ✅ Clear agent-tool separation
- ✅ Agents are markdown specs only (no Python)
- ✅ Tools have no orchestration logic
- ✅ Follows Maia agent template pattern

### User Experience Requirements
- ✅ "What should I focus on?" works
- ✅ "How's my relationship with X?" works
- ✅ "I need to decide on Y" works
- ✅ Complex workflows (multi-tool) work
- ✅ Response quality matches tool capabilities

### Documentation Requirements
- ✅ SYSTEM_STATE.md: Tools vs agents clearly distinguished
- ✅ README.md: Architecture diagram updated
- ✅ agents.md: Correct agent entries only
- ✅ Example usage patterns documented

---

## Risk Mitigation

### Risk 1: Agent delegation may not work through Claude
**Mitigation**: Test early with simple queries, iterate on specification format
**Fallback**: Create slash commands as intermediate step

### Risk 2: Tools may break when moved
**Mitigation**: Test CLI after moves, update paths incrementally
**Fallback**: Keep experimental/ as backup until validated

### Risk 3: Natural language understanding may be inconsistent
**Mitigation**: Provide clear trigger patterns in specs, include many examples
**Fallback**: Document exact query phrases that work

---

## Timeline

**Total Estimated Time**: 3 hours

- **Phase 1** (File Organization): 10 minutes
- **Phase 2** (Agent Specs): 90 minutes
  - Orchestrator: 30 min
  - Stakeholder: 30 min
  - Decision: 30 min
- **Phase 3** (Documentation): 15 minutes
- **Phase 4** (Testing): 30 minutes
- **Buffer**: 35 minutes

**Start**: 2025-10-13 21:45
**Target Completion**: 2025-10-14 00:45

---

## Post-Implementation

### Immediate Next Steps
1. Test agents with real daily workflow
2. Gather user feedback on natural language understanding
3. Iterate on response templates based on usage
4. Create slash commands for frequently used patterns

### Future Enhancements
1. **Agent Learning**: Track which queries work well, improve delegation patterns
2. **Context Persistence**: Remember user preferences, recent interactions
3. **Proactive Agents**: Push notifications for at-risk relationships, pending decisions
4. **Voice Interface**: Extend natural language to voice commands
5. **Mobile Integration**: Agent access from mobile devices

### Phase 3 Considerations
Phase 3 of Information Management System (from original plan):
- Advanced analytics across tools
- Predictive models (relationship health forecasting, decision outcome prediction)
- Cross-system insights and pattern recognition
- Machine learning for intent classification

---

## Appendix: Tool Inventory

### Phase 1 Production Tools (In Correct Locations)
1. `claude/tools/information_management/enhanced_daily_briefing_strategic.py` (650 lines)
   - 0-10 impact scoring, AI recommendations
   - LaunchAgent: Daily 7AM

2. `claude/tools/information_management/meeting_context_auto_assembly.py` (550 lines)
   - 6 meeting types, 80% prep time reduction
   - Integration: Calendar.app + Email RAG

3. `claude/tools/productivity/unified_action_tracker_gtd.py` (850 lines)
   - 7 GTD contexts, auto-classification
   - Database: action_items.db

4. `claude/tools/productivity/weekly_strategic_review.py` (700 lines)
   - 90-min guided GTD workflow
   - LaunchAgent: Friday 3PM

### Phase 2 Tools (Need Moving)
5. `claude/extensions/experimental/stakeholder_intelligence_agent.py` (750 lines)
   - CRM-style health monitoring (0-100 scoring)
   - Database: stakeholder_intelligence.db (4 tables)
   - MOVE TO: `claude/tools/information_management/stakeholder_intelligence.py`

6. `claude/extensions/experimental/executive_information_manager.py` (700 lines)
   - 5-tier prioritization, morning ritual generator
   - Database: executive_information.db (3 tables)
   - MOVE TO: `claude/tools/information_management/executive_information_manager.py`

7. `claude/extensions/experimental/decision_intelligence_agent.py` (700 lines)
   - 8 decision templates, 6-dimension quality framework
   - Database: decision_intelligence.db (4 tables)
   - MOVE TO: `claude/tools/productivity/decision_intelligence.py`

---

## References

- **Original Project**: `claude/data/INFORMATION_MANAGEMENT_SYSTEM_PROJECT.md`
- **Phase 2 Plan**: `claude/data/PHASE2_IMPLEMENTATION_PLAN.md`
- **Agent Template**: `claude/context/core/agents.md` (system overview)
- **Maia Architecture**: `CLAUDE.md` (working principles)

---

**Status**: ✅ Project plan saved, ready for implementation
