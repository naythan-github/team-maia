#!/usr/bin/env python3
"""
Unit Tests for Adaptive Complexity Routing System
"""

import unittest
import tempfile
import os
from datetime import datetime, timedelta
from adaptive_routing import (
    AdaptiveRoutingSystem,
    AdaptiveThreshold,
    TaskOutcome,
    generate_task_id
)


class TestAdaptiveThreshold(unittest.TestCase):
    """Test AdaptiveThreshold dataclass"""

    def test_default_values(self):
        threshold = AdaptiveThreshold(domain='test')
        self.assertEqual(threshold.domain, 'test')
        self.assertEqual(threshold.base_threshold, 3)
        self.assertEqual(threshold.current_threshold, 3.0)
        self.assertEqual(threshold.success_rate, 0.0)

    def test_should_load_agent_above_threshold(self):
        threshold = AdaptiveThreshold(domain='test', current_threshold=3.0)
        self.assertTrue(threshold.should_load_agent(3))
        self.assertTrue(threshold.should_load_agent(5))
        self.assertTrue(threshold.should_load_agent(10))

    def test_should_not_load_agent_below_threshold(self):
        threshold = AdaptiveThreshold(domain='test', current_threshold=3.0)
        self.assertFalse(threshold.should_load_agent(1))
        self.assertFalse(threshold.should_load_agent(2))


class TestAdaptiveRoutingSystem(unittest.TestCase):
    """Test AdaptiveRoutingSystem"""

    def setUp(self):
        """Create temp database for each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test_routing.db')
        self.system = AdaptiveRoutingSystem(db_path=self.db_path)

    def tearDown(self):
        """Clean up temp database"""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)

    def test_initialization(self):
        """Test system initializes correctly"""
        self.assertIsNotNone(self.system)
        self.assertIn('general', self.system.thresholds)

    def test_get_threshold_creates_new(self):
        """Test getting threshold for unknown domain creates it"""
        threshold = self.system.get_threshold('new_domain')
        self.assertEqual(threshold.domain, 'new_domain')
        self.assertEqual(threshold.current_threshold, 3.0)

    def test_should_load_agent_default(self):
        """Test default agent loading decision"""
        # Complexity 3 should load (equals threshold)
        should_load, reason = self.system.should_load_agent('general', 3)
        self.assertTrue(should_load)

        # Complexity 2 should not load (below threshold)
        should_load, reason = self.system.should_load_agent('general', 2)
        self.assertFalse(should_load)

    def test_record_outcome(self):
        """Test recording task outcome"""
        outcome = TaskOutcome(
            task_id=generate_task_id(),
            timestamp=datetime.now(),
            query='test query',
            domain='test',
            complexity=5,
            agent_used='test_agent',
            agent_loaded=True,
            success=True,
            quality_score=0.9,
            user_corrections=0
        )

        self.system.record_outcome(outcome)

        # Verify it was stored
        stats = self.system.get_domain_stats('test')
        self.assertEqual(stats['total_tasks'], 1)
        self.assertEqual(stats['success_count'], 1)

    def test_threshold_adapts_on_failures(self):
        """Test threshold adjusts when success rate drops"""
        # Record many failures to trigger adaptation
        for i in range(10):
            outcome = TaskOutcome(
                task_id=generate_task_id(),
                timestamp=datetime.now(),
                query='failing query',
                domain='failing_domain',
                complexity=4,
                agent_used=None,
                agent_loaded=False,
                success=False,  # All failures
                quality_score=0.2,
                user_corrections=2
            )
            self.system.record_outcome(outcome)

        # Check threshold was adjusted
        threshold = self.system.get_threshold('failing_domain')
        # With failures, threshold should decrease (load agents more often)
        self.assertLessEqual(threshold.current_threshold, 3.0)

    def test_threshold_adapts_on_successes(self):
        """Test threshold adjusts when success rate is high"""
        # Record many successes without agents
        for i in range(10):
            outcome = TaskOutcome(
                task_id=generate_task_id(),
                timestamp=datetime.now(),
                query='succeeding query',
                domain='success_domain',
                complexity=2,
                agent_used=None,
                agent_loaded=False,
                success=True,  # All successes
                quality_score=0.95,
                user_corrections=0
            )
            self.system.record_outcome(outcome)

        # Check threshold was adjusted
        threshold = self.system.get_threshold('success_domain')
        # With high success without agents, threshold could increase
        self.assertGreaterEqual(threshold.current_threshold, 3.0)

    def test_get_domain_stats(self):
        """Test getting domain statistics"""
        # Add some test data
        for i in range(5):
            outcome = TaskOutcome(
                task_id=generate_task_id(),
                timestamp=datetime.now(),
                query=f'query {i}',
                domain='stats_domain',
                complexity=i + 1,
                agent_used='agent' if i % 2 == 0 else None,
                agent_loaded=i % 2 == 0,
                success=i % 3 != 0,
                quality_score=0.7 + i * 0.05,
                user_corrections=0
            )
            self.system.record_outcome(outcome)

        stats = self.system.get_domain_stats('stats_domain')

        self.assertEqual(stats['domain'], 'stats_domain')
        self.assertEqual(stats['total_tasks'], 5)
        self.assertGreater(stats['success_count'], 0)
        self.assertIn('success_rate', stats)
        self.assertIn('agent_usage_rate', stats)

    def test_reset_domain(self):
        """Test resetting domain threshold"""
        # First modify the threshold
        threshold = self.system.get_threshold('reset_test')
        threshold.current_threshold = 5.0
        self.system._save_threshold(threshold)

        # Reset it
        self.system.reset_domain('reset_test')

        # Verify it's back to default
        threshold = self.system.get_threshold('reset_test')
        self.assertEqual(threshold.current_threshold, 3.0)

    def test_threshold_bounds(self):
        """Test threshold stays within bounds"""
        # The system should respect THRESHOLD_MIN and THRESHOLD_MAX
        self.assertGreaterEqual(self.system.THRESHOLD_MIN, 1)
        self.assertLessEqual(self.system.THRESHOLD_MAX, 10)


class TestGenerateTaskId(unittest.TestCase):
    """Test task ID generation"""

    def test_generates_unique_ids(self):
        """Test that generated IDs are unique"""
        ids = [generate_task_id() for _ in range(100)]
        self.assertEqual(len(ids), len(set(ids)))

    def test_id_format(self):
        """Test ID format"""
        task_id = generate_task_id()
        self.assertEqual(len(task_id), 8)


if __name__ == "__main__":
    print("🧪 Adaptive Routing Unit Tests")
    print("=" * 60)
    unittest.main(verbosity=2)
