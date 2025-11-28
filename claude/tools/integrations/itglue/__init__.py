"""
ITGlue API Integration for Maia

Production-grade ITGlue REST API client with caching, rate limiting,
circuit breaker, and multi-instance support (sandbox + production).

Usage:
    from claude.tools.integrations.itglue import ITGlueClient

    # Create client (API key from macOS Keychain)
    client = ITGlueClient(instance='sandbox')

    # List organizations
    orgs = client.list_organizations()

    # Create configuration
    config = client.create_configuration(
        organization_id='1',
        name='Web Server',
        configuration_type='Server'
    )
"""

from claude.tools.integrations.itglue.client import ITGlueClient
from claude.tools.integrations.itglue.cache import ITGlueCache
from claude.tools.integrations.itglue.exceptions import (
    ITGlueAuthError,
    ITGlueRateLimitError,
    ITGlueNotFoundError,
    ITGlueAPIError
)

__all__ = [
    'ITGlueClient',
    'ITGlueCache',
    'ITGlueAuthError',
    'ITGlueRateLimitError',
    'ITGlueNotFoundError',
    'ITGlueAPIError'
]

__version__ = '1.0.0'
