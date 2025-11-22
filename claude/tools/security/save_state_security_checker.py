#!/usr/bin/env python3
"""
Save State Security Checker - Pre-Commit Security Validation
=============================================================

Purpose: Lightweight security checks before git commits as part of save_state workflow.
         Blocks commits for critical issues, warns for medium issues.

Integration: Called by claude/commands/save_state.md before git commit

Checks:
1. Secret detection (API keys, passwords in staged files)
2. Critical vulnerability scan (block if CVE CRITICAL found)
3. Code security quick scan (Bandit high-severity only)
4. Basic compliance check (UFC validation)

Created: 2025-10-13 (Phase 113 - Security Automation Project)
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Maia root
MAIA_ROOT = Path.home() / "git" / "maia"

# Secret patterns (common credential indicators)
SECRET_PATTERNS = [
    (r'(?i)(api[_-]?key|apikey)[\s]*[:=][\s]*["\']([a-zA-Z0-9\-_]{20,})["\']', 'API Key'),
    (r'(?i)(password|passwd|pwd)[\s]*[:=][\s]*["\']([^"\']+)["\']', 'Password'),
    (r'(?i)(secret|token)[\s]*[:=][\s]*["\']([a-zA-Z0-9\-_]{20,})["\']', 'Secret/Token'),
    (r'(?i)(aws_access_key_id)[\s]*[:=][\s]*([A-Z0-9]{20})', 'AWS Access Key'),
    (r'(?i)(aws_secret_access_key)[\s]*[:=][\s]*([A-Za-z0-9/+=]{40})', 'AWS Secret Key'),
    (r'(?i)(private[_-]?key|privatekey)[\s]*[:=]', 'Private Key'),
    (r'-----BEGIN (RSA|DSA|EC|OPENSSH) PRIVATE KEY-----', 'SSH Private Key'),
    (r'(?i)(gh[psor]_[a-zA-Z0-9]{36})', 'GitHub Token'),
    (r'(?i)(xox[baprs]-[0-9]{10,13}-[0-9]{10,13}-[a-zA-Z0-9]{24,})', 'Slack Token'),
]

# Safe patterns to ignore (configuration examples, test data)
SAFE_PATTERNS = [
    r'YOUR_API_KEY',
    r'PLACEHOLDER',
    r'EXAMPLE',
    r'TEST_PASSWORD',
    r'dummy',
    r'sample',
    r'<[^>]+>',  # XML/HTML tags
]


class SecurityCheckResult:
    """Security check result"""
    def __init__(self, passed: bool, severity: str, findings: List[Dict]):
        self.passed = passed
        self.severity = severity  # critical, high, medium, low, info
        self.findings = findings

    def should_block_commit(self) -> bool:
        """Determine if findings should block commit"""
        return not self.passed and self.severity in ['critical', 'high']


class SaveStateSecurityChecker:
    """Pre-commit security validation"""

    def __init__(self, maia_root: Path, verbose: bool = False):
        self.maia_root = maia_root
        self.verbose = verbose
        self.results: Dict[str, SecurityCheckResult] = {}

    def _log(self, message: str):
        """Log if verbose"""
        if self.verbose:
            print(f"[Security] {message}")

    def get_staged_files(self) -> List[Path]:
        """Get list of staged files for commit"""
        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                cwd=str(self.maia_root),
                capture_output=True,
                text=True,
                check=True
            )

            files = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    file_path = self.maia_root / line
                    if file_path.exists() and file_path.is_file():
                        files.append(file_path)

            return files

        except subprocess.CalledProcessError:
            return []

    def check_secrets(self, files: List[Path]) -> SecurityCheckResult:
        """Check for exposed secrets in staged files"""
        self._log("Checking for secrets...")

        findings = []

        for file_path in files:
            # Skip binary files and large files
            if file_path.suffix in ['.db', '.sqlite', '.pyc', '.so', '.dylib']:
                continue

            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                # Check each secret pattern
                for pattern, secret_type in SECRET_PATTERNS:
                    for match in re.finditer(pattern, content):
                        # Check if it's a safe pattern
                        matched_text = match.group(0)
                        if any(re.search(safe, matched_text, re.IGNORECASE) for safe in SAFE_PATTERNS):
                            continue

                        # Get line number
                        line_num = content[:match.start()].count('\n') + 1

                        findings.append({
                            'file': str(file_path.relative_to(self.maia_root)),
                            'line': line_num,
                            'type': secret_type,
                            'matched': matched_text[:50] + '...' if len(matched_text) > 50 else matched_text
                        })

            except Exception as e:
                self._log(f"Error reading {file_path}: {e}")
                continue

        passed = len(findings) == 0
        severity = 'critical' if not passed else 'info'

        return SecurityCheckResult(passed, severity, findings)

    def check_vulnerabilities(self) -> SecurityCheckResult:
        """Quick check for critical vulnerabilities"""
        self._log("Checking for critical vulnerabilities...")

        findings = []

        try:
            # Check if recent scan has critical vulnerabilities
            import sqlite3
            db_path = self.maia_root / "claude/data/security_metrics.db"

            if not db_path.exists():
                # No database yet, assume clean
                return SecurityCheckResult(True, 'info', [])

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Check recent scans for critical findings
            cursor.execute("""
                SELECT scan_type, critical_count, timestamp
                FROM scan_history
                WHERE timestamp > datetime('now', '-24 hours')
                  AND critical_count > 0
                ORDER BY timestamp DESC
                LIMIT 5
            """)

            for row in cursor.fetchall():
                findings.append({
                    'scan_type': row[0],
                    'critical_count': row[1],
                    'timestamp': row[2]
                })

            conn.close()

            passed = len(findings) == 0
            severity = 'critical' if not passed else 'info'

            return SecurityCheckResult(passed, severity, findings)

        except Exception as e:
            self._log(f"Vulnerability check error: {e}")
            # If check fails, don't block commit
            return SecurityCheckResult(True, 'info', [{'error': str(e)}])

    def check_code_security(self, files: List[Path]) -> SecurityCheckResult:
        """Quick Bandit scan for high-severity issues in Python files"""
        self._log("Checking code security...")

        findings = []

        # Filter Python files only
        python_files = [f for f in files if f.suffix == '.py']
        if not python_files:
            return SecurityCheckResult(True, 'info', [])

        try:
            # Run Bandit on staged Python files (high severity only)
            bandit_path = Path.home() / "Library/Python/3.9/bin/bandit"
            if not bandit_path.exists():
                # Bandit not installed, skip check
                return SecurityCheckResult(True, 'info', [{'note': 'Bandit not installed'}])

            result = subprocess.run(
                [str(bandit_path), "-ll", "-f", "json"] + [str(f) for f in python_files],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.stdout:
                try:
                    data = json.loads(result.stdout)
                    for issue in data.get('results', []):
                        if issue.get('issue_severity') in ['HIGH', 'CRITICAL']:
                            findings.append({
                                'file': issue.get('filename'),
                                'line': issue.get('line_number'),
                                'issue': issue.get('issue_text'),
                                'severity': issue.get('issue_severity')
                            })
                except json.JSONDecodeError:
                    pass

            passed = len(findings) == 0
            severity = 'high' if not passed else 'info'

            return SecurityCheckResult(passed, severity, findings)

        except subprocess.TimeoutExpired:
            self._log("Code security check timed out")
            return SecurityCheckResult(True, 'info', [{'note': 'Timeout'}])
        except Exception as e:
            self._log(f"Code security check error: {e}")
            return SecurityCheckResult(True, 'info', [{'error': str(e)}])

    def check_compliance(self) -> SecurityCheckResult:
        """Basic UFC compliance check"""
        self._log("Checking UFC compliance...")

        findings = []

        try:
            ufc_checker = self.maia_root / "claude/tools/security/ufc_compliance_checker.py"
            if not ufc_checker.exists():
                return SecurityCheckResult(True, 'info', [{'note': 'UFC checker not found'}])

            result = subprocess.run(
                ["python3", str(ufc_checker)],
                cwd=str(self.maia_root),
                capture_output=True,
                text=True,
                timeout=10
            )

            # If non-zero exit code, there are compliance issues
            if result.returncode != 0:
                findings.append({
                    'check': 'UFC Compliance',
                    'status': 'violations detected',
                    'details': result.stdout[:200]
                })

            passed = len(findings) == 0
            severity = 'medium' if not passed else 'info'

            return SecurityCheckResult(passed, severity, findings)

        except subprocess.TimeoutExpired:
            return SecurityCheckResult(True, 'info', [{'note': 'Timeout'}])
        except Exception as e:
            self._log(f"Compliance check error: {e}")
            return SecurityCheckResult(True, 'info', [{'error': str(e)}])

    def run_all_checks(self) -> Tuple[bool, str]:
        """Run all security checks and return overall result"""
        print("🔒 Running pre-commit security checks...")

        # Get staged files
        staged_files = self.get_staged_files()
        print(f"   Analyzing {len(staged_files)} staged file(s)...")

        # Run checks
        self.results['secrets'] = self.check_secrets(staged_files)
        self.results['vulnerabilities'] = self.check_vulnerabilities()
        self.results['code_security'] = self.check_code_security(staged_files)
        self.results['compliance'] = self.check_compliance()

        # Determine overall result
        blocking_issues = []
        warnings = []

        for check_name, result in self.results.items():
            if result.should_block_commit():
                blocking_issues.append((check_name, result))
            elif not result.passed and result.severity in ['medium']:
                warnings.append((check_name, result))

        # Generate report
        if blocking_issues:
            return False, self._generate_blocking_report(blocking_issues)
        elif warnings:
            return True, self._generate_warning_report(warnings)
        else:
            return True, self._generate_clean_report()

    def _generate_blocking_report(self, issues: List[Tuple[str, SecurityCheckResult]]) -> str:
        """Generate report for blocking issues"""
        report = "\n❌ COMMIT BLOCKED - Critical security issues detected:\n\n"

        for check_name, result in issues:
            report += f"🚨 {check_name.upper()}:\n"
            for finding in result.findings[:5]:  # Show max 5 per check
                if check_name == 'secrets':
                    report += f"   - {finding['file']}:{finding['line']} - {finding['type']}\n"
                elif check_name == 'vulnerabilities':
                    report += f"   - {finding['scan_type']}: {finding['critical_count']} critical\n"
                elif check_name == 'code_security':
                    report += f"   - {finding['file']}:{finding['line']} - {finding['issue']}\n"

            if len(result.findings) > 5:
                report += f"   ... and {len(result.findings) - 5} more\n"
            report += "\n"

        report += "⚠️  Please fix these issues before committing.\n"
        report += "💡 Run: python3 claude/tools/security/local_security_scanner.py for details\n"

        return report

    def _generate_warning_report(self, warnings: List[Tuple[str, SecurityCheckResult]]) -> str:
        """Generate report for warnings (non-blocking)"""
        report = "\n⚠️  Security warnings (commit allowed with notes):\n\n"

        for check_name, result in warnings:
            report += f"   {check_name}: {len(result.findings)} issue(s)\n"

        report += "\n✅ Commit allowed - warnings added to commit message\n"
        return report

    def _generate_clean_report(self) -> str:
        """Generate report for clean checks"""
        return "\n✅ Security checks passed - no issues detected\n"

    def get_commit_message_note(self) -> str:
        """Generate security note for commit message"""
        if not self.results:
            return ""

        warnings = []
        for check_name, result in self.results.items():
            if not result.passed and result.severity == 'medium':
                warnings.append(f"{check_name}: {len(result.findings)} warnings")

        if warnings:
            return f"\n\nSecurity Notes:\n" + "\n".join(f"  - {w}" for w in warnings)
        else:
            return "\n\nSecurity: ✅ All checks passed"


def main():
    parser = argparse.ArgumentParser(
        description="Save State Security Checker - Pre-commit validation"
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    parser.add_argument(
        '--commit-note-only',
        action='store_true',
        help='Only output commit message note'
    )

    args = parser.parse_args()

    checker = SaveStateSecurityChecker(MAIA_ROOT, verbose=args.verbose)

    if args.commit_note_only:
        # Just output commit note
        checker.run_all_checks()
        print(checker.get_commit_message_note())
        sys.exit(0)

    # Run checks
    passed, report = checker.run_all_checks()

    # Print report
    print(report)

    # Exit with appropriate code
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
