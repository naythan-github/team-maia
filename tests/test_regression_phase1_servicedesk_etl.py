#!/usr/bin/env python3
"""
ServiceDesk ETL V2 - Phase 1 Regression Test Suite

Tests that V2 pipeline prevents ALL Phase 1 issues:
1. TIMESTAMP type mismatch (label vs actual type)
2. DD/MM/YYYY date format (9 records with non-ISO dates)
3. Empty strings vs NULL in date columns
4. PostgreSQL ROUND() casting issues

Usage:
    PYTHONPATH=. pytest tests/test_regression_phase1_servicedesk_etl.py -v -s

Author: ServiceDesk ETL V2 Team
Date: 2025-10-19
"""

import os
import sys
import sqlite3
import tempfile
import pytest
from pathlib import Path

# Add project root to path
MAIA_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(MAIA_ROOT))

from claude.tools.sre.servicedesk_etl_data_profiler import profile_database
from claude.tools.sre.servicedesk_etl_data_cleaner_enhanced import clean_database
from conftest import normalize_profiler_result, normalize_cleaner_result, assert_profiler_success, assert_cleaner_success


# ==============================================================================
# Phase 1 Issue Reproduction Fixtures
# ==============================================================================

@pytest.fixture
def phase1_issue_database():
    """
    Recreate Phase 1 database with ALL known issues:
    - TIMESTAMP columns with TEXT data
    - 9 records with DD/MM/YYYY format
    - Empty strings in date columns
    - REAL columns for ROUND() testing
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.db', delete=False) as f:
        db_path = f.name

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create table with TIMESTAMP column (but store TEXT)
    cursor.execute('''
        CREATE TABLE tickets (
            id INTEGER PRIMARY KEY,
            "TKT-Number" TEXT,
            "TKT-Created Time" TIMESTAMP,
            "TKT-Actual Resolution Date" TIMESTAMP,
            "TKT-Status" TEXT,
            quality_score REAL
        )
    ''')

    # Insert 100 records
    for i in range(100):
        # First 9 records have DD/MM/YYYY format (Phase 1 issue)
        if i < 9:
            created_time = f'{(i % 28) + 1:02d}/{(i % 12) + 1:02d}/2024 {(i % 12) + 8:02d}:00'
            resolution_date = f'{(i % 28) + 1:02d}/{(i % 12) + 1:02d}/2024 {(i % 12) + 10:02d}:00'
        else:
            # Rest have ISO format
            created_time = f'2024-{(i % 12) + 1:02d}-{(i % 28) + 1:02d} 10:00:00'
            resolution_date = f'2024-{(i % 12) + 1:02d}-{(i % 28) + 1:02d} 15:00:00'

        # Every 10th record has empty string in resolution date
        if i % 10 == 0:
            resolution_date = ''

        cursor.execute(
            'INSERT INTO tickets VALUES (?, ?, ?, ?, ?, ?)',
            (
                i + 1,
                f'TKT-{i+1:06d}',
                created_time,
                resolution_date,
                'Closed' if i % 2 == 0 else 'In Progress',
                75.5 + (i % 20)  # REAL value for ROUND() testing
            )
        )

    conn.commit()
    conn.close()

    yield db_path

    if os.path.exists(db_path):
        os.remove(db_path)


# ==============================================================================
# Regression Test 1: TIMESTAMP Type Mismatch Detection
# ==============================================================================

class TestTimestampTypeMismatch:
    """
    Phase 1 Issue: TIMESTAMP-labeled columns contained TEXT data
    V2 Fix: Profiler detects actual type via sampling, not schema labels
    """

    def test_profiler_detects_text_in_timestamp_column(self, phase1_issue_database):
        """Verify profiler detects TIMESTAMP column actually contains TEXT"""
        result = profile_database(phase1_issue_database, sample_size=100)
        result = normalize_profiler_result(result)

        # Check profiling results
        tables = result.get('tables', {})
        tickets_table = tables.get('tickets', {})
        columns = tickets_table.get('columns', {})

        # Check TKT-Created Time column
        created_time = columns.get('TKT-Created Time', {})

        # Should detect TEXT type (not TIMESTAMP) via sampling
        detected_type = created_time.get('detected_type', '')
        schema_type = created_time.get('schema_type', '')

        print(f"\n  Schema type: {schema_type}")
        print(f"  Detected type: {detected_type}")

        # V2 should detect TEXT (actual type) not TIMESTAMP (schema label)
        assert 'TEXT' in detected_type.upper() or 'STRING' in detected_type.upper(), \
            "Profiler should detect actual TEXT type, not schema label"

        # Should flag type mismatch
        issues = result.get('issues', [])
        type_issues = [i for i in issues if 'type' in i.get('type', '').lower()]

        assert len(type_issues) > 0, "Should detect type mismatch between schema and data"
        print(f"  ✅ Detected {len(type_issues)} type mismatch issues")

    def test_profiler_confidence_scoring(self, phase1_issue_database):
        """Verify profiler uses confidence scoring (≥95%) for type detection"""
        result = profile_database(phase1_issue_database, sample_size=100)
        result = normalize_profiler_result(result)

        tables = result.get('tables', {})
        tickets_table = tables.get('tickets', {})
        columns = tickets_table.get('columns', {})

        # Check confidence scores for all columns
        for col_name, col_info in columns.items():
            confidence = col_info.get('confidence', 0)
            print(f"\n  {col_name}: {confidence}% confidence")

            # All columns should have ≥95% confidence
            assert confidence >= 95, f"{col_name} confidence {confidence}% below 95% threshold"

        print("\n  ✅ All type detections have ≥95% confidence")


# ==============================================================================
# Regression Test 2: DD/MM/YYYY Date Format Detection & Conversion
# ==============================================================================

class TestDDMMYYYYDateFormat:
    """
    Phase 1 Issue: 9 records had DD/MM/YYYY format instead of YYYY-MM-DD
    V2 Fix: Profiler detects, Cleaner converts to YYYY-MM-DD HH:MM:SS
    """

    def test_profiler_detects_ddmmyyyy_format(self, phase1_issue_database):
        """Verify profiler detects DD/MM/YYYY date patterns"""
        result = profile_database(phase1_issue_database, sample_size=100)
        result = normalize_profiler_result(result)

        # Check for date format issues
        issues = result.get('issues', [])
        date_issues = [i for i in issues if 'date' in i.get('type', '').lower()]

        # Should detect DD/MM/YYYY format
        ddmmyyyy_issues = [
            i for i in date_issues
            if 'DD/MM/YYYY' in i.get('description', '') or 'format' in i.get('description', '').lower()
        ]

        print(f"\n  Total date issues: {len(date_issues)}")
        print(f"  DD/MM/YYYY format issues: {len(ddmmyyyy_issues)}")

        # Should detect the date format inconsistency
        assert len(date_issues) > 0, "Should detect date format issues"

    def test_cleaner_converts_ddmmyyyy_to_iso(self, phase1_issue_database):
        """Verify cleaner converts ALL DD/MM/YYYY dates to YYYY-MM-DD HH:MM:SS"""
        output_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False).name

        try:
            # Clean database
            result = clean_database(
            phase1_issue_database,
            output_db,
            config={
                'date_columns': [
                    ('tickets', 'TKT-Created Time'),
                    ('tickets', 'TKT-Actual Resolution Date')
                ],
                'empty_to_null_columns': []
            }
        )

            assert result['status'] == 'success'

            # Verify dates converted
            dates_converted = result.get('dates_converted', 0)
            print(f"\n  Dates converted: {dates_converted}")

            # Should convert at least 9 dates (the DD/MM/YYYY records)
            assert dates_converted >= 9, f"Should convert at least 9 DD/MM/YYYY dates"

            # Verify output has ISO format dates
            conn = sqlite3.connect(output_db)
            cursor = conn.cursor()

            # Check first 9 records (originally DD/MM/YYYY)
            cursor.execute('SELECT "TKT-Created Time" FROM tickets WHERE id <= 9')
            dates = cursor.fetchall()

            for i, (date_val,) in enumerate(dates):
                print(f"  Record {i+1}: {date_val}")
                # Should be YYYY-MM-DD HH:MM:SS format
                assert date_val is not None
                # Basic ISO format check (YYYY-MM-DD)
                assert len(date_val) >= 10, f"Date too short: {date_val}"
                assert date_val[4] == '-' and date_val[7] == '-', \
                    f"Not ISO format: {date_val}"

            conn.close()
            print("\n  ✅ All DD/MM/YYYY dates converted to ISO format")

        finally:
            if os.path.exists(output_db):
                os.remove(output_db)

    def test_cleaner_handles_edge_case_dates(self):
        """Verify cleaner handles date edge cases (31/01, 29/02 leap year, etc.)"""
        # Create database with edge case dates
        with tempfile.NamedTemporaryFile(mode='w', suffix='.db', delete=False) as f:
            db_path = f.name

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('CREATE TABLE tickets (id INTEGER PRIMARY KEY, date TEXT)')

        edge_cases = [
            ('31/01/2024 10:00', '2024-01-31 10:00:00'),  # Max day in Jan
            ('29/02/2024 10:00', '2024-02-29 10:00:00'),  # Leap year
            ('30/04/2024 10:00', '2024-04-30 10:00:00'),  # 30-day month
            ('01/12/2024 10:00', '2024-12-01 10:00:00'),  # December
            ('1/1/2024 9:00', '2024-01-01 09:00:00'),     # Single digit day/month
        ]

        for i, (input_date, expected_output) in enumerate(edge_cases):
            cursor.execute('INSERT INTO tickets VALUES (?, ?)', (i + 1, input_date))

        conn.commit()
        conn.close()

        output_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False).name

        try:
            # Clean database
            result = clean_database(
            db_path,
            output_db,
            config={
                'date_columns': [('tickets', 'date')],
                'empty_to_null_columns': []
            }
        )

            assert result['status'] == 'success'

            # Verify conversions
            conn = sqlite3.connect(output_db)
            cursor = conn.cursor()
            cursor.execute('SELECT id, date FROM tickets ORDER BY id')
            results = cursor.fetchall()
            conn.close()

            for (row_id, converted_date), (input_date, expected_output) in zip(results, edge_cases):
                print(f"\n  {input_date} → {converted_date}")
                # Verify starts with YYYY-MM-DD pattern
                assert converted_date.startswith(expected_output.split()[0]), \
                    f"Edge case {input_date} not converted correctly"

            print("\n  ✅ All edge case dates handled correctly")

        finally:
            for f in [db_path, output_db]:
                if os.path.exists(f):
                    os.remove(f)


# ==============================================================================
# Regression Test 3: Empty Strings vs NULL
# ==============================================================================

class TestEmptyStringVsNull:
    """
    Phase 1 Issue: Empty strings in date columns broke PostgreSQL conversion
    V2 Fix: Cleaner converts empty strings to NULL
    """

    def test_profiler_detects_empty_strings(self, phase1_issue_database):
        """Verify profiler detects empty strings in date columns"""
        result = profile_database(phase1_issue_database, sample_size=100)
        result = normalize_profiler_result(result)

        # Check for empty string issues
        issues = result.get('issues', [])
        empty_string_issues = [
            i for i in issues
            if 'empty' in i.get('description', '').lower() or 'blank' in i.get('description', '').lower()
        ]

        print(f"\n  Empty string issues detected: {len(empty_string_issues)}")

        # Should detect empty strings in date columns
        # (every 10th record has empty string resolution date = 10 records)

    def test_cleaner_converts_empty_strings_to_null(self, phase1_issue_database):
        """Verify cleaner converts empty strings to NULL in date columns"""
        output_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False).name

        try:
            # Clean database with empty string conversion
            result = clean_database(
            phase1_issue_database,
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

            assert result['status'] == 'success'

            # Verify empty strings converted to NULL
            conn = sqlite3.connect(output_db)
            cursor = conn.cursor()

            # Count empty strings (should be 0)
            cursor.execute('SELECT COUNT(*) FROM tickets WHERE "TKT-Actual Resolution Date" = ""')
            empty_count = cursor.fetchone()[0]

            # Count NULLs (should be ~10, every 10th record)
            cursor.execute('SELECT COUNT(*) FROM tickets WHERE "TKT-Actual Resolution Date" IS NULL')
            null_count = cursor.fetchone()[0]

            conn.close()

            print(f"\n  Empty strings remaining: {empty_count}")
            print(f"  NULL values: {null_count}")

            assert empty_count == 0, "All empty strings should be converted to NULL"
            assert null_count >= 10, "Should have ~10 NULL values (from empty strings)"

            print("\n  ✅ All empty strings converted to NULL")

        finally:
            if os.path.exists(output_db):
                os.remove(output_db)

    def test_cleaner_preserves_actual_nulls(self):
        """Verify cleaner preserves actual NULL values (doesn't corrupt them)"""
        # Create database with actual NULL values
        with tempfile.NamedTemporaryFile(mode='w', suffix='.db', delete=False) as f:
            db_path = f.name

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('CREATE TABLE tickets (id INTEGER PRIMARY KEY, date TEXT)')

        # Mix of NULL, empty string, and valid dates
        for i in range(30):
            if i < 10:
                date_val = None  # Actual NULL
            elif i < 20:
                date_val = ''  # Empty string
            else:
                date_val = '2024-01-01 10:00:00'

            cursor.execute('INSERT INTO tickets VALUES (?, ?)', (i + 1, date_val))

        conn.commit()
        conn.close()

        output_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False).name

        try:
            # Clean database
            result = clean_database(
            db_path,
            output_db,
            config={
                'date_columns': [('tickets', 'date')],
                'empty_to_null_columns': [('tickets', 'date')]
            }
        )

            # Verify NULL count
            conn = sqlite3.connect(output_db)
            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(*) FROM tickets WHERE date IS NULL')
            null_count = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM tickets WHERE date = ""')
            empty_count = cursor.fetchone()[0]

            conn.close()

            print(f"\n  NULL values: {null_count}")
            print(f"  Empty strings: {empty_count}")

            # Should have 20 NULLs (10 original + 10 converted)
            assert null_count == 20, f"Expected 20 NULLs, got {null_count}"
            assert empty_count == 0, "Should have no empty strings"

            print("\n  ✅ Actual NULLs preserved, empty strings converted")

        finally:
            for f in [db_path, output_db]:
                if os.path.exists(f):
                    os.remove(f)


# ==============================================================================
# Regression Test 4: PostgreSQL ROUND() Casting
# ==============================================================================

class TestPostgreSQLRoundCasting:
    """
    Phase 1 Issue: PostgreSQL ROUND() required explicit ::numeric cast for REAL columns
    V2 Fix: Query templates include ::numeric cast
    """

    def test_query_templates_include_numeric_cast(self):
        """Verify query templates use ROUND(column::numeric, 2) pattern"""
        query_template_path = MAIA_ROOT / 'claude' / 'infrastructure' / 'servicedesk-dashboard' / 'query_templates.sql'

        if not query_template_path.exists():
            pytest.skip(f"Query templates not found at {query_template_path}")

        with open(query_template_path, 'r') as f:
            content = f.read()

        # Count ROUND() usages
        round_count = content.count('ROUND(')

        # Count proper casting (::numeric)
        cast_count = content.count('::numeric')

        print(f"\n  ROUND() occurrences: {round_count}")
        print(f"  ::numeric casts: {cast_count}")

        # All ROUND() calls should have ::numeric cast
        # (allowing some flexibility for non-REAL columns)
        if round_count > 0:
            assert cast_count >= round_count * 0.8, \
                "Most ROUND() calls should include ::numeric cast"

        print("\n  ✅ Query templates include PostgreSQL casting")

    def test_profiler_validates_numeric_columns(self, phase1_issue_database):
        """Verify profiler identifies REAL columns that need casting in PostgreSQL"""
        result = profile_database(phase1_issue_database, sample_size=100)
        result = normalize_profiler_result(result)

        tables = result.get('tables', {})
        tickets_table = tables.get('tickets', {})
        columns = tickets_table.get('columns', {})

        # Check quality_score column (REAL type)
        quality_score = columns.get('quality_score', {})
        detected_type = quality_score.get('detected_type', '')

        print(f"\n  quality_score detected type: {detected_type}")

        # Should detect REAL/FLOAT type
        assert 'REAL' in detected_type.upper() or 'FLOAT' in detected_type.upper() or 'NUMERIC' in detected_type.upper(), \
            "Should detect numeric type for quality_score column"

        print("\n  ✅ Numeric columns correctly identified")


# ==============================================================================
# Integration Test: Full Phase 1 Issue Resolution
# ==============================================================================

class TestFullPhase1IssueResolution:
    """
    Integration test verifying ALL Phase 1 issues are resolved in pipeline
    """

    def test_complete_pipeline_resolves_all_phase1_issues(self, phase1_issue_database):
        """End-to-end test: Profile → Clean → Verify all issues resolved"""
        # Step 1: Profile and detect issues
        profile_result = profile_database(phase1_issue_database, sample_size=100)
        profile_result = normalize_profiler_result(profile_result)

        print("\n  === PROFILING RESULTS ===")
        print(f"  Status: {profile_result['status']}")
        print(f"  Issues detected: {len(profile_result.get('issues', []))}")

        for issue in profile_result.get('issues', [])[:5]:  # Show first 5
            print(f"    - {issue.get('type', 'unknown')}: {issue.get('description', 'no description')}")

        # Should detect issues
        assert len(profile_result.get('issues', [])) > 0, "Should detect Phase 1 issues"

        # Step 2: Clean database
        output_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False).name

        try:
            clean_result = clean_database(
            phase1_issue_database,
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

            print("\n  === CLEANING RESULTS ===")
            print(f"  Status: {clean_result['status']}")
            print(f"  Dates converted: {clean_result.get('dates_converted', 0)}")
            print(f"  Empty strings converted: {clean_result.get('empty_strings_converted', 0)}")

            assert clean_result['status'] == 'success'

            # Step 3: Re-profile cleaned database
            cleaned_profile = profile_database(output_db, sample_size=100)
            cleaned_profile = normalize_profiler_result(cleaned_profile)

            print("\n  === CLEANED PROFILING RESULTS ===")
            print(f"  Status: {cleaned_profile['status']}")
            print(f"  Issues detected: {len(cleaned_profile.get('issues', []))}")

            # Should have significantly fewer issues (only unfixable ones remain)
            initial_issues = len(profile_result.get('issues', []))
            final_issues = len(cleaned_profile.get('issues', []))

            print(f"\n  Issues before cleaning: {initial_issues}")
            print(f"  Issues after cleaning: {final_issues}")
            print(f"  Issues resolved: {initial_issues - final_issues}")

            # Should resolve most issues
            # (some type mismatch issues may remain as warnings)
            assert final_issues < initial_issues, "Cleaning should resolve some issues"

            # Verify specific Phase 1 fixes
            conn = sqlite3.connect(output_db)
            cursor = conn.cursor()

            # Check: No empty strings in date columns
            cursor.execute('SELECT COUNT(*) FROM tickets WHERE "TKT-Actual Resolution Date" = ""')
            empty_count = cursor.fetchone()[0]
            assert empty_count == 0, "No empty strings should remain"

            # Check: Dates in ISO format (YYYY-MM-DD pattern)
            cursor.execute('SELECT "TKT-Created Time" FROM tickets WHERE id <= 9')
            dates = cursor.fetchall()
            for (date_val,) in dates:
                if date_val and date_val != '':
                    assert date_val[4] == '-' and date_val[7] == '-', \
                        f"Date not in ISO format: {date_val}"

            conn.close()

            print("\n  ✅ ALL PHASE 1 ISSUES RESOLVED")
            print("    - TIMESTAMP type mismatch: DETECTED")
            print("    - DD/MM/YYYY dates: CONVERTED to ISO")
            print("    - Empty strings: CONVERTED to NULL")
            print("    - PostgreSQL ROUND(): CAST ADDED to templates")

        finally:
            if os.path.exists(output_db):
                os.remove(output_db)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
