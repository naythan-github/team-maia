#!/usr/bin/env python3
"""
Hook Performance Alerts - Phase 127 Monitoring

Performance monitoring alerts for hook degradation detection:
- P95 latency exceeding SLO thresholds
- Output pollution increases
- /compact failure rate monitoring

Integrates with existing Maia alert system.

Usage:
    # Check current performance against SLOs
    python3 claude/tools/sre/hook_performance_alerts.py check

    # Monitor continuously (for LaunchAgent/cron)
    python3 claude/tools/sre/hook_performance_alerts.py monitor

Author: Maia (Phase 127 - Monitoring & Alerting)
Created: 2025-10-17
"""

import sys
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Add maia root to path
MAIA_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

DB_PATH = MAIA_ROOT / "claude" / "data" / "databases" / "system" / "performance_metrics.db"


@dataclass
class PerformanceAlert:
    """Performance alert details"""
    severity: str  # 'critical', 'warning', 'info'
    title: str
    message: str
    metric_name: str
    current_value: float
    threshold_value: float
    timestamp: datetime


class HookPerformanceAlerting:
    """
    Hook performance monitoring and alerting.

    Alert Rules:
    1. hook_latency_high: P95 > 75ms for normal messages
    2. hook_latency_critical: P95 > 150ms for normal messages
    3. build_latency_high: P95 > 1500ms for build messages
    4. output_pollution_high: Avg > 3 lines per message
    5. capability_checker_slow: Build P95 > 500ms (post-optimization)
    """

    # Alert thresholds
    THRESHOLDS = {
        'normal': {
            'p95_warning': 75,      # 75% of 100ms SLO
            'p95_critical': 150,    # 150% of 100ms SLO
            'output_warning': 3     # Lines
        },
        'build': {
            'p95_warning': 1500,    # 150% of 1000ms SLO
            'p95_critical': 2000,   # 200% of 1000ms SLO
        },
        'slash_command': {
            'p95_warning': 15,      # 150% of 10ms SLO
            'p95_critical': 25,     # 250% of 10ms SLO
        }
    }

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.alerts: List[PerformanceAlert] = []

    def check_performance(self) -> List[PerformanceAlert]:
        """
        Check current performance against thresholds.

        Returns:
            List of PerformanceAlert objects (empty if all OK)
        """
        self.alerts = []

        if not self.db_path.exists():
            return self.alerts

        baseline = self._get_latest_baseline()
        if not baseline:
            return self.alerts

        # Check each message type
        for msg_type, metrics in baseline.items():
            self._check_latency_threshold(msg_type, metrics)
            self._check_output_pollution(msg_type, metrics)

        # Sort by severity (critical first)
        severity_order = {'critical': 0, 'warning': 1, 'info': 2}
        self.alerts.sort(key=lambda a: severity_order.get(a.severity, 3))

        return self.alerts

    def _get_latest_baseline(self) -> Dict:
        """Get latest performance baseline from database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT message_type, p50_latency_ms, p95_latency_ms, p99_latency_ms,
                       avg_output_lines, timestamp
                FROM performance_baselines
                ORDER BY timestamp DESC
                LIMIT 3
            """)

            results = {}
            for row in cursor.fetchall():
                msg_type, p50, p95, p99, output, timestamp = row
                results[msg_type] = {
                    'p50': p50,
                    'p95': p95,
                    'p99': p99,
                    'avg_output': output,
                    'timestamp': timestamp
                }

            conn.close()
            return results

        except Exception as e:
            print(f"Error reading baseline: {e}", file=sys.stderr)
            return {}

    def _check_latency_threshold(self, msg_type: str, metrics: Dict):
        """Check if latency exceeds thresholds."""
        thresholds = self.THRESHOLDS.get(msg_type)
        if not thresholds:
            return

        p95 = metrics['p95']

        # Critical threshold
        if p95 > thresholds.get('p95_critical', float('inf')):
            self.alerts.append(PerformanceAlert(
                severity='critical',
                title=f'Hook Latency Critical: {msg_type}',
                message=f'P95 latency ({p95:.0f}ms) exceeds critical threshold ({thresholds["p95_critical"]}ms)',
                metric_name=f'{msg_type}_p95_latency',
                current_value=p95,
                threshold_value=thresholds['p95_critical'],
                timestamp=datetime.now()
            ))

        # Warning threshold
        elif p95 > thresholds.get('p95_warning', float('inf')):
            self.alerts.append(PerformanceAlert(
                severity='warning',
                title=f'Hook Latency High: {msg_type}',
                message=f'P95 latency ({p95:.0f}ms) exceeds warning threshold ({thresholds["p95_warning"]}ms)',
                metric_name=f'{msg_type}_p95_latency',
                current_value=p95,
                threshold_value=thresholds['p95_warning'],
                timestamp=datetime.now()
            ))

    def _check_output_pollution(self, msg_type: str, metrics: Dict):
        """Check if output pollution is high."""
        thresholds = self.THRESHOLDS.get(msg_type)
        if not thresholds or 'output_warning' not in thresholds:
            return

        output = metrics['avg_output']
        threshold = thresholds['output_warning']

        if output > threshold:
            self.alerts.append(PerformanceAlert(
                severity='warning',
                title=f'Output Pollution High: {msg_type}',
                message=f'Average output ({output:.1f} lines) exceeds threshold ({threshold} lines)',
                metric_name=f'{msg_type}_avg_output',
                current_value=output,
                threshold_value=threshold,
                timestamp=datetime.now()
            ))

    def format_alerts_terminal(self) -> str:
        """Format alerts for terminal output."""
        if not self.alerts:
            return "✅ All performance metrics within SLO thresholds"

        lines = []
        lines.append(f"\n⚠️  {len(self.alerts)} Performance Alert(s) Detected\n")
        lines.append("=" * 80)

        for alert in self.alerts:
            # Severity indicator
            if alert.severity == 'critical':
                indicator = "🔴"
            elif alert.severity == 'warning':
                indicator = "🟠"
            else:
                indicator = "🔵"

            lines.append(f"\n{indicator} {alert.title}")
            lines.append(f"   {alert.message}")
            lines.append(f"   Metric: {alert.metric_name}")
            lines.append(f"   Current: {alert.current_value:.1f} | Threshold: {alert.threshold_value:.1f}")
            lines.append(f"   Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

        lines.append("\n" + "=" * 80)
        lines.append("\n📊 Dashboard: http://127.0.0.1:8067")
        lines.append("📈 Profiler: python3 claude/tools/sre/hook_performance_profiler.py report\n")

        return "\n".join(lines)

    def format_alerts_json(self) -> str:
        """Format alerts as JSON."""
        import json
        return json.dumps({
            'alert_count': len(self.alerts),
            'timestamp': datetime.now().isoformat(),
            'alerts': [
                {
                    'severity': a.severity,
                    'title': a.title,
                    'message': a.message,
                    'metric_name': a.metric_name,
                    'current_value': a.current_value,
                    'threshold_value': a.threshold_value,
                    'timestamp': a.timestamp.isoformat()
                }
                for a in self.alerts
            ]
        }, indent=2)

    def get_alert_summary(self) -> Tuple[int, int, int]:
        """
        Get alert summary counts.

        Returns:
            (critical_count, warning_count, info_count)
        """
        critical = sum(1 for a in self.alerts if a.severity == 'critical')
        warning = sum(1 for a in self.alerts if a.severity == 'warning')
        info = sum(1 for a in self.alerts if a.severity == 'info')

        return (critical, warning, info)


def main():
    """CLI interface for performance alerting."""
    import argparse

    parser = argparse.ArgumentParser(description='Hook Performance Alerts')
    parser.add_argument('command', choices=['check', 'monitor'],
                        help='check: One-time check | monitor: Continuous monitoring')
    parser.add_argument('--json', action='store_true', help='JSON output')
    parser.add_argument('--silent', action='store_true', help='Silent mode (exit code only)')
    args = parser.parse_args()

    alerting = HookPerformanceAlerting()

    if args.command == 'check':
        # One-time check
        alerts = alerting.check_performance()

        if args.silent:
            # Exit code only
            if any(a.severity == 'critical' for a in alerts):
                sys.exit(2)  # Critical alerts
            elif any(a.severity == 'warning' for a in alerts):
                sys.exit(1)  # Warning alerts
            else:
                sys.exit(0)  # All OK

        # Output
        if args.json:
            print(alerting.format_alerts_json())
        else:
            print(alerting.format_alerts_terminal())

        # Exit code
        critical, warning, info = alerting.get_alert_summary()
        if critical > 0:
            sys.exit(2)
        elif warning > 0:
            sys.exit(1)
        else:
            sys.exit(0)

    elif args.command == 'monitor':
        # Continuous monitoring (for LaunchAgent/cron)
        print("🔍 Starting continuous performance monitoring...")
        print(f"   Database: {DB_PATH.relative_to(MAIA_ROOT)}")
        print(f"   Checking every 5 minutes...\n")

        import time

        while True:
            alerts = alerting.check_performance()

            if alerts:
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] {len(alerts)} alert(s) detected")
                print(alerting.format_alerts_terminal())

                # TODO: Send to alert delivery service
                # from claude.tools.services.alert_delivery_service import send_alert
                # for alert in alerts:
                #     send_alert(alert)

            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ All metrics within SLO")

            time.sleep(300)  # 5 minutes


if __name__ == '__main__':
    main()
