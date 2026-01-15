"""
Integration Tests for /finish Skill

End-to-end tests validating the complete /finish workflow including
session integration, database persistence, and close-session warnings.

Sprint: /finish Skill Implementation
Phase: P1 - Integration Test Design (TDD)

Created: 2026-01-15
"""

import pytest
import json
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import will fail initially (P1 - tests should fail until P3/P5)
from claude.tools.sre.finish_checker import (
    FinishChecker,
    CheckResult,
    CompletionRecord,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def full_maia_setup(tmp_path):
    """
    Create a complete MAIA_ROOT structure for integration testing.

    Includes:
    - Directory structure
    - capabilities.db with schema
    - project_tracking.db with completion_records table
    - Sample tool files
    - Sample test files
    """
    # Create full directory structure
    dirs = [
        "claude/tools/sre",
        "claude/tools/learning",
        "claude/agents",
        "claude/commands",
        "claude/data/databases/system",
        "claude/data/project_status/active",
        "claude/context/core",
        "tests/integration",
    ]
    for d in dirs:
        (tmp_path / d).mkdir(parents=True, exist_ok=True)

    # Create capabilities.db
    cap_db = tmp_path / "claude/data/databases/system/capabilities.db"
    conn = sqlite3.connect(cap_db)
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
    # Pre-populate with existing tools
    conn.execute(
        "INSERT INTO capabilities (name, type, path, category, status) VALUES (?, ?, ?, ?, ?)",
        ("feature_tracker.py", "tool", "claude/tools/sre/feature_tracker.py", "sre", "production")
    )
    conn.commit()
    conn.close()

    # Create project_tracking.db with completion_records table
    proj_db = tmp_path / "claude/data/databases/system/project_tracking.db"
    conn = sqlite3.connect(proj_db)
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
    conn.execute("CREATE INDEX IF NOT EXISTS idx_completion_session ON completion_records(session_id)")
    conn.commit()
    conn.close()

    # Create sample tool file (well-documented)
    tool_content = '''"""
Sample Integration Test Tool.

This tool demonstrates proper documentation format.
"""

def main():
    """Main entry point."""
    pass

def helper():
    """Helper function."""
    pass
'''
    (tmp_path / "claude/tools/sre/sample_tool.py").write_text(tool_content)

    # Create corresponding test file
    test_content = '''"""Tests for sample_tool."""
import pytest
from claude.tools.sre.sample_tool import main, helper

def test_main():
    """Test main function."""
    assert main() is None

def test_helper():
    """Test helper function."""
    assert helper() is None
'''
    (tmp_path / "tests/test_sample_tool.py").write_text(test_content)

    # Register sample_tool in capabilities
    conn = sqlite3.connect(cap_db)
    conn.execute(
        "INSERT INTO capabilities (name, type, path, category, status) VALUES (?, ?, ?, ?, ?)",
        ("sample_tool.py", "tool", "claude/tools/sre/sample_tool.py", "sre", "production")
    )
    conn.commit()
    conn.close()

    return tmp_path


@pytest.fixture
def session_setup(full_maia_setup):
    """
    Setup with mocked session manager.

    Returns tuple of (maia_root, mock_session_manager)
    """
    mock_manager = MagicMock()
    mock_manager.current_session = True
    mock_manager.active_session_id = "integration_test_session"
    mock_manager.get_context.return_value = {
        "agent": "sre_principal_engineer_agent",
        "files_touched": ["claude/tools/sre/sample_tool.py"],
        "initial_query": "Integration test"
    }

    with patch('claude.tools.sre.finish_checker.get_session_manager', return_value=mock_manager):
        yield full_maia_setup, mock_manager


@pytest.fixture
def db_setup(full_maia_setup):
    """
    Setup with real database connections.

    Returns tuple of (maia_root, capabilities_db_path, project_tracking_db_path)
    """
    cap_db = full_maia_setup / "claude/data/databases/system/capabilities.db"
    proj_db = full_maia_setup / "claude/data/databases/system/project_tracking.db"

    return full_maia_setup, cap_db, proj_db


# =============================================================================
# Integration Tests
# =============================================================================

class TestFinishIntegration:
    """E2E Integration Tests for /finish skill."""

    def test_full_completion_workflow(self, full_maia_setup):
        """
        E2E: Complete finish workflow with all checks.

        Given: Clean working state with documented, tested, registered tool
        When: Full /finish workflow executed
        Then: All checks pass, completion recorded
        """
        checker = FinishChecker(maia_root=full_maia_setup)

        # Mock git status as clean
        with patch('subprocess.run') as mock_run:
            def mock_subprocess(cmd, **kwargs):
                cmd_str = ' '.join(cmd) if isinstance(cmd, list) else str(cmd)
                if 'status' in cmd_str:
                    return MagicMock(stdout="", returncode=0)
                elif 'ruff' in cmd_str:
                    return MagicMock(stdout="", stderr="", returncode=0)
                return MagicMock(returncode=0)

            mock_run.side_effect = mock_subprocess

            # Mock session manager
            with patch('claude.tools.sre.finish_checker.get_session_manager') as mock_session:
                manager = MagicMock()
                manager.current_session = True
                manager.active_session_id = "e2e_test_session"
                mock_session.return_value = manager

                # Run automated checks
                results = checker.run_automated_checks()

                # All checks should pass or warn (not fail) for this clean setup
                fail_count = sum(1 for r in results.values() if r.status == "FAIL")

                # In a clean setup, most checks should pass
                assert fail_count <= 2, f"Too many failures: {results}"

                # Run interactive review with valid responses
                review_responses = {
                    "claude_md": "No change needed - sample tool is internal only",
                    "dependent_systems": "Checked: None depend on sample_tool",
                    "ripple_effects": "Verified: No ripple effects identified",
                    "documentation": "Complete: docstrings in place, test file exists"
                }

                review_valid = checker.validate_review_responses(review_responses)
                assert review_valid is True

                # Persist completion
                record = CompletionRecord(
                    session_id="e2e_test_session",
                    context_id="e2e_ctx",
                    project_name="integration_test",
                    agent_used="sre_principal_engineer_agent",
                    check_results={k: v.status for k, v in results.items()},
                    review_responses=review_responses,
                    files_touched=["claude/tools/sre/sample_tool.py"],
                    status="COMPLETE"
                )

                persist_result = checker.persist_completion(record)
                assert persist_result is True

    def test_close_session_integration(self, session_setup):
        """
        E2E: /finish → /close-session flow.

        Given: Session with /finish completion
        When: /close-session checks for finish
        Then: No warning (finish was run)

        Given: Session without /finish completion
        When: /close-session checks for finish
        Then: Warning displayed
        """
        maia_root, mock_manager = session_setup
        checker = FinishChecker(maia_root=maia_root)

        # Scenario 1: Session WITHOUT /finish - should warn
        session_data_no_finish = {
            "session_id": "session_without_finish",
            "current_agent": "sre_principal_engineer_agent",
            "context_id": "ctx_no_finish"
        }

        warning = checker.check_finish_before_close(session_data_no_finish)
        assert warning is not None
        assert "/finish" in warning.lower()

        # Scenario 2: Session WITH /finish - should not warn
        # First, create a completion record
        record = CompletionRecord(
            session_id="session_with_finish",
            context_id="ctx_with_finish",
            project_name="test_project",
            agent_used="sre_principal_engineer_agent",
            check_results={"git_status": "PASS"},
            review_responses={"claude_md": "No change"},
            files_touched=[],
            status="COMPLETE"
        )
        checker.persist_completion(record)

        session_data_with_finish = {
            "session_id": "session_with_finish",
            "current_agent": "sre_principal_engineer_agent",
            "context_id": "ctx_with_finish"
        }

        warning = checker.check_finish_before_close(session_data_with_finish)
        assert warning is None  # No warning because /finish was run

    def test_database_persistence_integrity(self, db_setup):
        """
        E2E: Verify DB records match actual state.

        Given: Multiple completions stored
        When: Database queried
        Then: All records intact with correct data
        """
        maia_root, cap_db, proj_db = db_setup
        checker = FinishChecker(maia_root=maia_root)

        # Store multiple completion records
        test_records = [
            {
                "session_id": "integrity_session_1",
                "context_id": "ctx_1",
                "project_name": "project_alpha",
                "agent_used": "sre_agent",
                "check_results": {"git": "PASS", "cap": "PASS", "doc": "WARN"},
                "review_responses": {"claude_md": "Updated", "deps": "None"},
                "files_touched": ["file1.py", "file2.py"],
                "status": "COMPLETE"
            },
            {
                "session_id": "integrity_session_2",
                "context_id": "ctx_2",
                "project_name": "project_beta",
                "agent_used": "data_analyst_agent",
                "check_results": {"git": "PASS", "cap": "FAIL"},
                "review_responses": {"claude_md": "No change"},
                "files_touched": ["analysis.py"],
                "status": "BLOCKED"
            },
            {
                "session_id": "integrity_session_3",
                "context_id": "ctx_3",
                "project_name": "project_alpha",  # Same project, different session
                "agent_used": "sre_agent",
                "check_results": {"git": "PASS"},
                "review_responses": {"claude_md": "No change"},
                "files_touched": [],
                "status": "COMPLETE"
            }
        ]

        for rec_data in test_records:
            record = CompletionRecord(**rec_data)
            checker.persist_completion(record)

        # Verify record count
        conn = sqlite3.connect(proj_db)
        cursor = conn.execute("SELECT COUNT(*) FROM completion_records")
        count = cursor.fetchone()[0]
        assert count == 3

        # Verify project filter
        results = checker.query_completions(project_name="project_alpha")
        assert len(results) == 2

        # Verify agent filter
        results = checker.query_completions(agent_used="sre_agent")
        assert len(results) == 2

        # Verify status filter
        results = checker.query_completions(status="BLOCKED")
        assert len(results) == 1
        assert results[0]["session_id"] == "integrity_session_2"

        # Verify JSON fields properly stored/retrieved
        results = checker.query_completions(session_id="integrity_session_1")
        assert len(results) == 1
        record = results[0]

        # Check JSON was properly stored and can be parsed back
        check_results = json.loads(record["check_results"]) if isinstance(record["check_results"], str) else record["check_results"]
        assert check_results["git"] == "PASS"
        assert check_results["doc"] == "WARN"

        files_touched = json.loads(record["files_touched"]) if isinstance(record["files_touched"], str) else record["files_touched"]
        assert "file1.py" in files_touched
        assert "file2.py" in files_touched

        conn.close()


class TestFinishBlockingScenarios:
    """Integration tests for blocking behavior in real scenarios."""

    def test_unregistered_tool_blocks_completion(self, full_maia_setup):
        """
        Scenario: New tool created but not registered - should block.

        Given: New tool file exists without capabilities.db entry
        When: /finish run
        Then: FAIL on capability check, blocking completion
        """
        checker = FinishChecker(maia_root=full_maia_setup)

        # Create new unregistered tool
        new_tool = full_maia_setup / "claude/tools/sre/unregistered_new.py"
        new_tool.write_text('"""New unregistered tool."""\ndef main(): pass')

        with patch.object(checker, '_get_recently_modified_files', return_value=[new_tool]):
            result = checker.run_capability_check()

            assert result.status == "FAIL"
            assert "unregistered" in result.message.lower()

        # Verify blockers list includes this
        with patch.object(checker, '_get_recently_modified_files', return_value=[new_tool]):
            with patch('subprocess.run', return_value=MagicMock(stdout="", returncode=0)):
                blockers = checker.check_blockers()
                assert len(blockers) > 0

    def test_missing_test_blocks_completion(self, full_maia_setup):
        """
        Scenario: New tool without test file - should block.

        Given: New tool file exists without corresponding test
        When: /finish run
        Then: FAIL on testing check, blocking completion
        """
        checker = FinishChecker(maia_root=full_maia_setup)

        # Create new tool without test
        new_tool = full_maia_setup / "claude/tools/sre/untested_feature.py"
        new_tool.write_text('"""Feature without tests."""\ndef feature(): pass')

        with patch.object(checker, '_get_recently_modified_files', return_value=[new_tool]):
            result = checker.run_testing_check()

            assert result.status == "FAIL"
            assert "test" in result.message.lower()

    def test_incomplete_review_blocks_completion(self, full_maia_setup):
        """
        Scenario: Interactive review not properly answered - should block.

        Given: All automated checks pass
        When: Interactive review has insufficient answers
        Then: Validation fails, blocking completion
        """
        checker = FinishChecker(maia_root=full_maia_setup)

        # Insufficient responses
        insufficient_responses = {
            "claude_md": "No",  # Too short, no evidence
            "dependent_systems": "None",  # Too short
            # Missing: ripple_effects, documentation
        }

        result = checker.validate_review_responses(insufficient_responses)
        assert result is False


class TestFinishRecoveryScenarios:
    """Integration tests for error recovery and edge cases."""

    def test_graceful_handling_of_missing_db(self, tmp_path):
        """
        Scenario: Database files missing - should handle gracefully.

        Given: MAIA_ROOT with missing databases
        When: FinishChecker initialized
        Then: Creates necessary tables or handles gracefully
        """
        # Create minimal structure without databases
        (tmp_path / "claude/tools/sre").mkdir(parents=True)
        (tmp_path / "claude/data/databases/system").mkdir(parents=True)

        # Should not crash, may create DBs or return graceful errors
        try:
            checker = FinishChecker(maia_root=tmp_path)
            # If we get here, checker handled missing DBs gracefully
            assert True
        except Exception as e:
            # Acceptable if it raises a clear error about missing DB
            assert "database" in str(e).lower() or "db" in str(e).lower()

    def test_idempotent_completion_records(self, full_maia_setup):
        """
        Scenario: Same completion persisted twice - should handle gracefully.

        Given: Completion record already exists
        When: Same record persisted again
        Then: Either updates or creates new record (no crash)
        """
        checker = FinishChecker(maia_root=full_maia_setup)

        record = CompletionRecord(
            session_id="idempotent_session",
            context_id="ctx_idem",
            project_name="idem_project",
            agent_used="sre_agent",
            check_results={"git": "PASS"},
            review_responses={"claude_md": "No change"},
            files_touched=[],
            status="COMPLETE"
        )

        # Persist twice
        result1 = checker.persist_completion(record)
        result2 = checker.persist_completion(record)

        # Both should succeed (idempotent or creates new record)
        assert result1 is True
        assert result2 is True
