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
from typing import Dict, List, Optional, Tuple, Union

from .log_database import IRLogDatabase


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

    def activity_by_ip(self, ip: str) -> List[Dict]:
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
    ) -> List[Dict]:
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

    def suspicious_operations(self) -> List[Dict]:
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

    def inbox_rules_summary(self) -> List[Dict]:
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

    def oauth_consents_summary(self) -> List[Dict]:
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

    def execute(self, sql: str, params: Tuple = ()) -> List[Dict]:
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
    ) -> List[Dict]:
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
