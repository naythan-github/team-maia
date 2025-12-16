#!/usr/bin/env python3
"""
Emergency Kill Switch
Provides emergency shutdown capability for all Maia processes.

Use this in case of:
- Security breach detected
- Runaway processes
- System instability
- Manual emergency shutdown

Features:
- Lists all Maia services before shutdown
- Graceful shutdown with timeout
- Force kill option
- Dry run mode for safety
- Audit logging
"""

import os
import subprocess
import signal
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("kill-switch")


class EmergencyKillSwitch:
    """
    Emergency shutdown system for Maia processes.

    Usage:
        ks = EmergencyKillSwitch()
        services = ks.list_maia_services()
        result = ks.execute(dry_run=True)  # Preview what would stop
        result = ks.execute()  # Actually stop everything
    """

    MAIA_IDENTIFIERS = [
        'com.maia.',           # LaunchAgent prefix
        'maia/claude',         # Path identifier
        'maia.security',       # Module names
        'maia.tools',
    ]

    def __init__(self):
        """Initialize kill switch"""
        self.home = Path.home()
        self.launch_agents_dir = self.home / "Library" / "LaunchAgents"
        self.audit_log_path = self.home / ".maia" / "kill_switch_audit.log"
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)

    def _audit_log(self, action: str, details: str):
        """Log kill switch actions"""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "action": action,
                "details": details
            }
            with open(self.audit_log_path, 'a') as f:
                f.write(f"{log_entry}\n")
        except Exception as e:
            logger.warning(f"Failed to write audit log: {e}")

    def list_maia_services(self) -> List[Dict[str, Any]]:
        """
        List all running Maia services.

        Returns:
            List of dicts with service info (name, pid, status)
        """
        services = []

        try:
            # Get launchctl list
            result = subprocess.run(
                ['launchctl', 'list'],
                capture_output=True,
                text=True
            )

            for line in result.stdout.strip().split('\n')[1:]:  # Skip header
                parts = line.split('\t')
                if len(parts) >= 3:
                    pid, status, name = parts[0], parts[1], parts[2]

                    # Check if it's a Maia service
                    if any(ident in name.lower() for ident in ['maia']):
                        services.append({
                            'name': name,
                            'pid': pid if pid != '-' else None,
                            'status': status,
                            'type': 'launchagent'
                        })

        except Exception as e:
            logger.error(f"Failed to list LaunchAgents: {e}")

        # Also check for running Python processes
        try:
            result = subprocess.run(
                ['pgrep', '-fl', 'python.*maia'],
                capture_output=True,
                text=True
            )

            for line in result.stdout.strip().split('\n'):
                if line and 'maia' in line.lower():
                    parts = line.split(None, 1)
                    if len(parts) >= 2:
                        pid, cmd = parts[0], parts[1]
                        # Avoid duplicates from LaunchAgent list
                        if not any(s.get('pid') == pid for s in services):
                            services.append({
                                'name': cmd[:50] + '...' if len(cmd) > 50 else cmd,
                                'pid': pid,
                                'status': 'running',
                                'type': 'process'
                            })

        except Exception as e:
            logger.debug(f"pgrep failed (may be normal): {e}")

        return services

    def _unload_launchagent(self, service_name: str, force: bool = False) -> bool:
        """Unload a LaunchAgent"""
        plist_path = self.launch_agents_dir / f"{service_name}.plist"

        if not plist_path.exists():
            logger.warning(f"Plist not found: {plist_path}")
            return False

        try:
            cmd = ['launchctl', 'unload']
            if force:
                cmd.append('-w')  # Remove from launchd database
            cmd.append(str(plist_path))

            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0

        except Exception as e:
            logger.error(f"Failed to unload {service_name}: {e}")
            return False

    def _kill_process(self, pid: str, graceful: bool = True) -> bool:
        """Kill a process by PID"""
        try:
            pid_int = int(pid)

            if graceful:
                # Try SIGTERM first
                os.kill(pid_int, signal.SIGTERM)
                time.sleep(1)

                # Check if still running
                try:
                    os.kill(pid_int, 0)  # Check if process exists
                    # Still running, use SIGKILL
                    os.kill(pid_int, signal.SIGKILL)
                except ProcessLookupError:
                    pass  # Process already terminated
            else:
                # Force kill immediately
                os.kill(pid_int, signal.SIGKILL)

            return True

        except (ValueError, ProcessLookupError, PermissionError) as e:
            logger.error(f"Failed to kill PID {pid}: {e}")
            return False

    def execute(self, dry_run: bool = False, force: bool = False,
                include_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Execute emergency shutdown.

        Args:
            dry_run: If True, only report what would be stopped
            force: If True, use force kill (SIGKILL) instead of graceful
            include_types: List of service types to stop ('launchagent', 'process')
                          If None, stops all types

        Returns:
            Dict with results:
                - stopped: list of stopped services
                - failed: list of services that failed to stop
                - would_stop: (dry_run only) list of services that would be stopped
        """
        services = self.list_maia_services()

        if include_types:
            services = [s for s in services if s['type'] in include_types]

        if dry_run:
            self._audit_log('dry_run', f"Would stop {len(services)} services")
            return {
                'would_stop': services,
                'dry_run': True
            }

        # Log the shutdown
        self._audit_log('execute', f"Stopping {len(services)} services (force={force})")
        logger.warning(f"EMERGENCY SHUTDOWN: Stopping {len(services)} Maia services")

        stopped = []
        failed = []

        for service in services:
            success = False

            if service['type'] == 'launchagent':
                success = self._unload_launchagent(service['name'], force=force)
            elif service['type'] == 'process' and service['pid']:
                success = self._kill_process(service['pid'], graceful=not force)

            if success:
                stopped.append(service)
                logger.info(f"Stopped: {service['name']}")
            else:
                failed.append(service)
                logger.error(f"Failed to stop: {service['name']}")

        # Final audit log
        self._audit_log('complete',
                        f"Stopped {len(stopped)}/{len(services)} services, "
                        f"failed: {len(failed)}")

        return {
            'stopped': stopped,
            'failed': failed,
            'total': len(services)
        }

    def restart_services(self) -> Dict[str, Any]:
        """
        Restart all Maia LaunchAgents.

        Returns:
            Dict with loaded service names
        """
        loaded = []
        failed = []

        try:
            for plist in self.launch_agents_dir.glob("com.maia.*.plist"):
                try:
                    result = subprocess.run(
                        ['launchctl', 'load', str(plist)],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        loaded.append(plist.stem)
                    else:
                        failed.append(plist.stem)
                except Exception as e:
                    logger.error(f"Failed to load {plist.stem}: {e}")
                    failed.append(plist.stem)

        except Exception as e:
            logger.error(f"Failed to restart services: {e}")

        self._audit_log('restart', f"Loaded {len(loaded)} services")

        return {
            'loaded': loaded,
            'failed': failed
        }


def main():
    """CLI interface for emergency kill switch"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Emergency Kill Switch for Maia Services',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  List services:        python3 emergency_kill_switch.py --list
  Dry run:              python3 emergency_kill_switch.py --dry-run
  Stop all:             python3 emergency_kill_switch.py --execute
  Force stop:           python3 emergency_kill_switch.py --execute --force
  Restart services:     python3 emergency_kill_switch.py --restart
        """
    )

    parser.add_argument('--list', '-l', action='store_true',
                        help='List all Maia services')
    parser.add_argument('--dry-run', '-n', action='store_true',
                        help='Show what would be stopped without stopping')
    parser.add_argument('--execute', '-x', action='store_true',
                        help='Execute emergency shutdown')
    parser.add_argument('--force', '-f', action='store_true',
                        help='Force kill (SIGKILL) instead of graceful shutdown')
    parser.add_argument('--restart', '-r', action='store_true',
                        help='Restart all Maia LaunchAgents')

    args = parser.parse_args()

    ks = EmergencyKillSwitch()

    if args.list:
        services = ks.list_maia_services()
        print(f"Found {len(services)} Maia services:")
        for s in services:
            status = f"PID {s['pid']}" if s['pid'] else "not running"
            print(f"  [{s['type']}] {s['name']} - {status}")

    elif args.dry_run:
        result = ks.execute(dry_run=True)
        print(f"Would stop {len(result['would_stop'])} services:")
        for s in result['would_stop']:
            print(f"  [{s['type']}] {s['name']}")

    elif args.execute:
        confirm = input("Are you sure you want to stop all Maia services? (yes/no): ")
        if confirm.lower() == 'yes':
            result = ks.execute(force=args.force)
            print(f"\nStopped {len(result['stopped'])}/{result['total']} services")
            if result['failed']:
                print(f"Failed to stop: {[s['name'] for s in result['failed']]}")
        else:
            print("Aborted")

    elif args.restart:
        result = ks.restart_services()
        print(f"Loaded {len(result['loaded'])} services")
        if result['failed']:
            print(f"Failed: {result['failed']}")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
