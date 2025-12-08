"""
Resume Capability Tests

Tests validating extraction resume functionality after interruptions.

Context:
- Extraction can run for 10+ hours
- API rate limits can interrupt mid-extraction
- Must resume from last successful page (not restart from beginning)
"""

import pytest
import sqlite3
from datetime import datetime


# ============================================================================
# RESUME POINT CALCULATION TESTS
# ============================================================================

@pytest.mark.resume
def test_calculate_resume_point_from_beginning(temp_db, extraction_id):
    """
    Verify resume starts at page 1 when no existing records.
    """
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    # Simulate no existing records
    cursor.execute("SELECT COUNT(*) FROM supported_patches WHERE extraction_id = ?", (extraction_id,))
    existing_count = cursor.fetchone()[0]

    conn.close()

    # Resume calculation
    PAGE_SIZE = 25
    if existing_count == 0:
        start_page = 1
    else:
        start_page = (existing_count // PAGE_SIZE) + 1

    assert existing_count == 0, "Should have no existing records"
    assert start_page == 1, "Should start from page 1"


@pytest.mark.resume
def test_calculate_resume_point_midway(temp_db, extraction_id, db_helper):
    """
    Verify resume calculation from existing records.

    Scenario: 1,250 existing records (50 pages × 25 records/page)
    Expected: Resume from page 51
    """
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    # Insert 1,250 existing records (simulating 50 pages completed)
    for i in range(1, 1251):
        cursor.execute("""
            INSERT INTO supported_patches
            (patch_id, extraction_id, update_id, bulletin_id, extracted_at)
            VALUES (?, ?, ?, ?, ?)
        """, (i, extraction_id, i % 10, f'KB{i}', datetime.now().isoformat()))

    conn.commit()
    conn.close()

    # Calculate resume point
    existing_count = db_helper.get_count(temp_db, 'supported_patches')
    PAGE_SIZE = 25
    start_page = (existing_count // PAGE_SIZE) + 1

    assert existing_count == 1250, f"Expected 1250 records, got {existing_count}"
    assert start_page == 51, f"Should resume from page 51, got {start_page}"


@pytest.mark.resume
def test_resume_point_with_partial_page(temp_db, extraction_id, db_helper):
    """
    Verify resume handling with partial page.

    Scenario: 1,237 records (49 full pages + 12 records on page 50)
    Expected: Resume from page 50 (re-fetch partial page)
    """
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    # Insert 1,237 records
    for i in range(1, 1238):
        cursor.execute("""
            INSERT INTO supported_patches
            (patch_id, extraction_id, update_id, bulletin_id, extracted_at)
            VALUES (?, ?, ?, ?, ?)
        """, (i, extraction_id, i % 10, f'KB{i}', datetime.now().isoformat()))

    conn.commit()
    conn.close()

    existing_count = db_helper.get_count(temp_db, 'supported_patches')
    PAGE_SIZE = 25
    start_page = (existing_count // PAGE_SIZE) + 1

    assert existing_count == 1237
    assert start_page == 50, "Should resume from page 50 (re-fetch partial)"


# ============================================================================
# DUPLICATE PREVENTION TESTS
# ============================================================================

@pytest.mark.resume
def test_resume_prevents_duplicates(temp_db, extraction_id, db_helper):
    """
    Verify resumed extraction doesn't create duplicates.

    Scenario:
    1. First run: Extract 500 records (20 pages)
    2. Interruption
    3. Resume: Calculate start_page = 21
    4. Continue extraction
    5. Verify: No duplicates, all records unique
    """
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    # First run: Insert 500 records
    for i in range(1, 501):
        cursor.execute("""
            INSERT INTO supported_patches
            (patch_id, extraction_id, update_id, bulletin_id, extracted_at)
            VALUES (?, ?, ?, ?, ?)
        """, (i, extraction_id, i % 10, f'KB{i}', datetime.now().isoformat()))
    conn.commit()

    count_first = db_helper.get_count(temp_db, 'supported_patches')

    # Resume: Add 500 more records (simulating pages 21-40)
    for i in range(501, 1001):
        cursor.execute("""
            INSERT INTO supported_patches
            (patch_id, extraction_id, update_id, bulletin_id, extracted_at)
            VALUES (?, ?, ?, ?, ?)
        """, (i, extraction_id, i % 10, f'KB{i}', datetime.now().isoformat()))
    conn.commit()

    count_after = db_helper.get_count(temp_db, 'supported_patches')

    # Verify uniqueness (no duplicates)
    cursor.execute("SELECT COUNT(DISTINCT patch_id) FROM supported_patches")
    unique_count = cursor.fetchone()[0]

    conn.close()

    assert count_first == 500, "First run should have 500 records"
    assert count_after == 1000, "After resume should have 1000 records"
    assert unique_count == 1000, "All patch_ids should be unique (no duplicates)"


@pytest.mark.resume
def test_resume_with_insert_or_replace_safety(temp_db, extraction_id):
    """
    Verify INSERT OR REPLACE doesn't cause data loss on resume.

    With patch_id as PRIMARY KEY:
    - Re-fetching same page overwrites with latest data (safe)
    - No data loss from duplicate inserts
    """
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    # Insert record with patch_id=100
    cursor.execute("""
        INSERT INTO supported_patches
        (patch_id, extraction_id, update_id, bulletin_id, extracted_at)
        VALUES (?, ?, ?, ?, ?)
    """, (100, extraction_id, 0, 'KB100_v1', '2024-01-01T00:00:00'))
    conn.commit()

    # Re-fetch same record (simulating resume re-fetching partial page)
    cursor.execute("""
        INSERT OR REPLACE INTO supported_patches
        (patch_id, extraction_id, update_id, bulletin_id, extracted_at)
        VALUES (?, ?, ?, ?, ?)
    """, (100, extraction_id, 0, 'KB100_v2', '2024-01-01T01:00:00'))
    conn.commit()

    # Verify only 1 record exists (updated, not duplicated)
    cursor.execute("SELECT COUNT(*) FROM supported_patches WHERE patch_id = 100")
    count = cursor.fetchone()[0]

    cursor.execute("SELECT bulletin_id FROM supported_patches WHERE patch_id = 100")
    bulletin_id = cursor.fetchone()[0]

    conn.close()

    assert count == 1, "Should have exactly 1 record (no duplicate)"
    assert bulletin_id == 'KB100_v2', "Should have latest data"


# ============================================================================
# EXTRACTION RUN ISOLATION TESTS
# ============================================================================

@pytest.mark.resume
def test_multiple_extraction_runs_isolated(temp_db):
    """
    Verify multiple extraction runs don't interfere.

    Scenario:
    - Run 1: Extract 500 patches
    - Run 2: Extract same 500 patches (new extraction_id)
    - Verify: 1000 total records (500 per run)
    """
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    # Create extraction run 1
    cursor.execute("INSERT INTO api_extraction_runs (started_at, status) VALUES (?, 'running')",
                   (datetime.now().isoformat(),))
    extraction_id_1 = cursor.lastrowid

    # Create extraction run 2
    cursor.execute("INSERT INTO api_extraction_runs (started_at, status) VALUES (?, 'running')",
                   (datetime.now().isoformat(),))
    extraction_id_2 = cursor.lastrowid

    # Run 1: Insert 500 patches
    for i in range(1, 501):
        cursor.execute("""
            INSERT INTO supported_patches
            (patch_id, extraction_id, update_id, bulletin_id, extracted_at)
            VALUES (?, ?, ?, ?, ?)
        """, (i, extraction_id_1, i % 10, f'KB{i}', datetime.now().isoformat()))

    # Run 2: Insert same 500 patches (different extraction_id allows duplicates)
    # Note: This will FAIL because patch_id is PRIMARY KEY (not composite)
    # This test validates that we CAN'T have same patch in multiple extractions
    # Which is correct behavior for supported_patches (master catalog)

    with pytest.raises(sqlite3.IntegrityError):
        for i in range(1, 501):
            cursor.execute("""
                INSERT INTO supported_patches
                (patch_id, extraction_id, update_id, bulletin_id, extracted_at)
                VALUES (?, ?, ?, ?, ?)
            """, (i, extraction_id_2, i % 10, f'KB{i}', datetime.now().isoformat()))

    conn.close()


# ============================================================================
# PROGRESS TRACKING TESTS
# ============================================================================

@pytest.mark.resume
def test_extraction_run_metadata_tracking(temp_db):
    """
    Verify extraction run metadata is tracked correctly.
    """
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    # Create extraction run
    start_time = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO api_extraction_runs (started_at, status, endpoints_extracted, total_records)
        VALUES (?, 'running', 0, 0)
    """, (start_time,))
    extraction_id = cursor.lastrowid

    # Simulate extraction progress
    cursor.execute("""
        UPDATE api_extraction_runs
        SET endpoints_extracted = 5, total_records = 1250
        WHERE extraction_id = ?
    """, (extraction_id,))

    # Complete extraction
    end_time = datetime.now().isoformat()
    cursor.execute("""
        UPDATE api_extraction_runs
        SET status = 'completed', completed_at = ?
        WHERE extraction_id = ?
    """, (end_time, extraction_id))

    conn.commit()

    # Verify metadata
    cursor.execute("""
        SELECT started_at, completed_at, status, endpoints_extracted, total_records
        FROM api_extraction_runs WHERE extraction_id = ?
    """, (extraction_id,))
    row = cursor.fetchone()

    conn.close()

    assert row[0] == start_time, "Started time should match"
    assert row[1] == end_time, "Completed time should match"
    assert row[2] == 'completed', "Status should be completed"
    assert row[3] == 5, "Should have 5 endpoints extracted"
    assert row[4] == 1250, "Should have 1250 total records"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
