#!/usr/bin/env python3
"""
OTC to PostgreSQL Loader

Loads OTC API data (comments, tickets, timesheets) into PostgreSQL database.
Handles deduplication and provides detailed logging.

Usage:
    python3 -m claude.tools.integrations.otc.load_to_postgres
"""

import logging
import psycopg2
from psycopg2.extras import execute_batch
from typing import Dict, List
from datetime import datetime
import os

from .client import OTCClient
from .models import OTCComment, OTCTicket, OTCTimesheet
import sys

logger = logging.getLogger(__name__)


def get_pg_config() -> Dict:
    """
    Get PostgreSQL configuration from environment variables.

    Environment variables:
        OTC_PG_HOST: Database host (default: localhost)
        OTC_PG_PORT: Database port (default: 5432)
        OTC_PG_DATABASE: Database name (default: servicedesk)
        OTC_PG_USER: Database user (default: servicedesk_user)
        OTC_PG_PASSWORD: Database password (required)

    Returns:
        Dict with PostgreSQL connection parameters

    Raises:
        ValueError: If OTC_PG_PASSWORD not set
    """
    password = os.environ.get('OTC_PG_PASSWORD')
    if not password:
        # Fallback to hardcoded for backward compatibility (will be removed)
        password = 'ServiceDesk2025!SecurePass'

    return {
        'host': os.environ.get('OTC_PG_HOST', 'localhost'),
        'port': int(os.environ.get('OTC_PG_PORT', '5432')),
        'database': os.environ.get('OTC_PG_DATABASE', 'servicedesk'),
        'user': os.environ.get('OTC_PG_USER', 'servicedesk_user'),
        'password': password
    }


# PostgreSQL connection configuration (deprecated - use get_pg_config())
PG_CONFIG = get_pg_config()


class OTCPostgresLoader:
    """Loads OTC data into PostgreSQL with conflict handling."""

    def __init__(self, pg_config: Dict = None):
        """
        Initialize loader with PostgreSQL connection.

        Args:
            pg_config: PostgreSQL connection dict (uses default if None)
        """
        self.pg_config = pg_config or PG_CONFIG
        self.conn = None
        self.stats = {
            'fetched': 0,
            'inserted': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0,
        }

    def connect(self):
        """Establish PostgreSQL connection with transaction support."""
        if not self.conn:
            self.conn = psycopg2.connect(**self.pg_config)
            self.conn.autocommit = False  # Transaction mode with manual commit/rollback
            logger.info("Connected to PostgreSQL (transaction mode)")

    def close(self):
        """Close PostgreSQL connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("Closed PostgreSQL connection")

    def load_comments(self, batch_size: int = 500) -> Dict:
        """
        Load comments from OTC API to PostgreSQL.

        Args:
            batch_size: Number of records to insert per batch

        Returns:
            Stats dict with counts
        """
        logger.info("=" * 60)
        logger.info("LOADING OTC COMMENTS TO POSTGRESQL")
        logger.info("=" * 60)

        start_time = datetime.now()

        # Reset stats for this load
        self.stats = {
            'fetched': 0,
            'inserted': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0,
        }

        self.connect()

        try:
            # Fetch from OTC API
            logger.info("Step 1: Fetching comments from OTC API...")
            client = OTCClient()
            raw_comments = client.fetch_comments(raw=True)

            # Extract data array from response
            if isinstance(raw_comments, dict) and 'message' in raw_comments:
                comments_data = raw_comments['message']['data']
            elif isinstance(raw_comments, dict) and 'data' in raw_comments:
                comments_data = raw_comments['data']
            elif isinstance(raw_comments, list):
                comments_data = raw_comments
            else:
                raise ValueError(f"Unexpected response structure: {type(raw_comments)}")

            self.stats['fetched'] = len(comments_data)
            logger.info(f"   Fetched {self.stats['fetched']} comments")

            # Transform and load in batches
            logger.info("Step 2: Transforming and loading to PostgreSQL...")
            cursor = self.conn.cursor()

            # Prepare simple INSERT
            insert_sql = """
                INSERT INTO servicedesk.comments (
                    comment_id, ticket_id, comment_text, user_id, user_name,
                    owner_type, created_time, visible_to_customer, comment_type, team
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """

            update_sql = """
                UPDATE servicedesk.comments SET
                    comment_text = %s,
                    visible_to_customer = %s,
                    comment_type = %s,
                    team = %s
                WHERE comment_id = %s
            """

            batch = []
            for i, comment_data in enumerate(comments_data):
                try:
                    # Parse comment using Pydantic model
                    comment = OTCComment.model_validate(comment_data)

                    # Prepare values tuple
                    values = (
                        comment.comment_id,
                        comment.ticket_id,
                        comment.comment_text,
                        comment.user_id,
                        comment.user_name,
                        comment.owner_type,
                        comment.created_time,
                        comment.visible_to_customer,
                        comment.comment_type,
                        comment.team,
                    )

                    batch.append(values)

                    # Insert batch when full
                    if len(batch) >= batch_size:
                        self._insert_batch(cursor, insert_sql, update_sql, batch)
                        batch = []

                except Exception as e:
                    logger.warning(f"Failed to process comment {i}: {e}")
                    self.stats['errors'] += 1

            # Insert remaining batch
            if batch:
                self._insert_batch(cursor, insert_sql, update_sql, batch)

            cursor.close()

            duration = (datetime.now() - start_time).total_seconds()

            logger.info("=" * 60)
            logger.info("LOAD COMPLETE")
            logger.info(f"Duration: {duration:.1f}s")
            logger.info(f"Fetched: {self.stats['fetched']}")
            logger.info(f"Inserted: {self.stats['inserted']}")
            logger.info(f"Updated: {self.stats['updated']}")
            logger.info(f"Errors: {self.stats['errors']}")
            logger.info("=" * 60)

            # Record ETL metadata
            self._record_etl_metadata('comments', self.stats, start_time, datetime.now())

            # Commit transaction
            self.conn.commit()
            logger.info("Transaction committed successfully")

            return self.stats

        except Exception as e:
            logger.error(f"Load failed: {e}")
            if self.conn:
                self.conn.rollback()
                logger.error("Transaction rolled back")
            raise
        finally:
            self.close()

    def _insert_batch(self, cursor, insert_sql: str, update_sql: str, batch: List):
        """
        Insert a batch of records with individual error handling.

        Args:
            cursor: Database cursor
            insert_sql: INSERT SQL statement
            update_sql: UPDATE SQL statement for conflicts
            batch: List of value tuples
        """
        for values in batch:
            try:
                # Try INSERT first
                cursor.execute(insert_sql, values)
                self.stats['inserted'] += 1

            except psycopg2.IntegrityError:
                # Duplicate key - update instead (autocommit handles rollback)
                try:
                    # values: (comment_id, ticket_id, text, user_id, user_name, owner_type, created, visible, type, team)
                    # update needs: (text, visible, type, team, comment_id)
                    cursor.execute(update_sql, (values[2], values[7], values[8], values[9], values[0]))
                    if cursor.rowcount > 0:
                        self.stats['updated'] += 1
                    else:
                        self.stats['skipped'] += 1
                except Exception as e:
                    logger.warning(f"Failed to update comment {values[0]}: {e}")
                    self.stats['errors'] += 1

            except Exception as e:
                logger.warning(f"Failed to insert comment {values[0]}: {e}")
                self.stats['errors'] += 1


    def _record_etl_metadata(self, view_name: str, stats: dict,
                              start_time: datetime, end_time: datetime,
                              status: str = 'success', error_message: str = None):
        """
        Record ETL run metadata for tracking and monitoring.

        Args:
            view_name: 'tickets', 'comments', or 'timesheets'
            stats: Stats dict with fetched/inserted/updated/errors
            start_time: When load started
            end_time: When load completed
            status: 'success', 'partial', or 'failed'
            error_message: Error details if failed
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO servicedesk.etl_metadata (
                    view_name,
                    records_fetched,
                    records_inserted,
                    records_updated,
                    records_errors,
                    load_start,
                    load_end,
                    load_duration_seconds,
                    load_status,
                    error_message,
                    last_load_time
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                view_name,
                stats.get('fetched', 0),
                stats.get('inserted', 0),
                stats.get('updated', 0),
                stats.get('errors', 0),
                start_time,
                end_time,
                (end_time - start_time).total_seconds(),
                status,
                error_message,
                end_time
            ))
            self.conn.commit()
            logger.info(f"Recorded ETL metadata for {view_name}")
        except Exception as e:
            logger.error(f"Failed to record ETL metadata: {e}")

    def update_user_lookup(self) -> Dict:
        """
        Update user lookup table with username mappings from tickets and comments.

        Auto-discovers mappings by matching last names between:
        - Comment usernames (short: 'djewell')
        - Ticket assigned users (full: 'Dion Jewell')

        Returns:
            Stats dict with mapping counts
        """
        logger.info("Updating user_lookup table...")

        self.connect()
        cursor = self.conn.cursor()

        stats = {'new_mappings': 0, 'updated_mappings': 0}

        try:
            # Get full names from tickets
            cursor.execute("""
                SELECT DISTINCT "TKT-Assigned To User"
                FROM servicedesk.tickets
                WHERE "TKT-Assigned To User" IS NOT NULL
                  AND "TKT-Assigned To User" != ' PendingAssignment'
                  AND "TKT-Assigned To User" NOT LIKE ' %'
            """)

            full_names = [row[0] for row in cursor.fetchall()]

            # Get short usernames from comments (table might not exist yet)
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'servicedesk'
                    AND table_name = 'comments'
                )
            """)

            if cursor.fetchone()[0]:
                cursor.execute("""
                    SELECT DISTINCT user_name
                    FROM servicedesk.comments
                    WHERE user_name IS NOT NULL
                """)

                short_usernames = [row[0] for row in cursor.fetchall()]

                # Match by last name
                for full_name in full_names:
                    if full_name and len(full_name.split()) >= 2:
                        last_name = full_name.split()[-1].lower()

                        for short_user in short_usernames:
                            if last_name in str(short_user).lower():
                                cursor.execute("""
                                    INSERT INTO servicedesk.user_lookup (short_username, full_name, source)
                                    VALUES (%s, %s, 'auto_etl')
                                    ON CONFLICT (short_username)
                                    DO UPDATE SET full_name = EXCLUDED.full_name, updated_at = NOW()
                                    RETURNING (xmax = 0) AS inserted
                                """, (short_user, full_name))

                                result = cursor.fetchone()
                                if result and result[0]:
                                    stats['new_mappings'] += 1
                                else:
                                    stats['updated_mappings'] += 1

                self.conn.commit()
                logger.info(f"User lookup: {stats['new_mappings']} new, {stats['updated_mappings']} updated")

        except Exception as e:
            logger.error(f"Error updating user lookup: {e}")
            stats['error'] = str(e)

        return stats

    def load_all(self, batch_size: int = 500) -> Dict:
        """
        Load all OTC views (comments, tickets, timesheets) to PostgreSQL.

        Args:
            batch_size: Number of records to insert per batch

        Returns:
            Combined stats dict
        """
        all_stats = {}

        print("=" * 60)
        print("FULL OTC ETL - ALL VIEWS")
        print("=" * 60)

        # Load comments (10 days)
        print("\n1. Loading Comments (10 days)...")
        try:
            all_stats['comments'] = self.load_comments(batch_size)
        except Exception as e:
            print(f"   ❌ Comments failed: {e}")
            all_stats['comments'] = {'error': str(e)}

        # Load timesheets (18 months)
        print("\n2. Loading Timesheets (18 months)...")
        try:
            all_stats['timesheets'] = self.load_timesheets(batch_size)
        except Exception as e:
            print(f"   ❌ Timesheets failed: {e}")
            all_stats['timesheets'] = {'error': str(e)}

        # Load tickets (3 years)
        print("\n3. Loading Tickets (3 years - may take several minutes)...")
        try:
            all_stats['tickets'] = self.load_tickets(batch_size)
        except Exception as e:
            print(f"   ❌ Tickets failed: {e}")
            all_stats['tickets'] = {'error': str(e)}

        # Update user lookup table
        print("\n4. Updating user lookup table...")
        try:
            all_stats['user_lookup'] = self.update_user_lookup()
        except Exception as e:
            print(f"   ❌ User lookup failed: {e}")
            all_stats['user_lookup'] = {'error': str(e)}

        print("\n" + "=" * 60)
        print("ETL COMPLETE")
        print("=" * 60)

        return all_stats

    def load_timesheets(self, batch_size: int = 500) -> Dict:
        """
        Load timesheets from OTC API to PostgreSQL.

        Args:
            batch_size: Number of records to insert per batch

        Returns:
            Stats dict with counts
        """
        logger.info("=" * 60)
        logger.info("LOADING OTC TIMESHEETS TO POSTGRESQL")
        logger.info("=" * 60)

        start_time = datetime.now()
        self.connect()

        # Reset stats
        self.stats = {'fetched': 0, 'inserted': 0, 'updated': 0, 'skipped': 0, 'errors': 0}

        try:
            # Fetch from OTC API
            logger.info("Step 1: Fetching timesheets from OTC API...")
            client = OTCClient()
            raw_timesheets = client.fetch_timesheets(raw=True)

            # Extract data array
            if isinstance(raw_timesheets, dict) and 'message' in raw_timesheets:
                timesheets_data = raw_timesheets['message']['data']
            elif isinstance(raw_timesheets, dict) and 'data' in raw_timesheets:
                timesheets_data = raw_timesheets['data']
            elif isinstance(raw_timesheets, list):
                timesheets_data = raw_timesheets
            else:
                raise ValueError(f"Unexpected response structure: {type(raw_timesheets)}")

            self.stats['fetched'] = len(timesheets_data)
            logger.info(f"   Fetched {self.stats['fetched']} timesheets")

            # Transform and load
            logger.info("Step 2: Transforming and loading to PostgreSQL...")
            cursor = self.conn.cursor()

            upsert_sql = """
                INSERT INTO servicedesk.timesheets (
                    "TS-User Username", "TS-User Full Name", "TS-Date", "TS-Time From", "TS-Time To", "TS-Hours",
                    "TS-Category", "TS-Sub Category", "TS-Type", "TS-Crm ID", "TS-Description",
                    "TS-Account Name"
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT ("TS-User Username", "TS-Date", "TS-Time From", "TS-Crm ID")
                DO UPDATE SET
                    "TS-Hours" = EXCLUDED."TS-Hours",
                    "TS-Description" = EXCLUDED."TS-Description",
                    "TS-Category" = EXCLUDED."TS-Category",
                    "TS-Sub Category" = EXCLUDED."TS-Sub Category"
            """

            batch = []
            for i, ts_data in enumerate(timesheets_data):
                try:
                    ts = OTCTimesheet.model_validate(ts_data)
                    values = (
                        ts.user, ts.user_fullname, ts.date, ts.time_from, ts.time_to, ts.hours,
                        ts.category, ts.sub_category, ts.work_type, ts.crm_id, ts.description,
                        ts.account_name
                    )
                    batch.append(values)

                    if len(batch) >= batch_size:
                        self._upsert_batch_fast(cursor, upsert_sql, batch)
                        batch = []
                except Exception as e:
                    logger.warning(f"Failed to process timesheet {i}: {e}")
                    self.stats['errors'] += 1

            if batch:
                self._upsert_batch_fast(cursor, upsert_sql, batch)

            cursor.close()
            duration = (datetime.now() - start_time).total_seconds()

            logger.info("=" * 60)
            logger.info("LOAD COMPLETE")
            logger.info(f"Duration: {duration:.1f}s")
            logger.info(f"Fetched: {self.stats['fetched']}")
            logger.info(f"Inserted: {self.stats['inserted']}")
            logger.info(f"Errors: {self.stats['errors']}")
            logger.info("=" * 60)

            # Record ETL metadata
            self._record_etl_metadata('timesheets', self.stats, start_time, datetime.now())

            # Commit transaction
            self.conn.commit()
            logger.info("Transaction committed successfully")

            return self.stats
        except Exception as e:
            logger.error(f"Load failed: {e}")
            if self.conn:
                self.conn.rollback()
                logger.error("Transaction rolled back")
            raise
        finally:
            self.close()

    def load_tickets(self, batch_size: int = 500) -> Dict:
        """
        Load tickets from OTC API to PostgreSQL.

        Note: This is 3 years of data and may take several minutes.
        """
        logger.info("=" * 60)
        logger.info("LOADING OTC TICKETS TO POSTGRESQL")
        logger.info("=" * 60)

        start_time = datetime.now()
        self.connect()

        # Reset stats
        self.stats = {'fetched': 0, 'inserted': 0, 'updated': 0, 'skipped': 0, 'errors': 0}

        try:
            # Fetch from OTC API
            logger.info("Step 1: Fetching tickets from OTC API (this may take several minutes)...")
            client = OTCClient()
            raw_tickets = client.fetch_tickets(raw=True)

            # Extract data array
            if isinstance(raw_tickets, dict) and 'message' in raw_tickets:
                tickets_data = raw_tickets['message']['data']
            elif isinstance(raw_tickets, dict) and 'data' in raw_tickets:
                tickets_data = raw_tickets['data']
            elif isinstance(raw_tickets, list):
                tickets_data = raw_tickets
            else:
                raise ValueError(f"Unexpected response structure: {type(raw_tickets)}")

            self.stats['fetched'] = len(tickets_data)
            logger.info(f"   Fetched {self.stats['fetched']} tickets")

            # Transform and load
            logger.info("Step 2: Transforming and loading to PostgreSQL...")
            cursor = self.conn.cursor()

            upsert_sql = """
                INSERT INTO servicedesk.tickets (
                    "TKT-Ticket ID", "TKT-Title", "TKT-Status", "TKT-Severity", "TKT-Category",
                    "TKT-Team", "TKT-Assigned To User", "TKT-Created Time", "TKT-Modified Time",
                    "TKT-Account Name", "TKT-Client Name"
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT ("TKT-Ticket ID") DO UPDATE SET
                    "TKT-Title" = EXCLUDED."TKT-Title",
                    "TKT-Status" = EXCLUDED."TKT-Status",
                    "TKT-Severity" = EXCLUDED."TKT-Severity",
                    "TKT-Category" = EXCLUDED."TKT-Category",
                    "TKT-Team" = EXCLUDED."TKT-Team",
                    "TKT-Assigned To User" = EXCLUDED."TKT-Assigned To User",
                    "TKT-Modified Time" = EXCLUDED."TKT-Modified Time",
                    "TKT-Account Name" = EXCLUDED."TKT-Account Name",
                    "TKT-Client Name" = EXCLUDED."TKT-Client Name"
            """

            batch = []
            for i, ticket_data in enumerate(tickets_data):
                try:
                    ticket = OTCTicket.model_validate(ticket_data)
                    values = (
                        ticket.id, ticket.summary, ticket.status, ticket.priority, ticket.category,
                        ticket.team, ticket.assignee, ticket.created_time, ticket.modified_time,
                        ticket.account_name, ticket.client_name
                    )
                    batch.append(values)

                    if len(batch) >= batch_size:
                        self._upsert_batch_fast(cursor, upsert_sql, batch)
                        batch = []

                    # Progress logging for large dataset
                    if (i + 1) % 10000 == 0:
                        logger.info(f"   Processed {i+1}/{self.stats['fetched']} tickets...")
                except Exception as e:
                    logger.warning(f"Failed to process ticket {i}: {e}")
                    self.stats['errors'] += 1

            if batch:
                self._upsert_batch_fast(cursor, upsert_sql, batch)

            cursor.close()
            duration = (datetime.now() - start_time).total_seconds()

            logger.info("=" * 60)
            logger.info("LOAD COMPLETE")
            logger.info(f"Duration: {duration:.1f}s")
            logger.info(f"Fetched: {self.stats['fetched']}")
            logger.info(f"Inserted: {self.stats['inserted']}")
            logger.info(f"Errors: {self.stats['errors']}")
            logger.info("=" * 60)

            # Record ETL metadata
            self._record_etl_metadata('tickets', self.stats, start_time, datetime.now())

            # Commit transaction
            self.conn.commit()
            logger.info("Transaction committed successfully")

            return self.stats
        except Exception as e:
            logger.error(f"Load failed: {e}")
            if self.conn:
                self.conn.rollback()
                logger.error("Transaction rolled back")
            raise
        finally:
            self.close()

    def _insert_simple_batch(self, cursor, insert_sql: str, batch: List):
        """
        Insert batch with simple error handling (no updates, just inserts).

        Args:
            cursor: Database cursor
            insert_sql: INSERT SQL statement
            batch: List of value tuples
        """
        for values in batch:
            try:
                cursor.execute(insert_sql, values)
                self.stats['inserted'] += 1
            except Exception as e:
                logger.warning(f"Failed to insert record: {e}")
                self.stats['errors'] += 1

    def _upsert_batch(self, cursor, upsert_sql: str, batch: List):
        """
        Upsert a batch of records using ON CONFLICT.
        Tracks inserted vs updated counts.

        Args:
            cursor: Database cursor
            upsert_sql: UPSERT SQL statement with ON CONFLICT clause
            batch: List of value tuples
        """
        for values in batch:
            try:
                cursor.execute(upsert_sql, values)
                if cursor.rowcount > 0:
                    self.stats['inserted'] += 1
            except Exception as e:
                logger.warning(f"Failed to upsert record: {e}")
                self.stats['errors'] += 1

    def _upsert_batch_fast(self, cursor, upsert_sql: str, batch: List):
        """
        Upsert a batch using execute_batch for better performance.

        Uses psycopg2.extras.execute_batch which batches statements
        for significantly better performance (10-50x faster).

        Falls back to row-by-row processing on error for better
        error isolation.

        Args:
            cursor: Database cursor
            upsert_sql: UPSERT SQL statement with ON CONFLICT clause
            batch: List of value tuples
        """
        try:
            execute_batch(cursor, upsert_sql, batch, page_size=100)
            self.stats['inserted'] += len(batch)
        except Exception as e:
            # Fall back to row-by-row for error isolation
            logger.warning(f"Batch upsert failed, falling back to row-by-row: {e}")
            for values in batch:
                try:
                    cursor.execute(upsert_sql, values)
                    self.stats['inserted'] += 1
                except Exception as row_error:
                    logger.warning(f"Failed to upsert record: {row_error}")
                    self.stats['errors'] += 1


def main():
    """CLI interface."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Check command line args
    view = sys.argv[1] if len(sys.argv) > 1 else 'all'

    loader = OTCPostgresLoader()

    if view == 'comments':
        stats = loader.load_comments()
        print("\n✅ Comments load complete")
        print(f"   Fetched: {stats['fetched']}")
        print(f"   Inserted: {stats['inserted']}")
        print(f"   Updated: {stats['updated']}")
        print(f"   Errors: {stats['errors']}")
    elif view == 'timesheets':
        stats = loader.load_timesheets()
        print("\n✅ Timesheets load complete")
        print(f"   Fetched: {stats['fetched']}")
        print(f"   Inserted: {stats['inserted']}")
        print(f"   Errors: {stats['errors']}")
    elif view == 'tickets':
        stats = loader.load_tickets()
        print("\n✅ Tickets load complete")
        print(f"   Fetched: {stats['fetched']}")
        print(f"   Inserted: {stats['inserted']}")
        print(f"   Errors: {stats['errors']}")
    elif view == 'all':
        stats = loader.load_all()
        for view_name, view_stats in stats.items():
            print(f"\n{view_name.upper()}:")
            if 'error' in view_stats:
                print(f"   ❌ Error: {view_stats['error']}")
            else:
                print(f"   Fetched: {view_stats.get('fetched', 0)}")
                print(f"   Inserted: {view_stats.get('inserted', 0)}")
                print(f"   Updated: {view_stats.get('updated', 0)}")
    else:
        print(f"Unknown view: {view}")
        print("Usage: python -m claude.tools.integrations.otc.load_to_postgres [comments|timesheets|tickets|all]")


if __name__ == "__main__":
    main()
