"""
Subagent Prompt Builder

Generates Task tool prompts with agent context injection.
Part of SPRINT-003-SWARM-TASK-ORCHESTRATION.

Usage:
    from claude.tools.orchestration.subagent_prompt_builder import SubagentPromptBuilder

    builder = SubagentPromptBuilder()
    result = builder.build("sre_principal_engineer_agent", "analyze auth system")

    # Then in Claude Code, use Task tool:
    # Task(
    #     subagent_type="general-purpose",
    #     prompt=result.prompt,
    #     model=result.model_recommendation
    # )
"""

from pathlib import Path
from typing import Optional
from dataclasses import dataclass


class AgentNotFoundError(Exception):
    """Raised when specified agent cannot be found or loaded."""


@dataclass
class SubagentPrompt:
    """Container for built subagent prompt."""

    prompt: str
    agent_name: str
    agent_tokens: int  # Approximate token count of agent content
    task_tokens: int  # Approximate token count of task
    total_tokens: int  # Combined estimate
    model_recommendation: str  # "haiku" | "sonnet" | "opus"


# Agent name aliases for common shorthand lookups
AGENT_ALIASES = {
    "sre": "sre_principal_engineer_agent",
    "security": "cloud_security_principal_agent",
    "devops": "devops_principal_architect_agent",
    "python": "python_code_reviewer_agent",
    "terraform": "terraform_azure_specialist_agent",
    "azure": "azure_solutions_architect_agent",
    "infra": "azure_solutions_architect_agent",
    "finops": "finops_engineering_agent",
}


class SubagentPromptBuilder:
    """
    Builds Task tool prompts with agent context injection.

    This class generates prompts that inject agent.md content into Task tool
    subagent prompts, enabling specialized agent behavior without API tokens.

    Example:
        builder = SubagentPromptBuilder()
        result = builder.build("sre_principal_engineer_agent", "analyze auth system")

        # Then call Task tool with result.prompt and result.model_recommendation
    """

    # Token thresholds for model recommendations
    HAIKU_THRESHOLD = 2000  # Below this, use haiku
    SONNET_THRESHOLD = 8000  # Below this, use sonnet; above = opus

    def __init__(self, agents_dir: Optional[Path] = None):
        """
        Initialize with agents directory.

        Args:
            agents_dir: Path to agents directory. If None, uses MAIA_ROOT/claude/agents.
        """
        if agents_dir is None:
            from claude.tools.core.paths import MAIA_ROOT

            self.agents_dir = MAIA_ROOT / "claude" / "agents"
        else:
            self.agents_dir = Path(agents_dir)

    def build(
        self,
        agent_name: str,
        task: str,
        additional_context: Optional[str] = None,
        output_format: Optional[str] = None,
    ) -> SubagentPrompt:
        """
        Build a complete prompt for Task tool subagent.

        Args:
            agent_name: Name of agent (with or without _agent suffix, or alias)
            task: The task description for the subagent
            additional_context: Extra context to include (e.g., file contents)
            output_format: Expected output format (e.g., "JSON", "markdown summary")

        Returns:
            SubagentPrompt with full prompt and metadata

        Raises:
            AgentNotFoundError: If agent file cannot be found
        """
        # Normalize and load agent
        normalized_name = self._normalize_agent_name(agent_name)
        agent_content = self._load_agent(normalized_name)

        # Build the prompt
        prompt_parts = []

        # Agent Context section
        prompt_parts.append("## Agent Context")
        prompt_parts.append("")
        prompt_parts.append(
            "You are operating with the following agent specialization:"
        )
        prompt_parts.append("")
        prompt_parts.append(agent_content)
        prompt_parts.append("")

        # Task section
        prompt_parts.append("## Task")
        prompt_parts.append("")
        prompt_parts.append(task)
        prompt_parts.append("")

        # Additional context section (if provided)
        if additional_context:
            prompt_parts.append("## Additional Context")
            prompt_parts.append("")
            prompt_parts.append(additional_context)
            prompt_parts.append("")

        # Output format section (if provided)
        if output_format:
            prompt_parts.append("## Output Format")
            prompt_parts.append("")
            prompt_parts.append(f"Provide your response in the following format: {output_format}")
            prompt_parts.append("")

        # Combine prompt
        full_prompt = "\n".join(prompt_parts)

        # Calculate token estimates
        agent_tokens = self._estimate_tokens(agent_content)
        task_tokens = self._estimate_tokens(task)
        if additional_context:
            task_tokens += self._estimate_tokens(additional_context)
        if output_format:
            task_tokens += self._estimate_tokens(output_format)

        total_tokens = agent_tokens + task_tokens

        # Determine model recommendation
        model_recommendation = self._recommend_model(total_tokens)

        return SubagentPrompt(
            prompt=full_prompt,
            agent_name=normalized_name,
            agent_tokens=agent_tokens,
            task_tokens=task_tokens,
            total_tokens=total_tokens,
            model_recommendation=model_recommendation,
        )

    def _normalize_agent_name(self, agent_name: str) -> str:
        """
        Normalize agent name to full canonical form.

        Handles:
        - Full name: sre_principal_engineer_agent -> sre_principal_engineer_agent
        - Without suffix: sre_principal_engineer -> sre_principal_engineer_agent
        - Alias: sre -> sre_principal_engineer_agent
        """
        # Check if it's an alias
        if agent_name.lower() in AGENT_ALIASES:
            return AGENT_ALIASES[agent_name.lower()]

        # Add _agent suffix if missing
        if not agent_name.endswith("_agent"):
            candidate_with_suffix = f"{agent_name}_agent"
            # Check if file exists with suffix
            if (self.agents_dir / f"{candidate_with_suffix}.md").exists():
                return candidate_with_suffix

        return agent_name

    def _load_agent(self, agent_name: str) -> str:
        """
        Load agent markdown content.

        Args:
            agent_name: Normalized agent name

        Returns:
            Agent markdown content

        Raises:
            AgentNotFoundError: If agent file cannot be found or loaded
        """
        agent_path = self.agents_dir / f"{agent_name}.md"

        try:
            return agent_path.read_text()
        except FileNotFoundError:
            # Try alternate name without _agent suffix
            if agent_name.endswith("_agent"):
                base_name = agent_name[:-6]  # Remove _agent
                alt_path = self.agents_dir / f"{base_name}.md"
                try:
                    return alt_path.read_text()
                except (FileNotFoundError, IsADirectoryError, PermissionError):
                    pass  # Fall through to error below

            raise AgentNotFoundError(
                f"Agent '{agent_name}' not found at {agent_path}. "
                f"Available agents: {self._list_available_agents()}"
            )
        except IsADirectoryError:
            raise AgentNotFoundError(
                f"Cannot load agent '{agent_name}': path {agent_path} is a directory"
            )
        except PermissionError:
            raise AgentNotFoundError(
                f"Cannot load agent '{agent_name}': permission denied for {agent_path}"
            )
        except UnicodeDecodeError as e:
            raise AgentNotFoundError(
                f"Cannot load agent '{agent_name}': encoding error in {agent_path}: {e}"
            )

    def _list_available_agents(self) -> str:
        """List first 5 available agents for error messages."""
        try:
            agents = sorted(self.agents_dir.glob("*_agent.md"))[:5]
            agent_names = [a.stem for a in agents]
            if len(agent_names) >= 5:
                agent_names.append("...")
            return ", ".join(agent_names)
        except Exception:
            return "(unable to list)"

    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count (rough approximation).

        Uses chars/4 as a simple heuristic that works reasonably well
        for English text with code.

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        return max(1, len(text) // 4)

    def _recommend_model(self, total_tokens: int) -> str:
        """
        Recommend model based on token count.

        - haiku: Fast, cheap, good for small tasks (<2K tokens)
        - sonnet: Balanced, good for medium tasks (<8K tokens)
        - opus: Best quality, for complex/large tasks (>8K tokens)

        Args:
            total_tokens: Estimated total token count

        Returns:
            Model recommendation: "haiku", "sonnet", or "opus"
        """
        if total_tokens < self.HAIKU_THRESHOLD:
            return "haiku"
        elif total_tokens < self.SONNET_THRESHOLD:
            return "sonnet"
        else:
            return "opus"
