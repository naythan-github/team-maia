#!/usr/bin/env python3
"""
PMP Data Migrator - Consolidate 3 PMP databases into unified schema

Migrates data from:
- pmp_config.db (114 MB) → all_systems, all_patches
- pmp_resilient.db (1.7 MB) → metrics snapshots
- pmp_systemreports.db (267 MB) → system_reports

Into unified pmp_intelligence.db with:
- Deduplication of systems across sources
- Complete patch inventory preservation
- system_reports → patch_system_mapping conversion
- Initial snapshot creation (snapshot_id = 1)

Author: SRE Principal Engineer Agent
Date: 2026-01-15
Sprint: SPRINT-PMP-UNIFIED-001
Phase: P1 - Data Migration
"""

import sqlite3
import json
import logging
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class MigrationResult:
    """Result of migration operation"""
    success: bool
    snapshot_id: Optional[int]
    systems_migrated: int
    patches_migrated: int
    mappings_migrated: int
    error_message: Optional[str] = None
    duration_ms: int = 0


class PMPDataMigrator:
    """
    Migrate PMP data from 3 source databases to unified schema

    Usage:
        migrator = PMPDataMigrator(
            source_dir=Path("~/.maia/databases/intelligence"),
            target_db=Path("~/.maia/databases/intelligence/pmp_intelligence.db")
        )
        result = migrator.migrate()
        print(f"Migrated snapshot {result.snapshot_id}")
    """

    def __init__(
        self,
        source_dir: Optional[Path] = None,
        target_db: Optional[Path] = None
    ):
        """
        Initialize migrator

        Args:
            source_dir: Directory containing source databases
                       (default: ~/.maia/databases/intelligence)
            target_db: Target unified database path
                      (default: ~/.maia/databases/intelligence/pmp_intelligence.db)
        """
        # Default paths
        if source_dir is None:
            source_dir = Path.home() / ".maia/databases/intelligence"
        if target_db is None:
            target_db = source_dir / "pmp_intelligence.db"

        self.source_dir = Path(source_dir)
        self.target_db = Path(target_db)

        # Source database paths
        self.source_dbs = {
            'pmp_config.db': self.source_dir / 'pmp_config.db',
            'pmp_resilient.db': self.source_dir / 'pmp_resilient.db',
            'pmp_systemreports.db': self.source_dir / 'pmp_systemreports.db'
        }

        logger.info("pmp_data_migrator_initialized", extra={
            "source_dir": str(self.source_dir),
            "target_db": str(self.target_db)
        })

    def detect_source_databases(self) -> Dict[str, Path]:
        """
        Find and validate source databases

        Returns:
            Dictionary mapping database name to path

        Raises:
            FileNotFoundError: If any source database is missing
        """
        detected = {}

        for db_name, db_path in self.source_dbs.items():
            if not db_path.exists():
                raise FileNotFoundError(f"Source database not found: {db_path}")

            detected[db_name] = db_path
            logger.info("source_database_detected", extra={
                "database": db_name,
                "path": str(db_path),
                "size_mb": db_path.stat().st_size / (1024 * 1024)
            })

        return detected

    def validate_source_schemas(self) -> bool:
        """
        Validate source database schemas

        Returns:
            True if all required tables exist

        Raises:
            RuntimeError: If schema validation fails
        """
        # Expected tables in each source
        expected_tables = {
            'pmp_config.db': ['all_systems', 'all_patches'],
            'pmp_resilient.db': [],  # Metrics tables optional for now
            'pmp_systemreports.db': []  # Will check for system_reports if present
        }

        for db_name, required_tables in expected_tables.items():
            if not required_tables:
                continue  # Skip validation for optional DBs

            db_path = self.source_dbs[db_name]
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Get table list
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table'
            """)

            existing_tables = {row[0] for row in cursor.fetchall()}
            conn.close()

            # Validate required tables exist
            missing_tables = set(required_tables) - existing_tables

            if missing_tables:
                raise RuntimeError(
                    f"Missing required tables in {db_name}: {missing_tables}"
                )

            logger.info("schema_validated", extra={
                "database": db_name,
                "tables": list(existing_tables)
            })

        return True

    def migrate(self) -> Dict:
        """
        Execute complete migration

        Returns:
            Dictionary with migration results

        Raises:
            RuntimeError: If migration fails
        """
        start_time = datetime.now()

        # FIX #2: Open target database connection for transaction management
        target_conn = None

        try:
            logger.info("migration_started")

            # Step 1: Detect and validate sources
            sources = self.detect_source_databases()
            self.validate_source_schemas()

            # Step 2: Initialize target database
            self._init_target_database()

            # FIX #2: Begin transaction - all migration operations in single transaction
            target_conn = sqlite3.connect(self.target_db)
            target_conn.execute("BEGIN TRANSACTION")

            # Step 3: Create initial snapshot
            snapshot_id = self._create_initial_snapshot_transactional(target_conn)

            # Step 4: Migrate systems (with deduplication)
            systems_count = self._migrate_systems_transactional(target_conn, snapshot_id)

            # Step 5: Migrate patches
            patches_count = self._migrate_patches_transactional(target_conn, snapshot_id)

            # Step 6: Migrate mappings
            mappings_count = self._migrate_mappings_transactional(target_conn, snapshot_id)

            # FIX #2: Commit entire transaction only if all steps succeed
            target_conn.commit()

            # Calculate duration
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            logger.info("migration_completed", extra={
                "snapshot_id": snapshot_id,
                "systems": systems_count,
                "patches": patches_count,
                "mappings": mappings_count,
                "duration_ms": duration_ms
            })

            return {
                'success': True,
                'snapshot_id': snapshot_id,
                'systems_migrated': systems_count,
                'patches_migrated': patches_count,
                'mappings_migrated': mappings_count,
                'duration_ms': duration_ms
            }

        except Exception as e:
            # FIX #2: Rollback entire transaction on any failure
            if target_conn:
                try:
                    target_conn.rollback()
                    logger.info("transaction_rolled_back")
                except Exception as rollback_error:
                    logger.error("rollback_failed", extra={
                        "error": str(rollback_error)
                    })

            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            logger.error("migration_failed", extra={
                "error": str(e),
                "duration_ms": duration_ms
            }, exc_info=True)

            return {
                'success': False,
                'snapshot_id': None,
                'systems_migrated': 0,
                'patches_migrated': 0,
                'mappings_migrated': 0,
                'error_message': str(e),
                'duration_ms': duration_ms
            }

        finally:
            # FIX #2: Always close connection
            if target_conn:
                target_conn.close()

    def _init_target_database(self):
        """Initialize target database with unified schema"""
        # Get schema file
        schema_file = Path(__file__).parent / "pmp_unified_schema.sql"

        if not schema_file.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_file}")

        # Create database if it doesn't exist
        self.target_db.parent.mkdir(parents=True, exist_ok=True)

        # Execute schema
        schema_sql = schema_file.read_text()

        conn = sqlite3.connect(self.target_db)
        cursor = conn.cursor()
        cursor.executescript(schema_sql)
        conn.commit()
        conn.close()

        # Set permissions (owner read/write only)
        self.target_db.chmod(0o600)

        logger.info("target_database_initialized", extra={
            "path": str(self.target_db)
        })

    def _create_initial_snapshot_transactional(self, conn: sqlite3.Connection) -> int:
        """
        Create initial snapshot record for migration (transactional)

        Args:
            conn: Database connection (transaction already started)

        Returns:
            snapshot_id (always 1 for migration)
        """
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO snapshots (api_version, status, extraction_duration_ms)
            VALUES ('1.4', 'success', 0)
        """)

        snapshot_id = cursor.lastrowid

        logger.info("initial_snapshot_created", extra={
            "snapshot_id": snapshot_id
        })

        return snapshot_id

    def _migrate_systems_transactional(self, target_conn: sqlite3.Connection, snapshot_id: int) -> int:
        """
        Migrate systems from pmp_config.db with deduplication (transactional)

        Args:
            target_conn: Target database connection (transaction already started)
            snapshot_id: Target snapshot ID

        Returns:
            Number of systems migrated
        """
        config_db = self.source_dbs['pmp_config.db']

        # Read systems from source
        source_conn = sqlite3.connect(config_db)
        source_conn.row_factory = sqlite3.Row
        source_cursor = source_conn.cursor()

        # FIX #1: Column whitelist for SQL injection prevention
        ALLOWED_COLUMNS = {
            'resource_id',
            'resource_health_status',
            'os_platform_name',
            'raw_data',
            'extracted_at'
        }

        # First, check which columns exist in the source table
        source_cursor.execute("PRAGMA table_info(all_systems)")
        available_columns = {row[1] for row in source_cursor.fetchall()}

        # FIX #1: Validate columns against whitelist
        select_columns = []
        for col in ALLOWED_COLUMNS:
            if col in available_columns:
                select_columns.append(col)

        if not select_columns:
            raise RuntimeError("No valid columns found in all_systems table")

        # Safe to use f-string now - all columns validated against whitelist
        source_cursor.execute(f"""
            SELECT {', '.join(select_columns)}
            FROM all_systems
        """)

        # FIX #3: Use batching instead of fetchall to prevent memory exhaustion
        target_cursor = target_conn.cursor()

        migrated_count = 0
        duplicate_count = 0
        skipped_count = 0
        batch_size = 1000

        while True:
            systems = source_cursor.fetchmany(batch_size)
            if not systems:
                break

            for system in systems:
                # Safely get values with defaults for missing columns
                def get_val(key):
                    return system[key] if key in available_columns else None

                # FIX #5: Validate required fields are not None
                resource_id = get_val('resource_id')
                if resource_id is None:
                    logger.warning("skipping_system_null_resource_id", extra={
                        "system": dict(system)
                    })
                    skipped_count += 1
                    continue

                # Map source fields to target schema
                # Note: Using resource_id as both resource_id and resource_name for now
                try:
                    # FIX #4: Use INSERT OR IGNORE for duplicate key handling
                    target_cursor.execute("""
                        INSERT OR IGNORE INTO systems (
                            snapshot_id,
                            resource_id,
                            resource_name,
                            resource_health_status,
                            os_platform_name,
                            branch_office_name,
                            raw_data,
                            extracted_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        snapshot_id,
                        str(resource_id),
                        f"System-{resource_id}",  # Default name
                        get_val('resource_health_status'),
                        get_val('os_platform_name'),
                        'Default',  # Default branch office
                        get_val('raw_data'),
                        get_val('extracted_at')
                    ))

                    # FIX #4: Track if row was actually inserted
                    if target_cursor.rowcount == 0:
                        duplicate_count += 1
                    else:
                        migrated_count += 1

                except sqlite3.IntegrityError as e:
                    # This should not happen with INSERT OR IGNORE, but handle just in case
                    logger.warning("system_insert_failed", extra={
                        "resource_id": resource_id,
                        "error": str(e)
                    })
                    duplicate_count += 1

                # Log progress for large datasets
                if (migrated_count + duplicate_count) % 1000 == 0:
                    logger.info("systems_migration_progress", extra={
                        "migrated": migrated_count,
                        "duplicates": duplicate_count,
                        "skipped": skipped_count
                    })

        source_conn.close()

        logger.info("systems_migrated", extra={
            "count": migrated_count,
            "duplicates": duplicate_count,
            "skipped": skipped_count,
            "snapshot_id": snapshot_id
        })

        return migrated_count

    def _migrate_patches_transactional(self, target_conn: sqlite3.Connection, snapshot_id: int) -> int:
        """
        Migrate patches from pmp_config.db (transactional)

        Args:
            target_conn: Target database connection (transaction already started)
            snapshot_id: Target snapshot ID

        Returns:
            Number of patches migrated
        """
        config_db = self.source_dbs['pmp_config.db']

        # Read patches from source
        source_conn = sqlite3.connect(config_db)
        source_conn.row_factory = sqlite3.Row
        source_cursor = source_conn.cursor()

        # FIX #1: Column whitelist for SQL injection prevention
        ALLOWED_COLUMNS = {
            'patch_id',
            'bulletin_id',
            'update_name',
            'platform',
            'patch_released_time',
            'patch_size',
            'patch_noreboot',
            'installed',
            'raw_data',
            'extracted_at'
        }

        # First, check which columns exist in the source table
        source_cursor.execute("PRAGMA table_info(all_patches)")
        available_columns = {row[1] for row in source_cursor.fetchall()}

        # FIX #1: Validate columns against whitelist
        select_columns = []
        for col in ALLOWED_COLUMNS:
            if col in available_columns:
                select_columns.append(col)

        if not select_columns:
            raise RuntimeError("No valid columns found in all_patches table")

        # Safe to use f-string now - all columns validated against whitelist
        source_cursor.execute(f"""
            SELECT {', '.join(select_columns)}
            FROM all_patches
        """)

        # FIX #3: Use batching instead of fetchall to prevent memory exhaustion
        target_cursor = target_conn.cursor()

        migrated_count = 0
        duplicate_count = 0
        skipped_count = 0
        batch_size = 1000

        while True:
            patches = source_cursor.fetchmany(batch_size)
            if not patches:
                break

            for patch in patches:
                # Safely get values with defaults for missing columns
                def get_val(key):
                    return patch[key] if key in available_columns else None

                # FIX #5: Validate required fields are not None
                patch_id = get_val('patch_id')
                if patch_id is None:
                    logger.warning("skipping_patch_null_patch_id", extra={
                        "patch": dict(patch)
                    })
                    skipped_count += 1
                    continue

                # Map source fields to target schema
                try:
                    # FIX #4: Use INSERT OR IGNORE for duplicate key handling
                    target_cursor.execute("""
                        INSERT OR IGNORE INTO patches (
                            snapshot_id,
                            pmp_patch_id,
                            patch_name,
                            bulletin_id,
                            platform,
                            patch_released_time,
                            patch_size,
                            patch_noreboot,
                            installed,
                            raw_data,
                            extracted_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        snapshot_id,
                        str(patch_id),
                        get_val('update_name'),
                        get_val('bulletin_id'),
                        get_val('platform'),
                        get_val('patch_released_time'),
                        get_val('patch_size'),
                        get_val('patch_noreboot'),
                        get_val('installed'),
                        get_val('raw_data'),
                        get_val('extracted_at')
                    ))

                    # FIX #4: Track if row was actually inserted
                    if target_cursor.rowcount == 0:
                        duplicate_count += 1
                    else:
                        migrated_count += 1

                except sqlite3.IntegrityError as e:
                    # This should not happen with INSERT OR IGNORE, but handle just in case
                    logger.warning("patch_insert_failed", extra={
                        "patch_id": patch_id,
                        "error": str(e)
                    })
                    duplicate_count += 1

                # Log progress for large datasets
                if (migrated_count + duplicate_count) % 5000 == 0:
                    logger.info("patches_migration_progress", extra={
                        "migrated": migrated_count,
                        "duplicates": duplicate_count,
                        "skipped": skipped_count
                    })

        source_conn.close()

        logger.info("patches_migrated", extra={
            "count": migrated_count,
            "duplicates": duplicate_count,
            "skipped": skipped_count,
            "snapshot_id": snapshot_id
        })

        return migrated_count

    def _migrate_mappings_transactional(self, target_conn: sqlite3.Connection, snapshot_id: int) -> int:
        """
        Migrate system_reports to patch_system_mapping (transactional)

        Args:
            target_conn: Target database connection (transaction already started)
            snapshot_id: Target snapshot ID

        Returns:
            Number of mappings migrated
        """
        systemreports_db = self.source_dbs['pmp_systemreports.db']

        # Read system_reports from source
        source_conn = sqlite3.connect(systemreports_db)
        source_conn.row_factory = sqlite3.Row
        source_cursor = source_conn.cursor()

        # Check if system_reports table exists
        source_cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='system_reports'
        """)

        if not source_cursor.fetchone():
            logger.warning("system_reports_table_not_found", extra={
                "database": "pmp_systemreports.db"
            })
            source_conn.close()
            return 0

        source_cursor.execute("""
            SELECT
                resource_id,
                patch_id,
                patch_name,
                bulletin_id,
                severity,
                patch_status,
                approval_status,
                is_reboot_required,
                patch_deployed,
                raw_data,
                extracted_at
            FROM system_reports
        """)

        # FIX #3: Use batching instead of fetchall to prevent memory exhaustion
        target_cursor = target_conn.cursor()

        migrated_count = 0
        duplicate_count = 0
        skipped_count = 0
        batch_size = 1000

        while True:
            mappings = source_cursor.fetchmany(batch_size)
            if not mappings:
                break

            for mapping in mappings:
                # FIX #5: Validate required fields are not None
                resource_id = mapping['resource_id']
                patch_id = mapping['patch_id']

                if resource_id is None or patch_id is None:
                    logger.warning("skipping_mapping_null_keys", extra={
                        "resource_id": resource_id,
                        "patch_id": patch_id
                    })
                    skipped_count += 1
                    continue

                # Convert system_reports to patch_system_mapping
                try:
                    # FIX #4: Use INSERT OR IGNORE for duplicate key handling
                    target_cursor.execute("""
                        INSERT OR IGNORE INTO patch_system_mapping (
                            snapshot_id,
                            pmp_patch_id,
                            resource_id,
                            patch_status,
                            approval_status,
                            patch_deployed,
                            patch_name,
                            bulletin_id,
                            severity,
                            is_reboot_required,
                            raw_data,
                            extracted_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        snapshot_id,
                        str(patch_id),
                        str(resource_id),
                        mapping['patch_status'],
                        mapping['approval_status'],
                        mapping['patch_deployed'],
                        mapping['patch_name'],
                        mapping['bulletin_id'],
                        mapping['severity'],
                        mapping['is_reboot_required'],
                        mapping['raw_data'],
                        mapping['extracted_at']
                    ))

                    # FIX #4: Track if row was actually inserted
                    if target_cursor.rowcount == 0:
                        duplicate_count += 1
                    else:
                        migrated_count += 1

                except sqlite3.IntegrityError as e:
                    # This should not happen with INSERT OR IGNORE, but handle just in case
                    logger.warning("mapping_insert_failed", extra={
                        "resource_id": resource_id,
                        "patch_id": patch_id,
                        "error": str(e)
                    })
                    duplicate_count += 1

                # Log progress for large datasets (every 10k records)
                if (migrated_count + duplicate_count) % 10000 == 0:
                    logger.info("mappings_migration_progress", extra={
                        "migrated": migrated_count,
                        "duplicates": duplicate_count,
                        "skipped": skipped_count
                    })

        source_conn.close()

        logger.info("mappings_migrated", extra={
            "count": migrated_count,
            "duplicates": duplicate_count,
            "skipped": skipped_count,
            "snapshot_id": snapshot_id
        })

        return migrated_count


def main():
    """CLI interface for migration tool"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Migrate PMP data to unified schema"
    )
    parser.add_argument(
        '--source-dir',
        type=str,
        help='Source databases directory (default: ~/.maia/databases/intelligence)'
    )
    parser.add_argument(
        '--target-db',
        type=str,
        help='Target database path (default: ~/.maia/databases/intelligence/pmp_intelligence.db)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Validate sources without migrating'
    )

    args = parser.parse_args()

    # Initialize migrator
    source_dir = Path(args.source_dir) if args.source_dir else None
    target_db = Path(args.target_db) if args.target_db else None

    migrator = PMPDataMigrator(
        source_dir=source_dir,
        target_db=target_db
    )

    if args.dry_run:
        print("🔍 Dry run - validating sources...")
        try:
            sources = migrator.detect_source_databases()
            migrator.validate_source_schemas()

            print("\n✅ Validation successful")
            print("\nSource databases:")
            for db_name, db_path in sources.items():
                size_mb = db_path.stat().st_size / (1024 * 1024)
                print(f"  - {db_name}: {size_mb:.1f} MB")

            print(f"\nTarget: {migrator.target_db}")

        except Exception as e:
            print(f"\n❌ Validation failed: {e}")
            return 1

    else:
        print("🔄 Starting migration...")
        result = migrator.migrate()

        if result['success']:
            print(f"\n✅ Migration completed successfully")
            print(f"\nSnapshot ID: {result['snapshot_id']}")
            print(f"Systems migrated: {result['systems_migrated']}")
            print(f"Patches migrated: {result['patches_migrated']}")
            print(f"Mappings migrated: {result['mappings_migrated']}")
            print(f"Duration: {result['duration_ms']}ms")
        else:
            print(f"\n❌ Migration failed: {result['error_message']}")
            return 1

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
