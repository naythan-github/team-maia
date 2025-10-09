#!/usr/bin/env python3
"""
Save State Pre-Flight Checker - SRE Reliability Gate

Prevents silent failures in save state operations by validating all
dependencies, permissions, and system state before execution.

SRE Pattern: Reliability Gate - Fail fast with clear error messages
rather than silent failures discovered later by users.

Usage:
    python3 claude/tools/sre/save_state_preflight_checker.py --check
    python3 claude/tools/sre/save_state_preflight_checker.py --json
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

class SaveStatePreFlightChecker:
    """Pre-flight validation for save state operations"""

    def __init__(self):
        self.maia_root = Path(__file__).parent.parent.parent.parent
        self.checks_passed = []
        self.checks_failed = []
        self.warnings = []

    def check_tool_exists(self, tool_name: str, required: bool = True) -> bool:
        """Verify a tool exists in the codebase"""
        tool_path = self.maia_root / "claude" / "tools" / tool_name

        # Check in main tools directory
        if tool_path.exists():
            self.checks_passed.append(f"✅ Tool exists: {tool_name}")
            return True

        # Check in subdirectories
        for subdir in ['sre', 'security', 'data', 'communication', 'servicedesk']:
            subdir_path = self.maia_root / "claude" / "tools" / subdir / tool_name
            if subdir_path.exists():
                self.checks_passed.append(f"✅ Tool exists: {subdir}/{tool_name}")
                return True

        # Tool not found
        if required:
            self.checks_failed.append(f"❌ CRITICAL: Required tool missing: {tool_name}")
        else:
            self.warnings.append(f"⚠️  Optional tool missing: {tool_name}")

        return False

    def check_git_status(self) -> bool:
        """Verify git is in a clean state"""
        try:
            # Check if we're in a git repository
            result = subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                cwd=self.maia_root,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                self.checks_failed.append("❌ CRITICAL: Not in a git repository")
                return False

            # Check for uncommitted changes
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.maia_root,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.stdout.strip():
                # Has uncommitted changes - this is expected for save state
                self.warnings.append(f"⚠️  Uncommitted changes detected ({len(result.stdout.strip().splitlines())} files)")
            else:
                self.checks_passed.append("✅ Git repository clean")

            # Check if we can commit
            result = subprocess.run(
                ['git', 'config', 'user.name'],
                cwd=self.maia_root,
                capture_output=True,
                text=True,
                timeout=5
            )

            if not result.stdout.strip():
                self.checks_failed.append("❌ CRITICAL: Git user.name not configured")
                return False

            self.checks_passed.append("✅ Git configured and ready")
            return True

        except subprocess.TimeoutExpired:
            self.checks_failed.append("❌ CRITICAL: Git command timeout")
            return False
        except Exception as e:
            self.checks_failed.append(f"❌ CRITICAL: Git check failed: {e}")
            return False

    def check_write_permissions(self) -> bool:
        """Verify write permissions to critical paths"""
        critical_paths = [
            self.maia_root / "SYSTEM_STATE.md",
            self.maia_root / "README.md",
            self.maia_root / "claude" / "context" / "core" / "agents.md",
            self.maia_root / "claude" / "context" / "tools" / "available.md",
            self.maia_root / "claude" / "context" / "session",
        ]

        all_writable = True
        for path in critical_paths:
            if path.is_file():
                if os.access(path, os.W_OK):
                    self.checks_passed.append(f"✅ Writable: {path.name}")
                else:
                    self.checks_failed.append(f"❌ CRITICAL: No write permission: {path}")
                    all_writable = False
            elif path.is_dir():
                if os.access(path, os.W_OK):
                    self.checks_passed.append(f"✅ Writable: {path.name}/")
                else:
                    self.checks_failed.append(f"❌ CRITICAL: No write permission: {path}/")
                    all_writable = False
            else:
                self.warnings.append(f"⚠️  Path does not exist: {path}")

        return all_writable

    def check_disk_space(self, min_gb: float = 1.0) -> bool:
        """Verify sufficient disk space"""
        try:
            stat = os.statvfs(self.maia_root)
            free_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)

            if free_gb < min_gb:
                self.checks_failed.append(f"❌ CRITICAL: Low disk space: {free_gb:.2f} GB (need {min_gb} GB)")
                return False

            self.checks_passed.append(f"✅ Disk space sufficient: {free_gb:.2f} GB available")
            return True

        except Exception as e:
            self.warnings.append(f"⚠️  Could not check disk space: {e}")
            return True  # Don't fail if we can't check

    def check_phantom_tools_in_commands(self) -> bool:
        """Scan command files for phantom tool references"""
        commands_dir = self.maia_root / "claude" / "commands"
        phantom_references = []

        for cmd_file in commands_dir.glob("*.md"):
            try:
                content = cmd_file.read_text()

                # Look for .py references
                import re
                py_files = re.findall(r'([a-z_]+\.py)', content)

                for py_file in py_files:
                    if not self.check_tool_exists(py_file, required=False):
                        phantom_references.append(f"{cmd_file.name} -> {py_file}")

            except Exception as e:
                self.warnings.append(f"⚠️  Could not scan {cmd_file.name}: {e}")

        if phantom_references:
            self.checks_failed.append(f"❌ WARNING: Phantom tool references found in commands:")
            for ref in phantom_references[:5]:  # Show first 5
                self.checks_failed.append(f"   - {ref}")
            if len(phantom_references) > 5:
                self.checks_failed.append(f"   ... and {len(phantom_references) - 5} more")
            return False

        self.checks_passed.append("✅ No phantom tool references in commands")
        return True

    def check_ufc_compliance_tool(self) -> bool:
        """Verify UFC compliance checker exists and is functional"""
        tool_exists = self.check_tool_exists("security/ufc_compliance_checker.py", required=True)

        if tool_exists:
            # Check if it's executable
            tool_path = self.maia_root / "claude" / "tools" / "security" / "ufc_compliance_checker.py"
            if os.access(tool_path, os.X_OK) or tool_path.suffix == '.py':
                self.checks_passed.append("✅ UFC compliance checker ready")
                return True
            else:
                self.warnings.append("⚠️  UFC compliance checker exists but may not be executable")
                return True

        return False

    def run_all_checks(self) -> Dict:
        """Run all pre-flight checks"""
        print("🔍 Running Save State Pre-Flight Checks...\n")

        # Critical dependencies check
        print("📦 Checking Dependencies...")
        self.check_tool_exists("ufc_compliance_checker.py", required=False)
        self.check_ufc_compliance_tool()

        # Git status check
        print("\n📝 Checking Git Status...")
        self.check_git_status()

        # Permissions check
        print("\n🔐 Checking Write Permissions...")
        self.check_write_permissions()

        # Disk space check
        print("\n💾 Checking Disk Space...")
        self.check_disk_space()

        # Phantom tool check
        print("\n👻 Checking for Phantom Tool References...")
        self.check_phantom_tools_in_commands()

        # Calculate results
        total_checks = len(self.checks_passed) + len(self.checks_failed)
        critical_failures = len([c for c in self.checks_failed if "CRITICAL" in c])

        result = {
            "timestamp": datetime.now().isoformat(),
            "status": "PASS" if critical_failures == 0 else "FAIL",
            "total_checks": total_checks,
            "checks_passed": len(self.checks_passed),
            "checks_failed": len(self.checks_failed),
            "warnings": len(self.warnings),
            "critical_failures": critical_failures,
            "details": {
                "passed": self.checks_passed,
                "failed": self.checks_failed,
                "warnings": self.warnings
            }
        }

        return result

    def print_results(self, result: Dict):
        """Print formatted results"""
        print("\n" + "="*60)
        print("📊 PRE-FLIGHT CHECK RESULTS")
        print("="*60)

        if result["status"] == "PASS":
            print("✅ STATUS: PASS - Save state can proceed")
        else:
            print("❌ STATUS: FAIL - Save state blocked")

        print(f"\n📈 Summary:")
        print(f"   Total Checks: {result['total_checks']}")
        print(f"   Passed: {result['checks_passed']}")
        print(f"   Failed: {result['checks_failed']}")
        print(f"   Warnings: {result['warnings']}")
        print(f"   Critical Failures: {result['critical_failures']}")

        if result["details"]["passed"]:
            print(f"\n✅ Passed Checks ({len(result['details']['passed'])}):")
            for check in result["details"]["passed"]:
                print(f"   {check}")

        if result["details"]["warnings"]:
            print(f"\n⚠️  Warnings ({len(result['details']['warnings'])}):")
            for warning in result["details"]["warnings"]:
                print(f"   {warning}")

        if result["details"]["failed"]:
            print(f"\n❌ Failed Checks ({len(result['details']['failed'])}):")
            for failure in result["details"]["failed"]:
                print(f"   {failure}")

        print("\n" + "="*60)

        if result["status"] == "FAIL":
            print("\n🚨 SAVE STATE BLOCKED")
            print("Fix critical failures before proceeding.")
            print("="*60)
        else:
            print("\n🚀 READY TO PROCEED")
            print("All critical checks passed. Save state can proceed safely.")
            print("="*60)


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Save State Pre-Flight Checker - SRE Reliability Gate"
    )
    parser.add_argument(
        '--check',
        action='store_true',
        help='Run pre-flight checks'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON'
    )

    args = parser.parse_args()

    if not (args.check or args.json):
        parser.print_help()
        return 1

    checker = SaveStatePreFlightChecker()
    result = checker.run_all_checks()

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        checker.print_results(result)

    # Exit with appropriate code
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
