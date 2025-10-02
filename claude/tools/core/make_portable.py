#!/usr/bin/env python3
"""
Maia Portability Fixer

Automatically replaces hardcoded /Users/naythan/ paths with portable path resolution.
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple


def find_files_with_hardcoded_paths(root_dir: Path) -> List[Path]:
    """Find all files containing hardcoded /Users/naythan/ paths."""
    files_to_fix = []

    for pattern in ['**/*.py', '**/*.md', '**/*.json', '**/*.yaml', '**/*.yml']:
        for file_path in root_dir.glob(pattern):
            if file_path.is_file():
                try:
                    content = file_path.read_text(encoding='utf-8')
                    if '/Users/naythan/' in content:
                        files_to_fix.append(file_path)
                except Exception:
                    pass  # Skip files that can't be read

    return sorted(set(files_to_fix))


def fix_python_file(file_path: Path) -> Tuple[bool, str]:
    """
    Fix hardcoded paths in Python file.

    Returns: (success, message)
    """
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content

        # Pattern 1: Direct path assignments
        # Before: path = str(Path(__file__).resolve().parents[4 if 'claude/tools' in str(__file__) else 0] / 'claude' / 'data' / 'jobs.db'
        # After:  from claude.tools.core.path_manager import get_database_path
        #         path = get_database_path('jobs.db')

        # Pattern 2: Path() constructor
        # Before: Path('${MAIA_ROOT}/claude/tools')
        # After:  from claude.tools.core.path_manager import get_tools_dir
        #         get_tools_dir()

        # For now, do simple replacement - keep old structure but make paths dynamic
        replacements = [
            # Replace hardcoded maia root
            (r"str(Path(__file__).resolve().parents[4] if 'claude/tools' in str(__file__) else Path.cwd())", "str(Path(__file__).resolve().parents[4] if 'claude/tools' in str(__file__) else Path.cwd())"),
            (r'str(Path(__file__).resolve().parents[4] if "claude/tools" in str(__file__) else Path.cwd())', 'str(Path(__file__).resolve().parents[4] if "claude/tools" in str(__file__) else Path.cwd())'),

            # Replace specific subdirectories with dynamic resolution
            (r"str(Path(__file__).resolve().parents[4 if 'claude/tools' in str(__file__) else 0] / 'claude' / 'data' / '", "str(Path(__file__).resolve().parents[4 if 'claude/tools' in str(__file__) else 0] / 'claude' / 'data' / '"),
            (r'str(Path(__file__).resolve().parents[4 if "claude/tools" in str(__file__) else 0] / "claude" / "data" / "', 'str(Path(__file__).resolve().parents[4 if "claude/tools" in str(__file__) else 0] / "claude" / "data" / "'),

            (r"str(Path(__file__).resolve().parents[4 if 'claude/tools' in str(__file__) else 0] / 'claude' / 'tools' / '", "str(Path(__file__).resolve().parents[4 if 'claude/tools' in str(__file__) else 0] / 'claude' / 'tools' / '"),
            (r'str(Path(__file__).resolve().parents[4 if "claude/tools" in str(__file__) else 0] / "claude" / "tools" / "', 'str(Path(__file__).resolve().parents[4 if "claude/tools" in str(__file__) else 0] / "claude" / "tools" / "'),
        ]

        for pattern, replacement in replacements:
            content = re.sub(pattern, replacement, content)

        # Simpler approach: Just use path_manager for the most common case
        if str(Path(__file__).resolve().parents[4] if 'claude/tools' in str(__file__) else Path.cwd()) in content:
            # Add import if not present
            if 'from claude.tools.core.path_manager import' not in content:
                # Find first import or add at top
                lines = content.split('\n')
                import_idx = 0
                for i, line in enumerate(lines):
                    if line.startswith('import ') or line.startswith('from '):
                        import_idx = i + 1
                if import_idx > 0:
                    lines.insert(import_idx, 'from claude.tools.core.path_manager import get_maia_root')
                    content = '\n'.join(lines)

            # Replace remaining hardcoded paths
            content = content.replace("str(Path(__file__).resolve().parents[4] if 'claude/tools' in str(__file__) else Path.cwd())", "str(get_maia_root())")
            content = content.replace('str(Path(__file__).resolve().parents[4] if "claude/tools" in str(__file__) else Path.cwd())', 'str(get_maia_root())')

        if content != original_content:
            file_path.write_text(content, encoding='utf-8')
            return True, f"Fixed {len(original_content) - len(content)} characters"
        else:
            return False, "No changes needed"

    except Exception as e:
        return False, f"Error: {str(e)}"


def fix_non_python_file(file_path: Path) -> Tuple[bool, str]:
    """
    Fix hardcoded paths in non-Python files (MD, JSON, YAML).
    Just replace the username but keep the structure.

    Returns: (success, message)
    """
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content

        # For documentation and config files, we can't use Python code
        # So we use an environment variable placeholder
        content = content.replace(str(Path(__file__).resolve().parents[4] if 'claude/tools' in str(__file__) else Path.cwd()), '${MAIA_ROOT}')

        if content != original_content:
            file_path.write_text(content, encoding='utf-8')
            count = original_content.count('/Users/naythan/') - content.count('/Users/naythan/')
            return True, f"Replaced {count} paths with ${{MAIA_ROOT}}"
        else:
            return False, "No changes needed"

    except Exception as e:
        return False, f"Error: {str(e)}"


def main():
    """Main function to fix all hardcoded paths."""
    print("🔧 Maia Portability Fixer")
    print("=" * 70)

    # Get Maia root (current directory)
    maia_root = Path.cwd()
    if not (maia_root / 'claude').exists():
        print("❌ Error: Must run from Maia root directory")
        sys.exit(1)

    print(f"📁 Maia Root: {maia_root}")
    print()

    # Find files to fix
    print("🔍 Finding files with hardcoded paths...")
    files_to_fix = find_files_with_hardcoded_paths(maia_root)
    print(f"   Found {len(files_to_fix)} files")
    print()

    if not files_to_fix:
        print("✅ No files need fixing!")
        return

    # Fix files
    print("🔨 Fixing files...")
    fixed_count = 0
    skipped_count = 0
    error_count = 0

    for file_path in files_to_fix:
        relative_path = file_path.relative_to(maia_root)

        if file_path.suffix == '.py':
            success, message = fix_python_file(file_path)
        else:
            success, message = fix_non_python_file(file_path)

        if success:
            print(f"   ✅ {relative_path}")
            fixed_count += 1
        elif 'Error' in message:
            print(f"   ❌ {relative_path}: {message}")
            error_count += 1
        else:
            print(f"   ⏭️  {relative_path}: {message}")
            skipped_count += 1

    print()
    print("=" * 70)
    print("📊 Summary:")
    print(f"   ✅ Fixed: {fixed_count}")
    print(f"   ⏭️  Skipped: {skipped_count}")
    print(f"   ❌ Errors: {error_count}")
    print("=" * 70)

    if fixed_count > 0:
        print()
        print("✨ Maia is now portable!")
        print("   You can copy the directory anywhere and it will work.")
        print()
        print("💡 Optional: Set MAIA_ROOT environment variable:")
        print("   export MAIA_ROOT=\"/path/to/maia\"")


if __name__ == '__main__':
    main()
