"""
Repository Validator

Validates that current repository matches session context to prevent
cross-repo operations when working with multiple repositories.

Sprint: SPRINT-001-REPO-SYNC
Story: 2.1 - Create RepositoryValidator Class
Phase: P2 - Minimal Implementation

Created: 2026-01-15
"""

from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass, field
import subprocess


@dataclass
class ValidationResult:
    """Result of repository validation."""
    passed: bool
    reason: str
    warnings: List[str] = field(default_factory=list)
    current_directory: Optional[Path] = None
    current_remote: Optional[str] = None
    current_branch: Optional[str] = None


class RepositoryValidator:
    """
    Validates current repository against session context.

    Prevents cross-repo git operations by verifying:
    - Current working directory matches session
    - Git remote URL matches session
    - Git branch matches session (warning only)

    Usage:
        validator = RepositoryValidator()
        result = validator.validate_session_repo(session_data)

        if not result.passed:
            print(f"Validation failed: {result.reason}")

        for warning in result.warnings:
            print(f"Warning: {warning}")
    """

    def validate_session_repo(self, session_data: dict) -> ValidationResult:
        """
        Validate current repository matches session context.

        Args:
            session_data: Session JSON data containing repository metadata

        Returns:
            ValidationResult with passed status, reason, and warnings
        """
        # Handle legacy sessions without repository field
        if 'repository' not in session_data:
            return ValidationResult(
                passed=True,
                reason="Legacy session format (no repository field)",
                warnings=[],
                current_directory=Path.cwd(),
                current_remote=self._get_git_remote(),
                current_branch=self._get_git_branch()
            )

        repo_data = session_data['repository']
        warnings = []

        # Get current state
        current_dir = Path.cwd()
        current_remote = self._get_git_remote()
        current_branch = self._get_git_branch()

        # Check directory match
        session_dir = Path(repo_data['working_directory'])
        if current_dir != session_dir:
            return ValidationResult(
                passed=False,
                reason=f"Directory mismatch: current={current_dir}, session={session_dir}",
                warnings=warnings,
                current_directory=current_dir,
                current_remote=current_remote,
                current_branch=current_branch
            )

        # Check git remote URL match
        session_remote = repo_data['git_remote_url']
        if current_remote.strip() != session_remote.strip():
            return ValidationResult(
                passed=False,
                reason=f"Remote URL mismatch: current={current_remote}, session={session_remote}",
                warnings=warnings,
                current_directory=current_dir,
                current_remote=current_remote,
                current_branch=current_branch
            )

        # Check git branch (warning only, not failure)
        if 'git_branch' in repo_data:
            session_branch = repo_data['git_branch']
            if current_branch.strip() != session_branch.strip():
                warnings.append(
                    f"Branch mismatch: current={current_branch}, session={session_branch}"
                )

        # All validations passed
        return ValidationResult(
            passed=True,
            reason="Repository matches session context",
            warnings=warnings,
            current_directory=current_dir,
            current_remote=current_remote,
            current_branch=current_branch
        )

    def _get_git_remote(self) -> str:
        """
        Get current git remote URL.

        Returns:
            Git remote URL or empty string if not available
        """
        try:
            result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return ""
        except Exception:
            return ""

    def _get_git_branch(self) -> str:
        """
        Get current git branch name.

        Returns:
            Git branch name or empty string if not available
        """
        try:
            result = subprocess.run(
                ['git', 'branch', '--show-current'],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return ""
        except Exception:
            return ""
