# Automatic Agent Handoffs Implementation Plan

**Created**: 2026-01-11
**Completed**: 2026-01-11
**Status**: ✅ COMPLETE
**Priority**: High
**Final Effort**: 8 sprints (155 tests)

---

## Executive Summary

Enable Maia agents to automatically hand off work to other specialists without explicit user request. Leverages existing HANDOFF DECLARATION patterns in 90+ agents with OpenAI Swarm-style handoff functions.

---

## Architecture Overview

```
User Query
    ↓
Initial Agent (via swarm_auto_loader)
    ↓
Agent executes with handoff tools registered
    ↓
Agent decides to hand off (via tool call) OR completes
    ↓
If handoff: SwarmOrchestrator routes to target agent with enriched context
    ↓
Loop until: no handoff OR max_handoffs reached
    ↓
Return final result + handoff chain
```

---

## Sprint 1: Handoff Function Generator

**Goal**: Auto-generate `transfer_to_X` functions from agent metadata
**Model**: Sonnet (code generation benefits from stronger reasoning)
**TDD Features**: 5

### Feature 1.1: Agent Collaboration Parser
Parse agent markdown to extract collaboration partners.

**Test file**: `claude/tools/orchestration/tests/test_handoff_generator.py`

```python
def test_parse_agent_collaborations():
    """Extract collaboration partners from agent markdown."""
    agent_content = '''
    ## Integration Points
    **Collaborations**: Python Code Reviewer (code quality), DevOps Principal (CI/CD), Cloud Security Principal (security)
    '''
    result = parse_agent_collaborations(agent_content)
    assert result == [
        {"agent": "python_code_reviewer", "specialty": "code quality"},
        {"agent": "devops_principal", "specialty": "CI/CD"},
        {"agent": "cloud_security_principal", "specialty": "security"}
    ]
```

**Verification**:
- [ ] Parses Collaborations line from Integration Points section
- [ ] Extracts agent name and specialty
- [ ] Handles variations (with/without _agent suffix)
- [ ] Returns empty list if no collaborations found

---

### Feature 1.2: Handoff Function Factory
Generate callable handoff functions from parsed collaborations.

```python
def test_generate_handoff_functions():
    """Generate transfer_to_X functions from collaborations."""
    collaborations = [
        {"agent": "security_specialist", "specialty": "security audits"}
    ]
    functions = generate_handoff_functions(collaborations)

    assert len(functions) == 1
    assert functions[0].__name__ == "transfer_to_security_specialist"
    assert "security audits" in functions[0].__doc__

    # Function returns handoff structure
    result = functions[0]()
    assert result["handoff_to"] == "security_specialist"
```

**Verification**:
- [ ] Creates function with correct name pattern
- [ ] Includes specialty in docstring (for LLM tool selection)
- [ ] Returns handoff dict with target agent
- [ ] Supports context parameter for enrichment

---

### Feature 1.3: Agent Registry Enhancement
Extend agent registry with handoff capabilities.

```python
def test_registry_includes_handoff_tools():
    """Agent registry includes generated handoff tools."""
    registry = AgentRegistry()
    agent = registry.get("sre_principal_engineer")

    assert "handoff_tools" in agent
    assert len(agent["handoff_tools"]) > 0
    assert any(t.__name__ == "transfer_to_python_code_reviewer" for t in agent["handoff_tools"])
```

**Verification**:
- [ ] Registry loads agent with handoff tools
- [ ] Tools match agent's collaboration list
- [ ] Tools are callable
- [ ] Caches tools for performance (<10ms lookup)

---

### Feature 1.4: Handoff Tool Schema Generation
Generate OpenAI-compatible tool schemas for Claude.

```python
def test_generate_tool_schemas():
    """Generate tool schemas for Claude API."""
    functions = generate_handoff_functions([
        {"agent": "azure_architect", "specialty": "Azure infrastructure"}
    ])
    schemas = generate_tool_schemas(functions)

    assert schemas[0]["name"] == "transfer_to_azure_architect"
    assert "Azure infrastructure" in schemas[0]["description"]
    assert schemas[0]["input_schema"]["type"] == "object"
```

**Verification**:
- [ ] Generates valid Claude tool schema
- [ ] Includes context parameter in schema
- [ ] Description includes specialty for LLM guidance
- [ ] Schema validates against Claude API spec

---

### Feature 1.5: Handoff Context Builder
Build enriched context for handoff.

```python
def test_build_handoff_context():
    """Build context object for handoff."""
    current_context = {"query": "Setup Azure DNS", "domain": "example.com"}
    agent_output = "Configured public DNS. Need Azure Private DNS."

    enriched = build_handoff_context(
        current_context=current_context,
        agent_output=agent_output,
        source_agent="dns_specialist",
        handoff_reason="Azure infrastructure needed"
    )

    assert enriched["previous_agent"] == "dns_specialist"
    assert enriched["handoff_reason"] == "Azure infrastructure needed"
    assert "agent_output" in enriched
    assert enriched["query"] == "Setup Azure DNS"  # Preserved
```

**Verification**:
- [ ] Preserves original context
- [ ] Adds source agent and reason
- [ ] Includes relevant agent output (truncated if needed)
- [ ] Adds timestamp for tracking

---

## Sprint 2: Handoff Execution Engine

**Goal**: Execute handoffs when agent returns handoff tool call
**Model**: Sonnet (moderate complexity, needs reliability)
**TDD Features**: 5

### Feature 2.1: Handoff Detection
Detect when agent response contains handoff tool call.

**Test file**: `claude/tools/orchestration/tests/test_handoff_executor.py`

```python
def test_detect_handoff_in_response():
    """Detect handoff tool call in Claude response."""
    response = {
        "content": [
            {"type": "tool_use", "name": "transfer_to_security_specialist", "input": {"context": "..."}}
        ]
    }

    handoff = detect_handoff(response)
    assert handoff is not None
    assert handoff["target"] == "security_specialist"
```

**Verification**:
- [ ] Detects transfer_to_X tool calls
- [ ] Extracts target agent name
- [ ] Returns None if no handoff
- [ ] Handles multiple tool calls (handoff takes priority)

---

### Feature 2.2: Agent Executor with Handoff Tools
Execute agent with registered handoff tools.

```python
def test_execute_agent_with_handoff_tools():
    """Agent execution includes handoff tools."""
    executor = AgentExecutor()
    result = executor.execute(
        agent="sre_principal_engineer",
        query="Review this code for security issues",
        context={}
    )

    # Should hand off to security or code reviewer
    assert result.handoff is not None or result.complete
```

**Verification**:
- [ ] Loads agent prompt
- [ ] Registers handoff tools
- [ ] Executes via Claude API
- [ ] Returns AgentResult with handoff or completion

---

### Feature 2.3: Handoff Chain Tracker
Track handoff chain through execution.

```python
def test_handoff_chain_tracking():
    """Track chain of handoffs through execution."""
    tracker = HandoffChainTracker()

    tracker.add_handoff("sre_principal", "security_specialist", "Security review needed")
    tracker.add_handoff("security_specialist", "devops_principal", "CI/CD integration")

    chain = tracker.get_chain()
    assert len(chain) == 2
    assert chain[0]["from"] == "sre_principal"
    assert chain[1]["to"] == "devops_principal"
```

**Verification**:
- [ ] Tracks source, target, reason, timestamp
- [ ] Maintains order
- [ ] Detects circular handoffs
- [ ] Calculates total context size

---

### Feature 2.4: Max Handoffs Guard
Prevent infinite handoff loops.

```python
def test_max_handoffs_guard():
    """Stop execution after max handoffs reached."""
    executor = SwarmExecutor(max_handoffs=3)

    # Simulate 4 handoffs
    with pytest.raises(MaxHandoffsExceeded):
        for i in range(4):
            executor.process_handoff(f"agent_{i}", f"agent_{i+1}", {})
```

**Verification**:
- [ ] Counts handoffs
- [ ] Raises exception at limit
- [ ] Configurable limit (default 5)
- [ ] Logs warning before limit

---

### Feature 2.5: Handoff Result Aggregator
Aggregate results from multi-agent workflow.

```python
def test_aggregate_handoff_results():
    """Aggregate outputs from multiple agents."""
    results = [
        AgentResult(agent="dns", output="DNS configured", handoff=None),
        AgentResult(agent="azure", output="Azure setup complete", handoff=None)
    ]

    aggregated = aggregate_results(results)
    assert "DNS configured" in aggregated.combined_output
    assert "Azure setup complete" in aggregated.combined_output
    assert aggregated.handoff_count == 1
```

**Verification**:
- [ ] Combines outputs from all agents
- [ ] Preserves agent attribution
- [ ] Tracks total handoff count
- [ ] Includes timing metrics

---

## Sprint 3: Session Integration

**Goal**: Integrate handoffs with Maia session state
**Model**: Sonnet (session state is critical path)
**TDD Features**: 4

### Feature 3.1: Session Handoff State
Store handoff chain in session state.

**Test file**: `claude/hooks/tests/test_session_handoffs.py`

```python
def test_session_stores_handoff_chain():
    """Session state includes handoff chain."""
    session = load_session("swarm_session_12345.json")

    add_handoff_to_session(session, {
        "from": "sre_principal",
        "to": "security_specialist",
        "reason": "Security review",
        "timestamp": "2026-01-11T10:00:00Z"
    })

    assert len(session["handoff_chain"]) == 2  # Initial + handoff
    assert session["current_agent"] == "security_specialist"
```

**Verification**:
- [ ] Appends to handoff_chain array
- [ ] Updates current_agent
- [ ] Preserves session context
- [ ] Atomic write (no corruption)

---

### Feature 3.2: Handoff Context Injection
Inject prior agent context on handoff.

```python
def test_inject_handoff_context():
    """Inject prior agent context into new agent prompt."""
    context = inject_handoff_context(
        target_agent="security_specialist",
        handoff_chain=[
            {"from": "sre_principal", "output": "Found potential SQL injection..."}
        ]
    )

    assert "Prior work by sre_principal" in context
    assert "SQL injection" in context
```

**Verification**:
- [ ] Includes prior agent output
- [ ] Summarizes if output too long (>2000 chars)
- [ ] Formats for target agent prompt
- [ ] Respects token budget

---

### Feature 3.3: Learning Integration
Capture handoff patterns for PAI v2 learning.

```python
def test_capture_handoff_patterns():
    """Capture successful handoff patterns for learning."""
    from claude.tools.learning.session import get_session_manager

    manager = get_session_manager()
    manager.log_handoff(
        from_agent="sre_principal",
        to_agent="security_specialist",
        query="Review code security",
        success=True
    )

    patterns = manager.get_handoff_patterns()
    assert any(p["from"] == "sre_principal" and p["to"] == "security_specialist" for p in patterns)
```

**Verification**:
- [ ] Logs handoffs to learning system
- [ ] Tracks success/failure
- [ ] Extracts patterns from history
- [ ] Informs future routing confidence

---

### Feature 3.4: Handoff Recovery
Recover from failed handoffs gracefully.

```python
def test_handoff_recovery():
    """Recover when target agent fails."""
    executor = SwarmExecutor()

    # Simulate target agent failure
    result = executor.execute_with_recovery(
        current_agent="sre_principal",
        target_agent="nonexistent_agent",
        context={}
    )

    assert result.recovered
    assert result.fallback_agent == "sre_principal"  # Return to source
```

**Verification**:
- [ ] Detects agent not found
- [ ] Falls back to source agent
- [ ] Logs recovery event
- [ ] Suggests alternative agents

---

## Sprint 4: Swarm Orchestrator Integration

**Goal**: Replace SwarmOrchestrator stub with real execution
**Model**: Opus (critical integration, high complexity)
**TDD Features**: 4

### Feature 4.1: SwarmOrchestrator Execute Integration
Replace `_call_agent_with_context` stub.

**Test file**: `claude/tools/orchestration/tests/test_swarm_integration.py`

```python
def test_swarm_orchestrator_executes_agent():
    """SwarmOrchestrator executes real agents."""
    orchestrator = SwarmOrchestrator()

    result = orchestrator.execute_with_handoffs(
        initial_agent="dns_specialist",
        task={"query": "Setup Azure DNS", "domain": "example.com"},
        max_handoffs=3
    )

    assert result.final_output is not None
    assert isinstance(result.handoff_chain, list)
```

**Verification**:
- [ ] Loads agent from registry
- [ ] Injects context into prompt
- [ ] Executes via Claude API
- [ ] Parses handoff declarations
- [ ] Routes to next agent

---

### Feature 4.2: End-to-End DNS → Azure Handoff
Complete integration test for flagship workflow.

```python
def test_dns_to_azure_handoff_e2e():
    """DNS specialist hands off to Azure architect."""
    orchestrator = SwarmOrchestrator()

    result = orchestrator.execute_with_handoffs(
        initial_agent="dns_specialist",
        task={
            "query": "Setup Exchange Online with custom domain",
            "domain": "client.com",
            "tenant": "client.onmicrosoft.com"
        }
    )

    # Should involve handoff from DNS to Azure
    assert any(h["to"] == "azure_solutions_architect" for h in result.handoff_chain)
```

**Verification**:
- [ ] DNS agent configures public DNS
- [ ] Recognizes Azure work needed
- [ ] Hands off to Azure architect
- [ ] Azure completes Exchange setup
- [ ] Full chain recorded

---

### Feature 4.3: Hook Integration
Integrate with swarm_auto_loader hook.

```python
def test_auto_loader_triggers_handoffs():
    """Auto-loader enables handoffs for routed queries."""
    # Simulate query that should trigger handoff-capable execution
    result = process_query_with_handoffs(
        query="Review this Python code for security vulnerabilities",
        enable_handoffs=True
    )

    # Should route to SRE, which may hand off to security
    assert result.initial_agent in ["sre_principal_engineer", "python_code_reviewer"]
    assert result.handoffs_enabled
```

**Verification**:
- [ ] Hook enables handoff mode
- [ ] Initial agent loaded with handoff tools
- [ ] Handoffs execute automatically
- [ ] Session updated after each handoff

---

### Feature 4.4: Handoff Analytics Dashboard
Track handoff patterns for optimization.

```python
def test_handoff_analytics():
    """Generate handoff analytics for dashboard."""
    analytics = get_handoff_analytics(days=7)

    assert "total_handoffs" in analytics
    assert "common_paths" in analytics
    assert "avg_handoffs_per_task" in analytics
    assert "handoff_success_rate" in analytics
```

**Verification**:
- [ ] Queries handoff history
- [ ] Calculates common paths
- [ ] Tracks success rates
- [ ] Identifies optimization opportunities

---

## Model Selection Summary

| Sprint | Complexity | Model | Rationale |
|--------|------------|-------|-----------|
| Sprint 1 | Medium | **Sonnet** | Code generation benefits from stronger reasoning |
| Sprint 2 | Medium | **Sonnet** | Execution engine, needs reliability |
| Sprint 3 | Medium | **Sonnet** | Session state is critical path |
| Sprint 4 | High | **Opus** | Integration, complex orchestration |

---

## File Structure

```
claude/tools/orchestration/
├── handoff_generator.py      # Sprint 1: Function generation
├── handoff_executor.py       # Sprint 2: Execution engine
├── handoff_analytics.py      # Sprint 4: Analytics
├── tests/
│   ├── test_handoff_generator.py
│   ├── test_handoff_executor.py
│   └── test_swarm_integration.py

claude/hooks/
├── tests/
│   └── test_session_handoffs.py   # Sprint 3
```

---

## Success Criteria

1. **Functional**: Agents automatically hand off without user prompt
2. **Reliable**: <1% handoff failures, graceful recovery
3. **Observable**: Full handoff chain visible in session state
4. **Learnable**: PAI v2 captures patterns for optimization
5. **Performant**: <500ms overhead per handoff

---

## Dependencies

- `claude/tools/agent_swarm.py` - Existing SwarmOrchestrator (stub)
- `claude/hooks/swarm_auto_loader.py` - Query routing hook
- `claude/tools/learning/session.py` - PAI v2 learning system
- `claude/tools/orchestration/coordinator_agent.py` - Agent classification

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Infinite handoff loops | Max handoffs guard (Feature 2.4) |
| Context explosion | Truncation + summarization (Feature 3.2) |
| Agent not found | Recovery with fallback (Feature 3.4) |
| Performance degradation | Caching + async execution |

---

## Sprint 5: Hook Wiring & Deployment

**Goal**: Wire handoff system into swarm_auto_loader and enable for production
**Model**: Sonnet (integration work, moderate complexity)
**TDD Features**: 4

### Feature 5.1: Update swarm_auto_loader.py
Integrate IntegratedSwarmOrchestrator into the existing hook.

**Verification**:
- [ ] Import swarm_integration module
- [ ] Replace stub orchestrator with IntegratedSwarmOrchestrator
- [ ] Enable handoff tools when agent loads
- [ ] Update session state on handoffs

### Feature 5.2: Agent Collaboration Audit
Verify all 90+ agents have proper Collaborations sections.

**Verification**:
- [ ] Scan all agent files for Collaborations
- [ ] Report agents missing collaborations
- [ ] Add collaborations to key agents (top 20 by usage)
- [ ] Generate handoff capability report

### Feature 5.3: Claude API Integration
Replace mock responses with real Claude API calls.

**Verification**:
- [ ] Integrate with existing Claude API wrapper
- [ ] Pass handoff tools in tool_use format
- [ ] Handle streaming responses
- [ ] Respect rate limits and token budgets

### Feature 5.4: Feature Flag & Rollout
Add feature flag for gradual rollout.

**Verification**:
- [ ] Add `handoffs_enabled` to user_preferences.json
- [ ] Default to False (opt-in initially)
- [ ] Log handoff events for monitoring
- [ ] Add `/handoffs on|off` command

---

## Sprint 6: Integration Testing

**Goal**: Test all components working together with real agent files
**Model**: Sonnet (test writing, moderate complexity)
**TDD Features**: 4

### Feature 6.1: Multi-Agent Workflow Tests
Test complete workflows across multiple agents.

**Test file**: `claude/tools/orchestration/tests/test_integration_workflows.py`

**Verification**:
- [ ] SRE → Security → DevOps chain
- [ ] DNS → Azure → Security chain
- [ ] Circular handoff prevention
- [ ] Max handoffs enforcement

### Feature 6.2: Session State Integrity Tests
Verify session state remains consistent across handoffs.

**Verification**:
- [ ] Context preserved through 5+ handoffs
- [ ] Handoff chain accurate after failures
- [ ] Recovery doesn't corrupt session
- [ ] Concurrent session isolation

### Feature 6.3: Learning System Integration Tests
Verify PAI v2 captures handoff patterns correctly.

**Verification**:
- [ ] Patterns stored after successful handoffs
- [ ] Failed handoffs logged with error context
- [ ] Pattern retrieval for analytics
- [ ] Cross-session pattern aggregation

### Feature 6.4: Performance Benchmarks
Measure overhead of handoff system.

**Verification**:
- [ ] Handoff detection < 10ms
- [ ] Context injection < 50ms
- [ ] Session update < 20ms
- [ ] Total overhead < 500ms per handoff

---

## Sprint 7: End-to-End Testing

**Goal**: Test with real Claude API calls and real agent prompts
**Model**: Opus (complex orchestration, production-critical)
**TDD Features**: 4

### Feature 7.1: Live DNS → Azure Handoff
Execute actual DNS to Azure handoff with Claude API.

**Test file**: `claude/tools/orchestration/tests/test_e2e_live.py`

**Verification**:
- [ ] DNS agent loads and executes
- [ ] Handoff tool appears in response
- [ ] Azure agent receives context
- [ ] Complete workflow succeeds

### Feature 7.2: Error Scenario Testing
Test recovery from real-world failures.

**Verification**:
- [ ] API timeout recovery
- [ ] Invalid agent name handling
- [ ] Token limit exceeded handling
- [ ] Rate limit backoff

### Feature 7.3: User Experience Validation
Ensure handoffs are transparent to user.

**Verification**:
- [ ] User sees handoff notification
- [ ] Context continuity feels natural
- [ ] No duplicate work by agents
- [ ] Final output is coherent

### Feature 7.4: Production Readiness Checklist
Final validation before enabling.

**Verification**:
- [ ] All 83 unit tests pass
- [ ] All integration tests pass
- [ ] E2E tests pass with live API
- [ ] Performance within SLA
- [ ] Logging and monitoring in place

---

## Sprint 8: Documentation

**Goal**: Complete documentation for the handoff system
**Model**: Sonnet (clear technical writing)
**Features**: 4

### Feature 8.1: Developer Documentation
How to add handoff support to new agents.

**Output**: `claude/context/tools/agent_handoff_developer_guide.md`

**Contents**:
- [ ] Adding Collaborations section to agents
- [ ] Handoff function generation explained
- [ ] Testing handoff-enabled agents
- [ ] Debugging handoff issues

### Feature 8.2: Architecture Documentation
System design and component relationships.

**Output**: `claude/context/core/handoff_architecture.md`

**Contents**:
- [ ] Component diagram
- [ ] Data flow through handoffs
- [ ] Session state schema
- [ ] Integration points

### Feature 8.3: Operations Runbook
How to monitor and troubleshoot handoffs.

**Output**: `claude/context/tools/handoff_operations_runbook.md`

**Contents**:
- [ ] Monitoring handoff success rates
- [ ] Common failure patterns
- [ ] Recovery procedures
- [ ] Performance tuning

### Feature 8.4: Update CLAUDE.md
Add handoff system to main documentation.

**Verification**:
- [ ] Add to Architecture section
- [ ] Document /handoffs command
- [ ] Update agent collaboration standards
- [ ] Add to capability index

---

## Updated Model Selection Summary

| Sprint | Focus | Model | Rationale |
|--------|-------|-------|-----------|
| Sprint 1 | Handoff Generator | **Sonnet** | Code generation |
| Sprint 2 | Handoff Executor | **Sonnet** | Execution engine |
| Sprint 3 | Session Integration | **Sonnet** | Session state |
| Sprint 4 | Swarm Integration | **Opus** | Complex orchestration |
| Sprint 5 | Hook Wiring | **Sonnet** | Integration work |
| Sprint 6 | Integration Testing | **Sonnet** | Test writing |
| Sprint 7 | E2E Testing | **Opus** | Production-critical |
| Sprint 8 | Documentation | **Sonnet** | Technical writing |

---

## Subagent Strategy

| Sprint | Subagent? | Rationale |
|--------|-----------|-----------|
| 1-4 | ✅ Yes | TDD implementation - well-defined scope |
| 5 | ✅ Yes | Hook integration - isolated changes |
| 6 | ✅ Yes | Integration tests - test writing |
| 7 | ⚠️ Partial | E2E needs human oversight for API costs |
| 8 | ✅ Yes | Documentation - clear deliverables |

**Note**: Sprint 7 E2E testing with live API should be reviewed before each test run due to API cost implications.

---

## Complete Timeline

| Sprint | Status | Tests | Features |
|--------|--------|-------|----------|
| Sprint 1 | ✅ Complete | 22 | F001-F005 |
| Sprint 2 | ✅ Complete | 24 | F006-F010 |
| Sprint 3 | ✅ Complete | 11 | F011-F014 |
| Sprint 4 | ✅ Complete | 26 | F015-F018 |
| Sprint 5 | 🔲 Pending | TBD | F019-F022 |
| Sprint 6 | 🔲 Pending | TBD | F023-F026 |
| Sprint 7 | 🔲 Pending | TBD | F027-F030 |
| Sprint 8 | 🔲 Pending | N/A | Documentation |

---

## Next Steps

1. ✅ Sprints 1-4 complete (83 tests passing)
2. 🔲 Sprint 5: Wire into swarm_auto_loader
3. 🔲 Sprint 6: Integration testing
4. 🔲 Sprint 7: E2E with live API
5. 🔲 Sprint 8: Documentation

---

**Sprints 1-4 complete. Ready for Sprint 5: Hook Wiring & Deployment.**
