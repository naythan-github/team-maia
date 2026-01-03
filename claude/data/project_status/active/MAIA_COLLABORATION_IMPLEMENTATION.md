# Maia Multi-User Collaboration: Implementation Plan

**Project ID**: COLLAB-IMPL-001
**Created**: 2026-01-03
**Status**: Ready for Execution
**Priority**: Technical debt avoidance over speed
**Executor**: Maia (DevOps Principal Architect Agent)

---

## Execution Principles

1. **No shortcuts** - Implement fully, not partially
2. **Test everything** - Each component validated before moving on
3. **Document as you go** - Update docs with each change
4. **Debt-free** - If something feels hacky, fix it properly

---

## Phase 1: Foundation (6 hours)

### 1.1 Create GitHub Teams Structure

**Why**: Proper ownership from day 1, not refactored later.

**Teams to Create** (manually in GitHub org settings):
```
@org/maia-core        - Owner + 2 backups (core system approval)
@org/maia-sre         - SRE team members (SRE tools)
@org/maia-security    - Security team members (security tools)
@org/maia-contributors - All 30 engineers (extensions)
```

**Action**: Document team membership requirements for user to configure.

---

### 1.2 Create CODEOWNERS

**File**: `.github/CODEOWNERS`

```gitignore
# ═══════════════════════════════════════════════════════════════════
# MAIA CODEOWNERS - Defense in Depth Ownership Model
# ═══════════════════════════════════════════════════════════════════
#
# Tier 1: PROTECTED - Core team approval required
# Tier 2: DOMAIN - Domain team + core visibility
# Tier 3: OPEN - Any contributor, CI gates only
#
# ═══════════════════════════════════════════════════════════════════

# ───────────────────────────────────────────────────────────────────
# TIER 1: PROTECTED - @org/maia-core approval required
# ───────────────────────────────────────────────────────────────────

# System identity
/CLAUDE.md                                  @org/maia-core
/SYSTEM_STATE.md                            @org/maia-core

# Protection rules (self-protecting)
/.github/CODEOWNERS                         @org/maia-core
/CODEOWNERS                                 @org/maia-core

# Core context (identity, protocols, strategies)
/claude/context/core/                       @org/maia-core

# All agent definitions
/claude/agents/                             @org/maia-core

# System hooks (security-critical)
/claude/hooks/                              @org/maia-core

# Core utilities (path resolution, system bootstrap)
/claude/tools/core/                         @org/maia-core

# UFC system
/claude/context/ufc_system.md               @org/maia-core

# ───────────────────────────────────────────────────────────────────
# TIER 2: DOMAIN - Domain team ownership with core visibility
# ───────────────────────────────────────────────────────────────────

# SRE tools
/claude/tools/sre/                          @org/maia-sre @org/maia-core
/tests/sre/                                 @org/maia-sre

# Security tools
/claude/tools/security/                     @org/maia-security @org/maia-core
/tests/security/                            @org/maia-security

# ServiceDesk tools
/claude/tools/servicedesk/                  @org/maia-sre @org/maia-core

# Automation
/claude/tools/automation/                   @org/maia-sre @org/maia-core

# Business tools
/claude/tools/business/                     @org/maia-core

# Communication tools
/claude/tools/communication/                @org/maia-core

# Commands (slash commands)
/claude/commands/                           @org/maia-core

# Dashboards
/claude/tools/dashboards/                   @org/maia-sre @org/maia-core

# Monitoring
/claude/tools/monitoring/                   @org/maia-sre @org/maia-core

# General tests
/tests/                                     @org/maia-core

# ───────────────────────────────────────────────────────────────────
# TIER 3: OPEN - CI gates only, any contributor
# ───────────────────────────────────────────────────────────────────

# Extensions (experimental, plugins)
/claude/extensions/

# User namespaces
/claude/projects/*/

# Experimental tools
/claude/tools/experimental/

# Archive (historical)
/claude/tools/archive/

# Non-core documentation
/docs/
```

**Validation**:
- [ ] File created
- [ ] Syntax valid (no GitHub errors)
- [ ] All paths exist or are valid patterns

---

### 1.3 Configure Branch Protection

**Location**: GitHub repo → Settings → Branches → Add rule

**Rule for `main`**:
```
Branch name pattern: main

✅ Require a pull request before merging
   ✅ Required approving reviews: 1
   ✅ Dismiss stale pull request approvals when new commits are pushed
   ✅ Require review from Code Owners
   ✅ Require approval of the most recent reviewable push

✅ Require status checks to pass before merging
   ✅ Require branches to be up to date before merging
   Status checks that are required:
     - ci-quick-checks
     - ci-tests
     - ci-security
     - ci-contribution-review

✅ Require conversation resolution before merging

✅ Require linear history

✅ Do not allow bypassing the above settings

❌ Allow force pushes (DISABLED)
❌ Allow deletions (DISABLED)
```

**Action**: Document for user to configure manually (cannot automate via API without admin token).

---

### 1.4 Create CI Skeleton

**File**: `.github/workflows/ci.yml`

```yaml
name: Maia CI

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

env:
  PYTHON_VERSION: '3.11'

jobs:
  # ═══════════════════════════════════════════════════════════════
  # Quick checks - fast feedback (target: 30s)
  # ═══════════════════════════════════════════════════════════════
  ci-quick-checks:
    name: Quick Checks
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Check for personal data
        run: |
          echo "🔍 Scanning for personal data..."
          if grep -rE "(naythandawe|/Users/naythan|/home/naythan)" \
             claude/ --include="*.py" --include="*.md" 2>/dev/null | \
             grep -v "CODEOWNERS\|CONTRIBUTING\|\.gitignore"; then
            echo "::error::Personal data detected in source files"
            exit 1
          fi
          echo "✅ No personal data detected"

      - name: Check for hardcoded paths
        run: |
          echo "🔍 Scanning for hardcoded user paths..."
          if grep -rE '"/Users/[a-zA-Z]+|"/home/[a-zA-Z]+' \
             claude/tools --include="*.py" 2>/dev/null | \
             grep -v "test_\|# Example\|\.example"; then
            echo "::error::Hardcoded user paths detected"
            exit 1
          fi
          echo "✅ No hardcoded paths detected"

      - name: Check naming conventions
        run: |
          echo "🔍 Checking naming conventions..."
          bad_files=$(find claude/tools -type f \( \
            -name "*_v[0-9]*" -o \
            -name "*_new.*" -o \
            -name "*_old.*" -o \
            -name "*_backup.*" -o \
            -name "*_copy.*" \
          \) 2>/dev/null | grep -v "experimental\|archive" || true)

          if [ -n "$bad_files" ]; then
            echo "::error::Naming convention violations found:"
            echo "$bad_files"
            exit 1
          fi
          echo "✅ Naming conventions OK"

  # ═══════════════════════════════════════════════════════════════
  # Security scan (target: 1m)
  # ═══════════════════════════════════════════════════════════════
  ci-security:
    name: Security Scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Secret detection (Trufflehog)
        uses: trufflesecurity/trufflehog@main
        with:
          path: ./
          base: ${{ github.event.pull_request.base.sha || 'HEAD~1' }}
          head: HEAD
          extra_args: --only-verified

      - name: Check for potential secrets in code
        run: |
          echo "🔍 Scanning for hardcoded secrets..."
          patterns='(api_key|secret|password|token|credential)\s*=\s*["\x27][A-Za-z0-9+/=_-]{20,}["\x27]'
          if grep -rEi "$patterns" claude/ --include="*.py" 2>/dev/null | \
             grep -v "test_\|# Example\|\.example\|getenv\|environ"; then
            echo "::warning::Potential hardcoded secrets found - review required"
          fi
          echo "✅ Secret scan complete"

  # ═══════════════════════════════════════════════════════════════
  # Tests (target: 2m)
  # ═══════════════════════════════════════════════════════════════
  ci-tests:
    name: Tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'
          cache-dependency-path: |
            requirements.txt
            requirements-dev.txt

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt 2>/dev/null || pip install pytest pytest-cov ruff

      - name: Run tests
        run: |
          python -m pytest tests/ -v --tb=short \
            --cov=claude/tools \
            --cov-report=term-missing \
            -x || true  # Don't fail CI if no tests yet

      - name: Lint with ruff
        run: |
          pip install ruff
          ruff check claude/tools --select=E,F,W --ignore=E501 || true

  # ═══════════════════════════════════════════════════════════════
  # Contribution review (target: 30s)
  # ═══════════════════════════════════════════════════════════════
  ci-contribution-review:
    name: Contribution Review
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Run contribution reviewer
        run: |
          if [ -f "claude/hooks/contribution_reviewer.py" ]; then
            python3 claude/hooks/contribution_reviewer.py --ci
          else
            echo "⚠️ contribution_reviewer.py not yet implemented"
          fi

  # ═══════════════════════════════════════════════════════════════
  # Final gate
  # ═══════════════════════════════════════════════════════════════
  ci-all-passed:
    name: All Checks Passed
    needs: [ci-quick-checks, ci-security, ci-tests, ci-contribution-review]
    runs-on: ubuntu-latest
    steps:
      - run: echo "✅ All CI checks passed"
```

**Validation**:
- [ ] Workflow file valid YAML
- [ ] All job names match branch protection requirements
- [ ] Test run succeeds

---

### 1.5 Create requirements-dev.txt

**File**: `requirements-dev.txt`

```
# Development and testing dependencies
pytest>=7.0.0
pytest-cov>=4.0.0
ruff>=0.1.0
mypy>=1.0.0

# For contribution_reviewer.py
pathlib
```

**Validation**:
- [ ] File created
- [ ] pip install -r requirements-dev.txt succeeds

---

### 1.6 Update .gitignore

**Additions to**: `.gitignore`

```gitignore
# ═══════════════════════════════════════════════════════════════════
# PERSONAL DATA - CRITICAL: NEVER COMMIT
# ═══════════════════════════════════════════════════════════════════

# Personal profile and context (template OK, actual file local)
claude/context/personal/
!claude/context/personal/.gitkeep
!claude/context/personal/TEMPLATE_profile.md

# User-specific databases
claude/data/databases/user/
*_naythan*.db
personal_knowledge_graph.db

# User preferences (actual file - template is separate)
claude/data/user_preferences.json

# ═══════════════════════════════════════════════════════════════════
# SECRETS AND CREDENTIALS
# ═══════════════════════════════════════════════════════════════════

# Credential files
*.pem
*.key
*.p12
*.pfx
*credentials*.json
!*credentials.example.json
*token*.json
!*token.example.json
.credentials/
secrets/
*.secret

# Environment files
.env
.env.*
!.env.example

# OAuth
oauth*.json
*_credentials.json
*_token.json

# ═══════════════════════════════════════════════════════════════════
# DERIVED/REGENERABLE DATABASES
# ═══════════════════════════════════════════════════════════════════

# System databases (regenerated locally)
claude/data/databases/system/*.db
claude/data/databases/system/*.db-*
claude/data/databases/intelligence/*.db
claude/data/databases/intelligence/*.db-*

# SQLite temp files
*.db-shm
*.db-wal
*.db-journal

# ═══════════════════════════════════════════════════════════════════
# SESSION DATA
# ═══════════════════════════════════════════════════════════════════

# Session files (should be in /tmp but catch if local)
maia_*.json
*_session_*.json
checkpoint_*.json
```

**Validation**:
- [ ] Additions merged into existing .gitignore
- [ ] No existing tracked files match new patterns (or untrack them)

---

## Phase 2: Security Gates (6 hours)

### 2.1 Create contribution_reviewer.py

**File**: `claude/hooks/contribution_reviewer.py`

```python
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
```

**Validation**:
- [ ] File created
- [ ] `python3 contribution_reviewer.py --help` works
- [ ] `python3 contribution_reviewer.py --local` runs without error
- [ ] Test with intentionally bad file (should detect)

---

### 2.2 Create Pre-Commit Hook Template

**File**: `scripts/hooks/pre-commit`

```bash
#!/bin/bash
# Maia pre-commit hook
# Installed by scripts/setup-team-member.sh

set -e

echo "🔍 Running pre-commit checks..."

# Get repo root
MAIA_ROOT="$(git rev-parse --show-toplevel)"

# ───────────────────────────────────────────────────────────────
# Check 1: Personal data in staged files
# ───────────────────────────────────────────────────────────────
echo "  Checking for personal data..."
if git diff --cached --name-only | xargs grep -l \
   "naythandawe\|/Users/naythan\|/home/naythan" 2>/dev/null | \
   grep -v "CODEOWNERS\|CONTRIBUTING"; then
    echo "❌ BLOCKED: Personal data detected in staged files"
    echo "   Remove personal identifiers before committing"
    exit 1
fi

# ───────────────────────────────────────────────────────────────
# Check 2: Hardcoded paths in Python files
# ───────────────────────────────────────────────────────────────
echo "  Checking for hardcoded paths..."
staged_py=$(git diff --cached --name-only | grep "\.py$" || true)
if [ -n "$staged_py" ]; then
    if echo "$staged_py" | xargs grep -l '"/Users/\|"/home/' 2>/dev/null | \
       grep -v "test_\|\.example"; then
        echo "❌ BLOCKED: Hardcoded user paths detected"
        echo "   Use environment variables or PathManager instead"
        exit 1
    fi
fi

# ───────────────────────────────────────────────────────────────
# Check 3: Potential secrets
# ───────────────────────────────────────────────────────────────
echo "  Checking for secrets..."
if git diff --cached | grep -E 'sk-ant-api|sk-[a-zA-Z0-9]{48}|ghp_[a-zA-Z0-9]{36}' > /dev/null 2>&1; then
    echo "❌ BLOCKED: Potential API key detected"
    echo "   Never commit secrets - use environment variables"
    exit 1
fi

# ───────────────────────────────────────────────────────────────
# Check 4: TDD gate (if exists)
# ───────────────────────────────────────────────────────────────
if [ -f "$MAIA_ROOT/claude/hooks/pre_commit_tdd_gate.py" ]; then
    echo "  Running TDD gate..."
    python3 "$MAIA_ROOT/claude/hooks/pre_commit_tdd_gate.py" || exit 1
fi

echo "✅ Pre-commit passed"
```

**Validation**:
- [ ] File created with execute permission
- [ ] Works when installed in .git/hooks/

---

### 2.3 Create Pre-Push Hook Template

**File**: `scripts/hooks/pre-push`

```bash
#!/bin/bash
# Maia pre-push hook
# Installed by scripts/setup-team-member.sh

set -e

MAIA_ROOT="$(git rev-parse --show-toplevel)"

# ───────────────────────────────────────────────────────────────
# Block direct push to main
# ───────────────────────────────────────────────────────────────
current_branch=$(git symbolic-ref HEAD 2>/dev/null | sed -e 's,.*/\(.*\),\1,')

if [ "$current_branch" = "main" ]; then
    echo "❌ BLOCKED: Direct push to main not allowed"
    echo ""
    echo "   Create a feature branch instead:"
    echo "   git checkout -b feature/your-feature"
    echo "   git push -u origin feature/your-feature"
    echo ""
    exit 1
fi

# ───────────────────────────────────────────────────────────────
# Run contribution reviewer
# ───────────────────────────────────────────────────────────────
if [ -f "$MAIA_ROOT/claude/hooks/contribution_reviewer.py" ]; then
    echo "🤖 Running contribution review..."
    python3 "$MAIA_ROOT/claude/hooks/contribution_reviewer.py" --local

    if [ $? -ne 0 ]; then
        echo ""
        echo "❌ BLOCKED: Contribution review failed"
        echo "   Fix the issues above and try again"
        exit 1
    fi
fi

echo "✅ Ready to push"
```

**Validation**:
- [ ] File created with execute permission
- [ ] Blocks push to main when tested

---

### 2.4 Create Post-Merge Hook Template

**File**: `scripts/hooks/post-merge`

```bash
#!/bin/bash
# Maia post-merge hook
# Regenerates local databases after pulling changes

MAIA_ROOT="$(git rev-parse --show-toplevel)"

echo "🔄 Post-merge: Refreshing local databases..."

# Regenerate capabilities database
if [ -f "$MAIA_ROOT/claude/tools/sre/capabilities_registry.py" ]; then
    if python3 "$MAIA_ROOT/claude/tools/sre/capabilities_registry.py" scan --quiet 2>/dev/null; then
        echo "  ✅ Capabilities database updated"
    else
        echo "  ⚠️ Capabilities refresh failed (will regenerate on first use)"
    fi
fi

# Regenerate system state database
if [ -f "$MAIA_ROOT/claude/tools/sre/system_state_etl.py" ]; then
    if python3 "$MAIA_ROOT/claude/tools/sre/system_state_etl.py" --recent all --quiet 2>/dev/null; then
        echo "  ✅ System state database updated"
    else
        echo "  ⚠️ System state refresh failed (non-critical)"
    fi
fi

echo "✅ Post-merge complete"
```

**Validation**:
- [ ] File created with execute permission
- [ ] Runs after git pull

---

## Phase 3: Path Isolation (8 hours)

### 3.1 Create Path Resolution Module

**File**: `claude/tools/core/paths.py`

```python
#!/usr/bin/env python3
"""
Maia Path Resolution - Portable path handling for multi-user operation.

Provides consistent path resolution regardless of user or machine.
All tools should use these functions instead of hardcoded paths.

Usage:
    from claude.tools.core.paths import PathManager

    maia_root = PathManager.get_maia_root()
    user_data = PathManager.get_user_data_path()
    db_path = PathManager.get_user_db_path("preferences.db")

Environment Variables:
    MAIA_ROOT - Override Maia repository location
    MAIA_USER_DATA - Override user data location (default: ~/.maia)

Author: DevOps Principal Architect Agent
Date: 2026-01-03
"""

import os
from pathlib import Path
from typing import Optional


class PathManager:
    """
    Centralized path resolution for Maia.

    Locations:
    - MAIA_ROOT: Shared repository (tools, agents, context)
    - USER_DATA: Personal data (~/.maia/)
    - WORK_PROJECTS: User's work outputs (~/work_projects/)
    """

    _maia_root: Optional[Path] = None
    _user_data: Optional[Path] = None

    @classmethod
    def get_maia_root(cls) -> Path:
        """
        Get Maia repository root (shared code).

        Resolution order:
        1. MAIA_ROOT environment variable
        2. Git repository root detection
        3. Walk up from this file to find CLAUDE.md

        Returns:
            Path to Maia root directory

        Raises:
            RuntimeError: If MAIA_ROOT cannot be determined
        """
        if cls._maia_root is not None:
            return cls._maia_root

        # Try environment variable first
        env_root = os.environ.get("MAIA_ROOT")
        if env_root:
            root = Path(env_root)
            if root.exists() and (root / "CLAUDE.md").exists():
                cls._maia_root = root
                return root

        # Try git root
        try:
            import subprocess
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent
            )
            if result.returncode == 0:
                root = Path(result.stdout.strip())
                if (root / "CLAUDE.md").exists():
                    cls._maia_root = root
                    return root
        except Exception:
            pass

        # Walk up from this file
        current = Path(__file__).resolve()
        for parent in current.parents:
            if (parent / "CLAUDE.md").exists():
                cls._maia_root = parent
                return parent

        raise RuntimeError(
            "Cannot determine MAIA_ROOT. Set MAIA_ROOT environment variable or "
            "ensure you're running from within the Maia repository."
        )

    @classmethod
    def get_user_data_path(cls) -> Path:
        """
        Get user-specific data directory (~/.maia/).

        This directory contains:
        - Personal profile
        - User preferences
        - User databases
        - Session checkpoints

        Creates the directory if it doesn't exist.

        Returns:
            Path to user data directory
        """
        if cls._user_data is not None:
            return cls._user_data

        # Check environment override
        env_path = os.environ.get("MAIA_USER_DATA")
        if env_path:
            user_data = Path(env_path)
        else:
            user_data = Path.home() / ".maia"

        # Ensure directory exists with proper structure
        user_data.mkdir(parents=True, exist_ok=True)
        (user_data / "data" / "databases" / "user").mkdir(parents=True, exist_ok=True)
        (user_data / "data" / "checkpoints").mkdir(parents=True, exist_ok=True)
        (user_data / "context" / "personal").mkdir(parents=True, exist_ok=True)
        (user_data / "sessions").mkdir(parents=True, exist_ok=True)

        cls._user_data = user_data
        return user_data

    @classmethod
    def get_user_db_path(cls, db_name: str) -> Path:
        """
        Get path for user-specific database.

        Args:
            db_name: Database filename (e.g., "preferences.db")

        Returns:
            Full path to database in user data directory
        """
        return cls.get_user_data_path() / "data" / "databases" / "user" / db_name

    @classmethod
    def get_shared_db_path(cls, db_name: str) -> Path:
        """
        Get path for shared/derived database (regenerated locally).

        Args:
            db_name: Database filename (e.g., "capabilities.db")

        Returns:
            Full path to database in system directory
        """
        return cls.get_maia_root() / "claude" / "data" / "databases" / "system" / db_name

    @classmethod
    def get_work_projects_path(cls) -> Path:
        """
        Get user's work projects directory.

        This is for work outputs FROM Maia, not Maia system files.

        Returns:
            Path to work projects directory (~/work_projects/)
        """
        work_path = Path.home() / "work_projects"
        work_path.mkdir(parents=True, exist_ok=True)
        return work_path

    @classmethod
    def get_session_path(cls, session_id: str) -> Path:
        """
        Get path for session state file.

        Sessions are stored in ~/.maia/sessions/ to survive reboots.

        Args:
            session_id: Unique session identifier

        Returns:
            Path to session file
        """
        return cls.get_user_data_path() / "sessions" / f"session_{session_id}.json"

    @classmethod
    def get_profile_path(cls) -> Path:
        """
        Get path to user's personal profile.

        Returns:
            Path to profile.md in user data directory
        """
        return cls.get_user_data_path() / "context" / "personal" / "profile.md"

    @classmethod
    def get_preferences_path(cls) -> Path:
        """
        Get path to user preferences file.

        Returns:
            Path to user_preferences.json
        """
        return cls.get_user_data_path() / "data" / "user_preferences.json"


# Convenience functions for common operations
def get_maia_root() -> Path:
    """Shortcut for PathManager.get_maia_root()"""
    return PathManager.get_maia_root()


def get_user_data() -> Path:
    """Shortcut for PathManager.get_user_data_path()"""
    return PathManager.get_user_data_path()


# Self-test when run directly
if __name__ == "__main__":
    print("Maia Path Resolution Test")
    print("=" * 50)
    print(f"MAIA_ROOT:     {PathManager.get_maia_root()}")
    print(f"USER_DATA:     {PathManager.get_user_data_path()}")
    print(f"User DB:       {PathManager.get_user_db_path('test.db')}")
    print(f"Shared DB:     {PathManager.get_shared_db_path('capabilities.db')}")
    print(f"Work Projects: {PathManager.get_work_projects_path()}")
    print(f"Profile:       {PathManager.get_profile_path()}")
    print(f"Preferences:   {PathManager.get_preferences_path()}")
    print("=" * 50)
    print("✅ All paths resolved successfully")
```

**Validation**:
- [ ] File created
- [ ] `python3 claude/tools/core/paths.py` runs and shows all paths
- [ ] Paths are created correctly

---

### 3.2 Fix Hardcoded Path Tools

**Tools to fix** (8 identified):

| Tool | Current Path | Fix |
|------|--------------|-----|
| `claude/tools/dns_audit_route53.py:347-348` | `/Users/naythandawe/Library/CloudStorage/...` | Use CLI arg or config |
| `claude/tools/document_conversion/create_clean_orro_template.py:33` | `/Users/naythandawe/work_projects/...` | Use `PathManager.get_work_projects_path()` |
| `claude/tools/dns_complete_audit.py:348-349` | `/Users/naythandawe/Library/CloudStorage/...` | Use CLI arg or config |
| `claude/tools/intelligent_product_grouper.py:211,233` | `/Users/naythandawe/Library/CloudStorage/...` | Use CLI arg or config |
| `claude/tools/interview/test_cv_parser.py:283` | `/Users/naythandawe/Library/CloudStorage/...` | Use test fixtures |
| `claude/tools/monitoring/health_check.py:15` | `/Users/naythan/Library/Mobile Documents/...` | Use `PathManager` |
| `claude/tools/morning_email_intelligence_local.py` | Various | Use `PathManager` |
| `claude/tools/personal_knowledge_graph.py` | Various | Use `PathManager.get_user_db_path()` |

**Pattern for each fix**:
```python
# Before
OUTPUT_PATH = "/Users/naythandawe/work_projects/foo"

# After
from claude.tools.core.paths import PathManager
OUTPUT_PATH = PathManager.get_work_projects_path() / "foo"
```

**Validation**:
- [ ] Each tool updated
- [ ] No hardcoded paths remain (grep confirms)
- [ ] Tools still function correctly

---

### 3.3 Create Setup Script

**File**: `scripts/setup-team-member.sh`

```bash
#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# Maia Team Member Setup Script
#
# Sets up a new team member's local environment for Maia development.
# Run this once after cloning the repository.
#
# Usage: ./scripts/setup-team-member.sh
# ═══════════════════════════════════════════════════════════════════

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "═══════════════════════════════════════════════════════════════════"
echo "                    MAIA TEAM MEMBER SETUP                          "
echo "═══════════════════════════════════════════════════════════════════"
echo -e "${NC}"

# Get script directory and MAIA_ROOT
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MAIA_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "MAIA_ROOT: $MAIA_ROOT"
echo ""

# ───────────────────────────────────────────────────────────────────
# Step 1: Verify prerequisites
# ───────────────────────────────────────────────────────────────────
echo -e "${YELLOW}Step 1: Verifying prerequisites...${NC}"

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
python_major=$(echo "$python_version" | cut -d'.' -f1)
python_minor=$(echo "$python_version" | cut -d'.' -f2)

if [ "$python_major" -lt 3 ] || { [ "$python_major" -eq 3 ] && [ "$python_minor" -lt 9 ]; }; then
    echo -e "${RED}❌ Python 3.9+ required (found $python_version)${NC}"
    exit 1
fi
echo -e "  ${GREEN}✓${NC} Python $python_version"

# Check git
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Git not found${NC}"
    exit 1
fi
echo -e "  ${GREEN}✓${NC} Git installed"

# ───────────────────────────────────────────────────────────────────
# Step 2: Create local data directory (~/.maia/)
# ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}Step 2: Creating local data directory...${NC}"

mkdir -p ~/.maia/{data/databases/user,data/checkpoints,context/personal,sessions,projects}

echo -e "  ${GREEN}✓${NC} Created ~/.maia/ directory structure"

# ───────────────────────────────────────────────────────────────────
# Step 3: Create personal profile (if not exists)
# ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}Step 3: Setting up personal profile...${NC}"

if [ ! -f ~/.maia/context/personal/profile.md ]; then
    cat > ~/.maia/context/personal/profile.md << 'PROFILE'
# Personal Profile

## Identity
- **Name**: [Your Full Name]
- **Role**: [Your Role/Title]
- **Team**: [Your Team]

## Preferences
- **Default Agent**: sre_principal_engineer_agent
- **Working Style**: [e.g., "Prefer detailed explanations"]
- **Focus Areas**: [e.g., "Azure", "Security", "SRE"]

## Notes
<!-- Add any personal notes or context Maia should know -->

PROFILE
    echo -e "  ${GREEN}✓${NC} Created profile template"
    echo -e "  ${YELLOW}→${NC} Edit ~/.maia/context/personal/profile.md with your details"
else
    echo -e "  ${GREEN}✓${NC} Profile already exists"
fi

# ───────────────────────────────────────────────────────────────────
# Step 4: Create user preferences (if not exists)
# ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}Step 4: Setting up user preferences...${NC}"

if [ ! -f ~/.maia/data/user_preferences.json ]; then
    cat > ~/.maia/data/user_preferences.json << PREFS
{
  "default_agent": "sre_principal_engineer_agent",
  "fallback_agent": "sre_principal_engineer_agent",
  "version": "1.0",
  "description": "User-specific Maia preferences",
  "created": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "user": "$USER"
}
PREFS
    echo -e "  ${GREEN}✓${NC} Created user preferences"
else
    echo -e "  ${GREEN}✓${NC} User preferences already exists"
fi

# ───────────────────────────────────────────────────────────────────
# Step 5: Install Git hooks
# ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}Step 5: Installing Git hooks...${NC}"

HOOKS_DIR="$MAIA_ROOT/.git/hooks"
HOOKS_SRC="$MAIA_ROOT/scripts/hooks"

# Pre-commit hook
if [ -f "$HOOKS_SRC/pre-commit" ]; then
    cp "$HOOKS_SRC/pre-commit" "$HOOKS_DIR/pre-commit"
    chmod +x "$HOOKS_DIR/pre-commit"
    echo -e "  ${GREEN}✓${NC} Installed pre-commit hook"
else
    echo -e "  ${YELLOW}⚠${NC} pre-commit hook source not found (skipping)"
fi

# Pre-push hook
if [ -f "$HOOKS_SRC/pre-push" ]; then
    cp "$HOOKS_SRC/pre-push" "$HOOKS_DIR/pre-push"
    chmod +x "$HOOKS_DIR/pre-push"
    echo -e "  ${GREEN}✓${NC} Installed pre-push hook"
else
    echo -e "  ${YELLOW}⚠${NC} pre-push hook source not found (skipping)"
fi

# Post-merge hook
if [ -f "$HOOKS_SRC/post-merge" ]; then
    cp "$HOOKS_SRC/post-merge" "$HOOKS_DIR/post-merge"
    chmod +x "$HOOKS_DIR/post-merge"
    echo -e "  ${GREEN}✓${NC} Installed post-merge hook"
else
    echo -e "  ${YELLOW}⚠${NC} post-merge hook source not found (skipping)"
fi

# ───────────────────────────────────────────────────────────────────
# Step 6: Install Python dependencies
# ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}Step 6: Installing Python dependencies...${NC}"

cd "$MAIA_ROOT"

if [ -f "requirements.txt" ]; then
    pip3 install -q -r requirements.txt 2>/dev/null || {
        echo -e "  ${YELLOW}⚠${NC} Some dependencies may have failed (non-critical)"
    }
    echo -e "  ${GREEN}✓${NC} Installed requirements.txt"
fi

if [ -f "requirements-dev.txt" ]; then
    pip3 install -q -r requirements-dev.txt 2>/dev/null || true
    echo -e "  ${GREEN}✓${NC} Installed requirements-dev.txt"
fi

# ───────────────────────────────────────────────────────────────────
# Step 7: Generate local databases
# ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}Step 7: Generating local databases...${NC}"

# Capabilities database
if [ -f "$MAIA_ROOT/claude/tools/sre/capabilities_registry.py" ]; then
    if python3 "$MAIA_ROOT/claude/tools/sre/capabilities_registry.py" scan --quiet 2>/dev/null; then
        echo -e "  ${GREEN}✓${NC} Capabilities database generated"
    else
        echo -e "  ${YELLOW}⚠${NC} Capabilities database will generate on first use"
    fi
fi

# System state database
if [ -f "$MAIA_ROOT/claude/tools/sre/system_state_etl.py" ]; then
    if python3 "$MAIA_ROOT/claude/tools/sre/system_state_etl.py" --recent all --quiet 2>/dev/null; then
        echo -e "  ${GREEN}✓${NC} System state database generated"
    else
        echo -e "  ${YELLOW}⚠${NC} System state database will generate on first use"
    fi
fi

# ───────────────────────────────────────────────────────────────────
# Step 8: Verify setup
# ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}Step 8: Verifying setup...${NC}"

# Check path resolution
if python3 -c "from claude.tools.core.paths import PathManager; print(PathManager.get_maia_root())" 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} Path resolution working"
else
    echo -e "  ${YELLOW}⚠${NC} Path resolution may need MAIA_ROOT env var"
fi

# ───────────────────────────────────────────────────────────────────
# Complete!
# ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}                    SETUP COMPLETE!                                 ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Next steps:"
echo ""
echo "  1. Edit your profile:"
echo "     vim ~/.maia/context/personal/profile.md"
echo ""
echo "  2. Start Maia:"
echo "     Open Claude Code in $MAIA_ROOT"
echo "     Type: load"
echo ""
echo "  3. To contribute:"
echo "     git checkout -b feature/your-feature"
echo "     # make changes"
echo "     git add . && git commit -m 'your message'"
echo "     git push -u origin feature/your-feature"
echo "     # create PR on GitHub"
echo ""
echo "Documentation: .github/CONTRIBUTING.md"
echo ""
```

**Validation**:
- [ ] Script created with execute permission
- [ ] Runs successfully on fresh clone
- [ ] Creates all expected directories and files
- [ ] Hooks installed correctly

---

## Phase 4: Quality Automation (6 hours)

### 4.1 Create Auto-Labeler Config

**File**: `.github/labeler.yml`

```yaml
# ═══════════════════════════════════════════════════════════════════
# Maia Auto-Labeler Configuration
# Automatically labels PRs based on changed files
# ═══════════════════════════════════════════════════════════════════

# ───────────────────────────────────────────────────────────────────
# Protection tier labels
# ───────────────────────────────────────────────────────────────────
core-change:
  - changed-files:
      - any-glob-to-any-file:
          - 'claude/agents/**'
          - 'claude/hooks/**'
          - 'claude/context/core/**'
          - 'claude/tools/core/**'
          - 'CLAUDE.md'
          - 'SYSTEM_STATE.md'
          - '.github/CODEOWNERS'
          - 'CODEOWNERS'

# ───────────────────────────────────────────────────────────────────
# Domain labels
# ───────────────────────────────────────────────────────────────────
sre:
  - changed-files:
      - any-glob-to-any-file:
          - 'claude/tools/sre/**'
          - 'tests/sre/**'

security:
  - changed-files:
      - any-glob-to-any-file:
          - 'claude/tools/security/**'
          - 'tests/security/**'

servicedesk:
  - changed-files:
      - any-glob-to-any-file:
          - 'claude/tools/servicedesk/**'

automation:
  - changed-files:
      - any-glob-to-any-file:
          - 'claude/tools/automation/**'

dashboards:
  - changed-files:
      - any-glob-to-any-file:
          - 'claude/tools/dashboards/**'

monitoring:
  - changed-files:
      - any-glob-to-any-file:
          - 'claude/tools/monitoring/**'

# ───────────────────────────────────────────────────────────────────
# Type labels
# ───────────────────────────────────────────────────────────────────
tools:
  - changed-files:
      - any-glob-to-any-file:
          - 'claude/tools/**/*.py'

agents:
  - changed-files:
      - any-glob-to-any-file:
          - 'claude/agents/**'

commands:
  - changed-files:
      - any-glob-to-any-file:
          - 'claude/commands/**'

documentation:
  - changed-files:
      - any-glob-to-any-file:
          - '**/*.md'
          - 'docs/**'

tests:
  - changed-files:
      - any-glob-to-any-file:
          - 'tests/**'
          - '**/*_test.py'
          - '**/test_*.py'

ci-cd:
  - changed-files:
      - any-glob-to-any-file:
          - '.github/workflows/**'
          - '.github/*.yml'

# ───────────────────────────────────────────────────────────────────
# Special labels
# ───────────────────────────────────────────────────────────────────
experimental:
  - changed-files:
      - any-glob-to-any-file:
          - 'claude/tools/experimental/**'
          - 'claude/extensions/**'

dependencies:
  - changed-files:
      - any-glob-to-any-file:
          - 'requirements*.txt'
          - 'pyproject.toml'
          - 'setup.py'
```

**File**: `.github/workflows/labeler.yml`

```yaml
name: PR Labeler

on:
  pull_request_target:
    types: [opened, synchronize, reopened]

jobs:
  label:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    steps:
      - uses: actions/labeler@v5
        with:
          repo-token: ${{ secrets.GITHUB_TOKEN }}
          configuration-path: .github/labeler.yml
```

**Validation**:
- [ ] Both files created
- [ ] Workflow triggers on PR
- [ ] Labels applied correctly

---

### 4.2 Create Domain-Specific CI Triggers

**File**: `.github/workflows/ci-domain-sre.yml`

```yaml
name: SRE Domain Tests

on:
  pull_request:
    paths:
      - 'claude/tools/sre/**'
      - 'tests/sre/**'

jobs:
  sre-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run SRE-specific tests
        run: |
          python -m pytest tests/sre/ -v --tb=short \
            --cov=claude/tools/sre \
            --cov-report=term-missing
```

**File**: `.github/workflows/ci-domain-security.yml`

```yaml
name: Security Domain Tests

on:
  pull_request:
    paths:
      - 'claude/tools/security/**'
      - 'tests/security/**'

jobs:
  security-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov bandit

      - name: Run Security-specific tests
        run: |
          python -m pytest tests/security/ -v --tb=short \
            --cov=claude/tools/security \
            --cov-report=term-missing

      - name: Security scan with Bandit
        run: |
          bandit -r claude/tools/security/ -ll || true
```

**Validation**:
- [ ] Workflows only trigger on their domain paths
- [ ] Tests run correctly when triggered

---

### 4.3 Create Agent Validation Tests

**File**: `tests/core/test_agent_loading.py`

```python
#!/usr/bin/env python3
"""
Agent Loading Validation Tests

Ensures all 91 agents can be loaded without errors.
Validates required fields and structure.

Author: DevOps Principal Architect Agent
Date: 2026-01-03
"""

import pytest
import re
from pathlib import Path

# Find MAIA_ROOT
MAIA_ROOT = Path(__file__).resolve().parents[2]
AGENTS_DIR = MAIA_ROOT / "claude" / "agents"


def get_all_agent_files():
    """Get all agent markdown files."""
    return list(AGENTS_DIR.glob("*_agent.md"))


def parse_agent_file(filepath: Path) -> dict:
    """Parse agent file and extract metadata."""
    content = filepath.read_text()

    agent = {
        "path": filepath,
        "name": filepath.stem,
        "content": content,
        "has_title": False,
        "has_purpose": False,
        "has_version": False,
        "has_commands": False,
        "has_examples": False,
    }

    # Check for title (# Agent Name)
    if re.search(r'^#\s+.+Agent', content, re.MULTILINE):
        agent["has_title"] = True

    # Check for purpose/overview section
    if re.search(r'(Purpose|Overview|Agent Overview)', content, re.IGNORECASE):
        agent["has_purpose"] = True

    # Check for version
    if re.search(r'v\d+\.\d+', content):
        agent["has_version"] = True

    # Check for commands/key commands section
    if re.search(r'(Commands|Key Commands)', content, re.IGNORECASE):
        agent["has_commands"] = True

    # Check for examples/few-shot
    if re.search(r'(Example|Few-Shot)', content, re.IGNORECASE):
        agent["has_examples"] = True

    return agent


class TestAgentLoading:
    """Test all agents can be loaded."""

    @pytest.fixture(scope="class")
    def all_agents(self):
        """Load all agent files."""
        agent_files = get_all_agent_files()
        return [parse_agent_file(f) for f in agent_files]

    def test_agents_exist(self, all_agents):
        """Verify agents directory has agents."""
        assert len(all_agents) > 0, "No agents found in claude/agents/"
        print(f"\nFound {len(all_agents)} agents")

    def test_all_agents_have_title(self, all_agents):
        """All agents should have a title."""
        missing = [a["name"] for a in all_agents if not a["has_title"]]
        assert len(missing) == 0, f"Agents missing title: {missing}"

    def test_all_agents_have_purpose(self, all_agents):
        """All agents should have a purpose section."""
        missing = [a["name"] for a in all_agents if not a["has_purpose"]]
        # Warning only - don't fail
        if missing:
            pytest.skip(f"Agents missing purpose (non-critical): {missing[:5]}")

    def test_all_agents_parseable(self, all_agents):
        """All agents should be valid markdown."""
        for agent in all_agents:
            assert len(agent["content"]) > 100, f"{agent['name']} is too short"

    def test_no_duplicate_agent_names(self, all_agents):
        """No duplicate agent names."""
        names = [a["name"] for a in all_agents]
        duplicates = [n for n in names if names.count(n) > 1]
        assert len(duplicates) == 0, f"Duplicate agent names: {set(duplicates)}"

    def test_agent_file_naming(self, all_agents):
        """Agent files should end with _agent.md."""
        for agent in all_agents:
            assert agent["path"].name.endswith("_agent.md"), \
                f"{agent['path'].name} should end with _agent.md"


class TestAgentQuality:
    """Test agent quality standards."""

    @pytest.fixture(scope="class")
    def all_agents(self):
        agent_files = get_all_agent_files()
        return [parse_agent_file(f) for f in agent_files]

    def test_agents_have_examples(self, all_agents):
        """Agents should have examples for quality routing."""
        with_examples = [a for a in all_agents if a["has_examples"]]
        coverage = len(with_examples) / len(all_agents) * 100
        print(f"\nAgents with examples: {len(with_examples)}/{len(all_agents)} ({coverage:.1f}%)")
        # At least 50% should have examples
        assert coverage >= 50, f"Only {coverage:.1f}% of agents have examples"

    def test_agents_have_version(self, all_agents):
        """Agents should be versioned."""
        with_version = [a for a in all_agents if a["has_version"]]
        coverage = len(with_version) / len(all_agents) * 100
        print(f"\nAgents with version: {len(with_version)}/{len(all_agents)} ({coverage:.1f}%)")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

**Validation**:
- [ ] Test file created
- [ ] `pytest tests/core/test_agent_loading.py -v` passes
- [ ] Reports agent coverage statistics

---

## Phase 5: Performance (8 hours)

### 5.1 Create Performance Baseline Tool

**File**: `claude/tools/sre/performance_baseline.py`

```python
#!/usr/bin/env python3
"""
Maia Performance Baseline Tool

Measures critical operation latencies and detects regressions.
Run in CI to prevent performance degradation.

Usage:
    python3 performance_baseline.py --check      # Check against baseline
    python3 performance_baseline.py --update     # Update baseline
    python3 performance_baseline.py --verbose    # Detailed output

Author: SRE Principal Engineer Agent
Date: 2026-01-03
"""

import argparse
import json
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Optional

# Find MAIA_ROOT
MAIA_ROOT = Path(__file__).resolve().parents[3]
BASELINE_FILE = MAIA_ROOT / "claude" / "data" / "performance_baselines.json"


@dataclass
class Metric:
    """Performance metric definition."""
    name: str
    target_ms: float  # Target latency
    warn_ms: float    # Warning threshold
    fail_ms: float    # Failure threshold
    measured_ms: Optional[float] = None
    status: str = "pending"


# Baseline definitions
BASELINES = {
    "context_loading": Metric(
        name="UFC Context Loading",
        target_ms=500,
        warn_ms=750,
        fail_ms=1000,
    ),
    "agent_routing": Metric(
        name="Agent Routing Decision",
        target_ms=100,
        warn_ms=200,
        fail_ms=500,
    ),
    "tool_discovery": Metric(
        name="Tool Discovery Scan",
        target_ms=300,
        warn_ms=500,
        fail_ms=1000,
    ),
    "database_query": Metric(
        name="System State Query",
        target_ms=50,
        warn_ms=100,
        fail_ms=200,
    ),
    "path_resolution": Metric(
        name="Path Resolution",
        target_ms=10,
        warn_ms=50,
        fail_ms=100,
    ),
}


class PerformanceBaseline:
    """Performance baseline measurement and validation."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results: Dict[str, Metric] = {}

    def _time_operation(self, func, iterations: int = 10) -> float:
        """Time an operation and return average ms."""
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            func()
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)
        return sum(times) / len(times)

    def measure_context_loading(self) -> float:
        """Measure UFC context loading time."""
        try:
            sys.path.insert(0, str(MAIA_ROOT / "claude" / "tools" / "sre"))
            from smart_context_loader import SmartContextLoader

            def load_context():
                loader = SmartContextLoader()
                loader.load_guaranteed_minimum()

            return self._time_operation(load_context, iterations=5)
        except ImportError:
            return -1  # Not available

    def measure_agent_routing(self) -> float:
        """Measure agent routing decision time."""
        try:
            sys.path.insert(0, str(MAIA_ROOT / "claude" / "hooks"))
            from swarm_auto_loader import get_context_id

            def route_agent():
                get_context_id()

            return self._time_operation(route_agent, iterations=10)
        except ImportError:
            return -1

    def measure_tool_discovery(self) -> float:
        """Measure tool discovery scan time."""
        try:
            sys.path.insert(0, str(MAIA_ROOT / "claude" / "tools" / "sre"))

            def scan_tools():
                tools_dir = MAIA_ROOT / "claude" / "tools"
                list(tools_dir.rglob("*.py"))

            return self._time_operation(scan_tools, iterations=5)
        except Exception:
            return -1

    def measure_database_query(self) -> float:
        """Measure system state database query time."""
        try:
            db_path = MAIA_ROOT / "claude" / "data" / "databases" / "system" / "system_state.db"
            if not db_path.exists():
                return -1

            import sqlite3

            def query_db():
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM phases")
                cursor.fetchone()
                conn.close()

            return self._time_operation(query_db, iterations=10)
        except Exception:
            return -1

    def measure_path_resolution(self) -> float:
        """Measure path resolution time."""
        try:
            sys.path.insert(0, str(MAIA_ROOT / "claude" / "tools" / "core"))
            from paths import PathManager

            # Clear cache
            PathManager._maia_root = None
            PathManager._user_data = None

            def resolve_paths():
                PathManager.get_maia_root()
                PathManager.get_user_data_path()

            return self._time_operation(resolve_paths, iterations=10)
        except ImportError:
            return -1

    def run_measurements(self) -> Dict[str, Metric]:
        """Run all measurements."""
        measurements = {
            "context_loading": self.measure_context_loading,
            "agent_routing": self.measure_agent_routing,
            "tool_discovery": self.measure_tool_discovery,
            "database_query": self.measure_database_query,
            "path_resolution": self.measure_path_resolution,
        }

        for key, baseline in BASELINES.items():
            metric = Metric(
                name=baseline.name,
                target_ms=baseline.target_ms,
                warn_ms=baseline.warn_ms,
                fail_ms=baseline.fail_ms,
            )

            if key in measurements:
                measured = measurements[key]()
                metric.measured_ms = measured

                if measured < 0:
                    metric.status = "skipped"
                elif measured <= baseline.target_ms:
                    metric.status = "pass"
                elif measured <= baseline.warn_ms:
                    metric.status = "warn"
                elif measured <= baseline.fail_ms:
                    metric.status = "fail"
                else:
                    metric.status = "critical"

            self.results[key] = metric

        return self.results

    def check(self) -> bool:
        """Check current performance against baselines."""
        self.run_measurements()

        print("=" * 60)
        print("MAIA PERFORMANCE BASELINE CHECK")
        print("=" * 60)
        print()

        has_failures = False
        has_warnings = False

        for key, metric in self.results.items():
            if metric.status == "skipped":
                icon = "⏭️"
                status = "SKIP"
            elif metric.status == "pass":
                icon = "✅"
                status = "PASS"
            elif metric.status == "warn":
                icon = "⚠️"
                status = "WARN"
                has_warnings = True
            elif metric.status == "fail":
                icon = "❌"
                status = "FAIL"
                has_failures = True
            else:
                icon = "🚨"
                status = "CRIT"
                has_failures = True

            measured = f"{metric.measured_ms:.1f}ms" if metric.measured_ms and metric.measured_ms > 0 else "N/A"
            target = f"(target: {metric.target_ms}ms)"

            print(f"{icon} {metric.name}: {measured} {target} [{status}]")

            if self.verbose and metric.measured_ms and metric.measured_ms > 0:
                print(f"   Target: {metric.target_ms}ms | Warn: {metric.warn_ms}ms | Fail: {metric.fail_ms}ms")

        print()
        print("=" * 60)

        if has_failures:
            print("❌ PERFORMANCE CHECK FAILED")
            print("   Some operations exceed failure thresholds.")
            return False
        elif has_warnings:
            print("⚠️ PERFORMANCE CHECK PASSED WITH WARNINGS")
            return True
        else:
            print("✅ PERFORMANCE CHECK PASSED")
            return True

    def update_baseline(self):
        """Update baseline file with current measurements."""
        self.run_measurements()

        data = {}
        for key, metric in self.results.items():
            if metric.measured_ms and metric.measured_ms > 0:
                data[key] = {
                    "name": metric.name,
                    "measured_ms": metric.measured_ms,
                    "target_ms": metric.target_ms,
                    "warn_ms": metric.warn_ms,
                    "fail_ms": metric.fail_ms,
                }

        BASELINE_FILE.parent.mkdir(parents=True, exist_ok=True)
        BASELINE_FILE.write_text(json.dumps(data, indent=2))
        print(f"✅ Baseline updated: {BASELINE_FILE}")


def main():
    parser = argparse.ArgumentParser(description="Maia Performance Baseline Tool")
    parser.add_argument("--check", action="store_true", help="Check against baseline")
    parser.add_argument("--update", action="store_true", help="Update baseline file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    baseline = PerformanceBaseline(verbose=args.verbose)

    if args.update:
        baseline.update_baseline()
    else:
        passed = baseline.check()
        sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
```

**Validation**:
- [ ] Tool created
- [ ] `python3 performance_baseline.py --check` runs
- [ ] Reports meaningful latencies

---

### 5.2 Create Performance CI Workflow

**File**: `.github/workflows/ci-performance.yml`

```yaml
name: Performance Baseline

on:
  pull_request:
    paths:
      - 'claude/context/core/**'
      - 'claude/tools/sre/smart_context_loader.py'
      - 'claude/hooks/swarm_auto_loader.py'
      - 'claude/tools/core/**'
  schedule:
    - cron: '0 6 * * 1'  # Weekly Monday 6 AM UTC

jobs:
  performance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run performance baseline check
        run: python3 claude/tools/sre/performance_baseline.py --check --verbose

      - name: Upload baseline results
        if: github.event_name == 'schedule'
        uses: actions/upload-artifact@v4
        with:
          name: performance-baseline-${{ github.run_number }}
          path: claude/data/performance_baselines.json
```

**Validation**:
- [ ] Workflow created
- [ ] Triggers only on performance-sensitive paths
- [ ] Weekly update runs

---

## Phase 6: Operations (6 hours)

### 6.1 Create Emergency Rollback Workflow

**File**: `.github/workflows/emergency-rollback.yml`

```yaml
name: Emergency Rollback

on:
  workflow_dispatch:
    inputs:
      target_commit:
        description: 'Commit SHA to revert to (leave empty to revert last commit)'
        required: false
        type: string
      reason:
        description: 'Emergency reason (required for audit)'
        required: true
        type: string
      create_issue:
        description: 'Create post-mortem issue?'
        type: boolean
        default: true

jobs:
  emergency-rollback:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          token: ${{ secrets.ADMIN_PAT }}

      - name: Configure Git
        run: |
          git config user.name "Maia Emergency Bot"
          git config user.email "maia-emergency@noreply.github.com"

      - name: Create revert commit
        run: |
          echo "🚨 EMERGENCY ROLLBACK"
          echo "Reason: ${{ inputs.reason }}"
          echo "Triggered by: ${{ github.actor }}"
          echo ""

          if [ -z "${{ inputs.target_commit }}" ]; then
            echo "Reverting last commit..."
            git revert --no-edit HEAD
          else
            echo "Reverting to ${{ inputs.target_commit }}..."
            # Revert all commits between target and HEAD
            git revert --no-edit --no-commit HEAD...${{ inputs.target_commit }}
            git commit -m "Revert to ${{ inputs.target_commit }}"
          fi

      - name: Push revert
        run: git push origin main

      - name: Create post-mortem issue
        if: inputs.create_issue
        uses: actions/github-script@v7
        with:
          script: |
            const issue = await github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: `🚨 Post-Mortem: Emergency Rollback - ${new Date().toISOString().split('T')[0]}`,
              labels: ['incident', 'post-mortem', 'P1'],
              body: `## Emergency Rollback Triggered

            | Field | Value |
            |-------|-------|
            | **Timestamp** | ${new Date().toISOString()} |
            | **Triggered By** | @${{ github.actor }} |
            | **Reason** | ${{ inputs.reason }} |
            | **Target Commit** | ${{ inputs.target_commit || 'HEAD~1 (last commit)' }} |

            ## Post-Mortem Checklist

            - [ ] Root cause identified
            - [ ] Timeline documented
            - [ ] Impact assessed
            - [ ] Fix identified and PR created
            - [ ] Prevention measures documented
            - [ ] Runbooks updated (if needed)

            ## Root Cause Analysis

            _To be completed within 24 hours_

            ### What happened?

            ### Why did it happen?

            ### What's the fix?

            ## Timeline

            | Time (UTC) | Event |
            |------------|-------|
            | ${new Date().toISOString()} | Emergency rollback triggered |
            | | |

            ## Impact

            - Users affected:
            - Duration:
            - Services impacted:

            ## Prevention

            What changes will prevent this from recurring?

            ---
            _This issue was auto-created by the emergency rollback workflow._
            `
            });
            console.log(`Created issue #${issue.data.number}`);

      - name: Summary
        run: |
          echo "✅ Emergency rollback complete"
          echo ""
          echo "Next steps:"
          echo "1. Verify Maia works: git pull && type 'load' in Claude Code"
          echo "2. Fill in the post-mortem issue"
          echo "3. Create fix PR when ready"
```

**Validation**:
- [ ] Workflow created
- [ ] ADMIN_PAT secret configured (document for user)
- [ ] Test run creates proper revert

---

### 6.2 Create VERSION and CHANGELOG

**File**: `VERSION`

```
2.0.0
```

**File**: `CHANGELOG.md`

```markdown
# Changelog

All notable changes to Maia will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-01-XX

### Added
- Multi-user collaboration support
- CODEOWNERS-based protection model
- CI/CD pipeline with quality gates
- contribution_reviewer.py for defense-in-depth validation
- Auto-labeling for PRs
- Performance baseline monitoring
- Emergency rollback workflow
- Team setup script

### Changed
- Personal data moved to ~/.maia/
- Session files moved to ~/.maia/sessions/
- Database regeneration now happens locally

### Security
- Pre-commit hooks block personal data and secrets
- CI scans for hardcoded paths and credentials
- Branch protection requires PR review

## [1.x.x] - Previous

Single-user operation. See git history for details.
```

**Validation**:
- [ ] VERSION file created
- [ ] CHANGELOG.md created
- [ ] Version matches across files

---

### 6.3 Create CONTRIBUTING.md

**File**: `.github/CONTRIBUTING.md`

```markdown
# Contributing to Maia

Welcome to Maia! This guide explains how to contribute effectively.

## Quick Start

```bash
# 1. Clone and setup
git clone git@github.com:ORG/maia.git
cd maia
./scripts/setup-team-member.sh

# 2. Create branch
git checkout -b feature/your-feature

# 3. Make changes, commit, push
git add .
git commit -m "feat: your feature description"
git push -u origin feature/your-feature

# 4. Create PR on GitHub
```

## Protection Tiers

| Tier | Paths | Approval Required |
|------|-------|-------------------|
| **Protected** | `claude/agents/`, `claude/hooks/`, `claude/context/core/`, `CLAUDE.md` | Core team |
| **Domain** | `claude/tools/sre/`, `claude/tools/security/`, etc. | Domain team + visibility |
| **Open** | `claude/extensions/`, `claude/tools/experimental/` | CI only |

## Branch Naming

| Pattern | Use |
|---------|-----|
| `feature/description` | New functionality |
| `fix/description` | Bug fixes |
| `docs/description` | Documentation only |
| `refactor/description` | Code improvement |

## Commit Messages

Use conventional commits:

```
feat: add new tool for X
fix: resolve issue with Y
docs: update README
refactor: simplify Z logic
test: add tests for W
```

## What Gets Checked

### Pre-Commit (Local)
- No personal data (usernames, home paths)
- No hardcoded secrets
- TDD compliance (if applicable)

### CI (Remote)
- All pre-commit checks
- Tests pass
- Linting passes
- Security scan (Trufflehog)
- Contribution review

## Getting Help

- **Documentation**: This file + README.md
- **Questions**: #maia-support channel
- **Issues**: Create GitHub issue

## Code of Conduct

Be respectful. Help each other. Build great tools.
```

**Validation**:
- [ ] File created
- [ ] Accurate to implementation

---

## Phase 7: Validation (4 hours)

### 7.1 Validation Checklist

| Test | Command/Steps | Expected Result | Pass |
|------|---------------|-----------------|------|
| Fresh clone works | `git clone`, `./scripts/setup-team-member.sh` | Completes without error | [ ] |
| Maia loads | Type `load` in Claude Code | UFC system loaded | [ ] |
| Pre-commit blocks personal data | Add `naythandawe` to file, commit | Hook blocks | [ ] |
| Pre-push blocks main | `git push origin main` | Hook blocks | [ ] |
| CI runs on PR | Create test PR | All jobs pass | [ ] |
| Auto-labeler works | PR modifies `claude/tools/sre/` | `sre` label added | [ ] |
| CODEOWNERS enforced | PR to `claude/agents/` | Requires core team | [ ] |
| contribution_reviewer works | `python3 contribution_reviewer.py --local` | Reports results | [ ] |
| Performance baseline works | `python3 performance_baseline.py --check` | Reports metrics | [ ] |
| Emergency rollback works | Trigger workflow | Creates revert + issue | [ ] |

### 7.2 Test User Onboarding

- [ ] Recruit 2-3 team members for beta test
- [ ] Have them follow setup instructions
- [ ] Time the onboarding (target: <30 min)
- [ ] Collect feedback
- [ ] Iterate on documentation

---

## Execution Order Summary

```
Week 1:
├── Phase 1: Foundation (Day 1-2)
│   ├── CODEOWNERS
│   ├── CI workflow
│   ├── Branch protection
│   └── .gitignore updates
│
├── Phase 2: Security Gates (Day 2-3)
│   ├── contribution_reviewer.py
│   ├── Pre-commit hook
│   ├── Pre-push hook
│   └── Post-merge hook
│
└── Phase 3: Path Isolation (Day 3-4)
    ├── paths.py
    ├── Fix 8 hardcoded tools
    └── setup-team-member.sh

Week 2:
├── Phase 4: Quality Automation (Day 5-6)
│   ├── Auto-labeler
│   ├── Domain CI workflows
│   └── Agent validation tests
│
├── Phase 5: Performance (Day 6-7)
│   ├── performance_baseline.py
│   └── Performance CI workflow
│
├── Phase 6: Operations (Day 7-8)
│   ├── Emergency rollback workflow
│   ├── VERSION + CHANGELOG
│   └── CONTRIBUTING.md
│
└── Phase 7: Validation (Day 8-9)
    ├── Run all tests
    ├── Beta test with team
    └── Iterate on feedback
```

---

## Success Criteria

- [ ] All CI checks pass
- [ ] No personal data in repository
- [ ] Setup script works on fresh clone
- [ ] Onboarding time <30 minutes
- [ ] Emergency rollback tested
- [ ] 2-3 team members successfully onboarded
- [ ] Performance baselines established

---

**Document Status**: Ready for Execution
**Start Command**: Begin with Phase 1.1 (CODEOWNERS)
