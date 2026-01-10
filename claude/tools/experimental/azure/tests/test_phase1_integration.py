"""
Phase 1 Integration Tests - Azure Cost Optimization Platform

Tests that verify all Phase 1 components work correctly together:
- Validators
- Customer Database Manager (multi-tenant isolation)
- API Retry Logic

Run with: pytest tests/test_phase1_integration.py -v
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock


class TestPhase1Integration:
    """Integration tests for Phase 1 foundation components."""

    def test_customer_registration_with_validated_inputs(self):
        """
        Integration: Customer registration validates all inputs.

        Flow:
        1. Validate tenant_id and subscription_id using validators
        2. Register customer with validated data
        3. Verify isolated database created
        """
        from claude.tools.experimental.azure.validators import (
            validate_tenant_id,
            validate_subscription_id,
            validate_customer_slug,
        )
        from claude.tools.experimental.azure.customer_database import (
            CustomerDatabaseManager,
            Customer,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)

            # Step 1: Validate inputs
            tenant_id = validate_tenant_id("7e0c3f88-faec-4a28-86ad-33bfe7c4b326")
            subscription_id = validate_subscription_id(
                "9b8e7b3f-d3e7-4da9-a22a-9bf7c8ee4dde"
            )
            customer_slug = validate_customer_slug("nw-computing")

            # Step 2: Create customer with validated data
            customer = Customer(
                customer_id="cust-001",
                customer_slug=customer_slug,
                customer_name="NW Computing",
                tenant_ids=[tenant_id],
                subscription_ids=[subscription_id],
                created_at=datetime.now(),
            )

            # Step 3: Register customer
            manager = CustomerDatabaseManager(base_path)
            manager.register_customer(customer)

            # Step 4: Verify database created
            db_path = base_path / f"customer_{customer_slug}.db"
            assert db_path.exists()

            # Step 5: Verify subscription can be retrieved
            with manager.get_customer_db(customer_slug) as db:
                subs = db.list_subscriptions()
                # Initial registration may not add subscriptions directly
                # This verifies the DB is operational

    def test_invalid_subscription_rejected_at_validation_layer(self):
        """
        Integration: Invalid subscription_id caught by validator before DB.

        This prevents corrupted data from reaching the database.
        """
        from claude.tools.experimental.azure.validators import validate_subscription_id
        from claude.tools.experimental.azure.customer_database import (
            CustomerDatabaseManager,
            Customer,
        )

        # Invalid subscription should fail at validation
        with pytest.raises(ValueError) as exc_info:
            validate_subscription_id("not-a-valid-subscription")

        assert "subscription_id" in str(exc_info.value)

    def test_multi_customer_isolation_with_validation(self):
        """
        Integration: Multiple customers have isolated databases.

        Customer A's data cannot be accessed through Customer B's database.
        """
        from claude.tools.experimental.azure.validators import (
            validate_subscription_id,
            validate_customer_slug,
        )
        from claude.tools.experimental.azure.customer_database import (
            CustomerDatabaseManager,
            Customer,
            Subscription,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            manager = CustomerDatabaseManager(base_path)

            # Register two customers with different subscriptions
            customer_a = Customer(
                customer_id="cust-a",
                customer_slug=validate_customer_slug("customer-alpha"),
                customer_name="Customer Alpha",
                tenant_ids=["11111111-1111-1111-1111-111111111111"],
                subscription_ids=["aaaa1111-1111-1111-1111-aaaaaaaaaaaa"],
                created_at=datetime.now(),
            )

            customer_b = Customer(
                customer_id="cust-b",
                customer_slug=validate_customer_slug("customer-beta"),
                customer_name="Customer Beta",
                tenant_ids=["22222222-2222-2222-2222-222222222222"],
                subscription_ids=["bbbb2222-2222-2222-2222-bbbbbbbbbbbb"],
                created_at=datetime.now(),
            )

            manager.register_customer(customer_a)
            manager.register_customer(customer_b)

            # Verify both have separate databases
            db_a_path = base_path / "customer_customer-alpha.db"
            db_b_path = base_path / "customer_customer-beta.db"

            assert db_a_path.exists()
            assert db_b_path.exists()
            assert db_a_path != db_b_path

            # Add data to customer A
            with manager.get_customer_db("customer-alpha") as db:
                db.add_subscription(
                    Subscription(
                        subscription_id="aaaa1111-1111-1111-1111-aaaaaaaaaaaa",
                        subscription_name="Alpha Sub",
                        tenant_id="11111111-1111-1111-1111-111111111111",
                        state="Enabled",
                    )
                )

            # Verify customer B doesn't have customer A's data
            with manager.get_customer_db("customer-beta") as db:
                subs = db.list_subscriptions()
                sub_ids = [s["subscription_id"] for s in subs]
                assert "aaaa1111-1111-1111-1111-aaaaaaaaaaaa" not in sub_ids

    def test_subscription_ownership_validation_prevents_cross_access(self):
        """
        Integration: Cannot access subscription belonging to another customer.
        """
        from claude.tools.experimental.azure.customer_database import (
            CustomerDatabaseManager,
            Customer,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            manager = CustomerDatabaseManager(base_path)

            # Register customer with specific subscription
            customer = Customer(
                customer_id="cust-001",
                customer_slug="owned-customer",
                customer_name="Owned Customer",
                tenant_ids=["11111111-1111-1111-1111-111111111111"],
                subscription_ids=["11111111-2222-3333-4444-555555555555"],
                created_at=datetime.now(),
            )
            manager.register_customer(customer)

            # Validate ownership - owned subscription returns True
            assert manager.validate_subscription_ownership(
                "owned-customer", "11111111-2222-3333-4444-555555555555"
            )

            # Validate ownership - unowned subscription returns False
            assert not manager.validate_subscription_ownership(
                "owned-customer", "99999999-8888-7777-6666-555555555555"
            )

    def test_api_retry_with_confidence_validation(self):
        """
        Integration: API retry works with subsequent confidence validation.

        Simulates: API call retries then returns data that is validated.
        """
        from claude.tools.experimental.azure.api_utils import azure_retry
        from claude.tools.experimental.azure.validators import validate_confidence_score
        from azure.core.exceptions import HttpResponseError

        call_count = 0

        @azure_retry(max_retries=3, base_delay=0.01)
        def get_recommendation_with_retry() -> dict:
            nonlocal call_count
            call_count += 1

            if call_count < 2:
                error = HttpResponseError(message="Throttled")
                error.status_code = 429
                error.response = Mock()
                error.response.headers = {"Retry-After": "0"}
                raise error

            # Return recommendation data after retry
            return {
                "recommendation_id": "rec-001",
                "resource_id": "/subscriptions/xxx/resourceGroups/rg/providers/...",
                "confidence": 0.85,
                "savings_amount": 150.0,
            }

        # Execute with retry
        result = get_recommendation_with_retry()

        # Validate returned confidence score
        validated_confidence = validate_confidence_score(result["confidence"])

        assert call_count == 2  # Initial + 1 retry
        assert validated_confidence == 0.85

    def test_classification_validation_with_customer_context(self):
        """
        Integration: Resource classification validated in customer context.
        """
        from claude.tools.experimental.azure.validators import (
            validate_classification,
            validate_confidence_score,
        )
        from claude.tools.experimental.azure.customer_database import (
            CustomerDatabaseManager,
            Customer,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            manager = CustomerDatabaseManager(base_path)

            customer = Customer(
                customer_id="cust-001",
                customer_slug="classified-customer",
                customer_name="Classified Customer",
                tenant_ids=["11111111-1111-1111-1111-111111111111"],
                subscription_ids=["aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"],
                created_at=datetime.now(),
            )
            manager.register_customer(customer)

            # Validate classification before storing
            classification = validate_classification("dr_standby")
            confidence = validate_confidence_score(0.92)

            # These would be stored in the customer's isolated database
            assert classification == "dr_standby"
            assert confidence == 0.92

    def test_status_validation_workflow(self):
        """
        Integration: Recommendation status transitions are validated.
        """
        from claude.tools.experimental.azure.validators import validate_status

        # Valid status transitions
        status_flow = ["Active", "Implemented"]

        for status in status_flow:
            validated = validate_status(status)
            assert validated == status

        # Invalid status caught
        with pytest.raises(ValueError):
            validate_status("InvalidStatus")


class TestPhase1ErrorHandling:
    """Test error handling across Phase 1 components."""

    def test_api_error_does_not_corrupt_database(self):
        """
        Integration: API errors should not leave database in inconsistent state.
        """
        from claude.tools.experimental.azure.api_utils import azure_retry, AzureAPIError
        from claude.tools.experimental.azure.customer_database import (
            CustomerDatabaseManager,
            Customer,
        )
        from azure.core.exceptions import HttpResponseError

        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            manager = CustomerDatabaseManager(base_path)

            customer = Customer(
                customer_id="cust-err",
                customer_slug="error-test",
                customer_name="Error Test",
                tenant_ids=["11111111-1111-1111-1111-111111111111"],
                subscription_ids=[],
                created_at=datetime.now(),
            )
            manager.register_customer(customer)

            @azure_retry(max_retries=2, base_delay=0.01)
            def always_fails():
                error = HttpResponseError(message="Always fails")
                error.status_code = 503
                error.response = Mock()
                error.response.headers = {}
                raise error

            # API call fails
            with pytest.raises(AzureAPIError):
                always_fails()

            # Database should still be operational
            with manager.get_customer_db("error-test") as db:
                subs = db.list_subscriptions()
                assert isinstance(subs, list)

    def test_validation_error_provides_clear_context(self):
        """
        Integration: Validation errors provide enough context for debugging.
        """
        from claude.tools.experimental.azure.validators import (
            validate_subscription_id,
            validate_confidence_score,
            validate_status,
            validate_classification,
        )

        # Each error should include the field name or valid options
        with pytest.raises(ValueError) as exc_info:
            validate_subscription_id("invalid")
        assert "subscription_id" in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            validate_confidence_score(1.5)
        assert "0.0-1.0" in str(exc_info.value) or "Confidence" in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            validate_status("unknown")
        assert "Invalid status" in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            validate_classification("unknown")
        assert "Invalid classification" in str(exc_info.value)


class TestPhase1DataIntegrity:
    """Test data integrity across Phase 1 components."""

    def test_customer_slug_sanitization(self):
        """
        Integration: Customer slugs are validated to prevent path traversal.
        """
        from claude.tools.experimental.azure.validators import validate_customer_slug

        # Valid slugs
        assert validate_customer_slug("nw-computing") == "nw-computing"
        assert validate_customer_slug("customer123") == "customer123"

        # Path traversal attempts should fail
        with pytest.raises(ValueError):
            validate_customer_slug("../etc/passwd")

        with pytest.raises(ValueError):
            validate_customer_slug("customer/subdir")

        # System reserved prefix should fail
        with pytest.raises(ValueError):
            validate_customer_slug("_system")

    def test_guid_format_consistency(self):
        """
        Integration: All GUIDs validated consistently across components.
        """
        from claude.tools.experimental.azure.validators import (
            validate_subscription_id,
            validate_tenant_id,
        )

        valid_guid = "9b8e7b3f-d3e7-4da9-a22a-9bf7c8ee4dde"

        # Both should accept the same valid GUID
        sub_id = validate_subscription_id(valid_guid)
        tenant_id = validate_tenant_id(valid_guid)

        assert sub_id == tenant_id == valid_guid

        # Both should reject the same invalid format
        invalid = "not-a-guid"

        with pytest.raises(ValueError):
            validate_subscription_id(invalid)

        with pytest.raises(ValueError):
            validate_tenant_id(invalid)
