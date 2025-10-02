# Integration Test Command

## Overview
Execute comprehensive integration tests for pre/post change validation of Maia system components.

## Usage

```bash
# Run full pre-change validation
maia integration_test pre_change

# Run post-change validation
maia integration_test post_change

# Run specific test suites
maia integration_test custom --suites core_infrastructure database_integrity tool_functionality

# Run with detailed output
maia integration_test pre_change --detailed --save-report

# Run performance-focused tests
maia integration_test performance

# Get test history and trends
maia integration_test history --days 30
```

## Command Parameters

### Basic Test Modes
- **pre_change**: Complete validation before making system changes
- **post_change**: Complete validation after making system changes
- **custom**: Run specific test suites only
- **performance**: Focus on performance benchmarks and timing
- **quick**: Fast subset of critical tests for rapid validation

### Options
- **--detailed**: Show detailed test output and failure information
- **--save-report**: Save test results to timestamped report file
- **--suites**: Specify which test suites to run (for custom mode)
- **--fail-fast**: Stop on first critical failure
- **--quiet**: Minimal output, results only
- **--benchmark**: Include performance timing for all operations

## Test Suites

### Core Infrastructure
- Git repository integrity
- UFC directory structure validation
- iCloud Drive connectivity and permissions
- Python environment verification

### Database Integrity
- Database accessibility and connection testing
- Table structure validation
- Data consistency checks
- Path configuration verification

### Tool Functionality
- Critical tool import validation
- Basic functionality testing for key tools
- Configuration and dependency checks
- Inter-tool integration verification

### Agent System
- Agent definition availability
- Enhanced infrastructure component checks
- Message bus and context management (if available)
- Agent orchestration capability verification

### Context Management
- UFC mandatory context file validation
- Context file completeness and quality
- Context loading sequence verification
- Cross-context reference integrity

### Data Flow
- Path resolution and fallback mechanisms
- Database-to-tool integration
- Cross-component data consistency
- Configuration cascade validation

### Security Posture
- Security tool availability
- Git repository secret scanning
- Configuration security validation
- Access permission verification

### Performance Benchmarks
- Database query performance
- Tool initialization timing
- Memory usage patterns
- System resource utilization

## Implementation

```python
#!/usr/bin/env python3
import sys
import argparse
import json
from pathlib import Path
from datetime import datetime, timedelta

# Add Maia tools to path
sys.path.append(str(Path(__file__).parent.parent / "tools"))

from testing.integration_test_suite import MaiaIntegrationTestSuite

def main():
    parser = argparse.ArgumentParser(description="Maia Integration Test Suite")
    parser.add_argument("mode", choices=["pre_change", "post_change", "custom", "performance", "quick", "history"],
                       help="Test mode to execute")
    parser.add_argument("--suites", nargs="*",
                       choices=["core_infrastructure", "database_integrity", "tool_functionality",
                               "agent_system", "context_management", "data_flow", "security_posture", "performance_benchmarks"],
                       help="Specific test suites to run (custom mode)")
    parser.add_argument("--detailed", action="store_true", help="Show detailed test output")
    parser.add_argument("--save-report", action="store_true", help="Save results to report file")
    parser.add_argument("--fail-fast", action="store_true", help="Stop on first critical failure")
    parser.add_argument("--quiet", action="store_true", help="Minimal output")
    parser.add_argument("--benchmark", action="store_true", help="Include performance timing")
    parser.add_argument("--days", type=int, default=7, help="Days of history to show")

    args = parser.parse_args()

    suite = MaiaIntegrationTestSuite()

    try:
        if args.mode == "history":
            show_test_history(suite, args.days, args.detailed)
            return 0

        elif args.mode in ["pre_change", "post_change"]:
            pre_change = args.mode == "pre_change"
            results = suite.run_full_test_suite(pre_change)

        elif args.mode == "custom":
            if not args.suites:
                print("❌ Custom mode requires --suites parameter")
                return 1
            results = run_custom_test_suites(suite, args.suites)

        elif args.mode == "performance":
            results = run_performance_focused_tests(suite)

        elif args.mode == "quick":
            results = run_quick_validation(suite)

        # Handle results
        if args.save_report:
            save_test_report(results)

        # Determine exit code
        if results["overall_status"] == "CRITICAL_FAILURE":
            return 2  # Critical failure
        elif results["overall_status"] == "FAIL":
            return 1  # Standard failure
        else:
            return 0  # Success or warnings

    except Exception as e:
        print(f"💥 Test suite failed: {e}")
        return 3  # System error

def run_custom_test_suites(suite, selected_suites):
    """Run only selected test suites"""
    print(f"🧪 Running custom test suites: {', '.join(selected_suites)}")

    # Temporarily modify suite to only run selected tests
    original_suites = suite.test_suites.copy()
    suite.test_suites = {name: func for name, func in original_suites.items()
                        if name in selected_suites}

    try:
        results = suite.run_full_test_suite(pre_change=True)
        results["test_type"] = "custom"
        results["selected_suites"] = selected_suites
        return results
    finally:
        # Restore original test suites
        suite.test_suites = original_suites

def run_performance_focused_tests(suite):
    """Run performance-focused test suite"""
    print("🚀 Running performance-focused tests")

    # Focus on performance and core functionality
    performance_suites = ["core_infrastructure", "database_integrity", "performance_benchmarks"]
    return run_custom_test_suites(suite, performance_suites)

def run_quick_validation(suite):
    """Run quick validation for rapid feedback"""
    print("⚡ Running quick validation tests")

    # Critical tests only
    quick_suites = ["core_infrastructure", "database_integrity", "tool_functionality"]
    return run_custom_test_suites(suite, quick_suites)

def show_test_history(suite, days, detailed):
    """Show test history and trends"""
    print(f"📊 Test History (last {days} days)")
    print("=" * 50)

    # Get test result files from last N days
    cutoff_date = datetime.now() - timedelta(days=days)
    test_files = []

    for file_path in suite.test_results_dir.glob("integration_test_*.json"):
        try:
            # Extract date from filename
            parts = file_path.stem.split('_')
            if len(parts) >= 4:
                date_str = f"{parts[3]}_{parts[4]}"
                file_date = datetime.strptime(date_str, "%Y%m%d_%H%M%S")
                if file_date > cutoff_date:
                    test_files.append((file_date, file_path))
        except ValueError:
            continue

    # Sort by date
    test_files.sort(key=lambda x: x[0], reverse=True)

    if not test_files:
        print(f"No test results found in last {days} days")
        return

    # Show summary
    print(f"📋 Found {len(test_files)} test runs")

    for file_date, file_path in test_files:
        try:
            with open(file_path, 'r') as f:
                results = json.load(f)

            stats = results.get("summary_stats", {})
            status = results.get("overall_status", "UNKNOWN")
            test_type = results.get("test_type", "unknown")

            status_emoji = {"PASS": "✅", "PASS_WITH_WARNINGS": "⚠️", "FAIL": "❌", "CRITICAL_FAILURE": "🚨"}.get(status, "❓")

            print(f"\n{status_emoji} {file_date.strftime('%Y-%m-%d %H:%M')} - {test_type}")
            print(f"   Pass rate: {stats.get('pass_rate', 0):.1%} ({stats.get('passed_tests', 0)}/{stats.get('total_tests', 0)})")

            if detailed and results.get("critical_failures"):
                print(f"   Critical failures: {', '.join(results['critical_failures'])}")

        except Exception as e:
            print(f"❌ Error reading {file_path}: {e}")

def save_test_report(results):
    """Save detailed test report"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = Path(f"maia_integration_test_report_{timestamp}.md")

    with open(report_file, 'w') as f:
        f.write("# Maia Integration Test Report\n\n")
        f.write(f"**Test Session**: {results['test_session_id']}\n")
        f.write(f"**Timestamp**: {results['timestamp']}\n")
        f.write(f"**Test Type**: {results['test_type']}\n")
        f.write(f"**Overall Status**: {results['overall_status']}\n\n")

        # Summary stats
        stats = results['summary_stats']
        f.write("## Summary Statistics\n\n")
        f.write(f"- **Total Tests**: {stats['total_tests']}\n")
        f.write(f"- **Passed**: {stats['passed_tests']}\n")
        f.write(f"- **Failed**: {stats['failed_tests']}\n")
        f.write(f"- **Pass Rate**: {stats['pass_rate']:.1%}\n\n")

        # Suite results
        f.write("## Test Suite Results\n\n")
        for suite_name, suite_results in results['suite_results'].items():
            status = "✅ PASS" if suite_results.get('failed', 1) == 0 else "❌ FAIL"
            f.write(f"### {suite_name.replace('_', ' ').title()} {status}\n")
            f.write(f"- Passed: {suite_results.get('passed', 0)}\n")
            f.write(f"- Failed: {suite_results.get('failed', 0)}\n")

            if suite_results.get('failures'):
                f.write("- Failures:\n")
                for failure in suite_results['failures']:
                    f.write(f"  - {failure}\n")
            f.write("\n")

        # Recommendations
        if results.get('recommendations'):
            f.write("## Recommendations\n\n")
            for rec in results['recommendations']:
                f.write(f"- {rec}\n")

    print(f"📄 Test report saved to: {report_file}")

if __name__ == "__main__":
    sys.exit(main())
```

## Usage Examples

### Pre-Change Validation
```bash
# Before making major system changes
maia integration_test pre_change --save-report --detailed

# Quick validation before minor changes
maia integration_test quick
```

### Post-Change Validation
```bash
# After completing system changes
maia integration_test post_change --fail-fast

# Focus on areas likely affected by data migration
maia integration_test custom --suites database_integrity data_flow tool_functionality
```

### Performance Monitoring
```bash
# Regular performance checks
maia integration_test performance --benchmark

# Historical trend analysis
maia integration_test history --days 30 --detailed
```

### CI/CD Integration
```bash
# In automated pipelines
maia integration_test quick --quiet || exit 1

# Before deployment
maia integration_test pre_change --fail-fast || { echo "Pre-deployment tests failed"; exit 1; }
```

## Integration with Rollback System

### Pre-Change Workflow
1. Run pre-change validation: `maia integration_test pre_change`
2. Create rollback checkpoint: `maia system_rollback checkpoint`
3. Execute planned changes
4. Run post-change validation: `maia integration_test post_change`
5. If validation fails, execute rollback: `maia system_rollback execute`

### Automated Safety Pipeline
```bash
#!/bin/bash
# Comprehensive change safety pipeline

echo "🧪 Pre-change validation..."
maia integration_test pre_change --fail-fast || exit 1

echo "🛡️ Creating rollback checkpoint..."
CHECKPOINT_ID=$(maia system_rollback checkpoint "automated_change" "Automated system modification")

echo "🔧 Executing changes..."
# Your change commands here

echo "🧪 Post-change validation..."
if ! maia integration_test post_change --fail-fast; then
    echo "❌ Post-change validation failed - rolling back..."
    maia system_rollback execute "$CHECKPOINT_ID" --confirm
    exit 1
fi

echo "✅ Change completed successfully"
```

This integration test suite provides comprehensive validation capabilities ensuring system reliability before and after changes.
