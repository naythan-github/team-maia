#!/usr/bin/env python3
"""
SYSTEM_STATE Database Query Interface

Provides high-level query functions for smart context loader integration.
Designed for fast retrieval (<20ms) with graceful error handling.

Part of Phase 165: Smart Loader Database Integration

Usage:
    from claude.tools.sre.system_state_queries import SystemStateQueries

    queries = SystemStateQueries()

    # Get recent phases
    phases = queries.get_recent_phases(count=10)

    # Search by keyword
    phases = queries.get_phases_by_keyword("ChromaDB")

    # Get specific phases
    phases = queries.get_phases_by_number([2, 107, 134])

    # Get phase with full context
    phase = queries.get_phase_with_context(164)
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
import logging

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


@dataclass
class PhaseRecord:
    """Phase metadata from database"""
    id: int
    phase_number: int
    title: str
    date: str
    status: Optional[str]
    achievement: Optional[str]
    agent_team: Optional[str]
    git_commits: Optional[str]
    narrative_text: Optional[str]
    created_at: str
    updated_at: str


@dataclass
class PhaseWithContext:
    """Phase with all related data"""
    phase: PhaseRecord
    problems: List[Dict[str, Any]]
    solutions: List[Dict[str, Any]]
    metrics: List[Dict[str, Any]]
    files_created: List[Dict[str, Any]]
    tags: List[str]


class SystemStateQueries:
    """
    High-level query interface for SYSTEM_STATE database.

    Designed for smart context loader integration with <20ms query latency.
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize query interface.

        Args:
            db_path: Path to database (default: claude/data/databases/system/system_state.db)
        """
        if db_path is None:
            # Tool is in claude/tools/sre/, DB is in claude/data/databases/system/
            maia_root = Path(__file__).resolve().parent.parent.parent.parent
            db_path = maia_root / "claude" / "data" / "databases" / "system" / "system_state.db"

        self.db_path = Path(db_path)

        if not self.db_path.exists():
            raise FileNotFoundError(
                f"Database not found: {self.db_path}\n"
                f"Run ETL to create database: python3 claude/tools/sre/system_state_etl.py"
            )

    def _get_connection(self) -> sqlite3.Connection:
        """
        Get database connection with proper configuration.

        Returns:
            sqlite3.Connection configured for read-only access
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        conn.execute("PRAGMA query_only = ON")  # Read-only mode
        return conn

    def get_recent_phases(self, count: int = 10) -> List[PhaseRecord]:
        """
        Get most recent phases.

        Args:
            count: Number of phases to return

        Returns:
            List of PhaseRecord objects (most recent first)

        Example:
            >>> queries = SystemStateQueries()
            >>> phases = queries.get_recent_phases(5)
            >>> print(phases[0].phase_number)  # Most recent phase
            164
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM phases
                ORDER BY phase_number DESC
                LIMIT ?
            """, (count,))

            rows = cursor.fetchall()
            conn.close()

            return [PhaseRecord(**dict(row)) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get recent phases: {e}")
            raise

    def get_phases_by_keyword(self, keyword: str, limit: int = 20) -> List[PhaseRecord]:
        """
        Search for phases containing keyword in narrative text.

        Args:
            keyword: Search keyword (case-insensitive)
            limit: Maximum results to return

        Returns:
            List of matching PhaseRecord objects (most recent first)

        Example:
            >>> phases = queries.get_phases_by_keyword("ChromaDB")
            >>> print([p.phase_number for p in phases])
            [156, 10]
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM phases
                WHERE narrative_text LIKE ?
                OR title LIKE ?
                OR achievement LIKE ?
                ORDER BY phase_number DESC
                LIMIT ?
            """, (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%', limit))

            rows = cursor.fetchall()
            conn.close()

            return [PhaseRecord(**dict(row)) for row in rows]

        except Exception as e:
            logger.error(f"Failed to search keyword '{keyword}': {e}")
            raise

    def get_phases_by_number(self, phase_numbers: List[int]) -> List[PhaseRecord]:
        """
        Get specific phases by number.

        Args:
            phase_numbers: List of phase numbers to retrieve

        Returns:
            List of PhaseRecord objects (ordered by phase number descending)

        Example:
            >>> phases = queries.get_phases_by_number([2, 107, 134])
            >>> print(len(phases))
            3
        """
        if not phase_numbers:
            return []

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Build placeholders for IN clause
            placeholders = ','.join('?' * len(phase_numbers))

            cursor.execute(f"""
                SELECT * FROM phases
                WHERE phase_number IN ({placeholders})
                ORDER BY phase_number DESC
            """, phase_numbers)

            rows = cursor.fetchall()
            conn.close()

            return [PhaseRecord(**dict(row)) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get phases by number: {e}")
            raise

    def get_phase_with_context(self, phase_number: int) -> Optional[PhaseWithContext]:
        """
        Get phase with all related data (problems, solutions, metrics, files, tags).

        Args:
            phase_number: Phase number to retrieve

        Returns:
            PhaseWithContext object or None if phase not found

        Example:
            >>> phase = queries.get_phase_with_context(164)
            >>> print(phase.phase.title)
            'SYSTEM_STATE Hybrid Database'
            >>> print(len(phase.metrics))
            4
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Get phase
            cursor.execute("""
                SELECT * FROM phases
                WHERE phase_number = ?
            """, (phase_number,))

            phase_row = cursor.fetchone()
            if not phase_row:
                conn.close()
                return None

            phase = PhaseRecord(**dict(phase_row))
            phase_id = phase.id

            # Get related data
            cursor.execute("SELECT * FROM problems WHERE phase_id = ?", (phase_id,))
            problems = [dict(row) for row in cursor.fetchall()]

            cursor.execute("SELECT * FROM solutions WHERE phase_id = ?", (phase_id,))
            solutions = [dict(row) for row in cursor.fetchall()]

            cursor.execute("SELECT * FROM metrics WHERE phase_id = ?", (phase_id,))
            metrics = [dict(row) for row in cursor.fetchall()]

            cursor.execute("SELECT * FROM files_created WHERE phase_id = ?", (phase_id,))
            files_created = [dict(row) for row in cursor.fetchall()]

            cursor.execute("SELECT tag FROM tags WHERE phase_id = ?", (phase_id,))
            tags = [row['tag'] for row in cursor.fetchall()]

            conn.close()

            return PhaseWithContext(
                phase=phase,
                problems=problems,
                solutions=solutions,
                metrics=metrics,
                files_created=files_created,
                tags=tags
            )

        except Exception as e:
            logger.error(f"Failed to get phase {phase_number} with context: {e}")
            raise

    def search_problems_by_category(self, category: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Find phases that solved specific problem categories.

        Args:
            category: Problem category to search for (e.g., "SQL injection", "performance")
            limit: Maximum results to return

        Returns:
            List of dicts with phase info and problem details

        Example:
            >>> results = queries.search_problems_by_category("SQL injection")
            >>> print(results[0]['phase_number'])
            103
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    p.phase_number,
                    p.title,
                    p.date,
                    pr.problem_category,
                    pr.before_state,
                    pr.root_cause
                FROM problems pr
                JOIN phases p ON pr.phase_id = p.id
                WHERE pr.problem_category LIKE ?
                ORDER BY p.phase_number DESC
                LIMIT ?
            """, (f'%{category}%', limit))

            rows = cursor.fetchall()
            conn.close()

            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to search problem category '{category}': {e}")
            raise

    def get_all_problem_categories(self) -> List[Dict[str, Any]]:
        """
        Get summary of all problem categories.

        Returns:
            List of dicts with category, count, and phase numbers

        Example:
            >>> categories = queries.get_all_problem_categories()
            >>> print(categories[0])
            {'problem_category': 'SQL injection', 'count': 2, 'phase_numbers': '103,134'}
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM v_problem_categories")

            rows = cursor.fetchall()
            conn.close()

            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get problem categories: {e}")
            raise

    def get_metric_summary(self, metric_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get metric aggregation summary.

        Args:
            metric_name: Optional metric name filter

        Returns:
            List of dicts with metric statistics

        Example:
            >>> summary = queries.get_metric_summary("time_savings_hours")
            >>> print(summary[0]['total_value'])
            2847.5
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            if metric_name:
                cursor.execute("""
                    SELECT * FROM v_metric_summary
                    WHERE metric_name = ?
                """, (metric_name,))
            else:
                cursor.execute("SELECT * FROM v_metric_summary")

            rows = cursor.fetchall()
            conn.close()

            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get metric summary: {e}")
            raise

    def get_files_by_type(self, file_type: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all files of a specific type.

        Args:
            file_type: File type (e.g., "agent", "tool", "database")
            status: Optional status filter (e.g., "production", "deprecated")

        Returns:
            List of dicts with file information

        Example:
            >>> agents = queries.get_files_by_type("agent", status="production")
            >>> print(len(agents))
            49
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            if status:
                cursor.execute("""
                    SELECT
                        f.*,
                        p.phase_number,
                        p.title,
                        p.date
                    FROM files_created f
                    JOIN phases p ON f.phase_id = p.id
                    WHERE f.file_type = ? AND f.status = ?
                    ORDER BY p.phase_number DESC
                """, (file_type, status))
            else:
                cursor.execute("""
                    SELECT
                        f.*,
                        p.phase_number,
                        p.title,
                        p.date
                    FROM files_created f
                    JOIN phases p ON f.phase_id = p.id
                    WHERE f.file_type = ?
                    ORDER BY p.phase_number DESC
                """, (file_type,))

            rows = cursor.fetchall()
            conn.close()

            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get files by type '{file_type}': {e}")
            raise

    def format_phase_as_markdown(self, phase: PhaseRecord) -> str:
        """
        Format phase record as markdown (compatible with existing smart loader output).

        Args:
            phase: PhaseRecord to format

        Returns:
            Markdown-formatted string
        """
        if phase.narrative_text:
            # Use stored narrative text if available
            return phase.narrative_text

        # Otherwise, construct from structured data
        md = f"## PHASE {phase.phase_number}: {phase.title} ({phase.date})"
        if phase.status:
            md += f" **{phase.status}**"
        md += "\n\n"

        if phase.achievement:
            md += f"### Achievement\n{phase.achievement}\n\n"

        if phase.agent_team:
            md += f"**Agent Team**: {phase.agent_team}\n\n"

        if phase.git_commits:
            md += f"**Git Commits**: {phase.git_commits}\n\n"

        return md

    def format_phases_as_markdown(self, phases: List[PhaseRecord]) -> str:
        """
        Format multiple phases as markdown document.

        Args:
            phases: List of PhaseRecord objects

        Returns:
            Complete markdown document with all phases
        """
        sections = [self.format_phase_as_markdown(p) for p in phases]
        return "\n\n---\n\n".join(sections)


def main():
    """CLI interface for testing query functions."""
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="SYSTEM_STATE Database Query Interface"
    )

    subparsers = parser.add_subparsers(dest='command', help='Query command')

    # Recent phases
    recent_parser = subparsers.add_parser('recent', help='Get recent phases')
    recent_parser.add_argument('--count', type=int, default=10, help='Number of phases')

    # Keyword search
    search_parser = subparsers.add_parser('search', help='Search by keyword')
    search_parser.add_argument('keyword', help='Search keyword')
    search_parser.add_argument('--limit', type=int, default=20, help='Max results')

    # Specific phases
    phases_parser = subparsers.add_parser('phases', help='Get specific phases')
    phases_parser.add_argument('numbers', type=int, nargs='+', help='Phase numbers')

    # Phase with context
    context_parser = subparsers.add_parser('context', help='Get phase with full context')
    context_parser.add_argument('phase_number', type=int, help='Phase number')

    # Problem categories
    problems_parser = subparsers.add_parser('problems', help='Search problems by category')
    problems_parser.add_argument('category', help='Problem category')

    # Output format
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--markdown', action='store_true', help='Output as markdown')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    queries = SystemStateQueries()

    # Execute command
    if args.command == 'recent':
        results = queries.get_recent_phases(args.count)
    elif args.command == 'search':
        results = queries.get_phases_by_keyword(args.keyword, args.limit)
    elif args.command == 'phases':
        results = queries.get_phases_by_number(args.numbers)
    elif args.command == 'context':
        results = queries.get_phase_with_context(args.phase_number)
    elif args.command == 'problems':
        results = queries.search_problems_by_category(args.category)

    # Output results
    if args.json:
        if hasattr(results, '__iter__') and not isinstance(results, str):
            output = [asdict(r) if hasattr(r, '__dataclass_fields__') else r for r in results]
        else:
            output = asdict(results) if hasattr(results, '__dataclass_fields__') else results
        print(json.dumps(output, indent=2, default=str))
    elif args.markdown and args.command in ['recent', 'search', 'phases']:
        print(queries.format_phases_as_markdown(results))
    else:
        # Pretty print
        if isinstance(results, list):
            for i, r in enumerate(results):
                if hasattr(r, '__dataclass_fields__'):
                    print(f"\n=== Result {i+1} ===")
                    for field, value in asdict(r).items():
                        print(f"{field}: {value}")
                else:
                    print(f"\n=== Result {i+1} ===")
                    for k, v in r.items():
                        print(f"{k}: {v}")
        else:
            if hasattr(results, '__dataclass_fields__'):
                for field, value in asdict(results).items():
                    print(f"{field}: {value}")
            else:
                print(results)


if __name__ == '__main__':
    main()
