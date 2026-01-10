"""
TDD Tests for Azure Cost Optimization Input Validators

Tests written BEFORE implementation per TDD protocol.
Run with: pytest tests/test_validators.py -v
"""

import pytest
from typing import Set


class TestGuidValidation:
    """Tests for Azure GUID validation (subscription_id, tenant_id, etc.)."""

    def test_valid_guid_lowercase_accepted(self):
        """Valid lowercase GUID should be accepted."""
        from claude.tools.experimental.azure.validators import validate_guid

        valid_guid = "9b8e7b3f-d3e7-4da9-a22a-9bf7c8ee4dde"
        result = validate_guid(valid_guid, "subscription_id")
        assert result == valid_guid

    def test_valid_guid_uppercase_accepted(self):
        """Valid uppercase GUID should be accepted."""
        from claude.tools.experimental.azure.validators import validate_guid

        valid_guid = "9B8E7B3F-D3E7-4DA9-A22A-9BF7C8EE4DDE"
        result = validate_guid(valid_guid, "subscription_id")
        assert result == valid_guid

    def test_valid_guid_mixed_case_accepted(self):
        """Valid mixed case GUID should be accepted."""
        from claude.tools.experimental.azure.validators import validate_guid

        valid_guid = "9b8E7b3F-d3e7-4Da9-a22A-9bf7c8Ee4dde"
        result = validate_guid(valid_guid, "subscription_id")
        assert result == valid_guid

    def test_invalid_guid_too_short_rejected(self):
        """GUID that is too short should raise ValueError."""
        from claude.tools.experimental.azure.validators import validate_guid

        with pytest.raises(ValueError) as exc_info:
            validate_guid("9b8e7b3f-d3e7-4da9", "subscription_id")

        assert "subscription_id" in str(exc_info.value)

    def test_invalid_guid_wrong_format_rejected(self):
        """GUID with wrong format should raise ValueError."""
        from claude.tools.experimental.azure.validators import validate_guid

        with pytest.raises(ValueError):
            validate_guid("not-a-valid-guid-format", "subscription_id")

    def test_invalid_guid_no_hyphens_rejected(self):
        """GUID without hyphens should raise ValueError."""
        from claude.tools.experimental.azure.validators import validate_guid

        with pytest.raises(ValueError):
            validate_guid("9b8e7b3fd3e74da9a22a9bf7c8ee4dde", "subscription_id")

    def test_invalid_guid_extra_chars_rejected(self):
        """GUID with extra characters should raise ValueError."""
        from claude.tools.experimental.azure.validators import validate_guid

        with pytest.raises(ValueError):
            validate_guid("9b8e7b3f-d3e7-4da9-a22a-9bf7c8ee4dde-extra", "subscription_id")

    def test_empty_guid_rejected(self):
        """Empty string should raise ValueError."""
        from claude.tools.experimental.azure.validators import validate_guid

        with pytest.raises(ValueError):
            validate_guid("", "subscription_id")

    def test_none_guid_rejected(self):
        """None should raise appropriate error."""
        from claude.tools.experimental.azure.validators import validate_guid

        with pytest.raises((ValueError, TypeError, AttributeError)):
            validate_guid(None, "subscription_id")


class TestSubscriptionIdValidation:
    """Tests for Azure subscription ID validation."""

    def test_valid_subscription_id(self):
        """Valid subscription ID should be accepted."""
        from claude.tools.experimental.azure.validators import validate_subscription_id

        valid_id = "9b8e7b3f-d3e7-4da9-a22a-9bf7c8ee4dde"
        result = validate_subscription_id(valid_id)
        assert result == valid_id

    def test_invalid_subscription_id(self):
        """Invalid subscription ID should raise ValueError."""
        from claude.tools.experimental.azure.validators import validate_subscription_id

        with pytest.raises(ValueError) as exc_info:
            validate_subscription_id("not-valid")

        assert "subscription_id" in str(exc_info.value)


class TestTenantIdValidation:
    """Tests for Azure tenant ID validation."""

    def test_valid_tenant_id(self):
        """Valid tenant ID should be accepted."""
        from claude.tools.experimental.azure.validators import validate_tenant_id

        valid_id = "7e0c3f88-faec-4a28-86ad-33bfe7c4b326"
        result = validate_tenant_id(valid_id)
        assert result == valid_id

    def test_invalid_tenant_id(self):
        """Invalid tenant ID should raise ValueError."""
        from claude.tools.experimental.azure.validators import validate_tenant_id

        with pytest.raises(ValueError) as exc_info:
            validate_tenant_id("invalid")

        assert "tenant_id" in str(exc_info.value)


class TestConfidenceScoreValidation:
    """Tests for confidence score validation (0.0 to 1.0)."""

    def test_confidence_zero_accepted(self):
        """Confidence of 0.0 should be accepted."""
        from claude.tools.experimental.azure.validators import validate_confidence_score

        result = validate_confidence_score(0.0)
        assert result == 0.0

    def test_confidence_one_accepted(self):
        """Confidence of 1.0 should be accepted."""
        from claude.tools.experimental.azure.validators import validate_confidence_score

        result = validate_confidence_score(1.0)
        assert result == 1.0

    def test_confidence_mid_range_accepted(self):
        """Confidence of 0.5 should be accepted."""
        from claude.tools.experimental.azure.validators import validate_confidence_score

        result = validate_confidence_score(0.5)
        assert result == 0.5

    def test_confidence_0_85_accepted(self):
        """Confidence of 0.85 should be accepted."""
        from claude.tools.experimental.azure.validators import validate_confidence_score

        result = validate_confidence_score(0.85)
        assert result == 0.85

    def test_confidence_negative_rejected(self):
        """Negative confidence should raise ValueError."""
        from claude.tools.experimental.azure.validators import validate_confidence_score

        with pytest.raises(ValueError) as exc_info:
            validate_confidence_score(-0.1)

        assert "0.0-1.0" in str(exc_info.value) or "Confidence" in str(exc_info.value)

    def test_confidence_over_one_rejected(self):
        """Confidence over 1.0 should raise ValueError."""
        from claude.tools.experimental.azure.validators import validate_confidence_score

        with pytest.raises(ValueError):
            validate_confidence_score(1.1)

    def test_confidence_way_over_rejected(self):
        """Confidence of 5.0 should raise ValueError."""
        from claude.tools.experimental.azure.validators import validate_confidence_score

        with pytest.raises(ValueError):
            validate_confidence_score(5.0)


class TestStatusValidation:
    """Tests for recommendation status validation."""

    def test_status_active_accepted(self):
        """Status 'Active' should be accepted."""
        from claude.tools.experimental.azure.validators import validate_status

        result = validate_status("Active")
        assert result == "Active"

    def test_status_dismissed_accepted(self):
        """Status 'Dismissed' should be accepted."""
        from claude.tools.experimental.azure.validators import validate_status

        result = validate_status("Dismissed")
        assert result == "Dismissed"

    def test_status_implemented_accepted(self):
        """Status 'Implemented' should be accepted."""
        from claude.tools.experimental.azure.validators import validate_status

        result = validate_status("Implemented")
        assert result == "Implemented"

    def test_status_expired_accepted(self):
        """Status 'Expired' should be accepted."""
        from claude.tools.experimental.azure.validators import validate_status

        result = validate_status("Expired")
        assert result == "Expired"

    def test_status_invalid_rejected(self):
        """Invalid status should raise ValueError."""
        from claude.tools.experimental.azure.validators import validate_status

        with pytest.raises(ValueError) as exc_info:
            validate_status("InvalidStatus")

        assert "Invalid status" in str(exc_info.value)

    def test_status_lowercase_rejected(self):
        """Lowercase status should raise ValueError (case-sensitive)."""
        from claude.tools.experimental.azure.validators import validate_status

        with pytest.raises(ValueError):
            validate_status("active")

    def test_status_empty_rejected(self):
        """Empty status should raise ValueError."""
        from claude.tools.experimental.azure.validators import validate_status

        with pytest.raises(ValueError):
            validate_status("")


class TestImpactValidation:
    """Tests for recommendation impact validation."""

    def test_impact_high_accepted(self):
        """Impact 'High' should be accepted."""
        from claude.tools.experimental.azure.validators import validate_impact

        result = validate_impact("High")
        assert result == "High"

    def test_impact_medium_accepted(self):
        """Impact 'Medium' should be accepted."""
        from claude.tools.experimental.azure.validators import validate_impact

        result = validate_impact("Medium")
        assert result == "Medium"

    def test_impact_low_accepted(self):
        """Impact 'Low' should be accepted."""
        from claude.tools.experimental.azure.validators import validate_impact

        result = validate_impact("Low")
        assert result == "Low"

    def test_impact_none_accepted(self):
        """None impact should be accepted (optional field)."""
        from claude.tools.experimental.azure.validators import validate_impact

        result = validate_impact(None)
        assert result is None

    def test_impact_invalid_rejected(self):
        """Invalid impact should raise ValueError."""
        from claude.tools.experimental.azure.validators import validate_impact

        with pytest.raises(ValueError) as exc_info:
            validate_impact("Critical")  # Not a valid impact

        assert "Invalid impact" in str(exc_info.value)


class TestClassificationValidation:
    """Tests for resource classification validation."""

    def test_classification_production_accepted(self):
        """Classification 'production' should be accepted."""
        from claude.tools.experimental.azure.validators import validate_classification

        result = validate_classification("production")
        assert result == "production"

    def test_classification_dr_standby_accepted(self):
        """Classification 'dr_standby' should be accepted."""
        from claude.tools.experimental.azure.validators import validate_classification

        result = validate_classification("dr_standby")
        assert result == "dr_standby"

    def test_classification_dev_test_accepted(self):
        """Classification 'dev_test' should be accepted."""
        from claude.tools.experimental.azure.validators import validate_classification

        result = validate_classification("dev_test")
        assert result == "dev_test"

    def test_classification_batch_processing_accepted(self):
        """Classification 'batch_processing' should be accepted."""
        from claude.tools.experimental.azure.validators import validate_classification

        result = validate_classification("batch_processing")
        assert result == "batch_processing"

    def test_classification_template_accepted(self):
        """Classification 'template' should be accepted."""
        from claude.tools.experimental.azure.validators import validate_classification

        result = validate_classification("template")
        assert result == "template"

    def test_classification_backup_accepted(self):
        """Classification 'backup' should be accepted."""
        from claude.tools.experimental.azure.validators import validate_classification

        result = validate_classification("backup")
        assert result == "backup"

    def test_classification_reserved_capacity_accepted(self):
        """Classification 'reserved_capacity' should be accepted."""
        from claude.tools.experimental.azure.validators import validate_classification

        result = validate_classification("reserved_capacity")
        assert result == "reserved_capacity"

    def test_classification_invalid_rejected(self):
        """Invalid classification should raise ValueError."""
        from claude.tools.experimental.azure.validators import validate_classification

        with pytest.raises(ValueError) as exc_info:
            validate_classification("invalid_classification")

        assert "Invalid classification" in str(exc_info.value)


class TestCustomerSlugValidation:
    """Tests for customer slug validation (URL-safe identifier)."""

    def test_slug_lowercase_accepted(self):
        """Lowercase slug should be accepted."""
        from claude.tools.experimental.azure.validators import validate_customer_slug

        result = validate_customer_slug("aus_e_mart")
        assert result == "aus_e_mart"

    def test_slug_with_numbers_accepted(self):
        """Slug with numbers should be accepted."""
        from claude.tools.experimental.azure.validators import validate_customer_slug

        result = validate_customer_slug("customer123")
        assert result == "customer123"

    def test_slug_with_hyphens_accepted(self):
        """Slug with hyphens should be accepted."""
        from claude.tools.experimental.azure.validators import validate_customer_slug

        result = validate_customer_slug("nw-computing")
        assert result == "nw-computing"

    def test_slug_with_spaces_rejected(self):
        """Slug with spaces should raise ValueError."""
        from claude.tools.experimental.azure.validators import validate_customer_slug

        with pytest.raises(ValueError):
            validate_customer_slug("aus e mart")

    def test_slug_with_special_chars_rejected(self):
        """Slug with special characters should raise ValueError."""
        from claude.tools.experimental.azure.validators import validate_customer_slug

        with pytest.raises(ValueError):
            validate_customer_slug("customer@company")

    def test_slug_too_short_rejected(self):
        """Slug shorter than 2 characters should raise ValueError."""
        from claude.tools.experimental.azure.validators import validate_customer_slug

        with pytest.raises(ValueError):
            validate_customer_slug("a")

    def test_slug_empty_rejected(self):
        """Empty slug should raise ValueError."""
        from claude.tools.experimental.azure.validators import validate_customer_slug

        with pytest.raises(ValueError):
            validate_customer_slug("")

    def test_slug_system_prefix_rejected(self):
        """Slug starting with underscore (system prefix) should raise ValueError."""
        from claude.tools.experimental.azure.validators import validate_customer_slug

        with pytest.raises(ValueError) as exc_info:
            validate_customer_slug("_system")

        assert "reserved" in str(exc_info.value).lower() or "underscore" in str(exc_info.value).lower()


class TestSavingsValidation:
    """Tests for savings amount validation."""

    def test_positive_savings_accepted(self):
        """Positive savings should be accepted."""
        from claude.tools.experimental.azure.validators import validate_savings

        result = validate_savings(100.50)
        assert result == 100.50

    def test_zero_savings_accepted(self):
        """Zero savings should be accepted."""
        from claude.tools.experimental.azure.validators import validate_savings

        result = validate_savings(0.0)
        assert result == 0.0

    def test_none_savings_accepted(self):
        """None savings should be accepted (optional field)."""
        from claude.tools.experimental.azure.validators import validate_savings

        result = validate_savings(None)
        assert result is None

    def test_negative_savings_rejected(self):
        """Negative savings should raise ValueError."""
        from claude.tools.experimental.azure.validators import validate_savings

        with pytest.raises(ValueError) as exc_info:
            validate_savings(-50.0)

        assert "negative" in str(exc_info.value).lower()
