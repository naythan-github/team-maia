#!/usr/bin/env python3
"""
XLSX to PostgreSQL Loader for ServiceDesk Data

Loads ServiceDesk data from XLSX exports into PostgreSQL database.
Supports tickets, comments, and timesheets with upsert logic.

Usage:
    python3 -m claude.tools.integrations.otc.xlsx_to_postgres \
        --comments ~/Downloads/exports/Cloud-Ticket-Comments.xlsx \
        --tickets ~/Downloads/exports/Tickets-All-6Months.xlsx \
        --timesheets ~/Downloads/exports/Timesheet-18Months.xlsx

Author: Maia (Data Analyst Agent)
Created: 2026-01-08
"""

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch

# Add maia root to path
MAIA_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

from claude.tools.sre.servicedesk_column_mappings import COLUMN_MAPPINGS

logger = logging.getLogger(__name__)


def get_pg_config() -> Dict:
    """Get PostgreSQL configuration."""
    return {
        'host': os.environ.get('OTC_PG_HOST', 'localhost'),
        'port': int(os.environ.get('OTC_PG_PORT', '5432')),
        'database': os.environ.get('OTC_PG_DATABASE', 'servicedesk'),
        'user': os.environ.get('OTC_PG_USER', 'servicedesk_user'),
        'password': os.environ.get('OTC_PG_PASSWORD', 'ServiceDesk2025!SecurePass')
    }


class XLSXPostgresLoader:
    """Loads XLSX exports into PostgreSQL with upsert logic."""

    def __init__(self, pg_config: Dict = None):
        self.pg_config = pg_config or get_pg_config()
        self.conn = None
        self.stats = {'inserted': 0, 'updated': 0, 'errors': 0}

    def connect(self):
        """Establish PostgreSQL connection."""
        if not self.conn:
            self.conn = psycopg2.connect(**self.pg_config)
            self.conn.autocommit = False
            logger.info("Connected to PostgreSQL")

    def close(self):
        """Close connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def load_comments(self, file_path: str, batch_size: int = 500) -> Dict:
        """
        Load comments from XLSX to PostgreSQL.

        Args:
            file_path: Path to comments XLSX file
            batch_size: Records per batch

        Returns:
            Stats dict
        """
        print(f"\n💬 Loading comments from: {Path(file_path).name}")
        start_time = datetime.now()
        self.stats = {'loaded': 0, 'inserted': 0, 'errors': 0}

        # Load XLSX (first 10 columns only)
        print("   Reading XLSX...")
        df = pd.read_excel(file_path, usecols=range(10))
        print(f"   Loaded {len(df):,} rows")

        # Rename columns using mapping
        mapping = COLUMN_MAPPINGS['comments']
        df = df.rename(columns=mapping)
        print(f"   Columns mapped: {list(df.columns)}")

        # Parse dates
        df['created_time'] = pd.to_datetime(df['created_time'], errors='coerce')

        self.connect()
        cursor = self.conn.cursor()

        # Upsert SQL
        upsert_sql = """
            INSERT INTO servicedesk.comments (
                comment_id, ticket_id, comment_text, user_id, user_name,
                owner_type, created_time, visible_to_customer, comment_type, team
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (comment_id) DO UPDATE SET
                comment_text = EXCLUDED.comment_text,
                visible_to_customer = EXCLUDED.visible_to_customer,
                comment_type = EXCLUDED.comment_type,
                team = EXCLUDED.team
        """

        # Process in batches
        print("   Inserting to PostgreSQL...")
        batch = []
        for i, row in df.iterrows():
            try:
                values = (
                    int(row['comment_id']) if pd.notna(row['comment_id']) else None,
                    int(row['ticket_id']) if pd.notna(row['ticket_id']) else None,
                    str(row['comment_text']) if pd.notna(row['comment_text']) else None,
                    int(row['user_id']) if pd.notna(row['user_id']) else None,
                    str(row['user_name']) if pd.notna(row['user_name']) else None,
                    str(row['owner_type']) if pd.notna(row['owner_type']) else None,
                    row['created_time'] if pd.notna(row['created_time']) else None,
                    str(row['visible_to_customer']) if pd.notna(row['visible_to_customer']) else None,
                    str(row['comment_type']) if pd.notna(row['comment_type']) else None,
                    str(row['team']) if pd.notna(row['team']) else None,
                )
                batch.append(values)

                if len(batch) >= batch_size:
                    self._upsert_batch(cursor, upsert_sql, batch)
                    batch = []

                    # Progress
                    if (i + 1) % 50000 == 0:
                        print(f"   Progress: {i+1:,}/{len(df):,} ({(i+1)/len(df)*100:.1f}%)")

            except Exception as e:
                logger.warning(f"Error processing row {i}: {e}")
                self.stats['errors'] += 1

        # Final batch
        if batch:
            self._upsert_batch(cursor, upsert_sql, batch)

        self.conn.commit()
        cursor.close()

        duration = (datetime.now() - start_time).total_seconds()
        print(f"   ✅ Loaded {self.stats['inserted']:,} comments in {duration:.1f}s")
        print(f"   Errors: {self.stats['errors']}")

        return self.stats

    def load_tickets(self, file_path: str, batch_size: int = 500) -> Dict:
        """
        Load tickets from XLSX to PostgreSQL.

        Tickets use direct column names (TKT-*) matching the database schema.
        """
        print(f"\n📋 Loading tickets from: {Path(file_path).name}")
        start_time = datetime.now()
        self.stats = {'loaded': 0, 'inserted': 0, 'errors': 0}

        # Load XLSX
        print("   Reading XLSX...")
        df = pd.read_excel(file_path)
        print(f"   Loaded {len(df):,} rows, {len(df.columns)} columns")

        # Parse dates
        date_cols = ['TKT-Created Time', 'TKT-Modified Time', 'TKT-Actual Response Date',
                     'TKT-Actual Resolution Date', 'TKT-Closure Date', 'TKT-SLA Closure Date']
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')

        self.connect()
        cursor = self.conn.cursor()

        # Get existing columns from database
        cursor.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_schema = 'servicedesk' AND table_name = 'tickets'
        """)
        db_columns = [row[0] for row in cursor.fetchall()]

        # Filter to columns that exist in both xlsx and db
        common_cols = [col for col in df.columns if col in db_columns]
        print(f"   Using {len(common_cols)} matching columns")

        # Build dynamic upsert SQL
        col_list = ', '.join([f'"{col}"' for col in common_cols])
        placeholders = ', '.join(['%s'] * len(common_cols))
        update_cols = ', '.join([f'"{col}" = EXCLUDED."{col}"' for col in common_cols if col != 'TKT-Ticket ID'])

        upsert_sql = f"""
            INSERT INTO servicedesk.tickets ({col_list})
            VALUES ({placeholders})
            ON CONFLICT ("TKT-Ticket ID") DO UPDATE SET {update_cols}
        """

        # Process in batches
        print("   Inserting to PostgreSQL...")
        batch = []
        for i, row in df.iterrows():
            try:
                values = tuple(
                    row[col] if pd.notna(row[col]) else None
                    for col in common_cols
                )
                batch.append(values)

                if len(batch) >= batch_size:
                    self._upsert_batch(cursor, upsert_sql, batch)
                    batch = []

                    if (i + 1) % 50000 == 0:
                        print(f"   Progress: {i+1:,}/{len(df):,} ({(i+1)/len(df)*100:.1f}%)")

            except Exception as e:
                logger.warning(f"Error processing row {i}: {e}")
                self.stats['errors'] += 1

        if batch:
            self._upsert_batch(cursor, upsert_sql, batch)

        self.conn.commit()
        cursor.close()

        duration = (datetime.now() - start_time).total_seconds()
        print(f"   ✅ Loaded {self.stats['inserted']:,} tickets in {duration:.1f}s")
        print(f"   Errors: {self.stats['errors']}")

        return self.stats

    def load_timesheets(self, file_path: str, batch_size: int = 500) -> Dict:
        """
        Load timesheets from XLSX to PostgreSQL.

        Timesheets use direct column names (TS-*) matching the database schema.
        Uses upsert with ON CONFLICT for the unique constraint.
        """
        print(f"\n⏱️  Loading timesheets from: {Path(file_path).name}")
        start_time = datetime.now()
        self.stats = {'loaded': 0, 'inserted': 0, 'errors': 0}

        # Load XLSX
        print("   Reading XLSX...")
        df = pd.read_excel(file_path)
        print(f"   Loaded {len(df):,} rows, {len(df.columns)} columns")

        # Parse dates
        if 'TS-Date' in df.columns:
            df['TS-Date'] = pd.to_datetime(df['TS-Date'], errors='coerce')

        self.connect()
        cursor = self.conn.cursor()

        # Get existing columns from database
        cursor.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_schema = 'servicedesk' AND table_name = 'timesheets'
        """)
        db_columns = [row[0] for row in cursor.fetchall()]

        # Filter to columns that exist in both xlsx and db
        common_cols = [col for col in df.columns if col in db_columns]
        print(f"   Using {len(common_cols)} matching columns")

        # Build dynamic upsert SQL with ON CONFLICT
        # Unique constraint: ("TS-User Username", "TS-Date", "TS-Time From", "TS-Crm ID")
        col_list = ', '.join([f'"{col}"' for col in common_cols])
        placeholders = ', '.join(['%s'] * len(common_cols))

        # Columns to update on conflict (exclude the unique key columns)
        unique_cols = {'TS-User Username', 'TS-Date', 'TS-Time From', 'TS-Crm ID'}
        update_cols = [col for col in common_cols if col not in unique_cols]
        update_clause = ', '.join([f'"{col}" = EXCLUDED."{col}"' for col in update_cols])

        upsert_sql = f"""
            INSERT INTO servicedesk.timesheets ({col_list})
            VALUES ({placeholders})
            ON CONFLICT ("TS-User Username", "TS-Date", "TS-Time From", "TS-Crm ID")
            DO UPDATE SET {update_clause}
        """

        # Process in batches
        print("   Inserting to PostgreSQL (upsert mode)...")
        batch = []
        for i, row in df.iterrows():
            try:
                values = tuple(
                    row[col] if pd.notna(row[col]) else None
                    for col in common_cols
                )
                batch.append(values)

                if len(batch) >= batch_size:
                    self._upsert_batch(cursor, upsert_sql, batch)
                    batch = []

                    if (i + 1) % 100000 == 0:
                        print(f"   Progress: {i+1:,}/{len(df):,} ({(i+1)/len(df)*100:.1f}%)")

            except Exception as e:
                logger.warning(f"Error processing row {i}: {e}")
                self.stats['errors'] += 1

        if batch:
            self._upsert_batch(cursor, upsert_sql, batch)

        self.conn.commit()
        cursor.close()

        duration = (datetime.now() - start_time).total_seconds()
        print(f"   ✅ Loaded {self.stats['inserted']:,} timesheets in {duration:.1f}s")
        print(f"   Errors: {self.stats['errors']}")

        return self.stats

    def _upsert_batch(self, cursor, sql: str, batch: list):
        """Upsert batch with execute_batch for performance."""
        try:
            execute_batch(cursor, sql, batch, page_size=100)
            self.stats['inserted'] += len(batch)
        except Exception as e:
            logger.warning(f"Batch upsert failed, attempting recovery: {e}")
            # Rollback to clear aborted transaction state
            self.conn.rollback()
            # Fall back to row-by-row with individual commits
            for values in batch:
                try:
                    cursor.execute(sql, values)
                    self.conn.commit()
                    self.stats['inserted'] += 1
                except Exception as row_error:
                    self.conn.rollback()
                    logger.debug(f"Row upsert failed (likely duplicate): {row_error}")
                    self.stats['errors'] += 1

    def _insert_batch(self, cursor, sql: str, batch: list):
        """Insert batch with execute_batch for performance."""
        try:
            execute_batch(cursor, sql, batch, page_size=100)
            self.stats['inserted'] += len(batch)
        except Exception as e:
            logger.warning(f"Batch insert failed, falling back to row-by-row: {e}")
            for values in batch:
                try:
                    cursor.execute(sql, values)
                    self.stats['inserted'] += 1
                except Exception as row_error:
                    logger.warning(f"Row insert failed: {row_error}")
                    self.stats['errors'] += 1

    def load_all(self, comments_path: str, tickets_path: str, timesheets_path: str) -> Dict:
        """Load all three file types."""
        print("\n" + "=" * 60)
        print("XLSX TO POSTGRESQL - FULL LOAD")
        print("=" * 60)

        results = {}

        try:
            # Load comments first (identifies Cloud-touched tickets)
            results['comments'] = self.load_comments(comments_path)

            # Load tickets
            results['tickets'] = self.load_tickets(tickets_path)

            # Load timesheets
            results['timesheets'] = self.load_timesheets(timesheets_path)

            print("\n" + "=" * 60)
            print("✅ LOAD COMPLETE")
            print("=" * 60)
            for entity, stats in results.items():
                print(f"   {entity}: {stats.get('inserted', 0):,} loaded, {stats.get('errors', 0)} errors")

        except Exception as e:
            logger.error(f"Load failed: {e}")
            if self.conn:
                self.conn.rollback()
            raise
        finally:
            self.close()

        return results


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Load ServiceDesk XLSX exports to PostgreSQL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Load all three files
  python3 -m claude.tools.integrations.otc.xlsx_to_postgres \\
      --comments ~/Downloads/exports/Cloud-Ticket-Comments.xlsx \\
      --tickets ~/Downloads/exports/Tickets-All-6Months.xlsx \\
      --timesheets ~/Downloads/exports/Timesheet-18Months.xlsx

  # Load comments only
  python3 -m claude.tools.integrations.otc.xlsx_to_postgres \\
      --comments ~/Downloads/exports/Cloud-Ticket-Comments.xlsx
        """
    )
    parser.add_argument('--comments', '-c', help='Path to comments XLSX file')
    parser.add_argument('--tickets', '-t', help='Path to tickets XLSX file')
    parser.add_argument('--timesheets', '-ts', help='Path to timesheets XLSX file')
    parser.add_argument('--batch-size', type=int, default=500, help='Batch size for inserts')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    loader = XLSXPostgresLoader()

    if args.comments and args.tickets and args.timesheets:
        # Load all
        loader.load_all(args.comments, args.tickets, args.timesheets)
    else:
        # Load individual files
        if args.comments:
            loader.load_comments(args.comments, args.batch_size)
        if args.tickets:
            loader.load_tickets(args.tickets, args.batch_size)
        if args.timesheets:
            loader.load_timesheets(args.timesheets, args.batch_size)

        loader.close()


if __name__ == "__main__":
    main()
