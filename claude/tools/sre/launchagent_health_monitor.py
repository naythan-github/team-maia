#!/usr/bin/env python3
"""
LaunchAgent Health Monitor - SRE Service Health Dashboard

Monitors health and status of all Maia background services (LaunchAgents),
providing observability into service availability and failure patterns.

SRE Pattern: Service Health Monitoring - Continuous health checks with
alerting for failed services and zombie processes.

Usage:
    python3 claude/tools/sre/launchagent_health_monitor.py --status
    python3 claude/tools/sre/launchagent_health_monitor.py --dashboard
    python3 claude/tools/sre/launchagent_health_monitor.py --failed-only
"""

import os
import sys
import subprocess
import json
import plistlib
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class LogFileChecker:
    """Check service log files to determine last run time"""

    def __init__(self, maia_root: Path):
        # Logs are in ~/.maia/logs not ${MAIA_ROOT}/.maia/logs
        self.log_dir = Path.home() / ".maia" / "logs"

    def get_last_run_time(self, service_name: str) -> Optional[datetime]:
        """Get last run time from log file modification time

        Checks both stdout and stderr logs, returns most recent mtime
        """
        short_name = service_name.replace('com.maia.', '').replace('-', '_')

        # Try all common log file patterns
        log_patterns = [
            f"{short_name}.log",
            f"{short_name}.error.log",
            f"{short_name}_error.log",
            f"{short_name}_stdout.log",
            f"{short_name}_stderr.log",
        ]

        most_recent = None

        for pattern in log_patterns:
            log_path = self.log_dir / pattern
            if log_path.exists():
                try:
                    mtime = os.path.getmtime(log_path)
                    file_time = datetime.fromtimestamp(mtime)

                    if most_recent is None or file_time > most_recent:
                        most_recent = file_time
                except (OSError, ValueError):
                    continue

        return most_recent

    def get_time_since_last_run(self, service_name: str) -> Optional[float]:
        """Get seconds since last run (None if never run)"""
        last_run = self.get_last_run_time(service_name)
        if not last_run:
            return None

        return (datetime.now() - last_run).total_seconds()


class ServiceScheduleParser:
    """Parse LaunchAgent plist files to extract schedule configuration"""

    def parse_plist(self, plist_path: Path) -> Dict:
        """Extract schedule information from a LaunchAgent plist

        Returns dict with:
        - service_name: Label from plist
        - service_type: CONTINUOUS, INTERVAL, CALENDAR, TRIGGER, ONE_SHOT
        - schedule_config: Type-specific configuration
        """
        try:
            with open(plist_path, 'rb') as f:
                plist_data = plistlib.load(f)
        except Exception as e:
            return {
                'service_name': plist_path.stem,
                'service_type': 'UNKNOWN',
                'schedule_config': {},
                'error': f"Failed to parse plist: {e}"
            }

        schedule_info = {
            'service_name': plist_data.get('Label', plist_path.stem),
            'service_type': 'ONE_SHOT',  # Default
            'schedule_config': {}
        }

        # Determine service type and extract schedule config
        # Priority: CONTINUOUS > INTERVAL > CALENDAR > TRIGGER > ONE_SHOT

        if plist_data.get('KeepAlive'):
            schedule_info['service_type'] = 'CONTINUOUS'
            schedule_info['schedule_config']['keep_alive'] = plist_data['KeepAlive']

        elif 'StartInterval' in plist_data:
            schedule_info['service_type'] = 'INTERVAL'
            schedule_info['schedule_config']['interval_seconds'] = plist_data['StartInterval']

        elif 'StartCalendarInterval' in plist_data:
            schedule_info['service_type'] = 'CALENDAR'
            calendar_config = plist_data['StartCalendarInterval']
            # Handle both single dict and list of dicts
            if isinstance(calendar_config, list):
                schedule_info['schedule_config']['calendar'] = calendar_config
            else:
                schedule_info['schedule_config']['calendar'] = [calendar_config]

        elif 'WatchPaths' in plist_data:
            schedule_info['service_type'] = 'TRIGGER'
            schedule_info['schedule_config']['watch_paths'] = plist_data['WatchPaths']

        elif plist_data.get('RunAtLoad'):
            schedule_info['service_type'] = 'ONE_SHOT'
            schedule_info['schedule_config']['run_at_load'] = True

        return schedule_info


class LaunchAgentHealthMonitor:
    """Health monitoring for macOS LaunchAgents"""

    def __init__(self, maia_root: Optional[Path] = None):
        self.user_id = os.getuid()
        self.launchagents_dir = Path.home() / "Library" / "LaunchAgents"
        self.maia_root = maia_root or Path.home() / "git" / "maia"
        self.schedule_parser = ServiceScheduleParser()
        self.log_checker = LogFileChecker(self.maia_root)
        self.services = self._discover_maia_services()
        self.schedule_info = self._load_schedule_info()

    def _discover_maia_services(self) -> List[str]:
        """Discover all Maia LaunchAgent services"""
        maia_services = []

        if self.launchagents_dir.exists():
            for plist in self.launchagents_dir.glob("com.maia.*.plist"):
                service_name = plist.stem
                maia_services.append(service_name)

        return sorted(maia_services)

    def _load_schedule_info(self) -> Dict[str, Dict]:
        """Load schedule information for all services"""
        schedule_map = {}

        for service_name in self.services:
            plist_path = self.launchagents_dir / f"{service_name}.plist"
            if plist_path.exists():
                schedule_info = self.schedule_parser.parse_plist(plist_path)
                schedule_map[service_name] = schedule_info

        return schedule_map

    def _calculate_schedule_aware_health(self, service_name: str,
                                         launchctl_data: Dict) -> Dict:
        """Calculate health based on service type and schedule compliance

        Returns dict with:
        - health: HEALTHY, DEGRADED, FAILED, IDLE, UNKNOWN
        - reason: Human-readable explanation
        - service_type: Type of service
        """
        schedule_info = self.schedule_info.get(service_name, {})
        service_type = schedule_info.get('service_type', 'UNKNOWN')
        schedule_config = schedule_info.get('schedule_config', {})

        has_pid = launchctl_data.get('pid') is not None
        last_exit_code = launchctl_data.get('last_exit_status')

        # CONTINUOUS services: must always have PID
        if service_type == 'CONTINUOUS':
            if has_pid:
                return {
                    'health': 'HEALTHY',
                    'reason': 'Running (has PID)',
                    'service_type': service_type
                }
            else:
                return {
                    'health': 'FAILED',
                    'reason': 'Not running (should be continuous)',
                    'service_type': service_type
                }

        # INTERVAL services: check last run against interval
        elif service_type == 'INTERVAL':
            interval_seconds = schedule_config.get('interval_seconds', 0)
            time_since_run = self.log_checker.get_time_since_last_run(service_name)

            if time_since_run is None:
                return {
                    'health': 'UNKNOWN',
                    'reason': 'No log file found',
                    'service_type': service_type
                }

            # Grace periods: 1.5x for healthy, 3x for degraded
            if time_since_run < interval_seconds * 1.5:
                time_ago = f'{int(time_since_run/60)}m' if time_since_run < 3600 else f'{time_since_run/3600:.1f}h'
                interval_str = f'{int(interval_seconds/60)}m' if interval_seconds < 3600 else f'{interval_seconds/3600:.1f}h'
                return {
                    'health': 'HEALTHY',
                    'reason': f'Ran {time_ago} ago (every {interval_str})',
                    'service_type': service_type
                }
            elif time_since_run < interval_seconds * 3:
                return {
                    'health': 'DEGRADED',
                    'reason': f'Missed 1-2 runs ({int(time_since_run/60)}m since last run)',
                    'service_type': service_type
                }
            else:
                return {
                    'health': 'FAILED',
                    'reason': f'Missed 3+ runs ({time_since_run/3600:.1f}h since last run)',
                    'service_type': service_type
                }

        # CALENDAR services: check if ran within grace period of scheduled time
        elif service_type == 'CALENDAR':
            time_since_run = self.log_checker.get_time_since_last_run(service_name)

            if time_since_run is None:
                return {
                    'health': 'UNKNOWN',
                    'reason': 'No log file found',
                    'service_type': service_type
                }

            # Simple heuristic: if ran within last 24h, consider healthy
            # (proper calendar calculation would require parsing StartCalendarInterval)
            if time_since_run < 3600:  # Within 1 hour
                return {
                    'health': 'HEALTHY',
                    'reason': f'Ran {int(time_since_run/60)}m ago (on schedule)',
                    'service_type': service_type
                }
            elif time_since_run < 86400:  # Within 24 hours
                return {
                    'health': 'HEALTHY',
                    'reason': f'Ran {time_since_run/3600:.1f}h ago (daily schedule)',
                    'service_type': service_type
                }
            elif time_since_run < 172800:  # Within 48 hours
                return {
                    'health': 'DEGRADED',
                    'reason': f'Late by {time_since_run/3600:.1f}h',
                    'service_type': service_type
                }
            else:
                return {
                    'health': 'FAILED',
                    'reason': f'Missed scheduled run ({time_since_run/86400:.1f}d ago)',
                    'service_type': service_type
                }

        # TRIGGER / ONE_SHOT: check if ran successfully when triggered
        elif service_type in ['TRIGGER', 'ONE_SHOT']:
            if last_exit_code == 0:
                return {
                    'health': 'IDLE',
                    'reason': 'Last run successful (waiting for trigger)',
                    'service_type': service_type
                }
            elif last_exit_code and last_exit_code != 0:
                return {
                    'health': 'FAILED',
                    'reason': f'Last run failed (exit {last_exit_code})',
                    'service_type': service_type
                }
            else:
                return {
                    'health': 'UNKNOWN',
                    'reason': 'Never triggered/run',
                    'service_type': service_type
                }

        # UNKNOWN service type
        else:
            return {
                'health': 'UNKNOWN',
                'reason': f'Unknown service type: {service_type}',
                'service_type': service_type
            }

    def get_service_status(self, service_name: str) -> Dict:
        """Get detailed status for a specific service"""
        try:
            result = subprocess.run(
                ['launchctl', 'print', f'gui/{self.user_id}/{service_name}'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                return {
                    'name': service_name,
                    'status': 'NOT_LOADED',
                    'health': 'UNKNOWN',
                    'pid': None,
                    'exit_code': None,
                    'error': result.stderr.strip()
                }

            # Parse launchctl output
            output = result.stdout
            status_info = {
                'name': service_name,
                'status': 'LOADED',
                'health': 'UNKNOWN',
                'pid': None,
                'exit_code': None,
                'last_exit_status': None
            }

            # Extract PID
            for line in output.split('\n'):
                if 'pid =' in line:
                    try:
                        pid = int(line.split('=')[1].strip())
                        status_info['pid'] = pid
                        status_info['status'] = 'RUNNING'
                    except:
                        pass

                if 'last exit code =' in line:
                    try:
                        exit_code = int(line.split('=')[1].strip())
                        status_info['last_exit_status'] = exit_code
                    except:
                        pass

                if 'state =' in line:
                    state = line.split('=')[1].strip()
                    if 'running' in state:
                        status_info['status'] = 'RUNNING'
                    elif 'waiting' in state:
                        status_info['status'] = 'WAITING'

            # Calculate schedule-aware health
            health_result = self._calculate_schedule_aware_health(
                service_name, status_info
            )

            # Merge health calculation into status_info
            status_info['health'] = health_result['health']
            status_info['health_reason'] = health_result['reason']
            status_info['service_type'] = health_result['service_type']

            return status_info

        except subprocess.TimeoutExpired:
            return {
                'name': service_name,
                'status': 'TIMEOUT',
                'health': 'UNKNOWN',
                'error': 'launchctl command timeout'
            }
        except Exception as e:
            return {
                'name': service_name,
                'status': 'ERROR',
                'health': 'UNKNOWN',
                'error': str(e)
            }

    def get_all_services_status(self) -> List[Dict]:
        """Get status for all Maia services"""
        statuses = []

        for service in self.services:
            status = self.get_service_status(service)
            statuses.append(status)

        return statuses

    def generate_health_report(self) -> Dict:
        """Generate comprehensive health report with schedule-aware metrics"""
        print("🔍 Monitoring Maia LaunchAgent Services...\n")

        statuses = self.get_all_services_status()

        # Separate services by type
        continuous = [s for s in statuses if s.get('service_type') == 'CONTINUOUS']
        scheduled = [s for s in statuses if s.get('service_type') in ['INTERVAL', 'CALENDAR']]
        other = [s for s in statuses if s.get('service_type') in ['TRIGGER', 'ONE_SHOT', 'UNKNOWN']]

        # Calculate CONTINUOUS service availability (traditional SLI)
        continuous_healthy = len([s for s in continuous if s['health'] == 'HEALTHY'])
        continuous_availability = (continuous_healthy / len(continuous) * 100) if continuous else 0

        # Calculate SCHEDULED service health (on-schedule percentage)
        scheduled_healthy = len([s for s in scheduled if s['health'] == 'HEALTHY'])
        scheduled_degraded = len([s for s in scheduled if s['health'] == 'DEGRADED'])
        scheduled_failed = len([s for s in scheduled if s['health'] == 'FAILED'])
        scheduled_health = (scheduled_healthy / len(scheduled) * 100) if scheduled else 0

        # Overall statistics
        total = len(statuses)
        running = len([s for s in statuses if s['health'] == 'HEALTHY'])
        failed = len([s for s in statuses if s['health'] == 'FAILED'])
        degraded = len([s for s in statuses if s['health'] == 'DEGRADED'])
        idle = len([s for s in statuses if s['health'] == 'IDLE'])
        unknown = len([s for s in statuses if s['health'] == 'UNKNOWN'])

        # Calculate availability percentage (legacy metric for backwards compat)
        availability = (running / total * 100) if total > 0 else 0

        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_services': total,
                'running': running,
                'failed': failed,
                'degraded': degraded,
                'idle': idle,
                'unknown': unknown,
                'availability_percentage': round(availability, 1),
                'health_status': self._calculate_overall_health(
                    continuous_availability, scheduled_health, failed, degraded
                ),
                # Schedule-aware metrics
                'continuous_services': {
                    'total': len(continuous),
                    'healthy': continuous_healthy,
                    'availability_pct': round(continuous_availability, 1),
                    'slo_target': 99.9,
                    'slo_met': continuous_availability >= 99.9
                },
                'scheduled_services': {
                    'total': len(scheduled),
                    'healthy': scheduled_healthy,
                    'degraded': scheduled_degraded,
                    'failed': scheduled_failed,
                    'health_pct': round(scheduled_health, 1),
                    'slo_target': 95.0,
                    'slo_met': scheduled_health >= 95.0
                },
                'other_services': {
                    'total': len(other)
                }
            },
            'services': statuses
        }

        return report

    def _calculate_overall_health(self, continuous_availability: float,
                                   scheduled_health: float,
                                   failed: int, degraded: int) -> str:
        """Calculate overall system health status (schedule-aware)"""
        # CRITICAL: Any failed services or both SLOs missed
        if failed > 0:
            if continuous_availability < 99.9 and scheduled_health < 95.0:
                return 'CRITICAL'
            else:
                return 'DEGRADED'

        # DEGRADED: Any degraded services or one SLO missed
        if degraded > 0:
            return 'DEGRADED'

        if continuous_availability < 99.9 or scheduled_health < 95.0:
            return 'DEGRADED'

        # HEALTHY: All services healthy and SLOs met
        return 'HEALTHY'

    def print_dashboard(self, report: Dict, failed_only: bool = False):
        """Print service health dashboard"""
        print("="*70)
        print("🏥 MAIA LAUNCHAGENT HEALTH DASHBOARD")
        print("="*70)

        summary = report['summary']

        # Overall health status
        health_status = summary['health_status']
        if health_status == 'HEALTHY':
            status_icon = "✅"
        elif health_status == 'WARNING':
            status_icon = "⚠️"
        elif health_status == 'DEGRADED':
            status_icon = "🔴"
        else:
            status_icon = "🚨"

        print(f"\n{status_icon} Overall Health: {health_status}\n")

        # Schedule-aware metrics
        continuous = summary['continuous_services']
        scheduled = summary['scheduled_services']

        print(f"📊 Schedule-Aware SLI/SLO Metrics:")
        print(f"\n   🔄 Continuous Services (KeepAlive): {continuous['healthy']}/{continuous['total']}")
        print(f"      Availability: {continuous['availability_pct']}%")
        cont_slo = "✅ MEETING SLO" if continuous['slo_met'] else f"🔴 BELOW SLO (target {continuous['slo_target']}%)"
        print(f"      SLO Status: {cont_slo}")

        print(f"\n   ⏰ Scheduled Services (Interval/Calendar): {scheduled['healthy']}/{scheduled['total']}")
        print(f"      On-Schedule: {scheduled['health_pct']}%")
        if scheduled['degraded'] > 0:
            print(f"      Degraded: {scheduled['degraded']} (late but running)")
        if scheduled['failed'] > 0:
            print(f"      Failed: {scheduled['failed']} (missed runs)")
        sched_slo = "✅ MEETING SLO" if scheduled['slo_met'] else f"🔴 BELOW SLO (target {scheduled['slo_target']}%)"
        print(f"      SLO Status: {sched_slo}")

        print(f"\n📈 Overall Summary:")
        print(f"   Total Services: {summary['total_services']}")
        print(f"   Healthy: {summary['running']} ✅")
        if summary.get('degraded', 0) > 0:
            print(f"   Degraded: {summary['degraded']} ⚠️")
        print(f"   Failed: {summary['failed']} 🔴")
        print(f"   Unknown: {summary['unknown']} ❓")

        # Service details
        services = report['services']
        if failed_only:
            services = [s for s in services if s['health'] in ['FAILED', 'UNKNOWN']]

        if services:
            print(f"\n📋 Service Status:")
            print(f"   {'Service Name':<50} {'Type':<12} {'Health':<12} {'Details'}")
            print(f"   {'-'*50} {'-'*12} {'-'*12} {'-'*40}")

            for service in services:
                name = service['name'].replace('com.maia.', '')
                service_type = service.get('service_type', 'UNKNOWN')[:10]
                health = service['health']
                health_reason = service.get('health_reason', 'No details')

                # Health icon
                if health == 'HEALTHY':
                    health_icon = "✅"
                elif health == 'FAILED':
                    health_icon = "🔴"
                elif health == 'DEGRADED':
                    health_icon = "⚠️"
                elif health == 'IDLE':
                    health_icon = "💤"
                else:
                    health_icon = "❓"

                health_display = f"{health_icon} {health}"

                print(f"   {name:<50} {service_type:<12} {health_display:<20} {health_reason}")

        print("\n" + "="*70)

        if summary['failed'] > 0 or summary.get('degraded', 0) > 0:
            print(f"\n🚨 ACTION REQUIRED:")
            if summary['failed'] > 0:
                print(f"   ❌ {summary['failed']} service(s) FAILED (not running or missed 3+ runs)")
            if summary.get('degraded', 0) > 0:
                print(f"   ⚠️  {summary['degraded']} service(s) DEGRADED (late but running)")
            print(f"\n   Check logs: ~/.maia/logs/")
            print(f"   Check status: launchctl list | grep maia")

        print("="*70 + "\n")

    def get_service_logs(self, service_name: str, lines: int = 50) -> str:
        """Get recent logs for a service"""
        log_path = Path.home() / "git" / "maia" / "claude" / "data" / "logs" / f"{service_name}.log"

        if log_path.exists():
            try:
                result = subprocess.run(
                    ['tail', '-n', str(lines), str(log_path)],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                return result.stdout
            except:
                return f"Could not read log file: {log_path}"
        else:
            return f"Log file not found: {log_path}"


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="LaunchAgent Health Monitor - SRE Service Dashboard"
    )
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show service status'
    )
    parser.add_argument(
        '--dashboard',
        action='store_true',
        help='Show health dashboard'
    )
    parser.add_argument(
        '--failed-only',
        action='store_true',
        help='Show only failed services'
    )
    parser.add_argument(
        '--json',
        type=str,
        help='Save report as JSON to specified file'
    )
    parser.add_argument(
        '--logs',
        type=str,
        help='Get logs for specific service'
    )

    args = parser.parse_args()

    if not (args.status or args.dashboard or args.logs):
        parser.print_help()
        return 1

    monitor = LaunchAgentHealthMonitor()

    if args.logs:
        logs = monitor.get_service_logs(args.logs)
        print(logs)
        return 0

    report = monitor.generate_health_report()

    if args.dashboard or args.status:
        monitor.print_dashboard(report, failed_only=args.failed_only)

    if args.json:
        json_path = Path(args.json)
        json_path.write_text(json.dumps(report, indent=2))
        print(f"📄 Report saved to: {json_path}")

    # Exit code based on health
    if report['summary']['health_status'] in ['CRITICAL', 'DEGRADED']:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
