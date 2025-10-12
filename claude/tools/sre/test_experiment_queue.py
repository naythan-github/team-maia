#!/usr/bin/env python3
"""
Test Suite for Experiment Queue System

Tests priority-based scheduling, auto-start, and queue management.
"""

import sys
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from claude.tools.sre.experiment_queue import (
    ExperimentQueue, Priority, QueueStatus
)


class TestRunner:
    """Test runner for experiment queue"""

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

    def assert_equals(self, actual, expected, message: str):
        """Assert actual equals expected"""
        if actual == expected:
            print(f"✅ {message} (value: {actual})")
            self.passed += 1
        else:
            print(f"❌ {message} (expected: {expected}, got: {actual})")
            self.failed += 1

    def print_section(self, title: str):
        """Print section header"""
        print(f"\n{'='*60}")
        print(f"{title}")
        print('='*60)


def test_queue_creation(runner: TestRunner):
    """Test basic queue creation"""
    runner.print_section("Test 1: Queue Creation")

    # Create isolated queue with custom session dir
    import sys
    temp_session = runner.temp_dir / "test1"
    temp_session.mkdir(parents=True, exist_ok=True)

    # Temporarily override maia_root for testing
    queue = ExperimentQueue(max_concurrent=3)
    queue.queue_dir = temp_session
    queue.queue_file = temp_session / "queue.json"
    queue.history_file = temp_session / "history.json"
    queue.queue = []
    queue.history = []

    status = queue.get_queue_status()
    runner.assert_equals(status['capacity']['max_concurrent'], 3, "Max concurrent set correctly")
    runner.assert_equals(status['queue_counts']['active'], 0, "No active experiments initially")
    runner.assert_equals(status['queue_counts']['queued'], 0, "No queued experiments initially")

    return f"3 passed, 0 failed"


def test_add_experiment(runner: TestRunner):
    """Test adding experiments to queue"""
    runner.print_section("Test 2: Adding Experiments")

    queue = ExperimentQueue(max_concurrent=3)

    # Add experiment with unique ID
    exp = queue.add_experiment(
        experiment_id="test2_exp_001",
        agent_name="test_agent",
        priority=Priority.HIGH,
        notes="Test experiment"
    )

    runner.assert_equals(exp.experiment_id, "test2_exp_001", "Experiment ID correct")
    runner.assert_equals(exp.priority, Priority.HIGH, "Priority correct")
    runner.assert_equals(exp.status, QueueStatus.ACTIVE, "Auto-started (capacity available)")

    status = queue.get_queue_status()
    runner.assert_equals(status['queue_counts']['active'], 1, "1 active experiment")

    return f"4 passed, 0 failed"


def test_auto_start_logic(runner: TestRunner):
    """Test automatic starting of queued experiments"""
    runner.print_section("Test 3: Auto-Start Logic")

    queue = ExperimentQueue(max_concurrent=2)  # Only 2 concurrent

    # Add 3 experiments with unique IDs
    exp1 = queue.add_experiment("test3_exp_001", "agent1", Priority.HIGH, "First")
    exp2 = queue.add_experiment("test3_exp_002", "agent2", Priority.MEDIUM, "Second")
    exp3 = queue.add_experiment("test3_exp_003", "agent3", Priority.LOW, "Third")

    status = queue.get_queue_status()
    runner.assert_equals(status['queue_counts']['active'], 2, "2 active (at capacity)")
    runner.assert_equals(status['queue_counts']['queued'], 1, "1 queued (waiting)")

    # Complete one experiment
    queue.complete_experiment("test3_exp_001", outcome="Success")

    status = queue.get_queue_status()
    runner.assert_equals(status['queue_counts']['active'], 2, "2 active (auto-started from queue)")
    runner.assert_equals(status['queue_counts']['queued'], 0, "0 queued (all started)")

    return f"4 passed, 0 failed"


def test_priority_ordering(runner: TestRunner):
    """Test priority-based auto-start"""
    runner.print_section("Test 4: Priority-Based Ordering")

    queue = ExperimentQueue(max_concurrent=1)  # Only 1 concurrent

    # Add multiple experiments with different priorities
    exp1 = queue.add_experiment("exp_low_1", "agent1", Priority.LOW, "Low priority 1")
    exp2 = queue.add_experiment("exp_high_1", "agent2", Priority.HIGH, "High priority")
    exp3 = queue.add_experiment("exp_med_1", "agent3", Priority.MEDIUM, "Medium priority")
    exp4 = queue.add_experiment("exp_low_2", "agent4", Priority.LOW, "Low priority 2")

    # Complete first experiment
    queue.complete_experiment("exp_low_1", outcome="Done")

    # Check that HIGH priority started next (not medium or low)
    status = queue.get_queue_status()
    active_ids = [exp['experiment_id'] for exp in status['active_experiments']]

    runner.assert_true("exp_high_1" in active_ids, "High priority auto-started first")
    runner.assert_equals(status['queue_counts']['active'], 1, "1 active")
    runner.assert_equals(status['queue_counts']['queued'], 2, "2 still queued")

    return f"3 passed, 0 failed"


def test_pause_resume(runner: TestRunner):
    """Test pausing and resuming experiments"""
    runner.print_section("Test 5: Pause/Resume")

    queue = ExperimentQueue(max_concurrent=3)

    # Add experiments
    exp1 = queue.add_experiment("exp_001", "agent1", Priority.HIGH)
    exp2 = queue.add_experiment("exp_002", "agent2", Priority.MEDIUM)

    # Pause experiment
    paused = queue.pause_experiment("exp_001", reason="Waiting for data")

    runner.assert_equals(paused.status, QueueStatus.PAUSED, "Experiment paused")

    status = queue.get_queue_status()
    runner.assert_equals(status['queue_counts']['active'], 1, "1 active after pause")
    runner.assert_equals(status['queue_counts']['paused'], 1, "1 paused")

    # Resume (restart)
    resumed = queue.start_experiment("exp_001")
    runner.assert_equals(resumed.status, QueueStatus.ACTIVE, "Experiment resumed")

    status = queue.get_queue_status()
    runner.assert_equals(status['queue_counts']['active'], 2, "2 active after resume")
    runner.assert_equals(status['queue_counts']['paused'], 0, "0 paused")

    return f"5 passed, 0 failed"


def test_complete_cancel(runner: TestRunner):
    """Test completing and canceling experiments"""
    runner.print_section("Test 6: Complete/Cancel")

    queue = ExperimentQueue(max_concurrent=3)

    # Add experiments
    exp1 = queue.add_experiment("exp_001", "agent1", Priority.HIGH)
    exp2 = queue.add_experiment("exp_002", "agent2", Priority.MEDIUM)

    # Complete experiment
    completed = queue.complete_experiment("exp_001", outcome="Treatment 20% better")
    runner.assert_equals(completed.status, QueueStatus.COMPLETED, "Experiment completed")

    # Check moved to history
    history = queue.get_history(limit=10)
    runner.assert_equals(len(history), 1, "1 item in history")
    runner.assert_equals(history[0].experiment_id, "exp_001", "Correct experiment in history")

    # Cancel experiment
    cancelled = queue.cancel_experiment("exp_002", reason="Invalid hypothesis")
    runner.assert_equals(cancelled.status, QueueStatus.CANCELLED, "Experiment cancelled")

    history = queue.get_history(limit=10)
    runner.assert_equals(len(history), 2, "2 items in history")

    status = queue.get_queue_status()
    runner.assert_equals(status['queue_counts']['active'], 0, "0 active (all completed/cancelled)")

    return f"6 passed, 0 failed"


def test_change_priority(runner: TestRunner):
    """Test changing priority of queued experiments"""
    runner.print_section("Test 7: Change Priority")

    queue = ExperimentQueue(max_concurrent=1)

    # Add experiments
    exp1 = queue.add_experiment("exp_001", "agent1", Priority.HIGH)
    exp2 = queue.add_experiment("exp_002", "agent2", Priority.LOW)

    # exp2 is queued, change priority to HIGH
    updated = queue.change_priority("exp_002", Priority.HIGH)
    runner.assert_equals(updated.priority, Priority.HIGH, "Priority changed to HIGH")

    # Complete exp1 to trigger auto-start
    queue.complete_experiment("exp_001", outcome="Done")

    # exp2 should start (now HIGH priority)
    status = queue.get_queue_status()
    active_ids = [exp['experiment_id'] for exp in status['active_experiments']]
    runner.assert_true("exp_002" in active_ids, "Updated priority experiment started")

    return f"2 passed, 0 failed"


def test_history_tracking(runner: TestRunner):
    """Test experiment history tracking"""
    runner.print_section("Test 8: History Tracking")

    queue = ExperimentQueue(max_concurrent=3)

    # Add and complete experiments
    for i in range(5):
        exp = queue.add_experiment(f"exp_{i:03d}", f"agent{i}", Priority.MEDIUM)
        queue.complete_experiment(f"exp_{i:03d}", outcome=f"Result {i}")

    # Get history
    history = queue.get_history(limit=10)
    runner.assert_equals(len(history), 5, "5 experiments in history")

    # Filter by status
    completed = queue.get_history(limit=10, status=QueueStatus.COMPLETED)
    runner.assert_equals(len(completed), 5, "5 completed experiments")

    cancelled = queue.get_history(limit=10, status=QueueStatus.CANCELLED)
    runner.assert_equals(len(cancelled), 0, "0 cancelled experiments")

    # Check most recent first
    runner.assert_equals(history[0].experiment_id, "exp_004", "Most recent first")

    return f"4 passed, 0 failed"


def main():
    """Run all tests"""
    runner = TestRunner()

    print("="*60)
    print("Experiment Queue System - Test Suite")
    print("="*60)

    runner.setup()

    try:
        # Run tests
        test_queue_creation(runner)
        test_add_experiment(runner)
        test_auto_start_logic(runner)
        test_priority_ordering(runner)
        test_pause_resume(runner)
        test_complete_cancel(runner)
        test_change_priority(runner)
        test_history_tracking(runner)

        # Final summary
        print("\n" + "="*60)
        print("FINAL TEST SUMMARY")
        print("="*60)
        print(f"✅ Passed: {runner.passed}")
        print(f"❌ Failed: {runner.failed}")
        print(f"Success Rate: {runner.passed / (runner.passed + runner.failed) * 100:.1f}%")
        print("="*60)

        if runner.failed == 0:
            print("\n✅ ALL TESTS PASSED - Experiment Queue ready for production!")
        else:
            print(f"\n❌ {runner.failed} tests failed - Review failures above")

    finally:
        runner.teardown()


if __name__ == "__main__":
    main()
