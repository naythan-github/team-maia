#!/usr/bin/env python3
"""
PAI v2 End-to-End Integration Tests

Tests the complete PAI v2 learning system workflow:
1. Session start with context injection
2. Tool output capture via UOCS
3. Session end with VERIFY + LEARN
4. Files touched extraction
5. Preference detection and self-modification
6. LLM summarization (mocked)
"""

import pytest
import tempfile
import time
import json
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestPAIv2EndToEnd:
    """End-to-end integration tests for PAI v2."""

    def test_full_session_lifecycle_with_learning(self):
        """Test complete session lifecycle: start -> capture -> end -> learn."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                # Reset all singletons
                import claude.tools.learning.memory as memory_module
                import claude.tools.learning.session as session_module
                import claude.tools.learning.uocs as uocs_module
                import claude.tools.learning.learn as learn_module
                memory_module._memory = None
                session_module._manager = None
                uocs_module._active_uocs.clear()
                learn_module._learn = None

                from claude.tools.learning.session import SessionManager

                manager = SessionManager()

                # 1. Start session
                session_id = manager.start_session(
                    context_id="integration_test_ctx",
                    initial_query="Fix authentication bug in OAuth module",
                    agent_used="security_agent",
                    domain="security"
                )

                assert session_id is not None
                assert manager.active_session_id == session_id

                # 2. Capture tool outputs
                manager.capture_tool_output(
                    "read",
                    {"file_path": "/app/auth/oauth.py"},
                    "class OAuthProvider: ...",
                    True,
                    50
                )
                manager.capture_tool_output(
                    "grep",
                    {"pattern": "token", "path": "/app/auth"},
                    "oauth.py:15: token = ...",
                    True,
                    30
                )
                manager.capture_tool_output(
                    "edit",
                    {"file_path": "/app/auth/oauth.py", "old_string": "old", "new_string": "new"},
                    "success",
                    True,
                    100
                )
                manager.capture_tool_output(
                    "bash",
                    {"command": "pytest tests/auth/"},
                    "5 passed",
                    True,
                    500
                )

                # Wait for async captures
                time.sleep(0.3)

                # 3. End session - triggers VERIFY + LEARN
                result = manager.end_session()

                # 4. Verify results
                assert result['session_id'] == session_id
                assert 'verify' in result
                assert 'learn' in result
                assert result['verify']['success'] is True  # All tools succeeded

                # 5. Check Maia Memory was updated
                recent = manager.memory.get_recent(1)
                assert len(recent) == 1
                assert recent[0]['id'] == session_id
                assert recent[0]['status'] == 'completed'
                assert recent[0]['verify_success'] == 1

                # 6. Check files touched were extracted
                files_touched = json.loads(recent[0]['files_touched'])
                assert '/app/auth/oauth.py' in files_touched

    def test_context_injection_provides_relevant_history(self):
        """Test that context injection finds relevant prior sessions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                # Reset singletons
                import claude.tools.learning.memory as memory_module
                memory_module._memory = None

                from claude.tools.learning.memory import MaiaMemory
                from claude.tools.learning.context_injection import get_learning_context

                memory = MaiaMemory()

                # Create historical sessions
                memory.start_session("s1", "ctx1", "Fix OAuth authentication bug")
                memory.end_session("s1", "Fixed token refresh logic in oauth.py",
                                   ["Used debugger to trace token flow"],
                                   {"read": 5, "edit": 2}, ["/app/auth/oauth.py"],
                                   True, 0.9, {}, [])

                memory.start_session("s2", "ctx2", "Optimize database queries")
                memory.end_session("s2", "Added indexes", [], {}, [], True, 0.8, {}, [])

                # Query for authentication context
                context = get_learning_context("authentication bug")

                # Should find the OAuth session
                assert "Relevant Prior Sessions" in context or context != ""

    def test_preference_detection_in_conversation(self):
        """Test that preferences are detected from conversation patterns."""
        from claude.tools.learning.preference_detection import analyze_conversation

        messages = [
            {"role": "user", "content": "Help me format this code"},
            {"role": "assistant", "content": "Here's the formatted code with 2-space indentation..."},
            {"role": "user", "content": "No, use 4 spaces. I always prefer 4-space indentation."},
            {"role": "assistant", "content": "Updated to 4-space indentation."},
            {"role": "user", "content": "Never use semicolons in JavaScript."}
        ]

        result = analyze_conversation(messages)

        # Should detect preferences
        assert result['total_found'] >= 2
        prefs = result['preferences']

        # Check for indentation preference
        pref_values = [str(p.get('value', '')).lower() for p in prefs]
        assert any('indent' in v or '4' in v or 'space' in v for v in pref_values)

    def test_self_modification_stores_preferences(self):
        """Test that self-modification correctly stores learned preferences."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.self_modification import (
                    update_preference, get_preference, list_preferences
                )

                # Update preferences from learnings
                update_preference(
                    category='coding_style',
                    key='indentation',
                    value='4 spaces',
                    confidence=0.8,
                    source_session='test_session_1'
                )

                update_preference(
                    category='tool_choice',
                    key='package_manager',
                    value='pnpm',
                    confidence=0.7,
                    source_session='test_session_1'
                )

                # Verify storage
                indent_pref = get_preference('coding_style', 'indentation')
                assert indent_pref is not None
                assert indent_pref['value'] == '4 spaces'
                assert indent_pref['confidence'] == 0.8

                # List all
                all_prefs = list_preferences()
                assert len(all_prefs) == 2

    def test_tool_output_hook_integration(self):
        """Test that tool output hook correctly integrates with UOCS."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.uocs import _active_uocs, close_uocs
                from claude.hooks.tool_output_capture import capture_to_uocs

                _active_uocs.clear()

                session_id = "hook_test_session"

                # Simulate PostToolUse hook inputs
                tool_calls = [
                    {
                        "tool_name": "Read",
                        "tool_input": {"file_path": "/app/main.py"},
                        "tool_response": {"content": "def main(): pass"},
                        "session_id": session_id,
                        "duration_ms": 45
                    },
                    {
                        "tool_name": "Bash",
                        "tool_input": {"command": "python -m pytest"},
                        "tool_response": {"stdout": "10 passed"},
                        "session_id": session_id,
                        "duration_ms": 1500
                    },
                    {
                        "tool_name": "Edit",
                        "tool_input": {"file_path": "/app/main.py", "old_string": "pass", "new_string": "return 0"},
                        "tool_response": {"success": True},
                        "session_id": session_id,
                        "duration_ms": 80
                    }
                ]

                for call in tool_calls:
                    result = capture_to_uocs(call)
                    assert result['captured'] is True

                # Wait for async
                time.sleep(0.3)

                # Verify captures
                uocs = _active_uocs[session_id]
                assert len(uocs.captures) == 3

                # Check files touched
                files = uocs.get_files_touched()
                assert '/app/main.py' in files

                # Cleanup
                close_uocs(session_id)

    def test_llm_summarizer_graceful_degradation(self):
        """Test that LLM summarizer works without Ollama."""
        from claude.tools.learning.llm_summarizer import LLMSummarizer

        summarizer = LLMSummarizer()

        # Mock Ollama as unavailable
        with patch.object(summarizer, '_call_ollama') as mock_ollama:
            mock_ollama.side_effect = Exception("Ollama not running")

            session_data = {
                'initial_query': 'Fix the bug',
                'tools_used': {'bash': 5},
                'files_touched': ['main.py']
            }

            # Should return empty list, not raise
            decisions = summarizer.extract_decisions(session_data)
            assert decisions == []

            # Summary should have fallback
            summary = summarizer.generate_summary(session_data)
            assert summary == "Session completed."


class TestPAIv2DataIntegrity:
    """Tests for data integrity across PAI v2 components."""

    def test_session_data_persists_across_components(self):
        """Test that session data is correctly passed between components."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                # Reset singletons
                import claude.tools.learning.memory as memory_module
                import claude.tools.learning.session as session_module
                import claude.tools.learning.uocs as uocs_module
                import claude.tools.learning.learn as learn_module
                memory_module._memory = None
                session_module._manager = None
                uocs_module._active_uocs.clear()
                learn_module._learn = None

                from claude.tools.learning.session import SessionManager

                manager = SessionManager()

                # Start and populate session
                session_id = manager.start_session(
                    context_id="data_integrity_test",
                    initial_query="Test data integrity",
                    agent_used="sre_agent",
                    domain="sre"
                )

                manager.capture_tool_output("bash", {"cmd": "test"}, "ok", True, 100)
                time.sleep(0.2)

                # End session
                result = manager.end_session()

                # Verify UOCS summary made it to Memory
                recent = manager.memory.get_recent(1)
                assert recent[0]['id'] == session_id

                tools_used = json.loads(recent[0]['tools_used'])
                assert 'bash' in tools_used

    def test_files_touched_flows_to_memory(self):
        """Test that files_touched from UOCS flows to Maia Memory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                # Reset singletons
                import claude.tools.learning.memory as memory_module
                import claude.tools.learning.session as session_module
                import claude.tools.learning.uocs as uocs_module
                import claude.tools.learning.learn as learn_module
                memory_module._memory = None
                session_module._manager = None
                uocs_module._active_uocs.clear()
                learn_module._learn = None

                from claude.tools.learning.session import SessionManager

                manager = SessionManager()

                session_id = manager.start_session(
                    context_id="files_test",
                    initial_query="Test files",
                    agent_used="sre_agent"
                )

                # Capture file operations
                manager.capture_tool_output("read", {"file_path": "/a.py"}, "c", True, 10)
                manager.capture_tool_output("edit", {"file_path": "/b.py", "old_string": "x", "new_string": "y"}, "ok", True, 20)
                manager.capture_tool_output("write", {"file_path": "/c.py"}, "ok", True, 30)

                time.sleep(0.3)

                manager.end_session()

                # Verify files in memory
                recent = manager.memory.get_recent(1)
                files = json.loads(recent[0]['files_touched'])

                assert '/a.py' in files
                assert '/b.py' in files
                assert '/c.py' in files


class TestPAIv2ErrorRecovery:
    """Tests for error recovery and graceful degradation."""

    def test_session_end_without_captures(self):
        """Test ending session with no tool captures."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                # Reset singletons
                import claude.tools.learning.memory as memory_module
                import claude.tools.learning.session as session_module
                import claude.tools.learning.uocs as uocs_module
                import claude.tools.learning.learn as learn_module
                memory_module._memory = None
                session_module._manager = None
                uocs_module._active_uocs.clear()
                learn_module._learn = None

                from claude.tools.learning.session import SessionManager

                manager = SessionManager()

                session_id = manager.start_session(
                    context_id="empty_session",
                    initial_query="Quick question",
                    agent_used=None
                )

                # End without any captures
                result = manager.end_session()

                # Should complete without error
                assert result['session_id'] == session_id
                assert result['verify']['success'] is False  # No activity = not successful

    def test_context_injection_with_empty_history(self):
        """Test context injection when no prior sessions exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.context_injection import get_learning_context

                # Fresh database - no history
                context = get_learning_context("any query")

                # Should return empty string, not error
                assert context == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
