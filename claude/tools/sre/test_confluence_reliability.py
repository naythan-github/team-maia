#!/usr/bin/env python3
"""
Confluence Reliability Test - Post-Consolidation Validation

Tests the consolidated Confluence tooling for reliability improvements.
Part of Phase 129 - Confluence Tooling Consolidation

USAGE:
    # Run HTML validation only (safe, no API calls)
    python3 test_confluence_reliability.py --html-only

    # Run full test including page creation (creates test pages)
    python3 test_confluence_reliability.py --full --space TEST

    # Run with specific iteration count
    python3 test_confluence_reliability.py --full --iterations 5 --space TEST
"""

import sys
import time
import argparse
from pathlib import Path

# Add Maia tools to path
maia_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(maia_root))

# Import from absolute path
tools_path = maia_root / "claude" / "tools"
sys.path.insert(0, str(tools_path))

from reliable_confluence_client import ReliableConfluenceClient
from confluence_html_builder import (
    ConfluencePageBuilder,
    validate_confluence_html,
    PanelColor
)


def test_html_validation() -> bool:
    """
    Test HTML builder produces valid content
    Tests various HTML structures for validation
    """
    print(f"\n{'='*70}")
    print(f"HTML VALIDATION TEST")
    print(f"{'='*70}\n")

    builder = ConfluencePageBuilder()

    # Test complex page structure
    html = (builder
        .add_heading("Test Page - Reliability Validation", level=1)
        .add_paragraph("This page tests complex HTML structure validation.")

        .add_info_panel({
            "Test Type": "Reliability Validation",
            "Phase": "129 - Confluence Tooling Consolidation",
            "Date": time.strftime("%Y-%m-%d %H:%M:%S")
        })

        .add_heading("Section 1: Lists", level=2)
        .add_list(["Item 1", "Item 2", "Item 3"])

        .add_heading("Section 2: Expand Section", level=2)
        .add_expand_section(
            title="Click to expand",
            content="<p>Hidden content for validation testing</p>"
        )

        .add_heading("Section 3: Table", level=2)
        .add_table(
            headers=["Metric", "Expected", "Actual"],
            rows=[
                ["Success Rate", "99%+", "TBD"],
                ["Latency", "<3s", "TBD"],
                ["Validation", "100%", "100%"]
            ]
        )

        .build()
    )

    # Validate generated HTML
    result = validate_confluence_html(html)

    print(f"HTML Length: {len(html)} characters")
    print(f"Valid: {result.is_valid}")
    print(f"Errors: {len(result.errors)}")
    print(f"Warnings: {len(result.warnings)}")

    if result.errors:
        print(f"\n❌ ERRORS FOUND:")
        for error in result.errors:
            print(f"  - {error}")

    if result.warnings:
        print(f"\n⚠️  WARNINGS:")
        for warning in result.warnings:
            print(f"  - {warning}")

    if result.is_valid:
        print(f"\n✅ HTML VALIDATION PASSED")
    else:
        print(f"\n❌ HTML VALIDATION FAILED")

    print(f"\n{'='*70}\n")

    return result.is_valid


def test_page_creation_reliability(space_key: str = "TEST", iterations: int = 10) -> dict:
    """
    Test consecutive page creations for reliability

    Args:
        space_key: Confluence space for test pages
        iterations: Number of test pages to create

    Returns:
        dict: Test results with metrics
    """
    print(f"\n{'='*70}")
    print(f"PAGE CREATION RELIABILITY TEST")
    print(f"{'='*70}\n")

    print(f"Target Space: {space_key}")
    print(f"Iterations: {iterations}")
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    client = ReliableConfluenceClient()
    results = []

    for i in range(iterations):
        print(f"Test {i+1}/{iterations}...", end=" ", flush=True)

        # Build test page HTML
        builder = ConfluencePageBuilder()
        html = (builder
            .add_heading(f"Reliability Test {i+1}", level=1)
            .add_paragraph(f"This is test page {i+1} created during Phase 129 tooling consolidation validation.")
            .add_list([
                f"Test iteration: {i+1}/{iterations}",
                f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}",
                "Status: Active test page"
            ])
            .build())

        # Validate HTML first
        validation = validate_confluence_html(html)
        if not validation.is_valid:
            print(f"❌ HTML validation failed")
            results.append({
                "iteration": i+1,
                "success": False,
                "error": "HTML validation failed",
                "latency": 0
            })
            continue

        # Create page with timing
        start = time.time()
        result = client.create_page(
            space_key=space_key,
            title=f"Reliability Test {i+1} - {int(time.time())}",
            content=html,
            validate_html=True
        )
        latency = time.time() - start

        if result:
            print(f"✅ {latency:.2f}s")
            results.append({
                "iteration": i+1,
                "success": True,
                "latency": latency,
                "url": result.get('url'),
                "page_id": result.get('id')
            })
        else:
            print(f"❌ Failed")
            results.append({
                "iteration": i+1,
                "success": False,
                "error": "Page creation failed",
                "latency": latency
            })

        # Small delay to avoid rate limiting
        time.sleep(0.5)

    # Calculate metrics
    successes = sum(1 for r in results if r['success'])
    failures = len(results) - successes
    success_rate = (successes / len(results)) * 100 if results else 0

    successful_results = [r for r in results if r['success']]
    avg_latency = sum(r.get('latency', 0) for r in successful_results) / len(successful_results) if successful_results else 0
    min_latency = min((r.get('latency', 0) for r in successful_results), default=0)
    max_latency = max((r.get('latency', 0) for r in successful_results), default=0)

    # Print results
    print(f"\n{'='*70}")
    print(f"RELIABILITY TEST RESULTS")
    print(f"{'='*70}")
    print(f"Total Tests:      {len(results)}")
    print(f"Successes:        {successes}")
    print(f"Failures:         {failures}")
    print(f"Success Rate:     {success_rate:.1f}%")
    print(f"")
    print(f"Latency Metrics:")
    print(f"  Average:        {avg_latency:.2f}s")
    print(f"  Min:            {min_latency:.2f}s")
    print(f"  Max:            {max_latency:.2f}s")
    print(f"{'='*70}\n")

    # Get client metrics
    metrics = client.get_metrics_summary()
    print(f"CLIENT METRICS:")
    print(f"  Circuit Breaker:  {metrics.get('circuit_breaker_state', 'unknown')}")
    print(f"  Total Requests:   {metrics.get('total_requests', 0)}")
    print(f"  Success Rate:     {metrics.get('success_rate', 0):.1f}%")
    print(f"  Avg Latency:      {metrics.get('average_latency', 0):.2f}s")
    print(f"{'='*70}\n")

    # Pass/fail determination
    passed = success_rate >= 90.0  # 90%+ success required

    if passed:
        print(f"✅ RELIABILITY TEST PASSED (≥90% success rate)")
    else:
        print(f"❌ RELIABILITY TEST FAILED (<90% success rate)")

    print(f"\nCompleted: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")

    return {
        "passed": passed,
        "success_rate": success_rate,
        "successes": successes,
        "failures": failures,
        "avg_latency": avg_latency,
        "min_latency": min_latency,
        "max_latency": max_latency,
        "results": results,
        "client_metrics": metrics
    }


def main():
    parser = argparse.ArgumentParser(
        description="Test Confluence tooling reliability (Phase 129 validation)"
    )
    parser.add_argument(
        "--html-only",
        action="store_true",
        help="Only run HTML validation (no API calls)"
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run full test including page creation (CREATES TEST PAGES)"
    )
    parser.add_argument(
        "--space",
        type=str,
        default="TEST",
        help="Confluence space for test pages (default: TEST)"
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=10,
        help="Number of page creation tests (default: 10)"
    )

    args = parser.parse_args()

    print(f"\n{'#'*70}")
    print(f"# Confluence Tooling Reliability Test")
    print(f"# Phase 129 - Post-Consolidation Validation")
    print(f"{'#'*70}\n")

    # Test 1: HTML Validation (always run)
    html_valid = test_html_validation()

    # Test 2: Page Creation Reliability (only if --full specified)
    if args.full:
        print(f"\n⚠️  WARNING: About to create {args.iterations} test pages in space '{args.space}'")
        print(f"Press Ctrl+C within 3 seconds to cancel...\n")
        time.sleep(3)

        reliability_results = test_page_creation_reliability(
            space_key=args.space,
            iterations=args.iterations
        )
        reliability_passed = reliability_results['passed']
    else:
        print(f"\n⏭️  Skipping page creation test (use --full to enable)")
        print(f"   This will create test pages in Confluence\n")
        reliability_passed = None

    # Summary
    print(f"\n{'='*70}")
    print(f"TEST SUMMARY")
    print(f"{'='*70}")
    print(f"HTML Validation:        {'✅ PASS' if html_valid else '❌ FAIL'}")
    if reliability_passed is not None:
        print(f"Reliability Test:       {'✅ PASS' if reliability_passed else '❌ FAIL'}")
        print(f"Success Rate:           {reliability_results['success_rate']:.1f}%")
        print(f"Average Latency:        {reliability_results['avg_latency']:.2f}s")
    else:
        print(f"Reliability Test:       ⏭️  SKIPPED")
    print(f"{'='*70}\n")

    # Exit code
    if not html_valid:
        sys.exit(1)
    if reliability_passed is False:
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
