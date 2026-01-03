"""
OTC (Orro Ticketing Cloud) API Integration

This module provides a Python client for interacting with the OTC API,
enabling automated ticket, comment, and timesheet data retrieval.

Usage:
    from claude.tools.integrations.otc import OTCClient

    client = OTCClient()
    tickets = client.fetch_tickets()
    comments = client.fetch_comments()
    timesheets = client.fetch_timesheets()

Note: Credentials must be stored in macOS Keychain before use.
See auth.py for setup instructions.
"""

from .client import OTCClient
from .auth import get_credentials, set_credentials, delete_credentials
from .views import OTCViews
from .exceptions import (
    OTCAPIError,
    OTCAuthError,
    OTCRateLimitError,
    OTCConnectionError,
    OTCServerError,
)

__all__ = [
    'OTCClient',
    'OTCViews',
    'get_credentials',
    'set_credentials',
    'delete_credentials',
    'OTCAPIError',
    'OTCAuthError',
    'OTCRateLimitError',
    'OTCConnectionError',
    'OTCServerError',
]

__version__ = '1.0.0'
