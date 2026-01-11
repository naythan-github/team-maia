"""
Automatic agent handoff generator (Sprint 1).

Generates transfer_to_X functions from agent metadata to enable
automatic agent handoffs based on collaboration patterns.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Callable, Any, Optional


def parse_agent_collaborations(agent_content: str) -> List[Dict[str, str]]:
    """
    Parse agent markdown to extract collaboration partners.

    Args:
        agent_content: Markdown content of agent file

    Returns:
        List of dicts with 'agent' and 'specialty' keys

    Example:
        >>> content = '''
        ... ## Integration Points
        ... **Collaborations**: Python Code Reviewer (code quality), DevOps (CI/CD)
        ... '''
        >>> parse_agent_collaborations(content)
        [
            {"agent": "python_code_reviewer", "specialty": "code quality"},
            {"agent": "devops", "specialty": "CI/CD"}
        ]
    """
    # Find Collaborations line directly (more reliable than section-based parsing)
    collab_match = re.search(
        r'\*\*Collaborations\*\*:\s*(.+?)(?:\n|$)',
        agent_content,
        re.IGNORECASE
    )

    if not collab_match:
        return []

    collab_line = collab_match.group(1).strip()

    # Check for "None" or empty
    if collab_line.lower() == 'none' or not collab_line:
        return []

    # Parse individual collaborations: "Agent Name (specialty)"
    # Pattern: agent_name (specialty), agent_name (specialty)
    collaboration_pattern = r'([^(,]+)\s*\(([^)]+)\)'
    matches = re.findall(collaboration_pattern, collab_line)

    collaborations = []
    for agent_name, specialty in matches:
        # Clean up agent name
        agent_name = agent_name.strip()

        # Convert to snake_case
        # Handle "Python Code Reviewer" -> "python_code_reviewer"
        # Handle "DevOps Principal" -> "devops_principal"
        # Handle "Cloud Security Principal Agent" -> "cloud_security_principal_agent"
        agent_snake = agent_name.lower()
        # Replace spaces with underscores
        agent_snake = re.sub(r'\s+', '_', agent_snake)
        # Remove any non-alphanumeric except underscore
        agent_snake = re.sub(r'[^a-z0-9_]', '', agent_snake)

        collaborations.append({
            "agent": agent_snake,
            "specialty": specialty.strip()
        })

    return collaborations


def generate_handoff_functions(
    collaborations: List[Dict[str, str]]
) -> List[Callable]:
    """
    Generate transfer_to_X functions from collaboration metadata.

    Args:
        collaborations: List of collaboration dicts with 'agent' and 'specialty'

    Returns:
        List of callable handoff functions

    Example:
        >>> collabs = [{"agent": "security_specialist", "specialty": "security audits"}]
        >>> functions = generate_handoff_functions(collabs)
        >>> functions[0].__name__
        'transfer_to_security_specialist'
        >>> result = functions[0]()
        >>> result["handoff_to"]
        'security_specialist'
    """
    functions = []

    for collab in collaborations:
        agent_name = collab["agent"]
        specialty = collab["specialty"]

        # Create the handoff function dynamically
        def create_handoff_function(target_agent: str, target_specialty: str):
            def handoff_function(context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
                """
                Transfer conversation to {target_agent}.

                Specialty: {target_specialty}

                Args:
                    context: Optional context dict to pass to target agent

                Returns:
                    Handoff dict with target agent and context
                """
                result = {
                    "handoff_to": target_agent,
                }
                if context is not None:
                    result["context"] = context
                return result

            # Update docstring with actual values
            handoff_function.__doc__ = handoff_function.__doc__.format(
                target_agent=target_agent,
                target_specialty=target_specialty
            )
            handoff_function.__name__ = f"transfer_to_{target_agent}"

            return handoff_function

        func = create_handoff_function(agent_name, specialty)
        functions.append(func)

    return functions


def generate_tool_schemas(functions: List[Callable]) -> List[Dict[str, Any]]:
    """
    Generate OpenAI-compatible tool schemas for Claude API.

    Args:
        functions: List of handoff functions

    Returns:
        List of tool schema dicts compatible with Claude API

    Example:
        >>> functions = generate_handoff_functions([
        ...     {"agent": "azure_architect", "specialty": "Azure infrastructure"}
        ... ])
        >>> schemas = generate_tool_schemas(functions)
        >>> schemas[0]["name"]
        'transfer_to_azure_architect'
        >>> "Azure infrastructure" in schemas[0]["description"]
        True
    """
    schemas = []

    for func in functions:
        # Extract description from docstring
        description = func.__doc__.strip() if func.__doc__ else f"Transfer to {func.__name__}"

        schema = {
            "name": func.__name__,
            "description": description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "context": {
                        "type": "object",
                        "description": "Optional context to pass to the target agent"
                    }
                },
                "required": []
            }
        }

        schemas.append(schema)

    return schemas


def build_handoff_context(
    current_context: Dict[str, Any],
    agent_output: str,
    source_agent: str,
    handoff_reason: str
) -> Dict[str, Any]:
    """
    Build enriched context for agent handoff.

    Args:
        current_context: Current conversation context
        agent_output: Output from current agent
        source_agent: Name of agent handing off
        handoff_reason: Reason for handoff

    Returns:
        Enriched context dict with handoff metadata

    Example:
        >>> context = {"query": "Setup Azure DNS", "domain": "example.com"}
        >>> enriched = build_handoff_context(
        ...     current_context=context,
        ...     agent_output="Configured public DNS",
        ...     source_agent="dns_specialist",
        ...     handoff_reason="Azure infrastructure needed"
        ... )
        >>> enriched["previous_agent"]
        'dns_specialist'
        >>> enriched["query"]
        'Setup Azure DNS'
    """
    # Start with copy of current context
    enriched = current_context.copy()

    # Truncate agent output if too long (keep last 2000 chars for context)
    max_output_length = 2000
    truncated_output = agent_output
    if len(agent_output) > max_output_length:
        truncated_output = agent_output[-max_output_length:]

    # Add handoff metadata
    enriched.update({
        "previous_agent": source_agent,
        "handoff_reason": handoff_reason,
        "agent_output": truncated_output,
        "handoff_timestamp": datetime.utcnow().isoformat()
    })

    return enriched


class AgentRegistry:
    """
    Agent registry with handoff tool generation.

    Loads agent metadata and generates handoff tools automatically.
    Caches tools for performance.
    """

    def __init__(self, agents_dir: Optional[Path] = None):
        """
        Initialize agent registry.

        Args:
            agents_dir: Path to agents directory (defaults to claude/agents)
        """
        if agents_dir is None:
            # Default to claude/agents relative to this file
            repo_root = Path(__file__).parent.parent.parent
            agents_dir = repo_root / "agents"

        self.agents_dir = Path(agents_dir)
        self._cache: Dict[str, Dict[str, Any]] = {}

    def get(self, agent_name: str) -> Dict[str, Any]:
        """
        Get agent with handoff tools.

        Args:
            agent_name: Agent identifier (e.g., "sre_principal_engineer")

        Returns:
            Dict with agent metadata and handoff_tools list

        Example:
            >>> registry = AgentRegistry()
            >>> agent = registry.get("sre_principal_engineer")
            >>> "handoff_tools" in agent
            True
        """
        # Check cache
        if agent_name in self._cache:
            return self._cache[agent_name]

        # Load agent file
        agent_file = self.agents_dir / f"{agent_name}_agent.md"
        if not agent_file.exists():
            # Try without _agent suffix
            agent_file = self.agents_dir / f"{agent_name}.md"

        if not agent_file.exists():
            raise FileNotFoundError(f"Agent not found: {agent_name}")

        content = agent_file.read_text()
        return self._build_agent_with_tools(agent_name, content)

    def get_with_content(self, agent_name: str, content: str) -> Dict[str, Any]:
        """
        Get agent with handoff tools from provided content.

        Useful for testing.

        Args:
            agent_name: Agent identifier
            content: Agent markdown content

        Returns:
            Dict with agent metadata and handoff_tools list
        """
        return self._build_agent_with_tools(agent_name, content)

    def _build_agent_with_tools(
        self,
        agent_name: str,
        content: str
    ) -> Dict[str, Any]:
        """Build agent dict with handoff tools."""
        # Parse collaborations
        collaborations = parse_agent_collaborations(content)

        # Generate handoff functions
        handoff_tools = generate_handoff_functions(collaborations)

        # Build agent dict
        agent = {
            "name": agent_name,
            "content": content,
            "handoff_tools": handoff_tools,
            "collaborations": collaborations
        }

        # Cache it
        self._cache[agent_name] = agent

        return agent
