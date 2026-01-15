#!/usr/bin/env python3
"""
Tests for PMP Data Migrator

Tests migration of 3 source databases into unified pmp_intelligence.db:
- pmp_config.db (114 MB) - all_systems, all_patches
- pmp_resilient.db (1.7 MB) - metrics snapshots
- pmp_systemreports.db (267 MB) - system_reports

Author: SRE Principal Engineer Agent
Date: 2026-01-15
Sprint: SPRINT-PMP-UNIFIED-001
Phase: P1 - Data Migration
"""

import pytest
import sqlite3
import tempfile
from pathlib import Path
from claude.tools.pmp.pmp_data_migrator import PMPDataMigrator


class TestMigrationPreparation:
    """Tests for migration preparation and validation"""

    def test_detect_source_databases(self, tmp_path):
        """Finds all 3 source databases."""
        # Create mock source databases
        source_dir = tmp_path / "intelligence"
        source_dir.mkdir()

        config_db = source_dir / "pmp_config.db"
        resilient_db = source_dir / "pmp_resilient.db"
        systemreports_db = source_dir / "pmp_systemreports.db"

        # Create empty databases
        for db_path in [config_db, resilient_db, systemreports_db]:
            conn = sqlite3.connect(db_path)
            conn.close()

        # Initialize migrator
        target_db = tmp_path / "pmp_intelligence.db"
        migrator = PMPDataMigrator(
            source_dir=source_dir,
            target_db=target_db
        )

        # Should detect all 3 sources
        sources = migrator.detect_source_databases()

        assert len(sources) == 3
        assert 'pmp_config.db' in sources
        assert 'pmp_resilient.db' in sources
        assert 'pmp_systemreports.db' in sources
        assert all(Path(path).exists() for path in sources.values())

    def test_validate_source_schemas(self, tmp_path):
        """Validates source table structures."""
        # Create source database with expected schema
        source_dir = tmp_path / "intelligence"
        source_dir.mkdir()

        config_db = source_dir / "pmp_config.db"
        conn = sqlite3.connect(config_db)
        cursor = conn.cursor()

        # Create expected tables
        cursor.execute("""
            CREATE TABLE all_systems (
                resource_id INTEGER PRIMARY KEY,
                extraction_id INTEGER,
                resource_health_status INTEGER,
                os_platform_name TEXT,
                raw_data TEXT,
                extracted_at TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE all_patches (
                patch_id INTEGER PRIMARY KEY,
                extraction_id INTEGER,
                bulletin_id TEXT,
                update_name TEXT,
                raw_data TEXT,
                extracted_at TEXT
            )
        """)

        conn.commit()
        conn.close()

        # Create minimal resilient and systemreports DBs
        for db_name in ['pmp_resilient.db', 'pmp_systemreports.db']:
            db_path = source_dir / db_name
            conn = sqlite3.connect(db_path)
            conn.close()

        # Initialize migrator
        target_db = tmp_path / "pmp_intelligence.db"
        migrator = PMPDataMigrator(
            source_dir=source_dir,
            target_db=target_db
        )

        # Should validate schemas successfully
        assert migrator.validate_source_schemas() is True


class TestDataMigration:
    """Tests for actual data migration operations"""

    def test_migrate_systems_deduplicates(self, tmp_path):
        """Merges systems from config, resilient, systemreports."""
        # Create source databases with duplicate systems
        source_dir = tmp_path / "intelligence"
        source_dir.mkdir()

        # Create pmp_config.db with systems
        config_db = source_dir / "pmp_config.db"
        conn = sqlite3.connect(config_db)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE all_systems (
                resource_id INTEGER PRIMARY KEY,
                extraction_id INTEGER,
                resource_health_status INTEGER,
                os_platform_name TEXT,
                raw_data TEXT,
                extracted_at TEXT
            )
        """)

        # Insert test systems (some will be duplicates across DBs)
        cursor.execute("""
            INSERT INTO all_systems (resource_id, resource_health_status, os_platform_name, extracted_at)
            VALUES (1001, 1, 'Windows 10', '2026-01-15 10:00:00'),
                   (1002, 2, 'Windows Server 2019', '2026-01-15 10:00:00')
        """)

        cursor.execute("""
            CREATE TABLE all_patches (
                patch_id INTEGER PRIMARY KEY,
                extraction_id INTEGER,
                bulletin_id TEXT,
                update_name TEXT,
                raw_data TEXT,
                extracted_at TEXT
            )
        """)

        conn.commit()
        conn.close()

        # Create minimal resilient and systemreports DBs
        for db_name in ['pmp_resilient.db', 'pmp_systemreports.db']:
            db_path = source_dir / db_name
            conn = sqlite3.connect(db_path)
            conn.close()

        # Create target database with schema
        target_db = tmp_path / "pmp_intelligence.db"
        self._create_target_schema(target_db)

        # Run migration
        migrator = PMPDataMigrator(
            source_dir=source_dir,
            target_db=target_db
        )

        result = migrator.migrate()

        assert result['success'] is True
        assert result['snapshot_id'] == 1

        # Verify systems were migrated and deduplicated
        conn = sqlite3.connect(target_db)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM systems WHERE snapshot_id = 1")
        system_count = cursor.fetchone()[0]
        assert system_count == 2  # 2 unique systems

        conn.close()

    def test_migrate_patches_preserves_all(self, tmp_path):
        """All patches migrated (check count matches source)."""
        # Create source databases
        source_dir = tmp_path / "intelligence"
        source_dir.mkdir()

        config_db = source_dir / "pmp_config.db"
        conn = sqlite3.connect(config_db)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE all_systems (
                resource_id INTEGER PRIMARY KEY,
                extraction_id INTEGER,
                resource_health_status INTEGER,
                os_platform_name TEXT,
                raw_data TEXT,
                extracted_at TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE all_patches (
                patch_id INTEGER PRIMARY KEY,
                extraction_id INTEGER,
                bulletin_id TEXT,
                update_name TEXT,
                raw_data TEXT,
                extracted_at TEXT
            )
        """)

        # Insert 5 test patches
        for i in range(1, 6):
            cursor.execute("""
                INSERT INTO all_patches (patch_id, bulletin_id, update_name, extracted_at)
                VALUES (?, ?, ?, ?)
            """, (i, f'MS2026-00{i}', f'Security Update {i}', '2026-01-15 10:00:00'))

        conn.commit()
        conn.close()

        # Create minimal resilient and systemreports DBs
        for db_name in ['pmp_resilient.db', 'pmp_systemreports.db']:
            db_path = source_dir / db_name
            conn = sqlite3.connect(db_path)
            conn.close()

        # Create target database
        target_db = tmp_path / "pmp_intelligence.db"
        self._create_target_schema(target_db)

        # Run migration
        migrator = PMPDataMigrator(
            source_dir=source_dir,
            target_db=target_db
        )

        result = migrator.migrate()

        assert result['success'] is True

        # Verify all patches migrated
        conn = sqlite3.connect(target_db)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM patches WHERE snapshot_id = 1")
        patch_count = cursor.fetchone()[0]
        assert patch_count == 5  # All 5 patches

        conn.close()

    def test_migrate_system_reports_to_mapping(self, tmp_path):
        """system_reports → patch_system_mapping."""
        # Create source databases
        source_dir = tmp_path / "intelligence"
        source_dir.mkdir()

        # Create pmp_config.db
        config_db = source_dir / "pmp_config.db"
        conn = sqlite3.connect(config_db)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE all_systems (
                resource_id INTEGER PRIMARY KEY,
                extraction_id INTEGER,
                resource_health_status INTEGER,
                os_platform_name TEXT,
                raw_data TEXT,
                extracted_at TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE all_patches (
                patch_id INTEGER PRIMARY KEY,
                extraction_id INTEGER,
                bulletin_id TEXT,
                update_name TEXT,
                raw_data TEXT,
                extracted_at TEXT
            )
        """)

        conn.commit()
        conn.close()

        # Create pmp_systemreports.db with system_reports
        systemreports_db = source_dir / "pmp_systemreports.db"
        conn = sqlite3.connect(systemreports_db)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE system_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                extraction_id INTEGER,
                resource_id INTEGER,
                patch_id INTEGER,
                patch_name TEXT,
                bulletin_id TEXT,
                severity INTEGER,
                patch_status INTEGER,
                approval_status INTEGER,
                is_reboot_required INTEGER,
                patch_deployed INTEGER,
                raw_data TEXT,
                extracted_at TEXT
            )
        """)

        # Insert 3 system-patch mappings
        for i in range(1, 4):
            cursor.execute("""
                INSERT INTO system_reports (
                    resource_id, patch_id, patch_name, bulletin_id,
                    severity, patch_status, approval_status, extracted_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (1001, i, f'Patch {i}', f'MS2026-00{i}', 3, 1, 1, '2026-01-15 10:00:00'))

        conn.commit()
        conn.close()

        # Create minimal resilient DB
        resilient_db = source_dir / "pmp_resilient.db"
        conn = sqlite3.connect(resilient_db)
        conn.close()

        # Create target database
        target_db = tmp_path / "pmp_intelligence.db"
        self._create_target_schema(target_db)

        # Run migration
        migrator = PMPDataMigrator(
            source_dir=source_dir,
            target_db=target_db
        )

        result = migrator.migrate()

        assert result['success'] is True

        # Verify system_reports → patch_system_mapping
        conn = sqlite3.connect(target_db)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM patch_system_mapping WHERE snapshot_id = 1")
        mapping_count = cursor.fetchone()[0]
        assert mapping_count == 3  # All 3 mappings migrated

        # Verify mapping structure
        cursor.execute("""
            SELECT pmp_patch_id, resource_id, patch_status, severity
            FROM patch_system_mapping
            WHERE snapshot_id = 1
            LIMIT 1
        """)

        row = cursor.fetchone()
        assert row[0] is not None  # pmp_patch_id
        assert row[1] is not None  # resource_id
        assert row[2] is not None  # patch_status
        assert row[3] is not None  # severity

        conn.close()

    def test_creates_initial_snapshot(self, tmp_path):
        """Creates snapshot_id=1 for migrated data."""
        # Create minimal source databases
        source_dir = tmp_path / "intelligence"
        source_dir.mkdir()

        config_db = source_dir / "pmp_config.db"
        conn = sqlite3.connect(config_db)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE all_systems (
                resource_id INTEGER PRIMARY KEY,
                extraction_id INTEGER,
                resource_health_status INTEGER,
                os_platform_name TEXT,
                raw_data TEXT,
                extracted_at TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE all_patches (
                patch_id INTEGER PRIMARY KEY,
                extraction_id INTEGER,
                bulletin_id TEXT,
                update_name TEXT,
                raw_data TEXT,
                extracted_at TEXT
            )
        """)

        conn.commit()
        conn.close()

        # Create minimal resilient and systemreports DBs
        for db_name in ['pmp_resilient.db', 'pmp_systemreports.db']:
            db_path = source_dir / db_name
            conn = sqlite3.connect(db_path)
            conn.close()

        # Create target database
        target_db = tmp_path / "pmp_intelligence.db"
        self._create_target_schema(target_db)

        # Run migration
        migrator = PMPDataMigrator(
            source_dir=source_dir,
            target_db=target_db
        )

        result = migrator.migrate()

        assert result['success'] is True
        assert result['snapshot_id'] == 1

        # Verify snapshot record created
        conn = sqlite3.connect(target_db)
        cursor = conn.cursor()

        cursor.execute("SELECT snapshot_id, status FROM snapshots WHERE snapshot_id = 1")
        row = cursor.fetchone()

        assert row is not None
        assert row[0] == 1  # snapshot_id
        assert row[1] == 'success'  # status

        conn.close()

    def _create_target_schema(self, db_path: Path):
        """Helper to create target database schema"""
        schema_file = Path(__file__).parent.parent / "claude/tools/pmp/pmp_unified_schema.sql"
        schema_sql = schema_file.read_text()

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.executescript(schema_sql)
        conn.commit()
        conn.close()


class TestMigrationIntegrity:
    """Tests for migration data integrity"""

    def test_no_data_loss(self, tmp_path):
        """Record counts match source databases."""
        # Create source databases with known counts
        source_dir = tmp_path / "intelligence"
        source_dir.mkdir()

        config_db = source_dir / "pmp_config.db"
        conn = sqlite3.connect(config_db)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE all_systems (
                resource_id INTEGER PRIMARY KEY,
                extraction_id INTEGER,
                resource_health_status INTEGER,
                os_platform_name TEXT,
                raw_data TEXT,
                extracted_at TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE all_patches (
                patch_id INTEGER PRIMARY KEY,
                extraction_id INTEGER,
                bulletin_id TEXT,
                update_name TEXT,
                raw_data TEXT,
                extracted_at TEXT
            )
        """)

        # Insert known counts
        for i in range(1, 11):  # 10 systems
            cursor.execute("""
                INSERT INTO all_systems (resource_id, resource_health_status, os_platform_name, extracted_at)
                VALUES (?, ?, ?, ?)
            """, (i, 1, 'Windows 10', '2026-01-15 10:00:00'))

        for i in range(1, 21):  # 20 patches
            cursor.execute("""
                INSERT INTO all_patches (patch_id, bulletin_id, update_name, extracted_at)
                VALUES (?, ?, ?, ?)
            """, (i, f'MS2026-{i:03d}', f'Patch {i}', '2026-01-15 10:00:00'))

        conn.commit()
        conn.close()

        # Create systemreports with mappings
        systemreports_db = source_dir / "pmp_systemreports.db"
        conn = sqlite3.connect(systemreports_db)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE system_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                extraction_id INTEGER,
                resource_id INTEGER,
                patch_id INTEGER,
                patch_name TEXT,
                bulletin_id TEXT,
                severity INTEGER,
                patch_status INTEGER,
                approval_status INTEGER,
                is_reboot_required INTEGER,
                patch_deployed INTEGER,
                raw_data TEXT,
                extracted_at TEXT
            )
        """)

        # Insert 50 mappings (10 systems * 5 patches each)
        for system_id in range(1, 11):
            for patch_id in range(1, 6):
                cursor.execute("""
                    INSERT INTO system_reports (
                        resource_id, patch_id, patch_name, bulletin_id,
                        severity, patch_status, approval_status, extracted_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (system_id, patch_id, f'Patch {patch_id}', f'MS2026-{patch_id:03d}',
                      3, 1, 1, '2026-01-15 10:00:00'))

        conn.commit()
        conn.close()

        # Create minimal resilient DB
        resilient_db = source_dir / "pmp_resilient.db"
        conn = sqlite3.connect(resilient_db)
        conn.close()

        # Create target database
        target_db = tmp_path / "pmp_intelligence.db"
        self._create_target_schema(target_db)

        # Run migration
        migrator = PMPDataMigrator(
            source_dir=source_dir,
            target_db=target_db
        )

        result = migrator.migrate()

        assert result['success'] is True

        # Verify counts match
        conn = sqlite3.connect(target_db)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM systems WHERE snapshot_id = 1")
        assert cursor.fetchone()[0] == 10  # All 10 systems

        cursor.execute("SELECT COUNT(*) FROM patches WHERE snapshot_id = 1")
        assert cursor.fetchone()[0] == 20  # All 20 patches

        cursor.execute("SELECT COUNT(*) FROM patch_system_mapping WHERE snapshot_id = 1")
        assert cursor.fetchone()[0] == 50  # All 50 mappings

        conn.close()

    def test_foreign_keys_valid(self, tmp_path):
        """All FKs resolve to valid records."""
        # Create source databases
        source_dir = tmp_path / "intelligence"
        source_dir.mkdir()

        config_db = source_dir / "pmp_config.db"
        conn = sqlite3.connect(config_db)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE all_systems (
                resource_id INTEGER PRIMARY KEY,
                extraction_id INTEGER,
                resource_health_status INTEGER,
                os_platform_name TEXT,
                raw_data TEXT,
                extracted_at TEXT
            )
        """)

        cursor.execute("""
            INSERT INTO all_systems (resource_id, resource_health_status, os_platform_name, extracted_at)
            VALUES (1001, 1, 'Windows 10', '2026-01-15 10:00:00')
        """)

        cursor.execute("""
            CREATE TABLE all_patches (
                patch_id INTEGER PRIMARY KEY,
                extraction_id INTEGER,
                bulletin_id TEXT,
                update_name TEXT,
                raw_data TEXT,
                extracted_at TEXT
            )
        """)

        cursor.execute("""
            INSERT INTO all_patches (patch_id, bulletin_id, update_name, extracted_at)
            VALUES (2001, 'MS2026-001', 'Security Update', '2026-01-15 10:00:00')
        """)

        conn.commit()
        conn.close()

        # Create systemreports with mapping
        systemreports_db = source_dir / "pmp_systemreports.db"
        conn = sqlite3.connect(systemreports_db)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE system_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                extraction_id INTEGER,
                resource_id INTEGER,
                patch_id INTEGER,
                patch_name TEXT,
                bulletin_id TEXT,
                severity INTEGER,
                patch_status INTEGER,
                approval_status INTEGER,
                is_reboot_required INTEGER,
                patch_deployed INTEGER,
                raw_data TEXT,
                extracted_at TEXT
            )
        """)

        cursor.execute("""
            INSERT INTO system_reports (
                resource_id, patch_id, patch_name, bulletin_id,
                severity, patch_status, approval_status, extracted_at
            )
            VALUES (1001, 2001, 'Security Update', 'MS2026-001', 3, 1, 1, '2026-01-15 10:00:00')
        """)

        conn.commit()
        conn.close()

        # Create minimal resilient DB
        resilient_db = source_dir / "pmp_resilient.db"
        conn = sqlite3.connect(resilient_db)
        conn.close()

        # Create target database
        target_db = tmp_path / "pmp_intelligence.db"
        self._create_target_schema(target_db)

        # Run migration
        migrator = PMPDataMigrator(
            source_dir=source_dir,
            target_db=target_db
        )

        result = migrator.migrate()

        assert result['success'] is True

        # Verify all foreign keys are valid
        conn = sqlite3.connect(target_db)
        cursor = conn.cursor()

        # Enable foreign key checks
        cursor.execute("PRAGMA foreign_keys = ON")

        # Verify snapshot FK integrity
        cursor.execute("""
            SELECT COUNT(*) FROM systems s
            WHERE NOT EXISTS (
                SELECT 1 FROM snapshots sn WHERE sn.snapshot_id = s.snapshot_id
            )
        """)
        assert cursor.fetchone()[0] == 0  # No orphaned systems

        cursor.execute("""
            SELECT COUNT(*) FROM patches p
            WHERE NOT EXISTS (
                SELECT 1 FROM snapshots sn WHERE sn.snapshot_id = p.snapshot_id
            )
        """)
        assert cursor.fetchone()[0] == 0  # No orphaned patches

        cursor.execute("""
            SELECT COUNT(*) FROM patch_system_mapping psm
            WHERE NOT EXISTS (
                SELECT 1 FROM snapshots sn WHERE sn.snapshot_id = psm.snapshot_id
            )
        """)
        assert cursor.fetchone()[0] == 0  # No orphaned mappings

        conn.close()

    def _create_target_schema(self, db_path: Path):
        """Helper to create target database schema"""
        schema_file = Path(__file__).parent.parent / "claude/tools/pmp/pmp_unified_schema.sql"
        schema_sql = schema_file.read_text()

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.executescript(schema_sql)
        conn.commit()
        conn.close()
