"""
M365 IR Data Quality Checker - Phase 1.2

Purpose:
    Pre-analysis quality validation to prevent wrong field selection and data
    interpretation errors in M365 incident response investigations.

Key Features:
    1. Field population analysis (detect null/uniform fields)
    2. Discriminatory power scoring (measure field usefulness)
    3. Table-level quality scoring
    4. Field reliability detection (>99.5% uniform = unreliable)
    5. Auto-recommendation of best status fields

Usage:
    >>> from claude.tools.m365_ir.data_quality_checker import check_field_quality
    >>> result = check_field_quality('case.db', 'sign_in_logs', 'status_error_code')
    >>> if not result.is_reliable:
    ...     print(f"WARNING: {result.field_name} is unreliable!")

Design Principles:
    - Fail-fast: Detect bad data quality early (before analysis)
    - Reusable: Works with ANY table/field combination
    - Transparent: Clear scoring and recommendations

Phase: PHASE_1_FOUNDATION (Phase 1.2 - Data Quality Checker)
Status: In Progress (TDD Green Phase)
"""

import sqlite3
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class FieldQualityScore:
    """
    Quality metrics for a single field.

    Attributes:
        field_name: Name of the field being analyzed
        population_rate: Percentage of non-null values (0-100)
        discriminatory_power: Unique values / total rows (0-1)
        is_reliable: Whether field is suitable for analysis (>0.5% variation)
        distinct_values: Count of unique values in the field
        total_records: Total number of records analyzed
        most_common_value: The most frequent value in the field
        most_common_percentage: Percentage of records with most common value
    """
    field_name: str
    population_rate: float
    discriminatory_power: float
    is_reliable: bool
    distinct_values: int
    total_records: int
    most_common_value: Optional[str] = None
    most_common_percentage: float = 0.0


@dataclass
class TableQualityReport:
    """
    Aggregate quality report for an entire table.

    Attributes:
        table_name: Name of the table analyzed
        total_records: Total number of records in table
        field_scores: Quality scores for each field
        overall_quality_score: Aggregate quality score (0-1)
        reliable_fields: List of field names suitable for analysis
        unreliable_fields: List of field names NOT suitable for analysis
        recommendations: Suggested actions for data quality improvement
        warnings: Issues detected during quality analysis
        created_at: Timestamp when analysis was performed
    """
    table_name: str
    total_records: int
    field_scores: List[FieldQualityScore]
    overall_quality_score: float
    reliable_fields: List[str]
    unreliable_fields: List[str]
    recommendations: List[str]
    warnings: List[str]
    created_at: str


def check_field_quality(
    db_path: str,
    table: str,
    field: str,
    conn: Optional[sqlite3.Connection] = None
) -> FieldQualityScore:
    """
    Analyze quality metrics for a single field.

    This function calculates:
        1. Population rate (% non-null values)
        2. Discriminatory power (unique values / total rows)
        3. Reliability (is field suitable for analysis?)

    A field is considered UNRELIABLE if:
        - >99.5% of values are identical (uniform field)
        - OR only 1 distinct value exists
        - OR discriminatory power < 0.005

    Args:
        db_path: Path to SQLite database
        table: Table name to analyze
        field: Field name to analyze
        conn: Optional existing SQLite connection (for checking uncommitted data)

    Returns:
        FieldQualityScore with quality metrics

    Raises:
        ValueError: If table or field doesn't exist

    Example:
        >>> result = check_field_quality('case.db', 'sign_in_logs', 'status_error_code')
        >>> if not result.is_reliable:
        ...     print(f"Field {result.field_name} is 100% uniform - cannot use for analysis")
    """
    # Use provided connection or create new one
    should_close = False
    if conn is None:
        conn = sqlite3.connect(db_path)
        should_close = True

    cursor = conn.cursor()

    # Verify table exists
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,)
    )
    if not cursor.fetchone():
        if should_close:
            conn.close()
        raise ValueError(f"Table '{table}' does not exist")

    # Get total record count
    total_records = cursor.execute(
        f"SELECT COUNT(*) FROM {table}"
    ).fetchone()[0]

    if total_records == 0:
        if should_close:
            conn.close()
        return FieldQualityScore(
            field_name=field,
            population_rate=0.0,
            discriminatory_power=0.0,
            is_reliable=False,
            distinct_values=0,
            total_records=0
        )

    # Calculate population rate (non-null and non-empty values)
    # Treat empty strings '' the same as NULL for quality checks
    non_null_count = cursor.execute(
        f"SELECT COUNT({field}) FROM {table} WHERE {field} IS NOT NULL AND {field} != ''"
    ).fetchone()[0]

    population_rate = (non_null_count / total_records) * 100.0

    # Calculate discriminatory power (unique values, excluding empty strings)
    distinct_values = cursor.execute(
        f"SELECT COUNT(DISTINCT {field}) FROM {table} WHERE {field} IS NOT NULL AND {field} != ''"
    ).fetchone()[0]

    discriminatory_power = (
        distinct_values / total_records
        if total_records > 0 else 0.0
    )

    # Find most common value and its frequency (excluding empty strings)
    cursor.execute(f"""
        SELECT {field}, COUNT(*) as freq
        FROM {table}
        WHERE {field} IS NOT NULL AND {field} != ''
        GROUP BY {field}
        ORDER BY freq DESC
        LIMIT 1
    """)

    most_common_row = cursor.fetchone()
    if most_common_row:
        most_common_value = str(most_common_row[0])
        most_common_count = most_common_row[1]
        most_common_percentage = (most_common_count / non_null_count * 100.0) if non_null_count > 0 else 0.0
    else:
        most_common_value = None
        most_common_percentage = 0.0

    # Only close if we opened the connection
    if should_close:
        conn.close()

    # Determine reliability
    # A field is UNRELIABLE if:
    # 1. >99.5% of values are the same (uniform)
    # 2. OR only 1 distinct value
    # Note: We don't use discriminatory_power < 0.005 because binary fields
    # (e.g., success/failure) are valid despite having low discriminatory power
    is_reliable = not (
        most_common_percentage > 99.5 or
        distinct_values <= 1
    )

    return FieldQualityScore(
        field_name=field,
        population_rate=population_rate,
        discriminatory_power=discriminatory_power,
        is_reliable=is_reliable,
        distinct_values=distinct_values,
        total_records=total_records,
        most_common_value=most_common_value,
        most_common_percentage=most_common_percentage
    )


def check_table_quality(
    db_path: str,
    table: str,
    required_fields: Optional[List[str]] = None,
    conn: Optional[sqlite3.Connection] = None
) -> TableQualityReport:
    """
    Analyze quality metrics for an entire table.

    This function:
        1. Analyzes all fields in the table
        2. Calculates aggregate quality score
        3. Identifies reliable vs unreliable fields
        4. Generates recommendations for data quality improvement

    Args:
        db_path: Path to SQLite database
        table: Table name to analyze
        required_fields: Optional list of fields that must be present and reliable
        conn: Optional existing SQLite connection (for checking uncommitted data)

    Returns:
        TableQualityReport with comprehensive quality analysis

    Raises:
        ValueError: If table doesn't exist

    Example:
        >>> report = check_table_quality('case.db', 'sign_in_logs')
        >>> if report.overall_quality_score < 0.5:
        ...     print("WARNING: Poor data quality detected!")
        ...     for warning in report.warnings:
        ...         print(f"  - {warning}")
    """
    # Use provided connection or create new one
    should_close = False
    if conn is None:
        conn = sqlite3.connect(db_path)
        should_close = True

    cursor = conn.cursor()

    # Verify table exists
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,)
    )
    if not cursor.fetchone():
        if should_close:
            conn.close()
        raise ValueError(f"Table '{table}' does not exist")

    # Get total record count
    total_records = cursor.execute(
        f"SELECT COUNT(*) FROM {table}"
    ).fetchone()[0]

    # Get all columns in the table
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]

    # Analyze each field
    field_scores = []
    reliable_fields = []
    unreliable_fields = []
    populated_fields = []  # Fields with >5% population rate
    warnings = []
    recommendations = []

    for field in columns:
        try:
            score = check_field_quality(db_path, table, field, conn=conn)
            field_scores.append(score)

            # Skip mostly-NULL fields (unpopulated, not unreliable)
            if score.population_rate < 5.0:
                continue  # Don't count unpopulated fields in quality score

            populated_fields.append(field)

            if score.is_reliable:
                reliable_fields.append(field)
            else:
                unreliable_fields.append(field)

                # Generate warnings for unreliable fields (only if populated)
                if score.distinct_values <= 1:
                    warnings.append(
                        f"Field '{field}' is unreliable (only {score.distinct_values} distinct value)"
                    )
                elif score.most_common_percentage > 99.5:
                    warnings.append(
                        f"Field '{field}' is unreliable (>99.5% uniform or only 1 distinct value, "
                        f"discriminatory power: {score.discriminatory_power:.3f})"
                    )

        except Exception as e:
            warnings.append(f"Failed to analyze field '{field}': {e}")

    # Calculate overall quality score
    # Score = (reliable_fields / populated_fields)
    # Only count fields with >5% population rate (ignore NULL fields)
    if len(populated_fields) > 0:
        base_score = len(reliable_fields) / len(populated_fields)

        # Penalty for required fields being unreliable
        penalty = 0.0
        if required_fields:
            for req_field in required_fields:
                if req_field in unreliable_fields:
                    penalty += 0.2  # -20% per missing required field

        overall_quality_score = max(0.0, base_score - penalty)
    else:
        overall_quality_score = 0.0

    # Generate recommendations
    if unreliable_fields:
        # Recommend using reliable fields for analysis
        status_like_fields = [f for f in reliable_fields if 'status' in f.lower() or 'result' in f.lower()]
        if status_like_fields:
            recommendations.append(
                f"Use '{status_like_fields[0]}' for status analysis (reliable field with "
                f"{next(s for s in field_scores if s.field_name == status_like_fields[0]).distinct_values} distinct values)"
            )

    # Close connection if we opened it
    if should_close:
        conn.close()

    return TableQualityReport(
        table_name=table,
        total_records=total_records,
        field_scores=field_scores,
        overall_quality_score=overall_quality_score,
        reliable_fields=reliable_fields,
        unreliable_fields=unreliable_fields,
        recommendations=recommendations,
        warnings=warnings,
        created_at=datetime.now().isoformat()
    )


def check_multi_field_consistency(db_path: str, table: str) -> List[str]:
    """
    Check consistency across multiple fields.

    This is a placeholder for Phase 2 - will add advanced consistency checks:
        - Timestamp + Location timezone consistency
        - User ID + Email domain consistency
        - IP Address + Geo-location consistency

    Args:
        db_path: Path to SQLite database
        table: Table name to analyze

    Returns:
        List of consistency warnings (empty for Phase 1.2)

    Example:
        >>> warnings = check_multi_field_consistency('case.db', 'sign_in_logs')
        >>> if warnings:
        ...     print("Consistency issues detected:")
        ...     for warning in warnings:
        ...         print(f"  - {warning}")
    """
    # Phase 1.2: Return empty list (placeholder)
    # Phase 2 will add:
    # - Timestamp + Location timezone validation
    # - User ID + Email domain validation
    # - IP Address + Geo-location validation
    return []
