#!/usr/bin/env python3
"""
PMP Metrics Calculator - Calculate derived metrics from raw PMP data

Calculates:
- Patch metrics: missing/installed/applicable counts
- Severity metrics: critical/high/medium/low breakdown
- System health metrics: healthy/vulnerable/unknown systems

Operates on unified schema data, storing results in metrics tables.

Author: SRE Principal Engineer Agent
Date: 2026-01-15
Sprint: SPRINT-PMP-UNIFIED-001
Phase: P2 - Metrics Calculation Engine
"""

import sqlite3
import logging
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PMPMetricsCalculator:
    """
    Calculate derived metrics from PMP data

    Usage:
        calculator = PMPMetricsCalculator(
            db_path=Path("~/.maia/databases/intelligence/pmp_intelligence.db")
        )
        result = calculator.calculate_all(snapshot_id=1)
        print(f"Calculated metrics: {result}")
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize metrics calculator

        Args:
            db_path: Path to PMP intelligence database
                    (default: ~/.maia/databases/intelligence/pmp_intelligence.db)
        """
        if db_path is None:
            db_path = Path.home() / ".maia/databases/intelligence/pmp_intelligence.db"

        self.db_path = Path(db_path)

        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")

        logger.info("pmp_metrics_calculator_initialized", extra={
            "db_path": str(self.db_path)
        })

    def calculate_all(self, snapshot_id: int) -> Dict:
        """
        Calculate all metrics for a snapshot

        Args:
            snapshot_id: Snapshot ID to calculate metrics for

        Returns:
            Dictionary with results:
            {
                'success': bool,
                'snapshot_id': int,
                'patch_metrics': dict,
                'severity_metrics': dict,
                'system_health_metrics': dict,
                'duration_ms': int
            }
        """
        start_time = datetime.now()

        conn = None
        try:
            logger.info("metrics_calculation_started", extra={
                "snapshot_id": snapshot_id
            })

            # Open connection with transaction
            conn = sqlite3.connect(self.db_path)
            conn.execute("BEGIN TRANSACTION")

            # Delete existing metrics for this snapshot (idempotency)
            self._delete_existing_metrics(conn, snapshot_id)

            # Calculate each metric type
            patch_metrics = self._calculate_patch_metrics(conn, snapshot_id)
            severity_metrics = self._calculate_severity_metrics(conn, snapshot_id)
            health_metrics = self._calculate_system_health_metrics(conn, snapshot_id)

            # Commit transaction
            conn.commit()

            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            logger.info("metrics_calculation_completed", extra={
                "snapshot_id": snapshot_id,
                "duration_ms": duration_ms
            })

            return {
                'success': True,
                'snapshot_id': snapshot_id,
                'patch_metrics': patch_metrics,
                'severity_metrics': severity_metrics,
                'system_health_metrics': health_metrics,
                'duration_ms': duration_ms
            }

        except Exception as e:
            if conn:
                conn.rollback()

            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            logger.error("metrics_calculation_failed", extra={
                "snapshot_id": snapshot_id,
                "error": str(e),
                "duration_ms": duration_ms
            }, exc_info=True)

            return {
                'success': False,
                'snapshot_id': snapshot_id,
                'patch_metrics': None,
                'severity_metrics': None,
                'system_health_metrics': None,
                'error_message': str(e),
                'duration_ms': duration_ms
            }

        finally:
            if conn:
                conn.close()

    def _delete_existing_metrics(self, conn: sqlite3.Connection, snapshot_id: int):
        """
        Delete existing metrics for snapshot (for idempotency)

        Args:
            conn: Database connection
            snapshot_id: Snapshot ID
        """
        cursor = conn.cursor()

        # Gracefully handle tables that might not exist yet
        try:
            cursor.execute("DELETE FROM patch_metrics WHERE snapshot_id = ?", (snapshot_id,))
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("DELETE FROM severity_metrics WHERE snapshot_id = ?", (snapshot_id,))
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("DELETE FROM system_health_metrics WHERE snapshot_id = ?", (snapshot_id,))
        except sqlite3.OperationalError:
            pass

        logger.debug("existing_metrics_deleted", extra={
            "snapshot_id": snapshot_id
        })

    def _calculate_patch_metrics(self, conn: sqlite3.Connection, snapshot_id: int) -> Dict:
        """
        Calculate patch metrics: missing/installed/applicable

        Args:
            conn: Database connection
            snapshot_id: Snapshot ID

        Returns:
            Dictionary with patch metrics
        """
        cursor = conn.cursor()

        # Count installed patches (from patches table)
        cursor.execute("""
            SELECT COUNT(*) FROM patches
            WHERE snapshot_id = ? AND installed = 1
        """, (snapshot_id,))
        installed_patches = cursor.fetchone()[0]

        # Count applicable patches (from patch_system_mapping)
        cursor.execute("""
            SELECT COUNT(*) FROM patch_system_mapping
            WHERE snapshot_id = ?
        """, (snapshot_id,))
        applicable_patches = cursor.fetchone()[0]

        # Count missing patches (from patch_system_mapping where patch_status = 0)
        # This is the accurate count of patches that are missing on systems
        cursor.execute("""
            SELECT COUNT(*) FROM patch_system_mapping
            WHERE snapshot_id = ? AND patch_status = 0
        """, (snapshot_id,))
        missing_patches = cursor.fetchone()[0]

        # New patches (same as missing for now - patches that need to be applied)
        new_patches = missing_patches

        # Insert metrics
        cursor.execute("""
            INSERT INTO patch_metrics (
                snapshot_id,
                installed_patches,
                applicable_patches,
                new_patches,
                missing_patches
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            snapshot_id,
            installed_patches,
            applicable_patches,
            new_patches,
            missing_patches
        ))

        metrics = {
            'installed_patches': installed_patches,
            'applicable_patches': applicable_patches,
            'new_patches': new_patches,
            'missing_patches': missing_patches
        }

        logger.info("patch_metrics_calculated", extra={
            "snapshot_id": snapshot_id,
            "metrics": metrics
        })

        return metrics

    def _calculate_severity_metrics(self, conn: sqlite3.Connection, snapshot_id: int) -> Dict:
        """
        Calculate severity metrics: critical/high/medium/low

        Severity mapping (from PMP):
        - 4 = Critical
        - 3 = Important (High)
        - 2 = Moderate (Medium)
        - 1 = Low
        - NULL/0 = Unrated

        Args:
            conn: Database connection
            snapshot_id: Snapshot ID

        Returns:
            Dictionary with severity metrics
        """
        cursor = conn.cursor()

        # Count by severity (from patch_system_mapping)
        cursor.execute("""
            SELECT
                COUNT(CASE WHEN severity = 4 THEN 1 END) as critical_count,
                COUNT(CASE WHEN severity = 3 THEN 1 END) as important_count,
                COUNT(CASE WHEN severity = 2 THEN 1 END) as moderate_count,
                COUNT(CASE WHEN severity = 1 THEN 1 END) as low_count,
                COUNT(CASE WHEN severity IS NULL OR severity = 0 THEN 1 END) as unrated_count,
                COUNT(*) as total_count
            FROM patch_system_mapping
            WHERE snapshot_id = ?
        """, (snapshot_id,))

        row = cursor.fetchone()
        critical_count = row[0]
        important_count = row[1]
        moderate_count = row[2]
        low_count = row[3]
        unrated_count = row[4]
        total_count = row[5]

        # Insert metrics
        cursor.execute("""
            INSERT INTO severity_metrics (
                snapshot_id,
                critical_count,
                important_count,
                moderate_count,
                low_count,
                unrated_count,
                total_count
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            snapshot_id,
            critical_count,
            important_count,
            moderate_count,
            low_count,
            unrated_count,
            total_count
        ))

        metrics = {
            'critical_count': critical_count,
            'important_count': important_count,
            'moderate_count': moderate_count,
            'low_count': low_count,
            'unrated_count': unrated_count,
            'total_count': total_count
        }

        logger.info("severity_metrics_calculated", extra={
            "snapshot_id": snapshot_id,
            "metrics": metrics
        })

        return metrics

    def _calculate_system_health_metrics(self, conn: sqlite3.Connection, snapshot_id: int) -> Dict:
        """
        Calculate system health metrics: healthy/vulnerable/unknown

        Health status mapping (from PMP):
        - 1 = Healthy
        - 2 = Moderately Vulnerable
        - 3 = Highly Vulnerable
        - 0/NULL = Unknown

        Args:
            conn: Database connection
            snapshot_id: Snapshot ID

        Returns:
            Dictionary with system health metrics
        """
        cursor = conn.cursor()

        # Count by health status (from systems table)
        cursor.execute("""
            SELECT
                COUNT(*) as total_systems,
                COUNT(CASE WHEN resource_health_status = 1 THEN 1 END) as healthy_systems,
                COUNT(CASE WHEN resource_health_status = 2 THEN 1 END) as moderately_vulnerable_systems,
                COUNT(CASE WHEN resource_health_status = 3 THEN 1 END) as highly_vulnerable_systems,
                COUNT(CASE WHEN resource_health_status IS NULL OR resource_health_status = 0 THEN 1 END) as health_unknown_systems
            FROM systems
            WHERE snapshot_id = ?
        """, (snapshot_id,))

        row = cursor.fetchone()
        total_systems = row[0]
        healthy_systems = row[1]
        moderately_vulnerable_systems = row[2]
        highly_vulnerable_systems = row[3]
        health_unknown_systems = row[4]

        # Placeholder values for scan/task metrics (future enhancement)
        scanned_systems = 0
        unscanned_system_count = 0
        scan_success_count = 0
        scan_failure_count = 0
        number_of_apd_tasks = 0

        # Insert metrics
        cursor.execute("""
            INSERT INTO system_health_metrics (
                snapshot_id,
                total_systems,
                healthy_systems,
                moderately_vulnerable_systems,
                highly_vulnerable_systems,
                health_unknown_systems,
                scanned_systems,
                unscanned_system_count,
                scan_success_count,
                scan_failure_count,
                number_of_apd_tasks
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            snapshot_id,
            total_systems,
            healthy_systems,
            moderately_vulnerable_systems,
            highly_vulnerable_systems,
            health_unknown_systems,
            scanned_systems,
            unscanned_system_count,
            scan_success_count,
            scan_failure_count,
            number_of_apd_tasks
        ))

        metrics = {
            'total_systems': total_systems,
            'healthy_systems': healthy_systems,
            'moderately_vulnerable_systems': moderately_vulnerable_systems,
            'highly_vulnerable_systems': highly_vulnerable_systems,
            'health_unknown_systems': health_unknown_systems,
            'scanned_systems': scanned_systems,
            'unscanned_system_count': unscanned_system_count,
            'scan_success_count': scan_success_count,
            'scan_failure_count': scan_failure_count,
            'number_of_apd_tasks': number_of_apd_tasks
        }

        logger.info("system_health_metrics_calculated", extra={
            "snapshot_id": snapshot_id,
            "metrics": metrics
        })

        return metrics


def main():
    """CLI interface for metrics calculator"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Calculate PMP metrics from unified database"
    )
    parser.add_argument(
        '--db-path',
        type=str,
        help='Database path (default: ~/.maia/databases/intelligence/pmp_intelligence.db)'
    )
    parser.add_argument(
        '--snapshot-id',
        type=int,
        required=True,
        help='Snapshot ID to calculate metrics for'
    )

    args = parser.parse_args()

    # Initialize calculator
    db_path = Path(args.db_path) if args.db_path else None

    calculator = PMPMetricsCalculator(db_path=db_path)

    print(f"🔄 Calculating metrics for snapshot {args.snapshot_id}...")
    result = calculator.calculate_all(snapshot_id=args.snapshot_id)

    if result['success']:
        print(f"\n✅ Metrics calculated successfully")
        print(f"\nPatch Metrics:")
        print(f"  - Installed: {result['patch_metrics']['installed_patches']}")
        print(f"  - Missing: {result['patch_metrics']['missing_patches']}")
        print(f"  - Applicable: {result['patch_metrics']['applicable_patches']}")
        print(f"  - New: {result['patch_metrics']['new_patches']}")

        print(f"\nSeverity Metrics:")
        print(f"  - Critical: {result['severity_metrics']['critical_count']}")
        print(f"  - Important: {result['severity_metrics']['important_count']}")
        print(f"  - Moderate: {result['severity_metrics']['moderate_count']}")
        print(f"  - Low: {result['severity_metrics']['low_count']}")
        print(f"  - Unrated: {result['severity_metrics']['unrated_count']}")
        print(f"  - Total: {result['severity_metrics']['total_count']}")

        print(f"\nSystem Health Metrics:")
        print(f"  - Total Systems: {result['system_health_metrics']['total_systems']}")
        print(f"  - Healthy: {result['system_health_metrics']['healthy_systems']}")
        print(f"  - Moderately Vulnerable: {result['system_health_metrics']['moderately_vulnerable_systems']}")
        print(f"  - Highly Vulnerable: {result['system_health_metrics']['highly_vulnerable_systems']}")
        print(f"  - Unknown: {result['system_health_metrics']['health_unknown_systems']}")

        print(f"\nDuration: {result['duration_ms']}ms")
        return 0
    else:
        print(f"\n❌ Metrics calculation failed: {result['error_message']}")
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
