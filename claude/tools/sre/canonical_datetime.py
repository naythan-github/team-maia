#!/usr/bin/env python3
"""
Canonical Date/Time System - Protection Against Wild Variations
Phase: Date/Time Reliability Enhancement

Purpose:
    Single source of truth for all date/time operations in Maia system.
    Prevents common errors:
    - Timezone confusion (AWST vs UTC = 8 hour error)
    - Manual date entry mistakes (wrong month, year, etc.)
    - Relative time calculation errors ("3 days ago")
    - Format ambiguity (MM/DD vs DD/MM)
    - Invalid timestamps (month 13, hour 25)

Performance:
    - Date generation: ~2.8µs (negligible)
    - Full timestamp: ~2.2µs (negligible)
    - Validation: ~0.2µs (negligible)
    - Verification: ~1.81ms (use sparingly - startup only)

Usage:
    from claude.tools.sre.canonical_datetime import CanonicalDateTime

    # Always use these instead of manual date strings
    date = CanonicalDateTime.today_iso()
    timestamp = CanonicalDateTime.now_iso()
    three_hours_ago = CanonicalDateTime.hours_ago(3)

Author: SRE Principal Engineer Agent (Maia)
Date: 2025-12-01
Version: 1.0
Status: Production Ready
"""

from datetime import datetime, timedelta
import subprocess
import sys
from pathlib import Path
from typing import Optional

# Try to import pytz, graceful degradation if not available
try:
    import pytz
    PYTZ_AVAILABLE = True
except ImportError:
    PYTZ_AVAILABLE = False
    print("Warning: pytz not available, timezone support limited", file=sys.stderr)


class CanonicalDateTime:
    """
    Single source of truth for all date/time operations

    Provides timezone-aware datetime operations with validation
    and cross-verification against system time.
    """

    # Default timezone for Maia system (Perth, Australia)
    DEFAULT_TZ_NAME = 'Australia/Perth'  # AWST (UTC+8)

    @classmethod
    def _get_timezone(cls, timezone: str = None):
        """Get timezone object, with fallback if pytz unavailable"""
        if not PYTZ_AVAILABLE:
            return None

        tz_name = timezone or cls.DEFAULT_TZ_NAME
        return pytz.timezone(tz_name)

    @classmethod
    def now(cls, timezone: str = None) -> datetime:
        """
        Get current datetime with explicit timezone

        Args:
            timezone: Timezone name (default: Australia/Perth)

        Returns:
            Timezone-aware datetime object

        Example:
            >>> dt = CanonicalDateTime.now()
            >>> print(dt.isoformat())
            2025-12-01T14:30:00.123456+08:00
        """
        tz = cls._get_timezone(timezone)
        if tz:
            return datetime.now(tz)
        else:
            # Fallback to system local time if pytz unavailable
            return datetime.now()

    @classmethod
    def today_iso(cls) -> str:
        """
        Get today's date in ISO format (YYYY-MM-DD)

        Returns:
            Date string, e.g., "2025-12-01"

        Example:
            >>> date = CanonicalDateTime.today_iso()
            >>> print(date)
            2025-12-01
        """
        return cls.now().strftime('%Y-%m-%d')

    @classmethod
    def now_iso(cls) -> str:
        """
        Get current timestamp in ISO format with timezone

        Returns:
            Full ISO timestamp, e.g., "2025-12-01T14:30:00.123456+08:00"

        Example:
            >>> timestamp = CanonicalDateTime.now_iso()
            >>> print(timestamp)
            2025-12-01T14:30:00.123456+08:00
        """
        return cls.now().isoformat()

    @classmethod
    def now_iso_utc(cls) -> str:
        """
        Get current timestamp in UTC (for database storage)

        Returns:
            UTC timestamp, e.g., "2025-12-01T06:30:00.123456+00:00"

        Example:
            >>> timestamp = CanonicalDateTime.now_iso_utc()
            >>> print(timestamp)
            2025-12-01T06:30:00.123456+00:00
        """
        if PYTZ_AVAILABLE:
            return datetime.now(pytz.UTC).isoformat()
        else:
            return datetime.utcnow().isoformat() + '+00:00'

    @classmethod
    def time_iso(cls) -> str:
        """
        Get current time in 24h format with timezone

        Returns:
            Time string, e.g., "14:30:00+0800"

        Example:
            >>> time = CanonicalDateTime.time_iso()
            >>> print(time)
            14:30:00+0800
        """
        return cls.now().strftime('%H:%M:%S%z')

    @classmethod
    def hours_ago(cls, hours: int) -> datetime:
        """
        Calculate time N hours ago (prevents manual arithmetic errors)

        Args:
            hours: Number of hours to subtract

        Returns:
            Timezone-aware datetime N hours ago

        Example:
            >>> three_hours_ago = CanonicalDateTime.hours_ago(3)
            >>> print(three_hours_ago.isoformat())
            2025-12-01T11:30:00.123456+08:00
        """
        return cls.now() - timedelta(hours=hours)

    @classmethod
    def days_ago(cls, days: int) -> datetime:
        """
        Calculate date N days ago (prevents manual arithmetic errors)

        Args:
            days: Number of days to subtract

        Returns:
            Timezone-aware datetime N days ago

        Example:
            >>> week_ago = CanonicalDateTime.days_ago(7)
            >>> print(week_ago.strftime('%Y-%m-%d'))
            2025-11-24
        """
        return cls.now() - timedelta(days=days)

    @classmethod
    def minutes_ago(cls, minutes: int) -> datetime:
        """
        Calculate time N minutes ago

        Args:
            minutes: Number of minutes to subtract

        Returns:
            Timezone-aware datetime N minutes ago
        """
        return cls.now() - timedelta(minutes=minutes)

    @classmethod
    def verify(cls) -> dict:
        """
        Cross-check multiple sources for consistency

        WARNING: Uses subprocess (1.81ms cost) - use sparingly (startup only)

        Raises:
            ValueError: If sources disagree

        Returns:
            Dict with verification results

        Example:
            >>> result = CanonicalDateTime.verify()
            >>> print(result['verified'])
            True
        """
        python_date = datetime.now().strftime('%Y-%m-%d')
        python_time = datetime.now().strftime('%H:%M')

        try:
            system_date = subprocess.run(
                ['date', '+%Y-%m-%d'],
                capture_output=True,
                text=True,
                timeout=1
            ).stdout.strip()

            system_time = subprocess.run(
                ['date', '+%H:%M'],
                capture_output=True,
                text=True,
                timeout=1
            ).stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # System date command not available or timeout
            return {
                'date': python_date,
                'time': python_time,
                'verified': False,
                'error': 'System date command unavailable',
                'timezone': cls.DEFAULT_TZ_NAME
            }

        # Check date match
        if python_date != system_date:
            raise ValueError(
                f"Date mismatch detected: Python={python_date}, System={system_date}"
            )

        # Check time match (within 1 minute tolerance for clock drift)
        python_mins = int(python_time.split(':')[0]) * 60 + int(python_time.split(':')[1])
        system_mins = int(system_time.split(':')[0]) * 60 + int(system_time.split(':')[1])

        if abs(python_mins - system_mins) > 1:
            raise ValueError(
                f"Time mismatch detected: Python={python_time}, System={system_time} "
                f"(difference: {abs(python_mins - system_mins)} minutes)"
            )

        return {
            'date': python_date,
            'time': python_time,
            'verified': True,
            'timezone': cls.DEFAULT_TZ_NAME + ' (AWST, UTC+8)',
            'system_agrees': True
        }

    @classmethod
    def validate_timestamp(cls, timestamp: str) -> bool:
        """
        Validate timestamp string is reasonable (sanity checks)

        Args:
            timestamp: ISO format timestamp or date string

        Returns:
            True if valid

        Raises:
            ValueError: If timestamp invalid or implausible

        Example:
            >>> CanonicalDateTime.validate_timestamp("2025-12-01T14:30:00+08:00")
            True
            >>> CanonicalDateTime.validate_timestamp("2025-13-01")  # Month 13
            ValueError: Invalid month: 13
        """
        # Pre-validate format before parsing
        # This catches errors before datetime parsing does
        parts = timestamp.replace('T', '-').replace(':', '-').replace('+', '-').replace('Z', '').split('-')

        # Extract components based on format
        if 'T' in timestamp or ':' in timestamp:
            # Full timestamp format
            try:
                year = int(parts[0])
                month = int(parts[1])
                day = int(parts[2])
                if len(parts) >= 5:
                    hour = int(parts[3])
                    minute = int(parts[4])
                else:
                    hour = 0
                    minute = 0
                if len(parts) >= 6:
                    # Remove fractional seconds if present
                    second_part = parts[5].split('.')[0]
                    second = int(second_part) if second_part else 0
                else:
                    second = 0
            except (ValueError, IndexError):
                raise ValueError(
                    f"Invalid timestamp format '{timestamp}'. "
                    f"Expected ISO format (YYYY-MM-DDTHH:MM:SS+TZ) or date (YYYY-MM-DD)"
                )
        else:
            # Date-only format
            try:
                year = int(parts[0])
                month = int(parts[1])
                day = int(parts[2])
                hour = 0
                minute = 0
                second = 0
            except (ValueError, IndexError):
                raise ValueError(
                    f"Invalid date format '{timestamp}'. Expected YYYY-MM-DD"
                )

        # Sanity checks BEFORE datetime parsing
        if year < 2020 or year > 2030:
            raise ValueError(
                f"Implausible year: {year} (expected 2020-2030). "
                f"Check if system clock is correct."
            )

        if month < 1 or month > 12:
            raise ValueError(f"Invalid month: {month} (must be 1-12)")

        if day < 1 or day > 31:
            raise ValueError(f"Invalid day: {day} (must be 1-31)")

        if hour < 0 or hour > 23:
            raise ValueError(f"Invalid hour: {hour} (must be 0-23)")

        if minute < 0 or minute > 59:
            raise ValueError(f"Invalid minute: {minute} (must be 0-59)")

        if second < 0 or second > 59:
            raise ValueError(f"Invalid second: {second} (must be 0-59)")

        # Now try to parse it (should succeed if we got here)
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            # Try parsing as date only
            try:
                dt = datetime.strptime(timestamp, '%Y-%m-%d')
            except ValueError:
                raise ValueError(
                    f"Invalid timestamp format '{timestamp}'. "
                    f"Expected ISO format (YYYY-MM-DDTHH:MM:SS+TZ) or date (YYYY-MM-DD)"
                )

        return True

    @classmethod
    def validate_date(cls, date_str: str) -> bool:
        """
        Validate date string is reasonable (YYYY-MM-DD format)

        Args:
            date_str: Date string in YYYY-MM-DD format

        Returns:
            True if valid

        Raises:
            ValueError: If date invalid or implausible
        """
        return cls.validate_timestamp(date_str)


# Convenience functions for common operations
def today() -> str:
    """Get today's date (YYYY-MM-DD)"""
    return CanonicalDateTime.today_iso()

def now() -> str:
    """Get current timestamp with timezone"""
    return CanonicalDateTime.now_iso()

def now_utc() -> str:
    """Get current timestamp in UTC"""
    return CanonicalDateTime.now_iso_utc()


if __name__ == "__main__":
    """Demo and self-test"""
    print("=== Canonical DateTime System ===\n")

    # Basic operations
    print(f"Date (ISO):           {CanonicalDateTime.today_iso()}")
    print(f"Timestamp (local):    {CanonicalDateTime.now_iso()}")
    print(f"Timestamp (UTC):      {CanonicalDateTime.now_iso_utc()}")
    print(f"Time (24h):           {CanonicalDateTime.time_iso()}")

    # Relative time
    print(f"\n3 hours ago:          {CanonicalDateTime.hours_ago(3).isoformat()}")
    print(f"7 days ago:           {CanonicalDateTime.days_ago(7).strftime('%Y-%m-%d')}")
    print(f"30 minutes ago:       {CanonicalDateTime.minutes_ago(30).strftime('%H:%M')}")

    # Verification
    print(f"\nVerification:         {CanonicalDateTime.verify()}")

    # Validation tests
    print("\nValidation tests:")
    test_cases = [
        ("2025-12-01T14:30:00+08:00", True, "Valid timestamp"),
        ("2025-12-01", True, "Valid date"),
        ("2025-13-01", False, "Invalid month 13"),
        ("2025-01-32", False, "Invalid day 32"),
        ("2025-12-01T25:00:00", False, "Invalid hour 25"),
        ("2050-01-01", False, "Implausible year 2050"),
    ]

    for timestamp, should_pass, description in test_cases:
        try:
            CanonicalDateTime.validate_timestamp(timestamp)
            if should_pass:
                print(f"  ✅ {description}: '{timestamp}' accepted")
            else:
                print(f"  ❌ {description}: '{timestamp}' should have been rejected!")
        except ValueError as e:
            if not should_pass:
                print(f"  ✅ {description}: '{timestamp}' rejected correctly")
            else:
                print(f"  ❌ {description}: '{timestamp}' should have been accepted! Error: {e}")

    print("\n✅ Canonical DateTime System Ready")
