#!/usr/bin/env python3
"""
PMP Compliance Checker - Essential Eight (E8) compliance evaluation

Implements Essential Eight Patch Applications maturity level assessment:
- Level 0: Below minimum compliance thresholds
- Level 1: All patches deployed within 1 month (>80% compliance)
- Level 2: All patches within 2 weeks; critical patches within 48 hours (>90% compliance)
- Level 3: All patches within 48 hours; extreme risk within 24 hours (>95% compliance)

Note: This implementation checks ALL patches rather than filtering by internet-facing
services, as a simplified approach. Production deployments may need additional filtering.

Author: SRE Principal Engineer Agent
Date: 2026-01-15
Sprint: SPRINT-PMP-UNIFIED-001
Phase: P5 - Compliance Checks
"""

import sqlite3
import logging
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PMPComplianceChecker:
    """
    Essential Eight compliance checker for patch management

    Usage:
        checker = PMPComplianceChecker(
            db_path=Path("~/.maia/databases/intelligence/pmp_intelligence.db")
        )
        result = checker.check_compliance(snapshot_id=1)
        print(f"Maturity Level: {result['maturity_level']}")

        report = checker.generate_report(snapshot_id=1)
        print(report)
    """

    # SLA thresholds (in days)
    CRITICAL_SLA_HOURS = 48
    HIGH_SLA_DAYS = 14
    ONE_MONTH_DAYS = 30

    # Severity levels
    SEVERITY_CRITICAL = 4
    SEVERITY_HIGH = 3

    # Maturity level thresholds (percentage)
    LEVEL_3_CRITICAL_THRESHOLD = 95
    LEVEL_3_HIGH_THRESHOLD = 95
    LEVEL_2_CRITICAL_THRESHOLD = 90
    LEVEL_2_HIGH_THRESHOLD = 90
    LEVEL_1_THRESHOLD = 80

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize compliance checker

        Args:
            db_path: Path to PMP intelligence database
                    (default: ~/.maia/databases/intelligence/pmp_intelligence.db)
        """
        if db_path is None:
            db_path = Path.home() / ".maia/databases/intelligence/pmp_intelligence.db"

        self.db_path = Path(db_path)

        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")

        logger.info("pmp_compliance_checker_initialized", extra={
            "db_path": str(self.db_path)
        })

    def check_compliance(self, snapshot_id: int) -> Dict:
        """
        Check Essential Eight compliance for a snapshot

        Args:
            snapshot_id: Snapshot ID to check compliance for

        Returns:
            Dictionary with compliance results:
            {
                'success': bool,
                'snapshot_id': int,
                'maturity_level': int,
                'critical_sla': {
                    'critical_sla_percentage': float,
                    'critical_compliant': int,
                    'critical_total': int,
                    'passed': bool
                },
                'high_sla': {
                    'high_sla_percentage': float,
                    'high_compliant': int,
                    'high_total': int,
                    'passed': bool
                },
                'one_month_compliance': {
                    'one_month_percentage': float,
                    'one_month_compliant': int,
                    'one_month_total': int,
                    'passed': bool
                }
            }
        """
        try:
            logger.info("compliance_check_started", extra={
                "snapshot_id": snapshot_id
            })

            # Check critical patch SLA (48 hours)
            critical_sla = self._check_critical_sla(snapshot_id)

            # Check high patch SLA (2 weeks)
            high_sla = self._check_high_sla(snapshot_id)

            # Check one month compliance (for Level 1)
            one_month_compliance = self._check_one_month_compliance(snapshot_id)

            # Calculate maturity level
            maturity_level = self._calculate_maturity_level(
                critical_sla, high_sla, one_month_compliance
            )

            # Store results in compliance_checks table
            self._store_results(snapshot_id, maturity_level, critical_sla, high_sla, one_month_compliance)

            result = {
                'success': True,
                'snapshot_id': snapshot_id,
                'maturity_level': maturity_level,
                'critical_sla': critical_sla,
                'high_sla': high_sla,
                'one_month_compliance': one_month_compliance
            }

            logger.info("compliance_check_completed", extra={
                "snapshot_id": snapshot_id,
                "maturity_level": maturity_level,
                "critical_sla_percentage": critical_sla['critical_sla_percentage'],
                "high_sla_percentage": high_sla['high_sla_percentage']
            })

            return result

        except Exception as e:
            logger.error("compliance_check_failed", extra={
                "snapshot_id": snapshot_id,
                "error": str(e)
            }, exc_info=True)

            return {
                'success': False,
                'snapshot_id': snapshot_id,
                'error_message': str(e)
            }

    def _check_critical_sla(self, snapshot_id: int) -> Dict:
        """
        Check critical patches applied within 48 hours

        Args:
            snapshot_id: Snapshot ID

        Returns:
            Dictionary with critical SLA results
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Current time in milliseconds
            now_ms = int(datetime.now().timestamp() * 1000)
            sla_threshold_ms = now_ms - int(timedelta(hours=self.CRITICAL_SLA_HOURS).total_seconds() * 1000)

            # Count critical patches released more than 48 hours ago
            cursor.execute("""
                SELECT
                    COUNT(*) as total_critical,
                    COUNT(CASE WHEN installed = 1 THEN 1 END) as installed_critical
                FROM patches
                WHERE snapshot_id = ?
                  AND severity = ?
                  AND patch_released_time IS NOT NULL
                  AND patch_released_time < ?
            """, (snapshot_id, self.SEVERITY_CRITICAL, sla_threshold_ms))

            row = cursor.fetchone()
            total_critical = row[0]
            installed_critical = row[1]

            # Calculate percentage
            if total_critical > 0:
                critical_sla_percentage = round((installed_critical / total_critical) * 100, 2)
            else:
                critical_sla_percentage = 100.0  # No critical patches = 100% compliance

            passed = critical_sla_percentage >= self.LEVEL_2_CRITICAL_THRESHOLD

            return {
                'critical_sla_percentage': critical_sla_percentage,
                'critical_compliant': installed_critical,
                'critical_total': total_critical,
                'passed': passed
            }

        finally:
            conn.close()

    def _check_high_sla(self, snapshot_id: int) -> Dict:
        """
        Check high patches applied within 2 weeks

        Args:
            snapshot_id: Snapshot ID

        Returns:
            Dictionary with high SLA results
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Current time in milliseconds
            now_ms = int(datetime.now().timestamp() * 1000)
            sla_threshold_ms = now_ms - int(timedelta(days=self.HIGH_SLA_DAYS).total_seconds() * 1000)

            # Count high severity patches released more than 2 weeks ago
            cursor.execute("""
                SELECT
                    COUNT(*) as total_high,
                    COUNT(CASE WHEN installed = 1 THEN 1 END) as installed_high
                FROM patches
                WHERE snapshot_id = ?
                  AND severity = ?
                  AND patch_released_time IS NOT NULL
                  AND patch_released_time < ?
            """, (snapshot_id, self.SEVERITY_HIGH, sla_threshold_ms))

            row = cursor.fetchone()
            total_high = row[0]
            installed_high = row[1]

            # Calculate percentage
            if total_high > 0:
                high_sla_percentage = round((installed_high / total_high) * 100, 2)
            else:
                high_sla_percentage = 100.0  # No high patches = 100% compliance

            passed = high_sla_percentage >= self.LEVEL_2_HIGH_THRESHOLD

            return {
                'high_sla_percentage': high_sla_percentage,
                'high_compliant': installed_high,
                'high_total': total_high,
                'passed': passed
            }

        finally:
            conn.close()

    def _check_one_month_compliance(self, snapshot_id: int) -> Dict:
        """
        Check patches applied within one month (for Level 1)

        Note: This checks ALL patches (not limited to internet-facing services)
        as a simplified implementation. In production environments, you may want
        to filter by is_internet_facing if that column is available in your schema.

        Args:
            snapshot_id: Snapshot ID

        Returns:
            Dictionary with one month compliance results
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Current time in milliseconds
            now_ms = int(datetime.now().timestamp() * 1000)
            sla_threshold_ms = now_ms - int(timedelta(days=self.ONE_MONTH_DAYS).total_seconds() * 1000)

            # Count all patches released more than 1 month ago
            cursor.execute("""
                SELECT
                    COUNT(*) as total_patches,
                    COUNT(CASE WHEN installed = 1 THEN 1 END) as installed_patches
                FROM patches
                WHERE snapshot_id = ?
                  AND patch_released_time IS NOT NULL
                  AND patch_released_time < ?
            """, (snapshot_id, sla_threshold_ms))

            row = cursor.fetchone()
            total_patches = row[0]
            installed_patches = row[1]

            # Calculate percentage
            if total_patches > 0:
                one_month_percentage = round((installed_patches / total_patches) * 100, 2)
            else:
                one_month_percentage = 100.0  # No patches = 100% compliance

            passed = one_month_percentage >= self.LEVEL_1_THRESHOLD

            return {
                'one_month_percentage': one_month_percentage,
                'one_month_compliant': installed_patches,
                'one_month_total': total_patches,
                'passed': passed
            }

        finally:
            conn.close()

    def _calculate_maturity_level(self, critical_sla: Dict, high_sla: Dict,
                                   one_month_compliance: Dict) -> int:
        """
        Calculate Essential Eight maturity level based on SLA compliance

        Args:
            critical_sla: Critical SLA results
            high_sla: High SLA results
            one_month_compliance: One month compliance results

        Returns:
            Maturity level (0, 1, 2, or 3)
        """
        critical_pct = critical_sla['critical_sla_percentage']
        high_pct = high_sla['high_sla_percentage']
        one_month_pct = one_month_compliance['one_month_percentage']

        # Level 3: >95% critical in 48h, >95% high in 2 weeks
        if critical_pct >= self.LEVEL_3_CRITICAL_THRESHOLD and high_pct >= self.LEVEL_3_HIGH_THRESHOLD:
            return 3

        # Level 2: >90% critical in 48h, >90% high in 2 weeks
        if critical_pct >= self.LEVEL_2_CRITICAL_THRESHOLD and high_pct >= self.LEVEL_2_HIGH_THRESHOLD:
            return 2

        # Level 1: >80% patches in 1 month
        if one_month_pct >= self.LEVEL_1_THRESHOLD:
            return 1

        # Below Level 1
        return 0

    def _store_results(self, snapshot_id: int, maturity_level: int,
                      critical_sla: Dict, high_sla: Dict, one_month_compliance: Dict):
        """
        Store compliance results in compliance_checks table

        Args:
            snapshot_id: Snapshot ID
            maturity_level: Calculated maturity level
            critical_sla: Critical SLA results
            high_sla: High SLA results
            one_month_compliance: One month compliance results
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Insert maturity level check
            cursor.execute("""
                INSERT INTO compliance_checks (
                    snapshot_id, check_name, check_category, passed, severity,
                    details, threshold_value, actual_value
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                snapshot_id,
                'E8 Patch Applications Maturity Level',
                'essential_eight',
                maturity_level >= 2,  # Pass if Level 2 or higher
                'CRITICAL',
                f'Essential Eight maturity level {maturity_level}',
                2.0,
                float(maturity_level)
            ))

            # Insert critical SLA check
            cursor.execute("""
                INSERT INTO compliance_checks (
                    snapshot_id, check_name, check_category, passed, severity,
                    details, threshold_value, actual_value
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                snapshot_id,
                'Critical Patches - 48 Hour SLA',
                'essential_eight',
                critical_sla['passed'],
                'CRITICAL',
                f"{critical_sla['critical_compliant']}/{critical_sla['critical_total']} critical patches applied within 48 hours",
                float(self.LEVEL_2_CRITICAL_THRESHOLD),
                critical_sla['critical_sla_percentage']
            ))

            # Insert high SLA check
            cursor.execute("""
                INSERT INTO compliance_checks (
                    snapshot_id, check_name, check_category, passed, severity,
                    details, threshold_value, actual_value
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                snapshot_id,
                'High Patches - 2 Week SLA',
                'essential_eight',
                high_sla['passed'],
                'HIGH',
                f"{high_sla['high_compliant']}/{high_sla['high_total']} high severity patches applied within 2 weeks",
                float(self.LEVEL_2_HIGH_THRESHOLD),
                high_sla['high_sla_percentage']
            ))

            # Insert one month compliance check
            cursor.execute("""
                INSERT INTO compliance_checks (
                    snapshot_id, check_name, check_category, passed, severity,
                    details, threshold_value, actual_value
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                snapshot_id,
                'All Patches - 1 Month Compliance',
                'essential_eight',
                one_month_compliance['passed'],
                'MEDIUM',
                f"{one_month_compliance['one_month_compliant']}/{one_month_compliance['one_month_total']} patches applied within 1 month",
                float(self.LEVEL_1_THRESHOLD),
                one_month_compliance['one_month_percentage']
            ))

            conn.commit()

            logger.info("compliance_results_stored", extra={
                "snapshot_id": snapshot_id,
                "maturity_level": maturity_level
            })

        finally:
            conn.close()

    def generate_report(self, snapshot_id: int) -> str:
        """
        Generate human-readable compliance report

        Args:
            snapshot_id: Snapshot ID to generate report for

        Returns:
            Formatted compliance report string
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Get compliance checks for this snapshot
            cursor.execute("""
                SELECT check_name, passed, severity, details, threshold_value, actual_value
                FROM compliance_checks
                WHERE snapshot_id = ?
                  AND check_category = 'essential_eight'
                ORDER BY
                    CASE severity
                        WHEN 'CRITICAL' THEN 1
                        WHEN 'HIGH' THEN 2
                        WHEN 'MEDIUM' THEN 3
                        WHEN 'LOW' THEN 4
                    END
            """, (snapshot_id,))

            rows = cursor.fetchall()

            if not rows:
                return "No compliance data available for this snapshot."

            # Build report
            lines = []
            lines.append("=" * 80)
            lines.append("ESSENTIAL EIGHT (E8) PATCH APPLICATIONS COMPLIANCE REPORT")
            lines.append("=" * 80)
            lines.append("")
            lines.append(f"Snapshot ID: {snapshot_id}")
            lines.append(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append("")

            # Find maturity level
            maturity_level = None
            for row in rows:
                if row[0] == 'E8 Patch Applications Maturity Level':
                    maturity_level = int(row[5])  # actual_value
                    break

            if maturity_level is not None:
                lines.append(f"MATURITY LEVEL: {maturity_level} / 3")
                lines.append("")
                lines.append("Maturity Level Criteria:")
                lines.append("  Level 0: Below minimum compliance thresholds")
                lines.append("  Level 1: All patches deployed within 1 month (>80% compliance)")
                lines.append("  Level 2: All patches within 2 weeks; critical within 48 hours (>90% compliance)")
                lines.append("  Level 3: All patches within 48 hours; extreme risk within 24 hours (>95% compliance)")
                lines.append("")

            lines.append("-" * 80)
            lines.append("COMPLIANCE CHECKS")
            lines.append("-" * 80)
            lines.append("")

            for row in rows:
                check_name, passed, severity, details, threshold_value, actual_value = row

                # Skip the maturity level check (already shown above)
                if check_name == 'E8 Patch Applications Maturity Level':
                    continue

                status_icon = "✓" if passed else "✗"
                status_text = "PASS" if passed else "FAIL"

                lines.append(f"{status_icon} {check_name}")
                lines.append(f"  Status: {status_text}")
                lines.append(f"  Severity: {severity}")
                lines.append(f"  Details: {details}")
                lines.append(f"  Threshold: {threshold_value}%")
                lines.append(f"  Actual: {actual_value}%")
                lines.append("")

            lines.append("=" * 80)

            return "\n".join(lines)

        finally:
            conn.close()


def main():
    """CLI interface for compliance checker"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Essential Eight compliance checker for PMP"
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
        help='Snapshot ID to check compliance for'
    )
    parser.add_argument(
        '--report',
        action='store_true',
        help='Generate human-readable report'
    )

    args = parser.parse_args()

    # Initialize checker
    db_path = Path(args.db_path) if args.db_path else None

    checker = PMPComplianceChecker(db_path=db_path)

    print(f"Checking Essential Eight compliance for snapshot {args.snapshot_id}...")
    result = checker.check_compliance(snapshot_id=args.snapshot_id)

    if result['success']:
        print(f"\n✅ Compliance check completed")
        print(f"\nMaturity Level: {result['maturity_level']} / 3")
        print(f"\nCritical Patches (48 hour SLA):")
        print(f"  - Compliant: {result['critical_sla']['critical_compliant']}/{result['critical_sla']['critical_total']}")
        print(f"  - Percentage: {result['critical_sla']['critical_sla_percentage']}%")
        print(f"  - Status: {'PASS' if result['critical_sla']['passed'] else 'FAIL'}")

        print(f"\nHigh Patches (2 week SLA):")
        print(f"  - Compliant: {result['high_sla']['high_compliant']}/{result['high_sla']['high_total']}")
        print(f"  - Percentage: {result['high_sla']['high_sla_percentage']}%")
        print(f"  - Status: {'PASS' if result['high_sla']['passed'] else 'FAIL'}")

        if args.report:
            print("\n" + "=" * 80)
            print(checker.generate_report(snapshot_id=args.snapshot_id))

        return 0
    else:
        print(f"\n❌ Compliance check failed: {result['error_message']}")
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
