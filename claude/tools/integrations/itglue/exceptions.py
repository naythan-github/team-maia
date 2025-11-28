"""
Custom exceptions for ITGlue API Client
"""


class ITGlueAPIError(Exception):
    """Base exception for all ITGlue API errors"""
    pass


class ITGlueAuthError(ITGlueAPIError):
    """Authentication failed (401) - API key invalid or expired"""

    def __init__(self, message="API key invalid or expired. Check macOS Keychain."):
        super().__init__(message)


class ITGlueRateLimitError(ITGlueAPIError):
    """Rate limit exceeded (429) - Too many requests"""

    def __init__(self, retry_after_seconds=60):
        self.retry_after_seconds = retry_after_seconds
        super().__init__(f"Rate limit exceeded. Retry after {retry_after_seconds} seconds.")


class ITGlueNotFoundError(ITGlueAPIError):
    """Resource not found (404)"""

    def __init__(self, resource_type, resource_id):
        self.resource_type = resource_type
        self.resource_id = resource_id
        super().__init__(f"{resource_type} with ID {resource_id} not found.")


class ITGlueForbiddenError(ITGlueAPIError):
    """Forbidden (403) - Insufficient permissions"""

    def __init__(self, message="Forbidden. Insufficient API key permissions."):
        super().__init__(message)


class ITGlueServerError(ITGlueAPIError):
    """Server error (500/503) - ITGlue service issue"""

    def __init__(self, status_code, message="ITGlue server error"):
        self.status_code = status_code
        super().__init__(f"{message} (HTTP {status_code})")


class ITGlueCircuitBreakerOpen(ITGlueAPIError):
    """Circuit breaker is open - failing fast"""

    def __init__(self, message="Circuit breaker open. Too many failures detected."):
        super().__init__(message)
