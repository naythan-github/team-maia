#!/usr/bin/env python3
"""
TDD Test for M365 IR Impossible Travel Schema Fix (FIX-3)

Tests that impossible travel detection uses production schema:
- Coordinates are in sign_in_logs.location_coordinates (TEXT "lat,lon")
- NOT separate latitude/longitude columns

Requirements: /tmp/M365_IR_MISSING_LOG_HANDLERS_REQUIREMENTS.md v2.0
"""

import pytest
import sqlite3
from pathlib import Path

from claude.tools.m365_ir.log_database import IRLogDatabase
from claude.tools.m365_ir.phase0_auto_checks import detect_impossible_travel


@pytest.fixture
def temp_dir(tmp_path):
    """Create temporary directory for test databases."""
    return tmp_path


@pytest.fixture
def production_schema_db(temp_dir):
    """
    Create database with PRODUCTION schema.

    Production schema:
    - sign_in_logs: Has location_coordinates TEXT (format: "lat,lon")
    - sign_in_logs: Does NOT have separate latitude/longitude columns
    """
    db = IRLogDatabase(case_id="PIR-SCHEMA-TEST-004", base_path=str(temp_dir))
    db.create()

    conn = sqlite3.connect(db.db_path)

    # Insert sign-in logs with location_coordinates (production format)
    # Scenario: NYC (40.7128,-74.0060) to Tokyo (35.6762,139.6503) in 2 hours
    # Distance: ~6,700 miles = impossible at 3,350 mph (threshold 500 mph)
    conn.execute("""
        INSERT INTO sign_in_logs
        (timestamp, user_principal_name, ip_address, location_country, location_coordinates, imported_at)
        VALUES
            ('2025-01-01 10:00:00', 'user1@example.com', '1.2.3.4', 'US', '40.7128,-74.0060', '2025-01-01 00:00:00'),
            ('2025-01-01 12:00:00', 'user1@example.com', '5.6.7.8', 'JP', '35.6762,139.6503', '2025-01-01 00:00:00')
    """)

    # Normal travel: NYC to LA in 6 hours (reasonable for flight)
    # Distance: ~2,800 miles = 467 mph (within threshold)
    conn.execute("""
        INSERT INTO sign_in_logs
        (timestamp, user_principal_name, ip_address, location_country, location_coordinates, imported_at)
        VALUES
            ('2025-01-02 08:00:00', 'user2@example.com', '1.2.3.4', 'US', '40.7128,-74.0060', '2025-01-01 00:00:00'),
            ('2025-01-02 14:00:00', 'user2@example.com', '9.10.11.12', 'US', '34.0522,-118.2437', '2025-01-01 00:00:00')
    """)

    # NULL coordinates (should be ignored)
    conn.execute("""
        INSERT INTO sign_in_logs
        (timestamp, user_principal_name, ip_address, location_country, location_coordinates, imported_at)
        VALUES
            ('2025-01-03 10:00:00', 'user3@example.com', '1.2.3.4', 'US', NULL, '2025-01-01 00:00:00')
    """)

    conn.commit()
    conn.close()

    return db.db_path


def test_impossible_travel_production_schema(production_schema_db):
    """
    Test that detect_impossible_travel() works with production schema.

    This test will FAIL with current implementation because:
    - Current code queries latitude, longitude (don't exist)
    - Should query location_coordinates and parse "lat,lon" string
    """
    # This should NOT raise "no such column: latitude" error
    result = detect_impossible_travel(production_schema_db, speed_threshold_mph=500)

    # Verify structure
    assert 'impossible_travel_events' in result
    assert 'risk_level' in result

    # Should detect NYC → Tokyo as impossible (3,350 mph)
    events = result['impossible_travel_events']
    assert len(events) == 1, f"Expected 1 impossible travel event, got {len(events)}"

    # Verify event details
    event = events[0]
    assert event['upn'] == 'user1@example.com'
    assert event['login1']['country'] == 'US'
    assert event['login2']['country'] == 'JP'
    assert event['speed_mph'] > 500  # Exceeds threshold

    # Risk level should be CRITICAL
    assert result['risk_level'] == 'CRITICAL'


def test_impossible_travel_normal_speed(production_schema_db):
    """
    Test that normal travel speed doesn't trigger alerts.
    """
    # User2 travels NYC → LA in 6 hours (467 mph - within threshold)
    result = detect_impossible_travel(production_schema_db, speed_threshold_mph=500)

    # Should NOT flag user2's travel as impossible
    events = result['impossible_travel_events']
    user2_events = [e for e in events if e['upn'] == 'user2@example.com']
    assert len(user2_events) == 0, f"Normal travel incorrectly flagged: {user2_events}"


def test_impossible_travel_handles_null_coordinates(production_schema_db):
    """
    Test that NULL coordinates are gracefully ignored.
    """
    # user3 has NULL coordinates - should not crash
    result = detect_impossible_travel(production_schema_db, speed_threshold_mph=500)

    # Should not crash, just ignore NULL entries
    assert 'impossible_travel_events' in result


def test_impossible_travel_empty_database(temp_dir):
    """
    Test that empty database returns OK status.
    """
    db = IRLogDatabase(case_id="PIR-SCHEMA-TEST-005", base_path=str(temp_dir))
    db.create()

    result = detect_impossible_travel(db.db_path, speed_threshold_mph=500)

    # No sign-ins = no impossible travel
    assert result['impossible_travel_events'] == []
    assert result['risk_level'] == 'OK'


def test_impossible_travel_malformed_coordinates(temp_dir):
    """
    Test that malformed coordinates are gracefully handled.
    """
    db = IRLogDatabase(case_id="PIR-SCHEMA-TEST-006", base_path=str(temp_dir))
    db.create()

    conn = sqlite3.connect(db.db_path)

    # Insert malformed coordinates
    conn.execute("""
        INSERT INTO sign_in_logs
        (timestamp, user_principal_name, ip_address, location_country, location_coordinates, imported_at)
        VALUES
            ('2025-01-01 10:00:00', 'user1@example.com', '1.2.3.4', 'US', 'invalid', '2025-01-01 00:00:00'),
            ('2025-01-01 11:00:00', 'user1@example.com', '5.6.7.8', 'JP', '35.6762,139.6503', '2025-01-01 00:00:00')
    """)

    conn.commit()
    conn.close()

    # Should not crash on malformed data
    result = detect_impossible_travel(db.db_path, speed_threshold_mph=500)

    # Malformed coordinate should be skipped
    assert 'impossible_travel_events' in result
