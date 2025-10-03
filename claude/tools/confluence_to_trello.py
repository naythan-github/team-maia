#!/usr/bin/env python3
"""
Confluence to Trello Integration
Automatically creates categorized Trello cards from Confluence intelligence

Author: Maia Personal Assistant Agent
Phase: 86.4 - Executive Command Center
Date: 2025-10-03
"""

import os
import sys
from pathlib import Path
from typing import Dict, List
import logging

MAIA_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

from claude.tools.confluence_intelligence_processor import ConfluenceIntelligenceProcessor
from claude.tools.trello_fast import TrelloFast

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceTrelloIntegration:
    """Push Confluence intelligence to Trello boards"""

    def __init__(self, board_id: str):
        """Initialize with target board"""
        self.intelligence = ConfluenceIntelligenceProcessor()
        self.trello = TrelloFast()
        self.board_id = board_id

        # Get or create lists
        self.lists = self._setup_lists()

    def _setup_lists(self) -> Dict[str, str]:
        """Setup required lists on board"""
        existing_lists = {l['name'].lower(): l['id']
                         for l in self.trello.get_lists(self.board_id)}

        required_lists = {
            "strategic": "Strategic Initiatives",
            "operational": "Operational Tasks",
            "questions": "Open Questions",
            "decisions": "Decisions Needed"
        }

        list_ids = {}
        for key, name in required_lists.items():
            if name.lower() in existing_lists:
                list_ids[key] = existing_lists[name.lower()]
            else:
                # Create list
                new_list = self.trello.create_list(self.board_id, name)
                list_ids[key] = new_list['id']
                logger.info(f"Created list: {name}")

        return list_ids

    def sync_intelligence_to_trello(self) -> Dict:
        """Sync all intelligence to Trello"""
        export = self.intelligence.export_for_trello()

        results = {
            "strategic": {"created": 0, "skipped": 0},
            "operational": {"created": 0, "skipped": 0},
            "questions": {"created": 0, "skipped": 0},
            "decisions": {"created": 0, "skipped": 0}
        }

        # Sync each category
        for category in ["strategic", "operational", "questions", "decisions"]:
            list_id = self.lists[category]
            cards_data = export[category]

            # Get existing cards to avoid duplicates
            existing_cards = self.trello.get_cards(list_id)
            existing_names = {c['name'].lower() for c in existing_cards}

            for card_data in cards_data:
                if card_data['name'].lower() in existing_names:
                    results[category]["skipped"] += 1
                    continue

                try:
                    self.trello.create_card(
                        list_id=list_id,
                        name=card_data['name'],
                        desc=card_data['desc']
                    )
                    results[category]["created"] += 1
                    logger.info(f"Created {category} card: {card_data['name'][:50]}...")
                except Exception as e:
                    logger.error(f"Failed to create card: {e}")

        return results


def main():
    """CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(description="Confluence to Trello Integration")
    parser.add_argument("--board", required=True, help="Trello board ID")

    args = parser.parse_args()

    print("\n🔄 Syncing Confluence intelligence to Trello...")
    integration = ConfluenceTrelloIntegration(args.board)
    results = integration.sync_intelligence_to_trello()

    print(f"\n✅ Sync Complete:")
    for category, stats in results.items():
        print(f"   • {category.title()}: {stats['created']} created, {stats['skipped']} skipped")


if __name__ == "__main__":
    main()
