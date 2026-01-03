"""
TDD Tests for Azure Resource Management Tool
Tests written BEFORE implementation per TDD protocol.

Test Categories:
1. Subscription operations
2. Resource group operations
3. Resource operations
4. Error handling
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict
import json

try:
    from claude.tools.experimental.azure.azure_resources import (
        AzureResourceManager,
        list_subscriptions,
        list_resource_groups,
        list_resources,
        get_resource,
        ResourceFilter,
        AzureResourceError,
    )
    IMPLEMENTATION_EXISTS = True
except ImportError:
    IMPLEMENTATION_EXISTS = False


pytestmark = pytest.mark.skipif(
    not IMPLEMENTATION_EXISTS,
    reason="Implementation not yet created - TDD red phase"
)


class TestAzureResourceManager:
    """Test the main resource manager class."""

    def test_init_with_credential(self):
        """Should initialize with provided credential."""
        mock_cred = Mock()
        with patch('azure.mgmt.resource.SubscriptionClient') as mock_sub_client:
            manager = AzureResourceManager(credential=mock_cred)
            assert manager.credential == mock_cred
            mock_sub_client.assert_called_once_with(mock_cred)

    def test_init_creates_default_credential(self):
        """Should create default credential when none provided."""
        with patch('azure.identity.DefaultAzureCredential') as mock_cred_class:
            with patch('azure.mgmt.resource.SubscriptionClient'):
                manager = AzureResourceManager()
                mock_cred_class.assert_called_once()


class TestSubscriptionOperations:
    """Test subscription listing and management."""

    def test_list_subscriptions_returns_all(self):
        """Should return list of all accessible subscriptions."""
        mock_subs = [
            Mock(subscription_id="sub-1", display_name="Subscription 1", state="Enabled"),
            Mock(subscription_id="sub-2", display_name="Subscription 2", state="Enabled"),
        ]

        with patch('azure.mgmt.resource.SubscriptionClient') as mock_client_class:
            mock_client = Mock()
            mock_client.subscriptions.list.return_value = mock_subs
            mock_client_class.return_value = mock_client

            with patch('azure.identity.DefaultAzureCredential'):
                result = list_subscriptions()

            assert len(result) == 2
            assert result[0]["subscription_id"] == "sub-1"
            assert result[1]["display_name"] == "Subscription 2"

    def test_list_subscriptions_includes_state(self):
        """Should include subscription state in results."""
        mock_subs = [
            Mock(subscription_id="sub-1", display_name="Sub1", state="Enabled"),
            Mock(subscription_id="sub-2", display_name="Sub2", state="Disabled"),
        ]

        with patch('azure.mgmt.resource.SubscriptionClient') as mock_client_class:
            mock_client = Mock()
            mock_client.subscriptions.list.return_value = mock_subs
            mock_client_class.return_value = mock_client

            with patch('azure.identity.DefaultAzureCredential'):
                result = list_subscriptions()

            assert result[0]["state"] == "Enabled"
            assert result[1]["state"] == "Disabled"

    def test_list_subscriptions_filters_enabled_only(self):
        """Should filter to only enabled subscriptions when requested."""
        mock_subs = [
            Mock(subscription_id="sub-1", display_name="Sub1", state="Enabled"),
            Mock(subscription_id="sub-2", display_name="Sub2", state="Disabled"),
        ]

        with patch('azure.mgmt.resource.SubscriptionClient') as mock_client_class:
            mock_client = Mock()
            mock_client.subscriptions.list.return_value = mock_subs
            mock_client_class.return_value = mock_client

            with patch('azure.identity.DefaultAzureCredential'):
                result = list_subscriptions(enabled_only=True)

            assert len(result) == 1
            assert result[0]["state"] == "Enabled"


class TestResourceGroupOperations:
    """Test resource group operations."""

    def test_list_resource_groups_for_subscription(self):
        """Should list all resource groups in a subscription."""
        # Note: Mock(name=...) uses 'name' as the mock's name, not an attribute
        # So we create mocks and set attributes separately
        rg1 = Mock()
        rg1.name = "rg-1"
        rg1.location = "eastus"
        rg1.tags = {"env": "prod"}

        rg2 = Mock()
        rg2.name = "rg-2"
        rg2.location = "westus"
        rg2.tags = None

        mock_rgs = [rg1, rg2]

        with patch('azure.mgmt.resource.ResourceManagementClient') as mock_client_class:
            mock_client = Mock()
            mock_client.resource_groups.list.return_value = mock_rgs
            mock_client_class.return_value = mock_client

            with patch('azure.identity.DefaultAzureCredential'):
                result = list_resource_groups("sub-1")

            assert len(result) == 2
            assert result[0]["name"] == "rg-1"
            assert result[0]["location"] == "eastus"
            assert result[1]["tags"] is None

    def test_list_resource_groups_with_tag_filter(self):
        """Should filter resource groups by tags."""
        rg_prod = Mock()
        rg_prod.name = "rg-prod"
        rg_prod.location = "eastus"
        rg_prod.tags = {"env": "prod"}

        rg_dev = Mock()
        rg_dev.name = "rg-dev"
        rg_dev.location = "westus"
        rg_dev.tags = {"env": "dev"}

        mock_rgs = [rg_prod, rg_dev]

        with patch('azure.mgmt.resource.ResourceManagementClient') as mock_client_class:
            mock_client = Mock()
            mock_client.resource_groups.list.return_value = mock_rgs
            mock_client_class.return_value = mock_client

            with patch('azure.identity.DefaultAzureCredential'):
                result = list_resource_groups("sub-1", tag_filter={"env": "prod"})

            assert len(result) == 1
            assert result[0]["name"] == "rg-prod"

    def test_list_resource_groups_handles_empty(self):
        """Should return empty list when no resource groups exist."""
        with patch('azure.mgmt.resource.ResourceManagementClient') as mock_client_class:
            mock_client = Mock()
            mock_client.resource_groups.list.return_value = []
            mock_client_class.return_value = mock_client

            with patch('azure.identity.DefaultAzureCredential'):
                result = list_resource_groups("sub-1")

            assert result == []


class TestResourceOperations:
    """Test individual resource operations."""

    def test_list_resources_in_subscription(self):
        """Should list all resources in a subscription."""
        vm1 = Mock()
        vm1.id = "/subscriptions/sub-1/resourceGroups/rg-1/providers/Microsoft.Compute/virtualMachines/vm-1"
        vm1.name = "vm-1"
        vm1.type = "Microsoft.Compute/virtualMachines"
        vm1.location = "eastus"
        vm1.tags = {"env": "prod"}

        storage1 = Mock()
        storage1.id = "/subscriptions/sub-1/resourceGroups/rg-1/providers/Microsoft.Storage/storageAccounts/storage1"
        storage1.name = "storage1"
        storage1.type = "Microsoft.Storage/storageAccounts"
        storage1.location = "eastus"
        storage1.tags = None

        mock_resources = [vm1, storage1]

        with patch('azure.mgmt.resource.ResourceManagementClient') as mock_client_class:
            mock_client = Mock()
            mock_client.resources.list.return_value = mock_resources
            mock_client_class.return_value = mock_client

            with patch('azure.identity.DefaultAzureCredential'):
                result = list_resources("sub-1")

            assert len(result) == 2
            assert result[0]["name"] == "vm-1"
            assert result[0]["type"] == "Microsoft.Compute/virtualMachines"

    def test_list_resources_with_type_filter(self):
        """Should filter resources by type."""
        vm1 = Mock()
        vm1.id = "/sub/rg/Microsoft.Compute/virtualMachines/vm-1"
        vm1.name = "vm-1"
        vm1.type = "Microsoft.Compute/virtualMachines"
        vm1.location = "eastus"
        vm1.tags = None

        mock_resources = [vm1]

        with patch('azure.mgmt.resource.ResourceManagementClient') as mock_client_class:
            mock_client = Mock()
            mock_client.resources.list.return_value = mock_resources
            mock_client_class.return_value = mock_client

            with patch('azure.identity.DefaultAzureCredential'):
                result = list_resources(
                    "sub-1",
                    resource_type="Microsoft.Compute/virtualMachines"
                )

            assert len(result) == 1
            assert result[0]["type"] == "Microsoft.Compute/virtualMachines"

    def test_list_resources_in_resource_group(self):
        """Should list resources in a specific resource group."""
        vm1 = Mock()
        vm1.id = "/sub/rg-1/Microsoft.Compute/virtualMachines/vm-1"
        vm1.name = "vm-1"
        vm1.type = "Microsoft.Compute/virtualMachines"
        vm1.location = "eastus"
        vm1.tags = None

        mock_resources = [vm1]

        with patch('azure.mgmt.resource.ResourceManagementClient') as mock_client_class:
            mock_client = Mock()
            mock_client.resources.list_by_resource_group.return_value = mock_resources
            mock_client_class.return_value = mock_client

            with patch('azure.identity.DefaultAzureCredential'):
                result = list_resources("sub-1", resource_group="rg-1")

            assert len(result) == 1
            mock_client.resources.list_by_resource_group.assert_called_once_with("rg-1")

    def test_get_resource_by_id(self):
        """Should retrieve a specific resource by ID."""
        mock_resource = Mock()
        mock_resource.id = "/subscriptions/sub-1/resourceGroups/rg-1/providers/Microsoft.Compute/virtualMachines/vm-1"
        mock_resource.name = "vm-1"
        mock_resource.type = "Microsoft.Compute/virtualMachines"
        mock_resource.location = "eastus"
        mock_resource.properties = {"vmSize": "Standard_DS2_v2"}
        mock_resource.tags = {"env": "prod"}

        with patch('azure.mgmt.resource.ResourceManagementClient') as mock_client_class:
            mock_client = Mock()
            mock_client.resources.get_by_id.return_value = mock_resource
            mock_client_class.return_value = mock_client

            with patch('azure.identity.DefaultAzureCredential'):
                result = get_resource(
                    "/subscriptions/sub-1/resourceGroups/rg-1/providers/Microsoft.Compute/virtualMachines/vm-1"
                )

            assert result["name"] == "vm-1"
            assert result["properties"]["vmSize"] == "Standard_DS2_v2"


class TestResourceFilter:
    """Test resource filtering functionality."""

    def test_filter_by_location(self):
        """Should filter resources by location."""
        resource_filter = ResourceFilter(location="eastus")

        resources = [
            {"name": "vm-1", "location": "eastus"},
            {"name": "vm-2", "location": "westus"},
        ]

        filtered = resource_filter.apply(resources)
        assert len(filtered) == 1
        assert filtered[0]["name"] == "vm-1"

    def test_filter_by_multiple_criteria(self):
        """Should filter by multiple criteria."""
        resource_filter = ResourceFilter(
            location="eastus",
            resource_type="Microsoft.Compute/virtualMachines"
        )

        resources = [
            {"name": "vm-1", "location": "eastus", "type": "Microsoft.Compute/virtualMachines"},
            {"name": "storage-1", "location": "eastus", "type": "Microsoft.Storage/storageAccounts"},
            {"name": "vm-2", "location": "westus", "type": "Microsoft.Compute/virtualMachines"},
        ]

        filtered = resource_filter.apply(resources)
        assert len(filtered) == 1
        assert filtered[0]["name"] == "vm-1"


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_invalid_subscription_raises_error(self):
        """Should raise error for invalid subscription ID."""
        with patch('azure.mgmt.resource.ResourceManagementClient') as mock_client_class:
            mock_client = Mock()
            mock_client.resource_groups.list.side_effect = Exception("Subscription not found")
            mock_client_class.return_value = mock_client

            with patch('azure.identity.DefaultAzureCredential'):
                with pytest.raises(AzureResourceError) as exc_info:
                    list_resource_groups("invalid-sub")

                assert "Subscription not found" in str(exc_info.value)

    def test_network_error_raises_resource_error(self):
        """Should wrap network errors in AzureResourceError."""
        with patch('azure.mgmt.resource.SubscriptionClient') as mock_client_class:
            mock_client = Mock()
            mock_client.subscriptions.list.side_effect = ConnectionError("Network unreachable")
            mock_client_class.return_value = mock_client

            with patch('azure.identity.DefaultAzureCredential'):
                with pytest.raises(AzureResourceError) as exc_info:
                    list_subscriptions()

                assert "Network" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
