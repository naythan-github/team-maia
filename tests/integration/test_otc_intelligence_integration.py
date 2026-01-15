"""Integration tests for OTC Intelligence Service against real PostgreSQL.

Tests SKIP gracefully if PostgreSQL is unavailable - they do not fail the suite.

Sprint: SPRINT-UFC-001 (Unified Intelligence Framework)
Phase: 265
TDD Phase: P6 - Integration Testing
"""

import pytest
import time
from datetime import datetime


def has_postgresql_connection():
    """Check if PostgreSQL is available."""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="servicedesk",
            user="servicedesk_user",
            password="ServiceDesk2025!SecurePass",
            connect_timeout=3
        )
        conn.close()
        return True
    except:
        return False


# Skip all tests in this module if PostgreSQL is not available
pytestmark = pytest.mark.skipif(
    not has_postgresql_connection(),
    reason="PostgreSQL not available"
)


class TestRealDatabaseQueries:
    """Tests that verify service works against real PostgreSQL data."""

    def test_service_connects_to_postgresql(self):
        """Service connects to servicedesk database."""
        from claude.tools.collection.otc_intelligence_service import OTCIntelligenceService

        service = OTCIntelligenceService()

        # Should have active connection
        assert service.connection is not None, "Service should establish PostgreSQL connection"
        assert not service.connection.closed, "Connection should be open"

    def test_freshness_report_real_data(self):
        """Freshness report returns actual timestamps."""
        from claude.tools.collection.otc_intelligence_service import OTCIntelligenceService

        service = OTCIntelligenceService()
        freshness_report = service.get_data_freshness_report()

        # Should have at least one data source
        assert len(freshness_report) > 0, "Should have freshness data for at least one source"

        # Each source should have valid FreshnessInfo
        for source, info in freshness_report.items():
            assert isinstance(info.last_refresh, datetime) or info.last_refresh is None
            assert isinstance(info.days_old, int)
            assert isinstance(info.record_count, int)

            # If we have a last_refresh, verify it's a real datetime
            if info.last_refresh:
                assert info.last_refresh < datetime.now(), "last_refresh should be in the past"

    def test_get_tickets_by_team_real(self):
        """Returns real Cloud - Infrastructure tickets."""
        from claude.tools.collection.otc_intelligence_service import OTCIntelligenceService

        service = OTCIntelligenceService()
        result = service.get_tickets_by_team("Cloud - Infrastructure")

        # Should get QueryResult
        assert result.source == "otc_servicedesk"
        assert isinstance(result.data, list)
        assert isinstance(result.extraction_timestamp, datetime)

        # If data exists, verify structure
        if len(result.data) > 0:
            ticket = result.data[0]
            # Should have normalized column names
            assert "ticket_id" in ticket
            assert "team" in ticket
            assert "status" in ticket

            # Team should match query
            assert ticket["team"] == "Cloud - Infrastructure"

    def test_get_user_workload_real(self):
        """Returns real workload for known user."""
        from claude.tools.collection.otc_intelligence_service import OTCIntelligenceService

        service = OTCIntelligenceService()

        # First, get any assigned ticket to find a real user
        all_tickets = service.get_open_tickets()

        if len(all_tickets.data) > 0:
            # Find a ticket with an assignee
            assigned_ticket = None
            for ticket in all_tickets.data:
                if ticket.get("assignee"):
                    assigned_ticket = ticket
                    break

            if assigned_ticket:
                user = assigned_ticket["assignee"]
                result = service.get_user_workload(user)

                # Should get QueryResult
                assert result.source == "otc_servicedesk"
                assert isinstance(result.data, list)

                # Should have at least the one ticket we know about
                assert len(result.data) >= 1

                # All tickets should be assigned to this user
                for ticket in result.data:
                    assert ticket["assignee"] == user


class TestQueryPerformance:
    """Tests that verify queries complete within acceptable time limits."""

    def test_team_query_under_1_second(self):
        """Team queries complete in <1s."""
        from claude.tools.collection.otc_intelligence_service import OTCIntelligenceService

        service = OTCIntelligenceService()

        start = time.time()
        result = service.get_tickets_by_team("Cloud - Infrastructure")
        elapsed = time.time() - start

        assert elapsed < 1.0, f"Team query took {elapsed:.3f}s, expected <1.0s"

        # Verify we actually got data (not just a fast failure)
        assert result.source == "otc_servicedesk"

    def test_freshness_query_under_500ms(self):
        """Freshness check is fast."""
        from claude.tools.collection.otc_intelligence_service import OTCIntelligenceService

        service = OTCIntelligenceService()

        start = time.time()
        result = service.get_data_freshness_report()
        elapsed = time.time() - start

        assert elapsed < 0.5, f"Freshness query took {elapsed:.3f}s, expected <0.5s"

        # Verify we actually got data
        assert len(result) > 0


class TestDataIntegrity:
    """Tests that verify data integrity and normalization."""

    def test_normalized_field_names(self):
        """Results use normalized names (team, not TKT-Team)."""
        from claude.tools.collection.otc_intelligence_service import OTCIntelligenceService

        service = OTCIntelligenceService()
        result = service.get_tickets_by_team("Cloud - Infrastructure")

        if len(result.data) > 0:
            ticket = result.data[0]

            # Should have normalized names
            assert "team" in ticket, "Should have 'team' field"
            assert "status" in ticket, "Should have 'status' field"
            assert "ticket_id" in ticket, "Should have 'ticket_id' field"

            # Should NOT have raw database names
            assert "TKT-Team" not in ticket, "Should NOT have raw 'TKT-Team' field"
            assert "TKT-Status" not in ticket, "Should NOT have raw 'TKT-Status' field"
            assert "TKT-Ticket ID" not in ticket, "Should NOT have raw 'TKT-Ticket ID' field"

    def test_no_null_required_fields(self):
        """ticket_id, team, status are never null."""
        from claude.tools.collection.otc_intelligence_service import OTCIntelligenceService

        service = OTCIntelligenceService()
        result = service.get_tickets_by_team("Cloud - Infrastructure")

        # Check all returned tickets
        for ticket in result.data:
            assert ticket.get("ticket_id") is not None, "ticket_id should never be null"
            assert ticket.get("team") is not None, "team should never be null"
            assert ticket.get("status") is not None, "status should never be null"

            # Verify they're not empty strings either
            assert ticket["ticket_id"] != "", "ticket_id should not be empty"
            assert ticket["team"] != "", "team should not be empty"
            assert ticket["status"] != "", "status should not be empty"
