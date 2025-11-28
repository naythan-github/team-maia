"""
Rate limiter for ITGlue API

ITGlue rate limit: 3000 requests per 5-minute window.
This module tracks requests and throttles to stay within limits.
"""

import time
import logging
from collections import deque
from typing import Optional

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Rate limiter using sliding window algorithm.

    ITGlue limits: 3000 requests per 5 minutes
    Conservative threshold: 2400 requests (80%) before throttling
    """

    def __init__(
        self,
        max_requests: int = 3000,
        window_seconds: int = 300,  # 5 minutes
        throttle_threshold: float = 0.8  # Throttle at 80%
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.throttle_threshold = throttle_threshold
        self.throttle_requests = int(max_requests * throttle_threshold)

        # Sliding window of request timestamps
        self.request_times = deque()

        logger.info(
            f"Rate limiter initialized: {max_requests} req/{window_seconds}s, "
            f"throttle at {throttle_threshold * 100}% ({self.throttle_requests} req)"
        )

    @property
    def request_count(self) -> int:
        """Get current request count in sliding window"""
        self._cleanup_old_requests()
        return len(self.request_times)

    def _cleanup_old_requests(self) -> None:
        """Remove requests older than window_seconds"""
        now = time.time()
        cutoff = now - self.window_seconds

        while self.request_times and self.request_times[0] < cutoff:
            self.request_times.popleft()

    def check_rate_limit(self) -> tuple[bool, Optional[float]]:
        """
        Check if we should throttle or block requests.

        Returns:
            (should_proceed, sleep_seconds)
            - should_proceed: False if at hard limit
            - sleep_seconds: Delay before proceeding (throttling)
        """
        self._cleanup_old_requests()
        current_count = len(self.request_times)

        # Hard limit: block completely
        if current_count >= self.max_requests:
            # Calculate how long to wait for oldest request to expire
            oldest = self.request_times[0]
            wait_time = (oldest + self.window_seconds) - time.time()
            logger.warning(
                f"Hard rate limit hit ({current_count}/{self.max_requests}). "
                f"Waiting {wait_time:.1f}s"
            )
            return False, wait_time

        # Soft limit: throttle (add delays)
        if current_count >= self.throttle_requests:
            # Linear throttling: more requests = longer delay
            ratio = (current_count - self.throttle_requests) / (self.max_requests - self.throttle_requests)
            sleep_time = ratio * 2.0  # Up to 2 second delay at hard limit
            logger.info(
                f"Throttling activated ({current_count}/{self.max_requests}). "
                f"Sleeping {sleep_time:.2f}s"
            )
            return True, sleep_time

        # Under threshold: proceed without delay
        return True, None

    def record_request(self) -> None:
        """Record a request in the sliding window"""
        self.request_times.append(time.time())

    def wait_if_needed(self) -> None:
        """
        Wait if rate limit requires it.

        Handles both throttling (soft limit) and blocking (hard limit).
        """
        should_proceed, sleep_time = self.check_rate_limit()

        if sleep_time:
            time.sleep(sleep_time)

        # If hard limit, check again after sleep
        if not should_proceed:
            # Recursively check until we can proceed
            return self.wait_if_needed()

        self.record_request()

    def get_stats(self) -> dict:
        """Get rate limiter statistics"""
        self._cleanup_old_requests()
        current_count = len(self.request_times)

        return {
            'current_requests': current_count,
            'max_requests': self.max_requests,
            'window_seconds': self.window_seconds,
            'utilization_percent': (current_count / self.max_requests) * 100,
            'throttling': current_count >= self.throttle_requests,
            'at_limit': current_count >= self.max_requests
        }

    def reset(self) -> None:
        """Reset rate limiter (for testing)"""
        self.request_times.clear()
        logger.info("Rate limiter reset")
