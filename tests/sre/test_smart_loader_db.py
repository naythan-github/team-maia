#!/usr/bin/env python3
"""
Test Suite for Smart Loader Database Integration

Tests query interface and smart loader DB integration following TDD methodology.

Agent: SRE Principal Engineer Agent
Phase: 165 - Smart Loader Database Integration
"""

import unittest
import sqlite3
import tempfile
import os
import time
from pathlib import Path
from typing import List, Dict
from statistics import mean, stdev

# Import modules to test
import sys
maia_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(maia_root / "claude" / "tools" / "sre"))

from system_state_queries import SystemStateQueries, PhaseRecord, PhaseWithContext


class TestQueryInterface(unittest.TestCase):
    """Test SystemStateQueries interface"""

    @classmethod
    def setUpClass(cls):
        """Use real database for testing (10 migrated phases)"""
        cls.db_path = maia_root / "claude" / "data" / "databases" / "system" / "system_state.db"

        if not cls.db_path.exists():
            raise FileNotFoundError(
                f"Database not found: {cls.db_path}\n"
                f"Run ETL first: python3 claude/tools/sre/system_state_etl.py"
            )

    def setUp(self):
        """Initialize query interface"""
        self.queries = SystemStateQueries(self.db_path)

    def test_get_recent_phases(self):
        """Test retrieving recent phases"""
        phases = self.queries.get_recent_phases(count=5)

        self.assertIsInstance(phases, list)
        self.assertGreater(len(phases), 0)
        self.assertLessEqual(len(phases), 5)

        # Check type
        self.assertIsInstance(phases[0], PhaseRecord)

        # Check ordering (most recent first)
        for i in range(len(phases) - 1):
            self.assertGreater(phases[i].phase_number, phases[i+1].phase_number)

    def test_get_phases_by_keyword(self):
        """Test keyword search in narrative text"""
        # Search for "database" (should find Phase 164)
        phases = self.queries.get_phases_by_keyword("database")

        self.assertIsInstance(phases, list)
        self.assertGreater(len(phases), 0)

        # Check that results contain keyword
        phase_164_found = any(p.phase_number == 164 for p in phases)
        self.assertTrue(phase_164_found, "Phase 164 (database migration) should be found")

    def test_get_phases_by_number(self):
        """Test retrieving specific phases"""
        phases = self.queries.get_phases_by_number([163, 162, 161])

        self.assertIsInstance(phases, list)
        self.assertEqual(len(phases), 3)

        # Check that requested phases are returned
        phase_numbers = [p.phase_number for p in phases]
        self.assertIn(163, phase_numbers)
        self.assertIn(162, phase_numbers)
        self.assertIn(161, phase_numbers)

    def test_get_phases_by_number_empty(self):
        """Test empty phase number list"""
        phases = self.queries.get_phases_by_number([])
        self.assertEqual(len(phases), 0)

    def test_get_phase_with_context(self):
        """Test retrieving phase with all related data"""
        # Phase 164 should have problems, solutions, metrics, files
        phase = self.queries.get_phase_with_context(164)

        self.assertIsNotNone(phase)
        self.assertIsInstance(phase, PhaseWithContext)
        self.assertEqual(phase.phase.phase_number, 164)

        # Check related data exists
        self.assertIsInstance(phase.problems, list)
        self.assertIsInstance(phase.solutions, list)
        self.assertIsInstance(phase.metrics, list)
        self.assertIsInstance(phase.files_created, list)
        self.assertIsInstance(phase.tags, list)

    def test_get_phase_with_context_not_found(self):
        """Test retrieving non-existent phase"""
        phase = self.queries.get_phase_with_context(9999)
        self.assertIsNone(phase)

    def test_search_problems_by_category(self):
        """Test searching problems by category"""
        # This will depend on what's in the DB
        # Just verify the function works
        results = self.queries.search_problems_by_category("inefficiency")

        self.assertIsInstance(results, list)
        # Results may be empty if no problems in that category

    def test_get_all_problem_categories(self):
        """Test getting all problem categories"""
        categories = self.queries.get_all_problem_categories()

        self.assertIsInstance(categories, list)
        # May be empty if no problems have explicit categories
        # (many phases describe problems in narrative without category tags)

    def test_get_metric_summary(self):
        """Test metric aggregation"""
        summary = self.queries.get_metric_summary()

        self.assertIsInstance(summary, list)
        # Should have metrics from Phase 164
        self.assertGreater(len(summary), 0)

    def test_get_files_by_type(self):
        """Test file type filtering"""
        # Phase 164 created tools
        tools = self.queries.get_files_by_type("tool")

        self.assertIsInstance(tools, list)
        # Should find system_state_etl.py and related files
        self.assertGreater(len(tools), 0)

    def test_format_phase_as_markdown(self):
        """Test markdown formatting"""
        phases = self.queries.get_recent_phases(count=1)
        self.assertGreater(len(phases), 0)

        markdown = self.queries.format_phase_as_markdown(phases[0])

        self.assertIsInstance(markdown, str)
        self.assertIn(f"PHASE {phases[0].phase_number}", markdown)
        self.assertIn(phases[0].title, markdown)

    def test_format_phases_as_markdown(self):
        """Test formatting multiple phases"""
        phases = self.queries.get_recent_phases(count=3)

        markdown = self.queries.format_phases_as_markdown(phases)

        self.assertIsInstance(markdown, str)
        # Should have phase separators
        self.assertIn("---", markdown)


class TestPerformance(unittest.TestCase):
    """Test query performance benchmarks"""

    @classmethod
    def setUpClass(cls):
        """Use real database for benchmarking"""
        cls.db_path = maia_root / "claude" / "data" / "databases" / "system" / "system_state.db"

        if not cls.db_path.exists():
            raise FileNotFoundError(
                f"Database not found: {cls.db_path}\n"
                f"Run ETL first: python3 claude/tools/sre/system_state_etl.py"
            )

    def setUp(self):
        """Initialize query interface"""
        self.queries = SystemStateQueries(self.db_path)

    def benchmark_query(self, query_func, *args, iterations=100):
        """
        Benchmark a query function.

        Returns:
            (mean_ms, stdev_ms)
        """
        times = []

        # Warm up
        query_func(*args)

        # Benchmark
        for _ in range(iterations):
            start = time.perf_counter()
            query_func(*args)
            elapsed = time.perf_counter() - start
            times.append(elapsed * 1000)  # Convert to milliseconds

        return mean(times), stdev(times) if len(times) > 1 else 0

    def test_recent_phases_performance(self):
        """Test get_recent_phases query latency"""
        mean_ms, std_ms = self.benchmark_query(self.queries.get_recent_phases, 10)

        print(f"\n  get_recent_phases(10): {mean_ms:.2f}ms ± {std_ms:.2f}ms")

        # Should complete in <20ms (target)
        self.assertLess(mean_ms, 20, f"Query too slow: {mean_ms:.2f}ms (target: <20ms)")

    def test_keyword_search_performance(self):
        """Test keyword search query latency"""
        mean_ms, std_ms = self.benchmark_query(self.queries.get_phases_by_keyword, "database")

        print(f"\n  get_phases_by_keyword('database'): {mean_ms:.2f}ms ± {std_ms:.2f}ms")

        # Should complete in <20ms (target)
        self.assertLess(mean_ms, 20, f"Query too slow: {mean_ms:.2f}ms (target: <20ms)")

    def test_specific_phases_performance(self):
        """Test specific phase retrieval latency"""
        mean_ms, std_ms = self.benchmark_query(
            self.queries.get_phases_by_number,
            [163, 162, 161]
        )

        print(f"\n  get_phases_by_number([163,162,161]): {mean_ms:.2f}ms ± {std_ms:.2f}ms")

        # Should complete in <20ms (target)
        self.assertLess(mean_ms, 20, f"Query too slow: {mean_ms:.2f}ms (target: <20ms)")

    def test_phase_with_context_performance(self):
        """Test full context retrieval latency"""
        mean_ms, std_ms = self.benchmark_query(
            self.queries.get_phase_with_context,
            164
        )

        print(f"\n  get_phase_with_context(164): {mean_ms:.2f}ms ± {std_ms:.2f}ms")

        # Should complete in <20ms (target) - this is the slowest query (JOINs)
        self.assertLess(mean_ms, 20, f"Query too slow: {mean_ms:.2f}ms (target: <20ms)")


class TestSmartLoaderIntegration(unittest.TestCase):
    """Test integration with smart_context_loader.py (to be implemented)"""

    def test_db_path_detection(self):
        """Test that smart loader can find database"""
        # This test will be implemented after smart loader integration
        self.skipTest("Smart loader integration not yet complete")

    def test_db_query_path(self):
        """Test that smart loader uses DB when available"""
        self.skipTest("Smart loader integration not yet complete")

    def test_markdown_fallback_path(self):
        """Test that smart loader falls back to markdown when DB unavailable"""
        self.skipTest("Smart loader integration not yet complete")

    def test_output_format_consistency(self):
        """Test that DB and markdown paths return same format"""
        self.skipTest("Smart loader integration not yet complete")


def run_tests():
    """Run all tests and report results"""
    print("=" * 70)
    print("SMART LOADER DATABASE INTEGRATION - TEST SUITE")
    print("=" * 70)

    # Run tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(__import__(__name__))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Passed: {result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped)}")
    print(f"Failed: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print("=" * 70)

    return result.wasSuccessful()


if __name__ == '__main__':
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)
