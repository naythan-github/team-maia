"""
Integration tests for PMP Intelligence Service with real databases.

Sprint: SPRINT-PMP-INTEL-001
Phase: P5 - Integration Testing

Tests against real databases in ~/.maia/databases/intelligence/
Skipped if databases not present.
"""

import pytest
import time
from pathlib import Path


# Skip all tests if real databases not available
REAL_DB_PATH = Path.home() / ".maia" / "databases" / "intelligence"
SKIP_REASON = "Real PMP databases not available"


def has_real_databases() -> bool:
    """Check if real PMP databases exist."""
    if not REAL_DB_PATH.exists():
        return False
    pmp_dbs = list(REAL_DB_PATH.glob("pmp*.db"))
    # Need at least pmp_config.db with data
    config_db = REAL_DB_PATH / "pmp_config.db"
    return config_db.exists() and config_db.stat().st_size > 1000


pytestmark = pytest.mark.skipif(not has_real_databases(), reason=SKIP_REASON)


class TestRealDatabaseQueries:
    """Integration tests with real PMP databases."""

    def test_service_discovers_real_databases(self):
        """Service should discover pmp_config.db and others."""
        from claude.tools.pmp.pmp_intelligence_service import PMPIntelligenceService

        service = PMPIntelligenceService()

        assert "pmp_config.db" in service.available_databases
        assert len(service.available_databases) >= 1

    def test_real_database_query_gs1_systems(self):
        """Query real pmp_config.db for GS1 systems."""
        from claude.tools.pmp.pmp_intelligence_service import PMPIntelligenceService

        service = PMPIntelligenceService()
        result = service.get_systems_by_organization("GS1%")

        # Should return some data (GS1 exists in real DB)
        assert result is not None
        assert hasattr(result, 'data')
        assert result.source_database == "pmp_config.db"

        # If data exists, should have normalized fields
        if result.data:
            sample = result.data[0]
            assert 'name' in sample
            assert 'os' in sample
            assert 'health_status' in sample

    def test_cross_database_freshness_report(self):
        """Freshness report should cover all discovered databases."""
        from claude.tools.pmp.pmp_intelligence_service import PMPIntelligenceService

        service = PMPIntelligenceService()
        report = service.get_data_freshness_report()

        # Should have entry for each discovered database
        for db_name in service.available_databases:
            assert db_name in report
            assert 'is_stale' in report[db_name]
            assert 'days_old' in report[db_name]

    def test_failed_patches_query_real_data(self):
        """Query real failed patches data."""
        from claude.tools.pmp.pmp_intelligence_service import PMPIntelligenceService

        service = PMPIntelligenceService()
        result = service.get_failed_patches()

        assert result is not None
        assert hasattr(result, 'data')

        # If failures exist, should have expected fields
        if result.data:
            sample = result.data[0]
            assert 'patch_name' in sample
            assert 'failed_count' in sample

    def test_vulnerable_systems_real_data(self):
        """Query real vulnerable systems."""
        from claude.tools.pmp.pmp_intelligence_service import PMPIntelligenceService

        service = PMPIntelligenceService()
        result = service.get_vulnerable_systems(severity=3)

        assert result is not None
        assert hasattr(result, 'data')

        # Verify health_status is integer
        for sys in result.data:
            assert isinstance(sys.get('health_status'), int)
            assert sys['health_status'] >= 3


class TestQueryPerformance:
    """Performance benchmarks for real database queries."""

    def test_query_performance_under_1_second(self):
        """All standard queries should complete in <1s."""
        from claude.tools.pmp.pmp_intelligence_service import PMPIntelligenceService

        service = PMPIntelligenceService()

        queries = [
            ("get_systems_by_organization", lambda: service.get_systems_by_organization("GS1%")),
            ("get_failed_patches", lambda: service.get_failed_patches()),
            ("get_vulnerable_systems", lambda: service.get_vulnerable_systems(severity=3)),
            ("get_data_freshness_report", lambda: service.get_data_freshness_report()),
        ]

        for name, query_fn in queries:
            start = time.time()
            result = query_fn()
            elapsed = time.time() - start

            assert elapsed < 1.0, f"{name} took {elapsed:.2f}s (expected <1s)"

    def test_query_timing_metadata_accurate(self):
        """query_time_ms should reflect actual execution time."""
        from claude.tools.pmp.pmp_intelligence_service import PMPIntelligenceService

        service = PMPIntelligenceService()

        start = time.time()
        result = service.get_systems_by_organization("GS1%")
        elapsed_ms = (time.time() - start) * 1000

        # query_time_ms should be within 100ms of actual time
        assert abs(result.query_time_ms - elapsed_ms) < 100


class TestRealDataIntegrity:
    """Test data integrity in real databases."""

    def test_system_names_not_empty(self):
        """System names should not be empty or null."""
        from claude.tools.pmp.pmp_intelligence_service import PMPIntelligenceService

        service = PMPIntelligenceService()
        result = service.get_systems_by_organization("%")  # All systems

        for sys in result.data[:100]:  # Check first 100
            assert sys.get('name'), "System name should not be empty"
            assert len(sys['name']) > 0

    def test_health_status_valid_range(self):
        """Health status should be 1, 2, or 3."""
        from claude.tools.pmp.pmp_intelligence_service import PMPIntelligenceService

        service = PMPIntelligenceService()
        result = service.get_systems_by_organization("%")

        for sys in result.data[:100]:
            if sys.get('health_status') is not None:
                assert sys['health_status'] in [1, 2, 3], \
                    f"Invalid health_status: {sys['health_status']}"


class TestQueryTemplatesIntegration:
    """Test query templates against real data."""

    def test_templates_execute_without_error(self):
        """All templates should execute without SQL errors."""
        from claude.tools.pmp.pmp_intelligence_service import PMPIntelligenceService
        from claude.tools.pmp.pmp_query_templates import TEMPLATES

        service = PMPIntelligenceService()

        # Test templates that don't require parameters
        no_param_templates = ['failed_patches', 'org_health_summary', 'reboot_pending_systems']

        for name in no_param_templates:
            if name in TEMPLATES:
                template = TEMPLATES[name]
                if template.database in service.available_databases:
                    try:
                        result = service.query_raw(template.sql, database=template.database)
                        assert result is not None
                    except Exception as e:
                        pytest.fail(f"Template {name} failed: {e}")
