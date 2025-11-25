#!/usr/bin/env python3
"""
PMP Compliance Analyzer - Rule Evaluation Engine
Automated compliance checking against Essential Eight, CIS, and custom MSP rules

Features:
- Essential Eight Maturity Level 2/3 compliance checks
- CIS Controls 7.1, 7.2, 7.3 validation
- Custom MSP rules (healthy system ratio, scan success rate)
- Automated recommendations for non-compliant items
- Stores compliance results in database for trending

Author: Patch Manager Plus API Specialist Agent + SRE Principal Engineer Agent
Date: 2025-11-25
Version: 1.0
"""

import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class ComplianceResult:
    """Compliance check result"""
    check_name: str
    check_category: str  # 'essential_eight', 'cis', 'custom'
    passed: bool
    severity: str  # 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
    details: str
    threshold_value: float
    actual_value: float


class PMPComplianceAnalyzer:
    """
    Compliance analyzer for PMP configuration data

    Usage:
        analyzer = PMPComplianceAnalyzer()
        results = analyzer.analyze_latest_snapshot()
        print(f"Pass rate: {sum(r.passed for r in results) / len(results) * 100:.1f}%")
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize compliance analyzer

        Args:
            db_path: Path to SQLite database (default: ~/.maia/databases/intelligence/pmp_config.db)
        """
        if db_path is None:
            db_path = Path.home() / ".maia/databases/intelligence/pmp_config.db"

        self.db_path = Path(db_path)

        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")

    def analyze_latest_snapshot(self) -> List[ComplianceResult]:
        """
        Analyze latest snapshot for compliance

        Returns:
            List of compliance check results
        """
        # Get latest snapshot data
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM latest_snapshot")
        snapshot = dict(cursor.fetchone() or {})

        if not snapshot:
            logger.warning("No snapshots available for compliance analysis")
            return []

        snapshot_id = snapshot['snapshot_id']

        # Get vulnerability DB metrics
        cursor.execute("""
            SELECT * FROM vulnerability_db_metrics
            WHERE snapshot_id = ?
        """, (snapshot_id,))
        vuln_db = dict(cursor.fetchone() or {})

        conn.close()

        # Merge data for analysis
        data = {**snapshot, **vuln_db}

        # Run all compliance checks
        results = self.run_all_checks(data)

        # Save results to database
        self._save_compliance_results(snapshot_id, results)

        return results

    def run_all_checks(self, data: Dict) -> List[ComplianceResult]:
        """
        Run all compliance checks against snapshot data

        Args:
            data: Snapshot metrics dictionary

        Returns:
            List of compliance results
        """
        results = []

        # Essential Eight checks
        results.append(self._check_e8_critical_patches(data))
        results.append(self._check_e8_important_patches(data))
        results.append(self._check_e8_vulnerability_rate(data))
        results.append(self._check_e8_scan_coverage(data))
        results.append(self._check_e8_db_update_freshness(data))

        # CIS Controls checks
        results.append(self._check_cis_7_1_scan_deployment(data))
        results.append(self._check_cis_7_2_critical_remediation(data))
        results.append(self._check_cis_7_3_automated_patching(data))

        # Custom MSP checks
        results.append(self._check_healthy_system_ratio(data))
        results.append(self._check_scan_success_rate(data))
        results.append(self._check_unscanned_systems(data))

        return results

    # =========================================================================
    # ESSENTIAL EIGHT COMPLIANCE CHECKS
    # =========================================================================

    def _check_e8_critical_patches(self, data: Dict) -> ComplianceResult:
        """Essential Eight L2/3: Critical patches within 48h (threshold: ≤5)"""
        critical_count = data.get('critical_count', 0)
        threshold = 5
        passed = critical_count <= threshold

        details = (
            f"{'✅ PASS' if passed else '❌ FAIL'}: {critical_count} critical patches found. "
            f"Essential Eight L2/3 requires ≤{threshold} critical patches (48-hour remediation window)."
        )

        return ComplianceResult(
            check_name="Essential Eight: Critical Patches (48h)",
            check_category="essential_eight",
            passed=passed,
            severity="CRITICAL",
            details=details,
            threshold_value=threshold,
            actual_value=critical_count
        )

    def _check_e8_important_patches(self, data: Dict) -> ComplianceResult:
        """Essential Eight L2/3: Important patches within 30 days (threshold: ≤50)"""
        important_count = data.get('important_count', 0)
        threshold = 50
        passed = important_count <= threshold

        details = (
            f"{'✅ PASS' if passed else '❌ FAIL'}: {important_count} important patches found. "
            f"Essential Eight L2/3 requires ≤{threshold} important patches (30-day remediation window)."
        )

        return ComplianceResult(
            check_name="Essential Eight: Important Patches (30 days)",
            check_category="essential_eight",
            passed=passed,
            severity="HIGH",
            details=details,
            threshold_value=threshold,
            actual_value=important_count
        )

    def _check_e8_vulnerability_rate(self, data: Dict) -> ComplianceResult:
        """Essential Eight L2: System vulnerability rate ≤5%"""
        highly_vulnerable = data.get('highly_vulnerable_systems', 0)
        total_systems = data.get('total_systems', 1)
        vulnerability_rate = (highly_vulnerable / total_systems) * 100 if total_systems > 0 else 0
        threshold = 5.0
        passed = vulnerability_rate <= threshold

        details = (
            f"{'✅ PASS' if passed else '❌ FAIL'}: {vulnerability_rate:.1f}% of systems highly vulnerable "
            f"({highly_vulnerable}/{total_systems}). "
            f"Essential Eight L2 requires ≤{threshold}% vulnerability rate."
        )

        return ComplianceResult(
            check_name="Essential Eight: System Vulnerability Rate",
            check_category="essential_eight",
            passed=passed,
            severity="HIGH",
            details=details,
            threshold_value=threshold,
            actual_value=vulnerability_rate
        )

    def _check_e8_scan_coverage(self, data: Dict) -> ComplianceResult:
        """Essential Eight L1: Scan coverage ≥95%"""
        scanned = data.get('scanned_systems', 0)
        total = data.get('total_systems', 1)
        coverage = (scanned / total) * 100 if total > 0 else 0
        threshold = 95.0
        passed = coverage >= threshold

        details = (
            f"{'✅ PASS' if passed else '❌ FAIL'}: {coverage:.1f}% scan coverage ({scanned}/{total} systems). "
            f"Essential Eight L1 requires ≥{threshold}% coverage."
        )

        return ComplianceResult(
            check_name="Essential Eight: Scan Coverage",
            check_category="essential_eight",
            passed=passed,
            severity="MEDIUM",
            details=details,
            threshold_value=threshold,
            actual_value=coverage
        )

    def _check_e8_db_update_freshness(self, data: Dict) -> ComplianceResult:
        """Essential Eight L1: Vulnerability DB updated within 7 days"""
        last_update_time = data.get('last_db_update_time', 0)

        if last_update_time > 0:
            # Convert milliseconds to seconds
            last_update_timestamp = last_update_time / 1000
            age_days = (datetime.now().timestamp() - last_update_timestamp) / 86400
        else:
            age_days = 999  # Unknown = fail

        threshold = 7.0
        passed = age_days <= threshold

        details = (
            f"{'✅ PASS' if passed else '❌ FAIL'}: Vulnerability database updated {age_days:.1f} days ago. "
            f"Essential Eight L1 requires updates within {threshold} days."
        )

        return ComplianceResult(
            check_name="Essential Eight: Vulnerability DB Freshness",
            check_category="essential_eight",
            passed=passed,
            severity="MEDIUM",
            details=details,
            threshold_value=threshold,
            actual_value=age_days
        )

    # =========================================================================
    # CIS CONTROLS COMPLIANCE CHECKS
    # =========================================================================

    def _check_cis_7_1_scan_deployment(self, data: Dict) -> ComplianceResult:
        """CIS Control 7.1: Vulnerability scanning deployed (95% coverage)"""
        scanned = data.get('scanned_systems', 0)
        total = data.get('total_systems', 1)
        coverage = (scanned / total) * 100 if total > 0 else 0
        threshold = 95.0
        passed = coverage >= threshold

        details = (
            f"{'✅ PASS' if passed else '❌ FAIL'}: {coverage:.1f}% scan deployment ({scanned}/{total} systems). "
            f"CIS Control 7.1 requires ≥{threshold}% coverage."
        )

        return ComplianceResult(
            check_name="CIS 7.1: Vulnerability Scanning Deployment",
            check_category="cis",
            passed=passed,
            severity="MEDIUM",
            details=details,
            threshold_value=threshold,
            actual_value=coverage
        )

    def _check_cis_7_2_critical_remediation(self, data: Dict) -> ComplianceResult:
        """CIS Control 7.2: Critical patches remediated (0 critical within 30 days)"""
        critical_count = data.get('critical_count', 0)
        threshold = 0
        passed = critical_count <= threshold

        details = (
            f"{'✅ PASS' if passed else '❌ FAIL'}: {critical_count} critical patches outstanding. "
            f"CIS Control 7.2 requires all critical patches remediated within 30 days."
        )

        return ComplianceResult(
            check_name="CIS 7.2: Critical Patch Remediation",
            check_category="cis",
            passed=passed,
            severity="CRITICAL",
            details=details,
            threshold_value=threshold,
            actual_value=critical_count
        )

    def _check_cis_7_3_automated_patching(self, data: Dict) -> ComplianceResult:
        """CIS Control 7.3: Automated patching enabled (APD tasks > 0)"""
        apd_tasks = data.get('number_of_apd_tasks', 0)
        threshold = 1
        passed = apd_tasks >= threshold

        details = (
            f"{'✅ PASS' if passed else '❌ FAIL'}: {apd_tasks} automated patch deployment tasks active. "
            f"CIS Control 7.3 requires automated patching for critical/high patches."
        )

        return ComplianceResult(
            check_name="CIS 7.3: Automated Patch Deployment",
            check_category="cis",
            passed=passed,
            severity="MEDIUM",
            details=details,
            threshold_value=threshold,
            actual_value=apd_tasks
        )

    # =========================================================================
    # CUSTOM MSP COMPLIANCE CHECKS
    # =========================================================================

    def _check_healthy_system_ratio(self, data: Dict) -> ComplianceResult:
        """Custom MSP: Healthy system ratio ≥60%"""
        healthy = data.get('healthy_systems', 0)
        total = data.get('total_systems', 1)
        ratio = (healthy / total) * 100 if total > 0 else 0
        threshold = 60.0
        passed = ratio >= threshold

        details = (
            f"{'✅ PASS' if passed else '❌ FAIL'}: {ratio:.1f}% healthy systems ({healthy}/{total}). "
            f"MSP standard requires ≥{threshold}% healthy systems."
        )

        return ComplianceResult(
            check_name="Custom MSP: Healthy System Ratio",
            check_category="custom",
            passed=passed,
            severity="MEDIUM",
            details=details,
            threshold_value=threshold,
            actual_value=ratio
        )

    def _check_scan_success_rate(self, data: Dict) -> ComplianceResult:
        """Custom MSP: Scan success rate ≥98%"""
        success = data.get('scan_success_count', 0)
        scanned = data.get('scanned_systems', 1)
        rate = (success / scanned) * 100 if scanned > 0 else 0
        threshold = 98.0
        passed = rate >= threshold

        details = (
            f"{'✅ PASS' if passed else '❌ FAIL'}: {rate:.1f}% scan success rate ({success}/{scanned}). "
            f"MSP standard requires ≥{threshold}% scan reliability."
        )

        return ComplianceResult(
            check_name="Custom MSP: Scan Success Rate",
            check_category="custom",
            passed=passed,
            severity="LOW",
            details=details,
            threshold_value=threshold,
            actual_value=rate
        )

    def _check_unscanned_systems(self, data: Dict) -> ComplianceResult:
        """Custom MSP: Unscanned systems ≤50 (absolute count)"""
        unscanned = data.get('unscanned_system_count', 0)
        threshold = 50
        passed = unscanned <= threshold

        details = (
            f"{'✅ PASS' if passed else '❌ FAIL'}: {unscanned} unscanned systems. "
            f"MSP standard requires ≤{threshold} unscanned systems."
        )

        return ComplianceResult(
            check_name="Custom MSP: Unscanned Systems Limit",
            check_category="custom",
            passed=passed,
            severity="MEDIUM",
            details=details,
            threshold_value=threshold,
            actual_value=unscanned
        )

    # =========================================================================
    # DATABASE OPERATIONS
    # =========================================================================

    def _save_compliance_results(self, snapshot_id: int, results: List[ComplianceResult]):
        """Save compliance check results to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            for result in results:
                cursor.execute("""
                    INSERT INTO compliance_checks (
                        snapshot_id, check_name, check_category, passed, severity,
                        details, threshold_value, actual_value
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    snapshot_id,
                    result.check_name,
                    result.check_category,
                    result.passed,
                    result.severity,
                    result.details,
                    result.threshold_value,
                    result.actual_value
                ))

            conn.commit()

            logger.info("compliance_results_saved", extra={
                "snapshot_id": snapshot_id,
                "checks_saved": len(results),
                "passed_checks": sum(1 for r in results if r.passed)
            })

        except Exception as e:
            conn.rollback()
            logger.error("compliance_save_failed", extra={"error": str(e)})
            raise

        finally:
            conn.close()

    def get_compliance_summary(self) -> Dict:
        """
        Get compliance summary for latest snapshot

        Returns:
            Dictionary with pass rates by category and severity
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM compliance_summary")
        results = [dict(row) for row in cursor.fetchall()]

        conn.close()

        return {
            "summary": results,
            "total_checks": sum(r['total_checks'] for r in results),
            "total_passed": sum(r['passed_checks'] for r in results),
            "overall_pass_rate": (
                sum(r['passed_checks'] for r in results) /
                sum(r['total_checks'] for r in results) * 100
                if sum(r['total_checks'] for r in results) > 0 else 0
            )
        }

    def get_failed_checks(self) -> List[Dict]:
        """Get all failed compliance checks from latest snapshot"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM failed_compliance_checks")
        results = [dict(row) for row in cursor.fetchall()]

        conn.close()

        return results


def main():
    """CLI interface for compliance analyzer"""
    import argparse

    parser = argparse.ArgumentParser(description="PMP Compliance Analyzer")
    parser.add_argument('command', choices=['analyze', 'summary', 'failed'],
                       help='Command to execute')
    parser.add_argument('--db', type=str,
                       help='Path to SQLite database')

    args = parser.parse_args()

    db_path = Path(args.db) if args.db else None
    analyzer = PMPComplianceAnalyzer(db_path=db_path)

    if args.command == 'analyze':
        print("🔍 Analyzing latest snapshot for compliance...")

        try:
            results = analyzer.analyze_latest_snapshot()

            if not results:
                print("❌ No snapshots available for analysis")
                return

            # Summary
            passed = sum(1 for r in results if r.passed)
            total = len(results)
            pass_rate = (passed / total * 100) if total > 0 else 0

            print(f"\n📊 Compliance Analysis Results:")
            print(f"   Total Checks: {total}")
            print(f"   Passed: {passed} ({pass_rate:.1f}%)")
            print(f"   Failed: {total - passed}")

            # By category
            categories = {}
            for r in results:
                if r.check_category not in categories:
                    categories[r.check_category] = {'passed': 0, 'total': 0}
                categories[r.check_category]['total'] += 1
                if r.passed:
                    categories[r.check_category]['passed'] += 1

            print(f"\n📋 By Category:")
            for category, stats in categories.items():
                cat_pass_rate = (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0
                print(f"   {category}: {stats['passed']}/{stats['total']} ({cat_pass_rate:.1f}%)")

            # Failed checks
            failed = [r for r in results if not r.passed]
            if failed:
                print(f"\n❌ Failed Checks ({len(failed)}):")
                for r in failed:
                    print(f"   • [{r.severity}] {r.check_name}")
                    print(f"     {r.details}")

            else:
                print("\n✅ All compliance checks passed!")

        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            import sys
            sys.exit(1)

    elif args.command == 'summary':
        print("📊 Compliance Summary:")
        summary = analyzer.get_compliance_summary()

        print(f"\n   Overall Pass Rate: {summary['overall_pass_rate']:.1f}%")
        print(f"   Total Checks: {summary['total_checks']}")
        print(f"   Passed: {summary['total_passed']}")
        print(f"   Failed: {summary['total_checks'] - summary['total_passed']}")

        print(f"\n   By Category:")
        for item in summary['summary']:
            print(f"   • {item['check_category']} ({item['severity']}): "
                  f"{item['pass_rate']:.1f}% ({item['passed_checks']}/{item['total_checks']})")

    elif args.command == 'failed':
        print("❌ Failed Compliance Checks:")
        failed = analyzer.get_failed_checks()

        if not failed:
            print("   ✅ No failed checks - all compliance requirements met!")
        else:
            for check in failed:
                print(f"\n   • [{check['severity']}] {check['check_name']}")
                print(f"     Category: {check['check_category']}")
                print(f"     {check['details']}")
                print(f"     Threshold: {check['threshold_value']}, Actual: {check['actual_value']}")


if __name__ == '__main__':
    main()
