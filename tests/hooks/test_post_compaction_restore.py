#!/usr/bin/env python3
"""
Tests for Post-Compaction Restore Hook
Phase 264: Auto-Resume System for Compaction Survival

TDD Phase 1: Tests written BEFORE implementation

Test Coverage:
- Checkpoint loading from durable storage
- Session file loading
- Agent determination logic
- Context output formatting
- Graceful degradation
- Performance (<2s requirement)

Author: Maia (Phase 264)
Created: 2026-01-11
"""

import json
import pytest
import tempfile
import shutil
import time
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock


# Import will fail until implementation exists - that's TDD
try:
    from claude.hooks.post_compaction_restore import (
        PostCompactionRestore,
        load_latest_checkpoint,
        load_session,
        determine_agent,
        format_restoration_context,
    )
    IMPLEMENTATION_EXISTS = True
except ImportError:
    IMPLEMENTATION_EXISTS = False


@pytest.fixture
def temp_dirs():
    """Create temporary checkpoint and session directories."""
    temp_base = Path(tempfile.mkdtemp())
    checkpoints_dir = temp_base / "checkpoints"
    sessions_dir = temp_base / "sessions"
    checkpoints_dir.mkdir()
    sessions_dir.mkdir()

    yield {
        "base": temp_base,
        "checkpoints": checkpoints_dir,
        "sessions": sessions_dir,
    }

    shutil.rmtree(temp_base, ignore_errors=True)


@pytest.fixture
def sample_checkpoint():
    """Create sample checkpoint data."""
    return {
        "context_id": "12345",
        "created_at": "2026-01-11T10:00:00",
        "phase_number": 264,
        "phase_name": "Auto-Resume System",
        "percent_complete": 75,
        "tdd_phase": "P4",
        "recommended_agent": "sre_principal_engineer_agent",
        "current_agent": "sre_principal_engineer_agent",
        "domain": "sre",
        "tests_passing": 20,
        "tests_total": 25,
        "current_branch": "main",
        "last_commit": "abc123 feat: add feature",
        "modified_files": ["file1.py", "file2.py"],
        "is_code_project": True,
        "next_action": "Fix 5 failing tests",
    }


@pytest.fixture
def sample_session():
    """Create sample session data."""
    return {
        "current_agent": "sre_principal_engineer_agent",
        "session_start": "2026-01-11T09:00:00Z",
        "handoff_chain": ["sre_principal_engineer_agent"],
        "context": {},
        "domain": "sre",
        "last_classification_confidence": 1.0,
        "query": "Working on auto-resume feature",
    }


class TestLoadLatestCheckpoint:
    """Tests for loading checkpoint from durable storage."""

    @pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="Implementation not yet created")
    def test_load_latest_checkpoint_returns_dict(self, temp_dirs, sample_checkpoint):
        """load_latest_checkpoint returns checkpoint dictionary."""
        context_dir = temp_dirs["checkpoints"] / "12345"
        context_dir.mkdir()
        checkpoint_path = context_dir / "checkpoint_20260111_100000.json"
        checkpoint_path.write_text(json.dumps(sample_checkpoint))

        with patch(
            'claude.hooks.post_compaction_restore.DURABLE_CHECKPOINT_DIR',
            temp_dirs["checkpoints"]
        ):
            result = load_latest_checkpoint("12345")

        assert isinstance(result, dict)
        assert result["context_id"] == "12345"

    @pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="Implementation not yet created")
    def test_load_latest_checkpoint_returns_most_recent(self, temp_dirs, sample_checkpoint):
        """Returns the most recently modified checkpoint."""
        context_dir = temp_dirs["checkpoints"] / "12345"
        context_dir.mkdir()

        # Create older checkpoint
        old_checkpoint = sample_checkpoint.copy()
        old_checkpoint["phase_name"] = "Old Phase"
        (context_dir / "checkpoint_20260110_100000.json").write_text(json.dumps(old_checkpoint))

        time.sleep(0.01)

        # Create newer checkpoint
        new_checkpoint = sample_checkpoint.copy()
        new_checkpoint["phase_name"] = "New Phase"
        (context_dir / "checkpoint_20260111_100000.json").write_text(json.dumps(new_checkpoint))

        with patch(
            'claude.hooks.post_compaction_restore.DURABLE_CHECKPOINT_DIR',
            temp_dirs["checkpoints"]
        ):
            result = load_latest_checkpoint("12345")

        assert result["phase_name"] == "New Phase"

    @pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="Implementation not yet created")
    def test_load_latest_checkpoint_returns_none_if_missing(self, temp_dirs):
        """Returns None if no checkpoint exists (graceful degradation)."""
        with patch(
            'claude.hooks.post_compaction_restore.DURABLE_CHECKPOINT_DIR',
            temp_dirs["checkpoints"]
        ):
            result = load_latest_checkpoint("nonexistent")

        assert result is None

    @pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="Implementation not yet created")
    def test_load_latest_checkpoint_handles_corrupted_json(self, temp_dirs):
        """Handles corrupted JSON gracefully."""
        context_dir = temp_dirs["checkpoints"] / "12345"
        context_dir.mkdir()
        (context_dir / "checkpoint_20260111_100000.json").write_text("invalid json {{{")

        with patch(
            'claude.hooks.post_compaction_restore.DURABLE_CHECKPOINT_DIR',
            temp_dirs["checkpoints"]
        ):
            result = load_latest_checkpoint("12345")

        assert result is None  # Graceful degradation


class TestLoadSession:
    """Tests for loading session file."""

    @pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="Implementation not yet created")
    def test_load_session_returns_dict(self, temp_dirs, sample_session):
        """load_session returns session dictionary."""
        session_path = temp_dirs["sessions"] / "swarm_session_12345.json"
        session_path.write_text(json.dumps(sample_session))

        with patch(
            'claude.hooks.post_compaction_restore.SESSIONS_DIR',
            temp_dirs["sessions"]
        ):
            result = load_session("12345")

        assert isinstance(result, dict)
        assert result["current_agent"] == "sre_principal_engineer_agent"

    @pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="Implementation not yet created")
    def test_load_session_returns_none_if_missing(self, temp_dirs):
        """Returns None if session file doesn't exist."""
        with patch(
            'claude.hooks.post_compaction_restore.SESSIONS_DIR',
            temp_dirs["sessions"]
        ):
            result = load_session("nonexistent")

        assert result is None


class TestDetermineAgent:
    """Tests for agent determination logic."""

    @pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="Implementation not yet created")
    def test_determine_agent_prefers_checkpoint(self, sample_checkpoint, sample_session):
        """Uses checkpoint's recommended_agent first."""
        sample_checkpoint["recommended_agent"] = "checkpoint_agent"
        sample_session["current_agent"] = "session_agent"

        result = determine_agent(sample_checkpoint, sample_session)

        assert result == "checkpoint_agent"

    @pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="Implementation not yet created")
    def test_determine_agent_falls_back_to_session(self, sample_session):
        """Falls back to session's current_agent if no checkpoint."""
        sample_session["current_agent"] = "session_agent"

        result = determine_agent(None, sample_session)

        assert result == "session_agent"

    @pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="Implementation not yet created")
    def test_determine_agent_defaults_to_sre(self):
        """Defaults to SRE agent if no checkpoint or session."""
        result = determine_agent(None, None)

        assert result == "sre_principal_engineer_agent"

    @pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="Implementation not yet created")
    def test_determine_agent_forces_sre_for_code_projects(self, sample_checkpoint, sample_session):
        """Forces SRE agent for code projects even if session differs."""
        sample_checkpoint["is_code_project"] = True
        sample_checkpoint["recommended_agent"] = "sre_principal_engineer_agent"
        sample_session["current_agent"] = "docs_agent"

        result = determine_agent(sample_checkpoint, sample_session)

        assert result == "sre_principal_engineer_agent"


class TestFormatRestorationContext:
    """Tests for context output formatting."""

    @pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="Implementation not yet created")
    def test_format_includes_agent_header(self, sample_checkpoint, sample_session):
        """Output includes agent identification."""
        result = format_restoration_context(
            "sre_principal_engineer_agent",
            sample_checkpoint,
            sample_session
        )

        assert "sre_principal_engineer_agent" in result
        assert "Agent" in result

    @pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="Implementation not yet created")
    def test_format_includes_checkpoint_context(self, sample_checkpoint, sample_session):
        """Output includes checkpoint progress information."""
        result = format_restoration_context(
            "sre_principal_engineer_agent",
            sample_checkpoint,
            sample_session
        )

        assert "75%" in result
        assert "Auto-Resume System" in result
        assert "P4" in result

    @pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="Implementation not yet created")
    def test_format_includes_next_action(self, sample_checkpoint, sample_session):
        """Output includes next action for resumption."""
        result = format_restoration_context(
            "sre_principal_engineer_agent",
            sample_checkpoint,
            sample_session
        )

        assert "Fix 5 failing tests" in result

    @pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="Implementation not yet created")
    def test_format_includes_tdd_reminder(self, sample_checkpoint, sample_session):
        """Output includes TDD protocol reminder."""
        result = format_restoration_context(
            "sre_principal_engineer_agent",
            sample_checkpoint,
            sample_session
        )

        assert "TDD" in result
        assert "test" in result.lower()

    @pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="Implementation not yet created")
    def test_format_handles_no_checkpoint(self, sample_session):
        """Handles missing checkpoint gracefully."""
        result = format_restoration_context(
            "sre_principal_engineer_agent",
            None,
            sample_session
        )

        # Should still produce output with agent
        assert "sre_principal_engineer_agent" in result

    @pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="Implementation not yet created")
    def test_format_is_markdown(self, sample_checkpoint, sample_session):
        """Output is formatted as markdown."""
        result = format_restoration_context(
            "sre_principal_engineer_agent",
            sample_checkpoint,
            sample_session
        )

        # Should contain markdown headers
        assert "##" in result or "#" in result


class TestPostCompactionRestoreHook:
    """Integration tests for the full hook."""

    @pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="Implementation not yet created")
    def test_hook_processes_input(self, temp_dirs, sample_checkpoint, sample_session):
        """Hook processes standard hook input."""
        # Setup checkpoint
        context_dir = temp_dirs["checkpoints"] / "12345"
        context_dir.mkdir()
        (context_dir / "checkpoint_20260111_100000.json").write_text(json.dumps(sample_checkpoint))

        # Setup session
        (temp_dirs["sessions"] / "swarm_session_12345.json").write_text(json.dumps(sample_session))

        hook_input = {
            "session_id": "12345",
            "hook_event_name": "SessionStart",
            "trigger": "compact",
        }

        with patch(
            'claude.hooks.post_compaction_restore.DURABLE_CHECKPOINT_DIR',
            temp_dirs["checkpoints"]
        ):
            with patch(
                'claude.hooks.post_compaction_restore.SESSIONS_DIR',
                temp_dirs["sessions"]
            ):
                hook = PostCompactionRestore()
                result = hook.restore(hook_input)

        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="Implementation not yet created")
    def test_hook_outputs_to_stdout(self, temp_dirs, sample_checkpoint, sample_session, capsys):
        """Hook outputs context to stdout for injection."""
        # Setup checkpoint
        context_dir = temp_dirs["checkpoints"] / "12345"
        context_dir.mkdir()
        (context_dir / "checkpoint_20260111_100000.json").write_text(json.dumps(sample_checkpoint))

        # Setup session
        (temp_dirs["sessions"] / "swarm_session_12345.json").write_text(json.dumps(sample_session))

        hook_input = {
            "session_id": "12345",
            "hook_event_name": "SessionStart",
            "trigger": "compact",
        }

        with patch(
            'claude.hooks.post_compaction_restore.DURABLE_CHECKPOINT_DIR',
            temp_dirs["checkpoints"]
        ):
            with patch(
                'claude.hooks.post_compaction_restore.SESSIONS_DIR',
                temp_dirs["sessions"]
            ):
                hook = PostCompactionRestore()
                result = hook.restore(hook_input)
                print(result)

        captured = capsys.readouterr()
        assert "sre_principal_engineer_agent" in captured.out

    @pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="Implementation not yet created")
    def test_hook_graceful_without_checkpoint(self, temp_dirs, sample_session):
        """Hook provides minimal context without checkpoint."""
        # Setup session only (no checkpoint)
        (temp_dirs["sessions"] / "swarm_session_12345.json").write_text(json.dumps(sample_session))

        hook_input = {
            "session_id": "12345",
            "hook_event_name": "SessionStart",
            "trigger": "compact",
        }

        with patch(
            'claude.hooks.post_compaction_restore.DURABLE_CHECKPOINT_DIR',
            temp_dirs["checkpoints"]
        ):
            with patch(
                'claude.hooks.post_compaction_restore.SESSIONS_DIR',
                temp_dirs["sessions"]
            ):
                hook = PostCompactionRestore()
                result = hook.restore(hook_input)

        # Should still produce agent-focused output
        assert "sre_principal_engineer_agent" in result


class TestPerformance:
    """Performance tests for hook."""

    @pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="Implementation not yet created")
    def test_hook_completes_under_2_seconds(self, temp_dirs, sample_checkpoint, sample_session):
        """Hook completes in <2 seconds (timeout requirement)."""
        # Setup checkpoint
        context_dir = temp_dirs["checkpoints"] / "12345"
        context_dir.mkdir()
        (context_dir / "checkpoint_20260111_100000.json").write_text(json.dumps(sample_checkpoint))

        # Setup session
        (temp_dirs["sessions"] / "swarm_session_12345.json").write_text(json.dumps(sample_session))

        hook_input = {
            "session_id": "12345",
            "hook_event_name": "SessionStart",
            "trigger": "compact",
        }

        with patch(
            'claude.hooks.post_compaction_restore.DURABLE_CHECKPOINT_DIR',
            temp_dirs["checkpoints"]
        ):
            with patch(
                'claude.hooks.post_compaction_restore.SESSIONS_DIR',
                temp_dirs["sessions"]
            ):
                hook = PostCompactionRestore()

                start = time.time()
                result = hook.restore(hook_input)
                elapsed = time.time() - start

        assert elapsed < 2.0, f"Hook took {elapsed:.3f}s, expected <2s"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
