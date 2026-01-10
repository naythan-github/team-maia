"""
Test database helpers for M365 IR Phase 0 auto-checks testing.
Provides fixtures for creating test databases with various scenarios.
"""

import sqlite3
import tempfile
import os
from datetime import datetime, timedelta


def create_test_db():
    """Create empty test database with M365 IR schema"""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE password_status (
            user_principal_name TEXT PRIMARY KEY,
            last_password_change TEXT,
            mfa_status TEXT,
            auth_method TEXT
        );

        CREATE TABLE sign_in_logs (
            id INTEGER PRIMARY KEY,
            user_principal_name TEXT,
            timestamp TEXT,
            location_country TEXT,
            ip_address TEXT,
            latitude REAL,
            longitude REAL,
            auth_method TEXT
        );

        CREATE TABLE mfa_changes (
            id INTEGER PRIMARY KEY,
            user TEXT,
            timestamp TEXT,
            activity_display_name TEXT,
            result TEXT
        );

        CREATE TABLE entra_audit_log (
            id INTEGER PRIMARY KEY,
            timestamp TEXT,
            activity TEXT,
            target_user TEXT,
            result TEXT,
            initiated_by TEXT
        );

        CREATE TABLE risky_users (
            user_principal_name TEXT PRIMARY KEY,
            risk_level TEXT
        );

        CREATE TABLE unified_audit_log (
            id INTEGER PRIMARY KEY,
            timestamp TEXT,
            user_id TEXT,
            operation TEXT,
            client_ip TEXT,
            result_status TEXT
        );
    """)
    conn.close()

    return path


def create_test_db_with_password_distribution(total, over_1_year):
    """Create test DB with specific password age distribution"""
    db_path = create_test_db()
    conn = sqlite3.connect(db_path)

    old_date = (datetime.now() - timedelta(days=400)).strftime('%Y-%m-%d')
    new_date = (datetime.now() - timedelta(days=100)).strftime('%Y-%m-%d')

    for i in range(over_1_year):
        conn.execute(
            "INSERT INTO password_status (user_principal_name, last_password_change) VALUES (?, ?)",
            (f'old_user_{i}@test.com', old_date)
        )

    for i in range(total - over_1_year):
        conn.execute(
            "INSERT INTO password_status (user_principal_name, last_password_change) VALUES (?, ?)",
            (f'new_user_{i}@test.com', new_date)
        )

    conn.commit()
    conn.close()
    return db_path


def create_test_db_with_sign_ins():
    """Create test DB with sign-in log data for testing"""
    db_path = create_test_db()
    conn = sqlite3.connect(db_path)

    # Add sample sign-ins from multiple countries
    sign_ins = [
        ('user1@test.com', '2024-01-01 10:00:00', 'AU', '1.1.1.1'),
        ('user1@test.com', '2024-01-02 10:00:00', 'AU', '1.1.1.2'),
        ('user1@test.com', '2024-01-03 10:00:00', 'US', '2.2.2.2'),
        ('user2@test.com', '2024-01-01 11:00:00', 'AU', '3.3.3.3'),
        ('user2@test.com', '2024-01-02 11:00:00', 'AU', '3.3.3.4'),
    ]

    for upn, timestamp, country, ip in sign_ins:
        conn.execute("""
            INSERT INTO sign_in_logs (user_principal_name, timestamp, location_country, ip_address)
            VALUES (?, ?, ?, ?)
        """, (upn, timestamp, country, ip))

    conn.commit()
    conn.close()
    return db_path


def create_empty_test_db():
    """Create test DB with schema but no data"""
    return create_test_db()


def add_sign_ins(db_path, sign_ins):
    """
    Add sign-in log entries to existing database.

    Args:
        db_path: Path to database
        sign_ins: List of tuples (upn, timestamp, country, coords)
                  coords format: "lat,lon" or None
    """
    conn = sqlite3.connect(db_path)
    for upn, timestamp, country, coords in sign_ins:
        if coords:
            lat, lon = coords.split(',')
        else:
            lat, lon = None, None

        conn.execute("""
            INSERT INTO sign_in_logs (user_principal_name, timestamp, location_country, latitude, longitude)
            VALUES (?, ?, ?, ?, ?)
        """, (upn, timestamp, country, lat, lon))
    conn.commit()
    conn.close()


def add_mfa_event(db_path, user, timestamp, activity):
    """Add MFA change event to database"""
    conn = sqlite3.connect(db_path)
    conn.execute("""
        INSERT INTO mfa_changes (user, timestamp, activity_display_name, result)
        VALUES (?, ?, ?, 'success')
    """, (user, timestamp, activity))
    conn.commit()
    conn.close()


def add_mfa_status(db_path, mfa_enforced_pct):
    """
    Add MFA status to password_status table.

    Args:
        db_path: Path to database
        mfa_enforced_pct: Percentage of accounts with MFA enabled (0-100)
    """
    conn = sqlite3.connect(db_path)

    # Get all accounts
    accounts = conn.execute("""
        SELECT user_principal_name FROM password_status
    """).fetchall()

    total = len(accounts)
    enabled_count = int(total * (mfa_enforced_pct / 100))

    for i, (upn,) in enumerate(accounts):
        status = 'Enabled' if i < enabled_count else 'Disabled'
        conn.execute("""
            UPDATE password_status
            SET mfa_status = ?
            WHERE user_principal_name = ?
        """, (status, upn))

    conn.commit()
    conn.close()


def add_passwords(db_path, password_data):
    """
    Add password status records and corresponding sign-in log entries.

    Args:
        db_path: Path to database
        password_data: List of tuples (upn, last_change_date, auth_method)
    """
    conn = sqlite3.connect(db_path)
    import datetime
    for upn, last_change, auth_method in password_data:
        conn.execute("""
            INSERT INTO password_status (user_principal_name, last_password_change, auth_method)
            VALUES (?, ?, ?)
        """, (upn, last_change, auth_method))

        # Also add sign-in log with auth_method
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn.execute("""
            INSERT INTO sign_in_logs (user_principal_name, timestamp, location_country, auth_method)
            VALUES (?, ?, 'US', ?)
        """, (upn, timestamp, auth_method))

    conn.commit()
    conn.close()


def add_accounts(db_path, accounts):
    """
    Add accounts with password and activity data.

    Args:
        db_path: Path to database
        accounts: List of tuples (upn, account_type, login_count, password_age_days)
    """
    conn = sqlite3.connect(db_path)

    for upn, account_type, login_count, password_age_days in accounts:
        # Add password status
        password_date = (datetime.now() - timedelta(days=password_age_days)).strftime('%Y-%m-%d')
        conn.execute("""
            INSERT INTO password_status (user_principal_name, last_password_change)
            VALUES (?, ?)
        """, (upn, password_date))

        # Add sign-in logs
        for i in range(login_count):
            timestamp = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d %H:%M:%S')
            conn.execute("""
                INSERT INTO sign_in_logs (user_principal_name, timestamp, location_country)
                VALUES (?, ?, 'AU')
            """, (upn, timestamp))

    conn.commit()
    conn.close()


def add_role_assignments(db_path, role_data):
    """
    Add role assignment events to entra_audit_log.

    Args:
        db_path: Path to database
        role_data: List of tuples (target_user, role_name)
    """
    conn = sqlite3.connect(db_path)

    for target_user, role_name in role_data:
        if role_name:  # Only add if role exists
            conn.execute("""
                INSERT INTO entra_audit_log (timestamp, activity, target_user, result)
                VALUES (?, ?, ?, 'success')
            """, (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                  f'Add member to role: {role_name}',
                  target_user))

    conn.commit()
    conn.close()


def add_audit_logs(db_path, audit_events):
    """
    Add audit log events.

    Args:
        db_path: Path to database
        audit_events: List of tuples (timestamp, activity) or (timestamp, activity, user)
    """
    conn = sqlite3.connect(db_path)
    for event in audit_events:
        if len(event) == 3:
            timestamp, activity, user = event
            conn.execute("""
                INSERT INTO entra_audit_log (timestamp, activity, initiated_by, result)
                VALUES (?, ?, ?, 'success')
            """, (timestamp, activity, user))
        else:
            timestamp, activity = event
            conn.execute("""
                INSERT INTO entra_audit_log (timestamp, activity, result)
                VALUES (?, ?, 'success')
            """, (timestamp, activity))
    conn.commit()
    conn.close()


def add_suspicious_login(db_path, user, timestamp, country):
    """Add a suspicious login event"""
    conn = sqlite3.connect(db_path)
    conn.execute("""
        INSERT INTO sign_in_logs (user_principal_name, timestamp, location_country)
        VALUES (?, ?, ?)
    """, (user, timestamp, country))
    conn.commit()
    conn.close()


def add_accounts(db_path, accounts):
    """
    Add user accounts to password_status table.

    Args:
        db_path: Path to test database
        accounts: List of tuples (upn, account_type, days_since_login, days_since_password_change)
    """
    conn = sqlite3.connect(db_path)
    try:
        import datetime
        for upn, account_type, days_since_login, days_since_password in accounts:
            # Calculate dates
            password_date = (datetime.datetime.now() - datetime.timedelta(days=days_since_password)).strftime('%Y-%m-%d')

            conn.execute("""
                INSERT OR REPLACE INTO password_status (user_principal_name, last_password_change, mfa_status)
                VALUES (?, ?, 'Disabled')
            """, (upn, password_date))

            # Add sign-in log if days_since_login is specified
            if days_since_login >= 0:
                login_date = (datetime.datetime.now() - datetime.timedelta(days=days_since_login)).strftime('%Y-%m-%d')
                conn.execute("""
                    INSERT INTO sign_in_logs (user_principal_name, timestamp, location_country)
                    VALUES (?, ?, 'US')
                """, (upn, login_date))

        conn.commit()
    finally:
        conn.close()


def add_mfa_status(db_path, mfa_enforced_pct):
    """
    Add MFA status to password_status table.

    Args:
        db_path: Path to test database
        mfa_enforced_pct: Percentage of accounts with MFA enabled (0-100)
    """
    conn = sqlite3.connect(db_path)
    try:
        # Get total accounts
        total = conn.execute("SELECT COUNT(*) FROM password_status").fetchone()[0]

        if total == 0:
            return

        # Calculate how many should have MFA enabled
        mfa_enabled_count = int((mfa_enforced_pct / 100.0) * total)

        # Update first N accounts to have MFA enabled
        conn.execute("UPDATE password_status SET mfa_status = 'Disabled'")

        if mfa_enabled_count > 0:
            conn.execute(f"""
                UPDATE password_status
                SET mfa_status = 'Enabled'
                WHERE user_principal_name IN (
                    SELECT user_principal_name
                    FROM password_status
                    LIMIT {mfa_enabled_count}
                )
            """)

        conn.commit()
    finally:
        conn.close()


def add_role_assignments(db_path, role_data):
    """
    Add role assignment records to entra_audit_log.

    Args:
        db_path: Path to test database
        role_data: List of tuples (upn, role_name)
    """
    conn = sqlite3.connect(db_path)
    import datetime
    try:
        for upn, role_name in role_data:
            if role_name:
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                activity = f"Add member to role {role_name}"
                conn.execute("""
                    INSERT INTO entra_audit_log (timestamp, activity, target_user, result)
                    VALUES (?, ?, ?, 'success')
                """, (timestamp, activity, upn))
        conn.commit()
    finally:
        conn.close()


def create_test_db_without_role_data():
    """Create test DB with minimal schema (no audit log for fallback testing)"""
    import tempfile
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE password_status (
            user_principal_name TEXT PRIMARY KEY,
            last_password_change TEXT,
            mfa_status TEXT,
            auth_method TEXT
        );
    """)
    conn.execute("""
        CREATE TABLE sign_in_logs (
            id INTEGER PRIMARY KEY,
            user_principal_name TEXT,
            timestamp TEXT,
            location_country TEXT,
            ip_address TEXT,
            latitude REAL,
            longitude REAL,
            auth_method TEXT
        );
    """)
    conn.commit()
    conn.close()

    return db_path


def cleanup_test_db(db_path):
    """Clean up test database file"""
    try:
        if os.path.exists(db_path):
            os.unlink(db_path)
    except Exception:
        pass  # Best effort cleanup


def add_unified_audit_logs(db_path, operations):
    """
    Add Exchange/Office 365 unified audit log entries.

    Args:
        db_path: Path to database
        operations: List of tuples (timestamp, user, operation)
    """
    conn = sqlite3.connect(db_path)
    try:
        for timestamp, user, operation in operations:
            conn.execute("""
                INSERT INTO unified_audit_log (timestamp, user_id, operation, result_status)
                VALUES (?, ?, ?, 'Success')
            """, (timestamp, user, operation))
        conn.commit()
    finally:
        conn.close()


def add_sign_ins_with_coords(db_path, sign_ins):
    """
    Add sign-in log entries with latitude/longitude coordinates.

    Args:
        db_path: Path to database
        sign_ins: List of tuples (upn, timestamp, country, coords)
                  coords format: "lat,lon" (e.g., "40.7128,-74.0060")
    """
    conn = sqlite3.connect(db_path)
    try:
        for upn, timestamp, country, coords in sign_ins:
            lat, lon = coords.split(',')
            conn.execute("""
                INSERT INTO sign_in_logs (user_principal_name, timestamp, location_country, latitude, longitude)
                VALUES (?, ?, ?, ?, ?)
            """, (upn, timestamp, country, float(lat), float(lon)))
        conn.commit()
    finally:
        conn.close()


def add_mfa_events(db_path, events):
    """
    Add MFA change events to mfa_changes table.

    Args:
        db_path: Path to database
        events: List of tuples (user, timestamp, activity)
    """
    conn = sqlite3.connect(db_path)
    try:
        for user, timestamp, activity in events:
            conn.execute("""
                INSERT INTO mfa_changes (user, timestamp, activity_display_name, result)
                VALUES (?, ?, ?, 'success')
            """, (user, timestamp, activity))
        conn.commit()
    finally:
        conn.close()
