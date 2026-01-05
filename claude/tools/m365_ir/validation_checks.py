#!/usr/bin/env python3
"""
ValidationChecks - Timeline sanity checks and logic validation

Phase 230: Account Validator Implementation
Requirements: FR-3 (Timeline Sanity Checks - AUTOMATIC)

PURPOSE: Catch impossible scenarios and logic errors in account timelines.

Examples of what this catches:
- Activity after account disabled (unless re-enabled)
- Compromised account with >365 day old password (policy failure)
- Disabled during attack window (remediation) vs before attack (pre-existing)
"""

from datetime import datetime
from typing import Dict, Any, List, Optional


def validate_timeline_logic(lifecycle: Dict[str, Any], compromise: Dict[str, Any]) -> Dict[str, Any]:
    """
    FR-3: Check if timeline makes logical sense. Catch impossible scenarios.

    Args:
        lifecycle: Account lifecycle data from AccountValidator._validate_lifecycle()
        compromise: Compromise evidence from AccountValidator._validate_compromise()

    Returns:
        Dict with:
        - errors: List of CRITICAL logic errors (timeline impossibilities)
        - warnings: List of HIGH severity policy failures
        - timeline_valid: Boolean - False if any errors exist

    CHECK 1: If disabled, did activity occur after disable?
    CHECK 2: If password >365 days old, was account active?
    CHECK 3: If disabled during attack window, was it remediation or pre-existing?
    """
    errors: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []

    # Extract data
    current_status = lifecycle['current_status']
    disabled_date_str = lifecycle.get('disabled_date')
    re_enabled = lifecycle.get('re_enabled', False)
    re_enabled_date_str = lifecycle.get('re_enabled_date')
    password_age_days = lifecycle['password_age_days']

    foreign_logins = compromise['foreign_logins']
    first_foreign_str = foreign_logins.get('first_foreign_login')
    last_foreign_str = foreign_logins.get('last_foreign_login')
    total_foreign = foreign_logins.get('total_foreign_logins', 0)

    # Convert date strings to datetime for proper comparison
    # Dates are in format: '2025-12-03 01:53:35'
    def parse_date(date_str: Optional[str]) -> Optional[datetime]:
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            # Try without time
            try:
                return datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                return None

    disabled_date = parse_date(disabled_date_str)
    re_enabled_date = parse_date(re_enabled_date_str)
    first_foreign = parse_date(first_foreign_str)
    last_foreign = parse_date(last_foreign_str)

    # CHECK 1: If disabled, did activity occur after disable?
    if current_status == 'Disabled' and disabled_date and last_foreign:
        if last_foreign > disabled_date:
            # Account disabled but activity after - check if re-enabled
            if re_enabled and re_enabled_date:
                warnings.append({
                    'type': 'POST_DISABLE_ACTIVITY',
                    'message': (
                        f"Account disabled {disabled_date_str} but foreign activity detected {last_foreign_str}. "
                        f"Account was re-enabled {re_enabled_date_str}, explaining continued activity. "
                        f"Verify password was reset during re-enable to prevent continued abuse."
                    ),
                    'severity': 'MEDIUM',
                    'action_required': 'Verify password reset occurred at re-enable time'
                })
            else:
                errors.append({
                    'type': 'LOGIC_ERROR',
                    'message': (
                        f"Account disabled {disabled_date_str} but foreign activity detected {last_foreign_str}. "
                        f"Impossible unless: (1) Re-enabled after disable (but no enable event found), "
                        f"(2) Session tokens not revoked, (3) Log data error."
                    ),
                    'severity': 'CRITICAL',
                    'action_required': 'Investigate post-disable activity - check for session token revocation failure'
                })

    # CHECK 1B: If currently enabled but was previously disabled, check for post-re-enable activity
    if current_status == 'Enabled' and re_enabled and re_enabled_date and last_foreign:
        if last_foreign > re_enabled_date:
            warnings.append({
                'type': 'POST_REENABLE_ACTIVITY',
                'message': (
                    f"Account was re-enabled {re_enabled_date_str} and foreign activity continued until {last_foreign_str}. "
                    f"Verify password was reset when re-enabling to prevent continued abuse with old credentials."
                ),
                'severity': 'MEDIUM',
                'action_required': 'Verify password reset occurred at re-enable time'
            })

    # CHECK 2: If password >365 days old, was account active and compromised?
    if password_age_days > 365 and total_foreign > 0:
        warnings.append({
            'type': 'PASSWORD_POLICY',
            'message': (
                f"Password {password_age_days:,} days old ({password_age_days/365:.1f} years) and account compromised. "
                f"Indicates password expiration policy not enforced. "
                f"Organization should enforce max 90-day password age."
            ),
            'severity': 'HIGH',
            'action_required': 'Check organization password expiration policy enforcement'
        })

    # CHECK 3: If disabled during attack window, was it remediation or pre-existing?
    if current_status == 'Disabled' and disabled_date and first_foreign:
        if disabled_date >= first_foreign:
            # Disabled during or after attack started
            lifecycle['disabled_during_attack'] = True
            lifecycle['disable_reason'] = 'Remediation'
        else:
            # Disabled before attack started
            lifecycle['disabled_during_attack'] = False
            lifecycle['disable_reason'] = 'Pre-existing disabled account'

            # If account was disabled BEFORE attack but still shows compromise,
            # that's a logic error (unless re-enabled)
            if not re_enabled:
                errors.append({
                    'type': 'LOGIC_ERROR',
                    'message': (
                        f"Account disabled {disabled_date_str} but compromise started {first_foreign_str}. "
                        f"Account was disabled BEFORE attack, yet shows compromise activity. "
                        f"Impossible unless account was re-enabled (but no enable event found)."
                    ),
                    'severity': 'CRITICAL',
                    'action_required': 'Investigate timeline inconsistency'
                })

    return {
        'errors': errors,
        'warnings': warnings,
        'timeline_valid': len(errors) == 0
    }


def cross_validate_sources(account_data: Dict[str, Any]) -> bool:
    """
    FR-3.2: Ensure critical findings come from 2+ independent sources.

    Args:
        account_data: Full validation results from AccountValidator

    Returns:
        True if cross-validation passed

    Raises:
        ValidationError: If critical finding has only 1 source
    """
    from claude.tools.m365_ir.account_validator import ValidationError

    # Example: Account status should be confirmed by both password_status and entra_audit_log
    sources = set()

    if 'lifecycle' in account_data:
        lifecycle_sources = account_data['lifecycle'].get('source', '').split(', ')
        sources.update(lifecycle_sources)

    if len(sources) < 2:
        raise ValidationError(
            f"Critical finding requires 2+ sources. Only have: {sources}"
        )

    return True
