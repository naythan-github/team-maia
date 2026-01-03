# Azure Portal Tools

Python tools for accessing Azure Portal APIs with TDD-verified implementations.

## Installation

```bash
pip install -r requirements.txt
```

Required packages:
- azure-identity
- azure-mgmt-resource
- azure-mgmt-costmanagement
- azure-mgmt-monitor
- azure-monitor-query
- azure-mgmt-alertsmanagement

## Tools

### 1. Azure Authentication (`azure_auth.py`)

Handles Azure credential management with multiple auth methods.

```python
from claude.tools.experimental.azure.azure_auth import (
    AzureAuthManager,
    AuthMethod,
    get_default_credential,
    authenticate_with_service_principal
)

# Default credential (uses environment or Azure CLI)
cred = get_default_credential()

# Service principal authentication
cred = authenticate_with_service_principal(
    tenant_id="your-tenant-id",
    client_id="your-client-id",
    client_secret="your-secret"
)

# Auth manager with caching
manager = AzureAuthManager(method=AuthMethod.DEFAULT)
token = manager.get_token("https://management.azure.com/.default")
```

### 2. Azure Resources (`azure_resources.py`)

List and manage Azure subscriptions, resource groups, and resources.

```python
from claude.tools.experimental.azure.azure_resources import (
    list_subscriptions,
    list_resource_groups,
    list_resources,
    get_resource,
    ResourceFilter
)

# List subscriptions
subs = list_subscriptions(enabled_only=True)

# List resource groups
rgs = list_resource_groups("subscription-id", tag_filter={"env": "prod"})

# List resources with filtering
resources = list_resources(
    "subscription-id",
    resource_group="rg-prod",
    resource_type="Microsoft.Compute/virtualMachines"
)

# Get specific resource
vm = get_resource("/subscriptions/.../virtualMachines/vm-1")
```

### 3. Azure Costs (`azure_costs.py`)

Query costs, forecasts, and budgets.

```python
from claude.tools.experimental.azure.azure_costs import (
    get_usage_costs,
    get_cost_forecast,
    list_budgets,
    get_cost_by_resource_group,
    get_cost_by_service,
    CostTimeframe,
    CostGranularity
)

# Usage costs for last 30 days
costs = get_usage_costs(
    subscription_id="sub-id",
    timeframe=CostTimeframe.LAST_30_DAYS,
    granularity=CostGranularity.DAILY
)

# Custom date range
costs = get_usage_costs(
    subscription_id="sub-id",
    start_date="2024-01-01",
    end_date="2024-01-31"
)

# Cost forecast
forecast = get_cost_forecast(subscription_id="sub-id", forecast_days=30)

# Budgets
budgets = list_budgets(subscription_id="sub-id")

# Cost breakdown
by_rg = get_cost_by_resource_group(subscription_id="sub-id")
by_svc = get_cost_by_service(subscription_id="sub-id")
```

### 4. Azure Monitor (`azure_monitor.py`)

Query metrics, logs, and alerts.

```python
from claude.tools.experimental.azure.azure_monitor import (
    query_metrics,
    query_logs,
    list_alerts,
    get_metric_definitions,
    MetricAggregation,
    MetricTimespan
)

# Query CPU metrics
metrics = query_metrics(
    resource_id="/subscriptions/.../virtualMachines/vm-1",
    metric_name="Percentage CPU",
    aggregation=MetricAggregation.AVERAGE,
    timespan=MetricTimespan.LAST_HOUR
)

# Available metrics for a resource
definitions = get_metric_definitions(resource_id="/subscriptions/.../...")

# Log Analytics (Kusto) query
logs = query_logs(
    workspace_id="workspace-id",
    query="Heartbeat | summarize count() by Computer",
    subscription_id="sub-id"
)

# List alerts
alerts = list_alerts(
    subscription_id="sub-id",
    severity_filter=["Sev0", "Sev1"],
    fired_only=True
)
```

## CLI Usage

Each tool has a CLI interface:

```bash
# Authentication
python -m claude.tools.experimental.azure.azure_auth check

# Resources
python -m claude.tools.experimental.azure.azure_resources \
    subscriptions --enabled-only

python -m claude.tools.experimental.azure.azure_resources \
    --subscription-id sub-1 resource-groups

# Costs
python -m claude.tools.experimental.azure.azure_costs \
    --subscription-id sub-1 usage --timeframe 30d

python -m claude.tools.experimental.azure.azure_costs \
    --subscription-id sub-1 forecast --days 30

python -m claude.tools.experimental.azure.azure_costs \
    --subscription-id sub-1 by-service

# Monitor
python -m claude.tools.experimental.azure.azure_monitor \
    --subscription-id sub-1 metrics \
    --resource-id /subscriptions/.../vm-1 \
    --metric "Percentage CPU" --timespan 1h

python -m claude.tools.experimental.azure.azure_monitor \
    --subscription-id sub-1 alerts --fired-only
```

## Environment Variables

```bash
# Service principal auth
export AZURE_TENANT_ID="your-tenant-id"
export AZURE_CLIENT_ID="your-client-id"
export AZURE_CLIENT_SECRET="your-secret"

# Or use Azure CLI: az login
```

## Testing

```bash
# Run all tests
python -m pytest claude/tools/experimental/azure/tests/ -v

# Run specific test file
python -m pytest claude/tools/experimental/azure/tests/test_azure_costs.py -v

# Run with coverage
python -m pytest claude/tools/experimental/azure/tests/ --cov=claude.tools.experimental.azure
```

## SDK Notes

- **CostTimeframe**: Uses SDK enum values (WeekToDate, TheLastMonth, BillingMonthToDate)
- **CostGranularity**: SDK only supports DAILY granularity; aggregated queries omit this parameter
- **Lazy imports**: Optional SDK dependencies are loaded on first use for better startup time

## Test Results

All 68 tests passing (TDD methodology):
- Authentication: 16 tests
- Resources: 14 tests
- Costs: 16 tests
- Monitor: 22 tests
