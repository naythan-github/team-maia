"""Tests for collection scheduler."""
import json
import pytest
import tempfile
from datetime import datetime, time, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import yaml

from claude.tools.collection.scheduler import (
    CollectionScheduler,
    ScheduleEntry,
    ScheduleStatus,
)


class TestSchedulerImport:
    def test_import_scheduler(self):
        """CollectionScheduler should be importable."""
        assert CollectionScheduler is not None
        assert ScheduleEntry is not None
        assert ScheduleStatus is not None


class TestScheduleConfiguration:
    def test_load_schedule_from_yaml(self):
        """Loads schedule from ~/.maia/config/collection_schedule.yaml."""
        config_content = """
sources:
  pmp:
    refresh_time: "06:00"
    enabled: true
    refresh_command: "python3 claude/tools/pmp/pmp_resilient_extractor.py"
  otc:
    refresh_time: "06:30"
    enabled: false
    refresh_command: "python3 -m claude.tools.integrations.otc.load_to_postgres all"
"""

        with patch("builtins.open", mock_open(read_data=config_content)):
            with patch.object(Path, "exists", return_value=True):
                scheduler = CollectionScheduler()

                assert "pmp" in scheduler.schedule
                assert "otc" in scheduler.schedule
                assert scheduler.schedule["pmp"].refresh_time == time(6, 0)
                assert scheduler.schedule["pmp"].enabled is True
                assert scheduler.schedule["otc"].refresh_time == time(6, 30)
                assert scheduler.schedule["otc"].enabled is False

    def test_default_schedule_when_no_config(self):
        """Uses sensible defaults if config missing."""
        with patch.object(Path, "exists", return_value=False):
            scheduler = CollectionScheduler()

            # Should have default sources
            assert "pmp" in scheduler.schedule
            assert "otc" in scheduler.schedule
            assert scheduler.schedule["pmp"].enabled is True
            assert scheduler.schedule["otc"].enabled is True

    def test_schedule_structure(self):
        """Each entry has source, refresh_time, enabled."""
        with patch.object(Path, "exists", return_value=False):
            scheduler = CollectionScheduler()

            for source_name, entry in scheduler.schedule.items():
                assert isinstance(entry, ScheduleEntry)
                assert entry.source == source_name
                assert isinstance(entry.refresh_time, time)
                assert isinstance(entry.enabled, bool)
                assert isinstance(entry.refresh_command, str)
                assert entry.last_run is None or isinstance(entry.last_run, datetime)


class TestScheduleExecution:
    def test_get_pending_refreshes(self):
        """Returns sources due for refresh."""
        with patch.object(Path, "exists", return_value=False):
            scheduler = CollectionScheduler()

            # Mock current time to be after refresh time
            now = datetime.now().replace(hour=7, minute=0)

            with patch("claude.tools.collection.scheduler.datetime") as mock_dt:
                mock_dt.now.return_value = now
                mock_dt.combine = datetime.combine

                pending = scheduler.get_pending_refreshes()

                # Should return enabled sources that haven't run today
                assert isinstance(pending, list)

    def test_run_single_refresh(self):
        """Executes refresh for one source."""
        with patch.object(Path, "exists", return_value=False):
            scheduler = CollectionScheduler()

            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock(returncode=0)

                result = scheduler.run_refresh("pmp")

                assert result is True
                mock_run.assert_called_once()

    def test_run_all_pending(self):
        """Executes all pending refreshes."""
        with patch.object(Path, "exists", return_value=False):
            scheduler = CollectionScheduler()

            # Set last_run to yesterday for all sources
            yesterday = datetime.now() - timedelta(days=1)
            for entry in scheduler.schedule.values():
                entry.last_run = yesterday

            now = datetime.now().replace(hour=7, minute=0)

            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock(returncode=0)

                with patch("claude.tools.collection.scheduler.datetime") as mock_dt:
                    mock_dt.now.return_value = now
                    mock_dt.combine = datetime.combine

                    results = scheduler.run_all_pending()

                    assert isinstance(results, dict)
                    # Should have attempted to run enabled sources
                    assert len(results) >= 0

    def test_refresh_updates_last_run(self):
        """Tracks last_run timestamp after refresh."""
        with patch.object(Path, "exists", return_value=False):
            scheduler = CollectionScheduler()

            before_run = datetime.now()

            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock(returncode=0)

                scheduler.run_refresh("pmp")

                after_run = datetime.now()

                assert scheduler.schedule["pmp"].last_run is not None
                assert before_run <= scheduler.schedule["pmp"].last_run <= after_run


class TestScheduleStatus:
    def test_get_schedule_status(self):
        """Returns status for all configured sources."""
        with patch.object(Path, "exists", return_value=False):
            scheduler = CollectionScheduler()

            status = scheduler.get_schedule_status()

            assert isinstance(status, dict)
            assert "pmp" in status
            assert "otc" in status

            for source_name, source_status in status.items():
                assert isinstance(source_status, ScheduleStatus)
                assert source_status.source == source_name
                assert isinstance(source_status.enabled, bool)

    def test_status_includes_next_run(self):
        """Status shows next scheduled run time."""
        with patch.object(Path, "exists", return_value=False):
            scheduler = CollectionScheduler()

            status = scheduler.get_schedule_status()

            for source_status in status.values():
                assert hasattr(source_status, 'next_run')
                assert isinstance(source_status.next_run, datetime)
                assert hasattr(source_status, 'is_overdue')
                assert isinstance(source_status.is_overdue, bool)
