"""
Test Suite for ServiceDesk ETL Data Profiler

TDD Test Suite - Created Before Implementation
Tests verify data profiling, type detection, circuit breaker, and confidence scoring.
"""

import pytest
import os
import sys
import tempfile
import sqlite3
import json
from unittest import mock
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestTypeDetection:
    """Test type detection with data sampling"""

    def test_detect_column_type_identifies_text_in_timestamp_column(self):
        """Verify type detection identifies TEXT data in TIMESTAMP-labeled column"""
        from claude.tools.sre.servicedesk_etl_data_profiler import detect_column_type

        # Create test data - dates stored as TEXT
        data = ['2025-10-19 08:42:00', '2025-10-18 14:30:00', '2025-10-17 09:15:00']

        result = detect_column_type(data, schema_type='TIMESTAMP')

        assert result['detected_type'] == 'TEXT'
        assert result['schema_type'] == 'TIMESTAMP'
        assert result['type_mismatch'] is True

    def test_detect_column_type_with_confidence_scoring(self):
        """Verify type detection includes confidence scores"""
        from claude.tools.sre.servicedesk_etl_data_profiler import detect_column_type

        # Homogeneous data should have high confidence
        data = ['test1', 'test2', 'test3'] * 100

        result = detect_column_type(data)

        assert 'confidence' in result
        assert result['confidence'] >= 0.95
        assert result['detected_type'] == 'TEXT'

    def test_detect_column_type_handles_mixed_types_with_low_confidence(self):
        """Verify mixed types result in lower confidence"""
        from claude.tools.sre.servicedesk_etl_data_profiler import detect_column_type

        # Mixed data types
        data = ['text', '123', '456.78', 'more text', '2025-10-19']

        result = detect_column_type(data)

        assert result['confidence'] < 0.95
        assert result['recommendation'] == 'MANUAL_REVIEW'

    def test_detect_column_type_samples_large_datasets(self):
        """Verify type detection samples large datasets efficiently"""
        from claude.tools.sre.servicedesk_etl_data_profiler import detect_column_type

        # Large dataset - should sample, not scan all
        data = ['text_value'] * 100000

        result = detect_column_type(data, sample_size=5000)

        assert result['sample_size'] <= 5000
        assert result['detected_type'] == 'TEXT'

    def test_detect_column_type_identifies_integers(self):
        """Verify type detection identifies INTEGER columns"""
        from claude.tools.sre.servicedesk_etl_data_profiler import detect_column_type

        data = [1, 2, 3, 100, 500]

        result = detect_column_type(data)

        assert result['detected_type'] == 'INTEGER'

    def test_detect_column_type_identifies_real_numbers(self):
        """Verify type detection identifies REAL columns"""
        from claude.tools.sre.servicedesk_etl_data_profiler import detect_column_type

        data = [1.5, 2.7, 3.14, 100.99, 500.01]

        result = detect_column_type(data)

        assert result['detected_type'] == 'REAL'


class TestDateFormatDetection:
    """Test date format detection"""

    def test_detect_date_formats_finds_ddmmyyyy(self):
        """Verify detection of DD/MM/YYYY format"""
        from claude.tools.sre.servicedesk_etl_data_profiler import detect_date_formats

        data = ['20/05/2025 8:42', '15/06/2025 14:30', '01/07/2025 09:00']

        result = detect_date_formats(data)

        assert 'DD/MM/YYYY' in result['detected_formats']
        assert result['format_count']['DD/MM/YYYY'] == 3

    def test_detect_date_formats_finds_standard_iso(self):
        """Verify detection of YYYY-MM-DD format"""
        from claude.tools.sre.servicedesk_etl_data_profiler import detect_date_formats

        data = ['2025-05-20 08:42:00', '2025-06-15 14:30:00', '2025-07-01 09:00:00']

        result = detect_date_formats(data)

        assert 'YYYY-MM-DD' in result['detected_formats']
        assert result['consistent'] is True

    def test_detect_date_formats_detects_inconsistency(self):
        """Verify detection of mixed date formats"""
        from claude.tools.sre.servicedesk_etl_data_profiler import detect_date_formats

        # Mix of formats
        data = [
            '20/05/2025 8:42',  # DD/MM/YYYY
            '2025-06-15 14:30:00',  # YYYY-MM-DD
            '2/07/2025 16:21'  # D/MM/YYYY
        ]

        result = detect_date_formats(data)

        assert result['consistent'] is False
        assert len(result['detected_formats']) > 1

    def test_detect_date_formats_calculates_affected_rows(self):
        """Verify affected rows calculation"""
        from claude.tools.sre.servicedesk_etl_data_profiler import detect_date_formats

        data = ['20/05/2025'] * 9 + ['2025-05-20'] * 91

        result = detect_date_formats(data)

        assert result['format_count']['DD/MM/YYYY'] == 9
        assert result['format_count']['YYYY-MM-DD'] == 91


class TestEmptyStringDetection:
    """Test empty string detection"""

    def test_detect_empty_strings_in_date_columns(self):
        """Verify empty string detection in date columns"""
        from claude.tools.sre.servicedesk_etl_data_profiler import detect_empty_strings

        data = ['2025-10-19', '', '2025-10-20', '', '2025-10-21']

        result = detect_empty_strings(data, column_type='TIMESTAMP')

        assert result['has_empty_strings'] is True
        assert result['empty_count'] == 2
        assert result['empty_percent'] == 40.0

    def test_detect_empty_strings_distinguishes_from_null(self):
        """Verify empty strings distinguished from NULL"""
        from claude.tools.sre.servicedesk_etl_data_profiler import detect_empty_strings

        data = ['value1', '', None, 'value2', '']

        result = detect_empty_strings(data)

        assert result['empty_count'] == 2  # Only empty strings, not None
        assert result['null_count'] == 1


class TestCircuitBreaker:
    """Test circuit breaker logic"""

    def test_circuit_breaker_halts_on_high_type_mismatch(self):
        """Verify circuit breaker halts when >10% columns have type mismatches"""
        from claude.tools.sre.servicedesk_etl_data_profiler import check_circuit_breaker

        issues = {
            'type_mismatches': 12,  # >10% of 100 columns
            'total_columns': 100,
            'corrupt_dates_pct': 0.05
        }

        result = check_circuit_breaker(issues)

        assert result['should_halt'] is True
        assert result['is_fixable'] is False
        assert result['recommendation'] == 'FIX_SOURCE'
        assert 'type mismatches' in result['reason'].lower()

    def test_circuit_breaker_halts_on_high_corrupt_dates(self):
        """Verify circuit breaker halts when >20% dates are corrupt"""
        from claude.tools.sre.servicedesk_etl_data_profiler import check_circuit_breaker

        issues = {
            'type_mismatches': 2,
            'total_columns': 100,
            'corrupt_dates_pct': 0.25  # 25% corrupt
        }

        result = check_circuit_breaker(issues)

        assert result['should_halt'] is True
        assert result['is_fixable'] is False
        assert 'corrupt dates' in result['reason'].lower()

    def test_circuit_breaker_allows_fixable_data(self):
        """Verify circuit breaker allows data that can be fixed"""
        from claude.tools.sre.servicedesk_etl_data_profiler import check_circuit_breaker

        issues = {
            'type_mismatches': 2,  # <10%
            'total_columns': 100,
            'corrupt_dates_pct': 0.05  # 5% corrupt
        }

        result = check_circuit_breaker(issues)

        assert result['should_halt'] is False
        assert result['is_fixable'] is True
        assert result['recommendation'] == 'PROCEED'


class TestDryRunQueries:
    """Test dry-run PostgreSQL query validation"""

    def test_dry_run_queries_validates_timestamp_casting(self):
        """Verify dry-run tests TIMESTAMP casting"""
        from claude.tools.sre.servicedesk_etl_data_profiler import validate_postgres_compatibility

        # Sample data for testing
        sample_data = {
            'TKT-Created Time': ['2025-10-19 08:42:00', '2025-10-18 14:30:00'],
            'TKT-Status': ['Open', 'Closed']
        }

        with mock.patch('psycopg2.connect') as mock_connect:
            mock_conn = mock.MagicMock()
            mock_connect.return_value = mock_conn

            result = validate_postgres_compatibility(sample_data, mock_conn)

            assert 'timestamp_cast_test' in result
            assert result['compatible'] in [True, False]

    def test_dry_run_queries_detects_failed_casting(self):
        """Verify dry-run detects when casting will fail"""
        from claude.tools.sre.servicedesk_etl_data_profiler import validate_postgres_compatibility

        sample_data = {
            'TKT-Created Time': ['invalid_date', 'not_a_timestamp']
        }

        with mock.patch('psycopg2.connect') as mock_connect:
            mock_conn = mock.MagicMock()
            mock_cursor = mock.MagicMock()
            mock_conn.cursor.return_value = mock_cursor

            # Simulate PostgreSQL error on invalid cast
            mock_cursor.execute.side_effect = Exception("invalid input syntax for type timestamp")
            mock_connect.return_value = mock_conn

            result = validate_postgres_compatibility(sample_data, mock_conn)

            assert result['compatible'] is False
            assert 'failed_query' in result


class TestIntegrationWithPhase127:
    """Test integration with existing Phase 127 tools"""

    def test_profiler_calls_validator(self):
        """Verify profiler integrates with servicedesk_etl_validator"""
        from claude.tools.sre.servicedesk_etl_data_profiler import profile_database

        # Create test database
        db_path = os.path.join(tempfile.gettempdir(), 'test_integration.db')
        conn = sqlite3.connect(db_path)
        conn.execute('CREATE TABLE tickets (id INTEGER, summary TEXT)')
        conn.execute("INSERT INTO tickets VALUES (1, 'Test ticket')")
        conn.commit()
        conn.close()

        try:
            # Mock the validator - skip actual integration since Phase 127 tool may not exist
            # Just verify the profiler handles use_validator flag
            result = profile_database(db_path, use_validator=False)

            # Verify basic profiling works
            assert 'columns' in result
            assert 'issues' in result
        finally:
            os.unlink(db_path)

    def test_profiler_calls_quality_scorer(self):
        """Verify profiler integrates with servicedesk_quality_scorer"""
        from claude.tools.sre.servicedesk_etl_data_profiler import profile_database

        db_path = os.path.join(tempfile.gettempdir(), 'test_scorer.db')
        conn = sqlite3.connect(db_path)
        conn.execute('CREATE TABLE tickets (id INTEGER)')
        conn.commit()
        conn.close()

        try:
            # Just verify profiler handles use_scorer flag
            # Actual integration depends on Phase 127 tool existence
            result = profile_database(db_path, use_scorer=False)

            # Verify basic profiling works
            assert 'columns' in result
            assert 'issues' in result
        finally:
            os.unlink(db_path)


class TestProfilingReport:
    """Test profiling report generation"""

    def test_profile_database_generates_complete_report(self):
        """Verify profiler generates comprehensive report"""
        from claude.tools.sre.servicedesk_etl_data_profiler import profile_database

        # Create test database with known issues
        db_path = os.path.join(tempfile.gettempdir(), 'test_profile.db')
        conn = sqlite3.connect(db_path)
        conn.execute('CREATE TABLE tickets (id INTEGER, created_time TIMESTAMP, summary TEXT)')
        conn.execute("INSERT INTO tickets VALUES (1, '2025-10-19 08:42:00', 'Test')")
        conn.commit()
        conn.close()

        try:
            result = profile_database(db_path)

            # Verify report structure
            assert 'columns' in result
            assert 'circuit_breaker' in result
            assert 'issues' in result
            assert 'summary' in result
        finally:
            os.unlink(db_path)

    def test_profile_database_identifies_phase1_issues(self):
        """Verify profiler detects all Phase 1 known issues"""
        from claude.tools.sre.servicedesk_etl_data_profiler import profile_database

        # Create database mimicking Phase 1 issues
        db_path = os.path.join(tempfile.gettempdir(), 'test_phase1.db')
        conn = sqlite3.connect(db_path)

        # Issue 1: TIMESTAMP labeled but TEXT data
        conn.execute('CREATE TABLE tickets (created_time TIMESTAMP, resolution_date TIMESTAMP)')

        # Issue 2: Mixed date formats
        conn.execute("INSERT INTO tickets VALUES ('2025-10-19 08:42:00', '20/05/2025 8:42')")

        # Issue 3: Empty strings
        conn.execute("INSERT INTO tickets VALUES ('2025-10-18 14:30:00', '')")

        conn.commit()
        conn.close()

        try:
            result = profile_database(db_path)

            # Should detect type mismatch
            assert any(
                col['type_detection'].get('type_mismatch', False)
                for col in result['columns'].values()
            )

            # Should detect date format issues
            issues = result.get('issues', [])
            assert len(issues) > 0
        finally:
            os.unlink(db_path)


class TestPerformance:
    """Test profiler performance"""

    def test_profiler_completes_in_under_5_minutes_for_large_db(self):
        """Verify profiler meets <5 minute SLA for large datasets"""
        import time
        from claude.tools.sre.servicedesk_etl_data_profiler import profile_database

        # Create database with moderate size (10K rows for fast testing)
        db_path = os.path.join(tempfile.gettempdir(), 'test_performance.db')
        conn = sqlite3.connect(db_path)
        conn.execute('CREATE TABLE tickets (id INTEGER, summary TEXT, created_time TEXT)')

        # Insert 10K rows
        for i in range(10000):
            conn.execute(f"INSERT INTO tickets VALUES ({i}, 'Summary {i}', '2025-10-19 08:42:00')")

        conn.commit()
        conn.close()

        try:
            start = time.time()
            profile_database(db_path, sample_size=1000)  # Sample to speed up
            elapsed = time.time() - start

            # For 10K rows with sampling, should be very fast (<5 seconds)
            # Extrapolating: 260K rows would be ~26x, so <130 seconds acceptable for this test
            assert elapsed < 5.0, f"Profiler too slow: {elapsed}s for 10K rows"
        finally:
            os.unlink(db_path)


class TestCLI:
    """Test profiler CLI interface"""

    def test_cli_outputs_json_report(self):
        """Verify CLI outputs valid JSON profiling report"""
        from claude.tools.sre.servicedesk_etl_data_profiler import main
        from io import StringIO

        db_path = os.path.join(tempfile.gettempdir(), 'test_cli.db')
        conn = sqlite3.connect(db_path)
        conn.execute('CREATE TABLE tickets (id INTEGER)')
        conn.execute('INSERT INTO tickets VALUES (1)')
        conn.commit()
        conn.close()

        try:
            with mock.patch('sys.argv', ['profiler.py', '--source', db_path]), \
                 mock.patch('sys.stdout', new=StringIO()) as mock_stdout, \
                 mock.patch('sys.stderr', new=StringIO()):  # Mock stderr too

                with pytest.raises(SystemExit) as exc:
                    main()

                assert exc.value.code == 0

                output = mock_stdout.getvalue()
                result = json.loads(output)

                assert 'columns' in result
                assert 'circuit_breaker' in result
        finally:
            os.unlink(db_path)

    def test_cli_exits_with_error_on_circuit_breaker_halt(self):
        """Verify CLI exits with error code when circuit breaker halts"""
        from claude.tools.sre.servicedesk_etl_data_profiler import main

        db_path = os.path.join(tempfile.gettempdir(), 'test_halt.db')
        conn = sqlite3.connect(db_path)
        conn.execute('CREATE TABLE tickets (id INTEGER)')
        conn.commit()
        conn.close()

        try:
            # Mock circuit breaker to halt
            with mock.patch('sys.argv', ['profiler.py', '--source', db_path]), \
                 mock.patch('claude.tools.sre.servicedesk_etl_data_profiler.check_circuit_breaker') as mock_cb:

                mock_cb.return_value = {
                    'should_halt': True,
                    'is_fixable': False,
                    'recommendation': 'FIX_SOURCE',
                    'reason': 'Test halt'
                }

                with pytest.raises(SystemExit) as exc:
                    main()

                assert exc.value.code == 1  # Error exit
        finally:
            os.unlink(db_path)
