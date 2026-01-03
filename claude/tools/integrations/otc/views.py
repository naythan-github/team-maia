"""
OTC API View Definitions

Contains the GUIDs for available OTC data views.
These are provided by the Orro dev team and map to specific
data exports in the OTC system.
"""

from dataclasses import dataclass
from typing import ClassVar, List, Optional


@dataclass(frozen=True)
class OTCView:
    """Represents an OTC API view endpoint."""
    guid: str
    name: str
    description: str
    retention: str


class OTCViews:
    """
    Available OTC API views.

    Each view has a unique GUID that identifies the data export.
    Use these constants when calling the OTC API.

    Example:
        client.fetch_view(OTCViews.COMMENTS.guid)
    """

    # Ticket comments from the last 10 days
    COMMENTS = OTCView(
        guid="c59ca238-8249-48b9-bff9-092fd33ce916",
        name="PowerBi-CloudTicket-Comments",
        description="Ticket comments written during the past 10 days",
        retention="10 days"
    )

    # Timesheet data from the last 18 months
    TIMESHEETS = OTCView(
        guid="1199f2db-1201-4611-b769-c8a941d3a5bf",
        name="PowerBi-Timesheet-18Months",
        description="All timesheet data in the last 18 months",
        retention="18 months"
    )

    # All tickets (excluding ISMS) from the last 3 years
    TICKETS = OTCView(
        guid="dc8570af-facd-4799-9cc0-99641d394fce",
        name="PowerBi-Tickets-All-3Years",
        description="All tickets, except ISMS-related tickets from the past three years",
        retention="3 years"
    )

    # API Base URL
    BASE_URL: ClassVar[str] = "https://webhook.orro.support/OTC/Data/View/data"

    @classmethod
    def get_endpoint(cls, view: OTCView) -> str:
        """
        Get the full API endpoint URL for a view.

        Args:
            view: The OTCView to get the endpoint for

        Returns:
            Full URL with GUID parameter
        """
        return f"{cls.BASE_URL}?id={view.guid}"

    @classmethod
    def all_views(cls) -> List[OTCView]:
        """Return list of all available views."""
        return [cls.COMMENTS, cls.TIMESHEETS, cls.TICKETS]

    @classmethod
    def get_by_name(cls, name: str) -> Optional[OTCView]:
        """
        Get a view by its name.

        Args:
            name: View name (e.g., 'comments', 'timesheets', 'tickets')

        Returns:
            OTCView or None if not found
        """
        name_lower = name.lower()
        if 'comment' in name_lower:
            return cls.COMMENTS
        elif 'timesheet' in name_lower:
            return cls.TIMESHEETS
        elif 'ticket' in name_lower:
            return cls.TICKETS
        return None
