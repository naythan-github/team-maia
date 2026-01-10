"""
Azure Cost Optimization API Utilities

Handles Azure API rate limiting, retries, and error handling.

TDD Implementation - Tests in tests/test_api_utils.py
"""

import time
import logging
from functools import wraps
from typing import TypeVar, Callable, Dict, Any

logger = logging.getLogger(__name__)

# Azure API rate limits (documented limits)
RATE_LIMITS: Dict[str, Dict[str, int]] = {
    "cost_management": {"requests": 30, "period_seconds": 300},    # 30/5min
    "resource_graph": {"requests": 15, "period_seconds": 5},       # 15/5s
    "monitor": {"requests": 12000, "period_seconds": 3600},        # 12k/hr
    "advisor": {"requests": 10, "period_seconds": 1},              # 10/s
}

# HTTP status codes that should trigger retry
RETRYABLE_STATUS_CODES = {429, 503, 504}

# HTTP status codes that should NOT be retried (client errors)
NON_RETRYABLE_STATUS_CODES = {400, 401, 403, 404, 405, 409, 422}


class AzureAPIError(Exception):
    """Raised when Azure API operations fail after retries."""
    pass


T = TypeVar('T')


def azure_retry(
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    api_type: str = "default"
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for Azure API calls with exponential backoff.

    Handles:
    - 429 Too Many Requests (throttling)
    - 503 Service Unavailable
    - 504 Gateway Timeout
    - Transient network errors

    Does NOT retry:
    - 400 Bad Request
    - 401 Unauthorized
    - 403 Forbidden
    - 404 Not Found
    - Other client errors

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds (doubles each retry)
        max_delay: Maximum delay cap in seconds
        api_type: API type for rate limit lookup (for future enhancement)

    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)

                except Exception as e:
                    last_exception = e

                    # Check if this is an Azure HttpResponseError
                    if hasattr(e, 'status_code'):
                        status_code = e.status_code

                        if status_code == 429:  # Throttled
                            retry_after = _get_retry_after(e, base_delay, attempt)
                            delay = min(retry_after, max_delay)
                            logger.warning(
                                f"Throttled on {func.__name__}, "
                                f"attempt {attempt + 1}/{max_retries}, "
                                f"waiting {delay}s"
                            )
                            time.sleep(delay)
                            continue

                        elif status_code in (503, 504):  # Service unavailable
                            delay = min(base_delay * (2 ** attempt), max_delay)
                            logger.warning(
                                f"Service unavailable for {func.__name__}, "
                                f"attempt {attempt + 1}/{max_retries}, "
                                f"waiting {delay}s"
                            )
                            time.sleep(delay)
                            continue

                        elif status_code in NON_RETRYABLE_STATUS_CODES:
                            # Don't retry client errors
                            raise

                        else:
                            # Unknown status code - retry with backoff
                            delay = min(base_delay * (2 ** attempt), max_delay)
                            logger.warning(
                                f"HTTP {status_code} for {func.__name__}, "
                                f"attempt {attempt + 1}/{max_retries}"
                            )
                            time.sleep(delay)
                            continue

                    # Check if this is a validation/programming error that shouldn't be retried
                    elif isinstance(e, (ValueError, TypeError, KeyError, AttributeError)):
                        # Don't retry programming/validation errors from decorated function
                        logger.error(
                            f"Programming/validation error in {func.__name__}: {type(e).__name__}: {e}"
                        )
                        raise

                    else:
                        # Network errors, connection errors, etc. - retry
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        logger.warning(
                            f"Error in {func.__name__}: {e}, "
                            f"attempt {attempt + 1}/{max_retries}"
                        )
                        time.sleep(delay)
                        continue

            # All retries exhausted
            raise AzureAPIError(
                f"Max retries ({max_retries}) exceeded for {func.__name__}"
            ) from last_exception

        return wrapper
    return decorator


def _get_retry_after(error: Exception, base_delay: float, attempt: int) -> float:
    """
    Extract Retry-After value from error response.

    Args:
        error: The HttpResponseError exception
        base_delay: Base delay for exponential backoff
        attempt: Current attempt number (0-indexed)

    Returns:
        Delay in seconds to wait before retrying
    """
    try:
        if hasattr(error, 'response') and error.response is not None:
            headers = getattr(error.response, 'headers', {})
            retry_after = headers.get('Retry-After')

            if retry_after is not None:
                return float(retry_after)
    except (ValueError, AttributeError):
        pass

    # Fall back to exponential backoff
    return base_delay * (2 ** attempt)
