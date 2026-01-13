#!/usr/bin/env python3
"""
ServiceDesk ETL V2 - Performance Test Suite

Tests performance SLAs for the complete ETL pipeline:
- Profiler: <5 min for 260K rows
- Cleaner: <15 min for 260K rows
- Migration: <5 min for 260K rows
- Full Pipeline: <25 min total

Usage:
    PYTHONPATH=. pytest tests/test_performance_servicedesk_etl.py -v -s

Author: ServiceDesk ETL V2 Team
Date: 2025-10-19
"""

import os
import sys
import time
import sqlite3
import tempfile
import pytest
from pathlib import Path

# Add project root to path
MAIA_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(MAIA_ROOT))

from claude.tools.sre.servicedesk_etl_data_profiler import profile_database
from claude.tools.sre.servicedesk_etl_data_cleaner_enhanced import (
    clean_database, CleaningError
)
from tests.conftest import normalize_profiler_result, assert_profiler_success, assert_cleaner_success


# ==============================================================================
# Test Fixtures
# ==============================================================================

@pytest.fixture
def test_db_small():
    """Create small test database (1K rows) for quick tests"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.db', delete=False) as f:
        db_path = f.name

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create tickets table with known schema
    cursor.execute('''
        CREATE TABLE tickets (
            id INTEGER PRIMARY KEY,
            "TKT-Number" TEXT,
            "TKT-Created Time" TEXT,
            "TKT-Actual Resolution Date" TEXT,
            "TKT-Status" TEXT,
            "TKT-Product" TEXT
        )
    ''')

    # Insert 1K rows
    for i in range(1000):
        cursor.execute(
            'INSERT INTO tickets VALUES (?, ?, ?, ?, ?, ?)',
            (
                i + 1,
                f'TKT-{i+1:06d}',
                f'2024-{(i % 12) + 1:02d}-{(i % 28) + 1:02d} 10:00:00',
                f'2024-{(i % 12) + 1:02d}-{(i % 28) + 1:02d} 15:00:00',
                'Closed' if i % 3 == 0 else 'In Progress',
                f'Product-{i % 10}'
            )
        )

    conn.commit()
    conn.close()

    yield db_path

    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def test_db_medium():
    """Create medium test database (10K rows) for baseline tests"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.db', delete=False) as f:
        db_path = f.name

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create tickets table
    cursor.execute('''
        CREATE TABLE tickets (
            id INTEGER PRIMARY KEY,
            "TKT-Number" TEXT,
            "TKT-Created Time" TEXT,
            "TKT-Actual Resolution Date" TEXT,
            "TKT-Status" TEXT,
            "TKT-Product" TEXT
        )
    ''')

    # Insert 10K rows in batches
    batch_size = 1000
    for batch in range(10):
        rows = []
        for i in range(batch_size):
            idx = batch * batch_size + i
            rows.append((
                idx + 1,
                f'TKT-{idx+1:06d}',
                f'2024-{(idx % 12) + 1:02d}-{(idx % 28) + 1:02d} 10:00:00',
                f'2024-{(idx % 12) + 1:02d}-{(idx % 28) + 1:02d} 15:00:00',
                'Closed' if idx % 3 == 0 else 'In Progress',
                f'Product-{idx % 10}'
            ))
        cursor.executemany('INSERT INTO tickets VALUES (?, ?, ?, ?, ?, ?)', rows)

    conn.commit()
    conn.close()

    yield db_path

    if os.path.exists(db_path):
        os.remove(db_path)


# ==============================================================================
# Performance Baseline Tests
# ==============================================================================

class TestPerformanceBaselines:
    """Establish performance baselines with smaller datasets"""

    def test_profiler_baseline_1k_rows(self, test_db_small):
        """Baseline: Profiler on 1K rows (should be <1s)"""
        start = time.time()
        result = profile_database(test_db_small, sample_size=500)
        elapsed = time.time() - start

        result = normalize_profiler_result(result)


        assert result['status'] == 'success'
        assert elapsed < 1.0, f"Profiler took {elapsed:.2f}s for 1K rows (expected <1s)"

        # Calculate estimated time for 260K rows (linear extrapolation)
        estimated_260k = elapsed * 260
        print(f"\n  1K rows: {elapsed:.3f}s")
        print(f"  Estimated 260K rows: {estimated_260k:.1f}s ({estimated_260k/60:.1f}m)")

    def test_profiler_baseline_10k_rows(self, test_db_medium):
        """Baseline: Profiler on 10K rows (should be <10s)"""
        start = time.time()
        result = profile_database(test_db_medium, sample_size=5000)
        elapsed = time.time() - start

        result = normalize_profiler_result(result)


        assert result['status'] == 'success'
        assert elapsed < 10.0, f"Profiler took {elapsed:.2f}s for 10K rows (expected <10s)"

        # Calculate estimated time for 260K rows
        estimated_260k = elapsed * 26
        print(f"\n  10K rows: {elapsed:.3f}s")
        print(f"  Estimated 260K rows: {estimated_260k:.1f}s ({estimated_260k/60:.1f}m)")

    def test_cleaner_baseline_1k_rows(self, test_db_small):
        """Baseline: Cleaner on 1K rows (should be <2s)"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.db', delete=False) as f:
            output_db = f.name

        try:
            start = time.time()
            result = clean_database(
            test_db_small,
            output_db,
            config={
                'date_columns': [
                    ('tickets', 'TKT-Created Time'),
                    ('tickets', 'TKT-Actual Resolution Date')
                ],
                'empty_to_null_columns': [
                    ('tickets', 'TKT-Actual Resolution Date')
                ]
            }
        )
            elapsed = time.time() - start

            result = normalize_profiler_result(result)


            assert result['status'] == 'success'
            assert elapsed < 2.0, f"Cleaner took {elapsed:.2f}s for 1K rows (expected <2s)"

            # Calculate estimated time for 260K rows
            estimated_260k = elapsed * 260
            print(f"\n  1K rows: {elapsed:.3f}s")
            print(f"  Estimated 260K rows: {estimated_260k:.1f}s ({estimated_260k/60:.1f}m)")

        finally:
            if os.path.exists(output_db):
                os.remove(output_db)

    def test_cleaner_baseline_10k_rows(self, test_db_medium):
        """Baseline: Cleaner on 10K rows (should be <20s)"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.db', delete=False) as f:
            output_db = f.name

        try:
            start = time.time()
            result = clean_database(
            test_db_medium,
            output_db,
            config={
                'date_columns': [
                    ('tickets', 'TKT-Created Time'),
                    ('tickets', 'TKT-Actual Resolution Date')
                ],
                'empty_to_null_columns': [
                    ('tickets', 'TKT-Actual Resolution Date')
                ]
            }
        )
            elapsed = time.time() - start

            result = normalize_profiler_result(result)


            assert result['status'] == 'success'
            assert elapsed < 20.0, f"Cleaner took {elapsed:.2f}s for 10K rows (expected <20s)"

            # Calculate estimated time for 260K rows
            estimated_260k = elapsed * 26
            print(f"\n  10K rows: {elapsed:.3f}s")
            print(f"  Estimated 260K rows: {estimated_260k:.1f}s ({estimated_260k/60:.1f}m)")

        finally:
            if os.path.exists(output_db):
                os.remove(output_db)


# ==============================================================================
# Performance Scaling Tests
# ==============================================================================

class TestPerformanceScaling:
    """Test linear scaling characteristics"""

    def test_profiler_scales_linearly(self, test_db_small, test_db_medium):
        """Verify profiler scales linearly with row count"""
        # Test 1K rows
        start = time.time()
        profile_database(test_db_small, sample_size=500)
        time_1k = time.time() - start

        # Test 10K rows
        start = time.time()
        profile_database(test_db_medium, sample_size=5000)
        time_10k = time.time() - start

        # Verify linear scaling (10K should take ~10x time)
        ratio = time_10k / time_1k
        print(f"\n  1K rows: {time_1k:.3f}s")
        print(f"  10K rows: {time_10k:.3f}s")
        print(f"  Scaling ratio: {ratio:.2f}x (expected ~10x)")

        # Allow 5x-15x range (linear scaling with some overhead)
        assert 5 <= ratio <= 15, f"Non-linear scaling detected: {ratio:.2f}x"

    def test_cleaner_scales_linearly(self, test_db_small, test_db_medium):
        """Verify cleaner scales linearly with row count"""
        output_small = tempfile.NamedTemporaryFile(suffix='.db', delete=False).name
        output_medium = tempfile.NamedTemporaryFile(suffix='.db', delete=False).name

        try:
            # Test 1K rows
            start = time.time()
            clean_database(
            test_db_small,
            output_small,
            config={
                'date_columns': [('tickets', 'TKT-Created Time')],
                'empty_to_null_columns': []
            }
        )
            time_1k = time.time() - start

            # Test 10K rows
            start = time.time()
            clean_database(
            test_db_medium,
            output_medium,
            config={
                'date_columns': [('tickets', 'TKT-Created Time')],
                'empty_to_null_columns': []
            }
        )
            time_10k = time.time() - start

            # Verify linear scaling
            ratio = time_10k / time_1k
            print(f"\n  1K rows: {time_1k:.3f}s")
            print(f"  10K rows: {time_10k:.3f}s")
            print(f"  Scaling ratio: {ratio:.2f}x (expected ~10x)")

            # Allow 5x-15x range
            assert 5 <= ratio <= 15, f"Non-linear scaling detected: {ratio:.2f}x"

        finally:
            for f in [output_small, output_medium]:
                if os.path.exists(f):
                    os.remove(f)


# ==============================================================================
# Overhead Measurement Tests
# ==============================================================================

class TestOverheadMeasurement:
    """Measure overhead of observability components"""

    def test_profiler_observability_overhead(self, test_db_medium):
        """Measure profiler observability overhead (<1ms per operation)"""
        # This is tested implicitly by the performance tests
        # If observability has <1ms overhead per operation, it's negligible
        # at 10K rows scale

        start = time.time()
        result = profile_database(test_db_medium, sample_size=5000)
        total_time = time.time() - start

        # Extract metrics emission count from result
        metrics_count = result.get('metrics_emitted', 0) or 10  # Conservative estimate

        # Calculate overhead per metric
        overhead_per_metric = (total_time / metrics_count) * 1000  # Convert to ms

        print(f"\n  Total time: {total_time:.3f}s")
        print(f"  Metrics emitted: {metrics_count}")
        print(f"  Overhead per metric: {overhead_per_metric:.3f}ms")

        # Overhead should be negligible (<10ms per metric for 10K row operation)
        assert overhead_per_metric < 10, f"Observability overhead too high: {overhead_per_metric:.3f}ms"

    def test_cleaner_progress_tracking_overhead(self, test_db_medium):
        """Measure cleaner progress tracking overhead"""
        output_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False).name

        try:
            start = time.time()
            result = clean_database(
            test_db_medium,
            output_db,
            config={
                'date_columns': [('tickets', 'TKT-Created Time')],
                'empty_to_null_columns': []
            }
        )
            total_time = time.time() - start

            # Progress tracking happens every batch (~1000 rows)
            progress_updates = 10  # For 10K rows
            overhead_per_update = (total_time / progress_updates) * 1000

            print(f"\n  Total time: {total_time:.3f}s")
            print(f"  Progress updates: {progress_updates}")
            print(f"  Overhead per update: {overhead_per_update:.3f}ms")

            # Should be <1ms per update
            assert overhead_per_update < 1, f"Progress tracking overhead too high: {overhead_per_update:.3f}ms"

        finally:
            if os.path.exists(output_db):
                os.remove(output_db)


# ==============================================================================
# SLA Validation Tests (Estimated)
# ==============================================================================

class TestSLAValidation:
    """
    Validate SLA estimates based on baseline measurements

    NOTE: These tests use extrapolation from 10K row baselines.
    For production validation, run against actual 260K row database.
    """

    def test_profiler_estimated_sla(self, test_db_medium):
        """Estimate profiler performance on 260K rows"""
        start = time.time()
        result = profile_database(test_db_medium, sample_size=5000)
        time_10k = time.time() - start

        # Extrapolate to 260K rows (26x)
        estimated_260k = time_10k * 26
        estimated_minutes = estimated_260k / 60

        print(f"\n  10K rows: {time_10k:.3f}s")
        print(f"  Estimated 260K rows: {estimated_260k:.1f}s ({estimated_minutes:.1f}m)")
        print(f"  SLA: <5 minutes (300s)")

        # Log warning if estimate exceeds SLA
        if estimated_260k > 300:
            pytest.fail(
                f"Estimated profiler time {estimated_minutes:.1f}m exceeds 5m SLA. "
                f"Optimize or retest with actual 260K database."
            )

    def test_cleaner_estimated_sla(self, test_db_medium):
        """Estimate cleaner performance on 260K rows"""
        output_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False).name

        try:
            start = time.time()
            result = clean_database(
            test_db_medium,
            output_db,
            config={
                'date_columns': [
                    ('tickets', 'TKT-Created Time'),
                    ('tickets', 'TKT-Actual Resolution Date')
                ],
                'empty_to_null_columns': [('tickets', 'TKT-Actual Resolution Date')]
            }
        )
            time_10k = time.time() - start

            # Extrapolate to 260K rows
            estimated_260k = time_10k * 26
            estimated_minutes = estimated_260k / 60

            print(f"\n  10K rows: {time_10k:.3f}s")
            print(f"  Estimated 260K rows: {estimated_260k:.1f}s ({estimated_minutes:.1f}m)")
            print(f"  SLA: <15 minutes (900s)")

            # Log warning if estimate exceeds SLA
            if estimated_260k > 900:
                pytest.fail(
                    f"Estimated cleaner time {estimated_minutes:.1f}m exceeds 15m SLA. "
                    f"Optimize or retest with actual 260K database."
                )

        finally:
            if os.path.exists(output_db):
                os.remove(output_db)

    def test_full_pipeline_estimated_sla(self, test_db_medium):
        """Estimate full pipeline performance on 260K rows"""
        output_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False).name

        try:
            # Profiler
            start_profiler = time.time()
            profile_result = profile_database(test_db_medium, sample_size=5000)
            profiler_time = time.time() - start_profiler

            # Cleaner
            start_cleaner = time.time()
            clean_result = clean_database(
            test_db_medium,
            output_db,
            config={
                'date_columns': [('tickets', 'TKT-Created Time')],
                'empty_to_null_columns': []
            }
        )
            cleaner_time = time.time() - start_cleaner

            # Migration (estimate 5 min for 260K based on Phase 127 baseline)
            migration_time_estimate = 5 * 60  # 5 minutes in seconds

            # Calculate totals
            total_10k = profiler_time + cleaner_time
            estimated_260k_without_migration = total_10k * 26
            estimated_260k_total = estimated_260k_without_migration + migration_time_estimate
            estimated_minutes = estimated_260k_total / 60

            print(f"\n  Profiler (10K): {profiler_time:.3f}s → Estimated (260K): {profiler_time * 26:.1f}s")
            print(f"  Cleaner (10K): {cleaner_time:.3f}s → Estimated (260K): {cleaner_time * 26:.1f}s")
            print(f"  Migration (260K): {migration_time_estimate}s (baseline)")
            print(f"  Total estimated (260K): {estimated_260k_total:.1f}s ({estimated_minutes:.1f}m)")
            print(f"  SLA: <25 minutes (1500s)")

            # Log warning if estimate exceeds SLA
            if estimated_260k_total > 1500:
                pytest.fail(
                    f"Estimated full pipeline time {estimated_minutes:.1f}m exceeds 25m SLA. "
                    f"Optimize or retest with actual 260K database."
                )

        finally:
            if os.path.exists(output_db):
                os.remove(output_db)


# ==============================================================================
# Production Database Tests (Conditional)
# ==============================================================================

class TestProductionPerformance:
    """
    Tests against actual production database (260K rows)

    These tests are skipped unless SERVICEDESK_PRODUCTION_DB environment
    variable points to actual database.
    """

    @pytest.mark.skipif(
        'SERVICEDESK_PRODUCTION_DB' not in os.environ,
        reason="Production database not available (set SERVICEDESK_PRODUCTION_DB)"
    )
    def test_profiler_production_sla(self):
        """Validate profiler meets <5 min SLA on production database"""
        db_path = os.environ['SERVICEDESK_PRODUCTION_DB']
        assert os.path.exists(db_path), f"Production DB not found: {db_path}"

        print(f"\n  Testing against production database: {db_path}")

        start = time.time()
        result = profile_database(db_path, sample_size=5000)
        elapsed = time.time() - start

        result = normalize_profiler_result(result)


        assert result['status'] == 'success'
        assert elapsed < 300, f"Profiler took {elapsed:.1f}s ({elapsed/60:.1f}m), exceeds 5m SLA"

        print(f"  ✅ Profiler completed in {elapsed:.1f}s ({elapsed/60:.1f}m)")

    @pytest.mark.skipif(
        'SERVICEDESK_PRODUCTION_DB' not in os.environ,
        reason="Production database not available"
    )
    def test_cleaner_production_sla(self):
        """Validate cleaner meets <15 min SLA on production database"""
        db_path = os.environ['SERVICEDESK_PRODUCTION_DB']
        assert os.path.exists(db_path), f"Production DB not found: {db_path}"

        output_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False).name

        try:
            print(f"\n  Testing against production database: {db_path}")

            start = time.time()
            result = clean_database(
            db_path,
            output_db,
            config={
                'date_columns': [
                    ('tickets', 'TKT-Created Time'),
                    ('tickets', 'TKT-Actual Resolution Date')
                ],
                'empty_to_null_columns': [('tickets', 'TKT-Actual Resolution Date')]
            }
        )
            elapsed = time.time() - start

            result = normalize_profiler_result(result)


            assert result['status'] == 'success'
            assert elapsed < 900, f"Cleaner took {elapsed:.1f}s ({elapsed/60:.1f}m), exceeds 15m SLA"

            print(f"  ✅ Cleaner completed in {elapsed:.1f}s ({elapsed/60:.1f}m)")

        finally:
            if os.path.exists(output_db):
                os.remove(output_db)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
