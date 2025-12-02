"""
Pytest Fixtures for PMP Testing

Provides reusable test fixtures for all test categories.
"""

import pytest
import sqlite3
import tempfile
import json
import os
from pathlib import Path
from typing import Dict, List, Any
from unittest.mock import Mock, patch
from datetime import datetime


# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest.fixture
def temp_db():
    """
    Temporary SQLite database for testing.

    Creates a clean database with PMP schema, yields path, then cleanup.

    Usage:
        def test_something(temp_db):
            conn = sqlite3.connect(temp_db)
            # ... test code
    """
    # Create temp file
    db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    db_path = db_file.name
    db_file.close()

    # Initialize schema (same as production)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Extraction runs tracking
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS api_extraction_runs (
            extraction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at TEXT NOT NULL,
            completed_at TEXT,
            status TEXT NOT NULL,
            endpoints_extracted INTEGER DEFAULT 0,
            total_records INTEGER DEFAULT 0,
            errors TEXT
        )
    """)

    # All patches table (CORRECT schema - uses patch_id)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS all_patches (
            patch_id INTEGER PRIMARY KEY,
            extraction_id INTEGER,
            bulletin_id TEXT,
            update_name TEXT,
            platform TEXT,
            patch_released_time INTEGER,
            patch_size INTEGER,
            patch_noreboot INTEGER,
            installed INTEGER,
            raw_data TEXT,
            extracted_at TEXT NOT NULL,
            FOREIGN KEY (extraction_id) REFERENCES api_extraction_runs(extraction_id)
        )
    """)

    # Supported patches table (CORRECTED schema - uses patch_id)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS supported_patches (
            patch_id INTEGER PRIMARY KEY,
            extraction_id INTEGER,
            update_id INTEGER,
            bulletin_id TEXT,
            patch_lang TEXT,
            patch_updated_time INTEGER,
            is_superceded INTEGER,
            raw_data TEXT,
            extracted_at TEXT NOT NULL,
            FOREIGN KEY (extraction_id) REFERENCES api_extraction_runs(extraction_id)
        )
    """)

    # Installed patches table (CORRECT schema - composite key)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS installed_patches (
            patch_id INTEGER,
            extraction_id INTEGER,
            bulletin_id TEXT,
            update_name TEXT,
            platform TEXT,
            patch_released_time INTEGER,
            patch_noreboot INTEGER,
            raw_data TEXT,
            extracted_at TEXT NOT NULL,
            PRIMARY KEY (patch_id, extraction_id),
            FOREIGN KEY (extraction_id) REFERENCES api_extraction_runs(extraction_id)
        )
    """)

    # Missing patches table (CORRECT schema - composite key)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS missing_patches (
            patch_id INTEGER,
            extraction_id INTEGER,
            bulletin_id TEXT,
            update_name TEXT,
            platform TEXT,
            patch_released_time INTEGER,
            patch_noreboot INTEGER,
            raw_data TEXT,
            extracted_at TEXT NOT NULL,
            PRIMARY KEY (patch_id, extraction_id),
            FOREIGN KEY (extraction_id) REFERENCES api_extraction_runs(extraction_id)
        )
    """)

    # All systems table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS all_systems (
            resource_id INTEGER PRIMARY KEY,
            extraction_id INTEGER,
            resource_health_status INTEGER,
            os_platform_name TEXT,
            branch_office_id INTEGER,
            last_patched_time INTEGER,
            total_driver_patches INTEGER,
            missing_bios_patches INTEGER,
            raw_data TEXT,
            extracted_at TEXT NOT NULL,
            FOREIGN KEY (extraction_id) REFERENCES api_extraction_runs(extraction_id)
        )
    """)

    # SOM Computers
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS som_computers (
            resource_id INTEGER PRIMARY KEY,
            extraction_id INTEGER,
            os_platform_name TEXT,
            agent_installed_on INTEGER,
            raw_data TEXT,
            extracted_at TEXT NOT NULL,
            FOREIGN KEY (extraction_id) REFERENCES api_extraction_runs(extraction_id)
        )
    """)

    # SOM Summary
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS som_summary (
            extraction_id INTEGER PRIMARY KEY,
            summary_data TEXT,
            extracted_at TEXT NOT NULL,
            FOREIGN KEY (extraction_id) REFERENCES api_extraction_runs(extraction_id)
        )
    """)

    conn.commit()
    conn.close()

    yield db_path

    # Cleanup
    try:
        os.unlink(db_path)
    except:
        pass  # Ignore cleanup errors


@pytest.fixture
def temp_db_corrected():
    """
    Temporary database with CORRECTED schema (patch_id as PRIMARY KEY).

    Use this to test the fixed version.
    """
    db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    db_path = db_file.name
    db_file.close()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Extraction runs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS api_extraction_runs (
            extraction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at TEXT NOT NULL,
            completed_at TEXT,
            status TEXT NOT NULL,
            endpoints_extracted INTEGER DEFAULT 0,
            total_records INTEGER DEFAULT 0,
            errors TEXT
        )
    """)

    # Supported patches - CORRECTED to use patch_id
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS supported_patches (
            patch_id INTEGER PRIMARY KEY,
            extraction_id INTEGER,
            bulletin_id TEXT,
            patch_lang TEXT,
            patch_updated_time INTEGER,
            is_superceded INTEGER,
            update_id INTEGER,
            raw_data TEXT,
            extracted_at TEXT NOT NULL,
            FOREIGN KEY (extraction_id) REFERENCES api_extraction_runs(extraction_id)
        )
    """)

    conn.commit()
    conn.close()

    yield db_path

    try:
        os.unlink(db_path)
    except:
        pass


@pytest.fixture
def extraction_id(temp_db):
    """
    Create an extraction run and return extraction_id.

    Usage:
        def test_something(temp_db, extraction_id):
            # extraction_id is already created
    """
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO api_extraction_runs (started_at, status)
        VALUES (?, 'running')
    """, (datetime.now().isoformat(),))

    extraction_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return extraction_id


# ============================================================================
# MOCK DATA FIXTURES
# ============================================================================

@pytest.fixture
def mock_supported_patches():
    """
    Mock API response for supported patches.

    Returns 1000 patches with realistic data including:
    - Unique patch_id (1-1000)
    - Non-unique update_id (0-9 repeating) - THIS IS THE BUG
    """
    patches = []
    for i in range(1, 1001):
        patches.append({
            'patch_id': i,
            'update_id': i % 10,  # Repeats 0-9 (NOT UNIQUE!)
            'bulletin_id': f'KB{5000000 + i}',
            'patch_lang': 'en',
            'patch_updated_time': 1701388800 + (i * 86400),
            'is_superceded': 0,
            'vendor_name': 'Microsoft',
            'severity': ['Critical', 'Important', 'Moderate'][i % 3],
            'patch_description': f'Security update {i}'
        })
    return patches


@pytest.fixture
def mock_all_patches():
    """Mock API response for all patches (smaller set)"""
    patches = []
    for i in range(1, 101):
        patches.append({
            'patch_id': i,
            'bulletin_id': f'KB{4000000 + i}',
            'update_name': f'Update {i}',
            'platform': 'Windows',
            'patch_released_time': 1701388800 + (i * 86400),
            'patch_size': 1024 * (i % 100),
            'patch_noreboot': i % 2,
            'installed': i % 3
        })
    return patches


@pytest.fixture
def mock_api_response():
    """
    Generic mock API response wrapper.

    Usage:
        response = mock_api_response
        response['supportedpatches'] = [...]
    """
    return {
        'status': 'success',
        'message_response': {}
    }


# ============================================================================
# MOCK API FIXTURES
# ============================================================================

@pytest.fixture
def mock_oauth_manager():
    """Mock PMPOAuthManager for testing without real API"""
    mock = Mock()
    mock.server_url = "https://patchmgmtplus-au.manageengine.com"
    mock.get_token.return_value = "mock_access_token_12345"
    mock.get_auth_headers.return_value = {
        'Authorization': 'Zoho-oauthtoken mock_access_token_12345',
        'Content-Type': 'application/json'
    }
    return mock


@pytest.fixture
def mock_api_success_response():
    """Mock successful API response (200 OK)"""
    mock = Mock()
    mock.status_code = 200
    mock.json.return_value = {
        'supportedpatches': [],
        'total_count': 0
    }
    mock.text = json.dumps({'supportedpatches': []})
    return mock


@pytest.fixture
def mock_api_rate_limit_response():
    """Mock rate limit API response (429 Too Many Requests)"""
    mock = Mock()
    mock.status_code = 429
    mock.text = "Rate limit exceeded"
    return mock


@pytest.fixture
def mock_api_html_throttle_response():
    """Mock HTML throttling response (Bug #4)"""
    mock = Mock()
    mock.status_code = 200
    mock.text = '<!DOCTYPE html><html><body>Please wait...</body></html>'
    mock.json.side_effect = ValueError("Not JSON")
    return mock


# ============================================================================
# UTILITY FIXTURES
# ============================================================================

@pytest.fixture
def db_helper():
    """
    Database helper functions for testing.

    Usage:
        def test_something(temp_db, db_helper):
            db_helper.insert_patch(temp_db, {'patch_id': 1, ...})
            count = db_helper.get_count(temp_db, 'supported_patches')
    """
    class DBHelper:
        @staticmethod
        def get_count(db_path: str, table: str) -> int:
            """Get record count from table"""
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            conn.close()
            return count

        @staticmethod
        def get_schema(db_path: str, table: str) -> Dict[str, Any]:
            """Get table schema including PRIMARY KEY"""
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Get table info
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()

            # Get PRIMARY KEY
            cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,))
            create_sql = cursor.fetchone()[0]

            conn.close()

            # Parse PRIMARY KEY from CREATE statement
            primary_key = None
            if 'PRIMARY KEY' in create_sql:
                # Simple extraction (works for single-column PKs)
                for col in columns:
                    if col[5] == 1:  # pk column in PRAGMA table_info
                        primary_key = col[1]  # column name
                        break

            return {
                'columns': [col[1] for col in columns],
                'primary_key': primary_key,
                'create_sql': create_sql
            }

        @staticmethod
        def record_exists(db_path: str, table: str, **kwargs) -> bool:
            """Check if record exists with given criteria"""
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            where_clause = " AND ".join([f"{k} = ?" for k in kwargs.keys()])
            values = tuple(kwargs.values())

            cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {where_clause}", values)
            count = cursor.fetchone()[0]
            conn.close()

            return count > 0

        @staticmethod
        def get_record(db_path: str, table: str, **kwargs) -> Dict:
            """Get single record matching criteria"""
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            where_clause = " AND ".join([f"{k} = ?" for k in kwargs.keys()])
            values = tuple(kwargs.values())

            cursor.execute(f"SELECT * FROM {table} WHERE {where_clause}", values)
            row = cursor.fetchone()
            conn.close()

            return dict(row) if row else None

        @staticmethod
        def insert_mock_records(db_path: str, table: str, count: int, extraction_id: int = 1):
            """Insert mock records for testing resume capability"""
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            for i in range(1, count + 1):
                cursor.execute(f"""
                    INSERT INTO {table}
                    (patch_id, extraction_id, bulletin_id, extracted_at)
                    VALUES (?, ?, ?, ?)
                """, (i, extraction_id, f'KB{i}', datetime.now().isoformat()))

            conn.commit()
            conn.close()

    return DBHelper()


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """Pytest configuration hook"""
    # Register custom markers
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "critical: Critical path tests")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically"""
    for item in items:
        # Auto-mark critical tests
        if 'critical' in item.nodeid or 'data_integrity' in item.nodeid:
            item.add_marker(pytest.mark.critical)
