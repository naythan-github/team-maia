"""
Tests for production_readiness_report.py helper functions.

TDD: Phase 3 refactoring - decompose check_production_readiness (198 lines)
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestHelperFunctionsExist:
    """RED: Verify helper functions exist after refactoring."""

    def test_check_phase_evolution_exists(self):
        """Helper for phase evolution status check."""
        from production_readiness_report import _check_phase_evolution
        assert callable(_check_phase_evolution)

    def test_check_core_components_exists(self):
        """Helper for core system components check."""
        from production_readiness_report import _check_core_components
        assert callable(_check_core_components)

    def test_check_infrastructure_exists(self):
        """Helper for production infrastructure check."""
        from production_readiness_report import _check_infrastructure
        assert callable(_check_infrastructure)

    def test_check_api_integrations_exists(self):
        """Helper for API integrations check."""
        from production_readiness_report import _check_api_integrations
        assert callable(_check_api_integrations)

    def test_check_services_exists(self):
        """Helper for production services check."""
        from production_readiness_report import _check_services
        assert callable(_check_services)

    def test_calculate_readiness_exists(self):
        """Helper for calculating overall readiness."""
        from production_readiness_report import _calculate_readiness
        assert callable(_calculate_readiness)


class TestCheckPhaseEvolution:
    """Test _check_phase_evolution helper."""

    def test_returns_tuple_with_score_and_max(self):
        """Should return (score, max_score) tuple."""
        from production_readiness_report import _check_phase_evolution
        result = _check_phase_evolution()
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], (int, float))
        assert isinstance(result[1], (int, float))

    def test_all_complete_phases_score_correctly(self):
        """Completed phases should contribute to score."""
        from production_readiness_report import _check_phase_evolution
        score, max_score = _check_phase_evolution()
        # All 5 phases are marked complete, each worth 20 points
        assert score == 100
        assert max_score == 100


class TestCheckCoreComponents:
    """Test _check_core_components helper."""

    def test_returns_tuple_with_score_and_max(self):
        """Should return (score, max_score) tuple."""
        from production_readiness_report import _check_core_components
        result = _check_core_components()
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_scores_existing_files(self):
        """Existing files should add to score."""
        from production_readiness_report import _check_core_components
        score, max_score = _check_core_components()
        # Max is 7 components * 10 points = 70
        assert max_score == 70
        # Score depends on which files exist
        assert 0 <= score <= 70


class TestCheckInfrastructure:
    """Test _check_infrastructure helper."""

    def test_returns_tuple_with_score_and_max(self):
        """Should return (score, max_score) tuple."""
        from production_readiness_report import _check_infrastructure
        result = _check_infrastructure()
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_infrastructure_max_score(self):
        """Max score should be 7 items * 5 points = 35."""
        from production_readiness_report import _check_infrastructure
        _, max_score = _check_infrastructure()
        assert max_score == 35


class TestCheckApiIntegrations:
    """Test _check_api_integrations helper."""

    def test_returns_tuple_with_score_and_max(self):
        """Should return (score, max_score) tuple."""
        from production_readiness_report import _check_api_integrations
        result = _check_api_integrations()
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_api_max_score(self):
        """Max score should be 5 items * 5 points = 25."""
        from production_readiness_report import _check_api_integrations
        _, max_score = _check_api_integrations()
        assert max_score == 25


class TestCheckServices:
    """Test _check_services helper."""

    def test_returns_tuple_with_score_and_max(self):
        """Should return (score, max_score) tuple."""
        from production_readiness_report import _check_services
        result = _check_services()
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_services_max_score(self):
        """Max score should be 6 items * 5 points = 30."""
        from production_readiness_report import _check_services
        _, max_score = _check_services()
        assert max_score == 30


class TestCalculateReadiness:
    """Test _calculate_readiness helper."""

    def test_returns_dict_with_required_keys(self):
        """Should return dict with score, percentage, status."""
        from production_readiness_report import _calculate_readiness
        result = _calculate_readiness(90, 100)
        assert isinstance(result, dict)
        assert "readiness_score" in result
        assert "max_score" in result
        assert "readiness_percentage" in result
        assert "status" in result

    def test_calculates_percentage_correctly(self):
        """Percentage should be score/max * 100."""
        from production_readiness_report import _calculate_readiness
        result = _calculate_readiness(75, 100)
        assert result["readiness_percentage"] == 75.0

    def test_production_ready_at_90_percent(self):
        """90%+ should be PRODUCTION READY."""
        from production_readiness_report import _calculate_readiness
        result = _calculate_readiness(90, 100)
        assert "PRODUCTION READY" in result["status"]

    def test_nearly_ready_at_75_percent(self):
        """75-89% should be NEARLY READY."""
        from production_readiness_report import _calculate_readiness
        result = _calculate_readiness(80, 100)
        assert "NEARLY READY" in result["status"]

    def test_requires_work_below_75_percent(self):
        """<75% should be REQUIRES WORK."""
        from production_readiness_report import _calculate_readiness
        result = _calculate_readiness(50, 100)
        assert "REQUIRES WORK" in result["status"]
