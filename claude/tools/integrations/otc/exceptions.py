"""
OTC API Exception Hierarchy

Custom exceptions for handling OTC API errors with actionable messages.
"""

from typing import Optional


class OTCAPIError(Exception):
    """Base exception for all OTC API errors."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        self.status_code = status_code
        super().__init__(message)


class OTCAuthError(OTCAPIError):
    """
    Authentication failed (HTTP 401).

    The provided credentials are invalid or expired.
    """

    def __init__(self, message: Optional[str] = None):
        super().__init__(
            message or (
                "OTC authentication failed. Check credentials in macOS Keychain.\n\n"
                "To update credentials:\n"
                "  from claude.tools.integrations.otc import set_credentials\n"
                "  set_credentials('username', 'password')\n\n"
                "Or use the CLI:\n"
                "  python3 -m claude.tools.integrations.otc.auth --setup"
            ),
            status_code=401
        )


class OTCForbiddenError(OTCAPIError):
    """
    Access forbidden (HTTP 403).

    The credentials are valid but lack permission for this resource.
    """

    def __init__(self, resource: Optional[str] = None):
        msg = "OTC access forbidden."
        if resource:
            msg += f" Resource: {resource}"
        msg += " Contact Orro admin for access."
        super().__init__(msg, status_code=403)


class OTCNotFoundError(OTCAPIError):
    """
    Resource not found (HTTP 404).

    The requested view GUID does not exist.
    """

    def __init__(self, guid: Optional[str] = None):
        msg = "OTC view not found."
        if guid:
            msg += f" GUID: {guid}"
        msg += " Verify the view GUID with Orro dev team."
        super().__init__(msg, status_code=404)


class OTCRateLimitError(OTCAPIError):
    """
    Rate limit exceeded (HTTP 429).

    Too many requests sent to the legacy OTC system.
    """

    def __init__(self, retry_after: int = 60):
        self.retry_after = retry_after
        super().__init__(
            f"OTC rate limit exceeded. Retry after {retry_after} seconds.\n"
            "The OTC system is a legacy system - reduce request frequency.",
            status_code=429
        )


class OTCServerError(OTCAPIError):
    """
    Server error (HTTP 5xx).

    The OTC server encountered an internal error.
    """

    def __init__(self, status_code: int = 500, message: Optional[str] = None):
        super().__init__(
            message or (
                f"OTC server error (HTTP {status_code}). "
                "The system may be overloaded or under maintenance. "
                "Wait and retry with increased backoff."
            ),
            status_code=status_code
        )


class OTCConnectionError(OTCAPIError):
    """
    Connection error (network/timeout).

    Cannot establish connection to OTC API.
    Common causes:
    - VPN not connected
    - IP not whitelisted
    - Network timeout
    """

    def __init__(self, original_error: Optional[Exception] = None):
        msg = (
            "Cannot connect to OTC API at webhook.orro.support.\n\n"
            "Possible causes:\n"
            "  1. VPN not connected (Orro VPN required)\n"
            "  2. IP not whitelisted (contact Orro IT)\n"
            "  3. Network timeout (system may be slow)\n"
        )
        if original_error:
            msg += f"\nOriginal error: {original_error}"
        super().__init__(msg, status_code=None)


class OTCCircuitBreakerOpen(OTCAPIError):
    """
    Circuit breaker is open.

    Too many consecutive failures - failing fast to protect the legacy system.
    """

    def __init__(self, cooldown_seconds: int = 600):
        self.cooldown_seconds = cooldown_seconds
        super().__init__(
            f"OTC circuit breaker is OPEN after multiple failures.\n"
            f"Requests will be blocked for {cooldown_seconds} seconds.\n"
            "This protects the legacy OTC system from overload.",
            status_code=None
        )


class OTCDataError(OTCAPIError):
    """
    Data parsing or validation error.

    The API response could not be parsed or validated.
    """

    def __init__(self, message: str, raw_data: Optional[str] = None):
        full_msg = f"OTC data error: {message}"
        if raw_data:
            # Truncate for readability
            preview = raw_data[:200] + "..." if len(raw_data) > 200 else raw_data
            full_msg += f"\n\nData preview: {preview}"
        super().__init__(full_msg, status_code=None)
