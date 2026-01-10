"""
Phase 3 TDD Tests - Azure Resource Graph Integration

Tests for Azure Resource Graph client that enables efficient Kusto queries
for cross-subscription resource inventory and Advisor recommendations.

Run with: pytest tests/test_resource_graph.py -v
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
from typing import List, Dict, Any


class TestResourceGraphClientInitialization:
    """Tests for ResourceGraphClient initialization."""

    def test_client_initialization(self):
        """
        Verify ResourceGraphClient can be initialized.
        """
        from claude.tools.experimental.azure.resource_graph import ResourceGraphClient

        client = ResourceGraphClient()
        assert client is not None

    def test_client_initialization_with_credentials(self):
        """
        Verify client can be initialized with Azure credentials.
        """
        from claude.tools.experimental.azure.resource_graph import ResourceGraphClient

        mock_credential = Mock()
        client = ResourceGraphClient(credential=mock_credential)
        assert client is not None


class TestBasicQuery:
    """Tests for basic Resource Graph query functionality."""

    def test_query_execution_success(self):
        """
        Verify Resource Graph query can be executed successfully.
        """
        from claude.tools.experimental.azure.resource_graph import ResourceGraphClient

        client = ResourceGraphClient(credential=Mock())

        # Mock query response
        mock_response = Mock()
        mock_response.data = [
            {"id": "/subscriptions/sub-1/resourceGroups/rg-1/providers/Microsoft.Compute/virtualMachines/vm-1"},
            {"id": "/subscriptions/sub-1/resourceGroups/rg-1/providers/Microsoft.Compute/virtualMachines/vm-2"},
        ]

        with patch.object(client, '_execute_query', return_value=mock_response):
            results = client.query(
                subscription_ids=["sub-1"],
                query="Resources | where type == 'microsoft.compute/virtualmachines'"
            )

            assert len(results) == 2
            assert results[0]["id"].endswith("/vm-1")

    def test_query_with_multiple_subscriptions(self):
        """
        Verify query can span multiple subscriptions.
        """
        from claude.tools.experimental.azure.resource_graph import ResourceGraphClient

        client = ResourceGraphClient(credential=Mock())

        mock_response = Mock()
        mock_response.data = [
            {"id": "/subscriptions/sub-1/resourceGroups/rg-1/providers/Microsoft.Compute/virtualMachines/vm-1"},
            {"id": "/subscriptions/sub-2/resourceGroups/rg-2/providers/Microsoft.Compute/virtualMachines/vm-2"},
        ]

        with patch.object(client, '_execute_query', return_value=mock_response):
            results = client.query(
                subscription_ids=["sub-1", "sub-2"],
                query="Resources | where type == 'microsoft.compute/virtualmachines'"
            )

            assert len(results) == 2
            # Verify results from both subscriptions
            assert "/sub-1/" in results[0]["id"]
            assert "/sub-2/" in results[1]["id"]

    def test_empty_query_results(self):
        """
        Verify empty query results are handled correctly.
        """
        from claude.tools.experimental.azure.resource_graph import ResourceGraphClient

        client = ResourceGraphClient(credential=Mock())

        mock_response = Mock()
        mock_response.data = []

        with patch.object(client, '_execute_query', return_value=mock_response):
            results = client.query(
                subscription_ids=["sub-1"],
                query="Resources | where name == 'nonexistent'"
            )

            assert len(results) == 0


class TestRateLimiting:
    """Tests for rate limiting (15 requests per 5 seconds)."""

    def test_query_uses_azure_retry_decorator(self):
        """
        Verify query method uses @azure_retry decorator with resource_graph type.
        """
        from claude.tools.experimental.azure.resource_graph import ResourceGraphClient
        import inspect

        # Check that method has retry decorator
        method = ResourceGraphClient.query
        source = inspect.getsource(ResourceGraphClient)
        assert hasattr(method, '__wrapped__') or 'azure_retry' in source

    @patch('claude.tools.experimental.azure.api_utils.time.sleep')
    def test_429_throttling_triggers_retry(self, mock_sleep):
        """
        Verify 429 Too Many Requests triggers retry with backoff.
        """
        from claude.tools.experimental.azure.resource_graph import ResourceGraphClient
        from azure.core.exceptions import HttpResponseError

        client = ResourceGraphClient(credential=Mock())

        # Create mock 429 error
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {'Retry-After': '5'}
        error_429 = HttpResponseError(response=mock_response)

        # Mock success on second attempt
        mock_success = Mock()
        mock_success.data = [{"id": "resource-1"}]

        with patch.object(client, '_execute_query') as mock_execute:
            # Fail first, succeed second
            mock_execute.side_effect = [error_429, mock_success]

            results = client.query(["sub-1"], "Resources | limit 1")

            # Should eventually succeed
            assert len(results) == 1
            # Should have attempted twice
            assert mock_execute.call_count == 2


class TestAdvisorRecommendationsViaGraph:
    """Tests for querying Advisor recommendations via Resource Graph."""

    def test_get_advisor_cost_recommendations(self):
        """
        Verify Advisor cost recommendations can be queried via Resource Graph.
        """
        from claude.tools.experimental.azure.resource_graph import ResourceGraphClient

        client = ResourceGraphClient(credential=Mock())

        # Mock Advisor recommendations from Resource Graph
        mock_response = Mock()
        mock_response.data = [
            {
                "recommendationId": "/subscriptions/sub-1/providers/Microsoft.Advisor/recommendations/rec-1",
                "resourceId": "/subscriptions/sub-1/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm-1",
                "impact": "High",
                "problem": "Underutilized VM",
                "solution": "Downsize to Standard_D2_v3",
                "savings": "150.00",
            },
            {
                "recommendationId": "/subscriptions/sub-1/providers/Microsoft.Advisor/recommendations/rec-2",
                "resourceId": "/subscriptions/sub-1/resourceGroups/rg/providers/Microsoft.Storage/storageAccounts/stor1",
                "impact": "Medium",
                "problem": "Unused storage account",
                "solution": "Delete unused storage",
                "savings": "25.00",
            },
        ]

        with patch.object(client, 'query', return_value=mock_response.data):
            recommendations = client.get_advisor_cost_recommendations(["sub-1"])

            assert len(recommendations) == 2
            assert recommendations[0]["impact"] == "High"
            assert recommendations[0]["savings"] == "150.00"

    def test_advisor_query_filters_cost_category(self):
        """
        Verify query filters for Cost category recommendations only.
        """
        from claude.tools.experimental.azure.resource_graph import ResourceGraphClient

        client = ResourceGraphClient(credential=Mock())

        with patch.object(client, 'query') as mock_query:
            mock_query.return_value = []

            client.get_advisor_cost_recommendations(["sub-1"])

            # Verify query was called
            assert mock_query.called
            # Verify query contains Cost category filter
            called_query = mock_query.call_args[0][1]
            assert "category == 'Cost'" in called_query or "category == \"Cost\"" in called_query

    def test_advisor_recommendations_cross_subscription(self):
        """
        Verify Advisor recommendations can be queried across multiple subscriptions.
        """
        from claude.tools.experimental.azure.resource_graph import ResourceGraphClient

        client = ResourceGraphClient(credential=Mock())

        mock_data = [
            {"recommendationId": "rec-1", "resourceId": "/subscriptions/sub-1/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm-1"},
            {"recommendationId": "rec-2", "resourceId": "/subscriptions/sub-2/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm-2"},
        ]

        with patch.object(client, 'query', return_value=mock_data):
            recommendations = client.get_advisor_cost_recommendations(["sub-1", "sub-2"])

            # Should return recommendations from both subscriptions
            assert len(recommendations) == 2


class TestResourceInventory:
    """Tests for resource inventory queries."""

    def test_get_unattached_disks(self):
        """
        Verify unattached disks can be queried via Resource Graph.
        """
        from claude.tools.experimental.azure.resource_graph import ResourceGraphClient

        client = ResourceGraphClient(credential=Mock())

        mock_data = [
            {
                "id": "/subscriptions/sub-1/resourceGroups/rg/providers/Microsoft.Compute/disks/disk-1",
                "name": "orphaned-disk-1",
                "sku": "Premium_LRS",
                "diskSizeGB": 128,
                "diskState": "Unattached",
            },
            {
                "id": "/subscriptions/sub-1/resourceGroups/rg/providers/Microsoft.Compute/disks/disk-2",
                "name": "orphaned-disk-2",
                "sku": "Standard_LRS",
                "diskSizeGB": 256,
                "diskState": "Unattached",
            },
        ]

        with patch.object(client, 'query', return_value=mock_data):
            disks = client.get_unattached_disks(["sub-1"])

            assert len(disks) == 2
            assert disks[0]["diskState"] == "Unattached"
            assert disks[0]["diskSizeGB"] == 128

    def test_get_orphaned_nics(self):
        """
        Verify orphaned NICs can be queried via Resource Graph.
        """
        from claude.tools.experimental.azure.resource_graph import ResourceGraphClient

        client = ResourceGraphClient(credential=Mock())

        mock_data = [
            {
                "id": "/subscriptions/sub-1/resourceGroups/rg/providers/Microsoft.Network/networkInterfaces/nic-1",
                "name": "orphaned-nic-1",
                "properties": {"virtualMachine": None},  # Not attached
            },
        ]

        with patch.object(client, 'query', return_value=mock_data):
            nics = client.get_orphaned_nics(["sub-1"])

            assert len(nics) == 1
            assert nics[0]["properties"]["virtualMachine"] is None

    def test_get_unassociated_public_ips(self):
        """
        Verify unassociated public IPs can be queried via Resource Graph.
        """
        from claude.tools.experimental.azure.resource_graph import ResourceGraphClient

        client = ResourceGraphClient(credential=Mock())

        mock_data = [
            {
                "id": "/subscriptions/sub-1/resourceGroups/rg/providers/Microsoft.Network/publicIPAddresses/ip-1",
                "name": "orphaned-ip-1",
                "properties": {
                    "ipConfiguration": None,  # Not associated
                    "ipAddress": "1.2.3.4",
                },
            },
        ]

        with patch.object(client, 'query', return_value=mock_data):
            ips = client.get_unassociated_public_ips(["sub-1"])

            assert len(ips) == 1
            assert ips[0]["properties"]["ipConfiguration"] is None


class TestQueryValidation:
    """Tests for query input validation."""

    def test_empty_subscription_list_raises_error(self):
        """
        Verify empty subscription list raises ValueError.
        """
        from claude.tools.experimental.azure.resource_graph import ResourceGraphClient

        client = ResourceGraphClient(credential=Mock())

        with pytest.raises(ValueError, match="At least one subscription"):
            client.query(subscription_ids=[], query="Resources | limit 1")

    def test_none_subscription_list_raises_error(self):
        """
        Verify None subscription list raises ValueError.
        """
        from claude.tools.experimental.azure.resource_graph import ResourceGraphClient

        client = ResourceGraphClient(credential=Mock())

        with pytest.raises(ValueError, match="At least one subscription"):
            client.query(subscription_ids=None, query="Resources | limit 1")

    def test_empty_query_raises_error(self):
        """
        Verify empty query string raises ValueError.
        """
        from claude.tools.experimental.azure.resource_graph import ResourceGraphClient

        client = ResourceGraphClient(credential=Mock())

        with pytest.raises(ValueError, match="Query cannot be empty"):
            client.query(subscription_ids=["sub-1"], query="")


class TestIntegrationWithCustomerDatabase:
    """Tests for integration with CustomerDatabaseManager."""

    def test_sync_resources_to_customer_db(self):
        """
        Verify resources can be synced to correct customer database.
        """
        from claude.tools.experimental.azure.resource_graph import ResourceGraphClient

        client = ResourceGraphClient(credential=Mock())

        mock_resources = [
            {"id": "resource-1", "type": "Microsoft.Compute/virtualMachines"},
            {"id": "resource-2", "type": "Microsoft.Storage/storageAccounts"},
        ]

        with patch.object(client, 'query', return_value=mock_resources):
            with patch('claude.tools.experimental.azure.resource_graph.CustomerDatabaseManager') as mock_mgr_class:
                mock_mgr = Mock()
                mock_mgr.validate_subscription_ownership.return_value = True
                mock_db = Mock()
                mock_mgr.get_customer_db.return_value.__enter__ = Mock(return_value=mock_db)
                mock_mgr.get_customer_db.return_value.__exit__ = Mock(return_value=None)
                mock_mgr_class.return_value = mock_mgr

                count = client.sync_resources_to_database(
                    customer_slug="customer_a",
                    subscription_ids=["sub-1"],
                )

                # Should sync both resources
                assert count == 2
                assert mock_db.store_resource.call_count == 2

    def test_sync_validates_subscription_ownership(self):
        """
        Verify subscription ownership is validated before sync.
        """
        from claude.tools.experimental.azure.resource_graph import ResourceGraphClient

        client = ResourceGraphClient(credential=Mock())

        with patch('claude.tools.experimental.azure.resource_graph.CustomerDatabaseManager') as mock_mgr_class:
            mock_mgr = Mock()
            # Return False for first subscription, True for second
            mock_mgr.validate_subscription_ownership.side_effect = [False, True]
            mock_mgr_class.return_value = mock_mgr

            with pytest.raises(ValueError, match="Subscription.*does not belong"):
                client.sync_resources_to_database(
                    customer_slug="customer_a",
                    subscription_ids=["invalid-sub", "valid-sub"],
                )
