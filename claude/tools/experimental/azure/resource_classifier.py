"""
Azure Cost Optimization Resource Classifier

Classifies resources as DR/standby, dev/test, production, etc.
to prevent false positive recommendations.

CRITICAL for preventing:
- Recommending shutdown of DR/standby resources
- Flagging template disks as orphaned
- Missing production resources that should be protected

TDD Implementation - Tests in tests/test_resource_classifier.py
"""

import re
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Set


class ResourceClassification(Enum):
    """Types of resource classifications."""

    PRODUCTION = "production"
    DR_STANDBY = "dr_standby"
    DEV_TEST = "dev_test"
    BATCH_PROCESSING = "batch_processing"
    TEMPLATE = "template"
    BACKUP = "backup"
    RESERVED_CAPACITY = "reserved_capacity"
    UNKNOWN = "unknown"


# Classifications that block shutdown/deallocate recommendations
SHUTDOWN_BLOCKING_CLASSIFICATIONS: Set[ResourceClassification] = {
    ResourceClassification.DR_STANDBY,
    ResourceClassification.RESERVED_CAPACITY,
    ResourceClassification.TEMPLATE,
}


@dataclass
class ClassificationResult:
    """
    Result of resource classification.

    Used to determine if a resource should be protected from
    certain types of recommendations.
    """

    resource_id: str
    classification: ResourceClassification
    confidence: float
    source: str  # 'tag', 'resource_group', 'resource_name', 'ml_inferred'
    evidence: Dict[str, Any]

    def blocks_shutdown_recommendation(self) -> bool:
        """
        Check if classification blocks shutdown/deallocate recommendations.

        DR/standby, template, and reserved capacity resources should
        never be recommended for shutdown.
        """
        return self.classification in SHUTDOWN_BLOCKING_CLASSIFICATIONS


class ResourceClassifier:
    """
    Classifies resources to prevent false positive recommendations.

    Classification Sources (priority order):
    1. Explicit tags (Environment, Purpose, Classification)
    2. Resource group naming conventions
    3. Resource naming conventions
    4. ML inference from behavior patterns (future)

    Usage:
        classifier = ResourceClassifier()
        result = classifier.classify(
            resource_id=resource.id,
            tags=resource.tags,
            resource_group=resource.resource_group,
            resource_name=resource.name,
        )

        if result.blocks_shutdown_recommendation():
            # Don't recommend shutdown
            pass
    """

    # Confidence levels by source
    CONFIDENCE_TAG = 0.95
    CONFIDENCE_RESOURCE_GROUP = 0.80
    CONFIDENCE_RESOURCE_NAME = 0.65
    CONFIDENCE_UNKNOWN = 0.30

    # Tag patterns that indicate classification
    # Format: (tag_key_pattern, tag_value_pattern, classification)
    TAG_PATTERNS = [
        # Production patterns
        (r"^environment$", r"^prod(uction)?$", ResourceClassification.PRODUCTION),
        (r"^purpose$", r"^production$", ResourceClassification.PRODUCTION),
        # DR/Standby patterns
        (r"^environment$", r"^(dr|disaster[-_]?recovery|standby|failover)$", ResourceClassification.DR_STANDBY),
        (r"^purpose$", r"^(disaster[-_]?recovery|standby|failover)$", ResourceClassification.DR_STANDBY),
        # Dev/Test patterns
        (r"^environment$", r"^(dev(elopment)?|test(ing)?|qa|uat|staging|sandbox)$", ResourceClassification.DEV_TEST),
        (r"^purpose$", r"^(dev(elopment)?|test(ing)?|sandbox)$", ResourceClassification.DEV_TEST),
        # Batch processing patterns
        (r"^purpose$", r"^(batch|batch[-_]?processing|scheduled|cron|etl)$", ResourceClassification.BATCH_PROCESSING),
        (r"^workload$", r"^batch$", ResourceClassification.BATCH_PROCESSING),
        # Template patterns
        (r"^purpose$", r"^template$", ResourceClassification.TEMPLATE),
        (r"^classification$", r"^template$", ResourceClassification.TEMPLATE),
        (r"^type$", r"^golden[-_]?image$", ResourceClassification.TEMPLATE),
        # Backup patterns
        (r"^purpose$", r"^backup$", ResourceClassification.BACKUP),
    ]

    # Resource group naming patterns
    RG_PATTERNS = [
        (r"(^prod[-_]|[-_]prod[-_]|[-_]prd[-_]|^production)", ResourceClassification.PRODUCTION),
        (r"(^dr[-_]|[-_]dr[-_]|disaster|standby|failover)", ResourceClassification.DR_STANDBY),
        (r"(^dev[-_]|[-_]dev[-_]|^test[-_]|[-_]test[-_]|qa[-_]|uat[-_])", ResourceClassification.DEV_TEST),
    ]

    # Resource name patterns (lowest priority)
    NAME_PATTERNS = [
        (r"([-_]prod[-_]|[-_]prd[-_])", ResourceClassification.PRODUCTION),
        (r"([-_]dr[-_]|[-_]standby[-_]|[-_]failover[-_])", ResourceClassification.DR_STANDBY),
        (r"([-_]dev[-_]|[-_]test[-_]|[-_]qa[-_])", ResourceClassification.DEV_TEST),
    ]

    def classify(
        self,
        resource_id: str,
        tags: Optional[Dict[str, str]],
        resource_group: str,
        resource_name: str,
    ) -> ClassificationResult:
        """
        Classify a resource based on available metadata.

        Args:
            resource_id: Azure resource ID
            tags: Resource tags (may be None)
            resource_group: Resource group name
            resource_name: Resource name

        Returns:
            ClassificationResult with classification and confidence
        """
        # Try tag-based classification first (highest priority)
        if tags:
            tag_result = self._classify_from_tags(resource_id, tags)
            if tag_result:
                return tag_result

        # Try resource group naming patterns
        rg_result = self._classify_from_resource_group(resource_id, resource_group)
        if rg_result:
            return rg_result

        # Try resource name patterns (lowest priority)
        name_result = self._classify_from_resource_name(resource_id, resource_name)
        if name_result:
            return name_result

        # No classification found
        return ClassificationResult(
            resource_id=resource_id,
            classification=ResourceClassification.UNKNOWN,
            confidence=self.CONFIDENCE_UNKNOWN,
            source="none",
            evidence={"reason": "no_matching_patterns"},
        )

    def _classify_from_tags(
        self,
        resource_id: str,
        tags: Dict[str, str],
    ) -> Optional[ClassificationResult]:
        """Classify based on resource tags."""
        # Normalize tag keys to lowercase for matching
        normalized_tags = {k.lower(): v for k, v in tags.items()}

        for key_pattern, value_pattern, classification in self.TAG_PATTERNS:
            for tag_key, tag_value in normalized_tags.items():
                if re.match(key_pattern, tag_key, re.IGNORECASE):
                    if re.match(value_pattern, tag_value, re.IGNORECASE):
                        return ClassificationResult(
                            resource_id=resource_id,
                            classification=classification,
                            confidence=self.CONFIDENCE_TAG,
                            source="tag",
                            evidence={
                                "tag_key": tag_key,
                                "tag_value": tag_value,
                                "pattern": value_pattern,
                            },
                        )

        return None

    def _classify_from_resource_group(
        self,
        resource_id: str,
        resource_group: str,
    ) -> Optional[ClassificationResult]:
        """Classify based on resource group naming convention."""
        rg_lower = resource_group.lower()

        for pattern, classification in self.RG_PATTERNS:
            if re.search(pattern, rg_lower, re.IGNORECASE):
                return ClassificationResult(
                    resource_id=resource_id,
                    classification=classification,
                    confidence=self.CONFIDENCE_RESOURCE_GROUP,
                    source="resource_group",
                    evidence={
                        "resource_group": resource_group,
                        "pattern": pattern,
                    },
                )

        return None

    def _classify_from_resource_name(
        self,
        resource_id: str,
        resource_name: str,
    ) -> Optional[ClassificationResult]:
        """Classify based on resource naming convention."""
        name_lower = resource_name.lower()

        for pattern, classification in self.NAME_PATTERNS:
            if re.search(pattern, name_lower, re.IGNORECASE):
                return ClassificationResult(
                    resource_id=resource_id,
                    classification=classification,
                    confidence=self.CONFIDENCE_RESOURCE_NAME,
                    source="resource_name",
                    evidence={
                        "resource_name": resource_name,
                        "pattern": pattern,
                    },
                )

        return None

    def classify_multiple(
        self,
        resources: List[Dict[str, Any]],
    ) -> List[ClassificationResult]:
        """
        Classify multiple resources efficiently.

        Args:
            resources: List of resource dicts with keys:
                - resource_id: str
                - tags: Optional[Dict[str, str]]
                - resource_group: str
                - resource_name: str

        Returns:
            List of ClassificationResult objects in same order as input
        """
        results = []
        for resource in resources:
            result = self.classify(
                resource_id=resource["resource_id"],
                tags=resource.get("tags"),
                resource_group=resource["resource_group"],
                resource_name=resource["resource_name"],
            )
            results.append(result)

        return results
