#!/usr/bin/env python3
"""
Timeline Event Filter - Classify events as "interesting" for timeline inclusion

Phase 260: IR Timeline Persistence
Implements event inclusion criteria per requirements doc section 9.1

Author: SRE Principal Engineer Agent
Created: 2026-01-09
"""

from typing import Dict, Any, Optional


# High-risk countries for geo-based filtering
HIGH_RISK_COUNTRIES = {"RU", "CN", "KP", "IR", "BY", "VE", "CU", "SY"}


def is_interesting_event(
    event: Dict[str, Any],
    home_country: str = "AU",
    ir_knowledge_db: Optional[str] = None
) -> bool:
    """
    Determine if an event should be included in the timeline.

    Per Phase 260 requirements, only "interesting" events are persisted:
    - Foreign logins (non-home country)
    - Failed authentications
    - Legacy auth events (MFA bypass vectors)
    - Inbox rule changes (persistence)
    - Password/MFA changes (account manipulation)
    - Admin role assignments (privilege escalation)
    - OAuth consents (app-based attacks)
    - High-risk IPs (known bad actors)
    - Transport rule changes (exfiltration)

    Excludes:
    - Routine successful home-country logins
    - Normal business app access
    - Read-only mailbox operations without anomaly markers

    Args:
        event: Event dict with source_type and relevant fields
        home_country: Expected home country (default: AU)
        ir_knowledge_db: Optional path to IR knowledge DB for IP lookups

    Returns:
        True if event should be included in timeline, False otherwise
    """
    source_type = event.get('source_type', '')

    # =================================================================
    # Sign-in logs filtering
    # =================================================================
    if source_type == 'sign_in_logs':
        # Foreign login (non-home country) = interesting
        country = event.get('location_country', '')
        if country and country != home_country:
            return True

        # Failed auth = interesting
        ca_status = event.get('conditional_access_status', '')
        error_code = event.get('status_error_code')
        if ca_status == 'failure' or (error_code and error_code != 0):
            return True

        # Successful home-country login for normal apps = NOT interesting
        if ca_status == 'success' and country == home_country:
            return False

    # =================================================================
    # Legacy auth logs = ALWAYS interesting (MFA bypass vectors)
    # =================================================================
    if source_type == 'legacy_auth_logs':
        return True

    # =================================================================
    # Inbox rules = ALWAYS interesting (persistence)
    # =================================================================
    if source_type == 'inbox_rules':
        return True

    # =================================================================
    # Transport rules = ALWAYS interesting (exfiltration)
    # =================================================================
    if source_type == 'transport_rules':
        return True

    # =================================================================
    # OAuth consents = ALWAYS interesting (app-based attacks)
    # =================================================================
    if source_type == 'oauth_consents':
        return True

    # =================================================================
    # Entra audit log filtering (password/role changes)
    # =================================================================
    if source_type == 'entra_audit_log':
        activity = event.get('activity', '').lower()

        # Password changes = interesting
        if 'password' in activity:
            return True

        # Role assignments = interesting
        if 'role' in activity:
            return True

        # User manipulation = interesting
        if 'disable user' in activity or 'enable user' in activity:
            return True

    # =================================================================
    # MFA changes = ALWAYS interesting
    # =================================================================
    if source_type == 'mfa_changes':
        return True

    # =================================================================
    # Admin role assignments = ALWAYS interesting
    # =================================================================
    if source_type == 'admin_role_assignments':
        return True

    # =================================================================
    # Unified audit log filtering (operations)
    # =================================================================
    if source_type == 'unified_audit_log':
        operation = event.get('operation', '')

        # Persistence operations = interesting
        persistence_ops = {
            'Set-InboxRule', 'New-InboxRule', 'Add-MailboxPermission',
            'New-TransportRule', 'Set-TransportRule', 'Set-Mailbox'
        }
        if operation in persistence_ops:
            return True

        # Data access operations = interesting
        if operation in ['MailItemsAccessed', 'MessageBind']:
            return True

    # =================================================================
    # Mailbox audit log filtering
    # =================================================================
    if source_type == 'mailbox_audit_log':
        operation = event.get('operation', '')

        # HardDelete = evidence destruction (interesting)
        if operation == 'HardDelete':
            return True

        # UpdateInboxRules = persistence (interesting)
        if operation == 'UpdateInboxRules':
            return True

    # Default: not interesting
    return False


def get_event_severity(event: Dict[str, Any]) -> str:
    """
    Determine event severity for timeline classification.

    Returns:
        Severity level: CRITICAL, ALERT, WARNING, INFO
    """
    source_type = event.get('source_type', '')

    # Persistence mechanisms = CRITICAL
    if source_type in ['inbox_rules', 'transport_rules']:
        return 'CRITICAL'

    # Privilege escalation = CRITICAL
    if source_type == 'admin_role_assignments':
        return 'CRITICAL'

    # Foreign login from high-risk country = ALERT
    if source_type == 'sign_in_logs':
        country = event.get('location_country', '')
        if country in HIGH_RISK_COUNTRIES:
            return 'ALERT'

    # Failed auth = WARNING
    if source_type == 'sign_in_logs':
        ca_status = event.get('conditional_access_status', '')
        error_code = event.get('status_error_code')
        if ca_status == 'failure' or (error_code and error_code != 0):
            return 'WARNING'

    # Password/MFA changes = ALERT
    if source_type in ['entra_audit_log', 'mfa_changes']:
        activity = event.get('activity', '').lower()
        if 'password' in activity or 'mfa' in activity:
            return 'ALERT'

    # Default = INFO
    return 'INFO'


def map_mitre_technique(event: Dict[str, Any]) -> Optional[str]:
    """
    Map event to MITRE ATT&CK technique.

    Returns:
        MITRE technique ID (e.g., T1078.004) or None
    """
    source_type = event.get('source_type', '')

    # Valid accounts (Cloud)
    if source_type == 'sign_in_logs':
        return 'T1078.004'

    # Email collection: forwarding rule
    if source_type in ['inbox_rules', 'transport_rules']:
        return 'T1114.003'

    # Account manipulation
    if source_type == 'entra_audit_log':
        activity = event.get('activity', '').lower()
        if 'role' in activity:
            return 'T1098'
        if 'password' in activity:
            return 'T1098'

    # OAuth consent phishing
    if source_type == 'oauth_consents':
        return 'T1550.001'

    # Email collection: remote
    if source_type == 'mailbox_audit_log':
        operation = event.get('operation', '')
        if operation in ['MailItemsAccessed', 'MessageBind']:
            return 'T1114.002'

    return None
