#!/usr/bin/env python3
"""
Weekly Strategic Review Automation
Guided GTD-style weekly review with data aggregation from all sources.

6-Stage Review Process:
1. Clear Your Head (5 min) - Brain dump, calendar review
2. Review Projects (20 min) - 116 strategic initiatives summary
3. Review Waiting-For (10 min) - @waiting-for aging analysis
4. Review Goals/Horizons (20 min) - Quarterly OKR progress, role alignment
5. Review Stakeholders (15 min) - Relationship health, upcoming 1-on-1s
6. Plan Next Week (20 min) - Top 3-5 priorities, focus time blocks

Author: Maia Executive Information Manager Agent
Project: INFO_MGT_001 - Phase 1, Week 3
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

# Import dependencies
import importlib.util
def import_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Import GTD action tracker
gtd_tracker_path = MAIA_ROOT / "extensions" / "experimental" / "unified_action_tracker_gtd.py"
UnifiedActionTrackerGTD = import_module_from_path("unified_action_tracker_gtd", gtd_tracker_path).UnifiedActionTrackerGTD

# Import intelligence processors
conf_intel_path = MAIA_ROOT / "tools" / "confluence_intelligence_processor.py"
ConfluenceIntelligenceProcessor = import_module_from_path("confluence_intelligence_processor", conf_intel_path).ConfluenceIntelligenceProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WeeklyStrategicReview:
    """GTD-based weekly review system"""

    def __init__(self):
        """Initialize weekly review system"""
        self.action_tracker = UnifiedActionTrackerGTD()
        self.confluence_intel = ConfluenceIntelligenceProcessor()
        self.review_date = datetime.now()

    def generate_review_document(self) -> Dict:
        """
        Generate pre-populated weekly review document.

        Returns:
            Complete review document dictionary
        """
        logger.info("Generating weekly strategic review...")

        review = {
            'review_date': self.review_date.isoformat(),
            'review_week': f"Week of {self.review_date.strftime('%B %d, %Y')}",
            'sections': {}
        }

        # Section 1: Clear Your Head
        review['sections']['clear_head'] = self._section_clear_head()

        # Section 2: Review Projects
        review['sections']['review_projects'] = self._section_review_projects()

        # Section 3: Review Waiting-For
        review['sections']['review_waiting_for'] = self._section_review_waiting_for()

        # Section 4: Review Goals/Horizons
        review['sections']['review_goals'] = self._section_review_goals()

        # Section 5: Review Stakeholders
        review['sections']['review_stakeholders'] = self._section_review_stakeholders()

        # Section 6: Plan Next Week
        review['sections']['plan_next_week'] = self._section_plan_next_week()

        return review

    def _section_clear_head(self) -> Dict:
        """
        Section 1: Clear Your Head (5 min)

        Returns:
            Clear head section data
        """
        section = {
            'duration_minutes': 5,
            'instructions': [
                'Write down any thoughts, concerns, or random items on your mind',
                'Review last week\'s calendar - anything incomplete or needing follow-up?',
                'Review next week\'s calendar - any prep needed?'
            ],
            'brain_dump_prompts': [
                'What\'s been bothering you this week?',
                'Any incomplete conversations or commitments?',
                'What are you worried about?',
                'Any ideas or opportunities to capture?'
            ],
            'calendar_review': {
                'last_week': 'Review past 7 days for incomplete items',
                'next_week': 'Preview upcoming 7 days for preparation needs'
            }
        }

        return section

    def _section_review_projects(self) -> Dict:
        """
        Section 2: Review Projects (20 min)

        Returns:
            Projects review section data
        """
        # Get strategic initiatives from Confluence
        strategic_initiatives = self.confluence_intel.intelligence.get('strategic_initiatives', [])

        # Categorize by status
        active_projects = []
        stuck_projects = []
        completed_recent = []

        for initiative in strategic_initiatives[:20]:  # Top 20
            status = 'active'  # Would parse from initiative data in production
            project = {
                'initiative': initiative.get('initiative', ''),
                'status': status,
                'last_update': 'Recent',  # Would parse from metadata
                'next_action': 'TBD'  # Would determine from action tracker
            }

            if status == 'active':
                active_projects.append(project)
            elif status == 'stuck':
                stuck_projects.append(project)

        section = {
            'duration_minutes': 20,
            'total_initiatives': len(strategic_initiatives),
            'active_projects': active_projects[:10],
            'stuck_projects': stuck_projects,
            'completed_recent': completed_recent,
            'review_questions': [
                'Does each project have a clear next action?',
                'Are any projects stuck or blocked?',
                'Should any projects be cancelled or put on hold?',
                'Are priorities still aligned with strategic goals?'
            ],
            'action_required': [
                f'Review {len(strategic_initiatives)} strategic initiatives',
                'Identify stuck projects requiring intervention',
                'Celebrate completed milestones'
            ]
        }

        return section

    def _section_review_waiting_for(self) -> Dict:
        """
        Section 3: Review Waiting-For (10 min)

        Returns:
            Waiting-for review section data
        """
        waiting_items = self.action_tracker.get_waiting_for_items()

        # Categorize by aging
        overdue_items = [w for w in waiting_items if w.get('overdue', False)]
        aging_items = [w for w in waiting_items if w.get('days_waiting', 0) > 7 and not w.get('overdue', False)]
        recent_items = [w for w in waiting_items if w.get('days_waiting', 0) <= 7]

        section = {
            'duration_minutes': 10,
            'total_waiting': len(waiting_items),
            'overdue_items': [
                {
                    'title': w['title'],
                    'waiting_for': w.get('waiting_for_person', 'Unknown'),
                    'expected_date': w.get('waiting_for_expected_date', 'Not set'),
                    'days_overdue': w.get('days_overdue', 0),
                    'action': f'Follow up with {w.get("waiting_for_person", "Unknown")}'
                }
                for w in overdue_items
            ],
            'aging_items': [
                {
                    'title': w['title'],
                    'waiting_for': w.get('waiting_for_person', 'Unknown'),
                    'days_waiting': w.get('days_waiting', 0),
                    'action': 'Consider follow-up'
                }
                for w in aging_items
            ],
            'recent_items': len(recent_items),
            'review_questions': [
                'Which items are overdue and need immediate follow-up?',
                'Which items have been waiting too long (>2 weeks)?',
                'Should any items be escalated or reassigned?',
                'Are waiting dates realistic?'
            ],
            'follow_up_recommendations': [
                f'Follow up on {len(overdue_items)} overdue items immediately',
                f'Review {len(aging_items)} aging items (>7 days) for proactive follow-up',
                'Update expected dates for ambiguous items'
            ]
        }

        return section

    def _section_review_goals(self) -> Dict:
        """
        Section 4: Review Goals/Horizons (20 min)

        Returns:
            Goals and horizons review section data
        """
        section = {
            'duration_minutes': 20,
            'current_quarter': 'Q4 2025',
            'okr_progress': {
                'initiatives_tracked': 116,
                'key_metrics': [
                    {'metric': 'Team Engagement', 'baseline': '30%', 'current': '60%', 'target': '70%', 'progress': '75%'},
                    {'metric': 'Strategic Initiatives', 'baseline': '0', 'current': '116', 'target': '100', 'progress': '116%'},
                    {'metric': 'Cloud Practice Growth', 'baseline': 'TBD', 'current': 'In Progress', 'target': '20% YoY', 'progress': 'TBD'}
                ]
            },
            'role_responsibilities': [
                {
                    'area': 'Team Management',
                    'alignment': 'Strong',
                    'notes': 'Engagement improving, new starter onboarding in progress'
                },
                {
                    'area': 'Client Relationships',
                    'alignment': 'Good',
                    'notes': 'Regular touchpoints with key accounts, need more strategic discussions'
                },
                {
                    'area': 'Technical Strategy',
                    'alignment': 'Needs attention',
                    'notes': 'Azure Extended Zone positioning, M365 optimization opportunities'
                },
                {
                    'area': 'Budget & Resource Management',
                    'alignment': 'Good',
                    'notes': 'Confluence budget decision pending'
                }
            ],
            'review_questions': [
                'Am I making progress on quarterly goals?',
                'Is my time allocation aligned with role priorities?',
                'Are there any role responsibilities being neglected?',
                'What adjustments needed for next quarter?'
            ],
            'horizon_review': {
                '10000_ft': 'Current projects and initiatives (116 active)',
                '20000_ft': 'Areas of responsibility (team, clients, technical strategy, budget)',
                '30000_ft': '1-2 year goals (cloud practice growth, Azure Extended Zone positioning)',
                '40000_ft': '3-5 year vision (engineering leadership, technical expertise)',
                '50000_ft': 'Life purpose and values (human-first technology, systems thinking)'
            }
        }

        return section

    def _section_review_stakeholders(self) -> Dict:
        """
        Section 5: Review Stakeholders (15 min)

        Returns:
            Stakeholder review section data
        """
        # Known stakeholders from briefing data
        stakeholders = [
            {
                'name': 'Hamish',
                'role': 'Leadership',
                'last_contact': 'This week',
                'cadence': 'Weekly',
                'health': 'Good',
                'next_touchpoint': 'Executive sync - next week',
                'topics_for_next': ['Strategic alignment', 'Q4 progress', 'Resource needs']
            },
            {
                'name': 'Mariele',
                'role': 'Key Collaborator',
                'last_contact': 'Recent meeting',
                'cadence': 'As needed',
                'health': 'Good',
                'next_touchpoint': 'Follow up on subcategory list',
                'topics_for_next': ['Customer spreadsheet update', 'Project coordination']
            },
            {
                'name': 'MV (Michael Villaflor)',
                'role': 'Key Collaborator',
                'last_contact': 'This week',
                'cadence': 'Regular',
                'health': 'Strong',
                'next_touchpoint': 'Ongoing project collaboration',
                'topics_for_next': ['Project status', 'Technical decisions']
            },
            {
                'name': 'Trevor',
                'role': 'New Starter - Wintel Engineer',
                'last_contact': 'Not started yet',
                'cadence': 'Daily (first 2 weeks)',
                'health': 'New',
                'next_touchpoint': 'First day onboarding - next week',
                'topics_for_next': ['Onboarding plan', 'Initial projects', 'Team introductions']
            }
        ]

        # Categorize by health
        requiring_attention = [s for s in stakeholders if s['health'] in ['At risk', 'New']]
        healthy = [s for s in stakeholders if s['health'] in ['Strong', 'Good']]

        section = {
            'duration_minutes': 15,
            'stakeholders': stakeholders,
            'requiring_attention': requiring_attention,
            'healthy_relationships': len(healthy),
            'upcoming_1on1s': [
                {'stakeholder': 'Hamish', 'date': 'Next week', 'prep_needed': True},
                {'stakeholder': 'Trevor', 'date': 'Next week (first day)', 'prep_needed': True}
            ],
            'review_questions': [
                'Have I been in touch with all key stakeholders recently?',
                'Are any relationships showing signs of strain?',
                'Do I have 1-on-1 prep done for upcoming meetings?',
                'Are there opportunities for stronger collaboration?'
            ],
            'engagement_recommendations': [
                'Schedule 1-on-1 with Hamish for strategic alignment',
                'Prepare Trevor\'s onboarding plan',
                'Follow up with Mariele on subcategory list',
                'Maintain regular touchpoints with MV'
            ]
        }

        return section

    def _section_plan_next_week(self) -> Dict:
        """
        Section 6: Plan Next Week (20 min)

        Returns:
            Next week planning section data
        """
        # Get top priorities from action tracker
        strategic_actions = self.action_tracker.get_actions_by_context('@strategic', limit=10)
        quick_wins = self.action_tracker.get_actions_by_context('@quick-wins', limit=10)

        # Top 3-5 strategic priorities
        top_priorities = [
            {
                'priority': a['title'],
                'context': a.get('context_tags', []),
                'estimated_duration': a.get('estimated_duration_minutes', 30),
                'energy_level': a.get('energy_level', 'medium')
            }
            for a in strategic_actions[:5]
        ]

        section = {
            'duration_minutes': 20,
            'top_priorities': top_priorities,
            'focus_time_blocks': [
                {
                    'day': 'Tuesday',
                    'time': '9:00-11:00 AM',
                    'type': 'Deep Work',
                    'suggested_task': 'Strategic planning or architecture design'
                },
                {
                    'day': 'Thursday',
                    'time': '2:00-4:00 PM',
                    'type': 'Strategic Thinking',
                    'suggested_task': 'Team development or process improvement'
                },
                {
                    'day': 'Friday',
                    'time': '3:00-5:00 PM',
                    'type': 'Batch Processing',
                    'suggested_task': 'Email cleanup, low-priority reviews, weekly review'
                }
            ],
            'batch_processing_windows': [
                'Friday afternoon: Email cleanup and low-priority items',
                'Wednesday: Batch all 1-on-1s for efficiency'
            ],
            'meeting_optimization': [
                'Decline non-essential meetings to protect focus time',
                'Suggest async updates for recurring status meetings',
                'Block calendar around focus blocks to prevent encroachment'
            ],
            'planning_questions': [
                'What are my top 3-5 outcomes for next week?',
                'Do I have sufficient focus time blocked?',
                'Are my priorities aligned with quarterly goals?',
                'What can I delegate or defer?'
            ],
            'weekly_intentions': {
                'strategic_work': '50% of time (vs 20% baseline)',
                'team_management': '30% of time',
                'client_engagement': '15% of time',
                'admin_operational': '5% of time'
            }
        }

        return section

    def format_review_document(self, review: Dict) -> str:
        """
        Format weekly review as readable document.

        Args:
            review: Review document dictionary

        Returns:
            Formatted review text
        """
        lines = []
        lines.append("=" * 80)
        lines.append(f"📅 WEEKLY STRATEGIC REVIEW - {review['review_week']}")
        lines.append(f"Generated: {review['review_date']}")
        lines.append("=" * 80)

        # Section 1: Clear Your Head
        clear_head = review['sections']['clear_head']
        lines.append(f"\n## 1️⃣  CLEAR YOUR HEAD ({clear_head['duration_minutes']} min)")
        lines.append("\nInstructions:")
        for instruction in clear_head['instructions']:
            lines.append(f"  • {instruction}")
        lines.append("\nBrain Dump Prompts:")
        for prompt in clear_head['brain_dump_prompts']:
            lines.append(f"  • {prompt}")

        # Section 2: Review Projects
        projects = review['sections']['review_projects']
        lines.append(f"\n\n## 2️⃣  REVIEW PROJECTS ({projects['duration_minutes']} min)")
        lines.append(f"\nTotal Initiatives: {projects['total_initiatives']}")
        lines.append(f"\nActive Projects ({len(projects['active_projects'])}):")
        for proj in projects['active_projects'][:5]:
            lines.append(f"  • {proj['initiative']}")
        if projects['stuck_projects']:
            lines.append(f"\n⚠️  Stuck Projects ({len(projects['stuck_projects'])}):")
            for proj in projects['stuck_projects']:
                lines.append(f"  • {proj['initiative']}")
        lines.append("\nReview Questions:")
        for question in projects['review_questions']:
            lines.append(f"  • {question}")

        # Section 3: Review Waiting-For
        waiting = review['sections']['review_waiting_for']
        lines.append(f"\n\n## 3️⃣  REVIEW WAITING-FOR ({waiting['duration_minutes']} min)")
        lines.append(f"\nTotal Waiting Items: {waiting['total_waiting']}")
        if waiting['overdue_items']:
            lines.append(f"\n🔴 Overdue Items ({len(waiting['overdue_items'])}) - FOLLOW UP IMMEDIATELY:")
            for item in waiting['overdue_items']:
                lines.append(f"  • {item['title']}")
                lines.append(f"    Waiting for: {item['waiting_for']} | {item['days_overdue']} days overdue")
                lines.append(f"    Action: {item['action']}")
        if waiting['aging_items']:
            lines.append(f"\n⚠️  Aging Items ({len(waiting['aging_items'])}) - Consider Follow-up:")
            for item in waiting['aging_items'][:5]:
                lines.append(f"  • {item['title']} ({item['days_waiting']} days waiting)")

        # Section 4: Review Goals
        goals = review['sections']['review_goals']
        lines.append(f"\n\n## 4️⃣  REVIEW GOALS/HORIZONS ({goals['duration_minutes']} min)")
        lines.append(f"\nQuarter: {goals['current_quarter']}")
        lines.append(f"Initiatives Tracked: {goals['okr_progress']['initiatives_tracked']}")
        lines.append("\nKey Metrics:")
        for metric in goals['okr_progress']['key_metrics']:
            lines.append(f"  • {metric['metric']}: {metric['baseline']} → {metric['current']} (Target: {metric['target']}, Progress: {metric['progress']})")
        lines.append("\nRole Alignment:")
        for area in goals['role_responsibilities']:
            lines.append(f"  • {area['area']}: {area['alignment']} - {area['notes']}")

        # Section 5: Review Stakeholders
        stakeholders = review['sections']['review_stakeholders']
        lines.append(f"\n\n## 5️⃣  REVIEW STAKEHOLDERS ({stakeholders['duration_minutes']} min)")
        lines.append(f"\nKey Relationships: {len(stakeholders['stakeholders'])}")
        if stakeholders['requiring_attention']:
            lines.append(f"\n⚠️  Requiring Attention ({len(stakeholders['requiring_attention'])}):")
            for sh in stakeholders['requiring_attention']:
                lines.append(f"  • {sh['name']} ({sh['role']})")
                lines.append(f"    Next: {sh['next_touchpoint']}")
        lines.append(f"\n✅ Healthy Relationships: {stakeholders['healthy_relationships']}")
        if stakeholders['upcoming_1on1s']:
            lines.append("\nUpcoming 1-on-1s:")
            for meeting in stakeholders['upcoming_1on1s']:
                prep = 'PREP NEEDED' if meeting['prep_needed'] else 'Ready'
                lines.append(f"  • {meeting['stakeholder']} - {meeting['date']} ({prep})")

        # Section 6: Plan Next Week
        plan = review['sections']['plan_next_week']
        lines.append(f"\n\n## 6️⃣  PLAN NEXT WEEK ({plan['duration_minutes']} min)")
        lines.append(f"\nTop 3-5 Strategic Priorities:")
        for i, priority in enumerate(plan['top_priorities'][:5], 1):
            duration = priority['estimated_duration']
            energy = priority['energy_level']
            lines.append(f"  {i}. {priority['priority']} ({duration} min, {energy} energy)")
        lines.append(f"\nFocus Time Blocks:")
        for block in plan['focus_time_blocks']:
            lines.append(f"  • {block['day']} {block['time']} - {block['type']}: {block['suggested_task']}")
        lines.append(f"\nWeekly Time Allocation Intentions:")
        for area, allocation in plan['weekly_intentions'].items():
            lines.append(f"  • {area.replace('_', ' ').title()}: {allocation}")

        lines.append("\n" + "=" * 80)
        lines.append("✅ Review Complete - Execute priorities with focus and intention")
        lines.append("=" * 80)

        return "\n".join(lines)


def main():
    """Execute weekly strategic review"""
    print("\n=== Weekly Strategic Review System ===\n")

    reviewer = WeeklyStrategicReview()

    print("📊 Generating weekly strategic review...")
    review_doc = reviewer.generate_review_document()

    # Display formatted review
    formatted = reviewer.format_review_document(review_doc)
    print(formatted)

    # Save review
    output_file = MAIA_ROOT / 'data' / 'weekly_strategic_review.json'
    with open(output_file, 'w') as f:
        json.dump(review_doc, f, indent=2, default=str)

    print(f"\n💾 Review saved to {output_file}")

    # Also save formatted text version
    text_file = MAIA_ROOT / 'data' / 'weekly_strategic_review.txt'
    with open(text_file, 'w') as f:
        f.write(formatted)

    print(f"📄 Formatted review saved to {text_file}")


if __name__ == '__main__':
    main()
