"""
TDD Tests for Azure Resource Classifier

Classifies resources as DR/standby, dev/test, production, etc.
Critical for preventing false positive recommendations on DR resources.

Tests written BEFORE implementation per TDD protocol.
Run with: pytest tests/test_resource_classifier.py -v
"""

import pytest
from typing import Dict, Optional


class TestResourceClassificationEnum:
    """Tests for ResourceClassification enum."""

    def test_classification_values(self):
        """ResourceClassification should have all expected values."""
        from claude.tools.experimental.azure.resource_classifier import (
            ResourceClassification,
        )

        assert ResourceClassification.PRODUCTION.value == "production"
        assert ResourceClassification.DR_STANDBY.value == "dr_standby"
        assert ResourceClassification.DEV_TEST.value == "dev_test"
        assert ResourceClassification.BATCH_PROCESSING.value == "batch_processing"
        assert ResourceClassification.TEMPLATE.value == "template"
        assert ResourceClassification.BACKUP.value == "backup"
        assert ResourceClassification.RESERVED_CAPACITY.value == "reserved_capacity"
        assert ResourceClassification.UNKNOWN.value == "unknown"


class TestClassificationResultDataclass:
    """Tests for ClassificationResult dataclass."""

    def test_classification_result_creation(self):
        """ClassificationResult should store all fields."""
        from claude.tools.experimental.azure.resource_classifier import (
            ClassificationResult,
            ResourceClassification,
        )

        result = ClassificationResult(
            resource_id="/subscriptions/xxx/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm1",
            classification=ResourceClassification.PRODUCTION,
            confidence=0.95,
            source="tag",
            evidence={"tag_name": "Environment", "tag_value": "prod"},
        )

        assert result.resource_id.endswith("vm1")
        assert result.classification == ResourceClassification.PRODUCTION
        assert result.confidence == 0.95
        assert result.source == "tag"
        assert "tag_name" in result.evidence

    def test_dr_standby_blocks_shutdown(self):
        """DR/standby classification should block shutdown recommendations."""
        from claude.tools.experimental.azure.resource_classifier import (
            ClassificationResult,
            ResourceClassification,
        )

        dr_result = ClassificationResult(
            resource_id="test",
            classification=ResourceClassification.DR_STANDBY,
            confidence=0.90,
            source="tag",
            evidence={},
        )

        assert dr_result.blocks_shutdown_recommendation() is True

    def test_reserved_capacity_blocks_shutdown(self):
        """Reserved capacity should block shutdown recommendations."""
        from claude.tools.experimental.azure.resource_classifier import (
            ClassificationResult,
            ResourceClassification,
        )

        result = ClassificationResult(
            resource_id="test",
            classification=ResourceClassification.RESERVED_CAPACITY,
            confidence=0.85,
            source="tag",
            evidence={},
        )

        assert result.blocks_shutdown_recommendation() is True

    def test_template_blocks_shutdown(self):
        """Template classification should block shutdown recommendations."""
        from claude.tools.experimental.azure.resource_classifier import (
            ClassificationResult,
            ResourceClassification,
        )

        result = ClassificationResult(
            resource_id="test",
            classification=ResourceClassification.TEMPLATE,
            confidence=0.80,
            source="naming_convention",
            evidence={},
        )

        assert result.blocks_shutdown_recommendation() is True

    def test_production_does_not_block_shutdown(self):
        """Production classification should NOT block shutdown (may rightsize)."""
        from claude.tools.experimental.azure.resource_classifier import (
            ClassificationResult,
            ResourceClassification,
        )

        result = ClassificationResult(
            resource_id="test",
            classification=ResourceClassification.PRODUCTION,
            confidence=0.90,
            source="tag",
            evidence={},
        )

        assert result.blocks_shutdown_recommendation() is False

    def test_dev_test_does_not_block_shutdown(self):
        """Dev/test can be shut down."""
        from claude.tools.experimental.azure.resource_classifier import (
            ClassificationResult,
            ResourceClassification,
        )

        result = ClassificationResult(
            resource_id="test",
            classification=ResourceClassification.DEV_TEST,
            confidence=0.85,
            source="tag",
            evidence={},
        )

        assert result.blocks_shutdown_recommendation() is False


class TestTagBasedClassification:
    """Tests for classification based on resource tags."""

    def test_environment_tag_production(self):
        """Environment=prod tag should classify as PRODUCTION."""
        from claude.tools.experimental.azure.resource_classifier import (
            ResourceClassifier,
            ResourceClassification,
        )

        classifier = ResourceClassifier()

        result = classifier.classify(
            resource_id="/subscriptions/xxx/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm1",
            tags={"Environment": "prod"},
            resource_group="some-rg",
            resource_name="vm1",
        )

        assert result.classification == ResourceClassification.PRODUCTION
        assert result.source == "tag"
        assert result.confidence >= 0.90

    def test_environment_tag_production_variations(self):
        """Various production tag values should classify correctly."""
        from claude.tools.experimental.azure.resource_classifier import (
            ResourceClassifier,
            ResourceClassification,
        )

        classifier = ResourceClassifier()
        production_tags = [
            {"Environment": "prod"},
            {"Environment": "production"},
            {"Environment": "PROD"},
            {"Environment": "Production"},
            {"environment": "prod"},  # Lowercase key
        ]

        for tags in production_tags:
            result = classifier.classify("test", tags, "rg", "vm")
            assert result.classification == ResourceClassification.PRODUCTION, (
                f"Failed for tags: {tags}"
            )

    def test_environment_tag_dr_standby(self):
        """DR/standby environment tags should classify correctly."""
        from claude.tools.experimental.azure.resource_classifier import (
            ResourceClassifier,
            ResourceClassification,
        )

        classifier = ResourceClassifier()
        dr_tags = [
            {"Environment": "dr"},
            {"Environment": "DR"},
            {"Environment": "disaster-recovery"},
            {"Environment": "standby"},
            {"Environment": "failover"},
        ]

        for tags in dr_tags:
            result = classifier.classify("test", tags, "rg", "vm")
            assert result.classification == ResourceClassification.DR_STANDBY, (
                f"Failed for tags: {tags}"
            )

    def test_environment_tag_dev_test(self):
        """Dev/test environment tags should classify correctly."""
        from claude.tools.experimental.azure.resource_classifier import (
            ResourceClassifier,
            ResourceClassification,
        )

        classifier = ResourceClassifier()
        dev_tags = [
            {"Environment": "dev"},
            {"Environment": "development"},
            {"Environment": "test"},
            {"Environment": "testing"},
            {"Environment": "qa"},
            {"Environment": "uat"},
            {"Environment": "staging"},
            {"Environment": "sandbox"},
        ]

        for tags in dev_tags:
            result = classifier.classify("test", tags, "rg", "vm")
            assert result.classification == ResourceClassification.DEV_TEST, (
                f"Failed for tags: {tags}"
            )

    def test_purpose_tag_batch_processing(self):
        """Purpose=batch tags should classify as BATCH_PROCESSING."""
        from claude.tools.experimental.azure.resource_classifier import (
            ResourceClassifier,
            ResourceClassification,
        )

        classifier = ResourceClassifier()
        batch_tags = [
            {"Purpose": "batch"},
            {"Purpose": "batch-processing"},
            {"Purpose": "scheduled"},
            {"Purpose": "cron"},
            {"Purpose": "etl"},
            {"Workload": "batch"},
        ]

        for tags in batch_tags:
            result = classifier.classify("test", tags, "rg", "vm")
            assert result.classification == ResourceClassification.BATCH_PROCESSING, (
                f"Failed for tags: {tags}"
            )


class TestResourceGroupBasedClassification:
    """Tests for classification based on resource group naming."""

    def test_resource_group_prod_pattern(self):
        """Resource groups with prod patterns should classify as PRODUCTION."""
        from claude.tools.experimental.azure.resource_classifier import (
            ResourceClassifier,
            ResourceClassification,
        )

        classifier = ResourceClassifier()
        prod_rgs = [
            "prod-webapp-rg",
            "rg-prod-eastus",
            "myapp-prd-rg",
            "production-resources",
        ]

        for rg in prod_rgs:
            result = classifier.classify("test", None, rg, "vm")
            assert result.classification == ResourceClassification.PRODUCTION, (
                f"Failed for RG: {rg}"
            )
            assert result.source == "resource_group"

    def test_resource_group_dr_pattern(self):
        """Resource groups with DR patterns should classify as DR_STANDBY."""
        from claude.tools.experimental.azure.resource_classifier import (
            ResourceClassifier,
            ResourceClassification,
        )

        classifier = ResourceClassifier()
        dr_rgs = [
            "dr-webapp-rg",
            "rg-disaster-recovery",
            "standby-resources-rg",
            "failover-eastus",
        ]

        for rg in dr_rgs:
            result = classifier.classify("test", None, rg, "vm")
            assert result.classification == ResourceClassification.DR_STANDBY, (
                f"Failed for RG: {rg}"
            )

    def test_resource_group_dev_pattern(self):
        """Resource groups with dev/test patterns should classify as DEV_TEST."""
        from claude.tools.experimental.azure.resource_classifier import (
            ResourceClassifier,
            ResourceClassification,
        )

        classifier = ResourceClassifier()
        dev_rgs = [
            "dev-webapp-rg",
            "rg-dev-eastus",
            "test-resources-rg",
            "qa-environment",
        ]

        for rg in dev_rgs:
            result = classifier.classify("test", None, rg, "vm")
            assert result.classification == ResourceClassification.DEV_TEST, (
                f"Failed for RG: {rg}"
            )


class TestResourceNameFallback:
    """Tests for classification based on resource name patterns."""

    def test_resource_name_fallback(self):
        """Resource name should be used when no tags or RG pattern matches."""
        from claude.tools.experimental.azure.resource_classifier import (
            ResourceClassifier,
            ResourceClassification,
        )

        classifier = ResourceClassifier()

        # Resource name indicates DR
        result = classifier.classify(
            resource_id="test",
            tags=None,
            resource_group="generic-rg",
            resource_name="vm-dr-standby-01",
        )

        assert result.classification == ResourceClassification.DR_STANDBY
        assert result.source == "resource_name"

    def test_no_metadata_returns_unknown(self):
        """No matching patterns should return UNKNOWN classification."""
        from claude.tools.experimental.azure.resource_classifier import (
            ResourceClassifier,
            ResourceClassification,
        )

        classifier = ResourceClassifier()

        result = classifier.classify(
            resource_id="test",
            tags=None,
            resource_group="some-random-rg",
            resource_name="random-vm-name",
        )

        assert result.classification == ResourceClassification.UNKNOWN
        assert result.confidence < 0.5


class TestConfidenceScoring:
    """Tests for confidence scoring."""

    def test_tag_confidence_higher_than_naming(self):
        """Tag-based classification should have higher confidence than naming."""
        from claude.tools.experimental.azure.resource_classifier import (
            ResourceClassifier,
        )

        classifier = ResourceClassifier()

        # Classification from tag
        tag_result = classifier.classify(
            resource_id="test",
            tags={"Environment": "prod"},
            resource_group="generic-rg",
            resource_name="vm",
        )

        # Classification from resource group
        rg_result = classifier.classify(
            resource_id="test",
            tags=None,
            resource_group="prod-webapp-rg",
            resource_name="vm",
        )

        assert tag_result.confidence > rg_result.confidence

    def test_tag_overrides_resource_group(self):
        """Tag classification should take precedence over resource group."""
        from claude.tools.experimental.azure.resource_classifier import (
            ResourceClassifier,
            ResourceClassification,
        )

        classifier = ResourceClassifier()

        # Tag says dev, RG says prod
        result = classifier.classify(
            resource_id="test",
            tags={"Environment": "dev"},
            resource_group="prod-webapp-rg",
            resource_name="vm",
        )

        # Tag should win
        assert result.classification == ResourceClassification.DEV_TEST
        assert result.source == "tag"


class TestSpecialCases:
    """Tests for special classification cases."""

    def test_template_tag(self):
        """Template tags should classify as TEMPLATE."""
        from claude.tools.experimental.azure.resource_classifier import (
            ResourceClassifier,
            ResourceClassification,
        )

        classifier = ResourceClassifier()

        template_tags = [
            {"Purpose": "template"},
            {"Classification": "template"},
            {"Type": "golden-image"},
        ]

        for tags in template_tags:
            result = classifier.classify("test", tags, "rg", "vm")
            assert result.classification == ResourceClassification.TEMPLATE, (
                f"Failed for tags: {tags}"
            )

    def test_backup_tag(self):
        """Backup tags should classify as BACKUP."""
        from claude.tools.experimental.azure.resource_classifier import (
            ResourceClassifier,
            ResourceClassification,
        )

        classifier = ResourceClassifier()

        result = classifier.classify(
            resource_id="test",
            tags={"Purpose": "backup"},
            resource_group="rg",
            resource_name="vm",
        )

        assert result.classification == ResourceClassification.BACKUP

    def test_case_insensitive_tag_matching(self):
        """Tag matching should be case-insensitive."""
        from claude.tools.experimental.azure.resource_classifier import (
            ResourceClassifier,
            ResourceClassification,
        )

        classifier = ResourceClassifier()

        # Various case combinations
        results = [
            classifier.classify("test", {"ENVIRONMENT": "PROD"}, "rg", "vm"),
            classifier.classify("test", {"environment": "PROD"}, "rg", "vm"),
            classifier.classify("test", {"Environment": "PROD"}, "rg", "vm"),
        ]

        for result in results:
            assert result.classification == ResourceClassification.PRODUCTION

    def test_empty_tags_uses_fallback(self):
        """Empty tags dict should use resource group/name fallback."""
        from claude.tools.experimental.azure.resource_classifier import (
            ResourceClassifier,
            ResourceClassification,
        )

        classifier = ResourceClassifier()

        result = classifier.classify(
            resource_id="test",
            tags={},  # Empty dict, not None
            resource_group="prod-webapp-rg",
            resource_name="vm",
        )

        assert result.classification == ResourceClassification.PRODUCTION
        assert result.source == "resource_group"


class TestClassifyMultiple:
    """Tests for classifying multiple resources."""

    def test_classify_multiple_resources(self):
        """Should be able to classify multiple resources efficiently."""
        from claude.tools.experimental.azure.resource_classifier import (
            ResourceClassifier,
            ResourceClassification,
        )

        classifier = ResourceClassifier()

        resources = [
            {
                "resource_id": "vm1",
                "tags": {"Environment": "prod"},
                "resource_group": "rg1",
                "resource_name": "prod-vm-01",
            },
            {
                "resource_id": "vm2",
                "tags": {"Environment": "dr"},
                "resource_group": "rg2",
                "resource_name": "dr-vm-01",
            },
            {
                "resource_id": "vm3",
                "tags": None,
                "resource_group": "dev-rg",
                "resource_name": "test-vm",
            },
        ]

        results = classifier.classify_multiple(resources)

        assert len(results) == 3
        assert results[0].classification == ResourceClassification.PRODUCTION
        assert results[1].classification == ResourceClassification.DR_STANDBY
        assert results[2].classification == ResourceClassification.DEV_TEST
