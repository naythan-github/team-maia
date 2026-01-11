"""Test session state consistency across handoffs."""

import pytest
import json
import tempfile
from pathlib import Path
from claude.hooks.session_handoffs import add_handoff_to_session


class TestSessionStateIntegrity:
    """Test session state consistency across handoffs."""

    def test_context_preserved_through_multiple_handoffs(self):
        """Context preserved through 5+ handoffs."""
        session_file = Path(tempfile.gettempdir()) / "test_integrity_session.json"

        # Initial session with important context
        initial_session = {
            "current_agent": "agent_1",
            "handoff_chain": ["agent_1"],
            "context": {
                "user_id": "12345",
                "project": "maia",
                "critical_data": "must_preserve"
            },
            "session_start": "2026-01-11T10:00:00Z"
        }
        session_file.write_text(json.dumps(initial_session))

        # Simulate 5 handoffs
        for i in range(2, 7):
            add_handoff_to_session(session_file, {
                "from": f"agent_{i-1}",
                "to": f"agent_{i}",
                "reason": f"Handoff {i-1}"
            })

        final_session = json.loads(session_file.read_text())

        # Original context must be preserved
        assert final_session["context"]["user_id"] == "12345"
        assert final_session["context"]["project"] == "maia"
        assert final_session["context"]["critical_data"] == "must_preserve"
        assert len(final_session["handoff_chain"]) == 6

    def test_handoff_chain_accurate_after_recovery(self):
        """Handoff chain accurate after failed handoff + recovery."""
        session_file = Path(tempfile.gettempdir()) / "test_recovery_session.json"

        session = {
            "current_agent": "agent_a",
            "handoff_chain": ["agent_a"],
            "context": {}
        }
        session_file.write_text(json.dumps(session))

        # Successful handoff
        add_handoff_to_session(session_file, {
            "from": "agent_a",
            "to": "agent_b",
            "reason": "Normal handoff"
        })

        # Failed handoff (simulate by adding error context)
        add_handoff_to_session(session_file, {
            "from": "agent_b",
            "to": "agent_c",
            "reason": "Attempted handoff",
            "error": "Agent not found",
            "recovered": True,
            "fallback": "agent_b"
        })

        final_session = json.loads(session_file.read_text())

        # Chain should reflect the actual path - handoff_chain contains handoff records
        handoff_agents = [h["to"] for h in final_session["handoff_chain"] if isinstance(h, dict)]
        assert "agent_b" in handoff_agents
        # Initial agent is in handoff_chain as well
        assert final_session["handoff_chain"][0] == "agent_a" or (isinstance(final_session["handoff_chain"][0], dict) and final_session["handoff_chain"][0].get("to") == "agent_a")

    def test_session_not_corrupted_by_concurrent_writes(self):
        """Session file not corrupted by rapid writes."""
        session_file = Path(tempfile.gettempdir()) / "test_concurrent_session.json"

        session = {
            "current_agent": "start",
            "handoff_chain": ["start"],
            "context": {"counter": 0}
        }
        session_file.write_text(json.dumps(session))

        # Rapid sequential writes (simulating near-concurrent access)
        for i in range(10):
            add_handoff_to_session(session_file, {
                "from": f"agent_{i}",
                "to": f"agent_{i+1}",
                "reason": f"Handoff {i}"
            })

        # File should still be valid JSON
        final_session = json.loads(session_file.read_text())
        assert final_session["current_agent"] == "agent_10"
        assert len(final_session["handoff_chain"]) == 11

    def test_session_start_preserved_across_handoffs(self):
        """Original session_start timestamp preserved."""
        session_file = Path(tempfile.gettempdir()) / "test_timestamp_session.json"

        original_start = "2026-01-01T08:00:00Z"
        session = {
            "current_agent": "first",
            "handoff_chain": ["first"],
            "context": {},
            "session_start": original_start
        }
        session_file.write_text(json.dumps(session))

        add_handoff_to_session(session_file, {
            "from": "first",
            "to": "second",
            "reason": "Test"
        })

        final_session = json.loads(session_file.read_text())
        assert final_session["session_start"] == original_start
