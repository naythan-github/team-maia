"""
Tests for Repository Validator

Tests the RepositoryValidator class that validates current repository
matches session context to prevent cross-repo operations.

Sprint: SPRINT-001-REPO-SYNC
Story: 2.1 - Create RepositoryValidator Class
Phase: P0 - Test-First Design

Created: 2026-01-15
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import will fail initially (P0 - tests should fail)
from claude.tools.sre.repo_validator import RepositoryValidator, ValidationResult


class TestRepositoryValidator:
    """Test suite for RepositoryValidator."""

    def test_validator_passes_when_repo_matches(self):
        """
        Test validation passes when current repo matches session.

        Given: Session for team-maia with matching CWD
        When: validate_session_repo() called
        Then: Returns passed=True with no warnings
        """
        validator = RepositoryValidator()

        # Mock session with team-maia context
        session_data = {
            "repository": {
                "working_directory": "/Users/username/team-maia",
                "git_remote_url": "https://github.com/work-github/team-maia.git",
                "git_branch": "main"
            }
        }

        # Mock CWD to match
        with patch('pathlib.Path.cwd', return_value=Path('/Users/username/team-maia')):
            with patch('subprocess.run') as mock_run:
                # Mock both git remote and git branch
                def mock_subprocess(cmd, **kwargs):
                    if 'remote' in str(cmd):
                        return MagicMock(stdout="https://github.com/work-github/team-maia.git\n", returncode=0)
                    elif 'branch' in str(cmd):
                        return MagicMock(stdout="main\n", returncode=0)
                    return MagicMock(returncode=0)

                mock_run.side_effect = mock_subprocess

                result = validator.validate_session_repo(session_data)
                assert result.passed is True
                assert result.warnings == []

    def test_validator_fails_when_directory_mismatch(self):
        """
        Test validation fails when CWD doesn't match session.

        Given: Session for team-maia but CWD is personal maia
        When: validate_session_repo() called
        Then: Returns passed=False with directory mismatch reason
        """
        validator = RepositoryValidator()

        # Session for team-maia
        session_data = {
            "repository": {
                "working_directory": "/Users/username/team-maia",
                "git_remote_url": "https://github.com/work-github/team-maia.git"
            }
        }

        # But we're in personal maia
        with patch('pathlib.Path.cwd', return_value=Path('/Users/username/maia')):
            result = validator.validate_session_repo(session_data)
            assert result.passed is False
            assert 'directory mismatch' in result.reason.lower()

    def test_validator_fails_when_remote_url_mismatch(self):
        """
        Test validation fails when git remote URL doesn't match.

        Given: Session for team-maia but git remote is different
        When: validate_session_repo() called
        Then: Returns passed=False with remote URL mismatch reason
        """
        validator = RepositoryValidator()

        session_data = {
            "repository": {
                "working_directory": "/Users/username/team-maia",
                "git_remote_url": "https://github.com/work-github/team-maia.git"
            }
        }

        with patch('pathlib.Path.cwd', return_value=Path('/Users/username/team-maia')):
            with patch('subprocess.run') as mock_run:
                # Mock wrong remote URL
                mock_run.return_value = MagicMock(
                    stdout="https://github.com/personal-github/maia.git\n",
                    returncode=0
                )

                result = validator.validate_session_repo(session_data)
                assert result.passed is False
                assert 'remote url mismatch' in result.reason.lower()

    def test_validator_warns_when_branch_mismatch(self):
        """
        Test validation warns (not fails) when branch differs.

        Given: Session for main branch but currently on feature branch
        When: validate_session_repo() called
        Then: Returns passed=True with branch warning
        """
        validator = RepositoryValidator()

        session_data = {
            "repository": {
                "working_directory": "/Users/username/team-maia",
                "git_remote_url": "https://github.com/work-github/team-maia.git",
                "git_branch": "main"
            }
        }

        with patch('pathlib.Path.cwd', return_value=Path('/Users/username/team-maia')):
            with patch('subprocess.run') as mock_run:
                def mock_subprocess(cmd, **kwargs):
                    if 'remote' in str(cmd):
                        return MagicMock(stdout="https://github.com/work-github/team-maia.git\n", returncode=0)
                    elif 'branch' in str(cmd):
                        return MagicMock(stdout="feature-branch\n", returncode=0)
                    return MagicMock(returncode=0)

                mock_run.side_effect = mock_subprocess

                result = validator.validate_session_repo(session_data)
                assert result.passed is True  # Branch mismatch is warning only
                assert len(result.warnings) == 1
                assert 'branch' in result.warnings[0].lower()

    def test_validator_handles_legacy_sessions_without_repo(self):
        """
        Test validator passes for old sessions without repository field.

        Given: Old session format (no repository field)
        When: validate_session_repo() called
        Then: Returns passed=True with legacy session reason
        """
        validator = RepositoryValidator()

        # Old session format (no repository field)
        session_data = {
            "current_agent": "sre_principal_engineer_agent",
            "session_start": "2026-01-01T00:00:00Z"
        }

        result = validator.validate_session_repo(session_data)
        assert result.passed is True
        assert 'legacy session' in result.reason.lower()


class TestValidationResult:
    """Test suite for ValidationResult dataclass."""

    def test_validation_result_structure(self):
        """
        Test ValidationResult has required fields.

        Given: ValidationResult instantiated
        When: Fields accessed
        Then: Has passed, reason, warnings fields
        """
        result = ValidationResult(
            passed=True,
            reason="Test reason",
            warnings=["Warning 1"],
            current_directory=Path('/test'),
            current_remote="https://github.com/test/test.git",
            current_branch="main"
        )

        assert result.passed is True
        assert result.reason == "Test reason"
        assert len(result.warnings) == 1
        assert result.current_directory == Path('/test')
        assert result.current_remote == "https://github.com/test/test.git"
        assert result.current_branch == "main"
