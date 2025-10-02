#!/usr/bin/env python3
"""
Fast Trello query tool for Claude Code
Direct API calls without MCP overhead
"""

import sys
import json
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from claude.tools.mcp.trello_mcp_server import TrelloClient

def main():
    """Query Trello data"""

    client = TrelloClient(read_only=True)

    # Get all boards
    boards = client.list_boards()

    result = {
        "boards": [],
        "total_lists": 0,
        "total_cards": 0
    }

    for board in boards:
        board_data = {
            "id": board["id"],
            "name": board["name"],
            "url": board["url"],
            "lists": []
        }

        # Get lists for this board
        lists = client.get_lists(board["id"])
        result["total_lists"] += len(lists)

        for lst in lists:
            list_data = {
                "id": lst["id"],
                "name": lst["name"],
                "cards": []
            }

            # Get cards in this list
            cards = client.get_cards(lst["id"])
            result["total_cards"] += len(cards)

            for card in cards:
                list_data["cards"].append({
                    "id": card["id"],
                    "name": card["name"],
                    "desc": card.get("desc", "")[:100],
                    "url": card["url"]
                })

            board_data["lists"].append(list_data)

        result["boards"].append(board_data)

    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
