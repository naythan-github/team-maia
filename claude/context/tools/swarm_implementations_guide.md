# Swarm Framework - Implementation Guide

**Created**: 2025-10-12
**Status**: ✅ TWO IMPLEMENTATIONS AVAILABLE
**Purpose**: Guide for choosing and using the right Swarm implementation

---

## Overview

Maia now has **two Swarm Handoff Framework implementations**, each optimized for different use cases:

1. **Standalone Implementation** (`claude/tools/agent_swarm.py`) - New, comprehensive
2. **Orchestration Integration** (`claude/tools/orchestration/agent_swarm.py`) - Existing, enhanced

---

## Implementation Comparison

| Feature | Standalone (`claude/tools/`) | Orchestration (`orchestration/`) |
|---------|----------------------------|----------------------------------|
| **Purpose** | General-purpose multi-agent coordination | Integration with existing orchestration framework |
| **HandoffParser** | ✅ Included | ✅ Added (2025-10-12) |
| **Agent Registry** | Auto-discovers from `claude/agents/` | Auto-discovers from `claude/agents/` |
| **Context Enrichment** | ✅ Implemented | ✅ Implemented |
| **Circular Prevention** | ✅ Max 5 handoffs | ✅ Max 5 handoffs |
| **Statistics** | ✅ `get_handoff_stats()` + save to file | Basic handoff chain tracking |
| **Performance Metrics** | Basic | ✅ Execution time tracking |
| **Error Handling** | `AgentNotFoundError` | `AgentNotFound` + alternative suggestions |
| **File Size** | 451 lines | 473 lines |
| **Test Suite** | ✅ `test_agent_swarm_simple.py` | None yet |
| **Documentation** | ✅ `swarm_handoff_framework.md` | This guide |
| **Integration** | Standalone, import anywhere | Part of orchestration package |

---

## When to Use Each Implementation

### Use Standalone (`claude/tools/agent_swarm.py`)

**Best For**:
- ✅ New projects starting from scratch
- ✅ Simple multi-agent workflows without existing orchestration
- ✅ Projects needing handoff statistics and learning
- ✅ Quick prototyping and experimentation
- ✅ Scripts and standalone tools

**Example**:
```python
from claude.tools.agent_swarm import execute_swarm_workflow

result = execute_swarm_workflow(
    initial_agent="dns_specialist",
    task={"query": "Setup email authentication"}
)

print(f"Completed in {result['total_handoffs']} handoffs")
```

**Advantages**:
- Simpler imports (`from claude.tools import ...`)
- Comprehensive test suite
- Full documentation
- Statistics and learning capabilities
- Easier to understand for new users

---

### Use Orchestration (`claude/tools/orchestration/agent_swarm.py`)

**Best For**:
- ✅ Integration with existing Maia orchestration framework
- ✅ Projects already using `command_orchestration.md` patterns
- ✅ Complex workflows combining Swarm + Prompt Chains
- ✅ Enterprise systems with orchestration requirements
- ✅ Systems needing execution time tracking

**Example**:
```python
from claude.tools.orchestration.agent_swarm import SwarmOrchestrator

orchestrator = SwarmOrchestrator()
result = orchestrator.execute_with_handoffs(
    initial_agent="dns_specialist",
    task={"query": "Setup email authentication"}
)

# Returns execution_summary with timing
print(f"Execution time: {result['execution_summary']['total_time_ms']}ms")
```

**Advantages**:
- Part of larger orchestration framework
- Performance metrics built-in
- Alternative agent suggestions on error
- More detailed handoff chain entries

---

## Feature Details

### HandoffParser (Both Implementations)

**Purpose**: Extract structured handoff declarations from agent markdown output

**Input Format** (from v2.2 Enhanced agents):
```markdown
HANDOFF DECLARATION:
To: azure_solutions_architect
Reason: Azure DNS configuration needed
Context:
  - Work completed: Public DNS configured
  - Current state: DNS records propagated
  - Next steps: Configure Azure Private DNS
  - Key data: {"domain": "client.com"}
```

**Output**:
```python
AgentHandoff(
    to_agent="azure_solutions_architect",
    context={
        "work_completed": "Public DNS configured",
        "current_state": "DNS records propagated",
        "next_steps": "Configure Azure Private DNS",
        "key_data": {"domain": "client.com"}
    },
    reason="Azure DNS configuration needed"
)
```

**Usage**:
```python
from claude.tools.agent_swarm import HandoffParser
# OR
from claude.tools.orchestration.agent_swarm import HandoffParser

handoff = HandoffParser.extract_handoff(agent_output_text)
if handoff:
    print(f"Handoff to {handoff.to_agent}: {handoff.reason}")
```

---

## Integration with Agent Execution

Both implementations have a `_execute_agent` stub that needs integration with Maia's agent invocation system.

### Integration Steps (Both Implementations)

**1. Load Agent Prompt**:
```python
agent_file = Path(f"claude/agents/{agent_name}_v2.md")
with open(agent_file) as f:
    agent_prompt = f.read()
```

**2. Inject Context**:
```python
full_prompt = f"{agent_prompt}\n\nContext:\n{json.dumps(context, indent=2)}"
```

**3. Execute via LLM**:
```python
# Replace with actual Maia agent execution
response = claude_api.complete(
    prompt=full_prompt,
    model="claude-sonnet-4.5"
)
```

**4. Parse Handoff**:
```python
handoff = HandoffParser.extract_handoff(response.text)
```

**5. Return Result**:
```python
return AgentResult(
    output={"response": response.text},
    handoff=handoff,
    agent_name=agent_name,
    execution_time_ms=response.latency_ms
)
```

---

## Migration Path

### If Using Standalone → Want Orchestration

**Minimal Changes**:
```python
# Before
from claude.tools.agent_swarm import execute_swarm_workflow
result = execute_swarm_workflow(...)

# After
from claude.tools.orchestration.agent_swarm import SwarmOrchestrator
orchestrator = SwarmOrchestrator()
result = orchestrator.execute_with_handoffs(...)
```

**Benefit**: Access to orchestration framework features (command chaining, parallel execution, etc.)

---

### If Using Orchestration → Want Standalone

**Minimal Changes**:
```python
# Before
from claude.tools.orchestration.agent_swarm import SwarmOrchestrator
orchestrator = SwarmOrchestrator()
result = orchestrator.execute_with_handoffs(...)

# After
from claude.tools.agent_swarm import execute_swarm_workflow
result = execute_swarm_workflow(...)
```

**Benefit**: Simpler imports, handoff statistics, easier testing

---

## Recommendation

**For New Projects**: Start with **Standalone** (`claude/tools/agent_swarm.py`)
- Easier to use
- Better documented
- Tested (6/6 tests passing)
- Statistics and learning

**For Existing Orchestration Projects**: Use **Orchestration** (`claude/tools/orchestration/agent_swarm.py`)
- Already integrated
- Performance metrics
- Compatible with existing patterns

**Future**: May consolidate into single implementation after production validation

---

## Files Reference

### Standalone Implementation
- **Framework**: `claude/tools/agent_swarm.py` (451 lines)
- **Tests**: `claude/tools/test_agent_swarm_simple.py` (✅ ALL PASSING)
- **Test (pytest)**: `claude/tools/test_agent_swarm.py` (requires pytest)
- **Documentation**: `claude/context/tools/swarm_handoff_framework.md`

### Orchestration Implementation
- **Framework**: `claude/tools/orchestration/agent_swarm.py` (473 lines)
- **Tests**: None yet (uses orchestration test suite)
- **Documentation**: This guide + `claude/context/core/command_orchestration.md`

---

## Next Steps

### Phase 1: Complete Integration (Estimated: 20 hours)

**For Both Implementations**:
1. Replace `_execute_agent` stub with actual agent invocation (8hr)
2. Test with real DNS → Azure handoff workflow (6hr)
3. Add failure recovery and validation rules (6hr)

### Phase 2: Production Validation (Estimated: 10 hours)

**Metrics to Track**:
- Handoff accuracy: % of correct agent selections
- Context enrichment: % of useful context passed
- Execution overhead: Latency added by handoffs
- User satisfaction: Multi-agent workflow completion rates

### Phase 3: Consolidation Decision (Future)

**Options**:
1. **Keep Both**: Different use cases warrant different implementations
2. **Merge**: Combine best features into single implementation
3. **Deprecate**: Choose one based on production usage

**Decision Criteria**:
- Usage patterns (which gets used more?)
- Feature requirements (which features are essential?)
- Performance data (which performs better?)
- User feedback (which is easier to use?)

---

## Status Summary

| Component | Standalone | Orchestration |
|-----------|-----------|---------------|
| **Core Framework** | ✅ Complete | ✅ Complete |
| **HandoffParser** | ✅ Complete | ✅ Complete |
| **Agent Registry** | ✅ Complete | ✅ Complete |
| **Tests** | ✅ Passing (6/6) | ⏳ Pending |
| **Documentation** | ✅ Complete | ✅ This Guide |
| **Integration** | ⏳ Stub | ⏳ Stub |
| **Production Ready** | 🟡 Framework Yes, Integration No | 🟡 Framework Yes, Integration No |

**Both implementations are ready for agent execution integration** (~20 hours to production).

---

## Questions & Decisions

**Q: Why two implementations?**
A: Standalone was built as comprehensive Phase 1 Task 1.4 completion. Orchestration version already existed and was enhanced with HandoffParser.

**Q: Which should I use?**
A: New projects → Standalone. Existing orchestration → Orchestration.

**Q: Will they be merged?**
A: TBD after production validation. Both have merit.

**Q: Are they compatible?**
A: Yes - both use same AgentHandoff format and v2.2 agent declarations. Can switch between them.

**Q: Which is "official"?**
A: Both. Standalone has better documentation and tests. Orchestration is more integrated.
