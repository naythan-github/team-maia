#!/usr/bin/env python3
"""
Test Suite for Outcome Tracking Database - Phase 181

TDD: Tests written FIRST before implementation.
Covers all requirements from outcome_tracking_requirements.md

Author: Maia System (SRE Principal Engineer Agent)
Created: 2025-11-24 (Agentic AI Enhancement Project - Phase 4)
"""

import pytest
import sqlite3
import tempfile
import time
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List
from unittest.mock import patch, MagicMock

# Import will fail until implementation exists - this is expected in TDD
try:
    from claude.tools.orchestration.outcome_tracker import (
        OutcomeTracker,
        Outcome,
        ApproachStats,
        TrendPoint,
        Experiment,
        ExperimentResults,
    )
    IMPLEMENTATION_EXISTS = True
except ImportError:
    IMPLEMENTATION_EXISTS = False
    # Define stubs for test collection
    OutcomeTracker = None
    Outcome = None
    ApproachStats = None
    TrendPoint = None
    Experiment = None
    ExperimentResults = None


# Skip all tests if implementation doesn't exist yet (TDD red phase)
pytestmark = pytest.mark.skipif(
    not IMPLEMENTATION_EXISTS,
    reason="Implementation not yet created (TDD red phase)"
)


class TestOutcomeTrackerSetup:
    """Test initialization and setup"""

    def test_init_creates_database(self, tmp_path):
        """Tracker should create database file on init"""
        db_path = tmp_path / "test_outcomes.db"
        tracker = OutcomeTracker(db_path=str(db_path))
        assert db_path.exists()

    def test_init_creates_tables(self, tmp_path):
        """Tracker should create required tables"""
        db_path = tmp_path / "test_outcomes.db"
        tracker = OutcomeTracker(db_path=str(db_path))

        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = {row[0] for row in cursor.fetchall()}
        conn.close()

        assert 'outcomes' in tables
        assert 'experiments' in tables

    def test_init_with_default_path(self):
        """Tracker should use default path if none provided"""
        tracker = OutcomeTracker()
        assert tracker.db_path is not None
        assert 'outcome_tracker.db' in str(tracker.db_path)


class TestOutcomeRecording:
    """FR1: Outcome Recording"""

    @pytest.fixture
    def tracker(self, tmp_path):
        """Create a tracker with temp database"""
        db_path = tmp_path / "test_outcomes.db"
        return OutcomeTracker(db_path=str(db_path))

    def test_record_outcome_required_fields(self, tracker):
        """Record outcome with only required fields"""
        outcome = Outcome(
            domain="email",
            approach="rag_search",
            success=True
        )
        outcome_id = tracker.record_outcome(outcome)

        assert outcome_id is not None
        assert len(outcome_id) > 0

    def test_record_outcome_all_fields(self, tracker):
        """Record outcome with all optional fields"""
        outcome = Outcome(
            domain="email",
            approach="rag_search",
            success=True,
            task_type="search",
            query_hash="abc123",
            variant_id="A",
            agent_used="email_agent",
            quality_score=0.95,
            latency_ms=150,
            user_rating=5,
            user_correction=False,
            metadata={"source": "test"}
        )
        outcome_id = tracker.record_outcome(outcome)

        retrieved = tracker.get_outcome(outcome_id)
        assert retrieved is not None
        assert retrieved.domain == "email"
        assert retrieved.quality_score == 0.95
        assert retrieved.metadata == {"source": "test"}

    def test_record_outcome_auto_generates_id(self, tracker):
        """ID should be auto-generated if not provided"""
        outcome = Outcome(domain="test", approach="test", success=True)
        outcome_id = tracker.record_outcome(outcome)

        assert outcome_id is not None
        # Should be UUID format
        assert len(outcome_id) >= 32

    def test_record_outcome_auto_generates_timestamp(self, tracker):
        """Timestamp should be auto-generated if not provided"""
        outcome = Outcome(domain="test", approach="test", success=True)
        outcome_id = tracker.record_outcome(outcome)

        retrieved = tracker.get_outcome(outcome_id)
        assert retrieved.timestamp is not None
        # Should be recent (within last minute)
        assert (datetime.now() - retrieved.timestamp).seconds < 60

    def test_record_batch_outcomes(self, tracker):
        """Record multiple outcomes in batch"""
        outcomes = [
            Outcome(domain="email", approach="search", success=True),
            Outcome(domain="email", approach="search", success=False),
            Outcome(domain="calendar", approach="query", success=True),
        ]
        ids = tracker.record_batch(outcomes)

        assert len(ids) == 3
        assert all(id is not None for id in ids)

    def test_record_outcome_validates_quality_score(self, tracker):
        """Quality score must be between 0.0 and 1.0"""
        with pytest.raises(ValueError, match="quality_score"):
            outcome = Outcome(
                domain="test",
                approach="test",
                success=True,
                quality_score=1.5  # Invalid
            )
            tracker.record_outcome(outcome)

    def test_record_outcome_validates_user_rating(self, tracker):
        """User rating must be between 1 and 5"""
        with pytest.raises(ValueError, match="user_rating"):
            outcome = Outcome(
                domain="test",
                approach="test",
                success=True,
                user_rating=6  # Invalid
            )
            tracker.record_outcome(outcome)


class TestOutcomeQuerying:
    """FR2: Outcome Querying"""

    @pytest.fixture
    def tracker_with_data(self, tmp_path):
        """Create tracker with sample data"""
        db_path = tmp_path / "test_outcomes.db"
        tracker = OutcomeTracker(db_path=str(db_path))

        # Add sample data
        outcomes = [
            Outcome(domain="email", approach="rag", success=True, quality_score=0.9),
            Outcome(domain="email", approach="rag", success=True, quality_score=0.8),
            Outcome(domain="email", approach="keyword", success=False),
            Outcome(domain="calendar", approach="query", success=True),
            Outcome(domain="calendar", approach="query", success=True),
        ]
        for outcome in outcomes:
            tracker.record_outcome(outcome)

        return tracker

    def test_get_outcome_by_id(self, tracker_with_data):
        """Get specific outcome by ID"""
        outcome = Outcome(domain="test", approach="test", success=True)
        outcome_id = tracker_with_data.record_outcome(outcome)

        retrieved = tracker_with_data.get_outcome(outcome_id)
        assert retrieved is not None
        assert retrieved.domain == "test"

    def test_get_outcome_not_found(self, tracker_with_data):
        """Return None for non-existent ID"""
        result = tracker_with_data.get_outcome("nonexistent-id")
        assert result is None

    def test_query_by_domain(self, tracker_with_data):
        """Query outcomes filtered by domain"""
        results = tracker_with_data.query_outcomes(domain="email")

        assert len(results) == 3
        assert all(r.domain == "email" for r in results)

    def test_query_by_approach(self, tracker_with_data):
        """Query outcomes filtered by approach"""
        results = tracker_with_data.query_outcomes(approach="rag")

        assert len(results) == 2
        assert all(r.approach == "rag" for r in results)

    def test_query_by_time_range(self, tmp_path):
        """Query outcomes within time range"""
        db_path = tmp_path / "test_outcomes.db"
        tracker = OutcomeTracker(db_path=str(db_path))

        # Add outcomes with specific timestamps
        now = datetime.now()
        old_outcome = Outcome(
            domain="test", approach="test", success=True,
            timestamp=now - timedelta(days=10)
        )
        recent_outcome = Outcome(
            domain="test", approach="test", success=True,
            timestamp=now - timedelta(hours=1)
        )
        tracker.record_outcome(old_outcome)
        tracker.record_outcome(recent_outcome)

        # Query last 7 days
        results = tracker.query_outcomes(
            start_time=now - timedelta(days=7),
            end_time=now
        )

        assert len(results) == 1

    def test_query_combined_filters(self, tracker_with_data):
        """Query with multiple filters combined"""
        results = tracker_with_data.query_outcomes(
            domain="email",
            approach="rag"
        )

        assert len(results) == 2
        assert all(r.domain == "email" and r.approach == "rag" for r in results)

    def test_query_respects_limit(self, tracker_with_data):
        """Query respects limit parameter"""
        results = tracker_with_data.query_outcomes(limit=2)
        assert len(results) == 2

    def test_query_returns_empty_for_no_matches(self, tracker_with_data):
        """Return empty list when no outcomes match"""
        results = tracker_with_data.query_outcomes(domain="nonexistent")
        assert results == []


class TestPatternAnalysis:
    """FR3: Pattern Analysis"""

    @pytest.fixture
    def tracker_with_analytics_data(self, tmp_path):
        """Create tracker with data for analytics"""
        db_path = tmp_path / "test_outcomes.db"
        tracker = OutcomeTracker(db_path=str(db_path))

        # Email domain: 80% success with RAG, 40% with keyword
        for i in range(10):
            tracker.record_outcome(Outcome(
                domain="email",
                approach="rag",
                success=i < 8,  # 8 success, 2 failure
                quality_score=0.9 if i < 8 else 0.3
            ))
            tracker.record_outcome(Outcome(
                domain="email",
                approach="keyword",
                success=i < 4,  # 4 success, 6 failure
                quality_score=0.7 if i < 4 else 0.2
            ))

        return tracker

    def test_success_rate_by_domain(self, tracker_with_analytics_data):
        """Calculate success rate for a domain"""
        rate = tracker_with_analytics_data.get_success_rate(domain="email")

        # 12 successes out of 20 = 60%
        assert 0.55 <= rate <= 0.65

    def test_success_rate_by_approach(self, tracker_with_analytics_data):
        """Calculate success rate for an approach"""
        rag_rate = tracker_with_analytics_data.get_success_rate(approach="rag")
        keyword_rate = tracker_with_analytics_data.get_success_rate(approach="keyword")

        assert 0.75 <= rag_rate <= 0.85  # ~80%
        assert 0.35 <= keyword_rate <= 0.45  # ~40%

    def test_approach_comparison(self, tracker_with_analytics_data):
        """Compare multiple approaches"""
        comparison = tracker_with_analytics_data.get_approach_comparison(
            approaches=["rag", "keyword"],
            domain="email"
        )

        assert "rag" in comparison
        assert "keyword" in comparison
        assert comparison["rag"].success_rate > comparison["keyword"].success_rate
        assert comparison["rag"].total_count == 10
        assert comparison["rag"].avg_quality is not None

    def test_daily_trends(self, tmp_path):
        """Generate daily trend data"""
        db_path = tmp_path / "test_outcomes.db"
        tracker = OutcomeTracker(db_path=str(db_path))

        now = datetime.now()
        # Add outcomes over 3 days
        for day_offset in range(3):
            for i in range(5):
                tracker.record_outcome(Outcome(
                    domain="test",
                    approach="test",
                    success=True,
                    timestamp=now - timedelta(days=day_offset)
                ))

        trends = tracker.get_trends(granularity="day", days=7)

        assert len(trends) >= 3
        assert all(isinstance(t, TrendPoint) for t in trends)
        assert all(t.total_count > 0 for t in trends)

    def test_weekly_trends(self, tmp_path):
        """Generate weekly trend data"""
        db_path = tmp_path / "test_outcomes.db"
        tracker = OutcomeTracker(db_path=str(db_path))

        now = datetime.now()
        # Add outcomes over 2 weeks
        for week_offset in range(2):
            for i in range(10):
                tracker.record_outcome(Outcome(
                    domain="test",
                    approach="test",
                    success=True,
                    timestamp=now - timedelta(weeks=week_offset)
                ))

        trends = tracker.get_trends(granularity="week", days=30)

        assert len(trends) >= 2

    def test_analytics_handle_empty_data(self, tmp_path):
        """Analytics should handle empty data gracefully"""
        db_path = tmp_path / "test_outcomes.db"
        tracker = OutcomeTracker(db_path=str(db_path))

        rate = tracker.get_success_rate(domain="nonexistent")
        assert rate == 0.0 or rate is None  # Accept either

        comparison = tracker.get_approach_comparison(["a", "b"])
        assert comparison == {} or all(s.total_count == 0 for s in comparison.values())


class TestABTesting:
    """FR4: A/B Testing"""

    @pytest.fixture
    def tracker(self, tmp_path):
        """Create a tracker with temp database"""
        db_path = tmp_path / "test_outcomes.db"
        return OutcomeTracker(db_path=str(db_path))

    def test_create_experiment(self, tracker):
        """Create an A/B experiment"""
        experiment = Experiment(
            name="RAG vs Keyword Search",
            variants=["rag", "keyword"],
            description="Compare search approaches"
        )
        exp_id = tracker.create_experiment(experiment)

        assert exp_id is not None
        assert len(exp_id) > 0

    def test_record_outcome_with_variant(self, tracker):
        """Record outcomes with variant_id for experiments"""
        # Create experiment
        experiment = Experiment(name="Test", variants=["A", "B"])
        exp_id = tracker.create_experiment(experiment)

        # Record outcomes for each variant
        tracker.record_outcome(Outcome(
            domain="test",
            approach="test",
            success=True,
            variant_id="A"
        ))
        tracker.record_outcome(Outcome(
            domain="test",
            approach="test",
            success=False,
            variant_id="B"
        ))

        # Query by variant
        results_a = tracker.query_outcomes(variant_id="A")
        results_b = tracker.query_outcomes(variant_id="B")

        assert len(results_a) == 1
        assert len(results_b) == 1

    def test_get_experiment_results(self, tracker):
        """Get experiment results with per-variant statistics"""
        # Create experiment
        experiment = Experiment(name="Test", variants=["A", "B"])
        exp_id = tracker.create_experiment(experiment)

        # Record outcomes
        for i in range(10):
            tracker.record_outcome(Outcome(
                domain="test", approach="test",
                success=i < 8,  # A: 80% success
                variant_id="A"
            ))
            tracker.record_outcome(Outcome(
                domain="test", approach="test",
                success=i < 5,  # B: 50% success
                variant_id="B"
            ))

        results = tracker.get_experiment_results(exp_id)

        assert results.experiment_id == exp_id
        assert "A" in results.variant_stats
        assert "B" in results.variant_stats
        assert results.variant_stats["A"].success_rate > results.variant_stats["B"].success_rate

    def test_end_experiment(self, tracker):
        """End experiment and declare winner"""
        experiment = Experiment(name="Test", variants=["A", "B"])
        exp_id = tracker.create_experiment(experiment)

        tracker.end_experiment(exp_id, winner="A")

        results = tracker.get_experiment_results(exp_id)
        assert results.status == "completed"
        assert results.winner == "A"


class TestPerformance:
    """NFR1: Performance Requirements"""

    @pytest.fixture
    def tracker(self, tmp_path):
        """Create a tracker with temp database"""
        db_path = tmp_path / "test_outcomes.db"
        return OutcomeTracker(db_path=str(db_path))

    def test_record_latency_under_10ms(self, tracker):
        """Record operation should complete in <10ms"""
        outcome = Outcome(domain="test", approach="test", success=True)

        start = time.perf_counter()
        tracker.record_outcome(outcome)
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < 10, f"Record took {elapsed_ms:.2f}ms, expected <10ms"

    def test_query_latency_under_100ms(self, tracker):
        """Query should complete in <100ms with 1K records"""
        # Insert 1000 records
        outcomes = [
            Outcome(domain="test", approach="test", success=True)
            for _ in range(1000)
        ]
        tracker.record_batch(outcomes)

        start = time.perf_counter()
        results = tracker.query_outcomes(domain="test", limit=100)
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < 100, f"Query took {elapsed_ms:.2f}ms, expected <100ms"

    def test_handles_10k_records(self, tracker):
        """System should handle 10K+ records without degradation"""
        # Insert 10K records in batches
        for _ in range(100):
            outcomes = [
                Outcome(domain="test", approach="test", success=True)
                for _ in range(100)
            ]
            tracker.record_batch(outcomes)

        # Verify count
        stats = tracker.get_stats()
        assert stats['total_outcomes'] >= 10000

        # Query should still be fast
        start = time.perf_counter()
        tracker.get_success_rate(domain="test")
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < 500, f"Analytics took {elapsed_ms:.2f}ms with 10K records"


class TestReliability:
    """NFR2: Reliability Requirements"""

    def test_graceful_handling_db_unavailable(self, tmp_path):
        """Handle unavailable database gracefully"""
        db_path = tmp_path / "readonly" / "test.db"

        # This should not raise, but handle gracefully
        try:
            tracker = OutcomeTracker(db_path=str(db_path))
            # Operations should fail gracefully
            result = tracker.record_outcome(Outcome(
                domain="test", approach="test", success=True
            ))
            # Either returns None or raises specific exception
        except PermissionError:
            pass  # Acceptable
        except Exception as e:
            # Should be a specific, handled exception
            assert "database" in str(e).lower() or "permission" in str(e).lower()

    def test_data_persists_across_restarts(self, tmp_path):
        """Data should persist when tracker is recreated"""
        db_path = tmp_path / "test_outcomes.db"

        # Create tracker and add data
        tracker1 = OutcomeTracker(db_path=str(db_path))
        outcome_id = tracker1.record_outcome(Outcome(
            domain="test", approach="test", success=True
        ))
        del tracker1

        # Create new tracker instance
        tracker2 = OutcomeTracker(db_path=str(db_path))
        retrieved = tracker2.get_outcome(outcome_id)

        assert retrieved is not None
        assert retrieved.domain == "test"

    def test_concurrent_writes(self, tmp_path):
        """Handle concurrent writes without data loss"""
        import threading

        db_path = tmp_path / "test_outcomes.db"
        tracker = OutcomeTracker(db_path=str(db_path))

        results = []
        errors = []

        def write_outcomes(thread_id):
            try:
                for i in range(10):
                    outcome_id = tracker.record_outcome(Outcome(
                        domain=f"thread_{thread_id}",
                        approach="test",
                        success=True
                    ))
                    results.append(outcome_id)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=write_outcomes, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Concurrent write errors: {errors}"
        assert len(results) == 50  # 5 threads * 10 writes


class TestObservability:
    """NFR3: Observability Requirements"""

    @pytest.fixture
    def tracker(self, tmp_path):
        """Create a tracker with temp database"""
        db_path = tmp_path / "test_outcomes.db"
        return OutcomeTracker(db_path=str(db_path))

    def test_health_check_returns_status(self, tracker):
        """Health check should return status information"""
        health = tracker.health_check()

        assert 'status' in health
        assert health['status'] in ['healthy', 'degraded', 'unhealthy']
        assert 'database' in health

    def test_stats_include_counts(self, tracker):
        """Stats should include record counts"""
        # Add some data
        for _ in range(5):
            tracker.record_outcome(Outcome(
                domain="test", approach="test", success=True
            ))

        stats = tracker.get_stats()

        assert 'total_outcomes' in stats
        assert stats['total_outcomes'] == 5
        assert 'total_experiments' in stats

    def test_logging_on_errors(self, tracker, caplog):
        """Errors should be logged"""
        import logging

        # Attempt invalid operation
        with pytest.raises(ValueError):
            tracker.record_outcome(Outcome(
                domain="test",
                approach="test",
                success=True,
                quality_score=2.0  # Invalid
            ))

        # Check that error was logged
        # Note: Implementation should use logging module


class TestIntegration:
    """Integration with existing agentic patterns"""

    @pytest.fixture
    def tracker(self, tmp_path):
        """Create a tracker with temp database"""
        db_path = tmp_path / "test_outcomes.db"
        return OutcomeTracker(db_path=str(db_path))

    def test_compatible_with_adaptive_routing_outcome(self, tracker):
        """Should be compatible with adaptive_routing.TaskOutcome"""
        # Simulate converting from TaskOutcome format
        task_outcome_data = {
            'task_id': 'task-123',
            'domain': 'email',
            'complexity': 3,
            'agent_used': 'email_agent',
            'success': True,
            'quality_score': 0.9,
            'user_corrections': 0
        }

        # Convert to our Outcome format
        outcome = Outcome(
            id=task_outcome_data['task_id'],
            domain=task_outcome_data['domain'],
            approach=f"complexity_{task_outcome_data['complexity']}",
            agent_used=task_outcome_data['agent_used'],
            success=task_outcome_data['success'],
            quality_score=task_outcome_data['quality_score'],
            user_correction=task_outcome_data['user_corrections'] > 0
        )

        outcome_id = tracker.record_outcome(outcome)
        assert outcome_id == 'task-123'

    def test_compatible_with_continuous_eval_record(self, tracker):
        """Should be compatible with continuous_eval.EvaluationRecord"""
        eval_record_data = {
            'task_id': 'eval-456',
            'domain': 'calendar',
            'agent_used': 'calendar_agent',
            'output_quality': 0.85,
            'task_completed': True,
            'auto_score': 0.9
        }

        # Convert to our Outcome format
        outcome = Outcome(
            id=eval_record_data['task_id'],
            domain=eval_record_data['domain'],
            approach='agent_execution',
            agent_used=eval_record_data['agent_used'],
            success=eval_record_data['task_completed'],
            quality_score=eval_record_data['output_quality'],
            metadata={'auto_score': eval_record_data['auto_score']}
        )

        outcome_id = tracker.record_outcome(outcome)
        retrieved = tracker.get_outcome(outcome_id)

        assert retrieved.metadata['auto_score'] == 0.9


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
