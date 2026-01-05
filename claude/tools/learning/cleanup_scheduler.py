#!/usr/bin/env python3
"""
Cleanup Scheduler Module

Phase 234: Automated cleanup of old UOCS outputs via launchd.

Provides functions for generating, installing, and managing
a launchd plist that runs daily cleanup of old session outputs.
"""

import json
import plistlib
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Constants
PLIST_LABEL = "com.maia.uocs-cleanup"
DEFAULT_RETENTION_DAYS = 7
DEFAULT_CLEANUP_HOUR = 3  # 3:00 AM


def get_plist_path() -> Path:
    """Get the path to the launchd plist file."""
    return Path.home() / "Library" / "LaunchAgents" / f"{PLIST_LABEL}.plist"


def get_cleanup_script_path() -> Path:
    """Get the path to the cleanup script."""
    # Use the absolute path to uocs_cleanup.py
    return Path(__file__).parent / "uocs_cleanup.py"


def generate_launchd_plist(retention_days: int = DEFAULT_RETENTION_DAYS) -> str:
    """
    Generate launchd plist content for daily cleanup.

    Args:
        retention_days: Number of days to retain outputs (default 7)

    Returns:
        Plist content as string
    """
    cleanup_script = get_cleanup_script_path()

    plist_data = {
        "Label": PLIST_LABEL,
        "ProgramArguments": [
            sys.executable,  # python3 path
            str(cleanup_script),
            str(retention_days)
        ],
        "StartCalendarInterval": {
            "Hour": DEFAULT_CLEANUP_HOUR,
            "Minute": 0
        },
        "StandardOutPath": str(Path.home() / ".maia" / "logs" / "cleanup.log"),
        "StandardErrorPath": str(Path.home() / ".maia" / "logs" / "cleanup.error.log"),
        "RunAtLoad": False,
        "KeepAlive": False,
    }

    return plistlib.dumps(plist_data).decode("utf-8")


def install_cleanup_schedule(retention_days: int = DEFAULT_RETENTION_DAYS) -> Dict[str, Any]:
    """
    Install the cleanup schedule via launchd.

    Creates the plist file and loads it with launchctl.

    Args:
        retention_days: Number of days to retain outputs

    Returns:
        Result dict with installation status
    """
    result = {"installed": False, "error": None}

    try:
        plist_path = get_plist_path()

        # Ensure parent directory exists
        plist_path.parent.mkdir(parents=True, exist_ok=True)

        # Ensure logs directory exists
        logs_dir = Path.home() / ".maia" / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)

        # Generate and write plist
        plist_content = generate_launchd_plist(retention_days)
        plist_path.write_text(plist_content)

        # Load with launchctl
        subprocess.run(
            ["launchctl", "load", str(plist_path)],
            check=True,
            capture_output=True
        )

        result["installed"] = True
        result["plist_path"] = str(plist_path)
        result["retention_days"] = retention_days

    except subprocess.CalledProcessError as e:
        result["error"] = f"launchctl error: {e.stderr.decode()}"
    except Exception as e:
        result["error"] = str(e)

    return result


def uninstall_cleanup_schedule() -> Dict[str, Any]:
    """
    Uninstall the cleanup schedule.

    Unloads from launchctl and removes the plist file.

    Returns:
        Result dict with uninstallation status
    """
    result = {"uninstalled": False, "error": None}

    try:
        plist_path = get_plist_path()

        if plist_path.exists():
            # Unload from launchctl (ignore errors if not loaded)
            subprocess.run(
                ["launchctl", "unload", str(plist_path)],
                capture_output=True  # Don't check - may not be loaded
            )

            # Remove plist file
            plist_path.unlink()

        result["uninstalled"] = True

    except Exception as e:
        result["error"] = str(e)

    return result


def is_installed() -> bool:
    """Check if the cleanup schedule is installed."""
    return get_plist_path().exists()


def get_status() -> Dict[str, Any]:
    """
    Get the current status of the cleanup scheduler.

    Returns:
        Status dict with installation state and configuration
    """
    plist_path = get_plist_path()

    status = {
        "installed": plist_path.exists(),
        "plist_path": str(plist_path),
        "schedule": None,
        "retention_days": None
    }

    if status["installed"]:
        try:
            plist_data = plistlib.loads(plist_path.read_bytes())

            interval = plist_data.get("StartCalendarInterval", {})
            status["schedule"] = {
                "hour": interval.get("Hour"),
                "minute": interval.get("Minute")
            }

            # Extract retention days from program arguments
            args = plist_data.get("ProgramArguments", [])
            if len(args) >= 3:
                try:
                    status["retention_days"] = int(args[2])
                except (ValueError, IndexError):
                    status["retention_days"] = DEFAULT_RETENTION_DAYS
            else:
                status["retention_days"] = DEFAULT_RETENTION_DAYS

        except Exception:
            pass

    return status


def cli_main(args: list) -> int:
    """
    CLI entry point for cleanup scheduler management.

    Args:
        args: Command line arguments (install, uninstall, status)

    Returns:
        Exit code (0 for success)
    """
    if not args:
        print("Usage: cleanup_scheduler.py [install|uninstall|status]")
        return 1

    command = args[0]

    if command == "install":
        retention_days = int(args[1]) if len(args) > 1 else DEFAULT_RETENTION_DAYS
        result = install_cleanup_schedule(retention_days)

        if result["installed"]:
            print(f"Cleanup schedule installed: {result['plist_path']}")
            print(f"Retention: {result['retention_days']} days")
            print(f"Schedule: Daily at {DEFAULT_CLEANUP_HOUR}:00 AM")
            return 0
        else:
            print(f"Installation failed: {result['error']}")
            return 1

    elif command == "uninstall":
        result = uninstall_cleanup_schedule()

        if result["uninstalled"]:
            print("Cleanup schedule uninstalled")
            return 0
        else:
            print(f"Uninstallation failed: {result['error']}")
            return 1

    elif command == "status":
        status = get_status()

        print(f"Installed: {status['installed']}")
        if status["installed"]:
            print(f"Plist: {status['plist_path']}")
            if status["schedule"]:
                print(f"Schedule: Daily at {status['schedule']['hour']}:{status['schedule']['minute']:02d}")
            print(f"Retention: {status['retention_days']} days")

        return 0

    else:
        print(f"Unknown command: {command}")
        return 1


if __name__ == "__main__":
    sys.exit(cli_main(sys.argv[1:]))
