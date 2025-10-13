#!/usr/bin/env python3
"""
Calendar Availability Checker

Find free time slots for meetings by checking calendar availability.
Works with macOS Calendar synced with Teams/Exchange.

Author: Maia System
Created: 2025-10-13
Updated: 2025-10-13 - Optimized AppleScript performance
"""

import subprocess
import sys
from datetime import datetime, time as dt_time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class TimeSlot:
    """Represents a time slot"""
    start_time: str  # e.g., "9:00 AM"
    end_time: str    # e.g., "10:30 AM"
    duration_minutes: int

    def __str__(self):
        return f"{self.start_time} - {self.end_time} ({self.duration_minutes} min)"


@dataclass
class BusySlot:
    """Represents a busy time slot"""
    start_hour: float  # e.g., 9.5 for 9:30 AM
    end_hour: float    # e.g., 10.75 for 10:45 AM
    summary: str


class CalendarAvailability:
    """Check calendar availability for meeting scheduling"""

    def __init__(self):
        self.business_start_hour = 8.0   # 8 AM
        self.business_end_hour = 18.0    # 6 PM

    def _execute_applescript(self, script: str) -> str:
        """Execute AppleScript and return result"""
        try:
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                check=True,
                timeout=30
            )
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            raise RuntimeError("AppleScript timeout - calendar may have too many events")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"AppleScript error: {e.stderr}")

    def get_busy_slots(self, days_ahead: int = 0, attendee_filter: Optional[str] = None) -> List[BusySlot]:
        """
        Get busy time slots for a specific day

        Args:
            days_ahead: Number of days from today (0 = today, 1 = tomorrow)
            attendee_filter: Optional email to filter by specific attendee

        Returns:
            List of BusySlot objects with hour-based times
        """
        filter_clause = f'set targetEmail to "{attendee_filter}"' if attendee_filter else 'set targetEmail to ""'

        script = f'''
        tell application "Calendar"
            set checkDate to (current date) + ({days_ahead} * days)
            set time of checkDate to 0
            set nextDay to checkDate + (1 * days)

            {filter_clause}
            set output to ""

            repeat with cal in calendars
                (* Only check main work calendars, skip holidays/birthdays/suggestions for speed *)
                set calName to name of cal
                if calName is "Calendar" or calName contains "Work" or calName contains "Exchange" then
                    set calEvents to (every event of cal whose start date ≥ checkDate and start date < nextDay)
                else
                    set calEvents to {{}}
                end if

                repeat with evt in calEvents
                    if allday event of evt is false then
                        set includeEvent to false

                        if targetEmail is "" then
                            set includeEvent to true
                        else
                            try
                                repeat with att in attendees of evt
                                    if email of att contains targetEmail then
                                        set includeEvent to true
                                        exit repeat
                                    end if
                                end repeat
                            end try
                        end if

                        if includeEvent then
                            try
                                -- Get time in seconds since midnight, convert to decimal hours
                                set startSecs to (time of (start date of evt))
                                set endSecs to (time of (end date of evt))
                                set startDecimal to startSecs / 3600
                                set endDecimal to endSecs / 3600

                                set output to output & startDecimal & "|" & endDecimal & "|" & (summary of evt) & linefeed
                            end try
                        end if
                    end if
                end repeat
            end repeat

            return output
        end tell
        '''

        result = self._execute_applescript(script)

        busy_slots = []
        for line in result.split('\n'):
            if not line.strip():
                continue

            parts = line.split('|')
            if len(parts) >= 3:
                try:
                    start_hour = float(parts[0])
                    end_hour = float(parts[1])
                    summary = parts[2]

                    busy_slots.append(BusySlot(
                        start_hour=start_hour,
                        end_hour=end_hour,
                        summary=summary
                    ))
                except ValueError:
                    continue

        return sorted(busy_slots, key=lambda s: s.start_hour)

    def find_free_slots(
        self,
        days_ahead: int = 0,
        duration_minutes: int = 30,
        attendee_filter: Optional[str] = None
    ) -> List[TimeSlot]:
        """
        Find free time slots for a given day

        Args:
            days_ahead: Days from today (0 = today, 1 = tomorrow)
            duration_minutes: Minimum slot duration
            attendee_filter: Optional email to check specific person

        Returns:
            List of available TimeSlot objects
        """
        busy_slots = self.get_busy_slots(days_ahead, attendee_filter)

        # Merge overlapping slots
        if busy_slots:
            merged = [busy_slots[0]]
            for current in busy_slots[1:]:
                last = merged[-1]
                if current.start_hour <= last.end_hour:  # Overlapping
                    merged[-1] = BusySlot(
                        start_hour=last.start_hour,
                        end_hour=max(last.end_hour, current.end_hour),
                        summary=f"{last.summary} + {current.summary}"
                    )
                else:
                    merged.append(current)
            busy_slots = merged

        # Find free slots
        free_slots = []
        current_hour = self.business_start_hour
        duration_hours = duration_minutes / 60.0

        for busy in busy_slots:
            # Skip if busy time is outside business hours
            if busy.end_hour <= self.business_start_hour:
                continue
            if busy.start_hour >= self.business_end_hour:
                continue

            # Clip busy time to business hours
            busy_start = max(busy.start_hour, self.business_start_hour)
            busy_end = min(busy.end_hour, self.business_end_hour)

            # Check if there's a gap before this busy slot
            if busy_start - current_hour >= duration_hours:
                free_slots.append(TimeSlot(
                    start_time=self._format_time(current_hour),
                    end_time=self._format_time(busy_start),
                    duration_minutes=int((busy_start - current_hour) * 60)
                ))

            current_hour = busy_end

        # Check for free time after last meeting
        if self.business_end_hour - current_hour >= duration_hours:
            free_slots.append(TimeSlot(
                start_time=self._format_time(current_hour),
                end_time=self._format_time(self.business_end_hour),
                duration_minutes=int((self.business_end_hour - current_hour) * 60)
            ))

        return free_slots

    def _format_time(self, hour: float) -> str:
        """Convert decimal hour to formatted time string"""
        h = int(hour)
        m = int((hour - h) * 60)

        period = "AM" if h < 12 else "PM"
        display_hour = h if h <= 12 else h - 12
        if display_hour == 0:
            display_hour = 12

        return f"{display_hour}:{m:02d} {period}"

    def check_availability(
        self,
        attendee: Optional[str] = None,
        days: int = 5,
        duration_minutes: int = 30
    ) -> Dict[str, Dict[str, any]]:
        """
        Check availability for the next N days

        Args:
            attendee: Optional email to check specific person
            days: Number of days to check
            duration_minutes: Minimum meeting duration

        Returns:
            Dict with date strings as keys and availability data
        """
        results = {}

        for day_offset in range(days):
            # Get date string
            date_obj = datetime.now()
            for _ in range(day_offset):
                date_obj = date_obj.replace(hour=0, minute=0, second=0, microsecond=0)
                date_obj = date_obj.replace(day=date_obj.day + 1)

            # Skip weekends
            if date_obj.weekday() >= 5:
                continue

            date_str = date_obj.strftime('%A, %B %d')

            busy_slots = self.get_busy_slots(day_offset, attendee)
            free_slots = self.find_free_slots(day_offset, duration_minutes, attendee)

            results[date_str] = {
                'busy': busy_slots,
                'free': free_slots
            }

        return results


def main():
    """CLI interface for calendar availability"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Check calendar availability',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Check your availability for next 3 days
  %(prog)s --days 3

  # Check specific person's availability
  %(prog)s --attendee jono.pryor@orro.group --days 3

  # Find 60-minute slots tomorrow
  %(prog)s --days 1 --duration 60

  # Check if someone is free tomorrow
  %(prog)s --attendee hamish.ridland@orro.group --days 1
        '''
    )
    parser.add_argument('--attendee', help='Email or name to check (default: your calendar)')
    parser.add_argument('--days', type=int, default=3, help='Number of days to check (default: 3)')
    parser.add_argument('--duration', type=int, default=30, help='Meeting duration in minutes (default: 30)')

    args = parser.parse_args()

    try:
        checker = CalendarAvailability()

        print("=" * 60)
        print("📅 Calendar Availability Checker")
        print("=" * 60)

        if args.attendee:
            print(f"🔍 Checking: {args.attendee}")
        else:
            print("🔍 Checking: Your calendar")

        print(f"⏱️  Looking for: {args.duration} minute slots")
        print(f"📆 Days ahead: {args.days}")
        print()

        results = checker.check_availability(args.attendee, args.days, args.duration)

        for date_str, data in results.items():
            print(f"📆 {date_str}")

            if data['busy']:
                print("   Busy:")
                for slot in data['busy']:
                    start_time = checker._format_time(slot.start_hour)
                    end_time = checker._format_time(slot.end_hour)
                    print(f"      • {start_time} - {end_time}: {slot.summary}")

            if data['free']:
                print(f"   ✅ Available ({len(data['free'])} slots):")
                for slot in data['free']:
                    print(f"      • {slot}")
            else:
                print("   ❌ No availability")

            print()

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
