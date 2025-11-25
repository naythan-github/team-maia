#!/usr/bin/env python3
"""
PMP Configuration Extractor - Main Extraction Engine
Production-grade ManageEngine Patch Manager Plus configuration extraction with SQLite storage

Features:
- OAuth 2.0 integration (reuses pmp_oauth_manager.py from Phase 187)
- SQLite historical snapshot storage
- Data validation (schema, ranges, consistency)
- Error handling (401, 403, 429, 500) with retry logic
- Structured logging with metrics
- Rate limiting compliance (3000 req/5min)

Author: Patch Manager Plus API Specialist Agent + SRE Principal Engineer Agent
Date: 2025-11-25
Version: 1.0
"""

import sqlite3
import json
import time
import logging
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import sys

# Import existing OAuth manager from Phase 187
try:
    from claude.tools.pmp.pmp_oauth_manager import PMPOAuthManager
except ImportError:
    # Try relative import if absolute import fails
    try:
        from pmp_oauth_manager import PMPOAuthManager
    except ImportError:
        print("Error: pmp_oauth_manager.py not found. Ensure Phase 187 is complete.")
        sys.exit(1)

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class SnapshotData:
    """Data structure for a complete PMP configuration snapshot"""
    # Patch metrics
    installed_patches: int
    applicable_patches: int
    new_patches: int
    missing_patches: int

    # Severity metrics
    critical_count: int
    important_count: int
    moderate_count: int
    low_count: int
    unrated_count: int
    total_count: int

    # System health metrics
    total_systems: int
    healthy_systems: int
    moderately_vulnerable_systems: int
    highly_vulnerable_systems: int
    health_unknown_systems: int
    scanned_systems: int
    unscanned_system_count: int
    scan_success_count: int
    scan_failure_count: int
    number_of_apd_tasks: int

    # Vulnerability DB metrics
    last_db_update_status: str
    last_db_update_time: int
    is_auto_db_update_disabled: bool
    db_update_in_progress: bool

    # Metadata
    extraction_duration_ms: int
    api_version: str = '1.4'


class PMPConfigExtractor:
    """
    ManageEngine PMP configuration extractor with SQLite storage

    Usage:
        extractor = PMPConfigExtractor()
        snapshot_id = extractor.extract_snapshot()
        print(f"Extracted snapshot {snapshot_id}")
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize extractor with OAuth manager and database

        Args:
            db_path: Path to SQLite database (default: ~/.maia/databases/intelligence/pmp_config.db)
        """
        # Initialize OAuth manager (reuse from Phase 187)
        self.oauth_manager = PMPOAuthManager()

        # Database path
        if db_path is None:
            db_path = Path.home() / ".maia/databases/intelligence/pmp_config.db"
        self.db_path = Path(db_path)

        # Ensure database directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database schema
        self.init_database()

        # Consecutive failure tracking (for alerting)
        self.consecutive_failures = 0

        logger.info("pmp_config_extractor_initialized", extra={
            "db_path": str(self.db_path),
            "oauth_configured": True
        })

    def init_database(self):
        """Initialize database schema from SQL file"""
        schema_file = Path(__file__).parent / "pmp_db_schema.sql"

        if not schema_file.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_file}")

        # Read and execute schema
        schema_sql = schema_file.read_text()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Execute schema (handles IF NOT EXISTS, so safe to run multiple times)
        cursor.executescript(schema_sql)

        conn.commit()
        conn.close()

        # Set file permissions (owner read/write only)
        self.db_path.chmod(0o600)

        logger.info("database_schema_initialized", extra={
            "db_path": str(self.db_path),
            "schema_version": 1
        })

    def extract_snapshot(self) -> Optional[int]:
        """
        Extract complete configuration snapshot from PMP API

        Returns:
            snapshot_id if successful, None if failed

        Raises:
            RuntimeError: If extraction fails after retries
        """
        start_time = time.time()
        snapshot_id = None
        status = 'failed'
        error_message = None

        try:
            logger.info("extraction_started")

            # Call PMP API /api/1.4/patch/summary
            response = self.oauth_manager.api_request('GET', '/api/1.4/patch/summary')

            if response.status_code != 200:
                raise RuntimeError(f"API returned {response.status_code}: {response.text[:200]}")

            # Parse response
            data = response.json()

            # Extract summary data
            summary = data['message_response']['summary']

            # Build snapshot data structure
            snapshot_data = SnapshotData(
                # Patch metrics
                installed_patches=summary['patch_summary']['installed_patches'],
                applicable_patches=summary['patch_summary']['applicable_patches'],
                new_patches=summary['patch_summary']['new_patches'],
                missing_patches=summary['patch_summary']['missing_patches'],

                # Severity metrics
                critical_count=summary['missing_patch_severity_summary']['critical_count'],
                important_count=summary['missing_patch_severity_summary']['important_count'],
                moderate_count=summary['missing_patch_severity_summary']['moderate_count'],
                low_count=summary['missing_patch_severity_summary']['low_count'],
                unrated_count=summary['missing_patch_severity_summary']['unrated_count'],
                total_count=summary['missing_patch_severity_summary']['total_count'],

                # System health metrics
                total_systems=summary['system_summary']['total_systems'],
                healthy_systems=summary['system_summary']['healthy_systems'],
                moderately_vulnerable_systems=summary['system_summary']['moderately_vulnerable_systems'],
                highly_vulnerable_systems=summary['system_summary']['highly_vulnerable_systems'],
                health_unknown_systems=summary['system_summary']['health_unknown_systems'],
                scanned_systems=summary['patch_scan_summary']['scanned_systems'],
                unscanned_system_count=summary['patch_scan_summary']['unscanned_system_count'],
                scan_success_count=summary['patch_scan_summary']['scan_success_count'],
                scan_failure_count=summary['patch_scan_summary']['scan_failure_count'],
                number_of_apd_tasks=summary['apd_summary']['number_of_apd_tasks'],

                # Vulnerability DB metrics
                last_db_update_status=summary['vulnerability_db_summary']['last_db_update_status'],
                last_db_update_time=summary['vulnerability_db_summary']['last_db_update_time'],
                is_auto_db_update_disabled=summary['vulnerability_db_summary']['is_auto_db_update_disabled'],
                db_update_in_progress=summary['vulnerability_db_summary']['db_update_in_progress'],

                # Metadata
                extraction_duration_ms=int((time.time() - start_time) * 1000)
            )

            # Validate data
            if not self.validate_data(snapshot_data):
                raise ValueError("Data validation failed")

            # Save to database
            snapshot_id = self.save_snapshot(snapshot_data)
            status = 'success'

            # Reset consecutive failure counter
            self.consecutive_failures = 0

            logger.info("extraction_success", extra={
                "snapshot_id": snapshot_id,
                "duration_ms": snapshot_data.extraction_duration_ms,
                "missing_patches": snapshot_data.missing_patches,
                "critical_count": snapshot_data.critical_count
            })

            return snapshot_id

        except Exception as e:
            error_message = str(e)
            status = 'failed'
            self.consecutive_failures += 1

            logger.error("extraction_failed", extra={
                "error": error_message,
                "consecutive_failures": self.consecutive_failures
            }, exc_info=True)

            # Create failed snapshot record for audit trail
            duration_ms = int((time.time() - start_time) * 1000)
            snapshot_id = self.create_snapshot(status='failed', duration_ms=duration_ms, error_message=error_message)

            # Alert if 3 consecutive failures
            if self.consecutive_failures >= 3:
                logger.critical("consecutive_extraction_failures", extra={
                    "count": self.consecutive_failures,
                    "alert": "CRITICAL"
                })

            raise

    def validate_data(self, data: SnapshotData) -> bool:
        """
        Validate snapshot data for schema compliance and consistency

        Args:
            data: Snapshot data to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            # Schema validation: All required fields present (handled by dataclass)

            # Range validation: All counts >= 0
            if any(getattr(data, field) < 0 for field in [
                'installed_patches', 'applicable_patches', 'new_patches', 'missing_patches',
                'critical_count', 'important_count', 'moderate_count', 'low_count', 'unrated_count', 'total_count',
                'total_systems', 'healthy_systems', 'moderately_vulnerable_systems', 'highly_vulnerable_systems',
                'health_unknown_systems', 'scanned_systems', 'unscanned_system_count',
                'scan_success_count', 'scan_failure_count', 'number_of_apd_tasks'
            ]):
                logger.error("validation_failed_negative_count")
                return False

            # Consistency validation: Severity counts sum to total
            severity_sum = (data.critical_count + data.important_count + data.moderate_count +
                          data.low_count + data.unrated_count)
            if data.total_count != severity_sum:
                logger.error("validation_failed_severity_sum_mismatch", extra={
                    "total_count": data.total_count,
                    "severity_sum": severity_sum
                })
                return False

            # Consistency validation: System health counts don't exceed total
            health_sum = (data.healthy_systems + data.moderately_vulnerable_systems +
                        data.highly_vulnerable_systems + data.health_unknown_systems)
            if health_sum > data.total_systems:
                logger.error("validation_failed_health_sum_exceeds_total", extra={
                    "total_systems": data.total_systems,
                    "health_sum": health_sum
                })
                return False

            # Consistency validation: Scanned + unscanned <= total systems
            scan_sum = data.scanned_systems + data.unscanned_system_count
            if scan_sum > data.total_systems:
                logger.error("validation_failed_scan_sum_exceeds_total", extra={
                    "total_systems": data.total_systems,
                    "scan_sum": scan_sum
                })
                return False

            return True

        except Exception as e:
            logger.error("validation_error", extra={"error": str(e)})
            return False

    def save_snapshot(self, data: SnapshotData) -> int:
        """
        Save complete snapshot to database

        Args:
            data: Validated snapshot data

        Returns:
            snapshot_id of created snapshot
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Create snapshot record
            cursor.execute("""
                INSERT INTO snapshots (api_version, extraction_duration_ms, status)
                VALUES (?, ?, ?)
            """, (data.api_version, data.extraction_duration_ms, 'success'))

            snapshot_id = cursor.lastrowid

            # Insert patch metrics
            cursor.execute("""
                INSERT INTO patch_metrics (
                    snapshot_id, installed_patches, applicable_patches, new_patches, missing_patches
                ) VALUES (?, ?, ?, ?, ?)
            """, (snapshot_id, data.installed_patches, data.applicable_patches, data.new_patches, data.missing_patches))

            # Insert severity metrics
            cursor.execute("""
                INSERT INTO severity_metrics (
                    snapshot_id, critical_count, important_count, moderate_count, low_count, unrated_count, total_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (snapshot_id, data.critical_count, data.important_count, data.moderate_count,
                 data.low_count, data.unrated_count, data.total_count))

            # Insert system health metrics
            cursor.execute("""
                INSERT INTO system_health_metrics (
                    snapshot_id, total_systems, healthy_systems, moderately_vulnerable_systems,
                    highly_vulnerable_systems, health_unknown_systems, scanned_systems,
                    unscanned_system_count, scan_success_count, scan_failure_count, number_of_apd_tasks
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (snapshot_id, data.total_systems, data.healthy_systems, data.moderately_vulnerable_systems,
                 data.highly_vulnerable_systems, data.health_unknown_systems, data.scanned_systems,
                 data.unscanned_system_count, data.scan_success_count, data.scan_failure_count, data.number_of_apd_tasks))

            # Insert vulnerability DB metrics
            cursor.execute("""
                INSERT INTO vulnerability_db_metrics (
                    snapshot_id, last_db_update_status, last_db_update_time,
                    is_auto_db_update_disabled, db_update_in_progress
                ) VALUES (?, ?, ?, ?, ?)
            """, (snapshot_id, data.last_db_update_status, data.last_db_update_time,
                 data.is_auto_db_update_disabled, data.db_update_in_progress))

            conn.commit()

            logger.info("snapshot_saved", extra={
                "snapshot_id": snapshot_id,
                "tables_inserted": 4  # patch, severity, system_health, vuln_db
            })

            return snapshot_id

        except Exception as e:
            conn.rollback()
            logger.error("snapshot_save_failed", extra={"error": str(e)})
            raise

        finally:
            conn.close()

    def create_snapshot(self, status: str, duration_ms: int, error_message: Optional[str] = None) -> int:
        """
        Create snapshot record (for failed extractions)

        Args:
            status: 'success', 'partial', or 'failed'
            duration_ms: Extraction duration in milliseconds
            error_message: Error message if status = 'failed'

        Returns:
            snapshot_id
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO snapshots (api_version, extraction_duration_ms, status, error_message)
                VALUES (?, ?, ?, ?)
            """, ('1.4', duration_ms, status, error_message))

            snapshot_id = cursor.lastrowid
            conn.commit()

            return snapshot_id

        finally:
            conn.close()

    def get_latest_snapshot(self) -> Optional[Dict]:
        """
        Get most recent successful snapshot

        Returns:
            Dictionary with snapshot data or None if no snapshots exist
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT * FROM latest_snapshot")
            row = cursor.fetchone()

            if row:
                return dict(row)
            return None

        finally:
            conn.close()

    def get_trend_data(self, days: int = 30) -> List[Dict]:
        """
        Get trend data for specified number of days

        Args:
            days: Number of days to retrieve (default: 30)

        Returns:
            List of dictionaries with snapshot data
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT
                    s.snapshot_id,
                    s.timestamp,
                    pm.missing_patches,
                    sm.critical_count,
                    sm.important_count,
                    shm.healthy_systems,
                    shm.highly_vulnerable_systems,
                    shm.total_systems
                FROM snapshots s
                LEFT JOIN patch_metrics pm ON s.snapshot_id = pm.snapshot_id
                LEFT JOIN severity_metrics sm ON s.snapshot_id = sm.snapshot_id
                LEFT JOIN system_health_metrics shm ON s.snapshot_id = shm.snapshot_id
                WHERE s.status = 'success'
                  AND s.timestamp >= datetime('now', '-' || ? || ' days')
                ORDER BY s.timestamp ASC
            """, (days,))

            return [dict(row) for row in cursor.fetchall()]

        finally:
            conn.close()

    def should_alert_consecutive_failures(self) -> bool:
        """Check if consecutive failure threshold reached"""
        return self.consecutive_failures >= 3


def main():
    """CLI interface for config extractor"""
    import argparse

    parser = argparse.ArgumentParser(description="PMP Configuration Extractor")
    parser.add_argument('command', choices=['extract', 'latest', 'trend', 'test'],
                       help='Command to execute')
    parser.add_argument('--days', type=int, default=30,
                       help='Number of days for trend data (default: 30)')
    parser.add_argument('--db', type=str,
                       help='Path to SQLite database (default: ~/.maia/databases/intelligence/pmp_config.db)')

    args = parser.parse_args()

    # Initialize extractor
    db_path = Path(args.db) if args.db else None
    extractor = PMPConfigExtractor(db_path=db_path)

    if args.command == 'extract':
        print("🔄 Extracting PMP configuration...")
        try:
            snapshot_id = extractor.extract_snapshot()
            print(f"✅ Snapshot {snapshot_id} extracted successfully")

            # Show latest snapshot
            latest = extractor.get_latest_snapshot()
            if latest:
                print(f"\n📊 Latest Snapshot:")
                print(f"   Timestamp: {latest['timestamp']}")
                print(f"   Missing Patches: {latest['missing_patches']}")
                print(f"   Critical Patches: {latest['critical_count']}")
                print(f"   Total Systems: {latest['total_systems']}")
                print(f"   Healthy Systems: {latest['healthy_systems']}")

        except Exception as e:
            print(f"❌ Extraction failed: {e}")
            sys.exit(1)

    elif args.command == 'latest':
        print("📊 Latest Snapshot:")
        latest = extractor.get_latest_snapshot()
        if latest:
            for key, value in latest.items():
                print(f"   {key}: {value}")
        else:
            print("   No snapshots found")

    elif args.command == 'trend':
        print(f"📈 Trend Data (Last {args.days} Days):")
        trend_data = extractor.get_trend_data(days=args.days)

        if trend_data:
            print(f"   Found {len(trend_data)} snapshots")
            print(f"\n   {'Date':<12} {'Missing':>8} {'Critical':>10} {'Healthy %':>10}")
            print(f"   {'-'*12} {'-'*8} {'-'*10} {'-'*10}")

            for snapshot in trend_data:
                date = snapshot['timestamp'][:10]
                missing = snapshot['missing_patches'] or 0
                critical = snapshot['critical_count'] or 0
                healthy_pct = (snapshot['healthy_systems'] or 0) * 100.0 / (snapshot['total_systems'] or 1)

                print(f"   {date:<12} {missing:>8} {critical:>10} {healthy_pct:>9.1f}%")
        else:
            print(f"   No trend data found")

    elif args.command == 'test':
        print("🧪 Testing PMP Config Extractor")
        print(f"   Database: {extractor.db_path}")
        print(f"   OAuth Manager: {'✅ Configured' if extractor.oauth_manager else '❌ Not configured'}")

        # Test database connectivity
        try:
            latest = extractor.get_latest_snapshot()
            print(f"   Database Connection: ✅ Working")
            print(f"   Latest Snapshot: {latest['snapshot_id'] if latest else 'None'}")
        except Exception as e:
            print(f"   Database Connection: ❌ Failed - {e}")

        # Test API connectivity (without saving)
        try:
            response = extractor.oauth_manager.api_request('GET', '/api/1.4/patch/summary')
            print(f"   API Connectivity: ✅ Working (Status: {response.status_code})")
        except Exception as e:
            print(f"   API Connectivity: ❌ Failed - {e}")


if __name__ == '__main__':
    main()
