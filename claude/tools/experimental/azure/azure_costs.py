"""
Azure Cost Management Tool

Provides cost management and analysis for Azure Portal API access.
Supports:
- Usage cost queries
- Cost forecasting
- Budget management
- Cost breakdown by dimension (resource group, service, etc.)

TDD Implementation - Tests in tests/test_azure_costs.py
"""

from enum import Enum
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class AzureCostError(Exception):
    """Raised when Azure cost operations fail."""
    pass


class CostTimeframe(Enum):
    """Predefined timeframes for cost queries.

    Note: Values match Azure SDK TimeframeType enum.
    """
    LAST_7_DAYS = "WeekToDate"  # SDK uses WeekToDate (no 7-day option)
    LAST_30_DAYS = "TheLastMonth"
    BILLING_MONTH = "BillingMonthToDate"
    MONTH_TO_DATE = "MonthToDate"
    LAST_BILLING_MONTH = "TheLastBillingMonth"
    WEEK_TO_DATE = "WeekToDate"
    CUSTOM = "Custom"


class CostGranularity(Enum):
    """Cost data granularity.

    Note: Azure SDK only supports Daily granularity.
    MONTHLY is implemented via date range aggregation.
    """
    DAILY = "Daily"
    NONE = "None"  # For aggregated queries


class AzureCostManager:
    """
    Manages Azure cost operations.

    Usage:
        manager = AzureCostManager(credential=credential, subscription_id="sub-id")
        costs = manager.get_usage_costs()
        forecast = manager.get_forecast(days=30)
    """

    def __init__(
        self,
        credential: Optional[Any] = None,
        subscription_id: Optional[str] = None
    ):
        """
        Initialize Azure cost manager.

        Args:
            credential: Azure credential object
            subscription_id: Subscription ID for cost queries
        """
        if not subscription_id:
            raise ValueError("subscription_id is required for cost management")

        self.subscription_id = subscription_id

        # Create default credential if not provided
        if credential is None:
            try:
                from azure.identity import DefaultAzureCredential
                credential = DefaultAzureCredential()
            except ImportError as e:
                raise AzureCostError(
                    "Azure SDK not installed. Run: pip install azure-identity azure-mgmt-costmanagement"
                ) from e

        self.credential = credential

        # Initialize cost management client
        try:
            from azure.mgmt.costmanagement import CostManagementClient
            self._client = CostManagementClient(credential)
        except ImportError as e:
            raise AzureCostError(
                "azure-mgmt-costmanagement not installed. Run: pip install azure-mgmt-costmanagement"
            ) from e

    def get_usage_costs(
        self,
        timeframe: Optional[CostTimeframe] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        granularity: CostGranularity = CostGranularity.DAILY
    ) -> Dict[str, Any]:
        """
        Get usage costs for the subscription.

        Args:
            timeframe: Predefined timeframe
            start_date: Custom start date (YYYY-MM-DD)
            end_date: Custom end date (YYYY-MM-DD)
            granularity: Daily or Monthly

        Returns:
            Dict with cost data and totals
        """
        try:
            from azure.mgmt.costmanagement.models import (
                QueryDefinition,
                QueryTimePeriod,
                QueryDataset,
                QueryAggregation,
                QueryGrouping,
                TimeframeType,
                GranularityType
            )

            # Build query
            scope = f"/subscriptions/{self.subscription_id}"

            # Determine timeframe
            if start_date and end_date:
                # Validate dates
                start = datetime.strptime(start_date, "%Y-%m-%d")
                end = datetime.strptime(end_date, "%Y-%m-%d")
                if end < start:
                    raise ValueError("end_date must be after start_date")

                time_period = QueryTimePeriod(from_property=start, to=end)
                timeframe_type = TimeframeType.CUSTOM
            else:
                time_period = None
                timeframe_type = TimeframeType(
                    (timeframe or CostTimeframe.LAST_30_DAYS).value
                )

            # Build dataset - SDK only supports DAILY granularity
            # For NONE granularity, we skip the granularity parameter
            if granularity == CostGranularity.NONE:
                dataset = QueryDataset(
                    aggregation={
                        "totalCost": QueryAggregation(name="Cost", function="Sum")
                    },
                    grouping=[
                        QueryGrouping(type="Dimension", name="ResourceGroup")
                    ]
                )
            else:
                dataset = QueryDataset(
                    granularity=GranularityType.DAILY,  # Only DAILY is supported
                    aggregation={
                        "totalCost": QueryAggregation(name="Cost", function="Sum")
                    },
                    grouping=[
                        QueryGrouping(type="Dimension", name="ResourceGroup")
                    ]
                )

            query = QueryDefinition(
                type="Usage",
                timeframe=timeframe_type,
                time_period=time_period,
                dataset=dataset
            )

            result = self._client.query.usage(scope, query)

            # Parse results
            data = []
            total_cost = 0.0

            if result.rows:
                for row in result.rows:
                    cost = float(row[1]) if len(row) > 1 else 0.0
                    total_cost += cost
                    data.append({
                        "date": str(row[0]) if row else None,
                        "cost": cost,
                        "currency": row[2] if len(row) > 2 else "USD"
                    })

            return {
                "data": data,
                "total_cost": total_cost,
                "granularity": granularity.value,
                "timeframe": (timeframe or CostTimeframe.LAST_30_DAYS).value
            }

        except ValueError as e:
            raise e
        except Exception as e:
            raise AzureCostError(f"Failed to get usage costs: {e}") from e

    def get_forecast(self, forecast_days: int = 30) -> Dict[str, Any]:
        """
        Get cost forecast for the subscription.

        Args:
            forecast_days: Number of days to forecast

        Returns:
            Dict with forecast data
        """
        try:
            from azure.mgmt.costmanagement.models import (
                ForecastDefinition,
                ForecastTimePeriod,
                ForecastDataset,
                ForecastAggregation,
                GranularityType,
                ForecastType,
                ForecastTimeframe
            )

            scope = f"/subscriptions/{self.subscription_id}"

            # Forecast period
            start = datetime.now()
            end = start + timedelta(days=forecast_days)

            time_period = ForecastTimePeriod(from_property=start, to=end)

            dataset = ForecastDataset(
                granularity=GranularityType.DAILY,
                aggregation={
                    "totalCost": ForecastAggregation(name="Cost", function="Sum")
                }
            )

            query = ForecastDefinition(
                type=ForecastType.USAGE,
                timeframe=ForecastTimeframe.CUSTOM,
                time_period=time_period,
                dataset=dataset,
                include_actual_cost=True,
                include_fresh_partial_cost=True
            )

            result = self._client.forecast.usage(scope, query)

            # Parse results
            forecast = []
            if result.rows:
                for row in result.rows:
                    forecast.append({
                        "date": str(row[0]) if row else None,
                        "predicted_cost": float(row[1]) if len(row) > 1 else 0.0,
                        "confidence_low": float(row[2]) if len(row) > 2 else None,
                        "confidence_high": float(row[3]) if len(row) > 3 else None,
                        "currency": row[4] if len(row) > 4 else "USD"
                    })

            return {
                "forecast": forecast,
                "forecast_days": forecast_days,
                "generated_at": datetime.now().isoformat()
            }

        except Exception as e:
            raise AzureCostError(f"Failed to get forecast: {e}") from e

    def list_budgets(self) -> List[Dict[str, Any]]:
        """
        List all budgets for the subscription.

        Returns:
            List of budget dictionaries
        """
        try:
            scope = f"/subscriptions/{self.subscription_id}"
            budgets = []

            for budget in self._client.budgets.list(scope):
                current_spend = budget.current_spend.amount if budget.current_spend else 0.0
                percent_used = (current_spend / budget.amount * 100) if budget.amount > 0 else 0.0

                budget_dict = {
                    "name": budget.name,
                    "amount": budget.amount,
                    "time_grain": str(budget.time_grain),
                    "current_spend": current_spend,
                    "percent_used": round(percent_used, 1),
                    "time_period": {
                        "start": budget.time_period.start_date.isoformat() if budget.time_period else None,
                        "end": budget.time_period.end_date.isoformat() if budget.time_period else None
                    }
                }

                # Add alerts if present
                if budget.notifications:
                    budget_dict["alerts"] = []
                    for name, notification in budget.notifications.items():
                        budget_dict["alerts"].append({
                            "name": name,
                            "threshold": notification.threshold,
                            "operator": str(notification.operator),
                            "enabled": notification.enabled
                        })

                budgets.append(budget_dict)

            return budgets

        except Exception as e:
            raise AzureCostError(f"Failed to list budgets: {e}") from e


# Standalone functions for convenience

def get_usage_costs(
    subscription_id: str,
    timeframe: Optional[CostTimeframe] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    granularity: CostGranularity = CostGranularity.DAILY
) -> Dict[str, Any]:
    """Get usage costs for a subscription."""
    manager = AzureCostManager(subscription_id=subscription_id)
    return manager.get_usage_costs(
        timeframe=timeframe,
        start_date=start_date,
        end_date=end_date,
        granularity=granularity
    )


def get_cost_forecast(subscription_id: str, forecast_days: int = 30) -> Dict[str, Any]:
    """Get cost forecast for a subscription."""
    manager = AzureCostManager(subscription_id=subscription_id)
    return manager.get_forecast(forecast_days=forecast_days)


def list_budgets(subscription_id: str) -> List[Dict[str, Any]]:
    """List budgets for a subscription."""
    manager = AzureCostManager(subscription_id=subscription_id)
    return manager.list_budgets()


def get_cost_by_resource_group(
    subscription_id: str,
    timeframe: Optional[CostTimeframe] = None
) -> Dict[str, Any]:
    """Get costs grouped by resource group."""
    try:
        from azure.identity import DefaultAzureCredential
        from azure.mgmt.costmanagement import CostManagementClient
        from azure.mgmt.costmanagement.models import (
            QueryDefinition,
            QueryDataset,
            QueryAggregation,
            QueryGrouping,
            TimeframeType
        )

        credential = DefaultAzureCredential()
        client = CostManagementClient(credential)

        scope = f"/subscriptions/{subscription_id}"
        timeframe_type = TimeframeType((timeframe or CostTimeframe.LAST_30_DAYS).value)

        # Note: Omit granularity for aggregated queries (GranularityType.NONE not supported)
        dataset = QueryDataset(
            aggregation={
                "totalCost": QueryAggregation(name="Cost", function="Sum")
            },
            grouping=[
                QueryGrouping(type="Dimension", name="ResourceGroup")
            ]
        )

        query = QueryDefinition(
            type="Usage",
            timeframe=timeframe_type,
            dataset=dataset
        )

        result = client.query.usage(scope, query)

        breakdown = []
        total_cost = 0.0

        if result.rows:
            for row in result.rows:
                cost = float(row[1]) if len(row) > 1 else 0.0
                total_cost += cost
                breakdown.append({
                    "resource_group": row[0],
                    "cost": cost,
                    "currency": row[2] if len(row) > 2 else "USD"
                })

        # Sort by cost descending
        breakdown.sort(key=lambda x: x["cost"], reverse=True)

        return {
            "breakdown": breakdown,
            "total_cost": total_cost
        }

    except Exception as e:
        raise AzureCostError(f"Failed to get cost by resource group: {e}") from e


def get_cost_by_service(
    subscription_id: str,
    timeframe: Optional[CostTimeframe] = None
) -> Dict[str, Any]:
    """Get costs grouped by service type."""
    try:
        from azure.identity import DefaultAzureCredential
        from azure.mgmt.costmanagement import CostManagementClient
        from azure.mgmt.costmanagement.models import (
            QueryDefinition,
            QueryDataset,
            QueryAggregation,
            QueryGrouping,
            TimeframeType
        )

        credential = DefaultAzureCredential()
        client = CostManagementClient(credential)

        scope = f"/subscriptions/{subscription_id}"
        timeframe_type = TimeframeType((timeframe or CostTimeframe.LAST_30_DAYS).value)

        # Note: Omit granularity for aggregated queries (GranularityType.NONE not supported)
        dataset = QueryDataset(
            aggregation={
                "totalCost": QueryAggregation(name="Cost", function="Sum")
            },
            grouping=[
                QueryGrouping(type="Dimension", name="ServiceName")
            ]
        )

        query = QueryDefinition(
            type="Usage",
            timeframe=timeframe_type,
            dataset=dataset
        )

        result = client.query.usage(scope, query)

        breakdown = []
        total_cost = 0.0

        if result.rows:
            for row in result.rows:
                cost = float(row[1]) if len(row) > 1 else 0.0
                total_cost += cost
                breakdown.append({
                    "service": row[0],
                    "cost": cost,
                    "currency": row[2] if len(row) > 2 else "USD"
                })

        # Sort by cost descending
        breakdown.sort(key=lambda x: x["cost"], reverse=True)

        return {
            "breakdown": breakdown,
            "total_cost": total_cost
        }

    except Exception as e:
        raise AzureCostError(f"Failed to get cost by service: {e}") from e


# CLI interface
def main():
    """CLI interface for cost management."""
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Azure Cost Management Tool")
    parser.add_argument("--subscription-id", required=True, help="Subscription ID")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Usage costs
    usage_parser = subparsers.add_parser("usage", help="Get usage costs")
    usage_parser.add_argument("--timeframe", choices=["7d", "30d", "mtd", "billing"],
                              default="30d", help="Timeframe")
    usage_parser.add_argument("--granularity", choices=["daily", "monthly"],
                              default="daily", help="Granularity")

    # Forecast
    forecast_parser = subparsers.add_parser("forecast", help="Get cost forecast")
    forecast_parser.add_argument("--days", type=int, default=30, help="Forecast days")

    # Budgets
    subparsers.add_parser("budgets", help="List budgets")

    # By resource group
    subparsers.add_parser("by-rg", help="Costs by resource group")

    # By service
    subparsers.add_parser("by-service", help="Costs by service")

    args = parser.parse_args()

    try:
        if args.command == "usage":
            timeframe_map = {
                "7d": CostTimeframe.LAST_7_DAYS,
                "30d": CostTimeframe.LAST_30_DAYS,
                "mtd": CostTimeframe.MONTH_TO_DATE,
                "billing": CostTimeframe.BILLING_MONTH
            }
            granularity = CostGranularity.DAILY if args.granularity == "daily" else CostGranularity.MONTHLY
            result = get_usage_costs(
                args.subscription_id,
                timeframe=timeframe_map[args.timeframe],
                granularity=granularity
            )
        elif args.command == "forecast":
            result = get_cost_forecast(args.subscription_id, args.days)
        elif args.command == "budgets":
            result = list_budgets(args.subscription_id)
        elif args.command == "by-rg":
            result = get_cost_by_resource_group(args.subscription_id)
        elif args.command == "by-service":
            result = get_cost_by_service(args.subscription_id)
        else:
            parser.print_help()
            return 0

        print(json.dumps(result, indent=2, default=str))
        return 0

    except AzureCostError as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
