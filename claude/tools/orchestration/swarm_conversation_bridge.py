"""
Swarm Conversation Bridge for Claude Code Integration

Bridges Swarm Handoff Framework with Claude Code's conversation model.

Architecture:
- Swarm expects AgentResult from _execute_agent()
- Claude Code works via conversation (user sees agent prompts, responds)
- Bridge connects these two models using conversation-driven execution

Design Pattern:
1. Load agent prompt (AgentLoader)
2. Inject context (from previous agents)
3. Present to Claude Code conversation
4. Parse response (HandoffParser)
5. If handoff → repeat with next agent
6. If no handoff → return final result
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from agent_loader import AgentLoader
from agent_swarm import (
    SwarmOrchestrator,
    AgentResult,
    AgentHandoff,
    HandoffParser
)


class SwarmConversationBridge:
    """
    Bridges Swarm framework with Claude Code conversation execution.

    Two modes of operation:

    **Mode 1: Simulated (for testing)**
    - Loads agent prompts
    - Simulates responses
    - Tests handoff chain logic

    **Mode 2: Conversation-Driven (production)**
    - Loads agent prompts with context
    - Presents to user in conversation
    - User responds as agent
    - Parses handoff declarations
    - Continues chain

    Usage (Testing):
        bridge = SwarmConversationBridge(mode="simulated")
        result = bridge.execute_swarm_workflow(
            initial_agent="dns_specialist",
            task={"query": "Setup email authentication"}
        )

    Usage (Production - within conversation):
        bridge = SwarmConversationBridge(mode="conversation")
        prompt = bridge.get_next_agent_prompt(
            agent_name="dns_specialist",
            context={"query": "..."}
        )
        # Present prompt to conversation
        # User responds as agent
        # Parse response:
        result = bridge.process_agent_response(response_text)
    """

    def __init__(
        self,
        mode: str = "conversation",
        agents_dir: Path = None
    ):
        """
        Initialize bridge.

        Args:
            mode: "conversation" (production) or "simulated" (testing)
            agents_dir: Directory with agent markdown files
        """
        if mode not in ["conversation", "simulated"]:
            raise ValueError(f"Invalid mode: {mode}. Must be 'conversation' or 'simulated'")

        self.mode = mode
        self.agent_loader = AgentLoader(agents_dir)
        self.orchestrator = SwarmOrchestrator(agents_dir or Path("claude/agents"))

        # Conversation state (for mode=conversation)
        self.current_agent: Optional[str] = None
        self.conversation_context: Dict[str, Any] = {}
        self.handoff_chain: list = []

    def execute_swarm_workflow(
        self,
        initial_agent: str,
        task: Dict[str, Any],
        max_handoffs: int = 5
    ) -> Dict[str, Any]:
        """
        Execute swarm workflow (simulated mode).

        For testing handoff chain logic without actual conversation.

        Args:
            initial_agent: Starting agent
            task: Initial task context
            max_handoffs: Maximum handoffs allowed

        Returns:
            {
                "final_output": {...},
                "handoff_chain": [...],
                "agent_prompts_used": [...]  # For inspection
            }
        """
        if self.mode != "simulated":
            raise RuntimeError(
                "execute_swarm_workflow only available in 'simulated' mode. "
                "Use get_next_agent_prompt() for conversation mode."
            )

        # Use simulated responses to test handoff chain
        current_agent = initial_agent
        context = task.copy()
        handoff_chain = []
        agent_prompts = []

        for i in range(max_handoffs + 1):
            # Load agent prompt with context
            agent_prompt = self.agent_loader.load_agent(current_agent)
            full_prompt = self.agent_loader.inject_context(
                agent_prompt,
                context,
                handoff_reason=context.get('handoff_reason')
            )

            agent_prompts.append({
                'agent': current_agent,
                'prompt_length': len(full_prompt),
                'has_handoff_support': agent_prompt.has_handoff_support
            })

            # Simulate agent response
            response = self._simulate_agent_response(
                agent_name=current_agent,
                context=context,
                agent_prompt=agent_prompt
            )

            # Parse for handoff
            handoff = HandoffParser.extract_handoff(response['output'])

            if handoff:
                handoff_chain.append({
                    'from': current_agent,
                    'to': handoff.to_agent,
                    'reason': handoff.reason,
                    'context_keys': list(handoff.context.keys())
                })

                # Enrich context
                context.update(handoff.context)
                context['handoff_reason'] = handoff.reason
                current_agent = handoff.to_agent
            else:
                # Task complete
                return {
                    'final_output': response,
                    'final_agent': current_agent,
                    'handoff_chain': handoff_chain,
                    'total_handoffs': len(handoff_chain),
                    'agent_prompts_used': agent_prompts
                }

        # Max handoffs exceeded
        return {
            'final_output': {'error': 'Max handoffs exceeded'},
            'final_agent': current_agent,
            'handoff_chain': handoff_chain,
            'total_handoffs': len(handoff_chain),
            'agent_prompts_used': agent_prompts
        }

    def get_next_agent_prompt(
        self,
        agent_name: str,
        context: Dict[str, Any],
        handoff_reason: Optional[str] = None
    ) -> str:
        """
        Get agent prompt for conversation execution (production mode).

        Returns complete prompt ready to present in conversation.

        Args:
            agent_name: Agent to execute
            context: Enriched context from previous agents
            handoff_reason: Why this agent was invoked

        Returns:
            Complete agent prompt with injected context

        Usage:
            prompt = bridge.get_next_agent_prompt(
                agent_name="dns_specialist",
                context={"query": "Setup email auth"}
            )
            # Present to conversation:
            # "Executing DNS Specialist with context..."
            # {prompt}
        """
        if self.mode != "conversation":
            raise RuntimeError(
                "get_next_agent_prompt only available in 'conversation' mode"
            )

        # Update conversation state
        self.current_agent = agent_name
        self.conversation_context = context.copy()

        # Load agent prompt
        agent_prompt = self.agent_loader.load_agent(agent_name)

        # Inject context
        full_prompt = self.agent_loader.inject_context(
            agent_prompt,
            context,
            handoff_reason
        )

        return full_prompt

    def process_agent_response(
        self,
        response_text: str
    ) -> Dict[str, Any]:
        """
        Process agent response from conversation (production mode).

        Parses response for handoff declarations.

        Args:
            response_text: Agent's response from conversation

        Returns:
            {
                "handoff": AgentHandoff or None,
                "next_agent": str or None,
                "task_complete": bool
            }

        Usage:
            # After agent responds in conversation:
            result = bridge.process_agent_response(agent_response_text)

            if result['handoff']:
                # Get next agent prompt
                next_prompt = bridge.get_next_agent_prompt(
                    agent_name=result['next_agent'],
                    context=result['handoff'].context,
                    handoff_reason=result['handoff'].reason
                )
                # Present next prompt to conversation
            else:
                # Task complete
                print("Workflow complete!")
        """
        if self.mode != "conversation":
            raise RuntimeError(
                "process_agent_response only available in 'conversation' mode"
            )

        # Parse response for handoff
        handoff = HandoffParser.extract_handoff(response_text)

        if handoff:
            # Record handoff in chain
            self.handoff_chain.append({
                'from': self.current_agent,
                'to': handoff.to_agent,
                'reason': handoff.reason,
                'timestamp': datetime.now().isoformat()
            })

            # Enrich context for next agent
            self.conversation_context.update(handoff.context)

            return {
                'handoff': handoff,
                'next_agent': handoff.to_agent,
                'task_complete': False,
                'handoff_chain': self.handoff_chain
            }
        else:
            # No handoff = task complete
            return {
                'handoff': None,
                'next_agent': None,
                'task_complete': True,
                'final_output': response_text,
                'handoff_chain': self.handoff_chain
            }

    def _simulate_agent_response(
        self,
        agent_name: str,
        context: Dict[str, Any],
        agent_prompt: Any
    ) -> Dict[str, Any]:
        """
        Simulate agent response for testing (simulated mode only).

        Creates realistic responses with handoff declarations for testing.

        Args:
            agent_name: Current agent
            context: Context
            agent_prompt: Loaded agent prompt

        Returns:
            Simulated agent response
        """
        # Simulate handoff logic for testing
        # In reality, agent actually responds in conversation

        # DNS Specialist → Azure Solutions Architect (if Azure-related)
        if agent_name == "dns_specialist" and "azure" in str(context).lower():
            return {
                'output': f"""
I've configured the DNS records for the domain.

HANDOFF DECLARATION:
To: azure_solutions_architect
Reason: Azure DNS configuration needed for hybrid connectivity
Context:
  - Work completed: Public DNS configured, MX records set
  - Current state: DNS records propagated
  - Next steps: Configure Azure Private DNS
  - Key data: {{"domain": "{context.get('domain', 'example.com')}"}}

The DNS foundation is ready for Azure integration.
"""
            }

        # Default: no handoff (task complete)
        return {
            'output': f"Task completed by {agent_name}. No further handoff needed."
        }

    def get_workflow_summary(self) -> Dict[str, Any]:
        """
        Get summary of workflow execution (conversation mode).

        Returns:
            {
                "agents_invoked": [...],
                "total_handoffs": int,
                "handoff_chain": [...]
            }
        """
        return {
            'agents_invoked': list(set([
                h['from'] for h in self.handoff_chain
            ] + [h['to'] for h in self.handoff_chain])),
            'total_handoffs': len(self.handoff_chain),
            'handoff_chain': self.handoff_chain
        }


# Convenience functions for production use

def load_agent_prompt(
    agent_name: str,
    context: Dict[str, Any] = None,
    handoff_reason: str = None
) -> str:
    """
    Load agent prompt for conversation execution.

    Convenience wrapper for production use.

    Usage in Claude Code conversation:
        prompt = load_agent_prompt(
            agent_name="dns_specialist",
            context={"query": "Setup email auth"}
        )
        # Present prompt to conversation
    """
    bridge = SwarmConversationBridge(mode="conversation")
    return bridge.get_next_agent_prompt(agent_name, context or {}, handoff_reason)


def parse_agent_response_for_handoff(response_text: str) -> Optional[AgentHandoff]:
    """
    Parse agent response for handoff declaration.

    Convenience wrapper for production use.

    Usage in Claude Code conversation:
        # After agent responds:
        handoff = parse_agent_response_for_handoff(agent_response)

        if handoff:
            print(f"Handoff to {handoff.to_agent}: {handoff.reason}")
            # Load next agent
        else:
            print("Task complete!")
    """
    return HandoffParser.extract_handoff(response_text)
