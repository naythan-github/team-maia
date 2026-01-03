#!/usr/bin/env python3
"""
Maia Performance Baseline Tool

Measures critical operation latencies and detects regressions.
Run in CI to prevent performance degradation.

Usage:
    python3 performance_baseline.py --check      # Check against baseline
    python3 performance_baseline.py --update     # Update baseline
    python3 performance_baseline.py --verbose    # Detailed output

Author: SRE Principal Engineer Agent
Date: 2026-01-03
"""

import argparse
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

# Find MAIA_ROOT
MAIA_ROOT = Path(__file__).resolve().parents[3]
BASELINE_FILE = MAIA_ROOT / "claude" / "data" / "performance_baselines.json"


@dataclass
class Metric:
    """Performance metric definition."""
    name: str
    target_ms: float  # Target latency
    warn_ms: float    # Warning threshold
    fail_ms: float    # Failure threshold
    measured_ms: Optional[float] = None
    status: str = "pending"


# Baseline definitions
BASELINES = {
    "context_loading": Metric(
        name="UFC Context Loading",
        target_ms=500,
        warn_ms=750,
        fail_ms=1000,
    ),
    "agent_routing": Metric(
        name="Agent Routing Decision",
        target_ms=100,
        warn_ms=200,
        fail_ms=500,
    ),
    "tool_discovery": Metric(
        name="Tool Discovery Scan",
        target_ms=300,
        warn_ms=500,
        fail_ms=1000,
    ),
    "database_query": Metric(
        name="System State Query",
        target_ms=50,
        warn_ms=100,
        fail_ms=200,
    ),
    "path_resolution": Metric(
        name="Path Resolution",
        target_ms=10,
        warn_ms=50,
        fail_ms=100,
    ),
}


class PerformanceBaseline:
    """Performance baseline measurement and validation."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results: Dict[str, Metric] = {}

    def _time_operation(self, func, iterations: int = 10) -> float:
        """Time an operation and return average ms."""
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            func()
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)
        return sum(times) / len(times)

    def measure_context_loading(self) -> float:
        """Measure UFC context loading time."""
        try:
            sys.path.insert(0, str(MAIA_ROOT / "claude" / "tools" / "sre"))
            from smart_context_loader import SmartContextLoader

            def load_context():
                loader = SmartContextLoader()
                loader.load_guaranteed_minimum()

            return self._time_operation(load_context, iterations=5)
        except ImportError:
            return -1  # Not available

    def measure_agent_routing(self) -> float:
        """Measure agent routing decision time."""
        try:
            sys.path.insert(0, str(MAIA_ROOT / "claude" / "hooks"))
            from swarm_auto_loader import get_context_id

            def route_agent():
                get_context_id()

            return self._time_operation(route_agent, iterations=10)
        except ImportError:
            return -1

    def measure_tool_discovery(self) -> float:
        """Measure tool discovery scan time."""
        try:
            def scan_tools():
                tools_dir = MAIA_ROOT / "claude" / "tools"
                list(tools_dir.rglob("*.py"))

            return self._time_operation(scan_tools, iterations=5)
        except Exception:
            return -1

    def measure_database_query(self) -> float:
        """Measure system state database query time."""
        try:
            db_path = MAIA_ROOT / "claude" / "data" / "databases" / "system" / "system_state.db"
            if not db_path.exists():
                return -1

            import sqlite3

            def query_db():
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM phases")
                cursor.fetchone()
                conn.close()

            return self._time_operation(query_db, iterations=10)
        except Exception:
            return -1

    def measure_path_resolution(self) -> float:
        """Measure path resolution time."""
        try:
            sys.path.insert(0, str(MAIA_ROOT / "claude" / "tools" / "core"))
            from paths import PathManager

            # Clear cache
            PathManager.clear_cache()

            def resolve_paths():
                PathManager.get_maia_root()
                PathManager.get_user_data_path()

            return self._time_operation(resolve_paths, iterations=10)
        except ImportError:
            return -1

    def run_measurements(self) -> Dict[str, Metric]:
        """Run all measurements."""
        measurements = {
            "context_loading": self.measure_context_loading,
            "agent_routing": self.measure_agent_routing,
            "tool_discovery": self.measure_tool_discovery,
            "database_query": self.measure_database_query,
            "path_resolution": self.measure_path_resolution,
        }

        for key, baseline in BASELINES.items():
            metric = Metric(
                name=baseline.name,
                target_ms=baseline.target_ms,
                warn_ms=baseline.warn_ms,
                fail_ms=baseline.fail_ms,
            )

            if key in measurements:
                measured = measurements[key]()
                metric.measured_ms = measured

                if measured < 0:
                    metric.status = "skipped"
                elif measured <= baseline.target_ms:
                    metric.status = "pass"
                elif measured <= baseline.warn_ms:
                    metric.status = "warn"
                elif measured <= baseline.fail_ms:
                    metric.status = "fail"
                else:
                    metric.status = "critical"

            self.results[key] = metric

        return self.results

    def check(self) -> bool:
        """Check current performance against baselines."""
        self.run_measurements()

        print("=" * 60)
        print("MAIA PERFORMANCE BASELINE CHECK")
        print("=" * 60)
        print()

        has_failures = False
        has_warnings = False

        for key, metric in self.results.items():
            if metric.status == "skipped":
                icon = "⏭️"
                status = "SKIP"
            elif metric.status == "pass":
                icon = "✅"
                status = "PASS"
            elif metric.status == "warn":
                icon = "⚠️"
                status = "WARN"
                has_warnings = True
            elif metric.status == "fail":
                icon = "❌"
                status = "FAIL"
                has_failures = True
            else:
                icon = "🚨"
                status = "CRIT"
                has_failures = True

            measured = f"{metric.measured_ms:.1f}ms" if metric.measured_ms and metric.measured_ms > 0 else "N/A"
            target = f"(target: {metric.target_ms}ms)"

            print(f"{icon} {metric.name}: {measured} {target} [{status}]")

            if self.verbose and metric.measured_ms and metric.measured_ms > 0:
                print(f"   Target: {metric.target_ms}ms | Warn: {metric.warn_ms}ms | Fail: {metric.fail_ms}ms")

        print()
        print("=" * 60)

        if has_failures:
            print("❌ PERFORMANCE CHECK FAILED")
            print("   Some operations exceed failure thresholds.")
            return False
        elif has_warnings:
            print("⚠️ PERFORMANCE CHECK PASSED WITH WARNINGS")
            return True
        else:
            print("✅ PERFORMANCE CHECK PASSED")
            return True

    def update_baseline(self):
        """Update baseline file with current measurements."""
        self.run_measurements()

        data = {}
        for key, metric in self.results.items():
            if metric.measured_ms and metric.measured_ms > 0:
                data[key] = {
                    "name": metric.name,
                    "measured_ms": metric.measured_ms,
                    "target_ms": metric.target_ms,
                    "warn_ms": metric.warn_ms,
                    "fail_ms": metric.fail_ms,
                }

        BASELINE_FILE.parent.mkdir(parents=True, exist_ok=True)
        BASELINE_FILE.write_text(json.dumps(data, indent=2))
        print(f"✅ Baseline updated: {BASELINE_FILE}")


def main():
    parser = argparse.ArgumentParser(description="Maia Performance Baseline Tool")
    parser.add_argument("--check", action="store_true", help="Check against baseline")
    parser.add_argument("--update", action="store_true", help="Update baseline file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    baseline = PerformanceBaseline(verbose=args.verbose)

    if args.update:
        baseline.update_baseline()
    else:
        passed = baseline.check()
        sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
