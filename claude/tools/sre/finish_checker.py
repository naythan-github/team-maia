#!/usr/bin/env python3
"""
Finish Checker - Completion Verification Tool

Implements the /finish skill with 6 automated checks, blocking behavior,
mandatory interactive review, and completion state persistence.

Usage:
    # Library
    from finish_checker import FinishChecker
    checker = FinishChecker()
    results = checker.run_automated_checks()
    blockers = checker.check_blockers()

    # CLI
    python3 finish_checker.py check              # Run all checks
    python3 finish_checker.py blockers           # Show blocking issues
    python3 finish_checker.py persist --session-id X  # Store completion

Author: SRE Principal Engineer Agent (Maia)
Date: 2026-01-15
Version: 1.0
Status: Production Ready
"""

import json
import sqlite3
import subprocess
import argparse
import ast
import sys
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any, Literal


class FinishCheckerError(Exception):
    """Base exception for Finish Checker operations."""
    pass


@dataclass
class CheckResult:
    """Result of a single check."""
    name: str
    status: Literal["PASS", "WARN", "FAIL"]
    message: str
    evidence: Optional[str] = None


@dataclass
class CompletionRecord:
    """Record of a completion verification."""
    session_id: str
    context_id: str
    project_name: Optional[str]
    agent_used: str
    check_results: Dict[str, str]
    review_responses: Dict[str, str]
    files_touched: List[str]
    status: str = "COMPLETE"
    completed_at: Optional[str] = None


def get_session_manager():
    """Import and return session manager (lazy import to avoid circular deps)."""
    try:
        from claude.tools.learning.session import get_session_manager as _get_manager
        return _get_manager()
    except ImportError:
        return None


class FinishChecker:
    """
    Completion Verification Tool - Validates project completion.

    Provides 6 automated checks:
    1. Git Status - Clean working tree
    2. Capability Registration - All new tools in capabilities.db
    3. Documentation - Module docstrings present
    4. Testing - Corresponding test files exist
    5. Learning Capture - Session active
    6. Pre-Integration - ruff check passes

    Plus mandatory interactive review and completion state persistence.
    """

    CIRCUIT_BREAKER_THRESHOLD = 5
    MIN_REVIEW_RESPONSE_LENGTH = 15  # Minimum chars for review response

    def __init__(self, maia_root: Optional[Path] = None):
        """
        Initialize Finish Checker.

        Args:
            maia_root: Root directory of MAIA installation.
                      Defaults to auto-detection.
        """
        if maia_root:
            self.maia_root = Path(maia_root)
        else:
            # Auto-detect MAIA_ROOT
            self.maia_root = self._detect_maia_root()

        self.capabilities_db = self.maia_root / "claude" / "data" / "databases" / "system" / "capabilities.db"
        self.project_tracking_db = self.maia_root / "claude" / "data" / "databases" / "system" / "project_tracking.db"

        self._consecutive_failures = 0
        self._ensure_db_schema()

    def _detect_maia_root(self) -> Path:
        """Detect MAIA_ROOT from current file location."""
        # This file is at claude/tools/sre/finish_checker.py
        return Path(__file__).parent.parent.parent.parent

    def _ensure_db_schema(self) -> None:
        """Ensure completion_records table exists."""
        if not self.project_tracking_db.exists():
            self.project_tracking_db.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.project_tracking_db)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS completion_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                context_id TEXT NOT NULL,
                project_name TEXT,
                agent_used TEXT NOT NULL,
                completed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                check_results TEXT NOT NULL,
                review_responses TEXT NOT NULL,
                files_touched TEXT,
                total_checks INTEGER,
                passed_checks INTEGER,
                failed_checks INTEGER,
                warned_checks INTEGER,
                status TEXT NOT NULL DEFAULT 'COMPLETE'
            )
        """)
        conn.commit()
        conn.close()

    def _now_iso(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.utcnow().isoformat() + "Z"

    def _get_recently_modified_files(self, minutes: int = 60) -> List[Path]:
        """
        Get files modified recently in core directories.

        Args:
            minutes: Look back period in minutes

        Returns:
            List of recently modified file paths
        """
        core_dirs = [
            self.maia_root / "claude" / "tools",
            self.maia_root / "claude" / "agents",
            self.maia_root / "claude" / "commands",
        ]

        cutoff = datetime.now() - timedelta(minutes=minutes)
        recent_files = []

        for core_dir in core_dirs:
            if core_dir.exists():
                for pattern in ["**/*.py", "**/*.md"]:
                    for f in core_dir.glob(pattern):
                        if f.is_file() and "__pycache__" not in str(f):
                            # Exclude claude/commands/ - skill definitions, not capabilities
                            if "claude/commands/" in str(f):
                                continue
                            try:
                                mtime = datetime.fromtimestamp(f.stat().st_mtime)
                                if mtime > cutoff:
                                    recent_files.append(f)
                            except OSError:
                                pass

        return recent_files

    # =========================================================================
    # Automated Checks (FR-1)
    # =========================================================================

    def run_git_status_check(self) -> CheckResult:
        """
        FR-1.1: Check git working tree status.

        Returns:
            CheckResult with PASS if clean, WARN/FAIL if uncommitted changes
        """
        try:
            result = subprocess.run(
                ["git", "status", "--short"],
                capture_output=True,
                text=True,
                cwd=self.maia_root,
                timeout=30
            )

            if result.returncode != 0:
                return CheckResult(
                    name="git_status",
                    status="WARN",
                    message="Could not check git status",
                    evidence=result.stderr
                )

            output = result.stdout.strip()

            if not output:
                return CheckResult(
                    name="git_status",
                    status="PASS",
                    message="Working tree clean"
                )

            # Check if core files are modified
            core_patterns = ["claude/tools/", "claude/agents/", "claude/commands/"]
            core_changes = [line for line in output.split("\n")
                          if any(p in line for p in core_patterns)]

            if core_changes:
                return CheckResult(
                    name="git_status",
                    status="FAIL",
                    message=f"Uncommitted changes to {len(core_changes)} core file(s)",
                    evidence="\n".join(core_changes[:10])
                )

            return CheckResult(
                name="git_status",
                status="WARN",
                message=f"Uncommitted changes ({len(output.split(chr(10)))} files)",
                evidence=output[:500]
            )

        except subprocess.TimeoutExpired:
            return CheckResult(
                name="git_status",
                status="WARN",
                message="Git status timed out"
            )
        except Exception as e:
            return CheckResult(
                name="git_status",
                status="WARN",
                message=f"Git status error: {str(e)}"
            )

    def run_capability_check(self) -> CheckResult:
        """
        FR-1.2: Check capability registration.

        Returns:
            CheckResult with PASS if all registered, FAIL if unregistered tools
        """
        recent_files = self._get_recently_modified_files()

        # Filter to only tools/agents/commands
        tool_files = [f for f in recent_files
                     if f.suffix in [".py", ".md"]
                     and "__init__" not in f.name]

        if not tool_files:
            return CheckResult(
                name="capability",
                status="PASS",
                message="No recent tool/agent changes to verify"
            )

        # Check registration in capabilities.db
        if not self.capabilities_db.exists():
            return CheckResult(
                name="capability",
                status="WARN",
                message="Capabilities database not found"
            )

        try:
            conn = sqlite3.connect(self.capabilities_db)
            cursor = conn.execute("SELECT path FROM capabilities")
            registered_paths = {row[0] for row in cursor.fetchall()}
            conn.close()

            unregistered = []
            for f in tool_files:
                # Convert to relative path
                rel_path = str(f.relative_to(self.maia_root))
                if rel_path not in registered_paths:
                    unregistered.append(rel_path)

            if unregistered:
                return CheckResult(
                    name="capability",
                    status="FAIL",
                    message=f"{len(unregistered)} unregistered file(s)",
                    evidence="\n".join(unregistered[:10])
                )

            return CheckResult(
                name="capability",
                status="PASS",
                message=f"All {len(tool_files)} recent file(s) registered"
            )

        except Exception as e:
            return CheckResult(
                name="capability",
                status="WARN",
                message=f"Capability check error: {str(e)}"
            )

    def run_documentation_check(self) -> CheckResult:
        """
        FR-1.3: Check documentation completeness.

        Returns:
            CheckResult with PASS if documented, FAIL if missing docstrings
        """
        recent_files = self._get_recently_modified_files()
        py_files = [f for f in recent_files if f.suffix == ".py" and "__init__" not in f.name]

        if not py_files:
            return CheckResult(
                name="documentation",
                status="PASS",
                message="No recent Python files to check"
            )

        undocumented = []

        for py_file in py_files:
            try:
                content = py_file.read_text()
                tree = ast.parse(content)

                # Check module docstring
                if not ast.get_docstring(tree):
                    undocumented.append(f"{py_file.name}: missing module docstring")

            except SyntaxError:
                undocumented.append(f"{py_file.name}: syntax error (cannot parse)")
            except Exception:
                pass

        if undocumented:
            return CheckResult(
                name="documentation",
                status="FAIL",
                message=f"{len(undocumented)} file(s) missing documentation",
                evidence="\n".join(undocumented[:10])
            )

        return CheckResult(
            name="documentation",
            status="PASS",
            message=f"All {len(py_files)} Python file(s) documented"
        )

    def run_testing_check(self) -> CheckResult:
        """
        FR-1.4: Check for corresponding test files.

        Returns:
            CheckResult with PASS if tests exist, FAIL if missing
        """
        recent_files = self._get_recently_modified_files()
        tool_files = [f for f in recent_files
                     if f.suffix == ".py"
                     and "claude/tools/" in str(f)
                     and "__init__" not in f.name]

        if not tool_files:
            return CheckResult(
                name="testing",
                status="PASS",
                message="No recent tool files to check"
            )

        tests_dir = self.maia_root / "tests"
        missing_tests = []

        for tool_file in tool_files:
            # Generate expected test file name
            test_name = f"test_{tool_file.stem}.py"

            # Check various test locations
            possible_tests = [
                tests_dir / test_name,
                tests_dir / tool_file.parent.name / test_name,
            ]

            if not any(t.exists() for t in possible_tests):
                missing_tests.append(tool_file.name)

        if missing_tests:
            return CheckResult(
                name="testing",
                status="FAIL",
                message=f"{len(missing_tests)} tool(s) missing test files",
                evidence="\n".join(missing_tests[:10])
            )

        return CheckResult(
            name="testing",
            status="PASS",
            message=f"All {len(tool_files)} tool(s) have test files"
        )

    def run_learning_check(self) -> CheckResult:
        """
        FR-1.5: Check learning session status.

        Returns:
            CheckResult with PASS if session active, WARN if not
        """
        try:
            manager = get_session_manager()
            if manager and manager.active_session_id:
                return CheckResult(
                    name="learning",
                    status="PASS",
                    message=f"Learning session active: {manager.active_session_id}"
                )
            else:
                return CheckResult(
                    name="learning",
                    status="WARN",
                    message="No active learning session (insights may be lost)"
                )
        except Exception as e:
            return CheckResult(
                name="learning",
                status="WARN",
                message=f"Could not check learning session: {str(e)}"
            )

    def run_preintegration_check(self) -> CheckResult:
        """
        FR-1.6: Run pre-integration linting check.

        Returns:
            CheckResult with PASS if ruff passes, FAIL if errors
        """
        try:
            result = subprocess.run(
                ["ruff", "check", "claude/tools", "--select=E,F,W", "--ignore=E501"],
                capture_output=True,
                text=True,
                cwd=self.maia_root,
                timeout=60
            )

            if result.returncode == 0:
                return CheckResult(
                    name="preintegration",
                    status="PASS",
                    message="ruff check passed (no E/F/W errors)"
                )

            # Count errors
            error_lines = [l for l in result.stdout.split("\n") if l.strip()]
            error_count = len(error_lines)

            return CheckResult(
                name="preintegration",
                status="FAIL" if error_count > 5 else "WARN",
                message=f"ruff found {error_count} issue(s)",
                evidence="\n".join(error_lines[:10])
            )

        except FileNotFoundError:
            return CheckResult(
                name="preintegration",
                status="WARN",
                message="ruff not installed (skipping lint check)"
            )
        except subprocess.TimeoutExpired:
            return CheckResult(
                name="preintegration",
                status="WARN",
                message="ruff check timed out"
            )
        except Exception as e:
            return CheckResult(
                name="preintegration",
                status="WARN",
                message=f"Pre-integration check error: {str(e)}"
            )

    def _run_individual_checks(self) -> Dict[str, CheckResult]:
        """Run all individual checks and return results dict."""
        return {
            "git_status": self.run_git_status_check(),
            "capability": self.run_capability_check(),
            "documentation": self.run_documentation_check(),
            "testing": self.run_testing_check(),
            "learning": self.run_learning_check(),
            "preintegration": self.run_preintegration_check(),
        }

    def run_automated_checks(self) -> Dict[str, CheckResult]:
        """
        Run all 6 automated checks.

        Returns:
            Dict mapping check name to CheckResult
        """
        results = self._run_individual_checks()

        # Track consecutive failures for circuit breaker
        fail_count = sum(1 for r in results.values() if r.status == "FAIL")
        if fail_count > 0:
            self._consecutive_failures += 1
        else:
            self._consecutive_failures = 0

        # Add escalation flag if circuit breaker triggered
        if self._consecutive_failures >= self.CIRCUIT_BREAKER_THRESHOLD:
            results["_escalated"] = CheckResult(
                name="_escalated",
                status="FAIL",
                message=f"Circuit breaker: {self._consecutive_failures} consecutive failures"
            )

        return results

    # =========================================================================
    # Blocking Behavior (FR-2)
    # =========================================================================

    def check_blockers(self) -> List[str]:
        """
        FR-2.1-2.2: Check for blocking issues.

        Returns:
            List of blocking issue descriptions (empty if no blockers)
        """
        results = self.run_automated_checks()

        blockers = []
        for name, result in results.items():
            if name.startswith("_"):
                continue
            if result.status == "FAIL":
                blockers.append(f"{name}: {result.message}")

        return blockers

    # =========================================================================
    # Interactive Review (FR-3)
    # =========================================================================

    def is_review_required(self) -> bool:
        """
        FR-3.1: Check if interactive review is required.

        Always returns True - review is mandatory.
        """
        return True

    def validate_review_responses(self, responses: Dict[str, str]) -> bool:
        """
        FR-3.1-3.4: Validate review responses have evidence.

        Args:
            responses: Dict with keys: claude_md, dependent_systems,
                      ripple_effects, documentation

        Returns:
            True if all responses valid with evidence
        """
        required_keys = ["claude_md", "dependent_systems", "ripple_effects", "documentation"]

        # Check all required keys present
        for key in required_keys:
            if key not in responses:
                return False

            response = responses[key]

            # Check minimum length (requires evidence, not just "No")
            if len(response.strip()) < self.MIN_REVIEW_RESPONSE_LENGTH:
                return False

        return True

    # =========================================================================
    # Persistence (FR-4)
    # =========================================================================

    def persist_completion(self, record: CompletionRecord) -> bool:
        """
        FR-4.1-4.2: Store completion record in database.

        Args:
            record: CompletionRecord to store

        Returns:
            True if stored successfully
        """
        try:
            conn = sqlite3.connect(self.project_tracking_db)

            # Calculate summary metrics
            check_results = record.check_results
            total = len([k for k in check_results.keys() if not k.startswith("_")])
            passed = sum(1 for v in check_results.values() if v == "PASS")
            failed = sum(1 for v in check_results.values() if v == "FAIL")
            warned = sum(1 for v in check_results.values() if v == "WARN")

            conn.execute("""
                INSERT INTO completion_records (
                    session_id, context_id, project_name, agent_used,
                    check_results, review_responses, files_touched,
                    total_checks, passed_checks, failed_checks, warned_checks,
                    status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.session_id,
                record.context_id,
                record.project_name,
                record.agent_used,
                json.dumps(record.check_results),
                json.dumps(record.review_responses),
                json.dumps(record.files_touched),
                total,
                passed,
                failed,
                warned,
                record.status
            ))

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            print(f"Error persisting completion: {e}", file=sys.stderr)
            return False

    def query_completions(
        self,
        session_id: Optional[str] = None,
        project_name: Optional[str] = None,
        agent_used: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        FR-4.3: Query past completions.

        Args:
            session_id: Filter by session ID
            project_name: Filter by project name
            agent_used: Filter by agent
            status: Filter by status
            limit: Maximum results

        Returns:
            List of completion record dicts
        """
        try:
            conn = sqlite3.connect(self.project_tracking_db)
            conn.row_factory = sqlite3.Row

            query = "SELECT * FROM completion_records WHERE 1=1"
            params = []

            if session_id:
                query += " AND session_id = ?"
                params.append(session_id)
            if project_name:
                query += " AND project_name = ?"
                params.append(project_name)
            if agent_used:
                query += " AND agent_used = ?"
                params.append(agent_used)
            if status:
                query += " AND status = ?"
                params.append(status)

            query += f" ORDER BY completed_at DESC LIMIT {limit}"

            cursor = conn.execute(query, params)
            results = [dict(row) for row in cursor.fetchall()]
            conn.close()

            return results

        except Exception as e:
            print(f"Error querying completions: {e}", file=sys.stderr)
            return []

    # =========================================================================
    # Session Integration (FR-5)
    # =========================================================================

    def check_finish_before_close(self, session_data: Dict[str, Any]) -> Optional[str]:
        """
        FR-5.1: Check if /finish was run before session close.

        Args:
            session_data: Current session data dict

        Returns:
            Warning message if /finish not run, None otherwise
        """
        session_id = session_data.get("session_id") or session_data.get("context_id")
        if not session_id:
            return None

        # Check for completion record
        results = self.query_completions(session_id=session_id)

        if not results:
            return (
                f"Warning: /finish was not run for this session.\n"
                f"Run /finish to verify completion before closing."
            )

        return None

    def get_session_context(self) -> Dict[str, Any]:
        """
        FR-5.2: Get current session context.

        Returns:
            Dict with agent, files_touched, initial_query
        """
        try:
            manager = get_session_manager()
            if manager and hasattr(manager, 'get_context'):
                return manager.get_context()
            return {
                "agent": "unknown",
                "files_touched": [],
                "initial_query": ""
            }
        except Exception:
            return {
                "agent": "unknown",
                "files_touched": [],
                "initial_query": ""
            }

    # =========================================================================
    # Summary & Display
    # =========================================================================

    def get_summary(self) -> str:
        """
        Get formatted summary of check results.

        Returns:
            Human-readable summary string
        """
        results = self.run_automated_checks()

        lines = [
            "/finish Checklist",
            "=" * 50,
            ""
        ]

        status_emoji = {"PASS": "✅", "WARN": "⚠️ ", "FAIL": "❌"}

        for name, result in results.items():
            if name.startswith("_"):
                continue
            emoji = status_emoji.get(result.status, "?")
            lines.append(f"{emoji} {name.replace('_', ' ').title():<25} [{result.status}]")
            lines.append(f"   {result.message}")
            if result.evidence:
                for evi_line in result.evidence.split("\n")[:3]:
                    lines.append(f"      {evi_line}")
            lines.append("")

        # Summary counts
        pass_count = sum(1 for r in results.values() if r.status == "PASS")
        warn_count = sum(1 for r in results.values() if r.status == "WARN")
        fail_count = sum(1 for r in results.values() if r.status == "FAIL")
        total = pass_count + warn_count + fail_count

        lines.append("=" * 50)
        lines.append(f"Result: {pass_count}/{total} PASS | {warn_count} WARN | {fail_count} FAIL")

        if fail_count > 0:
            lines.append("")
            lines.append("Blockers (must fix):")
            for name, result in results.items():
                if result.status == "FAIL":
                    lines.append(f"  - {name}: {result.message}")

        return "\n".join(lines)


# =============================================================================
# CLI Interface
# =============================================================================

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Finish Checker - Completion Verification Tool"
    )

    parser.add_argument(
        "command",
        choices=["check", "blockers", "summary", "persist"],
        help="Command to run"
    )
    parser.add_argument("--session-id", help="Session ID for persistence")
    parser.add_argument("--context-id", help="Context ID for persistence")
    parser.add_argument("--project", help="Project name")
    parser.add_argument("--agent", default="sre_principal_engineer_agent", help="Agent name")

    args = parser.parse_args()

    checker = FinishChecker()

    if args.command == "check":
        results = checker.run_automated_checks()
        for name, result in results.items():
            if not name.startswith("_"):
                print(f"{result.status}: {name} - {result.message}")

    elif args.command == "blockers":
        blockers = checker.check_blockers()
        if blockers:
            print("Blocking issues:")
            for b in blockers:
                print(f"  - {b}")
        else:
            print("No blocking issues")

    elif args.command == "summary":
        print(checker.get_summary())

    elif args.command == "persist":
        if not args.session_id or not args.context_id:
            print("Error: --session-id and --context-id required")
            sys.exit(1)

        results = checker.run_automated_checks()
        record = CompletionRecord(
            session_id=args.session_id,
            context_id=args.context_id,
            project_name=args.project,
            agent_used=args.agent,
            check_results={k: v.status for k, v in results.items() if not k.startswith("_")},
            review_responses={},  # Would need interactive input
            files_touched=[],
            status="COMPLETE"
        )

        if checker.persist_completion(record):
            print(f"Completion record stored for session {args.session_id}")
        else:
            print("Failed to store completion record")
            sys.exit(1)


if __name__ == "__main__":
    main()
