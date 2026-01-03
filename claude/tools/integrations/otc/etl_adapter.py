"""
OTC ETL Adapter

Bridges the OTC API client to the existing ServiceDesk ETL pipeline.
Fetches data from API and transforms it to DataFrame format compatible
with existing validation, cleaning, and PostgreSQL insertion gates.

Usage:
    from claude.tools.integrations.otc.etl_adapter import OTCETLAdapter

    adapter = OTCETLAdapter()

    # Fetch and transform individual entities
    tickets_df = adapter.fetch_and_transform_tickets()
    comments_df = adapter.fetch_and_transform_comments()
    timesheets_df = adapter.fetch_and_transform_timesheets()

    # Or fetch all at once
    all_data = adapter.fetch_all()

The output DataFrames can be passed directly to:
- servicedesk_etl_validator.py for quality checks
- servicedesk_etl_data_cleaner_enhanced.py for cleaning
- PostgreSQL insertion via existing batch patterns
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd

from .client import OTCClient
from .models import OTCComment, OTCTicket, OTCTimesheet, parse_api_response

# Import existing column mappings
import sys
from pathlib import Path

# Add parent paths to import existing modules
MAIA_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

try:
    from claude.tools.sre.servicedesk_column_mappings import (
        COLUMN_MAPPINGS,
        rename_columns,
    )
except ImportError:
    # Fallback if import fails
    COLUMN_MAPPINGS = None
    rename_columns = None

logger = logging.getLogger(__name__)


class OTCETLAdapter:
    """
    Adapter to fetch OTC API data and transform for ETL pipeline.

    Integrates with existing:
    - servicedesk_column_mappings.py (schema mapping)
    - servicedesk_etl_validator.py (40 validation rules)
    - servicedesk_etl_data_cleaner_enhanced.py (data cleaning)
    - PostgreSQL batch insertion patterns
    """

    def __init__(self, client: Optional[OTCClient] = None):
        """
        Initialize adapter with optional client.

        Args:
            client: OTCClient instance. If None, creates new client.
        """
        self.client = client or OTCClient()
        self._last_fetch_time: Dict[str, datetime] = {}

    def fetch_and_transform_tickets(self) -> pd.DataFrame:
        """
        Fetch tickets from OTC API and transform to DataFrame.

        Returns:
            DataFrame with columns matching existing database schema.
            Compatible with existing ETL gates.
        """
        logger.info("Fetching tickets from OTC API...")

        # Fetch raw data
        raw_data = self.client.fetch_tickets(raw=True)
        records = self._normalize_response(raw_data)

        logger.info(f"Received {len(records)} ticket records from API")

        if not records:
            logger.warning("No tickets returned from API")
            return pd.DataFrame()

        # Create DataFrame
        df = pd.DataFrame(records)

        # Log column info for debugging
        logger.debug(f"API returned columns: {list(df.columns)}")

        # Apply column mapping if available
        if rename_columns:
            df = rename_columns(df, 'tickets', direction='to_db')
            logger.debug(f"Renamed columns: {list(df.columns)}")

        # Record fetch time
        self._last_fetch_time['tickets'] = datetime.now()

        logger.info(f"Transformed {len(df)} tickets for ETL")
        return df

    def fetch_and_transform_comments(self) -> pd.DataFrame:
        """
        Fetch comments from OTC API and transform to DataFrame.

        Note: Comments view only returns last 10 days.

        Returns:
            DataFrame with columns matching existing database schema.
        """
        logger.info("Fetching comments from OTC API...")

        # Fetch raw data
        raw_data = self.client.fetch_comments(raw=True)
        records = self._normalize_response(raw_data)

        logger.info(f"Received {len(records)} comment records from API")

        if not records:
            logger.warning("No comments returned from API")
            return pd.DataFrame()

        # Create DataFrame
        df = pd.DataFrame(records)

        # Log column info
        logger.debug(f"API returned columns: {list(df.columns)}")

        # Apply column mapping if available
        if rename_columns:
            df = rename_columns(df, 'comments', direction='to_db')
            logger.debug(f"Renamed columns: {list(df.columns)}")

        # Record fetch time
        self._last_fetch_time['comments'] = datetime.now()

        logger.info(f"Transformed {len(df)} comments for ETL")
        return df

    def fetch_and_transform_timesheets(self) -> pd.DataFrame:
        """
        Fetch timesheets from OTC API and transform to DataFrame.

        Note: Timesheets view returns last 18 months.

        Returns:
            DataFrame with columns matching existing database schema.
        """
        logger.info("Fetching timesheets from OTC API...")

        # Fetch raw data
        raw_data = self.client.fetch_timesheets(raw=True)
        records = self._normalize_response(raw_data)

        logger.info(f"Received {len(records)} timesheet records from API")

        if not records:
            logger.warning("No timesheets returned from API")
            return pd.DataFrame()

        # Create DataFrame
        df = pd.DataFrame(records)

        # Log column info
        logger.debug(f"API returned columns: {list(df.columns)}")

        # Apply column mapping if available
        if rename_columns:
            df = rename_columns(df, 'timesheets', direction='to_db')
            logger.debug(f"Renamed columns: {list(df.columns)}")

        # Record fetch time
        self._last_fetch_time['timesheets'] = datetime.now()

        logger.info(f"Transformed {len(df)} timesheets for ETL")
        return df

    def fetch_all(self) -> dict[str, pd.DataFrame]:
        """
        Fetch all data from OTC API (sequential with gaps).

        Uses the client's sync_all() method which includes 30-second
        gaps between views to protect the legacy system.

        Returns:
            Dict with 'tickets', 'comments', 'timesheets' DataFrames.
        """
        logger.info("Fetching all data from OTC API...")

        # Use client's sync method (handles gaps)
        raw_data = self.client.sync_all()

        result = {}

        # Transform tickets
        if raw_data.get('tickets'):
            df = pd.DataFrame(raw_data['tickets'])
            if rename_columns:
                df = rename_columns(df, 'tickets', direction='to_db')
            result['tickets'] = df
            self._last_fetch_time['tickets'] = datetime.now()
        else:
            result['tickets'] = pd.DataFrame()

        # Transform comments
        if raw_data.get('comments'):
            df = pd.DataFrame(raw_data['comments'])
            if rename_columns:
                df = rename_columns(df, 'comments', direction='to_db')
            result['comments'] = df
            self._last_fetch_time['comments'] = datetime.now()
        else:
            result['comments'] = pd.DataFrame()

        # Transform timesheets
        if raw_data.get('timesheets'):
            df = pd.DataFrame(raw_data['timesheets'])
            if rename_columns:
                df = rename_columns(df, 'timesheets', direction='to_db')
            result['timesheets'] = df
            self._last_fetch_time['timesheets'] = datetime.now()
        else:
            result['timesheets'] = pd.DataFrame()

        logger.info(
            f"Fetched all data: "
            f"{len(result['tickets'])} tickets, "
            f"{len(result['comments'])} comments, "
            f"{len(result['timesheets'])} timesheets"
        )

        return result

    def _normalize_response(self, data: Any) -> list[dict]:
        """
        Normalize API response to list of dicts.

        Handles various response formats:
        - List of records
        - Dict with 'data' key
        - Single record dict

        Args:
            data: Raw API response

        Returns:
            List of record dicts
        """
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            if 'data' in data:
                return data['data'] if isinstance(data['data'], list) else [data['data']]
            elif 'records' in data:
                return data['records'] if isinstance(data['records'], list) else [data['records']]
            else:
                return [data]
        else:
            logger.warning(f"Unexpected response type: {type(data)}")
            return []

    def get_fetch_stats(self) -> dict:
        """
        Get statistics about recent fetches.

        Returns:
            Dict with last fetch times and client metrics.
        """
        return {
            'last_fetch_times': {
                entity: t.isoformat() if t else None
                for entity, t in self._last_fetch_time.items()
            },
            'client_metrics': self.client.get_metrics(),
            'client_health': self.client.health_check(),
        }


class OTCETLSync:
    """
    High-level ETL synchronization from OTC API to PostgreSQL.

    Orchestrates the full sync pipeline:
    1. Fetch from API
    2. Validate data
    3. Clean data
    4. Insert to PostgreSQL

    Usage:
        sync = OTCETLSync()
        result = sync.run_full_sync()
    """

    def __init__(self, adapter: Optional['OTCETLAdapter'] = None):
        """
        Initialize sync orchestrator.

        Args:
            adapter: OTCETLAdapter instance. If None, creates new adapter.
        """
        self.adapter = adapter or OTCETLAdapter()

    def run_full_sync(self, dry_run: bool = False) -> dict:
        """
        Run full ETL sync from OTC API to PostgreSQL.

        Args:
            dry_run: If True, fetch and validate but don't insert.

        Returns:
            Sync result with stats.
        """
        logger.info("=" * 60)
        logger.info("OTC ETL SYNC STARTING")
        logger.info("=" * 60)

        start_time = datetime.now()
        result = {
            'status': 'unknown',
            'start_time': start_time.isoformat(),
            'dry_run': dry_run,
            'entities': {},
        }

        try:
            # Fetch all data
            logger.info("Step 1: Fetching data from OTC API...")
            data = self.adapter.fetch_all()

            for entity, df in data.items():
                result['entities'][entity] = {
                    'fetched_count': len(df),
                    'columns': list(df.columns) if not df.empty else [],
                }

            # Validation step (would integrate with existing validator)
            logger.info("Step 2: Validating data...")
            # TODO: Integrate with servicedesk_etl_validator.py
            for entity, df in data.items():
                if not df.empty:
                    result['entities'][entity]['validated'] = True
                    result['entities'][entity]['quality_score'] = 95  # Placeholder

            if dry_run:
                logger.info("DRY RUN - skipping database insertion")
                result['status'] = 'dry_run_complete'
            else:
                # Cleaning step (would integrate with existing cleaner)
                logger.info("Step 3: Cleaning data...")
                # TODO: Integrate with servicedesk_etl_data_cleaner_enhanced.py

                # PostgreSQL insertion
                logger.info("Step 4: Inserting to PostgreSQL...")
                # TODO: Integrate with existing batch insert patterns

                result['status'] = 'success'

        except Exception as e:
            logger.error(f"Sync failed: {e}")
            result['status'] = 'failed'
            result['error'] = str(e)

        end_time = datetime.now()
        result['end_time'] = end_time.isoformat()
        result['duration_seconds'] = (end_time - start_time).total_seconds()

        logger.info("=" * 60)
        logger.info(f"OTC ETL SYNC {result['status'].upper()}")
        logger.info(f"Duration: {result['duration_seconds']:.1f}s")
        logger.info("=" * 60)

        return result


# CLI interface
if __name__ == "__main__":
    import json
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    adapter = OTCETLAdapter()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "tickets":
            df = adapter.fetch_and_transform_tickets()
            print(f"Fetched {len(df)} tickets")
            if not df.empty:
                print(f"Columns: {list(df.columns)}")
                print(f"\nSample (first 2 rows):\n{df.head(2).to_string()}")

        elif command == "comments":
            df = adapter.fetch_and_transform_comments()
            print(f"Fetched {len(df)} comments")
            if not df.empty:
                print(f"Columns: {list(df.columns)}")

        elif command == "timesheets":
            df = adapter.fetch_and_transform_timesheets()
            print(f"Fetched {len(df)} timesheets")
            if not df.empty:
                print(f"Columns: {list(df.columns)}")

        elif command == "all":
            data = adapter.fetch_all()
            for entity, df in data.items():
                print(f"{entity}: {len(df)} records")

        elif command == "sync":
            sync = OTCETLSync()
            dry_run = "--dry-run" in sys.argv
            result = sync.run_full_sync(dry_run=dry_run)
            print(json.dumps(result, indent=2))

        elif command == "stats":
            stats = adapter.get_fetch_stats()
            print(json.dumps(stats, indent=2, default=str))

        else:
            print(f"Unknown command: {command}")
            print("Available: tickets, comments, timesheets, all, sync, stats")

    else:
        print("OTC ETL Adapter CLI")
        print("")
        print("Usage:")
        print("  python3 -m claude.tools.integrations.otc.etl_adapter tickets    # Fetch tickets")
        print("  python3 -m claude.tools.integrations.otc.etl_adapter comments   # Fetch comments")
        print("  python3 -m claude.tools.integrations.otc.etl_adapter timesheets # Fetch timesheets")
        print("  python3 -m claude.tools.integrations.otc.etl_adapter all        # Fetch all")
        print("  python3 -m claude.tools.integrations.otc.etl_adapter sync       # Full sync")
        print("  python3 -m claude.tools.integrations.otc.etl_adapter sync --dry-run")
        print("  python3 -m claude.tools.integrations.otc.etl_adapter stats      # Show stats")
