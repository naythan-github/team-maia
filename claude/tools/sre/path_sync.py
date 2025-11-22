#!/usr/bin/env python3
"""
Path Synchronization Tool - Keep Database Paths Current

Detects when files have moved and updates references in:
- system_state.db (narrative_text column)
- capabilities.db (via re-scan)

Phase 169: Auto-Update Paths

Usage:
    # Detect stale paths in system_state.db
    python3 path_sync.py check

    # Update paths after providing a moves mapping file
    python3 path_sync.py update --moves-file /tmp/path_moves.json

    # Auto-detect moves by matching filenames
    python3 path_sync.py auto-fix

    # Full sync (capabilities scan + system_state path update)
    python3 path_sync.py sync
"""

import sqlite3
import json
import re
import argparse
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class StalePathReport:
    """Report of stale paths found in a phase"""
    phase_number: str
    stale_paths: List[str]
    suggested_fixes: Dict[str, str]  # old_path -> new_path


class PathSynchronizer:
    """
    Keeps file paths in databases synchronized with filesystem.

    Handles the case where files are moved/reorganized but database
    records still reference old paths.
    """

    # Patterns to find file paths in narrative text
    PATH_PATTERNS = [
        r'`(claude/(?:tools|agents|data|context)/[^\s`\)]+)`',  # Backtick paths
        r'(?<![`\w])(claude/(?:tools|agents|data|context)/[\w\-_/\.]+)(?![`\w])',  # Plain paths
    ]

    def __init__(self):
        self.maia_root = Path(__file__).resolve().parent.parent.parent.parent
        self.system_state_db = self.maia_root / "claude" / "data" / "databases" / "system" / "system_state.db"
        self.capabilities_db = self.maia_root / "claude" / "data" / "databases" / "system" / "capabilities.db"

    def _get_system_state_conn(self) -> sqlite3.Connection:
        """Get connection to system_state.db"""
        conn = sqlite3.connect(self.system_state_db)
        conn.row_factory = sqlite3.Row
        return conn

    def _extract_paths_from_text(self, text: str) -> Set[str]:
        """Extract all file paths from narrative text."""
        paths = set()
        for pattern in self.PATH_PATTERNS:
            matches = re.findall(pattern, text)
            paths.update(matches)
        return paths

    def _path_exists(self, rel_path: str) -> bool:
        """Check if a relative path exists."""
        full_path = self.maia_root / rel_path
        return full_path.exists()

    def _find_file_by_name(self, filename: str) -> Optional[str]:
        """Search for a file by name and return its current path."""
        # Search in common directories
        search_dirs = [
            self.maia_root / "claude" / "tools",
            self.maia_root / "claude" / "agents",
            self.maia_root / "claude" / "data",
            self.maia_root / "claude" / "context",
        ]

        for search_dir in search_dirs:
            if search_dir.exists():
                for found_path in search_dir.rglob(filename):
                    return str(found_path.relative_to(self.maia_root))

        return None

    def check_stale_paths(self) -> List[StalePathReport]:
        """
        Check all phases for stale file paths.

        Returns list of reports showing which phases have stale paths.
        """
        conn = self._get_system_state_conn()
        cursor = conn.execute("SELECT phase_number, narrative_text FROM phases WHERE narrative_text IS NOT NULL")

        reports = []

        for row in cursor:
            phase_number = row['phase_number']
            narrative = row['narrative_text'] or ''

            paths = self._extract_paths_from_text(narrative)
            stale_paths = []
            suggested_fixes = {}

            for path in paths:
                if not self._path_exists(path):
                    stale_paths.append(path)

                    # Try to find the file by name
                    filename = Path(path).name
                    new_path = self._find_file_by_name(filename)
                    if new_path:
                        suggested_fixes[path] = new_path

            if stale_paths:
                reports.append(StalePathReport(
                    phase_number=phase_number,
                    stale_paths=stale_paths,
                    suggested_fixes=suggested_fixes
                ))

        conn.close()
        return reports

    def update_paths(self, path_mapping: Dict[str, str], dry_run: bool = False) -> int:
        """
        Update paths in system_state.db narrative_text.

        Args:
            path_mapping: Dict of old_path -> new_path
            dry_run: If True, just report what would change

        Returns:
            Number of phases updated
        """
        if not path_mapping:
            print("No path mappings provided")
            return 0

        conn = self._get_system_state_conn()
        cursor = conn.execute("SELECT id, phase_number, narrative_text FROM phases WHERE narrative_text IS NOT NULL")

        updates = []

        for row in cursor:
            phase_id = row['id']
            phase_number = row['phase_number']
            narrative = row['narrative_text']

            updated_narrative = narrative
            changes_made = []

            for old_path, new_path in path_mapping.items():
                if old_path in updated_narrative:
                    updated_narrative = updated_narrative.replace(old_path, new_path)
                    changes_made.append(f"{old_path} → {new_path}")

            if changes_made:
                updates.append({
                    'id': phase_id,
                    'phase_number': phase_number,
                    'new_narrative': updated_narrative,
                    'changes': changes_made
                })

        if dry_run:
            print(f"\n🔍 DRY RUN - Would update {len(updates)} phases:\n")
            for update in updates:
                print(f"  Phase {update['phase_number']}:")
                for change in update['changes']:
                    print(f"    • {change}")
            conn.close()
            return len(updates)

        # Apply updates
        for update in updates:
            conn.execute(
                "UPDATE phases SET narrative_text = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (update['new_narrative'], update['id'])
            )
            print(f"  ✅ Updated Phase {update['phase_number']}: {len(update['changes'])} paths fixed")

        conn.commit()
        conn.close()

        return len(updates)

    def auto_fix(self, dry_run: bool = False) -> int:
        """
        Automatically detect and fix stale paths.

        Uses filename matching to find where files moved to.
        """
        print("🔍 Checking for stale paths...")
        reports = self.check_stale_paths()

        if not reports:
            print("✅ No stale paths found!")
            return 0

        # Build path mapping from suggested fixes
        path_mapping = {}
        for report in reports:
            path_mapping.update(report.suggested_fixes)

        unfixable = []
        for report in reports:
            for stale_path in report.stale_paths:
                if stale_path not in path_mapping:
                    unfixable.append((report.phase_number, stale_path))

        print(f"\n📊 Found {sum(len(r.stale_paths) for r in reports)} stale paths in {len(reports)} phases")
        print(f"   • Auto-fixable: {len(path_mapping)}")
        print(f"   • Manual review needed: {len(unfixable)}")

        if path_mapping:
            print(f"\n{'🔍 DRY RUN - ' if dry_run else ''}Updating paths...")
            updated = self.update_paths(path_mapping, dry_run=dry_run)
            print(f"\n✅ {'Would update' if dry_run else 'Updated'} {updated} phases")

        if unfixable:
            print(f"\n⚠️  Unfixable paths (files may be deleted or renamed):")
            for phase, path in unfixable[:10]:  # Show first 10
                print(f"   Phase {phase}: {path}")
            if len(unfixable) > 10:
                print(f"   ... and {len(unfixable) - 10} more")

        return len(path_mapping)

    def sync_all(self, dry_run: bool = False) -> Dict[str, int]:
        """
        Full synchronization:
        1. Re-scan capabilities.db
        2. Auto-fix paths in system_state.db

        Returns dict with counts of updates made.
        """
        results = {'capabilities': 0, 'system_state': 0}

        # Step 1: Re-scan capabilities
        print("📦 Step 1: Re-scanning capabilities database...")
        try:
            from capabilities_registry import CapabilitiesRegistry
            registry = CapabilitiesRegistry()
            agents, tools = registry.scan_all()
            results['capabilities'] = agents + tools
        except Exception as e:
            print(f"   ⚠️ Could not re-scan capabilities: {e}")

        # Step 2: Auto-fix system_state paths
        print("\n📝 Step 2: Fixing stale paths in system_state.db...")
        results['system_state'] = self.auto_fix(dry_run=dry_run)

        print(f"\n{'='*50}")
        print(f"✅ Sync complete!")
        print(f"   Capabilities refreshed: {results['capabilities']}")
        print(f"   System state paths fixed: {results['system_state']}")

        return results


def main():
    parser = argparse.ArgumentParser(description='Path Synchronization Tool')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Check command
    subparsers.add_parser('check', help='Check for stale paths')

    # Update command
    update_parser = subparsers.add_parser('update', help='Update paths from mapping file')
    update_parser.add_argument('--moves-file', required=True, help='JSON file with old->new path mapping')
    update_parser.add_argument('--dry-run', action='store_true', help='Show what would change without updating')

    # Auto-fix command
    autofix_parser = subparsers.add_parser('auto-fix', help='Automatically detect and fix moved files')
    autofix_parser.add_argument('--dry-run', action='store_true', help='Show what would change without updating')

    # Sync command
    sync_parser = subparsers.add_parser('sync', help='Full sync: capabilities + system_state paths')
    sync_parser.add_argument('--dry-run', action='store_true', help='Show what would change without updating')

    args = parser.parse_args()

    syncer = PathSynchronizer()

    if args.command == 'check':
        reports = syncer.check_stale_paths()

        if not reports:
            print("✅ No stale paths found!")
        else:
            print(f"⚠️  Found stale paths in {len(reports)} phases:\n")
            for report in reports:
                print(f"Phase {report.phase_number}:")
                for path in report.stale_paths:
                    fix = report.suggested_fixes.get(path)
                    if fix:
                        print(f"  ❌ {path}")
                        print(f"     → {fix}")
                    else:
                        print(f"  ❌ {path} (no auto-fix available)")
                print()

    elif args.command == 'update':
        with open(args.moves_file) as f:
            path_mapping = json.load(f)

        updated = syncer.update_paths(path_mapping, dry_run=args.dry_run)
        print(f"\n{'Would update' if args.dry_run else 'Updated'} {updated} phases")

    elif args.command == 'auto-fix':
        syncer.auto_fix(dry_run=args.dry_run)

    elif args.command == 'sync':
        syncer.sync_all(dry_run=args.dry_run)

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
