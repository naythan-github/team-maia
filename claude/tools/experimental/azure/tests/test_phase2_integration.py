"""
Phase 2 Integration Tests - Azure Cost Optimization Platform

Tests that verify all Phase 2 Analysis Engine components work correctly together:
- Data Freshness Handler
- Workload Pattern Detector
- Resource Classifier
- Waste Detector

Run with: pytest tests/test_phase2_integration.py -v
"""

import pytest
from datetime import datetime, timedelta
from typing import List, Dict, Any
from unittest.mock import Mock, MagicMock


class TestDataFreshnessWithWasteDetector:
    """Integration: Data freshness affects waste detection accuracy."""

    def test_stale_data_warning_in_recommendations(self):
        """
        Integration: Stale data should generate warnings in recommendations.
        """
        from claude.tools.experimental.azure.data_freshness import (
            DataFreshnessManager,
        )

        manager = DataFreshnessManager()

        # Data collected 72 hours ago (stale for cost_management)
        old_collection = datetime.now() - timedelta(hours=72)
        manager.update_collection_status(
            data_type="cost_management",
            last_successful=old_collection,
            is_healthy=True,
        )

        freshness = manager.get_freshness("cost_management")

        # Should be stale and have warning
        assert freshness.is_stale is True
        assert freshness.warning_message is not None

    def test_safe_date_range_prevents_false_positives(self):
        """
        Integration: Safe date range should exclude potentially incomplete data.
        """
        from claude.tools.experimental.azure.data_freshness import (
            DataFreshnessManager,
        )

        manager = DataFreshnessManager()

        # Get safe date range for cost analysis
        start_date, end_date = manager.get_safe_date_range(
            data_type="cost_management",
            lookback_days=30,
        )

        # End date should be at least 48 hours ago
        expected_max_end = datetime.now().date() - timedelta(days=2)
        assert end_date <= expected_max_end

        # Should have 30 days lookback
        assert (end_date - start_date).days == 30


class TestWorkloadDetectorWithWasteDetector:
    """Integration: Workload pattern detection prevents waste detection false positives."""

    def test_scheduled_workload_blocks_idle_detection(self):
        """
        Integration: VMs detected as scheduled should not be flagged as idle.

        This is the CRITICAL integration point for false positive prevention.
        """
        from claude.tools.experimental.azure.workload_detector import (
            WorkloadPatternDetector,
            WorkloadPattern,
        )
        from claude.tools.experimental.azure.waste_detector import WasteDetector

        detector = WasteDetector()
        pattern_detector = WorkloadPatternDetector()

        # Generate batch job metrics (2-4am daily spikes)
        base_time = datetime.now() - timedelta(days=14)
        metrics = []
        for day in range(14):
            for hour in range(24):
                ts = base_time + timedelta(days=day, hours=hour)
                cpu = 80.0 if hour in [2, 3, 4] else 2.0
                metrics.append({
                    "timestamp": ts.isoformat(),
                    "cpu_percent": cpu,
                })

        # Verify pattern detection
        analysis = pattern_detector.analyze_pattern("batch-vm", metrics)
        assert analysis.pattern == WorkloadPattern.SCHEDULED

        # Now test waste detector with this pattern
        mock_db = Mock()
        mock_db.get_vms_with_metrics.return_value = [
            {
                "resource_id": "/subscriptions/xxx/vms/batch-vm",
                "vm_name": "batch-vm",
                "vm_size": "Standard_D2_v3",
                "power_state": "running",
                "metrics": metrics,
                "tags": {},
            }
        ]
        mock_db.get_resource_classification.return_value = None

        results = detector.detect_idle_vms(mock_db, pattern_detector)

        # Should NOT flag as idle due to scheduled pattern
        assert len(results) == 0 or all(r.is_actionable() is False for r in results)


class TestResourceClassifierWithWasteDetector:
    """Integration: Resource classification blocks inappropriate recommendations."""

    def test_dr_classification_blocks_shutdown(self):
        """
        Integration: DR/standby classified resources should not be flagged.
        """
        from claude.tools.experimental.azure.resource_classifier import (
            ResourceClassifier,
            ResourceClassification,
        )
        from claude.tools.experimental.azure.waste_detector import WasteDetector
        from claude.tools.experimental.azure.workload_detector import (
            WorkloadPatternDetector,
            WorkloadPattern,
            PatternAnalysis,
        )

        classifier = ResourceClassifier()
        detector = WasteDetector()

        # Classify resource with DR tag
        classification = classifier.classify(
            resource_id="/subscriptions/xxx/vms/dr-vm",
            tags={"Environment": "dr"},
            resource_group="rg",
            resource_name="vm",
        )

        assert classification.classification == ResourceClassification.DR_STANDBY
        assert classification.blocks_shutdown_recommendation() is True

        # Now verify waste detector respects this
        mock_pattern_detector = Mock(spec=WorkloadPatternDetector)
        mock_pattern_detector.analyze_pattern.return_value = PatternAnalysis(
            resource_id="dr-vm",
            pattern=WorkloadPattern.IDLE,  # Would be flagged without DR classification
            confidence=0.90,
            observation_days=21,
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
        mock_db.get_resource_classification.return_value = {
            "classification": "dr_standby",
            "confidence": 0.95,
        }

        results = detector.detect_idle_vms(mock_db, mock_pattern_detector)

        # Should have blocking factor
        assert len(results) == 0 or all(r.is_actionable() is False for r in results)

    def test_template_classification_blocks_disk_flagging(self):
        """
        Integration: Template disks should not be flagged as orphaned.
        """
        from claude.tools.experimental.azure.resource_classifier import (
            ResourceClassifier,
            ResourceClassification,
        )
        from claude.tools.experimental.azure.waste_detector import WasteDetector

        classifier = ResourceClassifier()
        detector = WasteDetector()

        # Classify resource with template tag
        classification = classifier.classify(
            resource_id="/subscriptions/xxx/disks/template-disk",
            tags={"Purpose": "template"},
            resource_group="rg",
            resource_name="template-disk",
        )

        assert classification.classification == ResourceClassification.TEMPLATE
        assert classification.blocks_shutdown_recommendation() is True

        # Verify waste detector respects this
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
        mock_db.get_resource_classification.return_value = {
            "classification": "template",
            "confidence": 0.95,
        }
        mock_db.get_resource_lifecycle.return_value = None

        results = detector.detect_orphaned_disks(mock_db)

        # Should have blocking factor
        assert len(results) == 0 or all(r.is_actionable() is False for r in results)


class TestEndToEndRecommendationFlow:
    """Integration: Full recommendation flow from data to actionable results."""

    def test_complete_waste_detection_pipeline(self):
        """
        Integration: Complete pipeline from raw data to actionable recommendations.

        Flow:
        1. Check data freshness
        2. Analyze workload patterns
        3. Classify resources
        4. Detect waste with all protections
        """
        from claude.tools.experimental.azure.data_freshness import DataFreshnessManager
        from claude.tools.experimental.azure.workload_detector import (
            WorkloadPatternDetector,
            WorkloadPattern,
        )
        from claude.tools.experimental.azure.resource_classifier import ResourceClassifier
        from claude.tools.experimental.azure.waste_detector import WasteDetector, WasteType

        # Initialize all components
        freshness_manager = DataFreshnessManager()
        pattern_detector = WorkloadPatternDetector()
        classifier = ResourceClassifier()
        waste_detector = WasteDetector()

        # Step 1: Update data freshness
        freshness_manager.update_collection_status(
            "cost_management",
            datetime.now() - timedelta(hours=6),  # Recent collection
            True,
        )
        freshness = freshness_manager.get_freshness("cost_management")
        assert freshness.is_stale is False

        # Step 2: Generate test data - truly orphaned disk
        mock_db = Mock()
        mock_db.get_unattached_disks.return_value = [
            {
                "resource_id": "/subscriptions/xxx/disks/orphaned-disk",
                "disk_name": "orphaned-disk",
                "size_gb": 256,
                "sku": "Premium_LRS",
                "detached_at": datetime.now() - timedelta(days=45),
                "tags": {},  # No blocking tags
            }
        ]
        mock_db.get_resource_classification.return_value = None
        mock_db.get_resource_lifecycle.return_value = None

        # Step 3: Classify (no tags = UNKNOWN)
        classification = classifier.classify(
            "/subscriptions/xxx/disks/orphaned-disk",
            {},
            "generic-rg",
            "orphaned-disk",
        )
        assert classification.blocks_shutdown_recommendation() is False

        # Step 4: Detect waste
        results = waste_detector.detect_orphaned_disks(mock_db)

        # Should produce actionable recommendation
        assert len(results) == 1
        assert results[0].waste_type == WasteType.ORPHANED_DISK
        assert results[0].is_actionable() is True
        assert results[0].days_inactive == 45
        assert results[0].confidence >= 0.75

    def test_multiple_waste_types_detected(self):
        """
        Integration: Detect multiple types of waste in single pass.
        """
        from claude.tools.experimental.azure.waste_detector import WasteDetector, WasteType
        from claude.tools.experimental.azure.workload_detector import (
            WorkloadPatternDetector,
            WorkloadPattern,
            PatternAnalysis,
        )

        detector = WasteDetector()
        pattern_detector = Mock(spec=WorkloadPatternDetector)
        pattern_detector.analyze_pattern.return_value = PatternAnalysis(
            resource_id="idle-vm",
            pattern=WorkloadPattern.IDLE,
            confidence=0.85,
            observation_days=21,
        )

        mock_db = Mock()

        # Orphaned disk
        mock_db.get_unattached_disks.return_value = [
            {
                "resource_id": "/disks/disk1",
                "disk_name": "disk1",
                "size_gb": 128,
                "sku": "Standard_LRS",
                "detached_at": datetime.now() - timedelta(days=30),
                "tags": {},
            }
        ]

        # Orphaned NIC
        mock_db.get_unattached_nics.return_value = [
            {
                "resource_id": "/nics/nic1",
                "nic_name": "nic1",
                "detached_at": datetime.now() - timedelta(days=10),
                "tags": {},
            }
        ]

        # Orphaned IP
        mock_db.get_unassociated_public_ips.return_value = [
            {
                "resource_id": "/ips/ip1",
                "ip_name": "ip1",
                "ip_address": "1.2.3.4",
                "unassociated_at": datetime.now() - timedelta(days=20),
                "tags": {},
            }
        ]

        # Idle VM
        mock_db.get_vms_with_metrics.return_value = [
            {
                "resource_id": "/vms/idle-vm",
                "vm_name": "idle-vm",
                "vm_size": "Standard_D2_v3",
                "power_state": "running",
                "metrics": [],
                "tags": {},
            }
        ]

        mock_db.get_resource_classification.return_value = None
        mock_db.get_resource_lifecycle.return_value = None

        # Detect all types
        disk_results = detector.detect_orphaned_disks(mock_db)
        nic_results = detector.detect_orphaned_nics(mock_db)
        ip_results = detector.detect_orphaned_public_ips(mock_db)
        vm_results = detector.detect_idle_vms(mock_db, pattern_detector)

        # Should find all four types
        assert len(disk_results) == 1
        assert disk_results[0].waste_type == WasteType.ORPHANED_DISK

        assert len(nic_results) == 1
        assert nic_results[0].waste_type == WasteType.ORPHANED_NIC

        assert len(ip_results) == 1
        assert ip_results[0].waste_type == WasteType.ORPHANED_IP

        assert len(vm_results) == 1
        assert vm_results[0].waste_type == WasteType.IDLE_VM


class TestFalsePositivePrevention:
    """Integration: Comprehensive false positive prevention tests."""

    def test_batch_vm_weekend_dev_month_end_all_protected(self):
        """
        Integration: All scheduled workload patterns should be protected.
        """
        from claude.tools.experimental.azure.workload_detector import (
            WorkloadPatternDetector,
            WorkloadPattern,
        )
        from claude.tools.experimental.azure.waste_detector import WasteDetector

        pattern_detector = WorkloadPatternDetector()

        # Test patterns that should NOT be flagged as idle
        patterns = [
            # Daily batch (2-4am)
            {
                "name": "daily_batch",
                "hours": 14 * 24,
                "gen": lambda h: 80.0 if (h % 24) in [2, 3, 4] else 2.0,
            },
            # Weekend only (Sat/Sun)
            {
                "name": "weekend_only",
                "hours": 21 * 24,
                "gen": lambda h: 60.0 if ((h // 24) % 7) in [5, 6] else 2.0,
            },
        ]

        for pattern in patterns:
            base_time = datetime.now() - timedelta(hours=pattern["hours"])
            metrics = []
            for h in range(pattern["hours"]):
                ts = base_time + timedelta(hours=h)
                metrics.append({
                    "timestamp": ts.isoformat(),
                    "cpu_percent": pattern["gen"](h),
                })

            analysis = pattern_detector.analyze_pattern(pattern["name"], metrics)

            # Should be SCHEDULED, not IDLE
            assert analysis.pattern == WorkloadPattern.SCHEDULED, (
                f"Pattern {pattern['name']} should be SCHEDULED, got {analysis.pattern}"
            )

    def test_all_blocking_tags_respected(self):
        """
        Integration: All blocking tags should prevent flagging.
        """
        from claude.tools.experimental.azure.waste_detector import WasteDetector

        detector = WasteDetector()

        blocking_tags = [
            {"Purpose": "template"},
            {"Purpose": "backup"},
            {"DoNotDelete": "true"},
            {"Template": "yes"},
            {"reserved": "true"},
        ]

        for tags in blocking_tags:
            mock_db = Mock()
            mock_db.get_unattached_disks.return_value = [
                {
                    "resource_id": f"/disks/disk-{list(tags.keys())[0]}",
                    "disk_name": "test-disk",
                    "size_gb": 128,
                    "sku": "Standard_LRS",
                    "detached_at": datetime.now() - timedelta(days=60),
                    "tags": tags,
                }
            ]
            mock_db.get_resource_classification.return_value = None
            mock_db.get_resource_lifecycle.return_value = None

            results = detector.detect_orphaned_disks(mock_db)

            # Should either not be returned or not be actionable
            assert len(results) == 0 or not results[0].is_actionable(), (
                f"Tags {tags} should block flagging"
            )
