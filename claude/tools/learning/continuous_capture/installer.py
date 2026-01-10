#!/usr/bin/env python3
"""
Continuous Capture Daemon LaunchAgent Installer
Phase 263 Sprint 1 - Phase 7: Manages macOS LaunchAgent for continuous learning capture

This module provides utilities to install, uninstall, and manage the
macOS LaunchAgent for the background continuous capture daemon.

LaunchAgent Features:
- Auto-start on login (RunAtLoad=true)
- Auto-restart on crash (KeepAlive=true)
- Configurable scan interval
- Stdout/stderr logging

Usage:
    python3 -m claude.tools.learning.continuous_capture.installer install
    python3 -m claude.tools.learning.continuous_capture.installer uninstall
    python3 -m claude.tools.learning.continuous_capture.installer status
"""

import subprocess
import sys
from pathlib import Path
from typing import Optional

# Paths
MAIA_ROOT = Path(__file__).parent.parent.parent.parent.parent  # Go up to maia/ directory
DAEMON_SCRIPT = MAIA_ROOT / 'claude' / 'tools' / 'learning' / 'continuous_capture' / 'daemon_runner.py'
LOG_DIR = Path.home() / '.maia' / 'logs'
PLIST_LABEL = 'com.maia.continuous-capture'


def get_plist_path() -> Path:
    """
    Get path to LaunchAgent plist file.

    Returns:
        Path to ~/Library/LaunchAgents/com.maia.continuous-capture.plist
    """
    return Path.home() / 'Library' / 'LaunchAgents' / f'{PLIST_LABEL}.plist'


def generate_plist(
    daemon_script: str,
    log_dir: str,
    maia_root: str,
    scan_interval: int = 180
) -> str:
    """
    Generate LaunchAgent plist content.

    Args:
        daemon_script: Path to daemon.py
        log_dir: Directory for logs
        maia_root: MAIA root directory (for PYTHONPATH)
        scan_interval: Scan interval in seconds (default: 180 = 3 minutes)

    Returns:
        Plist XML content as string
    """
    plist_template = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{PLIST_LABEL}</string>

    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>{daemon_script}</string>
    </array>

    <key>EnvironmentVariables</key>
    <dict>
        <key>MAIA_SCAN_INTERVAL</key>
        <string>{scan_interval}</string>
        <key>PYTHONPATH</key>
        <string>{maia_root}</string>
    </dict>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>{log_dir}/continuous_capture_stdout.log</string>

    <key>StandardErrorPath</key>
    <string>{log_dir}/continuous_capture_stderr.log</string>
</dict>
</plist>
"""
    return plist_template


def install(scan_interval: int = 180) -> bool:
    """
    Install LaunchAgent.

    Creates plist file and loads it with launchctl.

    Args:
        scan_interval: Scan interval in seconds (default: 180 = 3 minutes)

    Returns:
        True if installation succeeded
    """
    plist_path = get_plist_path()

    # Create LaunchAgents directory if needed
    plist_path.parent.mkdir(parents=True, exist_ok=True)

    # Create log directory
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # Generate plist content
    plist_content = generate_plist(
        daemon_script=str(DAEMON_SCRIPT),
        log_dir=str(LOG_DIR),
        maia_root=str(MAIA_ROOT),
        scan_interval=scan_interval
    )

    # Write plist file
    plist_path.write_text(plist_content)

    print(f"✅ Created plist: {plist_path}")

    # Load with launchctl
    try:
        result = subprocess.run(
            ['launchctl', 'load', str(plist_path)],
            capture_output=True,
            check=True
        )
        print(f"✅ Loaded LaunchAgent: {PLIST_LABEL}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to load LaunchAgent: {e.stderr.decode()}")
        return False


def uninstall() -> bool:
    """
    Uninstall LaunchAgent.

    Unloads with launchctl and removes plist file.

    Returns:
        True if uninstallation succeeded
    """
    plist_path = get_plist_path()

    # Unload with launchctl (attempt even if plist missing)
    try:
        subprocess.run(
            ['launchctl', 'unload', str(plist_path)],
            capture_output=True,
            check=False  # Don't fail if already unloaded
        )
        print(f"✅ Unloaded LaunchAgent: {PLIST_LABEL}")
    except Exception as e:
        print(f"⚠️  Unload warning: {e}")

    # Remove plist file
    if plist_path.exists():
        plist_path.unlink()
        print(f"✅ Removed plist: {plist_path}")
        return True
    else:
        print(f"ℹ️  Plist not found: {plist_path}")
        return True  # Not an error if already removed


def status() -> bool:
    """
    Check if daemon is running.

    Returns:
        True if daemon is running, False otherwise
    """
    try:
        result = subprocess.run(
            ['launchctl', 'list'],
            capture_output=True,
            check=True
        )

        # Check if our label appears in output
        output = result.stdout.decode()
        is_running = PLIST_LABEL in output

        if is_running:
            print(f"✅ Daemon is running: {PLIST_LABEL}")
        else:
            print(f"❌ Daemon not running: {PLIST_LABEL}")

        return is_running

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to check status: {e.stderr.decode()}")
        return False


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python3 -m claude.tools.learning.continuous_capture.installer {install|uninstall|status}")
        print("\nOptions:")
        print("  install [interval]  - Install LaunchAgent (optional scan interval in seconds)")
        print("  uninstall           - Uninstall LaunchAgent")
        print("  status              - Check daemon status")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'install':
        scan_interval = int(sys.argv[2]) if len(sys.argv) > 2 else 180
        success = install(scan_interval=scan_interval)
        sys.exit(0 if success else 1)

    elif command == 'uninstall':
        success = uninstall()
        sys.exit(0 if success else 1)

    elif command == 'status':
        is_running = status()
        sys.exit(0 if is_running else 1)

    else:
        print(f"Unknown command: {command}")
        print("Valid commands: install, uninstall, status")
        sys.exit(1)


if __name__ == '__main__':
    main()
