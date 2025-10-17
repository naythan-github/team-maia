#!/usr/bin/env python3
"""
ServiceDesk Quality Scorer - 5-Dimension Quality Assessment

Calculates composite quality score (0-100) across 5 dimensions:
1. Completeness (40 points) - Required fields populated
2. Validity (30 points) - Values in valid formats/ranges
3. Consistency (20 points) - Values consistent with business rules
4. Uniqueness (5 points) - Primary keys unique
5. Integrity (5 points) - Relationships between entities

Quality Grades:
- 90-100: 🟢 EXCELLENT (Production ready)
- 80-89: 🟡 GOOD (Acceptable quality)
- 70-79: 🟠 ACCEPTABLE (Usable but needs improvement)
- 60-69: 🔴 POOR (Major issues)
- 0-59: 🚨 FAILED (Critical issues)

Author: Maia
Created: 2025-10-17
Phase: 127 Day 4 - ServiceDesk ETL Quality Enhancement
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta


@dataclass
class ScoringConfig:
    """Configuration for quality scoring"""
    # Completeness weights (40 points total) - XLSX column names
    # Distributed across all entities: Comments (16pts) + Tickets (14pts) + Timesheets (10pts) = 40pts
    completeness_weights: Dict[str, Dict[str, float]] = field(default_factory=lambda: {
        'comments': {
            'CT-COMMENT-ID': 3.5,
            'CT-TKT-ID': 3.5,
            'CT-DATEAMDTIME': 3.5,
            'CT-COMMENT': 3.5,
            'CT-USERIDNAME': 1.0,
            'CT-VISIBLE-CUSTOMER': 1.0  # Sparse field, 0.1% = 100% score
        },
        'tickets': {
            'TKT-Ticket ID': 4.0,
            'TKT-Title': 3.5,
            'TKT-Created Time': 3.5,
            'TKT-Status': 2.0,
            'TKT-Assigned To User': 1.0
        },
        'timesheets': {
            'TS-Title': 3.0,  # Timesheet entry ID
            'TS-Hours': 3.0,
            'TS-Date': 2.5,
            'TS-User Username': 1.0,
            'TS-Crm ID': 0.5
        }
    })

    # Validity thresholds
    min_date: datetime = field(default_factory=lambda: datetime(2020, 1, 1))
    max_future_days: int = 30
    min_hours: float = 0.0
    max_hours: float = 24.0
    max_text_length: int = 100000
    max_consecutive_newlines: int = 100

    # CT-VISIBLE-CUSTOMER sparse field threshold
    ct_visible_customer_threshold: float = 0.001  # 0.1%

    # Orphaned timesheet expected range
    orphan_timesheet_min: float = 0.85
    orphan_timesheet_max: float = 0.95


@dataclass
class DimensionScore:
    """Score for a single quality dimension"""
    dimension: str
    score: float  # 0 to max_points
    max_points: float
    percentage: float  # 0-100
    details: Dict[str, any]


@dataclass
class QualityReport:
    """Complete quality assessment report"""
    timestamp: datetime
    dimension_scores: List[DimensionScore]
    composite_score: float  # 0-100
    quality_grade: str
    recommendation: str
    summary: Dict[str, any]

    def to_dict(self) -> Dict:
        """Convert report to dictionary"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'composite_score': self.composite_score,
            'quality_grade': self.quality_grade,
            'recommendation': self.recommendation,
            'dimension_scores': [
                {
                    'dimension': d.dimension,
                    'score': d.score,
                    'max_points': d.max_points,
                    'percentage': d.percentage,
                    'details': d.details
                }
                for d in self.dimension_scores
            ],
            'summary': self.summary
        }


class ServiceDeskQualityScorer:
    """
    5-dimension quality scoring system

    Implements comprehensive quality assessment with weighted scoring
    """

    def __init__(self, config: Optional[ScoringConfig] = None):
        """Initialize scorer with optional custom configuration"""
        self.config = config or ScoringConfig()

    def score_all(
        self,
        comments_df: pd.DataFrame,
        tickets_df: pd.DataFrame,
        timesheets_df: pd.DataFrame
    ) -> QualityReport:
        """
        Calculate comprehensive quality score across all dimensions

        Args:
            comments_df: Comments DataFrame
            tickets_df: Tickets DataFrame
            timesheets_df: Timesheets DataFrame

        Returns:
            QualityReport with dimension breakdown and composite score
        """
        print("Calculating quality scores across 5 dimensions...")

        dimension_scores = []

        # Dimension 1: Completeness (40 points)
        print("\n1. Completeness (40 points)...")
        completeness = self._score_completeness(comments_df, tickets_df, timesheets_df)
        dimension_scores.append(completeness)
        print(f"   Score: {completeness.score:.2f}/{completeness.max_points} ({completeness.percentage:.1f}%)")

        # Dimension 2: Validity (30 points)
        print("2. Validity (30 points)...")
        validity = self._score_validity(comments_df, tickets_df, timesheets_df)
        dimension_scores.append(validity)
        print(f"   Score: {validity.score:.2f}/{validity.max_points} ({validity.percentage:.1f}%)")

        # Dimension 3: Consistency (20 points)
        print("3. Consistency (20 points)...")
        consistency = self._score_consistency(comments_df, tickets_df, timesheets_df)
        dimension_scores.append(consistency)
        print(f"   Score: {consistency.score:.2f}/{consistency.max_points} ({consistency.percentage:.1f}%)")

        # Dimension 4: Uniqueness (5 points)
        print("4. Uniqueness (5 points)...")
        uniqueness = self._score_uniqueness(comments_df, tickets_df, timesheets_df)
        dimension_scores.append(uniqueness)
        print(f"   Score: {uniqueness.score:.2f}/{uniqueness.max_points} ({uniqueness.percentage:.1f}%)")

        # Dimension 5: Integrity (5 points)
        print("5. Integrity (5 points)...")
        integrity = self._score_integrity(comments_df, tickets_df, timesheets_df)
        dimension_scores.append(integrity)
        print(f"   Score: {integrity.score:.2f}/{integrity.max_points} ({integrity.percentage:.1f}%)")

        # Calculate composite score
        composite_score = sum(d.score for d in dimension_scores)
        quality_grade = self._get_quality_grade(composite_score)
        recommendation = self._get_recommendation(composite_score, dimension_scores)

        # Generate summary
        summary = self._generate_summary(comments_df, tickets_df, timesheets_df, dimension_scores)

        report = QualityReport(
            timestamp=datetime.now(),
            dimension_scores=dimension_scores,
            composite_score=round(composite_score, 2),
            quality_grade=quality_grade,
            recommendation=recommendation,
            summary=summary
        )

        return report

    def _score_completeness(
        self,
        comments_df: pd.DataFrame,
        tickets_df: pd.DataFrame,
        timesheets_df: pd.DataFrame
    ) -> DimensionScore:
        """Dimension 1: Completeness (40 points)"""
        total_score = 0.0
        max_points = 40.0
        details = {}

        # Score each entity type
        for entity_type, df in [('comments', comments_df), ('tickets', tickets_df), ('timesheets', timesheets_df)]:
            if entity_type in self.config.completeness_weights:
                entity_details = {}

                for col, weight in self.config.completeness_weights[entity_type].items():
                    if col in df.columns:
                        populated_pct = df[col].notna().sum() / len(df) if len(df) > 0 else 0

                        # Special case: CT-VISIBLE-CUSTOMER (sparse field)
                        if col == 'CT-VISIBLE-CUSTOMER':
                            # 0.1% populated = 100% score (expected sparse)
                            field_score = min(populated_pct / self.config.ct_visible_customer_threshold, 1.0) * weight
                        # Special case: crm_id (0 = valid admin time)
                        elif col == 'crm_id':
                            # Count 0 as populated
                            populated_or_zero = (df[col].notna() | (df[col] == 0)).sum() / len(df)
                            field_score = populated_or_zero * weight
                        else:
                            field_score = populated_pct * weight

                        total_score += field_score
                        entity_details[col] = {
                            'populated_pct': round(populated_pct * 100, 2),
                            'weight': weight,
                            'score': round(field_score, 2)
                        }

                details[entity_type] = entity_details

        percentage = (total_score / max_points) * 100 if max_points > 0 else 0

        return DimensionScore(
            dimension='completeness',
            score=total_score,
            max_points=max_points,
            percentage=round(percentage, 2),
            details=details
        )

    def _score_validity(
        self,
        comments_df: pd.DataFrame,
        tickets_df: pd.DataFrame,
        timesheets_df: pd.DataFrame
    ) -> DimensionScore:
        """Dimension 2: Validity (30 points)"""
        total_score = 0.0
        max_points = 30.0
        details = {}

        max_date = datetime.now() + timedelta(days=self.config.max_future_days)

        # Check 1: Dates parseable (10 points)
        dates_score = 0.0
        date_checks = []

        for name, df, date_col in [
            ('comments', comments_df, 'CT-DATEAMDTIME'),
            ('tickets', tickets_df, 'TKT-Created Time'),
            ('timesheets', timesheets_df, 'TS-Date')
        ]:
            if date_col in df.columns:
                try:
                    parsed_dates = pd.to_datetime(df[date_col], errors='coerce', dayfirst=True)
                    valid_pct = parsed_dates.notna().sum() / df[date_col].notna().sum() if df[date_col].notna().sum() > 0 else 1.0
                    dates_score += valid_pct * (10/3)  # 10 points divided by 3 entities
                    date_checks.append({
                        'entity': name,
                        'column': date_col,
                        'valid_pct': round(valid_pct * 100, 2)
                    })
                except Exception:
                    pass

        total_score += dates_score
        details['dates_parseable'] = {'score': round(dates_score, 2), 'checks': date_checks}

        # Check 2: Dates in valid range (10 points)
        range_score = 0.0
        range_checks = []

        for name, df, date_col in [
            ('comments', comments_df, 'CT-DATEAMDTIME'),
            ('tickets', tickets_df, 'TKT-Created Time'),
            ('timesheets', timesheets_df, 'TS-Date')
        ]:
            if date_col in df.columns:
                try:
                    dates = pd.to_datetime(df[date_col], errors='coerce', dayfirst=True)
                    valid_dates = dates[(dates >= self.config.min_date) & (dates <= max_date)]
                    valid_pct = len(valid_dates) / dates.notna().sum() if dates.notna().sum() > 0 else 1.0
                    range_score += valid_pct * (10/3)
                    range_checks.append({
                        'entity': name,
                        'column': date_col,
                        'valid_pct': round(valid_pct * 100, 2)
                    })
                except Exception:
                    pass

        total_score += range_score
        details['dates_valid_range'] = {'score': round(range_score, 2), 'checks': range_checks}

        # Check 3: Text integrity (10 points)
        text_score = 0.0

        if 'CT-COMMENT' in comments_df.columns:
            text_series = comments_df['CT-COMMENT'].dropna()

            # Check length
            valid_length = text_series[text_series.str.len().between(1, self.config.max_text_length)]
            length_pct = len(valid_length) / len(text_series) if len(text_series) > 0 else 1.0

            # Check no null bytes
            no_null_bytes = sum('\x00' not in str(x) for x in text_series)
            null_byte_pct = no_null_bytes / len(text_series) if len(text_series) > 0 else 1.0

            # Check no excessive newlines
            no_excessive_newlines = 0
            for text in text_series:
                max_consecutive = 0
                current = 0
                for char in str(text):
                    if char == '\n':
                        current += 1
                        max_consecutive = max(max_consecutive, current)
                    else:
                        current = 0
                if max_consecutive < self.config.max_consecutive_newlines:
                    no_excessive_newlines += 1

            newline_pct = no_excessive_newlines / len(text_series) if len(text_series) > 0 else 1.0

            text_score = (length_pct + null_byte_pct + newline_pct) / 3 * 10
            total_score += text_score

            details['text_integrity'] = {
                'score': round(text_score, 2),
                'length_valid_pct': round(length_pct * 100, 2),
                'no_null_bytes_pct': round(null_byte_pct * 100, 2),
                'no_excessive_newlines_pct': round(newline_pct * 100, 2)
            }

        percentage = (total_score / max_points) * 100 if max_points > 0 else 0

        return DimensionScore(
            dimension='validity',
            score=total_score,
            max_points=max_points,
            percentage=round(percentage, 2),
            details=details
        )

    def _score_consistency(
        self,
        comments_df: pd.DataFrame,
        tickets_df: pd.DataFrame,
        timesheets_df: pd.DataFrame
    ) -> DimensionScore:
        """Dimension 3: Consistency (20 points)"""
        total_score = 0.0
        max_points = 20.0
        details = {}

        # Check 1: Type consistency (10 points)
        type_score = 0.0
        type_checks = []

        for name, df, id_col in [
            ('comments', comments_df, 'CT-COMMENT-ID'),
            ('tickets', tickets_df, 'TKT-Ticket ID'),
            ('timesheets', timesheets_df, 'timesheet_entry_id')
        ]:
            if id_col in df.columns:
                try:
                    numeric_ids = pd.to_numeric(df[id_col], errors='coerce')
                    valid_pct = numeric_ids.notna().sum() / df[id_col].notna().sum() if df[id_col].notna().sum() > 0 else 1.0
                    type_score += valid_pct * (10/3)
                    type_checks.append({
                        'entity': name,
                        'column': id_col,
                        'numeric_pct': round(valid_pct * 100, 2)
                    })
                except Exception:
                    pass

        total_score += type_score
        details['type_consistency'] = {'score': round(type_score, 2), 'checks': type_checks}

        # Check 2: Temporal consistency (10 points)
        temporal_score = 0.0

        if 'TKT-Created Time' in tickets_df.columns:
            try:
                created = pd.to_datetime(tickets_df['TKT-Created Time'], errors='coerce', dayfirst=True)
                consistent_count = 0
                total_count = 0

                # Check created <= resolved
                if 'TKT-Modified Time' in tickets_df.columns:
                    resolved = pd.to_datetime(tickets_df['TKT-Modified Time'], errors='coerce', dayfirst=True)
                    both_present = created.notna() & resolved.notna()
                    if both_present.any():
                        consistent = created[both_present] <= resolved[both_present]
                        consistent_count += consistent.sum()
                        total_count += len(consistent)

                # Check resolved <= closed
                if 'TKT-Modified Time' in tickets_df.columns and 'TKT-Closed Time' in tickets_df.columns:
                    resolved = pd.to_datetime(tickets_df['TKT-Modified Time'], errors='coerce', dayfirst=True)
                    closed = pd.to_datetime(tickets_df['TKT-Closed Time'], errors='coerce', dayfirst=True)
                    both_present = resolved.notna() & closed.notna()
                    if both_present.any():
                        consistent = resolved[both_present] <= closed[both_present]
                        consistent_count += consistent.sum()
                        total_count += len(consistent)

                consistency_pct = consistent_count / total_count if total_count > 0 else 1.0
                temporal_score = consistency_pct * 10
                total_score += temporal_score

                details['temporal_consistency'] = {
                    'score': round(temporal_score, 2),
                    'consistent_count': consistent_count,
                    'total_checked': total_count,
                    'consistency_pct': round(consistency_pct * 100, 2)
                }
            except Exception as e:
                details['temporal_consistency'] = {'error': str(e)}

        percentage = (total_score / max_points) * 100 if max_points > 0 else 0

        return DimensionScore(
            dimension='consistency',
            score=total_score,
            max_points=max_points,
            percentage=round(percentage, 2),
            details=details
        )

    def _score_uniqueness(
        self,
        comments_df: pd.DataFrame,
        tickets_df: pd.DataFrame,
        timesheets_df: pd.DataFrame
    ) -> DimensionScore:
        """Dimension 4: Uniqueness (5 points)"""
        total_score = 0.0
        max_points = 5.0
        details = {}

        checks = []

        for name, df, id_col in [
            ('comments', comments_df, 'CT-COMMENT-ID'),
            ('tickets', tickets_df, 'TKT-Ticket ID'),
            ('timesheets', timesheets_df, 'timesheet_entry_id')
        ]:
            if id_col in df.columns:
                unique_count = df[id_col].nunique()
                total_count = df[id_col].notna().sum()
                uniqueness_pct = unique_count / total_count if total_count > 0 else 1.0

                score = uniqueness_pct * (5/3)
                total_score += score

                checks.append({
                    'entity': name,
                    'column': id_col,
                    'unique_count': unique_count,
                    'total_count': total_count,
                    'uniqueness_pct': round(uniqueness_pct * 100, 2),
                    'score': round(score, 2)
                })

        details['uniqueness_checks'] = checks

        percentage = (total_score / max_points) * 100 if max_points > 0 else 0

        return DimensionScore(
            dimension='uniqueness',
            score=total_score,
            max_points=max_points,
            percentage=round(percentage, 2),
            details=details
        )

    def _score_integrity(
        self,
        comments_df: pd.DataFrame,
        tickets_df: pd.DataFrame,
        timesheets_df: pd.DataFrame
    ) -> DimensionScore:
        """Dimension 5: Integrity (5 points)"""
        total_score = 0.0
        max_points = 5.0
        details = {}

        # Check 1: Comment→Ticket integrity (2 points)
        if 'CT-TKT-ID' in comments_df.columns and 'TKT-Ticket ID' in tickets_df.columns:
            comment_ticket_ids = set(pd.to_numeric(comments_df['CT-TKT-ID'], errors='coerce').dropna().astype(int))
            ticket_ids = set(pd.to_numeric(tickets_df['TKT-Ticket ID'], errors='coerce').dropna().astype(int))
            orphan_count = len(comment_ticket_ids - ticket_ids)
            orphan_rate = orphan_count / len(comment_ticket_ids) if len(comment_ticket_ids) > 0 else 0

            # Low orphan rate is good
            score = max(0, 2.0 * (1.0 - min(orphan_rate / 0.05, 1.0)))  # <5% orphan = full score
            total_score += score

            details['comment_ticket_integrity'] = {
                'orphan_count': orphan_count,
                'total_comments': len(comment_ticket_ids),
                'orphan_rate': round(orphan_rate * 100, 2),
                'score': round(score, 2)
            }

        # Check 2: Timesheet→Ticket integrity (2 points)
        if 'TS-Crm ID' in timesheets_df.columns and 'TKT-Ticket ID' in tickets_df.columns:
            timesheet_ticket_ids = set(pd.to_numeric(timesheets_df['TS-Crm ID'], errors='coerce').dropna().astype(int))
            timesheet_ticket_ids.discard(0)  # Exclude admin time
            ticket_ids = set(pd.to_numeric(tickets_df['TKT-Ticket ID'], errors='coerce').dropna().astype(int))
            orphan_count = len(timesheet_ticket_ids - ticket_ids)
            orphan_rate = orphan_count / len(timesheet_ticket_ids) if len(timesheet_ticket_ids) > 0 else 0

            # High orphan rate (85-95%) is EXPECTED
            in_expected_range = self.config.orphan_timesheet_min <= orphan_rate <= self.config.orphan_timesheet_max
            score = 2.0 if in_expected_range else 1.0  # Partial credit if outside range

            total_score += score

            details['timesheet_ticket_integrity'] = {
                'orphan_count': orphan_count,
                'total_timesheets': len(timesheet_ticket_ids),
                'orphan_rate': round(orphan_rate * 100, 2),
                'expected_range': f"{self.config.orphan_timesheet_min*100:.0f}-{self.config.orphan_timesheet_max*100:.0f}%",
                'in_expected_range': in_expected_range,
                'score': round(score, 2)
            }

        # Check 3: Admin time rate (1 point)
        if 'crm_id' in timesheets_df.columns:
            crm_ids = pd.to_numeric(timesheets_df['crm_id'], errors='coerce').fillna(0).astype(int)
            admin_time_count = (crm_ids == 0).sum()
            admin_time_rate = admin_time_count / len(crm_ids)

            # 10-30% expected
            in_expected_range = 0.10 <= admin_time_rate <= 0.30
            score = 1.0 if in_expected_range else 0.5

            total_score += score

            details['admin_time_rate'] = {
                'admin_time_count': admin_time_count,
                'total_timesheets': len(crm_ids),
                'admin_time_rate': round(admin_time_rate * 100, 2),
                'expected_range': '10-30%',
                'in_expected_range': in_expected_range,
                'score': round(score, 2)
            }

        percentage = (total_score / max_points) * 100 if max_points > 0 else 0

        return DimensionScore(
            dimension='integrity',
            score=total_score,
            max_points=max_points,
            percentage=round(percentage, 2),
            details=details
        )

    def _get_quality_grade(self, score: float) -> str:
        """Map composite score to quality grade"""
        if score >= 90:
            return "🟢 EXCELLENT"
        elif score >= 80:
            return "🟡 GOOD"
        elif score >= 70:
            return "🟠 ACCEPTABLE"
        elif score >= 60:
            return "🔴 POOR"
        else:
            return "🚨 FAILED"

    def _get_recommendation(self, score: float, dimensions: List[DimensionScore]) -> str:
        """Generate recommendation based on score and dimension breakdown"""
        if score >= 90:
            return "Production ready - High quality data suitable for immediate use"
        elif score >= 80:
            return "Acceptable quality - Minor issues present but data is usable"
        elif score >= 70:
            return "Usable but needs improvement - Consider data cleaning before production use"
        elif score >= 60:
            return "Major issues present - Investigation required before import"
        else:
            # Find weakest dimension
            weakest = min(dimensions, key=lambda d: d.percentage)
            return f"Critical issues - Do not import - Focus on improving {weakest.dimension} (only {weakest.percentage:.1f}%)"

    def _generate_summary(
        self,
        comments_df: pd.DataFrame,
        tickets_df: pd.DataFrame,
        timesheets_df: pd.DataFrame,
        dimensions: List[DimensionScore]
    ) -> Dict:
        """Generate summary statistics"""
        return {
            'total_records': len(comments_df) + len(tickets_df) + len(timesheets_df),
            'record_counts': {
                'comments': len(comments_df),
                'tickets': len(tickets_df),
                'timesheets': len(timesheets_df)
            },
            'dimension_summary': {
                d.dimension: {
                    'score': d.score,
                    'max_points': d.max_points,
                    'percentage': d.percentage
                }
                for d in dimensions
            },
            'weakest_dimension': min(dimensions, key=lambda d: d.percentage).dimension,
            'strongest_dimension': max(dimensions, key=lambda d: d.percentage).dimension
        }

    def print_report(self, report: QualityReport):
        """Print quality report to console"""
        print("\n" + "="*80)
        print("SERVICEDESK QUALITY SCORING REPORT")
        print("="*80)
        print(f"\nTimestamp: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Composite Score: {report.composite_score}/100")
        print(f"Quality Grade: {report.quality_grade}")
        print(f"Recommendation: {report.recommendation}")

        print(f"\nDimension Breakdown:")
        for dim in report.dimension_scores:
            print(f"\n  {dim.dimension.upper()}: {dim.score:.2f}/{dim.max_points} ({dim.percentage:.1f}%)")

            # Show key details
            if 'checks' in dim.details:
                for check in dim.details['checks'][:3]:  # Show first 3
                    print(f"    - {check}")

        print(f"\nSummary:")
        print(f"  Total Records: {report.summary['total_records']:,}")
        print(f"  Weakest Dimension: {report.summary['weakest_dimension']}")
        print(f"  Strongest Dimension: {report.summary['strongest_dimension']}")

        print("\n" + "="*80)


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="ServiceDesk Quality Scorer - 5-Dimension Quality Assessment")
    parser.add_argument('comments', type=Path, help="Path to comments.xlsx")
    parser.add_argument('tickets', type=Path, help="Path to tickets.xlsx")
    parser.add_argument('timesheets', type=Path, help="Path to timesheets.xlsx")
    parser.add_argument('--output', type=Path, help="Output path for JSON report")

    args = parser.parse_args()

    # Validate paths
    for path in [args.comments, args.tickets, args.timesheets]:
        if not path.exists():
            print(f"❌ Error: File not found: {path}")
            return 1

    # Load data
    print("Loading XLSX files...")
    comments_df = pd.read_excel(args.comments)
    tickets_df = pd.read_excel(args.tickets)
    timesheets_df = pd.read_excel(args.timesheets)

    # Run scoring
    scorer = ServiceDeskQualityScorer()
    report = scorer.score_all(comments_df, tickets_df, timesheets_df)

    # Print report
    scorer.print_report(report)

    # Save JSON if requested
    if args.output:
        import json
        with open(args.output, 'w') as f:
            json.dump(report.to_dict(), f, indent=2)
        print(f"\n✅ Report saved to: {args.output}")

    return 0 if report.composite_score >= 60 else 1


if __name__ == '__main__':
    exit(main())
