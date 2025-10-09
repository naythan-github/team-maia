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
from pathlib import Path
from typing import Dict, List
from datetime import datetime

class LaunchAgentHealthMonitor:
    """Health monitoring for macOS LaunchAgents"""

    def __init__(self):
        self.user_id = os.getuid()
        self.launchagents_dir = Path.home() / "Library" / "LaunchAgents"
        self.services = self._discover_maia_services()

    def _discover_maia_services(self) -> List[str]:
        """Discover all Maia LaunchAgent services"""
        maia_services = []

        if self.launchagents_dir.exists():
            for plist in self.launchagents_dir.glob("com.maia.*.plist"):
                service_name = plist.stem
                maia_services.append(service_name)

        return sorted(maia_services)

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

            # Determine health
            if status_info['pid']:
                status_info['health'] = 'HEALTHY'
            elif status_info['last_exit_status'] == 0:
                status_info['health'] = 'IDLE'
            elif status_info['last_exit_status'] and status_info['last_exit_status'] != 0:
                status_info['health'] = 'FAILED'
            else:
                status_info['health'] = 'UNKNOWN'

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
        """Generate comprehensive health report"""
        print("🔍 Monitoring Maia LaunchAgent Services...\n")

        statuses = self.get_all_services_status()

        # Calculate statistics
        total = len(statuses)
        running = len([s for s in statuses if s['health'] == 'HEALTHY'])
        failed = len([s for s in statuses if s['health'] == 'FAILED'])
        idle = len([s for s in statuses if s['health'] == 'IDLE'])
        unknown = len([s for s in statuses if s['health'] == 'UNKNOWN'])

        # Calculate availability percentage
        availability = (running / total * 100) if total > 0 else 0

        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_services': total,
                'running': running,
                'failed': failed,
                'idle': idle,
                'unknown': unknown,
                'availability_percentage': round(availability, 1),
                'health_status': self._calculate_overall_health(availability, failed)
            },
            'services': statuses
        }

        return report

    def _calculate_overall_health(self, availability: float, failed: int) -> str:
        """Calculate overall system health status"""
        if failed > 0:
            return 'DEGRADED'
        elif availability >= 75:
            return 'HEALTHY'
        elif availability >= 50:
            return 'WARNING'
        else:
            return 'CRITICAL'

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

        print(f"\n{status_icon} Overall Health: {health_status}")
        print(f"📊 Service Availability: {summary['availability_percentage']}%\n")

        print(f"📈 Summary:")
        print(f"   Total Services: {summary['total_services']}")
        print(f"   Running: {summary['running']} ✅")
        print(f"   Failed: {summary['failed']} 🔴")
        print(f"   Idle: {summary['idle']} 💤")
        print(f"   Unknown: {summary['unknown']} ❓")

        # Service details
        services = report['services']
        if failed_only:
            services = [s for s in services if s['health'] in ['FAILED', 'UNKNOWN']]

        if services:
            print(f"\n📋 Service Status:")
            print(f"   {'Service Name':<45} {'Status':<12} {'Health':<10} {'PID'}")
            print(f"   {'-'*45} {'-'*12} {'-'*10} {'-'*10}")

            for service in services:
                name = service['name']
                status = service['status']
                health = service['health']
                pid = service.get('pid', '-')

                # Health icon
                if health == 'HEALTHY':
                    health_icon = "✅"
                elif health == 'FAILED':
                    health_icon = "🔴"
                elif health == 'IDLE':
                    health_icon = "💤"
                else:
                    health_icon = "❓"

                pid_str = str(pid) if pid else '-'

                print(f"   {name:<45} {status:<12} {health_icon} {health:<8} {pid_str}")

        print("\n" + "="*70)

        # SLI/SLO Assessment
        print("\n📊 SRE Metrics:")
        availability = summary['availability_percentage']

        if availability >= 99.9:
            slo_status = "✅ Exceeding SLO (99.9%)"
        elif availability >= 99.0:
            slo_status = "✅ Meeting SLO (99.0%)"
        elif availability >= 95.0:
            slo_status = "⚠️  Below SLO, approaching error budget"
        else:
            slo_status = "🚨 Error budget exceeded"

        print(f"   SLI (Service Level Indicator): {availability}% availability")
        print(f"   SLO (Service Level Objective): {slo_status}")

        if summary['failed'] > 0:
            print(f"\n🚨 INCIDENT RESPONSE REQUIRED:")
            print(f"   {summary['failed']} service(s) failed")
            print(f"   Check logs in ~/git/maia/claude/data/logs/")
            print(f"   Run: launchctl list | grep maia")

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
