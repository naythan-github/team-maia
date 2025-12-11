#!/usr/bin/env python3
"""
Automated Daily Briefing System
Combines all intelligence sources for comprehensive daily briefing with email delivery.

Integrates:
- Unified Morning Briefing (unified_morning_briefing.py)
- Enhanced Email Triage (enhanced_email_triage.py)
- Meeting Prep Automation (meeting_prep_automation.py)
- Email delivery via iCloud SMTP

Author: Maia Personal Assistant Agent
Phase: 85c - Automated Daily Delivery
Date: 2025-10-03
"""

import json
import sys
import os
from datetime import datetime
from typing import Dict
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from claude.tools.core.paths import MAIA_ROOT
sys.path.insert(0, str(MAIA_ROOT))

from claude.tools.unified_morning_briefing import UnifiedMorningBriefing
from claude.tools.enhanced_email_triage import EnhancedEmailTriage
from claude.tools.meeting_prep_automation import MeetingPrepAutomation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AutomatedDailyBriefing:
    """Automated daily briefing with email delivery."""

    def __init__(self, delivery_email: str = "naythan.dawe@orro.group"):
        """
        Initialize automated briefing system.

        Args:
            delivery_email: Email address for briefing delivery
        """
        self.delivery_email = delivery_email

        # Initialize all intelligence systems
        self.morning_briefing = UnifiedMorningBriefing()
        self.email_triage = EnhancedEmailTriage()
        self.meeting_prep = MeetingPrepAutomation()

    def generate_complete_briefing(self) -> Dict:
        """
        Generate complete daily briefing.

        Returns:
            Complete briefing dictionary
        """
        logger.info("Generating complete daily briefing...")

        briefing = {
            'generated_at': datetime.now().isoformat(),
            'date': datetime.now().strftime("%A, %B %d, %Y"),
            'morning_brief': self.morning_briefing.generate_briefing(),
            'email_triage': self.email_triage.triage_inbox(limit=50, min_score=5),
            'meeting_prep': self.meeting_prep.prepare_todays_meetings(),
            'forgotten_followups': self.email_triage.detect_forgotten_followups(days_threshold=5)
        }

        logger.info("Complete briefing generated")
        return briefing

    def format_html_briefing(self, briefing: Dict) -> str:
        """
        Format briefing as HTML email.

        Args:
            briefing: Complete briefing dictionary

        Returns:
            HTML formatted briefing
        """
        html = []

        # Header
        html.append("""
        <html>
        <head>
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
                .header { background: #0066cc; color: white; padding: 20px; }
                .section { margin: 20px 0; padding: 15px; border-left: 4px solid #0066cc; background: #f5f5f5; }
                .priority-high { color: #d32f2f; font-weight: bold; }
                .meeting { background: #e3f2fd; padding: 10px; margin: 10px 0; border-radius: 5px; }
                .tip { background: #fff3cd; padding: 5px 10px; margin: 5px 0; border-radius: 3px; }
            </style>
        </head>
        <body>
        """)

        html.append(f"""
        <div class="header">
            <h1>🌅 Daily Intelligence Briefing</h1>
            <p>{briefing['date']}</p>
        </div>
        """)

        # Calendar Section
        morning = briefing['morning_brief']
        calendar = morning['calendar']

        html.append('<div class="section">')
        html.append('<h2>📅 Your Schedule Today</h2>')

        if calendar['has_events_today']:
            html.append(f"<p><strong>{calendar['today_count']} meetings scheduled</strong></p>")
            html.append('<ul>')
            for event in calendar['today_events']:
                if not event.get('all_day', False):
                    html.append(f"<li><strong>{event['summary']}</strong>")
                    if event.get('location'):
                        html.append(f" - 📍 {event['location']}")
                    html.append('</li>')
            html.append('</ul>')
        else:
            html.append('<p>✅ <strong>No meetings scheduled - focus time available!</strong></p>')

        html.append('</div>')

        # Email Triage Section
        triage = briefing['email_triage']

        html.append('<div class="section">')
        html.append('<h2>📧 Email Priorities</h2>')
        html.append(f"<p><strong>{morning['email']['unread_count']} unread messages</strong></p>")

        if triage['high_priority_messages']:
            html.append(f"<p>🔥 <strong>{triage['high_priority_count']} high-priority messages</strong> (≥{triage['threshold']} points):</p>")
            html.append('<ol>')

            for item in triage['high_priority_messages'][:5]:
                msg = item['message']
                score = item['priority_score']
                reasons = item['priority_reasons']

                html.append(f'<li class="priority-high">[{score} points] {msg.get("subject", "No Subject")}')
                html.append(f'<br><small>From: {msg.get("from", "Unknown")}</small>')
                html.append(f'<br><small>⭐ {", ".join(reasons)}</small>')
                html.append('</li>')

            html.append('</ol>')

        html.append('</div>')

        # Meeting Prep Section
        meetings = briefing['meeting_prep']

        if meetings:
            html.append('<div class="section">')
            html.append('<h2>📋 Meeting Preparation</h2>')

            for meeting in meetings:
                details = meeting['meeting']

                html.append('<div class="meeting">')
                html.append(f"<h3>{details['summary']}</h3>")
                html.append(f"<p>⏰ {details['time']}")
                if details['location']:
                    html.append(f" | 📍 {details['location']}")
                html.append('</p>')

                if meeting['attendees']:
                    html.append('<p><strong>Attendees:</strong></p><ul>')
                    for attendee in meeting['attendees'][:5]:
                        if attendee.get('found'):
                            html.append(f"<li>{attendee['name']}")
                            if attendee.get('job_title'):
                                html.append(f" - {attendee['job_title']}")
                            html.append('</li>')
                    html.append('</ul>')

                if meeting['preparation_tips']:
                    html.append('<p><strong>Preparation Tips:</strong></p>')
                    for tip in meeting['preparation_tips']:
                        html.append(f'<div class="tip">{tip}</div>')

                html.append('</div>')

            html.append('</div>')

        # Forgotten Follow-ups
        forgotten = briefing['forgotten_followups']

        if forgotten and len(forgotten) > 0:
            html.append('<div class="section">')
            html.append('<h2>⚠️ Follow-up Reminders</h2>')
            html.append(f'<p><strong>{len(forgotten)} messages may need follow-up:</strong></p>')
            html.append('<ul>')

            for item in forgotten[:5]:
                html.append(f"<li>{item['subject']}")
                html.append(f"<br><small>From: {item['from']}</small></li>")

            html.append('</ul>')
            html.append('</div>')

        # Footer
        html.append("""
        <div style="text-align: center; padding: 20px; color: #666;">
            <p>🚀 Have a productive day!</p>
            <p><small>Generated by Maia Personal Assistant Agent</small></p>
        </div>
        </body>
        </html>
        """)

        return ''.join(html)

    def send_email_briefing(self, briefing: Dict) -> bool:
        """
        Send briefing via email using Mail.app.

        Args:
            briefing: Complete briefing dictionary

        Returns:
            True if sent successfully
        """
        try:
            # Generate HTML content
            html_content = self.format_html_briefing(briefing)

            # Save to file for backup
            email_file = str(MAIA_ROOT / "claude/data/daily_briefing_email.html")
            with open(email_file, 'w') as f:
                f.write(html_content)

            logger.info(f"Email briefing saved to {email_file}")

            # Create draft email in Mail.app (avoids Exchange send crash)
            try:
                # Initialize mail bridge (from morning briefing)
                mail_bridge = self.morning_briefing.mail_bridge

                success = mail_bridge.create_draft_email(
                    to=self.delivery_email,
                    subject=f"Daily Briefing - {briefing['date']}",
                    body=html_content,
                    html=True,
                    account="Exchange"
                )

                if success:
                    logger.info(f"✅ Draft email created - Mail.app window opened")
                    logger.info(f"📧 Ready to send to {self.delivery_email} (just click Send)")
                else:
                    logger.warning(f"⚠️  Draft creation status unclear, check {email_file}")

                return success

            except Exception as e:
                logger.error(f"Failed to create draft via Mail.app: {e}")
                logger.info(f"Briefing saved to {email_file} for manual sending")
                return False

        except Exception as e:
            logger.error(f"Error preparing briefing email: {e}")
            return False

    def save_briefing_files(self, briefing: Dict):
        """
        Save briefing to JSON and text files.

        Args:
            briefing: Complete briefing dictionary
        """
        # JSON file
        json_file = str(MAIA_ROOT / "claude/data/daily_briefing_complete.json")
        with open(json_file, 'w') as f:
            json.dump(briefing, f, indent=2, default=str)
        logger.info(f"JSON briefing saved to {json_file}")

        # HTML file
        html_file = str(MAIA_ROOT / "claude/data/daily_briefing_email.html")
        html_content = self.format_html_briefing(briefing)
        with open(html_file, 'w') as f:
            f.write(html_content)
        logger.info(f"HTML briefing saved to {html_file}")


def main():
    """Test automated daily briefing system."""
    print("\n=== Automated Daily Briefing System ===\n")

    briefing_system = AutomatedDailyBriefing()

    # Generate complete briefing
    print("📊 Generating complete daily briefing...")
    briefing = briefing_system.generate_complete_briefing()

    # Save files
    print("\n💾 Saving briefing files...")
    briefing_system.save_briefing_files(briefing)

    # Send email (save to file for now)
    print("\n📧 Preparing email briefing...")
    briefing_system.send_email_briefing(briefing)

    print("\n✅ Daily briefing complete!")
    print("\n📂 Output files:")
    print("  • JSON: ~/git/maia/claude/data/daily_briefing_complete.json")
    print("  • HTML: ~/git/maia/claude/data/daily_briefing_email.html")
    print("\n💡 To email: Open HTML file in browser and send to naythan.general@icloud.com")


if __name__ == '__main__':
    main()
