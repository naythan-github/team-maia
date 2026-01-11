#!/usr/bin/env python3
"""
M365 Schema Transform Functions

Field transformation functions for multi-schema ETL pipeline.
Handles data type conversions, format normalization, and field parsing
for different M365 export schema variants.

Author: Maia System
Created: 2026-01-11 (Phase 264 Sprint 1.2)
"""

from datetime import datetime, timezone
from typing import Optional, Tuple


def parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
    """
    Parse ISO 8601 datetime string to datetime object.

    Graph API exports use ISO 8601 format with UTC timezone:
    - "2025-12-04T08:19:41Z"
    - "2025-12-04T08:19:41.000Z" (with milliseconds)
    - "2025-12-04T08:19:41.123456Z" (with microseconds)

    Args:
        value: ISO 8601 datetime string

    Returns:
        datetime: Timezone-aware datetime in UTC, or None if empty/None

    Raises:
        ValueError: If datetime string is invalid

    Example:
        >>> parse_iso_datetime("2025-12-04T08:19:41Z")
        datetime(2025, 12, 4, 8, 19, 41, tzinfo=timezone.utc)
    """
    if not value or (isinstance(value, str) and not value.strip()):
        return None

    value = value.strip()

    # Remove 'Z' suffix if present (indicates UTC)
    if value.endswith('Z'):
        value = value[:-1]

    # Parse ISO format
    try:
        # Try with microseconds first
        if '.' in value:
            dt = datetime.fromisoformat(value)
        else:
            dt = datetime.fromisoformat(value)

        # Ensure timezone-aware (assume UTC if not specified)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        return dt
    except ValueError as e:
        raise ValueError(f"Invalid ISO datetime format: {value}") from e


def parse_graph_location(location: Optional[str]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Parse Graph API location field into city, state, country components.

    Graph API exports combine location into single field:
    - "Melbourne, Victoria, AU" → (city, state, country)
    - "Sydney, AU" → (city, None, country)
    - "AU" → (None, None, country)
    - "London, , GB" → (city, None, country)

    Args:
        location: Combined location string

    Returns:
        Tuple of (city, state, country), each may be None

    Example:
        >>> parse_graph_location("Melbourne, Victoria, AU")
        ('Melbourne', 'Victoria', 'AU')
    """
    if not location or (isinstance(location, str) and not location.strip()):
        return None, None, None

    # Split by comma and strip whitespace
    parts = [p.strip() for p in location.split(',')]

    # Remove empty parts
    parts = [p if p else None for p in parts]

    # Parse based on number of segments
    if len(parts) == 1:
        # Country only
        return None, None, parts[0]
    elif len(parts) == 2:
        # City, Country
        return parts[0], None, parts[1]
    elif len(parts) >= 3:
        # City, State, Country (take last 3 if more than 3)
        return parts[-3], parts[-2], parts[-1]
    else:
        return None, None, None


def parse_graph_status(status: Optional[str]) -> Optional[str]:
    """
    Parse and normalize Graph API status field.

    Graph API status values:
    - "Success" → "success"
    - "Failure" → "failure"
    - "Interrupted" → "interrupted"

    Args:
        status: Status string from Graph API

    Returns:
        Normalized lowercase status, or None if empty

    Example:
        >>> parse_graph_status("Success")
        'success'
    """
    if not status or (isinstance(status, str) and not status.strip()):
        return None

    return status.strip().lower()


def parse_boolean_field(value: Optional[str]) -> Optional[bool]:
    """
    Parse boolean field from Graph API exports.

    Handles various boolean representations:
    - "Yes", "YES", "yes" → True
    - "No", "NO", "no" → False
    - "True", "TRUE", "true", "1" → True
    - "False", "FALSE", "false", "0" → False

    Args:
        value: Boolean field value

    Returns:
        True, False, or None if empty/unknown

    Example:
        >>> parse_boolean_field("Yes")
        True
        >>> parse_boolean_field("No")
        False
    """
    if not value or (isinstance(value, str) and not value.strip()):
        return None

    value_lower = value.strip().lower()

    if value_lower in ('yes', 'true', '1'):
        return True
    elif value_lower in ('no', 'false', '0'):
        return False
    else:
        return None


def parse_integer_field(value: Optional[str]) -> Optional[int]:
    """
    Parse integer field from Graph API exports.

    Handles:
    - Valid integer strings: "42" → 42
    - Empty/whitespace: "" → None
    - None: None → None

    Args:
        value: Integer field value

    Returns:
        int or None if empty

    Raises:
        ValueError: If value is not a valid integer

    Example:
        >>> parse_integer_field("245")
        245
        >>> parse_integer_field("0")
        0
    """
    if not value or (isinstance(value, str) and not value.strip()):
        return None

    try:
        return int(value.strip())
    except ValueError as e:
        raise ValueError(f"Invalid integer value: {value}") from e


def parse_latency_field(value: Optional[str]) -> Optional[int]:
    """
    Parse latency field from Graph API exports.

    Graph API latency format:
    - "123ms" → 123
    - "456.78ms" → 456 (truncates decimal)
    - "789ms" → 789
    - "" → None

    Args:
        value: Latency string with 'ms' suffix

    Returns:
        Latency in milliseconds as integer, or None if empty

    Raises:
        ValueError: If value is not a valid latency format

    Example:
        >>> parse_latency_field("123ms")
        123
        >>> parse_latency_field("456.78ms")
        456
    """
    if not value or (isinstance(value, str) and not value.strip()):
        return None

    value = value.strip()

    # Remove 'ms' suffix if present
    if value.endswith('ms'):
        value = value[:-2].strip()

    try:
        # Parse as float first (handles decimals), then truncate to int
        return int(float(value))
    except ValueError as e:
        raise ValueError(f"Invalid latency format: {value}") from e


def clean_trailing_spaces(field_name: str) -> str:
    """
    Clean trailing spaces from field names.

    Graph API bug: some field names have trailing spaces:
    - "Application ID " → "Application ID"
    - "Username" → "Username" (no change)

    Args:
        field_name: CSV field name

    Returns:
        Field name with trailing spaces removed

    Example:
        >>> clean_trailing_spaces("Application ID ")
        'Application ID'
    """
    if not field_name:
        return field_name
    return field_name.rstrip()


def normalize_conditional_access_status(status: Optional[str]) -> Optional[str]:
    """
    Normalize Conditional Access status across schema variants.

    Handles differences between Legacy Portal and Graph API:
    - Graph API: "Success", "Failure", "Not Applied"
    - Legacy Portal: "success", "failure", "notApplied"

    Normalization:
    - "Success" → "success"
    - "Failure" → "failure"
    - "Not Applied" → "notApplied" (canonical format)

    Args:
        status: Conditional Access status string

    Returns:
        Normalized status, or None if empty

    Example:
        >>> normalize_conditional_access_status("Not Applied")
        'notApplied'
    """
    if not status or (isinstance(status, str) and not status.strip()):
        return None

    status_lower = status.strip().lower()

    # Normalize "not applied" variants to camelCase
    if status_lower in ('not applied', 'notapplied'):
        return 'notApplied'
    else:
        return status_lower
