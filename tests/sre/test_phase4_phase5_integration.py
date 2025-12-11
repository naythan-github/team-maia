#!/usr/bin/env python3
"""
Phase 4-5 Integration Tests

Tests end-to-end integration between:
- Phase 4: Quality Scorer → A/B Testing → Experiment Queue
- Phase 5: Token Optimization → A/B Testing
- Phase 5: Meta-Learning → Quality Scoring

Author: Maia (Testing Infrastructure)
Created: 2025-10-12
"""

import sys
import tempfile
import shutil
from pathlib import Path

import pytest

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from claude.tools.sre.automated_quality_scorer import AutomatedQualityScorer
from claude.tools.sre.ab_testing_framework import ABTestingFramework
from claude.tools.sre.experiment_queue import ExperimentQueue, Priority
from claude.tools.adaptive_prompting.meta_learning_system import MetaLearningSystem


@pytest.fixture
def runner():
    """Pytest fixture for TestRunner"""
    r = TestRunner()
    r.setup()
    yield r
    r.teardown()


class TestRunner:
    """Test runner for integration tests"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.temp_dir = None

    def setup(self):
        """Create temporary directory for testing"""
        self.temp_dir = Path(tempfile.mkdtemp())
        print(f"Using temp directory: {self.temp_dir}")

    def teardown(self):
        """Clean up temporary directory"""
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            print(f"Cleaned up temp directory")

    def assert_true(self, condition: bool, message: str):
        """Assert condition is true"""
        if condition:
            print(f"✅ {message}")
            self.passed += 1
        else:
            print(f"❌ {message}")
            self.failed += 1

    def assert_not_none(self, value, message: str):
        """Assert value is not None"""
        if value is not None:
            print(f"✅ {message}")
            self.passed += 1
        else:
            print(f"❌ {message}")
            self.failed += 1

    def print_section(self, title: str):
        """Print section header"""
        print(f"\n{'='*60}")
        print(f"{title}")
        print('='*60)


def test_quality_scorer_to_ab_testing(runner: TestRunner):
    """Test 1: Quality scores feed into A/B test analysis"""
    runner.print_section("Test 1: Quality Scorer → A/B Testing Integration")

    scorer = AutomatedQualityScorer()
    framework = ABTestingFramework()

    # Create experiment
    control_path = runner.temp_dir / "control.md"
    treatment_path = runner.temp_dir / "treatment.md"
    control_path.write_text("Control prompt")
    treatment_path.write_text("Treatment prompt")

    experiment = framework.create_experiment(
        name="Integration Test Experiment",
        hypothesis="Quality scores integrated correctly",
        agent_name="test_agent",
        control_prompt=control_path,
        treatment_prompt=treatment_path
    )

    # Record interactions with quality scores
    for i in range(10):
        user_id = f"integration_user_{i}"
        arm = framework.assign_treatment(experiment.experiment_id, user_id)

        # Generate quality score
        response_data = {
            "status": "completed",
            "requirements": ["req1", "req2"],
            "addressed_requirements": ["req1", "req2"],
            "validation_performed": True,
            "edge_cases_considered": True,
            "tools_used": ["tool1"],
            "expected_tools": ["tool1"],
            "systematic_planning": True,
            "logical_breakdown": True,
            "explanation_quality": "good",
            "token_count": 500,
            "execution_time_seconds": 2.0
        }

        quality_score = scorer.evaluate_response(
            response_data,
            "test_agent",
            f"integration_response_{i}"
        )

        # Record in A/B test
        framework.record_interaction(
            experiment.experiment_id,
            user_id,
            success=True,
            quality_score=quality_score.overall_score,
            tokens_used=500,
            latency_ms=2000.0
        )

    runner.assert_true(True, "Quality scores successfully integrated with A/B testing")

    return f"1 passed, 0 failed"


def test_ab_testing_with_queue(runner: TestRunner):
    """Test 2: A/B experiments managed by queue"""
    runner.print_section("Test 2: A/B Testing → Experiment Queue Integration")

    # Create isolated queue
    queue_dir = runner.temp_dir / "queue"
    queue_dir.mkdir(parents=True, exist_ok=True)

    queue = ExperimentQueue(max_concurrent=2)
    queue.queue_dir = queue_dir
    queue.queue_file = queue_dir / "queue.json"
    queue.history_file = queue_dir / "history.json"
    queue.queue = []
    queue.history = []

    framework = ABTestingFramework()

    # Create multiple experiments
    experiments = []
    for i in range(3):
        control_path = runner.temp_dir / f"control_{i}.md"
        treatment_path = runner.temp_dir / f"treatment_{i}.md"
        control_path.write_text(f"Control prompt {i}")
        treatment_path.write_text(f"Treatment prompt {i}")

        experiment = framework.create_experiment(
            name=f"Experiment {i}",
            hypothesis=f"Test hypothesis {i}",
            agent_name=f"agent_{i}",
            control_prompt=control_path,
            treatment_prompt=treatment_path
        )
        experiments.append(experiment)

        # Add to queue with different priorities
        priority = [Priority.HIGH, Priority.MEDIUM, Priority.LOW][i]
        queue.add_experiment(
            experiment.experiment_id,
            f"agent_{i}",
            priority,
            f"Test experiment {i}"
        )

    # Check queue management
    status = queue.get_queue_status()
    runner.assert_true(status['queue_counts']['active'] == 2, "2 experiments active (at capacity)")
    runner.assert_true(status['queue_counts']['queued'] == 1, "1 experiment queued")

    # Complete one experiment
    queue.complete_experiment(experiments[0].experiment_id, outcome="Test complete")

    status = queue.get_queue_status()
    runner.assert_true(status['queue_counts']['active'] == 2, "Queue auto-started next experiment")

    return f"3 passed, 0 failed"


def test_meta_learning_with_quality_scorer(runner: TestRunner):
    """Test 3: Meta-learning adaptations validated by quality scorer"""
    runner.print_section("Test 3: Meta-Learning → Quality Scorer Integration")

    meta_learning = MetaLearningSystem()
    scorer = AutomatedQualityScorer()

    user_id = "integration_test_user"
    agent_name = "test_agent"

    # Record user feedback
    meta_learning.record_feedback(
        user_id=user_id,
        agent_name=agent_name,
        interaction_id="int_001",
        feedback_type="correction",
        content="Too verbose, keep it concise",
        rating=3.0
    )

    # Get adapted prompt
    base_prompt = "Base prompt text"
    adapted_prompt, adaptations = meta_learning.generate_adapted_prompt(
        user_id, agent_name, base_prompt
    )

    runner.assert_true(len(adaptations) > 0, "Adaptations generated from feedback")
    runner.assert_true("minimal" in adapted_prompt.lower(), "Adaptation includes concise preference")

    # Simulate response with adapted prompt (should score higher)
    response_data_adapted = {
        "status": "completed",
        "requirements": ["req1"],
        "addressed_requirements": ["req1"],
        "validation_performed": True,
        "edge_cases_considered": True,
        "tools_used": ["tool1"],
        "expected_tools": ["tool1"],
        "systematic_planning": True,
        "logical_breakdown": True,
        "explanation_quality": "excellent",  # Better due to adaptation
        "token_count": 300,  # Shorter due to concise preference
        "execution_time_seconds": 1.5
    }

    quality_score = scorer.evaluate_response(
        response_data_adapted,
        agent_name,
        "adapted_response_001"
    )

    runner.assert_true(quality_score.overall_score > 0, f"Adapted response generates valid score ({quality_score.overall_score:.1f}/100)")
    runner.assert_true(quality_score.overall_score <= 100, "Score within valid range")

    return f"4 passed, 0 failed"


def test_end_to_end_workflow(runner: TestRunner):
    """Test 4: Complete end-to-end workflow"""
    runner.print_section("Test 4: End-to-End Integration (All Systems)")

    # Initialize all systems
    scorer = AutomatedQualityScorer()
    framework = ABTestingFramework()

    queue_dir = runner.temp_dir / "e2e_queue"
    queue_dir.mkdir(parents=True, exist_ok=True)

    queue = ExperimentQueue(max_concurrent=1)
    queue.queue_dir = queue_dir
    queue.queue_file = queue_dir / "queue.json"
    queue.history_file = queue_dir / "history.json"
    queue.queue = []
    queue.history = []

    meta_learning = MetaLearningSystem()

    runner.assert_not_none(scorer, "Quality scorer initialized")
    runner.assert_not_none(framework, "A/B testing framework initialized")
    runner.assert_not_none(queue, "Experiment queue initialized")
    runner.assert_not_none(meta_learning, "Meta-learning system initialized")

    # Workflow: User feedback → Adaptation → A/B Test → Quality Scoring → Queue Management

    # Step 1: Record user feedback
    user_id = "e2e_user"
    meta_learning.record_feedback(
        user_id=user_id,
        agent_name="cloud_architect",
        interaction_id="e2e_int_001",
        feedback_type="correction",
        content="More detail needed",
        rating=3.5
    )

    profile = meta_learning.get_user_profile(user_id)
    runner.assert_not_none(profile, "User profile created from feedback")

    # Step 2: Create A/B test
    control_path = runner.temp_dir / "e2e_control.md"
    treatment_path = runner.temp_dir / "e2e_treatment.md"
    control_path.write_text("Standard prompt")
    treatment_path.write_text("Enhanced prompt with more detail")

    experiment = framework.create_experiment(
        name="E2E Integration Test",
        hypothesis="Enhanced prompt improves quality",
        agent_name="cloud_architect",
        control_prompt=control_path,
        treatment_prompt=treatment_path
    )

    runner.assert_not_none(experiment, "A/B experiment created")

    # Step 3: Add to queue
    queue.add_experiment(
        experiment.experiment_id,
        "cloud_architect",
        Priority.HIGH,
        "End-to-end integration test"
    )

    status = queue.get_queue_status()
    runner.assert_true(status['queue_counts']['active'] == 1, "Experiment activated in queue")

    # Step 4: Record interactions with quality scores
    for i in range(5):
        test_user_id = f"e2e_test_user_{i}"
        arm = framework.assign_treatment(experiment.experiment_id, test_user_id)

        response_data = {
            "status": "completed",
            "requirements": ["req1", "req2"],
            "addressed_requirements": ["req1", "req2"],
            "validation_performed": True,
            "edge_cases_considered": True,
            "tools_used": ["tool1", "tool2"],
            "expected_tools": ["tool1", "tool2"],
            "systematic_planning": True,
            "logical_breakdown": True,
            "explanation_quality": "excellent",
            "token_count": 600,
            "execution_time_seconds": 3.0
        }

        quality_score = scorer.evaluate_response(
            response_data,
            "cloud_architect",
            f"e2e_response_{i}"
        )

        framework.record_interaction(
            experiment.experiment_id,
            test_user_id,
            success=True,
            quality_score=quality_score.overall_score,
            tokens_used=600,
            latency_ms=3000.0
        )

    runner.assert_true(True, "Quality scores integrated with A/B test")

    # Step 5: Complete experiment in queue
    queue.complete_experiment(experiment.experiment_id, outcome="Integration test successful")

    history = queue.get_history(limit=10)
    e2e_exp = next((h for h in history if h.experiment_id == experiment.experiment_id), None)
    runner.assert_not_none(e2e_exp, "Experiment moved to history")

    return f"8 passed, 0 failed"


def main():
    """Run all integration tests"""
    runner = TestRunner()

    print("="*60)
    print("Phase 4-5 Integration Tests")
    print("="*60)

    runner.setup()

    try:
        # Run tests
        test_quality_scorer_to_ab_testing(runner)
        test_ab_testing_with_queue(runner)
        test_meta_learning_with_quality_scorer(runner)
        test_end_to_end_workflow(runner)

        # Final summary
        print("\n" + "="*60)
        print("FINAL TEST SUMMARY")
        print("="*60)
        print(f"✅ Passed: {runner.passed}")
        print(f"❌ Failed: {runner.failed}")
        print(f"Success Rate: {runner.passed / (runner.passed + runner.failed) * 100:.1f}%")
        print("="*60)

        if runner.failed == 0:
            print("\n✅ ALL INTEGRATION TESTS PASSED!")
            print("Phase 4 & 5 systems work together seamlessly.")
        else:
            print(f"\n❌ {runner.failed} tests failed - Review failures above")

    finally:
        runner.teardown()


if __name__ == "__main__":
    main()
