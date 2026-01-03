"""
OTC (Orro Ticketing Cloud) API Client

A resilient API client for the legacy OTC system with conservative
rate limiting to prevent overwhelming the system.

Usage:
    from claude.tools.integrations.otc import OTCClient

    client = OTCClient()

    # Fetch individual views
    tickets = client.fetch_tickets()
    comments = client.fetch_comments()
    timesheets = client.fetch_timesheets()

    # Sync all views (with 30s gaps between requests)
    all_data = client.sync_all()

    # Health check
    status = client.health_check()

Note: Credentials must be stored in macOS Keychain before use.
"""

import json
import logging
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import requests

from .auth import get_credentials
from .exceptions import (
    OTCAPIError,
    OTCAuthError,
    OTCCircuitBreakerOpen,
    OTCConnectionError,
    OTCDataError,
    OTCRateLimitError,
    OTCServerError,
)
from .views import OTCViews, OTCView

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"       # Normal operation
    OPEN = "open"           # Failing fast
    HALF_OPEN = "half_open" # Testing recovery


@dataclass
class CircuitBreaker:
    """
    Circuit breaker for legacy system protection.

    Opens after 3 consecutive failures, stays open for 10 minutes.
    More conservative than typical implementations due to legacy system.
    """
    failure_threshold: int = 3
    cooldown_seconds: int = 600  # 10 minutes - legacy system needs time
    half_open_successes_required: int = 2

    state: CircuitState = field(default=CircuitState.CLOSED)
    failure_count: int = field(default=0)
    last_failure_time: Optional[datetime] = field(default=None)
    half_open_successes: int = field(default=0)

    def is_open(self) -> bool:
        """Check if circuit breaker should block requests."""
        if self.state == CircuitState.CLOSED:
            return False

        if self.state == CircuitState.OPEN:
            # Check if cooldown has passed
            if self.last_failure_time:
                elapsed = (datetime.now() - self.last_failure_time).total_seconds()
                if elapsed >= self.cooldown_seconds:
                    logger.info("Circuit breaker: OPEN → HALF_OPEN (cooldown passed)")
                    self.state = CircuitState.HALF_OPEN
                    self.half_open_successes = 0
                    return False
            return True

        return False  # HALF_OPEN allows requests

    def record_success(self) -> None:
        """Record a successful request."""
        if self.state == CircuitState.HALF_OPEN:
            self.half_open_successes += 1
            if self.half_open_successes >= self.half_open_successes_required:
                logger.info("Circuit breaker: HALF_OPEN → CLOSED (recovered)")
                self.state = CircuitState.CLOSED
                self.failure_count = 0

        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0

    def record_failure(self) -> None:
        """Record a failed request."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.state == CircuitState.HALF_OPEN:
            # Any failure in HALF_OPEN goes back to OPEN
            logger.warning("Circuit breaker: HALF_OPEN → OPEN (failure during recovery)")
            self.state = CircuitState.OPEN
            self.half_open_successes = 0

        elif self.failure_count >= self.failure_threshold:
            logger.warning(
                f"Circuit breaker: CLOSED → OPEN "
                f"(failures: {self.failure_count}/{self.failure_threshold})"
            )
            self.state = CircuitState.OPEN

    def get_status(self) -> dict:
        """Get current circuit breaker status."""
        cooldown_remaining = 0
        if self.state == CircuitState.OPEN and self.last_failure_time:
            elapsed = (datetime.now() - self.last_failure_time).total_seconds()
            cooldown_remaining = max(0, self.cooldown_seconds - elapsed)

        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "cooldown_remaining_seconds": int(cooldown_remaining),
        }


@dataclass
class RateLimiter:
    """
    Conservative rate limiter for legacy OTC system.

    Enforces minimum 5 seconds between requests and limits to 100/hour.
    """
    min_interval_seconds: float = 5.0  # 5 seconds between requests
    max_requests_per_hour: int = 100

    request_times: deque = field(default_factory=lambda: deque(maxlen=100))
    last_request_time: Optional[datetime] = field(default=None)

    def wait_if_needed(self) -> None:
        """
        Wait if needed to respect rate limits.

        Blocks until it's safe to make another request.
        """
        now = datetime.now()

        # Enforce minimum interval
        if self.last_request_time:
            elapsed = (now - self.last_request_time).total_seconds()
            if elapsed < self.min_interval_seconds:
                wait_time = self.min_interval_seconds - elapsed
                logger.debug(f"Rate limiter: waiting {wait_time:.1f}s (min interval)")
                time.sleep(wait_time)

        # Clean old request times (older than 1 hour)
        cutoff = now - timedelta(hours=1)
        while self.request_times and self.request_times[0] < cutoff:
            self.request_times.popleft()

        # Check hourly limit
        if len(self.request_times) >= self.max_requests_per_hour:
            oldest = self.request_times[0]
            wait_until = oldest + timedelta(hours=1)
            wait_seconds = (wait_until - now).total_seconds()
            if wait_seconds > 0:
                logger.warning(
                    f"Rate limiter: hourly limit reached, waiting {wait_seconds:.0f}s"
                )
                time.sleep(wait_seconds)

    def record_request(self) -> None:
        """Record that a request was made."""
        now = datetime.now()
        self.request_times.append(now)
        self.last_request_time = now

    def get_status(self) -> dict:
        """Get current rate limiter status."""
        now = datetime.now()
        cutoff = now - timedelta(hours=1)

        # Count requests in last hour
        recent_requests = sum(1 for t in self.request_times if t > cutoff)

        return {
            "requests_last_hour": recent_requests,
            "max_requests_per_hour": self.max_requests_per_hour,
            "utilization_percent": (recent_requests / self.max_requests_per_hour) * 100,
        }


class OTCClient:
    """
    OTC API Client with legacy system protection.

    Features:
    - Conservative rate limiting (5s min between requests)
    - Circuit breaker (3 failures → 10 min cooldown)
    - Exponential backoff (10s initial, 5 min max)
    - Sequential fetching (30s gaps between views)
    """

    TIMEOUT = 120  # 2 minutes - legacy system can be slow
    MAX_RETRIES = 3
    INITIAL_BACKOFF = 10  # 10 seconds initial backoff
    MAX_BACKOFF = 300  # 5 minutes max backoff
    VIEW_GAP_SECONDS = 30  # 30 seconds between different views

    def __init__(self):
        """Initialize OTC client with credentials from Keychain."""
        self.session = requests.Session()
        self.rate_limiter = RateLimiter()
        self.circuit_breaker = CircuitBreaker()

        # Load credentials
        username, password = get_credentials()
        self.session.auth = (username, password)

        # Set headers
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'Maia-OTC-Client/1.0',
        })

        # Metrics
        self._metrics = {
            'request_count': 0,
            'error_count': 0,
            'total_duration_ms': 0,
        }

        logger.info("OTC client initialized")

    def _make_request(self, view: OTCView) -> dict:
        """
        Make a single API request with all protections.

        Args:
            view: The OTCView to fetch

        Returns:
            Parsed JSON response

        Raises:
            OTCAPIError: On any API error
        """
        # Check circuit breaker
        if self.circuit_breaker.is_open():
            status = self.circuit_breaker.get_status()
            raise OTCCircuitBreakerOpen(status['cooldown_remaining_seconds'])

        # Wait for rate limit
        self.rate_limiter.wait_if_needed()

        url = OTCViews.get_endpoint(view)
        retry_count = 0
        last_error = None

        while retry_count <= self.MAX_RETRIES:
            try:
                start_time = time.time()
                logger.info(f"Fetching OTC view: {view.name} (attempt {retry_count + 1})")

                response = self.session.get(url, timeout=self.TIMEOUT)

                duration_ms = (time.time() - start_time) * 1000
                self._metrics['request_count'] += 1
                self._metrics['total_duration_ms'] += duration_ms
                self.rate_limiter.record_request()

                logger.debug(
                    f"OTC response: status={response.status_code}, "
                    f"duration={duration_ms:.0f}ms, size={len(response.content)} bytes"
                )

                # Handle response codes
                if response.status_code == 200:
                    self.circuit_breaker.record_success()
                    return self._parse_response(response, view)

                elif response.status_code == 401:
                    self.circuit_breaker.record_failure()
                    raise OTCAuthError()

                elif response.status_code == 429:
                    self.circuit_breaker.record_failure()
                    retry_after = int(response.headers.get('Retry-After', 60))
                    raise OTCRateLimitError(retry_after)

                elif response.status_code >= 500:
                    self.circuit_breaker.record_failure()
                    self._metrics['error_count'] += 1

                    # Server error - wait longer and retry
                    backoff = min(
                        self.INITIAL_BACKOFF * (2 ** retry_count),
                        self.MAX_BACKOFF
                    )
                    logger.warning(
                        f"OTC server error ({response.status_code}), "
                        f"waiting {backoff}s before retry"
                    )
                    time.sleep(backoff)
                    retry_count += 1
                    last_error = OTCServerError(response.status_code)
                    continue

                else:
                    self.circuit_breaker.record_failure()
                    raise OTCAPIError(
                        f"Unexpected status code: {response.status_code}",
                        response.status_code
                    )

            except requests.exceptions.Timeout:
                self.circuit_breaker.record_failure()
                self._metrics['error_count'] += 1
                backoff = min(
                    self.INITIAL_BACKOFF * (2 ** retry_count),
                    self.MAX_BACKOFF
                )
                logger.warning(f"OTC timeout, waiting {backoff}s before retry")
                time.sleep(backoff)
                retry_count += 1
                last_error = OTCConnectionError(
                    Exception(f"Request timed out after {self.TIMEOUT}s")
                )

            except requests.exceptions.ConnectionError as e:
                self.circuit_breaker.record_failure()
                self._metrics['error_count'] += 1
                raise OTCConnectionError(e)

            except requests.exceptions.RequestException as e:
                self.circuit_breaker.record_failure()
                self._metrics['error_count'] += 1
                raise OTCAPIError(f"Request failed: {e}")

        # Exhausted retries
        raise last_error or OTCAPIError("Request failed after max retries")

    def _parse_response(self, response: requests.Response, view: OTCView) -> dict:
        """
        Parse API response as JSON.

        Args:
            response: The HTTP response
            view: The view that was fetched

        Returns:
            Parsed JSON data

        Raises:
            OTCDataError: If response cannot be parsed
        """
        try:
            data = response.json()

            # Log basic stats
            if isinstance(data, list):
                logger.info(f"Fetched {len(data)} records from {view.name}")
            elif isinstance(data, dict):
                if 'data' in data and isinstance(data['data'], list):
                    logger.info(f"Fetched {len(data['data'])} records from {view.name}")
                else:
                    logger.info(f"Fetched response from {view.name}")

            return data

        except json.JSONDecodeError as e:
            # Try to provide context
            preview = response.text[:500] if response.text else "(empty)"
            raise OTCDataError(
                f"Failed to parse JSON response: {e}",
                raw_data=preview
            )

    def fetch_tickets(self, raw: bool = False) -> Union[List, Dict]:
        """
        Fetch all tickets from OTC.

        Args:
            raw: If True, return raw JSON. If False, return list of records.

        Returns:
            List of ticket records or raw JSON response
        """
        data = self._make_request(OTCViews.TICKETS)

        if raw:
            return data

        # Normalize to list
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'data' in data:
            return data['data']
        else:
            return [data]

    def fetch_comments(self, raw: bool = False) -> Union[List, Dict]:
        """
        Fetch recent comments from OTC (last 10 days).

        Args:
            raw: If True, return raw JSON. If False, return list of records.

        Returns:
            List of comment records or raw JSON response
        """
        data = self._make_request(OTCViews.COMMENTS)

        if raw:
            return data

        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'data' in data:
            return data['data']
        else:
            return [data]

    def fetch_timesheets(self, raw: bool = False) -> Union[List, Dict]:
        """
        Fetch timesheet data from OTC (last 18 months).

        Args:
            raw: If True, return raw JSON. If False, return list of records.

        Returns:
            List of timesheet records or raw JSON response
        """
        data = self._make_request(OTCViews.TIMESHEETS)

        if raw:
            return data

        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'data' in data:
            return data['data']
        else:
            return [data]

    def sync_all(self) -> Dict[str, List]:
        """
        Fetch all views sequentially with gaps between requests.

        This is the recommended way to sync all data, as it respects
        the legacy system's limitations.

        Returns:
            Dict with 'tickets', 'comments', 'timesheets' keys
        """
        logger.info("Starting full OTC sync (sequential with gaps)")
        results = {}

        # Fetch tickets first (largest dataset)
        logger.info("Fetching tickets...")
        results['tickets'] = self.fetch_tickets()
        logger.info(f"Fetched {len(results['tickets'])} tickets")

        # Wait before next request
        logger.info(f"Waiting {self.VIEW_GAP_SECONDS}s before next view...")
        time.sleep(self.VIEW_GAP_SECONDS)

        # Fetch comments
        logger.info("Fetching comments...")
        results['comments'] = self.fetch_comments()
        logger.info(f"Fetched {len(results['comments'])} comments")

        # Wait before next request
        logger.info(f"Waiting {self.VIEW_GAP_SECONDS}s before next view...")
        time.sleep(self.VIEW_GAP_SECONDS)

        # Fetch timesheets
        logger.info("Fetching timesheets...")
        results['timesheets'] = self.fetch_timesheets()
        logger.info(f"Fetched {len(results['timesheets'])} timesheets")

        logger.info(
            f"OTC sync complete: "
            f"{len(results['tickets'])} tickets, "
            f"{len(results['comments'])} comments, "
            f"{len(results['timesheets'])} timesheets"
        )

        return results

    def health_check(self) -> Dict[str, Any]:
        """
        Check OTC API connectivity and status.

        Returns:
            Health status dict with connection info and metrics
        """
        status = {
            'status': 'unknown',
            'timestamp': datetime.now().isoformat(),
            'circuit_breaker': self.circuit_breaker.get_status(),
            'rate_limiter': self.rate_limiter.get_status(),
            'metrics': self.get_metrics(),
        }

        # Test connection with small request
        try:
            start = time.time()
            # Use comments view as it's the smallest (10 days)
            self._make_request(OTCViews.COMMENTS)
            duration_ms = (time.time() - start) * 1000

            status['status'] = 'healthy'
            status['response_time_ms'] = round(duration_ms, 2)
            status['api_reachable'] = True

            # Warn if slow
            if duration_ms > 30000:  # 30 seconds
                status['status'] = 'degraded'
                status['warning'] = 'API response time exceeds 30 seconds'

        except OTCConnectionError:
            status['status'] = 'unhealthy'
            status['api_reachable'] = False
            status['error'] = 'Cannot connect to OTC API'

        except OTCAuthError:
            status['status'] = 'unhealthy'
            status['api_reachable'] = True
            status['error'] = 'Authentication failed'

        except OTCCircuitBreakerOpen as e:
            status['status'] = 'degraded'
            status['api_reachable'] = None  # Unknown - not tested
            status['error'] = f'Circuit breaker open ({e.cooldown_seconds}s remaining)'

        except OTCAPIError as e:
            status['status'] = 'degraded'
            status['api_reachable'] = True
            status['error'] = str(e)

        return status

    def get_metrics(self) -> dict:
        """Get client metrics."""
        avg_duration = 0
        if self._metrics['request_count'] > 0:
            avg_duration = (
                self._metrics['total_duration_ms'] /
                self._metrics['request_count']
            )

        return {
            'request_count': self._metrics['request_count'],
            'error_count': self._metrics['error_count'],
            'avg_duration_ms': round(avg_duration, 2),
            'error_rate': (
                self._metrics['error_count'] /
                max(1, self._metrics['request_count'])
            ) * 100,
        }


# CLI interface
if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    client = OTCClient()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "health":
            status = client.health_check()
            print(json.dumps(status, indent=2))

        elif command == "tickets":
            tickets = client.fetch_tickets()
            print(f"Fetched {len(tickets)} tickets")
            if tickets:
                print(f"Sample keys: {list(tickets[0].keys())[:10]}")

        elif command == "comments":
            comments = client.fetch_comments()
            print(f"Fetched {len(comments)} comments")

        elif command == "timesheets":
            timesheets = client.fetch_timesheets()
            print(f"Fetched {len(timesheets)} timesheets")

        elif command == "sync":
            data = client.sync_all()
            print(f"Synced: {len(data['tickets'])} tickets, "
                  f"{len(data['comments'])} comments, "
                  f"{len(data['timesheets'])} timesheets")

        else:
            print(f"Unknown command: {command}")
            print("Available: health, tickets, comments, timesheets, sync")
    else:
        print("OTC Client CLI")
        print("")
        print("Usage:")
        print("  python3 -m claude.tools.integrations.otc.client health      # Check API status")
        print("  python3 -m claude.tools.integrations.otc.client tickets     # Fetch tickets")
        print("  python3 -m claude.tools.integrations.otc.client comments    # Fetch comments")
        print("  python3 -m claude.tools.integrations.otc.client timesheets  # Fetch timesheets")
        print("  python3 -m claude.tools.integrations.otc.client sync        # Sync all views")
