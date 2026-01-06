#!/usr/bin/env python3
"""
Test Context Monitor LaunchAgent - Phase 237.4.2
TDD: Write tests FIRST (RED phase)

Tests for macOS LaunchAgent installer/manager for context monitor.
"""

import os
import plistlib
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
import pytest

# Setup paths for MAIA imports
import sys
maia_root = Path(__file__).parent.parent.parent
if str(maia_root) not in sys.path:
    sys.path.insert(0, str(maia_root))

from claude.tools.learning.context_monitor_installer import (
    generate_plist,
    get_plist_path,
    install,
    uninstall,
    get_status,
    is_installed,
)


class TestLaunchdPlistGeneration:
    """Test LaunchAgent plist generation"""

    def test_generate_plist_creates_valid_plist(self, tmp_path):
        """
        Test LaunchAgent plist generation.

        Given: Monitor script path and log directory
        When: Generate plist
        Then: Should create valid plist with correct structure
        """
        monitor_script = tmp_path / "context_monitor.py"
        log_dir = tmp_path / "logs"

        plist_content = generate_plist(
            monitor_script=str(monitor_script),
            log_dir=str(log_dir)
        )

        # Parse as plist
        plist_data = plistlib.loads(plist_content.encode())

        # Verify structure
        assert 'Label' in plist_data
        assert 'ProgramArguments' in plist_data
        assert 'EnvironmentVariables' in plist_data
        assert 'RunAtLoad' in plist_data
        assert 'KeepAlive' in plist_data

    def test_plist_has_correct_label(self, tmp_path):
        """
        Test plist has correct label.

        Given: Generated plist
        When: Parse plist
        Then: Should have label com.maia.context-monitor
        """
        monitor_script = tmp_path / "context_monitor.py"
        log_dir = tmp_path / "logs"

        plist_content = generate_plist(
            monitor_script=str(monitor_script),
            log_dir=str(log_dir)
        )

        plist_data = plistlib.loads(plist_content.encode())

        assert plist_data['Label'] == 'com.maia.context-monitor'

    def test_plist_has_correct_program_arguments(self, tmp_path):
        """
        Test plist has correct program arguments.

        Given: Generated plist
        When: Parse plist
        Then: Should have python3 and monitor script path
        """
        monitor_script = tmp_path / "context_monitor.py"
        log_dir = tmp_path / "logs"

        plist_content = generate_plist(
            monitor_script=str(monitor_script),
            log_dir=str(log_dir)
        )

        plist_data = plistlib.loads(plist_content.encode())

        prog_args = plist_data['ProgramArguments']
        assert len(prog_args) == 2
        assert prog_args[0] == '/usr/bin/python3'
        assert prog_args[1] == str(monitor_script)

    def test_plist_has_environment_variables(self, tmp_path):
        """
        Test plist has environment variables.

        Given: Generated plist with custom env vars
        When: Parse plist
        Then: Should have MAIA_CONTEXT_THRESHOLD and MAIA_CHECK_INTERVAL
        """
        monitor_script = tmp_path / "context_monitor.py"
        log_dir = tmp_path / "logs"

        plist_content = generate_plist(
            monitor_script=str(monitor_script),
            log_dir=str(log_dir),
            threshold=0.75,
            check_interval=600
        )

        plist_data = plistlib.loads(plist_content.encode())

        env_vars = plist_data['EnvironmentVariables']
        assert env_vars['MAIA_CONTEXT_THRESHOLD'] == '0.75'
        assert env_vars['MAIA_CHECK_INTERVAL'] == '600'

    def test_plist_runs_at_load(self, tmp_path):
        """
        Test plist is configured to run at load.

        Given: Generated plist
        When: Parse plist
        Then: Should have RunAtLoad=true
        """
        monitor_script = tmp_path / "context_monitor.py"
        log_dir = tmp_path / "logs"

        plist_content = generate_plist(
            monitor_script=str(monitor_script),
            log_dir=str(log_dir)
        )

        plist_data = plistlib.loads(plist_content.encode())

        assert plist_data['RunAtLoad'] is True

    def test_plist_keeps_alive(self, tmp_path):
        """
        Test plist is configured to keep alive.

        Given: Generated plist
        When: Parse plist
        Then: Should have KeepAlive=true
        """
        monitor_script = tmp_path / "context_monitor.py"
        log_dir = tmp_path / "logs"

        plist_content = generate_plist(
            monitor_script=str(monitor_script),
            log_dir=str(log_dir)
        )

        plist_data = plistlib.loads(plist_content.encode())

        assert plist_data['KeepAlive'] is True

    def test_plist_has_log_paths(self, tmp_path):
        """
        Test plist has stdout/stderr log paths.

        Given: Generated plist
        When: Parse plist
        Then: Should have StandardOutPath and StandardErrorPath
        """
        monitor_script = tmp_path / "context_monitor.py"
        log_dir = tmp_path / "logs"

        plist_content = generate_plist(
            monitor_script=str(monitor_script),
            log_dir=str(log_dir)
        )

        plist_data = plistlib.loads(plist_content.encode())

        assert 'StandardOutPath' in plist_data
        assert 'StandardErrorPath' in plist_data
        assert str(log_dir) in plist_data['StandardOutPath']
        assert str(log_dir) in plist_data['StandardErrorPath']


class TestLaunchdPlistValidation:
    """Test plist XML validation"""

    def test_plist_xml_is_valid(self, tmp_path):
        """
        Test plist XML validation.

        Given: Generated plist
        When: Validate XML with plistlib
        Then: Should parse without errors
        """
        monitor_script = tmp_path / "context_monitor.py"
        log_dir = tmp_path / "logs"

        plist_content = generate_plist(
            monitor_script=str(monitor_script),
            log_dir=str(log_dir)
        )

        # Should not raise exception
        plist_data = plistlib.loads(plist_content.encode())
        assert plist_data is not None


class TestLaunchdInstallation:
    """Test LaunchAgent installation"""

    def test_get_plist_path_returns_launch_agents_path(self):
        """
        Test get_plist_path returns correct path.

        Given: No arguments
        When: Call get_plist_path()
        Then: Should return ~/Library/LaunchAgents/com.maia.context-monitor.plist
        """
        plist_path = get_plist_path()

        expected = Path.home() / "Library" / "LaunchAgents" / "com.maia.context-monitor.plist"
        assert plist_path == expected

    def test_install_creates_plist_file(self, tmp_path):
        """
        Test LaunchAgent installation creates plist file.

        Given: Mock plist path
        When: Install LaunchAgent
        Then: Should create plist file with correct content
        """
        # Mock paths
        plist_path = tmp_path / "com.maia.context-monitor.plist"
        monitor_script = tmp_path / "context_monitor.py"
        log_dir = tmp_path / "logs"

        # Create dummy script
        monitor_script.write_text("#!/usr/bin/env python3")

        with patch('claude.tools.learning.context_monitor_installer.get_plist_path', return_value=plist_path):
            with patch('claude.tools.learning.context_monitor_installer.MAIA_ROOT', tmp_path.parent):
                with patch('claude.tools.learning.context_monitor_installer.LOG_DIR', log_dir):
                    with patch('subprocess.run') as mock_run:
                        mock_run.return_value = MagicMock(returncode=0)

                        result = install()

                        assert result is True
                        assert plist_path.exists()

                        # Verify content
                        plist_data = plistlib.loads(plist_path.read_bytes())
                        assert plist_data['Label'] == 'com.maia.context-monitor'

    def test_install_calls_launchctl_load(self, tmp_path):
        """
        Test installation calls launchctl load.

        Given: Plist file created
        When: Install LaunchAgent
        Then: Should call launchctl load
        """
        plist_path = tmp_path / "com.maia.context-monitor.plist"
        monitor_script = tmp_path / "context_monitor.py"
        log_dir = tmp_path / "logs"

        monitor_script.write_text("#!/usr/bin/env python3")

        with patch('claude.tools.learning.context_monitor_installer.get_plist_path', return_value=plist_path):
            with patch('claude.tools.learning.context_monitor_installer.MAIA_ROOT', tmp_path.parent):
                with patch('claude.tools.learning.context_monitor_installer.LOG_DIR', log_dir):
                    with patch('subprocess.run') as mock_run:
                        mock_run.return_value = MagicMock(returncode=0)

                        install()

                        # Verify launchctl load was called
                        mock_run.assert_called_once()
                        call_args = mock_run.call_args[0][0]
                        assert 'launchctl' in call_args
                        assert 'load' in call_args
                        assert str(plist_path) in call_args


class TestLaunchdUninstallation:
    """Test LaunchAgent uninstallation"""

    def test_uninstall_removes_plist_file(self, tmp_path):
        """
        Test LaunchAgent uninstallation removes plist.

        Given: Installed LaunchAgent (plist exists)
        When: Uninstall
        Then: Should remove plist file
        """
        plist_path = tmp_path / "com.maia.context-monitor.plist"

        # Create dummy plist
        plist_data = {'Label': 'com.maia.context-monitor'}
        plist_path.write_bytes(plistlib.dumps(plist_data))

        with patch('claude.tools.learning.context_monitor_installer.get_plist_path', return_value=plist_path):
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(returncode=0)

                result = uninstall()

                assert result is True
                assert not plist_path.exists()

    def test_uninstall_calls_launchctl_unload(self, tmp_path):
        """
        Test uninstallation calls launchctl unload.

        Given: Installed LaunchAgent
        When: Uninstall
        Then: Should call launchctl unload before removing plist
        """
        plist_path = tmp_path / "com.maia.context-monitor.plist"

        # Create dummy plist
        plist_data = {'Label': 'com.maia.context-monitor'}
        plist_path.write_bytes(plistlib.dumps(plist_data))

        with patch('claude.tools.learning.context_monitor_installer.get_plist_path', return_value=plist_path):
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(returncode=0)

                uninstall()

                # Verify launchctl unload was called
                mock_run.assert_called_once()
                call_args = mock_run.call_args[0][0]
                assert 'launchctl' in call_args
                assert 'unload' in call_args
                assert str(plist_path) in call_args


class TestLaunchdStatus:
    """Test LaunchAgent status checking"""

    def test_is_installed_returns_true_when_plist_exists(self, tmp_path):
        """
        Test is_installed returns True when plist exists.

        Given: Plist file exists
        When: Check is_installed()
        Then: Should return True
        """
        plist_path = tmp_path / "com.maia.context-monitor.plist"
        plist_path.touch()

        with patch('claude.tools.learning.context_monitor_installer.get_plist_path', return_value=plist_path):
            assert is_installed() is True

    def test_is_installed_returns_false_when_plist_missing(self, tmp_path):
        """
        Test is_installed returns False when plist doesn't exist.

        Given: No plist file
        When: Check is_installed()
        Then: Should return False
        """
        plist_path = tmp_path / "com.maia.context-monitor.plist"

        with patch('claude.tools.learning.context_monitor_installer.get_plist_path', return_value=plist_path):
            assert is_installed() is False

    def test_get_status_returns_status_info(self):
        """
        Test get_status returns status information.

        Given: LaunchAgent installed
        When: Get status
        Then: Should return dict with installed, running, threshold, interval
        """
        with patch('claude.tools.learning.context_monitor_installer.is_installed', return_value=True):
            with patch('subprocess.run') as mock_run:
                # Mock launchctl list output (running)
                mock_run.return_value = MagicMock(
                    returncode=0,
                    stdout=b'"PID" = 12345;\n'
                )

                status = get_status()

                assert status['installed'] is True
                assert 'running' in status
                assert 'threshold' in status
                assert 'check_interval' in status
