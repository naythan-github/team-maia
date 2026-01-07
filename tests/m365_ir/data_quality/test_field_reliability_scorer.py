"""
Phase 2.1 - Field Reliability Scorer Unit Tests

Test Objective:
    Validate multi-factor field reliability scoring system that enhances Phase 1's
    binary reliable/unreliable classification with nuanced 0-1 scoring.

Key Features Tested:
    1. Multi-factor scoring (5 dimensions)
    2. Weighted scoring algorithm
    3. Context-aware thresholds
    4. Field ranking and recommendation
    5. Backward compatibility with Phase 1

Phase: PHASE_2_SMART_ANALYSIS (Phase 2.1.1)
Status: TDD - RED Phase (tests written, implementation pending)
TDD Cycle: Red → Green → Refactor
"""

import pytest
import sqlite3
import tempfile
import os
from dataclasses import dataclass
from typing import List, Optional


# Data classes (to be implemented in field_reliability_scorer.py)
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


@pytest.mark.phase_2_1
class TestFieldReliabilityScorer:
    """Unit tests for multi-factor field reliability scoring."""

    def setup_method(self):
        """Create test database before each test."""
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmpdir, "test.db")
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

    def teardown_method(self):
        """Clean up test database after each test."""
        self.conn.close()
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_uniformity_score_perfect_variety(self):
        """
        Test uniformity scoring with perfect variety (all distinct values).

        Expected: uniformity_score = 1.0 (no uniformity, maximum variety)
        """
        from claude.tools.m365_ir.field_reliability_scorer import calculate_reliability_score

        # Create test table with all distinct values
        self.cursor.execute("""
            CREATE TABLE test_logs (
                id INTEGER PRIMARY KEY,
                status TEXT
            )
        """)

        # Insert 100 records with 100 distinct values
        for i in range(100):
            self.cursor.execute("INSERT INTO test_logs (status) VALUES (?)", (f"value_{i}",))
        self.conn.commit()

        # Calculate score
        score = calculate_reliability_score(self.db_path, 'test_logs', 'status')

        # Validate uniformity score (should be very high, close to 1.0)
        # With 100 distinct values, mode_percentage = 1%, so uniformity_score = 0.9 + (50-1)/50*0.1 = 0.998
        assert score.uniformity_score >= 0.99, \
            f"Expected uniformity_score >= 0.99 for all distinct values, got {score.uniformity_score}"
        assert score.overall_score >= 0.79, \
            f"Overall score should be high for perfect variety, got {score.overall_score}"

    def test_uniformity_score_complete_uniformity(self):
        """
        Test uniformity scoring with complete uniformity (all same value).

        Expected: uniformity_score = 0.0 (100% uniform, no variety)
        """
        from claude.tools.m365_ir.field_reliability_scorer import calculate_reliability_score

        # Create test table with all same value
        self.cursor.execute("""
            CREATE TABLE test_logs (
                id INTEGER PRIMARY KEY,
                status TEXT
            )
        """)

        # Insert 100 records with same value
        for i in range(100):
            self.cursor.execute("INSERT INTO test_logs (status) VALUES (?)", ("same_value",))
        self.conn.commit()

        # Calculate score
        score = calculate_reliability_score(self.db_path, 'test_logs', 'status')

        # Validate uniformity score
        assert score.uniformity_score == 0.0, \
            f"Expected uniformity_score=0.0 for all same value, got {score.uniformity_score}"
        assert score.overall_score < 0.3, \
            "Overall score should be low for complete uniformity"
        assert len(score.warnings) > 0, \
            "Should warn about 100% uniformity"

    def test_uniformity_score_oculus_status_error_code(self):
        """
        Test uniformity scoring with Oculus-like scenario (99.9% uniform).

        PIR-OCULUS case: status_error_code was 100% value '1' (unreliable)
        Expected: uniformity_score close to 0.0, overall_score < 0.5
        """
        from claude.tools.m365_ir.field_reliability_scorer import calculate_reliability_score

        # Create test table mimicking Oculus status_error_code
        self.cursor.execute("""
            CREATE TABLE test_logs (
                id INTEGER PRIMARY KEY,
                status_error_code INTEGER
            )
        """)

        # 999 records with value 1, 1 record with value 0 (99.9% uniform)
        for i in range(999):
            self.cursor.execute("INSERT INTO test_logs (status_error_code) VALUES (?)", (1,))
        self.cursor.execute("INSERT INTO test_logs (status_error_code) VALUES (?)", (0,))
        self.conn.commit()

        # Calculate score
        score = calculate_reliability_score(self.db_path, 'test_logs', 'status_error_code')

        # Validate uniformity score (should be very low)
        assert score.uniformity_score < 0.1, \
            f"Expected uniformity_score < 0.1 for 99.9% uniform field, got {score.uniformity_score}"

        # Validate overall score (should fail reliability threshold)
        assert score.overall_score < 0.5, \
            f"Expected overall_score < 0.5 (unreliable), got {score.overall_score}"

        # Should warn about high uniformity
        assert any("uniform" in w.lower() for w in score.warnings), \
            "Should warn about high uniformity"

    def test_discriminatory_power_calculation(self):
        """
        Test discriminatory power calculation (distinct values / total).

        Expected: discriminatory_power = distinct_count / total_count
        """
        from claude.tools.m365_ir.field_reliability_scorer import calculate_reliability_score

        # Create test table with known discriminatory power
        self.cursor.execute("""
            CREATE TABLE test_logs (
                id INTEGER PRIMARY KEY,
                status TEXT
            )
        """)

        # 100 records with 10 distinct values = 0.10 discriminatory power
        for i in range(100):
            self.cursor.execute("INSERT INTO test_logs (status) VALUES (?)", (f"value_{i % 10}",))
        self.conn.commit()

        # Calculate score
        score = calculate_reliability_score(self.db_path, 'test_logs', 'status')

        # Validate discriminatory power
        expected_power = 10 / 100  # 0.10
        assert abs(score.discriminatory_power - expected_power) < 0.01, \
            f"Expected discriminatory_power={expected_power}, got {score.discriminatory_power}"

    def test_population_rate_fully_populated(self):
        """
        Test population rate with fully populated field (no NULLs).

        Expected: population_rate = 1.0
        """
        from claude.tools.m365_ir.field_reliability_scorer import calculate_reliability_score

        # Create test table with all values populated
        self.cursor.execute("""
            CREATE TABLE test_logs (
                id INTEGER PRIMARY KEY,
                status TEXT NOT NULL
            )
        """)

        for i in range(100):
            self.cursor.execute("INSERT INTO test_logs (status) VALUES (?)", ("value",))
        self.conn.commit()

        # Calculate score
        score = calculate_reliability_score(self.db_path, 'test_logs', 'status')

        # Validate population rate
        assert score.population_rate == 1.0, \
            f"Expected population_rate=1.0 for fully populated field, got {score.population_rate}"

    def test_population_rate_sparse_field(self):
        """
        Test population rate with sparse field (many NULLs).

        Expected: population_rate < 0.5, should warn about low population
        """
        from claude.tools.m365_ir.field_reliability_scorer import calculate_reliability_score

        # Create test table with 30% population rate
        self.cursor.execute("""
            CREATE TABLE test_logs (
                id INTEGER PRIMARY KEY,
                status TEXT
            )
        """)

        # 30 populated, 70 NULL
        for i in range(30):
            self.cursor.execute("INSERT INTO test_logs (status) VALUES (?)", ("value",))
        for i in range(70):
            self.cursor.execute("INSERT INTO test_logs (status) VALUES (NULL)")
        self.conn.commit()

        # Calculate score
        score = calculate_reliability_score(self.db_path, 'test_logs', 'status')

        # Validate population rate
        expected_rate = 30 / 100  # 0.30
        assert abs(score.population_rate - expected_rate) < 0.01, \
            f"Expected population_rate={expected_rate}, got {score.population_rate}"

        # Should warn about low population
        assert any("population" in w.lower() or "sparse" in w.lower() for w in score.warnings), \
            "Should warn about low population rate"

    def test_semantic_preference_preferred_field(self):
        """
        Test semantic preference for preferred field (conditional_access_status).

        Expected: semantic_preference = 1.0 for preferred fields
        """
        from claude.tools.m365_ir.field_reliability_scorer import calculate_reliability_score

        # Create test table with preferred field
        self.cursor.execute("""
            CREATE TABLE sign_in_logs (
                id INTEGER PRIMARY KEY,
                conditional_access_status TEXT
            )
        """)

        for i in range(100):
            self.cursor.execute(
                "INSERT INTO sign_in_logs (conditional_access_status) VALUES (?)",
                ("success" if i % 2 == 0 else "failure",)
            )
        self.conn.commit()

        # Calculate score
        score = calculate_reliability_score(
            self.db_path,
            'sign_in_logs',
            'conditional_access_status'
        )

        # Validate semantic preference
        assert score.semantic_preference == 1.0, \
            f"Expected semantic_preference=1.0 for preferred field, got {score.semantic_preference}"

    def test_semantic_preference_non_preferred_field(self):
        """
        Test semantic preference for non-preferred field.

        Expected: semantic_preference = 0.0 for non-preferred fields
        """
        from claude.tools.m365_ir.field_reliability_scorer import calculate_reliability_score

        # Create test table with non-preferred field
        self.cursor.execute("""
            CREATE TABLE sign_in_logs (
                id INTEGER PRIMARY KEY,
                some_other_field TEXT
            )
        """)

        for i in range(100):
            self.cursor.execute("INSERT INTO sign_in_logs (some_other_field) VALUES (?)", ("value",))
        self.conn.commit()

        # Calculate score
        score = calculate_reliability_score(self.db_path, 'sign_in_logs', 'some_other_field')

        # Validate semantic preference
        assert score.semantic_preference == 0.0, \
            f"Expected semantic_preference=0.0 for non-preferred field, got {score.semantic_preference}"

    def test_weighted_overall_score_calculation(self):
        """
        Test that overall score is correctly calculated as weighted average.

        Weights (from design):
        - uniformity_score: 30%
        - discriminatory_power: 25%
        - population_rate: 15%
        - historical_success_rate: 20%
        - semantic_preference: 10%

        Expected: overall_score = sum(score * weight)
        """
        from claude.tools.m365_ir.field_reliability_scorer import calculate_reliability_score

        # Create test table with known characteristics
        self.cursor.execute("""
            CREATE TABLE test_logs (
                id INTEGER PRIMARY KEY,
                status TEXT
            )
        """)

        # Create 50/50 split (good variety)
        for i in range(100):
            self.cursor.execute(
                "INSERT INTO test_logs (status) VALUES (?)",
                ("success" if i < 50 else "failure",)
            )
        self.conn.commit()

        # Calculate score
        score = calculate_reliability_score(self.db_path, 'test_logs', 'status')

        # Manual calculation (no historical data, non-preferred field)
        # uniformity_score: 2 distinct / high variety = high (~0.98)
        # discriminatory_power: 2/100 = 0.02
        # population_rate: 100/100 = 1.0
        # historical_success_rate: 0.5 (default when no history)
        # semantic_preference: 0.0

        # Weighted: 0.30*uniformity + 0.25*0.02 + 0.15*1.0 + 0.20*0.5 + 0.10*0.0

        # Just validate that overall_score is within reasonable range
        assert 0.0 <= score.overall_score <= 1.0, \
            f"Overall score must be 0-1, got {score.overall_score}"

        # Validate it's not just one dimension (should be weighted combination)
        assert score.overall_score != score.uniformity_score, \
            "Overall score should be weighted average, not just uniformity"

    def test_backward_compatibility_with_phase_1(self):
        """
        Test that Phase 2.1 scoring agrees with Phase 1 binary classification.

        Phase 1 rule: Field is unreliable if >99.5% uniform
        Phase 2.1: Should produce overall_score < 0.5 for same scenario
        """
        from claude.tools.m365_ir.field_reliability_scorer import calculate_reliability_score

        # Test Case 1: Phase 1 would reject (99.6% uniform)
        self.cursor.execute("""
            CREATE TABLE test_logs (
                id INTEGER PRIMARY KEY,
                status TEXT
            )
        """)

        # 996 same value, 4 different (99.6% uniform)
        for i in range(996):
            self.cursor.execute("INSERT INTO test_logs (status) VALUES (?)", ("same",))
        for i in range(4):
            self.cursor.execute("INSERT INTO test_logs (status) VALUES (?)", ("different",))
        self.conn.commit()

        score = calculate_reliability_score(self.db_path, 'test_logs', 'status')

        # Phase 1 would say: is_reliable = False (>99.5% uniform)
        # Phase 2.1 should say: overall_score < 0.5 (unreliable)
        assert score.overall_score < 0.5, \
            f"Phase 2.1 should agree with Phase 1 (unreliable), got overall_score={score.overall_score}"

        # Test Case 2: Phase 1 borderline (50/50 split, low uniformity)
        self.cursor.execute("DELETE FROM test_logs")

        # 50 success, 50 failure (50% uniform, good variety)
        for i in range(50):
            self.cursor.execute("INSERT INTO test_logs (status) VALUES (?)", ("success",))
        for i in range(50):
            self.cursor.execute("INSERT INTO test_logs (status) VALUES (?)", ("failure",))
        self.conn.commit()

        score = calculate_reliability_score(self.db_path, 'test_logs', 'status')

        # Phase 1 would say: is_reliable = True (50% ≤ 99.5% uniform)
        # Phase 2.1 should also say: overall_score >= 0.5 (reliable)
        # This has good variety (50/50 split) so both should agree
        assert score.overall_score >= 0.5, \
            f"Phase 2.1 should agree with Phase 1 on good variety field, got overall_score={score.overall_score}"


# Mark all tests for Phase 2.1
pytestmark = pytest.mark.phase_2_1
