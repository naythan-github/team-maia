#!/usr/bin/env python3
"""
Security Alert Delivery System
Delivers security alerts via Slack webhook and other channels.

Features:
- Slack webhook integration
- Alert formatting with severity colors
- Rate limiting to prevent alert fatigue
- Audit logging of all alerts
"""

import os
import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("security-alerts")


class SecurityAlertDelivery:
    """
    Delivers security alerts to configured channels.

    Usage:
        delivery = SecurityAlertDelivery()
        delivery.send_alert('critical', 'Security Breach', 'Unauthorized access detected')
    """

    SEVERITY_COLORS = {
        'critical': '#FF0000',  # Red
        'high': '#FFA500',      # Orange
        'medium': '#FFFF00',    # Yellow
        'low': '#00FF00',       # Green
        'info': '#0000FF'       # Blue
    }

    SEVERITY_EMOJIS = {
        'critical': ':rotating_light:',
        'high': ':warning:',
        'medium': ':large_yellow_circle:',
        'low': ':information_source:',
        'info': ':blue_book:'
    }

    def __init__(self, webhook_url: Optional[str] = None):
        """
        Initialize alert delivery system.

        Args:
            webhook_url: Slack webhook URL. If None, reads from MAIA_SECURITY_SLACK_WEBHOOK env var.
        """
        self.webhook_url = webhook_url or os.environ.get('MAIA_SECURITY_SLACK_WEBHOOK', '')

        # Rate limiting: track last alert times by type
        self._last_alerts: Dict[str, datetime] = {}
        self._rate_limit_seconds = 60  # Min seconds between same alert type

        # Audit log path
        self.audit_log_path = Path.home() / ".maia" / "security_alerts.log"
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)

    def format_alert(self, severity: str, title: str, description: str,
                     additional_fields: Optional[Dict[str, str]] = None) -> str:
        """
        Format alert message for display.

        Args:
            severity: Alert severity (critical, high, medium, low, info)
            title: Alert title
            description: Alert description
            additional_fields: Optional additional fields to include

        Returns:
            Formatted alert message string
        """
        severity_lower = severity.lower()
        emoji = self.SEVERITY_EMOJIS.get(severity_lower, ':question:')

        lines = [
            f"{emoji} **{severity.upper()}**: {title}",
            f"",
            f"{description}",
        ]

        if additional_fields:
            lines.append("")
            for key, value in additional_fields.items():
                lines.append(f"- **{key}**: {value}")

        lines.append(f"")
        lines.append(f"_Timestamp: {datetime.now().isoformat()}_")

        return "\n".join(lines)

    def _create_slack_payload(self, severity: str, title: str,
                              description: str) -> Dict[str, Any]:
        """Create Slack webhook payload"""
        severity_lower = severity.lower()
        color = self.SEVERITY_COLORS.get(severity_lower, '#808080')
        emoji = self.SEVERITY_EMOJIS.get(severity_lower, ':question:')

        return {
            "attachments": [{
                "color": color,
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"{emoji} {severity.upper()}: {title}",
                            "emoji": True
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": description
                        }
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"Maia Security System | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                            }
                        ]
                    }
                ]
            }]
        }

    def _audit_log(self, severity: str, title: str, description: str,
                   delivered: bool, channel: str):
        """Log alert to audit file"""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "severity": severity,
                "title": title,
                "description": description[:200],  # Truncate for log
                "delivered": delivered,
                "channel": channel
            }
            with open(self.audit_log_path, 'a') as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            logger.warning(f"Failed to write audit log: {e}")

    def _check_rate_limit(self, alert_key: str) -> bool:
        """Check if alert should be rate limited"""
        last_time = self._last_alerts.get(alert_key)
        if last_time:
            elapsed = (datetime.now() - last_time).total_seconds()
            if elapsed < self._rate_limit_seconds:
                return True  # Rate limited
        return False

    def send_alert(self, severity: str, title: str, description: str,
                   force: bool = False) -> bool:
        """
        Send security alert to configured channels.

        Args:
            severity: Alert severity (critical, high, medium, low, info)
            title: Alert title
            description: Alert description
            force: If True, bypass rate limiting

        Returns:
            True if alert was sent successfully, False otherwise
        """
        # Check rate limiting
        alert_key = f"{severity}:{title}"
        if not force and self._check_rate_limit(alert_key):
            logger.debug(f"Alert rate limited: {alert_key}")
            return False

        # Update last alert time
        self._last_alerts[alert_key] = datetime.now()

        # Check if webhook is configured
        if not self.webhook_url:
            logger.warning("No Slack webhook configured (MAIA_SECURITY_SLACK_WEBHOOK)")
            self._audit_log(severity, title, description, False, "slack")
            return False

        try:
            payload = self._create_slack_payload(severity, title, description)

            req = urllib.request.Request(
                self.webhook_url,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    logger.info(f"Alert sent: [{severity}] {title}")
                    self._audit_log(severity, title, description, True, "slack")
                    return True
                else:
                    logger.error(f"Slack webhook returned status {response.status}")
                    self._audit_log(severity, title, description, False, "slack")
                    return False

        except urllib.error.URLError as e:
            logger.error(f"Failed to send alert: {e}")
            self._audit_log(severity, title, description, False, "slack")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending alert: {e}")
            self._audit_log(severity, title, description, False, "slack")
            return False

    def send_critical_alert(self, title: str, description: str) -> bool:
        """Send critical severity alert (bypasses rate limiting)"""
        return self.send_alert('critical', title, description, force=True)

    def get_recent_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent alerts from audit log"""
        alerts = []
        cutoff = datetime.now() - timedelta(hours=hours)

        try:
            if self.audit_log_path.exists():
                with open(self.audit_log_path, 'r') as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            entry_time = datetime.fromisoformat(entry['timestamp'])
                            if entry_time >= cutoff:
                                alerts.append(entry)
                        except (json.JSONDecodeError, KeyError):
                            continue
        except Exception as e:
            logger.error(f"Failed to read audit log: {e}")

        return alerts


def main():
    """CLI interface for testing alert delivery"""
    import argparse

    parser = argparse.ArgumentParser(description='Security Alert Delivery')
    parser.add_argument('--test', action='store_true', help='Send test alert')
    parser.add_argument('--severity', '-s', default='info',
                        choices=['critical', 'high', 'medium', 'low', 'info'],
                        help='Alert severity')
    parser.add_argument('--title', '-t', default='Test Alert', help='Alert title')
    parser.add_argument('--description', '-d', default='This is a test alert',
                        help='Alert description')
    parser.add_argument('--recent', '-r', type=int, metavar='HOURS',
                        help='Show recent alerts from last N hours')

    args = parser.parse_args()

    delivery = SecurityAlertDelivery()

    if args.recent:
        alerts = delivery.get_recent_alerts(args.recent)
        print(f"Found {len(alerts)} alerts in last {args.recent} hours:")
        for alert in alerts:
            print(f"  [{alert['severity']}] {alert['title']} - {alert['timestamp']}")

    elif args.test:
        print(f"Sending test alert: [{args.severity}] {args.title}")
        result = delivery.send_alert(args.severity, args.title, args.description)
        if result:
            print("Alert sent successfully")
        else:
            print("Failed to send alert (check webhook configuration)")


if __name__ == '__main__':
    main()
