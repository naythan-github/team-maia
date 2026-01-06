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

from .client import OTCClient
from .models import OTCComment, OTCTicket, OTCTimesheet
import sys

logger = logging.getLogger(__name__)

# PostgreSQL connection configuration
PG_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'servicedesk',
    'user': 'servicedesk_user',
    'password': 'ServiceDesk2025!SecurePass'
}


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
        """Establish PostgreSQL connection."""
        if not self.conn:
            self.conn = psycopg2.connect(**self.pg_config)
            self.conn.autocommit = True  # Auto-commit each statement
            logger.info("Connected to PostgreSQL (autocommit mode)")

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

            return self.stats

        except Exception as e:
            logger.error(f"Load failed: {e}")
            if self.conn:
                self.conn.rollback()
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

            insert_sql = """
                INSERT INTO servicedesk.timesheets (
                    "TS-User Username", "TS-User Full Name", "TS-Date", "TS-Time From", "TS-Time To", "TS-Hours",
                    "TS-Category", "TS-Sub Category", "TS-Type", "TS-Crm ID", "TS-Description",
                    "TS-Account Name"
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                        self._insert_simple_batch(cursor, insert_sql, batch)
                        batch = []
                except Exception as e:
                    logger.warning(f"Failed to process timesheet {i}: {e}")
                    self.stats['errors'] += 1

            if batch:
                self._insert_simple_batch(cursor, insert_sql, batch)

            cursor.close()
            duration = (datetime.now() - start_time).total_seconds()

            logger.info("=" * 60)
            logger.info("LOAD COMPLETE")
            logger.info(f"Duration: {duration:.1f}s")
            logger.info(f"Fetched: {self.stats['fetched']}")
            logger.info(f"Inserted: {self.stats['inserted']}")
            logger.info(f"Errors: {self.stats['errors']}")
            logger.info("=" * 60)

            return self.stats
        except Exception as e:
            logger.error(f"Load failed: {e}")
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

            insert_sql = """
                INSERT INTO servicedesk.tickets (
                    "TKT-Ticket ID", "TKT-Title", "TKT-Status", "TKT-Severity", "TKT-Category",
                    "TKT-Assigned To User", "TKT-Created Time", "TKT-Modified Time",
                    "TKT-Account Name", "TKT-Client Name"
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            batch = []
            for i, ticket_data in enumerate(tickets_data):
                try:
                    ticket = OTCTicket.model_validate(ticket_data)
                    values = (
                        ticket.id, ticket.summary, ticket.status, ticket.priority, ticket.category,
                        ticket.assignee, ticket.created_time, ticket.modified_time,
                        ticket.account_name, ticket.client_name
                    )
                    batch.append(values)

                    if len(batch) >= batch_size:
                        self._insert_simple_batch(cursor, insert_sql, batch)
                        batch = []

                    # Progress logging for large dataset
                    if (i + 1) % 10000 == 0:
                        logger.info(f"   Processed {i+1}/{self.stats['fetched']} tickets...")
                except Exception as e:
                    logger.warning(f"Failed to process ticket {i}: {e}")
                    self.stats['errors'] += 1

            if batch:
                self._insert_simple_batch(cursor, insert_sql, batch)

            cursor.close()
            duration = (datetime.now() - start_time).total_seconds()

            logger.info("=" * 60)
            logger.info("LOAD COMPLETE")
            logger.info(f"Duration: {duration:.1f}s")
            logger.info(f"Fetched: {self.stats['fetched']}")
            logger.info(f"Inserted: {self.stats['inserted']}")
            logger.info(f"Errors: {self.stats['errors']}")
            logger.info("=" * 60)

            return self.stats
        except Exception as e:
            logger.error(f"Load failed: {e}")
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
