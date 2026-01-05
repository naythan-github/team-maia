#!/usr/bin/env python3
"""
Tests for learning_session_start.py - Unconditional PAI v2 session start.

Phase 236: Fix learning not capturing by starting sessions unconditionally.

TDD Tests:
1. test_starts_session_on_first_prompt - Session starts on first user prompt
2. test_no_duplicate_sessions - Doesn't start if session already exists
3. test_creates_session_file - Creates ~/.maia/sessions/ file
4. test_non_blocking - Returns quickly (<50ms)
5. test_extracts_context_id - Properly extracts context ID
6. test_handles_missing_dirs - Creates directories if needed
"""

import pytest
import time
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "claude" / "hooks"))


class TestLearningSessionStart:
    """Tests for the learning session start hook."""

    @pytest.fixture
    def maia_root(self):
        """Get maia root directory."""
        return Path(__file__).parent.parent.parent

    @pytest.fixture
    def sessions_dir(self, tmp_path):
        """Create temporary sessions directory."""
        sessions = tmp_path / "sessions"
        sessions.mkdir(parents=True)
        return sessions

    @pytest.fixture
    def mock_context_id(self):
        """Generate a mock context ID."""
        return "test_12345"

    def test_script_exists(self, maia_root):
        """The learning_session_start.py script should exist."""
        script = maia_root / "claude" / "hooks" / "learning_session_start.py"
        assert script.exists(), (
            "learning_session_start.py should exist in claude/hooks/"
        )

    def test_starts_session_on_first_prompt(self, maia_root, sessions_dir, mock_context_id):
        """Session should start on first user prompt."""
        from claude.hooks.learning_session_start import LearningSessionStarter

        starter = LearningSessionStarter(
            maia_root=maia_root,
            sessions_dir=sessions_dir
        )

        # No existing session
        assert not list(sessions_dir.glob("learning_session_*.json"))

        # Start session
        result = starter.start_if_needed(
            context_id=mock_context_id,
            user_message="help me debug this code"
        )

        assert result["started"] is True, "Should start a new session"
        assert result["session_id"] is not None, "Should return session ID"

    def test_no_duplicate_sessions(self, maia_root, sessions_dir, mock_context_id):
        """Should not start duplicate sessions for same context."""
        from claude.hooks.learning_session_start import LearningSessionStarter

        starter = LearningSessionStarter(
            maia_root=maia_root,
            sessions_dir=sessions_dir
        )

        # Start first session
        result1 = starter.start_if_needed(
            context_id=mock_context_id,
            user_message="first message"
        )
        assert result1["started"] is True

        # Try to start again
        result2 = starter.start_if_needed(
            context_id=mock_context_id,
            user_message="second message"
        )
        assert result2["started"] is False, "Should not start duplicate session"
        assert result2["reason"] == "session_exists"

    def test_creates_session_file(self, maia_root, sessions_dir, mock_context_id):
        """Should create a learning session file."""
        from claude.hooks.learning_session_start import LearningSessionStarter

        starter = LearningSessionStarter(
            maia_root=maia_root,
            sessions_dir=sessions_dir
        )

        starter.start_if_needed(
            context_id=mock_context_id,
            user_message="test message"
        )

        # Check session file exists
        session_files = list(sessions_dir.glob(f"learning_session_{mock_context_id}.json"))
        assert len(session_files) == 1, "Should create exactly one session file"

        # Verify file contents
        with open(session_files[0]) as f:
            data = json.load(f)
        assert "session_id" in data
        assert "context_id" in data
        assert data["context_id"] == mock_context_id
        assert "initial_query" in data
        assert "started_at" in data

    def test_non_blocking(self, maia_root, sessions_dir, mock_context_id):
        """Should return quickly (<50ms)."""
        from claude.hooks.learning_session_start import LearningSessionStarter

        starter = LearningSessionStarter(
            maia_root=maia_root,
            sessions_dir=sessions_dir
        )

        start = time.perf_counter()
        starter.start_if_needed(
            context_id=mock_context_id,
            user_message="test message"
        )
        elapsed = (time.perf_counter() - start) * 1000

        assert elapsed < 50, f"Should complete in <50ms, took {elapsed:.1f}ms"

    def test_handles_missing_dirs(self, maia_root, tmp_path, mock_context_id):
        """Should create directories if they don't exist."""
        from claude.hooks.learning_session_start import LearningSessionStarter

        sessions_dir = tmp_path / "nonexistent" / "sessions"
        assert not sessions_dir.exists()

        starter = LearningSessionStarter(
            maia_root=maia_root,
            sessions_dir=sessions_dir
        )

        result = starter.start_if_needed(
            context_id=mock_context_id,
            user_message="test"
        )

        assert result["started"] is True
        assert sessions_dir.exists(), "Should create missing directories"

    def test_integrates_with_session_manager(self, maia_root, sessions_dir, mock_context_id):
        """Should properly initialize PAI v2 SessionManager."""
        from claude.hooks.learning_session_start import LearningSessionStarter

        starter = LearningSessionStarter(
            maia_root=maia_root,
            sessions_dir=sessions_dir
        )

        result = starter.start_if_needed(
            context_id=mock_context_id,
            user_message="implement feature X"
        )

        # Session file should have learning-specific fields
        session_file = sessions_dir / f"learning_session_{mock_context_id}.json"
        with open(session_file) as f:
            data = json.load(f)

        assert "session_id" in data
        assert data["session_id"].startswith("s_"), "Session ID should have PAI v2 format"


class TestLearningSessionStartCLI:
    """Tests for CLI entry point."""

    @pytest.fixture
    def maia_root(self):
        return Path(__file__).parent.parent.parent

    def test_cli_returns_zero_on_success(self, maia_root, tmp_path):
        """CLI should return 0 on success."""
        import subprocess

        script = maia_root / "claude" / "hooks" / "learning_session_start.py"
        if not script.exists():
            pytest.skip("Script not yet implemented")

        env = os.environ.copy()
        env["MAIA_SESSIONS_DIR"] = str(tmp_path)
        env["CLAUDE_CONTEXT_ID"] = "cli_test_123"

        result = subprocess.run(
            ["python3", str(script), "test message"],
            capture_output=True,
            text=True,
            env=env,
            timeout=5
        )

        assert result.returncode == 0, f"CLI failed: {result.stderr}"

    def test_cli_silent_by_default(self, maia_root, tmp_path):
        """CLI should produce no output by default (silent mode)."""
        import subprocess

        script = maia_root / "claude" / "hooks" / "learning_session_start.py"
        if not script.exists():
            pytest.skip("Script not yet implemented")

        env = os.environ.copy()
        env["MAIA_SESSIONS_DIR"] = str(tmp_path)
        env["CLAUDE_CONTEXT_ID"] = "cli_test_456"

        result = subprocess.run(
            ["python3", str(script), "test message"],
            capture_output=True,
            text=True,
            env=env,
            timeout=5
        )

        assert result.stdout == "", "Should be silent (no stdout)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
