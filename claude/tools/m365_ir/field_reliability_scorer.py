"""
M365 IR Data Quality System - Field Reliability Scorer

Multi-factor field reliability scoring system that enhances Phase 1's binary
reliable/unreliable classification with nuanced 0-1 scoring across 5 dimensions.

Created: 2026-01-07
Phase: PHASE_2_SMART_ANALYSIS (Phase 2.1.1)
"""

import sqlite3
import logging
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


# Scoring weights (sum to 100%)
UNIFORMITY_WEIGHT = 0.30  # 30%
DISCRIMINATORY_POWER_WEIGHT = 0.25  # 25%
POPULATION_RATE_WEIGHT = 0.15  # 15%
HISTORICAL_SUCCESS_WEIGHT = 0.20  # 20%
SEMANTIC_PREFERENCE_WEIGHT = 0.10  # 10%

# Thresholds
UNIFORMITY_THRESHOLD_PERCENT = 99.5  # Same as Phase 1
LOW_POPULATION_THRESHOLD = 0.50  # Warn if <50% populated
SPARSE_FIELD_THRESHOLD = 0.30  # Warn if <30% populated

# Preferred fields by log type (semantic preference)
PREFERRED_FIELDS = {
    'sign_in_logs': ['conditional_access_status'],
    'unified_audit_log': ['operation', 'result_status'],
}


@dataclass
class FieldReliabilityScore:
    """Detailed reliability score for a single field."""
    field_name: str
    overall_score: float  # 0-1 weighted average
    uniformity_score: float  # 0-1 (higher = more varied)
    discriminatory_power: float  # 0-1 (distinct values / total)
    population_rate: float  # 0-1 (populated rows / total rows)
    historical_success_rate: float  # 0-1 (from historical DB)
    semantic_preference: float  # 0-1 (preferred field bonus)
    warnings: List[str]
    recommendations: List[str]


@dataclass
class FieldRanking:
    """Ranked field with confidence level."""
    field_name: str
    reliability_score: FieldReliabilityScore
    rank: int
    confidence: str  # HIGH/MEDIUM/LOW


@dataclass
class FieldRecommendation:
    """Best field recommendation with reasoning."""
    recommended_field: str
    confidence: str
    all_candidates: List[FieldRanking]
    reasoning: str
    threshold_context: Optional['DynamicThresholds'] = None  # Phase 2.2


# Phase 2.2: Context-Aware Thresholds
@dataclass
class ThresholdContext:
    """Context information for dynamic threshold calculation."""
    record_count: int
    null_rate: float  # Overall null rate (0-1)
    log_type: str
    case_severity: Optional[str] = None  # 'routine' | 'suspected_breach' | 'confirmed_breach'


@dataclass
class DynamicThresholds:
    """Calculated thresholds for confidence classification."""
    high_threshold: float  # Threshold for HIGH confidence
    medium_threshold: float  # Threshold for MEDIUM confidence
    reasoning: str  # Human-readable explanation
    adjustments: dict  # Adjustment breakdown


def calculate_reliability_score(
    db_path: str,
    table: str,
    field: str,
    historical_db_path: Optional[str] = None
) -> FieldReliabilityScore:
    """
    Calculate multi-factor reliability score for a field.

    Scoring Dimensions (weighted):
        1. Uniformity Score (30%): How varied are values?
        2. Discriminatory Power (25%): How many distinct values?
        3. Population Rate (15%): How often is field populated?
        4. Historical Success Rate (20%): Past cases using this field?
        5. Semantic Preference (10%): Is this a preferred field?

    Args:
        db_path: Path to database containing the table
        table: Table name to analyze
        field: Field name to score
        historical_db_path: Optional path to historical learning database

    Returns:
        FieldReliabilityScore with detailed scoring breakdown

    Raises:
        ValueError: If table or field doesn't exist
        sqlite3.Error: If database query fails

    Example:
        >>> score = calculate_reliability_score('case.db', 'sign_in_logs', 'conditional_access_status')
        >>> print(f"Overall: {score.overall_score:.2f}, Uniformity: {score.uniformity_score:.2f}")
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    warnings = []
    recommendations = []

    try:
        # Verify table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table,)
        )
        if not cursor.fetchone():
            raise ValueError(f"Table '{table}' does not exist in database")

        # Verify field exists
        cursor.execute(f"PRAGMA table_info({table})")
        schema = cursor.fetchall()
        field_exists = any(col[1] == field for col in schema)
        if not field_exists:
            raise ValueError(f"Field '{field}' does not exist in table '{table}'")

        # 1. Calculate Uniformity Score (0-1, higher = more varied)
        uniformity_score = _calculate_uniformity_score(
            cursor, table, field, warnings
        )

        # 2. Calculate Discriminatory Power (distinct / total)
        discriminatory_power = _calculate_discriminatory_power(
            cursor, table, field
        )

        # 3. Calculate Population Rate (populated / total)
        population_rate = _calculate_population_rate(
            cursor, table, field, warnings
        )

        # 4. Calculate Historical Success Rate (from learning DB)
        historical_success_rate = _calculate_historical_success_rate(
            historical_db_path, table, field
        )

        # 5. Calculate Semantic Preference (1.0 if preferred, 0.0 otherwise)
        semantic_preference = _calculate_semantic_preference(
            table, field
        )

        # Calculate weighted overall score
        overall_score = (
            uniformity_score * UNIFORMITY_WEIGHT +
            discriminatory_power * DISCRIMINATORY_POWER_WEIGHT +
            population_rate * POPULATION_RATE_WEIGHT +
            historical_success_rate * HISTORICAL_SUCCESS_WEIGHT +
            semantic_preference * SEMANTIC_PREFERENCE_WEIGHT
        )

        # Clamp to 0-1 range
        overall_score = max(0.0, min(1.0, overall_score))

        # Generate recommendations
        if overall_score >= 0.7:
            recommendations.append(f"Field '{field}' is highly reliable (score: {overall_score:.2f})")
        elif overall_score >= 0.5:
            recommendations.append(f"Field '{field}' is moderately reliable (score: {overall_score:.2f})")
        else:
            recommendations.append(f"Field '{field}' is unreliable (score: {overall_score:.2f}) - consider alternatives")

        return FieldReliabilityScore(
            field_name=field,
            overall_score=overall_score,
            uniformity_score=uniformity_score,
            discriminatory_power=discriminatory_power,
            population_rate=population_rate,
            historical_success_rate=historical_success_rate,
            semantic_preference=semantic_preference,
            warnings=warnings,
            recommendations=recommendations
        )

    finally:
        conn.close()


def _calculate_uniformity_score(
    cursor: sqlite3.Cursor,
    table: str,
    field: str,
    warnings: List[str]
) -> float:
    """
    Calculate uniformity score (0-1, higher = more varied).

    Uniformity measures how "uniform" (same) the field values are:
    - 100% same value → uniformity_score = 0.0 (completely uniform, no variety)
    - All distinct values → uniformity_score = 1.0 (no uniformity, maximum variety)

    Uses piecewise function aligned with Phase 1's 99.5% threshold:
    - mode_percentage > 99.5%: Low score (0-0.2) - unreliable
    - mode_percentage ≤ 50%: High score (0.8-1.0) - reliable
    - In between: Gradual transition

    Args:
        cursor: Database cursor
        table: Table name
        field: Field name
        warnings: List to append warnings to

    Returns:
        Uniformity score (0-1)
    """
    # Get total count
    total = cursor.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    if total == 0:
        return 0.0

    # Get distinct value count
    distinct = cursor.execute(
        f"SELECT COUNT(DISTINCT {field}) FROM {table}"
    ).fetchone()[0]

    # If only 1 distinct value → 100% uniform → score 0.0
    if distinct == 1:
        warnings.append(f"Field '{field}' has only 1 distinct value (100% uniform)")
        return 0.0

    # Get mode (most common value) percentage
    mode_count = cursor.execute(
        f"""
        SELECT COUNT(*) as cnt
        FROM {table}
        GROUP BY {field}
        ORDER BY cnt DESC
        LIMIT 1
        """
    ).fetchone()[0]

    mode_percentage = (mode_count / total) * 100.0

    # Calculate uniformity score using piecewise function
    # This ensures backward compatibility with Phase 1's 99.5% threshold
    if mode_percentage > UNIFORMITY_THRESHOLD_PERCENT:
        # Highly uniform (>99.5%) - Phase 1 would reject
        # Score: 0.0-0.2 (very unreliable)
        uniformity_score = max(0.0, (100.0 - mode_percentage) / (100.0 - UNIFORMITY_THRESHOLD_PERCENT) * 0.2)
        warnings.append(
            f"Field '{field}' is >{UNIFORMITY_THRESHOLD_PERCENT}% uniform "
            f"({mode_percentage:.1f}% same value) - likely unreliable"
        )
    elif mode_percentage <= 50.0:
        # Low uniformity (≤50%) - highly reliable
        # Score: 0.9-1.0 (highly reliable)
        # Perfect variety (1/n each) gets close to 1.0
        uniformity_score = 0.9 + (50.0 - mode_percentage) / 50.0 * 0.1
    elif mode_percentage <= 90.0:
        # Moderate uniformity (50-90%) - Phase 1 would accept
        # Score: 0.6-0.9 (moderately to highly reliable)
        # Linear interpolation
        uniformity_score = 0.6 + (90.0 - mode_percentage) / (90.0 - 50.0) * 0.3
    else:
        # High uniformity but below threshold (90-99.5%) - Phase 1 would accept
        # Score: 0.2-0.6 (moderately reliable)
        # Linear interpolation - gets lower as it approaches threshold
        uniformity_score = 0.2 + (UNIFORMITY_THRESHOLD_PERCENT - mode_percentage) / (UNIFORMITY_THRESHOLD_PERCENT - 90.0) * 0.4

    return uniformity_score


def _calculate_discriminatory_power(
    cursor: sqlite3.Cursor,
    table: str,
    field: str
) -> float:
    """
    Calculate discriminatory power (distinct values / total records).

    High discriminatory power means the field can distinguish between records.
    Low discriminatory power means many records share the same values.

    Args:
        cursor: Database cursor
        table: Table name
        field: Field name

    Returns:
        Discriminatory power (0-1)
    """
    # Get total count
    total = cursor.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    if total == 0:
        return 0.0

    # Get distinct value count
    distinct = cursor.execute(
        f"SELECT COUNT(DISTINCT {field}) FROM {table}"
    ).fetchone()[0]

    # Calculate discriminatory power
    return distinct / total


def _calculate_population_rate(
    cursor: sqlite3.Cursor,
    table: str,
    field: str,
    warnings: List[str]
) -> float:
    """
    Calculate population rate (non-NULL / total records).

    High population rate means field is consistently populated.
    Low population rate means field is sparse/missing.

    Args:
        cursor: Database cursor
        table: Table name
        field: Field name
        warnings: List to append warnings to

    Returns:
        Population rate (0-1)
    """
    # Get total count
    total = cursor.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    if total == 0:
        return 0.0

    # Get non-NULL count
    # Note: In SQLite, empty strings '' are not NULL, but we should count them as NULL
    # for M365 IR data (empty strings are common in CSV exports)
    populated = cursor.execute(
        f"SELECT COUNT(*) FROM {table} WHERE {field} IS NOT NULL AND {field} != ''"
    ).fetchone()[0]

    # Calculate population rate
    population_rate = populated / total

    # Warn if low population
    if population_rate < SPARSE_FIELD_THRESHOLD:
        warnings.append(
            f"Field '{field}' is very sparse ({population_rate*100:.1f}% populated) - "
            f"may not be reliable for verification"
        )
    elif population_rate < LOW_POPULATION_THRESHOLD:
        warnings.append(
            f"Field '{field}' has low population rate ({population_rate*100:.1f}%)"
        )

    return population_rate


def _calculate_historical_success_rate(
    historical_db_path: Optional[str],
    table: str,
    field: str
) -> float:
    """
    Calculate historical success rate from learning database.

    Queries historical cases to see how often this field was used successfully.

    Args:
        historical_db_path: Path to historical learning database (optional)
        table: Log type (e.g., 'sign_in_logs')
        field: Field name

    Returns:
        Historical success rate (0-1), defaults to 0.5 if no history
    """
    # No historical database provided - return neutral default
    if not historical_db_path:
        return 0.5

    try:
        conn = sqlite3.connect(historical_db_path)
        cursor = conn.cursor()

        # Query average success rate for this field
        cursor.execute("""
            SELECT AVG(verification_successful)
            FROM field_reliability_history
            WHERE log_type = ?
              AND field_name = ?
              AND used_for_verification = 1
              AND verification_successful IS NOT NULL
        """, (table, field))

        result = cursor.fetchone()[0]
        conn.close()

        # If no history found, return neutral default
        if result is None:
            return 0.5

        # Convert from 0-1 integer average to float
        return float(result)

    except sqlite3.Error:
        # If database doesn't exist or query fails, return neutral default
        return 0.5


def _calculate_semantic_preference(table: str, field: str) -> float:
    """
    Calculate semantic preference score.

    Gives bonus to fields known to be reliable from domain knowledge.

    Args:
        table: Log type (e.g., 'sign_in_logs')
        field: Field name

    Returns:
        1.0 if preferred field, 0.0 otherwise
    """
    preferred_fields = PREFERRED_FIELDS.get(table, [])
    return 1.0 if field in preferred_fields else 0.0


# ==================== Phase 2.1.2: Historical Learning ====================


def create_history_database(history_db_path: str) -> None:
    """
    Create historical learning database with field_reliability_history table.

    Args:
        history_db_path: Path to history database file

    Raises:
        sqlite3.Error: If database creation fails
    """
    conn = sqlite3.connect(history_db_path)
    cursor = conn.cursor()

    # Create field_reliability_history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS field_reliability_history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id TEXT NOT NULL,
            log_type TEXT NOT NULL,
            field_name TEXT NOT NULL,
            reliability_score REAL NOT NULL,
            used_for_verification INTEGER NOT NULL,
            verification_successful INTEGER,
            breach_detected INTEGER,
            notes TEXT,
            created_at TEXT NOT NULL,

            UNIQUE(case_id, log_type, field_name)
        )
    """)

    # Create indexes for fast queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_field_reliability_by_field
        ON field_reliability_history(log_type, field_name)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_field_reliability_by_case
        ON field_reliability_history(case_id)
    """)

    conn.commit()
    conn.close()


def store_field_usage(
    history_db_path: str,
    case_id: str,
    log_type: str,
    field_name: str,
    reliability_score: float,
    used_for_verification: bool,
    verification_successful: Optional[bool] = None,
    breach_detected: Optional[bool] = None,
    notes: Optional[str] = None
) -> None:
    """
    Store field usage outcome for historical learning.

    Args:
        history_db_path: Path to history database
        case_id: Investigation case ID (e.g., PIR-OCULUS-2025-12-19)
        log_type: Log type (e.g., 'sign_in_logs')
        field_name: Field that was used/evaluated
        reliability_score: Calculated reliability score (0-1)
        used_for_verification: Whether this field was selected for verification
        verification_successful: Whether verification completed without errors (optional)
        breach_detected: Whether breach was detected using this field (optional)
        notes: Additional notes (optional)

    Raises:
        sqlite3.Error: If database write fails
    """
    conn = sqlite3.connect(history_db_path)
    cursor = conn.cursor()

    # Convert booleans to integers for SQLite
    used_int = 1 if used_for_verification else 0
    success_int = 1 if verification_successful else (0 if verification_successful is False else None)
    breach_int = 1 if breach_detected else (0 if breach_detected is False else None)

    cursor.execute("""
        INSERT OR REPLACE INTO field_reliability_history
        (case_id, log_type, field_name, reliability_score, used_for_verification,
         verification_successful, breach_detected, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        case_id,
        log_type,
        field_name,
        reliability_score,
        used_int,
        success_int,
        breach_int,
        notes,
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()


def query_historical_success_rate(
    log_type: str,
    field_name: str,
    historical_db_path: str
) -> float:
    """
    Query historical success rate for a specific field.

    Public API wrapper around _calculate_historical_success_rate.

    Args:
        log_type: Log type (e.g., 'sign_in_logs', 'unified_audit_log', 'legacy_auth_logs')
        field_name: Field name to query
        historical_db_path: Path to historical learning database

    Returns:
        Historical success rate (0-1), defaults to 0.5 if no history

    Example:
        >>> rate = query_historical_success_rate(
        ...     log_type='sign_in_logs',
        ...     field_name='conditional_access_status',
        ...     historical_db_path='~/.maia/data/databases/system/m365_ir_field_reliability_history.db'
        ... )
        >>> print(f"Historical success: {rate*100:.0f}%")
    """
    return _calculate_historical_success_rate(historical_db_path, log_type, field_name)


# ==================== Phase 2.1.3: Auto-Discovery & Ranking ====================


# Keywords to match for candidate field discovery (case-insensitive)
CANDIDATE_FIELD_KEYWORDS = [
    'status', 'result', 'error', 'success', 'failure', 'outcome', 'code'
]


def discover_candidate_fields(
    db_path: str,
    table: str,
    log_type: str
) -> List[str]:
    """
    Auto-discover candidate fields for verification from table schema.

    Scans table schema and finds fields containing keywords like 'status',
    'result', 'error', etc. (case-insensitive).

    Args:
        db_path: Path to database
        table: Table name to scan
        log_type: Log type (e.g., 'sign_in_logs') - currently unused but reserved for future filtering

    Returns:
        List of field names that match keywords

    Raises:
        ValueError: If table doesn't exist
        sqlite3.Error: If database query fails

    Example:
        >>> candidates = discover_candidate_fields('case.db', 'sign_in_logs', 'sign_in_logs')
        >>> print(candidates)
        ['conditional_access_status', 'status_error_code', 'result_status']
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Verify table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table,)
        )
        if not cursor.fetchone():
            raise ValueError(f"Table '{table}' does not exist in database")

        # Get all column names
        cursor.execute(f"PRAGMA table_info({table})")
        all_columns = [row[1] for row in cursor.fetchall()]

        # Filter columns containing candidate keywords (case-insensitive)
        candidate_fields = []
        for column in all_columns:
            column_lower = column.lower()
            if any(keyword in column_lower for keyword in CANDIDATE_FIELD_KEYWORDS):
                candidate_fields.append(column)

        return candidate_fields

    finally:
        conn.close()


# Phase 2.2: Context-Aware Threshold Calculation

def calculate_dynamic_thresholds(
    context: ThresholdContext,
    base_high: float = 0.7,
    base_medium: float = 0.5
) -> DynamicThresholds:
    """
    Calculate context-aware confidence thresholds.

    Adjustments based on case characteristics:
    1. Dataset Size:
       - <100 records: -0.1 to both thresholds
       - 100-1000: -0.05 to both thresholds
       - 1000-10K: No adjustment (baseline)
       - 10K-100K: +0.025 to both thresholds
       - >100K: +0.05 to both thresholds

    2. Data Quality (null rate):
       - <10% null rate: +0.05 (high quality, can be stricter)
       - 10-30% null rate: No adjustment
       - 30-50% null rate: -0.05 (lower quality, be lenient)
       - >50% null rate: -0.1 (very low quality, very lenient)

    3. Log Type:
       - sign_in_logs: No adjustment (validated baseline)
       - unified_audit_log: -0.05 (less uniformity expected)
       - legacy_auth_logs: -0.05 (simpler schema, fewer fields)

    4. Case Severity:
       - routine: No adjustment
       - suspected_breach: -0.1 (lower threshold, catch all indicators)
       - confirmed_breach: -0.05 (slightly lower, comprehensive analysis)

    Args:
        context: ThresholdContext with case characteristics
        base_high: Baseline HIGH threshold (default: 0.7)
        base_medium: Baseline MEDIUM threshold (default: 0.5)

    Returns:
        DynamicThresholds with adjusted high/medium thresholds

    Safety Constraints:
        - HIGH threshold >= MEDIUM threshold + 0.1
        - MEDIUM threshold >= 0.15 (minimum useful threshold)
        - HIGH threshold <= 0.85 (avoid unreachable thresholds)
    """
    adjustments = {}
    reasoning_parts = []

    # 1. Dataset Size Adjustment
    if context.record_count < 100:
        adjustments['dataset_size'] = -0.1
        reasoning_parts.append("Small dataset (<100 records): -0.1")
    elif context.record_count < 1000:
        adjustments['dataset_size'] = -0.05
        reasoning_parts.append("Small-medium dataset (100-1K records): -0.05")
    elif context.record_count < 10000:
        adjustments['dataset_size'] = 0.0
        reasoning_parts.append("Medium dataset (1K-10K records): baseline")
    elif context.record_count < 100000:
        adjustments['dataset_size'] = 0.025
        reasoning_parts.append("Large dataset (10K-100K records): +0.025")
    else:
        adjustments['dataset_size'] = 0.05
        reasoning_parts.append(f"Very large dataset ({context.record_count:,} records): +0.05")

    # 2. Data Quality Adjustment (null rate)
    if context.null_rate < 0.10:
        adjustments['data_quality'] = 0.05
        reasoning_parts.append(f"High quality data ({context.null_rate:.0%} null): +0.05")
    elif context.null_rate < 0.30:
        adjustments['data_quality'] = 0.0
        reasoning_parts.append(f"Good quality data ({context.null_rate:.0%} null): baseline")
    elif context.null_rate < 0.50:
        adjustments['data_quality'] = -0.05
        reasoning_parts.append(f"Lower quality data ({context.null_rate:.0%} null): -0.05")
    else:
        adjustments['data_quality'] = -0.1
        reasoning_parts.append(f"Low quality data ({context.null_rate:.0%} null): -0.1")

    # 3. Log Type Adjustment
    if context.log_type == 'sign_in_logs':
        adjustments['log_type'] = 0.0
        reasoning_parts.append("Log type (sign_in_logs): baseline")
    elif context.log_type == 'unified_audit_log':
        adjustments['log_type'] = -0.05
        reasoning_parts.append("Log type (unified_audit_log): -0.05")
    elif context.log_type == 'legacy_auth_logs':
        adjustments['log_type'] = -0.05
        reasoning_parts.append("Log type (legacy_auth_logs): -0.05")
    else:
        adjustments['log_type'] = 0.0
        reasoning_parts.append(f"Log type ({context.log_type}): baseline")

    # 4. Case Severity Adjustment
    if context.case_severity == 'suspected_breach':
        adjustments['case_severity'] = -0.1
        reasoning_parts.append("Case severity (suspected breach): -0.1")
    elif context.case_severity == 'confirmed_breach':
        adjustments['case_severity'] = -0.05
        reasoning_parts.append("Case severity (confirmed breach): -0.05")
    else:
        adjustments['case_severity'] = 0.0
        if context.case_severity:
            reasoning_parts.append(f"Case severity ({context.case_severity}): baseline")

    # Calculate total adjustment
    total_adjustment = sum(adjustments.values())

    # Apply adjustments to base thresholds
    high_threshold = base_high + total_adjustment
    medium_threshold = base_medium + total_adjustment

    # Apply safety constraints
    # Minimum MEDIUM threshold
    if medium_threshold < 0.15:
        medium_threshold = 0.15
        reasoning_parts.append("⚠️ Applied minimum MEDIUM threshold (0.15)")

    # Maximum HIGH threshold
    if high_threshold > 0.85:
        high_threshold = 0.85
        reasoning_parts.append("⚠️ Applied maximum HIGH threshold (0.85)")

    # Ensure HIGH >= MEDIUM + 0.1
    if high_threshold < medium_threshold + 0.1:
        high_threshold = medium_threshold + 0.1
        reasoning_parts.append(f"⚠️ Adjusted HIGH to maintain +0.1 gap above MEDIUM")

    # Build final reasoning
    if total_adjustment == 0:
        reasoning = "Baseline thresholds (no adjustments needed)"
    else:
        reasoning = f"Adjusted by {total_adjustment:+.2f}: " + "; ".join(reasoning_parts)

    return DynamicThresholds(
        high_threshold=high_threshold,
        medium_threshold=medium_threshold,
        reasoning=reasoning,
        adjustments=adjustments
    )


def extract_threshold_context(
    db_path: str,
    table: str,
    log_type: str,
    case_severity: Optional[str] = None
) -> ThresholdContext:
    """
    Extract threshold context from database by analyzing table characteristics.

    Calculates:
    - record_count: Total rows in table
    - null_rate: Overall null rate across all fields (excludes metadata fields)

    Args:
        db_path: Path to database
        table: Table name to analyze
        log_type: Log type (e.g., 'sign_in_logs')
        case_severity: Optional case severity override

    Returns:
        ThresholdContext with extracted characteristics

    Raises:
        ValueError: If table doesn't exist
        sqlite3.Error: If database query fails

    Example:
        >>> context = extract_threshold_context('case.db', 'sign_in_logs', 'sign_in_logs')
        >>> print(f"Records: {context.record_count}, Null Rate: {context.null_rate:.1%}")
        Records: 5000, Null Rate: 25.0%
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Verify table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table,)
        )
        if not cursor.fetchone():
            raise ValueError(f"Table '{table}' does not exist in database")

        # Get record count
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        record_count = cursor.fetchone()[0]

        # Get all column names (excluding metadata fields)
        cursor.execute(f"PRAGMA table_info({table})")
        all_columns = [row[1] for row in cursor.fetchall()]

        # Exclude metadata fields from null rate calculation
        metadata_fields = {'id', 'raw_record', 'imported_at', 'timestamp'}
        data_columns = [col for col in all_columns if col not in metadata_fields]

        # Calculate overall null rate across data columns
        if not data_columns or record_count == 0:
            null_rate = 0.0
        else:
            null_counts = []
            for column in data_columns:
                cursor.execute(f"""
                    SELECT COUNT(*) FROM {table}
                    WHERE {column} IS NULL OR {column} = ''
                """)
                null_count = cursor.fetchone()[0]
                null_counts.append(null_count)

            # Average null rate across all data columns
            total_cells = record_count * len(data_columns)
            total_nulls = sum(null_counts)
            null_rate = total_nulls / total_cells if total_cells > 0 else 0.0

        return ThresholdContext(
            record_count=record_count,
            null_rate=null_rate,
            log_type=log_type,
            case_severity=case_severity
        )

    finally:
        conn.close()


def rank_fields_by_reliability(
    db_path: str,
    table: str,
    log_type: str,
    historical_db_path: Optional[str] = None,
    context: Optional[ThresholdContext] = None
) -> List[FieldRanking]:
    """
    Auto-discover and rank fields by reliability using context-aware thresholds.

    This is a convenience wrapper that:
    1. Auto-discovers candidate fields from table schema
    2. Extracts threshold context (if not provided)
    3. Ranks fields using dynamic thresholds

    Args:
        db_path: Path to database
        table: Table name
        log_type: Log type (e.g., 'sign_in_logs')
        historical_db_path: Optional path to historical learning database
        context: Optional ThresholdContext (auto-extracted if not provided)

    Returns:
        List of FieldRanking sorted by score (descending)

    Example:
        >>> # With auto context extraction:
        >>> rankings = rank_fields_by_reliability('case.db', 'sign_in_logs', 'sign_in_logs')

        >>> # With explicit context:
        >>> context = ThresholdContext(record_count=50, null_rate=0.2, log_type='sign_in_logs')
        >>> rankings = rank_fields_by_reliability('case.db', 'sign_in_logs', 'sign_in_logs', context=context)
    """
    # Auto-discover candidate fields
    candidate_fields = discover_candidate_fields(db_path, table, log_type)

    # Extract context if not provided
    if context is None:
        context = extract_threshold_context(db_path, table, log_type)

    # Rank candidates using context-aware thresholds
    return rank_candidate_fields(
        db_path=db_path,
        table=table,
        candidate_fields=candidate_fields,
        historical_db_path=historical_db_path,
        context=context
    )


def rank_candidate_fields(
    db_path: str,
    table: str,
    candidate_fields: List[str],
    historical_db_path: Optional[str] = None,
    context: Optional[ThresholdContext] = None
) -> List[FieldRanking]:
    """
    Rank candidate fields by reliability score using context-aware thresholds.

    Calculates reliability score for each field and sorts by overall_score
    (descending). Assigns rank numbers and confidence levels using dynamic
    thresholds based on case context (Phase 2.2).

    Args:
        db_path: Path to database
        table: Table name
        candidate_fields: List of field names to rank
        historical_db_path: Optional path to historical learning database
        context: Optional ThresholdContext for dynamic thresholds (Phase 2.2)

    Returns:
        List of FieldRanking sorted by score (descending)

    Confidence Levels (Phase 2.2 - context-aware):
        - If context provided: Uses calculate_dynamic_thresholds()
        - If context is None: Uses baseline thresholds (0.7 HIGH, 0.5 MEDIUM)

    Example:
        >>> # Baseline thresholds (backward compatibility):
        >>> rankings = rank_candidate_fields('case.db', 'sign_in_logs', ['field_a', 'field_b'])

        >>> # Context-aware thresholds (Phase 2.2):
        >>> context = ThresholdContext(record_count=50, null_rate=0.2, log_type='sign_in_logs')
        >>> rankings = rank_candidate_fields('case.db', 'sign_in_logs', ['field_a', 'field_b'], context=context)
    """
    # Calculate scores for all candidates
    field_scores = []
    for field in candidate_fields:
        try:
            score = calculate_reliability_score(
                db_path,
                table,
                field,
                historical_db_path=historical_db_path
            )
            field_scores.append((field, score))
        except Exception as e:
            logger.warning(f"Failed to score field '{field}': {e}")
            continue

    # Sort by overall_score (descending)
    field_scores.sort(key=lambda x: x[1].overall_score, reverse=True)

    # Phase 2.2: Calculate dynamic thresholds if context provided
    if context is not None:
        thresholds = calculate_dynamic_thresholds(context)
        high_threshold = thresholds.high_threshold
        medium_threshold = thresholds.medium_threshold
    else:
        # Backward compatibility: Use baseline thresholds
        high_threshold = 0.7
        medium_threshold = 0.5

    # Create rankings with rank numbers and confidence levels
    rankings = []
    for rank, (field, score) in enumerate(field_scores, start=1):
        # Determine confidence level using dynamic or baseline thresholds
        if score.overall_score >= high_threshold:
            confidence = 'HIGH'
        elif score.overall_score >= medium_threshold:
            confidence = 'MEDIUM'
        else:
            confidence = 'LOW'

        rankings.append(FieldRanking(
            field_name=field,
            reliability_score=score,
            rank=rank,
            confidence=confidence
        ))

    return rankings


def recommend_best_field(
    db_path: str,
    table: str,
    log_type: str,
    historical_db_path: Optional[str] = None,
    context: Optional[ThresholdContext] = None
) -> FieldRecommendation:
    """
    Recommend best field for verification with reasoning (Phase 2.2 context-aware).

    Combines auto-discovery and ranking to recommend the highest-scoring field
    using context-aware thresholds.

    Args:
        db_path: Path to database
        table: Table name
        log_type: Log type (e.g., 'sign_in_logs')
        historical_db_path: Optional path to historical learning database
        context: Optional ThresholdContext for dynamic thresholds (Phase 2.2)

    Returns:
        FieldRecommendation with top field, reasoning, and threshold context

    Raises:
        ValueError: If no candidate fields found

    Example:
        >>> # Baseline thresholds:
        >>> rec = recommend_best_field('case.db', 'sign_in_logs', 'sign_in_logs')

        >>> # Context-aware thresholds:
        >>> context = ThresholdContext(record_count=50, null_rate=0.2, log_type='sign_in_logs')
        >>> rec = recommend_best_field('case.db', 'sign_in_logs', 'sign_in_logs', context=context)
    """
    # Discover candidate fields
    candidate_fields = discover_candidate_fields(db_path, table, log_type)

    if not candidate_fields:
        raise ValueError(
            f"No candidate fields found in table '{table}'. "
            f"Looking for fields with keywords: {', '.join(CANDIDATE_FIELD_KEYWORDS)}"
        )

    # Extract context if not provided (Phase 2.2)
    if context is None:
        context = extract_threshold_context(db_path, table, log_type)

    # Rank all candidates with context-aware thresholds
    rankings = rank_candidate_fields(
        db_path,
        table,
        candidate_fields,
        historical_db_path=historical_db_path,
        context=context
    )

    if not rankings:
        raise ValueError(
            f"No fields could be scored in table '{table}'. "
            f"All {len(candidate_fields)} candidate fields failed scoring."
        )

    # Get top field
    best_ranking = rankings[0]

    # Phase 2.2: Calculate dynamic thresholds for reasoning
    thresholds = calculate_dynamic_thresholds(context)

    # Generate reasoning with threshold context
    reasoning_parts = [
        f"Selected '{best_ranking.field_name}' (rank #{best_ranking.rank} of {len(rankings)})",
        f"Overall score: {best_ranking.reliability_score.overall_score:.2f}",
        f"Uniformity: {best_ranking.reliability_score.uniformity_score:.2f}",
        f"Discriminatory power: {best_ranking.reliability_score.discriminatory_power:.2f}",
        f"Population: {best_ranking.reliability_score.population_rate*100:.1f}%"
    ]

    # Add historical context if available
    if best_ranking.reliability_score.historical_success_rate != 0.5:
        reasoning_parts.append(
            f"Historical success: {best_ranking.reliability_score.historical_success_rate*100:.0f}%"
        )

    # Add semantic preference if applicable
    if best_ranking.reliability_score.semantic_preference > 0:
        reasoning_parts.append("Preferred field (domain knowledge)")

    # Phase 2.2: Add threshold context to reasoning
    reasoning_parts.append(
        f"Thresholds: HIGH={thresholds.high_threshold:.2f}, MEDIUM={thresholds.medium_threshold:.2f}"
    )

    reasoning = ". ".join(reasoning_parts) + "."

    return FieldRecommendation(
        recommended_field=best_ranking.field_name,
        confidence=best_ranking.confidence,
        all_candidates=rankings,
        reasoning=reasoning,
        threshold_context=thresholds  # Phase 2.2
    )
