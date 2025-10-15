#!/usr/bin/env python3
"""
Agent Performance Dashboard

Real-time dashboard for monitoring agent routing performance, success rates,
execution times, and bottlenecks. Integrates with Phase 121 automatic routing
and performance monitoring system.

Usage:
    python3 claude/tools/orchestration/agent_performance_dashboard.py
    python3 claude/tools/orchestration/agent_performance_dashboard.py --json
    python3 claude/tools/orchestration/agent_performance_dashboard.py --watch

Author: Maia (Phase 121 Performance Monitoring)
Created: 2025-10-15
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Add maia root to path
MAIA_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

try:
    from claude.tools.orchestration.performance_monitoring import (
        MetricsCollector, PerformanceAnalytics
    )
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False


class AgentPerformanceDashboard:
    """
    Real-time dashboard for agent performance monitoring.

    Displays:
    - Overall system health
    - Per-agent statistics (success rate, avg time, handoffs)
    - Bottleneck detection
    - Failure analysis
    - Routing strategy effectiveness
    """

    def __init__(self):
        """Initialize dashboard with metrics collector and analytics."""
        if not MONITORING_AVAILABLE:
            raise ImportError("Performance monitoring not available")

        self.collector = MetricsCollector()
        self.analytics = PerformanceAnalytics(self.collector)

    def generate_dashboard(self, format: str = "terminal") -> str:
        """
        Generate dashboard in specified format.

        Args:
            format: "terminal" for rich terminal output, "json" for JSON output

        Returns:
            Formatted dashboard string
        """
        if format == "json":
            return self._generate_json()
        else:
            return self._generate_terminal()

    def _generate_terminal(self) -> str:
        """Generate rich terminal dashboard."""
        lines = []

        # Header
        lines.append("")
        lines.append("╭" + "─" * 78 + "╮")
        lines.append("│" + " 🎯 MAIA AGENT PERFORMANCE DASHBOARD ".center(78) + "│")
        lines.append("│" + f" {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ".center(78) + "│")
        lines.append("╰" + "─" * 78 + "╯")
        lines.append("")

        # Overall summary
        summary = self.analytics.get_performance_summary()

        if summary['total_executions'] == 0:
            lines.append("📊 No agent execution data available yet")
            lines.append("")
            lines.append("💡 Data will appear once automatic agent routing is used")
            lines.append("   Try queries like: 'Help me optimize Azure costs'")
            lines.append("")
            return "\n".join(lines)

        lines.append("📊 SYSTEM OVERVIEW")
        lines.append("─" * 80)
        lines.append(f"  Total Executions:     {summary['total_executions']}")
        lines.append(f"  Unique Agents:        {summary['unique_agents']}")
        lines.append(f"  Overall Success Rate: {summary['overall_success_rate']:.1%}")
        lines.append(f"  Avg Execution Time:   {summary['avg_execution_time_ms']:.0f}ms")

        # Time range
        if summary.get('time_range'):
            lines.append(f"  Data Range:           {summary['time_range']}")

        lines.append("")

        # Agent statistics
        lines.append("🤖 AGENT PERFORMANCE")
        lines.append("─" * 80)

        agent_stats = self.analytics.get_all_agent_statistics()

        if not agent_stats:
            lines.append("  No agent statistics available")
        else:
            # Sort by executions (most used first)
            agent_stats.sort(key=lambda x: x['total_executions'], reverse=True)

            for stats in agent_stats[:10]:  # Top 10 agents
                agent_name = stats['agent_name']
                executions = stats['total_executions']
                success_rate = stats['success_rate']
                avg_time = stats['avg_execution_time_ms']
                handoffs = stats['total_handoffs']

                # Success indicator
                if success_rate >= 0.95:
                    indicator = "✅"
                elif success_rate >= 0.80:
                    indicator = "⚠️ "
                else:
                    indicator = "❌"

                lines.append(f"  {indicator} {agent_name}")
                lines.append(f"     Executions: {executions:3d} | Success: {success_rate:5.1%} | Avg Time: {avg_time:6.0f}ms | Handoffs: {handoffs}")

        lines.append("")

        # Bottlenecks
        lines.append("⚠️  PERFORMANCE BOTTLENECKS (>2000ms)")
        lines.append("─" * 80)

        bottlenecks = self.analytics.identify_bottlenecks(threshold_ms=2000)

        if not bottlenecks:
            lines.append("  ✅ No bottlenecks detected - all agents performing well")
        else:
            for bottleneck in bottlenecks:
                agent_name = bottleneck['agent_name']
                avg_time = bottleneck['avg_execution_time_ms']
                lines.append(f"  🐌 {agent_name}: {avg_time:.0f}ms avg")

        lines.append("")

        # Failure analysis
        lines.append("❌ FAILURE ANALYSIS")
        lines.append("─" * 80)

        failures = self.analytics.get_failure_analysis()

        lines.append(f"  Total Failures:  {failures['total_failures']}")
        lines.append(f"  Failure Rate:    {failures['failure_rate']:.1%}")

        if failures['failures_by_agent']:
            lines.append("")
            lines.append("  Failures by Agent:")
            for agent, count in sorted(failures['failures_by_agent'].items(),
                                       key=lambda x: x[1], reverse=True)[:5]:
                lines.append(f"    • {agent}: {count}")

        if failures['common_errors']:
            lines.append("")
            lines.append("  Common Error Types:")
            for error, count in failures['common_errors'].items()[:5]:
                lines.append(f"    • {error}: {count}")

        lines.append("")

        # Routing strategy effectiveness
        lines.append("🎯 ROUTING STRATEGY EFFECTIVENESS")
        lines.append("─" * 80)

        strategy_stats = self._get_strategy_stats()

        if not strategy_stats:
            lines.append("  No routing strategy data available")
        else:
            for strategy, stats in strategy_stats.items():
                lines.append(f"  {strategy.upper().replace('_', ' ')}:")
                lines.append(f"    Executions: {stats['count']} | Success: {stats['success_rate']:.1%} | Avg Time: {stats['avg_time']:.0f}ms")

        lines.append("")
        lines.append("╰" + "─" * 78 + "╯")
        lines.append("")

        return "\n".join(lines)

    def _generate_json(self) -> str:
        """Generate JSON output."""
        summary = self.analytics.get_performance_summary()
        agent_stats = self.analytics.get_all_agent_statistics()
        bottlenecks = self.analytics.identify_bottlenecks(threshold_ms=2000)
        failures = self.analytics.get_failure_analysis()
        strategy_stats = self._get_strategy_stats()

        data = {
            "timestamp": datetime.now().isoformat(),
            "summary": summary,
            "agents": agent_stats,
            "bottlenecks": bottlenecks,
            "failures": failures,
            "routing_strategies": strategy_stats
        }

        return json.dumps(data, indent=2)

    def _get_strategy_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics grouped by routing strategy."""
        metrics = self.collector.get_recent_metrics(limit=1000)  # Last 1000 executions

        strategy_data = {}

        for metric in metrics:
            strategy = metric.strategy or "unknown"

            if strategy not in strategy_data:
                strategy_data[strategy] = {
                    'count': 0,
                    'successes': 0,
                    'total_time': 0
                }

            strategy_data[strategy]['count'] += 1
            if metric.success:
                strategy_data[strategy]['successes'] += 1
            strategy_data[strategy]['total_time'] += metric.execution_time_ms

        # Calculate aggregates
        result = {}
        for strategy, data in strategy_data.items():
            result[strategy] = {
                'count': data['count'],
                'success_rate': data['successes'] / data['count'] if data['count'] > 0 else 0,
                'avg_time': data['total_time'] / data['count'] if data['count'] > 0 else 0
            }

        return result

    def watch_mode(self, interval: int = 5):
        """
        Watch mode - continuously refresh dashboard.

        Args:
            interval: Refresh interval in seconds
        """
        try:
            while True:
                # Clear screen (cross-platform)
                print("\033[2J\033[H", end="")

                # Display dashboard
                print(self.generate_dashboard())

                # Wait for interval
                print(f"\n🔄 Refreshing in {interval}s... (Ctrl+C to exit)")
                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n\n👋 Dashboard closed")
            sys.exit(0)


def main():
    """CLI interface for agent performance dashboard."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Agent Performance Dashboard - Monitor routing and execution metrics"
    )
    parser.add_argument(
        '--format',
        choices=['terminal', 'json'],
        default='terminal',
        help='Output format (default: terminal)'
    )
    parser.add_argument(
        '--watch',
        action='store_true',
        help='Watch mode - continuously refresh dashboard'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=5,
        help='Refresh interval for watch mode in seconds (default: 5)'
    )

    args = parser.parse_args()

    # Check if monitoring available
    if not MONITORING_AVAILABLE:
        print("❌ Error: Performance monitoring system not available", file=sys.stderr)
        print("", file=sys.stderr)
        print("This requires the performance monitoring system to be set up.", file=sys.stderr)
        sys.exit(1)

    try:
        dashboard = AgentPerformanceDashboard()

        if args.watch:
            dashboard.watch_mode(interval=args.interval)
        else:
            output = dashboard.generate_dashboard(format=args.format)
            print(output)

    except Exception as e:
        print(f"❌ Error generating dashboard: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
