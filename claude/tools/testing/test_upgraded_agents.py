#!/usr/bin/env python3
"""
Test Upgraded Agents - Validation & Comparison
==============================================

Purpose: Test 5 upgraded agents to validate improvements and identify lessons before upgrading remaining 41 agents

Agents to Test:
1. DNS Specialist (v1: 305 lines → v2: 1,113 lines, +265%)
2. SRE Principal Engineer (v1: 44 lines → v2: 985 lines, +2,139%)
3. Azure Solutions Architect (v1: 240 lines → v2: 759 lines, +216%)
4. Service Desk Manager (v1: 348 lines → v2: 1,271 lines, +265%)
5. AI Specialists Agent (v1: 154 lines → v2: 1,271 lines, +725%)

Testing Approach:
- Manual quality assessment (not automated execution yet)
- Structure & completeness analysis
- Template compliance validation
- Few-shot example quality
- Lessons learned documentation
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict


@dataclass
class AgentTestResult:
    """Test results for a single agent"""
    agent_name: str
    version: str
    file_path: str

    # Size metrics
    line_count: int
    size_change_pct: float

    # Structure validation (template compliance)
    has_agent_overview: bool
    has_core_behavior_principles: bool
    has_openai_3_reminders: bool
    has_few_shot_examples: bool
    few_shot_example_count: int
    has_tool_calling_patterns: bool
    has_problem_solving_templates: bool
    has_performance_metrics: bool
    has_integration_points: bool

    # Quality assessment (manual scoring)
    template_compliance_score: int  # 0-100
    few_shot_quality_score: int  # 0-100
    overall_quality_score: int  # 0-100

    # Issues found
    issues: List[str]
    strengths: List[str]

    def to_dict(self):
        return asdict(self)


class AgentValidator:
    """Validate agent structure and template compliance"""

    def __init__(self, agent_dir: Path = Path("claude/agents")):
        self.agent_dir = agent_dir

    def validate_agent(self, agent_file: str, version: str) -> AgentTestResult:
        """Validate single agent file"""
        file_path = self.agent_dir / agent_file

        with open(file_path, 'r') as f:
            content = f.read()

        lines = content.split('\n')
        line_count = len(lines)

        # Structure validation
        has_agent_overview = "## Agent Overview" in content
        has_core_behavior = "## Core Behavior Principles" in content
        has_openai_reminders = all([
            "Persistence & Completion" in content,
            "Tool-Calling Protocol" in content,
            "Systematic Planning" in content
        ])
        has_few_shot = "**Few-Shot Examples:**" in content or "**Example 1:" in content
        few_shot_count = content.count("**Example ")
        has_tool_calling = "```python" in content and "self.call_tool" in content
        has_problem_solving = "## Problem-Solving Approach" in content
        has_metrics = "## Performance Metrics" in content
        has_integration = "## Integration Points" in content

        # Calculate scores
        template_compliance = self._calculate_template_compliance(
            has_agent_overview,
            has_core_behavior,
            has_openai_reminders,
            has_few_shot,
            has_tool_calling,
            has_problem_solving,
            has_metrics,
            has_integration
        )

        # Analyze quality
        issues = []
        strengths = []

        if not has_core_behavior:
            issues.append("Missing Core Behavior Principles section")
        else:
            strengths.append("Has Core Behavior Principles with OpenAI reminders")

        if few_shot_count < 2:
            issues.append(f"Only {few_shot_count} few-shot examples (need 2+ per key command)")
        else:
            strengths.append(f"Has {few_shot_count} few-shot examples")

        if not has_tool_calling:
            issues.append("Missing tool-calling code patterns")
        else:
            strengths.append("Includes tool-calling code patterns")

        if not has_problem_solving:
            issues.append("Missing Problem-Solving Approach section")
        else:
            strengths.append("Has Problem-Solving templates")

        # Few-shot quality score (manual assessment placeholder)
        few_shot_quality = 85 if few_shot_count >= 4 else 70 if few_shot_count >= 2 else 40

        # Overall quality score
        overall_quality = (template_compliance + few_shot_quality) // 2

        return AgentTestResult(
            agent_name=agent_file.replace("_agent_v2.md", "").replace("_agent.md", ""),
            version=version,
            file_path=str(file_path),
            line_count=line_count,
            size_change_pct=0.0,  # Will calculate separately
            has_agent_overview=has_agent_overview,
            has_core_behavior_principles=has_core_behavior,
            has_openai_3_reminders=has_openai_reminders,
            has_few_shot_examples=has_few_shot,
            few_shot_example_count=few_shot_count,
            has_tool_calling_patterns=has_tool_calling,
            has_problem_solving_templates=has_problem_solving,
            has_performance_metrics=has_metrics,
            has_integration_points=has_integration,
            template_compliance_score=template_compliance,
            few_shot_quality_score=few_shot_quality,
            overall_quality_score=overall_quality,
            issues=issues,
            strengths=strengths
        )

    def _calculate_template_compliance(self, *checks) -> int:
        """Calculate template compliance score (0-100)"""
        total_checks = len(checks)
        passed_checks = sum(1 for check in checks if check)
        return int((passed_checks / total_checks) * 100)

    def compare_versions(self, v1_result: AgentTestResult, v2_result: AgentTestResult) -> Dict:
        """Compare v1 and v2 versions"""
        size_change = ((v2_result.line_count - v1_result.line_count) / v1_result.line_count) * 100

        return {
            "agent_name": v1_result.agent_name,
            "v1_lines": v1_result.line_count,
            "v2_lines": v2_result.line_count,
            "size_change_pct": size_change,
            "v1_quality_score": v1_result.overall_quality_score,
            "v2_quality_score": v2_result.overall_quality_score,
            "quality_improvement": v2_result.overall_quality_score - v1_result.overall_quality_score,
            "v1_few_shot_count": v1_result.few_shot_example_count,
            "v2_few_shot_count": v2_result.few_shot_example_count,
            "v1_issues": v1_result.issues,
            "v2_issues": v2_result.issues,
            "improvements": self._identify_improvements(v1_result, v2_result)
        }

    def _identify_improvements(self, v1: AgentTestResult, v2: AgentTestResult) -> List[str]:
        """Identify specific improvements from v1 to v2"""
        improvements = []

        if not v1.has_core_behavior_principles and v2.has_core_behavior_principles:
            improvements.append("Added Core Behavior Principles (OpenAI's 3 critical reminders)")

        if v1.few_shot_example_count < 2 and v2.few_shot_example_count >= 2:
            improvements.append(f"Added few-shot examples ({v1.few_shot_example_count} → {v2.few_shot_example_count})")

        if not v1.has_tool_calling_patterns and v2.has_tool_calling_patterns:
            improvements.append("Added tool-calling code patterns")

        if not v1.has_problem_solving_templates and v2.has_problem_solving_templates:
            improvements.append("Added Problem-Solving Approach templates")

        if not v1.has_performance_metrics and v2.has_performance_metrics:
            improvements.append("Added Performance Metrics section")

        return improvements


def run_agent_validation_tests():
    """Run validation tests on all 5 upgraded agents"""

    validator = AgentValidator()

    agents_to_test = [
        ("dns_specialist_agent.md", "dns_specialist_agent_v2.md"),
        ("sre_principal_engineer_agent.md", "sre_principal_engineer_agent_v2.md"),
        ("azure_solutions_architect_agent.md", "azure_solutions_architect_agent_v2.md"),
        ("service_desk_manager_agent.md", "service_desk_manager_agent_v2.md"),
        ("ai_specialists_agent.md", "ai_specialists_agent_v2.md"),
    ]

    print("="*80)
    print("AGENT UPGRADE VALIDATION TEST")
    print("="*80)
    print(f"Testing {len(agents_to_test)} agents (v1 vs v2)\n")

    comparisons = []
    all_v2_results = []

    for v1_file, v2_file in agents_to_test:
        print(f"\nTesting: {v1_file.replace('_agent.md', '')}...")

        # Validate both versions
        v1_result = validator.validate_agent(v1_file, "v1")
        v2_result = validator.validate_agent(v2_file, "v2")

        # Compare
        comparison = validator.compare_versions(v1_result, v2_result)
        comparisons.append(comparison)
        all_v2_results.append(v2_result)

        # Print summary
        print(f"  v1: {v1_result.line_count} lines, quality: {v1_result.overall_quality_score}/100")
        print(f"  v2: {v2_result.line_count} lines, quality: {v2_result.overall_quality_score}/100")
        print(f"  Change: +{comparison['size_change_pct']:.1f}% size, +{comparison['quality_improvement']} quality")
        print(f"  Few-shot examples: {v1_result.few_shot_example_count} → {v2_result.few_shot_example_count}")

        if v2_result.issues:
            print(f"  ⚠️  Issues: {', '.join(v2_result.issues)}")
        else:
            print(f"  ✅ No issues found")

    # Generate summary report
    print("\n" + "="*80)
    print("SUMMARY REPORT")
    print("="*80)

    # Calculate averages
    avg_size_change = sum(c['size_change_pct'] for c in comparisons) / len(comparisons)
    avg_quality_improvement = sum(c['quality_improvement'] for c in comparisons) / len(comparisons)
    avg_v2_quality = sum(r.overall_quality_score for r in all_v2_results) / len(all_v2_results)
    total_few_shot = sum(r.few_shot_example_count for r in all_v2_results)

    print(f"\nAverage Metrics:")
    print(f"  Size increase: +{avg_size_change:.1f}%")
    print(f"  Quality improvement: +{avg_quality_improvement:.1f} points")
    print(f"  Average v2 quality score: {avg_v2_quality:.1f}/100")
    print(f"  Total few-shot examples created: {total_few_shot}")

    # Template compliance check
    print(f"\nTemplate Compliance (v2 agents):")
    compliance_checks = {
        "Agent Overview": sum(1 for r in all_v2_results if r.has_agent_overview),
        "Core Behavior Principles": sum(1 for r in all_v2_results if r.has_core_behavior_principles),
        "OpenAI 3 Reminders": sum(1 for r in all_v2_results if r.has_openai_3_reminders),
        "Few-Shot Examples": sum(1 for r in all_v2_results if r.has_few_shot_examples),
        "Tool-Calling Patterns": sum(1 for r in all_v2_results if r.has_tool_calling_patterns),
        "Problem-Solving Templates": sum(1 for r in all_v2_results if r.has_problem_solving_templates),
        "Performance Metrics": sum(1 for r in all_v2_results if r.has_performance_metrics),
        "Integration Points": sum(1 for r in all_v2_results if r.has_integration_points),
    }

    for check_name, count in compliance_checks.items():
        percentage = (count / len(all_v2_results)) * 100
        status = "✅" if percentage == 100 else "⚠️"
        print(f"  {status} {check_name}: {count}/{len(all_v2_results)} ({percentage:.0f}%)")

    # Lessons learned
    print(f"\n" + "="*80)
    print("LESSONS LEARNED")
    print("="*80)

    lessons = []

    # Check if all agents have minimum 2 few-shot examples
    low_few_shot = [r for r in all_v2_results if r.few_shot_example_count < 2]
    if low_few_shot:
        lessons.append(f"⚠️  {len(low_few_shot)} agents have <2 few-shot examples per command (need minimum 2)")
    else:
        lessons.append("✅ All agents have 2+ few-shot examples")

    # Check template compliance
    if all(r.template_compliance_score >= 90 for r in all_v2_results):
        lessons.append("✅ All agents have excellent template compliance (90%+)")
    else:
        low_compliance = [r for r in all_v2_results if r.template_compliance_score < 90]
        lessons.append(f"⚠️  {len(low_compliance)} agents have <90% template compliance")

    # Check size growth
    if avg_size_change > 500:
        lessons.append(f"⚠️  Very large size increase (+{avg_size_change:.0f}%) - may impact performance")
    elif avg_size_change > 200:
        lessons.append(f"✅ Significant size increase (+{avg_size_change:.0f}%) indicates comprehensive upgrades")

    # Check quality improvement
    if avg_quality_improvement > 20:
        lessons.append(f"✅ Strong quality improvement (+{avg_quality_improvement:.1f} points)")
    elif avg_quality_improvement > 10:
        lessons.append(f"⚠️  Moderate quality improvement (+{avg_quality_improvement:.1f} points) - could be better")
    else:
        lessons.append(f"❌ Weak quality improvement (+{avg_quality_improvement:.1f} points) - review approach")

    # Print lessons
    for i, lesson in enumerate(lessons, 1):
        print(f"{i}. {lesson}")

    # Recommendations
    print(f"\n" + "="*80)
    print("RECOMMENDATIONS FOR REMAINING 41 AGENTS")
    print("="*80)

    recommendations = []

    # Based on size growth
    if avg_size_change > 400:
        recommendations.append("Consider template optimization - average +500% size may be excessive")

    # Based on few-shot examples
    avg_few_shot = total_few_shot / len(all_v2_results)
    if avg_few_shot < 4:
        recommendations.append(f"Increase few-shot examples to 4+ per agent (current avg: {avg_few_shot:.1f})")

    # Based on quality scores
    if avg_v2_quality < 85:
        recommendations.append(f"Target 85+ quality score for remaining agents (current avg: {avg_v2_quality:.1f})")

    # Based on issues found
    common_issues = {}
    for r in all_v2_results:
        for issue in r.issues:
            common_issues[issue] = common_issues.get(issue, 0) + 1

    if common_issues:
        most_common = max(common_issues.items(), key=lambda x: x[1])
        recommendations.append(f"Address common issue: '{most_common[0]}' (found in {most_common[1]} agents)")

    if not recommendations:
        recommendations.append("✅ Template v2 is working well - continue with current approach for remaining 41 agents")

    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")

    # Save detailed results
    output_dir = Path("claude/data/ab_tests")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "agent_validation_results.json"
    results_data = {
        "test_date": "2025-10-11",
        "agents_tested": len(agents_to_test),
        "comparisons": comparisons,
        "v2_results": [r.to_dict() for r in all_v2_results],
        "summary": {
            "avg_size_change_pct": avg_size_change,
            "avg_quality_improvement": avg_quality_improvement,
            "avg_v2_quality_score": avg_v2_quality,
            "total_few_shot_examples": total_few_shot,
            "template_compliance": compliance_checks
        },
        "lessons_learned": lessons,
        "recommendations": recommendations
    }

    with open(output_file, 'w') as f:
        json.dump(results_data, f, indent=2)

    print(f"\n✅ Detailed results saved to: {output_file}")

    return results_data


if __name__ == "__main__":
    run_agent_validation_tests()
