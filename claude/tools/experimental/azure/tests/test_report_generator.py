"""
Phase 4 TDD Tests - Report Generator

Tests for cost optimization report generation including executive summaries
and detailed reports in multiple formats.

Run with: pytest tests/test_report_generator.py -v
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
from typing import List, Dict, Any


class TestReportGeneratorInitialization:
    """Tests for ReportGenerator initialization."""

    def test_report_generator_initialization(self):
        """
        Verify ReportGenerator can be initialized.
        """
        from claude.tools.experimental.azure.report_generator import ReportGenerator

        generator = ReportGenerator()
        assert generator is not None

    def test_report_generator_with_custom_db_path(self):
        """
        Verify ReportGenerator can be initialized with custom database path.
        """
        from claude.tools.experimental.azure.report_generator import ReportGenerator
        from pathlib import Path

        custom_path = Path("/tmp/test_reports")
        generator = ReportGenerator(base_path=custom_path)
        assert generator is not None


class TestExecutiveSummaryGeneration:
    """Tests for executive summary generation."""

    def test_generate_executive_summary_success(self):
        """
        Verify executive summary can be generated with top recommendations.
        """
        from claude.tools.experimental.azure.report_generator import ReportGenerator

        # Mock database with recommendations
        with patch('claude.tools.experimental.azure.report_generator.CustomerDatabaseManager') as mock_mgr_class:
            mock_mgr = Mock()
            mock_db = Mock()

            # Mock recommendations
            mock_db.get_all_recommendations.return_value = [
                Mock(
                    category="Cost",
                    impact="High",
                    estimated_savings_monthly=150.0,
                    estimated_savings_annual=1800.0,
                    title="Underutilized VM",
                    recommendation="Downsize to Standard_D2_v3",
                    status="Active",
                ),
                Mock(
                    category="Cost",
                    impact="Medium",
                    estimated_savings_monthly=25.0,
                    estimated_savings_annual=300.0,
                    title="Unused storage",
                    recommendation="Delete unused storage account",
                    status="Active",
                ),
            ]

            # Mock total spend
            mock_db.get_total_monthly_spend.return_value = 5000.0

            mock_mgr.get_customer_db.return_value.__enter__ = Mock(return_value=mock_db)
            mock_mgr.get_customer_db.return_value.__exit__ = Mock(return_value=None)
            mock_mgr_class.return_value = mock_mgr

            generator = ReportGenerator()

            summary = generator.generate_executive_summary(
                customer_slug="customer_a",
                top_n=10
            )

            assert summary is not None
            assert summary.customer_name == "customer_a"
            assert summary.total_monthly_spend == 5000.0
            assert summary.potential_monthly_savings == 175.0  # 150 + 25
            assert summary.potential_annual_savings == 2100.0  # 1800 + 300
            assert summary.recommendation_count == 2
            assert summary.high_impact_count == 1
            assert len(summary.top_recommendations) <= 10

    def test_executive_summary_top_n_limit(self):
        """
        Verify executive summary respects top_n parameter.
        """
        from claude.tools.experimental.azure.report_generator import ReportGenerator

        with patch('claude.tools.experimental.azure.report_generator.CustomerDatabaseManager') as mock_mgr_class:
            mock_mgr = Mock()
            mock_db = Mock()

            # Create 20 mock recommendations
            recommendations = []
            for i in range(20):
                recommendations.append(Mock(
                    category="Cost",
                    impact="Medium",
                    estimated_savings_monthly=float(i * 10),
                    estimated_savings_annual=float(i * 120),
                    title=f"Recommendation {i}",
                    recommendation=f"Solution {i}",
                    status="Active",
                ))

            mock_db.get_all_recommendations.return_value = recommendations
            mock_db.get_total_monthly_spend.return_value = 10000.0

            mock_mgr.get_customer_db.return_value.__enter__ = Mock(return_value=mock_db)
            mock_mgr.get_customer_db.return_value.__exit__ = Mock(return_value=None)
            mock_mgr_class.return_value = mock_mgr

            generator = ReportGenerator()

            summary = generator.generate_executive_summary(
                customer_slug="customer_a",
                top_n=5
            )

            # Should only include top 5
            assert len(summary.top_recommendations) == 5

    def test_executive_summary_quick_wins_calculation(self):
        """
        Verify quick wins (low effort, high impact) are calculated correctly.
        """
        from claude.tools.experimental.azure.report_generator import ReportGenerator


        with patch('claude.tools.experimental.azure.report_generator.CustomerDatabaseManager') as mock_mgr_class:
            mock_mgr = Mock()
            mock_db = Mock()

            # Mock recommendations - some quick wins, some not
            mock_db.get_all_recommendations.return_value = [
                Mock(
                    category="Cost",
                    impact="High",
                    estimated_savings_monthly=150.0,
                    estimated_savings_annual=1800.0,
                    title="Delete orphaned disk",  # Quick win keyword
                    recommendation="Delete unattached disk",
                    status="Active",
                    metadata={"effort": "low"},
                ),
                Mock(
                    category="Cost",
                    impact="High",
                    estimated_savings_monthly=500.0,
                    estimated_savings_annual=6000.0,
                    title="Migrate to reserved instances",  # Not a quick win
                    recommendation="Purchase 3-year RI commitment",
                    status="Active",
                    metadata={"effort": "high"},
                ),
                Mock(
                    category="Cost",
                    impact="Low",
                    estimated_savings_monthly=10.0,
                    estimated_savings_annual=120.0,
                    title="Unassociated public IP",  # Quick win keyword
                    recommendation="Release unused IP",
                    status="Active",
                    metadata={"effort": "low"},
                ),
            ]

            mock_db.get_total_monthly_spend.return_value = 10000.0

            mock_mgr.get_customer_db.return_value.__enter__ = Mock(return_value=mock_db)
            mock_mgr.get_customer_db.return_value.__exit__ = Mock(return_value=None)
            mock_mgr_class.return_value = mock_mgr

            generator = ReportGenerator()

            summary = generator.generate_executive_summary(
                customer_slug="customer_a",
                top_n=10
            )

            # Quick wins should be orphaned disk + public IP = 160.0
            assert summary.quick_wins_savings == 160.0

    def test_executive_summary_data_freshness_warning(self):
        """
        Verify data freshness warning is included when data is stale.
        """
        from claude.tools.experimental.azure.report_generator import ReportGenerator


        with patch('claude.tools.experimental.azure.report_generator.CustomerDatabaseManager') as mock_mgr_class:
            mock_mgr = Mock()
            mock_db = Mock()

            mock_db.get_all_recommendations.return_value = []
            mock_db.get_total_monthly_spend.return_value = 5000.0

            # Mock stale data collection status (>48 hours old)
            stale_timestamp = datetime.now() - timedelta(hours=72)
            mock_db.get_data_collection_status.return_value = {
                "cost": stale_timestamp,
                "metrics": datetime.now(),
                "resources": datetime.now(),
            }

            mock_mgr.get_customer_db.return_value.__enter__ = Mock(return_value=mock_db)
            mock_mgr.get_customer_db.return_value.__exit__ = Mock(return_value=None)
            mock_mgr_class.return_value = mock_mgr

            generator = ReportGenerator()

            summary = generator.generate_executive_summary(
                customer_slug="customer_a",
                top_n=10
            )

            # Should have freshness warning
            assert summary.data_freshness_warning is not None
            assert "stale" in summary.data_freshness_warning.lower() or "old" in summary.data_freshness_warning.lower()


class TestDetailedReportGeneration:
    """Tests for detailed report generation."""

    def test_generate_detailed_report_json_format(self):
        """
        Verify detailed report can be generated in JSON format.
        """
        from claude.tools.experimental.azure.report_generator import ReportGenerator
        import json


        with patch('claude.tools.experimental.azure.report_generator.CustomerDatabaseManager') as mock_mgr_class:
            mock_mgr = Mock()
            mock_db = Mock()

            mock_db.get_all_recommendations.return_value = [
                Mock(
                    recommendation_id="rec-1",
                    category="Cost",
                    impact="High",
                    title="Test recommendation",
                    recommendation="Test solution",
                    estimated_savings_monthly=100.0,
                    estimated_savings_annual=1200.0,
                    resource_id="/subscriptions/sub-1/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm-1",
                    subscription_id="sub-1",
                    status="Active",
                ),
            ]

            mock_mgr.get_customer_db.return_value.__enter__ = Mock(return_value=mock_db)
            mock_mgr.get_customer_db.return_value.__exit__ = Mock(return_value=None)
            mock_mgr_class.return_value = mock_mgr

            generator = ReportGenerator()

            report = generator.generate_detailed_report(
                customer_slug="customer_a",
                format="json"
            )

            # Should be valid JSON
            parsed = json.loads(report)
            assert "recommendations" in parsed
            assert len(parsed["recommendations"]) == 1

    def test_generate_detailed_report_markdown_format(self):
        """
        Verify detailed report can be generated in Markdown format.
        """
        from claude.tools.experimental.azure.report_generator import ReportGenerator


        with patch('claude.tools.experimental.azure.report_generator.CustomerDatabaseManager') as mock_mgr_class:
            mock_mgr = Mock()
            mock_db = Mock()

            mock_db.get_all_recommendations.return_value = [
                Mock(
                    recommendation_id="rec-1",
                    category="Cost",
                    impact="High",
                    title="Test recommendation",
                    recommendation="Test solution",
                    estimated_savings_monthly=100.0,
                    estimated_savings_annual=1200.0,
                    resource_id="/subscriptions/sub-1/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm-1",
                    subscription_id="sub-1",
                    status="Active",
                ),
            ]

            mock_mgr.get_customer_db.return_value.__enter__ = Mock(return_value=mock_db)
            mock_mgr.get_customer_db.return_value.__exit__ = Mock(return_value=None)
            mock_mgr_class.return_value = mock_mgr

            generator = ReportGenerator()

            report = generator.generate_detailed_report(
                customer_slug="customer_a",
                format="markdown"
            )

            # Should contain markdown elements
            assert "# " in report or "## " in report  # Headers
            assert "**" in report or "*" in report   # Bold/italic

    def test_generate_detailed_report_filters_by_category(self):
        """
        Verify detailed report can filter recommendations by category.
        """
        from claude.tools.experimental.azure.report_generator import ReportGenerator
        import json


        with patch('claude.tools.experimental.azure.report_generator.CustomerDatabaseManager') as mock_mgr_class:
            mock_mgr = Mock()
            mock_db = Mock()

            mock_db.get_all_recommendations.return_value = [
                Mock(
                    recommendation_id="rec-1",
                    category="Cost",
                    impact="High",
                    title="Cost rec",
                    recommendation="Cost solution",
                    estimated_savings_monthly=100.0,
                    estimated_savings_annual=1200.0,
                    resource_id="/subscriptions/sub-1/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm-1",
                    subscription_id="sub-1",
                    status="Active",
                ),
                Mock(
                    recommendation_id="rec-2",
                    category="Performance",
                    impact="Medium",
                    title="Perf rec",
                    recommendation="Perf solution",
                    estimated_savings_monthly=0.0,
                    estimated_savings_annual=0.0,
                    resource_id="/subscriptions/sub-1/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm-2",
                    subscription_id="sub-1",
                    status="Active",
                ),
            ]

            mock_mgr.get_customer_db.return_value.__enter__ = Mock(return_value=mock_db)
            mock_mgr.get_customer_db.return_value.__exit__ = Mock(return_value=None)
            mock_mgr_class.return_value = mock_mgr

            generator = ReportGenerator()

            report = generator.generate_detailed_report(
                customer_slug="customer_a",
                format="json",
                category="Cost"
            )

            parsed = json.loads(report)
            # Should only include Cost recommendations
            assert len(parsed["recommendations"]) == 1
            assert parsed["recommendations"][0]["category"] == "Cost"

    def test_generate_detailed_report_filters_by_impact(self):
        """
        Verify detailed report can filter recommendations by impact.
        """
        from claude.tools.experimental.azure.report_generator import ReportGenerator
        import json


        with patch('claude.tools.experimental.azure.report_generator.CustomerDatabaseManager') as mock_mgr_class:
            mock_mgr = Mock()
            mock_db = Mock()

            mock_db.get_all_recommendations.return_value = [
                Mock(
                    recommendation_id="rec-1",
                    category="Cost",
                    impact="High",
                    title="High impact",
                    recommendation="Solution",
                    estimated_savings_monthly=100.0,
                    estimated_savings_annual=1200.0,
                    resource_id="/subscriptions/sub-1/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm-1",
                    subscription_id="sub-1",
                    status="Active",
                ),
                Mock(
                    recommendation_id="rec-2",
                    category="Cost",
                    impact="Low",
                    title="Low impact",
                    recommendation="Solution",
                    estimated_savings_monthly=5.0,
                    estimated_savings_annual=60.0,
                    resource_id="/subscriptions/sub-1/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm-2",
                    subscription_id="sub-1",
                    status="Active",
                ),
            ]

            mock_mgr.get_customer_db.return_value.__enter__ = Mock(return_value=mock_db)
            mock_mgr.get_customer_db.return_value.__exit__ = Mock(return_value=None)
            mock_mgr_class.return_value = mock_mgr

            generator = ReportGenerator()

            report = generator.generate_detailed_report(
                customer_slug="customer_a",
                format="json",
                min_impact="High"
            )

            parsed = json.loads(report)
            # Should only include High impact
            assert len(parsed["recommendations"]) == 1
            assert parsed["recommendations"][0]["impact"] == "High"


class TestReportValidation:
    """Tests for report validation and error handling."""

    def test_invalid_customer_slug_raises_error(self):
        """
        Verify invalid customer slug raises ValueError.
        """
        from claude.tools.experimental.azure.report_generator import ReportGenerator


        with patch('claude.tools.experimental.azure.report_generator.CustomerDatabaseManager') as mock_mgr_class:
            mock_mgr = Mock()
            mock_mgr.get_customer_db.side_effect = ValueError("Customer not found")
            mock_mgr_class.return_value = mock_mgr

            generator = ReportGenerator()

            with pytest.raises(ValueError, match="Customer not found"):
                generator.generate_executive_summary(
                    customer_slug="invalid_customer",
                    top_n=10
                )

    def test_unsupported_format_raises_error(self):
        """
        Verify unsupported report format raises ValueError.
        """
        from claude.tools.experimental.azure.report_generator import ReportGenerator


        with patch('claude.tools.experimental.azure.report_generator.CustomerDatabaseManager') as mock_mgr_class:
            mock_mgr = Mock()
            mock_db = Mock()
            mock_db.get_all_recommendations.return_value = []

            mock_mgr.get_customer_db.return_value.__enter__ = Mock(return_value=mock_db)
            mock_mgr.get_customer_db.return_value.__exit__ = Mock(return_value=None)
            mock_mgr_class.return_value = mock_mgr

            generator = ReportGenerator()

            with pytest.raises(ValueError, match="Unsupported format"):
                generator.generate_detailed_report(
                    customer_slug="customer_a",
                    format="invalid_format"
                )

    def test_empty_recommendations_handled_gracefully(self):
        """
        Verify report generation handles empty recommendations gracefully.
        """
        from claude.tools.experimental.azure.report_generator import ReportGenerator


        with patch('claude.tools.experimental.azure.report_generator.CustomerDatabaseManager') as mock_mgr_class:
            mock_mgr = Mock()
            mock_db = Mock()

            mock_db.get_all_recommendations.return_value = []
            mock_db.get_total_monthly_spend.return_value = 5000.0

            mock_mgr.get_customer_db.return_value.__enter__ = Mock(return_value=mock_db)
            mock_mgr.get_customer_db.return_value.__exit__ = Mock(return_value=None)
            mock_mgr_class.return_value = mock_mgr

            generator = ReportGenerator()

            summary = generator.generate_executive_summary(
                customer_slug="customer_a",
                top_n=10
            )

            # Should handle gracefully
            assert summary.recommendation_count == 0
            assert summary.potential_monthly_savings == 0.0
            assert len(summary.top_recommendations) == 0


class TestReportSorting:
    """Tests for recommendation sorting in reports."""

    def test_recommendations_sorted_by_savings_descending(self):
        """
        Verify recommendations are sorted by savings (highest first).
        """
        from claude.tools.experimental.azure.report_generator import ReportGenerator


        with patch('claude.tools.experimental.azure.report_generator.CustomerDatabaseManager') as mock_mgr_class:
            mock_mgr = Mock()
            mock_db = Mock()

            # Create recommendations with different savings
            mock_db.get_all_recommendations.return_value = [
                Mock(
                    category="Cost",
                    impact="Low",
                    estimated_savings_monthly=25.0,
                    estimated_savings_annual=300.0,
                    title="Small savings",
                    recommendation="Small solution",
                    status="Active",
                ),
                Mock(
                    category="Cost",
                    impact="High",
                    estimated_savings_monthly=200.0,
                    estimated_savings_annual=2400.0,
                    title="Large savings",
                    recommendation="Large solution",
                    status="Active",
                ),
                Mock(
                    category="Cost",
                    impact="Medium",
                    estimated_savings_monthly=100.0,
                    estimated_savings_annual=1200.0,
                    title="Medium savings",
                    recommendation="Medium solution",
                    status="Active",
                ),
            ]

            mock_db.get_total_monthly_spend.return_value = 10000.0

            mock_mgr.get_customer_db.return_value.__enter__ = Mock(return_value=mock_db)
            mock_mgr.get_customer_db.return_value.__exit__ = Mock(return_value=None)
            mock_mgr_class.return_value = mock_mgr

            generator = ReportGenerator()

            summary = generator.generate_executive_summary(
                customer_slug="customer_a",
                top_n=10
            )

            # Should be sorted by savings descending
            assert summary.top_recommendations[0]["savings"] == 200.0
            assert summary.top_recommendations[1]["savings"] == 100.0
            assert summary.top_recommendations[2]["savings"] == 25.0
