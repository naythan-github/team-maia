"""
Performance Monitoring System

Tracks agent execution metrics, identifies bottlenecks, and enables
continuous improvement through data-driven insights.

Components:
1. ExecutionMetrics: Individual execution data points
2. MetricsCollector: Captures and persists metrics
3. PerformanceAnalytics: Aggregates and analyzes metrics
4. Integration hooks for Coordinator, Swarm, Registry

Usage:
    from performance_monitoring import track_execution, get_analytics

    # Automatic tracking via decorator
    @track_execution("dns_specialist")
    def execute_agent(query):
        # ... agent execution
        return result

    # Get performance analytics
    analytics = get_analytics()
    print(f"DNS Specialist success rate: {analytics.get_agent_success_rate('dns_specialist')}")
"""

import time
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from collections import defaultdict
from functools import wraps
import statistics


@dataclass
class ExecutionMetrics:
    """
    Metrics for a single agent execution.

    Captures:
    - Performance: execution time, token usage
    - Outcome: success/failure, error info
    - Context: query, complexity, handoffs
    """
    agent_name: str
    execution_id: str
    timestamp: datetime
    execution_time_ms: float
    success: bool

    # Context
    query: Optional[str] = None
    complexity: Optional[int] = None
    strategy: Optional[str] = None  # single_agent, swarm, chain

    # Performance
    tokens_used: Optional[int] = None
    context_size: Optional[int] = None
    handoff_count: int = 0

    # Outcome
    error_type: Optional[str] = None
    error_message: Optional[str] = None

    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExecutionMetrics':
        """Create from dictionary"""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


class MetricsCollector:
    """
    Collects and persists execution metrics.

    Features:
    - Automatic tracking via decorators
    - Manual tracking API
    - Persistent storage to disk
    - In-memory cache for fast access
    """

    def __init__(self, storage_dir: Path = None):
        """
        Initialize metrics collector.

        Args:
            storage_dir: Directory for metrics storage
        """
        if storage_dir is None:
            storage_dir = Path(__file__).parent.parent.parent / "context" / "session" / "metrics"

        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # In-memory cache
        self.metrics_cache: List[ExecutionMetrics] = []
        self.max_cache_size = 1000

        # Load recent metrics from disk
        self._load_recent_metrics()

    def record_execution(
        self,
        agent_name: str,
        execution_time_ms: float,
        success: bool,
        **kwargs
    ) -> ExecutionMetrics:
        """
        Record a single execution.

        Args:
            agent_name: Name of agent executed
            execution_time_ms: Execution time in milliseconds
            success: Whether execution succeeded
            **kwargs: Additional metadata

        Returns:
            ExecutionMetrics instance
        """
        execution_id = f"{agent_name}_{int(time.time() * 1000)}"

        metrics = ExecutionMetrics(
            agent_name=agent_name,
            execution_id=execution_id,
            timestamp=datetime.now(),
            execution_time_ms=execution_time_ms,
            success=success,
            **kwargs
        )

        # Add to cache
        self.metrics_cache.append(metrics)

        # Persist to disk
        self._persist_metrics(metrics)

        # Trim cache if needed
        if len(self.metrics_cache) > self.max_cache_size:
            self.metrics_cache = self.metrics_cache[-self.max_cache_size:]

        return metrics

    def track_execution(self, agent_name: str):
        """
        Decorator to automatically track execution metrics.

        Usage:
            @collector.track_execution("dns_specialist")
            def execute_agent(query):
                # ... execution logic
                return result
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                success = False
                error_info = {}

                try:
                    result = func(*args, **kwargs)
                    success = True
                    return result
                except Exception as e:
                    error_info = {
                        'error_type': type(e).__name__,
                        'error_message': str(e)
                    }
                    raise
                finally:
                    execution_time = (time.time() - start_time) * 1000

                    # Extract query from args if available
                    query = kwargs.get('query') or (args[0] if args else None)
                    if isinstance(query, str):
                        pass
                    else:
                        query = None

                    self.record_execution(
                        agent_name=agent_name,
                        execution_time_ms=execution_time,
                        success=success,
                        query=query,
                        **error_info
                    )

            return wrapper
        return decorator

    def get_recent_metrics(self, limit: int = 100) -> List[ExecutionMetrics]:
        """Get most recent metrics from cache"""
        return self.metrics_cache[-limit:]

    def get_metrics_by_agent(self, agent_name: str) -> List[ExecutionMetrics]:
        """Get all metrics for specific agent"""
        return [m for m in self.metrics_cache if m.agent_name == agent_name]

    def _persist_metrics(self, metrics: ExecutionMetrics):
        """Persist metrics to disk"""
        # Store by date for easy cleanup
        date_str = metrics.timestamp.strftime("%Y-%m-%d")
        metrics_file = self.storage_dir / f"metrics_{date_str}.jsonl"

        with metrics_file.open('a') as f:
            f.write(json.dumps(metrics.to_dict()) + '\n')

    def _load_recent_metrics(self, days: int = 7):
        """Load recent metrics from disk"""
        cutoff = datetime.now() - timedelta(days=days)

        # Load all metrics files from past N days
        for metrics_file in self.storage_dir.glob("metrics_*.jsonl"):
            try:
                with metrics_file.open('r') as f:
                    for line in f:
                        if line.strip():
                            metrics = ExecutionMetrics.from_dict(json.loads(line))
                            if metrics.timestamp >= cutoff:
                                self.metrics_cache.append(metrics)
            except Exception as e:
                print(f"⚠️  Failed to load metrics from {metrics_file}: {e}")

        # Sort by timestamp
        self.metrics_cache.sort(key=lambda m: m.timestamp)

        # Trim to max size
        if len(self.metrics_cache) > self.max_cache_size:
            self.metrics_cache = self.metrics_cache[-self.max_cache_size:]


class PerformanceAnalytics:
    """
    Aggregates and analyzes performance metrics.

    Provides:
    - Success rates by agent
    - Average execution times
    - Token usage patterns
    - Bottleneck identification
    - Trend analysis
    """

    def __init__(self, collector: MetricsCollector):
        """
        Initialize analytics engine.

        Args:
            collector: MetricsCollector instance
        """
        self.collector = collector

    def get_agent_success_rate(self, agent_name: str) -> float:
        """
        Calculate success rate for agent.

        Returns:
            Success rate between 0.0 and 1.0
        """
        metrics = self.collector.get_metrics_by_agent(agent_name)

        if not metrics:
            return 0.0

        successful = sum(1 for m in metrics if m.success)
        return successful / len(metrics)

    def get_agent_avg_execution_time(self, agent_name: str) -> float:
        """
        Calculate average execution time for agent in milliseconds.

        Returns:
            Average execution time in ms
        """
        metrics = self.collector.get_metrics_by_agent(agent_name)

        if not metrics:
            return 0.0

        times = [m.execution_time_ms for m in metrics]
        return statistics.mean(times)

    def get_agent_statistics(self, agent_name: str) -> Dict[str, Any]:
        """
        Get comprehensive statistics for agent.

        Returns:
            Dictionary with success rate, execution times, usage count, etc.
        """
        metrics = self.collector.get_metrics_by_agent(agent_name)

        if not metrics:
            return {
                'agent_name': agent_name,
                'total_executions': 0,
                'success_rate': 0.0,
                'avg_execution_time_ms': 0.0,
            }

        times = [m.execution_time_ms for m in metrics]
        successful = sum(1 for m in metrics if m.success)

        return {
            'agent_name': agent_name,
            'total_executions': len(metrics),
            'success_rate': successful / len(metrics),
            'avg_execution_time_ms': statistics.mean(times),
            'median_execution_time_ms': statistics.median(times),
            'min_execution_time_ms': min(times),
            'max_execution_time_ms': max(times),
            'total_handoffs': sum(m.handoff_count for m in metrics),
            'last_execution': metrics[-1].timestamp.isoformat(),
        }

    def get_all_agent_statistics(self) -> List[Dict[str, Any]]:
        """Get statistics for all agents with executions"""
        agent_names = set(m.agent_name for m in self.collector.metrics_cache)
        return [self.get_agent_statistics(name) for name in sorted(agent_names)]

    def identify_bottlenecks(self, threshold_ms: float = 5000) -> List[Dict[str, Any]]:
        """
        Identify agents with slow execution times.

        Args:
            threshold_ms: Execution time threshold in milliseconds

        Returns:
            List of agents with avg execution time > threshold
        """
        bottlenecks = []

        agent_names = set(m.agent_name for m in self.collector.metrics_cache)
        for agent_name in agent_names:
            avg_time = self.get_agent_avg_execution_time(agent_name)
            if avg_time > threshold_ms:
                bottlenecks.append({
                    'agent_name': agent_name,
                    'avg_execution_time_ms': avg_time,
                    'threshold_ms': threshold_ms,
                })

        # Sort by execution time descending
        return sorted(bottlenecks, key=lambda x: x['avg_execution_time_ms'], reverse=True)

    def get_failure_analysis(self) -> Dict[str, Any]:
        """Analyze failures across all agents"""
        all_metrics = self.collector.metrics_cache
        failures = [m for m in all_metrics if not m.success]

        if not failures:
            return {
                'total_failures': 0,
                'failure_rate': 0.0,
                'failures_by_agent': {},
                'common_errors': [],
            }

        # Failures by agent
        failures_by_agent = defaultdict(int)
        for failure in failures:
            failures_by_agent[failure.agent_name] += 1

        # Common error types
        error_counts = defaultdict(int)
        for failure in failures:
            if failure.error_type:
                error_counts[failure.error_type] += 1

        common_errors = sorted(
            [{'error_type': k, 'count': v} for k, v in error_counts.items()],
            key=lambda x: x['count'],
            reverse=True
        )

        return {
            'total_failures': len(failures),
            'failure_rate': len(failures) / len(all_metrics),
            'failures_by_agent': dict(failures_by_agent),
            'common_errors': common_errors[:5],  # Top 5
        }

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get overall performance summary"""
        all_metrics = self.collector.metrics_cache

        if not all_metrics:
            return {
                'total_executions': 0,
                'unique_agents': 0,
                'overall_success_rate': 0.0,
                'avg_execution_time_ms': 0.0,
            }

        times = [m.execution_time_ms for m in all_metrics]
        successful = sum(1 for m in all_metrics if m.success)

        return {
            'total_executions': len(all_metrics),
            'unique_agents': len(set(m.agent_name for m in all_metrics)),
            'overall_success_rate': successful / len(all_metrics),
            'avg_execution_time_ms': statistics.mean(times),
            'median_execution_time_ms': statistics.median(times),
            'total_handoffs': sum(m.handoff_count for m in all_metrics),
            'date_range': {
                'start': all_metrics[0].timestamp.isoformat(),
                'end': all_metrics[-1].timestamp.isoformat(),
            }
        }


# Global singleton instances
_collector: Optional[MetricsCollector] = None
_analytics: Optional[PerformanceAnalytics] = None


def get_collector() -> MetricsCollector:
    """Get global metrics collector instance"""
    global _collector
    if _collector is None:
        _collector = MetricsCollector()
    return _collector


def get_analytics() -> PerformanceAnalytics:
    """Get global analytics engine instance"""
    global _analytics
    if _analytics is None:
        _analytics = PerformanceAnalytics(get_collector())
    return _analytics


def track_execution(agent_name: str):
    """
    Convenience decorator for tracking execution.

    Usage:
        @track_execution("dns_specialist")
        def execute_agent(query):
            return result
    """
    return get_collector().track_execution(agent_name)


def record_execution(agent_name: str, execution_time_ms: float, success: bool, **kwargs):
    """
    Convenience function for recording execution.

    Usage:
        record_execution("dns_specialist", 1500, True, query="Setup SPF")
    """
    return get_collector().record_execution(agent_name, execution_time_ms, success, **kwargs)


if __name__ == '__main__':
    print("=" * 70)
    print("PERFORMANCE MONITORING SYSTEM - DEMO")
    print("=" * 70)

    # Initialize
    collector = get_collector()
    analytics = get_analytics()

    # Simulate some executions
    print("\n📊 Simulating agent executions...")

    # DNS Specialist - mostly successful
    for i in range(10):
        collector.record_execution(
            "dns_specialist",
            execution_time_ms=1200 + i * 100,
            success=i < 9,  # 90% success rate
            query=f"DNS query {i}",
            complexity=3
        )

    # Azure Architect - slower but successful
    for i in range(8):
        collector.record_execution(
            "azure_solutions_architect",
            execution_time_ms=2500 + i * 200,
            success=True,
            query=f"Azure query {i}",
            complexity=7,
            handoff_count=2
        )

    # Service Desk - fast but some failures
    for i in range(15):
        collector.record_execution(
            "service_desk_manager",
            execution_time_ms=800 + i * 50,
            success=i % 4 != 0,  # 75% success rate
            query=f"Support query {i}",
            complexity=2
        )

    # Analytics
    print("\n📊 Performance Summary:")
    summary = analytics.get_performance_summary()
    print(f"  Total executions: {summary['total_executions']}")
    print(f"  Unique agents: {summary['unique_agents']}")
    print(f"  Overall success rate: {summary['overall_success_rate']:.1%}")
    print(f"  Avg execution time: {summary['avg_execution_time_ms']:.0f}ms")

    print("\n📊 Agent Statistics:")
    for stats in analytics.get_all_agent_statistics():
        print(f"\n  {stats['agent_name']}:")
        print(f"    Executions: {stats['total_executions']}")
        print(f"    Success rate: {stats['success_rate']:.1%}")
        print(f"    Avg time: {stats['avg_execution_time_ms']:.0f}ms")
        print(f"    Handoffs: {stats['total_handoffs']}")

    print("\n⚠️  Bottlenecks (>2000ms):")
    bottlenecks = analytics.identify_bottlenecks(threshold_ms=2000)
    if bottlenecks:
        for bottleneck in bottlenecks:
            print(f"  {bottleneck['agent_name']}: {bottleneck['avg_execution_time_ms']:.0f}ms")
    else:
        print("  None detected")

    print("\n❌ Failure Analysis:")
    failures = analytics.get_failure_analysis()
    print(f"  Total failures: {failures['total_failures']}")
    print(f"  Failure rate: {failures['failure_rate']:.1%}")
    if failures['failures_by_agent']:
        print("  Failures by agent:")
        for agent, count in failures['failures_by_agent'].items():
            print(f"    {agent}: {count}")

    print("\n" + "=" * 70)
    print("Performance monitoring ready for production!")
    print("=" * 70)
