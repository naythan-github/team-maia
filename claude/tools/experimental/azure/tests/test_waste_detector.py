"""
TDD Tests for Azure Waste Detector

Detects orphaned resources with false positive prevention.
Critical for preventing incorrect recommendations.

Tests written BEFORE implementation per TDD protocol.
Run with: pytest tests/test_waste_detector.py -v
"""

import pytest
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from unittest.mock import Mock, MagicMock


class TestWasteTypeEnum:
    """Tests for WasteType enum."""

    def test_waste_type_values(self):
        """WasteType should have all expected values."""
        from claude.tools.experimental.azure.waste_detector import WasteType

        assert WasteType.ORPHANED_DISK.value == "orphaned_disk"
        assert WasteType.ORPHANED_NIC.value == "orphaned_nic"
        assert WasteType.ORPHANED_IP.value == "orphaned_ip"
        assert WasteType.IDLE_VM.value == "idle_vm"
        assert WasteType.STOPPED_VM.value == "stopped_vm"
        assert WasteType.OLD_SNAPSHOT.value == "old_snapshot"
        assert WasteType.EMPTY_RESOURCE_GROUP.value == "empty_resource_group"


class TestWasteDetectionResultDataclass:
    """Tests for WasteDetectionResult dataclass."""

    def test_waste_detection_result_creation(self):
        """WasteDetectionResult should store all fields."""
        from claude.tools.experimental.azure.waste_detector import (
            WasteDetectionResult,
            WasteType,
        )

        result = WasteDetectionResult(
            resource_id="/subscriptions/xxx/resourceGroups/rg/providers/Microsoft.Compute/disks/disk1",
            waste_type=WasteType.ORPHANED_DISK,
            confidence=0.85,
            estimated_monthly_cost=50.0,
            days_inactive=30,
            recommendation="Delete orphaned disk",
            blocking_factors=[],
        )

        assert result.resource_id.endswith("disk1")
        assert result.waste_type == WasteType.ORPHANED_DISK
        assert result.confidence == 0.85
        assert result.estimated_monthly_cost == 50.0
        assert result.days_inactive == 30

    def test_is_actionable_high_confidence_no_blockers(self):
        """Actionable when confidence >= 0.75 and no blocking factors."""
        from claude.tools.experimental.azure.waste_detector import (
            WasteDetectionResult,
            WasteType,
        )

        result = WasteDetectionResult(
            resource_id="test",
            waste_type=WasteType.ORPHANED_DISK,
            confidence=0.80,
            estimated_monthly_cost=25.0,
            days_inactive=20,
            recommendation="Delete",
            blocking_factors=[],
        )

        assert result.is_actionable() is True

    def test_not_actionable_low_confidence(self):
        """Not actionable when confidence < 0.75."""
        from claude.tools.experimental.azure.waste_detector import (
            WasteDetectionResult,
            WasteType,
        )

        result = WasteDetectionResult(
            resource_id="test",
            waste_type=WasteType.ORPHANED_DISK,
            confidence=0.60,
            estimated_monthly_cost=25.0,
            days_inactive=20,
            recommendation="Delete",
            blocking_factors=[],
        )

        assert result.is_actionable() is False

    def test_not_actionable_with_blocking_factors(self):
        """Not actionable when there are blocking factors."""
        from claude.tools.experimental.azure.waste_detector import (
            WasteDetectionResult,
            WasteType,
        )

        result = WasteDetectionResult(
            resource_id="test",
            waste_type=WasteType.ORPHANED_DISK,
            confidence=0.90,
            estimated_monthly_cost=25.0,
            days_inactive=20,
            recommendation="Delete",
            blocking_factors=["Has Template tag"],
        )

        assert result.is_actionable() is False


class TestMinOrphanDaysConstants:
    """Tests for minimum orphan days constants."""

    def test_orphan_days_constants(self):
        """Verify minimum orphan day constants are defined."""
        from claude.tools.experimental.azure.waste_detector import (
            WasteDetector,
            WasteType,
        )

        detector = WasteDetector()

        assert detector.MIN_ORPHAN_DAYS[WasteType.ORPHANED_DISK] == 14
        assert detector.MIN_ORPHAN_DAYS[WasteType.ORPHANED_NIC] == 7
        assert detector.MIN_ORPHAN_DAYS[WasteType.ORPHANED_IP] == 14
        assert detector.MIN_ORPHAN_DAYS[WasteType.IDLE_VM] == 14
        assert detector.MIN_ORPHAN_DAYS[WasteType.OLD_SNAPSHOT] == 90
        assert detector.MIN_ORPHAN_DAYS[WasteType.EMPTY_RESOURCE_GROUP] == 30


class TestOrphanedDiskDetection:
    """Tests for orphaned disk detection."""

    def test_recently_detached_disk_not_flagged(self):
        """Disk detached 3 days ago should not be flagged."""
        from claude.tools.experimental.azure.waste_detector import WasteDetector

        detector = WasteDetector()

        # Mock database with recently detached disk
        mock_db = Mock()
        mock_db.get_unattached_disks.return_value = [
            {
                "resource_id": "/subscriptions/xxx/disks/disk1",
                "disk_name": "disk1",
                "size_gb": 128,
                "sku": "Premium_LRS",
                "detached_at": datetime.now() - timedelta(days=3),
                "tags": {},
            }
        ]
        mock_db.get_resource_classification.return_value = None
        mock_db.get_resource_lifecycle.return_value = None

        results = detector.detect_orphaned_disks(mock_db)

        # Should not be flagged (only 3 days unattached)
        assert len(results) == 0 or all(r.confidence < 0.75 for r in results)

    def test_old_unattached_disk_flagged(self):
        """Disk detached 30 days ago should be flagged."""
        from claude.tools.experimental.azure.waste_detector import (
            WasteDetector,
            WasteType,
        )

        detector = WasteDetector()

        mock_db = Mock()
        mock_db.get_unattached_disks.return_value = [
            {
                "resource_id": "/subscriptions/xxx/disks/disk1",
                "disk_name": "disk1",
                "size_gb": 128,
                "sku": "Premium_LRS",
                "detached_at": datetime.now() - timedelta(days=30),
                "tags": {},
            }
        ]
        mock_db.get_resource_classification.return_value = None
        mock_db.get_resource_lifecycle.return_value = None

        results = detector.detect_orphaned_disks(mock_db)

        assert len(results) == 1
        assert results[0].waste_type == WasteType.ORPHANED_DISK
        assert results[0].confidence >= 0.75
        assert results[0].days_inactive == 30

    def test_template_disk_not_flagged(self):
        """Disk tagged as Template should not be flagged."""
        from claude.tools.experimental.azure.waste_detector import WasteDetector

        detector = WasteDetector()

        mock_db = Mock()
        mock_db.get_unattached_disks.return_value = [
            {
                "resource_id": "/subscriptions/xxx/disks/template-disk",
                "disk_name": "template-disk",
                "size_gb": 128,
                "sku": "Premium_LRS",
                "detached_at": datetime.now() - timedelta(days=60),
                "tags": {"Purpose": "template"},
            }
        ]
        mock_db.get_resource_classification.return_value = None
        mock_db.get_resource_lifecycle.return_value = None

        results = detector.detect_orphaned_disks(mock_db)

        # Should not be flagged due to Template tag
        assert len(results) == 0 or all(r.is_actionable() is False for r in results)

    def test_backup_disk_not_flagged(self):
        """Disk tagged as Backup should not be flagged."""
        from claude.tools.experimental.azure.waste_detector import WasteDetector

        detector = WasteDetector()

        mock_db = Mock()
        mock_db.get_unattached_disks.return_value = [
            {
                "resource_id": "/subscriptions/xxx/disks/backup-disk",
                "disk_name": "backup-disk",
                "size_gb": 256,
                "sku": "Standard_LRS",
                "detached_at": datetime.now() - timedelta(days=45),
                "tags": {"Purpose": "backup"},
            }
        ]
        mock_db.get_resource_classification.return_value = None
        mock_db.get_resource_lifecycle.return_value = None

        results = detector.detect_orphaned_disks(mock_db)

        # Should not be flagged due to Backup tag
        assert len(results) == 0 or all(r.is_actionable() is False for r in results)

    def test_do_not_delete_tag_blocks_flagging(self):
        """Disk with DoNotDelete tag should not be flagged."""
        from claude.tools.experimental.azure.waste_detector import WasteDetector

        detector = WasteDetector()

        mock_db = Mock()
        mock_db.get_unattached_disks.return_value = [
            {
                "resource_id": "/subscriptions/xxx/disks/important-disk",
                "disk_name": "important-disk",
                "size_gb": 512,
                "sku": "Premium_LRS",
                "detached_at": datetime.now() - timedelta(days=90),
                "tags": {"DoNotDelete": "true"},
            }
        ]
        mock_db.get_resource_classification.return_value = None
        mock_db.get_resource_lifecycle.return_value = None

        results = detector.detect_orphaned_disks(mock_db)

        assert len(results) == 0 or all(r.is_actionable() is False for r in results)


class TestIdleVMDetection:
    """Tests for idle VM detection."""

    def test_batch_vm_not_flagged_as_idle(self):
        """VM with scheduled workload pattern should not be flagged as idle."""
        from claude.tools.experimental.azure.waste_detector import WasteDetector
        from claude.tools.experimental.azure.workload_detector import (
            WorkloadPatternDetector,
            WorkloadPattern,
            PatternAnalysis,
        )

        detector = WasteDetector()

        # Mock pattern detector that returns SCHEDULED
        mock_pattern_detector = Mock(spec=WorkloadPatternDetector)
        mock_pattern_detector.analyze_pattern.return_value = PatternAnalysis(
            resource_id="batch-vm",
            pattern=WorkloadPattern.SCHEDULED,
            confidence=0.85,
            observation_days=14,
            peak_hours=[2, 3, 4],
        )

        mock_db = Mock()
        mock_db.get_vms_with_metrics.return_value = [
            {
                "resource_id": "/subscriptions/xxx/vms/batch-vm",
                "vm_name": "batch-vm",
                "vm_size": "Standard_D2_v3",
                "power_state": "running",
                "metrics": [],  # Would have actual metrics
                "tags": {},
            }
        ]
        mock_db.get_resource_classification.return_value = None

        results = detector.detect_idle_vms(mock_db, mock_pattern_detector)

        # Should not be flagged as idle
        assert len(results) == 0 or all(
            r.is_actionable() is False for r in results
        )

    def test_dr_standby_vm_not_flagged(self):
        """VM classified as DR/standby should not be flagged."""
        from claude.tools.experimental.azure.waste_detector import WasteDetector
        from claude.tools.experimental.azure.workload_detector import (
            WorkloadPatternDetector,
            WorkloadPattern,
            PatternAnalysis,
        )
        from claude.tools.experimental.azure.resource_classifier import (
            ResourceClassification,
        )

        detector = WasteDetector()

        mock_pattern_detector = Mock(spec=WorkloadPatternDetector)
        mock_pattern_detector.analyze_pattern.return_value = PatternAnalysis(
            resource_id="dr-vm",
            pattern=WorkloadPattern.IDLE,
            confidence=0.90,
            observation_days=30,
        )

        mock_db = Mock()
        mock_db.get_vms_with_metrics.return_value = [
            {
                "resource_id": "/subscriptions/xxx/vms/dr-vm",
                "vm_name": "dr-vm",
                "vm_size": "Standard_D4_v3",
                "power_state": "running",
                "metrics": [],
                "tags": {"Environment": "dr"},
            }
        ]
        # Return DR classification
        mock_db.get_resource_classification.return_value = {
            "classification": ResourceClassification.DR_STANDBY.value,
            "confidence": 0.95,
        }

        results = detector.detect_idle_vms(mock_db, mock_pattern_detector)

        # Should not be flagged due to DR classification
        assert len(results) == 0 or all(r.is_actionable() is False for r in results)

    def test_truly_idle_vm_flagged(self):
        """VM with 14+ days no activity should be flagged."""
        from claude.tools.experimental.azure.waste_detector import (
            WasteDetector,
            WasteType,
        )
        from claude.tools.experimental.azure.workload_detector import (
            WorkloadPatternDetector,
            WorkloadPattern,
            PatternAnalysis,
        )

        detector = WasteDetector()

        mock_pattern_detector = Mock(spec=WorkloadPatternDetector)
        mock_pattern_detector.analyze_pattern.return_value = PatternAnalysis(
            resource_id="idle-vm",
            pattern=WorkloadPattern.IDLE,
            confidence=0.90,
            observation_days=21,
        )

        mock_db = Mock()
        mock_db.get_vms_with_metrics.return_value = [
            {
                "resource_id": "/subscriptions/xxx/vms/idle-vm",
                "vm_name": "idle-vm",
                "vm_size": "Standard_D2_v3",
                "power_state": "running",
                "metrics": [],
                "tags": {},
            }
        ]
        mock_db.get_resource_classification.return_value = None

        results = detector.detect_idle_vms(mock_db, mock_pattern_detector)

        assert len(results) == 1
        assert results[0].waste_type == WasteType.IDLE_VM
        assert results[0].confidence >= 0.75


class TestConfidenceAndBlockingFactors:
    """Tests for confidence scoring and blocking factors."""

    def test_confidence_reflects_data_quality(self):
        """Confidence should be lower with less observation time."""
        from claude.tools.experimental.azure.waste_detector import WasteDetector

        detector = WasteDetector()

        mock_db = Mock()

        # 14 days - minimum
        mock_db.get_unattached_disks.return_value = [
            {
                "resource_id": "/subscriptions/xxx/disks/disk-14d",
                "disk_name": "disk-14d",
                "size_gb": 128,
                "sku": "Premium_LRS",
                "detached_at": datetime.now() - timedelta(days=14),
                "tags": {},
            }
        ]
        mock_db.get_resource_classification.return_value = None
        mock_db.get_resource_lifecycle.return_value = None

        results_14d = detector.detect_orphaned_disks(mock_db)

        # 60 days - well past threshold
        mock_db.get_unattached_disks.return_value = [
            {
                "resource_id": "/subscriptions/xxx/disks/disk-60d",
                "disk_name": "disk-60d",
                "size_gb": 128,
                "sku": "Premium_LRS",
                "detached_at": datetime.now() - timedelta(days=60),
                "tags": {},
            }
        ]

        results_60d = detector.detect_orphaned_disks(mock_db)

        # Longer orphan period should have higher confidence
        if results_14d and results_60d:
            assert results_60d[0].confidence >= results_14d[0].confidence

    def test_blocking_factors_listed(self):
        """Blocking factors should be listed when present."""
        from claude.tools.experimental.azure.waste_detector import WasteDetector

        detector = WasteDetector()

        mock_db = Mock()
        mock_db.get_unattached_disks.return_value = [
            {
                "resource_id": "/subscriptions/xxx/disks/disk-with-tags",
                "disk_name": "disk-with-tags",
                "size_gb": 128,
                "sku": "Premium_LRS",
                "detached_at": datetime.now() - timedelta(days=30),
                "tags": {"Purpose": "template"},  # Blocking tag
            }
        ]
        mock_db.get_resource_classification.return_value = None
        mock_db.get_resource_lifecycle.return_value = None

        results = detector.detect_orphaned_disks(mock_db)

        if results:
            # Should have blocking factors listed
            assert len(results[0].blocking_factors) > 0
            assert any("template" in f.lower() for f in results[0].blocking_factors)


class TestCostEstimation:
    """Tests for cost estimation."""

    def test_disk_cost_estimated(self):
        """Orphaned disk should have cost estimate."""
        from claude.tools.experimental.azure.waste_detector import WasteDetector

        detector = WasteDetector()

        mock_db = Mock()
        mock_db.get_unattached_disks.return_value = [
            {
                "resource_id": "/subscriptions/xxx/disks/disk1",
                "disk_name": "disk1",
                "size_gb": 128,
                "sku": "Premium_LRS",
                "detached_at": datetime.now() - timedelta(days=30),
                "tags": {},
                "monthly_cost": 45.00,  # If available
            }
        ]
        mock_db.get_resource_classification.return_value = None
        mock_db.get_resource_lifecycle.return_value = None

        results = detector.detect_orphaned_disks(mock_db)

        if results:
            assert results[0].estimated_monthly_cost >= 0


class TestOrphanedNICDetection:
    """Tests for orphaned NIC detection."""

    def test_orphaned_nic_detected(self):
        """Unattached NIC for 7+ days should be flagged."""
        from claude.tools.experimental.azure.waste_detector import (
            WasteDetector,
            WasteType,
        )

        detector = WasteDetector()

        mock_db = Mock()
        mock_db.get_unattached_nics.return_value = [
            {
                "resource_id": "/subscriptions/xxx/nics/nic1",
                "nic_name": "nic1",
                "detached_at": datetime.now() - timedelta(days=10),
                "tags": {},
            }
        ]

        results = detector.detect_orphaned_nics(mock_db)

        assert len(results) == 1
        assert results[0].waste_type == WasteType.ORPHANED_NIC


class TestOrphanedIPDetection:
    """Tests for orphaned public IP detection."""

    def test_orphaned_ip_detected(self):
        """Unassociated public IP for 14+ days should be flagged."""
        from claude.tools.experimental.azure.waste_detector import (
            WasteDetector,
            WasteType,
        )

        detector = WasteDetector()

        mock_db = Mock()
        mock_db.get_unassociated_public_ips.return_value = [
            {
                "resource_id": "/subscriptions/xxx/publicIPAddresses/pip1",
                "ip_name": "pip1",
                "ip_address": "52.123.45.67",
                "unassociated_at": datetime.now() - timedelta(days=20),
                "tags": {},
            }
        ]

        results = detector.detect_orphaned_public_ips(mock_db)

        assert len(results) == 1
        assert results[0].waste_type == WasteType.ORPHANED_IP


class TestOldSnapshotDetection:
    """Tests for old snapshot detection."""

    def test_old_snapshot_detected(self):
        """Snapshot older than 90 days should be flagged."""
        from claude.tools.experimental.azure.waste_detector import (
            WasteDetector,
            WasteType,
        )

        detector = WasteDetector()

        mock_db = Mock()
        mock_db.get_old_snapshots.return_value = [
            {
                "resource_id": "/subscriptions/xxx/snapshots/snap1",
                "snapshot_name": "snap1",
                "source_disk": "/subscriptions/xxx/disks/disk1",
                "created_at": datetime.now() - timedelta(days=120),
                "size_gb": 64,
                "tags": {},
            }
        ]

        results = detector.detect_old_snapshots(mock_db)

        assert len(results) == 1
        assert results[0].waste_type == WasteType.OLD_SNAPSHOT
        assert results[0].days_inactive >= 90
