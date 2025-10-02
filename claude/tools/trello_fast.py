#!/usr/bin/env python3
"""
Fast Trello Integration for Claude Code
Full CRUD operations without MCP overhead
"""

import os
import sys
import json
import requests
from typing import Optional, List, Dict, Any

API_KEY = os.getenv("TRELLO_API_KEY")
API_TOKEN = os.getenv("TRELLO_API_TOKEN")
BASE_URL = "https://api.trello.com/1"

class TrelloFast:
    """Fast Trello client for Claude Code"""

    def __init__(self, api_key: str = None, api_token: str = None):
        self.api_key = api_key or API_KEY
        self.api_token = api_token or API_TOKEN

        if not self.api_key or not self.api_token:
            raise ValueError("TRELLO_API_KEY and TRELLO_API_TOKEN must be set")

    def _request(self, method: str, endpoint: str, data: dict = None) -> Any:
        """Make API request"""
        url = f"{BASE_URL}/{endpoint}"
        params = {"key": self.api_key, "token": self.api_token}

        response = requests.request(
            method=method,
            url=url,
            params=params,
            json=data,
            timeout=10
        )
        response.raise_for_status()
        return response.json() if response.content else {}

    # ==================== Board Operations ====================

    def list_boards(self) -> List[Dict]:
        """List all boards"""
        return self._request("GET", "members/me/boards")

    def get_board(self, board_id: str) -> Dict:
        """Get board details"""
        return self._request("GET", f"boards/{board_id}")

    def create_board(self, name: str, desc: str = "") -> Dict:
        """Create new board"""
        return self._request("POST", "boards", {"name": name, "desc": desc})

    def search_boards(self, query: str) -> List[Dict]:
        """Search boards by name"""
        result = self._request("GET", "search", {"query": query, "modelTypes": "boards"})
        return result.get("boards", [])

    # ==================== List Operations ====================

    def get_lists(self, board_id: str, filter: str = "open") -> List[Dict]:
        """Get lists on a board"""
        return self._request("GET", f"boards/{board_id}/lists", {"filter": filter})

    def create_list(self, board_id: str, name: str, pos: str = "bottom") -> Dict:
        """Create new list"""
        return self._request("POST", "lists", {
            "name": name,
            "idBoard": board_id,
            "pos": pos
        })

    def archive_list(self, list_id: str) -> Dict:
        """Archive a list"""
        return self._request("PUT", f"lists/{list_id}/closed", {"value": True})

    # ==================== Card Operations ====================

    def get_cards(self, list_id: str, filter: str = "open") -> List[Dict]:
        """Get cards in a list"""
        return self._request("GET", f"lists/{list_id}/cards", {"filter": filter})

    def get_card(self, card_id: str) -> Dict:
        """Get card details"""
        return self._request("GET", f"cards/{card_id}")

    def create_card(
        self,
        list_id: str,
        name: str,
        desc: str = "",
        pos: str = "bottom",
        labels: List[str] = None,
        members: List[str] = None
    ) -> Dict:
        """Create new card"""
        data = {
            "idList": list_id,
            "name": name,
            "desc": desc,
            "pos": pos
        }

        if labels:
            data["idLabels"] = labels
        if members:
            data["idMembers"] = members

        return self._request("POST", "cards", data)

    def update_card(self, card_id: str, **kwargs) -> Dict:
        """Update card details"""
        return self._request("PUT", f"cards/{card_id}", kwargs)

    def move_card(self, card_id: str, list_id: str, pos: str = "bottom") -> Dict:
        """Move card to another list"""
        return self._request("PUT", f"cards/{card_id}", {
            "idList": list_id,
            "pos": pos
        })

    def add_comment(self, card_id: str, text: str) -> Dict:
        """Add comment to card"""
        return self._request("POST", f"cards/{card_id}/actions/comments", {"text": text})

    def archive_card(self, card_id: str) -> Dict:
        """Archive a card"""
        return self._request("PUT", f"cards/{card_id}", {"closed": True})

    def delete_card(self, card_id: str) -> Dict:
        """Permanently delete a card"""
        return self._request("DELETE", f"cards/{card_id}")

    # ==================== Label Operations ====================

    def get_board_labels(self, board_id: str) -> List[Dict]:
        """Get all labels on a board"""
        return self._request("GET", f"boards/{board_id}/labels")

    def create_label(self, board_id: str, name: str, color: str) -> Dict:
        """Create a label"""
        return self._request("POST", "labels", {
            "name": name,
            "color": color,
            "idBoard": board_id
        })

    def add_label_to_card(self, card_id: str, label_id: str) -> Dict:
        """Add label to card"""
        return self._request("POST", f"cards/{card_id}/idLabels", {"value": label_id})

    # ==================== Member Operations ====================

    def get_board_members(self, board_id: str) -> List[Dict]:
        """Get board members"""
        return self._request("GET", f"boards/{board_id}/members")

    def get_member(self, member_id: str = "me") -> Dict:
        """Get member details"""
        return self._request("GET", f"members/{member_id}")

    def add_member_to_card(self, card_id: str, member_id: str) -> Dict:
        """Add member to card"""
        return self._request("POST", f"cards/{card_id}/idMembers", {"value": member_id})

    # ==================== Checklist Operations ====================

    def create_checklist(self, card_id: str, name: str) -> Dict:
        """Create checklist on card"""
        return self._request("POST", "checklists", {
            "idCard": card_id,
            "name": name
        })

    def add_checklist_item(self, checklist_id: str, name: str) -> Dict:
        """Add item to checklist"""
        return self._request("POST", f"checklists/{checklist_id}/checkItems", {"name": name})

    # ==================== Helper: Get Everything ====================

    def get_everything(self) -> Dict:
        """Get complete board structure"""
        result = {"boards": [], "total_lists": 0, "total_cards": 0}

        boards = self.list_boards()

        for board in boards:
            board_data = {
                "id": board["id"],
                "name": board["name"],
                "url": board["url"],
                "lists": []
            }

            lists = self.get_lists(board["id"])
            result["total_lists"] += len(lists)

            for lst in lists:
                list_data = {
                    "id": lst["id"],
                    "name": lst["name"],
                    "cards": []
                }

                cards = self.get_cards(lst["id"])
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

        return result


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Fast Trello CLI")
    parser.add_argument("action", choices=["query", "create-card", "move-card", "list-boards"])
    parser.add_argument("--list-id", help="List ID")
    parser.add_argument("--card-id", help="Card ID")
    parser.add_argument("--name", help="Card/Board name")
    parser.add_argument("--desc", help="Card description")
    parser.add_argument("--pos", default="bottom", help="Position (top/bottom)")

    args = parser.parse_args()

    client = TrelloFast()

    if args.action == "query":
        result = client.get_everything()
        print(json.dumps(result, indent=2))

    elif args.action == "list-boards":
        boards = client.list_boards()
        for board in boards:
            print(f"{board['name']} - {board['url']}")

    elif args.action == "create-card":
        if not args.list_id or not args.name:
            print("ERROR: --list-id and --name required")
            sys.exit(1)
        card = client.create_card(args.list_id, args.name, args.desc or "", args.pos)
        print(f"✅ Created: {card['name']} - {card['url']}")

    elif args.action == "move-card":
        if not args.card_id or not args.list_id:
            print("ERROR: --card-id and --list-id required")
            sys.exit(1)
        card = client.move_card(args.card_id, args.list_id, args.pos)
        print(f"✅ Moved: {card['name']}")


if __name__ == "__main__":
    main()
