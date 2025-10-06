#!/usr/bin/env python3
"""
Deduplicate SYSTEM_STATE.md by removing duplicate phase sections.
Keeps only the first occurrence of each phase.
"""

import re
from pathlib import Path
from datetime import datetime
import shutil


def deduplicate_system_state():
    """Remove duplicate phases from SYSTEM_STATE.md"""

    maia_root = Path(__file__).resolve().parent.parent.parent
    system_state_path = maia_root / "SYSTEM_STATE.md"

    # Backup first
    backup_dir = Path.home() / ".maia" / "backups" / "system_state"
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"SYSTEM_STATE_before_dedup_{timestamp}.md"
    shutil.copy2(system_state_path, backup_path)
    print(f"💾 Backup created: {backup_path}")

    # Read file
    content = system_state_path.read_text()
    lines = content.splitlines()

    # Find all phase sections
    phase_pattern = re.compile(r'^###\s+\*\*✅.*\*\*\s+⭐\s+\*\*.*PHASE\s+(\d+)', re.IGNORECASE)

    seen_phases = set()
    output_lines = []
    current_phase_num = None
    current_phase_lines = []
    skip_current_phase = False
    in_header = True

    for line in lines:
        match = phase_pattern.search(line)

        if match:
            # Save previous phase if it wasn't a duplicate
            if current_phase_num is not None and not skip_current_phase:
                output_lines.extend(current_phase_lines)

            # Start new phase
            current_phase_num = int(match.group(1))

            # Check if we've seen this phase number before
            if current_phase_num in seen_phases:
                print(f"🗑️  Skipping duplicate: Phase {current_phase_num}")
                skip_current_phase = True
            else:
                print(f"✅ Keeping: Phase {current_phase_num}")
                seen_phases.add(current_phase_num)
                skip_current_phase = False

            current_phase_lines = [line]
            in_header = False

        elif line.strip() == '---' and current_phase_num is not None:
            # End of phase section
            current_phase_lines.append(line)

            if not skip_current_phase:
                output_lines.extend(current_phase_lines)

            current_phase_num = None
            current_phase_lines = []
            skip_current_phase = False

        elif in_header:
            # Before first phase - always keep
            output_lines.append(line)

        elif current_phase_num is not None:
            # Part of current phase
            current_phase_lines.append(line)

        else:
            # Between phases or after - always keep
            output_lines.append(line)

    # Don't forget last phase if no closing ---
    if current_phase_num is not None and not skip_current_phase:
        output_lines.extend(current_phase_lines)

    # Write deduplicated content
    new_content = '\n'.join(output_lines)
    system_state_path.write_text(new_content)

    # Stats
    original_lines = len(lines)
    new_lines = len(output_lines)
    removed_lines = original_lines - new_lines

    print(f"\n📊 Deduplication complete:")
    print(f"  Original: {original_lines} lines")
    print(f"  Deduplicated: {new_lines} lines")
    print(f"  Removed: {removed_lines} lines ({removed_lines/original_lines*100:.1f}%)")
    print(f"  Unique phases: {len(seen_phases)}")


if __name__ == '__main__':
    deduplicate_system_state()
