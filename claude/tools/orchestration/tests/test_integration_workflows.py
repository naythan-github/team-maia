"""Integration tests for multi-agent handoff workflows."""

import pytest
import json
import tempfile
from pathlib import Path
from claude.tools.orchestration.swarm_integration import IntegratedSwarmOrchestrator
from claude.tools.orchestration.handoff_executor import MaxHandoffsExceeded


class TestMultiAgentWorkflows:
    """Integration tests for multi-agent handoff workflows."""

    def test_sre_to_security_to_devops_chain(self):
        """Test SRE → Security → DevOps handoff chain."""
        orchestrator = IntegratedSwarmOrchestrator()

        # Mock 3-agent chain
        orchestrator.set_mock_responses([
            {"content": [
                {"type": "text", "text": "Identified security concern in deployment"},
                {"type": "tool_use", "name": "transfer_to_security_specialist", "input": {"context": {"issue": "SQL injection risk"}}}
            ]},
            {"content": [
                {"type": "text", "text": "Security review complete, CI/CD needs hardening"},
                {"type": "tool_use", "name": "transfer_to_devops_principal", "input": {"context": {"fix": "Add SAST scanning"}}}
            ]},
            {"content": [{"type": "text", "text": "CI/CD pipeline hardened with security scanning"}]}
        ])

        result = orchestrator.execute_with_handoffs(
            initial_agent="sre_principal_engineer",
            task={"query": "Review deployment security"},
            max_handoffs=5
        )

        assert len(result.handoff_chain) == 2
        assert result.handoff_chain[0]["to"] == "security_specialist"
        assert result.handoff_chain[1]["to"] == "devops_principal"

    def test_circular_handoff_prevention(self):
        """Prevent circular handoffs A → B → A."""
        orchestrator = IntegratedSwarmOrchestrator()

        # Mock circular pattern
        orchestrator.set_mock_responses([
            {"content": [{"type": "tool_use", "name": "transfer_to_agent_b", "input": {}}]},
            {"content": [{"type": "tool_use", "name": "transfer_to_agent_a", "input": {}}]},  # Back to A
            {"content": [{"type": "tool_use", "name": "transfer_to_agent_b", "input": {}}]},  # Loop
        ])

        result = orchestrator.execute_with_handoffs(
            initial_agent="agent_a",
            task={"query": "Test"},
            max_handoffs=2
        )

        # Should stop at max_handoffs, not infinite loop
        assert result.max_handoffs_reached or len(result.handoff_chain) <= 2

    def test_max_handoffs_enforcement(self):
        """Enforce max handoffs limit."""
        orchestrator = IntegratedSwarmOrchestrator()

        # Mock many handoffs
        orchestrator.set_mock_responses([
            {"content": [{"type": "tool_use", "name": "transfer_to_b", "input": {}}]},
            {"content": [{"type": "tool_use", "name": "transfer_to_c", "input": {}}]},
            {"content": [{"type": "tool_use", "name": "transfer_to_d", "input": {}}]},
            {"content": [{"type": "tool_use", "name": "transfer_to_e", "input": {}}]},
            {"content": [{"type": "tool_use", "name": "transfer_to_f", "input": {}}]},
        ])

        result = orchestrator.execute_with_handoffs(
            initial_agent="a",
            task={"query": "Test"},
            max_handoffs=3
        )

        assert len(result.handoff_chain) <= 3
        assert result.max_handoffs_reached

    def test_handoff_with_no_target_agent(self):
        """Handle handoff to nonexistent agent gracefully."""
        orchestrator = IntegratedSwarmOrchestrator()

        orchestrator.set_mock_responses([
            {"content": [{"type": "tool_use", "name": "transfer_to_nonexistent_agent", "input": {}}]},
        ])

        result = orchestrator.execute_with_handoffs(
            initial_agent="sre",
            task={"query": "Test"},
            max_handoffs=3
        )

        # Should handle gracefully - either recover or complete
        assert result.final_output is not None or result.error is not None
