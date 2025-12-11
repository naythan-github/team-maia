#!/usr/bin/env python3
"""
macOS Calendar Bridge - AppleScript Integration
Provides read-only access to macOS Calendar.app events via AppleScript automation.

Similar architecture to macos_mail_bridge.py - leverages existing Calendar.app
authentication without requiring new credentials or API access.

Author: Maia Personal Assistant Agent
Phase: 84 - Calendar Intelligence Integration
Date: 2025-10-03
"""

import subprocess
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import logging
from pathlib import Path

from claude.tools.core.paths import MAIA_ROOT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MacOSCalendarBridge:
    """Bridge to macOS Calendar.app using AppleScript automation."""

    def __init__(self, timeout: int = 30):
        """
        Initialize Calendar bridge.

        Args:
            timeout: Timeout for AppleScript commands (seconds)
        """
        self.timeout = timeout

    def _run_applescript(self, script: str) -> Tuple[bool, str]:
        """
        Execute AppleScript and return results.

        Args:
            script: AppleScript code to execute

        Returns:
            Tuple of (success, output/error)
        """
        try:
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            if result.returncode == 0:
                return True, result.stdout.strip()
            else:
                logger.error(f"AppleScript error: {result.stderr}")
                return False, result.stderr.strip()

        except subprocess.TimeoutExpired:
            logger.error(f"AppleScript timeout after {self.timeout}s")
            return False, f"Command timeout after {self.timeout}s"
        except Exception as e:
            logger.error(f"AppleScript execution error: {e}")
            return False, str(e)

    def list_calendars(self) -> List[Dict[str, str]]:
        """
        List all available calendars.

        Returns:
            List of calendar dictionaries with name and description
        """
        script = '''
        tell application "Calendar"
            set calList to {}
            repeat with cal in calendars
                set end of calList to (name of cal & "|" & description of cal)
            end repeat
            return calList
        end tell
        '''

        success, output = self._run_applescript(script)
        if not success:
            logger.error(f"Failed to list calendars: {output}")
            return []

        calendars = []
        if output:
            for line in output.split(', '):
                parts = line.split('|')
                if len(parts) >= 2:
                    calendars.append({
                        'name': parts[0],
                        'description': parts[1] if parts[1] else parts[0]
                    })
                elif len(parts) == 1:
                    calendars.append({
                        'name': parts[0],
                        'description': parts[0]
                    })

        logger.info(f"Found {len(calendars)} calendars")
        return calendars

    def get_events(
        self,
        days_ahead: int = 7,
        calendar_name: Optional[str] = None,
        include_all_day: bool = True
    ) -> List[Dict]:
        """
        Get calendar events for specified date range.

        Args:
            days_ahead: Number of days to look ahead (default 7)
            calendar_name: Optional calendar name filter
            include_all_day: Include all-day events (default True)

        Returns:
            List of event dictionaries
        """
        # Build calendar filter
        calendar_filter = ''
        if calendar_name:
            calendar_filter = f'whose name is "{calendar_name}"'

        script = f'''
        tell application "Calendar"
            set today to current date
            set startOfToday to today
            set time of startOfToday to 0
            set endDate to startOfToday + ({days_ahead} * days)

            set eventList to {{}}
            repeat with cal in (calendars {calendar_filter})
                set calEvents to (every event of cal whose start date ≥ startOfToday and start date ≤ endDate)
                repeat with evt in calEvents
                    set theLocation to ""
                    try
                        set theLocation to location of evt
                    end try
                    set theDescription to ""
                    try
                        set theDescription to description of evt
                    end try

                    set eventInfo to (summary of evt) & "|||" & ¬
                                   (start date of evt as string) & "|||" & ¬
                                   (end date of evt as string) & "|||" & ¬
                                   (name of cal) & "|||" & ¬
                                   theLocation & "|||" & ¬
                                   theDescription & "|||" & ¬
                                   (allday event of evt as string)
                    set end of eventList to eventInfo & "###EVENTSEP###"
                end repeat
            end repeat
            return eventList
        end tell
        '''

        success, output = self._run_applescript(script)
        if not success:
            logger.error(f"Failed to get events: {output}")
            return []

        events = []
        if output:
            # Split by unique event separator instead of comma
            event_strings = output.split('###EVENTSEP###, ')
            for line in event_strings:
                line = line.replace('###EVENTSEP###', '').strip()
                if not line:
                    continue
                try:
                    parts = line.split('|||')
                    if len(parts) >= 7:
                        is_all_day = parts[6].lower() == 'true'

                        # Skip all-day events if requested
                        if not include_all_day and is_all_day:
                            continue

                        events.append({
                            'summary': parts[0],
                            'start_date': parts[1],
                            'end_date': parts[2],
                            'calendar': parts[3],
                            'location': parts[4] if parts[4] != 'missing value' else '',
                            'description': parts[5] if parts[5] != 'missing value' else '',
                            'all_day': is_all_day
                        })
                except Exception as e:
                    logger.warning(f"Failed to parse event: {e}")
                    continue

        logger.info(f"Retrieved {len(events)} events")
        return events

    def get_today_events(self, calendar_name: Optional[str] = None) -> List[Dict]:
        """
        Get today's events.

        Args:
            calendar_name: Optional calendar name filter

        Returns:
            List of today's event dictionaries
        """
        script_filter = ''
        if calendar_name:
            script_filter = f'whose name is "{calendar_name}"'

        script = f'''
        tell application "Calendar"
            set today to current date
            set startOfToday to today
            set time of startOfToday to 0
            set endOfToday to startOfToday + (1 * days) - 1

            set eventList to {{}}
            repeat with cal in (calendars {script_filter})
                set calEvents to (every event of cal whose start date ≥ startOfToday and start date ≤ endOfToday)
                repeat with evt in calEvents
                    set theLocation to ""
                    try
                        set theLocation to location of evt
                    end try

                    set eventInfo to (summary of evt) & "|||" & ¬
                                   (start date of evt as string) & "|||" & ¬
                                   (end date of evt as string) & "|||" & ¬
                                   (name of cal) & "|||" & ¬
                                   theLocation & "|||" & ¬
                                   (allday event of evt as string)
                    set end of eventList to eventInfo & "###EVENTSEP###"
                end repeat
            end repeat
            return eventList
        end tell
        '''

        success, output = self._run_applescript(script)
        if not success:
            logger.error(f"Failed to get today's events: {output}")
            return []

        events = []
        if output:
            # Split by unique event separator
            event_strings = output.split('###EVENTSEP###, ')
            for line in event_strings:
                line = line.replace('###EVENTSEP###', '').strip()
                if not line:
                    continue
                try:
                    parts = line.split('|||')
                    if len(parts) >= 6:
                        events.append({
                            'summary': parts[0],
                            'start_date': parts[1],
                            'end_date': parts[2],
                            'calendar': parts[3],
                            'location': parts[4] if parts[4] != 'missing value' else '',
                            'all_day': parts[5].lower() == 'true'
                        })
                except Exception as e:
                    logger.warning(f"Failed to parse event: {e}")
                    continue

        logger.info(f"Retrieved {len(events)} events for today")
        return events

    def search_events(
        self,
        query: str,
        days_ahead: int = 30,
        calendar_name: Optional[str] = None
    ) -> List[Dict]:
        """
        Search events by summary/description.

        Args:
            query: Search term
            days_ahead: Days to search ahead
            calendar_name: Optional calendar filter

        Returns:
            List of matching event dictionaries
        """
        all_events = self.get_events(days_ahead=days_ahead, calendar_name=calendar_name)

        query_lower = query.lower()
        matching_events = [
            event for event in all_events
            if query_lower in event['summary'].lower() or
               query_lower in event.get('description', '').lower() or
               query_lower in event.get('location', '').lower()
        ]

        logger.info(f"Found {len(matching_events)} events matching '{query}'")
        return matching_events

    def get_week_summary(self) -> Dict:
        """
        Get weekly calendar summary.

        Returns:
            Dictionary with week overview statistics
        """
        events = self.get_events(days_ahead=7)

        # Categorize events
        today_events = []
        upcoming_events = []
        all_day_events = []

        today = datetime.now().date()

        for event in events:
            # Parse start date
            try:
                # AppleScript returns format like "Friday, 3 October 2025 at 10:30:00 am"
                if 'at' in event['start_date']:
                    date_str = event['start_date'].split(' at ')[0]
                else:
                    date_str = event['start_date']

                # Simplified date parsing (just check if it's today)
                if 'today' in event['start_date'].lower() or str(today.day) in date_str:
                    if event['all_day']:
                        all_day_events.append(event)
                    else:
                        today_events.append(event)
                else:
                    upcoming_events.append(event)

            except Exception as e:
                logger.warning(f"Date parsing error: {e}")
                upcoming_events.append(event)

        summary = {
            'total_events': len(events),
            'today_events': len(today_events),
            'upcoming_events': len(upcoming_events),
            'all_day_events': len(all_day_events),
            'today_details': today_events[:10],  # Limit to 10
            'upcoming_details': upcoming_events[:10]
        }

        logger.info(f"Week summary: {summary['total_events']} total, {summary['today_events']} today")
        return summary


def main():
    """Test calendar bridge functionality."""
    bridge = MacOSCalendarBridge()

    print("\n=== macOS Calendar Bridge Test ===\n")

    # List calendars
    print("📅 Available Calendars:")
    calendars = bridge.list_calendars()
    for cal in calendars:
        print(f"  - {cal['name']}: {cal['description']}")

    # Get today's events
    print("\n📆 Today's Events:")
    today_events = bridge.get_today_events()
    for event in today_events[:5]:  # Show first 5
        print(f"  • {event['summary']}")
        print(f"    Time: {event['start_date']}")
        if event['location']:
            print(f"    Location: {event['location']}")

    # Get week ahead
    print("\n📊 Next 7 Days:")
    week_summary = bridge.get_week_summary()
    print(f"  Total events: {week_summary['total_events']}")
    print(f"  Today: {week_summary['today_events']}")
    print(f"  Upcoming: {week_summary['upcoming_events']}")

    # Export to JSON
    print("\n💾 Exporting full week to JSON...")
    week_events = bridge.get_events(days_ahead=7)

    output_file = str(MAIA_ROOT / "claude/data/calendar_export.json")
    with open(output_file, 'w') as f:
        json.dump(week_events, f, indent=2, default=str)

    print(f"✅ Exported {len(week_events)} events to {output_file}")


if __name__ == '__main__':
    main()
