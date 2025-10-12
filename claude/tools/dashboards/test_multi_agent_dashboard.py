"""
Test Suite for Multi-Agent Dashboard

Comprehensive tests for data collection, aggregation, and visualization.
"""

import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from claude.tools.dashboards.multi_agent_dashboard import (
    MultiAgentDashboard, DashboardDataCollector, DashboardRenderer,
    WorkflowStats, AgentStats, SystemMetrics
)


class TestRunner:
    """Simple test runner that tracks assertions"""

    def __init__(self):
        self.passed = 0
        self.total = 0

    def assert_true(self, condition, message):
        self.total += 1
        if condition:
            print(f"✅ {message}")
            self.passed += 1
        else:
            print(f"❌ {message}")

    def assert_equal(self, actual, expected, message):
        self.total += 1
        if actual == expected:
            print(f"✅ {message}")
            self.passed += 1
        else:
            print(f"❌ {message}")
            print(f"   Expected: {expected}")
            print(f"   Actual: {actual}")

    def assert_in(self, item, container, message):
        self.total += 1
        if item in container:
            print(f"✅ {message}")
            self.passed += 1
        else:
            print(f"❌ {message}")

    def assert_greater(self, actual, minimum, message):
        self.total += 1
        if actual > minimum:
            print(f"✅ {message} (value: {actual})")
            self.passed += 1
        else:
            print(f"❌ {message}")
            print(f"   Expected > {minimum}, got {actual}")

    def summary(self):
        print(f"\n{'='*60}")
        print(f"Test Results: {self.passed}/{self.total} passed")
        if self.passed == self.total:
            print("✅ All tests passed!")
        else:
            print(f"❌ {self.total - self.passed} tests failed")
        print(f"{'='*60}\n")


def create_test_workflow_audit(temp_dir: Path, chain_id: str, status: str,
                               subtasks_count: int = 3, retry_attempts: int = 0) -> Path:
    """Helper to create test workflow audit file"""
    start_time = datetime.now() - timedelta(hours=1)
    end_time = datetime.now()

    audit_data = {
        "chain_id": chain_id,
        "workflow_name": "test_workflow",
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "status": status,
        "initial_input": {"test": "input"},
        "subtask_executions": [
            {
                "subtask_id": i,
                "name": f"Subtask {i}",
                "status": "completed" if status == "completed" else ("failed" if i == subtasks_count - 1 else "completed"),
                "agent_used": f"agent_{i % 2}",
                "tokens_used": 100 * i,
                "retry_attempts": retry_attempts if i == subtasks_count - 1 else 0
            }
            for i in range(1, subtasks_count + 1)
        ],
        "total_tokens": sum(100 * i for i in range(1, subtasks_count + 1)),
        "success_count": subtasks_count if status == "completed" else subtasks_count - 1,
        "failure_count": 0 if status == "completed" else 1
    }

    audit_file = temp_dir / f"{chain_id}.jsonl"
    audit_file.write_text(json.dumps(audit_data))
    return audit_file


def test_data_collection():
    """Test 1: Workflow data collection"""
    print("\n" + "="*60)
    print("Test 1: Workflow Data Collection")
    print("="*60)

    runner = TestRunner()

    with tempfile.TemporaryDirectory() as temp_dir:
        base_dir = Path(temp_dir)
        chain_dir = base_dir / "context" / "session" / "chain_executions"
        chain_dir.mkdir(parents=True)

        # Create test audit files
        create_test_workflow_audit(chain_dir, "chain_1", "completed", 3, 0)
        create_test_workflow_audit(chain_dir, "chain_2", "failed", 2, 2)
        create_test_workflow_audit(chain_dir, "chain_3", "partial", 4, 1)

        # Collect data
        collector = DashboardDataCollector(base_dir)
        workflows = collector.collect_workflow_data(time_window_hours=24)

        runner.assert_equal(len(workflows), 3, "Three workflows collected")

        # Check first workflow
        w1 = next(w for w in workflows if w.chain_id == "chain_1")
        runner.assert_equal(w1.status, "completed", "Workflow 1 status correct")
        runner.assert_equal(w1.subtasks_total, 3, "Workflow 1 subtasks count")
        runner.assert_equal(w1.retry_attempts, 0, "Workflow 1 no retries")

        # Check second workflow
        w2 = next(w for w in workflows if w.chain_id == "chain_2")
        runner.assert_equal(w2.status, "failed", "Workflow 2 status correct")
        runner.assert_equal(w2.retry_attempts, 2, "Workflow 2 has retries")

    runner.summary()
    return runner.passed == runner.total


def test_agent_aggregation():
    """Test 2: Agent statistics aggregation"""
    print("\n" + "="*60)
    print("Test 2: Agent Statistics Aggregation")
    print("="*60)

    runner = TestRunner()

    with tempfile.TemporaryDirectory() as temp_dir:
        base_dir = Path(temp_dir)
        chain_dir = base_dir / "context" / "session" / "chain_executions"
        chain_dir.mkdir(parents=True)

        # Create test workflows with agent data
        create_test_workflow_audit(chain_dir, "chain_1", "completed", 3, 0)
        create_test_workflow_audit(chain_dir, "chain_2", "completed", 3, 0)

        collector = DashboardDataCollector(base_dir)
        workflows = collector.collect_workflow_data(time_window_hours=24)
        agent_stats = collector.collect_agent_data(workflows)

        runner.assert_greater(len(agent_stats), 0, "Agent stats collected")

        # Check agent_0 stats (used in subtasks 2, 4, 6, etc.)
        if "agent_0" in agent_stats:
            agent_0 = agent_stats["agent_0"]
            runner.assert_greater(agent_0.total_executions, 0, "Agent 0 has executions")
            runner.assert_true(agent_0.average_latency_ms >= 0, "Agent 0 latency calculated")

    runner.summary()
    return runner.passed == runner.total


def test_system_metrics():
    """Test 3: System metrics calculation"""
    print("\n" + "="*60)
    print("Test 3: System Metrics Calculation")
    print("="*60)

    runner = TestRunner()

    with tempfile.TemporaryDirectory() as temp_dir:
        base_dir = Path(temp_dir)
        chain_dir = base_dir / "context" / "session" / "chain_executions"
        chain_dir.mkdir(parents=True)

        # Create mix of workflows
        create_test_workflow_audit(chain_dir, "chain_1", "completed", 3, 0)
        create_test_workflow_audit(chain_dir, "chain_2", "completed", 3, 0)
        create_test_workflow_audit(chain_dir, "chain_3", "failed", 2, 2)

        collector = DashboardDataCollector(base_dir)
        workflows = collector.collect_workflow_data(time_window_hours=24)
        agent_stats = collector.collect_agent_data(workflows)
        metrics = collector.calculate_system_metrics(workflows, agent_stats, 24)

        runner.assert_equal(metrics.total_workflows, 3, "Total workflows count")
        runner.assert_equal(metrics.successful_workflows, 2, "Successful workflows count")
        runner.assert_equal(metrics.failed_workflows, 1, "Failed workflows count")
        runner.assert_greater(metrics.success_rate, 60, "Success rate > 60%")
        runner.assert_greater(metrics.total_tokens, 0, "Total tokens > 0")
        runner.assert_equal(metrics.total_retry_attempts, 2, "Retry attempts tracked")

    runner.summary()
    return runner.passed == runner.total


def test_dashboard_rendering():
    """Test 4: Dashboard markdown rendering"""
    print("\n" + "="*60)
    print("Test 4: Dashboard Markdown Rendering")
    print("="*60)

    runner = TestRunner()

    # Create mock data
    metrics = SystemMetrics(
        time_window="Last 24 hours",
        total_workflows=10,
        successful_workflows=8,
        failed_workflows=2,
        partial_workflows=0,
        average_duration_ms=3500.0,
        total_tokens=5000,
        total_retry_attempts=3,
        active_agents=5,
        total_handoffs=12,
        success_rate=80.0,
        throughput_per_hour=0.42
    )

    workflows = [
        WorkflowStats(
            workflow_name="test_workflow",
            chain_id="chain_1",
            status="completed",
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration_ms=2000.0,
            subtasks_total=3,
            subtasks_completed=3,
            subtasks_failed=0,
            retry_attempts=0,
            agents_used=["agent_1", "agent_2"],
            total_tokens=500
        )
    ]

    agent_stats = {
        "agent_1": AgentStats(
            agent_name="agent_1",
            total_executions=10,
            successful_executions=9,
            failed_executions=1,
            total_tokens=3000,
            average_latency_ms=2500.0,
            handoffs_initiated=5,
            handoffs_received=3
        )
    }

    renderer = DashboardRenderer()

    # Test system overview
    overview = renderer.render_system_overview(metrics)
    runner.assert_in("System Overview", overview, "Overview section present")
    runner.assert_in("80.0%", overview, "Success rate shown")
    runner.assert_in("Total Workflows", overview, "Metrics table present")

    # Test recent workflows
    recent = renderer.render_recent_workflows(workflows)
    runner.assert_in("Recent Workflow Executions", recent, "Recent section present")
    runner.assert_in("test_workflow", recent, "Workflow name shown")

    # Test agent performance
    agent_perf = renderer.render_agent_performance(agent_stats)
    runner.assert_in("Agent Performance", agent_perf, "Agent section present")
    runner.assert_in("agent_1", agent_perf, "Agent name shown")

    # Test full dashboard
    full = renderer.render_full_dashboard(metrics, workflows, agent_stats)
    runner.assert_in("Multi-Agent System Dashboard", full, "Dashboard title present")
    runner.assert_greater(len(full), 500, "Dashboard has substantial content")

    runner.summary()
    return runner.passed == runner.total


def test_dashboard_integration():
    """Test 5: Full dashboard generation"""
    print("\n" + "="*60)
    print("Test 5: Full Dashboard Integration")
    print("="*60)

    runner = TestRunner()

    with tempfile.TemporaryDirectory() as temp_dir:
        base_dir = Path(temp_dir)
        chain_dir = base_dir / "context" / "session" / "chain_executions"
        chain_dir.mkdir(parents=True)

        # Create test data
        create_test_workflow_audit(chain_dir, "chain_1", "completed", 3, 0)
        create_test_workflow_audit(chain_dir, "chain_2", "failed", 2, 1)

        # Generate dashboard
        dashboard = MultiAgentDashboard(base_dir)
        markdown = dashboard.generate_dashboard(time_window_hours=24)

        runner.assert_true(len(markdown) > 0, "Dashboard generated")
        runner.assert_in("Multi-Agent System Dashboard", markdown, "Dashboard title present")
        runner.assert_in("System Overview", markdown, "Overview section present")
        runner.assert_in("Total Workflows", markdown, "Metrics present")

        # Test save to file
        output_file = Path(temp_dir) / "dashboard.md"
        dashboard.save_dashboard(output_file, time_window_hours=24)
        runner.assert_true(output_file.exists(), "Dashboard file saved")
        runner.assert_greater(len(output_file.read_text()), 0, "Saved file has content")

    runner.summary()
    return runner.passed == runner.total


def test_empty_data_handling():
    """Test 6: Handle empty data gracefully"""
    print("\n" + "="*60)
    print("Test 6: Empty Data Handling")
    print("="*60)

    runner = TestRunner()

    with tempfile.TemporaryDirectory() as temp_dir:
        base_dir = Path(temp_dir)
        # Don't create any data files

        dashboard = MultiAgentDashboard(base_dir)
        markdown = dashboard.generate_dashboard(time_window_hours=24)

        runner.assert_true(len(markdown) > 0, "Dashboard generated with no data")
        runner.assert_in("Multi-Agent System Dashboard", markdown, "Dashboard title present")
        runner.assert_in("0", markdown, "Zero metrics shown")

    runner.summary()
    return runner.passed == runner.total


def main():
    """Run all tests"""
    print("📊" * 30)
    print("MULTI-AGENT DASHBOARD - TEST SUITE")
    print("📊" * 30)

    tests = [
        test_data_collection,
        test_agent_aggregation,
        test_system_metrics,
        test_dashboard_rendering,
        test_dashboard_integration,
        test_empty_data_handling
    ]

    results = []
    for test_func in tests:
        result = test_func()
        results.append(result)

    # Final summary
    print("\n" + "📈" * 30)
    print("FINAL TEST SUMMARY")
    print("📈" * 30)

    for i, (test_func, result) in enumerate(zip(tests, results), 1):
        status = "✅ PASSED" if result else "❌ FAILED"
        test_name = test_func.__doc__.split(':')[0].replace(f'Test {i}', '').strip()
        print(f"{status}: {test_name}")

    print("\n" + "="*60)
    passed = sum(results)
    total = len(results)
    print(f"Overall: {passed}/{total} test suites passed")
    if passed == total:
        print("✅ ALL TESTS PASSED - Multi-Agent Dashboard ready for production!")
    else:
        print(f"❌ {total - passed} test suite(s) failed")
    print("="*60)

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
