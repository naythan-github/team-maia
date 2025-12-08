#!/usr/bin/env python3
"""
Trello MCP Server Test Script
Quick validation of Trello connection and basic operations
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from claude.tools.mcp.trello_mcp_server import TrelloClient

def test_trello_connection():
    """Test Trello connection and basic operations"""

    print("=" * 60)
    print("🔧 Testing Trello MCP Server")
    print("=" * 60)

    # Initialize client (read-only for safety)
    print("\n1️⃣  Initializing Trello client (read-only mode)...")
    client = TrelloClient(read_only=True)

    # Validate authentication
    if not client.auth.api_key or not client.auth.api_token:
        print("❌ Failed to initialize Trello client")
        print("\n📋 Troubleshooting:")
        print("   1. Set environment variables:")
        print("      export TRELLO_API_KEY='your_key'")
        print("      export TRELLO_API_TOKEN='your_token'")
        print("\n   2. Or use secure storage:")
        print("      python3 -c \"from claude.tools.security.mcp_env_manager import MCPEnvironmentManager; \\")
        print("      manager = MCPEnvironmentManager(); \\")
        print("      manager.set_service_config('trello', {'api_key': 'KEY', 'api_token': 'TOKEN'})\"")
        print("\n   3. Get credentials from: https://trello.com/power-ups/admin")
        return False

    try:
        # Test 1: Get current user
        print("\n2️⃣  Testing authentication...")
        member = client.get_member()
        print(f"✅ Connected as: {member.get('fullName')} (@{member.get('username')})")
        print(f"   Email: {member.get('email', 'N/A')}")
        print(f"   Member ID: {member.get('id')}")

        # Test 2: List boards
        print("\n3️⃣  Fetching boards...")
        boards = client.list_boards()
        print(f"✅ Found {len(boards)} board(s)")

        if not boards:
            print("\n⚠️  No boards found. Create a board in Trello to test further.")
            print("   Visit: https://trello.com/")
            return True

        # Show first few boards
        print("\n📋 Your boards:")
        for i, board in enumerate(boards[:5], 1):
            print(f"   {i}. {board['name']}")
            print(f"      ID: {board['id']}")
            print(f"      URL: {board.get('url', 'N/A')}")

        if len(boards) > 5:
            print(f"   ... and {len(boards) - 5} more")

        # Test 3: Get lists from first board
        board = boards[0]
        print(f"\n4️⃣  Fetching lists from: {board['name']}")
        lists = client.get_lists(board['id'])
        print(f"✅ Board has {len(lists)} list(s)")

        if lists:
            print("\n📝 Lists:")
            for i, lst in enumerate(lists, 1):
                print(f"   {i}. {lst['name']} (ID: {lst['id']})")

            # Test 4: Get cards from first list
            first_list = lists[0]
            print(f"\n5️⃣  Fetching cards from: {first_list['name']}")
            cards = client.get_cards(first_list['id'])
            print(f"✅ List has {len(cards)} card(s)")

            if cards:
                print("\n🎫 Cards:")
                for i, card in enumerate(cards[:5], 1):
                    print(f"   {i}. {card['name']}")
                    if card.get('desc'):
                        desc_preview = card['desc'][:50] + "..." if len(card['desc']) > 50 else card['desc']
                        print(f"      {desc_preview}")
                    print(f"      ID: {card['id']}")

                if len(cards) > 5:
                    print(f"   ... and {len(cards) - 5} more")

        # Test 5: Get board members
        print(f"\n6️⃣  Fetching members from: {board['name']}")
        members = client.get_board_members(board['id'])
        print(f"✅ Board has {len(members)} member(s)")

        if members:
            print("\n👥 Members:")
            for i, member in enumerate(members, 1):
                print(f"   {i}. {member.get('fullName')} (@{member.get('username')})")

        # Test 6: Get board labels
        print(f"\n7️⃣  Fetching labels from: {board['name']}")
        labels = client.get_board_labels(board['id'])
        print(f"✅ Board has {len(labels)} label(s)")

        if labels:
            print("\n🏷️  Labels:")
            for i, label in enumerate(labels, 1):
                name = label.get('name') or '(no name)'
                color = label.get('color') or 'none'
                print(f"   {i}. {name} (Color: {color})")

        # Success summary
        print("\n" + "=" * 60)
        print("🎉 Trello MCP Server Validation Complete!")
        print("=" * 60)
        print("\n✅ All tests passed:")
        print("   - Authentication working")
        print("   - Board access confirmed")
        print("   - List operations working")
        print("   - Card access working")
        print("   - Member access working")
        print("   - Label access working")

        print("\n📖 Next steps:")
        print("   1. Configure Claude Desktop MCP:")
        print("      See: TRELLO_SETUP_GUIDE.md")
        print("   2. Test write operations (disable read-only mode)")
        print("   3. Integrate with Maia agents")

        return True

    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        print(f"\n🔍 Error details: {type(e).__name__}")

        if "401" in str(e):
            print("\n📋 Authentication error:")
            print("   - Check API key and token are correct")
            print("   - Regenerate token if expired")
            print("   - Visit: https://trello.com/power-ups/admin")
        elif "403" in str(e):
            print("\n📋 Permission error:")
            print("   - Check token has required scopes (read, write)")
            print("   - Verify board/workspace access")
        elif "404" in str(e):
            print("\n📋 Not found error:")
            print("   - Check board/list/card IDs are correct")
            print("   - Verify resource hasn't been deleted")

        return False

def main():
    """Main entry point"""
    success = test_trello_connection()

    print("\n" + "=" * 60)
    if success:
        print("✅ TEST RESULT: PASS")
    else:
        print("❌ TEST RESULT: FAIL")
    print("=" * 60)

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
