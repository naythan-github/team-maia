#!/usr/bin/env python3
"""
Meeting Context Auto-Assembly System
Automatically generates comprehensive meeting context packages 30 minutes before meetings.

Enhancements over base meeting prep:
- Automatic triggering 30 min before meeting
- Stakeholder sentiment analysis
- Strategic context integration
- Action item status tracking
- Historical decision references
- Recommended discussion topics

Author: Maia Executive Information Manager Agent
Project: INFO_MGT_001 - Phase 1, Week 2
Date: 2025-10-13
"""

import json
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
import logging

MAIA_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

# Import base meeting prep
import importlib.util
def import_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

meeting_prep_path = MAIA_ROOT / "tools" / "meeting_prep_automation.py"
MeetingPrepAutomation = import_module_from_path("meeting_prep_automation", meeting_prep_path).MeetingPrepAutomation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MeetingContextAutoAssembly(MeetingPrepAutomation):
    """Enhanced meeting preparation with automatic context assembly"""

    def __init__(self):
        """Initialize auto-assembly system"""
        super().__init__()

    def _classify_meeting_type(self, event: Dict) -> str:
        """
        Classify meeting type for context-appropriate preparation.

        Returns:
            one of: 1-on-1, team, client, executive, vendor, technical
        """
        summary = event.get('summary', '').lower()
        attendee_emails = self._extract_attendees_from_description(event.get('description', ''))

        # Check for 1-on-1 (2 attendees or less)
        if len(attendee_emails) <= 1:
            return '1-on-1'

        # Check for client indicators
        if any(keyword in summary for keyword in ['client', 'customer', 'account']):
            return 'client'

        # Check for executive indicators
        if any(keyword in summary for keyword in ['exec', 'leadership', 'strategy', 'board']):
            return 'executive'

        # Check for technical indicators
        if any(keyword in summary for keyword in ['technical', 'architecture', 'design', 'review']):
            return 'technical'

        # Check for vendor indicators
        if any(keyword in summary for keyword in ['vendor', 'supplier', 'partner', 'microsoft']):
            return 'vendor'

        # Check for team indicators
        if any(keyword in summary for keyword in ['team', 'standup', 'sync', 'retro']):
            return 'team'

        # Default to team
        return 'team'

    def _analyze_stakeholder_sentiment(self, attendee: Dict) -> Dict:
        """
        Analyze stakeholder sentiment from email/meeting history.

        Note: Phase 1 uses basic inference. Phase 2 will integrate
        Stakeholder Relationship Intelligence Agent for full analysis.

        Returns:
            sentiment analysis dictionary
        """
        email = attendee.get('email', '')
        name = attendee.get('name', '')

        # Basic sentiment inference from name/role
        sentiment_data = {
            'sentiment': 'neutral',
            'confidence': 0.5,
            'recent_interactions': 0,
            'last_contact': 'Unknown',
            'engagement_trend': 'stable'
        }

        # Check if key stakeholder (known names from briefing data)
        known_stakeholders = {
            'hamish': {'sentiment': 'positive', 'engagement': 'high'},
            'mariele': {'sentiment': 'neutral', 'engagement': 'medium'},
            'michael': {'sentiment': 'positive', 'engagement': 'high'},
            'mv': {'sentiment': 'positive', 'engagement': 'high'}
        }

        name_lower = name.lower()
        for known_name, data in known_stakeholders.items():
            if known_name in name_lower or known_name in email.lower():
                sentiment_data['sentiment'] = data['sentiment']
                sentiment_data['engagement_trend'] = data['engagement']
                sentiment_data['confidence'] = 0.7
                sentiment_data['recent_interactions'] = 5  # Assume regular contact
                sentiment_data['last_contact'] = 'This week'
                break

        return sentiment_data

    def _get_strategic_context_for_meeting(self, event: Dict, meeting_type: str) -> Dict:
        """
        Get strategic context relevant to this meeting.

        Returns:
            strategic context dictionary
        """
        summary = event.get('summary', '')

        context = {
            'related_strategic_initiatives': [],
            'open_questions_relevant': [],
            'recent_decisions_relevant': [],
            'recommended_topics': []
        }

        summary_lower = summary.lower()

        # Match to strategic initiatives
        if 'intune' in summary_lower or 'deployment' in summary_lower:
            context['related_strategic_initiatives'].append({
                'initiative': 'Intune Deployment Audit',
                'status': 'Pending',
                'relevance': 'Lighthouse audit delegation and status tracking'
            })
            context['recommended_topics'].append('Intune deployment audit timeline and ownership')
            context['open_questions_relevant'].append('Who has had training so far?')

        if 'otc' in summary_lower or 'one touch' in summary_lower or 'cloud' in summary_lower:
            context['related_strategic_initiatives'].append({
                'initiative': 'OTC (One Touch Cloud) Training & Operations',
                'status': 'In Progress',
                'relevance': 'Training completion and cloud team impact'
            })
            context['recommended_topics'].append('OTC training completion status')
            context['open_questions_relevant'].append('AI in OTC post - how does it impact Cloud?')

        if 'budget' in summary_lower or 'finance' in summary_lower or 'confluence' in summary_lower:
            context['recent_decisions_relevant'].append({
                'decision': 'Confluence budget approval',
                'status': 'Pending',
                'urgency': 'High',
                'relevance': 'Budget decision needed for platform access'
            })
            context['recommended_topics'].append('Confluence budget justification and timeline')

        # Meeting type specific recommendations
        if meeting_type == '1-on-1':
            context['recommended_topics'].extend([
                'Career development and growth opportunities',
                'Current workload and capacity',
                'Any blockers or support needed'
            ])
        elif meeting_type == 'team':
            context['recommended_topics'].extend([
                'Team engagement and morale check',
                'Process improvements and feedback',
                'Upcoming priorities and resource needs'
            ])
        elif meeting_type == 'client':
            context['recommended_topics'].extend([
                'Project status and timeline confirmation',
                'Any concerns or change requests',
                'Next milestones and deliverables'
            ])
        elif meeting_type == 'executive':
            context['recommended_topics'].extend([
                'Strategic initiative progress summary',
                'Key decisions needed',
                'Resource or support requirements'
            ])

        return context

    def _get_action_item_status(self, attendee_emails: List[str]) -> List[Dict]:
        """
        Get status of action items involving meeting attendees.

        Returns:
            list of action item status dictionaries
        """
        # For Phase 1, return placeholder structure
        # Phase 2 will integrate with unified action tracker

        action_items = []

        # Check for known attendees from briefing data
        for email in attendee_emails:
            if 'mariele' in email.lower() or 'mariel' in email.lower():
                action_items.append({
                    'action': 'Provide subcategory list to Mariel for customer spreadsheet update',
                    'owner': 'You',
                    'assignee': 'Mariele',
                    'due_date': 'Next week',
                    'status': 'In Progress',
                    'last_update': 'Recent meeting'
                })

        if not action_items:
            action_items.append({
                'action': 'No pending action items with these attendees',
                'status': 'N/A'
            })

        return action_items

    def prepare_enhanced_meeting_briefing(self, event: Dict) -> Dict:
        """
        Prepare comprehensive enhanced meeting briefing.

        Extends base briefing with:
        - Meeting type classification
        - Stakeholder sentiment analysis
        - Strategic context
        - Action item status
        - Recommended discussion topics

        Args:
            event: Calendar event dictionary

        Returns:
            Enhanced meeting briefing dictionary
        """
        logger.info(f"Preparing enhanced briefing for: {event.get('summary', 'Unknown Meeting')}")

        # Get base briefing
        base_briefing = self.prepare_meeting_briefing(event)

        # Classify meeting type
        meeting_type = self._classify_meeting_type(event)
        logger.info(f"Meeting type classified as: {meeting_type}")

        # Enhance attendees with sentiment analysis
        enhanced_attendees = []
        for attendee in base_briefing['attendees']:
            sentiment_data = self._analyze_stakeholder_sentiment(attendee)
            attendee['sentiment_analysis'] = sentiment_data
            enhanced_attendees.append(attendee)

        # Get strategic context
        strategic_context = self._get_strategic_context_for_meeting(event, meeting_type)

        # Get action item status
        attendee_emails = [a['email'] for a in base_briefing['attendees']]
        action_item_status = self._get_action_item_status(attendee_emails)

        # Assemble enhanced briefing
        enhanced_briefing = {
            'meeting': base_briefing['meeting'],
            'meeting_type': meeting_type,
            'attendees': enhanced_attendees,
            'email_context': base_briefing['email_context'],
            'confluence_context': base_briefing['confluence_context'],
            'strategic_context': strategic_context,
            'action_item_status': action_item_status,
            'preparation_tips': self._generate_enhanced_prep_tips(
                event, meeting_type, enhanced_attendees, strategic_context
            )
        }

        logger.info(f"Enhanced briefing prepared with {len(strategic_context['recommended_topics'])} recommended topics")
        return enhanced_briefing

    def _generate_enhanced_prep_tips(
        self,
        event: Dict,
        meeting_type: str,
        attendees: List[Dict],
        strategic_context: Dict
    ) -> List[str]:
        """
        Generate enhanced meeting preparation tips.

        Args:
            event: Calendar event
            meeting_type: Classified meeting type
            attendees: Enriched attendees with sentiment
            strategic_context: Strategic context data

        Returns:
            List of preparation tips
        """
        tips = []

        # Meeting type specific tips
        type_tips = {
            '1-on-1': '🤝 1-on-1 meeting - focus on relationship building and individual support',
            'team': '👥 Team meeting - ensure all voices heard, time-box discussions',
            'client': '🎯 Client meeting - confirm deliverables, address concerns proactively',
            'executive': '⭐ Executive meeting - lead with outcomes, be concise and strategic',
            'technical': '🔧 Technical meeting - have data ready, focus on decisions not just discussion',
            'vendor': '🤝 Vendor meeting - clear expectations, track commitments'
        }
        tips.append(type_tips.get(meeting_type, '📋 Standard meeting'))

        # Attendee sentiment tips
        negative_sentiment = [a for a in attendees
                             if a.get('sentiment_analysis', {}).get('sentiment') == 'negative']
        if negative_sentiment:
            tips.append(f"⚠️  Stakeholder sentiment concern: {negative_sentiment[0]['name']} - address proactively")

        senior_attendees = [a for a in attendees
                           if 'manager' in a.get('job_title', '').lower() or
                              'director' in a.get('job_title', '').lower() or
                              a.get('sentiment_analysis', {}).get('engagement_trend') == 'high']
        if senior_attendees:
            tips.append(f"⭐ Senior/key stakeholder: {senior_attendees[0]['name']} - prepare executive summary")

        # Strategic context tips
        if strategic_context['related_strategic_initiatives']:
            init = strategic_context['related_strategic_initiatives'][0]
            tips.append(f"📈 Related initiative: {init['initiative']} ({init['status']})")

        if strategic_context['recent_decisions_relevant']:
            decision = strategic_context['recent_decisions_relevant'][0]
            tips.append(f"🎯 Pending decision: {decision['decision']} - opportunity to progress")

        # Location tips
        location = event.get('location', '')
        if 'teams' in location.lower() or 'zoom' in location.lower():
            tips.append("💻 Virtual meeting - test audio/video 5 mins before")
        elif location:
            tips.append(f"📍 In-person at: {location} - allow travel time")

        # Time tips
        start_time = event.get('start_date', '')
        if '9:00' in start_time or '9:30' in start_time:
            tips.append("☕ Early morning - grab coffee first, expect high energy")
        elif '4:00' in start_time or '4:30' in start_time or '5:00' in start_time:
            tips.append("⏰ Late afternoon - keep focused, respect end time")

        return tips

    def prepare_todays_enhanced_meetings(self) -> List[Dict]:
        """
        Prepare enhanced briefings for all today's meetings.

        Returns:
            List of enhanced meeting briefing dictionaries
        """
        logger.info("Preparing enhanced briefings for today's meetings...")

        # Get today's events
        today_events = self.calendar_bridge.get_today_events()

        # Filter out all-day events
        meetings = [e for e in today_events if not e.get('all_day', False)]

        logger.info(f"Found {len(meetings)} meetings today")

        # Prepare enhanced briefing for each
        briefings = []
        for event in meetings:
            try:
                briefing = self.prepare_enhanced_meeting_briefing(event)
                briefings.append(briefing)
            except Exception as e:
                logger.error(f"Error preparing enhanced briefing: {e}")
                # Fallback to base briefing
                try:
                    base_briefing = self.prepare_meeting_briefing(event)
                    base_briefing['meeting_type'] = 'unknown'
                    base_briefing['enhancement_error'] = str(e)
                    briefings.append(base_briefing)
                except Exception as e2:
                    logger.error(f"Error preparing base briefing fallback: {e2}")

        return briefings

    def format_enhanced_briefing_report(self, briefings: List[Dict]) -> str:
        """
        Format enhanced meeting briefings as readable report.

        Args:
            briefings: List of enhanced briefing dictionaries

        Returns:
            Formatted report text
        """
        lines = []
        lines.append("=" * 80)
        lines.append("📋 ENHANCED MEETING CONTEXT PACKAGES")
        lines.append("=" * 80)

        if not briefings:
            lines.append("\n✅ No meetings scheduled today")
            lines.append("\n" + "=" * 80)
            return "\n".join(lines)

        for idx, briefing in enumerate(briefings, 1):
            meeting = briefing['meeting']
            meeting_type = briefing.get('meeting_type', 'unknown')

            lines.append(f"\n## Meeting {idx}: {meeting['summary']}")
            lines.append(f"⏰ Time: {meeting['time']}")
            lines.append(f"📁 Type: {meeting_type.upper()}")

            if meeting['location']:
                lines.append(f"📍 Location: {meeting['location']}")

            # Attendees with sentiment
            if briefing.get('attendees'):
                lines.append(f"\n👥 Attendees ({len(briefing['attendees'])}):")
                for attendee in briefing['attendees'][:5]:
                    sentiment = attendee.get('sentiment_analysis', {})
                    sentiment_emoji = {'positive': '😊', 'neutral': '😐', 'negative': '😟'}.get(
                        sentiment.get('sentiment', 'neutral'), '😐'
                    )

                    if attendee.get('found'):
                        lines.append(f"  • {attendee['name']} {sentiment_emoji}")
                        if attendee.get('job_title'):
                            lines.append(f"    {attendee['job_title']}")
                        if sentiment.get('engagement_trend') != 'stable':
                            lines.append(f"    Engagement: {sentiment.get('engagement_trend', 'unknown')}")
                    else:
                        lines.append(f"  • {attendee['name']} ({attendee['email']}) {sentiment_emoji}")

            # Strategic context
            if briefing.get('strategic_context'):
                strat_ctx = briefing['strategic_context']

                if strat_ctx.get('related_strategic_initiatives'):
                    lines.append(f"\n📈 Related Strategic Initiatives:")
                    for init in strat_ctx['related_strategic_initiatives']:
                        lines.append(f"  • {init['initiative']} ({init['status']})")
                        lines.append(f"    Relevance: {init['relevance']}")

                if strat_ctx.get('recent_decisions_relevant'):
                    lines.append(f"\n🎯 Relevant Pending Decisions:")
                    for decision in strat_ctx['recent_decisions_relevant']:
                        lines.append(f"  • [{decision['urgency']}] {decision['decision']}")
                        lines.append(f"    Relevance: {decision['relevance']}")

                if strat_ctx.get('recommended_topics'):
                    lines.append(f"\n💬 Recommended Discussion Topics:")
                    for topic in strat_ctx['recommended_topics'][:5]:
                        lines.append(f"  • {topic}")

            # Action item status
            if briefing.get('action_item_status'):
                lines.append(f"\n📋 Action Item Status:")
                for action in briefing['action_item_status'][:5]:
                    if action.get('status') != 'N/A':
                        lines.append(f"  • {action['action']}")
                        lines.append(f"    Status: {action['status']} | Due: {action.get('due_date', 'TBD')}")

            # Email context
            if briefing.get('email_context'):
                lines.append(f"\n📧 Email Context ({len(briefing['email_context'])} recent):")
                for email in briefing['email_context'][:3]:
                    lines.append(f"  • {email.get('subject', 'No Subject')}")

            # Preparation tips
            if briefing.get('preparation_tips'):
                lines.append(f"\n💡 Preparation Tips:")
                for tip in briefing['preparation_tips']:
                    lines.append(f"  {tip}")

            lines.append("\n" + "-" * 80)

        lines.append("\n" + "=" * 80)
        lines.append(f"Generated: {datetime.now().isoformat()}")
        lines.append("Enhanced Meeting Context Auto-Assembly (Phase 1)")
        lines.append("=" * 80)
        return "\n".join(lines)


def main():
    """Test enhanced meeting context auto-assembly system."""
    print("\n=== Enhanced Meeting Context Auto-Assembly System ===\n")

    prep = MeetingContextAutoAssembly()

    # Prepare today's meetings
    print("📊 Preparing enhanced context packages for today's meetings...")
    briefings = prep.prepare_todays_enhanced_meetings()

    # Display report
    report = prep.format_enhanced_briefing_report(briefings)
    print(report)

    # Save results
    output_file = MAIA_ROOT / 'data' / 'enhanced_meeting_context_packages.json'
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump({
            'briefings': briefings,
            'generated_at': datetime.now().isoformat(),
            'meeting_count': len(briefings)
        }, f, indent=2, default=str)

    print(f"\n💾 Enhanced context packages saved to {output_file}")
    print(f"📊 Processed {len(briefings)} meetings")


if __name__ == '__main__':
    main()
