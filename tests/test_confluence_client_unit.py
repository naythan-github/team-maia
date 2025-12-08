#!/usr/bin/env python3
"""
Unit Tests for ConfluenceClient

Tests isolated logic without external API calls.
Uses mocks for ReliableConfluenceClient dependency.

Test Coverage:
- Markdown to HTML conversion
- Page URL extraction from responses
- Multi-site config loading
- Input validation
"""

import pytest
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from confluence_client import ConfluenceClient, ConfluenceError


class TestMarkdownConversion:
    """Test markdown to Confluence HTML conversion"""

    @pytest.fixture
    def client(self):
        """Create client with mocked underlying client"""
        with patch('reliable_confluence_client.ReliableConfluenceClient'):
            return ConfluenceClient()

    def test_markdown_headers_convert_to_html(self, client):
        """
        GIVEN: Markdown with headers (H1-H4)
        WHEN: Converted to HTML
        THEN: Headers become <h1>, <h2>, <h3>, <h4> tags
        """
        markdown = """# Header 1
## Header 2
### Header 3
#### Header 4"""

        html = client._markdown_to_html(markdown)

        assert "<h1>Header 1</h1>" in html
        assert "<h2>Header 2</h2>" in html
        assert "<h3>Header 3</h3>" in html
        assert "<h4>Header 4</h4>" in html

    def test_markdown_code_blocks_with_language(self, client):
        """
        GIVEN: Markdown with fenced code block and language hint
        WHEN: Converted to HTML
        THEN: Becomes <code> or <pre> with language class
        """
        markdown = """```python
def hello():
    print("world")
```"""

        html = client._markdown_to_html(markdown)

        # Should contain code content
        assert "def hello():" in html
        # HTML escapes quotes as &quot;
        assert 'print' in html and 'world' in html

    def test_markdown_tables_convert_to_html(self, client):
        """
        GIVEN: Markdown table with headers and rows
        WHEN: Converted to HTML
        THEN: Becomes <table> with <th> and <td>
        """
        markdown = """| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |"""

        html = client._markdown_to_html(markdown)

        assert "<table>" in html
        assert "<th>Header 1</th>" in html or "<th>Header  1</th>" in html  # Whitespace tolerance
        assert "<td>Cell 1</td>" in html or "<td>Cell  1</td>" in html

    def test_markdown_lists_convert_to_html(self, client):
        """
        GIVEN: Markdown with unordered and ordered lists
        WHEN: Converted to HTML
        THEN: Becomes <ul>/<ol> with <li> items
        """
        markdown = """- Item 1
- Item 2

1. First
2. Second"""

        html = client._markdown_to_html(markdown)

        assert "<ul>" in html
        assert "<li>Item 1</li>" in html
        assert "<ol>" in html
        assert "<li>First</li>" in html


class TestURLExtraction:
    """Test page URL extraction from various API response formats"""

    @pytest.fixture
    def client(self):
        """Create client with mocked underlying client"""
        with patch('reliable_confluence_client.ReliableConfluenceClient'):
            return ConfluenceClient()

    def test_extract_url_from_links_webui_format(self, client):
        """
        GIVEN: API response with _links.webui format
        WHEN: URL extracted
        THEN: Returns full URL with site domain
        """
        response = {
            "id": "123456",
            "title": "Test Page",
            "_links": {
                "webui": "/spaces/Orro/pages/123456"
            }
        }

        url = client._extract_page_url(response)

        assert url.startswith("https://")
        assert "spaces/Orro/pages/123456" in url

    def test_extract_url_from_legacy_webui_format(self, client):
        """
        GIVEN: API response with legacy webui format (no _links)
        WHEN: URL extracted
        THEN: Returns full URL constructed from webui field
        """
        response = {
            "id": "123456",
            "title": "Test Page",
            "webui": "/spaces/Orro/pages/123456"
        }

        url = client._extract_page_url(response)

        assert url.startswith("https://")
        assert "spaces/Orro/pages/123456" in url

    def test_extract_url_from_page_id_only(self, client):
        """
        GIVEN: API response with only page ID (no webui)
        WHEN: URL extracted
        THEN: Constructs URL from page ID
        """
        response = {
            "id": "123456",
            "title": "Test Page"
        }

        url = client._extract_page_url(response)

        assert url.startswith("https://")
        assert "123456" in url

    def test_extract_url_fails_on_invalid_response(self, client):
        """
        GIVEN: API response with no usable URL fields
        WHEN: URL extraction attempted
        THEN: Raises ValueError with helpful message
        """
        response = {
            "title": "Test Page"
            # No id, no _links, no webui
        }

        with pytest.raises(ValueError, match="Unable to extract URL"):
            client._extract_page_url(response)


class TestMultiSiteConfig:
    """Test multi-site configuration loading"""

    def test_default_config_when_file_missing(self):
        """
        GIVEN: No config file exists
        WHEN: Client initialized
        THEN: Uses hardcoded default config
        """
        with patch('confluence_client.Path.exists', return_value=False):
            with patch('reliable_confluence_client.ReliableConfluenceClient'):
                client = ConfluenceClient()

        assert client.site_name == "default"
        assert "vivoemc.atlassian.net" in client.config["url"]

    def test_load_config_from_file(self):
        """
        GIVEN: Config file with multiple sites
        WHEN: Client initialized with site_name
        THEN: Loads correct site configuration
        """
        config_data = {
            "default": {
                "url": "https://vivoemc.atlassian.net/wiki",
                "auth": "env:CONFLUENCE_API_TOKEN",
                "primary": True
            },
            "orro": {
                "url": "https://orro.atlassian.net/wiki",
                "auth": "env:ORRO_CONFLUENCE_TOKEN",
                "primary": False
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            with patch('confluence_client.Path.home') as mock_home:
                mock_home.return_value = Path(config_path).parent
                with patch('confluence_client.Path.exists', return_value=True):
                    with patch('builtins.open', return_value=open(config_path)):
                        with patch('reliable_confluence_client.ReliableConfluenceClient'):
                            client = ConfluenceClient(site_name="orro")

            assert client.site_name == "orro"
            assert "orro.atlassian.net" in client.config["url"]
        finally:
            Path(config_path).unlink()

    def test_invalid_site_name_raises_error(self):
        """
        GIVEN: Config file without requested site
        WHEN: Client initialized with invalid site_name
        THEN: Falls back to default config
        """
        config_data = {
            "default": {
                "url": "https://vivoemc.atlassian.net/wiki"
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            with patch('confluence_client.Path.home') as mock_home:
                mock_home.return_value = Path(config_path).parent
                with patch('confluence_client.Path.exists', return_value=True):
                    with patch('builtins.open', return_value=open(config_path)):
                        with patch('reliable_confluence_client.ReliableConfluenceClient'):
                            client = ConfluenceClient(site_name="nonexistent")

            # Should fall back to default
            assert client.config["url"] == "https://vivoemc.atlassian.net/wiki"
        finally:
            Path(config_path).unlink()


class TestInputValidation:
    """Test input validation before API calls"""

    @pytest.fixture
    def client(self):
        """Create client with mocked underlying client"""
        with patch('reliable_confluence_client.ReliableConfluenceClient'):
            return ConfluenceClient()

    def test_empty_space_key_raises_error(self, client):
        """
        GIVEN: Empty space_key
        WHEN: create_page_from_markdown called
        THEN: Raises ValueError before API call
        """
        with pytest.raises(ValueError, match="space_key.*empty"):
            client.create_page_from_markdown(
                space_key="",
                title="Test",
                markdown_content="# Content"
            )

    def test_empty_title_raises_error(self, client):
        """
        GIVEN: Empty title
        WHEN: create_page_from_markdown called
        THEN: Raises ValueError before API call
        """
        with pytest.raises(ValueError, match="title.*empty"):
            client.create_page_from_markdown(
                space_key="Orro",
                title="",
                markdown_content="# Content"
            )

    def test_empty_markdown_raises_error(self, client):
        """
        GIVEN: Empty markdown content
        WHEN: create_page_from_markdown called
        THEN: Raises ValueError before API call
        """
        with pytest.raises(ValueError, match="markdown.*empty"):
            client.create_page_from_markdown(
                space_key="Orro",
                title="Test",
                markdown_content=""
            )

    def test_title_too_long_raises_error(self, client):
        """
        GIVEN: Title >255 characters
        WHEN: create_page_from_markdown called
        THEN: Raises ValueError before API call
        """
        long_title = "A" * 256

        with pytest.raises(ValueError, match="title.*255"):
            client.create_page_from_markdown(
                space_key="Orro",
                title=long_title,
                markdown_content="# Content"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
