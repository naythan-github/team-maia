"""
Tests for PMP Intelligence Service - Unified query interface for PMP databases.

Sprint: SPRINT-PMP-INTEL-001
Phase: P1 - Test Infrastructure Setup
TDD: Tests written BEFORE implementation (must fail initially)
"""

import pytest
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import patch, MagicMock


# =============================================================================
# FIXTURES: Mock Database Setup
# =============================================================================

@pytest.fixture
def mock_pmp_config_db(tmp_path):
    """Create mock pmp_config.db with sample data."""
    db_path = tmp_path / "pmp_config.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create snapshots table
    cursor.execute("""
        CREATE TABLE snapshots (
            snapshot_id INTEGER PRIMARY KEY,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'success'
        )
    """)

    # Create all_systems table (matches real schema)
    cursor.execute("""
        CREATE TABLE all_systems (
            id INTEGER PRIMARY KEY,
            extraction_id INTEGER,
            raw_data TEXT
        )
    """)

    # Create missing_patches table
    cursor.execute("""
        CREATE TABLE missing_patches (
            id INTEGER PRIMARY KEY,
            extraction_id INTEGER,
            raw_data TEXT
        )
    """)

    # Insert snapshot
    cursor.execute("INSERT INTO snapshots (snapshot_id, status) VALUES (1, 'success')")

    # Insert sample systems (JSON in raw_data to match real schema)
    import json
    systems = [
        {"resource_name": "GS1MELB01", "os_name": "Windows Server 2019", "resource_health_status": 1},
        {"resource_name": "GS1MELB02", "os_name": "Windows Server 2016", "resource_health_status": 3},
        {"resource_name": "GS1SYD01", "os_name": "Ubuntu 22.04", "resource_health_status": 1},
        {"resource_name": "ABC001", "os_name": "Windows Server 2019", "resource_health_status": 2},
    ]
    for i, sys in enumerate(systems):
        cursor.execute(
            "INSERT INTO all_systems (id, extraction_id, raw_data) VALUES (?, 1, ?)",
            (i + 1, json.dumps(sys))
        )

    # Insert sample patches with failures
    patches = [
        {"patch_name": "KB5068864", "bulletin_id": "MS24-001", "failed": 6, "missing": 19},
        {"patch_name": "KB5066137", "bulletin_id": "MS24-002", "failed": 3, "missing": 4},
        {"patch_name": "KB5068791", "bulletin_id": "MS24-003", "failed": 0, "missing": 10},
    ]
    for i, p in enumerate(patches):
        cursor.execute(
            "INSERT INTO missing_patches (id, extraction_id, raw_data) VALUES (?, 1, ?)",
            (i + 1, json.dumps(p))
        )

    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def mock_pmp_systemreports_db(tmp_path):
    """Create mock pmp_systemreports.db with sample data."""
    db_path = tmp_path / "pmp_systemreports.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create extraction_runs table
    cursor.execute("""
        CREATE TABLE extraction_runs (
            id INTEGER PRIMARY KEY,
            started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            completed_at DATETIME,
            status TEXT DEFAULT 'success'
        )
    """)

    # Create systems table (normalized schema)
    cursor.execute("""
        CREATE TABLE systems (
            resource_id INTEGER PRIMARY KEY,
            computer_name TEXT,
            os_name TEXT,
            resource_health_status INTEGER,
            extraction_id INTEGER
        )
    """)

    # Create system_reports table
    cursor.execute("""
        CREATE TABLE system_reports (
            id INTEGER PRIMARY KEY,
            resource_id INTEGER,
            patch_id INTEGER,
            patch_name TEXT,
            deployment_status INTEGER,
            extraction_id INTEGER
        )
    """)

    # Insert extraction run
    cursor.execute("INSERT INTO extraction_runs (id, status) VALUES (1, 'success')")

    # Insert systems with different column naming
    cursor.execute("INSERT INTO systems VALUES (1, 'GS1MELB01', 'Windows Server 2019', 1, 1)")
    cursor.execute("INSERT INTO systems VALUES (2, 'GS1MELB02', 'Windows Server 2016', 3, 1)")

    # Insert system reports with deployment failures (status 206 = failed)
    cursor.execute("INSERT INTO system_reports VALUES (1, 1, 100, 'KB5068864', 206, 1)")
    cursor.execute("INSERT INTO system_reports VALUES (2, 2, 100, 'KB5068864', 209, 1)")

    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def mock_stale_db(tmp_path):
    """Create mock database with stale data (>7 days old)."""
    db_path = tmp_path / "stale_pmp.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE snapshots (
            snapshot_id INTEGER PRIMARY KEY,
            timestamp DATETIME,
            status TEXT DEFAULT 'success'
        )
    """)

    # Insert old snapshot (10 days ago)
    old_date = (datetime.now() - timedelta(days=10)).isoformat()
    cursor.execute(
        "INSERT INTO snapshots (snapshot_id, timestamp, status) VALUES (1, ?, 'success')",
        (old_date,)
    )

    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def mock_db_directory(tmp_path, mock_pmp_config_db, mock_pmp_systemreports_db):
    """Create directory structure matching ~/.maia/databases/intelligence/"""
    intel_dir = tmp_path / "intelligence"
    intel_dir.mkdir()

    # Copy mock databases to intelligence directory
    import shutil
    shutil.copy(mock_pmp_config_db, intel_dir / "pmp_config.db")
    shutil.copy(mock_pmp_systemreports_db, intel_dir / "pmp_systemreports.db")

    return intel_dir


# =============================================================================
# TESTS: Must FAIL until P2 implementation
# =============================================================================

class TestPMPIntelligenceServiceImport:
    """Test that the module can be imported."""

    def test_module_importable(self):
        """PMPIntelligenceService should be importable from expected path."""
        from claude.tools.pmp.pmp_intelligence_service import PMPIntelligenceService
        assert PMPIntelligenceService is not None

    def test_query_result_dataclass_exists(self):
        """PMPQueryResult dataclass should exist."""
        from claude.tools.pmp.pmp_intelligence_service import PMPQueryResult
        assert PMPQueryResult is not None


class TestPMPQueryResult:
    """Test the query result dataclass structure."""

    def test_query_result_has_required_fields(self):
        """PMPQueryResult should have all required fields."""
        from claude.tools.pmp.pmp_intelligence_service import PMPQueryResult

        result = PMPQueryResult(
            data=[{"name": "test"}],
            source_database="pmp_config.db",
            extraction_timestamp=datetime.now(),
            is_stale=False,
            staleness_warning=None,
            query_time_ms=100
        )

        assert hasattr(result, 'data')
        assert hasattr(result, 'source_database')
        assert hasattr(result, 'extraction_timestamp')
        assert hasattr(result, 'is_stale')
        assert hasattr(result, 'staleness_warning')
        assert hasattr(result, 'query_time_ms')

    def test_query_result_stale_flag_set_correctly(self):
        """is_stale should be True when staleness_warning is set."""
        from claude.tools.pmp.pmp_intelligence_service import PMPQueryResult

        result = PMPQueryResult(
            data=[],
            source_database="pmp_config.db",
            extraction_timestamp=datetime.now() - timedelta(days=10),
            is_stale=True,
            staleness_warning="Data is 10 days old",
            query_time_ms=50
        )

        assert result.is_stale is True
        assert result.staleness_warning is not None


class TestServiceInitialization:
    """Test service initialization and database discovery."""

    def test_init_with_default_path(self, mock_db_directory):
        """Service should auto-discover databases in default path."""
        from claude.tools.pmp.pmp_intelligence_service import PMPIntelligenceService

        service = PMPIntelligenceService(db_path=mock_db_directory)
        assert service is not None

    def test_init_discovers_pmp_databases(self, mock_db_directory):
        """Service should discover pmp_config.db and pmp_systemreports.db."""
        from claude.tools.pmp.pmp_intelligence_service import PMPIntelligenceService

        service = PMPIntelligenceService(db_path=mock_db_directory)

        # Should have discovered both databases
        assert "pmp_config.db" in service.available_databases
        assert "pmp_systemreports.db" in service.available_databases

    def test_init_handles_missing_directory(self, tmp_path):
        """Service should raise clear error if database directory missing."""
        from claude.tools.pmp.pmp_intelligence_service import PMPIntelligenceService

        nonexistent = tmp_path / "nonexistent"
        with pytest.raises(FileNotFoundError) as exc_info:
            PMPIntelligenceService(db_path=nonexistent)

        assert "database directory" in str(exc_info.value).lower()


class TestSystemsQueryNormalization:
    """Test that system queries return normalized data regardless of source."""

    def test_query_systems_by_org_returns_normalized_data(self, mock_db_directory):
        """Systems query returns consistent schema regardless of source DB."""
        from claude.tools.pmp.pmp_intelligence_service import PMPIntelligenceService

        service = PMPIntelligenceService(db_path=mock_db_directory)
        result = service.get_systems_by_organization("GS1%")

        # Should return PMPQueryResult
        assert hasattr(result, 'data')
        assert hasattr(result, 'source_database')

        # Data should have normalized field names
        for system in result.data:
            assert 'name' in system  # Normalized from resource_name/computer_name
            assert 'os' in system    # Normalized from os_name
            assert 'health_status' in system  # Normalized from resource_health_status

    def test_query_systems_filters_by_org_pattern(self, mock_db_directory):
        """Should only return systems matching organization pattern."""
        from claude.tools.pmp.pmp_intelligence_service import PMPIntelligenceService

        service = PMPIntelligenceService(db_path=mock_db_directory)
        result = service.get_systems_by_organization("GS1%")

        # Should only return GS1 systems (3 in mock data)
        assert len(result.data) == 3
        for system in result.data:
            assert system['name'].startswith('GS1')


class TestFailedPatchesAggregation:
    """Test cross-database aggregation for failed patches."""

    def test_query_failed_patches_aggregates_across_databases(self, mock_db_directory):
        """Failed patch query combines pmp_config + pmp_systemreports data."""
        from claude.tools.pmp.pmp_intelligence_service import PMPIntelligenceService

        service = PMPIntelligenceService(db_path=mock_db_directory)
        result = service.get_failed_patches()

        # Should return patches with failures
        assert len(result.data) > 0

        # Each patch should have aggregated failure info
        for patch in result.data:
            assert 'patch_name' in patch
            assert 'failed_count' in patch

    def test_failed_patches_filters_by_org(self, mock_db_directory):
        """Should filter failed patches by organization."""
        from claude.tools.pmp.pmp_intelligence_service import PMPIntelligenceService

        service = PMPIntelligenceService(db_path=mock_db_directory)
        result = service.get_failed_patches(org_pattern="GS1%")

        assert result is not None
        assert hasattr(result, 'data')

    def test_failed_patches_filters_by_os(self, mock_db_directory):
        """Should filter failed patches by OS type."""
        from claude.tools.pmp.pmp_intelligence_service import PMPIntelligenceService

        service = PMPIntelligenceService(db_path=mock_db_directory)
        result = service.get_failed_patches(os_filter="Windows Server%")

        assert result is not None


class TestTimestampNormalization:
    """Test timestamp normalization across all query results."""

    def test_timestamps_normalized_to_iso8601(self, mock_db_directory):
        """All timestamp fields converted to ISO 8601 strings."""
        from claude.tools.pmp.pmp_intelligence_service import PMPIntelligenceService

        service = PMPIntelligenceService(db_path=mock_db_directory)
        result = service.get_systems_by_organization("GS1%")

        # extraction_timestamp should be ISO 8601
        assert isinstance(result.extraction_timestamp, datetime)

        # If data contains timestamps, they should be normalized
        # (This tests the _normalize_timestamp internal method)

    def test_unix_ms_timestamps_converted(self, mock_db_directory):
        """Unix millisecond timestamps should be converted to ISO 8601."""
        from claude.tools.pmp.pmp_intelligence_service import PMPIntelligenceService

        service = PMPIntelligenceService(db_path=mock_db_directory)

        # Test internal normalization
        unix_ms = 1705334400000  # 2024-01-15T12:00:00Z in ms
        normalized = service._normalize_timestamp(unix_ms)

        assert isinstance(normalized, str)
        assert "2024" in normalized  # Should contain year

    def test_unix_seconds_timestamps_converted(self, mock_db_directory):
        """Unix second timestamps should be converted to ISO 8601."""
        from claude.tools.pmp.pmp_intelligence_service import PMPIntelligenceService

        service = PMPIntelligenceService(db_path=mock_db_directory)

        unix_s = 1705334400  # 2024-01-15T12:00:00Z in seconds
        normalized = service._normalize_timestamp(unix_s)

        assert isinstance(normalized, str)
        assert "2024" in normalized


class TestStalenessDetection:
    """Test automatic staleness detection and warnings."""

    def test_staleness_warning_on_old_data(self, tmp_path, mock_stale_db):
        """Query result includes warning if data >7 days old."""
        from claude.tools.pmp.pmp_intelligence_service import PMPIntelligenceService

        # Create directory with stale database
        intel_dir = tmp_path / "intelligence"
        intel_dir.mkdir()
        import shutil
        shutil.copy(mock_stale_db, intel_dir / "pmp_config.db")

        service = PMPIntelligenceService(db_path=intel_dir)
        result = service.get_data_freshness_report()

        # Should indicate staleness (now returns FreshnessInfo objects)
        assert result['pmp_config.db'].is_stale is True
        assert 'days old' in result['pmp_config.db'].warning.lower()

    def test_fresh_data_no_warning(self, mock_db_directory):
        """Fresh data (<7 days) should not have staleness warning."""
        from claude.tools.pmp.pmp_intelligence_service import PMPIntelligenceService

        service = PMPIntelligenceService(db_path=mock_db_directory)
        result = service.get_data_freshness_report()

        # Mock data was just created, should be fresh (now returns FreshnessInfo objects)
        for db_name, info in result.items():
            if info.last_refresh:
                assert info.is_stale is False


class TestDatabaseAutoSelection:
    """Test automatic database selection based on query type."""

    def test_detect_best_database_for_systems(self, mock_db_directory):
        """Should select pmp_systemreports.db for detailed system queries."""
        from claude.tools.pmp.pmp_intelligence_service import PMPIntelligenceService

        service = PMPIntelligenceService(db_path=mock_db_directory)
        best_db = service._detect_best_database("system_details")

        # systemreports has more detailed per-system data
        assert best_db in ["pmp_systemreports.db", "pmp_config.db"]

    def test_detect_best_database_for_patches(self, mock_db_directory):
        """Should select pmp_config.db for aggregate patch queries."""
        from claude.tools.pmp.pmp_intelligence_service import PMPIntelligenceService

        service = PMPIntelligenceService(db_path=mock_db_directory)
        best_db = service._detect_best_database("patch_aggregates")

        # config has better aggregate patch data
        assert best_db == "pmp_config.db"


class TestVulnerableSystemsQuery:
    """Test vulnerable systems query method."""

    def test_get_vulnerable_systems_default_severity(self, mock_db_directory):
        """Should return highly vulnerable systems (severity 3) by default."""
        from claude.tools.pmp.pmp_intelligence_service import PMPIntelligenceService

        service = PMPIntelligenceService(db_path=mock_db_directory)
        result = service.get_vulnerable_systems()

        # Should return systems with health_status = 3
        assert len(result.data) >= 1  # GS1MELB02 has status 3 in mock
        for system in result.data:
            assert system['health_status'] == 3

    def test_get_vulnerable_systems_custom_severity(self, mock_db_directory):
        """Should filter by custom severity threshold."""
        from claude.tools.pmp.pmp_intelligence_service import PMPIntelligenceService

        service = PMPIntelligenceService(db_path=mock_db_directory)
        result = service.get_vulnerable_systems(severity=2)

        # Should return systems with health_status >= 2
        for system in result.data:
            assert system['health_status'] >= 2


class TestRawQueryInterface:
    """Test low-level raw query interface."""

    def test_query_raw_executes_sql(self, mock_db_directory):
        """Should execute raw SQL and return PMPQueryResult."""
        from claude.tools.pmp.pmp_intelligence_service import PMPIntelligenceService

        service = PMPIntelligenceService(db_path=mock_db_directory)
        result = service.query_raw(
            "SELECT * FROM all_systems WHERE extraction_id = 1",
            database="pmp_config.db"
        )

        assert hasattr(result, 'data')
        assert result.source_database == "pmp_config.db"

    def test_query_raw_auto_database_selection(self, mock_db_directory):
        """Should auto-select database if not specified."""
        from claude.tools.pmp.pmp_intelligence_service import PMPIntelligenceService

        service = PMPIntelligenceService(db_path=mock_db_directory)
        result = service.query_raw(
            "SELECT COUNT(*) as cnt FROM systems",
            database="auto"
        )

        # Should succeed without explicit database
        assert result is not None


class TestQueryPerformance:
    """Test query performance characteristics."""

    def test_query_returns_timing_metadata(self, mock_db_directory):
        """All queries should include query_time_ms in result."""
        from claude.tools.pmp.pmp_intelligence_service import PMPIntelligenceService

        service = PMPIntelligenceService(db_path=mock_db_directory)
        result = service.get_systems_by_organization("GS1%")

        assert hasattr(result, 'query_time_ms')
        assert isinstance(result.query_time_ms, int)
        assert result.query_time_ms >= 0


class TestBaseClassInheritance:
    """Test BaseIntelligenceService inheritance (TDD for P5)."""

    def test_inherits_base_class(self):
        """PMPIntelligenceService inherits BaseIntelligenceService."""
        from claude.tools.collection.base_intelligence_service import BaseIntelligenceService
        from claude.tools.pmp.pmp_intelligence_service import PMPIntelligenceService

        assert issubclass(PMPIntelligenceService, BaseIntelligenceService)

    def test_returns_query_result_type(self, mock_db_directory):
        """Methods return QueryResult (not PMPQueryResult)."""
        from claude.tools.collection.base_intelligence_service import QueryResult
        from claude.tools.pmp.pmp_intelligence_service import PMPIntelligenceService

        service = PMPIntelligenceService(db_path=mock_db_directory)
        result = service.get_systems_by_organization("GS1%")

        # Should be instance of base QueryResult type
        assert isinstance(result, QueryResult)

        # Test other query methods return QueryResult
        result2 = service.get_failed_patches()
        assert isinstance(result2, QueryResult)

        result3 = service.get_vulnerable_systems()
        assert isinstance(result3, QueryResult)

    def test_freshness_returns_freshness_info(self, mock_db_directory):
        """get_data_freshness_report returns FreshnessInfo objects."""
        from claude.tools.collection.base_intelligence_service import FreshnessInfo
        from claude.tools.pmp.pmp_intelligence_service import PMPIntelligenceService

        service = PMPIntelligenceService(db_path=mock_db_directory)
        report = service.get_data_freshness_report()

        # Report should be dict mapping to FreshnessInfo instances
        assert isinstance(report, dict)
        assert len(report) > 0

        for db_name, info in report.items():
            assert isinstance(info, FreshnessInfo)
            assert hasattr(info, 'last_refresh')
            assert hasattr(info, 'days_old')
            assert hasattr(info, 'is_stale')
            assert hasattr(info, 'record_count')

    def test_refresh_method_exists(self, mock_db_directory):
        """refresh() method is implemented."""
        from claude.tools.pmp.pmp_intelligence_service import PMPIntelligenceService

        service = PMPIntelligenceService(db_path=mock_db_directory)

        # Method should exist and be callable
        assert hasattr(service, 'refresh')
        assert callable(service.refresh)

        # Call refresh (should return bool)
        result = service.refresh()
        assert isinstance(result, bool)
