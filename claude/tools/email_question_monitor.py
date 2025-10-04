#!/usr/bin/env python3
"""
Email Question Monitor - Detect unanswered questions and create Trello cards
"""

import sys
import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import subprocess

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from email_rag_ollama import EmailRAGOllama
from trello_fast import TrelloFast


class EmailQuestionMonitor:
    def __init__(self):
        self.rag = EmailRAGOllama()
        self.trello = TrelloFast()
        self.state_file = Path.home() / ".maia" / "email_questions_state.json"
        self.state = self._load_state()

    def _load_state(self) -> Dict:
        """Load tracking state"""
        if self.state_file.exists():
            with open(self.state_file) as f:
                return json.load(f)
        return {
            "processed_message_ids": [],
            "created_cards": {},
            "last_check": None
        }

    def _save_state(self):
        """Save tracking state"""
        self.state_file.parent.mkdir(exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)

    def _has_question_markers(self, text: str) -> bool:
        """Check if text contains question markers"""
        question_patterns = [
            r'\?',  # Question mark
            r'\bcan you\b',
            r'\bcould you\b',
            r'\bwould you\b',
            r'\bwill you\b',
            r'\bplease\s+(advise|confirm|review|provide|send|check)',
            r'\bneed\s+your\s+(input|feedback|thoughts|approval|response)',
            r'\bwaiting\s+for\s+your',
            r'\blet\s+me\s+know',
            r'\bwhat\s+do\s+you\s+think',
            r'\byour\s+thoughts\s+on',
            r'\bdo\s+you\s+(have|know|think)',
        ]

        text_lower = text.lower()
        for pattern in question_patterns:
            if re.search(pattern, text_lower):
                return True
        return False

    def _is_automated_email(self, sender: str, subject: str) -> bool:
        """Check if email is automated/notification"""
        automated_keywords = [
            'noreply', 'no-reply', 'donotreply', 'automated',
            'notification', 'alert', 'automatic reply',
            'out of office', 'teams@', 'calendar@',
            'accepted:', 'declined:', 'tentative:',
            'you have been added', 'you\'ve joined',
            'new post from', 'bitdefender', 'atlassian',
            'service automation', 'internalsupport@'
        ]

        combined = f"{sender} {subject}".lower()
        return any(keyword in combined for keyword in automated_keywords)

    def _check_if_responded(self, email_date: str, sender: str) -> bool:
        """
        Check if we've sent an email to this sender after receiving their email.
        This is a heuristic - searches for emails TO the sender after the question date.
        """
        # Search for emails to this sender
        sender_email = sender.split('<')[-1].replace('>', '').strip()

        # Query for recent sent emails (this is approximate since we index inbox)
        # In a full implementation, you'd also index sent items
        # For now, we'll use a conservative approach and flag if uncertain

        return False  # Conservative: assume not responded unless we have proof

    def detect_unanswered_questions(self, days_back: int = 7) -> List[Dict]:
        """Detect emails with questions that haven't been answered"""

        # Get recent emails
        recent_emails = self.rag.get_recent_emails(n=100)

        unanswered = []
        cutoff_date = datetime.now() - timedelta(days=days_back)

        for email in recent_emails:
            message_id = email.get('message_id', '')
            subject = email.get('subject', '')
            sender = email.get('sender', '')
            date_str = email.get('date', '')
            preview = email.get('preview', '')

            # Skip if already processed
            if message_id in self.state['processed_message_ids']:
                continue

            # Skip automated emails
            if self._is_automated_email(sender, subject):
                self.state['processed_message_ids'].append(message_id)
                continue

            # Parse date
            try:
                # Extract date from format like "Friday, 3 October 2025 at 6:27:25 pm"
                # This is simplified - you may need more robust parsing
                email_date = datetime.now()  # Placeholder
            except:
                email_date = datetime.now()

            # Skip if too old
            if email_date < cutoff_date:
                continue

            # Check for question markers
            full_text = f"{subject} {preview}"
            if self._has_question_markers(full_text):
                # Check if we've responded
                if not self._check_if_responded(date_str, sender):
                    unanswered.append({
                        'message_id': message_id,
                        'subject': subject,
                        'sender': sender,
                        'date': date_str,
                        'preview': preview[:300],
                        'has_question': True
                    })

        return unanswered

    def create_trello_cards(self, questions: List[Dict], board_id: str, list_name: str = "Naythan") -> Dict:
        """Create Trello cards for unanswered questions"""

        results = {
            'created': 0,
            'skipped': 0,
            'errors': []
        }

        # Get board lists
        lists = self.trello.get_lists(board_id)
        target_list = None
        for lst in lists:
            if lst['name'].lower() == list_name.lower():
                target_list = lst
                break

        if not target_list:
            results['errors'].append(f"List '{list_name}' not found")
            return results

        for question in questions:
            message_id = question['message_id']

            # Skip if already created card
            if message_id in self.state['created_cards']:
                results['skipped'] += 1
                continue

            # Create card
            sender_name = question['sender'].split('<')[0].strip()
            if '|' in sender_name:
                sender_name = sender_name.split('|')[0].strip()

            card_name = f"📧 Reply to {sender_name}: {question['subject'][:60]}"

            card_desc = f"""**From**: {question['sender']}
**Date**: {question['date']}
**Subject**: {question['subject']}

**Preview**:
{question['preview']}

---
📧 **Action Required**: This email contains a question that needs a response.

**Message ID**: `{message_id}`
"""

            try:
                card = self.trello.create_card(
                    list_id=target_list['id'],
                    name=card_name,
                    desc=card_desc,
                    pos='top'  # Add to top of list
                )

                # Track that we created a card
                self.state['created_cards'][message_id] = {
                    'card_id': card['id'],
                    'created_at': datetime.now().isoformat()
                }
                self.state['processed_message_ids'].append(message_id)

                results['created'] += 1
                print(f"✅ Created card: {card_name[:70]}...")

            except Exception as e:
                results['errors'].append(f"Failed to create card for {sender_name}: {e}")
                print(f"❌ Error: {e}")

        return results

    def run_check(self, board_id: str, list_name: str = "Naythan", days_back: int = 7):
        """Run full check and create cards"""
        print(f"🔍 Checking for unanswered questions in last {days_back} days...\n")

        # Detect questions
        questions = self.detect_unanswered_questions(days_back=days_back)

        if not questions:
            print("✅ No unanswered questions found!")
            self.state['last_check'] = datetime.now().isoformat()
            self._save_state()
            return

        print(f"📧 Found {len(questions)} potential unanswered questions\n")

        # Create Trello cards
        results = self.create_trello_cards(questions, board_id, list_name)

        print(f"\n📊 Results:")
        print(f"  • Created: {results['created']} cards")
        print(f"  • Skipped: {results['skipped']} (already tracked)")

        if results['errors']:
            print(f"  • Errors: {len(results['errors'])}")
            for error in results['errors']:
                print(f"    - {error}")

        self.state['last_check'] = datetime.now().isoformat()
        self._save_state()

        print(f"\n✅ Check complete!")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Monitor emails for unanswered questions")
    parser.add_argument('--board-id', type=str, help='Trello board ID')
    parser.add_argument('--list', type=str, default='Naythan', help='Target list name (default: Naythan)')
    parser.add_argument('--days', type=int, default=7, help='Days to look back (default: 7)')

    args = parser.parse_args()

    # Get board ID from Trello if not provided
    if not args.board_id:
        trello = TrelloFast()
        everything = trello.get_everything()
        boards = everything.get('boards', [])

        print("Available boards:")
        for board in boards:
            print(f"  • {board['name']}: {board['id']}")

        # Use "Naythan's Personal Board" if available
        for board in boards:
            if 'personal' in board['name'].lower():
                args.board_id = board['id']
                print(f"\nUsing board: {board['name']}")
                break

        if not args.board_id and boards:
            # Use first board as default
            args.board_id = boards[0]['id']
            print(f"\nUsing board: {boards[0]['name']}")
        elif not args.board_id:
            print("\nPlease specify --board-id")
            sys.exit(1)

    monitor = EmailQuestionMonitor()
    monitor.run_check(
        board_id=args.board_id,
        list_name=args.list,
        days_back=args.days
    )


if __name__ == '__main__':
    main()
