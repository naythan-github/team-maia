"""
OTC (Orro Ticketing Cloud) API Integration

This module provides a Python client for interacting with the OTC API,
enabling automated ticket, comment, and timesheet data retrieval, plus
team management database functionality.

Core Features:
- OTC API client for tickets, comments, and timesheets
- Team management database (PostgreSQL)
- Team roster with organizational hierarchy
- Queue assignment tracking
- Complete audit trail (7-year retention)
- JSON fallback support

Usage - API Client:
    from claude.tools.integrations.otc import OTCClient

    client = OTCClient()
    tickets = client.fetch_tickets()
    comments = client.fetch_comments()
    timesheets = client.fetch_timesheets()

Usage - Team Management:
    from claude.tools.integrations.otc import (
        get_team_members,
        add_team_member,
        update_team_member,
        get_member_workload
    )

    # Get active engineering team (with JSON fallback)
    members = get_team_members()

    # Add new member (creates history entry)
    member_id = add_team_member('John Doe', 'john.doe@orro.group')

    # Update with history tracking
    update_team_member(member_id, name='John Smith', changed_by='admin')

    # Get member workload statistics
    workload = get_member_workload(member_id)

Database Setup:
    from claude.tools.integrations.otc import (
        create_team_management_schema,
        migrate_team_data,
        get_connection
    )

    conn = get_connection()
    create_team_management_schema(conn)  # Create tables
    migrate_team_data(conn)              # Load initial data
    conn.close()

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
