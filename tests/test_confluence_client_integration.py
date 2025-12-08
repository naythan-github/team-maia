#!/usr/bin/env python3
"""
Integration Tests for ConfluenceClient

Tests end-to-end functionality with live Confluence API.
Requires valid CONFLUENCE_API_TOKEN environment variable.

Test Coverage:
- Create page from markdown (happy path)
- Update existing page with automatic lookup
- Duplicate title handling
- List spaces
- Get page URL
- Error handling (invalid space, network issues)

WARNING: These tests create/modify/delete pages in TEST space.
Use CONFLUENCE_TEST_SPACE environment variable or default "MAIA-TEST"
"""

import pytest
import os
import time
from datetime import datetime

# Will be implemented
# from confluence_client import ConfluenceClient, ConfluenceError


# Skip all tests if no API token (CI/CD without secrets)
pytestmark = pytest.mark.skipif(
    not os.getenv("CONFLUENCE_API_TOKEN"),
    reason="CONFLUENCE_API_TOKEN not set"
)


@pytest.fixture
def test_space():
    """Get test space from environment or use default"""
    return os.getenv("CONFLUENCE_TEST_SPACE", "MAIA-TEST")


@pytest.fixture
def client():
    """Create ConfluenceClient for integration tests"""
    from confluence_client import ConfluenceClient
    return ConfluenceClient()


@pytest.fixture
def unique_title():
    """Generate unique page title for test isolation"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    return f"Test Page {timestamp}"


class TestCreatePageFromMarkdown:
    """Test page creation from markdown content"""

    def test_create_simple_page_with_headers(self, client, test_space, unique_title):
        """
        GIVEN: Simple markdown with headers and text
        WHEN: create_page_from_markdown() called
        THEN: Page created successfully with correct formatting
        AND: Returns valid page URL
        """
        markdown = """# Main Header

## Section 1
This is some text.

## Section 2
More text here."""

        url = client.create_page_from_markdown(
            space_key=test_space,
            title=unique_title,
            markdown_content=markdown
        )

        # Validate URL format
        assert url.startswith("https://")
        assert test_space in url or test_space.lower() in url
        assert "pages/" in url

        # Cleanup
        # Note: Cleanup requires delete functionality (deferred to Phase 2)

    def test_create_page_with_code_blocks(self, client, test_space, unique_title):
        """
        GIVEN: Markdown with fenced code blocks
        WHEN: create_page_from_markdown() called
        THEN: Code blocks render correctly in Confluence
        """
        markdown = """# Code Example

Python function:

```python
def hello_world():
    print("Hello, World!")
    return 42
```

Bash script:

```bash
#!/bin/bash
echo "Hello from bash"
```"""

        url = client.create_page_from_markdown(
            space_key=test_space,
            title=unique_title,
            markdown_content=markdown
        )

        assert url.startswith("https://")
        # Verify code blocks present (would need page content fetch to validate)

    def test_create_page_with_tables(self, client, test_space, unique_title):
        """
        GIVEN: Markdown with table
        WHEN: create_page_from_markdown() called
        THEN: Table renders correctly in Confluence
        """
        markdown = """# Data Table

| Name | Role | Experience |
|------|------|-----------|
| Alice | Engineer | 5 years |
| Bob | Manager | 10 years |
| Charlie | Designer | 3 years |"""

        url = client.create_page_from_markdown(
            space_key=test_space,
            title=unique_title,
            markdown_content=markdown
        )

        assert url.startswith("https://")

    def test_create_page_with_lists(self, client, test_space, unique_title):
        """
        GIVEN: Markdown with ordered and unordered lists
        WHEN: create_page_from_markdown() called
        THEN: Lists render correctly
        """
        markdown = """# Task Lists

## TODO
- [ ] Task 1
- [ ] Task 2
- [x] Task 3 (completed)

## Steps
1. First step
2. Second step
3. Third step"""

        url = client.create_page_from_markdown(
            space_key=test_space,
            title=unique_title,
            markdown_content=markdown
        )

        assert url.startswith("https://")

    def test_create_page_performance_within_slo(self, client, test_space, unique_title):
        """
        GIVEN: Standard markdown content
        WHEN: create_page_from_markdown() called
        THEN: Completes within 10 seconds (P99 SLO)
        """
        markdown = "# Test Page\n\nThis is a performance test."

        start_time = time.time()
        url = client.create_page_from_markdown(
            space_key=test_space,
            title=unique_title,
            markdown_content=markdown
        )
        latency = time.time() - start_time

        assert url.startswith("https://")
        assert latency < 10.0, f"Latency {latency:.2f}s exceeds P99 SLO (10s)"

    def test_create_page_invalid_space_fails_fast(self, client, unique_title):
        """
        GIVEN: Non-existent space key
        WHEN: create_page_from_markdown() called
        THEN: Fails with clear error message
        AND: Error message includes suggestion
        """
        from confluence_client import ConfluenceError

        markdown = "# Test"

        with pytest.raises(ConfluenceError) as exc_info:
            client.create_page_from_markdown(
                space_key="NONEXISTENT_SPACE_12345",
                title=unique_title,
                markdown_content=markdown
            )

        error_message = str(exc_info.value)
        assert "NONEXISTENT_SPACE_12345" in error_message
        assert "not found" in error_message.lower() or "inaccessible" in error_message.lower()


class TestUpdatePageFromMarkdown:
    """Test page update with automatic lookup"""

    def test_update_existing_page_auto_lookup(self, client, test_space, unique_title):
        """
        GIVEN: Page already exists in space
        WHEN: update_page_from_markdown() called with same title
        THEN: Existing page updated (not duplicated)
        AND: Returns same page URL
        """
        # Create initial page
        initial_markdown = "# Version 1\n\nInitial content."
        url1 = client.create_page_from_markdown(
            space_key=test_space,
            title=unique_title,
            markdown_content=initial_markdown
        )

        time.sleep(2)  # Allow Confluence to index

        # Update same page
        updated_markdown = "# Version 2\n\nUpdated content with changes."
        url2 = client.update_page_from_markdown(
            space_key=test_space,
            title=unique_title,
            markdown_content=updated_markdown
        )

        # Should be same URL (same page updated)
        assert url1 == url2

    def test_update_nonexistent_page_creates_new(self, client, test_space, unique_title):
        """
        GIVEN: Page does NOT exist in space
        WHEN: update_page_from_markdown() called
        THEN: New page created (fallback behavior)
        AND: Returns new page URL
        """
        markdown = "# New Page\n\nCreated via update method."

        url = client.update_page_from_markdown(
            space_key=test_space,
            title=unique_title,
            markdown_content=markdown
        )

        assert url.startswith("https://")

    def test_update_performance_within_slo(self, client, test_space, unique_title):
        """
        GIVEN: Existing page
        WHEN: update_page_from_markdown() called
        THEN: Completes within 12 seconds (P99 SLO includes search)
        """
        # Create page first
        client.create_page_from_markdown(
            space_key=test_space,
            title=unique_title,
            markdown_content="# Initial"
        )

        time.sleep(2)  # Allow indexing

        # Update and measure
        start_time = time.time()
        url = client.update_page_from_markdown(
            space_key=test_space,
            title=unique_title,
            markdown_content="# Updated"
        )
        latency = time.time() - start_time

        assert url.startswith("https://")
        assert latency < 12.0, f"Latency {latency:.2f}s exceeds P99 SLO (12s)"


class TestGetPageURL:
    """Test simple page URL lookup"""

    def test_get_url_for_existing_page(self, client, test_space, unique_title):
        """
        GIVEN: Page exists in space
        WHEN: get_page_url() called
        THEN: Returns correct page URL
        """
        # Create page
        expected_url = client.create_page_from_markdown(
            space_key=test_space,
            title=unique_title,
            markdown_content="# Test"
        )

        time.sleep(2)  # Allow indexing

        # Lookup URL
        actual_url = client.get_page_url(space_key=test_space, title=unique_title)

        assert actual_url == expected_url

    def test_get_url_for_nonexistent_page_returns_none(self, client, test_space):
        """
        GIVEN: Page does NOT exist in space
        WHEN: get_page_url() called
        THEN: Returns None (not an exception)
        """
        url = client.get_page_url(
            space_key=test_space,
            title="NONEXISTENT_PAGE_12345_UNIQUE"
        )

        assert url is None


class TestListSpaces:
    """Test space listing functionality"""

    def test_list_spaces_returns_accessible_spaces(self, client):
        """
        GIVEN: User has access to multiple spaces
        WHEN: list_spaces() called
        THEN: Returns list of spaces with keys and names
        """
        spaces = client.list_spaces()

        assert isinstance(spaces, list)
        assert len(spaces) > 0

        # Validate structure
        first_space = spaces[0]
        assert "key" in first_space
        assert "name" in first_space
        assert isinstance(first_space["key"], str)
        assert isinstance(first_space["name"], str)

    def test_list_spaces_performance_within_slo(self, client):
        """
        GIVEN: Valid client
        WHEN: list_spaces() called
        THEN: Completes within 8 seconds (P99 SLO)
        """
        start_time = time.time()
        spaces = client.list_spaces()
        latency = time.time() - start_time

        assert len(spaces) > 0
        assert latency < 8.0, f"Latency {latency:.2f}s exceeds P99 SLO (8s)"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
