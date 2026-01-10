"""
TDD Tests for Azure Data Freshness Handler

Tests written BEFORE implementation per TDD protocol.
Run with: pytest tests/test_data_freshness.py -v
"""

import pytest
from datetime import datetime, date, timedelta
from typing import Any, Dict, Optional


class TestDataLagConstants:
    """Tests for data lag constant definitions."""

    def test_cost_management_lag_48_hours(self):
        """Cost Management API has 24-72hr lag, use 48hr as safe default."""
        from claude.tools.experimental.azure.data_freshness import DATA_LAG_HOURS

        assert "cost_management" in DATA_LAG_HOURS
        assert DATA_LAG_HOURS["cost_management"] == 48

    def test_azure_monitor_lag_4_hours(self):
        """Azure Monitor metrics have 1-4hr lag."""
        from claude.tools.experimental.azure.data_freshness import DATA_LAG_HOURS

        assert "azure_monitor" in DATA_LAG_HOURS
        assert DATA_LAG_HOURS["azure_monitor"] == 4

    def test_azure_advisor_lag_24_hours(self):
        """Azure Advisor refreshes daily."""
        from claude.tools.experimental.azure.data_freshness import DATA_LAG_HOURS

        assert "azure_advisor" in DATA_LAG_HOURS
        assert DATA_LAG_HOURS["azure_advisor"] == 24

    def test_resource_graph_lag_1_hour(self):
        """Resource Graph is near real-time."""
        from claude.tools.experimental.azure.data_freshness import DATA_LAG_HOURS

        assert "resource_graph" in DATA_LAG_HOURS
        assert DATA_LAG_HOURS["resource_graph"] == 1


class TestDataFreshnessDataclass:
    """Tests for DataFreshness dataclass."""

    def test_data_freshness_creation(self):
        """DataFreshness dataclass should store all fields."""
        from claude.tools.experimental.azure.data_freshness import DataFreshness

        now = datetime.now()
        freshness = DataFreshness(
            data_type="cost_management",
            last_collection=now,
            expected_lag_hours=48.0,
            actual_lag_hours=52.0,
            is_stale=True,
            warning_message="Data is stale",
        )

        assert freshness.data_type == "cost_management"
        assert freshness.last_collection == now
        assert freshness.expected_lag_hours == 48.0
        assert freshness.actual_lag_hours == 52.0
        assert freshness.is_stale is True
        assert freshness.warning_message == "Data is stale"

    def test_effective_as_of_property(self):
        """effective_as_of should subtract expected lag from collection time."""
        from claude.tools.experimental.azure.data_freshness import DataFreshness

        collection_time = datetime(2026, 1, 10, 12, 0, 0)
        freshness = DataFreshness(
            data_type="cost_management",
            last_collection=collection_time,
            expected_lag_hours=48.0,
            actual_lag_hours=48.0,
            is_stale=False,
        )

        expected_effective = datetime(2026, 1, 8, 12, 0, 0)  # 48 hours before
        assert freshness.effective_as_of == expected_effective

    def test_warning_message_optional(self):
        """warning_message should default to None."""
        from claude.tools.experimental.azure.data_freshness import DataFreshness

        freshness = DataFreshness(
            data_type="cost_management",
            last_collection=datetime.now(),
            expected_lag_hours=48.0,
            actual_lag_hours=48.0,
            is_stale=False,
        )

        assert freshness.warning_message is None


class TestDataFreshnessManager:
    """Tests for DataFreshnessManager class."""

    def test_get_safe_query_end_date_cost_management(self):
        """Safe query end date should be now minus 48 hours for cost data."""
        from claude.tools.experimental.azure.data_freshness import DataFreshnessManager

        manager = DataFreshnessManager()
        before = datetime.now() - timedelta(hours=48, minutes=1)
        safe_date = manager.get_safe_query_end_date("cost_management")
        after = datetime.now() - timedelta(hours=48)

        # Safe date should be approximately 48 hours ago
        assert before <= safe_date <= after + timedelta(minutes=1)

    def test_get_safe_query_end_date_azure_monitor(self):
        """Safe query end date should be now minus 4 hours for metrics."""
        from claude.tools.experimental.azure.data_freshness import DataFreshnessManager

        manager = DataFreshnessManager()
        before = datetime.now() - timedelta(hours=4, minutes=1)
        safe_date = manager.get_safe_query_end_date("azure_monitor")
        after = datetime.now() - timedelta(hours=4)

        # Safe date should be approximately 4 hours ago
        assert before <= safe_date <= after + timedelta(minutes=1)

    def test_get_safe_query_end_date_unknown_type_defaults_48(self):
        """Unknown data type should default to 48 hour lag (safe default)."""
        from claude.tools.experimental.azure.data_freshness import DataFreshnessManager

        manager = DataFreshnessManager()
        before = datetime.now() - timedelta(hours=48, minutes=1)
        safe_date = manager.get_safe_query_end_date("unknown_api_type")
        after = datetime.now() - timedelta(hours=48)

        assert before <= safe_date <= after + timedelta(minutes=1)

    def test_is_data_complete_for_date_old_date_true(self):
        """Data should be complete for dates well in the past."""
        from claude.tools.experimental.azure.data_freshness import DataFreshnessManager

        manager = DataFreshnessManager()
        old_date = date(2026, 1, 1)  # 9 days ago

        assert manager.is_data_complete_for_date("cost_management", old_date) is True

    def test_is_data_complete_for_date_yesterday_false_for_cost(self):
        """Yesterday's cost data may be incomplete (within 48hr lag)."""
        from claude.tools.experimental.azure.data_freshness import DataFreshnessManager

        manager = DataFreshnessManager()
        yesterday = date.today() - timedelta(days=1)

        # Cost data has 48hr lag, so yesterday is likely incomplete
        assert manager.is_data_complete_for_date("cost_management", yesterday) is False

    def test_is_data_complete_for_date_yesterday_true_for_metrics(self):
        """Yesterday's metrics should be complete (4hr lag)."""
        from claude.tools.experimental.azure.data_freshness import DataFreshnessManager

        manager = DataFreshnessManager()
        yesterday = date.today() - timedelta(days=1)

        assert manager.is_data_complete_for_date("azure_monitor", yesterday) is True

    def test_is_data_complete_for_date_today_always_false(self):
        """Today's data is never complete for any data type."""
        from claude.tools.experimental.azure.data_freshness import DataFreshnessManager

        manager = DataFreshnessManager()
        today = date.today()

        assert manager.is_data_complete_for_date("cost_management", today) is False
        assert manager.is_data_complete_for_date("azure_monitor", today) is False
        assert manager.is_data_complete_for_date("resource_graph", today) is False

    def test_get_freshness_warning_cost_management(self):
        """Warning message should include lag hours and effective date."""
        from claude.tools.experimental.azure.data_freshness import DataFreshnessManager

        manager = DataFreshnessManager()
        warning = manager.get_freshness_warning("cost_management")

        assert warning is not None
        assert "48" in warning
        assert "cost_management" in warning

    def test_get_freshness_warning_azure_monitor(self):
        """Monitor warning should mention 4 hour lag."""
        from claude.tools.experimental.azure.data_freshness import DataFreshnessManager

        manager = DataFreshnessManager()
        warning = manager.get_freshness_warning("azure_monitor")

        assert warning is not None
        assert "4" in warning

    def test_get_freshness_warning_includes_effective_timestamp(self):
        """Warning should include effective as-of timestamp."""
        from claude.tools.experimental.azure.data_freshness import DataFreshnessManager

        manager = DataFreshnessManager()
        warning = manager.get_freshness_warning("cost_management")

        # Should contain a date string
        assert any(char.isdigit() for char in warning)
        assert "effective" in warning.lower() or "as of" in warning.lower()


class TestDataFreshnessTracking:
    """Tests for tracking data collection status."""

    def test_update_collection_status(self):
        """Should track when data was last collected."""
        from claude.tools.experimental.azure.data_freshness import DataFreshnessManager

        manager = DataFreshnessManager()
        now = datetime.now()

        manager.update_collection_status(
            data_type="cost_management",
            last_successful=now,
            is_healthy=True,
        )

        status = manager.get_collection_status("cost_management")
        assert status is not None
        assert status["last_successful"] == now
        assert status["is_healthy"] is True

    def test_collection_status_includes_error_message(self):
        """Should track error message for failed collections."""
        from claude.tools.experimental.azure.data_freshness import DataFreshnessManager

        manager = DataFreshnessManager()
        now = datetime.now()

        manager.update_collection_status(
            data_type="cost_management",
            last_attempted=now,
            is_healthy=False,
            error_message="Rate limited",
        )

        status = manager.get_collection_status("cost_management")
        assert status["is_healthy"] is False
        assert status["error_message"] == "Rate limited"

    def test_get_freshness_for_data_type(self):
        """Should return DataFreshness object for a data type."""
        from claude.tools.experimental.azure.data_freshness import (
            DataFreshnessManager,
            DataFreshness,
        )

        manager = DataFreshnessManager()
        collection_time = datetime.now() - timedelta(hours=2)

        manager.update_collection_status(
            data_type="cost_management",
            last_successful=collection_time,
            is_healthy=True,
        )

        freshness = manager.get_freshness("cost_management")

        assert isinstance(freshness, DataFreshness)
        assert freshness.data_type == "cost_management"
        assert freshness.expected_lag_hours == 48

    def test_stale_detection_when_collection_too_old(self):
        """Should mark as stale when last collection is too old."""
        from claude.tools.experimental.azure.data_freshness import DataFreshnessManager

        manager = DataFreshnessManager()
        # Collection from 72 hours ago - way past the 48hr lag
        old_collection = datetime.now() - timedelta(hours=72)

        manager.update_collection_status(
            data_type="cost_management",
            last_successful=old_collection,
            is_healthy=True,
        )

        freshness = manager.get_freshness("cost_management")

        # Data is stale if actual lag exceeds 2x expected lag
        assert freshness.is_stale is True

    def test_not_stale_when_collection_recent(self):
        """Should not be stale when collection is recent."""
        from claude.tools.experimental.azure.data_freshness import DataFreshnessManager

        manager = DataFreshnessManager()
        recent_collection = datetime.now() - timedelta(hours=1)

        manager.update_collection_status(
            data_type="cost_management",
            last_successful=recent_collection,
            is_healthy=True,
        )

        freshness = manager.get_freshness("cost_management")

        assert freshness.is_stale is False


class TestDataFreshnessEdgeCases:
    """Edge case tests for data freshness handling."""

    def test_no_collection_status_returns_unknown_freshness(self):
        """When no collection status exists, should return unknown/stale."""
        from claude.tools.experimental.azure.data_freshness import DataFreshnessManager

        manager = DataFreshnessManager()

        freshness = manager.get_freshness("cost_management")

        # No collection ever = stale
        assert freshness.is_stale is True
        assert freshness.warning_message is not None

    def test_get_all_freshness_statuses(self):
        """Should return freshness status for all tracked data types."""
        from claude.tools.experimental.azure.data_freshness import DataFreshnessManager

        manager = DataFreshnessManager()
        now = datetime.now()

        manager.update_collection_status("cost_management", now, True)
        manager.update_collection_status("azure_monitor", now, True)

        all_statuses = manager.get_all_freshness()

        assert len(all_statuses) >= 2
        assert any(s.data_type == "cost_management" for s in all_statuses)
        assert any(s.data_type == "azure_monitor" for s in all_statuses)

    def test_safe_date_range_for_analysis(self):
        """Should provide safe date range for analysis."""
        from claude.tools.experimental.azure.data_freshness import DataFreshnessManager

        manager = DataFreshnessManager()

        start_date, end_date = manager.get_safe_date_range(
            data_type="cost_management",
            lookback_days=30,
        )

        # End date should account for 48hr lag
        expected_end = (datetime.now() - timedelta(hours=48)).date()
        expected_start = expected_end - timedelta(days=30)

        assert end_date <= expected_end
        assert start_date == expected_start

    def test_minimum_observation_period_check(self):
        """Should verify minimum observation period for recommendations."""
        from claude.tools.experimental.azure.data_freshness import DataFreshnessManager

        manager = DataFreshnessManager()
        now = datetime.now()

        # Collection started 5 days ago
        manager.update_collection_status(
            "cost_management",
            now,
            True,
            first_collection=now - timedelta(days=5),
        )

        # For 7-day minimum observation
        assert manager.has_minimum_observation_period("cost_management", 7) is False

        # For 3-day minimum observation
        assert manager.has_minimum_observation_period("cost_management", 3) is True
