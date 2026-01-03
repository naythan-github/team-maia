"""
TDD Tests for Azure Monitor Tool
Tests written BEFORE implementation per TDD protocol.

Test Categories:
1. Metrics queries
2. Log queries (Log Analytics)
3. Alert operations
4. Error handling
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from typing import List, Dict
import json

try:
    from claude.tools.experimental.azure.azure_monitor import (
        AzureMonitorManager,
        query_metrics,
        query_logs,
        list_alerts,
        get_metric_definitions,
        MetricAggregation,
        MetricTimespan,
        AzureMonitorError,
    )
    IMPLEMENTATION_EXISTS = True
except ImportError:
    IMPLEMENTATION_EXISTS = False


pytestmark = pytest.mark.skipif(
    not IMPLEMENTATION_EXISTS,
    reason="Implementation not yet created - TDD red phase"
)


@pytest.fixture
def mock_credential():
    """Provide a mock credential."""
    return Mock()


@pytest.fixture
def mock_monitor_client():
    """Provide a mock monitor management client."""
    return Mock()


class TestAzureMonitorManager:
    """Test the main monitor manager class."""

    def test_init_with_credential(self, mock_credential):
        """Should initialize with provided credential."""
        with patch('claude.tools.experimental.azure.azure_monitor._get_monitor_client') as mock_get_client:
            mock_client_class = Mock()
            mock_get_client.return_value = mock_client_class

            manager = AzureMonitorManager(
                credential=mock_credential,
                subscription_id="sub-1"
            )
            assert manager.subscription_id == "sub-1"

    def test_init_requires_subscription_id(self, mock_credential):
        """Should require subscription_id for initialization."""
        with pytest.raises(ValueError) as exc_info:
            AzureMonitorManager(credential=mock_credential, subscription_id=None)
        assert "subscription_id" in str(exc_info.value).lower()


class TestMetricQueries:
    """Test metric query operations."""

    def test_query_metrics_cpu_percentage(self, mock_credential):
        """Should query CPU percentage metrics for a VM."""
        # Create mock data points
        point1 = Mock()
        point1.time_stamp = datetime(2024, 1, 1, 12, 0)
        point1.average = 45.5

        point2 = Mock()
        point2.time_stamp = datetime(2024, 1, 1, 12, 5)
        point2.average = 52.3

        # Create mock timeseries
        timeseries = Mock()
        timeseries.data = [point1, point2]

        # Create mock metric name
        metric_name_obj = Mock()
        metric_name_obj.value = "Percentage CPU"

        # Create mock metric
        metric = Mock()
        metric.name = metric_name_obj
        metric.unit = "Percent"
        metric.timeseries = [timeseries]

        # Create mock result
        mock_result = Mock()
        mock_result.value = [metric]

        with patch('claude.tools.experimental.azure.azure_monitor._get_monitor_client') as mock_get_client:
            with patch('claude.tools.experimental.azure.azure_monitor._get_default_credential') as mock_get_cred:
                mock_client_class = Mock()
                mock_client = Mock()
                mock_client.metrics.list.return_value = mock_result
                mock_client_class.return_value = mock_client
                mock_get_client.return_value = mock_client_class
                mock_get_cred.return_value = Mock

                manager = AzureMonitorManager(
                    credential=mock_credential,
                    subscription_id="sub-1"
                )
                # Override the client with our mock
                manager._monitor_client = mock_client

                result = manager.query_metrics(
                    resource_id="/subscriptions/sub-1/resourceGroups/rg-1/providers/Microsoft.Compute/virtualMachines/vm-1",
                    metric_name="Percentage CPU",
                    aggregation=MetricAggregation.AVERAGE
                )

                assert len(result["data"]) == 2
                assert result["data"][0]["value"] == 45.5
                assert result["metric_name"] == "Percentage CPU"

    def test_query_metrics_with_timespan(self, mock_credential):
        """Should support custom timespan for metrics."""
        point = Mock()
        point.time_stamp = datetime.now()
        point.average = 8000000000

        timeseries = Mock()
        timeseries.data = [point]

        metric_name_obj = Mock()
        metric_name_obj.value = "Available Memory Bytes"

        metric = Mock()
        metric.name = metric_name_obj
        metric.unit = "Bytes"
        metric.timeseries = [timeseries]

        mock_result = Mock()
        mock_result.value = [metric]

        with patch('claude.tools.experimental.azure.azure_monitor._get_monitor_client') as mock_get_client:
            mock_client_class = Mock()
            mock_client = Mock()
            mock_client.metrics.list.return_value = mock_result
            mock_client_class.return_value = mock_client
            mock_get_client.return_value = mock_client_class

            manager = AzureMonitorManager(
                credential=mock_credential,
                subscription_id="sub-1"
            )
            manager._monitor_client = mock_client

            result = manager.query_metrics(
                resource_id="/sub/rg/providers/Microsoft.Compute/virtualMachines/vm-1",
                metric_name="Available Memory Bytes",
                timespan=MetricTimespan.LAST_HOUR
            )

            assert "timespan" in result
            assert result["timespan"] == "PT1H"

    def test_query_metrics_multiple_aggregations(self, mock_credential):
        """Should support multiple aggregations (min, max, avg)."""
        point = Mock()
        point.time_stamp = datetime.now()
        point.average = 1000
        point.minimum = 500
        point.maximum = 1500

        timeseries = Mock()
        timeseries.data = [point]

        metric_name_obj = Mock()
        metric_name_obj.value = "Network In Total"

        metric = Mock()
        metric.name = metric_name_obj
        metric.unit = "Bytes"
        metric.timeseries = [timeseries]

        mock_result = Mock()
        mock_result.value = [metric]

        with patch('claude.tools.experimental.azure.azure_monitor._get_monitor_client') as mock_get_client:
            mock_client_class = Mock()
            mock_client = Mock()
            mock_client.metrics.list.return_value = mock_result
            mock_client_class.return_value = mock_client
            mock_get_client.return_value = mock_client_class

            manager = AzureMonitorManager(
                credential=mock_credential,
                subscription_id="sub-1"
            )
            manager._monitor_client = mock_client

            result = manager.query_metrics(
                resource_id="/sub/rg/providers/Microsoft.Compute/virtualMachines/vm-1",
                metric_name="Network In Total",
                aggregation=[
                    MetricAggregation.AVERAGE,
                    MetricAggregation.MINIMUM,
                    MetricAggregation.MAXIMUM
                ]
            )

            assert "average" in result["data"][0]
            assert "minimum" in result["data"][0]
            assert "maximum" in result["data"][0]

    def test_get_metric_definitions_for_resource(self, mock_credential):
        """Should list available metrics for a resource."""
        def1_name = Mock()
        def1_name.value = "Percentage CPU"
        def1_name.localized_value = "Percentage CPU"

        def1 = Mock()
        def1.name = def1_name
        def1.unit = "Percent"
        def1.primary_aggregation_type = "Average"
        def1.dimensions = []

        def2_name = Mock()
        def2_name.value = "Network In Total"
        def2_name.localized_value = "Network In Total"

        def2 = Mock()
        def2.name = def2_name
        def2.unit = "Bytes"
        def2.primary_aggregation_type = "Total"
        def2.dimensions = []

        mock_definitions = [def1, def2]

        with patch('claude.tools.experimental.azure.azure_monitor._get_monitor_client') as mock_get_client:
            mock_client_class = Mock()
            mock_client = Mock()
            mock_client.metric_definitions.list.return_value = mock_definitions
            mock_client_class.return_value = mock_client
            mock_get_client.return_value = mock_client_class

            manager = AzureMonitorManager(
                credential=mock_credential,
                subscription_id="sub-1"
            )
            manager._monitor_client = mock_client

            result = manager.get_metric_definitions(
                resource_id="/sub/rg/providers/Microsoft.Compute/virtualMachines/vm-1"
            )

            assert len(result) == 2
            assert result[0]["name"] == "Percentage CPU"
            assert result[0]["unit"] == "Percent"


class TestLogQueries:
    """Test Log Analytics query operations."""

    def test_query_logs_basic_kusto(self, mock_credential):
        """Should execute basic Kusto query."""
        col1 = Mock()
        col1.name = "TimeGenerated"
        col2 = Mock()
        col2.name = "Computer"
        col3 = Mock()
        col3.name = "CounterValue"

        table = Mock()
        table.columns = [col1, col2, col3]
        table.rows = [
            [datetime(2024, 1, 1, 12, 0), "vm-1", 45.5],
            [datetime(2024, 1, 1, 12, 5), "vm-1", 52.3],
        ]

        mock_result = Mock()
        mock_result.tables = [table]

        with patch('claude.tools.experimental.azure.azure_monitor._get_logs_client') as mock_get_client:
            with patch('claude.tools.experimental.azure.azure_monitor._get_monitor_client'):
                mock_client_class = Mock()
                mock_client = Mock()
                mock_client.query_workspace.return_value = mock_result
                mock_client_class.return_value = mock_client
                mock_get_client.return_value = mock_client_class

                manager = AzureMonitorManager(
                    credential=mock_credential,
                    subscription_id="sub-1"
                )

                # Patch the logs client directly
                with patch.object(manager, 'credential', mock_credential):
                    with patch('azure.monitor.query.LogsQueryClient') as mock_logs_class:
                        mock_logs_class.return_value = mock_client

                        result = manager.query_logs(
                            workspace_id="workspace-123",
                            query="Perf | where ObjectName == 'Processor' | take 10"
                        )

                        assert len(result["data"]) == 2
                        assert result["data"][0]["Computer"] == "vm-1"

    def test_query_logs_with_timespan(self, mock_credential):
        """Should support timespan parameter for log queries."""
        table = Mock()
        table.columns = []
        table.rows = []

        mock_result = Mock()
        mock_result.tables = [table]

        with patch('claude.tools.experimental.azure.azure_monitor._get_monitor_client'):
            with patch('azure.monitor.query.LogsQueryClient') as mock_logs_class:
                mock_client = Mock()
                mock_client.query_workspace.return_value = mock_result
                mock_logs_class.return_value = mock_client

                manager = AzureMonitorManager(
                    credential=mock_credential,
                    subscription_id="sub-1"
                )

                result = manager.query_logs(
                    workspace_id="workspace-123",
                    query="Heartbeat | count",
                    timespan=timedelta(hours=24)
                )

                # Verify query was made
                mock_client.query_workspace.assert_called_once()

    def test_query_logs_returns_statistics(self, mock_credential):
        """Should include query statistics in response."""
        table = Mock()
        table.columns = []
        table.rows = []

        mock_result = Mock()
        mock_result.tables = [table]
        mock_result.statistics = {"query_time": 0.5, "result_count": 100}

        with patch('claude.tools.experimental.azure.azure_monitor._get_monitor_client'):
            with patch('azure.monitor.query.LogsQueryClient') as mock_logs_class:
                mock_client = Mock()
                mock_client.query_workspace.return_value = mock_result
                mock_logs_class.return_value = mock_client

                manager = AzureMonitorManager(
                    credential=mock_credential,
                    subscription_id="sub-1"
                )

                result = manager.query_logs(
                    workspace_id="workspace-123",
                    query="SecurityEvent | count",
                    include_statistics=True
                )

                assert "statistics" in result


class TestAlertOperations:
    """Test alert management operations."""

    @pytest.fixture(autouse=True)
    def reset_cache(self):
        """Reset the lazy import cache before each test."""
        import claude.tools.experimental.azure.azure_monitor as azure_monitor
        azure_monitor._AlertsManagementClient = None
        yield
        azure_monitor._AlertsManagementClient = None

    def test_list_alerts_returns_all(self, mock_credential):
        """Should list all alerts for a subscription."""
        alert1 = Mock()
        alert1.name = "high-cpu-alert"
        alert1.severity = "Sev1"
        alert1.monitor_condition = "Fired"
        alert1.signal_type = "Metric"
        alert1.target_resource = "/sub/rg/vm-1"
        alert1.fired_date_time = datetime(2024, 1, 1, 12, 0)
        alert1.resolved_date_time = None

        alert2 = Mock()
        alert2.name = "disk-space-alert"
        alert2.severity = "Sev2"
        alert2.monitor_condition = "Resolved"
        alert2.signal_type = "Metric"
        alert2.target_resource = "/sub/rg/vm-2"
        alert2.fired_date_time = datetime(2024, 1, 1, 10, 0)
        alert2.resolved_date_time = datetime(2024, 1, 1, 11, 0)

        mock_alerts = [alert1, alert2]

        with patch('claude.tools.experimental.azure.azure_monitor._get_monitor_client'):
            with patch('claude.tools.experimental.azure.azure_monitor._get_alerts_client') as mock_get_alerts:
                mock_alerts_class = Mock()
                mock_alerts_client = Mock()
                mock_alerts_client.alerts.get_all.return_value = mock_alerts
                mock_alerts_class.return_value = mock_alerts_client
                mock_get_alerts.return_value = mock_alerts_class

                manager = AzureMonitorManager(
                    credential=mock_credential,
                    subscription_id="sub-1"
                )

                result = manager.list_alerts()

                assert len(result) == 2
                assert result[0]["name"] == "high-cpu-alert"
                assert result[0]["severity"] == "Sev1"
                assert result[0]["state"] == "Fired"

    def test_list_alerts_filter_by_severity(self, mock_credential):
        """Should filter alerts by severity."""
        alert = Mock()
        alert.name = "critical-alert"
        alert.severity = "Sev0"
        alert.monitor_condition = "Fired"
        alert.signal_type = "Metric"
        alert.target_resource = "/sub/rg/vm-1"
        alert.fired_date_time = datetime.now()
        alert.resolved_date_time = None

        mock_alerts = [alert]

        with patch('claude.tools.experimental.azure.azure_monitor._get_monitor_client'):
            with patch('claude.tools.experimental.azure.azure_monitor._get_alerts_client') as mock_get_alerts:
                mock_alerts_class = Mock()
                mock_alerts_client = Mock()
                mock_alerts_client.alerts.get_all.return_value = mock_alerts
                mock_alerts_class.return_value = mock_alerts_client
                mock_get_alerts.return_value = mock_alerts_class

                manager = AzureMonitorManager(
                    credential=mock_credential,
                    subscription_id="sub-1"
                )

                result = manager.list_alerts(severity_filter=["Sev0", "Sev1"])

                assert len(result) == 1
                assert result[0]["severity"] == "Sev0"

    def test_list_alerts_filter_fired_only(self, mock_credential):
        """Should filter to only fired (active) alerts."""
        alert = Mock()
        alert.name = "active-alert"
        alert.severity = "Sev1"
        alert.monitor_condition = "Fired"
        alert.signal_type = "Metric"
        alert.target_resource = "/sub/rg/vm-1"
        alert.fired_date_time = datetime.now()
        alert.resolved_date_time = None

        mock_alerts = [alert]

        with patch('claude.tools.experimental.azure.azure_monitor._get_monitor_client'):
            with patch('claude.tools.experimental.azure.azure_monitor._get_alerts_client') as mock_get_alerts:
                mock_alerts_class = Mock()
                mock_alerts_client = Mock()
                mock_alerts_client.alerts.get_all.return_value = mock_alerts
                mock_alerts_class.return_value = mock_alerts_client
                mock_get_alerts.return_value = mock_alerts_class

                manager = AzureMonitorManager(
                    credential=mock_credential,
                    subscription_id="sub-1"
                )

                result = manager.list_alerts(fired_only=True)

                assert len(result) == 1
                assert result[0]["state"] == "Fired"


class TestMetricEnums:
    """Test metric-related enums."""

    def test_aggregation_average(self):
        """Should support average aggregation."""
        assert MetricAggregation.AVERAGE.value == "Average"

    def test_aggregation_total(self):
        """Should support total aggregation."""
        assert MetricAggregation.TOTAL.value == "Total"

    def test_timespan_last_hour(self):
        """Should support last hour timespan."""
        assert MetricTimespan.LAST_HOUR.value == "PT1H"

    def test_timespan_last_24_hours(self):
        """Should support last 24 hours timespan."""
        assert MetricTimespan.LAST_24_HOURS.value == "PT24H"


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_invalid_resource_id_raises_error(self, mock_credential):
        """Should raise error for invalid resource ID."""
        with patch('claude.tools.experimental.azure.azure_monitor._get_monitor_client') as mock_get_client:
            mock_client_class = Mock()
            mock_client = Mock()
            mock_client.metrics.list.side_effect = Exception("Resource not found")
            mock_client_class.return_value = mock_client
            mock_get_client.return_value = mock_client_class

            manager = AzureMonitorManager(
                credential=mock_credential,
                subscription_id="sub-1"
            )
            manager._monitor_client = mock_client

            with pytest.raises(AzureMonitorError) as exc_info:
                manager.query_metrics(
                    resource_id="/invalid/resource/id",
                    metric_name="Percentage CPU"
                )

            assert "Resource not found" in str(exc_info.value)

    def test_invalid_kusto_query_raises_error(self, mock_credential):
        """Should raise error for invalid Kusto query."""
        with patch('claude.tools.experimental.azure.azure_monitor._get_monitor_client'):
            with patch('azure.monitor.query.LogsQueryClient') as mock_logs_class:
                mock_client = Mock()
                mock_client.query_workspace.side_effect = Exception("Query syntax error")
                mock_logs_class.return_value = mock_client

                manager = AzureMonitorManager(
                    credential=mock_credential,
                    subscription_id="sub-1"
                )

                with pytest.raises(AzureMonitorError) as exc_info:
                    manager.query_logs(
                        workspace_id="workspace-123",
                        query="INVALID QUERY SYNTAX"
                    )

                assert "syntax" in str(exc_info.value).lower()

    def test_workspace_not_found_raises_error(self, mock_credential):
        """Should raise error when workspace not found."""
        with patch('claude.tools.experimental.azure.azure_monitor._get_monitor_client'):
            with patch('azure.monitor.query.LogsQueryClient') as mock_logs_class:
                mock_client = Mock()
                mock_client.query_workspace.side_effect = Exception("Workspace not found")
                mock_logs_class.return_value = mock_client

                manager = AzureMonitorManager(
                    credential=mock_credential,
                    subscription_id="sub-1"
                )

                with pytest.raises(AzureMonitorError) as exc_info:
                    manager.query_logs(
                        workspace_id="invalid-workspace",
                        query="Heartbeat | count"
                    )

                assert "Workspace not found" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
