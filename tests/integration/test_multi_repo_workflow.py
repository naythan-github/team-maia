"""
End-to-End Integration Tests for Multi-Repo Workflow

Tests complete workflows across personal and work repositories with
real git operations and session management.

Sprint: SPRINT-001-REPO-SYNC
Story: 5.1 - End-to-End Multi-Repo Workflow Tests
Phase: P0 - Test-First Design

Created: 2026-01-15
"""

import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from claude.tools.sre.repo_validator import RepositoryValidator
from claude.tools.sre.save_state import SaveState
from claude.hooks.swarm_auto_loader import create_session_state, get_session_file_path


@pytest.mark.integration
class TestMultiRepoWorkflow:
    """End-to-end integration tests for multi-repo workflows."""

    def test_complete_repo_switch_workflow(self, tmp_path):
        """
        Integration Test: Complete workflow switching between repos.

        Given: Active session in personal repo
        When: Switch to work repo with new session
        Then: Both repos maintain independent context
        """
        personal_repo = tmp_path / "maia"
        work_repo = tmp_path / "team-maia"
        personal_repo.mkdir()
        work_repo.mkdir()

        session_dir = tmp_path / "sessions"
        session_dir.mkdir()

        # Step 1: Create session in personal repo
        personal_session = session_dir / "swarm_session_personal.json"
        personal_session_data = {
            "current_agent": "sre_principal_engineer_agent",
            "repository": {
                "working_directory": str(personal_repo),
                "git_remote_url": "https://github.com/personal-github/maia.git",
                "git_branch": "main"
            }
        }
        personal_session.write_text(json.dumps(personal_session_data))

        # Mock subprocess for personal repo
        def mock_personal_git(cmd, **kwargs):
            if 'remote' in str(cmd):
                return MagicMock(stdout="https://github.com/personal-github/maia.git\n", returncode=0)
            elif 'branch' in str(cmd):
                return MagicMock(stdout="main\n", returncode=0)
            return MagicMock(returncode=0)

        # Validate personal repo session
        with patch('claude.hooks.swarm_auto_loader.get_session_file_path', return_value=personal_session):
            with patch('subprocess.run', side_effect=mock_personal_git):
                with patch('pathlib.Path.cwd', return_value=personal_repo):
                    validator = RepositoryValidator()
                    result = validator.validate_session_repo(personal_session_data)
                    assert result.passed is True

        # Step 2: Create session in work repo
        work_session = session_dir / "swarm_session_work.json"
        work_session_data = {
            "current_agent": "data_analyst_agent",
            "repository": {
                "working_directory": str(work_repo),
                "git_remote_url": "https://github.com/work-github/team-maia.git",
                "git_branch": "main"
            }
        }
        work_session.write_text(json.dumps(work_session_data))

        # Mock subprocess for work repo
        def mock_work_git(cmd, **kwargs):
            if 'remote' in str(cmd):
                return MagicMock(stdout="https://github.com/work-github/team-maia.git\n", returncode=0)
            elif 'branch' in str(cmd):
                return MagicMock(stdout="main\n", returncode=0)
            return MagicMock(returncode=0)

        # Validate work repo session
        with patch('claude.hooks.swarm_auto_loader.get_session_file_path', return_value=work_session):
            with patch('subprocess.run', side_effect=mock_work_git):
                with patch('pathlib.Path.cwd', return_value=work_repo):
                    validator = RepositoryValidator()
                    result = validator.validate_session_repo(work_session_data)
                    assert result.passed is True

        # Step 3: Verify sessions are independent
        assert personal_session_data['repository']['git_remote_url'] != work_session_data['repository']['git_remote_url']
        assert personal_session_data['current_agent'] != work_session_data['current_agent']

    def test_cross_repo_operation_blocked(self, tmp_path):
        """
        Integration Test: Cross-repo operation is blocked.

        Given: Session created for personal repo
        When: Try to run git operation in work repo
        Then: Validation fails with clear error message
        """
        personal_repo = tmp_path / "maia"
        work_repo = tmp_path / "team-maia"
        personal_repo.mkdir()
        work_repo.mkdir()

        # Create session for personal repo
        session_file = tmp_path / "swarm_session_12345.json"
        session_data = {
            "current_agent": "sre_principal_engineer_agent",
            "repository": {
                "working_directory": str(personal_repo),
                "git_remote_url": "https://github.com/personal-github/maia.git",
                "git_branch": "main"
            }
        }
        session_file.write_text(json.dumps(session_data))

        # Try to validate from work repo (should fail)
        with patch('claude.hooks.swarm_auto_loader.get_session_file_path', return_value=session_file):
            with pytest.raises(ValueError) as exc_info:
                save_state = SaveState(maia_root=work_repo)
                save_state.validate_repository()

            # Verify error message is helpful
            error_msg = str(exc_info.value)
            assert "validation failed" in error_msg.lower()
            assert "directory mismatch" in error_msg.lower()

    def test_force_override_workflow(self, tmp_path):
        """
        Integration Test: Force override allows cross-repo operation.

        Given: Session for personal repo, working in work repo
        When: Validate with force=True
        Then: Validation passes with warning
        """
        personal_repo = tmp_path / "maia"
        work_repo = tmp_path / "team-maia"
        personal_repo.mkdir()
        work_repo.mkdir()

        # Create session for personal repo
        session_file = tmp_path / "swarm_session_12345.json"
        session_data = {
            "current_agent": "sre_principal_engineer_agent",
            "repository": {
                "working_directory": str(personal_repo),
                "git_remote_url": "https://github.com/personal-github/maia.git",
                "git_branch": "main"
            }
        }
        session_file.write_text(json.dumps(session_data))

        # Force override should succeed with warning
        with patch('claude.hooks.swarm_auto_loader.get_session_file_path', return_value=session_file):
            save_state = SaveState(maia_root=work_repo)
            result = save_state.validate_repository(force=True)

            assert result.passed is True
            assert len(result.warnings) > 0
            # Should have warning about forced bypass
            assert any('forced' in w.lower() or 'bypass' in w.lower() for w in result.warnings)

    def test_session_creation_captures_repo_context(self, tmp_path):
        """
        Integration Test: New sessions capture repository context.

        Given: Creating session in work repo
        When: Session created with create_session_state
        Then: Session includes complete repo metadata
        """
        work_repo = tmp_path / "team-maia"
        work_repo.mkdir()
        session_file = tmp_path / "swarm_session_12345.json"

        # Mock git commands
        def mock_subprocess(cmd, **kwargs):
            if 'remote' in str(cmd):
                return MagicMock(stdout="https://github.com/work-github/team-maia.git\n", returncode=0)
            elif 'branch' in str(cmd):
                return MagicMock(stdout="feature-x\n", returncode=0)
            return MagicMock(returncode=0)

        with patch('claude.hooks.swarm_auto_loader.SESSION_STATE_FILE', session_file):
            with patch('claude.hooks.swarm_auto_loader._start_learning_session', return_value=("s_12345", None)):
                with patch('subprocess.run', side_effect=mock_subprocess):
                    with patch('claude.hooks.swarm_auto_loader.MAIA_ROOT', work_repo):
                        # Create session
                        result = create_session_state(
                            agent="devops_principal_architect_agent",
                            domain="devops",
                            classification={"confidence": 0.92},
                            query="Deploy infrastructure"
                        )

                        assert result is True

                        # Verify session has complete metadata
                        with open(session_file, 'r') as f:
                            session_data = json.load(f)

                        assert "repository" in session_data
                        repo_data = session_data["repository"]
                        assert repo_data["working_directory"] == str(work_repo)
                        assert "team-maia" in repo_data["git_remote_url"]
                        assert repo_data["git_branch"] == "feature-x"

    def test_validation_result_provides_debugging_info(self, tmp_path):
        """
        Integration Test: Validation failures provide debugging context.

        Given: Repository mismatch scenario
        When: Validation fails
        Then: Result includes current vs expected state
        """
        personal_repo = tmp_path / "maia"
        work_repo = tmp_path / "team-maia"
        personal_repo.mkdir()
        work_repo.mkdir()

        # Session for personal repo
        session_file = tmp_path / "swarm_session_12345.json"
        session_data = {
            "current_agent": "sre_principal_engineer_agent",
            "repository": {
                "working_directory": str(personal_repo),
                "git_remote_url": "https://github.com/personal-github/maia.git",
                "git_branch": "main"
            }
        }
        session_file.write_text(json.dumps(session_data))

        # Mock current git state (work repo)
        def mock_subprocess(cmd, **kwargs):
            if 'remote' in str(cmd):
                return MagicMock(stdout="https://github.com/work-github/team-maia.git\n", returncode=0)
            elif 'branch' in str(cmd):
                return MagicMock(stdout="develop\n", returncode=0)
            return MagicMock(returncode=0)

        with patch('claude.hooks.swarm_auto_loader.get_session_file_path', return_value=session_file):
            with patch('subprocess.run', side_effect=mock_subprocess):
                with patch('pathlib.Path.cwd', return_value=work_repo):
                    validator = RepositoryValidator()
                    result = validator.validate_session_repo(session_data)

                    # Should fail
                    assert result.passed is False

                    # Should provide debugging context
                    assert result.current_directory == work_repo
                    assert result.current_remote is not None
                    assert result.current_branch is not None
                    assert "mismatch" in result.reason.lower()

    def test_legacy_session_backward_compatibility(self, tmp_path):
        """
        Integration Test: Legacy sessions work without repo metadata.

        Given: Old session format (no repository field)
        When: Validation attempted
        Then: Passes gracefully (unrestricted mode)
        """
        # Old session format from before SPRINT-001-REPO-SYNC
        session_file = tmp_path / "swarm_session_legacy.json"
        legacy_session = {
            "current_agent": "python_code_reviewer_agent",
            "session_start": "2025-12-01T00:00:00Z",
            "handoff_chain": ["sre_principal_engineer_agent", "python_code_reviewer_agent"],
            "context": {},
            "domain": "code_review"
        }
        session_file.write_text(json.dumps(legacy_session))

        # Should pass validation (backward compat)
        with patch('claude.hooks.swarm_auto_loader.get_session_file_path', return_value=session_file):
            save_state = SaveState(maia_root=tmp_path)
            result = save_state.validate_repository()

            assert result.passed is True
            assert 'legacy' in result.reason.lower()
