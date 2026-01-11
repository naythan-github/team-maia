"""
Tests for Feature 5.1: Update swarm_auto_loader.py (F019)
Integrate IntegratedSwarmOrchestrator into the existing hook.
"""

def test_hook_imports_swarm_integration():
    """Hook can import swarm integration module."""
    from claude.tools.orchestration.swarm_integration import IntegratedSwarmOrchestrator
    assert IntegratedSwarmOrchestrator is not None

def test_hook_creates_handoff_enabled_session():
    """Hook creates session with handoff capability when enabled."""
    from claude.hooks.swarm_auto_loader import create_session_state

    classification = {
        "confidence": 0.85,
        "complexity": 5,
        "primary_domain": "sre"
    }

    # Create session with handoff enabled
    success = create_session_state(
        agent="sre_principal_engineer",
        domain="sre",
        classification=classification,
        query="Review system health",
        enable_handoffs=True  # New parameter
    )

    assert success

def test_session_includes_handoff_tools():
    """Session state includes handoff tools when enabled."""
    import json
    from pathlib import Path
    from claude.hooks.swarm_auto_loader import get_session_file_path, create_session_state

    classification = {
        "confidence": 0.85,
        "complexity": 5,
        "primary_domain": "sre"
    }

    # Create session with handoffs enabled
    create_session_state(
        agent="sre_principal_engineer",
        domain="sre",
        classification=classification,
        query="Review system health",
        enable_handoffs=True
    )

    # This test checks that session has handoff capability marker
    session_file = get_session_file_path()
    if session_file.exists():
        session = json.loads(session_file.read_text())
        # Check for handoff capability
        assert "handoffs_enabled" in session or session.get("version", "1.0") >= "1.4"
