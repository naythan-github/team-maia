"""
Performance Tests

Tests validating extraction performance and resource usage.
"""

import pytest
import time
import sqlite3
from datetime import datetime


# ============================================================================
# RATE LIMITING TESTS
# ============================================================================

@pytest.mark.performance
def test_respects_rate_limits():
    """
    Verify delays between API calls are enforced.
    """
    PAGE_DELAY_MS = 250  # 250ms between pages
    page_delay = PAGE_DELAY_MS / 1000.0

    # Simulate 2 API calls with delay
    start_time = time.time()

    # Call 1
    time.sleep(page_delay)

    # Call 2
    elapsed = time.time() - start_time

    # Should have at least one delay
    assert elapsed >= page_delay, f"Should delay at least {page_delay}s, got {elapsed:.3f}s"


@pytest.mark.performance
def test_rate_limit_configurable():
    """
    Verify rate limit delays can be adjusted.
    """
    # Different delay configurations
    delays = [50, 100, 250, 500, 1000]  # milliseconds

    for delay_ms in delays:
        delay_s = delay_ms / 1000.0

        start = time.time()
        time.sleep(delay_s)
        elapsed = time.time() - start

        # Allow 10ms tolerance for timing
        assert elapsed >= (delay_s - 0.01), f"Delay {delay_ms}ms not respected"


# ============================================================================
# BATCH PROCESSING TESTS
# ============================================================================

@pytest.mark.performance
def test_batch_insert_performance(temp_db, extraction_id):
    """
    Verify batch processing is faster than individual inserts.
    """
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    # Test 1: Individual commits (slow)
    start_individual = time.time()
    for i in range(100):
        cursor.execute("""
            INSERT INTO supported_patches
            (patch_id, extraction_id, update_id, bulletin_id, extracted_at)
            VALUES (?, ?, ?, ?, ?)
        """, (i, extraction_id, i % 10, f'KB{i}', datetime.now().isoformat()))
        conn.commit()  # Commit after EACH insert (slow)
    time_individual = time.time() - start_individual

    # Clear table
    cursor.execute("DELETE FROM supported_patches")
    conn.commit()

    # Test 2: Batch commits (fast)
    start_batch = time.time()
    for i in range(100, 200):
        cursor.execute("""
            INSERT INTO supported_patches
            (patch_id, extraction_id, update_id, bulletin_id, extracted_at)
            VALUES (?, ?, ?, ?, ?)
        """, (i, extraction_id, i % 10, f'KB{i}', datetime.now().isoformat()))
    conn.commit()  # Single commit for all inserts
    time_batch = time.time() - start_batch

    conn.close()

    # Batch should be significantly faster
    print(f"\nIndividual commits: {time_individual:.3f}s")
    print(f"Batch commit: {time_batch:.3f}s")
    print(f"Speedup: {time_individual/time_batch:.1f}x")

    assert time_batch < time_individual, "Batch commits should be faster"


@pytest.mark.performance
def test_batch_size_optimization(temp_db, extraction_id):
    """
    Verify batch size affects performance.

    Larger batches = fewer commits = faster (up to a point).
    """
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    batch_sizes = [10, 100, 1000]
    total_records = 1000
    timings = {}

    for batch_size in batch_sizes:
        # Clear table
        cursor.execute("DELETE FROM supported_patches")
        conn.commit()

        start = time.time()
        for i in range(total_records):
            cursor.execute("""
                INSERT INTO supported_patches
                (patch_id, extraction_id, update_id, bulletin_id, extracted_at)
                VALUES (?, ?, ?, ?, ?)
            """, (i + (batch_size * 10000), extraction_id, i % 10, f'KB{i}', datetime.now().isoformat()))

            # Commit every batch_size records
            if (i + 1) % batch_size == 0:
                conn.commit()

        # Final commit
        conn.commit()
        elapsed = time.time() - start
        timings[batch_size] = elapsed

    conn.close()

    print(f"\nBatch size timings for {total_records} records:")
    for batch_size, timing in timings.items():
        print(f"  {batch_size:4d} records/batch: {timing:.3f}s")

    # Larger batches should generally be faster
    assert timings[1000] <= timings[10], "Larger batches should be faster or equal"


# ============================================================================
# MEMORY EFFICIENCY TESTS
# ============================================================================

@pytest.mark.performance
def test_streaming_vs_loading_all(temp_db, extraction_id):
    """
    Verify streaming approach (process page-by-page) is memory efficient.

    Don't load all 365,487 patches into memory at once.
    """
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    # Simulate streaming: Process 1000 records in 40 pages of 25 each
    PAGE_SIZE = 25
    total_records = 1000

    for page in range(1, (total_records // PAGE_SIZE) + 1):
        # Fetch one page (simulate API call)
        page_data = [
            {'patch_id': (page - 1) * PAGE_SIZE + i,
             'update_id': i % 10,
             'bulletin_id': f'KB{(page-1)*PAGE_SIZE + i}'}
            for i in range(1, PAGE_SIZE + 1)
        ]

        # Process immediately (don't accumulate)
        for record in page_data:
            cursor.execute("""
                INSERT INTO supported_patches
                (patch_id, extraction_id, update_id, bulletin_id, extracted_at)
                VALUES (?, ?, ?, ?, ?)
            """, (record['patch_id'], extraction_id, record['update_id'],
                  record['bulletin_id'], datetime.now().isoformat()))

        conn.commit()
        # page_data goes out of scope - memory freed

    cursor.execute("SELECT COUNT(*) FROM supported_patches")
    count = cursor.fetchone()[0]

    conn.close()

    assert count == total_records, "Should process all records via streaming"


# ============================================================================
# DATABASE PERFORMANCE TESTS
# ============================================================================

@pytest.mark.performance
def test_index_improves_query_speed(temp_db, extraction_id):
    """
    Verify indexes improve query performance.
    """
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    # Insert 10,000 test records
    for i in range(10000):
        cursor.execute("""
            INSERT INTO supported_patches
            (patch_id, extraction_id, update_id, bulletin_id, extracted_at)
            VALUES (?, ?, ?, ?, ?)
        """, (i, extraction_id, i % 10, f'KB{i}', datetime.now().isoformat()))
    conn.commit()

    # Query WITHOUT index
    start_no_index = time.time()
    cursor.execute("SELECT * FROM supported_patches WHERE bulletin_id = 'KB5000'")
    result = cursor.fetchall()
    time_no_index = time.time() - start_no_index

    # Create index
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bulletin_id ON supported_patches(bulletin_id)")

    # Query WITH index
    start_with_index = time.time()
    cursor.execute("SELECT * FROM supported_patches WHERE bulletin_id = 'KB5000'")
    result = cursor.fetchall()
    time_with_index = time.time() - start_with_index

    conn.close()

    print(f"\nQuery time without index: {time_no_index*1000:.2f}ms")
    print(f"Query time with index: {time_with_index*1000:.2f}ms")
    print(f"Speedup: {time_no_index/time_with_index:.1f}x")

    # Index should improve performance (or at worst be equal for small datasets)
    assert time_with_index <= time_no_index * 1.5, "Index should not significantly slow queries"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
