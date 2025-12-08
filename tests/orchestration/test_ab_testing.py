#!/usr/bin/env python3
"""
Test Suite for A/B Testing Framework - Phase 183

TDD: Tests written FIRST before implementation.
Implements A/B testing with statistical significance.

Author: Maia System (SRE Principal Engineer Agent)
Created: 2025-11-24 (Agentic AI Enhancement Project - Phase 4)
"""

import pytest
import random
from datetime import datetime
from typing import Dict
from unittest.mock import MagicMock, patch
import tempfile
from pathlib import Path

# Import will fail until implementation exists - this is expected in TDD
try:
    from claude.tools.orchestration.ab_testing import (
        ABTestingFramework,
        ExperimentConfig,
        ExperimentStatus,
        ABResults,
        TrafficSplitStrategy,
    )
    IMPLEMENTATION_EXISTS = True
except ImportError:
    IMPLEMENTATION_EXISTS = False
    ABTestingFramework = None
    ExperimentConfig = None
    ExperimentStatus = None
    ABResults = None
    TrafficSplitStrategy = None


pytestmark = pytest.mark.skipif(
    not IMPLEMENTATION_EXISTS,
    reason="Implementation not yet created (TDD red phase)"
)


class TestABTestingSetup:
    """Test initialization"""

    @pytest.fixture
    def tracker(self, tmp_path):
        from claude.tools.orchestration.outcome_tracker import OutcomeTracker
        db_path = tmp_path / "test.db"
        return OutcomeTracker(db_path=str(db_path))

    def test_init_with_tracker(self, tracker):
        """Framework should initialize with OutcomeTracker"""
        ab = ABTestingFramework(outcome_tracker=tracker)
        assert ab.outcome_tracker is not None

    def test_init_creates_own_tracker(self, tmp_path):
        """Framework should create tracker if not provided"""
        ab = ABTestingFramework(db_path=str(tmp_path / "ab.db"))
        assert ab.outcome_tracker is not None


class TestExperimentCreation:
    """FR1: Create experiments with named variants"""

    @pytest.fixture
    def ab(self, tmp_path):
        from claude.tools.orchestration.outcome_tracker import OutcomeTracker
        tracker = OutcomeTracker(db_path=str(tmp_path / "test.db"))
        return ABTestingFramework(outcome_tracker=tracker)

    def test_create_experiment_basic(self, ab):
        """Create experiment with two variants"""
        exp_id = ab.create_experiment(
            name="search_test",
            variants=["rag", "keyword"]
        )

        assert exp_id is not None
        assert len(exp_id) > 0

    def test_create_experiment_with_config(self, ab):
        """Create experiment with full configuration"""
        config = ExperimentConfig(
            name="search_test",
            variants=["rag", "keyword", "hybrid"],
            description="Compare search approaches",
            traffic_split=[0.4, 0.4, 0.2],  # 40/40/20 split
            min_samples_per_variant=100,
            significance_threshold=0.95
        )

        exp_id = ab.create_experiment_from_config(config)
        assert exp_id is not None

    def test_create_experiment_validates_variants(self, ab):
        """Should require at least 2 variants"""
        with pytest.raises(ValueError, match="variant"):
            ab.create_experiment(name="invalid", variants=["only_one"])

    def test_create_experiment_validates_traffic_split(self, ab):
        """Traffic split must sum to 1.0"""
        with pytest.raises(ValueError, match="traffic"):
            ab.create_experiment(
                name="invalid",
                variants=["a", "b"],
                traffic_split=[0.3, 0.3]  # Sums to 0.6, not 1.0
            )

    def test_get_experiment_status(self, ab):
        """Should retrieve experiment status"""
        exp_id = ab.create_experiment(name="test", variants=["a", "b"])

        status = ab.get_experiment(exp_id)

        assert status is not None
        assert status.name == "test"
        assert status.status == ExperimentStatus.ACTIVE
        assert set(status.variants) == {"a", "b"}


class TestTrafficRouting:
    """FR2: Route traffic to variants"""

    @pytest.fixture
    def ab(self, tmp_path):
        from claude.tools.orchestration.outcome_tracker import OutcomeTracker
        tracker = OutcomeTracker(db_path=str(tmp_path / "test.db"))
        return ABTestingFramework(outcome_tracker=tracker)

    def test_get_variant_returns_valid_variant(self, ab):
        """get_variant should return one of the experiment variants"""
        exp_id = ab.create_experiment(name="test", variants=["a", "b", "c"])

        for _ in range(10):
            variant = ab.get_variant(exp_id)
            assert variant in ["a", "b", "c"]

    def test_get_variant_random_distribution(self, ab):
        """Random split should distribute roughly evenly"""
        exp_id = ab.create_experiment(
            name="test",
            variants=["a", "b"],
            strategy=TrafficSplitStrategy.RANDOM
        )

        counts = {"a": 0, "b": 0}
        for _ in range(1000):
            variant = ab.get_variant(exp_id)
            counts[variant] += 1

        # Should be roughly 50/50 (within 10% tolerance)
        assert 400 < counts["a"] < 600
        assert 400 < counts["b"] < 600

    def test_get_variant_weighted_distribution(self, ab):
        """Weighted split should respect traffic_split"""
        exp_id = ab.create_experiment(
            name="test",
            variants=["a", "b"],
            traffic_split=[0.8, 0.2]  # 80/20 split
        )

        counts = {"a": 0, "b": 0}
        for _ in range(1000):
            variant = ab.get_variant(exp_id)
            counts[variant] += 1

        # A should get ~80%, B should get ~20%
        assert 700 < counts["a"] < 900
        assert 100 < counts["b"] < 300

    def test_get_variant_sticky_by_user(self, ab):
        """Same user_id should get same variant (sticky assignment)"""
        exp_id = ab.create_experiment(name="test", variants=["a", "b"])

        # Same user should always get same variant
        first_variant = ab.get_variant(exp_id, user_id="user123")
        for _ in range(10):
            assert ab.get_variant(exp_id, user_id="user123") == first_variant

    def test_get_variant_different_users_get_different(self, ab):
        """Different users should potentially get different variants"""
        exp_id = ab.create_experiment(name="test", variants=["a", "b"])

        variants_seen = set()
        for i in range(100):
            variant = ab.get_variant(exp_id, user_id=f"user_{i}")
            variants_seen.add(variant)

        # Should see both variants across different users
        assert len(variants_seen) == 2


class TestOutcomeTracking:
    """FR3: Track outcomes per variant"""

    @pytest.fixture
    def ab(self, tmp_path):
        from claude.tools.orchestration.outcome_tracker import OutcomeTracker
        tracker = OutcomeTracker(db_path=str(tmp_path / "test.db"))
        return ABTestingFramework(outcome_tracker=tracker)

    def test_record_outcome_success(self, ab):
        """Record successful outcome for variant"""
        exp_id = ab.create_experiment(name="test", variants=["a", "b"])

        ab.record_outcome(exp_id, variant="a", success=True)
        ab.record_outcome(exp_id, variant="a", success=True)
        ab.record_outcome(exp_id, variant="b", success=False)

        results = ab.get_results(exp_id)
        assert results.variant_stats["a"].success_count == 2
        assert results.variant_stats["b"].success_count == 0

    def test_record_outcome_with_quality(self, ab):
        """Record outcome with quality score"""
        exp_id = ab.create_experiment(name="test", variants=["a", "b"])

        ab.record_outcome(exp_id, variant="a", success=True, quality_score=0.9)
        ab.record_outcome(exp_id, variant="a", success=True, quality_score=0.8)

        results = ab.get_results(exp_id)
        assert results.variant_stats["a"].avg_quality == pytest.approx(0.85, 0.01)

    def test_record_outcome_validates_variant(self, ab):
        """Should reject outcomes for invalid variants"""
        exp_id = ab.create_experiment(name="test", variants=["a", "b"])

        with pytest.raises(ValueError, match="variant"):
            ab.record_outcome(exp_id, variant="c", success=True)


class TestStatisticalSignificance:
    """FR4: Calculate statistical significance"""

    @pytest.fixture
    def ab(self, tmp_path):
        from claude.tools.orchestration.outcome_tracker import OutcomeTracker
        tracker = OutcomeTracker(db_path=str(tmp_path / "test.db"))
        return ABTestingFramework(outcome_tracker=tracker)

    def test_significance_with_clear_winner(self, ab):
        """Should detect significant difference with clear winner"""
        exp_id = ab.create_experiment(name="test", variants=["a", "b"])

        # A: 90% success rate (90/100)
        for i in range(100):
            ab.record_outcome(exp_id, variant="a", success=i < 90)

        # B: 50% success rate (50/100)
        for i in range(100):
            ab.record_outcome(exp_id, variant="b", success=i < 50)

        results = ab.get_results(exp_id)

        assert results.is_significant is True
        assert results.confidence >= 0.95
        assert results.winner == "a"

    def test_significance_with_no_clear_winner(self, ab):
        """Should not declare winner when difference is small"""
        exp_id = ab.create_experiment(name="test", variants=["a", "b"])

        # A: 51% success rate
        for i in range(100):
            ab.record_outcome(exp_id, variant="a", success=i < 51)

        # B: 49% success rate
        for i in range(100):
            ab.record_outcome(exp_id, variant="b", success=i < 49)

        results = ab.get_results(exp_id)

        # Not enough difference to be significant
        assert results.is_significant is False or results.confidence < 0.95

    def test_significance_insufficient_data(self, ab):
        """Should not declare significance with too few samples"""
        exp_id = ab.create_experiment(
            name="test",
            variants=["a", "b"],
            min_samples_per_variant=50
        )

        # Only 10 samples each
        for i in range(10):
            ab.record_outcome(exp_id, variant="a", success=True)
            ab.record_outcome(exp_id, variant="b", success=False)

        results = ab.get_results(exp_id)

        assert results.is_significant is False
        assert "insufficient" in results.message.lower()


class TestWinnerDeclaration:
    """FR5: Auto-declare winner"""

    @pytest.fixture
    def ab(self, tmp_path):
        from claude.tools.orchestration.outcome_tracker import OutcomeTracker
        tracker = OutcomeTracker(db_path=str(tmp_path / "test.db"))
        return ABTestingFramework(outcome_tracker=tracker)

    def test_auto_declare_winner(self, ab):
        """Should auto-declare winner when significance reached"""
        exp_id = ab.create_experiment(
            name="test",
            variants=["a", "b"],
            auto_conclude=True,
            significance_threshold=0.95
        )

        # Clear winner: A at 90%, B at 10%
        for i in range(200):
            ab.record_outcome(exp_id, variant="a", success=i < 180)
            ab.record_outcome(exp_id, variant="b", success=i < 20)

        status = ab.get_experiment(exp_id)

        assert status.status == ExperimentStatus.CONCLUDED
        assert status.winner == "a"

    def test_manual_conclude_experiment(self, ab):
        """Should allow manual conclusion"""
        exp_id = ab.create_experiment(name="test", variants=["a", "b"])

        ab.conclude_experiment(exp_id, winner="a", reason="Manual decision")

        status = ab.get_experiment(exp_id)
        assert status.status == ExperimentStatus.CONCLUDED
        assert status.winner == "a"

    def test_pause_experiment(self, ab):
        """Should allow pausing experiment"""
        exp_id = ab.create_experiment(name="test", variants=["a", "b"])

        ab.pause_experiment(exp_id)

        status = ab.get_experiment(exp_id)
        assert status.status == ExperimentStatus.PAUSED

        # get_variant should return control/first variant when paused
        variant = ab.get_variant(exp_id)
        assert variant == "a"  # First variant as fallback


class TestEarlyStopping:
    """FR6: Early stopping for clear winners/losers"""

    @pytest.fixture
    def ab(self, tmp_path):
        from claude.tools.orchestration.outcome_tracker import OutcomeTracker
        tracker = OutcomeTracker(db_path=str(tmp_path / "test.db"))
        return ABTestingFramework(outcome_tracker=tracker)

    def test_early_stop_clear_loser(self, ab):
        """Should stop early if variant is clearly losing"""
        exp_id = ab.create_experiment(
            name="test",
            variants=["a", "b"],
            early_stopping=True,
            early_stop_threshold=0.01  # Stop if <1% chance of catching up
        )

        # B is clearly losing: 0% vs 100%
        for _ in range(50):
            ab.record_outcome(exp_id, variant="a", success=True)
            ab.record_outcome(exp_id, variant="b", success=False)

        results = ab.get_results(exp_id)

        # Should recommend stopping B
        assert "b" in results.underperforming_variants


class TestResultsReporting:
    """Test results and reporting"""

    @pytest.fixture
    def ab(self, tmp_path):
        from claude.tools.orchestration.outcome_tracker import OutcomeTracker
        tracker = OutcomeTracker(db_path=str(tmp_path / "test.db"))
        return ABTestingFramework(outcome_tracker=tracker)

    def test_results_contain_all_stats(self, ab):
        """Results should contain comprehensive statistics"""
        exp_id = ab.create_experiment(name="test", variants=["a", "b"])

        for i in range(50):
            ab.record_outcome(exp_id, variant="a", success=i < 40, quality_score=0.8)
            ab.record_outcome(exp_id, variant="b", success=i < 30, quality_score=0.7)

        results = ab.get_results(exp_id)

        assert "a" in results.variant_stats
        assert "b" in results.variant_stats

        stats_a = results.variant_stats["a"]
        assert stats_a.total_count == 50
        assert stats_a.success_count == 40
        assert stats_a.success_rate == pytest.approx(0.8, 0.01)
        assert stats_a.avg_quality is not None

    def test_list_experiments(self, ab):
        """Should list all experiments"""
        ab.create_experiment(name="exp1", variants=["a", "b"])
        ab.create_experiment(name="exp2", variants=["x", "y"])

        experiments = ab.list_experiments()

        assert len(experiments) >= 2
        names = [e.name for e in experiments]
        assert "exp1" in names
        assert "exp2" in names

    def test_list_experiments_filter_by_status(self, ab):
        """Should filter experiments by status"""
        exp1 = ab.create_experiment(name="active1", variants=["a", "b"])
        exp2 = ab.create_experiment(name="active2", variants=["a", "b"])
        ab.conclude_experiment(exp2, winner="a")

        active = ab.list_experiments(status=ExperimentStatus.ACTIVE)
        concluded = ab.list_experiments(status=ExperimentStatus.CONCLUDED)

        assert len(active) >= 1
        assert len(concluded) >= 1
        assert all(e.status == ExperimentStatus.ACTIVE for e in active)
        assert all(e.status == ExperimentStatus.CONCLUDED for e in concluded)


class TestIntegration:
    """Integration with other components"""

    @pytest.fixture
    def ab(self, tmp_path):
        from claude.tools.orchestration.outcome_tracker import OutcomeTracker
        tracker = OutcomeTracker(db_path=str(tmp_path / "test.db"))
        return ABTestingFramework(outcome_tracker=tracker)

    def test_works_with_speculative_executor(self, ab, tmp_path):
        """Should integrate with SpeculativeExecutor"""
        from claude.tools.orchestration.speculative_executor import (
            SpeculativeExecutor, Approach
        )

        exp_id = ab.create_experiment(name="search_test", variants=["fast", "slow"])

        def run_with_ab(input_data):
            variant = ab.get_variant(exp_id)

            # Simulate different approaches
            if variant == "fast":
                result = f"fast_result_{input_data}"
                ab.record_outcome(exp_id, variant, success=True, quality_score=0.9)
            else:
                result = f"slow_result_{input_data}"
                ab.record_outcome(exp_id, variant, success=True, quality_score=0.7)

            return result

        # Run multiple times
        for i in range(20):
            run_with_ab(f"test_{i}")

        results = ab.get_results(exp_id)
        assert results.variant_stats["fast"].avg_quality > results.variant_stats["slow"].avg_quality


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
