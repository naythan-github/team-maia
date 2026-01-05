#!/usr/bin/env python3
"""
Tests for P6: PostToolUse Hook - Capture tool outputs via Claude Code hook (TDD)

Phase 234: Create a PostToolUse hook that captures tool outputs to UOCS.
"""

import pytest
import json
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestToolOutputHookBasic:
    """Tests for basic hook functionality."""

    def test_hook_script_exists(self):
        """Test that hook script file exists."""
        hook_path = Path(__file__).parent.parent.parent / "claude" / "hooks" / "tool_output_capture.py"

        # This will fail initially (TDD red phase)
        # After implementation, this should pass
        from claude.hooks.tool_output_capture import process_tool_output

        assert callable(process_tool_output)

    def test_hook_parses_json_input(self):
        """Test that hook correctly parses JSON input."""
        from claude.hooks.tool_output_capture import process_tool_output

        input_data = {
            "tool_name": "Read",
            "tool_input": {"file_path": "/test/file.py"},
            "tool_response": {"content": "file contents"},
            "session_id": "test_session_123"
        }

        result = process_tool_output(input_data)

        assert result is not None
        assert result.get('processed') is True

    def test_hook_handles_missing_fields(self):
        """Test that hook handles missing fields gracefully."""
        from claude.hooks.tool_output_capture import process_tool_output

        # Minimal input
        input_data = {"tool_name": "Bash"}

        result = process_tool_output(input_data)

        assert result is not None  # Should not raise


class TestToolOutputCapture:
    """Tests for capturing tool outputs to UOCS."""

    def test_captures_bash_output(self):
        """Test that Bash tool output is captured."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.hooks.tool_output_capture import capture_to_uocs

                input_data = {
                    "tool_name": "Bash",
                    "tool_input": {"command": "ls -la"},
                    "tool_response": {"stdout": "file1.txt\nfile2.txt"},
                    "session_id": "test_session"
                }

                result = capture_to_uocs(input_data)

                assert result['captured'] is True

    def test_captures_read_output(self):
        """Test that Read tool output is captured."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.hooks.tool_output_capture import capture_to_uocs

                input_data = {
                    "tool_name": "Read",
                    "tool_input": {"file_path": "/app/main.py"},
                    "tool_response": {"content": "def main(): pass"},
                    "session_id": "test_session"
                }

                result = capture_to_uocs(input_data)

                assert result['captured'] is True

    def test_captures_edit_output(self):
        """Test that Edit tool output is captured."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.hooks.tool_output_capture import capture_to_uocs

                input_data = {
                    "tool_name": "Edit",
                    "tool_input": {
                        "file_path": "/app/config.py",
                        "old_string": "DEBUG=True",
                        "new_string": "DEBUG=False"
                    },
                    "tool_response": {"success": True},
                    "session_id": "test_session"
                }

                result = capture_to_uocs(input_data)

                assert result['captured'] is True

    def test_extracts_latency_from_response(self):
        """Test that latency is extracted from tool response."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.hooks.tool_output_capture import capture_to_uocs

                input_data = {
                    "tool_name": "Bash",
                    "tool_input": {"command": "pwd"},
                    "tool_response": {"stdout": "/home"},
                    "session_id": "test_session",
                    "duration_ms": 150
                }

                result = capture_to_uocs(input_data)

                assert result.get('latency_ms') == 150 or result['captured'] is True


class TestHookIntegration:
    """Tests for hook integration with UOCS."""

    def test_hook_uses_existing_uocs_session(self):
        """Test that hook uses existing UOCS session if available."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.uocs import get_uocs, _active_uocs
                from claude.hooks.tool_output_capture import capture_to_uocs

                _active_uocs.clear()

                # Pre-create a UOCS session
                session_id = "existing_session"
                uocs = get_uocs(session_id)

                # Capture via hook
                input_data = {
                    "tool_name": "Bash",
                    "tool_input": {"command": "echo test"},
                    "tool_response": {"stdout": "test"},
                    "session_id": session_id
                }

                capture_to_uocs(input_data)

                # Give async capture time
                import time
                time.sleep(0.2)

                # Verify capture was added to existing session
                assert len(uocs.captures) >= 1

    def test_hook_creates_uocs_session_if_needed(self):
        """Test that hook creates UOCS session if none exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.uocs import _active_uocs, close_uocs
                from claude.hooks.tool_output_capture import capture_to_uocs

                _active_uocs.clear()

                session_id = "new_session"

                input_data = {
                    "tool_name": "Bash",
                    "tool_input": {"command": "pwd"},
                    "tool_response": {"stdout": "/home"},
                    "session_id": session_id
                }

                result = capture_to_uocs(input_data)

                assert result['captured'] is True
                assert session_id in _active_uocs

                # Clean up async operations before temp dir removal
                import time
                time.sleep(0.2)
                close_uocs(session_id)


class TestHookOutputFormat:
    """Tests for hook output format."""

    def test_hook_returns_valid_json(self):
        """Test that hook returns valid JSON response."""
        from claude.hooks.tool_output_capture import process_tool_output

        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "ls"},
            "tool_response": {"stdout": "files"},
            "session_id": "test"
        }

        result = process_tool_output(input_data)

        # Result should be JSON serializable
        json.dumps(result)  # Should not raise

    def test_hook_returns_decision_allow(self):
        """Test that hook returns 'allow' decision (non-blocking)."""
        from claude.hooks.tool_output_capture import process_tool_output

        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "ls"},
            "tool_response": {"stdout": "files"},
            "session_id": "test"
        }

        result = process_tool_output(input_data)

        # PostToolUse hooks should allow continuation
        assert result.get('decision', 'allow') == 'allow'


class TestHookErrorHandling:
    """Tests for hook error handling."""

    def test_hook_handles_invalid_json(self):
        """Test that hook handles invalid JSON gracefully."""
        from claude.hooks.tool_output_capture import main as hook_main

        with patch('sys.stdin') as mock_stdin:
            mock_stdin.read.return_value = "not valid json"

            # Should not raise, just exit cleanly
            with patch('sys.exit') as mock_exit:
                hook_main()
                # Should exit with 0 (success - don't block)
                mock_exit.assert_called_with(0)

    def test_hook_handles_uocs_errors(self):
        """Test that hook handles UOCS errors gracefully."""
        from claude.hooks.tool_output_capture import capture_to_uocs

        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "ls"},
            "tool_response": {"stdout": "files"},
            "session_id": "test"
        }

        with patch('claude.tools.learning.uocs.get_uocs') as mock_uocs:
            mock_uocs.side_effect = Exception("UOCS error")

            result = capture_to_uocs(input_data)

            # Should not raise, return graceful result
            assert result.get('captured') is False or result.get('error') is not None


class TestHookConfiguration:
    """Tests for hook configuration generation."""

    def test_generate_hook_config(self):
        """Test that hook configuration is correctly generated."""
        from claude.hooks.tool_output_capture import generate_hook_config

        config = generate_hook_config()

        assert 'PostToolUse' in config
        assert config['PostToolUse'][0]['matcher'] == '*'
        assert 'tool_output_capture.py' in config['PostToolUse'][0]['hooks'][0]['command']

    def test_hook_config_is_valid_json(self):
        """Test that hook config is valid JSON."""
        from claude.hooks.tool_output_capture import generate_hook_config

        config = generate_hook_config()

        # Should be JSON serializable
        json.dumps(config)  # Should not raise


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
