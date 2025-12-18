#!/usr/bin/env python3
"""
IR Knowledge Base - Cumulative learning database for incident response.

Phase 224 - IR Automation Tools
Stores IOCs, patterns, verified apps, and customer services across investigations.

Usage:
    from ir_knowledge import IRKnowledgeBase
    kb = IRKnowledgeBase("path/to/db.sqlite")
    kb.create_investigation("PIR-FYNA-2025-001", "Fyna Foods", "fynafoods.onmicrosoft.com")
"""

import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any


class IRKnowledgeBase:
    """Knowledge base for IR investigations with cumulative learning."""

    def __init__(self, db_path: str):
        """Initialize knowledge base with database path.

        Args:
            db_path: Path to SQLite database file (created if not exists)
        """
        self.db_path = db_path
        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_database(self):
        """Initialize database schema."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Investigations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS investigations (
                investigation_id TEXT PRIMARY KEY,
                customer TEXT NOT NULL,
                tenant TEXT NOT NULL,
                status TEXT DEFAULT 'OPEN',
                created_date TEXT NOT NULL
            )
        """)

        # IOCs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS iocs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                investigation_id TEXT NOT NULL,
                ioc_type TEXT NOT NULL,
                value TEXT NOT NULL,
                context TEXT,
                status TEXT,
                created_date TEXT NOT NULL,
                FOREIGN KEY (investigation_id) REFERENCES investigations(investigation_id)
            )
        """)

        # Patterns table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                investigation_id TEXT NOT NULL,
                pattern_type TEXT NOT NULL,
                signature TEXT NOT NULL,
                confidence REAL NOT NULL,
                description TEXT,
                created_date TEXT NOT NULL,
                FOREIGN KEY (investigation_id) REFERENCES investigations(investigation_id)
            )
        """)

        # Verified apps table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS verified_apps (
                app_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                owner TEXT NOT NULL,
                permissions TEXT NOT NULL,
                verification_date TEXT NOT NULL
            )
        """)

        # Customer services table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customer_services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer TEXT NOT NULL,
                service_name TEXT NOT NULL,
                expected_ips TEXT NOT NULL,
                verified INTEGER NOT NULL,
                notes TEXT,
                created_date TEXT NOT NULL
            )
        """)

        conn.commit()
        conn.close()

    # === Investigation Methods ===

    def create_investigation(
        self,
        investigation_id: str,
        customer: str,
        tenant: str,
        status: str = "OPEN"
    ) -> str:
        """Create a new investigation record.

        Args:
            investigation_id: Unique identifier (e.g., PIR-FYNA-2025-001)
            customer: Customer name
            tenant: Microsoft tenant domain
            status: Investigation status (default: OPEN)

        Returns:
            The investigation_id

        Raises:
            sqlite3.IntegrityError: If investigation_id already exists
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO investigations (investigation_id, customer, tenant, status, created_date)
            VALUES (?, ?, ?, ?, ?)
        """, (investigation_id, customer, tenant, status, datetime.now().isoformat()))

        conn.commit()
        conn.close()

        return investigation_id

    def get_investigation(self, investigation_id: str) -> Optional[Dict[str, Any]]:
        """Get investigation by ID.

        Args:
            investigation_id: The investigation identifier

        Returns:
            Dict with investigation fields or None if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM investigations WHERE investigation_id = ?
        """, (investigation_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    def get_investigation_summary(self, investigation_id: str) -> Dict[str, int]:
        """Get investigation summary with counts.

        Args:
            investigation_id: The investigation identifier

        Returns:
            Dict with ioc_count, pattern_count
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Count IOCs
        cursor.execute("""
            SELECT COUNT(*) FROM iocs WHERE investigation_id = ?
        """, (investigation_id,))
        ioc_count = cursor.fetchone()[0]

        # Count patterns
        cursor.execute("""
            SELECT COUNT(*) FROM patterns WHERE investigation_id = ?
        """, (investigation_id,))
        pattern_count = cursor.fetchone()[0]

        conn.close()

        return {
            'ioc_count': ioc_count,
            'pattern_count': pattern_count
        }

    # === IOC Methods ===

    def add_ioc(
        self,
        investigation_id: str,
        ioc_type: str,
        value: str,
        context: str,
        status: Optional[str] = None
    ) -> int:
        """Add an IOC linked to an investigation.

        Args:
            investigation_id: The investigation to link to
            ioc_type: Type of IOC (ip, domain, hash, etc.)
            value: The IOC value
            context: Description/context for the IOC
            status: Optional status (BLOCKED, MONITOR, INVESTIGATE)

        Returns:
            The IOC id
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO iocs (investigation_id, ioc_type, value, context, status, created_date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (investigation_id, ioc_type, value, context, status, datetime.now().isoformat()))

        ioc_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return ioc_id

    def query_ioc(self, ioc_type: str, value: str) -> List[Dict[str, Any]]:
        """Query IOC by type and value.

        Args:
            ioc_type: Type of IOC to search
            value: The IOC value to search

        Returns:
            List of dicts with investigation_id and context for each match
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT iocs.*, investigations.customer
            FROM iocs
            JOIN investigations ON iocs.investigation_id = investigations.investigation_id
            WHERE ioc_type = ? AND value = ?
        """, (ioc_type, value))

        results = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return results

    # === Pattern Methods ===

    def add_pattern(
        self,
        investigation_id: str,
        pattern_type: str,
        signature: str,
        confidence: float,
        description: Optional[str] = None
    ) -> int:
        """Add a suspicious pattern to an investigation.

        Args:
            investigation_id: The investigation to link to
            pattern_type: Type of pattern (impossible_ua, off_hours, etc.)
            signature: Regex or pattern signature
            confidence: Confidence score (0.0 to 1.0)
            description: Optional description

        Returns:
            The pattern id
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO patterns (investigation_id, pattern_type, signature, confidence, description, created_date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (investigation_id, pattern_type, signature, confidence, description, datetime.now().isoformat()))

        pattern_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return pattern_id

    def query_patterns(self, pattern_type: str) -> List[Dict[str, Any]]:
        """Query patterns by type.

        Args:
            pattern_type: Type of pattern to search

        Returns:
            List of pattern dicts
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM patterns WHERE pattern_type = ?
        """, (pattern_type,))

        results = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return results

    # === Verified App Methods ===

    def add_verified_app(
        self,
        app_id: str,
        name: str,
        owner: str,
        permissions: List[str],
        verification_date: Optional[str] = None
    ) -> str:
        """Add a verified OAuth app.

        Args:
            app_id: The app's unique identifier (GUID)
            name: App display name
            owner: App owner/publisher
            permissions: List of permissions granted
            verification_date: When the app was verified (defaults to now)

        Returns:
            The app_id
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        if verification_date is None:
            verification_date = datetime.now().isoformat()

        cursor.execute("""
            INSERT INTO verified_apps (app_id, name, owner, permissions, verification_date)
            VALUES (?, ?, ?, ?, ?)
        """, (app_id, name, owner, json.dumps(permissions), verification_date))

        conn.commit()
        conn.close()

        return app_id

    def is_app_verified(self, app_id: str) -> Dict[str, Any]:
        """Check if an app is verified.

        Args:
            app_id: The app's unique identifier

        Returns:
            Dict with 'verified' boolean and app details if verified
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM verified_apps WHERE app_id = ?
        """, (app_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                'verified': True,
                'name': row['name'],
                'owner': row['owner'],
                'permissions': json.loads(row['permissions']),
                'verification_date': row['verification_date']
            }

        return {'verified': False}

    # === Customer Service Methods ===

    def add_customer_service(
        self,
        customer: str,
        service_name: str,
        expected_ips: List[str],
        verified: bool,
        notes: Optional[str] = None
    ) -> int:
        """Add a customer service mapping.

        Args:
            customer: Customer name
            service_name: Third-party service name
            expected_ips: List of expected IP addresses for this service
            verified: Whether the service usage has been verified
            notes: Optional notes about the service

        Returns:
            The service id
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO customer_services (customer, service_name, expected_ips, verified, notes, created_date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (customer, service_name, json.dumps(expected_ips), int(verified), notes, datetime.now().isoformat()))

        service_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return service_id

    def check_ip_service(self, customer: str, ip: str) -> Optional[Dict[str, Any]]:
        """Check if an IP matches a known customer service.

        Args:
            customer: Customer name
            ip: IP address to check

        Returns:
            Dict with service_name and verified status, or None if no match
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM customer_services WHERE customer = ?
        """, (customer,))

        for row in cursor.fetchall():
            expected_ips = json.loads(row['expected_ips'])
            if ip in expected_ips:
                conn.close()
                return {
                    'service_name': row['service_name'],
                    'verified': bool(row['verified']),
                    'notes': row['notes']
                }

        conn.close()
        return None

    # === Utility Methods ===

    def get_tables(self) -> List[str]:
        """Get list of all tables in the database.

        Returns:
            List of table names
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT name FROM sqlite_master WHERE type='table' ORDER BY name
        """)

        tables = [row[0] for row in cursor.fetchall()]
        conn.close()

        return tables


if __name__ == "__main__":
    # Quick demo
    import tempfile
    import os

    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    kb = IRKnowledgeBase(path)
    print(f"Created database at: {path}")
    print(f"Tables: {kb.get_tables()}")

    # Create investigation
    kb.create_investigation("PIR-TEST-001", "Test Customer", "test.onmicrosoft.com")
    print(f"Investigation: {kb.get_investigation('PIR-TEST-001')}")

    # Add IOC
    kb.add_ioc("PIR-TEST-001", "ip", "1.2.3.4", "Test IOC", "BLOCKED")
    print(f"IOC query: {kb.query_ioc('ip', '1.2.3.4')}")

    # Cleanup
    os.unlink(path)
    print("Demo complete!")
