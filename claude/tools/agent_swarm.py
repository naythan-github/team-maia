"""
Swarm Handoff Framework for Multi-Agent Coordination

Implements OpenAI Swarm-inspired pattern where agents explicitly declare
handoffs to other specialized agents with enriched context.

Based on: claude/data/AGENT_EVOLUTION_PROJECT_PLAN.md Phase 1, Task 1.4
Research: claude/data/AI_SPECIALISTS_AGENT_ANALYSIS.md Section 3.1
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict


class MaxHandoffsExceeded(Exception):
    """Raised when maximum handoffs limit reached (prevents infinite loops)"""
    pass


class AgentNotFoundError(Exception):
    """Raised when target agent not found in registry"""
    pass


@dataclass
class AgentHandoff:
    """Represents a handoff from one agent to another"""

    to_agent: str              # Which agent to hand off to
    context: Dict[str, Any]    # Enriched context for next agent
    reason: str                # Why handoff occurred
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class AgentResult:
    """Result from agent execution with optional handoff"""

    output: Dict[str, Any]           # Agent's work product
    handoff: Optional[AgentHandoff]  # None = task complete, or next agent

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            'output': self.output,
            'handoff': self.handoff.to_dict() if self.handoff else None
        }


class HandoffParser:
    """Parse handoff declarations from agent markdown output"""

    HANDOFF_PATTERN = re.compile(
        r'HANDOFF DECLARATION:\s*\n'
        r'To:\s*([^\n]+)\n'
        r'Reason:\s*([^\n]+)\n'
        r'Context:\s*\n(.*?)(?=\n\n|$)',
        re.DOTALL | re.MULTILINE
    )

    @classmethod
    def extract_handoff(cls, agent_output: str) -> Optional[AgentHandoff]:
        """
        Extract handoff declaration from agent markdown output

        Looks for pattern:
        HANDOFF DECLARATION:
        To: agent_name
        Reason: why handoff needed
        Context:
          - Work completed: ...
          - Current state: ...
          - Next steps: ...
          - Key data: {...}

        Returns:
            AgentHandoff if found, None if no handoff
        """
        match = cls.HANDOFF_PATTERN.search(agent_output)

        if not match:
            return None

        to_agent = match.group(1).strip()
        reason = match.group(2).strip()
        context_text = match.group(3).strip()

        # Parse context section
        context = cls._parse_context(context_text)

        return AgentHandoff(
            to_agent=to_agent,
            context=context,
            reason=reason
        )

    @classmethod
    def _parse_context(cls, context_text: str) -> Dict[str, Any]:
        """Parse context section into structured dict"""
        context = {}

        # Extract key-value pairs from bullet list
        lines = context_text.split('\n')
        current_key = None

        for line in lines:
            line = line.strip()
            if not line or line == '-':
                continue

            # Match "- Key: Value" or "  - Key: Value"
            if line.startswith('- ') or line.startswith('  - '):
                line = line.lstrip('- ').strip()

                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower().replace(' ', '_')
                    value = value.strip()

                    # Try to parse JSON if looks like dict/list
                    if value.startswith('{') or value.startswith('['):
                        try:
                            value = json.loads(value)
                        except json.JSONDecodeError:
                            pass  # Keep as string

                    context[key] = value
                    current_key = key
            elif current_key:
                # Continuation of previous value
                context[current_key] += ' ' + line

        return context


class SwarmOrchestrator:
    """Orchestrates agent handoffs following Swarm pattern"""

    def __init__(self, agents_dir: Path = None):
        """
        Initialize orchestrator

        Args:
            agents_dir: Directory containing agent definitions
                       (defaults to claude/agents/)
        """
        if agents_dir is None:
            # Default to claude/agents/ relative to this file
            agents_dir = Path(__file__).parent.parent / 'agents'

        self.agents_dir = Path(agents_dir)
        self.agent_registry = self._load_agent_registry()
        self.handoff_history: List[Dict] = []

    def execute_with_handoffs(
        self,
        initial_agent: str,
        task: Dict[str, Any],
        max_handoffs: int = 5
    ) -> Dict[str, Any]:
        """
        Execute task with agent handoffs until completion

        Args:
            initial_agent: Starting agent name (e.g., "dns_specialist")
            task: Task dictionary with requirements
            max_handoffs: Maximum handoffs allowed (prevent infinite loops)

        Returns:
            {
                "final_output": {...},
                "handoff_chain": [
                    {
                        "from": "agent1",
                        "to": "agent2",
                        "reason": "...",
                        "context_size": 1234,
                        "timestamp": "2025-01-15T10:30:00"
                    }
                ],
                "total_handoffs": 2
            }

        Raises:
            MaxHandoffsExceeded: If max_handoffs limit reached
            AgentNotFoundError: If target agent not found
        """
        current_agent = initial_agent
        context = task.copy()
        handoff_chain = []

        for i in range(max_handoffs + 1):  # +1 to allow initial agent execution
            # Execute current agent
            result = self._execute_agent(current_agent, context)

            # Track handoff if present
            if result.handoff:
                if i >= max_handoffs:
                    raise MaxHandoffsExceeded(
                        f"Exceeded {max_handoffs} handoffs. "
                        f"Last handoff: {current_agent} → {result.handoff.to_agent}"
                    )

                handoff_info = {
                    "from": current_agent,
                    "to": result.handoff.to_agent,
                    "reason": result.handoff.reason,
                    "context_size": len(str(result.handoff.context)),
                    "timestamp": result.handoff.timestamp.isoformat()
                }
                handoff_chain.append(handoff_info)
                self.handoff_history.append(handoff_info)

                # Enrich context for next agent
                context.update(result.handoff.context)
                context['previous_agent'] = current_agent
                context['handoff_reason'] = result.handoff.reason

                # Switch to next agent
                current_agent = result.handoff.to_agent
            else:
                # Task complete, no more handoffs
                return {
                    "final_output": result.output,
                    "handoff_chain": handoff_chain,
                    "total_handoffs": len(handoff_chain)
                }

        # Should not reach here due to MaxHandoffsExceeded above
        raise MaxHandoffsExceeded(f"Exceeded {max_handoffs} handoffs")

    def _execute_agent(self, agent_name: str, context: Dict[str, Any]) -> AgentResult:
        """
        Execute specific agent with context

        Args:
            agent_name: Agent identifier (e.g., "dns_specialist")
            context: Enriched context from previous agents

        Returns:
            AgentResult with output and optional handoff

        Raises:
            AgentNotFoundError: If agent not in registry
        """
        # Validate agent exists
        if agent_name not in self.agent_registry:
            available = list(self.agent_registry.keys())
            raise AgentNotFoundError(
                f"Agent '{agent_name}' not found. "
                f"Available agents: {', '.join(available[:5])}... "
                f"({len(available)} total)"
            )

        agent_def = self.agent_registry[agent_name]

        # Execute agent with enriched context
        # NOTE: This is a stub - actual execution depends on Maia's agent invocation system
        result = self._call_agent_with_context(agent_def, context)

        return result

    def _call_agent_with_context(
        self,
        agent_def: Dict[str, Any],
        context: Dict[str, Any]
    ) -> AgentResult:
        """
        Call agent with enriched context

        This is a STUB for integration with Maia's agent execution system.

        In production, this would:
        1. Load agent prompt from agent_def['path']
        2. Inject enriched context into prompt
        3. Execute agent via Claude API
        4. Parse output for handoff declarations
        5. Return AgentResult with output and optional handoff

        Args:
            agent_def: Agent registry entry
            context: Enriched context

        Returns:
            AgentResult
        """
        # STUB: For now, return mock result
        # TODO: Integrate with actual Maia agent execution system

        mock_output = {
            "agent": agent_def['name'],
            "status": "executed",
            "context_received": list(context.keys()),
            "note": "STUB: Replace with actual agent execution"
        }

        # No handoff in stub (would be parsed from actual agent output)
        return AgentResult(output=mock_output, handoff=None)

    def _load_agent_registry(self) -> Dict[str, Dict[str, Any]]:
        """
        Load all available agents from claude/agents/

        Returns:
            {
                "dns_specialist": {
                    "name": "dns_specialist",
                    "path": Path("claude/agents/dns_specialist_agent_v2.md"),
                    "version": "v2",
                    "specialties": [...]
                },
                ...
            }
        """
        registry = {}

        if not self.agents_dir.exists():
            raise FileNotFoundError(f"Agents directory not found: {self.agents_dir}")

        # Load all *_v2.md files (upgraded agents with handoff support)
        for agent_file in self.agents_dir.glob('*_v2.md'):
            agent_name = self._extract_agent_name(agent_file.stem)

            registry[agent_name] = {
                'name': agent_name,
                'path': agent_file,
                'version': 'v2',
                'file': agent_file.name
            }

        # Also load v1 agents for backward compatibility
        for agent_file in self.agents_dir.glob('*_agent.md'):
            # Skip if v2 exists
            agent_name = self._extract_agent_name(agent_file.stem)
            if agent_name not in registry:
                registry[agent_name] = {
                    'name': agent_name,
                    'path': agent_file,
                    'version': 'v1',
                    'file': agent_file.name
                }

        return registry

    @staticmethod
    def _extract_agent_name(filename_stem: str) -> str:
        """
        Extract agent name from filename

        Examples:
            dns_specialist_agent_v2 → dns_specialist
            azure_solutions_architect_agent → azure_solutions_architect
        """
        # Remove _agent and _v2 suffixes
        name = filename_stem.replace('_agent_v2', '').replace('_agent', '')
        return name

    def get_handoff_stats(self) -> Dict[str, Any]:
        """
        Get statistics about handoff patterns

        Returns:
            {
                "total_handoffs": 42,
                "unique_paths": 15,
                "most_common_handoffs": [
                    {"from": "dns_specialist", "to": "azure_solutions_architect", "count": 8},
                    ...
                ]
            }
        """
        if not self.handoff_history:
            return {
                "total_handoffs": 0,
                "unique_paths": 0,
                "most_common_handoffs": []
            }

        # Count handoff paths
        path_counts = {}
        for handoff in self.handoff_history:
            path = (handoff['from'], handoff['to'])
            path_counts[path] = path_counts.get(path, 0) + 1

        # Sort by frequency
        sorted_paths = sorted(
            path_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )

        most_common = [
            {
                "from": path[0],
                "to": path[1],
                "count": count
            }
            for path, count in sorted_paths[:10]
        ]

        return {
            "total_handoffs": len(self.handoff_history),
            "unique_paths": len(path_counts),
            "most_common_handoffs": most_common
        }

    def save_handoff_history(self, output_file: Path):
        """Save handoff history to JSON for analysis"""
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump({
                'handoff_history': self.handoff_history,
                'stats': self.get_handoff_stats()
            }, f, indent=2)


# Convenience function for common use case
def execute_swarm_workflow(
    initial_agent: str,
    task: Dict[str, Any],
    max_handoffs: int = 5
) -> Dict[str, Any]:
    """
    Convenience function to execute swarm workflow

    Usage:
        result = execute_swarm_workflow(
            initial_agent="dns_specialist",
            task={
                "query": "Setup email authentication",
                "domain": "example.com"
            }
        )
    """
    orchestrator = SwarmOrchestrator()
    return orchestrator.execute_with_handoffs(initial_agent, task, max_handoffs)
