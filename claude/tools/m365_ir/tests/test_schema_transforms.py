#!/usr/bin/env python3
"""
TDD Tests for M365 Schema Transform Functions

Tests written FIRST per TDD methodology (Phase 264 Sprint 1.2).
Run: pytest claude/tools/m365_ir/tests/test_schema_transforms.py -v

Author: Maia System
Created: 2026-01-11 (Phase 264)
"""

import pytest
from datetime import datetime, timezone
from pathlib import Path
import sys

# Add Maia root to path
MAIA_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

from claude.tools.m365_ir.schema_transforms import (
    parse_iso_datetime,
    parse_graph_location,
    parse_graph_status,
    parse_boolean_field,
    parse_integer_field,
    normalize_conditional_access_status,
)


class TestISODateTimeParsing:
    """Test ISO 8601 datetime parsing for Graph API exports"""

    def test_parse_iso_datetime_with_z_suffix(self):
        """Parse ISO datetime with Z (UTC) suffix"""
        result = parse_iso_datetime("2025-12-04T08:19:41Z")
        assert result == datetime(2025, 12, 4, 8, 19, 41, tzinfo=timezone.utc)

    def test_parse_iso_datetime_with_milliseconds(self):
        """Parse ISO datetime with milliseconds"""
        result = parse_iso_datetime("2025-12-04T08:19:41.000Z")
        assert result == datetime(2025, 12, 4, 8, 19, 41, tzinfo=timezone.utc)

    def test_parse_iso_datetime_with_microseconds(self):
        """Parse ISO datetime with microseconds"""
        result = parse_iso_datetime("2025-12-04T08:19:41.123456Z")
        assert result == datetime(2025, 12, 4, 8, 19, 41, 123456, tzinfo=timezone.utc)

    def test_parse_iso_datetime_without_z_suffix(self):
        """Parse ISO datetime without timezone (assumes UTC)"""
        result = parse_iso_datetime("2025-12-04T08:19:41")
        assert result == datetime(2025, 12, 4, 8, 19, 41, tzinfo=timezone.utc)

    def test_parse_iso_datetime_empty_string(self):
        """Empty string returns None"""
        assert parse_iso_datetime("") is None

    def test_parse_iso_datetime_none(self):
        """None input returns None"""
        assert parse_iso_datetime(None) is None

    def test_parse_iso_datetime_invalid_format(self):
        """Invalid format raises ValueError"""
        with pytest.raises(ValueError):
            parse_iso_datetime("not-a-date")

    def test_parse_iso_datetime_real_graph_api_format(self):
        """Real Graph API export format from PIR-GOOD-SAMARITAN-777777"""
        # Format from actual CSV: 2025-12-04T08:19:41Z
        result = parse_iso_datetime("2025-12-04T08:19:41Z")
        assert result.year == 2025
        assert result.month == 12
        assert result.day == 4
        assert result.hour == 8
        assert result.minute == 19
        assert result.second == 41


class TestGraphLocationParsing:
    """Test location parsing for Graph API exports (City, State, Country)"""

    def test_parse_graph_location_full(self):
        """Parse full location: City, State, Country"""
        city, state, country = parse_graph_location("Melbourne, Victoria, AU")
        assert city == "Melbourne"
        assert state == "Victoria"
        assert country == "AU"

    def test_parse_graph_location_city_country(self):
        """Parse location without state: City, Country"""
        city, state, country = parse_graph_location("Sydney, AU")
        assert city == "Sydney"
        assert state is None
        assert country == "AU"

    def test_parse_graph_location_country_only(self):
        """Parse location with country only"""
        city, state, country = parse_graph_location("AU")
        assert city is None
        assert state is None
        assert country == "AU"

    def test_parse_graph_location_empty(self):
        """Empty location returns None, None, None"""
        city, state, country = parse_graph_location("")
        assert city is None
        assert state is None
        assert country is None

    def test_parse_graph_location_none(self):
        """None location returns None, None, None"""
        city, state, country = parse_graph_location(None)
        assert city is None
        assert state is None
        assert country is None

    def test_parse_graph_location_with_whitespace(self):
        """Parse location with extra whitespace"""
        city, state, country = parse_graph_location("  Melbourne ,  Victoria , AU  ")
        assert city == "Melbourne"
        assert state == "Victoria"
        assert country == "AU"

    def test_parse_graph_location_real_data(self):
        """Real location from PIR-GOOD-SAMARITAN-777777"""
        # Common formats in real data
        city, state, country = parse_graph_location("Melbourne, Victoria, AU")
        assert city == "Melbourne"
        assert state == "Victoria"
        assert country == "AU"

        city, state, country = parse_graph_location("London, , GB")
        assert city == "London"
        assert state == "" or state is None  # Empty state
        assert country == "GB"


class TestGraphStatusParsing:
    """Test status field parsing for Graph API exports"""

    def test_parse_graph_status_success(self):
        """Parse success status"""
        assert parse_graph_status("Success") == "success"

    def test_parse_graph_status_failure(self):
        """Parse failure status"""
        assert parse_graph_status("Failure") == "failure"

    def test_parse_graph_status_interrupted(self):
        """Parse interrupted status"""
        assert parse_graph_status("Interrupted") == "interrupted"

    def test_parse_graph_status_case_insensitive(self):
        """Status parsing is case-insensitive"""
        assert parse_graph_status("SUCCESS") == "success"
        assert parse_graph_status("failure") == "failure"
        assert parse_graph_status("InTeRrUpTeD") == "interrupted"

    def test_parse_graph_status_empty(self):
        """Empty status returns None"""
        assert parse_graph_status("") is None

    def test_parse_graph_status_none(self):
        """None status returns None"""
        assert parse_graph_status(None) is None

    def test_parse_graph_status_unknown(self):
        """Unknown status returns original value (lowercase)"""
        assert parse_graph_status("Unknown Status") == "unknown status"


class TestBooleanFieldParsing:
    """Test boolean field parsing for Graph API exports"""

    def test_parse_boolean_field_true_variants(self):
        """Parse various true representations"""
        assert parse_boolean_field("Yes") is True
        assert parse_boolean_field("YES") is True
        assert parse_boolean_field("yes") is True
        assert parse_boolean_field("True") is True
        assert parse_boolean_field("TRUE") is True
        assert parse_boolean_field("true") is True
        assert parse_boolean_field("1") is True

    def test_parse_boolean_field_false_variants(self):
        """Parse various false representations"""
        assert parse_boolean_field("No") is False
        assert parse_boolean_field("NO") is False
        assert parse_boolean_field("no") is False
        assert parse_boolean_field("False") is False
        assert parse_boolean_field("FALSE") is False
        assert parse_boolean_field("false") is False
        assert parse_boolean_field("0") is False

    def test_parse_boolean_field_empty(self):
        """Empty string returns None"""
        assert parse_boolean_field("") is None

    def test_parse_boolean_field_none(self):
        """None returns None"""
        assert parse_boolean_field(None) is None

    def test_parse_boolean_field_unknown(self):
        """Unknown value returns None"""
        assert parse_boolean_field("maybe") is None

    def test_parse_boolean_field_real_graph_api(self):
        """Real Graph API boolean values"""
        # Compliant field: "Yes" or "No"
        assert parse_boolean_field("Yes") is True
        assert parse_boolean_field("No") is False


class TestIntegerFieldParsing:
    """Test integer field parsing for Graph API exports"""

    def test_parse_integer_field_valid(self):
        """Parse valid integer strings"""
        assert parse_integer_field("42") == 42
        assert parse_integer_field("0") == 0
        assert parse_integer_field("-1") == -1
        assert parse_integer_field("999999") == 999999

    def test_parse_integer_field_empty(self):
        """Empty string returns None"""
        assert parse_integer_field("") is None

    def test_parse_integer_field_none(self):
        """None returns None"""
        assert parse_integer_field(None) is None

    def test_parse_integer_field_whitespace(self):
        """Whitespace-only returns None"""
        assert parse_integer_field("   ") is None

    def test_parse_integer_field_invalid(self):
        """Invalid integer raises ValueError"""
        with pytest.raises(ValueError):
            parse_integer_field("not-a-number")

    def test_parse_integer_field_real_graph_api(self):
        """Real Graph API integer fields"""
        # Sign-in error code: "0" for success, error codes for failures
        assert parse_integer_field("0") == 0
        assert parse_integer_field("50126") == 50126  # Invalid credentials
        assert parse_integer_field("50058") == 50058  # MFA required

        # Latency field: milliseconds
        assert parse_integer_field("245") == 245


class TestConditionalAccessStatusNormalization:
    """Test Conditional Access status normalization"""

    def test_normalize_ca_status_success(self):
        """Normalize success variants"""
        assert normalize_conditional_access_status("success") == "success"
        assert normalize_conditional_access_status("Success") == "success"
        assert normalize_conditional_access_status("SUCCESS") == "success"

    def test_normalize_ca_status_failure(self):
        """Normalize failure variants"""
        assert normalize_conditional_access_status("failure") == "failure"
        assert normalize_conditional_access_status("Failure") == "failure"

    def test_normalize_ca_status_not_applied(self):
        """Normalize not applied variants"""
        # Graph API: "Not Applied"
        # Legacy Portal: "notApplied"
        assert normalize_conditional_access_status("Not Applied") == "notApplied"
        assert normalize_conditional_access_status("not applied") == "notApplied"
        assert normalize_conditional_access_status("notApplied") == "notApplied"
        assert normalize_conditional_access_status("NOTAPPLIED") == "notApplied"

    def test_normalize_ca_status_empty(self):
        """Empty string returns None"""
        assert normalize_conditional_access_status("") is None

    def test_normalize_ca_status_none(self):
        """None returns None"""
        assert normalize_conditional_access_status(None) is None

    def test_normalize_ca_status_unknown(self):
        """Unknown status returns original (lowercase)"""
        assert normalize_conditional_access_status("Unknown") == "unknown"


class TestLocationParsingEdgeCases:
    """Test edge cases in location parsing"""

    def test_location_with_comma_in_city_name(self):
        """Location with comma in city name (rare)"""
        # Most locations won't have this, but handle gracefully
        city, state, country = parse_graph_location("Washington, D.C., US")
        # This will split incorrectly - document expected behavior
        assert country == "US"  # Last segment is always country

    def test_location_with_four_segments(self):
        """Location with more than 3 segments"""
        city, state, country = parse_graph_location("A, B, C, D")
        # Take last 3 segments: city=B, state=C, country=D
        assert city == "B"
        assert state == "C"
        assert country == "D"

    def test_location_single_word(self):
        """Location with single word (country code)"""
        city, state, country = parse_graph_location("US")
        assert city is None
        assert state is None
        assert country == "US"


class TestTransformFunctionIntegration:
    """Integration tests combining multiple transform functions"""

    def test_transform_graph_interactive_row(self):
        """Transform a complete Graph Interactive row"""
        # Simulate real CSV row data
        row_data = {
            "Date (UTC)": "2025-12-04T08:19:41Z",
            "Location": "Melbourne, Victoria, AU",
            "Status": "Success",
            "Sign-in error code": "0",
            "Compliant": "Yes",
            "Managed": "No",
            "Latency": "245",
            "Conditional Access": "Not Applied"
        }

        # Transform using our functions
        timestamp = parse_iso_datetime(row_data["Date (UTC)"])
        city, state, country = parse_graph_location(row_data["Location"])
        status = parse_graph_status(row_data["Status"])
        error_code = parse_integer_field(row_data["Sign-in error code"])
        compliant = parse_boolean_field(row_data["Compliant"])
        managed = parse_boolean_field(row_data["Managed"])
        latency = parse_integer_field(row_data["Latency"])
        ca_status = normalize_conditional_access_status(row_data["Conditional Access"])

        # Verify transformations
        assert timestamp == datetime(2025, 12, 4, 8, 19, 41, tzinfo=timezone.utc)
        assert city == "Melbourne"
        assert state == "Victoria"
        assert country == "AU"
        assert status == "success"
        assert error_code == 0
        assert compliant is True
        assert managed is False
        assert latency == 245
        assert ca_status == "notApplied"
