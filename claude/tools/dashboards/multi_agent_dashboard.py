"""
Multi-Agent Dashboard - Real-Time Workflow Visualization

Provides real-time monitoring and visualization of multi-agent workflow execution,
performance metrics, agent activity, and historical trends.

Based on: claude/data/AGENT_EVOLUTION_PROJECT_PLAN.md Phase 111, Workflow #9

Architecture:
    Data Collection → Aggregation → Visualization → Real-Time Updates

Key Features:
- Real-time workflow execution monitoring
- Performance metrics (latency, success rate, throughput)
- Agent activity tracking (handoffs, executions, errors)
- Historical trend visualization
- Markdown-based dashboard output
"""

import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict


@dataclass
class WorkflowStats:
    """Statistics for a single workflow execution"""
    workflow_name: str
    chain_id: str
    status: str
    start_time: datetime
    end_time: Optional[datetime]
    duration_ms: float
    subtasks_total: int
    subtasks_completed: int
    subtasks_failed: int
    retry_attempts: int
    agents_used: List[str]
    total_tokens: int


@dataclass
class AgentStats:
    """Statistics for agent activity"""
    agent_name: str
    total_executions: int
    successful_executions: int
    failed_executions: int
    total_tokens: int
    average_latency_ms: float
    handoffs_initiated: int
    handoffs_received: int


@dataclass
class SystemMetrics:
    """Overall system performance metrics"""
    time_window: str
    total_workflows: int
    successful_workflows: int
    failed_workflows: int
    partial_workflows: int
    average_duration_ms: float
    total_tokens: int
    total_retry_attempts: int
    active_agents: int
    total_handoffs: int
    success_rate: float
    throughput_per_hour: float


class DashboardDataCollector:
    """Collects data from various sources for dashboard display"""

    def __init__(self, base_dir: Path = None):
        if base_dir is None:
            base_dir = Path(__file__).parent.parent.parent
        self.base_dir = base_dir
        self.chain_executions_dir = base_dir / "context" / "session" / "chain_executions"
        self.swarm_history_dir = base_dir / "context" / "session" / "swarm_history"
        self.performance_dir = base_dir / "context" / "session" / "performance"

    def collect_workflow_data(self, time_window_hours: int = 24) -> List[WorkflowStats]:
        """
        Collect workflow execution data from chain execution audit trails.

        Args:
            time_window_hours: Look back this many hours

        Returns:
            List of WorkflowStats for executions in time window
        """
        workflows = []
        cutoff_time = datetime.now() - timedelta(hours=time_window_hours)

        if not self.chain_executions_dir.exists():
            return workflows

        for audit_file in self.chain_executions_dir.glob("*.jsonl"):
            try:
                # Read audit trail
                audit_data = json.loads(audit_file.read_text())

                # Parse start time
                start_time = datetime.fromisoformat(audit_data["start_time"])
                if start_time < cutoff_time:
                    continue

                # Parse end time
                end_time = None
                if audit_data.get("end_time"):
                    end_time = datetime.fromisoformat(audit_data["end_time"])

                # Calculate duration
                if end_time:
                    duration_ms = (end_time - start_time).total_seconds() * 1000
                else:
                    duration_ms = 0.0

                # Count subtask statuses
                subtasks = audit_data.get("subtask_executions", [])
                completed = sum(1 for st in subtasks if st.get("status") == "completed")
                failed = sum(1 for st in subtasks if st.get("status") == "failed")

                # Collect agents used
                agents_used = list(set(
                    st.get("agent_used", "default")
                    for st in subtasks
                    if st.get("agent_used")
                ))

                # Count retry attempts
                retry_attempts = sum(st.get("retry_attempts", 0) for st in subtasks)

                workflows.append(WorkflowStats(
                    workflow_name=audit_data.get("workflow_name", "unknown"),
                    chain_id=audit_data.get("chain_id", "unknown"),
                    status=audit_data.get("status", "unknown"),
                    start_time=start_time,
                    end_time=end_time,
                    duration_ms=duration_ms,
                    subtasks_total=len(subtasks),
                    subtasks_completed=completed,
                    subtasks_failed=failed,
                    retry_attempts=retry_attempts,
                    agents_used=agents_used,
                    total_tokens=audit_data.get("total_tokens", 0)
                ))

            except (json.JSONDecodeError, KeyError, ValueError) as e:
                # Skip malformed audit files
                continue

        return workflows

    def collect_agent_data(self, workflows: List[WorkflowStats]) -> Dict[str, AgentStats]:
        """
        Aggregate agent statistics from workflow data.

        Args:
            workflows: List of WorkflowStats

        Returns:
            Dict mapping agent name to AgentStats
        """
        agent_data = defaultdict(lambda: {
            "executions": [],
            "tokens": 0,
            "handoffs_initiated": 0,
            "handoffs_received": 0
        })

        # Aggregate from workflows
        for workflow in workflows:
            for agent in workflow.agents_used:
                agent_data[agent]["executions"].append({
                    "success": workflow.status == "completed",
                    "duration_ms": workflow.duration_ms / max(len(workflow.agents_used), 1)
                })
                agent_data[agent]["tokens"] += workflow.total_tokens / max(len(workflow.agents_used), 1)

        # Also check swarm history for handoffs
        if self.swarm_history_dir.exists():
            for history_file in self.swarm_history_dir.glob("*.jsonl"):
                try:
                    history = json.loads(history_file.read_text())
                    for handoff in history.get("handoffs", []):
                        from_agent = handoff.get("from_agent", "unknown")
                        to_agent = handoff.get("to_agent", "unknown")
                        agent_data[from_agent]["handoffs_initiated"] += 1
                        agent_data[to_agent]["handoffs_received"] += 1
                except (json.JSONDecodeError, KeyError):
                    continue

        # Convert to AgentStats objects
        agent_stats = {}
        for agent_name, data in agent_data.items():
            executions = data["executions"]
            if not executions:
                continue

            successful = sum(1 for e in executions if e["success"])
            failed = len(executions) - successful
            avg_latency = sum(e["duration_ms"] for e in executions) / len(executions)

            agent_stats[agent_name] = AgentStats(
                agent_name=agent_name,
                total_executions=len(executions),
                successful_executions=successful,
                failed_executions=failed,
                total_tokens=int(data["tokens"]),
                average_latency_ms=avg_latency,
                handoffs_initiated=data["handoffs_initiated"],
                handoffs_received=data["handoffs_received"]
            )

        return agent_stats

    def calculate_system_metrics(self, workflows: List[WorkflowStats],
                                 agent_stats: Dict[str, AgentStats],
                                 time_window_hours: int) -> SystemMetrics:
        """
        Calculate overall system performance metrics.

        Args:
            workflows: List of WorkflowStats
            agent_stats: Dict of AgentStats
            time_window_hours: Time window for metrics

        Returns:
            SystemMetrics object
        """
        if not workflows:
            return SystemMetrics(
                time_window=f"Last {time_window_hours} hours",
                total_workflows=0,
                successful_workflows=0,
                failed_workflows=0,
                partial_workflows=0,
                average_duration_ms=0.0,
                total_tokens=0,
                total_retry_attempts=0,
                active_agents=0,
                total_handoffs=0,
                success_rate=0.0,
                throughput_per_hour=0.0
            )

        # Count by status
        completed = sum(1 for w in workflows if w.status == "completed")
        failed = sum(1 for w in workflows if w.status == "failed")
        partial = sum(1 for w in workflows if w.status == "partial")

        # Calculate averages
        avg_duration = sum(w.duration_ms for w in workflows if w.duration_ms > 0) / max(
            sum(1 for w in workflows if w.duration_ms > 0), 1
        )
        total_tokens = sum(w.total_tokens for w in workflows)
        total_retries = sum(w.retry_attempts for w in workflows)

        # Agent metrics
        total_handoffs = sum(
            a.handoffs_initiated for a in agent_stats.values()
        )

        # Success rate
        success_rate = (completed / len(workflows) * 100) if workflows else 0.0

        # Throughput (workflows per hour)
        throughput = len(workflows) / time_window_hours if time_window_hours > 0 else 0.0

        return SystemMetrics(
            time_window=f"Last {time_window_hours} hours",
            total_workflows=len(workflows),
            successful_workflows=completed,
            failed_workflows=failed,
            partial_workflows=partial,
            average_duration_ms=avg_duration,
            total_tokens=total_tokens,
            total_retry_attempts=total_retries,
            active_agents=len(agent_stats),
            total_handoffs=total_handoffs,
            success_rate=success_rate,
            throughput_per_hour=throughput
        )


class DashboardRenderer:
    """Renders dashboard data as formatted markdown"""

    def render_system_overview(self, metrics: SystemMetrics) -> str:
        """Render system overview section"""
        return f"""# Multi-Agent System Dashboard

**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Time Window**: {metrics.time_window}

## System Overview

| Metric | Value | Status |
|--------|-------|--------|
| **Total Workflows** | {metrics.total_workflows} | {"🟢" if metrics.total_workflows > 0 else "⚪"} |
| **Success Rate** | {metrics.success_rate:.1f}% | {"🟢" if metrics.success_rate >= 90 else "🟡" if metrics.success_rate >= 70 else "🔴"} |
| **Successful** | {metrics.successful_workflows} | 🟢 |
| **Failed** | {metrics.failed_workflows} | {"🔴" if metrics.failed_workflows > 0 else "🟢"} |
| **Partial** | {metrics.partial_workflows} | {"🟡" if metrics.partial_workflows > 0 else "🟢"} |
| **Avg Duration** | {metrics.average_duration_ms:.0f}ms | {"🟢" if metrics.average_duration_ms < 5000 else "🟡" if metrics.average_duration_ms < 10000 else "🔴"} |
| **Throughput** | {metrics.throughput_per_hour:.2f}/hour | 📊 |
| **Total Tokens** | {metrics.total_tokens:,} | 💰 |
| **Retry Attempts** | {metrics.total_retry_attempts} | {"🟢" if metrics.total_retry_attempts < 10 else "🟡"} |
| **Active Agents** | {metrics.active_agents} | 🤖 |
| **Total Handoffs** | {metrics.total_handoffs} | 🔗 |

"""

    def render_recent_workflows(self, workflows: List[WorkflowStats], limit: int = 10) -> str:
        """Render recent workflow executions"""
        # Sort by start time (most recent first)
        recent = sorted(workflows, key=lambda w: w.start_time, reverse=True)[:limit]

        output = f"## Recent Workflow Executions (Last {limit})\n\n"

        if not recent:
            output += "_No workflows executed in time window_\n\n"
            return output

        output += "| Workflow | Status | Duration | Subtasks | Retries | Agents | Started |\n"
        output += "|----------|--------|----------|----------|---------|--------|----------|\n"

        for w in recent:
            status_icon = {
                "completed": "✅",
                "failed": "❌",
                "partial": "⚠️",
                "running": "⏳"
            }.get(w.status, "❓")

            duration_str = f"{w.duration_ms:.0f}ms" if w.duration_ms > 0 else "N/A"
            subtasks_str = f"{w.subtasks_completed}/{w.subtasks_total}"
            agents_str = f"{len(w.agents_used)}" if w.agents_used else "0"
            time_str = w.start_time.strftime("%H:%M:%S")

            output += f"| {w.workflow_name[:20]} | {status_icon} {w.status} | {duration_str} | {subtasks_str} | {w.retry_attempts} | {agents_str} | {time_str} |\n"

        output += "\n"
        return output

    def render_agent_performance(self, agent_stats: Dict[str, AgentStats], limit: int = 15) -> str:
        """Render agent performance metrics"""
        output = f"## Agent Performance (Top {limit} by Activity)\n\n"

        if not agent_stats:
            output += "_No agent activity in time window_\n\n"
            return output

        # Sort by total executions
        sorted_agents = sorted(
            agent_stats.values(),
            key=lambda a: a.total_executions,
            reverse=True
        )[:limit]

        output += "| Agent | Executions | Success Rate | Avg Latency | Tokens | Handoffs (Out/In) |\n"
        output += "|-------|------------|--------------|-------------|--------|-------------------|\n"

        for agent in sorted_agents:
            success_rate = (agent.successful_executions / agent.total_executions * 100) if agent.total_executions > 0 else 0.0
            success_icon = "🟢" if success_rate >= 90 else "🟡" if success_rate >= 70 else "🔴"

            latency_str = f"{agent.average_latency_ms:.0f}ms"
            handoffs_str = f"{agent.handoffs_initiated}/{agent.handoffs_received}"

            output += f"| {agent.agent_name[:25]} | {agent.total_executions} | {success_icon} {success_rate:.0f}% | {latency_str} | {agent.total_tokens:,} | {handoffs_str} |\n"

        output += "\n"
        return output

    def render_error_summary(self, workflows: List[WorkflowStats]) -> str:
        """Render error summary for failed workflows"""
        failed = [w for w in workflows if w.status == "failed"]

        output = "## Error Summary\n\n"

        if not failed:
            output += "✅ **No failures in time window**\n\n"
            return output

        output += f"⚠️ **{len(failed)} workflow(s) failed**\n\n"

        # Group by workflow name
        failures_by_workflow = defaultdict(int)
        for w in failed:
            failures_by_workflow[w.workflow_name] += 1

        output += "| Workflow | Failure Count |\n"
        output += "|----------|---------------|\n"

        for workflow_name, count in sorted(failures_by_workflow.items(), key=lambda x: x[1], reverse=True):
            output += f"| {workflow_name} | {count} |\n"

        output += "\n"
        return output

    def render_full_dashboard(self, metrics: SystemMetrics, workflows: List[WorkflowStats],
                             agent_stats: Dict[str, AgentStats]) -> str:
        """Render complete dashboard"""
        dashboard = self.render_system_overview(metrics)
        dashboard += self.render_recent_workflows(workflows)
        dashboard += self.render_agent_performance(agent_stats)
        dashboard += self.render_error_summary(workflows)

        dashboard += "---\n\n"
        dashboard += f"_Dashboard auto-generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_\n"

        return dashboard


class MultiAgentDashboard:
    """
    Main dashboard class for multi-agent system monitoring.

    Usage:
        dashboard = MultiAgentDashboard()

        # Generate dashboard for last 24 hours
        markdown = dashboard.generate_dashboard(time_window_hours=24)
        print(markdown)

        # Or save to file
        dashboard.save_dashboard("dashboard.md", time_window_hours=24)
    """

    def __init__(self, base_dir: Path = None):
        self.collector = DashboardDataCollector(base_dir)
        self.renderer = DashboardRenderer()

    def generate_dashboard(self, time_window_hours: int = 24) -> str:
        """
        Generate complete dashboard markdown.

        Args:
            time_window_hours: Look back this many hours

        Returns:
            Markdown string with complete dashboard
        """
        # Collect data
        workflows = self.collector.collect_workflow_data(time_window_hours)
        agent_stats = self.collector.collect_agent_data(workflows)
        system_metrics = self.collector.calculate_system_metrics(
            workflows, agent_stats, time_window_hours
        )

        # Render dashboard
        return self.renderer.render_full_dashboard(system_metrics, workflows, agent_stats)

    def save_dashboard(self, output_path: Path, time_window_hours: int = 24):
        """
        Generate and save dashboard to file.

        Args:
            output_path: Path to save dashboard markdown
            time_window_hours: Look back this many hours
        """
        dashboard_md = self.generate_dashboard(time_window_hours)
        Path(output_path).write_text(dashboard_md)


def main():
    """CLI entry point for dashboard generation"""
    import argparse

    parser = argparse.ArgumentParser(description="Generate Multi-Agent System Dashboard")
    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="Time window in hours (default: 24)"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file path (default: print to stdout)"
    )

    args = parser.parse_args()

    dashboard = MultiAgentDashboard()

    if args.output:
        dashboard.save_dashboard(Path(args.output), args.hours)
        print(f"Dashboard saved to {args.output}")
    else:
        print(dashboard.generate_dashboard(args.hours))


if __name__ == "__main__":
    main()
