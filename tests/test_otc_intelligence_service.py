"""Tests for OTC Intelligence Service.

Sprint: SPRINT-UFC-001 (Unified Intelligence Framework)
Phase: 265
TDD: Write tests first, then implement service
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from claude.tools.collection.otc_intelligence_service import (
    OTCIntelligenceService,
    COLUMN_NORMALIZATION,
)
from claude.tools.collection.base_intelligence_service import (
    BaseIntelligenceService,
    QueryResult,
    FreshnessInfo,
)


class TestOTCIntelligenceServiceImport:
    """Test basic imports and class structure."""

    def test_import_service(self):
        """OTCIntelligenceService should be importable."""
        assert OTCIntelligenceService is not None

    def test_inherits_base_class(self):
        """Should inherit from BaseIntelligenceService."""
        assert issubclass(OTCIntelligenceService, BaseIntelligenceService)


class TestServiceInitialization:
    """Test service initialization and connection handling."""

    @patch("claude.tools.collection.otc_intelligence_service.psycopg2.connect")
    def test_init_with_default_connection(self, mock_connect):
        """Uses default PostgreSQL connection settings."""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn

        service = OTCIntelligenceService()

        mock_connect.assert_called_once()
        call_args = mock_connect.call_args
        assert call_args[1]["host"] == "localhost"
        assert call_args[1]["port"] == 5432
        assert call_args[1]["database"] == "servicedesk"
        assert call_args[1]["user"] == "servicedesk_user"

    @patch("claude.tools.collection.otc_intelligence_service.psycopg2.connect")
    def test_init_with_custom_connection(self, mock_connect):
        """Accepts custom connection parameters."""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn

        custom_config = {
            "host": "custom-host",
            "port": 5433,
            "database": "custom_db",
            "user": "custom_user",
            "password": "custom_pass",
        }
        service = OTCIntelligenceService(db_config=custom_config)

        mock_connect.assert_called_once()
        call_args = mock_connect.call_args
        assert call_args[1]["host"] == "custom-host"
        assert call_args[1]["port"] == 5433
        assert call_args[1]["database"] == "custom_db"

    @patch("claude.tools.collection.otc_intelligence_service.psycopg2.connect")
    def test_connection_failure_handling(self, mock_connect):
        """Graceful error when PostgreSQL unavailable."""
        mock_connect.side_effect = Exception("Connection refused")

        service = OTCIntelligenceService()

        # Should not raise exception during init
        assert service is not None
        # Connection should be None
        assert service.connection is None


class TestFreshnessReport:
    """Test data freshness reporting."""

    @patch("claude.tools.collection.otc_intelligence_service.psycopg2.connect")
    def test_freshness_report_structure(self, mock_connect):
        """Returns FreshnessInfo for tickets, comments, timesheets."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Mock v_data_freshness view data
        now = datetime.now()
        mock_cursor.fetchall.return_value = [
            ("tickets", now - timedelta(days=2), timedelta(days=2), 1500),
            ("comments", now - timedelta(days=3), timedelta(days=3), 4200),
            ("timesheets", now - timedelta(days=1), timedelta(days=1), 850),
        ]
        mock_cursor.description = [("view_name",), ("last_loaded",), ("age",), ("total_records",)]

        service = OTCIntelligenceService()
        report = service.get_data_freshness_report()

        assert "tickets" in report
        assert "comments" in report
        assert "timesheets" in report
        assert isinstance(report["tickets"], FreshnessInfo)
        assert report["tickets"].record_count == 1500
        assert report["tickets"].days_old == 2

    @patch("claude.tools.collection.otc_intelligence_service.psycopg2.connect")
    def test_freshness_uses_v_data_freshness_view(self, mock_connect):
        """Queries servicedesk.v_data_freshness."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        now = datetime.now()
        mock_cursor.fetchall.return_value = [
            ("tickets", now, timedelta(days=0), 100),
        ]
        mock_cursor.description = [("view_name",), ("last_loaded",), ("age",), ("total_records",)]

        service = OTCIntelligenceService()
        service.get_data_freshness_report()

        # Verify it queries the v_data_freshness view
        executed_sql = mock_cursor.execute.call_args[0][0]
        assert "v_data_freshness" in executed_sql.lower()

    @patch("claude.tools.collection.otc_intelligence_service.psycopg2.connect")
    def test_staleness_detection(self, mock_connect):
        """Marks sources stale when >7 days old."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Stale data (10 days old)
        now = datetime.now()
        mock_cursor.fetchall.return_value = [
            ("tickets", now - timedelta(days=10), timedelta(days=10), 100),
        ]
        mock_cursor.description = [("view_name",), ("last_loaded",), ("age",), ("total_records",)]

        service = OTCIntelligenceService()
        report = service.get_data_freshness_report()

        assert report["tickets"].is_stale is True
        assert report["tickets"].days_old == 10
        assert report["tickets"].warning is not None


class TestTicketQueries:
    """Test ticket query methods."""

    @patch("claude.tools.collection.otc_intelligence_service.psycopg2.connect")
    def test_get_tickets_by_team(self, mock_connect):
        """Filters by TKT-Team field."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        now = datetime.now()
        mock_cursor.fetchall.return_value = [
            ("TKT-001", "Infrastructure Issue", "Infrastructure", "In Progress", "John Doe", now),
        ]
        mock_cursor.description = [
            ("TKT-Ticket ID",), ("TKT-Title",), ("TKT-Team",),
            ("TKT-Status",), ("TKT-Assigned To User",), ("TKT-Created Time",)
        ]

        service = OTCIntelligenceService()
        result = service.get_tickets_by_team("Infrastructure")

        assert len(result.data) == 1
        # Verify the WHERE clause filters by team
        executed_sql = mock_cursor.execute.call_args[0][0]
        assert "TKT-Team" in executed_sql or "team" in executed_sql.lower()

    @patch("claude.tools.collection.otc_intelligence_service.psycopg2.connect")
    def test_get_open_tickets(self, mock_connect):
        """Excludes Closed, Incident Resolved."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        now = datetime.now()
        mock_cursor.fetchall.return_value = [
            ("TKT-001", "Open Issue", "Infrastructure", "In Progress", "John Doe", now),
        ]
        mock_cursor.description = [
            ("TKT-Ticket ID",), ("TKT-Title",), ("TKT-Team",),
            ("TKT-Status",), ("TKT-Assigned To User",), ("TKT-Created Time",)
        ]

        service = OTCIntelligenceService()
        result = service.get_open_tickets()

        # Verify the WHERE clause excludes closed statuses
        executed_sql = mock_cursor.execute.call_args[0][0]
        assert "NOT IN" in executed_sql or "!=" in executed_sql or "<>" in executed_sql

    @patch("claude.tools.collection.otc_intelligence_service.psycopg2.connect")
    def test_get_unassigned_tickets(self, mock_connect):
        """Filters PendingAssignment."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        now = datetime.now()
        mock_cursor.fetchall.return_value = [
            ("TKT-001", "Unassigned Issue", "Infrastructure", "PendingAssignment", None, now),
        ]
        mock_cursor.description = [
            ("TKT-Ticket ID",), ("TKT-Title",), ("TKT-Team",),
            ("TKT-Status",), ("TKT-Assigned To User",), ("TKT-Created Time",)
        ]

        service = OTCIntelligenceService()
        result = service.get_unassigned_tickets()

        # Verify it filters by PendingAssignment status
        executed_sql = mock_cursor.execute.call_args[0][0]
        assert "PendingAssignment" in executed_sql

    @patch("claude.tools.collection.otc_intelligence_service.psycopg2.connect")
    def test_normalized_field_names(self, mock_connect):
        """Returns team, status, assignee (not TKT-Team, TKT-Status)."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        now = datetime.now()
        mock_cursor.fetchall.return_value = [
            ("TKT-001", "Test Ticket", "Infrastructure", "In Progress", "John Doe", now),
        ]
        mock_cursor.description = [
            ("TKT-Ticket ID",), ("TKT-Title",), ("TKT-Team",),
            ("TKT-Status",), ("TKT-Assigned To User",), ("TKT-Created Time",)
        ]

        service = OTCIntelligenceService()
        result = service.get_tickets_by_team("Infrastructure")

        # Verify normalized field names
        assert len(result.data) == 1
        record = result.data[0]
        assert "team" in record
        assert "status" in record
        assert "assignee" in record
        assert "ticket_id" in record
        assert "TKT-Team" not in record
        assert "TKT-Status" not in record


class TestUserQueries:
    """Test user-specific queries."""

    @patch("claude.tools.collection.otc_intelligence_service.psycopg2.connect")
    def test_get_user_workload(self, mock_connect):
        """Returns open tickets for user."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        now = datetime.now()
        mock_cursor.fetchall.return_value = [
            ("TKT-001", "User Task 1", "Infrastructure", "In Progress", "John Doe", now),
            ("TKT-002", "User Task 2", "Infrastructure", "PendingAssignment", "John Doe", now),
        ]
        mock_cursor.description = [
            ("TKT-Ticket ID",), ("TKT-Title",), ("TKT-Team",),
            ("TKT-Status",), ("TKT-Assigned To User",), ("TKT-Created Time",)
        ]

        service = OTCIntelligenceService()
        result = service.get_user_workload("John Doe")

        assert len(result.data) == 2
        # Verify it filters by assignee
        executed_sql = mock_cursor.execute.call_args[0][0]
        assert "TKT-Assigned To User" in executed_sql or "assignee" in executed_sql.lower()

    @patch("claude.tools.collection.otc_intelligence_service.psycopg2.connect")
    def test_get_user_activity(self, mock_connect):
        """Returns 30-day activity summary."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchall.return_value = [
            (10, 5, 3),  # tickets_updated, comments_added, hours_logged
        ]
        mock_cursor.description = [
            ("tickets_updated",), ("comments_added",), ("hours_logged",)
        ]

        service = OTCIntelligenceService()
        result = service.get_user_activity("John Doe")

        assert len(result.data) == 1
        assert result.data[0]["tickets_updated"] == 10
        # Verify it filters last 30 days
        executed_sql = mock_cursor.execute.call_args[0][0]
        assert "30" in executed_sql or "INTERVAL" in executed_sql


class TestTeamQueries:
    """Test team-specific queries."""

    @patch("claude.tools.collection.otc_intelligence_service.psycopg2.connect")
    def test_get_team_backlog(self, mock_connect):
        """Returns unassigned team tickets."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        now = datetime.now()
        mock_cursor.fetchall.return_value = [
            ("TKT-001", "Backlog Item", "Infrastructure", "PendingAssignment", None, now),
        ]
        mock_cursor.description = [
            ("TKT-Ticket ID",), ("TKT-Title",), ("TKT-Team",),
            ("TKT-Status",), ("TKT-Assigned To User",), ("TKT-Created Time",)
        ]

        service = OTCIntelligenceService()
        result = service.get_team_backlog("Infrastructure")

        # Verify it filters by team AND unassigned status
        executed_sql = mock_cursor.execute.call_args[0][0]
        assert "PendingAssignment" in executed_sql
        assert "TKT-Team" in executed_sql or "team" in executed_sql.lower()

    @patch("claude.tools.collection.otc_intelligence_service.psycopg2.connect")
    def test_get_team_health_summary(self, mock_connect):
        """Returns ticket counts by status per team."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchall.return_value = [
            ("Infrastructure", "In Progress", 5),
            ("Infrastructure", "PendingAssignment", 3),
            ("Infrastructure", "Blocked", 2),
        ]
        mock_cursor.description = [
            ("TKT-Team",), ("TKT-Status",), ("count",)
        ]

        service = OTCIntelligenceService()
        result = service.get_team_health_summary("Infrastructure")

        assert len(result.data) == 3
        # Verify it groups by status
        executed_sql = mock_cursor.execute.call_args[0][0]
        assert "GROUP BY" in executed_sql.upper() or "COUNT" in executed_sql.upper()


class TestRawQueryInterface:
    """Test raw SQL query interface."""

    @patch("claude.tools.collection.otc_intelligence_service.psycopg2.connect")
    def test_query_raw_returns_query_result(self, mock_connect):
        """Raw SQL returns QueryResult dataclass."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        now = datetime.now()
        mock_cursor.fetchall.return_value = [
            ("TKT-001", "Test"),
        ]
        mock_cursor.description = [("TKT-Ticket ID",), ("TKT-Title",)]

        service = OTCIntelligenceService()
        result = service.query_raw("SELECT * FROM servicedesk.tickets LIMIT 1")

        assert isinstance(result, QueryResult)
        assert result.source == "otc_servicedesk"
        assert len(result.data) == 1

    @patch("claude.tools.collection.otc_intelligence_service.psycopg2.connect")
    def test_query_raw_includes_timing(self, mock_connect):
        """query_time_ms is populated."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchall.return_value = []
        mock_cursor.description = []

        service = OTCIntelligenceService()
        result = service.query_raw("SELECT 1")

        assert result.query_time_ms >= 0


class TestRefreshOperation:
    """Test data refresh operations."""

    @patch("claude.tools.collection.otc_intelligence_service.subprocess.run")
    @patch("claude.tools.collection.otc_intelligence_service.psycopg2.connect")
    def test_refresh_calls_etl(self, mock_connect, mock_subprocess):
        """refresh() should call the existing ETL."""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn

        mock_subprocess.return_value = Mock(returncode=0)

        service = OTCIntelligenceService()
        result = service.refresh()

        assert result is True
        # Verify ETL was called
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0][0]
        assert "python3" in call_args or "python" in call_args
        assert "load_to_postgres" in " ".join(call_args)
