#!/usr/bin/env python3
"""
Fix clean_database() API calls properly - changing parameter style.

Converts:
    clean_database(
        test_db, output_db,
        date_columns=[...],
        empty_string_columns=[...]
    )

To:
    clean_database(
        test_db, output_db,
        config={
            'date_columns': [...],
            'empty_to_null_columns': [...]
        }
    )
"""
import re
from pathlib import Path

def fix_clean_database_calls(content: str) -> str:
    """Fix clean_database calls to use config dict parameter."""

    # Pattern: Match clean_database call with date_columns and empty_string_columns as kwargs
    # This is a multi-line pattern
    pattern = r'''clean_database\(
        \s*([^,]+),\s*([^,]+),\s*  # source, output
        date_columns=(\[[^\]]*\]),\s*  # date_columns
        empty_string_columns=(\[[^\]]*\])  # empty_string_columns
    \s*\)'''

    def replacement(match):
        indent = match.group(0).split('clean_database')[0]
        source = match.group(1).strip()
        output = match.group(2).strip()
        date_cols = match.group(3).strip()
        empty_cols = match.group(4).strip()

        # Determine indentation level
        base_indent = len(indent)

        return f'''clean_database(
{indent}    {source}, {output},
{indent}    config={{
{indent}        'date_columns': {date_cols},
{indent}        'empty_to_null_columns': {empty_cols}
{indent}    }}
{indent})'''

    content = re.sub(pattern, replacement, content, flags=re.VERBOSE | re.DOTALL)

    return content

def main():
    test_files = [
        'tests/test_failure_injection_servicedesk_etl.py',
    ]

    for filepath in test_files:
        path = Path(filepath)
        if not path.exists():
            print(f"⚠️  {filepath} not found")
            continue

        print(f"Processing {filepath}...")
        content = path.read_text()
        original = content

        content = fix_clean_database_calls(content)

        if content != original:
            path.write_text(content)
            print(f"✅ Fixed {filepath}")

            # Test syntax
            import subprocess
            result = subprocess.run(['python3', '-m', 'py_compile', filepath], capture_output=True)
            if result.returncode == 0:
                print(f"✅ Syntax check passed for {filepath}")
            else:
                print(f"❌ Syntax errors in {filepath}:\n{result.stderr.decode()}")
        else:
            print(f"ℹ️  No changes in {filepath}")

if __name__ == '__main__':
    main()
