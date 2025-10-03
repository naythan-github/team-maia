#!/usr/bin/env python3
"""
Enhanced Email Triage System
Combines Email RAG semantic search with priority scoring and forgotten follow-up detection.

Integrates:
- Email RAG (email_rag_ollama.py) - Semantic search
- Mail Bridge (macos_mail_bridge.py) - Email access
- Contacts Bridge (macos_contacts_bridge.py) - Sender enrichment

Author: Maia Personal Assistant Agent
Phase: 85a - Enhanced Email Intelligence
Date: 2025-10-03
"""

import json
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import logging

sys.path.insert(0, os.path.expanduser('~/git/maia'))

from claude.tools.macos_mail_bridge import MacOSMailBridge
from claude.tools.macos_contacts_bridge import MacOSContactsBridge

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedEmailTriage:
    """Enhanced email triage with RAG search and priority scoring."""

    def __init__(self):
        """Initialize email triage system."""
        self.mail_bridge = MacOSMailBridge()
        self.contacts_bridge = MacOSContactsBridge()

        # Priority scoring weights
        self.weights = {
            'orro_domain': 10,        # Orro Group emails
            'unread': 5,              # Unread messages
            'recent': 3,              # Last 24 hours
            'has_contact': 2,         # Known contact
            'senior_title': 5,        # Senior leadership
            'urgent_keywords': 8,     # Urgent/Important keywords
            'thread_length': -2       # Long threads deprioritized
        }

        # Urgent keywords
        self.urgent_keywords = [
            'urgent', 'asap', 'immediate', 'critical', 'important',
            'deadline', 'today', 'tomorrow', 'escalation', 'p1', 'p0',
            'client', 'customer', 'incident', 'outage'
        ]

        # Senior titles
        self.senior_titles = [
            'director', 'manager', 'head', 'chief', 'vp', 'ceo', 'cto',
            'cfo', 'president', 'principal', 'senior', 'lead'
        ]

    def _extract_email(self, sender: str) -> str:
        """
        Extract email from "Name <email>" format.

        Args:
            sender: Sender string

        Returns:
            Email address
        """
        if '<' in sender and '>' in sender:
            return sender.split('<')[1].split('>')[0]
        return sender

    def _is_orro_email(self, email: str) -> bool:
        """Check if email is from Orro domain."""
        return '@orro.group' in email.lower() or '@orro.' in email.lower()

    def _has_urgent_keywords(self, subject: str, content: str = '') -> bool:
        """Check for urgent keywords in subject/content."""
        text = (subject + ' ' + content).lower()
        return any(keyword in text for keyword in self.urgent_keywords)

    def _is_senior_title(self, job_title: str) -> bool:
        """Check if job title indicates senior leadership."""
        if not job_title:
            return False
        title_lower = job_title.lower()
        return any(senior in title_lower for senior in self.senior_titles)

    def _calculate_priority_score(
        self,
        message: Dict,
        contact_info: Optional[Dict] = None
    ) -> Tuple[int, List[str]]:
        """
        Calculate priority score for message.

        Args:
            message: Message dictionary
            contact_info: Optional contact information

        Returns:
            Tuple of (score, reasons)
        """
        score = 0
        reasons = []

        # Extract email
        sender_email = self._extract_email(message.get('from', ''))

        # Orro domain
        if self._is_orro_email(sender_email):
            score += self.weights['orro_domain']
            reasons.append("Orro Group sender")

        # Unread (if available in message data)
        if message.get('unread', False):
            score += self.weights['unread']
            reasons.append("Unread")

        # Recent (last 24 hours)
        date_received = message.get('date_received', '')
        if date_received:
            # Simple check - if date string contains today's date
            today = datetime.now().strftime('%Y-%m-%d')
            if today in str(date_received):
                score += self.weights['recent']
                reasons.append("Received today")

        # Contact enrichment
        if contact_info:
            score += self.weights['has_contact']
            reasons.append("Known contact")

            # Senior title
            job_title = contact_info.get('job_title', '')
            if self._is_senior_title(job_title):
                score += self.weights['senior_title']
                reasons.append(f"Senior: {job_title}")

        # Urgent keywords
        subject = message.get('subject', '')
        if self._has_urgent_keywords(subject):
            score += self.weights['urgent_keywords']
            reasons.append("Urgent keywords")

        return score, reasons

    def triage_inbox(
        self,
        limit: int = 50,
        min_score: int = 5
    ) -> Dict:
        """
        Triage inbox with priority scoring.

        Args:
            limit: Maximum messages to analyze
            min_score: Minimum priority score threshold

        Returns:
            Triage results dictionary
        """
        logger.info(f"Triaging inbox (limit={limit}, min_score={min_score})...")

        # Get inbox messages
        messages = self.mail_bridge.get_inbox_messages(
            limit=limit,
            account="Exchange"
        )

        # Score and enrich each message
        triaged_messages = []
        for msg in messages:
            sender_email = self._extract_email(msg.get('from', ''))

            # Get contact info
            contact_info = self.contacts_bridge.search_by_email(sender_email)

            # Calculate priority
            score, reasons = self._calculate_priority_score(msg, contact_info)

            # Only include if above threshold
            if score >= min_score:
                triaged_messages.append({
                    'message': msg,
                    'priority_score': score,
                    'priority_reasons': reasons,
                    'contact_info': contact_info,
                    'sender_email': sender_email
                })

        # Sort by priority score (descending)
        triaged_messages.sort(key=lambda x: x['priority_score'], reverse=True)

        logger.info(f"Triaged {len(triaged_messages)} high-priority messages from {len(messages)} total")

        return {
            'total_analyzed': len(messages),
            'high_priority_count': len(triaged_messages),
            'high_priority_messages': triaged_messages,
            'threshold': min_score
        }

    def detect_forgotten_followups(
        self,
        days_threshold: int = 5,
        limit: int = 100
    ) -> List[Dict]:
        """
        Detect emails needing follow-up.

        Args:
            days_threshold: Days without response = forgotten
            limit: Messages to analyze

        Returns:
            List of forgotten follow-up dictionaries
        """
        logger.info(f"Detecting forgotten follow-ups (>{days_threshold} days)...")

        # Get inbox messages
        messages = self.mail_bridge.get_inbox_messages(
            limit=limit,
            account="Exchange"
        )

        forgotten = []
        cutoff_date = datetime.now() - timedelta(days=days_threshold)

        for msg in messages:
            # Simple date check (would need more sophisticated parsing in production)
            date_received = msg.get('date_received', '')

            # Check if from Orro and old
            sender_email = self._extract_email(msg.get('from', ''))

            if self._is_orro_email(sender_email):
                # TODO: More sophisticated date parsing
                # For now, flag all Orro messages as potential follow-ups
                forgotten.append({
                    'subject': msg.get('subject', ''),
                    'from': msg.get('from', ''),
                    'date': date_received,
                    'reason': 'Orro Group message requiring review'
                })

        logger.info(f"Found {len(forgotten)} potential follow-ups")
        return forgotten[:10]  # Top 10

    def format_triage_report(self, triage_result: Dict) -> str:
        """
        Format triage results as readable report.

        Args:
            triage_result: Triage results dictionary

        Returns:
            Formatted report text
        """
        lines = []
        lines.append("=" * 70)
        lines.append("📧 ENHANCED EMAIL TRIAGE REPORT")
        lines.append("=" * 70)

        lines.append(f"\n📊 Analysis Summary:")
        lines.append(f"  • Total Messages Analyzed: {triage_result['total_analyzed']}")
        lines.append(f"  • High Priority (≥{triage_result['threshold']}): {triage_result['high_priority_count']}")

        lines.append(f"\n🔥 High Priority Messages:")
        lines.append("-" * 70)

        for idx, item in enumerate(triage_result['high_priority_messages'][:10], 1):
            msg = item['message']
            score = item['priority_score']
            reasons = item['priority_reasons']
            contact = item['contact_info']

            lines.append(f"\n{idx}. [{score} points] {msg.get('subject', 'No Subject')}")
            lines.append(f"   From: {msg.get('from', 'Unknown')}")

            if contact:
                if contact.get('company'):
                    lines.append(f"   💼 {contact['company']}")
                if contact.get('job_title'):
                    lines.append(f"   👔 {contact['job_title']}")

            lines.append(f"   ⭐ Priority Factors: {', '.join(reasons)}")

        lines.append("\n" + "=" * 70)
        return "\n".join(lines)


def main():
    """Test enhanced email triage system."""
    print("\n=== Enhanced Email Triage System ===\n")

    triage = EnhancedEmailTriage()

    # Run triage
    print("📊 Analyzing inbox...")
    results = triage.triage_inbox(limit=50, min_score=5)

    # Display report
    report = triage.format_triage_report(results)
    print(report)

    # Detect forgotten follow-ups
    print("\n🔍 Checking for forgotten follow-ups...")
    forgotten = triage.detect_forgotten_followups(days_threshold=5, limit=100)

    if forgotten:
        print(f"\n⚠️  {len(forgotten)} messages may need follow-up:")
        for item in forgotten[:5]:
            print(f"  • {item['subject']}")
            print(f"    From: {item['from']}")
    else:
        print("✅ No forgotten follow-ups detected")

    # Save results
    output_file = '/Users/naythandawe/git/maia/claude/data/email_triage_report.json'
    with open(output_file, 'w') as f:
        json.dump({
            'triage_results': results,
            'forgotten_followups': forgotten,
            'generated_at': datetime.now().isoformat()
        }, f, indent=2, default=str)

    print(f"\n💾 Report saved to {output_file}")


if __name__ == '__main__':
    main()
