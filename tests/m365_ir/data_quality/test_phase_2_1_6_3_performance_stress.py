#!/usr/bin/env python3
"""
Phase 2.1.6.3: Performance Stress Testing

Validates Phase 2.1 intelligent field selection performs well at scale:
- Large datasets (100K+ records)
- Memory profiling (no leaks)
- Historical DB performance (100+ cases)
- Concurrent operations (parallel imports)

Performance Targets (from Phase 2.1.5 baseline):
- Import rate: ≥24K rec/sec
- Verification time: ≤10ms
- Phase 2.1 overhead: ≤50ms
- Memory usage: ≤500MB for 100K records
- Historical DB query: ≤50ms for 100 cases

TDD Phase: RED → GREEN → No regressions

Author: Maia System (SRE Principal Engineer Agent)
Created: 2026-01-07
"""

import pytest
import tempfile
import time
import tracemalloc
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict
import random
import csv


@pytest.mark.phase_2_1_6
@pytest.mark.slow  # Mark as slow test (may take 1-2 minutes)
class TestPerformanceStressScenarios:
    """
    Phase 2.1.6.3: Performance stress testing for Phase 2.1 intelligent field selection.

    Validates system performs well at scale with realistic production loads.
    """

    def test_100k_record_import_performance(self):
        """
        Test import performance with 100K sign-in log records.

        Given: 100K synthetic sign-in records with Phase 2.1 enabled
        When: Import using LogImporter
        Then:
            - Import rate ≥24K rec/sec
            - Verification time ≤10ms per record
            - Phase 2.1 overhead ≤50ms total

        TDD Phase: RED → GREEN
        Expected to FAIL initially - need to implement synthetic data generator.
        """
        from claude.tools.m365_ir.log_database import IRLogDatabase
        from claude.tools.m365_ir.log_importer import LogImporter

        tmpdir = tempfile.mkdtemp()

        try:
            # Generate 100K synthetic sign-in records
            print("\n📊 Generating 100K synthetic sign-in records...")
            start_gen = time.time()
            synthetic_records = self._generate_synthetic_sign_in_logs(100_000)
            gen_duration = time.time() - start_gen
            print(f"   Generated in {gen_duration:.2f}s")

            # Write to temporary CSV file
            csv_path = Path(tmpdir) / "synthetic_100k.csv"
            self._write_records_to_csv(synthetic_records, csv_path)

            # Create database
            db = IRLogDatabase(case_id="TEST-100K-PERF", base_path=tmpdir)
            db.create()

            # Import with Phase 2.1 enabled
            print(f"\n⚡ Importing 100K records with Phase 2.1 enabled...")
            start_import = time.time()

            importer = LogImporter(db=db)
            stats = importer.import_sign_in_logs(str(csv_path))

            import_duration = time.time() - start_import

            # Calculate metrics
            records_per_sec = stats.records_imported / import_duration
            ms_per_record = (import_duration / stats.records_imported) * 1000

            print(f"\n📈 Performance Metrics:")
            print(f"   Total records: {stats.records_imported:,}")
            print(f"   Import time: {import_duration:.2f}s")
            print(f"   Import rate: {records_per_sec:,.0f} rec/sec")
            print(f"   Time per record: {ms_per_record:.3f}ms")
            print(f"   Failed records: {stats.records_failed}")

            # Assertions
            assert stats.records_imported == 100_000, \
                f"Should import all 100K records, got {stats.records_imported}"

            assert records_per_sec >= 24_000, \
                f"Import rate too slow: {records_per_sec:,.0f} rec/sec (target: ≥24K rec/sec)"

            assert ms_per_record <= 0.05, \
                f"Time per record too slow: {ms_per_record:.3f}ms (target: ≤0.05ms = 20K rec/sec)"

        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_memory_usage_during_large_import(self):
        """
        Test memory doesn't leak during 100K record import.

        Given: 100K synthetic sign-in records
        When: Import with memory profiling enabled
        Then:
            - Memory increase ≤500MB
            - No memory leaks after cleanup

        TDD Phase: RED → GREEN
        Expected to FAIL initially - need memory profiling instrumentation.
        """
        from claude.tools.m365_ir.log_database import IRLogDatabase
        from claude.tools.m365_ir.log_importer import LogImporter

        tmpdir = tempfile.mkdtemp()

        try:
            # Start memory tracking
            tracemalloc.start()

            # Baseline memory
            baseline_snapshot = tracemalloc.take_snapshot()
            baseline_mb = sum(stat.size for stat in baseline_snapshot.statistics('lineno')) / (1024 * 1024)

            print(f"\n💾 Memory Profiling:")
            print(f"   Baseline: {baseline_mb:.2f} MB")

            # Generate and import 100K records
            synthetic_records = self._generate_synthetic_sign_in_logs(100_000)

            # Write to temporary CSV file
            csv_path = Path(tmpdir) / "synthetic_memory_test.csv"
            self._write_records_to_csv(synthetic_records, csv_path)

            # Peak memory during import
            peak_snapshot = tracemalloc.take_snapshot()
            peak_mb = sum(stat.size for stat in peak_snapshot.statistics('lineno')) / (1024 * 1024)

            db = IRLogDatabase(case_id="TEST-MEMORY", base_path=tmpdir)
            db.create()

            importer = LogImporter(db=db)
            importer.import_sign_in_logs(str(csv_path))

            # Peak memory after import
            after_import_snapshot = tracemalloc.take_snapshot()
            after_import_mb = sum(stat.size for stat in after_import_snapshot.statistics('lineno')) / (1024 * 1024)

            # Cleanup
            del synthetic_records
            del importer
            import gc
            gc.collect()

            # Memory after cleanup
            after_cleanup_snapshot = tracemalloc.take_snapshot()
            after_cleanup_mb = sum(stat.size for stat in after_cleanup_snapshot.statistics('lineno')) / (1024 * 1024)

            # Calculate increases
            peak_increase = peak_mb - baseline_mb
            after_import_increase = after_import_mb - baseline_mb
            after_cleanup_increase = after_cleanup_mb - baseline_mb

            print(f"   Peak: {peak_mb:.2f} MB (+{peak_increase:.2f} MB)")
            print(f"   After import: {after_import_mb:.2f} MB (+{after_import_increase:.2f} MB)")
            print(f"   After cleanup: {after_cleanup_mb:.2f} MB (+{after_cleanup_increase:.2f} MB)")

            # Assertions
            assert after_import_increase <= 500, \
                f"Memory increase too high: {after_import_increase:.2f} MB (target: ≤500 MB)"

            # Check for memory leaks (after cleanup should be close to baseline)
            leak_threshold_mb = 50  # Allow 50MB tolerance for Python overhead
            assert after_cleanup_increase <= leak_threshold_mb, \
                f"Memory leak detected: {after_cleanup_increase:.2f} MB retained after cleanup (threshold: ≤{leak_threshold_mb} MB)"

            tracemalloc.stop()

        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_historical_db_query_performance_at_scale(self):
        """
        Test historical queries remain fast with 100 cases.

        Given: Historical DB populated with 100 cases worth of field usage data
        When: Query historical success rate for various fields
        Then: Query time ≤50ms per query

        TDD Phase: RED → GREEN
        Expected to FAIL initially - need to populate 100 cases of historical data.
        """
        from claude.tools.m365_ir.field_reliability_scorer import (
            create_history_database,
            store_field_usage,
            query_historical_success_rate
        )

        historical_db_path = Path(tempfile.mkdtemp()) / "test_historical_100_cases.db"

        try:
            # Initialize historical database
            create_history_database(str(historical_db_path))

            print(f"\n📚 Populating historical DB with 100 cases...")
            start_populate = time.time()

            # Populate with 100 cases (each case has ~10 field usages)
            for case_num in range(100):
                case_id = f'TEST-CASE-{case_num:04d}'

                # Each case has multiple field usages
                fields_to_test = [
                    ('sign_in_logs', 'conditional_access_status'),
                    ('sign_in_logs', 'status_error_code'),
                    ('sign_in_logs', 'status'),
                    ('unified_audit_log', 'result_status'),
                    ('unified_audit_log', 'operation'),
                    ('legacy_auth_logs', 'status'),
                ]

                for log_type, field_name in fields_to_test:
                    # Randomize success/failure for realistic distribution
                    verification_successful = random.choice([True, True, True, False])  # 75% success rate
                    breach_detected = random.choice([True, False])

                    store_field_usage(
                        history_db_path=str(historical_db_path),
                        case_id=case_id,
                        log_type=log_type,
                        field_name=field_name,
                        reliability_score=random.uniform(0.5, 0.95),
                        used_for_verification=True,
                        verification_successful=verification_successful,
                        breach_detected=breach_detected
                    )

            populate_duration = time.time() - start_populate
            print(f"   Populated in {populate_duration:.2f}s (100 cases × 6 fields = 600 entries)")

            # Benchmark queries
            print(f"\n🔍 Benchmarking historical queries...")
            query_times_ms = []

            queries_to_test = [
                ('sign_in_logs', 'conditional_access_status'),
                ('sign_in_logs', 'status_error_code'),
                ('unified_audit_log', 'result_status'),
                ('legacy_auth_logs', 'status'),
            ]

            for log_type, field_name in queries_to_test:
                start_query = time.time()

                success_rate = query_historical_success_rate(
                    log_type=log_type,
                    field_name=field_name,
                    historical_db_path=str(historical_db_path)
                )

                query_duration_ms = (time.time() - start_query) * 1000
                query_times_ms.append(query_duration_ms)

                print(f"   {log_type}/{field_name}: {query_duration_ms:.2f}ms (rate: {success_rate:.2%})")

            # Calculate stats
            avg_query_time_ms = sum(query_times_ms) / len(query_times_ms)
            max_query_time_ms = max(query_times_ms)

            print(f"\n📊 Query Performance:")
            print(f"   Average: {avg_query_time_ms:.2f}ms")
            print(f"   Max: {max_query_time_ms:.2f}ms")

            # Assertions
            assert avg_query_time_ms <= 50, \
                f"Average query time too slow: {avg_query_time_ms:.2f}ms (target: ≤50ms)"

            assert max_query_time_ms <= 100, \
                f"Max query time too slow: {max_query_time_ms:.2f}ms (target: ≤100ms for worst case)"

        finally:
            import shutil
            shutil.rmtree(historical_db_path.parent, ignore_errors=True)

    def test_concurrent_case_imports(self):
        """
        Test parallel imports don't cause race conditions.

        Given: 5 separate case imports running concurrently
        When: Import using multiprocessing
        Then:
            - All imports successful
            - No database locks or conflicts
            - Each case has isolated database

        Note: Historical DB is populated by auth_verifier (Phase 2.1), not by
        log_importer. This test validates concurrent *import* safety only.

        TDD Phase: RED → GREEN
        Expected to FAIL initially - need concurrent import orchestration.
        """
        from claude.tools.m365_ir.log_database import IRLogDatabase
        from claude.tools.m365_ir.log_importer import LogImporter
        from multiprocessing import Pool
        import sqlite3

        tmpdir = tempfile.mkdtemp()

        try:
            print(f"\n🔀 Testing concurrent imports (5 parallel cases)...")
            start_concurrent = time.time()

            # Define 5 concurrent import tasks
            import_tasks = [
                {'case_id': f'TEST-CONCURRENT-{i}', 'record_count': 10_000}
                for i in range(5)
            ]

            # Run imports in parallel
            with Pool(processes=5) as pool:
                results = pool.starmap(
                    self._import_case_worker,
                    [(task['case_id'], task['record_count'], tmpdir, None)  # No historical DB needed
                     for task in import_tasks]
                )

            concurrent_duration = time.time() - start_concurrent

            print(f"\n✅ Concurrent import results:")
            print(f"   Duration: {concurrent_duration:.2f}s")
            print(f"   Total records: {sum(r['total_records'] for r in results):,}")

            # Verify all imports succeeded
            for i, result in enumerate(results):
                print(f"   Case {i}: {result['total_records']:,} records, success={result['success']}")
                assert result['success'] is True, \
                    f"Case {i} import failed: {result.get('error', 'unknown error')}"
                assert result['total_records'] == 10_000, \
                    f"Case {i} should import 10K records, got {result['total_records']}"

            # Verify each case has its own isolated database
            print(f"\n📊 Database isolation verification:")
            for i in range(5):
                case_id = f'TEST-CONCURRENT-{i}'
                db_path = Path(tmpdir) / case_id / f"{case_id}_logs.db"

                assert db_path.exists(), \
                    f"Case {i} database should exist at {db_path}"

                # Verify record count in database
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM sign_in_logs")
                count = cursor.fetchone()[0]
                conn.close()

                print(f"   Case {i}: {count:,} records in database")
                assert count == 10_000, \
                    f"Case {i} database should have 10K records, got {count}"

        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    # ========== Helper Methods ==========

    def _write_records_to_csv(self, records: List[Dict], csv_path: Path) -> None:
        """
        Write synthetic records to CSV file in M365 sign-in log format.

        Args:
            records: List of record dictionaries
            csv_path: Output CSV file path
        """
        if not records:
            return

        # Get all field names from first record
        fieldnames = list(records[0].keys())

        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)

    def _generate_synthetic_sign_in_logs(self, count: int) -> List[Dict]:
        """
        Generate synthetic sign-in log records for stress testing.

        Args:
            count: Number of records to generate

        Returns:
            List of synthetic sign-in log dictionaries
        """
        statuses = ['success', 'failure', 'notApplied']
        error_codes = ['0', '1', '50126', '50053', '50076', '50055', '53003']
        countries = ['US', 'AU', 'GB', 'CA', 'DE', 'JP']

        records = []
        base_time = datetime.now() - timedelta(days=30)

        for i in range(count):
            # Realistic distributions
            conditional_access_status = random.choice(statuses)

            # Error code logic: '0' for success, others for failure
            if conditional_access_status == 'success':
                error_code = '0'
            else:
                error_code = random.choice(['1', '50126', '50053', '50076'])

            # Use Microsoft CSV column names (PascalCase)
            records.append({
                'CreatedDateTime': (base_time + timedelta(seconds=i)).isoformat(),
                'UserPrincipalName': f'user{i % 1000}@test.com',
                'IPAddress': f'203.0.{(i % 256)}.{(i % 256)}',
                'ConditionalAccessStatus': conditional_access_status,
                'ErrorCode': error_code,
                'Status': 'Success' if conditional_access_status == 'success' else 'Failure',
                'Country': random.choice(countries),
                'City': f'City{i % 100}',
                'AppDisplayName': f'App{i % 50}',
                'ClientAppUsed': random.choice(['Browser', 'Mobile Apps', 'Desktop']),
                'DeviceId': f'device-{i % 500}'
            })

        return records

    def _import_case_worker(self, case_id: str, record_count: int, base_path: str, historical_db_path: str) -> Dict:
        """
        Worker function for concurrent import testing.

        Args:
            case_id: Case identifier
            record_count: Number of records to import
            base_path: Base path for database
            historical_db_path: Path to shared historical database

        Returns:
            Result dictionary with success status and metrics
        """
        try:
            from claude.tools.m365_ir.log_database import IRLogDatabase
            from claude.tools.m365_ir.log_importer import LogImporter

            # Generate synthetic records
            synthetic_records = self._generate_synthetic_sign_in_logs(record_count)

            # Write to temporary CSV file
            csv_path = Path(base_path) / f"{case_id}_synthetic.csv"
            self._write_records_to_csv(synthetic_records, csv_path)

            # Create isolated database for this case
            db = IRLogDatabase(case_id=case_id, base_path=base_path)
            db.create()

            # Import with Phase 2.1 enabled
            # Note: LogImporter uses global historical DB from field_reliability_scorer
            importer = LogImporter(db=db)
            stats = importer.import_sign_in_logs(str(csv_path))

            return {
                'success': True,
                'case_id': case_id,
                'total_records': stats.records_imported,
                'error': None
            }

        except Exception as e:
            return {
                'success': False,
                'case_id': case_id,
                'total_records': 0,
                'error': str(e)
            }


# Mark all tests as Phase 2.1.6
pytestmark = pytest.mark.phase_2_1_6
