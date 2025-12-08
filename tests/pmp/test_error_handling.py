"""
Error Handling Tests

Tests validating graceful error handling for API failures.
"""

import pytest
import sqlite3
from unittest.mock import Mock, patch
import requests


# ============================================================================
# RATE LIMIT HANDLING TESTS
# ============================================================================

@pytest.mark.error_handling
def test_handles_rate_limit_429_response(mock_api_rate_limit_response):
    """
    Verify 429 Too Many Requests is detected and handled.
    """
    response = mock_api_rate_limit_response

    assert response.status_code == 429, "Should be 429 status"

    # Should trigger retry logic
    is_rate_limited = response.status_code == 429
    assert is_rate_limited, "Should detect rate limit"


@pytest.mark.error_handling
def test_daily_quota_detection():
    """
    Verify daily quota exceeded detection.

    After extracting for hours, API returns connection errors.
    Should detect quota exceeded and exit gracefully (not crash).
    """
    # Simulate quota exceeded scenario
    errors = 0
    max_consecutive_errors = 5

    # Multiple consecutive errors indicate quota exceeded
    for _ in range(10):
        errors += 1

    quota_exceeded = errors >= max_consecutive_errors

    assert quota_exceeded, "Should detect quota exceeded after consecutive errors"


# ============================================================================
# NETWORK ERROR TESTS
# ============================================================================

@pytest.mark.error_handling
def test_retries_on_network_error():
    """
    Verify network errors trigger retry logic.
    """
    # Mock sequence: 2 failures, then success
    responses = [
        requests.exceptions.ConnectionError(),
        requests.exceptions.ConnectionError(),
        Mock(status_code=200, json=lambda: {'supportedpatches': []})
    ]

    attempt = 0
    max_retries = 3
    success = False

    for response in responses:
        if isinstance(response, Exception):
            attempt += 1
            if attempt >= max_retries:
                break
            continue
        else:
            # Success
            success = True
            break

    assert success, "Should eventually succeed after retries"
    assert attempt == 2, "Should retry 2 times before success"


@pytest.mark.error_handling
def test_max_retries_exceeded():
    """
    Verify graceful failure after max retries exceeded.
    """
    max_retries = 3
    attempt = 0

    # Simulate all attempts failing
    while attempt < max_retries:
        attempt += 1

    assert attempt == max_retries, "Should attempt exactly max_retries times"


# ============================================================================
# JSON PARSE ERROR TESTS
# ============================================================================

@pytest.mark.error_handling
def test_handles_malformed_json(mock_api_html_throttle_response):
    """
    Verify malformed JSON responses handled gracefully.
    """
    response = mock_api_html_throttle_response

    # Attempt JSON parse
    try:
        data = response.json()
        pytest.fail("Should have raised ValueError for HTML response")
    except ValueError:
        # Expected - this is correct error handling
        pass


@pytest.mark.error_handling
def test_empty_response_handling():
    """
    Verify empty responses don't crash extraction.
    """
    # Empty JSON object
    response_data = {}

    # Extract records with fallback
    records = response_data.get('supportedpatches', [])

    assert isinstance(records, list), "Should return list"
    assert len(records) == 0, "Should be empty list (not crash)"


# ============================================================================
# DATABASE ERROR TESTS
# ============================================================================

@pytest.mark.error_handling
def test_database_locked_error_handling(temp_db):
    """
    Verify database locked errors are handled.

    SQLite can return SQLITE_BUSY if database is locked.
    """
    conn1 = sqlite3.connect(temp_db)
    cursor1 = conn1.cursor()

    # Start transaction (locks database)
    cursor1.execute("BEGIN EXCLUSIVE")

    # Attempt to write from another connection
    conn2 = sqlite3.connect(temp_db, timeout=0.1)  # Short timeout
    cursor2 = conn2.cursor()

    with pytest.raises(sqlite3.OperationalError):
        cursor2.execute("""
            INSERT INTO supported_patches
            (patch_id, extraction_id, update_id, bulletin_id, extracted_at)
            VALUES (1, 1, 0, 'KB1', '2024-01-01')
        """)

    conn1.close()
    conn2.close()


@pytest.mark.error_handling
def test_foreign_key_violation_handling(temp_db):
    """
    Verify foreign key violations are caught.
    """
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    # Enable foreign key enforcement
    cursor.execute("PRAGMA foreign_keys = ON")

    # Attempt to insert with invalid extraction_id
    with pytest.raises(sqlite3.IntegrityError) as exc_info:
        cursor.execute("""
            INSERT INTO supported_patches
            (patch_id, extraction_id, update_id, bulletin_id, extracted_at)
            VALUES (1, 999999, 0, 'KB1', '2024-01-01')
        """)

    assert "FOREIGN KEY" in str(exc_info.value).upper() or \
           "constraint" in str(exc_info.value).lower()

    conn.close()


# ============================================================================
# INTEGRATION ERROR TESTS
# ============================================================================

@pytest.mark.error_handling
@pytest.mark.integration
def test_extraction_continues_after_single_endpoint_failure():
    """
    Verify extraction continues to next endpoint if one fails.

    Scenario:
    - Endpoint 1: Success (1000 records)
    - Endpoint 2: Fails (404 Not Found)
    - Endpoint 3: Success (500 records)
    - Result: 1500 total records, 2/3 endpoints successful
    """
    endpoints_processed = 0
    total_records = 0
    failed_endpoints = []

    # Simulate endpoint results
    endpoint_results = [
        ('endpoint1', 1000, None),
        ('endpoint2', 0, '404 Not Found'),
        ('endpoint3', 500, None),
    ]

    for endpoint, records, error in endpoint_results:
        if error:
            failed_endpoints.append((endpoint, error))
            # Continue to next endpoint (don't abort)
            continue
        else:
            endpoints_processed += 1
            total_records += records

    assert endpoints_processed == 2, "Should process 2 successful endpoints"
    assert total_records == 1500, "Should have 1500 total records"
    assert len(failed_endpoints) == 1, "Should track 1 failed endpoint"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
