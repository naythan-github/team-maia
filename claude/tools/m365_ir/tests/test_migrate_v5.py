#!/usr/bin/env python3
"""
TDD Tests for Database Migration v4 → v5 (Phase 264 Sprint 1.3)

Tests written FIRST per TDD methodology.
Run: pytest claude/tools/m365_ir/tests/test_migrate_v5.py -v

Author: Maia System
Created: 2026-01-11 (Phase 264)
"""

import pytest
import tempfile
import sqlite3
from pathlib import Path
import sys

# Add Maia root to path
MAIA_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

from claude.tools.m365_ir.log_database import IRLogDatabase


class TestMigrationV5Structure:
    """Test that migration v5 adds all required columns"""

    def test_migration_adds_schema_variant_column(self, temp_db_v4):
        """Migration should add schema_variant TEXT column"""
        from claude.tools.m365_ir.migrations.migrate_v5 import migrate_to_v5

        db = temp_db_v4
        migrate_to_v5(db)

        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(sign_in_logs)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        conn.close()

        assert 'schema_variant' in columns
        assert columns['schema_variant'] == 'TEXT'

    def test_migration_adds_sign_in_type_column(self, temp_db_v4):
        """Migration should add sign_in_type TEXT column"""
        from claude.tools.m365_ir.migrations.migrate_v5 import migrate_to_v5

        db = temp_db_v4
        migrate_to_v5(db)

        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(sign_in_logs)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        conn.close()

        assert 'sign_in_type' in columns
        assert columns['sign_in_type'] == 'TEXT'

    def test_migration_adds_is_service_principal_column(self, temp_db_v4):
        """Migration should add is_service_principal INTEGER DEFAULT 0"""
        from claude.tools.m365_ir.migrations.migrate_v5 import migrate_to_v5

        db = temp_db_v4
        migrate_to_v5(db)

        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(sign_in_logs)")
        columns = {row[1]: (row[2], row[4]) for row in cursor.fetchall()}
        conn.close()

        assert 'is_service_principal' in columns
        assert columns['is_service_principal'][0] == 'INTEGER'
        assert columns['is_service_principal'][1] == '0'  # DEFAULT 0

    def test_migration_adds_service_principal_fields(self, temp_db_v4):
        """Migration should add service_principal_id and service_principal_name"""
        from claude.tools.m365_ir.migrations.migrate_v5 import migrate_to_v5

        db = temp_db_v4
        migrate_to_v5(db)

        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(sign_in_logs)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        conn.close()

        assert 'service_principal_id' in columns
        assert columns['service_principal_id'] == 'TEXT'
        assert 'service_principal_name' in columns
        assert columns['service_principal_name'] == 'TEXT'

    def test_migration_adds_user_id_column(self, temp_db_v4):
        """Migration should add user_id TEXT column"""
        from claude.tools.m365_ir.migrations.migrate_v5 import migrate_to_v5

        db = temp_db_v4
        migrate_to_v5(db)

        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(sign_in_logs)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        conn.close()

        assert 'user_id' in columns
        assert columns['user_id'] == 'TEXT'

    def test_migration_adds_request_id_column(self, temp_db_v4):
        """Migration should add request_id TEXT column"""
        from claude.tools.m365_ir.migrations.migrate_v5 import migrate_to_v5

        db = temp_db_v4
        migrate_to_v5(db)

        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(sign_in_logs)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        conn.close()

        assert 'request_id' in columns
        assert columns['request_id'] == 'TEXT'

    def test_migration_adds_auth_requirement_column(self, temp_db_v4):
        """Migration should add auth_requirement TEXT column"""
        from claude.tools.m365_ir.migrations.migrate_v5 import migrate_to_v5

        db = temp_db_v4
        migrate_to_v5(db)

        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(sign_in_logs)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        conn.close()

        assert 'auth_requirement' in columns
        assert columns['auth_requirement'] == 'TEXT'

    def test_migration_adds_mfa_result_column(self, temp_db_v4):
        """Migration should add mfa_result TEXT column"""
        from claude.tools.m365_ir.migrations.migrate_v5 import migrate_to_v5

        db = temp_db_v4
        migrate_to_v5(db)

        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(sign_in_logs)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        conn.close()

        assert 'mfa_result' in columns
        assert columns['mfa_result'] == 'TEXT'

    def test_migration_adds_latency_ms_column(self, temp_db_v4):
        """Migration should add latency_ms INTEGER column"""
        from claude.tools.m365_ir.migrations.migrate_v5 import migrate_to_v5

        db = temp_db_v4
        migrate_to_v5(db)

        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(sign_in_logs)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        conn.close()

        assert 'latency_ms' in columns
        assert columns['latency_ms'] == 'INTEGER'

    def test_migration_adds_device_compliance_columns(self, temp_db_v4):
        """Migration should add device_compliant and device_managed columns"""
        from claude.tools.m365_ir.migrations.migrate_v5 import migrate_to_v5

        db = temp_db_v4
        migrate_to_v5(db)

        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(sign_in_logs)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        conn.close()

        assert 'device_compliant' in columns
        assert columns['device_compliant'] == 'INTEGER'
        assert 'device_managed' in columns
        assert columns['device_managed'] == 'INTEGER'

    def test_migration_adds_credential_key_id_column(self, temp_db_v4):
        """Migration should add credential_key_id TEXT column"""
        from claude.tools.m365_ir.migrations.migrate_v5 import migrate_to_v5

        db = temp_db_v4
        migrate_to_v5(db)

        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(sign_in_logs)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        conn.close()

        assert 'credential_key_id' in columns
        assert columns['credential_key_id'] == 'TEXT'

    def test_migration_adds_resource_id_column(self, temp_db_v4):
        """Migration should add resource_id TEXT column"""
        from claude.tools.m365_ir.migrations.migrate_v5 import migrate_to_v5

        db = temp_db_v4
        migrate_to_v5(db)

        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(sign_in_logs)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        conn.close()

        assert 'resource_id' in columns
        assert columns['resource_id'] == 'TEXT'


class TestMigrationV5Indexes:
    """Test that migration v5 creates required indexes"""

    def test_migration_creates_sign_in_type_index(self, temp_db_v4):
        """Migration should create idx_signin_type index"""
        from claude.tools.m365_ir.migrations.migrate_v5 import migrate_to_v5

        db = temp_db_v4
        migrate_to_v5(db)

        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_signin_type'")
        result = cursor.fetchone()
        conn.close()

        assert result is not None
        assert result[0] == 'idx_signin_type'

    def test_migration_creates_schema_variant_index(self, temp_db_v4):
        """Migration should create idx_signin_schema index"""
        from claude.tools.m365_ir.migrations.migrate_v5 import migrate_to_v5

        db = temp_db_v4
        migrate_to_v5(db)

        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_signin_schema'")
        result = cursor.fetchone()
        conn.close()

        assert result is not None
        assert result[0] == 'idx_signin_schema'

    def test_migration_creates_service_principal_index(self, temp_db_v4):
        """Migration should create idx_signin_service_principal index"""
        from claude.tools.m365_ir.migrations.migrate_v5 import migrate_to_v5

        db = temp_db_v4
        migrate_to_v5(db)

        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_signin_service_principal'")
        result = cursor.fetchone()
        conn.close()

        assert result is not None
        assert result[0] == 'idx_signin_service_principal'


class TestMigrationV5Idempotency:
    """Test that migration v5 is idempotent (safe to run multiple times)"""

    def test_migration_is_idempotent(self, temp_db_v4):
        """Running migration twice should not raise errors"""
        from claude.tools.m365_ir.migrations.migrate_v5 import migrate_to_v5

        db = temp_db_v4

        # First migration
        migrate_to_v5(db)

        # Second migration (should not fail)
        migrate_to_v5(db)  # Should not raise

        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(sign_in_logs)")
        columns = {row[1] for row in cursor.fetchall()}
        conn.close()

        # Verify columns still exist
        assert 'schema_variant' in columns
        assert 'sign_in_type' in columns


class TestMigrationV5BackwardCompatibility:
    """Test that migration v5 preserves existing data"""

    def test_migration_preserves_existing_records(self, temp_db_v4_with_data):
        """Existing records should remain intact after migration"""
        from claude.tools.m365_ir.migrations.migrate_v5 import migrate_to_v5

        db = temp_db_v4_with_data

        # Get record count before migration
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM sign_in_logs")
        count_before = cursor.fetchone()[0]
        conn.close()

        # Run migration
        migrate_to_v5(db)

        # Get record count after migration
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM sign_in_logs")
        count_after = cursor.fetchone()[0]
        conn.close()

        assert count_before == count_after

    def test_migration_preserves_existing_columns(self, temp_db_v4_with_data):
        """Existing column data should be preserved"""
        from claude.tools.m365_ir.migrations.migrate_v5 import migrate_to_v5

        db = temp_db_v4_with_data

        # Get existing data
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT user_principal_name, ip_address FROM sign_in_logs ORDER BY id LIMIT 1")
        original_data = cursor.fetchone()
        conn.close()

        # Run migration
        migrate_to_v5(db)

        # Verify data unchanged
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT user_principal_name, ip_address FROM sign_in_logs ORDER BY id LIMIT 1")
        after_data = cursor.fetchone()
        conn.close()

        assert original_data == after_data

    def test_migration_sets_default_values_for_new_columns(self, temp_db_v4_with_data):
        """New columns should have NULL or default values for existing records"""
        from claude.tools.m365_ir.migrations.migrate_v5 import migrate_to_v5

        db = temp_db_v4_with_data
        migrate_to_v5(db)

        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT schema_variant, sign_in_type, is_service_principal FROM sign_in_logs LIMIT 1")
        row = cursor.fetchone()
        conn.close()

        # New columns should be NULL or default
        assert row[0] is None  # schema_variant
        assert row[1] is None  # sign_in_type
        assert row[2] == 0     # is_service_principal (DEFAULT 0)


class TestMigrationV5ErrorHandling:
    """Test migration error handling"""

    def test_migration_fails_on_nonexistent_database(self):
        """Migration should fail gracefully if database doesn't exist"""
        from claude.tools.m365_ir.migrations.migrate_v5 import migrate_to_v5

        db = IRLogDatabase(case_id="PIR-NONEXISTENT", base_path="/tmp")

        with pytest.raises(ValueError, match="Database does not exist"):
            migrate_to_v5(db)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def temp_db_v4():
    """Create a temporary v4 database for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db = IRLogDatabase(case_id="PIR-TEST-MIGRATION", base_path=tmpdir)
        db.create()
        yield db


@pytest.fixture
def temp_db_v4_with_data():
    """Create a temporary v4 database with sample data"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db = IRLogDatabase(case_id="PIR-TEST-DATA", base_path=tmpdir)
        db.create()

        # Insert sample data
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sign_in_logs (
                timestamp, user_principal_name, user_display_name,
                ip_address, location_city, location_country, imported_at
            ) VALUES (
                '2025-12-04T08:19:41Z', 'test@example.com', 'Test User',
                '192.168.1.1', 'Melbourne', 'AU', '2025-12-04T10:00:00Z'
            )
        """)
        conn.commit()
        conn.close()

        yield db
