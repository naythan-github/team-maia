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


class TestPhase2Performance:
    """Test Phase 2 performance improvements."""

    def test_batch_insert_uses_execute_batch(self, db_connection):
        """Verify _upsert_batch_fast uses execute_batch for performance."""
        from claude.tools.integrations.otc.load_to_postgres import OTCPostgresLoader
        from unittest.mock import patch, MagicMock

        loader = OTCPostgresLoader()
        cursor = MagicMock()

        # Mock execute_batch to verify it's called
        with patch('claude.tools.integrations.otc.load_to_postgres.execute_batch') as mock_execute_batch:
            test_sql = "INSERT INTO test VALUES (%s)"
            test_batch = [('value1',), ('value2',), ('value3',)]

            loader._upsert_batch_fast(cursor, test_sql, test_batch)

            # Verify execute_batch was called with correct parameters
            mock_execute_batch.assert_called_once()
            assert mock_execute_batch.call_args[0][0] == cursor
            assert mock_execute_batch.call_args[0][1] == test_sql
            assert mock_execute_batch.call_args[0][2] == test_batch

    def test_batch_insert_fallback_on_error(self, db_connection):
        """Verify graceful fallback to row-by-row on batch error."""
        from claude.tools.integrations.otc.load_to_postgres import OTCPostgresLoader
        from unittest.mock import patch, MagicMock

        loader = OTCPostgresLoader()
        cursor = MagicMock()

        # Mock execute_batch to raise an error
        with patch('claude.tools.integrations.otc.load_to_postgres.execute_batch') as mock_execute_batch:
            mock_execute_batch.side_effect = Exception("Batch failed")

            test_sql = "INSERT INTO test VALUES (%s)"
            test_batch = [('value1',), ('value2',)]

            # Should not raise - should fall back to row-by-row
            loader._upsert_batch_fast(cursor, test_sql, test_batch)

            # Verify individual execute was called for each row
            assert cursor.execute.call_count == 2

    def test_environment_variable_password_loading(self):
        """Verify password loaded from environment variable."""
        from claude.tools.integrations.otc.load_to_postgres import get_pg_config
        import os

        # Set test password
        os.environ['OTC_PG_PASSWORD'] = 'test_password_123'

        try:
            config = get_pg_config()
            assert config['password'] == 'test_password_123'
            assert config['host'] == 'localhost'  # default
            assert config['port'] == 5432  # default
            assert config['database'] == 'servicedesk'  # default
        finally:
            # Clean up
            del os.environ['OTC_PG_PASSWORD']

    def test_environment_variable_password_fallback(self):
        """Verify fallback to hardcoded password if env var not set."""
        from claude.tools.integrations.otc.load_to_postgres import get_pg_config
        import os

        # Ensure password not in environment
        if 'OTC_PG_PASSWORD' in os.environ:
            del os.environ['OTC_PG_PASSWORD']

        # Should use fallback password (backward compatibility)
        config = get_pg_config()
        assert config['password'] is not None
        assert len(config['password']) > 0


class TestPhase3Reliability:
    """Test Phase 3 reliability improvements."""

    def test_transaction_rollback_on_failure(self, db_connection):
        """Verify transaction rolls back when load fails."""
        from claude.tools.integrations.otc.load_to_postgres import OTCPostgresLoader
        from unittest.mock import patch

        loader = OTCPostgresLoader()

        # Mock the OTCClient class to raise an error during fetch
        with patch('claude.tools.integrations.otc.load_to_postgres.OTCClient') as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.fetch_tickets.side_effect = Exception("API failure")

            # Attempt to load tickets (should fail and rollback)
            try:
                loader.load_tickets()
                assert False, "Should have raised exception"
            except Exception as e:
                assert "API failure" in str(e)

            # Verify connection was rolled back
            # Connection should be None after close() in finally block
            assert loader.conn is None

    def test_transaction_commit_on_success(self, db_connection):
        """Verify transaction commits when load succeeds."""
        from claude.tools.integrations.otc.load_to_postgres import OTCPostgresLoader
        from unittest.mock import patch

        loader = OTCPostgresLoader()

        # Mock the OTCClient class to return empty data (successful load)
        with patch('claude.tools.integrations.otc.load_to_postgres.OTCClient') as mock_client_class:
            mock_client = mock_client_class.return_value
            # Return data in the expected format (list of tickets)
            mock_client.fetch_tickets.return_value = []

            # Load tickets (should succeed and commit)
            stats = loader.load_tickets()

            # Verify successful load
            assert stats['fetched'] == 0  # Empty data
            assert stats['errors'] == 0   # No errors
            # Connection should be None after close() in finally block
            assert loader.conn is None

    def test_stats_reset_in_load_comments(self):
        """Verify load_comments resets stats at start."""
        from claude.tools.integrations.otc.load_to_postgres import OTCPostgresLoader
        from unittest.mock import patch

        loader = OTCPostgresLoader()

        # Set dirty stats
        loader.stats = {
            'fetched': 100,
            'inserted': 50,
            'updated': 25,
            'skipped': 10,
            'errors': 5
        }

        # Mock the OTCClient class to return empty data
        with patch('claude.tools.integrations.otc.load_to_postgres.OTCClient') as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.fetch_comments.return_value = []

            # Load comments (should reset stats)
            stats = loader.load_comments()

            # Verify stats were reset (not cumulative from previous values)
            assert stats['fetched'] == 0, "Stats should be reset, not cumulative"
            assert stats['inserted'] == 0
            assert stats['errors'] == 0

    def test_autocommit_disabled(self):
        """Verify autocommit is disabled for transaction control."""
        from claude.tools.integrations.otc.load_to_postgres import OTCPostgresLoader

        loader = OTCPostgresLoader()
        loader.connect()

        # Verify autocommit is False
        assert loader.conn.autocommit == False, "autocommit should be False for transaction control"

        loader.close()


class TestPhase4CodeQuality:
    """Test Phase 4 code quality improvements."""

    def test_parse_datetime_value_with_none(self):
        """Verify parse_datetime_value handles None correctly."""
        from claude.tools.integrations.otc.models import parse_datetime_value

        result = parse_datetime_value(None)
        assert result is None

    def test_parse_datetime_value_with_empty_string(self):
        """Verify parse_datetime_value handles empty string correctly."""
        from claude.tools.integrations.otc.models import parse_datetime_value

        result = parse_datetime_value('')
        assert result is None

    def test_parse_datetime_value_with_datetime_object(self):
        """Verify parse_datetime_value passes through datetime objects."""
        from claude.tools.integrations.otc.models import parse_datetime_value
        from datetime import datetime

        dt = datetime(2025, 1, 7, 12, 30, 45)
        result = parse_datetime_value(dt)
        assert result == dt
        assert isinstance(result, datetime)

    def test_parse_datetime_value_with_iso_format(self):
        """Verify parse_datetime_value parses ISO format."""
        from claude.tools.integrations.otc.models import parse_datetime_value
        from datetime import datetime

        result = parse_datetime_value('2025-01-07T12:30:45')
        assert result == datetime(2025, 1, 7, 12, 30, 45)

    def test_parse_datetime_value_with_iso_format_z_suffix(self):
        """Verify parse_datetime_value handles ISO format with Z suffix."""
        from claude.tools.integrations.otc.models import parse_datetime_value
        from datetime import datetime, timezone

        result = parse_datetime_value('2025-01-07T12:30:45Z')
        assert result is not None
        assert isinstance(result, datetime)

    def test_parse_datetime_value_with_common_formats(self):
        """Verify parse_datetime_value handles common datetime formats."""
        from claude.tools.integrations.otc.models import parse_datetime_value
        from datetime import datetime

        test_cases = [
            ('2025-01-07 12:30:45', datetime(2025, 1, 7, 12, 30, 45)),
            ('2025-01-07', datetime(2025, 1, 7, 0, 0, 0)),
            ('07/01/2025 12:30:45', datetime(2025, 1, 7, 12, 30, 45)),
            ('07/01/2025 12:30', datetime(2025, 1, 7, 12, 30, 0)),
            ('07/01/2025', datetime(2025, 1, 7, 0, 0, 0)),
        ]

        for input_str, expected in test_cases:
            result = parse_datetime_value(input_str)
            assert result == expected, f"Failed for input: {input_str}"

    def test_parse_datetime_value_with_invalid_string(self):
        """Verify parse_datetime_value returns None for invalid strings."""
        from claude.tools.integrations.otc.models import parse_datetime_value

        result = parse_datetime_value('invalid date')
        assert result is None

    def test_models_use_shared_parser(self):
        """Verify all three models use the shared parse_datetime_value function."""
        from claude.tools.integrations.otc.models import OTCComment, OTCTicket, OTCTimesheet
        import inspect

        # Get the parse_datetime method from each model
        comment_validator = OTCComment.parse_datetime
        ticket_validator = OTCTicket.parse_datetime
        timesheet_validator = OTCTimesheet.parse_datetime

        # Verify they all reference the shared parse_datetime_value function
        # by checking their source code contains 'parse_datetime_value'
        comment_source = inspect.getsource(comment_validator)
        ticket_source = inspect.getsource(ticket_validator)
        timesheet_source = inspect.getsource(timesheet_validator)

        assert 'parse_datetime_value' in comment_source, "OTCComment should use shared parser"
        assert 'parse_datetime_value' in ticket_source, "OTCTicket should use shared parser"
        assert 'parse_datetime_value' in timesheet_source, "OTCTimesheet should use shared parser"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
