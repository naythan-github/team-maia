#!/usr/bin/env python3
"""
Backup Health Monitoring System
================================

Monitors backup health and sends alerts for:
- Backup age (no backup in X hours)
- Storage capacity issues
- Backup integrity failures
- Missing backup files

Usage:
    python3 backup_health_monitor.py status    # Show status report
    python3 backup_health_monitor.py check     # Run health check
"""

import sys
import os
import json
import shutil
from pathlib import Path
from datetime import datetime, timedelta

class BackupHealthMonitor:
    def __init__(self):
        # Determine Maia root
        if Path.cwd().name == 'maia':
            self.maia_root = Path.cwd()
        else:
            self.maia_root = Path(__file__).resolve().parents[3]

        # Backup locations
        self.production_backup_dir = Path.home() / "Library" / "Mobile Documents" / "com~apple~CloudDocs" / "maia" / "backups" / "production"
        self.system_backup_dir = self.maia_root / "claude" / "data" / "backups"

        # Configuration
        self.max_backup_age_hours = 48
        self.min_storage_gb = 10
        self.alert_log = self.maia_root / "claude" / "logs" / "backup_health.log"
        self.alert_log.parent.mkdir(parents=True, exist_ok=True)

    def check_backup_health(self) -> dict:
        """Comprehensive backup health check"""
        health_report = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'HEALTHY',
            'checks': {},
            'issues': [],
            'warnings': []
        }

        # Check 1: Backup age
        backup_age_check = self._check_backup_age()
        health_report['checks']['backup_age'] = backup_age_check
        if not backup_age_check['passed']:
            health_report['issues'].append(backup_age_check)
            health_report['overall_status'] = 'CRITICAL'

        # Check 2: Storage capacity
        storage_check = self._check_storage_capacity()
        health_report['checks']['storage_capacity'] = storage_check
        if not storage_check['passed']:
            if storage_check['severity'] == 'CRITICAL':
                health_report['issues'].append(storage_check)
                health_report['overall_status'] = 'CRITICAL'
            else:
                health_report['warnings'].append(storage_check)
                if health_report['overall_status'] == 'HEALTHY':
                    health_report['overall_status'] = 'WARNING'

        # Check 3: Backup integrity
        integrity_check = self._check_backup_integrity()
        health_report['checks']['backup_integrity'] = integrity_check
        if not integrity_check['passed']:
            health_report['issues'].append(integrity_check)
            health_report['overall_status'] = 'CRITICAL'

        # Check 4: Backup location accessibility
        location_check = self._check_backup_locations()
        health_report['checks']['backup_locations'] = location_check
        if not location_check['passed']:
            health_report['warnings'].append(location_check)
            if health_report['overall_status'] == 'HEALTHY':
                health_report['overall_status'] = 'WARNING'

        # Check 5: Automation status
        automation_check = self._check_automation_status()
        health_report['checks']['automation'] = automation_check
        if not automation_check['passed']:
            health_report['warnings'].append(automation_check)
            if health_report['overall_status'] == 'HEALTHY':
                health_report['overall_status'] = 'WARNING'

        # Log results
        self._log_health_check(health_report)

        # Send alerts if needed
        if health_report['overall_status'] != 'HEALTHY':
            self._send_alert(health_report)

        return health_report

    def _check_backup_age(self) -> dict:
        """Check if backups are recent enough"""
        try:
            # Find all backup directories and archives
            backups = []

            if self.production_backup_dir.exists():
                for item in self.production_backup_dir.iterdir():
                    if item.name.startswith("maia_backup_"):
                        if item.is_dir():
                            # Check for manifest
                            manifest_file = item / "backup_manifest.json"
                            if manifest_file.exists():
                                with open(manifest_file, 'r') as f:
                                    manifest = json.load(f)
                                backups.append({
                                    'name': item.name,
                                    'created_at': manifest['created_at'],
                                    'path': str(item)
                                })
                        elif item.suffix == '.gz':
                            # Archive file
                            backups.append({
                                'name': item.name,
                                'created_at': datetime.fromtimestamp(item.stat().st_mtime).isoformat(),
                                'path': str(item)
                            })

            if not backups:
                return {
                    'check': 'backup_age',
                    'passed': False,
                    'severity': 'CRITICAL',
                    'message': 'No backups found',
                    'details': f'No production backups in {self.production_backup_dir}'
                }

            # Sort by creation date
            backups.sort(key=lambda x: x['created_at'], reverse=True)
            latest_backup = backups[0]

            backup_time = datetime.fromisoformat(latest_backup['created_at'])
            age_hours = (datetime.now() - backup_time).total_seconds() / 3600

            if age_hours > self.max_backup_age_hours:
                return {
                    'check': 'backup_age',
                    'passed': False,
                    'severity': 'CRITICAL',
                    'message': f'No backup in {age_hours:.1f} hours',
                    'details': f'Latest: {latest_backup["name"]} at {backup_time.strftime("%Y-%m-%d %H:%M")}',
                    'threshold': f'{self.max_backup_age_hours} hours',
                    'actual': f'{age_hours:.1f} hours'
                }

            return {
                'check': 'backup_age',
                'passed': True,
                'message': f'Latest backup is {age_hours:.1f} hours old',
                'details': f'Backup: {latest_backup["name"]}',
                'threshold': f'{self.max_backup_age_hours} hours',
                'actual': f'{age_hours:.1f} hours'
            }

        except Exception as e:
            return {
                'check': 'backup_age',
                'passed': False,
                'severity': 'CRITICAL',
                'message': 'Failed to check backup age',
                'details': str(e)
            }

    def _check_storage_capacity(self) -> dict:
        """Check if backup storage has sufficient capacity"""
        try:
            # Check iCloud backup storage
            stat = shutil.disk_usage(self.production_backup_dir)
            free_gb = stat.free / (1024 ** 3)
            total_gb = stat.total / (1024 ** 3)
            used_gb = stat.used / (1024 ** 3)
            used_percent = (used_gb / total_gb) * 100

            if free_gb < self.min_storage_gb:
                severity = 'CRITICAL' if free_gb < 5 else 'WARNING'
                return {
                    'check': 'storage_capacity',
                    'passed': False,
                    'severity': severity,
                    'message': f'Low storage: {free_gb:.1f}GB free',
                    'details': f'{used_gb:.1f}GB used of {total_gb:.1f}GB ({used_percent:.1f}%)',
                    'threshold': f'{self.min_storage_gb}GB',
                    'actual': f'{free_gb:.1f}GB'
                }

            return {
                'check': 'storage_capacity',
                'passed': True,
                'message': f'Storage healthy: {free_gb:.1f}GB free',
                'details': f'{used_gb:.1f}GB used of {total_gb:.1f}GB ({used_percent:.1f}%)',
                'threshold': f'{self.min_storage_gb}GB',
                'actual': f'{free_gb:.1f}GB'
            }

        except Exception as e:
            return {
                'check': 'storage_capacity',
                'passed': False,
                'severity': 'WARNING',
                'message': 'Failed to check storage capacity',
                'details': str(e)
            }

    def _check_backup_integrity(self) -> dict:
        """Check integrity of latest backup"""
        try:
            # Find latest backup with manifest
            if not self.production_backup_dir.exists():
                return {
                    'check': 'backup_integrity',
                    'passed': False,
                    'severity': 'CRITICAL',
                    'message': 'Backup directory not found',
                    'details': str(self.production_backup_dir)
                }

            backups_with_manifest = []
            for item in self.production_backup_dir.iterdir():
                if item.is_dir() and item.name.startswith("maia_backup_"):
                    manifest_file = item / "backup_manifest.json"
                    if manifest_file.exists():
                        backups_with_manifest.append(item)

            if not backups_with_manifest:
                return {
                    'check': 'backup_integrity',
                    'passed': False,
                    'severity': 'WARNING',
                    'message': 'No backups with manifests found',
                    'details': 'Unable to verify backup integrity without manifest'
                }

            # Sort by modification time
            backups_with_manifest.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            latest_backup = backups_with_manifest[0]

            manifest_file = latest_backup / "backup_manifest.json"
            with open(manifest_file, 'r') as f:
                manifest = json.load(f)

            # Check required fields
            required_fields = ['backup_name', 'created_at', 'databases_backed_up']
            missing_fields = [f for f in required_fields if f not in manifest]

            if missing_fields:
                return {
                    'check': 'backup_integrity',
                    'passed': False,
                    'severity': 'CRITICAL',
                    'message': 'Backup manifest incomplete',
                    'details': f'Missing: {", ".join(missing_fields)}',
                    'backup': latest_backup.name
                }

            # Check if archive exists
            archive_path = latest_backup.parent / f"{latest_backup.name}.tar.gz"
            archive_exists = archive_path.exists()

            return {
                'check': 'backup_integrity',
                'passed': True,
                'message': 'Latest backup integrity verified',
                'details': f'{latest_backup.name}, {len(manifest["databases_backed_up"])} databases' + (', archive exists' if archive_exists else ''),
                'backup': latest_backup.name
            }

        except Exception as e:
            return {
                'check': 'backup_integrity',
                'passed': False,
                'severity': 'CRITICAL',
                'message': 'Integrity check failed',
                'details': str(e)
            }

    def _check_backup_locations(self) -> dict:
        """Check if backup locations are accessible"""
        try:
            locations = {
                'production_icloud': self.production_backup_dir,
                'system_local': self.system_backup_dir
            }

            inaccessible = []
            accessible = []

            for name, location in locations.items():
                if location.exists() and os.access(location, os.W_OK):
                    accessible.append(f'{name}: {location}')
                else:
                    inaccessible.append(f'{name}: {location}')

            if inaccessible:
                return {
                    'check': 'backup_locations',
                    'passed': False,
                    'severity': 'WARNING',
                    'message': f'{len(inaccessible)} location(s) inaccessible',
                    'details': 'Inaccessible: ' + ', '.join(inaccessible),
                    'accessible': accessible
                }

            return {
                'check': 'backup_locations',
                'passed': True,
                'message': 'All backup locations accessible',
                'details': f'{len(accessible)} locations verified'
            }

        except Exception as e:
            return {
                'check': 'backup_locations',
                'passed': False,
                'severity': 'WARNING',
                'message': 'Failed to check backup locations',
                'details': str(e)
            }

    def _check_automation_status(self) -> dict:
        """Check if automated backup script exists and is executable"""
        try:
            script_path = self.maia_root / "claude" / "tools" / "scripts" / "automated_backup.sh"

            if not script_path.exists():
                return {
                    'check': 'automation',
                    'passed': False,
                    'severity': 'WARNING',
                    'message': 'Automated backup script missing',
                    'details': f'Expected: {script_path}'
                }

            if not os.access(script_path, os.X_OK):
                return {
                    'check': 'automation',
                    'passed': False,
                    'severity': 'WARNING',
                    'message': 'Script not executable',
                    'details': f'Run: chmod +x {script_path}'
                }

            return {
                'check': 'automation',
                'passed': True,
                'message': 'Automation script ready',
                'details': str(script_path)
            }

        except Exception as e:
            return {
                'check': 'automation',
                'passed': False,
                'severity': 'WARNING',
                'message': 'Failed to check automation',
                'details': str(e)
            }

    def _log_health_check(self, health_report: dict):
        """Log health check results"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        with open(self.alert_log, 'a') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"Backup Health Check: {timestamp}\n")
            f.write(f"Overall Status: {health_report['overall_status']}\n")
            f.write(f"{'='*60}\n")

            for check_name, check_result in health_report['checks'].items():
                status = '✅ PASS' if check_result['passed'] else '❌ FAIL'
                f.write(f"{status} {check_name}: {check_result['message']}\n")
                if check_result.get('details'):
                    f.write(f"    {check_result['details']}\n")

            if health_report['issues']:
                f.write(f"\n⚠️  ISSUES ({len(health_report['issues'])}):\n")
                for issue in health_report['issues']:
                    f.write(f"   - {issue['message']}\n")

            if health_report['warnings']:
                f.write(f"\n⚠️  WARNINGS ({len(health_report['warnings'])}):\n")
                for warning in health_report['warnings']:
                    f.write(f"   - {warning['message']}\n")

    def _send_alert(self, health_report: dict):
        """Send alert notification"""
        print("\n🚨 BACKUP HEALTH ALERT")
        print(f"Status: {health_report['overall_status']}")

        if health_report['issues']:
            print(f"\nIssues ({len(health_report['issues'])}):")
            for issue in health_report['issues']:
                print(f"  ❌ {issue['message']}")
                if issue.get('details'):
                    print(f"     {issue['details']}")

        if health_report['warnings']:
            print(f"\nWarnings ({len(health_report['warnings'])}):")
            for warning in health_report['warnings']:
                print(f"  ⚠️  {warning['message']}")

    def generate_status_report(self) -> str:
        """Generate human-readable status report"""
        health_report = self.check_backup_health()

        status_emoji = {'HEALTHY': '✅', 'WARNING': '⚠️', 'CRITICAL': '❌'}

        report = []
        report.append("\n" + "="*60)
        report.append("BACKUP HEALTH STATUS REPORT")
        report.append("="*60)
        report.append(f"{status_emoji.get(health_report['overall_status'], '❓')} Overall Status: {health_report['overall_status']}")
        report.append(f"Timestamp: {health_report['timestamp'][:19]}")
        report.append("")

        report.append("Check Results:")
        report.append("-" * 60)
        for check_name, check_result in health_report['checks'].items():
            status = '✅' if check_result['passed'] else '❌'
            report.append(f"{status} {check_name.replace('_', ' ').title()}")
            report.append(f"   {check_result['message']}")
            if check_result.get('details'):
                report.append(f"   {check_result['details']}")
            report.append("")

        if health_report['issues']:
            report.append("Critical Issues:")
            report.append("-" * 60)
            for issue in health_report['issues']:
                report.append(f"❌ {issue['message']}")
                if issue.get('details'):
                    report.append(f"   {issue['details']}")
                report.append("")

        if health_report['warnings']:
            report.append("Warnings:")
            report.append("-" * 60)
            for warning in health_report['warnings']:
                report.append(f"⚠️  {warning['message']}")
                if warning.get('details'):
                    report.append(f"   {warning['details']}")
                report.append("")

        report.append("="*60)

        return "\n".join(report)


def main():
    monitor = BackupHealthMonitor()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "check":
            report = monitor.check_backup_health()
            print(f"\n✅ Health check complete")
            print(f"Status: {report['overall_status']}")
            print(f"Issues: {len(report['issues'])}")
            print(f"Warnings: {len(report['warnings'])}")

        elif command == "status":
            print(monitor.generate_status_report())

        else:
            print("Usage: python3 backup_health_monitor.py [check|status]")
    else:
        # Default: status
        print(monitor.generate_status_report())


if __name__ == "__main__":
    main()