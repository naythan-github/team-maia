#!/usr/bin/env python3
"""
Pre-Commit TDD Enforcement Gate - Phase 217

Prevents TDD protocol violations at commit time by validating:
1. New Python files in tools/ have corresponding test files
2. New tool projects have requirements.md
3. New agents follow v2.3 template patterns
4. Exemptions are properly documented

Enforcement Level: BLOCKING (prevents commits that violate TDD)
Escape Hatch: git commit --no-verify (requires justification in commit message)

Author: SRE Principal Engineer Agent
Date: 2025-12-01
Version: 1.0
"""

import subprocess
import sys
import re
from pathlib import Path
from typing import List, Tuple, Optional

# ANSI color codes for output
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
BOLD = '\033[1m'
RESET = '\033[0m'


class TDDEnforcementGate:
    """Enforces TDD protocol requirements at pre-commit time."""

    # Patterns that require TDD
    TOOL_PATTERN = re.compile(r'^maia/claude/tools/.*\.py$')
    AGENT_PATTERN = re.compile(r'^maia/claude/agents/.*\.md$')

    # Exemption patterns (don't require TDD)
    EXEMPT_PATTERNS = [
        re.compile(r'.*__init__\.py$'),           # Package init files
        re.compile(r'.*/test_.*\.py$'),           # Test files themselves
        re.compile(r'.*/conftest\.py$'),          # Pytest config
        re.compile(r'.*_test\.py$'),              # Test files (alternate naming)
        re.compile(r'.*/setup\.py$'),             # Setup scripts
        re.compile(r'.*/README\.md$'),            # Documentation
        re.compile(r'.*/requirements\.txt$'),     # Pip requirements
        re.compile(r'.*/requirements\.md$'),      # TDD requirements doc
    ]

    # Agent v2.3 required pattern markers
    AGENT_V23_PATTERNS = [
        'Self-Reflection & Review',
        'test frequently',
        'ADVANCED PATTERN',
    ]

    def __init__(self):
        self.violations = []
        self.warnings = []

    def get_staged_files(self) -> List[str]:
        """Get list of staged files from git."""
        try:
            result = subprocess.run(
                ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACM'],
                capture_output=True,
                text=True,
                check=True
            )
            return [f.strip() for f in result.stdout.split('\n') if f.strip()]
        except subprocess.CalledProcessError as e:
            print(f"{RED}Error getting staged files: {e}{RESET}")
            return []

    def is_exempt(self, filepath: str) -> bool:
        """Check if file is exempt from TDD requirements."""
        for pattern in self.EXEMPT_PATTERNS:
            if pattern.match(filepath):
                return True
        return False

    def find_corresponding_test(self, tool_file: str) -> Optional[str]:
        """Find the test file corresponding to a tool file."""
        path = Path(tool_file)

        # Try multiple test file naming conventions
        test_patterns = [
            path.parent / f"test_{path.stem}.py",                    # Same directory
            path.parent / "tests" / f"test_{path.stem}.py",          # tests/ subdirectory
            path.parent.parent / "tests" / f"test_{path.stem}.py",   # ../tests/ directory
        ]

        for test_path in test_patterns:
            if test_path.exists():
                return str(test_path)

        return None

    def find_requirements_md(self, tool_file: str) -> Optional[str]:
        """Find requirements.md for a tool project."""
        path = Path(tool_file)

        # Search up to 2 levels for requirements.md
        search_paths = [
            path.parent / "requirements.md",
            path.parent.parent / "requirements.md",
        ]

        for req_path in search_paths:
            if req_path.exists():
                return str(req_path)

        return None

    def check_agent_v23_compliance(self, agent_file: str) -> Tuple[bool, List[str]]:
        """Check if agent file follows v2.3 template patterns."""
        try:
            with open(agent_file, 'r') as f:
                content = f.read()

            missing_patterns = []
            for pattern in self.AGENT_V23_PATTERNS:
                if pattern not in content:
                    missing_patterns.append(pattern)

            return len(missing_patterns) == 0, missing_patterns
        except Exception as e:
            return False, [f"Error reading file: {e}"]

    def validate_tools(self, staged_files: List[str]) -> None:
        """Validate that new tools follow TDD requirements."""
        for filepath in staged_files:
            # Skip exempt files
            if self.is_exempt(filepath):
                continue

            # Check if it's a tool file
            if not self.TOOL_PATTERN.match(filepath):
                continue

            # Check for corresponding test file
            test_file = self.find_corresponding_test(filepath)
            if not test_file:
                self.violations.append({
                    'type': 'MISSING_TEST',
                    'file': filepath,
                    'message': f"No test file found for {filepath}"
                })

            # Check for requirements.md (unless it's a test file)
            if not filepath.endswith('test.py') and 'test_' not in filepath:
                req_file = self.find_requirements_md(filepath)
                if not req_file:
                    self.warnings.append({
                        'type': 'MISSING_REQUIREMENTS',
                        'file': filepath,
                        'message': f"No requirements.md found for {filepath} (recommended for TDD)"
                    })

    def validate_agents(self, staged_files: List[str]) -> None:
        """Validate that new agents follow v2.3 template."""
        for filepath in staged_files:
            if not self.AGENT_PATTERN.match(filepath):
                continue

            # Skip if file doesn't exist (deleted)
            if not Path(filepath).exists():
                continue

            compliant, missing = self.check_agent_v23_compliance(filepath)
            if not compliant:
                self.violations.append({
                    'type': 'AGENT_V23_NONCOMPLIANT',
                    'file': filepath,
                    'message': f"Agent missing v2.3 patterns: {', '.join(missing)}"
                })

    def print_violations(self) -> None:
        """Print violations and warnings in user-friendly format."""
        if self.violations:
            print(f"\n{RED}{BOLD}❌ TDD ENFORCEMENT GATE: VIOLATIONS DETECTED{RESET}\n")

            for i, violation in enumerate(self.violations, 1):
                print(f"{RED}{i}. {violation['type']}{RESET}")
                print(f"   File: {BLUE}{violation['file']}{RESET}")
                print(f"   Issue: {violation['message']}\n")

            print(f"{YELLOW}📋 TDD Protocol Requirements:{RESET}")
            print(f"   • All new tools (.py) must have test files (test_*.py)")
            print(f"   • Tool projects should have requirements.md")
            print(f"   • New agents must follow v2.3 template patterns")
            print(f"\n{YELLOW}🔧 How to fix:{RESET}")
            print(f"   1. Create missing test files before committing")
            print(f"   2. Add requirements.md for new tool projects")
            print(f"   3. Follow agent v2.3 template (see claude/agents/README.md)")
            print(f"\n{YELLOW}⚡ Emergency bypass (use sparingly):{RESET}")
            print(f"   git commit --no-verify -m \"reason for skipping TDD\"")
            print(f"\n{RED}Commit blocked until violations resolved.{RESET}\n")

        if self.warnings:
            print(f"\n{YELLOW}{BOLD}⚠️  TDD WARNINGS (non-blocking):{RESET}\n")
            for i, warning in enumerate(self.warnings, 1):
                print(f"{YELLOW}{i}. {warning['message']}{RESET}")
            print()

    def run(self) -> int:
        """Run TDD enforcement checks. Returns 0 if passed, 1 if failed."""
        print(f"{BLUE}🧪 Running TDD Enforcement Gate...{RESET}")

        staged_files = self.get_staged_files()

        if not staged_files:
            print(f"{GREEN}✅ No files staged for commit{RESET}")
            return 0

        # Run validation checks
        self.validate_tools(staged_files)
        self.validate_agents(staged_files)

        # Print results
        if self.violations:
            self.print_violations()
            return 1

        if self.warnings:
            self.print_violations()

        print(f"{GREEN}✅ TDD Enforcement Gate: PASSED{RESET}")
        return 0


def main():
    """Main entry point."""
    gate = TDDEnforcementGate()
    exit_code = gate.run()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
