#!/usr/bin/env python3
"""
TDD Tests for Agent Mandate Injector (Phase 229)

Tests for:
- FR-1: Mandate injection with actual agent content
- FR-2: Section extraction from agent .md files
- FR-3: Anti-delegation rules enforcement
- FR-4: Token budget compliance

Run: python3 -m pytest claude/hooks/tests/test_mandate_injector.py -v
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestAgentFileFinding:
    """FR-1.1: Agent file discovery"""

    def test_find_agent_file_direct_match(self):
        """Find agent file with exact name"""
        from agent_mandate_injector import find_agent_file

        result = find_agent_file("python_code_reviewer_agent")
        assert result is not None, "Should find python_code_reviewer_agent.md"
        assert result.exists()
        assert result.name == "python_code_reviewer_agent.md"

    def test_find_agent_file_without_suffix(self):
        """Find agent file when _agent suffix is missing"""
        from agent_mandate_injector import find_agent_file

        # Try finding with base name
        result = find_agent_file("sre_principal_engineer")
        # Either finds with _agent suffix or direct
        if result:
            assert result.exists()

    def test_find_agent_file_nonexistent(self):
        """Return None for non-existent agent"""
        from agent_mandate_injector import find_agent_file

        result = find_agent_file("nonexistent_agent_xyz_12345")
        assert result is None, "Should return None for non-existent agent"


class TestSectionExtraction:
    """FR-1.2: Section extraction from markdown"""

    def test_extract_sections_finds_core_behavior(self):
        """Extract Core Behavior section"""
        from agent_mandate_injector import extract_sections

        content = """
# Test Agent

## Core Behavior Principles
- Principle 1
- Principle 2

## Other Section
Content here
"""
        sections = extract_sections(content, ["Core Behavior Principles"])

        assert "Core Behavior Principles" in sections
        assert "Principle 1" in sections["Core Behavior Principles"]

    def test_extract_sections_multiple(self):
        """Extract multiple sections"""
        from agent_mandate_injector import extract_sections

        content = """
# Test Agent

## Core Specialties
- Specialty A
- Specialty B

## Key Commands
| Command | Description |
|---------|-------------|
| cmd1    | Does thing  |
"""
        sections = extract_sections(content, ["Core Specialties", "Key Commands"])

        assert "Core Specialties" in sections
        assert "Key Commands" in sections
        assert "Specialty A" in sections["Core Specialties"]
        assert "cmd1" in sections["Key Commands"]

    def test_extract_sections_truncates_long_content(self):
        """Truncate sections over 1500 chars"""
        from agent_mandate_injector import extract_sections

        long_content = "A" * 2000
        content = f"""
## Long Section
{long_content}
"""
        sections = extract_sections(content, ["Long Section"])

        assert "Long Section" in sections
        assert len(sections["Long Section"]) <= 1600  # 1500 + truncation msg


class TestMandateGeneration:
    """FR-2: Mandate generation"""

    def test_generate_mandate_contains_agent_name(self):
        """Mandate contains agent name in header"""
        from agent_mandate_injector import generate_mandate, find_agent_file

        agent_file = find_agent_file("python_code_reviewer_agent")
        if agent_file:
            mandate = generate_mandate("python_code_reviewer_agent", agent_file)

            assert mandate is not None
            assert "PYTHON_CODE_REVIEWER_AGENT" in mandate.upper()

    def test_generate_mandate_contains_mandatory_text(self):
        """Mandate includes 'MANDATORY' enforcement language"""
        from agent_mandate_injector import generate_mandate, find_agent_file

        agent_file = find_agent_file("python_code_reviewer_agent")
        if agent_file:
            mandate = generate_mandate("python_code_reviewer_agent", agent_file)

            assert "MANDATORY" in mandate.upper()
            assert "NOT A SUGGESTION" in mandate.upper()

    def test_generate_mandate_contains_anti_delegation_rules(self):
        """Mandate includes anti-delegation constraints"""
        from agent_mandate_injector import generate_mandate, find_agent_file

        agent_file = find_agent_file("python_code_reviewer_agent")
        if agent_file:
            mandate = generate_mandate("python_code_reviewer_agent", agent_file)

            assert "DO NOT use the Task tool" in mandate
            assert "HANDOFF DECLARATION" in mandate

    def test_generate_mandate_includes_context_reference(self):
        """Mandate includes path to full agent context"""
        from agent_mandate_injector import generate_mandate, find_agent_file

        agent_file = find_agent_file("python_code_reviewer_agent")
        if agent_file:
            mandate = generate_mandate("python_code_reviewer_agent", agent_file)

            assert "claude/agents/" in mandate


class TestTokenBudget:
    """NFR-1: Token budget compliance"""

    def test_mandate_under_token_limit(self):
        """Mandate stays under 6000 chars (~1500 tokens)"""
        from agent_mandate_injector import generate_mandate, find_agent_file

        agent_file = find_agent_file("python_code_reviewer_agent")
        if agent_file:
            mandate = generate_mandate("python_code_reviewer_agent", agent_file)

            assert len(mandate) < 6000, f"Mandate too long: {len(mandate)} chars"

    def test_mandate_minimum_content(self):
        """Mandate has meaningful content (at least 500 chars)"""
        from agent_mandate_injector import generate_mandate, find_agent_file

        agent_file = find_agent_file("python_code_reviewer_agent")
        if agent_file:
            mandate = generate_mandate("python_code_reviewer_agent", agent_file)

            assert len(mandate) > 500, f"Mandate too short: {len(mandate)} chars"


class TestOverviewExtraction:
    """FR-1.3: Agent overview extraction"""

    def test_extract_agent_overview_finds_purpose(self):
        """Extract agent purpose from overview (content BEFORE first ## section)"""
        from agent_mandate_injector import extract_agent_overview

        # Overview is content BEFORE the first ## header
        content = """# Python Code Reviewer Agent v2.3

**Purpose**: Enforce Python code quality across Maia.
**Target Role**: Principal Python Engineer

---

## Core Behavior
Content here
"""
        overview = extract_agent_overview(content)

        assert "Purpose" in overview or "Principal" in overview


class TestCLI:
    """FR-3: CLI functionality"""

    def test_inject_mandate_returns_true_for_valid_agent(self):
        """inject_mandate returns True when agent found"""
        from agent_mandate_injector import inject_mandate
        import io
        import sys

        # Capture stdout
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured

        try:
            result = inject_mandate("python_code_reviewer_agent")
        finally:
            sys.stdout = old_stdout

        assert result is True
        output = captured.getvalue()
        assert len(output) > 0

    def test_inject_mandate_returns_false_for_invalid_agent(self):
        """inject_mandate returns False for non-existent agent"""
        from agent_mandate_injector import inject_mandate

        result = inject_mandate("nonexistent_agent_xyz_12345")
        assert result is False


class TestIntegration:
    """Integration with swarm_auto_loader"""

    def test_swarm_auto_loader_uses_mandate_injector(self):
        """swarm_auto_loader imports and uses mandate injector"""
        from swarm_auto_loader import get_agent_loading_message

        classification = {
            "confidence": 0.90,
            "complexity": 4,
            "primary_domain": "python_review"
        }

        message = get_agent_loading_message(classification, "python_code_reviewer_agent")

        # Should use mandate injector (long format) not simple message
        assert message is not None
        assert len(message) > 500, "Should use mandate injector, not simple message"
        assert "MANDATORY" in message.upper() or "NOT A SUGGESTION" in message.upper()

    def test_swarm_auto_loader_fallback_when_injector_unavailable(self):
        """Falls back to simple message when injector fails"""
        from swarm_auto_loader import get_agent_loading_message

        classification = {
            "confidence": 0.90,
            "complexity": 4,
            "primary_domain": "general"
        }

        # Use a non-existent agent to force fallback
        message = get_agent_loading_message(classification, "fake_agent_for_fallback_test")

        # Should fallback to simple message
        if message:
            assert "AGENT LOADED" in message.upper()


class TestMultipleAgents:
    """Test with different agent types"""

    @pytest.mark.parametrize("agent_name", [
        "sre_principal_engineer_agent",
        "security_specialist_agent",
        "devops_principal_architect_agent",
    ])
    def test_mandate_generation_for_various_agents(self, agent_name):
        """Mandate works for multiple agent types"""
        from agent_mandate_injector import generate_mandate, find_agent_file

        agent_file = find_agent_file(agent_name)
        if agent_file:  # Only test if agent exists
            mandate = generate_mandate(agent_name, agent_file)

            assert mandate is not None
            assert len(mandate) > 500
            assert agent_name.upper().replace("_AGENT", "") in mandate.upper()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
