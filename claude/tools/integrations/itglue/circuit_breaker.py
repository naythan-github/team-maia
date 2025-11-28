"""
Circuit breaker pattern for ITGlue API client

Prevents cascading failures by failing fast when service is degraded.

States:
- CLOSED: Normal operation, requests pass through
- OPEN: Too many failures, fail fast without making requests
- HALF_OPEN: Testing if service recovered
"""

import time
import logging
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """
    Circuit breaker implementation.

    Opens after consecutive failures, closes after cooldown period.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        cooldown_seconds: int = 60,
        half_open_attempts: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.half_open_attempts = half_open_attempts

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.success_count = 0

        logger.info(
            f"Circuit breaker initialized: threshold={failure_threshold}, "
            f"cooldown={cooldown_seconds}s"
        )

    def is_open(self) -> bool:
        """Check if circuit breaker is open"""
        if self.state == CircuitState.CLOSED:
            return False

        if self.state == CircuitState.OPEN:
            # Check if cooldown period has elapsed
            if self.last_failure_time:
                elapsed = time.time() - self.last_failure_time
                if elapsed >= self.cooldown_seconds:
                    # Transition to half-open
                    logger.info(
                        f"Circuit breaker transitioning to HALF_OPEN after {elapsed:.1f}s cooldown"
                    )
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    return False

            # Still in cooldown
            return True

        # HALF_OPEN state
        return False

    def open(self) -> None:
        """Force circuit breaker open"""
        logger.warning("Circuit breaker forced OPEN")
        self.state = CircuitState.OPEN
        self.last_failure_time = time.time()

    def close(self) -> None:
        """Force circuit breaker closed"""
        logger.info("Circuit breaker forced CLOSED")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0

    def reset(self) -> None:
        """Reset circuit breaker to initial state"""
        logger.info("Circuit breaker reset")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None

    def record_success(self) -> None:
        """Record successful request"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            logger.debug(
                f"Circuit breaker HALF_OPEN: {self.success_count}/{self.half_open_attempts} successes"
            )

            if self.success_count >= self.half_open_attempts:
                # Recovered! Close circuit
                logger.info("Circuit breaker closing after successful recovery")
                self.close()
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            if self.failure_count > 0:
                logger.debug(f"Circuit breaker: Resetting failure count after success")
                self.failure_count = 0

    def record_failure(self) -> None:
        """Record failed request"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == CircuitState.CLOSED:
            logger.warning(
                f"Circuit breaker failure {self.failure_count}/{self.failure_threshold}"
            )

            if self.failure_count >= self.failure_threshold:
                # Open circuit
                logger.error(
                    f"Circuit breaker OPENING after {self.failure_count} consecutive failures"
                )
                self.state = CircuitState.OPEN

        elif self.state == CircuitState.HALF_OPEN:
            # Failed during recovery attempt
            logger.warning("Circuit breaker reopening after failure in HALF_OPEN state")
            self.state = CircuitState.OPEN
            self.success_count = 0

    def get_stats(self) -> dict:
        """Get circuit breaker statistics"""
        stats = {
            'state': self.state.value,
            'failure_count': self.failure_count,
            'failure_threshold': self.failure_threshold,
            'cooldown_seconds': self.cooldown_seconds
        }

        if self.state == CircuitState.OPEN and self.last_failure_time:
            elapsed = time.time() - self.last_failure_time
            stats['time_until_half_open'] = max(0, self.cooldown_seconds - elapsed)

        if self.state == CircuitState.HALF_OPEN:
            stats['success_count'] = self.success_count
            stats['half_open_attempts'] = self.half_open_attempts

        return stats

    def __repr__(self) -> str:
        return f"CircuitBreaker(state={self.state.value}, failures={self.failure_count})"
