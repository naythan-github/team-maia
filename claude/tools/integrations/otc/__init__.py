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
from .team_management_schema import create_team_management_schema, drop_team_management_schema, migrate_team_data
from .team_management import (
    get_connection,
    get_team_members,
    get_team_queues,
    get_member_by_email,
    get_member_workload,
    add_team_member,
    update_team_member,
    assign_queue,
    remove_queue_assignment,
    export_teams_to_json,
)
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
    'create_team_management_schema',
    'drop_team_management_schema',
    'migrate_team_data',
    'get_connection',
    'get_team_members',
    'get_team_queues',
    'get_member_by_email',
    'get_member_workload',
    'add_team_member',
    'update_team_member',
    'assign_queue',
    'remove_queue_assignment',
    'export_teams_to_json',
    'OTCAPIError',
    'OTCAuthError',
    'OTCRateLimitError',
    'OTCConnectionError',
    'OTCServerError',
]

__version__ = '1.0.0'
