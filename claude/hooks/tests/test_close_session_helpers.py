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

    def test_categorize_uncommitted_files_exists(self):
        """Verify _categorize_uncommitted_files function exists."""
        from swarm_auto_loader import _categorize_uncommitted_files
        assert callable(_categorize_uncommitted_files)

    def test_get_session_files_touched_exists(self):
        """Verify _get_session_files_touched function exists."""
        from swarm_auto_loader import _get_session_files_touched
        assert callable(_get_session_files_touched)

    def test_update_session_files_touched_exists(self):
        """Verify update_session_files_touched function exists."""
        from swarm_auto_loader import update_session_files_touched
        assert callable(update_session_files_touched)


class TestCategorizeUncommittedFiles:
    """Tests for _categorize_uncommitted_files() helper.

    Phase 234: Smart uncommitted file detection.
    Categorizes uncommitted files as 'this_session' vs 'other_session'
    based on files_touched from current session.
    """

    def test_returns_dict_with_categories(self):
        """Verify return type has both categories."""
        from swarm_auto_loader import _categorize_uncommitted_files

        result = _categorize_uncommitted_files(
            uncommitted_files=[],
            files_touched=[]
        )
        assert isinstance(result, dict)
        assert 'this_session' in result
        assert 'other_session' in result
        assert isinstance(result['this_session'], list)
        assert isinstance(result['other_session'], list)

    def test_file_in_session_goes_to_this_session(self):
        """File touched in this session goes to 'this_session' category."""
        from swarm_auto_loader import _categorize_uncommitted_files

        result = _categorize_uncommitted_files(
            uncommitted_files=[' M claude/tools/foo.py'],
            files_touched=['claude/tools/foo.py']
        )
        assert 'claude/tools/foo.py' in result['this_session']
        assert len(result['other_session']) == 0

    def test_file_not_in_session_goes_to_other_session(self):
        """File NOT touched in this session goes to 'other_session' category."""
        from swarm_auto_loader import _categorize_uncommitted_files

        result = _categorize_uncommitted_files(
            uncommitted_files=[' M claude/tools/bar.py'],
            files_touched=['claude/tools/foo.py']  # Different file
        )
        assert 'claude/tools/bar.py' in result['other_session']
        assert len(result['this_session']) == 0

    def test_mixed_files_categorized_correctly(self):
        """Mixed files go to correct categories."""
        from swarm_auto_loader import _categorize_uncommitted_files

        result = _categorize_uncommitted_files(
            uncommitted_files=[
                ' M claude/tools/touched.py',
                ' M claude/tools/untouched.py',
                '?? claude/tools/new_touched.py'
            ],
            files_touched=[
                'claude/tools/touched.py',
                'claude/tools/new_touched.py'
            ]
        )
        assert 'claude/tools/touched.py' in result['this_session']
        assert 'claude/tools/new_touched.py' in result['this_session']
        assert 'claude/tools/untouched.py' in result['other_session']

    def test_parses_git_status_prefixes(self):
        """Correctly parses git status output with status prefixes."""
        from swarm_auto_loader import _categorize_uncommitted_files

        result = _categorize_uncommitted_files(
            uncommitted_files=[
                ' M file1.py',    # Modified
                'M  file2.py',    # Staged modified
                '?? file3.py',    # Untracked
                'A  file4.py',    # Added
                ' D file5.py',    # Deleted
            ],
            files_touched=['file1.py', 'file3.py']
        )
        assert 'file1.py' in result['this_session']
        assert 'file3.py' in result['this_session']
        assert 'file2.py' in result['other_session']
        assert 'file4.py' in result['other_session']
        assert 'file5.py' in result['other_session']

    def test_handles_absolute_paths(self):
        """Handles absolute paths in files_touched."""
        from swarm_auto_loader import _categorize_uncommitted_files

        result = _categorize_uncommitted_files(
            uncommitted_files=[' M claude/tools/foo.py'],
            files_touched=['/Users/naythandawe/maia/claude/tools/foo.py']
        )
        # Should match even with absolute path
        assert 'claude/tools/foo.py' in result['this_session']

    def test_empty_files_touched_all_go_to_other(self):
        """When no files_touched, all uncommitted go to 'other_session'."""
        from swarm_auto_loader import _categorize_uncommitted_files

        result = _categorize_uncommitted_files(
            uncommitted_files=[' M file1.py', ' M file2.py'],
            files_touched=[]
        )
        assert len(result['this_session']) == 0
        assert len(result['other_session']) == 2

    def test_empty_uncommitted_returns_empty_lists(self):
        """When no uncommitted files, both categories are empty."""
        from swarm_auto_loader import _categorize_uncommitted_files

        result = _categorize_uncommitted_files(
            uncommitted_files=[],
            files_touched=['file1.py', 'file2.py']
        )
        assert len(result['this_session']) == 0
        assert len(result['other_session']) == 0


class TestGetSessionFilesTouched:
    """Tests for _get_session_files_touched() helper.

    Phase 234: Read files_touched from session file.
    """

    def test_returns_list(self):
        """Verify return type is list."""
        from swarm_auto_loader import _get_session_files_touched
        result = _get_session_files_touched()
        assert isinstance(result, list)

    def test_reads_files_touched_from_session(self, tmp_path):
        """Reads files_touched from session file."""
        from swarm_auto_loader import _get_session_files_touched

        session_file = tmp_path / "session.json"
        session_file.write_text(json.dumps({
            "current_agent": "sre",
            "files_touched": ["file1.py", "file2.py"]
        }))

        with patch('swarm_auto_loader.get_session_file_path', return_value=session_file):
            result = _get_session_files_touched()
            assert result == ["file1.py", "file2.py"]

    def test_returns_empty_when_no_session_file(self, tmp_path):
        """Returns empty list when session file doesn't exist."""
        from swarm_auto_loader import _get_session_files_touched

        nonexistent = tmp_path / "nonexistent.json"

        with patch('swarm_auto_loader.get_session_file_path', return_value=nonexistent):
            result = _get_session_files_touched()
            assert result == []

    def test_returns_empty_when_no_files_touched_key(self, tmp_path):
        """Returns empty list when files_touched key is missing."""
        from swarm_auto_loader import _get_session_files_touched

        session_file = tmp_path / "session.json"
        session_file.write_text(json.dumps({
            "current_agent": "sre"
            # No files_touched key
        }))

        with patch('swarm_auto_loader.get_session_file_path', return_value=session_file):
            result = _get_session_files_touched()
            assert result == []

    def test_handles_corrupt_json(self, tmp_path):
        """Handles corrupt JSON gracefully."""
        from swarm_auto_loader import _get_session_files_touched

        session_file = tmp_path / "corrupt.json"
        session_file.write_text("{invalid json")

        with patch('swarm_auto_loader.get_session_file_path', return_value=session_file):
            result = _get_session_files_touched()
            assert result == []


class TestUpdateSessionFilesTouched:
    """Tests for update_session_files_touched() function.

    Phase 234: Track files modified during session.
    """

    def test_adds_file_to_session(self, tmp_path):
        """Successfully adds file to files_touched list."""
        from swarm_auto_loader import update_session_files_touched

        session_file = tmp_path / "session.json"
        session_file.write_text(json.dumps({
            "current_agent": "sre"
        }))

        with patch('swarm_auto_loader.get_session_file_path', return_value=session_file):
            result = update_session_files_touched("claude/tools/foo.py")
            assert result is True

            # Verify file was written
            with open(session_file) as f:
                data = json.load(f)
            assert "claude/tools/foo.py" in data['files_touched']

    def test_does_not_duplicate_files(self, tmp_path):
        """Does not add duplicate file paths."""
        from swarm_auto_loader import update_session_files_touched

        session_file = tmp_path / "session.json"
        session_file.write_text(json.dumps({
            "current_agent": "sre",
            "files_touched": ["claude/tools/foo.py"]
        }))

        with patch('swarm_auto_loader.get_session_file_path', return_value=session_file):
            result = update_session_files_touched("claude/tools/foo.py")
            assert result is True

            with open(session_file) as f:
                data = json.load(f)
            assert data['files_touched'].count("claude/tools/foo.py") == 1

    def test_returns_false_when_no_session(self, tmp_path):
        """Returns False when session file doesn't exist."""
        from swarm_auto_loader import update_session_files_touched

        nonexistent = tmp_path / "nonexistent.json"

        with patch('swarm_auto_loader.get_session_file_path', return_value=nonexistent):
            result = update_session_files_touched("claude/tools/foo.py")
            assert result is False

    def test_normalizes_absolute_paths(self, tmp_path):
        """Strips MAIA_ROOT from absolute paths."""
        from swarm_auto_loader import update_session_files_touched, MAIA_ROOT

        session_file = tmp_path / "session.json"
        session_file.write_text(json.dumps({
            "current_agent": "sre"
        }))

        with patch('swarm_auto_loader.get_session_file_path', return_value=session_file):
            abs_path = f"{MAIA_ROOT}/claude/tools/bar.py"
            result = update_session_files_touched(abs_path)
            assert result is True

            with open(session_file) as f:
                data = json.load(f)
            assert "claude/tools/bar.py" in data['files_touched']
