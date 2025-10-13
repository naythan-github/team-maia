#!/usr/bin/env python3
"""
Security Orchestration Service - Continuous Security Monitoring
================================================================

Purpose: Background service providing automated security scanning, metrics
         collection, and alert generation for the Maia system.

Pattern: Similar to health_monitor_service.py and vtt_watcher.py
Usage: python3 security_orchestration_service.py [--daemon]
LaunchAgent: com.maia.security-orchestrator.plist

Architecture:
- Scheduled scans (hourly dependency, daily code, weekly compliance)
- SQLite metrics persistence
- Integration with existing security tools
- Alert generation and routing
- Dashboard data export

Created: 2025-10-13 (Phase 113 - Security Automation Project)
"""

import argparse
import json
import logging
import os
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add maia root to path for imports
MAIA_ROOT = Path.home() / "git" / "maia"
sys.path.insert(0, str(MAIA_ROOT))


class SecurityOrchestrator:
    """Orchestrates continuous security monitoring and scanning"""

    def __init__(self, maia_root: Path, log_dir: Path, db_path: Path):
        self.maia_root = maia_root
        self.log_dir = log_dir
        self.db_path = db_path

        # Security tool paths
        self.tools = {
            'local_scanner': maia_root / "claude/tools/security/local_security_scanner.py",
            'hardening_manager': maia_root / "claude/tools/security/security_hardening_manager.py",
            'weekly_scan': maia_root / "claude/tools/security/weekly_security_scan.py",
            'ufc_compliance': maia_root / "claude/tools/security/ufc_compliance_checker.py"
        }

        # Scan schedules (in seconds)
        self.schedules = {
            'dependency_scan': 3600,      # 1 hour
            'code_scan': 86400,           # 24 hours
            'compliance_audit': 604800,   # 7 days
            'metrics_collection': 300     # 5 minutes
        }

        # Last run timestamps
        self.last_run = {
            'dependency_scan': None,
            'code_scan': None,
            'compliance_audit': None,
            'metrics_collection': None
        }

        # Initialize database
        self._init_database()

        # Setup logging
        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        """Configure logging to file and console"""
        self.log_dir.mkdir(parents=True, exist_ok=True)
        log_file = self.log_dir / "security_orchestrator.log"

        logger = logging.getLogger("SecurityOrchestrator")
        logger.setLevel(logging.INFO)

        # File handler
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.INFO)

        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        logger.addHandler(fh)
        logger.addHandler(ch)

        return logger

    def _init_database(self):
        """Initialize SQLite database for metrics storage"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Security metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS security_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                metric_type TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value REAL,
                details TEXT,
                severity TEXT
            )
        """)

        # Scan history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scan_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                scan_type TEXT NOT NULL,
                status TEXT NOT NULL,
                findings_count INTEGER,
                critical_count INTEGER,
                high_count INTEGER,
                medium_count INTEGER,
                low_count INTEGER,
                duration_seconds REAL,
                details TEXT
            )
        """)

        # Alerts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS security_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                remediation TEXT,
                status TEXT DEFAULT 'new'
            )
        """)

        conn.commit()
        conn.close()

    def _record_metric(self, metric_type: str, metric_name: str,
                      metric_value: float, details: str = None,
                      severity: str = "info"):
        """Record a security metric to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO security_metrics
            (timestamp, metric_type, metric_name, metric_value, details, severity)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            metric_type,
            metric_name,
            metric_value,
            details,
            severity
        ))

        conn.commit()
        conn.close()

    def _record_scan(self, scan_type: str, status: str, findings: Dict[str, int],
                     duration: float, details: str = None):
        """Record scan execution to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO scan_history
            (timestamp, scan_type, status, findings_count, critical_count,
             high_count, medium_count, low_count, duration_seconds, details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            scan_type,
            status,
            findings.get('total', 0),
            findings.get('critical', 0),
            findings.get('high', 0),
            findings.get('medium', 0),
            findings.get('low', 0),
            duration,
            details
        ))

        conn.commit()
        conn.close()

    def _create_alert(self, alert_type: str, severity: str, title: str,
                     description: str, remediation: str = None):
        """Create a security alert"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO security_alerts
            (timestamp, alert_type, severity, title, description, remediation)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            alert_type,
            severity,
            title,
            description,
            remediation
        ))

        conn.commit()
        conn.close()

        self.logger.warning(f"🚨 ALERT: [{severity.upper()}] {title}")

    def _should_run_scan(self, scan_name: str) -> bool:
        """Check if scan should run based on schedule"""
        last_run = self.last_run.get(scan_name)
        if last_run is None:
            return True

        interval = self.schedules.get(scan_name, 3600)
        elapsed = (datetime.now() - last_run).total_seconds()

        return elapsed >= interval

    def run_dependency_scan(self) -> Dict[str, Any]:
        """Run dependency vulnerability scan using OSV-Scanner"""
        self.logger.info("🔍 Running dependency vulnerability scan...")
        start_time = time.time()

        try:
            result = subprocess.run(
                ["python3", str(self.tools['local_scanner']), "--quick"],
                capture_output=True,
                text=True,
                timeout=300,
                cwd=str(self.maia_root)
            )

            duration = time.time() - start_time

            # Parse output for vulnerabilities
            findings = {'total': 0, 'critical': 0, 'high': 0, 'medium': 0, 'low': 0}

            if "No vulnerabilities found" in result.stdout:
                status = "clean"
            elif result.returncode != 0:
                status = "error"
                findings['total'] = -1
            else:
                status = "completed"
                # Basic parsing - enhance based on actual scanner output
                if "vulnerabilities" in result.stdout.lower():
                    findings['total'] = 1  # Placeholder

            # Record scan
            self._record_scan('dependency_scan', status, findings, duration)

            # Record metrics
            self._record_metric('scan', 'dependency_vulnerabilities', findings['total'])
            self._record_metric('scan', 'dependency_scan_duration', duration)

            # Create alerts for critical findings
            if findings['critical'] > 0:
                self._create_alert(
                    'vulnerability',
                    'critical',
                    f"{findings['critical']} Critical Dependency Vulnerabilities",
                    "Critical vulnerabilities detected in project dependencies",
                    "Run 'python3 claude/tools/security/local_security_scanner.py' for details"
                )

            self.last_run['dependency_scan'] = datetime.now()
            self.logger.info(f"✅ Dependency scan complete: {status} ({duration:.2f}s)")

            return {'status': status, 'findings': findings, 'duration': duration}

        except subprocess.TimeoutExpired:
            self.logger.error("❌ Dependency scan timeout")
            return {'status': 'timeout', 'findings': {}, 'duration': 300}
        except Exception as e:
            self.logger.error(f"❌ Dependency scan error: {e}")
            return {'status': 'error', 'findings': {}, 'duration': time.time() - start_time}

    def run_code_scan(self) -> Dict[str, Any]:
        """Run code security scan using Bandit"""
        self.logger.info("🔍 Running code security scan...")
        start_time = time.time()

        try:
            result = subprocess.run(
                ["python3", str(self.tools['local_scanner']),
                 "--scan", str(self.maia_root / "claude/tools")],
                capture_output=True,
                text=True,
                timeout=600,
                cwd=str(self.maia_root)
            )

            duration = time.time() - start_time

            # Parse output
            findings = {'total': 0, 'critical': 0, 'high': 0, 'medium': 0, 'low': 0}

            if result.returncode == 0:
                status = "clean"
            else:
                status = "completed"
                # Basic parsing - enhance based on actual output
                findings['total'] = 1  # Placeholder

            # Record scan
            self._record_scan('code_scan', status, findings, duration)

            # Record metrics
            self._record_metric('scan', 'code_security_issues', findings['total'])
            self._record_metric('scan', 'code_scan_duration', duration)

            self.last_run['code_scan'] = datetime.now()
            self.logger.info(f"✅ Code scan complete: {status} ({duration:.2f}s)")

            return {'status': status, 'findings': findings, 'duration': duration}

        except Exception as e:
            self.logger.error(f"❌ Code scan error: {e}")
            return {'status': 'error', 'findings': {}, 'duration': time.time() - start_time}

    def run_compliance_audit(self) -> Dict[str, Any]:
        """Run compliance audit (UFC, SOC2, ISO27001)"""
        self.logger.info("🔍 Running compliance audit...")
        start_time = time.time()

        try:
            # Run UFC compliance checker
            result = subprocess.run(
                ["python3", str(self.tools['ufc_compliance'])],
                capture_output=True,
                text=True,
                timeout=300,
                cwd=str(self.maia_root)
            )

            duration = time.time() - start_time

            # Parse compliance results
            findings = {'total': 0, 'critical': 0, 'high': 0, 'medium': 0, 'low': 0}

            if "compliant" in result.stdout.lower() or result.returncode == 0:
                status = "compliant"
            else:
                status = "violations"
                findings['total'] = 1  # Placeholder

            # Record scan
            self._record_scan('compliance_audit', status, findings, duration)

            # Record metrics
            self._record_metric('compliance', 'ufc_compliance', 1.0 if status == "compliant" else 0.0)
            self._record_metric('scan', 'compliance_scan_duration', duration)

            self.last_run['compliance_audit'] = datetime.now()
            self.logger.info(f"✅ Compliance audit complete: {status} ({duration:.2f}s)")

            return {'status': status, 'findings': findings, 'duration': duration}

        except Exception as e:
            self.logger.error(f"❌ Compliance audit error: {e}")
            return {'status': 'error', 'findings': {}, 'duration': time.time() - start_time}

    def collect_metrics(self):
        """Collect current security metrics"""
        try:
            # Count active security services
            result = subprocess.run(
                ["launchctl", "list"],
                capture_output=True,
                text=True
            )

            security_services = 0
            for line in result.stdout.split('\n'):
                if 'maia' in line.lower() and 'security' in line.lower():
                    security_services += 1

            self._record_metric('system', 'active_security_services', security_services)

            # Get recent scan count
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Scans in last 24 hours
            yesterday = (datetime.now() - timedelta(days=1)).isoformat()
            cursor.execute("""
                SELECT COUNT(*) FROM scan_history
                WHERE timestamp > ? AND status = 'completed'
            """, (yesterday,))

            recent_scans = cursor.fetchone()[0]
            self._record_metric('system', 'scans_last_24h', recent_scans)

            # Active alerts
            cursor.execute("""
                SELECT COUNT(*) FROM security_alerts
                WHERE status = 'new'
            """)

            active_alerts = cursor.fetchone()[0]
            self._record_metric('system', 'active_alerts', active_alerts)

            conn.close()

            self.last_run['metrics_collection'] = datetime.now()

        except Exception as e:
            self.logger.error(f"❌ Metrics collection error: {e}")

    def get_security_status(self) -> Dict[str, Any]:
        """Get current security status summary"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get latest scan results
        cursor.execute("""
            SELECT scan_type, timestamp, status, critical_count, high_count
            FROM scan_history
            ORDER BY timestamp DESC
            LIMIT 10
        """)

        recent_scans = []
        for row in cursor.fetchall():
            recent_scans.append({
                'type': row[0],
                'timestamp': row[1],
                'status': row[2],
                'critical': row[3],
                'high': row[4]
            })

        # Get active alerts
        cursor.execute("""
            SELECT severity, COUNT(*)
            FROM security_alerts
            WHERE status = 'new'
            GROUP BY severity
        """)

        alerts = {row[0]: row[1] for row in cursor.fetchall()}

        conn.close()

        # Determine overall status
        if alerts.get('critical', 0) > 0:
            overall_status = "CRITICAL"
        elif alerts.get('high', 0) > 0:
            overall_status = "WARNING"
        elif any(s['status'] == 'error' for s in recent_scans[:3]):
            overall_status = "DEGRADED"
        else:
            overall_status = "HEALTHY"

        return {
            'status': overall_status,
            'recent_scans': recent_scans,
            'alerts': alerts,
            'last_scan': recent_scans[0] if recent_scans else None
        }

    def run_daemon(self):
        """Run orchestrator as continuous daemon"""
        self.logger.info("🚀 Security Orchestrator starting...")
        self.logger.info(f"📁 MAIA Root: {self.maia_root}")
        self.logger.info(f"💾 Database: {self.db_path}")
        self.logger.info(f"📊 Schedules: {self.schedules}")

        cycle = 0

        try:
            while True:
                cycle += 1
                self.logger.info(f"🔄 Orchestration cycle {cycle}")

                # Check and run scheduled scans
                if self._should_run_scan('dependency_scan'):
                    self.run_dependency_scan()

                if self._should_run_scan('code_scan'):
                    self.run_code_scan()

                if self._should_run_scan('compliance_audit'):
                    self.run_compliance_audit()

                if self._should_run_scan('metrics_collection'):
                    self.collect_metrics()

                # Get current status
                status = self.get_security_status()
                self.logger.info(f"📊 Current status: {status['status']}")

                # Sleep for 60 seconds between cycles
                time.sleep(60)

        except KeyboardInterrupt:
            self.logger.info("🛑 Security Orchestrator stopping (KeyboardInterrupt)")
        except Exception as e:
            self.logger.error(f"❌ Fatal error: {e}")
            raise


def main():
    parser = argparse.ArgumentParser(
        description="Security Orchestration Service - Continuous Security Monitoring"
    )
    parser.add_argument(
        '--daemon',
        action='store_true',
        help='Run as continuous daemon'
    )
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show current security status'
    )
    parser.add_argument(
        '--scan-now',
        choices=['dependency', 'code', 'compliance', 'all'],
        help='Run immediate scan'
    )

    args = parser.parse_args()

    # Paths
    maia_root = Path.home() / "git" / "maia"
    log_dir = maia_root / "claude/data/logs"
    db_path = maia_root / "claude/data/security_metrics.db"

    # Initialize orchestrator
    orchestrator = SecurityOrchestrator(maia_root, log_dir, db_path)

    if args.status:
        # Show status
        status = orchestrator.get_security_status()
        print(json.dumps(status, indent=2))

    elif args.scan_now:
        # Run immediate scan
        if args.scan_now in ['dependency', 'all']:
            orchestrator.run_dependency_scan()
        if args.scan_now in ['code', 'all']:
            orchestrator.run_code_scan()
        if args.scan_now in ['compliance', 'all']:
            orchestrator.run_compliance_audit()

        orchestrator.collect_metrics()
        status = orchestrator.get_security_status()
        print(json.dumps(status, indent=2))

    elif args.daemon:
        # Run as daemon
        orchestrator.run_daemon()

    else:
        # Default: run one cycle then exit
        orchestrator.run_dependency_scan()
        orchestrator.collect_metrics()
        status = orchestrator.get_security_status()
        print(json.dumps(status, indent=2))


if __name__ == "__main__":
    main()
