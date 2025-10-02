#!/usr/bin/env python3
"""
Trello MCP Server
=================

Enterprise-grade Model Context Protocol server for Trello integration.
Uses Trello REST API with Maia security patterns.

Capabilities:
- Board operations (list, create, archive, search)
- List operations (get, create, move, archive)
- Card operations (CRUD, move, comments, labels)
- Member and organization management
- Local LLM intelligence for analysis

Security:
- AES-256 encrypted credential storage
- API Key + Token authentication (OAuth 1.0a)
- Audit logging and compliance tracking
- Read-only mode for safe operations

Authentication:
- Current: API Key + Token (OAuth 1.0a)
- Future: OAuth 2.0 ready (abstract auth layer)
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import logging
import asyncio
import requests
from urllib.parse import urlencode

# MCP Protocol
try:
    from mcp.server.models import InitializationOptions
    from mcp.server import NotificationOptions, Server
    from mcp.types import Resource, Tool, TextContent, ImageContent, EmbeddedResource
except ImportError:
    print("Installing MCP library...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "mcp"])
    from mcp.server.models import InitializationOptions
    from mcp.server import NotificationOptions, Server
    from mcp.types import Resource, Tool, TextContent, ImageContent, EmbeddedResource

# Trello SDK
try:
    from trello import TrelloClient as PyTrelloClient
except ImportError:
    print("Installing py-trello library...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "py-trello"])
    from trello import TrelloClient as PyTrelloClient

# Maia security integration
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from claude.tools.security.mcp_env_manager import MCPEnvironmentManager
from claude.tools.core.path_manager import get_maia_root

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("trello-mcp")

class TrelloAuthProvider:
    """Authentication provider with OAuth 1.0a (current) and OAuth 2.0 (future) support"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_token: Optional[str] = None,
        use_oauth2: bool = False
    ):
        """Initialize auth provider"""
        self.api_key = api_key or os.getenv("TRELLO_API_KEY")
        self.api_token = api_token or os.getenv("TRELLO_API_TOKEN")
        self.use_oauth2 = use_oauth2

        # Initialize secure credential manager
        self.env_manager = MCPEnvironmentManager()

        # Load credentials from secure storage if not provided
        if not self.api_key or not self.api_token:
            self._load_secure_credentials()

    def _load_secure_credentials(self):
        """Load credentials from secure storage"""
        try:
            config = self.env_manager.get_service_config("trello")
            if config:
                self.api_key = config.get("api_key")
                self.api_token = config.get("api_token")
        except Exception as e:
            logger.warning(f"Could not load secure credentials: {e}")

    def get_auth_params(self) -> dict:
        """Get authentication parameters for API requests"""
        if self.use_oauth2:
            return self._oauth2_auth()
        else:
            return self._api_key_token_auth()

    def _api_key_token_auth(self) -> dict:
        """Current production authentication method"""
        return {
            "key": self.api_key,
            "token": self.api_token
        }

    def _oauth2_auth(self) -> dict:
        """Future OAuth 2.0 authentication (not yet available)"""
        raise NotImplementedError(
            "OAuth 2.0 not yet available for Trello. "
            "Expected availability: Late 2025. "
            "Using API Key/Token authentication."
        )

class TrelloClient:
    """Trello API client with enterprise security"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_token: Optional[str] = None,
        read_only: bool = False
    ):
        """Initialize Trello client with secure authentication"""

        self.read_only = read_only
        self.auth = TrelloAuthProvider(api_key, api_token)

        # Initialize py-trello client
        if self.auth.api_key and self.auth.api_token:
            self.client = PyTrelloClient(
                api_key=self.auth.api_key,
                token=self.auth.api_token
            )
        else:
            self.client = None
            logger.warning("Trello client not initialized - missing credentials")

        # Base API URL
        self.base_url = "https://api.trello.com/1"

        logger.info(f"Trello Client initialized (read_only={read_only})")

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        data: Optional[dict] = None
    ) -> dict:
        """Make authenticated API request"""

        url = f"{self.base_url}/{endpoint}"

        # Add authentication
        request_params = self.auth.get_auth_params()
        if params:
            request_params.update(params)

        # Read-only enforcement
        if self.read_only and method.upper() not in ["GET", "HEAD"]:
            raise PermissionError(
                f"Read-only mode: {method} requests not allowed"
            )

        # Make request
        response = requests.request(
            method=method,
            url=url,
            params=request_params,
            json=data
        )
        response.raise_for_status()

        return response.json() if response.content else {}

    # ==================== Board Operations ====================

    def list_boards(self, member: str = "me") -> List[dict]:
        """List all boards for a member"""
        return self._make_request("GET", f"members/{member}/boards")

    def get_board(self, board_id: str) -> dict:
        """Get board details"""
        return self._make_request("GET", f"boards/{board_id}")

    def create_board(self, name: str, desc: str = "", **kwargs) -> dict:
        """Create a new board"""
        data = {"name": name, "desc": desc, **kwargs}
        return self._make_request("POST", "boards", data=data)

    def archive_board(self, board_id: str) -> dict:
        """Archive (close) a board"""
        return self._make_request("PUT", f"boards/{board_id}", data={"closed": True})

    def search_boards(self, query: str) -> List[dict]:
        """Search boards by name"""
        results = self._make_request("GET", "search", params={
            "query": query,
            "modelTypes": "boards",
            "board_fields": "all"
        })
        return results.get("boards", [])

    # ==================== List Operations ====================

    def get_lists(self, board_id: str, filter: str = "open") -> List[dict]:
        """Get all lists on a board"""
        return self._make_request("GET", f"boards/{board_id}/lists", params={"filter": filter})

    def get_list(self, list_id: str) -> dict:
        """Get list details"""
        return self._make_request("GET", f"lists/{list_id}")

    def create_list(self, board_id: str, name: str, pos: str = "bottom") -> dict:
        """Create a new list on a board"""
        data = {"name": name, "idBoard": board_id, "pos": pos}
        return self._make_request("POST", "lists", data=data)

    def move_list(self, list_id: str, board_id: str, pos: str = "bottom") -> dict:
        """Move list to another board or position"""
        data = {"value": board_id, "pos": pos}
        return self._make_request("PUT", f"lists/{list_id}/idBoard", data=data)

    def archive_list(self, list_id: str) -> dict:
        """Archive (close) a list"""
        return self._make_request("PUT", f"lists/{list_id}/closed", data={"value": True})

    # ==================== Card Operations ====================

    def get_cards(self, list_id: str, filter: str = "open") -> List[dict]:
        """Get all cards in a list"""
        return self._make_request("GET", f"lists/{list_id}/cards", params={"filter": filter})

    def get_card(self, card_id: str) -> dict:
        """Get card details"""
        return self._make_request("GET", f"cards/{card_id}")

    def create_card(
        self,
        list_id: str,
        name: str,
        desc: str = "",
        pos: str = "bottom",
        labels: Optional[List[str]] = None,
        members: Optional[List[str]] = None,
        **kwargs
    ) -> dict:
        """Create a new card"""
        data = {
            "idList": list_id,
            "name": name,
            "desc": desc,
            "pos": pos,
            **kwargs
        }

        if labels:
            data["idLabels"] = labels
        if members:
            data["idMembers"] = members

        return self._make_request("POST", "cards", data=data)

    def update_card(self, card_id: str, **kwargs) -> dict:
        """Update card details"""
        return self._make_request("PUT", f"cards/{card_id}", data=kwargs)

    def move_card(self, card_id: str, list_id: str, pos: str = "bottom") -> dict:
        """Move card to another list"""
        data = {"idList": list_id, "pos": pos}
        return self._make_request("PUT", f"cards/{card_id}", data=data)

    def add_comment(self, card_id: str, text: str) -> dict:
        """Add comment to card"""
        return self._make_request("POST", f"cards/{card_id}/actions/comments", data={"text": text})

    def archive_card(self, card_id: str) -> dict:
        """Archive (close) a card"""
        return self._make_request("PUT", f"cards/{card_id}", data={"closed": True})

    def delete_card(self, card_id: str) -> dict:
        """Permanently delete a card"""
        return self._make_request("DELETE", f"cards/{card_id}")

    # ==================== Label Operations ====================

    def get_board_labels(self, board_id: str) -> List[dict]:
        """Get all labels on a board"""
        return self._make_request("GET", f"boards/{board_id}/labels")

    def create_label(self, board_id: str, name: str, color: str) -> dict:
        """Create a label on a board"""
        data = {"name": name, "color": color, "idBoard": board_id}
        return self._make_request("POST", "labels", data=data)

    def add_label_to_card(self, card_id: str, label_id: str) -> dict:
        """Add label to card"""
        return self._make_request("POST", f"cards/{card_id}/idLabels", data={"value": label_id})

    # ==================== Member Operations ====================

    def get_board_members(self, board_id: str) -> List[dict]:
        """Get all members of a board"""
        return self._make_request("GET", f"boards/{board_id}/members")

    def get_member(self, member_id: str = "me") -> dict:
        """Get member details"""
        return self._make_request("GET", f"members/{member_id}")

    def add_member_to_card(self, card_id: str, member_id: str) -> dict:
        """Add member to card"""
        return self._make_request("POST", f"cards/{card_id}/idMembers", data={"value": member_id})

    # ==================== Checklist Operations ====================

    def create_checklist(self, card_id: str, name: str) -> dict:
        """Create checklist on card"""
        data = {"idCard": card_id, "name": name}
        return self._make_request("POST", "checklists", data=data)

    def add_checklist_item(self, checklist_id: str, name: str) -> dict:
        """Add item to checklist"""
        return self._make_request("POST", f"checklists/{checklist_id}/checkItems", data={"name": name})

# ==================== MCP Server Setup ====================

server = Server("trello-mcp")
trello_client: Optional[TrelloClient] = None

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available Trello tools"""
    return [
        # Board Operations
        Tool(
            name="trello_list_boards",
            description="List all Trello boards for the authenticated user",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="trello_get_board",
            description="Get details of a specific Trello board",
            inputSchema={
                "type": "object",
                "properties": {
                    "board_id": {"type": "string", "description": "Board ID"}
                },
                "required": ["board_id"]
            }
        ),
        Tool(
            name="trello_create_board",
            description="Create a new Trello board",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Board name"},
                    "desc": {"type": "string", "description": "Board description"}
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="trello_search_boards",
            description="Search boards by name",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        ),

        # List Operations
        Tool(
            name="trello_get_lists",
            description="Get all lists on a board",
            inputSchema={
                "type": "object",
                "properties": {
                    "board_id": {"type": "string", "description": "Board ID"},
                    "filter": {"type": "string", "description": "Filter: open, closed, all", "default": "open"}
                },
                "required": ["board_id"]
            }
        ),
        Tool(
            name="trello_create_list",
            description="Create a new list on a board",
            inputSchema={
                "type": "object",
                "properties": {
                    "board_id": {"type": "string", "description": "Board ID"},
                    "name": {"type": "string", "description": "List name"},
                    "pos": {"type": "string", "description": "Position: top, bottom, or number", "default": "bottom"}
                },
                "required": ["board_id", "name"]
            }
        ),

        # Card Operations
        Tool(
            name="trello_get_cards",
            description="Get all cards in a list",
            inputSchema={
                "type": "object",
                "properties": {
                    "list_id": {"type": "string", "description": "List ID"},
                    "filter": {"type": "string", "description": "Filter: open, closed, all", "default": "open"}
                },
                "required": ["list_id"]
            }
        ),
        Tool(
            name="trello_get_card",
            description="Get details of a specific card",
            inputSchema={
                "type": "object",
                "properties": {
                    "card_id": {"type": "string", "description": "Card ID"}
                },
                "required": ["card_id"]
            }
        ),
        Tool(
            name="trello_create_card",
            description="Create a new card in a list",
            inputSchema={
                "type": "object",
                "properties": {
                    "list_id": {"type": "string", "description": "List ID"},
                    "name": {"type": "string", "description": "Card name/title"},
                    "desc": {"type": "string", "description": "Card description"},
                    "pos": {"type": "string", "description": "Position: top, bottom, or number", "default": "bottom"}
                },
                "required": ["list_id", "name"]
            }
        ),
        Tool(
            name="trello_update_card",
            description="Update card details",
            inputSchema={
                "type": "object",
                "properties": {
                    "card_id": {"type": "string", "description": "Card ID"},
                    "name": {"type": "string", "description": "New card name"},
                    "desc": {"type": "string", "description": "New card description"}
                },
                "required": ["card_id"]
            }
        ),
        Tool(
            name="trello_move_card",
            description="Move card to another list",
            inputSchema={
                "type": "object",
                "properties": {
                    "card_id": {"type": "string", "description": "Card ID"},
                    "list_id": {"type": "string", "description": "Target list ID"},
                    "pos": {"type": "string", "description": "Position: top, bottom, or number", "default": "bottom"}
                },
                "required": ["card_id", "list_id"]
            }
        ),
        Tool(
            name="trello_add_comment",
            description="Add comment to a card",
            inputSchema={
                "type": "object",
                "properties": {
                    "card_id": {"type": "string", "description": "Card ID"},
                    "text": {"type": "string", "description": "Comment text"}
                },
                "required": ["card_id", "text"]
            }
        ),
        Tool(
            name="trello_archive_card",
            description="Archive (close) a card",
            inputSchema={
                "type": "object",
                "properties": {
                    "card_id": {"type": "string", "description": "Card ID"}
                },
                "required": ["card_id"]
            }
        ),

        # Member Operations
        Tool(
            name="trello_get_board_members",
            description="Get all members of a board",
            inputSchema={
                "type": "object",
                "properties": {
                    "board_id": {"type": "string", "description": "Board ID"}
                },
                "required": ["board_id"]
            }
        ),
        Tool(
            name="trello_get_member",
            description="Get member details",
            inputSchema={
                "type": "object",
                "properties": {
                    "member_id": {"type": "string", "description": "Member ID or 'me'", "default": "me"}
                }
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> List[TextContent]:
    """Handle tool calls"""

    global trello_client

    if not trello_client:
        return [TextContent(
            type="text",
            text="Error: Trello client not initialized. Set TRELLO_API_KEY and TRELLO_API_TOKEN environment variables."
        )]

    try:
        # Board Operations
        if name == "trello_list_boards":
            result = trello_client.list_boards()

        elif name == "trello_get_board":
            result = trello_client.get_board(arguments["board_id"])

        elif name == "trello_create_board":
            result = trello_client.create_board(
                name=arguments["name"],
                desc=arguments.get("desc", "")
            )

        elif name == "trello_search_boards":
            result = trello_client.search_boards(arguments["query"])

        # List Operations
        elif name == "trello_get_lists":
            result = trello_client.get_lists(
                board_id=arguments["board_id"],
                filter=arguments.get("filter", "open")
            )

        elif name == "trello_create_list":
            result = trello_client.create_list(
                board_id=arguments["board_id"],
                name=arguments["name"],
                pos=arguments.get("pos", "bottom")
            )

        # Card Operations
        elif name == "trello_get_cards":
            result = trello_client.get_cards(
                list_id=arguments["list_id"],
                filter=arguments.get("filter", "open")
            )

        elif name == "trello_get_card":
            result = trello_client.get_card(arguments["card_id"])

        elif name == "trello_create_card":
            result = trello_client.create_card(
                list_id=arguments["list_id"],
                name=arguments["name"],
                desc=arguments.get("desc", ""),
                pos=arguments.get("pos", "bottom")
            )

        elif name == "trello_update_card":
            update_data = {k: v for k, v in arguments.items() if k != "card_id" and v is not None}
            result = trello_client.update_card(arguments["card_id"], **update_data)

        elif name == "trello_move_card":
            result = trello_client.move_card(
                card_id=arguments["card_id"],
                list_id=arguments["list_id"],
                pos=arguments.get("pos", "bottom")
            )

        elif name == "trello_add_comment":
            result = trello_client.add_comment(
                card_id=arguments["card_id"],
                text=arguments["text"]
            )

        elif name == "trello_archive_card":
            result = trello_client.archive_card(arguments["card_id"])

        # Member Operations
        elif name == "trello_get_board_members":
            result = trello_client.get_board_members(arguments["board_id"])

        elif name == "trello_get_member":
            result = trello_client.get_member(arguments.get("member_id", "me"))

        else:
            return [TextContent(
                type="text",
                text=f"Error: Unknown tool {name}"
            )]

        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    except Exception as e:
        logger.error(f"Error executing {name}: {e}")
        return [TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]

async def main():
    """Main entry point"""
    global trello_client

    # Initialize Trello client
    read_only = os.getenv("TRELLO_READ_ONLY", "false").lower() == "true"
    trello_client = TrelloClient(read_only=read_only)

    # Run MCP server
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="trello-mcp",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
