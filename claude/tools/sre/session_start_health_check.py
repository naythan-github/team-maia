#!/usr/bin/env python3
"""
Session Start Critical Health Check - Phase 103 Week 3

Lightweight health check for conversation start - ONLY shows critical issues.
Designed to be fast (<5 seconds) and non-intrusive.

Only checks:
- Failed LaunchAgent services (CRITICAL)
- Critical phantom dependencies (CRITICAL)

Skips:
- RAG health (warnings only)
- UFC compliance (warnings only)
- Non-critical issues

Usage:
    python3 claude/tools/sre/session_start_health_check.py
    python3 claude/tools/sre/session_start_health_check.py --silent  # Exit code only
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


def check_failed_services(maia_root: Path) -> Tuple[int, List[str]]:
    """Quick check for failed LaunchAgent services"""
    tool_path = maia_root / "claude/tools/sre/launchagent_health_monitor.py"

    if not tool_path.exists():
        return (0, [])

    try:
        result = subprocess.run(
            ["python3", str(tool_path), "--dashboard", "--failed-only"],
            cwd=maia_root,
            capture_output=True,
            text=True,
            timeout=10
        )

        failed_count = 0
        failed_services = []

        for line in result.stdout.split("\n"):
            if "Failed:" in line:
                try:
                    failed_count = int(line.split(":")[1].strip().split()[0])
                except:
                    pass
            elif "FAILED" in line and "com.maia." in line:
                service_name = line.split()[0]
                failed_services.append(service_name)

        return (failed_count, failed_services)

    except Exception:
        return (0, [])


def check_critical_phantoms(maia_root: Path) -> Tuple[int, List[str]]:
    """Quick check for critical phantom dependencies"""
    tool_path = maia_root / "claude/tools/sre/dependency_graph_validator.py"

    if not tool_path.exists():
        return (0, [])

    try:
        result = subprocess.run(
            ["python3", str(tool_path), "--analyze", "--critical-only"],
            cwd=maia_root,
            capture_output=True,
            text=True,
            timeout=15
        )

        critical_count = 0
        critical_phantoms = []

        in_phantoms_section = False
        for line in result.stdout.split("\n"):
            if "Critical Phantoms:" in line:
                try:
                    critical_count = int(line.split(":")[1].strip().split()[0])
                except:
                    pass
            elif "Critical Phantom Dependencies:" in line:
                in_phantoms_section = True
            elif in_phantoms_section and line.strip().startswith("•"):
                phantom = line.strip().lstrip("• ")
                if phantom:
                    critical_phantoms.append(phantom)

        return (critical_count, critical_phantoms[:3])  # Limit to 3

    except Exception:
        return (0, [])


def main():
    parser = argparse.ArgumentParser(
        description="Session Start Critical Health Check - Fast critical-only scan"
    )
    parser.add_argument(
        "--silent",
        action="store_true",
        help="Silent mode - exit code only, no output"
    )
    # Import MAIA_ROOT for default
    import os
    from claude.tools.core.paths import MAIA_ROOT

    parser.add_argument(
        "--maia-root",
        type=str,
        default=os.environ.get("MAIA_ROOT", str(MAIA_ROOT)),
        help="Path to Maia root directory"
    )

    args = parser.parse_args()
    maia_root = Path(args.maia_root)

    if not maia_root.exists():
        if not args.silent:
            print(f"❌ Error: MAIA_ROOT not found: {maia_root}")
        return 1

    # Quick checks
    failed_count, failed_services = check_failed_services(maia_root)
    phantom_count, critical_phantoms = check_critical_phantoms(maia_root)

    has_critical_issues = failed_count > 0 or phantom_count > 0

    # Silent mode: exit code only
    if args.silent:
        return 2 if has_critical_issues else 0

    # No critical issues: silent success
    if not has_critical_issues:
        return 0

    # Critical issues found: display banner
    print()
    print("=" * 70)
    print("⚠️  CRITICAL SYSTEM HEALTH ISSUES DETECTED")
    print("=" * 70)
    print()

    if failed_count > 0:
        print(f"🔴 Failed Services: {failed_count}")
        for service in failed_services[:3]:
            print(f"   • {service}")
        if len(failed_services) > 3:
            print(f"   ... and {len(failed_services) - 3} more")
        print()

    if phantom_count > 0:
        print(f"🔴 Critical Phantom Dependencies: {phantom_count}")
        for phantom in critical_phantoms:
            print(f"   • {phantom}")
        if phantom_count > len(critical_phantoms):
            print(f"   ... and {phantom_count - len(critical_phantoms)} more")
        print()

    print("📊 Run full health check for details:")
    print("   python3 claude/tools/sre/automated_health_monitor.py")
    print()
    print("=" * 70)
    print()

    return 2  # Critical issues found


if __name__ == "__main__":
    sys.exit(main())
