"""
Phase 4 TDD Tests - Cost Optimizer CLI

Tests for command-line interface to Azure Cost Optimization platform.

Run with: pytest tests/test_cost_optimizer_cli.py -v
"""

import pytest
from click.testing import CliRunner
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path


class TestCLIBasics:
    """Tests for CLI initialization and basic commands."""

    def test_cli_entrypoint_exists(self):
        """
        Verify CLI entrypoint can be imported.
        """
        from claude.tools.experimental.azure.cost_optimizer_cli import cli

        assert cli is not None

    def test_cli_help_command(self):
        """
        Verify CLI help command works.
        """
        from claude.tools.experimental.azure.cost_optimizer_cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])

        assert result.exit_code == 0
        assert 'Azure Cost Optimizer' in result.output or 'cost' in result.output.lower()


class TestCustomerManagement:
    """Tests for customer registration and management."""

    def test_register_customer_command(self):
        """
        Verify customer registration command works.
        """
        from claude.tools.experimental.azure.cost_optimizer_cli import cli

        runner = CliRunner()

        with patch('claude.tools.experimental.azure.cost_optimizer_cli.CustomerDatabaseManager') as mock_mgr_class:
            mock_mgr = Mock()
            mock_mgr.register_customer = Mock()
            mock_mgr_class.return_value = mock_mgr

            result = runner.invoke(cli, [
                'register-customer',
                '--name', 'Aus-E-Mart',
                '--slug', 'aus_e_mart'
            ])

            assert result.exit_code == 0
            assert mock_mgr.register_customer.called

    def test_list_customers_command(self):
        """
        Verify list customers command works.
        """
        from claude.tools.experimental.azure.cost_optimizer_cli import cli
        from claude.tools.experimental.azure.customer_database import Customer
        from datetime import datetime

        runner = CliRunner()

        with patch('claude.tools.experimental.azure.cost_optimizer_cli.CustomerDatabaseManager') as mock_mgr_class:
            mock_mgr = Mock()
            mock_mgr.list_customers.return_value = [
                Customer(
                    customer_id="cust-1",
                    customer_slug="customer_a",
                    customer_name="Customer A",
                    tenant_ids=["tenant-1"],
                    subscription_ids=["sub-1"],
                    created_at=datetime.now(),
                    is_active=True,
                ),
                Customer(
                    customer_id="cust-2",
                    customer_slug="customer_b",
                    customer_name="Customer B",
                    tenant_ids=["tenant-2"],
                    subscription_ids=["sub-2"],
                    created_at=datetime.now(),
                    is_active=True,
                ),
            ]
            mock_mgr_class.return_value = mock_mgr

            result = runner.invoke(cli, ['list-customers'])

            assert result.exit_code == 0
            assert 'customer_a' in result.output or 'Customer A' in result.output

    def test_add_subscription_command(self):
        """
        Verify add subscription command works.
        """
        from claude.tools.experimental.azure.cost_optimizer_cli import cli

        runner = CliRunner()

        with patch('claude.tools.experimental.azure.cost_optimizer_cli.CustomerDatabaseManager') as mock_mgr_class:
            mock_mgr = Mock()
            mock_mgr.add_subscription = Mock()
            mock_mgr_class.return_value = mock_mgr

            result = runner.invoke(cli, [
                'add-subscription',
                '--customer', 'aus_e_mart',
                '--subscription-id', 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'
            ])

            assert result.exit_code == 0
            assert mock_mgr.add_subscription.called


class TestDataCollection:
    """Tests for data collection orchestration."""

    def test_collect_command_basic(self):
        """
        Verify collect command orchestrates data collection.
        """
        from claude.tools.experimental.azure.cost_optimizer_cli import cli

        runner = CliRunner()

        with patch('claude.tools.experimental.azure.cost_optimizer_cli.CustomerDatabaseManager') as mock_mgr_class:
            with patch('claude.tools.experimental.azure.cost_optimizer_cli.AzureAdvisorClient') as mock_advisor_class:
                with patch('claude.tools.experimental.azure.cost_optimizer_cli.ResourceGraphClient') as mock_graph_class:
                    mock_mgr = Mock()
                    mock_mgr.list_subscriptions.return_value = ["sub-1"]
                    mock_mgr_class.return_value = mock_mgr

                    mock_advisor = Mock()
                    mock_advisor.sync_to_database.return_value = 5
                    mock_advisor_class.return_value = mock_advisor

                    mock_graph = Mock()
                    mock_graph.sync_resources_to_database.return_value = 100
                    mock_graph_class.return_value = mock_graph

                    result = runner.invoke(cli, [
                        'collect',
                        '--customer', 'customer_a'
                    ])

                    # Should call data collection methods
                    assert result.exit_code == 0
                    assert mock_advisor.sync_to_database.called or 'collect' in result.output.lower()

    def test_collect_command_requires_customer(self):
        """
        Verify collect command requires --customer flag.
        """
        from claude.tools.experimental.azure.cost_optimizer_cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ['collect'])

        # Should fail without customer
        assert result.exit_code != 0 or 'customer' in result.output.lower()


class TestReporting:
    """Tests for report generation commands."""

    def test_report_command_json_format(self):
        """
        Verify report command generates JSON reports.
        """
        from claude.tools.experimental.azure.cost_optimizer_cli import cli

        runner = CliRunner()

        with patch('claude.tools.experimental.azure.cost_optimizer_cli.ReportGenerator') as mock_gen_class:
            mock_gen = Mock()
            mock_gen.generate_detailed_report.return_value = '{"recommendations": []}'
            mock_gen_class.return_value = mock_gen

            result = runner.invoke(cli, [
                'report',
                '--customer', 'customer_a',
                '--format', 'json'
            ])

            assert result.exit_code == 0
            assert mock_gen.generate_detailed_report.called

    def test_report_command_markdown_format(self):
        """
        Verify report command generates Markdown reports.
        """
        from claude.tools.experimental.azure.cost_optimizer_cli import cli

        runner = CliRunner()

        with patch('claude.tools.experimental.azure.cost_optimizer_cli.ReportGenerator') as mock_gen_class:
            mock_gen = Mock()
            mock_gen.generate_detailed_report.return_value = '# Cost Report\n\nTest report'
            mock_gen_class.return_value = mock_gen

            result = runner.invoke(cli, [
                'report',
                '--customer', 'customer_a',
                '--format', 'markdown'
            ])

            assert result.exit_code == 0
            assert mock_gen.generate_detailed_report.called

    def test_recommendations_command_top_n(self):
        """
        Verify recommendations command shows top N recommendations.
        """
        from claude.tools.experimental.azure.cost_optimizer_cli import cli

        runner = CliRunner()

        with patch('claude.tools.experimental.azure.cost_optimizer_cli.ReportGenerator') as mock_gen_class:
            from claude.tools.experimental.azure.report_generator import ExecutiveSummary
            from datetime import datetime

            mock_gen = Mock()
            mock_gen.generate_executive_summary.return_value = ExecutiveSummary(
                customer_name="customer_a",
                generated_at=datetime.now(),
                total_monthly_spend=5000.0,
                potential_monthly_savings=500.0,
                potential_annual_savings=6000.0,
                quick_wins_savings=100.0,
                recommendation_count=10,
                high_impact_count=3,
                data_freshness_warning=None,
                top_recommendations=[
                    {"title": "Rec 1", "savings": 100.0, "impact": "High", "recommendation": "Solution 1", "category": "Cost"},
                    {"title": "Rec 2", "savings": 50.0, "impact": "Medium", "recommendation": "Solution 2", "category": "Cost"},
                ],
            )
            mock_gen_class.return_value = mock_gen

            result = runner.invoke(cli, [
                'recommendations',
                '--customer', 'customer_a',
                '--top', '10'
            ])

            assert result.exit_code == 0
            assert mock_gen.generate_executive_summary.called


class TestOutputOptions:
    """Tests for output formatting and file saving."""

    def test_report_command_output_file(self):
        """
        Verify report can be saved to file.
        """
        from claude.tools.experimental.azure.cost_optimizer_cli import cli

        runner = CliRunner()

        with runner.isolated_filesystem():
            with patch('claude.tools.experimental.azure.cost_optimizer_cli.ReportGenerator') as mock_gen_class:
                mock_gen = Mock()
                mock_gen.generate_detailed_report.return_value = '{"recommendations": []}'
                mock_gen_class.return_value = mock_gen

                result = runner.invoke(cli, [
                    'report',
                    '--customer', 'customer_a',
                    '--format', 'json',
                    '--output', 'report.json'
                ])

                assert result.exit_code == 0
                # File should exist
                assert Path('report.json').exists()

    def test_report_command_stdout_output(self):
        """
        Verify report prints to stdout when no output file specified.
        """
        from claude.tools.experimental.azure.cost_optimizer_cli import cli

        runner = CliRunner()

        with patch('claude.tools.experimental.azure.cost_optimizer_cli.ReportGenerator') as mock_gen_class:
            mock_gen = Mock()
            report_content = '{"recommendations": [{"title": "Test"}]}'
            mock_gen.generate_detailed_report.return_value = report_content
            mock_gen_class.return_value = mock_gen

            result = runner.invoke(cli, [
                'report',
                '--customer', 'customer_a',
                '--format', 'json'
            ])

            assert result.exit_code == 0
            # Output should be in stdout
            assert 'Test' in result.output or 'recommendations' in result.output


class TestErrorHandling:
    """Tests for CLI error handling."""

    def test_invalid_customer_slug_error(self):
        """
        Verify CLI handles invalid customer gracefully.
        """
        from claude.tools.experimental.azure.cost_optimizer_cli import cli

        runner = CliRunner()

        with patch('claude.tools.experimental.azure.cost_optimizer_cli.CustomerDatabaseManager') as mock_mgr_class:
            mock_mgr = Mock()
            mock_mgr.get_customer_db.side_effect = ValueError("Customer not found")
            mock_mgr_class.return_value = mock_mgr

            result = runner.invoke(cli, [
                'report',
                '--customer', 'invalid_customer',
                '--format', 'json'
            ])

            # Should fail gracefully
            assert result.exit_code != 0 or 'error' in result.output.lower() or 'not found' in result.output.lower()

    def test_missing_required_arguments(self):
        """
        Verify CLI validates required arguments.
        """
        from claude.tools.experimental.azure.cost_optimizer_cli import cli

        runner = CliRunner()

        # Try to register customer without name
        result = runner.invoke(cli, ['register-customer', '--slug', 'test'])

        # Should fail
        assert result.exit_code != 0 or 'name' in result.output.lower()
