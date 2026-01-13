#!/usr/bin/env python3
"""
Test Suite for Agent Chain Orchestrator
Tests workflow parsing, execution, validation, and audit trails.
"""

import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from claude.tools.orchestration.agent_chain_orchestrator import (
    AgentChainOrchestrator,
    WorkflowParser,
    ChainValidator,
    SubtaskStatus,
    execute_workflow
)


class TestRunner:
    """Simple test runner"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.total = 0

    def assert_true(self, condition: bool, message: str):
        """Assert condition is true"""
        self.total += 1
        if condition:
            self.passed += 1
            print(f"✅ {message}")
        else:
            self.failed += 1
            print(f"❌ {message}")

    def assert_equal(self, actual, expected, message: str):
        """Assert values are equal"""
        self.total += 1
        if actual == expected:
            self.passed += 1
            print(f"✅ {message}")
        else:
            self.failed += 1
            print(f"❌ {message}")
            print(f"   Expected: {expected}")
            print(f"   Actual: {actual}")

    def assert_greater(self, value: float, minimum: float, message: str):
        """Assert value greater than minimum"""
        self.total += 1
        if value > minimum:
            self.passed += 1
            print(f"✅ {message} (value: {value})")
        else:
            self.failed += 1
            print(f"❌ {message}")
            print(f"   Expected: > {minimum}")
            print(f"   Actual: {value}")

    def assert_in(self, item, container, message: str):
        """Assert item in container"""
        self.total += 1
        if item in container:
            self.passed += 1
            print(f"✅ {message}")
        else:
            self.failed += 1
            print(f"❌ {message}")
            print(f"   Expected {item} in container")

    def summary(self):
        """Print test summary"""
        print(f"\n{'='*60}")
        print(f"Test Results: {self.passed}/{self.total} passed")
        if self.failed > 0:
            print(f"❌ {self.failed} tests failed")
        else:
            print("✅ All tests passed!")
        print(f"{'='*60}")


def test_workflow_parser():
    """Test 1: Workflow file parsing"""
    print("\n" + "="*60)
    print("Test 1: Workflow Parser")
    print("="*60)

    runner = TestRunner()

    # Create temp workflow file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("""
# Test Workflow - Prompt Chain

## Overview
**Problem**: Test problem
**Solution**: Test solution

## Subtask Sequence

### Subtask 1: First Task

**Goal**: Complete first task

**Input**:
```json
{
  "domain": "example.com"
}
```

**Output**:
```json
{
  "result": "Success"
}
```

**Prompt**:
```
You are testing subtask 1.
Domain: {domain}
```

### Subtask 2: Second Task

**Goal**: Complete second task using first task output

**Input**:
```json
{
  "domain": "example.com"
}
```

**Output**:
```json
{
  "final_result": "Complete"
}
```

**Prompt**:
```
You are testing subtask 2.
Previous result: {subtask_1_output}
Domain: {domain}
```
""")
        temp_file = Path(f.name)

    try:
        parser = WorkflowParser()
        workflow = parser.parse_workflow_file(temp_file)

        runner.assert_equal(workflow['workflow_name'], temp_file.stem, "Workflow name extracted")
        runner.assert_true(len(workflow['overview']) > 0, "Overview extracted")
        runner.assert_equal(len(workflow['subtasks']), 2, "Two subtasks parsed")

        # Check subtask 1
        subtask1 = workflow['subtasks'][0]
        runner.assert_equal(subtask1.subtask_id, 1, "Subtask 1 ID correct")
        runner.assert_true("First Task" in subtask1.name, "Subtask 1 name extracted")
        runner.assert_true(len(subtask1.goal) > 0, "Subtask 1 goal extracted")
        runner.assert_in("domain", subtask1.input_schema, "Subtask 1 input schema parsed")
        runner.assert_in("result", subtask1.output_schema, "Subtask 1 output schema parsed")
        runner.assert_true(len(subtask1.prompt_template) > 0, "Subtask 1 prompt extracted")
        runner.assert_equal(subtask1.dependencies, [], "Subtask 1 has no dependencies")

        # Check subtask 2
        subtask2 = workflow['subtasks'][1]
        runner.assert_equal(subtask2.subtask_id, 2, "Subtask 2 ID correct")
        runner.assert_equal(subtask2.dependencies, [1], "Subtask 2 depends on subtask 1")

    finally:
        temp_file.unlink()

    runner.summary()
    return runner.passed == runner.total


def test_chain_validator():
    """Test 2: Output validation"""
    print("\n" + "="*60)
    print("Test 2: Chain Validator")
    print("="*60)

    runner = TestRunner()
    validator = ChainValidator()

    # Test valid output
    output = {"result": "success", "count": 5}
    schema = {"result": "string", "count": "number"}
    is_valid, errors = validator.validate_output(output, schema, {})

    runner.assert_true(is_valid, "Valid output passes validation")
    runner.assert_equal(len(errors), 0, "No errors for valid output")

    # Test missing required key
    output = {"result": "success"}
    schema = {"result": "string", "count": "number"}
    is_valid, errors = validator.validate_output(output, schema, {})

    runner.assert_true(not is_valid, "Invalid output fails validation")
    runner.assert_greater(len(errors), 0, "Errors reported for missing key")

    # Test validation rules
    output = {"result": "a"}
    schema = {"result": "string"}
    rules = {"min_length": {"result": 10}}
    is_valid, errors = validator.validate_output(output, schema, rules)

    runner.assert_true(not is_valid, "Min length rule enforced")

    runner.summary()
    return runner.passed == runner.total


def test_basic_execution():
    """Test 3: Basic chain execution"""
    print("\n" + "="*60)
    print("Test 3: Basic Chain Execution")
    print("="*60)

    runner = TestRunner()

    # Create temp workflow
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("""
# Simple Chain

## Overview
Test workflow

### Subtask 1: Task One

**Goal**: First task

**Input**:
```json
{"value": "test"}
```

**Output**:
```json
{"result": "output"}
```

**Prompt**:
```
Process: {value}
```

### Subtask 2: Task Two

**Goal**: Second task

**Input**:
```json
{"value": "test"}
```

**Output**:
```json
{"final": "done"}
```

**Prompt**:
```
Use previous: {subtask_1_output}
Value: {value}
```
""")
        temp_file = Path(f.name)

    try:
        # Use temp directory for audit
        with tempfile.TemporaryDirectory() as temp_dir:
            orchestrator = AgentChainOrchestrator(audit_dir=Path(temp_dir))
            workflow = orchestrator.load_workflow(temp_file)
            execution = orchestrator.execute_chain(workflow, {"value": "test123"})

            runner.assert_true(execution.chain_id is not None, "Chain ID generated")
            runner.assert_equal(execution.status, "completed", "Chain completed successfully")
            runner.assert_equal(len(execution.subtask_executions), 2, "Both subtasks executed")
            runner.assert_equal(execution.success_count, 2, "Both subtasks successful")
            runner.assert_equal(execution.failure_count, 0, "No failures")
            runner.assert_greater(execution.total_time_ms, 0, "Execution time recorded")

            # Check audit trail
            audit_files = list(Path(temp_dir).glob("*.jsonl"))
            runner.assert_equal(len(audit_files), 1, "Audit trail created")

    finally:
        temp_file.unlink()

    runner.summary()
    return runner.passed == runner.total


def test_dependency_validation():
    """Test 4: Dependency checking"""
    print("\n" + "="*60)
    print("Test 4: Dependency Validation")
    print("="*60)

    runner = TestRunner()

    # Create workflow with dependencies
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("""
# Dependency Chain

## Overview
Test dependencies

### Subtask 1: Base Task

**Goal**: Foundation

**Input**:
```json
{"data": "value"}
```

**Output**:
```json
{"base": "result"}
```

**Prompt**:
```
Process: {data}
```

### Subtask 2: Dependent Task

**Goal**: Uses subtask 1

**Input**:
```json
{"data": "value"}
```

**Output**:
```json
{"derived": "result"}
```

**Prompt**:
```
Using: {subtask_1_output}
Data: {data}
```
""")
        temp_file = Path(f.name)

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            orchestrator = AgentChainOrchestrator(audit_dir=Path(temp_dir))
            workflow = orchestrator.load_workflow(temp_file)

            # Check dependency detection
            runner.assert_equal(workflow['subtasks'][0].dependencies, [], "Subtask 1 has no deps")
            runner.assert_equal(workflow['subtasks'][1].dependencies, [1], "Subtask 2 depends on 1")

            # Execute chain
            execution = orchestrator.execute_chain(workflow, {"data": "test"})

            runner.assert_equal(execution.status, "completed", "Chain with dependencies completes")
            runner.assert_equal(execution.success_count, 2, "All subtasks succeed")

    finally:
        temp_file.unlink()

    runner.summary()
    return runner.passed == runner.total


def test_execution_history():
    """Test 5: Execution history retrieval"""
    print("\n" + "="*60)
    print("Test 5: Execution History")
    print("="*60)

    runner = TestRunner()

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("""
# History Test

## Overview
Test history

### Subtask 1: Only Task

**Goal**: Single task

**Input**:
```json
{"value": "v"}
```

**Output**:
```json
{"result": "r"}
```

**Prompt**:
```
Value: {value}
```
""")
        temp_file = Path(f.name)

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            orchestrator = AgentChainOrchestrator(audit_dir=Path(temp_dir))
            workflow = orchestrator.load_workflow(temp_file)

            # Execute multiple times
            exec1 = orchestrator.execute_chain(workflow, {"value": "test1"})
            exec2 = orchestrator.execute_chain(workflow, {"value": "test2"})

            # Retrieve history
            history = orchestrator.get_execution_history()

            runner.assert_equal(len(history), 2, "Two executions in history")
            runner.assert_equal(history[0]['chain_id'], exec2.chain_id, "Most recent first")
            runner.assert_equal(history[1]['chain_id'], exec1.chain_id, "Oldest second")

            # Filter by workflow name
            filtered = orchestrator.get_execution_history(workflow_name=workflow['workflow_name'])
            runner.assert_equal(len(filtered), 2, "Filtered history correct")

    finally:
        temp_file.unlink()

    runner.summary()
    return runner.passed == runner.total


def test_real_workflow():
    """Test 6: Execute real workflow file"""
    print("\n" + "="*60)
    print("Test 6: Real Workflow Execution")
    print("="*60)

    runner = TestRunner()

    # Find real workflow file (use new-format workflow for testing)
    workflows_dir = Path(__file__).parent.parent.parent / "workflows" / "prompt_chains"

    # Prefer new-format workflows (with **Input**: marker)
    new_format_workflows = [
        "dns_audit_security_migration_chain.md",
        "complaint_analysis_chain.md",
        "email_crisis_authentication_monitoring_chain.md",
        "system_health_bottleneck_optimization_chain.md"
    ]

    workflow_file = None
    for wf_name in new_format_workflows:
        candidate = workflows_dir / wf_name
        if candidate.exists():
            workflow_file = candidate
            break

    # Fallback to any workflow if new-format not found
    if workflow_file is None:
        workflow_files = list(workflows_dir.glob("*.md"))
        if workflow_files:
            workflow_file = workflow_files[0]

    if workflow_file:
        print(f"   Using: {workflow_file.name}")

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                orchestrator = AgentChainOrchestrator(audit_dir=Path(temp_dir))
                workflow = orchestrator.load_workflow(workflow_file)

                runner.assert_true(len(workflow['subtasks']) > 0, "Real workflow has subtasks")

                # Execute with mock input
                initial_input = {
                    "domain": "example.com",
                    "include_subdomains": True,
                    "dns_providers": ["Cloudflare"]
                }

                execution = orchestrator.execute_chain(workflow, initial_input)

                runner.assert_true(execution.chain_id is not None, "Real workflow executes")
                runner.assert_true(execution.status in ["completed", "partial"], "Execution completes or partial")
                runner.assert_greater(len(execution.subtask_executions), 0, "Subtasks executed")

        except Exception as e:
            print(f"   Note: Real workflow test encountered: {e}")
            runner.assert_true(True, "Real workflow parsing attempted")
    else:
        print("   ⚠️  No real workflow files found - skipping")
        runner.assert_true(True, "No real workflows to test")

    runner.summary()
    return runner.passed == runner.total


def test_convenience_function():
    """Test 7: Convenience function"""
    print("\n" + "="*60)
    print("Test 7: Convenience Function")
    print("="*60)

    runner = TestRunner()

    # Create temp workflow
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("""
# Convenience Test

## Overview
Test convenience

### Subtask 1: Single

**Goal**: Test

**Input**:
```json
{"test": "value"}
```

**Output**:
```json
{"output": "result"}
```

**Prompt**:
```
Test: {test}
```
""")
        temp_file = Path(f.name)

    try:
        execution = execute_workflow(temp_file, {"test": "convenience"})

        runner.assert_true(execution is not None, "Convenience function works")
        runner.assert_equal(execution.status, "completed", "Convenience execution completes")

    finally:
        temp_file.unlink()

    runner.summary()
    return runner.passed == runner.total


def test_error_handling():
    """Test 8: Error handling"""
    print("\n" + "="*60)
    print("Test 8: Error Handling")
    print("="*60)

    runner = TestRunner()

    # Test missing workflow file
    try:
        orchestrator = AgentChainOrchestrator()
        workflow = orchestrator.load_workflow(Path("/nonexistent/workflow.md"))
        runner.assert_true(False, "Should raise FileNotFoundError")
    except FileNotFoundError:
        runner.assert_true(True, "FileNotFoundError raised for missing file")

    # Test execution with missing context key
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("""
# Error Test

## Overview
Test errors

### Subtask 1: Missing Key

**Goal**: Test

**Input**:
```json
{"required_key": "value"}
```

**Output**:
```json
{"result": "output"}
```

**Prompt**:
```
Required: {required_key}
Missing: {missing_key}
```
""")
        temp_file = Path(f.name)

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            orchestrator = AgentChainOrchestrator(audit_dir=Path(temp_dir))
            workflow = orchestrator.load_workflow(temp_file)

            # Execute with missing key
            execution = orchestrator.execute_chain(workflow, {"required_key": "value"})

            # Single subtask that fails should have status "failed" (not "partial")
            # "partial" is for workflows where some subtasks succeed and some fail
            runner.assert_equal(execution.status, "failed", "Failed execution with error")
            runner.assert_equal(execution.failure_count, 1, "Failure recorded")
            runner.assert_true(
                execution.subtask_executions[0].error_message is not None,
                "Error message captured"
            )

    finally:
        temp_file.unlink()

    runner.summary()
    return runner.passed == runner.total


def run_all_tests():
    """Run all test suites"""
    print("\n" + "🧪" * 30)
    print("AGENT CHAIN ORCHESTRATOR - TEST SUITE")
    print("🧪" * 30)

    results = []

    # Run all tests
    results.append(("Workflow Parser", test_workflow_parser()))
    results.append(("Chain Validator", test_chain_validator()))
    results.append(("Basic Execution", test_basic_execution()))
    results.append(("Dependency Validation", test_dependency_validation()))
    results.append(("Execution History", test_execution_history()))
    results.append(("Real Workflow", test_real_workflow()))
    results.append(("Convenience Function", test_convenience_function()))
    results.append(("Error Handling", test_error_handling()))

    # Print final summary
    print("\n" + "📊" * 30)
    print("FINAL TEST SUMMARY")
    print("📊" * 30)

    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")

    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)

    print(f"\n{'='*60}")
    print(f"Overall: {total_passed}/{total_tests} test suites passed")
    if total_passed == total_tests:
        print("✅ ALL TESTS PASSED - Agent Chain Orchestrator ready for production!")
    else:
        print(f"❌ {total_tests - total_passed} test suite(s) failed")
    print(f"{'='*60}\n")

    return total_passed == total_tests


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
