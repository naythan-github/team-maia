"""
Pytest fixtures for M365 IR Data Quality System tests.

Provides reusable test databases, synthetic data, and helper functions.
"""

import pytest
import sqlite3
import tempfile
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json


@pytest.fixture
def temp_db():
    """Create a temporary SQLite database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def oculus_test_db(temp_db):
    """
    Create a test database modeled after the PIR-OCULUS case.

    This fixture recreates the exact scenario that caused the forensic error:
    - sign_in_logs with status_error_code (100% uniform, unreliable)
    - sign_in_logs with conditional_access_status (ground truth)
    - 8 compromised accounts, 188 successful foreign logins
    """
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    # Create sign_in_logs table
    cursor.execute("""
        CREATE TABLE sign_in_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            user_principal_name TEXT NOT NULL,
            user_id TEXT NOT NULL,
            app_display_name TEXT,
            location_country TEXT,
            location_city TEXT,
            ip_address TEXT,
            status_error_code INTEGER,
            status_failure_reason TEXT,
            conditional_access_status TEXT,
            risk_level TEXT,
            created_datetime TEXT
        )
    """)

    # Create unified_audit_log table
    cursor.execute("""
        CREATE TABLE unified_audit_log (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            user_id TEXT NOT NULL,
            operation TEXT NOT NULL,
            result_status TEXT,
            client_ip TEXT,
            item_type TEXT,
            created_datetime TEXT
        )
    """)

    # Create legacy_auth_logs table
    cursor.execute("""
        CREATE TABLE legacy_auth_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            user_principal_name TEXT NOT NULL,
            app_display_name TEXT,
            status_error_code INTEGER,
            status_failure_reason TEXT,
            location_country TEXT,
            ip_address TEXT,
            created_datetime TEXT
        )
    """)

    # Insert synthetic Oculus-like data
    # 188 successful foreign logins (breach)
    base_time = datetime(2025, 11, 4, 10, 0, 0)
    compromised_accounts = [
        'admin@oculus.com',
        'user1@oculus.com',
        'user2@oculus.com',
        'user3@oculus.com',
        'user4@oculus.com',
        'user5@oculus.com',
        'user6@oculus.com',
        'user7@oculus.com'
    ]

    foreign_ips = [
        '103.137.210.69',  # Vietnam
        '103.163.220.192',  # Vietnam
        '119.18.1.188',  # China
        '207.180.205.36',  # US (attacker)
    ]

    # Generate 188 successful foreign logins
    for i in range(188):
        account = compromised_accounts[i % len(compromised_accounts)]
        ip = foreign_ips[i % len(foreign_ips)]
        country = 'VN' if 'vietnam' in ip.lower() or '103.' in ip else 'CN' if '119.' in ip else 'US'
        timestamp = (base_time + timedelta(hours=i * 2)).isoformat()

        cursor.execute("""
            INSERT INTO sign_in_logs (
                timestamp, user_principal_name, user_id, app_display_name,
                location_country, ip_address,
                status_error_code, conditional_access_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp, account, f'user_{i}', 'Microsoft Exchange',
            country, ip,
            1,  # status_error_code = 1 (uniform, unreliable)
            'success'  # conditional_access_status = success (ground truth)
        ))

    # Add 2,748 legitimate Australian logins (all successful)
    for i in range(2748):
        account = 'user_au_' + str(i % 50) + '@oculus.com'
        timestamp = (base_time + timedelta(hours=i)).isoformat()

        cursor.execute("""
            INSERT INTO sign_in_logs (
                timestamp, user_principal_name, user_id, app_display_name,
                location_country, ip_address,
                status_error_code, conditional_access_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp, account, f'au_user_{i}', 'Microsoft Teams',
            'AU', '203.0.113.' + str(i % 255),
            1,  # status_error_code = 1 (uniform, unreliable)
            'success'  # All legitimate AU logins successful
        ))

    # Add 51 failed login attempts (legitimate blocks)
    for i in range(51):
        timestamp = (base_time + timedelta(hours=i * 3)).isoformat()
        cursor.execute("""
            INSERT INTO sign_in_logs (
                timestamp, user_principal_name, user_id, app_display_name,
                location_country, ip_address,
                status_error_code, conditional_access_status, status_failure_reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp, 'blocked_' + str(i) + '@oculus.com', f'blocked_{i}',
            'Microsoft Exchange', 'RU', '192.0.2.' + str(i),
            1,  # status_error_code = 1 (still uniform!)
            'failure',  # conditional_access_status = failure
            'Invalid password'
        ))

    # Add 160 MailItemsAccessed events (data exfiltration proof)
    for i in range(160):
        account_idx = i % len(compromised_accounts)
        account = compromised_accounts[account_idx]
        timestamp = (base_time + timedelta(hours=i * 2 + 1)).isoformat()

        cursor.execute("""
            INSERT INTO unified_audit_log (
                timestamp, user_id, operation, result_status,
                client_ip, item_type
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            timestamp, account, 'MailItemsAccessed', 'Success',
            foreign_ips[i % len(foreign_ips)], 'Message'
        ))

    # Add 354 failed legacy auth attempts (all blocked correctly)
    for i in range(354):
        timestamp = (base_time + timedelta(hours=i)).isoformat()
        cursor.execute("""
            INSERT INTO legacy_auth_logs (
                timestamp, user_principal_name, app_display_name,
                status_error_code, location_country, ip_address, status_failure_reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp, 'legacy_' + str(i) + '@oculus.com', 'SMTP',
            50126,  # Invalid credentials
            'CN', '192.0.2.' + str(i % 255),
            'Invalid username or password'
        ))

    # Create verification_summary table (Phase 241 output)
    cursor.execute("""
        CREATE TABLE verification_summary (
            verification_id INTEGER PRIMARY KEY AUTOINCREMENT,
            log_type TEXT NOT NULL,
            total_records INTEGER NOT NULL,
            success_count INTEGER NOT NULL,
            failure_count INTEGER NOT NULL,
            success_rate REAL NOT NULL,
            verification_status TEXT NOT NULL,
            notes TEXT,
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()

    yield temp_db


@pytest.fixture
def perfect_quality_db(temp_db):
    """
    Create a test database with perfect data quality (all fields populated, consistent).

    Use this to test that quality checks PASS when data is good.
    """
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE sign_in_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            user_id TEXT NOT NULL,
            status_error_code INTEGER NOT NULL,
            conditional_access_status TEXT NOT NULL,
            result_status TEXT NOT NULL
        )
    """)

    # Insert 1000 records with perfect quality
    for i in range(1000):
        status = 'success' if i % 3 == 0 else 'failure' if i % 3 == 1 else 'notApplied'
        error_code = 0 if status == 'success' else 50126 if status == 'failure' else 53003
        result = 'Success' if status == 'success' else 'Failure'

        cursor.execute("""
            INSERT INTO sign_in_logs (timestamp, user_id, status_error_code, conditional_access_status, result_status)
            VALUES (?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            f'user_{i}',
            error_code,
            status,
            result
        ))

    conn.commit()
    conn.close()

    yield temp_db


@pytest.fixture
def bad_quality_db(temp_db):
    """
    Create a test database with BAD data quality (unpopulated fields, 100% uniform).

    Use this to test that quality checks FAIL when data is unreliable.
    """
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE sign_in_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            user_id TEXT NOT NULL,
            status_error_code INTEGER,
            conditional_access_status TEXT,
            result_status TEXT
        )
    """)

    # Insert 1000 records where status_error_code is 100% uniform (unreliable)
    for i in range(1000):
        cursor.execute("""
            INSERT INTO sign_in_logs (timestamp, user_id, status_error_code, conditional_access_status, result_status)
            VALUES (?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            f'user_{i}',
            1,  # 100% uniform!
            'success' if i % 2 == 0 else 'failure',  # This is the real ground truth
            None  # result_status unpopulated
        ))

    conn.commit()
    conn.close()

    yield temp_db


@pytest.fixture
def status_code_reference_db(temp_db):
    """
    Create a test database with status code reference data.

    Includes common Microsoft Entra ID status codes for testing lookups.
    """
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE status_code_reference (
            code_id INTEGER PRIMARY KEY AUTOINCREMENT,
            log_type TEXT NOT NULL,
            field_name TEXT NOT NULL,
            code_value TEXT NOT NULL,
            meaning TEXT NOT NULL,
            severity TEXT NOT NULL,
            first_seen DATE NOT NULL,
            last_validated DATE NOT NULL,
            deprecated INTEGER DEFAULT 0,
            UNIQUE(log_type, field_name, code_value)
        )
    """)

    # Insert common status codes
    codes = [
        ('sign_in_logs', 'status_error_code', '0', 'Success', 'INFO', '2024-01-01', '2026-01-01', 0),
        ('sign_in_logs', 'status_error_code', '50126', 'Invalid username or password', 'WARNING', '2024-01-01', '2026-01-01', 0),
        ('sign_in_logs', 'status_error_code', '50053', 'Account locked', 'CRITICAL', '2024-01-01', '2026-01-01', 0),
        ('sign_in_logs', 'status_error_code', '53003', 'Access blocked by conditional access', 'WARNING', '2024-01-01', '2026-01-01', 0),
        ('sign_in_logs', 'conditional_access_status', 'success', 'Authentication succeeded', 'INFO', '2024-01-01', '2026-01-01', 0),
        ('sign_in_logs', 'conditional_access_status', 'failure', 'Authentication failed', 'WARNING', '2024-01-01', '2026-01-01', 0),
        ('sign_in_logs', 'conditional_access_status', 'notApplied', 'Conditional access not applied', 'INFO', '2024-01-01', '2026-01-01', 0),
        ('legacy_auth_logs', 'status_error_code', '0', 'Success', 'INFO', '2024-01-01', '2026-01-01', 0),
        ('legacy_auth_logs', 'status_error_code', '50126', 'Invalid username or password', 'WARNING', '2024-01-01', '2026-01-01', 0),
        ('unified_audit_log', 'result_status', 'Success', 'Operation succeeded', 'INFO', '2024-01-01', '2026-01-01', 0),
        ('unified_audit_log', 'result_status', 'Failed', 'Operation failed', 'WARNING', '2024-01-01', '2026-01-01', 0),
    ]

    cursor.executemany("""
        INSERT INTO status_code_reference
        (log_type, field_name, code_value, meaning, severity, first_seen, last_validated, deprecated)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, codes)

    conn.commit()
    conn.close()

    yield temp_db


@pytest.fixture
def synthetic_data_generator():
    """
    Provides a helper class for generating synthetic M365 log data.

    Usage:
        gen = synthetic_data_generator
        logs = gen.generate_sign_in_logs(count=100, breach=True)
    """

    class SyntheticDataGenerator:
        """Generates synthetic M365 log data for testing."""

        @staticmethod
        def generate_sign_in_logs(
            count: int = 100,
            breach: bool = False,
            uniform_status: bool = False,
            countries: List[str] = None
        ) -> List[Dict[str, Any]]:
            """
            Generate synthetic sign-in logs.

            Args:
                count: Number of records to generate
                breach: If True, include successful foreign logins
                uniform_status: If True, make status_error_code 100% uniform
                countries: List of country codes to use

            Returns:
                List of log dictionaries
            """
            logs = []
            base_time = datetime(2025, 11, 4, 10, 0, 0)
            countries = countries or ['AU', 'US', 'UK']

            for i in range(count):
                timestamp = (base_time + timedelta(hours=i)).isoformat()

                if breach and i < count // 10:  # 10% breach traffic
                    country = 'CN'
                    ip = '119.18.1.188'
                    status = 'success'
                else:
                    country = countries[i % len(countries)]
                    ip = f'203.0.{i % 256}.{(i * 7) % 256}'
                    status = 'success' if i % 5 != 0 else 'failure'

                logs.append({
                    'timestamp': timestamp,
                    'user_principal_name': f'user{i}@test.com',
                    'user_id': f'user_{i}',
                    'app_display_name': 'Microsoft Exchange',
                    'location_country': country,
                    'ip_address': ip,
                    'status_error_code': 1 if uniform_status else (0 if status == 'success' else 50126),
                    'conditional_access_status': status
                })

            return logs

        @staticmethod
        def generate_unified_audit_logs(
            count: int = 100,
            operations: List[str] = None
        ) -> List[Dict[str, Any]]:
            """Generate synthetic unified audit logs."""
            operations = operations or ['MailItemsAccessed', 'FileAccessed', 'FileSyncDownloadedFull']
            logs = []
            base_time = datetime(2025, 11, 4, 10, 0, 0)

            for i in range(count):
                logs.append({
                    'timestamp': (base_time + timedelta(hours=i)).isoformat(),
                    'user_id': f'user{i % 10}@test.com',
                    'operation': operations[i % len(operations)],
                    'result_status': 'Success' if i % 10 != 0 else 'Failed',
                    'client_ip': f'192.0.2.{i % 256}'
                })

            return logs

    return SyntheticDataGenerator()


@pytest.fixture
def assert_table_exists():
    """Helper to assert a table exists in a database."""
    def _assert(db_path: str, table_name: str):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name=?
        """, (table_name,))
        result = cursor.fetchone()
        conn.close()
        assert result is not None, f"Table {table_name} does not exist in {db_path}"
        return True

    return _assert


@pytest.fixture
def assert_record_count():
    """Helper to assert record count in a table."""
    def _assert(db_path: str, table_name: str, expected_count: int):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        actual_count = cursor.fetchone()[0]
        conn.close()
        assert actual_count == expected_count, \
            f"Expected {expected_count} records in {table_name}, got {actual_count}"
        return True

    return _assert
