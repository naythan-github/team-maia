#!/usr/bin/env python3
"""
Meeting Prep Automation System
Generates pre-meeting briefings using Calendar, Email RAG, and Confluence context.

Integrates:
- Calendar Bridge (macos_calendar_bridge.py) - Today's meetings
- Email RAG (email_rag_ollama.py) - Historical email context
- Confluence (reliable_confluence_client.py) - Documentation search
- Contacts Bridge (macos_contacts_bridge.py) - Attendee intelligence

Author: Maia Personal Assistant Agent
Phase: 85b - Meeting Preparation Intelligence
Date: 2025-10-03
"""

import json
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
import re

sys.path.insert(0, os.path.expanduser('~/git/maia'))

from claude.tools.macos_calendar_bridge import MacOSCalendarBridge
from claude.tools.macos_contacts_bridge import MacOSContactsBridge
from claude.tools.macos_mail_bridge import MacOSMailBridge
from claude.tools.reliable_confluence_client import ReliableConfluenceClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MeetingPrepAutomation:
    """Automated meeting preparation with multi-source intelligence."""

    def __init__(self):
        """Initialize meeting prep system."""
        self.calendar_bridge = MacOSCalendarBridge()
        self.contacts_bridge = MacOSContactsBridge()
        self.mail_bridge = MacOSMailBridge()
        self.confluence_client = ReliableConfluenceClient()

    def _extract_attendees_from_description(self, description: str) -> List[str]:
        """
        Extract attendee emails from meeting description.

        Args:
            description: Meeting description text

        Returns:
            List of email addresses
        """
        if not description:
            return []

        # Email regex pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, description)

        return list(set(emails))  # Unique emails

    def _search_email_context(self, keywords: List[str], limit: int = 5) -> List[Dict]:
        """
        Search email history for meeting context.

        Args:
            keywords: Search keywords
            limit: Maximum results

        Returns:
            List of relevant email dictionaries
        """
        relevant_emails = []

        for keyword in keywords[:3]:  # Limit keyword searches
            try:
                # Search by subject/sender
                results = self.mail_bridge.search_by_sender(
                    sender=keyword,
                    limit=limit
                )
                relevant_emails.extend(results)
            except Exception as e:
                logger.warning(f"Email search error for '{keyword}': {e}")

        # Remove duplicates
        seen = set()
        unique_emails = []
        for email in relevant_emails:
            email_id = email.get('subject', '') + email.get('from', '')
            if email_id not in seen:
                seen.add(email_id)
                unique_emails.append(email)

        return unique_emails[:limit]

    def _search_confluence_context(
        self,
        keywords: List[str],
        space_key: str = "ORRO",
        limit: int = 5
    ) -> List[Dict]:
        """
        Search Confluence for meeting-related documentation.

        Args:
            keywords: Search keywords
            space_key: Confluence space to search
            limit: Maximum results

        Returns:
            List of relevant Confluence pages
        """
        relevant_pages = []

        for keyword in keywords[:2]:  # Limit searches
            try:
                results = self.confluence_client.search_content(
                    cql=f'space = {space_key} AND text ~ "{keyword}"',
                    limit=limit
                )

                for page in results:
                    relevant_pages.append({
                        'title': page.get('title', ''),
                        'url': page.get('_links', {}).get('webui', ''),
                        'excerpt': page.get('excerpt', ''),
                        'space': space_key
                    })
            except Exception as e:
                logger.warning(f"Confluence search error for '{keyword}': {e}")

        return relevant_pages[:limit]

    def _enrich_attendees(self, attendee_emails: List[str]) -> List[Dict]:
        """
        Enrich attendee information from Contacts.

        Args:
            attendee_emails: List of attendee email addresses

        Returns:
            List of enriched attendee dictionaries
        """
        enriched = []

        for email in attendee_emails:
            contact = self.contacts_bridge.search_by_email(email)

            if contact:
                enriched.append({
                    'email': email,
                    'name': contact.get('full_name', ''),
                    'company': contact.get('company', ''),
                    'job_title': contact.get('job_title', ''),
                    'found': True
                })
            else:
                enriched.append({
                    'email': email,
                    'name': email.split('@')[0].replace('.', ' ').title(),
                    'found': False
                })

        return enriched

    def prepare_meeting_briefing(self, event: Dict) -> Dict:
        """
        Prepare comprehensive meeting briefing.

        Args:
            event: Calendar event dictionary

        Returns:
            Meeting briefing dictionary
        """
        logger.info(f"Preparing briefing for: {event.get('summary', 'Unknown Meeting')}")

        # Extract meeting details
        summary = event.get('summary', 'Unknown Meeting')
        location = event.get('location', '')
        description = event.get('description', '')
        start_time = event.get('start_date', '')

        # Extract keywords for search
        keywords = []
        keywords.append(summary)
        if location:
            keywords.append(location)

        # Extract attendees from description
        attendee_emails = self._extract_attendees_from_description(description)
        keywords.extend([email.split('@')[0] for email in attendee_emails])

        # Search email context
        email_context = self._search_email_context(keywords, limit=5)

        # Search Confluence context
        confluence_context = self._search_confluence_context(keywords, limit=5)

        # Enrich attendees
        enriched_attendees = self._enrich_attendees(attendee_emails)

        briefing = {
            'meeting': {
                'summary': summary,
                'time': start_time,
                'location': location,
                'description': description
            },
            'attendees': enriched_attendees,
            'email_context': email_context,
            'confluence_context': confluence_context,
            'preparation_tips': self._generate_prep_tips(event, enriched_attendees, email_context)
        }

        logger.info(f"Briefing prepared: {len(email_context)} emails, {len(confluence_context)} docs")
        return briefing

    def _generate_prep_tips(
        self,
        event: Dict,
        attendees: List[Dict],
        email_context: List[Dict]
    ) -> List[str]:
        """
        Generate meeting preparation tips.

        Args:
            event: Calendar event
            attendees: Enriched attendees
            email_context: Email context

        Returns:
            List of preparation tips
        """
        tips = []

        # Attendee-based tips
        if attendees:
            senior_attendees = [a for a in attendees if 'manager' in a.get('job_title', '').lower()
                               or 'director' in a.get('job_title', '').lower()]
            if senior_attendees:
                tips.append(f"⭐ Senior leadership attending: {senior_attendees[0].get('name', '')}")

        # Email context tips
        if email_context:
            recent_email = email_context[0]
            tips.append(f"📧 Recent email: \"{recent_email.get('subject', '')}\"")

        # Location tips
        location = event.get('location', '')
        if 'teams' in location.lower() or 'zoom' in location.lower():
            tips.append("💻 Virtual meeting - test audio/video 5 mins before")
        elif location:
            tips.append(f"📍 In-person at: {location}")

        # Time tips
        start_time = event.get('start_date', '')
        if '9:00' in start_time or '9:30' in start_time:
            tips.append("☕ Early morning - grab coffee first")

        return tips

    def prepare_todays_meetings(self) -> List[Dict]:
        """
        Prepare briefings for all today's meetings.

        Returns:
            List of meeting briefing dictionaries
        """
        logger.info("Preparing briefings for today's meetings...")

        # Get today's events
        today_events = self.calendar_bridge.get_today_events()

        # Filter out all-day events
        meetings = [e for e in today_events if not e.get('all_day', False)]

        logger.info(f"Found {len(meetings)} meetings today")

        # Prepare briefing for each
        briefings = []
        for event in meetings:
            try:
                briefing = self.prepare_meeting_briefing(event)
                briefings.append(briefing)
            except Exception as e:
                logger.error(f"Error preparing briefing: {e}")

        return briefings

    def format_briefing_report(self, briefings: List[Dict]) -> str:
        """
        Format meeting briefings as readable report.

        Args:
            briefings: List of briefing dictionaries

        Returns:
            Formatted report text
        """
        lines = []
        lines.append("=" * 70)
        lines.append("📋 MEETING PREPARATION BRIEFINGS")
        lines.append("=" * 70)

        if not briefings:
            lines.append("\n✅ No meetings scheduled today")
            lines.append("\n" + "=" * 70)
            return "\n".join(lines)

        for idx, briefing in enumerate(briefings, 1):
            meeting = briefing['meeting']

            lines.append(f"\n## Meeting {idx}: {meeting['summary']}")
            lines.append(f"⏰ Time: {meeting['time']}")

            if meeting['location']:
                lines.append(f"📍 Location: {meeting['location']}")

            # Attendees
            if briefing['attendees']:
                lines.append(f"\n👥 Attendees ({len(briefing['attendees'])}):")
                for attendee in briefing['attendees'][:5]:
                    if attendee.get('found'):
                        lines.append(f"  • {attendee['name']}")
                        if attendee.get('job_title'):
                            lines.append(f"    {attendee['job_title']}")
                    else:
                        lines.append(f"  • {attendee['name']} ({attendee['email']})")

            # Email context
            if briefing['email_context']:
                lines.append(f"\n📧 Email Context ({len(briefing['email_context'])} recent):")
                for email in briefing['email_context'][:3]:
                    lines.append(f"  • {email.get('subject', 'No Subject')}")

            # Confluence context
            if briefing['confluence_context']:
                lines.append(f"\n📚 Documentation ({len(briefing['confluence_context'])} pages):")
                for page in briefing['confluence_context'][:3]:
                    lines.append(f"  • {page['title']}")

            # Preparation tips
            if briefing['preparation_tips']:
                lines.append(f"\n💡 Preparation Tips:")
                for tip in briefing['preparation_tips']:
                    lines.append(f"  {tip}")

            lines.append("\n" + "-" * 70)

        lines.append("\n" + "=" * 70)
        return "\n".join(lines)


def main():
    """Test meeting prep automation system."""
    print("\n=== Meeting Prep Automation System ===\n")

    prep = MeetingPrepAutomation()

    # Prepare today's meetings
    print("📊 Preparing briefings for today's meetings...")
    briefings = prep.prepare_todays_meetings()

    # Display report
    report = prep.format_briefing_report(briefings)
    print(report)

    # Save results
    output_file = '/Users/naythandawe/git/maia/claude/data/meeting_prep_briefings.json'
    with open(output_file, 'w') as f:
        json.dump({
            'briefings': briefings,
            'generated_at': datetime.now().isoformat()
        }, f, indent=2, default=str)

    print(f"\n💾 Briefings saved to {output_file}")


if __name__ == '__main__':
    main()
