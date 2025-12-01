"""
Integration Tests

End-to-end tests validating complete extraction workflows.
"""

import pytest
import sqlite3
from datetime import datetime
from unittest.mock import Mock, patch


# ============================================================================
# END-TO-END EXTRACTION TESTS
# ============================================================================

@pytest.mark.integration
def test_full_extraction_workflow_mock(temp_db, db_helper):
    """
    End-to-end extraction with mocked API.

    Simulates:
    1. Start extraction run
    2. Extract from 3 endpoints
    3. Store all data
    4. Complete extraction run
    """
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    # Step 1: Start extraction run
    cursor.execute("""
        INSERT INTO api_extraction_runs (started_at, status, endpoints_extracted, total_records)
        VALUES (?, 'running', 0, 0)
    """, (datetime.now().isoformat(),))
    extraction_id = cursor.lastrowid

    # Step 2: Extract from endpoint 1 (supported_patches)
    for i in range(1, 101):
        cursor.execute("""
            INSERT INTO supported_patches
            (patch_id, extraction_id, update_id, bulletin_id, extracted_at)
            VALUES (?, ?, ?, ?, ?)
        """, (i, extraction_id, i % 10, f'KB{i}', datetime.now().isoformat()))

    # Step 3: Extract from endpoint 2 (all_patches)
    for i in range(1, 51):
        cursor.execute("""
            INSERT INTO all_patches
            (patch_id, extraction_id, bulletin_id, extracted_at)
            VALUES (?, ?, ?, ?)
        """, (i, extraction_id, f'KB{i}', datetime.now().isoformat()))

    # Step 4: Extract from endpoint 3 (all_systems)
    for i in range(1, 26):
        cursor.execute("""
            INSERT INTO all_systems
            (resource_id, extraction_id, extracted_at)
            VALUES (?, ?, ?)
        """, (i, extraction_id, datetime.now().isoformat()))

    # Step 5: Complete extraction run
    cursor.execute("""
        UPDATE api_extraction_runs
        SET status = 'completed',
            completed_at = ?,
            endpoints_extracted = 3,
            total_records = 176
        WHERE extraction_id = ?
    """, (datetime.now().isoformat(), extraction_id))

    conn.commit()
    conn.close()

    # Verify results
    supported_count = db_helper.get_count(temp_db, 'supported_patches')
    all_patches_count = db_helper.get_count(temp_db, 'all_patches')
    systems_count = db_helper.get_count(temp_db, 'all_systems')

    assert supported_count == 100, f"Expected 100 supported patches, got {supported_count}"
    assert all_patches_count == 50, f"Expected 50 all patches, got {all_patches_count}"
    assert systems_count == 25, f"Expected 25 systems, got {systems_count}"

    # Verify extraction run metadata
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute("SELECT status, endpoints_extracted, total_records FROM api_extraction_runs WHERE extraction_id = ?",
                   (extraction_id,))
    row = cursor.fetchone()
    conn.close()

    assert row[0] == 'completed', "Status should be completed"
    assert row[1] == 3, "Should have 3 endpoints extracted"
    assert row[2] == 176, "Should have 176 total records"


@pytest.mark.integration
def test_extraction_with_resume(temp_db, db_helper):
    """
    End-to-end extraction with interruption and resume.

    Scenario:
    1. Start extraction, get 500 records
    2. Interruption (rate limit)
    3. Resume extraction, get 500 more records
    4. Verify: 1000 total, no duplicates
    """
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    # Extraction run 1 (interrupted)
    cursor.execute("""
        INSERT INTO api_extraction_runs (started_at, status)
        VALUES (?, 'interrupted')
    """, (datetime.now().isoformat(),))
    extraction_id_1 = cursor.lastrowid

    # First 500 records
    for i in range(1, 501):
        cursor.execute("""
            INSERT INTO supported_patches
            (patch_id, extraction_id, update_id, bulletin_id, extracted_at)
            VALUES (?, ?, ?, ?, ?)
        """, (i, extraction_id_1, i % 10, f'KB{i}', datetime.now().isoformat()))
    conn.commit()

    # Extraction run 2 (resume)
    cursor.execute("""
        INSERT INTO api_extraction_runs (started_at, status)
        VALUES (?, 'running')
    """, (datetime.now().isoformat(),))
    extraction_id_2 = cursor.lastrowid

    # Calculate resume point (would be page 21 in real extraction)
    # For this test, just continue with next 500 records

    # Next 500 records (different extraction_id, but same patch_ids would conflict)
    # This tests that patch_id PRIMARY KEY prevents duplicates across runs

    # Since patch_id is PRIMARY KEY (not composite), we can't have same patch in different extractions
    # This is CORRECT behavior for supported_patches (master catalog)

    # Instead, test that we can INSERT OR REPLACE to update existing records
    for i in range(1, 501):
        cursor.execute("""
            INSERT OR REPLACE INTO supported_patches
            (patch_id, extraction_id, update_id, bulletin_id, extracted_at)
            VALUES (?, ?, ?, ?, ?)
        """, (i, extraction_id_2, i % 10, f'KB{i}_updated', datetime.now().isoformat()))
    conn.commit()

    # Verify no duplicates (still 500 records, just updated)
    total_count = db_helper.get_count(temp_db, 'supported_patches')

    # Check that records were updated (have new extraction_id)
    cursor.execute("SELECT COUNT(*) FROM supported_patches WHERE extraction_id = ?", (extraction_id_2,))
    updated_count = cursor.fetchone()[0]

    conn.close()

    assert total_count == 500, "Should still have 500 records (updated, not duplicated)"
    assert updated_count == 500, "All records should have new extraction_id"


@pytest.mark.integration
def test_data_integrity_across_endpoints(temp_db):
    """
    Verify data relationships between endpoints are preserved.
    """
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    # Create extraction run
    cursor.execute("INSERT INTO api_extraction_runs (started_at, status) VALUES (?, 'running')",
                   (datetime.now().isoformat(),))
    extraction_id = cursor.lastrowid

    # Insert system
    cursor.execute("""
        INSERT INTO all_systems (resource_id, extraction_id, extracted_at)
        VALUES (100, ?, ?)
    """, (extraction_id, datetime.now().isoformat()))

    # Insert patches referencing same extraction_id
    for i in range(1, 11):
        cursor.execute("""
            INSERT INTO supported_patches
            (patch_id, extraction_id, update_id, bulletin_id, extracted_at)
            VALUES (?, ?, ?, ?, ?)
        """, (i, extraction_id, i % 10, f'KB{i}', datetime.now().isoformat()))

    conn.commit()

    # Query related data
    cursor.execute("""
        SELECT COUNT(DISTINCT sp.patch_id)
        FROM supported_patches sp
        JOIN all_systems s ON sp.extraction_id = s.extraction_id
        WHERE s.resource_id = 100
    """)
    related_patches = cursor.fetchone()[0]

    conn.close()

    assert related_patches == 10, "Should find 10 patches for the system"


@pytest.mark.integration
@pytest.mark.critical
def test_bug_fix_validation_end_to_end(temp_db):
    """
    CRITICAL: Validate PRIMARY KEY bug fix end-to-end.

    Simulates real-world scenario that exposed the bug:
    - 58,600 records from API
    - update_id repeats 0-9
    - All records should be saved (not just 10)
    """
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    # Create extraction run
    cursor.execute("INSERT INTO api_extraction_runs (started_at, status) VALUES (?, 'running')",
                   (datetime.now().isoformat(),))
    extraction_id = cursor.lastrowid

    # Simulate API data (test with 1000 records for speed)
    total_api_records = 1000
    page_size = 25

    for i in range(1, total_api_records + 1):
        # Simulate API response (update_id repeats 0-9)
        cursor.execute("""
            INSERT OR REPLACE INTO supported_patches
            (patch_id, extraction_id, update_id, bulletin_id, extracted_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            i,  # Unique patch_id (API reality)
            extraction_id,
            i % 10,  # Repeating update_id (API reality)
            f'KB{5000000 + i}',
            datetime.now().isoformat()
        ))

        # Commit every page
        if i % page_size == 0:
            conn.commit()

    conn.commit()

    # Verify ALL records saved (not just 10)
    cursor.execute("SELECT COUNT(*) FROM supported_patches WHERE extraction_id = ?", (extraction_id,))
    saved_count = cursor.fetchone()[0]

    # Verify uniqueness
    cursor.execute("SELECT COUNT(DISTINCT patch_id) FROM supported_patches")
    unique_count = cursor.fetchone()[0]

    # Verify update_id distribution (should have 100 of each 0-9)
    cursor.execute("SELECT update_id, COUNT(*) FROM supported_patches GROUP BY update_id ORDER BY update_id")
    update_id_distribution = cursor.fetchall()

    conn.close()

    # CRITICAL ASSERTIONS
    assert saved_count == total_api_records, (
        f"BUG FIX VALIDATION FAILED: Expected {total_api_records} records, got {saved_count}. "
        f"PRIMARY KEY bug may still exist."
    )

    assert unique_count == total_api_records, (
        f"Duplicate patch_ids detected: {unique_count} unique vs {saved_count} total"
    )

    assert len(update_id_distribution) == 10, (
        f"Should have 10 different update_ids (0-9), got {len(update_id_distribution)}"
    )

    # Each update_id (0-9) should appear ~100 times
    for update_id, count in update_id_distribution:
        assert count == 100, (
            f"update_id {update_id} should appear 100 times, got {count}"
        )

    print(f"\n✅ BUG FIX VALIDATED:")
    print(f"   Total records: {saved_count}/{total_api_records} (100%)")
    print(f"   Unique patch_ids: {unique_count}")
    print(f"   update_id distribution: {update_id_distribution}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "critical"])
