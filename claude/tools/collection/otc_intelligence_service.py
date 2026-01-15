"""OTC Intelligence Service - Unified query interface for OTC ServiceDesk data.

Provides standardized access to OTC ServiceDesk PostgreSQL data with:
- Data freshness monitoring
- Ticket queries (by team, status, assignee)
- User workload and activity tracking
- Team health metrics
- Raw SQL query interface

Sprint: SPRINT-UFC-001 (Unified Intelligence Framework)
Phase: 265
"""

import time
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    psycopg2 = None

from claude.tools.collection.base_intelligence_service import (
    BaseIntelligenceService,
    QueryResult,
    FreshnessInfo,
)

# Default PostgreSQL connection configuration
DEFAULT_DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "servicedesk",
    "user": "servicedesk_user",
    "password": "ServiceDesk2025!SecurePass",
}

# Column name normalization for better usability
COLUMN_NORMALIZATION = {
    "TKT-Team": "team",
    "TKT-Status": "status",
    "TKT-Assigned To User": "assignee",
    "TKT-Ticket ID": "ticket_id",
    "TKT-Title": "title",
    "TKT-Created Time": "created_time",
    "TKT-Category": "category",
    "TKT-Severity": "priority",
    "TKT-Account Name": "account",
}


class OTCIntelligenceService(BaseIntelligenceService):
    """Intelligence service for OTC ServiceDesk PostgreSQL data.

    Provides unified interface for querying OTC ticket data with automatic
    column name normalization and data freshness tracking.
    """

    def __init__(self, db_config: Optional[Dict[str, Any]] = None):
        """Initialize OTC Intelligence Service.

        Args:
            db_config: Optional custom database configuration.
                      Defaults to DEFAULT_DB_CONFIG if not provided.
        """
        self.db_config = db_config or DEFAULT_DB_CONFIG
        self.connection = None

        # Attempt to connect, but don't fail if PostgreSQL is unavailable
        try:
            if psycopg2 is None:
                raise ImportError("psycopg2 not installed")
            self.connection = psycopg2.connect(**self.db_config)
        except Exception as e:
            # Log the error but don't raise - allow graceful degradation
            self.connection = None

    def get_data_freshness_report(self) -> Dict[str, FreshnessInfo]:
        """Get freshness information for all OTC data sources.

        Queries the servicedesk.v_data_freshness view to get last refresh
        timestamps and record counts for tickets, comments, and timesheets.

        Returns:
            Dictionary mapping source name to FreshnessInfo
        """
        if self.connection is None:
            return {}

        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT view_name, last_loaded, age, total_records
                FROM servicedesk.v_data_freshness
            """)

            report = {}
            for row in cursor.fetchall():
                view_name = row[0]
                last_loaded = row[1]
                age = row[2]
                total_records = row[3]

                # Parse age (timedelta object)
                try:
                    if hasattr(age, 'days'):
                        days_old = age.days
                    else:
                        days_old = 999
                except:
                    days_old = 999

                # Determine staleness
                is_stale = days_old > self.STALENESS_THRESHOLD_DAYS
                warning = None
                if is_stale:
                    warning = f"Data is {days_old} days old"

                report[view_name] = FreshnessInfo(
                    last_refresh=last_loaded,
                    days_old=days_old,
                    is_stale=is_stale,
                    record_count=total_records,
                    warning=warning,
                )

            cursor.close()
            return report

        except Exception as e:
            return {}

    def query_raw(self, sql: str, params: tuple = ()) -> QueryResult:
        """Execute raw SQL query against OTC ServiceDesk database.

        Args:
            sql: SQL query string
            params: Query parameters for parameterized queries

        Returns:
            QueryResult with data, timing, and freshness information
        """
        if self.connection is None:
            return QueryResult(
                data=[],
                source="otc_servicedesk",
                extraction_timestamp=datetime.now(),
                is_stale=True,
                staleness_warning="Database connection unavailable",
                query_time_ms=0,
            )

        try:
            start_time = time.time()
            cursor = self.connection.cursor()
            cursor.execute(sql, params)

            # Get column names from cursor description
            columns = [desc[0] for desc in (cursor.description or [])]

            # Fetch all rows and convert to dictionaries
            rows = cursor.fetchall()
            data = []
            for row in rows:
                record = {}
                for i, col in enumerate(columns):
                    # Normalize column names
                    normalized_col = COLUMN_NORMALIZATION.get(col, col)
                    record[normalized_col] = row[i]
                data.append(record)

            cursor.close()

            query_time_ms = int((time.time() - start_time) * 1000)

            return QueryResult(
                data=data,
                source="otc_servicedesk",
                extraction_timestamp=datetime.now(),
                query_time_ms=query_time_ms,
            )

        except Exception as e:
            return QueryResult(
                data=[],
                source="otc_servicedesk",
                extraction_timestamp=datetime.now(),
                is_stale=True,
                staleness_warning=f"Query failed: {str(e)}",
                query_time_ms=0,
            )

    def refresh(self) -> bool:
        """Refresh OTC data by calling existing ETL pipeline.

        Executes: python3 -m claude.tools.integrations.otc.load_to_postgres all

        Returns:
            True if refresh successful, False otherwise
        """
        try:
            result = subprocess.run(
                ["python3", "-m", "claude.tools.integrations.otc.load_to_postgres", "all"],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )
            return result.returncode == 0
        except Exception as e:
            return False

    def get_tickets_by_team(self, team: str) -> QueryResult:
        """Get all tickets for a specific team.

        Args:
            team: Team name to filter by

        Returns:
            QueryResult with ticket records
        """
        sql = """
            SELECT
                "TKT-Ticket ID",
                "TKT-Title",
                "TKT-Team",
                "TKT-Status",
                "TKT-Assigned To User",
                "TKT-Created Time"
            FROM servicedesk.tickets
            WHERE "TKT-Team" = %s
        """
        return self.query_raw(sql, (team,))

    def get_open_tickets(self) -> QueryResult:
        """Get all open tickets (excludes Closed and Incident Resolved).

        Returns:
            QueryResult with open ticket records
        """
        sql = """
            SELECT
                "TKT-Ticket ID",
                "TKT-Title",
                "TKT-Team",
                "TKT-Status",
                "TKT-Assigned To User",
                "TKT-Created Time"
            FROM servicedesk.tickets
            WHERE "TKT-Status" NOT IN ('Closed', 'Incident Resolved')
        """
        return self.query_raw(sql)

    def get_unassigned_tickets(self) -> QueryResult:
        """Get all unassigned tickets (PendingAssignment status).

        Returns:
            QueryResult with unassigned ticket records
        """
        sql = """
            SELECT
                "TKT-Ticket ID",
                "TKT-Title",
                "TKT-Team",
                "TKT-Status",
                "TKT-Assigned To User",
                "TKT-Created Time"
            FROM servicedesk.tickets
            WHERE "TKT-Status" = 'PendingAssignment'
        """
        return self.query_raw(sql)

    def get_user_workload(self, user: str) -> QueryResult:
        """Get open tickets assigned to a specific user.

        Args:
            user: User name to filter by

        Returns:
            QueryResult with user's assigned tickets
        """
        sql = """
            SELECT
                "TKT-Ticket ID",
                "TKT-Title",
                "TKT-Team",
                "TKT-Status",
                "TKT-Assigned To User",
                "TKT-Created Time"
            FROM servicedesk.tickets
            WHERE "TKT-Assigned To User" = %s
                AND "TKT-Status" NOT IN ('Closed', 'Incident Resolved')
        """
        return self.query_raw(sql, (user,))

    def get_user_activity(self, user: str) -> QueryResult:
        """Get 30-day activity summary for a user.

        Args:
            user: User name to get activity for

        Returns:
            QueryResult with activity metrics
        """
        sql = """
            SELECT
                COUNT(DISTINCT t."TKT-Ticket ID") as tickets_updated,
                COUNT(c."Comment ID") as comments_added,
                COALESCE(SUM(ts."Hours Logged"), 0) as hours_logged
            FROM servicedesk.tickets t
            LEFT JOIN servicedesk.comments c
                ON t."TKT-Ticket ID" = c."Ticket ID"
                AND c."Created Time" >= NOW() - INTERVAL '30 days'
            LEFT JOIN servicedesk.timesheets ts
                ON t."TKT-Ticket ID" = ts."Ticket ID"
                AND ts."Date" >= NOW() - INTERVAL '30 days'
            WHERE (
                t."TKT-Assigned To User" = %s
                OR c."Created By" = %s
                OR ts."User" = %s
            )
        """
        return self.query_raw(sql, (user, user, user))

    def get_team_backlog(self, team: str) -> QueryResult:
        """Get unassigned tickets for a team (team backlog).

        Args:
            team: Team name to filter by

        Returns:
            QueryResult with team backlog tickets
        """
        sql = """
            SELECT
                "TKT-Ticket ID",
                "TKT-Title",
                "TKT-Team",
                "TKT-Status",
                "TKT-Assigned To User",
                "TKT-Created Time"
            FROM servicedesk.tickets
            WHERE "TKT-Team" = %s
                AND "TKT-Status" = 'PendingAssignment'
        """
        return self.query_raw(sql, (team,))

    def get_team_health_summary(self, team: str) -> QueryResult:
        """Get ticket count by status for a team.

        Args:
            team: Team name to get health metrics for

        Returns:
            QueryResult with status counts
        """
        sql = """
            SELECT
                "TKT-Team",
                "TKT-Status",
                COUNT(*) as count
            FROM servicedesk.tickets
            WHERE "TKT-Team" = %s
            GROUP BY "TKT-Team", "TKT-Status"
        """
        return self.query_raw(sql, (team,))
