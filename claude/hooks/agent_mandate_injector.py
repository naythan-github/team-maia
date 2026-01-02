#!/usr/bin/env python3
"""
Agent Mandate Injector - Phase 229: Mandatory Agent Loading

Purpose:
- Injects actual agent instructions into Claude's context (not just notification)
- Makes agent behavior MANDATORY, not advisory
- Solves "Claude ignores hook output" problem from Phase 228.3

Architecture:
- Called by swarm_auto_loader.py after routing decision
- Reads agent .md file, extracts key behavioral sections
- Outputs strongly-worded mandate that Claude MUST follow

Token Budget: 800-1500 tokens (~3000-6000 chars) per injection
Performance SLA: <50ms

Usage:
    python3 agent_mandate_injector.py <agent_name>

Example:
    python3 agent_mandate_injector.py python_code_reviewer_agent

Output:
    Prints mandate to stdout (captured by hook pipeline → Claude's context)
"""

import sys
import re
from pathlib import Path
from typing import Optional, Dict, List

# Maia root detection
MAIA_ROOT = Path(__file__).parent.parent.parent.absolute()
AGENTS_DIR = MAIA_ROOT / "claude" / "agents"

# Maximum token budget (approximate: 4 chars = 1 token)
MAX_CHARS = 5000  # ~1250 tokens

# Sections to extract (priority order)
PRIORITY_SECTIONS = [
    "Core Behavior Principles",
    "Core Behavior",
    "Core Specialties",
    "Specialties",
    "Key Commands",
    "Commands",
    "Problem-Solving Approach",
    "Issue Classification",
    "Integration Points",
]

# Anti-delegation keywords (behavioral enforcement)
ANTI_DELEGATION_RULES = """
BEHAVIORAL CONSTRAINTS (NON-NEGOTIABLE):
1. You ARE this specialist - respond with this identity and expertise
2. DO NOT use the Task tool to delegate this work to another agent
3. DO NOT spawn subagents for this task - YOU are the specialist
4. If you need a different specialist, use explicit HANDOFF DECLARATION
5. Apply the agent's specific methodology and quality standards
"""


def find_agent_file(agent_name: str) -> Optional[Path]:
    """
    Find agent .md file by name.

    Tries:
    1. {agent_name}.md
    2. {agent_name}_agent.md
    3. {agent_name} without _agent suffix + _agent.md

    Returns:
        Path to agent file or None if not found
    """
    # Direct match
    direct = AGENTS_DIR / f"{agent_name}.md"
    if direct.exists():
        return direct

    # With _agent suffix
    with_suffix = AGENTS_DIR / f"{agent_name}_agent.md"
    if with_suffix.exists():
        return with_suffix

    # Without _agent suffix (if already has it)
    if agent_name.endswith("_agent"):
        base_name = agent_name[:-6]  # Remove "_agent"
        base_file = AGENTS_DIR / f"{base_name}_agent.md"
        if base_file.exists():
            return base_file

    return None


def extract_sections(content: str, sections: List[str]) -> Dict[str, str]:
    """
    Extract named sections from markdown content.

    Args:
        content: Full markdown content
        sections: List of section names to extract

    Returns:
        Dict mapping section name to content
    """
    extracted = {}

    for section_name in sections:
        # Match ## or ### headers with the section name
        pattern = rf'^##+ \s*{re.escape(section_name)}.*?\n(.*?)(?=^##|\Z)'
        match = re.search(pattern, content, re.MULTILINE | re.DOTALL | re.IGNORECASE)

        if match:
            section_content = match.group(1).strip()
            # Limit section size
            if len(section_content) > 1500:
                section_content = section_content[:1500] + "\n[... truncated ...]"
            extracted[section_name] = section_content

    return extracted


def extract_agent_overview(content: str) -> str:
    """
    Extract agent overview/purpose from the beginning of the file.

    Returns:
        Overview text (first ~500 chars before first ## section)
    """
    # Find first ## header
    match = re.search(r'^##', content, re.MULTILINE)
    if match:
        overview = content[:match.start()].strip()
    else:
        overview = content[:500].strip()

    # Clean up header line
    lines = overview.split('\n')
    if lines and lines[0].startswith('#'):
        lines = lines[1:]  # Remove title line

    return '\n'.join(lines[:10]).strip()  # Max 10 lines


def generate_mandate(agent_name: str, agent_file: Path) -> Optional[str]:
    """
    Generate agent mandate from .md file.

    Args:
        agent_name: Name of the agent
        agent_file: Path to agent .md file

    Returns:
        Formatted mandate string or None on error
    """
    try:
        content = agent_file.read_text()
    except IOError:
        return None

    # Extract overview
    overview = extract_agent_overview(content)

    # Extract priority sections
    sections = extract_sections(content, PRIORITY_SECTIONS)

    # Build mandate
    mandate_parts = [
        "=" * 80,
        f"MANDATORY AGENT LOADED: {agent_name.upper()}",
        "THIS IS NOT A SUGGESTION - YOU MUST RESPOND AS THIS SPECIALIST",
        "=" * 80,
        "",
    ]

    # Add overview
    if overview:
        mandate_parts.append("AGENT IDENTITY:")
        mandate_parts.append(overview)
        mandate_parts.append("")

    # Add extracted sections (up to token budget)
    current_chars = sum(len(p) for p in mandate_parts)

    for section_name, section_content in sections.items():
        section_block = f"### {section_name}\n{section_content}\n"

        if current_chars + len(section_block) > MAX_CHARS:
            break

        mandate_parts.append(section_block)
        current_chars += len(section_block)

    # Add anti-delegation rules
    mandate_parts.append("")
    mandate_parts.append(ANTI_DELEGATION_RULES)

    # Add context file reference
    mandate_parts.append("")
    mandate_parts.append(f"Full context: claude/agents/{agent_file.name}")
    mandate_parts.append("=" * 80)

    return '\n'.join(mandate_parts)


def inject_mandate(agent_name: str) -> bool:
    """
    Main entry point: find agent and output mandate.

    Args:
        agent_name: Name of agent to load

    Returns:
        True if mandate output, False otherwise

    Side effects:
        Prints mandate to stdout (captured by hook pipeline)
    """
    agent_file = find_agent_file(agent_name)
    if not agent_file:
        return False

    mandate = generate_mandate(agent_name, agent_file)
    if not mandate:
        return False

    # Output to stdout (hook captures this → Claude's context)
    print(mandate)
    return True


def main():
    """
    CLI entry point.

    Usage:
        python3 agent_mandate_injector.py <agent_name>

    Exit codes:
        0: Success (mandate output)
        1: Agent not found
        2: Error generating mandate
    """
    if len(sys.argv) < 2:
        print("Usage: agent_mandate_injector.py <agent_name>", file=sys.stderr)
        sys.exit(1)

    agent_name = sys.argv[1]

    agent_file = find_agent_file(agent_name)
    if not agent_file:
        print(f"Agent not found: {agent_name}", file=sys.stderr)
        sys.exit(1)

    mandate = generate_mandate(agent_name, agent_file)
    if not mandate:
        print(f"Error generating mandate for: {agent_name}", file=sys.stderr)
        sys.exit(2)

    print(mandate)
    sys.exit(0)


if __name__ == "__main__":
    main()
