#!/usr/bin/env python3
"""
Automation Health Monitor
Monitors all Maia automations and alerts on failures

Author: Maia Personal Assistant Agent
Phase: 88 - Personal Assistant Automation Expansion
Date: 2025-10-03
"""

import sys
from pathlib import Path
import json
from datetime import datetime, timedelta
import subprocess
from typing import Dict, List

MAIA_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))


class AutomationHealthMonitor:
    """Monitor automation health and detect failures"""

    def __init__(self):
        """Initialize health monitor"""
        self.status_file = Path.home() / ".maia" / "automation_health.json"
        self.log_dir = Path.home() / ".maia" / "logs"

        # Critical automations to monitor
        self.automations = {
            "com.maia.daily-briefing": {
                "name": "Daily Briefing",
                "frequency": "daily",
                "expected_time": "07:00",
                "log_file": self.log_dir / "daily_briefing.log",
                "error_log": self.log_dir / "daily_briefing_error.log",
                "critical": True
            },
            "com.maia.confluence-sync": {
                "name": "Confluence Sync",
                "frequency": "daily",
                "expected_time": "08:00",
                "log_file": self.log_dir / "confluence_sync.log",
                "error_log": self.log_dir / "confluence_sync_error.log",
                "critical": True
            },
            "com.maia.trello-status-tracker": {
                "name": "Trello Status Tracker",
                "frequency": "4-hourly",
                "expected_time": None,
                "log_file": self.log_dir / "trello_status_tracker.log",
                "error_log": self.log_dir / "trello_status_tracker_error.log",
                "critical": True
            },
            "com.maia.email-rag-indexer": {
                "name": "Email RAG Indexer",
                "frequency": "hourly",
                "expected_time": None,
                "log_file": self.log_dir / "email_rag_indexer.log",
                "error_log": self.log_dir / "email_rag_indexer_error.log",
                "critical": True
            },
            "com.maia.vtt-watcher": {
                "name": "VTT Watcher",
                "frequency": "continuous",
                "expected_time": None,
                "log_file": MAIA_ROOT / "claude" / "data" / "logs" / "vtt_watcher.log",
                "error_log": MAIA_ROOT / "claude" / "data" / "logs" / "vtt_watcher_error.log",
                "critical": True
            }
        }

    def check_launchagent_loaded(self, label: str) -> Dict:
        """Check if LaunchAgent is loaded"""
        try:
            result = subprocess.run(
                ['launchctl', 'list'],
                capture_output=True,
                text=True
            )
            loaded = label in result.stdout

            if loaded:
                # Get status
                list_result = subprocess.run(
                    ['launchctl', 'list', label],
                    capture_output=True,
                    text=True
                )
                return {
                    "loaded": True,
                    "status": "running" if list_result.returncode == 0 else "error",
                    "output": list_result.stdout
                }
            else:
                return {"loaded": False, "status": "not_loaded"}
        except Exception as e:
            return {"loaded": False, "status": "check_failed", "error": str(e)}

    def check_log_for_errors(self, log_file: Path, hours: int = 24) -> Dict:
        """Check log file for recent errors"""
        if not log_file.exists():
            return {
                "has_errors": False,  # Not an error if automation hasn't run yet
                "error": "Log file doesn't exist (automation not run yet)",
                "last_run": None,
                "first_run_pending": True
            }

        try:
            # Get file modification time
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            age_hours = (datetime.now() - mtime).total_seconds() / 3600

            # Read last 100 lines
            with open(log_file) as f:
                lines = f.readlines()[-100:]

            content = ''.join(lines)
            # Check for actual errors (not just the word "error" in success messages)
            error_lines = [line for line in lines if any(word in line.lower() for word in ['error', 'exception', 'failed', 'traceback'])]
            # Filter out false positives
            actual_errors = [line for line in error_lines if not any(fp in line.lower() for fp in ['✅', 'operational', 'no error'])]
            has_errors = len(actual_errors) > 0

            return {
                "has_errors": has_errors,
                "last_run": mtime.isoformat(),
                "age_hours": age_hours,
                "recent_errors": [line.strip() for line in actual_errors][-5:]
            }
        except Exception as e:
            return {
                "has_errors": True,
                "error": f"Failed to read log: {e}",
                "last_run": None
            }

    def check_data_freshness(self) -> Dict:
        """Check if critical data files are being updated"""
        data_files = {
            "vtt_intelligence": MAIA_ROOT / "claude" / "data" / "vtt_intelligence.json",
            "confluence_intelligence": MAIA_ROOT / "claude" / "data" / "confluence_intelligence.json",
            "daily_briefing": MAIA_ROOT / "claude" / "data" / "enhanced_daily_briefing.json",
            "email_rag_collection": Path.home() / ".maia" / "email_rag_ollama" / "chroma.sqlite3"
        }

        freshness = {}
        for name, path in data_files.items():
            if not path.exists():
                freshness[name] = {
                    "exists": False,
                    "stale": True,
                    "age_hours": None
                }
            else:
                mtime = datetime.fromtimestamp(path.stat().st_mtime)
                age_hours = (datetime.now() - mtime).total_seconds() / 3600

                # Stale thresholds
                threshold = {
                    "daily_briefing": 28,  # Should run daily
                    "confluence_intelligence": 28,  # Should update daily if changed
                    "vtt_intelligence": 72,  # Should update when meetings happen
                    "email_rag_collection": 2  # Should update hourly
                }.get(name, 48)

                freshness[name] = {
                    "exists": True,
                    "last_updated": mtime.isoformat(),
                    "age_hours": age_hours,
                    "stale": age_hours > threshold
                }

        return freshness

    def run_health_check(self) -> Dict:
        """Run complete health check"""
        print("🔍 Running Automation Health Check...\n")

        results = {
            "checked_at": datetime.now().isoformat(),
            "overall_status": "healthy",
            "automations": {},
            "data_freshness": {},
            "alerts": []
        }

        # Check each automation
        for label, config in self.automations.items():
            print(f"Checking {config['name']}...")

            agent_status = self.check_launchagent_loaded(label)
            log_status = self.check_log_for_errors(config['log_file'])
            error_log_status = self.check_log_for_errors(config['error_log'])

            automation_health = {
                "name": config['name'],
                "loaded": agent_status['loaded'],
                "status": agent_status['status'],
                "log_health": log_status,
                "error_log_health": error_log_status,
                "critical": config['critical']
            }

            # Generate alerts
            if not agent_status['loaded']:
                results['alerts'].append({
                    "severity": "CRITICAL" if config['critical'] else "WARNING",
                    "automation": config['name'],
                    "issue": "LaunchAgent not loaded",
                    "action": f"Run: launchctl load ~/Library/LaunchAgents/{label}.plist"
                })
                results['overall_status'] = "critical"

            if log_status.get('has_errors'):
                results['alerts'].append({
                    "severity": "ERROR",
                    "automation": config['name'],
                    "issue": "Errors detected in log file",
                    "details": log_status.get('recent_errors', [])[:2],
                    "action": f"Check: tail -50 {config['log_file']}"
                })
                if config['critical']:
                    results['overall_status'] = "degraded"

            # Check staleness for scheduled jobs
            if config['frequency'] == 'daily' and log_status.get('age_hours', 0) > 28:
                results['alerts'].append({
                    "severity": "WARNING",
                    "automation": config['name'],
                    "issue": f"Last run {log_status.get('age_hours', 0):.1f} hours ago (expected daily)",
                    "action": f"Manually run automation or check LaunchAgent schedule"
                })

            results['automations'][label] = automation_health

        # Check data freshness
        print("\nChecking data freshness...")
        results['data_freshness'] = self.check_data_freshness()

        for name, status in results['data_freshness'].items():
            if status.get('stale'):
                results['alerts'].append({
                    "severity": "WARNING",
                    "data_file": name,
                    "issue": f"Data file stale ({status.get('age_hours', 0):.1f} hours old)",
                    "action": "Check corresponding automation"
                })
                if results['overall_status'] == 'healthy':
                    results['overall_status'] = 'degraded'

        # Save status
        self.status_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.status_file, 'w') as f:
            json.dump(results, f, indent=2)

        return results

    def format_report(self, results: Dict) -> str:
        """Format health check report"""
        output = []

        status_emoji = {
            "healthy": "✅",
            "degraded": "⚠️",
            "critical": "🔴"
        }

        output.append("\n" + "="*70)
        output.append(f"{status_emoji.get(results['overall_status'], '❓')} AUTOMATION HEALTH STATUS: {results['overall_status'].upper()}")
        output.append("="*70)
        output.append(f"Checked: {results['checked_at']}")

        # Alerts section
        if results['alerts']:
            output.append(f"\n🚨 ALERTS ({len(results['alerts'])})")
            output.append("-"*70)
            for alert in results['alerts']:
                severity = alert['severity']
                emoji = {"CRITICAL": "🔴", "ERROR": "❌", "WARNING": "⚠️"}.get(severity, "ℹ️")
                output.append(f"\n{emoji} [{severity}] {alert.get('automation', alert.get('data_file', 'System'))}")
                output.append(f"   Issue: {alert['issue']}")
                if 'details' in alert and alert['details']:
                    output.append(f"   Details: {alert['details'][0][:100]}")
                output.append(f"   Action: {alert['action']}")
        else:
            output.append("\n✅ NO ALERTS - All systems operational")

        # Automation status
        output.append(f"\n📊 AUTOMATION STATUS")
        output.append("-"*70)
        for label, auto in results['automations'].items():
            status_icon = "✅" if auto['loaded'] and not auto['log_health'].get('has_errors') else "❌"
            output.append(f"{status_icon} {auto['name']}")
            output.append(f"   Loaded: {'Yes' if auto['loaded'] else 'NO'}")
            if auto['log_health'].get('last_run'):
                output.append(f"   Last Run: {auto['log_health']['last_run']} ({auto['log_health'].get('age_hours', 0):.1f}h ago)")
            output.append(f"   Errors: {'Yes - CHECK LOGS' if auto['log_health'].get('has_errors') else 'None'}")

        # Data freshness
        output.append(f"\n📁 DATA FRESHNESS")
        output.append("-"*70)
        for name, status in results['data_freshness'].items():
            if status['exists']:
                status_icon = "✅" if not status['stale'] else "⚠️"
                output.append(f"{status_icon} {name}: {status['age_hours']:.1f}h old {'(STALE)' if status['stale'] else ''}")
            else:
                output.append(f"❌ {name}: MISSING")

        output.append("\n" + "="*70)
        output.append(f"💾 Full status saved to: {self.status_file}")
        output.append("="*70 + "\n")

        return '\n'.join(output)


def main():
    """CLI entry"""
    import argparse
    parser = argparse.ArgumentParser(description="Monitor automation health")
    parser.add_argument('--quiet', action='store_true', help='Only show if there are issues')
    parser.add_argument('--json', action='store_true', help='Output JSON format')
    args = parser.parse_args()

    monitor = AutomationHealthMonitor()
    results = monitor.run_health_check()

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        report = monitor.format_report(results)

        if args.quiet:
            if results['overall_status'] != 'healthy':
                print(report)
            else:
                print("✅ All automations healthy")
        else:
            print(report)

    # Exit code based on status
    exit_codes = {"healthy": 0, "degraded": 1, "critical": 2}
    sys.exit(exit_codes.get(results['overall_status'], 1))


if __name__ == "__main__":
    main()
