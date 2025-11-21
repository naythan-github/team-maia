#!/usr/bin/env python3
"""
SYSTEM_STATE.md ETL (Extract, Transform, Load)

Parses markdown and populates SQLite database with structured data.
Following TDD methodology with comprehensive error handling.

Agent: SRE Principal Engineer Agent
Phase: 164 - SYSTEM_STATE Migration
"""

import re
import sqlite3
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Phase:
    """Structured phase data"""
    phase_number: int
    title: str
    date: str
    status: Optional[str] = None
    achievement: Optional[str] = None
    agent_team: Optional[str] = None
    git_commits: Optional[str] = None
    narrative_text: Optional[str] = None


@dataclass
class Problem:
    """Problem record"""
    problem_category: Optional[str]
    before_state: str
    root_cause: Optional[str] = None


@dataclass
class Solution:
    """Solution record"""
    solution_category: Optional[str]
    after_state: str
    architecture: Optional[str] = None
    implementation_approach: Optional[str] = None


@dataclass
class Metric:
    """Metric record"""
    metric_name: str
    value: float
    unit: str
    baseline: Optional[str] = None
    target: Optional[str] = None


@dataclass
class FileCreated:
    """File creation record"""
    file_path: str
    file_type: Optional[str] = None
    purpose: Optional[str] = None
    status: Optional[str] = None


class SystemStateParser:
    """Parser for SYSTEM_STATE.md markdown"""

    # Regex patterns for phase headers (handles emoji variations)
    PHASE_HEADER_PATTERNS = [
        # Format: ## 📄 PHASE 163: Title (2025-11-21) **STATUS**
        re.compile(r'^##\s+[🔬🚀🎯🤖💼📋🎓🔗🛡️🎤📊🧠📄🔄📦⚙️🏗️💡🔧🎨🧪🗄️].+?PHASE\s+(\d+):\s*(.+?)\s+\((\d{4}-\d{2}-\d{2})\)\s*(?:\*\*(.+?)\*\*)?', re.IGNORECASE),
        # Format: ## PHASE 163: Title (2025-11-21)
        re.compile(r'^##\s+PHASE\s+(\d+):\s*(.+?)\s+\((\d{4}-\d{2}-\d{2})\)', re.IGNORECASE),
    ]

    def __init__(self, system_state_path: Path):
        self.system_state_path = system_state_path
        self.content = system_state_path.read_text()

    def split_into_phases(self) -> List[Tuple[int, str]]:
        """
        Split SYSTEM_STATE.md into individual phase sections
        Uses --- separators to define phase boundaries (more reliable than headers alone)
        Returns: List of (phase_number, phase_text) tuples
        """
        # Split by --- section separators
        sections = re.split(r'\n---+\n', self.content)

        phases = []
        for section in sections:
            section = section.strip()
            if not section:
                continue

            # Check if this section starts with a phase header
            for pattern in self.PHASE_HEADER_PATTERNS:
                match = pattern.match(section)
                if match:
                    phase_number = int(match.group(1))
                    phases.append((phase_number, section))
                    break  # Found phase header, move to next section

        return phases

    def parse_phase_header(self, phase_text: str) -> Tuple[int, str, str, Optional[str]]:
        """
        Extract phase number, title, date, and status from header
        Returns: (phase_number, title, date, status)
        """
        lines = phase_text.splitlines()
        if not lines:
            raise ValueError("Empty phase text")

        # Try each pattern
        for pattern in self.PHASE_HEADER_PATTERNS:
            match = pattern.match(lines[0])
            if match:
                phase_number = int(match.group(1))
                title = match.group(2).strip()
                date = match.group(3)

                # Status is optional (group 4)
                status = None
                if len(match.groups()) >= 4:
                    status = match.group(4)

                return phase_number, title, date, status

        raise ValueError(f"Could not parse phase header: {lines[0][:100]}")

    def extract_section(self, phase_text: str, section_name: str) -> Optional[str]:
        """
        Extract content from a named section (e.g., "Achievement", "Problem Solved")
        Returns section content or None if not found
        """
        # Look for ### Section Name
        pattern = re.compile(rf'^###\s+{re.escape(section_name)}\s*$', re.MULTILINE | re.IGNORECASE)
        match = pattern.search(phase_text)

        if not match:
            return None

        # Extract content until next ### section or ---
        start = match.end()
        content_lines = []

        for line in phase_text[start:].splitlines():
            if line.strip().startswith('###') or line.strip() == '---':
                break
            content_lines.append(line)

        return '\n'.join(content_lines).strip()

    def parse_achievement(self, phase_text: str) -> Optional[str]:
        """Extract achievement summary"""
        return self.extract_section(phase_text, "Achievement")

    def parse_problems(self, phase_text: str) -> List[Problem]:
        """
        Extract problems from "Problem Solved" section
        Returns list of Problem objects
        """
        problems = []

        # Look for Problem Solved section
        section = self.extract_section(phase_text, "Problem Solved")
        if not section:
            return problems

        # Look for "Before:" and "After:" patterns
        before_pattern = re.compile(r'\*\*Before\*\*:\s*(.+?)(?=\*\*After\*\*|$)', re.DOTALL | re.IGNORECASE)
        before_matches = before_pattern.findall(section)

        for before_text in before_matches:
            problem = Problem(
                problem_category=None,  # TODO: Categorize problems
                before_state=before_text.strip(),
                root_cause=None  # TODO: Extract root cause if available
            )
            problems.append(problem)

        return problems

    def parse_solutions(self, phase_text: str) -> List[Solution]:
        """
        Extract solutions from "Problem Solved" section
        Returns list of Solution objects
        """
        solutions = []

        section = self.extract_section(phase_text, "Problem Solved")
        if not section:
            return solutions

        # Look for "After:" patterns
        after_pattern = re.compile(r'\*\*After\*\*:\s*(.+?)(?=\*\*Before\*\*|\*\*Part \d|###|$)', re.DOTALL | re.IGNORECASE)
        after_matches = after_pattern.findall(section)

        for after_text in after_matches:
            solution = Solution(
                solution_category=None,  # TODO: Categorize solutions
                after_state=after_text.strip(),
                architecture=None,  # TODO: Extract architecture if available
                implementation_approach=None
            )
            solutions.append(solution)

        return solutions

    def parse_metrics(self, phase_text: str) -> List[Metric]:
        """
        Extract metrics from "Metrics" section
        Returns list of Metric objects
        """
        metrics = []

        section = self.extract_section(phase_text, "Metrics")
        if not section:
            return metrics

        # Pattern: "Time Savings**: 30 min → 2 min (95% reduction)"
        # Pattern: "Performance**: 0.10s avg (50x faster)"
        metric_patterns = [
            # Hours pattern: "X hours → Y hours" or "X-Y hours → Z hours"
            (r'(\d+(?:-\d+)?)\s*(?:hours?|h)\s*→\s*(\d+(?:\.\d+)?)\s*(?:hours?|h)', 'time_savings_hours'),
            # Minutes pattern
            (r'(\d+)\s*(?:minutes?|min)\s*→\s*(\d+)\s*(?:minutes?|min)', 'time_savings_minutes'),
            # Percentage pattern: "(95% reduction)" or "95%"
            (r'(\d+(?:\.\d+)?)\s*%\s*(?:reduction|improvement|savings|faster)', 'percentage_improvement'),
            # Seconds pattern: "0.10s"
            (r'(\d+\.\d+)s\s*(?:avg|average)', 'performance_seconds'),
        ]

        for pattern, metric_name in metric_patterns:
            matches = re.findall(pattern, section, re.IGNORECASE)
            for match in matches:
                try:
                    if isinstance(match, tuple):
                        # Before → After pattern
                        baseline = match[0]
                        value = float(match[1])
                    else:
                        baseline = None
                        value = float(match)

                    # Determine unit
                    if 'hours' in metric_name:
                        unit = 'hours'
                    elif 'minutes' in metric_name:
                        unit = 'minutes'
                    elif 'seconds' in metric_name:
                        unit = 'seconds'
                    elif 'percentage' in metric_name:
                        unit = 'percent'
                    else:
                        unit = 'unknown'

                    metrics.append(Metric(
                        metric_name=metric_name,
                        value=value,
                        unit=unit,
                        baseline=str(baseline) if baseline else None,
                        target=None
                    ))
                except (ValueError, IndexError):
                    continue  # Skip malformed metrics

        return metrics

    def parse_files_created(self, phase_text: str) -> List[FileCreated]:
        """
        Extract files created from "Files Created" section
        Returns list of FileCreated objects
        """
        files = []

        # Look for multiple section names
        section = self.extract_section(phase_text, "Files Created")
        if not section:
            section = self.extract_section(phase_text, "Deliverables")
        if not section:
            return files

        # Pattern: "- `path/to/file.py` - Description"
        file_pattern = re.compile(r'[-*]\s+`([^`]+)`\s*(?:-\s*(.+?))?(?:\(|$)', re.MULTILINE)

        for match in file_pattern.finditer(section):
            file_path = match.group(1).strip()
            purpose = match.group(2).strip() if match.group(2) else None

            # Infer file type from extension
            file_type = None
            if file_path.endswith('.py'):
                if 'agent' in file_path:
                    file_type = 'agent'
                elif 'test' in file_path:
                    file_type = 'test'
                else:
                    file_type = 'tool'
            elif file_path.endswith('.md'):
                file_type = 'documentation'
            elif file_path.endswith('.db'):
                file_type = 'database'
            elif file_path.endswith(('.docx', '.json', '.yaml', '.sql')):
                file_type = 'data'

            files.append(FileCreated(
                file_path=file_path,
                file_type=file_type,
                purpose=purpose,
                status='production'  # Assume production unless stated otherwise
            ))

        return files

    def parse_git_commits(self, phase_text: str) -> Optional[str]:
        """Extract git commit hashes from phase text"""
        # Look for "Git Commits:" or similar section
        commit_pattern = re.compile(r'(?:Git Commits?:|Commit:)\s*(.+?)(?=\n\n|$)', re.DOTALL | re.IGNORECASE)
        match = commit_pattern.search(phase_text)

        if not match:
            return None

        # Extract commit hashes (7-40 character hex strings)
        commits_text = match.group(1)
        hash_pattern = re.compile(r'\b([0-9a-f]{7,40})\b')
        hashes = hash_pattern.findall(commits_text)

        return ', '.join(hashes) if hashes else None

    def parse_agent_team(self, phase_text: str) -> Optional[str]:
        """Extract agent team from phase text"""
        # Look for "Agent Team:" section
        team_pattern = re.compile(r'\*\*Agent Team\*\*:\s*(.+?)(?=\n\n|###|$)', re.DOTALL)
        match = team_pattern.search(phase_text)

        if not match:
            return None

        # Extract agent names
        team_text = match.group(1)
        # Remove list markers and extra whitespace
        agent_names = re.findall(r'[-*]\s*(.+?)(?:Agent|\n|$)', team_text)

        if agent_names:
            return ', '.join([name.strip() for name in agent_names])

        return team_text.strip()

    def parse_phase(self, phase_text: str) -> Phase:
        """
        Parse complete phase from markdown text
        Returns: Phase object with all extracted data
        """
        # Extract header info
        phase_number, title, date, status = self.parse_phase_header(phase_text)

        # Extract sections
        achievement = self.parse_achievement(phase_text)
        agent_team = self.parse_agent_team(phase_text)
        git_commits = self.parse_git_commits(phase_text)

        return Phase(
            phase_number=phase_number,
            title=title,
            date=date,
            status=status,
            achievement=achievement,
            agent_team=agent_team,
            git_commits=git_commits,
            narrative_text=phase_text
        )


class SystemStateETL:
    """ETL pipeline for SYSTEM_STATE.md → Database"""

    def __init__(self, db_path: Path, system_state_path: Path):
        self.db_path = db_path
        self.parser = SystemStateParser(system_state_path)

    def init_database(self):
        """Initialize database schema"""
        schema_path = Path(__file__).parent / "system_state_schema.sql"
        with open(schema_path) as f:
            schema_sql = f.read()

        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(schema_sql)
        conn.close()

    def load_phase(self, conn: sqlite3.Connection, phase: Phase,
                   problems: List[Problem], solutions: List[Solution],
                   metrics: List[Metric], files: List[FileCreated]) -> int:
        """
        Load phase and related data into database
        Returns: phase_id
        """
        cursor = conn.cursor()

        # Insert phase
        cursor.execute("""
            INSERT INTO phases (
                phase_number, title, date, status, achievement,
                agent_team, git_commits, narrative_text
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            phase.phase_number, phase.title, phase.date, phase.status,
            phase.achievement, phase.agent_team, phase.git_commits,
            phase.narrative_text
        ))
        phase_id = cursor.lastrowid

        # Insert problems
        for problem in problems:
            cursor.execute("""
                INSERT INTO problems (phase_id, problem_category, before_state, root_cause)
                VALUES (?, ?, ?, ?)
            """, (phase_id, problem.problem_category, problem.before_state, problem.root_cause))

        # Insert solutions
        for solution in solutions:
            cursor.execute("""
                INSERT INTO solutions (phase_id, solution_category, after_state, architecture, implementation_approach)
                VALUES (?, ?, ?, ?, ?)
            """, (phase_id, solution.solution_category, solution.after_state,
                  solution.architecture, solution.implementation_approach))

        # Insert metrics
        for metric in metrics:
            cursor.execute("""
                INSERT INTO metrics (phase_id, metric_name, value, unit, baseline, target)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (phase_id, metric.metric_name, metric.value, metric.unit,
                  metric.baseline, metric.target))

        # Insert files
        for file in files:
            cursor.execute("""
                INSERT INTO files_created (phase_id, file_path, file_type, purpose, status)
                VALUES (?, ?, ?, ?, ?)
            """, (phase_id, file.file_path, file.file_type, file.purpose, file.status))

        return phase_id

    def run(self, phase_numbers: Optional[List[int]] = None, progress: bool = True) -> Dict[str, any]:
        """
        Run ETL pipeline

        Args:
            phase_numbers: Optional list of specific phase numbers to process
            progress: Show progress output

        Returns: Statistics dict
        """
        print("🔄 SYSTEM_STATE ETL Pipeline")
        print("=" * 70)

        # Split into phases
        if progress:
            print("📄 Parsing SYSTEM_STATE.md...")

        phases_found = self.parser.split_into_phases()

        # Deduplicate phases (keep first occurrence only)
        seen_phases = set()
        deduped_phases = []
        for num, text in phases_found:
            if num not in seen_phases:
                seen_phases.add(num)
                deduped_phases.append((num, text))
        phases_found = deduped_phases

        if phase_numbers:
            # Filter to requested phases
            phases_found = [(num, text) for num, text in phases_found if num in phase_numbers]
            if progress:
                print(f"   Found {len(phases_found)} requested phases")
        else:
            if progress:
                print(f"   Found {len(phases_found)} total phases")

        # Statistics
        stats = {
            'phases_processed': 0,
            'problems_extracted': 0,
            'solutions_extracted': 0,
            'metrics_extracted': 0,
            'files_extracted': 0,
            'errors': []
        }

        # Initialize database
        if progress:
            print("\n🗄️  Initializing database...")
        self.init_database()

        # Process phases
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")

        try:
            for i, (phase_num, phase_text) in enumerate(phases_found):
                if progress:
                    print(f"\n📊 Processing Phase {phase_num} ({i+1}/{len(phases_found)})...")

                try:
                    # Parse phase
                    phase = self.parser.parse_phase(phase_text)
                    problems = self.parser.parse_problems(phase_text)
                    solutions = self.parser.parse_solutions(phase_text)
                    metrics = self.parser.parse_metrics(phase_text)
                    files = self.parser.parse_files_created(phase_text)

                    # Load into database
                    self.load_phase(conn, phase, problems, solutions, metrics, files)
                    conn.commit()

                    # Update stats
                    stats['phases_processed'] += 1
                    stats['problems_extracted'] += len(problems)
                    stats['solutions_extracted'] += len(solutions)
                    stats['metrics_extracted'] += len(metrics)
                    stats['files_extracted'] += len(files)

                    if progress:
                        print(f"   ✅ {len(problems)} problems, {len(solutions)} solutions, "
                              f"{len(metrics)} metrics, {len(files)} files")

                except Exception as e:
                    error_msg = f"Phase {phase_num}: {str(e)}"
                    stats['errors'].append(error_msg)
                    if progress:
                        print(f"   ❌ Error: {e}")
                    conn.rollback()  # Roll back this phase

        finally:
            conn.close()

        # Print summary
        if progress:
            print("\n" + "=" * 70)
            print("✅ ETL COMPLETE")
            print("=" * 70)
            print(f"Phases processed: {stats['phases_processed']}")
            print(f"Problems extracted: {stats['problems_extracted']}")
            print(f"Solutions extracted: {stats['solutions_extracted']}")
            print(f"Metrics extracted: {stats['metrics_extracted']}")
            print(f"Files extracted: {stats['files_extracted']}")

            if stats['errors']:
                print(f"\n⚠️  Errors: {len(stats['errors'])}")
                for error in stats['errors'][:5]:
                    print(f"   - {error}")

        return stats


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='ETL for SYSTEM_STATE.md → Database')
    parser.add_argument('--db', type=Path,
                       default=Path.home() / 'git/maia/claude/data/databases/system/system_state.db',
                       help='Database path')
    parser.add_argument('--source', type=Path,
                       default=Path.home() / 'git/maia/SYSTEM_STATE.md',
                       help='SYSTEM_STATE.md path')
    parser.add_argument('--phases', type=int, nargs='+',
                       help='Specific phase numbers to process (e.g., --phases 144 145 146)')
    parser.add_argument('--recent', type=int,
                       help='Process N most recent phases (e.g., --recent 20)')
    parser.add_argument('--quiet', action='store_true',
                       help='Suppress progress output')

    args = parser.parse_args()

    # Validate paths
    if not args.source.exists():
        print(f"❌ Error: SYSTEM_STATE.md not found at {args.source}")
        sys.exit(1)

    # Run ETL
    etl = SystemStateETL(args.db, args.source)

    # Determine which phases to process
    if args.recent:
        # Get all phases, take last N
        phases_found = etl.parser.split_into_phases()
        phase_numbers = [num for num, _ in sorted(phases_found, key=lambda x: x[0])[-args.recent:]]
        stats = etl.run(phase_numbers=phase_numbers, progress=not args.quiet)
    elif args.phases:
        stats = etl.run(phase_numbers=args.phases, progress=not args.quiet)
    else:
        stats = etl.run(progress=not args.quiet)

    # Exit code based on success
    sys.exit(0 if not stats['errors'] else 1)


if __name__ == '__main__':
    main()
