"""
Test Suite for Error Recovery System

Comprehensive tests for retry logic, rollback mechanisms, and recovery strategies.
"""

import sys
import tempfile
import time
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from claude.tools.orchestration.error_recovery import (
    ErrorRecoverySystem, RecoveryConfig, RecoveryStrategy,
    RetryConfig, RetryPolicy, ErrorClassifier, RetryManager,
    CheckpointManager, Checkpoint, RecoveryAttempt, ErrorSeverity
)


class TestRunner:
    """Simple test runner that tracks assertions"""

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

    def assert_equal(self, actual, expected, message):
        self.total += 1
        if actual == expected:
            print(f"✅ {message}")
            self.passed += 1
        else:
            print(f"❌ {message}")
            print(f"   Expected: {expected}")
            print(f"   Actual: {actual}")

    def assert_in(self, item, container, message):
        self.total += 1
        if item in container:
            print(f"✅ {message}")
            self.passed += 1
        else:
            print(f"❌ {message}")
            print(f"   Expected {item} in {container}")

    def assert_greater(self, actual, minimum, message):
        self.total += 1
        if actual > minimum:
            print(f"✅ {message} (value: {actual})")
            self.passed += 1
        else:
            print(f"❌ {message}")
            print(f"   Expected > {minimum}, got {actual}")

    def summary(self):
        print(f"\n{'='*60}")
        print(f"Test Results: {self.passed}/{self.total} passed")
        if self.passed == self.total:
            print("✅ All tests passed!")
        else:
            print(f"❌ {self.total - self.passed} tests failed")
        print(f"{'='*60}\n")


def test_error_classifier():
    """Test 1: Error classification"""
    print("\n" + "="*60)
    print("Test 1: Error Classifier")
    print("="*60)

    runner = TestRunner()
    classifier = ErrorClassifier()

    # Test transient errors
    transient_error = Exception("Connection timeout occurred")
    severity = classifier.classify(transient_error, str(transient_error))
    runner.assert_equal(severity, ErrorSeverity.TRANSIENT, "Timeout classified as transient")

    rate_limit_error = Exception("Rate limit exceeded: 503")
    severity = classifier.classify(rate_limit_error, str(rate_limit_error))
    runner.assert_equal(severity, ErrorSeverity.TRANSIENT, "Rate limit classified as transient")

    # Test validation errors
    validation_error = Exception("Validation failed: missing required key")
    severity = classifier.classify(validation_error, str(validation_error))
    runner.assert_equal(severity, ErrorSeverity.VALIDATION, "Missing key classified as validation")

    # Test dependency errors
    key_error = KeyError("missing_variable")
    severity = classifier.classify(key_error, "missing_variable")
    runner.assert_equal(severity, ErrorSeverity.DEPENDENCY, "KeyError classified as dependency")

    # Test fatal errors
    fatal_error = Exception("Out of memory")
    severity = classifier.classify(fatal_error, str(fatal_error))
    runner.assert_equal(severity, ErrorSeverity.FATAL, "Out of memory classified as fatal")

    runner.summary()
    return runner.passed == runner.total


def test_retry_manager():
    """Test 2: Retry delay calculation"""
    print("\n" + "="*60)
    print("Test 2: Retry Manager")
    print("="*60)

    runner = TestRunner()

    # Test exponential backoff
    config = RetryConfig(
        policy=RetryPolicy.EXPONENTIAL,
        initial_delay_ms=1000,
        backoff_multiplier=2.0,
        max_delay_ms=10000,
        jitter=False
    )
    retry_manager = RetryManager(config)

    delay1 = retry_manager.calculate_delay(1)
    runner.assert_equal(delay1, 1000, "First attempt: 1000ms")

    delay2 = retry_manager.calculate_delay(2)
    runner.assert_equal(delay2, 2000, "Second attempt: 2000ms (2^1 * 1000)")

    delay3 = retry_manager.calculate_delay(3)
    runner.assert_equal(delay3, 4000, "Third attempt: 4000ms (2^2 * 1000)")

    # Test max delay cap
    delay_large = retry_manager.calculate_delay(10)
    runner.assert_equal(delay_large, 10000, "Large attempt capped at max_delay")

    # Test linear backoff
    linear_config = RetryConfig(
        policy=RetryPolicy.LINEAR,
        initial_delay_ms=1000,
        jitter=False
    )
    linear_manager = RetryManager(linear_config)

    linear_delay2 = linear_manager.calculate_delay(2)
    runner.assert_equal(linear_delay2, 2000, "Linear: 2nd attempt = 2000ms")

    linear_delay3 = linear_manager.calculate_delay(3)
    runner.assert_equal(linear_delay3, 3000, "Linear: 3rd attempt = 3000ms")

    # Test should_retry logic
    runner.assert_true(
        retry_manager.should_retry(1, ErrorSeverity.TRANSIENT),
        "Should retry transient error on attempt 1"
    )

    runner.assert_true(
        not retry_manager.should_retry(1, ErrorSeverity.VALIDATION),
        "Should not retry validation error"
    )

    runner.assert_true(
        not retry_manager.should_retry(1, ErrorSeverity.FATAL),
        "Should not retry fatal error"
    )

    runner.assert_true(
        not retry_manager.should_retry(5, ErrorSeverity.TRANSIENT),
        "Should not retry beyond max_attempts"
    )

    runner.summary()
    return runner.passed == runner.total


def test_checkpoint_manager():
    """Test 3: Checkpoint persistence"""
    print("\n" + "="*60)
    print("Test 3: Checkpoint Manager")
    print("="*60)

    runner = TestRunner()

    with tempfile.TemporaryDirectory() as temp_dir:
        checkpoint_dir = Path(temp_dir)
        manager = CheckpointManager(checkpoint_dir)

        # Create checkpoint
        checkpoint = Checkpoint(
            chain_id="test_chain_123",
            workflow_name="test_workflow",
            checkpoint_time=datetime.now(),
            completed_subtasks=[1, 2],
            context={"key1": "value1", "subtask_1_output": {"result": "data"}},
            next_subtask_id=3,
            recovery_attempts=[
                RecoveryAttempt(
                    subtask_id=2,
                    attempt_number=2,
                    strategy_used="retry_1",
                    success=True,
                    timestamp=datetime.now(),
                    delay_ms=1000.0
                )
            ]
        )

        # Save checkpoint
        filepath = manager.save_checkpoint(checkpoint)
        runner.assert_true(filepath.exists(), "Checkpoint file created")

        # Load checkpoint
        loaded = manager.load_checkpoint("test_chain_123")
        runner.assert_true(loaded is not None, "Checkpoint loaded successfully")
        runner.assert_equal(loaded.chain_id, "test_chain_123", "Chain ID matches")
        runner.assert_equal(loaded.workflow_name, "test_workflow", "Workflow name matches")
        runner.assert_equal(loaded.completed_subtasks, [1, 2], "Completed subtasks match")
        runner.assert_equal(loaded.next_subtask_id, 3, "Next subtask ID matches")
        runner.assert_equal(len(loaded.recovery_attempts), 1, "Recovery attempts preserved")

        # Delete checkpoint
        manager.delete_checkpoint("test_chain_123")
        runner.assert_true(not filepath.exists(), "Checkpoint file deleted")

    runner.summary()
    return runner.passed == runner.total


def test_recovery_system_success():
    """Test 4: Successful execution (no recovery needed)"""
    print("\n" + "="*60)
    print("Test 4: Recovery System - Successful Execution")
    print("="*60)

    runner = TestRunner()

    config = RecoveryConfig(
        strategy=RecoveryStrategy.RETRY_THEN_FAIL,
        retry_config=RetryConfig(max_attempts=3)
    )
    recovery = ErrorRecoverySystem(config)

    # Function that succeeds on first try
    def successful_func():
        return {"result": "success"}

    success, result, error = recovery.execute_with_recovery(
        subtask_id=1,
        subtask_name="Test Subtask",
        execution_func=successful_func
    )

    runner.assert_true(success, "Execution succeeded")
    runner.assert_equal(result, {"result": "success"}, "Result returned correctly")
    runner.assert_true(error is None, "No error context")
    runner.assert_equal(len(recovery.recovery_attempts), 1, "One attempt recorded")
    runner.assert_true(recovery.recovery_attempts[0].success, "Attempt marked as successful")

    runner.summary()
    return runner.passed == runner.total


def test_recovery_system_retry():
    """Test 5: Recovery with retry"""
    print("\n" + "="*60)
    print("Test 5: Recovery System - Retry Logic")
    print("="*60)

    runner = TestRunner()

    config = RecoveryConfig(
        strategy=RecoveryStrategy.RETRY_THEN_FAIL,
        retry_config=RetryConfig(
            policy=RetryPolicy.FIXED,
            max_attempts=3,
            initial_delay_ms=10,  # Short delay for testing
            jitter=False
        )
    )
    recovery = ErrorRecoverySystem(config)

    # Function that fails twice, then succeeds
    attempt_counter = {"count": 0}

    def flaky_func():
        attempt_counter["count"] += 1
        if attempt_counter["count"] < 3:
            raise Exception("Temporary network error")
        return {"result": "success after retry"}

    start_time = time.time()
    success, result, error = recovery.execute_with_recovery(
        subtask_id=1,
        subtask_name="Flaky Subtask",
        execution_func=flaky_func
    )
    elapsed_ms = (time.time() - start_time) * 1000

    runner.assert_true(success, "Execution eventually succeeded")
    runner.assert_equal(result, {"result": "success after retry"}, "Result correct after retry")
    runner.assert_true(error is None, "No error on final success")
    runner.assert_equal(len(recovery.recovery_attempts), 3, "Three attempts recorded")
    runner.assert_equal(attempt_counter["count"], 3, "Function called 3 times")

    # Check that retry delays were applied (at least 20ms total for 2 retries @ 10ms each)
    runner.assert_greater(elapsed_ms, 20, "Retry delays applied")

    runner.summary()
    return runner.passed == runner.total


def test_recovery_system_failure():
    """Test 6: Recovery exhausts retries and fails"""
    print("\n" + "="*60)
    print("Test 6: Recovery System - Failure After Retries")
    print("="*60)

    runner = TestRunner()

    config = RecoveryConfig(
        strategy=RecoveryStrategy.RETRY_THEN_FAIL,
        retry_config=RetryConfig(
            policy=RetryPolicy.FIXED,
            max_attempts=2,
            initial_delay_ms=10,
            jitter=False
        )
    )
    recovery = ErrorRecoverySystem(config)

    # Function that always fails
    def failing_func():
        raise Exception("Persistent network timeout")

    success, result, error = recovery.execute_with_recovery(
        subtask_id=1,
        subtask_name="Failing Subtask",
        execution_func=failing_func
    )

    runner.assert_true(not success, "Execution failed")
    runner.assert_true(result is None, "No result on failure")
    runner.assert_true(error is not None, "Error context provided")
    runner.assert_equal(error.subtask_id, 1, "Error context has correct subtask ID")
    runner.assert_equal(error.subtask_name, "Failing Subtask", "Error context has correct name")
    runner.assert_in("network timeout", error.error_message.lower(), "Error message captured")
    runner.assert_equal(len(recovery.recovery_attempts), 2, "Two attempts made (max_attempts)")

    runner.summary()
    return runner.passed == runner.total


def test_recovery_system_validation_error():
    """Test 7: Validation errors should not retry"""
    print("\n" + "="*60)
    print("Test 7: Recovery System - Validation Error (No Retry)")
    print("="*60)

    runner = TestRunner()

    config = RecoveryConfig(
        strategy=RecoveryStrategy.RETRY_THEN_FAIL,
        retry_config=RetryConfig(max_attempts=5)  # High max attempts
    )
    recovery = ErrorRecoverySystem(config)

    # Function that raises validation error
    def validation_error_func():
        raise ValueError("Validation failed: missing required key 'email'")

    success, result, error = recovery.execute_with_recovery(
        subtask_id=1,
        subtask_name="Validation Test",
        execution_func=validation_error_func
    )

    runner.assert_true(not success, "Execution failed")
    runner.assert_equal(error.severity, ErrorSeverity.VALIDATION, "Classified as validation error")
    runner.assert_equal(len(recovery.recovery_attempts), 1, "Only one attempt (no retries)")

    runner.summary()
    return runner.passed == runner.total


def test_recovery_stats():
    """Test 8: Recovery statistics tracking"""
    print("\n" + "="*60)
    print("Test 8: Recovery Statistics")
    print("="*60)

    runner = TestRunner()

    config = RecoveryConfig(
        strategy=RecoveryStrategy.RETRY_THEN_FAIL,
        retry_config=RetryConfig(
            policy=RetryPolicy.FIXED,
            max_attempts=3,
            initial_delay_ms=1,
            jitter=False
        )
    )
    recovery = ErrorRecoverySystem(config)

    # Execute multiple subtasks
    # Subtask 1: Success on first try
    recovery.execute_with_recovery(1, "Subtask 1", lambda: {"ok": True})

    # Subtask 2: Success after 2 tries
    counter = {"count": 0}

    def retry_once():
        counter["count"] += 1
        if counter["count"] == 1:
            raise Exception("Transient error")
        return {"ok": True}

    recovery.execute_with_recovery(2, "Subtask 2", retry_once)

    # Get stats
    stats = recovery.get_recovery_stats()

    runner.assert_equal(stats["total_attempts"], 3, "Total attempts: 3 (1 + 2)")
    runner.assert_equal(stats["successful_attempts"], 2, "Successful attempts: 2")
    runner.assert_equal(stats["failed_attempts"], 1, "Failed attempts: 1")
    runner.assert_greater(stats["success_rate"], 0.6, "Success rate > 60%")

    runner.summary()
    return runner.passed == runner.total


def main():
    """Run all tests"""
    print("🧪" * 30)
    print("ERROR RECOVERY SYSTEM - TEST SUITE")
    print("🧪" * 30)

    tests = [
        test_error_classifier,
        test_retry_manager,
        test_checkpoint_manager,
        test_recovery_system_success,
        test_recovery_system_retry,
        test_recovery_system_failure,
        test_recovery_system_validation_error,
        test_recovery_stats
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
        print(f"{status}: {test_func.__doc__.split(':')[0].replace('Test ' + str(i), '').strip()}")

    print("\n" + "="*60)
    passed = sum(results)
    total = len(results)
    print(f"Overall: {passed}/{total} test suites passed")
    if passed == total:
        print("✅ ALL TESTS PASSED - Error Recovery System ready for production!")
    else:
        print(f"❌ {total - passed} test suite(s) failed")
    print("="*60)

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
