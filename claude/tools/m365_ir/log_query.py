#!/usr/bin/env python3
"""
LogQuery - Query interface for M365 IR investigation databases.

Phase 226 - IR Log Database Implementation
Provides convenient query methods and raw SQL access for investigation databases.

Usage:
    from log_database import IRLogDatabase
    from log_query import LogQuery

    db = IRLogDatabase(case_id="PIR-ACME-2025-001")
    query = LogQuery(db)

    # Convenience methods
    results = query.activity_by_ip("185.234.100.50")
    results = query.activity_by_user("victim@example.com")

    # Raw SQL
    results = query.execute("SELECT * FROM sign_in_logs WHERE location_country = ?", ("Russia",))

Author: Maia System (SRE Principal Engineer Agent)
Created: 2025-01-05
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from .log_database import IRLogDatabase

# Type alias for query results - common return type for all query methods
QueryResult = List[Dict[str, Any]]


# High-risk operations for suspicious_operations query
SUSPICIOUS_OPERATIONS = [
    'Set-InboxRule',
    'New-InboxRule',
    'Set-Mailbox',
    'Add-MailboxPermission',
    'New-TransportRule',
    'Set-TransportRule',
    'MailItemsAccessed',
    'Send',
    'SendAs',
    'SendOnBehalf',
    'Add-OAuthApp',
    'Consent to application',
    'Add app role assignment to service principal',
    'Add delegated permission grant',
    'UpdateInboxRules',
    'HardDelete',
]


class LogQuery:
    """
    Query interface for investigation database.

    Provides convenience methods for common IR queries and raw SQL access.
    All queries use parameterized statements for SQL injection prevention.
    """

    def __init__(self, db: IRLogDatabase):
        """
        Initialize query interface with database.

        Args:
            db: IRLogDatabase instance (must exist)
        """
        self._db = db

    def activity_by_ip(self, ip: str) -> QueryResult:
        """
        Get all activity from a specific IP address across all log types.

        Args:
            ip: IP address to search for

        Returns:
            List of activity dicts, sorted chronologically
        """
        results = []

        conn = self._db.connect()

        # Sign-in logs
        cursor = conn.execute("""
            SELECT timestamp, 'sign_in_logs' as source, user_principal_name as user,
                   'Login' as operation, ip_address, location_country, raw_record
            FROM sign_in_logs WHERE ip_address = ?
        """, (ip,))
        for row in cursor.fetchall():
            results.append(dict(row))

        # UAL
        cursor = conn.execute("""
            SELECT timestamp, 'unified_audit_log' as source, user_id as user,
                   operation, client_ip as ip_address, workload, raw_record
            FROM unified_audit_log WHERE client_ip = ?
        """, (ip,))
        for row in cursor.fetchall():
            results.append(dict(row))

        # Mailbox audit
        cursor = conn.execute("""
            SELECT timestamp, 'mailbox_audit_log' as source, user,
                   operation, client_ip as ip_address, '' as extra, raw_record
            FROM mailbox_audit_log WHERE client_ip = ?
        """, (ip,))
        for row in cursor.fetchall():
            results.append(dict(row))

        # Inbox rules
        cursor = conn.execute("""
            SELECT timestamp, 'inbox_rules' as source, user,
                   operation, client_ip as ip_address, forward_to, raw_record
            FROM inbox_rules WHERE client_ip = ?
        """, (ip,))
        for row in cursor.fetchall():
            results.append(dict(row))

        conn.close()

        # Sort chronologically
        results.sort(key=lambda x: x.get('timestamp', ''))

        return results

    def activity_by_user(
        self,
        user: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> QueryResult:
        """
        Get all activity for a specific user across all log types.

        Args:
            user: User email/UPN to search for
            start: Optional start time filter
            end: Optional end time filter

        Returns:
            List of activity dicts, sorted chronologically
        """
        results = []
        conn = self._db.connect()

        # Build time filter clause
        time_filter = ""
        params: List = [user]

        if start:
            time_filter += " AND timestamp >= ?"
            params.append(start.isoformat())
        if end:
            time_filter += " AND timestamp <= ?"
            params.append(end.isoformat())

        # Sign-in logs
        cursor = conn.execute(f"""
            SELECT timestamp, 'sign_in_logs' as source, user_principal_name as user,
                   'Login' as operation, ip_address, location_country as extra, raw_record
            FROM sign_in_logs WHERE user_principal_name = ? {time_filter}
        """, params)
        for row in cursor.fetchall():
            results.append(dict(row))

        # UAL - reset params for user field name difference
        params_ual = [user]
        if start:
            params_ual.append(start.isoformat())
        if end:
            params_ual.append(end.isoformat())

        cursor = conn.execute(f"""
            SELECT timestamp, 'unified_audit_log' as source, user_id as user,
                   operation, client_ip as ip_address, workload as extra, raw_record
            FROM unified_audit_log WHERE user_id = ? {time_filter}
        """, params_ual)
        for row in cursor.fetchall():
            results.append(dict(row))

        # Mailbox audit
        cursor = conn.execute(f"""
            SELECT timestamp, 'mailbox_audit_log' as source, user,
                   operation, client_ip as ip_address, folder_path as extra, raw_record
            FROM mailbox_audit_log WHERE user = ? {time_filter}
        """, params_ual)
        for row in cursor.fetchall():
            results.append(dict(row))

        # Inbox rules
        cursor = conn.execute(f"""
            SELECT timestamp, 'inbox_rules' as source, user,
                   operation, client_ip as ip_address, forward_to as extra, raw_record
            FROM inbox_rules WHERE user = ? {time_filter}
        """, params_ual)
        for row in cursor.fetchall():
            results.append(dict(row))

        conn.close()

        # Sort chronologically
        results.sort(key=lambda x: x.get('timestamp', ''))

        return results

    def suspicious_operations(self) -> QueryResult:
        """
        Get all high-risk operations from the database.

        Returns:
            List of suspicious operation dicts
        """
        results = []
        conn = self._db.connect()

        # Build operation placeholders
        placeholders = ','.join(['?' for _ in SUSPICIOUS_OPERATIONS])

        # UAL suspicious operations
        cursor = conn.execute(f"""
            SELECT timestamp, 'unified_audit_log' as source, user_id as user,
                   operation, client_ip as ip_address, workload, audit_data
            FROM unified_audit_log WHERE operation IN ({placeholders})
            ORDER BY timestamp
        """, SUSPICIOUS_OPERATIONS)
        for row in cursor.fetchall():
            results.append(dict(row))

        # Inbox rules (all are suspicious by nature)
        cursor = conn.execute("""
            SELECT timestamp, 'inbox_rules' as source, user,
                   operation, client_ip as ip_address, rule_name, forward_to
            FROM inbox_rules
            ORDER BY timestamp
        """)
        for row in cursor.fetchall():
            results.append(dict(row))

        conn.close()

        # Sort chronologically
        results.sort(key=lambda x: x.get('timestamp', ''))

        return results

    def inbox_rules_summary(self) -> QueryResult:
        """
        Get summary of all inbox rule changes.

        Returns:
            List of inbox rule dicts with forwarding targets
        """
        conn = self._db.connect()

        cursor = conn.execute("""
            SELECT timestamp, user, operation, rule_name, rule_id,
                   forward_to, forward_as_attachment_to, redirect_to,
                   delete_message, move_to_folder, client_ip
            FROM inbox_rules
            ORDER BY timestamp
        """)

        results = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return results

    def oauth_consents_summary(self) -> QueryResult:
        """
        Get summary of all OAuth app consents.

        Returns:
            List of OAuth consent dicts with risk scores
        """
        conn = self._db.connect()

        cursor = conn.execute("""
            SELECT timestamp, user_principal_name, app_id, app_display_name,
                   permissions, consent_type, client_ip, risk_score
            FROM oauth_consents
            ORDER BY timestamp
        """)

        results = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return results

    def legacy_auth_by_user(self, user: str) -> QueryResult:
        """
        Get legacy auth attempts for user.

        Supports SQL LIKE wildcard patterns for flexible matching:
        - '%@domain.com' matches all users from domain.com
        - 'john%' matches all users starting with 'john'
        - '%admin%' matches users containing 'admin'

        Args:
            user: User email/UPN. Supports SQL LIKE wildcards (%) for pattern
                  matching. If the string contains '%', a LIKE query is used;
                  otherwise an exact match is performed.

        Returns:
            List of legacy auth records, sorted by timestamp descending

        Examples:
            # Exact match
            query.legacy_auth_by_user('alice@example.com')

            # All users from a domain
            query.legacy_auth_by_user('%@example.com')

            # Users with 'admin' in name
            query.legacy_auth_by_user('%admin%')
        """
        conn = self._db.connect()

        if '%' in user:
            cursor = conn.execute("""
                SELECT * FROM legacy_auth_logs
                WHERE user_principal_name LIKE ?
                ORDER BY timestamp DESC
            """, (user,))
        else:
            cursor = conn.execute("""
                SELECT * FROM legacy_auth_logs
                WHERE user_principal_name = ?
                ORDER BY timestamp DESC
            """, (user,))

        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def legacy_auth_by_ip(self, ip: str) -> QueryResult:
        """
        Get legacy auth attempts from IP address.

        Args:
            ip: IP address to search for

        Returns:
            List of legacy auth records
        """
        conn = self._db.connect()

        cursor = conn.execute("""
            SELECT * FROM legacy_auth_logs
            WHERE ip_address = ?
            ORDER BY timestamp DESC
        """, (ip,))

        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def legacy_auth_by_client_app(self, client_app: str) -> QueryResult:
        """
        Get legacy auth attempts by client app type.

        Args:
            client_app: Client app (e.g., 'Authenticated SMTP', 'IMAP4', 'POP3')

        Returns:
            List of legacy auth records
        """
        conn = self._db.connect()

        cursor = conn.execute("""
            SELECT * FROM legacy_auth_logs
            WHERE client_app_used = ?
            ORDER BY timestamp DESC
        """, (client_app,))

        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def legacy_auth_summary(self) -> Dict:
        """
        Get summary of legacy auth usage.

        Returns:
            Dict with summary statistics
        """
        conn = self._db.connect()

        # Total events
        cursor = conn.execute("SELECT COUNT(*) FROM legacy_auth_logs")
        total_events = cursor.fetchone()[0]

        # By client app
        cursor = conn.execute("""
            SELECT client_app_used, COUNT(*) as count
            FROM legacy_auth_logs
            GROUP BY client_app_used
            ORDER BY count DESC
        """)
        by_client_app = {row[0]: row[1] for row in cursor.fetchall()}

        # By country
        cursor = conn.execute("""
            SELECT country, COUNT(*) as count
            FROM legacy_auth_logs
            WHERE country != ''
            GROUP BY country
            ORDER BY count DESC
        """)
        by_country = {row[0]: row[1] for row in cursor.fetchall()}

        # Unique users
        cursor = conn.execute("SELECT COUNT(DISTINCT user_principal_name) FROM legacy_auth_logs")
        unique_users = cursor.fetchone()[0]

        conn.close()

        return {
            'total_events': total_events,
            'by_client_app': by_client_app,
            'by_country': by_country,
            'unique_users': unique_users
        }

    def password_status(self, user: Optional[str] = None) -> QueryResult:
        """
        Get password status, optionally filtered by user.

        Args:
            user: Optional user email/UPN to filter by

        Returns:
            List of password status records
        """
        conn = self._db.connect()

        if user:
            cursor = conn.execute("""
                SELECT * FROM password_status
                WHERE user_principal_name = ?
            """, (user,))
        else:
            cursor = conn.execute("""
                SELECT * FROM password_status
                ORDER BY days_since_change DESC
            """)

        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def stale_passwords(self, days: int = 90, enabled_only: bool = False) -> QueryResult:
        """
        Get accounts with passwords older than N days.

        Args:
            days: Threshold for stale passwords (default 90)
            enabled_only: If True, only return enabled accounts

        Returns:
            List of password status records, sorted by age (oldest first)
        """
        conn = self._db.connect()

        if enabled_only:
            cursor = conn.execute("""
                SELECT * FROM password_status
                WHERE days_since_change > ?
                  AND account_enabled = 'True'
                ORDER BY days_since_change DESC
            """, (days,))
        else:
            cursor = conn.execute("""
                SELECT * FROM password_status
                WHERE days_since_change > ?
                ORDER BY days_since_change DESC
            """, (days,))

        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def entra_audit_by_user(self, user: str) -> QueryResult:
        """
        Get Entra ID audit events for a user (as target or initiator).

        Args:
            user: User email/UPN to search for

        Returns:
            List of Entra audit records, sorted by timestamp descending
        """
        conn = self._db.connect()

        cursor = conn.execute("""
            SELECT * FROM entra_audit_log
            WHERE target = ? OR initiated_by = ?
            ORDER BY timestamp DESC
        """, (user, user))

        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def entra_audit_by_activity(self, activity: str) -> QueryResult:
        """
        Get Entra audit events by activity type.

        Supports SQL LIKE wildcard patterns for flexible matching.

        Args:
            activity: Activity name (e.g., 'Update device')
                      Use % for LIKE matching (e.g., '%password%')

        Returns:
            List of Entra audit records, sorted by timestamp descending
        """
        conn = self._db.connect()

        if '%' in activity:
            cursor = conn.execute("""
                SELECT * FROM entra_audit_log
                WHERE activity LIKE ?
                ORDER BY timestamp DESC
            """, (activity,))
        else:
            cursor = conn.execute("""
                SELECT * FROM entra_audit_log
                WHERE activity = ?
                ORDER BY timestamp DESC
            """, (activity,))

        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def password_changes(self, user: str = None) -> QueryResult:
        """
        Get password-related Entra audit events.

        Args:
            user: Optional user to filter by (as target or initiator)

        Returns:
            List of password change events, sorted by timestamp descending
        """
        conn = self._db.connect()

        if user:
            cursor = conn.execute("""
                SELECT * FROM entra_audit_log
                WHERE (activity LIKE '%password%' OR activity LIKE '%PasswordProfile%')
                  AND (target = ? OR initiated_by = ?)
                ORDER BY timestamp DESC
            """, (user, user))
        else:
            cursor = conn.execute("""
                SELECT * FROM entra_audit_log
                WHERE activity LIKE '%password%' OR activity LIKE '%PasswordProfile%'
                ORDER BY timestamp DESC
            """)

        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def role_changes(self, user: str = None) -> QueryResult:
        """
        Get role assignment Entra audit events.

        Args:
            user: Optional user to filter by (as target)

        Returns:
            List of role change events, sorted by timestamp descending
        """
        conn = self._db.connect()

        if user:
            cursor = conn.execute("""
                SELECT * FROM entra_audit_log
                WHERE activity LIKE '%role%'
                  AND target = ?
                ORDER BY timestamp DESC
            """, (user,))
        else:
            cursor = conn.execute("""
                SELECT * FROM entra_audit_log
                WHERE activity LIKE '%role%'
                ORDER BY timestamp DESC
            """)

        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def entra_audit_summary(self) -> Dict:
        """
        Get summary statistics for Entra audit log.

        Returns:
            Dict with summary statistics including total_events, by_activity, by_result
        """
        conn = self._db.connect()

        # Total events
        cursor = conn.execute("SELECT COUNT(*) FROM entra_audit_log")
        total_events = cursor.fetchone()[0]

        # By activity
        cursor = conn.execute("""
            SELECT activity, COUNT(*) as count
            FROM entra_audit_log
            GROUP BY activity
            ORDER BY count DESC
        """)
        by_activity = {row[0]: row[1] for row in cursor.fetchall()}

        # By result
        cursor = conn.execute("""
            SELECT result, COUNT(*) as count
            FROM entra_audit_log
            WHERE result != ''
            GROUP BY result
            ORDER BY count DESC
        """)
        by_result = {row[0]: row[1] for row in cursor.fetchall()}

        conn.close()

        return {
            'total_events': total_events,
            'by_activity': by_activity,
            'by_result': by_result
        }

    def execute(self, sql: str, params: Tuple = ()) -> QueryResult:
        """
        Execute arbitrary SQL query with parameterization.

        Args:
            sql: SQL query (use ? for parameters)
            params: Tuple of parameter values

        Returns:
            List of result dicts
        """
        conn = self._db.connect()
        cursor = conn.execute(sql, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def execute_cross_table(
        self,
        tables: List[str],
        where: str,
        params: Tuple = ()
    ) -> QueryResult:
        """
        Query across multiple tables with UNION.

        Args:
            tables: List of table names to query
            where: WHERE clause (will be applied to each table appropriately)
            params: Parameters for the WHERE clause

        Returns:
            List of unified result dicts with source indicator
        """
        results = []
        conn = self._db.connect()

        # Table-specific column mappings for unified output
        table_queries = {
            'sign_in_logs': """
                SELECT timestamp, 'sign_in_logs' as source, user_principal_name as user,
                       'Login' as operation, ip_address, location_country as detail
                FROM sign_in_logs WHERE {where}
            """,
            'unified_audit_log': """
                SELECT timestamp, 'unified_audit_log' as source, user_id as user,
                       operation, client_ip as ip_address, workload as detail
                FROM unified_audit_log WHERE {where}
            """,
            'mailbox_audit_log': """
                SELECT timestamp, 'mailbox_audit_log' as source, user,
                       operation, client_ip as ip_address, folder_path as detail
                FROM mailbox_audit_log WHERE {where}
            """,
            'inbox_rules': """
                SELECT timestamp, 'inbox_rules' as source, user,
                       operation, client_ip as ip_address, forward_to as detail
                FROM inbox_rules WHERE {where}
            """,
            'oauth_consents': """
                SELECT timestamp, 'oauth_consents' as source, user_principal_name as user,
                       consent_type as operation, client_ip as ip_address, app_display_name as detail
                FROM oauth_consents WHERE {where}
            """
        }

        for table in tables:
            if table not in table_queries:
                continue

            # Adapt WHERE clause for table-specific column names
            adapted_where = where
            if table == 'sign_in_logs':
                adapted_where = where.replace('client_ip', 'ip_address')
            elif table in ['unified_audit_log', 'mailbox_audit_log', 'inbox_rules']:
                adapted_where = where.replace('ip_address', 'client_ip')

            query = table_queries[table].format(where=adapted_where)

            try:
                cursor = conn.execute(query, params)
                for row in cursor.fetchall():
                    results.append(dict(row))
            except Exception as e:
                # Skip tables that don't match the WHERE clause columns
                pass

        conn.close()

        # Sort chronologically
        results.sort(key=lambda x: x.get('timestamp', ''))

        return results


if __name__ == "__main__":
    # Quick demo
    import tempfile
    from datetime import timedelta

    from .log_database import IRLogDatabase

    with tempfile.TemporaryDirectory() as tmpdir:
        db = IRLogDatabase(case_id="PIR-DEMO-2025-001", base_path=tmpdir)
        db.create()

        # Insert test data
        conn = db.connect()
        now = datetime.now()
        conn.execute("""
            INSERT INTO sign_in_logs
            (timestamp, user_principal_name, ip_address, location_country, raw_record, imported_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (now.isoformat(), "test@example.com", "1.2.3.4", "Russia", "{}", now.isoformat()))
        conn.commit()
        conn.close()

        query = LogQuery(db)
        results = query.activity_by_ip("1.2.3.4")
        print(f"Activity by IP: {len(results)} results")

        results = query.execute("SELECT * FROM sign_in_logs")
        print(f"Raw SQL: {len(results)} results")
