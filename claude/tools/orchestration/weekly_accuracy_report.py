#!/usr/bin/env python3
"""
Weekly Accuracy Report Generator - Phase 122

Generates comprehensive weekly reports on routing accuracy with
visualizations, trends, and actionable recommendations.

Usage:
    # Generate report for last week
    python3 weekly_accuracy_report.py

    # Generate report for specific date range
    python3 weekly_accuracy_report.py --start 2025-10-01 --end 2025-10-07

    # Generate and email report
    python3 weekly_accuracy_report.py --email

Output: claude/data/logs/routing_accuracy_YYYY-WW.md
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from accuracy_analyzer import AccuracyAnalyzer, AccuracyMetric, LowAccuracyPattern, ImprovementRecommendation


class WeeklyAccuracyReport:
    """Generates weekly routing accuracy reports"""

    def __init__(self):
        self.analyzer = AccuracyAnalyzer()
        self.maia_root = Path(__file__).resolve().parents[3]
        self.report_dir = self.maia_root / "claude" / "data" / "logs"
        self.report_dir.mkdir(parents=True, exist_ok=True)

    # =========================================================================
    # Report Section Helpers (Phase 230 Refactoring)
    # =========================================================================

    def _add_header_section(self, lines: List[str], start_date: datetime, end_date: datetime, days: int) -> None:
        """Add report header and executive summary."""
        lines.append(f"# Routing Accuracy Report")
        lines.append(f"**Period**: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')} ({days} days)")
        lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

    def _add_executive_summary(self, lines: List[str], overall: Dict) -> None:
        """Add executive summary section."""
        lines.append("## Executive Summary")
        lines.append("")
        status_emoji = "✅" if overall['acceptance_rate'] >= 0.80 else "⚠️" if overall['acceptance_rate'] >= 0.60 else "❌"
        lines.append(f"{status_emoji} **Overall Acceptance Rate**: {overall['acceptance_rate']:.1%} (Target: >80%)")
        lines.append(f"- **Total Suggestions**: {overall['total_suggestions']}")
        lines.append(f"- **Accepted**: {overall['accepted_count']} ({overall['acceptance_rate']:.1%})")
        lines.append(f"- **Rejected**: {overall['rejected_count']} ({overall['rejection_rate']:.1%})")
        lines.append(f"- **Avg Confidence**: {overall['avg_confidence']:.1%}")
        lines.append(f"- **Avg Query Complexity**: {overall['avg_complexity']:.1f}/10")
        lines.append("")

    def _add_key_findings(self, lines: List[str], overall: Dict, low_patterns: List) -> None:
        """Add key findings section."""
        lines.append("### Key Findings")
        lines.append("")
        if overall['acceptance_rate'] >= 0.80:
            lines.append("✅ **Excellent** - Routing accuracy exceeds target")
        elif overall['acceptance_rate'] >= 0.60:
            lines.append("⚠️  **Needs Improvement** - Routing accuracy below target")
        else:
            lines.append("❌ **Critical** - Routing accuracy significantly below target")
        if overall['total_suggestions'] < 10:
            lines.append("⚠️  **Low Sample Size** - Need more data for statistical significance")
        if low_patterns:
            lines.append(f"⚠️  **{len(low_patterns)} Low Accuracy Patterns** identified requiring attention")
        lines.append("")

    def _add_overall_metrics(self, lines: List[str], overall: Dict) -> None:
        """Add overall metrics table."""
        lines.append("## Overall Metrics")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Total Suggestions | {overall['total_suggestions']} |")
        lines.append(f"| Accepted | {overall['accepted_count']} ({overall['acceptance_rate']:.1%}) |")
        lines.append(f"| Rejected | {overall['rejected_count']} ({overall['rejection_rate']:.1%}) |")
        lines.append(f"| Average Confidence | {overall['avg_confidence']:.1%} |")
        lines.append(f"| Average Complexity | {overall['avg_complexity']:.1f}/10 |")
        lines.append("")

    def _add_accuracy_table(self, lines: List[str], title: str, first_col: str, metrics: List) -> None:
        """Add accuracy table section (reusable for category/complexity/strategy)."""
        lines.append(f"## {title}")
        lines.append("")
        if metrics:
            lines.append(f"| {first_col} | Acceptance Rate | Samples | Avg Confidence |")
            lines.append("|" + "-" * len(first_col) + "|-----------------|---------|----------------|")
            for metric in metrics:
                status = "✅" if metric.acceptance_rate >= 0.80 else "⚠️" if metric.acceptance_rate >= 0.60 else "❌"
                lines.append(f"| {status} {metric.value} | {metric.acceptance_rate:.1%} | {metric.sample_size} | {metric.avg_confidence:.1%} |")
        else:
            lines.append(f"*No {title.lower().replace('accuracy by ', '')} data available*")
        lines.append("")

    def _add_low_accuracy_patterns(self, lines: List[str], low_patterns: List) -> None:
        """Add low accuracy patterns section."""
        lines.append("## Low Accuracy Patterns")
        lines.append("")
        if low_patterns:
            lines.append("Patterns with acceptance rate <60% requiring attention:")
            lines.append("")
            for i, pattern in enumerate(low_patterns, 1):
                severity_emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}[pattern.severity]
                lines.append(f"### {i}. {severity_emoji} {pattern.pattern_type.title()}: {pattern.pattern_value}")
                lines.append("")
                lines.append(f"- **Acceptance Rate**: {pattern.acceptance_rate:.1%}")
                lines.append(f"- **Sample Size**: {pattern.sample_size}")
                lines.append(f"- **Avg Confidence**: {pattern.avg_confidence:.1%}")
                lines.append(f"- **Severity**: {pattern.severity.upper()}")
                lines.append(f"- **Recommendation**: {pattern.recommendation}")
                lines.append("")
        else:
            lines.append("✅ No low accuracy patterns detected")
        lines.append("")

    def _add_override_analysis(self, lines: List[str], override_analysis: Dict) -> None:
        """Add override analysis section."""
        lines.append("## Override Analysis")
        lines.append("")
        if override_analysis['override_types']:
            lines.append("### Override Types")
            lines.append("")
            lines.append("| Type | Count | Avg Confidence |")
            lines.append("|------|-------|----------------|")
            for override_type, data in override_analysis['override_types'].items():
                lines.append(f"| {override_type} | {data['count']} | {data['avg_confidence']:.1%} |")
            lines.append("")
        if override_analysis['top_reasons']:
            lines.append("### Top Override Reasons")
            lines.append("")
            lines.append("| Reason | Count |")
            lines.append("|--------|-------|")
            for reason_data in override_analysis['top_reasons'][:5]:
                lines.append(f"| {reason_data['reason']} | {reason_data['count']} |")
            lines.append("")
        else:
            lines.append("*No override data available*")
        lines.append("")

    def _add_recommendations(self, lines: List[str], recommendations: List) -> None:
        """Add improvement recommendations section."""
        lines.append("## Improvement Recommendations")
        lines.append("")
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                priority_emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}[rec.priority]
                lines.append(f"### {i}. {priority_emoji} {rec.category.replace('_', ' ').title()}")
                lines.append("")
                lines.append(f"**Priority**: {rec.priority.upper()}")
                lines.append("")
                lines.append(f"**Issue**: {rec.issue}")
                lines.append("")
                lines.append(f"**Recommendation**: {rec.recommendation}")
                lines.append("")
                lines.append(f"**Expected Impact**: {rec.expected_impact}")
                lines.append("")
                lines.append(f"**Implementation**: {rec.implementation}")
                lines.append("")
        else:
            lines.append("✅ No critical recommendations - system performing well")
        lines.append("")

    def _add_next_steps(self, lines: List[str], recommendations: List) -> None:
        """Add next steps and footer."""
        lines.append("## Next Steps")
        lines.append("")
        if recommendations:
            lines.append("1. Review and prioritize recommendations above")
            lines.append("2. Implement critical/high priority improvements")
            lines.append("3. Monitor acceptance rate for improvement")
            lines.append("4. Re-run analysis after 7 days")
        else:
            lines.append("1. Continue monitoring routing accuracy")
            lines.append("2. Watch for emerging low-accuracy patterns")
            lines.append("3. Review monthly trends")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("*Report generated by Phase 122: Routing Accuracy Monitoring System*")

    def generate_report(
        self,
        start_date: datetime,
        end_date: datetime,
        output_path: Path = None
    ) -> str:
        """Generate weekly accuracy report (refactored - Phase 230)."""
        days = (end_date - start_date).days

        # Generate report filename if not provided
        if output_path is None:
            week_num = start_date.isocalendar()[1]
            year = start_date.year
            output_path = self.report_dir / f"routing_accuracy_{year}-W{week_num:02d}.md"

        # Gather data
        overall = self.analyzer.get_overall_accuracy(days=days)
        by_category = self.analyzer.get_accuracy_by_category(days=days)
        by_complexity = self.analyzer.get_accuracy_by_complexity(days=days)
        by_strategy = self.analyzer.get_accuracy_by_strategy(days=days)
        low_patterns = self.analyzer.identify_low_accuracy_patterns(threshold=0.60, min_sample_size=3)
        recommendations = self.analyzer.generate_recommendations(days=days)
        override_analysis = self.analyzer.get_override_analysis(days=days)

        # Build report using helper methods
        lines = []
        self._add_header_section(lines, start_date, end_date, days)
        self._add_executive_summary(lines, overall)
        self._add_key_findings(lines, overall, low_patterns)
        self._add_overall_metrics(lines, overall)
        self._add_accuracy_table(lines, "Accuracy by Category", "Category", by_category)
        self._add_accuracy_table(lines, "Accuracy by Complexity", "Complexity Range", by_complexity)
        self._add_accuracy_table(lines, "Accuracy by Strategy", "Strategy", by_strategy)
        self._add_low_accuracy_patterns(lines, low_patterns)
        self._add_override_analysis(lines, override_analysis)
        self._add_recommendations(lines, recommendations)
        self._add_next_steps(lines, recommendations)

        # Write report to file
        report_content = "\n".join(lines)
        output_path.write_text(report_content)

        return report_content

    def generate_latest_report(self) -> Path:
        """Generate report for last 7 days"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        self.generate_report(start_date, end_date)

        # Return path to generated report
        week_num = start_date.isocalendar()[1]
        year = start_date.year
        return self.report_dir / f"routing_accuracy_{year}-W{week_num:02d}.md"


def main():
    """CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(description="Generate routing accuracy report")
    parser.add_argument('--start', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, help='End date (YYYY-MM-DD)')
    parser.add_argument('--output', type=str, help='Output file path')
    parser.add_argument('--email', action='store_true', help='Email report (future)')

    args = parser.parse_args()

    reporter = WeeklyAccuracyReport()

    # Parse dates
    if args.start and args.end:
        start_date = datetime.strptime(args.start, '%Y-%m-%d')
        end_date = datetime.strptime(args.end, '%Y-%m-%d')
        output_path = Path(args.output) if args.output else None

        report_content = reporter.generate_report(start_date, end_date, output_path)

        if output_path is None:
            week_num = start_date.isocalendar()[1]
            year = start_date.year
            output_path = reporter.report_dir / f"routing_accuracy_{year}-W{week_num:02d}.md"
    else:
        # Default: last 7 days
        output_path = reporter.generate_latest_report()
        report_content = output_path.read_text()

    print(f"✅ Report generated: {output_path}")
    print("")
    print("=" * 80)
    print(report_content)
    print("=" * 80)

    if args.email:
        print("")
        print("📧 Email functionality not yet implemented (Phase 123 enhancement)")


if __name__ == "__main__":
    main()
