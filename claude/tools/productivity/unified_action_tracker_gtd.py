#!/usr/bin/env python3
"""
Unified Action Tracker - GTD Context System
Enhanced action tracking with Getting Things Done (GTD) context tags.

GTD Contexts Implemented:
- @waiting-for: Items blocked on others (track who, when expected)
- @delegated: Tasks assigned to team members (track assignee, due date, check-in)
- @needs-decision: Items requiring decision before action
- @strategic: Strategic thinking items requiring focus time
- @quick-wins: <15 min tasks for gaps between meetings
- @deep-work: Tasks requiring 2+ hours uninterrupted focus
- @stakeholder-[name]: Items specific to relationship (prep for 1-on-1)

Author: Maia Executive Information Manager Agent
Project: INFO_MGT_001 - Phase 1, Week 2
Date: 2025-10-13
"""

import json
import sys
import os
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
from pathlib import Path

MAIA_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

# Import base unified action tracker
import importlib.util
def import_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

action_tracker_path = MAIA_ROOT / "tools" / "unified_action_tracker.py"
UnifiedActionTracker = import_module_from_path("unified_action_tracker", action_tracker_path).UnifiedActionTracker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UnifiedActionTrackerGTD(UnifiedActionTracker):
    """Enhanced action tracker with GTD context tags"""

    def __init__(self, db_path: str = None):
        """Initialize GTD-enhanced action tracker"""
        super().__init__(db_path)
        self._upgrade_database_for_gtd()

    def _upgrade_database_for_gtd(self):
        """Add GTD context columns to existing database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check if context_tags column exists
        cursor.execute("PRAGMA table_info(action_items)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'context_tags' not in columns:
            logger.info("Upgrading database for GTD contexts...")

            # Add new columns
            cursor.execute('ALTER TABLE action_items ADD COLUMN context_tags TEXT')
            cursor.execute('ALTER TABLE action_items ADD COLUMN waiting_for_person TEXT')
            cursor.execute('ALTER TABLE action_items ADD COLUMN waiting_for_expected_date TEXT')
            cursor.execute('ALTER TABLE action_items ADD COLUMN delegated_to TEXT')
            cursor.execute('ALTER TABLE action_items ADD COLUMN delegated_due_date TEXT')
            cursor.execute('ALTER TABLE action_items ADD COLUMN estimated_duration_minutes INTEGER')
            cursor.execute('ALTER TABLE action_items ADD COLUMN energy_level TEXT')  # high, medium, low
            cursor.execute('ALTER TABLE action_items ADD COLUMN last_reviewed_at TEXT')

            conn.commit()
            logger.info("Database upgraded with GTD context columns")

        conn.close()

    def _auto_classify_context(self, action: Dict) -> List[str]:
        """
        Automatically classify action into GTD contexts.

        Args:
            action: Action item dictionary

        Returns:
            List of context tags (e.g., ['@quick-wins', '@stakeholder-hamish'])
        """
        contexts = []
        title = action.get('title', '').lower()
        description = action.get('description', '').lower()
        owner = action.get('owner', '').lower()
        source = action.get('source', '')

        # @waiting-for detection
        waiting_keywords = ['waiting', 'pending', 'blocked', 'awaiting', 'need from']
        if any(keyword in title or keyword in description for keyword in waiting_keywords):
            contexts.append('@waiting-for')
        elif owner not in ['me', 'you', ''] and owner != 'unknown':
            # If someone else is owner, likely waiting for them
            contexts.append('@waiting-for')

        # @delegated detection
        delegated_keywords = ['assigned to', 'delegated', 'team member', 'ask']
        if any(keyword in title or keyword in description for keyword in delegated_keywords):
            contexts.append('@delegated')

        # @needs-decision detection
        decision_keywords = ['decide', 'decision', 'approve', 'review', 'choice', 'option']
        if any(keyword in title or keyword in description for keyword in decision_keywords):
            contexts.append('@needs-decision')

        # @strategic detection
        strategic_keywords = ['strategic', 'planning', 'roadmap', 'vision', 'okr', 'quarterly', 'long-term']
        if any(keyword in title or keyword in description for keyword in strategic_keywords):
            contexts.append('@strategic')
        elif action.get('priority') == 'strategic':
            contexts.append('@strategic')

        # @quick-wins detection (estimate based on keywords)
        quick_keywords = ['quick', 'brief', 'email', 'confirm', 'check', 'verify', 'send', 'reply']
        if any(keyword in title for keyword in quick_keywords):
            contexts.append('@quick-wins')
            action['estimated_duration_minutes'] = 15

        # @deep-work detection
        deep_keywords = ['design', 'architect', 'analysis', 'write', 'develop', 'plan', 'research']
        if any(keyword in title for keyword in deep_keywords):
            contexts.append('@deep-work')
            action['estimated_duration_minutes'] = 120

        # @stakeholder-[name] detection
        stakeholder_names = ['hamish', 'mariele', 'michael', 'mv', 'trevor']
        for name in stakeholder_names:
            if name in title or name in description:
                contexts.append(f'@stakeholder-{name}')

        # Default to general if no specific context
        if not contexts:
            contexts.append('@general')

        return contexts

    def _estimate_duration(self, action: Dict) -> int:
        """
        Estimate task duration in minutes.

        Returns:
            Duration in minutes (default 30)
        """
        if action.get('estimated_duration_minutes'):
            return action['estimated_duration_minutes']

        title = action.get('title', '').lower()

        # Quick tasks (5-15 min)
        if any(keyword in title for keyword in ['quick', 'brief', 'email', 'confirm', 'check']):
            return 10

        # Deep work (2+ hours)
        if any(keyword in title for keyword in ['design', 'architect', 'analysis', 'develop']):
            return 120

        # Strategic work (1-2 hours)
        if any(keyword in title for keyword in ['strategic', 'planning', 'roadmap']):
            return 90

        # Medium tasks (30-60 min)
        return 30

    def _estimate_energy_level(self, action: Dict) -> str:
        """
        Estimate required energy level.

        Returns:
            'high', 'medium', or 'low'
        """
        title = action.get('title', '').lower()
        contexts = action.get('context_tags', [])

        # High energy tasks
        if '@strategic' in contexts or '@deep-work' in contexts:
            return 'high'
        if any(keyword in title for keyword in ['design', 'architect', 'strategic', 'analysis']):
            return 'high'

        # Low energy tasks
        if '@quick-wins' in contexts:
            return 'low'
        if any(keyword in title for keyword in ['email', 'check', 'verify', 'confirm']):
            return 'low'

        # Medium energy default
        return 'medium'

    def add_action_with_gtd_context(
        self,
        title: str,
        source: str = 'manual',
        description: str = '',
        priority: str = 'medium',
        due_date: str = None,
        owner: str = 'me',
        context_tags: List[str] = None,
        waiting_for_person: str = None,
        waiting_for_expected_date: str = None,
        delegated_to: str = None,
        delegated_due_date: str = None
    ) -> int:
        """
        Add action item with GTD context classification.

        Args:
            title: Action title
            source: Source of action (manual, email, vtt, trello)
            description: Detailed description
            priority: high, medium, low, strategic
            due_date: ISO format date
            owner: Person responsible
            context_tags: Manual context tags (auto-classified if None)
            waiting_for_person: Who we're waiting for
            waiting_for_expected_date: When we expect response
            delegated_to: Who task is delegated to
            delegated_due_date: When delegated task is due

        Returns:
            Action item ID
        """
        action = {
            'title': title,
            'source': source,
            'description': description,
            'priority': priority,
            'due_date': due_date,
            'owner': owner
        }

        # Auto-classify contexts if not provided
        if context_tags is None:
            context_tags = self._auto_classify_context(action)

        # Estimate duration and energy
        estimated_duration = self._estimate_duration(action)
        energy_level = self._estimate_energy_level(action)

        # Save to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        now = datetime.now().isoformat()

        cursor.execute('''
        INSERT INTO action_items
        (source, title, description, owner, due_date, status, priority, created_at, updated_at,
         context_tags, waiting_for_person, waiting_for_expected_date, delegated_to,
         delegated_due_date, estimated_duration_minutes, energy_level, last_reviewed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            source,
            title,
            description,
            owner,
            due_date,
            'pending',
            priority,
            now,
            now,
            json.dumps(context_tags),
            waiting_for_person,
            waiting_for_expected_date,
            delegated_to,
            delegated_due_date,
            estimated_duration,
            energy_level,
            now
        ))

        action_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.info(f"Added action #{action_id}: {title} with contexts: {', '.join(context_tags)}")
        return action_id

    def get_actions_by_context(self, context: str, limit: int = 50) -> List[Dict]:
        """
        Get actions filtered by GTD context.

        Args:
            context: Context tag (e.g., '@waiting-for', '@quick-wins')
            limit: Maximum items to return

        Returns:
            List of action dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
        SELECT * FROM action_items
        WHERE status = 'pending' AND context_tags LIKE ?
        ORDER BY priority DESC, due_date ASC
        LIMIT ?
        ''', (f'%{context}%', limit))

        rows = cursor.fetchall()
        conn.close()

        actions = []
        columns = ['id', 'source', 'source_id', 'title', 'description', 'owner', 'due_date',
                  'status', 'priority', 'created_at', 'updated_at', 'metadata', 'context_tags',
                  'waiting_for_person', 'waiting_for_expected_date', 'delegated_to',
                  'delegated_due_date', 'estimated_duration_minutes', 'energy_level', 'last_reviewed_at']

        for row in rows:
            action = dict(zip(columns[:len(row)], row))
            if action.get('context_tags'):
                action['context_tags'] = json.loads(action['context_tags'])
            actions.append(action)

        return actions

    def get_actions_by_duration(self, min_minutes: int, max_minutes: int) -> List[Dict]:
        """
        Get actions filtered by estimated duration.

        Useful for time-boxing (e.g., "Show me 15-min tasks for gap between meetings")

        Args:
            min_minutes: Minimum duration
            max_minutes: Maximum duration

        Returns:
            List of action dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
        SELECT * FROM action_items
        WHERE status = 'pending'
        AND estimated_duration_minutes >= ?
        AND estimated_duration_minutes <= ?
        ORDER BY priority DESC, due_date ASC
        ''', (min_minutes, max_minutes))

        rows = cursor.fetchall()
        conn.close()

        actions = []
        columns = ['id', 'source', 'source_id', 'title', 'description', 'owner', 'due_date',
                  'status', 'priority', 'created_at', 'updated_at', 'metadata', 'context_tags',
                  'waiting_for_person', 'waiting_for_expected_date', 'delegated_to',
                  'delegated_due_date', 'estimated_duration_minutes', 'energy_level', 'last_reviewed_at']

        for row in rows:
            action = dict(zip(columns[:len(row)], row))
            if action.get('context_tags'):
                action['context_tags'] = json.loads(action['context_tags'])
            actions.append(action)

        return actions

    def get_actions_by_energy(self, energy_level: str) -> List[Dict]:
        """
        Get actions filtered by energy level.

        Useful for matching tasks to current energy state.

        Args:
            energy_level: 'high', 'medium', or 'low'

        Returns:
            List of action dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
        SELECT * FROM action_items
        WHERE status = 'pending' AND energy_level = ?
        ORDER BY priority DESC, due_date ASC
        ''', (energy_level,))

        rows = cursor.fetchall()
        conn.close()

        actions = []
        columns = ['id', 'source', 'source_id', 'title', 'description', 'owner', 'due_date',
                  'status', 'priority', 'created_at', 'updated_at', 'metadata', 'context_tags',
                  'waiting_for_person', 'waiting_for_expected_date', 'delegated_to',
                  'delegated_due_date', 'estimated_duration_minutes', 'energy_level', 'last_reviewed_at']

        for row in rows:
            action = dict(zip(columns[:len(row)], row))
            if action.get('context_tags'):
                action['context_tags'] = json.loads(action['context_tags'])
            actions.append(action)

        return actions

    def get_waiting_for_items(self) -> List[Dict]:
        """
        Get all @waiting-for items with aging analysis.

        Returns:
            List of waiting-for items with days_waiting calculation
        """
        actions = self.get_actions_by_context('@waiting-for')

        now = datetime.now()
        for action in actions:
            created_at = datetime.fromisoformat(action['created_at'])
            days_waiting = (now - created_at).days
            action['days_waiting'] = days_waiting

            # Flag overdue waiting items
            if action.get('waiting_for_expected_date'):
                expected = datetime.fromisoformat(action['waiting_for_expected_date'])
                if now > expected:
                    action['overdue'] = True
                    action['days_overdue'] = (now - expected).days

        # Sort by days waiting (oldest first)
        actions.sort(key=lambda x: x.get('days_waiting', 0), reverse=True)

        return actions

    def generate_gtd_dashboard(self) -> Dict:
        """
        Generate GTD context dashboard with counts and key items.

        Returns:
            Dashboard dictionary with context summaries
        """
        dashboard = {
            'generated_at': datetime.now().isoformat(),
            'contexts': {}
        }

        # All GTD contexts
        contexts = [
            '@waiting-for',
            '@delegated',
            '@needs-decision',
            '@strategic',
            '@quick-wins',
            '@deep-work',
            '@stakeholder-hamish',
            '@stakeholder-mariele',
            '@stakeholder-mv'
        ]

        for context in contexts:
            actions = self.get_actions_by_context(context, limit=10)
            dashboard['contexts'][context] = {
                'count': len(actions),
                'top_items': [
                    {
                        'id': a['id'],
                        'title': a['title'],
                        'priority': a['priority'],
                        'due_date': a.get('due_date'),
                        'estimated_duration': a.get('estimated_duration_minutes')
                    }
                    for a in actions[:5]
                ]
            }

        # Add energy level summary
        dashboard['energy_levels'] = {
            'high': len(self.get_actions_by_energy('high')),
            'medium': len(self.get_actions_by_energy('medium')),
            'low': len(self.get_actions_by_energy('low'))
        }

        # Add duration buckets
        dashboard['duration_buckets'] = {
            'quick_wins_15min': len(self.get_actions_by_duration(0, 15)),
            'short_30min': len(self.get_actions_by_duration(16, 30)),
            'medium_1hr': len(self.get_actions_by_duration(31, 60)),
            'deep_work_2hr_plus': len(self.get_actions_by_duration(61, 999))
        }

        return dashboard

    def format_gtd_dashboard(self, dashboard: Dict) -> str:
        """Format GTD dashboard as readable text"""
        lines = []
        lines.append("=" * 80)
        lines.append("🎯 GTD CONTEXT DASHBOARD")
        lines.append(f"Generated: {dashboard['generated_at']}")
        lines.append("=" * 80)

        # Context summaries
        lines.append("\n📋 CONTEXT SUMMARIES:")
        for context, data in dashboard['contexts'].items():
            count = data['count']
            if count > 0:
                lines.append(f"\n{context}: {count} items")
                for item in data['top_items'][:3]:
                    duration = item.get('estimated_duration')
                    duration_str = f" ({duration}min)" if duration else ""
                    lines.append(f"  • [{item['priority'].upper()}] {item['title']}{duration_str}")

        # Energy levels
        lines.append("\n\n⚡ ENERGY LEVELS:")
        lines.append(f"  High Energy Tasks: {dashboard['energy_levels']['high']}")
        lines.append(f"  Medium Energy Tasks: {dashboard['energy_levels']['medium']}")
        lines.append(f"  Low Energy Tasks: {dashboard['energy_levels']['low']}")

        # Duration buckets
        lines.append("\n\n⏱️ DURATION BUCKETS:")
        lines.append(f"  Quick Wins (≤15 min): {dashboard['duration_buckets']['quick_wins_15min']}")
        lines.append(f"  Short Tasks (16-30 min): {dashboard['duration_buckets']['short_30min']}")
        lines.append(f"  Medium Tasks (31-60 min): {dashboard['duration_buckets']['medium_1hr']}")
        lines.append(f"  Deep Work (60+ min): {dashboard['duration_buckets']['deep_work_2hr_plus']}")

        lines.append("\n" + "=" * 80)
        return "\n".join(lines)


def main():
    """Test GTD-enhanced action tracker"""
    print("\n=== GTD-Enhanced Unified Action Tracker ===\n")

    tracker = UnifiedActionTrackerGTD()

    # Add test actions
    print("📝 Adding test actions with GTD contexts...\n")

    tracker.add_action_with_gtd_context(
        title="Quick check on Intune deployment status",
        description="Verify Lighthouse audit completion",
        priority="high"
    )

    tracker.add_action_with_gtd_context(
        title="Strategic planning for Q1 2026 Azure Extended Zone positioning",
        description="Long-term roadmap development",
        priority="strategic"
    )

    tracker.add_action_with_gtd_context(
        title="Waiting for Mariele subcategory list approval",
        description="Blocked on Mariele's review",
        priority="medium",
        waiting_for_person="Mariele",
        waiting_for_expected_date=(datetime.now() + timedelta(days=2)).isoformat()
    )

    tracker.add_action_with_gtd_context(
        title="Prepare 1-on-1 agenda for Hamish",
        description="Strategic alignment discussion",
        priority="high",
        due_date=(datetime.now() + timedelta(days=1)).isoformat()
    )

    tracker.add_action_with_gtd_context(
        title="Design cloud architecture for new client",
        description="Deep technical design work required",
        priority="high"
    )

    # Generate dashboard
    print("\n📊 Generating GTD dashboard...\n")
    dashboard = tracker.generate_gtd_dashboard()
    print(tracker.format_gtd_dashboard(dashboard))

    # Save dashboard
    output_file = MAIA_ROOT / 'data' / 'gtd_context_dashboard.json'
    with open(output_file, 'w') as f:
        json.dump(dashboard, f, indent=2)

    print(f"\n💾 Dashboard saved to {output_file}")

    # Test context queries
    print("\n\n🔍 CONTEXT QUERY EXAMPLES:\n")

    quick_wins = tracker.get_actions_by_context('@quick-wins')
    print(f"@quick-wins: {len(quick_wins)} items")
    for item in quick_wins:
        print(f"  • {item['title']}")

    waiting = tracker.get_waiting_for_items()
    print(f"\n@waiting-for: {len(waiting)} items")
    for item in waiting[:3]:
        print(f"  • {item['title']} (waiting {item.get('days_waiting', 0)} days)")

    strategic = tracker.get_actions_by_context('@strategic')
    print(f"\n@strategic: {len(strategic)} items")
    for item in strategic:
        print(f"  • {item['title']}")


if __name__ == '__main__':
    main()
