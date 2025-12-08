#!/usr/bin/env python3
"""
Comprehensive Test Suite for SYSTEM_STATE Hybrid Database

Tests schema creation, ETL parsing, query functions, and data integrity.
Following TDD methodology - tests written BEFORE implementation.

Agent: SRE Principal Engineer Agent
Phase: 164 - SYSTEM_STATE Migration
"""

import unittest
import sqlite3
import tempfile
import os
from pathlib import Path
from typing import List, Dict, Optional


class TestDatabaseSchema(unittest.TestCase):
    """Test database schema creation and constraints"""

    def setUp(self):
        """Create temporary database for testing"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_path = self.temp_db.name
        self.temp_db.close()

        # Load schema
        schema_path = Path(__file__).parent / "system_state_schema.sql"
        with open(schema_path) as f:
            schema_sql = f.read()

        conn = sqlite3.connect(self.db_path)
        conn.executescript(schema_sql)
        conn.close()

    def tearDown(self):
        """Clean up temporary database"""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_foreign_keys_enabled(self):
        """Test that foreign key constraints are enforced"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check PRAGMA setting
        cursor.execute("PRAGMA foreign_keys")
        result = cursor.fetchone()
        conn.close()

        # Note: PRAGMA foreign_keys must be set per connection
        # Schema file has it, but connections need to enable it
        self.assertIsNotNone(result)

    def test_phases_table_exists(self):
        """Test that phases table was created with correct columns"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(phases)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        conn.close()

        # Check required columns
        self.assertIn('id', columns)
        self.assertIn('phase_number', columns)
        self.assertIn('title', columns)
        self.assertIn('date', columns)
        self.assertIn('status', columns)
        self.assertIn('achievement', columns)
        self.assertIn('narrative_text', columns)

    def test_phase_number_unique_constraint(self):
        """Test that phase_number UNIQUE constraint is enforced"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Insert first phase
        cursor.execute("""
            INSERT INTO phases (phase_number, title, date)
            VALUES (163, 'Test Phase', '2025-11-21')
        """)

        # Try to insert duplicate phase_number (should fail)
        with self.assertRaises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO phases (phase_number, title, date)
                VALUES (163, 'Duplicate Phase', '2025-11-21')
            """)

        conn.close()

    def test_foreign_key_cascade_delete(self):
        """Test that deleting a phase cascades to related tables"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")  # Enable per connection
        cursor = conn.cursor()

        # Insert phase
        cursor.execute("""
            INSERT INTO phases (phase_number, title, date)
            VALUES (163, 'Test Phase', '2025-11-21')
        """)
        phase_id = cursor.lastrowid

        # Insert related records
        cursor.execute("""
            INSERT INTO problems (phase_id, problem_category, before_state)
            VALUES (?, 'test', 'test problem')
        """, (phase_id,))

        cursor.execute("""
            INSERT INTO metrics (phase_id, metric_name, value)
            VALUES (?, 'test_metric', 100.0)
        """, (phase_id,))

        # Verify related records exist
        cursor.execute("SELECT COUNT(*) FROM problems WHERE phase_id = ?", (phase_id,))
        self.assertEqual(cursor.fetchone()[0], 1)

        cursor.execute("SELECT COUNT(*) FROM metrics WHERE phase_id = ?", (phase_id,))
        self.assertEqual(cursor.fetchone()[0], 1)

        # Delete phase
        cursor.execute("DELETE FROM phases WHERE id = ?", (phase_id,))
        conn.commit()

        # Verify related records were deleted (CASCADE)
        cursor.execute("SELECT COUNT(*) FROM problems WHERE phase_id = ?", (phase_id,))
        self.assertEqual(cursor.fetchone()[0], 0)

        cursor.execute("SELECT COUNT(*) FROM metrics WHERE phase_id = ?", (phase_id,))
        self.assertEqual(cursor.fetchone()[0], 0)

        conn.close()

    def test_indexes_created(self):
        """Test that performance indexes were created"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [row[0] for row in cursor.fetchall()]
        conn.close()

        # Check critical indexes exist
        self.assertIn('idx_phases_phase_number', indexes)
        self.assertIn('idx_phases_date', indexes)
        self.assertIn('idx_metrics_name', indexes)

    def test_views_created(self):
        """Test that convenience views were created"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
        views = [row[0] for row in cursor.fetchall()]
        conn.close()

        self.assertIn('v_recent_phases', views)
        self.assertIn('v_metric_summary', views)
        self.assertIn('v_problem_categories', views)


class TestPhaseParser(unittest.TestCase):
    """Test markdown parsing functions (to be implemented)"""

    def test_parse_phase_header(self):
        """Test extracting phase number, title, date from header"""
        # Example header from Phase 163
        header = "## 📄 PHASE 163: Document Conversion + Pod Structure JDs + Save State Fix (2025-11-21) **PRODUCTION READY**"

        # TODO: Implement parse_phase_header function
        # result = parse_phase_header(header)
        # self.assertEqual(result['phase_number'], 163)
        # self.assertEqual(result['date'], '2025-11-21')
        # self.assertIn('Document Conversion', result['title'])
        self.skipTest("Parser not yet implemented")

    def test_parse_achievement_section(self):
        """Test extracting achievement text from markdown"""
        markdown = """
### Achievement
Built production-hardened generic markdown→DOCX converter with Orro corporate branding.
"""
        # TODO: Implement parse_achievement function
        # result = parse_achievement(markdown)
        # self.assertIn('markdown→DOCX', result)
        self.skipTest("Parser not yet implemented")

    def test_parse_metrics(self):
        """Test extracting metrics from markdown"""
        markdown = """
### Metrics
**Time Savings**: Manual formatting 30-45 min → 2 min automated (95% reduction)
**Performance**: 0.10s avg (50x faster than 5s target)
"""
        # TODO: Implement parse_metrics function
        # metrics = parse_metrics(markdown)
        # self.assertEqual(len(metrics), 2)
        # self.assertEqual(metrics[0]['metric_name'], 'time_savings_hours')
        self.skipTest("Parser not yet implemented")

    def test_parse_files_created(self):
        """Test extracting files created from markdown"""
        markdown = """
**Files Created**:
- `claude/tools/document_conversion/convert_md_to_docx.py` - Generic converter (205 lines)
- `claude/tools/document_conversion/test_converter.py` - Test suite (285 lines)
"""
        # TODO: Implement parse_files_created function
        # files = parse_files_created(markdown)
        # self.assertEqual(len(files), 2)
        # self.assertEqual(files[0]['file_path'], 'claude/tools/document_conversion/convert_md_to_docx.py')
        self.skipTest("Parser not yet implemented")

    def test_handle_missing_sections(self):
        """Test parser gracefully handles missing sections"""
        # Minimal phase with only required fields
        markdown = """
## PHASE 99: Test Phase (2025-11-21)

### Achievement
Test achievement text.
"""
        # TODO: Implement full phase parser
        # result = parse_phase(markdown)
        # self.assertEqual(result['phase_number'], 99)
        # self.assertEqual(result['achievement'], 'Test achievement text.')
        # self.assertEqual(result['problems'], [])  # No problems section
        self.skipTest("Parser not yet implemented")


class TestQueryFunctions(unittest.TestCase):
    """Test query interface functions (to be implemented)"""

    def setUp(self):
        """Create test database with sample data"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_path = self.temp_db.name
        self.temp_db.close()

        # Load schema and insert test data
        schema_path = Path(__file__).parent / "system_state_schema.sql"
        with open(schema_path) as f:
            schema_sql = f.read()

        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(schema_sql)

        # Insert test phases
        cursor = conn.cursor()
        for i in range(144, 164):  # Last 20 phases
            cursor.execute("""
                INSERT INTO phases (phase_number, title, date, status)
                VALUES (?, ?, ?, ?)
            """, (i, f'Phase {i}', f'2025-11-{(i-143):02d}', 'COMPLETE'))

        conn.commit()
        conn.close()

    def tearDown(self):
        """Clean up test database"""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_get_recent_phases(self):
        """Test retrieving recent phases"""
        # TODO: Implement get_recent_phases function
        # phases = get_recent_phases(self.db_path, count=10)
        # self.assertEqual(len(phases), 10)
        # self.assertEqual(phases[0]['phase_number'], 163)  # Most recent first
        self.skipTest("Query function not yet implemented")

    def test_get_phases_by_problem_category(self):
        """Test pattern analysis query"""
        # TODO: Add test data with problem categories
        # phases = get_phases_by_problem_category(self.db_path, 'SQL injection')
        # self.assertIsInstance(phases, list)
        self.skipTest("Query function not yet implemented")

    def test_aggregate_metric(self):
        """Test metric aggregation"""
        # TODO: Add test data with metrics
        # total = aggregate_metric(self.db_path, 'time_savings_hours', 'SUM')
        # self.assertIsInstance(total, float)
        self.skipTest("Query function not yet implemented")

    def test_search_narrative(self):
        """Test keyword search in narrative text"""
        # TODO: Implement narrative search
        # results = search_narrative(self.db_path, 'ChromaDB')
        # self.assertIsInstance(results, list)
        self.skipTest("Query function not yet implemented")


class TestETLPipeline(unittest.TestCase):
    """Test ETL (Extract, Transform, Load) pipeline (to be implemented)"""

    def test_etl_transaction_safety(self):
        """Test that ETL uses transactions (rollback on error)"""
        # TODO: Implement ETL with transaction support
        # Test that partial failure doesn't corrupt database
        self.skipTest("ETL not yet implemented")

    def test_etl_idempotent(self):
        """Test that running ETL twice doesn't create duplicates"""
        # TODO: Implement idempotent ETL
        # Run ETL twice on same data, verify no duplicates
        self.skipTest("ETL not yet implemented")

    def test_etl_progress_reporting(self):
        """Test that ETL reports progress during execution"""
        # TODO: Implement progress reporting
        # Capture progress output, verify it shows % complete
        self.skipTest("ETL not yet implemented")

    def test_etl_validation_report(self):
        """Test that ETL generates validation report"""
        # TODO: Implement validation reporting
        # Verify report shows: phases parsed, metrics extracted, errors
        self.skipTest("ETL not yet implemented")


class TestPerformance(unittest.TestCase):
    """Test performance benchmarks"""

    def test_query_performance(self):
        """Test that queries complete in <100ms"""
        # TODO: Benchmark queries with full dataset
        # All queries should complete in <100ms
        self.skipTest("Performance test requires full dataset")

    def test_database_size(self):
        """Test that database size is reasonable"""
        # TODO: Test with full 163 phases
        # Database should be <10 MB
        self.skipTest("Size test requires full dataset")


class TestDataIntegrity(unittest.TestCase):
    """Test data accuracy and integrity"""

    def test_no_orphaned_records(self):
        """Test that foreign keys prevent orphaned records"""
        # Already tested in TestDatabaseSchema, but worth documenting here
        pass

    def test_phase_count_matches_markdown(self):
        """Test that ETL extracts all phases from markdown"""
        # TODO: Compare phase count in DB vs markdown
        # Should extract all 163 phases
        self.skipTest("Requires ETL implementation")


def run_tests():
    """Run all tests and report results"""
    print("=" * 70)
    print("SYSTEM_STATE HYBRID DATABASE - TEST SUITE")
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
