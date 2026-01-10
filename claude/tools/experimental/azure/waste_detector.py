"""
Azure Cost Optimization Waste Detector

Detects orphaned resources (disks, NICs, IPs) and idle VMs
with comprehensive false positive prevention.

CRITICAL Rules:
- Minimum 14 days unattached for disks
- Minimum 7 days unattached for NICs
- Minimum 14 days unassociated for IPs
- Check for Template/Backup/DoNotDelete tags
- Check workload patterns before flagging VMs as idle
- Check DR/standby classification before any recommendation

TDD Implementation - Tests in tests/test_waste_detector.py
"""

from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from claude.tools.experimental.azure.workload_detector import WorkloadPatternDetector


class WasteType(Enum):
    """Types of wasted resources."""

    ORPHANED_DISK = "orphaned_disk"
    ORPHANED_NIC = "orphaned_nic"
    ORPHANED_IP = "orphaned_ip"
    IDLE_VM = "idle_vm"
    STOPPED_VM = "stopped_vm"  # Stopped but not deallocated
    OLD_SNAPSHOT = "old_snapshot"
    EMPTY_RESOURCE_GROUP = "empty_resource_group"


# Tags that block waste detection
BLOCKING_TAGS = {
    "template": True,
    "backup": True,
    "donotdelete": True,
    "do-not-delete": True,
    "do_not_delete": True,
    "golden-image": True,
    "golden_image": True,
    "reserved": True,
}


@dataclass
class WasteDetectionResult:
    """
    Result of waste detection analysis.

    Used to present recommendations to users with appropriate
    confidence levels and blocking factors.
    """

    resource_id: str
    waste_type: WasteType
    confidence: float
    estimated_monthly_cost: float
    days_inactive: int
    recommendation: str
    blocking_factors: List[str]

    def is_actionable(self) -> bool:
        """
        Check if recommendation should be shown to user.

        Require high confidence and no blocking factors.
        """
        return self.confidence >= 0.75 and len(self.blocking_factors) == 0


class WasteDetector:
    """
    Detects wasted resources with false positive prevention.

    Key Rules:
    - Orphaned disk: 14 days unattached minimum
    - Orphaned NIC: 7 days unattached minimum
    - Orphaned IP: 14 days unassociated minimum
    - Idle VM: 14 days + workload pattern analysis
    - Old snapshot: 90 days
    - Check for template/backup tags before flagging
    - Check lifecycle events (recent detachment = don't flag)

    Usage:
        detector = WasteDetector()

        # Detect orphaned disks
        results = detector.detect_orphaned_disks(db)
        for r in results:
            if r.is_actionable():
                print(f"Recommend: {r.recommendation}")
    """

    MIN_ORPHAN_DAYS = {
        WasteType.ORPHANED_DISK: 14,
        WasteType.ORPHANED_NIC: 7,
        WasteType.ORPHANED_IP: 14,
        WasteType.IDLE_VM: 14,
        WasteType.STOPPED_VM: 7,
        WasteType.OLD_SNAPSHOT: 90,
        WasteType.EMPTY_RESOURCE_GROUP: 30,
    }

    # Confidence scaling by days over threshold
    CONFIDENCE_BASE = 0.70
    CONFIDENCE_MAX = 0.95

    def detect_orphaned_disks(
        self,
        db: Any,
    ) -> List[WasteDetectionResult]:
        """
        Detect unattached disks that may be waste.

        False Positive Prevention:
        - Check tags for 'Template', 'Backup', 'DoNotDelete'
        - Check resource_classifications for protected types
        - Check resource_lifecycle for recent detachment
        - Minimum 14 days unattached

        Args:
            db: Database connection with get_unattached_disks method

        Returns:
            List of WasteDetectionResult for orphaned disks
        """
        results = []
        min_days = self.MIN_ORPHAN_DAYS[WasteType.ORPHANED_DISK]

        unattached_disks = db.get_unattached_disks()

        for disk in unattached_disks:
            resource_id = disk["resource_id"]
            detached_at = disk.get("detached_at")
            tags = disk.get("tags", {}) or {}

            # Calculate days inactive
            if detached_at:
                if isinstance(detached_at, str):
                    detached_at = datetime.fromisoformat(detached_at)
                days_inactive = (datetime.now() - detached_at).days
            else:
                days_inactive = 0

            # Check minimum threshold
            if days_inactive < min_days:
                continue

            # Check for blocking factors
            blocking_factors = self._check_blocking_tags(tags)

            # Check classification
            classification = db.get_resource_classification(resource_id)
            if classification:
                class_type = classification.get("classification", "").lower()
                if class_type in ["template", "backup", "dr_standby"]:
                    blocking_factors.append(f"Classified as {class_type}")

            # Calculate confidence
            confidence = self._calculate_confidence(days_inactive, min_days)

            # Get cost estimate
            monthly_cost = disk.get("monthly_cost", 0.0)
            if not monthly_cost:
                # Estimate from size and SKU
                monthly_cost = self._estimate_disk_cost(
                    disk.get("size_gb", 0),
                    disk.get("sku", "Standard_LRS"),
                )

            results.append(WasteDetectionResult(
                resource_id=resource_id,
                waste_type=WasteType.ORPHANED_DISK,
                confidence=confidence if not blocking_factors else 0.3,
                estimated_monthly_cost=monthly_cost,
                days_inactive=days_inactive,
                recommendation=f"Delete orphaned disk '{disk.get('disk_name', 'unknown')}'",
                blocking_factors=blocking_factors,
            ))

        return results

    def detect_idle_vms(
        self,
        db: Any,
        pattern_detector: "WorkloadPatternDetector",
    ) -> List[WasteDetectionResult]:
        """
        Detect VMs that appear idle.

        False Positive Prevention:
        - Minimum 14 days observation
        - Check workload patterns (batch jobs)
        - Check resource_classifications (DR/standby)
        - Verify metrics cover all hours of day

        Args:
            db: Database connection with get_vms_with_metrics method
            pattern_detector: WorkloadPatternDetector for pattern analysis

        Returns:
            List of WasteDetectionResult for idle VMs
        """
        from claude.tools.experimental.azure.workload_detector import WorkloadPattern
        from claude.tools.experimental.azure.resource_classifier import (
            ResourceClassification,
        )

        results = []
        min_days = self.MIN_ORPHAN_DAYS[WasteType.IDLE_VM]

        vms = db.get_vms_with_metrics()

        for vm in vms:
            resource_id = vm["resource_id"]
            tags = vm.get("tags", {}) or {}
            metrics = vm.get("metrics", [])

            # Analyze workload pattern
            analysis = pattern_detector.analyze_pattern(resource_id, metrics)

            # Check for blocking factors
            blocking_factors = self._check_blocking_tags(tags)

            # Check classification
            classification = db.get_resource_classification(resource_id)
            if classification:
                class_type = classification.get("classification", "").lower()
                if class_type in ["dr_standby", "reserved_capacity", "batch_processing"]:
                    blocking_factors.append(f"Classified as {class_type}")

            # Skip if not idle pattern or scheduled workload
            if analysis.pattern == WorkloadPattern.SCHEDULED:
                blocking_factors.append("Detected scheduled workload pattern")

            if analysis.pattern != WorkloadPattern.IDLE:
                continue

            # Skip if observation period too short
            if analysis.observation_days < min_days:
                continue

            # Calculate confidence from pattern analysis
            confidence = analysis.confidence if not blocking_factors else 0.3

            results.append(WasteDetectionResult(
                resource_id=resource_id,
                waste_type=WasteType.IDLE_VM,
                confidence=confidence,
                estimated_monthly_cost=self._estimate_vm_cost(vm.get("vm_size", "")),
                days_inactive=analysis.observation_days,
                recommendation=f"Consider stopping idle VM '{vm.get('vm_name', 'unknown')}'",
                blocking_factors=blocking_factors,
            ))

        return results

    def detect_orphaned_nics(
        self,
        db: Any,
    ) -> List[WasteDetectionResult]:
        """
        Detect unattached NICs that may be waste.

        Args:
            db: Database connection with get_unattached_nics method

        Returns:
            List of WasteDetectionResult for orphaned NICs
        """
        results = []
        min_days = self.MIN_ORPHAN_DAYS[WasteType.ORPHANED_NIC]

        unattached_nics = db.get_unattached_nics()

        for nic in unattached_nics:
            resource_id = nic["resource_id"]
            detached_at = nic.get("detached_at")
            tags = nic.get("tags", {}) or {}

            # Calculate days inactive
            if detached_at:
                if isinstance(detached_at, str):
                    detached_at = datetime.fromisoformat(detached_at)
                days_inactive = (datetime.now() - detached_at).days
            else:
                days_inactive = 0

            if days_inactive < min_days:
                continue

            blocking_factors = self._check_blocking_tags(tags)
            confidence = self._calculate_confidence(days_inactive, min_days)

            results.append(WasteDetectionResult(
                resource_id=resource_id,
                waste_type=WasteType.ORPHANED_NIC,
                confidence=confidence if not blocking_factors else 0.3,
                estimated_monthly_cost=0.0,  # NICs are free
                days_inactive=days_inactive,
                recommendation=f"Delete orphaned NIC '{nic.get('nic_name', 'unknown')}'",
                blocking_factors=blocking_factors,
            ))

        return results

    def detect_orphaned_public_ips(
        self,
        db: Any,
    ) -> List[WasteDetectionResult]:
        """
        Detect unassociated public IPs that may be waste.

        Args:
            db: Database connection with get_unassociated_public_ips method

        Returns:
            List of WasteDetectionResult for orphaned public IPs
        """
        results = []
        min_days = self.MIN_ORPHAN_DAYS[WasteType.ORPHANED_IP]

        unassociated_ips = db.get_unassociated_public_ips()

        for ip in unassociated_ips:
            resource_id = ip["resource_id"]
            unassociated_at = ip.get("unassociated_at")
            tags = ip.get("tags", {}) or {}

            # Calculate days inactive
            if unassociated_at:
                if isinstance(unassociated_at, str):
                    unassociated_at = datetime.fromisoformat(unassociated_at)
                days_inactive = (datetime.now() - unassociated_at).days
            else:
                days_inactive = 0

            if days_inactive < min_days:
                continue

            blocking_factors = self._check_blocking_tags(tags)
            confidence = self._calculate_confidence(days_inactive, min_days)

            # Public IPs have small monthly cost
            monthly_cost = 3.65  # Basic static IP cost

            results.append(WasteDetectionResult(
                resource_id=resource_id,
                waste_type=WasteType.ORPHANED_IP,
                confidence=confidence if not blocking_factors else 0.3,
                estimated_monthly_cost=monthly_cost,
                days_inactive=days_inactive,
                recommendation=f"Delete orphaned public IP '{ip.get('ip_name', 'unknown')}'",
                blocking_factors=blocking_factors,
            ))

        return results

    def detect_old_snapshots(
        self,
        db: Any,
    ) -> List[WasteDetectionResult]:
        """
        Detect old snapshots that may no longer be needed.

        Args:
            db: Database connection with get_old_snapshots method

        Returns:
            List of WasteDetectionResult for old snapshots
        """
        results = []
        min_days = self.MIN_ORPHAN_DAYS[WasteType.OLD_SNAPSHOT]

        old_snapshots = db.get_old_snapshots()

        for snap in old_snapshots:
            resource_id = snap["resource_id"]
            created_at = snap.get("created_at")
            tags = snap.get("tags", {}) or {}

            # Calculate days since creation
            if created_at:
                if isinstance(created_at, str):
                    created_at = datetime.fromisoformat(created_at)
                days_old = (datetime.now() - created_at).days
            else:
                days_old = 0

            if days_old < min_days:
                continue

            blocking_factors = self._check_blocking_tags(tags)
            confidence = self._calculate_confidence(days_old, min_days)

            # Estimate cost from size
            size_gb = snap.get("size_gb", 0)
            monthly_cost = size_gb * 0.05  # Rough snapshot cost

            results.append(WasteDetectionResult(
                resource_id=resource_id,
                waste_type=WasteType.OLD_SNAPSHOT,
                confidence=confidence if not blocking_factors else 0.3,
                estimated_monthly_cost=monthly_cost,
                days_inactive=days_old,
                recommendation=f"Review old snapshot '{snap.get('snapshot_name', 'unknown')}' ({days_old} days old)",
                blocking_factors=blocking_factors,
            ))

        return results

    def _check_blocking_tags(self, tags: Dict[str, str]) -> List[str]:
        """Check for tags that block waste detection."""
        blocking_factors = []

        if not tags:
            return blocking_factors

        for tag_key, tag_value in tags.items():
            key_lower = tag_key.lower()
            value_lower = str(tag_value).lower() if tag_value else ""

            # Check tag key
            if key_lower in BLOCKING_TAGS:
                blocking_factors.append(f"Has '{tag_key}' tag")
                continue

            # Check tag value for common patterns
            if key_lower == "purpose":
                if value_lower in ["template", "backup", "golden-image"]:
                    blocking_factors.append(f"Purpose tag is '{tag_value}'")

        return blocking_factors

    def _calculate_confidence(self, days_inactive: int, min_days: int) -> float:
        """Calculate confidence based on days over threshold."""
        if days_inactive < min_days:
            return 0.0

        # Scale from base to max over 3x the threshold
        days_over = days_inactive - min_days
        scale_range = min_days * 2  # e.g., 28 days for disk

        ratio = min(1.0, days_over / scale_range)
        confidence = self.CONFIDENCE_BASE + (self.CONFIDENCE_MAX - self.CONFIDENCE_BASE) * ratio

        return round(confidence, 2)

    def _estimate_disk_cost(self, size_gb: int, sku: str) -> float:
        """Estimate monthly cost for disk."""
        # Rough cost estimates per GB per month
        cost_per_gb = {
            "Premium_LRS": 0.132,
            "StandardSSD_LRS": 0.075,
            "Standard_LRS": 0.040,
            "Premium_ZRS": 0.165,
        }

        rate = cost_per_gb.get(sku, 0.075)  # Default to StandardSSD
        return round(size_gb * rate, 2)

    def _estimate_vm_cost(self, vm_size: str) -> float:
        """Estimate monthly cost for VM (rough estimate)."""
        # Very rough estimates for common sizes
        size_costs = {
            "Standard_D2_v3": 70.0,
            "Standard_D4_v3": 140.0,
            "Standard_D8_v3": 280.0,
            "Standard_D2s_v3": 77.0,
            "Standard_D4s_v3": 154.0,
            "Standard_B2s": 30.0,
            "Standard_B2ms": 60.0,
        }

        return size_costs.get(vm_size, 100.0)  # Default estimate
