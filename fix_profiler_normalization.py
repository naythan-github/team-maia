#!/usr/bin/env python3
"""
Add normalize_profiler_result() calls to all profiler result assertions.
"""
import re
from pathlib import Path

def add_profiler_normalization(content: str) -> str:
    """Add normalization after profile_database() calls."""

    # Pattern: Find profile_database() calls followed by assert result['status']
    # that don't already have normalization

    # First, find all profile_database calls without normalization
    pattern = r'''(result\s*=\s*profile_database\([^)]+\))
(\s+)
(assert\s+result\['status'\]\s*==\s*'success')'''

    def replacement(match):
        profile_call = match.group(1)
        indent = match.group(2)
        assert_line = match.group(3)

        # Check if normalization is already there
        if 'normalize_profiler_result' in profile_call:
            return match.group(0)  # Already normalized

        # Add normalization
        return f'''{profile_call}
{indent}result = normalize_profiler_result(result)
{indent}{assert_line}'''

    content = re.sub(pattern, replacement, content, flags=re.VERBOSE)

    return content

def main():
    test_files = [
        'tests/test_performance_servicedesk_etl.py',
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
        content = add_profiler_normalization(content)

        if content != original_content:
            path.write_text(content)
            print(f"✅ Fixed {filepath}")
        else:
            print(f"ℹ️  No changes needed in {filepath}")

    print("\n✅ All test files updated!")

if __name__ == '__main__':
    main()
