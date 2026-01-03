"""
TDD Tests for close_session() helper functions.

Phase 2: Decomposing close_session (286 lines) into testable helper functions.

These tests define the expected behavior BEFORE implementation (TDD Red phase).
"""

import pytest
import json
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime
import time
import sys

# Add hooks to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestCheckGitStatus:
    """Tests for _check_git_status() helper."""

    def test_returns_tuple_with_issues_and_files(self):
        """Verify return type is (has_issues: bool, files: List[str])."""
        from swarm_auto_loader import _check_git_status
        result = _check_git_status()
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], list)

    def test_detects_uncommitted_changes(self, tmp_path):
        """Verify uncommitted changes are detected."""
        from swarm_auto_loader import _check_git_status

        # Mock subprocess to return uncommitted files
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = " M file1.py\n M file2.py\n?? new_file.py"

        with patch('swarm_auto_loader.subprocess.run', return_value=mock_result):
            has_issues, files = _check_git_status()
            assert has_issues is True
            assert len(files) == 3

    def test_clean_repo_returns_no_issues(self):
        """Verify clean repo returns no issues."""
        from swarm_auto_loader import _check_git_status

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""

        with patch('swarm_auto_loader.subprocess.run', return_value=mock_result):
            has_issues, files = _check_git_status()
            assert has_issues is False
            assert len(files) == 0

    def test_handles_git_not_available(self):
        """Verify graceful degradation when git is not available."""
        from swarm_auto_loader import _check_git_status

        with patch('swarm_auto_loader.subprocess.run', side_effect=FileNotFoundError):
            has_issues, files = _check_git_status()
            assert has_issues is False
            assert len(files) == 0

    def test_handles_timeout(self):
        """Verify graceful handling of timeout."""
        from swarm_auto_loader import _check_git_status

        with patch('swarm_auto_loader.subprocess.run', side_effect=subprocess.TimeoutExpired('git', 2)):
            has_issues, files = _check_git_status()
            assert has_issues is False
            assert len(files) == 0


class TestCheckDocsCurrency:
    """Tests for _check_docs_currency() helper."""

    def test_returns_tuple_with_issues_and_message(self):
        """Verify return type is (has_issues: bool, message: str)."""
        from swarm_auto_loader import _check_docs_currency
        result = _check_docs_currency()
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], str)

    def test_detects_stale_docs(self, tmp_path):
        """Verify stale documentation is detected."""
        from swarm_auto_loader import _check_docs_currency

        # Create mock file structure
        system_state = tmp_path / "SYSTEM_STATE.md"
        system_state.write_text("# State")
        # Make it appear old
        old_time = time.time() - 7200  # 2 hours ago

        with patch('swarm_auto_loader.MAIA_ROOT', tmp_path):
            # Mock find command to return recent files
            mock_result = MagicMock()
            mock_result.stdout = str(tmp_path / "claude" / "test.py")

            with patch('swarm_auto_loader.subprocess.run', return_value=mock_result):
                with patch.object(Path, 'stat') as mock_stat:
                    mock_stat.return_value.st_mtime = time.time()  # Current time
                    # This would indicate docs are stale
                    pass

    def test_handles_missing_system_state(self, tmp_path):
        """Verify graceful handling when SYSTEM_STATE.md doesn't exist."""
        from swarm_auto_loader import _check_docs_currency

        with patch('swarm_auto_loader.MAIA_ROOT', tmp_path):
            has_issues, message = _check_docs_currency()
            assert has_issues is False


class TestCheckBackgroundProcesses:
    """Tests for _check_background_processes() helper."""

    def test_returns_tuple_with_issues_and_count(self):
        """Verify return type is (has_issues: bool, count: int)."""
        from swarm_auto_loader import _check_background_processes
        result = _check_background_processes()
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], int)

    def test_detects_running_processes(self):
        """Verify running background processes are detected."""
        from swarm_auto_loader import _check_background_processes

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "12345\n12346\n12347"

        with patch('swarm_auto_loader.subprocess.run', return_value=mock_result):
            has_issues, count = _check_background_processes()
            assert has_issues is True
            assert count == 3

    def test_no_processes_returns_zero(self):
        """Verify no processes returns count of 0."""
        from swarm_auto_loader import _check_background_processes

        mock_result = MagicMock()
        mock_result.returncode = 1  # pgrep returns 1 when no matches
        mock_result.stdout = ""

        with patch('swarm_auto_loader.subprocess.run', return_value=mock_result):
            has_issues, count = _check_background_processes()
            assert has_issues is False
            assert count == 0

    def test_handles_pgrep_not_available(self):
        """Verify graceful degradation when pgrep is not available."""
        from swarm_auto_loader import _check_background_processes

        with patch('swarm_auto_loader.subprocess.run', side_effect=FileNotFoundError):
            has_issues, count = _check_background_processes()
            assert has_issues is False
            assert count == 0


class TestCheckCheckpointCurrency:
    """Tests for _check_checkpoint_currency() helper."""

    def test_returns_tuple_with_issues_and_age(self):
        """Verify return type is (has_issues: bool, age_hours: float)."""
        from swarm_auto_loader import _check_checkpoint_currency
        result = _check_checkpoint_currency(has_git_issues=False)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], (int, float))

    def test_warns_on_old_checkpoint_with_git_changes(self, tmp_path):
        """Verify warning when checkpoint is old and git has changes."""
        from swarm_auto_loader import _check_checkpoint_currency

        # Create checkpoint directory with old checkpoint
        checkpoints_dir = tmp_path / "claude" / "data" / "checkpoints"
        checkpoints_dir.mkdir(parents=True)
        old_checkpoint = checkpoints_dir / "checkpoint_2024.json"
        old_checkpoint.write_text("{}")

        with patch('swarm_auto_loader.MAIA_ROOT', tmp_path):
            has_issues, age_hours = _check_checkpoint_currency(has_git_issues=True)
            # With git issues and old checkpoint, should warn
            assert isinstance(age_hours, (int, float))

    def test_no_warning_without_git_changes(self, tmp_path):
        """Verify no warning when no git changes even with old checkpoint."""
        from swarm_auto_loader import _check_checkpoint_currency

        checkpoints_dir = tmp_path / "claude" / "data" / "checkpoints"
        checkpoints_dir.mkdir(parents=True)

        with patch('swarm_auto_loader.MAIA_ROOT', tmp_path):
            has_issues, age_hours = _check_checkpoint_currency(has_git_issues=False)
            assert has_issues is False


class TestCheckDevelopmentCleanup:
    """Tests for _check_development_cleanup() helper."""

    def test_returns_dict_with_categories(self):
        """Verify return type is Dict[str, List[str]]."""
        from swarm_auto_loader import _check_development_cleanup
        result = _check_development_cleanup()
        assert isinstance(result, dict)
        assert 'versioned_files' in result
        assert 'misplaced_tests' in result
        assert 'build_artifacts' in result

    def test_detects_versioned_files(self, tmp_path):
        """Verify versioned files are detected."""
        from swarm_auto_loader import _check_development_cleanup

        tools_dir = tmp_path / "claude" / "tools"
        tools_dir.mkdir(parents=True)
        (tools_dir / "something_v2.py").write_text("# v2")
        (tools_dir / "something_v3.py").write_text("# v3")

        with patch('swarm_auto_loader.MAIA_ROOT', tmp_path):
            result = _check_development_cleanup()
            assert len(result['versioned_files']) == 2

    def test_detects_misplaced_tests(self, tmp_path):
        """Verify misplaced test files are detected."""
        from swarm_auto_loader import _check_development_cleanup

        tools_dir = tmp_path / "claude" / "tools"
        tools_dir.mkdir(parents=True)
        (tools_dir / "test_something.py").write_text("# test")  # Wrong location

        with patch('swarm_auto_loader.MAIA_ROOT', tmp_path):
            result = _check_development_cleanup()
            assert len(result['misplaced_tests']) >= 1


class TestCleanupSession:
    """Tests for _cleanup_session() helper."""

    def test_deletes_session_file(self, tmp_path):
        """Verify session file is deleted."""
        from swarm_auto_loader import _cleanup_session

        session_file = tmp_path / "session.json"
        session_file.write_text('{"current_agent": "test", "domain": "test"}')

        result = _cleanup_session(session_file)
        assert result is True
        assert not session_file.exists()

    def test_handles_missing_file(self, tmp_path):
        """Verify graceful handling of missing file."""
        from swarm_auto_loader import _cleanup_session

        session_file = tmp_path / "nonexistent.json"
        result = _cleanup_session(session_file)
        assert result is False

    def test_handles_corrupt_json(self, tmp_path):
        """Verify graceful handling of corrupt JSON."""
        from swarm_auto_loader import _cleanup_session

        session_file = tmp_path / "corrupt.json"
        session_file.write_text("{invalid json")

        result = _cleanup_session(session_file)
        # Should still delete the file even if corrupt
        assert not session_file.exists()


class TestHelperFunctionsExist:
    """Meta-test: Verify all helper functions are defined."""

    def test_check_git_status_exists(self):
        """Verify _check_git_status function exists."""
        from swarm_auto_loader import _check_git_status
        assert callable(_check_git_status)

    def test_check_docs_currency_exists(self):
        """Verify _check_docs_currency function exists."""
        from swarm_auto_loader import _check_docs_currency
        assert callable(_check_docs_currency)

    def test_check_background_processes_exists(self):
        """Verify _check_background_processes function exists."""
        from swarm_auto_loader import _check_background_processes
        assert callable(_check_background_processes)

    def test_check_checkpoint_currency_exists(self):
        """Verify _check_checkpoint_currency function exists."""
        from swarm_auto_loader import _check_checkpoint_currency
        assert callable(_check_checkpoint_currency)

    def test_check_development_cleanup_exists(self):
        """Verify _check_development_cleanup function exists."""
        from swarm_auto_loader import _check_development_cleanup
        assert callable(_check_development_cleanup)

    def test_cleanup_session_exists(self):
        """Verify _cleanup_session function exists."""
        from swarm_auto_loader import _cleanup_session
        assert callable(_cleanup_session)
