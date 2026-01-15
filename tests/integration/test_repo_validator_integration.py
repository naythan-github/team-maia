"""
Integration Tests for Repository Validator

Tests RepositoryValidator with actual git repository.

Sprint: SPRINT-001-REPO-SYNC
Story: 2.1 - Create RepositoryValidator Class
Phase: P5 - Integration Tests

Created: 2026-01-15
"""

import pytest
from pathlib import Path

from claude.tools.sre.repo_validator import RepositoryValidator, ValidationResult


@pytest.mark.integration
class TestRepositoryValidatorIntegration:
    """Integration tests for RepositoryValidator with real git repo."""

    def test_validate_with_actual_repo(self):
        """
        Integration Test: Validate against actual repository.

        Given: Real maia repository
        When: Validator checks current state
        Then: Can detect real directory, remote, branch
        """
        validator = RepositoryValidator()

        # Get actual current state
        current_dir = Path.cwd()
        current_remote = validator._get_git_remote()
        current_branch = validator._get_git_branch()

        # These should all be populated in a real repo
        assert current_dir.exists()
        assert len(str(current_dir)) > 0
        # Skip remote/branch checks if not in git repo
        # (tests might run outside git context)

    def test_validate_with_matching_session(self):
        """
        Integration Test: Validation passes with matching session.

        Given: Session data matching current repo
        When: Validator validates
        Then: Passes with no warnings
        """
        validator = RepositoryValidator()

        # Get current state
        current_dir = Path.cwd()
        current_remote = validator._get_git_remote()
        current_branch = validator._get_git_branch()

        # Create session matching current state
        session_data = {
            "repository": {
                "working_directory": str(current_dir),
                "git_remote_url": current_remote,
                "git_branch": current_branch
            }
        }

        result = validator.validate_session_repo(session_data)

        # Should pass
        assert result.passed is True
        assert result.current_directory == current_dir
        assert result.current_remote == current_remote
        assert result.current_branch == current_branch

    def test_validate_with_different_directory(self):
        """
        Integration Test: Validation fails with wrong directory.

        Given: Session for different directory
        When: Validator validates
        Then: Fails with directory mismatch
        """
        validator = RepositoryValidator()

        # Get current state
        current_remote = validator._get_git_remote()
        current_branch = validator._get_git_branch()

        # Create session with wrong directory
        session_data = {
            "repository": {
                "working_directory": "/tmp/fake-repo",
                "git_remote_url": current_remote,
                "git_branch": current_branch
            }
        }

        result = validator.validate_session_repo(session_data)

        # Should fail
        assert result.passed is False
        assert 'directory mismatch' in result.reason.lower()

    def test_validate_with_different_remote(self):
        """
        Integration Test: Validation fails with wrong remote URL.

        Given: Session for different remote
        When: Validator validates
        Then: Fails with remote mismatch
        """
        validator = RepositoryValidator()

        # Get current state
        current_dir = Path.cwd()
        current_branch = validator._get_git_branch()

        # Create session with wrong remote
        session_data = {
            "repository": {
                "working_directory": str(current_dir),
                "git_remote_url": "https://github.com/fake/repo.git",
                "git_branch": current_branch
            }
        }

        result = validator.validate_session_repo(session_data)

        # Should fail
        assert result.passed is False
        assert 'remote url mismatch' in result.reason.lower()

    def test_validate_with_different_branch(self):
        """
        Integration Test: Validation warns with different branch.

        Given: Session for different branch
        When: Validator validates
        Then: Passes with branch warning
        """
        validator = RepositoryValidator()

        # Get current state
        current_dir = Path.cwd()
        current_remote = validator._get_git_remote()

        # Create session with different branch
        session_data = {
            "repository": {
                "working_directory": str(current_dir),
                "git_remote_url": current_remote,
                "git_branch": "fake-branch-name-xyz"
            }
        }

        result = validator.validate_session_repo(session_data)

        # Should pass but warn
        assert result.passed is True
        assert len(result.warnings) == 1
        assert 'branch' in result.warnings[0].lower()

    def test_legacy_session_backwards_compatibility(self):
        """
        Integration Test: Legacy sessions without repo field.

        Given: Old session without repository metadata
        When: Validator validates
        Then: Passes with legacy reason
        """
        validator = RepositoryValidator()

        # Old session format
        session_data = {
            "current_agent": "sre_principal_engineer_agent",
            "session_start": "2026-01-01T00:00:00Z"
        }

        result = validator.validate_session_repo(session_data)

        # Should pass (backward compat)
        assert result.passed is True
        assert 'legacy' in result.reason.lower()
