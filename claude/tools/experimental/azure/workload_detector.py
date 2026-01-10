"""
Azure Cost Optimization Workload Pattern Detector

Detects batch jobs, scheduled workloads, and seasonal patterns
to prevent false positive recommendations.

CRITICAL for preventing:
- Flagging batch VMs as idle
- Recommending shutdown of DR/standby resources
- Missing scheduled workloads that run at night/weekends

TDD Implementation - Tests in tests/test_workload_detector.py
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict


class WorkloadPattern(Enum):
    """Types of workload patterns detected."""

    STEADY = "steady"  # Consistent usage throughout
    SCHEDULED = "scheduled"  # Regular patterns (batch jobs, cron)
    SEASONAL = "seasonal"  # Monthly/quarterly patterns
    BURST = "burst"  # Sporadic high usage
    IDLE = "idle"  # Consistently low usage
    UNKNOWN = "unknown"  # Insufficient data


@dataclass
class PatternAnalysis:
    """
    Result of workload pattern analysis.

    Used to determine if a resource is safe to rightsize or shut down.
    """

    resource_id: str
    pattern: WorkloadPattern
    confidence: float
    observation_days: int
    peak_hours: Optional[List[int]] = None  # 0-23
    peak_days: Optional[List[int]] = None  # 0-6 (Mon=0, Sun=6)
    peak_dates: Optional[List[int]] = None  # 1-31 (day of month)
    evidence: Optional[Dict[str, Any]] = None

    def is_safe_to_rightsize(self) -> bool:
        """
        Check if safe to recommend rightsizing.

        Rules:
        - Never rightsize scheduled workloads without human review
        - Require high confidence for idle detection
        - Steady/burst patterns need moderate confidence
        """
        # Never auto-rightsize scheduled workloads
        if self.pattern == WorkloadPattern.SCHEDULED:
            return False

        # Idle requires high confidence and long observation
        if self.pattern == WorkloadPattern.IDLE:
            return self.confidence >= 0.85 and self.observation_days >= 14

        # Other patterns need moderate confidence
        return self.confidence >= 0.75


class WorkloadPatternDetector:
    """
    Detects workload patterns from metrics to prevent false positives.

    Key Rules:
    - Minimum 7 days observation for any recommendation
    - Minimum 14 days for idle resource detection
    - Minimum 60 days (2 cycles) for monthly patterns
    - Check ALL hours of day, not just business hours

    Usage:
        detector = WorkloadPatternDetector()
        analysis = detector.analyze_pattern(resource_id, metrics)

        if analysis.pattern == WorkloadPattern.SCHEDULED:
            # Don't recommend shutdown - it's a batch job!
            pass
    """

    MIN_OBSERVATION_DAYS = 7
    MIN_IDLE_OBSERVATION_DAYS = 14
    MIN_MONTHLY_PATTERN_DAYS = 60

    # Thresholds
    IDLE_CPU_THRESHOLD = 5.0  # Below this = potentially idle
    SPIKE_CPU_THRESHOLD = 50.0  # Above this = significant activity
    PATTERN_CONFIDENCE_THRESHOLD = 0.6  # Min confidence for pattern detection

    def analyze_pattern(
        self,
        resource_id: str,
        metrics: List[Dict[str, Any]],
    ) -> PatternAnalysis:
        """
        Analyze metrics to detect workload pattern.

        Args:
            resource_id: Azure resource ID
            metrics: List of metric data points with timestamp and cpu_percent

        Returns:
            PatternAnalysis with detected pattern and confidence
        """
        if not metrics:
            return PatternAnalysis(
                resource_id=resource_id,
                pattern=WorkloadPattern.UNKNOWN,
                confidence=0.0,
                observation_days=0,
            )

        # Parse metrics and calculate observation period
        parsed_metrics = self._parse_metrics(metrics)
        if not parsed_metrics:
            return PatternAnalysis(
                resource_id=resource_id,
                pattern=WorkloadPattern.UNKNOWN,
                confidence=0.0,
                observation_days=0,
            )

        observation_days = self._calculate_observation_days(parsed_metrics)

        # Insufficient observation period
        if observation_days < self.MIN_OBSERVATION_DAYS:
            return PatternAnalysis(
                resource_id=resource_id,
                pattern=WorkloadPattern.UNKNOWN,
                confidence=0.3,
                observation_days=observation_days,
                evidence={"reason": "insufficient_observation_period"},
            )

        # Check for scheduled patterns first (most important for false positive prevention)
        schedule = self.detect_scheduled_workload(metrics)
        if schedule and schedule.get("confidence", 0) >= self.PATTERN_CONFIDENCE_THRESHOLD:
            return PatternAnalysis(
                resource_id=resource_id,
                pattern=WorkloadPattern.SCHEDULED,
                confidence=schedule["confidence"],
                observation_days=observation_days,
                peak_hours=schedule.get("peak_hours"),
                peak_days=schedule.get("peak_days"),
                peak_dates=schedule.get("peak_dates"),
                evidence=schedule,
            )

        # Check for seasonal (monthly) patterns
        if observation_days >= self.MIN_MONTHLY_PATTERN_DAYS:
            seasonal = self._detect_seasonal_pattern(parsed_metrics)
            if seasonal and seasonal.get("confidence", 0) >= self.PATTERN_CONFIDENCE_THRESHOLD:
                return PatternAnalysis(
                    resource_id=resource_id,
                    pattern=WorkloadPattern.SEASONAL,
                    confidence=seasonal["confidence"],
                    observation_days=observation_days,
                    peak_dates=seasonal.get("peak_dates"),
                    evidence=seasonal,
                )

        # Check for idle pattern
        idle_confidence = self.calculate_idle_confidence(
            metrics, threshold_cpu=self.IDLE_CPU_THRESHOLD
        )
        if idle_confidence >= 0.70 and observation_days >= self.MIN_IDLE_OBSERVATION_DAYS:
            return PatternAnalysis(
                resource_id=resource_id,
                pattern=WorkloadPattern.IDLE,
                confidence=idle_confidence,
                observation_days=observation_days,
                evidence={"idle_confidence": idle_confidence},
            )

        # Check for burst pattern
        burst = self._detect_burst_pattern(parsed_metrics)
        if burst and burst.get("confidence", 0) >= self.PATTERN_CONFIDENCE_THRESHOLD:
            return PatternAnalysis(
                resource_id=resource_id,
                pattern=WorkloadPattern.BURST,
                confidence=burst["confidence"],
                observation_days=observation_days,
                evidence=burst,
            )

        # Default to steady if no clear pattern
        steady_confidence = self._calculate_steady_confidence(parsed_metrics)
        return PatternAnalysis(
            resource_id=resource_id,
            pattern=WorkloadPattern.STEADY,
            confidence=steady_confidence,
            observation_days=observation_days,
            evidence={"type": "steady_usage"},
        )

    def detect_scheduled_workload(
        self,
        metrics: List[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """
        Detect if workload runs on a schedule (batch jobs).

        Looks for:
        - Regular spikes at same time of day (daily batch)
        - Regular spikes on same day of week (weekly batch)
        - Regular spikes on same day of month (monthly batch)

        Returns:
            Dict with schedule details or None if no pattern found
        """
        parsed_metrics = self._parse_metrics(metrics)
        if len(parsed_metrics) < self.MIN_OBSERVATION_DAYS * 24:
            return None

        # Analyze by hour of day
        hourly_usage = defaultdict(list)
        daily_usage = defaultdict(list)

        for metric in parsed_metrics:
            ts = metric["timestamp"]
            cpu = metric["cpu_percent"]
            hourly_usage[ts.hour].append(cpu)
            daily_usage[ts.weekday()].append(cpu)

        # Find peak hours (consistently high usage)
        peak_hours = []
        hourly_avg = {}
        for hour, values in hourly_usage.items():
            avg = sum(values) / len(values)
            hourly_avg[hour] = avg
            if avg > self.SPIKE_CPU_THRESHOLD:
                peak_hours.append(hour)

        # Find peak days
        peak_days = []
        daily_avg = {}
        for day, values in daily_usage.items():
            avg = sum(values) / len(values)
            daily_avg[day] = avg
            if avg > self.SPIKE_CPU_THRESHOLD:
                peak_days.append(day)

        # Calculate confidence based on consistency
        confidence = 0.0
        pattern_type = None

        if peak_hours:
            # Check if non-peak hours are consistently low
            non_peak_avg = sum(
                hourly_avg[h] for h in range(24) if h not in peak_hours
            ) / max(1, 24 - len(peak_hours))

            if non_peak_avg < self.IDLE_CPU_THRESHOLD * 3:
                # Clear contrast between peak and non-peak
                confidence = max(confidence, 0.75)
                pattern_type = "daily_batch"

        if peak_days:
            # Check if non-peak days are consistently low
            non_peak_avg = sum(
                daily_avg[d] for d in range(7) if d not in peak_days
            ) / max(1, 7 - len(peak_days))

            if non_peak_avg < self.IDLE_CPU_THRESHOLD * 3:
                # Clear contrast between peak and non-peak days
                confidence = max(confidence, 0.70)
                pattern_type = pattern_type or "weekly_batch"

        if confidence >= self.PATTERN_CONFIDENCE_THRESHOLD:
            return {
                "confidence": confidence,
                "pattern_type": pattern_type,
                "peak_hours": peak_hours if peak_hours else None,
                "peak_days": peak_days if peak_days else None,
                "hourly_avg": dict(hourly_avg),
                "daily_avg": dict(daily_avg),
            }

        return None

    def calculate_idle_confidence(
        self,
        metrics: List[Dict[str, Any]],
        threshold_cpu: float = 5.0,
    ) -> float:
        """
        Calculate confidence that resource is truly idle.

        Factors:
        - Duration of observation
        - Consistency of low usage
        - Coverage of all hours/days
        - Absence of any high-usage periods

        Args:
            metrics: List of metric data points
            threshold_cpu: CPU threshold below which is considered idle

        Returns:
            Confidence score 0.0-1.0
        """
        parsed_metrics = self._parse_metrics(metrics)
        if not parsed_metrics:
            return 0.0

        observation_days = self._calculate_observation_days(parsed_metrics)
        if observation_days < self.MIN_OBSERVATION_DAYS:
            return 0.3  # Low confidence without enough data

        # Count metrics below threshold
        below_threshold = sum(
            1 for m in parsed_metrics if m["cpu_percent"] <= threshold_cpu
        )
        idle_ratio = below_threshold / len(parsed_metrics)

        # Check for any significant spikes
        max_cpu = max(m["cpu_percent"] for m in parsed_metrics)
        has_spike = max_cpu > self.SPIKE_CPU_THRESHOLD

        # Check hour coverage (should have data from all hours)
        hours_covered = len(set(m["timestamp"].hour for m in parsed_metrics))
        hour_coverage = hours_covered / 24

        # Calculate base confidence from idle ratio
        base_confidence = idle_ratio

        # Penalties
        if has_spike:
            base_confidence *= 0.6  # Significant penalty for spikes

        if hour_coverage < 0.9:
            base_confidence *= 0.8  # Penalty for missing hours

        # Scale confidence by observation period
        # Minimum 7 days for any confidence, max bonus at 28+ days
        if observation_days < self.MIN_OBSERVATION_DAYS:
            observation_factor = 0.5
        elif observation_days < 14:
            # 7-13 days: 70-85% of potential confidence
            observation_factor = 0.70 + (observation_days - 7) * 0.02
        elif observation_days < 28:
            # 14-27 days: 85-95% of potential confidence
            observation_factor = 0.85 + (observation_days - 14) * 0.007
        else:
            # 28+ days: full confidence
            observation_factor = 0.95

        base_confidence *= observation_factor

        return round(min(1.0, base_confidence), 2)

    def _parse_metrics(
        self,
        metrics: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Parse and normalize metric data."""
        parsed = []
        for m in metrics:
            try:
                ts = m.get("timestamp")
                if isinstance(ts, str):
                    ts = datetime.fromisoformat(ts.replace("Z", "+00:00").replace("+00:00", ""))

                cpu = float(m.get("cpu_percent", 0))

                parsed.append({
                    "timestamp": ts,
                    "cpu_percent": cpu,
                    "memory_percent": float(m.get("memory_percent", 0)),
                })
            except (ValueError, TypeError):
                continue

        return sorted(parsed, key=lambda x: x["timestamp"])

    def _calculate_observation_days(
        self,
        parsed_metrics: List[Dict[str, Any]],
    ) -> int:
        """Calculate observation period in days (inclusive of partial days)."""
        if len(parsed_metrics) < 2:
            return 0

        first = parsed_metrics[0]["timestamp"]
        last = parsed_metrics[-1]["timestamp"]
        delta = last - first

        # Include partial days (round up if there are hours beyond whole days)
        total_hours = delta.total_seconds() / 3600
        return int((total_hours + 23) // 24)  # Round up to include partial days

    def _detect_seasonal_pattern(
        self,
        parsed_metrics: List[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """Detect monthly/seasonal patterns."""
        # Group by day of month
        monthly_usage = defaultdict(list)
        for metric in parsed_metrics:
            day_of_month = metric["timestamp"].day
            monthly_usage[day_of_month].append(metric["cpu_percent"])

        # Find peak days of month
        peak_dates = []
        monthly_avg = {}
        for day, values in monthly_usage.items():
            if len(values) >= 2:  # Need at least 2 occurrences
                avg = sum(values) / len(values)
                monthly_avg[day] = avg
                if avg > self.SPIKE_CPU_THRESHOLD:
                    peak_dates.append(day)

        if peak_dates and len(peak_dates) <= 5:  # Reasonable number of peak days
            # Check if non-peak days are consistently low
            non_peak_days = [d for d in monthly_avg if d not in peak_dates]
            if non_peak_days:
                non_peak_avg = sum(monthly_avg[d] for d in non_peak_days) / len(non_peak_days)
                if non_peak_avg < self.IDLE_CPU_THRESHOLD * 3:
                    return {
                        "confidence": 0.70,
                        "pattern_type": "monthly_batch",
                        "peak_dates": sorted(peak_dates),
                        "monthly_avg": dict(monthly_avg),
                    }

        return None

    def _detect_burst_pattern(
        self,
        parsed_metrics: List[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """Detect sporadic burst usage pattern."""
        if not parsed_metrics:
            return None

        # Count significant spikes
        spike_count = sum(
            1 for m in parsed_metrics if m["cpu_percent"] > self.SPIKE_CPU_THRESHOLD
        )
        spike_ratio = spike_count / len(parsed_metrics)

        # Burst pattern: occasional spikes (5-30% of time)
        if 0.05 <= spike_ratio <= 0.30:
            return {
                "confidence": 0.65,
                "pattern_type": "burst",
                "spike_ratio": spike_ratio,
            }

        return None

    def _calculate_steady_confidence(
        self,
        parsed_metrics: List[Dict[str, Any]],
    ) -> float:
        """Calculate confidence for steady workload pattern."""
        if not parsed_metrics:
            return 0.0

        cpu_values = [m["cpu_percent"] for m in parsed_metrics]
        avg_cpu = sum(cpu_values) / len(cpu_values)

        # Calculate variance (lower = more steady)
        variance = sum((c - avg_cpu) ** 2 for c in cpu_values) / len(cpu_values)
        std_dev = variance ** 0.5

        # Coefficient of variation (lower = more steady)
        if avg_cpu > 0:
            cv = std_dev / avg_cpu
        else:
            cv = 0

        # Convert to confidence (lower CV = higher confidence)
        confidence = max(0.5, min(1.0, 1.0 - cv * 0.5))

        return round(confidence, 2)
