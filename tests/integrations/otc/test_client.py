"""
Unit tests for OTC API Client

Tests the OTC client with mocked API responses to verify:
- Rate limiting behavior
- Circuit breaker logic
- Error handling
- Response parsing
"""

import json
import time
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, PropertyMock

import pytest
import requests

from claude.tools.integrations.otc.client import (
    OTCClient,
    CircuitBreaker,
    CircuitState,
    RateLimiter,
)
from claude.tools.integrations.otc.exceptions import (
    OTCAPIError,
    OTCAuthError,
    OTCCircuitBreakerOpen,
    OTCConnectionError,
    OTCRateLimitError,
    OTCServerError,
)
from claude.tools.integrations.otc.views import OTCViews


class TestCircuitBreaker:
    """Tests for circuit breaker logic."""

    def test_initial_state_is_closed(self):
        """Circuit breaker starts in CLOSED state."""
        cb = CircuitBreaker()
        assert cb.state == CircuitState.CLOSED
        assert not cb.is_open()

    def test_opens_after_threshold_failures(self):
        """Circuit breaker opens after 3 consecutive failures."""
        cb = CircuitBreaker(failure_threshold=3)

        cb.record_failure()
        assert cb.state == CircuitState.CLOSED

        cb.record_failure()
        assert cb.state == CircuitState.CLOSED

        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        assert cb.is_open()

    def test_success_resets_failure_count(self):
        """Success resets the failure counter."""
        cb = CircuitBreaker(failure_threshold=3)

        cb.record_failure()
        cb.record_failure()
        assert cb.failure_count == 2

        cb.record_success()
        assert cb.failure_count == 0
        assert cb.state == CircuitState.CLOSED

    def test_transitions_to_half_open_after_cooldown(self):
        """Circuit breaker transitions to HALF_OPEN after cooldown."""
        cb = CircuitBreaker(failure_threshold=3, cooldown_seconds=1)

        # Open the circuit
        for _ in range(3):
            cb.record_failure()
        assert cb.state == CircuitState.OPEN

        # Wait for cooldown
        time.sleep(1.1)

        # Check transitions to HALF_OPEN
        assert not cb.is_open()
        assert cb.state == CircuitState.HALF_OPEN

    def test_half_open_closes_after_successes(self):
        """HALF_OPEN state closes after required successes."""
        cb = CircuitBreaker(
            failure_threshold=3,
            cooldown_seconds=0,
            half_open_successes_required=2
        )

        # Open and immediately allow HALF_OPEN
        for _ in range(3):
            cb.record_failure()
        cb.is_open()  # Triggers state check
        cb.state = CircuitState.HALF_OPEN  # Force for test

        cb.record_success()
        assert cb.state == CircuitState.HALF_OPEN

        cb.record_success()
        assert cb.state == CircuitState.CLOSED

    def test_half_open_reopens_on_failure(self):
        """Failure in HALF_OPEN state reopens circuit."""
        cb = CircuitBreaker(failure_threshold=3, cooldown_seconds=0)

        # Get to HALF_OPEN state
        for _ in range(3):
            cb.record_failure()
        cb.state = CircuitState.HALF_OPEN

        cb.record_failure()
        assert cb.state == CircuitState.OPEN

    def test_get_status(self):
        """Status dict includes all relevant info."""
        cb = CircuitBreaker()
        status = cb.get_status()

        assert 'state' in status
        assert 'failure_count' in status
        assert 'cooldown_remaining_seconds' in status


class TestRateLimiter:
    """Tests for rate limiter logic."""

    def test_allows_first_request(self):
        """First request is allowed immediately."""
        rl = RateLimiter(min_interval_seconds=5)

        # Should not block
        start = time.time()
        rl.wait_if_needed()
        elapsed = time.time() - start

        assert elapsed < 0.1  # Should be immediate

    def test_enforces_minimum_interval(self):
        """Enforces minimum interval between requests."""
        rl = RateLimiter(min_interval_seconds=0.5)

        rl.record_request()

        start = time.time()
        rl.wait_if_needed()
        elapsed = time.time() - start

        assert elapsed >= 0.4  # Should have waited

    def test_get_status(self):
        """Status dict includes utilization info."""
        rl = RateLimiter()
        rl.record_request()

        status = rl.get_status()

        assert 'requests_last_hour' in status
        assert 'max_requests_per_hour' in status
        assert 'utilization_percent' in status
        assert status['requests_last_hour'] == 1


class TestOTCViews:
    """Tests for view definitions."""

    def test_comments_view(self):
        """Comments view has correct GUID."""
        assert OTCViews.COMMENTS.guid == "c59ca238-8249-48b9-bff9-092fd33ce916"
        assert "10 days" in OTCViews.COMMENTS.retention

    def test_timesheets_view(self):
        """Timesheets view has correct GUID."""
        assert OTCViews.TIMESHEETS.guid == "1199f2db-1201-4611-b769-c8a941d3a5bf"
        assert "18 months" in OTCViews.TIMESHEETS.retention

    def test_tickets_view(self):
        """Tickets view has correct GUID."""
        assert OTCViews.TICKETS.guid == "dc8570af-facd-4799-9cc0-99641d394fce"
        assert "3 years" in OTCViews.TICKETS.retention

    def test_get_endpoint(self):
        """get_endpoint returns full URL with GUID."""
        url = OTCViews.get_endpoint(OTCViews.COMMENTS)
        assert "webhook.orro.support" in url
        assert OTCViews.COMMENTS.guid in url

    def test_all_views(self):
        """all_views returns all 3 views."""
        views = OTCViews.all_views()
        assert len(views) == 3

    def test_get_by_name(self):
        """get_by_name finds views by partial name."""
        assert OTCViews.get_by_name('comments') == OTCViews.COMMENTS
        assert OTCViews.get_by_name('ticket') == OTCViews.TICKETS
        assert OTCViews.get_by_name('timesheet') == OTCViews.TIMESHEETS
        assert OTCViews.get_by_name('unknown') is None


class TestOTCClient:
    """Tests for OTC client with mocked API."""

    @pytest.fixture
    def mock_credentials(self):
        """Mock credentials from Keychain."""
        with patch('claude.tools.integrations.otc.client.get_credentials') as mock:
            mock.return_value = ('test-user', 'test-pass')
            yield mock

    @pytest.fixture
    def mock_session(self):
        """Mock requests session."""
        with patch('requests.Session') as mock:
            yield mock.return_value

    def test_client_initialization(self, mock_credentials):
        """Client initializes with credentials from Keychain."""
        with patch('requests.Session'):
            client = OTCClient()

        mock_credentials.assert_called_once()
        assert client.session.auth == ('test-user', 'test-pass')

    def test_fetch_tickets_success(self, mock_credentials):
        """Successful ticket fetch returns list."""
        with patch('requests.Session') as mock_session_class:
            mock_session = mock_session_class.return_value
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = [
                {'TKT-Ticket ID': 1, 'TKT-Title': 'Test'},
                {'TKT-Ticket ID': 2, 'TKT-Title': 'Test 2'},
            ]
            mock_response.content = b'[...]'
            mock_session.get.return_value = mock_response

            client = OTCClient()
            tickets = client.fetch_tickets()

            assert len(tickets) == 2
            assert tickets[0]['TKT-Ticket ID'] == 1

    def test_fetch_handles_auth_error(self, mock_credentials):
        """401 response raises OTCAuthError."""
        with patch('requests.Session') as mock_session_class:
            mock_session = mock_session_class.return_value
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_session.get.return_value = mock_response

            client = OTCClient()

            with pytest.raises(OTCAuthError):
                client.fetch_tickets()

    def test_fetch_handles_rate_limit(self, mock_credentials):
        """429 response raises OTCRateLimitError."""
        with patch('requests.Session') as mock_session_class:
            mock_session = mock_session_class.return_value
            mock_response = MagicMock()
            mock_response.status_code = 429
            mock_response.headers = {'Retry-After': '60'}
            mock_session.get.return_value = mock_response

            client = OTCClient()

            with pytest.raises(OTCRateLimitError) as exc_info:
                client.fetch_tickets()

            assert exc_info.value.retry_after == 60

    def test_fetch_handles_connection_error(self, mock_credentials):
        """Connection error raises OTCConnectionError."""
        with patch('requests.Session') as mock_session_class:
            mock_session = mock_session_class.return_value
            mock_session.get.side_effect = requests.exceptions.ConnectionError("Failed")

            client = OTCClient()

            with pytest.raises(OTCConnectionError):
                client.fetch_tickets()

    def test_circuit_breaker_blocks_when_open(self, mock_credentials):
        """Open circuit breaker raises OTCCircuitBreakerOpen."""
        with patch('requests.Session'):
            client = OTCClient()

            # Open the circuit breaker
            client.circuit_breaker.state = CircuitState.OPEN
            client.circuit_breaker.last_failure_time = datetime.now()

            with pytest.raises(OTCCircuitBreakerOpen):
                client.fetch_tickets()

    def test_get_metrics(self, mock_credentials):
        """Metrics are tracked correctly."""
        with patch('requests.Session') as mock_session_class:
            mock_session = mock_session_class.return_value
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = []
            mock_response.content = b'[]'
            mock_session.get.return_value = mock_response

            client = OTCClient()
            client.fetch_tickets()

            metrics = client.get_metrics()
            assert metrics['request_count'] == 1
            assert metrics['error_count'] == 0

    def test_health_check(self, mock_credentials):
        """Health check returns status dict."""
        with patch('requests.Session') as mock_session_class:
            mock_session = mock_session_class.return_value
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = []
            mock_response.content = b'[]'
            mock_session.get.return_value = mock_response

            client = OTCClient()
            status = client.health_check()

            assert 'status' in status
            assert 'circuit_breaker' in status
            assert 'rate_limiter' in status
            assert status['status'] == 'healthy'


class TestDataModels:
    """Tests for Pydantic data models."""

    def test_comment_model_parses_api_fields(self):
        """Comment model parses API field names."""
        from claude.tools.integrations.otc.models import OTCComment

        data = {
            'CT-COMMENT-ID': 12345,
            'CT-TKT-ID': 1001,
            'CT-COMMENT': 'Test comment',
            'CT-USERIDNAME': 'John Doe',
            'CT-VISIBLE-CUSTOMER': 'true',
        }

        comment = OTCComment.model_validate(data)

        assert comment.comment_id == 12345
        assert comment.ticket_id == 1001
        assert comment.comment_text == 'Test comment'
        assert comment.visible_to_customer is True

    def test_ticket_model_parses_api_fields(self):
        """Ticket model parses API field names."""
        from claude.tools.integrations.otc.models import OTCTicket

        data = {
            'TKT-Ticket ID': 1001,
            'TKT-Title': 'Test ticket',
            'TKT-Status': 'Open',
            'TKT-Created Time': '2025-01-01T10:00:00',
        }

        ticket = OTCTicket.model_validate(data)

        assert ticket.id == 1001
        assert ticket.summary == 'Test ticket'
        assert ticket.status == 'Open'
        assert ticket.created_time.year == 2025

    def test_timesheet_model_parses_hours(self):
        """Timesheet model parses hours correctly."""
        from claude.tools.integrations.otc.models import OTCTimesheet

        data = {
            'TS-User Username': 'jdoe',
            'TS-Hours': '2.5',
            'TS-Date': '2025-01-01',
        }

        timesheet = OTCTimesheet.model_validate(data)

        assert timesheet.user == 'jdoe'
        assert timesheet.hours == 2.5

    def test_to_db_dict(self):
        """to_db_dict converts to database column names."""
        from claude.tools.integrations.otc.models import OTCComment

        comment = OTCComment(
            comment_id=123,
            ticket_id=456,
            comment_text='Test',
        )

        db_dict = comment.to_db_dict()

        assert 'comment_id' in db_dict
        assert db_dict['comment_id'] == 123


# Run tests with: pytest tests/integrations/otc/test_client.py -v
