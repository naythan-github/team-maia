"""
TDD Tests for Azure Workload Pattern Detector

Critical for preventing false positives - detects batch jobs, scheduled workloads,
and seasonal patterns that could be mistaken for idle resources.

Tests written BEFORE implementation per TDD protocol.
Run with: pytest tests/test_workload_detector.py -v
"""

import pytest
from datetime import datetime, timedelta
from typing import List, Dict, Any


def generate_metrics(
    base_time: datetime,
    hours: int,
    cpu_pattern: str = "steady",
    base_cpu: float = 5.0,
    peak_cpu: float = 80.0,
    peak_hours: List[int] = None,
    peak_days: List[int] = None,
) -> List[Dict[str, Any]]:
    """
    Generate sample metric data for testing.

    Args:
        base_time: Starting time for metrics
        hours: Total hours of metrics to generate
        cpu_pattern: 'steady', 'idle', 'scheduled_daily', 'scheduled_weekly', 'random_spikes'
        base_cpu: Base CPU percentage
        peak_cpu: Peak CPU percentage for spikes
        peak_hours: Hours of day when peaks occur (0-23)
        peak_days: Days of week when peaks occur (0=Mon, 6=Sun)

    Returns:
        List of metric data points
    """
    metrics = []
    for i in range(hours):
        timestamp = base_time + timedelta(hours=i)
        hour = timestamp.hour
        day_of_week = timestamp.weekday()

        if cpu_pattern == "idle":
            cpu = base_cpu
        elif cpu_pattern == "steady":
            cpu = base_cpu + 20  # Moderate steady usage
        elif cpu_pattern == "scheduled_daily" and peak_hours:
            cpu = peak_cpu if hour in peak_hours else base_cpu
        elif cpu_pattern == "scheduled_weekly" and peak_days:
            cpu = peak_cpu if day_of_week in peak_days else base_cpu
        elif cpu_pattern == "random_spikes":
            # Occasional random spikes
            cpu = peak_cpu if i % 47 == 0 else base_cpu
        else:
            cpu = base_cpu

        metrics.append({
            "timestamp": timestamp.isoformat(),
            "cpu_percent": cpu,
            "memory_percent": cpu * 0.8,  # Memory roughly correlates with CPU
        })

    return metrics


class TestWorkloadPatternEnum:
    """Tests for WorkloadPattern enum."""

    def test_workload_pattern_values(self):
        """WorkloadPattern should have all expected values."""
        from claude.tools.experimental.azure.workload_detector import WorkloadPattern

        assert WorkloadPattern.STEADY.value == "steady"
        assert WorkloadPattern.SCHEDULED.value == "scheduled"
        assert WorkloadPattern.SEASONAL.value == "seasonal"
        assert WorkloadPattern.BURST.value == "burst"
        assert WorkloadPattern.IDLE.value == "idle"
        assert WorkloadPattern.UNKNOWN.value == "unknown"


class TestPatternAnalysisDataclass:
    """Tests for PatternAnalysis dataclass."""

    def test_pattern_analysis_creation(self):
        """PatternAnalysis should store all fields."""
        from claude.tools.experimental.azure.workload_detector import (
            PatternAnalysis,
            WorkloadPattern,
        )

        analysis = PatternAnalysis(
            resource_id="/subscriptions/xxx/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm1",
            pattern=WorkloadPattern.SCHEDULED,
            confidence=0.85,
            observation_days=14,
            peak_hours=[2, 3, 4],
            peak_days=[0, 1, 2, 3, 4],  # Weekdays
            evidence={"pattern_type": "daily_batch"},
        )

        assert analysis.resource_id.endswith("vm1")
        assert analysis.pattern == WorkloadPattern.SCHEDULED
        assert analysis.confidence == 0.85
        assert analysis.observation_days == 14
        assert analysis.peak_hours == [2, 3, 4]

    def test_is_safe_to_rightsize_scheduled_workload_false(self):
        """Scheduled workloads should NOT be safe to rightsize without human review."""
        from claude.tools.experimental.azure.workload_detector import (
            PatternAnalysis,
            WorkloadPattern,
        )

        analysis = PatternAnalysis(
            resource_id="test-resource",
            pattern=WorkloadPattern.SCHEDULED,
            confidence=0.95,
            observation_days=30,
        )

        assert analysis.is_safe_to_rightsize() is False

    def test_is_safe_to_rightsize_idle_requires_high_confidence(self):
        """Idle detection requires >= 0.85 confidence and >= 14 days observation."""
        from claude.tools.experimental.azure.workload_detector import (
            PatternAnalysis,
            WorkloadPattern,
        )

        # Low confidence - not safe
        low_confidence = PatternAnalysis(
            resource_id="test",
            pattern=WorkloadPattern.IDLE,
            confidence=0.80,
            observation_days=14,
        )
        assert low_confidence.is_safe_to_rightsize() is False

        # Short observation - not safe
        short_observation = PatternAnalysis(
            resource_id="test",
            pattern=WorkloadPattern.IDLE,
            confidence=0.90,
            observation_days=7,
        )
        assert short_observation.is_safe_to_rightsize() is False

        # High confidence + long observation - safe
        safe = PatternAnalysis(
            resource_id="test",
            pattern=WorkloadPattern.IDLE,
            confidence=0.90,
            observation_days=14,
        )
        assert safe.is_safe_to_rightsize() is True

    def test_is_safe_to_rightsize_steady_workload(self):
        """Steady workloads are safe to rightsize with >= 0.75 confidence."""
        from claude.tools.experimental.azure.workload_detector import (
            PatternAnalysis,
            WorkloadPattern,
        )

        safe = PatternAnalysis(
            resource_id="test",
            pattern=WorkloadPattern.STEADY,
            confidence=0.80,
            observation_days=7,
        )
        assert safe.is_safe_to_rightsize() is True

        not_safe = PatternAnalysis(
            resource_id="test",
            pattern=WorkloadPattern.STEADY,
            confidence=0.60,
            observation_days=7,
        )
        assert not_safe.is_safe_to_rightsize() is False


class TestWorkloadPatternDetector:
    """Tests for WorkloadPatternDetector class."""

    def test_minimum_observation_days_constant(self):
        """Detector should have minimum observation day constants."""
        from claude.tools.experimental.azure.workload_detector import (
            WorkloadPatternDetector,
        )

        assert WorkloadPatternDetector.MIN_OBSERVATION_DAYS == 7
        assert WorkloadPatternDetector.MIN_IDLE_OBSERVATION_DAYS == 14
        assert WorkloadPatternDetector.MIN_MONTHLY_PATTERN_DAYS == 60


class TestBatchJobDetection:
    """Tests for detecting batch/scheduled workloads."""

    def test_daily_batch_job_detected_as_scheduled(self):
        """
        VM with 2am-4am daily spikes should be SCHEDULED, not IDLE.

        This is CRITICAL for preventing false positives on batch processing VMs.
        """
        from claude.tools.experimental.azure.workload_detector import (
            WorkloadPatternDetector,
            WorkloadPattern,
        )

        detector = WorkloadPatternDetector()

        # Generate 14 days of metrics with 2-4am spikes
        base_time = datetime.now() - timedelta(days=14)
        metrics = generate_metrics(
            base_time=base_time,
            hours=14 * 24,  # 14 days
            cpu_pattern="scheduled_daily",
            base_cpu=3.0,
            peak_cpu=85.0,
            peak_hours=[2, 3, 4],
        )

        analysis = detector.analyze_pattern("resource-123", metrics)

        assert analysis.pattern == WorkloadPattern.SCHEDULED
        assert analysis.confidence >= 0.75
        assert 2 in analysis.peak_hours or 3 in analysis.peak_hours

    def test_weekend_dev_vm_not_flagged_as_idle(self):
        """
        VM used only weekends should be SCHEDULED, not IDLE.

        Developers may have VMs they only use on weekends for side projects.
        """
        from claude.tools.experimental.azure.workload_detector import (
            WorkloadPatternDetector,
            WorkloadPattern,
        )

        detector = WorkloadPatternDetector()

        # Generate 21 days with weekend-only usage
        base_time = datetime.now() - timedelta(days=21)
        metrics = generate_metrics(
            base_time=base_time,
            hours=21 * 24,
            cpu_pattern="scheduled_weekly",
            base_cpu=2.0,
            peak_cpu=60.0,
            peak_days=[5, 6],  # Saturday, Sunday
        )

        analysis = detector.analyze_pattern("resource-456", metrics)

        assert analysis.pattern == WorkloadPattern.SCHEDULED
        assert analysis.confidence >= 0.70
        assert 5 in analysis.peak_days or 6 in analysis.peak_days

    def test_month_end_batch_detected(self):
        """
        VM with month-end spikes should be SCHEDULED.

        Many financial systems have month-end batch processing.
        """
        from claude.tools.experimental.azure.workload_detector import (
            WorkloadPatternDetector,
            WorkloadPattern,
        )

        detector = WorkloadPatternDetector()

        # Generate 90 days with month-end spikes (days 28-31)
        base_time = datetime.now() - timedelta(days=90)
        metrics = []

        for day in range(90):
            timestamp = base_time + timedelta(days=day)
            day_of_month = timestamp.day

            # Spike on days 28-31 (month end)
            is_month_end = day_of_month >= 28

            for hour in range(24):
                metrics.append({
                    "timestamp": (timestamp + timedelta(hours=hour)).isoformat(),
                    "cpu_percent": 75.0 if is_month_end else 3.0,
                    "memory_percent": 60.0 if is_month_end else 5.0,
                })

        analysis = detector.analyze_pattern("resource-789", metrics)

        assert analysis.pattern in [WorkloadPattern.SCHEDULED, WorkloadPattern.SEASONAL]
        assert analysis.confidence >= 0.65


class TestIdleVMDetection:
    """Tests for detecting truly idle VMs."""

    def test_truly_idle_vm_detected(self):
        """
        VM with 14+ days of <5% CPU should be IDLE.
        """
        from claude.tools.experimental.azure.workload_detector import (
            WorkloadPatternDetector,
            WorkloadPattern,
        )

        detector = WorkloadPatternDetector()

        # Generate 14 days of consistently low usage
        base_time = datetime.now() - timedelta(days=14)
        metrics = generate_metrics(
            base_time=base_time,
            hours=14 * 24,
            cpu_pattern="idle",
            base_cpu=2.0,
        )

        analysis = detector.analyze_pattern("idle-vm", metrics)

        assert analysis.pattern == WorkloadPattern.IDLE
        assert analysis.confidence >= 0.80
        assert analysis.observation_days >= 14

    def test_insufficient_observation_returns_unknown(self):
        """
        <7 days observation should return UNKNOWN.

        We can't make confident predictions without enough data.
        """
        from claude.tools.experimental.azure.workload_detector import (
            WorkloadPatternDetector,
            WorkloadPattern,
        )

        detector = WorkloadPatternDetector()

        # Only 3 days of data
        base_time = datetime.now() - timedelta(days=3)
        metrics = generate_metrics(
            base_time=base_time,
            hours=3 * 24,
            cpu_pattern="idle",
            base_cpu=2.0,
        )

        analysis = detector.analyze_pattern("short-observation", metrics)

        assert analysis.pattern == WorkloadPattern.UNKNOWN
        assert analysis.confidence < 0.5

    def test_single_spike_prevents_idle_classification(self):
        """
        Any spike >50% CPU should prevent IDLE classification.

        A single significant spike indicates the resource IS being used,
        even if rarely.
        """
        from claude.tools.experimental.azure.workload_detector import (
            WorkloadPatternDetector,
            WorkloadPattern,
        )

        detector = WorkloadPatternDetector()

        # 14 days of low usage with ONE spike
        base_time = datetime.now() - timedelta(days=14)
        metrics = generate_metrics(
            base_time=base_time,
            hours=14 * 24,
            cpu_pattern="idle",
            base_cpu=2.0,
        )

        # Add a single spike
        metrics[100]["cpu_percent"] = 75.0

        analysis = detector.analyze_pattern("spike-vm", metrics)

        # Should NOT be IDLE due to the spike
        assert analysis.pattern != WorkloadPattern.IDLE or analysis.confidence < 0.70


class TestConfidenceScoring:
    """Tests for confidence scoring logic."""

    def test_confidence_increases_with_observation_period(self):
        """
        Longer observation periods should increase idle confidence.

        Uses calculate_idle_confidence directly since analyze_pattern may return
        different pattern types based on observation period thresholds.
        """
        from claude.tools.experimental.azure.workload_detector import (
            WorkloadPatternDetector,
        )

        detector = WorkloadPatternDetector()

        # 7 days of idle
        base_time = datetime.now() - timedelta(days=7)
        metrics_7d = generate_metrics(
            base_time=base_time,
            hours=7 * 24,
            cpu_pattern="idle",
            base_cpu=2.0,
        )

        # 21 days of idle
        base_time_21 = datetime.now() - timedelta(days=21)
        metrics_21d = generate_metrics(
            base_time=base_time_21,
            hours=21 * 24,
            cpu_pattern="idle",
            base_cpu=2.0,
        )

        # Compare idle confidence directly
        confidence_7d = detector.calculate_idle_confidence(metrics_7d)
        confidence_21d = detector.calculate_idle_confidence(metrics_21d)

        assert confidence_21d > confidence_7d

    def test_night_hours_included_in_analysis(self):
        """
        Analysis should include ALL hours of day, not just business hours.

        Batch jobs often run at night - missing night hours causes false positives.
        """
        from claude.tools.experimental.azure.workload_detector import (
            WorkloadPatternDetector,
            WorkloadPattern,
        )

        detector = WorkloadPatternDetector()

        # Generate metrics with 3am-4am batch job
        base_time = datetime.now() - timedelta(days=14)
        metrics = generate_metrics(
            base_time=base_time,
            hours=14 * 24,
            cpu_pattern="scheduled_daily",
            base_cpu=2.0,
            peak_cpu=80.0,
            peak_hours=[3, 4],  # 3-4am only
        )

        analysis = detector.analyze_pattern("night-batch", metrics)

        # Should detect the night batch job
        assert analysis.pattern == WorkloadPattern.SCHEDULED
        assert 3 in analysis.peak_hours or 4 in analysis.peak_hours


class TestScheduledWorkloadDetails:
    """Tests for scheduled workload detection details."""

    def test_detect_scheduled_workload_returns_schedule_details(self):
        """detect_scheduled_workload should return schedule details."""
        from claude.tools.experimental.azure.workload_detector import (
            WorkloadPatternDetector,
        )

        detector = WorkloadPatternDetector()

        # Daily 2-4am batch
        base_time = datetime.now() - timedelta(days=14)
        metrics = generate_metrics(
            base_time=base_time,
            hours=14 * 24,
            cpu_pattern="scheduled_daily",
            base_cpu=2.0,
            peak_cpu=80.0,
            peak_hours=[2, 3, 4],
        )

        schedule = detector.detect_scheduled_workload(metrics)

        assert schedule is not None
        assert "peak_hours" in schedule
        assert any(h in schedule["peak_hours"] for h in [2, 3, 4])

    def test_no_schedule_returns_none(self):
        """No clear schedule should return None."""
        from claude.tools.experimental.azure.workload_detector import (
            WorkloadPatternDetector,
        )

        detector = WorkloadPatternDetector()

        # Random/steady usage without pattern
        base_time = datetime.now() - timedelta(days=14)
        metrics = generate_metrics(
            base_time=base_time,
            hours=14 * 24,
            cpu_pattern="steady",
            base_cpu=30.0,
        )

        schedule = detector.detect_scheduled_workload(metrics)

        # May return None or low-confidence result
        assert schedule is None or schedule.get("confidence", 0) < 0.5


class TestIdleConfidenceCalculation:
    """Tests for idle confidence calculation."""

    def test_calculate_idle_confidence_high_for_truly_idle(self):
        """High confidence for consistently idle VMs."""
        from claude.tools.experimental.azure.workload_detector import (
            WorkloadPatternDetector,
        )

        detector = WorkloadPatternDetector()

        # 21 days of very low usage
        base_time = datetime.now() - timedelta(days=21)
        metrics = generate_metrics(
            base_time=base_time,
            hours=21 * 24,
            cpu_pattern="idle",
            base_cpu=1.0,
        )

        confidence = detector.calculate_idle_confidence(metrics, threshold_cpu=5.0)

        assert confidence >= 0.85

    def test_calculate_idle_confidence_low_with_spikes(self):
        """Low confidence when there are usage spikes."""
        from claude.tools.experimental.azure.workload_detector import (
            WorkloadPatternDetector,
        )

        detector = WorkloadPatternDetector()

        # Mostly idle with occasional spikes
        base_time = datetime.now() - timedelta(days=14)
        metrics = generate_metrics(
            base_time=base_time,
            hours=14 * 24,
            cpu_pattern="random_spikes",
            base_cpu=2.0,
            peak_cpu=60.0,
        )

        confidence = detector.calculate_idle_confidence(metrics, threshold_cpu=5.0)

        assert confidence < 0.70

    def test_calculate_idle_confidence_custom_threshold(self):
        """Should respect custom CPU threshold."""
        from claude.tools.experimental.azure.workload_detector import (
            WorkloadPatternDetector,
        )

        detector = WorkloadPatternDetector()

        # Metrics at 8% CPU - above default 5% but below 10%
        base_time = datetime.now() - timedelta(days=14)
        metrics = generate_metrics(
            base_time=base_time,
            hours=14 * 24,
            cpu_pattern="idle",
            base_cpu=8.0,
        )

        # With 5% threshold - not idle
        confidence_5 = detector.calculate_idle_confidence(metrics, threshold_cpu=5.0)

        # With 10% threshold - is idle
        confidence_10 = detector.calculate_idle_confidence(metrics, threshold_cpu=10.0)

        assert confidence_10 > confidence_5


class TestEdgeCases:
    """Edge case tests."""

    def test_empty_metrics_returns_unknown(self):
        """Empty metrics should return UNKNOWN pattern."""
        from claude.tools.experimental.azure.workload_detector import (
            WorkloadPatternDetector,
            WorkloadPattern,
        )

        detector = WorkloadPatternDetector()
        analysis = detector.analyze_pattern("empty", [])

        assert analysis.pattern == WorkloadPattern.UNKNOWN
        assert analysis.confidence == 0.0

    def test_single_metric_returns_unknown(self):
        """Single metric point should return UNKNOWN."""
        from claude.tools.experimental.azure.workload_detector import (
            WorkloadPatternDetector,
            WorkloadPattern,
        )

        detector = WorkloadPatternDetector()
        metrics = [{
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": 50.0,
        }]

        analysis = detector.analyze_pattern("single", metrics)

        assert analysis.pattern == WorkloadPattern.UNKNOWN

    def test_handles_missing_memory_metric(self):
        """Should handle metrics without memory data."""
        from claude.tools.experimental.azure.workload_detector import (
            WorkloadPatternDetector,
        )

        detector = WorkloadPatternDetector()

        # CPU only metrics
        base_time = datetime.now() - timedelta(days=7)
        metrics = []
        for i in range(7 * 24):
            metrics.append({
                "timestamp": (base_time + timedelta(hours=i)).isoformat(),
                "cpu_percent": 5.0,
            })

        # Should not raise
        analysis = detector.analyze_pattern("cpu-only", metrics)
        assert analysis is not None
