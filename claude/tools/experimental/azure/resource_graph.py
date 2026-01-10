"""
Azure Resource Graph Integration

Enables efficient resource inventory and Advisor queries via Kusto.
More efficient than individual API calls for cross-subscription queries.

Key Features:
- Rate limiting: 15 requests per 5 seconds per tenant
- Cross-subscription queries with single API call
- Kusto query language support
- Advisor recommendations via Resource Graph

TDD Implementation - Tests in tests/test_resource_graph.py
"""

import logging
from typing import List, Dict, Any, Optional
from azure.mgmt.resourcegraph import ResourceGraphClient as AzureResourceGraphClient
from azure.mgmt.resourcegraph.models import QueryRequest
from azure.core.credentials import TokenCredential
from azure.core.exceptions import HttpResponseError

from claude.tools.experimental.azure.api_utils import azure_retry
from claude.tools.experimental.azure.customer_database import CustomerDatabaseManager

logger = logging.getLogger(__name__)


class ResourceGraphClient:
    """
    Client for Azure Resource Graph (Kusto queries).

    Provides efficient cross-subscription resource queries and
    Advisor recommendation retrieval.

    Rate Limit: 15 requests per 5 seconds per tenant

    Usage:
        credential = DefaultAzureCredential()
        client = ResourceGraphClient(credential=credential)

        # Query resources across subscriptions
        results = client.query(
            subscription_ids=["sub-1", "sub-2"],
            query="Resources | where type == 'microsoft.compute/virtualmachines'"
        )

        # Get Advisor recommendations (more efficient than Advisor API)
        recommendations = client.get_advisor_cost_recommendations(["sub-1"])

        # Get resource inventory
        disks = client.get_unattached_disks(["sub-1"])
    """

    def __init__(self, credential: Optional[TokenCredential] = None):
        """
        Initialize Resource Graph client.

        Args:
            credential: Azure credential for authentication
        """
        self.credential = credential
        self._client = None

    def _get_client(self) -> AzureResourceGraphClient:
        """
        Get or create Azure Resource Graph client.

        Returns:
            AzureResourceGraphClient instance
        """
        if self._client is None:
            self._client = AzureResourceGraphClient(credential=self.credential)
        return self._client

    def _execute_query(
        self,
        subscription_ids: List[str],
        query: str,
    ) -> Any:
        """
        Execute Resource Graph query (internal method for mocking).

        Args:
            subscription_ids: List of subscription IDs to query
            query: Kusto query string

        Returns:
            Query response
        """
        client = self._get_client()
        request = QueryRequest(
            subscriptions=subscription_ids,
            query=query,
        )
        return client.resources(request)

    @azure_retry(api_type="resource_graph")
    def query(
        self,
        subscription_ids: List[str],
        query: str,
    ) -> List[Dict[str, Any]]:
        """
        Execute Resource Graph query.

        Uses @azure_retry decorator to handle throttling (429) and
        transient errors with exponential backoff.

        Args:
            subscription_ids: List of Azure subscription IDs to query
            query: Kusto query string

        Returns:
            List of query results

        Raises:
            ValueError: If subscription_ids is empty or query is empty
            HttpResponseError: If query fails after retries
        """
        # Validate inputs
        if not subscription_ids:
            raise ValueError("At least one subscription ID is required")

        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        try:
            response = self._execute_query(subscription_ids, query)

            # Extract data from response
            results = response.data if hasattr(response, 'data') else []

            logger.info(
                f"Resource Graph query returned {len(results)} results "
                f"across {len(subscription_ids)} subscription(s)"
            )

            return results

        except HttpResponseError as e:
            logger.error(f"Resource Graph query failed: {e}")
            raise

    def get_advisor_cost_recommendations(
        self,
        subscription_ids: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Query Advisor recommendations via Resource Graph.

        More efficient than Advisor API for cross-subscription queries
        as it retrieves all recommendations in a single API call.

        Args:
            subscription_ids: List of Azure subscription IDs

        Returns:
            List of cost optimization recommendations
        """
        query = """
        AdvisorResources
        | where type == 'microsoft.advisor/recommendations'
        | where properties.category == 'Cost'
        | project
            recommendationId = id,
            resourceId = properties.resourceMetadata.resourceId,
            impact = properties.impact,
            problem = properties.shortDescription.problem,
            solution = properties.shortDescription.solution,
            savings = properties.extendedProperties.savingsAmount
        """

        return self.query(subscription_ids, query)

    def get_unattached_disks(
        self,
        subscription_ids: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Query for unattached managed disks.

        Args:
            subscription_ids: List of Azure subscription IDs

        Returns:
            List of unattached disks with metadata
        """
        query = """
        Resources
        | where type == 'microsoft.compute/disks'
        | where properties.diskState == 'Unattached'
        | project
            id,
            name,
            sku = sku.name,
            diskSizeGB = properties.diskSizeGB,
            diskState = properties.diskState,
            tags
        """

        return self.query(subscription_ids, query)

    def get_orphaned_nics(
        self,
        subscription_ids: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Query for orphaned network interfaces (not attached to VMs).

        Args:
            subscription_ids: List of Azure subscription IDs

        Returns:
            List of orphaned NICs with metadata
        """
        query = """
        Resources
        | where type == 'microsoft.network/networkinterfaces'
        | where isnull(properties.virtualMachine)
        | project
            id,
            name,
            properties,
            tags
        """

        return self.query(subscription_ids, query)

    def get_unassociated_public_ips(
        self,
        subscription_ids: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Query for unassociated public IP addresses.

        Args:
            subscription_ids: List of Azure subscription IDs

        Returns:
            List of unassociated public IPs with metadata
        """
        query = """
        Resources
        | where type == 'microsoft.network/publicipaddresses'
        | where isnull(properties.ipConfiguration)
        | project
            id,
            name,
            properties,
            tags
        """

        return self.query(subscription_ids, query)

    def sync_resources_to_database(
        self,
        customer_slug: str,
        subscription_ids: List[str],
    ) -> int:
        """
        Sync resource inventory to customer database.

        Validates subscription ownership before syncing to ensure
        resources are stored in the correct customer database.

        Args:
            customer_slug: Customer identifier (e.g., "aus_e_mart")
            subscription_ids: List of Azure subscription IDs

        Returns:
            Number of resources synced

        Raises:
            ValueError: If any subscription does not belong to customer
        """
        # Validate subscription ownership
        db_manager = CustomerDatabaseManager()

        for subscription_id in subscription_ids:
            if not db_manager.validate_subscription_ownership(customer_slug, subscription_id):
                raise ValueError(
                    f"Subscription {subscription_id} does not belong to customer {customer_slug}"
                )

        # Query all resources
        query = """
        Resources
        | project
            id,
            name,
            type,
            location,
            resourceGroup,
            subscriptionId,
            tags,
            properties
        """

        resources = self.query(subscription_ids, query)

        # Store in customer database
        count = 0
        with db_manager.get_customer_db(customer_slug) as db:
            for resource in resources:
                db.store_resource(
                    resource_id=resource.get("id"),
                    resource_name=resource.get("name"),
                    resource_type=resource.get("type"),
                    location=resource.get("location"),
                    resource_group=resource.get("resourceGroup"),
                    subscription_id=resource.get("subscriptionId"),
                    tags=resource.get("tags"),
                    properties=resource.get("properties"),
                )
                count += 1

        logger.info(
            f"Synced {count} resources to database for {customer_slug}"
        )

        return count
