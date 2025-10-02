#!/usr/bin/env python3
"""
Security Hardening Manager - Maia Security Infrastructure
=========================================================

System security hardening using Lynis security auditing tool.
Provides actionable hardening recommendations for macOS/Linux systems.

Tool:
- Lynis: Security auditing and hardening tool for Unix-based systems

Usage:
    python3 security_hardening_manager.py --audit
    python3 security_hardening_manager.py --audit --format json
    python3 security_hardening_manager.py --recommendations
"""

import argparse
import json
import subprocess
import sys
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional


class SecurityHardeningManager:
    """Security hardening manager using Lynis"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results = {
            "audit_time": datetime.now().isoformat(),
            "lynis": {},
            "summary": {},
            "recommendations": []
        }

        # Find Lynis
        self.lynis_path = self._find_lynis()

    def _find_lynis(self) -> Optional[str]:
        """Find Lynis in PATH"""
        try:
            result = subprocess.run(
                ["which", "lynis"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass

        return None

    def _log(self, message: str):
        """Log message if verbose mode enabled"""
        if self.verbose:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

    def run_lynis_audit(self) -> Dict[str, Any]:
        """Run Lynis security audit"""
        self._log("Running Lynis security audit...")

        if not self.lynis_path:
            return {
                "status": "error",
                "message": "Lynis not found. Install with: brew install lynis"
            }

        try:
            # Create temporary directory for Lynis output
            output_dir = Path.home() / ".maia" / "security" / "lynis"
            output_dir.mkdir(parents=True, exist_ok=True)

            # Run Lynis audit
            cmd = [
                "sudo",
                self.lynis_path,
                "audit", "system",
                "--quick",  # Skip waiting for user input
                "--quiet"   # Reduce output verbosity
            ]

            self._log(f"Executing: {' '.join(cmd)}")
            self._log("Note: Lynis requires sudo access for system audit")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )

            # Parse Lynis output
            return self._parse_lynis_output(result.stdout, result.stderr)

        except Exception as e:
            return {
                "status": "error",
                "message": f"Lynis audit failed: {str(e)}"
            }

    def _parse_lynis_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """Parse Lynis output to extract key findings"""

        # Extract hardening index
        hardening_index = 0
        index_match = re.search(r'Hardening index\s*:\s*(\d+)', stdout)
        if index_match:
            hardening_index = int(index_match.group(1))

        # Extract tests performed
        tests_performed = 0
        tests_match = re.search(r'Tests performed\s*:\s*(\d+)', stdout)
        if tests_match:
            tests_performed = int(tests_match.group(1))

        # Extract warnings and suggestions
        warnings = []
        suggestions = []

        # Look for warning patterns
        warning_pattern = r'Warning:\s*(.+?)(?:\[|$)'
        for match in re.finditer(warning_pattern, stdout, re.MULTILINE):
            warnings.append(match.group(1).strip())

        # Look for suggestion patterns
        suggestion_pattern = r'Suggestion:\s*(.+?)(?:\[|$)'
        for match in re.finditer(suggestion_pattern, stdout, re.MULTILINE):
            suggestions.append(match.group(1).strip())

        return {
            "status": "completed",
            "hardening_index": hardening_index,
            "tests_performed": tests_performed,
            "warnings_count": len(warnings),
            "suggestions_count": len(suggestions),
            "warnings": warnings[:10],  # Limit to top 10
            "suggestions": suggestions[:10],  # Limit to top 10
            "raw_output": stdout if self.verbose else None
        }

    def generate_recommendations(self) -> List[Dict[str, Any]]:
        """Generate prioritized hardening recommendations"""
        lynis_result = self.results["lynis"]

        if lynis_result.get("status") != "completed":
            return []

        recommendations = []

        # Priority 1: Address warnings
        for i, warning in enumerate(lynis_result.get("warnings", [])[:5], 1):
            recommendations.append({
                "priority": "HIGH",
                "category": "Security Warning",
                "description": warning,
                "source": "Lynis",
                "order": i
            })

        # Priority 2: Address suggestions
        for i, suggestion in enumerate(lynis_result.get("suggestions", [])[:5], 1):
            recommendations.append({
                "priority": "MEDIUM",
                "category": "Hardening Suggestion",
                "description": suggestion,
                "source": "Lynis",
                "order": len(recommendations) + 1
            })

        # Priority 3: Maia-specific hardening recommendations
        maia_recommendations = [
            {
                "priority": "HIGH",
                "category": "Credential Security",
                "description": "Ensure all MCP server credentials are encrypted using mcp_env_manager.py",
                "source": "Maia Best Practices",
                "order": len(recommendations) + 1
            },
            {
                "priority": "MEDIUM",
                "category": "Docker Security",
                "description": "Verify all Docker containers run with security hardening flags (--read-only, --cap-drop ALL)",
                "source": "Maia Best Practices",
                "order": len(recommendations) + 2
            },
            {
                "priority": "MEDIUM",
                "category": "File Permissions",
                "description": "Review file permissions in claude/tools/security/ (should be 600 for sensitive files)",
                "source": "Maia Best Practices",
                "order": len(recommendations) + 3
            }
        ]

        recommendations.extend(maia_recommendations)

        return recommendations

    def run_audit(self) -> Dict[str, Any]:
        """Run complete security hardening audit"""
        self._log("Starting security hardening audit")

        # Run Lynis audit
        self.results["lynis"] = self.run_lynis_audit()

        # Generate recommendations
        self.results["recommendations"] = self.generate_recommendations()

        # Generate summary
        self.results["summary"] = self._generate_summary()

        self._log("Security hardening audit completed")
        return self.results

    def _generate_summary(self) -> Dict[str, Any]:
        """Generate summary of audit results"""
        lynis = self.results["lynis"]

        if lynis.get("status") != "completed":
            return {
                "status": "failed",
                "message": lynis.get("message", "Audit failed")
            }

        hardening_index = lynis.get("hardening_index", 0)

        # Determine security posture
        if hardening_index >= 80:
            posture = "EXCELLENT"
        elif hardening_index >= 70:
            posture = "GOOD"
        elif hardening_index >= 60:
            posture = "MODERATE"
        else:
            posture = "NEEDS_IMPROVEMENT"

        high_priority_count = sum(
            1 for r in self.results["recommendations"]
            if r.get("priority") == "HIGH"
        )

        return {
            "status": "completed",
            "security_posture": posture,
            "hardening_index": hardening_index,
            "tests_performed": lynis.get("tests_performed", 0),
            "total_recommendations": len(self.results["recommendations"]),
            "high_priority_items": high_priority_count
        }

    def format_markdown_report(self) -> str:
        """Generate markdown formatted hardening report"""
        summary = self.results["summary"]

        if summary.get("status") != "completed":
            return f"""# Security Hardening Audit Report

**Audit Time**: {self.results['audit_time']}
**Status**: FAILED

**Error**: {summary.get('message', 'Unknown error')}

Please install Lynis: `brew install lynis`
"""

        report = f"""# Security Hardening Audit Report

**Audit Time**: {self.results['audit_time']}
**Security Posture**: {summary['security_posture']}
**Hardening Index**: {summary['hardening_index']}/100

## Summary

- **Tests Performed**: {summary['tests_performed']}
- **Total Recommendations**: {summary['total_recommendations']}
- **High Priority Items**: {summary['high_priority_items']}

## Lynis Audit Results

**Hardening Index**: {self.results['lynis'].get('hardening_index', 0)}/100
**Warnings**: {self.results['lynis'].get('warnings_count', 0)}
**Suggestions**: {self.results['lynis'].get('suggestions_count', 0)}

"""

        # Recommendations section
        report += "## Hardening Recommendations\n\n"

        high_priority = [r for r in self.results["recommendations"] if r.get("priority") == "HIGH"]
        medium_priority = [r for r in self.results["recommendations"] if r.get("priority") == "MEDIUM"]

        if high_priority:
            report += "### 🚨 High Priority\n\n"
            for i, rec in enumerate(high_priority, 1):
                report += f"{i}. **{rec['category']}**: {rec['description']}\n"
                report += f"   - *Source: {rec['source']}*\n\n"

        if medium_priority:
            report += "### ⚠️  Medium Priority\n\n"
            for i, rec in enumerate(medium_priority[:5], 1):
                report += f"{i}. **{rec['category']}**: {rec['description']}\n"
                report += f"   - *Source: {rec['source']}*\n\n"

        # Overall assessment
        report += "## Overall Assessment\n\n"

        if summary['security_posture'] == "EXCELLENT":
            report += "✅ **System security posture is excellent**. Continue monitoring and applying updates.\n"
        elif summary['security_posture'] == "GOOD":
            report += "✅ **System security posture is good**. Address high priority items to improve further.\n"
        elif summary['security_posture'] == "MODERATE":
            report += "⚠️  **System security needs improvement**. Focus on high priority recommendations.\n"
        else:
            report += "🚨 **System security requires immediate attention**. Address all high priority items urgently.\n"

        return report


def main():
    parser = argparse.ArgumentParser(
        description="Maia Security Hardening Manager - Lynis integration"
    )
    parser.add_argument(
        "--audit",
        action="store_true",
        help="Run security hardening audit"
    )
    parser.add_argument(
        "--recommendations",
        action="store_true",
        help="Show hardening recommendations only (no audit)"
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

    if not args.audit and not args.recommendations:
        parser.print_help()
        sys.exit(1)

    manager = SecurityHardeningManager(verbose=args.verbose)

    if args.audit:
        results = manager.run_audit()

        if args.format == "json":
            print(json.dumps(results, indent=2))
        else:
            print(manager.format_markdown_report())

        # Exit code based on security posture
        posture = results["summary"].get("security_posture")
        if posture in ["EXCELLENT", "GOOD"]:
            sys.exit(0)
        else:
            sys.exit(1)

    elif args.recommendations:
        # Generate recommendations without full audit
        print("# Maia Security Hardening Recommendations\n")
        print("Run `--audit` for complete system security assessment.\n")


if __name__ == "__main__":
    main()
