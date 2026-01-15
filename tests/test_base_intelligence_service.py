"""Tests for BaseIntelligenceService - P1 Unified Intelligence Framework."""

import pytest
from datetime import datetime, timedelta
from abc import ABC
from dataclasses import is_dataclass


class TestBaseIntelligenceServiceImport:
    """Test that the base class can be imported."""

    def test_import_base_class(self):
        """Base class should be importable."""
        from claude.tools.collection.base_intelligence_service import BaseIntelligenceService
        assert BaseIntelligenceService is not None
        assert issubclass(BaseIntelligenceService, ABC)

    def test_base_class_is_abstract(self):
        """Cannot instantiate directly."""
        from claude.tools.collection.base_intelligence_service import BaseIntelligenceService

        with pytest.raises(TypeError) as exc_info:
            BaseIntelligenceService()

        assert "abstract" in str(exc_info.value).lower()


class TestQueryResultDataclass:
    """Test QueryResult dataclass structure and behavior."""

    def test_query_result_structure(self):
        """QueryResult has data, source, timestamp, is_stale, warning."""
        from claude.tools.collection.base_intelligence_service import QueryResult

        # Verify it's a dataclass
        assert is_dataclass(QueryResult)

        # Create instance
        result = QueryResult(
            data=[{"key": "value"}],
            source="test_source",
            extraction_timestamp=datetime.now()
        )

        # Verify required fields
        assert result.data == [{"key": "value"}]
        assert result.source == "test_source"
        assert isinstance(result.extraction_timestamp, datetime)
        assert isinstance(result.is_stale, bool)
        assert result.staleness_warning is None or isinstance(result.staleness_warning, str)
        assert isinstance(result.query_time_ms, int)

    def test_staleness_auto_detection(self):
        """is_stale=True when extraction_timestamp > threshold."""
        from claude.tools.collection.base_intelligence_service import QueryResult

        # Fresh data (today)
        fresh_result = QueryResult(
            data=[],
            source="test",
            extraction_timestamp=datetime.now()
        )
        assert fresh_result.is_stale is False
        assert fresh_result.staleness_warning is None

        # Stale data (10 days old)
        stale_timestamp = datetime.now() - timedelta(days=10)
        stale_result = QueryResult(
            data=[],
            source="test",
            extraction_timestamp=stale_timestamp
        )
        assert stale_result.is_stale is True
        assert stale_result.staleness_warning is not None
        assert "10 days old" in stale_result.staleness_warning


class TestFreshnessInfo:
    """Test FreshnessInfo dataclass structure."""

    def test_freshness_info_structure(self):
        """FreshnessInfo has last_refresh, days_old, is_stale, record_count."""
        from claude.tools.collection.base_intelligence_service import FreshnessInfo

        # Verify it's a dataclass
        assert is_dataclass(FreshnessInfo)

        # Create instance
        info = FreshnessInfo(
            last_refresh=datetime.now(),
            days_old=5,
            is_stale=False,
            record_count=100
        )

        # Verify fields
        assert isinstance(info.last_refresh, datetime)
        assert info.days_old == 5
        assert info.is_stale is False
        assert info.record_count == 100
        assert info.warning is None or isinstance(info.warning, str)


class TestBaseClassInterface:
    """Test abstract method requirements."""

    def test_requires_get_data_freshness_report(self):
        """Subclass must implement get_data_freshness_report()."""
        from claude.tools.collection.base_intelligence_service import BaseIntelligenceService

        # Missing get_data_freshness_report implementation
        class IncompleteService(BaseIntelligenceService):
            def query_raw(self, sql, params=()):
                pass
            def refresh(self):
                pass

        with pytest.raises(TypeError) as exc_info:
            IncompleteService()

        assert "get_data_freshness_report" in str(exc_info.value)

    def test_requires_query_raw(self):
        """Subclass must implement query_raw()."""
        from claude.tools.collection.base_intelligence_service import BaseIntelligenceService

        # Missing query_raw implementation
        class IncompleteService(BaseIntelligenceService):
            def get_data_freshness_report(self):
                pass
            def refresh(self):
                pass

        with pytest.raises(TypeError) as exc_info:
            IncompleteService()

        assert "query_raw" in str(exc_info.value)

    def test_requires_refresh(self):
        """Subclass must implement refresh()."""
        from claude.tools.collection.base_intelligence_service import BaseIntelligenceService

        # Missing refresh implementation
        class IncompleteService(BaseIntelligenceService):
            def get_data_freshness_report(self):
                pass
            def query_raw(self, sql, params=()):
                pass

        with pytest.raises(TypeError) as exc_info:
            IncompleteService()

        assert "refresh" in str(exc_info.value)
