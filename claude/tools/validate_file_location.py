#!/usr/bin/env python3
"""
File location validation tool for Maia file organization policy.

Usage:
    python3 validate_file_location.py <filepath> <purpose>

Example:
    python3 validate_file_location.py "claude/data/big_analysis.xlsx" "ServiceDesk analysis report"
"""

import os
import sys
from pathlib import Path
from typing import Dict, List

# Constants
MAIA_ROOT = Path(os.getenv('MAIA_ROOT', os.path.expanduser('~/git/maia')))
MAX_FILE_SIZE_MB = 10
ALLOWED_ROOT_FILES = ['CLAUDE.md', 'README.md', 'SYSTEM_STATE.md', 'SYSTEM_STATE_ARCHIVE.md']
WORK_OUTPUT_KEYWORDS = ['ServiceDesk', 'Infrastructure', 'Lance_Letran', 'L2_', 'Analysis', 'Summary']

def validate_file_location(filepath: str, file_purpose: str) -> Dict:
    """
    Validate if file should be saved to proposed location.

    Args:
        filepath: Proposed file path (relative or absolute)
        file_purpose: Description of file purpose

    Returns:
        {
            "valid": bool,
            "recommended_path": str,
            "reason": str,
            "policy_violated": str or None
        }
    """
    filepath = Path(filepath)

    # Make absolute if relative
    if not filepath.is_absolute():
        filepath = MAIA_ROOT / filepath

    # Check 1: Work output detection
    if is_work_output(file_purpose, filepath):
        project = infer_project(filepath)
        return {
            "valid": False,
            "recommended_path": f"~/work_projects/{project}/",
            "reason": "Work outputs should not be in Maia repository",
            "policy_violated": "Operational Data Separation Policy"
        }

    # Check 2: File size (if exists)
    if filepath.exists():
        size_mb = filepath.stat().st_size / (1024 * 1024)
        if size_mb > MAX_FILE_SIZE_MB and 'rag_databases' not in str(filepath):
            return {
                "valid": False,
                "recommended_path": "~/work_projects/",
                "reason": f"Files >10 MB must be in work_projects (file is {size_mb:.1f} MB)",
                "policy_violated": "Size Limit Policy"
            }

    # Check 3: UFC structure compliance
    if not matches_ufc_structure(filepath):
        recommended = get_ufc_compliant_path(filepath)
        return {
            "valid": False,
            "recommended_path": str(recommended),
            "reason": "File location violates UFC structure",
            "policy_violated": "UFC Directory Structure"
        }

    # Check 4: Root directory restriction
    if filepath.parent == MAIA_ROOT and filepath.name not in ALLOWED_ROOT_FILES:
        return {
            "valid": False,
            "recommended_path": "claude/data/project_status/active/",
            "reason": "Only 4 core files allowed in repository root",
            "policy_violated": "Root Directory Policy"
        }

    return {
        "valid": True,
        "recommended_path": str(filepath),
        "reason": "Compliant with file organization policy",
        "policy_violated": None
    }

def is_work_output(file_purpose: str, filepath: Path) -> bool:
    """Check if file is work output (not Maia system file)."""
    purpose_lower = file_purpose.lower()
    filename = filepath.name

    # Keywords indicating work output
    work_keywords = ['analysis', 'report', 'summary', 'deliverable', 'client', 'output']
    if any(keyword in purpose_lower for keyword in work_keywords):
        return True

    # Filename patterns indicating work output
    if any(keyword in filename for keyword in WORK_OUTPUT_KEYWORDS):
        return True

    return False

def matches_ufc_structure(filepath: Path) -> bool:
    """Check if file path matches UFC directory structure."""
    try:
        rel_path = filepath.relative_to(MAIA_ROOT) if filepath.is_relative_to(MAIA_ROOT) else filepath
    except ValueError:
        return False

    parts = rel_path.parts

    if len(parts) == 0:
        return False

    # Must be under claude/ directory for Maia files (or tests/)
    if parts[0] != 'claude':
        # Exception: tests/ directory
        return parts[0] in ['tests', 'docs']

    # Check second level (agents, tools, commands, context, data, hooks)
    if len(parts) < 2:
        return False

    valid_second_level = ['agents', 'tools', 'commands', 'context', 'data', 'hooks', 'extensions']
    return parts[1] in valid_second_level

def get_ufc_compliant_path(filepath: Path) -> Path:
    """Suggest UFC-compliant path for file."""
    filename = filepath.name

    # Agent files
    if filename.endswith('_agent.md'):
        return MAIA_ROOT / 'claude' / 'agents' / filename

    # Tool files
    if filename.endswith('.py') and not filename.startswith('test_'):
        return MAIA_ROOT / 'claude' / 'tools' / filename

    # Test files
    if filename.startswith('test_'):
        return MAIA_ROOT / 'tests' / filename

    # Database files
    if filename.endswith('.db'):
        return MAIA_ROOT / 'claude' / 'data' / 'databases' / 'system' / filename

    # Documentation files
    if filename.endswith('.md'):
        if 'PLAN' in filename or 'progress' in filename:
            return MAIA_ROOT / 'claude' / 'data' / 'project_status' / 'active' / filename
        if 'PHASE' in filename or 'COMPLETE' in filename:
            return MAIA_ROOT / 'claude' / 'data' / 'project_status' / 'active' / filename
        return MAIA_ROOT / 'claude' / 'data' / filename

    # Default
    return MAIA_ROOT / 'claude' / 'data' / filename

def infer_project(filepath: Path) -> str:
    """Infer project name from filepath."""
    filename = filepath.name.lower()

    if 'servicedesk' in filename:
        return 'servicedesk_analysis'
    if 'infrastructure' in filename:
        return 'infrastructure_team'
    if 'recruitment' in filename or 'l2_' in filename:
        return 'recruitment'

    return 'general'

# CLI interface
if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: validate_file_location.py <filepath> <purpose>")
        print()
        print("Example:")
        print('  validate_file_location.py "claude/data/analysis.xlsx" "ServiceDesk analysis"')
        sys.exit(1)

    result = validate_file_location(sys.argv[1], sys.argv[2])

    if result['valid']:
        print(f"✅ Valid: {result['reason']}")
        print(f"   Path: {result['recommended_path']}")
        sys.exit(0)
    else:
        print(f"❌ Invalid: {result['reason']}")
        print(f"   Recommended: {result['recommended_path']}")
        print(f"   Policy violated: {result['policy_violated']}")
        print()
        print("See: claude/context/core/file_organization_policy.md")
        sys.exit(1)
