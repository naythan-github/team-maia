#!/usr/bin/env python3
"""
Automated SRE Health Monitor - Phase 103 Week 3 Task 4

Runs comprehensive daily health checks across all Maia systems:
- Dependency Graph Health (phantom detection)
- RAG System Health (data freshness, availability)
- LaunchAgent Service Health (availability, failures)
- UFC Compliance (structure, naming)

Designed to run via LaunchAgent: com.maia.sre-health-monitor.plist

Usage:
    python3 claude/tools/sre/automated_health_monitor.py
    python3 claude/tools/sre/automated_health_monitor.py --verbose
    python3 claude/tools/sre/automated_health_monitor.py --json report.json
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List


class AutomatedHealthMonitor:
    """Orchestrates daily SRE health checks"""

    def __init__(self, maia_root: Path, verbose: bool = False):
        self.maia_root = maia_root
        self.verbose = verbose
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "overall_health": "UNKNOWN",
            "checks": {},
            "critical_issues": [],
            "warnings": []
        }

    def run_command(self, cmd: List[str], check_name: str) -> Dict:
        """Run a health check command and capture results"""
        try:
            if self.verbose:
                print(f"🔍 Running {check_name}...")

            result = subprocess.run(
                cmd,
                cwd=self.maia_root,
                capture_output=True,
                text=True,
                timeout=60
            )

            return {
                "status": "PASS" if result.returncode == 0 else "FAIL",
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }

        except subprocess.TimeoutExpired:
            return {
                "status": "TIMEOUT",
                "exit_code": -1,
                "stdout": "",
                "stderr": "Command timed out after 60 seconds"
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e)
            }

    def check_dependency_health(self) -> Dict:
        """Run dependency graph validator"""
        tool_path = self.maia_root / "claude/tools/sre/dependency_graph_validator.py"

        if not tool_path.exists():
            return {
                "status": "SKIP",
                "reason": "Tool not found",
                "health_score": 0
            }

        result = self.run_command(
            ["python3", str(tool_path), "--analyze", "--critical-only"],
            "Dependency Health Check"
        )

        # Parse output for health score and critical phantoms
        critical_phantoms = 0
        health_score = 0

        if "Dependency Health Score:" in result["stdout"]:
            for line in result["stdout"].split("\n"):
                if "Dependency Health Score:" in line:
                    try:
                        health_score = float(line.split(":")[1].split("/")[0].strip())
                    except:
                        pass
                elif "Critical Phantoms:" in line:
                    try:
                        critical_phantoms = int(line.split(":")[1].strip().split()[0])
                    except:
                        pass

        result["health_score"] = health_score
        result["critical_phantoms"] = critical_phantoms

        if critical_phantoms > 0:
            self.results["critical_issues"].append(
                f"Dependency Health: {critical_phantoms} critical phantom dependencies found"
            )

        return result

    def check_rag_health(self) -> Dict:
        """Run RAG system health monitor"""
        tool_path = self.maia_root / "claude/tools/sre/rag_system_health_monitor.py"

        if not tool_path.exists():
            return {
                "status": "SKIP",
                "reason": "Tool not found",
                "health_score": 0
            }

        result = self.run_command(
            ["python3", str(tool_path), "--dashboard"],
            "RAG System Health Check"
        )

        # Parse output for health score
        health_score = 0
        overall_status = "UNKNOWN"

        if "Health Score:" in result["stdout"]:
            for line in result["stdout"].split("\n"):
                if "Health Score:" in line:
                    try:
                        health_score = float(line.split(":")[1].strip().rstrip("%"))
                    except:
                        pass
                elif "Overall Health:" in line:
                    overall_status = line.split(":")[1].strip()

        result["health_score"] = health_score
        result["overall_status"] = overall_status

        if overall_status in ["DEGRADED", "CRITICAL"]:
            self.results["warnings"].append(
                f"RAG Health: System status is {overall_status} ({health_score}% healthy)"
            )

        return result

    def check_service_health(self) -> Dict:
        """Run LaunchAgent health monitor"""
        tool_path = self.maia_root / "claude/tools/sre/launchagent_health_monitor.py"

        if not tool_path.exists():
            return {
                "status": "SKIP",
                "reason": "Tool not found",
                "availability": 0
            }

        result = self.run_command(
            ["python3", str(tool_path), "--dashboard"],
            "Service Health Check"
        )

        # Parse output for availability
        availability = 0
        failed_count = 0

        if "Service Availability:" in result["stdout"]:
            for line in result["stdout"].split("\n"):
                if "Service Availability:" in line:
                    try:
                        availability = float(line.split(":")[1].strip().rstrip("%"))
                    except:
                        pass
                elif "Failed:" in line:
                    try:
                        failed_count = int(line.split(":")[1].strip().split()[0])
                    except:
                        pass

        result["availability"] = availability
        result["failed_count"] = failed_count

        if failed_count > 0:
            self.results["critical_issues"].append(
                f"Service Health: {failed_count} LaunchAgent service(s) failed"
            )

        if availability < 50.0:
            self.results["warnings"].append(
                f"Service Health: Low availability ({availability}%, target 99.9%)"
            )

        return result

    def check_ufc_compliance(self) -> Dict:
        """Run UFC compliance checker"""
        tool_path = self.maia_root / "claude/tools/security/ufc_compliance_checker.py"

        if not tool_path.exists():
            return {
                "status": "SKIP",
                "reason": "Tool not found",
                "compliant": False
            }

        result = self.run_command(
            ["python3", str(tool_path), "--check"],
            "UFC Compliance Check"
        )

        # Parse output for compliance status
        compliant = result["exit_code"] == 0
        violations_count = 0

        if "Violations (Critical/High):" in result["stdout"]:
            for line in result["stdout"].split("\n"):
                if "Violations (Critical/High):" in line:
                    try:
                        violations_count = int(line.split(":")[1].strip())
                    except:
                        pass

        result["compliant"] = compliant
        result["violations_count"] = violations_count

        if violations_count > 0:
            self.results["warnings"].append(
                f"UFC Compliance: {violations_count} critical/high violations found"
            )

        return result

    def check_backup_health(self) -> Dict:
        """Check disaster recovery backup system health"""
        # Detect OneDrive path
        onedrive_path = self._detect_onedrive_path()
        if not onedrive_path:
            return {
                "status": "CRITICAL",
                "message": "OneDrive path not found",
                "last_backup": None,
                "age_hours": None
            }

        backup_dir = Path(onedrive_path) / "MaiaBackups"

        if not backup_dir.exists():
            return {
                "status": "CRITICAL",
                "message": "Backup directory not found",
                "last_backup": None,
                "age_hours": None
            }

        # Find latest backup
        manifests = list(backup_dir.glob("*/backup_manifest.json"))
        if not manifests:
            return {
                "status": "CRITICAL",
                "message": "No backups found",
                "last_backup": None,
                "age_hours": None
            }

        latest_manifest = max(manifests, key=lambda p: p.stat().st_mtime)
        try:
            with open(latest_manifest) as f:
                manifest = json.load(f)
        except Exception as e:
            return {
                "status": "ERROR",
                "message": f"Failed to read manifest: {e}",
                "last_backup": None,
                "age_hours": None
            }

        created_at = datetime.fromisoformat(manifest['created_at'])
        age_hours = (datetime.now() - created_at).total_seconds() / 3600

        # Determine status
        if age_hours > 36:
            status = "CRITICAL"
            message = f"Backup is {age_hours:.1f} hours old (target: <36h)"
            self.results["critical_issues"].append(
                f"Disaster Recovery: Backup age {age_hours:.1f}h exceeds 36h threshold"
            )
        elif age_hours > 25:
            status = "WARNING"
            message = f"Backup is {age_hours:.1f} hours old (approaching threshold)"
            self.results["warnings"].append(
                f"Disaster Recovery: Backup age {age_hours:.1f}h approaching 36h threshold"
            )
        else:
            status = "PASS"
            message = f"Backup is {age_hours:.1f} hours old"

        return {
            "status": status,
            "message": message,
            "last_backup": manifest['backup_id'],
            "age_hours": round(age_hours, 1),
            "size_mb": self._calculate_backup_size_mb(latest_manifest.parent),
            "components": len(manifest.get('components', {})),
            "onedrive_synced": manifest.get('onedrive_sync_verified', False)
        }

    def _detect_onedrive_path(self) -> str:
        """Auto-detect OneDrive path"""
        import os

        # Priority order
        if os.environ.get('MAIA_ONEDRIVE_PATH'):
            return os.environ['MAIA_ONEDRIVE_PATH']

        cloudstorage = Path.home() / "Library" / "CloudStorage"
        if cloudstorage.exists():
            onedrive_dirs = list(cloudstorage.glob("OneDrive-*"))
            if onedrive_dirs:
                for od in onedrive_dirs:
                    if 'ORROPTYLTD' in od.name:
                        return str(od)
                return str(onedrive_dirs[0])

        onedrive_home = Path.home() / "OneDrive"
        if onedrive_home.exists():
            return str(onedrive_home)

        return None

    def _calculate_backup_size_mb(self, backup_path: Path) -> float:
        """Calculate total backup size in MB"""
        total_bytes = sum(f.stat().st_size for f in backup_path.glob('*') if f.is_file())
        return round(total_bytes / (1024 * 1024), 1)

    def determine_overall_health(self):
        """Calculate overall system health status"""
        critical_count = len(self.results["critical_issues"])
        warning_count = len(self.results["warnings"])

        if critical_count > 0:
            self.results["overall_health"] = "CRITICAL"
        elif warning_count > 5:
            self.results["overall_health"] = "DEGRADED"
        elif warning_count > 0:
            self.results["overall_health"] = "WARNING"
        else:
            self.results["overall_health"] = "HEALTHY"

    def run_all_checks(self) -> Dict:
        """Execute all health checks"""
        print("=" * 70)
        print("🏥 MAIA SRE AUTOMATED HEALTH MONITOR")
        print("=" * 70)
        print(f"📅 Timestamp: {self.results['timestamp']}")
        print()

        # Check 1: Dependency Health
        print("📊 [1/4] Checking Dependency Health...")
        self.results["checks"]["dependency_health"] = self.check_dependency_health()
        dep_status = self.results["checks"]["dependency_health"]["status"]
        print(f"   {'✅' if dep_status == 'PASS' else '⚠️ ' if dep_status == 'SKIP' else '❌'} {dep_status}")
        if "health_score" in self.results["checks"]["dependency_health"]:
            print(f"   Health Score: {self.results['checks']['dependency_health']['health_score']}/100")
        print()

        # Check 2: RAG System Health
        print("🧠 [2/4] Checking RAG System Health...")
        self.results["checks"]["rag_health"] = self.check_rag_health()
        rag_status = self.results["checks"]["rag_health"]["status"]
        print(f"   {'✅' if rag_status == 'PASS' else '⚠️ ' if rag_status == 'SKIP' else '❌'} {rag_status}")
        if "health_score" in self.results["checks"]["rag_health"]:
            print(f"   Health Score: {self.results['checks']['rag_health']['health_score']}%")
        print()

        # Check 3: Service Health
        print("🔧 [3/4] Checking LaunchAgent Service Health...")
        self.results["checks"]["service_health"] = self.check_service_health()
        svc_status = self.results["checks"]["service_health"]["status"]
        print(f"   {'✅' if svc_status == 'PASS' else '⚠️ ' if svc_status == 'SKIP' else '❌'} {svc_status}")
        if "availability" in self.results["checks"]["service_health"]:
            print(f"   Availability: {self.results['checks']['service_health']['availability']}%")
        print()

        # Check 4: UFC Compliance
        print("📏 [4/5] Checking UFC Compliance...")
        self.results["checks"]["ufc_compliance"] = self.check_ufc_compliance()
        ufc_status = self.results["checks"]["ufc_compliance"]["status"]
        print(f"   {'✅' if ufc_status == 'PASS' else '⚠️ ' if ufc_status == 'SKIP' else '❌'} {ufc_status}")
        if "compliant" in self.results["checks"]["ufc_compliance"]:
            compliant = self.results["checks"]["ufc_compliance"]["compliant"]
            print(f"   Compliant: {compliant}")
        print()

        # Check 5: Backup Health
        print("💾 [5/5] Checking Disaster Recovery Backup Health...")
        self.results["checks"]["backup_health"] = self.check_backup_health()
        backup_status = self.results["checks"]["backup_health"]["status"]
        print(f"   {'✅' if backup_status == 'PASS' else '⚠️ ' if backup_status == 'WARNING' else '❌'} {backup_status}")
        if "age_hours" in self.results["checks"]["backup_health"] and self.results["checks"]["backup_health"]["age_hours"]:
            age_hours = self.results["checks"]["backup_health"]["age_hours"]
            print(f"   Backup Age: {age_hours}h (threshold: 36h)")
        if "last_backup" in self.results["checks"]["backup_health"] and self.results["checks"]["backup_health"]["last_backup"]:
            print(f"   Last Backup: {self.results['checks']['backup_health']['last_backup']}")
        if "size_mb" in self.results["checks"]["backup_health"]:
            print(f"   Size: {self.results['checks']['backup_health']['size_mb']} MB")
        print()

        # Determine overall health
        self.determine_overall_health()

        print("=" * 70)
        health_emoji = {
            "HEALTHY": "✅",
            "WARNING": "⚠️ ",
            "DEGRADED": "⚠️ ",
            "CRITICAL": "🔴"
        }.get(self.results["overall_health"], "❓")

        print(f"{health_emoji} OVERALL HEALTH: {self.results['overall_health']}")
        print("=" * 70)
        print()

        # Show critical issues
        if self.results["critical_issues"]:
            print("🚨 CRITICAL ISSUES:")
            for issue in self.results["critical_issues"]:
                print(f"   🔴 {issue}")
            print()

        # Show warnings
        if self.results["warnings"]:
            print("⚠️  WARNINGS:")
            for warning in self.results["warnings"][:5]:  # Limit to 5
                print(f"   ⚠️  {warning}")
            if len(self.results["warnings"]) > 5:
                print(f"   ... and {len(self.results['warnings']) - 5} more warnings")
            print()

        print("📝 Run individual tools for detailed diagnostics:")
        print("   • python3 claude/tools/sre/dependency_graph_validator.py --analyze")
        print("   • python3 claude/tools/sre/rag_system_health_monitor.py --dashboard")
        print("   • python3 claude/tools/sre/launchagent_health_monitor.py --dashboard")
        print("   • python3 claude/tools/security/ufc_compliance_checker.py --check")
        print()

        return self.results


def main():
    parser = argparse.ArgumentParser(
        description="Automated SRE Health Monitor - Daily system health checks"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed output"
    )
    parser.add_argument(
        "--json",
        type=str,
        metavar="FILE",
        help="Export results to JSON file"
    )
    # Import MAIA_ROOT for default
    import os
    from claude.tools.core.paths import MAIA_ROOT as DEFAULT_MAIA_ROOT

    parser.add_argument(
        "--maia-root",
        type=str,
        default=os.environ.get("MAIA_ROOT", str(DEFAULT_MAIA_ROOT)),
        help="Path to Maia root directory"
    )

    args = parser.parse_args()

    maia_root = Path(args.maia_root)
    if not maia_root.exists():
        print(f"❌ Error: MAIA_ROOT not found: {maia_root}")
        return 1

    monitor = AutomatedHealthMonitor(maia_root, verbose=args.verbose)
    results = monitor.run_all_checks()

    # Export to JSON if requested
    if args.json:
        output_path = Path(args.json)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"📄 Results exported to: {output_path}")

    # Exit code based on overall health
    if results["overall_health"] == "CRITICAL":
        return 2
    elif results["overall_health"] in ["DEGRADED", "WARNING"]:
        return 1
    else:
        return 0


if __name__ == "__main__":
    sys.exit(main())
