#!/usr/bin/env python3
"""
Tests for P3: Cleanup Scheduling - Launchd plist for daily cleanup (TDD)

Phase 234: Automated cleanup of old UOCS outputs via launchd.
"""

import pytest
import tempfile
import plistlib
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess


class TestLaunchdPlistGeneration:
    """Tests for launchd plist file generation."""

    def test_generate_plist_creates_valid_plist(self):
        """Test that generated plist is valid plistlib format."""
        from claude.tools.learning.cleanup_scheduler import generate_launchd_plist

        plist_content = generate_launchd_plist()

        # Should be parseable as plist
        plist_data = plistlib.loads(plist_content.encode())

        assert "Label" in plist_data
        assert "ProgramArguments" in plist_data

    def test_plist_has_correct_label(self):
        """Test that plist has the correct label."""
        from claude.tools.learning.cleanup_scheduler import generate_launchd_plist

        plist_content = generate_launchd_plist()
        plist_data = plistlib.loads(plist_content.encode())

        assert plist_data["Label"] == "com.maia.uocs-cleanup"

    def test_plist_runs_cleanup_script(self):
        """Test that plist runs the correct cleanup script."""
        from claude.tools.learning.cleanup_scheduler import generate_launchd_plist

        plist_content = generate_launchd_plist()
        plist_data = plistlib.loads(plist_content.encode())

        program_args = plist_data["ProgramArguments"]

        # Should invoke python3 with uocs_cleanup.py
        assert "python3" in program_args[0] or program_args[0].endswith("python3")
        assert any("uocs_cleanup" in arg for arg in program_args)

    def test_plist_has_daily_schedule(self):
        """Test that plist runs daily."""
        from claude.tools.learning.cleanup_scheduler import generate_launchd_plist

        plist_content = generate_launchd_plist()
        plist_data = plistlib.loads(plist_content.encode())

        # Should have StartCalendarInterval for daily run
        assert "StartCalendarInterval" in plist_data

        interval = plist_data["StartCalendarInterval"]
        assert "Hour" in interval  # Runs at specific hour
        assert "Minute" in interval

    def test_plist_runs_at_3am(self):
        """Test that cleanup runs at 3:00 AM (low activity time)."""
        from claude.tools.learning.cleanup_scheduler import generate_launchd_plist

        plist_content = generate_launchd_plist()
        plist_data = plistlib.loads(plist_content.encode())

        interval = plist_data["StartCalendarInterval"]
        assert interval["Hour"] == 3
        assert interval["Minute"] == 0

    def test_plist_includes_retention_days_arg(self):
        """Test that plist passes retention days argument."""
        from claude.tools.learning.cleanup_scheduler import generate_launchd_plist

        plist_content = generate_launchd_plist(retention_days=14)
        plist_data = plistlib.loads(plist_content.encode())

        program_args = plist_data["ProgramArguments"]
        assert "14" in program_args

    def test_plist_default_retention_7_days(self):
        """Test that default retention is 7 days."""
        from claude.tools.learning.cleanup_scheduler import generate_launchd_plist

        plist_content = generate_launchd_plist()
        plist_data = plistlib.loads(plist_content.encode())

        program_args = plist_data["ProgramArguments"]
        assert "7" in program_args


class TestLaunchdInstallation:
    """Tests for launchd plist installation."""

    def test_get_plist_path_returns_launch_agents_path(self):
        """Test that plist path is in ~/Library/LaunchAgents."""
        from claude.tools.learning.cleanup_scheduler import get_plist_path

        plist_path = get_plist_path()

        assert "Library/LaunchAgents" in str(plist_path)
        assert plist_path.name == "com.maia.uocs-cleanup.plist"

    def test_install_creates_plist_file(self):
        """Test that install creates the plist file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            launch_agents = fake_home / "Library" / "LaunchAgents"
            launch_agents.mkdir(parents=True)

            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.cleanup_scheduler import install_cleanup_schedule

                # Mock subprocess to avoid actually loading the agent
                with patch('subprocess.run') as mock_run:
                    mock_run.return_value = MagicMock(returncode=0)

                    result = install_cleanup_schedule()

                    plist_path = launch_agents / "com.maia.uocs-cleanup.plist"
                    assert plist_path.exists()
                    assert result["installed"] is True

    def test_install_calls_launchctl_load(self):
        """Test that install calls launchctl load."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            launch_agents = fake_home / "Library" / "LaunchAgents"
            launch_agents.mkdir(parents=True)

            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.cleanup_scheduler import install_cleanup_schedule

                with patch('subprocess.run') as mock_run:
                    mock_run.return_value = MagicMock(returncode=0)

                    install_cleanup_schedule()

                    # Verify launchctl load was called
                    calls = [str(c) for c in mock_run.call_args_list]
                    assert any("launchctl" in str(c) and "load" in str(c) for c in calls)

    def test_uninstall_removes_plist_file(self):
        """Test that uninstall removes the plist file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            launch_agents = fake_home / "Library" / "LaunchAgents"
            launch_agents.mkdir(parents=True)

            # Create plist file
            plist_path = launch_agents / "com.maia.uocs-cleanup.plist"
            plist_path.write_text("test")

            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.cleanup_scheduler import uninstall_cleanup_schedule

                with patch('subprocess.run') as mock_run:
                    mock_run.return_value = MagicMock(returncode=0)

                    result = uninstall_cleanup_schedule()

                    assert not plist_path.exists()
                    assert result["uninstalled"] is True

    def test_uninstall_calls_launchctl_unload(self):
        """Test that uninstall calls launchctl unload."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            launch_agents = fake_home / "Library" / "LaunchAgents"
            launch_agents.mkdir(parents=True)

            plist_path = launch_agents / "com.maia.uocs-cleanup.plist"
            plist_path.write_text("test")

            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.cleanup_scheduler import uninstall_cleanup_schedule

                with patch('subprocess.run') as mock_run:
                    mock_run.return_value = MagicMock(returncode=0)

                    uninstall_cleanup_schedule()

                    calls = [str(c) for c in mock_run.call_args_list]
                    assert any("launchctl" in str(c) and "unload" in str(c) for c in calls)


class TestCleanupSchedulerStatus:
    """Tests for checking scheduler status."""

    def test_is_installed_returns_true_when_plist_exists(self):
        """Test is_installed returns True when plist file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            launch_agents = fake_home / "Library" / "LaunchAgents"
            launch_agents.mkdir(parents=True)

            plist_path = launch_agents / "com.maia.uocs-cleanup.plist"
            plist_path.write_text("test")

            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.cleanup_scheduler import is_installed

                assert is_installed() is True

    def test_is_installed_returns_false_when_plist_missing(self):
        """Test is_installed returns False when plist file missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            launch_agents = fake_home / "Library" / "LaunchAgents"
            launch_agents.mkdir(parents=True)

            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.cleanup_scheduler import is_installed

                assert is_installed() is False

    def test_get_status_returns_schedule_info(self):
        """Test get_status returns schedule information."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            launch_agents = fake_home / "Library" / "LaunchAgents"
            launch_agents.mkdir(parents=True)

            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.cleanup_scheduler import (
                    install_cleanup_schedule,
                    get_status
                )

                with patch('subprocess.run') as mock_run:
                    mock_run.return_value = MagicMock(returncode=0)

                    install_cleanup_schedule()
                    status = get_status()

                    assert status["installed"] is True
                    assert "schedule" in status
                    assert status["schedule"]["hour"] == 3
                    assert status["retention_days"] == 7


class TestCleanupSchedulerCLI:
    """Tests for CLI interface."""

    def test_cli_install_command(self):
        """Test CLI install command."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            launch_agents = fake_home / "Library" / "LaunchAgents"
            launch_agents.mkdir(parents=True)

            with patch.object(Path, 'home', return_value=fake_home):
                with patch('subprocess.run') as mock_run:
                    mock_run.return_value = MagicMock(returncode=0)

                    from claude.tools.learning.cleanup_scheduler import cli_main

                    result = cli_main(["install"])
                    assert result == 0

    def test_cli_uninstall_command(self):
        """Test CLI uninstall command."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            launch_agents = fake_home / "Library" / "LaunchAgents"
            launch_agents.mkdir(parents=True)

            # Create plist to uninstall
            plist_path = launch_agents / "com.maia.uocs-cleanup.plist"
            plist_path.write_text("test")

            with patch.object(Path, 'home', return_value=fake_home):
                with patch('subprocess.run') as mock_run:
                    mock_run.return_value = MagicMock(returncode=0)

                    from claude.tools.learning.cleanup_scheduler import cli_main

                    result = cli_main(["uninstall"])
                    assert result == 0

    def test_cli_status_command(self):
        """Test CLI status command."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            launch_agents = fake_home / "Library" / "LaunchAgents"
            launch_agents.mkdir(parents=True)

            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.cleanup_scheduler import cli_main

                result = cli_main(["status"])
                assert result == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
