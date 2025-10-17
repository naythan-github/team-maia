#!/usr/bin/env python3
"""
ServiceDesk ETL Validator - Pre-Import Validation Layer

Validates XLSX files before database import using 40 validation rules across 6 categories:
- Schema validation (10 rules)
- Field completeness (8 rules)
- Data type validation (8 rules)
- Business rules (8 rules)
- Referential integrity (4 rules)
- Text integrity (2 rules)

Quality gate: HALT import if composite score <60/100

Author: Maia
Created: 2025-10-17
Phase: 127 Day 4 - ServiceDesk ETL Quality Enhancement
"""

import pandas as pd
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta
import re
import sys

# Add tools directory to path for column mappings import
sys.path.insert(0, str(Path(__file__).parent))
from servicedesk_column_mappings import REQUIRED_XLSX_COLUMNS, get_xlsx_column


@dataclass
class ValidationConfig:
    """Configuration for validation rules"""
    # Schema expectations (actual XLSX column names from source system)
    comments_required_cols: List[str] = field(default_factory=lambda: REQUIRED_XLSX_COLUMNS['comments'])
    tickets_required_cols: List[str] = field(default_factory=lambda: REQUIRED_XLSX_COLUMNS['tickets'])
    timesheets_required_cols: List[str] = field(default_factory=lambda: REQUIRED_XLSX_COLUMNS['timesheets'])

    # Completeness thresholds (% populated expected)
    ct_visible_customer_threshold: float = 0.001  # 0.1% (sparse field)
    comment_text_threshold: float = 0.95  # 95%
    ticket_summary_threshold: float = 1.0  # 100%
    hours_threshold: float = 0.995  # 99.5%

    # Date range validation
    min_date: datetime = field(default_factory=lambda: datetime(2020, 1, 1))
    max_future_days: int = 30  # Allow up to 30 days in future

    # Business rules
    min_hours: float = 0.0
    max_hours: float = 24.0
    max_comment_length: int = 100000
    max_consecutive_newlines: int = 100
    max_consecutive_special_chars: int = 50

    # Referential integrity
    orphan_comment_threshold: float = 0.05  # <5% orphan rate acceptable
    orphan_timesheet_min: float = 0.85  # 85-95% expected
    orphan_timesheet_max: float = 0.95
    admin_time_crm_id_min: float = 0.10  # 10-30% expected
    admin_time_crm_id_max: float = 0.30


@dataclass
class ValidationResult:
    """Result of a single validation rule"""
    rule_name: str
    category: str
    passed: bool
    score: float  # 0.0 to 1.0
    message: str
    severity: str  # 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
    details: Optional[Dict] = None


@dataclass
class ValidationReport:
    """Complete validation report for all data sources"""
    timestamp: datetime
    results: List[ValidationResult]
    composite_score: float  # 0-100
    quality_grade: str
    should_proceed: bool
    summary: Dict[str, any]

    def to_dict(self) -> Dict:
        """Convert report to dictionary"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'composite_score': self.composite_score,
            'quality_grade': self.quality_grade,
            'should_proceed': self.should_proceed,
            'total_rules': len(self.results),
            'passed_rules': sum(1 for r in self.results if r.passed),
            'failed_rules': sum(1 for r in self.results if not r.passed),
            'summary': self.summary,
            'results': [
                {
                    'rule': r.rule_name,
                    'category': r.category,
                    'passed': r.passed,
                    'score': r.score,
                    'severity': r.severity,
                    'message': r.message
                }
                for r in self.results
            ]
        }


class ServiceDeskETLValidator:
    """
    Pre-import validation for ServiceDesk XLSX files

    Implements 40 validation rules across 6 categories with quality scoring
    """

    def __init__(self, config: Optional[ValidationConfig] = None):
        """Initialize validator with optional custom configuration"""
        self.config = config or ValidationConfig()
        self.results: List[ValidationResult] = []

    def validate_all(
        self,
        comments_path: Path,
        tickets_path: Path,
        timesheets_path: Path
    ) -> ValidationReport:
        """
        Execute all validation rules and generate comprehensive report

        Args:
            comments_path: Path to comments.xlsx
            tickets_path: Path to tickets.xlsx
            timesheets_path: Path to timesheets.xlsx

        Returns:
            ValidationReport with composite score and pass/fail decision
        """
        self.results = []

        # Load data
        print("Loading XLSX files...")
        comments_df = pd.read_excel(comments_path, nrows=None)
        tickets_df = pd.read_excel(tickets_path, nrows=None)
        timesheets_df = pd.read_excel(timesheets_path, nrows=None)

        print(f"Loaded: {len(comments_df):,} comments, {len(tickets_df):,} tickets, {len(timesheets_df):,} timesheets")

        # Run validation categories
        print("\n1. Schema Validation (10 rules)...")
        self._validate_schema(comments_df, tickets_df, timesheets_df)

        print("2. Field Completeness Validation (8 rules)...")
        self._validate_completeness(comments_df, tickets_df, timesheets_df)

        print("3. Data Type Validation (8 rules)...")
        self._validate_data_types(comments_df, tickets_df, timesheets_df)

        print("4. Business Rules Validation (8 rules)...")
        self._validate_business_rules(comments_df, tickets_df, timesheets_df)

        print("5. Referential Integrity Validation (4 rules)...")
        self._validate_referential_integrity(comments_df, tickets_df, timesheets_df)

        print("6. Text Integrity Validation (2 rules)...")
        self._validate_text_integrity(comments_df, tickets_df, timesheets_df)

        # Calculate composite score
        composite_score = self._calculate_composite_score()
        quality_grade = self._get_quality_grade(composite_score)
        should_proceed = self._should_proceed_with_import(composite_score)

        # Generate summary
        summary = self._generate_summary(comments_df, tickets_df, timesheets_df)

        report = ValidationReport(
            timestamp=datetime.now(),
            results=self.results,
            composite_score=composite_score,
            quality_grade=quality_grade,
            should_proceed=should_proceed,
            summary=summary
        )

        return report

    def _validate_schema(self, comments_df: pd.DataFrame, tickets_df: pd.DataFrame, timesheets_df: pd.DataFrame):
        """Schema validation (10 rules)"""

        # Rule 1-3: Required columns present
        for name, df, required_cols in [
            ('comments', comments_df, self.config.comments_required_cols),
            ('tickets', tickets_df, self.config.tickets_required_cols),
            ('timesheets', timesheets_df, self.config.timesheets_required_cols)
        ]:
            missing = set(required_cols) - set(df.columns)
            passed = len(missing) == 0
            score = 1.0 if passed else 0.0

            self.results.append(ValidationResult(
                rule_name=f"{name}_required_columns",
                category="schema",
                passed=passed,
                score=score,
                message=f"{name}: All required columns present" if passed else f"{name}: Missing columns: {missing}",
                severity="CRITICAL" if not passed else "LOW",
                details={'missing_columns': list(missing)} if not passed else None
            ))

        # Rule 4-6: Column count in expected range
        for name, df, min_cols in [
            ('comments', comments_df, 8),
            ('tickets', tickets_df, 20),
            ('timesheets', timesheets_df, 10)
        ]:
            col_count = len(df.columns)
            passed = col_count >= min_cols
            score = 1.0 if passed else 0.5

            self.results.append(ValidationResult(
                rule_name=f"{name}_column_count",
                category="schema",
                passed=passed,
                score=score,
                message=f"{name}: {col_count} columns (expected >={min_cols})",
                severity="MEDIUM" if not passed else "LOW",
                details={'column_count': col_count, 'min_expected': min_cols}
            ))

        # Rule 7-9: Row count sanity check (>0)
        for name, df in [('comments', comments_df), ('tickets', tickets_df), ('timesheets', timesheets_df)]:
            row_count = len(df)
            passed = row_count > 0
            score = 1.0 if passed else 0.0

            self.results.append(ValidationResult(
                rule_name=f"{name}_row_count",
                category="schema",
                passed=passed,
                score=score,
                message=f"{name}: {row_count:,} rows",
                severity="CRITICAL" if not passed else "LOW",
                details={'row_count': row_count}
            ))

        # Rule 10: Overall schema health
        schema_results = [r for r in self.results if r.category == "schema"]
        schema_score = sum(r.score for r in schema_results) / len(schema_results) if schema_results else 0
        passed = schema_score >= 0.9

        self.results.append(ValidationResult(
            rule_name="overall_schema_health",
            category="schema",
            passed=passed,
            score=schema_score,
            message=f"Overall schema health: {schema_score*100:.1f}%",
            severity="HIGH" if not passed else "LOW"
        ))

    def _validate_completeness(self, comments_df: pd.DataFrame, tickets_df: pd.DataFrame, timesheets_df: pd.DataFrame):
        """Field completeness validation (8 rules)"""

        # Comments completeness (using XLSX column names)
        comment_rules = [
            ('CT-COMMENT-ID', 1.0, 8),
            ('CT-TKT-ID', 0.99, 8),
            ('CT-DATEAMDTIME', 1.0, 8),
            ('CT-COMMENT', self.config.comment_text_threshold, 8),
            ('CT-USERIDNAME', 0.98, 4),
            ('CT-VISIBLE-CUSTOMER', self.config.ct_visible_customer_threshold, 4)
        ]

        for col, threshold, weight in comment_rules:
            if col in comments_df.columns:
                populated_pct = comments_df[col].notna().sum() / len(comments_df)
                passed = populated_pct >= threshold
                score = min(populated_pct / threshold, 1.0) if threshold > 0 else 1.0

                self.results.append(ValidationResult(
                    rule_name=f"comments_{col}_completeness",
                    category="completeness",
                    passed=passed,
                    score=score,
                    message=f"comments.{col}: {populated_pct*100:.2f}% populated (threshold: {threshold*100:.2f}%)",
                    severity="HIGH" if not passed and weight >= 8 else "MEDIUM",
                    details={'populated_pct': populated_pct, 'threshold': threshold, 'weight': weight}
                ))

        # Tickets completeness (using XLSX column names)
        if 'TKT-Ticket ID' in tickets_df.columns:
            populated_pct = tickets_df['TKT-Ticket ID'].notna().sum() / len(tickets_df)
            passed = populated_pct >= 1.0

            self.results.append(ValidationResult(
                rule_name="tickets_id_completeness",
                category="completeness",
                passed=passed,
                score=populated_pct,
                message=f"tickets.TKT-Ticket ID: {populated_pct*100:.2f}% populated",
                severity="CRITICAL" if not passed else "LOW",
                details={'populated_pct': populated_pct}
            ))

        # Timesheets completeness (using XLSX column names)
        if 'TS-Hours' in timesheets_df.columns:
            populated_pct = timesheets_df['TS-Hours'].notna().sum() / len(timesheets_df)
            passed = populated_pct >= self.config.hours_threshold

            self.results.append(ValidationResult(
                rule_name="timesheets_hours_completeness",
                category="completeness",
                passed=passed,
                score=min(populated_pct / self.config.hours_threshold, 1.0),
                message=f"timesheets.TS-Hours: {populated_pct*100:.2f}% populated",
                severity="HIGH" if not passed else "LOW",
                details={'populated_pct': populated_pct}
            ))

    def _validate_data_types(self, comments_df: pd.DataFrame, tickets_df: pd.DataFrame, timesheets_df: pd.DataFrame):
        """Data type validation (8 rules)"""

        # Rule 1-3: IDs are numeric (convertible to int)
        # Use XLSX column names (not database column names)
        for name, df, id_col in [
            ('comments', comments_df, 'CT-COMMENT-ID'),
            ('tickets', tickets_df, 'TKT-Ticket ID'),
            ('timesheets', timesheets_df, 'TS-Title')  # Timesheet entry ID
        ]:
            if id_col in df.columns:
                try:
                    # Try converting to numeric, count failures
                    numeric_series = pd.to_numeric(df[id_col], errors='coerce')
                    valid_count = numeric_series.notna().sum()
                    total_count = df[id_col].notna().sum()
                    valid_pct = valid_count / total_count if total_count > 0 else 0
                    passed = valid_pct >= 0.999  # Allow 0.1% failure

                    self.results.append(ValidationResult(
                        rule_name=f"{name}_{id_col}_numeric",
                        category="data_types",
                        passed=passed,
                        score=valid_pct,
                        message=f"{name}.{id_col}: {valid_pct*100:.2f}% numeric",
                        severity="CRITICAL" if not passed else "LOW",
                        details={'valid_count': int(valid_count), 'total_count': int(total_count)}
                    ))
                except Exception as e:
                    self.results.append(ValidationResult(
                        rule_name=f"{name}_{id_col}_numeric",
                        category="data_types",
                        passed=False,
                        score=0.0,
                        message=f"{name}.{id_col}: Conversion failed: {str(e)}",
                        severity="CRITICAL"
                    ))

        # Rule 4-6: Dates are parseable
        # Use XLSX column names (not database column names)
        for name, df, date_col in [
            ('comments', comments_df, 'CT-DATEAMDTIME'),
            ('tickets', tickets_df, 'TKT-Created Time'),
            ('timesheets', timesheets_df, 'TS-Date')
        ]:
            if date_col in df.columns:
                try:
                    parsed_dates = pd.to_datetime(df[date_col], errors='coerce', dayfirst=True)
                    valid_count = parsed_dates.notna().sum()
                    total_count = df[date_col].notna().sum()
                    valid_pct = valid_count / total_count if total_count > 0 else 0
                    passed = valid_pct >= 0.999  # Allow 0.1% failure

                    self.results.append(ValidationResult(
                        rule_name=f"{name}_{date_col}_parseable",
                        category="data_types",
                        passed=passed,
                        score=valid_pct,
                        message=f"{name}.{date_col}: {valid_pct*100:.2f}% parseable dates",
                        severity="HIGH" if not passed else "LOW",
                        details={'valid_count': int(valid_count), 'total_count': int(total_count)}
                    ))
                except Exception as e:
                    self.results.append(ValidationResult(
                        rule_name=f"{name}_{date_col}_parseable",
                        category="data_types",
                        passed=False,
                        score=0.0,
                        message=f"{name}.{date_col}: Parsing failed: {str(e)}",
                        severity="HIGH"
                    ))

        # Rule 7: Hours are numeric and in valid range
        # Use XLSX column name
        if 'TS-Hours' in timesheets_df.columns:
            try:
                hours_numeric = pd.to_numeric(timesheets_df['TS-Hours'], errors='coerce')
                valid_hours = hours_numeric[(hours_numeric > self.config.min_hours) & (hours_numeric <= self.config.max_hours)]
                valid_pct = len(valid_hours) / timesheets_df['TS-Hours'].notna().sum()
                passed = valid_pct >= 0.995

                self.results.append(ValidationResult(
                    rule_name="timesheets_hours_valid_range",
                    category="data_types",
                    passed=passed,
                    score=valid_pct,
                    message=f"timesheets.hours: {valid_pct*100:.2f}% in valid range (0-24)",
                    severity="HIGH" if not passed else "LOW",
                    details={'valid_pct': valid_pct, 'min': self.config.min_hours, 'max': self.config.max_hours}
                ))
            except Exception as e:
                self.results.append(ValidationResult(
                    rule_name="timesheets_hours_valid_range",
                    category="data_types",
                    passed=False,
                    score=0.0,
                    message=f"timesheets.hours: Validation failed: {str(e)}",
                    severity="HIGH"
                ))

        # Rule 8: Text fields are strings (valid UTF-8)
        # Use XLSX column name
        if 'CT-COMMENT' in comments_df.columns:
            text_series = comments_df['CT-COMMENT'].dropna()
            valid_count = sum(isinstance(x, str) for x in text_series)
            valid_pct = valid_count / len(text_series) if len(text_series) > 0 else 1.0
            passed = valid_pct >= 0.99

            self.results.append(ValidationResult(
                rule_name="comments_text_valid_utf8",
                category="data_types",
                passed=passed,
                score=valid_pct,
                message=f"comments.comment_text: {valid_pct*100:.2f}% valid strings",
                severity="MEDIUM" if not passed else "LOW",
                details={'valid_count': valid_count, 'total_count': len(text_series)}
            ))

    def _validate_business_rules(self, comments_df: pd.DataFrame, tickets_df: pd.DataFrame, timesheets_df: pd.DataFrame):
        """Business rules validation (8 rules)"""

        max_date = datetime.now() + timedelta(days=self.config.max_future_days)

        # Rule 1-3: Dates in valid range
        # Use XLSX column names (not database column names)
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
                    passed = valid_pct >= 0.999

                    self.results.append(ValidationResult(
                        rule_name=f"{name}_{date_col}_valid_range",
                        category="business_rules",
                        passed=passed,
                        score=valid_pct,
                        message=f"{name}.{date_col}: {valid_pct*100:.2f}% in valid range",
                        severity="MEDIUM" if not passed else "LOW",
                        details={'min_date': self.config.min_date.isoformat(), 'max_date': max_date.isoformat()}
                    ))
                except Exception:
                    pass

        # Rule 4: Comment text length
        # Use XLSX column name
        if 'CT-COMMENT' in comments_df.columns:
            text_series = comments_df['CT-COMMENT'].dropna()
            valid_lengths = text_series[text_series.str.len().between(1, self.config.max_comment_length)]
            valid_pct = len(valid_lengths) / len(text_series) if len(text_series) > 0 else 1.0
            passed = valid_pct >= 0.95

            self.results.append(ValidationResult(
                rule_name="comments_text_length_valid",
                category="business_rules",
                passed=passed,
                score=valid_pct,
                message=f"comments.comment_text: {valid_pct*100:.2f}% valid length (1-{self.config.max_comment_length})",
                severity="MEDIUM" if not passed else "LOW"
            ))

        # Rule 5-7: IDs are positive
        # Use XLSX column names (not database column names)
        for name, df, id_col in [
            ('comments', comments_df, 'CT-COMMENT-ID'),
            ('tickets', tickets_df, 'TKT-Ticket ID'),
            ('timesheets', timesheets_df, 'TS-Title')  # Timesheet entry ID
        ]:
            if id_col in df.columns:
                try:
                    numeric_ids = pd.to_numeric(df[id_col], errors='coerce')
                    valid_ids = numeric_ids[numeric_ids > 0]
                    valid_pct = len(valid_ids) / numeric_ids.notna().sum() if numeric_ids.notna().sum() > 0 else 1.0
                    passed = valid_pct >= 0.999

                    self.results.append(ValidationResult(
                        rule_name=f"{name}_{id_col}_positive",
                        category="business_rules",
                        passed=passed,
                        score=valid_pct,
                        message=f"{name}.{id_col}: {valid_pct*100:.2f}% positive",
                        severity="CRITICAL" if not passed else "LOW"
                    ))
                except Exception:
                    pass

        # Rule 8: Overall business rules compliance
        business_results = [r for r in self.results if r.category == "business_rules"]
        business_score = sum(r.score for r in business_results) / len(business_results) if business_results else 1.0
        passed = business_score >= 0.9

        self.results.append(ValidationResult(
            rule_name="overall_business_rules_compliance",
            category="business_rules",
            passed=passed,
            score=business_score,
            message=f"Overall business rules compliance: {business_score*100:.1f}%",
            severity="MEDIUM" if not passed else "LOW"
        ))

    def _validate_referential_integrity(self, comments_df: pd.DataFrame, tickets_df: pd.DataFrame, timesheets_df: pd.DataFrame):
        """Referential integrity validation (4 rules)"""

        # Rule 1: Comment→Ticket orphan rate
        # Use XLSX column names (not database column names)
        if 'CT-TKT-ID' in comments_df.columns and 'TKT-Ticket ID' in tickets_df.columns:
            comment_ticket_ids = set(pd.to_numeric(comments_df['CT-TKT-ID'], errors='coerce').dropna().astype(int))
            ticket_ids = set(pd.to_numeric(tickets_df['TKT-Ticket ID'], errors='coerce').dropna().astype(int))
            orphan_count = len(comment_ticket_ids - ticket_ids)
            orphan_rate = orphan_count / len(comment_ticket_ids) if len(comment_ticket_ids) > 0 else 0
            passed = orphan_rate <= self.config.orphan_comment_threshold
            score = max(0, 1.0 - (orphan_rate / self.config.orphan_comment_threshold))

            self.results.append(ValidationResult(
                rule_name="comment_ticket_referential_integrity",
                category="referential_integrity",
                passed=passed,
                score=score,
                message=f"Comment→Ticket: {orphan_rate*100:.2f}% orphan rate (threshold: {self.config.orphan_comment_threshold*100:.1f}%)",
                severity="HIGH" if not passed else "LOW",
                details={'orphan_count': orphan_count, 'total_comments': len(comment_ticket_ids)}
            ))

        # Rule 2: Timesheet→Ticket orphan rate (85-95% EXPECTED)
        # Use XLSX column names (not database column names)
        if 'TS-Crm ID' in timesheets_df.columns and 'TKT-Ticket ID' in tickets_df.columns:
            timesheet_ticket_ids = set(pd.to_numeric(timesheets_df['TS-Crm ID'], errors='coerce').dropna().astype(int))
            timesheet_ticket_ids.discard(0)  # Exclude admin time
            ticket_ids = set(pd.to_numeric(tickets_df['TKT-Ticket ID'], errors='coerce').dropna().astype(int))
            orphan_count = len(timesheet_ticket_ids - ticket_ids)
            orphan_rate = orphan_count / len(timesheet_ticket_ids) if len(timesheet_ticket_ids) > 0 else 0

            # Score based on proximity to expected range
            in_expected_range = self.config.orphan_timesheet_min <= orphan_rate <= self.config.orphan_timesheet_max
            passed = in_expected_range
            score = 1.0 if in_expected_range else 0.7  # Partial credit if outside range

            severity = "LOW" if in_expected_range else "MEDIUM"
            message = f"Timesheet→Ticket: {orphan_rate*100:.1f}% orphan rate (expected: {self.config.orphan_timesheet_min*100:.0f}-{self.config.orphan_timesheet_max*100:.0f}%)"

            self.results.append(ValidationResult(
                rule_name="timesheet_ticket_referential_integrity",
                category="referential_integrity",
                passed=passed,
                score=score,
                message=message,
                severity=severity,
                details={'orphan_count': orphan_count, 'total_timesheets': len(timesheet_ticket_ids), 'orphan_rate': orphan_rate}
            ))

        # Rule 3: Admin time (crm_id=0) rate
        # Use XLSX column name (not database column name)
        if 'TS-Crm ID' in timesheets_df.columns:
            crm_ids = pd.to_numeric(timesheets_df['TS-Crm ID'], errors='coerce').fillna(0).astype(int)
            admin_time_count = (crm_ids == 0).sum()
            admin_time_rate = admin_time_count / len(crm_ids)

            in_expected_range = self.config.admin_time_crm_id_min <= admin_time_rate <= self.config.admin_time_crm_id_max
            passed = in_expected_range
            score = 1.0 if in_expected_range else 0.8

            self.results.append(ValidationResult(
                rule_name="admin_time_rate",
                category="referential_integrity",
                passed=passed,
                score=score,
                message=f"Admin time (crm_id=0): {admin_time_rate*100:.1f}% (expected: {self.config.admin_time_crm_id_min*100:.0f}-{self.config.admin_time_crm_id_max*100:.0f}%)",
                severity="LOW" if in_expected_range else "MEDIUM",
                details={'admin_time_count': admin_time_count, 'total_timesheets': len(crm_ids)}
            ))

        # Rule 4: Overall referential integrity
        integrity_results = [r for r in self.results if r.category == "referential_integrity"]
        integrity_score = sum(r.score for r in integrity_results) / len(integrity_results) if integrity_results else 1.0
        passed = integrity_score >= 0.7

        self.results.append(ValidationResult(
            rule_name="overall_referential_integrity",
            category="referential_integrity",
            passed=passed,
            score=integrity_score,
            message=f"Overall referential integrity: {integrity_score*100:.1f}%",
            severity="MEDIUM" if not passed else "LOW"
        ))

    def _validate_text_integrity(self, comments_df: pd.DataFrame, tickets_df: pd.DataFrame, timesheets_df: pd.DataFrame):
        """Text integrity validation (2 rules)"""

        # Rule 1: No NULL bytes in text fields
        # Use XLSX column name (not database column name)
        if 'CT-COMMENT' in comments_df.columns:
            text_series = comments_df['CT-COMMENT'].dropna()
            null_byte_count = sum('\x00' in str(x) for x in text_series)
            clean_pct = 1.0 - (null_byte_count / len(text_series)) if len(text_series) > 0 else 1.0
            passed = clean_pct >= 0.999

            self.results.append(ValidationResult(
                rule_name="text_no_null_bytes",
                category="text_integrity",
                passed=passed,
                score=clean_pct,
                message=f"Text fields: {clean_pct*100:.3f}% free of NULL bytes ({null_byte_count} found)",
                severity="HIGH" if not passed else "LOW",
                details={'null_byte_count': null_byte_count, 'total_texts': len(text_series)}
            ))

        # Rule 2: Max consecutive newlines check
        # Use XLSX column name (not database column name)
        if 'CT-COMMENT' in comments_df.columns:
            text_series = comments_df['CT-COMMENT'].dropna()
            excessive_newlines = 0

            for text in text_series:
                # Count max consecutive newlines
                max_consecutive = 0
                current_consecutive = 0
                for char in str(text):
                    if char == '\n':
                        current_consecutive += 1
                        max_consecutive = max(max_consecutive, current_consecutive)
                    else:
                        current_consecutive = 0

                if max_consecutive >= self.config.max_consecutive_newlines:
                    excessive_newlines += 1

            clean_pct = 1.0 - (excessive_newlines / len(text_series)) if len(text_series) > 0 else 1.0
            passed = clean_pct >= 0.99

            self.results.append(ValidationResult(
                rule_name="text_excessive_newlines",
                category="text_integrity",
                passed=passed,
                score=clean_pct,
                message=f"Text fields: {clean_pct*100:.2f}% without excessive newlines ({excessive_newlines} found)",
                severity="MEDIUM" if not passed else "LOW",
                details={'excessive_newlines_count': excessive_newlines, 'threshold': self.config.max_consecutive_newlines}
            ))

    def _calculate_composite_score(self) -> float:
        """
        Calculate 0-100 composite quality score

        Weighting:
        - Schema: 15 points
        - Completeness: 30 points
        - Data types: 25 points
        - Business rules: 20 points
        - Referential integrity: 5 points
        - Text integrity: 5 points
        """
        category_weights = {
            'schema': 15,
            'completeness': 30,
            'data_types': 25,
            'business_rules': 20,
            'referential_integrity': 5,
            'text_integrity': 5
        }

        total_score = 0.0

        for category, weight in category_weights.items():
            category_results = [r for r in self.results if r.category == category]
            if category_results:
                category_avg = sum(r.score for r in category_results) / len(category_results)
                total_score += category_avg * weight

        return round(total_score, 2)

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

    def _should_proceed_with_import(self, score: float) -> bool:
        """Determine if import should proceed based on quality gate"""
        return score >= 60.0

    def _generate_summary(self, comments_df: pd.DataFrame, tickets_df: pd.DataFrame, timesheets_df: pd.DataFrame) -> Dict:
        """Generate summary statistics"""
        return {
            'total_rules': len(self.results),
            'passed_rules': sum(1 for r in self.results if r.passed),
            'failed_rules': sum(1 for r in self.results if not r.passed),
            'critical_failures': sum(1 for r in self.results if not r.passed and r.severity == 'CRITICAL'),
            'high_failures': sum(1 for r in self.results if not r.passed and r.severity == 'HIGH'),
            'record_counts': {
                'comments': len(comments_df),
                'tickets': len(tickets_df),
                'timesheets': len(timesheets_df),
                'total': len(comments_df) + len(tickets_df) + len(timesheets_df)
            }
        }

    def print_report(self, report: ValidationReport):
        """Print validation report to console"""
        print("\n" + "="*80)
        print("SERVICEDESK ETL VALIDATION REPORT")
        print("="*80)
        print(f"\nTimestamp: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Composite Score: {report.composite_score}/100")
        print(f"Quality Grade: {report.quality_grade}")
        print(f"Import Decision: {'✅ PROCEED' if report.should_proceed else '🚫 HALT'}")

        print(f"\nSummary:")
        print(f"  Total Rules: {report.summary['total_rules']}")
        print(f"  Passed: {report.summary['passed_rules']} ✅")
        print(f"  Failed: {report.summary['failed_rules']} ❌")
        print(f"  Critical Failures: {report.summary['critical_failures']} 🚨")
        print(f"  High Severity Failures: {report.summary['high_failures']} ⚠️")

        print(f"\nRecord Counts:")
        for source, count in report.summary['record_counts'].items():
            if source != 'total':
                print(f"  {source}: {count:,}")

        print(f"\nValidation Results by Category:")
        for category in ['schema', 'completeness', 'data_types', 'business_rules', 'referential_integrity', 'text_integrity']:
            category_results = [r for r in report.results if r.category == category]
            if category_results:
                passed_count = sum(1 for r in category_results if r.passed)
                avg_score = sum(r.score for r in category_results) / len(category_results)
                print(f"\n  {category.upper().replace('_', ' ')}: {passed_count}/{len(category_results)} passed ({avg_score*100:.1f}%)")

                # Show failed rules
                failed = [r for r in category_results if not r.passed]
                for r in failed:
                    print(f"    ❌ {r.rule_name}: {r.message} [{r.severity}]")

        print("\n" + "="*80)


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="ServiceDesk ETL Validator - Pre-Import Validation")
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

    # Run validation
    validator = ServiceDeskETLValidator()
    report = validator.validate_all(args.comments, args.tickets, args.timesheets)

    # Print report
    validator.print_report(report)

    # Save JSON if requested
    if args.output:
        import json
        with open(args.output, 'w') as f:
            json.dump(report.to_dict(), f, indent=2)
        print(f"\n✅ Report saved to: {args.output}")

    return 0 if report.should_proceed else 1


if __name__ == '__main__':
    exit(main())
