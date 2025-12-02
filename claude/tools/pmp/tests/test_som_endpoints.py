"""
TDD Tests for SOM (Scope of Management) Endpoints

Following TDD cycle:
1. RED: Write failing tests
2. GREEN: Implement minimal code to pass
3. REFACTOR: Improve implementation
"""

import pytest
import sqlite3
from pathlib import Path


@pytest.mark.critical
@pytest.mark.som
def test_som_computers_table_exists(temp_db):
    """
    Test that som_computers table exists with correct schema.

    This test will FAIL until we add the table to init_database().
    """
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    # Check table exists
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='som_computers'
    """)
    result = cursor.fetchone()
    assert result is not None, "som_computers table should exist"

    # Check has required columns
    cursor.execute("PRAGMA table_info(som_computers)")
    columns = {row[1] for row in cursor.fetchall()}

    required_columns = {'resource_id', 'extraction_id', 'raw_data', 'extracted_at'}
    assert required_columns.issubset(columns), \
           f"Missing columns: {required_columns - columns}"

    conn.close()


@pytest.mark.critical
@pytest.mark.som
def test_som_summary_table_exists(temp_db):
    """
    Test that som_summary table exists with correct schema.

    This test will FAIL until we add the table to init_database().
    """
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    # Check table exists
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='som_summary'
    """)
    result = cursor.fetchone()
    assert result is not None, "som_summary table should exist"

    conn.close()


@pytest.mark.critical
@pytest.mark.som
def test_extract_som_computers_function_exists():
    """
    Test that extract_som_computers() function exists.

    This test will FAIL until we add the function to the extractor.
    """
    from pmp_complete_intelligence_extractor_v4_resume import PMPCompleteIntelligenceExtractor

    extractor = PMPCompleteIntelligenceExtractor()
    assert hasattr(extractor, 'extract_som_computers'), \
           "Extractor should have extract_som_computers method"


@pytest.mark.critical
@pytest.mark.som
def test_extract_som_computers_preserves_records(temp_db, extraction_id):
    """
    Test that extract_som_computers() saves all records.

    Validates incremental write pattern works for SOM computers.
    """
    from pmp_complete_intelligence_extractor_v4_resume import PMPCompleteIntelligenceExtractor

    extractor = PMPCompleteIntelligenceExtractor()
    extractor.db_path = temp_db
    extractor.extraction_id = extraction_id

    # Mock 25 SOM computer records
    computers = [
        {
            'resource_id': i,
            'os_platform_name': f'Windows {i % 3 + 10}',
            'agent_installed_on': 1234567890 + i
        }
        for i in range(25)
    ]

    # Extract
    count = extractor.extract_som_computers(computers, 'som_computers')

    # Verify all saved
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM som_computers WHERE extraction_id = ?", (extraction_id,))
    db_count = cursor.fetchone()[0]
    conn.close()

    assert db_count == 25, f"Expected 25 records, got {db_count}"
    assert count == 25, f"extract_som_computers should return 25, got {count}"


@pytest.mark.som
def test_som_computers_primary_key_is_resource_id(temp_db):
    """Verify som_computers uses resource_id as PRIMARY KEY"""
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(som_computers)")
    columns = cursor.fetchall()

    # Find PRIMARY KEY column
    pk_columns = [col[1] for col in columns if col[5] == 1]  # col[5] is pk flag

    assert 'resource_id' in pk_columns, \
           "resource_id should be part of PRIMARY KEY"

    conn.close()


@pytest.mark.critical
@pytest.mark.som
def test_extract_simple_json_som_summary(temp_db, extraction_id):
    """
    Test that extract_simple_json() can handle som_summary table.

    This test will FAIL until we add som_summary case to extract_simple_json().
    """
    from pmp_complete_intelligence_extractor_v4_resume import PMPCompleteIntelligenceExtractor

    extractor = PMPCompleteIntelligenceExtractor()
    extractor.db_path = temp_db
    extractor.extraction_id = extraction_id

    # Mock SOM Summary data
    summary_data = {
        'managed_systems_count': 3448,
        'healthy_systems': 3200,
        'critical_systems': 248,
        'last_updated': 1234567890
    }

    # Extract using extract_simple_json
    count = extractor.extract_simple_json(summary_data, 'som_summary')

    # Verify record was actually written
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM som_summary WHERE extraction_id = ?", (extraction_id,))
    db_count = cursor.fetchone()[0]
    conn.close()

    assert db_count == 1, f"Expected 1 record in database, got {db_count}"
    assert count == 1, f"extract_simple_json should return 1, got {count}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "critical"])
