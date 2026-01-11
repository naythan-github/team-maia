#!/usr/bin/env python3
"""
Tests for Durable Checkpoint System
Phase 264: Auto-Resume System for Compaction Survival

TDD Phase 3: Tests written BEFORE/ALONGSIDE implementation

Test Coverage:
- ProjectState.to_json_dict() - JSON serialization
- CheckpointGenerator.save_durable_checkpoint() - Durable storage
- CheckpointGenerator._cleanup_old_durable_checkpoints() - Cleanup
- Pre-compaction auto-checkpoint integration

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

from claude.tools.sre.checkpoint import (
    CheckpointGenerator,
    ProjectState,
    DURABLE_CHECKPOINT_DIR,
)


@pytest.fixture
def temp_checkpoint_dir():
    """Create temporary checkpoint directory."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_project_state():
    """Create sample ProjectState for testing."""
    return ProjectState(
        modified_files=["file1.py", "file2.py"],
        staged_files=["file3.py"],
        new_files=["file4.py"],
        deleted_files=[],
        current_branch="main",
        last_commit="abc123 feat: add feature",
        tests_passing=10,
        tests_total=12,
        test_details="10 passed, 2 failed",
        current_agent="sre_principal_engineer_agent",
        context_id="12345",
        session_start="2026-01-11T10:00:00Z",
        domain="sre",
        phase_number=264,
        phase_name="Auto-Resume System",
        percent_complete=50,
        tdd_phase="P4",
    )


class TestProjectStateToJsonDict:
    """Tests for ProjectState.to_json_dict() method."""

    def test_to_json_dict_returns_dict(self, sample_project_state):
        """to_json_dict returns a dictionary."""
        result = sample_project_state.to_json_dict()
        assert isinstance(result, dict)

    def test_to_json_dict_contains_required_fields(self, sample_project_state):
        """to_json_dict contains all required fields for auto-restore."""
        result = sample_project_state.to_json_dict()

        required_fields = [
            "context_id",
            "created_at",
            "phase_number",
            "phase_name",
            "percent_complete",
            "tdd_phase",
            "recommended_agent",
            "current_agent",
            "domain",
            "tests_passing",
            "tests_total",
            "current_branch",
            "last_commit",
            "modified_files",
            "is_code_project",
            "next_action",
        ]

        for field in required_fields:
            assert field in result, f"Missing required field: {field}"

    def test_to_json_dict_created_at_is_iso_format(self, sample_project_state):
        """created_at is in ISO format."""
        result = sample_project_state.to_json_dict()

        # Should not raise
        datetime.fromisoformat(result["created_at"])

    def test_to_json_dict_limits_file_lists_to_20(self, sample_project_state):
        """File lists are limited to 20 entries to prevent huge JSON."""
        sample_project_state.modified_files = [f"file_{i}.py" for i in range(50)]
        sample_project_state.staged_files = [f"staged_{i}.py" for i in range(30)]

        result = sample_project_state.to_json_dict()

        assert len(result["modified_files"]) == 20
        assert len(result["staged_files"]) == 20

    def test_to_json_dict_is_json_serializable(self, sample_project_state):
        """Result can be serialized to JSON without errors."""
        result = sample_project_state.to_json_dict()

        # Should not raise
        json_str = json.dumps(result)
        assert len(json_str) > 0

    def test_to_json_dict_recommended_agent_for_code_project(self, sample_project_state):
        """recommended_agent is SRE for code projects."""
        result = sample_project_state.to_json_dict()

        assert result["is_code_project"] == True
        assert result["recommended_agent"] == "sre_principal_engineer_agent"

    def test_to_json_dict_next_action_suggests_fix_tests(self, sample_project_state):
        """next_action suggests fixing tests when tests are failing."""
        # 10/12 passing means 2 failing
        result = sample_project_state.to_json_dict()

        assert "Fix 2 failing tests" in result["next_action"]


class TestCheckpointGeneratorDurableCheckpoint:
    """Tests for CheckpointGenerator.save_durable_checkpoint() method."""

    def test_save_durable_checkpoint_creates_directory(
        self, temp_checkpoint_dir, sample_project_state
    ):
        """save_durable_checkpoint creates context-specific directory."""
        generator = CheckpointGenerator()

        with patch.object(generator, 'maia_root', temp_checkpoint_dir):
            with patch(
                'claude.tools.sre.checkpoint.DURABLE_CHECKPOINT_DIR',
                temp_checkpoint_dir / "checkpoints"
            ):
                result = generator.save_durable_checkpoint(sample_project_state)

                context_dir = temp_checkpoint_dir / "checkpoints" / sample_project_state.context_id
                assert context_dir.exists()

    def test_save_durable_checkpoint_creates_json_file(
        self, temp_checkpoint_dir, sample_project_state
    ):
        """save_durable_checkpoint creates JSON file."""
        generator = CheckpointGenerator()

        with patch(
            'claude.tools.sre.checkpoint.DURABLE_CHECKPOINT_DIR',
            temp_checkpoint_dir
        ):
            result = generator.save_durable_checkpoint(sample_project_state)

            assert result is not None
            assert result.suffix == ".json"
            assert result.exists()

    def test_save_durable_checkpoint_json_is_valid(
        self, temp_checkpoint_dir, sample_project_state
    ):
        """Saved JSON file contains valid JSON."""
        generator = CheckpointGenerator()

        with patch(
            'claude.tools.sre.checkpoint.DURABLE_CHECKPOINT_DIR',
            temp_checkpoint_dir
        ):
            result = generator.save_durable_checkpoint(sample_project_state)

            # Should not raise
            with open(result) as f:
                data = json.load(f)

            assert data["context_id"] == sample_project_state.context_id

    def test_save_durable_checkpoint_saves_markdown_when_provided(
        self, temp_checkpoint_dir, sample_project_state
    ):
        """Saves markdown file when content is provided."""
        generator = CheckpointGenerator()
        markdown = "# Test Checkpoint\n\nThis is a test."

        with patch(
            'claude.tools.sre.checkpoint.DURABLE_CHECKPOINT_DIR',
            temp_checkpoint_dir
        ):
            result = generator.save_durable_checkpoint(
                sample_project_state,
                markdown_content=markdown
            )

            md_path = result.with_suffix('.md')
            assert md_path.exists()
            assert md_path.read_text() == markdown

    def test_save_durable_checkpoint_returns_none_on_error(
        self, temp_checkpoint_dir, sample_project_state
    ):
        """Returns None on error (graceful degradation)."""
        generator = CheckpointGenerator()

        # Use a path that can't be written
        with patch(
            'claude.tools.sre.checkpoint.DURABLE_CHECKPOINT_DIR',
            Path("/nonexistent/path/that/cannot/be/created")
        ):
            result = generator.save_durable_checkpoint(sample_project_state)

            assert result is None  # Graceful degradation

    def test_save_durable_checkpoint_uses_atomic_write(
        self, temp_checkpoint_dir, sample_project_state
    ):
        """Uses atomic write pattern (temp file + rename)."""
        generator = CheckpointGenerator()

        with patch(
            'claude.tools.sre.checkpoint.DURABLE_CHECKPOINT_DIR',
            temp_checkpoint_dir
        ):
            # No .tmp files should remain after successful save
            result = generator.save_durable_checkpoint(sample_project_state)

            tmp_files = list(temp_checkpoint_dir.glob("**/*.tmp"))
            assert len(tmp_files) == 0


class TestCheckpointCleanup:
    """Tests for _cleanup_old_durable_checkpoints() method."""

    def test_cleanup_keeps_recent_checkpoints(self, temp_checkpoint_dir):
        """Keeps the N most recent checkpoints."""
        generator = CheckpointGenerator()
        context_dir = temp_checkpoint_dir / "12345"
        context_dir.mkdir(parents=True)

        # Create 3 checkpoint files
        for i in range(3):
            (context_dir / f"checkpoint_20260111_{i:02d}0000.json").touch()
            time.sleep(0.01)  # Ensure different mtimes

        generator._cleanup_old_durable_checkpoints(context_dir, keep=5)

        # All 3 should still exist (less than keep=5)
        remaining = list(context_dir.glob("*.json"))
        assert len(remaining) == 3

    def test_cleanup_removes_old_checkpoints(self, temp_checkpoint_dir):
        """Removes checkpoints beyond the keep limit."""
        generator = CheckpointGenerator()
        context_dir = temp_checkpoint_dir / "12345"
        context_dir.mkdir(parents=True)

        # Create 7 checkpoint files
        for i in range(7):
            (context_dir / f"checkpoint_20260111_{i:02d}0000.json").touch()
            time.sleep(0.01)  # Ensure different mtimes

        generator._cleanup_old_durable_checkpoints(context_dir, keep=5)

        # Only 5 should remain
        remaining = list(context_dir.glob("*.json"))
        assert len(remaining) == 5

    def test_cleanup_also_removes_corresponding_md_files(self, temp_checkpoint_dir):
        """Also removes corresponding .md files when removing .json."""
        generator = CheckpointGenerator()
        context_dir = temp_checkpoint_dir / "12345"
        context_dir.mkdir(parents=True)

        # Create 7 checkpoint pairs (json + md)
        for i in range(7):
            (context_dir / f"checkpoint_20260111_{i:02d}0000.json").touch()
            (context_dir / f"checkpoint_20260111_{i:02d}0000.md").touch()
            time.sleep(0.01)

        generator._cleanup_old_durable_checkpoints(context_dir, keep=5)

        # Only 5 of each should remain
        remaining_json = list(context_dir.glob("*.json"))
        remaining_md = list(context_dir.glob("*.md"))
        assert len(remaining_json) == 5
        assert len(remaining_md) == 5

    def test_cleanup_handles_empty_directory(self, temp_checkpoint_dir):
        """Handles empty directory gracefully."""
        generator = CheckpointGenerator()
        context_dir = temp_checkpoint_dir / "12345"
        context_dir.mkdir(parents=True)

        # Should not raise
        generator._cleanup_old_durable_checkpoints(context_dir, keep=5)

    def test_cleanup_handles_nonexistent_directory(self, temp_checkpoint_dir):
        """Handles nonexistent directory gracefully."""
        generator = CheckpointGenerator()
        nonexistent = temp_checkpoint_dir / "nonexistent"

        # Should not raise
        generator._cleanup_old_durable_checkpoints(nonexistent, keep=5)


class TestDurableCheckpointConstant:
    """Tests for DURABLE_CHECKPOINT_DIR constant."""

    def test_durable_checkpoint_dir_is_in_home(self):
        """DURABLE_CHECKPOINT_DIR is in user's home directory."""
        assert str(DURABLE_CHECKPOINT_DIR).startswith(str(Path.home()))

    def test_durable_checkpoint_dir_is_under_maia(self):
        """DURABLE_CHECKPOINT_DIR is under .maia directory."""
        assert ".maia" in str(DURABLE_CHECKPOINT_DIR)

    def test_durable_checkpoint_dir_ends_with_checkpoints(self):
        """DURABLE_CHECKPOINT_DIR ends with 'checkpoints'."""
        assert DURABLE_CHECKPOINT_DIR.name == "checkpoints"


class TestSaveCheckpointIntegration:
    """Integration tests for save_checkpoint calling save_durable_checkpoint."""

    def test_save_checkpoint_calls_durable_save(
        self, temp_checkpoint_dir, sample_project_state
    ):
        """save_checkpoint also saves to durable location."""
        generator = CheckpointGenerator()
        generator.checkpoint_dir = temp_checkpoint_dir

        with patch.object(generator, 'save_durable_checkpoint') as mock_durable:
            content = "# Test Checkpoint"
            generator.save_checkpoint(content, sample_project_state)

            mock_durable.assert_called_once()

    def test_save_checkpoint_continues_on_durable_failure(
        self, temp_checkpoint_dir, sample_project_state
    ):
        """save_checkpoint continues even if durable save fails."""
        generator = CheckpointGenerator()
        generator.checkpoint_dir = temp_checkpoint_dir

        with patch.object(generator, 'save_durable_checkpoint', side_effect=Exception("Test error")):
            # Should not raise
            content = "# Test Checkpoint"
            result = generator.save_checkpoint(content, sample_project_state)

            # Primary checkpoint should still be saved
            assert result.exists()


class TestPreCompactionCheckpointIntegration:
    """Tests for pre-compaction auto-checkpoint in PreCompactionHook."""

    def test_pre_compaction_hook_saves_checkpoint(self, temp_checkpoint_dir):
        """PreCompactionHook saves checkpoint during processing."""
        from claude.hooks.pre_compaction_learning_capture import PreCompactionHook

        with patch(
            'claude.tools.sre.checkpoint.DURABLE_CHECKPOINT_DIR',
            temp_checkpoint_dir
        ):
            hook = PreCompactionHook()

            # Mock the checkpoint generator to verify it's called
            with patch.object(hook.checkpoint_generator, 'save_durable_checkpoint') as mock_save:
                hook._save_pre_compaction_checkpoint("test_context")

                mock_save.assert_called_once()

    def test_pre_compaction_checkpoint_is_non_blocking(self, temp_checkpoint_dir):
        """Pre-compaction checkpoint failures don't block the hook."""
        from claude.hooks.pre_compaction_learning_capture import PreCompactionHook

        hook = PreCompactionHook()

        # Force an error in checkpoint saving
        with patch.object(
            hook.checkpoint_generator, 'gather_state',
            side_effect=Exception("Test error")
        ):
            # Should not raise
            hook._save_pre_compaction_checkpoint("test_context")

    def test_pre_compaction_sets_auto_checkpoint_metadata(self, temp_checkpoint_dir):
        """Pre-compaction checkpoint sets appropriate metadata."""
        from claude.hooks.pre_compaction_learning_capture import PreCompactionHook

        with patch(
            'claude.tools.sre.checkpoint.DURABLE_CHECKPOINT_DIR',
            temp_checkpoint_dir
        ):
            hook = PreCompactionHook()

            with patch.object(hook.checkpoint_generator, 'save_durable_checkpoint') as mock_save:
                # Mock gather_state to return a predictable state
                mock_state = MagicMock()
                with patch.object(
                    hook.checkpoint_generator, 'gather_state',
                    return_value=mock_state
                ):
                    hook._save_pre_compaction_checkpoint("test_context")

                    # Verify metadata was set
                    assert mock_state.phase_name == "Pre-compaction auto-checkpoint"
                    assert mock_state.percent_complete == 50
                    assert mock_state.tdd_phase == "P4"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
