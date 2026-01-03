"""
OTC API Data Models

Pydantic models for OTC API response data.
Maps API field names to database schema using existing column mappings.

Note: API field names may differ from XLSX exports. These models will be
updated once we can test the actual API response format.
"""

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict


class OTCComment(BaseModel):
    """
    Comment/note on a ticket.

    API fields map to database schema:
    - CT-COMMENT-ID → comment_id
    - CT-TKT-ID → ticket_id
    - CT-COMMENT → comment_text
    - CT-USERIDNAME → user_name
    - CT-DATEAMDTIME → created_time
    - CT-VISIBLE-CUSTOMER → visible_to_customer
    """
    model_config = ConfigDict(populate_by_name=True, extra='allow')

    # Core fields (expected in API response)
    comment_id: Optional[int] = Field(None, alias='CT-COMMENT-ID')
    ticket_id: Optional[int] = Field(None, alias='CT-TKT-ID')
    comment_text: Optional[str] = Field(None, alias='CT-COMMENT')
    user_id: Optional[str] = Field(None, alias='CT-USERID')
    user_name: Optional[str] = Field(None, alias='CT-USERIDNAME')
    owner_type: Optional[str] = Field(None, alias='CT-OWNERTYPE')
    created_time: Optional[datetime] = Field(None, alias='CT-DATEAMDTIME')
    visible_to_customer: Optional[bool] = Field(None, alias='CT-VISIBLE-CUSTOMER')
    comment_type: Optional[str] = Field(None, alias='CT-TYPE')
    team: Optional[str] = Field(None, alias='CT-TKT-TEAM')

    @field_validator('visible_to_customer', mode='before')
    @classmethod
    def parse_visible_to_customer(cls, v: Any) -> Optional[bool]:
        """Handle various boolean representations."""
        if v is None:
            return None
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() in ('true', 'yes', '1', 'y')
        return bool(v)

    @field_validator('created_time', mode='before')
    @classmethod
    def parse_datetime(cls, v: Any) -> Optional[datetime]:
        """Handle various datetime formats."""
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            # Try ISO format first
            try:
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                pass
            # Try common formats
            for fmt in [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%dT%H:%M:%S',
                '%d/%m/%Y %H:%M:%S',
                '%d/%m/%Y %H:%M',
            ]:
                try:
                    return datetime.strptime(v, fmt)
                except ValueError:
                    continue
        return None

    def to_db_dict(self) -> dict:
        """Convert to database column names."""
        return {
            'comment_id': self.comment_id,
            'ticket_id': self.ticket_id,
            'comment_text': self.comment_text,
            'user_id': self.user_id,
            'user_name': self.user_name,
            'owner_type': self.owner_type,
            'created_time': self.created_time,
            'visible_to_customer': self.visible_to_customer,
            'comment_type': self.comment_type,
            'team': self.team,
        }


class OTCTicket(BaseModel):
    """
    ServiceDesk ticket.

    API fields map to database schema:
    - TKT-Ticket ID → id
    - TKT-Title → summary
    - TKT-Created Time → created_time
    - TKT-Status → status
    - TKT-Assigned To User → assignee
    - TKT-Severity → priority
    - TKT-Team → category
    """
    model_config = ConfigDict(populate_by_name=True, extra='allow')

    # Core identification
    id: Optional[int] = Field(None, alias='TKT-Ticket ID')
    summary: Optional[str] = Field(None, alias='TKT-Title')
    description: Optional[str] = Field(None, alias='TKT-Description')

    # Status and classification
    status: Optional[str] = Field(None, alias='TKT-Status')
    priority: Optional[str] = Field(None, alias='TKT-Severity')
    category: Optional[str] = Field(None, alias='TKT-Team')
    platform: Optional[str] = Field(None, alias='TKT-Platform')
    group: Optional[str] = Field(None, alias='TKT-Group')

    # Assignment
    assignee: Optional[str] = Field(None, alias='TKT-Assigned To User')
    assigned_to_userid: Optional[int] = Field(None, alias='TKT-Assigned To Userid')
    created_by_user: Optional[str] = Field(None, alias='TKT-Created By User')
    created_by_userid: Optional[int] = Field(None, alias='TKT-Created By Userid')

    # Account info
    account_id: Optional[int] = Field(None, alias='TKT-Account Id')
    account_name: Optional[str] = Field(None, alias='TKT-Account Name')
    client_name: Optional[str] = Field(None, alias='TKT-Client Name')

    # Timestamps
    created_time: Optional[datetime] = Field(None, alias='TKT-Created Time')
    modified_time: Optional[datetime] = Field(None, alias='TKT-Modified Time')
    resolved_time: Optional[datetime] = Field(None, alias='TKT-Actual Resolution Date')
    closed_time: Optional[datetime] = Field(None, alias='TKT-Closure Date')
    due_date: Optional[datetime] = Field(None, alias='TKT-Due Date')
    response_date: Optional[datetime] = Field(None, alias='TKT-Actual Response Date')

    # SLA tracking
    sla: Optional[str] = Field(None, alias='TKT-SLA')
    sla_met: Optional[str] = Field(None, alias='TKT-SLA Met')
    response_met: Optional[str] = Field(None, alias='TKT-Response Met')
    resolution_met: Optional[str] = Field(None, alias='TKT-Resolution Met')
    sla_clock_status: Optional[str] = Field(None, alias='TKT-SLA Clock Status')

    # Resolution
    solution: Optional[str] = Field(None, alias='TKT-Solution')
    root_cause_category: Optional[str] = Field(None, alias='TKT-Root Cause Category')
    resolution_type: Optional[str] = Field(None, alias='TKT-Resolution/Change Type')
    ticket_source: Optional[str] = Field(None, alias='TKT-Ticket Source')

    @field_validator('created_time', 'modified_time', 'resolved_time',
                     'closed_time', 'due_date', 'response_date', mode='before')
    @classmethod
    def parse_datetime(cls, v: Any) -> Optional[datetime]:
        """Handle various datetime formats."""
        if v is None or v == '':
            return None
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            # Try ISO format first
            try:
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                pass
            # Try common formats
            for fmt in [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%dT%H:%M:%S',
                '%d/%m/%Y %H:%M:%S',
                '%d/%m/%Y %H:%M',
            ]:
                try:
                    return datetime.strptime(v, fmt)
                except ValueError:
                    continue
        return None

    def to_db_dict(self) -> dict:
        """Convert to database column names."""
        return {
            'id': self.id,
            'summary': self.summary,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'category': self.category,
            'platform': self.platform,
            'group': self.group,
            'assignee': self.assignee,
            'assigned_to_userid': self.assigned_to_userid,
            'created_by_user': self.created_by_user,
            'created_by_userid': self.created_by_userid,
            'account_id': self.account_id,
            'account_name': self.account_name,
            'client_name': self.client_name,
            'created_time': self.created_time,
            'modified_time': self.modified_time,
            'resolved_time': self.resolved_time,
            'closed_time': self.closed_time,
            'due_date': self.due_date,
            'response_date': self.response_date,
            'sla': self.sla,
            'sla_met': self.sla_met,
            'response_met': self.response_met,
            'resolution_met': self.resolution_met,
            'sla_clock_status': self.sla_clock_status,
            'solution': self.solution,
            'root_cause_category': self.root_cause_category,
            'resolution_type': self.resolution_type,
            'ticket_source': self.ticket_source,
        }


class OTCTimesheet(BaseModel):
    """
    Timesheet entry.

    API fields map to database schema:
    - TS-User Username → user
    - TS-Hours → hours
    - TS-Date → date
    - TS-Crm ID → crm_id
    - TS-User Full Name → user_fullname
    """
    model_config = ConfigDict(populate_by_name=True, extra='allow')

    # User identification
    user: Optional[str] = Field(None, alias='TS-User Username')
    user_fullname: Optional[str] = Field(None, alias='TS-User Full Name')

    # Time tracking
    date: Optional[datetime] = Field(None, alias='TS-Date')
    time_from: Optional[str] = Field(None, alias='TS-Time From')
    time_to: Optional[str] = Field(None, alias='TS-Time To')
    hours: Optional[float] = Field(None, alias='TS-Hours')

    # Categorization
    category: Optional[str] = Field(None, alias='TS-Category')
    sub_category: Optional[str] = Field(None, alias='TS-Sub Category')
    work_type: Optional[str] = Field(None, alias='TS-Type')

    # Ticket linkage
    crm_id: Optional[int] = Field(None, alias='TS-Crm ID')
    ticket_project_master_code: Optional[str] = Field(None, alias='TS-Ticket Project Master Code')
    description: Optional[str] = Field(None, alias='TS-Description')
    notes: Optional[str] = Field(None, alias='TS-Notes')

    # Client and billing
    account_name: Optional[str] = Field(None, alias='TS-Account Name')
    account_selcom: Optional[str] = Field(None, alias='TS-Account Selcom')
    costcentre: Optional[str] = Field(None, alias='TS-Costcentre')
    charge_code: Optional[str] = Field(None, alias='TS-Charge Code')
    client_bill_code: Optional[str] = Field(None, alias='TS-Client Bill Code')

    # Status
    billable: Optional[bool] = Field(None, alias='TS-Billable')
    approved: Optional[bool] = Field(None, alias='TS-Approved')
    modified_time: Optional[datetime] = Field(None, alias='TS-Modified Time')

    @field_validator('hours', mode='before')
    @classmethod
    def parse_hours(cls, v: Any) -> Optional[float]:
        """Handle various numeric formats."""
        if v is None or v == '':
            return None
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            try:
                return float(v.replace(',', '.'))
            except ValueError:
                return None
        return None

    @field_validator('date', 'modified_time', mode='before')
    @classmethod
    def parse_datetime(cls, v: Any) -> Optional[datetime]:
        """Handle various datetime formats."""
        if v is None or v == '':
            return None
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            # Try ISO format first
            try:
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                pass
            # Try common formats
            for fmt in [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%d',
                '%d/%m/%Y %H:%M:%S',
                '%d/%m/%Y',
            ]:
                try:
                    return datetime.strptime(v, fmt)
                except ValueError:
                    continue
        return None

    @field_validator('billable', 'approved', mode='before')
    @classmethod
    def parse_boolean(cls, v: Any) -> Optional[bool]:
        """Handle various boolean representations."""
        if v is None:
            return None
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() in ('true', 'yes', '1', 'y')
        return bool(v)

    def to_db_dict(self) -> dict:
        """Convert to database column names."""
        return {
            'user': self.user,
            'user_fullname': self.user_fullname,
            'date': self.date,
            'time_from': self.time_from,
            'time_to': self.time_to,
            'hours': self.hours,
            'category': self.category,
            'sub_category': self.sub_category,
            'work_type': self.work_type,
            'crm_id': self.crm_id,
            'ticket_project_master_code': self.ticket_project_master_code,
            'description': self.description,
            'notes': self.notes,
            'account_name': self.account_name,
            'account_selcom': self.account_selcom,
            'costcentre': self.costcentre,
            'charge_code': self.charge_code,
            'client_bill_code': self.client_bill_code,
            'billable': self.billable,
            'approved': self.approved,
            'modified_time': self.modified_time,
        }


def parse_api_response(data: list[dict], entity_type: str) -> list[BaseModel]:
    """
    Parse API response into typed models.

    Args:
        data: List of records from API
        entity_type: 'tickets', 'comments', or 'timesheets'

    Returns:
        List of parsed models
    """
    model_map = {
        'tickets': OTCTicket,
        'comments': OTCComment,
        'timesheets': OTCTimesheet,
    }

    model_class = model_map.get(entity_type)
    if not model_class:
        raise ValueError(f"Unknown entity type: {entity_type}")

    return [model_class.model_validate(record) for record in data]
