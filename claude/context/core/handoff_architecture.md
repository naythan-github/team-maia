# Handoff System Architecture

## Component Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     User Query                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   swarm_auto_loader.py                           │
│  - Query classification                                          │
│  - Session creation with handoffs_enabled flag                   │
│  - Agent loading                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│               IntegratedSwarmOrchestrator                        │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────┐  │
│  │ AgentRegistry   │  │ HandoffDetector  │  │ ChainTracker   │  │
│  │ - Load agents   │  │ - Parse response │  │ - Track chain  │  │
│  │ - Gen tools     │  │ - Extract target │  │ - Detect loops │  │
│  └─────────────────┘  └──────────────────┘  └────────────────┘  │
│                                                                  │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────┐  │
│  │ ContextBuilder  │  │ MaxHandoffGuard  │  │ ResultAggregator│ │
│  │ - Enrich context│  │ - Prevent loops  │  │ - Combine output│ │
│  │ - Add metadata  │  │ - Enforce limit  │  │ - Build chain   │ │
│  └─────────────────┘  └──────────────────┘  └────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Session State                                 │
│  ~/.maia/sessions/swarm_session_{context_id}.json               │
│  - current_agent, handoff_chain, context, handoffs_enabled      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Learning System                                │
│  HandoffPatternTracker                                          │
│  - Log patterns, track success rates, cross-session learning    │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Agent Loading
```
Agent Markdown → parse_agent_collaborations() → Collaborations List
                                                       │
                                                       ▼
                          generate_handoff_functions() → transfer_to_X()
                                                       │
                                                       ▼
                          generate_tool_schemas() → Claude Tool Format
```

### 2. Handoff Execution
```
Agent Response → detect_handoff() → Handoff Info (target, context)
                                           │
                                           ▼
                 build_handoff_context() → Enriched Context
                                           │
                                           ▼
                 HandoffChainTracker → Updated Chain
                                           │
                                           ▼
                 Next Agent Execution → Continue or Complete
```

### 3. Session Update
```
Handoff Event → add_handoff_to_session() → Session File Updated
                                                  │
                                                  ▼
              HandoffPatternTracker.log_handoff() → Pattern Stored
                                                  │
                                                  ▼
              log_handoff_event() → Event Log (JSONL)
```

## Session State Schema

```json
{
  "current_agent": "security_specialist",
  "session_start": "2026-01-11T10:00:00Z",
  "handoff_chain": [
    {"from": "sre_principal", "to": "security_specialist", "reason": "Security review", "timestamp": "..."}
  ],
  "context": {
    "original_query": "Review this code",
    "previous_work": "Initial analysis complete"
  },
  "handoffs_enabled": true,
  "version": "1.4",
  "domain": "security",
  "last_classification_confidence": 0.85
}
```

## Key Design Decisions

### 1. Swarm-Style Handoff Functions
**Decision**: Agents hand off by calling `transfer_to_X()` tools
**Rationale**: LLM decides when to hand off based on context, not hardcoded rules

### 2. Context Enrichment
**Decision**: Each handoff enriches context with previous agent's output
**Rationale**: Ensures continuity and prevents duplicate work

### 3. Max Handoffs Guard
**Decision**: Default limit of 5 handoffs per workflow
**Rationale**: Prevents infinite loops while allowing complex workflows

### 4. Feature Flag Rollout
**Decision**: Handoffs disabled by default, opt-in via feature flag
**Rationale**: Safe production deployment with gradual rollout

### 5. Collaboration-Based Generation
**Decision**: Parse Collaborations metadata from agent markdown
**Rationale**: Single source of truth, reduces duplication, enables discovery

### 6. Session State Integration
**Decision**: Handoff chain stored in session files alongside agent state
**Rationale**: Enables recovery, debugging, and pattern learning

## Performance Characteristics

| Operation | Target | Actual |
|-----------|--------|--------|
| Handoff detection | <10ms | <0.1ms |
| Context injection | <50ms | <0.1ms |
| Session update | <20ms | <1ms |
| Total overhead | <100ms | <1ms |

## Integration Points

- **swarm_auto_loader.py**: Entry point, creates handoff-enabled sessions
- **PAI v2 Learning**: Captures handoff patterns for optimization
- **Session Files**: Persists handoff chain and context
- **Feature Flags**: Controls rollout and logging

## Component Responsibilities

### AgentRegistry
- Loads agent markdown files
- Parses Collaborations sections
- Generates handoff tools and schemas
- Caches agents for performance

### HandoffDetector
- Parses Claude API responses
- Identifies transfer_to_X tool calls
- Extracts target agent and context
- Returns structured handoff info

### HandoffChainTracker
- Tracks handoff sequences
- Detects circular handoffs
- Enforces max handoffs limit
- Provides chain analytics

### IntegratedSwarmOrchestrator
- Orchestrates multi-agent workflows
- Executes agents with handoff tools
- Manages handoff detection and execution
- Aggregates results and builds chain

### SessionHandoffsManager
- Reads/writes session files
- Adds handoffs to chain
- Updates current agent
- Maintains handoff context

### HandoffPatternTracker
- Logs handoff patterns to database
- Tracks success rates per path
- Provides cross-session learning data
- Enables optimization insights

## Error Handling

### Agent Not Found
- Registry returns None if agent file missing
- Orchestrator raises clear error with agent name
- Suggests checking agent file path

### Circular Handoffs
- HandoffChainTracker detects A→B→A patterns
- MaxHandoffsGuard stops at limit (default: 5)
- Result includes handoff_chain for debugging

### Context Too Large
- build_handoff_context() enforces 2000 char limit
- Truncates with "..." indicator
- Preserves most recent context

### API Failures
- APIWrapper handles retries
- Mock mode for testing without API
- Clear error messages with debugging info

## Security Considerations

- Handoff context sanitized (no secrets/credentials)
- Agent boundaries enforced (can't hand off to non-collaborators)
- Session files have restricted permissions
- Event logs exclude sensitive data

## Future Enhancements

- **Parallel Handoffs**: Multiple agents working simultaneously
- **Conditional Handoffs**: If/then handoff logic
- **Priority Handoffs**: Urgent tasks jump queue
- **Agent Suggestions**: Recommend handoff targets based on context
- **Cost Optimization**: Prefer cheaper agents when appropriate
