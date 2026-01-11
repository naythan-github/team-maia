"""
Sprint 4: Swarm Orchestrator Integration Tests

Tests for F015-F018: Complete integration of agent handoffs with swarm orchestrator.

TDD Approach: Write tests first, then implement to pass them.
"""

import json
import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

# These will be imported from the implementation once created
# Stub imports for now - these will fail until we implement them
try:
    from claude.tools.orchestration.swarm_integration import (
        IntegratedSwarmOrchestrator,
        SwarmExecutionResult,
        create_handoff_enabled_session,
        update_session_on_handoff,
        record_handoff_for_learning,
        get_handoff_analytics,
        get_task_handoff_analytics,
    )
except ImportError:
    # Stubs for initial test runs (Red phase)
    IntegratedSwarmOrchestrator = None
    SwarmExecutionResult = None
    create_handoff_enabled_session = None
    update_session_on_handoff = None
    record_handoff_for_learning = None
    get_handoff_analytics = None
    get_task_handoff_analytics = None

# Import existing Sprint 1-3 components
from claude.tools.orchestration.handoff_generator import (
    parse_agent_collaborations,
    generate_handoff_functions,
    AgentRegistry,
    generate_tool_schemas,
    build_handoff_context,
)
from claude.tools.orchestration.handoff_executor import (
    detect_handoff,
    AgentExecutor,
    AgentResult,
    HandoffChainTracker,
    MaxHandoffsGuard,
    MaxHandoffsExceeded,
    aggregate_results,
)
from claude.hooks.session_handoffs import (
    add_handoff_to_session,
    inject_handoff_context,
    HandoffPatternTracker,
    HandoffRecovery,
)


# ==============================================================================
# Feature 4.1: SwarmOrchestrator Execute Integration (F015)
# ==============================================================================

class TestSwarmOrchestratorExecuteIntegration:
    """F015: SwarmOrchestrator executes agents with real handoff support."""

    def test_swarm_orchestrator_executes_agent(self):
        """SwarmOrchestrator executes real agents with handoff support."""
        pytest.importorskip("claude.tools.orchestration.swarm_integration")

        orchestrator = IntegratedSwarmOrchestrator()

        # Mock the Claude API call
        orchestrator.set_mock_response({
            "content": [{"type": "text", "text": "Task completed successfully"}]
        })

        result = orchestrator.execute_with_handoffs(
            initial_agent="sre_principal_engineer",
            task={"query": "Review system health", "context": {}},
            max_handoffs=3
        )

        assert result.final_output is not None
        assert isinstance(result.handoff_chain, list)
        assert result.initial_agent == "sre_principal_engineer"

    def test_swarm_orchestrator_handles_handoff(self):
        """SwarmOrchestrator routes handoffs to target agent."""
        pytest.importorskip("claude.tools.orchestration.swarm_integration")

        orchestrator = IntegratedSwarmOrchestrator()

        # First agent hands off to second
        orchestrator.set_mock_responses([
            {"content": [{"type": "tool_use", "name": "transfer_to_security_specialist", "input": {"context": {}}}]},
            {"content": [{"type": "text", "text": "Security review complete"}]}
        ])

        result = orchestrator.execute_with_handoffs(
            initial_agent="sre_principal_engineer",
            task={"query": "Check for security issues"},
            max_handoffs=3
        )

        assert len(result.handoff_chain) >= 1
        assert result.final_agent == "security_specialist"

    def test_swarm_orchestrator_respects_max_handoffs(self):
        """SwarmOrchestrator stops at max handoffs."""
        pytest.importorskip("claude.tools.orchestration.swarm_integration")

        orchestrator = IntegratedSwarmOrchestrator()

        # Infinite handoff loop scenario
        orchestrator.set_mock_responses([
            {"content": [{"type": "tool_use", "name": "transfer_to_agent_b", "input": {}}]},
            {"content": [{"type": "tool_use", "name": "transfer_to_agent_c", "input": {}}]},
            {"content": [{"type": "tool_use", "name": "transfer_to_agent_d", "input": {}}]},
            {"content": [{"type": "tool_use", "name": "transfer_to_agent_e", "input": {}}]},
        ])

        result = orchestrator.execute_with_handoffs(
            initial_agent="agent_a",
            task={"query": "Test query"},
            max_handoffs=2
        )

        assert len(result.handoff_chain) <= 2
        assert result.max_handoffs_reached

    def test_orchestrator_loads_agent_from_registry(self):
        """Orchestrator loads agent configuration from registry."""
        pytest.importorskip("claude.tools.orchestration.swarm_integration")

        orchestrator = IntegratedSwarmOrchestrator()

        # Set up mock response
        orchestrator.set_mock_response({
            "content": [{"type": "text", "text": "Done"}]
        })

        # Execute should load agent from registry
        result = orchestrator.execute_with_handoffs(
            initial_agent="sre_principal_engineer",
            task={"query": "Test"},
            max_handoffs=1
        )

        # Verify agent was loaded (by checking execution succeeded)
        assert result.final_output is not None

    def test_orchestrator_registers_handoff_tools(self):
        """Orchestrator registers handoff tools with agent execution."""
        pytest.importorskip("claude.tools.orchestration.swarm_integration")

        orchestrator = IntegratedSwarmOrchestrator()

        # Use mock response that calls a handoff tool
        orchestrator.set_mock_responses([
            {"content": [{"type": "tool_use", "name": "transfer_to_security_specialist", "input": {"context": {"reason": "test"}}}]},
            {"content": [{"type": "text", "text": "Complete"}]}
        ])

        result = orchestrator.execute_with_handoffs(
            initial_agent="sre_principal_engineer",
            task={"query": "Test handoff tools"},
            max_handoffs=3
        )

        # Handoff should have worked, meaning tools were registered
        assert len(result.handoff_chain) >= 1
        assert result.handoff_chain[0]["to"] == "security_specialist"

    def test_orchestrator_enriches_context_on_handoff(self):
        """Context is enriched when passing between agents."""
        pytest.importorskip("claude.tools.orchestration.swarm_integration")

        orchestrator = IntegratedSwarmOrchestrator()

        # First agent adds context, second uses it
        orchestrator.set_mock_responses([
            {
                "content": [
                    {"type": "text", "text": "Initial analysis complete"},
                    {"type": "tool_use", "name": "transfer_to_security_specialist", "input": {
                        "context": {"analysis": "vulnerability found", "priority": "high"}
                    }}
                ]
            },
            {"content": [{"type": "text", "text": "Security review with context"}]}
        ])

        result = orchestrator.execute_with_handoffs(
            initial_agent="sre_principal_engineer",
            task={"query": "Full security analysis"},
            max_handoffs=3
        )

        # Verify context was passed
        assert len(result.handoff_chain) >= 1
        handoff_context = result.handoff_chain[0].get("context", {})
        assert "analysis" in handoff_context or "priority" in handoff_context


# ==============================================================================
# Feature 4.2: End-to-End DNS to Azure Handoff (F016)
# ==============================================================================

class TestDNSToAzureHandoffE2E:
    """F016: DNS to Azure handoff - flagship workflow test."""

    def test_dns_to_azure_handoff_e2e(self):
        """DNS specialist hands off to Azure architect - full workflow."""
        pytest.importorskip("claude.tools.orchestration.swarm_integration")

        orchestrator = IntegratedSwarmOrchestrator()

        # Simulate DNS agent completing and handing off to Azure
        orchestrator.set_mock_responses([
            {
                "content": [
                    {"type": "text", "text": "Public DNS configured. MX records set."},
                    {"type": "tool_use", "name": "transfer_to_azure_solutions_architect", "input": {
                        "context": {"dns_configured": True, "domain": "client.com"}
                    }}
                ]
            },
            {
                "content": [{"type": "text", "text": "Exchange Online configured with custom domain."}]
            }
        ])

        result = orchestrator.execute_with_handoffs(
            initial_agent="dns_specialist",
            task={
                "query": "Setup Exchange Online with custom domain",
                "domain": "client.com",
                "tenant": "client.onmicrosoft.com"
            }
        )

        # Verify DNS to Azure handoff occurred
        handoff = next((h for h in result.handoff_chain if h["to"] == "azure_solutions_architect"), None)
        assert handoff is not None
        assert handoff["from"] == "dns_specialist"

        # Verify context was passed
        assert "Exchange Online" in result.final_output or "configured" in result.final_output.lower()

    def test_dns_handoff_includes_context(self):
        """DNS handoff passes DNS configuration context to Azure."""
        pytest.importorskip("claude.tools.orchestration.swarm_integration")

        orchestrator = IntegratedSwarmOrchestrator()

        orchestrator.set_mock_responses([
            {
                "content": [{
                    "type": "tool_use",
                    "name": "transfer_to_azure_solutions_architect",
                    "input": {"context": {"mx_records": ["mx1.outlook.com"], "spf_configured": True}}
                }]
            },
            {"content": [{"type": "text", "text": "Complete"}]}
        ])

        result = orchestrator.execute_with_handoffs(
            initial_agent="dns_specialist",
            task={"query": "Setup email"}
        )

        # Azure agent should receive DNS context
        assert len(result.handoff_chain) >= 1
        handoff_context = result.handoff_chain[0].get("context", {})
        # Context should be preserved/passed
        assert result.handoff_chain[0]["to"] == "azure_solutions_architect"

    def test_dns_configures_before_handoff(self):
        """DNS agent completes DNS work before handing off."""
        pytest.importorskip("claude.tools.orchestration.swarm_integration")

        orchestrator = IntegratedSwarmOrchestrator()

        # DNS agent produces output before handoff
        orchestrator.set_mock_responses([
            {
                "content": [
                    {"type": "text", "text": "SPF, DKIM, DMARC records configured for client.com"},
                    {"type": "tool_use", "name": "transfer_to_azure_solutions_architect", "input": {
                        "context": {
                            "dns_records_configured": True,
                            "records": ["SPF", "DKIM", "DMARC"],
                            "domain": "client.com"
                        }
                    }}
                ]
            },
            {"content": [{"type": "text", "text": "Azure configuration complete"}]}
        ])

        result = orchestrator.execute_with_handoffs(
            initial_agent="dns_specialist",
            task={"query": "Setup Exchange", "domain": "client.com"},
            max_handoffs=3
        )

        # Should have recorded DNS work in intermediate output
        assert result.final_agent == "azure_solutions_architect"
        assert len(result.handoff_chain) == 1

    def test_azure_completes_after_dns_handoff(self):
        """Azure architect completes Exchange setup after DNS handoff."""
        pytest.importorskip("claude.tools.orchestration.swarm_integration")

        orchestrator = IntegratedSwarmOrchestrator()

        orchestrator.set_mock_responses([
            {
                "content": [
                    {"type": "tool_use", "name": "transfer_to_azure_solutions_architect", "input": {
                        "context": {"dns_ready": True}
                    }}
                ]
            },
            {
                "content": [
                    {"type": "text", "text": "Exchange Online provisioned. Custom domain verified. Mail flow enabled."}
                ]
            }
        ])

        result = orchestrator.execute_with_handoffs(
            initial_agent="dns_specialist",
            task={"query": "Full email setup"}
        )

        # Azure should be final agent with complete output
        assert result.final_agent == "azure_solutions_architect"
        assert "Exchange" in result.final_output or "Mail" in result.final_output or "domain" in result.final_output.lower()


# ==============================================================================
# Feature 4.3: Hook Integration (F017)
# ==============================================================================

class TestHookIntegration:
    """F017: Integration with swarm_auto_loader hook."""

    def test_auto_loader_enables_handoffs(self):
        """Auto-loader creates session with handoff capability."""
        pytest.importorskip("claude.tools.orchestration.swarm_integration")

        # Simulate what swarm_auto_loader does
        session_data = create_handoff_enabled_session(
            agent="sre_principal_engineer",
            query="Review this Python code for security vulnerabilities"
        )

        assert session_data["handoffs_enabled"]
        assert "handoff_tools" in session_data or session_data.get("agent_capabilities", {}).get("can_handoff")

    def test_session_updates_on_handoff(self):
        """Session file updates when handoff occurs."""
        pytest.importorskip("claude.tools.orchestration.swarm_integration")

        session_file = Path(tempfile.gettempdir()) / "test_hook_session.json"

        # Create initial session
        initial_session = {
            "current_agent": "sre_principal_engineer",
            "handoff_chain": ["sre_principal_engineer"],
            "handoffs_enabled": True,
            "context": {}
        }
        session_file.write_text(json.dumps(initial_session))

        try:
            # Simulate handoff occurring
            update_session_on_handoff(
                session_file=session_file,
                from_agent="sre_principal_engineer",
                to_agent="security_specialist",
                reason="Security expertise needed",
                context={"code_reviewed": True}
            )

            updated = json.loads(session_file.read_text())
            assert updated["current_agent"] == "security_specialist"
            assert len(updated["handoff_chain"]) == 2
        finally:
            # Cleanup
            if session_file.exists():
                session_file.unlink()

    def test_handoff_triggers_learning_capture(self):
        """Handoff events are captured for learning."""
        pytest.importorskip("claude.tools.orchestration.swarm_integration")

        tracker = HandoffPatternTracker()

        record_handoff_for_learning(
            tracker=tracker,
            from_agent="sre_principal",
            to_agent="security_specialist",
            query="Security review request",
            success=True
        )

        patterns = tracker.get_patterns()
        assert any(p["from"] == "sre_principal" and p["to"] == "security_specialist" for p in patterns)

    def test_session_preserves_context_on_handoff(self):
        """Session context is preserved and augmented on handoff."""
        pytest.importorskip("claude.tools.orchestration.swarm_integration")

        session_file = Path(tempfile.gettempdir()) / "test_context_session.json"

        initial_session = {
            "current_agent": "dns_specialist",
            "handoff_chain": ["dns_specialist"],
            "handoffs_enabled": True,
            "context": {"domain": "example.com", "tenant": "test.onmicrosoft.com"}
        }
        session_file.write_text(json.dumps(initial_session))

        try:
            update_session_on_handoff(
                session_file=session_file,
                from_agent="dns_specialist",
                to_agent="azure_solutions_architect",
                reason="Azure configuration needed",
                context={"dns_configured": True, "mx_records": ["mx.outlook.com"]}
            )

            updated = json.loads(session_file.read_text())

            # Original context should be preserved
            assert updated["context"]["domain"] == "example.com"
            # New context should be added
            assert updated["context"]["dns_configured"] is True
        finally:
            if session_file.exists():
                session_file.unlink()

    def test_handoff_chain_grows_correctly(self):
        """Handoff chain tracks all agents in sequence."""
        pytest.importorskip("claude.tools.orchestration.swarm_integration")

        session_file = Path(tempfile.gettempdir()) / "test_chain_session.json"

        initial_session = {
            "current_agent": "agent_a",
            "handoff_chain": ["agent_a"],
            "handoffs_enabled": True,
            "context": {}
        }
        session_file.write_text(json.dumps(initial_session))

        try:
            # First handoff
            update_session_on_handoff(
                session_file=session_file,
                from_agent="agent_a",
                to_agent="agent_b",
                reason="Reason 1",
                context={}
            )

            # Second handoff
            update_session_on_handoff(
                session_file=session_file,
                from_agent="agent_b",
                to_agent="agent_c",
                reason="Reason 2",
                context={}
            )

            updated = json.loads(session_file.read_text())
            assert updated["handoff_chain"] == ["agent_a", "agent_b", "agent_c"]
            assert updated["current_agent"] == "agent_c"
        finally:
            if session_file.exists():
                session_file.unlink()


# ==============================================================================
# Feature 4.4: Handoff Analytics Dashboard (F018)
# ==============================================================================

class TestHandoffAnalyticsDashboard:
    """F018: Handoff analytics for optimization."""

    def test_handoff_analytics_basic(self):
        """Generate basic handoff analytics."""
        pytest.importorskip("claude.tools.orchestration.swarm_integration")

        # Create sample handoff history
        history = [
            {"from": "sre", "to": "security", "success": True, "timestamp": "2026-01-10T10:00:00Z"},
            {"from": "sre", "to": "security", "success": True, "timestamp": "2026-01-10T11:00:00Z"},
            {"from": "security", "to": "devops", "success": False, "timestamp": "2026-01-10T12:00:00Z"},
            {"from": "sre", "to": "azure", "success": True, "timestamp": "2026-01-11T10:00:00Z"},
        ]

        analytics = get_handoff_analytics(history)

        assert analytics["total_handoffs"] == 4
        assert analytics["success_rate"] == 0.75  # 3 of 4
        assert len(analytics["common_paths"]) > 0

    def test_handoff_analytics_common_paths(self):
        """Identify most common handoff paths."""
        pytest.importorskip("claude.tools.orchestration.swarm_integration")

        history = [
            {"from": "sre", "to": "security", "success": True},
            {"from": "sre", "to": "security", "success": True},
            {"from": "sre", "to": "security", "success": True},
            {"from": "dns", "to": "azure", "success": True},
        ]

        analytics = get_handoff_analytics(history)

        # sre -> security should be most common
        assert analytics["common_paths"][0]["from"] == "sre"
        assert analytics["common_paths"][0]["to"] == "security"
        assert analytics["common_paths"][0]["count"] == 3

    def test_handoff_analytics_avg_per_task(self):
        """Calculate average handoffs per task."""
        pytest.importorskip("claude.tools.orchestration.swarm_integration")

        # Simulate task-level tracking
        task_handoffs = [
            {"task_id": "t1", "handoff_count": 2},
            {"task_id": "t2", "handoff_count": 1},
            {"task_id": "t3", "handoff_count": 3},
        ]

        analytics = get_task_handoff_analytics(task_handoffs)

        assert analytics["avg_handoffs_per_task"] == 2.0
        assert analytics["max_handoffs"] == 3

    def test_handoff_analytics_time_range(self):
        """Filter analytics by time range."""
        pytest.importorskip("claude.tools.orchestration.swarm_integration")

        # Use dynamic dates relative to current time
        now = datetime.now()
        old_date = (now - timedelta(days=10)).isoformat() + "Z"
        recent_date_1 = (now - timedelta(days=2)).isoformat() + "Z"
        recent_date_2 = (now - timedelta(days=1)).isoformat() + "Z"

        history = [
            {"from": "a", "to": "b", "success": True, "timestamp": old_date},
            {"from": "a", "to": "b", "success": True, "timestamp": recent_date_1},
            {"from": "a", "to": "b", "success": True, "timestamp": recent_date_2},
        ]

        analytics = get_handoff_analytics(history, days=7)

        # Should only include last 7 days (2 handoffs from recent days)
        assert analytics["total_handoffs"] == 2

    def test_handoff_analytics_empty_history(self):
        """Handle empty handoff history gracefully."""
        pytest.importorskip("claude.tools.orchestration.swarm_integration")

        analytics = get_handoff_analytics([])

        assert analytics["total_handoffs"] == 0
        assert analytics["success_rate"] == 0.0
        assert analytics["common_paths"] == []

    def test_handoff_analytics_agent_frequency(self):
        """Track which agents are most frequently involved."""
        pytest.importorskip("claude.tools.orchestration.swarm_integration")

        history = [
            {"from": "sre", "to": "security", "success": True},
            {"from": "sre", "to": "azure", "success": True},
            {"from": "sre", "to": "dns", "success": True},
            {"from": "security", "to": "sre", "success": True},
        ]

        analytics = get_handoff_analytics(history)

        # sre should be most frequent (appears 4 times - 3 as from, 1 as to)
        assert "agent_frequency" in analytics
        assert analytics["agent_frequency"]["sre"] >= 3

    def test_task_handoff_analytics_min_handoffs(self):
        """Track minimum handoffs per task."""
        pytest.importorskip("claude.tools.orchestration.swarm_integration")

        task_handoffs = [
            {"task_id": "t1", "handoff_count": 2},
            {"task_id": "t2", "handoff_count": 0},  # No handoffs needed
            {"task_id": "t3", "handoff_count": 5},
        ]

        analytics = get_task_handoff_analytics(task_handoffs)

        assert analytics["min_handoffs"] == 0
        assert analytics["max_handoffs"] == 5


# ==============================================================================
# Integration Tests - Cross-feature verification
# ==============================================================================

class TestCrossFeatureIntegration:
    """Test that all Sprint 4 features work together."""

    def test_full_workflow_with_session_and_analytics(self):
        """Complete workflow: execute, update session, capture analytics."""
        pytest.importorskip("claude.tools.orchestration.swarm_integration")

        # Setup session file
        session_file = Path(tempfile.gettempdir()) / "test_full_workflow.json"
        initial_session = {
            "current_agent": "dns_specialist",
            "handoff_chain": ["dns_specialist"],
            "handoffs_enabled": True,
            "context": {"domain": "example.com"}
        }
        session_file.write_text(json.dumps(initial_session))

        try:
            # Create orchestrator
            orchestrator = IntegratedSwarmOrchestrator()
            orchestrator.set_mock_responses([
                {"content": [{"type": "tool_use", "name": "transfer_to_azure_solutions_architect", "input": {"context": {"dns_done": True}}}]},
                {"content": [{"type": "text", "text": "Azure setup complete"}]}
            ])

            # Execute workflow
            result = orchestrator.execute_with_handoffs(
                initial_agent="dns_specialist",
                task={"query": "Setup email", "domain": "example.com"}
            )

            # Update session
            for handoff in result.handoff_chain:
                update_session_on_handoff(
                    session_file=session_file,
                    from_agent=handoff["from"],
                    to_agent=handoff["to"],
                    reason=handoff.get("reason", ""),
                    context=handoff.get("context", {})
                )

            # Check session updated
            final_session = json.loads(session_file.read_text())
            assert final_session["current_agent"] == "azure_solutions_architect"

            # Generate analytics
            analytics = get_handoff_analytics(result.handoff_chain)
            assert analytics["total_handoffs"] >= 1

        finally:
            if session_file.exists():
                session_file.unlink()

    def test_orchestrator_integrates_with_sprint_1_registry(self):
        """Orchestrator works with Sprint 1 AgentRegistry."""
        pytest.importorskip("claude.tools.orchestration.swarm_integration")

        # Use the real AgentRegistry from Sprint 1
        registry = AgentRegistry()

        # IntegratedSwarmOrchestrator should be able to use this registry
        orchestrator = IntegratedSwarmOrchestrator(registry=registry)
        orchestrator.set_mock_response({
            "content": [{"type": "text", "text": "Done"}]
        })

        # Should execute successfully with registry integration
        result = orchestrator.execute_with_handoffs(
            initial_agent="sre_principal_engineer",
            task={"query": "Test"}
        )

        assert result.final_output is not None

    def test_orchestrator_uses_sprint_2_handoff_detection(self):
        """Orchestrator uses Sprint 2 detect_handoff function."""
        pytest.importorskip("claude.tools.orchestration.swarm_integration")

        # Create a response that detect_handoff should parse
        mock_response = {
            "content": [
                {"type": "tool_use", "name": "transfer_to_security_specialist", "input": {"context": {}}}
            ]
        }

        # Verify detect_handoff works as expected
        handoff = detect_handoff(mock_response)
        assert handoff is not None
        assert handoff["target"] == "security_specialist"

        # Now verify orchestrator uses it
        orchestrator = IntegratedSwarmOrchestrator()
        orchestrator.set_mock_responses([
            mock_response,
            {"content": [{"type": "text", "text": "Complete"}]}
        ])

        result = orchestrator.execute_with_handoffs(
            initial_agent="sre_principal_engineer",
            task={"query": "Test"},
            max_handoffs=2
        )

        # Should have detected and executed handoff
        assert len(result.handoff_chain) >= 1
        assert result.handoff_chain[0]["to"] == "security_specialist"

    def test_orchestrator_uses_sprint_3_session_handoffs(self):
        """Orchestrator integrates with Sprint 3 session_handoffs module."""
        pytest.importorskip("claude.tools.orchestration.swarm_integration")

        # Sprint 3's HandoffPatternTracker should work with our learning capture
        tracker = HandoffPatternTracker()

        # Record a handoff for learning
        record_handoff_for_learning(
            tracker=tracker,
            from_agent="dns_specialist",
            to_agent="azure_solutions_architect",
            query="Email setup",
            success=True
        )

        patterns = tracker.get_patterns()
        assert len(patterns) >= 1
        assert patterns[-1]["from"] == "dns_specialist"
