"""
Azure Monitor Tool

Provides monitoring and alerting operations for Azure Portal API access.
Supports:
- Metric queries
- Log Analytics (Kusto) queries
- Alert management
- Metric definitions

TDD Implementation - Tests in tests/test_azure_monitor.py
"""

from enum import Enum
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Lazy imports for optional dependencies
_MonitorManagementClient = None
_LogsQueryClient = None
_AlertsManagementClient = None
_DefaultAzureCredential = None


def _get_monitor_client():
    global _MonitorManagementClient
    if _MonitorManagementClient is None:
        from azure.mgmt.monitor import MonitorManagementClient
        _MonitorManagementClient = MonitorManagementClient
    return _MonitorManagementClient


def _get_logs_client():
    global _LogsQueryClient
    if _LogsQueryClient is None:
        from azure.monitor.query import LogsQueryClient
        _LogsQueryClient = LogsQueryClient
    return _LogsQueryClient


def _get_alerts_client():
    global _AlertsManagementClient
    if _AlertsManagementClient is None:
        from azure.mgmt.alertsmanagement import AlertsManagementClient
        _AlertsManagementClient = AlertsManagementClient
    return _AlertsManagementClient


def _get_default_credential():
    global _DefaultAzureCredential
    if _DefaultAzureCredential is None:
        from azure.identity import DefaultAzureCredential
        _DefaultAzureCredential = DefaultAzureCredential
    return _DefaultAzureCredential


class AzureMonitorError(Exception):
    """Raised when Azure monitor operations fail."""
    pass


class MetricAggregation(Enum):
    """Metric aggregation types."""
    AVERAGE = "Average"
    TOTAL = "Total"
    MINIMUM = "Minimum"
    MAXIMUM = "Maximum"
    COUNT = "Count"


class MetricTimespan(Enum):
    """Predefined metric timespans."""
    LAST_HOUR = "PT1H"
    LAST_4_HOURS = "PT4H"
    LAST_12_HOURS = "PT12H"
    LAST_24_HOURS = "PT24H"
    LAST_48_HOURS = "PT48H"
    LAST_7_DAYS = "P7D"
    LAST_30_DAYS = "P30D"


class AzureMonitorManager:
    """
    Manages Azure monitoring operations.

    Usage:
        manager = AzureMonitorManager(credential=credential, subscription_id="sub-id")
        metrics = manager.query_metrics(resource_id, "Percentage CPU")
        logs = manager.query_logs(workspace_id, "Heartbeat | count")
    """

    def __init__(
        self,
        credential: Optional[Any] = None,
        subscription_id: Optional[str] = None
    ):
        """
        Initialize Azure monitor manager.

        Args:
            credential: Azure credential object
            subscription_id: Subscription ID
        """
        if not subscription_id:
            raise ValueError("subscription_id is required for monitor management")

        self.subscription_id = subscription_id

        # Create default credential if not provided
        if credential is None:
            try:
                from azure.identity import DefaultAzureCredential
                credential = DefaultAzureCredential()
            except ImportError as e:
                raise AzureMonitorError(
                    "Azure SDK not installed. Run: pip install azure-identity azure-mgmt-monitor"
                ) from e

        self.credential = credential

        # Initialize monitor client
        try:
            MonitorManagementClient = _get_monitor_client()
            self._monitor_client = MonitorManagementClient(credential, subscription_id)
        except ImportError as e:
            raise AzureMonitorError(
                "azure-mgmt-monitor not installed. Run: pip install azure-mgmt-monitor"
            ) from e

    def query_metrics(
        self,
        resource_id: str,
        metric_name: str,
        aggregation: Union[MetricAggregation, List[MetricAggregation]] = MetricAggregation.AVERAGE,
        timespan: Optional[MetricTimespan] = None,
        interval: str = "PT5M"
    ) -> Dict[str, Any]:
        """
        Query metrics for a resource.

        Args:
            resource_id: Full Azure resource ID
            metric_name: Name of the metric
            aggregation: Aggregation type(s)
            timespan: Time range for query
            interval: Data interval (e.g., "PT5M", "PT1H")

        Returns:
            Dict with metric data
        """
        try:
            # Convert single aggregation to list
            if isinstance(aggregation, MetricAggregation):
                aggregations = [aggregation]
            else:
                aggregations = aggregation

            agg_str = ",".join(a.value for a in aggregations)

            # Build timespan string
            if timespan:
                timespan_str = timespan.value
            else:
                timespan_str = MetricTimespan.LAST_HOUR.value

            result = self._monitor_client.metrics.list(
                resource_id,
                metricnames=metric_name,
                aggregation=agg_str,
                timespan=timespan_str,
                interval=interval
            )

            # Parse results
            data = []
            metric_info = None

            for metric in result.value:
                metric_info = {
                    "name": metric.name.value if metric.name else metric_name,
                    "unit": str(metric.unit) if metric.unit else None
                }

                for timeseries in metric.timeseries:
                    for point in timeseries.data:
                        point_data = {
                            "timestamp": point.time_stamp.isoformat() if point.time_stamp else None
                        }

                        # Add all requested aggregations
                        if MetricAggregation.AVERAGE in aggregations and hasattr(point, 'average'):
                            point_data["average"] = point.average
                            point_data["value"] = point.average  # Default to average
                        if MetricAggregation.MINIMUM in aggregations and hasattr(point, 'minimum'):
                            point_data["minimum"] = point.minimum
                        if MetricAggregation.MAXIMUM in aggregations and hasattr(point, 'maximum'):
                            point_data["maximum"] = point.maximum
                        if MetricAggregation.TOTAL in aggregations and hasattr(point, 'total'):
                            point_data["total"] = point.total
                        if MetricAggregation.COUNT in aggregations and hasattr(point, 'count'):
                            point_data["count"] = point.count

                        # If only one aggregation, use it as "value"
                        if len(aggregations) == 1:
                            agg_name = aggregations[0].value.lower()
                            if hasattr(point, agg_name):
                                point_data["value"] = getattr(point, agg_name)

                        data.append(point_data)

            return {
                "metric_name": metric_name,
                "resource_id": resource_id,
                "data": data,
                "timespan": timespan_str,
                "interval": interval,
                "unit": metric_info["unit"] if metric_info else None
            }

        except Exception as e:
            raise AzureMonitorError(f"Failed to query metrics: {e}") from e

    def get_metric_definitions(self, resource_id: str) -> List[Dict[str, Any]]:
        """
        Get available metric definitions for a resource.

        Args:
            resource_id: Full Azure resource ID

        Returns:
            List of metric definitions
        """
        try:
            definitions = []

            for definition in self._monitor_client.metric_definitions.list(resource_id):
                definitions.append({
                    "name": definition.name.value if definition.name else None,
                    "display_name": definition.name.localized_value if definition.name else None,
                    "unit": str(definition.unit) if definition.unit else None,
                    "primary_aggregation": str(definition.primary_aggregation_type) if definition.primary_aggregation_type else None,
                    "dimensions": [d.value for d in definition.dimensions] if definition.dimensions else []
                })

            return definitions

        except Exception as e:
            raise AzureMonitorError(f"Failed to get metric definitions: {e}") from e

    def query_logs(
        self,
        workspace_id: str,
        query: str,
        timespan: Optional[timedelta] = None,
        include_statistics: bool = False
    ) -> Dict[str, Any]:
        """
        Execute a Log Analytics (Kusto) query.

        Args:
            workspace_id: Log Analytics workspace ID
            query: Kusto query string
            timespan: Time range for query
            include_statistics: Include query statistics

        Returns:
            Dict with query results
        """
        try:
            from azure.monitor.query import LogsQueryClient

            logs_client = LogsQueryClient(self.credential)

            result = logs_client.query_workspace(
                workspace_id=workspace_id,
                query=query,
                timespan=timespan or timedelta(hours=24)
            )

            # Parse results
            data = []

            if result.tables:
                for table in result.tables:
                    columns = [col.name for col in table.columns]

                    for row in table.rows:
                        row_dict = {}
                        for i, value in enumerate(row):
                            row_dict[columns[i]] = value
                        data.append(row_dict)

            response = {
                "data": data,
                "query": query,
                "workspace_id": workspace_id
            }

            if include_statistics and hasattr(result, 'statistics'):
                response["statistics"] = result.statistics

            return response

        except Exception as e:
            raise AzureMonitorError(f"Failed to query logs: {e}") from e

    def list_alerts(
        self,
        severity_filter: Optional[List[str]] = None,
        fired_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        List alerts for the subscription.

        Args:
            severity_filter: Filter by severity (e.g., ["Sev0", "Sev1"])
            fired_only: Only show fired (active) alerts

        Returns:
            List of alert dictionaries
        """
        try:
            AlertsManagementClient = _get_alerts_client()
            alerts_client = AlertsManagementClient(self.credential, self.subscription_id)

            alerts = []

            for alert in alerts_client.alerts.get_all():
                alert_dict = {
                    "name": alert.name,
                    "severity": str(alert.severity) if alert.severity else None,
                    "state": str(alert.monitor_condition) if alert.monitor_condition else None,
                    "signal_type": str(alert.signal_type) if alert.signal_type else None,
                    "target_resource": alert.target_resource,
                    "fired_time": alert.fired_date_time.isoformat() if alert.fired_date_time else None,
                    "resolved_time": alert.resolved_date_time.isoformat() if alert.resolved_date_time else None
                }

                # Apply filters
                if severity_filter and alert_dict["severity"] not in severity_filter:
                    continue

                if fired_only and alert_dict["state"] != "Fired":
                    continue

                alerts.append(alert_dict)

            return alerts

        except Exception as e:
            raise AzureMonitorError(f"Failed to list alerts: {e}") from e


# Standalone functions for convenience

def query_metrics(
    resource_id: str,
    metric_name: str,
    aggregation: Union[MetricAggregation, List[MetricAggregation]] = MetricAggregation.AVERAGE,
    timespan: Optional[MetricTimespan] = None,
    subscription_id: Optional[str] = None
) -> Dict[str, Any]:
    """Query metrics for a resource."""
    # Extract subscription ID from resource ID if not provided
    if not subscription_id:
        parts = resource_id.split("/")
        sub_idx = parts.index("subscriptions") if "subscriptions" in parts else -1
        if sub_idx >= 0 and sub_idx + 1 < len(parts):
            subscription_id = parts[sub_idx + 1]

    if not subscription_id:
        raise ValueError("subscription_id is required")

    manager = AzureMonitorManager(subscription_id=subscription_id)
    return manager.query_metrics(resource_id, metric_name, aggregation, timespan)


def query_logs(
    workspace_id: str,
    query: str,
    timespan: Optional[timedelta] = None,
    include_statistics: bool = False,
    subscription_id: Optional[str] = None
) -> Dict[str, Any]:
    """Execute a Log Analytics query."""
    if not subscription_id:
        raise ValueError("subscription_id is required for log queries")

    manager = AzureMonitorManager(subscription_id=subscription_id)
    return manager.query_logs(workspace_id, query, timespan, include_statistics)


def list_alerts(
    subscription_id: str,
    severity_filter: Optional[List[str]] = None,
    fired_only: bool = False
) -> List[Dict[str, Any]]:
    """List alerts for a subscription."""
    manager = AzureMonitorManager(subscription_id=subscription_id)
    return manager.list_alerts(severity_filter, fired_only)


def get_metric_definitions(
    resource_id: str,
    subscription_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Get metric definitions for a resource."""
    # Extract subscription ID from resource ID if not provided
    if not subscription_id:
        parts = resource_id.split("/")
        sub_idx = parts.index("subscriptions") if "subscriptions" in parts else -1
        if sub_idx >= 0 and sub_idx + 1 < len(parts):
            subscription_id = parts[sub_idx + 1]

    if not subscription_id:
        raise ValueError("subscription_id is required")

    manager = AzureMonitorManager(subscription_id=subscription_id)
    return manager.get_metric_definitions(resource_id)


# CLI interface
def main():
    """CLI interface for monitor operations."""
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Azure Monitor Tool")
    parser.add_argument("--subscription-id", required=True, help="Subscription ID")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Metrics
    metrics_parser = subparsers.add_parser("metrics", help="Query metrics")
    metrics_parser.add_argument("--resource-id", required=True, help="Resource ID")
    metrics_parser.add_argument("--metric", required=True, help="Metric name")
    metrics_parser.add_argument("--timespan", choices=["1h", "4h", "24h", "7d", "30d"],
                                default="1h", help="Timespan")

    # Metric definitions
    def_parser = subparsers.add_parser("definitions", help="Get metric definitions")
    def_parser.add_argument("--resource-id", required=True, help="Resource ID")

    # Logs
    logs_parser = subparsers.add_parser("logs", help="Query logs")
    logs_parser.add_argument("--workspace-id", required=True, help="Workspace ID")
    logs_parser.add_argument("--query", required=True, help="Kusto query")

    # Alerts
    alerts_parser = subparsers.add_parser("alerts", help="List alerts")
    alerts_parser.add_argument("--fired-only", action="store_true", help="Only fired alerts")
    alerts_parser.add_argument("--severity", nargs="+", help="Filter by severity")

    args = parser.parse_args()

    try:
        if args.command == "metrics":
            timespan_map = {
                "1h": MetricTimespan.LAST_HOUR,
                "4h": MetricTimespan.LAST_4_HOURS,
                "24h": MetricTimespan.LAST_24_HOURS,
                "7d": MetricTimespan.LAST_7_DAYS,
                "30d": MetricTimespan.LAST_30_DAYS
            }
            result = query_metrics(
                args.resource_id,
                args.metric,
                timespan=timespan_map[args.timespan],
                subscription_id=args.subscription_id
            )
        elif args.command == "definitions":
            result = get_metric_definitions(
                args.resource_id,
                subscription_id=args.subscription_id
            )
        elif args.command == "logs":
            result = query_logs(
                args.workspace_id,
                args.query,
                subscription_id=args.subscription_id
            )
        elif args.command == "alerts":
            result = list_alerts(
                args.subscription_id,
                severity_filter=args.severity,
                fired_only=args.fired_only
            )
        else:
            parser.print_help()
            return 0

        print(json.dumps(result, indent=2, default=str))
        return 0

    except AzureMonitorError as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
