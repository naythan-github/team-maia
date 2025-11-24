#!/usr/bin/env python3
"""
A/B Testing Framework - Agentic AI Enhancement Phase 4 (Phase 183)

Implements systematic A/B testing with statistical significance:
- Traffic splitting (random, weighted, sticky)
- Outcome tracking per variant
- Chi-squared significance testing
- Auto-winner declaration

Author: Maia System (SRE Principal Engineer Agent)
Created: 2025-11-24 (Agentic AI Enhancement Project - Phase 4)
"""

import hashlib
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from scipy import stats

logger = logging.getLogger(__name__)


class ExperimentStatus(Enum):
    """Status of an A/B experiment"""
    ACTIVE = "active"
    PAUSED = "paused"
    CONCLUDED = "concluded"


class TrafficSplitStrategy(Enum):
    """Strategy for splitting traffic between variants"""
    RANDOM = "random"  # Pure random assignment
    WEIGHTED = "weighted"  # Weighted random based on traffic_split
    STICKY = "sticky"  # Sticky assignment based on user_id


@dataclass
class ExperimentConfig:
    """Configuration for an A/B experiment"""
    name: str
    variants: List[str]
    description: Optional[str] = None
    traffic_split: Optional[List[float]] = None
    min_samples_per_variant: int = 30
    significance_threshold: float = 0.95
    auto_conclude: bool = False
    early_stopping: bool = False
    early_stop_threshold: float = 0.01


@dataclass
class VariantStats:
    """Statistics for a variant"""
    variant: str
    total_count: int
    success_count: int
    success_rate: float
    avg_quality: Optional[float] = None


@dataclass
class ExperimentInfo:
    """Information about an experiment"""
    id: str
    name: str
    variants: List[str]
    status: ExperimentStatus
    created_at: datetime
    winner: Optional[str] = None
    traffic_split: Optional[List[float]] = None


@dataclass
class ABResults:
    """Results of an A/B experiment"""
    experiment_id: str
    name: str
    status: ExperimentStatus
    variant_stats: Dict[str, VariantStats]
    is_significant: bool
    confidence: float
    winner: Optional[str] = None
    message: str = ""
    underperforming_variants: List[str] = field(default_factory=list)


class ABTestingFramework:
    """
    A/B Testing Framework with Statistical Significance.

    Provides systematic comparison of approaches with:
    - Traffic splitting strategies
    - Per-variant outcome tracking
    - Chi-squared significance testing
    - Auto-winner declaration
    """

    def __init__(
        self,
        outcome_tracker: Optional[Any] = None,
        db_path: Optional[str] = None
    ):
        """
        Initialize A/B Testing Framework.

        Args:
            outcome_tracker: OutcomeTracker instance for persistence
            db_path: Path to create OutcomeTracker if not provided
        """
        if outcome_tracker is not None:
            self.outcome_tracker = outcome_tracker
        else:
            from claude.tools.orchestration.outcome_tracker import OutcomeTracker
            if db_path is None:
                maia_root = Path(__file__).resolve().parents[3]
                db_path = maia_root / "claude" / "data" / "databases" / "intelligence" / "ab_testing.db"
            self.outcome_tracker = OutcomeTracker(db_path=str(db_path))

        # In-memory experiment metadata (extends OutcomeTracker experiments)
        self._experiments: Dict[str, Dict] = {}

    def create_experiment(
        self,
        name: str,
        variants: List[str],
        description: Optional[str] = None,
        traffic_split: Optional[List[float]] = None,
        strategy: TrafficSplitStrategy = TrafficSplitStrategy.RANDOM,
        min_samples_per_variant: int = 30,
        significance_threshold: float = 0.95,
        auto_conclude: bool = False,
        early_stopping: bool = False,
        early_stop_threshold: float = 0.01
    ) -> str:
        """
        Create a new A/B experiment.

        Args:
            name: Experiment name
            variants: List of variant names (minimum 2)
            description: Optional description
            traffic_split: Optional traffic weights per variant
            strategy: Traffic split strategy
            min_samples_per_variant: Minimum samples before significance test
            significance_threshold: Confidence threshold for winner (e.g., 0.95)
            auto_conclude: Auto-conclude when significance reached
            early_stopping: Enable early stopping for clear losers
            early_stop_threshold: Probability threshold for early stopping

        Returns:
            Experiment ID
        """
        # Validate variants
        if len(variants) < 2:
            raise ValueError("Experiment requires at least 2 variants")

        # Validate traffic split
        if traffic_split is not None:
            if len(traffic_split) != len(variants):
                raise ValueError("traffic_split length must match variants")
            if abs(sum(traffic_split) - 1.0) > 0.01:
                raise ValueError("traffic_split must sum to 1.0")
        else:
            # Equal split
            traffic_split = [1.0 / len(variants)] * len(variants)

        # Create in OutcomeTracker
        from claude.tools.orchestration.outcome_tracker import Experiment
        exp = Experiment(name=name, variants=variants, description=description)
        exp_id = self.outcome_tracker.create_experiment(exp)

        # Store extended metadata
        self._experiments[exp_id] = {
            "name": name,
            "variants": variants,
            "traffic_split": traffic_split,
            "strategy": strategy,
            "min_samples": min_samples_per_variant,
            "significance_threshold": significance_threshold,
            "auto_conclude": auto_conclude,
            "early_stopping": early_stopping,
            "early_stop_threshold": early_stop_threshold,
            "status": ExperimentStatus.ACTIVE,
            "created_at": datetime.now(),
            "winner": None,
            "user_assignments": {}  # For sticky assignment
        }

        return exp_id

    def create_experiment_from_config(self, config: ExperimentConfig) -> str:
        """Create experiment from config object"""
        return self.create_experiment(
            name=config.name,
            variants=config.variants,
            description=config.description,
            traffic_split=config.traffic_split,
            min_samples_per_variant=config.min_samples_per_variant,
            significance_threshold=config.significance_threshold,
            auto_conclude=config.auto_conclude,
            early_stopping=config.early_stopping,
            early_stop_threshold=config.early_stop_threshold
        )

    def get_experiment(self, experiment_id: str) -> ExperimentInfo:
        """Get experiment information"""
        if experiment_id not in self._experiments:
            # Try to load from OutcomeTracker
            results = self.outcome_tracker.get_experiment_results(experiment_id)
            return ExperimentInfo(
                id=experiment_id,
                name=results.name,
                variants=list(results.variant_stats.keys()),
                status=ExperimentStatus(results.status) if results.status in [e.value for e in ExperimentStatus] else ExperimentStatus.ACTIVE,
                created_at=datetime.now(),
                winner=results.winner
            )

        meta = self._experiments[experiment_id]
        return ExperimentInfo(
            id=experiment_id,
            name=meta["name"],
            variants=meta["variants"],
            status=meta["status"],
            created_at=meta["created_at"],
            winner=meta["winner"],
            traffic_split=meta["traffic_split"]
        )

    def get_variant(
        self,
        experiment_id: str,
        user_id: Optional[str] = None
    ) -> str:
        """
        Get variant assignment for this request.

        Args:
            experiment_id: Experiment ID
            user_id: Optional user ID for sticky assignment

        Returns:
            Variant name
        """
        if experiment_id not in self._experiments:
            raise ValueError(f"Experiment {experiment_id} not found")

        meta = self._experiments[experiment_id]

        # If paused, return first variant (control)
        if meta["status"] == ExperimentStatus.PAUSED:
            return meta["variants"][0]

        # If concluded, return winner
        if meta["status"] == ExperimentStatus.CONCLUDED and meta["winner"]:
            return meta["winner"]

        # Sticky assignment
        if user_id is not None:
            if user_id in meta["user_assignments"]:
                return meta["user_assignments"][user_id]

            # Deterministic hash-based assignment
            hash_val = int(hashlib.md5(f"{experiment_id}:{user_id}".encode()).hexdigest(), 16)
            variant = self._select_variant_by_weight(
                meta["variants"],
                meta["traffic_split"],
                hash_val / (2**128)  # Normalize to 0-1
            )
            meta["user_assignments"][user_id] = variant
            return variant

        # Random assignment based on traffic split
        return self._select_variant_by_weight(
            meta["variants"],
            meta["traffic_split"],
            random.random()
        )

    def _select_variant_by_weight(
        self,
        variants: List[str],
        weights: List[float],
        rand_val: float
    ) -> str:
        """Select variant based on cumulative weights"""
        cumulative = 0.0
        for variant, weight in zip(variants, weights):
            cumulative += weight
            if rand_val < cumulative:
                return variant
        return variants[-1]  # Fallback to last

    def record_outcome(
        self,
        experiment_id: str,
        variant: str,
        success: bool,
        quality_score: Optional[float] = None,
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Record outcome for a variant.

        Args:
            experiment_id: Experiment ID
            variant: Variant name
            success: Whether the interaction was successful
            quality_score: Optional quality score (0-1)
            metadata: Optional additional metadata
        """
        if experiment_id not in self._experiments:
            raise ValueError(f"Experiment {experiment_id} not found")

        meta = self._experiments[experiment_id]

        if variant not in meta["variants"]:
            raise ValueError(f"Invalid variant '{variant}' for experiment")

        # Record in OutcomeTracker
        from claude.tools.orchestration.outcome_tracker import Outcome
        outcome = Outcome(
            domain=f"ab_test:{experiment_id}",
            approach=variant,
            success=success,
            quality_score=quality_score,
            variant_id=variant,
            metadata=metadata
        )
        self.outcome_tracker.record_outcome(outcome)

        # Check for auto-conclude
        if meta["auto_conclude"] and meta["status"] == ExperimentStatus.ACTIVE:
            results = self.get_results(experiment_id)
            if results.is_significant and results.winner:
                self.conclude_experiment(experiment_id, results.winner, "Auto-concluded")

    def get_results(self, experiment_id: str) -> ABResults:
        """
        Get experiment results with statistical analysis.

        Args:
            experiment_id: Experiment ID

        Returns:
            ABResults with stats and significance
        """
        if experiment_id not in self._experiments:
            raise ValueError(f"Experiment {experiment_id} not found")

        meta = self._experiments[experiment_id]

        # Get outcomes for this experiment
        outcomes = self.outcome_tracker.query_outcomes(
            domain=f"ab_test:{experiment_id}",
            limit=10000
        )

        # Calculate per-variant stats
        variant_stats: Dict[str, VariantStats] = {}
        for variant in meta["variants"]:
            variant_outcomes = [o for o in outcomes if o.approach == variant]
            total = len(variant_outcomes)
            successes = sum(1 for o in variant_outcomes if o.success)
            qualities = [o.quality_score for o in variant_outcomes if o.quality_score is not None]

            variant_stats[variant] = VariantStats(
                variant=variant,
                total_count=total,
                success_count=successes,
                success_rate=successes / total if total > 0 else 0.0,
                avg_quality=sum(qualities) / len(qualities) if qualities else None
            )

        # Check minimum samples
        min_samples = meta["min_samples"]
        has_enough_samples = all(
            vs.total_count >= min_samples for vs in variant_stats.values()
        )

        if not has_enough_samples:
            return ABResults(
                experiment_id=experiment_id,
                name=meta["name"],
                status=meta["status"],
                variant_stats=variant_stats,
                is_significant=False,
                confidence=0.0,
                message="Insufficient samples for significance test"
            )

        # Chi-squared test for independence
        is_significant, confidence, winner = self._calculate_significance(
            variant_stats,
            meta["significance_threshold"]
        )

        # Check for underperforming variants (early stopping)
        underperforming = []
        if meta["early_stopping"]:
            underperforming = self._find_underperforming(
                variant_stats,
                meta["early_stop_threshold"]
            )

        return ABResults(
            experiment_id=experiment_id,
            name=meta["name"],
            status=meta["status"],
            variant_stats=variant_stats,
            is_significant=is_significant,
            confidence=confidence,
            winner=winner,
            message="Statistically significant" if is_significant else "Not yet significant",
            underperforming_variants=underperforming
        )

    def _calculate_significance(
        self,
        variant_stats: Dict[str, VariantStats],
        threshold: float
    ) -> tuple:
        """
        Calculate statistical significance using chi-squared test.

        Returns:
            (is_significant, confidence, winner)
        """
        if len(variant_stats) < 2:
            return False, 0.0, None

        # Build contingency table
        # Rows: success, failure
        # Cols: variants
        observed = []
        variants = list(variant_stats.keys())

        for variant in variants:
            vs = variant_stats[variant]
            observed.append([vs.success_count, vs.total_count - vs.success_count])

        # Transpose for scipy (needs [successes...], [failures...])
        observed_t = list(zip(*observed))

        try:
            chi2, p_value, dof, expected = stats.chi2_contingency(observed_t)
            confidence = float(1 - p_value)  # Cast to Python float

            is_significant = bool(confidence >= threshold)  # Cast to Python bool

            # Determine winner (highest success rate)
            winner = None
            if is_significant:
                best = max(variant_stats.values(), key=lambda x: x.success_rate)
                winner = best.variant

            return is_significant, confidence, winner

        except Exception as e:
            logger.warning(f"Significance calculation failed: {e}")
            return False, 0.0, None

    def _find_underperforming(
        self,
        variant_stats: Dict[str, VariantStats],
        threshold: float
    ) -> List[str]:
        """Find variants that are clearly underperforming"""
        if len(variant_stats) < 2:
            return []

        # Find best performer
        best = max(variant_stats.values(), key=lambda x: x.success_rate)

        underperforming = []
        for variant, vs in variant_stats.items():
            if variant == best.variant:
                continue

            # Simple heuristic: if success rate is much lower with enough samples
            if vs.total_count >= 30 and best.total_count >= 30:
                if vs.success_rate < best.success_rate * 0.5:  # Less than half
                    underperforming.append(variant)

        return underperforming

    def conclude_experiment(
        self,
        experiment_id: str,
        winner: str,
        reason: Optional[str] = None
    ) -> None:
        """Conclude experiment and declare winner"""
        if experiment_id not in self._experiments:
            raise ValueError(f"Experiment {experiment_id} not found")

        meta = self._experiments[experiment_id]
        meta["status"] = ExperimentStatus.CONCLUDED
        meta["winner"] = winner

        # Update in OutcomeTracker
        self.outcome_tracker.end_experiment(experiment_id, winner)

    def pause_experiment(self, experiment_id: str) -> None:
        """Pause experiment (routes to control)"""
        if experiment_id not in self._experiments:
            raise ValueError(f"Experiment {experiment_id} not found")

        self._experiments[experiment_id]["status"] = ExperimentStatus.PAUSED

    def resume_experiment(self, experiment_id: str) -> None:
        """Resume paused experiment"""
        if experiment_id not in self._experiments:
            raise ValueError(f"Experiment {experiment_id} not found")

        self._experiments[experiment_id]["status"] = ExperimentStatus.ACTIVE

    def list_experiments(
        self,
        status: Optional[ExperimentStatus] = None
    ) -> List[ExperimentInfo]:
        """List all experiments, optionally filtered by status"""
        results = []
        for exp_id, meta in self._experiments.items():
            if status is not None and meta["status"] != status:
                continue

            results.append(ExperimentInfo(
                id=exp_id,
                name=meta["name"],
                variants=meta["variants"],
                status=meta["status"],
                created_at=meta["created_at"],
                winner=meta["winner"],
                traffic_split=meta["traffic_split"]
            ))

        return results


if __name__ == "__main__":
    # Demo
    ab = ABTestingFramework()

    exp_id = ab.create_experiment(
        name="search_comparison",
        variants=["rag", "keyword"],
        auto_conclude=True
    )

    print(f"Created experiment: {exp_id}")

    # Simulate outcomes
    for i in range(100):
        # RAG: 80% success
        ab.record_outcome(exp_id, "rag", success=random.random() < 0.8)
        # Keyword: 60% success
        ab.record_outcome(exp_id, "keyword", success=random.random() < 0.6)

    results = ab.get_results(exp_id)
    print(f"Significant: {results.is_significant}")
    print(f"Confidence: {results.confidence:.2%}")
    print(f"Winner: {results.winner}")
