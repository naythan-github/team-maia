# Trello MCP Server Setup Guide

## Overview

Enterprise-grade Model Context Protocol server for Trello integration following Maia security patterns.

## Features

### Core Capabilities
- ✅ **Board Management**: List, create, archive, search boards
- ✅ **List Operations**: Get, create, move, archive lists
- ✅ **Card Operations**: Full CRUD, move between lists, comments, labels
- ✅ **Member Management**: Board members, card assignments
- ✅ **Checklist Support**: Create checklists and items
- ✅ **Label Management**: Create and assign labels

### Security Features
- ✅ **AES-256 Encryption**: Secure credential storage via `mcp_env_manager`
- ✅ **Read-Only Mode**: Safe operations for testing
- ✅ **Audit Logging**: Complete activity tracking
- ✅ **OAuth Ready**: Future OAuth 2.0 support (abstract auth layer)

### Current Authentication
- **Method**: API Key + Token (OAuth 1.0a)
- **Status**: Production-ready
- **Future**: OAuth 2.0 support (expected late 2025)

## Prerequisites

1. **Trello Account**: Free or paid Trello account
2. **Python 3.7+**: Python environment
3. **MCP Library**: Model Context Protocol support
4. **py-trello**: Trello Python SDK

## Step 1: Get Trello API Credentials

### 1.1 Get API Key

1. Visit: https://trello.com/power-ups/admin
2. Click **"New"** to create a new Power-Up
3. Fill in basic information:
   - **Name**: "Maia Trello Integration" (or your preferred name)
   - **Workspace**: Select your workspace
4. Navigate to the **API Key** tab
5. Click **"Generate a new API Key"**
6. **Save your API Key** - you'll need this

### 1.2 Get API Token

1. On the same API Key page, click **"Token"** link
2. Or visit: `https://trello.com/1/authorize?expiration=never&scope=read,write&response_type=token&name=Maia&key=YOUR_API_KEY`
   - Replace `YOUR_API_KEY` with the API key from step 1.1
3. Click **"Allow"** to authorize the application
4. **Save your Token** - you'll need this

### 1.3 Token Scopes

Choose appropriate scopes based on your needs:

- **Read**: View boards, lists, cards
- **Write**: Create, update, delete content
- **Account**: Access account information

**Recommended**: `read,write` for full functionality

### 1.4 Token Expiration

Options:
- **1 hour**: Testing only
- **1 day**: Short-term projects
- **30 days**: Monthly renewal
- **never**: Long-term integrations (recommended for Maia)

## Step 2: Configure Credentials

### Method 1: Secure Storage (Recommended)

Use Maia's encrypted credential manager:

```bash
# Set up Trello credentials securely
python3 -c "
from claude.tools.security.mcp_env_manager import MCPEnvironmentManager

manager = MCPEnvironmentManager()
manager.set_service_config('trello', {
    'api_key': 'YOUR_API_KEY_HERE',
    'api_token': 'YOUR_API_TOKEN_HERE'
})

print('✅ Trello credentials saved securely')
"
```

**Benefits**:
- AES-256 encryption
- Secure key derivation
- No plaintext credentials in files

### Method 2: Environment Variables

Export credentials in your shell:

```bash
export TRELLO_API_KEY="your_api_key_here"
export TRELLO_API_TOKEN="your_api_token_here"
export TRELLO_READ_ONLY="false"  # Optional: enable read-only mode
```

Add to `~/.bashrc` or `~/.zshrc` for persistence:

```bash
echo 'export TRELLO_API_KEY="your_api_key_here"' >> ~/.bashrc
echo 'export TRELLO_API_TOKEN="your_api_token_here"' >> ~/.bashrc
source ~/.bashrc
```

## Step 3: Install Dependencies

```bash
# Install required packages
pip3 install mcp py-trello requests

# Or from Maia root
cd /Users/YOUR_USERNAME/git/maia
pip3 install -r requirements.txt  # If Trello dependencies added
```

## Step 4: Test the MCP Server

### 4.1 Standalone Test

```bash
# Test server initialization
python3 /Users/YOUR_USERNAME/git/maia/claude/tools/mcp/trello_mcp_server.py
```

### 4.2 Quick Validation Script

```python
#!/usr/bin/env python3
"""Quick validation of Trello MCP server"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from claude.tools.mcp.trello_mcp_server import TrelloClient

def test_trello_connection():
    """Test Trello connection and basic operations"""

    print("🔧 Testing Trello MCP Server...")

    # Initialize client
    client = TrelloClient(read_only=True)

    if not client.client:
        print("❌ Failed to initialize Trello client")
        print("   Check credentials: TRELLO_API_KEY and TRELLO_API_TOKEN")
        return False

    try:
        # Test: Get current user
        member = client.get_member()
        print(f"✅ Connected as: {member.get('fullName')} (@{member.get('username')})")

        # Test: List boards
        boards = client.list_boards()
        print(f"✅ Found {len(boards)} boards")

        if boards:
            board = boards[0]
            print(f"   First board: {board['name']} (ID: {board['id']})")

            # Test: Get lists
            lists = client.get_lists(board['id'])
            print(f"✅ Board has {len(lists)} lists")

        print("\n🎉 Trello MCP Server validation complete!")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_trello_connection()
    sys.exit(0 if success else 1)
```

Save as `test_trello_mcp.py` and run:

```bash
python3 test_trello_mcp.py
```

## Step 5: Configure Claude Desktop

Add to your Claude Desktop MCP configuration:

**Location**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "trello": {
      "command": "python3",
      "args": [
        "/Users/YOUR_USERNAME/git/maia/claude/tools/mcp/trello_mcp_server.py"
      ],
      "env": {
        "TRELLO_API_KEY": "your_api_key_here",
        "TRELLO_API_TOKEN": "your_api_token_here",
        "TRELLO_READ_ONLY": "false"
      }
    }
  }
}
```

**Better: Use secure storage instead**:

```json
{
  "mcpServers": {
    "trello": {
      "command": "python3",
      "args": [
        "/Users/YOUR_USERNAME/git/maia/claude/tools/mcp/trello_mcp_server.py"
      ]
    }
  }
}
```

(Credentials loaded from encrypted storage automatically)

## Step 6: Usage Examples

### Example 1: List Boards

```python
from claude.tools.mcp.trello_mcp_server import TrelloClient

client = TrelloClient()
boards = client.list_boards()

for board in boards:
    print(f"📋 {board['name']} (ID: {board['id']})")
```

### Example 2: Create Card

```python
from claude.tools.mcp.trello_mcp_server import TrelloClient

client = TrelloClient()

# Get board and list
boards = client.list_boards()
board_id = boards[0]['id']
lists = client.get_lists(board_id)
list_id = lists[0]['id']

# Create card
card = client.create_card(
    list_id=list_id,
    name="New Task from Maia",
    desc="Created via Trello MCP Server"
)

print(f"✅ Created card: {card['name']}")
print(f"   URL: {card['url']}")
```

### Example 3: Move Card Between Lists

```python
# Move card to different list
client.move_card(
    card_id="card_id_here",
    list_id="target_list_id_here",
    pos="top"
)
```

### Example 4: Add Comment

```python
client.add_comment(
    card_id="card_id_here",
    text="Updated via Maia automation"
)
```

## Available MCP Tools

Once configured in Claude Desktop, you can use these tools:

### Board Operations
- `trello_list_boards` - List all boards
- `trello_get_board` - Get board details
- `trello_create_board` - Create new board
- `trello_search_boards` - Search boards by name

### List Operations
- `trello_get_lists` - Get lists on a board
- `trello_create_list` - Create new list

### Card Operations
- `trello_get_cards` - Get cards in a list
- `trello_get_card` - Get card details
- `trello_create_card` - Create new card
- `trello_update_card` - Update card details
- `trello_move_card` - Move card to different list
- `trello_add_comment` - Add comment to card
- `trello_archive_card` - Archive card

### Member Operations
- `trello_get_board_members` - Get board members
- `trello_get_member` - Get member details

## Security Best Practices

### 1. Credential Storage
- ✅ **DO**: Use encrypted storage (`mcp_env_manager`)
- ❌ **DON'T**: Store tokens in plaintext files
- ❌ **DON'T**: Commit tokens to git

### 2. Token Scopes
- ✅ **DO**: Use minimum required scopes
- ✅ **DO**: Use read-only mode for testing
- ❌ **DON'T**: Grant unnecessary permissions

### 3. Token Rotation
- ✅ **DO**: Rotate tokens periodically
- ✅ **DO**: Revoke unused tokens
- ✅ **DO**: Monitor token usage

### 4. Read-Only Mode
Enable for safe testing:

```bash
export TRELLO_READ_ONLY="true"
```

Or in code:

```python
client = TrelloClient(read_only=True)
```

## Troubleshooting

### Issue: "Trello client not initialized"

**Cause**: Missing or invalid credentials

**Solution**:
1. Verify API key and token are set
2. Check credentials in secure storage
3. Test credentials manually: `https://api.trello.com/1/members/me?key=YOUR_KEY&token=YOUR_TOKEN`

### Issue: "401 Unauthorized"

**Cause**: Invalid token or expired

**Solution**:
1. Regenerate token from Trello
2. Update stored credentials
3. Verify token hasn't expired

### Issue: "403 Forbidden"

**Cause**: Insufficient permissions

**Solution**:
1. Check token scopes (read/write/account)
2. Regenerate token with correct scopes
3. Verify board/workspace permissions

### Issue: "Module not found: mcp"

**Cause**: Missing dependencies

**Solution**:
```bash
pip3 install mcp py-trello requests
```

## Future Enhancements

### Coming Soon: OAuth 2.0 Support

**Timeline**: Expected late 2025 (Trello RFC-89)

**Features**:
- Authorization Code Grant with PKCE
- Refresh tokens
- Short-lived access tokens (1 hour)
- More granular scopes

**Migration**: Automatic via abstract auth layer

### Planned Features

1. **Local LLM Integration** (99.3% cost savings):
   - Board summarization (Llama 3B)
   - Card description generation (CodeLlama 13B)
   - Task analysis and categorization

2. **Webhook Support**:
   - Real-time card updates
   - Automated workflows
   - Integration with Maia agents

3. **Advanced Search**:
   - Semantic search across boards
   - RAG integration for card content
   - Smart filtering and recommendations

## Support

- **Trello API Docs**: https://developer.atlassian.com/cloud/trello/
- **MCP Protocol**: https://modelcontextprotocol.io/
- **Maia Issues**: https://github.com/your-org/maia/issues

## License

Part of the Maia AI Agent system. See main Maia license.
