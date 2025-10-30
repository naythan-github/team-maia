#!/usr/bin/env python3
"""
Simple, Reliable Confluence Client - THE ONLY TOOL YOU NEED

Usage:
    from confluence_client import ConfluenceClient

    client = ConfluenceClient()
    url = client.create_page_from_markdown(
        space_key="Orro",
        title="My Page Title",
        markdown_content=markdown_string
    )
    print(f"Page created: {url}")

Multi-Site Support:
    client = ConfluenceClient(site_name="orro")

Author: SRE Principal Engineer Agent (Maia)
Date: 2024-11-27
Version: 1.0
Status: Production Ready (TDD Complete)
"""

import os
import json
import markdown as md_lib
import logging
from typing import Optional, List, Dict
from pathlib import Path

# Import underlying reliable client (internal use only)
try:
    from _reliable_confluence_client import ReliableConfluenceClient
except ImportError:
    # Fallback for when file not yet renamed
    from reliable_confluence_client import ReliableConfluenceClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceError(Exception):
    """Base exception for Confluence operations"""
    pass


class ConfluenceClient:
    """
    Simple Confluence client that just works

    Provides one-function-call operations for:
    - Creating pages from markdown
    - Updating existing pages (with automatic lookup)
    - Getting page URLs by title
    - Listing accessible spaces

    Examples:
        # Create page
        client = ConfluenceClient()
        url = client.create_page_from_markdown(
            space_key="Orro",
            title="IaC Strategy",
            markdown_content="# Header\\n\\nContent here"
        )

        # Update existing page (auto-creates if not found)
        url = client.update_page_from_markdown(
            space_key="Orro",
            title="IaC Strategy",
            markdown_content="# Updated Header\\n\\nNew content"
        )

        # Multi-site
        client_orro = ConfluenceClient(site_name="orro")
    """

    def __init__(self, site_name: str = "default"):
        """
        Initialize Confluence client

        Args:
            site_name: Site identifier from config (default, orro, personal)
                      Loads configuration from ~/.maia/confluence_sites.json

        Raises:
            ConfluenceError: If site configuration invalid
        """
        self.site_name = site_name
        self.config = self._load_site_config(site_name)
        self.client = ReliableConfluenceClient()

        logger.info(f"ConfluenceClient initialized for site: {site_name}")

    def create_page_from_markdown(
        self,
        space_key: str,
        title: str,
        markdown_content: str,
        parent_id: Optional[str] = None
    ) -> str:
        """
        Create Confluence page from markdown

        This is the primary function for 95% of use cases. Converts markdown
        to Confluence HTML automatically and creates the page.

        Args:
            space_key: Confluence space key (e.g., "Orro", "MAIA-TEST")
            title: Page title (max 255 characters)
            markdown_content: Markdown content to convert
            parent_id: Optional parent page ID for hierarchical structure

        Returns:
            Page URL (str) - e.g., "https://site.atlassian.net/wiki/spaces/Orro/pages/123"

        Raises:
            ValueError: If input validation fails
            ConfluenceError: If page creation fails

        Example:
            url = client.create_page_from_markdown(
                space_key="Orro",
                title="IaC Enablement Strategy",
                markdown_content="# Strategy\\n\\n## Phase 1\\n..."
            )
        """
        # Validate input
        self._validate_input(space_key, title, markdown_content)

        try:
            # Convert markdown to HTML
            html = self._markdown_to_html(markdown_content)

            # Create page via underlying client
            result = self.client.create_page(
                space_key=space_key,
                title=title,
                content=html,
                parent_id=parent_id
            )

            # Check if creation failed (returns None)
            if result is None:
                raise ConfluenceError(
                    f"Page creation returned None - check API response. "
                    f"Space: {space_key}, Title: {title}"
                )

            # Extract and return URL
            url = self._extract_page_url(result)

            logger.info(f"Page created successfully: {title} → {url}")
            return url

        except ConfluenceError:
            # Re-raise ConfluenceError as-is
            raise
        except Exception as e:
            error_msg = self._format_error_message(
                operation="create page",
                space_key=space_key,
                title=title,
                original_error=e
            )
            logger.error(error_msg)
            raise ConfluenceError(error_msg) from e

    def update_page_from_markdown(
        self,
        space_key: str,
        title: str,
        markdown_content: str
    ) -> str:
        """
        Update existing page from markdown (handles lookup automatically)

        Searches for page by title. If found, updates content. If not found,
        creates new page (fallback behavior for simplified UX).

        Args:
            space_key: Confluence space key
            title: Page title to search for
            markdown_content: New markdown content

        Returns:
            Page URL (str)

        Raises:
            ValueError: If input validation fails
            ConfluenceError: If update/create fails

        Example:
            # Updates if exists, creates if not
            url = client.update_page_from_markdown(
                space_key="Orro",
                title="IaC Strategy",
                markdown_content="# Updated Strategy\\n..."
            )
        """
        # Validate input
        self._validate_input(space_key, title, markdown_content)

        try:
            # 1. Search for existing page
            existing_page = self._find_page_by_title(space_key, title)

            if existing_page:
                # 2a. Update existing page
                html = self._markdown_to_html(markdown_content)

                # Search results don't include version, need to fetch full page
                page_id = existing_page['id']
                full_page = self.client.get_page(page_id, expand='version')

                if not full_page:
                    raise ConfluenceError(f"Found page {page_id} but couldn't fetch full details")

                result = self.client.update_page(
                    page_id=page_id,
                    title=title,
                    content=html,
                    version_number=full_page['version']['number'] + 1
                )

                # Update response doesn't include URL, construct it
                if result and 'url' not in result:
                    # Add space_key and url to result for consistent extraction
                    result['url'] = f"{self.config.get('url', 'https://vivoemc.atlassian.net/wiki')}/spaces/{space_key}/pages/{page_id}"

                url = self._extract_page_url(result)
                logger.info(f"Page updated successfully: {title} → {url}")
                return url
            else:
                # 2b. Create new page if doesn't exist
                logger.info(f"Page not found, creating new: {title}")
                return self.create_page_from_markdown(space_key, title, markdown_content)

        except ConfluenceError:
            # Re-raise ConfluenceError from create_page_from_markdown
            raise
        except Exception as e:
            error_msg = self._format_error_message(
                operation="update page",
                space_key=space_key,
                title=title,
                original_error=e
            )
            logger.error(error_msg)
            raise ConfluenceError(error_msg) from e

    def get_page_url(self, space_key: str, title: str) -> Optional[str]:
        """
        Get page URL by title (simple lookup)

        Args:
            space_key: Confluence space key
            title: Page title to search for

        Returns:
            Page URL if found, None otherwise (not an exception)

        Example:
            url = client.get_page_url("Orro", "IaC Strategy")
            if url:
                print(f"Page exists: {url}")
            else:
                print("Page not found")
        """
        try:
            page = self._find_page_by_title(space_key, title)
            return self._extract_page_url(page) if page else None
        except Exception as e:
            logger.warning(f"Page lookup failed: {space_key}/{title} - {e}")
            return None

    def list_spaces(self) -> List[Dict[str, str]]:
        """
        List all accessible Confluence spaces

        Returns:
            List of spaces with keys and names
            Example: [{"key": "Orro", "name": "Orro Group"}, ...]

        Example:
            spaces = client.list_spaces()
            for space in spaces:
                print(f"{space['key']}: {space['name']}")
        """
        try:
            spaces = self.client.list_spaces()

            if not spaces:
                return []

            return [
                {"key": space.get("key", ""), "name": space.get("name", "")}
                for space in spaces
            ]
        except Exception as e:
            logger.error(f"Failed to list spaces: {e}")
            raise ConfluenceError(f"Failed to list spaces: {e}") from e

    def delete_page(self, space_key: str, title: str) -> bool:
        """
        Delete page by title

        Args:
            space_key: Confluence space key
            title: Page title to delete

        Returns:
            True if deleted, False if not found

        Raises:
            NotImplementedError: Delete not yet implemented in underlying client

        Note: This operation requires enhancement to ReliableConfluenceClient.
              Deferred to Phase 2 based on requirements (P2 priority).
        """
        raise NotImplementedError(
            "Delete operation requires enhancement to ReliableConfluenceClient. "
            "Tracked in requirements as P2 (low priority). "
            "Workaround: Use Confluence web UI for deletions."
        )

    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================

    def _validate_input(self, space_key: str, title: str, markdown_content: str):
        """
        Validate input parameters before API call

        Raises:
            ValueError: If validation fails
        """
        if not space_key or not space_key.strip():
            raise ValueError("space_key cannot be empty")

        if not title or not title.strip():
            raise ValueError("title cannot be empty")

        if len(title) > 255:
            raise ValueError(f"title too long ({len(title)} chars, max 255)")

        if not markdown_content or not markdown_content.strip():
            raise ValueError("markdown_content cannot be empty")

    def _markdown_to_html(self, markdown_content: str) -> str:
        """
        Convert markdown to Confluence-compatible HTML

        Uses Python markdown library with extensions:
        - tables: GitHub-style tables
        - fenced_code: Code blocks with language hints
        - nl2br: Markdown line breaks → HTML <br>
        - sane_lists: Better list handling

        Args:
            markdown_content: Markdown text

        Returns:
            HTML string (Confluence storage format)
        """
        html = md_lib.markdown(
            markdown_content,
            extensions=[
                'markdown.extensions.tables',
                'markdown.extensions.fenced_code',
                'markdown.extensions.nl2br',
                'markdown.extensions.sane_lists'
            ]
        )

        return html

    def _find_page_by_title(self, space_key: str, title: str) -> Optional[Dict]:
        """
        Find page by title using search

        Args:
            space_key: Confluence space key
            title: Page title to search for

        Returns:
            Page dict if found, None otherwise
        """
        try:
            # Use text search (search_content expects text, not CQL title)
            # Search for the title as text content
            search_results = self.client.search_content(
                query=title,
                space_key=space_key
            )

            if not search_results or len(search_results) == 0:
                return None

            # Filter results for exact title match (search returns partial matches)
            for result in search_results:
                if result.get('title') == title:
                    # Found exact match
                    return result

            # No exact match found
            return None

        except Exception as e:
            logger.warning(f"Page search failed: {space_key}/{title} - {e}")
            return None

    def _extract_page_url(self, page_response: Dict) -> str:
        """
        Extract page URL from API response (handles multiple formats)

        The Confluence API returns URLs in different formats:
        - ReliableConfluenceClient format: response['url'] (direct URL)
        - Modern: response['_links']['webui']
        - Legacy: response['webui']
        - Fallback: Construct from page ID

        Args:
            page_response: API response dict

        Returns:
            Full page URL

        Raises:
            ValueError: If URL cannot be extracted
        """
        # Try ReliableConfluenceClient format first (has 'url' key directly)
        if 'url' in page_response:
            return page_response['url']

        base_url = self.config.get("url", "https://vivoemc.atlassian.net/wiki")

        # Try modern format
        if '_links' in page_response and 'webui' in page_response['_links']:
            relative_url = page_response['_links']['webui']
            return f"{base_url}{relative_url}"

        # Try legacy format
        if 'webui' in page_response:
            relative_url = page_response['webui']
            return f"{base_url}{relative_url}"

        # Construct from page ID if available
        if 'id' in page_response:
            page_id = page_response['id']
            return f"{base_url}/pages/{page_id}"

        # Unable to extract URL
        available_keys = list(page_response.keys())
        raise ValueError(
            f"Unable to extract URL from response. "
            f"Available keys: {available_keys}. "
            f"Expected 'url', '_links.webui', 'webui', or 'id'."
        )

    def _load_site_config(self, site_name: str) -> Dict:
        """
        Load site configuration from config file

        Config file: ~/.maia/confluence_sites.json
        Format:
            {
                "default": {
                    "url": "https://vivoemc.atlassian.net/wiki",
                    "auth": "env:CONFLUENCE_API_TOKEN",
                    "primary": true
                },
                "orro": {
                    "url": "https://orro.atlassian.net/wiki",
                    "auth": "env:ORRO_CONFLUENCE_TOKEN",
                    "primary": false
                }
            }

        Args:
            site_name: Site identifier to load

        Returns:
            Site configuration dict

        Fallback: If file missing or site not found, returns hardcoded default
        """
        config_path = Path.home() / ".maia" / "confluence_sites.json"

        # If config file doesn't exist, use hardcoded default
        if not config_path.exists():
            logger.info(f"Config file not found: {config_path}, using default")
            return {
                "url": "https://vivoemc.atlassian.net/wiki",
                "auth": "env:CONFLUENCE_API_TOKEN",
                "primary": True
            }

        # Load config file
        try:
            with open(config_path) as f:
                all_configs = json.load(f)

            # Get requested site, fallback to default if not found
            config = all_configs.get(site_name, all_configs.get("default", {}))

            if not config:
                logger.warning(f"Site '{site_name}' not found in config, using default")
                return {
                    "url": "https://vivoemc.atlassian.net/wiki",
                    "auth": "env:CONFLUENCE_API_TOKEN",
                    "primary": True
                }

            return config

        except Exception as e:
            logger.warning(f"Failed to load config: {e}, using default")
            return {
                "url": "https://vivoemc.atlassian.net/wiki",
                "auth": "env:CONFLUENCE_API_TOKEN",
                "primary": True
            }

    def _format_error_message(
        self,
        operation: str,
        space_key: str,
        title: str,
        original_error: Exception
    ) -> str:
        """
        Format clear, actionable error message

        Args:
            operation: Operation that failed (e.g., "create page")
            space_key: Confluence space key
            title: Page title
            original_error: Original exception

        Returns:
            Formatted error message with context and suggestions
        """
        error_str = str(original_error)

        # Check for common error patterns
        if "404" in error_str or "not found" in error_str.lower():
            suggestion = f"Verify space key '{space_key}' exists with list_spaces()"
        elif "403" in error_str or "forbidden" in error_str.lower():
            suggestion = "Check authentication token and permissions"
        elif "401" in error_str or "unauthorized" in error_str.lower():
            suggestion = "Verify CONFLUENCE_API_TOKEN environment variable is set"
        elif "503" in error_str or "unavailable" in error_str.lower():
            suggestion = "Confluence service temporarily unavailable, retry in 60 seconds"
        else:
            suggestion = "Check Confluence API status and network connectivity"

        return (
            f"Failed to {operation} '{title}' in space '{space_key}'\n"
            f"Reason: {error_str}\n"
            f"Suggestion: {suggestion}"
        )


# ============================================================================
# CLI INTERFACE (for testing)
# ============================================================================

if __name__ == "__main__":
    import sys

    # Simple CLI for testing
    if len(sys.argv) < 2:
        print("Usage: python confluence_client.py <command>")
        print("Commands:")
        print("  list-spaces          - List all accessible spaces")
        print("  create <space> <title> <file.md> - Create page from markdown file")
        print("  get-url <space> <title>  - Get page URL by title")
        sys.exit(1)

    command = sys.argv[1]
    client = ConfluenceClient()

    if command == "list-spaces":
        spaces = client.list_spaces()
        print(f"Found {len(spaces)} accessible spaces:")
        for space in spaces:
            print(f"  - {space['key']}: {space['name']}")

    elif command == "create" and len(sys.argv) == 5:
        space_key = sys.argv[2]
        title = sys.argv[3]
        md_file = sys.argv[4]

        with open(md_file) as f:
            markdown_content = f.read()

        url = client.create_page_from_markdown(space_key, title, markdown_content)
        print(f"✅ Page created: {url}")

    elif command == "get-url" and len(sys.argv) == 4:
        space_key = sys.argv[2]
        title = sys.argv[3]

        url = client.get_page_url(space_key, title)
        if url:
            print(f"✅ Page found: {url}")
        else:
            print(f"❌ Page not found: {space_key}/{title}")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
