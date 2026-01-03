"""
Azure Resource Management Tool

Provides resource management operations for Azure Portal API access.
Supports:
- Subscription listing
- Resource group management
- Resource listing and filtering
- Resource details retrieval

TDD Implementation - Tests in tests/test_azure_resources.py
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class AzureResourceError(Exception):
    """Raised when Azure resource operations fail."""
    pass


@dataclass
class ResourceFilter:
    """Filter criteria for resource queries."""
    location: Optional[str] = None
    resource_type: Optional[str] = None
    tags: Optional[Dict[str, str]] = None

    def apply(self, resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply filter to a list of resources."""
        filtered = resources

        if self.location:
            filtered = [r for r in filtered if r.get("location") == self.location]

        if self.resource_type:
            filtered = [r for r in filtered if r.get("type") == self.resource_type]

        if self.tags:
            filtered = [
                r for r in filtered
                if r.get("tags") and all(
                    r["tags"].get(k) == v for k, v in self.tags.items()
                )
            ]

        return filtered


class AzureResourceManager:
    """
    Manages Azure resource operations.

    Usage:
        manager = AzureResourceManager(credential=credential)
        subscriptions = manager.list_subscriptions()
        resources = manager.list_resources("sub-id")
    """

    def __init__(
        self,
        credential: Optional[Any] = None,
        subscription_id: Optional[str] = None
    ):
        """
        Initialize Azure resource manager.

        Args:
            credential: Azure credential object
            subscription_id: Default subscription ID for operations
        """
        self.subscription_id = subscription_id

        # Create default credential if not provided
        if credential is None:
            try:
                from azure.identity import DefaultAzureCredential
                credential = DefaultAzureCredential()
            except ImportError as e:
                raise AzureResourceError(
                    "Azure SDK not installed. Run: pip install azure-identity azure-mgmt-resource"
                ) from e

        self.credential = credential

        # Initialize subscription client
        try:
            from azure.mgmt.resource import SubscriptionClient
            self._subscription_client = SubscriptionClient(credential)
        except ImportError as e:
            raise AzureResourceError(
                "azure-mgmt-resource not installed. Run: pip install azure-mgmt-resource"
            ) from e

    def _get_resource_client(self, subscription_id: str) -> Any:
        """Get a ResourceManagementClient for the given subscription."""
        try:
            from azure.mgmt.resource import ResourceManagementClient
            return ResourceManagementClient(self.credential, subscription_id)
        except ImportError as e:
            raise AzureResourceError(
                "azure-mgmt-resource not installed"
            ) from e

    def list_subscriptions(self, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """
        List all accessible subscriptions.

        Args:
            enabled_only: If True, only return enabled subscriptions

        Returns:
            List of subscription dictionaries
        """
        try:
            subscriptions = []
            for sub in self._subscription_client.subscriptions.list():
                sub_dict = {
                    "subscription_id": sub.subscription_id,
                    "display_name": sub.display_name,
                    "state": str(sub.state) if hasattr(sub.state, 'value') else sub.state,
                    "tenant_id": sub.tenant_id if hasattr(sub, 'tenant_id') else None
                }

                if enabled_only and sub_dict["state"] != "Enabled":
                    continue

                subscriptions.append(sub_dict)

            return subscriptions
        except Exception as e:
            raise AzureResourceError(f"Failed to list subscriptions: {e}") from e

    def list_resource_groups(
        self,
        subscription_id: Optional[str] = None,
        tag_filter: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """
        List resource groups in a subscription.

        Args:
            subscription_id: Subscription ID (uses default if not provided)
            tag_filter: Filter by tags

        Returns:
            List of resource group dictionaries
        """
        sub_id = subscription_id or self.subscription_id
        if not sub_id:
            raise ValueError("subscription_id is required")

        try:
            client = self._get_resource_client(sub_id)
            resource_groups = []

            for rg in client.resource_groups.list():
                rg_dict = {
                    "name": rg.name,
                    "location": rg.location,
                    "tags": dict(rg.tags) if rg.tags else None,
                    "provisioning_state": rg.properties.provisioning_state if hasattr(rg, 'properties') else None
                }

                # Apply tag filter
                if tag_filter:
                    if not rg_dict["tags"]:
                        continue
                    if not all(rg_dict["tags"].get(k) == v for k, v in tag_filter.items()):
                        continue

                resource_groups.append(rg_dict)

            return resource_groups
        except Exception as e:
            raise AzureResourceError(f"Failed to list resource groups: {e}") from e

    def list_resources(
        self,
        subscription_id: Optional[str] = None,
        resource_group: Optional[str] = None,
        resource_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List resources in a subscription or resource group.

        Args:
            subscription_id: Subscription ID
            resource_group: Specific resource group (optional)
            resource_type: Filter by resource type (e.g., "Microsoft.Compute/virtualMachines")

        Returns:
            List of resource dictionaries
        """
        sub_id = subscription_id or self.subscription_id
        if not sub_id:
            raise ValueError("subscription_id is required")

        try:
            client = self._get_resource_client(sub_id)
            resources = []

            # Choose list method based on scope
            if resource_group:
                resource_list = client.resources.list_by_resource_group(resource_group)
            else:
                resource_list = client.resources.list()

            for resource in resource_list:
                res_dict = {
                    "id": resource.id,
                    "name": resource.name,
                    "type": resource.type,
                    "location": resource.location,
                    "tags": dict(resource.tags) if resource.tags else None
                }

                # Apply type filter
                if resource_type and res_dict["type"] != resource_type:
                    continue

                resources.append(res_dict)

            return resources
        except Exception as e:
            raise AzureResourceError(f"Failed to list resources: {e}") from e

    def get_resource(self, resource_id: str, api_version: str = "2021-04-01") -> Dict[str, Any]:
        """
        Get a specific resource by ID.

        Args:
            resource_id: Full Azure resource ID
            api_version: API version to use

        Returns:
            Resource dictionary with full details
        """
        if not resource_id:
            raise ValueError("resource_id is required")

        try:
            # Extract subscription ID from resource ID
            parts = resource_id.split("/")
            sub_idx = parts.index("subscriptions") if "subscriptions" in parts else -1
            if sub_idx >= 0 and sub_idx + 1 < len(parts):
                sub_id = parts[sub_idx + 1]
            else:
                sub_id = self.subscription_id

            if not sub_id:
                raise ValueError("Could not determine subscription ID from resource ID")

            client = self._get_resource_client(sub_id)
            resource = client.resources.get_by_id(resource_id, api_version)

            return {
                "id": resource.id,
                "name": resource.name,
                "type": resource.type,
                "location": resource.location,
                "tags": dict(resource.tags) if resource.tags else None,
                "properties": dict(resource.properties) if hasattr(resource, 'properties') and resource.properties else None
            }
        except Exception as e:
            raise AzureResourceError(f"Failed to get resource: {e}") from e


# Standalone functions for convenience

def list_subscriptions(enabled_only: bool = False) -> List[Dict[str, Any]]:
    """List all accessible subscriptions."""
    manager = AzureResourceManager()
    return manager.list_subscriptions(enabled_only=enabled_only)


def list_resource_groups(
    subscription_id: str,
    tag_filter: Optional[Dict[str, str]] = None
) -> List[Dict[str, Any]]:
    """List resource groups in a subscription."""
    manager = AzureResourceManager(subscription_id=subscription_id)
    return manager.list_resource_groups(tag_filter=tag_filter)


def list_resources(
    subscription_id: str,
    resource_group: Optional[str] = None,
    resource_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """List resources in a subscription or resource group."""
    manager = AzureResourceManager(subscription_id=subscription_id)
    return manager.list_resources(
        resource_group=resource_group,
        resource_type=resource_type
    )


def get_resource(resource_id: str, api_version: str = "2021-04-01") -> Dict[str, Any]:
    """Get a specific resource by ID."""
    manager = AzureResourceManager()
    return manager.get_resource(resource_id, api_version)


# CLI interface
def main():
    """CLI interface for resource management."""
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Azure Resource Management Tool")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # List subscriptions
    sub_parser = subparsers.add_parser("subscriptions", help="List subscriptions")
    sub_parser.add_argument("--enabled-only", action="store_true",
                           help="Only show enabled subscriptions")

    # List resource groups
    rg_parser = subparsers.add_parser("resource-groups", help="List resource groups")
    rg_parser.add_argument("--subscription-id", required=True, help="Subscription ID")
    rg_parser.add_argument("--tag", nargs=2, action="append", metavar=("KEY", "VALUE"),
                          help="Filter by tag (can be repeated)")

    # List resources
    res_parser = subparsers.add_parser("resources", help="List resources")
    res_parser.add_argument("--subscription-id", required=True, help="Subscription ID")
    res_parser.add_argument("--resource-group", help="Resource group name")
    res_parser.add_argument("--type", dest="resource_type", help="Resource type filter")

    # Get resource
    get_parser = subparsers.add_parser("get", help="Get resource by ID")
    get_parser.add_argument("resource_id", help="Resource ID")

    args = parser.parse_args()

    try:
        if args.command == "subscriptions":
            result = list_subscriptions(enabled_only=args.enabled_only)
        elif args.command == "resource-groups":
            tag_filter = dict(args.tag) if args.tag else None
            result = list_resource_groups(args.subscription_id, tag_filter)
        elif args.command == "resources":
            result = list_resources(
                args.subscription_id,
                resource_group=args.resource_group,
                resource_type=args.resource_type
            )
        elif args.command == "get":
            result = get_resource(args.resource_id)
        else:
            parser.print_help()
            return 0

        print(json.dumps(result, indent=2, default=str))
        return 0

    except AzureResourceError as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
