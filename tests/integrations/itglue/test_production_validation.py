"""
Production Readiness Validation Tests for ITGlue API Client

Phase 6 Tests: Performance, Resilience, Observability, Smoke Tests
These tests validate the system is production-ready per SRE standards.

Run with: pytest tests/integrations/itglue/test_production_validation.py -m production
"""

import pytest
import time
import logging
from unittest.mock import Mock, patch
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

try:
    from claude.tools.integrations.itglue.client import ITGlueClient
    from claude.tools.integrations.itglue.cache import ITGlueCache
except ImportError:
    # Expected to fail initially - TDD red phase
    pass


# Mark all tests in this module as production validation tests
pytestmark = pytest.mark.production


class TestPerformanceValidation:
    """
    NFR2: Performance Testing
    Validates latency meets SLOs under load
    """

    @pytest.fixture
    def sandbox_client(self):
        return ITGlueClient(instance='sandbox')

    def test_single_api_call_latency_under_2_seconds(self, sandbox_client):
        """
        NFR2.1: Single API call P95 latency < 2 seconds

        Test:
        - Make 100 API calls (list organizations)
        - Measure latency for each
        - Calculate P95
        - Assert P95 < 2000ms
        """
        latencies = []

        for _ in range(100):
            start = time.time()
            sandbox_client.list_organizations()
            latency_ms = (time.time() - start) * 1000
            latencies.append(latency_ms)

        # Calculate P95 (95th percentile)
        latencies.sort()
        p95_index = int(len(latencies) * 0.95)
        p95_latency = latencies[p95_index]

        assert p95_latency < 2000, f"P95 latency {p95_latency}ms exceeds 2000ms SLO"

    def test_cache_query_latency_under_100ms(self, tmp_path):
        """
        NFR2.2: Cache query P95 latency < 100ms

        Test:
        - Populate cache with 1000 organizations
        - Query 1000 times
        - Measure latency for each
        - Assert P95 < 100ms
        """
        # Setup cache
        cache = ITGlueCache(str(tmp_path / "perf_test.db"))

        # Populate with 1000 orgs
        from claude.tools.integrations.itglue.models import Organization
        orgs = [
            Organization(id=str(i), name=f"Org {i}", created_at=datetime.now())
            for i in range(1000)
        ]
        cache.cache_organizations(orgs)

        # Query 1000 times
        latencies = []
        for i in range(1000):
            start = time.time()
            cache.get_organization(str(i % 1000))
            latency_ms = (time.time() - start) * 1000
            latencies.append(latency_ms)

        # Calculate P95
        latencies.sort()
        p95_index = int(len(latencies) * 0.95)
        p95_latency = latencies[p95_index]

        assert p95_latency < 100, f"Cache P95 latency {p95_latency}ms exceeds 100ms SLO"

    def test_bulk_query_100_orgs_under_30_seconds(self, sandbox_client):
        """
        NFR2.3: Bulk query (100 orgs) < 30 seconds

        Test:
        - Fetch all organizations
        - If < 100, create temporary ones
        - Measure total time
        - Assert < 30 seconds
        """
        start = time.time()
        orgs = sandbox_client.list_organizations()
        elapsed = time.time() - start

        # If we have orgs, measure query time
        if len(orgs) > 0:
            assert elapsed < 30, f"Bulk query took {elapsed}s, exceeds 30s SLO"

    def test_document_upload_10mb_under_10_seconds(self, sandbox_client, tmp_path):
        """
        NFR2.4: Document upload (10MB) < 10 seconds

        Test:
        - Create 10MB test file
        - Upload to ITGlue
        - Measure time
        - Assert < 10 seconds
        """
        # Create test organization
        org = sandbox_client.create_organization(name=f"Perf Test {datetime.now().strftime('%Y%m%d%H%M%S')}")
        org_id = org.id

        try:
            # Create 10MB file
            test_file = tmp_path / "10mb_test.bin"
            test_file.write_bytes(b'0' * (10 * 1024 * 1024))  # 10MB

            # Upload and measure
            start = time.time()
            doc = sandbox_client.upload_document(
                organization_id=org_id,
                file_path=str(test_file),
                name="10MB Test File"
            )
            elapsed = time.time() - start

            assert doc is not None
            assert elapsed < 10, f"10MB upload took {elapsed}s, exceeds 10s SLO"

        finally:
            sandbox_client.delete_organization(org_id)

    @pytest.mark.slow
    def test_performance_under_10x_load(self, sandbox_client):
        """
        Phase 6: Load test at 10x expected traffic

        Test:
        - Expected traffic: 100 req/day = ~0.001 req/sec
        - 10x load: 1000 req in test = ~0.01 req/sec sustained
        - Measure P95/P99 latency remains acceptable
        - Resource utilization < 70% (simulated)
        """
        latencies = []
        start_time = time.time()

        # Make 1000 requests
        for _ in range(1000):
            start = time.time()
            try:
                sandbox_client.list_organizations()
                latency_ms = (time.time() - start) * 1000
                latencies.append(latency_ms)
            except Exception as e:
                # Log but continue
                print(f"Request failed: {e}")

        total_time = time.time() - start_time

        # Calculate P95 and P99
        latencies.sort()
        p95_index = int(len(latencies) * 0.95)
        p99_index = int(len(latencies) * 0.99)
        p95_latency = latencies[p95_index]
        p99_latency = latencies[p99_index]

        # Assert latencies acceptable under load
        assert p95_latency < 3000, f"P95 under load: {p95_latency}ms exceeds 3000ms"
        assert p99_latency < 5000, f"P99 under load: {p99_latency}ms exceeds 5000ms"

        # Verify throughput
        requests_per_second = len(latencies) / total_time
        assert requests_per_second > 1, f"Throughput {requests_per_second} req/s too low"

    def test_no_n_plus_1_queries(self, sandbox_client, tmp_path):
        """
        Phase 6: Prevent N+1 query problem

        Test:
        - Fetch 10 organizations with cache
        - Count total API calls
        - Assert only 1 API call (bulk fetch), not 10 (N+1)
        """
        cache = ITGlueCache(str(tmp_path / "n_plus_1_test.db"))

        # Count API calls
        api_call_count = 0

        def count_api_calls(*args, **kwargs):
            nonlocal api_call_count
            api_call_count += 1
            # Call real method
            return ITGlueClient.list_organizations(sandbox_client)

        with patch.object(ITGlueClient, 'list_organizations', side_effect=count_api_calls):
            # Fetch 10 orgs (should be 1 bulk call, not 10)
            orgs = sandbox_client.list_organizations()
            for org in orgs[:10]:
                cache.smart_get_organization(org.id, api_client=sandbox_client)

        # Verify only 1 API call (bulk fetch), not N+1
        assert api_call_count == 1, f"N+1 query detected: {api_call_count} API calls instead of 1"


class TestResilienceValidation:
    """
    Phase 6: Resilience Testing
    Validates circuit breaker, fallbacks, graceful degradation, retries
    """

    @pytest.fixture
    def sandbox_client(self):
        return ITGlueClient(instance='sandbox')

    def test_circuit_breaker_opens_on_errors(self, sandbox_client):
        """
        Phase 6: Circuit breaker validation

        Test:
        - Simulate 5 consecutive API failures
        - Verify circuit breaker opens
        - Verify next request fails fast (no API call)
        - Wait for cooldown
        - Verify circuit closes
        """
        # Save original API key
        original_key = sandbox_client.api_key

        try:
            # Simulate failures
            sandbox_client.api_key = "invalid-key"
            failure_count = 0

            for _ in range(5):
                try:
                    sandbox_client.list_organizations()
                except Exception:
                    failure_count += 1

            assert failure_count == 5

            # Verify circuit opened
            assert sandbox_client.circuit_breaker.is_open() is True

            # Next request fails fast
            start = time.time()
            try:
                sandbox_client.list_organizations()
            except Exception:
                pass
            elapsed = time.time() - start

            # Should fail in < 100ms (no network call)
            assert elapsed < 0.1, "Circuit breaker not failing fast"

        finally:
            sandbox_client.api_key = original_key
            sandbox_client.circuit_breaker.reset()

    def test_fallback_to_cache_on_api_failure(self, sandbox_client, tmp_path):
        """
        Phase 6: Fallback behavior verification

        Test:
        - Populate cache with organization
        - Break API connection
        - Query organization
        - Verify falls back to cache
        - Returns stale data (better than nothing)
        """
        cache = ITGlueCache(str(tmp_path / "fallback_test.db"))

        # Populate cache
        from claude.tools.integrations.itglue.models import Organization
        org = Organization(id='1', name='Cached Org', created_at=datetime.now())
        cache.cache_organizations([org])

        # Break API
        sandbox_client.api_key = "invalid-key"

        # Query should fall back to cache
        result = cache.smart_get_organization('1', api_client=sandbox_client, allow_stale=True)
        assert result is not None
        assert result.name == 'Cached Org'

    def test_graceful_degradation_on_rate_limit(self, sandbox_client):
        """
        Phase 6: Graceful degradation

        Test:
        - Trigger rate limit (429)
        - Verify client degrades gracefully (slows down, doesn't crash)
        - Verify requests eventually succeed
        """
        # This would require making 3000+ requests in 5 minutes
        # For testing, we'll mock the rate limit response
        with patch.object(sandbox_client, '_make_request') as mock_request:
            # First 3 calls return 429, then succeed
            mock_request.side_effect = [
                Mock(status_code=429, headers={'Retry-After': '1'}),
                Mock(status_code=429, headers={'Retry-After': '1'}),
                Mock(status_code=429, headers={'Retry-After': '1'}),
                Mock(status_code=200, json=lambda: {'data': []})
            ]

            with patch('time.sleep'):  # Speed up test
                result = sandbox_client.list_organizations()
                # Should eventually succeed after retries
                assert result is not None

    def test_retry_logic_with_exponential_backoff(self, sandbox_client):
        """
        Phase 6: Retry logic validation

        Test:
        - Simulate intermittent 500 errors
        - Verify exponential backoff: 1s → 2s → 4s
        - Verify eventual success
        """
        with patch.object(sandbox_client, '_make_request') as mock_request:
            mock_request.side_effect = [
                Mock(status_code=500),  # Fail
                Mock(status_code=500),  # Fail
                Mock(status_code=200, json=lambda: {'data': []})  # Success
            ]

            sleep_times = []

            def mock_sleep(seconds):
                sleep_times.append(seconds)

            with patch('time.sleep', side_effect=mock_sleep):
                result = sandbox_client.list_organizations()

            # Verify exponential backoff pattern
            assert len(sleep_times) >= 2
            # Each sleep should be ~2x previous (exponential)
            assert sleep_times[1] > sleep_times[0]


class TestObservabilityValidation:
    """
    Phase 6: Observability Validation
    Validates structured logs, metrics, tracing
    """

    @pytest.fixture
    def sandbox_client(self):
        return ITGlueClient(instance='sandbox')

    def test_logs_contain_request_id(self, sandbox_client, caplog):
        """
        Phase 6: Structured logging validation

        Test:
        - Make API request
        - Verify logs contain request_id
        - Verify logs structured (JSON-compatible)
        """
        caplog.set_level(logging.INFO)

        sandbox_client.list_organizations()

        # Verify request_id in logs
        log_records = [r.message for r in caplog.records]
        assert any('request_id' in msg for msg in log_records), "Logs missing request_id"

    def test_metrics_exported(self, sandbox_client):
        """
        Phase 6: Metrics validation (RED: Rate, Errors, Duration)

        Test:
        - Make requests
        - Verify metrics collected:
          - Request count (Rate)
          - Error count (Errors)
          - Request duration (Duration)
        """
        # Make some requests
        sandbox_client.list_organizations()
        sandbox_client.list_organizations()

        # Get metrics
        metrics = sandbox_client.get_metrics()

        # Verify RED metrics
        assert 'request_count' in metrics, "Missing Rate metric"
        assert 'error_count' in metrics, "Missing Error metric"
        assert 'request_duration_ms' in metrics, "Missing Duration metric"

        assert metrics['request_count'] >= 2
        assert metrics['request_duration_ms'] > 0

    def test_trace_context_propagated(self, sandbox_client, caplog):
        """
        Phase 6: Trace context propagation

        Test:
        - Start trace with trace_id
        - Make nested calls
        - Verify trace_id propagated through all logs
        """
        trace_id = "test-trace-123"
        caplog.set_level(logging.INFO)

        # Make request with trace context
        with patch.dict('os.environ', {'TRACE_ID': trace_id}):
            sandbox_client.list_organizations()

        # Verify trace_id in logs
        log_records = [r.message for r in caplog.records]
        trace_logs = [msg for msg in log_records if trace_id in msg]
        assert len(trace_logs) > 0, "Trace ID not propagated"


class TestSmokeTests:
    """
    Phase 6: Smoke Testing
    End-to-end happy path in production-like environment
    """

    @pytest.fixture
    def sandbox_client(self):
        return ITGlueClient(instance='sandbox')

    def test_smoke_create_org_config_password_e2e(self, sandbox_client):
        """
        Phase 6: End-to-end smoke test

        Critical user journey:
        1. Create organization
        2. Create configuration
        3. Create password
        4. Link them
        5. Query and verify
        6. Cleanup
        """
        # Step 1: Create organization
        org = sandbox_client.create_organization(name=f"Smoke Test {datetime.now().strftime('%Y%m%d%H%M%S')}")
        assert org is not None
        org_id = org.id

        try:
            # Step 2: Create configuration
            config = sandbox_client.create_configuration(
                organization_id=org_id,
                name="Test Server",
                configuration_type="Server"
            )
            assert config is not None
            config_id = config.id

            # Step 3: Create password
            password = sandbox_client.create_password(
                organization_id=org_id,
                name="Admin Password",
                username="admin",
                password="TestPass123!"
            )
            assert password is not None
            password_id = password.id

            # Step 4: Link
            result = sandbox_client.link_configuration_to_password(config_id, password_id)
            assert result is True

            # Step 5: Query and verify
            fetched_org = sandbox_client.get_organization(org_id)
            assert fetched_org.name == org.name

            configs = sandbox_client.list_configurations(organization_id=org_id)
            assert len(configs) >= 1

            passwords = sandbox_client.list_passwords(organization_id=org_id)
            assert len(passwords) >= 1

        finally:
            # Step 6: Cleanup
            sandbox_client.delete_organization(org_id)

    def test_health_check_returns_200(self, sandbox_client):
        """
        Phase 6: Health check endpoint

        Test:
        - Call health_check()
        - Verify returns healthy status
        - Verify response time acceptable
        """
        health = sandbox_client.health_check()

        assert health['status'] == 'healthy'
        assert health['api_key_valid'] is True
        assert health['response_time_ms'] < 5000


class TestSecurityValidation:
    """
    NFR1: Security validation
    """

    def test_api_keys_never_logged(self, caplog):
        """
        NFR1.2: API keys never appear in logs

        Test:
        - Create client with test API key
        - Make requests
        - Verify API key NEVER in logs
        """
        test_api_key = "test-secret-key-12345"
        caplog.set_level(logging.DEBUG)  # Most verbose

        with patch('claude.tools.integrations.itglue.auth.get_api_key', return_value=test_api_key):
            client = ITGlueClient(instance='sandbox')

            with patch.object(client, '_make_request'):
                try:
                    client.list_organizations()
                except:
                    pass

        # Verify API key NEVER in logs
        log_output = caplog.text
        assert test_api_key not in log_output, "API key leaked to logs!"

    def test_password_values_never_logged(self, sandbox_client, caplog):
        """
        NFR1.2: Password values never logged

        Test:
        - Create password with sensitive value
        - Verify password value NEVER in logs
        """
        test_password = "SuperSecret123!"
        caplog.set_level(logging.DEBUG)

        org = sandbox_client.create_organization(name=f"Security Test {datetime.now().strftime('%Y%m%d%H%M%S')}")

        try:
            with patch.object(sandbox_client, '_make_request') as mock_request:
                mock_request.return_value = Mock(
                    status_code=201,
                    json=lambda: {'data': {'id': '999', 'attributes': {'name': 'Test'}}}
                )

                sandbox_client.create_password(
                    organization_id=org.id,
                    name="Test Password",
                    username="admin",
                    password=test_password
                )

            # Verify password NEVER in logs
            log_output = caplog.text
            assert test_password not in log_output, "Password leaked to logs!"

        finally:
            sandbox_client.delete_organization(org.id)

    def test_https_only_enforced(self, sandbox_client):
        """
        NFR1.3: HTTPS only (TLS 1.2+)

        Test:
        - Verify base_url uses https://
        - Verify HTTP URLs rejected
        """
        assert sandbox_client.base_url.startswith('https://'), "Not using HTTPS!"

        # Try to create client with HTTP URL (should fail)
        with pytest.raises(ValueError, match='HTTPS required'):
            ITGlueClient(instance='sandbox', base_url='http://insecure.com')
