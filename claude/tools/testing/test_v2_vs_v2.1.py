#!/usr/bin/env python3
"""
Test v2 vs v2.1 (Lean) - Validate Optimization
===============================================

Purpose: Compare v2 (bloated) vs v2.1 (lean) to validate size reduction maintains quality

Test: Azure Solutions Architect (v2 vs v2.1)
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from test_upgraded_agents import AgentValidator

def test_v2_vs_v2_1():
    """Test v2 vs v2.1 optimization"""

    validator = AgentValidator()

    print("="*80)
    print("V2 VS V2.1 (LEAN) OPTIMIZATION TEST - Azure Solutions Architect")
    print("="*80)
    print("\nValidating that size reduction maintains quality\n")

    # Test v2 (bloated)
    print("Testing v2 (Original)...")
    v2_result = validator.validate_agent("azure_solutions_architect_agent_v2.md", "v2")
    print(f"  Lines: {v2_result.line_count}")
    print(f"  Quality: {v2_result.overall_quality_score}/100")
    print(f"  Few-shot: {v2_result.few_shot_example_count}")
    print(f"  Compliance: {v2_result.template_compliance_score}%")
    if v2_result.issues:
        print(f"  Issues: {', '.join(v2_result.issues)}")
    print()

    # Test v2.1 (lean)
    print("Testing v2.1 (Lean)...")
    v21_result = validator.validate_agent("azure_solutions_architect_agent_v2.1_lean.md", "v2.1")
    print(f"  Lines: {v21_result.line_count}")
    print(f"  Quality: {v21_result.overall_quality_score}/100")
    print(f"  Few-shot: {v21_result.few_shot_example_count}")
    print(f"  Compliance: {v21_result.template_compliance_score}%")
    if v21_result.issues:
        print(f"  Issues: {', '.join(v21_result.issues)}")
    print()

    # Comparison
    print("="*80)
    print("COMPARISON")
    print("="*80)

    size_reduction_pct = ((v2_result.line_count - v21_result.line_count) / v2_result.line_count) * 100
    quality_change = v21_result.overall_quality_score - v2_result.overall_quality_score
    few_shot_change = v21_result.few_shot_example_count - v2_result.few_shot_example_count

    print(f"\nSize:")
    print(f"  v2:   {v2_result.line_count} lines")
    print(f"  v2.1: {v21_result.line_count} lines")
    print(f"  Reduction: {size_reduction_pct:.1f}% ✅")

    print(f"\nQuality Score:")
    print(f"  v2:   {v2_result.overall_quality_score}/100")
    print(f"  v2.1: {v21_result.overall_quality_score}/100")
    if quality_change > 0:
        print(f"  Change: +{quality_change} points ✅ (improved)")
    elif quality_change == 0:
        print(f"  Change: {quality_change} points ✅ (maintained)")
    else:
        print(f"  Change: {quality_change} points ⚠️ (decreased)")

    print(f"\nFew-Shot Examples:")
    print(f"  v2:   {v2_result.few_shot_example_count}")
    print(f"  v2.1: {v21_result.few_shot_example_count}")
    print(f"  Change: {few_shot_change:+d}")

    print(f"\nTemplate Compliance:")
    print(f"  v2:   {v2_result.template_compliance_score}%")
    print(f"  v2.1: {v21_result.template_compliance_score}%")

    # Feature comparison
    print(f"\nFeature Comparison:")
    features = [
        ("Core Behavior Principles", "has_core_behavior_principles"),
        ("OpenAI 3 Reminders", "has_openai_3_reminders"),
        ("Tool-Calling Patterns", "has_tool_calling_patterns"),
        ("Problem-Solving Templates", "has_problem_solving_templates"),
        ("Performance Metrics", "has_performance_metrics"),
    ]

    for feature_name, attr in features:
        v2_has = "✅" if getattr(v2_result, attr) else "❌"
        v21_has = "✅" if getattr(v21_result, attr) else "❌"
        maintained = "✅" if getattr(v2_result, attr) == getattr(v21_result, attr) else "⚠️"
        print(f"  {feature_name:<30} v2: {v2_has}  v2.1: {v21_has}  {maintained}")

    # Assessment
    print(f"\n{'='*80}")
    print("ASSESSMENT")
    print("="*80)

    success_criteria = {
        "size_reduction": size_reduction_pct >= 30,  # Target: 30%+ reduction
        "quality_maintained": quality_change >= 0,    # No quality loss
        "essentials_kept": all([
            v21_result.has_core_behavior_principles,
            v21_result.has_openai_3_reminders,
            v21_result.has_tool_calling_patterns
        ])
    }

    print(f"\n✅ Size Reduction >30%: {size_reduction_pct:.1f}% {'✅ PASS' if success_criteria['size_reduction'] else '❌ FAIL'}")
    print(f"✅ Quality Maintained: {quality_change:+d} points {'✅ PASS' if success_criteria['quality_maintained'] else '❌ FAIL'}")
    print(f"✅ Essentials Kept: {'✅ PASS' if success_criteria['essentials_kept'] else '❌ FAIL'}")

    all_pass = all(success_criteria.values())

    print(f"\n{'='*80}")
    if all_pass:
        print("✅ **V2.1 OPTIMIZATION SUCCESSFUL**")
        print("\nv2.1 (Lean) achieves:")
        print(f"- {size_reduction_pct:.1f}% size reduction (759→{v21_result.line_count} lines)")
        print(f"- Quality maintained: {v21_result.overall_quality_score}/100 ({quality_change:+d} vs v2)")
        print(f"- All essential features preserved")
        print("\n✅ Ready to use v2.1 template for remaining 41 agents")
    else:
        print("⚠️ **V2.1 OPTIMIZATION NEEDS REFINEMENT**")
        print("\nIssues:")
        if not success_criteria['size_reduction']:
            print(f"- Size reduction only {size_reduction_pct:.1f}% (target: 30%+)")
        if not success_criteria['quality_maintained']:
            print(f"- Quality decreased by {abs(quality_change)} points")
        if not success_criteria['essentials_kept']:
            print("- Essential features missing")
        print("\n⏳ Iterate on v2.1 template before scaling")

    print("="*80 + "\n")

    return {
        "v2_size": v2_result.line_count,
        "v2.1_size": v21_result.line_count,
        "size_reduction_pct": size_reduction_pct,
        "v2_quality": v2_result.overall_quality_score,
        "v2.1_quality": v21_result.overall_quality_score,
        "quality_change": quality_change,
        "success": all_pass
    }


if __name__ == "__main__":
    result = test_v2_vs_v2_1()

    # Exit with appropriate code
    sys.exit(0 if result['success'] else 1)
