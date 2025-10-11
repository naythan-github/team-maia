#!/usr/bin/env python3
"""
Agent Swarm Framework for Maia
===============================

Purpose: Lightweight multi-agent coordination with systematic handoffs

Features:
- Explicit agent handoffs (Agent A declares "I need Agent B because...")
- Context enrichment across handoffs (shared knowledge)
- Handoff chain tracking (audit trail)
- Circular handoff prevention (max handoffs limit)
- Failure recovery (alternative agent suggestions)

Inspired by: OpenAI Swarm framework
Source: claude/data/AI_SPECIALISTS_AGENT_ANALYSIS.md Section 3.1

Usage:
    from claude.tools.orchestration.agent_swarm import SwarmOrchestrator, AgentHandoff

    orchestrator = SwarmOrchestrator()
    result = orchestrator.execute_with_handoffs(
        initial_agent="dns_specialist",
        task={"query": "Setup Azure Exchange Online with custom domain"}
    )
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import json


class MaxHandoffsExceeded(Exception):
    """Raised when handoff limit exceeded (potential infinite loop)"""
    pass


class AgentNotFound(Exception):
    """Raised when requested agent doesn't exist"""
    pass


@dataclass
class AgentHandoff:
    """Represents a handoff from one agent to another

    Attributes:
        to_agent: Target agent name (e.g., "azure_solutions_architect")
        context: Enriched context for next agent (work completed, current state, next steps)
        reason: Why handoff occurred (e.g., "Azure expertise required")
        timestamp: When handoff was declared
    """
    to_agent: str
    context: Dict[str, Any]
    reason: str
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self):
        return asdict(self)


@dataclass
class AgentResult:
    """Result from agent execution with optional handoff

    Attributes:
        output: Agent's work product (analysis, recommendations, artifacts)
        handoff: Optional handoff to another agent (None = task complete)
        agent_name: Which agent produced this result
        execution_time_ms: How long agent took
    """
    output: Dict[str, Any]
    handoff: Optional[AgentHandoff] = None
    agent_name: str = ""
    execution_time_ms: int = 0

    def to_dict(self):
        data = {
            "output": self.output,
            "agent_name": self.agent_name,
            "execution_time_ms": self.execution_time_ms
        }
        if self.handoff:
            data["handoff"] = self.handoff.to_dict()
        return data


@dataclass
class HandoffChainEntry:
    """Single entry in handoff chain audit trail"""
    from_agent: str
    to_agent: str
    reason: str
    timestamp: str
    context_size_bytes: int

    def to_dict(self):
        return asdict(self)


class SwarmOrchestrator:
    """Orchestrates multi-agent workflows with systematic handoffs

    Key Responsibilities:
    1. Execute agents sequentially with handoff support
    2. Track handoff chain (audit trail)
    3. Prevent circular handoffs (max limit)
    4. Enrich context across agent transitions
    5. Suggest alternatives when handoff target unavailable

    Example:
        orchestrator = SwarmOrchestrator()
        result = orchestrator.execute_with_handoffs(
            initial_agent="dns_specialist",
            task={"query": "Setup Exchange Online", "domain": "company.com"}
        )

        # Result includes:
        # - final_output: Work product from last agent
        # - handoff_chain: List of agent transitions
        # - total_handoffs: Count of handoffs
        # - execution_summary: Performance metrics
    """

    def __init__(self, agent_dir: Path = Path("claude/agents")):
        """Initialize orchestrator with agent registry

        Args:
            agent_dir: Path to agent definitions directory
        """
        self.agent_dir = agent_dir
        self.agent_registry = self._load_agent_registry()
        self.handoff_history: List[HandoffChainEntry] = []

    def execute_with_handoffs(
        self,
        initial_agent: str,
        task: Dict[str, Any],
        max_handoffs: int = 5
    ) -> Dict[str, Any]:
        """Execute task with agent handoffs until completion

        Args:
            initial_agent: Starting agent name (e.g., "dns_specialist")
            task: Task dictionary with requirements
            max_handoffs: Maximum handoffs allowed (prevent infinite loops)

        Returns:
            {
                "final_output": Final work product,
                "handoff_chain": List of agent transitions,
                "total_handoffs": Count of handoffs,
                "execution_summary": Performance metrics
            }

        Raises:
            MaxHandoffsExceeded: If handoff limit exceeded
            AgentNotFound: If requested agent doesn't exist
        """
        current_agent = initial_agent
        context = task.copy()
        handoff_chain: List[HandoffChainEntry] = []
        start_time = datetime.now()

        # Validate initial agent exists
        if current_agent not in self.agent_registry:
            raise AgentNotFound(f"Agent '{current_agent}' not found in registry")

        for i in range(max_handoffs + 1):  # +1 to allow max_handoffs actual handoffs
            # Execute current agent
            print(f"🤖 Executing agent: {current_agent}")
            result = self._execute_agent(current_agent, context)

            # Check for handoff
            if result.handoff:
                # Validate handoff target exists
                if result.handoff.to_agent not in self.agent_registry:
                    # Suggest alternatives
                    alternatives = self._suggest_alternative_agents(result.handoff.to_agent)
                    raise AgentNotFound(
                        f"Handoff target '{result.handoff.to_agent}' not found. "
                        f"Alternatives: {', '.join(alternatives)}"
                    )

                # Record handoff in chain
                handoff_entry = HandoffChainEntry(
                    from_agent=current_agent,
                    to_agent=result.handoff.to_agent,
                    reason=result.handoff.reason,
                    timestamp=result.handoff.timestamp,
                    context_size_bytes=len(json.dumps(result.handoff.context))
                )
                handoff_chain.append(handoff_entry)

                print(f"  ↳ Handoff to {result.handoff.to_agent}: {result.handoff.reason}")

                # Check if we've exceeded max handoffs
                if i == max_handoffs:
                    raise MaxHandoffsExceeded(
                        f"Exceeded {max_handoffs} handoffs. "
                        f"Chain: {' → '.join([e.from_agent for e in handoff_chain] + [handoff_chain[-1].to_agent])}"
                    )

                # Enrich context for next agent
                context.update(result.handoff.context)
                context[f"{current_agent}_output"] = result.output
                current_agent = result.handoff.to_agent
            else:
                # Task complete, no more handoffs
                end_time = datetime.now()
                execution_time_ms = int((end_time - start_time).total_seconds() * 1000)

                print(f"✅ Task complete after {len(handoff_chain)} handoffs")

                return {
                    "final_output": result.output,
                    "final_agent": current_agent,
                    "handoff_chain": [e.to_dict() for e in handoff_chain],
                    "total_handoffs": len(handoff_chain),
                    "execution_summary": {
                        "start_time": start_time.isoformat(),
                        "end_time": end_time.isoformat(),
                        "total_time_ms": execution_time_ms,
                        "agents_involved": self._extract_agent_list(handoff_chain, current_agent)
                    }
                }

        # Should never reach here (loop exits via return or exception)
        raise MaxHandoffsExceeded(f"Exceeded {max_handoffs} handoffs")

    def _execute_agent(self, agent_name: str, context: Dict[str, Any]) -> AgentResult:
        """Execute specific agent with context

        NOTE: This is a mock implementation. In production, this would:
        1. Load agent prompt from claude/agents/{agent_name}.md
        2. Inject context into agent prompt
        3. Call LLM with agent prompt + context
        4. Parse agent response for handoff declarations
        5. Return AgentResult with output and optional handoff

        Args:
            agent_name: Agent to execute
            context: Enriched context from previous agents

        Returns:
            AgentResult with output and optional handoff
        """
        agent_def = self.agent_registry[agent_name]

        # MOCK IMPLEMENTATION - In production, call actual agent
        # For now, return mock result
        mock_output = {
            "agent": agent_name,
            "status": "executed",
            "context_received": list(context.keys())
        }

        # Mock handoff decision (in production, agent declares this)
        mock_handoff = None
        # Example: if agent_name == "dns_specialist" and "azure" in context.get("query", "").lower():
        #     mock_handoff = AgentHandoff(
        #         to_agent="azure_solutions_architect",
        #         context={"dns_completed": True, "next_steps": ["Configure Azure"]},
        #         reason="Azure configuration required"
        #     )

        return AgentResult(
            output=mock_output,
            handoff=mock_handoff,
            agent_name=agent_name,
            execution_time_ms=1000  # Mock
        )

    def _load_agent_registry(self) -> Dict[str, Any]:
        """Load all available agents from claude/agents/

        Returns:
            Dictionary mapping agent_name → agent_definition
        """
        registry = {}

        if not self.agent_dir.exists():
            print(f"⚠️  Agent directory not found: {self.agent_dir}")
            return registry

        # Find all agent .md files
        agent_files = list(self.agent_dir.glob("*.md"))

        for agent_file in agent_files:
            agent_name = agent_file.stem  # Filename without .md

            # Load agent definition (in production, parse full agent prompt)
            registry[agent_name] = {
                "name": agent_name,
                "file": str(agent_file),
                "loaded": True
            }

        print(f"✅ Loaded {len(registry)} agents into registry")
        return registry

    def _suggest_alternative_agents(self, target_agent: str) -> List[str]:
        """Suggest alternative agents when target not found

        Uses fuzzy matching on agent names to find similar agents

        Args:
            target_agent: Agent that wasn't found

        Returns:
            List of alternative agent names (max 3)
        """
        # Simple similarity: check if any registry agent name contains target substring
        alternatives = []

        target_lower = target_agent.lower()
        for agent_name in self.agent_registry.keys():
            if target_lower in agent_name.lower() or agent_name.lower() in target_lower:
                alternatives.append(agent_name)

        return alternatives[:3]  # Return top 3 matches

    def _extract_agent_list(self, handoff_chain: List[HandoffChainEntry], final_agent: str) -> List[str]:
        """Extract list of all agents involved in workflow

        Args:
            handoff_chain: List of handoff entries
            final_agent: Final agent that completed task

        Returns:
            List of agent names in execution order
        """
        if not handoff_chain:
            return [final_agent]

        agents = [handoff_chain[0].from_agent]
        for entry in handoff_chain:
            agents.append(entry.to_agent)

        return agents

    def get_handoff_statistics(self) -> Dict[str, Any]:
        """Get statistics on handoff patterns (for analysis)

        Returns:
            {
                "total_workflows": Count of workflows executed,
                "total_handoffs": Total handoffs across all workflows,
                "avg_handoffs_per_workflow": Average,
                "most_common_handoffs": List of (from_agent, to_agent, count),
                "agent_usage": Dict of agent → usage count
            }
        """
        # Placeholder for handoff analytics
        return {
            "total_workflows": 0,
            "total_handoffs": 0,
            "avg_handoffs_per_workflow": 0.0,
            "most_common_handoffs": [],
            "agent_usage": {}
        }


# Example usage and handoff patterns
def example_dns_to_azure_workflow():
    """Example: DNS Specialist → Azure Solutions Architect handoff"""

    orchestrator = SwarmOrchestrator()

    # Task requires DNS setup + Azure configuration
    task = {
        "query": "Setup Azure Exchange Online with custom domain company.com for 500 users",
        "domain": "company.com",
        "users": 500,
        "services": ["Exchange Online", "Teams"]
    }

    # Expected flow:
    # 1. DNS Specialist: Configures SPF, DKIM, DMARC records
    #    → Hands off to Azure Solutions Architect
    # 2. Azure Solutions Architect: Configures Exchange Online with custom domain
    #    → Task complete

    try:
        result = orchestrator.execute_with_handoffs(
            initial_agent="dns_specialist_agent",
            task=task,
            max_handoffs=3
        )

        print("\n" + "="*80)
        print("WORKFLOW EXECUTION COMPLETE")
        print("="*80)
        print(f"Final Agent: {result['final_agent']}")
        print(f"Total Handoffs: {result['total_handoffs']}")
        print(f"Execution Time: {result['execution_summary']['total_time_ms']}ms")
        print(f"Agents Involved: {' → '.join(result['execution_summary']['agents_involved'])}")

        if result['handoff_chain']:
            print("\nHandoff Chain:")
            for i, handoff in enumerate(result['handoff_chain'], 1):
                print(f"  {i}. {handoff['from_agent']} → {handoff['to_agent']}")
                print(f"     Reason: {handoff['reason']}")
                print(f"     Context: {handoff['context_size_bytes']} bytes")

        print("\nFinal Output:")
        print(json.dumps(result['final_output'], indent=2))

    except MaxHandoffsExceeded as e:
        print(f"❌ Error: {e}")
    except AgentNotFound as e:
        print(f"❌ Error: {e}")


def example_incident_response_workflow():
    """Example: Multi-agent incident response (SRE → Azure → SRE)"""

    orchestrator = SwarmOrchestrator()

    task = {
        "query": "URGENT: Database latency spike from 50ms to 2000ms",
        "service": "customer-api",
        "severity": "P1"
    }

    # Expected flow:
    # 1. SRE Principal Engineer: Initial assessment, identifies Azure-related issue
    #    → Hands off to Azure Solutions Architect
    # 2. Azure Solutions Architect: Analyzes Azure SQL performance, provides recommendations
    #    → Hands back to SRE for implementation
    # 3. SRE Principal Engineer: Implements fix, validates resolution
    #    → Task complete

    try:
        result = orchestrator.execute_with_handoffs(
            initial_agent="sre_principal_engineer_agent",
            task=task,
            max_handoffs=5
        )

        print(f"\n✅ Incident resolved after {result['total_handoffs']} handoffs")

    except MaxHandoffsExceeded as e:
        print(f"❌ Circular handoff detected: {e}")


if __name__ == "__main__":
    print("Agent Swarm Framework - Examples\n")

    # Example 1: DNS → Azure workflow
    print("Example 1: DNS Specialist → Azure Solutions Architect")
    print("-" * 80)
    example_dns_to_azure_workflow()

    print("\n\n")

    # Example 2: Multi-agent incident response
    print("Example 2: Multi-Agent Incident Response")
    print("-" * 80)
    example_incident_response_workflow()

    print("\n\n📝 Next Steps:")
    print("  1. Integrate with actual agent execution (LLM calls)")
    print("  2. Add handoff declaration parsing from agent responses")
    print("  3. Implement context enrichment strategies")
    print("  4. Build handoff analytics dashboard")
    print("  5. Update agent prompts with handoff guidelines")
