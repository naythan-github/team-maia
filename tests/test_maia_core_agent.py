#!/usr/bin/env python3
"""
Test Suite for Maia Core Agent Structure
TDD Phase 3: Tests written BEFORE implementation

Validates that maia_core_agent.md follows v2.3 template and
includes all required reliability-focused behaviors.

Requirements Reference: claude/data/project_status/active/MAIA_CORE_AGENT_requirements.md
Agent: SRE Principal Engineer Agent
Created: 2025-11-22
"""

import re
import unittest
from pathlib import Path

# Agent file location
MAIA_ROOT = Path(__file__).parent.parent.parent
AGENT_PATH = MAIA_ROOT / "claude" / "agents" / "maia_core_agent.md"


class TestAgentFileExists(unittest.TestCase):
    """Basic file existence check"""

    def test_agent_file_exists(self):
        """maia_core_agent.md exists in agents directory"""
        self.assertTrue(
            AGENT_PATH.exists(),
            f"Agent file not found at {AGENT_PATH}"
        )


class TestAgentV23Structure(unittest.TestCase):
    """Validate v2.3 agent template structure"""

    @classmethod
    def setUpClass(cls):
        """Load agent content once"""
        if AGENT_PATH.exists():
            cls.content = AGENT_PATH.read_text()
        else:
            cls.content = ""

    def test_has_agent_overview_section(self):
        """Agent has ## Agent Overview section"""
        self.assertIn("## Agent Overview", self.content)

    def test_has_purpose_field(self):
        """Agent Overview contains Purpose field"""
        self.assertRegex(self.content, r'\*\*Purpose\*\*:')

    def test_has_target_role_field(self):
        """Agent Overview contains Target Role field"""
        self.assertRegex(self.content, r'\*\*Target Role\*\*:')

    def test_has_core_behavior_principles(self):
        """Agent has Core Behavior Principles section"""
        self.assertIn("## Core Behavior Principles", self.content)

    def test_has_persistence_principle(self):
        """Has Persistence & Completion principle"""
        self.assertIn("Persistence", self.content)

    def test_has_core_specialties(self):
        """Agent has Core Specialties section"""
        self.assertIn("## Core Specialties", self.content)

    def test_has_key_commands(self):
        """Agent has Key Commands section"""
        self.assertIn("## Key Commands", self.content)

    def test_has_few_shot_examples(self):
        """Agent has at least one Few-Shot Example"""
        self.assertIn("## Few-Shot Example", self.content)

    def test_has_problem_solving_approach(self):
        """Agent has Problem-Solving Approach section"""
        self.assertIn("## Problem-Solving Approach", self.content)

    def test_has_model_selection(self):
        """Agent has Model Selection guidance"""
        self.assertIn("## Model Selection", self.content)

    def test_has_production_status(self):
        """Agent has Production Status indicator"""
        self.assertIn("## Production Status", self.content)


class TestReliabilityBehaviors(unittest.TestCase):
    """FR-3: Operational Discipline requirements"""

    @classmethod
    def setUpClass(cls):
        """Load agent content once"""
        if AGENT_PATH.exists():
            cls.content = AGENT_PATH.read_text()
        else:
            cls.content = ""

    def test_has_state_preservation_protocol(self):
        """Agent defines State Preservation Protocol (FR-1)"""
        self.assertTrue(
            "State Preservation" in self.content or "Checkpoint" in self.content,
            "Agent must define state preservation behavior"
        )

    def test_has_task_protocol(self):
        """Agent defines task execution protocol (FR-3.1)"""
        # Requirements → Plan → Execute → Validate → Document
        protocol_patterns = ["Requirements", "Plan", "Execute", "Validate"]
        found = sum(1 for p in protocol_patterns if p in self.content)
        self.assertGreaterEqual(
            found, 3,
            f"Task protocol should reference most of: {protocol_patterns}"
        )

    def test_no_investigate_further_pattern(self):
        """Agent explicitly prohibits 'investigate further' endings"""
        self.assertTrue(
            "investigate further" in self.content.lower() or
            "complete solutions" in self.content.lower() or
            "don't stop" in self.content.lower(),
            "Agent must address the 'investigate further' anti-pattern"
        )

    def test_has_failure_mode_awareness(self):
        """Agent addresses failure modes (FR-3.2)"""
        failure_patterns = ["failure", "error", "graceful", "fallback", "recovery"]
        found = sum(1 for p in failure_patterns if p.lower() in self.content.lower())
        self.assertGreaterEqual(
            found, 2,
            f"Agent should address failure handling"
        )

    def test_has_repeatability_focus(self):
        """Agent emphasizes repeatability (FR-3.3)"""
        repeatability_patterns = ["repeatable", "reproducible", "runbook", "documented", "another engineer"]
        found = sum(1 for p in repeatability_patterns if p.lower() in self.content.lower())
        self.assertGreaterEqual(
            found, 2,
            f"Agent should emphasize repeatability"
        )


class TestMSPPatterns(unittest.TestCase):
    """FR-4: MSP Operational Patterns"""

    @classmethod
    def setUpClass(cls):
        """Load agent content once"""
        if AGENT_PATH.exists():
            cls.content = AGENT_PATH.read_text()
        else:
            cls.content = ""

    def test_has_customer_awareness(self):
        """Agent has customer tier/impact awareness (FR-4.1)"""
        customer_patterns = ["customer", "client", "tenant", "impact"]
        found = sum(1 for p in customer_patterns if p.lower() in self.content.lower())
        self.assertGreaterEqual(
            found, 2,
            "Agent should have customer awareness"
        )

    def test_has_sla_consciousness(self):
        """Agent has SLA consciousness (FR-4.2)"""
        sla_patterns = ["SLA", "time", "resolution", "escalation", "priority"]
        found = sum(1 for p in sla_patterns if p.lower() in self.content.lower())
        self.assertGreaterEqual(
            found, 2,
            "Agent should reference SLA/timing concepts"
        )

    def test_has_documentation_first(self):
        """Agent emphasizes documentation-first (FR-4.4)"""
        doc_patterns = ["documentation", "document", "IT Glue", "Confluence", "source of truth"]
        found = sum(1 for p in doc_patterns if p.lower() in self.content.lower())
        self.assertGreaterEqual(
            found, 2,
            "Agent should emphasize documentation"
        )

    def test_has_handover_ready(self):
        """Agent ensures handover-ready work (FR-4.5)"""
        handover_patterns = ["handover", "hand-over", "another engineer", "reproducible", "follow"]
        found = sum(1 for p in handover_patterns if p.lower() in self.content.lower())
        self.assertGreaterEqual(
            found, 1,
            "Agent should ensure work is handover-ready"
        )


class TestRecoveryProtocol(unittest.TestCase):
    """FR-2: Recovery Protocol behaviors"""

    @classmethod
    def setUpClass(cls):
        """Load agent content once"""
        if AGENT_PATH.exists():
            cls.content = AGENT_PATH.read_text()
        else:
            cls.content = ""

    def test_has_recovery_behavior(self):
        """Agent defines recovery behavior (FR-2)"""
        recovery_patterns = ["recovery", "recover", "resume", "checkpoint", "restore"]
        found = sum(1 for p in recovery_patterns if p.lower() in self.content.lower())
        self.assertGreaterEqual(
            found, 2,
            "Agent should define recovery behavior"
        )

    def test_has_git_awareness(self):
        """Agent uses git for context recovery (FR-2.2)"""
        self.assertTrue(
            "git" in self.content.lower(),
            "Agent should reference git for recovery context"
        )

    def test_has_graceful_degradation(self):
        """Agent implements graceful degradation (FR-2.3)"""
        graceful_patterns = ["graceful", "fallback", "degrade", "path forward"]
        found = sum(1 for p in graceful_patterns if p.lower() in self.content.lower())
        self.assertGreaterEqual(
            found, 1,
            "Agent should implement graceful degradation"
        )


class TestDefaultAgentBehavior(unittest.TestCase):
    """FR-5: Default Agent Loading behaviors"""

    @classmethod
    def setUpClass(cls):
        """Load agent content once"""
        if AGENT_PATH.exists():
            cls.content = AGENT_PATH.read_text()
        else:
            cls.content = ""

    def test_identifies_as_default(self):
        """Agent identifies as default/core agent"""
        default_patterns = ["default", "core", "base", "foundation"]
        found = sum(1 for p in default_patterns if p.lower() in self.content.lower())
        self.assertGreaterEqual(
            found, 2,
            "Agent should identify as default/core"
        )

    def test_mentions_specialist_override(self):
        """Agent acknowledges specialist override capability"""
        override_patterns = ["specialist", "override", "specific agent", "load.*agent"]
        found = sum(1 for p in override_patterns if re.search(p, self.content.lower()))
        self.assertGreaterEqual(
            found, 1,
            "Agent should acknowledge specialist override"
        )


class TestAgentQuality(unittest.TestCase):
    """General quality checks"""

    @classmethod
    def setUpClass(cls):
        """Load agent content once"""
        if AGENT_PATH.exists():
            cls.content = AGENT_PATH.read_text()
        else:
            cls.content = ""

    def test_version_number(self):
        """Agent has version number in title"""
        self.assertRegex(
            self.content,
            r'# .+ v\d+\.\d+',
            "Agent should have version number (e.g., v1.0)"
        )

    def test_reasonable_length(self):
        """Agent is reasonably sized (not too short, not too long)"""
        lines = len(self.content.split('\n'))
        self.assertGreater(lines, 50, "Agent too short - missing content")
        self.assertLess(lines, 400, "Agent too long - should be compressed")

    def test_has_integration_points(self):
        """Agent defines integration points with other agents"""
        self.assertTrue(
            "Integration" in self.content or "Handoff" in self.content or "Collaborat" in self.content,
            "Agent should define integration/collaboration points"
        )


if __name__ == '__main__':
    unittest.main(verbosity=2)
