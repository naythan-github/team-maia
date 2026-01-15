"""
Tests for OTC Team Management Database.

Validates:
- Schema creation (3 tables with proper constraints)
- Data migration (11 members, 33 assignments)
- Helper functions (CRUD with history tracking)
- Performance benchmarks (<10ms roster, <20ms joins)
- Integration with existing tickets table
- Audit trail functionality

TDD Methodology: RED-GREEN-REFACTOR
"""

import pytest
import psycopg2
from psycopg2 import sql
from datetime import datetime
import time
import json


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


@pytest.fixture
def clean_tables(db_connection):
    """Clean up test tables before each test."""
    cursor = db_connection.cursor()
    # Drop in reverse dependency order
    cursor.execute("DROP TABLE IF EXISTS servicedesk.team_member_history CASCADE")
    cursor.execute("DROP TABLE IF EXISTS servicedesk.team_queue_assignments CASCADE")
    cursor.execute("DROP TABLE IF EXISTS servicedesk.team_members CASCADE")
    db_connection.commit()
    cursor.close()
    yield
    # Cleanup after test
    cursor = db_connection.cursor()
    cursor.execute("DROP TABLE IF EXISTS servicedesk.team_member_history CASCADE")
    cursor.execute("DROP TABLE IF EXISTS servicedesk.team_queue_assignments CASCADE")
    cursor.execute("DROP TABLE IF EXISTS servicedesk.team_members CASCADE")
    db_connection.commit()
    cursor.close()


class TestSchemaCreation:
    """Test Phase 1: Database schema creation."""

    def test_team_members_table_exists(self, db_connection, clean_tables):
        """Verify team_members table created with correct schema."""
        # This will fail until we create the table (RED)
        cursor = db_connection.cursor()

        # Create the table (this is where the implementation goes)
        from claude.tools.integrations.otc import create_team_management_schema
        create_team_management_schema(db_connection)

        # Verify table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'servicedesk'
                AND table_name = 'team_members'
            )
        """)
        assert cursor.fetchone()[0], "team_members table should exist"

        # Verify columns
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'servicedesk' AND table_name = 'team_members'
            ORDER BY ordinal_position
        """)
        columns = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}

        assert 'id' in columns
        assert 'name' in columns
        assert 'email' in columns
        assert 'organization' in columns
        assert 'team' in columns
        assert 'manager_id' in columns
        assert 'active' in columns
        assert 'start_date' in columns
        assert 'end_date' in columns
        assert 'created_at' in columns
        assert 'updated_at' in columns

        # Verify email is unique
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.table_constraints
            WHERE table_schema = 'servicedesk'
            AND table_name = 'team_members'
            AND constraint_type = 'UNIQUE'
            AND constraint_name LIKE '%email%'
        """)
        assert cursor.fetchone()[0] > 0, "Email should have unique constraint"

        cursor.close()

    def test_team_queue_assignments_table_exists(self, db_connection, clean_tables):
        """Verify team_queue_assignments table created with correct schema."""
        cursor = db_connection.cursor()

        # Create the table
        from claude.tools.integrations.otc import create_team_management_schema
        create_team_management_schema(db_connection)

        # Verify table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'servicedesk'
                AND table_name = 'team_queue_assignments'
            )
        """)
        assert cursor.fetchone()[0], "team_queue_assignments table should exist"

        # Verify key columns
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'servicedesk' AND table_name = 'team_queue_assignments'
        """)
        columns = [row[0] for row in cursor.fetchall()]

        assert 'id' in columns
        assert 'team_member_id' in columns
        assert 'queue_name' in columns
        assert 'assigned_date' in columns
        assert 'removed_date' in columns
        assert 'active' in columns
        assert 'assignment_type' in columns

        cursor.close()

    def test_team_member_history_table_exists(self, db_connection, clean_tables):
        """Verify team_member_history table created with correct schema."""
        cursor = db_connection.cursor()

        # Create the table
        from claude.tools.integrations.otc import create_team_management_schema
        create_team_management_schema(db_connection)

        # Verify table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'servicedesk'
                AND table_name = 'team_member_history'
            )
        """)
        assert cursor.fetchone()[0], "team_member_history table should exist"

        # Verify key columns
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'servicedesk' AND table_name = 'team_member_history'
        """)
        columns = [row[0] for row in cursor.fetchall()]

        assert 'id' in columns
        assert 'team_member_id' in columns
        assert 'change_type' in columns
        assert 'field_changed' in columns
        assert 'old_value' in columns
        assert 'new_value' in columns
        assert 'changed_by' in columns
        assert 'changed_at' in columns

        cursor.close()

    def test_composite_indexes_created(self, db_connection, clean_tables):
        """Verify composite indexes created per Data Analyst requirements."""
        cursor = db_connection.cursor()

        # Create the schema
        from claude.tools.integrations.otc import create_team_management_schema
        create_team_management_schema(db_connection)

        # Check for idx_team_members_team_active (Enhancement 1)
        cursor.execute("""
            SELECT indexname FROM pg_indexes
            WHERE schemaname = 'servicedesk'
            AND tablename = 'team_members'
            AND indexname = 'idx_team_members_team_active'
        """)
        assert cursor.fetchone() is not None, "Composite index idx_team_members_team_active should exist"

        # Check for idx_queue_assignments_queue_active (Enhancement 2)
        cursor.execute("""
            SELECT indexname FROM pg_indexes
            WHERE schemaname = 'servicedesk'
            AND tablename = 'team_queue_assignments'
            AND indexname = 'idx_queue_assignments_queue_active'
        """)
        assert cursor.fetchone() is not None, "Composite index idx_queue_assignments_queue_active should exist"

        cursor.close()

    def test_foreign_key_constraints(self, db_connection, clean_tables):
        """Verify foreign key constraints work correctly."""
        cursor = db_connection.cursor()

        # Create schema
        from claude.tools.integrations.otc import create_team_management_schema
        create_team_management_schema(db_connection)

        # Test manager_id FK (self-referential)
        cursor.execute("""
            INSERT INTO servicedesk.team_members (name, email)
            VALUES ('Test Manager', 'manager@test.com')
            RETURNING id
        """)
        manager_id = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO servicedesk.team_members (name, email, manager_id)
            VALUES ('Test Employee', 'employee@test.com', %s)
        """, (manager_id,))
        db_connection.commit()

        # Test team_member_id FK in assignments
        cursor.execute("""
            INSERT INTO servicedesk.team_members (name, email)
            VALUES ('Test Member', 'member@test.com')
            RETURNING id
        """)
        member_id = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO servicedesk.team_queue_assignments (team_member_id, queue_name)
            VALUES (%s, 'Test Queue')
        """, (member_id,))
        db_connection.commit()

        # Verify cascade delete works
        cursor.execute("DELETE FROM servicedesk.team_members WHERE id = %s", (member_id,))
        cursor.execute("SELECT COUNT(*) FROM servicedesk.team_queue_assignments WHERE team_member_id = %s", (member_id,))
        assert cursor.fetchone()[0] == 0, "Cascade delete should remove assignments"

        db_connection.commit()
        cursor.close()

    def test_check_constraints(self, db_connection, clean_tables):
        """Verify check constraints enforce business rules."""
        cursor = db_connection.cursor()

        # Create schema
        from claude.tools.integrations.otc import create_team_management_schema
        create_team_management_schema(db_connection)

        # Test valid_date_range constraint
        with pytest.raises(psycopg2.IntegrityError):
            cursor.execute("""
                INSERT INTO servicedesk.team_members (name, email, start_date, end_date)
                VALUES ('Test User', 'test@test.com', '2025-01-15', '2025-01-01')
            """)
            db_connection.commit()

        db_connection.rollback()

        # Test active_requires_no_end_date constraint
        with pytest.raises(psycopg2.IntegrityError):
            cursor.execute("""
                INSERT INTO servicedesk.team_members (name, email, active, end_date)
                VALUES ('Test User', 'test2@test.com', true, '2025-01-01')
            """)
            db_connection.commit()

        db_connection.rollback()
        cursor.close()

    def test_table_comments_exist(self, db_connection, clean_tables):
        """Verify table and column comments created for documentation."""
        cursor = db_connection.cursor()

        # Create schema
        from claude.tools.integrations.otc import create_team_management_schema
        create_team_management_schema(db_connection)

        # Check team_members table comment
        cursor.execute("""
            SELECT obj_description('servicedesk.team_members'::regclass)
        """)
        comment = cursor.fetchone()[0]
        assert comment is not None, "team_members table should have comment"

        # Check team_member_history retention policy comment (Enhancement 3)
        cursor.execute("""
            SELECT obj_description('servicedesk.team_member_history'::regclass)
        """)
        comment = cursor.fetchone()[0]
        assert comment is not None, "team_member_history should have retention policy comment"
        assert '7 year' in comment.lower(), "Retention policy should mention 7 years"

        cursor.close()


class TestDataMigration:
    """Test Phase 2: Data migration from JSON."""

    def test_migration_inserts_11_members(self, db_connection, clean_tables):
        """Verify all 11 team members migrated."""
        cursor = db_connection.cursor()

        # Create schema
        from claude.tools.integrations.otc import create_team_management_schema
        create_team_management_schema(db_connection)

        # Run migration
        from claude.tools.integrations.otc import migrate_team_data
        migrate_team_data(db_connection)

        # Verify 11 members inserted
        cursor.execute("""
            SELECT COUNT(*) FROM servicedesk.team_members WHERE active = true
        """)
        assert cursor.fetchone()[0] == 11, "Should have 11 active team members"

        # Verify expected members exist
        cursor.execute("""
            SELECT name FROM servicedesk.team_members WHERE active = true ORDER BY name
        """)
        names = [row[0] for row in cursor.fetchall()]

        expected_names = [
            'Abdallah Ziadeh', 'Alex Olver', 'Daniel Dignadice', 'Dion Jewell',
            'Josh James', 'Llewellyn Booth', 'Michael Villaflor', 'Olli Ojala',
            'Steve Daalmeyer', 'Taylor Barkle', 'Trevor Harte'
        ]
        assert names == expected_names, f"Expected {expected_names}, got {names}"

        cursor.close()

    def test_migration_inserts_33_assignments(self, db_connection, clean_tables):
        """Verify all 33 queue assignments migrated (11 × 3)."""
        cursor = db_connection.cursor()

        # Create schema and migrate
        from claude.tools.integrations.otc import create_team_management_schema, migrate_team_data
        create_team_management_schema(db_connection)
        migrate_team_data(db_connection)

        # Verify 33 assignments
        cursor.execute("""
            SELECT COUNT(*) FROM servicedesk.team_queue_assignments WHERE active = true
        """)
        assert cursor.fetchone()[0] == 33, "Should have 33 active queue assignments (11 members × 3 queues)"

        # Verify 11 members per queue
        cursor.execute("""
            SELECT queue_name, COUNT(*) AS members
            FROM servicedesk.team_queue_assignments
            WHERE active = true
            GROUP BY queue_name
            ORDER BY queue_name
        """)
        assignments = cursor.fetchall()

        assert len(assignments) == 3, "Should have 3 queues"
        for queue_name, count in assignments:
            assert count == 11, f"Queue '{queue_name}' should have 11 members, got {count}"

        cursor.close()

    def test_migrated_data_matches_json(self, db_connection, clean_tables):
        """Verify migrated data matches source JSON."""
        cursor = db_connection.cursor()

        # Create schema and migrate
        from claude.tools.integrations.otc import create_team_management_schema, migrate_team_data
        create_team_management_schema(db_connection)
        migrate_team_data(db_connection)

        # Load source JSON
        import json
        with open('/Users/YOUR_USERNAME/maia/claude/data/user_preferences.json', 'r') as f:
            prefs = json.load(f)

        source_members = prefs['analysis_preferences']['otc_servicedesk']['teams']['engineering']['members']
        source_queues = prefs['analysis_preferences']['otc_servicedesk']['teams']['engineering']['team_assignments']

        # Verify member emails match
        cursor.execute("""
            SELECT email FROM servicedesk.team_members WHERE active = true ORDER BY email
        """)
        db_emails = [row[0] for row in cursor.fetchall()]
        source_emails = sorted([m['email'] for m in source_members])

        assert db_emails == source_emails, "Database emails should match JSON source"

        # Verify queue names match
        cursor.execute("""
            SELECT DISTINCT queue_name FROM servicedesk.team_queue_assignments
            WHERE active = true ORDER BY queue_name
        """)
        db_queues = [row[0] for row in cursor.fetchall()]

        assert db_queues == sorted(source_queues), "Database queues should match JSON source"

        cursor.close()

    def test_no_duplicate_emails(self, db_connection, clean_tables):
        """Verify email uniqueness constraint enforced."""
        cursor = db_connection.cursor()

        # Create schema and migrate
        from claude.tools.integrations.otc import create_team_management_schema, migrate_team_data
        create_team_management_schema(db_connection)
        migrate_team_data(db_connection)

        # Try to insert duplicate email
        with pytest.raises(psycopg2.IntegrityError):
            cursor.execute("""
                INSERT INTO servicedesk.team_members (name, email)
                VALUES ('Duplicate User', 'trevor.harte@orro.group')
            """)
            db_connection.commit()

        db_connection.rollback()
        cursor.close()

    def test_migration_idempotent(self, db_connection, clean_tables):
        """Verify migration can be run multiple times safely."""
        cursor = db_connection.cursor()

        # Create schema
        from claude.tools.integrations.otc import create_team_management_schema, migrate_team_data
        create_team_management_schema(db_connection)

        # Run migration twice
        migrate_team_data(db_connection)
        cursor.execute("SELECT COUNT(*) FROM servicedesk.team_members")
        result1 = cursor.fetchone()[0]

        # Second run should not duplicate
        migrate_team_data(db_connection)
        cursor.execute("SELECT COUNT(*) FROM servicedesk.team_members")
        result2 = cursor.fetchone()[0]

        assert result1 == result2, "Migration should be idempotent (no duplicates)"

        cursor.close()


class TestTeamManagementFunctions:
    """Test Phase 3: Python helper functions."""

    def test_get_connection(self, clean_tables):
        """Test database connection helper."""
        from claude.tools.integrations.otc.team_management import get_connection

        conn = get_connection()
        assert conn is not None, "Connection should be established"

        # Verify connection is usable
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        assert cursor.fetchone()[0] == 1
        cursor.close()
        conn.close()

    def test_get_team_members(self, db_connection, clean_tables):
        """Test get_team_members returns correct roster."""
        from claude.tools.integrations.otc import create_team_management_schema, migrate_team_data
        from claude.tools.integrations.otc.team_management import get_team_members

        # Setup
        create_team_management_schema(db_connection)
        migrate_team_data(db_connection)

        # Test
        members = get_team_members()

        assert len(members) == 11, "Should have 11 engineering team members"
        assert all('name' in m for m in members), "All members should have name"
        assert all('email' in m for m in members), "All members should have email"

        # Verify specific member exists
        trevor = [m for m in members if m['email'] == 'trevor.harte@orro.group']
        assert len(trevor) == 1, "Trevor Harte should exist"

    def test_get_team_members_active_filter(self, db_connection, clean_tables):
        """Test active_only parameter filters correctly."""
        from claude.tools.integrations.otc import create_team_management_schema, migrate_team_data
        from claude.tools.integrations.otc.team_management import get_team_members, update_team_member, get_member_by_email

        # Setup
        create_team_management_schema(db_connection)
        migrate_team_data(db_connection)

        # Deactivate one member
        member = get_member_by_email('trevor.harte@orro.group')
        update_team_member(member['id'], active=False, end_date='2026-01-01')

        # Test active_only=True
        active_members = get_team_members(active_only=True)
        assert len(active_members) == 10, "Should have 10 active members"

        # Test active_only=False
        all_members = get_team_members(active_only=False)
        assert len(all_members) == 11, "Should have 11 total members"

    def test_get_team_members_fallback_to_json(self):
        """Test graceful fallback to JSON when DB unavailable."""
        from claude.tools.integrations.otc.team_management import get_team_members

        # Test with fallback enabled (DB not initialized, should use JSON)
        members = get_team_members(fallback_to_json=True)

        assert len(members) == 11, "Should fallback to JSON with 11 members"
        assert all('name' in m for m in members), "JSON members should have name"

    def test_get_team_queues(self, db_connection, clean_tables):
        """Test get_team_queues returns correct queues."""
        from claude.tools.integrations.otc import create_team_management_schema, migrate_team_data
        from claude.tools.integrations.otc.team_management import get_team_queues

        # Setup
        create_team_management_schema(db_connection)
        migrate_team_data(db_connection)

        # Test
        queues = get_team_queues()

        assert len(queues) == 3, "Should have 3 queues"
        assert 'Cloud - Infrastructure' in queues
        assert 'Cloud - Security' in queues
        assert 'Cloud - L3 Escalation' in queues

    def test_get_member_by_email(self, db_connection, clean_tables):
        """Test email lookup."""
        from claude.tools.integrations.otc import create_team_management_schema, migrate_team_data
        from claude.tools.integrations.otc.team_management import get_member_by_email

        # Setup
        create_team_management_schema(db_connection)
        migrate_team_data(db_connection)

        # Test existing member
        member = get_member_by_email('trevor.harte@orro.group')
        assert member is not None, "Should find Trevor Harte"
        assert member['name'] == 'Trevor Harte'
        assert member['email'] == 'trevor.harte@orro.group'

        # Test non-existent member
        no_member = get_member_by_email('nonexistent@test.com')
        assert no_member is None, "Should return None for non-existent email"

    def test_get_member_workload(self, db_connection, clean_tables):
        """Test workload statistics calculation."""
        from claude.tools.integrations.otc import create_team_management_schema, migrate_team_data
        from claude.tools.integrations.otc.team_management import get_member_by_email, get_member_workload

        # Setup
        create_team_management_schema(db_connection)
        migrate_team_data(db_connection)

        # Get a member
        member = get_member_by_email('trevor.harte@orro.group')

        # Test workload (may be zero if no tickets)
        workload = get_member_workload(member['id'])

        assert 'name' in workload
        assert 'total_tickets' in workload
        assert 'open_tickets' in workload
        assert 'closed_tickets' in workload
        assert 'closure_rate_pct' in workload
        assert workload['total_tickets'] >= 0

    def test_add_team_member(self, db_connection, clean_tables):
        """Test adding new team member creates history entry."""
        from claude.tools.integrations.otc import create_team_management_schema
        from claude.tools.integrations.otc.team_management import add_team_member, get_member_by_email

        # Setup
        create_team_management_schema(db_connection)

        # Add new member
        member_id = add_team_member(
            name='Test User',
            email='test.user@orro.group',
            changed_by='test_system'
        )

        assert member_id > 0, "Should return new member ID"

        # Verify member exists
        member = get_member_by_email('test.user@orro.group')
        assert member is not None
        assert member['name'] == 'Test User'

        # Verify history entry created
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM servicedesk.team_member_history
            WHERE team_member_id = %s AND change_type = 'created'
        """, (member_id,))
        assert cursor.fetchone()[0] == 1, "Should have history entry for member creation"
        cursor.close()

    def test_update_team_member_with_history(self, db_connection, clean_tables):
        """Test updating member creates history entry."""
        from claude.tools.integrations.otc import create_team_management_schema
        from claude.tools.integrations.otc.team_management import add_team_member, update_team_member, get_member_by_email

        # Setup
        create_team_management_schema(db_connection)

        # Add member
        member_id = add_team_member(name='Test User', email='test.user@orro.group')

        # Update member
        success = update_team_member(
            member_id,
            name='Updated User',
            notes='Test notes',
            changed_by='test_system'
        )

        assert success is True, "Update should succeed"

        # Verify update
        member = get_member_by_email('test.user@orro.group')
        assert member['name'] == 'Updated User'

        # Verify history entries created (one for each changed field)
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM servicedesk.team_member_history
            WHERE team_member_id = %s AND change_type = 'updated'
        """, (member_id,))
        history_count = cursor.fetchone()[0]
        assert history_count >= 2, "Should have history entries for name and notes changes"
        cursor.close()

    def test_assign_queue(self, db_connection, clean_tables):
        """Test queue assignment."""
        from claude.tools.integrations.otc import create_team_management_schema
        from claude.tools.integrations.otc.team_management import add_team_member, assign_queue

        # Setup
        create_team_management_schema(db_connection)

        # Add member
        member_id = add_team_member(name='Test User', email='test.user@orro.group')

        # Assign queue
        assignment_id = assign_queue(
            member_id,
            'Cloud - Infrastructure',
            assignment_type='primary'
        )

        assert assignment_id > 0, "Should return assignment ID"

        # Verify assignment
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT queue_name, active FROM servicedesk.team_queue_assignments
            WHERE id = %s
        """, (assignment_id,))
        result = cursor.fetchone()
        assert result[0] == 'Cloud - Infrastructure'
        assert result[1] is True
        cursor.close()

    def test_remove_queue_assignment_soft_delete(self, db_connection, clean_tables):
        """Test soft delete of queue assignment."""
        from claude.tools.integrations.otc import create_team_management_schema
        from claude.tools.integrations.otc.team_management import add_team_member, assign_queue, remove_queue_assignment

        # Setup
        create_team_management_schema(db_connection)

        # Add member and assign queue
        member_id = add_team_member(name='Test User', email='test.user@orro.group')
        assignment_id = assign_queue(member_id, 'Cloud - Infrastructure')

        # Remove assignment
        success = remove_queue_assignment(assignment_id)

        assert success is True, "Removal should succeed"

        # Verify soft delete (active=false, not deleted)
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT active, removed_date FROM servicedesk.team_queue_assignments
            WHERE id = %s
        """, (assignment_id,))
        result = cursor.fetchone()
        assert result[0] is False, "Assignment should be inactive"
        assert result[1] is not None, "Should have removed_date"
        cursor.close()

    def test_export_teams_to_json(self, db_connection, clean_tables):
        """Test DB → JSON export for fallback freshness."""
        from claude.tools.integrations.otc import create_team_management_schema, migrate_team_data
        from claude.tools.integrations.otc.team_management import export_teams_to_json
        import json

        # Setup
        create_team_management_schema(db_connection)
        migrate_team_data(db_connection)

        # Export
        export_teams_to_json()

        # Verify JSON updated
        with open('/Users/YOUR_USERNAME/maia/claude/data/user_preferences.json', 'r') as f:
            prefs = json.load(f)

        members = prefs['analysis_preferences']['otc_servicedesk']['teams']['engineering']['members']
        assert len(members) == 11, "JSON should have 11 members after export"

        # Verify expected member exists
        trevor = [m for m in members if m['email'] == 'trevor.harte@orro.group']
        assert len(trevor) == 1, "Trevor Harte should exist in exported JSON"


class TestQueryPerformance:
    """Test Phase 4: Performance benchmarks."""

    def test_team_roster_query_performance(self, db_connection, clean_tables):
        """Benchmark team roster query (target: <10ms)."""
        from claude.tools.integrations.otc import create_team_management_schema, migrate_team_data
        import time

        # Setup
        create_team_management_schema(db_connection)
        migrate_team_data(db_connection)

        # Warm up query cache
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT name, email FROM servicedesk.team_members
            WHERE team = 'engineering' AND active = true
        """)
        cursor.fetchall()
        cursor.close()

        # Benchmark
        start = time.time()
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT name, email FROM servicedesk.team_members
            WHERE team = 'engineering' AND active = true
        """)
        results = cursor.fetchall()
        elapsed_ms = (time.time() - start) * 1000
        cursor.close()

        assert len(results) == 11, "Should return 11 members"
        assert elapsed_ms < 10, f"Query took {elapsed_ms:.2f}ms, expected <10ms (target: 5-7ms)"

    def test_team_tickets_join_performance(self, db_connection, clean_tables):
        """Benchmark team tickets join query (target: <20ms)."""
        from claude.tools.integrations.otc import create_team_management_schema, migrate_team_data
        import time

        # Setup
        create_team_management_schema(db_connection)
        migrate_team_data(db_connection)

        # Check if tickets table exists and has data
        cursor = db_connection.cursor()
        try:
            cursor.execute("""
                SELECT COUNT(*) FROM servicedesk.tickets
                WHERE "TKT-Assigned To User" IN (
                    SELECT name FROM servicedesk.team_members WHERE team = 'engineering'
                )
            """)
            ticket_count = cursor.fetchone()[0]
        except Exception:
            # Tickets table might not exist or have different schema - skip this test
            cursor.close()
            import pytest
            pytest.skip("Tickets table not available for join test")
            return

        if ticket_count == 0:
            # No tickets assigned to team - test just the join performance with empty result
            pass

        # Warm up query cache
        cursor.execute("""
            SELECT COUNT(*) as ticket_count, tm.name
            FROM servicedesk.team_members tm
            LEFT JOIN servicedesk.tickets t ON t."TKT-Assigned To User" = tm.name
            WHERE tm.team = 'engineering' AND tm.active = true
            GROUP BY tm.name
        """)
        cursor.fetchall()

        # Benchmark
        start = time.time()
        cursor.execute("""
            SELECT COUNT(*) as ticket_count, tm.name
            FROM servicedesk.team_members tm
            LEFT JOIN servicedesk.tickets t ON t."TKT-Assigned To User" = tm.name
            WHERE tm.team = 'engineering' AND tm.active = true
            GROUP BY tm.name
        """)
        results = cursor.fetchall()
        elapsed_ms = (time.time() - start) * 1000
        cursor.close()

        assert len(results) == 11, "Should return stats for 11 members"
        assert elapsed_ms < 20, f"Join query took {elapsed_ms:.2f}ms, expected <20ms (target: 10-15ms)"

    def test_composite_index_usage(self, db_connection, clean_tables):
        """Verify composite indexes used in query plans."""
        from claude.tools.integrations.otc import create_team_management_schema, migrate_team_data

        # Setup
        create_team_management_schema(db_connection)
        migrate_team_data(db_connection)

        # Check idx_team_members_team_active usage
        cursor = db_connection.cursor()
        cursor.execute("""
            EXPLAIN (FORMAT JSON)
            SELECT name FROM servicedesk.team_members
            WHERE team = 'engineering' AND active = true
        """)
        plan = cursor.fetchone()[0]
        cursor.close()

        # Verify index is mentioned in plan
        plan_str = str(plan)
        assert 'idx_team_members' in plan_str.lower(), "Should use team_members index"

    def test_queue_composite_index_usage(self, db_connection, clean_tables):
        """Verify queue assignments composite index used."""
        from claude.tools.integrations.otc import create_team_management_schema, migrate_team_data

        # Setup
        create_team_management_schema(db_connection)
        migrate_team_data(db_connection)

        # Check idx_queue_assignments_queue_active usage
        cursor = db_connection.cursor()
        cursor.execute("""
            EXPLAIN (FORMAT JSON)
            SELECT team_member_id FROM servicedesk.team_queue_assignments
            WHERE queue_name = 'Cloud - Infrastructure' AND active = true
        """)
        plan = cursor.fetchone()[0]
        cursor.close()

        # Verify index is mentioned in plan
        plan_str = str(plan)
        assert 'idx_queue_assignments' in plan_str.lower(), "Should use queue_assignments index"


class TestIntegration:
    """Test Phase 5: Integration with existing system."""

    def test_team_tickets_join(self, db_connection, clean_tables):
        """Test joining team data with tickets table."""
        from claude.tools.integrations.otc import create_team_management_schema, migrate_team_data

        # Setup
        create_team_management_schema(db_connection)
        migrate_team_data(db_connection)

        # Test join query
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT
                tm.name,
                tm.email,
                COUNT(*) as ticket_count
            FROM servicedesk.team_members tm
            LEFT JOIN servicedesk.tickets t ON t."TKT-Assigned To User" = tm.name
            WHERE tm.team = 'engineering' AND tm.active = true
            GROUP BY tm.name, tm.email
            ORDER BY tm.name
        """)
        results = cursor.fetchall()
        cursor.close()

        assert len(results) == 11, "Should return all 11 team members"
        # Each result should have name, email, and ticket_count
        for row in results:
            assert len(row) == 3
            assert row[0] is not None  # name
            assert row[1] is not None  # email
            assert row[2] >= 0  # ticket_count (can be 0)

    def test_queue_workload_aggregation(self, db_connection, clean_tables):
        """Test queue workload aggregation query."""
        from claude.tools.integrations.otc import create_team_management_schema, migrate_team_data

        # Setup
        create_team_management_schema(db_connection)
        migrate_team_data(db_connection)

        # Test queue workload aggregation - just test member counts per queue
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT
                tqa.queue_name,
                COUNT(DISTINCT tm.id) as member_count
            FROM servicedesk.team_queue_assignments tqa
            JOIN servicedesk.team_members tm ON tqa.team_member_id = tm.id
            WHERE tqa.active = true
            GROUP BY tqa.queue_name
            ORDER BY tqa.queue_name
        """)
        results = cursor.fetchall()
        cursor.close()

        assert len(results) == 3, "Should return 3 queues"
        # Each queue should have 11 members
        for row in results:
            assert row[1] == 11, f"Queue {row[0]} should have 11 members, got {row[1]}"

    def test_individual_performance_query(self, db_connection, clean_tables):
        """Test individual team member performance query."""
        from claude.tools.integrations.otc import create_team_management_schema, migrate_team_data
        from claude.tools.integrations.otc.team_management import get_member_by_email, get_member_workload

        # Setup
        create_team_management_schema(db_connection)
        migrate_team_data(db_connection)

        # Get a member and their workload
        member = get_member_by_email('trevor.harte@orro.group')
        assert member is not None

        workload = get_member_workload(member['id'])

        assert workload['name'] == 'Trevor Harte'
        assert 'total_tickets' in workload
        assert 'open_tickets' in workload
        assert 'closed_tickets' in workload
        assert 'closure_rate_pct' in workload

    def test_historical_team_composition(self, db_connection, clean_tables):
        """Test historical team composition query."""
        from claude.tools.integrations.otc import create_team_management_schema, migrate_team_data
        from claude.tools.integrations.otc.team_management import add_team_member, update_team_member

        # Setup
        create_team_management_schema(db_connection)
        migrate_team_data(db_connection)

        # Add a new member
        new_member_id = add_team_member(
            name='Test Historical User',
            email='test.historical@orro.group',
            start_date='2026-01-01'
        )

        # Deactivate them
        update_team_member(new_member_id, active=False, end_date='2026-01-07')

        # Query historical composition
        cursor = db_connection.cursor()

        # Active members as of today
        cursor.execute("""
            SELECT COUNT(*) FROM servicedesk.team_members
            WHERE team = 'engineering' AND active = true
        """)
        active_count = cursor.fetchone()[0]
        assert active_count == 11, "Should have 11 active members (test user deactivated)"

        # Total members ever (including inactive)
        cursor.execute("""
            SELECT COUNT(*) FROM servicedesk.team_members
            WHERE team = 'engineering'
        """)
        total_count = cursor.fetchone()[0]
        assert total_count == 12, "Should have 12 total members (including deactivated)"

        # Members who were active at a specific date (2026-01-01)
        cursor.execute("""
            SELECT COUNT(*) FROM servicedesk.team_members
            WHERE team = 'engineering'
            AND start_date <= '2026-01-01'
            AND (end_date IS NULL OR end_date >= '2026-01-01')
        """)
        historical_count = cursor.fetchone()[0]
        assert historical_count >= 11, "Should have at least 11 members active on 2026-01-01"

        cursor.close()


class TestHistoryTracking:
    """Test Phase 6: Audit trail functionality."""

    def test_add_member_creates_history(self, db_connection, clean_tables):
        """Verify adding member creates history entry."""
        from claude.tools.integrations.otc import create_team_management_schema
        from claude.tools.integrations.otc.team_management import add_team_member

        # Setup
        create_team_management_schema(db_connection)

        # Add member
        member_id = add_team_member(
            name='Test History User',
            email='test.history@orro.group',
            changed_by='test_system'
        )

        # Verify history entry
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT change_type, changed_by, new_value
            FROM servicedesk.team_member_history
            WHERE team_member_id = %s
        """, (member_id,))
        history = cursor.fetchone()
        cursor.close()

        assert history is not None, "Should have history entry"
        assert history[0] == 'created', "Change type should be 'created'"
        assert history[1] == 'test_system', "Changed by should be 'test_system'"
        assert 'Test History User' in history[2], "New value should contain member name"

    def test_update_member_creates_history(self, db_connection, clean_tables):
        """Verify updating member creates history entry."""
        from claude.tools.integrations.otc import create_team_management_schema
        from claude.tools.integrations.otc.team_management import add_team_member, update_team_member

        # Setup
        create_team_management_schema(db_connection)

        # Add member
        member_id = add_team_member(
            name='Original Name',
            email='test.update@orro.group'
        )

        # Update member
        update_team_member(
            member_id,
            name='Updated Name',
            notes='Test update',
            changed_by='admin'
        )

        # Verify history entries (should have created + updated)
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT change_type, field_changed, old_value, new_value
            FROM servicedesk.team_member_history
            WHERE team_member_id = %s AND change_type = 'updated'
            ORDER BY changed_at
        """, (member_id,))
        history_entries = cursor.fetchall()
        cursor.close()

        assert len(history_entries) >= 2, "Should have at least 2 update history entries (name + notes)"

        # Find the name change entry
        name_entry = [e for e in history_entries if e[1] == 'name']
        assert len(name_entry) > 0, "Should have history entry for name change"
        assert name_entry[0][2] == 'Original Name', "Old value should be 'Original Name'"
        assert name_entry[0][3] == 'Updated Name', "New value should be 'Updated Name'"

    def test_deactivate_member_creates_history(self, db_connection, clean_tables):
        """Verify deactivating member creates history entry."""
        from claude.tools.integrations.otc import create_team_management_schema
        from claude.tools.integrations.otc.team_management import add_team_member, update_team_member

        # Setup
        create_team_management_schema(db_connection)

        # Add member
        member_id = add_team_member(
            name='Test Deactivate User',
            email='test.deactivate@orro.group'
        )

        # Deactivate member
        update_team_member(
            member_id,
            active=False,
            end_date='2026-01-07',
            changed_by='hr_system'
        )

        # Verify history entries for deactivation
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT field_changed, old_value, new_value, changed_by
            FROM servicedesk.team_member_history
            WHERE team_member_id = %s AND change_type = 'updated'
        """, (member_id,))
        history_entries = cursor.fetchall()
        cursor.close()

        assert len(history_entries) >= 2, "Should have history entries for active + end_date changes"

        # Find active field change
        active_entry = [e for e in history_entries if e[0] == 'active']
        assert len(active_entry) > 0, "Should have history entry for active field"
        assert active_entry[0][1] == 'True', "Old value should be True"
        assert active_entry[0][2] == 'False', "New value should be False"
        assert active_entry[0][3] == 'hr_system', "Changed by should be 'hr_system'"

    def test_history_retention_policy(self, db_connection, clean_tables):
        """Verify 7-year retention policy documented."""
        from claude.tools.integrations.otc import create_team_management_schema

        # Setup
        create_team_management_schema(db_connection)

        # Check table comment
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT obj_description('servicedesk.team_member_history'::regclass)
        """)
        comment = cursor.fetchone()[0]
        cursor.close()

        assert comment is not None, "Table should have comment"
        assert '7 year' in comment.lower(), "Comment should mention 7-year retention"
        assert 'audit trail' in comment.lower(), "Comment should mention audit trail"
