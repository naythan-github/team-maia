"""
Handoff execution engine - Sprint 2 of automatic agent handoffs.

Detects and executes handoffs when an agent returns a handoff tool call.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List


class MaxHandoffsExceeded(Exception):
    """Raised when max handoffs limit is exceeded."""
    pass


# Feature 2.1: Handoff Detection (F006)
def detect_handoff(response: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Detect handoff tool call in Claude response.

    Args:
        response: Claude API response dictionary with 'content' array

    Returns:
        Dict with 'target' and 'context' if handoff detected, None otherwise
    """
    if "content" not in response:
        return None

    content = response.get("content")
    if content is None:
        return None

    for item in content:
        if item.get("type") == "tool_use" and item.get("name", "").startswith("transfer_to_"):
            # Extract target agent name (strip "transfer_to_" prefix)
            target = item["name"][len("transfer_to_"):]

            # Extract context from input
            context = item.get("input", {}).get("context", {})

            return {
                "target": target,
                "context": context
            }

    return None


# Feature 2.2: Agent Executor with Handoff Tools (F007)
@dataclass
class AgentResult:
    """Result from agent execution."""
    agent: str
    output: str
    handoff: Optional[Dict[str, Any]] = None

    @property
    def has_handoff(self) -> bool:
        """Check if result contains a handoff."""
        return self.handoff is not None

    @property
    def complete(self) -> bool:
        """Check if agent completed without handoff."""
        return not self.has_handoff


class AgentExecutor:
    """
    Execute agent with registered handoff tools.

    NOTE: This is a stub/mock for now - doesn't call actual Claude API.
    """

    def execute(
        self,
        agent: str,
        query: str,
        context: Dict[str, Any]
    ) -> AgentResult:
        """
        Execute agent and return result.

        Args:
            agent: Agent name (e.g., "sre_principal_engineer")
            query: User query/request
            context: Additional context for the agent

        Returns:
            AgentResult with agent name, output, and optional handoff
        """
        # Stub implementation - just return a mock result
        # In production, this would:
        # 1. Load agent prompt from claude/agents/{agent}_agent.md
        # 2. Register handoff tools for this agent
        # 3. Call Claude API with agent prompt + tools
        # 4. Parse response for handoff

        output = f"Mock output from {agent} for query: {query}"

        return AgentResult(
            agent=agent,
            output=output,
            handoff=None  # Stub doesn't generate handoffs
        )


# Feature 2.3: Handoff Chain Tracker (F008)
class HandoffChainTracker:
    """Track handoff chain through execution."""

    def __init__(self):
        self._chain: List[Dict[str, Any]] = []

    def add_handoff(self, from_agent: str, to_agent: str, reason: str) -> None:
        """
        Add handoff to chain.

        Args:
            from_agent: Source agent
            to_agent: Target agent
            reason: Reason for handoff
        """
        self._chain.append({
            "from": from_agent,
            "to": to_agent,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        })

    def get_chain(self) -> List[Dict[str, Any]]:
        """Get complete handoff chain."""
        return self._chain.copy()

    def would_be_circular(self, from_agent: str, to_agent: str) -> bool:
        """
        Check if adding this handoff would create a circular pattern.

        Args:
            from_agent: Proposed source agent
            to_agent: Proposed target agent

        Returns:
            True if this would create a circular handoff
        """
        # Build set of all agents that have been involved
        agents_in_chain = set()
        for handoff in self._chain:
            agents_in_chain.add(handoff["from"])
            agents_in_chain.add(handoff["to"])

        # If we're trying to hand back to an agent already in the chain,
        # and that agent handed to something that eventually led to from_agent,
        # it's circular
        if to_agent in agents_in_chain:
            # Check if to_agent appears earlier in chain
            for handoff in self._chain:
                if handoff["from"] == to_agent:
                    # to_agent was a source agent earlier - this is circular
                    return True

        return False


# Feature 2.4: Max Handoffs Guard (F009)
class MaxHandoffsGuard:
    """Prevent infinite handoff loops by limiting max handoffs."""

    def __init__(self, max_handoffs: int = 5):
        """
        Initialize guard.

        Args:
            max_handoffs: Maximum number of handoffs allowed (default 5)
        """
        self.max_handoffs = max_handoffs
        self._count = 0

    def record_handoff(self) -> None:
        """
        Record a handoff. Raises MaxHandoffsExceeded if limit reached.

        Raises:
            MaxHandoffsExceeded: If handoff count exceeds limit
        """
        if self._count >= self.max_handoffs:
            raise MaxHandoffsExceeded(
                f"Maximum handoffs ({self.max_handoffs}) exceeded"
            )
        self._count += 1

    @property
    def is_approaching_limit(self) -> bool:
        """Check if approaching handoff limit (within 1 of limit)."""
        return self._count >= self.max_handoffs - 1


# Feature 2.5: Handoff Result Aggregator (F010)
@dataclass
class AggregatedResult:
    """Aggregated result from multi-agent workflow."""
    combined_output: str
    handoff_count: int
    agents_involved: List[str]
    final_agent: str = ""
    total_duration: float = 0.0


def aggregate_results(results: List[AgentResult]) -> AggregatedResult:
    """
    Aggregate results from multiple agents.

    Args:
        results: List of AgentResult from handoff chain

    Returns:
        AggregatedResult with combined output and metadata
    """
    if not results:
        return AggregatedResult(
            combined_output="",
            handoff_count=0,
            agents_involved=[],
            final_agent="",
            total_duration=0.0
        )

    # Build combined output with agent attribution
    combined_parts = []
    agents_involved = []
    handoff_count = 0

    for result in results:
        agents_involved.append(result.agent)

        # Add agent-attributed output
        combined_parts.append(f"[{result.agent}]: {result.output}")

        # Count handoffs
        if result.has_handoff:
            handoff_count += 1

    combined_output = "\n\n".join(combined_parts)
    final_agent = results[-1].agent if results else ""

    return AggregatedResult(
        combined_output=combined_output,
        handoff_count=handoff_count,
        agents_involved=agents_involved,
        final_agent=final_agent,
        total_duration=0.0  # Stub - would track actual duration in production
    )
