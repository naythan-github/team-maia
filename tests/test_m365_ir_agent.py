"""
Test suite for M365 Incident Response Agent v2.3

Tests agent definition compliance with Maia v2.3 agent standards.
"""

import pytest
import re
from pathlib import Path


# Agent paths - experimental first, then production
EXPERIMENTAL_PATH = Path("claude/tools/experimental/m365_incident_response_agent.md")
PRODUCTION_PATH = Path("claude/agents/m365_incident_response_agent.md")


def get_agent_path():
    """Return the agent path (experimental or production)."""
    if EXPERIMENTAL_PATH.exists():
        return EXPERIMENTAL_PATH
    elif PRODUCTION_PATH.exists():
        return PRODUCTION_PATH
    else:
        pytest.skip("Agent file not found in experimental or production paths")


def get_agent_content():
    """Load agent content."""
    path = get_agent_path()
    return path.read_text()


class TestAgentV23Format:
    """Test agent follows v2.3 format standards."""

    def test_has_agent_overview_section(self):
        """Agent must have Agent Overview section with Purpose and Target Role."""
        content = get_agent_content()
        assert "## Agent Overview" in content, "Missing Agent Overview section"
        assert "**Purpose**:" in content, "Missing Purpose in Agent Overview"
        assert "**Target Role**:" in content, "Missing Target Role in Agent Overview"

    def test_has_core_behavior_principles(self):
        """Agent must have Core Behavior Principles section."""
        content = get_agent_content()
        assert "## Core Behavior Principles" in content, "Missing Core Behavior Principles"
        assert "Persistence & Completion" in content, "Missing Persistence & Completion principle"
        assert "Tool-Calling Protocol" in content, "Missing Tool-Calling Protocol"
        assert "Systematic Planning" in content, "Missing Systematic Planning"

    def test_has_core_specialties(self):
        """Agent must have Core Specialties section."""
        content = get_agent_content()
        assert "## Core Specialties" in content, "Missing Core Specialties section"

    def test_has_key_commands(self):
        """Agent must have Key Commands table."""
        content = get_agent_content()
        assert "## Key Commands" in content, "Missing Key Commands section"
        assert "| Command |" in content, "Missing Key Commands table"

    def test_has_fewshot_examples(self):
        """Agent must have at least one few-shot example."""
        content = get_agent_content()
        assert "## Few-Shot Example" in content, "Missing Few-Shot Example section"
        # Check for complete example structure
        assert "USER:" in content, "Few-shot missing USER prompt"
        assert "THOUGHT:" in content, "Few-shot missing THOUGHT"
        assert "PLAN:" in content, "Few-shot missing PLAN"
        assert "ACTION" in content, "Few-shot missing ACTION steps"
        assert "RESULT:" in content, "Few-shot missing RESULT"

    def test_has_problem_solving_approach(self):
        """Agent must have Problem-Solving Approach section."""
        content = get_agent_content()
        assert "## Problem-Solving Approach" in content, "Missing Problem-Solving Approach"

    def test_has_integration_points(self):
        """Agent must have Integration Points section."""
        content = get_agent_content()
        assert "## Integration Points" in content, "Missing Integration Points"
        assert "HANDOFF DECLARATION" in content, "Missing Handoff Declaration pattern"

    def test_has_domain_reference(self):
        """Agent must have Domain Reference section."""
        content = get_agent_content()
        assert "## Domain Reference" in content, "Missing Domain Reference section"

    def test_has_model_selection(self):
        """Agent must have Model Selection guidance."""
        content = get_agent_content()
        assert "## Model Selection" in content or "**Sonnet**:" in content, "Missing Model Selection"

    def test_has_production_status(self):
        """Agent must have Production Status indicator."""
        content = get_agent_content()
        assert "## Production Status" in content or "Production Status" in content, "Missing Production Status"


class TestM365IRAgentSpecificContent:
    """Test M365 IR Agent has required domain-specific content."""

    def test_covers_unified_audit_log(self):
        """Agent must cover Unified Audit Log analysis."""
        content = get_agent_content()
        assert "Unified Audit Log" in content or "UAL" in content, "Missing UAL coverage"

    def test_covers_azure_ad_signin_logs(self):
        """Agent must cover Azure AD Sign-in log analysis."""
        content = get_agent_content()
        assert "Sign-in" in content or "signin" in content.lower(), "Missing Sign-in log coverage"

    def test_covers_mailbox_audit(self):
        """Agent must cover Mailbox Audit log analysis."""
        content = get_agent_content()
        assert "Mailbox Audit" in content or "MailboxAudit" in content, "Missing Mailbox Audit coverage"

    def test_covers_mitre_attack(self):
        """Agent must map to MITRE ATT&CK framework."""
        content = get_agent_content()
        assert "MITRE" in content, "Missing MITRE ATT&CK mapping"
        assert "T1" in content, "Missing MITRE technique IDs (T1xxx)"

    def test_covers_key_iocs(self):
        """Agent must cover key M365 IOC types."""
        content = get_agent_content()
        ioc_types = ["InboxRule", "MailItemsAccessed", "OAuth", "forwarding"]
        found = sum(1 for ioc in ioc_types if ioc.lower() in content.lower())
        assert found >= 3, f"Missing key IOC coverage (found {found}/4)"

    def test_covers_remediation(self):
        """Agent must provide remediation guidance."""
        content = get_agent_content()
        assert "Remediation" in content or "remediation" in content, "Missing remediation section"
        # Check for specific remediation actions
        remediation_keywords = ["revoke", "reset", "block", "remove"]
        found = sum(1 for kw in remediation_keywords if kw.lower() in content.lower())
        assert found >= 2, f"Missing specific remediation actions (found {found}/4)"

    def test_covers_evidence_preservation(self):
        """Agent must cover evidence preservation."""
        content = get_agent_content()
        assert "evidence" in content.lower() or "preservation" in content.lower(), "Missing evidence preservation"

    def test_covers_bec_scenario(self):
        """Agent should cover Business Email Compromise scenario."""
        content = get_agent_content()
        assert "BEC" in content or "Business Email Compromise" in content, "Missing BEC scenario"


class TestAgentQuality:
    """Test agent quality and completeness."""

    def test_minimum_content_length(self):
        """Agent should have substantial content (>5000 chars)."""
        content = get_agent_content()
        assert len(content) > 5000, f"Agent content too short ({len(content)} chars)"

    def test_has_multiple_examples(self):
        """Agent should have at least 2 few-shot examples."""
        content = get_agent_content()
        example_count = content.count("## Few-Shot Example")
        assert example_count >= 2, f"Only {example_count} examples (need 2+)"

    def test_no_placeholder_content(self):
        """Agent should not have placeholder/TODO content."""
        content = get_agent_content()
        placeholders = ["TODO", "FIXME", "XXX", "[placeholder]", "[TBD]"]
        for placeholder in placeholders:
            assert placeholder not in content, f"Found placeholder: {placeholder}"

    def test_version_number(self):
        """Agent should have version number in title."""
        content = get_agent_content()
        assert re.search(r"v\d+\.\d+", content), "Missing version number (e.g., v2.3)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
