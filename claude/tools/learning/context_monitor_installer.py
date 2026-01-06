#!/usr/bin/env python3
"""
Context Monitor LaunchAgent Installer
Phase 237.4.2: Manages macOS LaunchAgent for automatic context monitoring

This module provides utilities to install, uninstall, and manage the
macOS LaunchAgent for the background context monitor.

LaunchAgent Features:
- Auto-start on login (RunAtLoad=true)
- Auto-restart on crash (KeepAlive=true)
- Configurable threshold and check interval
- Stdout/stderr logging

Usage:
    python3 -m claude.tools.learning.context_monitor_installer install
    python3 -m claude.tools.learning.context_monitor_installer uninstall
    python3 -m claude.tools.learning.context_monitor_installer status

Author: Maia (Phase 237.4.2)
Created: 2026-01-06
"""

import subprocess
import sys
from pathlib import Path
from typing import Dict, Any


# Paths
MAIA_ROOT = Path(__file__).parent.parent.parent
MONITOR_SCRIPT = MAIA_ROOT / 'hooks' / 'context_monitor.py'
LOG_DIR = Path.home() / '.maia' / 'logs'
PLIST_LABEL = 'com.maia.context-monitor'


def get_plist_path() -> Path:
    """
    Get path to LaunchAgent plist file.

    Returns:
        Path to ~/Library/LaunchAgents/com.maia.context-monitor.plist
    """
    return Path.home() / 'Library' / 'LaunchAgents' / f'{PLIST_LABEL}.plist'


def generate_plist(
    monitor_script: str,
    log_dir: str,
    threshold: float = 0.70,
    check_interval: int = 300
) -> str:
    """
    Generate LaunchAgent plist content.

    Args:
        monitor_script: Path to context_monitor.py
        log_dir: Directory for logs
        threshold: Context threshold (0.0-1.0)
        check_interval: Check interval in seconds

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
        <string>{monitor_script}</string>
    </array>

    <key>EnvironmentVariables</key>
    <dict>
        <key>MAIA_CONTEXT_THRESHOLD</key>
        <string>{threshold}</string>
        <key>MAIA_CHECK_INTERVAL</key>
        <string>{check_interval}</string>
    </dict>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>{log_dir}/context_monitor_stdout.log</string>

    <key>StandardErrorPath</key>
    <string>{log_dir}/context_monitor_stderr.log</string>
</dict>
</plist>
"""
    return plist_template


def install(threshold: float = 0.70, check_interval: int = 300) -> bool:
    """
    Install LaunchAgent.

    Creates plist file and loads it with launchctl.

    Args:
        threshold: Context threshold (0.0-1.0)
        check_interval: Check interval in seconds

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
        monitor_script=str(MONITOR_SCRIPT),
        log_dir=str(LOG_DIR),
        threshold=threshold,
        check_interval=check_interval
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

    Unloads service with launchctl and removes plist file.

    Returns:
        True if uninstallation succeeded
    """
    plist_path = get_plist_path()

    if not plist_path.exists():
        print(f"⚠️ LaunchAgent not installed (plist not found)")
        return False

    # Unload with launchctl
    try:
        result = subprocess.run(
            ['launchctl', 'unload', str(plist_path)],
            capture_output=True,
            check=True
        )
        print(f"✅ Unloaded LaunchAgent: {PLIST_LABEL}")

    except subprocess.CalledProcessError as e:
        print(f"⚠️ Failed to unload LaunchAgent (may not be running): {e.stderr.decode()}")

    # Remove plist file
    plist_path.unlink()
    print(f"✅ Removed plist: {plist_path}")

    return True


def is_installed() -> bool:
    """
    Check if LaunchAgent is installed.

    Returns:
        True if plist file exists
    """
    return get_plist_path().exists()


def get_status() -> Dict[str, Any]:
    """
    Get LaunchAgent status.

    Returns:
        Dict with status information:
        {
            'installed': bool,
            'running': bool,
            'threshold': float,
            'check_interval': int
        }
    """
    status = {
        'installed': is_installed(),
        'running': False,
        'threshold': 0.70,
        'check_interval': 300
    }

    if not status['installed']:
        return status

    # Check if running with launchctl
    try:
        result = subprocess.run(
            ['launchctl', 'list', PLIST_LABEL],
            capture_output=True,
            check=True
        )

        # Parse output to check if PID exists
        output = result.stdout.decode()
        if 'PID' in output and 'PID" = ' in output:
            status['running'] = True

    except subprocess.CalledProcessError:
        # Service not loaded or not running
        status['running'] = False

    return status


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Manage Context Monitor LaunchAgent'
    )

    subparsers = parser.add_subparsers(dest='command', help='Command')

    # Install command
    install_parser = subparsers.add_parser('install', help='Install LaunchAgent')
    install_parser.add_argument(
        '--threshold',
        type=float,
        default=0.70,
        help='Context threshold (0.0-1.0, default: 0.70)'
    )
    install_parser.add_argument(
        '--interval',
        type=int,
        default=300,
        help='Check interval in seconds (default: 300)'
    )

    # Uninstall command
    uninstall_parser = subparsers.add_parser('uninstall', help='Uninstall LaunchAgent')

    # Status command
    status_parser = subparsers.add_parser('status', help='Show LaunchAgent status')

    args = parser.parse_args()

    if args.command == 'install':
        success = install(threshold=args.threshold, check_interval=args.interval)
        sys.exit(0 if success else 1)

    elif args.command == 'uninstall':
        success = uninstall()
        sys.exit(0 if success else 1)

    elif args.command == 'status':
        status = get_status()
        print(f"\nContext Monitor LaunchAgent Status:")
        print(f"  Installed: {'✅ Yes' if status['installed'] else '❌ No'}")
        print(f"  Running:   {'✅ Yes' if status['running'] else '❌ No'}")
        print(f"  Threshold: {status['threshold']*100:.0f}%")
        print(f"  Interval:  {status['check_interval']}s")
        print()
        sys.exit(0)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
