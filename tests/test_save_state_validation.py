"""
Tests for save_state Repository Validation

Tests that save_state.py validates repository context before git operations.

Sprint: SPRINT-001-REPO-SYNC
Story: 4.1 - Add Repo Validation to save_state.py
Phase: P0 - Test-First Design

Created: 2026-01-15
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import json

from claude.tools.sre.save_state import SaveState
from claude.tools.sre.repo_validator import ValidationResult


class TestSaveStateValidation:
    """Test suite for save_state repository validation."""

    def test_save_state_validates_before_commit(self, tmp_path):
        """
        Test save_state validates repo before git operations.

        Given: Session file with repository metadata
        When: save_state executes
        Then: Validates current repo matches session
        """
        # Create mock session file
        session_file = tmp_path / "swarm_session_12345.json"
        session_data = {
            "current_agent": "sre_principal_engineer_agent",
            "repository": {
                "working_directory": str(tmp_path),
                "git_remote_url": "https://github.com/work-github/team-maia.git",
                "git_branch": "main"
            }
        }
        session_file.write_text(json.dumps(session_data))

        # Mock subprocess for git commands
        def mock_subprocess(cmd, **kwargs):
            if 'remote' in str(cmd):
                return MagicMock(stdout="https://github.com/work-github/team-maia.git\n", returncode=0)
            elif 'branch' in str(cmd):
                return MagicMock(stdout="main\n", returncode=0)
            return MagicMock(returncode=0)

        with patch('claude.hooks.swarm_auto_loader.get_session_file_path', return_value=session_file):
            with patch('pathlib.Path.cwd', return_value=tmp_path):
                with patch('subprocess.run', side_effect=mock_subprocess):
                    # Create SaveState instance
                    save_state = SaveState(maia_root=tmp_path)
                    result = save_state.validate_repository()

                    # Should pass validation
                    assert result.passed is True

    def test_save_state_blocks_on_validation_failure(self, tmp_path):
        """
        Test save_state blocks git operations on repo mismatch.

        Given: Session for team-maia but CWD is personal maia
        When: save_state attempts git operation
        Then: Raises error with repo mismatch details
        """
        # Create session for different repo
        session_file = tmp_path / "swarm_session_12345.json"
        session_data = {
            "current_agent": "sre_principal_engineer_agent",
            "repository": {
                "working_directory": "/Users/username/team-maia",
                "git_remote_url": "https://github.com/work-github/team-maia.git",
                "git_branch": "main"
            }
        }
        session_file.write_text(json.dumps(session_data))

        maia_root = Path('/Users/username/maia')

        with patch('claude.hooks.swarm_auto_loader.get_session_file_path', return_value=session_file):
            with pytest.raises(ValueError) as exc_info:
                save_state = SaveState(maia_root=maia_root)
                save_state.validate_repository()

            assert "validation failed" in str(exc_info.value).lower()

    def test_save_state_warns_on_branch_mismatch(self, tmp_path):
        """
        Test save_state warns (not fails) on branch mismatch.

        Given: Session for main branch but on feature branch
        When: save_state validates
        Then: Prints warning but allows operation
        """
        session_file = tmp_path / "swarm_session_12345.json"
        session_data = {
            "current_agent": "sre_principal_engineer_agent",
            "repository": {
                "working_directory": str(tmp_path),
                "git_remote_url": "https://github.com/work-github/team-maia.git",
                "git_branch": "main"
            }
        }
        session_file.write_text(json.dumps(session_data))

        # Mock git commands to return different branch
        def mock_subprocess(cmd, **kwargs):
            if 'remote' in str(cmd):
                return MagicMock(
                    stdout="https://github.com/work-github/team-maia.git\n",
                    returncode=0
                )
            elif 'branch' in str(cmd):
                return MagicMock(stdout="feature-x\n", returncode=0)
            return MagicMock(returncode=0)

        with patch('claude.hooks.swarm_auto_loader.get_session_file_path', return_value=session_file):
            with patch('pathlib.Path.cwd', return_value=tmp_path):
                with patch('subprocess.run', side_effect=mock_subprocess):
                    save_state = SaveState(maia_root=tmp_path)
                    result = save_state.validate_repository()

                    # Should pass with warnings
                    assert result.passed is True
                    assert len(result.warnings) > 0
                    assert any('branch' in w.lower() for w in result.warnings)

    def test_save_state_handles_legacy_sessions_without_repo(self, tmp_path):
        """
        Test save_state handles old sessions without repository field.

        Given: Old session format (no repository metadata)
        When: save_state validates
        Then: Skips validation (backward compat)
        """
        session_file = tmp_path / "swarm_session_12345.json"
        session_data = {
            "current_agent": "sre_principal_engineer_agent",
            "session_start": "2026-01-01T00:00:00Z"
        }
        session_file.write_text(json.dumps(session_data))

        with patch('claude.hooks.swarm_auto_loader.get_session_file_path', return_value=session_file):
            save_state = SaveState(maia_root=tmp_path)
            result = save_state.validate_repository()

            # Should pass (skip validation for legacy sessions)
            assert result.passed is True
            assert 'legacy' in result.reason.lower()

    def test_save_state_allows_override_flag(self, tmp_path):
        """
        Test save_state can override validation with explicit flag.

        Given: Repo mismatch AND override flag
        When: save_state validates with force=True
        Then: Allows operation with warning
        """
        session_file = tmp_path / "swarm_session_12345.json"
        session_data = {
            "current_agent": "sre_principal_engineer_agent",
            "repository": {
                "working_directory": "/Users/username/team-maia",
                "git_remote_url": "https://github.com/work-github/team-maia.git",
                "git_branch": "main"
            }
        }
        session_file.write_text(json.dumps(session_data))

        maia_root = Path('/Users/username/maia')

        with patch('claude.hooks.swarm_auto_loader.get_session_file_path', return_value=session_file):
            save_state = SaveState(maia_root=maia_root)

            # Should allow with force flag
            result = save_state.validate_repository(force=True)
            assert result.passed is True
            # Should have warning about forced bypass
            assert len(result.warnings) > 0

    def test_save_state_no_session_file_passes(self, tmp_path):
        """
        Test save_state handles missing session file gracefully.

        Given: No session file exists
        When: save_state validates
        Then: Passes (no session = no repo constraint)
        """
        session_file = tmp_path / "nonexistent_session.json"

        with patch('claude.hooks.swarm_auto_loader.get_session_file_path', return_value=session_file):
            save_state = SaveState(maia_root=tmp_path)
            result = save_state.validate_repository()

            # Should pass (no session = unrestricted)
            assert result.passed is True
            assert "no session file exists" in result.reason.lower()
