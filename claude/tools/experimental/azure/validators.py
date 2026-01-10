"""
Azure Cost Optimization Input Validators

Validates all inputs before database operations to prevent:
- SQL injection (though we use parameterized queries)
- Invalid data corruption
- Cross-tenant data access

TDD Implementation - Tests in tests/test_validators.py
"""

import re
from typing import Optional, Set

# Azure GUID pattern (subscription_id, tenant_id, resource_id components)
GUID_PATTERN = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    re.IGNORECASE
)

# Customer slug pattern (URL-safe identifier)
# Allows: lowercase letters, numbers, hyphens, underscores
# Disallows: leading underscore (reserved for system), spaces, special chars
# Note: Pattern enforces lowercase-only (2-64 chars), case normalization happens in validate_customer_slug()
SLUG_PATTERN = re.compile(r'^[a-z0-9][a-z0-9_-]{1,63}$')  # Min 2, max 64 characters

# Reserved customer slug names (case-insensitive)
RESERVED_SLUGS: Set[str] = {
    "system", "admin", "root", "default", "test",
    "internal", "public", "private", "null", "undefined",
}

# Valid values for enum-like fields
VALID_STATUSES: Set[str] = {"Active", "Dismissed", "Implemented", "Expired"}
VALID_IMPACTS: Set[str] = {"High", "Medium", "Low"}
VALID_CLASSIFICATIONS: Set[str] = {
    "production",
    "dr_standby",
    "dev_test",
    "batch_processing",
    "template",
    "backup",
    "reserved_capacity",
}


def validate_guid(value: str, field_name: str) -> str:
    """
    Validate Azure GUID format.

    Args:
        value: The GUID string to validate
        field_name: Name of the field (for error messages)

    Returns:
        The validated GUID string

    Raises:
        ValueError: If the GUID format is invalid
    """
    if value is None:
        raise ValueError(f"Invalid {field_name} format: None")

    if not isinstance(value, str):
        raise ValueError(f"Invalid {field_name} format: expected string, got {type(value).__name__}")

    if not GUID_PATTERN.match(value):
        raise ValueError(f"Invalid {field_name} format: {value}")

    return value


def validate_subscription_id(value: str) -> str:
    """
    Validate Azure subscription ID format.

    Args:
        value: The subscription ID to validate

    Returns:
        The validated subscription ID

    Raises:
        ValueError: If the subscription ID format is invalid
    """
    return validate_guid(value, "subscription_id")


def validate_tenant_id(value: str) -> str:
    """
    Validate Azure tenant ID format.

    Args:
        value: The tenant ID to validate

    Returns:
        The validated tenant ID

    Raises:
        ValueError: If the tenant ID format is invalid
    """
    return validate_guid(value, "tenant_id")


def validate_confidence_score(value: float) -> float:
    """
    Validate confidence score is within valid range (0.0 to 1.0).

    Args:
        value: The confidence score to validate

    Returns:
        The validated confidence score

    Raises:
        ValueError: If the confidence score is out of range
    """
    if not isinstance(value, (int, float)):
        raise ValueError(f"Confidence must be a number, got: {type(value).__name__}")

    if not 0.0 <= value <= 1.0:
        raise ValueError(f"Confidence must be 0.0-1.0, got: {value}")

    return float(value)


def validate_status(value: str) -> str:
    """
    Validate recommendation status.

    Args:
        value: The status to validate

    Returns:
        The validated status

    Raises:
        ValueError: If the status is not valid
    """
    if value not in VALID_STATUSES:
        raise ValueError(f"Invalid status: {value}. Must be one of {VALID_STATUSES}")

    return value


def validate_impact(value: Optional[str]) -> Optional[str]:
    """
    Validate recommendation impact level.

    Args:
        value: The impact to validate (can be None)

    Returns:
        The validated impact or None

    Raises:
        ValueError: If the impact is not valid
    """
    if value is None:
        return None

    if value not in VALID_IMPACTS:
        raise ValueError(f"Invalid impact: {value}. Must be one of {VALID_IMPACTS}")

    return value


def validate_classification(value: str) -> str:
    """
    Validate resource classification.

    Args:
        value: The classification to validate

    Returns:
        The validated classification

    Raises:
        ValueError: If the classification is not valid
    """
    if value not in VALID_CLASSIFICATIONS:
        raise ValueError(
            f"Invalid classification: {value}. Must be one of {VALID_CLASSIFICATIONS}"
        )

    return value


def validate_customer_slug(value: str) -> str:
    """
    Validate customer slug (URL-safe identifier).

    Rules:
    - Must be 2-64 characters
    - Can only contain lowercase letters, numbers, hyphens, underscores
    - Cannot start with underscore (reserved for system databases)
    - Cannot use reserved words (system, admin, root, etc.)
    - Uppercase letters are automatically normalized to lowercase

    Args:
        value: The customer slug to validate

    Returns:
        The validated slug (normalized to lowercase)

    Raises:
        ValueError: If the slug format is invalid
    """
    if not value:
        raise ValueError("Customer slug cannot be empty")

    if len(value) < 2:
        raise ValueError("Customer slug must be at least 2 characters")

    if len(value) > 64:
        raise ValueError(f"Customer slug too long ({len(value)} chars). Maximum 64 characters allowed")

    if value.startswith("_"):
        raise ValueError("Customer slug cannot start with underscore (reserved for system)")

    # Normalize to lowercase
    normalized_slug = value.lower()

    # Check reserved words
    if normalized_slug in RESERVED_SLUGS:
        raise ValueError(
            f"Customer slug '{value}' is reserved. "
            f"Cannot use: {', '.join(sorted(RESERVED_SLUGS))}"
        )

    if not SLUG_PATTERN.match(normalized_slug):
        raise ValueError(
            f"Invalid customer slug: {value}. "
            "Must contain only letters, numbers, hyphens, and underscores"
        )

    return normalized_slug


def validate_savings(value: Optional[float]) -> Optional[float]:
    """
    Validate savings amount (must be non-negative).

    Args:
        value: The savings amount to validate (can be None)

    Returns:
        The validated savings amount or None

    Raises:
        ValueError: If the savings amount is negative
    """
    if value is None:
        return None

    if not isinstance(value, (int, float)):
        raise ValueError(f"Savings must be a number, got: {type(value).__name__}")

    if value < 0:
        raise ValueError(f"Savings cannot be negative: {value}")

    return float(value)
