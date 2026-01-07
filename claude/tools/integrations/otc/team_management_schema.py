"""
Team Management Database Schema Creation.

Creates 3 tables for managing engineering team membership and queue assignments:
- servicedesk.team_members: Team roster with organizational hierarchy
- servicedesk.team_queue_assignments: Queue assignments over time
- servicedesk.team_member_history: Audit trail for all changes

Includes Data Analyst-approved enhancements:
1. Composite index: idx_team_members_team_active (2-3x faster roster queries)
2. Composite index: idx_queue_assignments_queue_active (faster queue lookups)
3. Retention policy: 7-year history retention documented
"""

import psycopg2
import json
import os
from psycopg2.extras import execute_batch


def create_team_management_schema(conn):
    """
    Create team management tables in servicedesk schema.

    Args:
        conn: psycopg2 connection object

    Returns:
        None

    Raises:
        psycopg2.Error: If schema creation fails
    """
    cursor = conn.cursor()

    try:
        # Table 1: team_members
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS servicedesk.team_members (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                organization VARCHAR(100) DEFAULT 'Orro',
                team VARCHAR(100) DEFAULT 'engineering',
                manager_id INTEGER REFERENCES servicedesk.team_members(id),
                active BOOLEAN DEFAULT true,
                start_date DATE DEFAULT CURRENT_DATE,
                end_date DATE,
                notes TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),

                -- Constraints
                CONSTRAINT valid_date_range CHECK (end_date IS NULL OR end_date >= start_date),
                CONSTRAINT active_requires_no_end_date CHECK (active = false OR end_date IS NULL)
            )
        """)

        # Primary indexes for team_members
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_team_members_active
            ON servicedesk.team_members(active)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_team_members_team
            ON servicedesk.team_members(team)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_team_members_email
            ON servicedesk.team_members(email)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_team_members_name
            ON servicedesk.team_members(name)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_team_members_manager
            ON servicedesk.team_members(manager_id)
        """)

        # ⭐ REQUIRED ENHANCEMENT 1: Composite index for common filter pattern
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_team_members_team_active
            ON servicedesk.team_members(team, active)
        """)

        # Table comments for team_members
        cursor.execute("""
            COMMENT ON TABLE servicedesk.team_members IS
            'Engineering team roster with organizational hierarchy'
        """)

        cursor.execute("""
            COMMENT ON COLUMN servicedesk.team_members.name IS
            'Full name as it appears in TKT-Assigned To User field'
        """)

        cursor.execute("""
            COMMENT ON COLUMN servicedesk.team_members.manager_id IS
            'Self-referencing FK for organizational hierarchy'
        """)

        cursor.execute("""
            COMMENT ON COLUMN servicedesk.team_members.active IS
            'false = left team, true = current member'
        """)

        # Table 2: team_queue_assignments
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS servicedesk.team_queue_assignments (
                id SERIAL PRIMARY KEY,
                team_member_id INTEGER NOT NULL REFERENCES servicedesk.team_members(id) ON DELETE CASCADE,
                queue_name VARCHAR(255) NOT NULL,
                assigned_date DATE DEFAULT CURRENT_DATE,
                removed_date DATE,
                active BOOLEAN DEFAULT true,
                assignment_type VARCHAR(50) DEFAULT 'primary',
                notes TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),

                -- Constraints
                CONSTRAINT unique_active_assignment UNIQUE(team_member_id, queue_name, assigned_date),
                CONSTRAINT valid_assignment_dates CHECK (removed_date IS NULL OR removed_date >= assigned_date),
                CONSTRAINT active_requires_no_removal CHECK (active = false OR removed_date IS NULL)
            )
        """)

        # Primary indexes for team_queue_assignments
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_queue_assignments_member
            ON servicedesk.team_queue_assignments(team_member_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_queue_assignments_queue
            ON servicedesk.team_queue_assignments(queue_name)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_queue_assignments_active
            ON servicedesk.team_queue_assignments(active)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_queue_assignments_type
            ON servicedesk.team_queue_assignments(assignment_type)
        """)

        # ⭐ REQUIRED ENHANCEMENT 2: Composite index for queue lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_queue_assignments_queue_active
            ON servicedesk.team_queue_assignments(queue_name, active)
        """)

        # Table comments for team_queue_assignments
        cursor.execute("""
            COMMENT ON TABLE servicedesk.team_queue_assignments IS
            'Team member assignments to support queues over time'
        """)

        cursor.execute("""
            COMMENT ON COLUMN servicedesk.team_queue_assignments.queue_name IS
            'References TKT-Team field value'
        """)

        cursor.execute("""
            COMMENT ON COLUMN servicedesk.team_queue_assignments.assignment_type IS
            'primary (main responsibility), backup (secondary), rotation (scheduled)'
        """)

        # Table 3: team_member_history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS servicedesk.team_member_history (
                id SERIAL PRIMARY KEY,
                team_member_id INTEGER NOT NULL REFERENCES servicedesk.team_members(id) ON DELETE CASCADE,
                change_type VARCHAR(50) NOT NULL,
                field_changed VARCHAR(100),
                old_value TEXT,
                new_value TEXT,
                changed_by VARCHAR(255),
                changed_at TIMESTAMP DEFAULT NOW(),
                change_reason TEXT
            )
        """)

        # Indexes for team_member_history
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_history_member
            ON servicedesk.team_member_history(team_member_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_history_change_type
            ON servicedesk.team_member_history(change_type)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_history_changed_at
            ON servicedesk.team_member_history(changed_at)
        """)

        # ⭐ REQUIRED ENHANCEMENT 3: Retention policy documentation
        cursor.execute("""
            COMMENT ON TABLE servicedesk.team_member_history IS
            'Audit trail for all team roster changes - retain 7 years per compliance policy'
        """)

        conn.commit()

    except Exception as e:
        conn.rollback()
        raise

    finally:
        cursor.close()


def drop_team_management_schema(conn):
    """
    Drop team management tables (rollback script).

    Args:
        conn: psycopg2 connection object

    Returns:
        None
    """
    cursor = conn.cursor()

    try:
        # Drop in reverse order to handle dependencies
        cursor.execute("DROP TABLE IF EXISTS servicedesk.team_member_history CASCADE")
        cursor.execute("DROP TABLE IF EXISTS servicedesk.team_queue_assignments CASCADE")
        cursor.execute("DROP TABLE IF EXISTS servicedesk.team_members CASCADE")

        conn.commit()

    except Exception as e:
        conn.rollback()
        raise

    finally:
        cursor.close()


def migrate_team_data(conn):
    """
    Migrate team data from user_preferences.json to database.

    Migrates:
    - 11 engineering team members
    - 33 queue assignments (11 members × 3 queues)

    Idempotent: Checks for existing data before inserting.

    Args:
        conn: psycopg2 connection object

    Returns:
        tuple: (members_inserted, assignments_inserted)

    Raises:
        FileNotFoundError: If user_preferences.json not found
        psycopg2.Error: If migration fails
    """
    cursor = conn.cursor()
    members_inserted = 0
    assignments_inserted = 0

    try:
        # Load user preferences JSON
        user_prefs_path = os.path.join(
            os.path.dirname(__file__),
            '../../../data/user_preferences.json'
        )

        with open(user_prefs_path, 'r') as f:
            prefs = json.load(f)

        # Extract team data
        eng_team = prefs['analysis_preferences']['otc_servicedesk']['teams']['engineering']
        members = eng_team['members']
        queues = eng_team['team_assignments']

        # Insert team members (idempotent - check for existing)
        for member in members:
            cursor.execute("""
                SELECT id FROM servicedesk.team_members
                WHERE email = %s
            """, (member['email'],))

            if cursor.fetchone() is None:
                cursor.execute("""
                    INSERT INTO servicedesk.team_members (name, email, organization, team, active, start_date)
                    VALUES (%s, %s, 'Orro', 'engineering', true, '2025-01-01')
                """, (member['name'], member['email']))
                members_inserted += 1

        conn.commit()

        # Insert queue assignments (idempotent)
        for member in members:
            # Get member ID
            cursor.execute("""
                SELECT id FROM servicedesk.team_members WHERE email = %s
            """, (member['email'],))
            member_id = cursor.fetchone()[0]

            # Insert assignments for each queue
            for queue_name in queues:
                cursor.execute("""
                    SELECT id FROM servicedesk.team_queue_assignments
                    WHERE team_member_id = %s AND queue_name = %s AND assigned_date = '2025-01-01'
                """, (member_id, queue_name))

                if cursor.fetchone() is None:
                    cursor.execute("""
                        INSERT INTO servicedesk.team_queue_assignments
                        (team_member_id, queue_name, assigned_date, active, assignment_type)
                        VALUES (%s, %s, '2025-01-01', true, 'primary')
                    """, (member_id, queue_name))
                    assignments_inserted += 1

        conn.commit()
        return (members_inserted, assignments_inserted)

    except Exception as e:
        conn.rollback()
        raise

    finally:
        cursor.close()
