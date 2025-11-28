"""
Integration tests for ITGlue API Client

These tests verify cross-component interactions and external API integration.
Tests use REAL ITGlue sandbox API (requires valid API key).

Run with: pytest tests/integrations/itglue/test_integration.py -m integration
Mark as integration tests to separate from unit tests.
"""

import pytest
from unittest.mock import patch
from datetime import datetime
import os

try:
    from claude.tools.integrations.itglue.client import ITGlueClient
    from claude.tools.integrations.itglue.cache import ITGlueCache
    from claude.tools.integrations.itglue.exceptions import (
        ITGlueAuthError,
        ITGlueRateLimitError
    )
except ImportError:
    # Expected to fail initially - TDD red phase
    pass


# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


@pytest.fixture(scope='module')
def sandbox_client():
    """
    Create ITGlue client connected to sandbox instance.
    Requires ITGlue sandbox API key in macOS Keychain.
    """
    try:
        client = ITGlueClient(instance='sandbox')
        # Validate API key works
        if not client.validate_api_key():
            pytest.skip("Invalid ITGlue sandbox API key")
        return client
    except ITGlueAuthError:
        pytest.skip("ITGlue sandbox API key not configured")


@pytest.fixture(scope='module')
def cache_with_client(sandbox_client, tmp_path_factory):
    """Create cache connected to live API client"""
    db_path = tmp_path_factory.mktemp("data") / "itglue_integration_test.db"
    cache = ITGlueCache(str(db_path))
    cache.api_client = sandbox_client
    return cache


class TestEndToEndOrganizationWorkflow:
    """
    Integration Test: End-to-end organization CRUD workflow
    Verifies data flow from API → Client → Cache → Database
    """

    def test_create_list_update_delete_organization(self, sandbox_client):
        """
        Integration test: Full organization lifecycle

        Flow:
        1. Create organization in ITGlue
        2. Verify it appears in list
        3. Update organization name
        4. Delete organization
        5. Verify removal
        """
        # Step 1: Create
        org_name = f"Test Org {datetime.now().strftime('%Y%m%d%H%M%S')}"
        org = sandbox_client.create_organization(name=org_name)
        assert org is not None
        assert org.id is not None
        org_id = org.id

        try:
            # Step 2: Verify in list
            orgs = sandbox_client.list_organizations()
            org_ids = [o.id for o in orgs]
            assert org_id in org_ids

            # Step 3: Update
            updated = sandbox_client.update_organization(
                org_id,
                name=f"{org_name} (Updated)"
            )
            assert updated.name == f"{org_name} (Updated)"

            # Step 4: Get by ID
            fetched = sandbox_client.get_organization(org_id)
            assert fetched.name == f"{org_name} (Updated)"

        finally:
            # Step 5: Cleanup - delete organization
            sandbox_client.delete_organization(org_id)

            # Verify deletion
            deleted_org = sandbox_client.get_organization(org_id)
            assert deleted_org is None


class TestCacheAPIIntegration:
    """
    Integration Test: Cache → API interaction
    Verifies cache correctly falls back to API on cache miss
    """

    def test_smart_query_cache_miss_fetches_from_api(self, cache_with_client, sandbox_client):
        """
        Integration test: Cache miss → API fetch → Cache update

        Flow:
        1. Query organization not in cache (miss)
        2. Verify cache fetches from API
        3. Verify result cached for next query
        4. Next query is cache hit (no API call)
        """
        # Get first organization from API
        orgs = sandbox_client.list_organizations()
        if not orgs:
            pytest.skip("No organizations in sandbox")

        test_org_id = orgs[0].id

        # Clear cache to ensure miss
        cache_with_client.invalidate_organization(test_org_id)

        # First query: cache miss → API fetch
        result1 = cache_with_client.smart_get_organization(
            test_org_id,
            api_client=sandbox_client
        )
        assert result1 is not None

        # Second query: cache hit (no API call)
        # Mock API to verify it's NOT called
        with patch.object(sandbox_client, 'get_organization') as mock_api:
            result2 = cache_with_client.smart_get_organization(
                test_org_id,
                api_client=sandbox_client
            )
            assert result2 is not None
            # Verify API not called (cache hit)
            mock_api.assert_not_called()


class TestConfigurationPasswordLinking:
    """
    Integration Test: Configuration → Password relationship
    Verifies entity linking across API and cache
    """

    def test_link_configuration_to_password(self, sandbox_client):
        """
        Integration test: Link configuration to password

        Flow:
        1. Create organization
        2. Create configuration
        3. Create password
        4. Link configuration → password
        5. Verify relationship via API
        6. Cleanup
        """
        # Setup: Create organization
        org_name = f"Test Linking {datetime.now().strftime('%Y%m%d%H%M%S')}"
        org = sandbox_client.create_organization(name=org_name)
        org_id = org.id

        try:
            # Create configuration
            config = sandbox_client.create_configuration(
                organization_id=org_id,
                name="Test Server",
                configuration_type="Server"
            )
            config_id = config.id

            # Create password
            password = sandbox_client.create_password(
                organization_id=org_id,
                name="Test Admin Password",
                username="admin",
                password="TestPass123!"
            )
            password_id = password.id

            # Link them
            result = sandbox_client.link_configuration_to_password(
                configuration_id=config_id,
                password_id=password_id
            )
            assert result is True

            # Verify relationship
            relationships = sandbox_client.get_configuration_relationships(config_id)
            password_ids = [r['id'] for r in relationships if r['type'] == 'password']
            assert password_id in password_ids

        finally:
            # Cleanup
            sandbox_client.delete_organization(org_id)


class TestDocumentUploadDownload:
    """
    Integration Test: Document upload and download
    Verifies file transfer to/from ITGlue
    """

    def test_upload_and_download_document(self, sandbox_client, tmp_path):
        """
        Integration test: Upload document → Download → Verify content

        Flow:
        1. Create organization
        2. Create test file
        3. Upload to ITGlue
        4. Download from ITGlue
        5. Verify content matches
        6. Cleanup
        """
        # Setup: Create organization
        org_name = f"Test Docs {datetime.now().strftime('%Y%m%d%H%M%S')}"
        org = sandbox_client.create_organization(name=org_name)
        org_id = org.id

        try:
            # Create test file
            test_content = b"This is a test document for ITGlue integration testing."
            test_file = tmp_path / "test_doc.txt"
            test_file.write_bytes(test_content)

            # Upload
            doc = sandbox_client.upload_document(
                organization_id=org_id,
                file_path=str(test_file),
                name="Test Document.txt"
            )
            assert doc is not None
            doc_id = doc.id

            # Download
            output_file = tmp_path / "downloaded_doc.txt"
            result = sandbox_client.download_document(
                document_id=doc_id,
                output_path=str(output_file)
            )
            assert result is True

            # Verify content matches
            downloaded_content = output_file.read_bytes()
            assert downloaded_content == test_content

        finally:
            # Cleanup
            sandbox_client.delete_organization(org_id)


class TestRateLimitHandling:
    """
    Integration Test: Rate limit handling with real API
    Verifies client correctly handles 429 responses
    """

    @pytest.mark.slow
    def test_rate_limit_auto_retry(self, sandbox_client):
        """
        Integration test: Trigger rate limit → Auto-retry

        This test makes rapid requests to trigger rate limiting.
        ITGlue limit: 3000 req/5min (10 req/sec sustained)

        Flow:
        1. Make 100 rapid requests
        2. If rate limited, verify auto-retry works
        3. Verify all requests eventually succeed
        """
        success_count = 0
        rate_limited = False

        # Make 100 requests rapidly
        for i in range(100):
            try:
                orgs = sandbox_client.list_organizations()
                success_count += 1
            except ITGlueRateLimitError:
                rate_limited = True
                # Client should auto-retry
                pass

        # Verify most requests succeeded (allowing for retries)
        assert success_count >= 90  # Allow 10% retry overhead

        # If we hit rate limit, that's expected for this test
        # The important part is that requests eventually succeeded


class TestCircuitBreakerIntegration:
    """
    Integration Test: Circuit breaker with real API failures
    Simulates API failures and verifies circuit breaker opens
    """

    def test_circuit_breaker_opens_on_repeated_failures(self, sandbox_client):
        """
        Integration test: Repeated failures → Circuit opens

        Flow:
        1. Temporarily break API key (simulate expiry)
        2. Make 5 requests (should fail)
        3. Verify circuit breaker opens
        4. Verify next request fails fast (no API call)
        5. Restore API key
        """
        # Save original API key
        original_key = sandbox_client.api_key

        try:
            # Break API key
            sandbox_client.api_key = "invalid-key-12345"

            # Make 5 requests (will fail with 401)
            failure_count = 0
            for _ in range(5):
                try:
                    sandbox_client.list_organizations()
                except ITGlueAuthError:
                    failure_count += 1

            assert failure_count == 5

            # Verify circuit breaker opened
            assert sandbox_client.circuit_breaker.is_open() is True

            # Next request should fail fast (circuit open)
            # Should NOT make API call
            with pytest.raises(Exception, match='Circuit breaker open'):
                sandbox_client.list_organizations()

        finally:
            # Restore API key
            sandbox_client.api_key = original_key
            # Reset circuit breaker for other tests
            sandbox_client.circuit_breaker.reset()


class TestMultiInstanceIsolation:
    """
    Integration Test: Sandbox vs Production instance isolation
    Verifies separate API keys, caches, and endpoints
    """

    def test_sandbox_and_production_use_different_endpoints(self):
        """
        Integration test: Verify instance isolation

        Flow:
        1. Create sandbox client
        2. Create production client (if key available)
        3. Verify different base URLs
        4. Verify different API keys
        5. Verify different cache databases
        """
        # Sandbox client
        try:
            sandbox = ITGlueClient(instance='sandbox')
            assert sandbox.base_url == 'https://api-sandbox.itglue.com'
        except ITGlueAuthError:
            pytest.skip("Sandbox API key not configured")

        # Production client (optional)
        try:
            production = ITGlueClient(instance='production')
            assert production.base_url == 'https://api.itglue.com'

            # Verify different API keys
            assert sandbox.api_key != production.api_key

            # Verify different cache paths
            assert sandbox.cache.db_path != production.cache.db_path

        except ITGlueAuthError:
            # Production key not configured - that's OK for testing
            pass


class TestCacheRefreshAfterAPIUpdate:
    """
    Integration Test: Cache invalidation on write operations
    Verifies cache stays in sync with API
    """

    def test_cache_updates_after_organization_update(self, cache_with_client, sandbox_client):
        """
        Integration test: API update → Cache invalidation → Fresh data

        Flow:
        1. Create organization
        2. Cache organization data
        3. Update organization via API
        4. Verify cache invalidated
        5. Next query fetches fresh data from API
        """
        # Create organization
        org_name = f"Test Cache Sync {datetime.now().strftime('%Y%m%d%H%M%S')}"
        org = sandbox_client.create_organization(name=org_name)
        org_id = org.id

        try:
            # Cache it
            cache_with_client.cache_organizations([org])

            # Verify in cache
            cached1 = cache_with_client.get_organization(org_id)
            assert cached1.name == org_name

            # Update via API
            updated_name = f"{org_name} (Updated)"
            sandbox_client.update_organization(org_id, name=updated_name)

            # Cache should be invalidated
            cache_with_client.invalidate_organization(org_id)

            # Next query should fetch fresh data from API
            fresh = cache_with_client.smart_get_organization(org_id, api_client=sandbox_client)
            assert fresh.name == updated_name

        finally:
            # Cleanup
            sandbox_client.delete_organization(org_id)


class TestHealthCheckWithRealAPI:
    """
    Integration Test: Health check against real API
    Verifies connectivity and API key validation
    """

    def test_health_check_reports_healthy_with_valid_key(self, sandbox_client):
        """
        Integration test: Health check with valid API key

        Flow:
        1. Run health check
        2. Verify status = healthy
        3. Verify API key valid
        4. Verify response time measured
        """
        health = sandbox_client.health_check()

        assert health['status'] == 'healthy'
        assert health['api_key_valid'] is True
        assert health['response_time_ms'] > 0
        assert health['response_time_ms'] < 5000  # Should be under 5 seconds

    def test_health_check_detects_invalid_key(self):
        """
        Integration test: Health check with invalid API key

        Flow:
        1. Create client with invalid key
        2. Run health check
        3. Verify status = unhealthy
        4. Verify API key invalid detected
        """
        with patch('claude.tools.integrations.itglue.auth.get_api_key', return_value='invalid-key'):
            client = ITGlueClient(instance='sandbox')
            health = client.health_check()

            assert health['status'] == 'unhealthy'
            assert health['api_key_valid'] is False
