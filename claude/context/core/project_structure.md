# Maia Project Structure

## System Architecture Overview

```
maia/
├── claude/
│   ├── context/      # UFC system root
│   │   ├── core/     # System identity, agents, orchestration
│   │   ├── tools/    # Tool definitions and capabilities
│   │   ├── personal/ # Personal profile and preferences
│   │   ├── knowledge/# Domain expertise databases
│   │   └── session/  # Session state and compression data
│   ├── agents/       # Specialized AI agents (26+ active)
│   ├── commands/     # Reusable workflow commands (12+ advanced)
│   ├── tools/        # Executable automation tools (285+ enterprise tools)
│   ├── hooks/        # System integration hooks
│   └── data/         # Structured databases and assets
└── applications/     # Active job applications and CVs
```

## Directory Functions

### claude/context/
**UFC (Unified File-based Context) System Root**
- **core/**: System identity, agents, orchestration patterns
- **tools/**: Tool definitions, capabilities, and discovery frameworks
- **personal/**: User profile, preferences, and personal context
- **knowledge/**: Domain expertise databases and knowledge graphs
- **session/**: Session state, compression data, and context preservation

### claude/agents/
**Specialized AI Agents**
- Production-ready agents with domain expertise
- Multi-agent orchestration capabilities
- Real-time message bus communication

### claude/commands/
**Reusable Workflow Commands**
- Advanced multi-step workflows
- System automation and orchestration
- Implementation tracking and recovery

### claude/tools/
**Executable Automation Tools**
- 285+ enterprise-grade tools across 11 emoji domains
- Local LLM integration and cost optimization
- Security hardening and compliance tools

### claude/hooks/
**System Integration Hooks**
- Event-driven automation
- Context enforcement and validation
- User interaction enhancement

### claude/data/
**Structured Databases and Assets**
- SQLite databases for persistent state
- Knowledge management and RAG systems
- Implementation tracking and analytics