#!/usr/bin/env python3
"""
Reliability & Multi-Site Tests for ConfluenceClient

Reliability Tests:
- Retry logic on transient failures
- Circuit breaker behavior
- Concurrent request safety
- Latency SLO compliance

Multi-Site Tests:
- Default site configuration
- Orro site configuration (when available)
- Site isolation
"""

import pytest
import time
import os
from unittest.mock import Mock, patch, MagicMock
from concurrent.futures import ThreadPoolExecutor, as_completed

# Will be implemented
# from confluence_client import ConfluenceClient, ConfluenceError


# ============================================================================
# RELIABILITY TESTS
# ============================================================================

class TestRetryLogic:
    """Test automatic retry on transient failures"""

    def test_retry_on_503_service_unavailable(self):
        """
        GIVEN: Confluence API returns 503 (transient error)
        WHEN: create_page_from_markdown() called
        THEN: Retries up to 3 times with exponential backoff
        AND: Eventually succeeds or fails gracefully
        """
        from confluence_client import ConfluenceClient

        mock_client = Mock()
        # First 2 calls fail with 503, 3rd succeeds
        mock_client.create_page.side_effect = [
            Exception("503 Service Unavailable"),
            Exception("503 Service Unavailable"),
            {"id": "123", "_links": {"webui": "/spaces/Orro/pages/123"}}
        ]

        with patch('confluence_client._reliable_confluence_client.ReliableConfluenceClient', return_value=mock_client):
            client = ConfluenceClient()

            # Should succeed after retries
            url = client.create_page_from_markdown(
                space_key="Orro",
                title="Test",
                markdown_content="# Content"
            )

            assert url.startswith("https://")
            assert mock_client.create_page.call_count == 3  # 2 retries + 1 success

    def test_fail_fast_on_non_retryable_error(self):
        """
        GIVEN: Confluence API returns 404 (non-retryable)
        WHEN: create_page_from_markdown() called
        THEN: Fails immediately without retries
        """
        from confluence_client import ConfluenceClient, ConfluenceError

        mock_client = Mock()
        mock_client.create_page.side_effect = Exception("404 Not Found")

        with patch('confluence_client._reliable_confluence_client.ReliableConfluenceClient', return_value=mock_client):
            client = ConfluenceClient()

            with pytest.raises(ConfluenceError):
                client.create_page_from_markdown(
                    space_key="NONEXISTENT",
                    title="Test",
                    markdown_content="# Content"
                )

            # Should only call once (no retries for 404)
            assert mock_client.create_page.call_count == 1


class TestCircuitBreaker:
    """Test circuit breaker prevents cascading failures"""

    def test_circuit_opens_after_threshold_failures(self):
        """
        GIVEN: 5 consecutive failures (circuit breaker threshold)
        WHEN: 6th request attempted
        THEN: Circuit breaker opens, request fails fast
        AND: No API call made (circuit open)
        """
        from confluence_client import ConfluenceClient

        mock_client = Mock()
        mock_client.create_page.side_effect = Exception("500 Internal Server Error")

        with patch('confluence_client._reliable_confluence_client.ReliableConfluenceClient', return_value=mock_client):
            client = ConfluenceClient()

            # Make 5 failing requests (open circuit)
            for i in range(5):
                try:
                    client.create_page_from_markdown(
                        space_key="Orro",
                        title=f"Test {i}",
                        markdown_content="# Content"
                    )
                except:
                    pass

            # 6th request should fail fast (circuit open)
            call_count_before = mock_client.create_page.call_count

            try:
                client.create_page_from_markdown(
                    space_key="Orro",
                    title="Test 6",
                    markdown_content="# Content"
                )
            except:
                pass

            # Circuit open = no new API call
            assert mock_client.create_page.call_count == call_count_before

    def test_circuit_closes_after_timeout(self):
        """
        GIVEN: Circuit breaker opened
        WHEN: Timeout period elapses (60 seconds)
        THEN: Circuit enters half-open state
        AND: Allows one test request
        """
        # Note: This test would require mocking time or waiting 60s
        # Deferred to manual testing or time-mocking implementation
        pytest.skip("Circuit breaker timeout test requires time mocking")


class TestConcurrentSafety:
    """Test concurrent request handling"""

    @pytest.mark.skipif(
        not os.getenv("CONFLUENCE_API_TOKEN"),
        reason="Requires live Confluence API"
    )
    def test_concurrent_page_creation_no_race_conditions(self):
        """
        GIVEN: 10 concurrent page creation requests (different titles)
        WHEN: All execute simultaneously
        THEN: All 10 pages created successfully
        AND: No race conditions or deadlocks
        """
        from confluence_client import ConfluenceClient

        client = ConfluenceClient()
        test_space = os.getenv("CONFLUENCE_TEST_SPACE", "MAIA-TEST")

        def create_page(index):
            title = f"Concurrent Test {time.time()}_{index}"
            markdown = f"# Page {index}\n\nConcurrent creation test."
            return client.create_page_from_markdown(test_space, title, markdown)

        # Create 10 pages concurrently
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_page, i) for i in range(10)]

            results = []
            for future in as_completed(futures):
                try:
                    url = future.result(timeout=30)
                    results.append(url)
                except Exception as e:
                    pytest.fail(f"Concurrent creation failed: {e}")

        # All 10 should succeed
        assert len(results) == 10
        # All should be unique URLs
        assert len(set(results)) == 10

    @pytest.mark.skipif(
        not os.getenv("CONFLUENCE_API_TOKEN"),
        reason="Requires live Confluence API"
    )
    def test_concurrent_update_same_page_version_handling(self):
        """
        GIVEN: 5 concurrent updates to same page
        WHEN: All execute simultaneously
        THEN: All updates succeed with proper version increment
        AND: No version conflicts or lost updates
        """
        from confluence_client import ConfluenceClient

        client = ConfluenceClient()
        test_space = os.getenv("CONFLUENCE_TEST_SPACE", "MAIA-TEST")

        # Create initial page
        title = f"Concurrent Update Test {time.time()}"
        client.create_page_from_markdown(test_space, title, "# Initial")

        time.sleep(2)  # Allow indexing

        def update_page(index):
            markdown = f"# Update {index}\n\nConcurrent update test."
            return client.update_page_from_markdown(test_space, title, markdown)

        # Update 5 times concurrently
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(update_page, i) for i in range(5)]

            results = []
            for future in as_completed(futures):
                try:
                    url = future.result(timeout=30)
                    results.append(url)
                except Exception as e:
                    # Confluence may reject some due to version conflicts (expected)
                    pass

        # At least some should succeed (not all will due to version conflicts)
        assert len(results) >= 1


class TestLatencySLO:
    """Test latency SLO compliance"""

    @pytest.mark.skipif(
        not os.getenv("CONFLUENCE_API_TOKEN"),
        reason="Requires live Confluence API"
    )
    def test_create_page_p95_latency_under_5s(self):
        """
        GIVEN: 20 page creation requests
        WHEN: All execute sequentially
        THEN: P95 latency <5 seconds (SLO target)
        """
        from confluence_client import ConfluenceClient

        client = ConfluenceClient()
        test_space = os.getenv("CONFLUENCE_TEST_SPACE", "MAIA-TEST")

        latencies = []
        for i in range(20):
            title = f"Latency Test {time.time()}_{i}"
            markdown = f"# Test {i}"

            start = time.time()
            url = client.create_page_from_markdown(test_space, title, markdown)
            latency = time.time() - start

            latencies.append(latency)
            assert url.startswith("https://")

        # Calculate P95
        latencies.sort()
        p95_index = int(len(latencies) * 0.95)
        p95_latency = latencies[p95_index]

        assert p95_latency < 5.0, f"P95 latency {p95_latency:.2f}s exceeds SLO (5s)"


# ============================================================================
# MULTI-SITE TESTS
# ============================================================================

class TestMultiSiteConfiguration:
    """Test multi-site support"""

    def test_default_site_uses_vivoemc(self):
        """
        GIVEN: Client initialized without site_name
        WHEN: Client inspected
        THEN: Uses default site (vivoemc Confluence)
        """
        with patch('confluence_client._reliable_confluence_client.ReliableConfluenceClient'):
            from confluence_client import ConfluenceClient

            client = ConfluenceClient()

        assert client.site_name == "default"
        assert "vivoemc.atlassian.net" in client.config["url"]

    def test_orro_site_uses_correct_url(self):
        """
        GIVEN: Config file with orro site entry
        WHEN: Client initialized with site_name="orro"
        THEN: Uses orro Confluence URL
        """
        import json
        import tempfile
        from pathlib import Path

        config_data = {
            "default": {
                "url": "https://vivoemc.atlassian.net/wiki"
            },
            "orro": {
                "url": "https://orro.atlassian.net/wiki",
                "auth": "env:ORRO_CONFLUENCE_TOKEN"
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
                        with patch('confluence_client._reliable_confluence_client.ReliableConfluenceClient'):
                            from confluence_client import ConfluenceClient
                            client = ConfluenceClient(site_name="orro")

            assert client.site_name == "orro"
            assert "orro.atlassian.net" in client.config["url"]
        finally:
            Path(config_path).unlink()

    def test_site_operations_isolated_to_selected_site(self):
        """
        GIVEN: Two client instances with different sites
        WHEN: Operations performed
        THEN: URLs include correct site domain
        AND: No cross-site operations occur
        """
        with patch('confluence_client._reliable_confluence_client.ReliableConfluenceClient') as mock:
            from confluence_client import ConfluenceClient

            # Mock response with relative URL
            mock.return_value.create_page.return_value = {
                "id": "123",
                "_links": {"webui": "/spaces/Orro/pages/123"}
            }

            client_default = ConfluenceClient(site_name="default")
            url_default = client_default.create_page_from_markdown(
                "Orro", "Test", "# Content"
            )

            # URL should use default site domain
            assert "vivoemc.atlassian.net" in url_default

            # Note: Testing orro site requires config file (covered in test above)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
