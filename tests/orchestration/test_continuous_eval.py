#!/usr/bin/env python3
"""
Unit Tests for Continuous Evaluation System

Phase 2 Agentic AI Enhancement: Learning Foundation
Tests the continuous evaluation and feedback loop.
"""

import unittest
import tempfile
import os
from datetime import datetime, timedelta


class TestContinuousEval(unittest.TestCase):
    """Test ContinuousEvaluationSystem class"""

    def setUp(self):
        """Create temp database for each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test_eval.db')

        from continuous_eval import ContinuousEvaluationSystem
        self.system = ContinuousEvaluationSystem(db_path=self.db_path)

    def tearDown(self):
        """Clean up temp database"""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)

    def test_initialization(self):
        """Test system initializes correctly"""
        self.assertIsNotNone(self.system)
        self.assertTrue(os.path.exists(self.db_path))

    def test_record_evaluation(self):
        """Test recording an evaluation"""
        from continuous_eval import EvaluationRecord

        record = EvaluationRecord(
            task_id="test-001",
            timestamp=datetime.now(),
            agent_used="sre_principal_engineer",
            query="fix database latency",
            domain="sre",
            complexity=5,
            output_quality=0.85,
            task_completed=True,
            user_rating=None,
            auto_score=0.85,
            issues_found=[]
        )

        self.system.record_evaluation(record)

        # Verify it was stored
        records = self.system.get_recent_evaluations(limit=10)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['task_id'], "test-001")

    def test_auto_scoring(self):
        """Test automatic output scoring"""
        output = """
        ## Solution

        Here's how to fix the issue:

        1. First, check the configuration
        2. Update the settings
        3. Restart the service

        This handles the common case and edge cases.
        """

        score = self.system.auto_score_output(output, "how to fix the issue")

        self.assertGreater(score, 0.5)
        self.assertLessEqual(score, 1.0)

    def test_auto_score_low_quality(self):
        """Test auto scoring catches low quality output"""
        bad_output = "TODO: implement this later"

        score = self.system.auto_score_output(bad_output, "how to fix")

        self.assertLess(score, 0.7)

    def test_get_agent_performance(self):
        """Test getting agent performance stats"""
        from continuous_eval import EvaluationRecord

        # Record multiple evaluations for same agent
        for i in range(5):
            record = EvaluationRecord(
                task_id=f"perf-{i}",
                timestamp=datetime.now(),
                agent_used="test_agent",
                query=f"query {i}",
                domain="test",
                complexity=3,
                output_quality=0.8 + (i * 0.02),
                task_completed=True,
                user_rating=None,
                auto_score=0.8,
                issues_found=[]
            )
            self.system.record_evaluation(record)

        # Get performance
        perf = self.system.get_agent_performance("test_agent")

        self.assertEqual(perf['agent'], "test_agent")
        self.assertEqual(perf['total_tasks'], 5)
        self.assertGreater(perf['avg_quality'], 0.7)

    def test_get_domain_trends(self):
        """Test getting domain trends"""
        from continuous_eval import EvaluationRecord

        # Record evaluations over time
        for i in range(10):
            record = EvaluationRecord(
                task_id=f"trend-{i}",
                timestamp=datetime.now() - timedelta(days=i),
                agent_used="agent",
                query=f"query {i}",
                domain="trend_domain",
                complexity=3,
                output_quality=0.7 + (i * 0.02),  # Improving over time (older = higher)
                task_completed=True,
                user_rating=None,
                auto_score=0.7,
                issues_found=[]
            )
            self.system.record_evaluation(record)

        trends = self.system.get_domain_trends("trend_domain")

        self.assertIn('trend_direction', trends)
        self.assertIn('avg_quality', trends)

    def test_feedback_integration(self):
        """Test feedback loop to adaptive routing"""
        from continuous_eval import EvaluationRecord

        # Record poor performance without agent
        for i in range(10):
            record = EvaluationRecord(
                task_id=f"feedback-{i}",
                timestamp=datetime.now(),
                agent_used=None,  # No agent used
                query="complex query",
                domain="feedback_test",
                complexity=4,
                output_quality=0.4,  # Poor quality
                task_completed=False,
                user_rating=None,
                auto_score=0.4,
                issues_found=["incomplete", "missing_steps"]
            )
            self.system.record_evaluation(record)

        # Get recommendations
        recommendations = self.system.get_routing_recommendations("feedback_test")

        # Should recommend lowering threshold since tasks failing without agent
        self.assertIn('threshold_suggestion', recommendations)

    def test_user_rating_update(self):
        """Test updating evaluation with user rating"""
        from continuous_eval import EvaluationRecord

        record = EvaluationRecord(
            task_id="rating-001",
            timestamp=datetime.now(),
            agent_used="agent",
            query="test",
            domain="test",
            complexity=3,
            output_quality=0.8,
            task_completed=True,
            user_rating=None,
            auto_score=0.8,
            issues_found=[]
        )
        self.system.record_evaluation(record)

        # Update with user rating
        self.system.update_user_rating("rating-001", 4)  # 1-5 scale

        # Verify update
        records = self.system.get_recent_evaluations(limit=1)
        self.assertEqual(records[0]['user_rating'], 4)

    def test_quality_alerts(self):
        """Test quality alert generation"""
        from continuous_eval import EvaluationRecord

        # Record consistently poor evaluations
        for i in range(5):
            record = EvaluationRecord(
                task_id=f"alert-{i}",
                timestamp=datetime.now(),
                agent_used="poor_agent",
                query="query",
                domain="alert_test",
                complexity=3,
                output_quality=0.3,  # Very poor
                task_completed=False,
                user_rating=None,
                auto_score=0.3,
                issues_found=["major_error"]
            )
            self.system.record_evaluation(record)

        alerts = self.system.check_quality_alerts()

        # Should have alert for poor_agent
        agent_alerts = [a for a in alerts if a.get('agent') == 'poor_agent']
        self.assertGreater(len(agent_alerts), 0)

    def test_export_metrics(self):
        """Test exporting metrics for dashboard"""
        from continuous_eval import EvaluationRecord

        record = EvaluationRecord(
            task_id="export-001",
            timestamp=datetime.now(),
            agent_used="agent",
            query="test",
            domain="export",
            complexity=3,
            output_quality=0.8,
            task_completed=True,
            user_rating=None,
            auto_score=0.8,
            issues_found=[]
        )
        self.system.record_evaluation(record)

        metrics = self.system.export_metrics()

        self.assertIn('total_evaluations', metrics)
        self.assertIn('avg_quality', metrics)
        self.assertIn('completion_rate', metrics)


class TestEvaluationRecord(unittest.TestCase):
    """Test EvaluationRecord dataclass"""

    def test_record_creation(self):
        """Test creating an evaluation record"""
        from continuous_eval import EvaluationRecord

        record = EvaluationRecord(
            task_id="test-001",
            timestamp=datetime.now(),
            agent_used="test_agent",
            query="test query",
            domain="test",
            complexity=3,
            output_quality=0.8,
            task_completed=True,
            user_rating=4,
            auto_score=0.85,
            issues_found=["minor_issue"]
        )

        self.assertEqual(record.task_id, "test-001")
        self.assertEqual(record.domain, "test")
        self.assertEqual(record.output_quality, 0.8)


if __name__ == "__main__":
    print("Continuous Evaluation System Unit Tests")
    print("=" * 60)
    unittest.main(verbosity=2)
