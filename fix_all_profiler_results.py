#!/usr/bin/env python3
"""
Add normalize_profiler_result() to ALL profile_database() result assignments.
"""
import re
from pathlib import Path

def add_normalization_after_profiler(content: str) -> str:
    """Add normalization immediately after EVERY profile_database() assignment."""

    # Pattern: result = profile_database(...)
    # Add normalization on next line if not already there
    lines = content.split('\n')
    new_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]
        new_lines.append(line)

        # Check if this line assigns profile_database result
        if re.match(r'\s+result\s*=\s*profile_database\(', line):
            # Check if next line is already normalization
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                if 'normalize_profiler_result' not in next_line:
                    # Extract indentation from current line
                    indent = len(line) - len(line.lstrip())
                    indent_str = line[:indent]

                    # Add normalization line
                    new_lines.append(f"{indent_str}result = normalize_profiler_result(result)")

        i += 1

    return '\n'.join(new_lines)

def main():
    test_files = [
        'tests/test_stress_servicedesk_etl.py',
        'tests/test_failure_injection_servicedesk_etl.py',
        'tests/test_regression_phase1_servicedesk_etl.py',
    ]

    for filepath in test_files:
        path = Path(filepath)
        if not path.exists():
            print(f"⚠️  {filepath} not found, skipping")
            continue

        print(f"Processing {filepath}...")
        content = path.read_text()
        original_content = content

        # Add normalization
        content = add_normalization_after_profiler(content)

        if content != original_content:
            # Count how many normalizations were added
            added = content.count('normalize_profiler_result') - original_content.count('normalize_profiler_result')
            path.write_text(content)
            print(f"✅ Fixed {filepath} (added {added} normalizations)")
        else:
            print(f"ℹ️  No changes needed in {filepath}")

    print("\n✅ All test files updated!")

if __name__ == '__main__':
    main()
