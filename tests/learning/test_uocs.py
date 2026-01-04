#!/usr/bin/env python3
"""
Tests for Phase 2: UOCS - Universal Output Capture System (TDD)

Tests tool output capture, async writes, and session summaries.
"""

import pytest
import tempfile
import json
import time
from pathlib import Path
from unittest.mock import patch


class TestUOCSCapture:
    """Tests for UOCS capture functionality."""

    def test_uocs_creates_session_directory(self):
        """Test that UOCS creates session output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.uocs import UOCS

                uocs = UOCS("test_session_001")

                expected_dir = fake_home / ".maia" / "outputs" / "test_session_001"
                assert expected_dir.exists()
                assert expected_dir.is_dir()

    def test_uocs_capture_creates_output_file(self):
        """Test that capture creates output file for 'output' mode tools."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.uocs import UOCS

                uocs = UOCS("test_session")
                capture_id = uocs.capture(
                    tool_name="bash",
                    tool_input={"command": "ls -la"},
                    tool_output="file1.txt\nfile2.txt\nfile3.txt",
                    success=True,
                    latency_ms=150
                )

                # Wait for async write
                time.sleep(0.2)

                assert capture_id == "0001_bash"
                assert len(uocs.captures) == 1

                # Check output file created
                output_file = uocs.outputs_dir / "0001_bash.txt"
                assert output_file.exists()
                assert "file1.txt" in output_file.read_text()

    def test_uocs_capture_metadata_mode(self):
        """Test that metadata mode doesn't create output file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.uocs import UOCS

                uocs = UOCS("test_session")
                uocs.capture(
                    tool_name="read",  # read is metadata mode
                    tool_input={"file_path": "/some/file.py"},
                    tool_output="file contents here...",
                    success=True,
                    latency_ms=50
                )

                time.sleep(0.2)

                assert len(uocs.captures) == 1
                assert uocs.captures[0].capture_mode == "metadata"
                # No output file for metadata mode
                assert uocs.captures[0].output_path is None

    def test_uocs_capture_diff_mode(self):
        """Test that diff mode captures edit diffs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.uocs import UOCS

                uocs = UOCS("test_session")
                uocs.capture(
                    tool_name="edit",
                    tool_input={
                        "file_path": "/some/file.py",
                        "old_string": "def foo():",
                        "new_string": "def bar():"
                    },
                    tool_output="Edit successful",
                    success=True,
                    latency_ms=100
                )

                time.sleep(0.2)

                assert len(uocs.captures) == 1
                assert uocs.captures[0].capture_mode == "diff"

                # Check diff file
                diff_file = uocs.outputs_dir / "0001_edit.diff"
                assert diff_file.exists()
                content = diff_file.read_text()
                assert "def foo():" in content
                assert "def bar():" in content

    def test_uocs_capture_truncates_large_output(self):
        """Test that large outputs are truncated."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.uocs import UOCS

                uocs = UOCS("test_session")

                # Create output larger than MAX_OUTPUT_SIZE
                large_output = "x" * 150_000

                uocs.capture(
                    tool_name="bash",
                    tool_input={"command": "cat bigfile"},
                    tool_output=large_output,
                    success=True,
                    latency_ms=500
                )

                time.sleep(0.2)

                output_file = uocs.outputs_dir / "0001_bash.txt"
                content = output_file.read_text()

                # Should be truncated
                assert len(content) <= UOCS.MAX_OUTPUT_SIZE + 100  # buffer for truncation message
                assert "TRUNCATED" in content

    def test_uocs_captures_multiple_tools(self):
        """Test capturing multiple tool outputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.uocs import UOCS

                uocs = UOCS("test_session")

                uocs.capture("bash", {"cmd": "ls"}, "output1", True, 100)
                uocs.capture("grep", {"pattern": "test"}, "match1\nmatch2", True, 50)
                uocs.capture("read", {"file": "x.py"}, "content", True, 25)
                uocs.capture("bash", {"cmd": "pwd"}, "/home/user", True, 10)

                time.sleep(0.3)

                assert len(uocs.captures) == 4
                # Async threads may complete in any order, so check IDs exist
                capture_ids = {c.capture_id for c in uocs.captures}
                assert "0001_bash" in capture_ids
                assert "0002_grep" in capture_ids
                assert "0003_read" in capture_ids
                assert "0004_bash" in capture_ids

    def test_uocs_records_success_status(self):
        """Test that success/failure status is recorded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.uocs import UOCS

                uocs = UOCS("test_session")

                uocs.capture("bash", {"cmd": "ls"}, "output", True, 100)
                uocs.capture("bash", {"cmd": "bad"}, "error", False, 50)

                time.sleep(0.2)

                # Find captures by ID (async order not guaranteed)
                captures_by_id = {c.capture_id: c for c in uocs.captures}
                assert captures_by_id["0001_bash"].success is True
                assert captures_by_id["0002_bash"].success is False


class TestUOCSManifest:
    """Tests for UOCS manifest generation."""

    def test_uocs_writes_manifest(self):
        """Test that manifest.json is created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.uocs import UOCS

                uocs = UOCS("test_session")
                uocs.capture("bash", {"cmd": "ls"}, "output", True, 100)

                time.sleep(0.2)

                manifest_path = uocs.outputs_dir / "manifest.json"
                assert manifest_path.exists()

                manifest = json.loads(manifest_path.read_text())
                assert manifest["session_id"] == "test_session"
                assert manifest["capture_count"] == 1
                assert len(manifest["captures"]) == 1

    def test_uocs_manifest_updates_on_each_capture(self):
        """Test that manifest is updated after each capture."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.uocs import UOCS

                uocs = UOCS("test_session")

                uocs.capture("bash", {"cmd": "ls"}, "out1", True, 100)
                time.sleep(0.15)

                manifest = json.loads((uocs.outputs_dir / "manifest.json").read_text())
                assert manifest["capture_count"] == 1

                uocs.capture("grep", {"p": "x"}, "out2", True, 50)
                time.sleep(0.15)

                manifest = json.loads((uocs.outputs_dir / "manifest.json").read_text())
                assert manifest["capture_count"] == 2


class TestUOCSSummary:
    """Tests for UOCS summary generation."""

    def test_uocs_get_summary(self):
        """Test get_summary returns correct statistics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.uocs import UOCS

                uocs = UOCS("test_session")

                uocs.capture("bash", {}, "out1", True, 100)
                uocs.capture("bash", {}, "out2", True, 50)
                uocs.capture("read", {}, "out3", False, 25)
                uocs.capture("grep", {}, "out4", True, 75)

                time.sleep(0.3)

                summary = uocs.get_summary()

                assert summary["session_id"] == "test_session"
                assert summary["total_captures"] == 4
                assert summary["tools_used"]["bash"] == 2
                assert summary["tools_used"]["read"] == 1
                assert summary["tools_used"]["grep"] == 1
                assert summary["success_rate"] == pytest.approx(0.75, rel=0.01)
                assert summary["total_latency_ms"] == 250

    def test_uocs_finalize_writes_summary(self):
        """Test finalize writes summary.json."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.uocs import UOCS

                uocs = UOCS("test_session")
                uocs.capture("bash", {}, "out", True, 100)

                time.sleep(0.2)

                summary = uocs.finalize()

                summary_path = uocs.outputs_dir / "summary.json"
                assert summary_path.exists()

                saved_summary = json.loads(summary_path.read_text())
                assert saved_summary["session_id"] == "test_session"
                assert saved_summary["total_captures"] == 1


class TestUOCSSingleton:
    """Tests for UOCS singleton pattern."""

    def test_get_uocs_returns_same_instance(self):
        """Test that get_uocs returns same instance for same session."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.uocs import get_uocs, _active_uocs

                # Clear any existing
                _active_uocs.clear()

                uocs1 = get_uocs("session_a")
                uocs2 = get_uocs("session_a")
                uocs3 = get_uocs("session_b")

                assert uocs1 is uocs2
                assert uocs1 is not uocs3

    def test_close_uocs_removes_and_finalizes(self):
        """Test that close_uocs finalizes and removes session."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.uocs import get_uocs, close_uocs, _active_uocs

                _active_uocs.clear()

                uocs = get_uocs("session_to_close")
                uocs.capture("bash", {}, "out", True, 100)
                time.sleep(0.2)

                summary = close_uocs("session_to_close")

                assert summary is not None
                assert summary["session_id"] == "session_to_close"
                assert "session_to_close" not in _active_uocs

    def test_close_uocs_nonexistent_returns_none(self):
        """Test that closing nonexistent session returns None."""
        from claude.tools.learning.uocs import close_uocs, _active_uocs

        _active_uocs.clear()

        result = close_uocs("nonexistent_session")
        assert result is None


class TestUOCSCleanup:
    """Tests for UOCS cleanup functionality."""

    def test_cleanup_removes_old_directories(self):
        """Test that cleanup removes directories older than threshold."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            outputs_dir = fake_home / ".maia" / "outputs"
            outputs_dir.mkdir(parents=True)

            # Create old session (simulate old mtime)
            old_session = outputs_dir / "old_session"
            old_session.mkdir()
            old_manifest = old_session / "manifest.json"
            old_manifest.write_text('{"session_id": "old"}')

            # Create recent session
            new_session = outputs_dir / "new_session"
            new_session.mkdir()
            new_manifest = new_session / "manifest.json"
            new_manifest.write_text('{"session_id": "new"}')

            # Manually set old mtime (8 days ago)
            import os
            old_time = time.time() - (8 * 24 * 60 * 60)
            os.utime(old_manifest, (old_time, old_time))

            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.uocs_cleanup import cleanup_old_outputs

                removed = cleanup_old_outputs(days=7)

                assert removed == 1
                assert not old_session.exists()
                assert new_session.exists()

    def test_cleanup_keeps_recent_directories(self):
        """Test that cleanup keeps recent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            outputs_dir = fake_home / ".maia" / "outputs"
            outputs_dir.mkdir(parents=True)

            # Create recent session
            session = outputs_dir / "recent_session"
            session.mkdir()
            manifest = session / "manifest.json"
            manifest.write_text('{"session_id": "recent"}')

            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.uocs_cleanup import cleanup_old_outputs

                removed = cleanup_old_outputs(days=7)

                assert removed == 0
                assert session.exists()

    def test_cleanup_handles_missing_directory(self):
        """Test that cleanup handles missing outputs directory gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            # Don't create outputs directory

            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.uocs_cleanup import cleanup_old_outputs

                removed = cleanup_old_outputs(days=7)
                assert removed == 0


class TestUOCSInputHash:
    """Tests for input hashing (deduplication support)."""

    def test_same_input_same_hash(self):
        """Test that same inputs produce same hash."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.uocs import UOCS

                uocs = UOCS("test_session")

                uocs.capture("bash", {"command": "ls -la"}, "out1", True, 100)
                uocs.capture("bash", {"command": "ls -la"}, "out2", True, 100)

                time.sleep(0.2)

                # Same input should have same hash
                assert uocs.captures[0].input_hash == uocs.captures[1].input_hash

    def test_different_input_different_hash(self):
        """Test that different inputs produce different hashes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.uocs import UOCS

                uocs = UOCS("test_session")

                uocs.capture("bash", {"command": "ls -la"}, "out1", True, 100)
                uocs.capture("bash", {"command": "pwd"}, "out2", True, 100)

                time.sleep(0.2)

                # Different input should have different hash
                assert uocs.captures[0].input_hash != uocs.captures[1].input_hash


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
