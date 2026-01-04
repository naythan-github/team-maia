#!/usr/bin/env python3
"""
Tests for Phase 6: Session Manager Integration (TDD)

Tests the orchestration of all PAI v2 components.
"""

import pytest
import tempfile
import time
from pathlib import Path
from unittest.mock import patch


def reset_all_singletons():
    """Reset all PAI v2 singletons for clean test isolation."""
    import claude.tools.learning.memory as memory_module
    import claude.tools.learning.verify as verify_module
    import claude.tools.learning.learn as learn_module
    import claude.tools.learning.session as session_module
    import claude.tools.learning.uocs as uocs_module

    memory_module._memory = None
    verify_module._verify = None
    learn_module._learn = None
    session_module._manager = None
    uocs_module._instances = {}


class TestSessionManagerBasic:
    """Tests for basic SessionManager functionality."""

    def test_start_session_returns_session_id(self):
        """Test that start_session returns a session ID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                reset_all_singletons()
                from claude.tools.learning.session import SessionManager

                manager = SessionManager()

                session_id = manager.start_session(
                    context_id="ctx_123",
                    initial_query="Fix the bug",
                    agent_used="sre_agent",
                    domain="sre"
                )

                assert session_id is not None
                assert session_id.startswith("s_")

    def test_start_session_sets_active_session(self):
        """Test that start_session sets the active session."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                reset_all_singletons()
                from claude.tools.learning.session import SessionManager

                manager = SessionManager()

                session_id = manager.start_session(
                    context_id="ctx_123",
                    initial_query="Fix the bug"
                )

                assert manager.active_session_id == session_id

    def test_end_session_returns_result(self):
        """Test that end_session returns a result dict."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                reset_all_singletons()
                from claude.tools.learning.session import SessionManager

                manager = SessionManager()

                manager.start_session(
                    context_id="ctx_123",
                    initial_query="Fix the bug"
                )

                result = manager.end_session()

                assert isinstance(result, dict)
                assert 'session_id' in result
                assert 'verify' in result
                assert 'learn' in result
                assert 'summary' in result

    def test_end_session_clears_active_session(self):
        """Test that end_session clears the active session."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                reset_all_singletons()
                from claude.tools.learning.session import SessionManager

                manager = SessionManager()

                manager.start_session(
                    context_id="ctx_123",
                    initial_query="Fix the bug"
                )

                manager.end_session()

                assert manager.active_session_id is None

    def test_end_session_no_active_returns_error(self):
        """Test that end_session without active session returns error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                reset_all_singletons()
                from claude.tools.learning.session import SessionManager

                manager = SessionManager()

                result = manager.end_session()

                assert 'error' in result


class TestSessionManagerCapture:
    """Tests for tool output capture integration."""

    def test_capture_tool_output(self):
        """Test that capture_tool_output works during session."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                reset_all_singletons()
                from claude.tools.learning.session import SessionManager

                manager = SessionManager()

                manager.start_session(
                    context_id="ctx_123",
                    initial_query="Test"
                )

                # Should not raise
                manager.capture_tool_output(
                    tool_name="bash",
                    tool_input={"command": "ls"},
                    tool_output="file1.txt",
                    success=True,
                    latency_ms=100
                )

    def test_capture_tool_output_no_session(self):
        """Test that capture_tool_output is safe without session."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                reset_all_singletons()
                from claude.tools.learning.session import SessionManager

                manager = SessionManager()

                # Should not raise even without active session
                manager.capture_tool_output(
                    tool_name="bash",
                    tool_input={},
                    tool_output="",
                    success=True,
                    latency_ms=100
                )


class TestSessionManagerVerifyLearn:
    """Tests for VERIFY and LEARN integration."""

    def test_end_session_runs_verify(self):
        """Test that end_session runs VERIFY phase."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                reset_all_singletons()
                from claude.tools.learning.session import SessionManager

                manager = SessionManager()

                manager.start_session(
                    context_id="ctx_123",
                    initial_query="Test"
                )

                # Capture some outputs
                manager.capture_tool_output("bash", {}, "out", True, 100)
                time.sleep(0.2)

                result = manager.end_session()

                assert 'verify' in result
                assert 'success' in result['verify']
                assert 'confidence' in result['verify']

    def test_end_session_runs_learn(self):
        """Test that end_session runs LEARN phase."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                reset_all_singletons()
                from claude.tools.learning.session import SessionManager

                manager = SessionManager()

                manager.start_session(
                    context_id="ctx_123",
                    initial_query="Test",
                    domain="sre"
                )

                # Capture enough for patterns
                for i in range(5):
                    manager.capture_tool_output("bash", {"i": i}, f"out{i}", True, 100)
                    manager.capture_tool_output("read", {"i": i}, f"content{i}", True, 50)

                time.sleep(0.3)

                result = manager.end_session()

                assert 'learn' in result
                assert isinstance(result['learn'], list)


class TestSessionManagerContext:
    """Tests for context retrieval."""

    def test_get_relevant_context(self):
        """Test that get_relevant_context returns context."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                reset_all_singletons()
                from claude.tools.learning.session import SessionManager

                manager = SessionManager()

                # Create a session with summary
                manager.start_session("ctx", "Fix memory leak")
                manager.capture_tool_output("bash", {}, "out", True, 100)
                time.sleep(0.2)
                manager.end_session()

                # Query for related context
                context = manager.get_relevant_context("memory leak")

                # May or may not find context depending on FTS
                assert isinstance(context, str)


class TestSessionManagerSingleton:
    """Tests for SessionManager singleton."""

    def test_get_session_manager_returns_singleton(self):
        """Test that get_session_manager returns same instance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                reset_all_singletons()

                from claude.tools.learning.session import get_session_manager

                m1 = get_session_manager()
                m2 = get_session_manager()

                assert m1 is m2


class TestFullSessionLifecycle:
    """Integration tests for complete session lifecycle."""

    def test_full_session_lifecycle(self):
        """Test complete session from start to end."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                reset_all_singletons()
                from claude.tools.learning.session import SessionManager

                manager = SessionManager()

                # Start session
                sid = manager.start_session(
                    context_id="test_ctx",
                    initial_query="Help me fix the auth bug",
                    agent_used="security_agent",
                    domain="security"
                )

                assert manager.active_session_id == sid

                # Capture some tool outputs
                manager.capture_tool_output("read", {"file": "auth.py"}, "code...", True, 50)
                manager.capture_tool_output("grep", {"pattern": "password"}, "matches", True, 100)
                manager.capture_tool_output("edit", {"file": "auth.py"}, "edited", True, 200)

                time.sleep(0.3)

                # End session
                result = manager.end_session()

                assert result['session_id'] == sid
                assert 'verify' in result
                assert 'learn' in result
                assert 'summary' in result

                # Session should be cleared
                assert manager.active_session_id is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
