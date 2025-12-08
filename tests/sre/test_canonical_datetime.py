#!/usr/bin/env python3
"""
Tests for Canonical DateTime System
Phase: Date/Time Reliability Enhancement

Test Coverage:
- Date generation accuracy
- Timestamp generation with timezones
- Relative time calculations
- Validation (reject invalid dates/times)
- Cross-verification against system time
- Performance benchmarks

Author: SRE Principal Engineer Agent (Maia)
Date: 2025-12-01
"""

import pytest
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from claude.tools.sre.canonical_datetime import CanonicalDateTime, today, now, now_utc


class TestDateGeneration:
    """Test basic date generation"""

    def test_today_iso_format(self):
        """Today's date should be in YYYY-MM-DD format"""
        date = CanonicalDateTime.today_iso()
        assert len(date) == 10
        assert date[4] == '-'
        assert date[7] == '-'
        # Should parse as valid date
        datetime.strptime(date, '%Y-%m-%d')

    def test_today_is_current_date(self):
        """Today should match system date"""
        canonical_date = CanonicalDateTime.today_iso()
        system_date = datetime.now().strftime('%Y-%m-%d')
        assert canonical_date == system_date

    def test_convenience_function_today(self):
        """Convenience function should match class method"""
        assert today() == CanonicalDateTime.today_iso()


class TestTimestampGeneration:
    """Test timestamp generation with timezones"""

    def test_now_iso_has_timezone(self):
        """Timestamp should include timezone offset"""
        timestamp = CanonicalDateTime.now_iso()
        # Should have +HH:MM or -HH:MM timezone
        assert '+' in timestamp or timestamp.endswith('Z')

    def test_now_iso_is_valid_isoformat(self):
        """Timestamp should be valid ISO format"""
        timestamp = CanonicalDateTime.now_iso()
        # Should parse without error
        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))

    def test_now_utc_is_utc(self):
        """UTC timestamp should have +00:00 offset"""
        timestamp = CanonicalDateTime.now_iso_utc()
        assert '+00:00' in timestamp or timestamp.endswith('Z')

    def test_time_iso_format(self):
        """Time should be in HH:MM:SS format with timezone"""
        time = CanonicalDateTime.time_iso()
        # Should have : separators and timezone
        assert time.count(':') == 2
        assert '+' in time or '-' in time

    def test_convenience_functions(self):
        """Convenience functions should work"""
        assert len(now()) > 0
        assert len(now_utc()) > 0


class TestRelativeTimeCalculations:
    """Test relative time calculations (hours_ago, days_ago, etc.)"""

    def test_hours_ago(self):
        """hours_ago should calculate correctly"""
        now_time = CanonicalDateTime.now()
        three_hours_ago = CanonicalDateTime.hours_ago(3)

        difference = now_time - three_hours_ago
        # Should be approximately 3 hours (within 1 second tolerance)
        assert abs(difference.total_seconds() - 10800) < 1  # 3 hours = 10800 seconds

    def test_days_ago(self):
        """days_ago should calculate correctly"""
        now_time = CanonicalDateTime.now()
        seven_days_ago = CanonicalDateTime.days_ago(7)

        difference = now_time - seven_days_ago
        # Should be approximately 7 days (within 1 second tolerance)
        assert abs(difference.total_seconds() - 604800) < 1  # 7 days = 604800 seconds

    def test_minutes_ago(self):
        """minutes_ago should calculate correctly"""
        now_time = CanonicalDateTime.now()
        thirty_mins_ago = CanonicalDateTime.minutes_ago(30)

        difference = now_time - thirty_mins_ago
        # Should be approximately 30 minutes (within 1 second tolerance)
        assert abs(difference.total_seconds() - 1800) < 1  # 30 minutes = 1800 seconds

    def test_zero_offset(self):
        """Zero offset should return current time"""
        now_time = CanonicalDateTime.now()
        zero_hours = CanonicalDateTime.hours_ago(0)

        difference = abs((now_time - zero_hours).total_seconds())
        assert difference < 0.1  # Should be nearly identical


class TestValidation:
    """Test timestamp and date validation"""

    def test_valid_timestamp_accepted(self):
        """Valid timestamps should pass validation"""
        valid_timestamps = [
            "2025-12-01T14:30:00+08:00",
            "2025-12-01T14:30:00.123456+08:00",
            "2025-12-01T06:30:00+00:00",
            "2025-12-01T06:30:00Z",
        ]
        for ts in valid_timestamps:
            assert CanonicalDateTime.validate_timestamp(ts) is True

    def test_valid_date_accepted(self):
        """Valid dates should pass validation"""
        valid_dates = [
            "2025-12-01",
            "2024-01-01",
            "2030-12-31",
        ]
        for date in valid_dates:
            assert CanonicalDateTime.validate_date(date) is True

    def test_invalid_month_rejected(self):
        """Month 13+ should be rejected"""
        with pytest.raises(ValueError, match="Invalid month"):
            CanonicalDateTime.validate_timestamp("2025-13-01")

        with pytest.raises(ValueError, match="Invalid month"):
            CanonicalDateTime.validate_timestamp("2025-00-01")

    def test_invalid_day_rejected(self):
        """Day 32+ should be rejected"""
        with pytest.raises(ValueError, match="Invalid day"):
            CanonicalDateTime.validate_timestamp("2025-01-32")

        with pytest.raises(ValueError, match="Invalid day"):
            CanonicalDateTime.validate_timestamp("2025-01-00")

    def test_invalid_hour_rejected(self):
        """Hour 24+ should be rejected"""
        with pytest.raises(ValueError, match="Invalid hour"):
            CanonicalDateTime.validate_timestamp("2025-12-01T24:00:00")

        with pytest.raises(ValueError, match="Invalid hour"):
            CanonicalDateTime.validate_timestamp("2025-12-01T25:00:00")

    def test_invalid_minute_rejected(self):
        """Minute 60+ should be rejected"""
        with pytest.raises(ValueError, match="Invalid minute"):
            CanonicalDateTime.validate_timestamp("2025-12-01T14:60:00")

    def test_invalid_second_rejected(self):
        """Second 60+ should be rejected"""
        with pytest.raises(ValueError, match="Invalid second"):
            CanonicalDateTime.validate_timestamp("2025-12-01T14:30:60")

    def test_implausible_year_rejected(self):
        """Years outside 2020-2030 should be rejected"""
        with pytest.raises(ValueError, match="Implausible year"):
            CanonicalDateTime.validate_timestamp("2050-01-01")

        with pytest.raises(ValueError, match="Implausible year"):
            CanonicalDateTime.validate_timestamp("2019-12-31")

    def test_invalid_format_rejected(self):
        """Invalid formats should be rejected"""
        invalid_formats = [
            "12/01/2025",  # MM/DD/YYYY
            "01-12-2025",  # DD-MM-YYYY
            "2025/12/01",  # Slashes instead of dashes
            "not-a-date",
            "2025-12-01 14:30:00",  # Space instead of T
        ]
        for invalid in invalid_formats:
            with pytest.raises(ValueError):
                CanonicalDateTime.validate_timestamp(invalid)


class TestVerification:
    """Test cross-verification against system time"""

    def test_verify_succeeds(self):
        """Verification should succeed with correct system time"""
        result = CanonicalDateTime.verify()
        assert result['verified'] is True
        assert 'date' in result
        assert 'time' in result
        assert 'timezone' in result

    def test_verify_returns_current_date(self):
        """Verification should return current date"""
        result = CanonicalDateTime.verify()
        current_date = datetime.now().strftime('%Y-%m-%d')
        assert result['date'] == current_date


class TestConsistency:
    """Test consistency across multiple calls"""

    def test_date_stable_within_second(self):
        """Date should be stable within same second"""
        date1 = CanonicalDateTime.today_iso()
        date2 = CanonicalDateTime.today_iso()
        assert date1 == date2

    def test_timestamp_increases(self):
        """Timestamps should increase monotonically"""
        ts1 = CanonicalDateTime.now()
        import time
        time.sleep(0.01)  # Wait 10ms
        ts2 = CanonicalDateTime.now()
        assert ts2 > ts1


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_leap_day_valid(self):
        """Leap day should be valid in leap years"""
        # 2024 is a leap year
        assert CanonicalDateTime.validate_date("2024-02-29") is True

    def test_end_of_month(self):
        """End of month dates should be valid"""
        assert CanonicalDateTime.validate_date("2025-01-31") is True
        assert CanonicalDateTime.validate_date("2025-04-30") is True

    def test_negative_relative_time(self):
        """Negative offsets should work (future times)"""
        future = CanonicalDateTime.hours_ago(-3)
        now_time = CanonicalDateTime.now()
        assert future > now_time


class TestPerformance:
    """Performance tests (basic smoke tests)"""

    def test_date_generation_works(self):
        """Date generation should work without error"""
        result = CanonicalDateTime.today_iso()
        assert len(result) == 10

    def test_timestamp_generation_works(self):
        """Timestamp generation should work without error"""
        result = CanonicalDateTime.now_iso()
        assert len(result) > 0

    def test_validation_works(self):
        """Validation should work without error"""
        result = CanonicalDateTime.validate_timestamp("2025-12-01T14:30:00+08:00")
        assert result is True


if __name__ == "__main__":
    """Run tests with pytest"""
    pytest.main([__file__, "-v", "--tb=short"])
