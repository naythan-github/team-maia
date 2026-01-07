"""
Phase 1.2: Data Quality Checker - TDD Tests

Test Objective:
    Validate pre-analysis quality checks that prevent wrong field selection.

Key Features:
    1. Field population analysis (detect 100% uniform fields)
    2. Discriminatory power scoring (unique_values / total_rows)
    3. Multi-field consistency checks
    4. Table-level quality scoring

Expected Behavior:
    - Detect unreliable fields (>99.5% uniform)
    - Calculate discriminatory power (0-1 score)
    - Recommend best status field for analysis
    - Fail-fast on bad data quality (optional)

Phase: PHASE_1_FOUNDATION (Phase 1.2 - Data Quality Checker)
Status: In Progress (TDD Red Phase)
TDD Cycle: Red → Green → Refactor
"""

import pytest
import sqlite3
import tempfile
from pathlib import Path


@pytest.mark.phase_1_2
class TestFieldQualityScoring:
    """Test field-level quality metrics."""

    def test_check_field_population_rate(self, temp_db):
        """
        Test that field population rate is calculated correctly.

        Population rate = (non-null records / total records) * 100

        Example:
            - 100 records, 95 non-null → 95% population rate
            - 100 records, 100 non-null → 100% population rate
            - 100 records, 0 non-null → 0% population rate
        """
        from claude.tools.m365_ir.data_quality_checker import check_field_quality

        # Setup test data: 95 populated, 5 null
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Create test table
        cursor.execute("""
            CREATE TABLE test_logs (
                id INTEGER PRIMARY KEY,
                status_field TEXT,
                location TEXT
            )
        """)

        # Add 95 populated records
        for i in range(95):
            cursor.execute("INSERT INTO test_logs (status_field, location) VALUES (?, ?)",
                         ('success', 'AU'))

        # Add 5 null records
        for i in range(5):
            cursor.execute("INSERT INTO test_logs (status_field, location) VALUES (?, ?)",
                         (None, 'AU'))

        conn.commit()
        conn.close()

        # Check field quality
        result = check_field_quality(temp_db, 'test_logs', 'status_field')

        assert result.population_rate == pytest.approx(95.0, rel=0.1), \
            "Population rate should be 95% (95 non-null / 100 total)"
        assert result.total_records == 100, "Should count all 100 records"

    def test_check_discriminatory_power(self, temp_db):
        """
        Test discriminatory power calculation (unique_values / total_rows).

        High discriminatory power = many unique values (useful for analysis)
        Low discriminatory power = few unique values (uniform, unreliable)

        Examples:
            - 100 records, 100 unique values → 1.0 (perfect, like user_id)
            - 100 records, 2 unique values → 0.02 (binary field, like success/failure)
            - 100 records, 1 unique value → 0.01 (uniform, unreliable)
        """
        from claude.tools.m365_ir.data_quality_checker import check_field_quality

        # Setup test data: 100 records, all same value (uniform)
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE test_logs (
                id INTEGER PRIMARY KEY,
                status_error_code INTEGER,
                conditional_access_status TEXT
            )
        """)

        # All records have status_error_code = 1 (uniform, unreliable)
        for i in range(100):
            cursor.execute("""
                INSERT INTO test_logs (status_error_code, conditional_access_status)
                VALUES (?, ?)
            """, (1, 'success' if i < 80 else 'failure'))

        conn.commit()
        conn.close()

        # Check discriminatory power
        uniform_result = check_field_quality(temp_db, 'test_logs', 'status_error_code')
        binary_result = check_field_quality(temp_db, 'test_logs', 'conditional_access_status')

        # status_error_code: 1 unique value / 100 rows = 0.01
        assert uniform_result.discriminatory_power == pytest.approx(0.01, rel=0.01), \
            "Uniform field should have discriminatory power ~0.01 (1/100)"

        # conditional_access_status: 2 unique values / 100 rows = 0.02
        assert binary_result.discriminatory_power == pytest.approx(0.02, rel=0.01), \
            "Binary field should have discriminatory power ~0.02 (2/100)"

    def test_detect_unreliable_field(self, temp_db):
        """
        Test detection of unreliable fields (>99.5% uniform).

        Unreliable field criteria:
            - >99.5% of values are the same (uniform)
            - OR only 1 distinct value
            - OR discriminatory power < 0.005

        Example (Oculus case):
            - status_error_code: 100% uniform (all = 1) → UNRELIABLE
            - conditional_access_status: 80% success, 20% failure → RELIABLE
        """
        from claude.tools.m365_ir.data_quality_checker import check_field_quality

        # Setup test data matching Oculus case
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE sign_in_logs (
                id INTEGER PRIMARY KEY,
                status_error_code INTEGER,
                conditional_access_status TEXT
            )
        """)

        # Add 1000 records: status_error_code = 1 (100% uniform)
        for i in range(1000):
            cursor.execute("""
                INSERT INTO sign_in_logs (status_error_code, conditional_access_status)
                VALUES (?, ?)
            """, (1, 'success' if i < 800 else 'failure'))

        conn.commit()
        conn.close()

        # Check both fields
        uniform_result = check_field_quality(temp_db, 'sign_in_logs', 'status_error_code')
        reliable_result = check_field_quality(temp_db, 'sign_in_logs', 'conditional_access_status')

        # status_error_code should be flagged as unreliable
        assert uniform_result.is_reliable is False, \
            "status_error_code should be unreliable (100% uniform)"
        assert uniform_result.distinct_values == 1, \
            "status_error_code should have only 1 distinct value"

        # conditional_access_status should be reliable
        assert reliable_result.is_reliable is True, \
            "conditional_access_status should be reliable (80/20 split)"
        assert reliable_result.distinct_values == 2, \
            "conditional_access_status should have 2 distinct values"


@pytest.mark.phase_1_2
class TestTableQualityScoring:
    """Test table-level quality metrics."""

    def test_check_table_quality_with_good_data(self, temp_db):
        """
        Test table quality scoring with high-quality data.

        Good data characteristics:
            - All required fields populated (>95%)
            - Multiple fields with good discriminatory power
            - No 100% uniform fields
            - Overall quality score >0.8
        """
        from claude.tools.m365_ir.data_quality_checker import check_table_quality

        # Setup high-quality test data
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE sign_in_logs (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                user_id TEXT,
                location_country TEXT,
                conditional_access_status TEXT
            )
        """)

        # Add 100 records with good variation
        for i in range(100):
            cursor.execute("""
                INSERT INTO sign_in_logs (timestamp, user_id, location_country, conditional_access_status)
                VALUES (?, ?, ?, ?)
            """, (
                f'2025-11-04T10:{i:02d}:00Z',
                f'user_{i % 50}@test.com',  # 50 unique users
                'AU' if i < 95 else 'US',  # 95% AU, 5% US
                'success' if i < 90 else 'failure'  # 90% success, 10% failure
            ))

        conn.commit()
        conn.close()

        # Check table quality
        result = check_table_quality(temp_db, 'sign_in_logs')

        assert result.total_records == 100, "Should count 100 records"
        assert len(result.field_scores) == 5, "Should analyze all 5 fields (including id)"
        assert result.overall_quality_score > 0.8, \
            "High-quality data should score >0.8"
        assert len(result.unreliable_fields) == 0, \
            "No fields should be unreliable"

    def test_check_table_quality_with_bad_data(self, temp_db):
        """
        Test table quality scoring with poor-quality data.

        Bad data characteristics:
            - Some fields 100% uniform
            - Low discriminatory power across fields
            - Overall quality score <0.5
            - Warnings generated
        """
        from claude.tools.m365_ir.data_quality_checker import check_table_quality

        # Setup poor-quality test data (Oculus-like scenario)
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE sign_in_logs (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                status_error_code INTEGER,
                location_country TEXT,
                conditional_access_status TEXT
            )
        """)

        # Add 100 records with status_error_code uniform (bad)
        for i in range(100):
            cursor.execute("""
                INSERT INTO sign_in_logs (timestamp, status_error_code, location_country, conditional_access_status)
                VALUES (?, ?, ?, ?)
            """, (
                f'2025-11-04T10:{i:02d}:00Z',
                1,  # ALL records have status_error_code = 1 (uniform!)
                'AU',  # ALL records AU (uniform!)
                'success' if i < 90 else 'failure'
            ))

        conn.commit()
        conn.close()

        # Check table quality
        result = check_table_quality(temp_db, 'sign_in_logs')

        assert result.overall_quality_score < 0.7, \
            "Poor-quality data should score <0.7 (2/5 fields uniform)"
        assert len(result.unreliable_fields) >= 2, \
            "Should detect status_error_code AND location_country as unreliable"
        assert len(result.warnings) > 0, \
            "Should generate warnings for uniform fields"

        # Check that warnings mention the unreliable fields
        warnings_text = ' '.join(result.warnings).lower()
        assert 'status_error_code' in warnings_text, \
            "Warnings should mention status_error_code"

    def test_recommend_best_status_field(self, temp_db):
        """
        Test auto-recommendation of best status field for analysis.

        Scenario: Multiple status fields, system should recommend most reliable one.

        Example (Oculus case):
            - status_error_code: 100% uniform (discriminatory power = 0.01) → REJECT
            - conditional_access_status: 90/10 split (discriminatory power = 0.02) → RECOMMEND
        """
        from claude.tools.m365_ir.data_quality_checker import check_table_quality

        # Setup Oculus-like data
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE sign_in_logs (
                id INTEGER PRIMARY KEY,
                status_error_code INTEGER,
                conditional_access_status TEXT,
                user_id TEXT
            )
        """)

        for i in range(100):
            cursor.execute("""
                INSERT INTO sign_in_logs (status_error_code, conditional_access_status, user_id)
                VALUES (?, ?, ?)
            """, (1, 'success' if i < 90 else 'failure', f'user_{i}'))

        conn.commit()
        conn.close()

        # Check table quality
        result = check_table_quality(temp_db, 'sign_in_logs')

        # Recommendations should mention using conditional_access_status
        recommendations_text = ' '.join(result.recommendations).lower()
        assert 'conditional_access_status' in recommendations_text, \
            "Should recommend using conditional_access_status"

        # Should warn against using status_error_code
        warnings_text = ' '.join(result.warnings).lower()
        assert 'status_error_code' in warnings_text, \
            "Should warn about status_error_code being unreliable"


@pytest.mark.phase_1_2
class TestMultiFieldConsistency:
    """Test consistency checks across multiple fields."""

    def test_check_timestamp_location_consistency(self, temp_db):
        """
        Test consistency between timestamp and location fields.

        Example inconsistency:
            - Timestamp shows 3am Australia time
            - But location is USA (timezone mismatch)

        Note: This is a placeholder test - full implementation in Phase 2.
        """
        from claude.tools.m365_ir.data_quality_checker import check_multi_field_consistency

        # Setup test data
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE sign_in_logs (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                location_country TEXT
            )
        """)

        # Add mostly consistent data
        for i in range(100):
            cursor.execute("""
                INSERT INTO sign_in_logs (timestamp, location_country)
                VALUES (?, ?)
            """, (f'2025-11-04T10:{i:02d}:00Z', 'AU'))

        conn.commit()
        conn.close()

        # Check consistency
        warnings = check_multi_field_consistency(temp_db, 'sign_in_logs')

        # For now, just check that function returns a list
        assert isinstance(warnings, list), "Should return list of warnings"
        # Phase 2 will add actual consistency logic


# Mark all tests as Phase 1.2
pytestmark = pytest.mark.phase_1_2
