#!/usr/bin/env python3
"""
Migration Script: v4 → v5 (Phase 264 - Multi-Schema ETL Pipeline)

Adds multi-schema support columns to sign_in_logs table:
- Schema tracking: schema_variant, sign_in_type, is_service_principal
- Service principal fields: service_principal_id, service_principal_name
- Graph API fields: user_id, request_id, auth_requirement, mfa_result
- Performance fields: latency_ms
- Device compliance: device_compliant, device_managed
- Resource tracking: resource_id
- Credential tracking: credential_key_id

Idempotent: Safe to run multiple times (checks for column existence).

Usage:
    from claude.tools.m365_ir.migrations.migrate_v5 import migrate_to_v5
    from claude.tools.m365_ir.log_database import IRLogDatabase

    db = IRLogDatabase(case_id="PIR-EXISTING-CASE")
    migrate_to_v5(db)

Author: SRE Principal Engineer Agent
Created: 2026-01-11
Phase: 264 Sprint 1.3
"""

from pathlib import Path
import sys

MAIA_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))


def _column_exists(cursor, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = {row[1] for row in cursor.fetchall()}
    return column_name in columns


def migrate_to_v5(db) -> None:
    """
    Migrate existing v4 database to v5 (add multi-schema ETL columns).

    Args:
        db: IRLogDatabase instance

    Raises:
        ValueError if database doesn't exist
    """
    if not db.exists:
        raise ValueError(f"Database does not exist: {db.db_path}")

    conn = db.connect()
    cursor = conn.cursor()

    print(f"Migrating {db.case_id} to schema v5 (Multi-Schema ETL)...")

    # ================================================================
    # Add new columns to sign_in_logs table
    # ================================================================

    # Schema tracking columns
    if not _column_exists(cursor, 'sign_in_logs', 'schema_variant'):
        cursor.execute("""
            ALTER TABLE sign_in_logs ADD COLUMN schema_variant TEXT
        """)
        print("  ✓ Added column: schema_variant")

    if not _column_exists(cursor, 'sign_in_logs', 'sign_in_type'):
        cursor.execute("""
            ALTER TABLE sign_in_logs ADD COLUMN sign_in_type TEXT
        """)
        print("  ✓ Added column: sign_in_type")

    if not _column_exists(cursor, 'sign_in_logs', 'is_service_principal'):
        cursor.execute("""
            ALTER TABLE sign_in_logs ADD COLUMN is_service_principal INTEGER DEFAULT 0
        """)
        print("  ✓ Added column: is_service_principal")

    # Service principal fields
    if not _column_exists(cursor, 'sign_in_logs', 'service_principal_id'):
        cursor.execute("""
            ALTER TABLE sign_in_logs ADD COLUMN service_principal_id TEXT
        """)
        print("  ✓ Added column: service_principal_id")

    if not _column_exists(cursor, 'sign_in_logs', 'service_principal_name'):
        cursor.execute("""
            ALTER TABLE sign_in_logs ADD COLUMN service_principal_name TEXT
        """)
        print("  ✓ Added column: service_principal_name")

    # Graph API user/request tracking fields
    if not _column_exists(cursor, 'sign_in_logs', 'user_id'):
        cursor.execute("""
            ALTER TABLE sign_in_logs ADD COLUMN user_id TEXT
        """)
        print("  ✓ Added column: user_id")

    if not _column_exists(cursor, 'sign_in_logs', 'request_id'):
        cursor.execute("""
            ALTER TABLE sign_in_logs ADD COLUMN request_id TEXT
        """)
        print("  ✓ Added column: request_id")

    # Authentication fields
    if not _column_exists(cursor, 'sign_in_logs', 'auth_requirement'):
        cursor.execute("""
            ALTER TABLE sign_in_logs ADD COLUMN auth_requirement TEXT
        """)
        print("  ✓ Added column: auth_requirement")

    if not _column_exists(cursor, 'sign_in_logs', 'mfa_result'):
        cursor.execute("""
            ALTER TABLE sign_in_logs ADD COLUMN mfa_result TEXT
        """)
        print("  ✓ Added column: mfa_result")

    # Performance fields
    if not _column_exists(cursor, 'sign_in_logs', 'latency_ms'):
        cursor.execute("""
            ALTER TABLE sign_in_logs ADD COLUMN latency_ms INTEGER
        """)
        print("  ✓ Added column: latency_ms")

    # Device compliance fields
    if not _column_exists(cursor, 'sign_in_logs', 'device_compliant'):
        cursor.execute("""
            ALTER TABLE sign_in_logs ADD COLUMN device_compliant INTEGER
        """)
        print("  ✓ Added column: device_compliant")

    if not _column_exists(cursor, 'sign_in_logs', 'device_managed'):
        cursor.execute("""
            ALTER TABLE sign_in_logs ADD COLUMN device_managed INTEGER
        """)
        print("  ✓ Added column: device_managed")

    # Credential tracking
    if not _column_exists(cursor, 'sign_in_logs', 'credential_key_id'):
        cursor.execute("""
            ALTER TABLE sign_in_logs ADD COLUMN credential_key_id TEXT
        """)
        print("  ✓ Added column: credential_key_id")

    # Resource tracking
    if not _column_exists(cursor, 'sign_in_logs', 'resource_id'):
        cursor.execute("""
            ALTER TABLE sign_in_logs ADD COLUMN resource_id TEXT
        """)
        print("  ✓ Added column: resource_id")

    # ================================================================
    # Create indexes for performance
    # ================================================================

    # Sign-in type index (for filtering interactive vs noninteractive)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_signin_type
        ON sign_in_logs(sign_in_type)
    """)
    print("  ✓ Created index: idx_signin_type")

    # Schema variant index (for multi-schema queries)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_signin_schema
        ON sign_in_logs(schema_variant)
    """)
    print("  ✓ Created index: idx_signin_schema")

    # Service principal index (for filtering service principal auth)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_signin_service_principal
        ON sign_in_logs(is_service_principal)
    """)
    print("  ✓ Created index: idx_signin_service_principal")

    conn.commit()
    conn.close()

    print(f"✅ Migration complete: {db.case_id} now on schema v5")
    print("   Added: 14 new columns for multi-schema ETL support")
    print("   Added: 3 performance indexes")


if __name__ == "__main__":
    """Migrate all existing v4 databases in ~/work_projects/ir_cases/"""
    from claude.tools.m365_ir.log_database import IRLogDatabase
    import os

    base_path = os.path.expanduser("~/work_projects/ir_cases")

    if not os.path.exists(base_path):
        print(f"No IR cases directory found: {base_path}")
        sys.exit(1)

    # Find all case directories with databases
    migrated = 0
    for case_id in os.listdir(base_path):
        case_dir = os.path.join(base_path, case_id)
        if os.path.isdir(case_dir):
            db_path = os.path.join(case_dir, f"{case_id}_logs.db")
            if os.path.exists(db_path):
                print(f"\nMigrating {case_id}...")
                try:
                    db = IRLogDatabase(case_id=case_id, base_path=base_path)
                    migrate_to_v5(db)
                    migrated += 1
                except Exception as e:
                    print(f"❌ Error migrating {case_id}: {e}")

    print(f"\n{'='*60}")
    print(f"Migration complete: {migrated} cases upgraded to v5")
