#!/usr/bin/env python3
"""
Tests for P2: Files Touched - Extract files from UOCS captures (TDD)

Phase 234: Extract file paths from UOCS captures for session summaries.
"""

import pytest
import tempfile
import time
from pathlib import Path
from unittest.mock import patch


class TestFilesTouchedExtraction:
    """Tests for extracting files touched from UOCS captures."""

    def test_extract_files_from_read_captures(self):
        """Test extracting file paths from read tool captures."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.uocs import UOCS

                uocs = UOCS("test_session")

                # Capture read operations
                uocs.capture("read", {"file_path": "/app/src/main.py"}, "content", True, 50)
                uocs.capture("read", {"file_path": "/app/src/utils.py"}, "content", True, 30)

                time.sleep(0.2)

                files = uocs.get_files_touched()

                assert "/app/src/main.py" in files
                assert "/app/src/utils.py" in files

    def test_extract_files_from_edit_captures(self):
        """Test extracting file paths from edit tool captures."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.uocs import UOCS

                uocs = UOCS("test_session")

                uocs.capture("edit", {
                    "file_path": "/app/config.py",
                    "old_string": "DEBUG=True",
                    "new_string": "DEBUG=False"
                }, "success", True, 100)

                time.sleep(0.2)

                files = uocs.get_files_touched()
                assert "/app/config.py" in files

    def test_extract_files_from_write_captures(self):
        """Test extracting file paths from write tool captures."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.uocs import UOCS

                uocs = UOCS("test_session")

                uocs.capture("write", {"file_path": "/app/new_file.py"}, "created", True, 75)

                time.sleep(0.2)

                files = uocs.get_files_touched()
                assert "/app/new_file.py" in files

    def test_deduplicates_files(self):
        """Test that duplicate file paths are deduplicated."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.uocs import UOCS

                uocs = UOCS("test_session")

                # Same file read multiple times
                uocs.capture("read", {"file_path": "/app/main.py"}, "content", True, 50)
                uocs.capture("read", {"file_path": "/app/main.py"}, "content", True, 30)
                uocs.capture("edit", {"file_path": "/app/main.py", "old_string": "a", "new_string": "b"}, "ok", True, 100)

                time.sleep(0.2)

                files = uocs.get_files_touched()

                # Should only appear once
                assert files.count("/app/main.py") == 1

    def test_ignores_non_file_tools(self):
        """Test that non-file tools don't contribute to files touched."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.uocs import UOCS

                uocs = UOCS("test_session")

                uocs.capture("bash", {"command": "ls -la"}, "output", True, 50)
                uocs.capture("grep", {"pattern": "test", "path": "/app"}, "matches", True, 30)
                uocs.capture("websearch", {"query": "python docs"}, "results", True, 200)

                time.sleep(0.2)

                files = uocs.get_files_touched()
                assert len(files) == 0

    def test_handles_missing_file_path(self):
        """Test graceful handling when file_path is missing from input."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.uocs import UOCS

                uocs = UOCS("test_session")

                # Malformed capture without file_path
                uocs.capture("read", {"some_other_key": "value"}, "content", True, 50)

                time.sleep(0.2)

                files = uocs.get_files_touched()
                assert len(files) == 0

    def test_returns_sorted_list(self):
        """Test that files are returned in sorted order."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.uocs import UOCS

                uocs = UOCS("test_session")

                uocs.capture("read", {"file_path": "/z/file.py"}, "c", True, 50)
                uocs.capture("read", {"file_path": "/a/file.py"}, "c", True, 50)
                uocs.capture("read", {"file_path": "/m/file.py"}, "c", True, 50)

                time.sleep(0.2)

                files = uocs.get_files_touched()

                assert files == sorted(files)


class TestFilesTouchedInSummary:
    """Tests for including files touched in UOCS summary."""

    def test_summary_includes_files_touched(self):
        """Test that get_summary includes files_touched."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.uocs import UOCS

                uocs = UOCS("test_session")

                uocs.capture("read", {"file_path": "/app/main.py"}, "c", True, 50)
                uocs.capture("edit", {"file_path": "/app/config.py", "old_string": "a", "new_string": "b"}, "ok", True, 100)

                time.sleep(0.2)

                summary = uocs.get_summary()

                assert "files_touched" in summary
                assert "/app/main.py" in summary["files_touched"]
                assert "/app/config.py" in summary["files_touched"]


class TestFilesTouchedIntegration:
    """Tests for files touched integration with session lifecycle."""

    def test_session_end_includes_files_touched(self):
        """Test that session end captures files touched from UOCS."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                # Reset singletons for clean test
                import claude.tools.learning.memory as memory_module
                import claude.tools.learning.session as session_module
                import claude.tools.learning.uocs as uocs_module
                import claude.tools.learning.learn as learn_module
                memory_module._memory = None
                session_module._manager = None
                uocs_module._active_uocs.clear()
                learn_module._learn = None

                from claude.tools.learning.session import SessionManager

                manager = SessionManager()

                # Start session
                session_id = manager.start_session(
                    context_id="ctx_123",
                    initial_query="Fix the config",
                    agent_used="sre_agent"
                )

                # Simulate tool captures
                manager.capture_tool_output(
                    "read",
                    {"file_path": "/app/config.yaml"},
                    "content",
                    True,
                    50
                )
                manager.capture_tool_output(
                    "edit",
                    {"file_path": "/app/config.yaml", "old_string": "a", "new_string": "b"},
                    "success",
                    True,
                    100
                )

                time.sleep(0.2)

                # End session
                result = manager.end_session()

                # Verify files were captured
                recent = manager.memory.get_recent(1)
                import json
                files_touched = json.loads(recent[0]['files_touched'])

                assert "/app/config.yaml" in files_touched


class TestFilesTouchedInputExtraction:
    """Tests for extracting file paths from various input formats."""

    def test_extracts_file_path_key(self):
        """Test extraction from 'file_path' key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.uocs import UOCS

                uocs = UOCS("test")
                uocs.capture("read", {"file_path": "/test/file.py"}, "c", True, 50)
                time.sleep(0.2)

                files = uocs.get_files_touched()
                assert "/test/file.py" in files

    def test_extracts_path_key(self):
        """Test extraction from 'path' key for glob/grep tools."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.uocs import UOCS

                uocs = UOCS("test")
                # glob tool uses 'path' for directory
                uocs.capture("glob", {"pattern": "*.py", "path": "/app/src"}, "files", True, 50)
                time.sleep(0.2)

                files = uocs.get_files_touched()
                # Directories from glob/grep should NOT be included (only actual files)
                assert len(files) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
