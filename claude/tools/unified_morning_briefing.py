#!/usr/bin/env python3
"""
Unified Morning Briefing System
Combines Email RAG, Calendar, and Contacts for comprehensive daily intelligence.

Integrates:
- Email Intelligence (email_rag_ollama.py + macos_mail_bridge.py)
- Calendar Intelligence (macos_calendar_bridge.py)
- Contact Intelligence (macos_contacts_bridge.py)
- RSS Intelligence (existing automated_morning_briefing.py)

Author: Maia Personal Assistant Agent
Phase: 84 - Unified Work Intelligence
Date: 2025-10-03
"""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
from pathlib import Path

# Import all bridges
import sys
import os
from claude.tools.core.paths import MAIA_ROOT
sys.path.insert(0, str(MAIA_ROOT))

from claude.tools.macos_mail_bridge import MacOSMailBridge
from claude.tools.macos_calendar_bridge import MacOSCalendarBridge
from claude.tools.macos_contacts_bridge import MacOSContactsBridge

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UnifiedMorningBriefing:
    """Unified morning briefing combining email, calendar, and contacts."""

    def __init__(self):
        """Initialize all intelligence bridges."""
        self.mail_bridge = MacOSMailBridge()
        self.calendar_bridge = MacOSCalendarBridge()
        self.contacts_bridge = MacOSContactsBridge()

    def _format_time(self, date_str: str) -> str:
        """
        Extract time from AppleScript date string.

        Args:
            date_str: AppleScript date format

        Returns:
            Formatted time string
        """
        try:
            if ' at ' in date_str:
                time_part = date_str.split(' at ')[1]
                return time_part
            return date_str
        except Exception:
            return date_str

    def get_calendar_briefing(self) -> Dict:
        """
        Get today's calendar summary.

        Returns:
            Calendar briefing dictionary
        """
        today_events = self.calendar_bridge.get_today_events()
        upcoming_events = self.calendar_bridge.get_events(days_ahead=7)

        # Filter out today's events from upcoming
        upcoming_only = [e for e in upcoming_events if e not in today_events]

        return {
            'today_count': len(today_events),
            'today_events': today_events,
            'upcoming_count': len(upcoming_only),
            'upcoming_events': upcoming_only[:5],  # Next 5
            'has_events_today': len(today_events) > 0
        }

    def get_email_briefing(self, limit: int = 10) -> Dict:
        """
        Get email priority briefing.

        Args:
            limit: Maximum priority emails to return

        Returns:
            Email briefing dictionary
        """
        # Get unread messages
        unread = self.mail_bridge.get_unread_count()

        # Get recent messages from inbox
        recent = self.mail_bridge.get_inbox_messages(
            limit=limit,
            account="Exchange"
        )

        # Enrich with contact info
        enriched_messages = []
        for msg in recent:
            sender_email = msg.get('from', '')

            # Extract email from "Name <email>" format
            if '<' in sender_email and '>' in sender_email:
                email_only = sender_email.split('<')[1].split('>')[0]
            else:
                email_only = sender_email

            # Enrich with contact data
            contact_info = self.contacts_bridge.enrich_email_sender(
                email_only,
                sender_name=msg.get('from', '').split('<')[0].strip()
            )

            enriched_messages.append({
                'subject': msg.get('subject', ''),
                'from': msg.get('from', ''),
                'date': msg.get('date_received', ''),
                'contact_found': contact_info.get('found', False),
                'contact_info': contact_info.get('contact', {}) if contact_info.get('found') else None
            })

        return {
            'unread_count': unread,
            'recent_count': len(recent),
            'recent_messages': enriched_messages
        }

    def get_meeting_prep_briefing(self) -> List[Dict]:
        """
        Get meeting preparation briefings for today's events.

        Returns:
            List of meeting prep dictionaries
        """
        today_events = self.calendar_bridge.get_today_events()

        meeting_preps = []
        for event in today_events:
            # Skip all-day events
            if event.get('all_day', False):
                continue

            prep = {
                'meeting': event['summary'],
                'time': self._format_time(event['start_date']),
                'location': event.get('location', ''),
                'attendees': [],  # TODO: Parse from description
                'context': event.get('description', '')
            }

            # TODO: Add email context search
            # TODO: Add Confluence documentation search

            meeting_preps.append(prep)

        return meeting_preps

    def generate_briefing(self) -> Dict:
        """
        Generate complete morning briefing.

        Returns:
            Complete briefing dictionary
        """
        logger.info("Generating unified morning briefing...")

        briefing = {
            'generated_at': datetime.now().isoformat(),
            'calendar': self.get_calendar_briefing(),
            'email': self.get_email_briefing(),
            'meeting_prep': self.get_meeting_prep_briefing()
        }

        logger.info("Briefing generation complete")
        return briefing

    def format_briefing_text(self, briefing: Dict) -> str:
        """
        Format briefing as readable text.

        Args:
            briefing: Briefing dictionary

        Returns:
            Formatted briefing text
        """
        lines = []
        lines.append("=" * 60)
        lines.append("🌅 MORNING BRIEFING - {}".format(
            datetime.now().strftime("%A, %B %d, %Y")
        ))
        lines.append("=" * 60)

        # Calendar Section
        lines.append("\n📅 YOUR SCHEDULE TODAY")
        lines.append("-" * 60)

        calendar = briefing['calendar']
        if calendar['has_events_today']:
            lines.append(f"✅ {calendar['today_count']} meetings scheduled")
            for event in calendar['today_events']:
                if not event.get('all_day', False):
                    time = self._format_time(event['start_date'])
                    lines.append(f"  • {time} - {event['summary']}")
                    if event.get('location'):
                        lines.append(f"    📍 {event['location']}")
        else:
            lines.append("✅ No meetings scheduled - focus time available")

        if calendar['upcoming_count'] > 0:
            lines.append(f"\n📆 Upcoming this week: {calendar['upcoming_count']} events")

        # Email Section
        lines.append("\n📧 EMAIL PRIORITIES")
        lines.append("-" * 60)

        email = briefing['email']
        lines.append(f"📬 {email['unread_count']} unread messages")

        if email['recent_messages']:
            lines.append(f"\n🔥 Top {len(email['recent_messages'])} Priority:")
            for idx, msg in enumerate(email['recent_messages'][:5], 1):
                lines.append(f"  {idx}. {msg['subject']}")
                lines.append(f"     From: {msg['from']}")

                if msg['contact_found'] and msg['contact_info']:
                    contact = msg['contact_info']
                    if contact.get('company'):
                        lines.append(f"     💼 {contact['company']}")
                    if contact.get('job_title'):
                        lines.append(f"     👔 {contact['job_title']}")

        # Meeting Prep Section
        meeting_preps = briefing['meeting_prep']
        if meeting_preps:
            lines.append("\n📋 MEETING PREP")
            lines.append("-" * 60)

            for prep in meeting_preps:
                lines.append(f"⏰ {prep['time']} - {prep['meeting']}")
                if prep['location']:
                    lines.append(f"   Location: {prep['location']}")
                if prep['context']:
                    lines.append(f"   Context: {prep['context'][:100]}...")

        lines.append("\n" + "=" * 60)
        lines.append("🚀 Have a productive day!")
        lines.append("=" * 60)

        return "\n".join(lines)


def main():
    """Test unified briefing system."""
    print("\n=== Unified Morning Briefing System ===\n")

    briefing_system = UnifiedMorningBriefing()

    # Generate briefing
    print("📊 Generating briefing...")
    briefing = briefing_system.generate_briefing()

    # Display formatted briefing
    print("\n" + briefing_system.format_briefing_text(briefing))

    # Save to file
    output_file = str(MAIA_ROOT / "claude/data/morning_briefing.json")
    with open(output_file, 'w') as f:
        json.dump(briefing, f, indent=2, default=str)

    print(f"\n💾 Briefing saved to {output_file}")

    # Save formatted text
    text_file = str(MAIA_ROOT / "claude/data/morning_briefing.txt")
    with open(text_file, 'w') as f:
        f.write(briefing_system.format_briefing_text(briefing))

    print(f"📄 Text briefing saved to {text_file}")


if __name__ == '__main__':
    main()
