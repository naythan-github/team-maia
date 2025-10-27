#!/usr/bin/env python3
"""
Maia Project Registry - CLI Tool
Project: PROJ-REG-001
Purpose: Production-grade project backlog management
SRE Design: ACID transactions, input validation, error handling

Usage:
    project_registry.py add --id ID --name "Name" --priority high
    project_registry.py list --status planned
    project_registry.py show ID
    project_registry.py start ID
    project_registry.py complete ID --actual-hours 38
    project_registry.py backlog
    project_registry.py stats
    project_registry.py export --format markdown
"""

import sqlite3
import json
import argparse
import sys
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

# Constants
DB_PATH = "claude/data/project_registry.db"
MAIA_ROOT = os.environ.get("MAIA_ROOT", os.path.expanduser("~/git/maia"))

# Valid enum values
VALID_STATUSES = ["planned", "active", "blocked", "completed", "archived"]
VALID_PRIORITIES = ["critical", "high", "medium", "low"]
VALID_IMPACTS = ["high", "medium", "low"]
VALID_DELIVERABLE_TYPES = ["tool", "agent", "documentation", "infrastructure", "database", "workflow", "config"]
VALID_DEPENDENCY_TYPES = ["blocks", "optional", "enhances"]


class ProjectRegistry:
    """Main project registry database interface."""

    def __init__(self, db_path: str = DB_PATH):
        """Initialize database connection."""
        # Convert to absolute path if relative
        if not os.path.isabs(db_path):
            db_path = os.path.join(MAIA_ROOT, db_path)

        self.db_path = db_path
        self.conn = None
        self._connect()

    def _connect(self):
        """Establish database connection with proper configuration."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # Enable dict-like access

            # Enable foreign keys
            self.conn.execute("PRAGMA foreign_keys = ON")

            # Verify database exists and is valid
            self.conn.execute("SELECT COUNT(*) FROM projects")

        except sqlite3.Error as e:
            print(f"❌ Database error: {e}", file=sys.stderr)
            print(f"   Database path: {self.db_path}", file=sys.stderr)
            sys.exit(1)

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close connection."""
        if self.conn:
            self.conn.close()

    # =========================================================================
    # CRUD Operations
    # =========================================================================

    def add_project(
        self,
        project_id: str,
        name: str,
        status: str = "planned",
        priority: str = "medium",
        effort_hours: Optional[int] = None,
        impact: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        description: Optional[str] = None,
        notes: Optional[str] = None,
        project_plan_path: Optional[str] = None,
        confluence_url: Optional[str] = None,
        github_issue_url: Optional[str] = None
    ) -> bool:
        """Add new project to registry."""

        # Validate inputs
        if not self._validate_project_id(project_id):
            return False

        if status not in VALID_STATUSES:
            print(f"❌ Invalid status: {status}. Must be one of: {', '.join(VALID_STATUSES)}", file=sys.stderr)
            return False

        if priority not in VALID_PRIORITIES:
            print(f"❌ Invalid priority: {priority}. Must be one of: {', '.join(VALID_PRIORITIES)}", file=sys.stderr)
            return False

        if impact and impact not in VALID_IMPACTS:
            print(f"❌ Invalid impact: {impact}. Must be one of: {', '.join(VALID_IMPACTS)}", file=sys.stderr)
            return False

        # Check if project already exists
        existing = self.conn.execute("SELECT id FROM projects WHERE id = ?", (project_id,)).fetchone()
        if existing:
            print(f"❌ Project {project_id} already exists", file=sys.stderr)
            return False

        # Convert tags list to JSON
        tags_json = json.dumps(tags) if tags else None

        try:
            self.conn.execute("""
                INSERT INTO projects (
                    id, name, status, priority, effort_hours, impact, category, tags,
                    description, notes, project_plan_path, confluence_url, github_issue_url,
                    created_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                project_id, name, status, priority, effort_hours, impact, category, tags_json,
                description, notes, project_plan_path, confluence_url, github_issue_url
            ))
            self.conn.commit()

            print(f"✅ Project {project_id} added successfully")
            return True

        except sqlite3.Error as e:
            print(f"❌ Database error: {e}", file=sys.stderr)
            self.conn.rollback()
            return False

    def list_projects(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List projects with optional filters."""

        query = "SELECT * FROM projects WHERE 1=1"
        params = []

        if status:
            query += " AND status = ?"
            params.append(status)

        if priority:
            query += " AND priority = ?"
            params.append(priority)

        if category:
            query += " AND category LIKE ?"
            params.append(f"%{category}%")

        # Sort by priority, then by created date
        query += """ ORDER BY
            CASE priority
                WHEN 'critical' THEN 1
                WHEN 'high' THEN 2
                WHEN 'medium' THEN 3
                WHEN 'low' THEN 4
            END,
            created_date DESC
        """

        try:
            cursor = self.conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"❌ Database error: {e}", file=sys.stderr)
            return []

    def show_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Show detailed project information."""

        try:
            # Get project details
            cursor = self.conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
            project = cursor.fetchone()

            if not project:
                print(f"❌ Project {project_id} not found", file=sys.stderr)
                return None

            project_dict = dict(project)

            # Get deliverables
            cursor = self.conn.execute(
                "SELECT * FROM deliverables WHERE project_id = ? ORDER BY status, name",
                (project_id,)
            )
            project_dict['deliverables'] = [dict(row) for row in cursor.fetchall()]

            # Get dependencies
            cursor = self.conn.execute("""
                SELECT d.*, p.name as depends_on_name
                FROM dependencies d
                JOIN projects p ON d.depends_on_project_id = p.id
                WHERE d.project_id = ?
            """, (project_id,))
            project_dict['dependencies'] = [dict(row) for row in cursor.fetchall()]

            # Get audit history (last 10 updates)
            cursor = self.conn.execute("""
                SELECT * FROM project_updates
                WHERE project_id = ?
                ORDER BY timestamp DESC
                LIMIT 10
            """, (project_id,))
            project_dict['updates'] = [dict(row) for row in cursor.fetchall()]

            return project_dict

        except sqlite3.Error as e:
            print(f"❌ Database error: {e}", file=sys.stderr)
            return None

    def update_project(
        self,
        project_id: str,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        effort_hours: Optional[int] = None,
        impact: Optional[str] = None,
        notes: Optional[str] = None
    ) -> bool:
        """Update project fields."""

        # Check if project exists
        existing = self.conn.execute("SELECT id FROM projects WHERE id = ?", (project_id,)).fetchone()
        if not existing:
            print(f"❌ Project {project_id} not found", file=sys.stderr)
            return False

        # Validate inputs
        if status and status not in VALID_STATUSES:
            print(f"❌ Invalid status: {status}", file=sys.stderr)
            return False

        if priority and priority not in VALID_PRIORITIES:
            print(f"❌ Invalid priority: {priority}", file=sys.stderr)
            return False

        if impact and impact not in VALID_IMPACTS:
            print(f"❌ Invalid impact: {impact}", file=sys.stderr)
            return False

        try:
            # Build dynamic update query
            updates = []
            params = []

            if status:
                updates.append("status = ?")
                params.append(status)

            if priority:
                updates.append("priority = ?")
                params.append(priority)

            if effort_hours is not None:
                updates.append("effort_hours = ?")
                params.append(effort_hours)

            if impact:
                updates.append("impact = ?")
                params.append(impact)

            if notes:
                updates.append("notes = ?")
                params.append(notes)

            if not updates:
                print("❌ No fields to update", file=sys.stderr)
                return False

            params.append(project_id)
            query = f"UPDATE projects SET {', '.join(updates)} WHERE id = ?"

            self.conn.execute(query, params)
            self.conn.commit()

            print(f"✅ Project {project_id} updated successfully")
            return True

        except sqlite3.Error as e:
            print(f"❌ Database error: {e}", file=sys.stderr)
            self.conn.rollback()
            return False

    def start_project(self, project_id: str) -> bool:
        """Start a project (set status to active)."""
        return self.update_project(project_id, status="active")

    def complete_project(
        self,
        project_id: str,
        actual_hours: Optional[int] = None,
        notes: Optional[str] = None
    ) -> bool:
        """Complete a project."""

        try:
            # Update status to completed
            query = "UPDATE projects SET status = 'completed'"
            params = []

            if actual_hours is not None:
                query += ", actual_hours = ?"
                params.append(actual_hours)

            if notes:
                query += ", notes = ?"
                params.append(notes)

            query += " WHERE id = ?"
            params.append(project_id)

            self.conn.execute(query, params)
            self.conn.commit()

            print(f"✅ Project {project_id} marked as completed")

            # Show variance if both effort and actual hours provided
            if actual_hours is not None:
                project = self.show_project(project_id)
                if project and project.get('effort_hours'):
                    variance = actual_hours - project['effort_hours']
                    variance_pct = (variance / project['effort_hours']) * 100

                    if variance < 0:
                        print(f"   Under estimate by {abs(variance)}h ({abs(variance_pct):.1f}%)")
                    elif variance > 0:
                        print(f"   Over estimate by {variance}h ({variance_pct:.1f}%)")
                    else:
                        print(f"   Exactly on estimate!")

            return True

        except sqlite3.Error as e:
            print(f"❌ Database error: {e}", file=sys.stderr)
            self.conn.rollback()
            return False

    # =========================================================================
    # Dependency Management
    # =========================================================================

    def add_dependency(
        self,
        project_id: str,
        depends_on_project_id: str,
        dependency_type: str = "blocks",
        notes: Optional[str] = None
    ) -> bool:
        """Add project dependency."""

        # Validate inputs
        if dependency_type not in VALID_DEPENDENCY_TYPES:
            print(f"❌ Invalid dependency type: {dependency_type}", file=sys.stderr)
            return False

        # Check if projects exist
        for pid in [project_id, depends_on_project_id]:
            existing = self.conn.execute("SELECT id FROM projects WHERE id = ?", (pid,)).fetchone()
            if not existing:
                print(f"❌ Project {pid} not found", file=sys.stderr)
                return False

        # Check for circular dependency (simple check - would need graph traversal for full check)
        if project_id == depends_on_project_id:
            print(f"❌ Cannot create circular dependency (project depends on itself)", file=sys.stderr)
            return False

        try:
            self.conn.execute("""
                INSERT INTO dependencies (project_id, depends_on_project_id, dependency_type, notes)
                VALUES (?, ?, ?, ?)
            """, (project_id, depends_on_project_id, dependency_type, notes))
            self.conn.commit()

            print(f"✅ Dependency added: {project_id} depends on {depends_on_project_id} ({dependency_type})")
            return True

        except sqlite3.IntegrityError:
            print(f"❌ Dependency already exists", file=sys.stderr)
            return False
        except sqlite3.Error as e:
            print(f"❌ Database error: {e}", file=sys.stderr)
            self.conn.rollback()
            return False

    # =========================================================================
    # Reporting & Analytics
    # =========================================================================

    def get_backlog(self) -> List[Dict[str, Any]]:
        """Get prioritized backlog view."""
        try:
            cursor = self.conn.execute("SELECT * FROM v_backlog")
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"❌ Database error: {e}", file=sys.stderr)
            return []

    def get_stats(self) -> Dict[str, Any]:
        """Get project statistics."""

        try:
            stats = {}

            # Project counts by status
            cursor = self.conn.execute("""
                SELECT status, COUNT(*) as count, SUM(effort_hours) as total_effort
                FROM projects
                GROUP BY status
            """)
            stats['by_status'] = {row['status']: dict(row) for row in cursor.fetchall()}

            # Project counts by priority
            cursor = self.conn.execute("""
                SELECT priority, COUNT(*) as count, SUM(effort_hours) as total_effort
                FROM projects
                GROUP BY priority
            """)
            stats['by_priority'] = {row['priority']: dict(row) for row in cursor.fetchall()}

            # Project counts by category
            cursor = self.conn.execute("""
                SELECT category, COUNT(*) as count, SUM(effort_hours) as total_effort
                FROM projects
                WHERE category IS NOT NULL
                GROUP BY category
                ORDER BY count DESC
            """)
            stats['by_category'] = [dict(row) for row in cursor.fetchall()]

            # Overall stats
            cursor = self.conn.execute("""
                SELECT
                    COUNT(*) as total_projects,
                    SUM(effort_hours) as total_effort,
                    AVG(effort_hours) as avg_effort,
                    MAX(effort_hours) as max_effort,
                    MIN(effort_hours) as min_effort
                FROM projects
                WHERE effort_hours IS NOT NULL
            """)
            stats['overall'] = dict(cursor.fetchone())

            # Velocity (completed in last 30 days)
            cursor = self.conn.execute("""
                SELECT
                    COUNT(*) as completed_count,
                    SUM(actual_hours) as actual_hours,
                    SUM(effort_hours) as estimated_hours,
                    AVG(CAST(julianday(completed_date) - julianday(started_date) AS INTEGER)) as avg_days
                FROM projects
                WHERE status = 'completed'
                AND completed_date > datetime('now', '-30 days')
            """)
            stats['velocity'] = dict(cursor.fetchone())

            return stats

        except sqlite3.Error as e:
            print(f"❌ Database error: {e}", file=sys.stderr)
            return {}

    def export_markdown(self, status_filter: Optional[str] = None) -> str:
        """Export projects to markdown format."""

        projects = self.list_projects(status=status_filter)
        stats = self.get_stats()

        # Group projects by priority
        by_priority = {'critical': [], 'high': [], 'medium': [], 'low': []}
        for project in projects:
            by_priority[project['priority']].append(project)

        # Build markdown
        lines = []
        lines.append("# Maia Project Backlog")
        lines.append("")
        lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Total Projects**: {stats['overall']['total_projects']}")

        # Status breakdown
        status_counts = []
        for status in VALID_STATUSES:
            if status in stats['by_status']:
                count = stats['by_status'][status]['count']
                status_counts.append(f"{count} {status}")
        lines.append(f"**Status**: {', '.join(status_counts)}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Projects by priority
        priority_emojis = {'critical': '🔥', 'high': '⚡', 'medium': '📊', 'low': '📌'}

        for priority in ['critical', 'high', 'medium', 'low']:
            priority_projects = by_priority[priority]
            if not priority_projects:
                continue

            emoji = priority_emojis[priority]
            total_effort = sum(p.get('effort_hours') or 0 for p in priority_projects)

            lines.append(f"## {emoji} {priority.upper()} PRIORITY ({len(priority_projects)} projects, {total_effort}h)")
            lines.append("")

            for project in priority_projects:
                lines.append(f"### {project['id']}: {project['name']}")
                lines.append(f"- **Status**: {project['status']}")
                if project.get('effort_hours'):
                    lines.append(f"- **Effort**: {project['effort_hours']}h")
                if project.get('impact'):
                    lines.append(f"- **Impact**: {project['impact']}")
                if project.get('category'):
                    lines.append(f"- **Category**: {project['category']}")
                if project.get('description'):
                    lines.append(f"- **Description**: {project['description']}")
                if project.get('project_plan_path'):
                    lines.append(f"- **Plan**: [{project['project_plan_path']}]({project['project_plan_path']})")
                lines.append("")

        return "\n".join(lines)

    def export_json(self) -> str:
        """Export projects to JSON format."""
        projects = self.list_projects()
        return json.dumps(projects, indent=2, default=str)

    # =========================================================================
    # Validation Helpers
    # =========================================================================

    def _validate_project_id(self, project_id: str) -> bool:
        """Validate project ID format."""
        import re

        if not re.match(r'^[A-Z0-9-]+$', project_id):
            print(f"❌ Invalid project ID: {project_id}", file=sys.stderr)
            print("   ID must be uppercase letters, numbers, and hyphens only", file=sys.stderr)
            print("   Example: REPO-GOV-001", file=sys.stderr)
            return False

        return True


# =============================================================================
# CLI Interface
# =============================================================================

def cmd_add(args, registry: ProjectRegistry):
    """Add new project."""
    return registry.add_project(
        project_id=args.id,
        name=args.name,
        status=args.status,
        priority=args.priority,
        effort_hours=args.effort,
        impact=args.impact,
        category=args.category,
        description=args.description,
        project_plan_path=args.plan
    )

def cmd_list(args, registry: ProjectRegistry):
    """List projects."""
    projects = registry.list_projects(
        status=args.status,
        priority=args.priority,
        category=args.category
    )

    if not projects:
        print("No projects found matching criteria")
        return True

    # Print table
    print(f"{'ID':<20} {'Name':<40} {'Status':<12} {'Priority':<10} {'Effort':<8} {'Impact':<8}")
    print("=" * 110)

    for project in projects:
        effort = f"{project['effort_hours']}h" if project.get('effort_hours') else "-"
        impact = project.get('impact') or "-"

        print(f"{project['id']:<20} {project['name'][:38]:<40} {project['status']:<12} {project['priority']:<10} {effort:<8} {impact:<8}")

    print(f"\nTotal: {len(projects)} projects")
    return True

def cmd_show(args, registry: ProjectRegistry):
    """Show project details."""
    project = registry.show_project(args.id)

    if not project:
        return False

    # Print project details
    print(f"\n{'='*60}")
    print(f"Project: {project['id']}")
    print(f"{'='*60}")
    print(f"Name: {project['name']}")
    print(f"Status: {project['status']}")
    print(f"Priority: {project['priority']}")

    if project.get('effort_hours'):
        print(f"Effort: {project['effort_hours']} hours (estimated)")
    if project.get('actual_hours'):
        print(f"Actual: {project['actual_hours']} hours")
        if project.get('effort_hours'):
            variance = project['actual_hours'] - project['effort_hours']
            print(f"Variance: {variance:+d} hours")

    if project.get('impact'):
        print(f"Impact: {project['impact']}")
    if project.get('category'):
        print(f"Category: {project['category']}")

    print(f"\nDescription:")
    print(f"  {project.get('description') or '(none)'}")

    if project.get('project_plan_path'):
        print(f"\nProject Plan:")
        print(f"  {project['project_plan_path']}")

    print(f"\nTimeline:")
    print(f"  Created: {project['created_date']}")
    if project.get('started_date'):
        print(f"  Started: {project['started_date']}")
    if project.get('completed_date'):
        print(f"  Completed: {project['completed_date']}")

    # Dependencies
    if project.get('dependencies'):
        print(f"\nDependencies:")
        for dep in project['dependencies']:
            print(f"  - {dep['depends_on_project_id']}: {dep['depends_on_name']} ({dep['dependency_type']})")

    # Deliverables
    if project.get('deliverables'):
        print(f"\nDeliverables ({len(project['deliverables'])}):")
        for deliv in project['deliverables']:
            status_emoji = {'planned': '📋', 'in_progress': '🏗️', 'completed': '✅'}
            emoji = status_emoji.get(deliv['status'], '•')
            print(f"  {emoji} {deliv['name']} ({deliv['type']}) - {deliv['status']}")

    print()
    return True

def cmd_update(args, registry: ProjectRegistry):
    """Update project."""
    return registry.update_project(
        project_id=args.id,
        status=args.status,
        priority=args.priority,
        effort_hours=args.effort,
        impact=args.impact,
        notes=args.notes
    )

def cmd_start(args, registry: ProjectRegistry):
    """Start project."""
    return registry.start_project(args.id)

def cmd_complete(args, registry: ProjectRegistry):
    """Complete project."""
    return registry.complete_project(
        project_id=args.id,
        actual_hours=args.actual_hours,
        notes=args.notes
    )

def cmd_backlog(args, registry: ProjectRegistry):
    """Show prioritized backlog."""
    projects = registry.get_backlog()

    if not projects:
        print("No projects in backlog")
        return True

    print("\n" + "="*60)
    print("MAIA PROJECT BACKLOG")
    print("="*60)

    # Group by priority
    by_priority = {}
    for project in projects:
        priority = project['priority']
        if priority not in by_priority:
            by_priority[priority] = []
        by_priority[priority].append(project)

    # Display by priority
    priority_emojis = {'critical': '🔥', 'high': '⚡', 'medium': '📊', 'low': '📌'}

    for priority in ['critical', 'high', 'medium', 'low']:
        if priority not in by_priority:
            continue

        priority_projects = by_priority[priority]
        total_effort = sum(p['effort_hours'] or 0 for p in priority_projects)

        emoji = priority_emojis[priority]
        print(f"\n{emoji} {priority.upper()} PRIORITY ({len(priority_projects)} projects, {total_effort}h)")
        print("-" * 60)

        for project in priority_projects:
            effort = f"{project['effort_hours']}h" if project.get('effort_hours') else "?"
            impact = project.get('impact') or "?"
            category = project.get('category') or "General"

            print(f"\n  {project['id']}: {project['name']}")
            print(f"  Effort: {effort} | Impact: {impact} | Category: {category}")
            if project.get('dependency_count') and project['dependency_count'] > 0:
                print(f"  Dependencies: {project['dependency_count']}")

    print()
    return True

def cmd_stats(args, registry: ProjectRegistry):
    """Show project statistics."""
    stats = registry.get_stats()

    print("\n" + "="*60)
    print("MAIA PROJECT REGISTRY STATISTICS")
    print("="*60)

    # Overall stats
    overall = stats['overall']
    print(f"\nProject Count:")
    print(f"  Total Projects: {overall['total_projects']}")

    # By status
    print(f"\n  By Status:")
    for status in VALID_STATUSES:
        if status in stats['by_status']:
            count = stats['by_status'][status]['count']
            effort = stats['by_status'][status]['total_effort'] or 0
            pct = (count / overall['total_projects']) * 100 if overall['total_projects'] > 0 else 0
            print(f"    {status.capitalize()}: {count} ({pct:.1f}%, {effort}h)")

    # Effort estimates
    if overall['total_effort']:
        print(f"\nEffort Estimates:")
        print(f"  Total Planned Effort: {overall['total_effort']:.0f} hours")
        print(f"  Average Project Size: {overall['avg_effort']:.1f} hours")
        print(f"  Largest Project: {overall['max_effort']:.0f} hours")
        print(f"  Smallest Project: {overall['min_effort']:.0f} hours")

    # By priority
    print(f"\nBy Priority:")
    for priority in ['critical', 'high', 'medium', 'low']:
        if priority in stats['by_priority']:
            count = stats['by_priority'][priority]['count']
            effort = stats['by_priority'][priority]['total_effort'] or 0
            print(f"  {priority.capitalize()}: {count} projects ({effort}h)")

    # By category
    if stats['by_category']:
        print(f"\nBy Category:")
        for cat_stat in stats['by_category'][:10]:  # Top 10
            print(f"  {cat_stat['category']}: {cat_stat['count']} projects ({cat_stat['total_effort'] or 0}h)")

    # Velocity
    velocity = stats['velocity']
    if velocity['completed_count']:
        print(f"\nVelocity (last 30 days):")
        print(f"  Completed: {velocity['completed_count']} projects")
        if velocity['avg_days']:
            print(f"  Average completion time: {velocity['avg_days']:.1f} days")
        if velocity['estimated_hours'] and velocity['actual_hours']:
            variance_pct = ((velocity['actual_hours'] - velocity['estimated_hours']) / velocity['estimated_hours']) * 100
            print(f"  Effort variance: {variance_pct:+.1f}% ({'over' if variance_pct > 0 else 'under'} estimate)")

    print()
    return True

def cmd_export(args, registry: ProjectRegistry):
    """Export projects."""
    if args.format == 'markdown':
        output = registry.export_markdown(status_filter=args.status)

        if args.output:
            with open(args.output, 'w') as f:
                f.write(output)
            print(f"✅ Exported to {args.output}")
        else:
            print(output)

    elif args.format == 'json':
        output = registry.export_json()

        if args.output:
            with open(args.output, 'w') as f:
                f.write(output)
            print(f"✅ Exported to {args.output}")
        else:
            print(output)

    return True

def cmd_depend(args, registry: ProjectRegistry):
    """Manage dependencies."""
    if args.depend_command == 'add':
        return registry.add_dependency(
            project_id=args.project,
            depends_on_project_id=args.depends_on,
            dependency_type=args.type,
            notes=args.notes
        )

    return True


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Maia Project Registry - Production-grade project backlog management",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Add command
    parser_add = subparsers.add_parser('add', help='Add new project')
    parser_add.add_argument('--id', required=True, help='Project ID (e.g., REPO-GOV-001)')
    parser_add.add_argument('--name', required=True, help='Project name')
    parser_add.add_argument('--status', default='planned', choices=VALID_STATUSES, help='Project status')
    parser_add.add_argument('--priority', default='medium', choices=VALID_PRIORITIES, help='Priority level')
    parser_add.add_argument('--effort', type=int, help='Estimated effort in hours')
    parser_add.add_argument('--impact', choices=VALID_IMPACTS, help='Impact level')
    parser_add.add_argument('--category', help='Project category')
    parser_add.add_argument('--description', help='Brief description')
    parser_add.add_argument('--plan', help='Path to project plan file')

    # List command
    parser_list = subparsers.add_parser('list', help='List projects')
    parser_list.add_argument('--status', choices=VALID_STATUSES, help='Filter by status')
    parser_list.add_argument('--priority', choices=VALID_PRIORITIES, help='Filter by priority')
    parser_list.add_argument('--category', help='Filter by category')

    # Show command
    parser_show = subparsers.add_parser('show', help='Show project details')
    parser_show.add_argument('id', help='Project ID')

    # Update command
    parser_update = subparsers.add_parser('update', help='Update project')
    parser_update.add_argument('id', help='Project ID')
    parser_update.add_argument('--status', choices=VALID_STATUSES, help='New status')
    parser_update.add_argument('--priority', choices=VALID_PRIORITIES, help='New priority')
    parser_update.add_argument('--effort', type=int, help='New effort estimate')
    parser_update.add_argument('--impact', choices=VALID_IMPACTS, help='New impact')
    parser_update.add_argument('--notes', help='Additional notes')

    # Start command
    parser_start = subparsers.add_parser('start', help='Start project (set status to active)')
    parser_start.add_argument('id', help='Project ID')

    # Complete command
    parser_complete = subparsers.add_parser('complete', help='Complete project')
    parser_complete.add_argument('id', help='Project ID')
    parser_complete.add_argument('--actual-hours', type=int, help='Actual hours spent')
    parser_complete.add_argument('--notes', help='Completion notes')

    # Backlog command
    parser_backlog = subparsers.add_parser('backlog', help='Show prioritized backlog')

    # Stats command
    parser_stats = subparsers.add_parser('stats', help='Show project statistics')

    # Export command
    parser_export = subparsers.add_parser('export', help='Export projects')
    parser_export.add_argument('--format', choices=['markdown', 'json'], default='markdown', help='Export format')
    parser_export.add_argument('--status', choices=VALID_STATUSES, help='Filter by status')
    parser_export.add_argument('--output', help='Output file (default: stdout)')

    # Depend command
    parser_depend = subparsers.add_parser('depend', help='Manage dependencies')
    depend_subparsers = parser_depend.add_subparsers(dest='depend_command')

    parser_depend_add = depend_subparsers.add_parser('add', help='Add dependency')
    parser_depend_add.add_argument('--project', required=True, help='Project ID')
    parser_depend_add.add_argument('--depends-on', required=True, help='Dependency project ID')
    parser_depend_add.add_argument('--type', default='blocks', choices=VALID_DEPENDENCY_TYPES, help='Dependency type')
    parser_depend_add.add_argument('--notes', help='Dependency notes')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Execute command
    with ProjectRegistry() as registry:
        command_map = {
            'add': cmd_add,
            'list': cmd_list,
            'show': cmd_show,
            'update': cmd_update,
            'start': cmd_start,
            'complete': cmd_complete,
            'backlog': cmd_backlog,
            'stats': cmd_stats,
            'export': cmd_export,
            'depend': cmd_depend,
        }

        cmd_func = command_map.get(args.command)
        if cmd_func:
            success = cmd_func(args, registry)
            return 0 if success else 1
        else:
            print(f"❌ Unknown command: {args.command}", file=sys.stderr)
            return 1


if __name__ == '__main__':
    sys.exit(main())
