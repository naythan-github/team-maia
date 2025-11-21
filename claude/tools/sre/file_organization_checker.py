#!/usr/bin/env python3
"""
File Organization Checker - Repository Compliance Validation
=============================================================

Purpose: Comprehensive file organization policy validation for save_state workflow.
         Validates work output separation, root directory restrictions, size limits,
         and database categorization.

Integration: Called by claude/commands/save_state.md Phase 2.2 (System Health Check)

Checks:
1. Root directory restrictions (only 4 core files allowed)
2. Work output separation (no work outputs in Maia repo)
3. File size limits (>10 MB must be in ~/work_projects/)
4. Database categorization (claude/data/databases/{category}/)
5. Phase documentation archival (>30 days → archive/)

Created: 2025-11-17 (Phase 151.1 - Write Tool Guidance Enhancement)
Related: claude/context/core/file_organization_policy.md
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Maia root
MAIA_ROOT = Path.home() / "git" / "maia"

# File organization policy rules
ALLOWED_ROOT_FILES = [
    'CLAUDE.md',
    'README.md',
    'SYSTEM_STATE.md',
    'SYSTEM_STATE_ARCHIVE.md',
    '.gitignore',
]

WORK_OUTPUT_PATTERNS = [
    'ServiceDesk',
    'Infrastructure',
    'Lance_Letran',
    'L2_',
    'Analysis',
    'Summary',
    'Report',
    'Deliverable'
]

MAX_FILE_SIZE_MB = 10
PHASE_ARCHIVE_DAYS = 30

DATABASE_CATEGORIES = ['intelligence', 'system', 'user', 'archive']

# Exceptions
RAG_DATABASE_PATH = 'claude/data/rag_databases'
ALLOWED_LARGE_FILES = [RAG_DATABASE_PATH]


class FileOrgCheckResult:
    """File organization check result"""
    def __init__(self, passed: bool, severity: str, violations: List[Dict]):
        self.passed = passed
        self.severity = severity  # critical, warning, info
        self.violations = violations

    def should_block_save_state(self) -> bool:
        """Determine if violations should block save state"""
        return not self.passed and self.severity == 'critical'


class FileOrganizationChecker:
    """Repository file organization compliance validation"""

    def __init__(self, maia_root: Path, verbose: bool = False):
        self.maia_root = maia_root
        self.verbose = verbose
        self.results: Dict[str, FileOrgCheckResult] = {}
        self.stats = {
            'total_files_scanned': 0,
            'root_violations': 0,
            'work_output_violations': 0,
            'size_violations': 0,
            'database_violations': 0,
            'archive_candidates': 0
        }

    def _log(self, message: str):
        """Log if verbose"""
        if self.verbose:
            print(f"[FileOrg] {message}")

    def check_root_directory(self) -> FileOrgCheckResult:
        """Check root directory only contains allowed files"""
        self._log("Checking root directory restrictions...")

        violations = []

        if not self.maia_root.exists():
            return FileOrgCheckResult(False, 'critical', [{
                'type': 'MISSING_MAIA_ROOT',
                'message': f'Maia root not found: {self.maia_root}'
            }])

        # Scan root directory
        for item in self.maia_root.iterdir():
            # Skip hidden files and directories
            if item.name.startswith('.'):
                continue

            # Skip allowed directories
            if item.is_dir():
                continue

            # Check if file is allowed in root
            if item.name not in ALLOWED_ROOT_FILES:
                violations.append({
                    'type': 'ROOT_VIOLATION',
                    'severity': 'critical',
                    'file': item.name,
                    'message': f'File not allowed in root: {item.name}',
                    'recommendation': self._get_root_file_recommendation(item)
                })
                self.stats['root_violations'] += 1

        passed = len(violations) == 0
        severity = 'critical' if violations else 'info'

        return FileOrgCheckResult(passed, severity, violations)

    def _get_root_file_recommendation(self, file_path: Path) -> str:
        """Get recommendation for misplaced root file"""
        name = file_path.name.lower()

        if name.endswith('.md'):
            if 'phase' in name or 'complete' in name:
                return 'Move to: claude/data/project_status/archive/2025-Q4/'
            elif 'plan' in name or 'backlog' in name:
                return 'Move to: claude/data/project_status/active/'
            else:
                return 'Move to: claude/data/project_status/archive/2025-Q4/'

        elif name.endswith('.py'):
            if 'fix' in name or 'test' in name:
                return 'Move to: ~/work_projects/cleanup_scripts/'
            else:
                return 'Move to: claude/tools/ or ~/work_projects/'

        else:
            return 'Move to appropriate subdirectory or delete if obsolete'

    def check_work_output_separation(self) -> FileOrgCheckResult:
        """Check work outputs are not in Maia repository"""
        self._log("Checking work output separation...")

        violations = []

        # Scan claude/data/ for work output patterns
        data_dir = self.maia_root / 'claude' / 'data'
        if not data_dir.exists():
            return FileOrgCheckResult(True, 'info', [])

        for file_path in data_dir.rglob('*'):
            if not file_path.is_file():
                continue

            self.stats['total_files_scanned'] += 1

            # Skip allowed paths
            if self._is_allowed_data_file(file_path):
                continue

            # Check for work output patterns
            if self._is_work_output(file_path):
                violations.append({
                    'type': 'WORK_OUTPUT_IN_REPO',
                    'severity': 'warning',
                    'file': str(file_path.relative_to(self.maia_root)),
                    'message': f'Work output should be in ~/work_projects/',
                    'recommendation': self._get_work_output_recommendation(file_path)
                })
                self.stats['work_output_violations'] += 1

        passed = len(violations) == 0
        severity = 'warning' if violations else 'info'

        return FileOrgCheckResult(passed, severity, violations)

    def _is_allowed_data_file(self, file_path: Path) -> bool:
        """Check if file is allowed in claude/data/"""
        relative = file_path.relative_to(self.maia_root)
        path_str = str(relative)

        # Allowed paths
        allowed_prefixes = [
            'claude/data/databases/',
            'claude/data/rag_databases/',
            'claude/data/project_status/',
            'claude/data/action_completion_metrics.json',
            'claude/data/daily_briefing_email.html',
            'claude/data/enhanced_daily_briefing.json'
        ]

        return any(path_str.startswith(prefix) for prefix in allowed_prefixes)

    def _is_work_output(self, file_path: Path) -> bool:
        """Check if file appears to be work output"""
        name = file_path.name

        # Check for work output patterns in filename
        return any(pattern in name for pattern in WORK_OUTPUT_PATTERNS)

    def _get_work_output_recommendation(self, file_path: Path) -> str:
        """Get recommendation for work output file"""
        name = file_path.name.lower()

        if 'servicedesk' in name:
            return 'Move to: ~/work_projects/servicedesk_analysis/'
        elif 'infrastructure' in name:
            return 'Move to: ~/work_projects/infrastructure_team/'
        elif 'recruitment' in name or 'l2_' in name:
            return 'Move to: ~/work_projects/recruitment/'
        else:
            return 'Move to: ~/work_projects/general/'

    def check_file_sizes(self) -> FileOrgCheckResult:
        """Check files >10 MB are in work_projects"""
        self._log("Checking file sizes...")

        violations = []

        # Scan entire repository except .git
        for file_path in self.maia_root.rglob('*'):
            if not file_path.is_file():
                continue

            # Skip .git directory
            if '.git' in file_path.parts:
                continue

            # Skip allowed large file paths
            relative = file_path.relative_to(self.maia_root)
            if any(str(relative).startswith(allowed) for allowed in ALLOWED_LARGE_FILES):
                continue

            # Check size
            try:
                size_mb = file_path.stat().st_size / (1024 * 1024)

                if size_mb > MAX_FILE_SIZE_MB:
                    violations.append({
                        'type': 'SIZE_VIOLATION',
                        'severity': 'warning',
                        'file': str(relative),
                        'size_mb': round(size_mb, 1),
                        'message': f'File exceeds 10 MB limit: {size_mb:.1f} MB',
                        'recommendation': 'Move to: ~/work_projects/ (files >10 MB)'
                    })
                    self.stats['size_violations'] += 1
            except OSError:
                # File might not be accessible
                continue

        passed = len(violations) == 0
        severity = 'warning' if violations else 'info'

        return FileOrgCheckResult(passed, severity, violations)

    def check_database_categorization(self) -> FileOrgCheckResult:
        """Check databases are in correct category subdirectories"""
        self._log("Checking database categorization...")

        violations = []

        databases_dir = self.maia_root / 'claude' / 'data' / 'databases'
        if not databases_dir.exists():
            return FileOrgCheckResult(True, 'info', [])

        # Scan for .db files directly in databases/ (should be in subdirectories)
        for item in databases_dir.iterdir():
            if item.is_file() and item.name.endswith('.db'):
                violations.append({
                    'type': 'DATABASE_CATEGORIZATION',
                    'severity': 'warning',
                    'file': item.name,
                    'message': f'Database not in category subdirectory: {item.name}',
                    'recommendation': f'Move to: claude/data/databases/{{category}}/ (categories: {", ".join(DATABASE_CATEGORIES)})'
                })
                self.stats['database_violations'] += 1

        passed = len(violations) == 0
        severity = 'warning' if violations else 'info'

        return FileOrgCheckResult(passed, severity, violations)

    def check_phase_documentation_archival(self) -> FileOrgCheckResult:
        """Check if phase docs >30 days old should be archived"""
        self._log("Checking phase documentation archival...")

        candidates = []
        cutoff_date = datetime.now() - timedelta(days=PHASE_ARCHIVE_DAYS)

        active_dir = self.maia_root / 'claude' / 'data' / 'project_status' / 'active'
        if not active_dir.exists():
            return FileOrgCheckResult(True, 'info', [])

        for file_path in active_dir.glob('*.md'):
            # Skip non-phase documentation
            if 'PHASE' not in file_path.name.upper() and 'COMPLETE' not in file_path.name.upper():
                continue

            # Check modification time
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime)

            if mtime < cutoff_date:
                age_days = (datetime.now() - mtime).days
                candidates.append({
                    'type': 'ARCHIVE_CANDIDATE',
                    'severity': 'info',
                    'file': file_path.name,
                    'age_days': age_days,
                    'message': f'Phase doc >30 days old: {file_path.name} ({age_days} days)',
                    'recommendation': 'Move to: claude/data/project_status/archive/2025-Q4/'
                })
                self.stats['archive_candidates'] += 1

        # This is informational only, not a violation
        return FileOrgCheckResult(True, 'info', candidates)

    def run_all_checks(self) -> bool:
        """Run all file organization checks"""
        print("🔍 FILE ORGANIZATION COMPLIANCE CHECK")
        print(f"📂 Repository: {self.maia_root}\n")

        # Run checks
        self.results['root_directory'] = self.check_root_directory()
        self.results['work_output_separation'] = self.check_work_output_separation()
        self.results['file_sizes'] = self.check_file_sizes()
        self.results['database_categorization'] = self.check_database_categorization()
        self.results['phase_archival'] = self.check_phase_documentation_archival()

        # Generate report
        return self.generate_report()

    def generate_report(self) -> bool:
        """Generate compliance report"""
        all_passed = True
        has_critical = False
        has_warnings = False

        # Summary statistics
        print("📊 SUMMARY STATISTICS")
        print(f"   Files scanned: {self.stats['total_files_scanned']}")
        print(f"   Root violations: {self.stats['root_violations']}")
        print(f"   Work output violations: {self.stats['work_output_violations']}")
        print(f"   Size violations: {self.stats['size_violations']}")
        print(f"   Database violations: {self.stats['database_violations']}")
        print(f"   Archive candidates: {self.stats['archive_candidates']}\n")

        # Check results
        for check_name, result in self.results.items():
            if not result.passed:
                all_passed = False
                if result.severity == 'critical':
                    has_critical = True
                elif result.severity == 'warning':
                    has_warnings = True

        # Display results by severity
        if has_critical:
            print("❌ CRITICAL VIOLATIONS")
            self._display_violations('critical')
            print()

        if has_warnings:
            print("⚠️  WARNINGS")
            self._display_violations('warning')
            print()

        # Info items
        if self.results.get('phase_archival') and self.results['phase_archival'].violations:
            print("ℹ️  INFORMATIONAL")
            self._display_violations('info')
            print()

        # Overall status
        if all_passed:
            print("✅ PASSED: Repository complies with file organization policy")
            print()
            print("📚 Policy: claude/context/core/file_organization_policy.md")
            return True
        elif has_critical:
            print("❌ FAILED: Critical violations found")
            print()
            print("📚 Policy: claude/context/core/file_organization_policy.md")
            print("🔧 Fix critical violations before proceeding with save state")
            return False
        else:
            print("⚠️  WARNINGS: Non-critical issues found")
            print()
            print("📚 Policy: claude/context/core/file_organization_policy.md")
            print("💡 Consider addressing warnings to maintain repository health")
            return True  # Warnings don't block save state

    def _display_violations(self, severity: str):
        """Display violations of specific severity"""
        for check_name, result in self.results.items():
            if result.severity != severity:
                continue

            for violation in result.violations:
                if violation.get('severity', result.severity) != severity:
                    continue

                print(f"   {violation['type']}: {violation['message']}")
                if 'file' in violation:
                    print(f"      File: {violation['file']}")
                if 'size_mb' in violation:
                    print(f"      Size: {violation['size_mb']} MB")
                if 'age_days' in violation:
                    print(f"      Age: {violation['age_days']} days")
                if 'recommendation' in violation:
                    print(f"      Recommendation: {violation['recommendation']}")
                print()

    def generate_json_report(self, output_path: Path):
        """Generate JSON report for programmatic use"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'maia_root': str(self.maia_root),
            'statistics': self.stats,
            'checks': {}
        }

        for check_name, result in self.results.items():
            report['checks'][check_name] = {
                'passed': result.passed,
                'severity': result.severity,
                'violations': result.violations
            }

        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"📄 JSON report saved: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='File Organization Compliance Checker',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all checks with verbose output
  python3 file_organization_checker.py --check --verbose

  # Generate JSON report
  python3 file_organization_checker.py --check --json report.json

  # Check specific directory
  python3 file_organization_checker.py --check --maia-root /path/to/maia

Exit Codes:
  0 = All checks passed (compliant)
  1 = Warnings found (non-blocking)
  2 = Critical violations (should block save state)
        """
    )

    parser.add_argument(
        '--check',
        action='store_true',
        help='Run file organization compliance checks'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Verbose output'
    )

    parser.add_argument(
        '--json',
        type=str,
        metavar='FILE',
        help='Generate JSON report to file'
    )

    parser.add_argument(
        '--maia-root',
        type=str,
        default=str(MAIA_ROOT),
        help='Path to Maia root directory'
    )

    args = parser.parse_args()

    if not args.check:
        parser.print_help()
        return 0

    maia_root = Path(args.maia_root)
    if not maia_root.exists():
        print(f"❌ Error: Maia root not found: {maia_root}")
        return 2

    checker = FileOrganizationChecker(maia_root, verbose=args.verbose)
    passed = checker.run_all_checks()

    # Generate JSON report if requested
    if args.json:
        checker.generate_json_report(Path(args.json))

    # Exit codes
    if passed:
        # Check if there were any warnings
        has_warnings = any(
            not result.passed and result.severity == 'warning'
            for result in checker.results.values()
        )
        return 1 if has_warnings else 0
    else:
        return 2


if __name__ == '__main__':
    sys.exit(main())
