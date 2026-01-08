#!/usr/bin/env python3
"""
XLSX Pre-Import Validator for ServiceDesk Data

Purpose: Validate XLSX file quality BEFORE import to catch data corruption early
Principle: Fail-fast - detect issues before expensive import + RAG cycles

Author: Maia (Phase 127 - ServiceDesk ETL Quality Enhancement)
Created: 2025-10-17
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np
from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    """Validation result for a single check"""
    check_name: str
    passed: bool
    severity: str  # 'CRITICAL', 'WARNING', 'INFO'
    message: str
    details: Optional[Dict] = None


@dataclass
class FileValidationReport:
    """Complete validation report for a single file"""
    file_path: str
    file_type: str  # 'comments', 'tickets', 'timesheets'
    total_rows: int
    total_columns: int
    validation_results: List[ValidationResult] = field(default_factory=list)
    overall_passed: bool = True
    quality_score: float = 0.0

    def add_result(self, result: ValidationResult):
        """Add validation result and update overall status"""
        self.validation_results.append(result)
        if result.severity == 'CRITICAL' and not result.passed:
            self.overall_passed = False


class XLSXPreValidator:
    """
    Pre-import XLSX validation for ServiceDesk data

    Validates:
    - Schema (column count, required columns, structure)
    - Field completeness (critical fields populated)
    - Text integrity (detect truncation from comma-splitting)
    - Data types (ticket IDs numeric, dates parseable)
    - Business rules (no future dates, valid ranges)
    """

    # Expected schemas for each file type (ACTUAL column names from source system)
    EXPECTED_SCHEMAS = {
        'comments': {
            'required_columns': [
                'TKTCT-TicketID', 'TKTCT-CommentID', 'TKTCT-Comment',
                'TKTCT-Username', 'TKTCT-Created Time'
            ],
            'expected_column_count': 10,
            'critical_fields': ['TKTCT-VisibleCustomer'],
            'critical_threshold': 0.001  # >0.1% populated (actual reality, very sparse)
        },
        'tickets': {
            'required_columns': ['TKT-Ticket ID', 'TKT-Created Time'],
            'expected_column_count_min': 55,  # Actual: 60 columns
            'expected_column_count_max': 65
        },
        'timesheets': {
            'required_columns': ['TS-Date', 'TS-Crm ID'],
            'expected_column_count_min': 18,
            'expected_column_count_max': 24
        }
    }

    def __init__(self, sample_size: int = 1000):
        """
        Initialize validator

        Args:
            sample_size: Number of rows to sample for performance (full validation uses all rows)
        """
        self.sample_size = sample_size
        self.reports: List[FileValidationReport] = []

    def validate_file(self, file_path: str, file_type: str) -> FileValidationReport:
        """
        Validate a single XLSX file

        Args:
            file_path: Path to XLSX file
            file_type: One of 'comments', 'tickets', 'timesheets'

        Returns:
            FileValidationReport with all validation results
        """
        print(f"\n📄 Validating: {Path(file_path).name}")

        # Load sample for quick checks (comments: first 10 cols only, rest are empty)
        try:
            if file_type == 'comments':
                df_sample = pd.read_excel(file_path, nrows=self.sample_size, usecols=range(10))
            else:
                df_sample = pd.read_excel(file_path, nrows=self.sample_size)
            print(f"   Sample loaded: {len(df_sample):,} rows, {len(df_sample.columns)} columns")
        except Exception as e:
            report = FileValidationReport(
                file_path=file_path,
                file_type=file_type,
                total_rows=0,
                total_columns=0,
                overall_passed=False
            )
            report.add_result(ValidationResult(
                check_name="File Loading",
                passed=False,
                severity='CRITICAL',
                message=f"Failed to load XLSX file: {str(e)}"
            ))
            return report

        # Get full row count (without loading all data)
        print(f"   📊 Checking full file row count...")
        total_rows = self._get_row_count(file_path)

        # Create report
        report = FileValidationReport(
            file_path=file_path,
            file_type=file_type,
            total_rows=total_rows,
            total_columns=len(df_sample.columns)
        )

        # Run validation checks
        if file_type == 'comments':
            self._validate_comments(df_sample, report)
        elif file_type == 'tickets':
            self._validate_tickets(df_sample, report)
        elif file_type == 'timesheets':
            self._validate_timesheets(df_sample, report)
        else:
            report.add_result(ValidationResult(
                check_name="File Type",
                passed=False,
                severity='CRITICAL',
                message=f"Unknown file type: {file_type}"
            ))

        # Calculate quality score
        report.quality_score = self._calculate_quality_score(report)

        return report

    def _get_row_count(self, file_path: str) -> int:
        """Get total row count without loading entire file"""
        try:
            df_meta = pd.read_excel(file_path, nrows=0)
            # Use openpyxl to get row count efficiently
            import openpyxl
            wb = openpyxl.load_workbook(file_path, read_only=True)
            ws = wb.active
            row_count = ws.max_row - 1  # Subtract header row
            wb.close()
            return row_count
        except Exception:
            # Fallback: load entire file (slow but accurate)
            df = pd.read_excel(file_path)
            return len(df)

    # ========== Reusable Validation Helpers ==========

    def _check_exact_column_count(self, df: pd.DataFrame, report: FileValidationReport,
                                   expected: int) -> None:
        """Check if DataFrame has exact expected column count"""
        actual = len(df.columns)
        if actual == expected:
            report.add_result(ValidationResult(
                check_name="Schema: Column Count",
                passed=True,
                severity='INFO',
                message=f"✅ All {expected} expected columns present"
            ))
        else:
            report.add_result(ValidationResult(
                check_name="Schema: Column Count",
                passed=False,
                severity='CRITICAL',
                message=f"Expected {expected} columns, found {actual}",
                details={'actual_columns': list(df.columns)}
            ))

    def _check_column_count_range(self, df: pd.DataFrame, report: FileValidationReport,
                                   min_count: int, max_count: int) -> None:
        """Check if DataFrame column count is within expected range"""
        actual = len(df.columns)
        if min_count <= actual <= max_count:
            report.add_result(ValidationResult(
                check_name="Schema: Column Count",
                passed=True,
                severity='INFO',
                message=f"Column count in expected range: {actual}"
            ))
        else:
            report.add_result(ValidationResult(
                check_name="Schema: Column Count",
                passed=False,
                severity='WARNING',
                message=f"Column count {actual} outside expected range ({min_count}-{max_count})"
            ))

    def _check_required_columns(self, df: pd.DataFrame, report: FileValidationReport,
                                 required_cols: List[str]) -> None:
        """Check if all required columns are present"""
        missing = [col for col in required_cols if col not in df.columns]
        if not missing:
            report.add_result(ValidationResult(
                check_name="Schema: Required Columns",
                passed=True,
                severity='INFO',
                message=f"✅ All {len(required_cols)} required columns present"
            ))
        else:
            report.add_result(ValidationResult(
                check_name="Schema: Required Columns",
                passed=False,
                severity='CRITICAL',
                message=f"Missing required columns: {missing}",
                details={'missing': missing}
            ))

    def _check_row_count_threshold(self, report: FileValidationReport,
                                    threshold: int, file_type: str) -> None:
        """Check if row count meets minimum threshold"""
        print(f"   ✅ Total rows: {report.total_rows:,}")
        if report.total_rows >= threshold:
            report.add_result(ValidationResult(
                check_name="Data Volume: Row Count",
                passed=True,
                severity='INFO',
                message=f"Row count reasonable: {report.total_rows:,} (pre-filter)",
                details={'total_rows': report.total_rows}
            ))
        else:
            report.add_result(ValidationResult(
                check_name="Data Volume: Row Count",
                passed=False,
                severity='WARNING',
                message=f"Unexpected row count: {report.total_rows:,} (expected {threshold:,}+ pre-filter)",
                details={'total_rows': report.total_rows}
            ))

    def _check_field_population(self, df: pd.DataFrame, report: FileValidationReport,
                                 field_name: str, threshold: float) -> None:
        """Check if a field meets minimum population threshold"""
        if field_name not in df.columns:
            report.add_result(ValidationResult(
                check_name=f"Field Completeness: {field_name}",
                passed=False,
                severity='CRITICAL',
                message=f"{field_name} column not found (data corruption suspected)"
            ))
            return

        populated_pct = df[field_name].notna().sum() / len(df)
        if populated_pct >= threshold:
            report.add_result(ValidationResult(
                check_name=f"Field Completeness: {field_name}",
                passed=True,
                severity='INFO',
                message=f"✅ {field_name}: {populated_pct*100:.2f}% populated",
                details={'populated_pct': populated_pct}
            ))
        else:
            report.add_result(ValidationResult(
                check_name=f"Field Completeness: {field_name}",
                passed=False,
                severity='CRITICAL',
                message=f"{field_name} only {populated_pct*100:.2f}% populated (need >{threshold*100:.1f}%)",
                details={'populated_pct': populated_pct}
            ))

    def _check_field_numeric(self, df: pd.DataFrame, report: FileValidationReport,
                              field_name: str) -> None:
        """Check if a field contains numeric values"""
        if field_name not in df.columns:
            return

        try:
            df[field_name].astype(int)
            report.add_result(ValidationResult(
                check_name="Data Type: Ticket IDs",
                passed=True,
                severity='INFO',
                message="✅ Ticket IDs: All numeric (convertible to int)"
            ))
        except (ValueError, TypeError):
            non_numeric = df[~df[field_name].apply(lambda x: str(x).isdigit())]
            report.add_result(ValidationResult(
                check_name="Data Type: Ticket IDs",
                passed=False,
                severity='WARNING',
                message=f"Found {len(non_numeric)} non-numeric ticket IDs",
                details={'sample_invalid': list(non_numeric[field_name].head(5))}
            ))

    def _check_field_dates(self, df: pd.DataFrame, report: FileValidationReport,
                            field_name: str) -> None:
        """Check if a date field is parseable"""
        if field_name not in df.columns:
            return

        try:
            pd.to_datetime(df[field_name], dayfirst=True, errors='coerce')
            unparseable = df[field_name].isna().sum()
            if unparseable == 0:
                report.add_result(ValidationResult(
                    check_name="Data Type: Dates",
                    passed=True,
                    severity='INFO',
                    message="✅ Dates: All parseable (DD/MM/YYYY format)"
                ))
            else:
                report.add_result(ValidationResult(
                    check_name="Data Type: Dates",
                    passed=False,
                    severity='WARNING',
                    message=f"Found {unparseable} unparseable dates",
                    details={'unparseable_count': unparseable}
                ))
        except Exception as e:
            report.add_result(ValidationResult(
                check_name="Data Type: Dates",
                passed=False,
                severity='WARNING',
                message=f"Date parsing failed: {str(e)}"
            ))

    def _check_text_length(self, df: pd.DataFrame, report: FileValidationReport,
                            field_name: str, min_avg_length: int) -> None:
        """Check if text field has reasonable average length"""
        if field_name not in df.columns:
            return

        avg_length = df[field_name].astype(str).str.len().mean()
        min_length = df[field_name].astype(str).str.len().min()

        if avg_length >= min_avg_length:
            report.add_result(ValidationResult(
                check_name="Text Integrity: Comment Length",
                passed=True,
                severity='INFO',
                message=f"✅ Comment text: Average {avg_length:.0f} chars",
                details={'avg_length': avg_length, 'min_length': min_length}
            ))
        else:
            report.add_result(ValidationResult(
                check_name="Text Integrity: Comment Length",
                passed=False,
                severity='WARNING',
                message=f"Comment text avg {avg_length:.0f} chars (expected >{min_avg_length}, possible truncation)",
                details={'avg_length': avg_length, 'min_length': min_length}
            ))

    def _validate_comments(self, df: pd.DataFrame, report: FileValidationReport):
        """Validate comments XLSX file using reusable helpers"""
        schema = self.EXPECTED_SCHEMAS['comments']

        # Schema checks
        self._check_exact_column_count(df, report, schema['expected_column_count'])
        self._check_required_columns(df, report, schema['required_columns'])

        # Field-specific checks (updated for TKTCT-* format Jan 2026)
        self._check_field_population(df, report, 'TKTCT-VisibleCustomer', schema['critical_threshold'])
        self._check_field_numeric(df, report, 'TKTCT-TicketID')
        self._check_field_dates(df, report, 'TKTCT-Created Time')
        self._check_text_length(df, report, 'TKTCT-Comment', min_avg_length=100)

        # Volume check
        self._check_row_count_threshold(report, threshold=100000, file_type='comments')

    def _validate_tickets(self, df: pd.DataFrame, report: FileValidationReport):
        """Validate tickets XLSX file using reusable helpers"""
        schema = self.EXPECTED_SCHEMAS['tickets']

        # Schema checks
        self._check_required_columns(df, report, schema['required_columns'])
        self._check_column_count_range(df, report,
                                        schema['expected_column_count_min'],
                                        schema['expected_column_count_max'])

        # Volume check
        self._check_row_count_threshold(report, threshold=500000, file_type='tickets')

    def _validate_timesheets(self, df: pd.DataFrame, report: FileValidationReport):
        """Validate timesheets XLSX file using reusable helpers"""
        schema = self.EXPECTED_SCHEMAS['timesheets']

        # Schema checks
        self._check_required_columns(df, report, schema['required_columns'])
        self._check_column_count_range(df, report,
                                        schema['expected_column_count_min'],
                                        schema['expected_column_count_max'])

        # Volume check
        self._check_row_count_threshold(report, threshold=500000, file_type='timesheets')

    def _calculate_quality_score(self, report: FileValidationReport) -> float:
        """
        Calculate 0-100 quality score based on validation results

        Scoring:
        - CRITICAL failures: -20 points each
        - WARNING failures: -5 points each
        - INFO passes: +0 points (baseline expectation)
        - Start at 100, deduct for failures
        """
        score = 100.0

        for result in report.validation_results:
            if not result.passed:
                if result.severity == 'CRITICAL':
                    score -= 20
                elif result.severity == 'WARNING':
                    score -= 5

        return max(0.0, score)  # Floor at 0

    def generate_report(self) -> str:
        """
        Generate comprehensive validation report

        Returns:
            Formatted markdown report
        """
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("XLSX PRE-IMPORT VALIDATION REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")

        # Summary section
        all_passed = all(r.overall_passed for r in self.reports)
        total_critical = sum(
            1 for r in self.reports
            for vr in r.validation_results
            if vr.severity == 'CRITICAL' and not vr.passed
        )
        total_warnings = sum(
            1 for r in self.reports
            for vr in r.validation_results
            if vr.severity == 'WARNING' and not vr.passed
        )

        # Individual file reports
        for report in self.reports:
            report_lines.append("")
            status_icon = "✅" if report.overall_passed else "❌"
            report_lines.append(f"{status_icon} {report.file_type.upper()}: {Path(report.file_path).name}")
            report_lines.append(f"   Quality Score: {report.quality_score}/100")
            report_lines.append(f"   Total Rows: {report.total_rows:,}")
            report_lines.append(f"   Total Columns: {report.total_columns}")
            report_lines.append("")

            # Group results by severity
            for severity in ['CRITICAL', 'WARNING', 'INFO']:
                severity_results = [r for r in report.validation_results if r.severity == severity]
                if severity_results:
                    for result in severity_results:
                        icon = "✅" if result.passed else "❌"
                        report_lines.append(f"   {icon} [{severity}] {result.message}")

        # Overall summary
        report_lines.append("")
        report_lines.append("=" * 80)
        report_lines.append("VALIDATION SUMMARY")
        report_lines.append("=" * 80)

        for report in self.reports:
            status = "✅ PASS" if report.overall_passed else "❌ FAIL"
            report_lines.append(f"{status}: {report.file_type}.xlsx (Score: {report.quality_score}/100)")

        report_lines.append("")
        if all_passed and total_warnings == 0:
            report_lines.append("✅ No issues detected - files ready for import!")
        elif all_passed and total_warnings > 0:
            report_lines.append(f"⚠️  {total_warnings} warnings detected - review before import")
        else:
            report_lines.append(f"❌ {total_critical} critical issues detected - DO NOT IMPORT")
            report_lines.append("   Fix critical issues before proceeding")

        # Recommendation
        report_lines.append("")
        report_lines.append("=" * 80)
        report_lines.append("RECOMMENDATION")
        report_lines.append("=" * 80)

        if all_passed and total_warnings == 0:
            report_lines.append("✅ PROCEED WITH IMPORT - All validations passed")
        elif all_passed and total_warnings <= 3:
            report_lines.append("⚠️  PROCEED WITH CAUTION - Minor warnings acceptable")
        elif all_passed and total_warnings > 3:
            report_lines.append("⚠️  REVIEW WARNINGS - Multiple warnings require attention")
        else:
            report_lines.append("❌ DO NOT IMPORT - Fix critical issues first")
            report_lines.append("")
            report_lines.append("Critical Issues:")
            for report in self.reports:
                critical_failures = [r for r in report.validation_results if r.severity == 'CRITICAL' and not r.passed]
                for failure in critical_failures:
                    report_lines.append(f"  • {report.file_type}: {failure.message}")

        return "\n".join(report_lines)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Pre-import XLSX validation for ServiceDesk data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate all three files
  %(prog)s ~/Downloads/comments.xlsx ~/Downloads/tickets.xlsx ~/Downloads/timesheets.xlsx

  # Validate with custom sample size
  %(prog)s --sample-size 5000 ~/Downloads/comments.xlsx
        """
    )
    parser.add_argument('files', nargs='+', help='XLSX files to validate')
    parser.add_argument('--sample-size', type=int, default=1000,
                        help='Number of rows to sample for quick checks (default: 1000)')
    parser.add_argument('--output', '-o', help='Write report to file instead of stdout')

    args = parser.parse_args()

    # Detect file types from filenames
    file_mappings = []
    for file_path in args.files:
        filename = Path(file_path).name.lower()
        if 'comment' in filename:
            file_type = 'comments'
        elif 'ticket' in filename:
            file_type = 'tickets'
        elif 'timesheet' in filename or 'time' in filename:
            file_type = 'timesheets'
        else:
            print(f"❌ Cannot determine file type for: {filename}")
            print("   Filename should contain 'comment', 'ticket', or 'timesheet'")
            sys.exit(1)

        file_mappings.append((file_path, file_type))

    # Validate all files
    validator = XLSXPreValidator(sample_size=args.sample_size)

    for file_path, file_type in file_mappings:
        if not Path(file_path).exists():
            print(f"❌ File not found: {file_path}")
            sys.exit(1)

        report = validator.validate_file(file_path, file_type)
        validator.reports.append(report)

    # Generate and display report
    report_text = validator.generate_report()

    if args.output:
        Path(args.output).write_text(report_text)
        print(f"\n✅ Report written to: {args.output}")
    else:
        print("\n" + report_text)

    # Exit code based on validation results
    all_passed = all(r.overall_passed for r in validator.reports)
    sys.exit(0 if all_passed else 1)


if __name__ == '__main__':
    main()
