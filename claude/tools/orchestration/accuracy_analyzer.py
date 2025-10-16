#!/usr/bin/env python3
"""
Accuracy Analyzer - Phase 122

Analyzes routing accuracy patterns, identifies low-accuracy scenarios,
and generates improvement recommendations.

Usage:
    analyzer = AccuracyAnalyzer()

    # Overall accuracy
    overall = analyzer.get_overall_accuracy(days=7)

    # By category
    by_category = analyzer.get_accuracy_by_category(days=7)

    # Low accuracy patterns
    low_accuracy = analyzer.identify_low_accuracy_patterns(threshold=0.60)

    # Improvement recommendations
    recommendations = analyzer.generate_recommendations()

Database: routing_decisions.db (read-only)
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class AccuracyMetric:
    """Accuracy metric for a specific dimension"""
    dimension: str  # category, complexity, strategy, etc.
    value: str  # specific value (e.g., "technical", "7", "swarm")
    total_suggestions: int
    accepted_count: int
    rejected_count: int
    acceptance_rate: float
    avg_confidence: float
    sample_size: int


@dataclass
class LowAccuracyPattern:
    """Pattern with low accuracy requiring attention"""
    pattern_type: str  # category, complexity_range, agent_combo, etc.
    pattern_value: str
    acceptance_rate: float
    sample_size: int
    avg_confidence: float
    recommendation: str
    severity: str  # critical, high, medium, low


@dataclass
class ImprovementRecommendation:
    """Actionable recommendation to improve accuracy"""
    priority: str  # critical, high, medium, low
    category: str
    issue: str
    recommendation: str
    expected_impact: str
    implementation: str


class AccuracyAnalyzer:
    """Analyzes routing accuracy and generates recommendations"""

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize analyzer.

        Args:
            db_path: Path to routing_decisions.db
        """
        if db_path is None:
            maia_root = Path(__file__).resolve().parents[3]
            db_path = maia_root / "claude" / "data" / "routing_decisions.db"

        self.db_path = Path(db_path)

        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")

    def get_overall_accuracy(self, days: int = 7) -> Dict[str, Any]:
        """
        Get overall routing accuracy statistics.

        Args:
            days: Number of days to analyze

        Returns:
            Dict with overall statistics
        """
        cutoff = datetime.now() - timedelta(days=days)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN accepted = 1 THEN 1 ELSE 0 END) as accepted,
                SUM(CASE WHEN accepted = 0 THEN 1 ELSE 0 END) as rejected,
                AVG(confidence) as avg_confidence,
                AVG(query_complexity) as avg_complexity
            FROM routing_suggestions
            WHERE timestamp >= ?
            AND accepted IS NOT NULL
        """, (cutoff,))

        row = cursor.fetchone()
        conn.close()

        if row and row[0] > 0:
            total, accepted, rejected, avg_confidence, avg_complexity = row
            return {
                'total_suggestions': total,
                'accepted_count': accepted,
                'rejected_count': rejected,
                'acceptance_rate': accepted / total if total > 0 else 0.0,
                'rejection_rate': rejected / total if total > 0 else 0.0,
                'avg_confidence': avg_confidence or 0.0,
                'avg_complexity': avg_complexity or 0.0,
                'days_analyzed': days
            }

        return {
            'total_suggestions': 0,
            'accepted_count': 0,
            'rejected_count': 0,
            'acceptance_rate': 0.0,
            'rejection_rate': 0.0,
            'avg_confidence': 0.0,
            'avg_complexity': 0.0,
            'days_analyzed': days
        }

    def get_accuracy_by_category(self, days: int = 7) -> List[AccuracyMetric]:
        """
        Get accuracy broken down by query category.

        Args:
            days: Number of days to analyze

        Returns:
            List of AccuracyMetric objects per category
        """
        cutoff = datetime.now() - timedelta(days=days)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                query_category,
                COUNT(*) as total,
                SUM(CASE WHEN accepted = 1 THEN 1 ELSE 0 END) as accepted,
                SUM(CASE WHEN accepted = 0 THEN 1 ELSE 0 END) as rejected,
                AVG(confidence) as avg_confidence
            FROM routing_suggestions
            WHERE timestamp >= ?
            AND accepted IS NOT NULL
            GROUP BY query_category
            ORDER BY total DESC
        """, (cutoff,))

        metrics = []
        for row in cursor.fetchall():
            category, total, accepted, rejected, avg_confidence = row
            metrics.append(AccuracyMetric(
                dimension="category",
                value=category or "unknown",
                total_suggestions=total,
                accepted_count=accepted,
                rejected_count=rejected,
                acceptance_rate=accepted / total if total > 0 else 0.0,
                avg_confidence=avg_confidence or 0.0,
                sample_size=total
            ))

        conn.close()
        return metrics

    def get_accuracy_by_complexity(self, days: int = 7) -> List[AccuracyMetric]:
        """
        Get accuracy broken down by query complexity ranges.

        Args:
            days: Number of days to analyze

        Returns:
            List of AccuracyMetric objects per complexity range
        """
        cutoff = datetime.now() - timedelta(days=days)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Group complexity into ranges: 1-3 (simple), 4-6 (medium), 7-10 (complex)
        cursor.execute("""
            SELECT
                CASE
                    WHEN query_complexity <= 3 THEN 'simple (1-3)'
                    WHEN query_complexity <= 6 THEN 'medium (4-6)'
                    ELSE 'complex (7-10)'
                END as complexity_range,
                COUNT(*) as total,
                SUM(CASE WHEN accepted = 1 THEN 1 ELSE 0 END) as accepted,
                SUM(CASE WHEN accepted = 0 THEN 1 ELSE 0 END) as rejected,
                AVG(confidence) as avg_confidence
            FROM routing_suggestions
            WHERE timestamp >= ?
            AND accepted IS NOT NULL
            GROUP BY complexity_range
            ORDER BY
                CASE complexity_range
                    WHEN 'simple (1-3)' THEN 1
                    WHEN 'medium (4-6)' THEN 2
                    ELSE 3
                END
        """, (cutoff,))

        metrics = []
        for row in cursor.fetchall():
            range_name, total, accepted, rejected, avg_confidence = row
            metrics.append(AccuracyMetric(
                dimension="complexity",
                value=range_name,
                total_suggestions=total,
                accepted_count=accepted,
                rejected_count=rejected,
                acceptance_rate=accepted / total if total > 0 else 0.0,
                avg_confidence=avg_confidence or 0.0,
                sample_size=total
            ))

        conn.close()
        return metrics

    def get_accuracy_by_strategy(self, days: int = 7) -> List[AccuracyMetric]:
        """
        Get accuracy broken down by routing strategy.

        Args:
            days: Number of days to analyze

        Returns:
            List of AccuracyMetric objects per strategy
        """
        cutoff = datetime.now() - timedelta(days=days)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                routing_strategy,
                COUNT(*) as total,
                SUM(CASE WHEN accepted = 1 THEN 1 ELSE 0 END) as accepted,
                SUM(CASE WHEN accepted = 0 THEN 1 ELSE 0 END) as rejected,
                AVG(confidence) as avg_confidence
            FROM routing_suggestions
            WHERE timestamp >= ?
            AND accepted IS NOT NULL
            GROUP BY routing_strategy
            ORDER BY total DESC
        """, (cutoff,))

        metrics = []
        for row in cursor.fetchall():
            strategy, total, accepted, rejected, avg_confidence = row
            metrics.append(AccuracyMetric(
                dimension="strategy",
                value=strategy or "unknown",
                total_suggestions=total,
                accepted_count=accepted,
                rejected_count=rejected,
                acceptance_rate=accepted / total if total > 0 else 0.0,
                avg_confidence=avg_confidence or 0.0,
                sample_size=total
            ))

        conn.close()
        return metrics

    def identify_low_accuracy_patterns(
        self,
        threshold: float = 0.60,
        min_sample_size: int = 5
    ) -> List[LowAccuracyPattern]:
        """
        Identify patterns with low acceptance rate requiring attention.

        Args:
            threshold: Acceptance rate threshold (patterns below this are flagged)
            min_sample_size: Minimum number of samples to consider

        Returns:
            List of low accuracy patterns with recommendations
        """
        patterns = []

        # Check by category
        category_metrics = self.get_accuracy_by_category(days=30)
        for metric in category_metrics:
            if metric.sample_size >= min_sample_size and metric.acceptance_rate < threshold:
                severity = self._calculate_severity(metric.acceptance_rate, metric.sample_size)
                patterns.append(LowAccuracyPattern(
                    pattern_type="category",
                    pattern_value=metric.value,
                    acceptance_rate=metric.acceptance_rate,
                    sample_size=metric.sample_size,
                    avg_confidence=metric.avg_confidence,
                    recommendation=self._generate_category_recommendation(metric),
                    severity=severity
                ))

        # Check by complexity
        complexity_metrics = self.get_accuracy_by_complexity(days=30)
        for metric in complexity_metrics:
            if metric.sample_size >= min_sample_size and metric.acceptance_rate < threshold:
                severity = self._calculate_severity(metric.acceptance_rate, metric.sample_size)
                patterns.append(LowAccuracyPattern(
                    pattern_type="complexity",
                    pattern_value=metric.value,
                    acceptance_rate=metric.acceptance_rate,
                    sample_size=metric.sample_size,
                    avg_confidence=metric.avg_confidence,
                    recommendation=self._generate_complexity_recommendation(metric),
                    severity=severity
                ))

        # Check by strategy
        strategy_metrics = self.get_accuracy_by_strategy(days=30)
        for metric in strategy_metrics:
            if metric.sample_size >= min_sample_size and metric.acceptance_rate < threshold:
                severity = self._calculate_severity(metric.acceptance_rate, metric.sample_size)
                patterns.append(LowAccuracyPattern(
                    pattern_type="strategy",
                    pattern_value=metric.value,
                    acceptance_rate=metric.acceptance_rate,
                    sample_size=metric.sample_size,
                    avg_confidence=metric.avg_confidence,
                    recommendation=self._generate_strategy_recommendation(metric),
                    severity=severity
                ))

        # Sort by severity and acceptance rate
        patterns.sort(key=lambda p: (
            {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}[p.severity],
            p.acceptance_rate
        ))

        return patterns

    def _calculate_severity(self, acceptance_rate: float, sample_size: int) -> str:
        """Calculate severity based on acceptance rate and sample size"""
        if acceptance_rate < 0.40 and sample_size >= 10:
            return "critical"
        elif acceptance_rate < 0.50:
            return "high"
        elif acceptance_rate < 0.60:
            return "medium"
        else:
            return "low"

    def _generate_category_recommendation(self, metric: AccuracyMetric) -> str:
        """Generate recommendation for low-accuracy category"""
        if metric.avg_confidence < 0.70:
            return f"Low confidence ({metric.avg_confidence:.0%}) - refine intent classification for '{metric.value}' category"
        else:
            return f"High confidence ({metric.avg_confidence:.0%}) but low acceptance - agents may not match user expectations for '{metric.value}'"

    def _generate_complexity_recommendation(self, metric: AccuracyMetric) -> str:
        """Generate recommendation for low-accuracy complexity range"""
        if "simple" in metric.value:
            return "Simple queries being over-routed - consider raising complexity threshold for routing"
        elif "complex" in metric.value:
            return "Complex queries need better agent matching - review swarm/chain strategies"
        else:
            return "Medium complexity queries need routing refinement"

    def _generate_strategy_recommendation(self, metric: AccuracyMetric) -> str:
        """Generate recommendation for low-accuracy strategy"""
        if metric.value == "swarm":
            return "Swarm strategy over-suggesting multiple agents - refine agent selection criteria"
        elif metric.value == "prompt_chain":
            return "Chain strategy not matching user needs - review sequential routing logic"
        else:
            return f"Review routing logic for '{metric.value}' strategy"

    def generate_recommendations(self, days: int = 7) -> List[ImprovementRecommendation]:
        """
        Generate actionable improvement recommendations.

        Args:
            days: Days to analyze for recommendations

        Returns:
            List of prioritized recommendations
        """
        recommendations = []

        # Get overall accuracy
        overall = self.get_overall_accuracy(days=days)

        # Recommendation 1: Overall acceptance rate
        if overall['acceptance_rate'] < 0.80:
            recommendations.append(ImprovementRecommendation(
                priority="critical" if overall['acceptance_rate'] < 0.60 else "high",
                category="overall",
                issue=f"Overall acceptance rate is {overall['acceptance_rate']:.1%} (target: >80%)",
                recommendation="Review and refine intent classification and agent selection logic",
                expected_impact="+10-15% acceptance rate improvement",
                implementation="Analyze override patterns, adjust thresholds, refine agent matching"
            ))

        # Recommendation 2: Low accuracy patterns
        low_patterns = self.identify_low_accuracy_patterns(threshold=0.60, min_sample_size=5)
        for pattern in low_patterns[:3]:  # Top 3 worst patterns
            recommendations.append(ImprovementRecommendation(
                priority=pattern.severity,
                category=pattern.pattern_type,
                issue=f"{pattern.pattern_value}: {pattern.acceptance_rate:.1%} acceptance ({pattern.sample_size} samples)",
                recommendation=pattern.recommendation,
                expected_impact=f"+15-25% for {pattern.pattern_value}",
                implementation="See pattern-specific recommendation"
            ))

        # Recommendation 3: Confidence vs accuracy mismatch
        if overall['avg_confidence'] > 0.80 and overall['acceptance_rate'] < 0.70:
            recommendations.append(ImprovementRecommendation(
                priority="high",
                category="confidence_calibration",
                issue=f"High confidence ({overall['avg_confidence']:.1%}) but low acceptance ({overall['acceptance_rate']:.1%})",
                recommendation="Recalibrate confidence scoring - coordinator is overconfident",
                expected_impact="+5-10% accuracy through better confidence calibration",
                implementation="Review confidence calculation, lower thresholds for routing suggestions"
            ))

        # Sort by priority
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        recommendations.sort(key=lambda r: priority_order[r.priority])

        return recommendations

    def get_override_analysis(self, days: int = 7) -> Dict[str, Any]:
        """
        Analyze why routing suggestions were overridden.

        Args:
            days: Days to analyze

        Returns:
            Dict with override patterns and reasons
        """
        cutoff = datetime.now() - timedelta(days=days)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get override counts by type
        cursor.execute("""
            SELECT
                override_type,
                COUNT(*) as count,
                AVG(confidence) as avg_confidence
            FROM override_patterns
            WHERE timestamp >= ?
            GROUP BY override_type
            ORDER BY count DESC
        """, (cutoff,))

        override_types = {}
        for row in cursor.fetchall():
            override_type, count, avg_confidence = row
            override_types[override_type] = {
                'count': count,
                'avg_confidence': avg_confidence or 0.0
            }

        # Get top override reasons
        cursor.execute("""
            SELECT override_reason, COUNT(*) as count
            FROM override_patterns
            WHERE timestamp >= ?
            AND override_reason IS NOT NULL
            GROUP BY override_reason
            ORDER BY count DESC
            LIMIT 10
        """, (cutoff,))

        top_reasons = [
            {'reason': row[0], 'count': row[1]}
            for row in cursor.fetchall()
        ]

        conn.close()

        return {
            'override_types': override_types,
            'top_reasons': top_reasons,
            'days_analyzed': days
        }


def main():
    """CLI interface"""
    import sys

    analyzer = AccuracyAnalyzer()

    if len(sys.argv) < 2:
        command = "summary"
    else:
        command = sys.argv[1]

    if command == "summary":
        # Overall summary
        overall = analyzer.get_overall_accuracy(days=7)
        print("📊 Routing Accuracy Summary (Last 7 Days)\n")
        print(f"Total Suggestions: {overall['total_suggestions']}")
        print(f"Acceptance Rate:   {overall['acceptance_rate']:.1%}")
        print(f"Rejection Rate:    {overall['rejection_rate']:.1%}")
        print(f"Avg Confidence:    {overall['avg_confidence']:.1%}")
        print(f"Avg Complexity:    {overall['avg_complexity']:.1f}/10")

    elif command == "category":
        # By category
        metrics = analyzer.get_accuracy_by_category(days=30)
        print("📊 Accuracy by Category (Last 30 Days)\n")
        for metric in metrics:
            print(f"{metric.value:20s} {metric.acceptance_rate:>6.1%} ({metric.sample_size:>3} samples)")

    elif command == "low":
        # Low accuracy patterns
        patterns = analyzer.identify_low_accuracy_patterns(threshold=0.60)
        print("⚠️  Low Accuracy Patterns\n")
        for pattern in patterns:
            print(f"[{pattern.severity.upper()}] {pattern.pattern_type}: {pattern.pattern_value}")
            print(f"  Acceptance: {pattern.acceptance_rate:.1%} ({pattern.sample_size} samples)")
            print(f"  💡 {pattern.recommendation}\n")

    elif command == "recommendations":
        # Improvement recommendations
        recs = analyzer.generate_recommendations(days=7)
        print("💡 Improvement Recommendations\n")
        for i, rec in enumerate(recs, 1):
            print(f"{i}. [{rec.priority.upper()}] {rec.category}")
            print(f"   Issue: {rec.issue}")
            print(f"   Recommendation: {rec.recommendation}")
            print(f"   Expected Impact: {rec.expected_impact}\n")

    else:
        print(f"Unknown command: {command}")
        print("Available commands: summary, category, low, recommendations")


if __name__ == "__main__":
    main()
