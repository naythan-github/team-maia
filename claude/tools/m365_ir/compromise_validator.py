#!/usr/bin/env python3
"""
Post-Compromise Validator - Phase 261.3

Validates whether a successful authentication represents actual account compromise
by analyzing 11 post-authentication indicators within a 72-hour window.

The 11 indicators:
1. mailbox_access_from_ip - Mailbox access from the sign-in IP
2. ual_operations_from_ip - UAL operations from the sign-in IP
3. inbox_rules_created - Inbox rules created after sign-in
4. password_changed - Password changed after sign-in
5. follow_on_signins - Follow-on sign-ins from same IP
6. persistence_mechanisms - MFA/auth method changes
7. data_exfiltration - Large file downloads/shares
8. oauth_app_consents - OAuth app consents from IP (NEW)
9. mfa_modifications - MFA registration changes (NEW)
10. delegate_access_changes - Mailbox delegate access changes (NEW)
11. orphan_ual_activity - UAL activity without sign-in (token theft) (NEW)

Critical design requirements:
- User matching MUST be exact UPN (WHERE user_principal_name = ?)
- Extended window = 72 hours (not 24)
- NO_COMPROMISE confidence capped at 80% (not 100%)
- Each indicator returns: {detected: bool, confidence: float, count: int, details: dict}

Verdicts:
- NO_COMPROMISE: 0-1 indicators, confidence ≤ 80%
- LIKELY_COMPROMISE: 2-3 indicators, confidence 70-90%
- CONFIRMED_COMPROMISE: 4+ indicators or high-confidence indicators, confidence ≥ 95%

Author: Maia System
Created: 2025-01-09
Phase: 261.3
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path


def check_mailbox_access_from_ip(
    db_path: str,
    user_principal_name: str,
    ip_address: str,
    signin_time: datetime
) -> Dict[str, Any]:
    """
    Check for mailbox access from the sign-in IP within 72 hours.

    Args:
        db_path: Path to the investigation database
        user_principal_name: Exact UPN to check
        ip_address: IP address from sign-in
        signin_time: Time of the sign-in

    Returns:
        {
            'detected': bool,
            'confidence': float (0.80 if detected),
            'count': int,
            'operations': List[dict]
        }
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    end_time = signin_time + timedelta(hours=72)

    cursor.execute("""
        SELECT timestamp, operation, client_ip, folder_path, subject
        FROM mailbox_audit_log
        WHERE user = ?
          AND client_ip = ?
          AND timestamp BETWEEN ? AND ?
        ORDER BY timestamp
    """, (user_principal_name, ip_address, signin_time.isoformat(), end_time.isoformat()))

    results = cursor.fetchall()
    conn.close()

    operations = []
    for row in results:
        operations.append({
            'timestamp': row[0],
            'operation': row[1],
            'client_ip': row[2],
            'folder_path': row[3],
            'subject': row[4]
        })

    return {
        'detected': len(operations) > 0,
        'confidence': 0.80 if len(operations) > 0 else 0.0,
        'count': len(operations),
        'operations': operations
    }


def check_ual_operations_from_ip(
    db_path: str,
    user_principal_name: str,
    ip_address: str,
    signin_time: datetime
) -> Dict[str, Any]:
    """
    Check for UAL operations from the sign-in IP within 72 hours.

    Args:
        db_path: Path to the investigation database
        user_principal_name: Exact UPN to check
        ip_address: IP address from sign-in
        signin_time: Time of the sign-in

    Returns:
        {
            'detected': bool,
            'confidence': float (0.75 if detected),
            'count': int,
            'operations': List[dict]
        }
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    end_time = signin_time + timedelta(hours=72)

    cursor.execute("""
        SELECT timestamp, operation, workload, client_ip, object_id
        FROM unified_audit_log
        WHERE user_id = ?
          AND client_ip = ?
          AND timestamp BETWEEN ? AND ?
        ORDER BY timestamp
    """, (user_principal_name, ip_address, signin_time.isoformat(), end_time.isoformat()))

    results = cursor.fetchall()
    conn.close()

    operations = []
    for row in results:
        operations.append({
            'timestamp': row[0],
            'operation': row[1],
            'workload': row[2],
            'client_ip': row[3],
            'object_id': row[4]
        })

    return {
        'detected': len(operations) > 0,
        'confidence': 0.75 if len(operations) > 0 else 0.0,
        'count': len(operations),
        'operations': operations
    }


def check_inbox_rules_created(
    db_path: str,
    user_principal_name: str,
    signin_time: datetime
) -> Dict[str, Any]:
    """
    Check for inbox rules created within 72 hours after sign-in.

    Forwarding/redirecting rules have higher confidence (0.90) than other rules (0.70).

    Args:
        db_path: Path to the investigation database
        user_principal_name: Exact UPN to check
        signin_time: Time of the sign-in

    Returns:
        {
            'detected': bool,
            'confidence': float (0.90 for forwarding, 0.70 for other),
            'count': int,
            'rules': List[dict]
        }
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    end_time = signin_time + timedelta(hours=72)

    cursor.execute("""
        SELECT timestamp, operation, rule_name, forward_to, forward_as_attachment_to,
               redirect_to, delete_message, move_to_folder, conditions
        FROM inbox_rules
        WHERE user = ?
          AND timestamp BETWEEN ? AND ?
        ORDER BY timestamp
    """, (user_principal_name, signin_time.isoformat(), end_time.isoformat()))

    results = cursor.fetchall()
    conn.close()

    rules = []
    has_forwarding = False

    for row in results:
        rule = {
            'timestamp': row[0],
            'operation': row[1],
            'rule_name': row[2],
            'forward_to': row[3],
            'forward_as_attachment_to': row[4],
            'redirect_to': row[5],
            'delete_message': row[6],
            'move_to_folder': row[7],
            'conditions': row[8]
        }
        rules.append(rule)

        # Check if this is a forwarding/redirecting rule
        if row[3] or row[4] or row[5]:  # forward_to, forward_as_attachment_to, redirect_to
            has_forwarding = True

    confidence = 0.90 if has_forwarding else 0.70 if rules else 0.0

    return {
        'detected': len(rules) > 0,
        'confidence': confidence,
        'count': len(rules),
        'rules': rules
    }


def check_password_changed(
    db_path: str,
    user_principal_name: str,
    signin_time: datetime
) -> Dict[str, Any]:
    """
    Check for password change within 72 hours after sign-in.

    Args:
        db_path: Path to the investigation database
        user_principal_name: Exact UPN to check
        signin_time: Time of the sign-in

    Returns:
        {
            'detected': bool,
            'confidence': float (0.85 if detected),
            'changes': List[dict]
        }
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    end_time = signin_time + timedelta(hours=72)

    cursor.execute("""
        SELECT timestamp, operation, workload
        FROM unified_audit_log
        WHERE user_id = ?
          AND (operation LIKE '%password%' OR operation LIKE '%Password%')
          AND timestamp BETWEEN ? AND ?
        ORDER BY timestamp
    """, (user_principal_name, signin_time.isoformat(), end_time.isoformat()))

    results = cursor.fetchall()
    conn.close()

    changes = []
    for row in results:
        changes.append({
            'timestamp': row[0],
            'operation': row[1],
            'workload': row[2]
        })

    return {
        'detected': len(changes) > 0,
        'confidence': 0.85 if len(changes) > 0 else 0.0,
        'changes': changes
    }


def check_follow_on_signins(
    db_path: str,
    user_principal_name: str,
    ip_address: str,
    signin_time: datetime
) -> Dict[str, Any]:
    """
    Check for follow-on sign-ins from same IP within 72 hours.

    Args:
        db_path: Path to the investigation database
        user_principal_name: Exact UPN to check
        ip_address: IP address from sign-in
        signin_time: Time of the sign-in

    Returns:
        {
            'detected': bool,
            'confidence': float (0.70 if detected),
            'count': int,
            'signins': List[dict]
        }
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    end_time = signin_time + timedelta(hours=72)

    cursor.execute("""
        SELECT timestamp, ip_address, location_city, location_country,
               client_app, status_error_code
        FROM sign_in_logs
        WHERE user_principal_name = ?
          AND ip_address = ?
          AND timestamp > ?
          AND timestamp <= ?
        ORDER BY timestamp
    """, (user_principal_name, ip_address, signin_time.isoformat(), end_time.isoformat()))

    results = cursor.fetchall()
    conn.close()

    signins = []
    for row in results:
        signins.append({
            'timestamp': row[0],
            'ip_address': row[1],
            'location_city': row[2],
            'location_country': row[3],
            'client_app': row[4],
            'status_error_code': row[5]
        })

    return {
        'detected': len(signins) > 0,
        'confidence': 0.70 if len(signins) > 0 else 0.0,
        'count': len(signins),
        'signins': signins
    }


def check_persistence_mechanisms(
    db_path: str,
    user_principal_name: str,
    signin_time: datetime
) -> Dict[str, Any]:
    """
    Check for persistence mechanisms (MFA/auth method changes) within 72 hours.

    Args:
        db_path: Path to the investigation database
        user_principal_name: Exact UPN to check
        signin_time: Time of the sign-in

    Returns:
        {
            'detected': bool,
            'confidence': float (0.85 if detected),
            'mechanisms': List[dict]
        }
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    end_time = signin_time + timedelta(hours=72)

    # Look for auth method changes in UAL
    cursor.execute("""
        SELECT timestamp, operation, workload
        FROM unified_audit_log
        WHERE user_id = ?
          AND (operation LIKE '%auth%' OR operation LIKE '%Auth%' OR operation LIKE '%MFA%' OR operation LIKE '%mfa%')
          AND timestamp BETWEEN ? AND ?
        ORDER BY timestamp
    """, (user_principal_name, signin_time.isoformat(), end_time.isoformat()))

    results = cursor.fetchall()
    conn.close()

    mechanisms = []
    for row in results:
        mechanisms.append({
            'timestamp': row[0],
            'operation': row[1],
            'workload': row[2]
        })

    return {
        'detected': len(mechanisms) > 0,
        'confidence': 0.85 if len(mechanisms) > 0 else 0.0,
        'mechanisms': mechanisms
    }


def check_data_exfiltration(
    db_path: str,
    user_principal_name: str,
    signin_time: datetime
) -> Dict[str, Any]:
    """
    Check for data exfiltration (large downloads/shares) within 72 hours.

    Args:
        db_path: Path to the investigation database
        user_principal_name: Exact UPN to check
        signin_time: Time of the sign-in

    Returns:
        {
            'detected': bool,
            'confidence': float (0.80 if detected),
            'activities': List[dict]
        }
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    end_time = signin_time + timedelta(hours=72)

    # Look for file downloads and sharing operations
    cursor.execute("""
        SELECT timestamp, operation, workload, object_id, client_ip
        FROM unified_audit_log
        WHERE user_id = ?
          AND (operation LIKE '%Download%' OR operation LIKE '%Share%' OR operation LIKE '%Export%')
          AND timestamp BETWEEN ? AND ?
        ORDER BY timestamp
    """, (user_principal_name, signin_time.isoformat(), end_time.isoformat()))

    results = cursor.fetchall()
    conn.close()

    activities = []
    for row in results:
        activities.append({
            'timestamp': row[0],
            'operation': row[1],
            'workload': row[2],
            'object_id': row[3],
            'client_ip': row[4]
        })

    return {
        'detected': len(activities) > 0,
        'confidence': 0.80 if len(activities) > 0 else 0.0,
        'activities': activities
    }


def check_oauth_app_consents(
    db_path: str,
    user_principal_name: str,
    ip_address: str,
    signin_time: datetime
) -> Dict[str, Any]:
    """
    Check for OAuth app consents from the sign-in IP within 72 hours.

    NEW indicator in v2.0 - detects malicious app installations.

    Args:
        db_path: Path to the investigation database
        user_principal_name: Exact UPN to check
        ip_address: IP address from sign-in
        signin_time: Time of the sign-in

    Returns:
        {
            'detected': bool,
            'confidence': float (0.85 if detected),
            'count': int,
            'apps': List[dict]
        }
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    end_time = signin_time + timedelta(hours=72)

    cursor.execute("""
        SELECT timestamp, app_id, app_display_name, permissions, consent_type,
               client_ip, risk_score
        FROM oauth_consents
        WHERE user_principal_name = ?
          AND client_ip = ?
          AND timestamp BETWEEN ? AND ?
        ORDER BY timestamp
    """, (user_principal_name, ip_address, signin_time.isoformat(), end_time.isoformat()))

    results = cursor.fetchall()
    conn.close()

    apps = []
    for row in results:
        apps.append({
            'timestamp': row[0],
            'app_id': row[1],
            'app_display_name': row[2],
            'permissions': row[3],
            'consent_type': row[4],
            'client_ip': row[5],
            'risk_score': row[6]
        })

    return {
        'detected': len(apps) > 0,
        'confidence': 0.85 if len(apps) > 0 else 0.0,
        'count': len(apps),
        'apps': apps
    }


def check_mfa_modifications(
    db_path: str,
    user_principal_name: str,
    signin_time: datetime
) -> Dict[str, Any]:
    """
    Check for MFA registration changes within 72 hours.

    NEW indicator in v2.0 - detects MFA manipulation for persistence.

    Args:
        db_path: Path to the investigation database
        user_principal_name: Exact UPN to check
        signin_time: Time of the sign-in

    Returns:
        {
            'detected': bool,
            'confidence': float (0.90 if detected),
            'modifications': List[dict]
        }
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    end_time = signin_time + timedelta(hours=72)

    cursor.execute("""
        SELECT timestamp, operation, workload
        FROM unified_audit_log
        WHERE user_id = ?
          AND (operation LIKE '%security info%' OR operation LIKE '%Security info%'
               OR operation LIKE '%MFA%' OR operation LIKE '%multi-factor%')
          AND timestamp BETWEEN ? AND ?
        ORDER BY timestamp
    """, (user_principal_name, signin_time.isoformat(), end_time.isoformat()))

    results = cursor.fetchall()
    conn.close()

    modifications = []
    for row in results:
        modifications.append({
            'timestamp': row[0],
            'operation': row[1],
            'workload': row[2]
        })

    return {
        'detected': len(modifications) > 0,
        'confidence': 0.90 if len(modifications) > 0 else 0.0,
        'modifications': modifications
    }


def check_delegate_access_changes(
    db_path: str,
    user_principal_name: str,
    signin_time: datetime
) -> Dict[str, Any]:
    """
    Check for mailbox delegate access changes within 72 hours.

    NEW indicator in v2.0 - detects persistence via delegate access.

    Args:
        db_path: Path to the investigation database
        user_principal_name: Exact UPN to check
        signin_time: Time of the sign-in

    Returns:
        {
            'detected': bool,
            'confidence': float (0.85 if detected),
            'changes': List[dict]
        }
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    end_time = signin_time + timedelta(hours=72)

    # Look for delegate changes in UAL
    cursor.execute("""
        SELECT timestamp, operation, workload, object_id
        FROM unified_audit_log
        WHERE user_id = ?
          AND (operation LIKE '%delegate%' OR operation LIKE '%Delegate%'
               OR operation LIKE '%Add-MailboxPermission%' OR operation LIKE '%mailbox permission%')
          AND timestamp BETWEEN ? AND ?
        ORDER BY timestamp
    """, (user_principal_name, signin_time.isoformat(), end_time.isoformat()))

    results = cursor.fetchall()
    conn.close()

    changes = []
    for row in results:
        changes.append({
            'timestamp': row[0],
            'operation': row[1],
            'workload': row[2],
            'object_id': row[3]
        })

    return {
        'detected': len(changes) > 0,
        'confidence': 0.85 if len(changes) > 0 else 0.0,
        'changes': changes
    }


def check_orphan_ual_activity(
    db_path: str,
    user_principal_name: str,
    signin_time: datetime
) -> Dict[str, Any]:
    """
    Check for UAL activity without corresponding sign-in (token theft indicator).

    NEW indicator in v2.0 - detects token theft by finding activity from IPs
    that have no sign-in record for the user within the 72-hour window.

    This is a very high-confidence indicator (0.95) as it suggests the attacker
    is using stolen tokens without needing to authenticate.

    Args:
        db_path: Path to the investigation database
        user_principal_name: Exact UPN to check
        signin_time: Time of the sign-in

    Returns:
        {
            'detected': bool,
            'confidence': float (0.95 if detected - very high),
            'count': int,
            'orphan_activities': List[dict]
        }
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    end_time = signin_time + timedelta(hours=72)

    # Find UAL activities from IPs with no corresponding sign-in
    cursor.execute("""
        SELECT u.timestamp, u.operation, u.workload, u.client_ip, u.object_id
        FROM unified_audit_log u
        WHERE u.user_id = ?
          AND u.timestamp BETWEEN ? AND ?
          AND u.client_ip IS NOT NULL
          AND NOT EXISTS (
              SELECT 1
              FROM sign_in_logs s
              WHERE s.user_principal_name = u.user_id
                AND s.ip_address = u.client_ip
                AND s.timestamp <= u.timestamp
                AND s.timestamp >= datetime(u.timestamp, '-72 hours')
          )
        ORDER BY u.timestamp
    """, (user_principal_name, signin_time.isoformat(), end_time.isoformat()))

    results = cursor.fetchall()
    conn.close()

    orphan_activities = []
    for row in results:
        orphan_activities.append({
            'timestamp': row[0],
            'operation': row[1],
            'workload': row[2],
            'client_ip': row[3],
            'object_id': row[4]
        })

    return {
        'detected': len(orphan_activities) > 0,
        'confidence': 0.95 if len(orphan_activities) > 0 else 0.0,
        'count': len(orphan_activities),
        'orphan_activities': orphan_activities
    }


def validate_compromise(
    db_path: str,
    user_principal_name: str,
    ip_address: str,
    signin_time: datetime
) -> Dict[str, Any]:
    """
    Validate whether a successful authentication represents actual compromise.

    Analyzes 11 post-authentication indicators within a 72-hour window to determine
    if the authentication was followed by malicious activity.

    Critical design requirements:
    - User matching is EXACT UPN (no partial matching)
    - Analysis window is 72 hours (not 24)
    - NO_COMPROMISE confidence is capped at 80% (never 100%)

    Verdicts:
    - NO_COMPROMISE: 0-1 indicators, confidence ≤ 80%
    - LIKELY_COMPROMISE: 2-3 indicators, confidence 70-90%
    - CONFIRMED_COMPROMISE: 4+ indicators or very high confidence, confidence ≥ 95%

    Args:
        db_path: Path to the investigation database
        user_principal_name: Exact UPN to validate
        ip_address: IP address from the sign-in
        signin_time: Time of the sign-in

    Returns:
        {
            'verdict': str (NO_COMPROMISE|LIKELY_COMPROMISE|CONFIRMED_COMPROMISE),
            'confidence': float (0.0-1.0, NO_COMPROMISE capped at 0.80),
            'indicators_detected': int,
            'indicators': {
                'mailbox_access_from_ip': dict,
                'ual_operations_from_ip': dict,
                'inbox_rules_created': dict,
                'password_changed': dict,
                'follow_on_signins': dict,
                'persistence_mechanisms': dict,
                'data_exfiltration': dict,
                'oauth_app_consents': dict,
                'mfa_modifications': dict,
                'delegate_access_changes': dict,
                'orphan_ual_activity': dict
            },
            'summary': str
        }
    """
    # Run all 11 indicator checks
    indicators = {
        'mailbox_access_from_ip': check_mailbox_access_from_ip(db_path, user_principal_name, ip_address, signin_time),
        'ual_operations_from_ip': check_ual_operations_from_ip(db_path, user_principal_name, ip_address, signin_time),
        'inbox_rules_created': check_inbox_rules_created(db_path, user_principal_name, signin_time),
        'password_changed': check_password_changed(db_path, user_principal_name, signin_time),
        'follow_on_signins': check_follow_on_signins(db_path, user_principal_name, ip_address, signin_time),
        'persistence_mechanisms': check_persistence_mechanisms(db_path, user_principal_name, signin_time),
        'data_exfiltration': check_data_exfiltration(db_path, user_principal_name, signin_time),
        'oauth_app_consents': check_oauth_app_consents(db_path, user_principal_name, ip_address, signin_time),
        'mfa_modifications': check_mfa_modifications(db_path, user_principal_name, signin_time),
        'delegate_access_changes': check_delegate_access_changes(db_path, user_principal_name, signin_time),
        'orphan_ual_activity': check_orphan_ual_activity(db_path, user_principal_name, signin_time)
    }

    # Count detected indicators and calculate overall confidence
    detected_indicators = [name for name, result in indicators.items() if result['detected']]
    indicators_detected = len(detected_indicators)

    # Calculate weighted confidence based on detected indicators
    if indicators_detected == 0:
        # NO_COMPROMISE capped at 80%
        confidence = 0.80
        verdict = 'NO_COMPROMISE'
    else:
        # Sum confidences of detected indicators
        total_confidence = sum(indicators[name]['confidence'] for name in detected_indicators)
        avg_confidence = total_confidence / indicators_detected

        # Check for very high confidence indicators (orphan activity, MFA mods, inbox forwarding)
        high_confidence_indicators = [
            name for name in detected_indicators
            if indicators[name]['confidence'] >= 0.90
        ]

        if indicators_detected >= 4 or len(high_confidence_indicators) >= 2:
            verdict = 'CONFIRMED_COMPROMISE'
            confidence = max(0.95, avg_confidence)  # Ensure at least 0.95
        elif indicators_detected >= 2:
            verdict = 'LIKELY_COMPROMISE'
            confidence = min(0.90, max(0.70, avg_confidence))  # Between 0.70 and 0.90
        else:
            verdict = 'LIKELY_COMPROMISE'
            confidence = min(0.75, avg_confidence)

    # Generate summary
    if verdict == 'NO_COMPROMISE':
        summary = f"No post-authentication compromise indicators detected. Clean authentication from {ip_address}."
    elif verdict == 'LIKELY_COMPROMISE':
        summary = f"Detected {indicators_detected} compromise indicators: {', '.join(detected_indicators)}. Review recommended."
    else:
        summary = f"CONFIRMED COMPROMISE: {indicators_detected} indicators detected including high-confidence patterns. Immediate action required."

    return {
        'verdict': verdict,
        'confidence': confidence,
        'indicators_detected': indicators_detected,
        'indicators': indicators,
        'summary': summary,
        'user_principal_name': user_principal_name,
        'ip_address': ip_address,
        'signin_time': signin_time.isoformat(),
        'analysis_window_hours': 72
    }


if __name__ == '__main__':
    import sys
    import argparse

    parser = argparse.ArgumentParser(description='Validate post-authentication compromise')
    parser.add_argument('db_path', help='Path to investigation database')
    parser.add_argument('user_principal_name', help='User principal name (exact UPN)')
    parser.add_argument('ip_address', help='IP address from sign-in')
    parser.add_argument('signin_time', help='Sign-in time (ISO format)')

    args = parser.parse_args()

    signin_time = datetime.fromisoformat(args.signin_time)
    result = validate_compromise(args.db_path, args.user_principal_name, args.ip_address, signin_time)

    import json
    print(json.dumps(result, indent=2, default=str))
