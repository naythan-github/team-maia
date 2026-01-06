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
            logger.info("Connected to PostgreSQL")

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
                        self.conn.commit()  # Commit after each batch
                        batch = []

                except Exception as e:
                    logger.warning(f"Failed to process comment {i}: {e}")
                    self.stats['errors'] += 1

            # Insert remaining batch
            if batch:
                self._insert_batch(cursor, insert_sql, update_sql, batch)
                self.conn.commit()  # Final commit

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
                # Duplicate key - update instead
                self.conn.rollback()
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
                    self.conn.rollback()
                    self.stats['errors'] += 1

            except Exception as e:
                logger.warning(f"Failed to insert comment {values[0]}: {e}")
                self.conn.rollback()
                self.stats['errors'] += 1


def main():
    """CLI interface."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    loader = OTCPostgresLoader()
    stats = loader.load_comments()

    print("\n✅ Load complete")
    print(f"   Fetched: {stats['fetched']}")
    print(f"   Inserted: {stats['inserted']}")
    print(f"   Updated: {stats['updated']}")
    print(f"   Errors: {stats['errors']}")


if __name__ == "__main__":
    main()
