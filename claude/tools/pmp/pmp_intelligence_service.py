#!/usr/bin/env python3
"""
PMP Intelligence Service - Unified query interface for PMP databases.

Sprint: SPRINT-PMP-INTEL-001
Phase: P5 - BaseIntelligenceService Integration

Provides:
- Single query interface across pmp_config.db, pmp_systemreports.db, pmp_resilient.db
- Semantic query methods (get_systems_by_organization, get_failed_patches, etc.)
- Automatic database selection based on query type
- Timestamp normalization (Unix ms/s → ISO 8601)
- Data freshness tracking with staleness warnings (>7 days = stale)
- Inherits from BaseIntelligenceService for unified intelligence framework

Author: Data Analyst Agent
Date: 2026-01-15
Version: 2.0
"""

import json
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from claude.tools.collection.base_intelligence_service import (
    BaseIntelligenceService,
    QueryResult,
    FreshnessInfo,
)


# =============================================================================
# BACKWARD COMPATIBILITY ALIASES
# =============================================================================

# PMPQueryResult extends QueryResult for backward compatibility
class PMPQueryResult(QueryResult):
    """Backward compatible PMPQueryResult that extends QueryResult.

    Maps source_database -> source for backward compatibility.
    """

    def __init__(self, data, source_database=None, source=None, **kwargs):
        # Accept both source_database and source for backward compatibility
        if source_database is not None:
            source = source_database
        super().__init__(data=data, source=source, **kwargs)

    @property
    def source_database(self):
        """Backward compatible property for source."""
        return self.source


# =============================================================================
# MAIN SERVICE CLASS
# =============================================================================

class PMPIntelligenceService(BaseIntelligenceService):
    """
    Unified interface for PMP database queries.

    Usage:
        from claude.tools.pmp.pmp_intelligence_service import PMPIntelligenceService

        pmp = PMPIntelligenceService()
        result = pmp.get_failed_patches(org_pattern="GS1%", os_filter="Windows Server%")
        print(f"Found {len(result.data)} failed patches")
        if result.is_stale:
            print(f"Warning: {result.staleness_warning}")
    """

    # Default database path
    DEFAULT_DB_PATH = Path.home() / ".maia" / "databases" / "intelligence"

    # Staleness threshold in days
    STALENESS_THRESHOLD_DAYS = 7

    # Database selection hints
    DB_HINTS = {
        "system_details": "pmp_systemreports.db",
        "system_inventory": "pmp_config.db",
        "patch_aggregates": "pmp_config.db",
        "patch_per_system": "pmp_systemreports.db",
        "deployment_status": "pmp_systemreports.db",
        "policy_config": "pmp_config.db",
    }

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize service with database discovery.

        Args:
            db_path: Path to database directory (default: ~/.maia/databases/intelligence/)

        Raises:
            FileNotFoundError: If database directory doesn't exist
        """
        self.db_path = Path(db_path) if db_path else self.DEFAULT_DB_PATH

        if not self.db_path.exists():
            raise FileNotFoundError(
                f"Database directory not found: {self.db_path}. "
                "Please ensure PMP databases are extracted to ~/.maia/databases/intelligence/"
            )

        self._discover_databases()

    def _discover_databases(self) -> None:
        """Discover available PMP databases in the directory."""
        self.available_databases: List[str] = []
        self._db_connections: Dict[str, Path] = {}

        for db_file in self.db_path.glob("pmp*.db"):
            db_name = db_file.name
            self.available_databases.append(db_name)
            self._db_connections[db_name] = db_file

    def _get_connection(self, database: str) -> sqlite3.Connection:
        """Get SQLite connection for specified database."""
        if database not in self._db_connections:
            raise ValueError(f"Database not found: {database}. Available: {self.available_databases}")

        conn = sqlite3.connect(self._db_connections[database])
        conn.row_factory = sqlite3.Row
        return conn

    def _detect_best_database(self, query_type: str) -> str:
        """
        Detect best database for query type.

        Args:
            query_type: Type of query (system_details, patch_aggregates, etc.)

        Returns:
            Database filename
        """
        if query_type in self.DB_HINTS:
            preferred = self.DB_HINTS[query_type]
            if preferred in self.available_databases:
                return preferred

        # Fallback to pmp_config.db if available
        if "pmp_config.db" in self.available_databases:
            return "pmp_config.db"

        # Otherwise first available
        return self.available_databases[0] if self.available_databases else "pmp_config.db"

    def _normalize_timestamp(self, value: Any) -> str:
        """
        Normalize timestamp to ISO 8601 string.

        Args:
            value: Unix timestamp (ms or s), datetime, or string

        Returns:
            ISO 8601 formatted string
        """
        if value is None:
            return None

        if isinstance(value, datetime):
            return value.isoformat()

        if isinstance(value, str):
            # Already a string, try to parse and re-format
            try:
                dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
                return dt.isoformat()
            except ValueError:
                return value

        if isinstance(value, (int, float)):
            # Determine if milliseconds or seconds
            if value > 1e12:  # Likely milliseconds
                dt = datetime.fromtimestamp(value / 1000)
            else:  # Likely seconds
                dt = datetime.fromtimestamp(value)
            return dt.isoformat()

        return str(value)

    def _get_extraction_timestamp(self, database: str) -> Optional[datetime]:
        """Get most recent extraction timestamp for a database."""
        try:
            conn = self._get_connection(database)
            cursor = conn.cursor()

            # Try different table structures
            for query in [
                "SELECT MAX(timestamp) FROM snapshots WHERE status = 'success'",
                "SELECT MAX(completed_at) FROM extraction_runs WHERE status = 'success'",
                "SELECT MAX(created_at) FROM systems",
            ]:
                try:
                    cursor.execute(query)
                    result = cursor.fetchone()
                    if result and result[0]:
                        ts_str = result[0]
                        if isinstance(ts_str, str):
                            return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                        elif isinstance(ts_str, (int, float)):
                            if ts_str > 1e12:
                                return datetime.fromtimestamp(ts_str / 1000)
                            return datetime.fromtimestamp(ts_str)
                except sqlite3.OperationalError:
                    continue

            conn.close()
        except Exception:
            pass

        return datetime.now()  # Fallback to now if can't determine

    def _execute_query(
        self,
        sql: str,
        database: str,
        params: tuple = ()
    ) -> PMPQueryResult:
        """Execute query and return standardized result."""
        start_time = time.time()

        conn = self._get_connection(database)
        cursor = conn.cursor()
        cursor.execute(sql, params)

        rows = cursor.fetchall()
        data = [dict(row) for row in rows]

        conn.close()

        query_time_ms = int((time.time() - start_time) * 1000)
        extraction_ts = self._get_extraction_timestamp(database)

        return PMPQueryResult(
            data=data,
            source_database=database,
            extraction_timestamp=extraction_ts,
            query_time_ms=query_time_ms
        )

    # =========================================================================
    # SEMANTIC QUERY METHODS
    # =========================================================================

    def get_systems_by_organization(self, org_pattern: str) -> PMPQueryResult:
        """
        Get all systems for an organization/branch.

        Args:
            org_pattern: SQL LIKE pattern (e.g., "GS1%")

        Returns:
            QueryResult with normalized system data
        """
        # Try pmp_config.db first (has JSON raw_data)
        if "pmp_config.db" in self.available_databases:
            sql = """
                SELECT
                    json_extract(raw_data, '$.resource_name') as name,
                    json_extract(raw_data, '$.os_name') as os,
                    json_extract(raw_data, '$.resource_health_status') as health_status,
                    json_extract(raw_data, '$.branch_office_name') as organization,
                    json_extract(raw_data, '$.ip_address') as ip_address,
                    json_extract(raw_data, '$.last_scan_time') as last_scan_time
                FROM all_systems
                WHERE (
                    json_extract(raw_data, '$.resource_name') LIKE ?
                    OR json_extract(raw_data, '$.branch_office_name') LIKE ?
                )
                ORDER BY json_extract(raw_data, '$.resource_name')
            """
            result = self._execute_query(sql, "pmp_config.db", (org_pattern, org_pattern))

        # Fallback to pmp_systemreports.db
        elif "pmp_systemreports.db" in self.available_databases:
            sql = """
                SELECT
                    computer_name as name,
                    os_name as os,
                    resource_health_status as health_status
                FROM systems
                WHERE computer_name LIKE ?
                ORDER BY computer_name
            """
            result = self._execute_query(sql, "pmp_systemreports.db", (org_pattern,))
        else:
            return PMPQueryResult(
                data=[],
                source_database="none",
                extraction_timestamp=datetime.now(),
                staleness_warning="No PMP databases available"
            )

        # Ensure health_status is integer (handle "--" and other non-numeric values)
        for row in result.data:
            if 'health_status' in row and row['health_status'] is not None:
                try:
                    row['health_status'] = int(row['health_status'])
                except (ValueError, TypeError):
                    row['health_status'] = 0  # Unknown/invalid → 0

        return result

    def get_failed_patches(
        self,
        org_pattern: Optional[str] = None,
        os_filter: Optional[str] = None
    ) -> PMPQueryResult:
        """
        Get patches with deployment failures.

        Args:
            org_pattern: Optional organization filter (SQL LIKE)
            os_filter: Optional OS filter (SQL LIKE)

        Returns:
            QueryResult with failed patch data
        """
        database = self._detect_best_database("patch_aggregates")

        if database == "pmp_config.db" and "pmp_config.db" in self.available_databases:
            sql = """
                SELECT
                    json_extract(raw_data, '$.patch_name') as patch_name,
                    json_extract(raw_data, '$.bulletin_id') as bulletin_id,
                    CAST(json_extract(raw_data, '$.failed') AS INTEGER) as failed_count,
                    CAST(json_extract(raw_data, '$.missing') AS INTEGER) as missing_count,
                    json_extract(raw_data, '$.severity') as severity
                FROM missing_patches
                WHERE CAST(json_extract(raw_data, '$.failed') AS INTEGER) > 0
                ORDER BY failed_count DESC
            """
            result = self._execute_query(sql, database)

        elif "pmp_systemreports.db" in self.available_databases:
            sql = """
                SELECT
                    patch_name,
                    COUNT(*) as failed_count
                FROM system_reports
                WHERE patch_deployed = 0
                GROUP BY patch_name
                ORDER BY failed_count DESC
            """
            result = self._execute_query(sql, "pmp_systemreports.db")
        else:
            return PMPQueryResult(
                data=[],
                source_database="none",
                extraction_timestamp=datetime.now(),
                staleness_warning="No PMP databases available"
            )

        return result

    def get_vulnerable_systems(self, severity: int = 3) -> PMPQueryResult:
        """
        Get systems with specified vulnerability severity.

        Args:
            severity: Minimum severity (1=healthy, 2=moderate, 3=highly vulnerable)

        Returns:
            QueryResult with vulnerable system data
        """
        if "pmp_config.db" in self.available_databases:
            sql = """
                SELECT
                    json_extract(raw_data, '$.resource_name') as name,
                    json_extract(raw_data, '$.os_name') as os,
                    json_extract(raw_data, '$.resource_health_status') as health_status,
                    json_extract(raw_data, '$.branch_office_name') as organization
                FROM all_systems
                WHERE CAST(json_extract(raw_data, '$.resource_health_status') AS INTEGER) >= ?
                ORDER BY json_extract(raw_data, '$.resource_health_status') DESC
            """
            result = self._execute_query(sql, "pmp_config.db", (severity,))
        elif "pmp_systemreports.db" in self.available_databases:
            sql = """
                SELECT
                    computer_name as name,
                    os_name as os,
                    resource_health_status as health_status
                FROM systems
                WHERE resource_health_status >= ?
                ORDER BY resource_health_status DESC
            """
            result = self._execute_query(sql, "pmp_systemreports.db", (severity,))
        else:
            return PMPQueryResult(
                data=[],
                source_database="none",
                extraction_timestamp=datetime.now()
            )

        # Ensure health_status is integer (handle "--" and other non-numeric values)
        for row in result.data:
            if 'health_status' in row and row['health_status'] is not None:
                try:
                    row['health_status'] = int(row['health_status'])
                except (ValueError, TypeError):
                    row['health_status'] = 0  # Unknown/invalid → 0

        return result

    def get_patch_deployment_status(self, patch_id: str) -> PMPQueryResult:
        """
        Get deployment status for a specific patch.

        Args:
            patch_id: Patch identifier (KB number or bulletin ID)

        Returns:
            QueryResult with deployment status
        """
        database = self._detect_best_database("deployment_status")

        if "pmp_systemreports.db" in self.available_databases:
            sql = """
                SELECT
                    s.computer_name as system_name,
                    sr.patch_name,
                    sr.patch_status,
                    sr.patch_deployed,
                    CASE
                        WHEN sr.patch_deployed = 1 THEN 'Installed'
                        WHEN sr.is_reboot_required = 1 THEN 'Reboot Pending'
                        ELSE 'Not Installed'
                    END as status_text
                FROM system_reports sr
                JOIN systems s ON sr.resource_id = s.resource_id
                WHERE sr.patch_name LIKE ?
                ORDER BY sr.patch_deployed
            """
            return self._execute_query(sql, "pmp_systemreports.db", (f"%{patch_id}%",))

        return PMPQueryResult(
            data=[],
            source_database="none",
            extraction_timestamp=datetime.now(),
            staleness_warning="pmp_systemreports.db not available"
        )

    def get_data_freshness_report(self) -> Dict[str, FreshnessInfo]:
        """
        Get freshness report for all available databases.

        Returns:
            Dict mapping database name to FreshnessInfo
        """
        report = {}

        for db_name in self.available_databases:
            extraction_ts = self._get_extraction_timestamp(db_name)
            days_old = (datetime.now() - extraction_ts).days if extraction_ts else 0
            is_stale = days_old > self.STALENESS_THRESHOLD_DAYS

            # Get record count for this database
            try:
                conn = self._get_connection(db_name)
                cursor = conn.cursor()

                # Try different table names to get record count
                record_count = 0
                for table in ["all_systems", "systems", "missing_patches"]:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        record_count += count
                    except sqlite3.OperationalError:
                        continue

                conn.close()
            except Exception:
                record_count = 0

            report[db_name] = FreshnessInfo(
                last_refresh=extraction_ts,
                days_old=days_old,
                is_stale=is_stale,
                record_count=record_count,
                warning=f"Data is {days_old} days old" if is_stale else None
            )

        return report

    def query_raw(
        self,
        sql: str,
        database: str = "auto"
    ) -> PMPQueryResult:
        """
        Execute raw SQL query.

        Args:
            sql: SQL query string
            database: Database name or "auto" for automatic selection

        Returns:
            QueryResult
        """
        if database == "auto":
            # Try to detect based on table names in query
            sql_lower = sql.lower()
            if "system_reports" in sql_lower or "systems" in sql_lower:
                if "pmp_systemreports.db" in self.available_databases:
                    database = "pmp_systemreports.db"
            if database == "auto":
                database = self._detect_best_database("system_inventory")

        return self._execute_query(sql, database)

    def refresh(self) -> bool:
        """
        Refresh PMP intelligence data by running the resilient extractor.

        Returns:
            True if refresh successful, False otherwise
        """
        try:
            # Import the extractor dynamically to avoid circular dependencies
            import sys
            from claude.tools.pmp.pmp_resilient_extractor import PMPResilientExtractor

            # Initialize extractor
            # Use the first available database path as the target
            target_db = None
            if "pmp_resilient.db" in self.available_databases:
                target_db = self._db_connections.get("pmp_resilient.db")
            elif "pmp_config.db" in self.available_databases:
                target_db = self._db_connections.get("pmp_config.db")

            if not target_db:
                return False

            extractor = PMPResilientExtractor(db_path=str(target_db))

            # Run extraction
            result = extractor.extract_batch()

            # Check if successful
            if result.get('status') in ['target_met', 'batch_complete']:
                return True
            else:
                return False

        except Exception as e:
            # Log error but don't crash
            import logging
            logging.error(f"PMP refresh failed: {e}")
            return False


# =============================================================================
# CLI INTERFACE
# =============================================================================

if __name__ == "__main__":
    import sys

    print("PMP Intelligence Service - Interactive Mode")
    print("=" * 50)

    try:
        service = PMPIntelligenceService()
        print(f"Discovered databases: {service.available_databases}")
        print()

        # Show freshness report
        print("Data Freshness Report:")
        for db_name, info in service.get_data_freshness_report().items():
            status = "STALE" if info.is_stale else "OK"
            print(f"  {db_name}: {status} ({info.days_old} days old)")

        print()

        # Example query
        if len(sys.argv) > 1:
            org_pattern = sys.argv[1]
            print(f"Querying systems matching: {org_pattern}")
            result = service.get_systems_by_organization(org_pattern)
            print(f"Found {len(result.data)} systems (source: {result.source})")
            for sys_info in result.data[:5]:
                print(f"  - {sys_info.get('name', 'N/A')}: {sys_info.get('os', 'N/A')}")

    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
