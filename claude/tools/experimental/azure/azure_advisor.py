"""
Azure Advisor Integration - Cost Recommendations

Pulls native Azure cost recommendations from Azure Advisor API.

Key Features:
- Rate limiting with @azure_retry decorator (10 req/s)
- Per-customer database isolation
- Subscription ownership validation
- Savings estimate parsing

TDD Implementation - Tests in tests/test_azure_advisor.py
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from azure.mgmt.advisor import AdvisorManagementClient
from azure.core.credentials import TokenCredential
from azure.core.exceptions import HttpResponseError

from claude.tools.experimental.azure.api_utils import azure_retry
from claude.tools.experimental.azure.customer_database import CustomerDatabaseManager

logger = logging.getLogger(__name__)


@dataclass
class AdvisorRecommendation:
    """
    Azure Advisor recommendation.

    Represents a cost optimization recommendation from Azure Advisor.
    """

    recommendation_id: str
    subscription_id: str
    resource_id: Optional[str]  # None for subscription-level recommendations
    category: str  # 'Cost', 'Security', 'Performance', etc.
    impact: str  # 'High', 'Medium', 'Low'
    problem: str
    solution: str
    estimated_savings: Optional[float]
    extended_properties: Dict[str, Any]


class AzureAdvisorClient:
    """
    Client for Azure Advisor API.

    Retrieves cost optimization recommendations from Azure Advisor
    with rate limiting and retry logic.

    Usage:
        credential = DefaultAzureCredential()
        client = AzureAdvisorClient(credential=credential)

        # Get recommendations for a subscription
        recommendations = client.get_cost_recommendations("subscription-id")

        # Sync to customer database
        count = client.sync_to_database("customer_slug", "subscription-id")
    """

    def __init__(self, credential: Optional[TokenCredential] = None):
        """
        Initialize Azure Advisor client.

        Args:
            credential: Azure credential for authentication
        """
        self.credential = credential

    def _get_advisor_client(self, subscription_id: str) -> AdvisorManagementClient:
        """
        Get Azure Advisor Management Client for a subscription.

        Args:
            subscription_id: Azure subscription ID

        Returns:
            AdvisorManagementClient instance
        """
        return AdvisorManagementClient(
            credential=self.credential,
            subscription_id=subscription_id,
        )

    @azure_retry(api_type="advisor")
    def get_cost_recommendations(
        self,
        subscription_id: str,
    ) -> List[AdvisorRecommendation]:
        """
        Get cost optimization recommendations from Azure Advisor.

        Uses @azure_retry decorator to handle throttling (429) and
        transient errors with exponential backoff.

        Args:
            subscription_id: Azure subscription ID

        Returns:
            List of AdvisorRecommendation objects (Cost category only)
        """
        client = self._get_advisor_client(subscription_id)

        recommendations = []

        try:
            # List all recommendations for the subscription
            for rec in client.recommendations.list():
                # Filter for Cost category only
                if rec.properties.category != "Cost":
                    continue

                # Parse savings estimate
                estimated_savings = None
                if rec.properties.extended_properties:
                    savings_str = rec.properties.extended_properties.get("savingsAmount")
                    if savings_str:
                        try:
                            estimated_savings = float(savings_str)
                        except (ValueError, TypeError):
                            logger.warning(
                                f"Could not parse savings amount: {savings_str}"
                            )
                            estimated_savings = None

                # Extract resource ID from impacted_value
                resource_id = rec.properties.impacted_value

                # Create AdvisorRecommendation object
                recommendation = AdvisorRecommendation(
                    recommendation_id=rec.name,
                    subscription_id=subscription_id,
                    resource_id=resource_id,
                    category=rec.properties.category,
                    impact=rec.properties.impact,
                    problem=rec.properties.short_description.problem,
                    solution=rec.properties.short_description.solution,
                    estimated_savings=estimated_savings,
                    extended_properties=dict(rec.properties.extended_properties or {}),
                )

                recommendations.append(recommendation)

        except HttpResponseError as e:
            logger.error(
                f"Error retrieving Advisor recommendations for {subscription_id}: {e}"
            )
            raise

        logger.info(
            f"Retrieved {len(recommendations)} cost recommendations "
            f"from Azure Advisor for subscription {subscription_id}"
        )

        return recommendations

    def sync_to_database(
        self,
        customer_slug: str,
        subscription_id: str,
    ) -> int:
        """
        Sync Advisor recommendations to customer database.

        Validates subscription ownership before syncing to ensure
        recommendations are stored in the correct customer database.

        Args:
            customer_slug: Customer identifier (e.g., "aus_e_mart")
            subscription_id: Azure subscription ID

        Returns:
            Number of new/updated recommendations synced

        Raises:
            ValueError: If subscription does not belong to customer
        """
        # Validate subscription ownership
        db_manager = CustomerDatabaseManager()

        if not db_manager.validate_subscription_ownership(customer_slug, subscription_id):
            raise ValueError(
                f"Subscription {subscription_id} does not belong to customer {customer_slug}"
            )

        # Get recommendations from Advisor
        recommendations = self.get_cost_recommendations(subscription_id)

        # Store in customer database
        count = 0
        with db_manager.get_customer_db(customer_slug) as db:
            for rec in recommendations:
                db.store_advisor_recommendation(
                    recommendation_id=rec.recommendation_id,
                    subscription_id=rec.subscription_id,
                    resource_id=rec.resource_id,
                    category=rec.category,
                    impact=rec.impact,
                    problem=rec.problem,
                    solution=rec.solution,
                    estimated_savings=rec.estimated_savings,
                    extended_properties=rec.extended_properties,
                )
                count += 1

        logger.info(
            f"Synced {count} Advisor recommendations to database for {customer_slug}"
        )

        return count
