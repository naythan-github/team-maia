"""
TDD Tests for Azure API Retry Logic

Tests written BEFORE implementation per TDD protocol.
Run with: pytest tests/test_api_utils.py -v
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from typing import Any


class TestAzureRetryDecorator:
    """Tests for the @azure_retry decorator."""

    def test_successful_call_no_retry(self):
        """Successful API call should not trigger any retry logic."""
        from claude.tools.experimental.azure.api_utils import azure_retry

        call_count = 0

        @azure_retry(max_retries=3)
        def successful_call() -> str:
            nonlocal call_count
            call_count += 1
            return "success"

        result = successful_call()

        assert result == "success"
        assert call_count == 1

    def test_429_triggers_retry(self):
        """429 Too Many Requests should trigger retry with delay."""
        from claude.tools.experimental.azure.api_utils import azure_retry
        from azure.core.exceptions import HttpResponseError

        call_count = 0

        @azure_retry(max_retries=3, base_delay=0.01)  # Short delay for tests
        def throttled_then_success() -> str:
            nonlocal call_count
            call_count += 1

            if call_count < 3:
                # Create mock response with status_code
                error = HttpResponseError(message="Throttled")
                error.status_code = 429
                error.response = Mock()
                error.response.headers = {"Retry-After": "0"}
                raise error

            return "success after retry"

        result = throttled_then_success()

        assert result == "success after retry"
        assert call_count == 3

    def test_503_triggers_retry(self):
        """503 Service Unavailable should trigger retry."""
        from claude.tools.experimental.azure.api_utils import azure_retry
        from azure.core.exceptions import HttpResponseError

        call_count = 0

        @azure_retry(max_retries=3, base_delay=0.01)
        def unavailable_then_success() -> str:
            nonlocal call_count
            call_count += 1

            if call_count < 2:
                error = HttpResponseError(message="Service Unavailable")
                error.status_code = 503
                error.response = Mock()
                error.response.headers = {}
                raise error

            return "recovered"

        result = unavailable_then_success()

        assert result == "recovered"
        assert call_count == 2

    def test_504_triggers_retry(self):
        """504 Gateway Timeout should trigger retry."""
        from claude.tools.experimental.azure.api_utils import azure_retry
        from azure.core.exceptions import HttpResponseError

        call_count = 0

        @azure_retry(max_retries=3, base_delay=0.01)
        def timeout_then_success() -> str:
            nonlocal call_count
            call_count += 1

            if call_count < 2:
                error = HttpResponseError(message="Gateway Timeout")
                error.status_code = 504
                error.response = Mock()
                error.response.headers = {}
                raise error

            return "recovered"

        result = timeout_then_success()

        assert result == "recovered"
        assert call_count == 2

    def test_max_retries_exceeded_raises(self):
        """After max retries, AzureAPIError should be raised."""
        from claude.tools.experimental.azure.api_utils import azure_retry, AzureAPIError
        from azure.core.exceptions import HttpResponseError

        call_count = 0

        @azure_retry(max_retries=3, base_delay=0.01)
        def always_fails() -> str:
            nonlocal call_count
            call_count += 1

            error = HttpResponseError(message="Always throttled")
            error.status_code = 429
            error.response = Mock()
            error.response.headers = {"Retry-After": "0"}
            raise error

        with pytest.raises(AzureAPIError) as exc_info:
            always_fails()

        assert call_count == 3
        assert "Max retries" in str(exc_info.value)
        assert "always_fails" in str(exc_info.value)

    def test_non_retryable_error_immediate_raise(self):
        """Non-retryable errors (400, 401, 403, 404) should raise immediately."""
        from claude.tools.experimental.azure.api_utils import azure_retry
        from azure.core.exceptions import HttpResponseError

        call_count = 0

        @azure_retry(max_retries=3, base_delay=0.01)
        def bad_request() -> str:
            nonlocal call_count
            call_count += 1

            error = HttpResponseError(message="Bad Request")
            error.status_code = 400
            error.response = Mock()
            error.response.headers = {}
            raise error

        with pytest.raises(HttpResponseError) as exc_info:
            bad_request()

        assert call_count == 1  # No retries for 400
        assert exc_info.value.status_code == 400

    def test_401_unauthorized_no_retry(self):
        """401 Unauthorized should not retry."""
        from claude.tools.experimental.azure.api_utils import azure_retry
        from azure.core.exceptions import HttpResponseError

        call_count = 0

        @azure_retry(max_retries=3, base_delay=0.01)
        def unauthorized() -> str:
            nonlocal call_count
            call_count += 1

            error = HttpResponseError(message="Unauthorized")
            error.status_code = 401
            error.response = Mock()
            error.response.headers = {}
            raise error

        with pytest.raises(HttpResponseError):
            unauthorized()

        assert call_count == 1

    def test_403_forbidden_no_retry(self):
        """403 Forbidden should not retry."""
        from claude.tools.experimental.azure.api_utils import azure_retry
        from azure.core.exceptions import HttpResponseError

        call_count = 0

        @azure_retry(max_retries=3, base_delay=0.01)
        def forbidden() -> str:
            nonlocal call_count
            call_count += 1

            error = HttpResponseError(message="Forbidden")
            error.status_code = 403
            error.response = Mock()
            error.response.headers = {}
            raise error

        with pytest.raises(HttpResponseError):
            forbidden()

        assert call_count == 1

    def test_404_not_found_no_retry(self):
        """404 Not Found should not retry."""
        from claude.tools.experimental.azure.api_utils import azure_retry
        from azure.core.exceptions import HttpResponseError

        call_count = 0

        @azure_retry(max_retries=3, base_delay=0.01)
        def not_found() -> str:
            nonlocal call_count
            call_count += 1

            error = HttpResponseError(message="Not Found")
            error.status_code = 404
            error.response = Mock()
            error.response.headers = {}
            raise error

        with pytest.raises(HttpResponseError):
            not_found()

        assert call_count == 1

    def test_exponential_backoff_timing(self):
        """Verify exponential backoff increases delay between retries."""
        from claude.tools.experimental.azure.api_utils import azure_retry
        from azure.core.exceptions import HttpResponseError

        call_times = []

        @azure_retry(max_retries=4, base_delay=0.05, max_delay=1.0)
        def track_timing() -> str:
            call_times.append(time.time())

            error = HttpResponseError(message="Service Unavailable")
            error.status_code = 503
            error.response = Mock()
            error.response.headers = {}
            raise error

        from claude.tools.experimental.azure.api_utils import AzureAPIError

        with pytest.raises(AzureAPIError):
            track_timing()

        # Calculate delays between calls
        delays = []
        for i in range(1, len(call_times)):
            delays.append(call_times[i] - call_times[i - 1])

        # Verify each delay is roughly double the previous (exponential)
        # With base_delay=0.05: expected ~0.05, ~0.10, ~0.20
        assert len(delays) == 3

        # Each delay should be approximately 2x the previous (with some tolerance)
        for i in range(1, len(delays)):
            ratio = delays[i] / delays[i - 1]
            assert 1.5 <= ratio <= 2.5, f"Expected ~2x backoff, got {ratio:.2f}x"

    def test_retry_after_header_respected(self):
        """Retry-After header value should be used for delay."""
        from claude.tools.experimental.azure.api_utils import azure_retry
        from azure.core.exceptions import HttpResponseError

        call_times = []
        call_count = 0

        @azure_retry(max_retries=3, base_delay=0.01)
        def with_retry_after() -> str:
            nonlocal call_count
            call_times.append(time.time())
            call_count += 1

            if call_count < 2:
                error = HttpResponseError(message="Throttled")
                error.status_code = 429
                error.response = Mock()
                # Tell client to wait 0.1 seconds
                error.response.headers = {"Retry-After": "0.1"}
                raise error

            return "success"

        result = with_retry_after()

        assert result == "success"
        assert len(call_times) == 2

        # Delay should be close to 0.1 seconds (Retry-After value)
        actual_delay = call_times[1] - call_times[0]
        assert 0.08 <= actual_delay <= 0.2, f"Expected ~0.1s delay, got {actual_delay:.3f}s"

    def test_max_delay_cap_respected(self):
        """Delay should never exceed max_delay even with large Retry-After."""
        from claude.tools.experimental.azure.api_utils import azure_retry
        from azure.core.exceptions import HttpResponseError

        call_times = []
        call_count = 0

        @azure_retry(max_retries=2, base_delay=0.01, max_delay=0.05)
        def with_large_retry_after() -> str:
            nonlocal call_count
            call_times.append(time.time())
            call_count += 1

            if call_count < 2:
                error = HttpResponseError(message="Throttled")
                error.status_code = 429
                error.response = Mock()
                # Request 10 second delay - should be capped
                error.response.headers = {"Retry-After": "10"}
                raise error

            return "success"

        result = with_large_retry_after()

        assert result == "success"
        assert len(call_times) == 2

        # Delay should be capped at max_delay (0.05s)
        actual_delay = call_times[1] - call_times[0]
        assert actual_delay <= 0.15, f"Expected delay <= 0.15s, got {actual_delay:.3f}s"

    def test_network_error_triggers_retry(self):
        """Generic network errors should trigger retry."""
        from claude.tools.experimental.azure.api_utils import azure_retry

        call_count = 0

        @azure_retry(max_retries=3, base_delay=0.01)
        def network_flaky() -> str:
            nonlocal call_count
            call_count += 1

            if call_count < 2:
                raise ConnectionError("Network unreachable")

            return "connected"

        result = network_flaky()

        assert result == "connected"
        assert call_count == 2


class TestAzureAPIError:
    """Tests for the AzureAPIError exception class."""

    def test_azure_api_error_is_exception(self):
        """AzureAPIError should be a proper Exception subclass."""
        from claude.tools.experimental.azure.api_utils import AzureAPIError

        error = AzureAPIError("Test error message")

        assert isinstance(error, Exception)
        assert str(error) == "Test error message"

    def test_azure_api_error_preserves_cause(self):
        """AzureAPIError should preserve the original exception as cause."""
        from claude.tools.experimental.azure.api_utils import AzureAPIError

        original = ValueError("Original error")
        error = AzureAPIError("Wrapped error")
        error.__cause__ = original

        assert error.__cause__ is original


class TestRateLimits:
    """Tests for rate limit constants."""

    def test_rate_limits_defined(self):
        """Rate limits should be defined for known Azure APIs."""
        from claude.tools.experimental.azure.api_utils import RATE_LIMITS

        assert "cost_management" in RATE_LIMITS
        assert "resource_graph" in RATE_LIMITS
        assert "monitor" in RATE_LIMITS
        assert "advisor" in RATE_LIMITS

    def test_cost_management_rate_limit(self):
        """Cost Management API should have 30 requests per 5 minutes."""
        from claude.tools.experimental.azure.api_utils import RATE_LIMITS

        limit = RATE_LIMITS["cost_management"]
        assert limit["requests"] == 30
        assert limit["period_seconds"] == 300

    def test_resource_graph_rate_limit(self):
        """Resource Graph should have 15 requests per 5 seconds."""
        from claude.tools.experimental.azure.api_utils import RATE_LIMITS

        limit = RATE_LIMITS["resource_graph"]
        assert limit["requests"] == 15
        assert limit["period_seconds"] == 5

    def test_monitor_rate_limit(self):
        """Monitor API should have 12000 requests per hour."""
        from claude.tools.experimental.azure.api_utils import RATE_LIMITS

        limit = RATE_LIMITS["monitor"]
        assert limit["requests"] == 12000
        assert limit["period_seconds"] == 3600

    def test_advisor_rate_limit(self):
        """Advisor API should have 10 requests per second."""
        from claude.tools.experimental.azure.api_utils import RATE_LIMITS

        limit = RATE_LIMITS["advisor"]
        assert limit["requests"] == 10
        assert limit["period_seconds"] == 1
