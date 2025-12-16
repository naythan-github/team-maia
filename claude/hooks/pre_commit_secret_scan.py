#!/usr/bin/env python3
"""
Pre-Commit Secret Scanning Hook
Scans staged files for secrets before allowing commits.

Installation:
    1. Copy or symlink to .git/hooks/pre-commit
    2. Or add to Claude Code hooks in settings

Usage:
    python3 pre_commit_secret_scan.py
"""

import sys
from pathlib import Path

# Add maia root to path
MAIA_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(MAIA_ROOT))

from claude.tools.security.hook_integration import check_staged_files_for_secrets


def main():
    """Run pre-commit secret scan"""
    result = check_staged_files_for_secrets()

    if result['blocked']:
        print(f"🚨 SECRETS DETECTED - Commit blocked")
        print(f"   Found {result['total_findings']} secret(s) in {len(result['files_with_secrets'])} file(s)")
        print()

        for detail in result['details']:
            print(f"📁 {detail['file']}:")
            for finding in detail['findings']:
                severity = finding.get('severity', 'unknown').upper()
                line = finding.get('line', 'N/A')
                desc = finding.get('description', 'Unknown secret type')
                print(f"   [{severity}] Line {line}: {desc}")
            print()

        print("❌ Remove secrets before committing.")
        print("   Use environment variables or the MCP credential manager instead.")
        return 1

    # Silent success - don't pollute git output
    return 0


if __name__ == '__main__':
    sys.exit(main())
