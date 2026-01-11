"""
Tests for Sprint 3: Session Integration - Automatic Agent Handoffs

Features:
- F011: Session Handoff State
- F012: Handoff Context Injection
- F013: Learning Integration
- F014: Handoff Recovery
"""

import json
import tempfile
from pathlib import Path
import pytest


# ==============================================================================
# Feature 3.1: Session Handoff State (F011)
# ==============================================================================

def test_session_stores_handoff_chain():
    """Session state includes handoff chain."""
    from claude.hooks.session_handoffs import add_handoff_to_session

    # Create test session file
    session_file = Path(tempfile.gettempdir()) / "test_session.json"
    session = {
        "current_agent": "sre_principal",
        "handoff_chain": ["sre_principal"],
        "context": {}
    }
    session_file.write_text(json.dumps(session))

    add_handoff_to_session(session_file, {
        "from": "sre_principal",
        "to": "security_specialist",
        "reason": "Security review",
        "timestamp": "2026-01-11T10:00:00Z"
    })

    updated = json.loads(session_file.read_text())
    assert len(updated["handoff_chain"]) == 2
    assert updated["current_agent"] == "security_specialist"

    # Cleanup
    session_file.unlink()


def test_session_preserves_context():
    """Handoff preserves existing session context."""
    from claude.hooks.session_handoffs import add_handoff_to_session

    session_file = Path(tempfile.gettempdir()) / "test_session2.json"
    session = {
        "current_agent": "agent_a",
        "handoff_chain": ["agent_a"],
        "context": {"important_data": "preserved"},
        "session_start": "2026-01-11T09:00:00Z"
    }
    session_file.write_text(json.dumps(session))

    add_handoff_to_session(session_file, {
        "from": "agent_a",
        "to": "agent_b",
        "reason": "Handoff reason"
    })

    updated = json.loads(session_file.read_text())
    assert updated["context"]["important_data"] == "preserved"
    assert updated["session_start"] == "2026-01-11T09:00:00Z"

    # Cleanup
    session_file.unlink()


# ==============================================================================
# Feature 3.2: Handoff Context Injection (F012)
# ==============================================================================

def test_inject_handoff_context():
    """Inject prior agent context into new agent prompt."""
    from claude.hooks.session_handoffs import inject_handoff_context

    handoff_chain = [
        {
            "from": "sre_principal",
            "to": "security_specialist",
            "reason": "Security review",
            "output": "Found potential SQL injection in user_handler.py line 42"
        }
    ]

    context = inject_handoff_context(
        target_agent="security_specialist",
        handoff_chain=handoff_chain
    )

    assert "Prior work by sre_principal" in context
    assert "SQL injection" in context
    assert "user_handler.py" in context


def test_inject_handoff_context_truncates_long_output():
    """Truncate long agent output in context injection."""
    from claude.hooks.session_handoffs import inject_handoff_context

    long_output = "x" * 5000  # Exceeds 2000 char limit

    handoff_chain = [
        {
            "from": "verbose_agent",
            "to": "next_agent",
            "output": long_output
        }
    ]

    context = inject_handoff_context("next_agent", handoff_chain)
    assert len(context) < 3000  # Reasonable limit with formatting


def test_inject_multiple_handoffs():
    """Handle multiple prior handoffs in context."""
    from claude.hooks.session_handoffs import inject_handoff_context

    handoff_chain = [
        {"from": "agent_a", "to": "agent_b", "output": "Step 1 complete"},
        {"from": "agent_b", "to": "agent_c", "output": "Step 2 complete"}
    ]

    context = inject_handoff_context("agent_c", handoff_chain)
    assert "agent_a" in context
    assert "agent_b" in context
    assert "Step 1" in context
    assert "Step 2" in context


# ==============================================================================
# Feature 3.3: Learning Integration (F013)
# ==============================================================================

def test_capture_handoff_patterns():
    """Capture successful handoff patterns for learning."""
    from claude.hooks.session_handoffs import HandoffPatternTracker

    tracker = HandoffPatternTracker(storage_path=Path(tempfile.gettempdir()) / "test_capture.json")

    tracker.log_handoff(
        from_agent="sre_principal",
        to_agent="security_specialist",
        query="Review code security",
        success=True
    )

    patterns = tracker.get_patterns()
    assert len(patterns) >= 1
    assert patterns[0]["from"] == "sre_principal"
    assert patterns[0]["to"] == "security_specialist"
    assert patterns[0]["success"]

    # Cleanup
    (Path(tempfile.gettempdir()) / "test_capture.json").unlink(missing_ok=True)


def test_pattern_frequency_tracking():
    """Track frequency of handoff patterns."""
    from claude.hooks.session_handoffs import HandoffPatternTracker

    tracker = HandoffPatternTracker(storage_path=Path(tempfile.gettempdir()) / "test_frequency.json")

    # Same handoff pattern twice
    tracker.log_handoff("agent_a", "agent_b", "query1", True)
    tracker.log_handoff("agent_a", "agent_b", "query2", True)

    stats = tracker.get_pattern_stats("agent_a", "agent_b")
    assert stats["count"] == 2
    assert stats["success_rate"] == 1.0

    # Cleanup
    (Path(tempfile.gettempdir()) / "test_frequency.json").unlink(missing_ok=True)


def test_pattern_persistence():
    """Patterns persist to file."""
    from claude.hooks.session_handoffs import HandoffPatternTracker

    tracker = HandoffPatternTracker(storage_path=Path(tempfile.gettempdir()) / "patterns.json")
    tracker.log_handoff("a", "b", "q", True)

    # New tracker loads same patterns
    tracker2 = HandoffPatternTracker(storage_path=Path(tempfile.gettempdir()) / "patterns.json")
    patterns = tracker2.get_patterns()
    assert len(patterns) >= 1

    # Cleanup
    (Path(tempfile.gettempdir()) / "patterns.json").unlink(missing_ok=True)


# ==============================================================================
# Feature 3.4: Handoff Recovery (F014)
# ==============================================================================

def test_handoff_recovery_agent_not_found():
    """Recover when target agent not found."""
    from claude.hooks.session_handoffs import HandoffRecovery

    recovery = HandoffRecovery()

    result = recovery.handle_failure(
        source_agent="sre_principal",
        target_agent="nonexistent_agent",
        error="Agent not found",
        context={"query": "original query"}
    )

    assert result.recovered
    assert result.fallback_agent == "sre_principal"  # Return to source
    assert result.error_logged


def test_handoff_recovery_suggests_alternatives():
    """Suggest alternative agents when target fails."""
    from claude.hooks.session_handoffs import HandoffRecovery

    recovery = HandoffRecovery()

    result = recovery.handle_failure(
        source_agent="sre_principal",
        target_agent="security_specialist",
        error="Agent timeout",
        context={}
    )

    # Should suggest related agents or have fallback
    assert len(result.suggested_alternatives) > 0 or result.fallback_agent is not None


def test_handoff_recovery_logs_failure():
    """Failed handoffs are logged for analysis."""
    from claude.hooks.session_handoffs import HandoffRecovery

    recovery = HandoffRecovery(log_path=Path(tempfile.gettempdir()) / "failures.json")

    recovery.handle_failure(
        source_agent="agent_a",
        target_agent="agent_b",
        error="Connection timeout",
        context={}
    )

    # Verify failure logged
    log_content = json.loads(Path(Path(tempfile.gettempdir()) / "failures.json").read_text())
    assert len(log_content) >= 1
    assert log_content[-1]["error"] == "Connection timeout"

    # Cleanup
    (Path(tempfile.gettempdir()) / "failures.json").unlink(missing_ok=True)
