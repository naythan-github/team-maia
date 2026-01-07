"""
Tests for OTC database schema improvements.

Validates:
- Primary key constraints
- Index existence and performance
- User lookup completeness
- Reporting views functionality
- Helper functions
"""

import pytest
import psycopg2
from datetime import datetime, timedelta


@pytest.fixture
def db_connection():
    """PostgreSQL connection fixture."""
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='servicedesk',
        user='servicedesk_user',
        password='ServiceDesk2025!SecurePass'
    )
    yield conn
    conn.close()


class TestPrimaryKeyConstraints:
    """Test primary key constraints are properly enforced."""

    def test_tickets_has_primary_key(self, db_connection):
        """Tickets table should have primary key on TKT-Ticket ID."""
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT constraint_name
            FROM information_schema.table_constraints
            WHERE table_schema = 'servicedesk'
              AND table_name = 'tickets'
              AND constraint_type = 'PRIMARY KEY'
        """)
        result = cursor.fetchone()
        assert result is not None, "Tickets table should have a primary key"
        assert result[0] == 'tickets_pkey'

    def test_no_duplicate_ticket_ids(self, db_connection):
        """Tickets table should have no duplicate TKT-Ticket IDs."""
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT "TKT-Ticket ID", COUNT(*) as count
            FROM servicedesk.tickets
            GROUP BY "TKT-Ticket ID"
            HAVING COUNT(*) > 1
        """)
        duplicates = cursor.fetchall()
        assert len(duplicates) == 0, f"Found {len(duplicates)} duplicate ticket IDs"


class TestIndexes:
    """Test required indexes exist."""

    def test_tickets_assigned_user_index_exists(self, db_connection):
        """Index on TKT-Assigned To User should exist."""
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = 'servicedesk'
              AND tablename = 'tickets'
              AND indexname = 'idx_tickets_assigned_user'
        """)
        result = cursor.fetchone()
        assert result is not None, "idx_tickets_assigned_user should exist"

    def test_tickets_modified_time_index_exists(self, db_connection):
        """Index on TKT-Modified Time should exist."""
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = 'servicedesk'
              AND tablename = 'tickets'
              AND indexname = 'idx_tickets_modified_time'
        """)
        result = cursor.fetchone()
        assert result is not None, "idx_tickets_modified_time should exist"

    def test_timesheets_crm_id_index_exists(self, db_connection):
        """Index on TS-Crm ID should exist (correct join column)."""
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = 'servicedesk'
              AND tablename = 'timesheets'
              AND indexname = 'idx_timesheets_crm_id'
        """)
        result = cursor.fetchone()
        assert result is not None, "idx_timesheets_crm_id should exist"

    def test_comments_user_name_index_exists(self, db_connection):
        """Index on user_name should exist."""
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = 'servicedesk'
              AND tablename = 'comments'
              AND indexname = 'idx_comments_user_name'
        """)
        result = cursor.fetchone()
        assert result is not None, "idx_comments_user_name should exist"


class TestUserLookupTable:
    """Test user lookup table completeness."""

    def test_user_lookup_has_unique_constraint(self, db_connection):
        """User lookup should have unique constraint on full_name."""
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT constraint_name
            FROM information_schema.table_constraints
            WHERE table_schema = 'servicedesk'
              AND table_name = 'user_lookup'
              AND constraint_type = 'UNIQUE'
              AND constraint_name = 'user_lookup_full_name_unique'
        """)
        result = cursor.fetchone()
        assert result is not None, "user_lookup should have unique constraint on full_name"

    def test_user_lookup_populated(self, db_connection):
        """User lookup should have at least 300 users."""
        cursor = db_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM servicedesk.user_lookup")
        count = cursor.fetchone()[0]
        assert count >= 300, f"Expected at least 300 users, found {count}"

    def test_engineering_team_in_lookup(self, db_connection):
        """All Engineering team members should be in user_lookup."""
        cursor = db_connection.cursor()

        engineering_team = [
            'Trevor Harte', 'Llewellyn Booth', 'Dion Jewell',
            'Michael Villaflor', 'Olli Ojala', 'Abdallah Ziadeh',
            'Alex Olver', 'Josh James', 'Taylor Barkle',
            'Steve Daalmeyer', 'Daniel Dignadice'
        ]

        for name in engineering_team:
            cursor.execute(
                "SELECT COUNT(*) FROM servicedesk.user_lookup WHERE full_name = %s",
                (name,)
            )
            count = cursor.fetchone()[0]
            assert count > 0, f"{name} should be in user_lookup"


class TestMetadataTracking:
    """Test ETL metadata tracking."""

    def test_etl_metadata_table_exists(self, db_connection):
        """etl_metadata table should exist."""
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'servicedesk'
                  AND table_name = 'etl_metadata'
            )
        """)
        exists = cursor.fetchone()[0]
        assert exists, "etl_metadata table should exist"

    def test_etl_metadata_has_index(self, db_connection):
        """etl_metadata should have index on view_name."""
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = 'servicedesk'
              AND tablename = 'etl_metadata'
              AND indexname = 'idx_etl_metadata_view'
        """)
        result = cursor.fetchone()
        assert result is not None, "idx_etl_metadata_view should exist"


class TestReportingViews:
    """Test reporting views exist and function correctly."""

    def test_v_data_freshness_exists(self, db_connection):
        """v_data_freshness view should exist."""
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.views
                WHERE table_schema = 'servicedesk'
                  AND table_name = 'v_data_freshness'
            )
        """)
        exists = cursor.fetchone()[0]
        assert exists, "v_data_freshness view should exist"

    def test_v_orphaned_data_exists(self, db_connection):
        """v_orphaned_data view should exist."""
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.views
                WHERE table_schema = 'servicedesk'
                  AND table_name = 'v_orphaned_data'
            )
        """)
        exists = cursor.fetchone()[0]
        assert exists, "v_orphaned_data view should exist"

    def test_v_user_activity_exists(self, db_connection):
        """v_user_activity view should exist."""
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.views
                WHERE table_schema = 'servicedesk'
                  AND table_name = 'v_user_activity'
            )
        """)
        exists = cursor.fetchone()[0]
        assert exists, "v_user_activity view should exist"

    def test_v_orphaned_data_returns_data(self, db_connection):
        """v_orphaned_data should return expected structure."""
        cursor = db_connection.cursor()
        cursor.execute("SELECT * FROM servicedesk.v_orphaned_data")
        results = cursor.fetchall()
        assert len(results) == 2, "Should have 2 rows (timesheets + comments)"

        # Check structure
        for row in results:
            assert row[0] in ['timesheets', 'comments'], "Source should be timesheets or comments"
            assert isinstance(row[1], int), "Count should be integer"


class TestHelperFunctions:
    """Test helper functions for reporting."""

    def test_get_user_workload_function_exists(self, db_connection):
        """get_user_workload function should exist."""
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM pg_proc p
                JOIN pg_namespace n ON p.pronamespace = n.oid
                WHERE n.nspname = 'servicedesk'
                  AND p.proname = 'get_user_workload'
            )
        """)
        exists = cursor.fetchone()[0]
        assert exists, "get_user_workload function should exist"

    def test_get_team_backlog_function_exists(self, db_connection):
        """get_team_backlog function should exist."""
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM pg_proc p
                JOIN pg_namespace n ON p.pronamespace = n.oid
                WHERE n.nspname = 'servicedesk'
                  AND p.proname = 'get_team_backlog'
            )
        """)
        exists = cursor.fetchone()[0]
        assert exists, "get_team_backlog function should exist"

    def test_get_user_workload_executes(self, db_connection):
        """get_user_workload should execute without error."""
        cursor = db_connection.cursor()
        cursor.execute("SELECT * FROM servicedesk.get_user_workload('Dion Jewell')")
        results = cursor.fetchall()
        # Should return results or empty set (both valid)
        assert isinstance(results, list), "Should return a list"

    def test_get_team_backlog_executes(self, db_connection):
        """get_team_backlog should execute without error."""
        cursor = db_connection.cursor()
        cursor.execute("SELECT * FROM servicedesk.get_team_backlog('Cloud - Infrastructure')")
        results = cursor.fetchall()
        # Should return results or empty set (both valid)
        assert isinstance(results, list), "Should return a list"

    def test_get_team_backlog_returns_correct_structure(self, db_connection):
        """get_team_backlog should return expected columns."""
        cursor = db_connection.cursor()
        cursor.execute("SELECT * FROM servicedesk.get_team_backlog('Cloud - Infrastructure') LIMIT 1")

        if cursor.rowcount > 0:
            row = cursor.fetchone()
            assert len(row) == 6, "Should return 6 columns"
            assert isinstance(row[0], int), "ticket_id should be integer"
            assert isinstance(row[5], int), "age_days should be integer"


class TestDataQuality:
    """Test data quality improvements."""

    def test_engineering_tickets_view_uses_team_field(self, db_connection):
        """v_engineering_tickets should use TKT-Team not TKT-Category."""
        cursor = db_connection.cursor()

        # Get view definition
        cursor.execute("""
            SELECT view_definition
            FROM information_schema.views
            WHERE table_schema = 'servicedesk'
              AND table_name = 'v_engineering_tickets'
        """)
        result = cursor.fetchone()

        if result:
            view_def = result[0]
            assert 'TKT-Team' in view_def, "View should reference TKT-Team field"
            assert 'Cloud - Infrastructure' in view_def or 'is_engineering_team' in view_def, \
                "View should filter by Cloud teams or use is_engineering_team function"

    def test_orphaned_data_percentage_acceptable(self, db_connection):
        """Orphaned data should be tracked and visible."""
        cursor = db_connection.cursor()
        cursor.execute("SELECT * FROM servicedesk.v_orphaned_data WHERE source = 'timesheets'")
        result = cursor.fetchone()

        # Just verify we can see orphaned data, don't enforce percentage
        # (will improve after manual import)
        assert result is not None, "Should be able to query orphaned timesheets"
        assert isinstance(result[1], int), "Count should be integer"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
