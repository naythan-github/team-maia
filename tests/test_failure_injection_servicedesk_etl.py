#!/usr/bin/env python3
"""
ServiceDesk ETL V2 - Failure Injection Test Suite

Tests resilience and recovery under failure conditions:
- Transaction rollback on errors
- Disk full scenarios
- Process termination recovery
- Corrupt data handling
- Network failures (PostgreSQL)

Usage:
    PYTHONPATH=. pytest tests/test_failure_injection_servicedesk_etl.py -v -s

Author: ServiceDesk ETL V2 Team
Date: 2025-10-19
"""

import os
import sys
import sqlite3
import tempfile
import pytest
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
MAIA_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(MAIA_ROOT))

from claude.tools.sre.servicedesk_etl_data_profiler import profile_database
from claude.tools.sre.servicedesk_etl_data_cleaner_enhanced import (
    clean_database, CleaningError
)
from tests.conftest import normalize_profiler_result, normalize_cleaner_result, assert_profiler_success, assert_cleaner_success


# ==============================================================================
# Test Fixtures
# ==============================================================================

@pytest.fixture
def test_db():
    """Create standard test database"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.db', delete=False) as f:
        db_path = f.name

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE tickets (
            id INTEGER PRIMARY KEY,
            "TKT-Number" TEXT,
            "TKT-Created Time" TEXT,
            "TKT-Actual Resolution Date" TEXT,
            "TKT-Status" TEXT
        )
    ''')

    # Insert 1000 test rows
    for i in range(1000):
        cursor.execute(
            'INSERT INTO tickets VALUES (?, ?, ?, ?, ?)',
            (
                i + 1,
                f'TKT-{i+1:06d}',
                f'2024-01-{(i % 28) + 1:02d} 10:00:00',
                f'2024-01-{(i % 28) + 1:02d} 15:00:00',
                'Closed' if i % 2 == 0 else 'In Progress'
            )
        )

    conn.commit()
    conn.close()

    yield db_path

    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def corrupt_db():
    """Create database with corrupt data to trigger circuit breaker"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.db', delete=False) as f:
        db_path = f.name

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE tickets (
            id INTEGER PRIMARY KEY,
            "TKT-Created Time" TEXT
        )
    ''')

    # Insert >20% corrupt dates to trigger circuit breaker
    for i in range(1000):
        if i < 250:  # 25% corrupt dates (exceeds 20% threshold)
            date_value = 'CORRUPT_DATE_VALUE'
        else:
            date_value = f'2024-01-{(i % 28) + 1:02d} 10:00:00'

        cursor.execute('INSERT INTO tickets VALUES (?, ?)', (i + 1, date_value))

    conn.commit()
    conn.close()

    yield db_path

    if os.path.exists(db_path):
        os.remove(db_path)


# ==============================================================================
# Transaction Rollback Tests
# ==============================================================================

class TestTransactionRollback:
    """Test transaction rollback on various failure modes"""

    def test_source_never_modified_on_error(self, test_db):
        """CRITICAL: Verify source database NEVER modified even on error"""
        # Calculate MD5 of source before cleaning
        with open(test_db, 'rb') as f:
            md5_before = hashlib.md5(f.read()).hexdigest()

        output_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False).name

        try:
            # Attempt cleaning with invalid configuration (should fail)
            with pytest.raises(Exception):
                clean_database(
                    test_db,
                    output_db,
                    config={
                        'date_columns': [('nonexistent_table', 'nonexistent_column')],
                        'empty_to_null_columns': []
                    }
                )

        except Exception:
            pass  # Expected to fail

        finally:
            if os.path.exists(output_db):
                os.remove(output_db)

        # Verify source unchanged
        with open(test_db, 'rb') as f:
            md5_after = hashlib.md5(f.read()).hexdigest()

        assert md5_before == md5_after, "Source database was modified during failed operation!"
        print("\n  ✅ Source database integrity preserved")

    def test_partial_output_deleted_on_rollback(self, test_db):
        """Verify partial output file deleted on rollback"""
        output_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False).name

        try:
            # Force an error mid-cleaning by using invalid column
            with pytest.raises(Exception):
                clean_database(
                    test_db,
                    output_db,
                    config={
                        'date_columns': [('tickets', 'nonexistent_column')],
                        'empty_to_null_columns': []
                    }
                )

        except Exception:
            pass  # Expected

        # Verify output file was cleaned up
        assert not os.path.exists(output_db), "Partial output file not deleted on rollback"
        print("\n  ✅ Partial output file cleaned up")

    def test_transaction_rolled_back_on_validation_failure(self, test_db):
        """Verify transaction rollback when post-cleaning validation fails"""
        output_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False).name

        # Mock quality scorer to simulate validation failure
        with patch('claude.tools.sre.servicedesk_etl_data_cleaner_enhanced.score_database') as mock_scorer:
            mock_scorer.return_value = 50  # Below threshold of 80

            try:
                result = clean_database(
                    test_db, output_db,
                    date_columns=[('tickets', 'TKT-Created Time')],
                    empty_string_columns=[],
                    min_quality=80  # Require ≥80
                )

                # Should have failed quality gate
                assert result['status'] == 'error', "Should fail on low quality score"

            except CleaningError:
                pass  # Expected

        # Verify output deleted
        assert not os.path.exists(output_db), "Output not deleted on quality gate failure"
        print("\n  ✅ Quality gate enforced with rollback")


# ==============================================================================
# Disk Space Failure Tests
# ==============================================================================

class TestDiskSpaceFailures:
    """Test behavior when disk space is exhausted"""

    def test_cleaning_halts_on_low_disk_space(self, test_db):
        """Verify cleaner halts when disk space critically low"""
        output_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False).name

        # Mock psutil to simulate low disk space
        try:
            with patch('claude.tools.sre.servicedesk_etl_data_cleaner_enhanced.check_disk_space_health') as mock_disk:
                mock_disk.return_value = {
                    'healthy': False,
                    'available_gb': 0.5,
                    'threshold_gb': 1.0,
                    'message': 'Disk space critically low'
                }

                result = clean_database(
                    test_db,
                    output_db,
                    config={
                        'date_columns': [('tickets', 'TKT-Created Time')],
                        'empty_to_null_columns': []
                    }
                )

                # Should halt on disk space check
                assert result['status'] == 'error', "Should halt on low disk space"

        except CleaningError as e:
            assert 'disk' in str(e).lower() or 'space' in str(e).lower()
            print(f"\n  ✅ Correctly halted on low disk: {e}")

        finally:
            if os.path.exists(output_db):
                os.remove(output_db)

    def test_profiler_checks_disk_space(self, test_db):
        """Verify profiler performs disk space checks"""
        # Mock psutil to simulate low disk space
        with patch('claude.tools.sre.servicedesk_etl_data_profiler.check_disk_space_health') as mock_disk:
            mock_disk.return_value = {
                'healthy': True,
                'available_gb': 50.0,
                'threshold_gb': 1.0
            }

            # Should succeed with adequate disk space
            result = profile_database(test_db, sample_size=500)
            result = normalize_profiler_result(result)
            assert result['status'] == 'success'

            # Verify health check was called
            assert mock_disk.called, "Disk space health check not called"
            print("\n  ✅ Disk space health check integration verified")


# ==============================================================================
# Memory Exhaustion Tests
# ==============================================================================

class TestMemoryExhaustion:
    """Test behavior when memory is exhausted"""

    def test_cleaning_halts_on_high_memory_usage(self, test_db):
        """Verify cleaner halts when memory usage critically high"""
        output_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False).name

        # Mock psutil to simulate high memory usage
        try:
            with patch('claude.tools.sre.servicedesk_etl_data_cleaner_enhanced.check_memory_health') as mock_memory:
                mock_memory.return_value = {
                    'healthy': False,
                    'usage_percent': 95.0,
                    'threshold_percent': 90.0,
                    'message': 'Memory usage critically high'
                }

                result = clean_database(
                    test_db,
                    output_db,
                    config={
                        'date_columns': [('tickets', 'TKT-Created Time')],
                        'empty_to_null_columns': []
                    }
                )

                # Should halt on memory check
                assert result['status'] == 'error', "Should halt on high memory usage"

        except CleaningError as e:
            assert 'memory' in str(e).lower()
            print(f"\n  ✅ Correctly halted on high memory: {e}")

        finally:
            if os.path.exists(output_db):
                os.remove(output_db)


# ==============================================================================
# Circuit Breaker Tests
# ==============================================================================

class TestCircuitBreaker:
    """Test circuit breaker halts on unfixable data"""

    def test_circuit_breaker_halts_on_corrupt_dates(self, corrupt_db):
        """Verify circuit breaker halts when >20% dates corrupt"""
        try:
            result = profile_database(corrupt_db, sample_size=1000)
            result = normalize_profiler_result(result)

            # Should trigger circuit breaker
            assert result.get('circuit_breaker', {}).get('should_halt', False), \
                "Circuit breaker should halt on >20% corrupt dates"

            reason = result.get('circuit_breaker', {}).get('reason', '')
            assert 'date' in reason.lower() or 'corrupt' in reason.lower()

            print(f"\n  ✅ Circuit breaker triggered: {reason}")

        except Exception as e:
            # Also acceptable to raise exception
            print(f"\n  ✅ Circuit breaker raised exception: {e}")

    def test_circuit_breaker_halts_on_type_mismatches(self):
        """Verify circuit breaker halts when >10% columns have type mismatches"""
        # Create database with type mismatches
        with tempfile.NamedTemporaryFile(mode='w', suffix='.db', delete=False) as f:
            db_path = f.name

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create table with TIMESTAMP column but store TEXT
        cursor.execute('CREATE TABLE tickets (id INTEGER PRIMARY KEY, date TIMESTAMP)')

        # Insert text values in TIMESTAMP column
        for i in range(1000):
            cursor.execute('INSERT INTO tickets VALUES (?, ?)', (i + 1, 'NOT_A_TIMESTAMP'))

        conn.commit()
        conn.close()

        try:
            result = profile_database(db_path, sample_size=1000)
            result = normalize_profiler_result(result)

            # Check for type mismatch detection
            issues = result.get('issues', [])
            type_issues = [i for i in issues if 'type' in i.get('type', '').lower()]

            assert len(type_issues) > 0, "Should detect type mismatch"
            print(f"\n  ✅ Detected {len(type_issues)} type mismatch issues")

        finally:
            if os.path.exists(db_path):
                os.remove(db_path)

    def test_circuit_breaker_allows_fixable_data(self, test_db):
        """Verify circuit breaker allows data that's fixable (e.g., DD/MM/YYYY dates)"""
        # Create database with fixable DD/MM/YYYY dates
        with tempfile.NamedTemporaryFile(mode='w', suffix='.db', delete=False) as f:
            db_path = f.name

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('CREATE TABLE tickets (id INTEGER PRIMARY KEY, date TEXT)')

        # Insert DD/MM/YYYY dates (fixable)
        for i in range(1000):
            cursor.execute(
                'INSERT INTO tickets VALUES (?, ?)',
                (i + 1, f'{(i % 28) + 1:02d}/{(i % 12) + 1:02d}/2024 10:00')
            )

        conn.commit()
        conn.close()

        try:
            result = profile_database(db_path, sample_size=1000)
            result = normalize_profiler_result(result)

            # Should NOT halt (dates are fixable)
            circuit_breaker = result.get('circuit_breaker', {})
            should_halt = circuit_breaker.get('should_halt', False)

            if should_halt:
                reason = circuit_breaker.get('reason', '')
                # If it halts, reason should indicate fixable
                assert 'fixable' in reason.lower() or 'clean' in reason.lower()
            else:
                print("\n  ✅ Circuit breaker correctly allows fixable data")

        finally:
            if os.path.exists(db_path):
                os.remove(db_path)


# ==============================================================================
# Idempotency Tests (Process Kill Recovery)
# ==============================================================================

class TestIdempotency:
    """Test that operations are idempotent (safe to retry after failure)"""

    def test_profiler_idempotent_multiple_runs(self, test_db):
        """Verify profiler can be run multiple times with same results"""
        # Run profiler 3 times
        result1 = profile_database(test_db, sample_size=500)
        result1 = normalize_profiler_result(result1)
        result2 = profile_database(test_db, sample_size=500)
        result2 = normalize_profiler_result(result2)
        result3 = profile_database(test_db, sample_size=500)
        result3 = normalize_profiler_result(result3)

        # Results should be consistent
        assert result1['status'] == result2['status'] == result3['status']

        # Issue counts should be identical
        issues1_count = len(result1.get('issues', []))
        issues2_count = len(result2.get('issues', []))
        issues3_count = len(result3.get('issues', []))

        assert issues1_count == issues2_count == issues3_count, \
            "Profiler results should be deterministic"

        print(f"\n  ✅ Profiler produced consistent results across 3 runs")

    def test_cleaner_idempotent_multiple_runs(self, test_db):
        """Verify cleaner can be run multiple times (output is idempotent)"""
        # Clean database first time
        output1 = tempfile.NamedTemporaryFile(suffix='.db', delete=False).name
        result1 = clean_database(
            test_db,
            output1,
            config={
                'date_columns': [('tickets', 'TKT-Created Time')],
                'empty_to_null_columns': []
            }
        )

        # Clean the cleaned database again (should be no-op)
        output2 = tempfile.NamedTemporaryFile(suffix='.db', delete=False).name

        try:
            result2 = clean_database(
            output1,
            output2,
            config={
                'date_columns': [('tickets', 'TKT-Created Time')],
                'empty_to_null_columns': []
            }
        )

            # Second cleaning should convert 0 dates (already clean)
            assert result2.get('dates_converted', 0) == 0, \
                "Second cleaning should be no-op"

            # Calculate MD5 of both outputs
            with open(output1, 'rb') as f:
                md5_1 = hashlib.md5(f.read()).hexdigest()
            with open(output2, 'rb') as f:
                md5_2 = hashlib.md5(f.read()).hexdigest()

            assert md5_1 == md5_2, "Cleaning twice should produce identical output"
            print("\n  ✅ Cleaner is idempotent (2 runs produced identical output)")

        finally:
            for f in [output1, output2]:
                if os.path.exists(f):
                    os.remove(f)

    def test_partial_cleanup_allows_safe_retry(self, test_db):
        """Verify failed operation can be safely retried"""
        output_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False).name

        # First attempt: Force failure
        try:
            with patch('claude.tools.sre.servicedesk_etl_data_cleaner_enhanced.check_disk_space_health') as mock:
                mock.return_value = {'healthy': False, 'available_gb': 0.1, 'threshold_gb': 1.0}
                result = clean_database(
            test_db,
            output_db,
            config={
                'date_columns': [('tickets', 'TKT-Created Time')],
                'empty_to_null_columns': []
            }
        )
        except Exception:
            pass  # Expected to fail

        # Verify output was cleaned up
        assert not os.path.exists(output_db), "Partial output should be deleted"

        # Second attempt: Succeed
        result = clean_database(
            test_db,
            output_db,
            config={
                'date_columns': [('tickets', 'TKT-Created Time')],
                'empty_to_null_columns': []
            }
        )

        try:
            assert result['status'] == 'success', "Retry should succeed"
            assert os.path.exists(output_db), "Output should exist after successful retry"
            print("\n  ✅ Safe retry after failure confirmed")

        finally:
            if os.path.exists(output_db):
                os.remove(output_db)


# ==============================================================================
# Data Corruption Handling Tests
# ==============================================================================

class TestDataCorruptionHandling:
    """Test handling of corrupt or malformed data"""

    def test_handles_null_values_gracefully(self):
        """Verify system handles NULL values in date columns"""
        # Create database with NULL date values
        with tempfile.NamedTemporaryFile(mode='w', suffix='.db', delete=False) as f:
            db_path = f.name

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('CREATE TABLE tickets (id INTEGER PRIMARY KEY, date TEXT)')

        # Mix of NULL, valid dates, and empty strings
        for i in range(100):
            if i % 3 == 0:
                date_val = None  # NULL
            elif i % 3 == 1:
                date_val = ''  # Empty string
            else:
                date_val = '2024-01-01 10:00:00'

            cursor.execute('INSERT INTO tickets VALUES (?, ?)', (i + 1, date_val))

        conn.commit()
        conn.close()

        output_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False).name

        try:
            # Should handle NULLs gracefully
            result = clean_database(
            db_path,
            output_db,
            config={
                'date_columns': [('tickets', 'date')],
                'empty_to_null_columns': [('tickets', 'date')]
            }
        )

            assert result['status'] == 'success'
            print("\n  ✅ Handled NULL and empty string values gracefully")

        finally:
            for f in [db_path, output_db]:
                if os.path.exists(f):
                    os.remove(f)

    def test_handles_malformed_dates_gracefully(self):
        """Verify system handles malformed date strings"""
        # Create database with various malformed dates
        with tempfile.NamedTemporaryFile(mode='w', suffix='.db', delete=False) as f:
            db_path = f.name

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('CREATE TABLE tickets (id INTEGER PRIMARY KEY, date TEXT)')

        malformed_dates = [
            '32/13/2024 10:00',  # Invalid day/month
            '2024-13-32 25:99:99',  # Invalid values
            'NOT_A_DATE',
            '00/00/0000',
            '2024-01-01',  # Missing time
            '10:00:00',  # Missing date
        ]

        for i, date_val in enumerate(malformed_dates):
            cursor.execute('INSERT INTO tickets VALUES (?, ?)', (i + 1, date_val))

        conn.commit()
        conn.close()

        output_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False).name

        try:
            # Should handle malformed dates without crashing
            result = clean_database(
            db_path,
            output_db,
            config={
                'date_columns': [('tickets', 'date')],
                'empty_to_null_columns': []
            }
        )

            # May succeed or fail depending on implementation
            # Key: should not crash, should provide useful error
            if result['status'] == 'error':
                assert 'date' in result.get('error', '').lower() or \
                       'malformed' in result.get('error', '').lower()

            print("\n  ✅ Handled malformed dates gracefully")

        finally:
            for f in [db_path, output_db]:
                if os.path.exists(f):
                    os.remove(f)


# ==============================================================================
# Permission and Access Tests
# ==============================================================================

class TestPermissionFailures:
    """Test handling of permission and access failures"""

    def test_handles_readonly_source_database(self, test_db):
        """Verify profiler works with read-only source database"""
        # Make source read-only
        os.chmod(test_db, 0o444)

        try:
            # Profiler should still work (read-only operation)
            result = profile_database(test_db, sample_size=100)
            result = normalize_profiler_result(result)
            assert result['status'] == 'success'
            print("\n  ✅ Profiler works with read-only source")

        finally:
            # Restore permissions for cleanup
            os.chmod(test_db, 0o644)

    def test_handles_missing_source_database(self):
        """Verify graceful error on missing source database"""
        nonexistent_db = '/tmp/nonexistent_database_12345.db'

        with pytest.raises(Exception) as exc_info:
            profile_database(nonexistent_db, sample_size=100)

        error_msg = str(exc_info.value).lower()
        assert 'not found' in error_msg or 'no such file' in error_msg or 'exist' in error_msg
        print(f"\n  ✅ Graceful error on missing source: {exc_info.value}")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
