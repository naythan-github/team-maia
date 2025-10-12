# Phase 111: Prompt Chain Orchestrator - Production Integration Guide

**Status**: ✅ COMPLETE (100% - 10/10 workflows)
**Last Updated**: 2025-10-12
**Documentation Version**: 1.0

---

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Getting Started](#getting-started)
4. [Core Components](#core-components)
5. [Integration Examples](#integration-examples)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)
8. [API Reference](#api-reference)

---

## Overview

Phase 111 delivers a complete multi-agent orchestration system with:

- **9 Production-Ready Components** (5,700+ lines)
- **152+ Tests** across all systems (100% passing)
- **Complete Observability** (dashboards, metrics, audit trails)
- **Production Resilience** (error recovery, retry logic, checkpoints)

### What You Can Build

- **Complex Workflows**: Multi-step sequential tasks with dependencies
- **Multi-Agent Collaboration**: Parallel coordination via handoffs
- **Production Systems**: Resilient workflows with automatic error recovery
- **Observable Operations**: Real-time monitoring and performance tracking

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    USER REQUEST                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                COORDINATOR AGENT                             │
│  • Intent classification (10 domains, 5 categories)         │
│  • Complexity assessment (1-10 scale)                        │
│  • Routing strategy selection                               │
└────────┬────────────────────────────────┬───────────────────┘
         │                                │
         ▼                                ▼
┌──────────────────┐            ┌──────────────────────┐
│  SINGLE AGENT    │            │  MULTI-AGENT         │
│  Direct routing  │            │  Orchestration       │
└──────────────────┘            └──────┬───────────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                  │
                    ▼                  ▼                  ▼
          ┌─────────────────┐  ┌─────────────┐  ┌─────────────┐
          │ SWARM HANDOFFS  │  │ SEQUENTIAL  │  │   PARALLEL  │
          │ Dynamic routing │  │ CHAINS      │  │   EXECUTION │
          │ 14 v2 agents    │  │ Dependencies│  │   Future    │
          └─────────────────┘  └──────┬──────┘  └─────────────┘
                                      │
                              ┌───────┴────────┐
                              │ ERROR RECOVERY │
                              │ • Retry logic  │
                              │ • Rollback     │
                              │ • Checkpoints  │
                              └───────┬────────┘
                                      │
                          ┌───────────┴─────────────┐
                          │  CONTEXT MANAGEMENT     │
                          │  • Compression          │
                          │  • Archival             │
                          │  • Infinite workflows   │
                          └───────────┬─────────────┘
                                      │
                          ┌───────────┴─────────────┐
                          │  AUDIT & MONITORING     │
                          │  • JSONL audit trails   │
                          │  • Performance metrics  │
                          │  • Real-time dashboard  │
                          └─────────────────────────┘
```

---

## Getting Started

### Quick Start (5 minutes)

```python
# 1. Simple agent execution
from claude.tools.agent_swarm import execute_swarm_workflow

result = execute_swarm_workflow(
    initial_agent="dns_specialist",
    task={"query": "Audit DNS for example.com"}
)
print(result.final_output)

# 2. Sequential workflow (prompt chain)
from claude.tools.orchestration.agent_chain_orchestrator import execute_workflow
from pathlib import Path

execution = execute_workflow(
    workflow_file=Path("claude/workflows/prompt_chains/dns_audit_security_migration_chain.md"),
    initial_input={"domain": "example.com", "include_subdomains": True}
)
print(f"Status: {execution.status}, Subtasks: {execution.success_count}/{len(execution.subtask_executions)}")

# 3. Generate dashboard
from claude.tools.dashboards.multi_agent_dashboard import MultiAgentDashboard

dashboard = MultiAgentDashboard()
markdown = dashboard.generate_dashboard(time_window_hours=24)
print(markdown)
```

### Installation Requirements

**No additional dependencies** - Phase 111 uses only Python standard library.

**File Locations**:
```
maia/
├── claude/
│   ├── agents/                    # 66 agent files (14 v2 with handoffs)
│   ├── workflows/prompt_chains/   # 7 workflow definitions
│   ├── tools/
│   │   ├── agent_swarm.py        # Swarm orchestration
│   │   ├── orchestration/
│   │   │   ├── agent_chain_orchestrator.py
│   │   │   ├── error_recovery.py
│   │   │   └── context_manager.py
│   │   └── dashboards/
│   │       └── multi_agent_dashboard.py
│   └── context/
│       └── session/               # Audit trails & history
```

---

## Core Components

### 1. Coordinator Agent (Automatic Routing)

**Purpose**: Automatically route user requests to the right agent(s)

```python
from claude.tools.agent_coordinator import route_to_agent

# Automatic routing based on intent
result = route_to_agent(
    user_query="Help me configure Azure DNS records",
    context={"user_role": "admin"}
)

# Returns: Routed to DNS Specialist, complexity=6, strategy=single_agent
```

**When to Use**:
- User-facing applications (chatbots, assistants)
- Dynamic routing based on query content
- Unknown task complexity

**Capabilities**:
- **10 Domain Classifications**: Infra, security, data, web, cloud, ops, testing, planning, communication, general
- **5 Categories**: Question, task, analysis, planning, troubleshooting
- **Complexity Assessment**: 1-10 scale with 8 indicators
- **Strategy Selection**: Single agent, swarm, coordinator

### 2. Swarm Handoffs (Dynamic Multi-Agent)

**Purpose**: Agents explicitly hand off work to specialists

```python
from claude.tools.agent_swarm import SwarmOrchestrator

orchestrator = SwarmOrchestrator()

# Start with DNS specialist, may hand off to Azure architect
result = orchestrator.execute_workflow(
    initial_agent="dns_specialist_v2",
    task={"query": "Setup custom domain for Azure App Service"}
)

# Handoff chain: DNS Specialist → Azure Solutions Architect
print(f"Handoffs: {result.total_handoffs}, Final agent: {result.handoff_chain[-1]}")
```

**When to Use**:
- Task requires multiple domains of expertise
- Dynamic workflows (path determined at runtime)
- Agent discovers need for specialist mid-execution

**Handoff Declaration Format** (in agent prompts):
```markdown
HANDOFF DECLARATION:
To: azure_solutions_architect
Reason: Azure-specific configuration needed
Context:
  - Work completed: DNS records configured
  - Next steps: Configure Azure Private DNS
  - Key data: {"domain": "example.com", "dns_records": [...]}
```

**14 Agents with Handoff Support**: DNS Specialist, Azure Solutions Architect, Security Analyst, FinOps Engineer, Data Analyst, Jobs Agent, LinkedIn AI Advisor, Financial Advisor, Principal Cloud Architect, Personal Assistant, DevOps Principal Architect, Email Specialist, Prompt Engineer, Team Knowledge Sharing

### 3. Agent Chain Orchestrator (Sequential Workflows)

**Purpose**: Execute multi-step workflows with dependencies

```python
from claude.tools.orchestration.agent_chain_orchestrator import AgentChainOrchestrator
from pathlib import Path

orchestrator = AgentChainOrchestrator()

# Load workflow definition
workflow = orchestrator.load_workflow(
    Path("claude/workflows/prompt_chains/dns_audit_security_migration_chain.md")
)

# Execute with automatic dependency management
execution = orchestrator.execute_chain(
    workflow=workflow,
    initial_input={
        "domain": "example.com",
        "include_subdomains": True,
        "dns_providers": ["Cloudflare"]
    }
)

# Check results
print(f"Status: {execution.status}")
print(f"Subtasks completed: {execution.success_count}/{len(execution.subtask_executions)}")
print(f"Final output: {execution.final_output}")
```

**When to Use**:
- Multi-step processes with clear sequence
- Each step depends on previous outputs
- Validation required between steps
- Audit trail needed

**Workflow Format** (Markdown):
```markdown
# Workflow Name

## Overview
Description of the workflow...

### Subtask 1: DNS Audit

**Goal**: Discover all DNS records

**Input**:
- `domain`: Primary domain to audit
- `include_subdomains`: Boolean

**Output**:
```json
{
  "dns_inventory": {...},
  "dependencies_mapped": {...}
}
```

**Prompt**:
```
You are the DNS Specialist agent...
CONTEXT:
- Domain: {domain}
TASK: [detailed instructions]
```
```

### 4. Error Recovery System

**Purpose**: Production-resilient execution with retry logic

```python
from claude.tools.orchestration.agent_chain_orchestrator import AgentChainOrchestrator
from claude.tools.orchestration.error_recovery import (
    RecoveryConfig, RecoveryStrategy, RetryConfig, RetryPolicy
)

# Configure retry behavior
recovery_config = RecoveryConfig(
    strategy=RecoveryStrategy.RETRY_THEN_FAIL,
    retry_config=RetryConfig(
        policy=RetryPolicy.EXPONENTIAL,
        max_attempts=5,
        initial_delay_ms=1000,
        max_delay_ms=30000
    )
)

orchestrator = AgentChainOrchestrator(recovery_config=recovery_config)

# Automatic retry on transient failures (network, rate limits)
execution = orchestrator.execute_chain(workflow, initial_input)
```

**When to Use**:
- Production systems requiring high reliability
- Workflows calling external APIs (network failures)
- Rate-limited services
- Long-running processes

**Error Classifications**:
- **TRANSIENT** (retry): Network errors, timeouts, rate limits → Exponential backoff
- **VALIDATION** (fail immediately): Schema errors, invalid input → No retry
- **DEPENDENCY** (skip): Missing variables → Continue chain
- **FATAL** (abort): OOM, permissions → Stop immediately

**4 Recovery Strategies**:
1. **FAIL_FAST**: Stop on first error
2. **CONTINUE_ON_ERROR**: Skip failed tasks, continue
3. **RETRY_THEN_FAIL**: Retry N times, then abort
4. **RETRY_THEN_SKIP**: Retry N times, then skip

### 5. Context Management System

**Purpose**: Handle infinite-length workflows with compression

```python
from claude.tools.orchestration.context_manager import ContextManager

context_mgr = ContextManager()

# Add conversation turns (automatically compresses when needed)
for i in range(100):
    context_mgr.add_turn(
        role="user",
        content=f"Message {i}...",
        metadata={"turn": i}
    )

# Compression happens automatically at token threshold
summary = context_mgr.get_compressed_context()
print(f"Compressed {context_mgr.metrics.turns_archived} turns")
```

**When to Use**:
- Long conversations (>100K tokens)
- Multi-day workflows
- Workflows with large outputs

**Features**:
- Automatic compression at 80% token threshold
- Archival to disk (JSONL format)
- Retrieval of historical turns
- Metrics tracking (compression ratio, archived turns)

### 6. Multi-Agent Dashboard

**Purpose**: Real-time monitoring and performance visualization

```bash
# CLI: Generate dashboard for last 24 hours
python3 claude/tools/dashboards/multi_agent_dashboard.py --hours 24

# Save to file
python3 claude/tools/dashboards/multi_agent_dashboard.py --hours 24 --output dashboard.md
```

```python
# Python API
from claude.tools.dashboards.multi_agent_dashboard import MultiAgentDashboard

dashboard = MultiAgentDashboard()

# Generate markdown
markdown = dashboard.generate_dashboard(time_window_hours=24)
print(markdown)

# Save to file
dashboard.save_dashboard("dashboard.md", time_window_hours=24)
```

**When to Use**:
- Morning standup reviews
- Incident response (current system status)
- Performance optimization (identify slow agents)
- SLA monitoring

**Dashboard Sections**:
- **System Overview**: Success rate, throughput, active agents
- **Recent Workflows**: Last 10 executions with status
- **Agent Performance**: Top 15 agents by activity
- **Error Summary**: Failed workflows grouped by type

---

## Integration Examples

### Example 1: Simple Task (Single Agent)

```python
"""
Use Case: User asks a simple question
Routing: Coordinator → Single Agent
"""

from claude.tools.agent_coordinator import route_to_agent

result = route_to_agent(
    user_query="What is the difference between A and CNAME records?",
    context={}
)

print(result.final_output)
# Routed to: DNS Specialist (single agent, complexity=2)
```

### Example 2: Complex Task (Swarm Handoffs)

```python
"""
Use Case: Setup custom domain for Azure App Service
Routing: DNS Specialist → Azure Solutions Architect
"""

from claude.tools.agent_swarm import execute_swarm_workflow

result = execute_swarm_workflow(
    initial_agent="dns_specialist_v2",
    task={
        "query": "Configure custom domain myapp.example.com for Azure App Service",
        "domain": "example.com",
        "app_service_name": "myapp-prod"
    }
)

print(f"Handoff chain: {' → '.join(result.handoff_chain)}")
print(f"Final output: {result.final_output}")
```

### Example 3: Multi-Step Workflow (Sequential Chain)

```python
"""
Use Case: Complete DNS audit → security assessment → migration plan
Routing: Coordinator → Chain Orchestrator → 3 Sequential Subtasks
"""

from claude.tools.orchestration.agent_chain_orchestrator import execute_workflow
from pathlib import Path

execution = execute_workflow(
    workflow_file=Path("claude/workflows/prompt_chains/dns_audit_security_migration_chain.md"),
    initial_input={
        "domain": "example.com",
        "include_subdomains": True,
        "dns_providers": ["Cloudflare"],
        "security_requirements": "SOC2"
    }
)

# Access sequential outputs
print(f"Audit complete: {execution.subtask_executions[0].output_data}")
print(f"Security assessment: {execution.subtask_executions[1].output_data}")
print(f"Migration plan: {execution.final_output}")
```

### Example 4: Production Workflow (With Error Recovery)

```python
"""
Use Case: Production system calling external APIs
Features: Automatic retry, checkpoint resume, audit trails
"""

from claude.tools.orchestration.agent_chain_orchestrator import AgentChainOrchestrator
from claude.tools.orchestration.error_recovery import (
    RecoveryConfig, RecoveryStrategy, RetryConfig, RetryPolicy
)
from pathlib import Path

# Configure production-grade error recovery
recovery_config = RecoveryConfig(
    strategy=RecoveryStrategy.RETRY_THEN_SKIP,  # Don't fail entire workflow
    retry_config=RetryConfig(
        policy=RetryPolicy.EXPONENTIAL,
        max_attempts=5,
        initial_delay_ms=1000,
        jitter=True  # Prevent thundering herd
    ),
    enable_rollback=True,
    checkpoint_enabled=True
)

orchestrator = AgentChainOrchestrator(recovery_config=recovery_config)

# Load and execute
workflow = orchestrator.load_workflow(Path("claude/workflows/prompt_chains/system_health_bottleneck_optimization_chain.md"))

execution = orchestrator.execute_chain(
    workflow=workflow,
    initial_input={
        "system_inventory": ["web-server-1", "db-server-1"],
        "timeframe": "last_7_days",
        "baseline_metrics": {"p95_latency_ms": 200}
    }
)

# Check retry statistics
for subtask in execution.subtask_executions:
    if subtask.retry_attempts > 0:
        print(f"{subtask.name}: {subtask.retry_attempts} retries")

# Audit trail saved automatically
print(f"Audit trail: context/session/chain_executions/{execution.chain_id}.jsonl")
```

### Example 5: Monitoring & Observability

```python
"""
Use Case: Daily operations review
Features: Real-time dashboard, performance tracking, error analysis
"""

from claude.tools.dashboards.multi_agent_dashboard import MultiAgentDashboard

dashboard = MultiAgentDashboard()

# Morning standup: Yesterday's metrics
yesterday = dashboard.generate_dashboard(time_window_hours=24)
print(yesterday)

# Weekly review: Last 7 days
weekly = dashboard.generate_dashboard(time_window_hours=168)
dashboard.save_dashboard("weekly_report.md", time_window_hours=168)

# Real-time monitoring: Last hour
realtime = dashboard.generate_dashboard(time_window_hours=1)
```

---

## Best Practices

### Workflow Design

**DO**:
✅ Keep subtasks focused (single responsibility)
✅ Define clear input/output schemas
✅ Use descriptive subtask names
✅ Document dependencies explicitly
✅ Include validation rules

**DON'T**:
❌ Create monolithic workflows (>10 subtasks)
❌ Use ambiguous variable names
❌ Skip output validation
❌ Hard-code values in prompts

### Agent Handoffs

**DO**:
✅ Provide complete context in handoff
✅ Explain reason for handoff
✅ Include key data from previous work
✅ Limit handoff chain length (max 5)

**DON'T**:
❌ Hand off without context
❌ Create circular handoff loops
❌ Hand off for trivial tasks

### Error Handling

**DO**:
✅ Use RETRY_THEN_SKIP for production
✅ Enable checkpoints for long workflows
✅ Set appropriate retry limits (3-5)
✅ Use exponential backoff with jitter

**DON'T**:
❌ Use FAIL_FAST in production (too brittle)
❌ Retry validation errors (wastes attempts)
❌ Set delay_ms too high (slow recovery)
❌ Ignore error classifications

### Performance Optimization

**DO**:
✅ Monitor dashboard daily
✅ Identify slow agents (>5s latency)
✅ Optimize prompts to reduce tokens
✅ Use checkpoints for resume capability

**DON'T**:
❌ Ignore partial failures
❌ Skip audit trail analysis
❌ Overlook retry attempt spikes

---

## Troubleshooting

### Issue: Workflow Parser Errors

**Symptom**: Empty subtask names, prompts, or schemas

**Causes**:
- Old workflow format (uses `**Input Variables**:` instead of `**Input**:`)
- Missing markdown sections
- Malformed JSON in schemas

**Solution**:
```python
# Check workflow format
from claude.tools.orchestration.agent_chain_orchestrator import WorkflowParser

parser = WorkflowParser()
try:
    workflow = parser.parse_workflow_file(Path("your_workflow.md"))
    print(f"Parsed {len(workflow['subtasks'])} subtasks")

    # Verify first subtask
    st1 = workflow['subtasks'][0]
    print(f"Name: {st1.name}")
    print(f"Input keys: {list(st1.input_schema.keys())}")
    print(f"Prompt length: {len(st1.prompt_template)} chars")
except Exception as e:
    print(f"Parse error: {e}")
```

**Fix**: Use new format (see `dns_audit_security_migration_chain.md` as template)

### Issue: Handoffs Not Triggering

**Symptom**: Agent completes task instead of handing off

**Causes**:
- Agent not v2 (no handoff training)
- Missing handoff declaration in agent prompt
- Handoff parser not detecting format

**Solution**:
```python
# Check if agent has handoff support
from claude.tools.agent_loader import AgentLoader

loader = AgentLoader()
agents = loader.get_agents_with_handoffs()
print(f"Agents with handoff support: {[a.name for a in agents]}")

# Verify handoff format in agent prompt
# Should include:
# HANDOFF DECLARATION:
# To: <agent_name>
# Reason: <reason>
# Context:
#   - Key: value
```

### Issue: High Retry Attempt Count

**Symptom**: Dashboard shows many retry attempts

**Causes**:
- Flaky external API
- Rate limiting
- Network issues
- Too aggressive retry policy

**Solution**:
```python
# Adjust retry policy
from claude.tools.orchestration.error_recovery import RetryConfig, RetryPolicy

# Increase delays
retry_config = RetryConfig(
    policy=RetryPolicy.EXPONENTIAL,
    max_attempts=3,
    initial_delay_ms=2000,  # Start at 2s
    max_delay_ms=60000,     # Cap at 60s
    jitter=True
)
```

### Issue: Context Manager Compression Failures

**Symptom**: Workflow stops with compression error

**Causes**:
- No write permission to archive directory
- Disk full
- Malformed conversation turn

**Solution**:
```python
# Check archive directory
from pathlib import Path

archive_dir = Path("claude/context/session/context_archive")
if not archive_dir.exists():
    archive_dir.mkdir(parents=True)

# Test write permission
test_file = archive_dir / "test.txt"
test_file.write_text("test")
test_file.unlink()
print("Archive directory writable")
```

---

## API Reference

### AgentChainOrchestrator

```python
class AgentChainOrchestrator:
    """Sequential workflow orchestrator with error recovery"""

    def __init__(self, audit_dir: Path = None, recovery_config: RecoveryConfig = None):
        """
        Args:
            audit_dir: Directory for audit trails (default: context/session/chain_executions)
            recovery_config: Error recovery configuration (default: 3 retries, exponential backoff)
        """

    def load_workflow(self, workflow_file: Path) -> Dict[str, Any]:
        """
        Parse workflow definition file.

        Args:
            workflow_file: Path to markdown workflow file

        Returns:
            Dict with workflow_name, overview, subtasks
        """

    def execute_chain(self, workflow: Dict, initial_input: Dict, chain_id: str = None) -> ChainExecution:
        """
        Execute complete workflow.

        Args:
            workflow: Parsed workflow (from load_workflow)
            initial_input: Initial input data
            chain_id: Optional execution ID

        Returns:
            ChainExecution with status, outputs, audit trail
        """
```

### ErrorRecoverySystem

```python
class ErrorRecoverySystem:
    """Error recovery with retry, rollback, checkpoints"""

    def __init__(self, config: RecoveryConfig):
        """
        Args:
            config: Recovery configuration
        """

    def execute_with_recovery(
        self,
        subtask_id: int,
        subtask_name: str,
        execution_func: Callable,
        rollback_func: Callable = None
    ) -> tuple[bool, Any, ErrorContext]:
        """
        Execute function with automatic retry.

        Args:
            subtask_id: Subtask ID
            subtask_name: Subtask name
            execution_func: Function to execute
            rollback_func: Optional rollback function

        Returns:
            (success, result, error_context)
        """

    def get_recovery_stats(self) -> Dict[str, Any]:
        """Get recovery attempt statistics"""
```

### MultiAgentDashboard

```python
class MultiAgentDashboard:
    """Real-time monitoring dashboard"""

    def __init__(self, base_dir: Path = None):
        """
        Args:
            base_dir: Base directory (default: maia root)
        """

    def generate_dashboard(self, time_window_hours: int = 24) -> str:
        """
        Generate complete dashboard markdown.

        Args:
            time_window_hours: Lookback window

        Returns:
            Markdown string
        """

    def save_dashboard(self, output_path: Path, time_window_hours: int = 24):
        """
        Save dashboard to file.

        Args:
            output_path: Output file path
            time_window_hours: Lookback window
        """
```

---

## Success Metrics

Phase 111 is complete with:

✅ **9 Production-Ready Components**: All tested and documented
✅ **152+ Tests**: 100% passing across all systems
✅ **7 Workflow Definitions**: Ready-to-use examples
✅ **4 Workflow Formats Validated**: Production-tested
✅ **Complete Observability**: Dashboards, metrics, audit trails
✅ **Production Resilience**: Error recovery, retry logic, checkpoints
✅ **Zero External Dependencies**: Pure Python stdlib

---

## Next Steps

### For Developers

1. **Start Simple**: Try the Quick Start examples
2. **Explore Workflows**: Review the 7 pre-built workflow definitions
3. **Create Custom Workflows**: Use the template format
4. **Monitor**: Generate daily dashboards
5. **Optimize**: Use performance metrics to improve

### For Operations

1. **Setup Monitoring**: Schedule daily dashboard generation
2. **Review Metrics**: Check success rates and error patterns
3. **Tune Recovery**: Adjust retry policies based on failure types
4. **Archive Audit Trails**: Implement retention policy for JSONL files

### For Product

1. **Build User Experiences**: Integrate coordinator for automatic routing
2. **Enable Multi-Step Workflows**: Use chain orchestrator for complex tasks
3. **Add Observability**: Expose dashboard metrics to users
4. **Scale Confidently**: Error recovery ensures reliability

---

## Support & Resources

- **System State**: `SYSTEM_STATE.md` (current status, metrics)
- **Project Plan**: `claude/data/AGENT_EVOLUTION_PROJECT_PLAN.md` (full specification)
- **Research Foundation**: `claude/data/PROMPT_ENGINEER_AGENT_ANALYSIS.md` (patterns, best practices)
- **Agent Prompts**: `claude/agents/` (66 agents, 14 v2 with handoffs)
- **Workflow Examples**: `claude/workflows/prompt_chains/` (7 production workflows)
- **Test Suites**: `claude/tools/*/test_*.py` (152+ tests for validation)

---

**End of Phase 111 Integration Guide**

*This guide represents the complete documentation for Phase 111: Prompt Chain Orchestrator, a production-ready multi-agent orchestration system built from 2025-10-11 to 2025-10-12.*
