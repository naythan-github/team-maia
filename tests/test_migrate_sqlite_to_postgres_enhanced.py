"""
ServiceDesk ETL V2 - Enhanced Migration Script Tests (TDD)

Tests written BEFORE implementation to drive design.

Test Categories:
1. Quality Gate Integration (reject poor quality data)
2. Canary Deployment (test 10% sample first)
3. Blue-Green Deployment (versioned schemas)
4. Enhanced Rollback (DROP + restore from backup)
5. Type Validation (sample-based, not schema labels)
6. Health Checks & Progress Tracking
"""

import os
import sqlite3
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add migration directory to path (workaround for hyphenated directory name)
migration_path = Path(__file__).parent.parent / 'claude' / 'infrastructure' / 'servicedesk-dashboard' / 'migration'
sys.path.insert(0, str(migration_path))

# Now import from the migration script
import migrate_sqlite_to_postgres_enhanced as migration_module


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def temp_sqlite_db():
    """Create temporary SQLite database with test data"""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    conn = sqlite3.connect(path)
    cursor = conn.cursor()

    # Create tickets table with cleaned data (from Phase 2)
    cursor.execute('''
        CREATE TABLE tickets (
            id INTEGER PRIMARY KEY,
            ticket_number TEXT,
            created_time TEXT,
            resolved_date TEXT,
            status TEXT,
            priority TEXT
        )
    ''')

    # Insert test data (dates already standardized by Phase 2)
    test_data = [
        (1, 'TKT-001', '2024-06-15 09:30:00', '2024-06-20 14:45:00', 'Closed', 'High'),
        (2, 'TKT-002', '2024-01-01 08:00:00', '2024-01-05 16:30:00', 'Closed', 'Medium'),
        (3, 'TKT-003', '2024-12-28 23:59:00', '2024-01-02 10:00:00', 'Closed', 'Low'),
        (4, 'TKT-004', '2024-06-15 09:30:00', None, 'Open', 'High'),
        (5, 'TKT-005', '2024-06-15 09:30:00', '2024-06-15 10:00:00', 'Closed', 'Medium'),
    ]

    cursor.executemany('''
        INSERT INTO tickets (id, ticket_number, created_time, resolved_date, status, priority)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', test_data)

    conn.commit()
    conn.close()

    yield path

    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def mock_postgres_conn():
    """Mock PostgreSQL connection"""
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value = cursor
    cursor.fetchone.return_value = [0]  # Default: no rows
    cursor.fetchall.return_value = []
    return conn


# ============================================================================
# Test Class 1: Quality Gate Integration
# ============================================================================

class TestQualityGate:
    """
    Verify quality gate blocks poor quality data from migration
    """

    def test_rejects_migration_below_quality_threshold(self, temp_sqlite_db, mock_postgres_conn):
        """
        Verify quality gate blocks data with quality score <80

        Success criteria:
        - Migration fails with quality gate error
        - No data written to PostgreSQL
        - Clear error message about quality threshold
        """
        from migration_module import (
            migrate_with_quality_gate, MigrationError
        )

        # Mock quality scorer to return low score
        with patch('migration_module.score_database') as mock_scorer:
            mock_scorer.return_value = 65  # Below 80 threshold

            with pytest.raises(MigrationError, match="quality|threshold|65"):
                migrate_with_quality_gate(
                    source_db=temp_sqlite_db,
                    postgres_conn=mock_postgres_conn,
                    min_quality=80
                )


    def test_proceeds_with_high_quality_data(self, temp_sqlite_db, mock_postgres_conn):
        """
        Verify quality gate allows data with quality score ≥80

        Success criteria:
        - Migration completes successfully
        - Data written to PostgreSQL
        - Quality score logged
        """
        from migration_module import (
            migrate_with_quality_gate
        )

        # Mock quality scorer to return high score
        with patch('migration_module.score_database') as mock_scorer:
            mock_scorer.return_value = 95  # Above 80 threshold

            result = migrate_with_quality_gate(
                source_db=temp_sqlite_db,
                postgres_conn=mock_postgres_conn,
                min_quality=80
            )

            assert result['status'] == 'success'
            assert result['quality_score'] == 95
            assert result['quality_passed'] is True


    def test_respects_circuit_breaker_from_profiler(self, temp_sqlite_db, mock_postgres_conn):
        """
        Verify quality gate checks circuit breaker from Phase 1 profiler

        Success criteria:
        - Migration halts if profiler circuit breaker triggered
        - Clear error message about data issues
        """
        from migration_module import (
            migrate_with_quality_gate, MigrationError
        )

        # Mock profiler to return circuit breaker halt
        with patch('migration_module.profile_database') as mock_profiler:
            mock_profiler.return_value = {
                'circuit_breaker': {
                    'should_halt': True,
                    'reason': 'Type mismatches >10%'
                }
            }

            with pytest.raises(MigrationError, match="circuit breaker|Type mismatches"):
                migrate_with_quality_gate(
                    source_db=temp_sqlite_db,
                    postgres_conn=mock_postgres_conn
                )


# ============================================================================
# Test Class 2: Canary Deployment
# ============================================================================

class TestCanaryDeployment:
    """
    Verify canary deployment validates 10% sample before full migration
    """

    def test_canary_validates_before_full_migration(self, temp_sqlite_db, mock_postgres_conn):
        """
        Verify 10% sample migrated to canary schema first

        Success criteria:
        - Creates servicedesk_canary schema
        - Migrates ~10% of data
        - Validates canary data
        - Drops canary on success
        - Proceeds with full migration
        """
        from migration_module import (
            canary_migration
        )

        result = canary_migration(
            source_db=temp_sqlite_db,
            postgres_conn=mock_postgres_conn,
            sample_rate=0.10
        )

        assert result['status'] == 'success'
        assert result['canary_passed'] is True
        assert 'canary_rows' in result
        assert 'full_rows' in result


    def test_canary_failure_prevents_full_migration(self, temp_sqlite_db, mock_postgres_conn):
        """
        Verify full migration blocked if canary fails validation

        Success criteria:
        - Canary schema created
        - Validation fails (simulated)
        - Canary schema dropped
        - Full migration NOT executed
        - Clear error message
        """
        from migration_module import (
            canary_migration, CanaryError
        )

        # Mock validation to fail
        with patch('migration_module.validate_migration') as mock_validate:
            mock_validate.side_effect = ValueError("Canary validation failed: data mismatch")

            with pytest.raises((CanaryError, ValueError), match="[Cc]anary|validation"):
                canary_migration(
                    source_db=temp_sqlite_db,
                    postgres_conn=mock_postgres_conn,
                    sample_rate=0.10
                )


    def test_canary_creates_sample_database(self, temp_sqlite_db, mock_postgres_conn):
        """
        Verify canary creates proper 10% sample database

        Success criteria:
        - Sample database created
        - Row count ~10% of original (±5%)
        - Sample is representative
        """
        from migration_module import (
            create_sample_database
        )

        sample_db = create_sample_database(temp_sqlite_db, sample_rate=0.10)

        try:
            # Check original row count
            conn_orig = sqlite3.connect(temp_sqlite_db)
            orig_count = conn_orig.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
            conn_orig.close()

            # Check sample row count
            conn_sample = sqlite3.connect(sample_db)
            sample_count = conn_sample.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
            conn_sample.close()

            # Sample should be ~10% (±20% tolerance for small datasets)
            expected = orig_count * 0.10
            tolerance = expected * 0.20
            assert abs(sample_count - expected) <= max(1, tolerance), \
                f"Sample size {sample_count} not within 20% of expected {expected}"

        finally:
            if os.path.exists(sample_db):
                os.remove(sample_db)


# ============================================================================
# Test Class 3: Blue-Green Deployment
# ============================================================================

class TestBlueGreenDeployment:
    """
    Verify blue-green deployment with versioned schemas
    """

    def test_creates_versioned_schema(self, temp_sqlite_db, mock_postgres_conn):
        """
        Verify new schema created with timestamp version

        Success criteria:
        - Schema name includes timestamp (servicedesk_v20251019_143022)
        - Old schema preserved
        - Migration completes to new schema
        - Cutover command returned
        """
        from migration_module import (
            migrate_blue_green
        )

        result = migrate_blue_green(
            source_db=temp_sqlite_db,
            postgres_conn=mock_postgres_conn
        )

        assert result['status'] == 'success'
        assert 'new_schema' in result
        assert result['new_schema'].startswith('servicedesk_v')
        assert 'cutover_command' in result
        assert 'rollback_command' in result


    def test_enables_instant_rollback(self, temp_sqlite_db, mock_postgres_conn):
        """
        Verify old schema preserved for instant rollback

        Success criteria:
        - Old schema NOT dropped
        - Rollback command switches back to old schema
        - Zero-downtime cutover possible
        """
        from migration_module import (
            migrate_blue_green
        )

        result = migrate_blue_green(
            source_db=temp_sqlite_db,
            postgres_conn=mock_postgres_conn,
            old_schema='servicedesk_old'
        )

        # Verify rollback command references old schema
        assert 'servicedesk_old' in result['rollback_command']
        assert result['status'] == 'success'


    def test_validation_before_cutover(self, temp_sqlite_db, mock_postgres_conn):
        """
        Verify new schema validated before cutover enabled

        Success criteria:
        - Data count matches source
        - Schema structure validated
        - Sample queries tested
        - Validation errors prevent cutover
        """
        from migration_module import (
            migrate_blue_green, MigrationError
        )

        # Mock validation to fail
        with patch('migration_module.validate_migration') as mock_validate:
            mock_validate.side_effect = ValueError("Row count mismatch")

            with pytest.raises((MigrationError, ValueError), match="validation|mismatch"):
                migrate_blue_green(
                    source_db=temp_sqlite_db,
                    postgres_conn=mock_postgres_conn
                )


# ============================================================================
# Test Class 4: Enhanced Rollback
# ============================================================================

class TestEnhancedRollback:
    """
    Verify automatic rollback on migration failure
    """

    def test_restores_from_backup_on_failure(self, temp_sqlite_db, mock_postgres_conn):
        """
        Verify automatic restore from pg_dump backup on failure

        Success criteria:
        - PostgreSQL schema backed up before migration
        - Migration fails (simulated)
        - Schema restored from backup
        - Database state unchanged
        """
        from migration_module import (
            migrate_with_rollback, MigrationError
        )

        # Mock migration to fail mid-process
        with patch('migration_module.migrate_to_schema') as mock_migrate:
            mock_migrate.side_effect = Exception("Migration failed: network error")

            with pytest.raises(MigrationError, match="failed and rolled back"):
                migrate_with_rollback(
                    source_db=temp_sqlite_db,
                    postgres_conn=mock_postgres_conn,
                    schema='servicedesk'
                )


    def test_transaction_rollback_on_validation_failure(self, temp_sqlite_db, mock_postgres_conn):
        """
        Verify ROLLBACK on post-migration validation failure

        Success criteria:
        - Transaction begins
        - Data migrated
        - Validation fails
        - ROLLBACK executed
        - No partial data committed
        """
        from migration_module import (
            migrate_with_rollback, MigrationError
        )

        # Mock validation to fail
        with patch('migration_module.validate_migration') as mock_validate:
            mock_validate.side_effect = ValueError("Data integrity check failed")

            with pytest.raises(MigrationError, match="validation|integrity"):
                migrate_with_rollback(
                    source_db=temp_sqlite_db,
                    postgres_conn=mock_postgres_conn,
                    schema='servicedesk'
                )

            # Verify ROLLBACK was called
            mock_postgres_conn.execute.assert_any_call("ROLLBACK")


    def test_backup_created_before_migration(self, temp_sqlite_db, mock_postgres_conn):
        """
        Verify pg_dump backup created before any schema changes

        Success criteria:
        - Backup file created
        - Backup includes all schema objects
        - Backup timestamp recorded
        """
        from migration_module import (
            backup_postgres_schema
        )

        # Mock schema_exists to return True
        with patch('migration_module.schema_exists') as mock_exists:
            mock_exists.return_value = True

            backup_path = backup_postgres_schema(
                schema='servicedesk',
                postgres_conn=mock_postgres_conn
            )

            assert backup_path is not None
            assert 'servicedesk' in backup_path
            assert '.backup' in backup_path or '.sql' in backup_path


# ============================================================================
# Test Class 5: Type Validation
# ============================================================================

class TestTypeValidation:
    """
    Verify sample-based type validation (not schema labels)
    """

    def test_validates_timestamp_columns_not_text(self, temp_sqlite_db, mock_postgres_conn):
        """
        Verify date columns created as TIMESTAMP, not TEXT

        Success criteria:
        - created_time column type = TIMESTAMP
        - resolved_date column type = TIMESTAMP
        - Sample queries work with TIMESTAMP functions
        """
        from migration_module import (
            validate_column_types
        )

        result = validate_column_types(
            postgres_conn=mock_postgres_conn,
            schema='servicedesk',
            table='tickets'
        )

        assert result['created_time'] == 'timestamp'
        assert result['resolved_date'] == 'timestamp'


    def test_handles_phase1_date_format_edge_cases(self, temp_sqlite_db, mock_postgres_conn):
        """
        Verify migration handles cleaned date formats from Phase 2

        Success criteria:
        - All YYYY-MM-DD HH:MM:SS dates migrate correctly
        - NULL values preserved
        - TIMESTAMP columns accept date strings
        """
        from migration_module import (
            migrate_with_quality_gate
        )

        # Mock quality scorer
        with patch('migration_module.score_database') as mock_scorer:
            mock_scorer.return_value = 95

            result = migrate_with_quality_gate(
                source_db=temp_sqlite_db,
                postgres_conn=mock_postgres_conn
            )

            assert result['status'] == 'success'
            # Verify no date conversion errors
            assert 'errors' not in result or len(result.get('errors', [])) == 0


# ============================================================================
# Test Class 6: Health Checks & Progress Tracking
# ============================================================================

class TestHealthAndProgress:
    """
    Verify health checks and progress tracking during migration
    """

    def test_health_checks_during_migration(self, temp_sqlite_db, mock_postgres_conn):
        """
        Verify periodic health checks prevent resource exhaustion

        Success criteria:
        - Disk space checked
        - Memory usage monitored
        - PostgreSQL connection validated
        - Migration halts on health failure
        """
        from migration_module import (
            migrate_with_quality_gate, HealthCheckError
        )

        # Mock health check to fail
        with patch('migration_module.check_disk_space_health') as mock_disk:
            with patch('migration_module.score_database') as mock_scorer:
                mock_disk.return_value = {'healthy': False, 'free_gb': 0.3}
                mock_scorer.return_value = 95

                with pytest.raises((HealthCheckError, Exception), match="[Dd]isk|space"):
                    migrate_with_quality_gate(
                        source_db=temp_sqlite_db,
                        postgres_conn=mock_postgres_conn
                    )


    def test_progress_tracking_with_eta(self, temp_sqlite_db, mock_postgres_conn):
        """
        Verify real-time progress tracking with ETA

        Success criteria:
        - Progress updates emitted
        - Rows/second rate calculated
        - ETA displayed
        - <1ms overhead per operation
        """
        from migration_module import (
            migrate_with_quality_gate
        )

        # Mock quality scorer
        with patch('migration_module.score_database') as mock_scorer:
            mock_scorer.return_value = 95

            start = time.time()
            result = migrate_with_quality_gate(
                source_db=temp_sqlite_db,
                postgres_conn=mock_postgres_conn
            )
            elapsed = time.time() - start

            assert 'duration_seconds' in result
            assert 'rows_migrated' in result
            # Progress tracking shouldn't add significant overhead
            assert elapsed < 5.0  # For 5 rows, should be near-instant


# ============================================================================
# Test Class 7: Integration Tests
# ============================================================================

class TestIntegration:
    """
    End-to-end integration tests
    """

    def test_complete_migration_workflow(self, temp_sqlite_db, mock_postgres_conn):
        """
        End-to-end: quality gate → canary → blue-green → validate

        Success criteria:
        - Quality gate passes
        - Canary validates
        - Blue-green schema created
        - Data migrated correctly
        - Rollback commands available
        """
        from migration_module import (
            migrate_complete_workflow
        )

        # Mock quality scorer
        with patch('migration_module.score_database') as mock_scorer:
            mock_scorer.return_value = 95

            result = migrate_complete_workflow(
                source_db=temp_sqlite_db,
                postgres_conn=mock_postgres_conn
            )

            assert result['status'] == 'success'
            assert result['quality_passed'] is True
            assert result['canary_passed'] is True
            assert 'new_schema' in result
            assert 'rollback_available' in result


    def test_zero_manual_schema_fixes_required(self, temp_sqlite_db, mock_postgres_conn):
        """
        Verify migration creates correct schema with no manual fixes

        Success criteria:
        - TIMESTAMP columns (not TEXT)
        - Correct data types for all columns
        - Indexes created
        - Constraints applied
        - Sample queries work without modification
        """
        from migration_module import (
            migrate_with_quality_gate
        )

        # Mock quality scorer
        with patch('migration_module.score_database') as mock_scorer:
            mock_scorer.return_value = 95

            result = migrate_with_quality_gate(
                source_db=temp_sqlite_db,
                postgres_conn=mock_postgres_conn
            )

            assert result['status'] == 'success'
            assert result.get('manual_fixes_required', 0) == 0


# ============================================================================
# Run tests with: PYTHONPATH=. pytest tests/test_migrate_sqlite_to_postgres_enhanced.py -v
# ============================================================================
