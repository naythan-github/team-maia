#!/usr/bin/env python3
"""Fast Trello queries - no encryption overhead"""

import os
import sys
import json
import requests

API_KEY = os.getenv("TRELLO_API_KEY")
API_TOKEN = os.getenv("TRELLO_API_TOKEN")
BASE_URL = "https://api.trello.com/1"

def get(endpoint):
    """Fast GET request"""
    url = f"{BASE_URL}/{endpoint}"
    params = {"key": API_KEY, "token": API_TOKEN}
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()

def main():
    """Query everything"""

    result = {"boards": [], "total_lists": 0, "total_cards": 0}

    boards = get("members/me/boards")

    for board in boards:
        board_data = {
            "id": board["id"],
            "name": board["name"],
            "url": board["url"],
            "lists": []
        }

        lists = get(f"boards/{board['id']}/lists")
        result["total_lists"] += len(lists)

        for lst in lists:
            list_data = {
                "id": lst["id"],
                "name": lst["name"],
                "cards": []
            }

            cards = get(f"lists/{lst['id']}/cards")
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
