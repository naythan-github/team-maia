#!/usr/bin/env python3
"""
Fix clean_database() API calls to use config dictionary.

Converts:
    clean_database(source, output, date_columns=[...], empty_string_columns=[...])

To:
    clean_database(source, output, config={'date_columns': [...], 'empty_to_null_columns': [...]})
"""
import re
from pathlib import Path

def fix_cleaner_calls(content: str) -> str:
    """Fix clean_database() calls to use config parameter."""

    # Pattern 1: Match clean_database calls with date_columns and empty_string_columns
    # This pattern handles multi-line calls
    pattern = r'''clean_database\(
        \s*([^,]+),\s*  # source_db
        ([^,]+),\s*      # output_db
        date_columns=(\[[^\]]*\]),\s*  # date_columns list
        empty_string_columns=(\[[^\]]*\])  # empty_string_columns list
    \s*\)'''

    def replacement(match):
        source = match.group(1).strip()
        output = match.group(2).strip()
        date_cols = match.group(3).strip()
        empty_cols = match.group(4).strip()

        return f'''clean_database(
            {source},
            {output},
            config={{
                'date_columns': {date_cols},
                'empty_to_null_columns': {empty_cols}
            }}
        )'''

    content = re.sub(pattern, replacement, content, flags=re.VERBOSE | re.MULTILINE)

    # Pattern 2: Single-line format
    pattern2 = r'clean_database\(([^,]+),\s*([^,]+),\s*date_columns=(\[[^\]]+\]),\s*empty_string_columns=(\[[^\]]+\])\)'

    def replacement2(match):
        source = match.group(1).strip()
        output = match.group(2).strip()
        date_cols = match.group(3).strip()
        empty_cols = match.group(4).strip()

        return f"clean_database({source}, {output}, config={{'date_columns': {date_cols}, 'empty_to_null_columns': {empty_cols}}})"

    content = re.sub(pattern2, replacement2, content)

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

        # Fix cleaner calls
        content = fix_cleaner_calls(content)

        if content != original_content:
            path.write_text(content)
            print(f"✅ Fixed {filepath}")
        else:
            print(f"ℹ️  No changes needed in {filepath}")

    print("\n✅ All test files updated!")

if __name__ == '__main__':
    main()
