# Agent Swarm Framework

**Purpose**: Lightweight multi-agent coordination with systematic handoffs

**Inspired by**: OpenAI Swarm framework
**Source**: `claude/data/AI_SPECIALISTS_AGENT_ANALYSIS.md` Section 3.1

---

## Quick Start

### 1. Initialize Orchestrator

```python
from claude.tools.orchestration.agent_swarm import SwarmOrchestrator

orchestrator = SwarmOrchestrator()
```

### 2. Execute Workflow with Handoffs

```python
result = orchestrator.execute_with_handoffs(
    initial_agent="dns_specialist_agent",
    task={
        "query": "Setup Azure Exchange Online with custom domain",
        "domain": "company.com",
        "users": 500
    },
    max_handoffs=5  # Prevent infinite loops
)

print(f"✅ Task complete after {result['total_handoffs']} handoffs")
print(f"Agents involved: {result['execution_summary']['agents_involved']}")
```

---

## Core Concepts

### 1. Explicit Handoffs

Agents **explicitly declare** when they need another agent:

```python
# Agent declares handoff
handoff = AgentHandoff(
    to_agent="azure_solutions_architect_agent",
    context={
        "dns_setup_complete": True,
        "spf_record": "v=spf1 include:spf.protection.outlook.com -all",
        "next_steps": ["Configure Exchange Online", "Add custom domain"]
    },
    reason="Azure Exchange Online configuration requires Azure expertise"
)

return AgentResult(
    output={"dns_records": [...], "validation": "passed"},
    handoff=handoff
)
```

**Key Principle**: Agents say "I need Agent B because..." (not implicit routing)

### 2. Context Enrichment

Each agent adds to **shared context**:

```
Agent 1 (DNS): context = {"domain": "company.com"}
  ↓ Adds DNS records
Agent 2 (Azure): context = {"domain": "company.com", "dns_records": [...]}
  ↓ Adds Azure config
Agent 3 (SRE): context = {"domain": "company.com", "dns_records": [...], "azure_config": [...]}
```

**Benefit**: Later agents have full history without re-querying

### 3. Handoff Chain (Audit Trail)

Every handoff is recorded:

```python
{
    "from_agent": "dns_specialist_agent",
    "to_agent": "azure_solutions_architect_agent",
    "reason": "Azure configuration required",
    "timestamp": "2025-10-11T15:30:00",
    "context_size_bytes": 2048
}
```

**Use Cases**:
- Debug workflow issues
- Analyze handoff patterns
- Optimize agent coordination
- Generate execution reports

### 4. Circular Handoff Prevention

Maximum handoff limit (default: 5) prevents infinite loops:

```
DNS → Azure → DNS → Azure → DNS → Azure (6th handoff)
❌ MaxHandoffsExceeded: Exceeded 5 handoffs
```

**Protection**: Detects misconfigured handoffs or circular dependencies

---

## Handoff Patterns

### Pattern 1: Sequential Handoff (DNS → Azure)

**Scenario**: DNS setup complete, need Azure configuration

```python
# DNS Specialist Agent
if task_requires_azure_configuration:
    return AgentResult(
        output=dns_work_product,
        handoff=AgentHandoff(
            to_agent="azure_solutions_architect_agent",
            context={"dns_complete": True, "records": [...]},
            reason="Azure Exchange Online configuration required"
        )
    )
```

**Flow**: DNS → Azure → Complete

### Pattern 2: Round-Trip Handoff (SRE → Azure → SRE)

**Scenario**: SRE needs Azure analysis, then implements fix

```python
# SRE Agent (Initial)
if root_cause_is_azure:
    return AgentResult(
        output=initial_assessment,
        handoff=AgentHandoff(
            to_agent="azure_solutions_architect_agent",
            context={"incident_details": [...], "metrics": [...]},
            reason="Need Azure SQL performance analysis"
        )
    )

# Azure Agent
return AgentResult(
    output=azure_analysis,
    handoff=AgentHandoff(
        to_agent="sre_principal_engineer_agent",
        context={"azure_recommendations": [...]},
        reason="SRE to implement Azure SQL optimization"
    )
)

# SRE Agent (Final)
return AgentResult(
    output=fix_implemented,
    handoff=None  # Task complete
)
```

**Flow**: SRE → Azure → SRE → Complete

### Pattern 3: Parallel Consultation (Future Enhancement)

**Scenario**: Get input from multiple agents simultaneously

```python
# Not yet implemented - future enhancement
results = orchestrator.execute_parallel(
    agents=["dns_specialist_agent", "azure_solutions_architect_agent"],
    task=shared_context
)
# Coordinator synthesizes results
```

**Flow**: Coordinator → (DNS + Azure in parallel) → Coordinator → Complete

---

## Integration with Agent Prompts

### Adding Handoff Capability to Agent

Update agent prompt to include handoff guidelines:

````markdown
## Agent Coordination & Handoffs

### When to Hand Off

Hand off to another agent when:
- Task requires expertise outside your domain
- Another agent has specialized tools you don't have
- Multi-phase work where another agent owns next phase

### How to Declare Handoff

Use this pattern in your response:

```python
HANDOFF DECLARATION:
To: [target_agent_name]
Reason: [Why this agent is needed]
Context:
  - Work completed: [What you've accomplished]
  - Current state: [Where things stand]
  - Next steps needed: [What receiving agent should do]
  - Key data: [Relevant information to pass along]
```

### Handoff Decision Matrix

| Scenario | Hand Off To | Reason |
|----------|-------------|--------|
| Azure infrastructure issue | azure_solutions_architect_agent | Azure expertise |
| DNS configuration | dns_specialist_agent | DNS expertise |
| Production incident | sre_principal_engineer_agent | SRE expertise |
| Security assessment | cloud_security_principal_agent | Security expertise |
| Service Desk complaint | service_desk_manager_agent | Complaint analysis |

### Example Handoff

```
USER: "Setup Azure Exchange Online with company.com domain"

AGENT (DNS Specialist):
I've completed the DNS configuration:
- Created SPF record: v=spf1 include:spf.protection.outlook.com -all
- Created DKIM records: selector1._domainkey, selector2._domainkey
- Created DMARC record: v=DMARC1; p=quarantine; rua=mailto:dmarc@company.com
- Validated all records propagated (TTL: 300s)

HANDOFF DECLARATION:
To: azure_solutions_architect_agent
Reason: DNS setup complete, need Azure Exchange Online configuration
Context:
  - Work completed: DNS records configured and validated
  - Current state: Domain ready for Azure integration
  - Next steps needed: Configure Exchange Online, add custom domain, assign licenses
  - Key data: Domain=company.com, Users=500, DNS records validated
```
````

---

## Result Format

```python
{
    "final_output": {
        # Work product from last agent
        "status": "complete",
        "artifacts": [...]
    },
    "final_agent": "azure_solutions_architect_agent",
    "handoff_chain": [
        {
            "from_agent": "dns_specialist_agent",
            "to_agent": "azure_solutions_architect_agent",
            "reason": "Azure configuration required",
            "timestamp": "2025-10-11T15:30:00",
            "context_size_bytes": 2048
        }
    ],
    "total_handoffs": 1,
    "execution_summary": {
        "start_time": "2025-10-11T15:29:45",
        "end_time": "2025-10-11T15:31:20",
        "total_time_ms": 95000,
        "agents_involved": ["dns_specialist_agent", "azure_solutions_architect_agent"]
    }
}
```

---

## Error Handling

### MaxHandoffsExceeded

```python
try:
    result = orchestrator.execute_with_handoffs(
        initial_agent="dns_specialist_agent",
        task=task,
        max_handoffs=3
    )
except MaxHandoffsExceeded as e:
    print(f"❌ Circular handoff detected: {e}")
    # Chain: DNS → Azure → DNS → Azure → DNS → Azure (6th handoff blocked)
```

**Fix**: Review agent handoff logic, ensure termination conditions

### AgentNotFound

```python
try:
    result = orchestrator.execute_with_handoffs(...)
except AgentNotFound as e:
    print(f"❌ Agent not found: {e}")
    # Error includes alternative suggestions
```

**Fix**: Use correct agent name from registry or create missing agent

---

## Files Created

- `claude/tools/orchestration/agent_swarm.py` - Core framework
- `claude/tools/orchestration/README.md` - This documentation

---

## Implementation Status

✅ **Core Framework Complete**:
- AgentHandoff, AgentResult, SwarmOrchestrator classes
- Handoff chain tracking
- Circular handoff prevention
- Agent registry loading
- Error handling with alternatives

⏳ **Integration Pending** (Week 5-8):
- Actual agent execution (LLM calls)
- Handoff declaration parsing from agent responses
- Context enrichment strategies
- Handoff analytics dashboard

⏳ **Agent Updates Pending** (Week 5-20):
- Add handoff guidelines to all 46 agent prompts
- Define handoff decision matrices per agent
- Add few-shot handoff examples
- Test multi-agent workflows

---

## Next Steps

### Week 3-4 (Current)
1. ✅ Build Swarm framework core
2. ✅ Create documentation
3. ⏳ Add handoff guidelines to 5 upgraded agents (DNS, SRE, Azure, Service Desk, AI Specialists)
4. ⏳ Test example workflows (DNS→Azure, SRE→Azure→SRE)

### Week 5-8
1. Integrate with actual agent execution
2. Add handoff guidelines to remaining 41 agents
3. Build handoff analytics dashboard
4. Measure workflow efficiency improvements

### Week 9-12
1. Implement parallel consultation pattern
2. Build coordinator agent for intelligent routing
3. Optimize handoff patterns based on analytics
4. Deploy to production

---

## References

- **Source Document**: `claude/data/AI_SPECIALISTS_AGENT_ANALYSIS.md` Section 3.1
- **OpenAI Swarm**: Lightweight agent coordination primitives
- **Phase 107 Plan**: `claude/data/AGENT_EVOLUTION_PROJECT_PLAN.md` Task 1.4
- **Agent Registry**: `claude/agents/*.md` (49 agents)

---

## Performance Goals

**Target Improvements** (measured via A/B testing):
- Multi-agent task completion: 72% → 90%+ (eliminate handoff failures)
- Context loss during handoffs: 40% → <5% (context enrichment)
- Workflow efficiency: +25-40% (parallel work, optimized routing)
- User satisfaction: 4.2 → 4.6/5.0 (seamless multi-agent coordination)

**Measurement**:
- A/B test multi-agent scenarios (baseline vs Swarm framework)
- Track handoff success rate
- Measure context preservation across handoffs
- Monitor execution time improvements
