"""
Agent Loader for Swarm Integration

Loads agent prompts from markdown files and prepares them for execution
within Claude Code conversation context.

Design Philosophy:
- Maia works WITHIN Claude Code (not via API)
- Agents are markdown files loaded into conversation context
- HandoffParser extracts decisions from conversation responses
- Integration is conversation-driven, not API-driven
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class AgentPrompt:
    """Loaded agent prompt ready for injection into conversation"""
    agent_name: str
    prompt_content: str
    agent_file: Path
    version: str  # v1, v2, v2.2
    has_handoff_support: bool
    specialties: List[str]


class AgentLoader:
    """
    Loads and prepares agent prompts for execution.

    Usage within Claude Code conversation:
    1. Load agent prompt from file
    2. Inject enriched context from previous agents
    3. Present to user: "Executing {agent_name} with context..."
    4. Agent responds within conversation
    5. Parse response with HandoffParser
    6. If handoff detected → load next agent
    7. If no handoff → task complete
    """

    def __init__(self, agents_dir: Path = None):
        """
        Initialize agent loader.

        Args:
            agents_dir: Directory containing agent markdown files
                       Defaults to claude/agents/ relative to MAIA_ROOT
        """
        if agents_dir is None:
            # Default to claude/agents/ from repository root
            agents_dir = Path(__file__).parent.parent.parent / 'agents'

        self.agents_dir = Path(agents_dir)
        self.agent_registry = self._scan_agents()

    def _scan_agents(self) -> Dict[str, Dict[str, Any]]:
        """
        Scan agents directory and build registry.

        Returns:
            {
                "dns_specialist": {
                    "name": "dns_specialist",
                    "file": Path(...),
                    "version": "v2",
                    "has_handoff": True
                }
            }
        """
        registry = {}

        if not self.agents_dir.exists():
            raise FileNotFoundError(
                f"Agents directory not found: {self.agents_dir}\n"
                f"Expected: {self.agents_dir.absolute()}"
            )

        # Scan for agent files
        for agent_file in self.agents_dir.glob('*.md'):
            agent_name = self._extract_agent_name(agent_file.stem)
            version = self._determine_version(agent_file.stem)

            # Check if agent has handoff support (v2+ agents with Integration Points)
            has_handoff = self._check_handoff_support(agent_file)

            registry[agent_name] = {
                'name': agent_name,
                'file': agent_file,
                'version': version,
                'has_handoff': has_handoff
            }

        return registry

    def load_agent(self, agent_name: str) -> AgentPrompt:
        """
        Load agent prompt from file.

        Args:
            agent_name: Agent identifier (e.g., "dns_specialist")

        Returns:
            AgentPrompt with loaded content

        Raises:
            KeyError: If agent not found in registry
        """
        if agent_name not in self.agent_registry:
            available = list(self.agent_registry.keys())
            raise KeyError(
                f"Agent '{agent_name}' not found in registry.\n"
                f"Available agents: {', '.join(available[:10])}... "
                f"({len(available)} total)"
            )

        agent_info = self.agent_registry[agent_name]
        agent_file = agent_info['file']

        # Load agent prompt content
        with open(agent_file, 'r', encoding='utf-8') as f:
            prompt_content = f.read()

        # Extract specialties from prompt (for context)
        specialties = self._extract_specialties(prompt_content)

        return AgentPrompt(
            agent_name=agent_name,
            prompt_content=prompt_content,
            agent_file=agent_file,
            version=agent_info['version'],
            has_handoff_support=agent_info['has_handoff'],
            specialties=specialties
        )

    def inject_context(
        self,
        agent_prompt: AgentPrompt,
        context: Dict[str, Any],
        handoff_reason: Optional[str] = None
    ) -> str:
        """
        Inject enriched context into agent prompt.

        Creates complete prompt ready for conversation:
        - Original agent instructions
        - Enriched context from previous agents
        - Handoff reason (if applicable)
        - Clear task framing

        Args:
            agent_prompt: Loaded agent prompt
            context: Enriched context from previous agents
            handoff_reason: Why this agent was invoked (from handoff)

        Returns:
            Complete prompt string ready for conversation
        """
        # Build context injection section
        context_section = self._build_context_section(context, handoff_reason)

        # Combine agent prompt + context
        complete_prompt = f"""
{agent_prompt.prompt_content}

---

## 🔄 SWARM CONTEXT (Enriched from Previous Agents)

{context_section}

---

**Your Task**: Execute the user's request using the above context from previous agents.
If you need another specialist, use the HANDOFF DECLARATION format from your Integration Points section.
"""

        return complete_prompt

    def _build_context_section(
        self,
        context: Dict[str, Any],
        handoff_reason: Optional[str]
    ) -> str:
        """Build formatted context section for agent."""
        lines = []

        if handoff_reason:
            lines.append(f"**Handoff Reason**: {handoff_reason}\n")

        lines.append("**Context from Previous Agents**:")
        for key, value in context.items():
            # Skip internal metadata
            if key.startswith('_'):
                continue

            # Format value (pretty print dicts/lists)
            if isinstance(value, (dict, list)):
                value_str = json.dumps(value, indent=2)
            else:
                value_str = str(value)

            lines.append(f"- **{key}**: {value_str}")

        return "\n".join(lines)

    @staticmethod
    def _extract_agent_name(file_stem: str) -> str:
        """
        Extract agent name from filename.

        Examples:
            dns_specialist_agent_v2 → dns_specialist
            azure_solutions_architect_agent → azure_solutions_architect
        """
        name = file_stem.replace('_agent_v2', '').replace('_agent', '')
        return name

    @staticmethod
    def _determine_version(file_stem: str) -> str:
        """Determine agent version from filename."""
        if '_v2' in file_stem:
            return 'v2'
        return 'v1'

    @staticmethod
    def _check_handoff_support(agent_file: Path) -> bool:
        """Check if agent has handoff support (Integration Points section)."""
        try:
            with open(agent_file, 'r', encoding='utf-8') as f:
                content = f.read()
                return 'Integration Points' in content and 'HANDOFF DECLARATION' in content
        except Exception:
            return False

    @staticmethod
    def _extract_specialties(prompt_content: str) -> List[str]:
        """Extract agent specialties from prompt (for logging/context)."""
        specialties = []

        # Look for Specialties section
        if '## Specialties' in prompt_content:
            lines = prompt_content.split('\n')
            in_specialties = False

            for line in lines:
                if '## Specialties' in line:
                    in_specialties = True
                    continue
                elif in_specialties and line.startswith('##'):
                    # End of specialties section
                    break
                elif in_specialties and line.strip().startswith('-'):
                    # Extract specialty
                    specialty = line.strip().lstrip('- ').split(':')[0]
                    specialties.append(specialty)

        return specialties[:5]  # Top 5 specialties


# Convenience function
def load_agent_for_swarm(agent_name: str, context: Dict[str, Any] = None) -> str:
    """
    Convenience function to load agent with context for Swarm execution.

    Usage in conversation:
        prompt = load_agent_for_swarm("dns_specialist", context={...})
        # Present prompt to user, agent responds
        # Parse response with HandoffParser

    Args:
        agent_name: Agent to load
        context: Enriched context from previous agents

    Returns:
        Complete prompt ready for conversation
    """
    loader = AgentLoader()
    agent_prompt = loader.load_agent(agent_name)

    if context:
        return loader.inject_context(agent_prompt, context)
    else:
        return agent_prompt.prompt_content
