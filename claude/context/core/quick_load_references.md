# Quick Load References

## Purpose
This file provides shorthand references for quickly loading frequently-used agents and context bundles. Use these references to minimize typing and standardize loading requests across sessions.

## Agent Quick References

### Personal Assistant (PA)
**Load Command**: `load PA` or `load personal assistant`

**Files to Load**:
- `/Users/naythandawe/git/maia/claude/agents/personal_assistant_agent.md`

**Context Bundle**: Personal productivity and executive support
- Daily executive briefing
- Email management (Email RAG integration)
- Calendar optimization
- Task orchestration (Trello integration)
- Travel coordination
- Meeting intelligence (VTT pipeline)
- Strategic weekly planning

**Key Capabilities**:
- 9 core commands (daily briefing, email management, calendar, travel, tasks, communication, information intelligence, weekly planning, Trello workflow)
- MCP integrations (Gmail, Google Calendar, Google Contacts, Zapier)
- Automated pipelines (email RAG hourly, VTT watcher, meeting intelligence)
- Trello workflow intelligence via `trello_fast.py`

**Voice**: Caring Professional - Supportive, organized, proactive

---

### Engineering Manager (EM)
**Load Command**: `load EM` or `load engineering manager`

**Files to Load**:
- `/Users/naythandawe/git/maia/claude/agents/engineering_manager_cloud_mentor.md`

**Context Bundle**: Cloud MSP strategic leadership and team management
- Strategic decision-making
- Team performance analysis
- Business intelligence
- Stakeholder management
- Financial operations

---

### Service Desk Manager (SDM)
**Load Command**: `load SDM` or `load service desk manager`

**Files to Load**:
- `/Users/naythandawe/git/maia/claude/agents/service_desk_manager_agent.md`

**Context Bundle**: Service desk operations and escalation intelligence
- Complaint analysis
- Root cause investigation
- Escalation pattern detection
- Workflow bottleneck identification
- CMDB management

---

### Technical Recruitment (TR)
**Load Command**: `load TR` or `load technical recruitment`

**Files to Load**:
- `/Users/naythandawe/git/maia/claude/agents/technical_recruitment_agent.md`

**Context Bundle**: MSP/Cloud technical hiring
- CV screening (100-point framework)
- Technical skill assessment
- Role-specific evaluation
- Interview question generation

---

### Data Analyst (DA)
**Load Command**: `load DA` or `load data analyst`

**Files to Load**:
- `/Users/naythandawe/git/maia/claude/agents/data_analyst_agent.md`

**Context Bundle**: Business intelligence and data analysis
- Statistical analysis
- Dashboard design
- Revenue intelligence
- Pattern detection

---

## Context Bundle Quick References

### Complete Core Context (FULL)
**Load Command**: `load full context`

**Files to Load** (in order):
1. `/Users/naythandawe/git/maia/claude/context/ufc_system.md` (mandatory first)
2. `/Users/naythandawe/git/maia/claude/context/core/identity.md`
3. `/Users/naythandawe/git/maia/claude/context/core/systematic_thinking_protocol.md`
4. `/Users/naythandawe/git/maia/claude/context/core/model_selection_strategy.md`
5. `/Users/naythandawe/git/maia/SYSTEM_STATE.md`

---

### Productivity Suite (PROD)
**Load Command**: `load productivity suite`

**Components**:
- Personal Assistant Agent
- Email RAG system status
- Trello integration status
- Meeting intelligence pipeline
- Daily briefing automation

---

### Orro Business Context (ORRO)
**Load Command**: `load orro context`

**Files to Load**:
- `/Users/naythandawe/git/maia/claude/context/projects/orro/`
- Engineering Manager Agent (for MSP/Cloud context)
- Service Desk Manager Agent (for operations context)

---

## Usage Examples

**Single Agent Load**:
```
User: load PA
Assistant: [Loads personal_assistant_agent.md]
```

**Multiple Agent Load**:
```
User: load PA and EM
Assistant: [Loads personal assistant + engineering manager agents]
```

**Context Bundle Load**:
```
User: load productivity suite
Assistant: [Loads PA agent + checks email RAG status + Trello integration + meeting pipeline]
```

---

## Maintenance Notes

**Update Frequency**: Update this file when:
- New frequently-used agents are created
- Agent file paths change
- New context bundles are established
- User feedback suggests new quick references

**Agent Count**: Currently tracking 5 agents (PA, EM, SDM, TR, DA)

**Last Updated**: 2025-10-08 (Phase 99 - Personal Assistant quick reference established)
