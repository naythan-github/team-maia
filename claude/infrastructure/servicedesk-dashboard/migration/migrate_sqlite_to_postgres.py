#!/usr/bin/env python3
"""
ServiceDesk Database Migration: SQLite → PostgreSQL
Migrates 1.2GB database (10,939 tickets, 108K+ comments, 141K+ timesheets)
"""

import sqlite3
import psycopg2
from psycopg2.extras import execute_batch
import os
import sys
from datetime import datetime

# Configuration
SQLITE_DB = "/Users/naythandawe/git/maia/claude/data/servicedesk_tickets.db"
POSTGRES_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "servicedesk",
    "user": "servicedesk_user",
    "password": "ServiceDesk2025!SecurePass",  # From .env file
}

# Table migration order (respects dependencies)
TABLES = [
    "tickets",           # No dependencies
    "comments",          # References tickets
    "timesheets",        # References tickets (soft reference)
    "comment_quality",   # References comments (soft reference)
    "cloud_team_roster", # No dependencies
    "import_metadata",   # No dependencies
]

def sqlite_to_postgres_type(sqlite_type):
    """Convert SQLite type to PostgreSQL type"""
    type_lower = str(sqlite_type).upper()
    if 'INT' in type_lower:
        return 'INTEGER'
    elif 'REAL' in type_lower or 'FLOAT' in type_lower or 'DOUBLE' in type_lower:
        return 'REAL'
    elif 'TEXT' in type_lower or 'CHAR' in type_lower or 'CLOB' in type_lower:
        return 'TEXT'
    elif 'TIMESTAMP' in type_lower or 'DATETIME' in type_lower:
        return 'TIMESTAMP'
    elif 'BLOB' in type_lower:
        return 'BYTEA'
    else:
        return 'TEXT'  # Default to TEXT

def create_postgres_schema(sqlite_conn, postgres_conn):
    """
    Create PostgreSQL schema based on SQLite schema
    """
    sqlite_cursor = sqlite_conn.cursor()
    postgres_cursor = postgres_conn.cursor()

    print("\n" + "="*60)
    print("CREATING POSTGRESQL SCHEMA")
    print("="*60)

    # Create schema namespace
    postgres_cursor.execute("CREATE SCHEMA IF NOT EXISTS servicedesk;")
    postgres_cursor.execute("SET search_path TO servicedesk, public;")
    postgres_conn.commit()

    for table in TABLES:
        print(f"\n📋 Creating table: {table}")

        # Get SQLite table schema
        sqlite_cursor.execute(f"PRAGMA table_info({table})")
        columns = sqlite_cursor.fetchall()

        # Build CREATE TABLE statement
        col_defs = []
        for col in columns:
            col_name = col[1]
            col_type = sqlite_to_postgres_type(col[2])

            # Handle quoted column names (with spaces/special chars)
            if ' ' in col_name or '-' in col_name:
                col_name_quoted = f'"{col_name}"'
            else:
                col_name_quoted = col_name

            col_defs.append(f"{col_name_quoted} {col_type}")

        create_sql = f"""
            CREATE TABLE IF NOT EXISTS servicedesk.{table} (
                {', '.join(col_defs)}
            );
        """

        postgres_cursor.execute(create_sql)
        print(f"  ✅ Table created with {len(columns)} columns")

    # Create indexes for analytics performance
    print("\n📊 Creating indexes for analytics...")

    indexes = [
        # SLA queries
        ('idx_tickets_sla_met', 'tickets', '"TKT-SLA Met"'),
        ('idx_tickets_status', 'tickets', '"TKT-Status"'),
        ('idx_tickets_created_time', 'tickets', '"TKT-Created Time"'),

        # Resolution time queries
        ('idx_tickets_resolution_dates', 'tickets', '"TKT-Actual Resolution Date", "TKT-Created Time"'),

        # Team performance queries
        ('idx_tickets_team', 'tickets', '"TKT-Team"'),
        ('idx_tickets_category', 'tickets', '"TKT-Category"'),
        ('idx_tickets_root_cause', 'tickets', '"TKT-Root Cause Category"'),

        # FCR and Comment Coverage queries
        ('idx_comments_ticket_id', 'comments', 'ticket_id'),
        ('idx_comments_visible_to_customer', 'comments', 'visible_to_customer'),

        # Quality queries
        ('idx_comment_quality_score', 'comment_quality', 'quality_score'),
        ('idx_comment_quality_tier', 'comment_quality', 'quality_tier'),

        # Reassignment queries
        ('idx_timesheets_ticket_id', 'timesheets', '"TS-Ticket Project Master Code"'),
        ('idx_timesheets_user', 'timesheets', '"TS-User Full Name"'),

        # Month-based trend queries
        ('idx_tickets_month_created', 'tickets', '"TKT-Month Created"'),

        # Composite indexes
        ('idx_tickets_status_team', 'tickets', '"TKT-Status", "TKT-Team"'),
        ('idx_tickets_status_category', 'tickets', '"TKT-Status", "TKT-Category"'),
    ]

    for idx_name, table, columns in indexes:
        try:
            postgres_cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS {idx_name}
                ON servicedesk.{table} ({columns});
            """)
            print(f"  ✅ Index created: {idx_name}")
        except Exception as e:
            print(f"  ⚠️  Index {idx_name} skipped: {e}")

    postgres_conn.commit()
    print("\n✅ Schema creation complete")

def get_column_names(sqlite_cursor, table_name):
    """Get column names from SQLite table"""
    sqlite_cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in sqlite_cursor.fetchall()]
    return columns

def migrate_table(sqlite_conn, postgres_conn, table_name, batch_size=1000):
    """
    Migrate single table from SQLite to PostgreSQL
    Uses batch inserts for performance (1000 rows/batch)
    """
    sqlite_cursor = sqlite_conn.cursor()
    postgres_cursor = postgres_conn.cursor()

    print(f"\n{'='*60}")
    print(f"Migrating table: {table_name}")
    print(f"{'='*60}")

    # Get column names
    columns = get_column_names(sqlite_cursor, table_name)
    print(f"Columns: {len(columns)}")

    # Get row count
    sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    total_rows = sqlite_cursor.fetchone()[0]
    print(f"Total rows: {total_rows:,}")

    if total_rows == 0:
        print("⚠️  No data to migrate")
        return

    # Prepare INSERT statement
    placeholders = ",".join(["%s"] * len(columns))
    column_names = ",".join([f'"{col}"' if (' ' in col or '-' in col) else col for col in columns])
    insert_sql = f"""
        INSERT INTO servicedesk.{table_name} ({column_names})
        VALUES ({placeholders})
        ON CONFLICT DO NOTHING
    """

    # Fetch and insert in batches
    quoted_cols = ",".join([f'"{col}"' if (' ' in col or '-' in col) else col for col in columns])
    sqlite_cursor.execute(f"SELECT {quoted_cols} FROM {table_name}")

    batch = []
    rows_inserted = 0

    print(f"Migrating in batches of {batch_size}...")
    while True:
        rows = sqlite_cursor.fetchmany(batch_size)
        if not rows:
            break

        batch.extend(rows)

        # Insert batch when full
        if len(batch) >= batch_size:
            execute_batch(postgres_cursor, insert_sql, batch)
            postgres_conn.commit()
            rows_inserted += len(batch)
            print(f"  Progress: {rows_inserted:,}/{total_rows:,} rows ({100*rows_inserted/total_rows:.1f}%)")
            batch = []

    # Insert remaining rows
    if batch:
        execute_batch(postgres_cursor, insert_sql, batch)
        postgres_conn.commit()
        rows_inserted += len(batch)
        print(f"  Progress: {rows_inserted:,}/{total_rows:,} rows (100.0%)")

    print(f"✅ Successfully migrated {rows_inserted:,} rows")

    # Verify row count
    postgres_cursor.execute(f"SELECT COUNT(*) FROM servicedesk.{table_name}")
    postgres_count = postgres_cursor.fetchone()[0]
    print(f"PostgreSQL row count: {postgres_count:,}")

    if postgres_count != total_rows:
        print(f"⚠️  WARNING: Row count mismatch! SQLite: {total_rows}, PostgreSQL: {postgres_count}")
    else:
        print("✅ Row count verified")

def validate_migration(sqlite_conn, postgres_conn):
    """
    Validation checks after migration
    """
    print(f"\n{'='*60}")
    print("VALIDATION CHECKS")
    print(f"{'='*60}\n")

    sqlite_cursor = sqlite_conn.cursor()
    postgres_cursor = postgres_conn.cursor()

    all_pass = True
    for table in TABLES:
        # Row count check
        sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
        sqlite_count = sqlite_cursor.fetchone()[0]

        postgres_cursor.execute(f"SELECT COUNT(*) FROM servicedesk.{table}")
        postgres_count = postgres_cursor.fetchone()[0]

        status = "✅" if sqlite_count == postgres_count else "❌"
        if sqlite_count != postgres_count:
            all_pass = False

        print(f"{status} {table}: SQLite={sqlite_count:,}, PostgreSQL={postgres_count:,}")

    return all_pass

def main():
    """Main migration workflow"""
    start_time = datetime.now()

    print(f"""
╔══════════════════════════════════════════════════════════════╗
║  ServiceDesk Database Migration: SQLite → PostgreSQL         ║
║  Source: {SQLITE_DB}      ║
║  Target: PostgreSQL servicedesk database                     ║
╚══════════════════════════════════════════════════════════════╝
""")

    # Check source database exists
    if not os.path.exists(SQLITE_DB):
        print(f"❌ ERROR: SQLite database not found at {SQLITE_DB}")
        sys.exit(1)

    # Connect to databases
    print("Connecting to databases...")
    try:
        sqlite_conn = sqlite3.connect(SQLITE_DB)
        postgres_conn = psycopg2.connect(**POSTGRES_CONFIG)
        print("✅ Connections established\n")
    except Exception as e:
        print(f"❌ ERROR connecting to databases: {e}")
        sys.exit(1)

    # Create PostgreSQL schema
    try:
        create_postgres_schema(sqlite_conn, postgres_conn)
    except Exception as e:
        print(f"❌ ERROR creating schema: {e}")
        postgres_conn.rollback()
        sys.exit(1)

    # Migrate each table
    for table in TABLES:
        try:
            migrate_table(sqlite_conn, postgres_conn, table, batch_size=1000)
        except Exception as e:
            print(f"❌ ERROR migrating {table}: {e}")
            import traceback
            traceback.print_exc()
            postgres_conn.rollback()
            # Continue with next table

    # Validate migration
    all_pass = validate_migration(sqlite_conn, postgres_conn)

    # Close connections
    sqlite_conn.close()
    postgres_conn.close()

    # Summary
    elapsed = datetime.now() - start_time
    print(f"\n{'='*60}")
    if all_pass:
        print(f"✅ Migration completed successfully in {elapsed}")
    else:
        print(f"⚠️  Migration completed with warnings in {elapsed}")
    print(f"{'='*60}\n")

    if all_pass:
        print("🎉 All tables migrated successfully!")
        print("\nNext steps:")
        print("1. Test Grafana connection to PostgreSQL")
        print("2. Run sample queries to verify data integrity")
        print("3. Configure Grafana data source")
    else:
        print("⚠️  Some tables had migration issues. Review output above.")

if __name__ == "__main__":
    main()
