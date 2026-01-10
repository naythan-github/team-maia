"""
Phase 3 TDD Tests - Azure Advisor Integration

Tests for Azure Advisor API client that pulls native Azure cost recommendations.

Run with: pytest tests/test_azure_advisor.py -v
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
from typing import List, Dict, Any


class TestAdvisorRecommendationDataClass:
    """Tests for AdvisorRecommendation dataclass."""

    def test_advisor_recommendation_creation(self):
        """
        Verify AdvisorRecommendation dataclass can be created with required fields.
        """
        from claude.tools.experimental.azure.azure_advisor import AdvisorRecommendation

        rec = AdvisorRecommendation(
            recommendation_id="rec-123",
            subscription_id="sub-456",
            resource_id="/subscriptions/sub-456/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm1",
            category="Cost",
            impact="High",
            problem="VM is underutilized",
            solution="Downsize to Standard_D2_v3",
            estimated_savings=150.00,
            extended_properties={"currentSku": "Standard_D4_v3"},
        )

        assert rec.recommendation_id == "rec-123"
        assert rec.subscription_id == "sub-456"
        assert rec.category == "Cost"
        assert rec.impact == "High"
        assert rec.estimated_savings == 150.00

    def test_advisor_recommendation_optional_resource_id(self):
        """
        Verify resource_id can be None (some recommendations are subscription-level).
        """
        from claude.tools.experimental.azure.azure_advisor import AdvisorRecommendation

        rec = AdvisorRecommendation(
            recommendation_id="rec-123",
            subscription_id="sub-456",
            resource_id=None,  # Subscription-level recommendation
            category="Cost",
            impact="Medium",
            problem="Reserved instances available",
            solution="Purchase RI for VM family",
            estimated_savings=500.00,
            extended_properties={},
        )

        assert rec.resource_id is None
        assert rec.estimated_savings == 500.00


class TestAzureAdvisorClientInitialization:
    """Tests for AzureAdvisorClient initialization."""

    def test_client_initialization(self):
        """
        Verify AzureAdvisorClient can be initialized.
        """
        from claude.tools.experimental.azure.azure_advisor import AzureAdvisorClient

        client = AzureAdvisorClient()
        assert client is not None

    def test_client_initialization_with_credentials(self):
        """
        Verify client can be initialized with Azure credentials.
        """
        from claude.tools.experimental.azure.azure_advisor import AzureAdvisorClient

        mock_credential = Mock()
        client = AzureAdvisorClient(credential=mock_credential)
        assert client is not None


class TestGetCostRecommendations:
    """Tests for retrieving cost recommendations from Azure Advisor."""

    def test_get_cost_recommendations_success(self):
        """
        Verify cost recommendations can be retrieved for a subscription.
        """
        from claude.tools.experimental.azure.azure_advisor import (
            AzureAdvisorClient,
            AdvisorRecommendation,
        )

        client = AzureAdvisorClient(credential=Mock())

        # Mock Azure SDK response
        mock_recommendation = Mock()
        mock_recommendation.id = "/subscriptions/sub-123/providers/Microsoft.Advisor/recommendations/rec-456"
        mock_recommendation.name = "rec-456"
        mock_recommendation.properties.category = "Cost"
        mock_recommendation.properties.impact = "High"
        mock_recommendation.properties.short_description.problem = "Underutilized VM"
        mock_recommendation.properties.short_description.solution = "Downsize VM"
        mock_recommendation.properties.impacted_value = "/subscriptions/sub-123/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm1"
        mock_recommendation.properties.extended_properties = {
            "savingsAmount": "150",
            "savingsCurrency": "USD",
            "currentSku": "Standard_D4_v3",
            "targetSku": "Standard_D2_v3",
        }

        with patch.object(client, '_get_advisor_client') as mock_get_client:
            mock_advisor_client = Mock()
            mock_advisor_client.recommendations.list.return_value = [mock_recommendation]
            mock_get_client.return_value = mock_advisor_client

            recommendations = client.get_cost_recommendations("sub-123")

            assert len(recommendations) == 1
            assert isinstance(recommendations[0], AdvisorRecommendation)
            assert recommendations[0].category == "Cost"
            assert recommendations[0].impact == "High"
            assert recommendations[0].estimated_savings == 150.00

    def test_get_cost_recommendations_filters_non_cost(self):
        """
        Verify only Cost category recommendations are returned.
        """
        from claude.tools.experimental.azure.azure_advisor import AzureAdvisorClient

        client = AzureAdvisorClient(credential=Mock())

        # Mock recommendations with different categories
        mock_cost_rec = Mock()
        mock_cost_rec.id = "/subscriptions/sub-123/providers/Microsoft.Advisor/recommendations/rec-1"
        mock_cost_rec.properties.category = "Cost"
        mock_cost_rec.properties.impact = "High"
        mock_cost_rec.properties.short_description.problem = "Cost issue"
        mock_cost_rec.properties.short_description.solution = "Cost solution"
        mock_cost_rec.properties.impacted_value = None
        mock_cost_rec.properties.extended_properties = {"savingsAmount": "100"}

        mock_security_rec = Mock()
        mock_security_rec.properties.category = "Security"

        with patch.object(client, '_get_advisor_client') as mock_get_client:
            mock_advisor_client = Mock()
            mock_advisor_client.recommendations.list.return_value = [mock_cost_rec, mock_security_rec]
            mock_get_client.return_value = mock_advisor_client

            recommendations = client.get_cost_recommendations("sub-123")

            # Should only return the Cost recommendation
            assert len(recommendations) == 1
            assert recommendations[0].category == "Cost"

    def test_get_cost_recommendations_handles_missing_savings(self):
        """
        Verify recommendations without savings estimates are handled gracefully.
        """
        from claude.tools.experimental.azure.azure_advisor import AzureAdvisorClient

        client = AzureAdvisorClient(credential=Mock())

        mock_recommendation = Mock()
        mock_recommendation.id = "/subscriptions/sub-123/providers/Microsoft.Advisor/recommendations/rec-1"
        mock_recommendation.properties.category = "Cost"
        mock_recommendation.properties.impact = "Low"
        mock_recommendation.properties.short_description.problem = "Issue"
        mock_recommendation.properties.short_description.solution = "Solution"
        mock_recommendation.properties.impacted_value = None
        mock_recommendation.properties.extended_properties = {}  # No savings

        with patch.object(client, '_get_advisor_client') as mock_get_client:
            mock_advisor_client = Mock()
            mock_advisor_client.recommendations.list.return_value = [mock_recommendation]
            mock_get_client.return_value = mock_advisor_client

            recommendations = client.get_cost_recommendations("sub-123")

            assert len(recommendations) == 1
            assert recommendations[0].estimated_savings is None


class TestRateLimitingAndRetry:
    """Tests for rate limiting and retry logic."""

    def test_rate_limiting_uses_azure_retry_decorator(self):
        """
        Verify get_cost_recommendations uses @azure_retry decorator.
        """
        from claude.tools.experimental.azure.azure_advisor import AzureAdvisorClient
        import inspect

        # Check that method has retry decorator
        method = AzureAdvisorClient.get_cost_recommendations
        # The decorator should be applied
        assert hasattr(method, '__wrapped__') or 'azure_retry' in str(inspect.getsource(AzureAdvisorClient))

    @patch('claude.tools.experimental.azure.api_utils.time.sleep')
    def test_429_throttling_triggers_retry(self, mock_sleep):
        """
        Verify 429 Too Many Requests triggers retry with backoff.
        """
        from claude.tools.experimental.azure.azure_advisor import AzureAdvisorClient
        from azure.core.exceptions import HttpResponseError

        client = AzureAdvisorClient(credential=Mock())

        # Create mock 429 error
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {'Retry-After': '5'}
        error_429 = HttpResponseError(response=mock_response)

        # Mock success on second attempt
        mock_recommendation = Mock()
        mock_recommendation.id = "/subscriptions/sub-123/providers/Microsoft.Advisor/recommendations/rec-1"
        mock_recommendation.properties.category = "Cost"
        mock_recommendation.properties.impact = "Medium"
        mock_recommendation.properties.short_description.problem = "Issue"
        mock_recommendation.properties.short_description.solution = "Solution"
        mock_recommendation.properties.impacted_value = None
        mock_recommendation.properties.extended_properties = {"savingsAmount": "50"}

        with patch.object(client, '_get_advisor_client') as mock_get_client:
            mock_advisor_client = Mock()
            # Fail first, succeed second
            mock_advisor_client.recommendations.list.side_effect = [error_429, [mock_recommendation]]
            mock_get_client.return_value = mock_advisor_client

            recommendations = client.get_cost_recommendations("sub-123")

            # Should eventually succeed
            assert len(recommendations) == 1
            # Should have slept due to throttling
            assert mock_sleep.called


class TestSyncToDatabase:
    """Tests for syncing Advisor recommendations to customer database."""

    def test_sync_to_database_validates_subscription_ownership(self):
        """
        Verify subscription ownership is validated before sync.
        """
        from claude.tools.experimental.azure.azure_advisor import AzureAdvisorClient

        client = AzureAdvisorClient(credential=Mock())

        # Mock customer database manager
        with patch('claude.tools.experimental.azure.azure_advisor.CustomerDatabaseManager') as mock_mgr_class:
            mock_mgr = Mock()
            mock_mgr.validate_subscription_ownership.return_value = False  # Invalid
            mock_mgr_class.return_value = mock_mgr

            with pytest.raises(ValueError, match="Subscription.*does not belong"):
                client.sync_to_database("customer_a", "invalid-sub-123")

    def test_sync_to_database_stores_recommendations(self):
        """
        Verify recommendations are stored in correct customer database.
        """
        from claude.tools.experimental.azure.azure_advisor import (
            AzureAdvisorClient,
            AdvisorRecommendation,
        )

        client = AzureAdvisorClient(credential=Mock())

        # Mock recommendations
        mock_recs = [
            AdvisorRecommendation(
                recommendation_id="rec-1",
                subscription_id="sub-123",
                resource_id="/resource/vm1",
                category="Cost",
                impact="High",
                problem="Issue 1",
                solution="Solution 1",
                estimated_savings=100.00,
                extended_properties={},
            ),
            AdvisorRecommendation(
                recommendation_id="rec-2",
                subscription_id="sub-123",
                resource_id="/resource/vm2",
                category="Cost",
                impact="Medium",
                problem="Issue 2",
                solution="Solution 2",
                estimated_savings=50.00,
                extended_properties={},
            ),
        ]

        with patch.object(client, 'get_cost_recommendations', return_value=mock_recs):
            with patch('claude.tools.experimental.azure.azure_advisor.CustomerDatabaseManager') as mock_mgr_class:
                mock_mgr = Mock()
                mock_mgr.validate_subscription_ownership.return_value = True
                mock_db = Mock()
                mock_mgr.get_customer_db.return_value.__enter__ = Mock(return_value=mock_db)
                mock_mgr.get_customer_db.return_value.__exit__ = Mock(return_value=None)
                mock_mgr_class.return_value = mock_mgr

                count = client.sync_to_database("customer_a", "sub-123")

                # Should return count of synced recommendations
                assert count == 2
                # Should store in database
                assert mock_db.store_advisor_recommendation.call_count == 2

    def test_sync_to_database_returns_count(self):
        """
        Verify sync returns number of new/updated recommendations.
        """
        from claude.tools.experimental.azure.azure_advisor import (
            AzureAdvisorClient,
            AdvisorRecommendation,
        )

        client = AzureAdvisorClient(credential=Mock())

        mock_recs = [
            AdvisorRecommendation(
                recommendation_id="rec-1",
                subscription_id="sub-123",
                resource_id=None,
                category="Cost",
                impact="High",
                problem="RI opportunity",
                solution="Purchase RI",
                estimated_savings=500.00,
                extended_properties={},
            ),
        ]

        with patch.object(client, 'get_cost_recommendations', return_value=mock_recs):
            with patch('claude.tools.experimental.azure.azure_advisor.CustomerDatabaseManager') as mock_mgr_class:
                mock_mgr = Mock()
                mock_mgr.validate_subscription_ownership.return_value = True
                mock_db = Mock()
                mock_mgr.get_customer_db.return_value.__enter__ = Mock(return_value=mock_db)
                mock_mgr.get_customer_db.return_value.__exit__ = Mock(return_value=None)
                mock_mgr_class.return_value = mock_mgr

                count = client.sync_to_database("customer_a", "sub-123")

                assert count == 1


class TestSavingsEstimateParsing:
    """Tests for parsing savings estimates from extended properties."""

    def test_savings_amount_parsed_as_float(self):
        """
        Verify savings amount is correctly parsed from string to float.
        """
        from claude.tools.experimental.azure.azure_advisor import AzureAdvisorClient

        client = AzureAdvisorClient(credential=Mock())

        mock_recommendation = Mock()
        mock_recommendation.id = "/subscriptions/sub-123/providers/Microsoft.Advisor/recommendations/rec-1"
        mock_recommendation.properties.category = "Cost"
        mock_recommendation.properties.impact = "High"
        mock_recommendation.properties.short_description.problem = "Issue"
        mock_recommendation.properties.short_description.solution = "Solution"
        mock_recommendation.properties.impacted_value = None
        mock_recommendation.properties.extended_properties = {
            "savingsAmount": "1234.56",  # String
            "savingsCurrency": "USD",
        }

        with patch.object(client, '_get_advisor_client') as mock_get_client:
            mock_advisor_client = Mock()
            mock_advisor_client.recommendations.list.return_value = [mock_recommendation]
            mock_get_client.return_value = mock_advisor_client

            recommendations = client.get_cost_recommendations("sub-123")

            assert recommendations[0].estimated_savings == 1234.56  # Float

    def test_savings_amount_handles_invalid_format(self):
        """
        Verify invalid savings format is handled gracefully.
        """
        from claude.tools.experimental.azure.azure_advisor import AzureAdvisorClient

        client = AzureAdvisorClient(credential=Mock())

        mock_recommendation = Mock()
        mock_recommendation.id = "/subscriptions/sub-123/providers/Microsoft.Advisor/recommendations/rec-1"
        mock_recommendation.properties.category = "Cost"
        mock_recommendation.properties.impact = "Low"
        mock_recommendation.properties.short_description.problem = "Issue"
        mock_recommendation.properties.short_description.solution = "Solution"
        mock_recommendation.properties.impacted_value = None
        mock_recommendation.properties.extended_properties = {
            "savingsAmount": "invalid",  # Not a number
        }

        with patch.object(client, '_get_advisor_client') as mock_get_client:
            mock_advisor_client = Mock()
            mock_advisor_client.recommendations.list.return_value = [mock_recommendation]
            mock_get_client.return_value = mock_advisor_client

            recommendations = client.get_cost_recommendations("sub-123")

            # Should set to None if parsing fails
            assert recommendations[0].estimated_savings is None


class TestCustomerDatabaseIntegration:
    """Integration tests with CustomerDatabaseManager."""

    def test_recommendations_isolated_per_customer(self):
        """
        Verify recommendations are stored in correct customer database.
        """
        from claude.tools.experimental.azure.azure_advisor import (
            AzureAdvisorClient,
            AdvisorRecommendation,
        )

        client = AzureAdvisorClient(credential=Mock())

        mock_rec = AdvisorRecommendation(
            recommendation_id="rec-1",
            subscription_id="sub-123",
            resource_id=None,
            category="Cost",
            impact="High",
            problem="Issue",
            solution="Solution",
            estimated_savings=100.00,
            extended_properties={},
        )

        with patch.object(client, 'get_cost_recommendations', return_value=[mock_rec]):
            with patch('claude.tools.experimental.azure.azure_advisor.CustomerDatabaseManager') as mock_mgr_class:
                mock_mgr = Mock()
                mock_mgr.validate_subscription_ownership.return_value = True

                # Customer A DB
                mock_db_a = Mock()
                mock_mgr.get_customer_db.return_value.__enter__ = Mock(return_value=mock_db_a)
                mock_mgr.get_customer_db.return_value.__exit__ = Mock(return_value=None)
                mock_mgr_class.return_value = mock_mgr

                # Sync for customer A
                client.sync_to_database("customer_a", "sub-123")

                # Verify get_customer_db called with correct customer
                mock_mgr.get_customer_db.assert_called_with("customer_a")
                # Verify data stored in customer A's DB
                assert mock_db_a.store_advisor_recommendation.called
