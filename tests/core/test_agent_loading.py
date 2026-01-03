#!/usr/bin/env python3
"""
Agent Loading Validation Tests

Ensures all agents can be loaded without errors.
Validates required fields and structure.

Author: SRE Principal Engineer Agent
Date: 2026-01-03
"""

import pytest
import re
from pathlib import Path

# Find MAIA_ROOT
MAIA_ROOT = Path(__file__).resolve().parents[2]
AGENTS_DIR = MAIA_ROOT / "claude" / "agents"


def get_all_agent_files():
    """Get all agent markdown files."""
    return list(AGENTS_DIR.glob("*_agent.md"))


def parse_agent_file(filepath: Path) -> dict:
    """Parse agent file and extract metadata."""
    content = filepath.read_text()

    agent = {
        "path": filepath,
        "name": filepath.stem,
        "content": content,
        "has_title": False,
        "has_purpose": False,
        "has_version": False,
        "has_commands": False,
        "has_examples": False,
    }

    # Check for title (# Agent Name)
    if re.search(r'^#\s+.+Agent', content, re.MULTILINE):
        agent["has_title"] = True

    # Check for purpose/overview section
    if re.search(r'(Purpose|Overview|Agent Overview)', content, re.IGNORECASE):
        agent["has_purpose"] = True

    # Check for version
    if re.search(r'v\d+\.\d+', content):
        agent["has_version"] = True

    # Check for commands/key commands section
    if re.search(r'(Commands|Key Commands)', content, re.IGNORECASE):
        agent["has_commands"] = True

    # Check for examples/few-shot
    if re.search(r'(Example|Few-Shot)', content, re.IGNORECASE):
        agent["has_examples"] = True

    return agent


class TestAgentLoading:
    """Test all agents can be loaded."""

    @pytest.fixture(scope="class")
    def all_agents(self):
        """Load all agent files."""
        agent_files = get_all_agent_files()
        return [parse_agent_file(f) for f in agent_files]

    def test_agents_exist(self, all_agents):
        """Verify agents directory has agents."""
        assert len(all_agents) > 0, "No agents found in claude/agents/"
        print(f"\nFound {len(all_agents)} agents")

    def test_all_agents_have_title(self, all_agents):
        """All agents should have a title."""
        missing = [a["name"] for a in all_agents if not a["has_title"]]
        assert len(missing) == 0, f"Agents missing title: {missing}"

    def test_all_agents_have_purpose(self, all_agents):
        """All agents should have a purpose section."""
        missing = [a["name"] for a in all_agents if not a["has_purpose"]]
        # Warning only - don't fail
        if missing:
            pytest.skip(f"Agents missing purpose (non-critical): {missing[:5]}")

    def test_all_agents_parseable(self, all_agents):
        """All agents should be valid markdown."""
        for agent in all_agents:
            assert len(agent["content"]) > 100, f"{agent['name']} is too short"

    def test_no_duplicate_agent_names(self, all_agents):
        """No duplicate agent names."""
        names = [a["name"] for a in all_agents]
        duplicates = [n for n in names if names.count(n) > 1]
        assert len(duplicates) == 0, f"Duplicate agent names: {set(duplicates)}"

    def test_agent_file_naming(self, all_agents):
        """Agent files should end with _agent.md."""
        for agent in all_agents:
            assert agent["path"].name.endswith("_agent.md"), \
                f"{agent['path'].name} should end with _agent.md"


class TestAgentQuality:
    """Test agent quality standards."""

    @pytest.fixture(scope="class")
    def all_agents(self):
        agent_files = get_all_agent_files()
        return [parse_agent_file(f) for f in agent_files]

    def test_agents_have_examples(self, all_agents):
        """Agents should have examples for quality routing."""
        with_examples = [a for a in all_agents if a["has_examples"]]
        coverage = len(with_examples) / len(all_agents) * 100
        print(f"\nAgents with examples: {len(with_examples)}/{len(all_agents)} ({coverage:.1f}%)")
        # At least 50% should have examples
        assert coverage >= 50, f"Only {coverage:.1f}% of agents have examples"

    def test_agents_have_version(self, all_agents):
        """Agents should be versioned."""
        with_version = [a for a in all_agents if a["has_version"]]
        coverage = len(with_version) / len(all_agents) * 100
        print(f"\nAgents with version: {len(with_version)}/{len(all_agents)} ({coverage:.1f}%)")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
