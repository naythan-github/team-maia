#!/usr/bin/env python3
"""
Maia Project Registry - Migration Script
Project: PROJ-REG-001
Purpose: Import existing project files into project_registry.db

Usage:
    migrate_existing_projects.py --dry-run     # Preview without importing
    migrate_existing_projects.py --confirm     # Execute migration
"""

import sqlite3
import re
import os
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# Import registry for database operations
from project_registry import ProjectRegistry, VALID_STATUSES, VALID_PRIORITIES, VALID_IMPACTS

MAIA_ROOT = os.environ.get("MAIA_ROOT", os.path.expanduser("~/git/maia"))


class ProjectFileMigrator:
    """Migrates existing project markdown files to database."""

    def __init__(self, source_dir: str):
        """Initialize migrator."""
        self.source_dir = Path(source_dir)
        self.projects_found = []
        self.migration_results = {
            'success': [],
            'skipped': [],
            'failed': [],
            'warnings': []
        }

    def scan_project_files(self) -> List[Path]:
        """Scan source directory for project files."""
        print(f"Scanning {self.source_dir} for project files...")

        patterns = ["*PROJECT*.md", "*PLAN*.md"]
        project_files = []

        for pattern in patterns:
            files = list(self.source_dir.glob(pattern))
            project_files.extend(files)

        # Exclude the backlog file we generate
        project_files = [f for f in project_files if f.name != "MAIA_PROJECT_BACKLOG.md"]

        # Sort by name for consistent processing
        project_files.sort()

        print(f"Found {len(project_files)} project files")
        return project_files

    def extract_metadata(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Extract metadata from project markdown file."""

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            metadata = {
                'file_path': str(file_path),
                'file_name': file_path.name,
                'project_id': self._generate_project_id(file_path.name),
                'name': self._extract_title(content, file_path.name),
                'status': self._infer_status(content, file_path.name),
                'priority': self._infer_priority(content),
                'effort_hours': self._extract_effort(content),
                'impact': self._infer_impact(content),
                'category': self._infer_category(content, file_path.name),
                'description': self._extract_description(content),
                'project_plan_path': str(file_path.relative_to(MAIA_ROOT)),
                'created_date': self._get_file_creation_date(file_path)
            }

            return metadata

        except Exception as e:
            print(f"⚠️  Error parsing {file_path.name}: {e}")
            self.migration_results['warnings'].append(f"{file_path.name}: Parse error - {e}")
            return None

    def _generate_project_id(self, filename: str) -> str:
        """Generate project ID from filename."""
        # Remove extensions and common suffixes
        name = filename.replace('.md', '')
        name = re.sub(r'_(PROJECT|PLAN|IMPLEMENTATION).*', '', name)

        # Convert to uppercase with hyphens
        project_id = name.replace('_', '-').upper()

        # Limit length
        if len(project_id) > 30:
            project_id = project_id[:30]

        # Ensure it ends with a sequence number if not already
        if not re.search(r'-\d+$', project_id):
            # Use a hash of the full filename for uniqueness
            hash_suffix = abs(hash(filename)) % 1000
            project_id = f"{project_id}-{hash_suffix:03d}"

        return project_id

    def _extract_title(self, content: str, filename: str) -> str:
        """Extract project title from content."""
        # Try to find first H1 heading
        match = re.search(r'^#\s+(.+?)$', content, re.MULTILINE)
        if match:
            return match.group(1).strip()

        # Try to find title in frontmatter-style metadata
        match = re.search(r'^\*\*Project\*\*:\s*(.+?)$', content, re.MULTILINE)
        if match:
            return match.group(1).strip()

        # Fallback: Convert filename to title
        title = filename.replace('.md', '')
        title = title.replace('_', ' ').title()
        return title

    def _infer_status(self, content: str, filename: str) -> str:
        """Infer project status from content and filename."""
        # Check for explicit status markers
        if re.search(r'\*\*Status\*\*:\s*(planned|active|blocked|completed|archived)', content, re.IGNORECASE):
            match = re.search(r'\*\*Status\*\*:\s*(\w+)', content, re.IGNORECASE)
            if match:
                status = match.group(1).lower()
                if status in VALID_STATUSES:
                    return status

        # Check filename patterns
        if 'IMPLEMENTATION_PLAN' in filename or 'ACTION_PLAN' in filename:
            return 'planned'

        # Check for completion indicators in content
        if re.search(r'(complete|completed|finished|done)', content[:2000], re.IGNORECASE):
            # Check if it's in a "Status: completed" context
            if re.search(r'(status|state).*?complete', content[:2000], re.IGNORECASE):
                return 'completed'

        # Default to planned
        return 'planned'

    def _infer_priority(self, content: str) -> str:
        """Infer priority from content."""
        # Check for explicit priority markers
        match = re.search(r'\*\*Priority\*\*:\s*(critical|high|medium|low)', content, re.IGNORECASE)
        if match:
            priority = match.group(1).lower()
            if priority in VALID_PRIORITIES:
                return priority

        # Check for urgency indicators
        if re.search(r'(critical|urgent|emergency|asap)', content[:3000], re.IGNORECASE):
            return 'critical'

        if re.search(r'(high priority|important|high-priority)', content[:3000], re.IGNORECASE):
            return 'high'

        if re.search(r'(low priority|nice-to-have|optional)', content[:3000], re.IGNORECASE):
            return 'low'

        # Default to medium
        return 'medium'

    def _extract_effort(self, content: str) -> Optional[int]:
        """Extract effort estimate from content."""
        # Look for hour estimates
        patterns = [
            r'\*\*Estimated\*\*:\s*(\d+)[-\s]?hours?',
            r'\*\*Effort\*\*:\s*(\d+)[-\s]?hours?',
            r'\*\*Timeline\*\*:\s*(\d+)[-\s]?hours?',
            r'(\d+)[-\s]?hours?\s+implementation',
            r'estimated:\s*(\d+)h'
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                try:
                    hours = int(match.group(1))
                    if 1 <= hours <= 1000:  # Sanity check
                        return hours
                except ValueError:
                    continue

        return None

    def _infer_impact(self, content: str) -> Optional[str]:
        """Infer impact level from content."""
        # Check for explicit impact markers
        match = re.search(r'\*\*Impact\*\*:\s*(high|medium|low)', content, re.IGNORECASE)
        if match:
            impact = match.group(1).lower()
            if impact in VALID_IMPACTS:
                return impact

        # Check for impact indicators
        if re.search(r'(production-grade|critical|strategic|major impact)', content[:3000], re.IGNORECASE):
            return 'high'

        if re.search(r'(moderate impact|incremental|enhancement)', content[:3000], re.IGNORECASE):
            return 'medium'

        return None  # Let database default handle it

    def _infer_category(self, content: str, filename: str) -> Optional[str]:
        """Infer category from content and filename."""
        # Check filename
        if 'SERVICEDESK' in filename:
            return 'ServiceDesk'
        if 'AGENT' in filename:
            return 'Agent'
        if 'SECURITY' in filename:
            return 'Security'
        if 'ETL' in filename:
            return 'Data/ETL'
        if 'DASHBOARD' in filename:
            return 'Monitoring'
        if 'CONFLUENCE' in filename:
            return 'Productivity'

        # Check content for category markers
        categories = {
            'SRE': ['reliability', 'monitoring', 'slo', 'incident'],
            'DevOps': ['ci/cd', 'pipeline', 'deployment', 'infrastructure'],
            'Security': ['security', 'vulnerability', 'compliance'],
            'Agent': ['agent', 'orchestration', 'swarm'],
            'Documentation': ['documentation', 'guide', 'readme']
        }

        content_lower = content[:2000].lower()
        for category, keywords in categories.items():
            if any(keyword in content_lower for keyword in keywords):
                return category

        return None

    def _extract_description(self, content: str) -> Optional[str]:
        """Extract brief description from content."""
        # Try to find summary/purpose/problem section
        patterns = [
            r'\*\*Purpose\*\*:\s*(.+?)(?:\n\n|\*\*)',
            r'##\s*Purpose\s*\n(.+?)(?:\n\n|##)',
            r'\*\*Problem\*\*:\s*(.+?)(?:\n\n|\*\*)',
            r'##\s*Executive Summary\s*\n(.+?)(?:\n\n|##)',
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                description = match.group(1).strip()
                # Clean up and limit length
                description = re.sub(r'\s+', ' ', description)
                if len(description) > 200:
                    description = description[:197] + "..."
                return description

        # Fallback: Use first paragraph after title
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('# '):
                # Found title, get next non-empty line
                for j in range(i + 1, min(i + 10, len(lines))):
                    if lines[j].strip() and not lines[j].startswith('#'):
                        description = lines[j].strip()
                        if len(description) > 200:
                            description = description[:197] + "..."
                        return description

        return None

    def _get_file_creation_date(self, file_path: Path) -> str:
        """Get file creation date as ISO 8601 string."""
        stat = file_path.stat()
        # Use modification time as proxy for creation (more reliable)
        mtime = datetime.fromtimestamp(stat.st_mtime)
        return mtime.strftime('%Y-%m-%d %H:%M:%S')

    def migrate(self, dry_run: bool = True) -> bool:
        """Execute migration."""
        project_files = self.scan_project_files()

        if not project_files:
            print("No project files found to migrate")
            return False

        print(f"\n{'='*60}")
        print(f"{'DRY RUN - Preview Only' if dry_run else 'EXECUTING MIGRATION'}")
        print(f"{'='*60}\n")

        # Extract metadata from all files
        print("Extracting metadata from project files...")
        projects_to_import = []

        for file_path in project_files:
            metadata = self.extract_metadata(file_path)
            if metadata:
                projects_to_import.append(metadata)

        print(f"Parsed {len(projects_to_import)} projects successfully")

        # Check for duplicate IDs
        ids = [p['project_id'] for p in projects_to_import]
        duplicates = [id for id in ids if ids.count(id) > 1]
        if duplicates:
            print(f"\n⚠️  WARNING: Duplicate project IDs detected: {set(duplicates)}")
            print("   Will resolve by adding unique suffixes")

        if dry_run:
            self._print_preview(projects_to_import)
            return True

        # Execute import
        return self._execute_import(projects_to_import)

    def _print_preview(self, projects: List[Dict[str, Any]]):
        """Print preview of projects to be imported."""
        print(f"\n{'='*60}")
        print("MIGRATION PREVIEW")
        print(f"{'='*60}\n")

        # Group by status
        by_status = {}
        for project in projects:
            status = project['status']
            if status not in by_status:
                by_status[status] = []
            by_status[status].append(project)

        for status in ['planned', 'active', 'blocked', 'completed', 'archived']:
            if status not in by_status:
                continue

            status_projects = by_status[status]
            print(f"\n{status.upper()} ({len(status_projects)} projects):")
            print("-" * 60)

            for project in status_projects[:10]:  # Show first 10 per status
                effort = f"{project['effort_hours']}h" if project.get('effort_hours') else "?"
                priority = project['priority']
                category = project.get('category') or "General"

                print(f"  {project['project_id']}")
                print(f"    Name: {project['name'][:50]}")
                print(f"    Priority: {priority} | Effort: {effort} | Category: {category}")
                print(f"    File: {project['file_name']}")

            if len(status_projects) > 10:
                print(f"    ... and {len(status_projects) - 10} more")

        # Summary statistics
        print(f"\n{'='*60}")
        print("SUMMARY")
        print(f"{'='*60}")
        print(f"Total projects: {len(projects)}")
        print(f"By status: {', '.join(f'{len(by_status.get(s, []))} {s}' for s in VALID_STATUSES if s in by_status)}")
        print(f"With effort estimates: {sum(1 for p in projects if p.get('effort_hours'))}")
        print(f"With categories: {sum(1 for p in projects if p.get('category'))}")
        print(f"Warnings: {len(self.migration_results['warnings'])}")

        if self.migration_results['warnings']:
            print(f"\nWarnings:")
            for warning in self.migration_results['warnings'][:10]:
                print(f"  - {warning}")

    def _execute_import(self, projects: List[Dict[str, Any]]) -> bool:
        """Execute import to database."""
        print(f"\n{'='*60}")
        print("EXECUTING MIGRATION")
        print(f"{'='*60}\n")

        with ProjectRegistry() as registry:
            for project in projects:
                try:
                    # Check if already exists
                    existing = registry.conn.execute(
                        "SELECT id FROM projects WHERE id = ?",
                        (project['project_id'],)
                    ).fetchone()

                    if existing:
                        print(f"⏭️  Skipping {project['project_id']} (already exists)")
                        self.migration_results['skipped'].append(project['project_id'])
                        continue

                    # Import project
                    success = registry.add_project(
                        project_id=project['project_id'],
                        name=project['name'],
                        status=project['status'],
                        priority=project['priority'],
                        effort_hours=project.get('effort_hours'),
                        impact=project.get('impact'),
                        category=project.get('category'),
                        description=project.get('description'),
                        project_plan_path=project.get('project_plan_path')
                    )

                    if success:
                        self.migration_results['success'].append(project['project_id'])
                    else:
                        self.migration_results['failed'].append(project['project_id'])

                except Exception as e:
                    print(f"❌ Error importing {project['project_id']}: {e}")
                    self.migration_results['failed'].append(project['project_id'])

        # Print final report
        self._print_migration_report()
        return len(self.migration_results['failed']) == 0

    def _print_migration_report(self):
        """Print final migration report."""
        print(f"\n{'='*60}")
        print("MIGRATION COMPLETE")
        print(f"{'='*60}\n")

        results = self.migration_results
        total = len(results['success']) + len(results['skipped']) + len(results['failed'])

        print(f"Total projects processed: {total}")
        print(f"  ✅ Successfully migrated: {len(results['success'])}")
        print(f"  ⏭️  Skipped (already exist): {len(results['skipped'])}")
        print(f"  ❌ Failed: {len(results['failed'])}")
        print(f"  ⚠️  Warnings: {len(results['warnings'])}")

        if results['failed']:
            print(f"\nFailed projects:")
            for project_id in results['failed']:
                print(f"  - {project_id}")

        if results['warnings']:
            print(f"\nWarnings:")
            for warning in results['warnings'][:10]:
                print(f"  - {warning}")
            if len(results['warnings']) > 10:
                print(f"  ... and {len(results['warnings']) - 10} more")

        # Database statistics
        with ProjectRegistry() as registry:
            stats = registry.get_stats()
            print(f"\nDatabase Statistics:")
            print(f"  Total projects in database: {stats['overall']['total_projects']}")
            print(f"  Database location: {registry.db_path}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Migrate existing project files to Maia Project Registry",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--source-dir',
        default='claude/data',
        help='Source directory to scan for project files (default: claude/data)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview migration without importing'
    )

    parser.add_argument(
        '--confirm',
        action='store_true',
        help='Execute migration (import to database)'
    )

    args = parser.parse_args()

    # Convert to absolute path
    source_dir = args.source_dir
    if not os.path.isabs(source_dir):
        source_dir = os.path.join(MAIA_ROOT, source_dir)

    if not os.path.exists(source_dir):
        print(f"❌ Source directory not found: {source_dir}", file=sys.stderr)
        return 1

    # Run migration
    migrator = ProjectFileMigrator(source_dir)

    if args.confirm:
        success = migrator.migrate(dry_run=False)
        return 0 if success else 1
    else:
        # Default to dry-run
        migrator.migrate(dry_run=True)
        print("\n💡 Run with --confirm to execute migration")
        return 0


if __name__ == '__main__':
    sys.exit(main())
