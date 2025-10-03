#!/usr/bin/env python3
"""
Unified Action Item Tracker
Aggregates action items from Email, Meetings (VTT), and Trello with status tracking.

Integrates:
- Email Intelligence (macos_mail_bridge.py) - Email action items
- VTT Summaries (transcript_summaries/) - Meeting action items
- Trello (trello_fast.py) - Task management
- SQLite persistence for cross-session tracking

Author: Maia Personal Assistant Agent
Phase: 85d - Unified Action Item Tracking
Date: 2025-10-03
"""

import json
import sys
import os
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
import glob

sys.path.insert(0, os.path.expanduser('~/git/maia'))

from claude.tools.macos_mail_bridge import MacOSMailBridge
from claude.tools.trello_fast import TrelloFast

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UnifiedActionTracker:
    """Unified action item tracking across all sources."""

    def __init__(self, db_path: str = None):
        """
        Initialize action tracker.

        Args:
            db_path: Path to SQLite database
        """
        if db_path is None:
            db_path = os.path.expanduser('~/.maia/action_items.db')

        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        self.db_path = db_path
        self.mail_bridge = MacOSMailBridge()

        try:
            self.trello = TrelloFast()
        except Exception as e:
            logger.warning(f"Trello not available: {e}")
            self.trello = None

        self._init_database()

    def _init_database(self):
        """Initialize SQLite database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS action_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            source_id TEXT,
            title TEXT NOT NULL,
            description TEXT,
            owner TEXT,
            due_date TEXT,
            status TEXT DEFAULT 'pending',
            priority TEXT DEFAULT 'medium',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            metadata TEXT
        )
        ''')

        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {self.db_path}")

    def extract_email_actions(self, limit: int = 20) -> List[Dict]:
        """
        Extract action items from emails.

        Args:
            limit: Maximum emails to analyze

        Returns:
            List of action item dictionaries
        """
        logger.info("Extracting action items from emails...")

        messages = self.mail_bridge.get_inbox_messages(limit=limit, account="Exchange")

        action_items = []
        action_keywords = ['action', 'todo', 'task', 'please', 'need', 'review', 'approve']

        for msg in messages:
            subject = msg.get('subject', '').lower()

            # Check for action keywords
            if any(keyword in subject for keyword in action_keywords):
                action_items.append({
                    'source': 'email',
                    'source_id': msg.get('id', ''),
                    'title': msg.get('subject', 'No Subject'),
                    'description': f"From: {msg.get('from', 'Unknown')}",
                    'owner': 'me',  # Emails to you = your actions
                    'due_date': None,
                    'priority': 'high' if 'urgent' in subject else 'medium',
                    'metadata': json.dumps({
                        'from': msg.get('from', ''),
                        'date': str(msg.get('date_received', ''))
                    })
                })

        logger.info(f"Extracted {len(action_items)} action items from emails")
        return action_items

    def extract_vtt_actions(self) -> List[Dict]:
        """
        Extract action items from VTT meeting summaries.

        Returns:
            List of action item dictionaries
        """
        logger.info("Extracting action items from VTT summaries...")

        summaries_path = os.path.expanduser('~/git/maia/claude/data/transcript_summaries/*.json')
        summary_files = glob.glob(summaries_path)

        action_items = []

        for file_path in summary_files:
            try:
                with open(file_path, 'r') as f:
                    summary = json.load(f)

                # Extract action items if present
                fob_sections = summary.get('fob_sections', {})

                # Client meetings have deliverables
                deliverables = fob_sections.get('deliverables', [])
                for item in deliverables:
                    if isinstance(item, dict):
                        action_items.append({
                            'source': 'vtt_meeting',
                            'source_id': os.path.basename(file_path),
                            'title': item.get('item', ''),
                            'owner': item.get('owner', 'Unknown'),
                            'due_date': item.get('deadline', None),
                            'priority': 'high',
                            'metadata': json.dumps({
                                'meeting_type': summary.get('meeting_type', ''),
                                'file': os.path.basename(file_path)
                            })
                        })

                # Next steps
                next_steps = fob_sections.get('next_steps', {})
                for category in ['internal', 'client']:
                    steps = next_steps.get(category, [])
                    for step in steps:
                        action_items.append({
                            'source': 'vtt_meeting',
                            'source_id': os.path.basename(file_path),
                            'title': step if isinstance(step, str) else step.get('action', ''),
                            'owner': 'team' if category == 'internal' else 'client',
                            'priority': 'medium',
                            'metadata': json.dumps({
                                'category': category,
                                'meeting_type': summary.get('meeting_type', '')
                            })
                        })

            except Exception as e:
                logger.warning(f"Error processing {file_path}: {e}")

        logger.info(f"Extracted {len(action_items)} action items from VTT summaries")
        return action_items

    def extract_trello_actions(self) -> List[Dict]:
        """
        Extract action items from Trello.

        Returns:
            List of action item dictionaries
        """
        if not self.trello:
            logger.warning("Trello not available")
            return []

        logger.info("Extracting action items from Trello...")

        try:
            boards = self.trello.list_boards()
            action_items = []

            for board in boards:
                lists = self.trello.get_board_lists(board['id'])

                for list_item in lists:
                    # Skip "Done" lists
                    if 'done' in list_item['name'].lower() or 'complete' in list_item['name'].lower():
                        continue

                    cards = self.trello.get_list_cards(list_item['id'])

                    for card in cards:
                        action_items.append({
                            'source': 'trello',
                            'source_id': card['id'],
                            'title': card['name'],
                            'description': card.get('desc', ''),
                            'due_date': card.get('due', None),
                            'priority': 'high' if card.get('due') else 'medium',
                            'metadata': json.dumps({
                                'board': board['name'],
                                'list': list_item['name'],
                                'url': card.get('url', '')
                            })
                        })

            logger.info(f"Extracted {len(action_items)} action items from Trello")
            return action_items

        except Exception as e:
            logger.error(f"Error extracting Trello actions: {e}")
            return []

    def sync_action_items(self):
        """Sync action items from all sources to database."""
        logger.info("Syncing action items from all sources...")

        # Extract from all sources
        email_actions = self.extract_email_actions(limit=20)
        vtt_actions = self.extract_vtt_actions()
        trello_actions = self.extract_trello_actions()

        all_actions = email_actions + vtt_actions + trello_actions

        # Save to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        now = datetime.now().isoformat()

        for action in all_actions:
            # Check if already exists
            cursor.execute(
                'SELECT id FROM action_items WHERE source = ? AND source_id = ?',
                (action['source'], action.get('source_id', ''))
            )

            if cursor.fetchone() is None:
                # Insert new action
                cursor.execute('''
                INSERT INTO action_items
                (source, source_id, title, description, owner, due_date, priority, created_at, updated_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    action['source'],
                    action.get('source_id', ''),
                    action['title'],
                    action.get('description', ''),
                    action.get('owner', ''),
                    action.get('due_date'),
                    action.get('priority', 'medium'),
                    now,
                    now,
                    action.get('metadata', '{}')
                ))

        conn.commit()
        conn.close()

        logger.info(f"Synced {len(all_actions)} action items to database")

    def get_pending_actions(self, limit: int = 20) -> List[Dict]:
        """
        Get pending action items.

        Args:
            limit: Maximum items to return

        Returns:
            List of pending action dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
        SELECT * FROM action_items
        WHERE status = 'pending'
        ORDER BY
            CASE priority
                WHEN 'high' THEN 1
                WHEN 'medium' THEN 2
                WHEN 'low' THEN 3
            END,
            created_at DESC
        LIMIT ?
        ''', (limit,))

        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()

        actions = []
        for row in rows:
            actions.append(dict(zip(columns, row)))

        conn.close()
        return actions

    def who_waiting_on_me(self) -> List[Dict]:
        """
        Get action items where others are waiting on me.

        Returns:
            List of action dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
        SELECT * FROM action_items
        WHERE status = 'pending' AND owner = 'me'
        ORDER BY created_at ASC
        ''')

        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()

        actions = []
        for row in rows:
            actions.append(dict(zip(columns, row)))

        conn.close()
        return actions

    def format_action_report(self, actions: List[Dict], title: str = "Action Items") -> str:
        """
        Format action items as readable report.

        Args:
            actions: List of action dictionaries
            title: Report title

        Returns:
            Formatted report
        """
        lines = []
        lines.append("=" * 70)
        lines.append(f"📋 {title.upper()}")
        lines.append("=" * 70)

        if not actions:
            lines.append("\n✅ No pending action items")
            lines.append("\n" + "=" * 70)
            return "\n".join(lines)

        # Group by source
        by_source = {}
        for action in actions:
            source = action['source']
            if source not in by_source:
                by_source[source] = []
            by_source[source].append(action)

        for source, items in by_source.items():
            lines.append(f"\n## {source.upper()} ({len(items)} items)")
            lines.append("-" * 70)

            for action in items:
                priority_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(action['priority'], '⚪')

                lines.append(f"\n{priority_emoji} {action['title']}")

                if action.get('owner'):
                    lines.append(f"   Owner: {action['owner']}")

                if action.get('due_date'):
                    lines.append(f"   Due: {action['due_date']}")

                if action.get('description'):
                    lines.append(f"   {action['description'][:100]}")

        lines.append("\n" + "=" * 70)
        return "\n".join(lines)


def main():
    """Test unified action tracker."""
    print("\n=== Unified Action Item Tracker ===\n")

    tracker = UnifiedActionTracker()

    # Sync all sources
    print("📊 Syncing action items from all sources...")
    tracker.sync_action_items()

    # Get pending actions
    print("\n📋 Pending Action Items:")
    pending = tracker.get_pending_actions(limit=20)
    print(tracker.format_action_report(pending, "Pending Actions"))

    # Who's waiting on me
    print("\n⏰ Who's Waiting On Me:")
    waiting = tracker.who_waiting_on_me()
    print(tracker.format_action_report(waiting, "Waiting On Me"))

    # Save to file
    output_file = '/Users/naythandawe/git/maia/claude/data/action_items_report.json'
    with open(output_file, 'w') as f:
        json.dump({
            'pending': pending,
            'waiting_on_me': waiting,
            'generated_at': datetime.now().isoformat()
        }, f, indent=2, default=str)

    print(f"\n💾 Report saved to {output_file}")


if __name__ == '__main__':
    main()
