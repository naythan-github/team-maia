#!/usr/bin/env python3
"""
Unit Tests for Adaptive Human-in-the-Loop System

Phase 3 Agentic AI Enhancement: Dynamic HITL Pattern
Tests confidence-based interruption decisions.
"""

import unittest
import tempfile
import os
from datetime import datetime


class TestAdaptiveHITL(unittest.TestCase):
    """Test AdaptiveHITL class"""

    def setUp(self):
        """Create temp database for each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test_hitl.db')

        from adaptive_hitl import AdaptiveHITL
        self.hitl = AdaptiveHITL(db_path=self.db_path)

    def tearDown(self):
        """Clean up temp database"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization(self):
        """Test HITL system initializes correctly"""
        self.assertIsNotNone(self.hitl)
        self.assertTrue(os.path.exists(self.db_path))

    def test_calculate_action_confidence(self):
        """Test calculating confidence for an action"""
        action = {
            'type': 'file_read',
            'path': '/tmp/test.txt'
        }

        confidence = self.hitl.calculate_confidence(action)

        # File read should be high confidence (safe)
        self.assertGreater(confidence, 0.8)

    def test_low_confidence_for_destructive_action(self):
        """Test low confidence for destructive actions"""
        action = {
            'type': 'file_delete',
            'path': '/important/data.txt'
        }

        confidence = self.hitl.calculate_confidence(action)

        # Delete should be lower confidence
        self.assertLess(confidence, 0.7)

    def test_should_pause_for_low_confidence(self):
        """Test pausing for human when confidence low"""
        action = {
            'type': 'database_drop',
            'target': 'production_db'
        }

        should_pause, reason = self.hitl.should_pause(action)

        self.assertTrue(should_pause)
        # Could be 'confidence' or 'critical'
        self.assertTrue('confidence' in reason.lower() or 'critical' in reason.lower())

    def test_should_not_pause_for_high_confidence(self):
        """Test not pausing for safe actions"""
        action = {
            'type': 'file_read',
            'path': '/tmp/log.txt'
        }

        should_pause, reason = self.hitl.should_pause(action)

        self.assertFalse(should_pause)

    def test_always_pause_for_critical_actions(self):
        """Test always pausing for critical actions regardless of confidence"""
        action = {
            'type': 'git_push_force',
            'branch': 'main'
        }

        should_pause, reason = self.hitl.should_pause(action)

        self.assertTrue(should_pause)
        self.assertIn('critical', reason.lower())

    def test_record_human_decision(self):
        """Test recording human approval/rejection"""
        action = {'type': 'file_delete', 'path': '/tmp/test.txt'}

        self.hitl.record_decision(
            action=action,
            approved=True,
            human_feedback="OK to delete temp file"
        )

        # Should be recorded
        decisions = self.hitl.get_recent_decisions(limit=1)
        self.assertEqual(len(decisions), 1)
        self.assertTrue(decisions[0]['approved'])

    def test_learn_from_approvals(self):
        """Test learning from repeated approvals"""
        action_type = 'custom_action'

        # Record multiple approvals
        for i in range(5):
            self.hitl.record_decision(
                action={'type': action_type, 'id': i},
                approved=True,
                human_feedback=None
            )

        # Confidence should increase for this action type
        confidence = self.hitl.get_learned_confidence(action_type)

        self.assertGreater(confidence, 0.5)

    def test_learn_from_rejections(self):
        """Test learning from repeated rejections"""
        action_type = 'risky_action'

        # Record multiple rejections
        for i in range(5):
            self.hitl.record_decision(
                action={'type': action_type, 'id': i},
                approved=False,
                human_feedback="Too risky"
            )

        # Confidence should decrease for this action type
        confidence = self.hitl.get_learned_confidence(action_type)

        self.assertLess(confidence, 0.5)

    def test_context_affects_confidence(self):
        """Test that context affects confidence calculation"""
        # Same action, different contexts
        action = {'type': 'file_write', 'path': '/tmp/test.txt'}

        # Development context
        dev_confidence = self.hitl.calculate_confidence(
            action,
            context={'environment': 'development'}
        )

        # Production context
        prod_confidence = self.hitl.calculate_confidence(
            action,
            context={'environment': 'production'}
        )

        # Production should be more cautious
        self.assertLess(prod_confidence, dev_confidence)

    def test_threshold_customization(self):
        """Test customizing pause threshold"""
        from adaptive_hitl import AdaptiveHITL

        strict_hitl = AdaptiveHITL(db_path=self.db_path, pause_threshold=0.9)
        lenient_hitl = AdaptiveHITL(db_path=self.db_path, pause_threshold=0.3)

        action = {'type': 'moderate_action', 'confidence_override': 0.6}

        strict_should_pause, _ = strict_hitl.should_pause(action)
        lenient_should_pause, _ = lenient_hitl.should_pause(action)

        self.assertTrue(strict_should_pause)  # 0.6 < 0.9
        self.assertFalse(lenient_should_pause)  # 0.6 > 0.3

    def test_get_stats(self):
        """Test getting HITL statistics"""
        # Record some decisions
        self.hitl.record_decision({'type': 'a'}, True, None)
        self.hitl.record_decision({'type': 'b'}, True, None)
        self.hitl.record_decision({'type': 'c'}, False, "Rejected")

        stats = self.hitl.get_stats()

        self.assertEqual(stats['total_decisions'], 3)
        self.assertEqual(stats['approvals'], 2)
        self.assertEqual(stats['rejections'], 1)

    def test_bulk_action_detection(self):
        """Test detecting bulk/batch operations"""
        action = {
            'type': 'file_delete',
            'targets': ['/tmp/a.txt', '/tmp/b.txt', '/tmp/c.txt', '/tmp/d.txt', '/tmp/e.txt']
        }

        should_pause, reason = self.hitl.should_pause(action)

        # Bulk operations should always pause
        self.assertTrue(should_pause)
        self.assertIn('bulk', reason.lower())

    def test_rate_limit_detection(self):
        """Test detecting rapid action sequences"""
        action = {'type': 'api_call'}

        # Simulate rapid actions
        for i in range(10):
            self.hitl.record_action_attempt(action)

        should_pause, reason = self.hitl.should_pause(action)

        # Should pause due to rate
        self.assertTrue(should_pause)


class TestActionCategories(unittest.TestCase):
    """Test action category classification"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test_hitl2.db')

        from adaptive_hitl import AdaptiveHITL
        self.hitl = AdaptiveHITL(db_path=self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)

    def test_classify_read_action(self):
        """Test classifying read actions as safe"""
        category = self.hitl.classify_action({'type': 'file_read'})
        self.assertEqual(category, 'safe')

    def test_classify_write_action(self):
        """Test classifying write actions as moderate"""
        category = self.hitl.classify_action({'type': 'file_write'})
        self.assertEqual(category, 'moderate')

    def test_classify_delete_action(self):
        """Test classifying delete actions as destructive"""
        category = self.hitl.classify_action({'type': 'file_delete'})
        self.assertEqual(category, 'destructive')

    def test_classify_critical_action(self):
        """Test classifying critical actions"""
        category = self.hitl.classify_action({'type': 'git_push_force'})
        self.assertEqual(category, 'critical')


if __name__ == "__main__":
    print("Adaptive Human-in-the-Loop Unit Tests")
    print("=" * 60)
    unittest.main(verbosity=2)
