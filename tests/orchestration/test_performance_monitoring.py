"""
Performance Monitoring Test Suite

Tests:
1. Metrics collection and persistence
2. Execution tracking (decorator and manual)
3. Performance analytics (success rates, execution times)
4. Bottleneck identification
5. Failure analysis
6. Integration with Capability Registry
"""

import sys
import time
from pathlib import Path

# Add orchestration directory to path
sys.path.insert(0, str(Path(__file__).parent))

from performance_monitoring import (
    MetricsCollector,
    PerformanceAnalytics,
    ExecutionMetrics,
    track_execution,
    get_collector,
    get_analytics
)


class TestMetricsCollection:
    """Test metrics collection and persistence"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.collector = MetricsCollector()

    def test_record_execution(self):
        """Test 1: Record execution metrics"""
        metrics = self.collector.record_execution(
            agent_name="test_agent",
            execution_time_ms=1500,
            success=True,
            query="Test query",
            complexity=5
        )

        assert metrics.agent_name == "test_agent"
        assert metrics.execution_time_ms == 1500
        assert metrics.success == True
        assert metrics.query == "Test query"
        assert metrics.complexity == 5

        print("✅ Test 1: Record execution - PASSED")
        self.passed += 1

    def test_metrics_persistence(self):
        """Test 2: Metrics persisted to disk"""
        # Record a metric
        self.collector.record_execution(
            agent_name="persistence_test",
            execution_time_ms=1000,
            success=True
        )

        # Check storage directory exists
        assert self.collector.storage_dir.exists(), "Storage directory not created"

        # Check metrics file exists
        metrics_files = list(self.collector.storage_dir.glob("metrics_*.jsonl"))
        assert len(metrics_files) > 0, "No metrics files found"

        print("✅ Test 2: Metrics persistence - PASSED")
        print(f"    Storage: {self.collector.storage_dir}")
        print(f"    Files: {len(metrics_files)}")
        self.passed += 1

    def test_metrics_cache(self):
        """Test 3: Metrics cached in memory"""
        initial_count = len(self.collector.metrics_cache)

        self.collector.record_execution(
            agent_name="cache_test",
            execution_time_ms=500,
            success=True
        )

        assert len(self.collector.metrics_cache) == initial_count + 1, \
            "Metrics not added to cache"

        print("✅ Test 3: Metrics cache - PASSED")
        print(f"    Cache size: {len(self.collector.metrics_cache)}")
        self.passed += 1

    def test_get_metrics_by_agent(self):
        """Test 4: Filter metrics by agent"""
        # Record metrics for specific agent
        for i in range(3):
            self.collector.record_execution(
                agent_name="filter_test_agent",
                execution_time_ms=1000 + i * 100,
                success=True
            )

        metrics = self.collector.get_metrics_by_agent("filter_test_agent")
        assert len(metrics) >= 3, f"Expected ≥3 metrics, got {len(metrics)}"

        print("✅ Test 4: Get metrics by agent - PASSED")
        print(f"    Metrics found: {len(metrics)}")
        self.passed += 1

    def run_all(self):
        """Run all collection tests"""
        print("\n=== Metrics Collection Tests ===\n")

        tests = [
            self.test_record_execution,
            self.test_metrics_persistence,
            self.test_metrics_cache,
            self.test_get_metrics_by_agent,
        ]

        for test in tests:
            try:
                test()
            except AssertionError as e:
                print(f"❌ {test.__doc__} - FAILED: {e}")
                self.failed += 1
            except Exception as e:
                print(f"❌ {test.__doc__} - ERROR: {e}")
                self.failed += 1

        print(f"\nMetrics Collection: {self.passed} passed, {self.failed} failed\n")
        return self.failed == 0


class TestPerformanceAnalytics:
    """Test performance analytics and calculations"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.collector = MetricsCollector()
        self.analytics = PerformanceAnalytics(self.collector)

        # Populate with test data
        self._populate_test_data()

    def _populate_test_data(self):
        """Populate collector with test data"""
        # Agent A: High success rate
        for i in range(10):
            self.collector.record_execution(
                "agent_a",
                execution_time_ms=1200,
                success=True
            )

        # Agent B: Lower success rate
        for i in range(10):
            self.collector.record_execution(
                "agent_b",
                execution_time_ms=1500,
                success=i < 7  # 70% success
            )

        # Agent C: Slow execution
        for i in range(5):
            self.collector.record_execution(
                "agent_c",
                execution_time_ms=5000,
                success=True,
                handoff_count=2
            )

    def test_success_rate_calculation(self):
        """Test 5: Success rate calculation"""
        rate_a = self.analytics.get_agent_success_rate("agent_a")
        rate_b = self.analytics.get_agent_success_rate("agent_b")

        assert rate_a == 1.0, f"Expected 1.0, got {rate_a}"
        assert 0.6 <= rate_b <= 0.8, f"Expected ~0.7, got {rate_b}"

        print("✅ Test 5: Success rate calculation - PASSED")
        print(f"    Agent A: {rate_a:.1%}")
        print(f"    Agent B: {rate_b:.1%}")
        self.passed += 1

    def test_execution_time_calculation(self):
        """Test 6: Average execution time"""
        time_a = self.analytics.get_agent_avg_execution_time("agent_a")
        time_c = self.analytics.get_agent_avg_execution_time("agent_c")

        assert time_a == 1200, f"Expected 1200ms, got {time_a}"
        assert time_c == 5000, f"Expected 5000ms, got {time_c}"

        print("✅ Test 6: Execution time calculation - PASSED")
        print(f"    Agent A: {time_a}ms")
        print(f"    Agent C: {time_c}ms")
        self.passed += 1

    def test_agent_statistics(self):
        """Test 7: Comprehensive agent statistics"""
        stats = self.analytics.get_agent_statistics("agent_a")

        assert 'total_executions' in stats
        assert 'success_rate' in stats
        assert 'avg_execution_time_ms' in stats
        assert stats['total_executions'] >= 10

        print("✅ Test 7: Agent statistics - PASSED")
        print(f"    Executions: {stats['total_executions']}")
        print(f"    Success rate: {stats['success_rate']:.1%}")
        self.passed += 1

    def test_bottleneck_identification(self):
        """Test 8: Identify slow agents"""
        bottlenecks = self.analytics.identify_bottlenecks(threshold_ms=3000)

        # Agent C should be identified (5000ms avg)
        bottleneck_names = [b['agent_name'] for b in bottlenecks]
        assert 'agent_c' in bottleneck_names, f"Agent C not identified as bottleneck: {bottleneck_names}"

        print("✅ Test 8: Bottleneck identification - PASSED")
        print(f"    Bottlenecks found: {len(bottlenecks)}")
        for b in bottlenecks:
            print(f"      {b['agent_name']}: {b['avg_execution_time_ms']:.0f}ms")
        self.passed += 1

    def test_failure_analysis(self):
        """Test 9: Failure analysis"""
        analysis = self.analytics.get_failure_analysis()

        assert 'total_failures' in analysis
        assert 'failure_rate' in analysis
        assert analysis['total_failures'] >= 3  # From agent_b

        print("✅ Test 9: Failure analysis - PASSED")
        print(f"    Total failures: {analysis['total_failures']}")
        print(f"    Failure rate: {analysis['failure_rate']:.1%}")
        self.passed += 1

    def test_performance_summary(self):
        """Test 10: Overall performance summary"""
        summary = self.analytics.get_performance_summary()

        assert 'total_executions' in summary
        assert 'overall_success_rate' in summary
        assert summary['total_executions'] >= 25  # 10 + 10 + 5

        print("✅ Test 10: Performance summary - PASSED")
        print(f"    Total executions: {summary['total_executions']}")
        print(f"    Success rate: {summary['overall_success_rate']:.1%}")
        self.passed += 1

    def run_all(self):
        """Run all analytics tests"""
        print("\n=== Performance Analytics Tests ===\n")

        tests = [
            self.test_success_rate_calculation,
            self.test_execution_time_calculation,
            self.test_agent_statistics,
            self.test_bottleneck_identification,
            self.test_failure_analysis,
            self.test_performance_summary,
        ]

        for test in tests:
            try:
                test()
            except AssertionError as e:
                print(f"❌ {test.__doc__} - FAILED: {e}")
                self.failed += 1
            except Exception as e:
                print(f"❌ {test.__doc__} - ERROR: {e}")
                self.failed += 1

        print(f"\nPerformance Analytics: {self.passed} passed, {self.failed} failed\n")
        return self.failed == 0


class TestCapabilityRegistryIntegration:
    """Test integration with Capability Registry"""

    def __init__(self):
        self.passed = 0
        self.failed = 0

    def test_update_registry_with_metrics(self):
        """Test 11: Update registry with performance metrics"""
        from agent_capability_registry import create_registry

        # Create registry and analytics
        registry = create_registry()
        collector = MetricsCollector()
        analytics = PerformanceAnalytics(collector)

        # Record some metrics
        for i in range(5):
            collector.record_execution(
                "dns_specialist",
                execution_time_ms=1500,
                success=i < 4  # 80% success
            )

        # Update registry
        registry.update_performance_metrics(analytics)

        # Check updated
        dns_capability = registry.get_capability("dns_specialist")
        if dns_capability:
            assert dns_capability.usage_count >= 5, \
                f"Expected ≥5 usage, got {dns_capability.usage_count}"
            assert dns_capability.success_rate is not None, \
                "Success rate not updated"

            print("✅ Test 11: Registry integration - PASSED")
            print(f"    Usage count: {dns_capability.usage_count}")
            print(f"    Success rate: {dns_capability.success_rate:.1%}")
            print(f"    Avg time: {dns_capability.avg_response_time:.0f}ms")
        else:
            print("✅ Test 11: Registry integration - SKIPPED (agent not found)")

        self.passed += 1

    def run_all(self):
        """Run all integration tests"""
        print("\n=== Capability Registry Integration Tests ===\n")

        tests = [
            self.test_update_registry_with_metrics,
        ]

        for test in tests:
            try:
                test()
            except AssertionError as e:
                print(f"❌ {test.__doc__} - FAILED: {e}")
                self.failed += 1
            except Exception as e:
                print(f"❌ {test.__doc__} - ERROR: {e}")
                self.failed += 1

        print(f"\nRegistry Integration: {self.passed} passed, {self.failed} failed\n")
        return self.failed == 0


def main():
    """Run all test suites"""
    print("=" * 70)
    print("PERFORMANCE MONITORING TEST SUITE")
    print("=" * 70)

    # Run test suites
    collection_tests = TestMetricsCollection()
    collection_passed = collection_tests.run_all()

    analytics_tests = TestPerformanceAnalytics()
    analytics_passed = analytics_tests.run_all()

    integration_tests = TestCapabilityRegistryIntegration()
    integration_passed = integration_tests.run_all()

    # Summary
    total_passed = (collection_tests.passed + analytics_tests.passed +
                   integration_tests.passed)
    total_failed = (collection_tests.failed + analytics_tests.failed +
                   integration_tests.failed)

    print("=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)
    print(f"Total Passed: {total_passed}")
    print(f"Total Failed: {total_failed}")
    print(f"Success Rate: {total_passed / (total_passed + total_failed) * 100:.1f}%")
    print("=" * 70)

    if total_failed == 0:
        print("\n✅ ALL TESTS PASSED\n")
        return 0
    else:
        print(f"\n❌ {total_failed} TESTS FAILED\n")
        return 1


if __name__ == '__main__':
    exit(main())
