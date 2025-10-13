#!/usr/bin/env python3
"""
Calendar Availability Checker

Find free time slots for meetings by checking calendar availability.
Works with macOS Calendar synced with Teams/Exchange.

Author: Maia System
Created: 2025-10-13
"""

import subprocess
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class TimeSlot:
    """Represents a time slot"""
    start: datetime
    end: datetime

    def __str__(self):
        return f"{self.start.strftime('%I:%M %p')} - {self.end.strftime('%I:%M %p')}"

    def duration_minutes(self) -> int:
        return int((self.end - self.start).total_seconds() / 60)


@dataclass
class CalendarEvent:
    """Represents a calendar event"""
    summary: str
    start: datetime
    end: datetime
    attendees: List[str]
    status: str = "confirmed"


class CalendarAvailability:
    """Check calendar availability for meeting scheduling"""

    def __init__(self):
        self.business_start = 8  # 8 AM
        self.business_end = 18   # 6 PM

    def _execute_applescript(self, script: str) -> str:
        """Execute AppleScript and return result"""
        try:
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"AppleScript error: {e.stderr}")

    def get_events(self, start_date: datetime, end_date: datetime, attendee_filter: Optional[str] = None) -> List[CalendarEvent]:
        """
        Get calendar events for a date range

        Args:
            start_date: Start of range
            end_date: End of range
            attendee_filter: Optional email to filter events by attendee

        Returns:
            List of CalendarEvent objects
        """
        # Format dates for AppleScript
        start_str = start_date.strftime('%m/%d/%Y %H:%M:%S')
        end_str = end_date.strftime('%m/%d/%Y %H:%M:%S')

        script = f'''
        tell application "Calendar"
            set startDate to date "{start_str}"
            set endDate to date "{end_str}"
            set output to ""

            repeat with cal in calendars
                set calEvents to (every event of cal whose start date ≥ startDate and start date < endDate)
                repeat with evt in calEvents
                    -- Skip all-day events and reminders
                    if allday event of evt is false then
                        set eventInfo to summary of evt & "||"
                        set eventInfo to eventInfo & (start date of evt as string) & "||"
                        set eventInfo to eventInfo & (end date of evt as string) & "||"

                        -- Get attendee emails
                        set attendeeEmails to ""
                        try
                            repeat with att in attendees of evt
                                if attendeeEmails is not "" then
                                    set attendeeEmails to attendeeEmails & ","
                                end if
                                set attendeeEmails to attendeeEmails & email of att
                            end repeat
                        end try

                        set eventInfo to eventInfo & attendeeEmails & "||"
                        set eventInfo to eventInfo & (status of evt as string)

                        set output to output & eventInfo & linefeed
                    end if
                end repeat
            end repeat

            return output
        end tell
        '''

        result = self._execute_applescript(script)

        events = []
        for line in result.split('\n'):
            if not line.strip():
                continue

            parts = line.split('||')
            if len(parts) >= 5:
                summary = parts[0]
                start_str = parts[1]
                end_str = parts[2]
                attendee_str = parts[3]
                status = parts[4]

                # Parse dates
                try:
                    # AppleScript date format: "Tuesday, 14 October 2025 at 1:00:00 pm"
                    start = self._parse_applescript_date(start_str)
                    end = self._parse_applescript_date(end_str)

                    attendees = [a.strip() for a in attendee_str.split(',') if a.strip()]

                    # Filter by attendee if requested
                    if attendee_filter:
                        if not any(attendee_filter.lower() in a.lower() for a in attendees):
                            continue

                    events.append(CalendarEvent(
                        summary=summary,
                        start=start,
                        end=end,
                        attendees=attendees,
                        status=status
                    ))
                except Exception as e:
                    # Skip events we can't parse
                    continue

        return sorted(events, key=lambda e: e.start)

    def _parse_applescript_date(self, date_str: str) -> datetime:
        """Parse AppleScript date format to datetime"""
        # Format: "Tuesday, 14 October 2025 at 1:00:00 pm"
        # Remove day of week
        if ',' in date_str:
            date_str = date_str.split(',', 1)[1].strip()

        # Parse with datetime
        try:
            return datetime.strptime(date_str, '%d %B %Y at %I:%M:%S %p')
        except:
            # Try without seconds
            return datetime.strptime(date_str, '%d %B %Y at %I:%M %p')

    def find_free_slots(
        self,
        date: datetime,
        duration_minutes: int = 30,
        attendee_filter: Optional[str] = None
    ) -> List[TimeSlot]:
        """
        Find free time slots for a given date

        Args:
            date: Date to check
            duration_minutes: Minimum slot duration
            attendee_filter: Optional email to check specific person's availability

        Returns:
            List of available TimeSlot objects
        """
        # Get events for the entire day
        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)

        events = self.get_events(day_start, day_end, attendee_filter)

        # Build list of busy slots during business hours
        business_start_time = day_start.replace(hour=self.business_start, minute=0)
        business_end_time = day_start.replace(hour=self.business_end, minute=0)

        # Filter events to business hours only
        busy_slots = []
        for event in events:
            # Skip if event is outside business hours
            if event.end <= business_start_time or event.start >= business_end_time:
                continue

            # Clip to business hours
            slot_start = max(event.start, business_start_time)
            slot_end = min(event.end, business_end_time)

            busy_slots.append((slot_start, slot_end))

        # Sort and merge overlapping busy slots
        if busy_slots:
            busy_slots.sort()
            merged = [busy_slots[0]]
            for current in busy_slots[1:]:
                last = merged[-1]
                if current[0] <= last[1]:  # Overlapping
                    merged[-1] = (last[0], max(last[1], current[1]))
                else:
                    merged.append(current)
            busy_slots = merged

        # Find free slots between busy periods
        free_slots = []
        current_time = business_start_time

        for busy_start, busy_end in busy_slots:
            if (busy_start - current_time).total_seconds() >= duration_minutes * 60:
                free_slots.append(TimeSlot(current_time, busy_start))
            current_time = busy_end

        # Check if there's free time after last meeting
        if (business_end_time - current_time).total_seconds() >= duration_minutes * 60:
            free_slots.append(TimeSlot(current_time, business_end_time))

        return free_slots

    def check_availability(
        self,
        attendee: str,
        days: int = 5,
        duration_minutes: int = 30
    ) -> Dict[str, List[TimeSlot]]:
        """
        Check availability for an attendee over the next N days

        Args:
            attendee: Email or name to check
            days: Number of days to check
            duration_minutes: Minimum meeting duration

        Returns:
            Dict mapping date strings to available time slots
        """
        results = {}

        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        for i in range(days):
            check_date = today + timedelta(days=i)

            # Skip weekends
            if check_date.weekday() >= 5:
                continue

            free_slots = self.find_free_slots(check_date, duration_minutes, attendee)

            date_str = check_date.strftime('%A, %B %d')
            results[date_str] = free_slots

        return results


def main():
    """CLI interface for calendar availability"""
    import argparse

    parser = argparse.ArgumentParser(description='Check calendar availability')
    parser.add_argument('--attendee', help='Email or name to check availability for')
    parser.add_argument('--days', type=int, default=5, help='Number of days to check (default: 5)')
    parser.add_argument('--duration', type=int, default=30, help='Meeting duration in minutes (default: 30)')
    parser.add_argument('--date', help='Specific date to check (YYYY-MM-DD)')

    args = parser.parse_args()

    checker = CalendarAvailability()

    print("=" * 60)
    print("📅 Calendar Availability Checker")
    print("=" * 60)

    if args.attendee:
        print(f"🔍 Checking availability for: {args.attendee}")
    else:
        print("🔍 Checking your availability")

    print(f"⏱️  Meeting duration: {args.duration} minutes")
    print()

    if args.date:
        # Check specific date
        check_date = datetime.strptime(args.date, '%Y-%m-%d')
        free_slots = checker.find_free_slots(check_date, args.duration, args.attendee)

        date_str = check_date.strftime('%A, %B %d, %Y')
        print(f"📆 {date_str}")

        if free_slots:
            print(f"   ✅ {len(free_slots)} available slots:")
            for slot in free_slots:
                print(f"      • {slot} ({slot.duration_minutes()} min)")
        else:
            print("   ❌ No availability")
    else:
        # Check multiple days
        availability = checker.check_availability(args.attendee, args.days, args.duration)

        for date_str, slots in availability.items():
            print(f"📆 {date_str}")
            if slots:
                print(f"   ✅ {len(slots)} available slots:")
                for slot in slots:
                    print(f"      • {slot} ({slot.duration_minutes()} min)")
            else:
                print("   ❌ No availability")
            print()


if __name__ == "__main__":
    main()
