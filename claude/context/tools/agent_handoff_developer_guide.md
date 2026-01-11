# Agent Handoff Developer Guide

## Overview
This guide explains how to add automatic handoff capabilities to Maia agents.

## Quick Start

### 1. Add Collaborations Section
Add a Collaborations line to your agent's Integration Points section:

```markdown
## Integration Points

### Explicit Handoff Declaration
[existing content]

**Collaborations**: Security Specialist (security audits), DevOps Principal (CI/CD), Azure Architect (infrastructure)
```

### 2. Verify Handoff Tools Generated
```python
from claude.tools.orchestration.handoff_generator import AgentRegistry

registry = AgentRegistry()
agent = registry.get("your_agent_name")
print(agent["handoff_tools"])  # Shows transfer_to_X functions
```

### 3. Test Handoffs
```python
from claude.tools.orchestration.swarm_integration import IntegratedSwarmOrchestrator

orchestrator = IntegratedSwarmOrchestrator()
orchestrator.set_mock_responses([...])  # Mock for testing
result = orchestrator.execute_with_handoffs(
    initial_agent="your_agent",
    task={"query": "Test task"},
    max_handoffs=3
)
```

## Collaboration Format

Format: `Agent Name (specialty), Agent Name (specialty), ...`

- **Agent Name**: Human-readable name (converted to snake_case automatically)
- **Specialty**: Brief description of what they handle (used in tool description)

Examples:
- `Python Code Reviewer (code quality)` → `transfer_to_python_code_reviewer`
- `Azure Solutions Architect (Azure infrastructure)` → `transfer_to_azure_solutions_architect`

## How Handoffs Work

1. Agent executes and includes handoff tool in available tools
2. If agent decides handoff needed, it calls `transfer_to_X(context={...})`
3. SwarmOrchestrator detects handoff tool call
4. Context is enriched with previous agent's work
5. Target agent executes with enriched context
6. Process repeats until no handoff or max_handoffs reached

## Handoff Decision Guidelines

Agents should hand off when:
- Task requires expertise outside their domain
- Another specialist can complete work more effectively
- Work is blocked pending another agent's output

Agents should NOT hand off when:
- They can complete the task themselves
- The task is trivial
- Handoff would just delay completion

## Debugging Handoffs

### Check Agent Has Collaborations
```bash
grep -l "Collaborations" claude/agents/*.md
```

### Run Agent Audit
```python
from claude.tools.orchestration.agent_audit import scan_agent_collaborations
report = scan_agent_collaborations()
print(f"Coverage: {report['coverage_percentage']}%")
```

### View Handoff Chain
```python
result = orchestrator.execute_with_handoffs(...)
for handoff in result.handoff_chain:
    print(f"{handoff['from']} → {handoff['to']}: {handoff.get('reason', 'N/A')}")
```

### Check Session State
```bash
cat ~/.maia/sessions/swarm_session_*.json | jq '.handoff_chain'
```

## Testing Handoff-Enabled Agents

### Unit Test
```python
def test_agent_has_handoff_tools():
    registry = AgentRegistry()
    agent = registry.get("my_agent")
    assert len(agent["handoff_tools"]) > 0
```

### Integration Test
```python
def test_agent_hands_off_correctly():
    orchestrator = IntegratedSwarmOrchestrator()
    orchestrator.set_mock_responses([
        {"content": [{"type": "tool_use", "name": "transfer_to_target", "input": {}}]},
        {"content": [{"type": "text", "text": "Complete"}]}
    ])
    result = orchestrator.execute_with_handoffs(
        initial_agent="my_agent",
        task={"query": "Test"},
        max_handoffs=2
    )
    assert result.handoff_chain[0]["to"] == "target"
```

## Common Issues

### "Agent not found"
- Check agent file exists: `claude/agents/{name}_agent.md`
- Verify name conversion: "Python Code Reviewer" → "python_code_reviewer"

### "No handoff tools generated"
- Ensure Collaborations line is in Integration Points section
- Format must be: `**Collaborations**: Agent (specialty), ...`

### "Handoff not detected"
- Tool call must use `transfer_to_` prefix
- Check response structure matches expected format

## Best Practices

1. **Limit collaborations to 3-5 agents** - Too many creates decision paralysis
2. **Use specific specialties** - "security audits" better than "security"
3. **Test handoff chains** - Verify multi-hop workflows work
4. **Monitor handoff patterns** - Use analytics to optimize

## Example Agent Integration

```markdown
# My Specialist Agent

## Purpose
Expert in data analysis and visualization.

## Capabilities
- Statistical analysis
- Data visualization
- Report generation

## Integration Points

### Explicit Handoff Declaration
This agent can collaborate with other specialists when needed.

**Collaborations**: Python Code Reviewer (code quality), Security Specialist (data privacy), UI Systems Agent (dashboard creation)

### When to Hand Off
- Code review needed: Python Code Reviewer
- Security concerns: Security Specialist
- UI/dashboard work: UI Systems Agent

## Usage
...
```

This creates three handoff tools:
- `transfer_to_python_code_reviewer` - For code quality reviews
- `transfer_to_security_specialist` - For security/privacy concerns
- `transfer_to_ui_systems_agent` - For dashboard creation
