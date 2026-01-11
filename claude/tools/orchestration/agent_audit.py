"""
Feature 5.2: Agent Collaboration Audit (F020)
Scan all agents and report collaboration coverage.

This module provides:
- scan_agent_collaborations() - Full agent scan with coverage report
- get_priority_agents_missing_collaborations() - Identify key gaps
- Generate audit reports for tracking collaboration adoption

Purpose:
- Track which agents have Collaborations sections defined
- Identify gaps in collaboration coverage
- Generate recommendations for adding collaborations
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional


def get_maia_root() -> Path:
    """Get MAIA root directory."""
    # claude/tools/orchestration/agent_audit.py -> go up 3 levels
    return Path(__file__).parent.parent.parent.parent.absolute()


def get_agents_directory() -> Path:
    """Get path to agents directory."""
    return get_maia_root() / "claude" / "agents"


def has_collaborations_section(agent_file: Path) -> bool:
    """
    Check if an agent file has a Collaborations section.

    Args:
        agent_file: Path to agent markdown file

    Returns:
        True if agent has ## Collaborations section, False otherwise
    """
    try:
        content = agent_file.read_text()

        # Look for collaboration indicators
        # Common patterns:
        # - "## Collaborations"
        # - "## Agent Collaborations"
        # - "## Common Collaborations"
        lower_content = content.lower()

        return (
            "## collaborations" in lower_content or
            "## agent collaborations" in lower_content or
            "## common collaborations" in lower_content
        )

    except (IOError, UnicodeDecodeError):
        return False


def scan_agent_collaborations() -> Dict[str, Any]:
    """
    Scan all agents and generate collaboration coverage report.

    Returns:
        Report dictionary:
        {
            "total_agents": 90,
            "agents_with_collaborations": 15,
            "agents_missing_collaborations": 75,
            "coverage_percentage": 16.7,
            "agents_with_collab": ["sre_principal_engineer_agent", ...],
            "agents_missing_collab": ["security_specialist_agent", ...]
        }

    Performance: <100ms (scan ~90 agent files)
    Graceful: Never raises, returns empty report on error
    """
    try:
        agents_dir = get_agents_directory()

        if not agents_dir.exists():
            return {
                "total_agents": 0,
                "agents_with_collaborations": 0,
                "agents_missing_collaborations": 0,
                "coverage_percentage": 0.0,
                "agents_with_collab": [],
                "agents_missing_collab": [],
                "error": "Agents directory not found"
            }

        # Scan all .md files in agents directory
        agent_files = list(agents_dir.glob("*.md"))

        agents_with_collab = []
        agents_missing_collab = []

        for agent_file in agent_files:
            agent_name = agent_file.stem  # Remove .md extension

            if has_collaborations_section(agent_file):
                agents_with_collab.append(agent_name)
            else:
                agents_missing_collab.append(agent_name)

        total = len(agent_files)
        with_collab = len(agents_with_collab)
        coverage = (with_collab / total * 100) if total > 0 else 0.0

        report = {
            "total_agents": total,
            "agents_with_collaborations": with_collab,
            "agents_missing_collaborations": len(agents_missing_collab),
            "coverage_percentage": round(coverage, 1),
            "agents_with_collab": sorted(agents_with_collab),
            "agents_missing_collab": sorted(agents_missing_collab)
        }

        # Save report to file
        save_audit_report(report)

        return report

    except Exception as e:
        return {
            "total_agents": 0,
            "agents_with_collaborations": 0,
            "agents_missing_collaborations": 0,
            "coverage_percentage": 0.0,
            "agents_with_collab": [],
            "agents_missing_collab": [],
            "error": str(e)
        }


def get_priority_agents_missing_collaborations(
    priority_agents: List[str]
) -> List[str]:
    """
    Identify priority agents that are missing collaboration definitions.

    Args:
        priority_agents: List of high-priority agent names to check
                        (e.g., ["sre_principal_engineer", "security_specialist"])

    Returns:
        List of priority agents missing collaborations

    Example:
        >>> priority = ["sre_principal_engineer", "security_specialist"]
        >>> missing = get_priority_agents_missing_collaborations(priority)
        >>> print(missing)
        ["security_specialist"]  # If security_specialist has no collaborations
    """
    try:
        agents_dir = get_agents_directory()

        if not agents_dir.exists():
            return []

        missing = []

        for agent_name in priority_agents:
            # Try both with and without _agent suffix
            agent_file = agents_dir / f"{agent_name}.md"
            if not agent_file.exists():
                agent_file = agents_dir / f"{agent_name}_agent.md"

            # Check if file exists and has collaborations
            if agent_file.exists():
                if not has_collaborations_section(agent_file):
                    missing.append(agent_name)
            else:
                # Agent file doesn't exist - also "missing" collaborations
                missing.append(agent_name)

        return missing

    except Exception:
        return []


def save_audit_report(report: Dict[str, Any]) -> bool:
    """
    Save audit report to JSON file.

    Args:
        report: Audit report dictionary

    Returns:
        True if saved successfully, False otherwise
    """
    try:
        maia_root = get_maia_root()
        report_file = maia_root / "claude" / "data" / "agent_collaboration_audit.json"

        # Ensure directory exists
        report_file.parent.mkdir(parents=True, exist_ok=True)

        # Atomic write
        tmp_file = report_file.with_suffix(".tmp")
        with open(tmp_file, 'w') as f:
            json.dump(report, f, indent=2)
        tmp_file.replace(report_file)

        return True

    except (IOError, OSError):
        return False


def load_audit_report() -> Optional[Dict[str, Any]]:
    """
    Load most recent audit report.

    Returns:
        Audit report dictionary or None if not available
    """
    try:
        maia_root = get_maia_root()
        report_file = maia_root / "claude" / "data" / "agent_collaboration_audit.json"

        if not report_file.exists():
            return None

        with open(report_file, 'r') as f:
            return json.load(f)

    except (IOError, json.JSONDecodeError):
        return None
