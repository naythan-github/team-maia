#!/usr/bin/env python3
"""
Pre-commit hook for UFC compliance validation.
Prevents commits that violate UFC structure.
"""

import sys
import subprocess
from pathlib import Path
from typing import List, Tuple

def get_staged_files() -> List[Path]:
    """Get list of staged files from git."""
    try:
        result = subprocess.run(
            ['git', 'diff', '--cached', '--name-only'],
            capture_output=True,
            text=True,
            check=True
        )
        return [Path(f) for f in result.stdout.strip().split('\n') if f]
    except subprocess.CalledProcessError:
        return []

def validate_ufc_compliance(file_path: Path) -> Tuple[bool, str]:
    """Validate file against UFC structure rules."""
    try:
        # Skip files outside claude/ directory
        if 'claude' not in file_path.parts:
            return True, "Outside claude directory"

        # Protect critical system files from being moved
        if str(file_path) == 'claude/context/ufc_system.md':
            return True, "Protected system file - correct location"

        # Find claude/ index in path
        claude_index = file_path.parts.index('claude')
        relative_parts = file_path.parts[claude_index + 1:]

        if not relative_parts:
            return True, "Claude root file"

        # Check valid top-level directories
        valid_top_level = {'context', 'agents', 'commands', 'tools', 'hooks', 'data'}
        if relative_parts[0] not in valid_top_level:
            return False, f"Invalid top-level directory: {relative_parts[0]}"

        # Context directory rules - DOCUMENTATION ONLY
        if relative_parts[0] == 'context':
            # CRITICAL: No executable Python files in context directories
            if file_path.suffix == '.py':
                return False, f"Python files not allowed in context directories - move to claude/tools/"

            if len(relative_parts) > 6:  # Allow up to 5 levels: context/category/subcategory/domain/subdomain/file
                return False, "Context directory exceeds 5-level depth limit"
            elif len(relative_parts) > 4:  # 4-5 levels should be justified
                path_str = '/'.join(relative_parts).lower()
                justified_domains = ['session/analytics', 'knowledge/', 'projects/']
                if not any(domain in path_str for domain in justified_domains):
                    return False, "4-5 level nesting should be justified by domain complexity"

            # Check valid context categories
            valid_context = {'core', 'projects', 'tools', 'personal', 'knowledge', 'session'}
            if len(relative_parts) > 1 and relative_parts[1] not in valid_context:
                return False, f"Invalid context category: {relative_parts[1]}"

        # Commands directory rules - WORKFLOWS ONLY
        elif relative_parts[0] == 'commands':
            # CRITICAL: No executable Python files in commands directories
            if file_path.suffix == '.py':
                return False, f"Python files not allowed in commands directory - move to claude/tools/"
            # Only allow markdown workflow definitions
            if file_path.suffix not in {'.md', '.txt'}:
                return False, f"Commands directory only allows .md workflow definitions"

        # File naming conventions
        filename = file_path.name.lower()

        # Prevent common anti-patterns
        anti_patterns = [
            ('temp', 'Temporary files should not be committed'),
            ('test_', 'Test files should follow proper naming in tools/'),
            ('.tmp', 'Temporary files should not be committed'),
            ('untitled', 'Files should have descriptive names'),
        ]

        for pattern, message in anti_patterns:
            if pattern in filename and 'tools/' not in str(file_path):
                return False, message

        return True, "Valid UFC structure"

    except Exception as e:
        return False, f"Validation error: {str(e)}"

def check_file_organization(file_path: Path) -> Tuple[bool, str]:
    """Check if file is in the most appropriate UFC location."""
    filename = file_path.name.lower()
    path_str = str(file_path).lower()

    # Job-related files should be in job_search project or career knowledge (but tools can stay in tools/)
    if any(term in filename for term in ['job', 'career', 'linkedin', 'seek']):
        if ('context/projects/job_search' not in path_str and
            'context/knowledge/career' not in path_str and
            'tools/' not in path_str and
            'agents/' not in path_str and
            'data/' not in path_str and
            'context/session' not in path_str and
            'collateral/' not in path_str):
            return False, "Job-related files should be in context/projects/job_search/ or context/knowledge/career/"

    # Analysis files should be in knowledge or session (but not command files)
    if ('analysis' in filename and 'context/' not in path_str and
        'commands/' not in path_str and not filename.endswith('.md')):
        return False, "Analysis files should be in context/knowledge/ or context/session/"

    # Config files should be in context/tools/config
    if filename.endswith('.json') and 'config' in filename and 'context/tools/config' not in path_str:
        return False, "Config files should be in context/tools/config/"

    # Log files should be in session/analytics
    if filename.endswith('.log') and 'context/session/analytics' not in path_str:
        return False, "Log files should be in context/session/analytics/"

    return True, "Appropriate location"

def main():
    """Main pre-commit validation."""
    staged_files = get_staged_files()
    if not staged_files:
        sys.exit(0)

    violations = []

    for file_path in staged_files:
        # Skip deleted files
        if not file_path.exists():
            continue

        # Skip binary files and specific exceptions
        if file_path.suffix in {'.db', '.pickle', '.pyc', '.so'}:
            continue

        if file_path.name in {'.DS_Store', '.gitignore', 'requirements.txt'}:
            continue

        # Validate UFC compliance
        is_valid, message = validate_ufc_compliance(file_path)
        if not is_valid:
            violations.append(f"❌ {file_path}: {message}")
            continue

        # Check file organization
        is_organized, org_message = check_file_organization(file_path)
        if not is_organized:
            violations.append(f"⚠️  {file_path}: {org_message}")

    if violations:
        print("🚨 UFC Structure Violations Detected:")
        print()
        for violation in violations:
            print(violation)
        print()
        print("💡 Fix violations before committing:")
        print("   - Move files to appropriate UFC locations")
        print("   - Use claude/tools/ufc_paths.py for proper routing")
        print("   - Follow optimized nesting guidelines (3 levels preferred, 4-5 where justified)")
        print()
        sys.exit(1)

    print("✅ UFC structure compliance verified")
    sys.exit(0)

if __name__ == '__main__':
    main()
