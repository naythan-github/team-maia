"""
Test Suite for Automated Quality Scorer

Tests rubric-based evaluation across all criteria.
"""

import sys
import tempfile
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from claude.tools.sre.automated_quality_scorer import (
    AutomatedQualityScorer, QualityRubric, CriteriaScore
)


class TestRunner:
    """Simple test runner"""

    def __init__(self):
        self.passed = 0
        self.total = 0

    def assert_true(self, condition, message):
        self.total += 1
        if condition:
            print(f"✅ {message}")
            self.passed += 1
        else:
            print(f"❌ {message}")

    def assert_greater(self, actual, minimum, message):
        self.total += 1
        if actual > minimum:
            print(f"✅ {message} (value: {actual:.1f})")
            self.passed += 1
        else:
            print(f"❌ {message} - Expected > {minimum}, got {actual}")

    def assert_less(self, actual, maximum, message):
        self.total += 1
        if actual < maximum:
            print(f"✅ {message} (value: {actual:.1f})")
            self.passed += 1
        else:
            print(f"❌ {message} - Expected < {maximum}, got {actual}")

    def assert_in_range(self, actual, min_val, max_val, message):
        self.total += 1
        if min_val <= actual <= max_val:
            print(f"✅ {message} (value: {actual:.1f})")
            self.passed += 1
        else:
            print(f"❌ {message} - Expected {min_val}-{max_val}, got {actual}")

    def summary(self):
        print(f"\n{'='*60}")
        print(f"Test Results: {self.passed}/{self.total} passed")
        if self.passed == self.total:
            print("✅ All tests passed!")
        else:
            print(f"❌ {self.total - self.passed} tests failed")
        print(f"{'='*60}\n")


def test_perfect_response():
    """Test 1: Perfect response scores highly"""
    print("\n" + "="*60)
    print("Test 1: Perfect Response Scoring")
    print("="*60)

    runner = TestRunner()

    response_data = {
        "status": "completed",
        "requirements": ["req1", "req2", "req3"],
        "addressed_requirements": ["req1", "req2", "req3"],
        "validation_performed": True,
        "edge_cases_considered": True,
        "tool_calls": [{"tool": "bash", "params": {"command": "ls"}}],
        "tools_required": True,
        "correct_tool_calls": 1,
        "parameters_appropriate": True,
        "redundant_calls": 0,
        "planning_shown": True,
        "systematic_approach": True,
        "subtasks": ["subtask1", "subtask2", "subtask3"],
        "edge_cases_identified": ["edge1", "edge2"],
        "response_text": "This is a clear, helpful response with appropriate detail. " * 10,
        "explanations_provided": True,
        "examples_included": True,
        "professional_tone": True,
        "tokens_used": 400,
        "tokens_expected": 500,
        "execution_time_ms": 2000,
        "redundant_operations": False
    }

    with tempfile.TemporaryDirectory() as temp_dir:
        scorer = AutomatedQualityScorer(Path(temp_dir))
        score = scorer.evaluate_response(response_data, "test_agent", "response_1")

        runner.assert_greater(score.overall_score, 85, "Perfect response scores > 85")
        runner.assert_greater(score.task_completion_score, 90, "Task completion > 90")
        runner.assert_greater(score.tool_accuracy_score, 90, "Tool accuracy > 90")
        runner.assert_greater(score.decomposition_score, 80, "Decomposition > 80")
        runner.assert_greater(score.response_quality_score, 80, "Response quality > 80")

    runner.summary()
    return runner.passed == runner.total


def test_partial_completion():
    """Test 2: Partial completion scores moderately"""
    print("\n" + "="*60)
    print("Test 2: Partial Completion Scoring")
    print("="*60)

    runner = TestRunner()

    response_data = {
        "status": "partial",
        "requirements": ["req1", "req2", "req3"],
        "addressed_requirements": ["req1", "req2"],  # Only 2/3
        "validation_performed": False,
        "tool_calls": [],
        "tools_required": False,
        "planning_shown": False,
        "response_text": "Brief response.",
        "professional_tone": True,
        "tokens_used": 100,
        "execution_time_ms": 1000
    }

    with tempfile.TemporaryDirectory() as temp_dir:
        scorer = AutomatedQualityScorer(Path(temp_dir))
        score = scorer.evaluate_response(response_data, "test_agent", "response_2")

        runner.assert_in_range(score.overall_score, 40, 70, "Partial completion scores 40-70")
        runner.assert_less(score.task_completion_score, 70, "Task completion < 70")
        runner.assert_less(score.decomposition_score, 50, "Decomposition < 50")

    runner.summary()
    return runner.passed == runner.total


def test_poor_tool_usage():
    """Test 3: Poor tool usage is penalized"""
    print("\n" + "="*60)
    print("Test 3: Poor Tool Usage Penalty")
    print("="*60)

    runner = TestRunner()

    response_data = {
        "status": "completed",
        "requirements": ["req1"],
        "addressed_requirements": ["req1"],
        "tool_calls": [
            {"tool": "bash", "params": {}},
            {"tool": "wrong_tool", "params": {}},
            {"tool": "bash", "params": {}}  # Redundant
        ],
        "tools_required": True,
        "correct_tool_calls": 1,  # Only 1/3 correct
        "parameters_appropriate": False,
        "redundant_calls": 1,
        "response_text": "Response with poor tool usage.",
        "professional_tone": True,
        "tokens_used": 200,
        "execution_time_ms": 3000
    }

    with tempfile.TemporaryDirectory() as temp_dir:
        scorer = AutomatedQualityScorer(Path(temp_dir))
        score = scorer.evaluate_response(response_data, "test_agent", "response_3")

        runner.assert_less(score.tool_accuracy_score, 50, "Tool accuracy < 50 for poor usage")
        runner.assert_less(score.overall_score, 75, "Overall score penalized for poor tools")

    runner.summary()
    return runner.passed == runner.total


def test_rubric_weights():
    """Test 4: Rubric weights sum to 1.0"""
    print("\n" + "="*60)
    print("Test 4: Rubric Weight Validation")
    print("="*60)

    runner = TestRunner()

    rubric = QualityRubric()
    total_weight = sum(rubric.weights.values())

    runner.assert_in_range(total_weight, 0.99, 1.01, "Weights sum to 1.0")
    runner.assert_true(rubric.weights["task_completion"] == 0.40, "Task completion weight = 40%")
    runner.assert_true(rubric.weights["tool_accuracy"] == 0.20, "Tool accuracy weight = 20%")
    runner.assert_true(rubric.weights["decomposition"] == 0.20, "Decomposition weight = 20%")
    runner.assert_true(rubric.weights["response_quality"] == 0.15, "Response quality weight = 15%")
    runner.assert_true(rubric.weights["efficiency"] == 0.05, "Efficiency weight = 5%")

    runner.summary()
    return runner.passed == runner.total


def test_score_persistence():
    """Test 5: Scores are saved and retrievable"""
    print("\n" + "="*60)
    print("Test 5: Score Persistence")
    print("="*60)

    runner = TestRunner()

    response_data = {
        "status": "completed",
        "requirements": ["req1"],
        "addressed_requirements": ["req1"],
        "response_text": "Test response.",
        "professional_tone": True,
        "tokens_used": 100,
        "execution_time_ms": 1000
    }

    with tempfile.TemporaryDirectory() as temp_dir:
        scorer = AutomatedQualityScorer(Path(temp_dir))

        # Score response
        score1 = scorer.evaluate_response(response_data, "test_agent", "response_persist")

        # Check file exists
        score_file = Path(temp_dir) / "response_persist.json"
        runner.assert_true(score_file.exists(), "Score file created")

        # Retrieve scores
        agent_scores = scorer.get_agent_scores("test_agent")
        runner.assert_true(len(agent_scores) > 0, "Scores retrievable")
        runner.assert_true(agent_scores[0]["overall_score"] == score1.overall_score, "Score matches")

    runner.summary()
    return runner.passed == runner.total


def test_average_score_calculation():
    """Test 6: Average score calculation"""
    print("\n" + "="*60)
    print("Test 6: Average Score Calculation")
    print("="*60)

    runner = TestRunner()

    with tempfile.TemporaryDirectory() as temp_dir:
        scorer = AutomatedQualityScorer(Path(temp_dir))

        # Create multiple scores
        for i in range(5):
            response_data = {
                "status": "completed",
                "requirements": ["req1"],
                "addressed_requirements": ["req1"],
                "validation_performed": i % 2 == 0,  # Vary quality
                "response_text": "Test response.",
                "professional_tone": True,
                "tokens_used": 100,
                "execution_time_ms": 1000
            }
            scorer.evaluate_response(response_data, "test_agent", f"response_{i}")

        # Calculate average
        avg = scorer.get_average_score("test_agent", days=7)
        runner.assert_greater(avg, 0, "Average score calculated")
        runner.assert_less(avg, 100, "Average score in valid range")

    runner.summary()
    return runner.passed == runner.total


def main():
    """Run all tests"""
    print("🧪" * 30)
    print("AUTOMATED QUALITY SCORER - TEST SUITE")
    print("🧪" * 30)

    tests = [
        test_perfect_response,
        test_partial_completion,
        test_poor_tool_usage,
        test_rubric_weights,
        test_score_persistence,
        test_average_score_calculation
    ]

    results = []
    for test_func in tests:
        result = test_func()
        results.append(result)

    # Final summary
    print("\n" + "📊" * 30)
    print("FINAL TEST SUMMARY")
    print("📊" * 30)

    for i, (test_func, result) in enumerate(zip(tests, results), 1):
        status = "✅ PASSED" if result else "❌ FAILED"
        test_name = test_func.__doc__.split(':')[0].replace(f'Test {i}', '').strip()
        print(f"{status}: {test_name}")

    print("\n" + "="*60)
    passed = sum(results)
    total = len(results)
    print(f"Overall: {passed}/{total} test suites passed")
    if passed == total:
        print("✅ ALL TESTS PASSED - Automated Quality Scorer ready for production!")
    else:
        print(f"❌ {total - passed} test suite(s) failed")
    print("="*60)

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
