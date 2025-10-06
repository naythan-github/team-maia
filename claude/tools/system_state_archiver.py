#!/usr/bin/env python3
"""
Automated SYSTEM_STATE.md Archiving Tool
Moves older phases to SYSTEM_STATE_ARCHIVE.md when threshold exceeded
Integrates with RAG reindexing and maintains phase boundaries

Usage:
    python3 claude/tools/system_state_archiver.py           # Check and archive if needed
    python3 claude/tools/system_state_archiver.py --now     # Force archive now
    python3 claude/tools/system_state_archiver.py --dry-run # Preview changes only
    python3 claude/tools/system_state_archiver.py --status  # Show current stats
"""

import argparse
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional


class SystemStateArchiver:
    """Manages automated archiving of SYSTEM_STATE.md phases"""

    def __init__(self, maia_root: Optional[Path] = None):
        if maia_root is None:
            # Auto-detect from script location
            self.maia_root = Path(__file__).resolve().parent.parent.parent
        else:
            self.maia_root = Path(maia_root)

        self.system_state_path = self.maia_root / "SYSTEM_STATE.md"
        self.archive_path = self.maia_root / "SYSTEM_STATE_ARCHIVE.md"
        self.backup_dir = Path.home() / ".maia" / "backups" / "system_state"

        # Configuration
        self.threshold_lines = 1000  # Archive when exceeding this
        self.critical_threshold = 1200  # Critical - must archive immediately
        self.keep_recent_phases = 15  # Keep this many phases in main file

    def get_file_stats(self) -> dict:
        """Get current file statistics"""
        if not self.system_state_path.exists():
            raise FileNotFoundError(f"SYSTEM_STATE.md not found at {self.system_state_path}")

        lines = self.system_state_path.read_text().splitlines()

        # Count phases - look for actual phase markers (not historical references)
        phase_pattern = re.compile(r'^###\s+\*\*✅.*\*\*\s+⭐\s+\*\*.*PHASE\s+\d+', re.IGNORECASE)
        phases = [i for i, line in enumerate(lines) if phase_pattern.search(line)]

        archive_lines = 0
        archive_phases = 0
        if self.archive_path.exists():
            archive_content = self.archive_path.read_text().splitlines()
            archive_lines = len(archive_content)
            archive_phases = len([i for i, line in enumerate(archive_content)
                                if phase_pattern.search(line)])

        return {
            'current_lines': len(lines),
            'current_phases': len(phases),
            'archive_lines': archive_lines,
            'archive_phases': archive_phases,
            'needs_archiving': len(lines) > self.threshold_lines,
            'critical': len(lines) > self.critical_threshold
        }

    def parse_phases(self, content: str) -> List[Tuple[int, int, str]]:
        """
        Parse content into phases with start/end line numbers
        Returns: List of (start_line, end_line, phase_title)

        Phase format: ### **✅ [Title]** ⭐ **[SESSION] - PHASE XX**
        Sections separated by --- markers
        """
        lines = content.splitlines()

        # Match actual phase markers at end of title
        phase_pattern = re.compile(r'^###\s+\*\*✅.*\*\*\s+⭐\s+\*\*.*PHASE\s+(\d+)', re.IGNORECASE)

        phases = []
        current_phase_start = None
        current_phase_title = None

        for i, line in enumerate(lines):
            # Check for phase header
            match = phase_pattern.search(line)
            if match:
                # Save previous phase if exists
                if current_phase_start is not None:
                    phases.append((current_phase_start, i - 1, current_phase_title))

                current_phase_start = i
                current_phase_title = line.strip()
            # Check for section separator (end of phase)
            elif line.strip() == '---' and current_phase_start is not None:
                # Phase ends at separator line
                phases.append((current_phase_start, i, current_phase_title))
                current_phase_start = None
                current_phase_title = None

        # Add last phase if no closing separator
        if current_phase_start is not None:
            phases.append((current_phase_start, len(lines) - 1, current_phase_title))

        return phases

    def extract_phase_number(self, phase_title: str) -> Optional[int]:
        """Extract numeric phase number from title (at end after PHASE keyword)"""
        match = re.search(r'PHASE\s+(\d+)', phase_title, re.IGNORECASE)
        return int(match.group(1)) if match else None

    def create_backup(self) -> Path:
        """Create timestamped backup of current files"""
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        backup_main = self.backup_dir / f"SYSTEM_STATE_{timestamp}.md"
        shutil.copy2(self.system_state_path, backup_main)

        if self.archive_path.exists():
            backup_archive = self.backup_dir / f"SYSTEM_STATE_ARCHIVE_{timestamp}.md"
            shutil.copy2(self.archive_path, backup_archive)

        return backup_main

    def archive_phases(self, dry_run: bool = False) -> dict:
        """
        Archive older phases to SYSTEM_STATE_ARCHIVE.md
        Returns: Dict with archiving results
        """
        content = self.system_state_path.read_text()
        phases = self.parse_phases(content)

        if not phases:
            return {'status': 'error', 'message': 'No phases found in SYSTEM_STATE.md'}

        # Group phases by number (handle multiple subsections per phase)
        phase_groups = {}
        for start, end, title in phases:
            phase_num = self.extract_phase_number(title)
            if phase_num is not None:
                if phase_num not in phase_groups:
                    phase_groups[phase_num] = []
                phase_groups[phase_num].append((start, end, title))

        # Get unique phase numbers sorted
        unique_phases = sorted(phase_groups.keys())

        if len(unique_phases) <= self.keep_recent_phases:
            return {
                'status': 'skipped',
                'message': f'Only {len(unique_phases)} unique phases found, keeping all'
            }

        # Determine which phase NUMBERS to archive (not individual sections)
        phase_nums_to_archive = unique_phases[:-self.keep_recent_phases]
        phase_nums_to_keep = unique_phases[-self.keep_recent_phases:]

        # Flatten groups back to individual sections for archiving
        phases_to_archive = []
        for phase_num in phase_nums_to_archive:
            phases_to_archive.extend([(phase_num, s, e, t) for s, e, t in phase_groups[phase_num]])

        phases_to_keep = []
        for phase_num in phase_nums_to_keep:
            phases_to_keep.extend([(phase_num, s, e, t) for s, e, t in phase_groups[phase_num]])

        # Sort by line number for contiguous extraction
        phases_to_archive.sort(key=lambda x: x[1])
        phases_to_keep.sort(key=lambda x: x[1])

        if not phases_to_archive:
            return {'status': 'skipped', 'message': 'No phases to archive'}

        lines = content.splitlines()

        # Extract content to archive (from first phase start to last archived phase end)
        archive_start_line = phases_to_archive[0][1]
        archive_end_line = phases_to_archive[-1][2]

        # Keep header content before first phase
        header_content = '\n'.join(lines[:archive_start_line])

        # Content to archive
        content_to_archive = '\n'.join(lines[archive_start_line:archive_end_line + 1])

        # Content to keep (header + recent phases)
        keep_start_line = phases_to_keep[0][1]
        content_to_keep = header_content + '\n\n' + '\n'.join(lines[keep_start_line:])

        result = {
            'status': 'success',
            'dry_run': dry_run,
            'phases_archived': [f"Phase {p[0]}" for p in phases_to_archive],
            'phases_kept': [f"Phase {p[0]}" for p in phases_to_keep],
            'lines_archived': archive_end_line - archive_start_line + 1,
            'new_main_lines': len(content_to_keep.splitlines())
        }

        if dry_run:
            return result

        # Create backup before modifying
        backup_path = self.create_backup()
        result['backup_path'] = str(backup_path)

        try:
            # Update archive file
            if self.archive_path.exists():
                archive_content = self.archive_path.read_text()
                # Append new archived content
                new_archive = archive_content.rstrip() + '\n\n' + content_to_archive
            else:
                # Create new archive with header
                archive_header = f"""# Maia System State Archive

**Archived Phases**: Contains historical phases moved from SYSTEM_STATE.md
**Last Updated**: {datetime.now().strftime("%Y-%m-%d")}

See [SYSTEM_STATE.md](SYSTEM_STATE.md) for recent phases.

---

"""
                new_archive = archive_header + content_to_archive

            # Write atomically (write to temp, then rename)
            archive_temp = self.archive_path.with_suffix('.tmp')
            archive_temp.write_text(new_archive)
            archive_temp.replace(self.archive_path)

            # Update main file
            main_temp = self.system_state_path.with_suffix('.tmp')
            main_temp.write_text(content_to_keep)
            main_temp.replace(self.system_state_path)

            result['status'] = 'completed'

        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
            # Restore from backup
            if backup_path.exists():
                shutil.copy2(backup_path, self.system_state_path)
                result['restored_from_backup'] = True

        return result

    def trigger_rag_reindex(self) -> bool:
        """Trigger RAG reindexing after archiving"""
        try:
            rag_tool = self.maia_root / "claude" / "tools" / "system_state_rag_ollama.py"
            if rag_tool.exists():
                import subprocess
                result = subprocess.run(
                    ["python3", str(rag_tool), "--auto-reindex"],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                return result.returncode == 0
            return False
        except Exception as e:
            print(f"⚠️  RAG reindex failed: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(
        description="Automated SYSTEM_STATE.md archiving tool"
    )
    parser.add_argument(
        '--now', action='store_true',
        help='Force archiving now regardless of threshold'
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help='Preview changes without modifying files'
    )
    parser.add_argument(
        '--status', action='store_true',
        help='Show current statistics only'
    )
    parser.add_argument(
        '--threshold', type=int,
        help='Override default threshold (1000 lines)'
    )

    args = parser.parse_args()

    archiver = SystemStateArchiver()

    if args.threshold:
        archiver.threshold_lines = args.threshold

    # Show status
    stats = archiver.get_file_stats()

    print("📊 SYSTEM_STATE Status:")
    print(f"  Main file: {stats['current_lines']} lines, {stats['current_phases']} phases")
    print(f"  Archive: {stats['archive_lines']} lines, {stats['archive_phases']} phases")
    print(f"  Threshold: {archiver.threshold_lines} lines")
    print(f"  Status: {'🔴 CRITICAL' if stats['critical'] else '⚠️  Needs archiving' if stats['needs_archiving'] else '✅ OK'}")

    if args.status:
        return

    # Determine if archiving needed
    should_archive = args.now or stats['needs_archiving']

    if not should_archive:
        print("\n✅ No archiving needed")
        return

    print(f"\n{'🔍 DRY RUN:' if args.dry_run else '📦 Archiving:'} Moving older phases to archive...")

    result = archiver.archive_phases(dry_run=args.dry_run)

    if result['status'] == 'skipped':
        print(f"⏭️  {result['message']}")
        return

    if result['status'] == 'error':
        print(f"❌ Error: {result.get('error', 'Unknown error')}")
        if result.get('restored_from_backup'):
            print("   Restored from backup")
        return

    print(f"\n{'Would archive' if args.dry_run else 'Archived'}:")
    print(f"  Phases: {', '.join(result['phases_archived'])}")
    print(f"  Lines moved: {result['lines_archived']}")
    print(f"\nKept in main file:")
    print(f"  Phases: {', '.join(result['phases_kept'])}")
    print(f"  New size: {result['new_main_lines']} lines")

    if not args.dry_run:
        print(f"\n💾 Backup: {result.get('backup_path', 'N/A')}")

        # Trigger RAG reindex
        print("\n📚 Triggering RAG reindex...")
        if archiver.trigger_rag_reindex():
            print("✅ RAG reindex complete")
        else:
            print("⚠️  RAG reindex failed - run manually")

        print("\n✅ Archiving complete!")
    else:
        print("\n✅ Dry run complete - no files modified")


if __name__ == '__main__':
    main()
