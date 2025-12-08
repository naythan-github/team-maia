#!/usr/bin/env python3
"""
Unit Tests for Long-Term Memory System

Phase 2 Agentic AI Enhancement: Memory-Enhanced Agents
Tests preference tracking and cross-session learning.
"""

import unittest
import tempfile
import os
from datetime import datetime, timedelta


class TestLongTermMemory(unittest.TestCase):
    """Test LongTermMemory class"""

    def setUp(self):
        """Create temp database for each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test_preferences.db')

        from long_term_memory import LongTermMemory
        self.memory = LongTermMemory(db_path=self.db_path)

    def tearDown(self):
        """Clean up temp database"""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)

    def test_initialization(self):
        """Test memory system initializes correctly"""
        self.assertIsNotNone(self.memory)
        self.assertTrue(os.path.exists(self.db_path))

    def test_store_preference_explicit(self):
        """Test storing explicit preference"""
        self.memory.store_preference(
            key="preferred_language",
            value="python",
            source="explicit",
            confidence=1.0
        )

        pref = self.memory.get_preference("preferred_language")

        self.assertEqual(pref['value'], "python")
        self.assertEqual(pref['source'], "explicit")
        self.assertEqual(pref['confidence'], 1.0)

    def test_store_preference_inferred(self):
        """Test storing inferred preference with lower confidence"""
        self.memory.store_preference(
            key="prefers_verbose",
            value="true",
            source="inferred",
            confidence=0.7
        )

        pref = self.memory.get_preference("prefers_verbose")

        self.assertEqual(pref['source'], "inferred")
        self.assertLess(pref['confidence'], 1.0)

    def test_preference_update(self):
        """Test updating existing preference"""
        # Initial preference
        self.memory.store_preference("tool", "terraform", "explicit", 1.0)

        # Update preference
        self.memory.store_preference("tool", "pulumi", "explicit", 1.0)

        pref = self.memory.get_preference("tool")
        self.assertEqual(pref['value'], "pulumi")

    def test_preference_not_found(self):
        """Test getting non-existent preference"""
        pref = self.memory.get_preference("nonexistent")
        self.assertIsNone(pref)

    def test_record_correction(self):
        """Test recording user correction"""
        self.memory.record_correction(
            original_output="Use Azure CLI",
            correction="Use Terraform instead",
            domain="cloud"
        )

        patterns = self.memory.get_correction_patterns("cloud")

        self.assertEqual(len(patterns), 1)
        self.assertIn("Terraform", patterns[0]['correction'])

    def test_infer_preference_from_corrections(self):
        """Test inferring preferences from repeated corrections"""
        # Record multiple similar corrections
        for i in range(3):
            self.memory.record_correction(
                original_output=f"Output {i} with Azure CLI",
                correction=f"Use Terraform instead (correction {i})",
                domain="infra"
            )

        # Get inferred preferences
        inferred = self.memory.infer_preferences_from_corrections()

        # Should notice pattern
        self.assertGreater(len(inferred), 0)

    def test_get_domain_preferences(self):
        """Test getting all preferences for a domain"""
        self.memory.store_preference("sre.monitoring", "datadog", "explicit", 1.0)
        self.memory.store_preference("sre.alerting", "pagerduty", "explicit", 0.9)
        self.memory.store_preference("dev.ide", "vscode", "explicit", 1.0)

        sre_prefs = self.memory.get_domain_preferences("sre")

        self.assertEqual(len(sre_prefs), 2)

    def test_preference_confidence_decay(self):
        """Test that inferred preferences decay over time"""
        from long_term_memory import LongTermMemory

        # Store old inferred preference
        self.memory.store_preference(
            key="old_preference",
            value="old_value",
            source="inferred",
            confidence=0.8
        )

        # Get decayed confidence
        decayed = self.memory.get_decayed_confidence("old_preference", days_old=60)

        self.assertLess(decayed, 0.8)

    def test_load_session_context(self):
        """Test loading preferences for session startup"""
        # Store some preferences
        self.memory.store_preference("pref1", "val1", "explicit", 1.0)
        self.memory.store_preference("pref2", "val2", "inferred", 0.8)

        # Load session context
        context = self.memory.load_session_context()

        self.assertIn('preferences', context)
        self.assertGreater(len(context['preferences']), 0)

    def test_export_preferences(self):
        """Test exporting all preferences"""
        self.memory.store_preference("export1", "val1", "explicit", 1.0)
        self.memory.store_preference("export2", "val2", "inferred", 0.7)

        export = self.memory.export_all()

        self.assertIn('preferences', export)
        self.assertIn('corrections', export)

    def test_clear_preference(self):
        """Test clearing a specific preference"""
        self.memory.store_preference("to_clear", "value", "explicit", 1.0)
        self.memory.clear_preference("to_clear")

        pref = self.memory.get_preference("to_clear")
        self.assertIsNone(pref)

    def test_high_confidence_filter(self):
        """Test getting only high-confidence preferences"""
        self.memory.store_preference("high", "val1", "explicit", 0.95)
        self.memory.store_preference("low", "val2", "inferred", 0.3)

        high_conf = self.memory.get_preferences_above_confidence(0.7)

        self.assertEqual(len(high_conf), 1)
        self.assertEqual(high_conf[0]['key'], "high")


class TestCorrectionPatterns(unittest.TestCase):
    """Test correction pattern detection"""

    def setUp(self):
        """Create temp database for each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test_corrections.db')

        from long_term_memory import LongTermMemory
        self.memory = LongTermMemory(db_path=self.db_path)

    def tearDown(self):
        """Clean up temp database"""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)

    def test_pattern_detection(self):
        """Test detecting patterns in corrections"""
        # Same type of correction multiple times
        for i in range(5):
            self.memory.record_correction(
                original_output=f"Here is the code: {i}",
                correction="Add more comments please",
                domain="code"
            )

        patterns = self.memory.analyze_correction_patterns()

        # Should detect "needs more comments" pattern
        self.assertGreater(len(patterns), 0)


if __name__ == "__main__":
    print("Long-Term Memory System Unit Tests")
    print("=" * 60)
    unittest.main(verbosity=2)
