#!/usr/bin/env python3
"""
ServiceDesk Column Mappings - XLSX to Database Schema

Central mapping dictionary for all 3 entity types.
Maps source XLSX column names → target database column names.

Author: Maia (SRE Principal Engineer Agent)
Created: 2025-10-17
Phase: 127 Day 4 - Column Mapping Fix
"""

# XLSX → Database column mappings
COLUMN_MAPPINGS = {
    'comments': {
        # Source XLSX → Database schema (NEW format as of Jan 2026)
        'TKTCT-CommentID': 'comment_id',
        'TKTCT-TicketID': 'ticket_id',
        'TKTCT-Comment': 'comment_text',
        'TKTCT-UserID': 'user_id',
        'TKTCT-Username': 'user_name',
        'TKTCT-OwnerType': 'owner_type',
        'TKTCT-Created Time': 'created_time',
        'TKTCT-VisibleCustomer': 'visible_to_customer',
        'TKTCT-Type': 'comment_type',
        'TKTCT-Team': 'team'
    },
    # Legacy comment mappings (pre-Jan 2026)
    'comments_legacy': {
        'CT-COMMENT-ID': 'comment_id',
        'CT-TKT-ID': 'ticket_id',
        'CT-COMMENT': 'comment_text',
        'CT-USERID': 'user_id',
        'CT-USERIDNAME': 'user_name',
        'CT-OWNERTYPE': 'owner_type',
        'CT-DATEAMDTIME': 'created_time',
        'CT-VISIBLE-CUSTOMER': 'visible_to_customer',
        'CT-TYPE': 'comment_type',
        'CT-TKT-TEAM': 'team'
    },
    'tickets': {
        # Source XLSX → Database schema
        'TKT-Ticket ID': 'id',
        'TKT-Title': 'summary',
        'TKT-Created Time': 'created_time',
        'TKT-Status': 'status',
        'TKT-Assigned To User': 'assignee',
        'TKT-Severity': 'priority',
        'TKT-Team': 'category',
        'TKT-Modified Time': 'resolved_time',
        'TKT-Closed Time': 'closed_time',
        'TKT-Due Date': 'due_date'
    },
    'timesheets': {
        # Source XLSX → Database schema
        'TS-User Username': 'user',
        'TS-Hours': 'hours',
        'TS-Date': 'date',
        'TS-Crm ID': 'crm_id',
        'TS-Description': 'description',
        'TS-Billable': 'billable',
        'TS-Approved': 'approved',
        'TS-Modified Time': 'modified_time',
        'TS-User Full Name': 'user_fullname',
        'TS-Title': 'timesheet_entry_id'  # Placeholder - actual ID column TBD
    }
}

# Reverse mappings (Database → XLSX)
REVERSE_MAPPINGS = {
    entity: {db_col: xlsx_col for xlsx_col, db_col in mapping.items()}
    for entity, mapping in COLUMN_MAPPINGS.items()
}


def get_xlsx_column(entity_type: str, db_column: str) -> str:
    """
    Get XLSX column name from database column name

    Args:
        entity_type: 'comments', 'tickets', or 'timesheets'
        db_column: Database column name (e.g., 'comment_id')

    Returns:
        XLSX column name (e.g., 'CT-COMMENT-ID')
    """
    return REVERSE_MAPPINGS.get(entity_type, {}).get(db_column, db_column)


def get_db_column(entity_type: str, xlsx_column: str) -> str:
    """
    Get database column name from XLSX column name

    Args:
        entity_type: 'comments', 'tickets', or 'timesheets'
        xlsx_column: XLSX column name (e.g., 'CT-COMMENT-ID')

    Returns:
        Database column name (e.g., 'comment_id')
    """
    return COLUMN_MAPPINGS.get(entity_type, {}).get(xlsx_column, xlsx_column)


def rename_columns(df, entity_type: str, direction: str = 'to_db'):
    """
    Rename DataFrame columns between XLSX and database schemas

    Args:
        df: pandas DataFrame
        entity_type: 'comments', 'tickets', or 'timesheets'
        direction: 'to_db' (XLSX→DB) or 'to_xlsx' (DB→XLSX)

    Returns:
        DataFrame with renamed columns
    """
    if direction == 'to_db':
        mapping = COLUMN_MAPPINGS.get(entity_type, {})
    elif direction == 'to_xlsx':
        mapping = REVERSE_MAPPINGS.get(entity_type, {})
    else:
        raise ValueError(f"Invalid direction: {direction}. Use 'to_db' or 'to_xlsx'")

    return df.rename(columns=mapping)


# Quick reference of required XLSX columns for validation
REQUIRED_XLSX_COLUMNS = {
    'comments': [
        'TKTCT-CommentID',
        'TKTCT-TicketID',
        'TKTCT-Created Time',
        'TKTCT-Comment',
        'TKTCT-Username',
        'TKTCT-VisibleCustomer'
    ],
    # Legacy format (pre-Jan 2026)
    'comments_legacy': [
        'CT-COMMENT-ID',
        'CT-TKT-ID',
        'CT-DATEAMDTIME',
        'CT-COMMENT',
        'CT-USERIDNAME',
        'CT-VISIBLE-CUSTOMER'
    ],
    'tickets': [
        'TKT-Ticket ID',
        'TKT-Title',
        'TKT-Created Time',
        'TKT-Status',
        'TKT-Assigned To User',
        'TKT-Severity',
        'TKT-Team'
    ],
    'timesheets': [
        'TS-User Username',
        'TS-Hours',
        'TS-Date',
        'TS-Crm ID'
    ]
}
