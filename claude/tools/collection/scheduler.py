"""Automated daily data refresh scheduler.

This module provides automated scheduling for data collection refreshes
from various sources (PMP, OTC, etc.) at configured times each day.

Usage:
    from claude.tools.collection.scheduler import CollectionScheduler

    scheduler = CollectionScheduler()

    # Get sources due for refresh
    pending = scheduler.get_pending_refreshes()

    # Run all pending refreshes
    results = scheduler.run_all_pending()

    # Get status of all scheduled sources
    status = scheduler.get_schedule_status()
"""

import json
import subprocess
from dataclasses import dataclass, asdict
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import yaml


@dataclass
class ScheduleEntry:
    """Configuration for a scheduled data source refresh."""

    source: str
    refresh_time: time
    enabled: bool
    refresh_command: str
    last_run: Optional[datetime] = None


@dataclass
class ScheduleStatus:
    """Status information for a scheduled source."""

    source: str
    enabled: bool
    last_run: Optional[datetime]
    next_run: datetime
    is_overdue: bool


class CollectionScheduler:
    """Manages automated daily data refresh scheduling.

    Loads schedule configuration from YAML, tracks execution state,
    and provides methods to check for and execute pending refreshes.
    """

    CONFIG_PATH = Path.home() / ".maia" / "config" / "collection_schedule.yaml"
    STATE_PATH = Path.home() / ".maia" / "state" / "scheduler_state.json"

    DEFAULT_SCHEDULE = {
        "pmp": {
            "refresh_time": "06:00",
            "enabled": True,
            "refresh_command": "python3 claude/tools/pmp/pmp_resilient_extractor.py"
        },
        "otc": {
            "refresh_time": "06:30",
            "enabled": True,
            "refresh_command": "python3 -m claude.tools.integrations.otc.load_to_postgres all"
        }
    }

    def __init__(self):
        """Initialize scheduler with configuration and state."""
        self.schedule: Dict[str, ScheduleEntry] = self._load_schedule()
        self._load_state()

    def _load_schedule(self) -> Dict[str, ScheduleEntry]:
        """Load schedule configuration from YAML or use defaults.

        Returns:
            Dictionary mapping source names to ScheduleEntry objects
        """
        if self.CONFIG_PATH.exists():
            try:
                with open(self.CONFIG_PATH, 'r') as f:
                    config = yaml.safe_load(f)

                schedule = {}
                for source_name, source_config in config.get('sources', {}).items():
                    # Parse time string (HH:MM format)
                    time_parts = source_config['refresh_time'].split(':')
                    refresh_time = time(int(time_parts[0]), int(time_parts[1]))

                    schedule[source_name] = ScheduleEntry(
                        source=source_name,
                        refresh_time=refresh_time,
                        enabled=source_config['enabled'],
                        refresh_command=source_config['refresh_command']
                    )

                return schedule
            except Exception:
                # Fall back to defaults on any error
                return self._create_default_schedule()
        else:
            return self._create_default_schedule()

    def _create_default_schedule(self) -> Dict[str, ScheduleEntry]:
        """Create schedule from default configuration.

        Returns:
            Dictionary mapping source names to ScheduleEntry objects
        """
        schedule = {}
        for source_name, source_config in self.DEFAULT_SCHEDULE.items():
            # Parse time string (HH:MM format)
            time_parts = source_config['refresh_time'].split(':')
            refresh_time = time(int(time_parts[0]), int(time_parts[1]))

            schedule[source_name] = ScheduleEntry(
                source=source_name,
                refresh_time=refresh_time,
                enabled=source_config['enabled'],
                refresh_command=source_config['refresh_command']
            )

        return schedule

    def _load_state(self):
        """Load persisted state (last run timestamps) from JSON."""
        if self.STATE_PATH.exists():
            try:
                with open(self.STATE_PATH, 'r') as f:
                    state = json.load(f)

                # Restore last_run timestamps
                for source_name, last_run_str in state.get('last_runs', {}).items():
                    if source_name in self.schedule and last_run_str:
                        self.schedule[source_name].last_run = datetime.fromisoformat(last_run_str)
            except Exception:
                # Ignore errors loading state
                pass

    def _save_state(self):
        """Persist current state (last run timestamps) to JSON."""
        # Ensure directory exists
        self.STATE_PATH.parent.mkdir(parents=True, exist_ok=True)

        state = {
            'last_runs': {
                source_name: entry.last_run.isoformat() if entry.last_run else None
                for source_name, entry in self.schedule.items()
            }
        }

        with open(self.STATE_PATH, 'w') as f:
            json.dump(state, f, indent=2)

    def get_pending_refreshes(self) -> List[str]:
        """Get list of sources that are due for refresh.

        A source is pending if:
        - It is enabled
        - Current time is past its scheduled refresh time
        - It hasn't run today (or never run)

        Returns:
            List of source names that need refresh
        """
        now = datetime.now()
        today = now.date()
        pending = []

        for source_name, entry in self.schedule.items():
            if not entry.enabled:
                continue

            # Calculate scheduled time for today
            scheduled_today = datetime.combine(today, entry.refresh_time)

            # Check if we've passed the scheduled time
            if now < scheduled_today:
                continue

            # Check if already run today
            if entry.last_run and entry.last_run.date() == today:
                continue

            pending.append(source_name)

        return pending

    def run_refresh(self, source: str) -> bool:
        """Execute refresh command for a single source.

        Args:
            source: Name of the source to refresh

        Returns:
            True if refresh succeeded, False otherwise
        """
        if source not in self.schedule:
            return False

        entry = self.schedule[source]

        try:
            # Execute refresh command
            result = subprocess.run(
                entry.refresh_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )

            success = result.returncode == 0

            if success:
                # Update last_run timestamp
                entry.last_run = datetime.now()
                self._save_state()

            return success

        except Exception:
            return False

    def run_all_pending(self) -> Dict[str, bool]:
        """Execute all pending refreshes.

        Returns:
            Dictionary mapping source names to success status
        """
        pending = self.get_pending_refreshes()
        results = {}

        for source in pending:
            results[source] = self.run_refresh(source)

        return results

    def get_schedule_status(self) -> Dict[str, ScheduleStatus]:
        """Get status information for all scheduled sources.

        Returns:
            Dictionary mapping source names to ScheduleStatus objects
        """
        now = datetime.now()
        today = now.date()
        tomorrow = today + timedelta(days=1)

        status = {}

        for source_name, entry in self.schedule.items():
            # Calculate next scheduled run
            scheduled_today = datetime.combine(today, entry.refresh_time)
            scheduled_tomorrow = datetime.combine(tomorrow, entry.refresh_time)

            if now < scheduled_today:
                # Haven't reached today's scheduled time yet
                next_run = scheduled_today
            else:
                # Past today's time, next run is tomorrow
                next_run = scheduled_tomorrow

            # Check if overdue (enabled, past scheduled time, not run today)
            is_overdue = (
                entry.enabled and
                now >= scheduled_today and
                (not entry.last_run or entry.last_run.date() < today)
            )

            status[source_name] = ScheduleStatus(
                source=source_name,
                enabled=entry.enabled,
                last_run=entry.last_run,
                next_run=next_run,
                is_overdue=is_overdue
            )

        return status
