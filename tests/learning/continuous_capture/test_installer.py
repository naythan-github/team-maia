#!/usr/bin/env python3
"""
Phase 7: LaunchAgent Installer - TDD Tests

Tests for continuous capture daemon LaunchAgent installer.
Manages macOS LaunchAgent for automatic continuous learning capture.
"""

import pytest
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

from claude.tools.learning.continuous_capture.installer import (
    generate_plist,
    get_plist_path,
    install,
    uninstall,
    status
)


class TestPlistGeneration:
    """Test plist XML generation."""

    def test_generates_valid_plist(self, tmp_path):
        """Should generate valid plist XML."""
        daemon_script = "/path/to/daemon.py"
        log_dir = "/path/to/logs"
        maia_root = "/path/to/maia"

        plist_content = generate_plist(
            daemon_script=daemon_script,
            log_dir=log_dir,
            maia_root=maia_root,
            scan_interval=180
        )

        # Verify XML structure
        assert '<?xml version="1.0" encoding="UTF-8"?>' in plist_content
        assert '<!DOCTYPE plist' in plist_content
        assert '<plist version="1.0">' in plist_content

        # Verify label
        assert '<key>Label</key>' in plist_content
        assert '<string>com.maia.continuous-capture</string>' in plist_content

        # Verify program arguments
        assert '<key>ProgramArguments</key>' in plist_content
        assert '<string>/usr/bin/python3</string>' in plist_content
        assert f'<string>{daemon_script}</string>' in plist_content

        # Verify environment variables
        assert '<key>EnvironmentVariables</key>' in plist_content
        assert '<key>MAIA_SCAN_INTERVAL</key>' in plist_content
        assert '<string>180</string>' in plist_content
        assert '<key>PYTHONPATH</key>' in plist_content
        assert f'<string>{maia_root}</string>' in plist_content

        # Verify launch settings
        assert '<key>RunAtLoad</key>' in plist_content
        assert '<true/>' in plist_content
        assert '<key>KeepAlive</key>' in plist_content

        # Verify logging paths
        assert '<key>StandardOutPath</key>' in plist_content
        assert f'<string>{log_dir}/continuous_capture_stdout.log</string>' in plist_content
        assert '<key>StandardErrorPath</key>' in plist_content
        assert f'<string>{log_dir}/continuous_capture_stderr.log</string>' in plist_content

    def test_includes_custom_scan_interval(self):
        """Should include custom scan interval in environment."""
        plist_content = generate_plist(
            daemon_script="/path/to/daemon.py",
            log_dir="/logs",
            maia_root="/path/to/maia",
            scan_interval=120  # 2 minutes
        )

        assert '<key>MAIA_SCAN_INTERVAL</key>' in plist_content
        assert '<string>120</string>' in plist_content

    def test_includes_all_required_keys(self):
        """Should include all required LaunchAgent keys."""
        plist_content = generate_plist(
            daemon_script="/path/to/daemon.py",
            log_dir="/logs",
            maia_root="/path/to/maia"
        )

        required_keys = [
            '<key>Label</key>',
            '<key>ProgramArguments</key>',
            '<key>RunAtLoad</key>',
            '<key>KeepAlive</key>',
            '<key>StandardOutPath</key>',
            '<key>StandardErrorPath</key>'
        ]

        for key in required_keys:
            assert key in plist_content, f"Missing required key: {key}"


class TestInstaller:
    """Test installation functionality."""

    def test_installs_to_correct_location(self):
        """Should install plist to ~/Library/LaunchAgents/."""
        plist_path = get_plist_path()

        expected_path = Path.home() / 'Library' / 'LaunchAgents' / 'com.maia.continuous-capture.plist'
        assert plist_path == expected_path, "Should use correct LaunchAgents location"

    @patch('subprocess.run')
    def test_creates_plist_file_on_install(self, mock_run, tmp_path):
        """Should create plist file when installing."""
        # Mock successful launchctl
        mock_run.return_value = MagicMock(returncode=0)

        # Override plist path for testing
        test_plist_path = tmp_path / "LaunchAgents" / "com.maia.continuous-capture.plist"

        with patch('claude.tools.learning.continuous_capture.installer.get_plist_path', return_value=test_plist_path):
            with patch('claude.tools.learning.continuous_capture.installer.DAEMON_SCRIPT', tmp_path / "daemon.py"):
                with patch('claude.tools.learning.continuous_capture.installer.LOG_DIR', tmp_path / "logs"):
                    # Create daemon script (installer checks it exists)
                    daemon_script = tmp_path / "daemon.py"
                    daemon_script.parent.mkdir(parents=True, exist_ok=True)
                    daemon_script.touch()

                    # Install
                    result = install(scan_interval=180)

                    # Verify file created
                    assert test_plist_path.exists(), "Should create plist file"

                    # Verify content
                    content = test_plist_path.read_text()
                    assert 'com.maia.continuous-capture' in content

    @patch('subprocess.run')
    def test_loads_with_launchctl(self, mock_run, tmp_path):
        """Should call launchctl load after creating plist."""
        mock_run.return_value = MagicMock(returncode=0)

        test_plist_path = tmp_path / "LaunchAgents" / "com.maia.continuous-capture.plist"

        with patch('claude.tools.learning.continuous_capture.installer.get_plist_path', return_value=test_plist_path):
            with patch('claude.tools.learning.continuous_capture.installer.DAEMON_SCRIPT', tmp_path / "daemon.py"):
                with patch('claude.tools.learning.continuous_capture.installer.LOG_DIR', tmp_path / "logs"):
                    # Create daemon script
                    daemon_script = tmp_path / "daemon.py"
                    daemon_script.parent.mkdir(parents=True, exist_ok=True)
                    daemon_script.touch()

                    # Install
                    install(scan_interval=180)

                    # Verify launchctl was called
                    mock_run.assert_called_once()
                    call_args = mock_run.call_args[0][0]
                    assert call_args[0] == 'launchctl'
                    assert call_args[1] == 'load'
                    assert str(test_plist_path) in call_args


class TestUninstaller:
    """Test uninstallation functionality."""

    @patch('subprocess.run')
    def test_uninstall_removes_plist(self, mock_run, tmp_path):
        """Should remove plist file when uninstalling."""
        mock_run.return_value = MagicMock(returncode=0)

        # Create fake plist
        test_plist_path = tmp_path / "com.maia.continuous-capture.plist"
        test_plist_path.write_text("fake plist")

        with patch('claude.tools.learning.continuous_capture.installer.get_plist_path', return_value=test_plist_path):
            # Uninstall
            result = uninstall()

            # Verify file removed
            assert not test_plist_path.exists(), "Should remove plist file"

    @patch('subprocess.run')
    def test_unloads_with_launchctl(self, mock_run, tmp_path):
        """Should call launchctl unload before removing plist."""
        mock_run.return_value = MagicMock(returncode=0)

        test_plist_path = tmp_path / "com.maia.continuous-capture.plist"
        test_plist_path.write_text("fake plist")

        with patch('claude.tools.learning.continuous_capture.installer.get_plist_path', return_value=test_plist_path):
            uninstall()

            # Verify launchctl was called
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert call_args[0] == 'launchctl'
            assert call_args[1] == 'unload'

    @patch('subprocess.run')
    def test_uninstall_handles_missing_plist(self, mock_run, tmp_path):
        """Should handle gracefully if plist doesn't exist."""
        test_plist_path = tmp_path / "nonexistent.plist"

        with patch('claude.tools.learning.continuous_capture.installer.get_plist_path', return_value=test_plist_path):
            # Should not crash
            result = uninstall()

            # Should still attempt unload (in case LaunchAgent is loaded)
            assert mock_run.called


class TestStatus:
    """Test status checking functionality."""

    @patch('subprocess.run')
    def test_status_checks_launchctl(self, mock_run):
        """Should use launchctl to check daemon status."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=b"com.maia.continuous-capture"
        )

        result = status()

        # Verify launchctl was called
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == 'launchctl'
        assert call_args[1] == 'list'

    @patch('subprocess.run')
    def test_status_returns_true_when_running(self, mock_run):
        """Should return True if daemon is running."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=b"12345\t0\tcom.maia.continuous-capture"
        )

        result = status()

        assert result is True, "Should return True when daemon is running"

    @patch('subprocess.run')
    def test_status_returns_false_when_not_running(self, mock_run):
        """Should return False if daemon not in launchctl list."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=b"other.daemon.name"
        )

        result = status()

        assert result is False, "Should return False when daemon not running"
