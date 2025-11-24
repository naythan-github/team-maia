#!/usr/bin/env python3
"""
Speculative Executor - Agentic AI Enhancement Phase 4 (Phase 182)

Implements speculative execution pattern:
  CURRENT: Try A -> fail -> try B -> fail -> try C (sequential)
  AGENTIC: [Try A, B, C in parallel] -> use first success (fast)

Key Features:
- Execute multiple approaches concurrently for same task
- Return first successful result, cancel others
- Track which approach won via OutcomeTracker
- Configurable strategies (first success, priority, best quality)
- Fallback chain support

Author: Maia System (SRE Principal Engineer Agent)
Created: 2025-11-24 (Agentic AI Enhancement Project - Phase 4)
"""

import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, Future, as_completed, TimeoutError as FuturesTimeoutError
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class ExecutionStrategy(Enum):
    """Strategy for selecting winning approach"""
    FIRST_SUCCESS = "first_success"  # Return first successful result
    PRIORITY = "priority"  # Prefer higher priority approaches
    BEST_QUALITY = "best_quality"  # Wait for all, pick highest quality


@dataclass
class Approach:
    """Definition of an execution approach"""
    name: str
    callable: Callable[[Any], Any]
    timeout: Optional[float] = None
    priority: int = 0
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class SpeculativeResult:
    """Result from speculative execution"""
    success: bool
    value: Any = None
    error: Optional[str] = None
    approach_name: Optional[str] = None
    approach_metadata: Optional[Dict[str, Any]] = None
    duration_ms: float = 0.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    all_attempts: List[Dict[str, Any]] = field(default_factory=list)


class SpeculativeExecutor:
    """
    Speculative Executor for parallel approach execution.

    Runs multiple approaches concurrently and returns the first success,
    optionally tracking outcomes for learning.
    """

    def __init__(
        self,
        max_workers: int = 5,
        default_timeout: float = 30.0,
        strategy: ExecutionStrategy = ExecutionStrategy.FIRST_SUCCESS,
        outcome_tracker: Optional[Any] = None
    ):
        """
        Initialize Speculative Executor.

        Args:
            max_workers: Maximum concurrent workers
            default_timeout: Default timeout per approach in seconds
            strategy: Execution strategy for selecting winner
            outcome_tracker: Optional OutcomeTracker for recording outcomes
        """
        self.max_workers = max_workers
        self.default_timeout = default_timeout
        self.strategy = strategy
        self.outcome_tracker = outcome_tracker
        self._lock = threading.Lock()

    def execute(
        self,
        approaches: List[Approach],
        input_data: Any,
        domain: Optional[str] = None,
        fallback: Optional[Callable[[Any], Any]] = None,
        quality_extractor: Optional[Callable[[Any], float]] = None
    ) -> SpeculativeResult:
        """
        Execute approaches speculatively.

        Args:
            approaches: List of approaches to try
            input_data: Input data to pass to each approach
            domain: Optional domain for outcome tracking
            fallback: Optional fallback function if all approaches fail
            quality_extractor: Function to extract quality score from result

        Returns:
            SpeculativeResult with winning approach's result or failure info
        """
        started_at = datetime.now()
        start_time = time.perf_counter()

        # Handle empty approaches
        if not approaches:
            return SpeculativeResult(
                success=False,
                error="No approaches provided",
                started_at=started_at,
                completed_at=datetime.now(),
                duration_ms=0.0
            )

        # Execute based on strategy
        if self.strategy == ExecutionStrategy.FIRST_SUCCESS:
            result = self._execute_first_success(approaches, input_data, domain)
        elif self.strategy == ExecutionStrategy.PRIORITY:
            result = self._execute_priority(approaches, input_data, domain)
        elif self.strategy == ExecutionStrategy.BEST_QUALITY:
            result = self._execute_best_quality(approaches, input_data, domain, quality_extractor)
        else:
            result = self._execute_first_success(approaches, input_data, domain)

        # Try fallback if all failed
        if not result.success and fallback is not None:
            try:
                fallback_result = fallback(input_data)
                result = SpeculativeResult(
                    success=True,
                    value=fallback_result,
                    approach_name="fallback",
                    started_at=started_at,
                    completed_at=datetime.now(),
                    duration_ms=(time.perf_counter() - start_time) * 1000,
                    all_attempts=result.all_attempts
                )
            except Exception as e:
                logger.error(f"Fallback failed: {e}")

        # Update timing
        result.started_at = started_at
        result.completed_at = datetime.now()
        result.duration_ms = (time.perf_counter() - start_time) * 1000

        return result

    def _execute_first_success(
        self,
        approaches: List[Approach],
        input_data: Any,
        domain: Optional[str]
    ) -> SpeculativeResult:
        """Execute and return first successful result"""
        all_attempts = []
        winner_found = threading.Event()
        lock = threading.Lock()

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_approach: Dict[Future, Approach] = {}

            # Submit all approaches
            for approach in approaches:
                future = executor.submit(
                    self._run_approach,
                    approach,
                    input_data,
                    winner_found
                )
                future_to_approach[future] = approach

            # Process results as they complete
            winning_result = None
            try:
                for future in as_completed(future_to_approach, timeout=self.default_timeout):
                    approach = future_to_approach[future]

                    try:
                        attempt = future.result(timeout=0.1)

                        with lock:
                            all_attempts.append(attempt)

                            # Record outcome if tracker available
                            if self.outcome_tracker and domain:
                                self._record_outcome(attempt, domain)

                            # Check for success
                            if attempt["success"] and winning_result is None:
                                winning_result = SpeculativeResult(
                                    success=True,
                                    value=attempt["result"],
                                    approach_name=approach.name,
                                    approach_metadata=approach.metadata,
                                    duration_ms=attempt["duration_ms"]
                                )
                                winner_found.set()  # Signal other threads to stop
                                break  # Exit early on first success

                    except Exception as e:
                        attempt = {
                            "approach": approach.name,
                            "success": False,
                            "error": str(e),
                            "duration_ms": 0
                        }
                        with lock:
                            all_attempts.append(attempt)
                            if self.outcome_tracker and domain:
                                self._record_outcome(attempt, domain)

            except (TimeoutError, FuturesTimeoutError):
                # Overall timeout reached
                all_attempts.append({
                    "approach": "all",
                    "success": False,
                    "error": f"Timeout after {self.default_timeout}s",
                    "duration_ms": self.default_timeout * 1000
                })

        # Return winner or failure
        if winning_result is not None:
            winning_result.all_attempts = all_attempts
            return winning_result

        # All failed
        errors = [a.get("error", "Unknown error") for a in all_attempts if not a.get("success")]
        return SpeculativeResult(
            success=False,
            error=f"All approaches failed: {'; '.join(errors)}",
            all_attempts=all_attempts
        )

    def _execute_priority(
        self,
        approaches: List[Approach],
        input_data: Any,
        domain: Optional[str]
    ) -> SpeculativeResult:
        """Execute all and prefer highest priority success"""
        all_attempts = []
        results_by_priority: Dict[int, SpeculativeResult] = {}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_approach: Dict[Future, Approach] = {}

            for approach in approaches:
                future = executor.submit(
                    self._run_approach,
                    approach,
                    input_data,
                    None  # No early termination for priority strategy
                )
                future_to_approach[future] = approach

            for future in as_completed(future_to_approach):
                approach = future_to_approach[future]

                try:
                    attempt = future.result()
                    all_attempts.append(attempt)

                    if self.outcome_tracker and domain:
                        self._record_outcome(attempt, domain)

                    if attempt["success"]:
                        results_by_priority[approach.priority] = SpeculativeResult(
                            success=True,
                            value=attempt["result"],
                            approach_name=approach.name,
                            approach_metadata=approach.metadata,
                            duration_ms=attempt["duration_ms"]
                        )

                except Exception as e:
                    all_attempts.append({
                        "approach": approach.name,
                        "success": False,
                        "error": str(e),
                        "duration_ms": 0
                    })

        # Return highest priority success
        if results_by_priority:
            highest_priority = max(results_by_priority.keys())
            result = results_by_priority[highest_priority]
            result.all_attempts = all_attempts
            return result

        return SpeculativeResult(
            success=False,
            error="All approaches failed",
            all_attempts=all_attempts
        )

    def _execute_best_quality(
        self,
        approaches: List[Approach],
        input_data: Any,
        domain: Optional[str],
        quality_extractor: Optional[Callable[[Any], float]]
    ) -> SpeculativeResult:
        """Execute all and pick highest quality result"""
        all_attempts = []
        results_with_quality: List[tuple] = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_approach: Dict[Future, Approach] = {}

            for approach in approaches:
                future = executor.submit(
                    self._run_approach,
                    approach,
                    input_data,
                    None
                )
                future_to_approach[future] = approach

            for future in as_completed(future_to_approach):
                approach = future_to_approach[future]

                try:
                    attempt = future.result()
                    all_attempts.append(attempt)

                    if self.outcome_tracker and domain:
                        self._record_outcome(attempt, domain)

                    if attempt["success"]:
                        quality = 0.0
                        if quality_extractor:
                            try:
                                quality = quality_extractor(attempt["result"])
                            except Exception:
                                quality = 0.0

                        results_with_quality.append((
                            quality,
                            SpeculativeResult(
                                success=True,
                                value=attempt["result"],
                                approach_name=approach.name,
                                approach_metadata=approach.metadata,
                                duration_ms=attempt["duration_ms"]
                            )
                        ))

                except Exception as e:
                    all_attempts.append({
                        "approach": approach.name,
                        "success": False,
                        "error": str(e),
                        "duration_ms": 0
                    })

        # Return highest quality
        if results_with_quality:
            results_with_quality.sort(key=lambda x: x[0], reverse=True)
            result = results_with_quality[0][1]
            result.all_attempts = all_attempts
            return result

        return SpeculativeResult(
            success=False,
            error="All approaches failed",
            all_attempts=all_attempts
        )

    def _run_approach_with_timeout(
        self,
        approach: Approach,
        input_data: Any,
        stop_event: Optional[threading.Event]
    ) -> Dict[str, Any]:
        """Run a single approach with timeout handling using a nested executor"""
        start_time = time.perf_counter()
        timeout = approach.timeout or self.default_timeout

        # Check if we should stop early (another approach already won)
        if stop_event and stop_event.is_set():
            return {
                "approach": approach.name,
                "success": False,
                "error": "Cancelled - another approach succeeded",
                "duration_ms": 0
            }

        # Use a nested single-thread executor to enforce timeout
        with ThreadPoolExecutor(max_workers=1) as inner_executor:
            try:
                future = inner_executor.submit(approach.callable, input_data)

                # Wait with timeout, checking stop_event periodically
                result = None
                elapsed = 0
                check_interval = 0.05  # Check every 50ms

                while elapsed < timeout:
                    if stop_event and stop_event.is_set():
                        # Another approach won, abandon this one
                        future.cancel()
                        return {
                            "approach": approach.name,
                            "success": False,
                            "error": "Cancelled - another approach succeeded",
                            "duration_ms": (time.perf_counter() - start_time) * 1000
                        }

                    try:
                        result = future.result(timeout=check_interval)
                        # Got result
                        duration_ms = (time.perf_counter() - start_time) * 1000
                        return {
                            "approach": approach.name,
                            "success": True,
                            "result": result,
                            "duration_ms": duration_ms
                        }
                    except TimeoutError:
                        elapsed += check_interval
                        continue
                    except Exception as e:
                        duration_ms = (time.perf_counter() - start_time) * 1000
                        return {
                            "approach": approach.name,
                            "success": False,
                            "error": str(e),
                            "duration_ms": duration_ms
                        }

                # Timeout reached
                return {
                    "approach": approach.name,
                    "success": False,
                    "error": f"Timeout after {timeout}s",
                    "duration_ms": timeout * 1000
                }

            except Exception as e:
                duration_ms = (time.perf_counter() - start_time) * 1000
                logger.debug(f"Approach {approach.name} failed: {e}")
                return {
                    "approach": approach.name,
                    "success": False,
                    "error": str(e),
                    "duration_ms": duration_ms
                }

    def _run_approach(
        self,
        approach: Approach,
        input_data: Any,
        stop_event: Optional[threading.Event]
    ) -> Dict[str, Any]:
        """Run a single approach (simple version without timeout)"""
        start_time = time.perf_counter()

        try:
            if stop_event and stop_event.is_set():
                return {
                    "approach": approach.name,
                    "success": False,
                    "error": "Cancelled",
                    "duration_ms": 0
                }

            result = approach.callable(input_data)
            duration_ms = (time.perf_counter() - start_time) * 1000

            return {
                "approach": approach.name,
                "success": True,
                "result": result,
                "duration_ms": duration_ms
            }

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.debug(f"Approach {approach.name} failed: {e}")

            return {
                "approach": approach.name,
                "success": False,
                "error": str(e),
                "duration_ms": duration_ms
            }

    def _record_outcome(self, attempt: Dict[str, Any], domain: str) -> None:
        """Record outcome to tracker"""
        if not self.outcome_tracker:
            return

        try:
            from claude.tools.orchestration.outcome_tracker import Outcome

            outcome = Outcome(
                domain=domain,
                approach=attempt.get("approach", "unknown"),
                success=attempt.get("success", False),
                latency_ms=int(attempt.get("duration_ms", 0)),
                error_type=attempt.get("error") if not attempt.get("success") else None
            )
            self.outcome_tracker.record_outcome(outcome)

        except Exception as e:
            logger.warning(f"Failed to record outcome: {e}")


if __name__ == "__main__":
    import time

    # Demo
    def fast_approach(x):
        time.sleep(0.1)
        return f"fast_result_{x}"

    def slow_approach(x):
        time.sleep(0.5)
        return f"slow_result_{x}"

    def failing_approach(x):
        time.sleep(0.05)
        raise ValueError("This approach fails")

    executor = SpeculativeExecutor()

    approaches = [
        Approach(name="failing", callable=failing_approach),
        Approach(name="fast", callable=fast_approach),
        Approach(name="slow", callable=slow_approach),
    ]

    print("Running speculative execution...")
    result = executor.execute(approaches, input_data="test")

    print(f"Success: {result.success}")
    print(f"Winner: {result.approach_name}")
    print(f"Value: {result.value}")
    print(f"Duration: {result.duration_ms:.2f}ms")
    print(f"Attempts: {len(result.all_attempts)}")
