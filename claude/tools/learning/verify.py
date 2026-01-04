#!/usr/bin/env python3
"""
VERIFY Phase - Success Measurement

Measures session success across multiple dimensions:
- Tool execution success rate
- Task completion indicators
- Error recovery effectiveness
- User correction frequency
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class VerifyResult:
    """Result of VERIFY phase analysis."""
    success: bool
    confidence: float
    metrics: Dict[str, float]
    insights: List[str]


class VerifyPhase:
    """Implements VERIFY phase logic."""

    # Thresholds
    SUCCESS_THRESHOLD = 0.7
    TOOL_SUCCESS_WEIGHT = 0.4
    COMPLETION_WEIGHT = 0.4
    RECOVERY_WEIGHT = 0.2

    def verify(
        self,
        uocs_summary: Dict[str, Any],
        session_data: Dict[str, Any]
    ) -> VerifyResult:
        """
        Verify session success.

        Args:
            uocs_summary: From UOCS.get_summary()
            session_data: Session metadata (agent, domain, etc.)

        Returns:
            VerifyResult with success assessment
        """
        metrics = {}
        insights = []

        # Metric 1: Tool success rate
        tool_success = uocs_summary.get('success_rate', 0)
        metrics['tool_success_rate'] = tool_success

        if tool_success < 0.8:
            insights.append(f"Tool success rate ({tool_success:.0%}) below target")

        # Metric 2: Task completion heuristic
        # High tool count + low errors = likely completion
        tool_count = uocs_summary.get('total_captures', 0)
        completion = min(1.0, tool_count / 10) * tool_success  # Normalize to ~10 tools
        metrics['task_completion'] = completion

        # Metric 3: Error recovery
        # If there were failures but overall success, good recovery
        if tool_success > 0 and tool_success < 1.0:
            recovery = tool_success  # Recovered from some failures
        else:
            recovery = 1.0 if tool_success == 1.0 else 0.0
        metrics['error_recovery'] = recovery

        # Metric 4: Session duration efficiency
        total_latency = uocs_summary.get('total_latency_ms', 0)
        if tool_count > 0:
            avg_latency = total_latency / tool_count
            # Penalize very slow sessions (>5s avg)
            efficiency = min(1.0, 5000 / max(avg_latency, 1))
            metrics['efficiency'] = efficiency
        else:
            metrics['efficiency'] = 0.5  # Neutral

        # Calculate overall score
        overall = (
            metrics['tool_success_rate'] * self.TOOL_SUCCESS_WEIGHT +
            metrics['task_completion'] * self.COMPLETION_WEIGHT +
            metrics['error_recovery'] * self.RECOVERY_WEIGHT
        )

        success = overall >= self.SUCCESS_THRESHOLD

        if success:
            insights.append(f"Session successful (confidence: {overall:.0%})")
        else:
            insights.append(f"Session had issues (confidence: {overall:.0%})")

        return VerifyResult(
            success=success,
            confidence=overall,
            metrics=metrics,
            insights=insights
        )

    def to_dict(self, result: VerifyResult) -> Dict[str, Any]:
        """Convert result to dict for storage."""
        return asdict(result)


# Singleton
_verify: Optional[VerifyPhase] = None


def get_verify() -> VerifyPhase:
    """Get VerifyPhase singleton."""
    global _verify
    if _verify is None:
        _verify = VerifyPhase()
    return _verify


__all__ = ["VerifyPhase", "VerifyResult", "get_verify"]
