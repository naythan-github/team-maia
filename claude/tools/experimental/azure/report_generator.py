"""
Azure Cost Optimization Report Generator

Generates executive summaries and detailed reports for cost optimization
recommendations with data freshness warnings and savings calculations.

TDD Implementation - Tests in tests/test_report_generator.py
"""

import logging
import json
from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path

from claude.tools.experimental.azure.customer_database import CustomerDatabaseManager

logger = logging.getLogger(__name__)


class ImpactLevel(Enum):
    """
    Impact level hierarchy for recommendations.

    Used for filtering and prioritizing recommendations by impact.
    """
    LOW = 0
    MEDIUM = 1
    HIGH = 2

    @classmethod
    def from_string(cls, value: str) -> Optional['ImpactLevel']:
        """
        Convert string to ImpactLevel enum.

        Args:
            value: Impact level string (case-insensitive)

        Returns:
            ImpactLevel enum or None if invalid
        """
        try:
            return cls[value.upper()]
        except KeyError:
            return None


@dataclass
class ExecutiveSummary:
    """
    Executive summary for customer cost optimization.

    Provides high-level overview of savings potential and top recommendations.
    """
    customer_name: str
    generated_at: datetime
    total_monthly_spend: float
    potential_monthly_savings: float
    potential_annual_savings: float
    quick_wins_savings: float  # Low effort recommendations
    recommendation_count: int
    high_impact_count: int
    data_freshness_warning: Optional[str]
    top_recommendations: List[Dict[str, Any]]


class ReportGenerator:
    """
    Generates cost optimization reports for customers.

    Provides executive summaries, detailed reports in multiple formats,
    and data freshness tracking.

    Usage:
        generator = ReportGenerator()

        # Executive summary
        summary = generator.generate_executive_summary(
            customer_slug="aus_e_mart",
            top_n=10
        )

        # Detailed report
        report = generator.generate_detailed_report(
            customer_slug="aus_e_mart",
            format="json",
            category="Cost",
            min_impact="High"
        )
    """

    # Quick win keywords (lowercase)
    QUICK_WIN_KEYWORDS = [
        "orphaned",
        "unattached",
        "unassociated",
        "unused",
        "delete",
        "release",
        "remove",
    ]

    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize report generator.

        Args:
            base_path: Optional custom path for database files
        """
        self.base_path = base_path
        self.db_manager = CustomerDatabaseManager(base_path=base_path)
        self._quick_win_cache: Dict[str, bool] = {}  # Cache: recommendation_id -> is_quick_win

    def _recommendation_to_dict(self, rec: Any, include_ids: bool = False) -> Dict[str, Any]:
        """
        Convert recommendation object to dictionary with consistent field extraction.

        Args:
            rec: Recommendation object
            include_ids: Whether to include recommendation_id, resource_id, subscription_id

        Returns:
            Dictionary with recommendation fields
        """
        result = {
            "title": getattr(rec, 'title', ''),
            "recommendation": getattr(rec, 'recommendation', ''),
            "impact": getattr(rec, 'impact', ''),
            "category": getattr(rec, 'category', ''),
            "estimated_savings_monthly": getattr(rec, 'estimated_savings_monthly', 0),
            "estimated_savings_annual": getattr(rec, 'estimated_savings_annual', 0),
        }

        if include_ids:
            result.update({
                "id": getattr(rec, 'recommendation_id', ''),
                "resource_id": getattr(rec, 'resource_id', ''),
                "subscription_id": getattr(rec, 'subscription_id', ''),
            })

        return result

    def _is_quick_win(self, recommendation: Any) -> bool:
        """
        Determine if recommendation is a quick win (low effort, fast implementation).

        Checks metadata for effort level or uses keyword detection.
        Results are cached per recommendation_id for performance.

        Args:
            recommendation: Recommendation dict or object

        Returns:
            True if quick win, False otherwise
        """
        # Get recommendation ID for caching
        rec_id = self._get_value(recommendation, 'recommendation_id')

        # Check cache first
        if rec_id and rec_id in self._quick_win_cache:
            return self._quick_win_cache[rec_id]

        # Compute quick win status
        is_quick_win = False

        # Check metadata first
        metadata = self._get_value(recommendation, 'metadata', {})
        if isinstance(metadata, dict):
            effort = metadata.get('effort', '').lower()
            if effort == 'low':
                is_quick_win = True

        # Check title for quick win keywords (if not already determined)
        if not is_quick_win:
            title = self._get_value(recommendation, 'title', '').lower()
            for keyword in self.QUICK_WIN_KEYWORDS:
                if keyword in title:
                    is_quick_win = True
                    break

        # Cache the result if we have a recommendation ID
        if rec_id:
            self._quick_win_cache[rec_id] = is_quick_win

        return is_quick_win

    def _check_data_freshness(self, customer_db: Any) -> Optional[str]:
        """
        Check data collection freshness and generate warning if stale.

        Args:
            customer_db: Customer database instance

        Returns:
            Warning message if data is stale, None otherwise
        """
        try:
            # Check if database has get_data_collection_status method
            if not hasattr(customer_db, 'get_data_collection_status'):
                return None

            status = customer_db.get_data_collection_status()

            # Check cost data freshness (most critical)
            if 'cost' in status:
                cost_timestamp = status['cost']
                if isinstance(cost_timestamp, datetime):
                    hours_old = (datetime.now() - cost_timestamp).total_seconds() / 3600

                    # Warn if data is >48 hours old
                    if hours_old > 48:
                        days_old = int(hours_old / 24)
                        return f"Cost data is {days_old} days old. Recommendations may not reflect current state."

            return None

        except (AttributeError, TypeError, KeyError) as e:
            # Expected exceptions from status access or datetime operations
            logger.warning(f"Could not check data freshness: {e}")
            return None
        except Exception as e:
            # Unexpected exception - log as error and re-raise for investigation
            logger.error(f"Unexpected error checking data freshness: {e}")
            raise

    def generate_executive_summary(
        self,
        customer_slug: str,
        top_n: int = 10
    ) -> ExecutiveSummary:
        """
        Generate executive summary with top recommendations.

        Args:
            customer_slug: Customer identifier (e.g., "aus_e_mart")
            top_n: Number of top recommendations to include

        Returns:
            ExecutiveSummary object

        Raises:
            ValueError: If customer does not exist
        """
        with self.db_manager.get_customer_db(customer_slug) as db:
            # Get all active recommendations
            all_recommendations = db.get_all_recommendations()
            active_recommendations = [
                rec for rec in all_recommendations
                if getattr(rec, 'status', 'Active') == 'Active'
            ]

            # Calculate totals
            total_monthly_savings = sum(
                getattr(rec, 'estimated_savings_monthly', 0) or 0
                for rec in active_recommendations
            )

            total_annual_savings = sum(
                getattr(rec, 'estimated_savings_annual', 0) or 0
                for rec in active_recommendations
            )

            # Calculate quick wins savings
            quick_wins_savings = sum(
                getattr(rec, 'estimated_savings_monthly', 0) or 0
                for rec in active_recommendations
                if self._is_quick_win(rec)
            )

            # Count high impact recommendations
            high_impact_count = sum(
                1 for rec in active_recommendations
                if getattr(rec, 'impact', '') == 'High'
            )

            # Get total monthly spend
            total_monthly_spend = 0.0
            if hasattr(db, 'get_total_monthly_spend'):
                total_monthly_spend = db.get_total_monthly_spend()

            # Check data freshness
            data_freshness_warning = self._check_data_freshness(db)

            # Sort recommendations by savings (descending)
            sorted_recommendations = sorted(
                active_recommendations,
                key=lambda r: getattr(r, 'estimated_savings_monthly', 0) or 0,
                reverse=True
            )

            # Get top N recommendations
            top_recommendations = []
            for rec in sorted_recommendations[:top_n]:
                rec_dict = self._recommendation_to_dict(rec)
                # Add 'savings' alias for executive summary
                rec_dict["savings"] = rec_dict["estimated_savings_monthly"]
                top_recommendations.append(rec_dict)

            summary = ExecutiveSummary(
                customer_name=customer_slug,
                generated_at=datetime.now(),
                total_monthly_spend=total_monthly_spend,
                potential_monthly_savings=total_monthly_savings,
                potential_annual_savings=total_annual_savings,
                quick_wins_savings=quick_wins_savings,
                recommendation_count=len(active_recommendations),
                high_impact_count=high_impact_count,
                data_freshness_warning=data_freshness_warning,
                top_recommendations=top_recommendations,
            )

            logger.info(
                f"Generated executive summary for {customer_slug}: "
                f"{summary.recommendation_count} recommendations, "
                f"${summary.potential_monthly_savings:.2f}/month savings"
            )

            return summary

    def generate_detailed_report(
        self,
        customer_slug: str,
        format: str = "json",
        category: Optional[str] = None,
        min_impact: Optional[str] = None,
    ) -> str:
        """
        Generate detailed recommendation report.

        Args:
            customer_slug: Customer identifier (e.g., "aus_e_mart")
            format: Output format ("json" or "markdown")
            category: Optional category filter (e.g., "Cost")
            min_impact: Optional minimum impact filter (e.g., "High")

        Returns:
            Formatted report string

        Raises:
            ValueError: If customer does not exist or format is unsupported
        """
        # Validate format
        if format not in ["json", "markdown"]:
            raise ValueError(f"Unsupported format: {format}. Use 'json' or 'markdown'")

        # Convert min_impact to enum for type-safe filtering
        min_impact_enum = ImpactLevel.from_string(min_impact) if min_impact else None
        min_impact_level = min_impact_enum.value if min_impact_enum else -1

        with self.db_manager.get_customer_db(customer_slug) as db:
            # Get all active recommendations
            all_recommendations = db.get_all_recommendations()
            active_recommendations = [
                rec for rec in all_recommendations
                if getattr(rec, 'status', 'Active') == 'Active'
            ]

            # Filter by category if specified
            if category:
                active_recommendations = [
                    rec for rec in active_recommendations
                    if getattr(rec, 'category', '') == category
                ]

            # Filter by minimum impact if specified
            if min_impact_enum:
                active_recommendations = [
                    rec for rec in active_recommendations
                    if (rec_impact := ImpactLevel.from_string(getattr(rec, 'impact', 'Low')))
                    and rec_impact.value >= min_impact_level
                ]

            # Sort by savings descending
            sorted_recommendations = sorted(
                active_recommendations,
                key=lambda r: getattr(r, 'estimated_savings_monthly', 0) or 0,
                reverse=True
            )

            # Generate report based on format
            if format == "json":
                return self._generate_json_report(sorted_recommendations, customer_slug)
            elif format == "markdown":
                return self._generate_markdown_report(sorted_recommendations, customer_slug)

    def _generate_json_report(
        self,
        recommendations: List[Any],
        customer_slug: str
    ) -> str:
        """
        Generate JSON format report.

        Args:
            recommendations: List of recommendation objects
            customer_slug: Customer identifier

        Returns:
            JSON string
        """
        report = {
            "customer": customer_slug,
            "generated_at": datetime.now().isoformat(),
            "recommendation_count": len(recommendations),
            "recommendations": []
        }

        for rec in recommendations:
            report["recommendations"].append(self._recommendation_to_dict(rec, include_ids=True))

        return json.dumps(report, indent=2)

    def _generate_markdown_report(
        self,
        recommendations: List[Any],
        customer_slug: str
    ) -> str:
        """
        Generate Markdown format report with enhanced customer deliverable formatting.

        Args:
            recommendations: List of recommendation dicts
            customer_slug: Customer identifier

        Returns:
            Markdown string formatted for customer delivery
        """
        lines = []
        lines.append(f"# Azure Cost Optimization Report")
        lines.append(f"## Customer: {customer_slug}")
        lines.append("")
        lines.append(f"**Report Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Total Recommendations**: {len(recommendations)}")
        lines.append("")

        # Calculate total savings - handle both dict and object access
        total_monthly = sum(
            self._get_value(rec, 'estimated_savings_monthly', 0)
            for rec in recommendations
        )
        total_annual = sum(
            self._get_value(rec, 'estimated_savings_annual', 0)
            for rec in recommendations
        )

        # Count by impact level
        high_impact = sum(1 for rec in recommendations if self._get_value(rec, 'impact', '').upper() == 'HIGH')
        medium_impact = sum(1 for rec in recommendations if self._get_value(rec, 'impact', '').upper() == 'MEDIUM')
        low_impact = sum(1 for rec in recommendations if self._get_value(rec, 'impact', '').upper() == 'LOW')

        lines.append("## Executive Summary")
        lines.append("")
        lines.append(f"- **Potential Monthly Savings**: ${total_monthly:,.2f}")
        lines.append(f"- **Potential Annual Savings**: ${total_annual:,.2f}")
        lines.append(f"- **High Impact Recommendations**: {high_impact}")
        lines.append(f"- **Medium Impact Recommendations**: {medium_impact}")
        lines.append(f"- **Low Impact Recommendations**: {low_impact}")
        lines.append("")

        # Quick wins section
        quick_wins = [rec for rec in recommendations if self._is_quick_win(rec)]
        if quick_wins:
            quick_win_savings = sum(self._get_value(rec, 'estimated_savings_monthly', 0) for rec in quick_wins)
            lines.append("### Quick Wins (Low Effort, High Impact)")
            lines.append("")
            lines.append(f"**{len(quick_wins)} recommendations** with potential savings of **${quick_win_savings:,.2f}/month**")
            lines.append("")
            lines.append("These are low-effort optimizations that can typically be implemented within 1-2 hours:")
            lines.append("")
            for i, rec in enumerate(quick_wins[:5], 1):  # Show top 5 quick wins
                title = self._get_value(rec, 'title', 'Untitled')
                savings = self._get_value(rec, 'estimated_savings_monthly', 0)
                lines.append(f"{i}. {title} - ${savings:,.2f}/month")
            lines.append("")

        lines.append("---")
        lines.append("")
        lines.append("## Detailed Recommendations")
        lines.append("")

        for i, rec in enumerate(recommendations, 1):
            # Get recommendation details - handle both dict and object
            title = self._get_value(rec, 'title', 'Cost Optimization Opportunity')
            impact = self._get_value(rec, 'impact', 'Unknown')
            category = self._get_value(rec, 'category', 'Unknown')
            monthly_savings = self._get_value(rec, 'estimated_savings_monthly', 0)
            annual_savings = self._get_value(rec, 'estimated_savings_annual', 0)
            recommendation_text = self._get_value(rec, 'recommendation', 'See Azure Advisor for details')
            resource_id = self._get_value(rec, 'resource_id', '')

            # Format impact with emoji
            impact_emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(impact.upper(), "⚪")

            lines.append(f"### {i}. {title}")
            lines.append("")
            lines.append(f"{impact_emoji} **Impact Level**: {impact}")
            lines.append(f"📂 **Category**: {category}")
            lines.append(f"💰 **Monthly Savings**: ${monthly_savings:,.2f}")
            if annual_savings:
                lines.append(f"💰 **Annual Savings**: ${annual_savings:,.2f}")
            lines.append("")

            lines.append("**Description**:")
            lines.append(f"> {recommendation_text}")
            lines.append("")

            if resource_id:
                lines.append("**Affected Resource**:")
                lines.append(f"```")
                lines.append(f"{resource_id}")
                lines.append(f"```")
                lines.append("")

            # Add implementation guidance based on title/category
            if self._is_quick_win(rec):
                lines.append("**Implementation**:")
                lines.append("- ⏱️ **Effort**: Low (< 1 hour)")
                lines.append("- ⚠️ **Risk**: Low")
                lines.append("- ✅ **Priority**: Quick Win - Implement immediately")
                lines.append("")

                # Add specific commands for orphaned resources
                if 'disk' in title.lower() or 'disk' in recommendation_text.lower():
                    lines.append("**Azure CLI Commands**:")
                    lines.append("```bash")
                    lines.append("# List unattached disks")
                    lines.append("az disk list --query \"[?diskState=='Unattached']\" -o table")
                    lines.append("")
                    if resource_id:
                        disk_name = resource_id.split('/')[-1] if '/' in resource_id else resource_id
                        rg_match = '/resourceGroups/' in resource_id
                        if rg_match:
                            rg = resource_id.split('/resourceGroups/')[1].split('/')[0]
                            lines.append(f"# Delete this specific disk")
                            lines.append(f"az disk delete --resource-group {rg} --name {disk_name} --yes")
                    else:
                        lines.append("# Delete specific disk (replace values)")
                        lines.append("az disk delete --resource-group <RG_NAME> --name <DISK_NAME> --yes")
                    lines.append("```")
                    lines.append("")
            else:
                lines.append("**Implementation**:")
                lines.append("- ⏱️ **Effort**: Medium-High")
                lines.append("- ⚠️ **Risk**: Requires testing and validation")
                lines.append("- 📋 **Priority**: Plan during maintenance window")
                lines.append("")

            lines.append("---")
            lines.append("")

        # Footer with next steps
        lines.append("## Next Steps")
        lines.append("")
        lines.append("1. **Review Quick Wins** - Start with low-effort, high-impact optimizations")
        lines.append("2. **Validate Recommendations** - Confirm resources are truly unused/over-provisioned")
        lines.append("3. **Plan Implementation** - Schedule changes during appropriate maintenance windows")
        lines.append("4. **Track Savings** - Monitor billing after implementation to confirm savings")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("*Report generated by Azure Cost Optimization Platform v1.1.0*")
        lines.append("")

        return "\n".join(lines)

    def _get_value(self, rec: Any, key: str, default: Any = None) -> Any:
        """
        Get value from recommendation dict or object.

        Handles both dictionary access and object attribute access.
        """
        if isinstance(rec, dict):
            return rec.get(key, default) or default
        else:
            return getattr(rec, key, default) or default
