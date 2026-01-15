"""
Tests for Collection Scheduler

Sprint: SPRINT-FINISH-FIXFORWARD-001
Stub tests for pre-existing tool.
"""

import pytest
from datetime import time, datetime
from unittest.mock import patch, MagicMock


class TestSchedulerImports:
    """Verify module can be imported and exports exist."""

    def test_module_imports(self):
        """Module can be imported without error."""
        from claude.tools.collection import scheduler
        assert scheduler is not None

    def test_collection_scheduler_exists(self):
        """CollectionScheduler class exists."""
        from claude.tools.collection.scheduler import CollectionScheduler
        assert CollectionScheduler is not None

    def test_schedule_entry_exists(self):
        """ScheduleEntry dataclass exists."""
        from claude.tools.collection.scheduler import ScheduleEntry
        assert ScheduleEntry is not None

    def test_schedule_status_exists(self):
        """ScheduleStatus dataclass exists."""
        from claude.tools.collection.scheduler import ScheduleStatus
        assert ScheduleStatus is not None


class TestScheduleEntry:
    """Test ScheduleEntry dataclass."""

    def test_schedule_entry_creation(self):
        """ScheduleEntry can be created with required fields."""
        from claude.tools.collection.scheduler import ScheduleEntry

        entry = ScheduleEntry(
            source="test_source",
            refresh_time=time(6, 0),
            enabled=True,
            refresh_command="echo test"
        )

        assert entry.source == "test_source"
        assert entry.refresh_time == time(6, 0)
        assert entry.enabled is True
        assert entry.refresh_command == "echo test"
        assert entry.last_run is None


class TestCollectionScheduler:
    """Test CollectionScheduler functionality."""

    def test_scheduler_has_default_schedule(self):
        """CollectionScheduler has default schedule configured."""
        from claude.tools.collection.scheduler import CollectionScheduler

        assert hasattr(CollectionScheduler, 'DEFAULT_SCHEDULE')
        assert 'pmp' in CollectionScheduler.DEFAULT_SCHEDULE
        assert 'otc' in CollectionScheduler.DEFAULT_SCHEDULE

    def test_get_pending_refreshes_method_exists(self):
        """get_pending_refreshes method exists."""
        from claude.tools.collection.scheduler import CollectionScheduler

        with patch.object(CollectionScheduler, '_load_schedule', return_value={}):
            with patch.object(CollectionScheduler, '_load_state', return_value=None):
                scheduler = CollectionScheduler()
                assert callable(scheduler.get_pending_refreshes)

    def test_get_schedule_status_method_exists(self):
        """get_schedule_status method exists."""
        from claude.tools.collection.scheduler import CollectionScheduler

        with patch.object(CollectionScheduler, '_load_schedule', return_value={}):
            with patch.object(CollectionScheduler, '_load_state', return_value=None):
                scheduler = CollectionScheduler()
                assert callable(scheduler.get_schedule_status)
