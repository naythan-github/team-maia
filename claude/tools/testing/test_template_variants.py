#!/usr/bin/env python3
"""
Test Template Variants - Compare 3 Optimization Approaches
==========================================================

Purpose: Test 3 template variants (Lean, Minimalist, Hybrid) against baseline to find optimal balance

Variants:
- v1 (Baseline): 250 lines - original agent
- v2.1 (Lean): ~500 lines - compressed v2 template
- v2.2 (Minimalist): ~300 lines - essential OpenAI reminders only
- v2.3 (Hybrid): ~550 lines - balance quality + efficiency

Testing: Structure validation + quality scoring
"""

import sys
from pathlib import Path

# Import validator from previous test
sys.path.append(str(Path(__file__).parent))
from test_upgraded_agents import AgentValidator

def test_template_variants():
    """Test all 4 variants of Cloud Security Principal agent"""

    validator = AgentValidator()

    variants = [
        ("cloud_security_principal_agent.md", "v1 (Baseline)", "claude/agents"),
        ("cloud_security_v2.1_lean.md", "v2.1 (Lean)", "claude/agents/test_variants"),
        ("cloud_security_v2.2_minimalist.md", "v2.2 (Minimalist)", "claude/agents/test_variants"),
        ("cloud_security_v2.3_hybrid.md", "v2.3 (Hybrid)", "claude/agents/test_variants"),
    ]

    print("="*80)
    print("TEMPLATE VARIANT COMPARISON - Cloud Security Principal Agent")
    print("="*80)
    print("\nTesting 4 variants to find optimal template structure\n")

    results = []

    for filename, variant_name, directory in variants:
        print(f"Testing {variant_name}...")

        # Temporarily change directory for validator
        original_dir = validator.agent_dir
        validator.agent_dir = Path(directory)

        result = validator.validate_agent(filename, variant_name)
        results.append(result)

        # Restore directory
        validator.agent_dir = original_dir

        print(f"  Lines: {result.line_count}")
        print(f"  Quality Score: {result.overall_quality_score}/100")
        print(f"  Few-shot examples: {result.few_shot_example_count}")
        print(f"  Template compliance: {result.template_compliance_score}%")

        if result.issues:
            print(f"  ⚠️  Issues: {', '.join(result.issues)}")
        else:
            print(f"  ✅ No issues")
        print()

    # Comparison Analysis
    print("="*80)
    print("COMPARATIVE ANALYSIS")
    print("="*80)

    # Create comparison table
    print(f"\n{'Variant':<20} {'Lines':<10} {'Quality':<10} {'Examples':<10} {'Compliance':<12} {'Grade'}")
    print("-"*80)

    for result in results:
        grade = "✅" if result.overall_quality_score >= 85 else "⚠️" if result.overall_quality_score >= 70 else "❌"
        print(f"{result.version:<20} {result.line_count:<10} {result.overall_quality_score:<10} {result.few_shot_example_count:<10} {result.template_compliance_score}%{' '*(11-len(str(result.template_compliance_score)))} {grade}")

    # Size comparison
    baseline_size = results[0].line_count
    print(f"\n{'Size vs Baseline (v1):':<40}")
    for result in results[1:]:  # Skip baseline
        size_change = ((result.line_count - baseline_size) / baseline_size) * 100
        print(f"  {result.version}: {size_change:+.1f}% ({baseline_size} → {result.line_count} lines)")

    # Quality comparison
    print(f"\n{'Quality Score Comparison:':<40}")
    baseline_quality = results[0].overall_quality_score
    for result in results:
        if result.version == "v1 (Baseline)":
            print(f"  {result.version}: {result.overall_quality_score}/100 (baseline)")
        else:
            improvement = result.overall_quality_score - baseline_quality
            print(f"  {result.version}: {result.overall_quality_score}/100 ({improvement:+d} vs baseline)")

    # Feature comparison
    print(f"\n{'Feature Comparison:':<40}")
    features = [
        ("Core Behavior Principles", "has_core_behavior_principles"),
        ("OpenAI 3 Reminders", "has_openai_3_reminders"),
        ("Few-Shot Examples (2+)", lambda r: r.few_shot_example_count >= 2),
        ("Tool-Calling Patterns", "has_tool_calling_patterns"),
        ("Problem-Solving Templates", "has_problem_solving_templates"),
        ("Performance Metrics", "has_performance_metrics"),
    ]

    for feature_name, attr in features:
        print(f"  {feature_name}:")
        for result in results:
            if callable(attr):
                has_feature = attr(result)
            else:
                has_feature = getattr(result, attr)

            status = "✅" if has_feature else "❌"
            value = ""
            if feature_name == "Few-Shot Examples (2+)":
                value = f" ({result.few_shot_example_count} examples)"
            print(f"    {result.version:<20} {status}{value}")

    # Recommendations
    print(f"\n{'='*80}")
    print("RECOMMENDATIONS")
    print("="*80)

    # Find best variant
    best_variant = max(results[1:], key=lambda r: r.overall_quality_score)  # Skip baseline
    most_efficient = min(results[1:], key=lambda r: r.line_count)
    best_balance = max(results[1:], key=lambda r: r.overall_quality_score / (r.line_count / 100))

    print(f"\n1. **Highest Quality**: {best_variant.version}")
    print(f"   - Score: {best_variant.overall_quality_score}/100")
    print(f"   - Size: {best_variant.line_count} lines")
    print(f"   - Few-shot examples: {best_variant.few_shot_example_count}")

    print(f"\n2. **Most Efficient (Smallest)**: {most_efficient.version}")
    print(f"   - Score: {most_efficient.overall_quality_score}/100")
    print(f"   - Size: {most_efficient.line_count} lines")
    print(f"   - Size vs baseline: {((most_efficient.line_count - baseline_size) / baseline_size * 100):+.1f}%")

    print(f"\n3. **Best Balance (Quality/Size Ratio)**: {best_balance.version}")
    print(f"   - Score: {best_balance.overall_quality_score}/100")
    print(f"   - Size: {best_balance.line_count} lines")
    print(f"   - Ratio: {best_balance.overall_quality_score / (best_balance.line_count / 100):.2f}")

    # Decision matrix
    print(f"\n{'='*80}")
    print("DECISION MATRIX")
    print("="*80)

    print(f"\n**If priority is QUALITY (>85/100 score)**:")
    quality_variants = [r for r in results[1:] if r.overall_quality_score >= 85]
    if quality_variants:
        recommended = min(quality_variants, key=lambda r: r.line_count)
        print(f"  → Recommend: {recommended.version}")
        print(f"    - Achieves quality target with minimal size")
        print(f"    - {recommended.line_count} lines vs {best_variant.line_count} (smallest high-quality option)")
    else:
        print(f"  → No variant achieves 85+ score")
        print(f"    - Highest is {best_variant.version} at {best_variant.overall_quality_score}/100")

    print(f"\n**If priority is EFFICIENCY (<400 lines)**:")
    efficient_variants = [r for r in results[1:] if r.line_count < 400]
    if efficient_variants:
        recommended = max(efficient_variants, key=lambda r: r.overall_quality_score)
        print(f"  → Recommend: {recommended.version}")
        print(f"    - Best quality within size constraint")
        print(f"    - {recommended.overall_quality_score}/100 score with {recommended.line_count} lines")
    else:
        print(f"  → No variant under 400 lines")
        print(f"    - Smallest is {most_efficient.version} at {most_efficient.line_count} lines")

    print(f"\n**If priority is BALANCE (quality + efficiency)**:")
    print(f"  → Recommend: {best_balance.version}")
    print(f"    - Best quality-to-size ratio: {best_balance.overall_quality_score / (best_balance.line_count / 100):.2f}")
    print(f"    - {best_balance.overall_quality_score}/100 quality with {best_balance.line_count} lines")

    # Final recommendation
    print(f"\n{'='*80}")
    print("FINAL RECOMMENDATION")
    print("="*80)

    # Logic: Prioritize quality (85+) with minimal size
    if quality_variants:
        final_recommendation = min(quality_variants, key=lambda r: r.line_count)
        print(f"\n✅ **Recommended Template: {final_recommendation.version}**")
        print(f"\n**Rationale**:")
        print(f"- Achieves quality target: {final_recommendation.overall_quality_score}/100 (≥85 threshold)")
        print(f"- Minimal size: {final_recommendation.line_count} lines")
        print(f"- Size reduction vs v2: {((final_recommendation.line_count - 1081) / 1081 * 100):+.1f}% (v2 avg: 1,081 lines)")
        print(f"- Size increase vs baseline: {((final_recommendation.line_count - baseline_size) / baseline_size * 100):+.1f}%")
        print(f"- Template compliance: {final_recommendation.template_compliance_score}%")
        print(f"- Few-shot examples: {final_recommendation.few_shot_example_count}")

        print(f"\n**Use this template for remaining 41 agents**")

    else:
        print(f"\n⚠️  **No variant achieves 85+ quality score**")
        print(f"\n**Options**:")
        print(f"1. Use highest quality variant: {best_variant.version} ({best_variant.overall_quality_score}/100)")
        print(f"2. Iterate on template design to improve quality")
        print(f"3. Test with real agent execution (structure score may not reflect actual performance)")

    print(f"\n{'='*80}\n")

    return results


if __name__ == "__main__":
    test_template_variants()
