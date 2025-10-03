#!/usr/bin/env python3
"""
VTT to Trello Integration
Automatically creates Trello cards from VTT meeting action items

Author: Maia Personal Assistant Agent
Phase: 86.2 - VTT Intelligence Pipeline
Date: 2025-10-03
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Optional
import logging

MAIA_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

from claude.tools.vtt_intelligence_processor import VTTIntelligenceProcessor
from claude.tools.trello_fast import TrelloFast

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VTTTrelloIntegration:
    """Integrate VTT intelligence with Trello"""

    def __init__(self, default_board: str = None, default_list: str = None):
        """
        Initialize integration

        Args:
            default_board: Default Trello board name/ID
            default_list: Default list name for action items
        """
        self.intelligence = VTTIntelligenceProcessor()
        self.trello = TrelloFast()
        self.default_board = default_board
        self.default_list = default_list or "Action Items"

    def create_cards_for_owner(self, owner: str, board_id: str = None, list_id: str = None) -> Dict:
        """
        Create Trello cards for all pending actions for owner

        Args:
            owner: Owner name to filter actions
            board_id: Target board ID (optional if default set)
            list_id: Target list ID (optional if default set)

        Returns:
            Results summary
        """
        # Get action items
        cards_data = self.intelligence.export_for_trello(owner)

        if not cards_data:
            logger.info(f"No pending actions for {owner}")
            return {"created": 0, "skipped": 0, "errors": 0}

        # Determine target list
        if not list_id:
            if not board_id and not self.default_board:
                raise ValueError("Board ID required")

            target_board = board_id or self.default_board
            lists = self.trello.get_lists(target_board)

            # Find action items list
            action_list = next((l for l in lists if self.default_list.lower() in l['name'].lower()), None)

            if not action_list:
                raise ValueError(f"List '{self.default_list}' not found in board")

            list_id = action_list['id']

        # Create cards
        results = {"created": 0, "skipped": 0, "errors": 0, "cards": []}

        for card_data in cards_data:
            try:
                # Check if card already exists (avoid duplicates)
                existing_cards = self.trello.get_cards_on_list(list_id)
                if any(card_data['name'] in c['name'] for c in existing_cards):
                    logger.info(f"Skipping duplicate: {card_data['name'][:50]}...")
                    results["skipped"] += 1
                    continue

                # Create card
                card = self.trello.create_card(
                    list_id=list_id,
                    name=card_data['name'],
                    desc=card_data['desc'],
                    due=card_data.get('due')
                )

                logger.info(f"✅ Created card: {card_data['name'][:50]}...")
                results["created"] += 1
                results["cards"].append(card)

            except Exception as e:
                logger.error(f"Failed to create card: {e}")
                results["errors"] += 1

        return results

    def sync_all_meetings_to_trello(self, owner: str, board_id: str = None) -> Dict:
        """
        Sync all unsynced meeting action items to Trello

        Args:
            owner: Owner to filter by
            board_id: Target board

        Returns:
            Sync results
        """
        return self.create_cards_for_owner(owner, board_id)


def main():
    """CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(description="VTT to Trello Integration")
    parser.add_argument("command", choices=["sync", "list-boards"],
                       help="Command to execute")
    parser.add_argument("--owner", default="Naythan", help="Owner name for filtering")
    parser.add_argument("--board", help="Board ID or name")
    parser.add_argument("--list", default="Action Items", help="List name for cards")

    args = parser.parse_args()

    integration = VTTTrelloIntegration(default_list=args.list)

    if args.command == "list-boards":
        boards = integration.trello.list_boards()
        print("\n📋 Available Boards:")
        for board in boards:
            print(f"  • {board['name']} (ID: {board['id']})")

    elif args.command == "sync":
        if not args.board:
            print("❌ Error: --board required for sync")
            sys.exit(1)

        print(f"\n🔄 Syncing action items for {args.owner} to Trello...")
        results = integration.create_cards_for_owner(args.owner, board_id=args.board)

        print(f"\n✅ Sync Complete:")
        print(f"   • Created: {results['created']}")
        print(f"   • Skipped (duplicates): {results['skipped']}")
        print(f"   • Errors: {results['errors']}")

        if results['cards']:
            print(f"\n📌 Created Cards:")
            for card in results['cards']:
                print(f"   • {card['name']}")


if __name__ == "__main__":
    main()
