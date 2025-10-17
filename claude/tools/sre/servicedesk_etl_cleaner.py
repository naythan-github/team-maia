#!/usr/bin/env python3
"""
ServiceDesk ETL Cleaner - Data Cleaning with Full Audit Trail

Performs 5 cleaning operations:
1. Date standardization (ISO 8601, dayfirst=True)
2. Type normalization (int/float/bool conversion)
3. Missing value imputation (reject/default/keep_null strategies)
4. Text field cleaning (whitespace, newlines, null bytes)
5. Business defaults (conservative values)

All transformations are logged for complete audit trail.

Author: Maia
Created: 2025-10-17
Phase: 127 Day 4 - ServiceDesk ETL Quality Enhancement
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import re


@dataclass
class CleaningConfig:
    """Configuration for cleaning operations"""
    # Date parsing
    dayfirst: bool = True  # Australian DD/MM/YYYY format
    date_format: str = '%Y-%m-%d %H:%M:%S'  # ISO 8601 output

    # Missing value strategies (XLSX column names)
    reject_null_fields: List[str] = field(default_factory=lambda: [
        'CT-COMMENT-ID', 'CT-TKT-ID', 'CT-DATEAMDTIME', 'CT-COMMENT',
        'TS-Title', 'TS-Hours', 'TS-Date'
    ])

    # Conservative defaults (XLSX column names)
    defaults: Dict[str, Any] = field(default_factory=lambda: {
        'CT-USERIDNAME': 'UNKNOWN',
        'is_public': False,  # No XLSX column for this
        'TKT-Assigned To User': 'Unassigned',
        'TS-Billable': False,
        'TS-Approved': False
    })

    # Text cleaning
    max_consecutive_newlines: int = 3
    max_text_length: int = 100000


@dataclass
class TransformationRecord:
    """Record of a single transformation operation"""
    timestamp: datetime
    entity_type: str  # 'comments', 'tickets', 'timesheets'
    column: str
    operation: str  # 'date_standardization', 'type_conversion', etc.
    records_changed: int
    sample_before: Optional[str] = None
    sample_after: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class CleaningReport:
    """Complete cleaning report with audit trail"""
    timestamp: datetime
    transformations: List[TransformationRecord]
    summary: Dict[str, Any]

    def to_dict(self) -> Dict:
        """Convert report to dictionary"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'total_transformations': len(self.transformations),
            'summary': self.summary,
            'transformations': [
                {
                    'timestamp': t.timestamp.isoformat(),
                    'entity_type': t.entity_type,
                    'column': t.column,
                    'operation': t.operation,
                    'records_changed': t.records_changed,
                    'sample_before': t.sample_before,
                    'sample_after': t.sample_after,
                    'notes': t.notes
                }
                for t in self.transformations
            ]
        }


class AuditLogger:
    """Audit trail logger for all transformations"""

    def __init__(self):
        self.records: List[TransformationRecord] = []

    def log(
        self,
        entity_type: str,
        column: str,
        operation: str,
        records_changed: int,
        sample_before: Optional[Any] = None,
        sample_after: Optional[Any] = None,
        notes: Optional[str] = None
    ):
        """Log a transformation"""
        record = TransformationRecord(
            timestamp=datetime.now(),
            entity_type=entity_type,
            column=column,
            operation=operation,
            records_changed=records_changed,
            sample_before=str(sample_before) if sample_before is not None else None,
            sample_after=str(sample_after) if sample_after is not None else None,
            notes=notes
        )
        self.records.append(record)

    def get_records(self) -> List[TransformationRecord]:
        """Get all transformation records"""
        return self.records

    def to_dataframe(self) -> pd.DataFrame:
        """Convert audit trail to DataFrame"""
        return pd.DataFrame([
            {
                'timestamp': r.timestamp,
                'entity_type': r.entity_type,
                'column': r.column,
                'operation': r.operation,
                'records_changed': r.records_changed,
                'sample_before': r.sample_before,
                'sample_after': r.sample_after,
                'notes': r.notes
            }
            for r in self.records
        ])


class ServiceDeskETLCleaner:
    """
    Data cleaning with full audit trail

    Implements 5 cleaning operations with comprehensive transformation logging
    """

    def __init__(self, config: Optional[CleaningConfig] = None):
        """Initialize cleaner with optional custom configuration"""
        self.config = config or CleaningConfig()
        self.audit_logger = AuditLogger()

    def clean_all(
        self,
        comments_df: pd.DataFrame,
        tickets_df: pd.DataFrame,
        timesheets_df: pd.DataFrame
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, CleaningReport]:
        """
        Execute all cleaning operations and generate comprehensive report

        Args:
            comments_df: Comments DataFrame
            tickets_df: Tickets DataFrame
            timesheets_df: Timesheets DataFrame

        Returns:
            Tuple of (cleaned_comments, cleaned_tickets, cleaned_timesheets, report)
        """
        print("Starting data cleaning with full audit trail...")

        # Make copies to avoid modifying originals
        comments_clean = comments_df.copy()
        tickets_clean = tickets_df.copy()
        timesheets_clean = timesheets_df.copy()

        # Operation 1: Date Standardization
        print("\n1. Date Standardization (ISO 8601)...")
        comments_clean = self._standardize_dates(comments_clean, 'comments')
        tickets_clean = self._standardize_dates(tickets_clean, 'tickets')
        timesheets_clean = self._standardize_dates(timesheets_clean, 'timesheets')

        # Operation 2: Type Normalization
        print("2. Type Normalization (int/float/bool)...")
        comments_clean = self._normalize_types(comments_clean, 'comments')
        tickets_clean = self._normalize_types(tickets_clean, 'tickets')
        timesheets_clean = self._normalize_types(timesheets_clean, 'timesheets')

        # Operation 3: Text Field Cleaning
        print("3. Text Field Cleaning (whitespace, newlines, null bytes)...")
        comments_clean = self._clean_text_fields(comments_clean, 'comments')
        tickets_clean = self._clean_text_fields(tickets_clean, 'tickets')
        timesheets_clean = self._clean_text_fields(timesheets_clean, 'timesheets')

        # Operation 4: Missing Value Imputation
        print("4. Missing Value Imputation (reject/default/keep_null)...")
        comments_clean = self._impute_missing_values(comments_clean, 'comments')
        tickets_clean = self._impute_missing_values(tickets_clean, 'tickets')
        timesheets_clean = self._impute_missing_values(timesheets_clean, 'timesheets')

        # Operation 5: Business Defaults
        print("5. Business Defaults (conservative values)...")
        comments_clean = self._apply_business_defaults(comments_clean, 'comments')
        tickets_clean = self._apply_business_defaults(tickets_clean, 'tickets')
        timesheets_clean = self._apply_business_defaults(timesheets_clean, 'timesheets')

        # Generate report
        summary = self._generate_summary(
            comments_df, tickets_df, timesheets_df,
            comments_clean, tickets_clean, timesheets_clean
        )

        report = CleaningReport(
            timestamp=datetime.now(),
            transformations=self.audit_logger.get_records(),
            summary=summary
        )

        print(f"\n✅ Cleaning complete: {len(self.audit_logger.get_records())} transformations applied")

        return comments_clean, tickets_clean, timesheets_clean, report

    def _standardize_dates(self, df: pd.DataFrame, entity_type: str) -> pd.DataFrame:
        """Operation 1: Date standardization to ISO 8601"""
        date_columns = [col for col in df.columns if 'time' in col.lower() or col.lower() == 'date']

        for col in date_columns:
            if col in df.columns:
                # Get sample before
                non_null_mask = df[col].notna()
                sample_before = df.loc[non_null_mask, col].iloc[0] if non_null_mask.any() else None

                # Parse dates with dayfirst=True (Australian format)
                original_series = df[col].copy()
                df[col] = pd.to_datetime(df[col], errors='coerce', dayfirst=self.config.dayfirst)

                # Count changes
                changes = (original_series.notna() & df[col].notna()).sum()

                # Get sample after
                sample_after = df.loc[non_null_mask, col].iloc[0] if non_null_mask.any() else None

                # Log transformation
                if changes > 0:
                    self.audit_logger.log(
                        entity_type=entity_type,
                        column=col,
                        operation='date_standardization',
                        records_changed=changes,
                        sample_before=sample_before,
                        sample_after=sample_after,
                        notes=f"Parsed with dayfirst={self.config.dayfirst}, converted to ISO 8601"
                    )

        return df

    def _normalize_types(self, df: pd.DataFrame, entity_type: str) -> pd.DataFrame:
        """Operation 2: Type normalization (int/float/bool)"""

        # Integer conversions (XLSX column names)
        int_columns = {
            'comments': ['CT-COMMENT-ID', 'CT-TKT-ID'],
            'tickets': ['TKT-Ticket ID'],
            'timesheets': ['TS-Title', 'TS-Crm ID']
        }

        if entity_type in int_columns:
            for col in int_columns[entity_type]:
                if col in df.columns:
                    sample_before = df[col].iloc[0] if len(df) > 0 else None
                    original_series = df[col].copy()

                    # Convert to numeric, round, then to int64
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    valid_mask = df[col].notna()
                    if valid_mask.any():
                        # Round floats to integers before conversion
                        df.loc[valid_mask, col] = df.loc[valid_mask, col].round().astype('Int64')

                    changes = (original_series.notna() & df[col].notna()).sum()
                    sample_after = df[col].iloc[0] if len(df) > 0 else None

                    if changes > 0:
                        self.audit_logger.log(
                            entity_type=entity_type,
                            column=col,
                            operation='type_normalization_int',
                            records_changed=changes,
                            sample_before=sample_before,
                            sample_after=sample_after,
                            notes="Converted to Int64 (nullable integer)"
                        )

        # Float conversions (XLSX column names)
        if entity_type == 'timesheets' and 'TS-Hours' in df.columns:
            sample_before = df['TS-Hours'].iloc[0] if len(df) > 0 else None
            original_series = df['TS-Hours'].copy()

            df['TS-Hours'] = pd.to_numeric(df['TS-Hours'], errors='coerce')

            changes = (original_series.notna() & df['TS-Hours'].notna()).sum()
            sample_after = df['TS-Hours'].iloc[0] if len(df) > 0 else None

            if changes > 0:
                self.audit_logger.log(
                    entity_type=entity_type,
                    column='TS-Hours',
                    operation='type_normalization_float',
                    records_changed=changes,
                    sample_before=sample_before,
                    sample_after=sample_after,
                    notes="Converted to float64"
                )

        # Boolean conversions (XLSX column names)
        bool_columns = {
            'comments': ['CT-VISIBLE-CUSTOMER'],
            'timesheets': ['TS-Billable', 'TS-Approved']
        }

        if entity_type in bool_columns:
            for col in bool_columns[entity_type]:
                if col in df.columns:
                    sample_before = df[col].iloc[0] if len(df) > 0 else None
                    original_series = df[col].copy()

                    # Map string values to boolean
                    df[col] = df[col].map({
                        'true': True, 'True': True, 'TRUE': True, True: True, 1: True, '1': True,
                        'false': False, 'False': False, 'FALSE': False, False: False, 0: False, '0': False
                    })

                    changes = (original_series.notna() & df[col].notna()).sum()
                    sample_after = df[col].iloc[0] if len(df) > 0 else None

                    if changes > 0:
                        self.audit_logger.log(
                            entity_type=entity_type,
                            column=col,
                            operation='type_normalization_bool',
                            records_changed=changes,
                            sample_before=sample_before,
                            sample_after=sample_after,
                            notes="Mapped string values to boolean"
                        )

        return df

    def _clean_text_fields(self, df: pd.DataFrame, entity_type: str) -> pd.DataFrame:
        """Operation 3: Text field cleaning (XLSX column names)"""
        text_columns = {
            'comments': ['CT-COMMENT', 'CT-USERIDNAME'],
            'tickets': ['TKT-Title', 'TKT-Assigned To User'],
            'timesheets': ['TS-Description', 'TS-User Username']
        }

        if entity_type in text_columns:
            for col in text_columns[entity_type]:
                if col in df.columns:
                    sample_before = df[col].iloc[0] if len(df) > 0 and df[col].notna().any() else None
                    original_series = df[col].copy()
                    changes_made = 0

                    # Apply cleaning operations
                    text_mask = df[col].notna()
                    if text_mask.any():
                        # Strip whitespace
                        df.loc[text_mask, col] = df.loc[text_mask, col].str.strip()

                        # Normalize line endings (CRLF → LF)
                        df.loc[text_mask, col] = df.loc[text_mask, col].str.replace('\r\n', '\n', regex=False)
                        df.loc[text_mask, col] = df.loc[text_mask, col].str.replace('\r', '\n', regex=False)

                        # Remove NULL bytes
                        df.loc[text_mask, col] = df.loc[text_mask, col].str.replace('\x00', '', regex=False)

                        # Collapse excessive newlines
                        pattern = '\n{' + str(self.config.max_consecutive_newlines + 1) + ',}'
                        replacement = '\n' * self.config.max_consecutive_newlines
                        df.loc[text_mask, col] = df.loc[text_mask, col].str.replace(pattern, replacement, regex=True)

                        # Count changes
                        changes_made = (original_series != df[col]).sum()

                    sample_after = df[col].iloc[0] if len(df) > 0 and df[col].notna().any() else None

                    if changes_made > 0:
                        self.audit_logger.log(
                            entity_type=entity_type,
                            column=col,
                            operation='text_cleaning',
                            records_changed=changes_made,
                            sample_before=sample_before,
                            sample_after=sample_after,
                            notes="Stripped whitespace, normalized line endings, removed NULL bytes, collapsed excessive newlines"
                        )

        return df

    def _impute_missing_values(self, df: pd.DataFrame, entity_type: str) -> pd.DataFrame:
        """Operation 4: Missing value imputation"""

        # Check for critical NULLs (reject strategy)
        for col in self.config.reject_null_fields:
            if col in df.columns:
                null_count = df[col].isna().sum()
                if null_count > 0:
                    # For critical fields, log but don't reject (allow validator to handle)
                    self.audit_logger.log(
                        entity_type=entity_type,
                        column=col,
                        operation='missing_value_check',
                        records_changed=0,
                        notes=f"CRITICAL: {null_count} NULL values in required field (validation should catch this)"
                    )

        # Apply defaults where configured
        for col, default_value in self.config.defaults.items():
            if col in df.columns:
                null_mask = df[col].isna()
                null_count = null_mask.sum()

                if null_count > 0:
                    df.loc[null_mask, col] = default_value

                    self.audit_logger.log(
                        entity_type=entity_type,
                        column=col,
                        operation='missing_value_imputation',
                        records_changed=null_count,
                        sample_before='NULL',
                        sample_after=str(default_value),
                        notes=f"Filled {null_count} NULL values with default: {default_value}"
                    )

        # Special case: TS-Crm ID NULL → 0 (admin time) (XLSX column name)
        if entity_type == 'timesheets' and 'TS-Crm ID' in df.columns:
            null_mask = df['TS-Crm ID'].isna()
            null_count = null_mask.sum()

            if null_count > 0:
                df.loc[null_mask, 'TS-Crm ID'] = 0

                self.audit_logger.log(
                    entity_type=entity_type,
                    column='TS-Crm ID',
                    operation='missing_value_imputation',
                    records_changed=null_count,
                    sample_before='NULL',
                    sample_after='0',
                    notes="Admin time (no ticket reference)"
                )

        return df

    def _apply_business_defaults(self, df: pd.DataFrame, entity_type: str) -> pd.DataFrame:
        """Operation 5: Business defaults (conservative values)"""

        # Conservative defaults for ambiguous values
        business_rules = {
            'comments': {
                'is_public': (lambda x: x is None, False, "Conservative: assume private"),
            },
            'timesheets': {
                'billable': (lambda x: x is None, False, "Conservative: assume non-billable"),
                'approved': (lambda x: x is None, False, "Conservative: assume not approved"),
            }
        }

        if entity_type in business_rules:
            for col, (condition_func, default_value, rationale) in business_rules[entity_type].items():
                if col in df.columns:
                    # Find rows matching condition
                    mask = df[col].apply(condition_func)
                    changes = mask.sum()

                    if changes > 0:
                        df.loc[mask, col] = default_value

                        self.audit_logger.log(
                            entity_type=entity_type,
                            column=col,
                            operation='business_default',
                            records_changed=changes,
                            sample_before='NULL/ambiguous',
                            sample_after=str(default_value),
                            notes=rationale
                        )

        return df

    def _generate_summary(
        self,
        comments_orig: pd.DataFrame, tickets_orig: pd.DataFrame, timesheets_orig: pd.DataFrame,
        comments_clean: pd.DataFrame, tickets_clean: pd.DataFrame, timesheets_clean: pd.DataFrame
    ) -> Dict:
        """Generate summary statistics"""
        return {
            'total_transformations': len(self.audit_logger.get_records()),
            'transformations_by_operation': {
                op: sum(1 for r in self.audit_logger.get_records() if r.operation == op)
                for op in set(r.operation for r in self.audit_logger.get_records())
            },
            'transformations_by_entity': {
                entity: sum(1 for r in self.audit_logger.get_records() if r.entity_type == entity)
                for entity in ['comments', 'tickets', 'timesheets']
            },
            'total_records_affected': sum(r.records_changed for r in self.audit_logger.get_records()),
            'record_counts': {
                'comments': {'original': len(comments_orig), 'cleaned': len(comments_clean)},
                'tickets': {'original': len(tickets_orig), 'cleaned': len(tickets_clean)},
                'timesheets': {'original': len(timesheets_orig), 'cleaned': len(timesheets_clean)}
            }
        }

    def get_audit_trail(self) -> pd.DataFrame:
        """Export audit trail as DataFrame"""
        return self.audit_logger.to_dataframe()

    def print_report(self, report: CleaningReport):
        """Print cleaning report to console"""
        print("\n" + "="*80)
        print("SERVICEDESK ETL CLEANING REPORT")
        print("="*80)
        print(f"\nTimestamp: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total Transformations: {report.summary['total_transformations']}")
        print(f"Total Records Affected: {report.summary['total_records_affected']:,}")

        print(f"\nTransformations by Operation:")
        for op, count in report.summary['transformations_by_operation'].items():
            print(f"  {op}: {count}")

        print(f"\nTransformations by Entity:")
        for entity, count in report.summary['transformations_by_entity'].items():
            print(f"  {entity}: {count}")

        print(f"\nRecord Counts:")
        for entity, counts in report.summary['record_counts'].items():
            print(f"  {entity}: {counts['original']:,} → {counts['cleaned']:,}")

        print(f"\nSample Transformations (first 5):")
        for i, t in enumerate(report.transformations[:5], 1):
            print(f"\n  {i}. {t.entity_type}.{t.column} - {t.operation}")
            print(f"     Records changed: {t.records_changed:,}")
            if t.sample_before:
                print(f"     Before: {t.sample_before[:100]}...")
            if t.sample_after:
                print(f"     After: {t.sample_after[:100]}...")
            if t.notes:
                print(f"     Notes: {t.notes}")

        print("\n" + "="*80)


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="ServiceDesk ETL Cleaner - Data Cleaning with Audit Trail")
    parser.add_argument('comments', type=Path, help="Path to comments.xlsx")
    parser.add_argument('tickets', type=Path, help="Path to tickets.xlsx")
    parser.add_argument('timesheets', type=Path, help="Path to timesheets.xlsx")
    parser.add_argument('--output-dir', type=Path, help="Output directory for cleaned files")
    parser.add_argument('--audit-trail', type=Path, help="Output path for audit trail CSV")

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

    # Run cleaning
    cleaner = ServiceDeskETLCleaner()
    comments_clean, tickets_clean, timesheets_clean, report = cleaner.clean_all(
        comments_df, tickets_df, timesheets_df
    )

    # Print report
    cleaner.print_report(report)

    # Save cleaned files if requested
    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        comments_clean.to_excel(args.output_dir / 'comments_cleaned.xlsx', index=False)
        tickets_clean.to_excel(args.output_dir / 'tickets_cleaned.xlsx', index=False)
        timesheets_clean.to_excel(args.output_dir / 'timesheets_cleaned.xlsx', index=False)
        print(f"\n✅ Cleaned files saved to: {args.output_dir}")

    # Save audit trail if requested
    if args.audit_trail:
        audit_df = cleaner.get_audit_trail()
        audit_df.to_csv(args.audit_trail, index=False)
        print(f"✅ Audit trail saved to: {args.audit_trail}")

    return 0


if __name__ == '__main__':
    exit(main())
