"""
Tests for Session Repository Metadata

Tests that session files capture repository context on creation.

Sprint: SPRINT-001-REPO-SYNC
Story: 3.1 - Update Session Manager with Repository Tracking
Phase: P0 - Test-First Design

Created: 2026-01-15
"""

import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess

# Import will be enhanced in P2
from claude.hooks.swarm_auto_loader import create_session_state, get_session_file_path


class TestSessionRepositoryMetadata:
    """Test suite for session repository metadata capture."""

    def test_session_captures_repository_metadata(self, tmp_path):
        """
        Test session creation captures repository context.

        Given: Creating new session in team-maia repo
        When: create_session_state() called
        Then: Session file includes repository metadata
        """
        # Mock session file location
        test_session_file = tmp_path / "swarm_session_12345.json"

        # Mock subprocess calls for git commands
        def mock_subprocess(cmd, **kwargs):
            if 'remote' in str(cmd):
                return MagicMock(
                    stdout="https://github.com/work-github/team-maia.git\n",
                    returncode=0
                )
            elif 'branch' in str(cmd):
                return MagicMock(stdout="main\n", returncode=0)
            return MagicMock(returncode=0)

        maia_root = Path('/Users/username/team-maia')

        with patch('claude.hooks.swarm_auto_loader.SESSION_STATE_FILE', test_session_file):
            with patch('claude.hooks.swarm_auto_loader._start_learning_session', return_value=("s_12345", None)):
                with patch('subprocess.run', side_effect=mock_subprocess):
                    with patch('claude.hooks.swarm_auto_loader.MAIA_ROOT', maia_root):
                        # Create session
                        result = create_session_state(
                            agent="sre_principal_engineer_agent",
                            domain="sre",
                            classification={"confidence": 0.85},
                            query="Test query"
                        )

                        assert result is True

                        # Verify session file has repository metadata
                        assert test_session_file.exists()

                        with open(test_session_file, 'r') as f:
                            session_data = json.load(f)

                        # Check repository metadata
                        assert "repository" in session_data
                        repo_data = session_data["repository"]

                        assert repo_data["working_directory"] == str(Path('/Users/username/team-maia'))
                        assert repo_data["git_remote_url"] == "https://github.com/work-github/team-maia.git"
                        assert repo_data["git_branch"] == "main"

    def test_session_handles_non_git_directory(self, tmp_path):
        """
        Test session creation in non-git directory.

        Given: Creating session in directory without git
        When: create_session_state() called
        Then: Session includes directory but no git metadata
        """
        test_session_file = tmp_path / "swarm_session_12345.json"

        # Mock git commands failing (not a git repo)
        def mock_subprocess_fail(cmd, **kwargs):
            return MagicMock(stdout="", returncode=128)

        maia_root = Path('/Users/username/non-git-dir')

        with patch('claude.hooks.swarm_auto_loader.SESSION_STATE_FILE', test_session_file):
            with patch('claude.hooks.swarm_auto_loader._start_learning_session', return_value=("s_12345", None)):
                with patch('subprocess.run', side_effect=mock_subprocess_fail):
                    with patch('claude.hooks.swarm_auto_loader.MAIA_ROOT', maia_root):
                        result = create_session_state(
                            agent="sre_principal_engineer_agent",
                            domain="sre",
                            classification={"confidence": 0.85},
                            query="Test query"
                        )

                        assert result is True

                        with open(test_session_file, 'r') as f:
                            session_data = json.load(f)

                        # Should still have repository field with directory
                        assert "repository" in session_data
                        repo_data = session_data["repository"]

                        assert repo_data["working_directory"] == str(Path('/Users/username/non-git-dir'))
                        # Git fields should be empty or None
                        assert repo_data.get("git_remote_url") in ["", None]
                        assert repo_data.get("git_branch") in ["", None]

    def test_session_preserves_repo_on_update(self, tmp_path):
        """
        Test session update preserves repository metadata.

        Given: Existing session with repository metadata
        When: Session updated (handoff)
        Then: Repository metadata preserved
        """
        test_session_file = tmp_path / "swarm_session_12345.json"

        # Create initial session
        initial_session = {
            "current_agent": "sre_principal_engineer_agent",
            "session_start": "2026-01-15T00:00:00Z",
            "handoff_chain": ["sre_principal_engineer_agent"],
            "context": {},
            "domain": "sre",
            "query": "Initial query",
            "repository": {
                "working_directory": "/Users/username/team-maia",
                "git_remote_url": "https://github.com/work-github/team-maia.git",
                "git_branch": "main"
            }
        }

        test_session_file.write_text(json.dumps(initial_session))

        # Mock subprocess for git commands
        def mock_subprocess(cmd, **kwargs):
            if 'remote' in str(cmd):
                return MagicMock(
                    stdout="https://github.com/work-github/team-maia.git\n",
                    returncode=0
                )
            elif 'branch' in str(cmd):
                return MagicMock(stdout="main\n", returncode=0)
            return MagicMock(returncode=0)

        maia_root = Path('/Users/username/team-maia')

        with patch('claude.hooks.swarm_auto_loader.SESSION_STATE_FILE', test_session_file):
            with patch('claude.hooks.swarm_auto_loader._start_learning_session', return_value=("s_12345", None)):
                with patch('subprocess.run', side_effect=mock_subprocess):
                    with patch('claude.hooks.swarm_auto_loader.MAIA_ROOT', maia_root):
                        # Update session (handoff to new agent)
                        result = create_session_state(
                            agent="python_code_reviewer_agent",
                            domain="code_review",
                            classification={"confidence": 0.90},
                            query="Review code"
                        )

                        assert result is True

                        with open(test_session_file, 'r') as f:
                            session_data = json.load(f)

                        # Repository metadata should be preserved/updated
                        assert "repository" in session_data
                        repo_data = session_data["repository"]

                        assert repo_data["working_directory"] == "/Users/username/team-maia"
                        assert repo_data["git_remote_url"] == "https://github.com/work-github/team-maia.git"
                        assert repo_data["git_branch"] == "main"

    def test_repo_metadata_uses_get_maia_root(self, tmp_path):
        """
        Test repository detection uses get_maia_root() for consistency.

        Given: Session creation in deep subdirectory
        When: create_session_state() called
        Then: Repository path uses MAIA_ROOT (not CWD)
        """
        test_session_file = tmp_path / "swarm_session_12345.json"
        maia_root = Path('/Users/username/team-maia')

        def mock_subprocess(cmd, **kwargs):
            if 'remote' in str(cmd):
                return MagicMock(
                    stdout="https://github.com/work-github/team-maia.git\n",
                    returncode=0
                )
            elif 'branch' in str(cmd):
                return MagicMock(stdout="feature-x\n", returncode=0)
            return MagicMock(returncode=0)

        with patch('claude.hooks.swarm_auto_loader.SESSION_STATE_FILE', test_session_file):
            with patch('claude.hooks.swarm_auto_loader._start_learning_session', return_value=("s_12345", None)):
                with patch('subprocess.run', side_effect=mock_subprocess):
                    with patch('claude.hooks.swarm_auto_loader.MAIA_ROOT', maia_root):
                        with patch('pathlib.Path.cwd', return_value=maia_root / 'claude' / 'tools'):
                            result = create_session_state(
                                agent="sre_principal_engineer_agent",
                                domain="sre",
                                classification={"confidence": 0.85},
                                query="Test query"
                            )

                            assert result is True

                            with open(test_session_file, 'r') as f:
                                session_data = json.load(f)

                            # Should use MAIA_ROOT, not deep CWD
                            repo_data = session_data["repository"]
                            assert repo_data["working_directory"] == str(maia_root)
