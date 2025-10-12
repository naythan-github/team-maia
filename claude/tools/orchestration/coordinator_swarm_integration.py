"""
Coordinator + Swarm Integration

Complete integration demonstrating:
1. User query → Coordinator classification
2. Coordinator → Swarm routing decision
3. Swarm orchestration of multi-agent workflows
4. Enriched context flow through agent chain

Usage:
    from coordinator_swarm_integration import route_and_execute

    # Automatically routes to single agent or swarm
    result = route_and_execute("Setup DNS authentication for example.com")
"""

from typing import Dict, Any, Optional
from pathlib import Path

from coordinator_agent import CoordinatorAgent, RoutingDecision
from swarm_conversation_bridge import SwarmConversationBridge, load_agent_prompt
from agent_swarm import AgentResult


class CoordinatorSwarmIntegration:
    """
    Unified entry point for intelligent multi-agent routing.

    Combines:
    - CoordinatorAgent: Intent classification and routing
    - SwarmConversationBridge: Multi-agent workflow execution

    Workflow:
    1. User submits natural language query
    2. Coordinator classifies intent and selects strategy
    3. If swarm needed, SwarmBridge orchestrates agent chain
    4. If single agent, loads agent prompt directly
    5. Returns routing decision + execution instructions
    """

    def __init__(self, mode: str = "conversation"):
        """
        Initialize coordinator + swarm integration.

        Args:
            mode: "conversation" (production) or "simulated" (testing)
        """
        self.coordinator = CoordinatorAgent()
        self.swarm_bridge = SwarmConversationBridge(mode=mode)

    def route(self, user_query: str) -> RoutingDecision:
        """
        Route user query to optimal agent(s).

        Returns routing decision with strategy and agents.
        """
        return self.coordinator.route(user_query)

    def route_and_prepare(self, user_query: str) -> Dict[str, Any]:
        """
        Route query and prepare execution instructions.

        Returns:
            {
                'routing': RoutingDecision,
                'execution_type': 'single_agent' | 'swarm',
                'initial_prompt': str,  # For single agent
                'swarm_config': dict    # For swarm execution
            }
        """
        # Step 1: Route query
        routing = self.coordinator.route(user_query)

        # Step 2: Prepare execution based on strategy
        if routing.strategy == 'single_agent':
            # Single agent: Load prompt with context
            initial_prompt = load_agent_prompt(
                agent_name=routing.initial_agent,
                context=routing.context,
                handoff_reason=f"User query: {user_query}"
            )

            return {
                'routing': routing,
                'execution_type': 'single_agent',
                'initial_prompt': initial_prompt,
                'agent_name': routing.initial_agent
            }

        elif routing.strategy == 'swarm':
            # Swarm: Prepare config for multi-agent execution
            return {
                'routing': routing,
                'execution_type': 'swarm',
                'swarm_config': {
                    'initial_agent': routing.initial_agent,
                    'initial_context': routing.context,
                    'max_iterations': 10,
                    'handoff_reason': f"User query: {user_query}"
                }
            }

        else:
            # Prompt chain (future)
            raise NotImplementedError(f"Strategy {routing.strategy} not yet implemented")

    def execute_swarm(self, swarm_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute swarm workflow.

        Args:
            swarm_config: Config from route_and_prepare()

        Returns:
            Swarm execution result
        """
        return self.swarm_bridge.execute_swarm_workflow(
            initial_agent=swarm_config['initial_agent'],
            task=swarm_config['initial_context'],
            max_handoffs=swarm_config.get('max_iterations', 10)
        )

    def route_and_execute(self, user_query: str) -> Dict[str, Any]:
        """
        Complete end-to-end: Route → Execute → Return result.

        For single agent: Returns prompt to present to user
        For swarm: Executes workflow and returns complete result

        Returns:
            {
                'routing': RoutingDecision,
                'execution_type': str,
                'result': str | AgentResult
            }
        """
        execution = self.route_and_prepare(user_query)

        if execution['execution_type'] == 'single_agent':
            # Single agent: Return prompt for user presentation
            return {
                'routing': execution['routing'],
                'execution_type': 'single_agent',
                'agent_name': execution['agent_name'],
                'prompt': execution['initial_prompt']
            }

        elif execution['execution_type'] == 'swarm':
            # Swarm: Execute workflow
            result = self.execute_swarm(execution['swarm_config'])

            return {
                'routing': execution['routing'],
                'execution_type': 'swarm',
                'result': result,
                'summary': self._create_swarm_summary(result)
            }

    def _create_swarm_summary(self, result: Dict[str, Any]) -> str:
        """Create human-readable summary of swarm execution"""
        handoff_chain = result.get('handoff_chain', [])
        final_output = result.get('final_output', {})

        lines = [
            f"Swarm Execution Complete",
            f"Total Handoffs: {len(handoff_chain)}",
            ""
        ]

        if handoff_chain and len(handoff_chain) > 0:
            # Extract agent chain from handoffs
            agents = []
            for i, handoff in enumerate(handoff_chain):
                if i == 0 and 'from_agent' in handoff:
                    agents.append(handoff['from_agent'])
                if 'to_agent' in handoff:
                    agents.append(handoff['to_agent'])

            if agents:
                lines.append(f"Agent Chain: {' → '.join(agents)}")

        if final_output and isinstance(final_output, dict):
            lines.append("\nFinal Output:")
            for key, value in final_output.items():
                if key != 'full_history':  # Skip verbose history
                    value_str = str(value)[:100] if value else ""
                    lines.append(f"  - {key}: {value_str}...")

        return "\n".join(lines)


# Convenience functions
def route_and_execute(user_query: str, mode: str = "conversation") -> Dict[str, Any]:
    """
    Convenience function for complete routing + execution.

    Args:
        user_query: Natural language query
        mode: "conversation" (production) or "simulated" (testing)

    Returns:
        Execution result (prompt for single agent, or complete result for swarm)

    Examples:
        # Simple query (single agent)
        result = route_and_execute("How do I set up MX records?")
        print(result['prompt'])  # DNS Specialist prompt

        # Complex query (swarm)
        result = route_and_execute("Setup DNS auth and migrate to Azure")
        print(result['summary'])  # Swarm execution summary
    """
    integration = CoordinatorSwarmIntegration(mode=mode)
    return integration.route_and_execute(user_query)


def route_query(user_query: str) -> RoutingDecision:
    """
    Convenience function for routing only (no execution).

    Returns:
        RoutingDecision with strategy and agents
    """
    integration = CoordinatorSwarmIntegration()
    return integration.route(user_query)


# Production usage patterns
def example_single_agent_flow():
    """Example: Simple query → Single agent"""
    result = route_and_execute("How do I configure SPF records?")

    print(f"Execution Type: {result['execution_type']}")
    print(f"Agent: {result['agent_name']}")
    print(f"Routing Confidence: {result['routing'].confidence}")
    print("\n--- Agent Prompt ---")
    print(result['prompt'][:500] + "...")


def example_swarm_flow():
    """Example: Complex query → Swarm execution"""
    result = route_and_execute(
        "Setup email authentication for example.com and configure Azure Exchange Online",
        mode="simulated"  # Use simulated for testing
    )

    print(f"Execution Type: {result['execution_type']}")
    print(f"Routing Strategy: {result['routing'].strategy}")
    print(f"\n{result['summary']}")


def example_routing_inspection():
    """Example: Inspect routing decision without execution"""
    routing = route_query("Migrate 200 users to Azure with DNS and security audit")

    print(f"Strategy: {routing.strategy}")
    print(f"Initial Agent: {routing.initial_agent}")
    print(f"All Agents: {routing.agents}")
    print(f"Confidence: {routing.confidence}")
    print(f"Reasoning: {routing.reasoning}")
    print(f"Complexity: {routing.context.get('complexity')}")
    print(f"Domains: {routing.context.get('domains_involved')}")


if __name__ == '__main__':
    print("=" * 70)
    print("COORDINATOR + SWARM INTEGRATION EXAMPLES")
    print("=" * 70)

    print("\n=== Example 1: Single Agent Flow ===\n")
    example_single_agent_flow()

    print("\n\n=== Example 2: Swarm Flow (Simulated) ===\n")
    example_swarm_flow()

    print("\n\n=== Example 3: Routing Inspection ===\n")
    example_routing_inspection()

    print("\n" + "=" * 70)
    print("Integration ready for production use!")
    print("=" * 70)
