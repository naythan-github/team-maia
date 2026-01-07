"""
OTC Team Management Helper Functions.

Provides Python interface to team_members, team_queue_assignments, and
team_member_history tables with JSON fallback support.

Usage:
    from claude.tools.integrations.otc.team_management import get_team_members

    # Get active engineering team
    members = get_team_members()

    # Add new member
    member_id = add_team_member('John Doe', 'john.doe@orro.group')

    # Update with history tracking
    update_team_member(member_id, name='John Smith', changed_by='admin')
"""

from typing import List, Dict, Optional
import psycopg2
from datetime import datetime, date
import json
import os


def get_connection():
    """
    Get PostgreSQL database connection.

    Returns:
        psycopg2.connection: Database connection object

    Raises:
        psycopg2.Error: If connection fails
    """
    return psycopg2.connect(
        host='localhost',
        port=5432,
        database='servicedesk',
        user='servicedesk_user',
        password='ServiceDesk2025!SecurePass'
    )


def get_team_members(
    team: str = 'engineering',
    active_only: bool = True,
    fallback_to_json: bool = True
) -> List[Dict]:
    """
    Get team members from database with JSON fallback.

    Args:
        team: Team name (default: 'engineering')
        active_only: Filter to active members only (default: True)
        fallback_to_json: Fall back to JSON if DB unavailable (default: True)

    Returns:
        List of team member dicts with keys: id, name, email, organization, team, active, start_date

    Raises:
        Exception: If DB unavailable and fallback_to_json=False
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        if active_only:
            cursor.execute("""
                SELECT id, name, email, organization, team, active, start_date
                FROM servicedesk.team_members
                WHERE team = %s AND active = true
                ORDER BY name
            """, (team,))
        else:
            cursor.execute("""
                SELECT id, name, email, organization, team, active, start_date
                FROM servicedesk.team_members
                WHERE team = %s
                ORDER BY name
            """, (team,))

        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        return [
            {
                'id': row[0],
                'name': row[1],
                'email': row[2],
                'organization': row[3],
                'team': row[4],
                'active': row[5],
                'start_date': row[6]
            }
            for row in rows
        ]

    except Exception as e:
        if fallback_to_json:
            # Load from JSON
            user_prefs_path = os.path.join(
                os.path.dirname(__file__),
                '../../../data/user_preferences.json'
            )
            with open(user_prefs_path, 'r') as f:
                prefs = json.load(f)

            members = prefs['analysis_preferences']['otc_servicedesk']['teams'][team]['members']
            return members
        else:
            raise


def get_team_queues(team: str = 'engineering', active_only: bool = True) -> List[str]:
    """
    Get queue assignments for team.

    Args:
        team: Team name (default: 'engineering')
        active_only: Filter to active assignments only (default: True)

    Returns:
        List of queue names (TKT-Team values)
    """
    conn = get_connection()
    cursor = conn.cursor()

    if active_only:
        cursor.execute("""
            SELECT DISTINCT tqa.queue_name
            FROM servicedesk.team_queue_assignments tqa
            JOIN servicedesk.team_members tm ON tqa.team_member_id = tm.id
            WHERE tm.team = %s AND tqa.active = true
            ORDER BY tqa.queue_name
        """, (team,))
    else:
        cursor.execute("""
            SELECT DISTINCT tqa.queue_name
            FROM servicedesk.team_queue_assignments tqa
            JOIN servicedesk.team_members tm ON tqa.team_member_id = tm.id
            WHERE tm.team = %s
            ORDER BY tqa.queue_name
        """, (team,))

    queues = [row[0] for row in cursor.fetchall()]

    cursor.close()
    conn.close()

    return queues


def get_member_by_email(email: str) -> Optional[Dict]:
    """
    Get team member by email address.

    Args:
        email: Email address

    Returns:
        Team member dict or None if not found
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, email, organization, team, active, start_date, end_date, notes
        FROM servicedesk.team_members
        WHERE email = %s
    """, (email,))

    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if row is None:
        return None

    return {
        'id': row[0],
        'name': row[1],
        'email': row[2],
        'organization': row[3],
        'team': row[4],
        'active': row[5],
        'start_date': row[6],
        'end_date': row[7],
        'notes': row[8]
    }


def get_member_workload(member_id: int) -> Dict:
    """
    Get workload statistics for team member.

    Args:
        member_id: Team member ID

    Returns:
        Dict with keys: name, total_tickets, open_tickets, closed_tickets, closure_rate_pct
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Get member name
    cursor.execute("""
        SELECT name FROM servicedesk.team_members WHERE id = %s
    """, (member_id,))
    member_name = cursor.fetchone()[0]

    # Get ticket statistics
    cursor.execute("""
        SELECT
            COUNT(*) as total_tickets,
            COUNT(*) FILTER (WHERE "TKT-Status" IN ('Open', 'In Progress', 'Pending')) as open_tickets,
            COUNT(*) FILTER (WHERE "TKT-Status" = 'Closed') as closed_tickets
        FROM servicedesk.tickets
        WHERE "TKT-Assigned To User" = %s
    """, (member_name,))

    row = cursor.fetchone()
    cursor.close()
    conn.close()

    total = row[0] or 0
    open_count = row[1] or 0
    closed = row[2] or 0

    closure_rate = (closed / total * 100) if total > 0 else 0.0

    return {
        'name': member_name,
        'total_tickets': total,
        'open_tickets': open_count,
        'closed_tickets': closed,
        'closure_rate_pct': round(closure_rate, 2)
    }


def _record_history(
    conn,
    member_id: int,
    change_type: str,
    field_changed: Optional[str] = None,
    old_value: Optional[str] = None,
    new_value: Optional[str] = None,
    changed_by: str = 'system',
    reason: Optional[str] = None
):
    """
    Internal helper for history tracking.

    Args:
        conn: Database connection
        member_id: Team member ID
        change_type: 'created', 'updated', 'deactivated', 'reactivated'
        field_changed: Field name that changed
        old_value: Previous value
        new_value: New value
        changed_by: Who made the change
        reason: Optional reason for change
    """
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO servicedesk.team_member_history
        (team_member_id, change_type, field_changed, old_value, new_value, changed_by, change_reason)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        member_id,
        change_type,
        field_changed,
        str(old_value) if old_value is not None else None,
        str(new_value) if new_value is not None else None,
        changed_by,
        reason
    ))

    cursor.close()


def add_team_member(
    name: str,
    email: str,
    organization: str = 'Orro',
    team: str = 'engineering',
    start_date: Optional[date] = None,
    notes: Optional[str] = None,
    changed_by: str = 'system'
) -> int:
    """
    Add new team member with history tracking.

    Args:
        name: Full name (as appears in TKT-Assigned To User)
        email: Email address (must be unique)
        organization: Organization name (default: 'Orro')
        team: Team name (default: 'engineering')
        start_date: Start date (default: today)
        notes: Optional notes
        changed_by: Who is making the change (default: 'system')

    Returns:
        New team member ID

    Raises:
        psycopg2.IntegrityError: If email already exists
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Insert member
        if start_date is None:
            start_date = datetime.now().date()

        cursor.execute("""
            INSERT INTO servicedesk.team_members
            (name, email, organization, team, start_date, notes, active)
            VALUES (%s, %s, %s, %s, %s, %s, true)
            RETURNING id
        """, (name, email, organization, team, start_date, notes))

        member_id = cursor.fetchone()[0]

        # Record history
        _record_history(
            conn,
            member_id,
            'created',
            field_changed=None,
            old_value=None,
            new_value=f"name={name}, email={email}, team={team}",
            changed_by=changed_by,
            reason='New team member added'
        )

        conn.commit()
        cursor.close()
        conn.close()

        return member_id

    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        raise


def update_team_member(
    member_id: int,
    changed_by: str = 'system',
    **updates
) -> bool:
    """
    Update team member with history tracking.

    Args:
        member_id: Team member ID
        changed_by: Who is making the change (default: 'system')
        **updates: Fields to update (name, email, organization, team, active, end_date, notes)

    Returns:
        True if successful

    Raises:
        ValueError: If member_id not found
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Get current values
        cursor.execute("""
            SELECT name, email, organization, team, active, end_date, notes
            FROM servicedesk.team_members
            WHERE id = %s
        """, (member_id,))

        row = cursor.fetchone()
        if row is None:
            raise ValueError(f"Team member {member_id} not found")

        current_values = {
            'name': row[0],
            'email': row[1],
            'organization': row[2],
            'team': row[3],
            'active': row[4],
            'end_date': row[5],
            'notes': row[6]
        }

        # Build UPDATE query
        set_clauses = []
        params = []

        for field, new_value in updates.items():
            if field in current_values:
                old_value = current_values[field]

                # Only update if value changed
                if old_value != new_value:
                    set_clauses.append(f"{field} = %s")
                    params.append(new_value)

                    # Record history for each changed field
                    _record_history(
                        conn,
                        member_id,
                        'updated',
                        field_changed=field,
                        old_value=old_value,
                        new_value=new_value,
                        changed_by=changed_by
                    )

        if set_clauses:
            # Add updated_at
            set_clauses.append("updated_at = NOW()")

            # Execute update
            params.append(member_id)
            query = f"UPDATE servicedesk.team_members SET {', '.join(set_clauses)} WHERE id = %s"
            cursor.execute(query, params)

        conn.commit()
        cursor.close()
        conn.close()

        return True

    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        raise


def assign_queue(
    member_id: int,
    queue_name: str,
    assigned_date: Optional[date] = None,
    assignment_type: str = 'primary',
    notes: Optional[str] = None
) -> int:
    """
    Assign team member to queue.

    Args:
        member_id: Team member ID
        queue_name: Queue name (TKT-Team value)
        assigned_date: Assignment date (default: today)
        assignment_type: 'primary', 'backup', or 'rotation' (default: 'primary')
        notes: Optional notes

    Returns:
        Assignment ID
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        if assigned_date is None:
            assigned_date = datetime.now().date()

        cursor.execute("""
            INSERT INTO servicedesk.team_queue_assignments
            (team_member_id, queue_name, assigned_date, assignment_type, notes, active)
            VALUES (%s, %s, %s, %s, %s, true)
            RETURNING id
        """, (member_id, queue_name, assigned_date, assignment_type, notes))

        assignment_id = cursor.fetchone()[0]

        conn.commit()
        cursor.close()
        conn.close()

        return assignment_id

    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        raise


def remove_queue_assignment(assignment_id: int, removed_date: Optional[date] = None) -> bool:
    """
    Remove queue assignment (soft delete).

    Args:
        assignment_id: Assignment ID
        removed_date: Removal date (default: today)

    Returns:
        True if successful
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        if removed_date is None:
            removed_date = datetime.now().date()

        cursor.execute("""
            UPDATE servicedesk.team_queue_assignments
            SET active = false, removed_date = %s, updated_at = NOW()
            WHERE id = %s
        """, (removed_date, assignment_id))

        conn.commit()
        cursor.close()
        conn.close()

        return True

    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        raise


def export_teams_to_json() -> None:
    """
    Export database team data to JSON for fallback freshness.

    Updates user_preferences.json with current team roster from database.
    This provides unidirectional sync (DB → JSON) as approved by Data Analyst.

    Should be run periodically (e.g., daily cron) to keep JSON fallback fresh.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Get all active engineering team members
        cursor.execute("""
            SELECT name, email
            FROM servicedesk.team_members
            WHERE team = 'engineering' AND active = true
            ORDER BY name
        """)

        members = [{'name': row[0], 'email': row[1]} for row in cursor.fetchall()]

        # Get all active queues
        cursor.execute("""
            SELECT DISTINCT queue_name
            FROM servicedesk.team_queue_assignments tqa
            JOIN servicedesk.team_members tm ON tqa.team_member_id = tm.id
            WHERE tm.team = 'engineering' AND tqa.active = true
            ORDER BY queue_name
        """)

        queues = [row[0] for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        # Update JSON file
        user_prefs_path = os.path.join(
            os.path.dirname(__file__),
            '../../../data/user_preferences.json'
        )

        with open(user_prefs_path, 'r') as f:
            prefs = json.load(f)

        # Update team data
        prefs['analysis_preferences']['otc_servicedesk']['teams']['engineering']['members'] = members
        prefs['analysis_preferences']['otc_servicedesk']['teams']['engineering']['team_assignments'] = queues

        # Write back
        with open(user_prefs_path, 'w') as f:
            json.dump(prefs, f, indent=2)

    except Exception as e:
        if 'conn' in locals():
            conn.close()
        raise
