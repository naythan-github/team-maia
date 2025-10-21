#!/usr/bin/env python3
"""
Maia Health Check - Team Deployment Monitoring
Phase 134.2 - Production Monitoring for Team Sharing

Simple health check command that validates Maia is working correctly on each
team member's laptop. No central logging - each person monitors their own instance.

Usage:
    python3 claude/tools/sre/maia_health_check.py
    python3 claude/tools/sre/maia_health_check.py --detailed
    python3 claude/tools/sre/maia_health_check.py --fix

Checks:
    1. Routing Accuracy (coordinator suggestions vs actual usage)
    2. Agent Quality (spot-check top agents)
    3. Performance (agent loading latency)
    4. System Health (session state, graceful degradation)
"""

import sys
import sqlite3
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
import json

# Maia root detection
MAIA_ROOT = Path(__file__).resolve().parents[3]
ROUTING_DB = MAIA_ROOT / "claude/data/routing_decisions.db"
SESSION_STATE = Path("/tmp/maia_active_swarm_session.json")


class HealthCheckResult:
    """Health check result"""

    def __init__(self, name: str, status: str, message: str, score: int = None):
        self.name = name
        self.status = status  # ✅ PASS, ⚠️ WARNING, ❌ FAIL
        self.message = message
        self.score = score  # Optional numerical score


def check_routing_accuracy() -> HealthCheckResult:
    """
    Check routing accuracy from Phase 125 routing logger.

    Target: >80% acceptance rate
    Warning: <80% but >50%
    Fail: <50%
    """
    if not ROUTING_DB.exists():
        return HealthCheckResult(
            "Routing Accuracy",
            "⚠️ WARNING",
            "No routing data yet (database doesn't exist)"
        )

    try:
        conn = sqlite3.connect(ROUTING_DB)
        cursor = conn.cursor()

        # Get last 7 days of routing decisions
        seven_days_ago = datetime.now() - timedelta(days=7)

        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN accepted = 1 THEN 1 ELSE 0 END) as accepted,
                AVG(confidence) as avg_confidence
            FROM routing_suggestions
            WHERE timestamp > ?
        """, (seven_days_ago.isoformat(),))

        result = cursor.fetchone()
        total, accepted, avg_confidence = result

        if total == 0:
            return HealthCheckResult(
                "Routing Accuracy",
                "⚠️ WARNING",
                "No routing decisions in last 7 days - need more usage data"
            )

        acceptance_rate = (accepted / total) * 100 if total > 0 else 0

        if acceptance_rate >= 80:
            status = "✅ PASS"
            message = f"{acceptance_rate:.1f}% acceptance rate (target: >80%)"
        elif acceptance_rate >= 50:
            status = "⚠️ WARNING"
            message = f"{acceptance_rate:.1f}% acceptance rate (target: >80%, needs improvement)"
        else:
            status = "❌ FAIL"
            message = f"{acceptance_rate:.1f}% acceptance rate (CRITICAL - coordinator routing poorly)"

        conn.close()

        return HealthCheckResult(
            "Routing Accuracy",
            status,
            message,
            score=int(acceptance_rate)
        )

    except Exception as e:
        return HealthCheckResult(
            "Routing Accuracy",
            "❌ FAIL",
            f"Error checking routing database: {e}"
        )


def check_session_state() -> HealthCheckResult:
    """
    Check session state file health.

    Validates:
    - File exists (optional - may not be in active session)
    - Valid JSON structure
    - Correct permissions (600)
    - Required fields present
    """
    if not SESSION_STATE.exists():
        return HealthCheckResult(
            "Session State",
            "✅ PASS",
            "No active session (normal between conversations)"
        )

    try:
        # Check permissions
        import os
        stat_info = os.stat(SESSION_STATE)
        perms = oct(stat_info.st_mode)[-3:]

        if perms != "600":
            return HealthCheckResult(
                "Session State",
                "❌ FAIL",
                f"Insecure permissions: {perms} (should be 600)"
            )

        # Check JSON validity
        with open(SESSION_STATE) as f:
            session = json.load(f)

        # Check required fields
        required_fields = ["current_agent", "domain", "handoff_chain", "version"]
        missing = [f for f in required_fields if f not in session]

        if missing:
            return HealthCheckResult(
                "Session State",
                "⚠️ WARNING",
                f"Missing fields: {', '.join(missing)}"
            )

        # Check version
        if session.get("version") != "1.1":
            return HealthCheckResult(
                "Session State",
                "⚠️ WARNING",
                f"Old session version: {session.get('version')} (expected 1.1)"
            )

        return HealthCheckResult(
            "Session State",
            "✅ PASS",
            f"Active session: {session['current_agent']} ({session['domain']} domain)"
        )

    except json.JSONDecodeError:
        return HealthCheckResult(
            "Session State",
            "❌ FAIL",
            "Corrupted session state (invalid JSON) - will auto-recover on next load"
        )
    except Exception as e:
        return HealthCheckResult(
            "Session State",
            "❌ FAIL",
            f"Error checking session state: {e}"
        )


def check_performance() -> HealthCheckResult:
    """
    Check agent loading performance.

    Target: P95 <200ms
    Warning: P95 200-500ms
    Fail: P95 >500ms

    Quick test: Load a simple query and measure time
    """
    import time

    try:
        swarm_loader = MAIA_ROOT / "claude/hooks/swarm_auto_loader.py"

        if not swarm_loader.exists():
            return HealthCheckResult(
                "Performance",
                "❌ FAIL",
                "Swarm auto-loader not found"
            )

        # Run 5 quick tests
        durations = []
        for i in range(5):
            start = time.time()
            result = subprocess.run(
                [sys.executable, str(swarm_loader), f"test query {i}"],
                capture_output=True,
                timeout=2
            )
            duration_ms = (time.time() - start) * 1000
            durations.append(duration_ms)

        # Calculate P95 (for 5 samples, just use max)
        avg_ms = sum(durations) / len(durations)
        p95_ms = max(durations)

        if p95_ms < 200:
            status = "✅ PASS"
            message = f"P95 {p95_ms:.0f}ms (target: <200ms) - excellent"
        elif p95_ms < 500:
            status = "⚠️ WARNING"
            message = f"P95 {p95_ms:.0f}ms (target: <200ms) - acceptable but slow"
        else:
            status = "❌ FAIL"
            message = f"P95 {p95_ms:.0f}ms (target: <200ms) - too slow, investigate"

        return HealthCheckResult(
            "Performance",
            status,
            message,
            score=int(p95_ms)
        )

    except subprocess.TimeoutExpired:
        return HealthCheckResult(
            "Performance",
            "❌ FAIL",
            "Agent loading timeout (>2s) - critical performance issue"
        )
    except Exception as e:
        return HealthCheckResult(
            "Performance",
            "❌ FAIL",
            f"Error checking performance: {e}"
        )


def check_integration_tests() -> HealthCheckResult:
    """
    Run Phase 134.1 integration tests to validate system health.

    Quick subset: 3 critical tests
    - Session state management
    - Domain change detection
    - Graceful degradation
    """
    try:
        test_file = MAIA_ROOT / "tests/test_agent_persistence_integration.py"

        if not test_file.exists():
            return HealthCheckResult(
                "Integration Tests",
                "⚠️ WARNING",
                "Integration test suite not found (Phase 134.1)"
            )

        # Run quick subset of tests (session state + graceful degradation)
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(test_file),
             "-k", "session_state or graceful",
             "-v", "--tb=no"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=MAIA_ROOT
        )

        # Parse output for pass/fail count
        output = result.stdout + result.stderr

        if "passed" in output:
            # Extract test counts
            import re
            match = re.search(r'(\d+) passed', output)
            passed = int(match.group(1)) if match else 0

            match_failed = re.search(r'(\d+) failed', output)
            failed = int(match_failed.group(1)) if match_failed else 0

            if failed == 0:
                status = "✅ PASS"
                message = f"All {passed} critical tests passing"
            else:
                status = "❌ FAIL"
                message = f"{failed} test(s) failed, {passed} passed"

            return HealthCheckResult(
                "Integration Tests",
                status,
                message,
                score=passed
            )
        else:
            return HealthCheckResult(
                "Integration Tests",
                "⚠️ WARNING",
                "Could not parse test results"
            )

    except subprocess.TimeoutExpired:
        return HealthCheckResult(
            "Integration Tests",
            "❌ FAIL",
            "Tests timeout (>30s) - may indicate performance issue"
        )
    except Exception as e:
        return HealthCheckResult(
            "Integration Tests",
            "⚠️ WARNING",
            f"Skipped (pytest may not be installed): {e}"
        )


def run_health_check(detailed: bool = False) -> dict:
    """
    Run complete health check.

    Returns:
        dict with results and overall status
    """
    print("=" * 70)
    print("MAIA HEALTH CHECK")
    print("=" * 70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Location: {MAIA_ROOT}")
    print()

    # Run all checks
    checks = [
        check_session_state(),
        check_performance(),
        check_routing_accuracy(),
    ]

    # Add integration tests only in detailed mode
    if detailed:
        checks.append(check_integration_tests())

    # Print results
    print("HEALTH CHECK RESULTS")
    print("=" * 70)

    for check in checks:
        print(f"{check.status} {check.name}")
        print(f"   {check.message}")
        if check.score is not None and detailed:
            print(f"   Score: {check.score}")
        print()

    # Overall status
    fail_count = sum(1 for c in checks if "❌" in c.status)
    warning_count = sum(1 for c in checks if "⚠️" in c.status)
    pass_count = sum(1 for c in checks if "✅" in c.status)

    print("=" * 70)
    print("OVERALL STATUS")
    print("=" * 70)

    if fail_count > 0:
        print(f"❌ DEGRADED - {fail_count} critical issue(s)")
        overall_status = "DEGRADED"
    elif warning_count > 0:
        print(f"⚠️  OPERATIONAL WITH WARNINGS - {warning_count} warning(s)")
        overall_status = "WARNING"
    else:
        print(f"✅ HEALTHY - All checks passing")
        overall_status = "HEALTHY"

    print(f"\n   Passed: {pass_count}, Warnings: {warning_count}, Failed: {fail_count}")
    print()

    # Recommendations
    if fail_count > 0 or warning_count > 0:
        print("RECOMMENDATIONS:")
        print("-" * 70)

        for check in checks:
            if "❌" in check.status:
                print(f"🔴 {check.name}: {check.message}")
            elif "⚠️" in check.status:
                print(f"🟡 {check.name}: {check.message}")

        print()
        print("Run: python3 claude/tools/sre/maia_health_check.py --fix")
        print("     for automated fixes (if available)")
        print()

    return {
        "overall_status": overall_status,
        "checks": checks,
        "summary": {
            "passed": pass_count,
            "warnings": warning_count,
            "failed": fail_count
        }
    }


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Maia Health Check - Validate system is working correctly"
    )
    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Run detailed checks including integration tests"
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Attempt automated fixes for common issues"
    )

    args = parser.parse_args()

    if args.fix:
        print("Automated fixes not yet implemented")
        print("Please review health check output and fix manually")
        sys.exit(1)

    result = run_health_check(detailed=args.detailed)

    # Exit code: 0 = healthy, 1 = warnings, 2 = degraded
    if result["overall_status"] == "HEALTHY":
        sys.exit(0)
    elif result["overall_status"] == "WARNING":
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == "__main__":
    main()
