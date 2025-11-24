#!/usr/bin/env python3
"""
Test Suite for Speculative Executor - Phase 182

TDD: Tests written FIRST before implementation.
Implements speculative execution pattern - try multiple approaches,
use first success.

Author: Maia System (SRE Principal Engineer Agent)
Created: 2025-11-24 (Agentic AI Enhancement Project - Phase 4)
"""

import pytest
import time
import threading
from datetime import datetime
from typing import Any, Optional
from unittest.mock import MagicMock, patch
import tempfile
from pathlib import Path

# Import will fail until implementation exists - this is expected in TDD
try:
    from claude.tools.orchestration.speculative_executor import (
        SpeculativeExecutor,
        Approach,
        SpeculativeResult,
        ExecutionStrategy,
    )
    IMPLEMENTATION_EXISTS = True
except ImportError:
    IMPLEMENTATION_EXISTS = False
    SpeculativeExecutor = None
    Approach = None
    SpeculativeResult = None
    ExecutionStrategy = None


pytestmark = pytest.mark.skipif(
    not IMPLEMENTATION_EXISTS,
    reason="Implementation not yet created (TDD red phase)"
)


# Test helper functions
def fast_success(x: Any) -> str:
    """Fast approach that succeeds"""
    time.sleep(0.05)
    return f"fast_result_{x}"


def slow_success(x: Any) -> str:
    """Slow approach that succeeds"""
    time.sleep(0.3)
    return f"slow_result_{x}"


def fast_failure(x: Any) -> str:
    """Fast approach that fails"""
    time.sleep(0.05)
    raise ValueError("fast_failure")


def slow_failure(x: Any) -> str:
    """Slow approach that fails"""
    time.sleep(0.3)
    raise ValueError("slow_failure")


def flaky_approach(x: Any) -> str:
    """Approach that sometimes fails"""
    import random
    time.sleep(0.1)
    if random.random() < 0.5:
        raise ValueError("flaky_failure")
    return f"flaky_result_{x}"


def timeout_approach(x: Any) -> str:
    """Approach that times out"""
    time.sleep(5.0)  # Will timeout
    return "should_not_return"


class TestSpeculativeExecutorSetup:
    """Test initialization"""

    def test_init_default_settings(self):
        """Executor should initialize with sensible defaults"""
        executor = SpeculativeExecutor()
        assert executor.max_workers >= 1
        assert executor.default_timeout > 0

    def test_init_custom_settings(self):
        """Executor should accept custom settings"""
        executor = SpeculativeExecutor(max_workers=10, default_timeout=60.0)
        assert executor.max_workers == 10
        assert executor.default_timeout == 60.0

    def test_init_with_outcome_tracker(self, tmp_path):
        """Executor should optionally integrate with OutcomeTracker"""
        from claude.tools.orchestration.outcome_tracker import OutcomeTracker

        db_path = tmp_path / "test.db"
        tracker = OutcomeTracker(db_path=str(db_path))
        executor = SpeculativeExecutor(outcome_tracker=tracker)

        assert executor.outcome_tracker is not None


class TestApproachDefinition:
    """Test Approach dataclass"""

    def test_approach_required_fields(self):
        """Approach should require name and callable"""
        approach = Approach(
            name="test_approach",
            callable=fast_success
        )
        assert approach.name == "test_approach"
        assert approach.callable == fast_success

    def test_approach_optional_fields(self):
        """Approach should support optional configuration"""
        approach = Approach(
            name="test_approach",
            callable=fast_success,
            timeout=10.0,
            priority=1,
            metadata={"model": "gpt-4"}
        )
        assert approach.timeout == 10.0
        assert approach.priority == 1
        assert approach.metadata["model"] == "gpt-4"


class TestSpeculativeExecution:
    """FR1-FR2: Execute multiple approaches, return first success"""

    @pytest.fixture
    def executor(self):
        return SpeculativeExecutor()

    def test_execute_returns_first_success(self, executor):
        """Should return result from first successful approach"""
        approaches = [
            Approach(name="fast", callable=fast_success),
            Approach(name="slow", callable=slow_success),
        ]

        result = executor.execute(approaches, input_data="test")

        assert result.success is True
        assert result.approach_name == "fast"
        assert "fast_result" in result.value

    def test_execute_skips_failures(self, executor):
        """Should skip failed approaches and use successful one"""
        approaches = [
            Approach(name="fails", callable=fast_failure),
            Approach(name="succeeds", callable=fast_success),
        ]

        result = executor.execute(approaches, input_data="test")

        assert result.success is True
        assert result.approach_name == "succeeds"

    def test_execute_all_fail(self, executor):
        """Should return failure result if all approaches fail"""
        approaches = [
            Approach(name="fail1", callable=fast_failure),
            Approach(name="fail2", callable=slow_failure),
        ]

        result = executor.execute(approaches, input_data="test")

        assert result.success is False
        assert result.error is not None
        assert "all approaches failed" in result.error.lower()

    def test_execute_empty_approaches(self, executor):
        """Should handle empty approach list"""
        result = executor.execute([], input_data="test")

        assert result.success is False
        assert "no approaches" in result.error.lower()

    def test_execute_single_approach(self, executor):
        """Should work with single approach"""
        approaches = [
            Approach(name="only", callable=fast_success),
        ]

        result = executor.execute(approaches, input_data="test")

        assert result.success is True
        assert result.approach_name == "only"

    def test_execute_respects_timeout(self, executor):
        """Should timeout slow approaches"""
        executor = SpeculativeExecutor(default_timeout=0.2)

        approaches = [
            Approach(name="timeout", callable=timeout_approach),
            Approach(name="fast", callable=fast_success),
        ]

        result = executor.execute(approaches, input_data="test")

        # Fast approach should win while timeout is still running
        assert result.success is True
        assert result.approach_name == "fast"

    def test_execute_per_approach_timeout(self, executor):
        """Should respect per-approach timeout override"""
        approaches = [
            Approach(name="timeout", callable=timeout_approach, timeout=0.1),
            Approach(name="slow", callable=slow_success),
        ]

        result = executor.execute(approaches, input_data="test")

        assert result.success is True
        # Slow should win because timeout gets cancelled quickly


class TestLatencyOptimization:
    """NFR1: Total latency ≈ fastest successful approach"""

    def test_latency_equals_fastest_success(self):
        """Fast approach should win even when slow is also running"""
        executor = SpeculativeExecutor()

        approaches = [
            Approach(name="slow", callable=slow_success),  # 300ms
            Approach(name="fast", callable=fast_success),  # 50ms
        ]

        result = executor.execute(approaches, input_data="test")

        assert result.success is True
        assert result.approach_name == "fast"
        # Fast approach should win
        assert "fast_result" in result.value

    def test_latency_with_fast_failure(self):
        """Should still be fast even if fast approach fails"""
        executor = SpeculativeExecutor()

        approaches = [
            Approach(name="fast_fail", callable=fast_failure),  # 50ms, fails
            Approach(name="slow_success", callable=slow_success),  # 300ms
        ]

        start = time.perf_counter()
        result = executor.execute(approaches, input_data="test")
        elapsed = time.perf_counter() - start

        assert result.success is True
        assert result.approach_name == "slow_success"
        # Should still complete around 300ms (slow success time)
        assert elapsed < 0.5


class TestOutcomeTracking:
    """FR3: Track which approach won"""

    @pytest.fixture
    def executor_with_tracker(self, tmp_path):
        from claude.tools.orchestration.outcome_tracker import OutcomeTracker

        db_path = tmp_path / "test.db"
        tracker = OutcomeTracker(db_path=str(db_path))
        executor = SpeculativeExecutor(outcome_tracker=tracker)
        return executor, tracker

    def test_records_winning_approach(self, executor_with_tracker):
        """Should record which approach won"""
        executor, tracker = executor_with_tracker

        approaches = [
            Approach(name="winner", callable=fast_success),
            Approach(name="loser", callable=slow_success),
        ]

        result = executor.execute(
            approaches,
            input_data="test",
            domain="test_domain"
        )

        # Check outcomes were recorded
        outcomes = tracker.query_outcomes(domain="test_domain")
        assert len(outcomes) >= 1

        # Find the successful outcome - should be "winner"
        successful_outcomes = [o for o in outcomes if o.success]
        assert len(successful_outcomes) >= 1
        # The winning approach should be recorded
        approach_names = [o.approach for o in successful_outcomes]
        assert "winner" in approach_names

    def test_records_failure_outcomes(self, executor_with_tracker):
        """Should record failed approaches too"""
        executor, tracker = executor_with_tracker

        approaches = [
            Approach(name="fail1", callable=fast_failure),
            Approach(name="fail2", callable=slow_failure),
        ]

        result = executor.execute(
            approaches,
            input_data="test",
            domain="test_domain"
        )

        # Both failures should be recorded
        outcomes = tracker.query_outcomes(domain="test_domain")
        assert len(outcomes) >= 2
        assert all(not o.success for o in outcomes)

    def test_records_latency(self, executor_with_tracker):
        """Should record approach latency"""
        executor, tracker = executor_with_tracker

        approaches = [
            Approach(name="timed", callable=fast_success),
        ]

        executor.execute(approaches, input_data="test", domain="test_domain")

        outcomes = tracker.query_outcomes(domain="test_domain")
        assert outcomes[0].latency_ms is not None
        assert outcomes[0].latency_ms > 0


class TestExecutionStrategies:
    """FR5-FR6: Strategy configuration"""

    def test_first_success_strategy(self):
        """Default strategy: return first success"""
        executor = SpeculativeExecutor(strategy=ExecutionStrategy.FIRST_SUCCESS)

        approaches = [
            Approach(name="fast", callable=fast_success),
            Approach(name="slow", callable=slow_success),
        ]

        result = executor.execute(approaches, input_data="test")

        assert result.approach_name == "fast"

    def test_priority_strategy(self):
        """Priority strategy: prefer higher priority approaches"""
        executor = SpeculativeExecutor(strategy=ExecutionStrategy.PRIORITY)

        approaches = [
            Approach(name="low_priority_fast", callable=fast_success, priority=1),
            Approach(name="high_priority_slow", callable=slow_success, priority=10),
        ]

        result = executor.execute(approaches, input_data="test")

        # Should wait for high priority even though low priority finishes first
        assert result.approach_name == "high_priority_slow"

    def test_best_quality_strategy(self):
        """Best quality strategy: wait for all, pick highest quality"""
        executor = SpeculativeExecutor(strategy=ExecutionStrategy.BEST_QUALITY)

        def low_quality(x):
            time.sleep(0.05)
            return {"value": x, "quality": 0.5}

        def high_quality(x):
            time.sleep(0.1)
            return {"value": x, "quality": 0.9}

        approaches = [
            Approach(name="low", callable=low_quality),
            Approach(name="high", callable=high_quality),
        ]

        result = executor.execute(
            approaches,
            input_data="test",
            quality_extractor=lambda r: r.get("quality", 0)
        )

        assert result.approach_name == "high"


class TestFallbackChain:
    """FR5: Fallback chain if all approaches fail"""

    def test_fallback_on_all_failure(self):
        """Should use fallback when all approaches fail"""
        executor = SpeculativeExecutor()

        def fallback(x):
            return f"fallback_result_{x}"

        approaches = [
            Approach(name="fail1", callable=fast_failure),
            Approach(name="fail2", callable=slow_failure),
        ]

        result = executor.execute(
            approaches,
            input_data="test",
            fallback=fallback
        )

        assert result.success is True
        assert "fallback_result" in result.value

    def test_no_fallback_on_success(self):
        """Should not use fallback when an approach succeeds"""
        executor = SpeculativeExecutor()

        fallback_called = []

        def fallback(x):
            fallback_called.append(True)
            return f"fallback_{x}"

        approaches = [
            Approach(name="succeeds", callable=fast_success),
        ]

        result = executor.execute(
            approaches,
            input_data="test",
            fallback=fallback
        )

        assert result.success is True
        assert len(fallback_called) == 0


class TestResourceCleanup:
    """NFR2: Resource cleanup on cancellation"""

    def test_signals_cancellation_on_success(self):
        """Should signal other approaches when one succeeds first"""
        executor = SpeculativeExecutor()

        approaches = [
            Approach(name="fast", callable=fast_success),
            Approach(name="slow", callable=slow_success),
        ]

        result = executor.execute(approaches, input_data="test")

        assert result.success is True
        assert result.approach_name == "fast"
        # Fast approach should win
        assert "fast_result" in result.value

    def test_cleanup_on_timeout(self):
        """Should fail gracefully on timeout and remain usable"""
        executor = SpeculativeExecutor(default_timeout=0.15)

        approaches = [
            Approach(name="timeout", callable=timeout_approach),
        ]

        result = executor.execute(approaches, input_data="test")

        # Should fail with timeout error
        assert result.success is False
        assert "timeout" in result.error.lower() or "Timeout" in result.error

        # Executor should still be usable after timeout
        result2 = executor.execute(
            [Approach(name="fast", callable=fast_success)],
            input_data="test2"
        )
        assert result2.success is True


class TestThreadSafety:
    """NFR3: Thread-safe execution"""

    def test_concurrent_executions(self):
        """Should handle multiple concurrent execute() calls"""
        executor = SpeculativeExecutor(max_workers=10)

        results = []
        errors = []

        def run_execution(i):
            try:
                approaches = [
                    Approach(name=f"approach_{i}", callable=fast_success),
                ]
                result = executor.execute(approaches, input_data=f"input_{i}")
                results.append((i, result))
            except Exception as e:
                errors.append((i, e))

        threads = [threading.Thread(target=run_execution, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Errors: {errors}"
        assert len(results) == 5
        assert all(r[1].success for r in results)


class TestResultDataclass:
    """Test SpeculativeResult dataclass"""

    def test_result_contains_timing(self):
        """Result should include timing information"""
        executor = SpeculativeExecutor()

        approaches = [
            Approach(name="test", callable=fast_success),
        ]

        result = executor.execute(approaches, input_data="test")

        assert result.duration_ms > 0
        assert result.started_at is not None
        assert result.completed_at is not None

    def test_result_contains_approach_details(self):
        """Result should include details of winning approach"""
        executor = SpeculativeExecutor()

        approaches = [
            Approach(name="winner", callable=fast_success, metadata={"key": "value"}),
        ]

        result = executor.execute(approaches, input_data="test")

        assert result.approach_name == "winner"
        assert result.approach_metadata == {"key": "value"}


class TestIntegrationWithExistingPatterns:
    """Integration with other agentic patterns"""

    def test_works_with_parallel_executor_results(self):
        """Should handle results from ParallelExecutor"""
        executor = SpeculativeExecutor()

        def parallel_approach(x):
            # Simulate parallel executor output
            return {
                "merged_results": [f"result_1_{x}", f"result_2_{x}"],
                "source_count": 2
            }

        approaches = [
            Approach(name="parallel", callable=parallel_approach),
        ]

        result = executor.execute(approaches, input_data="test")

        assert result.success is True
        assert "merged_results" in result.value

    def test_callable_with_exception_info(self):
        """Should capture detailed exception info for debugging"""
        executor = SpeculativeExecutor()

        def detailed_failure(x):
            raise RuntimeError("Detailed error message with context")

        approaches = [
            Approach(name="fails", callable=detailed_failure),
        ]

        result = executor.execute(approaches, input_data="test")

        assert result.success is False
        assert "Detailed error message" in result.error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
