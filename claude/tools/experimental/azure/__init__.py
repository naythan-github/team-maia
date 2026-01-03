# Azure Portal Tools - Experimental
# TDD Development: Tests first, implementation second
# Graduation target: claude/tools/azure/

from claude.tools.experimental.azure.azure_auth import (
    AzureAuthManager,
    AuthMethod,
    AzureAuthError,
    get_default_credential,
    authenticate_with_service_principal,
)

from claude.tools.experimental.azure.azure_resources import (
    AzureResourceManager,
    ResourceFilter,
    AzureResourceError,
    list_subscriptions,
    list_resource_groups,
    list_resources,
    get_resource,
)

from claude.tools.experimental.azure.azure_costs import (
    AzureCostManager,
    CostTimeframe,
    CostGranularity,
    AzureCostError,
    get_usage_costs,
    get_cost_forecast,
    list_budgets,
    get_cost_by_resource_group,
    get_cost_by_service,
)

from claude.tools.experimental.azure.azure_monitor import (
    AzureMonitorManager,
    MetricAggregation,
    MetricTimespan,
    AzureMonitorError,
    query_metrics,
    query_logs,
    list_alerts,
    get_metric_definitions,
)

__all__ = [
    # Auth
    "AzureAuthManager",
    "AuthMethod",
    "AzureAuthError",
    "get_default_credential",
    "authenticate_with_service_principal",
    # Resources
    "AzureResourceManager",
    "ResourceFilter",
    "AzureResourceError",
    "list_subscriptions",
    "list_resource_groups",
    "list_resources",
    "get_resource",
    # Costs
    "AzureCostManager",
    "CostTimeframe",
    "CostGranularity",
    "AzureCostError",
    "get_usage_costs",
    "get_cost_forecast",
    "list_budgets",
    "get_cost_by_resource_group",
    "get_cost_by_service",
    # Monitor
    "AzureMonitorManager",
    "MetricAggregation",
    "MetricTimespan",
    "AzureMonitorError",
    "query_metrics",
    "query_logs",
    "list_alerts",
    "get_metric_definitions",
]
