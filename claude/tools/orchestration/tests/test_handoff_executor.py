"""
Tests for handoff executor - Sprint 2 of automatic agent handoffs.

Tests the handoff execution engine that detects and executes handoffs
when an agent returns a handoff tool call.
"""

import pytest
from datetime import datetime
from claude.tools.orchestration.handoff_executor import (
    detect_handoff,
    AgentExecutor,
    AgentResult,
    HandoffChainTracker,
    MaxHandoffsGuard,
    MaxHandoffsExceeded,
    aggregate_results,
)


# Feature 2.1: Handoff Detection (F006)
def test_detect_handoff_in_response():
    """Detect handoff tool call in Claude response."""
    response = {
        "content": [
            {"type": "tool_use", "name": "transfer_to_security_specialist", "input": {"context": "..."}}
        ]
    }

    handoff = detect_handoff(response)
    assert handoff is not None
    assert handoff["target"] == "security_specialist"


def test_detect_no_handoff():
    """Return None when no handoff in response."""
    response = {
        "content": [
            {"type": "text", "text": "Here is my analysis..."}
        ]
    }
    handoff = detect_handoff(response)
    assert handoff is None


def test_detect_handoff_with_context():
    """Extract context from handoff tool call."""
    response = {
        "content": [
            {"type": "tool_use", "name": "transfer_to_azure_architect", "input": {"context": {"query": "setup DNS"}}}
        ]
    }
    handoff = detect_handoff(response)
    assert handoff["context"]["query"] == "setup DNS"


def test_detect_handoff_with_multiple_tools():
    """Handoff takes priority when multiple tool calls present."""
    response = {
        "content": [
            {"type": "tool_use", "name": "some_other_tool", "input": {}},
            {"type": "tool_use", "name": "transfer_to_security_specialist", "input": {"context": "..."}},
            {"type": "text", "text": "Additional text"}
        ]
    }
    handoff = detect_handoff(response)
    assert handoff is not None
    assert handoff["target"] == "security_specialist"


# Feature 2.2: Agent Executor with Handoff Tools (F007)
def test_execute_agent_returns_result():
    """Agent execution returns AgentResult."""
    executor = AgentExecutor()
    result = executor.execute(
        agent="sre_principal_engineer",
        query="Review this code",
        context={}
    )

    assert isinstance(result, AgentResult)
    assert result.agent == "sre_principal_engineer"
    assert result.output is not None


def test_agent_result_with_handoff():
    """AgentResult can contain handoff."""
    result = AgentResult(
        agent="sre_principal",
        output="Found security issue",
        handoff={"target": "security_specialist", "context": {}}
    )
    assert result.has_handoff
    assert result.handoff["target"] == "security_specialist"


def test_agent_result_without_handoff():
    """AgentResult without handoff is marked complete."""
    result = AgentResult(
        agent="sre_principal",
        output="Task completed",
        handoff=None
    )
    assert not result.has_handoff
    assert result.complete


def test_agent_result_stores_metadata():
    """AgentResult stores agent name, output, and handoff."""
    result = AgentResult(
        agent="test_agent",
        output="Test output",
        handoff={"target": "next_agent", "context": {"key": "value"}}
    )
    assert result.agent == "test_agent"
    assert result.output == "Test output"
    assert result.handoff["context"]["key"] == "value"


# Feature 2.3: Handoff Chain Tracker (F008)
def test_handoff_chain_tracking():
    """Track chain of handoffs through execution."""
    tracker = HandoffChainTracker()

    tracker.add_handoff("sre_principal", "security_specialist", "Security review needed")
    tracker.add_handoff("security_specialist", "devops_principal", "CI/CD integration")

    chain = tracker.get_chain()
    assert len(chain) == 2
    assert chain[0]["from"] == "sre_principal"
    assert chain[0]["to"] == "security_specialist"
    assert chain[1]["to"] == "devops_principal"


def test_handoff_chain_detects_circular():
    """Detect circular handoff patterns."""
    tracker = HandoffChainTracker()
    tracker.add_handoff("agent_a", "agent_b", "reason1")
    tracker.add_handoff("agent_b", "agent_c", "reason2")

    is_circular = tracker.would_be_circular("agent_c", "agent_a")
    assert is_circular


def test_handoff_chain_timestamps():
    """Each handoff has timestamp."""
    tracker = HandoffChainTracker()
    tracker.add_handoff("agent_a", "agent_b", "reason")

    chain = tracker.get_chain()
    assert "timestamp" in chain[0]
    # Verify timestamp is recent (within last second)
    timestamp = datetime.fromisoformat(chain[0]["timestamp"])
    assert (datetime.now() - timestamp).total_seconds() < 1


def test_handoff_chain_maintains_order():
    """Chain maintains chronological order."""
    tracker = HandoffChainTracker()
    tracker.add_handoff("agent_1", "agent_2", "first")
    tracker.add_handoff("agent_2", "agent_3", "second")
    tracker.add_handoff("agent_3", "agent_4", "third")

    chain = tracker.get_chain()
    assert chain[0]["from"] == "agent_1"
    assert chain[1]["from"] == "agent_2"
    assert chain[2]["from"] == "agent_3"


def test_handoff_chain_no_circular_for_different_agents():
    """Don't detect circular for different agents."""
    tracker = HandoffChainTracker()
    tracker.add_handoff("agent_a", "agent_b", "reason")

    is_circular = tracker.would_be_circular("agent_b", "agent_c")
    assert not is_circular


# Feature 2.4: Max Handoffs Guard (F009)
def test_max_handoffs_guard():
    """Stop execution after max handoffs reached."""
    guard = MaxHandoffsGuard(max_handoffs=3)

    guard.record_handoff()  # 1
    guard.record_handoff()  # 2
    guard.record_handoff()  # 3

    with pytest.raises(MaxHandoffsExceeded):
        guard.record_handoff()  # 4 - exceeds limit


def test_max_handoffs_configurable():
    """Max handoffs limit is configurable."""
    guard = MaxHandoffsGuard(max_handoffs=5)

    for _ in range(5):
        guard.record_handoff()  # Should not raise

    with pytest.raises(MaxHandoffsExceeded):
        guard.record_handoff()


def test_max_handoffs_warns_before_limit():
    """Warn when approaching limit."""
    guard = MaxHandoffsGuard(max_handoffs=3)
    guard.record_handoff()
    guard.record_handoff()

    assert guard.is_approaching_limit  # At 2 of 3


def test_max_handoffs_default_limit():
    """Default limit is 5."""
    guard = MaxHandoffsGuard()

    for _ in range(5):
        guard.record_handoff()

    with pytest.raises(MaxHandoffsExceeded):
        guard.record_handoff()


def test_max_handoffs_not_approaching_initially():
    """Not approaching limit initially."""
    guard = MaxHandoffsGuard(max_handoffs=5)
    assert not guard.is_approaching_limit


# Feature 2.5: Handoff Result Aggregator (F010)
def test_aggregate_handoff_results():
    """Aggregate outputs from multiple agents."""
    results = [
        AgentResult(agent="dns", output="DNS configured", handoff={"target": "azure", "context": {}}),
        AgentResult(agent="azure", output="Azure setup complete", handoff=None)
    ]

    aggregated = aggregate_results(results)
    assert "DNS configured" in aggregated.combined_output
    assert "Azure setup complete" in aggregated.combined_output
    assert aggregated.handoff_count == 1  # One handoff between them


def test_aggregated_result_has_chain():
    """Aggregated result includes handoff chain."""
    results = [
        AgentResult(agent="agent_a", output="Step 1", handoff={"target": "agent_b"}),
        AgentResult(agent="agent_b", output="Step 2", handoff=None)
    ]

    aggregated = aggregate_results(results)
    assert len(aggregated.agents_involved) == 2
    assert aggregated.final_agent == "agent_b"


def test_aggregated_result_preserves_attribution():
    """Aggregated result preserves agent attribution."""
    results = [
        AgentResult(agent="agent_a", output="Output A", handoff={"target": "agent_b"}),
        AgentResult(agent="agent_b", output="Output B", handoff=None)
    ]

    aggregated = aggregate_results(results)
    assert "agent_a" in aggregated.combined_output
    assert "agent_b" in aggregated.combined_output
    assert "Output A" in aggregated.combined_output
    assert "Output B" in aggregated.combined_output


def test_aggregated_result_tracks_timing():
    """Aggregated result includes timing metrics."""
    results = [
        AgentResult(agent="agent_a", output="Output A", handoff=None),
    ]

    aggregated = aggregate_results(results)
    assert hasattr(aggregated, 'total_duration')
    assert aggregated.total_duration >= 0


def test_aggregated_result_single_agent():
    """Aggregate works with single agent (no handoffs)."""
    results = [
        AgentResult(agent="solo_agent", output="Completed task", handoff=None)
    ]

    aggregated = aggregate_results(results)
    assert aggregated.handoff_count == 0
    assert len(aggregated.agents_involved) == 1
    assert aggregated.final_agent == "solo_agent"


def test_aggregated_result_empty_list():
    """Aggregate handles empty results list."""
    results = []

    aggregated = aggregate_results(results)
    assert aggregated.handoff_count == 0
    assert len(aggregated.agents_involved) == 0
    assert aggregated.combined_output == ""
