#!/usr/bin/env python3
"""
Pre-commit hook: File organization policy enforcement.

Prevents commits that violate file organization policy.

Installation:
  ln -s ../../claude/hooks/pre_commit_file_organization.py .git/hooks/pre-commit
  chmod +x .git/hooks/pre-commit

Bypass (if urgent):
  git commit --no-verify
"""

import sys
import subprocess
from pathlib import Path

# Configuration
MAIA_ROOT = Path(__file__).parent.parent.parent
ALLOWED_ROOT_FILES = ['CLAUDE.md', 'README.md', 'SYSTEM_STATE.md', 'SYSTEM_STATE_ARCHIVE.md', '.gitignore']
ALLOWED_ROOT_DIRS = ['${MAIA_ROOT}', "get_path_manager().get_path('backup') "]  # Path manager directories
WORK_OUTPUT_PATTERNS = ['ServiceDesk', 'Infrastructure', 'Lance_Letran', 'L2_']
MAX_FILE_SIZE_MB = 10

def get_staged_files():
    """Get list of staged files."""
    try:
        result = subprocess.run(
            ['git', 'diff', '--cached', '--name-only'],
            capture_output=True,
            text=True,
            check=True
        )
        files = [f for f in result.stdout.strip().split('\n') if f]
        # Strip workspace prefix (e.g., 'maia/') if present
        return [f.split('/', 1)[1] if '/' in f and not f.startswith('claude/') and not f.startswith('tests/') else f for f in files]
    except subprocess.CalledProcessError:
        return []

def check_violations():
    """Check for file organization violations."""
    violations = []
    staged_files = get_staged_files()

    for file in staged_files:
        filepath = MAIA_ROOT / file

        # Skip if file doesn't exist (deletion)
        if not filepath.exists():
            continue

        # Skip git files and hidden files
        if file.startswith('.git/') or file.startswith('.'):
            continue

        # Check 1: Work outputs in Maia repo
        filename = filepath.name
        if any(pattern in filename for pattern in WORK_OUTPUT_PATTERNS):
            if file.startswith('claude/data'):
                violations.append(
                    f"❌ {file} - Work output in Maia repo (move to ~/work_projects/)"
                )

        # Check 2: Files >10 MB
        try:
            size_mb = filepath.stat().st_size / (1024 * 1024)
            if size_mb > MAX_FILE_SIZE_MB and 'rag_databases' not in file:
                violations.append(
                    f"❌ {file} - File >10 MB ({size_mb:.1f} MB) (move to ~/work_projects/)"
                )
        except OSError:
            pass  # File might not be accessible

        # Check 3: Root directory pollution
        if '/' not in file:  # File is in root
            if filename not in ALLOWED_ROOT_FILES and filename not in ALLOWED_ROOT_DIRS:
                violations.append(
                    f"❌ {file} - Not allowed in root (move to appropriate subdirectory)"
                )

        # Check 4: Databases not in databases/
        if filename.endswith('.db'):
            if 'databases/' not in file and 'rag_databases' not in file:
                violations.append(
                    f"❌ {file} - Database not in claude/data/databases/ subdirectory"
                )

    return violations

def main():
    """Main execution."""
    violations = check_violations()

    if violations:
        print("\n🚨 FILE ORGANIZATION POLICY VIOLATIONS:\n")
        for v in violations:
            print(v)
        print("\n📚 Policy: claude/context/core/file_organization_policy.md")
        print("🔧 Bypass (if urgent): git commit --no-verify")
        print()
        return 1

    return 0

if __name__ == '__main__':
    sys.exit(main())
