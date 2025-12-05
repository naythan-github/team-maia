#!/usr/bin/env python3
"""
Test v2.2 Enhanced Template - Validate Advanced Patterns
========================================================

Purpose: Verify that adding advanced patterns (self-reflection, review,
prompt chaining, explicit handoffs, test frequently) improves template
without excessive size increase.

Advanced patterns added:
1. Self-Reflection & Review
2. Review and Critique (in examples)
3. Prompt Chaining guidance
4. Explicit Handoff Declaration
7. Test Frequently (in problem-solving)
"""

from pathlib import Path

def test_template_enhancements():
    """Test v2.2 enhanced template against v2.1"""

    print("="*80)
    print("V2.2 ENHANCED TEMPLATE TEST")
    print("="*80)
    print("\nValidating advanced pattern additions\n")

    template_file = Path("claude/templates/agent_prompt_template_v2.1_lean.md")

    with open(template_file, 'r') as f:
        content = f.read()
        lines = content.split('\n')

    # Check for advanced patterns
    has_self_reflection = "Self-Reflection & Review" in content
    has_test_frequently = "Test frequently" in content
    has_prompt_chaining = "When to Use Prompt Chaining" in content
    has_explicit_handoff = "Explicit Handoff Declaration Pattern" in content
    has_validation_checkpoint = "Self-Reflection Checkpoint" in content

    print(f"Template Size: {len(lines)} lines\n")

    print("Advanced Patterns Check:")
    print(f"  ✅ Self-Reflection & Review: {'✅ FOUND' if has_self_reflection else '❌ MISSING'}")
    print(f"  ✅ Test Frequently: {'✅ FOUND' if has_test_frequently else '❌ MISSING'}")
    print(f"  ✅ Prompt Chaining: {'✅ FOUND' if has_prompt_chaining else '❌ MISSING'}")
    print(f"  ✅ Explicit Handoff: {'✅ FOUND' if has_explicit_handoff else '❌ MISSING'}")
    print(f"  ✅ Validation Checkpoint: {'✅ FOUND' if has_validation_checkpoint else '❌ MISSING'}")

    all_patterns = all([
        has_self_reflection,
        has_test_frequently,
        has_prompt_chaining,
        has_explicit_handoff,
        has_validation_checkpoint
    ])

    print(f"\n{'='*80}")
    print("SIZE COMPARISON")
    print("="*80)

    print(f"\nv2.1 (Lean): 273 lines (baseline)")
    print(f"v2.2 (Enhanced): {len(lines)} lines")
    size_increase = len(lines) - 273
    size_increase_pct = (size_increase / 273) * 100
    print(f"Increase: +{size_increase} lines (+{size_increase_pct:.1f}%)")

    print(f"\n{'='*80}")
    print("ASSESSMENT")
    print("="*80)

    success_criteria = {
        "all_patterns_added": all_patterns,
        "size_under_400": len(lines) < 400,
        "size_increase_reasonable": size_increase < 100
    }

    print(f"\n✅ All 5 Advanced Patterns Added: {'✅ PASS' if success_criteria['all_patterns_added'] else '❌ FAIL'}")
    print(f"✅ Size Under 400 Lines: {len(lines)} {'✅ PASS' if success_criteria['size_under_400'] else '❌ FAIL'}")
    print(f"✅ Size Increase Reasonable (<100): +{size_increase} {'✅ PASS' if success_criteria['size_increase_reasonable'] else '❌ FAIL'}")

    all_pass = all(success_criteria.values())

    print(f"\n{'='*80}")
    if all_pass:
        print("✅ **V2.2 ENHANCED TEMPLATE READY**")
        print(f"\nv2.2 achieves:")
        print(f"- All 5 advanced patterns from research")
        print(f"- Size: {len(lines)} lines (still under 400-line target)")
        print(f"- +{size_increase_pct:.1f}% increase (reasonable for added value)")
        print("\n✅ Ready to test with real agents")
    else:
        print("⚠️ **V2.2 NEEDS ADJUSTMENT**")
        if not success_criteria['all_patterns_added']:
            print("- Some patterns missing")
        if not success_criteria['size_under_400']:
            print(f"- Size {len(lines)} exceeds 400-line target")
        if not success_criteria['size_increase_reasonable']:
            print(f"- Size increase +{size_increase} too large")

    print("="*80 + "\n")

    # Show what was added
    print("="*80)
    print("PATTERN DETAILS")
    print("="*80)

    patterns = [
        ("Self-Reflection & Review", "Core Behavior Principles", has_self_reflection),
        ("Test Frequently", "Problem-Solving Approach", has_test_frequently),
        ("Prompt Chaining", "Problem-Solving Approach", has_prompt_chaining),
        ("Explicit Handoff", "Integration Points", has_explicit_handoff),
        ("Validation Checkpoint", "Problem-Solving Approach", has_validation_checkpoint),
    ]

    for pattern_name, section, found in patterns:
        status = "✅" if found else "❌"
        print(f"\n{status} {pattern_name}")
        print(f"   Section: {section}")
        print(f"   Status: {'Added' if found else 'Missing'}")

    print(f"\n{'='*80}")
    print("RECOMMENDATION")
    print("="*80)

    if all_pass:
        print("\n✅ **Use v2.2 Enhanced template** for remaining agents")
        print("\nBenefits vs v2.1:")
        print("- Self-reflection catches errors before completion")
        print("- Review pattern improves solution quality")
        print("- Prompt chaining guidance for complex workflows")
        print("- Explicit handoff format enables orchestration")
        print("- Test frequently emphasis reduces production issues")
        print("\nCost:")
        print(f"- +{size_increase} lines (reasonable for 5 high-value patterns)")
        print(f"- Still industry-standard size ({len(lines)} vs OpenAI 300-500)")
    else:
        print("\n⚠️ Fix issues before using v2.2")

    print("="*80 + "\n")

    return {
        "size": len(lines),
        "patterns_added": all_patterns,
        "success": all_pass
    }


if __name__ == "__main__":
    result = test_template_enhancements()
    import sys
    sys.exit(0 if result['success'] else 1)
