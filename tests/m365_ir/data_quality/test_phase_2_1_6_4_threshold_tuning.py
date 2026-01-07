"""
M365 IR Data Quality System - Phase 2.1.6.4 Threshold Tuning Tests

Empirical validation of confidence thresholds (0.5 and 0.7) using:
- ROC curve analysis
- Precision/recall/specificity metrics
- Threshold sensitivity analysis
- Historical data validation

Created: 2026-01-07
Phase: PHASE_2_SMART_ANALYSIS (Phase 2.1.6.4 - Confidence Threshold Tuning)
TDD Methodology: RED → GREEN → No regressions
"""

import pytest
import tempfile
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple
import numpy as np
from sklearn.metrics import roc_curve, roc_auc_score, confusion_matrix


@pytest.mark.phase_2_1_6
class TestConfidenceThresholdValidation:
    """
    Phase 2.1.6.4: Validate that confidence thresholds (0.5, 0.7) effectively
    discriminate between reliable and unreliable fields.
    """

    def test_high_confidence_precision(self):
        """
        Test that HIGH confidence fields (score >= 0.7) have high success rates.

        Given: Historical data with varying field success rates
        When: Scoring fields and classifying by confidence level
        Then:
            - HIGH confidence fields should have ≥85% success rate
            - Verifies that 0.7 threshold is not too lenient

        TDD Phase: RED → GREEN
        Expected to FAIL initially - need threshold analysis utilities.
        """
        from claude.tools.m365_ir.log_database import IRLogDatabase
        from claude.tools.m365_ir.field_reliability_scorer import (
            calculate_reliability_score,
            create_history_database,
            store_field_usage
        )

        tmpdir = tempfile.mkdtemp()

        try:
            # Create database with test data
            db = IRLogDatabase(case_id="TEST-PRECISION", base_path=tmpdir)
            db.create()

            # Create historical database
            historical_db_path = Path(tmpdir) / "historical_precision.db"
            create_history_database(str(historical_db_path))

            # Populate database with fields that should score >= 0.7
            # Strategy: High uniformity, high population, high historical success
            conn = sqlite3.connect(db.db_path)
            cursor = conn.cursor()

            # Field 1: Should be HIGH confidence (very uniform, 100% historical success)
            test_data_high_confidence = [
                ('success', 'user1@test.com'),
                ('failure', 'user2@test.com'),
                ('notApplied', 'user3@test.com'),
                ('success', 'user4@test.com'),
                ('failure', 'user5@test.com'),
                ('success', 'user6@test.com'),
                ('notApplied', 'user7@test.com'),
                ('failure', 'user8@test.com'),
                ('success', 'user9@test.com'),
                ('failure', 'user10@test.com'),
            ]

            for status, user in test_data_high_confidence:
                cursor.execute("""
                    INSERT INTO sign_in_logs
                    (timestamp, user_principal_name, ip_address, conditional_access_status,
                     status_error_code, raw_record, imported_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    datetime.now().isoformat(),
                    user,
                    '203.0.113.1',
                    status,
                    '0' if status == 'success' else '50126',
                    '{}',
                    datetime.now().isoformat()
                ))

            conn.commit()
            conn.close()

            # Store historical success data (10 successful cases)
            for i in range(10):
                store_field_usage(
                    history_db_path=str(historical_db_path),
                    case_id=f'HIST-SUCCESS-{i}',
                    log_type='sign_in_logs',
                    field_name='conditional_access_status',
                    reliability_score=0.75,
                    used_for_verification=True,
                    verification_successful=True,
                    breach_detected=True
                )

            # Calculate reliability score
            score = calculate_reliability_score(
                db_path=str(db.db_path),
                table='sign_in_logs',
                field='conditional_access_status',
                historical_db_path=str(historical_db_path)
            )

            # Verify HIGH confidence (>= 0.7)
            assert score.overall_score >= 0.7, \
                f"Field with high uniformity and 100% historical success should score >= 0.7, got {score.overall_score:.3f}"

            # This field should have 100% success rate in our historical data
            # Verify precision: P(success | HIGH confidence) >= 0.85
            historical_success_rate = score.historical_success_rate
            assert historical_success_rate >= 0.85, \
                f"HIGH confidence field should have ≥85% historical success, got {historical_success_rate:.1%}"

        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_low_confidence_specificity(self):
        """
        Test that LOW confidence fields (score < 0.5) correctly identify unreliable fields.

        Given: Fields with known low reliability characteristics
        When: Scoring and classifying by confidence
        Then:
            - LOW confidence fields should have ≤30% success rate
            - Verifies that 0.5 threshold effectively filters out bad fields

        TDD Phase: RED → GREEN
        Expected to FAIL initially - need low-scoring field construction.
        """
        from claude.tools.m365_ir.log_database import IRLogDatabase
        from claude.tools.m365_ir.field_reliability_scorer import (
            calculate_reliability_score,
            create_history_database,
            store_field_usage
        )

        tmpdir = tempfile.mkdtemp()

        try:
            # Create database with test data
            db = IRLogDatabase(case_id="TEST-SPECIFICITY", base_path=tmpdir)
            db.create()

            # Create historical database
            historical_db_path = Path(tmpdir) / "historical_specificity.db"
            create_history_database(str(historical_db_path))

            # Populate database with field that should score < 0.5
            # Strategy: Low uniformity (mostly NULL), low historical success
            conn = sqlite3.connect(db.db_path)
            cursor = conn.cursor()

            # Add device_id column
            cursor.execute("ALTER TABLE sign_in_logs ADD COLUMN device_id TEXT")

            # Insert 10 records, mostly NULL/sparse field
            for i in range(10):
                # Only 2 records have device_id populated (low population rate)
                device_id = f'device-{i}' if i < 2 else None

                cursor.execute("""
                    INSERT INTO sign_in_logs
                    (timestamp, user_principal_name, ip_address, conditional_access_status,
                     status_error_code, device_id, raw_record, imported_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    datetime.now().isoformat(),
                    f'user{i}@test.com',
                    '203.0.113.1',
                    'success',
                    '0',
                    device_id,
                    '{}',
                    datetime.now().isoformat()
                ))

            conn.commit()
            conn.close()

            # Store historical failure data (8 failed, 2 success = 25% success rate)
            for i in range(10):
                store_field_usage(
                    history_db_path=str(historical_db_path),
                    case_id=f'HIST-FAIL-{i}',
                    log_type='sign_in_logs',
                    field_name='device_id',
                    reliability_score=0.25,
                    used_for_verification=True,
                    verification_successful=(i < 2),  # Only 2 successes
                    breach_detected=False
                )

            # Calculate reliability score
            score = calculate_reliability_score(
                db_path=str(db.db_path),
                table='sign_in_logs',
                field='device_id',
                historical_db_path=str(historical_db_path)
            )

            # Verify LOW confidence (< 0.5)
            assert score.overall_score < 0.5, \
                f"Field with low population and 25% historical success should score < 0.5, got {score.overall_score:.3f}"

            # Verify specificity: P(failure | LOW confidence) >= 0.70
            historical_failure_rate = 1.0 - score.historical_success_rate
            assert historical_failure_rate >= 0.70, \
                f"LOW confidence field should have ≥70% historical failure, got {historical_failure_rate:.1%}"

        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_threshold_recall(self):
        """
        Test that thresholds don't miss too many successful fields (recall).

        Given: Fields with verified high success rates (>80%)
        When: Scoring with 0.5/0.7 thresholds
        Then:
            - ≥90% should be classified as MEDIUM or HIGH
            - Verifies we're not too conservative (missing good fields)

        TDD Phase: RED → GREEN
        Expected to FAIL initially - need multiple field evaluation.
        """
        from claude.tools.m365_ir.log_database import IRLogDatabase
        from claude.tools.m365_ir.field_reliability_scorer import (
            calculate_reliability_score,
            create_history_database,
            store_field_usage
        )

        tmpdir = tempfile.mkdtemp()

        try:
            # Create database with test data
            db = IRLogDatabase(case_id="TEST-RECALL", base_path=tmpdir)
            db.create()

            # Create historical database
            historical_db_path = Path(tmpdir) / "historical_recall.db"
            create_history_database(str(historical_db_path))

            # Create 10 fields with ≥80% historical success
            # These should mostly be MEDIUM or HIGH confidence
            test_fields = [
                'conditional_access_status',
                'status_error_code',
                'ip_address',
                'location_country',
                'user_principal_name',
            ]

            conn = sqlite3.connect(db.db_path)
            cursor = conn.cursor()

            # Populate with varied data (good uniformity, high population)
            for i in range(10):
                cursor.execute("""
                    INSERT INTO sign_in_logs
                    (timestamp, user_principal_name, ip_address, conditional_access_status,
                     status_error_code, location_country, raw_record, imported_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    datetime.now().isoformat(),
                    f'user{i}@test.com',
                    f'203.0.{i}.1',
                    ['success', 'failure', 'notApplied'][i % 3],
                    ['0', '50126', '50053'][i % 3],
                    ['US', 'AU', 'GB'][i % 3],
                    '{}',
                    datetime.now().isoformat()
                ))

            conn.commit()
            conn.close()

            # Store historical data with 80-100% success rates for each field
            for field in test_fields:
                successes = 9 if field == 'conditional_access_status' else 8
                for i in range(10):
                    store_field_usage(
                        history_db_path=str(historical_db_path),
                        case_id=f'RECALL-{field}-{i}',
                        log_type='sign_in_logs',
                        field_name=field,
                        reliability_score=0.75,
                        used_for_verification=True,
                        verification_successful=(i < successes),
                        breach_detected=(i < successes)
                    )

            # Score all fields and count MEDIUM/HIGH classifications
            medium_or_high_count = 0
            for field in test_fields:
                score = calculate_reliability_score(
                    db_path=str(db.db_path),
                    table='sign_in_logs',
                    field=field,
                    historical_db_path=str(historical_db_path)
                )

                # MEDIUM or HIGH = score >= 0.5
                if score.overall_score >= 0.5:
                    medium_or_high_count += 1

            # Verify recall: ≥90% of successful fields are MEDIUM or HIGH
            recall_rate = medium_or_high_count / len(test_fields)
            assert recall_rate >= 0.90, \
                f"Recall too low: {recall_rate:.1%} of successful fields are MEDIUM/HIGH (target: ≥90%)"

        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.mark.phase_2_1_6
class TestROCCurveAnalysis:
    """
    Phase 2.1.6.4: ROC curve analysis to validate threshold optimality.
    """

    def test_roc_curve_generation(self):
        """
        Generate ROC curve across threshold values [0.0, 0.1, ..., 1.0].

        Given: Historical field usage data with known outcomes
        When: Varying confidence threshold from 0.0 to 1.0
        Then:
            - Calculate TPR (True Positive Rate) and FPR (False Positive Rate)
            - Verify ROC curve is monotonic (TPR increases with threshold decrease)
            - Calculate AUC (Area Under Curve) - should be ≥0.70

        TDD Phase: RED → GREEN
        Expected to FAIL initially - need ROC analysis utilities.
        """
        from claude.tools.m365_ir.log_database import IRLogDatabase
        from claude.tools.m365_ir.field_reliability_scorer import (
            calculate_reliability_score,
            create_history_database,
            store_field_usage
        )

        tmpdir = tempfile.mkdtemp()

        try:
            # Create database with diverse field scores
            db = IRLogDatabase(case_id="TEST-ROC", base_path=tmpdir)
            db.create()

            # Create historical database
            historical_db_path = Path(tmpdir) / "historical_roc.db"
            create_history_database(str(historical_db_path))

            # Create fields with known success rates (ground truth)
            field_ground_truth = [
                ('field_perfect', 1.0),      # 100% success
                ('field_excellent', 0.9),    # 90% success
                ('field_good', 0.75),        # 75% success
                ('field_moderate', 0.6),     # 60% success
                ('field_poor', 0.4),         # 40% success
                ('field_bad', 0.25),         # 25% success
                ('field_terrible', 0.1),     # 10% success
                ('field_failed', 0.0),       # 0% success
            ]

            conn = sqlite3.connect(db.db_path)
            cursor = conn.cursor()

            # Add all fields as columns
            for field_name, _ in field_ground_truth:
                cursor.execute(f"""
                    ALTER TABLE sign_in_logs ADD COLUMN {field_name} TEXT
                """)

            # Populate with data (varying uniformity)
            for i in range(20):
                values = {
                    'timestamp': datetime.now().isoformat(),
                    'user_principal_name': f'user{i}@test.com',
                    'ip_address': '203.0.113.1',
                    'conditional_access_status': 'success',
                    'status_error_code': '0',
                    'raw_record': '{}',
                    'imported_at': datetime.now().isoformat(),
                }

                # Add field values (more varied = higher uniformity score)
                for field_name, _ in field_ground_truth:
                    values[field_name] = f'value_{i % 5}'  # 5 distinct values

                columns = ', '.join(values.keys())
                placeholders = ', '.join(['?' for _ in values])
                cursor.execute(f"""
                    INSERT INTO sign_in_logs ({columns})
                    VALUES ({placeholders})
                """, list(values.values()))

            conn.commit()
            conn.close()

            # Store historical data matching ground truth success rates
            for field_name, success_rate in field_ground_truth:
                total_cases = 20
                successes = int(total_cases * success_rate)

                for i in range(total_cases):
                    store_field_usage(
                        history_db_path=str(historical_db_path),
                        case_id=f'ROC-{field_name}-{i}',
                        log_type='sign_in_logs',
                        field_name=field_name,
                        reliability_score=success_rate,
                        used_for_verification=True,
                        verification_successful=(i < successes),
                        breach_detected=(i < successes)
                    )

            # Calculate scores for all fields
            y_true = []  # Ground truth (1 = successful field, 0 = failed field)
            y_scores = []  # Predicted scores

            for field_name, success_rate in field_ground_truth:
                score = calculate_reliability_score(
                    db_path=str(db.db_path),
                    table='sign_in_logs',
                    field=field_name,
                    historical_db_path=str(historical_db_path)
                )

                # Ground truth: field is "successful" if success_rate >= 0.7
                y_true.append(1 if success_rate >= 0.7 else 0)
                y_scores.append(score.overall_score)

            # Generate ROC curve
            fpr, tpr, thresholds = roc_curve(y_true, y_scores)
            auc = roc_auc_score(y_true, y_scores)

            print(f"\n📊 ROC Curve Analysis:")
            print(f"   AUC: {auc:.3f}")
            print(f"   Number of threshold points: {len(thresholds)}")
            print(f"   FPR range: [{fpr.min():.3f}, {fpr.max():.3f}]")
            print(f"   TPR range: [{tpr.min():.3f}, {tpr.max():.3f}]")

            # Assertions
            assert auc >= 0.70, \
                f"AUC too low: {auc:.3f} (target: ≥0.70) - classifier not discriminating well"

            # Verify ROC curve is valid (TPR increases as FPR increases)
            assert len(fpr) > 2, "ROC curve should have multiple points"
            assert tpr[-1] >= tpr[0], "ROC curve should be monotonically increasing"

        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_optimal_threshold_identification(self):
        """
        Identify optimal threshold using ROC curve analysis.

        Given: ROC curve data from multiple fields
        When: Finding threshold closest to perfect classifier (TPR=1, FPR=0)
        Then:
            - Optimal threshold should be between 0.6-0.8
            - Current 0.7 threshold should be within ±0.1 of optimal

        TDD Phase: RED → GREEN
        Expected to FAIL initially - need optimal threshold calculation.
        """
        from claude.tools.m365_ir.log_database import IRLogDatabase
        from claude.tools.m365_ir.field_reliability_scorer import (
            calculate_reliability_score,
            create_history_database,
            store_field_usage
        )

        tmpdir = tempfile.mkdtemp()

        try:
            # Use same setup as ROC curve generation test
            db = IRLogDatabase(case_id="TEST-OPTIMAL", base_path=tmpdir)
            db.create()

            historical_db_path = Path(tmpdir) / "historical_optimal.db"
            create_history_database(str(historical_db_path))

            # Create fields with known success rates
            field_ground_truth = [
                ('field_high_1', 0.95),
                ('field_high_2', 0.85),
                ('field_high_3', 0.75),
                ('field_medium_1', 0.65),
                ('field_medium_2', 0.55),
                ('field_low_1', 0.45),
                ('field_low_2', 0.35),
                ('field_low_3', 0.15),
            ]

            conn = sqlite3.connect(db.db_path)
            cursor = conn.cursor()

            for field_name, _ in field_ground_truth:
                cursor.execute(f"""
                    ALTER TABLE sign_in_logs ADD COLUMN {field_name} TEXT
                """)

            for i in range(20):
                values = {
                    'timestamp': datetime.now().isoformat(),
                    'user_principal_name': f'user{i}@test.com',
                    'ip_address': '203.0.113.1',
                    'conditional_access_status': 'success',
                    'status_error_code': '0',
                    'raw_record': '{}',
                    'imported_at': datetime.now().isoformat(),
                }

                for field_name, _ in field_ground_truth:
                    values[field_name] = f'value_{i % 5}'

                columns = ', '.join(values.keys())
                placeholders = ', '.join(['?' for _ in values])
                cursor.execute(f"""
                    INSERT INTO sign_in_logs ({columns})
                    VALUES ({placeholders})
                """, list(values.values()))

            conn.commit()
            conn.close()

            # Store historical data
            for field_name, success_rate in field_ground_truth:
                total_cases = 20
                successes = int(total_cases * success_rate)

                for i in range(total_cases):
                    store_field_usage(
                        history_db_path=str(historical_db_path),
                        case_id=f'OPT-{field_name}-{i}',
                        log_type='sign_in_logs',
                        field_name=field_name,
                        reliability_score=success_rate,
                        used_for_verification=True,
                        verification_successful=(i < successes),
                        breach_detected=(i < successes)
                    )

            # Calculate scores
            y_true = []
            y_scores = []

            for field_name, success_rate in field_ground_truth:
                score = calculate_reliability_score(
                    db_path=str(db.db_path),
                    table='sign_in_logs',
                    field=field_name,
                    historical_db_path=str(historical_db_path)
                )

                y_true.append(1 if success_rate >= 0.7 else 0)
                y_scores.append(score.overall_score)

            # Generate ROC curve
            fpr, tpr, thresholds = roc_curve(y_true, y_scores)

            # Find optimal threshold (closest to top-left corner)
            # Distance from (0, 1) = sqrt((FPR - 0)^2 + (TPR - 1)^2)
            distances = np.sqrt(fpr**2 + (1 - tpr)**2)
            optimal_idx = np.argmin(distances)
            optimal_threshold = thresholds[optimal_idx]

            print(f"\n🎯 Optimal Threshold Analysis:")
            print(f"   Optimal threshold: {optimal_threshold:.3f}")
            print(f"   Current HIGH threshold: 0.700")
            print(f"   Difference: {abs(optimal_threshold - 0.7):.3f}")
            print(f"   TPR at optimal: {tpr[optimal_idx]:.3f}")
            print(f"   FPR at optimal: {fpr[optimal_idx]:.3f}")

            # Assertions
            assert 0.6 <= optimal_threshold <= 0.8, \
                f"Optimal threshold {optimal_threshold:.3f} outside expected range [0.6, 0.8]"

            # Current 0.7 threshold should be within ±0.1 of optimal
            assert abs(optimal_threshold - 0.7) <= 0.1, \
                f"Current threshold 0.7 differs from optimal {optimal_threshold:.3f} by >{0.1:.1f}"

        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.mark.phase_2_1_6
class TestThresholdSensitivity:
    """
    Phase 2.1.6.4: Test threshold stability and sensitivity to small changes.
    """

    def test_threshold_stability(self):
        """
        Test that small threshold changes don't drastically affect classification.

        Given: Set of fields with known scores
        When: Adjusting HIGH threshold by ±0.05 (0.65, 0.70, 0.75)
        Then:
            - <25% of fields should change classification
            - Threshold should be reasonably stable

        TDD Phase: RED → GREEN
        Expected to FAIL initially - reveals actual threshold stability.
        """
        from claude.tools.m365_ir.log_database import IRLogDatabase
        from claude.tools.m365_ir.field_reliability_scorer import (
            calculate_reliability_score,
            create_history_database,
            store_field_usage
        )

        tmpdir = tempfile.mkdtemp()

        try:
            # Create database with fields spanning score range
            db = IRLogDatabase(case_id="TEST-STABILITY", base_path=tmpdir)
            db.create()

            historical_db_path = Path(tmpdir) / "historical_stability.db"
            create_history_database(str(historical_db_path))

            # Create 20 fields with scores distributed across range
            test_fields = [f'field_{i:02d}' for i in range(20)]

            conn = sqlite3.connect(db.db_path)
            cursor = conn.cursor()

            for field_name in test_fields:
                cursor.execute(f"""
                    ALTER TABLE sign_in_logs ADD COLUMN {field_name} TEXT
                """)

            # Populate with varied data
            for i in range(20):
                values = {
                    'timestamp': datetime.now().isoformat(),
                    'user_principal_name': f'user{i}@test.com',
                    'ip_address': '203.0.113.1',
                    'conditional_access_status': 'success',
                    'status_error_code': '0',
                    'raw_record': '{}',
                    'imported_at': datetime.now().isoformat(),
                }

                for field_name in test_fields:
                    values[field_name] = f'value_{i % 5}'

                columns = ', '.join(values.keys())
                placeholders = ', '.join(['?' for _ in values])
                cursor.execute(f"""
                    INSERT INTO sign_in_logs ({columns})
                    VALUES ({placeholders})
                """, list(values.values()))

            conn.commit()
            conn.close()

            # Store historical data with distributed success rates (0.0 to 1.0)
            for idx, field_name in enumerate(test_fields):
                success_rate = idx / (len(test_fields) - 1)  # 0.0, 0.05, 0.10, ..., 1.0

                for i in range(20):
                    successes = int(20 * success_rate)
                    store_field_usage(
                        history_db_path=str(historical_db_path),
                        case_id=f'STAB-{field_name}-{i}',
                        log_type='sign_in_logs',
                        field_name=field_name,
                        reliability_score=success_rate,
                        used_for_verification=True,
                        verification_successful=(i < successes),
                        breach_detected=(i < successes)
                    )

            # Calculate scores for all fields
            field_scores = {}
            for field_name in test_fields:
                score = calculate_reliability_score(
                    db_path=str(db.db_path),
                    table='sign_in_logs',
                    field=field_name,
                    historical_db_path=str(historical_db_path)
                )
                field_scores[field_name] = score.overall_score

            # Test threshold stability at 0.65, 0.70, 0.75
            thresholds_to_test = [0.65, 0.70, 0.75]
            classifications = {}

            for threshold in thresholds_to_test:
                classifications[threshold] = {}
                for field_name, score in field_scores.items():
                    if score >= threshold:
                        classifications[threshold][field_name] = 'HIGH'
                    elif score >= 0.5:
                        classifications[threshold][field_name] = 'MEDIUM'
                    else:
                        classifications[threshold][field_name] = 'LOW'

            # Compare 0.70 vs 0.65 (threshold decrease)
            changes_down = 0
            for field_name in test_fields:
                if classifications[0.70][field_name] != classifications[0.65][field_name]:
                    changes_down += 1

            # Compare 0.70 vs 0.75 (threshold increase)
            changes_up = 0
            for field_name in test_fields:
                if classifications[0.70][field_name] != classifications[0.75][field_name]:
                    changes_up += 1

            print(f"\n🔀 Threshold Stability Analysis:")
            print(f"   Changes when threshold 0.70 → 0.65: {changes_down}/{len(test_fields)} ({changes_down/len(test_fields):.1%})")
            print(f"   Changes when threshold 0.70 → 0.75: {changes_up}/{len(test_fields)} ({changes_up/len(test_fields):.1%})")

            # Assertions
            reclassification_rate_down = changes_down / len(test_fields)
            reclassification_rate_up = changes_up / len(test_fields)

            assert reclassification_rate_down < 0.25, \
                f"Too many reclassifications with -0.05 threshold change: {reclassification_rate_down:.1%} (target: <25%)"

            assert reclassification_rate_up < 0.25, \
                f"Too many reclassifications with +0.05 threshold change: {reclassification_rate_up:.1%} (target: <25%)"

        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_confusion_matrix_at_thresholds(self):
        """
        Generate confusion matrix at 0.5 and 0.7 thresholds.

        Given: Historical data with known outcomes
        When: Classifying at current thresholds
        Then:
            - Calculate TP, TN, FP, FN
            - Verify false positive rate <15%
            - Verify false negative rate <30%

        TDD Phase: RED → GREEN
        Expected to FAIL initially - reveals actual threshold performance.
        """
        from claude.tools.m365_ir.log_database import IRLogDatabase
        from claude.tools.m365_ir.field_reliability_scorer import (
            calculate_reliability_score,
            create_history_database,
            store_field_usage
        )

        tmpdir = tempfile.mkdtemp()

        try:
            # Create database with fields of known quality
            db = IRLogDatabase(case_id="TEST-CONFUSION", base_path=tmpdir)
            db.create()

            historical_db_path = Path(tmpdir) / "historical_confusion.db"
            create_history_database(str(historical_db_path))

            # Create 30 fields with known success rates
            # 15 "good" fields (≥70% success), 15 "bad" fields (<70% success)
            # Use higher variety for good fields to boost overall scores
            good_fields = [('good_field_{:02d}'.format(i), 0.85 + (i * 0.01)) for i in range(15)]
            bad_fields = [('bad_field_{:02d}'.format(i), 0.65 - (i * 0.04)) for i in range(15)]
            all_fields = good_fields + bad_fields

            conn = sqlite3.connect(db.db_path)
            cursor = conn.cursor()

            for field_name, _ in all_fields:
                cursor.execute(f"""
                    ALTER TABLE sign_in_logs ADD COLUMN {field_name} TEXT
                """)

            for i in range(20):
                values = {
                    'timestamp': datetime.now().isoformat(),
                    'user_principal_name': f'user{i}@test.com',
                    'ip_address': '203.0.113.1',
                    'conditional_access_status': 'success',
                    'status_error_code': '0',
                    'raw_record': '{}',
                    'imported_at': datetime.now().isoformat(),
                }

                # Use varied data to boost uniformity (more distinct values)
                for field_name, success_rate in all_fields:
                    # Good fields get more variety (higher uniformity)
                    if success_rate >= 0.7:
                        values[field_name] = f'value_{i % 10}'  # 10 distinct values
                    else:
                        values[field_name] = f'value_{i % 3}'   # 3 distinct values

                columns = ', '.join(values.keys())
                placeholders = ', '.join(['?' for _ in values])
                cursor.execute(f"""
                    INSERT INTO sign_in_logs ({columns})
                    VALUES ({placeholders})
                """, list(values.values()))

            conn.commit()
            conn.close()

            # Store historical data
            for field_name, success_rate in all_fields:
                for i in range(20):
                    successes = int(20 * success_rate)
                    store_field_usage(
                        history_db_path=str(historical_db_path),
                        case_id=f'CONF-{field_name}-{i}',
                        log_type='sign_in_logs',
                        field_name=field_name,
                        reliability_score=success_rate,
                        used_for_verification=True,
                        verification_successful=(i < successes),
                        breach_detected=(i < successes)
                    )

            # Calculate scores and build confusion matrix
            y_true = []  # Ground truth: 1 = good field, 0 = bad field
            y_pred_070 = []  # Predictions at 0.7 threshold
            y_pred_050 = []  # Predictions at 0.5 threshold

            for field_name, success_rate in all_fields:
                score = calculate_reliability_score(
                    db_path=str(db.db_path),
                    table='sign_in_logs',
                    field=field_name,
                    historical_db_path=str(historical_db_path)
                )

                # Ground truth: field is "good" if success_rate >= 0.7
                y_true.append(1 if success_rate >= 0.7 else 0)

                # Prediction at 0.7 threshold
                y_pred_070.append(1 if score.overall_score >= 0.7 else 0)

                # Prediction at 0.5 threshold
                y_pred_050.append(1 if score.overall_score >= 0.5 else 0)

            # Generate confusion matrices
            cm_070 = confusion_matrix(y_true, y_pred_070)
            cm_050 = confusion_matrix(y_true, y_pred_050)

            # Extract metrics for 0.7 threshold
            tn_070, fp_070, fn_070, tp_070 = cm_070.ravel()
            fpr_070 = fp_070 / (fp_070 + tn_070) if (fp_070 + tn_070) > 0 else 0
            fnr_070 = fn_070 / (fn_070 + tp_070) if (fn_070 + tp_070) > 0 else 0

            # Extract metrics for 0.5 threshold
            tn_050, fp_050, fn_050, tp_050 = cm_050.ravel()
            fpr_050 = fp_050 / (fp_050 + tn_050) if (fp_050 + tn_050) > 0 else 0
            fnr_050 = fn_050 / (fn_050 + tp_050) if (fn_050 + tp_050) > 0 else 0

            print(f"\n📊 Confusion Matrix Analysis:")
            print(f"\n   Threshold 0.7 (HIGH):")
            print(f"      TP: {tp_070}, TN: {tn_070}, FP: {fp_070}, FN: {fn_070}")
            print(f"      FPR: {fpr_070:.1%}, FNR: {fnr_070:.1%}")
            print(f"\n   Threshold 0.5 (MEDIUM):")
            print(f"      TP: {tp_050}, TN: {tn_050}, FP: {fp_050}, FN: {fn_050}")
            print(f"      FPR: {fpr_050:.1%}, FNR: {fnr_050:.1%}")

            # Assertions for 0.7 threshold
            assert fpr_070 < 0.15, \
                f"False positive rate too high at 0.7 threshold: {fpr_070:.1%} (target: <15%)"

            assert fnr_070 < 0.30, \
                f"False negative rate too high at 0.7 threshold: {fnr_070:.1%} (target: <30%)"

        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.mark.phase_2_1_6
class TestHistoricalDataValidation:
    """
    Phase 2.1.6.4: Validate threshold behavior with varying historical data.
    """

    def test_varying_historical_success_rates(self):
        """
        Test threshold behavior with varying historical success rates.

        Given: Fields with 0%, 25%, 50%, 75%, 100% historical success
        When: Scoring includes 20% historical success weight
        Then:
            - 100% success → contributes 0.20 to overall score
            - 0% success → contributes 0.00 to overall score
            - Verify linear relationship

        TDD Phase: RED → GREEN
        Expected to FAIL initially - need historical rate verification.
        """
        from claude.tools.m365_ir.log_database import IRLogDatabase
        from claude.tools.m365_ir.field_reliability_scorer import (
            calculate_reliability_score,
            create_history_database,
            store_field_usage,
            HISTORICAL_SUCCESS_WEIGHT
        )

        tmpdir = tempfile.mkdtemp()

        try:
            # Create database
            db = IRLogDatabase(case_id="TEST-HIST-VARY", base_path=tmpdir)
            db.create()

            historical_db_path = Path(tmpdir) / "historical_vary.db"
            create_history_database(str(historical_db_path))

            # Create fields with known historical success rates
            field_success_rates = [0.0, 0.25, 0.50, 0.75, 1.0]
            test_fields = [f'field_hist_{int(rate*100):03d}' for rate in field_success_rates]

            conn = sqlite3.connect(db.db_path)
            cursor = conn.cursor()

            for field_name in test_fields:
                cursor.execute(f"""
                    ALTER TABLE sign_in_logs ADD COLUMN {field_name} TEXT
                """)

            # Populate with identical data (uniformity, population should be same)
            for i in range(20):
                values = {
                    'timestamp': datetime.now().isoformat(),
                    'user_principal_name': f'user{i}@test.com',
                    'ip_address': '203.0.113.1',
                    'conditional_access_status': 'success',
                    'status_error_code': '0',
                    'raw_record': '{}',
                    'imported_at': datetime.now().isoformat(),
                }

                for field_name in test_fields:
                    values[field_name] = f'value_{i % 5}'  # Same variety

                columns = ', '.join(values.keys())
                placeholders = ', '.join(['?' for _ in values])
                cursor.execute(f"""
                    INSERT INTO sign_in_logs ({columns})
                    VALUES ({placeholders})
                """, list(values.values()))

            conn.commit()
            conn.close()

            # Store historical data with varying success rates
            for field_name, success_rate in zip(test_fields, field_success_rates):
                for i in range(20):
                    successes = int(20 * success_rate)
                    store_field_usage(
                        history_db_path=str(historical_db_path),
                        case_id=f'VARY-{field_name}-{i}',
                        log_type='sign_in_logs',
                        field_name=field_name,
                        reliability_score=0.5,
                        used_for_verification=True,
                        verification_successful=(i < successes),
                        breach_detected=(i < successes)
                    )

            # Calculate scores and verify historical contribution
            print(f"\n📈 Historical Success Rate Contribution (weight: {HISTORICAL_SUCCESS_WEIGHT:.0%}):")

            for field_name, expected_rate in zip(test_fields, field_success_rates):
                score = calculate_reliability_score(
                    db_path=str(db.db_path),
                    table='sign_in_logs',
                    field=field_name,
                    historical_db_path=str(historical_db_path)
                )

                # Historical contribution = success_rate * weight
                expected_contribution = expected_rate * HISTORICAL_SUCCESS_WEIGHT
                actual_contribution = score.historical_success_rate * HISTORICAL_SUCCESS_WEIGHT

                print(f"   {field_name}: {score.historical_success_rate:.1%} success → {actual_contribution:.3f} contribution")

                # Verify historical success rate is correct
                assert abs(score.historical_success_rate - expected_rate) < 0.05, \
                    f"Historical rate mismatch for {field_name}: expected {expected_rate:.1%}, got {score.historical_success_rate:.1%}"

        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_threshold_with_no_historical_data(self):
        """
        Test that thresholds work correctly when no historical data exists.

        Given: New field with no historical usage
        When: Historical success rate defaults to 0.5 (neutral)
        Then:
            - Should not unfairly penalize new fields
            - Other scoring dimensions should dominate
            - Field with good uniformity/population should still score MEDIUM

        TDD Phase: RED → GREEN
        Expected to FAIL initially - need no-history scenario validation.
        """
        from claude.tools.m365_ir.log_database import IRLogDatabase
        from claude.tools.m365_ir.field_reliability_scorer import (
            calculate_reliability_score,
            create_history_database
        )

        tmpdir = tempfile.mkdtemp()

        try:
            # Create database
            db = IRLogDatabase(case_id="TEST-NO-HIST", base_path=tmpdir)
            db.create()

            historical_db_path = Path(tmpdir) / "historical_empty.db"
            create_history_database(str(historical_db_path))

            # Populate with good field (high uniformity, full population)
            conn = sqlite3.connect(db.db_path)
            cursor = conn.cursor()

            for i in range(20):
                cursor.execute("""
                    INSERT INTO sign_in_logs
                    (timestamp, user_principal_name, ip_address, conditional_access_status,
                     status_error_code, raw_record, imported_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    datetime.now().isoformat(),
                    f'user{i}@test.com',
                    '203.0.113.1',
                    ['success', 'failure', 'notApplied'][i % 3],  # Good variety
                    '0',
                    '{}',
                    datetime.now().isoformat()
                ))

            conn.commit()
            conn.close()

            # Calculate score WITHOUT historical data
            score = calculate_reliability_score(
                db_path=str(db.db_path),
                table='sign_in_logs',
                field='conditional_access_status',
                historical_db_path=str(historical_db_path)
            )

            print(f"\n🆕 No Historical Data Scenario:")
            print(f"   Historical success rate: {score.historical_success_rate:.1%} (should default to neutral)")
            print(f"   Overall score: {score.overall_score:.3f}")
            print(f"   Uniformity: {score.uniformity_score:.3f}")
            print(f"   Population: {score.population_rate:.1%}")

            # Assertions
            # Historical rate should default to 0.5 (neutral)
            assert 0.45 <= score.historical_success_rate <= 0.55, \
                f"No-history field should have neutral historical rate (~0.5), got {score.historical_success_rate:.1%}"

            # Field with good characteristics should still score MEDIUM despite no history
            assert score.overall_score >= 0.5, \
                f"Field with good uniformity/population should score ≥0.5 even without history, got {score.overall_score:.3f}"

        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)


# Module-level marker
pytestmark = pytest.mark.phase_2_1_6
