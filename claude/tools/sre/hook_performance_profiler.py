#!/usr/bin/env python3
"""
Phase 127: Hook Performance Profiler
Establishes performance baselines and tracks hook latency over time
"""

import sqlite3
import subprocess
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

class HookPerformanceProfiler:
    """Profile and track hook performance metrics"""

    def __init__(self):
        self.maia_root = Path(__file__).resolve().parents[3]
        self.db_path = self.maia_root / "claude" / "data" / "databases" / "system" / "performance_metrics.db"
        self.hook_path = self.maia_root / "claude" / "hooks" / "user-prompt-submit"
        self._init_database()

    def _init_database(self):
        """Initialize performance metrics database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Hook performance metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hook_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                message_type TEXT NOT NULL,
                message_sample TEXT,
                latency_ms INTEGER NOT NULL,
                output_lines INTEGER NOT NULL,
                exit_code INTEGER NOT NULL,
                git_commit TEXT
            )
        """)

        # Performance baselines table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_baselines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                message_type TEXT NOT NULL,
                p50_latency_ms INTEGER,
                p95_latency_ms INTEGER,
                p99_latency_ms INTEGER,
                avg_output_lines REAL,
                sample_count INTEGER
            )
        """)

        conn.commit()
        conn.close()

    def profile_hook(self, message: str, message_type: str = "normal") -> Dict:
        """
        Profile single hook execution

        Args:
            message: Test message to send to hook
            message_type: "normal", "build", or "slash_command"

        Returns:
            Dict with latency_ms, output_lines, exit_code
        """
        import os

        env = os.environ.copy()
        env["CLAUDE_USER_MESSAGE"] = message

        start = time.time()
        result = subprocess.run(
            ["bash", str(self.hook_path)],
            env=env,
            capture_output=True,
            text=True
        )
        end = time.time()

        latency_ms = int((end - start) * 1000)
        output_lines = len(result.stdout.splitlines()) if result.stdout else 0

        return {
            "latency_ms": latency_ms,
            "output_lines": output_lines,
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }

    def establish_baseline(self, samples_per_type: int = 10) -> Dict:
        """
        Establish performance baseline for different message types

        Args:
            samples_per_type: Number of samples to collect per message type

        Returns:
            Dict with baseline metrics per message type
        """
        print(f"🔍 Establishing performance baseline ({samples_per_type} samples per type)...")

        message_scenarios = {
            "normal": [
                "What is the system status?",
                "Explain this concept",
                "Analyze the data",
                "Check the configuration",
                "Optimize the query performance"
            ],
            "build": [
                "Create a new function",
                "Build a dashboard",
                "Implement feature X",
                "Add tests for module Y",
                "Develop new tool"
            ],
            "slash_command": [
                "/help",
                "/compact",
                "/save",
                "/status",
                "/list"
            ]
        }

        results = {}

        for msg_type, messages in message_scenarios.items():
            print(f"\n  Testing {msg_type} messages...")
            latencies = []
            output_counts = []

            for i in range(samples_per_type):
                message = messages[i % len(messages)]
                profile = self.profile_hook(message, msg_type)
                latencies.append(profile["latency_ms"])
                output_counts.append(profile["output_lines"])

                # Store in database
                self._record_measurement(message, msg_type, profile)

                print(f"    Sample {i+1}/{samples_per_type}: {profile['latency_ms']}ms, {profile['output_lines']} lines")

            # Calculate percentiles
            latencies.sort()
            p50 = latencies[len(latencies) // 2]
            p95 = latencies[int(len(latencies) * 0.95)]
            p99 = latencies[int(len(latencies) * 0.99)]
            avg_output = sum(output_counts) / len(output_counts)

            results[msg_type] = {
                "p50_latency_ms": p50,
                "p95_latency_ms": p95,
                "p99_latency_ms": p99,
                "avg_output_lines": avg_output,
                "sample_count": samples_per_type
            }

            # Store baseline
            self._record_baseline(msg_type, results[msg_type])

        return results

    def _record_measurement(self, message: str, message_type: str, profile: Dict):
        """Record single performance measurement"""
        try:
            git_commit = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True,
                text=True,
                cwd=self.maia_root
            ).stdout.strip()
        except:
            git_commit = "unknown"

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO hook_performance
            (timestamp, message_type, message_sample, latency_ms, output_lines, exit_code, git_commit)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            message_type,
            message[:50],
            profile["latency_ms"],
            profile["output_lines"],
            profile["exit_code"],
            git_commit
        ))

        conn.commit()
        conn.close()

    def _record_baseline(self, message_type: str, baseline: Dict):
        """Record performance baseline"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO performance_baselines
            (timestamp, message_type, p50_latency_ms, p95_latency_ms, p99_latency_ms, avg_output_lines, sample_count)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            message_type,
            baseline["p50_latency_ms"],
            baseline["p95_latency_ms"],
            baseline["p99_latency_ms"],
            baseline["avg_output_lines"],
            baseline["sample_count"]
        ))

        conn.commit()
        conn.close()

    def get_latest_baseline(self) -> Dict:
        """Get most recent baseline metrics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT message_type, p50_latency_ms, p95_latency_ms, p99_latency_ms, avg_output_lines, timestamp
            FROM performance_baselines
            ORDER BY timestamp DESC
            LIMIT 10
        """)

        baselines = {}
        for row in cursor.fetchall():
            msg_type, p50, p95, p99, avg_out, ts = row
            if msg_type not in baselines:  # Get most recent for each type
                baselines[msg_type] = {
                    "p50_latency_ms": p50,
                    "p95_latency_ms": p95,
                    "p99_latency_ms": p99,
                    "avg_output_lines": avg_out,
                    "timestamp": ts
                }

        conn.close()
        return baselines

    def print_baseline_report(self):
        """Print formatted baseline report"""
        baselines = self.get_latest_baseline()

        print("\n" + "=" * 70)
        print("  Hook Performance Baseline Report")
        print("=" * 70)

        for msg_type, metrics in baselines.items():
            print(f"\n{msg_type.upper()} Messages:")
            print(f"  P50 Latency: {metrics['p50_latency_ms']}ms")
            print(f"  P95 Latency: {metrics['p95_latency_ms']}ms")
            print(f"  P99 Latency: {metrics['p99_latency_ms']}ms")
            print(f"  Avg Output:  {metrics['avg_output_lines']:.1f} lines")
            print(f"  Recorded:    {metrics['timestamp'][:19]}")

        print("\n" + "=" * 70)

        # SLO evaluation
        print("\nSLO Compliance:")

        for msg_type, metrics in baselines.items():
            if msg_type == "slash_command":
                # Slash commands should be instant
                if metrics["p95_latency_ms"] <= 10:
                    print(f"  ✅ {msg_type}: {metrics['p95_latency_ms']}ms ≤ 10ms (EXCELLENT)")
                else:
                    print(f"  ⚠️  {msg_type}: {metrics['p95_latency_ms']}ms > 10ms (REVIEW NEEDED)")
            elif msg_type == "build":
                # Build requests can be slower (capability checking)
                if metrics["p95_latency_ms"] <= 1000:
                    print(f"  ✅ {msg_type}: {metrics['p95_latency_ms']}ms ≤ 1000ms (ACCEPTABLE)")
                else:
                    print(f"  ❌ {msg_type}: {metrics['p95_latency_ms']}ms > 1000ms (OPTIMIZATION NEEDED)")
            else:  # normal
                # Normal messages should be fast
                if metrics["p95_latency_ms"] <= 100:
                    print(f"  ✅ {msg_type}: {metrics['p95_latency_ms']}ms ≤ 100ms (GOOD)")
                else:
                    print(f"  ⚠️  {msg_type}: {metrics['p95_latency_ms']}ms > 100ms (NEEDS OPTIMIZATION)")

        print("")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Hook Performance Profiler")
    parser.add_argument("command", choices=["baseline", "report", "test"],
                       help="Command to execute")
    parser.add_argument("--samples", type=int, default=10,
                       help="Number of samples per message type (default: 10)")

    args = parser.parse_args()

    profiler = HookPerformanceProfiler()

    if args.command == "baseline":
        baselines = profiler.establish_baseline(args.samples)
        profiler.print_baseline_report()

    elif args.command == "report":
        profiler.print_baseline_report()

    elif args.command == "test":
        # Quick test
        print("🧪 Quick Performance Test")
        print("\nNormal message:")
        result = profiler.profile_hook("What is the system status?", "normal")
        print(f"  Latency: {result['latency_ms']}ms")
        print(f"  Output:  {result['output_lines']} lines")

        print("\nBuild message:")
        result = profiler.profile_hook("Create a new function", "build")
        print(f"  Latency: {result['latency_ms']}ms")
        print(f"  Output:  {result['output_lines']} lines")

        print("\nSlash command:")
        result = profiler.profile_hook("/help", "slash_command")
        print(f"  Latency: {result['latency_ms']}ms")
        print(f"  Output:  {result['output_lines']} lines")


if __name__ == "__main__":
    main()
