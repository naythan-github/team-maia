#!/usr/bin/env python3
"""
Fix indentation issues caused by clean_database config parameter changes.
"""
import re
from pathlib import Path

def fix_indentation(content: str) -> str:
    """Fix clean_database call indentation issues."""

    # Pattern: Find clean_database calls with wrong indentation
    # Looking for pattern where clean_database( starts at wrong indent
    lines = content.split('\n')
    fixed_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check if this is a messed up clean_database call
        # Pattern: line ending with = clean_database(, followed by line with wrong indent
        if re.match(r'\s+result = clean_database\(', line):
            # Get base indentation
            base_indent = len(line) - len(line.lstrip())

            # Collect all lines of this call
            call_lines = [line]
            i += 1

            # Collect until we find the closing parenthesis
            paren_count = line.count('(') - line.count(')')

            while i < len(lines) and paren_count > 0:
                next_line = lines[i]
                call_lines.append(next_line)
                paren_count += next_line.count('(') - next_line.count(')')
                i += 1

            # Re-format this call
            fixed_lines.append(f"{' ' * base_indent}result = clean_database(")
            fixed_lines.append(f"{' ' * (base_indent + 4)}test_db,")
            fixed_lines.append(f"{' ' * (base_indent + 4)}output_db,")
            fixed_lines.append(f"{' ' * (base_indent + 4)}config={{")

            # Extract date_columns and empty_to_null_columns from the call
            full_call = '\n'.join(call_lines)

            # Extract date_columns
            date_match = re.search(r"'date_columns':\s*(\[[^\]]*\])", full_call)
            if date_match:
                date_cols = date_match.group(1)
                fixed_lines.append(f"{' ' * (base_indent + 8)}'date_columns': {date_cols},")

            # Extract empty_to_null_columns
            empty_match = re.search(r"'empty_to_null_columns':\s*(\[[^\]]*\])", full_call)
            if empty_match:
                empty_cols = empty_match.group(1)
                fixed_lines.append(f"{' ' * (base_indent + 8)}'empty_to_null_columns': {empty_cols}")

            fixed_lines.append(f"{' ' * (base_indent + 4)}}}")
            fixed_lines.append(f"{' ' * base_indent})")

            continue

        fixed_lines.append(line)
        i += 1

    return '\n'.join(fixed_lines)

def main():
    filepath = 'tests/test_failure_injection_servicedesk_etl.py'
    path = Path(filepath)

    if not path.exists():
        print(f"⚠️  {filepath} not found")
        return

    print(f"Processing {filepath}...")
    content = path.read_text()

    # Try to fix
    content = fix_indentation(content)

    # Write back
    path.write_text(content)
    print(f"✅ Fixed {filepath}")

    # Verify syntax
    import subprocess
    result = subprocess.run(['python3', '-m', 'py_compile', filepath], capture_output=True)
    if result.returncode == 0:
        print("✅ Syntax check passed!")
    else:
        print(f"❌ Syntax errors remain:\n{result.stderr.decode()}")

if __name__ == '__main__':
    main()
