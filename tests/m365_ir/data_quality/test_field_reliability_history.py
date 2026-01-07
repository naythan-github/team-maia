"""
Phase 2.1.2 - Field Reliability Historical Learning Tests

Test Objective:
    Validate historical learning system that tracks field usage outcomes across
    cases to improve field selection over time.

Key Features Tested:
    1. field_reliability_history table creation
    2. Field usage storage (store_field_usage)
    3. Historical success rate calculation
    4. Learning from past cases
    5. Default behavior when no history exists

Phase: PHASE_2_SMART_ANALYSIS (Phase 2.1.2)
Status: TDD - RED Phase (tests written, implementation pending)
TDD Cycle: Red → Green → Refactor
"""

import pytest
import sqlite3
import tempfile
import os
from datetime import datetime


@pytest.mark.phase_2_1
class TestFieldReliabilityHistory:
    """Unit tests for historical learning system."""

    def setup_method(self):
        """Create test database before each test."""
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmpdir, "test.db")
        self.history_db_path = os.path.join(self.tmpdir, "history.db")

    def teardown_method(self):
        """Clean up test database after each test."""
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_create_field_reliability_history_table(self):
        """
        Test that field_reliability_history table is created with correct schema.

        Expected schema:
        - history_id INTEGER PRIMARY KEY
        - case_id TEXT NOT NULL
        - log_type TEXT NOT NULL
        - field_name TEXT NOT NULL
        - reliability_score REAL NOT NULL
        - used_for_verification INTEGER NOT NULL (boolean)
        - verification_successful INTEGER (boolean, nullable)
        - breach_detected INTEGER (boolean, nullable)
        - notes TEXT
        - created_at TEXT NOT NULL
        """
        from claude.tools.m365_ir.field_reliability_scorer import create_history_database

        # Create history database
        create_history_database(self.history_db_path)

        # Verify table exists
        conn = sqlite3.connect(self.history_db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='field_reliability_history'
        """)
        assert cursor.fetchone() is not None, "field_reliability_history table should exist"

        # Verify schema
        cursor.execute("PRAGMA table_info(field_reliability_history)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        expected_columns = {
            'history_id': 'INTEGER',
            'case_id': 'TEXT',
            'log_type': 'TEXT',
            'field_name': 'TEXT',
            'reliability_score': 'REAL',
            'used_for_verification': 'INTEGER',
            'verification_successful': 'INTEGER',
            'breach_detected': 'INTEGER',
            'notes': 'TEXT',
            'created_at': 'TEXT'
        }

        for col_name, col_type in expected_columns.items():
            assert col_name in columns, f"Column '{col_name}' should exist"
            assert columns[col_name] == col_type, \
                f"Column '{col_name}' should be type {col_type}, got {columns[col_name]}"

        conn.close()

    def test_store_field_usage_basic(self):
        """
        Test storing field usage outcome.

        Expected: Record inserted with all fields populated correctly
        """
        from claude.tools.m365_ir.field_reliability_scorer import (
            create_history_database,
            store_field_usage
        )

        # Create history database
        create_history_database(self.history_db_path)

        # Store field usage
        store_field_usage(
            history_db_path=self.history_db_path,
            case_id="PIR-TEST-2026-01",
            log_type="sign_in_logs",
            field_name="conditional_access_status",
            reliability_score=0.85,
            used_for_verification=True,
            verification_successful=True,
            breach_detected=False,
            notes="Test usage"
        )

        # Verify record stored
        conn = sqlite3.connect(self.history_db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT case_id, log_type, field_name, reliability_score,
                   used_for_verification, verification_successful,
                   breach_detected, notes
            FROM field_reliability_history
            WHERE case_id = 'PIR-TEST-2026-01'
        """)

        row = cursor.fetchone()
        assert row is not None, "Record should be stored"

        case_id, log_type, field_name, score, used, success, breach, notes = row

        assert case_id == "PIR-TEST-2026-01"
        assert log_type == "sign_in_logs"
        assert field_name == "conditional_access_status"
        assert abs(score - 0.85) < 0.01
        assert used == 1  # True stored as 1
        assert success == 1
        assert breach == 0  # False stored as 0
        assert notes == "Test usage"

        conn.close()

    def test_historical_success_rate_no_history(self):
        """
        Test historical success rate when no history exists.

        Expected: Returns default value of 0.5 (neutral)
        """
        from claude.tools.m365_ir.field_reliability_scorer import (
            create_history_database,
            calculate_reliability_score
        )

        # Create empty history database
        create_history_database(self.history_db_path)

        # Create test table
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE sign_in_logs (
                id INTEGER PRIMARY KEY,
                status TEXT
            )
        """)
        for i in range(100):
            cursor.execute(
                "INSERT INTO sign_in_logs (status) VALUES (?)",
                ("success" if i % 2 == 0 else "failure",)
            )
        conn.commit()
        conn.close()

        # Calculate score with empty history
        score = calculate_reliability_score(
            self.db_path,
            'sign_in_logs',
            'status',
            historical_db_path=self.history_db_path
        )

        # Verify historical success rate defaults to 0.5
        assert score.historical_success_rate == 0.5, \
            f"Expected default historical_success_rate=0.5, got {score.historical_success_rate}"

    def test_historical_success_rate_all_successful(self):
        """
        Test historical success rate when all past uses were successful.

        Expected: Returns 1.0 (100% success rate)
        """
        from claude.tools.m365_ir.field_reliability_scorer import (
            create_history_database,
            store_field_usage,
            calculate_reliability_score
        )

        # Create history database
        create_history_database(self.history_db_path)

        # Store 5 successful uses
        for i in range(5):
            store_field_usage(
                history_db_path=self.history_db_path,
                case_id=f"PIR-TEST-2026-0{i}",
                log_type="sign_in_logs",
                field_name="conditional_access_status",
                reliability_score=0.85,
                used_for_verification=True,
                verification_successful=True,  # All successful
                breach_detected=False
            )

        # Create test table
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE sign_in_logs (
                id INTEGER PRIMARY KEY,
                conditional_access_status TEXT
            )
        """)
        for i in range(100):
            cursor.execute(
                "INSERT INTO sign_in_logs (conditional_access_status) VALUES (?)",
                ("success" if i % 2 == 0 else "failure",)
            )
        conn.commit()
        conn.close()

        # Calculate score with history
        score = calculate_reliability_score(
            self.db_path,
            'sign_in_logs',
            'conditional_access_status',
            historical_db_path=self.history_db_path
        )

        # Verify historical success rate is 1.0 (100%)
        assert score.historical_success_rate == 1.0, \
            f"Expected historical_success_rate=1.0 for all successful, got {score.historical_success_rate}"

    def test_historical_success_rate_mixed_results(self):
        """
        Test historical success rate with mixed successful/failed uses.

        Expected: Returns correct percentage (3/5 = 0.6)
        """
        from claude.tools.m365_ir.field_reliability_scorer import (
            create_history_database,
            store_field_usage,
            calculate_reliability_score
        )

        # Create history database
        create_history_database(self.history_db_path)

        # Store 3 successful, 2 failed uses
        results = [True, True, False, True, False]
        for i, success in enumerate(results):
            store_field_usage(
                history_db_path=self.history_db_path,
                case_id=f"PIR-TEST-2026-0{i}",
                log_type="sign_in_logs",
                field_name="status_error_code",
                reliability_score=0.60,
                used_for_verification=True,
                verification_successful=success,
                breach_detected=False
            )

        # Create test table
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE sign_in_logs (
                id INTEGER PRIMARY KEY,
                status_error_code INTEGER
            )
        """)
        for i in range(100):
            cursor.execute("INSERT INTO sign_in_logs (status_error_code) VALUES (?)", (i % 2,))
        conn.commit()
        conn.close()

        # Calculate score with history
        score = calculate_reliability_score(
            self.db_path,
            'sign_in_logs',
            'status_error_code',
            historical_db_path=self.history_db_path
        )

        # Verify historical success rate is 0.6 (3/5 = 60%)
        assert abs(score.historical_success_rate - 0.6) < 0.01, \
            f"Expected historical_success_rate=0.6 for 3/5 successful, got {score.historical_success_rate}"


# Mark all tests for Phase 2.1
pytestmark = pytest.mark.phase_2_1
