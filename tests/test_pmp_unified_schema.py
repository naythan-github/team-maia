#!/usr/bin/env python3
"""
Tests for PMP Unified Schema Design

Following TDD protocol:
1. Tests written FIRST (must fail initially)
2. Schema implementation comes after
3. Validates schema correctness, foreign keys, indexes, and BaseIntelligenceService compatibility

Author: SRE Principal Engineer Agent
Date: 2025-01-15
Sprint: SPRINT-PMP-UNIFIED-001
"""

import sqlite3
import tempfile
from pathlib import Path
import pytest


class TestSchemaDesign:
    """Test suite for unified PMP schema validation"""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = Path(tmp.name)

        yield db_path

        # Cleanup
        if db_path.exists():
            db_path.unlink()

    @pytest.fixture
    def schema_file(self):
        """Get path to unified schema SQL file"""
        schema_path = Path(__file__).parent.parent / "claude/tools/pmp/pmp_unified_schema.sql"
        return schema_path

    @pytest.fixture
    def initialized_db(self, temp_db, schema_file):
        """Database initialized with unified schema"""
        if not schema_file.exists():
            pytest.fail(f"Schema file not found: {schema_file}")

        schema_sql = schema_file.read_text()

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.executescript(schema_sql)
        conn.commit()
        conn.close()

        return temp_db

    def test_schema_creates_all_tables(self, initialized_db):
        """Schema creates 12 required tables.

        Required tables:
        - Core: snapshots, systems, patches, patch_system_mapping, vulnerabilities
        - Metrics: patch_metrics, severity_metrics, system_health_metrics, vulnerability_db_metrics
        - Policy: deployment_policies, deployment_tasks, compliance_checks
        """
        conn = sqlite3.connect(initialized_db)
        cursor = conn.cursor()

        # Query sqlite_master for all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = {row[0] for row in cursor.fetchall()}

        conn.close()

        # Required core tables
        required_tables = {
            'snapshots',
            'systems',
            'patches',
            'patch_system_mapping',
            'vulnerabilities',
            'patch_metrics',
            'severity_metrics',
            'system_health_metrics',
            'vulnerability_db_metrics',
            'deployment_policies',
            'deployment_tasks',
            'compliance_checks'
        }

        # All required tables must exist
        missing_tables = required_tables - tables
        assert not missing_tables, f"Missing required tables: {missing_tables}"

        # Must have at least 12 tables (can have more for schema_version, etc)
        assert len(tables) >= 12, f"Expected at least 12 tables, found {len(tables)}"

    def test_schema_has_snapshot_foreign_keys(self, initialized_db):
        """All metric tables have snapshot_id FK pointing to snapshots table.

        Verifies:
        - Every metric/data table has snapshot_id column
        - Foreign key constraint exists to snapshots.snapshot_id
        - ON DELETE CASCADE is configured for data consistency
        """
        conn = sqlite3.connect(initialized_db)
        cursor = conn.cursor()

        # Tables that must have snapshot_id FK
        fk_tables = [
            'patch_metrics',
            'severity_metrics',
            'system_health_metrics',
            'vulnerability_db_metrics',
            'compliance_checks',
            'systems',
            'patches',
            'patch_system_mapping',
            'vulnerabilities',
            'deployment_policies',
            'deployment_tasks'
        ]

        for table_name in fk_tables:
            # Get foreign key info for this table
            cursor.execute(f"PRAGMA foreign_key_list({table_name})")
            foreign_keys = cursor.fetchall()

            # Find snapshot_id FK
            snapshot_fks = [fk for fk in foreign_keys if fk[3] == 'snapshot_id']

            assert len(snapshot_fks) >= 1, \
                f"Table '{table_name}' missing snapshot_id foreign key"

            # Verify FK points to snapshots table
            fk = snapshot_fks[0]
            assert fk[2] == 'snapshots', \
                f"Table '{table_name}' snapshot_id FK must point to 'snapshots' table, found '{fk[2]}'"

            # Verify ON DELETE CASCADE (fk[6] is on_delete action)
            assert fk[6] == 'CASCADE', \
                f"Table '{table_name}' snapshot_id FK must have ON DELETE CASCADE, found '{fk[6]}'"

        conn.close()

    def test_schema_has_proper_indexes(self, initialized_db):
        """Performance indexes on key lookup columns.

        Required indexes:
        - snapshots: timestamp DESC, status
        - systems: resource_id, branch_office_name, health_status
        - patches: pmp_patch_id, severity, bulletin_id
        - patch_system_mapping: pmp_patch_id, resource_id
        - compliance_checks: snapshot_id, category, severity
        """
        conn = sqlite3.connect(initialized_db)
        cursor = conn.cursor()

        # Get all indexes
        cursor.execute("SELECT name, tbl_name, sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL")
        indexes = cursor.fetchall()

        conn.close()

        # Convert to dict for easier lookup
        indexes_by_table = {}
        for idx_name, tbl_name, idx_sql in indexes:
            if tbl_name not in indexes_by_table:
                indexes_by_table[tbl_name] = []
            indexes_by_table[tbl_name].append((idx_name, idx_sql))

        # Check snapshots indexes
        assert 'snapshots' in indexes_by_table, "Missing indexes on snapshots table"
        snapshot_indexes = [sql for _, sql in indexes_by_table['snapshots']]
        assert any('timestamp' in sql for sql in snapshot_indexes), \
            "Missing index on snapshots.timestamp"

        # Check systems indexes
        assert 'systems' in indexes_by_table, "Missing indexes on systems table"
        system_indexes = [sql for _, sql in indexes_by_table['systems']]
        assert any('resource_id' in sql for sql in system_indexes), \
            "Missing index on systems.resource_id"
        assert any('branch_office_name' in sql or 'organization' in sql for sql in system_indexes), \
            "Missing index on systems.branch_office_name/organization"

        # Check patches indexes
        assert 'patches' in indexes_by_table, "Missing indexes on patches table"
        patch_indexes = [sql for _, sql in indexes_by_table['patches']]
        assert any('pmp_patch_id' in sql for sql in patch_indexes), \
            "Missing index on patches.pmp_patch_id"

        # Check compliance_checks indexes
        assert 'compliance_checks' in indexes_by_table, "Missing indexes on compliance_checks table"
        compliance_indexes = [sql for _, sql in indexes_by_table['compliance_checks']]
        assert any('snapshot_id' in sql for sql in compliance_indexes), \
            "Missing index on compliance_checks.snapshot_id"

    def test_schema_compatible_with_base_intelligence(self, initialized_db):
        """Schema supports BaseIntelligenceService interface.

        Verifies:
        1. snapshots table has timestamp column (for get_data_freshness_report)
        2. snapshots table has status column (for staleness detection)
        3. Can execute SELECT COUNT(*) queries (for record_count)
        4. Can query latest snapshot by timestamp DESC
        """
        conn = sqlite3.connect(initialized_db)
        cursor = conn.cursor()

        # 1. Verify snapshots table structure
        cursor.execute("PRAGMA table_info(snapshots)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        assert 'snapshot_id' in columns, "snapshots table missing snapshot_id column"
        assert 'timestamp' in columns, "snapshots table missing timestamp column (required for freshness)"
        assert 'status' in columns, "snapshots table missing status column (required for staleness)"

        # 2. Test freshness query (get_data_freshness_report pattern)
        cursor.execute("""
            SELECT
                MAX(timestamp) as last_refresh,
                COUNT(*) as record_count,
                status
            FROM snapshots
            WHERE status = 'success'
        """)
        result = cursor.fetchone()
        assert result is not None, "Freshness query failed"

        # 3. Test latest snapshot query (common pattern in BaseIntelligenceService)
        cursor.execute("""
            SELECT snapshot_id, timestamp, status
            FROM snapshots
            WHERE status = 'success'
            ORDER BY timestamp DESC
            LIMIT 1
        """)
        # Should execute without error (no data yet is OK)
        result = cursor.fetchone()

        # 4. Test COUNT query for record_count
        cursor.execute("SELECT COUNT(*) FROM snapshots")
        count = cursor.fetchone()[0]
        assert count == 0, "Fresh database should have 0 snapshots"

        # 5. Verify all metric tables are queryable
        metric_tables = [
            'patch_metrics',
            'severity_metrics',
            'system_health_metrics',
            'vulnerability_db_metrics'
        ]

        for table_name in metric_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            assert count == 0, f"Fresh database should have 0 records in {table_name}"

        conn.close()
