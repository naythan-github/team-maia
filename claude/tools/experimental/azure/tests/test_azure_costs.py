"""
TDD Tests for Azure Cost Management Tool
Tests written BEFORE implementation per TDD protocol.

Test Categories:
1. Cost queries (usage, forecasts)
2. Budget operations
3. Cost analysis
4. Error handling
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from typing import List, Dict
import json

try:
    from claude.tools.experimental.azure.azure_costs import (
        AzureCostManager,
        get_usage_costs,
        get_cost_forecast,
        list_budgets,
        get_cost_by_resource_group,
        get_cost_by_service,
        CostTimeframe,
        CostGranularity,
        AzureCostError,
    )
    IMPLEMENTATION_EXISTS = True
except ImportError:
    IMPLEMENTATION_EXISTS = False


pytestmark = pytest.mark.skipif(
    not IMPLEMENTATION_EXISTS,
    reason="Implementation not yet created - TDD red phase"
)


class TestAzureCostManager:
    """Test the main cost manager class."""

    def test_init_with_credential(self):
        """Should initialize with provided credential."""
        mock_cred = Mock()
        with patch('azure.mgmt.costmanagement.CostManagementClient') as mock_client:
            manager = AzureCostManager(credential=mock_cred, subscription_id="sub-1")
            assert manager.subscription_id == "sub-1"
            mock_client.assert_called_once()

    def test_init_requires_subscription_id(self):
        """Should require subscription_id for initialization."""
        with pytest.raises(ValueError) as exc_info:
            AzureCostManager(credential=Mock(), subscription_id=None)
        assert "subscription_id" in str(exc_info.value).lower()


class TestCostQueries:
    """Test cost query operations."""

    def test_get_usage_costs_last_30_days(self):
        """Should return usage costs for the last 30 days."""
        mock_result = Mock()
        mock_result.rows = [
            ["2024-01-01", 100.50, "USD"],
            ["2024-01-02", 125.75, "USD"],
        ]
        mock_result.columns = [
            Mock(name="UsageDate"),
            Mock(name="Cost"),
            Mock(name="Currency"),
        ]

        with patch('azure.mgmt.costmanagement.CostManagementClient') as mock_client_class:
            mock_client = Mock()
            mock_client.query.usage.return_value = mock_result
            mock_client_class.return_value = mock_client

            with patch('azure.identity.DefaultAzureCredential'):
                result = get_usage_costs(
                    subscription_id="sub-1",
                    timeframe=CostTimeframe.LAST_30_DAYS
                )

            assert len(result["data"]) == 2
            assert result["data"][0]["cost"] == 100.50
            assert result["total_cost"] == 226.25

    def test_get_usage_costs_custom_date_range(self):
        """Should support custom date ranges."""
        mock_result = Mock()
        mock_result.rows = [["2024-01-15", 50.00, "USD"]]
        mock_result.columns = [
            Mock(name="UsageDate"),
            Mock(name="Cost"),
            Mock(name="Currency"),
        ]

        with patch('azure.mgmt.costmanagement.CostManagementClient') as mock_client_class:
            mock_client = Mock()
            mock_client.query.usage.return_value = mock_result
            mock_client_class.return_value = mock_client

            with patch('azure.identity.DefaultAzureCredential'):
                result = get_usage_costs(
                    subscription_id="sub-1",
                    start_date="2024-01-01",
                    end_date="2024-01-31"
                )

            assert len(result["data"]) == 1

    def test_get_usage_costs_with_granularity(self):
        """Should support daily granularity (SDK only supports Daily)."""
        mock_result = Mock()
        mock_result.rows = [["2024-01-01", 100.00, "USD"]]
        mock_result.columns = [
            Mock(name="UsageDate"),
            Mock(name="Cost"),
            Mock(name="Currency"),
        ]

        with patch('azure.mgmt.costmanagement.CostManagementClient') as mock_client_class:
            mock_client = Mock()
            mock_client.query.usage.return_value = mock_result
            mock_client_class.return_value = mock_client

            with patch('azure.identity.DefaultAzureCredential'):
                result = get_usage_costs(
                    subscription_id="sub-1",
                    granularity=CostGranularity.DAILY
                )

            assert result["granularity"] == "Daily"


class TestCostForecast:
    """Test cost forecasting functionality."""

    def test_get_cost_forecast_returns_prediction(self):
        """Should return cost forecast for specified period."""
        mock_result = Mock()
        mock_result.rows = [
            ["2024-02-01", 100.00, 90.00, 110.00, "USD"],
            ["2024-02-02", 105.00, 95.00, 115.00, "USD"],
        ]
        mock_result.columns = [
            Mock(name="UsageDate"),
            Mock(name="Cost"),
            Mock(name="CostLow"),
            Mock(name="CostHigh"),
            Mock(name="Currency"),
        ]

        with patch('azure.mgmt.costmanagement.CostManagementClient') as mock_client_class:
            mock_client = Mock()
            mock_client.forecast.usage.return_value = mock_result
            mock_client_class.return_value = mock_client

            with patch('azure.identity.DefaultAzureCredential'):
                result = get_cost_forecast(
                    subscription_id="sub-1",
                    forecast_days=30
                )

            assert "forecast" in result
            assert len(result["forecast"]) == 2
            assert result["forecast"][0]["predicted_cost"] == 100.00
            assert result["forecast"][0]["confidence_low"] == 90.00
            assert result["forecast"][0]["confidence_high"] == 110.00


class TestCostBreakdown:
    """Test cost breakdown by different dimensions."""

    def test_get_cost_by_resource_group(self):
        """Should return costs grouped by resource group."""
        mock_result = Mock()
        mock_result.rows = [
            ["rg-prod", 500.00, "USD"],
            ["rg-dev", 150.00, "USD"],
        ]
        mock_result.columns = [
            Mock(name="ResourceGroup"),
            Mock(name="Cost"),
            Mock(name="Currency"),
        ]

        with patch('azure.mgmt.costmanagement.CostManagementClient') as mock_client_class:
            mock_client = Mock()
            mock_client.query.usage.return_value = mock_result
            mock_client_class.return_value = mock_client

            with patch('azure.identity.DefaultAzureCredential'):
                result = get_cost_by_resource_group(subscription_id="sub-1")

            assert len(result["breakdown"]) == 2
            assert result["breakdown"][0]["resource_group"] == "rg-prod"
            assert result["breakdown"][0]["cost"] == 500.00

    def test_get_cost_by_service(self):
        """Should return costs grouped by service type."""
        mock_result = Mock()
        mock_result.rows = [
            ["Virtual Machines", 800.00, "USD"],
            ["Storage", 200.00, "USD"],
            ["Networking", 100.00, "USD"],
        ]
        mock_result.columns = [
            Mock(name="ServiceName"),
            Mock(name="Cost"),
            Mock(name="Currency"),
        ]

        with patch('azure.mgmt.costmanagement.CostManagementClient') as mock_client_class:
            mock_client = Mock()
            mock_client.query.usage.return_value = mock_result
            mock_client_class.return_value = mock_client

            with patch('azure.identity.DefaultAzureCredential'):
                result = get_cost_by_service(subscription_id="sub-1")

            assert len(result["breakdown"]) == 3
            assert result["breakdown"][0]["service"] == "Virtual Machines"
            assert result["total_cost"] == 1100.00


class TestBudgetOperations:
    """Test budget management operations."""

    def test_list_budgets_returns_all(self):
        """Should list all budgets for a subscription."""
        budget = Mock()
        budget.name = "monthly-budget"
        budget.amount = 5000.00
        budget.time_grain = "Monthly"
        budget.current_spend = Mock(amount=3500.00)
        budget.time_period = Mock(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31)
        )
        budget.notifications = None  # Explicitly set to None

        mock_budgets = [budget]

        with patch('azure.mgmt.costmanagement.CostManagementClient') as mock_client_class:
            mock_client = Mock()
            mock_client.budgets.list.return_value = mock_budgets
            mock_client_class.return_value = mock_client

            with patch('azure.identity.DefaultAzureCredential'):
                result = list_budgets(subscription_id="sub-1")

            assert len(result) == 1
            assert result[0]["name"] == "monthly-budget"
            assert result[0]["amount"] == 5000.00
            assert result[0]["current_spend"] == 3500.00

    def test_list_budgets_includes_alerts(self):
        """Should include budget alerts in response."""
        mock_budgets = [
            Mock(
                name="budget-with-alerts",
                amount=5000.00,
                time_grain="Monthly",
                current_spend=Mock(amount=4500.00),
                time_period=Mock(
                    start_date=datetime(2024, 1, 1),
                    end_date=datetime(2024, 12, 31)
                ),
                notifications={
                    "90_percent": Mock(
                        threshold=90,
                        operator="GreaterThan",
                        enabled=True
                    )
                }
            ),
        ]

        with patch('azure.mgmt.costmanagement.CostManagementClient') as mock_client_class:
            mock_client = Mock()
            mock_client.budgets.list.return_value = mock_budgets
            mock_client_class.return_value = mock_client

            with patch('azure.identity.DefaultAzureCredential'):
                result = list_budgets(subscription_id="sub-1")

            assert result[0]["percent_used"] == 90.0
            assert "alerts" in result[0]


class TestCostTimeframes:
    """Test cost timeframe enums."""

    def test_timeframe_last_7_days(self):
        """Should support week-to-date timeframe (SDK equivalent of 7 days)."""
        assert CostTimeframe.LAST_7_DAYS.value == "WeekToDate"

    def test_timeframe_last_30_days(self):
        """Should support 30-day timeframe."""
        assert CostTimeframe.LAST_30_DAYS.value == "TheLastMonth"

    def test_timeframe_billing_month(self):
        """Should support billing month timeframe."""
        assert CostTimeframe.BILLING_MONTH.value == "BillingMonthToDate"


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_invalid_subscription_raises_error(self):
        """Should raise error for invalid subscription."""
        with patch('azure.mgmt.costmanagement.CostManagementClient') as mock_client_class:
            mock_client = Mock()
            mock_client.query.usage.side_effect = Exception("Subscription not found")
            mock_client_class.return_value = mock_client

            with patch('azure.identity.DefaultAzureCredential'):
                with pytest.raises(AzureCostError) as exc_info:
                    get_usage_costs(subscription_id="invalid-sub")

                assert "Subscription not found" in str(exc_info.value)

    def test_invalid_date_range_raises_error(self):
        """Should raise error for invalid date range."""
        with pytest.raises(ValueError) as exc_info:
            get_usage_costs(
                subscription_id="sub-1",
                start_date="2024-12-31",
                end_date="2024-01-01"  # End before start
            )
        assert "date" in str(exc_info.value).lower()

    def test_missing_cost_data_returns_empty(self):
        """Should return empty results when no cost data available."""
        mock_result = Mock()
        mock_result.rows = []
        mock_result.columns = []

        with patch('azure.mgmt.costmanagement.CostManagementClient') as mock_client_class:
            mock_client = Mock()
            mock_client.query.usage.return_value = mock_result
            mock_client_class.return_value = mock_client

            with patch('azure.identity.DefaultAzureCredential'):
                result = get_usage_costs(subscription_id="sub-1")

            assert result["data"] == []
            assert result["total_cost"] == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
