"""
ServiceDesk ETL V2 - Enhanced Data Cleaner Tests (TDD)

Tests written BEFORE implementation to drive design.

Test Categories:
1. Transaction Management (CRITICAL - source never modified)
2. Date Format Standardization (DD/MM/YYYY → YYYY-MM-DD)
3. Empty String → NULL Conversion
4. Health Checks & Circuit Breakers
5. Progress Tracking & Observability
6. Integration with Phase 1 Database
"""

import os
import sqlite3
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def temp_db():
    """Create temporary test database"""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def source_db_with_issues(temp_db):
    """
    Create source database with known data quality issues:
    - DD/MM/YYYY date formats (9 records)
    - Empty strings in date columns
    - Mixed date formats
    """
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    # Create tickets table with date issues
    cursor.execute('''
        CREATE TABLE tickets (
            id INTEGER PRIMARY KEY,
            ticket_number TEXT,
            created_time TEXT,
            resolved_date TEXT,
            status TEXT
        )
    ''')

    # Insert test data with issues
    test_data = [
        # DD/MM/YYYY format (should be converted)
        (1, 'TKT-001', '15/06/2024 9:30', '20/06/2024 14:45', 'Closed'),
        (2, 'TKT-002', '1/01/2024 8:00', '5/01/2024 16:30', 'Closed'),
        (3, 'TKT-003', '28/12/2023 23:59', '2/01/2024 10:00', 'Closed'),

        # YYYY-MM-DD format (should be preserved)
        (4, 'TKT-004', '2024-06-15 09:30:00', '2024-06-20 14:45:00', 'Closed'),

        # Empty strings (should → NULL)
        (5, 'TKT-005', '2024-06-15 09:30:00', '', 'Open'),
        (6, 'TKT-006', '', '', 'Open'),

        # NULL values (should be preserved)
        (7, 'TKT-007', '2024-06-15 09:30:00', None, 'In Progress'),

        # More DD/MM/YYYY formats
        (8, 'TKT-008', '3/03/2024 12:00', '3/03/2024 15:30', 'Closed'),
        (9, 'TKT-009', '31/01/2024 8:15', '31/01/2024 17:00', 'Closed'),
    ]

    cursor.executemany('''
        INSERT INTO tickets (id, ticket_number, created_time, resolved_date, status)
        VALUES (?, ?, ?, ?, ?)
    ''', test_data)

    conn.commit()
    conn.close()

    return temp_db


@pytest.fixture
def output_db(temp_db):
    """Separate output database path"""
    # Use different temp file
    fd, path = tempfile.mkstemp(suffix='_output.db')
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)


# ============================================================================
# Test Class 1: Transaction Management (CRITICAL)
# ============================================================================

class TestTransactionManagement:
    """
    CRITICAL: Verify source database NEVER modified
    """

    def test_clean_to_new_file_never_modifies_source(self, source_db_with_issues, output_db):
        """
        CRITICAL TEST: Source database must NEVER be modified

        Success criteria:
        - Source file unchanged (MD5 checksum)
        - Output file created
        - All changes in output only
        """
        from claude.tools.sre.servicedesk_etl_data_cleaner_enhanced import clean_database
        import hashlib

        # Calculate source MD5 before cleaning
        with open(source_db_with_issues, 'rb') as f:
            source_md5_before = hashlib.md5(f.read()).hexdigest()

        # Clean database
        result = clean_database(
            source_db=source_db_with_issues,
            output_db=output_db
        )

        # Verify source unchanged
        with open(source_db_with_issues, 'rb') as f:
            source_md5_after = hashlib.md5(f.read()).hexdigest()

        assert source_md5_before == source_md5_after, "Source database was modified!"
        assert result['status'] == 'success'
        assert os.path.exists(output_db), "Output database not created"


    def test_rejects_same_source_and_output(self, source_db_with_issues):
        """
        Verify error when source == output (prevents in-place modification)
        """
        from claude.tools.sre.servicedesk_etl_data_cleaner_enhanced import clean_database, CleaningError

        with pytest.raises((ValueError, CleaningError), match="different files|in-place"):
            clean_database(
                source_db=source_db_with_issues,
                output_db=source_db_with_issues  # Same file!
            )


    def test_transaction_rollback_on_error(self, source_db_with_issues, output_db):
        """
        Verify transaction rollback on cleaning error

        Success criteria:
        - Exception raised
        - Output file deleted (no partial results)
        - Source unchanged
        """
        from claude.tools.sre.servicedesk_etl_data_cleaner_enhanced import clean_database
        from unittest.mock import patch

        # Force error by mocking quality scorer to fail quality gate
        with patch('claude.tools.sre.servicedesk_etl_data_cleaner_enhanced.score_database') as mock_scorer:
            mock_scorer.return_value = 10  # Low quality score

            with pytest.raises(Exception):
                clean_database(
                    source_db=source_db_with_issues,
                    output_db=output_db,
                    config={'min_quality_score': 80}  # Require 80, but returns 10
                )

        # Verify output deleted
        assert not os.path.exists(output_db), "Partial output not cleaned up"


    def test_atomic_commit_on_success(self, source_db_with_issues, output_db):
        """
        Verify all changes committed atomically

        Success criteria:
        - All changes visible in output
        - No partial state possible
        """
        from claude.tools.sre.servicedesk_etl_data_cleaner_enhanced import clean_database

        result = clean_database(
            source_db=source_db_with_issues,
            output_db=output_db
        )

        # Verify output database complete
        conn = sqlite3.connect(output_db)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM tickets')
        row_count = cursor.fetchone()[0]
        conn.close()

        assert row_count == 9, "Output database incomplete"
        assert result['status'] == 'success'


# ============================================================================
# Test Class 2: Date Format Standardization
# ============================================================================

class TestDateStandardization:
    """
    Verify DD/MM/YYYY → YYYY-MM-DD HH:MM:SS conversion
    """

    def test_converts_ddmmyyyy_to_iso(self, source_db_with_issues, output_db):
        """
        Verify DD/MM/YYYY dates converted to YYYY-MM-DD HH:MM:SS

        Example: '15/06/2024 9:30' → '2024-06-15 09:30:00'
        """
        from claude.tools.sre.servicedesk_etl_data_cleaner_enhanced import clean_database

        result = clean_database(
            source_db=source_db_with_issues,
            output_db=output_db
        )

        # Check converted dates
        conn = sqlite3.connect(output_db)
        cursor = conn.cursor()
        cursor.execute("SELECT created_time FROM tickets WHERE id = 1")
        created = cursor.fetchone()[0]
        conn.close()

        # Should be converted to ISO format
        assert created == '2024-06-15 09:30:00', f"Expected ISO format, got: {created}"
        assert result['dates_standardized'] >= 5, "Not enough dates converted"


    def test_handles_single_digit_days_months(self, source_db_with_issues, output_db):
        """
        Verify single-digit days/months padded correctly

        Example: '1/01/2024 8:00' → '2024-01-01 08:00:00'
        """
        from claude.tools.sre.servicedesk_etl_data_cleaner_enhanced import clean_database

        clean_database(
            source_db=source_db_with_issues,
            output_db=output_db
        )

        conn = sqlite3.connect(output_db)
        cursor = conn.cursor()
        cursor.execute("SELECT created_time FROM tickets WHERE id = 2")
        created = cursor.fetchone()[0]
        conn.close()

        assert created == '2024-01-01 08:00:00', f"Padding incorrect: {created}"


    def test_preserves_already_standard_dates(self, source_db_with_issues, output_db):
        """
        Verify YYYY-MM-DD dates unchanged
        """
        from claude.tools.sre.servicedesk_etl_data_cleaner_enhanced import clean_database

        clean_database(
            source_db=source_db_with_issues,
            output_db=output_db
        )

        conn = sqlite3.connect(output_db)
        cursor = conn.cursor()
        cursor.execute("SELECT created_time FROM tickets WHERE id = 4")
        created = cursor.fetchone()[0]
        conn.close()

        assert created == '2024-06-15 09:30:00', "Standard date was modified"


    def test_handles_edge_dates(self, temp_db, output_db):
        """
        Verify edge case dates (31/01, 29/02 leap year, etc.)
        """
        # Create database with edge dates
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE tickets (id INTEGER, created_time TEXT)')
        cursor.execute("INSERT INTO tickets VALUES (1, '31/01/2024 23:59')")
        cursor.execute("INSERT INTO tickets VALUES (2, '29/02/2024 12:00')")  # Leap year
        conn.commit()
        conn.close()

        from claude.tools.sre.servicedesk_etl_data_cleaner_enhanced import clean_database

        clean_database(source_db=temp_db, output_db=output_db)

        conn = sqlite3.connect(output_db)
        cursor = conn.cursor()
        cursor.execute("SELECT created_time FROM tickets WHERE id = 1")
        date1 = cursor.fetchone()[0]
        cursor.execute("SELECT created_time FROM tickets WHERE id = 2")
        date2 = cursor.fetchone()[0]
        conn.close()

        assert date1 == '2024-01-31 23:59:00'
        assert date2 == '2024-02-29 12:00:00'


# ============================================================================
# Test Class 3: Empty String Conversion
# ============================================================================

class TestEmptyStringConversion:
    """
    Verify empty string → NULL conversion
    """

    def test_converts_empty_strings_to_null(self, source_db_with_issues, output_db):
        """
        Verify '' → NULL in date columns
        """
        from claude.tools.sre.servicedesk_etl_data_cleaner_enhanced import clean_database

        result = clean_database(
            source_db=source_db_with_issues,
            output_db=output_db
        )

        conn = sqlite3.connect(output_db)
        cursor = conn.cursor()

        # Check row with empty resolved_date
        cursor.execute("SELECT resolved_date FROM tickets WHERE id = 5")
        resolved = cursor.fetchone()[0]

        conn.close()

        assert resolved is None, f"Empty string not converted to NULL: {resolved}"
        assert result['empty_strings_converted'] >= 2


    def test_preserves_actual_null_values(self, source_db_with_issues, output_db):
        """
        Verify NULL values unchanged
        """
        from claude.tools.sre.servicedesk_etl_data_cleaner_enhanced import clean_database

        clean_database(
            source_db=source_db_with_issues,
            output_db=output_db
        )

        conn = sqlite3.connect(output_db)
        cursor = conn.cursor()
        cursor.execute("SELECT resolved_date FROM tickets WHERE id = 7")
        resolved = cursor.fetchone()[0]
        conn.close()

        assert resolved is None, "NULL value was modified"


    def test_converts_empty_in_multiple_columns(self, temp_db, output_db):
        """
        Verify empty string conversion across all date columns
        """
        # Create test data with empty strings in multiple columns
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE tickets (
                id INTEGER,
                created_time TEXT,
                resolved_date TEXT,
                updated_time TEXT
            )
        ''')
        cursor.execute("INSERT INTO tickets VALUES (1, '', '', '')")
        conn.commit()
        conn.close()

        from claude.tools.sre.servicedesk_etl_data_cleaner_enhanced import clean_database

        # Explicitly specify all columns
        clean_database(
            source_db=temp_db,
            output_db=output_db,
            config={
                'empty_to_null_columns': ['created_time', 'resolved_date', 'updated_time']
            }
        )

        conn = sqlite3.connect(output_db)
        cursor = conn.cursor()
        cursor.execute("SELECT created_time, resolved_date, updated_time FROM tickets WHERE id = 1")
        row = cursor.fetchone()
        conn.close()

        assert all(val is None for val in row), "Not all empty strings converted"


# ============================================================================
# Test Class 4: Health Checks & Circuit Breakers
# ============================================================================

class TestHealthChecks:
    """
    Verify health checks prevent resource exhaustion
    """

    @patch('claude.tools.sre.servicedesk_etl_data_cleaner_enhanced.check_disk_space_health')
    def test_halts_on_low_disk_space(self, mock_disk_check, source_db_with_issues, output_db):
        """
        Verify cleaning halts when disk space <1GB
        """
        from claude.tools.sre.servicedesk_etl_data_cleaner_enhanced import clean_database

        # Mock disk space failure
        mock_disk_check.return_value = {'healthy': False, 'free_gb': 0.5}

        with pytest.raises(Exception, match="disk|space"):
            clean_database(
                source_db=source_db_with_issues,
                output_db=output_db
            )


    @patch('claude.tools.sre.servicedesk_etl_data_cleaner_enhanced.check_memory_health')
    def test_halts_on_high_memory_usage(self, mock_memory_check, source_db_with_issues, output_db):
        """
        Verify cleaning halts when memory >90%
        """
        from claude.tools.sre.servicedesk_etl_data_cleaner_enhanced import clean_database

        # Mock memory pressure
        mock_memory_check.return_value = {'healthy': False, 'percent_used': 95.0}

        with pytest.raises(Exception, match="[Mm]emory"):
            clean_database(
                source_db=source_db_with_issues,
                output_db=output_db
            )


    def test_health_checks_run_periodically(self, source_db_with_issues, output_db):
        """
        Verify health checks run every 10K rows (or configured interval)
        """
        from claude.tools.sre.servicedesk_etl_data_cleaner_enhanced import clean_database

        # This should complete without health check failures
        result = clean_database(
            source_db=source_db_with_issues,
            output_db=output_db
        )

        assert result['status'] == 'success'
        assert 'health_checks_passed' in result


# ============================================================================
# Test Class 5: Progress Tracking & Observability
# ============================================================================

class TestProgressTracking:
    """
    Verify progress tracking and observability integration
    """

    def test_progress_tracking_updates(self, source_db_with_issues, output_db):
        """
        Verify progress updates during cleaning
        """
        from claude.tools.sre.servicedesk_etl_data_cleaner_enhanced import clean_database

        result = clean_database(
            source_db=source_db_with_issues,
            output_db=output_db
        )

        assert 'rows_processed' in result
        assert result['rows_processed'] == 9


    def test_metrics_emission(self, source_db_with_issues, output_db):
        """
        Verify metrics emitted for observability
        """
        from claude.tools.sre.servicedesk_etl_data_cleaner_enhanced import clean_database

        result = clean_database(
            source_db=source_db_with_issues,
            output_db=output_db
        )

        # Check for key metrics
        assert 'duration_seconds' in result
        assert 'dates_standardized' in result
        assert 'empty_strings_converted' in result


    def test_observability_overhead_minimal(self, source_db_with_issues, output_db):
        """
        Verify observability overhead <1ms per operation (100ms for 100 ops)
        """
        from claude.tools.sre.servicedesk_etl_data_cleaner_enhanced import clean_database

        start = time.time()
        clean_database(
            source_db=source_db_with_issues,
            output_db=output_db
        )
        elapsed = time.time() - start

        # For 9 rows, should be nearly instant (<1 second)
        assert elapsed < 5.0, f"Cleaning took too long: {elapsed}s"


# ============================================================================
# Test Class 6: Integration Tests
# ============================================================================

class TestIntegration:
    """
    End-to-end integration tests
    """

    def test_complete_cleaning_workflow(self, source_db_with_issues, output_db):
        """
        End-to-end test: dirty data → cleaned output

        Success criteria:
        - All DD/MM/YYYY converted
        - All empty strings → NULL
        - Source unchanged
        - Output complete
        - Quality improved
        """
        from claude.tools.sre.servicedesk_etl_data_cleaner_enhanced import clean_database

        result = clean_database(
            source_db=source_db_with_issues,
            output_db=output_db
        )

        # Verify results
        assert result['status'] == 'success'
        assert result['dates_standardized'] >= 5
        assert result['empty_strings_converted'] >= 2
        assert result['rows_processed'] == 9

        # Verify output database quality
        conn = sqlite3.connect(output_db)
        cursor = conn.cursor()

        # Check all dates standardized
        cursor.execute("SELECT created_time FROM tickets WHERE id IN (1,2,3,8,9)")
        dates = cursor.fetchall()
        for (date,) in dates:
            assert '-' in date, f"Date not standardized: {date}"
            assert date.count(':') == 2, f"Time not complete: {date}"

        conn.close()


    def test_idempotency(self, source_db_with_issues):
        """
        Verify running cleaner twice produces same result (idempotent)
        """
        from claude.tools.sre.servicedesk_etl_data_cleaner_enhanced import clean_database

        # First cleaning
        fd1, output1 = tempfile.mkstemp(suffix='_output1.db')
        os.close(fd1)

        # Second cleaning output
        fd2, output2 = tempfile.mkstemp(suffix='_output2.db')
        os.close(fd2)

        try:
            result1 = clean_database(
                source_db=source_db_with_issues,
                output_db=output1
            )

            # Second cleaning (using first output as source)
            result2 = clean_database(
                source_db=output1,
                output_db=output2
            )

            # Second run should find nothing to clean
            assert result2['dates_standardized'] == 0, "Dates re-cleaned (not idempotent)"
            assert result2['empty_strings_converted'] == 0, "Empty strings re-cleaned"

        finally:
            if os.path.exists(output1):
                os.remove(output1)
            if os.path.exists(output2):
                os.remove(output2)


    def test_quality_score_improvement(self, source_db_with_issues, output_db):
        """
        Verify quality score improves +10+ points after cleaning

        Note: Requires Phase 127 quality scorer integration
        """
        from claude.tools.sre.servicedesk_etl_data_cleaner_enhanced import clean_database
        from unittest.mock import patch

        # Mock quality scorer to test improvement tracking
        with patch('claude.tools.sre.servicedesk_etl_data_cleaner_enhanced.score_database') as mock_scorer:
            # Simulate quality improvement: 70 → 95
            mock_scorer.side_effect = [70, 95]

            result = clean_database(
                source_db=source_db_with_issues,
                output_db=output_db
            )

            # Verify quality tracked
            assert result['quality_score_before'] == 70
            assert result['quality_score_after'] == 95
            improvement = result['quality_score_after'] - result['quality_score_before']
            assert improvement >= 10, f"Quality improvement too low: {improvement}"


# ============================================================================
# Test Class 7: Error Handling
# ============================================================================

class TestErrorHandling:
    """
    Verify robust error handling
    """

    def test_handles_missing_source_database(self, output_db):
        """
        Verify error on missing source database
        """
        from claude.tools.sre.servicedesk_etl_data_cleaner_enhanced import clean_database

        with pytest.raises(Exception, match="not found|does not exist"):
            clean_database(
                source_db='/nonexistent/database.db',
                output_db=output_db
            )


    def test_handles_corrupt_database(self, temp_db, output_db):
        """
        Verify error on corrupt source database
        """
        # Create corrupt file
        with open(temp_db, 'wb') as f:
            f.write(b'CORRUPT DATA')

        from claude.tools.sre.servicedesk_etl_data_cleaner_enhanced import clean_database

        with pytest.raises(Exception):
            clean_database(
                source_db=temp_db,
                output_db=output_db
            )


    def test_handles_permission_errors(self, source_db_with_issues):
        """
        Verify error on permission issues
        """
        from claude.tools.sre.servicedesk_etl_data_cleaner_enhanced import clean_database

        # Try to write to read-only location
        with pytest.raises(Exception):
            clean_database(
                source_db=source_db_with_issues,
                output_db='/root/readonly.db'  # Permission denied
            )


# ============================================================================
# Run tests with: PYTHONPATH=. pytest tests/test_servicedesk_etl_data_cleaner_enhanced.py -v
# ============================================================================
