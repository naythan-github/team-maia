#!/usr/bin/env python3
"""
Maia Contribution Reviewer - Defense in Depth Quality Gate

Validates contributions meet security and quality standards.
Runs locally (pre-push) and in CI.

Usage:
    python3 contribution_reviewer.py --local   # Pre-push (staged files)
    python3 contribution_reviewer.py --ci      # CI mode (vs main branch)

Author: DevOps Principal Architect Agent
Date: 2026-01-03
Status: Production
"""

import argparse
import ast
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

# Resolve MAIA_ROOT
MAIA_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class CheckResult:
    """Result of a single check."""
    name: str
    passed: bool
    message: str
    severity: str = "error"  # error, warning, info
    files: Optional[List[str]] = None


class ContributionReviewer:
    """
    Multi-layer contribution validation.

    Checks:
    1. No secrets (API keys, passwords, private keys)
    2. No personal data (usernames, home paths)
    3. No hardcoded paths (/Users/*, /home/*)
    4. File locations correct (new tools in experimental/)
    5. Naming conventions (no _v2, _new, _backup)
    6. Tests exist for new tools
    7. Docstrings present in Python files
    """

    # Patterns that indicate secrets
    SECRET_PATTERNS = [
        r'(api_key|api-key)\s*[=:]\s*["\'][A-Za-z0-9+/=_-]{20,}["\']',
        r'(secret|secret_key)\s*[=:]\s*["\'][A-Za-z0-9+/=_-]{16,}["\']',
        r'(password|passwd)\s*[=:]\s*["\'][^"\']{8,}["\']',
        r'(token|auth_token|access_token)\s*[=:]\s*["\'][A-Za-z0-9+/=_-]{20,}["\']',
        r'-----BEGIN\s+(RSA\s+|OPENSSH\s+)?PRIVATE\s+KEY-----',
        r'sk-ant-api[a-zA-Z0-9-_]{20,}',  # Anthropic
        r'sk-[a-zA-Z0-9]{48}',  # OpenAI
        r'ghp_[a-zA-Z0-9]{36}',  # GitHub PAT
        r'AKIA[0-9A-Z]{16}',  # AWS Access Key
    ]

    # Personal data patterns
    PERSONAL_PATTERNS = [
        r'naythandawe',
        r'naythan',
        r'/Users/naythan',
        r'/home/naythan',
        r'nd25@',  # Email prefix
    ]

    # Hardcoded path patterns
    PATH_PATTERNS = [
        r'["\']/Users/[a-zA-Z]+/',
        r'["\']/home/[a-zA-Z]+/',
        r'OneDrive-[A-Z]+',
        r'Library/CloudStorage',
        r'Library/Mobile Documents',
    ]

    # Bad naming patterns
    BAD_NAME_PATTERNS = [
        r'_v\d+\.',
        r'_new\.',
        r'_old\.',
        r'_backup\.',
        r'_copy\.',
        r'_temp\.',
        r'_test\.',  # Should be test_*.py not *_test.py for tools
    ]

    # Allowlist patterns (don't flag these)
    ALLOWLIST_PATTERNS = [
        r'test_',
        r'# Example',
        r'\.example',
        r'CODEOWNERS',
        r'CONTRIBUTING',
        r'getenv',
        r'environ\[',
        r'os\.environ',
    ]

    def __init__(self, ci_mode: bool = False, verbose: bool = False):
        self.ci_mode = ci_mode
        self.verbose = verbose
        self.results: List[CheckResult] = []

    def get_changed_files(self) -> List[Path]:
        """Get list of changed files based on mode."""
        try:
            if self.ci_mode:
                # Compare to main branch
                cmd = ["git", "diff", "--name-only", "origin/main..HEAD"]
            else:
                # Staged files only
                cmd = ["git", "diff", "--cached", "--name-only"]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=MAIA_ROOT
            )
            files = [Path(f) for f in result.stdout.strip().split("\n") if f]
            return files
        except Exception as e:
            print(f"⚠️ Could not get changed files: {e}")
            return []

    def _is_allowlisted(self, line: str) -> bool:
        """Check if line matches allowlist patterns."""
        return any(re.search(p, line, re.IGNORECASE) for p in self.ALLOWLIST_PATTERNS)

    def _read_file_safe(self, filepath: Path) -> Optional[str]:
        """Safely read file contents."""
        full_path = MAIA_ROOT / filepath
        if not full_path.exists():
            return None
        try:
            return full_path.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            return None

    # ───────────────────────────────────────────────────────────────
    # Check 1: No Secrets
    # ───────────────────────────────────────────────────────────────
    def check_no_secrets(self, files: List[Path]) -> CheckResult:
        """Detect hardcoded secrets."""
        violations = []

        for filepath in files:
            if filepath.suffix not in ['.py', '.md', '.yml', '.yaml', '.json', '.sh']:
                continue

            content = self._read_file_safe(filepath)
            if not content:
                continue

            for i, line in enumerate(content.split('\n'), 1):
                if self._is_allowlisted(line):
                    continue

                for pattern in self.SECRET_PATTERNS:
                    if re.search(pattern, line, re.IGNORECASE):
                        violations.append(f"{filepath}:{i}")
                        break

        if violations:
            return CheckResult(
                name="No Secrets",
                passed=False,
                message=f"Potential secrets detected in {len(violations)} location(s)",
                severity="error",
                files=violations[:5]  # Show first 5
            )
        return CheckResult(
            name="No Secrets",
            passed=True,
            message="No secrets detected"
        )

    # ───────────────────────────────────────────────────────────────
    # Check 2: No Personal Data
    # ───────────────────────────────────────────────────────────────
    def check_no_personal_data(self, files: List[Path]) -> CheckResult:
        """Detect personal identifiers."""
        violations = []

        for filepath in files:
            # Skip CODEOWNERS (needs real usernames)
            if 'CODEOWNERS' in str(filepath):
                continue

            content = self._read_file_safe(filepath)
            if not content:
                continue

            for i, line in enumerate(content.split('\n'), 1):
                if self._is_allowlisted(line):
                    continue

                for pattern in self.PERSONAL_PATTERNS:
                    if re.search(pattern, line, re.IGNORECASE):
                        violations.append(f"{filepath}:{i}")
                        break

        if violations:
            return CheckResult(
                name="No Personal Data",
                passed=False,
                message=f"Personal data detected in {len(violations)} location(s)",
                severity="error",
                files=violations[:5]
            )
        return CheckResult(
            name="No Personal Data",
            passed=True,
            message="No personal data detected"
        )

    # ───────────────────────────────────────────────────────────────
    # Check 3: No Hardcoded Paths
    # ───────────────────────────────────────────────────────────────
    def check_no_hardcoded_paths(self, files: List[Path]) -> CheckResult:
        """Detect hardcoded user paths."""
        violations = []

        for filepath in files:
            if filepath.suffix != '.py':
                continue

            content = self._read_file_safe(filepath)
            if not content:
                continue

            for i, line in enumerate(content.split('\n'), 1):
                if self._is_allowlisted(line):
                    continue

                for pattern in self.PATH_PATTERNS:
                    if re.search(pattern, line):
                        violations.append(f"{filepath}:{i}")
                        break

        if violations:
            return CheckResult(
                name="No Hardcoded Paths",
                passed=False,
                message=f"Hardcoded paths in {len(violations)} location(s)",
                severity="error",
                files=violations[:5]
            )
        return CheckResult(
            name="No Hardcoded Paths",
            passed=True,
            message="No hardcoded paths detected"
        )

    # ───────────────────────────────────────────────────────────────
    # Check 4: File Locations
    # ───────────────────────────────────────────────────────────────
    def check_file_locations(self, files: List[Path]) -> CheckResult:
        """New tools should start in experimental/."""
        warnings = []

        for filepath in files:
            # Only check Python files in tools/
            if not (str(filepath).startswith('claude/tools/') and filepath.suffix == '.py'):
                continue

            # Skip test files, __init__, and already experimental
            if 'test_' in filepath.name or filepath.name == '__init__.py':
                continue
            if 'experimental' in str(filepath) or 'archive' in str(filepath):
                continue

            # Check if this is a NEW file (not in main)
            result = subprocess.run(
                ["git", "show", f"origin/main:{filepath}"],
                capture_output=True,
                cwd=MAIA_ROOT
            )
            if result.returncode != 0:  # File doesn't exist in main = new file
                warnings.append(str(filepath))

        if warnings:
            return CheckResult(
                name="File Locations",
                passed=True,  # Warning only
                message=f"New tools should start in experimental/: {len(warnings)} file(s)",
                severity="warning",
                files=warnings[:5]
            )
        return CheckResult(
            name="File Locations",
            passed=True,
            message="File locations OK"
        )

    # ───────────────────────────────────────────────────────────────
    # Check 5: Naming Conventions
    # ───────────────────────────────────────────────────────────────
    def check_naming_conventions(self, files: List[Path]) -> CheckResult:
        """Block bad naming patterns."""
        violations = []

        for filepath in files:
            # Skip archive and experimental
            if 'archive' in str(filepath) or 'experimental' in str(filepath):
                continue

            for pattern in self.BAD_NAME_PATTERNS:
                if re.search(pattern, filepath.name):
                    violations.append(str(filepath))
                    break

        if violations:
            return CheckResult(
                name="Naming Conventions",
                passed=False,
                message=f"Bad naming in {len(violations)} file(s) (_v2, _new, _old not allowed)",
                severity="error",
                files=violations
            )
        return CheckResult(
            name="Naming Conventions",
            passed=True,
            message="Naming conventions OK"
        )

    # ───────────────────────────────────────────────────────────────
    # Check 6: Tests Exist
    # ───────────────────────────────────────────────────────────────
    def check_tests_exist(self, files: List[Path]) -> CheckResult:
        """New tools should have tests."""
        missing_tests = []

        for filepath in files:
            # Only check new Python tools
            if not (str(filepath).startswith('claude/tools/') and filepath.suffix == '.py'):
                continue
            if 'test_' in filepath.name or filepath.name == '__init__.py':
                continue
            if 'experimental' in str(filepath) or 'archive' in str(filepath):
                continue

            # Check if corresponding test exists
            test_name = f"test_{filepath.stem}.py"
            test_paths = [
                MAIA_ROOT / "tests" / filepath.parent.name / test_name,
                MAIA_ROOT / "tests" / "tools" / filepath.parent.name / test_name,
                MAIA_ROOT / "tests" / test_name,
            ]

            if not any(p.exists() for p in test_paths):
                missing_tests.append(str(filepath))

        if missing_tests:
            return CheckResult(
                name="Tests Exist",
                passed=True,  # Warning only
                message=f"Missing tests for {len(missing_tests)} tool(s)",
                severity="warning",
                files=missing_tests[:5]
            )
        return CheckResult(
            name="Tests Exist",
            passed=True,
            message="Tests present"
        )

    # ───────────────────────────────────────────────────────────────
    # Check 7: Docstrings
    # ───────────────────────────────────────────────────────────────
    def check_docstrings(self, files: List[Path]) -> CheckResult:
        """Python files should have module docstrings."""
        missing_docstrings = []

        for filepath in files:
            if filepath.suffix != '.py':
                continue
            if filepath.name == '__init__.py':
                continue

            content = self._read_file_safe(filepath)
            if not content:
                continue

            try:
                tree = ast.parse(content)
                docstring = ast.get_docstring(tree)
                if not docstring:
                    missing_docstrings.append(str(filepath))
            except SyntaxError:
                pass  # Skip files with syntax errors

        if missing_docstrings:
            return CheckResult(
                name="Docstrings",
                passed=True,  # Warning only
                message=f"Missing module docstrings in {len(missing_docstrings)} file(s)",
                severity="warning",
                files=missing_docstrings[:5]
            )
        return CheckResult(
            name="Docstrings",
            passed=True,
            message="Docstrings present"
        )

    # ───────────────────────────────────────────────────────────────
    # Main Review Method
    # ───────────────────────────────────────────────────────────────
    def review(self) -> bool:
        """Run all checks and return pass/fail."""
        files = self.get_changed_files()

        if not files:
            print("✅ No files to review")
            return True

        print(f"📋 Reviewing {len(files)} file(s)...")
        if self.verbose:
            for f in files[:10]:
                print(f"   - {f}")
            if len(files) > 10:
                print(f"   ... and {len(files) - 10} more")
        print()

        # Run all checks
        self.results = [
            self.check_no_secrets(files),
            self.check_no_personal_data(files),
            self.check_no_hardcoded_paths(files),
            self.check_file_locations(files),
            self.check_naming_conventions(files),
            self.check_tests_exist(files),
            self.check_docstrings(files),
        ]

        # Display results
        errors = []
        warnings = []

        for result in self.results:
            icon = "✅" if result.passed else ("⚠️" if result.severity == "warning" else "❌")
            print(f"  {icon} {result.name}: {result.message}")

            if result.files and (not result.passed or result.severity == "warning"):
                for f in result.files[:3]:
                    print(f"      → {f}")
                if len(result.files) > 3:
                    print(f"      ... and {len(result.files) - 3} more")

            if not result.passed:
                if result.severity == "error":
                    errors.append(result)
                else:
                    warnings.append(result)

        print()

        if errors:
            print(f"❌ REVIEW FAILED: {len(errors)} error(s), {len(warnings)} warning(s)")
            print()
            print("Fix the errors above before pushing.")
            return False
        elif warnings:
            print(f"⚠️ REVIEW PASSED WITH {len(warnings)} WARNING(S)")
            return True
        else:
            print("✅ REVIEW PASSED")
            return True


def main():
    parser = argparse.ArgumentParser(
        description="Maia Contribution Reviewer - Quality gate for contributions"
    )
    parser.add_argument(
        "--ci",
        action="store_true",
        help="CI mode: compare against origin/main"
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="Local mode: check staged files"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output"
    )
    args = parser.parse_args()

    # Default to local mode if neither specified
    ci_mode = args.ci and not args.local

    reviewer = ContributionReviewer(ci_mode=ci_mode, verbose=args.verbose)
    passed = reviewer.review()

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
