"""
Schema Validation Tests - CRITICAL PATH

Tests database schema correctness against API reality.

Bug Context:
- supported_patches table used update_id (non-unique) as PRIMARY KEY
- API returns update_id as 0-9 sequential (repeats every 10 records)
- API returns patch_id as globally unique identifier
- Correct PRIMARY KEY should be patch_id

These tests validate:
1. PRIMARY KEY uses unique fields
2. Foreign key relationships valid
3. Field types match API types
4. Schema consistency across tables
"""

import pytest
import sqlite3
from pathlib import Path


# ============================================================================
# PRIMARY KEY VALIDATION TESTS
# ============================================================================

@pytest.mark.critical
@pytest.mark.schema
def test_supported_patches_primary_key_is_unique(temp_db, db_helper):
    """
    CRITICAL BUG TEST - Primary Key Uniqueness

    Verify supported_patches PRIMARY KEY is patch_id (unique), NOT update_id (repeating).

    Expected: PRIMARY KEY should be patch_id
    Actual (buggy): PRIMARY KEY is update_id (causes 99.98% data loss)

    This test FAILS with current schema.
    """
    schema = db_helper.get_schema(temp_db, 'supported_patches')

    # Current schema uses update_id (WRONG)
    current_pk = schema['primary_key']

    # Assert FAILS with buggy schema
    assert current_pk != 'update_id', (
        f"SCHEMA BUG DETECTED: PRIMARY KEY is '{current_pk}' (update_id). "
        f"update_id is NOT unique (0-9 sequential from API). "
        f"This causes INSERT OR REPLACE to overwrite records, leading to 99.98% data loss. "
        f"PRIMARY KEY MUST be 'patch_id' (globally unique)."
    )

    # Assert what it SHOULD be
    assert current_pk == 'patch_id', (
        f"PRIMARY KEY is '{current_pk}', expected 'patch_id'. "
        f"patch_id is the globally unique identifier from API."
    )


@pytest.mark.critical
@pytest.mark.schema
def test_all_patches_primary_key_correct(temp_db, db_helper):
    """
    Verify all_patches uses correct PRIMARY KEY (patch_id).

    This table is CORRECT - uses patch_id.
    Use as reference for supported_patches fix.
    """
    schema = db_helper.get_schema(temp_db, 'all_patches')

    assert schema['primary_key'] == 'patch_id', (
        f"all_patches PRIMARY KEY should be 'patch_id', got '{schema['primary_key']}'"
    )


@pytest.mark.schema
def test_installed_patches_composite_key_correct(temp_db, db_helper):
    """
    Verify installed_patches uses composite PRIMARY KEY.

    Correct schema: PRIMARY KEY (patch_id, extraction_id)
    Allows same patch in multiple extractions.
    """
    schema = db_helper.get_schema(temp_db, 'installed_patches')

    # Composite key should include both patch_id and extraction_id
    assert 'patch_id' in schema['columns']
    assert 'extraction_id' in schema['columns']

    # Verify PRIMARY KEY in CREATE statement
    assert 'PRIMARY KEY (patch_id, extraction_id)' in schema['create_sql'] or \
           'PRIMARY KEY(patch_id, extraction_id)' in schema['create_sql'], \
           "installed_patches should have composite PRIMARY KEY (patch_id, extraction_id)"


@pytest.mark.schema
def test_missing_patches_composite_key_correct(temp_db, db_helper):
    """
    Verify missing_patches uses composite PRIMARY KEY.

    Correct schema: PRIMARY KEY (patch_id, extraction_id)
    """
    schema = db_helper.get_schema(temp_db, 'missing_patches')

    assert 'patch_id' in schema['columns']
    assert 'extraction_id' in schema['columns']

    assert 'PRIMARY KEY (patch_id, extraction_id)' in schema['create_sql'] or \
           'PRIMARY KEY(patch_id, extraction_id)' in schema['create_sql'], \
           "missing_patches should have composite PRIMARY KEY (patch_id, extraction_id)"


# ============================================================================
# FOREIGN KEY VALIDATION TESTS
# ============================================================================

@pytest.mark.schema
def test_foreign_key_references_valid(temp_db):
    """
    Verify all FOREIGN KEY references point to existing tables.

    All patch tables should reference api_extraction_runs(extraction_id).
    """
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    # Tables with foreign keys
    tables_with_fks = [
        'supported_patches',
        'all_patches',
        'installed_patches',
        'missing_patches',
        'all_systems'
    ]

    for table in tables_with_fks:
        cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,))
        create_sql = cursor.fetchone()

        if create_sql:
            create_sql = create_sql[0]
            assert 'FOREIGN KEY' in create_sql, f"{table} should have FOREIGN KEY constraint"
            assert 'REFERENCES api_extraction_runs(extraction_id)' in create_sql, \
                   f"{table} should reference api_extraction_runs(extraction_id)"

    conn.close()


@pytest.mark.schema
def test_foreign_key_enforcement(temp_db, extraction_id):
    """
    Verify foreign key constraints are enforced.

    Attempt to insert record with invalid extraction_id should fail.
    """
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    # Enable foreign key enforcement
    cursor.execute("PRAGMA foreign_keys = ON")

    # Attempt to insert with invalid extraction_id
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("""
            INSERT INTO supported_patches
            (update_id, extraction_id, bulletin_id, extracted_at)
            VALUES (?, ?, ?, ?)
        """, (0, 999999, 'KB_INVALID', '2024-01-01T00:00:00'))

    conn.close()


# ============================================================================
# FIELD TYPE VALIDATION TESTS
# ============================================================================

@pytest.mark.schema
def test_timestamp_fields_are_integer(temp_db, db_helper):
    """
    Verify timestamp fields use INTEGER (Unix epoch).

    API returns timestamps as integers, not strings.
    Correct: INTEGER
    Incorrect: TEXT
    """
    schema = db_helper.get_schema(temp_db, 'supported_patches')

    # Get column info
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(supported_patches)")
    columns = {col[1]: col[2] for col in cursor.fetchall()}  # name: type
    conn.close()

    # Verify timestamp fields are INTEGER
    if 'patch_updated_time' in columns:
        assert columns['patch_updated_time'] == 'INTEGER', \
               f"patch_updated_time should be INTEGER, got {columns['patch_updated_time']}"


@pytest.mark.schema
def test_boolean_fields_are_integer(temp_db):
    """
    Verify boolean fields use INTEGER (0/1).

    SQLite doesn't have native BOOLEAN type.
    Convention: INTEGER with 0 (false) or 1 (true)
    """
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(supported_patches)")
    columns = {col[1]: col[2] for col in cursor.fetchall()}
    conn.close()

    if 'is_superceded' in columns:
        assert columns['is_superceded'] == 'INTEGER', \
               f"is_superceded (boolean) should be INTEGER, got {columns['is_superceded']}"


@pytest.mark.schema
def test_id_fields_are_integer(temp_db):
    """
    Verify ID fields use INTEGER type.

    All IDs from API are integers.
    """
    tables_and_id_fields = [
        ('supported_patches', 'update_id'),
        ('all_patches', 'patch_id'),
        ('all_systems', 'resource_id'),
    ]

    conn = sqlite3.connect(temp_db)

    for table, id_field in tables_and_id_fields:
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table})")
        columns = {col[1]: col[2] for col in cursor.fetchall()}

        if id_field in columns:
            assert columns[id_field] == 'INTEGER', \
                   f"{table}.{id_field} should be INTEGER, got {columns[id_field]}"

    conn.close()


# ============================================================================
# SCHEMA CONSISTENCY TESTS
# ============================================================================

@pytest.mark.schema
def test_all_patch_tables_have_extraction_id(temp_db):
    """
    Verify all patch tables include extraction_id for run isolation.
    """
    patch_tables = [
        'supported_patches',
        'all_patches',
        'installed_patches',
        'missing_patches'
    ]

    conn = sqlite3.connect(temp_db)

    for table in patch_tables:
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [col[1] for col in cursor.fetchall()]

        assert 'extraction_id' in columns, \
               f"{table} should have extraction_id column for run isolation"

    conn.close()


@pytest.mark.schema
def test_all_tables_have_extracted_at_timestamp(temp_db):
    """
    Verify all data tables have extracted_at timestamp for audit trail.
    """
    data_tables = [
        'supported_patches',
        'all_patches',
        'installed_patches',
        'missing_patches',
        'all_systems'
    ]

    conn = sqlite3.connect(temp_db)

    for table in data_tables:
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [col[1] for col in cursor.fetchall()]

        assert 'extracted_at' in columns, \
               f"{table} should have extracted_at timestamp"

    conn.close()


@pytest.mark.schema
def test_raw_data_field_is_text(temp_db):
    """
    Verify raw_data fields use TEXT type for JSON storage.
    """
    tables_with_raw_data = [
        'supported_patches',
        'all_patches',
        'all_systems'
    ]

    conn = sqlite3.connect(temp_db)

    for table in tables_with_raw_data:
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table})")
        columns = {col[1]: col[2] for col in cursor.fetchall()}

        if 'raw_data' in columns:
            assert columns['raw_data'] == 'TEXT', \
                   f"{table}.raw_data should be TEXT (for JSON), got {columns['raw_data']}"

    conn.close()


# ============================================================================
# CORRECTED SCHEMA TESTS (Post-Fix Validation)
# ============================================================================

@pytest.mark.schema
def test_corrected_schema_has_patch_id_primary_key(temp_db_corrected, db_helper):
    """
    Test CORRECTED schema with patch_id as PRIMARY KEY.

    This test validates the FIX works correctly.
    """
    schema = db_helper.get_schema(temp_db_corrected, 'supported_patches')

    assert schema['primary_key'] == 'patch_id', \
           f"Corrected schema should use patch_id as PRIMARY KEY, got {schema['primary_key']}"

    # Verify update_id still exists as regular column (not PRIMARY KEY)
    assert 'update_id' in schema['columns'], \
           "update_id should still exist as regular column"


@pytest.mark.schema
def test_corrected_schema_preserves_all_records(temp_db_corrected, db_helper):
    """
    Verify corrected schema doesn't lose data on duplicate update_ids.

    Insert 1000 patches with repeating update_ids (0-9).
    All 1000 should be preserved (not just 10).
    """
    conn = sqlite3.connect(temp_db_corrected)
    cursor = conn.cursor()

    # Create extraction run
    cursor.execute("""
        INSERT INTO api_extraction_runs (started_at, status)
        VALUES (?, 'running')
    """, ('2024-01-01T00:00:00',))
    extraction_id = cursor.lastrowid

    # Insert 1000 patches with repeating update_ids
    for i in range(1, 1001):
        cursor.execute("""
            INSERT INTO supported_patches
            (patch_id, extraction_id, update_id, bulletin_id, extracted_at)
            VALUES (?, ?, ?, ?, ?)
        """, (i, extraction_id, i % 10, f'KB{5000000+i}', '2024-01-01T00:00:00'))

    conn.commit()
    conn.close()

    # Verify all 1000 records saved
    db_count = db_helper.get_count(temp_db_corrected, 'supported_patches')

    assert db_count == 1000, \
           f"Corrected schema should preserve all 1000 records, got {db_count}"


# ============================================================================
# TABLE EXISTENCE TESTS
# ============================================================================

@pytest.mark.schema
def test_all_required_tables_exist(temp_db):
    """
    Verify all required tables are created by init_database().
    """
    required_tables = [
        'api_extraction_runs',
        'supported_patches',
        'all_patches',
        'installed_patches',
        'missing_patches',
        'all_systems'
    ]

    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = [row[0] for row in cursor.fetchall()]

    conn.close()

    for table in required_tables:
        assert table in existing_tables, f"Required table '{table}' not found in schema"


@pytest.mark.schema
def test_no_unexpected_tables_created(temp_db):
    """
    Verify no extra/unexpected tables are created.
    """
    expected_tables = [
        'api_extraction_runs',
        'supported_patches',
        'all_patches',
        'installed_patches',
        'missing_patches',
        'all_systems',
        'scan_details',
        'deployment_policies',
        'health_policy',
        'view_configurations',
        'approval_settings',
        'patch_summary'
    ]

    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = [row[0] for row in cursor.fetchall()]

    conn.close()

    # All existing tables should be in expected list (excluding SQLite internal tables)
    sqlite_internal_tables = {'sqlite_sequence', 'sqlite_stat1', 'sqlite_stat2', 'sqlite_stat3', 'sqlite_stat4'}
    for table in existing_tables:
        if table in sqlite_internal_tables:
            continue  # Skip SQLite internal tables
        assert table in expected_tables, f"Unexpected table '{table}' found in schema"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "critical"])
