"""
M365 IR Phase 0 Auto-Checks
Sprint 1: Critical Bug Fixes (A1-A4)
Sprint 2: False Positive Prevention (B1-B5)

This module provides automated Phase 0 checks that run immediately after log import
to identify critical security issues before detailed analysis begins.

Key Features (Sprint 1):
- A1: SQL injection prevention via parameterized queries
- A2: Proper resource management with try/finally
- A3: Inclusive threshold boundaries (>= not >)
- A4: Explicit NULL handling

Key Features (Sprint 2):
- B1: MFA context check (PRIMARY vs SECONDARY vulnerability)
- B2: Service account detection (exclude from dormant checks)
- B3: Break-glass account whitelist
- B4: FIDO2/passwordless detection
- B5: Role-based admin detection
"""

import sqlite3
import re
import os
import json
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2


def parse_timestamp(timestamp_str):
    """
    Parse timestamp with multiple format fallback.

    Args:
        timestamp_str: Timestamp string in various formats

    Returns:
        datetime: Parsed datetime object

    Raises:
        ValueError: If timestamp cannot be parsed
    """
    try:
        return datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return datetime.fromisoformat(timestamp_str)


def check_foreign_baseline(db_path, override_home_country=None):
    """
    Check foreign login baseline with SQL injection prevention.
    Uses parameterized queries exclusively (A1).
    Proper connection management with try/finally (A2).

    Args:
        db_path: Path to M365 IR investigation database
        override_home_country: Optional home country override (for testing)

    Returns:
        dict: {
            'status': 'OK' | 'NO_DATA',
            'home_country': str,
            'accounts': list of tuples with login statistics
        }
    """
    conn = sqlite3.connect(db_path)
    try:
        # Detect home country from most common location
        if override_home_country:
            home_country = override_home_country
        else:
            result = conn.execute("""
                SELECT location_country
                FROM sign_in_logs
                WHERE location_country IS NOT NULL
                GROUP BY location_country
                ORDER BY COUNT(*) DESC
                LIMIT 1
            """).fetchone()
            home_country = result[0] if result else None

        # A4: NULL handling - return early if no data
        if not home_country:
            return {'status': 'NO_DATA', 'message': 'No country data available'}

        # A1: PARAMETERIZED QUERY - prevents SQL injection
        # Use ? placeholders instead of f-strings
        foreign_baseline = conn.execute("""
            SELECT
                user_principal_name,
                COUNT(*) as total_logins,
                SUM(CASE WHEN location_country = ? THEN 1 ELSE 0 END) as home_logins,
                SUM(CASE WHEN location_country <> ? THEN 1 ELSE 0 END) as foreign_logins,
                ROUND(SUM(CASE WHEN location_country <> ? THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as foreign_pct,
                COUNT(DISTINCT location_country) as country_count
            FROM sign_in_logs
            WHERE location_country IS NOT NULL
            GROUP BY user_principal_name
            HAVING total_logins >= 5
            ORDER BY foreign_pct DESC
        """, (home_country, home_country, home_country)).fetchall()

        return {
            'status': 'OK',
            'home_country': home_country,
            'accounts': foreign_baseline
        }
    finally:
        # A2: Always close connection (even on exception)
        conn.close()


def analyze_password_hygiene(db_path, exclude_passwordless=False):
    """
    Analyze password hygiene with proper resource management and NULL handling.

    Implements:
    - A2: try/finally for connection management
    - A3: Inclusive thresholds (>= not >)
    - A4: Explicit NULL filtering
    - B4: FIDO2/passwordless exclusion (optional)

    Args:
        db_path: Path to M365 IR investigation database
        exclude_passwordless: Exclude FIDO2/passwordless accounts from analysis (default: False)

    Returns:
        dict: {
            'risk': 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'OK' | 'NO_DATA',
            'total_accounts': int,
            'over_1_year': int,
            'over_2_years': int,
            'over_3_years': int,
            'pct_over_1_year': float
        }
    """
    # B4: Get passwordless accounts to exclude if requested
    passwordless_upns = set()
    if exclude_passwordless:
        passwordless_upns = get_passwordless_accounts(db_path)

    conn = sqlite3.connect(db_path)
    try:
        # A4: Explicit NULL handling - filter out NULL dates and optionally passwordless accounts
        if exclude_passwordless and passwordless_upns:
            placeholders = ','.join('?' * len(passwordless_upns))
            query = f"""
                SELECT
                    COUNT(*) as total_accounts,
                    COUNT(CASE WHEN last_password_change < date('now', '-1 year') THEN 1 END) as over_1_year,
                    COUNT(CASE WHEN last_password_change < date('now', '-2 years') THEN 1 END) as over_2_years,
                    COUNT(CASE WHEN last_password_change < date('now', '-3 years') THEN 1 END) as over_3_years
                FROM password_status
                WHERE last_password_change IS NOT NULL
                  AND user_principal_name NOT IN ({placeholders})
            """
            result = conn.execute(query, tuple(passwordless_upns)).fetchone()
        else:
            result = conn.execute("""
                SELECT
                    COUNT(*) as total_accounts,
                    COUNT(CASE WHEN last_password_change < date('now', '-1 year') THEN 1 END) as over_1_year,
                    COUNT(CASE WHEN last_password_change < date('now', '-2 years') THEN 1 END) as over_2_years,
                    COUNT(CASE WHEN last_password_change < date('now', '-3 years') THEN 1 END) as over_3_years
                FROM password_status
                WHERE last_password_change IS NOT NULL
            """).fetchone()

        total, over_1y, over_2y, over_3y = result

        # A4: Handle empty dataset
        if total == 0:
            return {'risk': 'NO_DATA', 'message': 'No password data available'}

        pct = round((over_1y / total) * 100, 1)

        # A3: Inclusive thresholds (>= not >) - boundary values trigger alert
        if pct >= 70:
            risk = 'CRITICAL'
        elif pct >= 50:
            risk = 'HIGH'
        elif pct >= 30:
            risk = 'MEDIUM'
        else:
            risk = 'OK'

        return {
            'risk': risk,
            'total_accounts': total,
            'over_1_year': over_1y,
            'over_2_years': over_2y,
            'over_3_years': over_3y,
            'pct_over_1_year': pct
        }
    finally:
        # A2: Always close connection
        conn.close()


###############################################################################
# Sprint 2: B1 - MFA Context Check
###############################################################################

def get_mfa_enforcement_rate(conn):
    """
    Calculate MFA enforcement percentage from sign_in_logs table.

    FIX-2: Production schema stores MFA data in sign_in_logs.mfa_detail (JSON),
    not password_status.mfa_status.

    Args:
        conn: Active SQLite connection

    Returns:
        float: MFA enforcement percentage (0-100), or None if no data
    """
    # Query sign_in_logs.mfa_detail instead of password_status.mfa_status
    # mfa_detail is TEXT containing JSON - NOT NULL means MFA was used
    result = conn.execute("""
        SELECT
            COUNT(DISTINCT user_principal_name) as total,
            COUNT(DISTINCT CASE WHEN mfa_detail IS NOT NULL THEN user_principal_name END) as mfa_enabled
        FROM sign_in_logs
    """).fetchone()

    if result[0] == 0:
        return None  # No sign-in data

    return round((result[1] / result[0]) * 100, 1)


def _analyze_password_hygiene_internal(conn):
    """
    Internal helper for password hygiene analysis (reused by analyze_password_hygiene_with_context).

    Args:
        conn: Active SQLite connection

    Returns:
        dict: Password hygiene statistics (same structure as analyze_password_hygiene)
    """
    # A4: Explicit NULL handling - filter out NULL dates
    result = conn.execute("""
        SELECT
            COUNT(*) as total_accounts,
            COUNT(CASE WHEN last_password_change < date('now', '-1 year') THEN 1 END) as over_1_year,
            COUNT(CASE WHEN last_password_change < date('now', '-2 years') THEN 1 END) as over_2_years,
            COUNT(CASE WHEN last_password_change < date('now', '-3 years') THEN 1 END) as over_3_years
        FROM password_status
        WHERE last_password_change IS NOT NULL
    """).fetchone()

    total, over_1y, over_2y, over_3y = result

    # A4: Handle empty dataset
    if total == 0:
        return {'risk': 'NO_DATA', 'message': 'No password data available'}

    pct = round((over_1y / total) * 100, 1)

    # A3: Inclusive thresholds (>= not >) - boundary values trigger alert
    if pct >= 70:
        risk = 'CRITICAL'
    elif pct >= 50:
        risk = 'HIGH'
    elif pct >= 30:
        risk = 'MEDIUM'
    else:
        risk = 'OK'

    return {
        'risk': risk,
        'total_accounts': total,
        'over_1_year': over_1y,
        'over_2_years': over_2y,
        'over_3_years': over_3y,
        'pct_over_1_year': pct
    }


def analyze_password_hygiene_with_context(db_path):
    """
    Analyze password hygiene with MFA context (B1).

    MFA enforcement determines if password is PRIMARY or SECONDARY vulnerability:
    - MFA < 50%: Password is PRIMARY vulnerability (high urgency)
    - MFA 50-89%: Password is MODERATE_RISK
    - MFA >= 90%: Password is SECONDARY vulnerability (mitigated by MFA)

    Args:
        db_path: Path to M365 IR investigation database

    Returns:
        dict: {
            'risk': 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'OK' | 'NO_DATA',
            'total_accounts': int,
            'over_1_year': int,
            'over_2_years': int,
            'over_3_years': int,
            'pct_over_1_year': float,
            'mfa_rate': float | None,
            'context': 'PRIMARY_VULNERABILITY' | 'SECONDARY_VULNERABILITY' | 'MODERATE_RISK' | 'UNKNOWN_MFA'
        }
    """
    conn = sqlite3.connect(db_path)
    try:
        # Get MFA context first
        mfa_rate = get_mfa_enforcement_rate(conn)

        # Get password hygiene (reuse existing logic)
        password_result = _analyze_password_hygiene_internal(conn)

        # Determine context
        if mfa_rate is None:
            context = 'UNKNOWN_MFA'
        elif mfa_rate < 50:
            context = 'PRIMARY_VULNERABILITY'
        elif mfa_rate >= 90:
            context = 'SECONDARY_VULNERABILITY'
        else:
            context = 'MODERATE_RISK'

        password_result['mfa_rate'] = mfa_rate
        password_result['context'] = context

        return password_result
    finally:
        # A2: Always close connection
        conn.close()


###############################################################################
# Sprint 2: B2 - Service Account Detection
###############################################################################

SERVICE_ACCOUNT_PATTERNS = [
    r'^svc[_\-\.]',       # svc_backup, svc-api
    r'^service[_\-\.]',   # service_account
    r'^app[_\-\.]',       # app-integration
    r'^noreply@',         # noreply@
    r'^api[_\-\.]',       # api.connector
]


def is_service_account(upn):
    """
    Detect service accounts by naming convention (B2).

    Service accounts typically use app-only authentication and have 0 interactive logins,
    but this is intentional and should not trigger dormant account alerts.

    Args:
        upn: User principal name (email address)

    Returns:
        bool: True if account matches service account patterns
    """
    upn_lower = upn.lower()
    for pattern in SERVICE_ACCOUNT_PATTERNS:
        if re.search(pattern, upn_lower):
            return True
    return False


def detect_dormant_accounts(db_path, exclude_service=True, window_days=60, breakglass_whitelist=None):
    """
    Detect dormant accounts with service account exclusion (B2) and break-glass whitelist (B3).

    A dormant account is one with no sign-in activity in the last window_days.
    Service accounts and break-glass accounts are excluded.

    Args:
        db_path: Path to M365 IR investigation database
        exclude_service: Exclude service accounts from dormant detection (default: True)
        window_days: Lookback window in days (default: 60)
        breakglass_whitelist: List of UPNs to exclude (break-glass accounts)

    Returns:
        dict: {
            'dormant_accounts': [{'upn': str, 'days_since_login': int}, ...],
            'excluded_service_accounts': [str, ...] if exclude_service=True,
            'excluded_breakglass_accounts': [str, ...] if breakglass_whitelist provided
        }
    """
    conn = sqlite3.connect(db_path)
    try:
        # Optimized: Single aggregated query with LEFT JOIN
        # Get all accounts with their last login timestamp in one query
        all_accounts_with_logins = conn.execute("""
            SELECT DISTINCT ps.user_principal_name,
                   MAX(sl.timestamp) as last_login_timestamp
            FROM password_status ps
            LEFT JOIN sign_in_logs sl ON ps.user_principal_name = sl.user_principal_name
            GROUP BY ps.user_principal_name
        """).fetchall()

        dormant_accounts = []
        excluded_service = []
        excluded_breakglass = []

        breakglass_set = set(breakglass_whitelist) if breakglass_whitelist else set()

        for upn, last_login_timestamp in all_accounts_with_logins:
            # Check if break-glass account and should be excluded (B3)
            if upn in breakglass_set:
                excluded_breakglass.append(upn)
                continue

            # Check if service account and should be excluded (B2)
            if exclude_service and is_service_account(upn):
                excluded_service.append(upn)
                continue

            # Check if dormant
            if not last_login_timestamp:
                # No login records = dormant
                dormant_accounts.append({'upn': upn, 'days_since_login': None})
            else:
                # Calculate days since last login (single query via SQLite julianday)
                days_since = conn.execute("""
                    SELECT julianday('now') - julianday(?)
                """, (last_login_timestamp,)).fetchone()[0]

                if days_since >= window_days:
                    dormant_accounts.append({'upn': upn, 'days_since_login': int(days_since)})

        result = {'dormant_accounts': dormant_accounts}
        if exclude_service:
            result['excluded_service_accounts'] = excluded_service
        if breakglass_whitelist:
            result['excluded_breakglass_accounts'] = excluded_breakglass

        return result
    finally:
        # A2: Always close connection
        conn.close()


###############################################################################
# Sprint 2: B3 - Break-Glass Account Whitelist
###############################################################################

def load_breakglass_whitelist():
    """
    Load break-glass account whitelist from config (B3).

    Break-glass accounts are emergency admin accounts that intentionally have
    no recent activity but should not trigger dormant account alerts.

    Returns:
        list: List of UPNs in the break-glass whitelist, or empty list if config not found
    """
    config_path = os.path.expanduser('~/.maia/config/breakglass_accounts.json')
    if os.path.exists(config_path):
        try:
            with open(config_path) as f:
                config = json.load(f)
                return config.get('accounts', [])
        except (IOError, json.JSONDecodeError):
            return []
    return []


###############################################################################
# Sprint 2: B4 - FIDO2/Passwordless Detection
###############################################################################

def get_passwordless_accounts(db_path):
    """
    Get accounts using FIDO2/passwordless authentication (B4).

    Passwordless accounts don't rely on passwords and should not be included
    in password hygiene analysis.

    Args:
        db_path: Path to M365 IR investigation database

    Returns:
        set: Set of UPNs using passwordless authentication methods
    """
    conn = sqlite3.connect(db_path)
    try:
        result = conn.execute("""
            SELECT DISTINCT user_principal_name
            FROM sign_in_logs
            WHERE auth_method IN ('FIDO2', 'fido2', 'CertificateBasedAuthentication', 'WindowsHello')
        """).fetchall()
        return {row[0] for row in result}
    finally:
        # A2: Always close connection
        conn.close()


###############################################################################
# Sprint 2: B5 - Role-Based Admin Detection
###############################################################################

ADMIN_ROLES = {
    'Global Administrator',
    'Privileged Role Administrator',
    'Privileged Authentication Administrator',
    'Security Administrator',
    'Exchange Administrator',
    'SharePoint Administrator',
    'User Administrator',
    'Billing Administrator',
    'Application Administrator',
}

ADMIN_NAME_PATTERNS = [
    r'admin',
    r'sysadmin',
    r'itadmin',
    r'administrator',
]


def get_admin_accounts(db_path, fallback_to_naming=True):
    """
    Get admin accounts by role assignment with naming convention fallback (B5).

    Role-based detection is more accurate than naming conventions. If no role
    data is available, falls back to naming pattern detection.

    Args:
        db_path: Path to M365 IR investigation database
        fallback_to_naming: If True, use naming patterns when no role data available

    Returns:
        set: Set of UPNs identified as admin accounts
    """
    conn = sqlite3.connect(db_path)
    try:
        # Try role-based detection first
        try:
            role_admins = conn.execute("""
                SELECT DISTINCT target_user
                FROM entra_audit_log
                WHERE activity LIKE '%role%'
                  AND activity LIKE '%add%'
                  AND result = 'success'
            """).fetchall()

            if role_admins:
                return {row[0] for row in role_admins if row[0]}
        except sqlite3.OperationalError:
            # Table doesn't exist, fall through to naming convention
            pass

        # Fallback to naming convention if no role data
        if fallback_to_naming:
            all_accounts = conn.execute("""
                SELECT DISTINCT user_principal_name
                FROM password_status
            """).fetchall()

            admin_accounts = set()
            for (upn,) in all_accounts:
                upn_lower = upn.lower()
                for pattern in ADMIN_NAME_PATTERNS:
                    if re.search(pattern, upn_lower):
                        admin_accounts.add(upn)
                        break

            return admin_accounts

        return set()
    finally:
        # A2: Always close connection
        conn.close()


# ============================================================================
# SPRINT 3: FALSE NEGATIVE PREVENTION (C1-C3)
# ============================================================================


def detect_logging_tampering(db_path):
    """
    Detect attempts to disable or tamper with cloud audit logging (C1 - T1562.008).

    MITRE ATT&CK T1562.008: Impair Defenses - Disable Cloud Logs
    Attackers disable logging to hide their activities.

    Detection Methods:
    1. Entra ID audit log changes (service principal updates, policy changes)
    2. Exchange/M365 unified audit log disable commands

    Args:
        db_path: Path to M365 IR investigation database

    Returns:
        dict: {
            'logging_changes': List of logging tampering events,
            'risk_level': 'CRITICAL' if any found, else 'OK',
            'mitre_technique': 'T1562.008'
        }
    """
    conn = sqlite3.connect(db_path)
    try:
        logging_changes = []

        # Check Entra ID audit log for logging configuration changes
        try:
            entra_events = conn.execute("""
                SELECT timestamp, activity, initiated_by
                FROM entra_audit_log
                WHERE (activity LIKE '%service principal%'
                   OR activity LIKE '%directory properties%'
                   OR activity LIKE '%policy%')
                  AND result = 'success'
                ORDER BY timestamp DESC
            """).fetchall()

            for timestamp, activity, user in entra_events:
                logging_changes.append({
                    'timestamp': timestamp,
                    'activity': activity,
                    'user': user,
                    'source': 'entra_audit_log'
                })
        except sqlite3.OperationalError:
            # Table doesn't exist, skip
            pass

        # Check unified audit log for Exchange audit disable commands
        try:
            unified_events = conn.execute("""
                SELECT timestamp, user_id, operation
                FROM unified_audit_log
                WHERE (operation LIKE '%AdminAuditLog%'
                   OR operation LIKE '%MailboxAuditBypass%')
                  AND result_status = 'Success'
                ORDER BY timestamp DESC
            """).fetchall()

            for timestamp, user, operation in unified_events:
                logging_changes.append({
                    'timestamp': timestamp,
                    'activity': operation,
                    'user': user,
                    'source': 'unified_audit_log'
                })
        except sqlite3.OperationalError:
            # Table doesn't exist, skip
            pass

        # Determine risk level
        risk_level = 'CRITICAL' if logging_changes else 'OK'

        return {
            'logging_changes': logging_changes,
            'risk_level': risk_level,
            'mitre_technique': 'T1562.008'
        }
    finally:
        # A2: Always close connection
        conn.close()


def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance in kilometers using Haversine formula.

    Args:
        lat1, lon1: Latitude and longitude of first point (degrees)
        lat2, lon2: Latitude and longitude of second point (degrees)

    Returns:
        float: Distance in kilometers
    """
    R = 6371  # Earth radius in km

    # Convert degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    # Haversine formula
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))

    return R * c


def detect_impossible_travel(db_path, speed_threshold_mph=500):
    """
    Detect geographically impossible logins (C2).

    FIX-3: Production schema stores coordinates in location_coordinates TEXT ("lat,lon"),
    not separate latitude/longitude columns.

    Identifies cases where a user signs in from locations that are impossible
    to reach within the time between logins (e.g., NYC to Beijing in 1.5 hours).

    Args:
        db_path: Path to M365 IR investigation database
        speed_threshold_mph: Maximum reasonable travel speed in mph (default: 500)

    Returns:
        dict: {
            'impossible_travel_events': List of impossible travel events,
            'risk_level': 'CRITICAL' if any found, else 'OK'
        }
    """
    conn = sqlite3.connect(db_path)
    try:
        impossible_travel_events = []

        # Get all sign-ins with coordinates, ordered by user and timestamp
        # FIX-3: Query location_coordinates instead of latitude, longitude
        # A4: Explicitly filter NULL coordinates
        sign_ins = conn.execute("""
            SELECT user_principal_name, timestamp, location_country, location_coordinates
            FROM sign_in_logs
            WHERE location_coordinates IS NOT NULL
            ORDER BY user_principal_name, timestamp
        """).fetchall()

        # Group by user and check consecutive logins
        current_user = None
        prev_login = None

        for upn, timestamp, country, coords_str in sign_ins:
            # FIX-3: Parse "lat,lon" string into floats
            try:
                lat_str, lon_str = coords_str.split(',')
                lat = float(lat_str.strip())
                lon = float(lon_str.strip())
            except (ValueError, AttributeError):
                # Skip malformed coordinates
                continue
            if upn != current_user:
                # New user, reset tracking
                current_user = upn
                prev_login = (timestamp, country, lat, lon)
                continue

            # Check distance and time between consecutive logins
            prev_timestamp, prev_country, prev_lat, prev_lon = prev_login

            # Calculate distance in km
            distance_km = calculate_distance(prev_lat, prev_lon, lat, lon)

            # Calculate time difference in hours
            try:
                time1 = parse_timestamp(prev_timestamp)
                time2 = parse_timestamp(timestamp)
            except ValueError:
                # Skip if timestamps can't be parsed
                prev_login = (timestamp, country, lat, lon)
                continue

            time_delta = time2 - time1
            time_hours = time_delta.total_seconds() / 3600

            # Skip if time is zero or negative (data quality issue)
            if time_hours <= 0:
                prev_login = (timestamp, country, lat, lon)
                continue

            # Calculate travel speed in mph
            distance_miles = distance_km * 0.621371  # Convert km to miles
            speed_mph = distance_miles / time_hours

            # Flag if speed exceeds threshold
            if speed_mph > speed_threshold_mph:
                impossible_travel_events.append({
                    'upn': upn,
                    'login1': {
                        'timestamp': prev_timestamp,
                        'country': prev_country,
                        'coords': f'{prev_lat},{prev_lon}'
                    },
                    'login2': {
                        'timestamp': timestamp,
                        'country': country,
                        'coords': f'{lat},{lon}'
                    },
                    'distance_km': round(distance_km, 2),
                    'time_hours': round(time_hours, 2),
                    'speed_mph': round(speed_mph, 2),
                    'threshold_mph': speed_threshold_mph
                })

            # Update previous login for next comparison
            prev_login = (timestamp, country, lat, lon)

        # Determine risk level
        risk_level = 'CRITICAL' if impossible_travel_events else 'OK'

        return {
            'impossible_travel_events': impossible_travel_events,
            'risk_level': risk_level
        }
    finally:
        # A2: Always close connection
        conn.close()


def detect_mfa_bypass(db_path, threshold_hours=24):
    """
    Detect bidirectional MFA bypass attempts (C3).

    Identifies cases where MFA is enabled and then disabled within a short
    timeframe, which may indicate an attacker bypassing security controls.

    Args:
        db_path: Path to M365 IR investigation database
        threshold_hours: Maximum time between enable/disable to flag (default: 24)

    Returns:
        dict: {
            'mfa_bypass_attempts': List of MFA bypass attempts,
            'risk_level': 'CRITICAL' if <1 hour, 'HIGH' if <24 hours, else 'OK'
        }
    """
    conn = sqlite3.connect(db_path)
    try:
        mfa_bypass_attempts = []

        # Get all MFA change events ordered by user and timestamp
        try:
            mfa_events = conn.execute("""
                SELECT user, timestamp, activity_display_name
                FROM mfa_changes
                WHERE activity_display_name IS NOT NULL
                ORDER BY user, timestamp
            """).fetchall()
        except sqlite3.OperationalError:
            # Table doesn't exist
            return {
                'mfa_bypass_attempts': [],
                'risk_level': 'OK'
            }

        # Group by user and look for Enable → Disable pattern
        current_user = None
        enable_timestamp = None

        for user, timestamp, activity in mfa_events:
            activity_lower = activity.lower()

            if user != current_user:
                # New user, reset tracking
                current_user = user
                enable_timestamp = None

            # Check for Enable event
            if 'enable' in activity_lower and 'disable' not in activity_lower:
                enable_timestamp = timestamp
                continue

            # Check for Disable event
            if 'disable' in activity_lower:
                # If we have a previous Enable event, check time delta
                if enable_timestamp:
                    try:
                        time1 = parse_timestamp(enable_timestamp)
                        time2 = parse_timestamp(timestamp)
                    except ValueError:
                        # Skip if timestamps can't be parsed
                        enable_timestamp = None
                        continue

                    time_delta = time2 - time1
                    time_delta_hours = time_delta.total_seconds() / 3600

                    # Flag if within threshold
                    if time_delta_hours <= threshold_hours and time_delta_hours > 0:
                        mfa_bypass_attempts.append({
                            'upn': user,
                            'enabled_timestamp': enable_timestamp,
                            'disabled_timestamp': timestamp,
                            'time_delta_hours': round(time_delta_hours, 2),
                            'threshold_hours': threshold_hours
                        })

                # Reset enable_timestamp after processing
                enable_timestamp = None

        # Determine risk level
        if mfa_bypass_attempts:
            # CRITICAL if any bypass happened in less than 1 hour
            min_delta = min(attempt['time_delta_hours'] for attempt in mfa_bypass_attempts)
            if min_delta < 1:
                risk_level = 'CRITICAL'
            else:
                risk_level = 'HIGH'
        else:
            risk_level = 'OK'

        return {
            'mfa_bypass_attempts': mfa_bypass_attempts,
            'risk_level': risk_level
        }
    finally:
        # A2: Always close connection
        conn.close()
