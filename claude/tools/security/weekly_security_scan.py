#!/usr/bin/env python3
"""
Weekly Security Scan - Maia Security Infrastructure
===================================================

Orchestrated weekly security scanning combining vulnerability scanning and
system hardening audits. Generates unified security reports with trend analysis.

Tools Orchestrated:
- local_security_scanner.py: Dependency & code vulnerability scanning
- security_hardening_manager.py: System hardening audit

Usage:
    python3 weekly_security_scan.py
    python3 weekly_security_scan.py --format json
    python3 weekly_security_scan.py --output-dir /path/to/reports
    python3 weekly_security_scan.py --no-hardening  # Skip Lynis audit (no sudo)
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional


class WeeklySecurityScan:
    """Weekly security scan orchestrator"""

    def __init__(self, output_dir: Optional[Path] = None, verbose: bool = False):
        self.verbose = verbose
        self.output_dir = output_dir or (Path.home() / ".maia" / "security" / "reports")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.results = {
            "scan_time": datetime.now().isoformat(),
            "scan_week": datetime.now().isocalendar()[1],
            "scan_year": datetime.now().year,
            "vulnerability_scan": {},
            "hardening_audit": {},
            "summary": {},
            "trend_analysis": {}
        }

        # Tool paths
        self.maia_root = Path(__file__).parent.parent.parent.parent
        self.scanner_path = self.maia_root / "claude/tools/security/local_security_scanner.py"
        self.hardening_path = self.maia_root / "claude/tools/security/security_hardening_manager.py"

    def _log(self, message: str):
        """Log message if verbose mode enabled"""
        if self.verbose:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

    def run_vulnerability_scan(self) -> Dict[str, Any]:
        """Run vulnerability scanning"""
        self._log("Running vulnerability scan...")

        try:
            cmd = [
                "python3",
                str(self.scanner_path),
                "--scan", str(self.maia_root),
                "--format", "json"
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )

            if result.stdout:
                return json.loads(result.stdout)
            else:
                return {
                    "status": "error",
                    "message": f"Scanner failed: {result.stderr}"
                }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Vulnerability scan failed: {str(e)}"
            }

    def run_hardening_audit(self) -> Dict[str, Any]:
        """Run system hardening audit"""
        self._log("Running hardening audit (requires sudo)...")

        try:
            cmd = [
                "python3",
                str(self.hardening_path),
                "--audit",
                "--format", "json"
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )

            if result.stdout:
                return json.loads(result.stdout)
            else:
                return {
                    "status": "error",
                    "message": f"Hardening audit failed: {result.stderr}"
                }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Hardening audit failed: {str(e)}"
            }

    def load_historical_scans(self) -> List[Dict[str, Any]]:
        """Load historical scan results for trend analysis"""
        historical = []

        # Find all JSON reports
        for report_file in sorted(self.output_dir.glob("security_scan_*.json")):
            try:
                with open(report_file, 'r') as f:
                    data = json.load(f)
                    historical.append({
                        "date": data.get("scan_time"),
                        "vulnerabilities": data.get("vulnerability_scan", {}).get("summary", {}).get("total_findings", 0),
                        "hardening_index": data.get("hardening_audit", {}).get("summary", {}).get("hardening_index", 0)
                    })
            except Exception:
                continue

        return historical[-12:]  # Last 12 weeks

    def analyze_trends(self) -> Dict[str, Any]:
        """Analyze security trends over time"""
        historical = self.load_historical_scans()

        if len(historical) < 2:
            return {
                "status": "insufficient_data",
                "message": "Need at least 2 weeks of data for trend analysis"
            }

        # Calculate trends
        vuln_trend = []
        hardening_trend = []

        for scan in historical:
            vuln_trend.append(scan.get("vulnerabilities", 0))
            hardening_trend.append(scan.get("hardening_index", 0))

        # Simple trend calculation (improving/degrading)
        vuln_direction = "improving" if vuln_trend[-1] < vuln_trend[0] else "degrading"
        hardening_direction = "improving" if hardening_trend[-1] > hardening_trend[0] else "degrading"

        return {
            "status": "completed",
            "weeks_analyzed": len(historical),
            "vulnerability_trend": {
                "direction": vuln_direction,
                "current": vuln_trend[-1],
                "baseline": vuln_trend[0],
                "change": vuln_trend[-1] - vuln_trend[0]
            },
            "hardening_trend": {
                "direction": hardening_direction,
                "current": hardening_trend[-1],
                "baseline": hardening_trend[0],
                "change": hardening_trend[-1] - hardening_trend[0]
            }
        }

    def run_weekly_scan(self, skip_hardening: bool = False) -> Dict[str, Any]:
        """Run complete weekly security scan"""
        self._log("Starting weekly security scan...")

        # Run vulnerability scan
        self.results["vulnerability_scan"] = self.run_vulnerability_scan()

        # Run hardening audit (unless skipped)
        if not skip_hardening:
            self.results["hardening_audit"] = self.run_hardening_audit()
        else:
            self.results["hardening_audit"] = {
                "status": "skipped",
                "message": "Hardening audit skipped (--no-hardening flag)"
            }

        # Analyze trends
        self.results["trend_analysis"] = self.analyze_trends()

        # Generate summary
        self.results["summary"] = self._generate_summary()

        # Save results
        self._save_results()

        self._log("Weekly security scan completed")
        return self.results

    def _generate_summary(self) -> Dict[str, Any]:
        """Generate summary of weekly scan"""
        vuln_scan = self.results["vulnerability_scan"]
        hardening = self.results["hardening_audit"]

        # Overall security score (0-100)
        vuln_score = 100
        if vuln_scan.get("summary", {}).get("total_findings", 0) > 0:
            findings = vuln_scan["summary"]["total_findings"]
            vuln_score = max(0, 100 - (findings * 10))

        hardening_score = hardening.get("summary", {}).get("hardening_index", 0)

        overall_score = int((vuln_score + hardening_score) / 2)

        # Determine grade
        if overall_score >= 90:
            grade = "A"
        elif overall_score >= 80:
            grade = "B"
        elif overall_score >= 70:
            grade = "C"
        elif overall_score >= 60:
            grade = "D"
        else:
            grade = "F"

        return {
            "overall_score": overall_score,
            "grade": grade,
            "vulnerability_score": vuln_score,
            "hardening_score": hardening_score,
            "total_vulnerabilities": vuln_scan.get("summary", {}).get("total_findings", 0),
            "hardening_index": hardening.get("summary", {}).get("hardening_index", 0),
            "tools_run": {
                "vulnerability_scanner": vuln_scan.get("summary", {}).get("tools_run", {}).get("osv_scanner", False),
                "code_scanner": vuln_scan.get("summary", {}).get("tools_run", {}).get("bandit", False),
                "hardening_audit": hardening.get("status") == "completed"
            }
        }

    def _save_results(self):
        """Save scan results to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"security_scan_{timestamp}.json"
        filepath = self.output_dir / filename

        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2)

        self._log(f"Results saved to: {filepath}")

    def format_markdown_report(self) -> str:
        """Generate markdown formatted weekly report"""
        summary = self.results["summary"]

        report = f"""# Weekly Security Scan Report

**Scan Date**: {datetime.fromisoformat(self.results['scan_time']).strftime('%Y-%m-%d %H:%M:%S')}
**Week**: {self.results['scan_week']} of {self.results['scan_year']}
**Overall Grade**: {summary['grade']} ({summary['overall_score']}/100)

## Executive Summary

- **Vulnerability Score**: {summary['vulnerability_score']}/100
- **Hardening Score**: {summary['hardening_score']}/100
- **Total Vulnerabilities**: {summary['total_vulnerabilities']}
- **Hardening Index**: {summary['hardening_index']}/100

## Vulnerability Scan Results

"""

        vuln_scan = self.results["vulnerability_scan"]
        if vuln_scan.get("status") == "error":
            report += f"❌ **Scan Failed**: {vuln_scan.get('message')}\n\n"
        else:
            vuln_summary = vuln_scan.get("summary", {})
            report += f"""- **Dependency Vulnerabilities**: {vuln_summary.get('dependency_vulnerabilities', 0)}
- **Code Security Issues**: {vuln_summary.get('code_security_issues', 0)}
- **Risk Level**: {vuln_summary.get('risk_level', 'UNKNOWN')}

"""

        report += "## System Hardening Audit\n\n"

        hardening = self.results["hardening_audit"]
        if hardening.get("status") == "skipped":
            report += "⏭️  **Skipped**: Hardening audit not run (requires sudo access)\n\n"
        elif hardening.get("status") == "error":
            report += f"❌ **Audit Failed**: {hardening.get('message')}\n\n"
        else:
            hard_summary = hardening.get("summary", {})
            report += f"""- **Security Posture**: {hard_summary.get('security_posture', 'UNKNOWN')}
- **Tests Performed**: {hard_summary.get('tests_performed', 0)}
- **High Priority Items**: {hard_summary.get('high_priority_items', 0)}

"""

        # Trend analysis
        report += "## Trend Analysis\n\n"

        trends = self.results["trend_analysis"]
        if trends.get("status") == "insufficient_data":
            report += "📊 Insufficient historical data for trend analysis (need 2+ weeks)\n\n"
        else:
            vuln_trend = trends.get("vulnerability_trend", {})
            hard_trend = trends.get("hardening_trend", {})

            vuln_emoji = "📉" if vuln_trend.get("direction") == "improving" else "📈"
            hard_emoji = "📈" if hard_trend.get("direction") == "improving" else "📉"

            report += f"""**Vulnerabilities** {vuln_emoji}: {vuln_trend.get('direction')}
- Current: {vuln_trend.get('current')}
- Change: {vuln_trend.get('change'):+d} from baseline

**Hardening** {hard_emoji}: {hard_trend.get('direction')}
- Current: {hard_trend.get('current')}/100
- Change: {hard_trend.get('change'):+d} from baseline

*Based on {trends.get('weeks_analyzed')} weeks of data*

"""

        # Recommendations
        report += "## Recommendations\n\n"

        if summary['overall_score'] >= 90:
            report += "✅ **Excellent security posture**. Maintain current practices.\n"
        elif summary['overall_score'] >= 70:
            report += "⚠️  **Good security posture** with room for improvement:\n"
        else:
            report += "🚨 **Security requires immediate attention**:\n"

        if summary['total_vulnerabilities'] > 0:
            report += f"- Address {summary['total_vulnerabilities']} vulnerabilities found\n"

        if summary['hardening_score'] < 70:
            report += "- Focus on system hardening improvements\n"

        report += f"\n**Detailed Reports**:\n"
        report += f"- Vulnerability scan: `python3 claude/tools/security/local_security_scanner.py --scan .`\n"
        report += f"- Hardening audit: `python3 claude/tools/security/security_hardening_manager.py --audit`\n"

        return report


def main():
    parser = argparse.ArgumentParser(
        description="Maia Weekly Security Scan - Orchestrated security assessment"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Output directory for reports (default: ~/.maia/security/reports)"
    )
    parser.add_argument(
        "--no-hardening",
        action="store_true",
        help="Skip hardening audit (no sudo required)"
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

    # Run weekly scan
    scanner = WeeklySecurityScan(output_dir=args.output_dir, verbose=args.verbose)
    results = scanner.run_weekly_scan(skip_hardening=args.no_hardening)

    # Output results
    if args.format == "json":
        print(json.dumps(results, indent=2))
    else:
        print(scanner.format_markdown_report())

    # Exit code based on overall grade
    grade = results["summary"]["grade"]
    if grade in ["A", "B"]:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
