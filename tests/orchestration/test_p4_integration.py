#!/usr/bin/env python3
"""
Integration Tests for P4→P1-P3 Pattern Integration - Phase 184

Tests the actual wiring between P4 patterns (OutcomeTracker) and
P1-P3 patterns (AdaptiveRouting, ContinuousEval).

Author: Maia System (SRE Principal Engineer Agent)
Created: 2025-11-24 (Agentic AI Enhancement Project - Phase 4)
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime


class TestAdaptiveRoutingWithOutcomeTracker:
    """Test AdaptiveRouting → OutcomeTracker integration"""

    @pytest.fixture
    def setup_with_tracker(self, tmp_path):
        """Create AdaptiveRoutingSystem with OutcomeTracker"""
        from claude.tools.orchestration.outcome_tracker import OutcomeTracker
        from claude.tools.orchestration.adaptive_routing import AdaptiveRoutingSystem

        tracker_db = tmp_path / "tracker.db"
        routing_db = tmp_path / "routing.db"

        tracker = OutcomeTracker(db_path=str(tracker_db))
        routing = AdaptiveRoutingSystem(
            db_path=str(routing_db),
            outcome_tracker=tracker
        )

        return routing, tracker

    def test_outcome_tracker_receives_routing_outcomes(self, setup_with_tracker):
        """AdaptiveRouting should forward outcomes to OutcomeTracker"""
        routing, tracker = setup_with_tracker

        from claude.tools.orchestration.adaptive_routing import TaskOutcome

        # Record outcome via AdaptiveRouting
        outcome = TaskOutcome(
            task_id="test-task-001",
            timestamp=datetime.now(),
            query="test email query",
            domain="email",
            complexity=3,
            agent_used="email_agent",
            agent_loaded=True,
            success=True,
            quality_score=0.9,
            user_corrections=0
        )

        routing.record_outcome(outcome)

        # Verify it appears in OutcomeTracker
        outcomes = tracker.query_outcomes(domain="email")
        assert len(outcomes) >= 1

        # Find our outcome
        our_outcome = next((o for o in outcomes if "test-task-001" in str(o.id)), None)
        assert our_outcome is not None
        assert our_outcome.success is True
        assert our_outcome.quality_score == 0.9

    def test_outcome_tracker_records_complexity_as_approach(self, setup_with_tracker):
        """Complexity level should be recorded as approach"""
        routing, tracker = setup_with_tracker

        from claude.tools.orchestration.adaptive_routing import TaskOutcome

        # Record with complexity 5
        outcome = TaskOutcome(
            task_id="complexity-test-001",
            timestamp=datetime.now(),
            query="test calendar query",
            domain="calendar",
            complexity=5,
            agent_used="calendar_agent",
            agent_loaded=True,
            success=True,
            quality_score=0.85,
            user_corrections=0
        )

        routing.record_outcome(outcome)

        # Verify approach is recorded
        outcomes = tracker.query_outcomes(domain="calendar")
        our_outcome = next((o for o in outcomes if "complexity-test-001" in str(o.id)), None)
        assert our_outcome is not None
        assert "complexity_5" in our_outcome.approach

    def test_multiple_outcomes_tracked_correctly(self, setup_with_tracker):
        """Multiple outcomes should all be tracked"""
        routing, tracker = setup_with_tracker

        from claude.tools.orchestration.adaptive_routing import TaskOutcome

        # Record 5 outcomes
        for i in range(5):
            outcome = TaskOutcome(
                task_id=f"multi-test-{i:03d}",
                timestamp=datetime.now(),
                query=f"research query {i}",
                domain="research",
                complexity=i + 1,
                agent_used="research_agent",
                agent_loaded=True,
                success=i % 2 == 0,  # Alternating success/failure
                quality_score=0.7 + (i * 0.05),
                user_corrections=0
            )
            routing.record_outcome(outcome)

        # Verify all tracked
        outcomes = tracker.query_outcomes(domain="research")
        assert len(outcomes) >= 5

        # Verify success rate calculation
        success_rate = tracker.get_success_rate(domain="research")
        assert 0.5 <= success_rate <= 0.7  # 3/5 = 0.6

    def test_routing_still_works_without_tracker(self, tmp_path):
        """AdaptiveRouting should work when no OutcomeTracker provided"""
        from claude.tools.orchestration.adaptive_routing import (
            AdaptiveRoutingSystem, TaskOutcome
        )

        routing_db = tmp_path / "routing_only.db"
        routing = AdaptiveRoutingSystem(db_path=str(routing_db))

        # This should not raise an error
        outcome = TaskOutcome(
            task_id="no-tracker-test",
            timestamp=datetime.now(),
            query="test query",
            domain="test",
            complexity=1,
            agent_used="test_agent",
            agent_loaded=False,
            success=True,
            quality_score=0.8,
            user_corrections=0
        )

        routing.record_outcome(outcome)

        # Verify internal tracking still works
        stats = routing.get_domain_stats("test")
        assert stats is not None


class TestContinuousEvalWithOutcomeTracker:
    """Test ContinuousEval → OutcomeTracker integration"""

    @pytest.fixture
    def setup_with_tracker(self, tmp_path):
        """Create ContinuousEvaluationSystem with OutcomeTracker"""
        from claude.tools.orchestration.outcome_tracker import OutcomeTracker
        from claude.tools.orchestration.continuous_eval import ContinuousEvaluationSystem

        tracker_db = tmp_path / "tracker.db"
        eval_db = tmp_path / "eval.db"

        tracker = OutcomeTracker(db_path=str(tracker_db))
        eval_system = ContinuousEvaluationSystem(
            db_path=str(eval_db),
            outcome_tracker=tracker
        )

        return eval_system, tracker

    def test_outcome_tracker_receives_eval_outcomes(self, setup_with_tracker):
        """ContinuousEval should forward outcomes to OutcomeTracker"""
        eval_system, tracker = setup_with_tracker

        from claude.tools.orchestration.continuous_eval import EvaluationRecord

        # Record evaluation via ContinuousEval
        record = EvaluationRecord(
            task_id="eval-test-001",
            timestamp=datetime.now(),
            agent_used="email_agent",
            query="test email query",
            domain="email",
            complexity=3,
            output_quality=0.88,
            task_completed=True,
            user_rating=None,
            auto_score=0.85
        )

        eval_system.record_evaluation(record)

        # Verify it appears in OutcomeTracker
        outcomes = tracker.query_outcomes(domain="email")
        assert len(outcomes) >= 1

        # Find our outcome
        our_outcome = next((o for o in outcomes if "eval-test-001" in str(o.id)), None)
        assert our_outcome is not None
        assert our_outcome.success is True  # task_completed=True
        assert our_outcome.quality_score == 0.88

    def test_failed_task_recorded_correctly(self, setup_with_tracker):
        """Failed tasks should have success=False"""
        eval_system, tracker = setup_with_tracker

        from claude.tools.orchestration.continuous_eval import EvaluationRecord

        record = EvaluationRecord(
            task_id="failed-eval-001",
            timestamp=datetime.now(),
            agent_used="calendar_agent",
            query="test calendar query",
            domain="calendar",
            complexity=2,
            output_quality=0.3,
            task_completed=False,
            user_rating=None,
            auto_score=0.2
        )

        eval_system.record_evaluation(record)

        outcomes = tracker.query_outcomes(domain="calendar")
        our_outcome = next((o for o in outcomes if "failed-eval-001" in str(o.id)), None)
        assert our_outcome is not None
        assert our_outcome.success is False

    def test_eval_still_works_without_tracker(self, tmp_path):
        """ContinuousEval should work when no OutcomeTracker provided"""
        from claude.tools.orchestration.continuous_eval import (
            ContinuousEvaluationSystem, EvaluationRecord
        )

        eval_db = tmp_path / "eval_only.db"
        eval_system = ContinuousEvaluationSystem(db_path=str(eval_db))

        # This should not raise an error
        record = EvaluationRecord(
            task_id="no-tracker-eval",
            timestamp=datetime.now(),
            agent_used="test_agent",
            query="test query",
            domain="test",
            complexity=1,
            output_quality=0.8,
            task_completed=True,
            user_rating=None,
            auto_score=0.75
        )

        eval_system.record_evaluation(record)

        # Verify internal tracking still works
        evals = eval_system.get_recent_evaluations(limit=10)
        assert len(evals) >= 1


class TestUnifiedOutcomeStorage:
    """Test unified outcome storage across both systems"""

    @pytest.fixture
    def setup_unified(self, tmp_path):
        """Create both systems sharing same OutcomeTracker"""
        from claude.tools.orchestration.outcome_tracker import OutcomeTracker
        from claude.tools.orchestration.adaptive_routing import AdaptiveRoutingSystem
        from claude.tools.orchestration.continuous_eval import ContinuousEvaluationSystem

        tracker_db = tmp_path / "unified_tracker.db"
        routing_db = tmp_path / "routing.db"
        eval_db = tmp_path / "eval.db"

        # Shared tracker
        tracker = OutcomeTracker(db_path=str(tracker_db))

        routing = AdaptiveRoutingSystem(
            db_path=str(routing_db),
            outcome_tracker=tracker
        )

        eval_system = ContinuousEvaluationSystem(
            db_path=str(eval_db),
            outcome_tracker=tracker
        )

        return routing, eval_system, tracker

    def test_both_systems_write_to_same_tracker(self, setup_unified):
        """Both AdaptiveRouting and ContinuousEval should write to same tracker"""
        routing, eval_system, tracker = setup_unified

        from claude.tools.orchestration.adaptive_routing import TaskOutcome
        from claude.tools.orchestration.continuous_eval import EvaluationRecord

        # Record via routing
        routing.record_outcome(TaskOutcome(
            task_id="routing-unified-001",
            timestamp=datetime.now(),
            query="unified test query",
            domain="unified",
            complexity=3,
            agent_used="test_agent",
            agent_loaded=True,
            success=True,
            quality_score=0.9,
            user_corrections=0
        ))

        # Record via eval
        eval_system.record_evaluation(EvaluationRecord(
            task_id="eval-unified-001",
            timestamp=datetime.now(),
            agent_used="test_agent",
            query="unified eval query",
            domain="unified",
            complexity=2,
            output_quality=0.85,
            task_completed=True,
            user_rating=None,
            auto_score=0.8
        ))

        # Both should be in unified tracker
        outcomes = tracker.query_outcomes(domain="unified")
        assert len(outcomes) >= 2

        # Verify both sources present
        ids = [str(o.id) for o in outcomes]
        assert any("routing-unified" in id_ for id_ in ids)
        assert any("eval-unified" in id_ for id_ in ids)

    def test_cross_system_analytics(self, setup_unified):
        """Should be able to analyze across both systems"""
        routing, eval_system, tracker = setup_unified

        from claude.tools.orchestration.adaptive_routing import TaskOutcome
        from claude.tools.orchestration.continuous_eval import EvaluationRecord

        # Mix of outcomes from both systems
        for i in range(10):
            if i % 2 == 0:
                routing.record_outcome(TaskOutcome(
                    task_id=f"cross-routing-{i:03d}",
                    timestamp=datetime.now(),
                    query=f"routing query {i}",
                    domain="cross_test",
                    complexity=3,
                    agent_used="agent_a",
                    agent_loaded=True,
                    success=True,
                    quality_score=0.9,
                    user_corrections=0
                ))
            else:
                eval_system.record_evaluation(EvaluationRecord(
                    task_id=f"cross-eval-{i:03d}",
                    timestamp=datetime.now(),
                    agent_used="agent_a",
                    query=f"eval query {i}",
                    domain="cross_test",
                    complexity=2,
                    output_quality=0.8,
                    task_completed=True,
                    user_rating=None,
                    auto_score=0.75
                ))

        # Unified success rate
        success_rate = tracker.get_success_rate(domain="cross_test")
        assert success_rate == 1.0  # All succeeded

    def test_unified_experiment_tracking(self, setup_unified):
        """Should track experiments across both sources"""
        routing, eval_system, tracker = setup_unified

        from claude.tools.orchestration.outcome_tracker import Experiment
        from claude.tools.orchestration.adaptive_routing import TaskOutcome
        from claude.tools.orchestration.continuous_eval import EvaluationRecord

        # Create experiment
        exp = Experiment(
            name="unified_experiment",
            variants=["control", "treatment"],
            description="Test across both systems"
        )
        exp_id = tracker.create_experiment(exp)

        # Record outcomes from both systems
        routing.record_outcome(TaskOutcome(
            task_id="exp-routing-001",
            timestamp=datetime.now(),
            query="experiment routing query",
            domain=f"ab_test:{exp_id}",
            complexity=3,
            agent_used="test_agent",
            agent_loaded=True,
            success=True,
            quality_score=0.9,
            user_corrections=0
        ))

        # Verify experiment tracking works
        results = tracker.get_experiment_results(exp_id)
        assert results is not None


class TestSpeculativeExecutorWithOutcomeTracker:
    """Test SpeculativeExecutor → OutcomeTracker integration"""

    @pytest.fixture
    def setup_with_tracker(self, tmp_path):
        """Create SpeculativeExecutor with OutcomeTracker"""
        from claude.tools.orchestration.outcome_tracker import OutcomeTracker
        from claude.tools.orchestration.speculative_executor import SpeculativeExecutor

        tracker_db = tmp_path / "tracker.db"
        tracker = OutcomeTracker(db_path=str(tracker_db))
        executor = SpeculativeExecutor(outcome_tracker=tracker)

        return executor, tracker

    def test_executor_records_outcomes(self, setup_with_tracker):
        """SpeculativeExecutor should record outcomes to OutcomeTracker"""
        import time
        executor, tracker = setup_with_tracker

        from claude.tools.orchestration.speculative_executor import Approach

        def fast_approach(x):
            time.sleep(0.01)
            return f"fast_{x}"

        approaches = [
            Approach(name="fast", callable=fast_approach)
        ]

        result = executor.execute(
            approaches,
            input_data="test",
            domain="speculative_test"
        )

        assert result.success is True

        # Verify tracked
        outcomes = tracker.query_outcomes(domain="speculative_test")
        assert len(outcomes) >= 1
        assert any(o.approach == "fast" for o in outcomes)


class TestABTestingWithOutcomeTracker:
    """Test ABTestingFramework → OutcomeTracker integration"""

    @pytest.fixture
    def setup_with_tracker(self, tmp_path):
        """Create ABTestingFramework with OutcomeTracker"""
        from claude.tools.orchestration.outcome_tracker import OutcomeTracker
        from claude.tools.orchestration.ab_testing import ABTestingFramework

        tracker_db = tmp_path / "tracker.db"
        tracker = OutcomeTracker(db_path=str(tracker_db))
        ab = ABTestingFramework(outcome_tracker=tracker)

        return ab, tracker

    def test_ab_records_via_tracker(self, setup_with_tracker):
        """ABTestingFramework should use OutcomeTracker for storage"""
        ab, tracker = setup_with_tracker

        exp_id = ab.create_experiment(
            name="ab_integration_test",
            variants=["a", "b"]
        )

        ab.record_outcome(exp_id, variant="a", success=True)
        ab.record_outcome(exp_id, variant="b", success=False)

        # Both should be in tracker
        outcomes = tracker.query_outcomes(domain=f"ab_test:{exp_id}")
        assert len(outcomes) >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
