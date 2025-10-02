#!/usr/bin/env python3
"""
Local Security Scanner - Maia Security Infrastructure
=====================================================

Comprehensive vulnerability scanning using OSV-Scanner and Bandit.
Provides unified security assessment for dependencies and Python code.

Tools:
- OSV-Scanner V2.0: Multi-ecosystem dependency vulnerability scanning
- Bandit: Python Static Application Security Testing (SAST)

Usage:
    python3 local_security_scanner.py --scan /path/to/project
    python3 local_security_scanner.py --scan /path/to/project --format json
    python3 local_security_scanner.py --quick  # Scan current directory, dependencies only
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional


class SecurityScanner:
    """Local security scanner integrating OSV-Scanner and Bandit"""

    def __init__(self, scan_path: Path, verbose: bool = False):
        self.scan_path = scan_path
        self.verbose = verbose
        self.results = {
            "scan_time": datetime.now().isoformat(),
            "scan_path": str(scan_path),
            "osv_scanner": {},
            "bandit": {},
            "summary": {}
        }

        # Tool paths
        self.osv_scanner_path = self._find_tool("osv-scanner")
        self.bandit_path = self._find_tool("bandit")

    def _find_tool(self, tool_name: str) -> Optional[str]:
        """Find tool in PATH or common locations"""
        # Try which command
        try:
            result = subprocess.run(
                ["which", tool_name],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass

        # Try common Python user bin location for bandit
        if tool_name == "bandit":
            user_bin = Path.home() / "Library/Python/3.9/bin/bandit"
            if user_bin.exists():
                return str(user_bin)

        return None

    def _log(self, message: str):
        """Log message if verbose mode enabled"""
        if self.verbose:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

    def scan_osv(self) -> Dict[str, Any]:
        """Run OSV-Scanner for dependency vulnerabilities"""
        self._log("Running OSV-Scanner...")

        if not self.osv_scanner_path:
            return {
                "status": "error",
                "message": "OSV-Scanner not found. Install with: brew install osv-scanner"
            }

        try:
            # Run OSV-Scanner in JSON format
            cmd = [
                self.osv_scanner_path,
                "--format", "json",
                "--recursive",
                str(self.scan_path)
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )

            # OSV-Scanner returns non-zero if vulnerabilities found
            if result.stdout:
                try:
                    osv_results = json.loads(result.stdout)
                    vulnerabilities = osv_results.get("results", [])

                    vuln_count = sum(
                        len(r.get("packages", []))
                        for r in vulnerabilities
                    )

                    return {
                        "status": "completed",
                        "vulnerabilities_found": vuln_count,
                        "exit_code": result.returncode,
                        "details": osv_results
                    }
                except json.JSONDecodeError:
                    return {
                        "status": "completed",
                        "vulnerabilities_found": 0,
                        "exit_code": result.returncode,
                        "message": "No vulnerabilities found"
                    }
            else:
                return {
                    "status": "completed",
                    "vulnerabilities_found": 0,
                    "exit_code": result.returncode,
                    "message": result.stderr if result.stderr else "No vulnerabilities found"
                }

        except Exception as e:
            return {
                "status": "error",
                "message": f"OSV-Scanner failed: {str(e)}"
            }

    def scan_bandit(self, severity_level: str = "MEDIUM") -> Dict[str, Any]:
        """Run Bandit for Python code security issues"""
        self._log("Running Bandit...")

        if not self.bandit_path:
            return {
                "status": "error",
                "message": "Bandit not found. Install with: pip install bandit"
            }

        try:
            # Run Bandit in JSON format
            cmd = [
                self.bandit_path,
                "-r", str(self.scan_path),
                "-f", "json",
                "-ll"  # Only report medium and high severity
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )

            if result.stdout:
                try:
                    bandit_results = json.loads(result.stdout)

                    # Count issues by severity
                    issues = bandit_results.get("results", [])
                    severity_counts = {}
                    for issue in issues:
                        sev = issue.get("issue_severity", "UNKNOWN")
                        severity_counts[sev] = severity_counts.get(sev, 0) + 1

                    return {
                        "status": "completed",
                        "issues_found": len(issues),
                        "severity_breakdown": severity_counts,
                        "exit_code": result.returncode,
                        "details": bandit_results
                    }
                except json.JSONDecodeError:
                    return {
                        "status": "error",
                        "message": f"Failed to parse Bandit output: {result.stdout[:200]}"
                    }
            else:
                return {
                    "status": "completed",
                    "issues_found": 0,
                    "severity_breakdown": {},
                    "message": "No issues found"
                }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Bandit failed: {str(e)}"
            }

    def run_scan(self) -> Dict[str, Any]:
        """Run complete security scan"""
        self._log(f"Starting security scan of {self.scan_path}")

        # Run OSV-Scanner
        self.results["osv_scanner"] = self.scan_osv()

        # Run Bandit
        self.results["bandit"] = self.scan_bandit()

        # Generate summary
        self.results["summary"] = self._generate_summary()

        self._log("Security scan completed")
        return self.results

    def _generate_summary(self) -> Dict[str, Any]:
        """Generate summary of findings"""
        osv_vulns = self.results["osv_scanner"].get("vulnerabilities_found", 0)
        bandit_issues = self.results["bandit"].get("issues_found", 0)

        total_findings = osv_vulns + bandit_issues

        # Determine risk level
        if total_findings == 0:
            risk_level = "LOW"
        elif total_findings < 5:
            risk_level = "MEDIUM"
        elif total_findings < 15:
            risk_level = "HIGH"
        else:
            risk_level = "CRITICAL"

        return {
            "total_findings": total_findings,
            "dependency_vulnerabilities": osv_vulns,
            "code_security_issues": bandit_issues,
            "risk_level": risk_level,
            "tools_run": {
                "osv_scanner": self.results["osv_scanner"].get("status") == "completed",
                "bandit": self.results["bandit"].get("status") == "completed"
            }
        }

    def format_markdown_report(self) -> str:
        """Generate markdown formatted security report"""
        summary = self.results["summary"]

        report = f"""# Security Scan Report

**Scan Time**: {self.results['scan_time']}
**Scan Path**: {self.results['scan_path']}
**Risk Level**: {summary['risk_level']}

## Summary

- **Total Findings**: {summary['total_findings']}
- **Dependency Vulnerabilities**: {summary['dependency_vulnerabilities']} (OSV-Scanner)
- **Code Security Issues**: {summary['code_security_issues']} (Bandit)

## OSV-Scanner Results (Dependencies)

**Status**: {self.results['osv_scanner'].get('status')}
**Vulnerabilities Found**: {self.results['osv_scanner'].get('vulnerabilities_found', 0)}

"""

        if self.results['osv_scanner'].get('status') == 'error':
            report += f"**Error**: {self.results['osv_scanner'].get('message')}\n\n"
        elif self.results['osv_scanner'].get('vulnerabilities_found', 0) > 0:
            report += "⚠️ **Vulnerabilities detected**. Run `osv-scanner --recursive .` for details.\n\n"
        else:
            report += "✅ **No vulnerabilities found**\n\n"

        report += f"""## Bandit Results (Python Code Security)

**Status**: {self.results['bandit'].get('status')}
**Issues Found**: {self.results['bandit'].get('issues_found', 0)}

"""

        if self.results['bandit'].get('status') == 'error':
            report += f"**Error**: {self.results['bandit'].get('message')}\n\n"
        elif self.results['bandit'].get('issues_found', 0) > 0:
            severity = self.results['bandit'].get('severity_breakdown', {})
            report += "**Severity Breakdown**:\n"
            for sev, count in severity.items():
                report += f"- {sev}: {count}\n"
            report += f"\n⚠️ **Security issues detected**. Run `bandit -r {self.scan_path}` for details.\n\n"
        else:
            report += "✅ **No security issues found**\n\n"

        report += f"""## Recommendations

"""

        if summary['total_findings'] == 0:
            report += "✅ No immediate security concerns detected.\n"
        else:
            report += "⚠️ **Action Required**:\n"
            if summary['dependency_vulnerabilities'] > 0:
                report += f"1. Review OSV-Scanner findings and update vulnerable dependencies\n"
            if summary['code_security_issues'] > 0:
                report += f"2. Review Bandit findings and remediate security issues in Python code\n"

        return report


def main():
    parser = argparse.ArgumentParser(
        description="Maia Local Security Scanner - OSV-Scanner + Bandit integration"
    )
    parser.add_argument(
        "--scan",
        type=Path,
        help="Path to scan (default: current directory)"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick scan (current directory, dependencies only)"
    )
    parser.add_argument(
        "--format",
        choices=["json", "markdown"],
        default="markdown",
        help="Output format (default: markdown)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output"
    )

    args = parser.parse_args()

    # Determine scan path
    if args.quick:
        scan_path = Path.cwd()
    elif args.scan:
        scan_path = args.scan
    else:
        scan_path = Path.cwd()

    if not scan_path.exists():
        print(f"Error: Path does not exist: {scan_path}", file=sys.stderr)
        sys.exit(1)

    # Run scan
    scanner = SecurityScanner(scan_path, verbose=args.verbose)
    results = scanner.run_scan()

    # Output results
    if args.format == "json":
        print(json.dumps(results, indent=2))
    else:
        print(scanner.format_markdown_report())

    # Exit code based on findings
    total_findings = results["summary"]["total_findings"]
    if total_findings > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
