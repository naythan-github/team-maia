"""
Tests for Finish Checker - Completion Verification Tool

Tests the FinishChecker class that validates project completion
with 6 automated checks, blocking behavior, and interactive review.

Sprint: /finish Skill Implementation
Phase: P1 - Test-First Design (TDD)

Created: 2026-01-15
"""

import pytest
import json
import sqlite3
from pathlib import Path
from unittest.mock import patch, MagicMock
from dataclasses import dataclass
from typing import Dict, List, Optional

# Import will fail initially (P1 - tests should fail until P3)
from claude.tools.sre.finish_checker import (
    FinishChecker,
    CheckResult,
    CompletionRecord,
    FinishCheckerError
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def tmp_maia_root(tmp_path):
    """Create a temporary MAIA_ROOT structure."""
    # Create directory structure
    (tmp_path / "claude" / "tools" / "sre").mkdir(parents=True)
    (tmp_path / "claude" / "agents").mkdir(parents=True)
    (tmp_path / "claude" / "commands").mkdir(parents=True)
    (tmp_path / "claude" / "data" / "databases" / "system").mkdir(parents=True)
    (tmp_path / "tests").mkdir(parents=True)

    # Create capabilities.db with schema
    db_path = tmp_path / "claude" / "data" / "databases" / "system" / "capabilities.db"
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE capabilities (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            path TEXT NOT NULL,
            category TEXT,
            purpose TEXT,
            keywords TEXT,
            status TEXT DEFAULT 'production'
        )
    """)
    conn.commit()
    conn.close()

    return tmp_path


@pytest.fixture
def checker(tmp_maia_root):
    """Create FinishChecker instance with temp root."""
    return FinishChecker(maia_root=tmp_maia_root)


@pytest.fixture
def mock_session():
    """Mock session manager for learning capture tests."""
    with patch('claude.tools.sre.finish_checker.get_session_manager') as mock:
        manager = MagicMock()
        manager.current_session = True
        manager.active_session_id = "test_session_123"
        mock.return_value = manager
        yield manager


@pytest.fixture
def db_path(tmp_maia_root):
    """Path to completion records database."""
    return tmp_maia_root / "claude" / "data" / "databases" / "system" / "project_tracking.db"


# =============================================================================
# TestAutomatedChecks - FR-1: 6 Automated Checks
# =============================================================================

class TestAutomatedChecks:
    """FR-1: Automated Check Tests (10 tests)."""

    def test_git_status_check_clean(self, checker):
        """
        FR-1.1: Clean git status returns PASS.

        Given: Git working tree is clean
        When: run_git_status_check() called
        Then: Returns CheckResult with status=PASS
        """
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                stdout="",
                returncode=0
            )

            result = checker.run_git_status_check()

            assert result.status == "PASS"
            assert "clean" in result.message.lower()

    def test_git_status_check_uncommitted(self, checker):
        """
        FR-1.1: Uncommitted changes returns WARN or FAIL.

        Given: Git has uncommitted changes to core files
        When: run_git_status_check() called
        Then: Returns CheckResult with status=FAIL for core files
        """
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                stdout=" M claude/tools/sre/new_tool.py\n M README.md",
                returncode=0
            )

            result = checker.run_git_status_check()

            # Core file changes should FAIL
            assert result.status in ["WARN", "FAIL"]
            assert result.evidence is not None

    def test_capability_registration_check_registered(self, tmp_maia_root, checker):
        """
        FR-1.2: Registered capabilities return PASS.

        Given: New tool is registered in capabilities.db
        When: run_capability_check() called
        Then: Returns CheckResult with status=PASS
        """
        # Create a tool file
        tool_path = tmp_maia_root / "claude" / "tools" / "sre" / "test_tool.py"
        tool_path.write_text('"""Test tool."""\ndef main(): pass')

        # Register it in capabilities.db
        db_path = tmp_maia_root / "claude" / "data" / "databases" / "system" / "capabilities.db"
        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO capabilities (name, type, path, category, status) VALUES (?, ?, ?, ?, ?)",
            ("test_tool.py", "tool", "claude/tools/sre/test_tool.py", "sre", "production")
        )
        conn.commit()
        conn.close()

        # Mock recently modified files
        with patch.object(checker, '_get_recently_modified_files') as mock_recent:
            mock_recent.return_value = [tool_path]

            result = checker.run_capability_check()

            assert result.status == "PASS"

    def test_capability_registration_check_unregistered(self, tmp_maia_root, checker):
        """
        FR-1.2: Unregistered tools return FAIL.

        Given: New tool NOT registered in capabilities.db
        When: run_capability_check() called
        Then: Returns CheckResult with status=FAIL listing unregistered file
        """
        # Create a tool file but don't register it
        tool_path = tmp_maia_root / "claude" / "tools" / "sre" / "unregistered_tool.py"
        tool_path.write_text('"""Unregistered tool."""\ndef main(): pass')

        # Mock recently modified files
        with patch.object(checker, '_get_recently_modified_files') as mock_recent:
            mock_recent.return_value = [tool_path]

            result = checker.run_capability_check()

            assert result.status == "FAIL"
            assert "unregistered" in result.message.lower()

    def test_documentation_check_complete(self, tmp_maia_root, checker):
        """
        FR-1.3: Complete docs return PASS.

        Given: Tool has proper docstrings
        When: run_documentation_check() called
        Then: Returns CheckResult with status=PASS
        """
        # Create a well-documented tool
        tool_path = tmp_maia_root / "claude" / "tools" / "sre" / "documented_tool.py"
        tool_path.write_text('''"""
Tool with proper documentation.

This module provides test functionality.
"""

def public_function():
    """Public function with docstring."""
    pass
''')

        with patch.object(checker, '_get_recently_modified_files') as mock_recent:
            mock_recent.return_value = [tool_path]

            result = checker.run_documentation_check()

            assert result.status == "PASS"

    def test_documentation_check_missing(self, tmp_maia_root, checker):
        """
        FR-1.3: Missing docstrings return FAIL.

        Given: Tool has no module docstring
        When: run_documentation_check() called
        Then: Returns CheckResult with status=FAIL
        """
        # Create a tool without docstrings
        tool_path = tmp_maia_root / "claude" / "tools" / "sre" / "undocumented_tool.py"
        tool_path.write_text('def public_function():\n    pass')

        with patch.object(checker, '_get_recently_modified_files') as mock_recent:
            mock_recent.return_value = [tool_path]

            result = checker.run_documentation_check()

            assert result.status == "FAIL"
            assert "docstring" in result.message.lower() or "documentation" in result.message.lower()

    def test_testing_check_exists(self, tmp_maia_root, checker):
        """
        FR-1.4: Test file exists returns PASS.

        Given: Tool has corresponding test file
        When: run_testing_check() called
        Then: Returns CheckResult with status=PASS
        """
        # Create tool and corresponding test
        tool_path = tmp_maia_root / "claude" / "tools" / "sre" / "tested_tool.py"
        tool_path.write_text('"""Tested tool."""\ndef main(): pass')

        test_path = tmp_maia_root / "tests" / "test_tested_tool.py"
        test_path.write_text('"""Tests for tested_tool."""\ndef test_main(): pass')

        with patch.object(checker, '_get_recently_modified_files') as mock_recent:
            mock_recent.return_value = [tool_path]

            result = checker.run_testing_check()

            assert result.status == "PASS"

    def test_testing_check_missing(self, tmp_maia_root, checker):
        """
        FR-1.4: Missing test returns FAIL.

        Given: Tool has no corresponding test file
        When: run_testing_check() called
        Then: Returns CheckResult with status=FAIL
        """
        # Create tool without test
        tool_path = tmp_maia_root / "claude" / "tools" / "sre" / "untested_tool.py"
        tool_path.write_text('"""Untested tool."""\ndef main(): pass')

        with patch.object(checker, '_get_recently_modified_files') as mock_recent:
            mock_recent.return_value = [tool_path]

            result = checker.run_testing_check()

            assert result.status == "FAIL"
            assert "test" in result.message.lower()

    def test_learning_check_active(self, checker, mock_session):
        """
        FR-1.5: Active session returns PASS.

        Given: Learning session is active
        When: run_learning_check() called
        Then: Returns CheckResult with status=PASS
        """
        mock_session.current_session = True

        result = checker.run_learning_check()

        assert result.status == "PASS"
        assert "active" in result.message.lower()

    def test_learning_check_inactive(self, checker):
        """
        FR-1.5: No session returns WARN.

        Given: No learning session active
        When: run_learning_check() called
        Then: Returns CheckResult with status=WARN
        """
        with patch('claude.tools.sre.finish_checker.get_session_manager') as mock:
            manager = MagicMock()
            manager.current_session = None
            mock.return_value = manager

            result = checker.run_learning_check()

            assert result.status == "WARN"

    def test_preintegration_check_clean(self, tmp_maia_root, checker):
        """
        FR-1.6: No linting errors returns PASS.

        Given: ruff check passes with no errors
        When: run_preintegration_check() called
        Then: Returns CheckResult with status=PASS
        """
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                stdout="",
                stderr="",
                returncode=0
            )

            result = checker.run_preintegration_check()

            assert result.status == "PASS"


# =============================================================================
# TestBlockingBehavior - FR-2: Blocking Logic
# =============================================================================

class TestBlockingBehavior:
    """FR-2: Blocking Behavior Tests (3 tests)."""

    def test_fail_blocks_completion(self, checker):
        """
        FR-2.1: FAIL items prevent completion.

        Given: One or more checks return FAIL
        When: check_blockers() called
        Then: Returns list of blocking issues
        """
        # Mock automated checks with one FAIL
        mock_results = {
            "git_status": CheckResult(name="git_status", status="PASS", message="Clean"),
            "capability": CheckResult(name="capability", status="FAIL", message="Unregistered tool"),
            "documentation": CheckResult(name="documentation", status="PASS", message="Complete"),
        }

        with patch.object(checker, 'run_automated_checks', return_value=mock_results):
            blockers = checker.check_blockers()

            assert len(blockers) > 0
            assert any("capability" in b.lower() for b in blockers)

    def test_warn_does_not_block(self, checker):
        """
        FR-2.2: WARN items allow continuation.

        Given: Only WARN checks (no FAIL)
        When: check_blockers() called
        Then: Returns empty list (no blockers)
        """
        mock_results = {
            "git_status": CheckResult(name="git_status", status="WARN", message="Minor changes"),
            "capability": CheckResult(name="capability", status="PASS", message="Registered"),
            "learning": CheckResult(name="learning", status="WARN", message="Session ending"),
        }

        with patch.object(checker, 'run_automated_checks', return_value=mock_results):
            blockers = checker.check_blockers()

            assert len(blockers) == 0

    def test_circuit_breaker_triggers(self, checker, tmp_maia_root):
        """
        FR-2.3: 5 consecutive fails escalates.

        Given: 5 consecutive FAIL runs recorded
        When: run_automated_checks() called again
        Then: Raises FinishCheckerError or returns ESCALATED status
        """
        # Initialize checker state with failure history
        checker._consecutive_failures = 4

        mock_results = {
            "git_status": CheckResult(name="git_status", status="FAIL", message="Issues"),
        }

        with patch.object(checker, '_run_individual_checks', return_value=mock_results):
            result = checker.run_automated_checks()

            # Should either raise or indicate escalation
            assert checker._consecutive_failures >= 5 or result.get("_escalated", False)


# =============================================================================
# TestInteractiveReview - FR-3: Mandatory Review
# =============================================================================

class TestInteractiveReview:
    """FR-3: Interactive Review Tests (3 tests)."""

    def test_review_required(self, checker):
        """
        FR-3.1: Integration review is mandatory.

        Given: Automated checks all pass
        When: is_review_required() called
        Then: Returns True (review always required)
        """
        assert checker.is_review_required() is True

    def test_review_responses_validated(self, checker):
        """
        FR-3.1-3.4: Evidence required for each question.

        Given: Review responses provided
        When: validate_review_responses() called
        Then: Validates each response has evidence (not just "No")
        """
        # Valid responses with evidence
        valid_responses = {
            "claude_md": "No change needed - only added internal tool",
            "dependent_systems": "Checked: swarm_auto_loader.py, close-session.md - no impact",
            "ripple_effects": "Verified: no other tools use this pattern",
            "documentation": "Updated: capability_index.md, SYSTEM_STATE.md"
        }

        result = checker.validate_review_responses(valid_responses)
        assert result is True

        # Invalid responses (too short, no evidence)
        invalid_responses = {
            "claude_md": "No",
            "dependent_systems": "None",
            "ripple_effects": "No",
            "documentation": "Done"
        }

        result = checker.validate_review_responses(invalid_responses)
        assert result is False

    def test_incomplete_review_blocks(self, checker):
        """
        FR-3: Skipped questions block completion.

        Given: Not all review questions answered
        When: validate_review_responses() called
        Then: Returns False (blocks completion)
        """
        # Missing responses
        incomplete_responses = {
            "claude_md": "No change needed",
            # Missing: dependent_systems, ripple_effects, documentation
        }

        result = checker.validate_review_responses(incomplete_responses)
        assert result is False


# =============================================================================
# TestPersistence - FR-4: Completion State Storage
# =============================================================================

class TestPersistence:
    """FR-4: Completion State Tests (3 tests)."""

    def test_completion_record_stored(self, checker, db_path):
        """
        FR-4.1: Completion stored in DB.

        Given: Successful completion with all checks passed
        When: persist_completion() called
        Then: Record stored in completion_records table
        """
        record = CompletionRecord(
            session_id="test_session",
            context_id="12345",
            project_name="test_project",
            agent_used="sre_principal_engineer_agent",
            check_results={"git_status": "PASS", "capability": "PASS"},
            review_responses={"claude_md": "No change needed"},
            files_touched=["claude/tools/sre/test.py"],
            status="COMPLETE"
        )

        result = checker.persist_completion(record)

        assert result is True

        # Verify in database
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("SELECT * FROM completion_records WHERE session_id = ?", ("test_session",))
        row = cursor.fetchone()
        conn.close()

        assert row is not None

    def test_record_includes_all_fields(self, checker, db_path):
        """
        FR-4.2: All required fields present in record.

        Given: CompletionRecord with all fields
        When: persist_completion() called
        Then: All fields stored correctly
        """
        record = CompletionRecord(
            session_id="test_session_2",
            context_id="67890",
            project_name="full_test",
            agent_used="sre_principal_engineer_agent",
            check_results={
                "git_status": "PASS",
                "capability": "PASS",
                "documentation": "WARN",
                "testing": "PASS",
                "learning": "PASS",
                "preintegration": "PASS"
            },
            review_responses={
                "claude_md": "No change",
                "dependent_systems": "None",
                "ripple_effects": "None",
                "documentation": "Complete"
            },
            files_touched=["file1.py", "file2.py"],
            status="COMPLETE"
        )

        checker.persist_completion(record)

        # Verify all fields
        conn = sqlite3.connect(db_path)
        cursor = conn.execute(
            "SELECT session_id, context_id, project_name, agent_used, check_results, "
            "review_responses, files_touched, status FROM completion_records WHERE session_id = ?",
            ("test_session_2",)
        )
        row = cursor.fetchone()
        conn.close()

        assert row[0] == "test_session_2"  # session_id
        assert row[1] == "67890"  # context_id
        assert row[2] == "full_test"  # project_name
        assert row[3] == "sre_principal_engineer_agent"  # agent_used
        assert "git_status" in row[4]  # check_results (JSON string)
        assert "claude_md" in row[5]  # review_responses (JSON string)
        assert "file1.py" in row[6]  # files_touched (JSON string)
        assert row[7] == "COMPLETE"  # status

    def test_query_past_completions(self, checker, db_path):
        """
        FR-4.3: Query completions by criteria.

        Given: Multiple completion records stored
        When: query_completions() called with filters
        Then: Returns matching records
        """
        # Store multiple records
        for i in range(3):
            record = CompletionRecord(
                session_id=f"session_{i}",
                context_id=f"ctx_{i}",
                project_name="test_project" if i < 2 else "other_project",
                agent_used="sre_principal_engineer_agent",
                check_results={"git_status": "PASS"},
                review_responses={"claude_md": "No change"},
                files_touched=[],
                status="COMPLETE"
            )
            checker.persist_completion(record)

        # Query by project
        results = checker.query_completions(project_name="test_project")
        assert len(results) == 2

        # Query by agent
        results = checker.query_completions(agent_used="sre_principal_engineer_agent")
        assert len(results) == 3


# =============================================================================
# TestSessionIntegration - FR-5: Session Lifecycle
# =============================================================================

class TestSessionIntegration:
    """FR-5: Session Integration Tests (3 tests)."""

    def test_close_session_warns_no_finish(self, checker):
        """
        FR-5.1: Warning if /finish not run.

        Given: Session about to close
        When: check_finish_before_close() called
        Then: Returns warning if no completion record for session
        """
        # Mock session without finish
        session_data = {
            "session_id": "no_finish_session",
            "current_agent": "sre_principal_engineer_agent"
        }

        warning = checker.check_finish_before_close(session_data)

        assert warning is not None
        assert "/finish" in warning.lower()

    def test_finish_reads_session_context(self, checker, mock_session):
        """
        FR-5.2: Session context available to finish checker.

        Given: Active session with context
        When: get_session_context() called
        Then: Returns agent, files_touched, query from session
        """
        mock_session.active_session_id = "test_session"
        mock_session.get_context.return_value = {
            "agent": "sre_principal_engineer_agent",
            "files_touched": ["file1.py", "file2.py"],
            "initial_query": "Implement feature X"
        }

        context = checker.get_session_context()

        assert context["agent"] == "sre_principal_engineer_agent"
        assert len(context["files_touched"]) == 2

    def test_completion_links_to_session(self, checker, db_path, mock_session):
        """
        FR-5.3: Audit trail established between completion and session.

        Given: Completion record created during session
        When: Queried later
        Then: Can trace completion back to session
        """
        mock_session.active_session_id = "linked_session"

        record = CompletionRecord(
            session_id="linked_session",
            context_id="ctx_linked",
            project_name="linked_project",
            agent_used="sre_principal_engineer_agent",
            check_results={"git_status": "PASS"},
            review_responses={"claude_md": "No change"},
            files_touched=[],
            status="COMPLETE"
        )

        checker.persist_completion(record)

        # Query by session ID
        results = checker.query_completions(session_id="linked_session")
        assert len(results) == 1
        assert results[0]["session_id"] == "linked_session"


# =============================================================================
# TestCheckResultDataclass
# =============================================================================

class TestCheckResult:
    """Test CheckResult dataclass structure."""

    def test_check_result_structure(self):
        """
        Test CheckResult has required fields.

        Given: CheckResult instantiated
        When: Fields accessed
        Then: Has name, status, message, evidence fields
        """
        result = CheckResult(
            name="test_check",
            status="PASS",
            message="Test passed successfully",
            evidence="No issues found"
        )

        assert result.name == "test_check"
        assert result.status == "PASS"
        assert result.message == "Test passed successfully"
        assert result.evidence == "No issues found"

    def test_check_result_status_values(self):
        """
        Test CheckResult status must be PASS, WARN, or FAIL.
        """
        for status in ["PASS", "WARN", "FAIL"]:
            result = CheckResult(name="test", status=status, message="msg")
            assert result.status == status


# =============================================================================
# TestCompletionRecordDataclass
# =============================================================================

class TestCompletionRecord:
    """Test CompletionRecord dataclass structure."""

    def test_completion_record_structure(self):
        """
        Test CompletionRecord has all required fields.
        """
        record = CompletionRecord(
            session_id="sess_123",
            context_id="ctx_456",
            project_name="my_project",
            agent_used="sre_agent",
            check_results={"git": "PASS"},
            review_responses={"claude_md": "Done"},
            files_touched=["file.py"],
            status="COMPLETE"
        )

        assert record.session_id == "sess_123"
        assert record.context_id == "ctx_456"
        assert record.project_name == "my_project"
        assert record.agent_used == "sre_agent"
        assert record.check_results == {"git": "PASS"}
        assert record.review_responses == {"claude_md": "Done"}
        assert record.files_touched == ["file.py"]
        assert record.status == "COMPLETE"
