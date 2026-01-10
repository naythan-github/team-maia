#!/usr/bin/env python3
"""
Azure Cost Optimizer CLI

Command-line interface for Azure Cost Optimization Platform.

Usage:
    cost_optimizer register-customer --name "Aus-E-Mart" --slug aus_e_mart
    cost_optimizer add-subscription --customer aus_e_mart --subscription-id XXX
    cost_optimizer collect --customer aus_e_mart
    cost_optimizer report --customer aus_e_mart --format json
    cost_optimizer recommendations --customer aus_e_mart --top 10
    cost_optimizer list-customers

TDD Implementation - Tests in tests/test_cost_optimizer_cli.py
"""

import click
import logging
from pathlib import Path
from typing import Optional

from claude.tools.experimental.azure.customer_database import CustomerDatabaseManager, Customer
from claude.tools.experimental.azure.report_generator import ReportGenerator
from claude.tools.experimental.azure.azure_advisor import AzureAdvisorClient
from claude.tools.experimental.azure.resource_graph import ResourceGraphClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version='1.0.0', prog_name='Azure Cost Optimizer')
def cli() -> None:
    """
    Azure Cost Optimizer - Multi-tenant cost optimization platform.

    Analyze Azure spending, detect waste, and generate actionable recommendations.
    """
    pass


@cli.command('register-customer')
@click.option('--name', required=True, help='Customer display name (e.g., "Aus-E-Mart")')
@click.option('--slug', required=True, help='Customer slug identifier (e.g., "aus_e_mart")')
@click.option('--contact-email', help='Customer contact email')
def register_customer(name: str, slug: str, contact_email: Optional[str] = None) -> None:
    """
    Register a new customer in the system.

    Creates an isolated database for the customer.
    """
    try:
        from datetime import datetime
        import uuid

        db_manager = CustomerDatabaseManager()

        customer = Customer(
            customer_id=str(uuid.uuid4()),
            customer_slug=slug,
            customer_name=name,
            tenant_ids=[],
            subscription_ids=[],
            created_at=datetime.now(),
            is_active=True,
        )

        db_manager.register_customer(customer)

        click.echo(f"✅ Customer registered: {name} ({slug})")
        logger.info(f"Registered customer: {slug}")

    except Exception as e:
        click.echo(f"❌ Error registering customer: {e}", err=True)
        logger.error(f"Failed to register customer {slug}: {e}")
        raise click.Abort()


@cli.command('add-subscription')
@click.option('--customer', required=True, help='Customer slug')
@click.option('--subscription-id', required=True, help='Azure subscription ID')
def add_subscription(customer: str, subscription_id: str) -> None:
    """
    Add an Azure subscription to a customer.

    Links the subscription to the customer's database.
    """
    try:
        db_manager = CustomerDatabaseManager()
        db_manager.add_subscription_to_customer(customer, subscription_id)

        click.echo(f"✅ Subscription {subscription_id} added to {customer}")
        logger.info(f"Added subscription {subscription_id} to {customer}")

    except Exception as e:
        click.echo(f"❌ Error adding subscription: {e}", err=True)
        logger.error(f"Failed to add subscription {subscription_id} to {customer}: {e}")
        raise click.Abort()


@cli.command('list-customers')
@click.option('--active-only/--all', default=True, help='Show only active customers')
def list_customers(active_only: bool) -> None:
    """
    List all registered customers.
    """
    try:
        db_manager = CustomerDatabaseManager()
        customers = db_manager.list_customers(active_only=active_only)

        if not customers:
            click.echo("No customers found.")
            return

        click.echo("\nRegistered Customers:")
        click.echo("=" * 80)

        for customer in customers:
            status_icon = "✓" if customer.is_active else "✗"
            click.echo(f"{status_icon} {customer.customer_name} ({customer.customer_slug})")
            click.echo(f"   Subscriptions: {len(customer.subscription_ids)}")
            click.echo(f"   Customer ID: {customer.customer_id}")
            click.echo()

        click.echo(f"Total: {len(customers)} customer(s)")

    except Exception as e:
        click.echo(f"❌ Error listing customers: {e}", err=True)
        logger.error(f"Failed to list customers: {e}")
        raise click.Abort()


@cli.command('collect')
@click.option('--customer', required=True, help='Customer slug')
@click.option('--credential', help='Azure credential type (default: DefaultAzureCredential)', default='default')
def collect(customer: str, credential: str) -> None:
    """
    Collect cost data from Azure APIs for a customer.

    Orchestrates:
    - Azure Advisor recommendations
    - Resource Graph inventory
    - Cost Management data (if available)
    """
    try:
        from azure.identity import DefaultAzureCredential

        click.echo(f"🔄 Collecting data for {customer}...")

        # Get customer subscriptions
        db_manager = CustomerDatabaseManager()
        customer_obj = db_manager.get_customer(customer)

        if not customer_obj:
            click.echo(f"❌ Customer '{customer}' not found", err=True)
            raise click.Abort()

        subscriptions = customer_obj.subscription_ids

        if not subscriptions:
            click.echo(f"⚠️  No subscriptions found for {customer}. Add subscriptions first.")
            return

        click.echo(f"   Found {len(subscriptions)} subscription(s)")

        # Ensure subscriptions exist in customer database before syncing
        # (required for foreign key constraints on resources/recommendations tables)
        click.echo("   Initializing customer database...")
        from claude.tools.experimental.azure.customer_database import Subscription
        with db_manager.get_customer_db(customer) as customer_db:
            for sub_id in subscriptions:
                # Add minimal subscription record (will be enriched during collection)
                customer_db.add_subscription(Subscription(
                    subscription_id=sub_id,
                    subscription_name=f"Subscription {sub_id[:8]}",
                    tenant_id="00000000-0000-0000-0000-000000000000",  # Placeholder
                    state="Enabled"
                ))

        # Initialize Azure credential
        cred = DefaultAzureCredential()

        # Collect Advisor recommendations
        click.echo("\n📊 Collecting Azure Advisor recommendations...")
        advisor_client = AzureAdvisorClient(credential=cred)
        total_advisor_recs = 0

        # Use progress bar for multiple subscriptions
        if len(subscriptions) > 1:
            with click.progressbar(
                subscriptions,
                label='Processing subscriptions',
                show_eta=True,
                show_percent=True,
                item_show_func=lambda s: f"Processing {s}" if s else ""
            ) as bar:
                for sub_id in bar:
                    try:
                        count = advisor_client.sync_to_database(customer, sub_id)
                        total_advisor_recs += count
                        click.echo(f"   ✅ {sub_id}: {count} recommendations")
                    except Exception as e:
                        click.echo(f"   ⚠️  {sub_id}: {e}", err=True)
                        logger.warning(f"Failed to collect Advisor data for {sub_id}: {e}")
        else:
            # Single subscription - no progress bar needed
            for sub_id in subscriptions:
                try:
                    count = advisor_client.sync_to_database(customer, sub_id)
                    total_advisor_recs += count
                    click.echo(f"   ✅ {sub_id}: {count} recommendations")
                except Exception as e:
                    click.echo(f"   ⚠️  {sub_id}: {e}", err=True)
                    logger.warning(f"Failed to collect Advisor data for {sub_id}: {e}")

        # Collect Resource Graph inventory
        click.echo("\n🗂️  Collecting Resource Graph inventory...")
        graph_client = ResourceGraphClient(credential=cred)

        try:
            resource_count = graph_client.sync_resources_to_database(customer, subscriptions)
            click.echo(f"   ✅ Synced {resource_count} resources")
        except Exception as e:
            click.echo(f"   ⚠️  Resource Graph sync failed: {e}", err=True)
            logger.warning(f"Failed to collect Resource Graph data: {e}")

        click.echo(f"\n✅ Data collection complete for {customer}")
        click.echo(f"   Total Advisor recommendations: {total_advisor_recs}")

    except Exception as e:
        click.echo(f"❌ Error during data collection: {e}", err=True)
        logger.error(f"Failed to collect data for {customer}: {e}")
        raise click.Abort()


@cli.command('report')
@click.option('--customer', required=True, help='Customer slug')
@click.option('--format', type=click.Choice(['json', 'markdown']), default='json', help='Output format')
@click.option('--category', help='Filter by category (e.g., Cost)')
@click.option('--min-impact', type=click.Choice(['Low', 'Medium', 'High']), help='Minimum impact level')
@click.option('--output', '-o', type=click.Path(), help='Output file path (default: stdout)')
def report(customer: str, format: str, category: Optional[str], min_impact: Optional[str], output: Optional[str]) -> None:
    """
    Generate detailed cost optimization report.

    Outputs recommendations in JSON or Markdown format.
    """
    try:
        generator = ReportGenerator()

        click.echo(f"📝 Generating {format} report for {customer}...")

        report_content = generator.generate_detailed_report(
            customer_slug=customer,
            format=format,
            category=category,
            min_impact=min_impact,
        )

        if output:
            # Write to file
            Path(output).write_text(report_content)
            click.echo(f"✅ Report saved to {output}")
        else:
            # Print to stdout
            click.echo("\n" + "=" * 80)
            click.echo(report_content)
            click.echo("=" * 80)

    except Exception as e:
        click.echo(f"❌ Error generating report: {e}", err=True)
        logger.error(f"Failed to generate report for {customer}: {e}")
        raise click.Abort()


@cli.command('recommendations')
@click.option('--customer', required=True, help='Customer slug')
@click.option('--top', type=int, default=10, help='Number of top recommendations to show')
def recommendations(customer: str, top: int) -> None:
    """
    Show executive summary with top recommendations.

    Displays quick wins and high-impact recommendations.
    """
    try:
        generator = ReportGenerator()

        click.echo(f"💡 Generating executive summary for {customer}...")

        summary = generator.generate_executive_summary(
            customer_slug=customer,
            top_n=top
        )

        # Display summary
        click.echo("\n" + "=" * 80)
        click.echo(f"Executive Summary - {summary.customer_name}")
        click.echo("=" * 80)

        click.echo(f"\n📊 Monthly Spend: ${summary.total_monthly_spend:,.2f}")
        click.echo(f"💰 Potential Monthly Savings: ${summary.potential_monthly_savings:,.2f}")
        click.echo(f"💰 Potential Annual Savings: ${summary.potential_annual_savings:,.2f}")
        click.echo(f"⚡ Quick Wins Savings: ${summary.quick_wins_savings:,.2f}")
        click.echo(f"\n📋 Total Recommendations: {summary.recommendation_count}")
        click.echo(f"🔴 High Impact: {summary.high_impact_count}")

        if summary.data_freshness_warning:
            click.echo(f"\n⚠️  {summary.data_freshness_warning}")

        # Display top recommendations
        if summary.top_recommendations:
            click.echo(f"\n🏆 Top {len(summary.top_recommendations)} Recommendations:")
            click.echo("-" * 80)

            for i, rec in enumerate(summary.top_recommendations, 1):
                impact_icon = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(rec['impact'], "⚪")
                click.echo(f"\n{i}. {rec['title']}")
                click.echo(f"   {impact_icon} Impact: {rec['impact']} | 💰 Savings: ${rec['savings']:,.2f}/month")
                click.echo(f"   {rec['recommendation']}")

        click.echo("\n" + "=" * 80)

    except Exception as e:
        click.echo(f"❌ Error generating summary: {e}", err=True)
        logger.error(f"Failed to generate summary for {customer}: {e}")
        raise click.Abort()


if __name__ == '__main__':
    cli()
