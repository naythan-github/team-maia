#!/usr/bin/env python3
"""
Remove duplicate normalize_profiler_result() calls.
"""
import re
from pathlib import Path

def remove_duplicates(content: str) -> str:
    """Remove consecutive duplicate normalization lines."""

    # Pattern: Two consecutive normalization calls
    pattern = r'(\s+result = normalize_profiler_result\(result\))\n\s+result = normalize_profiler_result\(result\)'

    # Replace with single call
    content = re.sub(pattern, r'\1', content)

    return content

def main():
    test_files = [
        'tests/test_stress_servicedesk_etl.py',
        'tests/test_failure_injection_servicedesk_etl.py',
        'tests/test_regression_phase1_servicedesk_etl.py',
    ]

    for filepath in test_files:
        path = Path(filepath)
        if not path.exists():
            continue

        content = path.read_text()
        original = content

        content = remove_duplicates(content)

        if content != original:
            path.write_text(content)
            removed = original.count('normalize_profiler_result') - content.count('normalize_profiler_result')
            print(f"✅ Fixed {filepath} (removed {removed} duplicates)")
        else:
            print(f"ℹ️  No duplicates in {filepath}")

if __name__ == '__main__':
    main()
